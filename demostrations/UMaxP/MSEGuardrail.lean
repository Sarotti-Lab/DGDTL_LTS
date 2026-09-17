-- SPDX-FileCopyrightText: 2026 José A. Pérez
-- SPDX-License-Identifier: MIT
--

-- ==============================================================================
-- FILE: DGDTL/Protocol/MSEGuardrail.lean
-- OBJECTIVE: Formalization of the MSE Tail Guardrail
-- REFERENCE: Section 3.3, Supplementary Information (DGDTL-LTS)
-- ==============================================================================

import Mathlib.Analysis.SpecialFunctions.Exp
import Mathlib.Data.Real.Basic
import Mathlib.Order.Bounds.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Positivity

/-!
# MSE Tail Guardrail Framework (Strict Refactoring)
Formalization of the structural Pareto dominance block.
-/

namespace GuardrailFramework

/-- Structural parameters of the system. -/
structure SystemParameters where
  τ_anch    : ℝ
  δ_eff     : ℝ
  ε_tie     : ℝ
  h_eff_pos : 0 < δ_eff
  h_eps_pos : 0 < ε_tie

/-- Metrics recorded during a specific algorithmic run. -/
structure RunMetrics where
  MSE_val   : ℝ
  e_max_rob : ℝ
  SDEb      : ℝ
  GCI       : ℝ
  Φ_arb     : ℝ

/-- Normalized empirical excess (Φ_emp) penalty. -/
noncomputable def Φ_emp (p : SystemParameters) (m : RunMetrics) : ℝ :=
  max 0 ((m.e_max_rob - p.τ_anch) / p.δ_eff)

/-- Empirical authenticity barrier (A_emp). -/
noncomputable def A_emp (p : SystemParameters) (m : RunMetrics) : ℝ :=
  Real.exp (- (Φ_emp p m ^ 2))

/-- Definition of the three-dimensional Pareto space. -/
structure ParetoPoint where
  SDEb  : ℝ
  GCI   : ℝ
  A_emp : ℝ

noncomputable def toParetoPoint (p : SystemParameters) (m : RunMetrics) : ParetoPoint :=
  ⟨m.SDEb, m.GCI, A_emp p m⟩

/-- Strict Pareto dominance relation. -/
def pareto_dominates (pt1 pt2 : ParetoPoint) : Prop :=
  (pt1.SDEb ≥ pt2.SDEb ∧ pt1.GCI ≥ pt2.GCI ∧ pt1.A_emp ≥ pt2.A_emp) ∧
  (pt1.SDEb > pt2.SDEb ∨ pt1.GCI > pt2.GCI ∨ pt1.A_emp > pt2.A_emp)

/-! ### 1. Explicit Pareto Blocking Theorem -/

/--
SUPPLEMENTARY THEOREM 3.1: Impossibility of Strict Pareto Dominance.
A strict degradation in the empirical authenticity barrier systematically
blocks any possibility of Pareto dominance.
-/
theorem A_emp_drop_blocks_pareto (p : SystemParameters) (m1 m2 : RunMetrics)
    (hA : A_emp p m2 < A_emp p m1) :
    ¬ pareto_dominates (toParetoPoint p m2) (toParetoPoint p m1) := by
  intro hPareto
  rcases hPareto with ⟨hweak, _⟩
  rcases hweak with ⟨_, _, hA_ge⟩
  change A_emp p m2 ≥ A_emp p m1 at hA_ge
  linarith

/-! ### 2. Strict Monotonicity Hypothesis -/

/-- Strict MSE Tail Monotonicity Hypothesis. -/
def MSE_Monotonicity_Hypothesis_Strict (m1 m2 : RunMetrics) : Prop :=
  m2.MSE_val > m1.MSE_val → m2.e_max_rob > m1.e_max_rob

/-! ### 3. Main Theorem: Strict Degradation -/

/--
SUPPLEMENTARY PROPOSITION 3.1 (First Half): MSE tail guardrail as a strict non-dominance safeguard.
Demonstrates that an increase in MSE strictly degrades the authenticity
barrier, formally blocking Pareto dominance via Supplementary Theorem 3.1.
-/
theorem prop_guardrail_pareto_strict (p : SystemParameters) (m1 m2 : RunMetrics)
    (h_mono : MSE_Monotonicity_Hypothesis_Strict m1 m2)
    (h_mse_degradation : m2.MSE_val > m1.MSE_val)
    (h_tail_active : m1.e_max_rob > p.τ_anch) :
    Φ_emp p m2 > Φ_emp p m1 ∧
    A_emp p m2 < A_emp p m1 ∧
    ¬ pareto_dominates (toParetoPoint p m2) (toParetoPoint p m1) := by

  have h_emax : m2.e_max_rob > m1.e_max_rob := h_mono h_mse_degradation

  have h_arg1_pos : 0 < (m1.e_max_rob - p.τ_anch) / p.δ_eff :=
    div_pos (by linarith) p.h_eff_pos

  have h_arg2_pos : 0 < (m2.e_max_rob - p.τ_anch) / p.δ_eff :=
    div_pos (by linarith) p.h_eff_pos

  have h_diff_strict : m2.e_max_rob - p.τ_anch > m1.e_max_rob - p.τ_anch := by linarith
  have h_div_strict : (m2.e_max_rob - p.τ_anch) / p.δ_eff > (m1.e_max_rob - p.τ_anch) / p.δ_eff :=
    div_lt_div_of_pos_right h_diff_strict p.h_eff_pos

  have h_phi : Φ_emp p m2 > Φ_emp p m1 := by
    unfold Φ_emp
    rw [max_eq_right (le_of_lt h_arg2_pos), max_eq_right (le_of_lt h_arg1_pos)]
    exact h_div_strict

  have h_phi1_pos : 0 < Φ_emp p m1 := by
    unfold Φ_emp
    rw [max_eq_right (le_of_lt h_arg1_pos)]
    exact h_arg1_pos

  have h_sq_strict : Φ_emp p m1 ^ 2 < Φ_emp p m2 ^ 2 := by
    nlinarith [h_phi1_pos, h_phi]

  have h_neg_sq_strict : - (Φ_emp p m2 ^ 2) < - (Φ_emp p m1 ^ 2) := by linarith

  have h_aexp_strict : A_emp p m2 < A_emp p m1 := by
    unfold A_emp
    exact Real.exp_lt_exp.mpr h_neg_sq_strict

  have hBlock : ¬ pareto_dominates (toParetoPoint p m2) (toParetoPoint p m1) :=
    A_emp_drop_blocks_pareto p m1 m2 h_aexp_strict

  exact ⟨h_phi, h_aexp_strict, hBlock⟩

/-! ### 3b. Second half of Supplementary Proposition 3.1 -/

/--
Necessity of structural margin for scalar compensation.
If A_emp strictly degrades (R2 < R1) and yet the aggregate U-MaxP metric
favors R2 (scalar compensation U-MaxP(R2) > U-MaxP(R1)), then the structural
core (SDEb · GCI) must have strictly improved.

This formalizes the second logical condition of Supplementary Proposition 3.1:
"Any scalar compensation would require S_DEb(R2)·G_CI(R2) > S_DEb(R1)·G_CI(R1)".
It operates as the logical reverse of the Strict Mode Non-Compensation theorem.
-/
theorem scalar_compensation_requires_structural_margin
    (p : SystemParameters) (m1 m2 : RunMetrics)
    (hAemp_pos2 : 0 < A_emp p m2)
    (hcore1_pos : 0 < m1.SDEb * m1.GCI)
    (hAemp_drop : A_emp p m2 < A_emp p m1)
    (hUMaxP : m2.SDEb * m2.GCI * A_emp p m2 > m1.SDEb * m1.GCI * A_emp p m1) :
    m2.SDEb * m2.GCI > m1.SDEb * m1.GCI := by
  by_contra hcontra
  push Not at hcontra -- Corrected for Lean 4 v4.32.0-rc1
  have hstep1 : m2.SDEb * m2.GCI * A_emp p m2 ≤ m1.SDEb * m1.GCI * A_emp p m2 :=
    mul_le_mul_of_nonneg_right hcontra hAemp_pos2.le
  have hstep2 : m1.SDEb * m1.GCI * A_emp p m2 < m1.SDEb * m1.GCI * A_emp p m1 :=
    mul_lt_mul_of_pos_left hAemp_drop hcore1_pos
  linarith

end GuardrailFramework
