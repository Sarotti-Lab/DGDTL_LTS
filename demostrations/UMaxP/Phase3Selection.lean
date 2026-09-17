-- SPDX-FileCopyrightText: 2026 José A. Pérez
-- SPDX-License-Identifier: MIT
--

-- ==============================================================================
-- FILE: DGDTL/Protocol/Phase3Selection.lean
-- OBJECTIVE: Formalization of Phase 3 Structural Selection Protocol
-- REFERENCE: Section 3.5, Supplementary Information (DGDTL-LTS)
-- ==============================================================================

import Mathlib.Data.Real.Basic
import Mathlib.Tactic

open Real

-- Disable the unused variables warning to strictly preserve exact signatures
set_option linter.unusedVariables false

noncomputable section

-- ============================================================
-- PART I: INCOHERENCE-PENALIZED ERROR (E_inc)
-- ============================================================

/--
Supplementary Definition 3.5: Incoherence-Penalized Error (E_inc).
Formalizes Equation (S66) from the manuscript.
Penalizes the geometric mean of the validation and training errors based on
the loss of structural coherence (φ).
-/
def E_inc (e_val e_tr φ : ℝ) : ℝ :=
  Real.sqrt (e_val * e_tr) * (1 - φ)

-- ============================================================
-- PROPERTIES OF E_inc (Supplementary Proposition 3.2)
-- ============================================================

/--
SUPPLEMENTARY PROPOSITION 3.2 (i) - Part 1: Non-negativity.
E_inc is inherently non-negative given that φ ≤ 1.
-/
theorem E_inc_nonneg
    {e_val e_tr φ : ℝ}
    (h_φ : φ ≤ 1) :
    0 ≤ E_inc e_val e_tr φ := by
  unfold E_inc
  have h_sqrt : 0 ≤ Real.sqrt (e_val * e_tr) := Real.sqrt_nonneg _
  have h_φ_term : 0 ≤ 1 - φ := sub_nonneg.mpr h_φ
  exact mul_nonneg h_sqrt h_φ_term

/--
SUPPLEMENTARY PROPOSITION 3.2 (i) - Part 2: Zero-condition Biconditional.
E_inc = 0 if and only if φ = 1 or the product of the errors is zero.
-/
theorem E_inc_eq_zero_iff
    {e_val e_tr φ : ℝ}
    (h_eval : 0 ≤ e_val)
    (h_etr : 0 ≤ e_tr) :
    E_inc e_val e_tr φ = 0 ↔ e_val * e_tr = 0 ∨ φ = 1 := by
  unfold E_inc
  constructor
  · intro h
    cases mul_eq_zero.mp h with
    | inl h_sqrt => left; exact (Real.sqrt_eq_zero (mul_nonneg h_eval h_etr)).mp h_sqrt
    | inr h_φ => right; linarith
  · intro h
    cases h with
    | inl h_prod =>
        have h_sqrt : Real.sqrt (e_val * e_tr) = 0 := (Real.sqrt_eq_zero (mul_nonneg h_eval h_etr)).mpr h_prod
        rw [h_sqrt, zero_mul]
    | inr h_φ =>
        have h_sub : 1 - φ = 0 := by linarith
        rw [h_sub, mul_zero]

/--
SUPPLEMENTARY PROPOSITION 3.2 (ii): Strict Anti-monotonicity.
E_inc is strictly decreasing with respect to φ, provided e_val, e_tr > 0.
-/
theorem E_inc_strict_anti_mono_φ
    {e_val e_tr φ₁ φ₂ : ℝ}
    (h_eval : 0 < e_val)
    (h_etr : 0 < e_tr)
    (h_φ : φ₁ < φ₂) :
    E_inc e_val e_tr φ₂ < E_inc e_val e_tr φ₁ := by
  unfold E_inc
  have h_prod : 0 < e_val * e_tr := mul_pos h_eval h_etr
  have h_sqrt : 0 < Real.sqrt (e_val * e_tr) := Real.sqrt_pos.mpr h_prod
  have h_sub : 1 - φ₂ < 1 - φ₁ := by linarith
  exact mul_lt_mul_of_pos_left h_sub h_sqrt

/--
SUPPLEMENTARY PROPOSITION 3.2 (iii) - Part 1: Weak monotonicity (e_val).
-/
theorem E_inc_mono_eval
    {e_val₁ e_val₂ e_tr φ : ℝ}
    (h_eval_le : e_val₁ ≤ e_val₂)
    (h_etr : 0 ≤ e_tr)
    (h_φ : φ ≤ 1) :
    E_inc e_val₁ e_tr φ ≤ E_inc e_val₂ e_tr φ := by
  unfold E_inc
  have h_φ_term : 0 ≤ 1 - φ := sub_nonneg.mpr h_φ
  have h_prod : e_val₁ * e_tr ≤ e_val₂ * e_tr := mul_le_mul_of_nonneg_right h_eval_le h_etr
  have h_sqrt : Real.sqrt (e_val₁ * e_tr) ≤ Real.sqrt (e_val₂ * e_tr) := Real.sqrt_le_sqrt h_prod
  exact mul_le_mul_of_nonneg_right h_sqrt h_φ_term

/--
SUPPLEMENTARY PROPOSITION 3.2 (iii) - Part 2: Weak monotonicity (e_tr).
-/
theorem E_inc_mono_etr
    {e_val e_tr₁ e_tr₂ φ : ℝ}
    (h_etr_le : e_tr₁ ≤ e_tr₂)
    (h_eval : 0 ≤ e_val)
    (h_φ : φ ≤ 1) :
    E_inc e_val e_tr₁ φ ≤ E_inc e_val e_tr₂ φ := by
  unfold E_inc
  have h_φ_term : 0 ≤ 1 - φ := sub_nonneg.mpr h_φ
  have h_prod : e_val * e_tr₁ ≤ e_val * e_tr₂ := mul_le_mul_of_nonneg_left h_etr_le h_eval
  have h_sqrt : Real.sqrt (e_val * e_tr₁) ≤ Real.sqrt (e_val * e_tr₂) := Real.sqrt_le_sqrt h_prod
  exact mul_le_mul_of_nonneg_right h_sqrt h_φ_term

/--
SUPPLEMENTARY PROPOSITION 3.2 (iii) - Part 3: Strict monotonicity (e_val).
Formalizes the condition that monotonicity is strict whenever φ < 1.
-/
theorem E_inc_strict_mono_eval
    {e_val₁ e_val₂ e_tr φ : ℝ}
    (h_eval_lt : e_val₁ < e_val₂)
    (h_eval1_nonneg : 0 ≤ e_val₁)
    (h_etr : 0 < e_tr)
    (h_φ : φ < 1) :
    E_inc e_val₁ e_tr φ < E_inc e_val₂ e_tr φ := by
  unfold E_inc
  have h_φ_term : 0 < 1 - φ := by linarith
  have h_prod : e_val₁ * e_tr < e_val₂ * e_tr := mul_lt_mul_of_pos_right h_eval_lt h_etr
  have h_sqrt : Real.sqrt (e_val₁ * e_tr) < Real.sqrt (e_val₂ * e_tr) :=
    Real.sqrt_lt_sqrt (mul_nonneg h_eval1_nonneg h_etr.le) h_prod
  exact mul_lt_mul_of_pos_right h_sqrt h_φ_term

/--
SUPPLEMENTARY PROPOSITION 3.2 (iii) - Part 4: Strict monotonicity (e_tr).
Symmetrical explicit strict boundary condition for φ < 1.
-/
theorem E_inc_strict_mono_etr
    {e_val e_tr₁ e_tr₂ φ : ℝ}
    (h_etr_lt : e_tr₁ < e_tr₂)
    (h_etr1_nonneg : 0 ≤ e_tr₁)
    (h_eval : 0 < e_val)
    (h_φ : φ < 1) :
    E_inc e_val e_tr₁ φ < E_inc e_val e_tr₂ φ := by
  unfold E_inc
  have h_φ_term : 0 < 1 - φ := by linarith
  have h_prod : e_val * e_tr₁ < e_val * e_tr₂ := mul_lt_mul_of_pos_left h_etr_lt h_eval
  have h_sqrt : Real.sqrt (e_val * e_tr₁) < Real.sqrt (e_val * e_tr₂) :=
    Real.sqrt_lt_sqrt (mul_nonneg h_eval.le h_etr1_nonneg) h_prod
  exact mul_lt_mul_of_pos_right h_sqrt h_φ_term


-- ============================================================
-- PART II: HYPERBOLIC TAIL FACTOR (H)
-- ============================================================

/--
Definition of the Hyperbolic Tail Factor (H).
Formalizes Equation (S68) from the manuscript.
-/
def H_factor (Φ_emp ε : ℝ) : ℝ :=
  (1 - Φ_emp) / (Φ_emp + ε)

-- ============================================================
-- PROPERTIES OF THE H FACTOR (Supplementary Proposition 3.3)
-- ============================================================

/--
SUPPLEMENTARY PROPOSITION 3.3 (ii): Equivalent algebraic representation.
Makes the regularized rational structure explicit.
-/
lemma H_factor_equiv
    {Φ_emp ε : ℝ}
    (h_den : Φ_emp + ε ≠ 0) :
    H_factor Φ_emp ε = (1 + ε) / (Φ_emp + ε) - 1 := by
  unfold H_factor
  calc
    (1 - Φ_emp) / (Φ_emp + ε)
      = (1 + ε - (Φ_emp + ε)) / (Φ_emp + ε) := by ring
    _ = (1 + ε) / (Φ_emp + ε) - (Φ_emp + ε) / (Φ_emp + ε) := sub_div (1 + ε) (Φ_emp + ε) (Φ_emp + ε)
    _ = (1 + ε) / (Φ_emp + ε) - 1 := by rw [div_self h_den]

/--
SUPPLEMENTARY PROPOSITION 3.3 (i): H is strictly decreasing with respect to Φ_emp.
-/
theorem H_factor_strict_anti_mono
    {Φ_emp₁ Φ_emp₂ ε : ℝ}
    (h_ε : 0 < ε)
    (h_Φ1 : 0 ≤ Φ_emp₁)
    (h_lt : Φ_emp₁ < Φ_emp₂) :
    H_factor Φ_emp₂ ε < H_factor Φ_emp₁ ε := by
  have h_den1_pos : 0 < Φ_emp₁ + ε := by linarith
  have h_den2_pos : 0 < Φ_emp₂ + ε := by linarith
  have h_den1_nz : Φ_emp₁ + ε ≠ 0 := ne_of_gt h_den1_pos
  have h_den2_nz : Φ_emp₂ + ε ≠ 0 := ne_of_gt h_den2_pos
  rw [H_factor_equiv h_den2_nz, H_factor_equiv h_den1_nz]
  have h_inv : 1 / (Φ_emp₂ + ε) < 1 / (Φ_emp₁ + ε) := one_div_lt_one_div_of_lt h_den1_pos (by linarith)
  have h_num : 0 < 1 + ε := by linarith
  have h_mul : (1 + ε) * (1 / (Φ_emp₂ + ε)) < (1 + ε) * (1 / (Φ_emp₁ + ε)) := mul_lt_mul_of_pos_left h_inv h_num
  have h_div : (1 + ε) / (Φ_emp₂ + ε) < (1 + ε) / (Φ_emp₁ + ε) := by
    calc
      (1 + ε) / (Φ_emp₂ + ε) = (1 + ε) * (1 / (Φ_emp₂ + ε)) := by ring
      _ < (1 + ε) * (1 / (Φ_emp₁ + ε)) := h_mul
      _ = (1 + ε) / (Φ_emp₁ + ε) := by ring
  exact sub_lt_sub_right h_div 1

/--
SUPPLEMENTARY PROPOSITION 3.3 (iii): Full Biconditional.
H reverses the order in both directions. Proves the equivalence
"argmin H = argmax Φ_emp" as an iff statement.
-/
theorem H_factor_order_reversing
    {Φ_emp1 Φ_emp2 ε : ℝ} (h_ε : 0 < ε) (hΦ1 : 0 ≤ Φ_emp1) (hΦ2 : 0 ≤ Φ_emp2) :
    H_factor Φ_emp1 ε < H_factor Φ_emp2 ε ↔ Φ_emp2 < Φ_emp1 := by
  constructor
  · intro hH
    rcases lt_trichotomy Φ_emp1 Φ_emp2 with hlt | heq | hgt
    · exfalso
      have := H_factor_strict_anti_mono h_ε hΦ1 hlt
      linarith
    · exfalso
      rw [heq] at hH
      exact lt_irrefl _ hH
    · exact hgt
  · intro hlt
    exact H_factor_strict_anti_mono h_ε hΦ2 hlt

/--
SUPPLEMENTARY PROPOSITION 3.3 (iv): Singularity avoidance.
The constant ε evades the singularity precisely at Φ_emp = 0,
where H evaluates to a finite boundary (1/ε).
-/
theorem H_factor_no_singularity_at_zero
    {ε : ℝ} (_h_ε : 0 < ε) :
    H_factor 0 ε = 1 / ε := by
  unfold H_factor
  simp

/--
SUPPLEMENTARY PROPOSITION 3.3 (v): Gap Amplification Near Zero.
For a fixed positive increment δ in Φ_emp, the induced gap in H is strictly
greater when the starting point is closer to zero.
-/
theorem H_factor_gap_amplified_near_zero
    {ε : ℝ} (h_ε : 0 < ε)
    {a1 a2 δ : ℝ} (ha1 : 0 ≤ a1) (hδ : 0 < δ) (h_lt : a1 < a2) :
    H_factor a2 ε - H_factor (a2 + δ) ε < H_factor a1 ε - H_factor (a1 + δ) ε := by
  have ha2 : (0:ℝ) ≤ a2 := by linarith
  have ha1e : (0:ℝ) < a1 + ε := by linarith
  have ha2e : (0:ℝ) < a2 + ε := by linarith
  have ha1de : (0:ℝ) < a1 + δ + ε := by linarith
  have ha2de : (0:ℝ) < a2 + δ + ε := by linarith

  have heq1 : H_factor a1 ε - H_factor (a1 + δ) ε = (1 + ε) * δ / ((a1 + ε) * (a1 + δ + ε)) := by
    unfold H_factor; field_simp; ring

  have heq2 : H_factor a2 ε - H_factor (a2 + δ) ε = (1 + ε) * δ / ((a2 + ε) * (a2 + δ + ε)) := by
    unfold H_factor; field_simp; ring

  have hden1 : (0:ℝ) < (a1 + ε) * (a1 + δ + ε) := mul_pos ha1e ha1de
  have hden2 : (0:ℝ) < (a2 + ε) * (a2 + δ + ε) := mul_pos ha2e ha2de
  have hprod : (a1 + ε) * (a1 + δ + ε) < (a2 + ε) * (a2 + δ + ε) := by
    nlinarith [mul_pos (sub_pos.mpr h_lt) (by linarith : (0:ℝ) < a1 + a2 + δ + 2 * ε)]

  have hpos_num : (0:ℝ) < (1 + ε) * δ := by positivity
  rw [heq1, heq2, div_lt_div_iff₀ hden2 hden1]
  exact mul_lt_mul_of_pos_left hprod hpos_num


-- ============================================================
-- PART III: COMBINATORIAL COMPLETENESS OF PHASE 3
-- ============================================================

/--
Concordance definition (Step 3b-II(a) in Supplementary Definition 3.6):
Argmax coincidence between φ and Φ_emp (`same_argmax`), EVT arbiter indifference
(`evt_indifferent`, |ΔΦ_emp| < ε), or both Φ_emp values contained inside the noise channel.
-/
def concordance (same_argmax evt_indifferent : Prop) (Φ_emp1 Φ_emp2 : ℝ) : Prop :=
  same_argmax ∨ evt_indifferent ∨ (Φ_emp1 = 0 ∧ Φ_emp2 = 0)

/--
SUBSTANTIVE PROOF of Supplementary Proposition 3.4 (Completeness):
Divergence (¬concordance) automatically implies max(Φ_emp) > 0, which is the
exact precondition required by Step 3b-II(b) for the Hyperbolic Factor.
This guarantees no topological case is left without a valid resolution branch.
-/
theorem divergence_implies_active_evt
    {same_argmax evt_indifferent : Prop} {Φ_emp1 Φ_emp2 : ℝ}
    (hΦ1 : 0 ≤ Φ_emp1) (hΦ2 : 0 ≤ Φ_emp2)
    (h_not_conc : ¬ concordance same_argmax evt_indifferent Φ_emp1 Φ_emp2) :
    0 < max Φ_emp1 Φ_emp2 := by
  by_contra h
  push Not at h
  have hΦ1_le : Φ_emp1 ≤ 0 := le_trans (le_max_left Φ_emp1 Φ_emp2) h
  have hΦ2_le : Φ_emp2 ≤ 0 := le_trans (le_max_right Φ_emp1 Φ_emp2) h
  apply h_not_conc
  unfold concordance
  right; right
  exact ⟨le_antisymm hΦ1_le hΦ1, le_antisymm hΦ2_le hΦ2⟩

/--
Logical partition of the three decision branches in Step 3b.
Provides pure partition mechanics mapping to Supplementary Proposition 3.4.
-/
theorem phase3_completeness
    (δ_E ε_tie : ℝ)
    (concordance : Prop) :
    (δ_E < ε_tie) ∨
    (δ_E ≥ ε_tie ∧ concordance) ∨
    (δ_E ≥ ε_tie ∧ ¬concordance) := by
  by_cases h_delta : δ_E < ε_tie
  · left; exact h_delta
  · right
    have h_ge : δ_E ≥ ε_tie := by linarith
    by_cases h_conc : concordance
    · left; exact ⟨h_ge, h_conc⟩
    · right; exact ⟨h_ge, h_conc⟩

-- End of noncomputable section
end
