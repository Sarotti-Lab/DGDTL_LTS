# DGDTL-LTS / U-MaxP

DGDTL-LTS is a deterministic regression engine for low-data, structurally
constrained modelling. U-MaxP provides the associated structural criterion
and reference selection protocol.

This repository brings together the Lean formalization and the Python
software distribution, including scientific engines, reference workflows,
examples, and Linux and Windows execution instructions.

## Repository contents

| Directory | Contents |
| --- | --- |
| [`demostrations/`](demostrations/README.md) | Lean formalization of mathematical properties and selection rules associated with DGDTL-LTS and U-MaxP. |
| [`scripts/software/`](scripts/software/README.md) | Complete software distribution: Python packages, local wheels, reference environment, Hunter and Unified workflows, launchers, examples, manuals, and Certified Runtime. |

## Install the Python packages from PyPI

The scientific engines are available on PyPI:

- [dgdtl-lts](https://pypi.org/project/dgdtl-lts/)
- [u-maxp](https://pypi.org/project/u-maxp/)

Version 1.0.0 of both packages requires **Python 3.12.12**.

With that interpreter's environment active, install the packages using:

```bash
pip install dgdtl-lts
pip install u-maxp
```

Use their public Python interfaces:

```python
from dgdtl_lts import DGDTLEstimator
from u_maxp import UMaxPCriterion, StructuralSelectionProtocol
```

The packages contain the scientific engines, including the underlying
`dgdtl_core.py` and `u_maxp_core.py` modules. Researchers can use the public
interfaces in their own scripts without copying those modules manually.

API documentation:

- [DGDTL-LTS](scripts/software/packages/dgdtl-lts/README.md)
- [U-MaxP](scripts/software/packages/u-maxp/README.md)

The PyPI packages provide the engines and their declared dependencies.
The complete Hunter and Unified workflows, launchers, examples, and runtime
are distributed separately in `scripts/software/`.

## Use the complete software distribution

The complete distribution supports the documented Linux and Windows routes.

| Platform | Execution route |
| --- | --- |
| Linux | Prepare the reference `dgdtl_v2` environment, install the supplied local wheels, and use the Python interfaces or reference workflows. |
| Windows x86-64 | Use the supplied launchers with Docker Desktop and its WSL2 Linux-container backend. The Certified Runtime already contains Python and the scientific packages. |

For Linux installation from the supplied wheels, follow the
[environment and installation instructions](scripts/software/environment/README.md).

For Windows, follow the
[Windows launcher instructions](scripts/software/launchers/windows/README.md).
The documented Windows route does not require installing scientific Python
on the host.

Keep `scripts/software/` complete and unchanged. Use a separate working
directory for your input data and generated results.

### Reference workflows

- **Unified** evaluates a fixed configuration or a Hunter deployment guide.
  It is the recommended starting point for the supplied examples.
- **Hunter** performs the full hyperparameter search. It is designed for
  cluster execution and also supports the documented local routes when
  sufficient computing resources are available.

Start with the [scientific examples](scripts/software/examples/README.md).
The distribution includes D01, D02, D08, D11, and S03, with input data,
deployment guides, provenance information, and reference results.

Further documentation:

- [Software overview](scripts/software/README.md)
- [User guide — English](scripts/software/docs/en/USER_GUIDE.md)
- [Manual de usuario — Español](scripts/software/docs/es/MANUAL_DE_USUARIO.md)
- [Hunter and Unified](scripts/software/orchestrators/README.md)

## Lean formalization

The `demostrations/` directory contains the canonical formalization,
organized into:

- `Theory/`: theoretical properties, including identifiability and TIE.
- `Topology/`: existence and relaxation results.
- `UMaxP/`: structural quantities, criterion properties, and selection rules.

The recorded build uses **Lean 4.30.0** and the dependency revisions pinned
in `lake-manifest.json`. Its 14 project modules passed the recorded build
without `sorry` or `admit`.

See the [formalization README](demostrations/README.md) and
[build record](demostrations/BUILD_RECORD.md) for instructions and scope.

The Lean development formalizes specified mathematical properties and
protocol rules. Scientific execution and reproducibility are documented
separately in the software distribution.

## Reproducibility and provenance

For reproduction of the recorded scientific results, follow the supplied
reference environment, configurations, and comparison procedures.
Installing the packages alone does not establish equivalence with a
certified execution.

See the [documented reproducibility scope](scripts/software/README.md#reproducibility-scope)
and [reference-result guidance](scripts/software/examples/REFERENCE_RESULTS.md).

Historical provenance records may refer to development sources and evidence
preserved in the separate full project archive.

## Citation and licenses

For software attribution, see [CITATION.cff](scripts/software/CITATION.cff).
When using the supplied datasets, also cite their
[original publications](scripts/software/examples/README.md#data-sources-and-references).

The scientific software and Lean formalization are distributed under their
respective MIT license files:

- [Software license](scripts/software/LICENSE)
- [Formalization license](demostrations/LICENSE)

Bundled third-party components retain their
[separate license terms](scripts/software/launchers/windows/third-party/README.md).

## Contact

For questions regarding conceptualization and support, contact:
jandrespmen@gmail.com
