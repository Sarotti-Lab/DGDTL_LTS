# Layer 3 Curated Build Record

- Release: `1.0.0`
- Curated build date: `2026-08-26`
- Python: `3.12.12` in `dgdtl_v2`
- pip: `26.1.1`
- setuptools: `82.0.1`
- wheel: `0.47.0`
- `SOURCE_DATE_EPOCH`: `1767225600` (`2026-01-01T00:00:00Z`)
- `PYTHONHASHSEED`: `0`
- Build mode: `pip wheel --no-deps --no-build-isolation`

## Curated wheels

- `dgdtl_lts-1.0.0-py3-none-any.whl`
  - SHA-256: `debe10053115fd3a6014f75502086ef8ac5a37dc1e20bf26546614585e6d404d`
- `u_maxp-1.0.0-py3-none-any.whl`
  - SHA-256: `781debee6ac96d0ac42677d64afa9a6287eb9d9033f7b3a83bf7bcbbe964a0ea`

The two builds performed with the recorded inputs were byte-identical for each
wheel. Wheel inventory inspection confirmed that the only executable modules
are the certified core module and public package initializer. The embedded core
hashes are the Golden Master values:

```text
dgdtl_core.py  25e0663160e0379e5f2fbac6ae86091bc51c8c07552aa27d3050148b0b2621b6
u_maxp_core.py 88559753226df385afedf978e85d785f9c0a1dcb2840c0967174cc6112d4ce53
```

The earlier installation-test wheels and their hashes remain preserved without
modification in `../../PyPI_cp/`.
