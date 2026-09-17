# DGDTL-LTS / U-MaxP Formalization

This directory is the canonical Layer 3 formalization for DGDTL-LTS and
U-MaxP. It is derived from the immutable sources in `../demostrations_prev/`.

The original formalization remains unchanged. Its source hashes are recorded
in `ORIGINAL_SOURCES.sha256`. All corrections made here concern the explicit
correspondence between the validated Python Golden Masters, the manuscript and
the Lean model; they do not modify the Python implementation.

## Build

The pinned toolchain is Lean 4.30.0. The default Lake targets compile all
current modules under:

- `Theory/`
- `Topology/`
- `UMaxP/`

Run:

```text
lake build
```

No theorem containing `sorry` or `admit` is accepted for release.
Current source hashes are recorded in `CURRENT_SOURCES.sha256`; the validated
local build is recorded in `BUILD_RECORD.md`.

Every canonical Lean source carries an SPDX copyright and MIT licence header.
The original sources in `../demostrations_prev/` remain unmodified for
provenance comparison.

## Provenance and changes

See `FORMALIZATION_CHANGES.md` for the exact refinement changes and validation
status. `REORGANIZATION_RECORD.md` records the path transition that made this
the canonical formalization without changing Lean source content. The complete
project is licensed under the MIT License.
