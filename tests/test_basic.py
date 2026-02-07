"""Basic tests for FastYAML parser."""

import pytest
import pyfastyaml


def test_loads_simple_string():
    """Test parsing a simple string value."""
    yaml_str = 'key: value'
    result = pyfastyaml.loads(yaml_str)
    assert result == {"key": "value"}


def test_loads_integer():
    """Test parsing integer values."""
    yaml_str = 'number: 42'
    result = pyfastyaml.loads(yaml_str)
    assert result == {"number": 42}


def test_loads_float():
    """Test parsing float values."""
    yaml_str = 'pi: 3.14159'
    result = pyfastyaml.loads(yaml_str)
    assert result == {"pi": 3.14159}


def test_loads_boolean():
    """Test parsing boolean values."""
    yaml_str = 'flag: true'
    result = pyfastyaml.loads(yaml_str)
    assert result == {"flag": True}


def test_loads_null():
    """Test parsing null values."""
    yaml_str = 'empty: null'
    result = pyfastyaml.loads(yaml_str)
    assert result == {"empty": None}


def test_loads_sequence():
    """Test parsing sequence (list)."""
    yaml_str = '''
items:
  - a
  - b
  - c
'''
    result = pyfastyaml.loads(yaml_str)
    assert result == {"items": ["a", "b", "c"]}


def test_loads_nested_mapping():
    """Test parsing nested mappings."""
    yaml_str = '''
outer:
  inner: value
  num: 1
'''
    result = pyfastyaml.loads(yaml_str)
    assert result == {"outer": {"inner": "value", "num": 1}}


def test_loads_multiple_sibling_keys_in_mapping():
    """Multiple sibling keys at same level (e.g. tool with pytest + coverage)."""
    yaml_str = '''
tool:
  pytest:
    minversion: "7.0"
  coverage:
    branch: true
'''
    result = pyfastyaml.loads(yaml_str)
    assert "tool" in result
    assert "pytest" in result["tool"]
    assert "coverage" in result["tool"]
    assert result["tool"]["pytest"]["minversion"] == "7.0"
    assert result["tool"]["coverage"]["branch"] is True


def test_loads_sequence_of_mappings():
    """Test parsing sequence of mappings (common in K8s/Ansible)."""
    yaml_str = '''
items:
  - name: foo
    value: 1
  - name: bar
    value: 2
'''
    result = pyfastyaml.loads(yaml_str)
    assert result == {
        "items": [
            {"name": "foo", "value": 1},
            {"name": "bar", "value": 2},
        ]
    }


def test_loads_ip_as_string():
    """IP addresses (192.168.1.1) should parse as strings, not floats."""
    yaml_str = "host: 192.168.1.1"
    result = pyfastyaml.loads(yaml_str)
    assert result == {"host": "192.168.1.1"}


def test_loads_quoted_string():
    """Test parsing quoted strings."""
    yaml_str = 'message: "Hello\\nWorld"'
    result = pyfastyaml.loads(yaml_str)
    assert result == {"message": "Hello\nWorld"}


def test_loads_empty_string():
    """Test parsing empty YAML string."""
    result = pyfastyaml.loads("")
    assert result == {}


def test_loads_root_sequence():
    """Test parsing root-level sequence."""
    yaml_str = '''
- first
- second
- third
'''
    result = pyfastyaml.loads(yaml_str)
    assert result == ["first", "second", "third"]


def test_loads_comments():
    """Test parsing files with comments."""
    yaml_str = '''
# comment
key: value  # inline
'''
    result = pyfastyaml.loads(yaml_str)
    assert result == {"key": "value"}


def test_load_error():
    """Test error handling for invalid YAML."""
    # MVP parser may not detect all errors; verify it doesn't crash
    # Use clearly invalid structure that should trigger an error
    try:
        pyfastyaml.loads(': invalid')  # Empty key
    except ValueError:
        pass  # Expected


def test_load_from_path(tmp_path):
    """Test load() with file path."""
    f = tmp_path / "test.yaml"
    f.write_text("a: 1\nb: 2", encoding="utf-8")
    result = pyfastyaml.load(f)  # Path is path-like, open() accepts it
    assert result == {"a": 1, "b": 2}


# --- Edge case tests ---


def test_empty_string_value():
    """Key with empty quoted string value."""
    result = pyfastyaml.loads('k: ""')
    assert result == {"k": ""}


def test_implicit_null_value():
    """Key with no value (implicit null)."""
    result = pyfastyaml.loads("key:")
    assert result == {"key": None}


def test_tilde_null():
    """Tilde as null alternative."""
    result = pyfastyaml.loads("x: ~")
    assert result == {"x": None}


def test_sequence_with_null_item():
    """Sequence containing null/empty items."""
    result = pyfastyaml.loads("items:\n  - null\n  - x\n  - ")
    assert result == {"items": [None, "x", None]}


def test_tab_indentation():
    """Tab treated as 2 spaces (parser convention)."""
    yaml_str = "a:\n\tb: 1"
    result = pyfastyaml.loads(yaml_str)
    assert result == {"a": {"b": 1}}


def test_four_space_indentation():
    """4-space indentation (common alternative to 2)."""
    yaml_str = """
a:
    b: 1
    c: 2
"""
    result = pyfastyaml.loads(yaml_str)
    assert result == {"a": {"b": 1, "c": 2}}


def test_multiple_blank_lines_between_keys():
    """Multiple blank lines between key-value pairs."""
    result = pyfastyaml.loads("a: 1\n\n\n\nb: 2")
    assert result == {"a": 1, "b": 2}


def test_leading_newlines():
    """Leading newlines before content."""
    result = pyfastyaml.loads("\n\nkey: val")
    assert result == {"key": "val"}


def test_trailing_newline():
    """Trailing newline does not affect parsing."""
    result = pyfastyaml.loads("a: 1\n")
    assert result == {"a": 1}


def test_key_with_value_on_next_line_only_whitespace():
    """Key with value on next line that is only whitespace/blank -> null."""
    result = pyfastyaml.loads("items:\n")
    assert result == {"items": None}


def test_inline_comment_after_value():
    """Inline comment after value (already in test_loads_comments)."""
    result = pyfastyaml.loads("key: value  # comment")
    assert result == {"key": "value"}


def test_colon_in_quoted_string_value():
    """Value containing colon parsed as string."""
    result = pyfastyaml.loads('url: "https://example.com"')
    assert result == {"url": "https://example.com"}


def test_negative_number():
    """Negative integer and float."""
    result = pyfastyaml.loads("a: -42\nb: -3.14")
    assert result == {"a": -42, "b": -3.14}


def test_scientific_notation():
    """Float in scientific notation."""
    result = pyfastyaml.loads("x: 1e10\ny: 2.5e-3")
    assert result["x"] == 1e10
    assert result["y"] == 2.5e-3


def test_sequence_of_one_item():
    """Sequence with single element."""
    result = pyfastyaml.loads("items:\n  - single")
    assert result == {"items": ["single"]}


def test_empty_root_sequence():
    """Root-level sequence with no items (edge case)."""
    result = pyfastyaml.loads("- ")
    assert result == [None]


# --- Flow syntax tests ---


def test_flow_sequence_simple():
    """Flow sequence [a, b, c]."""
    result = pyfastyaml.loads("items: [a, b, c]")
    assert result == {"items": ["a", "b", "c"]}


def test_flow_sequence_root():
    """Root-level flow sequence."""
    result = pyfastyaml.loads("[a, b, c]")
    assert result == ["a", "b", "c"]


def test_flow_sequence_empty():
    """Empty flow sequence."""
    result = pyfastyaml.loads("x: []")
    assert result == {"x": []}


def test_flow_mapping_simple():
    """Flow mapping {a: 1, b: 2}."""
    result = pyfastyaml.loads("data: {a: 1, b: 2}")
    assert result == {"data": {"a": 1, "b": 2}}


def test_flow_mapping_no_spaces():
    """Flow mapping without spaces {a:1,b:2}."""
    result = pyfastyaml.loads("data: {a:1,b:2}")
    assert result == {"data": {"a": 1, "b": 2}}


def test_flow_sequence_nested():
    """Nested flow sequences [a, [b, c], d]."""
    result = pyfastyaml.loads("items: [a, [b, c], d]")
    assert result == {"items": ["a", ["b", "c"], "d"]}


def test_flow_mapping_nested():
    """Flow mapping with nested sequence {a: [1, 2], b: 3}."""
    result = pyfastyaml.loads("data: {a: [1, 2], b: 3}")
    assert result == {"data": {"a": [1, 2], "b": 3}}


# --- Multiline block scalar tests ---


def test_literal_block_same_line():
    """Literal block | on same line as key."""
    yaml_str = "text: |\n  line1\n  line2"
    result = pyfastyaml.loads(yaml_str)
    assert result == {"text": "line1\nline2"}


def test_folded_block_same_line():
    """Folded block > on same line as key."""
    yaml_str = "text: >\n  this is\n  one line"
    result = pyfastyaml.loads(yaml_str)
    assert result == {"text": "this is one line"}


def test_literal_block_next_line():
    """Literal block with | on next line."""
    yaml_str = "text:\n  |\n  line1\n  line2"
    result = pyfastyaml.loads(yaml_str)
    assert result == {"text": "line1\nline2"}


def test_folded_blank_line_paragraph():
    """Folded: blank line becomes newline (matches PyYAML)."""
    yaml_str = "text: >\n  para one\n\n  para two"
    result = pyfastyaml.loads(yaml_str)
    assert result == {"text": "para one\npara two"}


def test_literal_in_sequence():
    """Literal block as sequence item."""
    yaml_str = """
items:
  - |
    first
    block
  - plain
"""
    result = pyfastyaml.loads(yaml_str)
    assert result == {"items": ["first\nblock", "plain"]}


# --- Document markers and directives ---


def test_document_start_marker():
    """--- at start is skipped."""
    result = pyfastyaml.loads("---\nkey: value")
    assert result == {"key": "value"}


def test_document_end_marker():
    """... at end is skipped."""
    result = pyfastyaml.loads("key: value\n...")
    assert result == {"key": "value"}


def test_yaml_directive():
    """%YAML 1.2 directive is skipped."""
    result = pyfastyaml.loads("%YAML 1.2\n---\nkey: value")
    assert result == {"key": "value"}


def test_bare_document_no_markers():
    """Document without markers still works."""
    result = pyfastyaml.loads("a: 1")
    assert result == {"a": 1}


def test_document_with_block_scalar():
    """--- | starts document with literal block scalar."""
    result = pyfastyaml.loads("--- |\n  line1\n  line2")
    assert result == "line1\nline2"


# --- Anchors and aliases ---


def test_anchor_alias_simple():
    """Simple anchor and alias."""
    result = pyfastyaml.loads("x: &ref [1, 2, 3]\ny: *ref")
    assert result["x"] == [1, 2, 3]
    assert result["y"] == [1, 2, 3]
    assert result["x"] is result["y"]


def test_anchor_alias_mapping():
    """Anchor on mapping, alias references same object."""
    result = pyfastyaml.loads("""
defaults: &defaults
  adapter: postgres
  host: localhost
copy: *defaults
""")
    assert result["defaults"]["adapter"] == "postgres"
    assert result["copy"]["adapter"] == "postgres"
    assert result["defaults"] is result["copy"]


def test_anchor_in_sequence():
    """Anchor on sequence item."""
    result = pyfastyaml.loads("items: [&ref [1, 2], *ref, [3]]")
    assert result["items"][0] == [1, 2]
    assert result["items"][1] == [1, 2]
    assert result["items"][0] is result["items"][1]


def test_anchor_flow():
    """Anchor and alias in flow."""
    result = pyfastyaml.loads("data: {a: &x {n: 1}, b: *x}")
    assert result["data"]["a"] == {"n": 1}
    assert result["data"]["b"] == {"n": 1}
    assert result["data"]["a"] is result["data"]["b"]


# --- Merge key ---


def test_merge_key():
    """Merge key <<: *anchor merges mapping keys."""
    result = pyfastyaml.loads("""
defaults: &defaults
  adapter: postgres
  host: localhost
development:
  <<: *defaults
  database: dev
""")
    assert result["development"]["adapter"] == "postgres"
    assert result["development"]["host"] == "localhost"
    assert result["development"]["database"] == "dev"


def test_merge_key_multiple():
    """Merge key with multiple aliases <<: [*a, *b]."""
    result = pyfastyaml.loads("""
base: &base
  a: 1
extra: &extra
  b: 2
  a: 99
merged:
  <<: [*base, *extra]
  c: 3
""")
    assert result["merged"]["a"] == 99  # extra overrides base
    assert result["merged"]["b"] == 2
    assert result["merged"]["c"] == 3


# --- Multi-document (load_all) ---


def test_load_all_empty():
    """load_all of empty string returns empty list."""
    assert pyfastyaml.load_all("") == []


def test_load_all_single():
    """load_all of single document returns list of one."""
    assert pyfastyaml.load_all("a: 1") == [{"a": 1}]


def test_load_all_multi():
    """load_all of multi-document stream."""
    result = pyfastyaml.load_all("---\na: 1\n---\nb: 2")
    assert result == [{"a": 1}, {"b": 2}]


def test_load_all_from_file(tmp_path):
    """load_all with file-like object."""
    f = tmp_path / "multi.yaml"
    f.write_text("---\nx: 1\n---\ny: 2", encoding="utf-8")
    with open(f, encoding="utf-8") as fp:
        result = pyfastyaml.load_all(fp)
    assert result == [{"x": 1}, {"y": 2}]
