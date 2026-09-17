# Orchestrator provenance

## Original validated copies

- Hunter SHA-256:
  `0ad4b2527dc70d3beed87d543962ee983dfb8d1bd8c34e56e152958cfef47d18`
- Unified SHA-256:
  `e8d6a83be2f16471215c4ab8332271e3e7248c63f05c40304a72551c9d4a1c00`

These hashes match both `scripts/source/` and every applicable local
`scripts/source/pre_PyPI/` copy.

## Package-import candidates

- Hunter SHA-256:
  `5fa2379b8155951aa3e3b8d35543c988e84c81aa56104c8e78408ce6ded6762c`
- Unified SHA-256:
  `1503d0d1ccbb3d6d9ccb71172a2be4a16702d2e58d164973f28985d02110541c`

The Hunter candidate differs only in these import targets:

```text
dgdtl_core  -> dgdtl_lts
u_maxp_core -> u_maxp
```

Its two `ImportError` messages were also updated to name the public
distributions and import packages instead of the old sibling core filenames.

The Unified candidate has the same two import-target substitutions. No formula,
parameter, threshold, seed, branch, candidate ordering, or scientific
orchestration logic was modified.
