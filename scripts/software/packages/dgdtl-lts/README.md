# dgdtl-lts

`dgdtl-lts` version 1.0.0 provides the deterministic DGDTL-LTS regression
engine used by the reference workflow. Its public import is `dgdtl_lts`, which
exports `DGDTLEstimator`. Reference use requires Python 3.12.12 and the frozen
`dgdtl_v2` scientific environment.

## Linux installation

Prepare the environment using the
[environment instructions](../../environment/README.md), including the check
against the recorded scientific package versions. If that environment already
exists, activate it instead of creating it again.

Run these commands from the **`software` directory**, not from this package
directory:

```bash
mamba activate dgdtl_v2
python -m pip install --no-index --no-deps dist/dgdtl_lts-1.0.0-py3-none-any.whl
python -m pip check
```

The wheel installs the package; its dependencies must already be present in
the environment. The supplied Hunter and Unified workflows also require
`u-maxp`; the [shared installation procedure](../../environment/README.md#linux-install-the-supplied-wheels)
installs both wheels. These commands use local artifacts and do not assume
that either distribution has been published to a package index.

For an existing installation, confirm the interpreter, version, and public
import location:

```bash
python --version
python -c "import sys, importlib.metadata as m, dgdtl_lts; print(sys.executable); print(m.version('dgdtl-lts')); print(dgdtl_lts.__file__)"
```

Expect Python 3.12.12, package version 1.0.0, and an import path beneath the
active environment's `site-packages`.

## Windows execution

Windows users run the supplied Hunter and Unified launchers through the
Certified Runtime, which already contains the installed scientific packages.
No host Python installation or package build is required. Keep the complete
`software` distribution and use a separate working directory for inputs and
new results. See the [platform requirements](../../README.md#files-needed-for-each-use)
and [Windows example setup](../../examples/README.md#prepare-a-windows-example).

The existing Windows launchers expose Hunter and Unified. They do not provide
a generic command for executing an arbitrary researcher script.

## Public API

The following raw-mode usage pattern assumes that the researcher has already
prepared the numeric arrays `X_train`, `y_train`, `X_valid`, `y_valid`, and
`X_test`. It illustrates the estimator interface; reproducing a supplied
domain requires that domain's full configuration and preprocessing.

```python
from dgdtl_lts import DGDTLEstimator

estimator = DGDTLEstimator(
    mode="raw",
    fit_intercept=False,
    beta_sum_one=True,
    random_state=42,
)
estimator.fit(X_train, y_train, X_valid, y_valid)
prediction = estimator.predict(X_test)
```

`X_train`, `X_valid`, and `X_test` must use the same feature columns in the
same order. Targets are separate one-dimensional arrays aligned with the
corresponding rows. Do not include sample identifiers or the target column in
the predictor matrix. If `fit_intercept=True`, the estimator adds its own
intercept column.

The caller supplies feature construction, normalization, and consistent
transforms between partitions. The estimator does not parse deployment guides
or automatically reproduce the preprocessing performed by Unified.

| Interface | Purpose |
| --- | --- |
| `calibrate(X, y)` | Compute baseline coefficients for the supplied arrays. |
| `fit(X_train, y_train, X_valid, y_valid)` | Run baseline calibration when needed, the two search phases, filtering, and estimator champion selection; return the fitted estimator. |
| `predict(X, y_reference=None, beta=None)` | Predict using `champion_['coeffs']` by default, or the explicitly supplied coefficients. |

In `raw` mode, `predict(X)` returns predictions on the scale of the supplied
model inputs and coefficients. In `error_matrix` mode, `X` is the prepared
error matrix and prediction requires `y_reference`; the method adds the
coefficient-weighted correction to that reference. These modes are not
interchangeable input representations.

After a successful fit, the existing attributes include `baseline_coeffs_`,
`baseline_mse_`, `champion_run1_`, `champion_run2_`, `champion_`,
`run1_report_df_`, and `run2_report_df_`. The estimator's default prediction
uses its own selected champion. The complete cross-candidate U-MaxP structural
selection is performed separately by the protocol and reference orchestrators;
a direct `fit` call does not run the complete Hunter workflow.

The [preserved estimator source](src/dgdtl_core.py) defines the exact
constructor parameters, method signatures, and behavior. Configuration choices
such as bounds, thresholds, normalization, and process parallelism belong to
the researcher's execution design. Training can be computationally intensive.

## Use from a researcher script

On Linux, activate the prepared environment and run your script with its Python.
The package is imported from `site-packages`; copying `dgdtl_core.py` into the
working directory is unnecessary and can shadow the installed module. Your
script remains responsible for loading inputs, preparing arrays, preserving
configuration, and writing its outputs.

The package wheel supplies the engine and public interface. Hunter, Unified,
reporting modules, launchers, datasets, and example results are separate parts
of the distribution. Consult the [file requirements](../../README.md#files-needed-for-each-use)
for the selected workflow. For a complete worked example, use the
[example instructions](../../examples/README.md) and their supplied guides.

## Reproducibility

The package includes `dgdtl_core` as a legacy compatibility module. New code
should import `DGDTLEstimator` from `dgdtl_lts`. The packaged core is bytewise
identical to the certified Golden Master. Artifact identities and original
build details are preserved in the [build record](../../manifests/BUILD_RECORD.md).

The [documented certification scope](../../README.md#reproducibility-scope)
applies to the recorded environment, artifacts, workflows, and comparison
conditions. It does not automatically certify new researcher scripts, altered
configurations, or new datasets. Use the existing
[reference comparison rules](../../examples/REFERENCE_RESULTS.md) when
interpreting a reproduction attempt.

## Citation and license

Use the [software citation](../../CITATION.cff) for DGDTL-LTS / U-MaxP and the
[example references](../../examples/README.md#data-sources-and-references)
when using the associated datasets. License: [MIT](LICENSE).

## Contact

For questions regarding conceptualization and support, contact:
jandrespmen@gmail.com
