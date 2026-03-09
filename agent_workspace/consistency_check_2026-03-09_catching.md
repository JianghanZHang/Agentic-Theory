# Self-Symbolic Consistency Check — catching.tex (post-surgery)

**Date:** 2026-03-09
**Scope:** `appendices/catching.tex` after surgical fix plan (Tasks 1–9)
**Central claim:** λ₁ > 0 (spectral gap) characterizes successful agent control; catching is the topological transition λ₁: 0 → 3 via gripper bang.

---

## Summary

| Category | Count | Details |
|----------|-------|---------|
| LOAD-BEARING tensions | 1 | 0 reinforced, 1 **unresolved**, 0 contradicted |
| STRUCTURAL tensions | 2 | Both noted, non-fatal |
| Time-axis issues | 1 drift, 0 breaking | Sword definition prose imprecision |
| Unresolved confusions | 4 | η logic error, Reach(κ), TM undefined, v_⊥ forward ref |
| Symbolic issues | 0 | All refs, citations, notation clean |

---

## Critical Findings (requires action)

### C1. Compliant springs vs. rigid edges — criterion unstated [LOAD-BEARING, UNRESOLVED]

**Location:** catching.tex:478-480, 422-428

**The claim:** "compliant contact does not constitute a rigid edge" — springs decelerate but don't create graph edges, so λ₁ = 0 during viability window.

**The problem:** The framework's edge definition (calculus.tex:48-60, def:exgraph) says an edge exists "whenever a_i's actuation can affect a_j's state." Spring forces **do** affect the object's state. The qualifier "rigid" appears nowhere in the formal definition. Worse, threebody.tex uses compliant gravitational forces as edges (w_ij = Gm_im_j/||q_i-q_j||³) — compliant forces count as edges there.

**Cross-validation verdict:** UNRESOLVED. The distinction is asserted but not derived from the framework.

**Possible resolutions (not prescriptive):**
- (a) Add a formal criterion in def:exgraph distinguishing rigid constraint edges from compliant force fields
- (b) Admit λ₁ rises continuously through a small value during spring contact, with the discrete jump at gripper bang being the **dominant** spectral event (from ~ε to 3)
- (c) Define edges via Signorini complementarity: an edge exists iff the gap d = 0 (contact established), not merely when forces are transmitted through a potential field

### C2. Catching number η > 1 biconditional is logically incorrect [NEW, from Phase 4]

**Location:** catching.tex:798-799 (prop:c-action-bound)

**The claim:** "capturable if and only if η(m, v_⊥) > 1"

**The problem:** η is defined as:
```
η = (Kd²/mv²_⊥) × (Δt_viable/Δt_grip)
```
The capture theorem requires BOTH factors individually > 1. But η > 1 does NOT imply both factors > 1: one could be 0.5 and the other 3, giving η = 1.5 while violating the energy condition. The biconditional is necessary but not sufficient.

**Fix:** Either (a) change "if and only if" to "only if" (η > 1 is necessary), or (b) redefine η as min(energy margin, timing margin) instead of their product, or (c) add the qualifier "provided both margins individually exceed unity."

---

## Structural Findings (author's discretion)

### S1. Capture theorem "iff" conflates design and control [STRUCTURAL]
**Location:** catching.tex:402-404

Conditions (i)–(ii) are hardware design constraints; only (iii) is an active control decision. The "if and only if" obscures which failures are hardware vs. policy. Not logically wrong, but misrepresents agency.

### S2. Mass invariance scope [STRUCTURAL]
**Location:** catching.tex:170-172

Now scoped with "provided K > mv²_⊥/d²" (our fix), which is correct. Residual concern: friction μ dependence on normal force (heavy vs. light objects) is not addressed in the static hold proof. Minor — the framework's λ₁ claim is not threatened.

### S3. Sword definition prose drift [DRIFT, from Phase 3]
**Location:** catching.tex:17-19

Prose says "sword in the precise sense of the framework," but def:c-sword (line 58-70) adds a third condition (reachability) beyond the framework's two-condition def:sword. Line 72 partially resolves this by calling it an "instantiation."

---

## Unresolved Confusions (from Phase 4)

### U1. `Reach(κ)` notation mismatch
**Location:** catching.tex:68

Framework defines `Reach(x, U_r, T)` with three arguments (framework.tex:478-479). Catching uses `Reach(κ)` with one argument. Symbol `κ` is defined as "curvature of viability manifold" in framework.tex:719, not as "king."

### U2. Tangent bundle TM — manifold M undefined
**Location:** catching.tex:28, 169

`TM` is standard differential geometry but `M` is never defined in this document. Reader doesn't know if M is the robot's joint space, object configuration space, or product space.

### U3. v_⊥ forward reference
**Location:** catching.tex:172

Used in Theorem c-equivalence (line 172) but first defined 230 lines later in Theorem c-capture (line 402).

### U4. η biconditional [= Critical finding C2 above]

---

## Cosmetic Findings

- **\cite{cheeger} misdirected** (catching.tex:488): Cited for C₃ eigenvalue computation, but Cheeger's work is about the inequality relating spectral gap to isoperimetric constants. The eigenvalue {0,3,3} is elementary linear algebra. Minor — the math is correct regardless.

---

## Symbolic Integrity (Phase 5)

| Check | Status | Issues |
|-------|--------|--------|
| 5a. Notation consistency | PASS | 0 critical collisions |
| 5b. Reference integrity | PASS | 20/20 internal + 5/5 external refs resolve |
| 5c. Citation integrity | PASS | 3/3 citations in bibliography |
| 5d. Notation collision | PASS | K, D, d, F, L, m, v all well-distinguished |

No other files reference catching.tex labels — it is self-contained.

---

## Action Priority

1. **Fix η biconditional** (C2) — straightforward, our code, our bug
2. **Address compliant-vs-rigid edge criterion** (C1) — the deepest issue; needs architectural decision
3. **Fix Reach(κ) notation** (U1) — mechanical
4. **Define M or qualify TM** (U2) — one sentence
5. **Move v_⊥ definition earlier or add forward pointer** (U3) — mechanical
