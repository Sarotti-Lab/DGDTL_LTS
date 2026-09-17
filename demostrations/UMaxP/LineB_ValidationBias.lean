-- SPDX-FileCopyrightText: 2026 José A. Pérez
-- SPDX-License-Identifier: MIT
--

-- ==============================================================================
-- FILE: DGDTL/Protocol/LineB_ValidationBias.lean
-- OBJECTIVE: Formalization of Line B (Exception Tribunal for Validation Bias)
-- REFERENCE: Section 3.6, Supplementary Information (DGDTL-LTS)
-- ==============================================================================

import Mathlib.Data.Real.Basic
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Tactic

open Real

-- Disable the unused variables warning to strictly preserve exact signatures
set_option linter.unusedVariables false

noncomputable section

-- ============================================================
-- LINE B: Validation Bias Discriminant (Ψ)
-- ============================================================

/-- Auxiliary definition for base-10 logarithm. -/
def log10 (x : ℝ) : ℝ := Real.log x / Real.log 10

/--
Equation (S70): Validation Bias Discriminant (Ψ).
Evaluates the directional coherence of the scaling between validation and training
across different statistical moments (MAE and MSE).
-/
def Ψ (ρ_MAE ρ_MSE : ℝ) : ℝ :=
  log10 ρ_MAE * log10 ρ_MSE

-- ============================================================
-- REGIME TAXONOMY
-- ============================================================

/-
SUPPLEMENTARY DEFINITION 3.7: Regime taxonomy by Ψ.
The sign geometry in the logarithmic plane classifies the state into mutually exclusive regimes.
-/

/-- Severe Overfitting to Validation (SOV): Both moments improve proportionally. -/
def is_SOV (ρ_MAE ρ_MSE : ℝ) : Prop :=
  log10 ρ_MAE < 0 ∧ log10 ρ_MSE < 0

/-- Overfitting to Training (OFT): Both moments degrade proportionally. -/
def is_OFT (ρ_MAE ρ_MSE : ℝ) : Prop :=
  log10 ρ_MAE > 0 ∧ log10 ρ_MSE > 0

/-- Inconsistency (INC): Structural divergence between moments (opposite signs). -/
def is_INC (ρ_MAE ρ_MSE : ℝ) : Prop :=
  (log10 ρ_MAE < 0 ∧ log10 ρ_MSE > 0) ∨
  (log10 ρ_MAE > 0 ∧ log10 ρ_MSE < 0)

-- ============================================================
-- GEOMETRIC BOUNDARY (Critical axes of the logarithmic plane)
-- ============================================================

/--
SUPPLEMENTARY PROPOSITION 3.5: Geometric boundary of the validation-bias plane.
Ψ = 0 if and only if at least one of the error proportions exactly matches
the baseline (log10(ρ) = 0, i.e., ρ = 1).
This boundary separates the inflation, degradation, and inconsistency regimes.
-/
theorem Ψ_eq_zero_iff
    {ρ_MAE ρ_MSE : ℝ}
    (_h_mae_pos : 0 < ρ_MAE) -- Mathematical domain contract
    (_h_mse_pos : 0 < ρ_MSE) :
    Ψ ρ_MAE ρ_MSE = 0 ↔ log10 ρ_MAE = 0 ∨ log10 ρ_MSE = 0 := by
  unfold Ψ
  exact mul_eq_zero

-- ============================================================
-- STRUCTURAL BEHAVIOR THEOREMS
-- ============================================================

/--
SUPPLEMENTARY THEOREM 3.2 (i):
Biconditional: Ψ > 0 ⟺ SOV ∨ OFT.
Demonstrates that a positive discriminant strictly bounds the state to
symmetrical proportional scaling (either dual improvement or dual degradation).
-/
theorem Ψ_pos_iff_SOV_or_OFT
    {ρ_MAE ρ_MSE : ℝ} :
    0 < Ψ ρ_MAE ρ_MSE ↔ is_SOV ρ_MAE ρ_MSE ∨ is_OFT ρ_MAE ρ_MSE := by
  unfold Ψ is_SOV is_OFT
  rw [mul_pos_iff]
  tauto

/--
SUPPLEMENTARY THEOREM 3.2 (ii):
Biconditional: Ψ < 0 ⟺ INC.
-/
theorem Ψ_neg_iff_INC
    {ρ_MAE ρ_MSE : ℝ} :
    Ψ ρ_MAE ρ_MSE < 0 ↔ is_INC ρ_MAE ρ_MSE := by
  unfold Ψ is_INC
  rw [mul_neg_iff]
  tauto

/--
SUPPLEMENTARY THEOREM 3.2 (iii): Trichotomy and completeness.
Excluding the measure-zero boundary (ρ_MAE ≠ 1, ρ_MSE ≠ 1), every state
falls exactly into one of the three regimes (SOV, OFT, or INC).
-/
theorem regime_trichotomy
    {ρ_MAE ρ_MSE : ℝ}
    (h_mae_ne : log10 ρ_MAE ≠ 0) (h_mse_ne : log10 ρ_MSE ≠ 0) :
    is_SOV ρ_MAE ρ_MSE ∨ is_OFT ρ_MAE ρ_MSE ∨ is_INC ρ_MAE ρ_MSE := by
  rcases lt_trichotomy (Ψ ρ_MAE ρ_MSE) 0 with h | h | h
  · exact Or.inr (Or.inr (Ψ_neg_iff_INC.mp h))
  · exfalso
    rcases mul_eq_zero.mp h with h' | h' <;> [exact h_mae_ne h'; exact h_mse_ne h']
  · rcases Ψ_pos_iff_SOV_or_OFT.mp h with h' | h'
    · exact Or.inl h'
    · exact Or.inr (Or.inl h')

/--
Robust Topological Partition.
Unconditional four-way partition of the domain, accommodating the boundary explicitly
without requiring non-zero hypotheses. Ensures algorithmic completeness.
-/
theorem Ψ_four_way_partition
    (ρ_MAE ρ_MSE : ℝ) :
    is_INC ρ_MAE ρ_MSE ∨
    (log10 ρ_MAE = 0 ∨ log10 ρ_MSE = 0) ∨
    is_SOV ρ_MAE ρ_MSE ∨ is_OFT ρ_MAE ρ_MSE := by
  rcases lt_trichotomy (Ψ ρ_MAE ρ_MSE) 0 with h | h | h
  · exact Or.inl (Ψ_neg_iff_INC.mp h)
  · exact Or.inr (Or.inl (mul_eq_zero.mp h))
  · exact Or.inr (Or.inr (Ψ_pos_iff_SOV_or_OFT.mp h))

-- End of noncomputable section
end
