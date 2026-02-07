"""YAML samples for benchmarking (small / medium / large / realworld).

Structures are chosen to work with FastYAML MVP parser:
- 2-space indentation, mappings, sequences, scalars.
"""

# Small: ~200 bytes (simple config)
YAML_SMALL = """
title: App
version: "1.0"
server:
  host: localhost
  port: 8080
"""

# Medium: ~1.5 KB (K8s/Ansible style - flat keys + nested blocks)
YAML_MEDIUM = """
title: App Example

owner:
  name: Tom Preston-Werner
  dob: "1979-05-27T07:32:00Z"

database:
  server: 192.168.1.1
  ports:
    - 8001
    - 8001
    - 8002
  connection_max: 5000
  enabled: true

servers:
  alpha:
    ip: 10.0.0.1
    dc: eqdc10
  beta:
    ip: 10.0.0.2
    dc: eqdc10

products:
  - name: Hammer
    price: 10
  - name: Nail
    price: 1
"""

# Large: repeat content to get ~15 KB
YAML_LARGE = (
    "# config\n" + YAML_MEDIUM.strip() + "\n\n"
    + "\n".join(
        f"section_{i}:\n  foo: {i}\n  bar: value_{i}"
        for i in range(80)
    )
)

# Real-world: CI/Docker Compose style (simplified structure)
YAML_REALWORLD = """
name: myapp
version: "0.1.0"
description: An app

authors:
  - Alice
  - Bob

keywords:
  - yaml
  - config

requires-python: ">=3.10"

dependencies:
  - pyfastyaml
  - pytest

tool:
  pytest:
    minversion: "7.0"
    testpaths:
      - tests
    addopts: -v

  coverage:
    source:
      - src
    branch: true
"""
