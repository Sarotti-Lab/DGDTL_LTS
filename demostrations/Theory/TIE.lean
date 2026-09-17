-- SPDX-FileCopyrightText: 2026 José A. Pérez
-- SPDX-License-Identifier: MIT
--

-- ==============================================================================
-- FILE: DGDTL/Theory/TIE_Properties.lean
-- OBJECTIVE:
--   Formalization of fundamental analytical properties of the TIE metric:
--
--   • Scale Invariance
--   • Monotonic Growth of the Diversity Component
--   • Asymptotic Divergence near the Origin
--
-- This file establishes mathematically rigorous properties required for the
-- theoretical consistency of the TIE framework.
-- ==============================================================================

import Mathlib.Data.Real.Basic
import Mathlib.Analysis.SpecialFunctions.Log.Deriv
import Mathlib.Analysis.Calculus.Deriv.Add
import Mathlib.Analysis.Calculus.Deriv.Mul
import Mathlib.Topology.Algebra.Order.Field

open Set Filter Topology

-- ==============================================================================
-- PROPERTY 2: SCALE INVARIANCE
-- ==============================================================================

/--
Scale invariance of the performance ratio.

If both validation and baseline errors are scaled by the same nonzero factor
`c²`, their ratio remains unchanged.

Mathematically:

  (c² · mse_vldt) / (c² · mse_base)
    = mse_vldt / mse_base

for every `c ≠ 0`.
-/
theorem scale_invariance
    (mse_vldt mse_base c : ℝ)
    (hc : c ≠ 0) :
    (c ^ 2 * mse_vldt) / (c ^ 2 * mse_base)
      = mse_vldt / mse_base := by
  exact mul_div_mul_left mse_vldt mse_base (pow_ne_zero 2 hc)

-- ==============================================================================
-- TIE DIVERSITY COMPONENT
-- ==============================================================================

/--
Logarithmic diversity component used by the TIE metric.

The transformation

  log(1 + 100x)

is strictly increasing on its domain and exhibits diminishing marginal growth,
providing a compressed representation of diversity contributions.
-/
noncomputable def tie_diversity (x : ℝ) : ℝ :=
  Real.log (1 + 100 * x)

-- ==============================================================================
-- PROPERTY 3: MONOTONIC GROWTH
-- ==============================================================================

/--
First derivative of the diversity component.

The derivative is

  d/dx log(1 + 100x) = 100 / (1 + 100x).

Since the denominator is strictly positive for `x ≥ 0`, the derivative is
strictly positive throughout the operational domain of the metric, implying
monotonic growth.
-/
theorem tie_diversity_deriv_first
    (x : ℝ)
    (hx : 0 ≤ x) :
    HasDerivAt tie_diversity
      (100 / (1 + 100 * x)) x := by

  unfold tie_diversity

  have h_inner_pos : 0 < 1 + 100 * x := by
    positivity

  have h_inner_ne : 1 + 100 * x ≠ 0 :=
    ne_of_gt h_inner_pos

  have h_deriv_inner :
      HasDerivAt (fun y => 1 + 100 * y) 100 x := by
    simpa using
      (HasDerivAt.const_add 1
        (HasDerivAt.const_mul 100 (hasDerivAt_id x)))

  exact HasDerivAt.log h_deriv_inner h_inner_ne

-- ==============================================================================
-- PROPERTY 4: ASYMPTOTIC DIVERGENCE
-- ==============================================================================

variable (pic div_term : ℝ)

/--
Asymptotic divergence of the inverse-scale contribution.

For strictly positive constants `pic` and `div_term`,

  pic * (div_term / s)

diverges to positive infinity as `s → 0⁺`.

Formally:

  lim_{s → 0⁺} pic · div_term / s = +∞.

This result characterizes the asymptotic behavior of the inverse-scale term
appearing in the TIE formulation.
-/
theorem tie_asymptotic_divergence
    (h_pic : 0 < pic)
    (h_div : 0 < div_term) :
    Tendsto
      (fun s => pic * (div_term / s))
      (𝓝[>] (0 : ℝ))
      atTop := by

  have h_const_pos : 0 < pic * div_term :=
    mul_pos h_pic h_div

  have h_rewrite :
      (fun s => pic * (div_term / s))
        =
      (fun s : ℝ => (pic * div_term) * s⁻¹) := by
    ext s
    field_simp

  rw [h_rewrite]

  -- Standard Mathlib result:
  -- lim_{s → 0⁺} s⁻¹ = +∞.
  have h_inv :
      Tendsto (fun s : ℝ => s⁻¹)
        (𝓝[>] (0 : ℝ))
        atTop :=
    inv_nhdsGT_zero.le

  exact Tendsto.const_mul_atTop h_const_pos h_inv
