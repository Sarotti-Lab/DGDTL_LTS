# Windows Hunter and Unified

Use Windows x86-64 with Docker Desktop running the WSL2 backend and Linux
containers. The supplied Hunter and Unified launchers are functional under
Windows PowerShell 5.1. Their operation has been checked separately from the
completed scientific certification. Native Windows Python, macOS and ARM
execution are outside the certified scope.

Keep the release directory intact, including `runtime/`. From your own existing
scientific working directory, invoke the appropriate command by its path:

```powershell
& "<release>\orchestrators\Hunter.cmd"
& "<release>\orchestrators\Unified.cmd"
```

Replace `<release>` with the location where you extracted the release. Keep
datasets and generated results outside that directory. For a packaged example,
copy its input CSVs and deployment guide to your working directory first.
The launchers preserve the caller's current directory; they do not switch to
their own installation directory. Double-clicking from the release directory
is therefore unsuitable for Unified.

Hunter asks for an existing working directory (Enter keeps the current one),
then uses the original Linux configuration questions and defaults. Dataset
and output paths resolve relative to the selected directory; absolute local
Windows paths also work. Inputs are mounted read-only and the selected host
output directory is writable. Hunter starts immediately without generating a
shell script. Output must not contain either input dataset.

Unified uses the caller's directory as `/work`, writable for its original Python
workflow. Unified itself offers **1 — Deployment Guide** and
**2 — Interactive Configuration**, with its own diagnosis and training menu
in interactive mode. Enter
relative paths with `/` separators, or paths under `/work`; Windows drive-letter
paths and files outside this mounted directory are not visible to Unified.
Its original defaults, including `results`, apply. This is the same Python
orchestrator, with no additional Windows configuration menu.

Local physical paths with spaces and Unicode are preserved. UNC paths,
junctions/symlinks, and mount paths containing commas or newlines are rejected
with a diagnostic. The release, its ancestors and any `reference_results`
directory are protected from writable mounts. The launcher does not transform
datasets or change the scientific environment.

The exact official OCI SHA-256 is
`5f2779def4bb23fe2102945d97d34d67d949dbcd075f0483cdde415a1e949b05`.
Each start verifies release files and OCI bytes, inspects the installed image
identity and layers, and loads the official artifact only if absent. For the
classic Docker image store, a temporary transport archive adds a Docker
manifest around the exact OCI config/layer blobs. It does not rebuild or
replace the official OCI. The detected Docker image store determines which
loading path is used.

Scientific execution explicitly uses `/opt/dgdtl/env/bin/python` and the frozen
`/opt/dgdtl/env` environment. Before configuration/execution, the launcher checks
the interpreter, prefix, public package locations, WSL2 kernel and controlled
Arial resolution. Thread controls and `PYTHONHASHSEED=0` match the certified
transport. Scientific containers have networking disabled. No host scientific
Python or Conda/Mamba setup is needed.

Four exact Arial faces are required. The original `arial32.exe` package is
included in `launchers/windows/third-party/`, so **font preparation works
offline on a fresh host**. No download, separate font copy, environment-variable
configuration or certification directory is needed. Launch Hunter or Unified
normally; on first preparation, read the included Microsoft EULA and enter
`I ACCEPT`. The launcher extracts the embedded cabinet automatically and checks
the package, cabinet and all four font hashes. It never runs the installer or
installs system fonts. Only the per-user `%LOCALAPPDATA%\DGDTL\fonts` cache is
populated. Subsequent starts reuse the exact verified faces.

Existing exact fonts are still accepted from `-FontDirectory`,
`DGDTL_ARIAL_FONT_DIR`, the per-user cache or Windows Fonts. These are optional
overrides, not prerequisites. For example:

```powershell
& "<release>\orchestrators\Hunter.cmd" -FontDirectory "<fonts>"
& "<release>\orchestrators\Unified.cmd" -InstallerPath "<original-package>\arial32.exe"
```

If Docker is unavailable, start Docker Desktop and select WSL2/Linux containers.
If identity verification fails, restore the exact distributed artifact; do not
build or pull a replacement. If the bundled font package fails verification,
restore the complete original release. Preserve the diagnostic and process exit code for execution
failures; the launcher returns the actual Hunter/Unified container exit code.
Temporary transport files are removed after exit. Scientific output stays in
the selected host directory.

The bundled Microsoft package has its own license and is not MIT-licensed.
Keep the original package and EULA intact; its redistribution restrictions
also apply when distributing DGDTL with that package. See the
[third-party notice](third-party/README.md).
