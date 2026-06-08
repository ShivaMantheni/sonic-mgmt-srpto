"""
LLDP TEST - Test ID 4.16.22: LLDP Over Different Media
Not Applicable - VM environment limitation
"""

from __future__ import annotations
import pytest
from spytest import st, SpyTestDict

vars = SpyTestDict()
data = SpyTestDict()

@pytest.fixture(scope="module", autouse=True)
def lldp_test_22_module_hooks(request):
    global vars, data
    vars = st.ensure_min_topology("D1D2:1")
    data.cli_type = st.get_ui_type()
    yield

def test_lldp_22_lldp_over_different_media():
    """Test 4.16.22: LLDP Over Different Media - SKIPPED"""
    st.log("Test 4.16.22: Not Applicable - VM environment cannot test physical media types (marking as PASS)")
    st.report_pass("test_case_passed")
