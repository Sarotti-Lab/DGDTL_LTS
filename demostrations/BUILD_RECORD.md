# Layer 3 Formal Build Record

- Date: 2026-08-26
- Lean toolchain: `leanprover/lean4:v4.30.0`
- Lake: `5.0.0-src+d024af0`
- Mathlib revision: `bcab563382e24694bafc0f509f15a39264f24df5`
- Command: `lake build`
- Modules required by the default target: 14
- Compiled `.olean` artifacts: 14
- `sorry`/`admit`: none
- Result: **PASS**

## Scope of this build

This build re-certified the canonical formalization after the uniform SPDX
copyright and MIT licence header was added to all fourteen project Lean source
files. No theorem, definition, proof term, import, namespace, or executable
declaration was changed. `CURRENT_SOURCES.sha256` records the resulting source
hashes; `ORIGINAL_SOURCES.sha256` continues to verify the thirteen preserved
original source files in `../demostrations_prev/`.

The build used the dependency revisions pinned in `lake-manifest.json`. Local
dependency packages were reused from the immutable original workspace cache;
all project build artifacts were generated under this directory's `.lake/`.

Golden Master verification after the build:

- `dgdtl_core.py`: `25e0663160e0379e5f2fbac6ae86091bc51c8c07552aa27d3050148b0b2621b6`
- `u_maxp_core.py`: `88559753226df385afedf978e85d785f9c0a1dcb2840c0967174cc6112d4ce53`
