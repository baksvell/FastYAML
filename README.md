# pyfastyaml

[![PyPI version](https://badge.fury.io/py/pyfastyaml.svg)](https://pypi.org/project/pyfastyaml/)

**pyfastyaml** — Fast YAML parser for Python with C++/SIMD backend. **12–18× faster** than PyYAML (CSafeLoader/libyaml), **100–170× faster** than PyYAML (SafeLoader), **150–220× faster** than ruamel.yaml. API compatible with PyYAML for typical config use cases (Kubernetes, Ansible, CI, Docker Compose).

## Features

- **High performance**: C++17 implementation with AVX2 SIMD on x86 — orders of magnitude faster than pure-Python parsers
- **PyYAML compatible API**: `loads(s)`, `load(fp)`, `load_all(s)`, `dump()`, `dump_all()` — drop-in replacement for config loading
- **Types**: dict, list, str, int, float, bool, null, nested structures
- **Indentation**: 2-space (preferred), 4-space, tabs
- **Flow syntax**: `[a, b, c]`, `{a: 1, b: 2}` (incl. nested)
- **Multiline strings**: `|` (literal), `>` (folded)
- **Anchors and aliases**: `&anchor`, `*alias`
- **Merge key**: `<<: *anchor` and `<<: [*a, *b]`
- **Document markers**: `---`, `...`, `%YAML` directive

## Installation

```bash
pip install pyfastyaml
```

Requires Python 3.10+ and a C++ compiler with C++17 support.

## Usage

```python
import pyfastyaml

# Parse string
data = pyfastyaml.loads("""
key: value
nested:
  inner: 42
items:
  - a
  - b
""")
# {'key': 'value', 'nested': {'inner': 42}, 'items': ['a', 'b']}

# Parse file (path or file-like object)
data = pyfastyaml.load("config.yaml")

# Serialize to YAML
yaml_str = pyfastyaml.dump(data)
pyfastyaml.dump(data, stream=open("out.yaml", "w"))
```

API matches PyYAML for common cases:

```python
# Drop-in replacement
import pyfastyaml as yaml  # instead of import yaml
data = yaml.loads(yaml_string)
data = yaml.load("config.yaml")
```

## Benchmark

Parsing time (μs, lower is better):

| Size     | pyfastyaml | PyYAML (C) | PyYAML | ruamel |
|----------|------------|------------|--------|--------|
| Small (~200 B)   | ~2.3   | ~32   | ~229  | ~376  |
| Medium (~1.5 KB) | ~11    | ~134  | ~1,014| ~1,689|
| Large (~15 KB)   | ~83    | ~1,483| ~11,169| ~17,954|
| Realworld        | ~6.4   | ~98   | ~833  | ~1,388|

*PyYAML (C)* = CSafeLoader (libyaml extension). *PyYAML* = SafeLoader (pure Python).

Run benchmarks:

```bash
pip install pytest-benchmark PyYAML ruamel.yaml
pytest tests/test_benchmark.py -v --benchmark-only
```

## PyYAML Compatibility

pyfastyaml produces the same result as `yaml.safe_load()` for block-style YAML typical of configs. Compatibility tests included in `tests/test_pyyaml_compat.py`.

## Serialization (dump)

```python
# Single document
yaml_str = pyfastyaml.dump({"a": 1, "b": [1, 2, 3]})

# Write to file (path or stream)
pyfastyaml.dump(data, "output.yaml")
pyfastyaml.dump(data, stream=open("out.yaml", "w"))

# Deterministic output (sorted keys)
yaml_str = pyfastyaml.dump(data, sort_keys=True)

# Multiple documents
yaml_str = pyfastyaml.dump_all([{"a": 1}, {"b": 2}])
```

## Multi-document streams

```python
docs = pyfastyaml.load_all("""
---
a: 1
---
b: 2
""")
# [{'a': 1}, {'b': 2}]
```

## Limitations

Not yet supported:

- **Custom tags**
- **Complex flow keys** (`?` syntax)

## Development

```bash
pip install -e ".[dev]"
python setup.py build_ext --inplace
pytest tests/
```

## ConfigLint (experimental)

`configlint` is an experimental YAML dev-tool (lint / fix / format) built on top of FastYAML.

Configuration (optional): create `.configlint.yaml` in your repo root (auto-discovered).

Install (from PyPI, `configlint` ships with `pyfastyaml`):

```bash
pip install pyfastyaml
```

Run:

```bash
# If configlint is on PATH
configlint check path/to/configs
configlint fix path/to/configs --keep last
configlint format path/to/configs
configlint format path/to/configs --check

# Or always works without PATH changes
python -m configlint check path/to/configs
python -m configlint fix path/to/configs --keep last
python -m configlint format path/to/configs

# stdin modes (useful in CI / editors)
type config.yaml | python -m configlint check --stdin --path config.yaml
type config.yaml | python -m configlint fix --stdin --path config.yaml > config.yaml.fixed
type config.yaml | python -m configlint format --stdin > config.yaml.formatted
```

Benchmark commands:

```bash
pytest tests/test_benchmark.py -v --benchmark-only
pytest tests/test_benchmark.py -v --benchmark-only --benchmark-autosave
pytest tests/test_benchmark.py -v --benchmark-only --benchmark-compare
```

## Publishing (maintainers)

```bash
pip install build twine
python -m build
python -m twine upload dist/*
```

## License

MIT
