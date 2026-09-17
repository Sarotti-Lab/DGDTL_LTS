# Changelog

## 2026-09-15 — Windows functional-status documentation (1.0.0)

- Recorded that the Hunter and Unified Windows launchers are functional under
  PowerShell 5.1, without enumerating functional-test domains. Kept this status
  separate from the completed scientific certification.
- Replaced outdated pending-status and menu wording in the Windows README and
  aligned the functional-status statement in the main README. Commands,
  launchers, runtime, and scientific behavior remain unchanged.
- Updated only the hashes of these two README files and this changelog in the
  release-content manifest.

## 2026-09-15 — Cluster acknowledgment language update (1.0.0)

- Added an English translation of the Capitán acknowledgment emitted by
  `launchers/cluster/create_job_dgdtl_lts.py`, preserving the original mandatory
  Spanish text and institutional names. The Serafín acknowledgment was already
  in English and remains unchanged.
- Limited generated-job differences to the added acknowledgment text and its
  separating blank line. Resource policies, scheduler directives, environment
  setup, Hunter commands, scratch cleanup, and submission behavior are unchanged.
- Updated only the script and changelog hashes in the release-content manifest.
  No scientific execution or recertification was performed.

## 2026-09-15 — Layer 3 documentation update (1.0.0)

- Clarified Hunter's design for complete-search execution on computing
  clusters and its supported local execution on Linux and on Windows through the
  supplied Docker/WSL2 launchers, subject to adequate resources for the domain.
  Added the clarification to the release, orchestrator, launcher, and examples
  overview README files and both user manuals, without changing commands or
  the existing certification scope.
- Documented the approved `software/` release-directory name without changing
  package names, public imports, or historical provenance paths.
- Updated the release, environment, package, orchestrator, and launcher README
  files to explain installation, public APIs, execution files, and platform
  requirements from the existing implementation.
- Documented the selected examples, their original data publications, and the
  304 preserved Linux reference outputs, with provenance and comparison rules
  separate from new executions. Retained D11's diagnostic interpretation and
  S03's attribution to this study's synthetic dataset collection.
- Aligned the English and Spanish user manuals: native Linux setup, existing
  Windows Docker/WSL2 execution, required components, own-data and example
  workflows, working directories, configuration, and expected outputs.
- Clarified that Windows uses a subset of components for execution while its
  existing launcher verifies every file in the release manifest. New outputs
  written outside `software/` do not require manifest changes.
- Corrected the manuals' description of Unified guide-mode paths: input CSV
  names and `results/` are defaults of the executor, not paths read from the
  guide. Documented interactive configuration separately.
- Distinguished the original native Linux certification from the subsequently
  completed Linux/Windows runtime certification and from user-experience checks.
- Synchronized hashes of the edited documentation in the release-content
  manifest without changing the current file inventory or verification logic.

This documentation update changes no scientific code, parameters, package
artifacts, environment definitions, runtime, Windows transport, controlled-font
resources, or preserved reference outputs. It adds no scientific execution or
recertification. Final manual acceptance of Layer 3 remains a separate review.

## 1.0.0 — Layer 3 release candidate

- Packaged the byte-preserved DGDTL-LTS and U-MaxP Golden Masters.
- Added public imports `dgdtl_lts` and `u_maxp` while retaining legacy-module
  compatibility.
- Certified installation from wheels in the mandatory `dgdtl_v2` environment.
- Compared Hunter and Unified outputs across local, cluster, and pre-PyPI
  references using exact scientific comparisons.
- Curated D01, D02, D08, D11, and S03 as public examples.
- Verified exact reproducibility on two independent Ubuntu 24.04 systems and
  two high-performance computing clusters in Argentina.

No scientific algorithm, constant, threshold, seed, ordering, or selection
rule was changed for packaging.
