"""
Benchmarks: FastYAML vs PyYAML vs ruamel.yaml.

Run:
  pytest tests/test_benchmark.py -v --benchmark-only
  pytest tests/test_benchmark.py -v --benchmark-only --benchmark-autosave
  pytest tests/test_benchmark.py -v --benchmark-only -k "small"
  pytest tests/test_benchmark.py -v --benchmark-only --benchmark-compare
"""

import pytest

import pyfastyaml
from tests.benchmark_data import YAML_SMALL, YAML_MEDIUM, YAML_LARGE, YAML_REALWORLD

try:
    import yaml

    HAS_PYYAML = True
except ImportError:
    HAS_PYYAML = False

try:
    from ruamel.yaml import YAML

    ruamel_loader = YAML(typ="safe")
    HAS_RUAMEL = True
except ImportError:
    HAS_RUAMEL = False


def _pyyaml_loads(s: str):
    return yaml.safe_load(s)


def _ruamel_loads(s: str):
    from io import StringIO

    return ruamel_loader.load(StringIO(s))


# --- FastYAML ---

@pytest.mark.benchmark(group="small")
def test_bench_fastyaml_small(benchmark):
    """Parse small YAML (~200 bytes) with FastYAML."""
    result = benchmark(pyfastyaml.loads, YAML_SMALL)
    assert "title" in result


@pytest.mark.benchmark(group="medium")
def test_bench_fastyaml_medium(benchmark):
    """Parse medium YAML (~1.5 KB) with FastYAML."""
    result = benchmark(pyfastyaml.loads, YAML_MEDIUM)
    assert "title" in result and "owner" in result and "database" in result


@pytest.mark.benchmark(group="large")
def test_bench_fastyaml_large(benchmark):
    """Parse large YAML (~15 KB) with FastYAML."""
    result = benchmark(pyfastyaml.loads, YAML_LARGE)
    assert "title" in result


@pytest.mark.benchmark(group="realworld")
def test_bench_fastyaml_realworld(benchmark):
    """Parse real-world style YAML with FastYAML."""
    result = benchmark(pyfastyaml.loads, YAML_REALWORLD)
    assert "name" in result and "version" in result


# --- PyYAML ---

@pytest.mark.benchmark(group="small")
@pytest.mark.skipif(not HAS_PYYAML, reason="PyYAML not installed")
def test_bench_pyyaml_small(benchmark):
    """Parse small YAML with PyYAML."""
    result = benchmark(_pyyaml_loads, YAML_SMALL)
    assert "title" in result


@pytest.mark.benchmark(group="medium")
@pytest.mark.skipif(not HAS_PYYAML, reason="PyYAML not installed")
def test_bench_pyyaml_medium(benchmark):
    """Parse medium YAML with PyYAML."""
    result = benchmark(_pyyaml_loads, YAML_MEDIUM)
    assert "owner" in result


@pytest.mark.benchmark(group="large")
@pytest.mark.skipif(not HAS_PYYAML, reason="PyYAML not installed")
def test_bench_pyyaml_large(benchmark):
    """Parse large YAML with PyYAML."""
    result = benchmark(_pyyaml_loads, YAML_LARGE)
    assert "title" in result


@pytest.mark.benchmark(group="realworld")
@pytest.mark.skipif(not HAS_PYYAML, reason="PyYAML not installed")
def test_bench_pyyaml_realworld(benchmark):
    """Parse real-world YAML with PyYAML."""
    result = benchmark(_pyyaml_loads, YAML_REALWORLD)
    assert "name" in result


# --- ruamel.yaml ---

@pytest.mark.benchmark(group="small")
@pytest.mark.skipif(not HAS_RUAMEL, reason="ruamel.yaml not installed")
def test_bench_ruamel_small(benchmark):
    """Parse small YAML with ruamel.yaml."""
    result = benchmark(_ruamel_loads, YAML_SMALL)
    assert "title" in result


@pytest.mark.benchmark(group="medium")
@pytest.mark.skipif(not HAS_RUAMEL, reason="ruamel.yaml not installed")
def test_bench_ruamel_medium(benchmark):
    """Parse medium YAML with ruamel.yaml."""
    result = benchmark(_ruamel_loads, YAML_MEDIUM)
    assert "owner" in result


@pytest.mark.benchmark(group="large")
@pytest.mark.skipif(not HAS_RUAMEL, reason="ruamel.yaml not installed")
def test_bench_ruamel_large(benchmark):
    """Parse large YAML with ruamel.yaml."""
    result = benchmark(_ruamel_loads, YAML_LARGE)
    assert "title" in result


@pytest.mark.benchmark(group="realworld")
@pytest.mark.skipif(not HAS_RUAMEL, reason="ruamel.yaml not installed")
def test_bench_ruamel_realworld(benchmark):
    """Parse real-world YAML with ruamel.yaml."""
    result = benchmark(_ruamel_loads, YAML_REALWORLD)
    assert "name" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])
