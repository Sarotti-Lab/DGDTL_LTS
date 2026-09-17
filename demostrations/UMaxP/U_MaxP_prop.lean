-- SPDX-FileCopyrightText: 2026 José A. Pérez
-- SPDX-License-Identifier: MIT
--

-- ==============================================================================
-- FILE: DGDTL/Theory/UMaxP_Properties.lean
-- OBJECTIVE: Formal Properties of the U-MaxP Criterion
-- REFERENCE: Section 2.6, Supplementary Information (DGDTL-LTS)
-- ==============================================================================

import Mathlib.Data.Real.Basic
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Tactic

open Real

-- Disable the unused variables warning to strictly preserve exact signatures
set_option linter.unusedVariables false

noncomputable section

-- ============================================================
-- DEFINITION OF U-MaxP
-- ============================================================

/--
Equation (S22): The Unified Maximum A Posteriori (U-MaxP) Criterion.
Normalized volumetric multiplicative metric over the three-dimensional quality space.
-/
def UMaxP (SDEb GCI A_emp : ℝ) : ℝ :=
  SDEb * GCI * A_emp

-- ============================================================
-- THEOREM: BOUNDEDNESS
-- ============================================================

/--
SUPPLEMENTARY THEOREM 2.2: Boundedness of U-MaxP.
If all components belong to (0,1], then U-MaxP strictly maps to (0,1].
This guarantees a dimensionless, strictly normalized metric.
-/
theorem umaxp_bounded
    {SDEb GCI A_emp : ℝ}
    (hS_pos : 0 < SDEb) (hS_le : SDEb ≤ 1)
    (hG_pos : 0 < GCI) (hG_le : GCI ≤ 1)
    (hA_pos : 0 < A_emp) (hA_le : A_emp ≤ 1) :
    0 < UMaxP SDEb GCI A_emp ∧ UMaxP SDEb GCI A_emp ≤ 1 := by

  unfold UMaxP
  constructor
  -- Strict Positivity
  · have hsg : 0 < SDEb * GCI := mul_pos hS_pos hG_pos
    exact mul_pos hsg hA_pos
  -- Upper Bound
  · have hsg : SDEb * GCI ≤ 1 := by nlinarith
    have hsga : SDEb * GCI * A_emp ≤ 1 * A_emp :=
      mul_le_mul_of_nonneg_right hsg (le_of_lt hA_pos)
    nlinarith

-- ============================================================
-- PROPOSITION: MONOTONICITY
-- ============================================================

/--
SUPPLEMENTARY PROPOSITION 2.8: Strict Monotonicity.
U-MaxP is strictly increasing with respect to each component when the others
are held constant (corresponding to positive partial derivatives).
-/
theorem umaxp_monotone_SDEb
    {SDEb₁ SDEb₂ GCI A_emp : ℝ}
    (hG_pos : 0 < GCI)
    (hA_pos : 0 < A_emp)
    (hS : SDEb₁ < SDEb₂) :
    UMaxP SDEb₁ GCI A_emp < UMaxP SDEb₂ GCI A_emp := by
  unfold UMaxP
  have h1 : SDEb₁ * GCI < SDEb₂ * GCI := mul_lt_mul_of_pos_right hS hG_pos
  exact mul_lt_mul_of_pos_right h1 hA_pos

theorem umaxp_monotone_GCI
    {SDEb GCI₁ GCI₂ A_emp : ℝ}
    (hS_pos : 0 < SDEb)
    (hA_pos : 0 < A_emp)
    (hG : GCI₁ < GCI₂) :
    UMaxP SDEb GCI₁ A_emp < UMaxP SDEb GCI₂ A_emp := by
  unfold UMaxP
  have h1 : SDEb * GCI₁ < SDEb * GCI₂ := mul_lt_mul_of_pos_left hG hS_pos
  exact mul_lt_mul_of_pos_right h1 hA_pos

theorem umaxp_monotone_A_emp
    {SDEb GCI A_emp₁ A_emp₂ : ℝ}
    (hS_pos : 0 < SDEb)
    (hG_pos : 0 < GCI)
    (hA : A_emp₁ < A_emp₂) :
    UMaxP SDEb GCI A_emp₁ < UMaxP SDEb GCI A_emp₂ := by
  unfold UMaxP
  have hsg : 0 < SDEb * GCI := mul_pos hS_pos hG_pos
  exact mul_lt_mul_of_pos_left hA hsg

-- ============================================================
-- PROPOSITION: PARETO CONSISTENCY
-- ============================================================

/--
SUPPLEMENTARY PROPOSITION 2.9: Pareto Dominance Consistency.
If all dimensions improve or remain equal, and at least one improves strictly,
then the global U-MaxP metric improves strictly.
-/
theorem pareto_consistency
    {SDEb₁ SDEb₂ GCI₁ GCI₂ A_emp₁ A_emp₂ : ℝ}
    (hS_pos : 0 < SDEb₂) (hG_pos : 0 < GCI₂) (hA_pos : 0 < A_emp₂)
    (hS : SDEb₂ ≤ SDEb₁) (hG : GCI₂ ≤ GCI₁) (hA : A_emp₂ ≤ A_emp₁)
    (h_strict : SDEb₂ < SDEb₁ ∨ GCI₂ < GCI₁ ∨ A_emp₂ < A_emp₁) :
    UMaxP SDEb₂ GCI₂ A_emp₂ < UMaxP SDEb₁ GCI₁ A_emp₁ := by

  unfold UMaxP

  have hS_nonneg : 0 ≤ SDEb₂ := le_of_lt hS_pos
  have hG_nonneg : 0 ≤ GCI₂ := le_of_lt hG_pos
  have hA_nonneg : 0 ≤ A_emp₂ := le_of_lt hA_pos
  have hS1_nonneg : 0 ≤ SDEb₁ := le_trans hS_nonneg hS
  have hG1_nonneg : 0 ≤ GCI₁ := le_trans hG_nonneg hG

  rcases h_strict with hS_strict | hG_strict | hA_strict

  -- Case 1: Strict improvement in SDEb
  · have h1 : SDEb₂ * GCI₂ < SDEb₁ * GCI₂ := mul_lt_mul_of_pos_right hS_strict hG_pos
    have h2 : SDEb₁ * GCI₂ ≤ SDEb₁ * GCI₁ := mul_le_mul_of_nonneg_left hG hS1_nonneg
    have hcore : SDEb₂ * GCI₂ < SDEb₁ * GCI₁ := lt_of_lt_of_le h1 h2
    have hmain : (SDEb₂ * GCI₂) * A_emp₂ < (SDEb₁ * GCI₁) * A_emp₂ := mul_lt_mul_of_pos_right hcore hA_pos
    have hfinal : (SDEb₁ * GCI₁) * A_emp₂ ≤ (SDEb₁ * GCI₁) * A_emp₁ :=
      mul_le_mul_of_nonneg_left hA (mul_nonneg hS1_nonneg hG1_nonneg)
    exact lt_of_lt_of_le hmain hfinal

  -- Case 2: Strict improvement in GCI
  · have h1 : SDEb₂ * GCI₂ < SDEb₂ * GCI₁ := mul_lt_mul_of_pos_left hG_strict hS_pos
    have h2 : SDEb₂ * GCI₁ ≤ SDEb₁ * GCI₁ := mul_le_mul_of_nonneg_right hS hG1_nonneg
    have hcore : SDEb₂ * GCI₂ < SDEb₁ * GCI₁ := lt_of_lt_of_le h1 h2
    have hmain : (SDEb₂ * GCI₂) * A_emp₂ < (SDEb₁ * GCI₁) * A_emp₂ := mul_lt_mul_of_pos_right hcore hA_pos
    have hfinal : (SDEb₁ * GCI₁) * A_emp₂ ≤ (SDEb₁ * GCI₁) * A_emp₁ :=
      mul_le_mul_of_nonneg_left hA (mul_nonneg hS1_nonneg hG1_nonneg)
    exact lt_of_lt_of_le hmain hfinal

  -- Case 3: Strict improvement in A_emp
  · have hcore : SDEb₂ * GCI₂ ≤ SDEb₁ * GCI₁ := mul_le_mul hS hG hG_nonneg hS1_nonneg
    have hsg_pos : 0 < SDEb₁ * GCI₁ := by
      have hs1_pos : 0 < SDEb₁ := lt_of_lt_of_le hS_pos hS
      have hg1_pos : 0 < GCI₁ := lt_of_lt_of_le hG_pos hG
      exact mul_pos hs1_pos hg1_pos
    have hmain : (SDEb₂ * GCI₂) * A_emp₂ ≤ (SDEb₁ * GCI₁) * A_emp₂ := mul_le_mul_of_nonneg_right hcore hA_nonneg
    have hfinal : (SDEb₁ * GCI₁) * A_emp₂ < (SDEb₁ * GCI₁) * A_emp₁ := mul_lt_mul_of_pos_left hA_strict hsg_pos
    exact lt_of_le_of_lt hmain hfinal

-- ============================================================
-- PROPOSITION: VOLUMETRIC INTERPRETATION
-- ============================================================

/--
SUPPLEMENTARY PROPOSITION 2.10: Volumetric interpretation.
U-MaxP defines a normalized volumetric measure over the unit cube (0,1]^3,
evaluating the relative volume of the model within the admissible performance space.
-/
theorem volumetric_interpretation
    {SDEb GCI A_emp : ℝ}
    (hS_pos : 0 < SDEb) (hS_le : SDEb ≤ 1)
    (hG_pos : 0 < GCI) (hG_le : GCI ≤ 1)
    (hA_pos : 0 < A_emp) (hA_le : A_emp ≤ 1) :
    0 < UMaxP SDEb GCI A_emp ∧ UMaxP SDEb GCI A_emp ≤ 1 := by
  exact umaxp_bounded hS_pos hS_le hG_pos hG_le hA_pos hA_le

-- ============================================================
-- LOG-ADDITIVE IDENTITY
-- ============================================================

/--
Logarithmic representation.
log(U-MaxP) = log(SDEb) + log(GCI) + log(A_emp).
Connects the criterion to classical log-linear representations from information theory.
-/
theorem umaxp_log_additive
    {SDEb GCI A_emp : ℝ} (hS : 0 < SDEb) (hG : 0 < GCI) (hA : 0 < A_emp) :
    Real.log (UMaxP SDEb GCI A_emp) = Real.log SDEb + Real.log GCI + Real.log A_emp := by
  unfold UMaxP
  rw [Real.log_mul (mul_ne_zero (ne_of_gt hS) (ne_of_gt hG)) (ne_of_gt hA),
      Real.log_mul (ne_of_gt hS) (ne_of_gt hG)]

-- ============================================================
-- COROLLARY: COLLAPSE UPON SINGLE-DIMENSION FAILURE
-- ============================================================

/--
SUPPLEMENTARY COROLLARY 2.1: Collapse.
If ANY of the three components is exactly zero, the global metric collapses to zero.
Formalizes the principle of structural prudence.
-/
theorem collapse_dimension_any
    {SDEb GCI A_emp : ℝ}
    (h : SDEb = 0 ∨ GCI = 0 ∨ A_emp = 0) :
    UMaxP SDEb GCI A_emp = 0 := by
  unfold UMaxP
  rcases h with h | h | h <;> simp [h]

/-- Auxiliary bounding lemma: the product of a factor ≤ ε with two factors in (0,1] is bounded by ε. -/
private lemma prod_le_of_first_small
    {x y z ε : ℝ}
    (hx_pos : 0 < x) (hx_le : x ≤ ε)
    (hy_pos : 0 < y) (hy_le : y ≤ 1)
    (_hz_pos : 0 < z) (hz_le : z ≤ 1) :
    x * y * z ≤ ε := by
  have h1 : x * y ≤ x := by
    calc x * y ≤ x * 1 := mul_le_mul_of_nonneg_left hy_le hx_pos.le
      _ = x := mul_one x
  have h2 : x * y * z ≤ x * y := by
    calc x * y * z ≤ (x * y) * 1 := mul_le_mul_of_nonneg_left hz_le (mul_nonneg hx_pos.le hy_pos.le)
      _ = x * y := mul_one (x * y)
  linarith [h1, h2, hx_le]

/-- SDEb → 0 ⟹ U-MaxP → 0 (ε-δ version, with GCI and A_emp bounded in (0,1]). -/
theorem umaxp_le_of_SDEb_small
    {SDEb GCI A_emp ε : ℝ}
    (hS_pos : 0 < SDEb) (hS_le : SDEb ≤ ε)
    (hG_pos : 0 < GCI) (hG_le : GCI ≤ 1)
    (hA_pos : 0 < A_emp) (hA_le : A_emp ≤ 1) :
    UMaxP SDEb GCI A_emp ≤ ε := by
  unfold UMaxP
  exact prod_le_of_first_small hS_pos hS_le hG_pos hG_le hA_pos hA_le

/-- GCI → 0 ⟹ U-MaxP → 0 (ε-δ version, with SDEb and A_emp bounded in (0,1]). -/
theorem umaxp_le_of_GCI_small
    {SDEb GCI A_emp ε : ℝ}
    (hS_pos : 0 < SDEb) (hS_le : SDEb ≤ 1)
    (hG_pos : 0 < GCI) (hG_le : GCI ≤ ε)
    (hA_pos : 0 < A_emp) (hA_le : A_emp ≤ 1) :
    UMaxP SDEb GCI A_emp ≤ ε := by
  unfold UMaxP
  have heq : SDEb * GCI * A_emp = GCI * SDEb * A_emp := by ring
  rw [heq]
  exact prod_le_of_first_small hG_pos hG_le hS_pos hS_le hA_pos hA_le

/-- A_emp → 0 ⟹ U-MaxP → 0 (ε-δ version, with SDEb and GCI bounded in (0,1]). -/
theorem umaxp_le_of_A_emp_small
    {SDEb GCI A_emp ε : ℝ}
    (hS_pos : 0 < SDEb) (hS_le : SDEb ≤ 1)
    (hG_pos : 0 < GCI) (hG_le : GCI ≤ 1)
    (hA_pos : 0 < A_emp) (hA_le : A_emp ≤ ε) :
    UMaxP SDEb GCI A_emp ≤ ε := by
  unfold UMaxP
  have heq : SDEb * GCI * A_emp = A_emp * SDEb * GCI := by ring
  rw [heq]
  exact prod_le_of_first_small hA_pos hA_le hS_pos hS_le hG_pos hG_le

-- ============================================================
-- PROPOSITIONS: DIMENSIONLESSNESS AND SCALE INVARIANCE
-- ============================================================

/--
SUPPLEMENTARY PROPOSITION 2.11: Dimensionlessness and scale invariance.
Mechanism: if homogeneous quantities scale by a non-zero factor c, their ratio is invariant.
-/
theorem ratio_scale_invariant
    {x y c : ℝ} (hc : c ≠ 0) :
    (c * x) / (c * y) = x / y :=
  mul_div_mul_left x y hc

/--
SUPPLEMENTARY PROPOSITION 2.1: Non-invariance of the absolute gap.
Formal counterexample: An absolute difference (unlike a ratio) does not cancel
the scale factor c, proving that traditional gap metrics (Δ) lack scale invariance.
-/
theorem absolute_gap_not_scale_invariant
    {Δ c : ℝ} (hc : c ≠ 1) (hΔ : Δ ≠ 0) :
    c * Δ ≠ Δ := by
  intro h
  have heq : (c - 1) * Δ = 0 := by nlinarith [h]
  rcases mul_eq_zero.mp heq with h1 | h1
  · exact hc (by linarith)
  · exact hΔ h1

/--
Because SDEb, GCI, and A_emp are inherently constructed as scale-invariant ratios,
U-MaxP trivially inherits full scale invariance as their product.
-/
theorem umaxp_scale_invariant
    {SDEb GCI A_emp SDEb' GCI' A_emp' : ℝ}
    (hS : SDEb' = SDEb) (hG : GCI' = GCI) (hA : A_emp' = A_emp) :
    UMaxP SDEb' GCI' A_emp' = UMaxP SDEb GCI A_emp := by
  rw [hS, hG, hA]

-- ============================================================
-- THEOREM: STRICT DOMINANCE & NO-COMPENSATION PROPERTY
-- ============================================================

/--
SUPPLEMENTARY THEOREM 2.1 / SUPPLEMENTARY OBSERVATION 2.8.
Non-Compensatory Tradeoff Theorem in Strict Mode.

NOTE: This is the exact same theorem proved in the Strict Mode section
(Theorem 2.1). It is included here in the formal properties suite because
it mathematically emerges as a direct corollary of Pareto Consistency
(Proposition 2.9) and Strict Monotonicity (Proposition 2.8).

If the structural core (SDEb * GCI) strictly improves, and empirical
authenticity (A_emp) does not degrade, U-MaxP strictly improves.
-/
theorem nc_tradeoff_implication
    {SDEb₁ SDEb₂ GCI₁ GCI₂ A_emp₁ A_emp₂ : ℝ}
    (h_pos_s2 : 0 < SDEb₂)
    (h_pos_g2 : 0 < GCI₂)
    (h_pos_a2 : 0 < A_emp₂)
    (h_strict : SDEb₂ * GCI₂ < SDEb₁ * GCI₁)
    (h_a : A_emp₂ ≤ A_emp₁) :
    UMaxP SDEb₂ GCI₂ A_emp₂ < UMaxP SDEb₁ GCI₁ A_emp₁ := by

  unfold UMaxP

  have h_pos_sg1 : 0 < SDEb₁ * GCI₁ := by
    calc
      0 < SDEb₂ * GCI₂ := mul_pos h_pos_s2 h_pos_g2
      _ < SDEb₁ * GCI₁ := h_strict

  have h_step1 : SDEb₂ * GCI₂ * A_emp₂ < (SDEb₁ * GCI₁) * A_emp₂ :=
    mul_lt_mul_of_pos_right h_strict h_pos_a2

  have h_step2 : (SDEb₁ * GCI₁) * A_emp₂ ≤ (SDEb₁ * GCI₁) * A_emp₁ :=
    mul_le_mul_of_nonneg_left h_a (le_of_lt h_pos_sg1)

  exact lt_of_lt_of_le h_step1 h_step2

-- End of noncomputable section
end
