# Self-Symbolic Consistency Check — Cross-Paper Exponential Bridge

**Date:** 2026-03-10
**Scope:** CLT duality paper × XLA-∞ paper — new Proposition 10.6 + Remark (rem:exp-bridge)

## Summary

- LOAD-BEARING tensions: 5 (2 reinforced, 3 unresolved)
- Time-axis issues: 0 breaking, 0 drift
- Unresolved confusions: 3 (all in XLA-∞ remark)
- Symbolic issues: 0 (all references/citations/labels compile correctly)

---

## Critical Findings (requires action)

### C1. {exp, log, MMA} ≠ {smooth_where, grad_rescale, safe_ops} — naming collision in XLA-∞

**Source:** Phase 1 (XLA-∞) + Phase 4 (fresh-eyes)
**Severity:** LOAD-BEARING
**Location:** `main.tex:617`

The XLA-∞ paper defines its "three primitives" as `{smooth_where, grad_rescale, safe_ops}` (Section 3.2, line 383). The new remark introduces `{exp, log, MMA}` and calls it "the three-primitive architecture of this paper." These are two different triads at two different levels:

- **Compile-time (branch elimination):** {smooth_where, grad_rescale, safe_ops}
- **Runtime (arithmetic):** {exp, log, MMA}

The remark overloads "three primitives" without acknowledgment, creating a false identification.

### C2. "DPPU pipeline" undefined in XLA-∞

**Source:** Phase 1 (XLA-∞) + Phase 4 (fresh-eyes)
**Severity:** STRUCTURAL → effectively LOAD-BEARING (correspondence item (a) references it)
**Location:** `main.tex:624`

The acronym "DPPU" appears exactly once, never expanded. The paper uses "differentiable rigid-body dynamics pipeline" elsewhere.

### C3. "MMA" unexpanded in XLA-∞

**Source:** Phase 4 (fresh-eyes)
**Severity:** STRUCTURAL
**Location:** `main.tex:617, 628`

"MMA" (matrix multiply-accumulate) is used twice without expansion. The CLT paper defines it; the XLA-∞ paper does not.

### C4. Completeness Theorem scope mismatch in XLA-∞

**Source:** Phase 1 (XLA-∞)
**Severity:** LOAD-BEARING
**Location:** `main.tex:631-632`

The remark states: "The Completeness Theorem ensures that this three-primitive reduction is branchless." But the Completeness Theorem (line 563) proves branch elimination via Layers 0–1 ({smooth_where, grad_rescale, safe_ops}), not branchlessness of {exp, log, MMA}. The theorem says nothing about exp, log, or MMA. The remark misattributes the theorem's scope.

**Correct reading:** The Completeness Theorem ensures the *pipeline* is branchless. The CLT paper's proposition ensures the *remaining runtime arithmetic* decomposes into {exp, log, MMA}. These are complementary, not identical.

### C5. "four computational stages" but five enumerated in CLT paper

**Source:** Phase 1 (CLT)
**Severity:** LOAD-BEARING (creates ambiguity in the enumeration that is the proof's core)
**Location:** `clt-duality-note.tex:1496`

The proof says "four computational stages" but enumerates five `\emph{}` subsections: SDE step, Cost evaluation, Exponential reweighting, Weighted average, Convergence. The fifth (Convergence) is a meta-conclusion, not a computational stage; the count should be "four" and "Convergence" should be separated from the enumeration.

---

## Structural Findings (author's discretion)

### S1. Scalar exp characterized as "dim G = 1 case of exp_G" (CLT paper)

**Location:** `clt-duality-note.tex:1511`
**Verdict after cross-validation:** REINFORCED. The paper establishes (ℝ₊, ×) as a 1D Lie group (Section 4) whose exp is the ordinary scalar exponential. The identification is consistent but relies on the reader recalling which 1D group is relevant.

### S2. Weighted CLT invocation (CLT paper)

**Location:** `clt-duality-note.tex:1518-1521`
**Note:** The proof invokes the CLT for bounded-weight Monte Carlo. The preceding Hopf-Cole remark (line 1463) makes the same claim. The proposition inherits the existing gap—the bounded-cost → CLT argument should reference the delta method or self-normalizing CLT. However, this is a pre-existing issue in the Hopf-Cole remark, not newly introduced by the proposition.

### S3. Mellin-Fourier theorem cited for convolution property (CLT paper)

**Location:** `clt-duality-note.tex:1530-1533`
**Note:** The exponential bridge remark says thm:mellin-fourier shows log converts multiplicative convolution to additive. The theorem actually states transform equality (ℳ[μ](s) = ℱ[log*μ](s)), not the convolution property directly. The convolution property follows from the group isomorphism plus the theorem, but the citation is slightly imprecise.

---

## Cosmetic Findings

- None beyond the structural findings above.

---

## Symbolic Integrity (Phase 5)

| Check | Result |
|-------|--------|
| Notation consistency (exp_G, log_G, 𝔤, G) between papers | PASS |
| Reference integrity — CLT paper (thm:add-clt, thm:mult-clt, thm:mellin-fourier) | PASS |
| Reference integrity — XLA-∞ (thm:completeness, rem:exp-bridge) | PASS |
| Citation integrity — zhang2026clt | PASS (defined at line 1658, cited at line 620) |
| Claim distinction — "arithmetically complete" vs "branchless" | PASS (properly distinguished at line 633) |
| Compilation — both papers | PASS (xelatex ×2, no errors) |

---

## Time-Axis (Phase 3)

No BREAKING or DRIFT issues detected. Both insertions are properly integrated with existing content and all cross-references resolve.
