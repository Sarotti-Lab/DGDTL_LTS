-- SPDX-FileCopyrightText: 2026 José A. Pérez
-- SPDX-License-Identifier: MIT
--

-- ==============================================================================
-- FILE: DGDTL/Topology/Existence.lean
-- OBJECTIVE: Formalization of Supplementary Theorem 1.1 (Existence Conditions)
-- REFERENCE: Section 1.1, Supplementary Information (DGDTL-LTS)
-- ==============================================================================

import Mathlib.Data.Set.Basic
import Mathlib.Data.Finset.Basic
import Mathlib.Order.Basic

open Set

-- We maintain abstract types for absolute generality across regression families.
-- `Beta` represents the parameter space (β ∈ ℝ^p).
-- `Err` represents the error metric space (e.g., MSE in ℝ).
variable {Beta : Type*}
variable {Err : Type*} [LinearOrder Err]

/--
Equation (S2): Training accuracy space.
𝓕_train(τ) = { β ∈ 𝓕 | MSE_train(β) ≤ τ }
-/
def F_train (mse_t : Beta → Err) (τ_train : Err) : Set Beta :=
  { b | mse_t b ≤ τ_train }

/--
Equation (S3): Internal validation accuracy space.
𝓕_val(τ) = { β ∈ 𝓕 | MSE_val(β) ≤ τ }
-/
def F_val (mse_v : Beta → Err) (τ_val : Err) : Set Beta :=
  { b | mse_v b ≤ τ_val }

/--
Equation (S5): Discrete Valid Set (Selection-evaluation stage).
𝓚_valid = { β^(k) ∈ 𝓚_transfer | MSE_val(β^(k)) ≤ ε_val }

Filters the discrete ensemble transferred from the training phase
using the continuous validation threshold.
-/
def K_valid (mse_v : Beta → Err) (ε_val : Err) (K_transfer : Finset Beta) : Finset Beta :=
  K_transfer.filter (fun b => mse_v b ≤ ε_val)

/--
SUPPLEMENTARY THEOREM 1.1 (i): Sufficient condition for non-emptiness.
Demonstrates that the filtered set (𝓚_valid) is non-empty if and only if
the topological intersection between the discrete ensemble (𝓚_transfer) and
the continuous validation space (𝓕_val) is non-empty.

Formal Statement: 𝓚_valid ≠ ∅  ⟺  𝓚_transfer ∩ 𝓕_val(ε_val) ≠ ∅
-/
theorem K_valid_nonempty_iff
    (mse_v : Beta → Err) (ε_val : Err) (K_transfer : Finset Beta) :
    (K_valid mse_v ε_val K_transfer).Nonempty ↔
    ((K_transfer : Set Beta) ∩ F_val mse_v ε_val).Nonempty := by

  -- Expand definitions to set theory level
  unfold K_valid F_val

  -- Reduce the problem to pure predicate logic (existential quantifiers)
  simp only [Finset.Nonempty, Set.Nonempty, Finset.mem_filter,
             Set.mem_inter_iff, Finset.mem_coe, Set.mem_setOf_eq]

/--
SUPPLEMENTARY THEOREM 1.1 (ii): Implicit Necessary Condition.
If 𝓚_valid is non-empty, then the intersection of the continuous
accuracy spaces (𝓕_train and 𝓕_val) must be non-empty.

This underpins the diagnostic power of DGDTL: an empty valid set
structurally guarantees the absence of overlapping generalization spaces.
-/
theorem K_valid_implies_F_train_inter_F_val_nonempty
    (mse_t mse_v : Beta → Err)
    (ε_train ε_val : Err)
    (K_transfer : Finset Beta)
    (h_subset : (K_transfer : Set Beta) ⊆ F_train mse_t ε_train)
    (h_nonempty : (K_valid mse_v ε_val K_transfer).Nonempty) :
    (F_train mse_t ε_train ∩ F_val mse_v ε_val).Nonempty := by

  -- Extraction of the viable candidate anchored to the discrete optimum
  rcases h_nonempty with ⟨b, hb⟩
  simp only [K_valid, Finset.mem_filter] at hb

  -- Direct instantiation into the continuous intersection space
  use b
  simp only [Set.mem_inter_iff, F_train, F_val, Set.mem_setOf_eq]
  exact ⟨h_subset hb.1, hb.2⟩
