# Layer 3 launchers

This area preserves the Layer 3 launcher inventory for the reference
orchestrators: the Linux local generator, the research group's institutional
cluster helper, and the Windows Docker/WSL2 transport. The distribution makes
all of them available; select the route appropriate to your platform.

Hunter is designed for complete-search execution on computing clusters.
Local execution is also supported on Linux and on Windows through the supplied
Docker/WSL2 launchers, provided that adequate computing resources are available
for the selected domain.

## Which components do I need?

| Route | Components used | What the researcher prepares |
| --- | --- | --- |
| Linux, direct Python execution | The selected orchestrator and its companion modules; no launcher from this folder is required. | Active frozen environment with both wheels installed, input data, and configuration. |
| Linux, local Hunter generator | `linux/create_local_sh_dgdtl_lts.py`, followed by its generated shell script and Hunter. | The same environment and inputs; Hunter must be accessible by its filename in the execution working directory. |
| Institutional cluster helper | `cluster/create_job_dgdtl_lts.py`, its generated submission script, and Hunter. | The supported institutional environment, working files, and resource allocation. |
| Windows, Hunter or Unified | The selected `.cmd`, Windows transport, Certified Runtime, controlled fonts, and selected orchestrator with its companion modules. Hunter additionally reads `linux/create_local_sh_dgdtl_lts.py`. | Docker Desktop/WSL2, the installed distribution, and an external working directory with the selected inputs. |

The [release file requirements](../README.md#files-needed-for-each-use) list
the concrete execution files and separate initial installation from subsequent
use. Native Linux execution does not need the Windows transport or runtime.
Windows uses the packages inside the runtime and needs no host scientific
Python installation.

For Windows, the existing launcher also verifies every file listed in
`manifests/RELEASE_CONTENTS.sha256`. Keep those files and the manifest in the
installed distribution, even when they do not participate in the selected
scientific workflow. The execution components above are therefore not a list
of files to extract into a smaller Windows distribution.

## Data and working directories

Prepare a fresh working directory outside `software`. For your own analysis,
supply your own CSV partitions and modelling settings. Hunter reads training
and validation data; Unified also reads test data. Unified's Deployment Guide
mode requires a guide and the default `data_train.csv`, `data_valid.csv`, and
`data_test.csv` filenames. Its interactive mode collects the paths and settings
without requiring a guide. See the
[orchestrator instructions](../orchestrators/README.md#prepare-a-working-directory)
for the column layout and configuration routes.

If using a supplied example, copy only that domain's CSVs and guide into the
working directory using the [example setup](../examples/README.md). Reference
results are available for comparison; they are not inputs to Hunter or Unified
and need not be copied into a new run directory. Their retention in a Windows
installation is a separate manifest-integrity requirement.

## Linux local

[`linux/create_local_sh_dgdtl_lts.py`](linux/create_local_sh_dgdtl_lts.py)
interactively collects Hunter configuration and creates `run_<job_name>.sh`
in an existing working directory selected by the researcher. It generates the
batch script; it does not run Hunter itself.

From the release root, start the generator with:

```bash
python launchers/linux/create_local_sh_dgdtl_lts.py
```

The generated script uses `python` from the active environment and invokes
`python dgdtl_hunter_umaxp_cluster.py` from the execution working directory.
Before execution, place a copy of the supplied Hunter script in that directory,
with `dgdtl_reporting.py` beside it for the supplied console presentation.
Activate the frozen environment with both packages installed, change to the
selected working directory, and run the generated `run_<job_name>.sh` as shown
by the generator. It does not install packages, activate an environment, or
copy Hunter and the datasets for you. Choose the input paths, output location,
and local resources for the intended analysis.

See the [reference orchestrator instructions](../orchestrators/README.md) and
[environment instructions](../environment/README.md) for the existing setup
and scientific usage guidance. This helper preserves the original Linux-local
configuration and execution behavior.

## Institutional cluster helper

[`cluster/create_job_dgdtl_lts.py`](cluster/create_job_dgdtl_lts.py) generates
Hunter submission scripts for the research group's configured Capitán
(CCT-Rosario) and Serafín (CCAD-UNC) environments. Its institutional policies,
submission workflow and mandatory acknowledgments are preserved.

This is not a claim of universal HPC or SLURM support. The helper is retained
here as part of the complete local Layer 3 inventory. Its exposure or selective
transfer to Layer 2 repositories will be decided during the Layer 2 transition.

## Windows

Use Windows x86-64, PowerShell 5.1, and Docker Desktop configured for WSL2 and
Linux containers. Keep the installed distribution in place and invoke the
selected entry point from your external scientific working directory:

```powershell
$DGDTLSoftware = 'C:\DGDTL\software'
& "$DGDTLSoftware\orchestrators\Unified.cmd"
```

For Hunter, invoke `Hunter.cmd` instead:

```powershell
& "$DGDTLSoftware\orchestrators\Hunter.cmd"
```

Replace the software path with its installed location. Unified opens its own
menu; Hunter first collects the working-directory and modelling configuration.
The transport resolves Hunter's host data/output paths. Within Unified's
Python dialogue, use paths relative to the mounted working directory, with
forward slashes for subdirectories.

Both [`Hunter.cmd`](../orchestrators/Hunter.cmd) and
[`Unified.cmd`](../orchestrators/Unified.cmd) use the frozen scientific
environment inside the exact Certified Runtime. See
[Windows usage and prerequisites](windows/README.md).
The bundled font package supports offline font preparation with its license
acceptance. Keep `linux/create_local_sh_dgdtl_lts.py` in its release location:
Windows Hunter reads its configuration class without generating a Linux job.

Scientific certification and the completed Windows functional checks remain
the existing evidence; these usage instructions do not introduce a new runtime
or modify the transport.
