# u-maxp

`u-maxp` version 1.0.0 provides the stateless U-MaxP criterion, associated
observables, arbitration primitives, and the reference Structural Selection
Protocol used by DGDTL-LTS. Its public import is `u_maxp`. Reference use requires
Python 3.12.12 and the frozen `dgdtl_v2` scientific environment.

## Linux installation

Prepare and check the environment using the
[environment instructions](../../environment/README.md). An existing prepared
environment only needs to be activated in the current shell.

Run these commands from the **`software` directory**, not from this package
directory:

```bash
mamba activate dgdtl_v2
python -m pip install --no-index --no-deps dist/u_maxp-1.0.0-py3-none-any.whl
python -m pip check
```

Dependencies must already be installed in the environment. The supplied
Hunter and Unified workflows also use `dgdtl-lts`; the
[shared installation procedure](../../environment/README.md#linux-install-the-supplied-wheels)
installs both wheels. Local wheel installation does not assume package-index
publication and does not require rebuilding either package.

For an existing installation, check the interpreter, version, and public import:

```bash
python --version
python -c "import sys, importlib.metadata as m, u_maxp; print(sys.executable); print(m.version('u-maxp')); print(u_maxp.__file__)"
```

Expect Python 3.12.12, package version 1.0.0, and an import path beneath the
active environment's `site-packages`.

## Windows execution

The supplied Windows Hunter and Unified launchers use the installed packages
inside the frozen Certified Runtime. Windows users keep the complete
`software` distribution and place inputs and new outputs in a separate working
directory. No host scientific Python installation is needed. See the
[platform requirements](../../README.md#files-needed-for-each-use) and
[Windows example setup](../../examples/README.md#prepare-a-windows-example).

The existing Windows launchers expose Hunter and Unified; they do not provide
a generic entry point for arbitrary researcher scripts.

## Public API

```python
from u_maxp import (
    ProtocolConfig,
    StructuralSelectionProtocol,
    TopologicalEngine,
    UMaxPCriterion,
)
```

The public namespace exports the following groups, as defined in the
[preserved core source](src/u_maxp_core.py):

| Group | Public names |
| --- | --- |
| Reference constants and verdicts | `EPS_F`, `DELTA_REL`, `EPS_TIE`, `EPS_PSI`, `ProtocolConfig`, `ProtocolVerdictCodes` |
| Observables and criterion | `TopologicalEngine`, `EVTAnalyzer`, `ConsistencyEngine`, `UMaxPCriterion` |
| Structural and framework metrics | `StructuralMetricsEngine`, `FrameworkMetricsEngine` |
| Arbitration | `u_comp_operator`, `e_inc_operator`, `MicroArbitration`, `PhaseEvaluator`, `Phase3TieBreaker` |
| Selection and compatibility interface | `StructuralSelectionProtocol`, `StructuralFramework` |

`ProtocolConfig` contains the calibrated constants used by the reference
protocol. The supplied scientific definitions and selection rules remain fixed.

## Criterion and selection protocol

`UMaxPCriterion` exposes stateless calculations from already prepared scientific
observables. For example, the following pattern assumes that `sde_b`, `gci`,
`a_emp`, `tau_anchor`, and `emax_rob` have been computed with the appropriate
definitions and scales for a non-baseline candidate:

```python
u_value = UMaxPCriterion.compute_umaxp(sde_b=sde_b, gci=gci, a_emp=a_emp)
kappa = UMaxPCriterion.compute_kappa(tau_anchor=tau_anchor, emax_rob=emax_rob)
u_value_k = UMaxPCriterion.compute_umaxp_k(u_maxp=u_value, kappa=kappa)
```

This computes criterion values. The full structural selection protocol also
uses candidate relationships, baseline comparisons, and the recorded
arbitration rules; choosing the largest scalar alone does not reproduce it.

`StructuralSelectionProtocol` accepts an already prepared pandas metric table.
For a table named `metrics_df` that follows the reference schema:

```python
protocol = StructuralSelectionProtocol(metrics_df, source_name="Researcher metrics")
ranked_metrics = protocol.execute()
```

The input must preserve the complete metric schema constructed by the
[reference Hunter](../../orchestrators/dgdtl_hunter_umaxp_cluster.py), including
candidate labels, `Scout_Base`, `Run_ID`, the required baseline records, and
the numerical observables consumed by the protocol. In particular,
`BASELINE_TRAIN_ONLY` is a required baseline label. The source defines the
complete requirements; the fields mentioned here are not an exhaustive schema.
Keep row identities and ordering consistent with that construction.

The constructor copies the supplied table, and `execute()` returns the ranked
DataFrame with the protocol diagnostics. The optional `logger` argument
provides reporting callbacks; omitting it uses the built-in no-op logger.
This protocol consumes metrics rather than raw train/validation/test CSVs and
does not train a `DGDTLEstimator` or generate the full Hunter output directory.

## Use from a researcher script

On Linux, activate `dgdtl_v2` and import the required objects from `u_maxp` in
your script. Prepare the scientific observables and protocol inputs before
calling the relevant interface. Use the existing Hunter and Unified source
as the reference for their respective metric construction and selection flow.

The [DGDTL-LTS package](../dgdtl-lts/README.md) supplies the estimator. The
orchestrators combine the packages with workflow configuration and reporting;
their companion files are separate from the wheels. See the
[file requirements](../../README.md#files-needed-for-each-use) and
[complete examples](../../examples/README.md) for those execution routes.

## Reproducibility

`u_maxp_core` remains installed for legacy compatibility. New code should use
imports from `u_maxp`. The packaged core is bytewise identical to the certified
Golden Master; wheel identities and historical build details are recorded in
the [build record](../../manifests/BUILD_RECORD.md).

The [certification scope](../../README.md#reproducibility-scope) covers the
recorded artifacts, environment, workflows, and comparisons. Importing the
package or computing a criterion value does not automatically certify a new
researcher script, an input metric table, or a scientific conclusion. For a
reference reproduction, retain the existing
[exact comparison rules](../../examples/REFERENCE_RESULTS.md).

## Citation and license

Use the [software citation](../../CITATION.cff) and the relevant
[data-source references](../../examples/README.md#data-sources-and-references)
when using the examples. License: [MIT](LICENSE).

## Contact

For questions regarding conceptualization and support, contact:
jandrespmen@gmail.com
