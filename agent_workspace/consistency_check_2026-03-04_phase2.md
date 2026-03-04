# Phase 2: Cross-Validation of Load-Bearing Tensions

Timestamp: 2026-03-04T$(date +%H:%M:%S)

---

## TENSION T1: Agents can strategically shape Ubar (meanfield.tex:37-62)

**Vulnerability:** If agents can coordinate to keep actuation below threshold while maintaining hidden capacity, the detection threshold becomes a game, not a law.

### Cross-reference check

**framework.tex (ex:xiaohe, lines 837-868):** The Xiao He example directly addresses this. Xiao He *does* strategically game the threshold via deliberate self-corruption. The text explicitly states:

> "Xiao He's response: deliberate self-corruption (accepting bribes conspicuously). This performed two operations simultaneously: (i) Signal reduction: visible moral degradation signals ||U_r|| -> 0 ... (ii) Detection exit: pull ||U_r|| toward Ubar, falling below the detection threshold" (framework.tex:843-850)

But critically, the framework does NOT treat this as a refutation. It classifies Xiao He's outcome as **sword -> pre-sword regression**, not as resolution:

> "The pre-sword state is unstable: the causal envelope remains, and any expansion of Obs re-detects r, returning to the sword row." (framework.tex:864-865)

**results.tex (rem:lifecycle-scope, lines 62-81):** Reinforces that the pre-sword state is a *deferral*, not a resolution:

> "the pre-sword defers rather than resolves the binary fate." (results.tex:80)

**results.tex (prop:imperfect, lines 137-168):** The imperfect observability proposition addresses the *systemic* response to gaming: expanding Obs creates new swords definitionally. The surveillance expansion co-drives with elimination:

> "Expanding Obs does not 'discover existing swords'---it *creates new ones* definitionally." (results.tex:151-152)

**meanfield.tex (rem:meanfield-validity, lines 206-212):** Acknowledges a limit of the arithmetic mean in hierarchical systems:

> "In hierarchical systems, clique amplification (see app:zhongxian) may require a modified threshold that accounts for correlated actuation within subgroups." (meanfield.tex:209-211)

This partially addresses coordinated gaming by acknowledging that correlated actuation within subgroups breaks the simple arithmetic mean.

### Verdict: REINFORCED (partially)

The document explicitly models strategic threshold-gaming (Xiao He) and classifies it as unstable deferral, not successful evasion. The pre-sword state's instability (any Obs expansion re-detects) provides a structural answer. However, the vulnerability's deeper point -- that *coordinated* hidden capacity could systematically suppress the mean -- is only partially addressed by rem:meanfield-validity's acknowledgment of clique amplification. The framework recognizes the problem exists but defers the modified threshold to an appendix rather than integrating it into the main theorems.

---

## TENSION T2: Circular definition of K (framework.tex:33-39)

**Vulnerability:** The viability kernel is defined as "where the king retains authority," then the tangential condition is claimed to hold by definition. This is circular.

### Cross-reference check

**framework.tex (lines 33-39):** The claimed circularity is at:

> "When U = Umax, the control set is full and this path is mathematically guaranteed to exist: ... since K is defined as the set of states where the king retains authority, C(x) spans T_K(x) at every x in K^o --- the king would not include in K states he cannot control. The tangential condition holds trivially." (framework.tex:33-39)

**framework.tex (rem:viab-subset, lines 24-31):** The distinction between K and Viab(K) provides a partial break. K is the *static* criterion; Viab(K) is the *dynamic* subset from which viable paths exist:

> "Viab(K) subset K is the largest closed subset of K from which a viable path exists. States in K \ Viab(K) satisfy the static criterion (the king retains authority) but lack a dynamic escape." (framework.tex:25-28)

**calculus.tex (def:tower, lines 16-33):** The agentic space tower provides an independent *structural* definition of the viability kernel:

> "L1: Viable kernel Viab(K) subset S. The compact set of states from which the king retains a path to infinity." (calculus.tex:22-24)

This is still a reformulation rather than an independent characterization.

**calculus.tex (thm:massgap, lines 715-742):** The mass gap theorem provides the *independent* characterization that breaks the circularity. It defines viability equivalently as:

> "(i) lambda_1 > 0 (spectral gap), (ii) h(G) > 0 (positive Cheeger constant), (iii) |phi| > 0 for some agentic flow phi (viability axiom), (iv) kappa can reach infinity in G (connectivity)." (calculus.tex:717-724)

The spectral gap lambda_1 > 0 is computable from the execution graph's Laplacian (def:laplacian, line 666) without any reference to "where the king retains authority." The Cheeger constant h(G) is a purely graph-theoretic quantity. These provide non-circular operational definitions of viability.

**framework.tex (def:viab-metric, lines 249-259):** The viability metric g_V = V^{-2} g_S gives K an intrinsic Riemannian geometry. Completeness (prop:viab-complete, line 267) and negative curvature (prop:neg-curvature, line 294) are geometric properties that characterize K independently of the king's "authority."

### Verdict: REINFORCED

The circularity at framework.tex:33-39 is real *locally*, but it is broken by thm:massgap (calculus.tex:715), which provides four equivalent, independently computable characterizations of viability that do not reference "authority." The spectral gap lambda_1 > 0 and the Cheeger constant h(G) > 0 are graph-theoretic quantities defined on the execution graph without circular reference to K. The initial definition of K in framework.tex is a *semantic* starting point; the operational content is supplied by the spectral characterization.

---

## TENSION T3: Mean-field detection assumes full observability (calculus.tex:125-144)

**Vulnerability:** The capacity assignment c(e_r) = max(||U_r|| - Ubar, 0) requires the king to observe all U_r, but real detection has bounded bandwidth.

### Cross-reference check

**meanfield.tex (prop:detection-derivation, lines 22-62):** The tension is directly addressed at the *source*. The detection derivation explicitly starts from finite bandwidth:

> "Let the king have finite monitoring bandwidth B: he can observe at most B agents simultaneously." (meanfield.tex:24-25)

The optimal monitoring policy is derived as a threshold rule under this constraint:

> "r in Im(Obs*) iff ||U_r|| - Ubar > tau(B), where tau(B) is the threshold that selects the top-B agents by deviation from the mean." (meanfield.tex:30-34)

The king does NOT observe all U_r. He observes the *deviations from the mean* that exceed the bandwidth-dependent threshold tau(B). The mean Ubar is computed as a population statistic (computable from aggregate information, not per-agent monitoring).

**manipulation.tex (sec:m-observer, lines 457-572):** The observer section provides a concrete physical instantiation with bounded bandwidth:

> "Detection bandwidth B = camera resolution x FOV solid angle: the maximum number of blocks simultaneously monitorable." (manipulation.tex:516-518)

> "Detection threshold tau(Obs) = minimum block size (in pixels) for reliable pose estimation." (manipulation.tex:519-520)

This demonstrates that the framework *already operates* with bounded-bandwidth detection in its applied chapter.

**manipulation.tex (rem:m-bandwidth, lines 511-528):** Explicitly links the finite-bandwidth camera to the detection function of prop:detection-derivation.

**applications.tex (def:corruption, lines 353-365):** The corrupted detection function addresses what happens when Obs is *wrong*, not just bandwidth-limited. Identity-based detection produces mass false positives -- showing the framework is sensitive to detection function quality.

**discussion.tex (sec:domain, lines 1-29):** "High-latency detection" is listed as an explicit failure mode:

> "Obs too slow; phase transition completes before detection" (discussion.tex:19)

### Verdict: REINFORCED

The vulnerability is addressed at the source: prop:detection-derivation (meanfield.tex:22-35) derives the threshold rule *from* finite bandwidth B, not despite it. The capacity assignment c(e_r) uses Ubar as a population statistic (computable without per-agent monitoring) and the threshold tau(B) explicitly depends on the bandwidth. The manipulation chapter (sec:m-observer) instantiates this with a physically bounded camera. The framework does not assume full observability; it derives optimal monitoring under bounded observability.

---

## TENSION T4: Dimension d=4 spatial/temporal conflation (fields2022.tex:209-229)

**Vulnerability:** The Hausdorff dimension intersection criterion is purely topological and doesn't distinguish spatial from temporal dimensions. Applying it to Lorentzian spacetime is unjustified.

### Cross-reference check

**fields2022.tex (rem:d4-not-analogy, lines 209-229):** The source remark acknowledges and attempts to address the issue:

> "The Hausdorff dimension intersection criterion is a topological theorem about generic intersection in R^d; it does not distinguish between spatial and temporal dimensions." (fields2022.tex:210-212)

The remark *asserts* rather than *proves* that the topological criterion applies to spacetime:

> "The temporal dimension is not Wick-rotated fictitious time: it is the irreversible wall-clock time ... Agents execute in spacetime, not in space. Their causal envelopes are subsets of R^4, not R^3." (fields2022.tex:221-228)

**manipulation.tex (rem:m-d4, lines 1601-1631):** Provides a second, independent justification grounded in physical robotics:

> "Every object in this chapter --- the robot's end-effector, each block, the wrist camera's field of view --- traces a worldline in physical spacetime R^3 x R^1 = R^4." (manipulation.tex:1603-1605)

> "The robot's execution path and a given block's worldline are each curves of Hausdorff dimension 2 (Brownian scaling under finite-bandwidth control)." (manipulation.tex:1613-1615)

The argument is: because the robot's control bandwidth is finite, the execution path's roughness gives it Hausdorff dimension 2 in R^4 regardless of the Riemannian vs. Lorentzian signature. The *marginality* at d=4 is then a statement about control-theoretic reachability, not about metric geometry.

**threebody.tex:** No remark labeled "rem:3b-d4" was found. The threebody chapter does not separately address the d=4 question.

**calculus.tex:** No independent justification for d=4 beyond the references to temporal linearity (rem:di-temporal).

### Verdict: UNRESOLVED (partially mitigated)

The vulnerability is real. The Hausdorff dimension intersection theorem assumes a Euclidean (or at minimum, Riemannian) metric. Lorentzian spacetime has indefinite signature -- causal structure restricts which curves can intersect, and the "generic intersection" theorem does not apply naively. The document acknowledges the issue (fields2022.tex:210-212) and asserts that the Euclidean topology of R^4 is the relevant one for execution paths (since agents use wall-clock time), but it does not provide a proof that the intersection criterion survives the causal constraint. The manipulation.tex instantiation (rem:m-d4) provides a more grounded argument: the Hausdorff dimension arises from *control bandwidth*, not from the spacetime metric, so the Riemannian/Lorentzian distinction may be irrelevant at the level of the controller's sampling rate. However, this argument is stated as a remark, not a theorem, and the gap between "R^4 as ambient space" and "generic intersection under causal constraints" remains unproved.

---

## TENSION T5: Phase reassertion claimed automatic but indistinguishable from agency (second_sex.tex:214-220)

**Vulnerability:** Mulan's return to feminine roles is interpreted as "automatic phase function" but the text presents it as active choice. The framework cannot distinguish structure from agency.

### Cross-reference check

**second_sex.tex (lines 206-220):** The relevant passage:

> "The moment the mean field stabilises --- war ends, peace returns --- the boundary reasserts: '脱我战时袍，著我旧时裳。当窗理云鬓，对镜帖花黄。' She removes the war robe, puts on the old clothes, arranges her hair, applies the forehead ornament. The poem presents this as free choice ('木兰不用尚书郎'), but structurally it is the phase function restoring equilibrium." (second_sex.tex:206-212)

> "蔡文姬 and 花木兰 are complementary probes of the same boundary ... 花木兰 is a supercritical fluctuation: the sword breaks under perturbation (war), but the system anneals back when the perturbation ends. Neither literary genius nor military prowess shifts the attractor." (second_sex.tex:214-220)

**framework.tex (rem:intent, line 673):** States explicitly that the framework tests capability, not intention:

> "The criterion tests *capability*, not *intention*. The king detects whether you *can* act, not whether you *want to*. Loyalty does not enter the criterion." (framework.tex:674-676)

This is the framework's deliberate design choice: it excludes agency/intention from the formal model.

**framework.tex (rem:scope, lines 102-109):** Acknowledges the scope limitation directly:

> "This paper presents a compressed model of the topology of execution capability under the viability axiom. It deliberately ignores culture, personality, economics, and moral narrative in exchange for a testable structural criterion." (framework.tex:103-106)

**framework.tex (prop:phase, lines 689-712):** Phase transitions are defined as shifts in the king's objective function J(s, phi), not as changes in any agent's properties. The labeling is *functional*:

> "The phase transition does not change the physical properties of r. It changes the king's objective function J(s, phi)." (framework.tex:701-702)

**calculus.tex (thm:beauvoir, lines 1839-1873):** The Beauvoir representation theorem formalizes the Subject/Other distinction as the dual of the agentic tower operations. The passive voice marker 被 maps each operation to its dual. But this formalization still does not provide a criterion to distinguish "the phase function restoring equilibrium" from "the agent choosing."

**discussion.tex:** The discussion chapter does not address the structure-vs-agency distinction.

### Verdict: UNRESOLVED

The framework *acknowledges* this limitation (rem:intent, rem:scope) but does not resolve it. By design, the model tests capability, not intention, and excludes agency from its formal vocabulary. The vulnerability is therefore structural: the framework *cannot* distinguish Mulan's "choice" from the phase function's "restoration" because it deliberately excludes the vocabulary needed to make that distinction. This is a genuine boundary of the model -- it is a compressed structural theory that does not model agency. Whether this is a flaw or a feature depends on whether one accepts the scope limitation stated in rem:scope.

---

## TENSION T6: Force closure maintenance under coupled wind (manipulation.tex:286-311)

**Vulnerability:** The bi-level coupling theorem assumes force closure is continuously maintainable, but wind in the tangential contact plane could break it.

### Cross-reference check

**manipulation.tex (thm:m-bilevel, lines 286-325):** The bi-level coupling theorem already includes wind in its Newton constraint:

> "sum_i f_i = m(x_des(t) - g) + F_wind(t)" (manipulation.tex:293-294)

The acceleration bound explicitly accounts for wind:

> "|x_z(t)| <= (2 mu_s N_max - |F_wind^perp(t)|) / m - g" (manipulation.tex:302-304)

So wind is *not* ignored in the theorem; it constrains the feasible trajectory set.

**manipulation.tex (rem:m-singularity, lines 327-348):** Explicitly addresses wind as a perturbation to force closure:

> "Wind and inertial loads attempt to restore the object's free DOF (break the singularity); the inner optimisation maintains it." (manipulation.tex:343-345)

**manipulation.tex (sec:m-curriculum, subsection "Adversarial robustness", lines 1491-1599):** A dedicated subsection formalizes wind as a sword and addresses wind robustness:

> "The wind is a sword in the exact sense of def:sword: (i) Autonomous actuation. U_W != empty: the wind applies force independently of the robot's control. (ii) Observable. The wind's effect is observable through two channels: the rho monitor detects shifting contact forces (lambda_1 drops as a block slides), and the wrist camera detects displaced blocks." (manipulation.tex:1508-1517)

**manipulation.tex (prop:m-wind, lines 1520-1561):** Provides the exact formula for how wind reduces lambda_1:

> "lambda_1' = lambda_1 - ||F_wind^perp|| / (m_k g)" (manipulation.tex:1527-1529)

Three regimes are defined: stable, sliding (robot intervenes), and toppled (robot replans). This directly addresses the vulnerability: force closure *can* be broken by wind, and the framework defines the recovery mechanism (FSM re-enters Phase 1, DAG is recomputed).

**manipulation.tex (rem:m-wind-training, lines 1563-1599):** Wind is explicitly a curriculum axis:

> "The wind intensity F_max is a fourth curriculum axis, orthogonal to the three in sec:m-curriculum" (manipulation.tex:1585-1586)

Training includes annealing wind intensity from 0 to 0.5 m_k g (half the block's weight), teaching the policy to recover from wind-induced perturbations.

### Verdict: REINFORCED

The vulnerability is comprehensively addressed. The bi-level coupling theorem (thm:m-bilevel) includes wind in its Newton constraint and derives the wind-dependent acceleration bound. Proposition prop:m-wind formalizes exactly how wind reduces lambda_1 and defines three regimes including toppling (lambda_1 <= 0). Wind is classified as a sword (autonomous actuation, observable), and the training curriculum (rem:m-wind-training) explicitly trains the policy against scheduled wind perturbations. Force closure is *not* assumed to be continuously maintainable -- the framework models its breakage and defines recovery.

---

## Summary Table

| Tension | Vulnerability | Verdict | Key Resolution |
|---------|--------------|---------|----------------|
| T1 | Strategic Ubar gaming | REINFORCED (partial) | Xiao He classified as unstable deferral; clique amplification acknowledged; Obs expansion creates new swords |
| T2 | Circular K definition | REINFORCED | Mass gap theorem (thm:massgap) provides four independent, non-circular characterizations |
| T3 | Full observability assumed | REINFORCED | prop:detection-derivation derives from finite bandwidth B; manipulation chapter instantiates with bounded camera |
| T4 | d=4 conflation | UNRESOLVED (mitigated) | Remark acknowledges issue; control-bandwidth argument is asserted but not proved under causal constraints |
| T5 | Structure vs. agency | UNRESOLVED | Framework deliberately excludes agency (rem:intent, rem:scope); cannot distinguish phase function from choice |
| T6 | Wind breaks force closure | REINFORCED | Wind included in Newton constraint; prop:m-wind formalizes lambda_1 reduction; training curriculum includes wind |

**Overall assessment:** 4 of 6 tensions are REINFORCED by cross-references elsewhere in the document. 2 are UNRESOLVED: T4 (the d=4 argument lacks a rigorous proof under Lorentzian causal constraints) and T5 (the structure-vs-agency distinction is a declared scope limitation, not a resolved tension). No tensions are CONTRADICTED -- the document's internal consistency holds, though with acknowledged blind spots.
