# klayout-pex-plugin-kqcircuits

Development scaffold for exporting [KLayout-PEX](https://iic-jku.github.io/klayout-pex-website/)
`PEX25D` scenes through [KQCircuits](https://iqm-finland.github.io/KQCircuits/)
to `Elmer`.

**The exporter is not implemented yet.** This repository provides package discovery,
the exporter interface, contract tests and release infrastructure for the partners
who will implement the scene translation. Calling the exporter reports that it is
not implemented and writes no solver files.

## Intended use

The planned route is:

```text
resolved PEX25D scene → KQCircuits simulation inputs → Gmsh/Elmer run
```

The motivation is access to the `KQCircuits` simulation workflow, including its
mesh-refinement controls. This is an alternative to the existing
[`klayout-pex-plugin-elmer`](https://github.com/iic-jku/klayout-pex-plugin-elmer).
It does not depend on that plugin or copy its mesher.

## Install for development

Use Python `3.12` or later and Poetry `2`:

```bash
poetry install
poetry run pex25d exporters
```

The exporter list includes `klayout-pex-plugin-kqcircuits:kqcircuits`.
Discovery and factory construction work without `KQCircuits`, `Gmsh` or `Elmer`
installed. The scaffold does not declare a `KQCircuits` dependency until an actual
adapter has been qualified against a specific version and installation method.

This command demonstrates the current implementation boundary:

```bash
poetry run pex25d export testdata/two_nets.pex25d \
  --to kqcircuits --out-dir output_kqcircuits
```

It exits with status `3` and explains that export is not implemented. It does not
create the output directory. Installing this package therefore does not yet provide
capacitance extraction through `KQCircuits`.

## Check changes

```bash
poetry run pytest
poetry build
poetry run twine check --strict dist/*
```

Tests cover registration through the real KPEX registry, lazy loading, coexistence
with other namespace packages, the CLI failure status and preservation of inputs
and existing files. Numerical export and simulation tests belong with the actual
adapter implementation.

`klayout_pex_plugins` is an implicit namespace. Do not add an `__init__.py` at that
level: it would interfere with sibling plugins. Only the `kqcircuits` child package
belongs to this distribution.

## Compatibility and licence

- `klayout-pex>=0.9.0,<1`
- Plugin API `v1` is provisional and may change before it is declared stable
- GPL-3.0-or-later, matching the existing KPEX plugins; see [LICENSE](https://github.com/martinjankoehler/klayout-pex-plugin-kqcircuits/blob/main/LICENSE)
