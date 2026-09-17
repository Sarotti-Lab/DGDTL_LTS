# SPDX-FileCopyrightText: 2026 José A. Pérez
# SPDX-License-Identifier: MIT

"""
DGDTL-LTS Core Engine
Dynamic Generalization-Driven Transfer Learning Estimator 
=========================================================

Abstract:
---------
This engine implements the DGDTL-LTS
(Dynamic Generalization-Driven Transfer Learning Local Topological Stability)
regression algorithm. It is designed to solve ill-conditioned inverse
problems in computational chemistry and physics, where feature
collinearity and hardware-specific floating-point drift may compromise
numerical reproducibility.

Key Architectural Features:
---------------------------
1. High-Fidelity Anchor Stabilization
   Implements a quantization barrier (4-decimal precision) between
   optimization phases to filter hardware-induced floating-point noise
   while preserving solution-landscape topology.

2. Deterministic Bridge
   Run 2 (Topological Refinement Phase or Focused) boundaries are derived strictly from
   stabilized Run 1 (Exploration Phase) anchors, enforcing deterministic
   cross-platform refinement boundaries.

3. Robust Dynamics
   Maintains dynamic search-space overlap to mitigate premature
   convergence to local minima, safeguarded by controlled numerical
   quantization.

4. Symmetric Constraints
   Enforces absolute-error boundaries to prevent sign-biased
   optimization.

Usage:
------
Designed for scikit-learn compatibility. The engine can be used as a
standalone estimator or integrated into higher-level orchestration
workflows.

Author:
-------
DGDTL Research Team
Prof. José A. Pérez (JP)

Copyright:
----------
Copyright (c) 2026 José A. Pérez.

License:
--------
MIT License. See the LICENSE file distributed with this package.
"""

import os

# --- CRITICAL REPRODUCIBILITY SETTINGS ---
# Enforce single-threaded execution for linear algebra libraries to prevent
# non-deterministic thread switching behaviors in multi-core environments.
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['VECLIB_MAXIMUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

import numpy as np
import pandas as pd
from scipy.optimize import minimize, OptimizeWarning
from scipy.stats import shapiro
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.utils.validation import check_is_fitted
from joblib import Parallel, delayed, parallel_backend
import warnings
from typing import Dict, Optional, Tuple, Any, List

# Configuration for display and warnings
np.set_printoptions(precision=4, suppress=True)
warnings.filterwarnings("ignore", category=OptimizeWarning)

__all__ = ["DGDTLEstimator"]

# =============================================================================
# DETERMINISTIC UTILITIES
# =============================================================================

def round_to_precision(value: float, decimals: int = 6) -> float:
    """
    Applies numerical quantization to enforce deterministic floating-point behavior.
    Acts as a low-pass filter for hardware-specific gradient noise.
    """
    return np.round(value, decimals)

def argmin_with_tiebreaker(arr: np.ndarray) -> int:
    """
    Deterministic argmin implementation.
    Returns the first index in case of ties, ensuring consistent selection order across platforms.
    """
    min_val = np.min(arr)
    return np.where(arr == min_val)[0][0]

def argmax_with_tiebreaker(arr: np.ndarray) -> int:
    """
    Deterministic argmax implementation.
    Returns the first index in case of ties, ensuring consistent selection order across platforms.
    """
    max_val = np.max(arr)
    return np.where(arr == max_val)[0][0]

# =============================================================================
# OPTIMIZATION WORKER (PARALLEL EXECUTION)
# =============================================================================

def _worker_optimization(args: Tuple) -> Tuple[int, Optional[np.ndarray]]:
    """
    Executes a single SLSQP optimization task within a specific feasibility tunnel.
    
    Parameters
    ----------
    args : Tuple
        Contains start_point, data matrices, constraints, and random seed.

    Returns
    -------
    Tuple[int, Optional[np.ndarray]]
        Returns the original job index and the optimized coefficients (or None if failed).
        The index is preserved to allow deterministic sorting of results.
    """
    # Re-enforce environment variables within the worker process
    os.environ['OPENBLAS_NUM_THREADS'] = '1'
    os.environ['OMP_NUM_THREADS'] = '1'
    
    start_point, X_data, y_data, params, mode, worker_seed, idx = args
    has_intercept = params.get('fit_intercept', False)
    
    # Initialize local deterministic RNG
    local_rng = np.random.default_rng(worker_seed)
    
    def objective(beta):
        """
        Objective Function (Loss).
        Minimizes Mean Squared Error (MSE) subject to diversity and tunnel constraints.
        Note: Internal rounding is disabled to preserve gradient smoothness for SLSQP.
        """
        # 1. Diversity Penalty (Regularization)
        div_weight = params.get('diversity_weight', 0.0)
        div_penalty = 0.0
        if div_weight > 0:
            if has_intercept:
                div_penalty = -div_weight * np.var(beta[1:])
            else:
                div_penalty = -div_weight * np.var(beta)
        
        # 2. MSE Calculation
        if mode == 'raw':
            pred = X_data @ beta
            mse = np.mean((pred - y_data)**2)
        else: 
            resultant_error = X_data @ beta
            mse = np.mean(resultant_error**2)

        # 3. Tunnel Penalty (Soft Lagrangian Constraint)
        # Penalizes solutions that drift outside the defined search tunnel [min_limit, max_limit]
        mse_penalty = max(0, params['mse_min_limit'] - mse) + max(0, mse - params['mse_max_limit'])
        
        return mse + div_penalty + mse_penalty

    # Constraint Definitions (Hard Constraints)
    constraints = []
    
    # Sum-to-One Constraint (Mixture Model Requirement)
    if params.get('beta_sum_one', True):
        if has_intercept:
            constraints.append({'type': 'eq', 'fun': lambda b: np.sum(b[1:]) - 1})
        else:
            constraints.append({'type': 'eq', 'fun': lambda b: np.sum(b) - 1})
    
    # Absolute Error Constraint (Outlier Control)
    thresh = params.get('constraint_threshold')
    if thresh is not None:
        if mode == 'raw':
            constraints.append({'type': 'ineq', 'fun': lambda b: thresh - np.max(np.abs(X_data @ b - y_data))})
        else:
            constraints.append({'type': 'ineq', 'fun': lambda b: thresh - np.max(np.abs(X_data @ b))})

    # Variable Bounds
    user_bounds = params.get('coeff_bounds') 
    int_bounds = params.get('intercept_bounds')
    
    if user_bounds:
        if has_intercept and int_bounds is not None:
            bounds = [int_bounds] + [user_bounds] * (len(start_point) - 1)
        else:
            bounds = [user_bounds] * len(start_point)
    else:
        bounds = None

    # Execute SLSQP Optimization
    try:
        res = minimize(
            objective, start_point, 
            constraints=constraints, bounds=bounds, method='SLSQP', 
            options={
                'disp': False, 
                'maxiter': params.get('max_iter', 100),
                'ftol': 1e-9 
            }
        )
        if res.success:
            # Return index and coefficients rounded to 6 decimals
            return idx, round_to_precision(res.x, decimals=6)
        else:
            return idx, None
    except (ValueError, RuntimeError, np.linalg.LinAlgError):
        return idx, None
    except Exception:
        return idx, None


# =============================================================================
# MAIN ESTIMATOR CLASS
# =============================================================================

class DGDTLEstimator(BaseEstimator, RegressorMixin):
    """
    Dynamic Generalization-Driven Transfer Learning (DGDTL) Estimator.
    
    Performs a two-phase optimization process (Exploration -> Topological Refinement or Focused) to find
    robust coefficients for linear models on collinear or ill-conditioned data.
    """
    
    def __init__(self, 
                 mode: str = 'raw', 
                 TOLERANCE_FACTOR: float = 0.1,
                 num_solutions_run1: int = 1000,
                 num_solutions_run2: int = 1000,
                 fit_intercept: bool = False,
                 beta_sum_one: bool = True,
                 coeff_bounds: Optional[Tuple[float, float]] = None,
                 intercept_bounds: Optional[Tuple[float, float]] = None,
                 VALIDATION_THRESHOLD: Optional[float] = None,
                 diversity_weight: float = 0.0,
                 constraint_threshold: Optional[float] = None,
                 shapiro_threshold: float = 0.05,
                 damping_factor: float = 200.0,
                 filter_limits: Optional[Dict[str, float]] = None,
                 random_state: Optional[int] = None,
                 n_jobs: int = -1,
                 verbose: bool = True):
        
        # Parameter Validation
        if coeff_bounds and coeff_bounds[0] > coeff_bounds[1]:
            raise ValueError(f"Invalid coeff_bounds: {coeff_bounds}. Lower bound must be <= Upper bound.")
        
        self.mode = mode
        self.TOLERANCE_FACTOR = TOLERANCE_FACTOR
        self.num_solutions_run1 = num_solutions_run1
        self.num_solutions_run2 = num_solutions_run2
        self.fit_intercept = fit_intercept
        self.beta_sum_one = beta_sum_one
        self.coeff_bounds = coeff_bounds
        self.intercept_bounds = intercept_bounds
        self.VALIDATION_THRESHOLD = VALIDATION_THRESHOLD
        self.diversity_weight = diversity_weight
        self.constraint_threshold = constraint_threshold
        self.shapiro_threshold = shapiro_threshold
        self.damping_factor = damping_factor
        self.filter_limits = filter_limits
        self.random_state = random_state
        self.n_jobs = n_jobs
        self.verbose = verbose
            
        # Internal State Attributes
        self.baseline_mse_ = None       
        self.baseline_coeffs_ = None    
        self.champion_ = None           
        self.is_fitted_ = False
        self._baseline_calculated = False
        
        # Solution Repositories
        self.run1_raw_ = []
        self.run1_unique_ = []
        self.run1_valid_ = []
        self.run1_report_df_ = None
        self.champion_run1_ = None
        self.run1_params_ = None
        
        self.run2_raw_ = []
        self.run2_unique_ = []
        self.run2_valid_ = []
        self.run2_report_df_ = None
        self.champion_run2_ = None
        self.run2_params_ = None

    def _log(self, message: str):
        if self.verbose: print(f"[DGDTL-{self.mode.upper()}] {message}")

    def _get_run_params(self):
        """Extracts hyperparameters for worker processes."""
        return {k: v for k, v in self.get_params().items() if not k.endswith('_')}

    def _prepare_data(self, X):
        """Augments data with intercept column if required."""
        if self.fit_intercept:
            ones = np.ones((X.shape[0], 1))
            return np.hstack((ones, X))
        return X

    def calibrate(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Runs a single baseline calibration optimization."""
        X_proc = self._prepare_data(X)
        self._log("Running baseline calibration...")
        self._fit_baseline(X_proc, y)
        return self.baseline_coeffs_

    def fit(self, X_train: np.ndarray, y_train: np.ndarray, 
            X_valid: np.ndarray, y_valid: np.ndarray):
        """
        Main training loop executing the two-phase DGDTL protocol.
        """
        # Input Validation
        if len(X_train) != len(y_train):
            raise ValueError(f"X_train and y_train size mismatch.")
        
        # Filter Limits Initialization
        if self.filter_limits is None:
            self.filter_limits_ = {'lower_limit': 1.05, 'upper_limit': 1.0 + abs(self.TOLERANCE_FACTOR)}
        elif self.filter_limits.get('upper_limit') is None:
            self.filter_limits_ = self.filter_limits.copy()
            self.filter_limits_['upper_limit'] = 1.0 + abs(self.TOLERANCE_FACTOR)
        else:
            self.filter_limits_ = self.filter_limits

        X_train_proc = self._prepare_data(X_train)
        X_valid_proc = self._prepare_data(X_valid)
        
        self._log(f"Training started. Shape: {X_train_proc.shape}. Intercept: {self.fit_intercept}")
        
        # ---------------------------------------------------------------------
        # PHASE 1: Baseline Calibration (Point of Reference)
        # ---------------------------------------------------------------------
        if not self._baseline_calculated:
            self._fit_baseline(X_train_proc, y_train)
        
        # Apply 6-decimal rounding for consistency
        self.baseline_mse_ = round_to_precision(self.baseline_mse_, decimals=6)
        self.baseline_coeffs_ = round_to_precision(self.baseline_coeffs_, decimals=6)
        
        # ---------------------------------------------------------------------
        # PHASE 2: Run 1 (Directional Exploration)
        # ---------------------------------------------------------------------
        tol = self.TOLERANCE_FACTOR
        limit_A = self.baseline_mse_
        limit_B = self.baseline_mse_ * (1 + tol)
        
        # Establish Global Exploration Boundaries
        min_lim_r1 = round_to_precision(max(0.0, min(limit_A, limit_B)), decimals=6)
        max_lim_r1 = round_to_precision(max(limit_A, limit_B), decimals=6)
        
        run1_params = self._get_run_params()
        run1_params.update({
            'num_solutions': self.num_solutions_run1,
            'mse_min_limit': min_lim_r1, 
            'mse_max_limit': max_lim_r1
        })
        self.run1_params_ = run1_params

        self._log(f"Run 1 | Tunnel: [{min_lim_r1:.6f} - {max_lim_r1:.6f}]")
        
        # Fixed Seeds for Determinism
        seed1 = 42
        seed2 = 43
        
        # Execute Parallel Search
        self.run1_raw_ = self._run_parallel_search(X_train_proc, y_train, run1_params, seed=seed1)
        self.run1_unique_, self.run1_valid_ = self._filter_and_validate(self.run1_raw_, X_train_proc, y_train, X_valid_proc, y_valid)
        
        if not self.run1_valid_:
            raise RuntimeError(f"Run 1: No solutions found in [{min_lim_r1:.6f}-{max_lim_r1:.6f}].")

        # Select Intermediate Champion
        self.champion_run1_, self.run1_report_df_ = self._select_champion_and_get_report(self.run1_valid_, X_train_proc, y_train, ref_mse=self.baseline_mse_)

        # ---------------------------------------------------------------------
        # PHASE 3: Run 2 (Topological Refinement or Focused)
        # ---------------------------------------------------------------------
        mse_values = np.array([s['MSE_train'] for s in self.run1_valid_])
        idx_min = argmin_with_tiebreaker(mse_values)
        idx_max = argmax_with_tiebreaker(mse_values)
        
        raw_min_mse = mse_values[idx_min]
        raw_max_mse = mse_values[idx_max]
        
        # [ANCHOR STABILIZATION LOGIC]
        # 1. Quantize Stable Minimum to 4 decimals (Fine Floor).
        # 2. Quantize Maximum to 4 decimals (High-Fidelity Ceiling).
        # This stripping of hardware noise (< 1e-4) guarantees identical Run 2 conditions.
        anchor_min = round_to_precision(raw_min_mse, decimals=4)
        anchor_max = round_to_precision(raw_max_mse, decimals=4)
        
        if self.verbose:
            print(f"[DGDTL-SYNC] High-Fidelity Anchors: Min={anchor_min:.4f}, Max={anchor_max:.4f}")
        
        # Calculate Refinement Boundaries
        tentative_min = (min_lim_r1 + anchor_min) / 2.0
        new_min_limit = max(0.0, min(tentative_min, max_lim_r1)) 
        
        if tol < 0:
            # Deep dive expansion logic
            new_max_limit = (new_min_limit + anchor_max) / 1.5 
        else:
            if self.baseline_mse_ > 0 and anchor_min > 0:
                # Proportional expansion
                new_max_limit = anchor_max * (new_min_limit / self.baseline_mse_)
            else:
                new_max_limit = new_min_limit * 1.5
        
        # Ensure minimal tunnel width
        if new_max_limit <= new_min_limit:
            new_max_limit = new_min_limit * 1.2

        # Finalize Run 2 Boundaries (6-decimal precision)
        new_min_limit = round_to_precision(new_min_limit, decimals=6)
        new_max_limit = round_to_precision(new_max_limit, decimals=6)

        run2_params = self._get_run_params()
        run2_params.update({
            'num_solutions': self.num_solutions_run2,
            'mse_min_limit': new_min_limit, 
            'mse_max_limit': new_max_limit
        })
        self.run2_params_ = run2_params
        
        self._log(f"Run 2 | Tunnel: [{new_min_limit:.6f} - {new_max_limit:.6f}]")
        
        # Execute Refined Search
        self.run2_raw_ = self._run_parallel_search(X_train_proc, y_train, run2_params, seed=seed2)
        self.run2_unique_, self.run2_valid_ = self._filter_and_validate(self.run2_raw_, X_train_proc, y_train, X_valid_proc, y_valid)
        
        # ---------------------------------------------------------------------
        # PHASE 4: Final Champion Selection
        # ---------------------------------------------------------------------
        is_fallback = not self.run2_valid_
        final_pool = self.run2_valid_ if self.run2_valid_ else self.run1_valid_
        
        self.champion_run2_, self.run2_report_df_ = self._select_champion_and_get_report(
            final_pool, X_train_proc, y_train, ref_mse=new_min_limit, is_fallback=is_fallback
        )
        
        self.champion_ = self.champion_run2_
        
        if self.champion_:
            self.is_fitted_ = True
            self._log(f"Champion Selected. Coeffs: {np.array(self.champion_['coeffs'])}")
        else:
            raise RuntimeError("Champion selection failed.")
            
        return self

    def predict(self, X: np.ndarray, y_reference: Optional[np.ndarray] = None, beta: Optional[np.ndarray] = None) -> np.ndarray:
        """Predicts target values using the champion coefficients."""
        check_is_fitted(self)
        X = np.atleast_2d(X)
        X_proc = self._prepare_data(X)
        coeffs = beta if beta is not None else self.champion_['coeffs']
        
        if X_proc.shape[1] != len(coeffs):
            raise ValueError(f"Feature mismatch: Model expects {len(coeffs)} features.")

        if self.mode == 'raw':
            return X_proc @ coeffs
        else:
            # Error Matrix Mode: Prediction = Reference + Correction
            if y_reference is None: raise ValueError("y_reference needed for error_matrix mode.")
            return y_reference + (X_proc @ coeffs)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Returns the R^2 score of the prediction."""
        from sklearn.metrics import r2_score
        y_pred = self.predict(X, y_reference=y if self.mode == 'error_matrix' else None)
        return r2_score(y, y_pred)

    # -------------------------------------------------------------------------
    # INTERNAL HELPER METHODS
    # -------------------------------------------------------------------------

    def _fit_baseline(self, X, y):
        """Calculates the initial reference point (Baseline) using a single minimization run."""
        n_feat = X.shape[1]
        ub = self.coeff_bounds
        int_b = self.intercept_bounds
        has_intercept = self.fit_intercept
        
        # Configure Bounds
        if ub:
            if has_intercept and int_b is not None:
                bounds = [int_b] + [ub] * (n_feat - 1)
            else:
                bounds = [ub] * n_feat
        else:
            bounds = None
        
        def obj(b): 
            return np.mean((X @ b - y)**2) if self.mode == 'raw' else np.mean((X @ b)**2)
        
        constraints = []
        if self.beta_sum_one:
            if has_intercept:
                constraints.append({'type': 'eq', 'fun': lambda b: np.sum(b[1:]) - 1})
            else:
                constraints.append({'type': 'eq', 'fun': lambda b: np.sum(b) - 1})
        
        # Deterministic Initialization
        rng = np.random.default_rng(42)
        if ub:
            if has_intercept and int_b is not None:
                x0_int = rng.uniform(int_b[0], int_b[1], 1)
                x0_feat = rng.uniform(ub[0], ub[1], n_feat - 1)
                x0 = np.concatenate([x0_int, x0_feat])
            else:
                x0 = rng.uniform(ub[0], ub[1], n_feat)
        else:
            x0 = rng.standard_normal(n_feat)
        
        x0 = round_to_precision(x0, decimals=6)
            
        res = minimize(obj, x0, constraints=constraints, bounds=bounds, method='SLSQP', options={'ftol': 1e-9, 'maxiter': 200})
        
        if res.success:
            self.baseline_mse_ = round_to_precision(res.fun, decimals=6)
            self.baseline_coeffs_ = round_to_precision(res.x, decimals=6)
        else:
            self.baseline_mse_ = 1e9 
            self.baseline_coeffs_ = np.zeros(n_feat)
        
        self._baseline_calculated = True

    def _run_parallel_search(self, X, y, run_params, seed):
        """Orchestrates parallel optimization tasks."""
        n_feat = X.shape[1]
        ub = self.coeff_bounds
        int_b = self.intercept_bounds
        has_intercept = self.fit_intercept
        
        master_rng = np.random.default_rng(seed)
        worker_seeds = master_rng.integers(0, 2**31 - 1, size=run_params['num_solutions'])
        
        tasks = []
        for i in range(run_params['num_solutions']):
            w_seed = int(worker_seeds[i])
            local_rng = np.random.default_rng(w_seed)
            
            # Generate Start Points
            if ub:
                if has_intercept and int_b is not None:
                    sp_int = local_rng.uniform(int_b[0], int_b[1], 1)
                    sp_feat = local_rng.uniform(ub[0], ub[1], n_feat - 1)
                    sp = np.concatenate([sp_int, sp_feat])
                else:
                    sp = local_rng.uniform(ub[0], ub[1], n_feat)
            else:
                sp = local_rng.standard_normal(n_feat)
            
            sp = round_to_precision(sp, decimals=6)
            # Add Index for sorting
            tasks.append((sp, X, y, run_params, self.mode, w_seed, i))
        
        with parallel_backend('loky', inner_max_num_threads=1):
            raw_results = Parallel(
                n_jobs=self.n_jobs,
                backend='loky',
                batch_size=1,
                pre_dispatch='all'
            )(
                delayed(_worker_optimization)(task) for task in tasks
            )
        
        # Sort by original task index to ensure deterministic list order
        raw_results.sort(key=lambda x: x[0])
        
        return [res[1] for res in raw_results if res[1] is not None]

    def _filter_and_validate(self, solutions, X_train, y_train, X_valid, y_valid):
        """Filters unique solutions and validates them against constraints."""
        unique_solutions = []
        seen = set()
        
        PRECISION = 6
        
        # Uniqueness Filter
        for i, s in enumerate(solutions):
            s_rounded = round_to_precision(s, decimals=PRECISION)
            if (t := tuple(s_rounded)) not in seen:
                seen.add(t)
                unique_solutions.append({'coeffs': s_rounded, 'Original_Index': i + 1})

        # Constraint Validation
        thresh = self.VALIDATION_THRESHOLD
        valid_solutions = []
        
        for sol in unique_solutions:
            beta = sol['coeffs']
            if self.mode == 'raw':
                e_tr, e_val = (X_train @ beta) - y_train, (X_valid @ beta) - y_valid
            else:
                e_tr, e_val = X_train @ beta, X_valid @ beta
            
            mse_tr = round_to_precision(np.mean(e_tr**2), decimals=PRECISION)
            mse_val = round_to_precision(np.mean(e_val**2), decimals=PRECISION)
            mae_val = round_to_precision(np.mean(np.abs(e_val)), decimals=PRECISION)
            
            if not np.isfinite(mse_tr) or not np.isfinite(mse_val):
                continue

            sol['MSE_train'] = mse_tr
            sol['MSE_vldt'] = mse_val
            sol['MAE_vldt'] = mae_val
            
            # Apply absolute error threshold if defined
            if thresh is None:
                valid_solutions.append(sol)
            else:
                if np.all(np.abs(e_tr) < thresh) and np.all(np.abs(e_val) < thresh):
                    valid_solutions.append(sol)
            
        return unique_solutions, valid_solutions

    def _select_champion_and_get_report(self, valid_solutions, X_train, y_train, ref_mse, is_fallback=False):
        """
        Selects the best solution (Champion) based on PEL (Pareto-Efficiency-Like) metric
        and residual normality (Shapiro-Wilk test).
        """
        if not valid_solutions: return None, pd.DataFrame()
        df = pd.DataFrame(valid_solutions)
        alpha = self.shapiro_threshold
        k = self.damping_factor
        pels, ps = [], []
        
        for _, row in df.iterrows():
            beta = row['coeffs']
            resid = (X_train@beta)-y_train if self.mode=='raw' else X_train@beta
            
            # Shapiro-Wilk Test for Normality
            try: _, p_val = shapiro(resid)
            except: p_val = 0.0
            ps.append(p_val)
            
            # PEL Metric Calculation (Weighting MSE vs MAE based on normality. Only for diagnostic)
            w = 1.0
            if p_val >= alpha:
                try: w = 1 / (1 + np.exp(-k * (p_val - alpha)))
                except OverflowError: w = 1.0
            else: w = p_val 
            
            pels.append((w * np.sqrt(row['MSE_vldt'])) + ((1 - w) * row['MAE_vldt']))
            
        df['shapiro_p_train'] = ps
        df['PEL_Metric'] = pels
        
        # Calculate Ratio against reference
        safe_ref = ref_mse if ref_mse > 1e-9 else 1.0
        df['R_train'] = df['MSE_train'] / safe_ref
        
        fl = self.filter_limits_
        elite = df[(df['R_train'] > fl['lower_limit']) & (df['R_train'] < fl['upper_limit'])]
        
        best_champion_dict = None

        # Hierarchy of Selection
        if elite.empty:
            if df.empty: return None, df
            # Fallback: Best MAE
            best_idx = df['MAE_vldt'].idxmin()
            best_champion_dict = df.loc[best_idx].to_dict()
            best_champion_dict['selection_criterion'] = 'MAE (Fallback - No Elite)'
            df.loc[best_idx, 'Conceptual_Champion'] = '<<- FALLBACK CHAMPION'
        else:
            # Primary: Best MSE within Elite group
            idx_mse_candidate = elite['MSE_vldt'].idxmin()
            mse_cand = elite.loc[idx_mse_candidate]
        
            if mse_cand['shapiro_p_train'] >= alpha:
                best_idx = idx_mse_candidate
                best_champion_dict = mse_cand.to_dict()
                best_champion_dict['selection_criterion'] = f"MSE (Normal p={mse_cand['shapiro_p_train']:.3f})"
            else:
                # Secondary: Best MAE if normality fails
                best_idx = elite['MAE_vldt'].idxmin()
                best_champion_dict = elite.loc[best_idx].to_dict()
                best_champion_dict['selection_criterion'] = "MAE (Robust - MSE Rejected)"
            
            if best_champion_dict:
                if is_fallback:
                    best_champion_dict['selection_criterion'] += ' [Fallback from Run 1]'
                    df.loc[best_idx, 'Conceptual_Champion'] = '<<- CHAMPION (from Run 1 Fallback)'
                else:
                    df.loc[best_idx, 'Conceptual_Champion'] = f'<<- CHAMPION ({best_champion_dict["selection_criterion"]})'

        return best_champion_dict, df
        
"""
Final comments
Numerical Quantization Policy.
DGDTL performs quantization exclusively at predefined synchronization points. This operation is optimization-neutral, idempotent for stable values, and uses a deliberate 4-decimal quantization at the Run 2 boundary to suppress sub-noise variations and ensure cross-platform invariant refinement boundaries.
"""
