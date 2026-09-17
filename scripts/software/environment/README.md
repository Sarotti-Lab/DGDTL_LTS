# Reference environment

This directory describes the `dgdtl_v2` scientific environment used by
DGDTL-LTS / U-MaxP. The reference interpreter is Python 3.12.12. Linux users
prepare and activate the native environment; Windows users access the frozen
environment already contained in the supplied Certified Runtime.

## Files and their roles

| File | Role |
| --- | --- |
| [dgdtl_v2.yml](dgdtl_v2.yml) | Reference environment definition: its name, channels, Python version, and explicitly listed package versions. |
| [runtime-constraints.txt](runtime-constraints.txt) | Recorded versions of scientific packages used by the engines and reference workflows, including reporting and plotting dependencies. |
| [build-tools.txt](build-tools.txt) | Historical versions of pip, setuptools, and wheel used for package construction. Users install the supplied wheels without rebuilding them. |

The YAML defines a broader environment than the scientific package list in
`runtime-constraints.txt`. Conversely, `joblib==1.5.3` and
`statsmodels==0.14.6` are recorded in that list but are not explicitly pinned
in the YAML. They may be absent or resolved differently during a fresh setup.
Creating the YAML environment therefore needs to be followed by the version
check below before it is treated as the recorded reference setup.

These files describe package versions; the YAML is not a complete binary lock
of every transitive dependency. The exact distributed container identity is
recorded separately in
[runtime/RUNTIME_PROVENANCE.json](../runtime/RUNTIME_PROVENANCE.json).

## Linux: create the environment once

Run all commands below from the `software` directory, the parent of this
directory. Mamba must already be available in the shell. If the reference
environment is not installed, create it using the unchanged definition:

```bash
mamba env create -f environment/dgdtl_v2.yml
```

Environment creation can require access to the configured package channels
unless the required packages are already available in the local cache. The
subsequent installation of the supplied wheels uses local files.

## Linux: activate an existing environment

For an environment that has already been prepared, activate it in the current
shell. This is also the next step after initial creation:

```bash
mamba activate dgdtl_v2
python --version
python -c "import sys; print(sys.executable); print(sys.prefix)"
```

The interpreter must report Python 3.12.12 and belong to the intended
`dgdtl_v2` environment. An environment name alone does not establish that its
installed packages match the reference versions.

## Linux: check the recorded scientific package versions

The following read-only check compares the active interpreter and installed
package metadata with `runtime-constraints.txt`. It neither installs packages
nor runs a scientific workflow:

```bash
python - <<'PY'
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import sys

if sys.version_info[:3] != (3, 12, 12):
    raise SystemExit("Python 3.12.12 is required for the reference setup.")

mismatches = []
for line in Path("environment/runtime-constraints.txt").read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    name, expected = line.split("==", 1)
    try:
        actual = version(name)
    except PackageNotFoundError:
        actual = "NOT INSTALLED"
    print(f"{name}: {actual} (reference: {expected})")
    if actual != expected:
        mismatches.append(name)

if mismatches:
    raise SystemExit("Reference package mismatch: " + ", ".join(mismatches))
print("Recorded Python and scientific package versions match.")
PY
```

If a package is missing or differs, the environment does not yet meet the
recorded version requirements. Resolve that installation discrepancy before a
reference execution. Keep the supplied definitions and certified artifacts
unchanged; neither `pip check` nor the environment name can substitute for
this version comparison. Matching these versions alone does not establish
binary identity or extend the certified platform scope.

## Linux: install the supplied wheels

Inside the prepared environment, install the two local release wheels:

```bash
python -m pip install --no-index --no-deps \
  dist/dgdtl_lts-1.0.0-py3-none-any.whl \
  dist/u_maxp-1.0.0-py3-none-any.whl
python -m pip check
```

`--no-index` avoids package-index access for this installation; `--no-deps`
leaves dependency installation to the prepared environment. These options do
not supply a missing dependency. If the exact wheels are already installed,
proceed to the checks without reinstalling them.

Confirm package versions and public import locations:

```bash
python -c "import importlib.metadata as m, dgdtl_lts, u_maxp; print(m.version('dgdtl-lts'), dgdtl_lts.__file__); print(m.version('u-maxp'), u_maxp.__file__)"
```

Both distributions are version 1.0.0. Their public imports must resolve from
the active environment's `site-packages`, rather than from copied core files
in a working directory. The historical build-tool versions in
`build-tools.txt` document the wheel build; they are not instructions to
rebuild wheels or replace the user's installation tools. See the preserved
[build record](../manifests/BUILD_RECORD.md) for artifact provenance.

## Windows: use the environment inside the runtime

The existing Windows launchers use Python at `/opt/dgdtl/env/bin/python` inside
the official Linux runtime. A Windows user does not create a host environment
from this YAML, install the wheels into host Python, or install the build tools.
The launchers already verify the frozen environment and controlled fonts as
part of their established execution route.

Keep the complete `software` distribution, including this directory: the
launcher verifies all files listed in the release-content manifest before
execution. Prepare only the required CSVs and deployment guide in a separate
working directory. See the [platform requirements](../README.md#files-needed-for-each-use)
and [Windows example setup](../examples/README.md#prepare-a-windows-example).

## Continue with an example or a researcher script

Once the native Linux environment is ready, it can run a researcher script
using `dgdtl_lts` and `u_maxp`, or the supplied Hunter and Unified orchestrators.
The [main README](../README.md) lists the execution files needed for each use.
The [examples overview](../examples/README.md) explains how to prepare inputs
and keep new outputs separate from the preserved references.

The existing [reproducibility scope](../README.md#reproducibility-scope) and
[reference comparison rules](../examples/REFERENCE_RESULTS.md) govern
scientific interpretation. The setup checks above are installation checks,
not a new certification campaign.
