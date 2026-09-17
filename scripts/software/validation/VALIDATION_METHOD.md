# Layer 3 validation method

Validation compared packaged-wheel executions with both local and cluster
outputs and with the immutable pre-PyPI references. The two scientific engines
were never modified for packaging.

## Exact comparison policy

- CSV numerical outputs: byte comparison, `DataFrame.equals`,
  `numpy.array_equal(equal_nan=True)`, and `float.hex()` for critical floating
  values.
- Text reports: byte equality when possible; otherwise exact equality after
  removing only documented dynamic fields such as date and execution duration.
- PNG: SHA-256 byte equality.
- PDF: when metadata caused byte differences, equality of extracted text and
  rendered pages by SHA-256.

No tolerance-based `allclose` substitution was used.

## Certified matrix

All eleven selected domains — D01, D02, D04, D06, D07, D08, D9B, D9C, D11,
D12, and S03 — were executed for Hunter and Unified. Exact reproducibility was
verified across two independent Ubuntu 24.04 systems and two independent Linux
high-performance computing clusters in Argentina, with the immutable pre-PyPI
output retained as the scientific reference.

Hunter compared 280 artifacts: 183 CSV artifacts were byte/numerically exact;
97 report files differed only in normalized dynamic metadata. Unified compared
325 artifacts: 139 CSV and 76 PNG artifacts were byte/numerically exact; 66
text artifacts were exact directly or after dynamic-metadata normalization; 44
PDF artifacts had identical extracted text and rendered pages.

S03 is certified by its completed artifact comparison rather than by a launcher
log. Raw runs, transient logs, and exploratory records are preserved in
`../PyPI_cp/`, not in this curated distribution.
