# Plan: §7.8 Representation Dynamics (表示学习)

Updated: 2026-02-25T12:00:00+08:00
Horizon: 4

## Controller: Claude (this session)
## Status: ALL PHASES COMPLETE — AWAITING REVIEW

---

## T (Target)

Promote the 第二性 framework from Appendix C to 正文 as §7.8 "Representation dynamics" (following §7.7 Contact dynamics). Formalize two theorems (Beauvoir Representation + Camus Absurdity), then derive three algorithms (video/image/text generation) that are structurally identical — same contact gradient flow, different execution graphs.

## B (Basis)

- §7.7 Contact dynamics (calculus.tex:771–1720) = structural template
- Appendix C 第二性 (second_sex.tex) = source material
- Tower L = (L₀, L₁, L₂, L₃), loss L = -|φ|, contact flow dc/dt = ∂|φ|/∂c - γ·c
- 力立丽 = lì lì lì = L₀ L₁ L₂₃ = the dual tower = the representation space

---

## Objectives (4 phases)

### Phase I: Foundations (Slot 0)

Write the two theorems + combination corollary into calculus.tex as §7.8.

0.1 — Definition: Dual tower L* = 力* ⊕ 立* ⊕ 丽*
0.2 — Theorem: Beauvoir Representation
0.3 — Theorem: Camus Absurdity
0.4 — Corollary: Beauvoir + Camus = Representation Learning
0.5 — Remark: Connection to Le Deuxième Sexe (Destin/Histoire/Mythes = 力/立/丽)

### Phase II: Universal Generation (Slot 1)

1.1 — Definition: Generation execution graph G_gen
1.2 — Remark: Generation = contact gradient flow on G_gen
1.3 — Table: Universality (locomotion / text / image / video = same flow, different G)

### Phase III: Three Algorithms (Slot 2)

2.1 — Algorithm 2: Text generation (base case, sequential G)
2.2 — Algorithm 3: Image generation (2D G = text on patches)
2.3 — Algorithm 4: Video generation (2D×T G = image × time)
2.4 — Remark: Universality — all three = Algorithm 1 with different G

### Phase IV: Integration (Slot 3)

3.1 — Update appendix C: add forward reference to §7.8
3.2 — Verify build, cross-references, narrative flow
3.3 — Final cascade verify

---

## Structural Template (from §7.7)

1. Definition → 2. Theorem → 3. Theorem → 4. Corollary → 5. Remark
→ 6. Definition → 7. Table → 8–10. Algorithms → 11. Remark (universality)

## Constraints

- No code (现在不用写代码)
- LaTeX only, matching existing style
- All notation from existing definitions
- Must compile with xelatex
- Surgery protocol on every edit
