"""
srpto.lock_manager.dut_lock
============================
Thread-safe DUT lock pool — direct port of Eka's acquire_duts / release_duts
logic from main.py (lines 6891-6938) extended to support:

  * PTF host locking
  * Exclusive topology lock (for config reload / reboot tests)
  * Shared-resource conflict detection (VLANs, port-channels)
  * Optional timeout so scripts never block forever

Eka original model (single-process threading):
  pool_lock  = threading.Lock()
  available_pool: list  — mutable shared state

SRPTO adds:
  LockTier.DEVICE    → per-DUT mutex (default, matches Eka behaviour)
  LockTier.PTF       → PTF host exclusive
  LockTier.TOPOLOGY  → whole-topology exclusive (warm-reboot, config reload)
"""

from __future__ import annotations

import re
import time
import threading
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger("srpto.lock_manager")


# ---------------------------------------------------------------------------
# Lock tiers
# ---------------------------------------------------------------------------

class LockTier(Enum):
    DEVICE   = "device"    # per-DUT, same as Eka
    PTF      = "ptf"       # PTF host exclusive
    TOPOLOGY = "topology"  # whole topology exclusive (reboot / config reload)


# ---------------------------------------------------------------------------
# Resource descriptor
# ---------------------------------------------------------------------------

@dataclass
class ResourceRequirement:
    """What a single test script needs."""
    dut_count: int = 1
    dut_names: List[str] = field(default_factory=list)   # explicit names, or empty = any
    ptf_required: bool = False
    topology_exclusive: bool = False                      # config reload, reboot, warm-reboot
    shared_resources: Set[str] = field(default_factory=set)  # e.g. "vlan:100", "portchannel:Po1"
    link_requirements: Dict[Tuple[str, str], int] = field(default_factory=dict)
    # e.g. {("DUT1", "DUT2"): 2}  — matches Eka _find_duts_matching_topology input


# ---------------------------------------------------------------------------
# Lock state
# ---------------------------------------------------------------------------

@dataclass
class DUTSlot:
    name: str          # testbed device name e.g. "sonic-dut-1"
    busy: bool = False
    held_by: Optional[str] = None   # script path holding the lock


# ---------------------------------------------------------------------------
# Main pool
# ---------------------------------------------------------------------------

class DUTPool:
    """
    Thread-safe DUT pool.

    Ported from Eka main.py:
      pool_lock = Lock()
      available_pool: list
      def acquire_duts(needed, link_requirements) -> list: ...
      def release_duts(duts_to_free) -> None: ...

    SRPTO extensions:
      * PTF exclusive lock
      * Topology exclusive lock
      * Timeout support
      * Conflict-aware allocation (shared resources)
    """

    def __init__(
        self,
        dut_names: List[str],
        ptf_host: Optional[str] = None,
        topology_connections: Optional[Dict[Tuple[str, str], int]] = None,
        poll_interval: float = 5.0,
        max_wait_seconds: float = 0.0,   # 0 = wait forever (Eka default)
    ):
        self._lock = threading.Lock()
        self._slots: Dict[str, DUTSlot] = {n: DUTSlot(name=n) for n in dut_names}
        self._ptf_host = ptf_host
        self._ptf_busy = False
        self._ptf_held_by: Optional[str] = None
        self._topo_exclusive = False
        self._topo_held_by: Optional[str] = None
        self._topology_connections: Dict[Tuple[str, str], int] = topology_connections or {}
        # shared resource → set of script names currently holding that resource
        self._shared_resources: Dict[str, Set[str]] = {}
        self._poll_interval = poll_interval
        self._max_wait = max_wait_seconds

        # Status snapshot for the UI / websocket equivalent
        self._status_callbacks: List = []

        logger.info(
            "[DUTPool] Initialised with %d DUT(s): %s | PTF: %s | Topology links: %d",
            len(dut_names), dut_names, ptf_host, len(self._topology_connections)
        )

    # ------------------------------------------------------------------
    # Public: acquire / release  (mirrors Eka acquire_duts / release_duts)
    # ------------------------------------------------------------------

    def acquire(
        self,
        req: ResourceRequirement,
        script_name: str,
        stop_event: Optional[threading.Event] = None,
        poll_interval: Optional[float] = None,
    ) -> Optional[List[str]]:
        """
        Block until the requested resources are free and atomically grab them.

        Returns the list of allocated DUT names, or None on timeout / cancellation.

        Logic flow mirrors Eka main.py acquire_duts():
          1. Topology-exclusive check (new in SRPTO)
          2. PTF lock (new in SRPTO)
          3. Shared-resource conflict check (new in SRPTO)
          4. DUT-level pool allocation  ← same as Eka
             a. If topology connections exist → topology-aware match
             b. Otherwise → FIFO (simple slice)
        """
        deadline = time.time() + self._max_wait if self._max_wait > 0 else None
        poll = poll_interval if poll_interval is not None else self._poll_interval

        while True:
            # --- Check for user-requested stop ---------------------------------
            if stop_event and stop_event.is_set():
                logger.info("[%s] Cancelled while waiting for DUTs", script_name)
                return None

            # --- Timeout guard -------------------------------------------------
            if deadline and time.time() > deadline:
                logger.warning(
                    "[%s] Timed out waiting for %d DUT(s) after %.0fs",
                    script_name, req.dut_count, self._max_wait
                )
                return None

            with self._lock:
                allocated = self._try_allocate(req, script_name)
                if allocated is not None:
                    self._fire_status()
                    return allocated

            logger.debug(
                "[QUEUE][%s] Waiting for %d DUT(s)…  (pool free: %s)",
                script_name, req.dut_count, self._free_names()
            )
            time.sleep(poll)

    def release(self, duts: List[str], script_name: str, req: ResourceRequirement):
        """
        Return DUT slots (and PTF / topology lock) back to the pool.
        Mirrors Eka release_duts().
        """
        with self._lock:
            for d in duts:
                if d in self._slots:
                    self._slots[d].busy = False
                    self._slots[d].held_by = None

            if req.ptf_required and self._ptf_busy and self._ptf_held_by == script_name:
                self._ptf_busy = False
                self._ptf_held_by = None

            if req.topology_exclusive and self._topo_exclusive and self._topo_held_by == script_name:
                self._topo_exclusive = False
                self._topo_held_by = None

            # Release shared resources
            for res in req.shared_resources:
                if res in self._shared_resources:
                    self._shared_resources[res].discard(script_name)

            self._fire_status()
            logger.info(
                "[DUTPool] Released by %s → freed: %s | pool now free: %s",
                script_name, duts, self._free_names()
            )

    # ------------------------------------------------------------------
    # Public: status snapshot (mirrors Eka _exec_queue_state / _q_set_free)
    # ------------------------------------------------------------------

    def get_status(self) -> dict:
        """Return a snapshot dict compatible with Eka's _exec_queue_state schema."""
        with self._lock:
            return {
                "free_duts":  self._free_names(),
                "busy_duts":  [s.name for s in self._slots.values() if s.busy],
                "ptf_busy":   self._ptf_busy,
                "topo_locked": self._topo_exclusive,
                "shared_resources": {k: list(v) for k, v in self._shared_resources.items()},
            }

    def register_status_callback(self, cb):
        """Register a callable(status_dict) to be invoked on every state change."""
        self._status_callbacks.append(cb)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _try_allocate(self, req: ResourceRequirement, script_name: str) -> Optional[List[str]]:
        """
        One allocation attempt under the lock.
        Returns list of DUT names on success, None if not yet possible.
        """
        # ── 1. Topology exclusive guard ──────────────────────────────────────
        if self._topo_exclusive:
            return None   # wait for exclusive-lock holder to finish

        if req.topology_exclusive:
            # Need all DUTs free before grabbing topology lock
            if any(s.busy for s in self._slots.values()):
                return None
            if self._ptf_busy:
                return None

        # ── 2. PTF guard ─────────────────────────────────────────────────────
        if req.ptf_required and self._ptf_busy:
            return None

        # ── 3. Shared-resource conflict check ────────────────────────────────
        for res in req.shared_resources:
            holders = self._shared_resources.get(res, set())
            if holders:
                logger.debug(
                    "[CONFLICT] %s needs %s but it's held by %s",
                    script_name, res, holders
                )
                return None

        # ── 4. DUT-level pool allocation (matches Eka logic exactly) ─────────
        free = self._free_names()

        if len(free) < req.dut_count:
            return None     # not enough free DUTs yet

        # Topology-aware path (mirrors Eka _find_duts_matching_topology)
        if self._topology_connections and req.link_requirements:
            matched = self._find_duts_matching_topology(
                free, req.dut_count, req.link_requirements
            )
            if not matched:
                return None     # wait for matching combo
            selected = matched
        elif req.dut_names:
            # Explicit DUT names requested
            available_named = [d for d in req.dut_names if d in free]
            if len(available_named) < req.dut_count:
                return None
            selected = available_named[: req.dut_count]
        else:
            # Simple FIFO (Eka default path)
            selected = free[: req.dut_count]

        # ── Commit allocation ─────────────────────────────────────────────────
        for d in selected:
            self._slots[d].busy = True
            self._slots[d].held_by = script_name

        if req.ptf_required:
            self._ptf_busy = True
            self._ptf_held_by = script_name

        if req.topology_exclusive:
            self._topo_exclusive = True
            self._topo_held_by = script_name

        for res in req.shared_resources:
            self._shared_resources.setdefault(res, set()).add(script_name)

        logger.info(
            "[DUTPool] Allocated to %s → DUTs: %s | PTF: %s | Exclusive: %s",
            script_name, selected, req.ptf_required, req.topology_exclusive
        )
        return selected

    def _free_names(self) -> List[str]:
        return [s.name for s in self._slots.values() if not s.busy]

    def _find_duts_matching_topology(
        self,
        free_duts: List[str],
        needed: int,
        link_requirements: Dict[Tuple[str, str], int],
    ) -> Optional[List[str]]:
        """
        Topology-aware DUT matching.

        Direct port of Eka's _find_duts_matching_topology (main.py ~3142-3206).

        Tries all combinations of `needed` DUTs from `free_duts` and returns
        the first combo whose inter-device link counts satisfy `link_requirements`.

        link_requirements: {(role_A, role_B): min_links}
          e.g. {("D1","D2"): 2, ("D2","D3"): 1}
        topology_connections: {(dut_A, dut_B): link_count}
          e.g. {("sonic-dut-1","sonic-dut-2"): 4}
        """
        from itertools import combinations, permutations

        if not link_requirements:
            return free_duts[:needed]

        for combo in combinations(free_duts, needed):
            for perm in permutations(combo):
                # perm[0] → D1, perm[1] → D2, etc.
                role_map = {f"D{i+1}": name for i, name in enumerate(perm)}
                ok = True
                for (rA, rB), min_links in link_requirements.items():
                    dA = role_map.get(rA)
                    dB = role_map.get(rB)
                    if not dA or not dB:
                        ok = False
                        break
                    actual = (
                        self._topology_connections.get((dA, dB), 0)
                        or self._topology_connections.get((dB, dA), 0)
                    )
                    if actual < min_links:
                        ok = False
                        break
                if ok:
                    return list(perm)
        return None

    def _fire_status(self):
        snap = {
            "free_duts": self._free_names(),
            "busy_duts": [s.name for s in self._slots.values() if s.busy],
        }
        for cb in self._status_callbacks:
            try:
                cb(snap)
            except Exception:
                pass
