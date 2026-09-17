# D11 — Extreme low-data diagnostic case

D11 contains 15/5/5 training, validation, and test observations. It is an external extreme-low-data diagnostic case. The supplied `DGDTL_Report_L2_FAIL_GM_Scout_4.txt` is a fixed diagnostic configuration; it is not evidence of an automatically certified Hunter deployment champion.

## Data source and references

The original Suzuki cross-coupling site-selectivity data originate from
Niemeyer and colleagues. This domain uses those data as reprocessed through
the COBRA framework described by Cao and colleagues. Please cite both
publications to preserve the original and intermediate data provenance.
The fixed partitions and DGDTL-LTS / U-MaxP diagnostics distributed here
belong to the present study.

Niemeyer, Z. L.; Milo, A.; Hickey, D. P.; Sigman, M. S.
**Parameterization of phosphine ligands reveals mechanistic pathways and
predicts reaction outcomes.** *Nature Chemistry* **2016**, *8*, 610–617.
[DOI: 10.1038/nchem.2501](https://doi.org/10.1038/nchem.2501).

Cao, Z.; Falivene, L.; Poater, A.; Maity, B.; Zhang, Z.; Takasao, G.;
Sayed, S. B.; Petta, A.; Talarico, G.; Oliva, R.; Cavallo, L.
**COBRA web application to benchmark linear regression models for catalyst
optimization with few-entry datasets.** *Cell Reports Physical Science*
**2025**, *6* (1), 102348.
[DOI: 10.1016/j.xcrp.2024.102348](https://doi.org/10.1016/j.xcrp.2024.102348).

## Prepare the example

Follow the [Linux or Windows setup](../README.md) with domain `d11`. This
creates a separate working directory containing copies of `data_train.csv`,
`data_valid.csv`, `data_test.csv`, and `DGDTL_Report_L2_FAIL_GM_Scout_4.txt`.
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
DGDTL_Report_L2_FAIL_GM_Scout_4.txt
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
  --mode raw --no-intercept --norm-y
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
| Fit intercept | No |
| Sum-to-one coefficient constraint | No |
| Normalize predictors (X) | Yes |
| Normalize target (Y) | Yes |
| Additional feature formulas | None |

The complete Hunter reference contains 8 files under
[reference_results/hunter](reference_results/hunter/). Start with its
[ranking table](reference_results/hunter/UMaxP_Ranking_Framework.csv) and
[framework report](reference_results/hunter/UMaxP_Framework_Report.txt).

The Hunter reference deliberately retains the `L1_FAIL_GM_Scout_4` and
`L2_FAIL_GM_Scout_4` diagnostics. Unified can evaluate this configuration and
produce a selection report; that does not establish a Hunter deployment
certification. Preserving and interpreting this outcome is part of the example.

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
