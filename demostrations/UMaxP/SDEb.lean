-- SPDX-FileCopyrightText: 2026 José A. Pérez
-- SPDX-License-Identifier: MIT
--

-- ==============================================================================
-- FILE: DGDTL/Theory/SDEb.lean
-- OBJECTIVE: Formalization of the Bounded Stability-Diversity-Efficiency Index (SDEb)
-- REFERENCE: Section 2.2, Supplementary Information (DGDTL-LTS)
-- ==============================================================================

import Mathlib.Analysis.SpecialFunctions.Exp
import Mathlib.Data.Real.Basic
import Mathlib.Tactic
import Mathlib.Order.Filter.AtTopBot.Basic
import Mathlib.Topology.Basic
import Mathlib.Topology.Algebra.Order.Field

open Real
open Filter Topology

-- Disable the unused variables warning to strictly preserve the exact theorem signatures
set_option linter.unusedVariables false

noncomputable section

-- ============================================================
-- COMPONENT I: The Bounded Stability-Diversity-Efficiency Index
-- ============================================================

/--
Equation (S24): The Bounded Stability-Diversity-Efficiency Index.
𝓚_DEb(𝓕) = S * Ω * exp(-E / (D * √α))

This function formalizes the topological stability of a multivariate regression
model in parameter space, penalizing sharp minima and favoring broad,
flat basins of the loss landscape.
-/
def SDEb (S Ω E D α : ℝ) : ℝ :=
  S * Ω * exp (-E / (D * Real.sqrt α))

/--
SUPPLEMENTARY PROPOSITION 2.2: Boundedness of 𝓚_DEb.
Demonstrates that the index is strictly bounded in the interval (0, 1].
This property is critical for its use as a probabilistic or
information-theoretic surrogate in the U-MaxP criterion.
-/
theorem SDEb_bounded
    (hS : 0 < S ∧ S ≤ 1)
    (hΩ : 0 < Ω ∧ Ω ≤ 1)
    (hE : 0 ≤ E)
    (hD : 0 < D)
    (hα : 0 < α) :
    0 < SDEb S Ω E D α ∧ SDEb S Ω E D α ≤ 1 := by

  rcases hS with ⟨hSpos, hSle⟩
  rcases hΩ with ⟨hΩpos, hΩle⟩

  have hsqrt : 0 < Real.sqrt α := Real.sqrt_pos.mpr hα
  have hden : 0 < D * Real.sqrt α := mul_pos hD hsqrt

  have hexp_pos : 0 < exp (-E / (D * Real.sqrt α)) := exp_pos _

  have hexp_le : exp (-E / (D * Real.sqrt α)) ≤ 1 := by
    apply exp_le_one_iff.mpr
    apply div_nonpos_of_nonpos_of_nonneg
    · exact neg_nonpos.mpr hE
    · exact le_of_lt hden

  constructor
  · -- Left bound: 0 < SDEb
    unfold SDEb
    positivity

  · -- Right bound: SDEb ≤ 1
    unfold SDEb
    have h_S_Omega : S * Ω ≤ 1 * 1 :=
      mul_le_mul hSle hΩle (le_of_lt hΩpos) zero_le_one
    rw [mul_one] at h_S_Omega

    have h_final : S * Ω * exp (-E / (D * Real.sqrt α)) ≤ 1 * 1 :=
      mul_le_mul h_S_Omega hexp_le (le_of_lt hexp_pos) zero_le_one
    rw [mul_one] at h_final

    exact h_final


-- ============================================================
-- COMPONENT I-B: Monotonicity of the SDEb Index
-- ============================================================

/-- Monotonicity regarding Energy (E): strictly decreasing. -/
theorem SDEb_strict_anti_mono_E
    {S Ω D α : ℝ}
    (hS : 0 < S) (hΩ : 0 < Ω) (hD : 0 < D) (hα : 0 < α)
    {E₁ E₂ : ℝ} (hE : E₁ < E₂) :
    SDEb S Ω E₂ D α < SDEb S Ω E₁ D α := by

  unfold SDEb

  have h_sqrt : 0 < Real.sqrt α := Real.sqrt_pos.mpr hα
  have h_den : 0 < D * Real.sqrt α := mul_pos hD h_sqrt

  have h_frac : -E₂ / (D * Real.sqrt α) < -E₁ / (D * Real.sqrt α) := by
    have h_neg : -E₂ < -E₁ := neg_lt_neg hE
    exact div_lt_div_of_pos_right h_neg h_den

  have h_exp : exp (-E₂ / (D * Real.sqrt α)) < exp (-E₁ / (D * Real.sqrt α)) := by
    exact Real.exp_lt_exp.mpr h_frac

  have h_S_Omega : 0 < S * Ω := mul_pos hS hΩ

  calc
    S * Ω * exp (-E₂ / (D * Real.sqrt α))
      = (S * Ω) * exp (-E₂ / (D * Real.sqrt α)) := by ring
    _ < (S * Ω) * exp (-E₁ / (D * Real.sqrt α)) := mul_lt_mul_of_pos_left h_exp h_S_Omega
    _ = S * Ω * exp (-E₁ / (D * Real.sqrt α)) := by ring


/-- Monotonicity regarding Spectral Stability (S): strictly increasing. -/
theorem SDEb_strict_mono_S
    {Ω E D α : ℝ}
    (hΩ : 0 < Ω)
    {S₁ S₂ : ℝ} (hS : S₁ < S₂) :
    SDEb S₁ Ω E D α < SDEb S₂ Ω E D α := by

  unfold SDEb

  have h_exp : 0 < exp (-E / (D * Real.sqrt α)) := exp_pos _
  have h_Omega_exp : 0 < Ω * exp (-E / (D * Real.sqrt α)) := mul_pos hΩ h_exp

  calc
    S₁ * Ω * exp (-E / (D * Real.sqrt α))
      = S₁ * (Ω * exp (-E / (D * Real.sqrt α))) := by ring
    _ < S₂ * (Ω * exp (-E / (D * Real.sqrt α))) := mul_lt_mul_of_pos_right hS h_Omega_exp
    _ = S₂ * Ω * exp (-E / (D * Real.sqrt α)) := by ring


/-- Monotonicity regarding Support Regularization (Ω): strictly increasing. -/
theorem SDEb_strict_mono_Omega
    {S E D α : ℝ}
    (hS : 0 < S)
    {Ω₁ Ω₂ : ℝ} (hΩ : Ω₁ < Ω₂) :
    SDEb S Ω₁ E D α < SDEb S Ω₂ E D α := by

  unfold SDEb

  have h_exp : 0 < exp (-E / (D * Real.sqrt α)) := exp_pos _
  have h_S_exp : 0 < S * exp (-E / (D * Real.sqrt α)) := mul_pos hS h_exp

  calc
    S * Ω₁ * exp (-E / (D * Real.sqrt α))
      = Ω₁ * (S * exp (-E / (D * Real.sqrt α))) := by ring
    _ < Ω₂ * (S * exp (-E / (D * Real.sqrt α))) := mul_lt_mul_of_pos_right hΩ h_S_exp
    _ = S * Ω₂ * exp (-E / (D * Real.sqrt α)) := by ring


-- ============================================================
-- COMPONENT I-C: Additional Analytical Results
-- ============================================================

private lemma mul_eq_one_iff_of_le_one {x y : ℝ}
    (hx0 : 0 < x) (hx1 : x ≤ 1) (hy0 : 0 < y) (hy1 : y ≤ 1) :
    x * y = 1 ↔ x = 1 ∧ y = 1 := by
  constructor
  · intro h
    have hxy_le : x * y ≤ y := by
      calc x * y ≤ 1 * y := mul_le_mul_of_nonneg_right hx1 (le_of_lt hy0)
        _ = y := one_mul y
    have hy_eq : y = 1 := le_antisymm hy1 (h ▸ hxy_le)
    have hx_eq : x = 1 := by
      rw [hy_eq, mul_one] at h
      exact h
    exact ⟨hx_eq, hy_eq⟩
  · rintro ⟨hx, hy⟩
    rw [hx, hy, mul_one]

private lemma exp_inj {x y : ℝ} (hxy : exp x = exp y) : x = y := by
  by_contra hne
  rcases lt_or_gt_of_ne hne with h | h
  · exact absurd hxy (ne_of_lt (Real.exp_lt_exp.mpr h))
  · exact absurd hxy.symm (ne_of_lt (Real.exp_lt_exp.mpr h))

/-- Characterization of the maximum. 𝓚_DEb reaches its upper bound 1
    if and only if S = Ω = 1 and E = 0. -/
theorem SDEb_eq_one_iff
    (hS : 0 < S ∧ S ≤ 1) (hΩ : 0 < Ω ∧ Ω ≤ 1)
    (hE : 0 ≤ E) (hD : 0 < D) (hα : 0 < α) :
    SDEb S Ω E D α = 1 ↔ (S = 1 ∧ Ω = 1 ∧ E = 0) := by
  rcases hS with ⟨hSpos, hSle⟩
  rcases hΩ with ⟨hΩpos, hΩle⟩
  have hsqrt : 0 < Real.sqrt α := Real.sqrt_pos.mpr hα
  have hden : 0 < D * Real.sqrt α := mul_pos hD hsqrt
  have hexp_pos : 0 < exp (-E / (D * Real.sqrt α)) := exp_pos _
  have hexp_le : exp (-E / (D * Real.sqrt α)) ≤ 1 := by
    apply exp_le_one_iff.mpr
    apply div_nonpos_of_nonpos_of_nonneg
    · exact neg_nonpos.mpr hE
    · exact le_of_lt hden
  have hSΩ_pos : 0 < S * Ω := mul_pos hSpos hΩpos
  have hSΩ_le : S * Ω ≤ 1 := by
    calc S * Ω ≤ 1 * 1 := mul_le_mul hSle hΩle (le_of_lt hΩpos) zero_le_one
      _ = 1 := mul_one 1
  constructor
  · intro h
    unfold SDEb at h
    obtain ⟨hSΩ_eq, hexp_eq⟩ :=
      (mul_eq_one_iff_of_le_one hSΩ_pos hSΩ_le hexp_pos hexp_le).mp h
    obtain ⟨hS_eq, hΩ_eq⟩ :=
      (mul_eq_one_iff_of_le_one hSpos hSle hΩpos hΩle).mp hSΩ_eq
    refine ⟨hS_eq, hΩ_eq, ?_⟩
    have hexp_eq' : exp (-E / (D * Real.sqrt α)) = exp 0 := by
      rw [Real.exp_zero]; exact hexp_eq
    have hexp_arg : -E / (D * Real.sqrt α) = 0 := exp_inj hexp_eq'
    have hnum : -E = 0 := by
      rcases div_eq_zero_iff.mp hexp_arg with h1 | h2
      · exact h1
      · exact absurd h2 (ne_of_gt hden)
    linarith
  · rintro ⟨hS_eq, hΩ_eq, hE_eq⟩
    unfold SDEb
    rw [hS_eq, hΩ_eq, hE_eq]
    simp

/-- Monotonicity regarding Topological Diversity (D): strictly increasing.
    Requires E > 0 since D acts as a geometric scaler of the residual energy. -/
theorem SDEb_strict_mono_D
    {S Ω E α : ℝ}
    (hS : 0 < S) (hΩ : 0 < Ω) (hE : 0 < E) (hα : 0 < α)
    {D₁ D₂ : ℝ} (hD₁ : 0 < D₁) (hD : D₁ < D₂) :
    SDEb S Ω E D₁ α < SDEb S Ω E D₂ α := by
  unfold SDEb
  have hD₂ : 0 < D₂ := lt_trans hD₁ hD
  have hsqrt : 0 < Real.sqrt α := Real.sqrt_pos.mpr hα
  have hden₁ : 0 < D₁ * Real.sqrt α := mul_pos hD₁ hsqrt
  have hden₂ : 0 < D₂ * Real.sqrt α := mul_pos hD₂ hsqrt
  have hden_lt : D₁ * Real.sqrt α < D₂ * Real.sqrt α :=
    mul_lt_mul_of_pos_right hD hsqrt
  have hfrac_pos : E / (D₂ * Real.sqrt α) < E / (D₁ * Real.sqrt α) := by
    rw [div_lt_div_iff₀ hden₂ hden₁]
    exact mul_lt_mul_of_pos_left hden_lt hE
  have h_frac : -E / (D₁ * Real.sqrt α) < -E / (D₂ * Real.sqrt α) := by
    rw [neg_div, neg_div]
    exact neg_lt_neg hfrac_pos
  have h_exp : exp (-E / (D₁ * Real.sqrt α)) < exp (-E / (D₂ * Real.sqrt α)) :=
    Real.exp_lt_exp.mpr h_frac
  have h_S_Omega : 0 < S * Ω := mul_pos hS hΩ
  calc
    S * Ω * exp (-E / (D₁ * Real.sqrt α))
        = (S * Ω) * exp (-E / (D₁ * Real.sqrt α)) := by ring
      _ < (S * Ω) * exp (-E / (D₂ * Real.sqrt α)) := mul_lt_mul_of_pos_left h_exp h_S_Omega
      _ = S * Ω * exp (-E / (D₂ * Real.sqrt α)) := by ring

/-- Monotonicity regarding Ambition Factor (α): strictly increasing.
    Requires E > 0. -/
theorem SDEb_strict_mono_alpha
    {S Ω E D : ℝ}
    (hS : 0 < S) (hΩ : 0 < Ω) (hE : 0 < E) (hD : 0 < D)
    {α₁ α₂ : ℝ} (hα₁ : 0 < α₁) (hα : α₁ < α₂) :
    SDEb S Ω E D α₁ < SDEb S Ω E D α₂ := by
  unfold SDEb
  have hα₂ : 0 < α₂ := lt_trans hα₁ hα
  have hsqrt_lt : Real.sqrt α₁ < Real.sqrt α₂ :=
    Real.sqrt_lt_sqrt (le_of_lt hα₁) hα
  have hsqrt₁ : 0 < Real.sqrt α₁ := Real.sqrt_pos.mpr hα₁
  have hsqrt₂ : 0 < Real.sqrt α₂ := Real.sqrt_pos.mpr hα₂
  have hden₁ : 0 < D * Real.sqrt α₁ := mul_pos hD hsqrt₁
  have hden₂ : 0 < D * Real.sqrt α₂ := mul_pos hD hsqrt₂
  have hden_lt : D * Real.sqrt α₁ < D * Real.sqrt α₂ :=
    mul_lt_mul_of_pos_left hsqrt_lt hD
  have hfrac_pos : E / (D * Real.sqrt α₂) < E / (D * Real.sqrt α₁) := by
    rw [div_lt_div_iff₀ hden₂ hden₁]
    exact mul_lt_mul_of_pos_left hden_lt hE
  have h_frac : -E / (D * Real.sqrt α₁) < -E / (D * Real.sqrt α₂) := by
    rw [neg_div, neg_div]
    exact neg_lt_neg hfrac_pos
  have h_exp : exp (-E / (D * Real.sqrt α₁)) < exp (-E / (D * Real.sqrt α₂)) :=
    Real.exp_lt_exp.mpr h_frac
  have h_S_Omega : 0 < S * Ω := mul_pos hS hΩ
  calc
    S * Ω * exp (-E / (D * Real.sqrt α₁))
        = (S * Ω) * exp (-E / (D * Real.sqrt α₁)) := by ring
      _ < (S * Ω) * exp (-E / (D * Real.sqrt α₂)) := mul_lt_mul_of_pos_left h_exp h_S_Omega
      _ = S * Ω * exp (-E / (D * Real.sqrt α₂)) := by ring

/--
Equation (S34): Baseline consistency recovery.
The theoretical formulation seamlessly recovers the index evaluation for
the MinMSE baseline.
-/
theorem SDEb_baseline_recovery (Ω D : ℝ) :
    SDEb 1 Ω 1 D 1 = Ω * exp (-1 / D) := by
  unfold SDEb
  simp [Real.sqrt_one]

/--
SUPPLEMENTARY OBSERVATION 2.1 (Item 1): Topological degeneracy regime N_elite = 0.
The index inherently collapses to 0 when the spectral stability S is 0.
-/
theorem SDEb_zero_of_S_zero (Ω E D α : ℝ) : SDEb 0 Ω E D α = 0 := by
  unfold SDEb; ring

/--
SUPPLEMENTARY OBSERVATION 2.1 (Item 3): Topological degeneracy regime N_elite = 2.
The index inherently collapses to 0 when the support regularization Ω is 0.
-/
theorem SDEb_zero_of_Omega_zero (S E D α : ℝ) : SDEb S 0 E D α = 0 := by
  unfold SDEb; ring


-- ============================================================
-- COMPONENT I-D: Limiting Behavior
-- ============================================================

/-- Infinite energy limit: SDEb → 0 as E → ∞. -/
theorem SDEb_tendsto_zero_atTop_E
    {S Ω D α : ℝ} (hS : 0 < S) (hΩ : 0 < Ω) (hD : 0 < D) (hα : 0 < α) :
    Tendsto (fun E => SDEb S Ω E D α) atTop (𝓝 0) := by
  have hsqrt : 0 < Real.sqrt α := Real.sqrt_pos.mpr hα
  have hden : 0 < D * Real.sqrt α := mul_pos hD hsqrt
  have h1 : Tendsto (fun E : ℝ => E / (D * Real.sqrt α)) atTop atTop :=
    tendsto_id.atTop_div_const hden
  have h2 : Tendsto (fun E : ℝ => -(E / (D * Real.sqrt α))) atTop atBot :=
    tendsto_neg_atTop_atBot.comp h1
  have h3 : Tendsto (fun E : ℝ => Real.exp (-(E / (D * Real.sqrt α)))) atTop (𝓝 0) :=
    Real.tendsto_exp_atBot.comp h2
  have h4 : Tendsto (fun E : ℝ => S * Ω * Real.exp (-(E / (D * Real.sqrt α))))
      atTop (𝓝 (S * Ω * 0)) := h3.const_mul (S * Ω)
  simp only [mul_zero] at h4
  simpa [SDEb, neg_div] using h4

/--
SUPPLEMENTARY PROPOSITION 2.3: Lateral limit in the topological collapse regime.
(Consistent with Supplementary Observation 2.1, Item 2: N_elite = 1)
SDEb → 0 as D → 0⁺, assuming E > 0.

This formally guarantees that in the absence of certifiable topological
diversity (D -> 0), the metric correctly collapses, preventing artificial
credit for sharp/degenerate optimization artifacts.
-/
theorem SDEb_tendsto_zero_right_D
    {S Ω E α : ℝ} (hS : 0 < S) (hΩ : 0 < Ω) (hE : 0 < E) (hα : 0 < α) :
    Tendsto (fun D => SDEb S Ω E D α) (𝓝[>] (0:ℝ)) (𝓝 0) := by
  have hsqrt : 0 < Real.sqrt α := Real.sqrt_pos.mpr hα
  have h_c : 0 < E / Real.sqrt α := div_pos hE hsqrt

  -- Standard limit for the multiplicative inverse as x → 0⁺
  have h1 : Tendsto (fun D : ℝ => D⁻¹) (𝓝[>] 0) atTop := tendsto_inv_nhdsGT_zero

  have h2 : Tendsto (fun D : ℝ => (E / Real.sqrt α) * D⁻¹) (𝓝[>] 0) atTop :=
    Tendsto.const_mul_atTop h_c h1

  -- Pure algebraic resolution based on field properties
  have h_eq : (fun D : ℝ => (E / Real.sqrt α) * D⁻¹) = (fun D : ℝ => E / (D * Real.sqrt α)) := by
    ext D
    calc (E / Real.sqrt α) * D⁻¹
      _ = (E / Real.sqrt α) / D := rfl
      _ = E / (Real.sqrt α * D) := by rw [div_div]
      _ = E / (D * Real.sqrt α) := by rw [mul_comm (Real.sqrt α) D]

  have h3 : Tendsto (fun D : ℝ => E / (D * Real.sqrt α)) (𝓝[>] 0) atTop := by
    rw [← h_eq]
    exact h2

  have h4 : Tendsto (fun D : ℝ => -(E / (D * Real.sqrt α))) (𝓝[>] 0) atBot :=
    tendsto_neg_atTop_atBot.comp h3

  have h5 : Tendsto (fun D : ℝ => Real.exp (-(E / (D * Real.sqrt α)))) (𝓝[>] 0) (𝓝 0) :=
    Real.tendsto_exp_atBot.comp h4

  have h6 : Tendsto (fun D : ℝ => S * Ω * Real.exp (-(E / (D * Real.sqrt α)))) (𝓝[>] 0) (𝓝 (S * Ω * 0)) :=
    Tendsto.const_mul (S * Ω) h5

  simp only [mul_zero] at h6
  simpa [SDEb, neg_div] using h6

-- End of noncomputable section
end
