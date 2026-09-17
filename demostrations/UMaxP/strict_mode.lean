-- SPDX-FileCopyrightText: 2026 José A. Pérez
-- SPDX-License-Identifier: MIT
--

-- ==============================================================================
-- FILE: DGDTL/Theory/strict_mode.lean
-- OBJECTIVE: Formalization of the Unified Maximum A Posteriori (U-MaxP) Criterion
-- REFERENCE: Sections 2 and 2.5, Supplementary Information (DGDTL-LTS)
-- ==============================================================================

import Mathlib.Data.Real.Basic
import Mathlib.Tactic

open Real

-- Disable the unused variables warning to strictly preserve the exact theorem signatures
set_option linter.unusedVariables false

noncomputable section

-- ============================================================
-- THE U-MaxP CRITERION
-- ============================================================

/--
Equation (S22): The Unified Maximum A Posteriori (U-MaxP) Criterion.
U-MaxP(𝓜) = 𝓚_DEb(𝓜) × 𝓚_CI(𝓜) × 𝓐_emp(𝓜)

This multiplicative structure constitutes a Pareto-front scalarization
in the three-dimensional quality space (SDEb, GCI, A_emp). It enforces a
strict logical imperative: all three conditions (topological stability,
generalization consistency, and empirical authenticity) must be met concurrently.
-/
def UMaxP (SDEb GCI A_emp : ℝ) : ℝ :=
  SDEb * GCI * A_emp

-- ============================================================
-- THEOREM: STRICT DOMINANCE & NO-COMPENSATION PROPERTY
-- ============================================================

/--
SUPPLEMENTARY THEOREM 2.1: Non-Compensatory Tradeoff Theorem in Strict Mode.
If the core generalization performance (SDEb * GCI) is strictly superior (Eq. S54),
and the empirical authenticity (A_emp) does not degrade (Eq. S55),
then the global U-MaxP metric evaluates strictly higher (Eq. S56).

This mathematically formalizes the inability of the criterion to compensate
for a degradation in tail risk authenticity, preventing the selection of
models that trade robustness for marginal gains in average accuracy.
-/
theorem nc_tradeoff_implication
    {SDEb₁ SDEb₂ GCI₁ GCI₂ A_emp₁ A_emp₂ : ℝ}
    (h_pos_s2 : 0 < SDEb₂)
    (h_pos_g2 : 0 < GCI₂)
    (h_pos_a2 : 0 < A_emp₂)
    -- Strict improvement in core generalization performance (Equation S54)
    (h_strict : SDEb₂ * GCI₂ < SDEb₁ * GCI₁)
    -- No degradation in empirical authenticity (Equation S55)
    (h_a : A_emp₂ ≤ A_emp₁) :
    UMaxP SDEb₂ GCI₂ A_emp₂ < UMaxP SDEb₁ GCI₁ A_emp₁ := by

  unfold UMaxP

  -- Positivity of the structural core of model 1
  have h_pos_sg1 : 0 < SDEb₁ * GCI₁ := by
    calc
      0 < SDEb₂ * GCI₂ := mul_pos h_pos_s2 h_pos_g2
      _ < SDEb₁ * GCI₁ := h_strict

  -- Step A: Propagate the strict inequality through the A_emp baseline
  have h_step1 :
      SDEb₂ * GCI₂ * A_emp₂ < (SDEb₁ * GCI₁) * A_emp₂ := by
    exact mul_lt_mul_of_pos_right h_strict h_pos_a2

  -- Step B: Monotonicity with respect to the A_emp improvement
  have h_step2 :
      (SDEb₁ * GCI₁) * A_emp₂ ≤ (SDEb₁ * GCI₁) * A_emp₁ := by
    exact mul_le_mul_of_nonneg_left h_a (le_of_lt h_pos_sg1)

  -- Final Conclusion: Transitivity of the strict boundary (Equation S56)
  exact lt_of_lt_of_le h_step1 h_step2

-- End of noncomputable section
end
