# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0b5] - 2025-02-07

### Changed

- Add PyYAML CSafeLoader (libyaml) to benchmarks
- Update README benchmark table with PyYAML (C) column and accurate comparisons

## [0.1.0b4] - 2025-02-07

### Added

- `dump()` / `dump_all()`: support for path string — `dump(data, "output.yaml")`, `dump_all(docs, "file.yaml")`
- `dump()`: `sort_keys` parameter for deterministic output

### Fixed

- Root-level scalars: `loads("null")` → `None`, `loads("true")` → `True`, numbers, plain strings
- Implicit null: `loads("key:")` → `{"key": None}`
- Block-style nested sequences: `loads("-\n  - a\n  - b")` → `[['a', 'b']]`
- Indent handling when skipping blank lines in nested structures

## [0.1.0b3] - 2025-02

### Added

- `dump()` and `dump_all()` — pure Python serialization
- Block/flow style, literal block `|` for multiline strings
- Support for nested mappings and sequences in dump

## [0.1.0b2] - 2025-01

### Added

- Anchors and aliases (`&anchor`, `*alias`)
- Merge key (`<<: *anchor`, `<<: [*a, *b]`)
- Document markers (`---`, `...`, `%YAML` directive)

## [0.1.0b1] - 2024

### Added

- Initial C++/SIMD YAML parser
- `loads()`, `load()`, `load_all()` — PyYAML-compatible API
- Types: dict, list, str, int, float, bool, null
- Indentation: 2-space, 4-space, tabs
- Flow syntax: `[a, b, c]`, `{a: 1, b: 2}`
- Multiline strings: `|` (literal), `>` (folded)

[Unreleased]: https://github.com/baksvell/FastYAML/compare/v0.1.0b5...HEAD
[0.1.0b5]: https://github.com/baksvell/FastYAML/compare/v0.1.0b4...v0.1.0b5
[0.1.0b4]: https://github.com/baksvell/FastYAML/compare/v0.1.0b3...v0.1.0b4
[0.1.0b3]: https://github.com/baksvell/FastYAML/compare/v0.1.0b2...v0.1.0b3
[0.1.0b2]: https://github.com/baksvell/FastYAML/compare/v0.1.0b1...v0.1.0b2
[0.1.0b1]: https://github.com/baksvell/FastYAML/releases/tag/v0.1.0b1
