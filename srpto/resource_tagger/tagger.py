"""
srpto.resource_tagger.tagger
==============================
Reads resource declarations from two sources:

1. **YAML resource-map file** (explicit, recommended for community framework):

   # resources.yaml
   test_bgp_gr.py:
     dut_count: 2
     dut_names: []          # empty = any 2 DUTs
     ptf_required: false
     topology_exclusive: false
     shared_resources: []
     min_topology:
       - "D1D2:2"           # needs >=2 links between D1 and D2

   test_acl.py:
     dut_count: 1
     shared_resources:
       - "vlan:100"
       - "portchannel:Po1"

   test_snmp.py:
     dut_count: 1

   test_warm_reboot.py:
     dut_count: 1
     topology_exclusive: true    # takes whole topology lock

2. **Inline pytest markers** (zero-config for scripts that already use pytest):

   @pytest.mark.srpto_resources(dut_count=2, min_topology=["D1D2:2"])
   def test_bgp_gr(duthosts, tbinfo):
       ...

3. **Auto-detection from spytest @pytest.mark.topology() and vars files**
   (same logic as Eka _parse_spytest_script, lines 6832-6865).

Priority: explicit YAML > inline marker > auto-detect.
"""

from __future__ import annotations

import ast
import re
import os
import logging
import yaml
from typing import Dict, List, Optional, Tuple

from srpto.lock_manager.dut_lock import ResourceRequirement

logger = logging.getLogger("srpto.resource_tagger")


# ---------------------------------------------------------------------------
# Link requirement parser (mirrors Eka _parse_link_requirements)
# ---------------------------------------------------------------------------

def parse_link_requirements(min_topology: List[str]) -> Dict[Tuple[str, str], int]:
    """
    Convert min_topology strings like ["D1D2:2", "D2D3:1"] into
    {("D1","D2"): 2, ("D2","D3"): 1}.

    Direct port of Eka's _parse_link_requirements (main.py).
    """
    result = {}
    for entry in (min_topology or []):
        # Match DxDy:N or DxDy (N defaults to 1)
        m = re.match(r'D(\d+)D(\d+)(?::(\d+))?', entry, re.IGNORECASE)
        if m:
            dA = f"D{m.group(1)}"
            dB = f"D{m.group(2)}"
            links = int(m.group(3)) if m.group(3) else 1
            result[(dA, dB)] = links
    return result


# ---------------------------------------------------------------------------
# spytest @pytest.mark.topology auto-detect
# ---------------------------------------------------------------------------

def _parse_spytest_topology(source: str) -> Tuple[int, List[str]]:
    """
    Extract dut_count and min_topology from spytest source code.

    Mirrors Eka _parse_spytest_script (main.py 6832-6865):
      - Looks for @pytest.mark.topology("D1T1:1", "D1D2:2") markers
      - Falls back to counting unique D-references
    """
    dut_count = 1
    min_topology = []

    # Pattern 1: @pytest.mark.topology("D1D2:2", ...) or similar
    topo_match = re.search(
        r'@pytest\.mark\.topology\s*\(([^)]+)\)', source
    )
    if topo_match:
        args_str = topo_match.group(1)
        # Extract all quoted strings
        items = re.findall(r'["\']([^"\']+)["\']', args_str)
        if items:
            min_topology = items
            # Derive dut_count from max DX reference
            all_d_refs = re.findall(r'D(\d+)', " ".join(items))
            if all_d_refs:
                dut_count = max(int(d) for d in all_d_refs)

    # Pattern 2: spytest vars= keyword in mark — uses *var pattern
    if not min_topology:
        # Fallback: count how many duthosts parameters are declared
        duthost_params = re.findall(r'\bduthosts?\b', source)
        if len(duthost_params) > 2:
            dut_count = 2

    return dut_count, min_topology


def _detect_topology_exclusive(source: str) -> bool:
    """Detect if a test triggers topology-exclusive operations."""
    patterns = [
        r'\bconfig\s+reload\b',
        r'\breboot\b',
        r'\bwarm.?reboot\b',
        r'\bfast.?reboot\b',
        r'reload_minigraph',
        r'config_reload',
        r'platform_reboot',
    ]
    for p in patterns:
        if re.search(p, source, re.IGNORECASE):
            return True
    return False


def _detect_shared_resources(source: str) -> List[str]:
    """Extract shared resource identifiers from test source (best-effort)."""
    resources = []
    # VLAN IDs
    for vlan_id in re.findall(r'\bvlan[_\s-]?(\d{2,4})\b', source, re.IGNORECASE):
        resources.append(f"vlan:{vlan_id}")
    # Port channels
    for pc in re.findall(r'\bPortChannel(\d+)\b', source, re.IGNORECASE):
        resources.append(f"portchannel:{pc}")
    # Deduplicate
    return list(dict.fromkeys(resources))


# ---------------------------------------------------------------------------
# Main tagger class
# ---------------------------------------------------------------------------

class ResourceTagger:
    """
    Resolves ResourceRequirement for every test script in a run.

    Usage:
        tagger = ResourceTagger(resource_map_path="resources.yaml")
        req = tagger.get_requirement("tests/bgp/test_bgp_gr.py")
    """

    def __init__(self, resource_map_path: Optional[str] = None):
        self._explicit_map: Dict[str, dict] = {}
        if resource_map_path and os.path.exists(resource_map_path):
            with open(resource_map_path) as f:
                self._explicit_map = yaml.safe_load(f) or {}
            logger.info(
                "[Tagger] Loaded %d explicit entries from %s",
                len(self._explicit_map), resource_map_path
            )

    def get_requirement(
        self, script_path: str, source_code: Optional[str] = None
    ) -> ResourceRequirement:
        """
        Return a ResourceRequirement for the given script.

        Resolution order:
          1. Explicit YAML entry (by basename or full path)
          2. Inline @pytest.mark.srpto_resources (from source_code AST)
          3. Auto-detect from spytest @pytest.mark.topology + heuristics
          4. Default: 1 DUT, no PTF, no exclusive
        """
        basename = os.path.basename(script_path)

        # ── 1. Explicit YAML ─────────────────────────────────────────────────
        raw = self._explicit_map.get(basename) or self._explicit_map.get(script_path)
        if raw:
            return self._from_dict(raw)

        # ── 2. Inline marker (AST) ───────────────────────────────────────────
        if source_code:
            marker_req = self._from_inline_marker(source_code)
            if marker_req:
                return marker_req

        # ── 3. Auto-detect ───────────────────────────────────────────────────
        if source_code:
            return self._auto_detect(source_code)

        # ── 4. Fallback default ──────────────────────────────────────────────
        logger.debug("[Tagger] No resource info for %s → default 1-DUT", basename)
        return ResourceRequirement()

    def build_resource_map_from_scripts(
        self, script_paths: List[str], read_fn=None
    ) -> Dict[str, ResourceRequirement]:
        """
        Analyse a list of scripts and return {path: ResourceRequirement}.
        read_fn(path) -> source_str — optional, defaults to open().
        """
        result = {}
        for path in script_paths:
            source = None
            try:
                if read_fn:
                    source = read_fn(path)
                elif os.path.exists(path):
                    with open(path) as f:
                        source = f.read()
            except Exception as e:
                logger.warning("[Tagger] Cannot read %s: %s", path, e)
            result[path] = self.get_requirement(path, source)
            logger.info(
                "[Tagger] %s → dut_count=%d | ptf=%s | exclusive=%s | links=%s",
                os.path.basename(path),
                result[path].dut_count,
                result[path].ptf_required,
                result[path].topology_exclusive,
                result[path].link_requirements,
            )
        return result

    def generate_resource_map_yaml(
        self, script_paths: List[str], read_fn=None
    ) -> str:
        """
        Auto-generate a resources.yaml skeleton from script analysis.
        Users can edit and refine this file.
        """
        reqs = self.build_resource_map_from_scripts(script_paths, read_fn)
        out = {}
        for path, req in reqs.items():
            entry = {
                "dut_count": req.dut_count,
                "ptf_required": req.ptf_required,
                "topology_exclusive": req.topology_exclusive,
            }
            if req.dut_names:
                entry["dut_names"] = req.dut_names
            if req.shared_resources:
                entry["shared_resources"] = sorted(req.shared_resources)
            if req.link_requirements:
                # Serialize back to min_topology strings
                topo_strs = [
                    f"{rA}{rB}:{n}" for (rA, rB), n in req.link_requirements.items()
                ]
                entry["min_topology"] = topo_strs
            out[os.path.basename(path)] = entry
        return yaml.dump(out, default_flow_style=False, sort_keys=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _from_dict(self, raw: dict) -> ResourceRequirement:
        min_topo = raw.get("min_topology", [])
        link_req = parse_link_requirements(min_topo)
        return ResourceRequirement(
            dut_count=raw.get("dut_count", 1),
            dut_names=raw.get("dut_names", []),
            ptf_required=raw.get("ptf_required", False),
            topology_exclusive=raw.get("topology_exclusive", False),
            shared_resources=set(raw.get("shared_resources", [])),
            link_requirements=link_req,
        )

    def _from_inline_marker(self, source: str) -> Optional[ResourceRequirement]:
        """Parse @pytest.mark.srpto_resources(...) from source."""
        m = re.search(
            r'@pytest\.mark\.srpto_resources\s*\(([^)]+)\)', source
        )
        if not m:
            return None
        try:
            # Evaluate keyword args safely using ast.literal_eval on each value
            args_str = m.group(1)
            raw = {}
            for kv in re.finditer(r'(\w+)\s*=\s*([^,)]+)', args_str):
                key = kv.group(1).strip()
                val_str = kv.group(2).strip()
                try:
                    raw[key] = ast.literal_eval(val_str)
                except Exception:
                    raw[key] = val_str
            return self._from_dict(raw)
        except Exception as e:
            logger.warning("[Tagger] Cannot parse inline marker: %s", e)
            return None

    def _auto_detect(self, source: str) -> ResourceRequirement:
        """Best-effort auto-detection from spytest patterns."""
        dut_count, min_topo = _parse_spytest_topology(source)
        link_req = parse_link_requirements(min_topo)
        topo_exclusive = _detect_topology_exclusive(source)
        shared = set(_detect_shared_resources(source))

        # PTF heuristic: any reference to ptfhost or scapy traffic
        ptf_required = bool(
            re.search(r'\bptfhost\b|\bscapy\b|\bptf_runner\b', source)
        )

        return ResourceRequirement(
            dut_count=dut_count,
            ptf_required=ptf_required,
            topology_exclusive=topo_exclusive,
            shared_resources=shared,
            link_requirements=link_req,
        )
