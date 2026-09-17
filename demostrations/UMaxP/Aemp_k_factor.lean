-- SPDX-FileCopyrightText: 2026 José A. Pérez
-- SPDX-License-Identifier: MIT
--

-- ==============================================================================
-- FILE: DGDTL/Theory/Aemp_k_factor.lean
-- OBJECTIVE: Formalization of Component III: Empirical Authenticity Barrier
-- REFERENCE: Section 2.4, Supplementary Information (DGDTL-LTS)
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
-- COMPONENT III: EMPIRICAL AUTHENTICITY BARRIER
-- ============================================================

/-
This file formalizes the third component of the U-MaxP criterion.
It establishes the mathematical bounds, properties, and asymptotic behavior
of the semi-Gaussian penalty applied to extreme validation errors.
-/

-- ============================================================
-- 1. NOISE CHANNEL PARAMETERS
-- ============================================================

/-
SUPPLEMENTARY DEFINITION 2.4: Noise Channel Parameters.
The definitions of the statistical quantities (anchor, geometric mean,
effective thickness) rely on percentiles and CVaR. Since these operators
belong to the statistical protocol rather than pure topological theory,
they are modeled here as axioms and derived properties.
-/

/-- Equation (S40): Training anchor (P97.5 of training absolute errors). -/
axiom τ_anch : ℝ

/-- Equation (S41): Geometric-mean ceiling of the channel. -/
axiom e_gm : ℝ

/-- Numerical-stability constant ε. -/
axiom ε : ℝ
axiom ε_pos : 0 < ε

/-- Difference: τ_anch − P50(|ε_tr|), of arbitrary sign in general. -/
axiom p50_gap : ℝ

/--
Equation (S42): Universal minimum channel thickness.
δ_min = max(τ_anch - P50, ε).
Modeled structurally so that strict positivity is a formally DERIVED theorem,
not merely an assumed hypothesis.
-/
def δ_min : ℝ := max p50_gap ε

/--
δ_min > 0 is guaranteed by construction. This formalizes the manuscript's claim
that ε > 0 guarantees positivity even under hyper-concentrated distributions.
-/
theorem δ_min_pos : 0 < δ_min :=
  lt_of_lt_of_le ε_pos (le_max_right _ _)

/-- Equation (S43): Robust tail error (CVaR95). -/
axiom e_max_rob : ℝ

/--
Equation (S44): Effective channel thickness (δ_eff).
δ_eff = max(e_gm - τ_anch, δ_min)
-/
def δ_eff : ℝ :=
  max (e_gm - τ_anch) δ_min

/-- Strict positivity of the effective channel thickness (derived property). -/
theorem δ_eff_pos : 0 < δ_eff :=
  lt_of_lt_of_le δ_min_pos (le_max_right _ _)

/--
SUPPLEMENTARY PROPOSITION 2.5: Universal Channel Property.
The effective channel depends exclusively on the training protocol and
the baseline model, establishing an invariant geometric reference.
-/
theorem δ_eff_independent_of_candidate :
    δ_eff = max (e_gm - τ_anch) δ_min := by
  rfl

-- ============================================================
-- 2. NORMALIZED EMPIRICAL EXCESS
-- ============================================================

/--
Equation (S45): Normalized empirical excess (Φ_emp).
Quantifies the normalized over-ceiling deviation.
-/
def Φ_emp (e_max τ δ : ℝ) : ℝ :=
  max 0 ((e_max - τ) / δ)

-- ============================================================
-- 3. EMPIRICAL AUTHENTICITY BARRIER
-- ============================================================

/--
Equation (S46): Semi-Gaussian empirical authenticity barrier (A_emp).
Applies a quadratic exponential decay strictly outside the acceptable error channel.
-/
def A_emp (e_max τ δ : ℝ) : ℝ :=
  exp (-(Φ_emp e_max τ δ)^2)

-- ============================================================
-- PROPERTIES OF Φ_emp
-- ============================================================

/-- The normalized excess is inherently non-negative. -/
theorem Φ_emp_nonneg
    (e_max τ δ : ℝ) :
    0 ≤ Φ_emp e_max τ δ := by
  unfold Φ_emp
  exact le_max_left 0 ((e_max - τ) / δ)

/-- The excess vanishes entirely inside the operational channel. -/
theorem Φ_emp_eq_zero
    {e_max τ δ : ℝ}
    (hδ : 0 < δ)
    (h : e_max ≤ τ) :
    Φ_emp e_max τ δ = 0 := by

  unfold Φ_emp

  have hfrac : (e_max - τ) / δ ≤ 0 := by
    apply div_nonpos_of_nonpos_of_nonneg
    · linarith
    · exact le_of_lt hδ

  exact max_eq_left hfrac

-- ============================================================
-- PROPERTIES OF A_emp
-- ============================================================

/--
SUPPLEMENTARY PROPOSITION 2.6 (i):
The empirical authenticity barrier is strictly bounded in (0, 1].
Essential for maintaining the multiplicative coherence of U-MaxP.
-/
theorem A_emp_bounded
    (e_max τ δ : ℝ) :
    0 < A_emp e_max τ δ ∧ A_emp e_max τ δ ≤ 1 := by

  unfold A_emp

  have hphi : 0 ≤ Φ_emp e_max τ δ :=
    Φ_emp_nonneg e_max τ δ

  constructor

  · positivity

  · apply exp_le_one_iff.mpr

    have hsquare : 0 ≤ (Φ_emp e_max τ δ)^2 := by
      exact sq_nonneg _

    linarith


/--
Inside the empirical channel, the barrier reaches its unpenalized maximum (1).
-/
theorem A_emp_eq_one_inside_channel
    {e_max τ δ : ℝ}
    (hδ : 0 < δ)
    (h : e_max ≤ τ) :
    A_emp e_max τ δ = 1 := by

  unfold A_emp

  have hphi : Φ_emp e_max τ δ = 0 :=
    Φ_emp_eq_zero hδ h

  rw [hphi]
  norm_num


/-- Outside the channel, the empirical excess is strictly positive. -/
theorem Φ_emp_pos_outside_channel
    {e_max τ δ : ℝ}
    (hδ : 0 < δ)
    (h : τ < e_max) :
    0 < Φ_emp e_max τ δ := by

  unfold Φ_emp

  have hfrac : 0 < (e_max - τ) / δ := by
    apply div_pos
    · linarith
    · exact hδ

  rw [max_eq_right (le_of_lt hfrac)]
  exact hfrac


/--
Dichotomy: The empirical excess is either exactly zero (inside the channel)
or strictly positive (outside the channel).
-/
theorem Φ_emp_zero_or_positive
    {e_max τ δ : ℝ}
    (hδ : 0 < δ) :
    (e_max ≤ τ ∧ Φ_emp e_max τ δ = 0) ∨ (τ < e_max ∧ 0 < Φ_emp e_max τ δ) := by

  by_cases h : e_max ≤ τ
  · left
    constructor
    · exact h
    · exact Φ_emp_eq_zero hδ h
  · right
    have hgt : τ < e_max := lt_of_not_ge h
    constructor
    · exact hgt
    · exact Φ_emp_pos_outside_channel hδ hgt


/-- The barrier equals one whenever the empirical excess vanishes. -/
theorem A_emp_eq_one_of_Φ_zero
    {e_max τ δ : ℝ}
    (hphi : Φ_emp e_max τ δ = 0) :
    A_emp e_max τ δ = 1 := by
  unfold A_emp
  rw [hphi]
  norm_num


/-- The semi-Gaussian barrier is strictly decreasing with respect to the empirical excess. -/
theorem A_emp_strict_anti_mono
    {φ₁ φ₂ : ℝ}
    (hφ : 0 ≤ φ₁)
    (hlt : φ₁ < φ₂) :
    exp (-φ₂^2) < exp (-φ₁^2) := by

  apply Real.exp_lt_exp.mpr

  have hsquare : φ₁^2 < φ₂^2 := by
    nlinarith [sq_nonneg (φ₂ - φ₁)]

  nlinarith


/-- Algebraic identity used in Proposition 2.6 (iv) for asymptotic domination. -/
theorem gaussian_decay_faster
    (φ : ℝ) :
    exp (-φ^2) / exp (-φ) = exp (-φ * (φ - 1)) := by
  rw [← Real.exp_sub]
  congr 1
  ring


/-- Quadratic decay algebraically dominates linear exponential decay. -/
theorem gaussian_decay_identity
    (φ : ℝ) :
    exp (-φ^2) = exp (-φ) * exp (-φ * (φ - 1)) := by
  calc
    exp (-φ^2) = exp (-φ * (φ - 1)) * exp (-φ) := by
      rw [← Real.exp_add]
      congr
      ring
    _ = exp (-φ) * exp (-φ * (φ - 1)) := by
      ring


-- ============================================================
-- PROPOSITION COMPLETION (Biconditionals and Asymptotic Limits)
-- ============================================================

/--
SUPPLEMENTARY PROPOSITION 2.6 (ii):
A_emp = 1 IFF e_max ≤ τ (Biconditional equivalence).
Proves that the penalty is exclusively inactive within the acceptable channel.
-/
theorem A_emp_eq_one_iff
    {e_max τ δ : ℝ} (hδ : 0 < δ) :
    A_emp e_max τ δ = 1 ↔ e_max ≤ τ := by
  constructor
  · intro h
    unfold A_emp at h
    have hphi_nonneg : 0 ≤ Φ_emp e_max τ δ := Φ_emp_nonneg e_max τ δ
    have hexp_eq : exp (-(Φ_emp e_max τ δ)^2) = exp 0 := by
      rw [Real.exp_zero]; exact h
    have hexp_inj : ∀ x y : ℝ, exp x = exp y → x = y := by
      intro x y hxy
      by_contra hne
      rcases lt_or_gt_of_ne hne with hlt | hgt
      · exact absurd hxy (ne_of_lt (Real.exp_lt_exp.mpr hlt))
      · exact absurd hxy.symm (ne_of_lt (Real.exp_lt_exp.mpr hgt))
    have harg : -(Φ_emp e_max τ δ)^2 = 0 := hexp_inj _ _ hexp_eq
    have hphi_zero : Φ_emp e_max τ δ = 0 := by
      nlinarith [sq_nonneg (Φ_emp e_max τ δ), harg, hphi_nonneg]
    rcases Φ_emp_zero_or_positive hδ with ⟨hle, -⟩ | ⟨-, hpos⟩
    · exact hle
    · exfalso; rw [hphi_zero] at hpos; exact lt_irrefl 0 hpos
  · intro h
    exact A_emp_eq_one_inside_channel hδ h

/--
SUPPLEMENTARY PROPOSITION 2.6 (iii): Asymptotic collapse.
A_emp → 0 as e_max → ∞, with τ, δ fixed and δ > 0.
-/
theorem A_emp_tendsto_zero_atTop
    (τ δ : ℝ) (hδ : 0 < δ) :
    Tendsto (fun e_max => A_emp e_max τ δ) atTop (𝓝 0) := by
  have hsub : Tendsto (fun e_max : ℝ => e_max - τ) atTop atTop := by
    have h := tendsto_id.atTop_add (tendsto_const_nhds (x := (-τ : ℝ)))
    simpa [sub_eq_add_neg] using h
  have h1 : Tendsto (fun e_max : ℝ => (e_max - τ) / δ) atTop atTop :=
    hsub.atTop_div_const hδ
  have h2 : Tendsto (fun e_max : ℝ => ((e_max - τ) / δ)^2) atTop atTop :=
    (tendsto_pow_atTop (two_ne_zero)).comp h1
  have h3 : Tendsto (fun e_max : ℝ => -(((e_max - τ) / δ)^2)) atTop atBot :=
    tendsto_neg_atTop_atBot.comp h2
  have h4 : Tendsto (fun e_max : ℝ => Real.exp (-(((e_max - τ) / δ)^2))) atTop (𝓝 0) :=
    Real.tendsto_exp_atBot.comp h3
  have heq : ∀ᶠ e_max in atTop, A_emp e_max τ δ = Real.exp (-(((e_max - τ) / δ)^2)) := by
    filter_upwards [eventually_gt_atTop τ] with e_max he
    unfold A_emp Φ_emp
    have hpos : 0 < (e_max - τ) / δ := div_pos (by linarith) hδ
    rw [max_eq_right hpos.le]
  exact (tendsto_congr' heq).mpr h4

/--
SUPPLEMENTARY PROPOSITION 2.6 (iv): Quadratic dominance over linear exponential decay.
The ratio → 0 as φ → ∞. This establishes that the semi-Gaussian penalization
is structurally more severe than standard Gibbs/Laplace distributions for outliers.
-/
theorem gaussian_decay_dominates :
    Tendsto (fun φ : ℝ => exp (-φ^2) / exp (-φ)) atTop (𝓝 0) := by
  have heq : (fun φ : ℝ => exp (-φ^2) / exp (-φ)) = (fun φ : ℝ => exp (-(φ * (φ - 1)))) := by
    funext φ
    rw [gaussian_decay_faster]
    ring_nf
  rw [heq]
  have hquad : Tendsto (fun φ : ℝ => φ * (φ - 1)) atTop atTop := by
    rw [tendsto_atTop]
    intro b
    filter_upwards [eventually_ge_atTop (max (b + 1) 2)] with φ hφ
    have h1 : (2:ℝ) ≤ φ := le_trans (le_max_right _ _) hφ
    have h2 : b + 1 ≤ φ := le_trans (le_max_left _ _) hφ
    nlinarith [mul_nonneg (by linarith : (0:ℝ) ≤ φ - 2) (by linarith : (0:ℝ) ≤ φ)]
  have hneg : Tendsto (fun φ : ℝ => -(φ * (φ - 1))) atTop atBot :=
    tendsto_neg_atTop_atBot.comp hquad
  exact Real.tendsto_exp_atBot.comp hneg


-- ============================================================
-- 4. ABSOLUTE COMPLIANCE FACTOR (κ)
-- ============================================================

/--
SUPPLEMENTARY DEFINITION 2.6: Absolute compliance factor (κ).
Equation (S47): κ = τ_anch / max(τ_anch, e_max_rob)
Depends exclusively on the anchor τ and the robust tail error.
Independent of the geometry of the empirical channel.
-/
def κ (τ e : ℝ) : ℝ :=
  τ / max τ e

-- ============================================================
-- PROPERTIES OF κ
-- ============================================================

/--
SUPPLEMENTARY PROPOSITION 2.7 (i):
κ is strictly bounded in (0,1].
-/
theorem κ_bounded
    {τ e : ℝ}
    (hτ : 0 < τ) :
    0 < κ τ e ∧ κ τ e ≤ 1 := by

  unfold κ

  have hmax_pos : 0 < max τ e :=
    lt_of_lt_of_le hτ (le_max_left τ e)

  constructor
  · exact div_pos hτ hmax_pos
  · apply (div_le_one hmax_pos).mpr
    exact le_max_left τ e


/--
SUPPLEMENTARY PROPOSITION 2.7 (ii):
κ reaches its maximum value exactly inside the empirical channel.
-/
theorem κ_eq_one_iff
    {τ e : ℝ}
    (hτ : 0 < τ) :
    κ τ e = 1 ↔ e ≤ τ := by

  unfold κ

  have hmax_pos : 0 < max τ e :=
    lt_of_lt_of_le hτ (le_max_left τ e)

  constructor
  · intro h
    have hEq : τ = max τ e := by
      exact (div_eq_one_iff_eq (ne_of_gt hmax_pos)).mp h
    exact max_eq_left_iff.mp hEq.symm
  · intro h
    have hmax : max τ e = τ := max_eq_left h
    rw [hmax]
    exact div_self (ne_of_gt hτ)


/-- Outside the empirical channel, κ reduces directly to τ/e. -/
theorem κ_outside_channel
    {τ e : ℝ}
    (h : τ < e) :
    κ τ e = τ / e := by
  unfold κ
  have hmax : max τ e = e := max_eq_right (le_of_lt h)
  rw [hmax]


/-- Inside the empirical channel, κ evaluates to one. -/
theorem κ_inside_channel
    {τ e : ℝ}
    (hτ : 0 < τ)
    (h : e ≤ τ) :
    κ τ e = 1 := by
  exact (κ_eq_one_iff hτ).2 h


/-- Outside the channel, κ is strictly smaller than one. -/
theorem κ_lt_one_outside_channel
    {τ e : ℝ}
    (hτ : 0 < τ)
    (h : τ < e) :
    κ τ e < 1 := by

  rw [κ_outside_channel h]
  have he : 0 < e := lt_trans hτ h
  have hdiv : τ / e < 1 := by
    apply (div_lt_one he).mpr
    exact h
  simpa using hdiv


/--
SUPPLEMENTARY PROPOSITION 2.7 (iii):
Strict anti-monotonicity outside the empirical channel.
-/
theorem κ_strict_anti_mono
    {τ e₁ e₂ : ℝ}
    (hτ : 0 < τ)
    (h₁ : τ < e₁)
    (h₂ : e₁ < e₂) :
    κ τ e₂ < κ τ e₁ := by

  rw [κ_outside_channel h₁]
  rw [κ_outside_channel (lt_trans h₁ h₂)]

  have he₁ : 0 < e₁ := lt_trans hτ h₁
  have he₂ : 0 < e₂ := lt_trans he₁ h₂

  have hInv : 1 / e₂ < 1 / e₁ :=
    one_div_lt_one_div_of_lt he₁ h₂

  calc
    τ / e₂ = τ * (1 / e₂) := by ring
    _ < τ * (1 / e₁) := by
      exact mul_lt_mul_of_pos_left hInv hτ
    _ = τ / e₁ := by ring


/-- Universal upper bound for κ. -/
theorem κ_le_one
    {τ e : ℝ}
    (hτ : 0 < τ) :
    κ τ e ≤ 1 := by
  exact (κ_bounded hτ).2


/-- Universal lower bound for κ (strictly positive). -/
theorem κ_pos
    {τ e : ℝ}
    (hτ : 0 < τ) :
    0 < κ τ e := by
  exact (κ_bounded hτ).1


/--
SUPPLEMENTARY PROPOSITION 2.7 (iv):
κ functionally depends only on τ and the robust tail error.
-/
theorem κ_channel_independent
    {τ e : ℝ} :
    κ τ e = τ / max τ e := by
  rfl

/--
SUPPLEMENTARY PROPOSITION 2.7 (iii), second half:
Asymptotic property: κ → 0 as e → ∞, with τ fixed.
Demonstrates the structural collapse of compliance for arbitrarily large errors.
-/
theorem κ_tendsto_zero_atTop
    (τ : ℝ) (_hτ : 0 < τ) :
    Tendsto (fun e => κ τ e) atTop (𝓝 0) := by
  have heq : ∀ᶠ e in atTop, κ τ e = τ / e := by
    filter_upwards [eventually_gt_atTop τ] with e he
    exact κ_outside_channel he
  have h1 : Tendsto (fun e : ℝ => τ / e) atTop (𝓝 0) :=
    (tendsto_const_nhds (x := τ)).div_atTop tendsto_id
  exact (tendsto_congr' heq).mpr h1

-- End of noncomputable section
end
