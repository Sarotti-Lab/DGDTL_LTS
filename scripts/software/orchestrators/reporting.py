# SPDX-FileCopyrightText: 2026 José A. Pérez
# SPDX-License-Identifier: MIT

"""
DGDTL-LTS Scientific Reporting Module
Model Evaluation, Statistical Diagnostics & Stability Reporting
================================================================

Abstract:
---------
This module provides the centralized text-based and tabular reporting
architecture used by DGDTL-LTS analysis workflows. It generates standardized
reports for predictive performance, baseline evaluation, residual diagnostics,
cross-validation stability, coefficient stability, overfitting assessment,
and structured CSV output.

The module operates on numerical results supplied by external workflows and
does not execute DGDTL-LTS optimization or U-MaxP structural selection.

Key Architectural Features:
---------------------------
1. Statistical Diagnostic Reporting
   Generates residual-analysis reports including Shapiro-Wilk normality
   assessment, Breusch-Pagan homoscedasticity testing, leverage analysis,
   and Cook's-distance diagnostics.

2. Performance Reporting
   Produces structured model-evaluation reports containing hyperparameter
   summaries, coefficient tables, MAE, MSE, R-squared, maximum absolute error,
   normalization status, and optional training-duration information.

3. Baseline Reporting
   Generates dedicated DGDTL baseline reports for original and retrained
   coefficient sets, including performance metrics across training,
   validation, testing, and combined evaluation subsets.

4. Tabular Output Management
   Provides standardized CSV writers for full numerical results, model
   summaries, and overfitting-analysis datasets.

5. Cross-Validation & Stability Reporting
   Generates cross-validation reports describing training-versus-validation
   performance, hyperparameter stability, coefficient means and dispersion,
   coefficient variation, and fold-level coefficient behavior.

6. Public Functional API
   Exposes function-level facades around the reporting classes so external
   orchestration scripts can generate reports without depending directly on
   the internal class structure.

Sections:
---------
1. Shared Constants & Formatters
   - ALPHA_LEVEL
   - format_max_error_section

2. Statistical Reporting
   - StatisticalReportGenerator

3. Performance Reporting
   - PerformanceReportGenerator

4. Baseline Reporting
   - BaselineReportGenerator

5. CSV Output Management
   - CSVReportManager

6. Cross-Validation & Stability Reporting
   - CVStabilityReportGenerator

7. Public API
   - generate_statistical_report
   - generate_performance_report
   - generate_baseline_report
   - save_full_results_csv
   - save_model_summary_csv
   - save_overfitting_analysis_csv
   - generate_cv_stability_report

Usage:
------
Designed as an auxiliary scientific reporting module for DGDTL-LTS
orchestration and analysis workflows. The public API accepts model results,
residuals, coefficients, performance metrics, and cross-validation data
generated externally and produces standardized text and CSV reports without
executing optimization or structural-selection logic.

Author:
-------
DGDTL Research Team
Prof. José A. Pérez (JP)

Copyright:
----------
Copyright (c) 2026 José A. Pérez.

License:
--------
MIT License. See the LICENSE file distributed with this software.
"""

import os
from datetime import datetime 
from typing import List, Dict, Any, Union, Optional

import numpy as np
import pandas as pd
import scipy.stats as stats
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.tools.tools import add_constant

# --- Constants ---
ALPHA_LEVEL = 0.05

def format_max_error_section(
    data: Dict[str, Dict[str, Any]],
    key_name: str = "MaxErr",
    title: str = "Maximum Absolute Error (MaxErr)",
    dataset_names: Optional[List[str]] = None,
    name_width: int = 12,
    value_width: int = 8,
    sep: str = "",
) -> str:
    """
    Shared formatter for the 'Maximum Absolute Error' section, used by both
    PerformanceReportGenerator (champion reports) and BaselineReportGenerator
    (baseline report). Intentionally restricted to the base subsets only
    (Training / Validation / Testing) — combined sets (Train+Valid,
    Valid+Testing) are excluded by design. A 'Global' row is appended with
    the maximum across the base subsets found in `data` (max of maxes ==
    global max, no extra computation needed).
    """
    if dataset_names is None:
        dataset_names = ['Training', 'Validation', 'Testing']

    lines = [f"\n{title}", "-" * len(title)]
    values = []
    for name in dataset_names:
        entry = data.get(name)
        if entry and key_name in entry and entry[key_name] is not None:
            v = entry[key_name]
            values.append(v)
            lines.append(f"{name:<{name_width}}{sep}{v:>{value_width}.4f}")

    if values:
        lines.append(f"{'Global':<{name_width}}{sep}{max(values):>{value_width}.4f}")

    return "\n".join(lines)


# ==========================================
# OOP Core Classes
# ==========================================

class StatisticalReportGenerator:
    """Class responsible for building and saving statistical analysis reports."""
    
    def __init__(self, model_name: str, residuals: np.ndarray, X_data: pd.DataFrame, output_path_base: str):
        self.model_name = model_name
        self.residuals = residuals
        self.X_data = X_data
        self.output_path_base = output_path_base
        self.n_samples, self.n_features = X_data.shape
        self.p = self.n_features + 1  # Number of predictors including intercept
        self.report_lines = []

    def _build_header(self):
        self.report_lines.append(f"--- STATISTICAL ANALYSIS FOR MODEL: {self.model_name} ---")
        self.report_lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def _analyze_normality(self):
        # The Shapiro-Wilk test is suitable for sample sizes from 3 to 5000.
        if 3 <= self.n_samples < 5000:
            self.report_lines.append("\n\n1. Normality of Residuals")
            self.report_lines.append("--------------------------")
            shapiro_test = stats.shapiro(self.residuals)
            self.report_lines.append(f"   - Test: Shapiro-Wilk")
            self.report_lines.append(f"   - Statistic: {shapiro_test.statistic:.4f}, p-value: {shapiro_test.pvalue:.4f}")
            if shapiro_test.pvalue > ALPHA_LEVEL:
                conclusion = "The residuals appear to be normally distributed. (✓ Assumption met)"
            else:
                conclusion = "The residuals are likely not normally distributed. (X Assumption not met)"
            self.report_lines.append(f"   - Conclusion: {conclusion}")
        else:
            self.report_lines.append("\n\n1. Normality of Residuals")
            self.report_lines.append("--------------------------")
            self.report_lines.append(f"   - Shapiro-Wilk test skipped (Sample size {self.n_samples} is outside the valid range [3, 5000]).")

    def _analyze_homoscedasticity(self):
        self.report_lines.append("\n\n2. Homoscedasticity of Residuals (Constant Variance)")
        self.report_lines.append("-----------------------------------------------------")
        # Breusch-Pagan test requires the design matrix (X) with an intercept.
        X_with_const = add_constant(self.X_data, prepend=True)
        try:
            bp_test = het_breuschpagan(self.residuals, X_with_const)
            self.report_lines.append(f"   - Test: Breusch-Pagan")
            self.report_lines.append(f"   - LM Statistic: {bp_test[0]:.4f}, p-value: {bp_test[1]:.4f}")
            if bp_test[1] > ALPHA_LEVEL:
                conclusion = "The variance of the residuals appears constant (homoscedastic). (✓ Assumption met)"
            else:
                conclusion = "Heteroscedasticity is likely present (non-constant variance). (X Assumption not met)"
            self.report_lines.append(f"   - Conclusion: {conclusion}")
        except Exception as e:
            self.report_lines.append(f"   - Breusch-Pagan test failed: {e}")
        return X_with_const

    def _analyze_influential_points(self, X_with_const):
        self.report_lines.append("\n\n3. Influential Points Analysis")
        self.report_lines.append("------------------------------")
        
        try:
            # Hat matrix diagonal (leverage) calculation
            hat_matrix_diag = np.diag(X_with_const @ np.linalg.inv(X_with_const.T @ X_with_const) @ X_with_const.T)
            
            # Mean Squared Error of residuals
            mse_residuals = np.sum(self.residuals**2) / (self.n_samples - self.p)
            
            # Cook's Distance calculation
            cooks_d = (self.residuals**2 / (self.p * mse_residuals)) * (hat_matrix_diag / (1 - hat_matrix_diag)**2)

            # Thresholds for identifying influential points
            leverage_threshold = 2 * self.p / self.n_samples
            high_leverage_count = np.sum(hat_matrix_diag > leverage_threshold)
            high_leverage_pct = (high_leverage_count / self.n_samples) * 100
            
            cooks_d_half_count = np.sum(cooks_d > 0.5)
            cooks_d_one_count = np.sum(cooks_d > 1.0)
            
            self.report_lines.append(f"   - High Leverage Points (> 2*p/n = {leverage_threshold:.3f}): {high_leverage_count} ({high_leverage_pct:.2f}%)")
            self.report_lines.append(f"   - Points with Cook's D > 0.5: {cooks_d_half_count}")
            self.report_lines.append(f"   - Points with Cook's D > 1.0: {cooks_d_one_count}")
            self.report_lines.append(f"   - Interpretation:")
            self.report_lines.append(f"       Points with high leverage have unusual predictor values. Points with a high Cook's Distance")
            self.report_lines.append(f"       have a strong influence on the model's results. These points can be inspected in the")
            self.report_lines.append(f"       'Residuals vs Leverage' plot.")
        except np.linalg.LinAlgError:
            self.report_lines.append("   - Analysis skipped: Could not compute leverage and Cook's distance due to a singular matrix.")
            self.report_lines.append("     This often occurs with perfect multicollinearity in the predictor data.")

    def generate_and_save(self):
        self._build_header()
        self._analyze_normality()
        X_with_const = self._analyze_homoscedasticity()
        self._analyze_influential_points(X_with_const)

        report_content = "\n".join(self.report_lines)
        report_filename_txt = self.output_path_base + '.txt'
        
        try:
            with open(report_filename_txt, "w", encoding='utf-8') as f:
                f.write(report_content)
            #print(f"Statistical analysis report saved to: {report_filename_txt}")
        except IOError as e:
            print(f"Error saving statistical report: {e}")


class PerformanceReportGenerator:
    """Class responsible for building and saving performance metrics reports."""
    
    def __init__(self, model_name: str, hyperparams: Dict[str, Any], coef_df: pd.DataFrame, 
                 metrics_by_dataset: Dict[str, Dict[str, Any]], output_path_base: str,
                 x_normalized: bool, y_normalized: bool, duration_minutes: Optional[float]):
        self.model_name = model_name
        self.hyperparams = hyperparams
        self.coef_df = coef_df
        self.metrics_by_dataset = metrics_by_dataset
        self.output_path_base = output_path_base
        self.x_normalized = x_normalized
        self.y_normalized = y_normalized
        self.duration_minutes = duration_minutes
        self.report_lines = []

    def _format_metric(self, title: str, key_name: str, data: Dict[str, Dict[str, Any]]) -> str:
        lines = [f"\n{title}", "-"*len(title)]
        for name in ['Training', 'Validation', 'Train+Valid', 'Testing', 'Valid+Testing']:
            if name in data:
                m = data[name]
                ci_key = f"{key_name}_CI"
                # Check if CI data exists before trying to format it
                if ci_key in m and m[ci_key] is not None and len(m[ci_key]) == 2:
                    lines.append(f"{name:<12}{m[key_name]:>8.4f} ({m[ci_key][0]:.4f}, {m[ci_key][1]:.4f})")
                else:
                    lines.append(f"{name:<12}{m[key_name]:>8.4f}")
        return "\n".join(lines)

    def _build_summary(self):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        hyperparam_parts = []
        for k, v in sorted(self.hyperparams.items()):
            if isinstance(v, float):
                hyperparam_parts.append(f"{k}={v:.6f}")
            elif isinstance(v, int):
                hyperparam_parts.append(f"{k}={v}")
            elif isinstance(v, tuple) and len(v) == 2 and all(isinstance(x, (float, np.float64)) for x in v):
                hyperparam_parts.append(f"{k}=({v[0]:.6f}, {v[1]:.6f})")
            else:
                hyperparam_parts.append(f"{k}={str(v)}")
        hyperparam_str = ", ".join(hyperparam_parts)
        
        self.report_lines.append(f"--- Summary of Model Evaluation ---")
        self.report_lines.append(f"Timestamp: {timestamp}")
        self.report_lines.append(f"Predictors Normalized (X): {self.x_normalized}")
        self.report_lines.append(f"Target Normalized (Y): {self.y_normalized}")
        if self.duration_minutes is not None:
            self.report_lines.append(f"Duration (Training Phase): {self.duration_minutes:.2f} minutes")
        self.report_lines.append(f"Model: {self.model_name} ({hyperparam_str})")
        self.report_lines.append("="*60)

    def _build_coefficients(self):
        if 'CI_2.5%' in self.coef_df.columns and 'CI_97.5%' in self.coef_df.columns:
            self.report_lines.append("\nCoefficients (with 95% CI):")
        else:
            self.report_lines.append("\nCoefficients:")
        self.report_lines.append(self.coef_df.to_string(index=False, float_format='%.6f'))

    def _build_metrics(self):
        self.report_lines.append("\n\n--- Performance Metrics (Original scale) ---")
        self.report_lines.append(self._format_metric("Mean Absolute Error (MAE)", "MAE", self.metrics_by_dataset))
        self.report_lines.append(self._format_metric("\nMean Squared Error (MSE)", "MSE", self.metrics_by_dataset))
        self.report_lines.append(self._format_metric("\nR-squared (R²)", "R²", self.metrics_by_dataset))
        self.report_lines.append(format_max_error_section(self.metrics_by_dataset))

    def generate_and_save(self):
        self._build_summary()
        self._build_coefficients()
        self._build_metrics()

        report_content = "\n".join(self.report_lines)
        report_filename_txt = self.output_path_base + '.txt'
        
        try:
            with open(report_filename_txt, "w", encoding='utf-8') as f:
                f.write(report_content)
            print(f"\nPerformance metrics report saved to: {report_filename_txt}")
            print("\n" + report_content) # Also print to console
        except IOError as e:
            print(f"Error saving performance report: {e}")


class BaselineReportGenerator:
    """Class responsible for building and saving the DGDTL baseline report.

    Mirrors PerformanceReportGenerator's structure/conventions, adapted to the
    baseline's specifics: two coefficient sets (Original vs Retrain) and
    metrics split between the original model (Training/Validation/Testing/
    Valid+Testing) and the retrained model (Train+Valid/Testing).
    """

    def __init__(self, mode: str, baseline_mse: float, n_formulas: int,
                 feature_names: List[str], coef_col_name: str,
                 original_coeffs: Union[np.ndarray, List[float]],
                 retrain_coeffs: Union[np.ndarray, List[float]],
                 mets_orig: List[Dict[str, Any]], mets_retr: List[Dict[str, Any]],
                 output_path_base: str):
        self.mode = mode
        self.baseline_mse = baseline_mse
        self.n_formulas = n_formulas
        self.feature_names = feature_names
        self.coef_col_name = coef_col_name
        self.original_coeffs = original_coeffs
        self.retrain_coeffs = retrain_coeffs
        self.mets_orig = mets_orig
        self.mets_retr = mets_retr
        self.output_path_base = output_path_base
        self.report_lines = []

    def _build_header(self):
        self.report_lines.append(
            f"--- DGDTL Baseline Report ---\nMode: {self.mode}\nBaseline MSE: {self.baseline_mse:.6f}"
        )
        if self.n_formulas:
            self.report_lines.append(f"Feature Engineering: {self.n_formulas} formulas applied.")

    def _build_coefficients(self):
        for title, coeffs in [("Coefficients (Original)", self.original_coeffs),
                               ("Coefficients (Retrain)", self.retrain_coeffs)]:
            lines = [f"\n{title}:", f"    {'Predictor':<25} {self.coef_col_name}"]
            lines.extend(f"    {n:<25} {c:12.6f}" for n, c in zip(self.feature_names, coeffs))
            self.report_lines.append("\n".join(lines))

    def _format_metric_block(self, title: str, key: str) -> str:
        lines = [f"\n{title}", "-" * len(title)]
        for m in self.mets_orig:
            lines.append(f"{m['Dataset']:<15} {m[key]:.4f}")
        lines.append(f"{'Train+Valid':<15} {self.mets_retr[0][key]:.4f} (Retrain)")
        lines.append(f"{'Testing':<15} {self.mets_retr[1][key]:.4f} (Retrain)")
        return "\n".join(lines)

    def _build_metrics(self):
        self.report_lines.append("\n--- Performance Metrics (Original scale) ---")
        self.report_lines.append(self._format_metric_block("Mean Absolute Error (MAE)", "MAE"))
        self.report_lines.append(self._format_metric_block("Mean Squared Error (MSE)", "MSE"))
        self.report_lines.append(self._format_metric_block("R-squared (R²)", "R²"))

        # Original model: only base subsets (Training/Validation/Testing), no combinations,
        # plus a Global row (max of the three).
        mets_by_dataset = {m['Dataset']: m for m in self.mets_orig}
        max_err_block = format_max_error_section(mets_by_dataset, name_width=15, value_width=0, sep=" ")

        # Retrained model (trained on Train+Valid): its only two evaluated sets are
        # Train+Valid and Testing — there is no separate Training/Validation split to
        # combine, so these aren't "combinations" in the sense excluded above. Add them
        # plus their own Global (Retrain) = max of the two.
        if 'MaxErr' in self.mets_retr[0] and 'MaxErr' in self.mets_retr[1]:
            retr_values = [self.mets_retr[0]['MaxErr'], self.mets_retr[1]['MaxErr']]
            retrain_lines = [
                f"{'Train+Valid':<15} {self.mets_retr[0]['MaxErr']:.4f} (Retrain)",
                f"{'Testing':<15} {self.mets_retr[1]['MaxErr']:.4f} (Retrain)",
                f"{'Global':<15} {max(retr_values):.4f} (Retrain)",
            ]
            max_err_block += "\n" + "\n".join(retrain_lines)

        self.report_lines.append(max_err_block)

    def generate_and_save(self):
        self._build_header()
        self._build_coefficients()
        self._build_metrics()

        report_content = "\n".join(self.report_lines)
        report_filename_txt = self.output_path_base + '.txt'

        try:
            with open(report_filename_txt, "w", encoding='utf-8') as f:
                f.write(report_content)
            print(f"\nBaseline report saved to: {report_filename_txt}")
        except IOError as e:
            print(f"Error saving baseline report: {e}")


class CSVReportManager:
    """Utility class containing static methods for saving various tabular data as CSVs."""
    
    @staticmethod
    def save_full_results(results_df: pd.DataFrame, output_path_base: str) -> None:
        try:
            filename = output_path_base + '_Full_Results.csv'
            results_df.to_csv(filename, index=False, float_format="%.6f")
            print(f"Full results saved to: {filename}")
        except (IOError, AttributeError) as e:
            print(f"Error saving full results CSV: {e}")

    @staticmethod
    def save_model_summary(model_name: str, predictors: List[str], coefficients: Union[np.ndarray, List[float]], 
                           metrics_by_dataset: Dict[str, Dict[str, Any]], output_path_base: str) -> None:
        try:
            summary_data = {'Model_Name': model_name}
            
            for pred, coef in zip(predictors, coefficients):
                summary_data[f'Coef_{pred}'] = coef
            
            for metric in ['MAE', 'MSE']:
                for dataset in ['Training', 'Validation', 'Train+Valid']:
                    key_name = f'{metric}_{dataset.lower().replace("+", "_")}'
                    summary_data[key_name] = metrics_by_dataset.get(dataset, {}).get(metric)

            summary_df = pd.DataFrame([summary_data])
            filename = output_path_base + '_Model_Summary.csv'
            summary_df.to_csv(filename, index=False, float_format="%.6f")
            print(f"Model summary saved to: {filename}")
        except Exception as e:
            print(f"Error saving model summary CSV: {e}")

    @staticmethod
    def save_overfitting_analysis(fold_results_df: pd.DataFrame, output_path: str) -> None:
        parameter_cols = ['alpha', 'l1_ratio']
        metric_cols = [
            'mae_train', 'mse_train', 'r2_train',
            'mae_validation', 'mse_validation', 'r2_validation'
        ]
        
        columns_to_save = ['fold']
        for col in parameter_cols:
            if col in fold_results_df.columns:
                columns_to_save.append(col)
                
        columns_to_save.extend(metric_cols)
        existing_cols = [col for col in columns_to_save if col in fold_results_df.columns]
        df_to_save = fold_results_df[existing_cols]
        
        df_to_save.to_csv(output_path, index=False, float_format='%.5f')
        print(f"Overfitting analysis data saved to: {output_path}")


class CVStabilityReportGenerator:
    """Class responsible for generating the cross-validation and stability text report."""
    
    def __init__(self, fold_results_df: pd.DataFrame, predictors: List[str], output_path: str, cv_method: str):
        self.fold_results_df = fold_results_df
        self.predictors = predictors
        self.output_path = output_path
        self.cv_method = cv_method
        self.coefs_df = pd.DataFrame(fold_results_df['coefficients'].tolist(), columns=predictors)

    def _write_header(self, f):
        f.write("="*80 + "\n")
        f.write(f"Cross-Validation Stability & Overfitting Report - Method: {self.cv_method}\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")

    def _write_overfitting_analysis(self, f):
        f.write("--- Overfitting Analysis (Mean Metrics) ---\n")
        f.write(f"{'Metric':<10} {'Train Set':<25} {'Validation Set':<25}\n")
        f.write("-"*65 + "\n")

        mean_mae_train = f"{self.fold_results_df['mae_train'].mean():.4f} (+/- {self.fold_results_df['mae_train'].std():.4f})"
        mean_mae_valid = f"{self.fold_results_df['mae_validation'].mean():.4f} (+/- {self.fold_results_df['mae_validation'].std():.4f})"
        f.write(f"{'MAE':<10} {mean_mae_train:<25} {mean_mae_valid:<25}\n")

        mean_mse_train = f"{self.fold_results_df['mse_train'].mean():.4f} (+/- {self.fold_results_df['mse_train'].std():.4f})"
        mean_mse_valid = f"{self.fold_results_df['mse_validation'].mean():.4f} (+/- {self.fold_results_df['mse_validation'].std():.4f})"
        f.write(f"{'MSE':<10} {mean_mse_train:<25} {mean_mse_valid:<25}\n")

        mean_r2_train = f"{self.fold_results_df['r2_train'].mean():.4f} (+/- {self.fold_results_df['r2_train'].std():.4f})"
        mean_r2_valid = f"{self.fold_results_df['r2_validation'].mean():.4f} (+/- {self.fold_results_df['r2_validation'].std():.4f})"
        f.write(f"{'R²':<10} {mean_r2_train:<25} {mean_r2_valid:<25}\n")

    def _write_hyperparameter_summary(self, f):
        f.write("\n" + "-"*65 + "\n")
        f.write("Hyperparameter Stability (Mean +/- Std. Dev.):\n")
        
        if 'alpha' in self.fold_results_df.columns:
            alpha_mean = self.fold_results_df['alpha'].mean()
            alpha_std = self.fold_results_df['alpha'].std()
            f.write(f"{'Alpha':<10} {alpha_mean:.4f} (+/- {alpha_std:.4f})\n")

        if 'l1_ratio' in self.fold_results_df.columns:
            l1_ratio_mean = self.fold_results_df['l1_ratio'].mean()
            l1_ratio_std = self.fold_results_df['l1_ratio'].std()
            if pd.isna(l1_ratio_std): l1_ratio_std = 0.0 
            f.write(f"{'L1 Ratio':<10} {l1_ratio_mean:.4f} (+/- {l1_ratio_std:.4f})\n")

    def _write_coefficient_stability(self, f):
        f.write("\n" + "="*80 + "\n\n")
        f.write("--- Coefficient Stability Analysis ---\n")
        
        mean_coefs, std_coefs = self.coefs_df.mean(), self.coefs_df.std()
        cv_coefs = (std_coefs / mean_coefs.replace(0, 1e-9)).abs().fillna(0) * 100
        coef_stats = pd.DataFrame({
            'Mean': mean_coefs, 
            'Std. Dev.': std_coefs, 
            'CV (%)': cv_coefs
        }).reset_index().rename(columns={'index': 'Predictor'})

        f.write("Coefficient Statistics:\n")
        f.write(coef_stats.to_string(index=False, float_format='%.4f'))
        f.write("\n\n")
        f.write("Coefficients per Fold:\n")
        self.coefs_df.index = [f"Fold_{i+1}" for i in range(len(self.coefs_df))]
        f.write(self.coefs_df.T.to_string(float_format='%.4f'))
        f.write("\n\n" + "="*80 + "\n")

    def generate_and_save(self):
        with open(self.output_path, 'w', encoding='utf-8') as f:
            self._write_header(f)
            self._write_overfitting_analysis(f)
            self._write_hyperparameter_summary(f)
            self._write_coefficient_stability(f)
        print(f"CV stability and overfitting report saved to: {self.output_path}")


# ==========================================
# Original Public API (Wrappers / Facades)
# ==========================================

def generate_statistical_report(
    model_name: str, 
    residuals: np.ndarray, 
    X_data: pd.DataFrame, 
    output_path_base: str
) -> None:
    """Facade for generating the statistical report."""
    generator = StatisticalReportGenerator(model_name, residuals, X_data, output_path_base)
    generator.generate_and_save()


def generate_performance_report(
    model_name: str, 
    hyperparams: Dict[str, Any], 
    coef_df: pd.DataFrame, 
    metrics_by_dataset: Dict[str, Dict[str, Any]], 
    output_path_base: str,
    x_normalized: bool = False,
    y_normalized: bool = False,
    duration_minutes: Optional[float] = None
) -> None:
    """Facade for generating the performance report."""
    generator = PerformanceReportGenerator(
        model_name, hyperparams, coef_df, metrics_by_dataset, 
        output_path_base, x_normalized, y_normalized, duration_minutes
    )
    generator.generate_and_save()


def generate_baseline_report(
    mode: str,
    baseline_mse: float,
    n_formulas: int,
    feature_names: List[str],
    coef_col_name: str,
    original_coeffs: Union[np.ndarray, List[float]],
    retrain_coeffs: Union[np.ndarray, List[float]],
    mets_orig: List[Dict[str, Any]],
    mets_retr: List[Dict[str, Any]],
    output_path_base: str
) -> None:
    """Facade for generating the baseline report."""
    generator = BaselineReportGenerator(
        mode, baseline_mse, n_formulas, feature_names, coef_col_name,
        original_coeffs, retrain_coeffs, mets_orig, mets_retr, output_path_base
    )
    generator.generate_and_save()


def save_full_results_csv(
    results_df: pd.DataFrame, 
    output_path_base: str
) -> None:
    """Facade for saving full results to CSV."""
    CSVReportManager.save_full_results(results_df, output_path_base)


def save_model_summary_csv(
    model_name: str, 
    predictors: List[str], 
    coefficients: Union[np.ndarray, List[float]], 
    metrics_by_dataset: Dict[str, Dict[str, Any]], 
    output_path_base: str
) -> None:
    """Facade for saving the model summary to CSV."""
    CSVReportManager.save_model_summary(model_name, predictors, coefficients, metrics_by_dataset, output_path_base)


# --- CV and Stability Reporting Functions ---

def save_overfitting_analysis_csv(fold_results_df, output_path):
    """Facade for saving overfitting analysis to CSV."""
    CSVReportManager.save_overfitting_analysis(fold_results_df, output_path)


def generate_cv_stability_report(
    fold_results_df: pd.DataFrame, 
    predictors: List[str], 
    output_path: str, 
    cv_method: str
) -> None:
    """Facade for generating the CV stability text report."""
    generator = CVStabilityReportGenerator(fold_results_df, predictors, output_path, cv_method)
    generator.generate_and_save()
