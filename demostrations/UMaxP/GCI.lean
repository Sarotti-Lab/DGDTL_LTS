-- SPDX-FileCopyrightText: 2026 José A. Pérez
-- SPDX-License-Identifier: MIT
--

-- ==============================================================================
-- FILE: DGDTL/Theory/GCI.lean
-- OBJECTIVE: Formalization of the Generalization Consistency Index (GCI)
-- REFERENCE: Section 2.3, Supplementary Information (DGDTL-LTS)
-- ==============================================================================

import Mathlib.Data.Real.Basic
import Mathlib.Tactic
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Arctan

open Real

-- Disable the unused variables warning to strictly preserve the exact theorem signatures
set_option linter.unusedVariables false

noncomputable section

-- ============================================================
-- COMPONENT II: The Generalization Consistency Index (GCI)
-- ============================================================

-- ------------------------------------------------------------
-- 1. Cauchy Balance Factor (φ)
-- ------------------------------------------------------------

/--
Equation (S38): Cauchy balance factor.
φ(ρ) = 2ρ / (1 + ρ²)

Measures the structural ratio between the candidate's training and validation
errors, relativized to the baseline.
-/
def φ (ρ : ℝ) : ℝ :=
  (2 * ρ) / (1 + ρ^2)

/--
SUPPLEMENTARY PROPOSITION 2.4 (iv):
φ is strictly decreasing for ρ > 1 (overfitting regime) and strictly
increasing for ρ < 1 (underfitting regime).
Here we formalize the negative derivative condition for ρ > 1.
-/
theorem φ_derivative_negative
    {ρ : ℝ}
    (hρ : ρ > 1) :
    ((2 * (1 - ρ^2)) / (1 + ρ^2)^2) < 0 := by
  have hnum : 2 * (1 - ρ^2) < 0 := by nlinarith
  have hden : (1 + ρ^2)^2 > 0 := by positivity
  exact div_neg_of_neg_of_pos hnum hden

/--
Equivalent Representation: φ(ρ) = sin(2 arctan(ρ)).
Demonstrates that the functional form belongs to the rational Cauchy family,
accounting for its exact symmetry about ρ = 1.
-/
theorem φ_trig
    (ρ : ℝ) :
    φ ρ = Real.sin (2 * Real.arctan ρ) := by

  unfold φ
  rw [Real.sin_two_mul]
  rw [Real.cos_arctan, Real.sin_arctan]

  have h_pos : 0 ≤ 1 + ρ^2 := by positivity
  have h_pos_strict : 0 < 1 + ρ^2 := by positivity

  have h_sqrt :
      Real.sqrt (1 + ρ^2) *
      Real.sqrt (1 + ρ^2)
      = 1 + ρ^2 := by
    exact Real.mul_self_sqrt h_pos

  generalize hx : Real.sqrt (1 + ρ^2) = x

  rw [hx] at h_sqrt
  rw [← h_sqrt]

  have hx_pos : 0 < x := by
    rw [← hx]
    exact Real.sqrt_pos.mpr h_pos_strict
  have hx_ne_zero : x ≠ 0 := ne_of_gt hx_pos

  field_simp [hx_ne_zero]

-- ------------------------------------------------------------
-- 2. Efficiency Factor (f_eff)
-- ------------------------------------------------------------

/--
Equation (S36): Efficiency factor.
f_eff = 1 / (1 + e_val / (e_base + ε))

Measures the relative performance of the candidate against the baseline.
-/
def f_eff (e_val e_base ε : ℝ) : ℝ :=
  1 / (1 + e_val / (e_base + ε))

-- ------------------------------------------------------------
-- 3. Continuity Factor (h_cont)
-- ------------------------------------------------------------

/--
Equation (S39): Continuity factor.
h_cont = 1 / (1 + e_max / (e_gm + ε))

Encodes whether the model's maximum error respects the statistical ceiling.
-/
def h_cont (e_max e_gm ε : ℝ) : ℝ :=
  1 / (1 + e_max / (e_gm + ε))

-- ------------------------------------------------------------
-- 4. Global Index (GCI)
-- ------------------------------------------------------------

/--
Equation (S35): The Generalization Consistency Index.
GCI = f_eff * φ * h_cont
-/
def GCI (e_val e_base e_max e_gm ρ ε : ℝ) : ℝ :=
  f_eff e_val e_base ε * φ ρ * h_cont e_max e_gm ε

-- ============================================================
-- COMPONENT II-B: Boundedness of the GCI Index
-- ============================================================

/-- Lemma: The efficiency factor is strictly bounded in (0, 1]. -/
theorem f_eff_bounded
    {e_val e_base ε : ℝ}
    (h_val : 0 ≤ e_val) (h_base : 0 ≤ e_base) (h_ε : 0 < ε) :
    0 < f_eff e_val e_base ε ∧ f_eff e_val e_base ε ≤ 1 := by

  unfold f_eff

  have h_den_pos : 0 < e_base + ε := by linarith
  have h_frac_nonneg : 0 ≤ e_val / (e_base + ε) := div_nonneg h_val (le_of_lt h_den_pos)
  have h_one_le : 1 ≤ 1 + e_val / (e_base + ε) := by linarith
  have h_pos : 0 < 1 + e_val / (e_base + ε) := by linarith

  constructor
  · exact one_div_pos.mpr h_pos
  · exact (div_le_one h_pos).mpr h_one_le


/-- Lemma: The continuity factor is strictly bounded in (0, 1]. -/
theorem h_cont_bounded
    {e_max e_gm ε : ℝ}
    (h_max : 0 ≤ e_max) (h_gm : 0 ≤ e_gm) (h_ε : 0 < ε) :
    0 < h_cont e_max e_gm ε ∧ h_cont e_max e_gm ε ≤ 1 := by

  unfold h_cont

  have h_den_pos : 0 < e_gm + ε := by linarith
  have h_frac_nonneg : 0 ≤ e_max / (e_gm + ε) := div_nonneg h_max (le_of_lt h_den_pos)
  have h_one_le : 1 ≤ 1 + e_max / (e_gm + ε) := by linarith
  have h_pos : 0 < 1 + e_max / (e_gm + ε) := by linarith

  constructor
  · exact one_div_pos.mpr h_pos
  · exact (div_le_one h_pos).mpr h_one_le


/--
SUPPLEMENTARY PROPOSITION 2.4 (i):
The Cauchy balance factor φ is strictly bounded in (0, 1] for all ρ > 0.
-/
theorem φ_bounded
    {ρ : ℝ}
    (hρ : 0 < ρ) :
    0 < φ ρ ∧ φ ρ ≤ 1 := by

  unfold φ

  have h_num : 0 < 2 * ρ := mul_pos zero_lt_two hρ
  have h_den : 0 < 1 + ρ^2 := by positivity

  constructor
  · -- Left bound: 0 < φ
    exact div_pos h_num h_den
  · -- Right bound: φ ≤ 1
    -- Explicitly declare that the square (1 - ρ)² is non-negative
    have h_sq : 0 ≤ (1 - ρ)^2 := sq_nonneg (1 - ρ)

    -- Pass this hint to nlinarith to establish 2ρ ≤ 1 + ρ²
    have h_ineq : 2 * ρ ≤ 1 + ρ^2 := by nlinarith [h_sq]

    exact (div_le_one h_den).mpr h_ineq


/--
MAIN THEOREM:
The Generalization Consistency Index (GCI) is strictly bounded in (0, 1].
This guarantees its mathematical coherence as a multiplicative factor
within the U-MaxP criterion.
-/
theorem GCI_bounded
    {e_val e_base e_max e_gm ρ ε : ℝ}
    (h_val : 0 ≤ e_val) (h_base : 0 ≤ e_base)
    (h_max : 0 ≤ e_max) (h_gm : 0 ≤ e_gm)
    (hρ : 0 < ρ) (h_ε : 0 < ε) :
    0 < GCI e_val e_base e_max e_gm ρ ε ∧
    GCI e_val e_base e_max e_gm ρ ε ≤ 1 := by

  unfold GCI

  have ⟨hf_pos, hf_le⟩ := f_eff_bounded h_val h_base h_ε
  have ⟨hφ_pos, hφ_le⟩ := φ_bounded hρ
  have ⟨hh_pos, hh_le⟩ := h_cont_bounded h_max h_gm h_ε

  constructor
  · positivity

  · have step1 : f_eff e_val e_base ε * φ ρ ≤ 1 * 1 :=
      mul_le_mul hf_le hφ_le (le_of_lt hφ_pos) zero_le_one
    rw [mul_one] at step1

    have step2 : (f_eff e_val e_base ε * φ ρ) * h_cont e_max e_gm ε ≤ 1 * 1 :=
      mul_le_mul step1 hh_le (le_of_lt hh_pos) zero_le_one
    rw [mul_one] at step2

    have h_eq : f_eff e_val e_base ε * φ ρ * h_cont e_max e_gm ε =
                (f_eff e_val e_base ε * φ ρ) * h_cont e_max e_gm ε := by ring
    rw [h_eq]

    exact step2

-- ============================================================
-- COMPONENT II-C: Structural Properties of the Cauchy Factor
-- ============================================================

/--
SUPPLEMENTARY PROPOSITION 2.4 (ii): Maximum characterization.
φ reaches the value 1 if and only if ρ = 1.
This implies the index reaches its maximum when the candidate's
training-to-validation ratio exactly matches that of the baseline.
-/
theorem φ_eq_one_iff
    {ρ : ℝ}
    (hρ : 0 < ρ) :
    φ ρ = 1 ↔ ρ = 1 := by

  unfold φ

  have hden : 0 < 1 + ρ^2 := by
    positivity

  constructor

  · intro h

    have hcross :
        2 * ρ = 1 + ρ^2 := by
      have := congrArg (fun x => x * (1 + ρ^2)) h
      field_simp [hden.ne'] at this
      simpa using this

    have hsq :
        (ρ - 1)^2 = 0 := by
      nlinarith [hcross]

    nlinarith

  · intro h
    subst h
    norm_num

/--
SUPPLEMENTARY PROPOSITION 2.4 (iii): Exact symmetry.
φ(ρ) = φ(1/ρ)

This is epistemologically significant: the index symmetrically penalizes
both overfitting (ρ > 1) and underfitting (ρ < 1), treating both deviations
as equivalent ruptures of the train/validation equilibrium regime.
-/
theorem φ_symmetry
    {ρ : ℝ}
    (hρ : 0 < ρ) :
    φ (1 / ρ) = φ ρ := by

  unfold φ

  have hne : ρ ≠ 0 := by
    linarith

  field_simp [hne]

  ring

/-- Baseline optimal identity test -/
theorem φ_one :
    φ 1 = 1 := by
  unfold φ
  norm_num

/--
Algebraic helper identity: difference of φ at two points.
Both branches of SUPPLEMENTARY PROPOSITION 2.4 (iv) follow directly from
the sign of this expression, with no need for calculus / MVT machinery.
-/
private lemma φ_sub (a b : ℝ) :
    φ b - φ a = 2 * (b - a) * (1 - a * b) / ((1 + a^2) * (1 + b^2)) := by
  unfold φ
  have ha : (0:ℝ) < 1 + a^2 := by positivity
  have hb : (0:ℝ) < 1 + b^2 := by positivity
  field_simp
  ring

/--
SUPPLEMENTARY PROPOSITION 2.4 (iv), left branch:
φ is strictly increasing on (0,1] (underfitting regime).
-/
theorem φ_strict_mono_left
    {a b : ℝ} (ha : 0 < a) (hb : b ≤ 1) (hab : a < b) :
    φ a < φ b := by
  have hd : φ b - φ a = 2 * (b - a) * (1 - a * b) / ((1 + a^2) * (1 + b^2)) :=
    φ_sub a b
  have h1 : 0 < b - a := by linarith
  have hab1 : a < 1 := lt_of_lt_of_le hab hb
  have hprod : a * b ≤ a := by
    calc a * b ≤ a * 1 := mul_le_mul_of_nonneg_left hb ha.le
      _ = a := mul_one a
  have h2 : 0 < 1 - a * b := by linarith
  have h3 : 0 < (1 + a^2) * (1 + b^2) := by positivity
  have hpos : 0 < φ b - φ a := by
    rw [hd]
    exact div_pos (mul_pos (mul_pos two_pos h1) h2) h3
  linarith

/--
SUPPLEMENTARY PROPOSITION 2.4 (iv), right branch:
φ is strictly decreasing on [1,∞) (overfitting regime).
-/
theorem φ_strict_anti_mono_right
    {a b : ℝ} (ha : 1 ≤ a) (hab : a < b) :
    φ b < φ a := by
  have hd : φ b - φ a = 2 * (b - a) * (1 - a * b) / ((1 + a^2) * (1 + b^2)) :=
    φ_sub a b
  have h1 : 0 < b - a := by linarith
  have hb1 : 1 < b := lt_of_le_of_lt ha hab
  have hb_pos : 0 < b := by linarith
  have hprod : b ≤ a * b := by
    calc b = 1 * b := (one_mul b).symm
      _ ≤ a * b := mul_le_mul_of_nonneg_right ha (le_of_lt hb_pos)
  have h2 : 1 < a * b := lt_of_lt_of_le hb1 hprod
  have h3 : 0 < (1 + a^2) * (1 + b^2) := by positivity
  have hnum : 2 * (b - a) * (1 - a * b) < 0 := by
    have haux : 0 < a * b - 1 := by linarith
    nlinarith [mul_pos h1 haux]
  have hneg : φ b - φ a < 0 := by
    rw [hd]
    exact div_neg_of_neg_of_pos hnum h3
  linarith

-- End of noncomputable section
end
