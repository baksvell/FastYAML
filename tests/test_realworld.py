"""
Real-world YAML tests.

Parse config-style YAML (K8s, Docker Compose, CI, Ansible) with FastYAML
and optionally compare with PyYAML.
"""

import pathlib

import pytest
import pyfastyaml

SAMPLES_DIR = pathlib.Path(__file__).parent / "realworld_samples"

REALWORLD_FILES = [
    "k8s-deployment.yaml",
    "docker-compose.yaml",
    "github-actions.yml",
    "ansible-playbook.yaml",
    "prometheus-config.yaml",
]


@pytest.mark.parametrize("filename", REALWORLD_FILES)
def test_realworld_parse(filename):
    """Parse real-world YAML with FastYAML - no crash, returns dict or list."""
    path = SAMPLES_DIR / filename
    if not path.exists():
        pytest.skip(f"Sample not found: {path}")
    content = path.read_text(encoding="utf-8")
    result = pyfastyaml.loads(content)
    assert result is not None
    assert isinstance(result, (dict, list))


@pytest.mark.parametrize("filename", REALWORLD_FILES)
def test_realworld_vs_pyyaml(filename):
    """Real-world samples: FastYAML result equals PyYAML."""
    try:
        import yaml
    except ImportError:
        pytest.skip("PyYAML not installed")
    path = SAMPLES_DIR / filename
    if not path.exists():
        pytest.skip(f"Sample not found: {path}")
    content = path.read_text(encoding="utf-8")
    fy = pyfastyaml.loads(content)
    py = yaml.safe_load(content)
    assert fy == py, f"Mismatch in {filename}"


def test_realworld_k8s_structure():
    """K8s deployment: expected keys present."""
    path = SAMPLES_DIR / "k8s-deployment.yaml"
    content = path.read_text(encoding="utf-8")
    data = pyfastyaml.loads(content)
    assert "apiVersion" in data
    assert data["kind"] == "Deployment"
    assert "metadata" in data
    assert "spec" in data
    assert data["spec"]["replicas"] == 3
    assert len(data["spec"]["template"]["spec"]["containers"]) == 1
    container = data["spec"]["template"]["spec"]["containers"][0]
    assert container["image"] == "nginx:1.14.2"
    assert "resources" in container
    assert "ports" in container


def test_realworld_docker_compose_structure():
    """Docker Compose: services parsed."""
    path = SAMPLES_DIR / "docker-compose.yaml"
    content = path.read_text(encoding="utf-8")
    data = pyfastyaml.loads(content)
    assert "services" in data
    assert "web" in data["services"]
    assert "db" in data["services"]
    assert data["services"]["web"]["image"] == "nginx:alpine"
    assert "depends_on" in data["services"]["web"]
    assert "db" in data["services"]["web"]["depends_on"]


def test_realworld_ansible_structure():
    """Ansible playbook: root sequence of plays."""
    path = SAMPLES_DIR / "ansible-playbook.yaml"
    content = path.read_text(encoding="utf-8")
    data = pyfastyaml.loads(content)
    assert isinstance(data, list)
    assert len(data) >= 1
    play = data[0]
    assert "name" in play
    assert "hosts" in play
    assert "tasks" in play
    assert play["hosts"] == "webservers"
