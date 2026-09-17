-- SPDX-FileCopyrightText: 2026 José A. Pérez
-- SPDX-License-Identifier: MIT

-- ==============================================================================
-- FILE: DGDTL/Protocol/StructuralSelection.lean
-- OBJECTIVE: Formal Properties of the Structural Selection Protocol
-- REFERENCE: Section 3.8, Supplementary Information (DGDTL-LTS)
-- ==============================================================================

import Mathlib.Data.Real.Basic
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Tactic

open Classical

/-!
# DGDTL-LTS — Structural Selection Protocol

Formal support in Lean 4 / Mathlib for the Formal Properties of the
Structural Selection Protocol (Supplementary Information, Section 3.8
and related components: MSE Tail Guardrail §3.3, Phase 3 §3.5, Line B
§3.6, Phase 4 §3.7, Prop. 2.1/2.11 §2).

Step 3a (inter-scout tie-break via U_comp), the post-dictamen stability
audit, and the operational ψ_G/ICV/VBD rules are formalized in the companion
module `ProtocolOperational.lean`. Prop. 3.9 (OOD certification) remains an
epistemological interpretation of the deterministic Phase-4 verdict.
-/

namespace DGDTL_LTS

-- Disable the unused variables warning to strictly preserve exact signatures
set_option linter.unusedVariables false

/-! ## Phase 1 (Definition 3.2, Proposition 3.10 / 3.13(i)) -/

section Phase1

inductive Phase1Verdict
  | TEQ | JDC | IRF | SDI | STP | GTR
  deriving Repr, DecidableEq

def isTEQ (dU_abs dφ ε_F : ℝ) : Prop := |dU_abs| < ε_F ∧ |dφ| < ε_F
def isJDC (dU_abs dφ ε_F : ℝ) : Prop :=
  ¬isTEQ dU_abs dφ ε_F ∧ dU_abs < -ε_F ∧ dφ < -ε_F
def isIRF (dU_abs dφ ε_F : ℝ) : Prop :=
  ¬isTEQ dU_abs dφ ε_F ∧ dU_abs < -ε_F ∧ dφ ≥ -ε_F
def isSDI (dU_abs dφ ε_F θ_adp : ℝ) : Prop :=
  ¬isTEQ dU_abs dφ ε_F ∧ dU_abs ≥ -ε_F ∧ dφ < -θ_adp
def isSTP (dU_abs dU_rel dφ ε_F θ_adp ε_tie : ℝ) : Prop :=
  ¬isTEQ dU_abs dφ ε_F ∧ dU_abs ≥ -ε_F ∧ dφ ≥ -θ_adp ∧
    (0 ≤ dU_rel ∧ dU_rel < ε_tie ∧ dφ < 0)
def isGTR (dU_abs dU_rel dφ ε_F θ_adp ε_tie : ℝ) : Prop :=
  ¬isTEQ dU_abs dφ ε_F ∧ dU_abs ≥ -ε_F ∧ dφ ≥ -θ_adp ∧
    ¬(0 ≤ dU_rel ∧ dU_rel < ε_tie ∧ dφ < 0)

/-- Exact relative increment used by `u_maxp_core.py` in the STP gate. -/
noncomputable def phase1RelativeIncrement (U_A U_B ε_num : ℝ) : ℝ :=
  (U_B - U_A) / (|U_A| + ε_num)

/--
Supplementary Definition 3.2: Topological Step Acceptance Criterion.
Maps perfectly to the logical structure of Table S1.
-/
noncomputable def classifyPhase1
    (dU_abs dU_rel dφ ε_F θ_adp ε_tie : ℝ) : Phase1Verdict :=
  if |dU_abs| < ε_F ∧ |dφ| < ε_F then Phase1Verdict.TEQ
  else if dU_abs < -ε_F ∧ dφ < -ε_F then Phase1Verdict.JDC
  else if dU_abs < -ε_F ∧ dφ ≥ -ε_F then Phase1Verdict.IRF
  else if dU_abs ≥ -ε_F ∧ dφ < -θ_adp then Phase1Verdict.SDI
  else if dU_abs ≥ -ε_F ∧ dφ ≥ -θ_adp ∧
      (0 ≤ dU_rel ∧ dU_rel < ε_tie ∧ dφ < 0) then Phase1Verdict.STP
  else Phase1Verdict.GTR

/-- Python-level binding: absolute and relative increments are derived from the
same pair `(U_A, U_B)`, with the numerical denominator stabilizer explicit. -/
noncomputable def classifyPhase1Python
    (U_A U_B dφ ε_num ε_F θ_adp ε_tie : ℝ) : Phase1Verdict :=
  classifyPhase1 (U_B - U_A) (phase1RelativeIncrement U_A U_B ε_num)
    dφ ε_F θ_adp ε_tie

theorem phase1_python_binding_deterministic
    (U_A U_B dφ ε_num ε_F θ_adp ε_tie : ℝ) :
    ∃! v : Phase1Verdict,
      classifyPhase1Python U_A U_B dφ ε_num ε_F θ_adp ε_tie = v :=
  ⟨_, rfl, fun _ hy => hy.symm⟩

theorem phase1_deterministic (dU_abs dU_rel dφ ε_F θ_adp ε_tie : ℝ) :
    ∃! v : Phase1Verdict,
      classifyPhase1 dU_abs dU_rel dφ ε_F θ_adp ε_tie = v :=
  ⟨_, rfl, fun _ hy => hy.symm⟩

lemma teq_excludes_all (dU_abs dU_rel dφ ε_F θ_adp ε_tie : ℝ)
    (hTEQ : isTEQ dU_abs dφ ε_F) :
    ¬isJDC dU_abs dφ ε_F ∧ ¬isIRF dU_abs dφ ε_F ∧
    ¬isSDI dU_abs dφ ε_F θ_adp ∧
    ¬isSTP dU_abs dU_rel dφ ε_F θ_adp ε_tie ∧
    ¬isGTR dU_abs dU_rel dφ ε_F θ_adp ε_tie :=
  ⟨fun h => h.1 hTEQ, fun h => h.1 hTEQ, fun h => h.1 hTEQ,
   fun h => h.1 hTEQ, fun h => h.1 hTEQ⟩

lemma jdc_excludes_rest (dU_abs dU_rel dφ ε_F θ_adp ε_tie : ℝ)
    (hJDC : isJDC dU_abs dφ ε_F) :
    ¬isIRF dU_abs dφ ε_F ∧ ¬isSDI dU_abs dφ ε_F θ_adp ∧
    ¬isSTP dU_abs dU_rel dφ ε_F θ_adp ε_tie ∧
    ¬isGTR dU_abs dU_rel dφ ε_F θ_adp ε_tie := by
  refine ⟨?_, ?_, ?_, ?_⟩
  · intro h; linarith [h.2.2, hJDC.2.2]
  · intro h; linarith [h.2.1, hJDC.2.1]
  · intro h; linarith [h.2.1, hJDC.2.1]
  · intro h; linarith [h.2.1, hJDC.2.1]

lemma irf_excludes_rest (dU_abs dU_rel dφ ε_F θ_adp ε_tie : ℝ)
    (hIRF : isIRF dU_abs dφ ε_F) :
    ¬isSDI dU_abs dφ ε_F θ_adp ∧
    ¬isSTP dU_abs dU_rel dφ ε_F θ_adp ε_tie ∧
    ¬isGTR dU_abs dU_rel dφ ε_F θ_adp ε_tie := by
  refine ⟨?_, ?_, ?_⟩
  · intro h; linarith [h.2.1, hIRF.2.1]
  · intro h; linarith [h.2.1, hIRF.2.1]
  · intro h; linarith [h.2.1, hIRF.2.1]

lemma sdi_excludes_rest (dU_abs dU_rel dφ ε_F θ_adp ε_tie : ℝ)
    (hSDI : isSDI dU_abs dφ ε_F θ_adp) :
    ¬isSTP dU_abs dU_rel dφ ε_F θ_adp ε_tie ∧
    ¬isGTR dU_abs dU_rel dφ ε_F θ_adp ε_tie := by
  refine ⟨?_, ?_⟩
  · intro h; linarith [h.2.2.1, hSDI.2.2]
  · intro h; linarith [h.2.2.1, hSDI.2.2]

lemma stp_excludes_gtr (dU_abs dU_rel dφ ε_F θ_adp ε_tie : ℝ)
    (hSTP : isSTP dU_abs dU_rel dφ ε_F θ_adp ε_tie) :
    ¬isGTR dU_abs dU_rel dφ ε_F θ_adp ε_tie :=
  fun hGTR => hGTR.2.2.2 hSTP.2.2.2

lemma phase1_exhaustive (dU_abs dU_rel dφ ε_F θ_adp ε_tie : ℝ) :
    isTEQ dU_abs dφ ε_F ∨ isJDC dU_abs dφ ε_F ∨
    isIRF dU_abs dφ ε_F ∨ isSDI dU_abs dφ ε_F θ_adp ∨
    isSTP dU_abs dU_rel dφ ε_F θ_adp ε_tie ∨
    isGTR dU_abs dU_rel dφ ε_F θ_adp ε_tie := by
  by_cases h1 : isTEQ dU_abs dφ ε_F
  · exact Or.inl h1
  · right
    by_cases h2 : dU_abs < -ε_F
    · by_cases h3 : dφ < -ε_F
      · exact Or.inl ⟨h1, h2, h3⟩
      · exact Or.inr (Or.inl ⟨h1, h2, by linarith⟩)
    · right; right
      have h2' : dU_abs ≥ -ε_F := by linarith
      by_cases h4 : dφ < -θ_adp
      · exact Or.inl ⟨h1, h2', h4⟩
      · right
        have h4' : dφ ≥ -θ_adp := by linarith
        by_cases h5 : 0 ≤ dU_rel ∧ dU_rel < ε_tie ∧ dφ < 0
        · exact Or.inl ⟨h1, h2', h4', h5⟩
        · exact Or.inr ⟨h1, h2', h4', h5⟩

/--
SUPPLEMENTARY PROPOSITION 3.10: Combinatorial completeness of Phase 1.
Exhaustive and mutually exclusive partition mapping all six states.
-/
theorem phase1_complete_partition (dU_abs dU_rel dφ ε_F θ_adp ε_tie : ℝ) :
    (isTEQ dU_abs dφ ε_F ∧ ¬isJDC dU_abs dφ ε_F ∧
      ¬isIRF dU_abs dφ ε_F ∧ ¬isSDI dU_abs dφ ε_F θ_adp ∧
      ¬isSTP dU_abs dU_rel dφ ε_F θ_adp ε_tie ∧
      ¬isGTR dU_abs dU_rel dφ ε_F θ_adp ε_tie) ∨
    (isJDC dU_abs dφ ε_F ∧ ¬isTEQ dU_abs dφ ε_F ∧
      ¬isIRF dU_abs dφ ε_F ∧ ¬isSDI dU_abs dφ ε_F θ_adp ∧
      ¬isSTP dU_abs dU_rel dφ ε_F θ_adp ε_tie ∧
      ¬isGTR dU_abs dU_rel dφ ε_F θ_adp ε_tie) ∨
    (isIRF dU_abs dφ ε_F ∧ ¬isTEQ dU_abs dφ ε_F ∧
      ¬isJDC dU_abs dφ ε_F ∧ ¬isSDI dU_abs dφ ε_F θ_adp ∧
      ¬isSTP dU_abs dU_rel dφ ε_F θ_adp ε_tie ∧
      ¬isGTR dU_abs dU_rel dφ ε_F θ_adp ε_tie) ∨
    (isSDI dU_abs dφ ε_F θ_adp ∧ ¬isTEQ dU_abs dφ ε_F ∧
      ¬isJDC dU_abs dφ ε_F ∧ ¬isIRF dU_abs dφ ε_F ∧
      ¬isSTP dU_abs dU_rel dφ ε_F θ_adp ε_tie ∧
      ¬isGTR dU_abs dU_rel dφ ε_F θ_adp ε_tie) ∨
    (isSTP dU_abs dU_rel dφ ε_F θ_adp ε_tie ∧
      ¬isTEQ dU_abs dφ ε_F ∧ ¬isJDC dU_abs dφ ε_F ∧
      ¬isIRF dU_abs dφ ε_F ∧ ¬isSDI dU_abs dφ ε_F θ_adp ∧
      ¬isGTR dU_abs dU_rel dφ ε_F θ_adp ε_tie) ∨
    (isGTR dU_abs dU_rel dφ ε_F θ_adp ε_tie ∧
      ¬isTEQ dU_abs dφ ε_F ∧ ¬isJDC dU_abs dφ ε_F ∧
      ¬isIRF dU_abs dφ ε_F ∧ ¬isSDI dU_abs dφ ε_F θ_adp ∧
      ¬isSTP dU_abs dU_rel dφ ε_F θ_adp ε_tie) := by
  rcases phase1_exhaustive dU_abs dU_rel dφ ε_F θ_adp ε_tie with
    hTEQ | hJDC | hIRF | hSDI | hSTP | hGTR
  · left
    have hExcl := teq_excludes_all dU_abs dU_rel dφ ε_F θ_adp ε_tie hTEQ
    exact ⟨hTEQ, hExcl.1, hExcl.2.1, hExcl.2.2.1, hExcl.2.2.2.1, hExcl.2.2.2.2⟩
  · right; left
    have hExcl := jdc_excludes_rest dU_abs dU_rel dφ ε_F θ_adp ε_tie hJDC
    exact ⟨hJDC, hJDC.1, hExcl.1, hExcl.2.1, hExcl.2.2.1, hExcl.2.2.2⟩
  · right; right; left
    have hExcl := irf_excludes_rest dU_abs dU_rel dφ ε_F θ_adp ε_tie hIRF
    have hNotJDC : ¬isJDC dU_abs dφ ε_F := by intro h; linarith [h.2.2, hIRF.2.2]
    exact ⟨hIRF, hIRF.1, hNotJDC, hExcl.1, hExcl.2.1, hExcl.2.2⟩
  · right; right; right; left
    have hExcl := sdi_excludes_rest dU_abs dU_rel dφ ε_F θ_adp ε_tie hSDI
    have hNotJDC : ¬isJDC dU_abs dφ ε_F := by intro h; linarith [h.2.1, hSDI.2.1]
    have hNotIRF : ¬isIRF dU_abs dφ ε_F := by intro h; linarith [h.2.1, hSDI.2.1]
    exact ⟨hSDI, hSDI.1, hNotJDC, hNotIRF, hExcl.1, hExcl.2⟩
  · right; right; right; right; left
    have hExcl := stp_excludes_gtr dU_abs dU_rel dφ ε_F θ_adp ε_tie hSTP
    have hNotJDC : ¬isJDC dU_abs dφ ε_F := by intro h; linarith [h.2.1, hSTP.2.1]
    have hNotIRF : ¬isIRF dU_abs dφ ε_F := by intro h; linarith [h.2.1, hSTP.2.1]
    have hNotSDI : ¬isSDI dU_abs dφ ε_F θ_adp := by intro h; linarith [h.2.2, hSTP.2.2.1]
    exact ⟨hSTP, hSTP.1, hNotJDC, hNotIRF, hNotSDI, hExcl⟩
  · right; right; right; right; right
    have hNotJDC : ¬isJDC dU_abs dφ ε_F := by intro h; linarith [h.2.1, hGTR.2.1]
    have hNotIRF : ¬isIRF dU_abs dφ ε_F := by intro h; linarith [h.2.1, hGTR.2.1]
    have hNotSDI : ¬isSDI dU_abs dφ ε_F θ_adp := by intro h; linarith [h.2.2, hGTR.2.2.1]
    have hNotSTP : ¬isSTP dU_abs dU_rel dφ ε_F θ_adp ε_tie :=
      fun h => hGTR.2.2.2 h.2.2.2
    exact ⟨hGTR, hGTR.1, hNotJDC, hNotIRF, hNotSDI, hNotSTP⟩

/--
SUPPLEMENTARY PROPOSITION 3.13 (i):
If refinement is accepted (GTR), then U-MaxP(B) ≥ U-MaxP(A) - ε_F.
-/
theorem gtr_lower_bound (dU_abs dU_rel dφ ε_F θ_adp ε_tie : ℝ)
    (h : isGTR dU_abs dU_rel dφ ε_F θ_adp ε_tie) : dU_abs ≥ -ε_F :=
  h.2.1

end Phase1

/-! ## Phase 2 (Def. 3.3, Prop. 3.11 / 3.13(ii) / 3.15) and Accessibility of F2.1/F2.2-RT -/

section Phase2

inductive Phase2Verdict
  | BND | SPT | TRG | STD | ISI
  deriving Repr, DecidableEq

/--
Supplementary Definition 3.3: Absolute Structural Integrity Filter.
Maps perfectly to Table S2.
-/
noncomputable def classifyPhase2 (U_C U_B : ℝ) (I G : Bool) : Phase2Verdict :=
  if U_C ≤ U_B then Phase2Verdict.BND
  else match I, G with
    | true, false  => Phase2Verdict.SPT
    | true, true   => Phase2Verdict.TRG
    | false, true  => Phase2Verdict.STD
    | false, false => Phase2Verdict.ISI

theorem phase2_deterministic (U_C U_B : ℝ) (I G : Bool) :
    ∃! v : Phase2Verdict, classifyPhase2 U_C U_B I G = v :=
  ⟨_, rfl, fun _ hy => hy.symm⟩

/--
SUPPLEMENTARY PROPOSITION 3.13 (ii):
The champion only wins (verdict ≠ BND) if U-MaxP(C) > U-MaxP(B).
-/
theorem phase2_winner_dominates (U_C U_B : ℝ) (I G : Bool)
    (h : classifyPhase2 U_C U_B I G ≠ Phase2Verdict.BND) : U_C > U_B := by
  by_contra hle
  have hle_le : U_C ≤ U_B := not_lt.mp hle
  apply h
  unfold classifyPhase2
  rw [if_pos hle_le]

/--
SUPPLEMENTARY PROPOSITION 3.15: Coherence with Strict Mode criterion.
C wins with TRG or STD if and only if U-MaxP(C) > U-MaxP(B) and G(C) = V.
-/
theorem hardmode_coherence (U_C U_B : ℝ) (I G : Bool) :
    (classifyPhase2 U_C U_B I G = Phase2Verdict.TRG ∨
     classifyPhase2 U_C U_B I G = Phase2Verdict.STD)
    ↔ (U_C > U_B ∧ G = true) := by
  unfold classifyPhase2
  split_ifs with hle
  · constructor
    · rintro (h | h) <;> exact absurd h (by decide)
    · rintro ⟨hgt, -⟩
      exact absurd hgt (not_lt.mpr hle)
  · have hgt : U_C > U_B := not_le.mp hle
    cases I <;> cases G
    · constructor
      · rintro (h | h) <;> exact absurd h (by decide)
      · rintro ⟨-, hG⟩; exact absurd hG (by decide)
    · constructor
      · intro _; exact ⟨hgt, rfl⟩
      · intro _; right; rfl
    · constructor
      · rintro (h | h) <;> exact absurd h (by decide)
      · rintro ⟨-, hG⟩; exact absurd hG (by decide)
    · constructor
      · intro _; exact ⟨hgt, rfl⟩
      · intro _; left; rfl

/--
SUPPLEMENTARY PROPOSITION 3.19:
F2.1 is algebraically impossible if ratio_ref > 1.
-/
theorem f21_impossible (e_tr e_val ratio_ref ε_F : ℝ)
    (h_I : e_tr > e_val) (h_G : e_val / e_tr > ratio_ref + ε_F)
    (h_eps : ε_F ≥ 0) (h_etr : e_tr > 0) (h_ratio : ratio_ref > 1) : False := by
  have h_ratio_lt_one : e_val / e_tr < 1 := (div_lt_one h_etr).mpr h_I
  linarith

/--
SUPPLEMENTARY LEMMA 3.1: Structural contraction of U-MaxP.
U-MaxP^(κ)(M) ≤ U-RAW(M) for all models M, given A_emp(M), κ(M) ∈ (0,1].
-/
theorem umaxp_kappa_leq_uraw (U_RAW A_emp κ : ℝ)
    (hURaw : 0 < U_RAW)
    (_hAemp0 : 0 < A_emp) (hAemp1 : A_emp ≤ 1)
    (hKappa0 : 0 < κ) (hKappa1 : κ ≤ 1) :
    U_RAW * A_emp * κ ≤ U_RAW := by
  have hProd : A_emp * κ ≤ 1 := by
    have step1 : A_emp * κ ≤ 1 * κ :=
      mul_le_mul_of_nonneg_right hAemp1 hKappa0.le
    have step2 : (1 : ℝ) * κ ≤ 1 := by linarith
    linarith [step1, step2]
  calc U_RAW * A_emp * κ = U_RAW * (A_emp * κ) := by ring
    _ ≤ U_RAW * 1 := mul_le_mul_of_nonneg_left hProd hURaw.le
    _ = U_RAW := by ring

/--
SUPPLEMENTARY PROPOSITION 3.20:
Algebraic inaccessibility of F2.2-RT under the formulation of U-MaxP^(κ).
-/
theorem f22rt_inaccessible
    (UMaxP_C URaw_ret Aemp_ret kappa_ret : ℝ)
    (h_C_beats_ret : UMaxP_C > URaw_ret)
    (h_ret_beats_C : URaw_ret * Aemp_ret * kappa_ret > UMaxP_C)
    (hURaw_ret : 0 < URaw_ret)
    (hAemp0 : 0 < Aemp_ret) (hAemp1 : Aemp_ret ≤ 1)
    (hKappa0 : 0 < kappa_ret) (hKappa1 : kappa_ret ≤ 1) :
    False := by
  have h_contraction : URaw_ret * Aemp_ret * kappa_ret ≤ URaw_ret :=
    umaxp_kappa_leq_uraw URaw_ret Aemp_ret kappa_ret hURaw_ret hAemp0 hAemp1 hKappa0 hKappa1
  linarith [h_contraction, h_ret_beats_C, h_C_beats_ret]

end Phase2

/-! ## Invariance and Ranking (Proposition 3.14) -/

section InvarianceAndRanking

theorem multiplicative_ratio_invariance (x y a : ℝ) (ha_ne : a ≠ 0) :
    (a * x) / (a * y) = x / y :=
  mul_div_mul_left x y ha_ne

theorem scale_preserves_inequality (x y a : ℝ) (ha : a > 0) :
    (a * x < a * y) ↔ (x < y) :=
  ⟨fun h => lt_of_mul_lt_mul_left h (le_of_lt ha),
   fun h => mul_lt_mul_of_pos_left h ha⟩

variable (U_C1 U_C2 ε_tie : ℝ)

theorem strict_ranking_consistency (h_gap : U_C1 - U_C2 > ε_tie * U_C1) :
    ¬ (U_C1 - U_C2 ≤ ε_tie * U_C1) := by
  linarith

/--
SUPPLEMENTARY PROPOSITION 3.14: Global monotonicity of the protocol.
A large margin implies C1 numerically dominates, circumventing Phase 3 arbitration.
-/
theorem global_monotonicity_core
    (h_eps_nonneg : 0 ≤ ε_tie)
    (h_U1_pos : 0 < U_C1)
    (h_gap : U_C1 - U_C2 > ε_tie * U_C1) :
    U_C1 > U_C2 ∧ ¬ (U_C1 - U_C2 ≤ ε_tie * U_C1) := by
  constructor
  · linarith [mul_nonneg h_eps_nonneg h_U1_pos.le]
  · exact strict_ranking_consistency U_C1 U_C2 ε_tie h_gap

end InvarianceAndRanking

/-! ## Supplementary Proposition 3.16 (Retrain Asymmetry) -/

section RetrainAsymmetry

/-- Cauchy balance factor φ(ρ) = 2ρ/(1+ρ²) (Eq. S38). -/
noncomputable def φ (ρ : ℝ) : ℝ := (2 * ρ) / (1 + ρ ^ 2)

theorem φ_bounded {ρ : ℝ} (hρ : 0 < ρ) : 0 < φ ρ ∧ φ ρ ≤ 1 := by
  unfold φ
  have h_num : 0 < 2 * ρ := mul_pos zero_lt_two hρ
  have h_den : 0 < 1 + ρ ^ 2 := by positivity
  constructor
  · exact div_pos h_num h_den
  · have h_sq : 0 ≤ (1 - ρ) ^ 2 := sq_nonneg (1 - ρ)
    have h_ineq : 2 * ρ ≤ 1 + ρ ^ 2 := by nlinarith [h_sq]
    exact (div_le_one h_den).mpr h_ineq

theorem φ_eq_one_iff {ρ : ℝ} (hρ : 0 < ρ) : φ ρ = 1 ↔ ρ = 1 := by
  unfold φ
  have hden : 0 < 1 + ρ ^ 2 := by positivity
  constructor
  · intro h
    have hcross : 2 * ρ = 1 + ρ ^ 2 := by
      have := congrArg (fun x => x * (1 + ρ ^ 2)) h
      field_simp [hden.ne'] at this
      simpa using this
    have hsq : (ρ - 1) ^ 2 = 0 := by nlinarith [hcross]
    nlinarith
  · intro h; subst h; norm_num

/--
SUPPLEMENTARY PROPOSITION 3.16(iii):
In symmetric domains, φ(M_ret) evaluates to exactly 1.
-/
theorem retrain_phi_eq_one_iff_symmetric
    {ratio_ref : ℝ} (h_pos : 0 < ratio_ref) :
    φ (1 / ratio_ref) = 1 ↔ ratio_ref = 1 := by
  have hρ_pos : 0 < 1 / ratio_ref := one_div_pos.mpr h_pos
  rw [φ_eq_one_iff hρ_pos]
  constructor
  · intro h; field_simp [h_pos.ne'] at h; linarith
  · intro h; rw [h]; norm_num

/--
SUPPLEMENTARY PROPOSITION 3.16(iv):
In asymmetric domains, φ(M_ret) < 1 constitutes a genuine topological signal.
-/
theorem retrain_phi_lt_one_of_asymmetric
    {ratio_ref : ℝ} (h_pos : 0 < ratio_ref) (h_ne : ratio_ref ≠ 1) :
    φ (1 / ratio_ref) < 1 := by
  have hρ_pos : 0 < 1 / ratio_ref := one_div_pos.mpr h_pos
  have hle : φ (1 / ratio_ref) ≤ 1 := (φ_bounded hρ_pos).2
  have hne : φ (1 / ratio_ref) ≠ 1 := by
    intro h; exact h_ne ((retrain_phi_eq_one_iff_symmetric h_pos).mp h)
  exact lt_of_le_of_ne hle hne

end RetrainAsymmetry

/-! ## Supplementary Proposition 3.18 (Protocol Adimensionality) -/

section ScaleInvariance

theorem residual_rescale (y yhat c : ℝ) :
    |c * y - c * yhat| = |c| * |y - yhat| := by
  rw [← mul_sub, abs_mul]

theorem residual_shift_invariant (y yhat b : ℝ) :
    (y + b) - (yhat + b) = y - yhat := by ring

theorem residual_scale (y yhat a b : ℝ) :
    |(a * y + b) - (a * yhat + b)| = |a| * |y - yhat| := by
  rw [residual_shift_invariant, ← mul_sub, abs_mul]

theorem residual_ratio_scale_invariant
    (y1 yhat1 y2 yhat2 a b : ℝ) (ha : a ≠ 0) :
    |(a * y2 + b) - (a * yhat2 + b)| / |(a * y1 + b) - (a * yhat1 + b)|
    = |y2 - yhat2| / |y1 - yhat1| := by
  rw [residual_scale, residual_scale]
  exact multiplicative_ratio_invariance |y2 - yhat2| |y1 - yhat1| |a| (abs_ne_zero.mpr ha)

noncomputable def trainingMAE (n : ℕ) (y yhat : Fin n → ℝ) : ℝ :=
  (1 / (n : ℝ)) * Finset.sum Finset.univ (fun i => |y i - yhat i|)

noncomputable def trainingMSE (n : ℕ) (y yhat : Fin n → ℝ) : ℝ :=
  (1 / (n : ℝ)) * Finset.sum Finset.univ (fun i => (y i - yhat i) ^ 2)

/--
SUPPLEMENTARY PROPOSITION 2.1: Non-invariance of the absolute gap.
Constructive proof for Mean Absolute Error (MAE).
-/
theorem mae_rescale (n : ℕ) (y yhat : Fin n → ℝ) (c : ℝ) :
    trainingMAE n (fun i => c * y i) (fun i => c * yhat i) = |c| * trainingMAE n y yhat := by
  unfold trainingMAE
  have step : ∀ i, |c * y i - c * yhat i| = |c| * |y i - yhat i| :=
    fun i => residual_rescale (y i) (yhat i) c
  simp_rw [step]
  rw [← Finset.mul_sum]
  ring

theorem mae_scale_invariant (n : ℕ) (y yhat : Fin n → ℝ) (a b : ℝ) :
    trainingMAE n (fun i => a * y i + b) (fun i => a * yhat i + b) = |a| * trainingMAE n y yhat := by
  unfold trainingMAE
  have step : ∀ i, |a * y i + b - (a * yhat i + b)| = |a| * |y i - yhat i| :=
    fun i => residual_scale (y i) (yhat i) a b
  simp_rw [step]
  rw [← Finset.mul_sum]
  ring

theorem mse_scale_invariant (n : ℕ) (y yhat : Fin n → ℝ) (a b : ℝ) :
    trainingMSE n (fun i => a * y i + b) (fun i => a * yhat i + b) = a ^ 2 * trainingMSE n y yhat := by
  unfold trainingMSE
  have step : ∀ i, (a * y i + b - (a * yhat i + b)) ^ 2 = a ^ 2 * (y i - yhat i) ^ 2 := by
    intro i
    have h : a * y i + b - (a * yhat i + b) = a * (y i - yhat i) := by ring
    rw [h]; ring
  simp_rw [step]
  rw [← Finset.mul_sum]
  ring

theorem gap_rescale (n m : ℕ) (ytr yhattr : Fin n → ℝ) (yte yhatte : Fin m → ℝ) (c : ℝ) :
    trainingMAE m (fun i => c * yte i) (fun i => c * yhatte i)
      - trainingMAE n (fun i => c * ytr i) (fun i => c * yhattr i)
    = |c| * (trainingMAE m yte yhatte - trainingMAE n ytr yhattr) := by
  rw [mae_rescale, mae_rescale]
  ring

/--
SUPPLEMENTARY PROPOSITION 3.18:
ΔU-MaxP, Δφ, δ_E, and Ψ are ratios of homogeneous errors ⟹ invariant under y ↦ ay + b.
-/
theorem error_ratio_scale_invariant_MAE
    (n m : ℕ) (y1 yhat1 : Fin n → ℝ) (y2 yhat2 : Fin m → ℝ) (a b : ℝ) (ha : a ≠ 0) :
    trainingMAE m (fun i => a * y2 i + b) (fun i => a * yhat2 i + b) /
    trainingMAE n (fun i => a * y1 i + b) (fun i => a * yhat1 i + b)
    = trainingMAE m y2 yhat2 / trainingMAE n y1 yhat1 := by
  rw [mae_scale_invariant, mae_scale_invariant]
  exact multiplicative_ratio_invariance (trainingMAE m y2 yhat2) (trainingMAE n y1 yhat1) |a|
    (abs_ne_zero.mpr ha)

theorem error_ratio_scale_invariant_MSE
    (n m : ℕ) (y1 yhat1 : Fin n → ℝ) (y2 yhat2 : Fin m → ℝ) (a b : ℝ) (ha : a ≠ 0) :
    trainingMSE m (fun i => a * y2 i + b) (fun i => a * yhat2 i + b) /
    trainingMSE n (fun i => a * y1 i + b) (fun i => a * yhat1 i + b)
    = trainingMSE m y2 yhat2 / trainingMSE n y1 yhat1 := by
  rw [mse_scale_invariant, mse_scale_invariant]
  exact multiplicative_ratio_invariance (trainingMSE m y2 yhat2) (trainingMSE n y1 yhat1) (a ^ 2)
    (pow_ne_zero 2 ha)

end ScaleInvariance

/-! ## Phase 3 (Definition 3.6, Proposition 3.4/3.17) -/

section Phase3

/-- Equation (S66): Incoherence-Penalized Error. -/
noncomputable def E_inc (e_val e_tr φ : ℝ) : ℝ :=
  Real.sqrt (e_val * e_tr) * (1 - φ)

/-- Equation (S68): Hyperbolic Tail Factor. -/
noncomputable def H_factor (Φ_emp ε : ℝ) : ℝ :=
  (1 - Φ_emp) / (Φ_emp + ε)

/-- Equation (S67), represented as a fraction exactly as in `u_maxp_core.py`.
The manuscript's multiplication by `100%` is a display conversion only. -/
noncomputable def δ_E (E1 E2 ε : ℝ) : ℝ :=
  (max E1 E2 - min E1 E2) / (min E1 E2 + ε)

/-- Percentage display of `δ_E`; this quantity is not used in the gate. -/
noncomputable def δ_E_percent (E1 E2 ε : ℝ) : ℝ :=
  100 * δ_E E1 E2 ε

theorem δ_E_percent_is_display_conversion (E1 E2 ε : ℝ) :
    δ_E_percent E1 E2 ε = 100 * δ_E E1 E2 ε := rfl

/-- Exact directional concordance predicate used by the Python implementation.
Equality is deliberately resolved in favor of Run 1; Run 2 must improve both
components strictly to activate its concordant branch. -/
def sameArgmaxφΦemp (φ1 φ2 Φemp1 Φemp2 : ℝ) : Prop :=
  (φ2 > φ1 ∧ Φemp2 > Φemp1) ∨ (φ1 ≥ φ2 ∧ Φemp1 ≥ Φemp2)

def evtIndifferent (Φemp1 Φemp2 ε : ℝ) : Prop :=
  |Φemp1 - Φemp2| < ε

def concordancePhase3 (φ1 φ2 Φemp1 Φemp2 ε : ℝ) : Prop :=
  sameArgmaxφΦemp φ1 φ2 Φemp1 Φemp2 ∨ evtIndifferent Φemp1 Φemp2 ε ∨ (Φemp1 = 0 ∧ Φemp2 = 0)

inductive RunChoice
  | R1 | R2
  deriving Repr, DecidableEq

/--
Supplementary Definition 3.6: Inter-Run Decision Rule by E_inc and Φ_emp.
Operates strictly on the pre-resolved (R1, R2) pair from the same scout (Step 3b);
does not include inter-scout Step 3a.
-/
noncomputable def classifyPhase3
    (E1 E2 φ1 φ2 Φemp1 Φemp2 ε_tie ε : ℝ) : RunChoice :=
  if δ_E E1 E2 ε < ε_tie then
    (if E1 ≤ E2 then RunChoice.R1 else RunChoice.R2)
  else if concordancePhase3 φ1 φ2 Φemp1 Φemp2 ε then
    (if φ1 ≥ φ2 then RunChoice.R1 else RunChoice.R2)
  else
    (if H_factor Φemp1 ε ≤ H_factor Φemp2 ε then RunChoice.R1 else RunChoice.R2)

theorem phase3_deterministic (E1 E2 φ1 φ2 Φemp1 Φemp2 ε_tie ε : ℝ) :
    ∃! r : RunChoice, classifyPhase3 E1 E2 φ1 φ2 Φemp1 Φemp2 ε_tie ε = r :=
  ⟨_, rfl, fun _ hy => hy.symm⟩

end Phase3

/-! ## Phase 4 — Observable Dominance Audit (Definition 3.9, Table S4) -/

section Phase4

inductive Phase4Verdict
  | DAC | DAE | DPO | ROS
  deriving Repr, DecidableEq

/-- Supplementary Definition 3.9: Observable Dominance Audit (Table S4). -/
def classifyPhase4 (IRT JRT : Bool) : Phase4Verdict :=
  match IRT, JRT with
  | true,  true  => Phase4Verdict.DAC
  | true,  false => Phase4Verdict.DAE
  | false, true  => Phase4Verdict.DPO
  | false, false => Phase4Verdict.ROS

theorem phase4_deterministic (IRT JRT : Bool) :
    ∃! v : Phase4Verdict, classifyPhase4 IRT JRT = v :=
  ⟨_, rfl, fun _ hy => hy.symm⟩

end Phase4

/-! ## Line B — F1-VB Activation and Routing (Def 3.7 / 3.8, Prop 3.17) -/

section LineBRouting

noncomputable def log10 (x : ℝ) : ℝ := Real.log x / Real.log 10

/-- Equation (S70): Validation Bias Discriminant. -/
noncomputable def Ψ (ρ_MAE ρ_MSE : ℝ) : ℝ := log10 ρ_MAE * log10 ρ_MSE

def is_SOV (ρ_MAE ρ_MSE : ℝ) : Prop := log10 ρ_MAE < 0 ∧ log10 ρ_MSE < 0
def is_OFT (ρ_MAE ρ_MSE : ℝ) : Prop := log10 ρ_MAE > 0 ∧ log10 ρ_MSE > 0

/-- Supplementary Definition 3.8: F1-VB Activation Condition. -/
def F1_VB_activates
    (ρMAE_star ρMSE_star ρMAE_twin ρMSE_twin UMaxP_star ε_Ψ ε_F : ℝ) : Prop :=
  (Ψ ρMAE_star ρMSE_star > ε_Ψ ∧ is_SOV ρMAE_star ρMSE_star) ∧
  (Ψ ρMAE_twin ρMSE_twin > ε_Ψ ∧ is_OFT ρMAE_twin ρMSE_twin) ∧
  (UMaxP_star > ε_F)

inductive ProtocolRoute
  | LineA | LineB
  deriving Repr, DecidableEq

noncomputable def routeProtocol
    (ρMAE_star ρMSE_star ρMAE_twin ρMSE_twin UMaxP_star ε_Ψ ε_F : ℝ) : ProtocolRoute :=
  if F1_VB_activates ρMAE_star ρMSE_star ρMAE_twin ρMSE_twin UMaxP_star ε_Ψ ε_F
  then ProtocolRoute.LineB
  else ProtocolRoute.LineA

theorem route_deterministic
    (ρMAE_star ρMSE_star ρMAE_twin ρMSE_twin UMaxP_star ε_Ψ ε_F : ℝ) :
    ∃! r : ProtocolRoute,
      routeProtocol ρMAE_star ρMSE_star ρMAE_twin ρMSE_twin UMaxP_star ε_Ψ ε_F = r :=
  ⟨_, rfl, fun _ hy => hy.symm⟩

theorem route_lineB_of_activates
    {ρMAE_star ρMSE_star ρMAE_twin ρMSE_twin UMaxP_star ε_Ψ ε_F : ℝ}
    (h : F1_VB_activates ρMAE_star ρMSE_star ρMAE_twin ρMSE_twin UMaxP_star ε_Ψ ε_F) :
    routeProtocol ρMAE_star ρMSE_star ρMAE_twin ρMSE_twin UMaxP_star ε_Ψ ε_F
      = ProtocolRoute.LineB := by
  unfold routeProtocol; rw [if_pos h]

theorem route_lineA_of_not_activates
    {ρMAE_star ρMSE_star ρMAE_twin ρMSE_twin UMaxP_star ε_Ψ ε_F : ℝ}
    (h : ¬ F1_VB_activates ρMAE_star ρMSE_star ρMAE_twin ρMSE_twin UMaxP_star ε_Ψ ε_F) :
    routeProtocol ρMAE_star ρMSE_star ρMAE_twin ρMSE_twin UMaxP_star ε_Ψ ε_F
      = ProtocolRoute.LineA := by
  unfold routeProtocol; rw [if_neg h]

/--
SUPPLEMENTARY PROPOSITION 3.17:
Line A and Line B decisions are structurally and mathematically mutually exclusive.
-/
theorem route_lineA_ne_lineB
    {ρMAE_star ρMSE_star ρMAE_twin ρMSE_twin UMaxP_star ε_Ψ ε_F : ℝ} :
    ¬ (routeProtocol ρMAE_star ρMSE_star ρMAE_twin ρMSE_twin UMaxP_star ε_Ψ ε_F
        = ProtocolRoute.LineA ∧
       routeProtocol ρMAE_star ρMSE_star ρMAE_twin ρMSE_twin UMaxP_star ε_Ψ ε_F
        = ProtocolRoute.LineB) := by
  intro ⟨hA, hB⟩
  rw [hA] at hB
  exact absurd hB (by decide)

end LineBRouting

end DGDTL_LTS
