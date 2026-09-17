# D08 — Constraint-induced search geometry

D08 contains 101/18/13 training, validation, and test observations. It uses the D07 empirical matrix with a sum-to-one coefficient constraint, illustrating how a structural restriction changes the optimization geometry while leaving the observations unchanged.

## Data source and references

The nicotinamide cofactor biomimetic stability data and descriptors originate
from Platt and colleagues. D08 reuses the D07 data and partitions. The
sum-to-one coefficient constraint defining D08 was introduced in the present
DGDTL-LTS / U-MaxP study; it was not part of the original source study.
Please cite the source publication when using this example's data:

Platt, A. P.; Klem, H.; Mallinson, S. J. B.; Bomble, Y. J.; Paton, R. S.
**Computer-aided design of stability enhanced nicotinamide cofactor biomimetics
for cell-free biocatalysis.** *Green Chemistry* **2025**, *27*, 6831–6844.
[DOI: 10.1039/D5GC00351B](https://doi.org/10.1039/D5GC00351B).

## Prepare the example

Follow the [Linux or Windows setup](../README.md) with domain `d08`. This
creates a separate working directory containing copies of `data_train.csv`,
`data_valid.csv`, `data_test.csv`, and `DGDTL_Report_L2_Scout_4.txt`.
Run the commands below from that working directory, using the software-path
variable defined in the shared setup. Keep `reference_results/` in the release
unchanged and choose a fresh working directory for each execution.

## Unified: evaluate the supplied configuration

Linux, with the wheels installed in the frozen `dgdtl_v2` environment:

```bash
python "$DGDTL_SOFTWARE/orchestrators/dgdtl_unified_umaxp.py"
```

Windows PowerShell 5.1, through the supplied Docker/WSL2 launcher:

```powershell
& "$DGDTLSoftware\orchestrators\Unified.cmd"
```

Select **1 — Deployment Guide** (or press Enter for its default) and enter:

```text
DGDTL_Report_L2_Scout_4.txt
```

The guide supplies the fixed configuration. Unified writes new outputs to
`results/` in the working directory. Its supplied reference contains 30 files
under [reference_results/unified](reference_results/unified/).
Begin with the
[reference selection report](reference_results/unified/DGDTL_Champion_Selection_Report.txt),
then inspect the Run 1/Run 2 metrics, predictions, diagnostics, and figures.

## Hunter: reproduce the complete search

Hunter is a resource-intensive search. The saved references can be studied
without rerunning it. For a Linux execution, use:

```bash
python "$DGDTL_SOFTWARE/orchestrators/dgdtl_hunter_umaxp_cluster.py" \
  --train data_train.csv --valid data_valid.csv --out-dir results_hunter \
  --mode raw --beta-sum-one
```

On Windows, start the configuration dialogue:

```powershell
& "$DGDTLSoftware\orchestrators\Hunter.cmd"
```

Keep the prepared working directory, select `data_train.csv` and
`data_valid.csv`, and use `results_hunter` as the output directory. Set the
scientific options to match this example:

| Setting | Value |
| --- | --- |
| Mode | `raw` |
| Fit intercept | Yes |
| Sum-to-one coefficient constraint | Yes |
| Normalize predictors (X) | Yes |
| Normalize target (Y) | No |
| Additional feature formulas | None |

The complete Hunter reference contains 26 files under
[reference_results/hunter](reference_results/hunter/). Start with its
[ranking table](reference_results/hunter/UMaxP_Ranking_Framework.csv) and
[framework report](reference_results/hunter/UMaxP_Framework_Report.txt).

## Verify and interpret

Compare new `results/` and `results_hunter/` with their respective reference
directories. The [shared provenance and comparison rules](../REFERENCE_RESULTS.md)
explain exact numerical checks, report dates and durations, and PDF comparison.
The guide supplied here differs from the guide in the selected source collection
only in its date and execution duration; its scientific configuration is identical.

Reference-file hashes are listed in
[REFERENCE_RESULTS.sha256](../REFERENCE_RESULTS.sha256). Source identities and
execution details are recorded in
[REFERENCE_PROVENANCE.json](../REFERENCE_PROVENANCE.json). Consult
[data provenance](../DATA_PROVENANCE.md) for scientific context and dataset origins.
