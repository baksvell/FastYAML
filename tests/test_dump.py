"""Tests for dump() and dump_all() serialization."""

import io
import tempfile
from pathlib import Path

import pytest
import pyfastyaml


def test_dump_simple_dict():
    """Test dumping a simple mapping."""
    data = {"a": 1, "b": 2}
    out = pyfastyaml.dump(data)
    assert "a: 1" in out
    assert "b: 2" in out
    loaded = pyfastyaml.loads(out)
    assert loaded == data


def test_dump_nested_dict():
    """Test dumping nested mappings."""
    data = {"outer": {"inner": "value", "num": 1}}
    out = pyfastyaml.dump(data)
    loaded = pyfastyaml.loads(out)
    assert loaded == data


def test_dump_list():
    """Test dumping a sequence."""
    data = [1, 2, "three"]
    out = pyfastyaml.dump(data)
    loaded = pyfastyaml.loads(out)
    assert loaded == data


def test_dump_nested_list():
    """Test dumping nested sequences. Block style roundtrips correctly."""
    data = [["a", "b"], ["c", "d"]]
    out = pyfastyaml.dump(data)  # block style
    loaded = pyfastyaml.loads(out)
    assert loaded == data


def test_dump_scalars():
    """Test dumping scalar types."""
    assert pyfastyaml.loads(pyfastyaml.dump(None)) is None
    assert pyfastyaml.loads(pyfastyaml.dump(True)) is True
    assert pyfastyaml.loads(pyfastyaml.dump(42)) == 42
    assert pyfastyaml.loads(pyfastyaml.dump(3.14)) == 3.14
    assert pyfastyaml.loads(pyfastyaml.dump("hello")) == "hello"


def test_dump_to_stream():
    """Test dumping to a stream."""
    data = {"x": 1}
    buf = io.StringIO()
    result = pyfastyaml.dump(data, stream=buf)
    assert result is None
    buf.seek(0)
    loaded = pyfastyaml.loads(buf.read())
    assert loaded == data


def test_dump_all():
    """Test dumping multiple documents."""
    docs = [{"a": 1}, {"b": 2}]
    out = pyfastyaml.dump_all(docs)
    assert "---" in out
    loaded = pyfastyaml.load_all(out)
    assert loaded == docs


def test_dump_all_to_stream():
    """Test dump_all to stream."""
    docs = [{"x": 1}, {"y": 2}]
    buf = io.StringIO()
    pyfastyaml.dump_all(docs, stream=buf)
    buf.seek(0)
    loaded = pyfastyaml.load_all(buf.read())
    assert loaded == docs


def test_roundtrip_complex():
    """Round-trip: loads(dump(x)) == x for complex data."""
    data = {
        "name": "app",
        "version": "1.0",
        "ports": [8000, 8001],
        "env": {"DEBUG": "true", "LOG_LEVEL": "info"},
        "nested": [{"id": 1, "active": True}, {"id": 2, "active": False}],
    }
    out = pyfastyaml.dump(data)
    loaded = pyfastyaml.loads(out)
    assert loaded == data


def test_roundtrip_multiline_string():
    """Round-trip with multiline string."""
    data = {"text": "line1\nline2\nline3"}
    out = pyfastyaml.dump(data)
    loaded = pyfastyaml.loads(out)
    assert loaded == data


def test_dump_empty_structures():
    """Test dumping empty dict and list."""
    assert pyfastyaml.loads(pyfastyaml.dump({})) == {}
    assert pyfastyaml.loads(pyfastyaml.dump([])) == []


def test_dump_flow_style():
    """Test dump with default_flow_style=True."""
    data = {"a": 1, "b": 2}
    out = pyfastyaml.dump(data, default_flow_style=True)
    assert "{" in out and "}" in out
    loaded = pyfastyaml.loads(out)
    assert loaded == data


def test_dump_to_path():
    """Test dumping to file path."""
    data = {"x": 1, "y": 2}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        path = f.name
    try:
        result = pyfastyaml.dump(data, stream=path)
        assert result is None
        loaded = pyfastyaml.loads(Path(path).read_text(encoding="utf-8"))
        assert loaded == data
    finally:
        Path(path).unlink(missing_ok=True)


def test_dump_all_to_path():
    """Test dump_all to file path."""
    docs = [{"a": 1}, {"b": 2}]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        path = f.name
    try:
        pyfastyaml.dump_all(docs, stream=path)
        loaded = pyfastyaml.load_all(Path(path).read_text(encoding="utf-8"))
        assert loaded == docs
    finally:
        Path(path).unlink(missing_ok=True)


def test_dump_sort_keys():
    """Test sort_keys produces deterministic output."""
    data = {"z": 3, "a": 1, "m": 2}
    out1 = pyfastyaml.dump(data, sort_keys=True)
    out2 = pyfastyaml.dump(data, sort_keys=True)
    assert out1 == out2
    assert out1.index("a:") < out1.index("m:") < out1.index("z:")
    assert pyfastyaml.loads(out1) == data
