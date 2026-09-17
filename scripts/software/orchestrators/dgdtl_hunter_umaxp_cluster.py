# SPDX-FileCopyrightText: 2026 José A. Pérez
# SPDX-License-Identifier: MIT

"""
DGDTL-LTS Hunter
U-MaxP Integrated Hyperparameter-Search Orchestrator
====================================================

Abstract:
---------
Hunter implements the automated hyperparameter-search architecture of the
DGDTL-LTS framework. It coordinates deterministic exploration of the
hyperparameter space through Scout, Diagnosis, Siege, and GM-valve stages,
while using the DGDTL-LTS motor to generate candidate solution states and
the U-MaxP motor to evaluate their structural admissibility.

The orchestrator controls the search strategy, candidate generation,
progression across Scout levels and STRICT/EXPANDED operating regimes,
intra-Siege candidate resolution, and final structural evaluation through
the reference Structural Selection Protocol.

Key Architectural Features:
---------------------------
1. DGDTL-LTS Integration
   Instantiates the DGDTL-LTS optimization motor for each hyperparameter
   configuration and obtains the Run 1 exploration and Run 2 topological
   refinement candidate states.

2. U-MaxP-Driven Hyperparameter Search
   Uses the U-MaxP criterion as the structural objective guiding Optuna/TPE
   exploration while preserving the distinction between search-time U-MaxP
   and post-hoc certified U-MaxP_k evaluation.

3. Hierarchical Search Architecture
   Executes the Scout, Diagnosis, Siege, and GM-valve stages through
   deterministic search-space definitions, seeded TPE exploration, warm
   starts, and controlled progression across search levels.

4. Conditioned Micro-Arbitration
   Resolves stochastic-equivalence pools at the intra-Siege level through
   the U-MaxP Micro-Arbitration protocol before promoting a trial-level
   representative.

5. Structural Selection & Certification
   Supplies the accumulated candidate states to the reference Structural
   Selection Protocol for deterministic inter-candidate arbitration,
   validation-bias analysis, and final observable certification.

6. Reproducible Execution
   Enforces fixed random seeds, controlled numerical threading, deterministic
   candidate ordering, and fixed search logic to preserve reproducibility
   within and across supported computational environments.

Sections:
---------
1. Global Configuration
2. Data Utilities & Configuration
3. Baseline Evaluation
4. Optimization Orchestrator
   - Scout
   - Diagnosis
   - Siege
   - GM Valve
5. Hunter Reporting
6. Structural Selection Integration
7. Final Framework Audit
8. Main Application

Usage:
------
Hunter is the hyperparameter-search orchestrator of the DGDTL-LTS
implementation. Given training and internal-validation data, it explores
the configured hyperparameter space, generates DGDTL-LTS candidate states,
evaluates them through U-MaxP, and applies the reference Structural
Selection Protocol to obtain the final certified result.

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

# --- CRITICAL REPRODUCIBILITY SETTINGS ---
os.environ['PYTHONHASHSEED'] = '0'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['VECLIB_MAXIMUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

import multiprocessing
import sys
import time
import warnings
import traceback
import re
import numpy as np
import pandas as pd
import argparse
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any, Union


try:
    from dgdtl_lts import DGDTLEstimator
except ImportError:
    sys.exit("CRITICAL ERROR: package 'dgdtl-lts' (import 'dgdtl_lts') not found.")

try:
    from u_maxp import (
        TopologicalEngine, EVTAnalyzer, ConsistencyEngine, MicroArbitration,
        UMaxPCriterion, StructuralSelectionProtocol,
        ProtocolConfig, ProtocolVerdictCodes
    )
except ImportError:
    sys.exit("CRITICAL ERROR: package 'u-maxp' (import 'u_maxp') not found.")

try:
    from dgdtl_reporting import (Colors as _ColorsExt,
                                  TerminalLogger as _TLExt)
    _REPORTING_AVAILABLE = True
except ImportError:
    _REPORTING_AVAILABLE = False

warnings.filterwarnings('ignore')
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

try:
    import optuna
    from optuna.samplers import TPESampler
    optuna.logging.set_verbosity(optuna.logging.ERROR) 
except ImportError:
    sys.exit("CRITICAL ERROR: 'optuna' missing. Install with: pip install optuna")

# =============================================================================
# GLOBAL CONFIGURATION
# =============================================================================
TRAIN_PATH = "data_train.csv"
VALID_PATH = "data_valid.csv"
OUTPUT_DIR = "results_hunter_umaxp_cluster"

N_TRIALS_SCOUT = 25   
N_TRIALS_SIEGE = 50   
ERROR_PERCENTILE = 97.5
GAP_SEEDS = [0.00, 0.05, 0.10, 0.20, 0.30]

try: FIXED_N_JOBS = max(1, multiprocessing.cpu_count())
except (NotImplementedError, AttributeError): FIXED_N_JOBS = 4

FrameworkConfig = ProtocolConfig
VerdictCodes = ProtocolVerdictCodes

if _REPORTING_AVAILABLE:
    Colors         = _ColorsExt
    TerminalLogger = _TLExt
else:
    class Colors:
        HEADER, BLUE, CYAN, GREEN, YELLOW, RED, ENDC, BOLD = '\033[95m', '\033[94m', '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[0m', '\033[1m'

    class TerminalLogger:
        @staticmethod
        def title(*args, **kwargs): pass
        @staticmethod
        def section(*args, **kwargs): pass
        @staticmethod
        def info(*args, **kwargs): pass
        @staticmethod
        def warning(*args, **kwargs): pass
        @staticmethod
        def success(*args, **kwargs): pass
        @staticmethod
        def error(*args, **kwargs): pass

# =============================================================================
# DATA UTILITIES & CLASSES
# =============================================================================

class DataUtils:
    @staticmethod
    def scale_predictors(data: pd.DataFrame, stats: Dict) -> pd.DataFrame:
        means, stds = stats['means'].to_numpy(), stats['stds'].to_numpy()
        stds = np.where(stds == 0, 1.0, stds)
        return (data - means) / stds

    @staticmethod
    def scale_target(target: np.ndarray, stats: Dict) -> np.ndarray:
        return (target - stats['mean']) / stats['std']

    @staticmethod
    def create_feature_names_from_formulas(base_names: List[str], formulas: List[str]) -> List[str]:
        return base_names + [f.replace(' ', '').replace('**', '_pow_').replace('*', '_x_') for f in formulas]

    @staticmethod
    def apply_feature_engineering(X_raw: np.ndarray, formulas: List[str], base_feature_names: List[str], x_stats: Optional[Dict] = None) -> np.ndarray:
        df_source = pd.DataFrame(X_raw, columns=base_feature_names)
        eval_df = pd.DataFrame(DataUtils.scale_predictors(df_source, x_stats), columns=base_feature_names) if x_stats else df_source
        
        new_features_list = []
        for formula in formulas:
            try:
                new_feature = eval_df.eval(formula, engine='python')
                new_features_list.append(new_feature.values.reshape(-1, 1))
            except Exception as e:
                raise ValueError(f"Error evaluating formula '{formula}': {e}")

        final_X = np.hstack([eval_df.values] + new_features_list) if new_features_list else eval_df.values
        if not np.isfinite(final_X).all(): raise ValueError("Feature Engineering produced Infinite/NaN values.")
        return final_X

@dataclass
class HunterConfig:
    mode: str; fit_intercept: bool; beta_sum_one: bool; custom_formulas: List[str]
    feature_names: List[str]; stats_x: Optional[Dict]; stats_y: Optional[Dict]; y_std: float

@dataclass
class BaselineMetrics:
    base_mse_raw: float; base_mse: float; base_coeffs: np.ndarray; retrain_coeffs: np.ndarray
    sde_train: float; sde_retrain: float; baseline_mae_train: float; baseline_mae_val: float
    max_train_real: float; max_retrain_real: float; p97_train_metric: float; p97_retrain_metric: float
    mse_retrain: float; mae_retrain: float; truth_anchor: float; ref_int: float; ref_feats: np.ndarray
    e_gm: float; ref_mse_active: float; fixed_fb: Tuple[float, float]; fixed_ib: Optional[Tuple[float, float]]
    base_mse_train: float; base_mse_val: float; base_mse_nat: float; baseline_mae_train_nat: float
    baseline_mae_val_nat: float; base_mse_train_nat: float; base_mse_val_nat: float; mse_retrain_nat: float
    mae_retrain_nat: float; mae_type: str; outlier_pct: float; base_gci_train: float; base_gci_retrain: float
    base_u_train_raw: float; base_u_retrain_raw: float; base_u_train_map: float; base_u_retrain_map: float
    a_emp_train: float; a_emp_retrain: float; phi_emp_train: float; phi_emp_retrain: float
    emax_robusto_train: float; emax_robusto_retrain: float; min_thickness: float

@dataclass
class ScoutRecord:
    label: str; loop_id: int; scout_level: int; is_gm: bool; verdict_r1: str; verdict_r2: str
    mae_r1: float; mae_r2: float; mse_r1: float; mse_r2: float; mae_tr_r1: float; mae_tr_r2: float
    mse_tr_r1: float; mse_tr_r2: float; max_err_r1: float; max_err_r2: float
    sde_r1: float; sde_r2: float; gci_r1: float; gci_r2: float; u_r1: float; u_r2: float
    a_emp_r1: float; a_emp_r2: float; phi_emp_r1: float; phi_emp_r2: float; emax_rob_r1: float; emax_rob_r2: float
    coeffs_r1: list; coeffs_r2: list; ambition: float; gap: float; threshold_train: float
    threshold_valid: float; anchor_used: float; trial_number: int; elapsed: str

class AdaptiveBounds:
    @staticmethod
    def calculate(coeffs: Union[np.ndarray, float], beta_sum_one: bool) -> Tuple[float, float]:
        coeffs_arr = np.atleast_1d(coeffs)
        max_val, min_val, abs_max = float(np.max(coeffs_arr)), float(np.min(coeffs_arr)), float(np.max(np.abs(coeffs_arr)))
        if beta_sum_one:
            if min_val >= -1e-5: 
                f_low, f_up = max(min_val * 0.5, 0.001), min(max_val * 1.5, 0.999)
                if f_up <= f_low: f_low, f_up = 0.001, 0.999
                return (round(f_low, 6), round(f_up, 6))
            else:
                return (round(np.floor(min_val - max(abs(min_val)*0.5, 0.5)*100)/100, 6), round(np.ceil(max_val + max(abs(max_val)*0.5, 0.5)*100)/100, 6))
        else:
            bm = 1.5 if abs_max < 10 else (5.0 if abs_max < 100 else (10.0 if abs_max < 1000 else 100.0))
            if coeffs_arr.size == 1: return (round(np.floor((coeffs_arr[0]-bm)*10)/10, 6), round(np.ceil((coeffs_arr[0]+bm)*10)/10, 6))
            eff_m = bm if abs_max >= 1.0 else (abs_max * 0.5)
            if min_val >= 0: return (round(-0.1 if min_val <= 0.1 else min_val*0.5, 6), round(max_val*1.5 if max_val < 1.0 else max_val+bm, 6))
            elif max_val <= 0: return (round(min_val*1.5 if abs(min_val)<1.0 else min_val-bm, 6), round(0.1 if abs(max_val)<=0.1 else max_val*0.5, 6))
            else: return (round(np.floor((min_val-eff_m)*100)/100, 6), round(np.ceil((max_val+eff_m)*100)/100, 6))


# =============================================================================
# DATA ENVIRONMENT & AUTOMATED CLUSTER SETUP
# =============================================================================

class ClusterSetup:
    @staticmethod
    def run(df_train: pd.DataFrame, base_feature_names: List[str], target_name: str, args: argparse.Namespace) -> HunterConfig:
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*80}\nCLUSTER AUTOMATED CONFIGURATION\n{'='*80}{Colors.ENDC}")
        
        mode = args.mode
        fit_intercept = not args.no_intercept
        beta_sum_one = args.beta_sum_one
        custom_formulas = args.formulas if args.formulas else []
        
        feature_names = DataUtils.create_feature_names_from_formulas(base_feature_names, custom_formulas)        
        
        stats_x = {'means': df_train[base_feature_names].mean(), 'stds': df_train[base_feature_names].std(ddof=1)} if not args.no_norm_x else None
        
        stats_y = None
        y_std  = df_train[target_name].std(ddof=1) if mode == 'raw' else 1.0
        y_mean = df_train[target_name].mean()

        if mode == 'raw' and args.norm_y:
            stats_y = {'mean': y_mean, 'std': y_std}
        elif mode == 'raw' and not fit_intercept and not args.norm_y:
            stats_y = {'mean': y_mean, 'std': 1.0}

        _y_transform = (
            "standardized (zero mean, unit variance)"
            if (mode == 'raw' and args.norm_y)
            else ("mean-centred (zero mean, natural scale)"
                  if (mode == 'raw' and not fit_intercept and not args.norm_y)
                  else "none (natural scale)")
        )

        print(f"  {Colors.GREEN}✓ Mode               : {mode.upper()}{Colors.ENDC}")
        print(f"  {Colors.GREEN}✓ Fit Intercept      : {fit_intercept}{Colors.ENDC}")
        print(f"  {Colors.GREEN}✓ Beta Sum=1         : {beta_sum_one}{Colors.ENDC}")
        print(f"  {Colors.GREEN}✓ Predictor Scaling  : {'enabled' if stats_x is not None else 'disabled'}{Colors.ENDC}")
        print(f"  {Colors.GREEN}✓ Target Transform   : {_y_transform}{Colors.ENDC}")
        print(f"  {Colors.GREEN}✓ Feature Engineering: {len(custom_formulas)} formula(s){Colors.ENDC}")

        return HunterConfig(mode, fit_intercept, beta_sum_one, custom_formulas, feature_names, stats_x, stats_y, y_std)

class DataEnvironment:
    def __init__(self, df_train: pd.DataFrame, df_valid: pd.DataFrame, base_feature_names: List[str], target_name: str, config: HunterConfig):
        self.config = config
        self.base_feature_names = base_feature_names
        self.target_name = target_name
        self.X_t, self.y_t = self._prepare_data(df_train)
        self.X_v, self.y_v = self._prepare_data(df_valid)

    def _prepare_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        X_raw, y_raw = df[self.base_feature_names].values, df[self.target_name].values
        X = DataUtils.apply_feature_engineering(X_raw, self.config.custom_formulas, self.base_feature_names, self.config.stats_x)
        y = DataUtils.scale_target(y_raw, self.config.stats_y) if self.config.stats_y else y_raw
        return X, y


# =============================================================================
# BASELINE EVALUATOR
# =============================================================================

class BaselineEvaluator:
    @staticmethod
    def calculate(env: DataEnvironment, config: HunterConfig) -> BaselineMetrics:
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*80}\nESTABLISHING INDEPENDENT BASELINE (CORE DELEGATED)\n{'='*80}{Colors.ENDC}")
        
        model = DGDTLEstimator(
            mode=config.mode, fit_intercept=config.fit_intercept,
            beta_sum_one=config.beta_sum_one, random_state=RANDOM_SEED,
            verbose=False, n_jobs=FIXED_N_JOBS
        )
        
        base_coeffs = model.calibrate(env.X_t, env.y_t)
        base_mse_raw = float(model.baseline_mse_)
        base_mse = round(base_mse_raw, 6)
        _sf  = config.stats_y['std'] if config.stats_y else 1.0
        _sf2 = _sf ** 2
        
        p_b_t = model.predict(env.X_t, beta=base_coeffs) if config.mode == 'raw' else model.predict(env.X_t, y_reference=env.y_t, beta=base_coeffs)
        p_b_v = model.predict(env.X_v, beta=base_coeffs) if config.mode == 'raw' else model.predict(env.X_v, y_reference=env.y_v, beta=base_coeffs)
        
        err_t, err_v = np.abs(env.y_t - p_b_t), np.abs(env.y_v - p_b_v)
        err_comb = np.concatenate((err_t, err_v))
        N_tot = len(err_comb)
        
        q1, q3 = np.percentile(err_comb, 25), np.percentile(err_comb, 75)
        iqr = q3 - q1
        tukey_limit = q3 + 1.5 * iqr
        
        outliers_count = int(np.sum(err_comb > tukey_limit))
        outlier_pct = (outliers_count / N_tot) * 100.0
        min_required_outliers = max(2, int(np.ceil(N_tot * 0.05)))

        if outliers_count >= min_required_outliers:
            mae_type = 'median'
            agg_func = np.median
            print(f" {Colors.YELLOW}{Colors.BOLD}  >> DYNAMIC ERROR SELECTOR: MEDIAN (Triggered: {outliers_count} outliers / Min Required: {min_required_outliers}){Colors.ENDC}")
        else:
            mae_type = 'mean'
            agg_func = np.mean
            print(f" {Colors.GREEN}{Colors.BOLD}  >> DYNAMIC ERROR SELECTOR: MEAN (Stable: {outliers_count} outliers / Min Required: {min_required_outliers}){Colors.ENDC}")
        
        p97_t = np.percentile(err_t, ERROR_PERCENTILE)
        p97_v = np.percentile(err_v, ERROR_PERCENTILE)
        p97_train_metric = max(p97_t, p97_v)
        max_train_real = max(np.max(err_t), np.max(err_v))
        
        baseline_mae_train, baseline_mae_val = agg_func(err_t), agg_func(err_v)
        base_mse_train = round(float(np.mean(err_t ** 2)), 6)
        base_mse_val   = round(float(np.mean(err_v ** 2)), 6)

        X_comb = np.vstack((env.X_t, env.X_v))
        y_comb = np.concatenate((env.y_t, env.y_v))
        retrain_coeffs = model.calibrate(X_comb, y_comb)
        
        p_retr = model.predict(X_comb, beta=retrain_coeffs) if config.mode == 'raw' else model.predict(X_comb, y_reference=y_comb, beta=retrain_coeffs)
        err_retrain = np.abs(y_comb - p_retr)
        
        mse_retrain = round(np.mean((y_comb - p_retr)**2), 6)
        mae_retrain = agg_func(err_retrain)
        p97_retrain_metric = np.percentile(err_retrain, ERROR_PERCENTILE)
        max_retrain_real = np.max(err_retrain)
        
        truth_anchor = round(min(p97_train_metric, p97_retrain_metric), 6)
        
        N_feats = env.X_t.shape[1]
        has_int = (len(base_coeffs) == N_feats + 1)
        ref_int = base_coeffs[0] if has_int else 0.0
        ref_feats = base_coeffs[1:] if has_int else base_coeffs

        ref_mse_active = base_mse if truth_anchor == p97_train_metric else mse_retrain
        e_max = max(max_train_real, max_retrain_real)
        e_gm = round(np.sqrt(truth_anchor * e_max), 6)

        if has_int:
            fixed_ib = AdaptiveBounds.calculate(np.array([ref_int]), False)
            fixed_fb = AdaptiveBounds.calculate(ref_feats, config.beta_sum_one)
        else:
            fixed_ib = None
            fixed_fb = AdaptiveBounds.calculate(ref_feats, config.beta_sum_one)

        base_sde_train = TopologicalEngine.compute_baseline_sde_hc0(env.X_t, env.y_t, base_coeffs)
        base_sde_retrain = TopologicalEngine.compute_baseline_sde_hc0(X_comb, y_comb, retrain_coeffs)

        p50_train = float(np.percentile(err_t, 50))
        min_thickness = max(truth_anchor - p50_train, 1e-9)

        a_emp_base_tr,  phi_base_tr,  emax_rob_base_tr  = EVTAnalyzer.compute_empirical_authenticity(err_t * _sf, truth_anchor * _sf, e_gm * _sf, min_thickness * _sf)
        a_emp_base_ret, phi_base_ret, emax_rob_base_ret = EVTAnalyzer.compute_empirical_authenticity(err_retrain * _sf, truth_anchor * _sf, e_gm * _sf, min_thickness * _sf)

        base_gci_train = ConsistencyEngine.compute_gci(
            float(baseline_mae_val * _sf), round(base_mse_val * _sf2, 6),
            float(baseline_mae_train * _sf), round(base_mse_train * _sf2, 6), max_train_real * _sf,
            float(baseline_mae_val * _sf), round(base_mse_val * _sf2, 6),
            float(baseline_mae_train * _sf), round(base_mse_train * _sf2, 6), e_gm * _sf
        )
        base_gci_retrain = ConsistencyEngine.compute_gci(
            float(mae_retrain * _sf), round(float(mse_retrain) * _sf2, 6),
            float(mae_retrain * _sf), round(float(mse_retrain) * _sf2, 6), max_retrain_real * _sf,
            float(baseline_mae_val * _sf), round(base_mse_val * _sf2, 6),
            float(baseline_mae_train * _sf), round(base_mse_train * _sf2, 6), e_gm * _sf
        )

        base_u_train_raw    = UMaxPCriterion.compute_uraw(base_sde_train, base_gci_train)
        base_u_retrain_raw  = UMaxPCriterion.compute_uraw(base_sde_retrain, base_gci_retrain)
        base_u_train_map    = UMaxPCriterion.compute_umaxp(base_sde_train, base_gci_train, a_emp_base_tr)
        base_u_retrain_map  = UMaxPCriterion.compute_umaxp(base_sde_retrain, base_gci_retrain, a_emp_base_ret)

        print(f"\n   [RESULTS]\n   MSE (Train Mode):     {round(base_mse * _sf2, 6):.6f}\n   MSE (Retrain Mode):   {round(float(mse_retrain) * _sf2, 6):.6f}")
        print(f"   MAE (Train Mode):     {float(baseline_mae_train * _sf):.6f}\n   MAE (Retrain Mode):   {float(mae_retrain * _sf):.6f}")
        print(f"\n   [CALCULATED REFERENCES (NATURAL SCALE)]\n   1. Max Error (Train):       {max_train_real * _sf:.6f}")
        print(f"   2. Max Error (Retrain):     {max_retrain_real * _sf:.6f}\n   3. P97.5 (Train Anchor):    {p97_train_metric * _sf:.6f}")
        print(f"   4. P97.5 (Retrain Anchor):  {p97_retrain_metric * _sf:.6f}")
        print(f" {Colors.YELLOW}{Colors.BOLD}  >> FINAL ANCHOR (for Optuna): {truth_anchor * _sf:.6f}{Colors.ENDC}")
        print(f" {Colors.YELLOW}{Colors.BOLD}  >> UNIVERSAL GM CEILING:      {e_gm * _sf:.6f}{Colors.ENDC}")
        print(f" {Colors.BLUE}{Colors.BOLD}  >> MIN CHANNEL THICKNESS:     {min_thickness * _sf:.6f} (Universal Dataset Property){Colors.ENDC}")
        print(f" {Colors.GREEN}{Colors.BOLD}  >> FIXED COEFF BOUNDS:        ({fixed_fb[0]:.6f}, {fixed_fb[1]:.6f}){Colors.ENDC}")
        if has_int:
            print(f" {Colors.GREEN}{Colors.BOLD}  >> FIXED INTERCEPT BOUNDS:    ({fixed_ib[0]:.6f}, {fixed_ib[1]:.6f}){Colors.ENDC}")
        print(f"\n {Colors.CYAN}{Colors.BOLD}  >> U_MAXP RAW (Train)  [Hard-Mode Rival]:  {base_u_train_raw:.6f}   (GCI={base_gci_train:.6f}, SDE={base_sde_train:.6f}){Colors.ENDC}")
        print(f" {Colors.CYAN}{Colors.BOLD}  >> U_MAXP MAP (Train)  [EVT Report]:        {base_u_train_map:.6f}   (A_emp={a_emp_base_tr:.6f}, Phi={phi_base_tr:.4f}){Colors.ENDC}")
        print(f" {Colors.CYAN}{Colors.BOLD}  >> U_MAXP RAW (Retrain)[Hard-Mode Rival]:  {base_u_retrain_raw:.6f}   (GCI={base_gci_retrain:.6f}, SDE={base_sde_retrain:.6f}){Colors.ENDC}")
        print(f" {Colors.CYAN}{Colors.BOLD}  >> U_MAXP MAP (Retrain)[EVT Report]:        {base_u_retrain_map:.6f}   (A_emp={a_emp_base_ret:.6f}, Phi={phi_base_ret:.4f}){Colors.ENDC}")
        print(f"{'='*80}")

        return BaselineMetrics(base_mse_raw, base_mse, base_coeffs, retrain_coeffs, base_sde_train, base_sde_retrain, 
                               baseline_mae_train, baseline_mae_val, max_train_real, max_retrain_real, p97_train_metric, p97_retrain_metric, 
                               mse_retrain, mae_retrain, truth_anchor, ref_int, ref_feats, e_gm, ref_mse_active, fixed_fb, fixed_ib,
                               base_mse_train, base_mse_val, round(base_mse * _sf2, 6), float(baseline_mae_train * _sf),
                               float(baseline_mae_val * _sf), round(base_mse_train * _sf2, 6), round(base_mse_val * _sf2, 6),
                               round(mse_retrain * _sf2, 6), float(mae_retrain * _sf), mae_type, outlier_pct,
                               base_gci_train, base_gci_retrain, base_u_train_raw, base_u_retrain_raw, base_u_train_map, base_u_retrain_map,
                               a_emp_base_tr, a_emp_base_ret, phi_base_tr, phi_base_ret, emax_rob_base_tr, emax_rob_base_ret, min_thickness)


# =============================================================================
# OPTIMIZATION ORCHESTRATOR
# =============================================================================

class DGDTLOptimizer:
    def __init__(self, env: DataEnvironment, baseline: BaselineMetrics, loop_id: int):
        self.env = env
        self.config = env.config
        self.baseline = baseline
        self.target_anchor_ = baseline.truth_anchor
        self.loop_id = loop_id

    def _objective_internal(self, trial: optuna.Trial, search_space: Dict) -> float:
        dw = round(trial.suggest_float('dw', *search_space['dw'], step=1e-6), 6)
        tol = round(trial.suggest_float('tol', *search_space['tol'], step=1e-6), 6)
        ambition = round(trial.suggest_float('ambition', *search_space['ambition'], step=0.01), 4) if isinstance(search_space['ambition'], tuple) else search_space['ambition']
        gap = round(trial.suggest_float('gap', *search_space['gap'], step=0.01), 4)
        
        raw_natural_train = round(self.target_anchor_ * ambition, 6)
        raw_natural_valid = round(raw_natural_train * (1.0 + gap), 6)
        
        scale_factor = 1.0 if self.config.mode == 'error_matrix' else (self.config.stats_y['std'] if self.config.stats_y else 1.0)
        scale_sq     = scale_factor ** 2
        
        if scale_factor < 1e-6: raise optuna.TrialPruned()
        
        user_input_train = round(raw_natural_train * scale_factor, 6)
        user_input_valid = round(raw_natural_valid * scale_factor, 6)
        
        if user_input_train > 50.0 or user_input_valid > 50.0: raise optuna.TrialPruned()
        
        internal_train = user_input_train / scale_factor
        internal_valid = user_input_valid / scale_factor
        fb = self.baseline.fixed_fb
        ib = self.baseline.fixed_ib
        
        if self.baseline.base_mse * (1 + tol) <= 1e-7: raise optuna.TrialPruned()
        
        params = {
            'mode': self.config.mode, 'fit_intercept': self.config.fit_intercept, 'beta_sum_one': self.config.beta_sum_one, 
            'diversity_weight': dw, 'TOLERANCE_FACTOR': tol, 'coeff_bounds': fb, 'intercept_bounds': ib,
            'constraint_threshold': internal_train, 'VALIDATION_THRESHOLD': internal_valid,
            'num_solutions_run1': 1000, 'num_solutions_run2': 1000, 'n_jobs': FIXED_N_JOBS, 'verbose': False, 'random_state': RANDOM_SEED
        }
        
        # --- REPRODUCIBILITY ISOLATION ---
        # Reset NumPy's global RNG before each trial to ensure identical
        # initial random states across all DGDTLEstimator executions.
        
        np.random.seed(RANDOM_SEED)
        
        try:
            model = DGDTLEstimator(**params)
            model.baseline_mse_ = self.baseline.base_mse
            model.baseline_coeffs_ = self.baseline.base_coeffs
            model._baseline_calculated = True 
            
            model.fit(self.env.X_t, self.env.y_t, self.env.X_v, self.env.y_v)
            
            S, D, comp_pen, N_elite, N_valid = TopologicalEngine.extract_topology(model.run1_valid_, model.baseline_mse_, model.filter_limits_)
            
            X_comb = np.vstack((self.env.X_t, self.env.X_v))
            y_comb = np.concatenate((self.env.y_t, self.env.y_v))
            agg_func = np.median if self.baseline.mae_type == 'median' else np.mean

            tau_anchor_nat    = self.baseline.truth_anchor  * scale_factor
            e_gm_nat          = self.baseline.e_gm           * scale_factor
            min_thickness_nat = self.baseline.min_thickness  * scale_factor

            if model.champion_run2_: 
                c_r2 = model.champion_run2_['coeffs']
                trial.set_user_attr("coeffs", c_r2)
                p_r2 = model.predict(X_comb, beta=c_r2) if self.config.mode == 'raw' else model.predict(X_comb, y_reference=y_comb, beta=c_r2)
                err_r2_nat = np.abs(y_comb - p_r2) * scale_factor
                max_r2_nat = float(np.max(err_r2_nat))
                mse_r2_nat = float(model.champion_run2_['MSE_vldt'] * scale_sq)
                mae_r2_nat = float(model.champion_run2_['MAE_vldt'] * scale_factor)
                
                trial.set_user_attr("max_err_r2", max_r2_nat)
                trial.set_user_attr("mse_vldt_r2", mse_r2_nat)
                trial.set_user_attr("mae_vldt_r2", mae_r2_nat)
                
                p_tr_r2 = model.predict(self.env.X_t, beta=c_r2) if self.config.mode == 'raw' else model.predict(self.env.X_t, y_reference=self.env.y_t, beta=c_r2)
                err_tr_r2_nat = np.abs(self.env.y_t - p_tr_r2) * scale_factor
                mse_tr_r2_nat = float(np.mean(err_tr_r2_nat ** 2))
                mae_tr_r2_nat = float(agg_func(err_tr_r2_nat))
                trial.set_user_attr("mse_train_r2", mse_tr_r2_nat)
                trial.set_user_attr("mae_train_r2", mae_tr_r2_nat)
                
                e_r2 = np.sqrt(mae_r2_nat * np.sqrt(mse_r2_nat)) / (self.baseline.baseline_mae_val_nat + 1e-9)
                sde_b_r2 = UMaxPCriterion.compute_sde_b(S, D, comp_pen, e_r2, ambition)
                trial.set_user_attr("sde_run2", float(sde_b_r2))
                
                gci_r2 = ConsistencyEngine.compute_gci(mae_r2_nat, mse_r2_nat, mae_tr_r2_nat, mse_tr_r2_nat, max_r2_nat,
                                                       self.baseline.baseline_mae_val_nat, self.baseline.base_mse_val_nat,
                                                       self.baseline.baseline_mae_train_nat, self.baseline.base_mse_train_nat, e_gm_nat)
                trial.set_user_attr("gci_run2", gci_r2)
                
                a_emp_r2, phi_emp_r2, emax_rob_r2 = EVTAnalyzer.compute_empirical_authenticity(err_r2_nat, tau_anchor_nat, e_gm_nat, min_thickness_nat)
                trial.set_user_attr("a_emp_r2", a_emp_r2)
                trial.set_user_attr("phi_emp_r2", phi_emp_r2)
                trial.set_user_attr("emax_rob_r2", emax_rob_r2)

                u_run2 = UMaxPCriterion.compute_umaxp(sde_b_r2, gci_r2, a_emp_r2)
                trial.set_user_attr("u_run2", u_run2)
            
            if model.champion_run1_:
                c_r1 = model.champion_run1_['coeffs']
                trial.set_user_attr("coeffs_run1", c_r1)
                p_r1 = model.predict(X_comb, beta=c_r1) if self.config.mode == 'raw' else model.predict(X_comb, y_reference=y_comb, beta=c_r1)
                err_r1_nat = np.abs(y_comb - p_r1) * scale_factor
                max_r1_nat = float(np.max(err_r1_nat))
                mse_r1_nat = float(model.champion_run1_['MSE_vldt'] * scale_sq)
                mae_r1_nat = float(model.champion_run1_['MAE_vldt'] * scale_factor)
                
                trial.set_user_attr("max_err_r1", max_r1_nat)
                trial.set_user_attr("mse_vldt_r1", mse_r1_nat)
                trial.set_user_attr("mae_vldt_r1", mae_r1_nat)
                
                p_tr_r1 = model.predict(self.env.X_t, beta=c_r1) if self.config.mode == 'raw' else model.predict(self.env.X_t, y_reference=self.env.y_t, beta=c_r1)
                err_tr_r1_nat = np.abs(self.env.y_t - p_tr_r1) * scale_factor
                mse_tr_r1_nat = float(np.mean(err_tr_r1_nat ** 2))
                mae_tr_r1_nat = float(agg_func(err_tr_r1_nat))
                trial.set_user_attr("mse_train_r1", mse_tr_r1_nat)
                trial.set_user_attr("mae_train_r1", mae_tr_r1_nat)
                
                e_r1 = np.sqrt(mae_r1_nat * np.sqrt(mse_r1_nat)) / (self.baseline.baseline_mae_val_nat + 1e-9)
                sde_b_r1 = UMaxPCriterion.compute_sde_b(S, D, comp_pen, e_r1, ambition)
                trial.set_user_attr("sde_run1", float(sde_b_r1))
                
                gci_r1 = ConsistencyEngine.compute_gci(mae_r1_nat, mse_r1_nat, mae_tr_r1_nat, mse_tr_r1_nat, max_r1_nat,
                                                       self.baseline.baseline_mae_val_nat, self.baseline.base_mse_val_nat,
                                                       self.baseline.baseline_mae_train_nat, self.baseline.base_mse_train_nat, e_gm_nat)
                trial.set_user_attr("gci_run1", gci_r1)
                
                a_emp_r1, phi_emp_r1, emax_rob_r1 = EVTAnalyzer.compute_empirical_authenticity(err_r1_nat, tau_anchor_nat, e_gm_nat, min_thickness_nat)
                trial.set_user_attr("a_emp_r1", a_emp_r1)
                trial.set_user_attr("phi_emp_r1", phi_emp_r1)
                trial.set_user_attr("emax_rob_r1", emax_rob_r1)

                U_score = UMaxPCriterion.compute_umaxp(sde_b_r1, gci_r1, a_emp_r1)
                trial.set_user_attr("U_score", U_score)
            
            u1 = float(U_score)     if 'U_score' in locals() else 0.0
            u2 = float(u_run2)      if 'u_run2'  in locals() else 0.0
            return u1 if u1 > 0.0 else u2
        except Exception:
            return 0.0

    def run_scout(self, start_attempt: int, ambition_ceil: float) -> Dict[str, Any]:
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*80}\nPHASE 1: THE SCOUT (Ambition Locked: {ambition_ceil:.2f})\n{'='*80}{Colors.ENDC}\n")
        
        scout_levels = [
            {'attempt': 1, 'dw_range': (0.0, 1.0),   'seeds': [0.1, 0.3, 0.5, 0.7, 0.9]},
            {'attempt': 2, 'dw_range': (1.0, 10.0),  'seeds': [1.5, 3.5, 5.5, 7.5, 9.5]},
            {'attempt': 3, 'dw_range': (10.0, 20.0), 'seeds': [11.0, 13.0, 15.0, 17.0, 19.0]},
            {'attempt': 4, 'dw_range': (20.0, 50.0), 'seeds': [22.0, 28.0, 34.0, 40.0, 46.0]}
        ]
        
        results = []
        for level in scout_levels:
            attempt = level['attempt']
            if attempt < start_attempt: continue
                
            gap_max, dw_range, seeds = 0.30, level['dw_range'], level['seeds']
            print(f"--- Scout Attempt {attempt}/4 (Gap Max: {gap_max:.2f} | DW Range: {dw_range}) ---")
            
            sampler_seed = RANDOM_SEED + attempt if self.loop_id == 1 else RANDOM_SEED + (self.loop_id * 100) + attempt
            sampler = TPESampler(seed=sampler_seed, n_startup_trials=len(seeds), n_ei_candidates=24, consider_prior=True, multivariate=False, warn_independent_sampling=False)
            study = optuna.create_study(direction='maximize', sampler=sampler)
            
            print(f"  {Colors.BLUE}Injecting {len(seeds)} paired seeds (dw, gap): {list(zip(seeds, GAP_SEEDS))}{Colors.ENDC}")
            for s_dw, s_gap in zip(seeds, GAP_SEEDS): study.enqueue_trial({'dw': s_dw, 'gap': s_gap})

            space = {'dw': dw_range, 'tol': (-0.5, 2.0), 'ambition': (0.50, ambition_ceil), 'gap': (0.00, gap_max)}
            study.optimize(lambda t: self._objective_internal(t, space), n_trials=N_TRIALS_SCOUT)
            
            v_trials = [t for t in study.trials if t.value is not None and t.value > 0]
            s_trials = [t for t in v_trials if t.params.get('ambition', 1.2) <= ambition_ceil]
            n_valid, n_strong = len(v_trials), len(s_trials)
            
            print(f"  {Colors.GREEN}> Valid Solutions: {n_valid} | Strong Candidates (Ambition <= {ambition_ceil:.2f}): {n_strong}{Colors.ENDC}\n")
            
            results.append({'attempt': attempt, 'gap': gap_max, 'study': study, 'valid_count': n_valid, 'strong_count': n_strong, 'dw_range': dw_range})
            
            if n_strong > 0:
                print(f"    {Colors.YELLOW}EARLY STOPPING: Optimal candidate found at Level {attempt}.{Colors.ENDC}")
                print(f"{Colors.BLUE}{'-'*80}\nHYBRID LEVEL SELECTION (DOUBLE LOCK):{Colors.ENDC}")
                print(f"  {Colors.GREEN}✓ WINNER (STRONG): Attempt {attempt} (Gap {gap_max:.2f}) - {n_strong} strong solutions found.{Colors.ENDC}")
                return {'success': True, 'study': study, 'gap_max': gap_max, 'dw_range': dw_range, 'attempt': attempt}

        valid_results = [r for r in results if r['valid_count'] > 0]
        if valid_results:
            winner = max(valid_results, key=lambda x: x['valid_count'])
            print(f"{Colors.BLUE}{'-'*80}\nHYBRID LEVEL SELECTION (DOUBLE LOCK):{Colors.ENDC}")
            print(f"  {Colors.YELLOW}⚠ WINNER (FALLBACK): Attempt {winner['attempt']} (Gap {winner['gap']:.2f}) - Selected by highest valid count ({winner['valid_count']}).{Colors.ENDC}")
            return {'success': True, 'study': winner['study'], 'gap_max': winner['gap'], 'dw_range': winner['dw_range'], 'attempt': winner['attempt']}
                
        return {'success': False}

    def diagnose(self, scout_results: Dict[str, Any], ambition_ceil: float) -> Dict[str, Any]:
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*80}\nPHASE 2: DIAGNOSIS (Warm Start Generation)\n{'='*80}{Colors.ENDC}")
        study = scout_results['study']
        valid_trials = sorted([t for t in study.trials if t.value is not None and t.value > 0], key=lambda t: t.value, reverse=True)
        
        top_trials = valid_trials[:min(5, len(valid_trials))]
        ambitions = [round(t.params['ambition'], 4) for t in top_trials]
        print(f"  {Colors.CYAN}Top {len(top_trials)} Ambitions (by U_MAXP from winning level): {sorted(ambitions)}{Colors.ENDC}")
        
        good_starts = [t for t in valid_trials if t.params['ambition'] <= ambition_ceil]
        if good_starts:
            warm_starts = [t.params for t in good_starts[:3]]
            print(f"  {Colors.BLUE}Diagnosis: Clean Convergence -> Capping ambition strictly at {ambition_ceil:.2f}{Colors.ENDC}")
            print(f"  {Colors.GREEN}✓ Selected {len(warm_starts)} warm starts.{Colors.ENDC}")
        else:
            adj_params = valid_trials[0].params.copy()
            adj_params['ambition'] = ambition_ceil - 0.05
            warm_starts = [adj_params]
            print(f"  {Colors.YELLOW}Diagnosis: Low coverage -> Fallback seed generated.{Colors.ENDC}")
            
        return {'ambition_range': (0.50, ambition_ceil), 'gap_max': scout_results['gap_max'], 'warm_starts': warm_starts, 'dw_range': scout_results['dw_range']}

    def run_siege(self, siege_conf: Dict[str, Any], attempt: int) -> optuna.study.Study:
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*80}\nPHASE 3: THE SIEGE (Exploitation)\n{'='*80}{Colors.ENDC}")
        dw_min, dw_max = siege_conf['dw_range']
        
        print(f"  {Colors.YELLOW}>> Siege DW Range dynamically locked to Scout: ({dw_min}, {dw_max}){Colors.ENDC}")
        
        sampler_seed = RANDOM_SEED + 10 if self.loop_id == 1 else RANDOM_SEED + 10 + (self.loop_id * 100) + attempt
        sampler = TPESampler(seed=sampler_seed, n_startup_trials=len(siege_conf['warm_starts']) + 7, n_ei_candidates=24, consider_prior=True, multivariate=False, warn_independent_sampling=False)
        study = optuna.create_study(direction='maximize', sampler=sampler)

        print(f"  {Colors.BLUE}Injecting {len(siege_conf['warm_starts'])} warm start seeds from Diagnosis...{Colors.ENDC}")
        for ws in siege_conf['warm_starts']: study.enqueue_trial(ws)
        
        siege_seeds = np.linspace(dw_min, dw_max, 7)
        print(f"  {Colors.BLUE}Injecting {len(siege_seeds)} hardcoded safety seeds for 'dw': {np.round(siege_seeds, 2).tolist()}{Colors.ENDC}")
        for s in siege_seeds: study.enqueue_trial({'dw': round(float(s), 6)})
            
        space = {'dw': (dw_min, dw_max), 'tol': (-0.5, 2.0), 'ambition': siege_conf['ambition_range'], 'gap': (0.00, siege_conf['gap_max'])}
        
        def monitor(study, trial):
            if trial.value is not None and trial.value > 0: 
                print(f"  [Siege {trial.number+1:02d}] U_MAXP: {Colors.CYAN}{trial.value:.4f}{Colors.ENDC} | Ambition: {Colors.YELLOW}{trial.params['ambition']:.4f}{Colors.ENDC} | DW: {trial.params.get('dw', 0):.4f}")

        study.optimize(lambda t: self._objective_internal(t, space), n_trials=N_TRIALS_SIEGE, callbacks=[monitor])
        return study

    def run_gm_valve_grid(self, best_t: Any, dw_range: Tuple[float, float], ambition_ceil: float, gap_max: float, attempt: int) -> optuna.study.Study:
        print(f"\n{Colors.RED}{Colors.BOLD}{'='*80}\nPHASE 3.5: ESCAPE VALVE (GM THRESHOLD GRID)\n{'='*80}{Colors.ENDC}")
        self.target_anchor_ = self.baseline.e_gm 
        
        sampler_seed = RANDOM_SEED + 20 + attempt if self.loop_id == 1 else RANDOM_SEED + 20 + (self.loop_id * 100) + attempt
        sampler_gm = TPESampler(seed=sampler_seed, n_startup_trials=6, n_ei_candidates=24, consider_prior=True, multivariate=False, warn_independent_sampling=False)
        study = optuna.create_study(direction='maximize', sampler=sampler_gm)
        
        b_dw = best_t.params['dw'] if best_t else sum(dw_range)/2.0
        b_tol = best_t.params['tol'] if best_t else 0.5

        for g in [0.0, gap_max]:
            study.enqueue_trial({'ambition': ambition_ceil, 'gap': g, 'dw': b_dw, 'tol': b_tol})
            study.enqueue_trial({'ambition': ambition_ceil, 'gap': g, 'dw': dw_range[0], 'tol': -0.5})
            study.enqueue_trial({'ambition': ambition_ceil, 'gap': g, 'dw': dw_range[1], 'tol': 2.0})

        space = {'dw': dw_range, 'tol': (-0.5, 2.0), 'ambition': (0.50, ambition_ceil), 'gap': (0.00, gap_max)}
        
        def gm_monitor(study, trial):
            if trial.value is not None and trial.value > 0: 
                print(f"  [GM Valve {trial.number+1:02d}] U_MAXP: {Colors.CYAN}{trial.value:.4f}{Colors.ENDC} | Ambition: {Colors.YELLOW}{trial.params['ambition']:.4f}{Colors.ENDC} | DW: {trial.params.get('dw', 0):.4f}")
                
        study.optimize(lambda t: self._objective_internal(t, space), n_trials=N_TRIALS_SIEGE, callbacks=[gm_monitor])
        
        self.target_anchor_ = self.baseline.truth_anchor 
        return study


# =============================================================================
# REPORTING ENGINE (HUNTER MAP REPORT)
# =============================================================================

class ReportGenerator:
    @staticmethod
    def generate(config: HunterConfig, baseline: BaselineMetrics, study: optuna.study.Study, elapsed: str, out_dir: str, attempt: int = 0, suffix: str = "", active_anchor: float = None, is_gm_valve: bool = False, loop_status: str = "STRICT") -> Tuple[float, float, List[ScoutRecord]]:
        
        valid_trials = [t for t in study.trials if t.value is not None]
        if not valid_trials:
            return 0.0, 0.0, []

        # ── Inter-trial tie-break (Regime-Aware) ───────────────────────────
        # Resolve |ΔU| < ε_tie ties with U_comp only for identical
        # "thermodynamic" regimes; otherwise retain the original U_score.
        # ε_tie = 0.02 is inter-scout calibrated; diagnostics support
        # future intra-Siege recalibration.
        
        _EPS_TIE_TRIAL = 0.02
        best_val = max(t.value for t in valid_trials if t.value is not None)
        top_trials = [t for t in valid_trials
                      if t.value is not None and
                      abs(t.value - best_val) / (best_val + 1e-12) < _EPS_TIE_TRIAL]

        # ── DIAGNOSTIC: inter-trial tie pool census ─────────────────
        # Exports trial rankings, tie-pool membership, and U_comp for
        # post-hoc diagnostics. Does not affect selection.
        
        try:
            _diag_rows = []
            for _rank, _tr in enumerate(
                sorted(valid_trials, key=lambda x: x.value, reverse=True), start=1
            ):
                _gap_pct = abs(_tr.value - best_val) / (best_val + 1e-12) * 100.0
                _in_pool = _tr in top_trials
                _u1_d = _tr.user_attrs.get('U_score', 0.0)
                _u2_d = _tr.user_attrs.get('u_run2', 0.0)
                # Minimal U_comp proxy (geom mean only — phi not recomputed here)
                _ucomp_proxy = float(np.sqrt(_u1_d * _u2_d)) if (_u1_d > 0 and _u2_d > 0) else max(_u1_d, _u2_d)
                _diag_rows.append({
                    'Scout': f"{suffix}_Scout_{attempt}",
                    'Trial': _tr.number,
                    'Rank': _rank,
                    'U_score_R1': round(_u1_d, 8),
                    'U_score_R2': round(_u2_d, 8),
                    'U_optuna': round(_tr.value, 8),
                    'Gap_pct_vs_best': round(_gap_pct, 6),
                    'In_TiePool_2pct': _in_pool,
                    'U_comp_proxy': round(_ucomp_proxy, 8),
                    'Ambition': round(_tr.params.get('ambition', 0.0), 6),
                    'DW': round(_tr.params.get('dw', 0.0), 6),
                    'Gap_param': round(_tr.params.get('gap', 0.0), 6),
                })
            if _diag_rows:
                _diag_fname = os.path.join(
                    out_dir, f"tie_pool_diag_{suffix}_Scout_{attempt}.csv"
                )
                pd.DataFrame(_diag_rows).to_csv(_diag_fname, index=False)
        except Exception:
            pass   
        # ───────────────────────────────────────────────────────────────────

        # ── Intra-Siege selection delegated to MicroArbitration ──────
        # Replaces inline _u_comp + _e_inc_r1 + selection loop.
        # Implements the two-level protocol (Level-1: U_comp, Level-2: E_inc)
        # defined in u_maxp_core. Metric: U_score (raw U_MAXP, pre-k-
        # penalization) — the correct metric for intra-Siege context.
        
        _e_base    = np.sqrt(baseline.baseline_mae_val_nat   * np.sqrt(baseline.base_mse_val_nat))
        _e_base_tr = np.sqrt(baseline.baseline_mae_train_nat * np.sqrt(baseline.base_mse_train_nat))
        t = MicroArbitration.select_best_trial(
            top_trials    = top_trials,
            e_base        = _e_base,
            e_base_tr     = _e_base_tr,
            mae_val_bl    = baseline.baseline_mae_val_nat,
            mae_tr_bl     = baseline.baseline_mae_train_nat + 1e-12,
            mse_val_bl    = baseline.base_mse_val_nat,
            mse_tr_bl     = baseline.base_mse_train_nat + 1e-12,
            eps_tie       = _EPS_TIE_TRIAL,
        )
        
        # ───────────────────────────────────────────────────────────────────
        p = t.params
        p = t.params
        # ──────────────────────────────────────────────────────────────────

        anchor_used = active_anchor if active_anchor is not None else baseline.truth_anchor
        
        amb, gap = round(p['ambition'], 4), round(p['gap'], 4)
        raw_natural_train = round(anchor_used * amb, 6)
        raw_natural_valid = round(raw_natural_train * (1.0 + gap), 6)
        
        scale_factor = config.stats_y['std'] if config.stats_y else 1.0
        user_input_train = round(raw_natural_train * scale_factor, 6)
        user_input_valid = round(raw_natural_valid * scale_factor, 6)
        abs_gap_val = round(user_input_valid - user_input_train, 6)

        fb = baseline.fixed_fb
        ib = baseline.fixed_ib
        ib_str = f"{ib[0]:.6f} to {ib[1]:.6f}" if ib else "N/A"
        
        sde_r1 = t.user_attrs.get('sde_run1', 0.0)   
        sde_r2 = t.user_attrs.get('sde_run2', 0.0)
        gci_r1 = t.user_attrs.get('gci_run1', 0.0)
        gci_r2 = t.user_attrs.get('gci_run2', 0.0)

        max_r1 = t.user_attrs.get('max_err_r1', user_input_train)
        max_r2 = t.user_attrs.get('max_err_r2', user_input_train)
        mse_r1 = t.user_attrs.get('mse_vldt_r1', float('inf'))
        mse_r2 = t.user_attrs.get('mse_vldt_r2', float('inf'))
        mae_r1 = t.user_attrs.get('mae_vldt_r1', float('inf'))
        mae_r2 = t.user_attrs.get('mae_vldt_r2', float('inf'))
        
        a_emp_r1 = t.user_attrs.get('a_emp_r1', 1.0)
        a_emp_r2 = t.user_attrs.get('a_emp_r2', 1.0)
        phi_emp_r1 = t.user_attrs.get('phi_emp_r1', 0.0)
        phi_emp_r2 = t.user_attrs.get('phi_emp_r2', 0.0)
        emax_rob_r1 = t.user_attrs.get('emax_rob_r1', max_r1)
        emax_rob_r2 = t.user_attrs.get('emax_rob_r2', max_r2)
        
        coeffs_r1 = t.user_attrs.get('coeffs_run1', [])
        coeffs_r2 = t.user_attrs.get('coeffs', [])

        u_r1 = t.user_attrs.get('U_score', sde_r1 * gci_r1 * a_emp_r1)
        u_r2 = t.user_attrs.get('u_run2', sde_r2 * gci_r2 * a_emp_r2)

        max_base_u_raw = max(baseline.base_u_train_raw, baseline.base_u_retrain_raw)

        delta_r1_tr  = ((u_r1 - baseline.base_u_train_raw)   / (baseline.base_u_train_raw   + 1e-12)) * 100.0
        delta_r1_ret = ((u_r1 - baseline.base_u_retrain_raw) / (baseline.base_u_retrain_raw + 1e-12)) * 100.0
        delta_r2_tr  = ((u_r2 - baseline.base_u_train_raw)   / (baseline.base_u_train_raw   + 1e-12)) * 100.0
        delta_r2_ret = ((u_r2 - baseline.base_u_retrain_raw) / (baseline.base_u_retrain_raw + 1e-12)) * 100.0

        delta_r1_max = ((u_r1 - max_base_u_raw) / (max_base_u_raw + 1e-12)) * 100.0
        delta_r2_max = ((u_r2 - max_base_u_raw) / (max_base_u_raw + 1e-12)) * 100.0

        def get_verdict_info(delta):
            if delta > 1.0: return "IMPROVEMENT"
            elif delta < -1.0: return "DEGRADATION"
            else: return "BASELINE"

        verdict_r1_plain = get_verdict_info(delta_r1_max)
        verdict_r2_plain = get_verdict_info(delta_r2_max)
        
        valve_msg = f"ACCEPTED (Valve)"
        if verdict_r1_plain == "BASELINE" and is_gm_valve: verdict_c1 = f"{valve_msg:<15}"
        else: verdict_c1 = f"{verdict_r1_plain:<15}"
            
        if verdict_r2_plain == "BASELINE" and is_gm_valve: verdict_c2 = f"{valve_msg}"
        else: verdict_c2 = f"{verdict_r2_plain}"

        fmt_d1_tr  = f"{'+' if delta_r1_tr  > 0 else ''}{delta_r1_tr:.2f}%"
        fmt_d1_ret = f"{'+' if delta_r1_ret > 0 else ''}{delta_r1_ret:.2f}%"
        fmt_d2_tr  = f"{'+' if delta_r2_tr  > 0 else ''}{delta_r2_tr:.2f}%"
        fmt_d2_ret = f"{'+' if delta_r2_ret > 0 else ''}{delta_r2_ret:.2f}%"
        fmt_d1_max = f"{'+' if delta_r1_max > 0 else ''}{delta_r1_max:.2f}%"
        fmt_d2_max = f"{'+' if delta_r2_max > 0 else ''}{delta_r2_max:.2f}%"

        imp_train_r1   = max_r1 / (baseline.max_train_real   * scale_factor + 1e-9)
        imp_retrain_r1 = max_r1 / (baseline.max_retrain_real * scale_factor + 1e-9)
        imp_train_r2   = max_r2 / (baseline.max_train_real   * scale_factor + 1e-9)
        imp_retrain_r2 = max_r2 / (baseline.max_retrain_real * scale_factor + 1e-9)
        amb_actual_r1  = max_r1 / (baseline.truth_anchor * scale_factor + 1e-9)
        amb_actual_r2  = max_r2 / (baseline.truth_anchor * scale_factor + 1e-9)

        if config.stats_y and config.stats_y.get('std', 1.0) != 1.0:
            scale_label = "STANDARDIZED (zero mean, unit variance)"
        elif config.stats_y and config.stats_y.get('std', 1.0) == 1.0:
            scale_label = "MEAN-CENTRED (zero mean, natural scale)"
        else:
            scale_label = "NATURAL (original target scale)"

        report_content = f"""
{'='*80}
DGDTL HUNTER v1.0.0 - MAP UNIFIED METRICS REPORT (EPISTEMOLOGICALLY SHIELDED)
{'='*80}
Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Execution Time: {elapsed}
Mode: {config.mode.upper()} | Error Scale: {scale_label}
Loop Status: {loop_status}

{Colors.HEADER}[0] BASELINE REFERENCES & EPISTEMOLOGICAL SEPARATION{Colors.ENDC}
{'-'*80}
   [RESULTS]
   MSE (Train Mode):     {baseline.base_mse_nat:.6f}
   MSE (Retrain Mode):   {baseline.mse_retrain_nat:.6f}
   MAE (Train Mode):     {baseline.baseline_mae_train_nat:.6f}  [{baseline.mae_type.upper()}]
   MAE (Retrain Mode):   {baseline.mae_retrain_nat:.6f}  [{baseline.mae_type.upper()}]

   [CALCULATED REFERENCES (NATURAL SCALE)]
   1. Max Error (Train):         {baseline.max_train_real * scale_factor:.6f}
   2. Max Error (Retrain):       {baseline.max_retrain_real * scale_factor:.6f}
   3. Truth Anchor (P97.5):      {baseline.truth_anchor * scale_factor:.6f}
   >> UNIVERSAL GM CEILING:        {baseline.e_gm * scale_factor:.6f}
   >> DATASET MIN THICKNESS:       {baseline.min_thickness * scale_factor:.6f}
   >> Active Anchor for Run:       {anchor_used * scale_factor:.6f}

   [Epistemological Separation]
   Baseline U_MAXP Train   -> RAW (Hard-Mode Rival): {baseline.base_u_train_raw:.4f}  |  MAP (EVT Collapse): {baseline.base_u_train_map:.4f}  (A_emp={baseline.a_emp_train:.4f})
   Baseline U_MAXP Retrain -> RAW (Hard-Mode Rival): {baseline.base_u_retrain_raw:.4f}  |  MAP (EVT Collapse): {baseline.base_u_retrain_map:.4f}  (A_emp={baseline.a_emp_retrain:.4f})
   NOTE: All deltas use RAW baseline as denominator. Candidate U_MAXP uses penalized MAP score.

{Colors.HEADER}[1] UNIFIED ROBUSTNESS (U_MAXP = SDE_b* x GCI x A_emp){Colors.ENDC}
{'-'*80}
                            RUN 1           RUN 2
   > Verdict (vs RAW):      {verdict_c1} {verdict_c2}
   > U_MAXP (Penalized MAP): {u_r1:<15.4f} {Colors.BOLD}{u_r2:.4f}{Colors.ENDC}

   [Hard-Mode Deltas: Candidate MAP vs Baseline RAW]
   > Rel. Perf vs Max RAW:  {fmt_d1_max:<15} {fmt_d2_max}
   > Rel. Perf vs Train RAW:{fmt_d1_tr:<15} {fmt_d2_tr}
   > Rel. Perf vs Ret. RAW: {fmt_d1_ret:<15} {fmt_d2_ret}

   [Empirical Authenticity (A_emp)]
   > A_emp Penalty:         {a_emp_r1:<15.4f} {a_emp_r2:.4f}
   > Phi_emp (Excess):      {phi_emp_r1:<15.4f} {phi_emp_r2:.4f}
   > e_max_robusto (CVaR):  {emax_rob_r1:<15.6f} {emax_rob_r2:.6f}

   [Topological Stability]
   > SDE_b* (Optuna FG):    {sde_r1:<15.4f} {sde_r2:.4f}
   > GCI Score:             {gci_r1:<15.4f} {gci_r2:.4f}
   > MSE Validation:        {mse_r1:<15.6f} {mse_r2:.6f}
   > GM Valve Triggered:    {is_gm_valve}

{Colors.HEADER}[2] MAXIMUM ERROR ANALYSIS (EVT CONTEXT){Colors.ENDC}
{'-'*80}
   > Target P97.5 Error (Anchor * Ambition): {user_input_train:.6f}
   
   The model achieved an Absolute MAXIMUM Error (Train+Valid) of:
   > MAX Error Achieved:    {max_r1:<15.6f} {max_r2:.6f}
   > CVaR (Robust Tail):    {emax_rob_r1:<15.6f} {emax_rob_r2:.6f}
   
                            RUN 1           RUN 2
   A. vs. BASELINE MAX ERRORS (Worst-case vs Worst-case)
      1. vs. Max Train Error:  {imp_train_r1:<15.4f} {imp_train_r2:.4f}
      2. vs. Max Retrain Error:{imp_retrain_r1:<15.4f} {imp_retrain_r2:.4f}
      
   B. vs. ALGORITHM ANCHOR (Max Error vs Statistical Target)
      3. vs. Anchor (P97.5):   {amb_actual_r1:<15.4f} {amb_actual_r2:.4f}

{Colors.HEADER}[3] ENGINEERING THRESHOLDS{Colors.ENDC}
{'-'*80}
   > Ambition (vs. Anchor):   {amb:.4f}
   > Gap Factor (%):          {gap:.4f}
   > Gap Absolute (Y-units):  {abs_gap_val:.6f}
   > Threshold (Train):       {user_input_train:.6f}
   > Threshold (Valid):       {user_input_valid:.6f}

{Colors.HEADER}[4] HYPERPARAMETERS (For dgdtl_unified_umaxp.py){Colors.ENDC}
{'-'*80}
   > Diversity Weight:        {round(p['dw'], 6):.6f}
   > Tolerance Factor:        {round(p['tol'], 6):.6f}
   > Constraint Threshold:    {user_input_train:.6f}
   > Validation Threshold:    {user_input_valid:.6f}
   > Coeff Bounds:            {fb[0]:.6f} to {fb[1]:.6f}
   > Intercept Bounds:        {ib_str}
   
{Colors.HEADER}[5] COEFFICIENTS (Verify with hyperparameters from section 4){Colors.ENDC}
{'-'*80}
                            RUN 1           RUN 2\n"""

        off_r1 = len(coeffs_r1) - len(config.feature_names) if len(coeffs_r1) > 0 else 0
        off_r2 = len(coeffs_r2) - len(config.feature_names) if len(coeffs_r2) > 0 else 0
        has_int_r1 = (off_r1 == 1)
        has_int_r2 = (off_r2 == 1)

        if len(coeffs_r2) > 0 or len(coeffs_r1) > 0:
            if has_int_r1 or has_int_r2:
                c1_int = coeffs_r1[0] if has_int_r1 else 0.0
                c2_int = coeffs_r2[0] if has_int_r2 else 0.0
                report_content += f"   > Intercept:             {c1_int:<15.6f} {c2_int:.6f}\n"

            for i, name in enumerate(config.feature_names):
                c1_val = coeffs_r1[i + off_r1] if (i + off_r1) < len(coeffs_r1) and off_r1 >= 0 else 0.0
                c2_val = coeffs_r2[i + off_r2] if (i + off_r2) < len(coeffs_r2) and off_r2 >= 0 else 0.0
                report_content += f"   > {name:20s}: {c1_val:<15.6f} {c2_val:.6f}\n"

        report_content += f"""
{Colors.HEADER}[6] DEPLOYMENT GUIDE{Colors.ENDC}
{'-'*80}
   1. Open dgdtl_unified_umaxp.py
   2. Configure:
      - Mode:             {config.mode}
      - Fit Intercept:  {'YES' if config.fit_intercept else 'NO'}
      - Beta Sum=1:     {'YES' if config.beta_sum_one else 'NO'}
      - Normalize X:    {'YES' if config.stats_x else 'NO'}
      - Target Y:       {'NORMALIZED' if (config.stats_y and config.stats_y.get('std', 1.0) != 1.0) else ('CENTRED' if config.stats_y else 'NO')}
   3. Features:         {config.custom_formulas if config.custom_formulas else 'None'}
   4. Copy hyperparameters from Section [4]
   5. Verify Y_std = {config.y_std:.6f}
{'='*80}
"""
        clean_report_content = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', report_content)
        rep_name = f"DGDTL_Report_{suffix}_Scout_{attempt}.txt" 
        csv_name = f"metrics_{suffix}_Scout_{attempt}.csv" 
        
        with open(os.path.join(out_dir, rep_name), "w") as f: 
            f.write(clean_report_content)

        print(report_content.replace("IMPROVEMENT", f"{Colors.GREEN}IMPROVEMENT{Colors.ENDC}")
                            .replace("BASELINE", f"{Colors.YELLOW}BASELINE{Colors.ENDC}")
                            .replace("DEGRADATION", f"{Colors.RED}DEGRADATION{Colors.ENDC}"))
        
        pd.DataFrame([{
            'Verdict_Run1': verdict_r1_plain, 'Verdict_Run2': verdict_r2_plain,
            'Delta_R1_vs_Train_RAW': delta_r1_tr, 'Delta_R1_vs_Retrain_RAW': delta_r1_ret,
            'Delta_R2_vs_Train_RAW': delta_r2_tr, 'Delta_R2_vs_Retrain_RAW': delta_r2_ret,
            'Delta_R1_vs_MaxBase_RAW': delta_r1_max, 'Delta_R2_vs_MaxBase_RAW': delta_r2_max,
            'U_MAXP_Run1': u_r1, 'U_MAXP_Run2': u_r2,
            'Base_U_MAXP_Train_RAW': baseline.base_u_train_raw, 'Base_U_MAXP_Retrain_RAW': baseline.base_u_retrain_raw,
            'Base_U_MAXP_Train_MAP': baseline.base_u_train_map, 'Base_U_MAXP_Retrain_MAP': baseline.base_u_retrain_map,
            'SDE_b_Run1': sde_r1, 'SDE_b_Run2': sde_r2,
            'GCI_Run1': gci_r1, 'GCI_Run2': gci_r2,
            'A_emp_Run1': a_emp_r1, 'A_emp_Run2': a_emp_r2,
            'Phi_emp_Run1': phi_emp_r1, 'Phi_emp_Run2': phi_emp_r2,
            'e_max_rob_Run1': emax_rob_r1, 'e_max_rob_Run2': emax_rob_r2,
            'Ambition_vs_Anchor': amb, 'Max_Error_R1': max_r1, 'Max_Error_R2': max_r2,
            'MSE_Vldt_R1': mse_r1, 'MSE_Vldt_R2': mse_r2, 'Baseline_MSE': baseline.base_mse_nat,
            'Gap': gap, 'Threshold_Train': user_input_train, 'Version': '1.0.0', 'Valve_Triggered': is_gm_valve, 'Loop': loop_status
        }]).to_csv(os.path.join(out_dir, csv_name), index=False)
        
        try: loop_id_rec = int(suffix[1]) if len(suffix) >= 2 and suffix[0] == 'L' and suffix[1].isdigit() else 0
        except Exception: loop_id_rec = 0

        record_champion = ScoutRecord(
            label=f"{suffix}_Scout_{attempt}", loop_id=loop_id_rec, scout_level=attempt,
            is_gm=is_gm_valve, verdict_r1=verdict_r1_plain, verdict_r2=verdict_r2_plain,
            mae_r1=float(mae_r1), mae_r2=float(mae_r2),
            mse_r1=float(mse_r1), mse_r2=float(mse_r2), 
            mae_tr_r1=float(t.user_attrs.get('mae_train_r1', float('inf'))), mae_tr_r2=float(t.user_attrs.get('mae_train_r2', float('inf'))),
            mse_tr_r1=float(t.user_attrs.get('mse_train_r1', float('inf'))), mse_tr_r2=float(t.user_attrs.get('mse_train_r2', float('inf'))),
            max_err_r1=float(max_r1), max_err_r2=float(max_r2),
            sde_r1=float(sde_r1), sde_r2=float(sde_r2),
            gci_r1=float(gci_r1), gci_r2=float(gci_r2),
            u_r1=float(u_r1), u_r2=float(u_r2),
            a_emp_r1=float(a_emp_r1), a_emp_r2=float(a_emp_r2),
            phi_emp_r1=float(phi_emp_r1), phi_emp_r2=float(phi_emp_r2),
            emax_rob_r1=float(emax_rob_r1), emax_rob_r2=float(emax_rob_r2),
            coeffs_r1=list(coeffs_r1), coeffs_r2=list(coeffs_r2),
            ambition=float(amb), gap=float(gap),
            threshold_train=float(user_input_train), threshold_valid=float(user_input_valid),
            anchor_used=float(anchor_used), elapsed=elapsed, trial_number=t.number
        )

        return sde_r1, sde_r2, [record_champion]


# =============================================================================
# STRUCTURAL PROTOCOL
# =============================================================================
# Criterion mathematics and the reference Structural Selection Protocol are
# delegated to u_maxp_core_candidate. Hunter retains only search orchestration
# and report/application responsibilities.

class FrameworkReportBuilder:
    @staticmethod
    def generate_txt(pipeline: 'DGDTLPipeline'):
        df = pipeline.df
        df_base = pipeline.df_base
        all_cand_rows = pipeline.df_cands.index.tolist()
        dgdtl_winners = pipeline.dgdtl_winners
        
        SEP  = "=" * 110
        DASH = "-" * 110
        now  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        L    = []

        L += [
            SEP,
            f"DGDTL STRUCTURAL SELECTION FRAMEWORK  v1.0.0",
            "Four-Phase U_MAXP Post-Processor — Selection Narrative Report",
            SEP,
            f"Date              : {now}",
            f"Input Source      : {pipeline.source_name}",
            f"eps_F (num. floor): {FrameworkConfig.EPS_F}  [delta_min=1e-6 -> Delta_phi_min=1e-12, margin=1e8x]",
            f"delta_rel (thr)   : {FrameworkConfig.DELTA_REL}  [0.5% of phi_A — Run-2 contraction noise floor]",
            f"eps_tie (tie mrg) : {FrameworkConfig.EPS_TIE*100:.0f}%  [geom. mean: Delta_tie=0.35%(Max Tie), Delta_min=6.1%(Min Win)]",
            "",
            "ACRONYM LEGEND:",
            "  --- Models ---",
            "  BL_TR   BASELINE_TRAIN_ONLY  (M_MSE on training partition only)",
            "  BL_RT   BASELINE_RETRAIN     (M_MSE on train + validation)",
            "  HM      Hard-Mode rival = max{U_RAW(BL_TR), U_RAW(BL_RT)}",
            "  M_MSE   MSE Minimization (analytical baseline estimator)",
            "",
            "  --- Phase 1 verdict codes ---",
            "  TEQ   F1.0    Topological Equivalence        Run-1 retained (precedence)",
            "  JDC   F1.1    Joint Density Collapse         Run-1 retained",
            "  IRF   F1.2    Inefficient Refinement         Run-1 retained",
            "  GTR   F1.3    Genuine Topological Refinement Run-2 accepted",
            "  STP   F1.3phi Step Tie — phi Defends R1      Run-1 retained (P6)",
            "  SDI   F1.4    Spurious Density Increment     Run-1 retained",
            "",
            "  --- Phase 2 verdict codes ---",
            "  BND   F2.0    Baseline Native Dominance        BL wins (Gate 1 fail)",
            "  SPT   F2.1    Spurious Transfer                BL wins (I=T, G=F)",
            "  TRG   F2.2    Topological Regularization       C  wins (I=T, G=T)",
            "  TSA   F2.2-RT Topological Reg. — Scope Adv.    C  wins (P7 advisory)",
            "  STD   F2.3    Structural Dominance             C  wins (I=F, G=T)",
            "  ISI   F2.4    Incoherent Scalar Improvement    BL wins (I=F, G=F)",
            "",
            "  --- Phase 4 verdict codes (DOA = Dominance of Observable Accuracy) ---",
            "  DAC   FA.1  DOA Complete          C dominated BL_RT on both metrics (I=T, J=T)",
            "  DAE   FA.2  DOA Error             C lower error than BL_RT            (I=T, J=F)",
            "  DPO   FA.3  DOA Phi Only          C better coherence; BL_RT less err  (I=F, J=T)",
            "  ROS   FA.4  RT Observable Sup.    BL_RT dominated both metrics        (I=F, J=F)",
            "",
        ]

        if pipeline.f1_vb_active and pipeline.f1_vb_data and 'audits' in pipeline.f1_vb_data:
            L += [
                "F1-VB PARALLEL BRANCH (VALIDATION BIAS DIVERGENCE)", DASH,
                "  [!] F1-VB ACTIVE — Severe Overfitting to Validation detected in corpus.",
                f"  Corpus VBD Prevalence (π_VBD) : {pipeline.f1_vb_data.get('pi_vbd', 0.0)*100:.1f}%",
                ""
            ]
            for audit in pipeline.f1_vb_data['audits']:
                lb = audit.get('lb_res', {})
                sov_label = audit.get('sov_label', 'Unknown')
                
                L += [
                    f"  Champion (SOV)               : {sov_label}",
                    "  LINE B — OFT Twin Verification:",
                ]
                
                if lb.get('twin_label'):
                    L += [
                        f"    Twin candidate (OFT)     : {lb['twin_label']}",
                        f"    Topological class        : {lb['topo_class_txt']}",
                        f"      SDE_b(twin)={lb['sde_twin']:.4f}  SDE_b(C*_A)={lb['sde_cstar']:.4f}  ratio={lb['sde_ratio']:.4f}",
                        "",
                        "    Criterion 1 — vs. BL_TR (psi_G):",
                        f"      psi_G(twin)  = {lb['psi_G_twin']:.6f}",
                        f"      psi_G(BL_TR) = {lb['psi_G_bl_tr']:.6f}",
                        f"      psi_G(twin) > psi_G(BL_TR) : {lb['crit_1']}",
                        "",
                    ]
                    if lb.get('has_retrain', False):
                        L += [
                            "    Criterion 2 — vs. BL_RT (|Psi|):",
                            f"      |Psi(twin)|  = {lb['psi_twin_abs']:.6e}",
                            f"      |Psi(BL_RT)| = {lb['psi_bl_rt']:.6e}",
                            f"      |Psi(twin)| < |Psi(BL_RT)| : {lb['crit_2']}",
                            "",
                        ]
                    L += [
                        f"    LB Verdict : {lb['lb_verdict']} — {lb['lb_verdict_txt']}",
                        "",
                        "    Coherence Proposition P_coh:",
                        f"      U_MAXP_k(twin)={lb['uk_twin']:.6f} < U_MAXP_k(C*_A)={lb['uk_c_star']:.6f} ",
                        f"AND |Psi(twin)|={lb['psi_twin_abs']:.6e} < |Psi(C*_A)|={lb['psi_c_star']:.6e}",
                        f"      P_coh = {lb['p_coh']}  ",
                    ]
                    
                    if audit.get('action') == 'PROMOTED':
                        L += [
                            "",
                            f"    >>> LINE B PROMOTION [{audit['verdict']}]: {lb['twin_label']} dynamically overrides {sov_label} as Champion. <<<",
                            ""
                        ]
                    else:
                        L += [
                            "",
                            f"    >>> LINE B DIAGNOSTIC [{audit['verdict']}]: {sov_label} retained. Evidence insufficient for override. <<<",
                            ""
                        ]
                else:
                    L.append(f"    {lb.get('reason', 'No OFT twin available for Line B.')}\n")
            L.append("")

        L += [
            "BASELINE REFERENCE", DASH,
            f"  HM rival (U_MAXP_k) : {pipeline.label_hm}  [{pipeline.uk_hm:.6f}]",
            f"  Asymmetry ref BL_TR: e_val={pipeline.e_ref_val:.6f}  e_tr={pipeline.e_ref_tr:.6f}  ratio_ref={pipeline.ratio_ref:.6f}",
            "",
        ]
        for _, row in df_base.iterrows():
            ratio = float(row['E_Valid']) / (float(row['E_Train']) + 1e-12)
            L.append(f"  {row['Candidate_Label']:<30}  U_k={row['U_MAXP_k']:.6f}  e_val={row['E_Valid']:.6f}  e_tr={row['E_Train']:.6f}  ratio={ratio:.6f}  SDE_b={row['SDE_b']:.4f}")
        L.append("")

        L += [
            "PHASE 1 — TOPOLOGICAL STEP ACCEPTANCE CRITERION  (intra-scout)", DASH,
            "  Evaluates Run-1->Run-2 transition using (Delta_U_k, Delta_phi).",
            "",
        ]
        hdr1 = f"  {'Scout':<30} {'[Code] Case':<18} {'Delta_U_k':>12} {'Delta_phi':>12} {'Champion':>8}"
        L += [hdr1, "  " + "─" * 82]

        seen = set()
        for idx in all_cand_rows:
            row   = df.loc[idx]
            scout = str(row['Scout_Base'])
            if scout in seen: continue
            seen.add(scout)
            short = str(row.get('F1_Short', '—'))
            case  = str(row.get('F1_Case',  '—'))
            duk   = row.get('F1_dUk')
            dphi  = row.get('F1_dphi')
            cr    = row.get('Champion_Run', '?')
            
            duk_s  = f"{float(duk):+.6f}"  if pd.notna(duk) else '         —'
            dphi_s = f"{float(dphi):+.6f}" if pd.notna(dphi) else '         —'
            
            L.append(f"  {scout:<30} [{short}] {case:<10} {duk_s:>12} {dphi_s:>12} {'Run '+str(cr):>8}")
        L.append("")

        L += [
            "PHASE 2 — ABSOLUTE STRUCTURAL INTEGRITY FILTER  (vs. HM M_MSE)", DASH,
            f"  I(C) = [e_tr(C) > e_val(C)]  e=sqrt(MAE*sqrt(MSE))  [P2]",
            f"  G(C) = [ratio_c <= ratio_ref+eps_F]  ratio_ref={pipeline.ratio_ref:.6f}  [P1-final]",
            "",
        ]
        hdr2 = f"  {'Scout':<30} {'[Code] Case':<14} {'U_k(C)':>8} {'Delta%':>7} {'ratio_c':>8} {'I':>3} {'G':>3} {'Verdict':>12}"
        L += [hdr2, "  " + "─" * 94]

        for idx in all_cand_rows:
            row   = df.loc[idx]
            scout = str(row['Scout_Base'])
            short = str(row.get('F2_Short', '—'))
            case  = str(row.get('F2_Case',  '—'))
            fw    = str(row.get('Framework_Winner', '—'))
            uk_c  = float(row['U_MAXP_k'])
            delta = (uk_c - pipeline.uk_hm) / (pipeline.uk_hm + 1e-12) * 100.0
            
            rc    = row.get('F2_ratio_c')
            i_s   = str(row.get('F2_I'))[0] if pd.notna(row.get('F2_I')) else '—'
            g_s   = str(row.get('F2_G'))[0] if pd.notna(row.get('F2_G')) else '—'
            rc_s  = f"{float(rc):.4f}" if pd.notna(rc) else '    —'
            
            verd  = '>>>DGDTL' if fw in ('DGDTL','DGDTL_RT','DGDTL_TIE1','DGDTL_TIE2','DGDTL_TIE_WIN', 'DGDTL_VBD_WIN') else 'BASELINE'
            L.append(f"  {scout:<30} [{short}] {case:<7}  {uk_c:>8.4f} {delta:>+7.1f}% {rc_s:>8} {i_s:>3} {g_s:>3} {verd:>12}")
        L.append("")

        L += ["PHASE 3 — POST-HOC DUAL TIE-BREAK", DASH]
        if pipeline.phase3_active:
            L.append("  [STATUS] : ACTIVE — Tie-break protocol executed.")
        else:
            L.append("  [STATUS] : INACTIVE — No tie-break required (clear dominance or single candidate).")

        if pipeline.tie_break_log and len(pipeline.tie_break_log) > 0:
            L.extend(pipeline.tie_break_log)
        L.append("")

        L += ["PHASE 4 — OBSERVABLE DOMINANCE AUDIT  (champion vs. BL_RT)", DASH]
        fa_row = next((df.loc[idx] for idx in dgdtl_winners if str(df.loc[idx].get('FA_Case', '')).startswith('FA.')), None)

        if not pipeline.has_retrain:
            L.append("  [~] BL_RT not present in input — Phase 4 skipped.")
        elif fa_row is not None:
            fa_case  = str(fa_row.get('FA_Case',  '—'))
            fa_short = str(fa_row.get('FA_Short', '—'))
            fa_label = str(fa_row.get('FA_Label', '—'))
            fa_i     = str(fa_row.get('FA_I_RT',  '—'))
            fa_j     = str(fa_row.get('FA_J_RT',  '—'))

            def _f(v, fmt='.6f'): return f"{float(v):{fmt}}" if pd.notna(v) else '—'
            ev_c_s, ev_rt_s = _f(fa_row.get('FA_ev_c')), _f(fa_row.get('FA_ev_rt'))
            delta_s  = f"{float(fa_row.get('FA_delta_ev_pct')):+.2f}%" if pd.notna(fa_row.get('FA_delta_ev_pct')) else '—'
            phi_c_s, phi_rt_s = _f(fa_row.get('FA_phi_c')), _f(fa_row.get('FA_phi_rt'))

            L += [
                f"  [{fa_short}] {fa_case} — {VerdictCodes.PHASE4[fa_case][1]}",
                f"  Narrative: {fa_label}",
                f"  I_RT : e_val(C)={ev_c_s}  vs  e_val(BL_RT)={ev_rt_s}  Delta={delta_s}  [{fa_i}]",
                f"  J_RT : phi(C) ={phi_c_s}  vs  phi(BL_RT) ={phi_rt_s}  [{fa_j}]",
                "",
            ]
        else:
            L.append("  [~] No active DGDTL candidates — Phase 4 not applicable.")
        L.append("")

        L += ["TOP DGDTL CANDIDATES — FINAL FILTERED RANKING", DASH]

        if not dgdtl_winners:
            # ---------------------------------------------------------------
            # FALLBACK OUTPUT — Case A / Case B
            # Activated when the baseline is retained (all scouts fail Gate 1
            # or K_valid = ∅). This block does not modify the protocol; it
            # reports either the best DGDTL-LTS candidate (Case A) or K_valid = ∅
            # (Case B) for transparency.
            # ---------------------------------------------------------------

            # --- Crown the winning baseline ---
            L.append(f"  ★  CHAMPION DEPLOYED  : {pipeline.label_hm}")
            L.append(f"     U_MAXP_k = {pipeline.uk_hm:.6f}  (Hard-Mode reference)")
            for _, bl_row in df_base.iterrows():
                bl_label = str(bl_row['Candidate_Label'])
                bl_uk    = float(bl_row['U_MAXP_k'])
                bl_sde   = float(bl_row['SDE_b'])
                bl_ev    = float(bl_row['E_Valid'])
                bl_et    = float(bl_row['E_Train'])
                marker   = "  ►" if bl_label == pipeline.label_hm else "   "
                L.append(f"{marker}  {bl_label:<35}  U_k={bl_uk:.6f}  SDE_b={bl_sde:.4f}  e_val={bl_ev:.6f}  e_tr={bl_et:.6f}")
            L.append("")

            # --- Case A vs Case B ---
            # K_valid candidates: any row in df_cands not marked BASELINE,
            # regardless of SDE_b, GCI, A_emp or degree of topological collapse.
            dgdtl_cands_all = pipeline.df_cands[
                ~pipeline.df_cands['Scout_Base'].str.contains('BASELINE', na=False)
            ].copy()

            if dgdtl_cands_all.empty:
                # Case B — K_valid = ∅
                L.append("  [CASE B — K_valid = ∅]  The exploration produced no valid DGDTL-LTS solution.")
                L.append("  No diagnostic candidate available. Baseline deployment is the only result.")
            else:
                # Case A — K_valid ≠ ∅, Gate 1 failed for all.
                # Best diagnostic candidate = argmax U_MAXP_k over K_valid.
                best_diag_idx = dgdtl_cands_all['U_MAXP_k'].astype(float).idxmax()
                best_diag     = dgdtl_cands_all.loc[best_diag_idx]
                bd_uk   = float(best_diag['U_MAXP_k'])
                bd_sde  = float(best_diag['SDE_b'])
                bd_gci  = float(best_diag['GCI'])
                bd_aemp = float(best_diag['A_emp'])
                bd_kap  = float(best_diag['Kappa'])
                bd_phi  = float(best_diag['phi'])
                bd_ev   = float(best_diag['E_Valid'])
                bd_et   = float(best_diag['E_Train'])
                bd_sc   = str(best_diag['Scout_Base'])
                bd_run  = best_diag.get('Run_ID', '—')
                bd_gap  = (bd_uk - pipeline.uk_hm) / (pipeline.uk_hm + 1e-12) * 100.0
                bd_mae  = float(best_diag['MAE_Valid'])
                bd_mse  = float(best_diag['MSE_Valid'])

                L.append("  [CASE A — K_valid ≠ ∅]  Gate 1 not cleared. Best DGDTL-LTS diagnostic candidate:")
                L.append(f"")
                L.append(f"  ◈  DIAGNOSTIC CANDIDATE  : {bd_sc}  Run {bd_run}")
                L.append(f"     U_MAXP_k = {bd_uk:.6f}  (Gap vs HM: {bd_gap:+.2f}%  — did not clear Hard-Mode)")
                L.append(f"     SDE_b={bd_sde:.4f}  GCI={bd_gci:.4f}  A_emp={bd_aemp:.4f}  kappa={bd_kap:.4f}  phi={bd_phi:.6f}")
                L.append(f"     e_val={bd_ev:.6f}  e_tr={bd_et:.6f}  MAE_val={bd_mae:.6f}  MSE_val={bd_mse:.6f}")
                L.append(f"")
                L.append(f"  [!] Reported as-is. No quality filter applied. For analyst use only.")
                L.append(f"      Baseline remains the deployed champion per protocol.")

                # Show remaining K_valid candidates ranked by U_MAXP_k
                other_cands = dgdtl_cands_all.drop(index=best_diag_idx).sort_values(
                    by='U_MAXP_k', ascending=False
                )
                if not other_cands.empty:
                    L.append(f"")
                    L.append(f"  All K_valid DGDTL-LTS candidates (ranked by U_MAXP_k):")
                    for rank_i, (cidx, crow) in enumerate(
                        [(best_diag_idx, best_diag)] +
                        list(other_cands.iterrows()), 1
                    ):
                        marker = "  ◈" if cidx == best_diag_idx else "   "
                        L.append(
                            f"{marker} #{rank_i}  {str(crow['Scout_Base']):<30}  Run {crow.get('Run_ID','—')}"
                            f"  U_k={float(crow['U_MAXP_k']):.6f}"
                            f"  SDE_b={float(crow['SDE_b']):.4f}"
                            f"  GCI={float(crow['GCI']):.4f}"
                            f"  A_emp={float(crow['A_emp']):.4f}"
                            f"  phi={float(crow['phi']):.6f}"
                        )
        else:
            for rank, idx in enumerate(dgdtl_winners, 1):
                row  = df.loc[idx]
                sc   = str(row['Scout_Base'])
                rc   = row.get('Run_ID')
                uk_c = float(row['U_MAXP_k'])
                dlt  = (uk_c - pipeline.uk_hm) / (pipeline.uk_hm + 1e-12) * 100.0
                r_c  = float(row.get('F2_ratio_c', 0) or 0)
                f2s, f2c  = str(row.get('F2_Short', '')), str(row.get('F2_Case',  ''))

                L.append(f"\n  #{rank}  {sc}  Run {rc}  U_k={uk_c:.6f}  Delta={dlt:+.2f}%  [{f2s}] {f2c}")
                L.append(f"       SDE_b={float(row['SDE_b']):.4f}  GCI={float(row['GCI']):.4f}  A_emp={float(row['A_emp']):.4f}  kappa={float(row['Kappa']):.4f}  phi={float(row['phi']):.6f}")
                L.append(f"       e_val={float(row['E_Valid']):.6f}  e_tr={float(row['E_Train']):.6f}  ratio_c={r_c:.6f}  ratio_ref={pipeline.ratio_ref:.6f}")
                L.append(f"       MAE_val={float(row['MAE_Valid']):.6f}  MSE_val={float(row['MSE_Valid']):.6f}  Ambition={float(row['Ambition']):.4f}  Gap={float(row['Gap']):.4f}")
                L.append(f"       Psi={float(row['Psi']):.8f}  Regime={str(row['Regime'])}  psi_G={float(row['psi_G']):.6f}")

                _skip = {'Rank','Candidate_Label','Scout_Base','Run_ID','U_MAXP_k','Kappa','U_MAXP','SDE_b','GCI','A_emp','Phi_emp','e_max_R','f_eff','phi','rho','h_cont','E_Valid','E_Train','Baseline_E_val','MAE_Valid','MSE_Valid','MAE_Train','MSE_Train','Max_Err','Ambition','Gap','Surrogate_Coherent','Psi', 'Regime', 'psi_G', 'Is_Final_Champion', 'ICV', 'Psi_Rank', 'VBD_Verdict'}
                coeff_cols = [c for c in df.columns if c not in _skip and not c.startswith('F') and not c.startswith('FA') and c not in ('Champion_Run', 'Framework_Winner')]
                if coeff_cols:
                    parts = [f"{c}={float(row[c]):.6f}" for c in coeff_cols if pd.notna(row.get(c))]
                    if parts:
                        L.append(f"       Coefficients: {'  '.join(parts)}")

        L.append("")

        n_scouts = len(df.loc[all_cand_rows, 'Scout_Base'].unique())
        winning_scouts = set(df.loc[dgdtl_winners, 'Scout_Base'])
        n_winning_scouts = len(winning_scouts)

        # Fallback classification for summary
        if not dgdtl_winners:
            dgdtl_cands_all = pipeline.df_cands[
                ~pipeline.df_cands['Scout_Base'].str.contains('BASELINE', na=False)
            ]
            fallback_line = (
                f"  Fallback Case             : CASE B — K_valid = ∅  (no valid DGDTL-LTS solution found)"
                if dgdtl_cands_all.empty else
                f"  Fallback Case             : CASE A — K_valid ≠ ∅  (Gate 1 failed; diagnostic candidate shown above)"
            )
            champion_line = f"  Champion Deployed         : {pipeline.label_hm}  [BASELINE — protocol decision]"
        else:
            fallback_line = "  Fallback Case             : N/A — DGDTL-LTS champion certified by protocol"
            champion_label = str(df.loc[dgdtl_winners[0], 'Scout_Base'])
            champion_line  = f"  Champion Deployed         : {champion_label}  [DGDTL-LTS]"

        ratio_note = '> 1 — natural val/train asymmetry (domain property)' if pipeline.ratio_ref > 1 else '< 1 — inverted natural asymmetry (domain property)'

        L += [
            DASH, "EXECUTIVE SUMMARY", DASH,
            f"  Scouts Evaluated          : {n_scouts}",
            f"  DGDTL candidates passing  : {len(dgdtl_winners)} (from {n_winning_scouts} distinct scouts)",
            f"  Baseline dominant scouts  : {n_scouts - n_winning_scouts}",
            champion_line,
            fallback_line,
            "",
            "  FORMAL CORRECTIONS APPLIED:",
            "    P1-final  G(C)=[ratio_c<=ratio_ref+eps_F]",
            "    P2        I(C)=[e_tr(C)>e_val(C)]  e=sqrt(MAE*sqrt(MSE))",
            f"    P3        eps_F={FrameworkConfig.EPS_F}  [Delta_phi_min=1e-12, margin=1e8x]",
            f"    P4        thr_adp=max(eps_F,{FrameworkConfig.DELTA_REL}*phi_A)  [adaptive phi threshold]",
            f"    P5/P6     eps_tie={FrameworkConfig.EPS_TIE*100:.0f}%  [Delta_tie=0.35%(Max Tie), Delta_min=6.1%(Min Win)]",
            "    P7/TSA    F2.2-RT sub-verdict: DGDTL>BL_TR but BL_RT scope advisory.",
            "    P8/DOA    Phase-4 audit: DAC/DAE/DPO/ROS certification vs BL_RT.",
            "    F1-VB     Parallel Branch for Validation Bias Divergence via Psi metric.",
            "    Phase 3a  Post-Hoc Dual Tie-Break upgraded to U_comp structural metric.",
            "    P3b/EVT   Intra-scout tie-break via E_inc & EVT Guardrail (Hyperbolic Factor).",
            "",
            "  EPISTEMOLOGICAL NOTES:",
            "    TRG(F2.2): DGDTL constraints displaced solution outside training minimum.",
            "    STD(F2.3): pure Pareto dominance — lower error AND better integrity.",
            "    DAC(FA.1): if test degrades -> cause is OOD shift, not selection error.",
            "    DAE(FA.2): J_RT=False expected in symmetric domains (ratio_ref~1).",
            f"    ratio_ref {ratio_note}",
            SEP,
        ]

        with open(pipeline.output_txt, 'w', encoding='utf-8') as fh: 
            fh.write('\n'.join(L))


class DGDTLPipeline:
    """Hunter adapter for the reference StructuralSelectionProtocol."""

    def __init__(self, df: pd.DataFrame, output_csv: str, output_txt: str,
                 source_name: str = "In-Memory Hunter Engine"):
        self.df = df.copy()
        self.input_csv = source_name
        self.source_name = source_name
        self.output_csv = output_csv
        self.output_txt = output_txt
        self.line_label = ""

        # Initialize compatibility attributes consumed by FrameworkReportBuilder.
        self.df_cands = None
        self.df_base = None
        self.tr_only = None
        self.rt_rows = None
        self.dgdtl_winners = []
        self.uk_hm = 0.0
        self.label_hm = ""
        self.e_ref_val = 0.0
        self.e_ref_tr = 0.0
        self.ratio_ref = 0.0
        self.uk_retrain = 0.0
        self.has_retrain = False
        self.phase3_active = False
        self.tie_break_log = []
        self.f1_vb_active = False
        self.f1_vb_data = {}
        self.pi_vbd = 0.0

        self._protocol = StructuralSelectionProtocol(
            df=self.df, source_name=source_name, logger=TerminalLogger
        )

    def _sync_protocol_state(self):
        p = self._protocol
        self.df = p.df
        for name in (
            'df_cands', 'df_base', 'tr_only', 'rt_rows', 'dgdtl_winners',
            'uk_hm', 'label_hm', 'e_ref_val', 'e_ref_tr', 'ratio_ref',
            'uk_retrain', 'has_retrain', 'phase3_active', 'tie_break_log',
            'f1_vb_active', 'f1_vb_data', 'pi_vbd'
        ):
            setattr(self, name, getattr(p, name))

    def execute(self):
        TerminalLogger.title(
            "DGDTL STRUCTURAL SELECTION FRAMEWORK v1.0.0 (OOP)",
            f"Source: {self.source_name}"
        )
        df_final = self._protocol.execute()
        self._sync_protocol_state()

        df_final.to_csv(self.output_csv, index=False)
        TerminalLogger.success(f"[✓] FINAL CSV : {self.output_csv}")

        FrameworkReportBuilder.generate_txt(self)
        TerminalLogger.success(f"[✓] TXT       : {self.output_txt}\n")
        return df_final


class FinalFrameworkAuditor:
    """Adapter class bridging the Optuna Hunter orchestrator and the Structural Selection Protocol."""
    
    @staticmethod
    def execute(records: List[ScoutRecord], baseline: BaselineMetrics, config: HunterConfig, out_dir: str, elapsed_total: str):
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*80}\nFINAL U-MAXP STRUCTURAL SELECTION AUDIT \n{'='*80}{Colors.ENDC}")
        
        _sf = config.stats_y['std'] if config.stats_y else 1.0
        df_rows = []
        for r in records:
            for run_id in [1, 2]:
                is_r1 = (run_id == 1)
                mae_v = r.mae_r1 if is_r1 else r.mae_r2
                mse_v = r.mse_r1 if is_r1 else r.mse_r2
                mae_t = r.mae_tr_r1 if is_r1 else r.mae_tr_r2
                mse_t = r.mse_tr_r1 if is_r1 else r.mse_tr_r2
                if not (0 < mse_v < float('inf')) or not (0 < mae_t < float('inf')): continue
                
                e_v = UMaxPCriterion.composite_error(mae_v, mse_v)
                e_t = UMaxPCriterion.composite_error(mae_t, mse_t)
                e_base = UMaxPCriterion.composite_error(baseline.baseline_mae_val_nat, baseline.base_mse_val_nat)
                e_base_tr = UMaxPCriterion.composite_error(baseline.baseline_mae_train_nat, baseline.base_mse_train_nat)
                
                rho = UMaxPCriterion.cauchy_rho(e_v, e_t, e_base, e_base_tr)
                phi = UMaxPCriterion.cauchy_phi_from_rho(rho)
                
                is_base = "BASELINE" in r.label
                u_map = r.u_r1 if is_r1 else r.u_r2
                tau_nat = baseline.truth_anchor * _sf
                emax_rob = r.emax_rob_r1 if is_r1 else r.emax_rob_r2
                kappa = UMaxPCriterion.compute_kappa(tau_nat, emax_rob, is_baseline=is_base)
                
                max_err = r.max_err_r1 if is_r1 else r.max_err_r2
                phi_emp = r.phi_emp_r1 if is_r1 else r.phi_emp_r2
                f_eff = UMaxPCriterion.compute_f_eff(e_v, e_base)
                h_cont = UMaxPCriterion.compute_h_cont(max_err, baseline.e_gm * _sf)
                surrogate_coherent = bool(e_v < e_base and phi >= 1.0)

                df_rows.append({
                    'Candidate_Label': f"{r.label}_R{run_id}" if not is_base else r.label,
                    'Scout_Base': r.label, 
                    'Run_ID': run_id if not is_base else 0,
                    'U_MAXP_k': UMaxPCriterion.compute_umaxp_k(u_map, kappa), 
                    'Kappa': kappa, 
                    'U_MAXP': u_map, 
                    'SDE_b': r.sde_r1 if is_r1 else r.sde_r2,
                    'GCI': r.gci_r1 if is_r1 else r.gci_r2, 
                    'A_emp': r.a_emp_r1 if is_r1 else r.a_emp_r2,
                    'Phi_emp': phi_emp,
                    'e_max_R': emax_rob,
                    'f_eff': f_eff,
                    'phi': phi,
                    'rho': rho,
                    'h_cont': h_cont,
                    'E_Valid': e_v, 
                    'E_Train': e_t, 
                    'Baseline_E_val': e_base,
                    'MAE_Valid': mae_v, 
                    'MSE_Valid': mse_v,
                    'MAE_Train': mae_t, 
                    'MSE_Train': mse_t, 
                    'Max_Err': max_err,
                    'Ambition': r.ambition, 
                    'Gap': r.gap,
                    'Surrogate_Coherent': surrogate_coherent
                })

        df_raw = pd.DataFrame(df_rows)
        if df_raw.empty:
            print(f"{Colors.RED}No valid data for Framework execution.{Colors.ENDC}")
            return

        csv_path = os.path.join(out_dir, "UMaxP_Ranking_Framework.csv")
        txt_path = os.path.join(out_dir, "UMaxP_Framework_Report.txt")

        # Hand over control to the rigorous OOP Pipeline
        pipeline = DGDTLPipeline(df=df_raw, output_csv=csv_path, output_txt=txt_path)
        pipeline.execute()


# =============================================================================
# MAIN APPLICATION APP
# =============================================================================

class DGDTLHunterApp:
    def __init__(self, args: argparse.Namespace):
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*80}\nDGDTL-LTS HUNTER v1.0.0 - CLUSTER AUTOMATED ENGINE\n{'='*80}{Colors.ENDC}")
        self.start_time = time.time()
        self.out_dir = args.out_dir
        if not os.path.exists(self.out_dir): os.makedirs(self.out_dir)
        self.all_records: List[ScoutRecord] = []  
        
        try:
            self.df_train = pd.read_csv(args.train)
            self.df_valid = pd.read_csv(args.valid)
            print(f"{Colors.GREEN}✓ Datasets loaded:\n  - Training:   {len(self.df_train)} samples\n  - Validation: {len(self.df_valid)} samples{Colors.ENDC}")
        except Exception as e:
            sys.exit(f"{Colors.RED}Data Loading Error: {e}{Colors.ENDC}")

        base_feats = self.df_train.columns[1:-1].tolist()
        target = self.df_train.columns[-1]
        
        print(f"\n{Colors.GREEN}✓ Variables identified:\n  - Target:       {target}\n  - Predictors: {base_feats}{Colors.ENDC}")
        
        self.config = ClusterSetup.run(self.df_train, base_feats, target, args)
        self.env = DataEnvironment(self.df_train, self.df_valid, base_feats, target, self.config)
        self.baseline = BaselineEvaluator.calculate(self.env, self.config)

        rec_base_train = ScoutRecord(
            label="BASELINE_TRAIN_ONLY", loop_id=0, scout_level=0, is_gm=False, verdict_r1="BASELINE", verdict_r2="BASELINE",
            mae_r1=self.baseline.baseline_mae_val_nat, mae_r2=0.0, mse_r1=self.baseline.base_mse_val_nat, mse_r2=0.0,
            mae_tr_r1=self.baseline.baseline_mae_train_nat, mae_tr_r2=0.0, mse_tr_r1=self.baseline.base_mse_train_nat, mse_tr_r2=0.0,
            max_err_r1=self.baseline.max_train_real, max_err_r2=0.0, sde_r1=self.baseline.sde_train, sde_r2=0.0,
            gci_r1=self.baseline.base_gci_train, gci_r2=0.0, u_r1=self.baseline.base_u_train_raw, u_r2=0.0,
            a_emp_r1=self.baseline.a_emp_train, a_emp_r2=0.0, phi_emp_r1=self.baseline.phi_emp_train, phi_emp_r2=0.0,
            emax_rob_r1=self.baseline.emax_robusto_train, emax_rob_r2=0.0, coeffs_r1=list(self.baseline.base_coeffs), coeffs_r2=[],
            ambition=1.0, gap=0.0, threshold_train=0.0, threshold_valid=0.0, anchor_used=self.baseline.truth_anchor, elapsed="00:00:00", trial_number=-1)

        rec_base_retrain = ScoutRecord(
            label="BASELINE_RETRAIN", loop_id=0, scout_level=0, is_gm=False, verdict_r1="BASELINE", verdict_r2="BASELINE",
            mae_r1=0.0, mae_r2=self.baseline.mae_retrain_nat, mse_r1=0.0, mse_r2=self.baseline.mse_retrain_nat,
            mae_tr_r1=0.0, mae_tr_r2=self.baseline.mae_retrain_nat, mse_tr_r1=0.0, mse_tr_r2=self.baseline.mse_retrain_nat,
            max_err_r1=0.0, max_err_r2=self.baseline.max_retrain_real, sde_r1=0.0, sde_r2=self.baseline.sde_retrain,
            gci_r1=0.0, gci_r2=self.baseline.base_gci_retrain, u_r1=0.0, u_r2=self.baseline.base_u_retrain_raw,
            a_emp_r1=0.0, a_emp_r2=self.baseline.a_emp_retrain, phi_emp_r1=0.0, phi_emp_r2=self.baseline.phi_emp_retrain,
            emax_rob_r1=0.0, emax_rob_r2=self.baseline.emax_robusto_retrain, coeffs_r1=[], coeffs_r2=list(self.baseline.retrain_coeffs),
            ambition=1.0, gap=0.0, threshold_train=0.0, threshold_valid=0.0, anchor_used=self.baseline.truth_anchor, elapsed="00:00:00", trial_number=-1)

        self.all_records.extend([rec_base_train, rec_base_retrain])

    def run(self):
        loops = [{'id': 1, 'ambition': 1.0, 'status': 'STRICT'}, {'id': 2, 'ambition': 1.2, 'status': 'EXPANDED'}]
        
        for current_loop in loops:
            l_id, l_amb, l_st = current_loop['id'], current_loop['ambition'], current_loop['status']
            print(f"\n{Colors.BOLD}>>> STARTING {l_st} LOOP (Ambition Ceiling: {l_amb}) <<<{Colors.ENDC}")
            
            current_level = 1
            while current_level <= 4:
                optimizer = DGDTLOptimizer(self.env, self.baseline, l_id)
                scout_res = optimizer.run_scout(start_attempt=current_level, ambition_ceil=l_amb)
                
                if not scout_res.get('success'):
                    print(f"\n{Colors.YELLOW}[!] EXPLORATION FAILED. TRIGGERING GM RESCUE.{Colors.ENDC}")
                    v_study = optimizer.run_gm_valve_grid(None, (0, 50), l_amb, 0.3, 4)
                    elapsed_fail = time.strftime("%H:%M:%S", time.gmtime(time.time() - self.start_time))
                    _, _, _recs = ReportGenerator.generate(self.config, self.baseline, v_study, elapsed_fail, self.out_dir, 4, f"L{l_id}_FAIL_GM", self.baseline.e_gm, True, l_st)
                    if _recs: self.all_records.extend(_recs)
                    
                    if l_id == 1:
                        print(f"    {Colors.YELLOW}>> Auto-advancing to EXPANDED Loop 2 (Ambition 1.2).{Colors.ENDC}")
                        break
                    else:
                        FinalFrameworkAuditor.execute(self.all_records, self.baseline, self.config, self.out_dir, elapsed_fail)
                        return

                winning_level = scout_res['attempt']
                siege_conf = optimizer.diagnose(scout_res, l_amb)
                final_study = optimizer.run_siege(siege_conf, winning_level)
                
                elapsed_siege = time.strftime("%H:%M:%S", time.gmtime(time.time() - self.start_time))
                s1, s2, _recs = ReportGenerator.generate(self.config, self.baseline, final_study, elapsed_siege, self.out_dir, winning_level, f"L{l_id}", loop_status=l_st)
                if _recs: self.all_records.extend(_recs)
                
                try:
                    mse_r1 = final_study.best_trial.user_attrs.get('mse_vldt_r1', float('inf'))
                    mse_r2 = final_study.best_trial.user_attrs.get('mse_vldt_r2', float('inf'))
                except ValueError:
                    mse_r1, mse_r2 = float('inf'), float('inf')
                
                if mse_r1 >= self.baseline.ref_mse_active or mse_r2 >= self.baseline.ref_mse_active:
                    print(f"\n{Colors.RED}[!] ESCAPE VALVE: Triggering GM Grid (MSE limit breached).{Colors.ENDC}")
                    gm_study = optimizer.run_gm_valve_grid(final_study.best_trial, scout_res['dw_range'], l_amb, scout_res['gap_max'], winning_level)
                    elapsed_gm = time.strftime("%H:%M:%S", time.gmtime(time.time() - self.start_time))
                    _, _, _recs = ReportGenerator.generate(self.config, self.baseline, gm_study, elapsed_gm, self.out_dir, winning_level, f"L{l_id}_GM", self.baseline.e_gm, True, l_st)
                    if _recs: self.all_records.extend(_recs)
                    current_level = winning_level + 1
                
                elif s1 >= s2 or (np.abs(s1 - s2) / max(s1, s2, 1e-9)) * 100 < 2.5:
                    print(f"\n{Colors.YELLOW}[!] OVERFITTING SIGNAL. Auto-advancing Scout.{Colors.ENDC}")
                    current_level = winning_level + 1
                    
                else:
                    print(f"\n{Colors.GREEN}✅ CLEAN CONVERGENCE ACHIEVED.{Colors.ENDC}")
                    print(f"    {Colors.CYAN}>> [AUTO] Exploring GM Grid for flatter minima (simulating Y).{Colors.ENDC}")
                    tac_study = optimizer.run_gm_valve_grid(final_study.best_trial, scout_res['dw_range'], l_amb, scout_res['gap_max'], winning_level)
                    elapsed_tac = time.strftime("%H:%M:%S", time.gmtime(time.time() - self.start_time))
                    _, _, _recs = ReportGenerator.generate(self.config, self.baseline, tac_study, elapsed_tac, self.out_dir, winning_level, f"L{l_id}_TACTICAL_GM", self.baseline.e_gm, True, l_st)
                    if _recs: self.all_records.extend(_recs)

                    if winning_level < 4:
                        print(f"    {Colors.CYAN}>> [AUTO] Continuing to Scout {winning_level + 1} (simulating choice=1).{Colors.ENDC}")
                        current_level = winning_level + 1
                    else:
                        print(f"    {Colors.GREEN}>> Maximum Scout level (4) reached for this loop.{Colors.ENDC}")
                        current_level = 5

            if current_level > 4:
                if l_id == 1:
                    print(f"    {Colors.CYAN}>> [AUTO] Auto-advancing to EXPANDED Loop 2 (simulating Y).{Colors.ENDC}")
                else:
                    print(f"    {Colors.YELLOW}>> Maximum Scout level (4) reached in final loop.{Colors.ENDC}")

        FinalFrameworkAuditor.execute(self.all_records, self.baseline, self.config, self.out_dir, time.strftime("%H:%M:%S", time.gmtime(time.time() - self.start_time)))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DGDTL-LTS U-MAXP Hunter - Cluster Automated Engine v1.0.0")
    parser.add_argument('--train', default=TRAIN_PATH, help="Path to training data CSV")
    parser.add_argument('--valid', default=VALID_PATH, help="Path to validation data CSV")
    parser.add_argument('--out-dir', default=OUTPUT_DIR, help="Output directory")
    parser.add_argument('--mode', default='raw', choices=['raw', 'error_matrix'], help="Model mode")
    parser.add_argument('--no-intercept', action='store_true', help="Disable intercept fitting")
    parser.add_argument('--beta-sum-one', action='store_true', help="Constrain betas to sum to 1")
    parser.add_argument('--formulas', nargs='*', default=[], help="List of custom formulas for feature engineering (e.g., 'A * B')")
    parser.add_argument('--no-norm-x', action='store_true', help="Disable predictor normalization")
    parser.add_argument('--norm-y', action='store_true', help="Enable target normalization")

    args = parser.parse_args()

    try:
        app = DGDTLHunterApp(args)
        app.run()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Process interrupted by user.{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}A critical error occurred:{Colors.ENDC}")
        traceback.print_exc()
        sys.exit(1)
