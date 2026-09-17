-- SPDX-FileCopyrightText: 2026 José A. Pérez
-- SPDX-License-Identifier: MIT
--

-- ==============================================================================
-- FILE: DGDTL/Topology/Relaxation.lean
-- OBJECTIVE: Formalization of Supplementary Lemma 1.1 and Corollary 1.1
-- REFERENCE: Section 1.1, Supplementary Information (DGDTL-LTS)
-- ==============================================================================

import Mathlib.Data.Set.Basic
import Mathlib.Data.Finset.Basic
import Mathlib.Order.Basic

open Set

variable {Beta : Type*}
variable {Err : Type*} [LinearOrder Err]

/--
Equation (S5) Base: Discrete Valid Set definition.
Used here to evaluate the impact of threshold relaxation on the viable subset.
-/
def K_valid (mse_v : Beta → Err) (ε_val : Err) (K_transfer : Finset Beta) : Finset Beta :=
  K_transfer.filter (fun b => mse_v b ≤ ε_val)

/--
SUPPLEMENTARY LEMMA 1.1: Monotonicity of the Viable Subset.
For any pair of internal validation thresholds ε, ε' ∈ ℝ_{>0} such that ε ≤ ε',
the set of viable solutions expands monotonically.

Equation (S4): 𝓚_valid(ε) ⊆ 𝓚_valid(ε')
-/
theorem K_valid_monotone_in_eps
    (mse_v : Beta → Err)
    (K_transfer : Finset Beta)
    {ε ε' : Err} (h_le : ε ≤ ε') :
    K_valid mse_v ε K_transfer ⊆ K_valid mse_v ε' K_transfer := by
  intro b hb
  simp [K_valid] at hb ⊢
  exact ⟨hb.1, le_trans hb.2 h_le⟩

-- Generic Merit Function Definition (φ)
-- Represents any generic evaluation metric (e.g., U-MaxP, PEL, MAE, etc.)
def Phi (Err : Type*) := Err → Err → Err

-- Formal definition of being the "minimum" of the merit function over a set
-- without relying on computable algorithms.
def IsMinMeritValue (mse_t mse_v : Beta → Err) (φ : Phi Err) (K : Finset Beta) (m : Err) : Prop :=
  (∃ b ∈ K, φ (mse_t b) (mse_v b) = m) ∧
  (∀ b ∈ K, m ≤ φ (mse_t b) (mse_v b))

/--
SUPPLEMENTARY COROLLARY 1.1 (ii): Topological descent of the minimum under relaxation.
Demonstrates that expanding the viable space strictly bounds the new minimum
to be less than or equal to the original minimum (m' ≤ m), independent of
the mathematical formulation of the generic merit function φ.

This formalizes the structural loss of statistical reliability: as the threshold
relaxes away from the absolute anchor, the global minimizer shifts toward
regions with larger absolute errors and higher dispersion.
-/
theorem min_merit_decreases_with_relaxation
    (mse_t mse_v : Beta → Err)
    (φ : Phi Err)
    (K_transfer : Finset Beta)
    {ε ε' : Err}
    (h_le : ε ≤ ε')
    (m m' : Err)
    (h_min : IsMinMeritValue mse_t mse_v φ (K_valid mse_v ε K_transfer) m)
    (h_min' : IsMinMeritValue mse_t mse_v φ (K_valid mse_v ε' K_transfer) m') :
    m' ≤ m := by

  rcases h_min with ⟨⟨b, hb_in_K, hb_eq_m⟩, _⟩
  rcases h_min' with ⟨_, h_m'_le_all⟩

  have h_sub : K_valid mse_v ε K_transfer ⊆ K_valid mse_v ε' K_transfer :=
    K_valid_monotone_in_eps mse_v K_transfer h_le

  have hb_in_K' : b ∈ K_valid mse_v ε' K_transfer := h_sub hb_in_K
  have h_m'_le_val_b : m' ≤ φ (mse_t b) (mse_v b) := h_m'_le_all b hb_in_K'

  rw [hb_eq_m] at h_m'_le_val_b
  exact h_m'_le_val_b
