# Reference orchestrators

Hunter and Unified implement the reference workflows using the installed
`dgdtl_lts` and `u_maxp` packages. For a first execution, use Unified with a
supplied example deployment guide. Hunter performs the complete search and can
require substantially more computing time and resources.

Hunter is designed for complete-search execution on computing clusters.
Local execution is also supported on Linux and on Windows through the supplied
Docker/WSL2 launchers, provided that adequate computing resources are available
for the selected domain.

| Workflow | Inputs | Configuration | Default output directory |
| --- | --- | --- | --- |
| Hunter | Training and validation CSVs | Command-line arguments on Linux; configuration dialogue through the Windows launcher | `results_hunter_umaxp_cluster/` for the Python CLI |
| Unified | Training, validation, and test CSVs | Deployment guide or interactive configuration | `results/` |

The [scientific examples](../examples/README.md) provide fixed inputs, selected
deployment guides, Linux reference outputs, and data-source citations for D01,
D02, D08, D11, and S03. Their README files specify each domain's configuration.

## Files and platform requirements

The distribution includes both platforms' components. The requirements below
identify what each workflow uses; they do not imply that every distributed
folder participates in every execution. The release-level
[file requirements](../README.md#files-needed-for-each-use) distinguish
installation, execution components, and scientific inputs.

| File | Role |
| --- | --- |
| `dgdtl_hunter_umaxp_cluster.py` | Hunter search and framework evaluation. |
| `dgdtl_reporting.py` | Hunter terminal formatting and logging support; the script has a fallback if this module cannot be imported. |
| `dgdtl_unified_umaxp.py` | Unified deployment-guide and interactive workflows. |
| `plotting_style.py` | Unified plotting support. |
| `reporting.py` | Unified report-generation support. |
| `Hunter.cmd` | Windows entry point for Hunter configuration and execution. |
| `Unified.cmd` | Windows entry point for Unified execution. |

**Linux:** first prepare the frozen `dgdtl_v2` environment and install both
supplied wheels using the [environment instructions](../environment/README.md).
The reference environment uses Python 3.12.12; public package imports must
resolve from its `site-packages`. Once installed, Hunter needs its Python
script and the two input CSVs; retain `dgdtl_reporting.py` beside it for the
supplied terminal presentation. For Unified with full reporting and plotting,
retain its Python script, `plotting_style.py`, and `reporting.py` together, and
provide the three input CSVs plus the deployment guide when using guide mode.
If either Unified companion cannot be imported, the script disables that
reporting/visualization branch; the resulting output set is reduced.

**Windows:** use Windows x86-64, PowerShell 5.1, and Docker Desktop with the
WSL2 backend and Linux containers. The execution uses the selected `.cmd`,
its Python orchestrator and companion modules, the Windows transport, the
Certified Runtime, and controlled-font resources. Hunter also uses
`launchers/linux/create_local_sh_dgdtl_lts.py` for configuration. Python and
both scientific packages are already installed inside the runtime; host Python
and host wheel installation are unnecessary.

The launcher separately requires the release manifest and every file it lists
to remain in the distribution, including files that are not scientific inputs.
This is an integrity requirement of the current launcher. Reference outputs
need not be copied to a working directory or used in an analysis of your own
data. See the [Windows execution components](../README.md#windows-with-the-supplied-launchers),
[launcher arrangements](../launchers/README.md), and
[Windows instructions](../launchers/windows/README.md).

The scripts use the installed public packages. They do not require copies of
the legacy core source files in the working directory. Researchers developing
their own Linux scripts can consult the
[DGDTL-LTS API](../packages/dgdtl-lts/README.md) and
[U-MaxP API](../packages/u-maxp/README.md). The supplied Windows entry points
cover Hunter and Unified; they do not expose a generic custom-script command.

## Prepare a working directory

Use a fresh directory outside `software` for each execution. For your own data,
provide training and validation CSVs for Hunter, or training, validation, and
test CSVs for Unified. Choose the configuration appropriate to those data.
Unified's interactive mode requires no guide; its Deployment Guide mode needs
a corresponding guide and uses the default CSV filenames described below.
You do not need any of the distributed example datasets for this route.

For a supplied example, copy the selected domain's `data_*.csv` files and
`DGDTL_Report_*.txt` guide there, keeping the release's `reference_results/`
directories intact. Those results are available for comparison and are not
inputs to a new run. Follow the
[Linux setup](../examples/README.md#prepare-a-linux-example) or
[Windows setup](../examples/README.md#prepare-a-windows-example), which defines
`DGDTL_SOFTWARE` or `$DGDTLSoftware`, respectively, and changes to that working
directory. The commands below assume that setup with domain `d01`.

Both scripts interpret CSV columns by position: identifier first, predictors
in the middle, and numeric target last. Preserve predictor names and ordering
across partitions. Feature formulas refer to those predictor names. Hunter
uses training and validation data; Unified also reads the test data.

## Unified: execute a deployment guide

On Linux, with the reference environment active:

```bash
python "$DGDTL_SOFTWARE/orchestrators/dgdtl_unified_umaxp.py"
```

On Windows, from PowerShell in the prepared working directory:

```powershell
& "$DGDTLSoftware\orchestrators\Unified.cmd"
```

Select **1 — Deployment Guide** or press Enter for the default. For D01, enter:

```text
DGDTL_Report_L1_Scout_4.txt
```

The parser reads the modelling configuration, feature formulas, and search
parameters from the guide. In this mode, CSV paths retain the defaults
`data_train.csv`, `data_valid.csv`, and `data_test.csv`, resolved from the
working directory; outputs go to `results/`. Placing a guide in another
directory does not change where the default CSV paths are resolved.

Unified also offers **2 — Interactive Configuration**. This collects the mode,
intercept and coefficient constraint, data paths, output directory, and feature
formulas, then presents:

1. **Baseline Diagnosis (with Retraining Preview)**
2. **Run Training (Auto/Custom Configuration)**
3. **Exit**

Follow the subsequent transformation and training-parameter prompts for the
selected action. Unified uses its own menu; it does not implement Hunter's
command-line options. For a supplied reference example, use the guide route
and the exact inputs identified in that example's README.

On Windows, paths entered inside the Unified Python dialogue refer to the
container's mounted working directory. Use relative paths within that directory
and forward slashes for subdirectories, rather than Windows drive paths.

## Hunter: execute the full search

For the D01 configuration on Linux:

```bash
python "$DGDTL_SOFTWARE/orchestrators/dgdtl_hunter_umaxp_cluster.py" \
  --train data_train.csv --valid data_valid.csv --out-dir results_hunter \
  --mode raw --norm-y --formulas 'NBO_C1*sEpi'
```

The target normalization and feature formula above belong to D01. Use the
corresponding example README for other domains. Quote each formula so the shell
passes it as one argument.

The Python CLI accepts the following options:

| Option | Default when omitted | Meaning |
| --- | --- | --- |
| `--train PATH` | `data_train.csv` | Training CSV. |
| `--valid PATH` | `data_valid.csv` | Validation CSV. |
| `--out-dir PATH` | `results_hunter_umaxp_cluster` | Output directory; the example command explicitly uses `results_hunter`. |
| `--mode MODE` | `raw` | `raw` or `error_matrix`. |
| `--no-intercept` | Intercept enabled | Disable intercept fitting. |
| `--beta-sum-one` | Constraint disabled | Constrain the coefficient sum to one. |
| `--formulas FORMULA ...` | Empty list | Feature-construction formulas. |
| `--no-norm-x` | Predictor normalization enabled | Disable predictor normalization. |
| `--norm-y` | Target normalization disabled | Request target normalization. |

On Windows, start the supplied configuration dialogue:

```powershell
& "$DGDTLSoftware\orchestrators\Hunter.cmd"
```

Provide the working-directory and data/output paths as requested by the
launcher and enter the selected example's modelling settings. The transport
converts that configuration into Hunter arguments and runs the existing Python
script. The CLI table above documents the Python script, not additional `.cmd`
switches. Keep new outputs outside the release and separate from input files.

Hunter has no `--test` or `--n-jobs` argument. Parallelism is set internally by
the reference scripts. Researchers choose resource allocation, scheduler
directives, and working/output locations appropriate to their machine or
cluster. This folder does not provide a universal scheduler launcher.

## Outputs and reference comparisons

Hunter writes per-attempt deployment reports (`DGDTL_Report_*.txt`) and metrics,
and its final framework evaluation writes `UMaxP_Ranking_Framework.csv` and
`UMaxP_Framework_Report.txt` when records are available for evaluation. Read the
framework report and verdicts when interpreting or selecting a guide. A report
file's existence alone does not establish that its configuration was certified
as a champion; D11's supplied guide is an explicitly documented diagnostic
case.

Unified writes baseline outputs, Run 1/Run 2 solution tables, champion metrics
and predictions, and `DGDTL_Champion_Selection_Report.txt`. With the companion
modules available, its reporting path also produces diagnostic figures and
formatted reports. The exact preserved output inventory for each supplied
example is linked from that example's README.

Compare new outputs against the separate Linux reference directories using the
documented [reference comparison rules](../examples/REFERENCE_RESULTS.md).
Preserve numerical values, rankings, verdicts, and selection results; apply
only the recorded treatment of dynamic report fields and PDF metadata. These
examples support learning and verification of executions. They do not replace
the existing scientific certification records.

## Provenance and integrity

The [orchestrator provenance record](../manifests/ORCHESTRATORS.md) documents
the original validated scripts and their package-import adaptations. Current
release file hashes are listed in
[RELEASE_CONTENTS.sha256](../manifests/RELEASE_CONTENTS.sha256). The reference
scripts, package artifacts, runtime, and Windows transport remain frozen;
documentation updates do not change their scientific behavior.
