# Plan
Updated: 2026-02-23T23:55:00+08:00
Horizon: 3

## Objective

T := Upgrade 论一把刀.md into an arxiv-style paper: "The Agentic Theory"
B := pool/论一把刀.md (the source essay, 1775 lines, Chinese+English, with formal framework)

## Central Thesis (from the author)

**The 刀 (knife) is the mean.**

The knife — defined as a resource r satisfying U_r ≠ ∅ ∧ r ∈ Im(O) — is the mean field of autonomous actuation in the system. Phase transition occurs at the mean. Below = tool. Above = knife. The viability axiom is maintenance of the mean below critical threshold.

## Current step

Step 0: Executor reads pool/论一把刀.md. Understands the full structure (§0–§12, Appendices A–E, Epilogue). Identifies the formal elements that map to arxiv paper structure.

## Next 3 steps

1. **Structural mapping**: Map essay sections to paper sections (Abstract, Introduction, Definitions, Main Results, Applications, Discussion). Identify what becomes theorems, what becomes examples, what becomes remarks. Write the mapping to agent_workspace/.

2. **LaTeX scaffold**: Create main.tex with arxiv-compatible preamble (amsart or similar), theorem environments matching the essay's formal structure (Axiom, Definition, Theorem, Remark, Proof). Section stubs from the mapping. Build with latexmk -pdf.

3. **Content migration — core theory (§0–§9)**: Translate §0 (Viability Axiom) through §9 (Breakpoint Strategy) into LaTeX. Preserve all formal content. Chinese prose becomes English academic prose. Historical examples become numbered Examples. The knife definition becomes Definition 1. The phase transition becomes Proposition 1. The cut vertex analysis becomes Theorem 1.

## Status

Awaiting executor. Pool loaded. Plan written by Grade 2 controller.
