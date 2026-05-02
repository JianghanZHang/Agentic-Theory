# Self Review: paper_minimalist

Internal honesty check. **Not for submission.** Lives next to the paper as a working document.

Generated after Task 9 (full compile) of the implementation plan. Page count: 7 (target was 8+1; gap is from `TBD` placeholder cells in experiments tables — will fill when experiments run).

---

## A. Claim audit

For each substantive claim in the paper, classify support type:
**E** = depends on experiment (placeholder), **C** = cited prior work, **P** = proved standalone in paper, **O** = overclaim / unsupported.

| # | Claim (paraphrased) | Section | Support | Notes |
|---|---|---|---|---|
| 1 | Student-$t$ mollifier restores $C^\infty$ dependence of soft-min expected objective on $\theta$ even when per-step margins are non-differentiable | §4.1 (Lemma 1) | P | Standard mollification + DCT; cite Folland already done. Bounded compact support makes DCT clean. Proof sketch is correct. |
| 2 | Capacity clamp gives finite score variance (Frobenius bound → operator norm → bounded score) | §4.2 (Lemma 2) | P | Operator-norm bound correct; proof sketch leaves input bound $\|s\|$ unquantified — see B.5. |
| 3 | Soft-min variance $\le M^2 H C$ (finite without baseline) | §4.3 (eq. variance-bound) | P | Follows directly from Lemmas 1+2 and $J_\beta \in [-M,0]$; algebra correct. |
| 4 | MinPG matches or exceeds PPO at $\ge$2M steps on Walker2d-v4 | §6.2 | E | Highest-risk empirical claim. Could fail entirely. Currently placeholder. |
| 5 | MinPG decisively beats REINFORCE-Gaussian | §6.2 | E | Should hold if mollifier hypothesis is correct; testable. Currently placeholder. |
| 6 | MinPG loses to SAC at low sample budgets ($\le$0.5M steps) | §6.2 | E | Stated as hypothesis in §6.2 prose. Currently placeholder. |
| 7 | Standard PG tricks are unnecessary in this setting | §1, §6.2 | mixed E + C | Engstrom/Andrychowicz cited but both papers argue tricks DO help; tension a reviewer will flag. §1 paragraph 3 states this as a logical consequence, not an empirical hypothesis. |
| 8 | The combination (Student-$t$ + soft-min + Frobenius clamp) is novel — no prior 3-of-3 paper | §1 (implicit), §2 | C | Verified by literature audit during planning; defensible. Individual primitives are known. |
| 9 | State-dependent $\nu(s)$ tracks the active contact-mode count | §3.2 (mollifier subsection) | O | Asserted in §3.2 prose ("at small $\nu$ the heavy tails enable exploratory escape from local plateaus arising at contact-mode boundaries"). Network outputs $\log\nu(s)$ with no contact-count input feature and no inductive bias enforcing this correlation. |
| 10 | Walker2d-v4 per-step task return is $O(1)$; accumulated return over $H=1000$ is $O(10^3)$ | §4.3 (variance comparison paragraph) | [verify: confirm with Gymnasium reward function source] | The "$10^3\times$ reduction in variance contribution" depends on this. Actual default Walker2d-v4 reward is velocity-forward + control cost ≈ O(1)–O(10) per step, so $O(10^3)$ cumulative may be correct, but the text should cite the specific reward function or provide a measurement. |
| 11 | Frobenius clamping admits a "clean closed-form projection step" | §2 (Spectral/Frobenius paragraph) | P | True; projection onto Frobenius ball is just scalar division — §3.3 eq. (3) confirms this. |
| 12 | The soft-min objective is bounded: $J_\beta \in [-M, 0]$ where $M = \sup_{j,s} m_j(s)^- + \log(kH)/\beta$ | §4.3 | P | Standard log-sum-exp bound; correct given margins bounded below. Depends on $m_j$ bounded below (contact simulator enforces this in practice but not stated as assumption). |
| 13 | Per-step margin non-differentiability arises at contact switching surfaces (foot strike/release, joint-limit hits) | §4 preamble | C | Standard claim in contact-rich locomotion literature; Aubin 1991 cited. Correct. |
| 14 | The learning rate $\eta$ is bounded above by $1/\gamma$ where $\gamma$ is the simulator's intrinsic damping | §3.5 (Hyperparameter atlas, Tier I) | O | No derivation provided. The claim "bounded above by the contractivity condition $\eta \ll 1/\gamma$" is asserted without any convergence theorem linking the damping constant to the gradient step size. Reviewers in control-aware RL will question this. |
| 15 | The CPO (Achiam et al.) Lagrangian approach differs from soft-min: "the soft-min margin is the objective, not a penalty added to one" | §2 | C | True as stated; the distinction is real. However one-sentence treatment is thin — see B.4. |
| 16 | $\beta$-annealing (small $\beta$ → explore broadly, large $\beta$ → sharpen worst-margin focus) | §3.5 Remark 1 | O | Stated as design intuition with no supporting analysis or citation. The monotone relationship between $\beta$ and gradient concentration is qualitatively correct (log-sum-exp properties) but the claim that this aids exploration is not supported. |
| 17 | Per-layer capacity caps $\{c_\ell\}$ are "derived from the torque/velocity envelope of the actuators" | §3.5 | [verify: exact derivation missing] | Asserted but the derivation or formula is deferred to §3.5 with only the label "determined from the control-authority bounds." No explicit mapping from torque limits to $c_\ell$ values appears in the text. |

---

## B. Weakest claims (in order of severity)

1. **State-dependent $\nu(s)$ tracking contact-mode count (Claim #9).**
   §3.2 asserts that at small $\nu$ the heavy tails "enable exploratory escape from local plateaus arising at contact-mode boundaries," implying $\nu(s)$ encodes contact-mode information. The network outputs $(\mu, \log\sigma, \log\nu)$ as three heads of the same MLP; nothing in the architecture, loss function, or input features enforces any correlation between $\nu(s)$ and contact count. This is the strongest overclaim in the paper. **Recommend:** weaken to "the network learns $\nu(s)$; we conjecture and will measure whether it correlates with foot-contact rate," OR provide an explicit contact-count input feature to the $\nu$ head.

2. **"Standard PG tricks are unnecessary" framing (Claim #7).**
   §1 paragraph 3 ("Given these three pieces, the score-function gradient is sufficient.") presents a logical claim. The §1 scope paragraph correctly limits this to Walker2d-v4, but the abstract and contribution item (1) do not carry this qualification consistently. Engstrom et al. and Andrychowicz et al. both conclude tricks contribute; the paper asks the converse but does not yet have data. **Recommend:** restrict the strong framing to the experimental scope throughout, matching the careful language already in §6 and §7.

3. **Learning rate bound $\eta \ll 1/\gamma$ (Claim #14).**
   §3.5 Tier I states the learning rate is "bounded above by the contractivity condition $\eta \ll 1/\gamma$ where $\gamma$ is the simulator's intrinsic damping." This is a consequential claim — it affects reproducibility — but no convergence theorem or stability argument appears in the paper. For an underdamped simulator ($\gamma \approx 0$) the bound is vacuous. **Recommend:** either cite a relevant convergence result (e.g., a Lipschitz-gradient descent bound on $J_\beta$) or replace this with a practical rule like "tune $\eta$ on validation rollouts from the range $[10^{-4}, 10^{-3}]$."

4. **CPO distinction (Claim #15) is under-argued.**
   §2 paragraph 2 distinguishes from CPO by stating "the soft-min margin is the objective, not a penalty added to one." A determined reviewer can argue the soft-min objective is mathematically equivalent to a Lagrangian collapse with an infinite penalty multiplier. **Recommend:** add a sentence quantifying the gradient direction: the soft-min gradient pushes toward higher worst-step margin regardless of mean task return, which is categorically different from the CPO Lagrangian update direction.

5. **Lemma 2 proof sketch leaves input bound implicit (Claim #2).**
   The proof says "$\sigma$ bounded below by $e^{-\sum_\ell c_\ell \|s\|}$" without bounding $\|s\|$. For Walker2d-v4 the observation is bounded by joint limits and gravity-bounded torso pose, but the paper doesn't state this assumption. The constant $C$ in the bound therefore has an unspecified dependence on the observation space diameter. **Recommend:** add an explicit observation-bound assumption (e.g., $\|s\| \le S_{\max}$) with a stated value or citation to the environment specification.

6. **$\beta$-annealing claim (Claim #16).**
   Remark 1 asserts that annealing $\beta$ upward aids exploration and then sharpens focus on the worst margin. The qualitative gradient-concentration argument is plausible but no experiment or citation supports the schedule design. **Recommend:** mark as design intuition and add "we use a linear $\beta$ schedule in experiments and verify sensitivity in §6.3."

---

## C. Overclaims to fix before any external read

- **§1 paragraph 3** ("Given these three pieces, the score-function gradient is sufficient.") — "sufficient" is presented as a logical conclusion from the three design choices, but it is actually an empirical hypothesis. Recommend rephrase: "Given these three pieces, we test whether the score-function gradient suffices on Walker2d-v4."

- **Abstract** ("no value function, no replay buffer, no PPO clipping, no entropy bonus, no DAgger") — the DAgger reference is a category error: DAgger is an imitation-learning algorithm that cannot be "a missing trick" in a pure-RL pipeline. Its inclusion in the negative list signals confusion to a reviewer familiar with imitation learning. **Remove DAgger from both the abstract and §3.4 ("What is absent").**

- **§3.4 ("What is absent")** lists "no DAgger correction" — same issue as above. DAgger requires expert demonstrations; there are none here. Remove this item to avoid signalling category confusion.

- **§3.2** ("at small $\nu$ the heavy tails enable exploratory escape from local plateaus arising at contact-mode boundaries") — "enable" is a causal claim without support. Either cite a specific empirical or theoretical study connecting heavy-tailed distributions to escape from local optima in contact-rich systems, or downgrade to "we conjecture that heavy tails facilitate exploration near contact-mode boundaries."

- **§3.5 Tier I** — framing $\{c_\ell\}$ as "not free choices" derived from physics is only defensible if the derivation is shown. Currently the mapping from torque/velocity envelope to cap values is absent. Either provide the formula or move $\{c_\ell\}$ to Tier II (user-tuned).

---

## D. Novelty risks per literature audit

The literature audit during planning identified these prior-art collisions. The paper's positioning must hold up against each.

- **Tokutake & Yamashita 2019** uses Student-$t$ for actor-critic robot control. Differences claimed in §2: (i) pure REINFORCE (no critic); (ii) state-dependent $\nu(s)$; (iii) soft-min reward (not task return). All three differences are real and §2 names this paper. ✓
- **Garg et al. 2021** characterises heavy-tailed PPO gradients but does NOT propose heavy-tailed policies — different direction. Cited and distinguished in §2. ✓
- **Achiam et al. 2017 (CPO)** is the strongest prior-art risk: a reviewer may insist the soft-min objective is a Lagrangian-CPO collapse. Mitigation in §2 paragraph 2 exists but is one sentence; needs quantifying (see B.4 above).
- **Yoshida & Miyato 2017, Miyato et al. 2018 (spectral norm)** are cited; we use the cheaper Frobenius variant and explain why. ✓
- **Henderson et al. 2018** is in references.bib but not cited in the body. Either cite it or remove it to avoid reviewer confusion about missing citations.
- **Aubin 1991** is cited in §2 for viability theory but is a book from 1991; reviewers may expect a contemporary HJ-reachability citation (e.g., Fisac et al. 2019 or Herbert et al. 2017) to situate the work in the modern safe-RL literature. Consider adding one.

No 3-of-3-component preempting paper found in 2023–2025 literature. The combination is novel; the primitives are not. ✓

---

## E. Empirical risks (what could kill the paper)

These are testable hypotheses. Each should be an explicit hypothesis in the experiment plan.

1. **REINFORCE-Gaussian and MinPG-Gaussian both fail to learn → the mollifier carries everything.** Story still works. Reposition method paragraph slightly; the paper becomes a strong argument for the policy family choice.

2. **MinPG-Student-$t$ fails to match PPO on Walker2d-v4.** Paper becomes a careful negative result; suitable for TMLR or a workshop. The variance bound in §4.3 still holds but the empirical thesis fails.

3. **PPO-with-soft-min-reward outperforms MinPG.** The main contribution becomes the reward formulation, not the algorithm. Restructure around the soft-min objective and compare PPO/SAC variants using it.

4. **Capacity clamp is unnecessary** (Frobenius bound never binds in practice during Walker2d-v4 training). Drop component 3, simplify; the variance bound in §4.3 weakens but Lemma 1 still holds.

5. **The smoothness lemma's hypotheses fail in practice** — e.g., Walker2d's terminate-on-fall reward shaping introduces an unbounded margin spike that violates the Lipschitz $L_Q$ assumption in Lemma 1. Discussion §7.2 partially acknowledges this; experiments should check whether any episode terminates with an extreme margin value.

6. **Hyperparameter sensitivity sweep (§6.3) reveals MinPG is brittle to $\beta$** — if performance varies by more than 2× across the $\beta \in \{1,10,100\}$ sweep, the soft-min design is less clean than claimed. This should be treated as a risk, not merely a sensitivity study.

---

## F. Suggested rewrites before submission

Concrete edits, in priority order:

1. **Remove DAgger from negative list (C.2, C.3).** Two-line cleanup in abstract and §3.4. Highest priority: it signals a category error and costs no content.

2. **Soften §1 paragraph 3 "sufficient" claim (C.1, B.2).** Change "the score-function gradient is sufficient" → "we test whether the score-function gradient suffices on Walker2d-v4." About 12 words of change.

3. **Address state-dependent $\nu(s)$ mechanism (B.1).** Either weaken §3.2 exploration claim to a conjecture or add a contact-count input feature. Adding the feature is cleaner; weakening is faster for submission.

4. **Rewrite §3.2 exploration claim with proper hedging (C.4).** "at small $\nu$ the heavy tails enable…" → "at small $\nu$ the heavy tails may facilitate…; we measure whether $\nu(s)$ correlates with foot-contact rate in §6."

5. **Quantify the CPO distinction (B.4).** Add a 2-sentence note about gradient direction in §2 paragraph 2.

6. **Either derive $\{c_\ell\}$ from physics or move to Tier II (C.5).** Provide the formula (torque-limit to Frobenius cap) or remove the "not a free choice" framing.

7. **Add observation-bound assumption to Lemma 2 (B.5).** One line: "$\|s\| \le S_{\max}$ for Walker2d-v4 by joint and velocity limits (cite gymnasium env spec)."

8. **Verify Walker2d-v4 reward scale (Claim #10).** One simulator call: run a random policy for 1000 steps and measure cumulative return. Set the variance-comparison numbers in §4.3 to confirmed values.

9. **Resolve learning rate bound (B.3).** Provide the convergence argument or replace the $1/\gamma$ rule with a practical tuning guideline.

10. **Cite or remove Henderson et al. 2018 from bib (D.5).** If not cited, remove to keep the bibliography tight.

(After these are addressed, Tasks 11 and 12 of the plan perform a literature cross-check and an algorithm-vs-theory cross-check, which may surface additional small fixes.)

---

## G. Status

- Paper draft compiles cleanly: **7 pages**, 0 errors, 0 undefined refs, 0 overfull boxes (Task 9 verification).
- All bibliography entries in references.bib: 17 entries. `henderson2018` appears in the bib but is not cited in any section body — either cite it or remove it before submission.
- Experiments section uses `TBD` placeholders for all numerical cells: 24 TBD entries across 2 tables (Table 1: 4 methods × 4 checkpoints = 16; Table 2: 4 configurations × 2 reward columns = 8). Page count will increase when those land.
- Branch: `paper-minimalist`. Last commit before SELF_REVIEW: `9161cce` (Task 9 compile verification / discussion).
- Section count: 7 sections (Introduction, Related work, Method, Theory, Experiments, Discussion) + Abstract + Algorithm box + 2 Lemmas + 1 Remark + 2 Tables.
- Critical path to submission: (1) run experiments to fill TBD cells; (2) apply F.1–F.4 before any external read; (3) apply F.5–F.10 before camera-ready.
