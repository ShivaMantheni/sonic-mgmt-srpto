"""
srpto.scheduler.engine
=======================
Parallel scheduler engine — the heart of SRPTO.

Mirrors the architecture of Eka's _run_spytest_execution() (main.py 6678-7200)
but runs scripts via subprocess (spytest or pytest) instead of a remote SSH
worker.  The DUT pool and lock logic is fully reused from
srpto.lock_manager.dut_lock.DUTPool.

Execution model (same as Eka):
  ┌─────────────────────────────────────────────────┐
  │  ONE call to engine.run(scripts)                │
  │   ↓                                             │
  │  spawn ONE worker thread per script             │
  │   ↓                                             │
  │  each worker calls pool.acquire() ─── BLOCKS    │
  │  until DUTs are free                            │
  │   ↓                                             │
  │  launches spytest/pytest subprocess             │
  │   ↓                                             │
  │  calls pool.release() when done                 │
  └─────────────────────────────────────────────────┘

New SRPTO concepts vs Eka:
  * Works locally (subprocess) instead of remote SSH
  * Supports both spytest and pytest (sonic-mgmt) invocation styles
  * Resource-map driven (no topology canvas — uses YAML or inline markers)
  * JSON status stream on stdout (replaces WebSocket / _exec_queue_state)
  * Plugin hook system: pre_script / post_script / on_conflict
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from srpto.lock_manager.dut_lock import DUTPool, ResourceRequirement, LockTier
from srpto.resource_tagger.tagger import ResourceTagger, parse_link_requirements
from srpto.scheduler.conflict import ConflictDetector

logger = logging.getLogger("srpto.scheduler")


# ---------------------------------------------------------------------------
# Script result
# ---------------------------------------------------------------------------

@dataclass
class ScriptResult:
    script_path: str
    status: str          # queued | waiting | running | done | failed | cancelled
    duts_allocated: List[str] = field(default_factory=list)
    return_code: Optional[int] = None
    log_path: Optional[str] = None
    duration_s: float = 0.0
    error: str = ""


# ---------------------------------------------------------------------------
# Scheduler configuration
# ---------------------------------------------------------------------------

@dataclass
class SchedulerConfig:
    # Testbed YAML (sonic-mgmt / spytest style)
    testbed_path: str = ""
    # Resource map YAML (srpto resource declarations)
    resource_map_path: str = ""
    # Logs output directory
    logs_dir: str = "./srpto_logs"
    # Maximum parallel workers
    max_workers: int = 16
    # DUT acquire timeout in seconds (0 = wait forever, matches Eka default)
    acquire_timeout: float = 0.0
    # Poll interval for DUT pool (seconds, default matches Eka)
    poll_interval: float = 5.0
    # Invocation mode: "spytest" or "pytest"
    mode: str = "spytest"
    # Extra CLI args passed to every script invocation
    extra_args: List[str] = field(default_factory=list)
    # spytest binary path (resolved automatically if empty)
    spytest_bin: str = ""
    # pytest binary path
    pytest_bin: str = "pytest"
    # Status callback: receives ScriptResult on every status change
    on_status_change: Optional[Callable[[ScriptResult], None]] = None
    # Enable dry-run (resolve allocations only, no subprocess)
    dry_run: bool = False
    # Optional shell command run on each allocated DUT after its test finishes.
    # Prevents "dirty DUT" failures when the next test inherits stale state
    # (e.g. stale BGP routes, ACLs, VLANs from a previous parallel session).
    # The command receives each DUT name as a positional arg.
    # Example: "ssh admin@{dut} sudo config reload -y"
    # Leave empty to skip scrub (default — matches current sequential behaviour).
    dut_scrub_cmd: str = ""


# ---------------------------------------------------------------------------
# Testbed parser
# ---------------------------------------------------------------------------

def _parse_testbed(testbed_path: str) -> Tuple[List[str], Dict, Optional[str]]:
    """
    Parse a sonic-mgmt / spytest testbed YAML and return:
      (dut_names, topology_connections, ptf_host)

    Supports both spytest v1 and v2 (version: "2.0") testbed formats.
    """
    if not testbed_path or not os.path.exists(testbed_path):
        logger.warning("[Testbed] File not found: %s — using empty testbed", testbed_path)
        return [], {}, None

    with open(testbed_path) as f:
        tb = yaml.safe_load(f) or {}

    dut_names = list(tb.get("devices", {}).keys())
    ptf_host = tb.get("ptf_host") or tb.get("ptf")
    topology_connections = {}

    # Parse topology links (spytest format: links section)
    links_section = tb.get("links", [])
    for link in links_section:
        # link: {endpoints: [dut1:eth0, dut2:eth1]} or similar
        if isinstance(link, dict):
            eps = link.get("endpoints", [])
            if len(eps) >= 2:
                dA = eps[0].split(":")[0]
                dB = eps[1].split(":")[0]
                key = (dA, dB)
                topology_connections[key] = topology_connections.get(key, 0) + 1

    # Parse sonic-mgmt format: topo section with port-channel / interface maps
    topo = tb.get("topo", {})
    if topo and not links_section:
        # Best-effort: extract DUT pairs from port_channel_config or interface_config
        for dut, iface_map in topo.get("properties", {}).items():
            for peer in iface_map.get("peers", {}).keys():
                key = (dut, peer)
                topology_connections[key] = topology_connections.get(key, 0) + 1

    logger.info(
        "[Testbed] Parsed %d DUT(s): %s | PTF: %s | Links: %d",
        len(dut_names), dut_names, ptf_host, len(topology_connections)
    )
    return dut_names, topology_connections, ptf_host


# ---------------------------------------------------------------------------
# Subset testbed generator (mirrors Eka _create_subset_testbed)
# ---------------------------------------------------------------------------

def _create_subset_testbed(testbed_config: dict, allocated_duts: List[str]) -> dict:
    """
    Build a minimal testbed YAML containing only the allocated DUTs.
    Direct port of Eka _create_subset_testbed (main.py 3517-3551).
    """
    import copy
    subset = copy.deepcopy(testbed_config)
    all_devices = subset.get("devices", {})
    # Remove DUTs not in allocated set
    for dut in list(all_devices.keys()):
        if dut not in allocated_duts:
            del all_devices[dut]
    # Prune links to only those between allocated DUTs
    if "links" in subset:
        subset["links"] = [
            l for l in subset["links"]
            if all(
                ep.split(":")[0] in allocated_duts
                for ep in l.get("endpoints", [])
            )
        ]
    return subset


# ---------------------------------------------------------------------------
# Script invoker
# ---------------------------------------------------------------------------

def _build_command(
    cfg: SchedulerConfig,
    script_path: str,
    subset_testbed_path: str,
    log_dir: str,
) -> List[str]:
    """Build the subprocess command for a single script."""
    if cfg.mode == "spytest":
        spy_bin = cfg.spytest_bin or _find_spytest_bin(script_path)
        cmd = [
            sys.executable, spy_bin,
            "--tryssh", "1",
            "--testbed", subset_testbed_path,
            script_path,
            "--logs-path", log_dir,
            "--get-tech-support", "none",
            "--syslog-check", "none",
        ]
    else:
        # pytest (sonic-mgmt community style)
        cmd = [
            cfg.pytest_bin,
            script_path,
            "--testbed-file", subset_testbed_path,
            f"--log-file={os.path.join(log_dir, 'pytest.log')}",
        ]
    cmd += cfg.extra_args
    return cmd


def _find_spytest_bin(script_path: str) -> str:
    """Walk up from script_path to find bin/spytest."""
    p = Path(script_path).resolve()
    for parent in p.parents:
        candidate = parent / "bin" / "spytest"
        if candidate.exists():
            return str(candidate)
    return "spytest"


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

class ParallelScheduler:
    """
    SRPTO Parallel Scheduler.

    Usage:
        cfg = SchedulerConfig(testbed_path="sonic_t0.yaml", mode="pytest")
        scheduler = ParallelScheduler(cfg)
        results = scheduler.run([
            "tests/bgp/test_bgp_gr.py",
            "tests/acl/test_acl.py",
            "tests/snmp/test_snmp.py",
        ])
    """

    def __init__(self, cfg: SchedulerConfig):
        self.cfg = cfg
        self._stop_event = threading.Event()
        self._results: Dict[str, ScriptResult] = {}
        self._results_lock = threading.Lock()

        # Parse testbed
        dut_names, topo_connections, ptf_host = _parse_testbed(cfg.testbed_path)
        if not dut_names:
            logger.warning("[Scheduler] No DUTs in testbed — using synthetic slots")
            dut_names = ["Slot-1"]

        # DUT pool (Eka acquire_duts / release_duts)
        self._pool = DUTPool(
            dut_names=dut_names,
            ptf_host=ptf_host,
            topology_connections=topo_connections,
            poll_interval=cfg.poll_interval,
            max_wait_seconds=cfg.acquire_timeout,
        )
        self._pool.register_status_callback(self._on_pool_change)

        # Resource tagger
        self._tagger = ResourceTagger(cfg.resource_map_path)

        # Conflict detector
        self._conflict_detector = ConflictDetector()

        # Testbed config for subset generation
        self._testbed_config: dict = {}
        if cfg.testbed_path and os.path.exists(cfg.testbed_path):
            with open(cfg.testbed_path) as f:
                self._testbed_config = yaml.safe_load(f) or {}

        os.makedirs(cfg.logs_dir, exist_ok=True)
        logger.info("[Scheduler] Ready | DUTs: %s | Mode: %s", dut_names, cfg.mode)

    # ------------------------------------------------------------------
    # Public: run
    # ------------------------------------------------------------------

    def run(self, script_paths: List[str]) -> List[ScriptResult]:
        """
        Schedule and run all scripts in parallel.

        Returns a list of ScriptResult, one per script.

        Implementation mirrors Eka _run_spytest_execution():
          1. Analyse all scripts → ResourceRequirement
          2. Pre-flight conflict check
          3. Init queue state (_q_init equivalent)
          4. Spawn one thread per script
          5. Each thread: acquire DUTs → run subprocess → release DUTs
          6. Join all threads → return results
        """
        if not script_paths:
            logger.warning("[Scheduler] No scripts to run")
            return []

        logger.info(
            "[Scheduler] Starting %d script(s) in parallel | testbed: %s",
            len(script_paths), self.cfg.testbed_path
        )

        # ── 1. Resolve requirements for all scripts ───────────────────────────
        requirements: Dict[str, ResourceRequirement] = {}
        for path in script_paths:
            source = None
            try:
                with open(path) as f:
                    source = f.read()
            except Exception:
                pass
            requirements[path] = self._tagger.get_requirement(path, source)

        # ── 2. Pre-flight conflict check ─────────────────────────────────────
        conflicts = self._conflict_detector.check_all(requirements)
        if conflicts:
            logger.warning("[Scheduler] Pre-flight conflicts detected:")
            for c in conflicts:
                logger.warning("  %s", c)

        # ── 3. Init result slots (mirrors Eka _q_init) ────────────────────────
        with self._results_lock:
            for path in script_paths:
                self._results[path] = ScriptResult(
                    script_path=path, status="queued"
                )
        self._emit_queue_state()

        # ── 4. Spawn workers ─────────────────────────────────────────────────
        t_start = time.time()
        with ThreadPoolExecutor(
            max_workers=min(len(script_paths), self.cfg.max_workers),
            thread_name_prefix="srpto-worker"
        ) as executor:
            futures = {
                executor.submit(
                    self._run_one_script, path, requirements[path], idx
                ): path
                for idx, path in enumerate(script_paths)
            }
            for future in as_completed(futures):
                path = futures[future]
                try:
                    future.result()
                except Exception as e:
                    logger.error("[Scheduler] Worker exception for %s: %s", path, e)
                    with self._results_lock:
                        r = self._results[path]
                        r.status = "failed"
                        r.error = str(e)

        total = time.time() - t_start
        results = list(self._results.values())
        passed = sum(1 for r in results if r.status == "done")
        failed = sum(1 for r in results if r.status == "failed")
        logger.info(
            "[Scheduler] All done in %.1fs | passed=%d failed=%d cancelled=%d",
            total, passed, failed, len(results) - passed - failed
        )
        self._print_summary(results, total)
        return results

    def stop(self):
        """Signal all workers to stop (mirrors Eka _is_exec_cancelled)."""
        self._stop_event.set()
        logger.info("[Scheduler] Stop signal sent")

    # ------------------------------------------------------------------
    # Internal: per-script worker (mirrors Eka run_one_script)
    # ------------------------------------------------------------------

    def _run_one_script(
        self, script_path: str, req: ResourceRequirement, slot_idx: int
    ):
        """
        Single script worker thread.

        Flow mirrors Eka run_one_script (main.py 6941-7100):
          1. acquire_duts() — blocks until DUTs available
          2. Create subset testbed YAML
          3. Launch spytest / pytest subprocess
          4. Stream log tail
          5. release_duts()
        """
        sname = os.path.basename(script_path)
        self._update_status(script_path, "waiting")
        # Register this request's DUT count for anti-starvation fairness.
        # The pool won't let smaller requests starve a large pending request.
        self._pool.register_pending(req.dut_count)
        logger.info(
            "[QUEUE][%s] Waiting for %d DUT(s) (exclusive=%s, ptf=%s)",
            sname, req.dut_count, req.topology_exclusive, req.ptf_required
        )

        allocated = []
        t0 = time.time()

        try:
            # ── acquire_duts (Eka equivalent) ─────────────────────────────────
            allocated = self._pool.acquire(req, sname, self._stop_event)
            if allocated is None:
                self._update_status(script_path, "cancelled",
                                    error="Timed out / stopped waiting for DUTs")
                return

            self._update_status(script_path, "running", duts=allocated)
            logger.info("[ALLOC][%s] → DUT(s): %s", sname, allocated)

            if self.cfg.dry_run:
                logger.info("[DRY-RUN][%s] Would run on DUTs: %s", sname, allocated)
                time.sleep(0.1)
                self._update_status(script_path, "done", duts=allocated,
                                    duration=time.time() - t0)
                return

            # ── Create isolated workspace per script ──────────────────────────
            # Each script gets its own directory so SpyTest artifacts
            # (results.csv, spytest.html, syslog, pcaps) NEVER collide between
            # parallel sessions. This is the subprocess isolation boundary.
            ts = int(time.time())
            workspace = os.path.join(
                self.cfg.logs_dir, f"run_{sname}_{ts}"
            )
            os.makedirs(workspace, exist_ok=True)

            # ── Write subset testbed YAML into the workspace ──────────────────
            # *** SpyTestSessionBinder ***
            # SpyTest receives a testbed YAML that contains ONLY the DUTs
            # allocated to this script. It physically cannot see or touch busy
            # DUTs. This is what actually enforces DUT isolation — not just the
            # Python lock. Without this, all subprocesses would share the same
            # testbed topology and use whatever DUTs it provides.
            subset_cfg = _create_subset_testbed(self._testbed_config, allocated)
            subset_tb_path = os.path.join(workspace, "testbed_subset.yaml")
            with open(subset_tb_path, "w") as f:
                yaml.dump(subset_cfg, f, default_flow_style=False)

            # Write a human-readable allocation record for debugging
            with open(os.path.join(workspace, "srpto_allocation.txt"), "w") as f:
                f.write(f"Script   : {script_path}\n")
                f.write(f"DUTs     : {allocated}\n")
                f.write(f"Testbed  : {self.cfg.testbed_path}\n")
                f.write(f"Subset   : {subset_tb_path}\n")
                f.write(f"PTF      : {req.ptf_required}\n")
                f.write(f"Exclusive: {req.topology_exclusive}\n")
                f.write(f"Resources: {sorted(req.shared_resources)}\n")

            log_dir = os.path.join(workspace, "logs")
            os.makedirs(log_dir, exist_ok=True)

            # ── Launch subprocess ─────────────────────────────────────────────
            # subset_tb_path → SpyTest sees ONLY allocated DUTs
            # cwd=workspace  → all SpyTest output files stay in this dir
            cmd = _build_command(self.cfg, script_path, subset_tb_path, log_dir)
            log_file = os.path.join(log_dir, "stdout.log")
            logger.info("[RUN][%s] workspace: %s", sname, workspace)
            logger.info(
                "[RUN][%s] subset testbed: %s (DUTs: %s)",
                sname, subset_tb_path, allocated
            )
            logger.info("[RUN][%s] CMD: %s", sname, " ".join(cmd))

            rc = self._run_process(cmd, log_file, script_path, sname, cwd=workspace)

            dur = time.time() - t0
            if self._stop_event.is_set() and rc != 0:
                self._update_status(script_path, "cancelled", duts=allocated,
                                    return_code=rc, log_path=log_dir, duration=dur)
            elif rc == 0:
                logger.info("[DONE][%s] ✓ in %.1fs", sname, dur)
                self._update_status(script_path, "done", duts=allocated,
                                    return_code=rc, log_path=log_dir, duration=dur)
            else:
                logger.error("[FAIL][%s] ✗ rc=%d in %.1fs", sname, rc, dur)
                self._update_status(script_path, "failed", duts=allocated,
                                    return_code=rc, log_path=log_dir, duration=dur,
                                    error=f"exit code {rc}")

        except Exception as e:
            logger.exception("[ERROR][%s] %s", sname, e)
            self._update_status(script_path, "failed", duts=allocated,
                                error=str(e), duration=time.time() - t0)
            raise
        finally:
            # Unregister pending count — may allow starvation guard to relax
            self._pool.unregister_pending(req.dut_count)
            # Optional: scrub DUTs before returning to pool to prevent
            # "dirty DUT" state from affecting the next parallel test.
            if allocated and self.cfg.dut_scrub_cmd:
                self._scrub_duts(allocated, sname)
            if allocated:
                self._pool.release(allocated, sname, req)

    def _scrub_duts(self, duts: List[str], sname: str):
        """
        Optional post-test DUT cleanup.

        Runs cfg.dut_scrub_cmd on each allocated DUT before releasing them
        back to the pool. This prevents a test from leaving stale BGP routes,
        ACL rules, VLAN configs, or PortChannel state that would cause the
        NEXT parallel test to fail on a "dirty" DUT.

        cfg.dut_scrub_cmd example:
            "ssh -o StrictHostKeyChecking=no admin@{dut} sudo config reload -y"

        The string {dut} is replaced with each DUT name. Failures are logged
        but do NOT prevent DUT release — a failed scrub is better than a
        deadlocked pool.
        """
        for dut in duts:
            cmd_str = self.cfg.dut_scrub_cmd.replace("{dut}", dut)
            try:
                logger.info("[SCRUB][%s] %s → %s", sname, dut, cmd_str)
                result = subprocess.run(
                    cmd_str, shell=True, timeout=120,
                    capture_output=True, text=True
                )
                if result.returncode != 0:
                    logger.warning(
                        "[SCRUB][%s] %s scrub failed (rc=%d): %s",
                        sname, dut, result.returncode, result.stderr[:300]
                    )
                else:
                    logger.info("[SCRUB][%s] %s scrubbed OK", sname, dut)
            except subprocess.TimeoutExpired:
                logger.warning("[SCRUB][%s] %s scrub timed out (120s)", sname, dut)
            except Exception as exc:
                logger.warning("[SCRUB][%s] %s scrub error: %s", sname, dut, exc)

    def _run_process(
        self, cmd: List[str], log_file: str, script_path: str, sname: str,
        cwd: Optional[str] = None,
    ) -> int:
        """
        Launch a subprocess and tail its output.
        cwd= isolates all SpyTest output artifacts (results.csv, spytest.html,
        syslog, pcaps) to the per-script workspace directory.
        """
        with open(log_file, "w") as lf:
            proc = subprocess.Popen(
                cmd,
                stdout=lf,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=cwd,      # ← SpyTest writes all relative-path files here
            )

        last_pos = 0
        while True:
            time.sleep(10)

            # Check stop signal (mirrors Eka _is_exec_cancelled)
            if self._stop_event.is_set():
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                logger.info("[%s] Killed by stop signal", sname)
                return -1

            # Stream log tail (mirrors Eka log_tail logic)
            try:
                with open(log_file) as lf:
                    lf.seek(last_pos)
                    new_lines = lf.read()
                    last_pos = lf.tell()
                if new_lines.strip():
                    for line in new_lines.strip().splitlines()[-20:]:
                        logger.debug("[LOG][%s] %s", sname, line)
            except Exception:
                pass

            # Check if process finished
            rc = proc.poll()
            if rc is not None:
                return rc

    # ------------------------------------------------------------------
    # Status management (mirrors Eka _q_update_script / _exec_queue_state)
    # ------------------------------------------------------------------

    def _update_status(
        self, script_path: str, status: str,
        duts: Optional[List[str]] = None,
        return_code: Optional[int] = None,
        log_path: Optional[str] = None,
        duration: float = 0.0,
        error: str = "",
    ):
        with self._results_lock:
            r = self._results.get(script_path)
            if r:
                r.status = status
                if duts:
                    r.duts_allocated = duts
                if return_code is not None:
                    r.return_code = return_code
                if log_path:
                    r.log_path = log_path
                if duration:
                    r.duration_s = duration
                if error:
                    r.error = error

        if self.cfg.on_status_change:
            try:
                with self._results_lock:
                    r = self._results.get(script_path)
                if r:
                    self.cfg.on_status_change(r)
            except Exception:
                pass

        self._emit_queue_state()

    def _emit_queue_state(self):
        """
        Print JSON queue state to stdout.
        Mirrors Eka's WebSocket message {type: 'queue_state', ...}.
        Consumers (CI/CD, Eka UI) can parse this stream.
        """
        with self._results_lock:
            scripts = [
                {
                    "name": os.path.basename(r.script_path),
                    "status": r.status,
                    "duts": r.duts_allocated,
                }
                for r in self._results.values()
            ]
        pool_status = self._pool.get_status()
        state = {
            "type": "queue_state",
            "scripts": scripts,
            "free_duts": pool_status["free_duts"],
            "busy_duts": pool_status["busy_duts"],
        }
        # Write to stdout as JSON line (parseable by Eka UI or CI)
        print(json.dumps(state), flush=True)

    def _on_pool_change(self, snap: dict):
        """Callback from DUTPool on any lock state change."""
        logger.debug("[Pool] Free: %s | Busy: %s", snap["free_duts"], snap["busy_duts"])

    def _print_summary(self, results: List[ScriptResult], total: float):
        """Print a human-readable execution summary (replaces Eka HTML report)."""
        print("\n" + "=" * 70)
        print(f"SRPTO Execution Summary  |  Total time: {total:.1f}s")
        print("=" * 70)
        print(f"{'Script':<40} {'Status':<12} {'DUTs':<20} {'Duration'}")
        print("-" * 70)
        for r in results:
            name = os.path.basename(r.script_path)[:39]
            duts = ",".join(r.duts_allocated) if r.duts_allocated else "-"
            dur = f"{r.duration_s:.1f}s"
            status_icon = {"done": "✓", "failed": "✗", "cancelled": "■"}.get(r.status, "?")
            print(f"{name:<40} {status_icon} {r.status:<10} {duts:<20} {dur}")
        print("=" * 70)
