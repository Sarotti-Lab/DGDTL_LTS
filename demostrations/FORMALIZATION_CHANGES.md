# Formalization Changes

## Provenance

Thirteen current Lean source files were initially copied byte for byte from
`../demostrations_prev/`. Their original SHA-256 hashes are recorded in
`ORIGINAL_SOURCES.sha256`.

On 2026-08-26, every canonical Lean source received the uniform SPDX header:

```lean
-- SPDX-FileCopyrightText: 2026 José A. Pérez
-- SPDX-License-Identifier: MIT
--
```

This is a licensing and attribution change only. It does not alter a theorem,
definition, proof term, import, namespace, executable declaration, or the
mathematical content inherited from the original sources.

The Python references are immutable Golden Masters:

- `dgdtl_core.py`: `25e0663160e0379e5f2fbac6ae86091bc51c8c07552aa27d3050148b0b2621b6`
- `u_maxp_core.py`: `88559753226df385afedf978e85d785f9c0a1dcb2840c0967174cc6112d4ce53`

## Refinement corrections

`UMaxP/StructuralSelection.lean` was corrected as follows:

1. Phase 1 now distinguishes `dU_abs`, used by Gates 0–2, from `dU_rel`, used
   by the STP gate. `classifyPhase1Python` binds both quantities to the same
   `(U_A, U_B)` pair and includes the numerical denominator stabilizer.
2. Phase-3 `delta_E` is represented as a fraction and compared directly with
   `epsilon_tie = 0.02`, matching Python. `delta_E_percent` is explicitly a
   display-only conversion.
3. Phase-3 concordance reproduces the Python equality policy: Run 2 must
   improve both components strictly; equality is resolved toward Run 1 before
   the EVT-divergence branch is considered.

`UMaxP/ProtocolOperational.lean` was added to cover rules that the original
file explicitly excluded:

- Step 3a and deterministic `U_comp`/`phi` fallback selection;
- the post-dictamen theta stability audit;
- `psi_G`, the ICV product and its non-negative real cube-root score;
- Line-B reference classification;
- VBD stable/fragile/conditional/diagnostic classification;
- the single-promotion guard.

The OOD meaning of Phase 4 remains an epistemological interpretation of its
formally deterministic four-way verdict, rather than a separate numerical
theorem.

## Validation status

- The twelve previously unmodified copied sources retain their original Lean
  content after the SPDX header; their full-file hashes necessarily changed
  because of that header.
- One copied source, `UMaxP/StructuralSelection.lean`, was corrected.
- One new source, `UMaxP/ProtocolOperational.lean`, was added.
- All fourteen canonical Lean sources now carry the same SPDX copyright and MIT
  licence declaration.
- All fourteen modules are mandatory roots of the default Lake target.
- `lake build`: PASS.
- `sorry`/`admit`: none.
- Current hashes: `CURRENT_SOURCES.sha256`.
- Build evidence: `BUILD_RECORD.md`.
