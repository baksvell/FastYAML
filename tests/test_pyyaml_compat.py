"""
PyYAML compatibility tests.

Parse the same YAML with FastYAML and PyYAML (safe_load), compare results.
FastYAML MVP targets config-style YAML (K8s, Ansible, CI, Docker Compose).
"""

import pytest

import pyfastyaml
from tests.benchmark_data import YAML_SMALL, YAML_MEDIUM, YAML_LARGE, YAML_REALWORLD

try:
    import yaml
    HAS_PYYAML = True
except ImportError:
    HAS_PYYAML = False


def _deep_equal(a, b, path="root"):
    """Compare two parsed structures, return (equal, diff_message)."""
    if type(a) != type(b):
        return False, f"{path}: type {type(a).__name__} != {type(b).__name__}"
    if isinstance(a, dict):
        if set(a.keys()) != set(b.keys()):
            extra_fy = set(a) - set(b)
            extra_py = set(b) - set(a)
            msg = f"{path}: key mismatch"
            if extra_fy:
                msg += f" (FastYAML extra: {extra_fy})"
            if extra_py:
                msg += f" (PyYAML extra: {extra_py})"
            return False, msg
        for k in a:
            ok, msg = _deep_equal(a[k], b[k], f"{path}.{k}")
            if not ok:
                return False, msg
        return True, ""
    if isinstance(a, list):
        if len(a) != len(b):
            return False, f"{path}: list len {len(a)} != {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            ok, msg = _deep_equal(x, y, f"{path}[{i}]")
            if not ok:
                return False, msg
        return True, ""
    if a != b:
        return False, f"{path}: {repr(a)} != {repr(b)}"
    return True, ""


def _both_load(yaml_str):
    """Parse with both libraries. Skip if PyYAML unavailable."""
    if not HAS_PYYAML:
        pytest.skip("PyYAML not installed")
    fy = pyfastyaml.loads(yaml_str)
    py = yaml.safe_load(yaml_str)
    return fy, py


@pytest.mark.skipif(not HAS_PYYAML, reason="PyYAML not installed")
class TestPyYAMLCompat:
    """Parse same YAML with FastYAML and PyYAML, assert equal results."""

    def test_benchmark_small(self):
        fy, py = _both_load(YAML_SMALL)
        ok, msg = _deep_equal(fy, py)
        assert ok, msg

    def test_benchmark_medium(self):
        fy, py = _both_load(YAML_MEDIUM)
        ok, msg = _deep_equal(fy, py)
        assert ok, msg

    def test_benchmark_large(self):
        fy, py = _both_load(YAML_LARGE)
        ok, msg = _deep_equal(fy, py)
        assert ok, msg

    def test_benchmark_realworld(self):
        fy, py = _both_load(YAML_REALWORLD)
        ok, msg = _deep_equal(fy, py)
        assert ok, msg

    def test_simple_mapping(self):
        s = "a: 1\nb: two\nc: true"
        fy, py = _both_load(s)
        ok, msg = _deep_equal(fy, py)
        assert ok, msg

    def test_nested_and_sequences(self):
        """Block-style sequences only (FastYAML MVP does not support flow [a,b])."""
        s = """
x:
  a: 1
  b:
    - 1
    - 2
    - 3
y:
  - name: foo
    val: 1
  - name: bar
    val: 2
"""
        fy, py = _both_load(s)
        ok, msg = _deep_equal(fy, py)
        assert ok, msg

    def test_null_and_empty_string(self):
        s = 'a: null\nb: ""\nc:'
        fy, py = _both_load(s)
        ok, msg = _deep_equal(fy, py)
        assert ok, msg

    def test_ip_address_as_string(self):
        """Both should treat 192.168.1.1 as string (PyYAML safe_load does)."""
        s = "host: 192.168.1.1"
        fy, py = _both_load(s)
        assert fy["host"] == py["host"] == "192.168.1.1"
