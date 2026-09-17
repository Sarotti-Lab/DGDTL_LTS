# SPDX-FileCopyrightText: 2026 José A. Pérez
# SPDX-License-Identifier: MIT

"""
U-MaxP Core Engine
Unified Maximum A Posteriori
Stateless Mathematical & Structural Decision Engine
====================================================

Abstract:
---------
This engine implements the U-MaxP (Unified Maximum A Posteriori)
semi-empirical criterion and the mathematical infrastructure supporting
structural evaluation and deterministic model selection.

It provides the constitutive U-MaxP components, structural observables,
shared arbitration operators, and the reference Structural Selection
Protocol used to evaluate, compare, rank, and certify candidate solutions
independently of the optimization process that generated them.

Key Architectural Features:
---------------------------
1. U-MaxP Criterion
   Implements the constitutive U-MaxP architecture through the bounded
   Stability-Diversity-Efficiency index (SDE_b), the Generalization
   Consistency Index (GCI), and the Empirical Authenticity Barrier (A_emp),
   together with U-RAW, the Absolute Compliance Factor kappa, and the
   certified U-MaxP_k score.

2. Stateless Analytical Architecture
   Implements topological, consistency, Extreme Value Theory (EVT), and
   structural analyses without maintaining optimization state.

3. Shared Structural Operators
   Provides reusable mathematical observables and arbitration operators,
   including phi, Psi, psi_G, structural regimes, U_comp, E_inc, H, and ICV.

4. Reference Structural Selection Protocol
   Implements the deterministic selection protocol associated with the
   current theoretical framework, including Micro-Arbitration, structural
   transition analysis, absolute integrity filtering, Phase 3 arbitration,
   the post-dictamen stability auditor, Line B validation-bias analysis,
   and final observable certification.

5. Multi-Scale Decision Logic
   Applies shared mathematical principles at microscopic (trial-level) and
   structural (candidate/scout-level) decision scales while preserving the
   metric appropriate to each context.

Sections:
---------
1. Core Constants & Thresholds
2. Mathematical Engines
   - TopologicalEngine
   - EVTAnalyzer
   - ConsistencyEngine
3. U-MaxP Criterion
   - UMaxPCriterion
4. Structural Metrics & Operators
   - StructuralMetricsEngine
   - U_comp
   - E_inc
5. Micro-Arbitration
   - MicroArbitration
6. Reference Structural Selection Protocol
   - PhaseEvaluator
   - Phase3TieBreaker
   - StructuralSelectionProtocol

Usage:
------
Designed as a stateless mathematical and structural decision engine.
U-MaxP evaluates candidate solutions supplied by an external optimization
or search process. The reference Structural Selection Protocol consumes
these structural quantities to produce deterministic selection and
certification decisions.

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

import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist
from typing import Dict, List, Tuple, Optional

EPS_F     = 1e-4
DELTA_REL = 0.005
EPS_TIE   = 0.02
EPS_PSI   = 1e-8

PHASE1_CODES: Dict[str, tuple] = {
    'F1.0':    ('TEQ', 'Topological Equivalence'),
    'F1.1':    ('JDC', 'Joint Density Collapse'),
    'F1.2':    ('IRF', 'Inefficient Refinement'),
    'F1.3':    ('GTR', 'Genuine Topological Refinement'),
    'F1.3phi': ('STP', 'Step Tie — phi Defends R1'),
    'F1.4':    ('SDI', 'Spurious Density Increment'),
    'F1.X':    ('SNG', 'Single Run — No Comparison'),
}

PHASE2_CODES: Dict[str, tuple] = {
    'F2.0':    ('BND', 'Baseline Native Dominance'),
    'F2.1':    ('SPT', 'Spurious Transfer'),
    'F2.2':    ('TRG', 'Topological Regularization'),
    'F2.2-RT': ('TSA', 'Topological Reg. — Scope Advisory'),
    'F2.3':    ('STD', 'Structural Dominance'),
    'F2.4':    ('ISI', 'Incoherent Scalar Improvement'),
}

PHASE4_CODES: Dict[str, tuple] = {
    'FA.1': ('DAC', 'DOA Complete',
             'DGDTL dominated BL_RT on both observable metrics'),
    'FA.2': ('DAE', 'DOA Error',
             'DGDTL lower error than BL_RT; phi gap expected (BL_RT asymmetry)'),
    'FA.3': ('DPO', 'DOA Phi Only',
             'DGDTL better structural coherence; BL_RT lower error (data advantage)'),
    'FA.4': ('ROS', 'RT Observable Superior',
             'BL_RT dominated both observable metrics; DGDTL leads in U_MAXP_k only'),
}

class ProtocolConfig:
    """Calibrated constants used by the reference Structural Selection Protocol."""
    EPS_F           = 1e-4
    DELTA_REL       = 0.005
    EPS_TIE         = 0.02
    EPS_PSI         = 1e-8
    ICV_STRONG      = 1.0
    ICV_CONDITIONAL = 0.85
    PSI_RANK_MIN    = 0.5
    PSI_RANK_N_MIN  = 5
    THETA_STABILITY = 0.10

class ProtocolVerdictCodes:
    """Formal verdict-code registry used by the validated Hunter protocol."""
    PHASE1 = PHASE1_CODES
    PHASE2 = PHASE2_CODES
    PHASE4 = {
        'FA.1': ('DAC', 'DOA Complete',
                 'DGDTL dominated BL_RT on both observable metrics'),
        'FA.2': ('DAE', 'DOA Error',
                 'DGDTL lower error than BL_RT; phi gap expected (BL_RT asymmetry)'),
        'FA.3': ('DPO', 'DOA Phi Only',
                 'DGDTL better structural coherence; BL_RT lower error (data advantage)'),
        'FA.4': ('ROS', 'RT Observable Superior',
                 'BL_RT dominated both observable metrics; DGDTL leads in U_MAXP_k only'),
    }

class _NullLogger:
    """No-op logger used when the protocol is invoked outside an orchestrator."""
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
# 1. CONSTITUTIVE U-MAXP MATHEMATICS
# =============================================================================

class TopologicalEngine:
    @staticmethod
    def compute_baseline_sde_hc0(X: np.ndarray, y: np.ndarray, coeffs: np.ndarray) -> float:
        try:
            n, p = X.shape[0], len(coeffs)
            if n == 0 or p == 0: return 0.0
            X_aug = np.hstack([np.ones((n, 1)), X]) if (p == X.shape[1] + 1) else X
            if X_aug.shape[1] != p: return 0.0
            
            y_hat = X_aug @ coeffs
            residuals = y - y_hat
            B = (X_aug.T @ X_aug) / n
            try: B_inv = np.linalg.pinv(B)
            except np.linalg.LinAlgError: return 0.0
            
            eps_sq = (residuals.flatten() ** 2)
            M = (X_aug.T * eps_sq) @ X_aug / n
            W = (1.0 / n) * (B_inv @ M @ B_inv)
            W_diag = np.maximum(np.diag(W), 0.0)
            
            cvs = np.sqrt(W_diag) / (np.abs(coeffs) + 1e-9)
            cv_global = float(np.mean(cvs))
            omega_base = 1.0 / (1.0 + cv_global)
            d_base = float(np.log1p(100.0 * float(np.mean(W_diag))))
            
            if d_base <= 0.0: return 0.0
            return round(float(omega_base * np.exp(-1.0 / d_base)), 6)
        except Exception:
            return 0.0

    @staticmethod
    def extract_topology(run1_valid: list, baseline_mse: float, filter_limits: dict) -> Tuple[float, float, float, int, int]:
        N_valid = len(run1_valid)
        if N_valid > 0:
            df_valid = pd.DataFrame(run1_valid)
            df_valid['R_train'] = (df_valid['MSE_train'] / baseline_mse).round(6) 
            elite = df_valid[(df_valid['R_train'] > filter_limits['lower_limit']) & (df_valid['R_train'] < filter_limits['upper_limit'])]
            N_elite = len(elite)
        else:
            N_elite, elite = 0, pd.DataFrame()
        
        S = N_elite / N_valid if N_valid > 0 else 0
        compactness_penalty, D = 1.0, 0.0
        
        if N_elite > 1:
            coeffs_elite = np.round(np.array([sol['coeffs'] for sol in elite.to_dict('records')]), 6)
            try:
                distances = pdist(coeffs_elite, metric='euclidean')
                cv_distances = float(np.std(distances)) / (float(np.median(distances)) + 1e-9)
                if cv_distances > 1.0: compactness_penalty = 1.0 / (cv_distances)
                elif cv_distances < 0.2: compactness_penalty = cv_distances / 0.2
            except Exception:
                compactness_penalty = 0.5
            D = round(float(np.log1p(np.mean(np.var(coeffs_elite, axis=0, ddof=1)) * 100)), 6)
            
        return S, D, compactness_penalty, N_elite, N_valid

class EVTAnalyzer:
    @staticmethod
    def compute_empirical_authenticity(errors: np.ndarray, tau_anchor: float, e_gm: float, min_thickness: float) -> Tuple[float, float, float]:
        if len(errors) == 0: return 1.0, 0.0, 0.0
        p95 = np.percentile(errors, 95)
        tail = errors[errors >= p95]
        e_max_robusto = float(np.mean(tail)) if len(tail) > 0 else float(np.max(errors))
        
        eff_thickness = max(e_gm - tau_anchor, min_thickness)
        phi_emp = max(0.0, (e_max_robusto - tau_anchor) / eff_thickness)
        a_emp = float(np.exp(-(phi_emp ** 2)))
        
        return round(a_emp, 6), round(phi_emp, 6), round(e_max_robusto, 6)

class ConsistencyEngine:
    @staticmethod
    def compute_gci(mae_val: float, mse_val: float, mae_tr: float, mse_tr: float, max_err: float, 
                    mae_base_val: float, mse_base_val: float, mae_base_tr: float, mse_base_tr: float, e_gm_nat: float) -> float:
        if not (0 < mse_val < float('inf')) or not (0 < mae_val < float('inf')) or \
           not (0 < mse_tr < float('inf')) or not (0 < mae_tr < float('inf')) or \
           mse_base_val <= 0 or mae_base_val <= 0 or mse_base_tr <= 0 or mae_base_tr <= 0: 
            return 0.0
            
        e_val, e_tr = np.sqrt(mae_val * np.sqrt(mse_val)), np.sqrt(mae_tr * np.sqrt(mse_tr))
        e_base, e_base_tr = np.sqrt(mae_base_val * np.sqrt(mse_base_val)), np.sqrt(mae_base_tr * np.sqrt(mse_base_tr))
        
        f_eff = 1.0 / (1.0 + (e_val / (e_base + 1e-12)))
        rho = (e_val / (e_tr + 1e-12)) / (e_base / (e_base_tr + 1e-12) + 1e-12)
        phi = (2.0 * rho) / (1.0 + rho**2 + 1e-12)
        h_cont = 1.0 / (1.0 + (max_err / (e_gm_nat + 1e-12)))
        
        return round(float(f_eff * phi * h_cont), 6)

class UMaxPCriterion:
    """
    Stateless implementation of the constitutive U-MaxP criterion.

    These methods deliberately preserve the exact arithmetic expressions used
    by the validated Hunter code.  No algebraic simplification, vectorization,
    or re-ordering is performed here.
    """

    @staticmethod
    def compute_sde_b(S: float, D: float, compactness_penalty: float,
                      e_normalized: float, ambition: float) -> float:
        if S > 0 and D > 0 and e_normalized > 0:
            return float(S * compactness_penalty * np.exp(-(e_normalized / (D * np.sqrt(ambition)))))
        return 0.0

    @staticmethod
    def compute_uraw(sde_b: float, gci: float) -> float:
        return float(sde_b * gci)

    @staticmethod
    def compute_umaxp(sde_b: float, gci: float, a_emp: float) -> float:
        return float(sde_b * gci * a_emp)

    @staticmethod
    def compute_kappa(tau_anchor: float, emax_rob: float,
                      is_baseline: bool = False) -> float:
        if is_baseline:
            return 1.0
        return float(tau_anchor / max(tau_anchor, emax_rob) if tau_anchor > 0 else 1.0)

    @staticmethod
    def compute_umaxp_k(u_maxp: float, kappa: float) -> float:
        return float(u_maxp * kappa)

    @staticmethod
    def composite_error(mae: float, mse: float) -> float:
        return float(np.sqrt(mae * np.sqrt(mse)))

    @staticmethod
    def cauchy_rho(e_val: float, e_train: float,
                   e_base_val: float, e_base_train: float) -> float:
        return float((e_val / (e_train + 1e-12)) /
                     (e_base_val / (e_base_train + 1e-12) + 1e-12))

    @staticmethod
    def cauchy_phi_from_rho(rho: float) -> float:
        return float((2.0 * rho) / (1.0 + rho**2 + 1e-12))

    @staticmethod
    def cauchy_phi(e_val: float, e_train: float,
                   e_base_val: float, e_base_train: float) -> float:
        rho = UMaxPCriterion.cauchy_rho(e_val, e_train, e_base_val, e_base_train)
        return UMaxPCriterion.cauchy_phi_from_rho(rho)

    @staticmethod
    def compute_f_eff(e_val: float, e_base_val: float) -> float:
        return float(1.0 / (1.0 + (e_val / (e_base_val + 1e-12))))

    @staticmethod
    def compute_h_cont(max_err: float, e_gm: float) -> float:
        return float(1.0 / (1.0 + (max_err / (e_gm + 1e-12))))

# =============================================================================
# 2. SHARED STRUCTURAL OBSERVABLES & ARBITRATION PRIMITIVES
# =============================================================================

class StructuralMetricsEngine:
    """Reusable structural observables used by the reference protocol."""

    @staticmethod
    def compute_psi_metrics(row: pd.Series, bl_tr: pd.Series) -> Dict:
        mae_tr_bl  = float(bl_tr['MAE_Train']) + 1e-12
        mae_val_bl = float(bl_tr['MAE_Valid'])
        mse_tr_bl  = float(bl_tr['MSE_Train']) + 1e-12
        mse_val_bl = float(bl_tr['MSE_Valid'])
        mae_tr  = float(row['MAE_Train']) + 1e-12
        mae_val = float(row['MAE_Valid'])
        mse_tr  = float(row['MSE_Train']) + 1e-12
        mse_val = float(row['MSE_Valid'])

        rho_mae = (mae_val / mae_tr) / (mae_val_bl / mae_tr_bl)
        rho_mse = (mse_val / mse_tr) / (mse_val_bl / mse_tr_bl)
        log_rho_mae = np.log10(rho_mae) if rho_mae > 0 else 0.0
        log_rho_mse = np.log10(rho_mse) if rho_mse > 0 else 0.0
        psi = log_rho_mae * log_rho_mse

        regime = 'SOV' if log_rho_mae < 0 and log_rho_mse < 0 else ('OFT' if log_rho_mae > 0 and log_rho_mse > 0 else 'INC')
        psi_G = np.sqrt((mae_val / mae_tr) * (np.sqrt(mse_val) / np.sqrt(mse_tr)))

        return {'Psi': psi, 'Regime': regime, 'psi_G': psi_G}

    @staticmethod
    def compute_e_inc(e_val: float, e_tr: float, phi: float) -> float:
        return float(np.sqrt(e_val * e_tr) * (1.0 - phi))

    @staticmethod
    def compute_h_factor(phi_emp: float, eps: float = 1e-12) -> float:
        return (1.0 - phi_emp) / (phi_emp + eps)

    @staticmethod
    def compute_icv(twin_row: pd.Series, c_star_row: pd.Series,
                    psi_G_bl_tr: float) -> float:
        psi_ratio  = float(twin_row['psi_G']) / (psi_G_bl_tr + 1e-12)
        sde_ratio  = float(twin_row['SDE_b']) / (float(c_star_row['SDE_b']) + 1e-12)
        e_inc_twin  = StructuralMetricsEngine.compute_e_inc(
            float(twin_row['E_Valid']), float(twin_row['E_Train']), float(twin_row['phi'])
        )
        e_inc_cstar = StructuralMetricsEngine.compute_e_inc(
            float(c_star_row['E_Valid']), float(c_star_row['E_Train']), float(c_star_row['phi'])
        )
        e_ratio = (e_inc_cstar + 1e-12) / (e_inc_twin + 1e-12)
        product = float(psi_ratio * sde_ratio * e_ratio)
        return float(np.cbrt(max(product, 0.0)))

def u_comp_operator(u_a: float, u_b: float,
                    phi_a: float, phi_b: float,
                    reg_a: str, reg_b: str) -> float:
    """
    U_comp = sqrt(U_A * U_B) / (1 + |phi_B - phi_A|)

    Applied only when both candidates share the same thermodynamic regime.
    Falls back to max(u_a, u_b) on regime divergence (Line-B scenario).

    Parameters
    ----------
    u_a, u_b    : U scores (U_score intra-Siege; U_MAXP_k inter-scout)
    phi_a, phi_b: Cauchy phi values
    reg_a, reg_b: thermodynamic regimes ('SOV', 'OFT', 'INC')

    Returns
    -------
    float — U_comp score (higher is better)
    """
    if u_a > 0 and u_b > 0 and reg_a == reg_b:
        return float(np.sqrt(u_a * u_b)) / (1.0 + abs(phi_b - phi_a))
    return float(max(u_a, u_b))

def e_inc_operator(e_v: float, e_t: float, phi: float) -> float:
    """
    E_inc = sqrt(e_val * e_tr) * (1 - phi)

    Penalized combined error. Lower is better.
    Identical to the E_inc operator used in Framework Phase-3 Step-3b-I.

    Parameters
    ----------
    e_v  : composite validation error  sqrt(MAE_val * sqrt(MSE_val))
    e_t  : composite training error    sqrt(MAE_tr  * sqrt(MSE_tr))
    phi  : Cauchy coherence factor in (0, 1]

    Returns
    -------
    float — E_inc score (lower is better)
    """
    return float(np.sqrt(e_v * e_t) * (1.0 - phi))

class MicroArbitration:
    """
    Intra-Siege trial selection arbiter (Context A).

    Implements the two-level selection protocol on Optuna trial
    user_attrs. The metric is U_score (raw U_MAXP, pre-k-penalization),
    consistent with the Optuna objective that was maximized during
    the Siege.

    Two-level protocol
    ------------------
    Level 1 — U_comp
        U_comp(t) = sqrt(U_R1 * U_R2) / (1 + |phi_R2 - phi_R1|)
        Applied when both runs share the same thermodynamic regime.
        Rewards structurally stable trials (flat minima) over fragile
        peaks. Falls back to max(U_R1, U_R2) on regime divergence.

    Level 2 — E_inc  (Step-3b-I analogue; only on genuine U_comp tie)
        E_inc(R1) = sqrt(e_val * e_tr) * (1 - phi)
        Between trials indistinguishable by U_comp (gap < eps_tie),
        selects the trial with the most compact structural error.

    Empirical validation
    --------------------
    eps_tie = 2% confirmed as invariant across both intra-Siege and
    inter-scout contexts (corpus: 8 domains, 68 scouts, 408 trials).
      Delta_tie_intra = 1.857%  (max gap inside pool)
      Delta_min_intra = 2.024%  (min gap outside pool)
      Geometric mean eps* = 1.94% → 2.0%
    """

    # ------------------------------------------------------------------
    # Internal primitives (operate on trial user_attrs)
    # ------------------------------------------------------------------

    @staticmethod
    def _composite_error(mae: float, mse: float) -> float:
        """e = sqrt(MAE * sqrt(MSE))"""
        return float(np.sqrt(mae * np.sqrt(mse))) if mae > 0 and mse > 0 else 0.0

    @staticmethod
    def _cauchy_phi(e_v: float, e_t: float,
                    e_base: float, e_base_tr: float) -> float:
        """phi = 2*rho / (1 + rho^2),  rho = (e_v/e_t) / (e_base/e_base_tr)"""
        if e_t <= 0 or e_base_tr <= 0:
            return 0.0
        rho = (e_v / (e_t + 1e-12)) / (e_base / (e_base_tr + 1e-12) + 1e-12)
        return float((2.0 * rho) / (1.0 + rho ** 2 + 1e-12))

    @staticmethod
    def _regime(mae_v: float, mae_t: float,
                mse_v: float, mse_t: float,
                mae_val_bl: float, mae_tr_bl: float,
                mse_val_bl: float, mse_tr_bl: float) -> str:
        """SOV | OFT | INC based on log-ratio signs."""
        if mae_t <= 0 or mse_t <= 0 or mae_tr_bl <= 0 or mse_tr_bl <= 0:
            return 'INC'
        rho_mae = (mae_v / mae_t) / (mae_val_bl / mae_tr_bl + 1e-12)
        rho_mse = (mse_v / mse_t) / (mse_val_bl / mse_tr_bl + 1e-12)
        lm = np.log10(rho_mae) if rho_mae > 0 else 0.0
        ls = np.log10(rho_mse) if rho_mse > 0 else 0.0
        if lm < 0 and ls < 0:
            return 'SOV'
        if lm > 0 and ls > 0:
            return 'OFT'
        return 'INC'

    # ------------------------------------------------------------------
    # Public scoring API
    # ------------------------------------------------------------------

    @staticmethod
    def score_trial(trial,
                    e_base: float, e_base_tr: float,
                    mae_val_bl: float, mae_tr_bl: float,
                    mse_val_bl: float, mse_tr_bl: float) -> dict:
        """
        Compute U_comp and E_inc for a single Optuna trial.

        Reads user_attrs written by _objective_internal:
            U_score, u_run2,
            mae_vldt_r1/r2, mse_vldt_r1/r2,
            mae_train_r1/r2, mse_train_r1/r2.

        Returns
        -------
        dict: u_comp, e_inc_r1, phi1, phi2, reg1, reg2, u1, u2
        """
        attrs = trial.user_attrs
        u1 = float(attrs.get('U_score', 0.0))
        u2 = float(attrs.get('u_run2',  0.0))

        def _extract(suf):
            return (
                float(attrs.get(f'mae_vldt_{suf}',  0.0)),
                float(attrs.get(f'mse_vldt_{suf}',  0.0)),
                float(attrs.get(f'mae_train_{suf}', 0.0)),
                float(attrs.get(f'mse_train_{suf}', 0.0)),
            )

        mv1, msv1, mt1, mst1 = _extract('r1')
        mv2, msv2, mt2, mst2 = _extract('r2')

        ev1 = MicroArbitration._composite_error(mv1, msv1)
        et1 = MicroArbitration._composite_error(mt1, mst1)
        ev2 = MicroArbitration._composite_error(mv2, msv2)
        et2 = MicroArbitration._composite_error(mt2, mst2)

        phi1 = MicroArbitration._cauchy_phi(ev1, et1, e_base, e_base_tr)
        phi2 = MicroArbitration._cauchy_phi(ev2, et2, e_base, e_base_tr)

        reg1 = MicroArbitration._regime(mv1, mt1, msv1, mst1,
                                       mae_val_bl, mae_tr_bl,
                                       mse_val_bl, mse_tr_bl)
        reg2 = MicroArbitration._regime(mv2, mt2, msv2, mst2,
                                       mae_val_bl, mae_tr_bl,
                                       mse_val_bl, mse_tr_bl)

        uc   = u_comp_operator(u1, u2, phi1, phi2, reg1, reg2)
        einc = e_inc_operator(ev1, et1, phi1) if et1 > 0 else float('inf')

        return {
            'u_comp':   uc,
            'e_inc_r1': einc,
            'phi1': phi1, 'phi2': phi2,
            'reg1': reg1, 'reg2': reg2,
            'u1': u1,     'u2': u2,
        }

    # ------------------------------------------------------------------
    # Main selection entry point
    # ------------------------------------------------------------------

    @staticmethod
    def select_best_trial(top_trials: list,
                          e_base: float, e_base_tr: float,
                          mae_val_bl: float, mae_tr_bl: float,
                          mse_val_bl: float, mse_tr_bl: float,
                          eps_tie: float = EPS_TIE):
        """
        Select the best trial from the eps_tie-equivalent pool.

        Level 1 — U_comp
            Highest U_comp wins.  If a single clear winner exists
            (gap to second >= eps_tie), return immediately.

        Level 2 — E_inc  (Step-3b-I analogue)
            Invoked only on genuine U_comp tie (gap < eps_tie).
            Returns the trial with minimum E_inc(R1).

        Parameters
        ----------
        top_trials            : list[optuna.Trial] — pool from ReportGenerator
        e_base, e_base_tr     : baseline composite errors (val, train)
        mae_val_bl, mae_tr_bl : baseline MAE statistics
        mse_val_bl, mse_tr_bl : baseline MSE statistics
        eps_tie               : tie threshold (default EPS_TIE = 2%)

        Returns
        -------
        optuna.Trial — selected best trial
        """
        if not top_trials:
            raise ValueError("MicroArbitration.select_best_trial: empty pool.")
        if len(top_trials) == 1:
            return top_trials[0]

        scores = [
            MicroArbitration.score_trial(
                tr, e_base, e_base_tr,
                mae_val_bl, mae_tr_bl,
                mse_val_bl, mse_tr_bl,
            )
            for tr in top_trials
        ]

        ucomp_vals = [s['u_comp'] for s in scores]
        best_ucomp = max(ucomp_vals)

        if best_ucomp <= 0:
            return max(top_trials,
                       key=lambda tr: tr.user_attrs.get('U_score', 0.0))

        # Check for genuine U_comp tie
        tied = [
            (tr, s) for tr, s, uc in zip(top_trials, scores, ucomp_vals)
            if abs(uc - best_ucomp) / (best_ucomp + 1e-12) < eps_tie
        ]

        if len(tied) == 1:
            return tied[0][0]

        # Level 2: E_inc Step-3b-I analogue
        return min(tied, key=lambda x: x[1]['e_inc_r1'])[0]

# Backward-compatible alias used by the validated Hunter naming.
FrameworkMetricsEngine = StructuralMetricsEngine

# =============================================================================
# 3. REFERENCE STRUCTURAL SELECTION PROTOCOL
# =============================================================================

class PhaseEvaluator:
    """Pure phase-level rules of the reference Structural Selection Protocol."""

    @staticmethod
    def evaluate_phase1(row_a: pd.Series, row_b: pd.Series) -> Dict:
        uk_a, uk_b = float(row_a['U_MAXP_k']), float(row_b['U_MAXP_k'])
        phi_a, phi_b = float(row_a['phi']), float(row_b['phi'])
        duk, dphi = uk_b - uk_a, phi_b - phi_a
        rel_duk = duk / (abs(uk_a) + 1e-12)

        if abs(duk) < ProtocolConfig.EPS_F and abs(dphi) < ProtocolConfig.EPS_F:
            return dict(case='F1.0', short='TEQ', label=ProtocolVerdictCodes.PHASE1['F1.0'][1], winner='A', delta_uk=duk, delta_phi=dphi)
        if duk < -ProtocolConfig.EPS_F:
            key = 'F1.1' if dphi < -ProtocolConfig.EPS_F else 'F1.2'
            return dict(case=key, short=ProtocolVerdictCodes.PHASE1[key][0], label=ProtocolVerdictCodes.PHASE1[key][1], winner='A', delta_uk=duk, delta_phi=dphi)
        thr_adp = max(ProtocolConfig.EPS_F, ProtocolConfig.DELTA_REL * phi_a)
        if dphi < -thr_adp:
            return dict(case='F1.4', short='SDI', label=ProtocolVerdictCodes.PHASE1['F1.4'][1], winner='A', delta_uk=duk, delta_phi=dphi)
        if 0.0 <= rel_duk < ProtocolConfig.EPS_TIE and phi_b < phi_a:
            return dict(case='F1.3phi', short='STP', label=ProtocolVerdictCodes.PHASE1['F1.3phi'][1], winner='A', delta_uk=duk, delta_phi=dphi)
        return dict(case='F1.3', short='GTR', label=ProtocolVerdictCodes.PHASE1['F1.3'][1], winner='B', delta_uk=duk, delta_phi=dphi)

    @staticmethod
    def evaluate_phase2(row_c: pd.Series, uk_hm: float, ratio_ref: float,
                        uk_retrain: float = 0.0) -> Dict:
        uk_c, e_val, e_tr = float(row_c['U_MAXP_k']), float(row_c['E_Valid']), float(row_c['E_Train'])
        ratio_c = e_val / (e_tr + 1e-12)
        if uk_c <= uk_hm:
            return dict(case='F2.0', short='BND', label=ProtocolVerdictCodes.PHASE2['F2.0'][1], winner='BL', I=None, G=None, I_val=e_tr - e_val, G_val=ratio_ref - ratio_c + ProtocolConfig.EPS_F, ratio_c=ratio_c)
        I, G = bool(e_tr > e_val), bool(ratio_c <= ratio_ref + ProtocolConfig.EPS_F)
        key = {(True, False): 'F2.1', (True, True): 'F2.2', (False, True): 'F2.3', (False, False): 'F2.4'}[(I, G)]
        short, label = ProtocolVerdictCodes.PHASE2[key]
        winner = 'C' if key in ('F2.2', 'F2.3') else 'BL'
        if winner == 'C' and uk_retrain > uk_c:
            key, short, label = 'F2.2-RT', ProtocolVerdictCodes.PHASE2['F2.2-RT'][0], ProtocolVerdictCodes.PHASE2['F2.2-RT'][1]
        return dict(case=key, short=short, label=label, winner=winner, I=I, G=G, I_val=e_tr - e_val, G_val=ratio_ref - ratio_c + ProtocolConfig.EPS_F, ratio_c=ratio_c)

    @staticmethod
    def evaluate_phase4(row_c: pd.Series, row_retrain: pd.Series) -> Dict:
        ev_c, phi_c = float(row_c['E_Valid']), float(row_c['phi'])
        ev_rt, phi_rt = float(row_retrain['E_Valid']), float(row_retrain['phi'])
        I_RT, J_RT = bool(ev_c < ev_rt), bool(phi_c >= phi_rt)
        key = {(True, True): 'FA.1', (True, False): 'FA.2', (False, True): 'FA.3', (False, False): 'FA.4'}[(I_RT, J_RT)]
        short, short_label, narrative = ProtocolVerdictCodes.PHASE4[key]
        return dict(case=key, short=short, short_label=short_label, label=narrative, I_RT=I_RT, J_RT=J_RT, ev_c=ev_c, ev_rt=ev_rt, delta_ev_pct=(ev_rt - ev_c) / (ev_rt + 1e-12) * 100.0, phi_c=phi_c, phi_rt=phi_rt)

    @staticmethod
    def evaluate_line_b(df: pd.DataFrame, df_cands: pd.DataFrame,
                        c_star_idx: int, tr_only: pd.Series,
                        rt_rows: pd.DataFrame) -> Dict:
        c_star_row = df.loc[c_star_idx]
        scout = c_star_row['Scout_Base']
        s = df_cands[df_cands['Scout_Base'] == scout]
        twin_candidates = [idx for idx in s.index if idx != c_star_idx and df.loc[idx, 'Regime'] == 'OFT' and df.loc[idx, 'Psi'] > ProtocolConfig.EPS_PSI]
        if not twin_candidates:
            return {
                'active': True, 'twin_label': None,
                'verdict': 'NO_TWIN', 'vbd_verdict': 'VBD_NO_TWIN',
                'reason': f'No valid OFT twin found in scout {scout}.',
                'c_star_A': c_star_row['Candidate_Label'],
                'icv': 0.0, 'psi_rank': None,
            }

        twin_idx = sorted(twin_candidates, key=lambda i: (-float(df.loc[i, 'psi_G']), abs(float(df.loc[i, 'Psi']))))[0]
        twin_row = df.loc[twin_idx]

        psi_G_bl_tr = np.sqrt(((float(tr_only['MAE_Valid']) / (float(tr_only['MAE_Train']) + 1e-12)) * (np.sqrt(float(tr_only['MSE_Valid'])) / np.sqrt(float(tr_only['MSE_Train']) + 1e-12))))
        has_retrain = not rt_rows.empty
        psi_bl_rt = abs(StructuralMetricsEngine.compute_psi_metrics(rt_rows.iloc[0], tr_only)['Psi']) if has_retrain else 0.0

        crit_1 = bool(float(twin_row['psi_G']) > psi_G_bl_tr)
        crit_2 = bool(abs(float(twin_row['Psi'])) < psi_bl_rt) if has_retrain else False

        if crit_1 and crit_2:       lb_verdict, lb_verdict_txt = 'LB_FULL',         'Twin surpasses BOTH domain references (BL_TR and BL_RT).'
        elif crit_1 and not crit_2: lb_verdict, lb_verdict_txt = 'LB_TRAIN_ONLY',   'Twin surpasses BL_TR but NOT BL_RT.'
        elif not crit_1 and crit_2: lb_verdict, lb_verdict_txt = 'LB_RETRAIN_ONLY', 'Twin surpasses BL_RT but NOT BL_TR.'
        else:                       lb_verdict, lb_verdict_txt = 'LB_NONE',          'Twin surpasses neither reference. Diagnostic evidence only.'

        icv = StructuralMetricsEngine.compute_icv(twin_row, c_star_row, psi_G_bl_tr)

        sde_ratio = float(twin_row['SDE_b']) / float(c_star_row['SDE_b']) if float(c_star_row['SDE_b']) > 0 else 0.0
        topo_class = 'ROBUST' if sde_ratio > 0.5 else 'SENSITIVE' if sde_ratio > 0 else 'UNAVAILABLE'
        topo_class_txt = (
            'Robust — sufficient spectral support (SDE_b > C*/2).' if topo_class == 'ROBUST' else
            'Sensitive — limited spectral support (0 < SDE_b <= C*/2).' if topo_class == 'SENSITIVE' else
            'Unavailable — topological collapse of twin (SDE_b = 0).'
        )
        p_coh = bool((float(twin_row['U_MAXP_k']) < float(c_star_row['U_MAXP_k'])) and (abs(float(twin_row['Psi'])) < abs(float(c_star_row['Psi']))))

        return {
            'active': True, 'is_nuance2': (len(twin_candidates) > 1), 'c_star_A': c_star_row['Candidate_Label'],
            'twin_label': twin_row['Candidate_Label'], 'twin_idx': twin_idx, 'twin_regime': twin_row['Regime'],
            'psi_twin': float(twin_row['Psi']), 'psi_twin_abs': abs(float(twin_row['Psi'])), 'psi_G_twin': float(twin_row['psi_G']),
            'psi_G_bl_tr': psi_G_bl_tr, 'psi_bl_rt': psi_bl_rt, 'sde_twin': float(twin_row['SDE_b']), 'sde_cstar': float(c_star_row['SDE_b']),
            'sde_ratio': sde_ratio, 'crit_1': crit_1, 'crit_2': crit_2, 'has_retrain': has_retrain,
            'lb_verdict': lb_verdict, 'lb_verdict_txt': lb_verdict_txt,
            'icv': icv, 'psi_rank': None, 'vbd_verdict': None,
            'topo_class': topo_class, 'topo_class_txt': topo_class_txt, 'p_coh': p_coh,
            'uk_twin': float(twin_row['U_MAXP_k']), 'uk_c_star': float(c_star_row['U_MAXP_k']),
            'psi_c_star': abs(float(c_star_row['Psi'])), 'e_val_twin': float(twin_row['E_Valid']),
            'n_twins_found': len(twin_candidates), 'verdict': lb_verdict,
        }

class Phase3TieBreaker:
    """Reference Phase-3 implementation for structural tie resolution."""

    _THETA = ProtocolConfig.THETA_STABILITY

    def __init__(self, df_inter: pd.DataFrame, colors_cls=None, logger=None):
        self.df_inter = df_inter
        self.colors = colors_cls
        self.logger = logger if logger is not None else _NullLogger
        self.df_c = self.df_inter[~self.df_inter['Scout_Base'].str.contains('BASELINE', na=False)]

    def _compute_u_comp(self, scout_name: str) -> float:
        s = self.df_c[self.df_c['Scout_Base'].str.strip() == scout_name]
        r1, r2 = s[s['Run_ID'] == 1], s[s['Run_ID'] == 2]

        if r1.empty or r2.empty:
            available = r2 if r1.empty else r1
            return float(available['U_MAXP_k'].iloc[0]) if not available.empty else 0.0

        uk_r1, uk_r2 = float(r1['U_MAXP_k'].iloc[0]), float(r2['U_MAXP_k'].iloc[0])
        phi_r1, phi_r2 = float(r1['phi'].iloc[0]), float(r2['phi'].iloc[0])

        geom_mean = float(np.sqrt(uk_r1 * uk_r2))
        return geom_mean / (1.0 + abs(phi_r2 - phi_r1))

    # Compatibility with the previous public method name in u_maxp_core.py.
    def compute_u_comp(self, scout_name: str) -> float:
        return self._compute_u_comp(scout_name)

    def resolve_intra_scout(self, idx1: int, idx2: int) -> Tuple[int, int, str]:
        row1, row2 = self.df_inter.loc[idx1], self.df_inter.loc[idx2]

        e1 = StructuralMetricsEngine.compute_e_inc(float(row1['E_Valid']), float(row1['E_Train']), float(row1['phi']))
        e2 = StructuralMetricsEngine.compute_e_inc(float(row2['E_Valid']), float(row2['E_Train']), float(row2['phi']))

        phi1, phi2 = float(row1['phi']), float(row2['phi'])
        phi_emp1, phi_emp2 = float(row1.get('Phi_emp', 0.0)), float(row2.get('Phi_emp', 0.0))

        e_min, e_max = min(e1, e2), max(e1, e2)
        delta_e = (e_max - e_min) / (e_min + 1e-12)

        if delta_e < ProtocolConfig.EPS_TIE:
            winner_idx, loser_idx = (idx1, idx2) if e1 <= e2 else (idx2, idx1)
            msg = f"  Step 3b-I [Quasi-equivalence δE={delta_e*100:.2f}%]: min E_inc -> {self.df_inter.loc[winner_idx, 'Candidate_Label']}"
            return self._apply_stability_audit(winner_idx, loser_idx, msg)

        concordant = (phi2 > phi1 and phi_emp2 > phi_emp1) or (phi1 >= phi2 and phi_emp1 >= phi_emp2)
        pemp_tied, evt_inactive = abs(phi_emp1 - phi_emp2) < 1e-12, max(phi_emp1, phi_emp2) == 0.0

        if concordant or pemp_tied or evt_inactive:
            winner_idx, loser_idx = (idx2, idx1) if phi2 > phi1 else (idx1, idx2)
            msg = f"  Step 3b-II(a) [Concordance/EVT-eq — Cauchy]: {self.df_inter.loc[winner_idx, 'Candidate_Label']} won."
            return self._apply_stability_audit(winner_idx, loser_idx, msg)

        h1 = StructuralMetricsEngine.compute_h_factor(phi_emp1, 1e-9)
        h2 = StructuralMetricsEngine.compute_h_factor(phi_emp2, 1e-9)

        winner_idx, loser_idx = (idx1, idx2) if h1 < h2 else (idx2, idx1)
        msg = f"  Step 3b-II(b) [Divergence — EVT Guardrail H]: {self.df_inter.loc[winner_idx, 'Candidate_Label']} H={min(h1,h2):.6f} < H={max(h1,h2):.6f}"

        return self._apply_stability_audit(winner_idx, loser_idx, msg)

    def _apply_stability_audit(self, winner_idx: int, loser_idx: int,
                               structural_msg: str) -> Tuple[int, int, str]:
        components = ['SDE_b', 'GCI', 'A_emp']
        w_row = self.df_inter.loc[winner_idx]
        l_row = self.df_inter.loc[loser_idx]

        active = {}
        for j in components:
            w_val = float(w_row.get(j, float('nan')))
            l_val = float(l_row.get(j, float('nan')))
            if (w_val != w_val) or (l_val != l_val):
                continue
            diff = abs(w_val - l_val)
            if diff >= self._THETA and w_val < l_val:
                active[j] = (diff, w_val, l_val)

        if not active:
            return winner_idx, loser_idx, structural_msg

        deciding = max(active, key=lambda j: active[j][0])
        d_diff, d_w, d_l = active[deciding]

        all_flags = ", ".join(
            f"{j}: W={active[j][1]:.4f} < L={active[j][2]:.4f} |Δ|={active[j][0]:.4f}"
            for j in active
        )
        audit_msg = (
            f"  [θ-AUDIT | θ={self._THETA}] Stability filter triggered — "
            f"winner was less stable in: {all_flags}. "
            f"Deciding component (max |Δ|): {deciding} "
            f"(W={d_w:.4f} < L={d_l:.4f}, |Δ|={d_diff:.4f}). "
            f"REVERSAL APPLIED."
        )
        combined_msg = structural_msg + "\n" + audit_msg
        return loser_idx, winner_idx, combined_msg

    def execute(self, dgdtl_winners: List[int]) -> Tuple[bool, List[str]]:
        log = []
        if len(dgdtl_winners) == 0:
            return False, log

        t1 = dgdtl_winners[0]
        scout_1 = str(self.df_inter.loc[t1, 'Scout_Base']).strip()

        if len(dgdtl_winners) >= 2:
            t2 = dgdtl_winners[1]
            gap = abs(float(self.df_inter.loc[t1, 'U_MAXP_k']) - float(self.df_inter.loc[t2, 'U_MAXP_k'])) / (max(float(self.df_inter.loc[t1, 'U_MAXP_k']), float(self.df_inter.loc[t2, 'U_MAXP_k'])) + 1e-12)
            scout_2 = str(self.df_inter.loc[t2, 'Scout_Base']).strip()

            if scout_1 == scout_2:
                self.logger.warning("[PHASE 3 — INTRA-SCOUT SECURITY FILTER]")
                best_idx, loser_idx, msg2 = self.resolve_intra_scout(t1, t2)
                log.extend([f"  [!] Security Filter: Same scout ({scout_1}). Gap ignored.", msg2])
                self.logger.info(msg2)
                dgdtl_winners[0], dgdtl_winners[1] = best_idx, loser_idx
                self.df_inter.loc[loser_idx, 'Framework_Winner'] = 'DGDTL_TIE_LOSS'
                self.df_inter.loc[best_idx,  'Framework_Winner'] = 'DGDTL_TIE_WIN'
                return True, log

            if gap < ProtocolConfig.EPS_TIE:
                self.logger.warning("[PHASE 3 — DUAL TIE-BREAK]")
                s1_runs = self.df_c[self.df_c['Scout_Base'].str.strip() == scout_1]
                s2_runs = self.df_c[self.df_c['Scout_Base'].str.strip() == scout_2]

                if len(s1_runs) == 2 and len(s2_runs) == 2:
                    uc_1, uc_2 = self._compute_u_comp(scout_1), self._compute_u_comp(scout_2)
                    winning_scout, winning_runs, losing_runs = (scout_2, s2_runs, s1_runs) if uc_2 > uc_1 else (scout_1, s1_runs, s2_runs)
                    self.logger.info(f"  Step 3a (U_comp): {scout_1}={uc_1:.6f} vs {scout_2}={uc_2:.6f} -> Winner: {winning_scout}")
                else:
                    self.logger.warning("  Step 3a skipped: fallback to phi.")
                    phi_t1, phi_t2 = float(self.df_inter.loc[t1, 'phi']), float(self.df_inter.loc[t2, 'phi'])
                    best_idx, loser_idx = (t2, t1) if phi_t2 > phi_t1 else (t1, t2)
                    dgdtl_winners[0], dgdtl_winners[1] = best_idx, loser_idx
                    self.df_inter.loc[loser_idx, 'Framework_Winner'], self.df_inter.loc[best_idx, 'Framework_Winner'] = 'DGDTL_TIE_LOSS', 'DGDTL_TIE_WIN'
                    return True, log

                win_valid = winning_runs[winning_runs['F2_Winner'] == 'C'] if not winning_runs[winning_runs['F2_Winner'] == 'C'].empty else winning_runs
                lose_valid = losing_runs[losing_runs['F2_Winner'] == 'C']
                best_win = self.resolve_intra_scout(win_valid.index[0], win_valid.index[1])[0] if len(win_valid) == 2 else win_valid.index[0]
                best_lose = self.resolve_intra_scout(lose_valid.index[0], lose_valid.index[1])[0] if len(lose_valid) == 2 else (lose_valid.index[0] if len(lose_valid) == 1 else None)
                new_top = [best_win] + ([best_lose] if best_lose else []) + [i for i in win_valid.index if i != best_win]
                for x in new_top:
                    if x in dgdtl_winners:
                        dgdtl_winners.remove(x)
                dgdtl_winners[:0] = new_top
                self.df_inter.loc[dgdtl_winners[1], 'Framework_Winner'], self.df_inter.loc[dgdtl_winners[0], 'Framework_Winner'] = 'DGDTL_TIE_LOSS', 'DGDTL_TIE_WIN'
                return True, log

            msg = f"[PHASE 3 — NO DUAL TIE-BREAK] Gap {gap*100:.4f}% >= eps_tie. Proceeding to mandatory Intra-Scout Audit."
            self.logger.info(msg)
            log.append(msg)
        else:
            msg = f"[PHASE 3 — SINGLE SCOUT WINNER] Proceeding to mandatory Intra-Scout Audit."
            self.logger.info(msg)
            log.append(msg)

        self.logger.info(f"  [MANDATORY AUDIT] Evaluating inter-run consistency for scout: {scout_1}")
        s1_runs = self.df_c[self.df_c['Scout_Base'].str.strip() == scout_1]

        if len(s1_runs) == 2:
            best_idx, loser_idx, msg2 = self.resolve_intra_scout(s1_runs.index[0], s1_runs.index[1])
            self.logger.info(msg2)
            log.append(msg2)

            if best_idx != t1:
                override_msg = f"  >>> MANDATORY OVERRIDE: Structural consistency preferred {self.df_inter.loc[best_idx, 'Candidate_Label']} over volume leader {self.df_inter.loc[t1, 'Candidate_Label']} <<<"
                self.logger.success(override_msg)
                log.append(override_msg)

                if best_idx in dgdtl_winners:
                    dgdtl_winners.remove(best_idx)
                if t1 in dgdtl_winners:
                    dgdtl_winners.remove(t1)

                dgdtl_winners.insert(0, best_idx)
                dgdtl_winners.insert(1, t1)

                self.df_inter.loc[t1, 'Framework_Winner'] = 'DGDTL_TIE_LOSS'
                self.df_inter.loc[best_idx, 'Framework_Winner'] = 'DGDTL_TIE_WIN'
                return True, log
        else:
            self.logger.info(f"  Scout {scout_1} only has one run. Mandatory audit complete.")

        return False, log

    # Compatibility with previous u_maxp_core API.
    def resolve_tie(self, dgdtl_winners: List[int]) -> Tuple[bool, List[str]]:
        return self.execute(dgdtl_winners)

class StructuralSelectionProtocol:
    """
    Reference Structural Selection Protocol used by the validated Hunter.

    The protocol is logically distinct from the U-MaxP criterion.  It consumes
    U-MaxP-derived metrics and applies the current Line-A / Line-B policy.
    """

    def __init__(self, df: pd.DataFrame, source_name: str = "In-Memory Engine",
                 logger=None):
        self.df = df.copy()
        self.source_name = source_name
        self.logger = logger if logger is not None else _NullLogger
        self.line_label = ""

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
        self.df_final = None

        self._diag_cols = [
            'F1_Case', 'F1_Short', 'F1_Label', 'F1_Winner', 'F1_dUk', 'F1_dphi',
            'F2_Case', 'F2_Short', 'F2_Label', 'F2_Winner', 'F2_I', 'F2_G', 'F2_ratio_c', 'F2_I_val', 'F2_G_val',
            'Champion_Run', 'Framework_Winner', 'FA_Case', 'FA_Short', 'FA_Label',
            'FA_I_RT', 'FA_J_RT', 'FA_ev_c', 'FA_ev_rt', 'FA_delta_ev_pct', 'FA_phi_c', 'FA_phi_rt', 'Is_Final_Champion',
            'ICV', 'Psi_Rank', 'VBD_Verdict'
        ]

    def _prepare_data(self):
        mask_base = self.df['Scout_Base'].str.contains('BASELINE', na=False)
        self.df_base = self.df[mask_base].copy()

        idx_hm = self.df_base['U_MAXP_k'].astype(float).idxmax()
        self.uk_hm, self.label_hm = float(self.df_base.loc[idx_hm, 'U_MAXP_k']), str(self.df_base.loc[idx_hm, 'Candidate_Label'])

        tr_only_rows = self.df_base[self.df_base['Scout_Base'] == 'BASELINE_TRAIN_ONLY']
        if tr_only_rows.empty:
            self.logger.error("[CRITICAL] BASELINE_TRAIN_ONLY not found in generated records.", indent=0)
            raise SystemExit(1)

        self.tr_only = tr_only_rows.iloc[0]
        self.e_ref_val, self.e_ref_tr = float(self.tr_only['E_Valid']), float(self.tr_only['E_Train'])
        self.ratio_ref = self.e_ref_val / (self.e_ref_tr + 1e-12)

        self.rt_rows = self.df_base[self.df_base['Scout_Base'] == 'BASELINE_RETRAIN']
        self.uk_retrain = float(self.rt_rows.iloc[0]['U_MAXP_k']) if not self.rt_rows.empty else 0.0
        self.has_retrain = not self.rt_rows.empty

        self.df['Psi'], self.df['Regime'], self.df['psi_G'] = 0.0, 'INC', 0.0
        for idx in self.df.index:
            m = StructuralMetricsEngine.compute_psi_metrics(self.df.loc[idx], self.tr_only)
            self.df.loc[idx, ['Psi', 'Regime', 'psi_G']] = [m['Psi'], m['Regime'], m['psi_G']]

        self.df_cands = self.df[~mask_base].copy()

        vbd_scouts = set()
        total_scouts = self.df_cands['Scout_Base'].nunique()
        for scout in self.df_cands['Scout_Base'].unique():
            s = self.df_cands[self.df_cands['Scout_Base'] == scout]
            if len(s) == 2:
                r1, r2 = s.iloc[0], s.iloc[1]
                if {r1['Regime'], r2['Regime']} == {'SOV', 'OFT'} and r1['Psi'] > ProtocolConfig.EPS_PSI and r2['Psi'] > ProtocolConfig.EPS_PSI:
                    vbd_scouts.add(scout)
        self.pi_vbd = len(vbd_scouts) / total_scouts if total_scouts > 0 else 0.0

        for col in self._diag_cols:
            self.df[col] = pd.Series(dtype='object')

        self.df['Is_Final_Champion'] = False
        self.df.loc[mask_base, ['Champion_Run', 'Framework_Winner']] = ['N/A', 'BASELINE']

    def _execute_phases_1_and_2(self):
        self.logger.section("PHASE 1 & 2 — GLOBAL LABELING FOR ALL CANDIDATES")
        for scout in self.df_cands['Scout_Base'].unique():
            s = self.df_cands[self.df_cands['Scout_Base'] == scout]
            r1, r2 = s[s['Run_ID'] == 1], s[s['Run_ID'] == 2]

            if r1.empty and r2.empty:
                continue
            if r1.empty or r2.empty:
                idx_c = r2.index[0] if r1.empty else r1.index[0]
                self.df.loc[idx_c, ['F1_Case','F1_Short','F1_Label','F1_Winner','Champion_Run']] = ['F1.X', 'SNG', ProtocolVerdictCodes.PHASE1['F1.X'][1], 'B' if r1.empty else 'A', 2 if r1.empty else 1]
                continue

            idx_a, idx_b = r1.index[0], r2.index[0]
            res = PhaseEvaluator.evaluate_phase1(self.df.loc[idx_a], self.df.loc[idx_b])

            for idx in [idx_a, idx_b]:
                self.df.loc[idx, ['F1_Case', 'F1_Short', 'F1_Label', 'F1_Winner', 'F1_dUk', 'F1_dphi']] = [res['case'], res['short'], res['label'], res['winner'], round(res['delta_uk'], 8), round(res['delta_phi'], 8)]
            self.df.loc[idx_b if res['winner'] == 'B' else idx_a, 'Champion_Run'] = 2 if res['winner'] == 'B' else 1

        for idx_c in self.df_cands.index:
            res2 = PhaseEvaluator.evaluate_phase2(self.df.loc[idx_c], self.uk_hm, self.ratio_ref, self.uk_retrain)
            self.df.loc[idx_c, ['F2_Case', 'F2_Short', 'F2_Label', 'F2_Winner', 'F2_I', 'F2_G', 'F2_ratio_c', 'F2_I_val', 'F2_G_val']] = [res2['case'], res2['short'], res2['label'], res2['winner'], res2['I'], res2['G'], round(res2['ratio_c'], 8), round(res2['I_val'], 8), round(res2['G_val'], 8)]
            self.df.loc[idx_c, 'Framework_Winner'] = 'DGDTL_RT' if res2['case'] == 'F2.2-RT' else 'DGDTL' if res2['winner'] == 'C' else 'BASELINE'

        valid_pool = self.df['F2_Winner'] == 'C'
        self.dgdtl_winners = self.df[valid_pool].sort_values(by='U_MAXP_k', ascending=False).index.tolist()

    def _execute_phase_3(self):
        self.logger.section("PHASE 3 — POST-HOC DUAL TIE-BREAK")
        tie_breaker = Phase3TieBreaker(self.df, logger=self.logger)
        self.phase3_active, self.tie_break_log = tie_breaker.execute(self.dgdtl_winners)

    def _execute_f1_vb(self):
        if not self.dgdtl_winners:
            return

        df_c = self.df[~self.df['Scout_Base'].str.contains('BASELINE', na=False)]

        sov_candidates = []
        for idx in self.dgdtl_winners:
            row = self.df.loc[idx]
            if row['Regime'] != 'SOV':
                continue
            if row['Psi'] <= ProtocolConfig.EPS_PSI:
                continue
            if row['U_MAXP_k'] <= ProtocolConfig.EPS_F:
                continue

            twins = df_c[
                (df_c['Scout_Base'] == row['Scout_Base']) &
                (df_c.index != idx) &
                (df_c['Regime'] == 'OFT') &
                (df_c['Psi'] > ProtocolConfig.EPS_PSI)
            ]
            if twins.empty:
                continue

            lb_res = PhaseEvaluator.evaluate_line_b(self.df, df_c, idx, self.tr_only, self.rt_rows)
            if lb_res.get('twin_label'):
                sov_candidates.append((idx, lb_res))

        if not sov_candidates:
            return

        self.f1_vb_active = True

        icv_scores = [lb['icv'] for _, lb in sov_candidates]
        n_corpus = len(icv_scores)
        psi_rank_active = (n_corpus >= ProtocolConfig.PSI_RANK_N_MIN)
        sorted_icv = sorted(icv_scores)

        def _psi_rank(icv_val: float) -> Optional[float]:
            if not psi_rank_active:
                return None
            pos = sorted_icv.index(icv_val)
            return (pos + 1) / n_corpus

        promoted_once = False
        self.logger.warning(">>> [F1-VB] VBD-Audit v2.0 — Corpus Scan Initiated <<<")

        for c_star_idx, lb_res in sov_candidates:
            c_star_row = self.df.loc[c_star_idx]
            twin_idx = lb_res['twin_idx']
            icv = lb_res['icv']
            psi_rank = _psi_rank(icv)

            lb_res['psi_rank'] = psi_rank
            lb_res['psi_rank_active'] = psi_rank_active

            if icv > ProtocolConfig.ICV_STRONG:
                if psi_rank_active:
                    vbd_verdict = 'VBD_STABLE' if psi_rank >= ProtocolConfig.PSI_RANK_MIN else 'VBD_FRAGILE'
                else:
                    vbd_verdict = 'VBD_STABLE'
            elif icv > ProtocolConfig.ICV_CONDITIONAL:
                vbd_verdict = 'VBD_CONDITIONAL'
            else:
                vbd_verdict = 'VBD_DIAGNOSTIC'

            lb_res['vbd_verdict'] = vbd_verdict

            self.df.loc[twin_idx, 'ICV'] = round(icv, 6)
            self.df.loc[twin_idx, 'Psi_Rank'] = round(psi_rank, 4) if psi_rank is not None else np.nan
            self.df.loc[twin_idx, 'VBD_Verdict'] = vbd_verdict

            promoted = False

            if vbd_verdict in ('VBD_STABLE', 'VBD_FRAGILE', 'VBD_CONDITIONAL') and not promoted_once:
                if twin_idx in self.dgdtl_winners:
                    self.dgdtl_winners.remove(twin_idx)
                self.dgdtl_winners.insert(0, twin_idx)

                self.df.loc[twin_idx, 'Framework_Winner'] = 'DGDTL_VBD_WIN'
                self.df.loc[c_star_idx, 'Framework_Winner'] = 'DGDTL_VBD_LOSS'

                promoted = True
                promoted_once = True

                psi_rank_str = f"{psi_rank:.4f}" if psi_rank is not None else f"N/A (N={n_corpus}<{ProtocolConfig.PSI_RANK_N_MIN})"
                self.logger.success(
                    f">>> LINE B PROMOTION [{vbd_verdict}]: "
                    f"{lb_res['twin_label']} overrides {c_star_row['Candidate_Label']} "
                    f"(ICV={icv:.4f}  Psi-Rank={psi_rank_str}) <<<"
                )
            else:
                self.logger.info(
                    f"  [VBD_DIAGNOSTIC] {c_star_row['Candidate_Label']} retained "
                    f"(ICV={icv:.4f} <= threshold={ProtocolConfig.ICV_CONDITIONAL:.2f}). Logged only."
                )

            if 'audits' not in self.f1_vb_data:
                self.f1_vb_data = {'pi_vbd': self.pi_vbd, 'audits': []}
            self.f1_vb_data['audits'].append({
                'sov_idx': c_star_idx,
                'twin_idx': twin_idx,
                'sov_label': c_star_row['Candidate_Label'],
                'twin_label': lb_res['twin_label'],
                'psi_sov': self.df.loc[c_star_idx, 'Psi'],
                'uk_sov': self.df.loc[c_star_idx, 'U_MAXP_k'],
                'psi_G_twin': self.df.loc[twin_idx, 'psi_G'],
                'icv': icv, 'psi_rank': psi_rank,
                'verdict': vbd_verdict, 'action': 'PROMOTED' if promoted else 'DIAGNOSTIC_ONLY',
                'lb_res': lb_res,
            })

    def _execute_phase_4(self):
        self.logger.section("PHASE 4 — OBSERVABLE DOMINANCE AUDIT (vs. BL_RT)")
        if not self.has_retrain or not self.dgdtl_winners:
            self.logger.warning("[~] Phase 4 skipped or not applicable.")
            return

        row_rt = self.rt_rows.iloc[0]
        for idx in self.dgdtl_winners:
            aud = PhaseEvaluator.evaluate_phase4(self.df.loc[idx], row_rt)
            self.df.loc[idx, ['FA_Case', 'FA_Short', 'FA_Label', 'FA_I_RT', 'FA_J_RT', 'FA_ev_c', 'FA_ev_rt', 'FA_delta_ev_pct', 'FA_phi_c', 'FA_phi_rt']] = [aud['case'], aud['short'], aud['label'], aud['I_RT'], aud['J_RT'], round(aud['ev_c'], 8), round(aud['ev_rt'], 8), round(aud['delta_ev_pct'], 4), round(aud['phi_c'], 8), round(aud['phi_rt'], 8)]

        aud_champ = PhaseEvaluator.evaluate_phase4(self.df.loc[self.dgdtl_winners[0]], row_rt)
        self.logger.success(f">>> [{aud_champ['short']}] {aud_champ['case']} — {aud_champ['short_label']}")

    def _finalize_ranking(self):
        if self.dgdtl_winners:
            self.df.loc[self.dgdtl_winners[0], 'Is_Final_Champion'] = True

        losers_idx = self.df[~self.df.index.isin(self.dgdtl_winners + self.df_base.index.tolist())].sort_values(by='U_MAXP_k', ascending=False).index.tolist()
        final_indices = self.dgdtl_winners + self.df_base.index.tolist() + losers_idx

        df_final = self.df.loc[final_indices].copy()

        if 'Rank' in df_final.columns:
            df_final.drop(columns=['Rank'], inplace=True)
        df_final.insert(0, 'Rank', list(range(1, len(df_final) + 1)))

        orig_cols = [c for c in df_final.columns if c not in self._diag_cols and c not in ['Psi', 'Regime', 'psi_G', 'Is_Final_Champion']]
        self.df_final = df_final[orig_cols + ['Psi', 'Regime', 'psi_G'] + self._diag_cols]
        return self.df_final

    def execute(self):
        self._prepare_data()
        self._execute_phases_1_and_2()
        self._execute_phase_3()
        self._execute_f1_vb()
        self._execute_phase_4()
        return self._finalize_ranking()

class StructuralFramework:
    """Compatibility façade for the static structural API."""

    compute_psi_metrics = staticmethod(StructuralMetricsEngine.compute_psi_metrics)
    phase1_criterion = staticmethod(PhaseEvaluator.evaluate_phase1)
    phase2_criterion = staticmethod(PhaseEvaluator.evaluate_phase2)
    phase4_audit = staticmethod(PhaseEvaluator.evaluate_phase4)

    def run_line_b(df: pd.DataFrame, df_cands: pd.DataFrame, dgdtl_winners: List[int], tr_only: pd.Series, rt_rows: pd.DataFrame, uk_hm: float) -> Dict:
        if not dgdtl_winners: return {'active': False, 'reason': 'No DGDTL-LTS winners — Line B not applicable.'}
        
        c_star_idx = dgdtl_winners[0]
        c_star_row = df.loc[c_star_idx]
        scout = c_star_row['Scout_Base']

        s = df_cands[df_cands['Scout_Base'] == scout]
        twin_candidates = [idx for idx in s.index if idx != c_star_idx and df.loc[idx, 'Regime'] == 'OFT' and df.loc[idx, 'Psi'] > EPS_PSI]

        if not twin_candidates:
            return {'active': True, 'twin_label': None, 'verdict': 'NO_TWIN', 'reason': f'No valid OFT twin found in scout {scout}.', 'c_star_A': c_star_row['Candidate_Label']}

        twin_idx = sorted(twin_candidates, key=lambda i: (-float(df.loc[i, 'psi_G']), abs(float(df.loc[i, 'Psi']))))[0]
        twin_row = df.loc[twin_idx]

        mae_tr_bl, mae_val_bl = float(tr_only['MAE_Train']) + 1e-12, float(tr_only['MAE_Valid'])
        mse_tr_bl, mse_val_bl = float(tr_only['MSE_Train']) + 1e-12, float(tr_only['MSE_Valid'])
        psi_G_bl_tr = np.sqrt((mae_val_bl / mae_tr_bl) * (np.sqrt(mse_val_bl) / np.sqrt(mse_tr_bl)))

        has_retrain = not rt_rows.empty
        psi_bl_rt = abs(StructuralFramework.compute_psi_metrics(rt_rows.iloc[0], tr_only)['Psi']) if has_retrain else 0.0

        psi_G_twin, psi_twin_abs = float(twin_row['psi_G']), abs(float(twin_row['Psi']))
        crit_1, crit_2 = bool(psi_G_twin > psi_G_bl_tr), bool(psi_twin_abs < psi_bl_rt) if has_retrain else False

        if crit_1 and crit_2: lb_verdict, lb_verdict_txt = 'LB_FULL', 'Twin surpasses BOTH domain references.'
        elif crit_1: lb_verdict, lb_verdict_txt = 'LB_TRAIN_ONLY', 'Twin surpasses BL_TR but NOT BL_RT.'
        elif crit_2: lb_verdict, lb_verdict_txt = 'LB_RETRAIN_ONLY', 'Twin surpasses BL_RT but NOT BL_TR.'
        else: lb_verdict, lb_verdict_txt = 'LB_NONE', 'Twin surpasses neither reference. Diagnostic only.'

        sde_twin, sde_cstar = float(twin_row['SDE_b']), float(c_star_row['SDE_b'])
        sde_ratio = (sde_twin / sde_cstar) if sde_cstar > 0 else 0.0
        topo_class = 'ROBUST' if sde_ratio > 0.5 else ('SENSITIVE' if sde_ratio > 0 else 'UNAVAILABLE')

        uk_twin, uk_c_star, psi_c_star = float(twin_row['U_MAXP_k']), float(c_star_row['U_MAXP_k']), abs(float(c_star_row['Psi']))
        p_coh = bool((uk_twin < uk_c_star) and (psi_twin_abs < psi_c_star))

        return {
            'active': True, 'is_nuance2': len(twin_candidates) > 1, 'c_star_A': c_star_row['Candidate_Label'],
            'twin_label': twin_row['Candidate_Label'], 'twin_idx': twin_idx, 'twin_regime': twin_row['Regime'],
            'psi_twin': float(twin_row['Psi']), 'psi_twin_abs': psi_twin_abs, 'psi_G_twin': psi_G_twin,
            'psi_G_bl_tr': psi_G_bl_tr, 'psi_bl_rt': psi_bl_rt, 'sde_twin': sde_twin, 'sde_cstar': sde_cstar,
            'sde_ratio': sde_ratio, 'crit_1': crit_1, 'crit_2': crit_2, 'has_retrain': has_retrain,
            'lb_verdict': lb_verdict, 'lb_verdict_txt': lb_verdict_txt, 'topo_class': topo_class,
            'p_coh': p_coh, 'uk_twin': uk_twin, 'uk_c_star': uk_c_star, 'psi_c_star': psi_c_star,
            'e_val_twin': float(twin_row['E_Valid']), 'n_twins_found': len(twin_candidates), 'verdict': lb_verdict
        }

__all__ = [
    'EPS_F', 'DELTA_REL', 'EPS_TIE', 'EPS_PSI',
    'ProtocolConfig', 'ProtocolVerdictCodes',
    'TopologicalEngine', 'EVTAnalyzer', 'ConsistencyEngine', 'UMaxPCriterion',
    'StructuralMetricsEngine', 'FrameworkMetricsEngine',
    'u_comp_operator', 'e_inc_operator', 'MicroArbitration',
    'PhaseEvaluator', 'Phase3TieBreaker', 'StructuralSelectionProtocol',
    'StructuralFramework',
]
