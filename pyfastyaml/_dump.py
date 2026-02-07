"""YAML dump (serialization) - pure Python implementation."""

from __future__ import annotations

import math
from typing import Any, TextIO


# Chars that require quoting in YAML plain scalars
_NEEDS_QUOTE = frozenset(":{}[],#&*!|>'\"%@`\n\r\t")


def _needs_quotes(s: str) -> bool:
    """Check if string needs quoting."""
    if not s or s in ("true", "false", "null", "~", "yes", "no", ".inf", "-.inf", ".nan"):
        return True
    if s[0] in " -?" or s[-1] in " :":
        return True
    if any(c in _NEEDS_QUOTE for c in s):
        return True
    try:
        float(s)
        return True  # Number-like: quote to avoid type coercion
    except ValueError:
        pass
    return False


def _escape_double(s: str) -> str:
    """Escape for double-quoted YAML string."""
    result = []
    for c in s:
        if c == "\\":
            result.append("\\\\")
        elif c == '"':
            result.append('\\"')
        elif c == "\n":
            result.append("\\n")
        elif c == "\r":
            result.append("\\r")
        elif c == "\t":
            result.append("\\t")
        elif ord(c) < 0x20:
            result.append(f"\\x{ord(c):02x}")
        else:
            result.append(c)
    return "".join(result)


def _dump_str(s: str) -> str:
    """Convert string to YAML representation."""
    if "\n" in s:
        # Multiline: use literal block (content indented; caller puts "|" on same line as key if needed)
        lines = s.split("\n")
        return "|\n" + "\n".join("  " + line for line in lines)
    if _needs_quotes(s):
        return '"' + _escape_double(s) + '"'
    return s


def _dump_value(
    obj: Any,
    indent: int,
    default_flow_style: bool,
    indent_step: int = 2,
    sort_keys: bool = False,
) -> str:
    """Serialize a single value."""
    if obj is None:
        return "null"
    if obj is True:
        return "true"
    if obj is False:
        return "false"
    if isinstance(obj, int):
        return str(obj)
    if isinstance(obj, float):
        if math.isnan(obj):
            return ".nan"
        if math.isinf(obj):
            return "-.inf" if obj < 0 else ".inf"
        s = repr(obj)
        if "e" in s.lower():
            return s
        return s if "." in s else s + ".0"
    if isinstance(obj, str):
        return _dump_str(obj)
    if isinstance(obj, dict):
        return _dump_mapping(obj, indent, default_flow_style, indent_step, sort_keys)
    if isinstance(obj, (list, tuple)):
        return _dump_sequence(obj, indent, default_flow_style, indent_step, sort_keys)
    return _dump_str(str(obj))


def _dump_mapping(
    d: dict,
    indent: int,
    default_flow_style: bool,
    indent_step: int,
    sort_keys: bool = False,
) -> str:
    """Serialize mapping to YAML block or flow style."""
    if not d:
        return "{}"
    items = sorted(d.items(), key=lambda x: str(x[0])) if sort_keys else d.items()
    if default_flow_style and all(
        not isinstance(v, (dict, list)) or (isinstance(v, (dict, list)) and len(v) == 0)
        for v in d.values()
    ):
        # Simple flow mapping
        parts = []
        for k, v in items:
            key = _dump_str(str(k)) if _needs_quotes(str(k)) else str(k)
            val = _dump_value(v, 0, False, indent_step, sort_keys)
            parts.append(f"{key}: {val}")
        return "{" + ", ".join(parts) + "}"
    lines = []
    prefix = " " * indent
    for k, v in items:
        key_str = str(k)
        if _needs_quotes(key_str):
            key_str = '"' + _escape_double(key_str) + '"'
        val = _dump_value(v, indent + indent_step, default_flow_style, indent_step, sort_keys)
        if "\n" in val:
            if val.startswith("|\n"):
                # Literal block: put "|" on same line as key for parser compatibility
                rest = val[2:]  # skip "|\n"
                lines.append(f"{prefix}{key_str}: |")
                for line in rest.split("\n"):
                    lines.append(prefix + line)
            else:
                lines.append(f"{prefix}{key_str}:")
                for line in val.split("\n"):
                    lines.append(line)
        else:
            lines.append(f"{prefix}{key_str}: {val}")
    return "\n".join(lines)


def _dump_sequence(
    seq: list | tuple,
    indent: int,
    default_flow_style: bool,
    indent_step: int,
    sort_keys: bool = False,
) -> str:
    """Serialize sequence to YAML block or flow style."""
    if not seq:
        return "[]"
    if default_flow_style and all(
        not isinstance(v, (dict, list)) or (isinstance(v, (dict, list)) and len(v) == 0)
        for v in seq
    ):
        parts = [_dump_value(v, 0, False, indent_step, sort_keys) for v in seq]
        return "[" + ", ".join(parts) + "]"
    lines = []
    prefix = " " * indent
    item_indent = " " * (indent + indent_step)
    for v in seq:
        val = _dump_value(v, indent + indent_step, default_flow_style, indent_step, sort_keys)
        if "\n" in val:
            val_lines = val.split("\n")
            first = val_lines[0]
            # Nested list: use block format "-" on own line for parser compatibility
            if first.strip().startswith("-"):
                lines.append(f"{prefix}-")
                for line in val_lines:
                    lines.append(line)
            else:
                # Mapping or other: put first line inline with "- "
                first_stripped = first[len(item_indent):] if first.startswith(item_indent) else first.strip()
                lines.append(f"{prefix}- {first_stripped}")
                for line in val_lines[1:]:
                    lines.append(line)
        else:
            lines.append(f"{prefix}- {val}")
    return "\n".join(lines)


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
        allow_unicode: Unused, for API compatibility.
        sort_keys: Sort mapping keys for deterministic output.

    Returns:
        YAML string if stream is None, else None.
    """
    result = _dump_value(data, 0, default_flow_style, indent, sort_keys)
    if stream is not None:
        if isinstance(stream, str):
            with open(stream, "w", encoding="utf-8") as f:
                f.write(result)
                f.write("\n")
        else:
            stream.write(result)
            stream.write("\n")
        return None
    return result + "\n"


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
    parts = []
    for i, doc in enumerate(documents):
        if i > 0:
            parts.append("---")
        parts.append(_dump_value(doc, 0, default_flow_style, indent, sort_keys))
    result = "\n".join(parts) + "\n"
    if stream is not None:
        if isinstance(stream, str):
            with open(stream, "w", encoding="utf-8") as f:
                f.write(result)
        else:
            stream.write(result)
        return None
    return result
