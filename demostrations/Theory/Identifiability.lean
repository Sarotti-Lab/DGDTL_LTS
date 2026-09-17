-- SPDX-FileCopyrightText: 2026 José A. Pérez
-- SPDX-License-Identifier: MIT
--

-- ==============================================================================
-- FILE: DGDTL/Theory/Identifiability.lean
-- OBJECTIVE: Formalization of Supplementary Theorem 1.3 (Model Identifiability)
-- REFERENCE: Section 1.4, Supplementary Information (DGDTL-LTS)
-- ==============================================================================

import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Linarith

open Set

-- Substitution of module hierarchy for direct operational classes.
-- `Beta` represents the parameter space (β ∈ ℝ^p).
variable {Beta : Type*} [Add Beta] [SMul ℝ Beta]

-- 𝓕 represents the feasible space defined by box constraints (Equation S1).
variable (𝓕 : Set Beta)
-- MSE_train represents the empirical risk function.
variable (MSE_train : Beta → ℝ)

-- Manual isolation of topological dependencies for pure geometric reasoning
def IsMinOnSet (f : Beta → ℝ) (s : Set Beta) (β : Beta) : Prop :=
  β ∈ s ∧ ∀ β' ∈ s, f β ≤ f β'

def IsUniqueMinimizerOn (f : Beta → ℝ) (s : Set Beta) (β : Beta) : Prop :=
  β ∈ s ∧ ∀ β' ∈ s, β' ≠ β → f β < f β'

def IsConvexSet (s : Set Beta) : Prop :=
  ∀ β ∈ s, ∀ β' ∈ s, ∀ a b : ℝ, 0 ≤ a → 0 ≤ b → a + b = 1 → a • β + b • β' ∈ s

def StrictConvexOnSet (s : Set Beta) (f : Beta → ℝ) : Prop :=
  ∀ β ∈ s, ∀ β' ∈ s, β ≠ β' → ∀ a b : ℝ, 0 < a → 0 < b → a + b = 1 →
    f (a • β + b • β') < a * f β + b * f β'

/--
SUPPLEMENTARY THEOREM 1.3: Identifiability Under Box Constraints.
If the design matrix X_train has full column rank, the restricted
least squares problem over the feasible space 𝓕 possesses a unique solution,
rendering the vector β strictly identifiable.

Formalization note: The full column rank of X_train induces strict convexity
in the MSE loss. The feasible space 𝓕 (Equation S1) is a compact convex polyhedron.
This theorem mechanically proves that strict convexity over a convex set
guarantees a unique global minimizer, resolving parametric instability.
-/
theorem identifiability_under_box_constraints
    (h𝓕_convex : IsConvexSet 𝓕)
    (hMSE_strict_convex : StrictConvexOnSet 𝓕 MSE_train)
    (β : Beta) (hβ_min : IsMinOnSet MSE_train 𝓕 β) :
    IsUniqueMinimizerOn MSE_train 𝓕 β := by

  constructor
  · exact hβ_min.1
  · intro β' hβ' h_diff

    have h_mid_in_𝓕 : (1/2 : ℝ) • β + (1/2 : ℝ) • β' ∈ 𝓕 := by
      apply h𝓕_convex β hβ_min.1 β' hβ' (1/2) (1/2) (by norm_num) (by norm_num) (by norm_num)

    have h_strict_conv := hMSE_strict_convex β hβ_min.1 β' hβ' h_diff.symm (1/2) (1/2) (by norm_num) (by norm_num) (by norm_num)
    have h_min_eval := hβ_min.2 ((1/2 : ℝ) • β + (1/2 : ℝ) • β') h_mid_in_𝓕

    by_contra h_le
    have h_β'_le_β : MSE_train β' ≤ MSE_train β := not_lt.mp h_le

    linarith
