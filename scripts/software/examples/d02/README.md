# D02 — Constrained error-matrix configuration

D02 contains 24/5/14 training, validation, and test observations. This constrained proof-of-concept configuration uses error-matrix mode, no intercept, a sum-to-one coefficient constraint, and no predictor normalization.

## Data source and references

This domain reuses the Diels–Alder activation-energy data and constrained
error-matrix formulation of the original DGDTL proof of concept. The
DGDTL-LTS / U-MaxP analyses distributed here belong to the present study.
Please cite the original publication when using this example's data:

Pérez, J. A.; Zanardi, M. M.; Sarotti, A. M.
**Low-Cost, High-Accuracy Reactivity Modeling: Integrating Genetic Algorithms
and Machine Learning with Multilevel DFT Calculations.** *Journal of Chemical
Information and Modeling* **2025**, *65* (22), 12422–12436.
[DOI: 10.1021/acs.jcim.5c02048](https://doi.org/10.1021/acs.jcim.5c02048).

## Prepare the example

Follow the [Linux or Windows setup](../README.md) with domain `d02`. This
creates a separate working directory containing copies of `data_train.csv`,
`data_valid.csv`, `data_test.csv`, and `DGDTL_Report_L2_GM_Scout_1.txt`.
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
DGDTL_Report_L2_GM_Scout_1.txt
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
  --mode error_matrix --no-intercept --beta-sum-one --no-norm-x
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
| Mode | `error_matrix` |
| Fit intercept | No |
| Sum-to-one coefficient constraint | Yes |
| Normalize predictors (X) | No |
| Normalize target (Y) | No |
| Additional feature formulas | None |

The complete Hunter reference contains 44 files under
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
