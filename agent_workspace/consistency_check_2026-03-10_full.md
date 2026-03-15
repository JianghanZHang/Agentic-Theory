# Self-Symbolic Consistency Check — Full Paper

**Date:** 2026-03-10
**File:** `independent_volume/add_mult_clt/clt-duality-note.tex`
**Central claim:** Additive and multiplicative CLTs are instances of a single phenomenon on LCA groups, connected by Fourier-Mellin duality via log: (R+, x) -> (R, +).

## Summary

- LOAD-BEARING tensions: 4 (1 self-resolving, 2 acknowledged by paper, 1 genuine)
- Time-axis issues: 0 breaking, 0 drift
- Unresolved confusions: 3
- Symbolic issues: 0 critical (3 mild notation overlaps, 8 uncited bibitems)

---

## Critical Findings (requires action)

### F1. "LQG" acronym never expanded (line 1575)

**Phase 4 — UNRESOLVED confusion.**
"Linear-Quadratic-Gaussian" is standard in control theory but the paper's audience is probability/harmonic analysis (MSC 60F05, 43A25). Same issue with "LQR" at line 1395.

**Action:** Expand both on first use.

### F2. Representation variable switches from ρ to π unsignaled (lines 1248 vs 1318)

**Phase 4 — UNRESOLVED confusion.**
Peter-Weyl theorem (line 1248) indexes representations by ρ. Fokker-Planck proposition (line 1318) switches to π without signal. This collides with the double-cover map π: SU(2) → SO(3) at line 1218.

**Action:** Author's discretion — either unify to one variable or add a brief signal at the switch.

---

## Structural Findings (author's discretion)

### S1. CLT → Strong Szegő regularity asserted without proof (lines 1108-1150)

**Phase 1 — LOAD-BEARING.**
The paper claims the CLT dynamics "draw spectral densities toward" the Gaussian attractor, placing them generically in the Strong Szegő basin where E(f) < ∞. This is asserted with the qualifier "naturally satisfied in its vicinity" but not proved. The nontrivial-multiverse corollary (cor:nontrivial-volume) depends on E(f) ∈ (0, ∞).

**Cross-validation:** The paper itself acknowledges this explicitly at line 1136: "The difference between a trivial and non-trivial multiverse reduces to a single analytic condition: the finiteness of E(f)." The tension is by design — the paper flags the condition as open rather than claiming it is proved. **Verdict: ACKNOWLEDGED.**

### S2. Spectral gap vanishes for non-compact groups (lines 1374-1375)

**Phase 1 — LOAD-BEARING.**
On SE(3), the Casimir spectrum has continuous spectrum down to 0 → polynomial convergence (t^{-d/2}) rather than exponential. This means the non-abelian extension is weaker than the compact case.

**Cross-validation:** The paper explicitly states this at line 1375 and identifies it as the reason stochastic methods (MPPI) are preferable — they bypass the spectral curse at O(N^{-1/2}) independently of dim G (line 1402). The CLT rate replaces the spectral gap as the operative bound. **Verdict: ACKNOWLEDGED.**

### S3. Exponential map only local in non-abelian (lines 1164-1167)

**Phase 1 — LOAD-BEARING.**
The Fourier-Mellin duality is exact (global isomorphism) on LCA groups. On non-abelian Lie groups, exp is only a local diffeomorphism. The paper states: "The CLT concerns small fluctuations near the identity — precisely the regime where exp is a diffeomorphism."

**Cross-validation:** This is the correct mathematical statement. The CLT is inherently a local phenomenon (normalized sums converge weakly, which is a statement about neighborhoods of the identity in the character group). The paper's claim is limited and accurate. **Verdict: ACKNOWLEDGED.**

### S4. Hardy decomposition transport to (R+, ×) (lines 988-1030)

**Phase 1 — STRUCTURAL.**
The Hardy duality theorem (thm:hardy-duality) claims the projection operators commute with log_*. The proof uses Fourier-transform uniqueness. The concern is whether Mellin analyticity as a causal proxy is fully justified.

**Cross-validation:** The proof at lines 1024-1031 is self-contained: both sides have the same Fourier transform, so they are equal as L² functions. The analyticity is inherited via the isometric isomorphism. **Verdict: REINFORCED.**

### S5. ε notation collision (lines 230 vs 1318+)

**Phase 5 — MEDIUM.**
ε = residual error Y - E[Y|G] in the proof at line 230; ε = diffusion parameter in the Fokker-Planck section. Separated by ~1000 lines, different mathematical contexts.

---

## Cosmetic Findings

- **Unstated second-moment assumption in multiplicative CLT** (line 615): The Phase 1 agent flagged this, but Var(log Y) < ∞ IS the second-moment condition by definition. Self-resolving.
- **CMT applied without formal citation** (line 619): Standard practice in a paper of this level. The continuous mapping theorem is a basic tool.
- **Ambiguous quantifier in Mellin-Fourier** (line 674): The proof makes it transparent. Cosmetic.
- **42 orphan labels**: Definitions, examples, and remarks not cross-referenced. Intentional — they establish foundations.
- **8 uncited bibliography entries**: Douglas, Garnett, Hoffman, Nikolski, Simon, BottcherSilbermann, SzNF, Hall (Hall may be a false positive). Optional cleanup.

---

## Symbolic Integrity (Phase 5)

| Check | Count | Status |
|-------|-------|--------|
| Labels defined | 96 | Clean |
| Crefs resolved | 75/75 | Clean |
| Dangling references | 0 | Clean |
| Citations matched | 36/36 | Clean |
| Circular dependencies | 0 | Clean |
| Forward references | 0 | Clean |
| Notation conflicts | 3 mild (P, Q, ε) | Contextually separated |

---

## Phase 3: Time-Axis

All changes since baseline (dcb103b) are HARMLESS. No breaking issues, no drift. All new labels resolve, all new crefs point to existing targets, all new content is backward-referencing only.
