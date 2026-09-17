# Scientific examples

These five examples provide fixed inputs, a deployment guide, and preserved
Linux reference outputs for learning the DGDTL-LTS / U-MaxP workflow. Start
with Unified to evaluate the supplied configuration. Hunter performs the full
search and can require substantially more computing time and resources.

Hunter is designed for complete-search execution on computing clusters.
Local execution is also supported on Linux and on Windows through the supplied
Docker/WSL2 launchers, provided that adequate computing resources are available
for the selected domain.

| Example | Purpose | Train / validation / test rows | Reference files: Unified / Hunter |
| --- | --- | --- | --- |
| [D01](d01/README.md) | Feature construction in an extreme low-data case | 11 / 3 / 3 | 30 / 32 |
| [D02](d02/README.md) | Constrained error-matrix configuration | 24 / 5 / 14 | 30 / 44 |
| [D08](d08/README.md) | Constraint-induced search geometry | 101 / 18 / 13 | 30 / 26 |
| [D11](d11/README.md) | Structural diagnostics in an extreme low-data case | 15 / 5 / 5 | 30 / 8 |
| [S03](s03/README.md) | Fixed synthetic multiple-regression sentinel | 35 / 9 / 15 | 30 / 44 |

## Data sources and references

Please cite the original data publications when using the empirical examples.
The full references below identify each source and its relationship to the
corresponding example. They are also included in the individual example README
files so that each example retains its attribution when consulted separately.

### D01 — Orlandi and colleagues

The source study reports the chiral anion phase-transfer (CAPT) reaction and
enantioselectivity data used for this domain. The fixed partitions and
DGDTL-LTS / U-MaxP analyses distributed here belong to the present study.
Please cite the source publication when using this example's data:

Orlandi, M.; Hilton, M. J.; Yamamoto, E.; Toste, F. D.; Sigman, M. S.
**Mechanistic Investigations of the Pd(0)-Catalyzed Enantioselective
1,1-Diarylation of Benzyl Acrylates.** *Journal of the American Chemical
Society* **2017**, *139* (36), 12688–12695.
[DOI: 10.1021/jacs.7b06917](https://doi.org/10.1021/jacs.7b06917).

### D02 — Pérez, Zanardi, and Sarotti

This domain reuses the Diels–Alder activation-energy data and constrained
error-matrix formulation of the original DGDTL proof of concept. The
DGDTL-LTS / U-MaxP analyses distributed here belong to the present study.
Please cite the original publication when using this example's data:

Pérez, J. A.; Zanardi, M. M.; Sarotti, A. M.
**Low-Cost, High-Accuracy Reactivity Modeling: Integrating Genetic Algorithms
and Machine Learning with Multilevel DFT Calculations.** *Journal of Chemical
Information and Modeling* **2025**, *65* (22), 12422–12436.
[DOI: 10.1021/acs.jcim.5c02048](https://doi.org/10.1021/acs.jcim.5c02048).

### D08 — Platt and colleagues

The nicotinamide cofactor biomimetic stability data and descriptors originate
from Platt and colleagues. D08 reuses the D07 data and partitions. The
sum-to-one coefficient constraint defining D08 was introduced in the present
DGDTL-LTS / U-MaxP study; it was not part of the original source study.
Please cite the source publication when using this example's data:

Platt, A. P.; Klem, H.; Mallinson, S. J. B.; Bomble, Y. J.; Paton, R. S.
**Computer-aided design of stability enhanced nicotinamide cofactor biomimetics
for cell-free biocatalysis.** *Green Chemistry* **2025**, *27*, 6831–6844.
[DOI: 10.1039/D5GC00351B](https://doi.org/10.1039/D5GC00351B).

### D11 — Original data and COBRA reprocessing

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

### S03 — Synthetic dataset from this study

S03 is part of the synthetic dataset collection developed for the present
DGDTL-LTS / U-MaxP study. The example includes its fixed training, validation,
and test partitions, together with the corresponding reference results.

These data-source citations complement the
[software citation](../CITATION.cff). The fixed example partitions and
DGDTL-LTS / U-MaxP reference analyses are contributions of the present study;
they should not be attributed to the authors of the original datasets.
The source keys used in the Supplementary Information are retained in
[DATA_PROVENANCE.md](DATA_PROVENANCE.md).

## Contents and working directories

Each example contains three `data_*.csv` files, one `DGDTL_Report_*.txt`
deployment guide, and the following reference directories:

```text
d01/
├── README.md
├── data_train.csv
├── data_valid.csv
├── data_test.csv
├── DGDTL_Report_L1_Scout_4.txt
└── reference_results/
    ├── unified/
    └── hunter/
```

Run from a separate working directory containing copies of only the input
CSVs and deployment guide. Keep the release and its reference results intact.
Choose a fresh working directory for each run to avoid mixing or overwriting
outputs. The supplied Unified guides write to `results/`; the Hunter commands
below use `results_hunter/`.

## Prepare a Linux example

First install the supplied wheels inside the frozen `dgdtl_v2` environment as
described in the [user guide](../docs/en/USER_GUIDE.md#certified-setup).
Python 3.12.12 and the frozen scientific dependencies are the reference setup;
the public imports are `dgdtl_lts` and `u_maxp` from that environment's
`site-packages`.

Replace the software path below and select a domain. These shell variables are
also used by the commands in each domain README.

```bash
mamba activate dgdtl_v2
DGDTL_SOFTWARE="/absolute/path/to/software"
DGDTL_DOMAIN="d01"
DGDTL_WORKDIR="$HOME/dgdtl_runs/${DGDTL_DOMAIN}_01"
mkdir -p "$DGDTL_WORKDIR"
cp "$DGDTL_SOFTWARE/examples/$DGDTL_DOMAIN/"data_*.csv \
   "$DGDTL_SOFTWARE/examples/$DGDTL_DOMAIN/"DGDTL_Report_*.txt \
   "$DGDTL_WORKDIR/"
cd "$DGDTL_WORKDIR"
```

Follow the selected domain README to run Unified or Hunter. The cluster job
scripts in the historical evidence are site-specific and are not required for
these local examples.

## Prepare a Windows example

Use Windows x86-64, PowerShell 5.1, and Docker Desktop with the WSL2 backend
and Linux containers. Keep the complete `software` directory, including the
official runtime and bundled offline-font package. Scientific execution uses
the frozen Python environment inside that runtime; host Python is unnecessary.

Replace the software path and select a domain. These PowerShell variables are
also used by the commands in each domain README.

```powershell
$DGDTLSoftware = 'C:\DGDTL\software'
$DGDTLDomain = 'd01'
$DGDTLWorkdir = Join-Path $env:USERPROFILE "dgdtl_runs\${DGDTLDomain}_01"
New-Item -ItemType Directory -Path $DGDTLWorkdir -Force | Out-Null
Copy-Item -Path "$DGDTLSoftware\examples\$DGDTLDomain\data_*.csv", `
                "$DGDTLSoftware\examples\$DGDTLDomain\DGDTL_Report_*.txt" `
          -Destination $DGDTLWorkdir
Set-Location $DGDTLWorkdir
```

Follow the selected domain README. Invoke the `.cmd` launchers from this
working directory so that Unified can see the CSVs and guide. At first font
preparation, review the included Microsoft EULA and enter `I ACCEPT` if you
accept its terms. The original package is included; no font download is needed.
See the [Windows launcher instructions](../launchers/windows/README.md) for
transport requirements and diagnostics.

## Read and compare results

Each domain README links to the main Unified selection report and Hunter
ranking and framework report. Compare a new run against the corresponding
workflow under `reference_results/`, using the same inputs and configuration.
Read [reference provenance and comparison rules](REFERENCE_RESULTS.md) before
interpreting differences. The 304 supplied reference files occupy 10,602,679
bytes and can be inspected without executing either workflow.

The reference set contains Linux outputs only. The previously completed
Linux/Windows Docker certification remains separate evidence; native Windows
Python, macOS, and ARM execution are outside that certified scope. D11's
preserved Hunter `FAIL` diagnostics are part of the scientific example and
must be interpreted separately from successful reproducibility checks.

These examples teach the workflow and support verification; they do not replace
an independent study design. Dataset origins are documented in
[DATA_PROVENANCE.md](DATA_PROVENANCE.md). Selection of figures or results for
the manuscript is a separate editorial decision.
