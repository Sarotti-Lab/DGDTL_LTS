# Layer 3 Certificate — DGDTL-LTS / U-MaxP 1.0.0

## Status

**PASS — executable scientific payload validated.**

The Layer 3 certificate establishes exact equivalence of the packaged engines
and the validated pre-PyPI scientific behavior under the certified environment.
It does not certify Windows or macOS, nor does it grant a third-party-data
redistribution licence.

## Immutable cores

```text
dgdtl_core.py  25e0663160e0379e5f2fbac6ae86091bc51c8c07552aa27d3050148b0b2621b6
u_maxp_core.py 88559753226df385afedf978e85d785f9c0a1dcb2840c0967174cc6112d4ce53
```

The package source copies compare byte for byte with these Golden Masters.

## Environment and installation

- Environment: `dgdtl_v2` from `environment/dgdtl_v2.yml`.
- Python: 3.12.12.
- Install mode: offline wheels with `--no-index --no-deps` into that environment.
- Import paths: verified from the active environment's `site-packages`.
- Dependency consistency: `python -m pip check` passed.

## Evidence

The validation method and complete scope are in `VALIDATION_METHOD.md`.
Exact reproducibility was verified on two independent Ubuntu 24.04 systems and
two high-performance computing clusters in Argentina under the frozen reference
environment.
Original wheels and raw Layer 3 evidence remain immutable in `../PyPI_cp/`.
The documented-wheel rebuild is recorded in `../manifests/BUILD_RECORD.md`.
It was reproducible byte for byte and preserves the core payload exactly.
`../manifests/RELEASE_CONTENTS.sha256` records the complete curated release
tree for exact Capa 2 and Capa 1 transfer verification.
