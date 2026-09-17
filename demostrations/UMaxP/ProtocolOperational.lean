-- SPDX-FileCopyrightText: 2026 José A. Pérez
-- SPDX-License-Identifier: MIT

import Mathlib.Data.Real.Basic
import Mathlib.Analysis.SpecialFunctions.Pow.Real
import Mathlib.Tactic

/-!
# Operational correspondence for the Python Structural Selection Protocol

This module formalizes the deterministic rules that were explicitly outside
the scope of the original `StructuralSelection.lean`: Phase-3 Step 3a,
the post-dictamen stability audit, and the operational Line-B observables and
VBD verdict classifier.  Numerical inputs are modeled over `ℝ`; DataFrame
construction, logging and report serialization are implementation concerns.
-/

namespace DGDTL_LTS.Operational

noncomputable section

inductive BinaryChoice
  | first | second
  deriving Repr, DecidableEq

/-- Deterministic argmax used by Python: the second candidate must be strictly
larger; exact equality is resolved in favor of the first candidate. -/
def chooseHigher (x₁ x₂ : ℝ) : BinaryChoice :=
  if x₂ > x₁ then BinaryChoice.second else BinaryChoice.first

theorem chooseHigher_deterministic (x₁ x₂ : ℝ) :
    ∃! c : BinaryChoice, chooseHigher x₁ x₂ = c :=
  ⟨_, rfl, fun _ h => h.symm⟩

theorem chooseHigher_tie_first (x : ℝ) :
    chooseHigher x x = BinaryChoice.first := by
  unfold chooseHigher
  simp

/-- Phase-3 dual-density index for scouts having both Run 1 and Run 2. -/
def U_comp (u₁ u₂ φ₁ φ₂ : ℝ) : ℝ :=
  Real.sqrt (u₁ * u₂) / (1 + |φ₂ - φ₁|)

/-- Exact Step-3a routing: compare `U_comp` when both scouts provide it;
otherwise use the Python fallback comparison on candidate `φ`. -/
def chooseStep3a (uComp₁ uComp₂ : Option ℝ) (φ₁ φ₂ : ℝ) : BinaryChoice :=
  match uComp₁, uComp₂ with
  | some u₁, some u₂ => chooseHigher u₁ u₂
  | _, _ => chooseHigher φ₁ φ₂

theorem chooseStep3a_deterministic
    (uComp₁ uComp₂ : Option ℝ) (φ₁ φ₂ : ℝ) :
    ∃! c : BinaryChoice, chooseStep3a uComp₁ uComp₂ φ₁ φ₂ = c :=
  ⟨_, rfl, fun _ h => h.symm⟩

/-- A component activates the Python stability audit precisely when the
provisional winner is lower by at least `θ`. -/
def componentReversal (winner loser θ : ℝ) : Prop :=
  |winner - loser| ≥ θ ∧ winner < loser

def stabilityReversal
    (sdeWinner sdeLoser gciWinner gciLoser aempWinner aempLoser θ : ℝ) : Prop :=
  componentReversal sdeWinner sdeLoser θ ∨
  componentReversal gciWinner gciLoser θ ∨
  componentReversal aempWinner aempLoser θ

/-- Post-dictamen θ-audit. The maximum active component controls only the log;
the final winner is reversed whenever at least one component is active. -/
noncomputable def applyStabilityAudit
    (provisional : BinaryChoice)
    (sdeWinner sdeLoser gciWinner gciLoser aempWinner aempLoser θ : ℝ) :
    BinaryChoice := by
  classical
  exact
    if stabilityReversal sdeWinner sdeLoser gciWinner gciLoser
        aempWinner aempLoser θ then
      match provisional with
      | BinaryChoice.first => BinaryChoice.second
      | BinaryChoice.second => BinaryChoice.first
    else provisional

theorem applyStabilityAudit_deterministic
    (provisional : BinaryChoice)
    (sdeWinner sdeLoser gciWinner gciLoser aempWinner aempLoser θ : ℝ) :
    ∃! c : BinaryChoice,
      applyStabilityAudit provisional sdeWinner sdeLoser gciWinner gciLoser
        aempWinner aempLoser θ = c :=
  ⟨_, rfl, fun _ h => h.symm⟩

/-! ## Line-B operational observables -/

/-- `ψ_G` as evaluated by `StructuralMetricsEngine.compute_psi_metrics`. -/
def ψ_G (maeVal maeTrain mseVal mseTrain ε : ℝ) : ℝ :=
  Real.sqrt ((maeVal / (maeTrain + ε)) *
    (Real.sqrt mseVal / Real.sqrt (mseTrain + ε)))

/-- Product beneath the Python cube root in the ICV definition. -/
def icvProduct (ψRatio sdeRatio eRatio : ℝ) : ℝ :=
  ψRatio * sdeRatio * eRatio

/-- Real-valued counterpart of `np.cbrt(max(product, 0.0))`. -/
def icvScore (ψRatio sdeRatio eRatio : ℝ) : ℝ :=
  Real.rpow (max (icvProduct ψRatio sdeRatio eRatio) 0) (1 / 3)

inductive LineBReferenceVerdict
  | full | trainOnly | retrainOnly | none
  deriving Repr, DecidableEq

def classifyLineBReferences (beatsTrain beatsRetrain : Bool) :
    LineBReferenceVerdict :=
  match beatsTrain, beatsRetrain with
  | true, true => LineBReferenceVerdict.full
  | true, false => LineBReferenceVerdict.trainOnly
  | false, true => LineBReferenceVerdict.retrainOnly
  | false, false => LineBReferenceVerdict.none

theorem classifyLineBReferences_deterministic (beatsTrain beatsRetrain : Bool) :
    ∃! v : LineBReferenceVerdict,
      classifyLineBReferences beatsTrain beatsRetrain = v :=
  ⟨_, rfl, fun _ h => h.symm⟩

inductive VBDVerdict
  | stable | fragile | conditional | diagnostic
  deriving Repr, DecidableEq

/-- Exact strict/non-strict boundaries of the Python VBD classifier.
`icvStrong`, `icvConditional` and `psiRankMin` instantiate respectively to
`1.0`, `0.85` and `0.5`. -/
def classifyVBD
    (icv psiRank icvStrong icvConditional psiRankMin : ℝ)
    (psiRankActive : Bool) : VBDVerdict :=
  if icv > icvStrong then
    if psiRankActive then
      if psiRank ≥ psiRankMin then VBDVerdict.stable else VBDVerdict.fragile
    else VBDVerdict.stable
  else if icv > icvConditional then VBDVerdict.conditional
  else VBDVerdict.diagnostic

theorem classifyVBD_deterministic
    (icv psiRank icvStrong icvConditional psiRankMin : ℝ)
    (psiRankActive : Bool) :
    ∃! v : VBDVerdict,
      classifyVBD icv psiRank icvStrong icvConditional psiRankMin
        psiRankActive = v :=
  ⟨_, rfl, fun _ h => h.symm⟩

def VBDVerdict.promotable : VBDVerdict → Bool
  | VBDVerdict.stable => true
  | VBDVerdict.fragile => true
  | VBDVerdict.conditional => true
  | VBDVerdict.diagnostic => false

/-- Python's `promoted_once` guard: at most one twin can be promoted. -/
def shouldPromote (verdict : VBDVerdict) (alreadyPromoted : Bool) : Bool :=
  verdict.promotable && !alreadyPromoted

theorem no_second_promotion (verdict : VBDVerdict) :
    shouldPromote verdict true = false := by
  cases verdict <;> rfl

end

end DGDTL_LTS.Operational
