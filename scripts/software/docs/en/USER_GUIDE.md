# DGDTL-LTS / U-MaxP User Guide

This guide describes the supplied version 1.0.0 workflows. For a first
execution, run Unified with a selected example's deployment guide. Hunter
performs the complete search and can require substantially more computing time
and resources. Researchers can also use their own datasets.

Hunter is designed for complete-search execution on computing clusters.
Local execution is also supported on Linux and on Windows through the supplied
Docker/WSL2 launchers, provided that adequate computing resources are available
for the selected domain.

[Manual en español](../es/MANUAL_DE_USUARIO.md).

## Choose your execution route

| Platform | Route | Initial preparation |
| --- | --- | --- |
| Native Linux | Python in the frozen `dgdtl_v2` environment | Prepare the environment and install both supplied wheels. |
| Windows x86-64 | Supplied `.cmd` launchers through Docker Desktop/WSL2 Linux containers | Prepare Docker Desktop and use the supplied Certified Runtime. No host scientific Python installation is needed. |

The distribution makes all components available together. Each workflow uses
only some of them. Keep the software installation separate from each run's
working directory, which contains the selected inputs and receives new outputs.

## Certified setup

### Linux: prepare once, activate for each session

Run the installation commands from the `software` directory. Mamba must
already be available. If the reference environment has not been created:

```bash
mamba env create -f environment/dgdtl_v2.yml
```

Activate the environment:

```bash
mamba activate dgdtl_v2
python --version
```

The reference interpreter is Python 3.12.12. Before installing the wheels,
perform the [recorded scientific-version check](../../environment/README.md#linux-check-the-recorded-scientific-package-versions).
The unchanged YAML does not explicitly pin every recorded scientific package:
`joblib` and `statsmodels` require particular attention. An environment name
or a successful creation command alone does not establish a matching setup.
Resolve missing or mismatched dependencies before a reference execution.

Install the local wheels inside that prepared environment:

```bash
python -m pip install --no-index --no-deps \
  dist/dgdtl_lts-1.0.0-py3-none-any.whl \
  dist/u_maxp-1.0.0-py3-none-any.whl
python -m pip check
```

Environment creation can require network access to the configured channels;
this wheel installation uses local files and does not install dependencies.
If the exact environment and wheels are already installed, activate and check
them without repeating installation. Confirm package versions and locations:

```bash
python -c "import importlib.metadata as m, dgdtl_lts, u_maxp; print(m.version('dgdtl-lts'), dgdtl_lts.__file__); print(m.version('u-maxp'), u_maxp.__file__)"
```

Both distributions are version 1.0.0. Imports must resolve from the active
environment's `site-packages`. See the [environment documentation](../../environment/README.md)
for the full setup and its reproducibility limits. Matching package versions
alone does not establish binary identity or extend the certified scope.

### Windows: use the installed runtime

Use Windows x86-64, PowerShell 5.1, and Docker Desktop with the WSL2 backend
and Linux containers. Start Docker Desktop before launching a workflow.
Python and both scientific packages are already installed inside the supplied
Linux runtime; Windows users do not create a host environment from the YAML
or install the wheels into host Python.

The existing launchers prepare controlled Arial fonts from the bundled offline
package when needed. At first preparation, read the included Microsoft license
and enter `I ACCEPT` if you accept its terms. No separate font download or copy
from a certification directory is needed. See the
[Windows launcher instructions](../../launchers/windows/README.md) for details.

## Files needed for execution

| Use | Execution components, beyond the prepared environment | Scientific inputs |
| --- | --- | --- |
| Linux, own Python script | The script and any additional modules it uses. | Data required by that script. |
| Linux, Hunter | `orchestrators/dgdtl_hunter_umaxp_cluster.py`; retain `dgdtl_reporting.py` beside it for the supplied console presentation. | Training and validation CSVs and modelling settings. |
| Linux, Unified with complete reports and figures | `orchestrators/dgdtl_unified_umaxp.py`, `plotting_style.py`, and `reporting.py`, kept together. | Training, validation, and test CSVs; a guide in Deployment Guide mode. |
| Windows, Hunter or Unified | Selected `.cmd`, Python orchestrator and companions, Windows transport, runtime, and controlled-font resources. Hunter also uses `launchers/linux/create_local_sh_dgdtl_lts.py` for configuration. | The same CSVs and configuration or guide as the selected workflow above. |

Hunter has a console fallback if `dgdtl_reporting.py` is unavailable. Unified
disables a reporting/visualization branch if either companion cannot be
imported, so retain both for the complete reference output set. Linux direct
execution needs neither the Windows transport nor the OCI runtime archive;
the Linux launcher generators are optional helpers.

Windows uses the listed execution components, but its launcher also verifies
every file in `manifests/RELEASE_CONTENTS.sha256`. Keep that manifest and all
its listed files in the distribution, including documentation and reference
results. This separate integrity requirement does not make those files
scientific inputs. The table is not an instruction to extract a reduced Windows
installation. The [release file requirements](../../README.md#files-needed-for-each-use)
provide the detailed paths; the [launcher overview](../../launchers/README.md)
explains the supported arrangements.

## Input data

Hunter requires training and internal-validation CSV files. Unified also reads
a test CSV. Each partition must preserve the same column names and order:
identifier first, predictors in the middle, and numeric response last. Feature
formulas refer to predictor names. Keep partitions and configuration consistent
between Hunter and Unified when evaluating a selected Hunter configuration.

For your own data, choose the modelling mode, constraints, feature formulas,
and transformations appropriate to the study. No distributed example dataset
or reference result is required as input. Unified's interactive mode can be
used without a deployment guide. In Deployment Guide mode, provide a guide
corresponding to your configuration and the default CSV filenames described
below.

## Prepare a working directory

Choose a fresh directory outside `software` for each run. Do not reuse a
reference-results directory as an output location. Keep the installed scripts
in the distribution when invoking them by path as shown below.

For a first example, the following commands copy only D01's CSVs and guide.
Replace the software path and choose an unused working-directory name.

### Linux example

With the prepared environment active:

```bash
DGDTL_SOFTWARE="/absolute/path/to/software"
DGDTL_WORKDIR="$HOME/dgdtl_runs/d01_01"
mkdir -p "$DGDTL_WORKDIR"
cp "$DGDTL_SOFTWARE/examples/d01/"data_*.csv \
   "$DGDTL_SOFTWARE/examples/d01/"DGDTL_Report_*.txt \
   "$DGDTL_WORKDIR/"
cd "$DGDTL_WORKDIR"
```

### Windows example

In PowerShell 5.1:

```powershell
$DGDTLSoftware = 'C:\DGDTL\software'
$DGDTLWorkdir = Join-Path $env:USERPROFILE 'dgdtl_runs\d01_01'
New-Item -ItemType Directory -Path $DGDTLWorkdir -Force | Out-Null
Copy-Item -Path "$DGDTLSoftware\examples\d01\data_*.csv", `
                "$DGDTLSoftware\examples\d01\DGDTL_Report_*.txt" `
          -Destination $DGDTLWorkdir
Set-Location $DGDTLWorkdir
```

For another supplied domain, follow its [example README](../../examples/README.md).
For your own dataset, define the same software-path variable and change to your
own prepared working directory; place your own inputs there instead of copying
D01. Reference results remain available in the distribution for optional
comparison and need not be copied into a new run directory.

## Unified: fixed-configuration evaluation

From the prepared working directory, on Linux:

```bash
python "$DGDTL_SOFTWARE/orchestrators/dgdtl_unified_umaxp.py"
```

Or on Windows:

```powershell
& "$DGDTLSoftware\orchestrators\Unified.cmd"
```

Select **1 — Deployment Guide** or press Enter for the default. For D01, enter:

```text
DGDTL_Report_L1_Scout_4.txt
```

The guide supplies the modelling configuration and search parameters. In this
mode, Unified reads `data_train.csv`, `data_valid.csv`, and `data_test.csv`
from the current working directory and writes to `results/`. The parser does
not take input/output paths from the guide. A guide stored elsewhere does not
change where the default CSV paths are resolved.

For your own configuration, select **2 — Interactive Configuration**. Enter
the mode, intercept and coefficient constraint, data paths, output directory,
and feature formulas. The subsequent menu offers **Baseline Diagnosis (with
Retraining Preview)**, **Run Training (Auto/Custom Configuration)**, and
**Exit**. Follow the transformation and training-parameter prompts for the
selected action. Unified does not use Hunter's command-line options.

On Windows, paths inside the Unified Python dialogue refer to the container's
mounted working directory. Use relative paths there and forward slashes for
subdirectories, not Windows drive paths.

## Hunter: complete search

For the D01 example on Linux:

```bash
python "$DGDTL_SOFTWARE/orchestrators/dgdtl_hunter_umaxp_cluster.py" \
  --train data_train.csv --valid data_valid.csv --out-dir results_hunter \
  --mode raw --norm-y --formulas 'NBO_C1*sEpi'
```

The normalization and feature formula in this command are specific to D01.
Use the selected domain's README for other examples and choose settings for
your own study. The [Hunter option table](../../orchestrators/README.md#hunter-execute-the-full-search)
lists all nine arguments and their defaults. Quote each feature formula when
passing it through the shell. The example explicitly selects `results_hunter`;
the Python CLI's default output directory is `results_hunter_umaxp_cluster`.

On Windows:

```powershell
& "$DGDTLSoftware\orchestrators\Hunter.cmd"
```

The launcher requests the data working directory and opens the configuration
dialogue. For D01, use raw mode, enable intercept and predictor/target
normalization, leave the coefficient-sum constraint disabled, and enter
`NBO_C1*sEpi` as the feature formula. Use `data_train.csv`, `data_valid.csv`,
and `results_hunter` for the paths when following this example. The transport
resolves these paths relative to the selected host working directory; the
output directory must be separate from input files and outside the release.

Hunter is resource-intensive. Parallelism is defined internally; its CLI has
no `--n-jobs` or `--test` option. Select resources and wall time appropriate to
your hardware. The [launcher overview](../../launchers/README.md) explains the
optional Linux local generator and institutional cluster helper. Neither is a
universal scheduler interface.

## Read outputs and compare references

Unified's `results/` contains baseline outputs, Run 1/Run 2 solution tables,
champion predictions and metrics, and, with its companions, reports and figures.
Start with `DGDTL_Champion_Selection_Report.txt`. Hunter writes deployment
reports and metrics; its final framework evaluation produces
`UMaxP_Ranking_Framework.csv` and `UMaxP_Framework_Report.txt` when records
are available. Read verdicts before selecting a guide. A report's existence
alone does not establish successful deployment certification.

The five [selected examples](../../examples/README.md) are D01, D02, D08, D11,
and S03. Their separate `reference_results/unified/` and
`reference_results/hunter/` directories contain 304 preserved Linux output
files. D11 deliberately retains Hunter `FAIL` diagnostics; Unified's evaluation
of that diagnostic guide does not turn it into a Hunter-certified champion.
S03 belongs to this study's synthetic dataset collection. Cite the
[data publications](../../examples/README.md#data-sources-and-references) for
empirical examples and the [software citation](../../CITATION.cff).

Use the [reference provenance and comparison rules](../../examples/REFERENCE_RESULTS.md)
when comparing the same inputs, configuration, environment, and workflow.
Scientific comparisons retain exact numerical values, ordering, rankings,
verdicts, and selection results. Apply only the documented treatment of dates,
durations, and PDF metadata; do not introduce rounding or numerical tolerances
to obtain agreement. Preserve original outputs when investigating differences.

The release manifest checks distributed files, not newly generated results.
Normal runs writing outside `software` do not require any manifest update.
Reference hashes verify the preserved copies; they do not by themselves verify
a new scientific execution. Keep documentation and its matching release
manifest together when transferring an updated distribution.

## Recommended workflow

1. To learn the interface, start with Unified and a supplied example guide;
   the preserved references can be inspected without repeating Hunter's search.
2. For a new study, define and preserve your own data partitions and modelling
   choices. Use Hunter when a complete search is needed, or Unified's
   interactive mode for an investigator-defined configuration.
3. Inspect structural reports and verdicts. When continuing from Hunter,
   select the corresponding guide and evaluate it with Unified using the
   consistent data partitions.
4. Preserve commands or interactive choices, environment and artifact
   identities, input hashes, guides, resource settings, and raw outputs with
   scientific results.

Linux researchers can also activate the prepared environment and run their
own Python scripts using `dgdtl_lts` and `u_maxp`. See the
[DGDTL-LTS API](../../packages/dgdtl-lts/README.md) and
[U-MaxP API](../../packages/u-maxp/README.md). The supplied Windows entry points
cover Hunter and Unified; they do not expose a generic custom-script command.

## Reproducibility boundaries

Native Linux reproducibility was verified across eleven domains on two
independent Ubuntu 24.04 systems and two computing clusters in Argentina under
the frozen environment. The original [validation method](../../validation/VALIDATION_METHOD.md)
retains that scope and its exact comparison policy.

The subsequently certified Linux runtime reproduced the approved outputs on
Linux x86-64 Docker and Windows x86-64 Docker Desktop/WSL2 Linux containers
for D01, D02, D08, D11, and S03, covering Hunter, Unified, and their combined
workflow. See the [runtime provenance](../../runtime/RUNTIME_PROVENANCE.json)
and [reference provenance](../../examples/REFERENCE_RESULTS.md#execution-provenance-and-existing-certification).
Native Windows Python, macOS, and ARM execution are outside this certified
scope.

Example runs and later user-experience checks do not constitute a new
scientific certification. The examples teach usage and support comparison;
they do not replace independent study design or external validation. These
manual updates leave the scientific implementation and certified artifacts
unchanged.
