# Layer 3 Formalization Reorganization Record

## Date and scope

On 2026-08-26, the verified Layer 3 formalization directory was made canonical
by the following path-only transition:

```text
demostrations/     -> demostrations_prev/
demostrations_v2/  -> demostrations/
```

No Lean source file was edited, removed, or regenerated as part of this path
transition. The original formalization remains available at
`../demostrations_prev/`; the verified formalization is now at
`../demostrations/`.

## Required path updates

`ORIGINAL_SOURCES.sha256`, `README.md`, and `FORMALIZATION_CHANGES.md` were
updated only to refer to the new original-directory path. The `.lake/packages`
symbolic link was redirected from the former original path to
`../../demostrations_prev/.lake/packages`, preserving the same pinned local
dependency cache without copying or rebuilding it.

## Preserved verification

- The fourteen canonical Lean sources remain governed by
  `CURRENT_SOURCES.sha256`.
- The thirteen original source references remain governed by
  `ORIGINAL_SOURCES.sha256`.
- The successful `lake build` evidence remains in `BUILD_RECORD.md`.
- No new `lake build` was run as part of this reorganization.

## Subsequent licensing metadata update

Later on 2026-08-26, the fourteen canonical Lean source files received uniform
SPDX copyright and MIT licence headers. That separate cosmetic metadata update
is documented in `FORMALIZATION_CHANGES.md`, its hashes are recorded in the
current manifest, and its build is recorded in `BUILD_RECORD.md`.
