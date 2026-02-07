"""
Fast YAML parser for Python with C++/SIMD backend.

This module provides a fast YAML parser implemented in C++ with SIMD optimizations.
API compatible with PyYAML for typical config use cases (Kubernetes, Ansible, CI, Docker Compose).
"""
from __future__ import annotations

import re
from typing import Any, BinaryIO, TextIO, Union

try:
    from ._native import loads as _loads, load_all as _load_all
    from ._dump import dump as _dump, dump_all as _dump_all
except ImportError as e:
    raise ImportError(
        "pyfastyaml native extension not found. "
        "Make sure the package is properly installed."
    ) from e


def _get_version() -> str:
    try:
        from importlib.metadata import version
        return version("pyfastyaml")
    except Exception:
        pass
    try:
        from pathlib import Path
        path = Path(__file__).resolve().parents[1] / "pyproject.toml"
        if path.exists():
            m = re.search(r'version\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"))
            return m.group(1) if m else "0.0.0"
    except Exception:
        pass
    return "0.0.0"


__version__ = _get_version()

__all__ = ["loads", "load", "load_all", "dump", "dump_all", "__version__"]


def loads(s: str) -> dict | list:
    """
    Parse a YAML string and return a dictionary or list.

    Args:
        s: The YAML string to parse

    Returns:
        dict or list: Parsed YAML data (root mapping or sequence)

    Raises:
        ValueError: If parsing fails

    Example:
        >>> import pyfastyaml
        >>> data = pyfastyaml.loads('key: value')
        >>> print(data)
        {'key': 'value'}
    """
    try:
        return _loads(s)
    except RuntimeError as e:
        raise ValueError(str(e)) from e


def load(fp: Union[str, BinaryIO, TextIO]) -> dict | list:
    """
    Parse a YAML file and return a dictionary or list.

    Args:
        fp: File path (str) or file-like object open for reading (text or binary).

    Returns:
        Parsed YAML data (dict or list).

    Raises:
        ValueError: If the content is not valid YAML.
        FileNotFoundError: If fp is a path and the file does not exist.
        OSError: If the file cannot be read.
    """
    if hasattr(fp, 'read'):
        content = fp.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        return loads(content)
    else:
        with open(fp, 'r', encoding='utf-8') as f:
            return loads(f.read())


def load_all(s: str | Union[str, BinaryIO, TextIO]) -> list:
    """
    Parse all YAML documents in a multi-document stream.

    Args:
        s: YAML string or file path / file-like object.

    Returns:
        List of parsed documents (dict or list each).

    Raises:
        ValueError: If parsing fails.

    Example:
        >>> import pyfastyaml
        >>> docs = pyfastyaml.load_all('---\\na: 1\\n---\\nb: 2')
        >>> docs
        [{'a': 1}, {'b': 2}]
    """
    if hasattr(s, 'read'):
        content = s.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        yaml_str = content
    else:
        yaml_str = s
    try:
        return _load_all(yaml_str)
    except RuntimeError as e:
        raise ValueError(str(e)) from e


def dump(
    data: Any,
    stream: TextIO | str | None = None,
    *,
    default_flow_style: bool = False,
    indent: int = 2,
    allow_unicode: bool = True,
    sort_keys: bool = False,
) -> str | None:
    """
    Serialize Python object to YAML string.

    Args:
        data: Object to serialize (dict, list, str, int, float, bool, None).
        stream: If provided, write to stream and return None. Can be file path (str).
        default_flow_style: Use flow style [a,b] and {a:1} for simple structures.
        indent: Indentation width (default 2).
        allow_unicode: Unused, for API compatibility with PyYAML.
        sort_keys: Sort mapping keys for deterministic output.

    Returns:
        YAML string if stream is None, else None.
    """
    return _dump(
        data, stream,
        default_flow_style=default_flow_style, indent=indent,
        allow_unicode=allow_unicode, sort_keys=sort_keys,
    )


def dump_all(
    documents: list,
    stream: TextIO | str | None = None,
    *,
    default_flow_style: bool = False,
    indent: int = 2,
    allow_unicode: bool = True,
    sort_keys: bool = False,
) -> str | None:
    """
    Serialize multiple documents to YAML stream.

    Args:
        documents: List of objects to serialize.
        stream: If provided, write to stream and return None. Can be file path (str).
        default_flow_style: Use flow style for simple structures.
        indent: Indentation width.
        allow_unicode: Unused, for API compatibility.
        sort_keys: Sort mapping keys for deterministic output.

    Returns:
        YAML string if stream is None, else None.
    """
    return _dump_all(
        documents, stream,
        default_flow_style=default_flow_style, indent=indent,
        allow_unicode=allow_unicode, sort_keys=sort_keys,
    )
