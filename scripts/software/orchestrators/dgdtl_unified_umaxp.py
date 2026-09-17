# SPDX-FileCopyrightText: 2026 José A. Pérez
# SPDX-License-Identifier: MIT

"""
DGDTL-LTS Unified
Fixed-Configuration Evaluation & Deployment Orchestrator
========================================================

Abstract:
---------
Unified implements the fixed-configuration execution architecture of the
DGDTL-LTS framework. It evaluates a prescribed hyperparameter configuration
through the DGDTL-LTS optimization motor and applies the U-MaxP structural
framework to determine the deployable candidate generated across Run 1
exploration and Run 2 topological refinement.

Unlike the Hunter orchestrator, Unified does not perform hyperparameter-space
search. It operates on a single supplied configuration and employs the
theoretically authorized proxy-based inter-run guardrails required for rapid
structural evaluation without reproducing the full search-level calculations
used by Hunter.

The orchestrator supports both Deployment Guide and Interactive execution
modes while preserving an identical computational path once the production
configuration has been resolved.

Key Architectural Features:
---------------------------
1. Fixed-Configuration DGDTL-LTS Execution
   Executes the DGDTL-LTS motor for a prescribed diversity weight, tolerance
   factor, numerical constraints, coefficient bounds, and data-transformation
   configuration.

2. Dual-Mode Operation
   Supports Deployment Guide and Interactive workflows that converge to the
   same ProductionConfig representation and subsequently execute the same
   computational pipeline.

3. Proxy-Assisted Structural Evaluation
   Applies the theoretically authorized fixed-configuration proxies and
   guardrails required for inter-run structural arbitration while preserving
   consistency with the U-MaxP decision framework.

4. Inter-Run Structural Arbitration
   Evaluates the Run 1 and Run 2 candidate states through structural
   coherence, empirical-tail information, proxy stability diagnostics,
   conditioned tie resolution, and the applicable validation-bias safeguards.

5. U-MaxP Integration
   Delegates shared mathematical primitives and structural operators to the
   U-MaxP core motor while retaining the proxy quantities specific to the
   Unified fixed-configuration operating regime.

6. Deployment-Oriented Execution
   Produces the selected deployable candidate together with structural
   diagnostics, performance reports, coefficient summaries, residual
   analyses, and publication-quality visualization outputs.

7. Reproducible Execution
   Enforces fixed numerical threading, deterministic DGDTL-LTS execution,
   controlled data transformations, and invariant configuration handling to
   preserve reproducibility within and across supported computational
   environments.

Sections:
---------
1. Production Configuration & Deployment Guide Parser
2. Data Utilities & Feature Engineering
3. Interactive Bounds Heuristics
4. Reporting & Visualization Integration
5. DGDTL-LTS Fixed-Configuration Execution
6. Run 1 / Run 2 Structural Evaluation
7. Proxy-Assisted U-MaxP Arbitration
8. Final Deployment Selection
9. Dual-Mode Application Interface

Usage:
------
Unified is the fixed-configuration evaluation and deployment orchestrator of
the DGDTL-LTS implementation. Given training, internal-validation, and testing
data together with a resolved ProductionConfig, it executes DGDTL-LTS,
evaluates the resulting Run 1 and Run 2 candidate states through the U-MaxP
structural framework and its authorized proxies, and returns the final
deployable solution with its associated structural and predictive diagnostics.

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
import re

# --- CRITICAL REPRODUCIBILITY SETTINGS (TOP LEVEL) ---
os.environ['PYTHONHASHSEED'] = '0'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['VECLIB_MAXIMUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

import multiprocessing
import sys
import warnings
import traceback
import time
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Union, Any

import pandas as pd
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from dgdtl_lts import DGDTLEstimator
from u_maxp import UMaxPCriterion, StructuralMetricsEngine, ProtocolConfig

# --- CONFIGURATION ---
try:
    FIXED_N_JOBS = max(1, multiprocessing.cpu_count() - 1)
except NotImplementedError:
    FIXED_N_JOBS = 8

warnings.filterwarnings("ignore")

# --- PRODUCTION DEPLOYMENT CONFIGURATION ---
@dataclass
class ProductionConfig:
    """
    Production deployment parameters and hyperparameters parsed from the deployment guide.
    """
    mode: str = 'raw'
    fit_intercept: bool = True
    beta_sum_one: bool = False
    normalize_x: bool = True
    normalize_y: bool = False   # True => NORMALIZED (standardized)
    centre_y:    bool = False   # True => CENTRED    (mean-centred, natural scale)
    feature_formulas: List[str] = field(default_factory=list)
    
    diversity_weight: float = 0.0
    tolerance_factor: float = 0.0
    constraint_threshold: float = 0.0
    validation_threshold: float = 0.0
    coeff_bounds: Tuple[float, float] = (0.0, 0.0)
    intercept_bounds: Tuple[float, float] = (0.0, 0.0)
    
    expected_y_std: float = 0.0
    train_path: str = "data_train.csv"
    valid_path: str = "data_valid.csv"
    test_path: str = "data_test.csv"
    output_dir: str = "results"


# --- PARSER ENGINE ---
def parse_deployment_guide(filepath: str) -> ProductionConfig:
    """Reads the .txt deployment guide and extracts hyperparameters using regex."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    def extract_float(pattern):
        match = re.search(pattern, content)
        return float(match.group(1)) if match else 0.0

    def extract_str(pattern):
        match = re.search(pattern, content)
        return match.group(1).strip() if match else ""

    def extract_bool(pattern):
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).strip().upper() == 'YES'
        return False

    def extract_bounds(pattern):
        match = re.search(pattern, content)
        if match:
            return (float(match.group(1)), float(match.group(2)))
        return (0.0, 0.0)

    def extract_features(pattern):
        match = re.search(pattern, content)
        if match:
            feats_str = match.group(1)
            # Handle multiple features separated by comma and strip quotes
            return [f.strip(" '\"") for f in feats_str.split(',')]
        return []

    config = ProductionConfig()
    
    config.diversity_weight = extract_float(r"Diversity Weight:\s*([0-9.-]+)")
    config.tolerance_factor = extract_float(r"Tolerance Factor:\s*([0-9.-]+)")
    config.constraint_threshold = extract_float(r"Constraint Threshold:\s*([0-9.-]+)")
    config.validation_threshold = extract_float(r"Validation Threshold:\s*([0-9.-]+)")
    
    config.coeff_bounds = extract_bounds(r"Coeff Bounds:\s*([0-9.-]+)\s*to\s*([0-9.-]+)")
    config.intercept_bounds = extract_bounds(r"Intercept Bounds:\s*([0-9.-]+)\s*to\s*([0-9.-]+)")
    
    config.mode = extract_str(r"Mode:\s*(raw|error_matrix)") or 'raw'
    config.fit_intercept = extract_bool(r"Fit Intercept:\s*(YES|NO)")
    config.beta_sum_one = extract_bool(r"Beta Sum=1:\s*(YES|NO)")
    config.normalize_x = extract_bool(r"Normalize X:\s*(YES|NO)")
    _target_y = extract_str(r"Target Y:\s*(NORMALIZED|CENTRED|NO)")
    if _target_y is None:
        # Backward compatibility: old guides used "Normalize Y: YES/NO"
        _ny = extract_bool(r"Normalize Y:\s*(YES|NO)")
        config.normalize_y = bool(_ny)
        config.centre_y    = False
    else:
        config.normalize_y = (_target_y == 'NORMALIZED')
        config.centre_y    = (_target_y == 'CENTRED')
    
    config.feature_formulas = extract_features(r"Features:\s*\[(.*?)\]")
    config.expected_y_std = extract_float(r"Verify Y_std\s*=\s*([0-9.]+)")

    return config

# --- ANSI COLORS FOR TERMINAL UI ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Attempt to import optional visualization modules
try:
    import plotting_style as ps
    import reporting as rp
    VISUALS_AVAILABLE = True
except ImportError:
    ps = None; rp = None
    VISUALS_AVAILABLE = False

# =============================================================================
# UTILITY CLASSES
# =============================================================================

class DataUtils:
    @staticmethod
    def scale_predictors(data: pd.DataFrame, stats: Dict) -> pd.DataFrame:
        means = stats['means'].to_numpy()
        stds = stats['stds'].to_numpy()
        stds = np.where(stds == 0, 1.0, stds)
        return (data - means) / stds

    @staticmethod
    def unscale_predictions(scaled_preds: np.ndarray, stats: Dict) -> np.ndarray:
        return (scaled_preds * stats['std']) + stats['mean']

    @staticmethod
    def scale_target(target: np.ndarray, stats: Dict) -> np.ndarray:
        return (target - stats['mean']) / stats['std']

    @staticmethod
    def create_feature_names_from_formulas(base_names: List[str], formulas: List[str]) -> List[str]:
        new_names = [f.replace(' ', '').replace('**', '_pow_').replace('*', '_x_') for f in formulas]
        return base_names + new_names

    @staticmethod
    def apply_feature_engineering(X_raw: np.ndarray, formulas: List[str], base_feature_names: List[str], x_stats: Optional[Dict] = None) -> np.ndarray:
        df_source = pd.DataFrame(X_raw, columns=base_feature_names)
        if x_stats:
            scaled_data = DataUtils.scale_predictors(df_source, x_stats)
            eval_df = pd.DataFrame(scaled_data, columns=base_feature_names)
        else:
            eval_df = df_source

        new_features_list = []
        for formula in formulas:
            try:
                new_feature = eval_df.eval(formula, engine='python')
                new_features_list.append(new_feature.values.reshape(-1, 1))
            except Exception as e:
                raise ValueError(f"Error evaluating formula '{formula}': {e}")

        if new_features_list:
            final_X = np.hstack([eval_df.values] + new_features_list)
        else:
            final_X = eval_df.values

        if not np.isfinite(final_X).all():
            raise ValueError(f"{Colors.RED}Feature Engineering produced Infinite or NaN values. Check your formulas/data.{Colors.ENDC}")

        return final_X

# =============================================================================
# HEURISTICS (Interactive flow — Automatic bounds mode)
# =============================================================================
# Proposes parameter bounds from the calibrated baseline.
# Used only in the Interactive flow; the Deployment Guide uses
# pre-computed bounds instead.

class Heuristics:
    @staticmethod
    def calculate_adaptive_bounds(coeffs: Union[np.ndarray, float], beta_sum_one: bool) -> Tuple[Tuple[float, float], str]:
        coeffs_arr = np.atleast_1d(coeffs)
        max_val = np.max(coeffs_arr)
        min_val = np.min(coeffs_arr)
        abs_max = np.max(np.abs(coeffs_arr))

        if beta_sum_one:
            if min_val >= -1e-5:
                expansion_factor = 0.50
                raw_upper = max_val * (1.0 + expansion_factor)
                raw_lower = min_val * (1.0 - expansion_factor)
                final_upper = min(raw_upper, 0.999)
                final_lower = max(raw_lower, 0.001)
                if final_upper <= final_lower:
                    final_lower, final_upper = 0.001, 0.999
                return (round(final_lower, 6), round(final_upper, 6)), f"Strict Mixture (Clamped: {final_lower:.6f} - {final_upper:.6f})"
            else:
                upper_bound = np.ceil(max_val + max(abs(max_val) * 0.5, 0.5) * 100) / 100
                lower_bound = np.floor(min_val - max(abs(min_val) * 0.5, 0.5) * 100) / 100
                return (lower_bound, upper_bound), f"Mixed Signs (Expanded: {lower_bound} - {upper_bound})"
        else:
            borderline_threshold = 0.1
            noise_buffer = 0.1
            if coeffs_arr.size == 1:
                base_margin = 1.5 if abs_max < 10 else (5.0 if abs_max < 100 else 10.0)
                val = coeffs_arr[0]
                lower_bound = np.floor((val - base_margin) * 10) / 10
                upper_bound = np.ceil((val + base_margin) * 10) / 10
                return (lower_bound, upper_bound), f"Intercept Centered (+/- {base_margin})"

            if abs_max < 10: base_margin = 1.5
            elif abs_max < 100: base_margin = 5.0
            elif abs_max < 1000: base_margin = 10.0
            else: base_margin = 100.0

            if min_val >= 0:
                upper_bound = max_val * 1.5 if max_val < 1.0 else max_val + base_margin
                lower_bound = min_val * 0.5 if min_val > borderline_threshold else -noise_buffer
                desc = "Positive Coeffs (Hybrid Bounds)"
            elif max_val <= 0:
                lower_bound = min_val * 1.5 if abs(min_val) < 1.0 else min_val - base_margin
                upper_bound = max_val * 0.5 if abs(max_val) > borderline_threshold else noise_buffer
                desc = "Negative Coeffs (Hybrid Bounds)"
            else:
                eff_margin = base_margin if abs_max >= 1.0 else (abs_max * 0.5)
                upper_bound = np.ceil((max_val + eff_margin) * 100) / 100
                lower_bound = np.floor((min_val - eff_margin) * 100) / 100
                desc = f"Mixed Signs (Symmetric)"

            return (round(lower_bound, 6), round(upper_bound, 6)), desc

# =============================================================================
# REPORTING ENGINE
# =============================================================================

def save_comparative_absolute_errors(output_dir, filename, champion_dict, all_solutions_list,
                                     df_train, df_vldt, df_test, model, x_stats, y_stats,
                                     feature_formulas=None):
    print(f"\n{Colors.CYAN}--- Generating Comparative Absolute Error Report: {filename} ---{Colors.ENDC}")
    criterion = champion_dict.get('selection_criterion', 'MSE')
    sort_key = 'MAE_vldt' if 'MAE' in criterion else 'MSE_vldt'

    champ_idx = champion_dict['Original_Index']
    others = [s for s in all_solutions_list if s['Original_Index'] != champ_idx]
    others_sorted = sorted(others, key=lambda x: x.get(sort_key, 0))

    champ_full_data = next((s for s in all_solutions_list if s['Original_Index'] == champ_idx), None)
    sorted_solutions = ([champ_full_data] + others_sorted) if champ_full_data else others_sorted

    df_train['Dataset'] = 'Training'
    df_vldt['Dataset'] = 'Validation'
    df_test['Dataset'] = 'Testing'

    master_df = pd.concat([df_train, df_vldt, df_test], ignore_index=True)
    output_df_base = master_df.iloc[:, [0, -1]].copy()

    X_raw_features = master_df.iloc[:, 1:-2].values
    y_full_raw = master_df.iloc[:, -2].values
    base_names = list(master_df.columns[1:-2])
    is_normalized = x_stats is not None

    if feature_formulas:
        X_features_only = DataUtils.apply_feature_engineering(X_raw_features, feature_formulas, base_names, x_stats)
    else:
        X_features_only = DataUtils.scale_predictors(pd.DataFrame(X_raw_features, columns=base_names), x_stats) if is_normalized else X_raw_features

    if model.fit_intercept:
        ones_col = np.ones((X_features_only.shape[0], 1))
        X_full_eval = np.hstack([ones_col, X_features_only])
    else:
        X_full_eval = X_features_only

    y_is_normalized = y_stats is not None
    new_cols_data = {}
    for sol in sorted_solutions:
        idx = sol['Original_Index']
        beta = np.asarray(sol['coeffs'])

        if model.mode == 'raw':
            y_pred_model = X_full_eval @ beta
            y_pred_unscaled = DataUtils.unscale_predictions(y_pred_model, y_stats) if is_normalized and y_is_normalized else y_pred_model
            abs_error = np.abs(y_pred_unscaled - y_full_raw)
        else:
            abs_error = np.abs(X_full_eval @ beta)

        col_name = f"Sol_{idx}_AbsErr"
        new_cols_data[col_name] = abs_error

    output_df = pd.concat([output_df_base, pd.DataFrame(new_cols_data)], axis=1) if new_cols_data else output_df_base
    output_df.to_csv(os.path.join(output_dir, filename), index=False, float_format="%.6f")
    print(f" > Report saved.")


def generate_comprehensive_reports(model, output_dir, dfs, mode, x_stats, y_stats, feature_formulas=None, training_duration_minutes: Optional[float] = None, _perf_saved_lines=None):

    df_train, df_vldt, df_test = dfs['train'], dfs['valid'], dfs['test']
    base_names = list(df_train.columns[1:-1])
    feature_names = DataUtils.create_feature_names_from_formulas(base_names, feature_formulas) if feature_formulas else base_names
    if model.fit_intercept: feature_names = ["Intercept"] + feature_names

    is_normalized = x_stats is not None
    y_is_normalized = y_stats is not None
    coef_col_name = 'Coefficient_Normalized' if is_normalized else 'Coefficient'


    df_train_valid = pd.concat([df_train, df_vldt])
    X_comb_raw = df_train_valid.iloc[:, 1:-1].values
    y_comb_raw = df_train_valid.iloc[:, -1].values

    if feature_formulas:
        X_comb_fit = DataUtils.apply_feature_engineering(X_comb_raw, feature_formulas, base_names, x_stats)
    else:
        X_comb_fit = DataUtils.scale_predictors(pd.DataFrame(X_comb_raw, columns=base_names), x_stats) if is_normalized else X_comb_raw

    y_comb_fit = y_comb_raw
    if is_normalized and y_is_normalized:
        y_comb_fit = (y_comb_raw - y_stats['mean']) / y_stats['std']

    temp_model_retr = DGDTLEstimator(mode=mode, fit_intercept=model.fit_intercept, beta_sum_one=model.beta_sum_one, n_jobs=FIXED_N_JOBS)
    retrain_coeffs = temp_model_retr.calibrate(X_comb_fit, y_comb_fit)

    base_res_rows = []
    mets_orig = []
    all_sets = [("Training", df_train), ("Validation", df_vldt), ("Testing", df_test)]

    for name, df in all_sets:
        X_raw, y_real = df.iloc[:, 1:-1].values, df.iloc[:, -1].values
        X_ev = DataUtils.apply_feature_engineering(X_raw, feature_formulas, base_names, x_stats) if feature_formulas else (DataUtils.scale_predictors(pd.DataFrame(X_raw, columns=base_names), x_stats) if is_normalized else X_raw)
        y_ref = y_real if mode == 'error_matrix' else None

        y_p_orig_m = model.predict(X_ev, y_reference=y_ref, beta=model.baseline_coeffs_)
        y_p_orig = DataUtils.unscale_predictions(y_p_orig_m, y_stats) if is_normalized and y_is_normalized else y_p_orig_m
        err_orig = y_p_orig - y_real

        y_p_retr_m = model.predict(X_ev, y_reference=y_ref, beta=retrain_coeffs)
        y_p_retr = DataUtils.unscale_predictions(y_p_retr_m, y_stats) if is_normalized and y_is_normalized else y_p_retr_m
        err_retr = y_p_retr - y_real

        base_res_rows.append(pd.DataFrame({
            "System": df.iloc[:, 0], "Dataset": name, "Real_Values": y_real,
            "Predicted_Values": y_p_orig, "Error": err_orig, "Abs_error": np.abs(err_orig),
            "Pred_retrain": y_p_retr, "Error_retrain": err_retr, "Abs_error_retrain": np.abs(err_retr)
        }))
        mets_orig.append({"Dataset": name, "R²": r2_score(y_real, y_p_orig), "MAE": mean_absolute_error(y_real, y_p_orig), "MSE": mean_squared_error(y_real, y_p_orig), "MaxErr": np.max(np.abs(err_orig))})

    df_valid_test = pd.concat([df_vldt, df_test])
    X_raw_vt, y_real_vt = df_valid_test.iloc[:, 1:-1].values, df_valid_test.iloc[:, -1].values
    X_ev_vt = DataUtils.apply_feature_engineering(X_raw_vt, feature_formulas, base_names, x_stats) if feature_formulas else (DataUtils.scale_predictors(pd.DataFrame(X_raw_vt, columns=base_names), x_stats) if is_normalized else X_raw_vt)
    y_ref_vt = y_real_vt if mode == 'error_matrix' else None
    y_p_orig_m_vt = model.predict(X_ev_vt, y_reference=y_ref_vt, beta=model.baseline_coeffs_)
    y_p_orig_vt = DataUtils.unscale_predictions(y_p_orig_m_vt, y_stats) if is_normalized and y_is_normalized else y_p_orig_m_vt
    mets_orig.append({
        "Dataset": "Valid+Testing",
        "R²": r2_score(y_real_vt, y_p_orig_vt),
        "MAE": mean_absolute_error(y_real_vt, y_p_orig_vt),
        "MSE": mean_squared_error(y_real_vt, y_p_orig_vt)
    })

    df_all_retr = pd.concat(base_res_rows)
    tv_mask = df_all_retr['Dataset'].isin(['Training', 'Validation'])
    test_mask = df_all_retr['Dataset'] == 'Testing'

    mets_retr = []
    for mask, label in [(tv_mask, "Training_valid"), (test_mask, "Testing")]:
        sub = df_all_retr[mask]
        mets_retr.append({"Dataset": label, "R²": r2_score(sub['Real_Values'], sub['Pred_retrain']),
                          "MAE": mean_absolute_error(sub['Real_Values'], sub['Pred_retrain']),
                          "MSE": mean_squared_error(sub['Real_Values'], sub['Pred_retrain']),
                          "MaxErr": sub['Abs_error_retrain'].max()})

    pd.concat(base_res_rows).to_csv(os.path.join(output_dir, "baseline_predictions.csv"), index=False, float_format="%.6f")

    df_mets_orig_csv = pd.DataFrame(mets_orig)[['Dataset', 'R²', 'MAE', 'MSE']]
    df_mets_orig_csv['Dataset'] = df_mets_orig_csv['Dataset'].replace('Valid+Testing', 'Valid_Testing')

    with open(os.path.join(output_dir, "baseline_metrics.csv"), 'w') as f:
        f.write("Dataset,R²,MAE,MSE\n")
        df_mets_orig_csv.to_csv(f, index=False, header=False, float_format="%.6f")
        f.write("Retraining,,,\nDataset,R²,MAE,MSE\n")
        pd.DataFrame(mets_retr)[['Dataset', 'R²', 'MAE', 'MSE']].to_csv(f, index=False, header=False, float_format="%.6f")

    pd.DataFrame({
        'Predictor': feature_names,
        coef_col_name: model.baseline_coeffs_,
        f"{coef_col_name}_Retrain": retrain_coeffs
    }).to_csv(os.path.join(output_dir, "baseline_coefficients.csv"), index=False)

    if VISUALS_AVAILABLE and rp:
        rp.generate_baseline_report(
            mode=mode,
            baseline_mse=model.baseline_mse_,
            n_formulas=len(feature_formulas) if feature_formulas else 0,
            feature_names=feature_names,
            coef_col_name=coef_col_name,
            original_coeffs=model.baseline_coeffs_,
            retrain_coeffs=retrain_coeffs,
            mets_orig=mets_orig,
            mets_retr=mets_retr,
            output_path_base=os.path.join(output_dir, "baseline_report")
        )
    else:
        print(f"{Colors.YELLOW}[WARN] 'reporting' module not available: baseline_report.txt was not generated.{Colors.ENDC}")

    try:
        baseline_mse_vldt = next(m['MSE'] for m in mets_orig if m['Dataset'] == 'Validation')
        if mode == 'raw' and y_is_normalized: baseline_mse_vldt /= (y_stats['std'] ** 2)
    except: baseline_mse_vldt = 0

    stages = [("Run1", getattr(model, 'run1_raw_', None), getattr(model, 'run1_unique_', None), getattr(model, 'run1_valid_', None), getattr(model, 'champion_run1_', None)),
              ("Run2", getattr(model, 'run2_raw_', None), getattr(model, 'run2_unique_', None), getattr(model, 'run2_valid_', None), getattr(model, 'champion_run2_', None))]

    for r_name, raw, unique, valid, champ in stages:
        if not unique: continue

        suf = r_name.lower()

        df_raw = pd.DataFrame(raw, columns=feature_names)
        X_train_raw_features = df_train.iloc[:, 1:-1].values
        y_train_raw = df_train.iloc[:, -1].values

        X_feat_only = DataUtils.apply_feature_engineering(X_train_raw_features, feature_formulas, base_names, x_stats) if feature_formulas else (DataUtils.scale_predictors(pd.DataFrame(X_train_raw_features, columns=base_names), x_stats) if is_normalized else X_train_raw_features)
        X_train_eval = np.hstack([np.ones((X_feat_only.shape[0], 1)), X_feat_only]) if model.fit_intercept else X_feat_only

        mse_train_list = []
        for _, row in df_raw.iterrows():
            beta = np.asarray(row.values)
            y_p_m = X_train_eval @ beta
            if mode == 'raw':
                if is_normalized and y_is_normalized and y_stats:
                    y_train_for_mse_calc = DataUtils.scale_target(y_train_raw, y_stats)
                    mse_train_list.append(np.mean((y_p_m - y_train_for_mse_calc)**2))
                else:
                    mse_train_list.append(np.mean((y_p_m - y_train_raw)**2))
            else:
                mse_train_list.append(np.mean(y_p_m**2))

        df_raw['MSE_train'] = mse_train_list
        df_raw.to_csv(os.path.join(output_dir, f"all_solutions_{suf}.csv"), index_label="Solution_ID", float_format="%.6f")

        unique_df_data = [[v['Original_Index']] + list(v['coeffs']) + [v.get('MSE_train', 0.0)] for v in unique]
        pd.DataFrame(unique_df_data, columns=['Original_Index'] + feature_names + ['MSE_train']).to_csv(os.path.join(output_dir, f"unique_solutions_{suf}.csv"), index=False, float_format="%.8f")

        rep_df = model.run1_report_df_ if r_name == "Run1" else model.run2_report_df_
        if rep_df is not None and not rep_df.empty:
            if 'coeffs' in rep_df.columns:
                c_df = pd.DataFrame(rep_df['coeffs'].tolist(), columns=feature_names, index=rep_df.index)
                rep_df = pd.concat([rep_df.drop(columns=['coeffs']), c_df], axis=1)
            rep_df.to_csv(os.path.join(output_dir, f"valid_solutions_report_{suf}.csv"), index=False, float_format="%.6f")

        if VISUALS_AVAILABLE and ps and champ:
            sol_plot = rep_df.to_dict('records') if (rep_df is not None and not rep_df.empty) else valid
            r_params = (model.run1_params_ if r_name == "Run1" else model.run2_params_) or model.get_params()
            ps.plot_solution_space(sol_plot, model.baseline_mse_, baseline_mse_vldt, champ, r_params, output_dir, f"DGDTL_Solution_Space_Plot_{r_name}.png")
        if champ:
            fallback_pool = model.run1_valid_ if r_name == "Run2" and not valid else valid
            save_comparative_absolute_errors(output_dir, f"DGDTL_Champion_Conceptual_{r_name}_Full_Results_ABSERR.csv",
                                             champ, fallback_pool, df_train.copy(), df_vldt.copy(), df_test.copy(),
                                             model, x_stats, y_stats, feature_formulas=feature_formulas)

    if VISUALS_AVAILABLE and ps and getattr(model, 'run1_valid_', None):

        ps.plot_goldilocks_donut(model.run1_valid_, model.run2_valid_, model.baseline_mse_, model.run1_params_, model.run2_params_, output_dir, model.champion_run1_, model.champion_run2_)

    champ_metrics = {'Run1': None, 'Run2': None}

    for r_name, champ in [("Run1", getattr(model, 'champion_run1_', None)), ("Run2", getattr(model, 'champion_run2_', None))]:
        if not champ: continue
        tag = f"DGDTL_Champion_Conceptual_{r_name}"
        all_res, mets_list = [], []
        X_train_for_stats = None

        datasets_report = {
            "Training": df_train,
            "Validation": df_vldt,
            "Testing": df_test,
            "Train+Valid": pd.concat([df_train, df_vldt]),
            "Valid+Testing": pd.concat([df_vldt, df_test])
        }
        for n, df in datasets_report.items():
            X, y = df.iloc[:, 1:-1].values, df.iloc[:, -1].values
            X_e = DataUtils.apply_feature_engineering(X, feature_formulas, base_names, x_stats) if feature_formulas else (DataUtils.scale_predictors(pd.DataFrame(X, columns=base_names), x_stats) if is_normalized else X)

            if n == "Training":
                X_train_for_stats = X_e.values if hasattr(X_e, 'values') else X_e

            y_p_m = model.predict(X_e, y_reference=y if mode == 'error_matrix' else None, beta=champ['coeffs'])
            y_p = DataUtils.unscale_predictions(y_p_m, y_stats) if is_normalized and y_is_normalized else y_p_m

            err = y_p - y
            abs_err = np.abs(err)

            if n not in ["Train+Valid", "Valid+Testing"]:
                all_res.append(pd.DataFrame({
                    "System": df.iloc[:, 0],
                    "Dataset": n,
                    "Real_Values": y,
                    "Predicted_Values": y_p,
                    "Error": err,
                    "Abs_error": abs_err
                }))
            mets_list.append({"Dataset": n, "R²": r2_score(y, y_p), "MAE": mean_absolute_error(y, y_p), "MSE": mean_squared_error(y, y_p)})

        tr_metrics = next((m for m in mets_list if m['Dataset'] == 'Training'), None)
        if tr_metrics:
            champ_metrics[r_name] = {'mae_tr': tr_metrics['MAE'], 'mse_tr': tr_metrics['MSE']}

        master_df = pd.concat(all_res)
        master_df.to_csv(os.path.join(output_dir, f"{tag}.csv"), index=False, float_format="%.6f")

        if VISUALS_AVAILABLE and ps:
            m_by_ds = {m['Dataset']: m for m in mets_list}
            params_for_report = model.get_params()
            if y_is_normalized and y_stats:
                y_std = y_stats.get('std', 1.0)
                params_for_report = params_for_report.copy()
                if 'constraint_threshold' in params_for_report and params_for_report['constraint_threshold'] is not None:
                    params_for_report['constraint_threshold'] *= y_std
                if 'VALIDATION_THRESHOLD' in params_for_report and params_for_report['VALIDATION_THRESHOLD'] is not None:
                    params_for_report['VALIDATION_THRESHOLD'] *= y_std

            pass  # performance report written and displayed in Phase 3
            
            pel_val = champ.get('PEL_Metric')
            p_val = champ.get('shapiro_p_train')
            
            if pel_val is not None and p_val is not None:
                alpha = getattr(model, 'shapiro_threshold', 0.05)
                k_damp = getattr(model, 'damping_factor', 200.0)
                
                scale_y = y_stats['std'] if (is_normalized and y_is_normalized and mode == 'raw') else 1.0
                
                mae_val = champ.get('MAE_vldt', 0.0) * scale_y
                rmse_val = np.sqrt(champ.get('MSE_vldt', 0.0) * (scale_y**2))
                pel_val_esc = pel_val * scale_y
                
                if p_val >= alpha:
                    try: w = 1.0 / (1.0 + np.exp(-k_damp * (p_val - alpha)))
                    except OverflowError: w = 1.0
                else:
                    w = p_val
                
                if w > 0.8:
                    pel_approx = "PEL ≈ RMSE (Strong L2 Dominance)"
                    diag_text  = "Gaussian Regime. Absolute priority assigned to global precision."
                elif w < 0.2:
                    pel_approx = "PEL ≈ MAE  (Strong L1 Dominance)"
                    diag_text  = "Heavy-Tails Regime. Robust outlier protection activated."
                else:
                    pel_approx = "Transitional PEL (Between MAE and RMSE)"
                    diag_text  = "Hybrid Regime. Balanced mixture of L1 robustness and L2 precision."
                
                perf_file = os.path.join(output_dir, f"{tag}_Performance_Metrics.txt")
                if os.path.exists(perf_file):
                    with open(perf_file, 'a', encoding='utf-8') as f:
                        f.write("\n" + "="*70 + "\n")
                        f.write("  PEL DIAGNOSTIC (Pareto-Efficiency-Like)\n")
                        f.write("="*70 + "\n")
                        f.write(f"  Shapiro-Wilk p-value (Train) : {p_val:.6f}  (Alpha Threshold: {alpha})\n")
                        f.write(f"  Weighting Factor (w)         : {w:.4f}\n\n")
                        f.write("  Metrics Ordered by Magnitude (Unified Scale):\n")
                        f.write(f"    1. MAE (L1)  : {mae_val:.6f}  <- Lower Bound (Robust Floor)\n")
                        f.write(f"    2. PEL       : {pel_val_esc:.6f}  <- {pel_approx}\n")
                        f.write(f"    3. RMSE (L2) : {rmse_val:.6f}  <- Upper Bound (Gaussian Ceiling)\n\n")
                        f.write(f"  Diagnostic   : {diag_text}\n")
                        f.write("="*70 + "\n")

            rp.generate_statistical_report(
                tag, master_df[master_df['Dataset'] == 'Training']['Error'].values, X_train_for_stats, os.path.join(output_dir, f"{tag}_Statistical_Analysis")
            )

            tr_df = master_df[master_df['Dataset']=='Training']
            X_des = np.hstack((np.ones((X_train_for_stats.shape[0], 1)), X_train_for_stats)) if model.fit_intercept else X_train_for_stats
            try: lev = np.diag(X_des @ np.linalg.pinv(X_des.T @ X_des) @ X_des.T)
            except: lev = np.zeros(X_des.shape[0])
            ps.plot_diagnostics(tr_df['Predicted_Values'], tr_df['Error'], lev, len(champ['coeffs']), f"Diagnostics {r_name}", os.path.join(output_dir, f"{tag}_Diagnostic_Plots"))
            ps.plot_parity(master_df['Real_Values'], master_df['Predicted_Values'], master_df['Dataset'], f"Parity {r_name}", 'Experimental', 'Predicted', os.path.join(output_dir, f"{tag}_Parity_Plot"))
        else:
            mets_list_for_csv = [m for m in mets_list if m.get("Dataset") != "Valid+Testing"]
            pd.DataFrame(mets_list_for_csv).to_csv(os.path.join(output_dir, f"{tag}_metrics.csv"), index=False)

    base_metrics = {
        'mae_tr': next((m['MAE'] for m in mets_orig if m['Dataset'] == 'Training'), 1.0),
        'mse_tr': next((m['MSE'] for m in mets_orig if m['Dataset'] == 'Training'), 1.0),
        'mae_val': next((m['MAE'] for m in mets_orig if m['Dataset'] == 'Validation'), 1.0),
        'mse_val': next((m['MSE'] for m in mets_orig if m['Dataset'] == 'Validation'), 1.0)
    }

    _save_champion_of_champions_report(
        model, output_dir, mode, y_stats, base_metrics, champ_metrics
    )

    print(f"[SAVED] Predictions   : baseline, Run1 & Run2 solution sets")
    print(f"[SAVED] Figures       : solution space (×2), Goldilocks donut, diagnostic plots, parity plot")
    print(f"[SAVED] Statistics    : performance metrics (×2), statistical analysis")
    print(f"[SAVED] Reports       : champion selection report")


def _composite_e_val(champ: dict) -> float:
    mae = champ.get('MAE_vldt', float('inf'))
    mse = champ.get('MSE_vldt', float('inf'))
    if mae == float('inf') or mse == float('inf'):
        return float('inf')
    return UMaxPCriterion.composite_error(mae, mse)


def _save_champion_of_champions_report(
    model,
    output_dir: str,
    mode: str,
    y_stats: Optional[Dict],
    base_metrics: dict,
    champ_metrics: dict
) -> str:
    filepath = os.path.join(output_dir, "DGDTL_Champion_Selection_Report.txt")


    c1 = getattr(model, 'champion_run1_', None)
    c2 = getattr(model, 'champion_run2_', None)

    is_y_normalized = (y_stats is not None) and (mode == 'raw')
    scale  = float(y_stats['std']) if is_y_normalized else 1.0
    sq_scl = scale ** 2

    scale_note = (
        f"Y normalized (std={scale:.6f}) — display errors in original scale."
        if is_y_normalized
        else "Y not normalized — errors in model units."
    )

    def _metrics(champ: Optional[dict]) -> dict:
        if champ is None:
            return dict(present=False)
        mae_n = champ.get('MAE_vldt', float('inf'))
        mse_n = champ.get('MSE_vldt', float('inf'))
        mae_o = mae_n * scale
        mse_o = mse_n * sq_scl
        ev_n  = _composite_e_val(champ)
        ev_o  = float(np.sqrt(mae_o * np.sqrt(mse_o)))
        return dict(
            present    = True,
            idx        = champ.get('Original_Index', '?'),
            criterion  = champ.get('selection_criterion', 'N/A'),
            mae_orig   = mae_o,
            mse_orig   = mse_o,
            e_val_norm = ev_n,
            e_val_orig = ev_o,
        )

    m1 = _metrics(c1)
    m2 = _metrics(c2)

    def _calc_phi(mae_val, mse_val, mae_tr, mse_tr):
        eps = 1e-12
        e_val      = np.sqrt(mae_val * np.sqrt(mse_val))
        e_tr       = np.sqrt(mae_tr  * np.sqrt(mse_tr))
        e_val_base = np.sqrt(base_metrics['mae_val'] * np.sqrt(base_metrics['mse_val']))
        e_tr_base  = np.sqrt(base_metrics['mae_tr']  * np.sqrt(base_metrics['mse_tr']))
        return UMaxPCriterion.cauchy_phi(
            e_val, e_tr, e_val_base, e_tr_base
        )

    phi1, phi2 = 0.0, 0.0
    if m1['present'] and champ_metrics.get('Run1'):
        phi1 = _calc_phi(m1['mae_orig'], m1['mse_orig'],
                         champ_metrics['Run1']['mae_tr'],
                         champ_metrics['Run1']['mse_tr'])
    if m2['present'] and champ_metrics.get('Run2'):
        phi2 = _calc_phi(m2['mae_orig'], m2['mse_orig'],
                         champ_metrics['Run2']['mae_tr'],
                         champ_metrics['Run2']['mse_tr'])

    _EPS_PSI = ProtocolConfig.EPS_PSI
    _ratio_mae_bl  = base_metrics['mae_val'] / (base_metrics['mae_tr']  + 1e-12)
    _ratio_mse_bl  = base_metrics['mse_val'] / (base_metrics['mse_tr']  + 1e-12)
    _ratio_rmse_bl = (np.sqrt(base_metrics['mse_val']) /
                      (np.sqrt(base_metrics['mse_tr']) + 1e-12))

    def _calc_psi(mae_val, mse_val, mae_tr, mse_tr):
        eps = 1e-12
        rho_mae = (mae_val / (mae_tr + eps)) / (_ratio_mae_bl + eps)
        rho_mse = (mse_val / (mse_tr + eps)) / (_ratio_mse_bl + eps)
        if rho_mae <= 0 or rho_mse <= 0:
            return 0.0, 0.0, 0.0, 'UNKNOWN'
        log_mae = np.log10(rho_mae)
        log_mse = np.log10(rho_mse)
        psi     = log_mae * log_mse
        if log_mae < 0 and log_mse < 0:
            regime = 'SOV'
        elif log_mae > 0 and log_mse > 0:
            regime = 'OFT'
        else:
            regime = 'INC'
        return psi, log_mae, log_mse, regime

    def _calc_psi_sqrt(mae_val, mse_val, mae_tr, mse_tr):
        eps = 1e-12
        ratio_mae  = mae_val          / (mae_tr          + eps)
        ratio_rmse = np.sqrt(mse_val) / (np.sqrt(mse_tr) + eps)
        return float(np.sqrt(ratio_mae * ratio_rmse))

    psi1, lmae1, lmse1, regime1 = (0.0, 0.0, 0.0, 'UNKNOWN')
    psi2, lmae2, lmse2, regime2 = (0.0, 0.0, 0.0, 'UNKNOWN')
    psisqrt1, psisqrt2 = 0.0, 0.0

    if m1['present'] and champ_metrics.get('Run1'):
        psi1, lmae1, lmse1, regime1 = _calc_psi(
            m1['mae_orig'], m1['mse_orig'],
            champ_metrics['Run1']['mae_tr'],
            champ_metrics['Run1']['mse_tr'])
        psisqrt1 = _calc_psi_sqrt(
            m1['mae_orig'], m1['mse_orig'],
            champ_metrics['Run1']['mae_tr'],
            champ_metrics['Run1']['mse_tr'])
    if m2['present'] and champ_metrics.get('Run2'):
        psi2, lmae2, lmse2, regime2 = _calc_psi(
            m2['mae_orig'], m2['mse_orig'],
            champ_metrics['Run2']['mae_tr'],
            champ_metrics['Run2']['mse_tr'])
        psisqrt2 = _calc_psi_sqrt(
            m2['mae_orig'], m2['mse_orig'],
            champ_metrics['Run2']['mae_tr'],
            champ_metrics['Run2']['mse_tr'])

    _psisqrt_bl_tr = _calc_psi_sqrt(
        base_metrics['mae_val'], base_metrics['mse_val'],
        base_metrics['mae_tr'],  base_metrics['mse_tr'])

    _EPS_F   = ProtocolConfig.EPS_F
    _EPS_TIE = ProtocolConfig.EPS_TIE

    both_present = m1['present'] and m2['present']

    # ==========================================================================
    # PHASE 1 — INTER-RUN VERDICT
    # ==========================================================================
    if not m1['present'] and not m2['present']:
        verdict_code  = 'F1.X'
        verdict_short = 'SNG'
        verdict_label = 'No valid champion in either run'
        winner_run    = 'NONE'
        f1_note       = 'Neither Run1 nor Run2 produced a valid champion.'

    elif not m2['present']:
        verdict_code  = 'F1.X'
        verdict_short = 'SNG'
        verdict_label = 'Single Run — Run2 produced no champion'
        winner_run    = 'Run1'
        f1_note       = 'Run2 yielded no valid solutions. Run1 champion selected by default.'

    elif not m1['present']:
        verdict_code  = 'F1.X'
        verdict_short = 'SNG'
        verdict_label = 'Single Run — Run1 produced no champion'
        winner_run    = 'Run2'
        f1_note       = 'Run1 yielded no valid solutions. Run2 champion selected by default.'

    else:
        ev1       = m1['e_val_norm']
        ev2       = m2['e_val_norm']
        delta_abs = ev2 - ev1
        denom     = max(ev1, 1e-12)
        delta_rel = delta_abs / denom

        mse1_n = c1.get('MSE_vldt', float('inf'))
        mse2_n = c2.get('MSE_vldt', float('inf'))

        if abs(delta_abs) < _EPS_F:
            verdict_code  = 'F1.0'
            verdict_short = 'TEQ'
            verdict_label = 'Topological Equivalence'
            winner_run    = 'Run1'
            f1_note       = (
                f"|Δe_val| = {abs(delta_abs):.2e} < ε_F = {_EPS_F:.0e}. "
                "Both runs are indistinguishable at numerical resolution. "
                "Run1 retained by precedence rule."
            )

        elif delta_abs < -_EPS_F:
            improvement_rel = abs(delta_rel)
            if improvement_rel < _EPS_TIE:
                if phi2 < phi1:
                    verdict_code  = 'F1.3φ'
                    verdict_short = 'STP'
                    verdict_label = 'Step Tie — φ Defends Run1'
                    winner_run    = 'Run1'
                    f1_note       = (
                        f"Run2 improved e_val by {improvement_rel*100:.3f}% "
                        f"(< ε_tie = {_EPS_TIE*100:.0f}%, tie zone). "
                        f"φ coherence favors Run1: φ_R1 ({phi1:.4f}) > φ_R2 ({phi2:.4f}). "
                        "Marginal improvement offset by structural coherence loss. "
                        "Run1 retained."
                    )
                else:
                    verdict_code  = 'F1.3'
                    verdict_short = 'GTR'
                    verdict_label = 'Genuine Topological Refinement (φ-confirmed)'
                    winner_run    = 'Run2'
                    f1_note       = (
                        f"Run2 improved e_val by {improvement_rel*100:.3f}% "
                        f"(< ε_tie = {_EPS_TIE*100:.0f}%, tie zone). "
                        f"φ coherence confirms improvement: "
                        f"φ_R2 ({phi2:.4f}) >= φ_R1 ({phi1:.4f}). "
                        "Marginal improvement validated by structural coherence. "
                        "Run2 selected."
                    )
            else:
                if mse2_n > mse1_n + 1e-8:
                    verdict_code  = 'F1.2'
                    verdict_short = 'IRF'
                    verdict_label = 'Invalid Refinement (MSE Tail Degradation)'
                    winner_run    = 'Run1'
                    f1_note       = (
                        f"Run2 improved composite e_val by {improvement_rel*100:.3f}% "
                        f"(> ε_tie = {_EPS_TIE*100:.0f}%), BUT degraded MSE "
                        f"({m2['mse_orig']:.6f} > {m1['mse_orig']:.6f}). "
                        "Under U-MAXP strict tail protection, sacrificing the tail "
                        "for central accuracy is an invalid topological displacement. "
                        "Run1 retained."
                    )
                else:
                    verdict_code  = 'F1.3'
                    verdict_short = 'GTR'
                    verdict_label = 'Genuine Topological Refinement'
                    winner_run    = 'Run2'
                    f1_note       = (
                        f"Run2 improved composite e_val by {improvement_rel*100:.3f}% "
                        f"(> ε_tie = {_EPS_TIE*100:.0f}%) without degrading MSE. "
                        "Transition from Exploration to Refinement is a genuine "
                        "geometric improvement."
                    )

        else:
            regression_rel = abs(delta_rel)
            if regression_rel < _EPS_TIE:
                if phi2 > phi1:
                    verdict_code  = 'F1.3φ'
                    verdict_short = 'STP'
                    verdict_label = 'Step Tie — φ Defends Run2'
                    winner_run    = 'Run2'
                    f1_note       = (
                        f"Run2 regressed e_val by {regression_rel*100:.3f}% "
                        f"(Δ > ε_F but < ε_tie = {_EPS_TIE*100:.0f}%, tie zone). "
                        f"φ coherence favors Run2: φ_R2 ({phi2:.4f}) > φ_R1 ({phi1:.4f}). "
                        "Run2 selected as champion."
                    )
                else:
                    verdict_code  = 'F1.2'
                    verdict_short = 'IRF'
                    verdict_label = 'Inefficient Refinement (marginal regression)'
                    winner_run    = 'Run1'
                    f1_note       = (
                        f"Run2 regressed e_val by {regression_rel*100:.3f}% "
                        f"(Δ > ε_F but < ε_tie = {_EPS_TIE*100:.0f}%). "
                        f"φ coherence confirms Run1: φ_R1 ({phi1:.4f}) >= φ_R2 ({phi2:.4f}). "
                        "Marginal degradation — Run1 retained."
                    )
            else:
                verdict_code  = 'F1.2'
                verdict_short = 'IRF'
                verdict_label = 'Inefficient Refinement'
                winner_run    = 'Run1'
                f1_note       = (
                    f"Run2 regressed composite e_val by {regression_rel*100:.3f}% "
                    f"(> ε_tie = {_EPS_TIE*100:.0f}%). "
                    "Refinement phase degraded over Exploration. Run1 retained."
                )

    phase1_winner = winner_run

    # ==========================================================================
    # PHASE 3 — INCOHERENCE-PENALIZED ERROR GUARDRAIL (E_inc) + EVT CHANNEL
    # Always active when both runs are present, UNLESS Line B is active.
    # Metric: E_inc = sqrt(e_tr * e_val) * (1 - phi)
    # ==========================================================================
    phase3 = dict(
        active=False,
        suspended_by_line_b=False,
        e_inc1=0.0,
        e_inc2=0.0,
        delta_rel=0.0,
        step='',
        phase3_champion='NONE',
        override_applied=False,
        original_winner=phase1_winner
    )

    p1_champ_reg   = regime1 if phase1_winner == 'Run1' else regime2
    p1_champ_psi   = psi1    if phase1_winner == 'Run1' else psi2
    p1_twin_reg    = regime2 if phase1_winner == 'Run1' else regime1
    p1_twin_psi    = psi2    if phase1_winner == 'Run1' else psi1
    p1_champ_e_val = (m1['e_val_norm'] if phase1_winner == 'Run1'
                      else m2['e_val_norm'] if phase1_winner == 'Run2'
                      else 0.0)

    cond_i   = (p1_champ_reg == 'SOV') and (p1_champ_psi > _EPS_PSI)
    cond_ii  = (p1_twin_reg  == 'OFT') and (p1_twin_psi  > _EPS_PSI)
    cond_iii = both_present and (p1_champ_e_val > _EPS_F)
    f1vb_active = cond_i and cond_ii and cond_iii

    if both_present and not f1vb_active:
        phase3['active'] = True

        def _get_e_tr_orig(champ_dict_metrics):
            if not champ_dict_metrics: return 0.0
            m_tr  = champ_dict_metrics['mae_tr'] * scale
            ms_tr = champ_dict_metrics['mse_tr'] * sq_scl
            return UMaxPCriterion.composite_error(m_tr, ms_tr)

        e_tr1_orig = _get_e_tr_orig(champ_metrics.get('Run1'))
        e_tr2_orig = _get_e_tr_orig(champ_metrics.get('Run2'))

        e_inc1 = StructuralMetricsEngine.compute_e_inc(m1['e_val_orig'], e_tr1_orig, phi1)
        e_inc2 = StructuralMetricsEngine.compute_e_inc(m2['e_val_orig'], e_tr2_orig, phi2)

        delta_inc_abs = abs(e_inc2 - e_inc1)
        delta_inc_rel = delta_inc_abs / max(e_inc1, e_inc2, 1e-12)

        if delta_inc_rel > _EPS_TIE:
            phi_winner = 'Run1' if phi1 >= phi2 else 'Run2'
            
            _phi_emp_r1 = getattr(model, '_phi_emp_r1', 0.0)
            _phi_emp_r2 = getattr(model, '_phi_emp_r2', 0.0)
            
            if _phi_emp_r1 > 0 or _phi_emp_r2 > 0:
                h1 = StructuralMetricsEngine.compute_h_factor(_phi_emp_r1, 1e-9)
                h2 = StructuralMetricsEngine.compute_h_factor(_phi_emp_r2, 1e-9)
                phi_emp_winner = 'Run1' if h1 < h2 else 'Run2'
                
                if phi_emp_winner != phi_winner:
                    p3_champ = phi_emp_winner
                    h_w = h1 if p3_champ == 'Run1' else h2
                    h_l = h2 if p3_champ == 'Run1' else h1
                    pe_w = _phi_emp_r1 if p3_champ == 'Run1' else _phi_emp_r2
                    pe_l = _phi_emp_r2 if p3_champ == 'Run1' else _phi_emp_r1
                    
                    step_str = (
                        f"Step 3b-II: ΔE_inc_rel = {delta_inc_rel*100:.3f}% > ε_tie ({_EPS_TIE*100:.0f}%).\n"
                        f"             φ points to {phi_winner} (φ_R1={phi1:.4f}, φ_R2={phi2:.4f}), BUT\n"
                        f"             φ_emp diverged. EVT Guardrail (H factor) dominates.\n"
                        f"             {p3_champ} selected: H={h_w:.6f} (φ_emp={pe_w:.4f}) < H={h_l:.6f} (φ_emp={pe_l:.4f})."
                    )
                else:
                    p3_champ = phi_winner
                    step_str = (
                        f"Step 3b-II: ΔE_inc_rel = {delta_inc_rel*100:.3f}% > ε_tie ({_EPS_TIE*100:.0f}%).\n"
                        f"             φ and φ_emp BOTH confirm {p3_champ} "
                        f"(φ_R1={phi1:.4f}, φ_R2={phi2:.4f} | φ_emp R1={_phi_emp_r1:.4f}, R2={_phi_emp_r2:.4f})."
                    )
            else:
                p3_champ = phi_winner
                step_str = (
                    f"Step 3b-II: ΔE_inc_rel = {delta_inc_rel*100:.3f}% > ε_tie ({_EPS_TIE*100:.0f}%).\n"
                    f"             φ_emp is 0 for both (within EVT noise channel).\n"
                    f"             φ strictly decides: {p3_champ} wins (φ_R1={phi1:.4f}, φ_R2={phi2:.4f})."
                )
        else:
            p3_champ = 'Run1' if e_inc1 <= e_inc2 else 'Run2'
            step_str = (
                f"Step 3b-I: ΔE_inc_rel = {delta_inc_rel*100:.3f}% ≤ ε_tie ({_EPS_TIE*100:.0f}%)\n"
                f"             quasi-equivalence zone, lower E_inc wins "
                f"(E_inc_R1={e_inc1:.6f}, E_inc_R2={e_inc2:.6f})."
            )

        phase3.update({
            'e_inc1'          : e_inc1,
            'e_inc2'          : e_inc2,
            'delta_rel'       : delta_inc_rel,
            'step'            : step_str,
            'phase3_champion' : p3_champ,
            'override_applied': p3_champ != phase1_winner,
        })

        # ------------------------------------------------------------------
        # STEP 3b STABILITY AUDIT (θ-filter)
        # Applied only after Step 3b selects a winner. The audit uses the
        # stability proxies already available in this report (SDE_b, GCI,
        # and A_emp) and reverses the decision only if the winner is
        # significantly less stable (|Δ| ≥ θ = 0.10). Otherwise, the original
        # selection is retained.
        # ------------------------------------------------------------------
        
        _THETA = ProtocolConfig.THETA_STABILITY

        # SDE_b proxy: Independently calculated to expose topological degradation
        try:
            # Retrieve lists of VALID solutions from Run 1 and Run 2
            _r1_valid_list = getattr(model, 'run1_valid_', []) or []
            _r2_valid_list = getattr(model, 'run2_valid_', []) or []
            
            _n1_valid = len(_r1_valid_list)
            _n2_valid = len(_r2_valid_list)
            
            # Defensive fallback for design boundaries.
            # Uses getattr to avoid report failures if training ends
            # before these attributes are initialized.
            _base_mse = getattr(model, 'baseline_mse_', 1e-9)
            _filter_lims = getattr(model, 'filter_limits_', {'lower_limit': 1.05, 'upper_limit': 1.3})
            _low_lim = _filter_lims.get('lower_limit', 1.05)
            _upp_lim = _filter_lims.get('upper_limit', 1.3)
            
            # Auxiliary function counts of elites
            def count_elites(valid_sols, ref_mse, low, upp):
                if not valid_sols or ref_mse <= 0: return 0
                return sum(1 for sol in valid_sols if low < (sol.get('MSE_train', 0.0) / ref_mse) < upp)
                
            _n1_elite = count_elites(_r1_valid_list, _base_mse, _low_lim, _upp_lim)
            _n2_elite = count_elites(_r2_valid_list, _base_mse, _low_lim, _upp_lim)
            
            # Independent topological collapse rule: N_elite < 3 => SDE_b = 0.0
            _sde_r1 = 0.0 if _n1_elite < 2 else (_n1_elite / max(_n1_valid, 1))
            _sde_r2 = 0.0 if _n2_elite < 2 else (_n2_elite / max(_n2_valid, 1))

        except Exception:
            _sde_r1 = _sde_r2 = None
            _n1_valid = _n2_valid = 0
            _n1_elite = _n2_elite = 0

        # GCI proxy — phi already computed in this function
        _gci_r1 = phi1
        _gci_r2 = phi2

        # A_emp proxy — phi_emp set on model by DGDTLUnifiedExecutor.
        _pe_r1 = getattr(model, '_phi_emp_r1', None)
        _pe_r2 = getattr(model, '_phi_emp_r2', None)
        if _pe_r1 is not None and _pe_r2 is not None:
            _aemp_r1 = float(np.exp(-float(_pe_r1) ** 2))
            _aemp_r2 = float(np.exp(-float(_pe_r2) ** 2))
        else:
            _aemp_r1 = _aemp_r2 = None

        # The SDE_b proxy independently evaluates R1 and R2 for 
        #     capture true intra-scout topological degradations.
        _comp_map = {
            'SDE_b': (_sde_r1,  _sde_r2),
            'GCI'  : (_gci_r1,  _gci_r2),
            'A_emp': (_aemp_r1, _aemp_r2),
        }

        _active = {}
        _all_available = all(v is not None for vals in _comp_map.values() for v in vals)
        
        if _all_available:
            for _j, (_vr1, _vr2) in _comp_map.items():
                _w_val = float(_vr1 if p3_champ == 'Run1' else _vr2)
                _l_val = float(_vr2 if p3_champ == 'Run1' else _vr1)
                _diff  = abs(_w_val - _l_val)
                if _diff >= _THETA and _w_val < _l_val:
                    _active[_j] = (_diff, _w_val, _l_val)

        if _active:
            _deciding = max(_active, key=lambda j: _active[j][0])
            _d_diff, _d_w, _d_l = _active[_deciding]

            # Diagnostic only: expose the raw counts behind the SDE_b proxy
            _extra_diag = {}
            if 'SDE_b' in _active:
                _w_is_r1 = (p3_champ == 'Run1')
                _w_elite, _w_valid = (_n1_elite, _n1_valid) if _w_is_r1 else (_n2_elite, _n2_valid)
                _l_elite, _l_valid = (_n2_elite, _n2_valid) if _w_is_r1 else (_n1_elite, _n1_valid)
                _extra_diag['SDE_b'] = f" [N_elite/N_valid — W: {_w_elite}/{_w_valid}, L: {_l_elite}/{_l_valid}]"

            _flags = ', '.join(
                f"{j}: W={_active[j][1]:.4f} < L={_active[j][2]:.4f}"
                f" |Δ|={_active[j][0]:.4f}{_extra_diag.get(j, '')}"
                for j in _active
            )
            _audit_note = (
                f"\n  [θ-AUDIT | θ={_THETA}] Stability filter triggered — "
                f"winner was less stable in: {_flags}. "
                f"Deciding component (max |Δ|): {_deciding} "
                f"(W={_d_w:.4f} < L={_d_l:.4f}, |Δ|={_d_diff:.4f}). "
                f"REVERSAL APPLIED."
            )
            p3_champ = 'Run2' if p3_champ == 'Run1' else 'Run1'
            phase3.update({
                'step'            : phase3['step'] + _audit_note,
                'phase3_champion' : p3_champ,
                'override_applied': p3_champ != phase1_winner,
            })

        if phase3['override_applied']:
            winner_run = p3_champ

    elif both_present and f1vb_active:
        phase3['suspended_by_line_b'] = True

    # ==========================================================================
    # ASSIGNMENTS FOR LINE B
    # ==========================================================================
    prov_deployed_m       = m1 if phase1_winner == 'Run1' else (m2 if phase1_winner == 'Run2' else None)
    prov_deployed_reg     = p1_champ_reg
    prov_deployed_psi     = p1_champ_psi
    prov_deployed_psisqrt = psisqrt1 if phase1_winner == 'Run1' else psisqrt2

    twin_run     = 'Run2'    if phase1_winner == 'Run1' else 'Run1'
    twin_m       = m2        if phase1_winner == 'Run1' else m1
    twin_reg     = p1_twin_reg
    twin_psi     = p1_twin_psi
    twin_psisqrt = psisqrt2  if phase1_winner == 'Run1' else psisqrt1

    # ==========================================================================
    # LINE B — F1-VB PARALLEL BRANCH
    # ==========================================================================
    vbd_status = 'NOT_ACTIVE'

    _eps12 = 1e-12
    _rho_mae_blrt = 1.0 / (_ratio_mae_bl  + _eps12)
    _rho_mse_blrt = 1.0 / (_ratio_mse_bl  + _eps12)
    _psi_bl_rt = float(np.log10(_rho_mae_blrt) * np.log10(_rho_mse_blrt))

    lineB = dict(
        active           = f1vb_active,
        twin_run         = twin_run,
        twin_regime      = twin_reg,
        twin_psi         = twin_psi,
        twin_psisqrt     = twin_psisqrt,
        psisqrt_bl_tr    = _psisqrt_bl_tr,
        psi_bl_rt        = _psi_bl_rt,
        beats_bl_tr      = None,
        beats_bl_rt      = None,
        lb_verdict       = None,
        sde_champion     = None,
        sde_twin         = None,
        sde_ratio        = None,
        topo_class       = None,
        p_coh            = None,
        p_coh_note       = '',
        final_champion   = winner_run,
        override_note    = '',
        scope_note       = (
            "Full Line B canonical verification requires the Hunter. "
            "This Executor covers Shade 1 (unique twin) with the "
            "bidimensional criterion psi_sqrt / |Ψ|."
        )
    )

    if f1vb_active:
        vbd_status = 'ACTIVE'

    if f1vb_active and twin_m.get('present', False):
        beats_tr = twin_psisqrt > _psisqrt_bl_tr
        lineB['beats_bl_tr'] = beats_tr

        beats_rt = abs(twin_psi) < abs(_psi_bl_rt)
        lineB['beats_bl_rt'] = beats_rt

        if beats_tr and beats_rt:
            lb_verdict = 'Certified'
            lineB['final_champion'] = twin_run
            lineB['override_note'] = f"The OFT twin ({twin_run}) is fully certified and OVERRIDES the SOV champion ({phase1_winner})."
        elif beats_tr and not beats_rt:
            lb_verdict = 'Partial-TR'
            lineB['override_note'] = f"The OFT twin ({twin_run}) lacks full certification. The original champion ({phase1_winner}) is retained under diagnostic warning."
        elif beats_rt and not beats_tr:
            lb_verdict = 'Partial-RT'
            lineB['override_note'] = f"The OFT twin ({twin_run}) lacks full certification. The original champion ({phase1_winner}) is retained under diagnostic warning."
        else:
            lb_verdict = 'Diagnostic'
            lineB['override_note'] = f"The OFT twin ({twin_run}) failed certification. The original champion ({phase1_winner}) is retained under diagnostic warning."

        lineB['lb_verdict'] = lb_verdict
        
        sde_champ = None
        sde_twin  = None
        try:
            rep1 = model.run1_report_df_
            rep2 = model.run2_report_df_
            rep_champ = rep1 if phase1_winner == 'Run1' else rep2
            rep_twin  = rep2 if phase1_winner == 'Run1' else rep1
            
            # Recover design limits for elite counting
            _base_mse = getattr(model, 'baseline_mse_', 1e-9)
            _filter_lims = getattr(model, 'filter_limits_', {'lower_limit': 1.05, 'upper_limit': 1.3})
            _low_lim = _filter_lims.get('lower_limit', 1.05)
            _upp_lim = _filter_lims.get('upper_limit', 1.3)
            
            def count_elites(valid_sols, ref_mse, low, upp):
                if not valid_sols or ref_mse <= 0: return 0
                return sum(1 for sol in valid_sols if low < (sol.get('MSE_train', 0.0) / ref_mse) < upp)

            if rep_champ is not None and not rep_champ.empty:
                valid_list_champ = getattr(model, 'run1_valid_' if phase1_winner == 'Run1' else 'run2_valid_', [])
                n_valid_champ = len(valid_list_champ)
                n_elite_champ = count_elites(valid_list_champ, _base_mse, _low_lim, _upp_lim)
                
                # Topological collapse rule
                sde_champ = 0.0 if n_elite_champ < 2 else (n_elite_champ / max(n_valid_champ, 1))

            if rep_twin is not None and not rep_twin.empty:
                valid_list_twin = getattr(model, 'run2_valid_' if phase1_winner == 'Run1' else 'run1_valid_', [])
                n_valid_twin = len(valid_list_twin)
                n_elite_twin = count_elites(valid_list_twin, _base_mse, _low_lim, _upp_lim)
                
                # Topological collapse rule
                sde_twin = 0.0 if n_elite_twin < 2 else (n_elite_twin / max(n_valid_twin, 1))
                
        except Exception:
            sde_champ = None
            sde_twin  = None

        lineB['sde_champion'] = sde_champ
        lineB['sde_twin']     = sde_twin

        if sde_champ is not None and sde_twin is not None and sde_champ > 0:
            ratio = sde_twin / sde_champ
            lineB['sde_ratio'] = ratio
            lineB['topo_class'] = (
                'Not available' if sde_twin == 0 else
                'Robust'        if ratio > 0.5   else
                'Sensitive'
            )
        else:
            lineB['topo_class'] = 'Not evaluable (requires Hunter)'

        if twin_m.get('present', False) and prov_deployed_m is not None:
            psi_twin_lower      = abs(twin_psi)    < abs(prov_deployed_psi)
            psisqrt_twin_higher = twin_psisqrt     > prov_deployed_psisqrt
            p_coh = psi_twin_lower and psisqrt_twin_higher
            lineB['p_coh'] = p_coh
            if p_coh:
                lineB['p_coh_note'] = (
                    f"TRUE — Twin is more balanced than champion: "
                    f"|Ψ_twin|={abs(twin_psi):.6f} < |Ψ_champ|={abs(prov_deployed_psi):.6f} "
                    f"and psi_sqrt_twin={twin_psisqrt:.6f} > psi_sqrt_champ={prov_deployed_psisqrt:.6f}. "
                    "SOV contamination affected selection in a quantifiable way."
                )
            else:
                lineB['p_coh_note'] = (
                    "FALSE — the practical impact of SOV bias is nil: "
                    "The champion would have won regardless of inflation."
                )
        else:
            lineB['p_coh']      = None
            lineB['p_coh_note'] = 'Not evaluable — twin with no metrics available.'

    if f1vb_active and lineB.get('lb_verdict') == 'Certified':
        winner_run = lineB['final_champion']

    deployed_champ = c1 if winner_run == 'Run1' else (c2 if winner_run == 'Run2' else None)
    deployed_m     = m1 if winner_run == 'Run1' else (m2 if winner_run == 'Run2' else None)
    deployed_phi   = phi1 if winner_run == 'Run1' else phi2
    deployed_psi   = psi1 if winner_run == 'Run1' else psi2
    deployed_reg   = regime1 if winner_run == 'Run1' else regime2
    _phi_r1_dep    = getattr(model, '_phi_emp_r1', 0.0)
    _phi_r2_dep    = getattr(model, '_phi_emp_r2', 0.0)

    trail_lines = []
    trail_lines.append(f"[Phase 1 / Inter-Run]  {verdict_code} ({verdict_short}): {f1_note}")

    if phase3['active']:
        if phase3['override_applied']:
            trail_lines.append(
                f"[Phase 3 / E_inc    ]  OVERRIDE — {phase3['step']} "
            )
        else:
            trail_lines.append(
                f"[Phase 3 / E_inc    ]  CONFIRMED — {phase3['step']} "
            )
    elif phase3['suspended_by_line_b']:
        trail_lines.append(
            "[Phase 3 / E_inc    ]  SUSPENDED — Line B (F1-VB) is active; "
            "E_inc guardrail does not apply over a regime-inversion scenario."
        )
    else:
        trail_lines.append(
            "[Phase 3 / E_inc    ]  NOT ACTIVE — requires both Run1 and Run2."
        )

    if f1vb_active:
        lb_outcome = lineB.get('lb_verdict', 'N/A')
        if lb_outcome == 'Certified':
            trail_lines.append(
                f"[Line B / F1-VB    ]  OVERRIDE — OFT twin ({twin_run}) fully certified. "
                f"Final deployed: {winner_run}."
            )
        else:
            trail_lines.append(
                f"[Line B / F1-VB    ]  ACTIVE, verdict={lb_outcome} — "
                f"twin not certified; original selection retained."
            )
    else:
        trail_lines.append(
            "[Line B / F1-VB    ]  NOT ACTIVE — no inter-scout regime inversion detected."
        )

    trail_lines.append(f"[Final Deployed    ]  {winner_run}")
    decision_trail = "\n  ".join(trail_lines)

    if phase3['active']:
        p3_status = f"OVERRIDE → {phase3['phase3_champion']}" if phase3['override_applied'] else f"CONFIRMED ({phase1_winner})"
    elif phase3['suspended_by_line_b']:
        p3_status = "SUSPENDED (Line B active)"
    else:
        p3_status = "NOT ACTIVE (single run)"

    sep  = "=" * 70
    sep2 = "-" * 70
    sep3 = "~" * 70

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"{sep}\n")
        f.write(f"  DGDTL CHAMPION SELECTION REPORT\n")
        f.write(f"  File — U_MAXP Structural Selection (Phase 1 / Inter-Run)\n")
        f.write(f"  Mode: {mode.upper()}    Scale note: {scale_note}\n")
        f.write(f"{sep}\n\n")

        phase1_twin = 'Run2' if phase1_winner == 'Run1' else 'Run1'
        f.write(f"PHASE 1 VERDICT : {phase1_winner} -> [{verdict_code}]  {verdict_short}  —  {verdict_label}\n")
        f.write(f"PHASE 1 TWIN    : {phase1_twin} -> [{verdict_code}]  {verdict_short}  —  {verdict_label}\n")
        f.write(f"PHASE 3 STATUS  : {p3_status}\n")
        f.write(f"VBD FLAG        : {vbd_status}\n")
        f.write(f"FINAL DEPLOYED  : {winner_run}\n\n")

        f.write(f"DECISION TRAIL:\n  {decision_trail}\n\n")

        f.write(f"{sep2}\n")
        f.write(f"  Ψ DISCRIMINANT — VALIDATION BIAS DETECTOR\n")
        f.write(f"{sep2}\n")
        f.write(f"  ε_Ψ threshold        : {_EPS_PSI:.0e}  (= ε_F²)\n\n")
        f.write(f"  Run1  Ψ={psi1:.8f}  log_MAE={lmae1:.6f}  log_MSE={lmse1:.6f}  "
                f"Regime={regime1}\n")
        f.write(f"  Run2  Ψ={psi2:.8f}  log_MAE={lmae2:.6f}  log_MSE={lmse2:.6f}  "
                f"Regime={regime2}\n\n")
        f.write(f"  Champion ({phase1_winner}): Regime={prov_deployed_reg}  "
                f"|Ψ|={abs(prov_deployed_psi):.8f}\n")
        f.write(f"  Twin    ({twin_run}):    Regime={twin_reg}  "
                f"|Ψ|={abs(twin_psi):.8f}\n\n")

        f.write(f"{sep2}\n")
        f.write(f"  RUN1 CHAMPION METRICS\n")
        f.write(f"{sep2}\n")
        if m1['present']:
            f.write(f"  Original Index      : {m1['idx']}\n")
            f.write(f"  Selection Criterion : {m1['criterion']}\n")
            f.write(f"  MAE (validation)    : {m1['mae_orig']:.6f}\n")
            f.write(f"  MSE (validation)    : {m1['mse_orig']:.6f}\n")
            f.write(f"  e_val composite     : {m1['e_val_orig']:.6f}"
                    f"  [sqrt(MAE * sqrt(MSE)), original scale]\n")
            f.write(f"  φ (Cauchy Balance)  : {phi1:.4f}\n")
            f.write(f"  Ψ (Bias Discrim.)   : {psi1:.8f}  Regime: {regime1}\n")
        else:
            f.write(f"  No valid champion produced by Run1.\n")

        f.write(f"\n{sep2}\n")
        f.write(f"  RUN2 CHAMPION METRICS\n")
        f.write(f"{sep2}\n")
        if m2['present']:
            f.write(f"  Original Index      : {m2['idx']}\n")
            f.write(f"  Selection Criterion : {m2['criterion']}\n")
            f.write(f"  MAE (validation)    : {m2['mae_orig']:.6f}\n")
            f.write(f"  MSE (validation)    : {m2['mse_orig']:.6f}\n")
            f.write(f"  e_val composite     : {m2['e_val_orig']:.6f}"
                    f"  [sqrt(MAE * sqrt(MSE)), original scale]\n")
            f.write(f"  φ (Cauchy Balance)  : {phi2:.4f}\n")
            f.write(f"  Ψ (Bias Discrim.)   : {psi2:.8f}  Regime: {regime2}\n")
        else:
            f.write(f"  No valid champion produced by Run2.\n")

        if both_present:
            delta_disp     = m2['e_val_orig'] - m1['e_val_orig']
            delta_disp_rel = delta_disp / max(m1['e_val_orig'], 1e-12)
            f.write(f"\n{sep2}\n")
            f.write(f"  COMPARISON SUMMARY  "
                    f"(decision in model space; display in original scale)\n")
            f.write(f"{sep2}\n")
            f.write(f"  e_val Run1          : {m1['e_val_orig']:.6f}\n")
            f.write(f"  e_val Run2          : {m2['e_val_orig']:.6f}\n")
            f.write(f"  Δe_val (R2 − R1)    : {delta_disp:+.6f}  "
                    f"({'Run2 better' if delta_disp < 0 else 'Run1 better'})\n")
            f.write(f"  Δe_val (relative)   : {delta_disp_rel*100:+.4f}%\n")
            f.write(f"  ε_F threshold       : {_EPS_F:.0e}\n")
            f.write(f"  ε_tie threshold     : {_EPS_TIE*100:.0f}%\n")

        f.write(f"\n{sep}\n")
        f.write(f"  LINE B — F1-VB PARALLEL BRANCH\n")
        f.write(f"{sep}\n")

        if not f1vb_active:
            f.write(f"  Status              : NOT ACTIVE\n\n")
            f.write(f"  Activation conditions (all required):\n")
            f.write(f"    (i)  Champion is SOV with |Ψ| >= ε_Ψ : "
                    f"{'✓' if cond_i  else '✗'}  "
                    f"(regime={prov_deployed_reg}, |Ψ|={abs(prov_deployed_psi):.8f})\n")
            f.write(f"    (ii) Twin is OFT with |Ψ| >= ε_Ψ     : "
                    f"{'✓' if cond_ii else '✗'}  "
                    f"(regime={twin_reg}, |Ψ|={abs(twin_psi):.8f})\n")
            f.write(f"    (iii)Champion operationally relevant  : "
                    f"{'✓' if cond_iii else '✗'}\n\n")
            f.write(f"  Interpretation: No inter-scout regime inversion detected.\n")
            f.write(f"  The champion score is not flagged as inflated by "
                    f"validation partition bias.\n")

        else:
            f.write(f"  Status              : ACTIVE — VBD FLAG SET\n")
            f.write(f"  Champion ({phase1_winner}) : SOV regime  "
                    f"Ψ={prov_deployed_psi:.8f}  (score may be inflated)\n")
            f.write(f"  Twin    ({twin_run})    : OFT regime  "
                    f"Ψ={twin_psi:.8f}  (unbiased topological evidence)\n\n")

            f.write(f"{sep3}\n")
            f.write(f"  TWIN VERIFICATION — Shade 1 (unique twin)\n")
            f.write(f"{sep3}\n\n")

            f.write(f"  [A] Criterion 1 — vs BL_TR  (psi_sqrt = √(ratio_MAE × ratio_RMSE))\n")
            f.write(f"      psi_sqrt(BL_TR) : {lineB['psisqrt_bl_tr']:.8f}  (natural reference of the domain)\n")
            f.write(f"      psi_sqrt(BL_RT) : 1.00000000  (= 1 by construction)\n")
            f.write(f"      psi_sqrt(twin)  : {lineB['twin_psisqrt']:.8f}\n")
            c1_str = '✓ OVERPASSES' if lineB['beats_bl_tr'] else '✗ DOES NOT overpass'
            f.write(f"      psi_sqrt(twin) > psi_sqrt(BL_TR)?  {c1_str}\n\n")

            f.write(f"  [B] Criterion 2 — vs BL_RT  (|Ψ| = |log10(ρ_MAE) × log10(ρ_MSE)|)\n")
            f.write(f"      |Ψ(BL_RT)| : {abs(lineB['psi_bl_rt']):.8f}  (structural OFT, fixed)\n")
            f.write(f"      |Ψ(twin)|  : {abs(twin_psi):.8f}\n")
            c2_str = '✓ OVERPASSES' if lineB['beats_bl_rt'] else '✗ DOES NOT overpass'
            f.write(f"      |Ψ(twin)| < |Ψ(BL_RT)|?  {c2_str}\n\n")

            f.write(f"  [C] Verdict Line B: {lineB['lb_verdict']}\n")
            verdicts_map = {
                'Certified' : 'Twin overpasses both benchmarks of the domain.',
                'Partial-TR': 'Twin overpasses Baseline Train but not Baseline Re-train.',
                'Partial-RT': 'Twin overpasses Baseline Re-train but not Baseline Train.',
                'Diagnostic': 'Twin does not overpass any benchmarks — diagnostic evidence.',
            }
            f.write(f"      {verdicts_map.get(lineB['lb_verdict'], '')}\n\n")

            f.write(f"  [D] Topological classification (SDE_b proxy)\n")
            if lineB['sde_champion'] is not None:
                f.write(f"      SDE_b proxy (champion) : "
                        f"{lineB['sde_champion']:.4f}  [N_elite/N_valid]\n")
                f.write(f"      SDE_b proxy (twin)     : "
                        f"{lineB['sde_twin']:.4f}\n")
                f.write(f"      Ratio twin/champion    : "
                        f"{lineB['sde_ratio']:.4f}  (threshold > 0.5 for Robust)\n")
            f.write(f"      Classification          : {lineB['topo_class']}\n\n")

            f.write(f"  [E] Coherence Proposition P_coh\n")
            f.write(f"      Condition: |Ψ(twin)| < |Ψ(champion)|\n")
            f.write(f"                 AND psi_sqrt(twin) > psi_sqrt(champion)\n")
            if lineB['p_coh'] is not None:
                pch_str = 'TRUE' if lineB['p_coh'] else 'FALSE'
                f.write(f"      Result          : {pch_str}\n")
                f.write(f"      Interpretation  : {lineB['p_coh_note']}\n\n")
            else:
                f.write(f"      Result          : NOT EVALUABLE\n")
                f.write(f"      {lineB['p_coh_note']}\n\n")

            f.write(f"  [F] Scope\n")
            f.write(f"      {lineB['scope_note']}\n\n")

            f.write(f"  [G] Final Line B Outcome\n")
            f.write(f"      Final Champion : {lineB['final_champion']}\n")
            f.write(f"      Resolution     : {lineB['override_note']}\n")

        f.write(f"\n{sep}\n")
        f.write(f"  PHASE 3 — STRUCTURAL COHERENCE GUARDRAIL (E_inc)\n")
        f.write(f"{sep}\n")

        if phase3['suspended_by_line_b']:
            f.write(f"  [STATUS] : SUSPENDED — Line B (F1-VB) is active.\n")
            f.write(f"             E_inc guardrail does not apply over a regime-inversion scenario.\n")
            f.write(f"             Epistemological precedence: a champion flagged as SOV-inflated\n")
            f.write(f"             cannot be evaluated for structural coherence against its twin.\n")

        elif not phase3['active']:
            f.write(f"  [STATUS] : NOT ACTIVE — requires both Run1 and Run2.\n")

        else:
            f.write(f"  [RULE]   : E_inc = √(e_tr × e_val) × (1 − φ)\n")
            f.write(f"             Step 3b-I  (ΔE_inc_rel ≤ ε_tie): lower E_inc wins.\n")
            f.write(f"             Step 3b-II (ΔE_inc_rel >  ε_tie): lower H (higher φ_emp) dominates if contradicts φ.\n\n")
            
            _h1_str = f"{StructuralMetricsEngine.compute_h_factor(_phi_r1_dep, 1e-9):.4f}" if _phi_r1_dep > 0 else "N/A"
            _h2_str = f"{StructuralMetricsEngine.compute_h_factor(_phi_r2_dep, 1e-9):.4f}" if _phi_r2_dep > 0 else "N/A"

            f.write(f"      E_inc(Run1)    : {phase3['e_inc1']:.6f}  [φ = {phi1:.4f} | φ_emp = {_phi_r1_dep:.4f} | H = {_h1_str}]\n")
            f.write(f"      E_inc(Run2)    : {phase3['e_inc2']:.6f}  [φ = {phi2:.4f} | φ_emp = {_phi_r2_dep:.4f} | H = {_h2_str}]\n")
            f.write(f"      ΔE_inc (rel)   : {phase3['delta_rel']*100:.3f}%\n\n")
            f.write(f"      {phase3['step']}\n\n")

            if phase3['override_applied']:
                f.write(f"  [STATUS] : OVERRIDE — {phase3['phase3_champion']} selected, "
                        f"overriding Phase 1 ({phase3['original_winner']}).\n")
            else:
                f.write(f"  [STATUS] : CONFIRMED — Phase 1 selection ({phase3['original_winner']}) "
                        f"structurally validated.\n")

        f.write(f"\n{sep2}\n")
        f.write(f"  DEPLOYED CHAMPION SUMMARY\n")
        f.write(f"{sep2}\n")
        if deployed_champ is not None and deployed_m is not None:
            f.write(f"  Source              : {winner_run}\n")
            f.write(f"  Original Index      : {deployed_m['idx']}\n")
            f.write(f"  MAE (validation)    : {deployed_m['mae_orig']:.6f}\n")
            f.write(f"  MSE (validation)    : {deployed_m['mse_orig']:.6f}\n")
            f.write(f"  e_val composite     : {deployed_m['e_val_orig']:.6f}\n")
            f.write(f"  φ (Cauchy Balance)  : {deployed_phi:.4f}\n")
            f.write(f"  φ_emp (EVT excess)  : {(_phi_r1_dep if winner_run == 'Run1' else _phi_r2_dep):.6f}\n")
            f.write(f"  Ψ regime            : {deployed_reg}  "
                    f"|Ψ|={abs(deployed_psi):.8f}\n")
            f.write(f"  VBD Flag            : {vbd_status}\n")
            f.write(f"  No. of coefficients : {len(deployed_champ.get('coeffs', []))}\n")
        else:
            f.write(f"  No champion available for deployment.\n")

        f.write(f"\n{sep}\n")
        f.write(f"  METHODOLOGY NOTE\n")
        f.write(f"{sep}\n")
        f.write(
            "  This file implements the Phase-1 (Inter-Run) + Phase-3 stages of\n"
            "  the U_MAXP Structural Selection Framework.\n"
            "  The primary selection criterion is the composite validation error\n"
            "  e_val = sqrt(MAE_vldt * sqrt(MSE_vldt)), consistent with\n"
            "  dgdtl_core._select_champion_and_get_report. The comparison is\n"
            "  performed in the model/normalized space to ensure scale-invariance;\n"
            "  all displayed metrics are converted to original units.\n\n"
            "  PHASE 3 EXECUTION POLICY:\n"
            "  Phase 3 (E_inc guardrail) runs automatically whenever both Run1\n"
            "  and Run2 produce valid champions, UNLESS Line B (F1-VB) is active.\n"
            "  A Line B activation indicates a regime-inversion (SOV champion vs\n"
            "  OFT twin); applying E_inc over an inflated champion score would\n"
            "  lack epistemological validity, so Phase 3 is suspended in that case.\n\n"
            "  STEP 3b-II — NATIVE EVT CHANNEL INTEGRATION (H-FACTOR):\n"
            "  When the structural gap is significant (ΔE_inc_rel > eps_tie), the theory\n"
            "  requires validating structural coherence (φ) against empirical\n"
            "  authenticity (φ_emp). If they disagree, the Hyperbolic Tail Factor (H)\n"
            "  derived from φ_emp overrides structural coherence. (Ref: U-MAXP Cor. 2.1)\n\n"
            "  SYMMETRY OF φ ARBITER:\n"
            "  φ is the sole arbiter in the tie zone [ε_F, ε_tie) in BOTH\n"
            "  improvement and regression directions. The MSE guardrail (U-MAXP\n"
            "  Strict Tail Protection) applies exclusively outside the tie zone\n"
            "  (|Δe_val_rel| ≥ ε_tie) where clear improvement justifies its use.\n\n"
            "  LINE B SCOPE:\n"
            "  The F1-VB parallel branch uses a bidimensional criterion:\n"
            "  Criterion 1 (vs BL_TR): psi_sqrt = sqrt(ratio_MAE x ratio_RMSE)\n"
            "  Criterion 2 (vs BL_RT): |Psi| = |log10(rho_MAE) x log10(rho_MSE)|\n"
            "  U_MAXP_k does NOT apply to the OFT twin (loses by construction).\n"
            "  Full Line B canonical verification requires the Hunter.\n\n"
            "  Verdict codes: TEQ / GTR / IRF / STP / SNG.\n"
            "  This report does NOT apply Phase-2 (Hard-Mode) or Phase-4 (DOA)\n"
            "  logic — those require U_RAW values from dgdtl_hunter.\n\n"
            "  Numerical thresholds:\n"
            f"    ε_F   = {_EPS_F:.0e}  (quantization floor δ_min=1e-6, P3)\n"
            f"    ε_tie = {_EPS_TIE*100:.0f}%   "
            f"(geometric mean Max Tie=0.35% / Min Win=6.1%, P5)\n"
            f"    ε_Ψ   = {_EPS_PSI:.0e}  (= ε_F², filters float noise)\n"
        )
        f.write(f"{sep}\n")


    return winner_run

# =============================================================================
# MAIN EXECUTOR CLASS
# =============================================================================

class DGDTLUnifiedExecutor:
    def __init__(self):
        self.deployment_config = ProductionConfig()
        self.config = {}
        self.data = {}
        self.dfs = {}
        self.model = None
        self.stats = {'x': None, 'y': None}
        self.feature_formulas = []
        self.base_feature_names = []
        self.final_feature_names = []

    @staticmethod
    def _get_path(prompt: str, default_val: str) -> str:
        val = input(f"{Colors.YELLOW}{prompt} (Default: {default_val}): {Colors.ENDC}").strip()
        return val if val else default_val

    @staticmethod
    def _get_required_float(prompt: str) -> np.float64:
        while True:
            val = input(f"{Colors.YELLOW}{prompt}: {Colors.ENDC}").strip()
            if val:
                try:
                    return np.float64(val)
                except ValueError:
                    print(f"{Colors.RED}Invalid number.{Colors.ENDC}")
            else:
                print(f"{Colors.RED}Required.{Colors.ENDC}")

    @staticmethod
    def _get_required_tuple(prompt: str) -> Tuple[float, float]:
        while True:
            val = input(f"{Colors.YELLOW}{prompt}: {Colors.ENDC}").strip()
            if val:
                try:
                    return tuple(map(np.float64, val.split(',')))
                except Exception:
                    print(f"{Colors.RED}Invalid format (e.g. 0.1,0.5){Colors.ENDC}")
            else:
                print(f"{Colors.RED}Required.{Colors.ENDC}")

    def setup_config(self):
        self.config['mode'] = self.deployment_config.mode
        self.config['fit_intercept'] = self.deployment_config.fit_intercept
        self.config['beta_sum_one'] = self.deployment_config.beta_sum_one

        # Format booleans to YES/NO for the console output
        norm_x_str = "YES" if self.deployment_config.normalize_x else "NO"
        _cy = getattr(self.deployment_config, 'centre_y', False)
        norm_y_str = "NORMALIZED" if self.deployment_config.normalize_y else ("CENTRED" if _cy else "NO")


    def load_data(self):
        train_path = self.deployment_config.train_path
        valid_path = self.deployment_config.valid_path
        test_path  = self.deployment_config.test_path

        if not os.path.exists(train_path):
            sys.exit(f"{Colors.RED}Error: {train_path} not found{Colors.ENDC}")


        self.dfs['train'] = pd.read_csv(train_path)
        self.dfs['valid'] = pd.read_csv(valid_path)
        self.dfs['test']  = pd.read_csv(test_path)
        if self.dfs['train'].shape[1] < 3:
            sys.exit(f"{Colors.RED}[CRITICAL] Data violation: Must have ID, Predictor(s), and Target.{Colors.ENDC}")
        if not pd.api.types.is_numeric_dtype(self.dfs['train'].iloc[:, -1]):
            sys.exit(f"{Colors.RED}[CRITICAL] Target column (Last) must be numeric.{Colors.ENDC}")

        self.data['train'] = (self.dfs['train'].iloc[:, 1:-1].values, self.dfs['train'].iloc[:, -1].values)
        self.data['valid'] = (self.dfs['valid'].iloc[:, 1:-1].values, self.dfs['valid'].iloc[:, -1].values)
        self.data['test']  = (self.dfs['test'].iloc[:, 1:-1].values,  self.dfs['test'].iloc[:, -1].values)

        self.base_feature_names = list(self.dfs['train'].columns[1:-1])


    def configure_features(self):
        self.feature_formulas = self.deployment_config.feature_formulas
        self.final_feature_names = DataUtils.create_feature_names_from_formulas(self.base_feature_names, self.feature_formulas)

    def _prepare_data_matrix(self, df_key, x_stats=None, y_stats=None):
        X_raw, y_raw = self.data[df_key]
        X_proc = DataUtils.apply_feature_engineering(X_raw, self.feature_formulas, self.base_feature_names, x_stats)
        if self.config['mode'] == 'raw' and y_stats:
            y_proc = DataUtils.scale_target(y_raw, y_stats)
        else:
            y_proc = y_raw
        return X_proc, y_proc, y_raw

    # =========================================================================
    # INTERACTIVE FLOW
    # -------------------------------------------------------------------------
    # Collects user input into the shared ProductionConfig. Both the
    # Interactive and Deployment Guide (.txt) modes then follow the same
    # execution pipeline, ensuring identical results for equivalent inputs.
    # =========================================================================

    def _interactive_basic_config(self):
        print(f"\n{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}       DGDTL UNIFIED EXECUTOR — INTERACTIVE MODE       {Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")

        mode_in = input(f"{Colors.YELLOW}Mode [raw / error_matrix] (Default: raw): {Colors.ENDC}").strip().lower()
        self.deployment_config.mode = 'error_matrix' if mode_in == 'error_matrix' else 'raw'

        intercept_in = input(f"{Colors.YELLOW}Use Intercept? [y/n] (Default: y): {Colors.ENDC}").strip().lower()
        self.deployment_config.fit_intercept = not (intercept_in == 'n')

        beta_sum_in = input(f"{Colors.YELLOW}Beta Sum to 1 Constraint? [y/n] (Default: n): {Colors.ENDC}").strip().lower()
        self.deployment_config.beta_sum_one = (beta_sum_in == 'y')

        print(f"{Colors.GREEN}>> Config: Mode={self.deployment_config.mode.upper()}, "
              f"Intercept={self.deployment_config.fit_intercept}, BetaSum={self.deployment_config.beta_sum_one}{Colors.ENDC}")

        self.deployment_config.train_path = self._get_path("Train Data Path", "data_train.csv")
        self.deployment_config.valid_path = self._get_path("Validation Data Path", "data_valid.csv")
        self.deployment_config.test_path  = self._get_path("Test Data Path", "data_test.csv")
        self.deployment_config.output_dir = self._get_path("Output Directory", "results")
        self.deployment_config._source_file = "interactive"

    def _interactive_feature_config(self):
        print(f"{Colors.CYAN}--- Feature Engineering ---{Colors.ENDC}")
        print(f"{Colors.BOLD}Base Predictors:{Colors.ENDC} {self.base_feature_names}\n")

        formulas = []
        if input(f"{Colors.YELLOW}Add non-linear features? [y/n] (Default: n): {Colors.ENDC}").lower() == 'y':
            print("Examples: 'ColA * ColB'; 'ColC ** 2'")
            print("Separate multiple formulas with semicolons (;)")
            formulas_in = input(f"{Colors.YELLOW}Formulas: {Colors.ENDC}").strip()
            if formulas_in:
                formulas = [f.strip() for f in formulas_in.split(';')]
                print(f"{Colors.GREEN}>> Added {len(formulas)} formulas.{Colors.ENDC}")

        self.deployment_config.feature_formulas = formulas

    def _prompt_target_transform(self) -> Tuple[bool, bool, bool]:
        """
        Shared by run_diagnosis() and _interactive_training_params(): ask
        Normalize Predictors (X)?, then Normalize Target (Y)? or — only when
        it applies — Center Target (Y)? (mean-centring only).

        Centering only applies when fit_intercept=NO and mode='raw': with an
        intercept the model already absorbs E[Y] (centring would be
        redundant), and error_matrix mode does not operate on raw Y in a way
        centring is meaningful for. This is the exact same rule already
        enforced by the Deployment Guide flow (ProductionConfig.centre_y).
        Returns (use_norm, norm_y, centre_y).
        """
        use_norm, norm_y, centre_y = False, False, False
        centering_applies = (not self.config['fit_intercept']) and (self.config['mode'] == 'raw')

        if self.config['mode'] == 'raw':
            if input(f"{Colors.YELLOW}Normalize Predictors (X)? [y/n] (Default: n): {Colors.ENDC}").lower() == 'y':
                use_norm = True
                if input(f"{Colors.YELLOW}Normalize Target (Y)? [y/n] (Default: n): {Colors.ENDC}").lower() == 'y':
                    norm_y = True
                elif centering_applies:
                    if input(f"{Colors.YELLOW}Center Target (Y)? Mean-centring only, no intercept [y/n] (Default: n): {Colors.ENDC}").lower() == 'y':
                        centre_y = True

        return use_norm, norm_y, centre_y

    def run_diagnosis(self):
        print(f"\n{Colors.HEADER}--- Baseline Diagnosis ---{Colors.ENDC}")
        use_norm, norm_y, centre_y = self._prompt_target_transform()

        x_stats, y_stats = None, None
        if use_norm:
            df = self.dfs['train']
            cols = self.base_feature_names
            x_stats = {'means': df[cols].mean(), 'stds': df[cols].std(ddof=1)}
            if norm_y:
                t_col = df.columns[-1]
                y_stats = {'mean': df[t_col].mean(), 'std': df[t_col].std(ddof=1)}
            elif centre_y:
                t_col = df.columns[-1]
                y_stats = {'mean': df[t_col].mean(), 'std': 1.0}

        X_train_base, y_train_for_model, y_train_raw = self._prepare_data_matrix('train', x_stats, y_stats)
        df_comb_raw = pd.concat([self.dfs['train'], self.dfs['valid']])
        X_comb_raw_arr = df_comb_raw.iloc[:, 1:-1].values
        y_comb_raw_arr = df_comb_raw.iloc[:, -1].values
        X_comb_base = DataUtils.apply_feature_engineering(X_comb_raw_arr, self.feature_formulas, self.base_feature_names, x_stats)
        y_comb_base = DataUtils.scale_target(y_comb_raw_arr, y_stats) if (use_norm and (norm_y or centre_y)) else y_comb_raw_arr

        print(f"{Colors.BOLD}>> Active Predictors ({len(self.final_feature_names)}):{Colors.ENDC} {self.final_feature_names}")

        temp_model_orig = DGDTLEstimator(mode=self.config['mode'], fit_intercept=self.config['fit_intercept'], beta_sum_one=self.config['beta_sum_one'], n_jobs=FIXED_N_JOBS, random_state=42)
        coeffs_orig = temp_model_orig.calibrate(X_train_base, y_train_for_model)
        mse_orig = temp_model_orig.baseline_mse_

        temp_model_retr = DGDTLEstimator(mode=self.config['mode'], fit_intercept=self.config['fit_intercept'], beta_sum_one=self.config['beta_sum_one'], n_jobs=FIXED_N_JOBS, random_state=42)
        coeffs_retr = temp_model_retr.calibrate(X_comb_base, y_comb_base)
        mse_retr = temp_model_retr.baseline_mse_

        coef_col_name = 'Coefficient_Normalized' if use_norm else 'Coefficient'
        display_feature_names = self.final_feature_names
        if self.config['fit_intercept']:
            display_feature_names = ["Intercept"] + display_feature_names

        df_coeffs = pd.DataFrame({
            'Predictor': display_feature_names,
            f'{coef_col_name}_Original': coeffs_orig,
            f'{coef_col_name}_Retrain': coeffs_retr
        })

        print(f"\n{Colors.CYAN}--- Baseline & Retraining Coefficient Diagnosis ---{Colors.ENDC}")
        print(f"Original Baseline MSE (Train Only):    {mse_orig:.6f}")
        print(f"Retraining Baseline MSE (Train+Valid): {mse_retr:.6f}\n")
        print(df_coeffs.to_string(index=False, float_format="%.6f"))
        input(f"\n{Colors.YELLOW}Press Enter to return to menu...{Colors.ENDC}")

    def _interactive_training_params(self):
        print(f"\n{Colors.HEADER}--- 2. Training Configuration ---{Colors.ENDC}")

        use_norm, norm_y, centre_y = self._prompt_target_transform()
        self.deployment_config.normalize_x = use_norm
        self.deployment_config.normalize_y = norm_y
        self.deployment_config.centre_y    = centre_y

        # Temporary statistics used only to estimate Auto-Mode bounds and
        # expected_y_std. The shared training pipeline recomputes self.stats
        # from the same data and configuration, yielding identical values.
        x_stats_tmp, y_stats_tmp = None, None
        if use_norm:
            df = self.dfs['train']
            cols = self.base_feature_names
            x_stats_tmp = {'means': df[cols].mean(), 'stds': df[cols].std(ddof=1)}
            if norm_y:
                t_col = df.columns[-1]
                y_stats_tmp = {'mean': df[t_col].mean(), 'std': df[t_col].std(ddof=1)}
                self.deployment_config.expected_y_std = float(y_stats_tmp['std'])
            elif centre_y:
                t_col = df.columns[-1]
                y_stats_tmp = {'mean': df[t_col].mean(), 'std': 1.0}

        X_train, y_train_for_model, y_train_raw = self._prepare_data_matrix('train', x_stats_tmp, y_stats_tmp)

        print(f"\n{Colors.CYAN}--- Hyperparameter Configuration ---{Colors.ENDC}")
        print(f"{Colors.BOLD}[A]utomatic Mode:{Colors.ENDC} Auto-configures bounds based on data magnitude.")
        print(f"{Colors.BOLD}[C]ustom Mode:{Colors.ENDC} Manual control of all parameters.")
        config_mode = input(f"{Colors.YELLOW}Select Mode [A/C] (Default: A): {Colors.ENDC}").strip().upper()

        bounds, int_bounds, tol_factor = (np.float64(0.1), np.float64(0.5)), (np.float64(0.1), np.float64(0.5)), 0.3

        if config_mode != 'C':
            print(f"\n{Colors.CYAN}>> Running Auto-Pilot Pre-Flight Check...{Colors.ENDC}")
            try:
                temp_est = DGDTLEstimator(mode=self.config['mode'], fit_intercept=self.config['fit_intercept'], beta_sum_one=self.config['beta_sum_one'], random_state=42, verbose=False)
                coeffs = temp_est.calibrate(X_train, y_train_for_model)
                print(f"  {Colors.BLUE}> Baseline MSE: {temp_est.baseline_mse_:.6f}{Colors.ENDC}")

                if self.config['fit_intercept']:
                    int_bounds, int_desc = Heuristics.calculate_adaptive_bounds(coeffs[0], beta_sum_one=False)
                    bounds, margin_desc = Heuristics.calculate_adaptive_bounds(coeffs[1:], self.config['beta_sum_one'])
                    print(f"  > Intercept Bounds ({int_desc}): Accepted Limits ({int_bounds[0]:.6f}, {int_bounds[1]:.6f})")
                else:
                    bounds, margin_desc = Heuristics.calculate_adaptive_bounds(coeffs, self.config['beta_sum_one'])
                    int_bounds = (0.0, 0.0)

                print(f"  > Predictor Bounds ({margin_desc}): Accepted Limits ({bounds[0]:.6f}, {bounds[1]:.6f})")
            except Exception as e:
                print(f"{Colors.RED}Auto-Config Failed: {e}. Using default bounds.{Colors.ENDC}")
                traceback.print_exc()

            # Ask the Tolerance Factor even in Automatic Mode —
            # it no longer silently defaults to 0.3.
            tol_in = input(f"{Colors.YELLOW}Tolerance Factor (Default 0.3, or -0.3 for Deep): {Colors.ENDC}").strip() or "0.3"
            tol_factor = np.float64(tol_in)
        else:
            print(f"\n{Colors.YELLOW}>>> CUSTOM MODE: Manual Configuration{Colors.ENDC}")
            bounds = self._get_required_tuple("Feature Bounds (e.g., -0.5,1.5)")
            int_bounds = bounds
            if self.config['fit_intercept']:
                int_bounds = self._get_required_tuple("Intercept Bounds (e.g., -2.0,2.0)")
            tol_in = input(f"{Colors.YELLOW}Tolerance Factor (Default 0.3, or -0.3 for Deep): {Colors.ENDC}").strip() or "0.3"
            tol_factor = np.float64(tol_in)

        self.deployment_config.coeff_bounds     = bounds
        self.deployment_config.intercept_bounds = int_bounds
        self.deployment_config.tolerance_factor = float(tol_factor)

        print(f"\n{Colors.YELLOW}>>> REQUIRED THRESHOLDS & WEIGHTS{Colors.ENDC}")
        self.deployment_config.validation_threshold = float(self._get_required_float("Validation Threshold (Required)"))
        self.deployment_config.constraint_threshold = float(self._get_required_float("Constraint Threshold (Required)"))
        self.deployment_config.diversity_weight     = float(self._get_required_float("Diversity Weight (Required)"))

    def _run_interactive_menu(self):
        while True:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.ENDC}")
            print(f"{Colors.BOLD}   DGDTL UNIFIED EXECUTOR - MAIN MENU   {Colors.ENDC}")
            print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
            print("1. Baseline Diagnosis (with Retraining Preview)")
            print("2. Run Training (Auto/Custom Configuration)")
            print("3. Exit")

            opt = input(f"\n{Colors.YELLOW}Select Option [1-3]: {Colors.ENDC}").strip()

            try:
                if opt == '1':
                    self.run_diagnosis()
                elif opt == '2':
                    self._interactive_training_params()
                    self.execute_training()
                elif opt == '3':
                    print(f"\n{Colors.CYAN}Exiting DGDTL Unified Executor. Goodbye!{Colors.ENDC}")
                    sys.exit(0)
                else:
                    print(f"{Colors.RED}Invalid selection. Please try again.{Colors.ENDC}")
            except Exception as e:
                print(f"\n{Colors.RED}An error occurred in option {opt}:{Colors.ENDC}")
                traceback.print_exc()
                input(f"{Colors.YELLOW}Press Enter to return to menu...{Colors.ENDC}")

    def execute_training(self):
        _div = "─" * 58
        norm_x_str = "YES" if self.deployment_config.normalize_x else "NO"
        _cy = getattr(self.deployment_config, 'centre_y', False)
        norm_y_str = "NORMALIZED" if self.deployment_config.normalize_y else ("CENTRED" if _cy else "NO")
        intercept_str = "YES" if self.config["fit_intercept"] else "NO"
        betasum_str   = "YES" if self.config["beta_sum_one"]   else "NO"
        n_train = len(self.dfs["train"]); n_valid = len(self.dfs["valid"]); n_test = len(self.dfs["test"])
        feat_str = ", ".join(self.final_feature_names) + f" ({len(self.final_feature_names)} total)"
        print(f"")
        print(f"[CONFIG] Deployment guide   : {getattr(self.deployment_config, '_source_file', 'deployment guide')}")
        print(f"[CONFIG] Mode               : {self.config['mode'].upper()} | Intercept: {intercept_str} | BetaSum: {betasum_str}")
        print(f"[CONFIG] Normalize X/Y      : {norm_x_str} / {norm_y_str}")
        print(f"[CONFIG] Features           : {feat_str}")
        print(f"[CONFIG] Train/Valid/Test   : {n_train} / {n_valid} / {n_test} samples")
        print(f"\n{Colors.CYAN}{_div}{Colors.ENDC}")
        print(f"{Colors.BOLD}PHASE 1 — BASELINE CALIBRATION{Colors.ENDC}")
        print(f"{Colors.CYAN}{_div}{Colors.ENDC}")

        use_norm = self.deployment_config.normalize_x
        norm_y = self.deployment_config.normalize_y
        centre_y = getattr(self.deployment_config, 'centre_y', False)

        self.stats = {'x': None, 'y': None}
        if use_norm:
            df = self.dfs['train']
            cols = self.base_feature_names
            self.stats['x'] = {'means': df[cols].mean(), 'stds': df[cols].std(ddof=1)}
            if norm_y:
                t_col = df.columns[-1]
                self.stats['y'] = {'mean': df[t_col].mean(), 'std': df[t_col].std(ddof=1)}
                print(f"[OK] Target transform        : standardized (zero mean, unit variance)")
                y_std_calc = self.stats['y']['std']
                if abs(y_std_calc - self.deployment_config.expected_y_std) <= 1e-4:
                    print(f"[OK] Y std verified          : {self.deployment_config.expected_y_std:.6f}")
                else:
                    print(f"{Colors.YELLOW}[WARNING] Target Y standard deviation ({y_std_calc:.6f}) differs from deployment guide ({self.deployment_config.expected_y_std:.6f}).{Colors.ENDC}")
            elif centre_y:
                # Mean-centring only: no intercept => model cannot absorb E[Y].
                # std=1.0 preserves natural Y units; scale_factor=1.0.
                t_col = df.columns[-1]
                self.stats['y'] = {'mean': df[t_col].mean(), 'std': 1.0}
                print(f"[OK] Target transform        : mean-centred (zero mean, natural scale)")

        X_train, y_train_for_model, y_train_raw = self._prepare_data_matrix('train', self.stats['x'], self.stats['y'])
        X_valid, y_valid_for_model, y_valid_raw = self._prepare_data_matrix('valid', self.stats['x'], self.stats['y'])

        bounds = self.deployment_config.coeff_bounds
        int_bounds = self.deployment_config.intercept_bounds
        if not self.config['fit_intercept']:
            int_bounds = None 
        tol_factor = self.deployment_config.tolerance_factor
        val_thresh = self.deployment_config.validation_threshold
        con_thresh = self.deployment_config.constraint_threshold
        div_w = self.deployment_config.diversity_weight

        np.random.seed(42) 
        temp_baseline_model = DGDTLEstimator(
            mode=self.config['mode'],
            fit_intercept=self.config['fit_intercept'],
            beta_sum_one=self.config['beta_sum_one'],
            random_state=42,
            verbose=False,
            n_jobs=FIXED_N_JOBS
        )
        unbounded_coeffs = temp_baseline_model.calibrate(X_train, y_train_for_model)
        unbounded_mse    = temp_baseline_model.baseline_mse_
        print(f"[OK] Independent Baseline MSE: {unbounded_mse:.6f}")


        self.model = DGDTLEstimator(
            mode=self.config['mode'], TOLERANCE_FACTOR=tol_factor, VALIDATION_THRESHOLD=val_thresh,
            constraint_threshold=con_thresh, diversity_weight=div_w, coeff_bounds=bounds,
            intercept_bounds=int_bounds, num_solutions_run1=1000, num_solutions_run2=1000,
            fit_intercept=self.config['fit_intercept'], beta_sum_one=self.config['beta_sum_one'],
            n_jobs=FIXED_N_JOBS, random_state=42
        )

        self.model.baseline_mse_         = unbounded_mse
        self.model.baseline_coeffs_      = unbounded_coeffs
        self.model._baseline_calculated  = True

        if self.config['mode'] == 'raw' and self.stats['y']:
            y_std = self.stats['y']['std']
            if y_std != 1.0:
                # NORMALIZED: guide writes thresholds in natural scale → divide
                # back to model scale (unit-variance space).
                print(f"[OK] Threshold scaling   : natural -> model scale (Y_std={y_std:.6f})")
                self.model.VALIDATION_THRESHOLD /= y_std
                self.model.constraint_threshold  /= y_std
            else:
                # CENTRED: std=1.0 => natural scale == model scale; no scaling.
                print(f"[OK] Threshold scaling   : none (mean-centred, std=1.0, natural scale)")

        start_time = time.time()
        print(f"\n{Colors.CYAN}{_div}{Colors.ENDC}")
        print(f"{Colors.BOLD}PHASE 2 — SEARCH  (n_jobs={FIXED_N_JOBS}, seed=42){Colors.ENDC}")
        print(f"{Colors.CYAN}{_div}{Colors.ENDC}")

        search_failed = False
        try:
            np.random.seed(42)
            self.model.fit(X_train, y_train_for_model, X_valid, y_valid_for_model)

            if getattr(self.model, 'baseline_coeffs_', None) is not None:
                beta_baseline = self.model.baseline_coeffs_
                
                X_comb_raw = np.vstack((X_train, X_valid))
                y_comb_for_model = np.concatenate((y_train_for_model, y_valid_for_model))
                y_comb_raw = np.concatenate((y_train_raw, y_valid_raw))
                
                if self.config['fit_intercept']:
                    X_tr_ev = np.hstack([np.ones((X_train.shape[0], 1)), X_train])
                    X_vl_ev = np.hstack([np.ones((X_valid.shape[0], 1)), X_valid])
                    X_cb_ev = np.hstack([np.ones((X_comb_raw.shape[0], 1)), X_comb_raw])
                else:
                    X_tr_ev = X_train
                    X_vl_ev = X_valid
                    X_cb_ev = X_comb_raw
                    
                y_tr_pred = X_tr_ev @ beta_baseline
                y_vl_pred = X_vl_ev @ beta_baseline
                if self.config['mode'] == 'raw' and self.stats['y']:
                    y_tr_pred = DataUtils.unscale_predictions(y_tr_pred, self.stats['y'])
                    y_vl_pred = DataUtils.unscale_predictions(y_vl_pred, self.stats['y'])
                    
                err_t = np.abs(y_tr_pred - y_train_raw)
                err_v = np.abs(y_vl_pred - y_valid_raw)
                
                p97_t = np.percentile(err_t, 97.5)
                p97_v = np.percentile(err_v, 97.5)
                p97_train_metric = max(p97_t, p97_v)
                max_train_real = max(np.max(err_t), np.max(err_v))
                
                temp_model_retr = DGDTLEstimator(
                    mode=self.config['mode'], fit_intercept=self.config['fit_intercept'], 
                    beta_sum_one=self.config['beta_sum_one'], n_jobs=FIXED_N_JOBS, random_state=42
                )
                retrain_coeffs = temp_model_retr.calibrate(X_comb_raw, y_comb_for_model)
                
                y_cb_pred = X_cb_ev @ retrain_coeffs
                if self.config['mode'] == 'raw' and self.stats['y']:
                    y_cb_pred = DataUtils.unscale_predictions(y_cb_pred, self.stats['y'])
                    
                err_retrain = np.abs(y_cb_pred - y_comb_raw)
                p97_retrain_metric = np.percentile(err_retrain, 97.5)
                max_retrain_real = np.max(err_retrain)
                
                tau_anchor = round(min(p97_train_metric, p97_retrain_metric), 6)
                e_max = max(max_train_real, max_retrain_real)
                e_gm = round(np.sqrt(tau_anchor * e_max), 6)
                
                p50_train = float(np.percentile(err_t, 50))
                min_thickness = max(tau_anchor - p50_train, 1e-9)
                delta_eff = max(e_gm - tau_anchor, min_thickness)
                
                def phi_emp_fn(errors_abs):
                    if len(errors_abs) == 0: return 0.0, 0.0
                    idx_95 = int(0.95 * len(errors_abs))
                    cvar_95 = np.mean(np.sort(errors_abs)[idx_95:]) if idx_95 < len(errors_abs) else np.max(errors_abs)
                    excess = max(0.0, (cvar_95 - tau_anchor) / delta_eff)
                    return excess, np.exp(-excess**2)
                    
                def compute_run_metrics(c_dict):
                    if not c_dict: return 0.0, 0.0
                    c_beta = np.asarray(c_dict['coeffs'])
                    y_cb_c = X_cb_ev @ c_beta
                    
                    if self.config['mode'] == 'raw' and self.stats['y']:
                        y_cb_c = DataUtils.unscale_predictions(y_cb_c, self.stats['y'])
                        scale = self.stats['y']['std']
                        mae_v = c_dict.get('MAE_vldt', 0.0) * scale
                        mse_v = c_dict.get('MSE_vldt', 0.0) * (scale**2)
                    else:
                        mae_v = c_dict.get('MAE_vldt', 0.0)
                        mse_v = c_dict.get('MSE_vldt', 0.0)
                        
                    err_comb_c = np.abs(y_cb_c - y_comb_raw)
                    p_emp, _ = phi_emp_fn(err_comb_c)
                    e_val = np.sqrt(mae_v * np.sqrt(mse_v))
                    return p_emp, e_val

                phi_r1, eval_r1 = compute_run_metrics(getattr(self.model, 'champion_run1_', None))
                phi_r2, eval_r2 = compute_run_metrics(getattr(self.model, 'champion_run2_', None))
                
                self.model._phi_emp_r1 = phi_r1
                self.model._phi_emp_r2 = phi_r2
                self.model._e_val_r1   = eval_r1
                self.model._e_val_r2   = eval_r2

        except RuntimeError as e:
            if "No solutions found" in str(e):
                print(f"\n{Colors.RED}>> Core Error: {e}{Colors.ENDC}")
                search_failed = True
            else:
                raise e

        end_time = time.time()
        training_duration_minutes = (end_time - start_time) / 60.0
        if not search_failed:
            print(f"[OK] Search completed in {training_duration_minutes:.2f} min")

        if not search_failed and getattr(self.model, 'champion_run1_', None):
            X_test_eval, _, y_test_raw = self._prepare_data_matrix('test', self.stats['x'], self.stats['y'])
            y_pred_sc = self.model.predict(X_test_eval, y_reference=y_test_raw if self.config['mode'] == 'error_matrix' else None)
            y_pred = DataUtils.unscale_predictions(y_pred_sc, self.stats['y']) if self.stats['y'] else y_pred_sc



        else:
            print(f"\n{Colors.RED}No valid solutions were found during the exploration phase.{Colors.ENDC}")

        out_dir = self.deployment_config.output_dir
        if not os.path.exists(out_dir): os.makedirs(out_dir)

        print(f"\n{Colors.CYAN}{_div}{Colors.ENDC}")
        print(f"{Colors.BOLD}PHASE 3 — PERFORMANCE SUMMARY{Colors.ENDC}")
        print(f"{Colors.CYAN}{_div}{Colors.ENDC}")

        import io as _io
        _perf_saved_lines = []
        if VISUALS_AVAILABLE and rp:
            base_names_pre = list(self.dfs["train"].columns[1:-1])
            feature_names_pre = DataUtils.create_feature_names_from_formulas(base_names_pre, self.feature_formulas) if self.feature_formulas else base_names_pre
            if self.model.fit_intercept:
                feature_names_pre = ["Intercept"] + feature_names_pre
            coef_col_pre = "Coefficient_Normalized" if self.stats["x"] is not None else "Coefficient"
            is_norm_pre  = self.stats["x"] is not None
            y_norm_pre   = self.stats["y"] is not None
            for _rn, _champ in [("Run1", getattr(self.model, "champion_run1_", None)),
                                 ("Run2", getattr(self.model, "champion_run2_", None))]:
                if not _champ:
                    continue
                _tag_pre = f"DGDTL_Champion_Conceptual_{_rn}"
                _datasets_pre = {
                    "Training":      self.dfs["train"],
                    "Validation":    self.dfs["valid"],
                    "Testing":       self.dfs["test"],
                    "Train+Valid":   pd.concat([self.dfs["train"], self.dfs["valid"]]),
                    "Valid+Testing": pd.concat([self.dfs["valid"], self.dfs["test"]]),
                }
                _mets_pre = []
                for _n, _df in _datasets_pre.items():
                    _X, _y = _df.iloc[:, 1:-1].values, _df.iloc[:, -1].values
                    _Xe = DataUtils.apply_feature_engineering(_X, self.feature_formulas, base_names_pre, self.stats["x"]) if self.feature_formulas else (DataUtils.scale_predictors(pd.DataFrame(_X, columns=base_names_pre), self.stats["x"]) if is_norm_pre else _X)
                    _ypm = self.model.predict(_Xe, y_reference=_y if self.config["mode"] == "error_matrix" else None, beta=_champ["coeffs"])
                    _yp  = DataUtils.unscale_predictions(_ypm, self.stats["y"]) if is_norm_pre and y_norm_pre else _ypm
                    _mets_pre.append({"Dataset": _n, "R²": r2_score(_y, _yp), "MAE": mean_absolute_error(_y, _yp), "MSE": mean_squared_error(_y, _yp), "MaxErr": np.max(np.abs(_yp - _y))})
                _m_by_ds_pre = {m["Dataset"]: m for m in _mets_pre}
                _params_pre  = self.model.get_params().copy()
                if y_norm_pre and self.stats["y"]:
                    _ystd = self.stats["y"].get("std", 1.0)
                    if _params_pre.get("constraint_threshold") is not None: _params_pre["constraint_threshold"] *= _ystd
                    if _params_pre.get("VALIDATION_THRESHOLD")  is not None: _params_pre["VALIDATION_THRESHOLD"]  *= _ystd
                _buf_pre = _io.StringIO()
                _rs = sys.stdout; sys.stdout = _buf_pre
                try:
                    rp.generate_performance_report(_tag_pre, _params_pre, pd.DataFrame({"Predictor": feature_names_pre, coef_col_pre: _champ["coeffs"]}), _m_by_ds_pre, os.path.join(out_dir, f"{_tag_pre}_Performance_Metrics"), x_normalized=is_norm_pre, y_normalized=y_norm_pre, duration_minutes=training_duration_minutes)
                finally:
                    sys.stdout = _rs
                for _ln in _buf_pre.getvalue().splitlines():
                    if "Performance metrics report saved to:" in _ln:
                        _perf_saved_lines.append(_ln)
                    else:
                        print(_ln)

        print(f"\n{Colors.CYAN}{_div}{Colors.ENDC}")
        print(f"{Colors.BOLD}PHASE 4 — REPORT GENERATION  →  {out_dir}/{Colors.ENDC}")
        print(f"{Colors.CYAN}{_div}{Colors.ENDC}")

        generate_comprehensive_reports(self.model, out_dir, self.dfs, self.config["mode"], self.stats["x"], self.stats["y"], self.feature_formulas, training_duration_minutes, _perf_saved_lines)

    def run(self):
        print(f"\n{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}   DGDTL UNIFIED EXECUTOR v2.0.0{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print("1. Deployment Guide (.txt) — automated")
        print("2. Interactive Configuration — manual")
        entry_mode = input(f"\n{Colors.YELLOW}Select Input Mode [1/2] (Default: 1): {Colors.ENDC}").strip()

        if entry_mode == '2':
            self._interactive_basic_config()
            self.setup_config()
            self.load_data()
            self._interactive_feature_config()
            self.configure_features()

            self._run_interactive_menu()
        else:
            txt_path = input(f"\n{Colors.YELLOW}Enter the path to the Deployment Guide (.txt): {Colors.ENDC}").strip()
            if not os.path.exists(txt_path):
                sys.exit(f"{Colors.RED}Error: Deployment guide file '{txt_path}' not found.{Colors.ENDC}")

            self.deployment_config = parse_deployment_guide(txt_path)
            self.deployment_config._source_file = os.path.basename(txt_path)

            self.setup_config()
            self.load_data()
            self.configure_features()

            self.execute_training()

            print(f"\n{Colors.CYAN}{'='*60}{Colors.ENDC}")
            print(f"{Colors.GREEN}[SUCCESS] All reports generated. Exiting.{Colors.ENDC}")
            print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")

# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    try:
        executor = DGDTLUnifiedExecutor()
        executor.run()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Process interrupted by user.{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}A critical error occurred outside the main loop:{Colors.ENDC}")
        traceback.print_exc()
        sys.exit(1)
