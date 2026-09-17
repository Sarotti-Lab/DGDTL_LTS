# Reference results: provenance and comparison

Selection date: 2026-09-14. The researcher approved including the complete
Hunter and Unified output directories for D01, D02, D08, D11, and S03 as
didactic references. The files were copied from existing evidence; no
scientific execution or recertification was performed for this selection.

## Source and exact copy mapping

The preserved source collection is located at the following path relative to
the development workspace root:

```text
scripts/PyPI_cp/validation/cases/PyPI_dgdtl_lts_results_cluster_cord/
```

For each selected domain, the mapping into `software/examples/` is:

| Source beneath the collection | Destination beneath `examples/` |
| --- | --- |
| `<domain>/results/<file>` | `<domain>/reference_results/unified/<file>` |
| `<domain>/results_dgdtl_job/<file>` | `<domain>/reference_results/hunter/<file>` |

All 304 output files were copied byte for byte, retaining their filenames and
contents. No report, timestamp, diagnostic, figure, or numerical value was
edited. The source tree remains read-only. Source scripts, scheduler files,
logs, caches, and duplicate inputs were not added to the example directories.

[REFERENCE_PROVENANCE.json](REFERENCE_PROVENANCE.json) records per-domain
counts, input hashes, guide identities, source script hashes, Hunter job/log
identities and recorded hardware details, Unified's reported `n_jobs`, and
the identities of the existing certification records.
[REFERENCE_RESULTS.sha256](REFERENCE_RESULTS.sha256) lists the hash of every
copied output, with paths relative to `examples/`. Together with the mapping
above, each destination has an unambiguous original source path and hash.

## Execution provenance and existing certification

These are the selected Linux reference outputs from the preserved collection.
The Hunter job logs identify Serafin (CCAD-UNC), its recorded CPU model, the
allocation, and the `dgdtl_v2` interpreter. The frozen reference specification
is distributed in [environment/dgdtl_v2.yml](../environment/dgdtl_v2.yml).
Original commands and their source identities are retained in the provenance
JSON; the historical scheduler script has an `.sge` suffix but uses Slurm.

Unified's reports retain their own execution parameters. The collection name
does not establish that Unified ran in the same Hunter job or on the same
hardware. Missing historical fingerprints are not inferred, and the current
wheel hashes are not retroactively assigned to these earlier executions.

The completed native Linux comparisons are summarized in the preserved
[Layer 3 validation method](../validation/VALIDATION_METHOD.md). The later
cross-OS certification covers the frozen Linux runtime on Linux x86-64 Docker
and Windows x86-64 Docker Desktop/WSL2 for the five domains and both workflows.
Its authoritative archival location is
`scripts/PyPI_cp/runtime_validation/certification-record/cross-os-v1/`;
the provenance JSON records the exact summary and evidence-index hashes.
The distributed [runtime provenance](../runtime/RUNTIME_PROVENANCE.json)
retains the runtime promotion history. Earlier certificates and their original
scope statements remain historical records.

The current selection adds no new platform claim. Windows reference outputs
are not duplicated here, and the approved Linux/Windows evidence is preserved
at its existing location.

## Inputs and deployment guides

All 15 example CSVs match their counterparts in the selected source collection
byte for byte. Each of the five deployment guides already present in the
examples differs from its source-collection counterpart only in the `Date:`
and `Execution Time:` lines. Removing those two fields for comparison yields
identical text. Both guide hashes are recorded in the provenance JSON; the
original files remain unchanged.

Run Unified with the guide supplied at the root of the example. Reproducing
Hunter requires the corresponding search configuration, not merely the name
of the final guide. The domain README provides the Hunter configuration used
by the source job. Preserve environment, effective parallelism, parameters,
input hashes, and execution details when interpreting a new run.

## Verify the distributed reference files

On Linux, from `software/examples/`:

```bash
sha256sum -c REFERENCE_RESULTS.sha256
```

On Windows PowerShell 5.1, from `software\examples\`:

```powershell
Get-Content .\REFERENCE_RESULTS.sha256 -ErrorAction Stop | ForEach-Object {
    $Parts = $_ -split '\s+', 2
    $Actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $Parts[1] -ErrorAction Stop).Hash
    if ($Actual -ne $Parts[0]) { throw "Reference hash mismatch: $($Parts[1])" }
}
Write-Host 'All reference hashes match.'
```

This verifies the distributed reference bytes. It is not a comparison of a new
scientific run. The release-wide manifest also covers these outputs and their
documentation. Git attributes preserve the reference bytes during checkout.

## Compare a new execution

Keep new outputs in the separate working directory described in the
[examples README](README.md). Compare its `results/` with the selected
`reference_results/unified/`, or its `results_hunter/` with
`reference_results/hunter/`.

1. Confirm the same workflow, file inventory, input partitions, guide or search
   configuration, and certified environment. Investigate missing or extra
   artifacts before interpreting numerical agreement.
2. Compare CSV scientific values, rankings, candidate ordering, verdicts,
   U-MaxP values, and final selection using the existing exact-comparison
   policy. Depending on the artifact, the approved checks use byte equality,
   exact scalar equality, `float.hex()`, or `numpy.array_equal` with the
   established handling of missing values. Do not introduce `allclose`,
   rounding, or a new numerical tolerance to obtain agreement.
3. Dates and execution durations in text reports can differ. Apply only the
   documented dynamic-field rules from the existing comparisons; retain raw
   outputs and record every normalization. Do not remove scientific fields or
   execution parameters merely because they differ.
4. The approved native Linux checks included PNG byte equality. PDF container
   hashes can differ because of metadata; the existing PDF comparison uses
   exact extracted text and rendered-page checks with controlled tools and
   fonts. Visual similarity alone does not establish equivalence. Preserve a
   raw mismatch and any subsequent documented PDF adjudication separately.

Begin with `DGDTL_Champion_Selection_Report.txt`, the Run 1/Run 2 metric and
prediction files, and Hunter's `UMaxP_Ranking_Framework.csv` and
`UMaxP_Framework_Report.txt`. These are useful entry points, not substitutes
for the complete artifact comparison. An unexplained scientific difference
must be investigated rather than relabelled as a successful reproduction.

For D11, Hunter's `FAIL` guides and structural diagnostics are intentional
reference outcomes. Unified evaluates the supplied fixed diagnostic
configuration; its selection report does not turn that guide into a Hunter
deployment certification.

## Selection verification

The copy operation verified all 304 source/destination hashes, the 15 input
CSV identities, and the five documented guide differences. Golden Masters,
packaged scientific payloads, wheels, runtime, and existing reference sources
were preserved. The release-content manifest was refreshed for the added
outputs and documentation. This is an integrity check of a curated copy, not
a repetition of the scientific certification campaign.
