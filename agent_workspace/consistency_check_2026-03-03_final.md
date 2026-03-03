# Self-Symbolic Consistency Check (Post-Surgery)

**Date:** 2026-03-03
**Scope:** Full thesis, focus on kinks after Appendix K refactor + axiom layer patch

---

## Summary

| Category | Count |
|----------|-------|
| LOAD-BEARING tensions | 0 |
| STRUCTURAL tensions | 3 (all minor) |
| COSMETIC tensions | 5 |
| Time-axis issues | 2 drift, 0 breaking |
| Unresolved confusions | 1 (numerical typo) |
| Symbolic issues | 0 dangling refs, 6 orphan labels (acceptable) |

**All 8 previous fixes verified landed correctly.**

---

## Critical Findings (requires action)

### None.

No LOAD-BEARING issues remain. The axiom chain (viability -> mass gap -> mean field -> sword lifecycle -> event-locking) is intact and consistent across all cross-referenced files.

---

## Actionable Findings (small kinks)

### K1. Section title "three orthogonal axes" — stale after roadmap fix

- `manipulation.tex:1047`: section title still says `\section{Curriculum: three orthogonal axes}`
- `manipulation.tex:1049`: body still says "three independent complexity axes"
- But `manipulation.tex:46` (roadmap) now says "four orthogonal complexity axes"
- **Fix:** Update section title and opening sentence to "four"

### K2. Unit-move count discrepancy: 118 vs 116

- `huarongdao.tex:337` (thm:eightyone): says "118 unit moves"
- `huarongdao.tex:366` (counting table): says "116 unit moves"
- These describe the same quantity but give different values.
- **Fix:** Verify the correct count and reconcile.

### K3. rem:m-event-lock "sequentially activated" claim is vague

- `manipulation.tex:1278`: "four conditions are sequentially activated and discharged" through five phases
- The 4-to-5 mapping is never made explicit (which phases activate which conditions)
- Condition (i) viability is persistent, not "activated" in one phase
- **Fix:** Either make the mapping explicit or soften to "are maintained and discharged"

---

## Structural Findings (author's discretion)

### S1. prop:event-lock condition (iv) wording is ambiguous
`meanfield.tex:234`: "closed under the pushforward" could mean preimage closure or measure invariance. The instantiation in manipulation.tex suggests measure invariance. Technically sound but a careful reader may stumble.

### S2. "Eight stages" roadmap doesn't mention new subsections
`manipulation.tex:22` says "eight stages" — correct for the enumeration, but `sec:m-friction-di` and `sec:m-rlmd` are substantial new subsections not previewed. Readers encounter unannounced content. Acceptable since they are subsections within existing stages.

### S3. rem:m-singularity is now an orphan label
After fixing rem:m-soft-hard, nothing references `rem:m-singularity` anymore. The remark itself is valuable and reads well in place — just unreferenced.

---

## Cosmetic Findings

- **T2/T7:** `thm:m-invisible` cited for "persistent excitation" but the theorem is about causal invisibility. Semantically adjacent but misleading citation.
- **T4:** Opening sentence conflates five-phase cycle with sword lifecycle. Explained later in rem:m-singularity but initial phrasing overstates.
- **T5:** Variable `g` used for both margin function (RLMD) and gravity (dynamics). Standard in robotics, contextually clear.
- **6 orphan labels** among new additions: `rem:is-ising`, `eq:event-lock`, `sec:m-friction-di`, `eq:m-contact-di`, `rem:m-soft-hard`, `rem:m-event-lock`. All are terminal content; unreferenced labels are normal for closing remarks.

---

## Symbolic Integrity

- **Dangling references:** 0
- **Beta fix verified:** no collision with β usage in threebody.tex (different context)
- **Sigma definition chain verified:** consistent across framework.tex, threebody.tex, manipulation.tex
- **All cross-references valid** across all 21 .tex files
- **Overall coherence:** Thesis reads as one argument, not a collection of papers. Inter-chapter flow is strong at every seam except Mean Field → Applications (abrupt topic shift, but functional).
