# DGDTL-LTS / U-MaxP

DGDTL-LTS is a deterministic regression engine for low-data, structurally
constrained modelling. U-MaxP supplies the associated structural criterion and
selection protocol. This `software` directory contains the curated version
1.0.0 distribution: Python packages, the frozen reference environment, Hunter
and Unified, platform launchers, scientific examples, and the Certified Runtime.

## Start here

| Platform | Execution route | What to prepare |
| --- | --- | --- |
| Linux | Python in the frozen `dgdtl_v2` environment | Install the supplied wheels, then use your own script or the reference orchestrators. |
| Windows x86-64 | Supplied launchers using Docker Desktop/WSL2 Linux containers | Keep the complete `software` directory and prepare an external working directory. Host scientific Python is unnecessary. |

For a first example, start with the
[examples overview](examples/README.md), select a domain, and run Unified with
its supplied deployment guide. Each example includes Linux reference outputs
for both workflows and the relevant data-source citations.

## Linux: environment and installation

Reference reproducibility requires the supplied environment, which fixes
Python 3.12.12 and the scientific dependencies. With Mamba available, run the
following commands from the `software` directory to create the environment
and install the two supplied wheels:

```bash
mamba env create -f environment/dgdtl_v2.yml
mamba activate dgdtl_v2
python -m pip install --no-index --no-deps \
  dist/dgdtl_lts-1.0.0-py3-none-any.whl \
  dist/u_maxp-1.0.0-py3-none-any.whl
python -m pip check
```

If the exact reference environment is already installed, activate it and
confirm the package installation rather than creating another environment.
`pip` installs the engines inside `dgdtl_v2`; it does not replace the frozen
environment definition. The commands above use the local release wheels and
do not assume that the packages have been published to a package index.

Confirm the interpreter, package versions, and import locations:

```bash
python --version
python -c "import importlib.metadata as m, dgdtl_lts, u_maxp; print(m.version('dgdtl-lts'), dgdtl_lts.__file__); print(m.version('u-maxp'), u_maxp.__file__)"
```

The public modules must resolve from the active environment's `site-packages`.
See [environment documentation](environment/README.md) for the supplied
environment files.

## Windows: use the supplied runtime

Use Windows x86-64 with PowerShell 5.1 and Docker Desktop configured for the
WSL2 backend and Linux containers. The supplied launchers execute Python inside
the frozen Linux runtime. A host Python or Mamba installation is not required.

Keep the complete `software` directory in its installed location. Prepare an
existing scientific working directory outside it, using the
[Windows example setup](examples/README.md#prepare-a-windows-example) when
running a supplied example. From that working directory, invoke the desired
launcher by its path:

```powershell
$DGDTLSoftware = 'C:\DGDTL\software'
& "$DGDTLSoftware\orchestrators\Unified.cmd"
```

To run Hunter instead, use:

```powershell
& "$DGDTLSoftware\orchestrators\Hunter.cmd"
```

Replace the software path with its actual location. Keep the launchers in the
distribution; the working directory contains your inputs and receives the new
outputs. The original Arial package is bundled for offline font preparation,
with its own license acceptance. No separate font download is needed. See the
[Windows launcher instructions](launchers/windows/README.md) for the existing
transport, path, and font-preparation details.

## Files needed for each use

The distribution makes all components available together. Each platform and
workflow uses only the components described below. Distinguish the installed
software from the working directory: each execution needs only its own inputs
there, and writes its own outputs. Reference examples are optional scientific
inputs, not a prerequisite for analysing a researcher's own dataset.

### Native Linux

For initial native Linux installation, the release inputs are
`environment/dgdtl_v2.yml` and the two wheels in `dist/`. The dependencies in
that environment must be installed before running scientific code. Once the
environment and packages are installed, the execution files depend on the use:

| Native Linux use | Execution files | Scientific inputs |
| --- | --- | --- |
| Researcher's own Python script | The script and any additional dependencies it uses | Inputs required by that script. |
| Hunter | `orchestrators/dgdtl_hunter_umaxp_cluster.py` | Training and validation CSVs; the example README specifies the search options. |
| Unified with complete reports and figures | `orchestrators/dgdtl_unified_umaxp.py`, `orchestrators/plotting_style.py`, and `orchestrators/reporting.py`, kept together | Training, validation, and test CSVs; a deployment guide when using Deployment Guide mode. |

Hunter can additionally use `orchestrators/dgdtl_reporting.py` for console
presentation; that import has a built-in fallback. Unified's reporting and
plotting modules are needed to produce the complete output set supplied in the
examples. The Linux local and institutional cluster generators are optional
helpers. Native Linux execution does not require the Windows launchers or OCI
runtime archive.

### Windows with the supplied launchers

Windows uses the scientific environment and both packages already installed
inside the Certified Runtime. It does not install the host-side wheels or
create a host environment from the YAML file.

| Execution component | Purpose |
| --- | --- |
| `runtime/dgdtl-crt-exp-pv1-linux-amd64-c001.oci.tar` | Frozen Linux runtime used through Docker Desktop/WSL2. |
| `orchestrators/Hunter.cmd` or `orchestrators/Unified.cmd` | Entry point for the selected workflow. |
| The selected Python orchestrator and its companion modules listed above | Scientific execution and reporting inside the runtime. |
| `launchers/windows/Start-DGDTL.ps1` and `runtime_entry.py` in that directory | Host launch, path handling, checks, and container execution. |
| `launchers/windows/Controlled-Fonts.ps1`, its bundled `third-party/arial32.exe`, and font license notice | Controlled fonts, with offline preparation when needed. |
| `launchers/linux/create_local_sh_dgdtl_lts.py` | Configuration component also used by the Windows Hunter launcher. |

These are the components used by the execution route, not instructions to
create a reduced Windows installation. The current launcher additionally reads
`manifests/RELEASE_CONTENTS.sha256` and verifies every listed file, including
documentation and example references. Keep the manifest and its listed files
in the distribution. Their presence satisfies the existing integrity check;
it does not mean that every folder supplies inputs to the scientific analysis.

### Your own data or a supplied example

| Workflow | Contents needed in the working directory |
| --- | --- |
| Hunter | Training and validation CSVs; choose the modelling settings for those data. |
| Unified, Deployment Guide mode | Training, validation, and test CSVs named `data_train.csv`, `data_valid.csv`, and `data_test.csv`, plus the corresponding deployment guide. |
| Unified, Interactive Configuration mode | Training, validation, and test CSVs; enter their paths and the modelling configuration in the dialogue. No deployment guide is required. |

For your own analysis, supply your own compatible data and configuration; no
example dataset or reference result is needed as scientific input. For a
supplied example, copy only the selected domain's CSVs and guide to a fresh
working directory, following its README. Consult `reference_results/` only
when comparing outputs; do not copy it into each new working directory.
On Windows it remains in the installed distribution for the integrity check.

See the [orchestrator instructions](orchestrators/README.md) for the CSV layout,
configuration, and commands, and the [launcher instructions](launchers/README.md)
for platform-specific arrangements. `PyPI_cp`, manuscript sources, Lean sources,
and development or certification workspaces are not user installation inputs.

## Public interfaces and researcher scripts

```python
from dgdtl_lts import DGDTLEstimator
from u_maxp import StructuralSelectionProtocol, UMaxPCriterion
```

The public distribution names are `dgdtl-lts` and `u-maxp`; the import names are
`dgdtl_lts` and `u_maxp`. The legacy `dgdtl_core` and `u_maxp_core` modules remain
installed for compatibility. New researcher scripts should use the public
imports above.

On Linux, activate `dgdtl_v2` and run the researcher's script with that
environment's Python. The supplied Windows launchers provide the Hunter and
Unified workflows; they do not expose a generic entry point for arbitrary
researcher scripts. The package interfaces are documented in the
[DGDTL-LTS package README](packages/dgdtl-lts/README.md) and
[U-MaxP package README](packages/u-maxp/README.md).

## Execution routes

- **Hunter** is designed for complete-search execution on computing clusters.
  Local execution is also supported on Linux and on Windows through the
  supplied Docker/WSL2 launchers, provided that adequate computing resources
  are available for the selected domain.
- **Unified** evaluates a fixed configuration or a Hunter deployment guide.
  It is the starting route for the supplied examples and also supports the
  existing interactive configuration workflow.

Use a separate working directory containing copies of the required input files.
Keep new outputs outside the distribution and outside `reference_results/`.
Choose a fresh working directory for each execution to avoid mixing results.
The supplied Unified guides write to `results/`; the example Hunter commands
use `results_hunter/`.

The [orchestrator documentation](orchestrators/README.md) describes the scripts,
and the [launcher overview](launchers/README.md) describes the available
helpers. Institutional cluster helpers retain their site-specific resource and
acknowledgment requirements.

## Examples and reference results

The five examples are [D01](examples/d01/README.md),
[D02](examples/d02/README.md), [D08](examples/d08/README.md),
[D11](examples/d11/README.md), and [S03](examples/s03/README.md). Each contains
fixed CSV inputs, a deployment guide, and separate `reference_results/unified/`
and `reference_results/hunter/` directories. The 304 reference files are exact
copies from preserved Linux evidence and can be studied without rerunning the
complete search.

D11 retains its diagnostic Hunter `FAIL` outcomes. S03 belongs to the synthetic
dataset collection developed for this study. Full bibliographic references and
the attribution of adapted empirical data are available in the
[examples README](examples/README.md#data-sources-and-references).

Read the [reference provenance and comparison rules](examples/REFERENCE_RESULTS.md)
before comparing a new execution. Scientific comparisons use the existing exact
criteria; dates, durations, and PDF metadata require the documented treatment.
The reference hash manifest verifies the supplied copies, while comparisons of
new runs also require matching scientific inputs and execution conditions.

## Certified artifacts

| Artifact | SHA-256 |
| --- | --- |
| `dgdtl_lts-1.0.0-py3-none-any.whl` | `706ac7b97ef3d292c34e50acb67999465bc08a433d182ae05d640f2418dc4aef` |
| `u_maxp-1.0.0-py3-none-any.whl` | `2c33016abc89324cc113f6bd927d331a7c11a496517db7a53f19da33d41fe85d` |

These wheels preserve the certified Golden Master payloads. Their build
history is recorded in [BUILD_RECORD.md](manifests/BUILD_RECORD.md).
The official runtime archive is
`runtime/dgdtl-crt-exp-pv1-linux-amd64-c001.oci.tar`, with SHA-256
`5f2779def4bb23fe2102945d97d34d67d949dbcd075f0483cdde415a1e949b05`.
Its identity, approved scope, and promotion history are recorded in
[RUNTIME_PROVENANCE.json](runtime/RUNTIME_PROVENANCE.json).

[RELEASE_CONTENTS.sha256](manifests/RELEASE_CONTENTS.sha256) identifies the
current distributed files. From the `software` directory on Linux, verify it
with:

```bash
sha256sum -c manifests/RELEASE_CONTENTS.sha256
```

The Windows launcher performs the corresponding release-file verification at
startup. Preserved historical records retain the names and paths used when
they were created, including the former release directory name `PyPI`.

## Reproducibility scope

Native Linux reproducibility was verified on two independent Ubuntu 24.04
systems and two high-performance computing clusters in Argentina under the
frozen reference environment. The original engine certificate and comparison
method are preserved in [validation/](validation/VALIDATION_METHOD.md).

The subsequently certified Linux runtime reproduced the approved outputs on
Linux x86-64 Docker and Windows x86-64 Docker Desktop/WSL2 Linux containers
across D01, D02, D08, D11, and S03 for Hunter, Unified, and their combined
workflow. This completed cross-OS scope is recorded in the distributed
[runtime provenance](runtime/RUNTIME_PROVENANCE.json). The Windows Hunter and
Unified launchers are functional under PowerShell 5.1. Their operation has been
checked separately from the completed scientific certification.

Native Windows Python is outside the certified scope. macOS and ARM execution
remain unvalidated. Certification applies to the recorded artifacts,
environment, workflows, and comparison conditions; it does not automatically
certify arbitrary researcher code or altered configurations.

## Layout

```text
packages/       installable package sources
dist/           release wheels
environment/    frozen reference environment specifications
orchestrators/  Hunter, Unified, and support modules
launchers/      Linux, institutional cluster, and Windows entry points
runtime/        official frozen Linux OCI runtime and provenance
examples/       five domains, input data, guides, references, and citations
docs/           English and Spanish user guides
validation/     preserved engine certificate and comparison method
manifests/      hashes and build provenance
```

The detailed manuals are available in
[English](docs/en/USER_GUIDE.md) and [Spanish](docs/es/MANUAL_DE_USUARIO.md).

## Citation and licenses

DGDTL-LTS and U-MaxP are distributed under the [MIT License](LICENSE).
The Windows launcher includes the original Microsoft Arial package for
offline font preparation, under its separate
[third-party license and redistribution terms](launchers/windows/third-party/README.md).
See [`CITATION.cff`](CITATION.cff) for preferred software citation and the
[example references](examples/README.md#data-sources-and-references) for
attribution of the original data publications. Dataset provenance is documented
in [DATA_PROVENANCE.md](examples/DATA_PROVENANCE.md).

## Acknowledgements

The author acknowledges the computing resources provided by the High
Performance Computing Center of CCT Rosario, a member of Argentina's National
High-Performance Computing System, and by the High Performance Computing Center
of the National University of Córdoba. This work was supported by a CONICET
doctoral fellowship (2023–2028).

## Contact

For questions regarding conceptualization and support, contact:
jandrespmen@gmail.com
