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

## H. Literature audit cross-check (Task 11)

- **Total `\cite` keys used in draft:** 16 (across sections/*.tex and main.tex)
- **Total entries in `references.bib`:** 17
- **Dead references (in bib, never cited):** `henderson2018` — as flagged in D.5 above.
- **All cited keys resolve in bib:** YES — every one of the 16 cited keys has a matching `@` entry.

### Year / venue / author verification

- **tokutake2019** — VERIFIED. Springer Link confirms "Student-t policy in reinforcement learning to acquire global optimum of robot control," Applied Intelligence, published June 2019. Authors Tokutake & Yamashita. Title, year, journal match exactly. ✓
- **garg2021heavytails** — VERIFIED. ICML 2021 proceedings (mlr.press/v139/garg21b.html); Spotlight talk confirmed. Full author list matches bib entry (Garg, Zhanson, Parisotto, Prasad, Kolter, Lipton, Balakrishnan, Salakhutdinov, Ravikumar). Title matches exactly. ✓
- **engstrom2020** — VERIFIED. Appears in ICLR 2020 proceedings (iclr.cc/virtual_2020/poster_r1etN1rtPB.html; OpenReview r1etN1rtPB). Note: there is a separate arXiv version 2005.12729 titled slightly differently ("Deep Policy Gradients" instead of "Deep RL") — but the official ICLR 2020 publication uses the bib title "Implementation Matters in Deep RL." Bib entry is correct. ✓
- **andrychowicz2021** — VERIFIED. ICLR 2021, Oral/Spotlight (openreview.net/forum?id=nIAxjsniDzg; dblp AndrychowiczRSO21). Title "What Matters for On-Policy Deep Actor-Critic Methods? A Large-Scale Study" matches. Note: the bib title says "What Matters for On-Policy Deep Actor-Critic Methods?" — the ICLR listing adds a question mark and "A Large-Scale Study"; bib matches. ✓
- **oquab2024dinov2** — VERIFIED. Published in Transactions on Machine Learning Research (TMLR), accepted January 2024 (openreview.net/forum?id=a68SUt6zFt). Author list and title match. ✓
- **hwangbo2019anymal** — VERIFIED. Science Robotics, DOI 10.1126/scirobotics.aau5872, 2019. Authors Hwangbo, Lee, Dosovitskiy, Bellicoso, Tsounis, Koltun, Hutter match. Title "Learning agile and dynamic motor skills for legged robots" matches; bib entry is correct (note: bib has volume=4, number=26 which corresponds to the article number eaau5872 — plausible for Science Robotics Vol. 4). ✓
- **henderson2018** — NOT CITED; bib entry itself is accurate (Henderson et al., AAAI 2018, "Deep Reinforcement Learning that Matters"). No factual error; simply unused.
- **schulman2017ppo, haarnoja2018sac, williams1992, achiam2017cpo, aubin1991, yoshida2017spectral, miyato2018spectral, todorov2012mujoco, gymnasium2023, folland1999real** — standard well-known references; titles, years, and venues are consistent with widely-used citations in the RL literature. No discrepancies identified. [verify: venue for schulman2017ppo is listed as "arXiv preprint arXiv:1707.06347" — PPO was never formally published at a conference; arXiv listing is the canonical reference. ✓ intentional.]

### Missing citations a reviewer would expect

1. **Stable-Baselines3** — §6.1 ("Baselines" paragraph) names "Stable-Baselines3" as the baseline implementation but provides no citation. Raffin et al. (2021), "Stable-Baselines3: Reliable Reinforcement Learning Implementations," JMLR 22(268):1–8, is the standard reference and should be added. **File:** `sections/experiments.tex`, §6.1 baseline paragraph.

2. **Hamilton–Jacobi reachability** — §2 ("Safe RL and margin-based reward" paragraph) mentions "the Hamilton–Jacobi reachability literature" with no citation. Bansal et al. 2017 ("Hamilton-Jacobi reachability: A brief overview and recent advances," IEEE CDC 2017) is the standard survey citation here. **File:** `sections/related_work.tex`, line ~21.

3. **REINFORCE with normalization / recent pure-PG variants** — §2 paragraph 3 states "Subsequent work in language-model fine-tuning has shown pure score-function methods can match clipped surrogates in discrete-text regimes" with no citation. This sentence invites a reviewer to demand references (e.g., REINFORCE++, GRPO). Either cite specific papers or remove the sentence. **File:** `sections/related_work.tex`, final sentence of "Implementation matters" paragraph.

4. **DINOv2 citation placement** — `oquab2024dinov2` is cited in §2 ("What we are not") in a sentence that positions DINOv2 as "complementary" work the paper neither uses nor competes with. This is a legitimate defensive citation; no omission. However, it may draw reviewer attention to a perceived scope mismatch (vision encoder in a proprioceptive-only locomotion paper). Risk is positional, not factual.

5. **Walker2d-v4 reward function** — §4.3 compares variance of soft-min vs. task return and states "default per-step task return ranges over O(1)." No citation or measurement supports this. A reviewer may request either a Gymnasium source reference for the Walker2d reward function or a measurement. **File:** `sections/theory.tex`, variance comparison paragraph.

### Risk citations (papers that could be claimed as preempting our work)

- **tokutake2019** — distinguished in §2.1 (pure REINFORCE vs. actor-critic; state-dependent ν; soft-min objective). ✓
- **garg2021heavytails** — distinguished in §2.1 (characterises gradients, does not propose heavy-tailed policies). ✓
- **achiam2017cpo** — distinguished in §2.2 by one sentence (Lagrangian vs. objective). Thin but present; see B.4 for recommended expansion.
- **engstrom2020, andrychowicz2021** — framed correctly as motivation ("tricks matter"; we ask converse). ✓

### Recommendations

1. **Add `raffin2021sb3` to bib and cite it in §6.1** — "Stable-Baselines3" is named without attribution; this is a clear missing citation that any reviewer would flag. Bib entry: Raffin et al., JMLR 2021, vol. 22, no. 268.
2. **Add a HJ-reachability citation in §2** — one sentence mentioning "the Hamilton–Jacobi reachability literature" without a cite is a gap. Add Bansal et al. 2017 (IEEE CDC) or Herbert et al. 2017 as the standard pointer.
3. **Either cite the LM-finetuning pure-PG work or remove that sentence** — the "language-model fine-tuning" sentence in §2 is uncited and could frustrate a reviewer expecting REINFORCE++ / GRPO references.
4. **Keep `henderson2018` in bib but note it as dead** — removing it is fine for camera-ready; keeping it is fine for a draft. Do not cite it gratuitously.
5. **Verify Walker2d-v4 reward scale empirically** — the O(1) per-step / O(10³) cumulative claim in §4.3 should be grounded by a simulator measurement or a Gymnasium env-spec reference.

---

## I. Algorithm + math cross-check (Task 12)

### I.1 alg:minpg vs monograph alg:loco

Source: `sections/calculus.tex` lines 1276–1368 (monograph `alg:loco`) vs
`paper_minimalist/sections/method.tex` Algorithm 1 (`alg:minpg`).

| Monograph alg:loco element | MinPG counterpart | Status | Notes |
|---|---|---|---|
| Phase loop (Stand / Walk / Work curriculum) | (none) | Dropped | Curriculum is out of scope; MinPG is single-phase, no phase-gating. |
| `\varphi_{\mathrm{vis}}(I_t)` — DINOv2 frozen vision encoder | (none) | Dropped | Walker2d-v4 is proprioceptive-only ($n_s = 17$); no image input. |
| Demonstrations `D` for Work phase | (none) | Dropped | No imitation loss in MinPG; `D = ∅` throughout. |
| `u ~ U` command sampling per rollout | (none) | Dropped | Walker2d has a single fixed-speed task; no command distribution. |
| Truncated Student-$t$ action sample `τ_t ~ π_θ(· | o_t, u)` | Algorithm 1 line 3 | Same | Identical policy family; truncation and score-function philosophy unchanged. |
| `softmin_β` viability margin (height, orientation, foot-z for go2) | §3.1 eq. (1) + §6.1 instantiation | Adapted | Walker2d uses 3 margins: torso height, pitch angle, foot clearance. Quadruped-specific `‖R_t − I‖_F` orientation replaced by scalar pitch for biped. |
| Score-function gradient `s_t = ∇_θ log π_θ(τ_t | o_t, u)` | Algorithm 1 line 5 | Same | Stops gradient at engine; score through `π` only. |
| Weight update with L2 decay `W_ℓ ← W_ℓ + η[∇W_ℓ − γW_ℓ]` | (none; hard projection instead) | Different | MinPG replaces soft L2 decay with hard Frobenius projection eq. (3). Justified in §3.3: projection is sharper and admits a clean closed form. |
| Capacity clamp `‖W_ℓ‖_F ← min(‖W_ℓ‖_F, c_max(e_ℓ))` | Algorithm 1 line 7 | Same | Same projection step; caps sourced from per-layer XML limits vs. per-actuator torque envelope. |
| In-episode reset on fall (`|φ|_β ≤ 0`) | (none) | Dropped | Standard Gymnasium episode-end termination replaces in-episode weight reinitialisation; no mid-episode hard reset of parameters. |
| Imitation margin augmentation `softmin(|φ|_β, ε − ‖τ_t − τ_t*‖)` | (none) | Dropped | Pure margin objective; no demonstration-following term. |
| MuJoCo engine `mj_step` (MJX/JAX) | Walker2d-v4 step (Gymnasium / MuJoCo) | Adapted | Same gradient-stops-at-engine philosophy; engine call unchanged in spirit. |
| Convergence criterion: `max|φ| = min|C|` for N consecutive rollouts | Epoch loop (no explicit criterion) | Adapted | MinPG runs for a fixed number of epochs; no formal convergence check (appropriate for benchmark comparison). |

**Verdict:** All differences are intentional and consistent with the standalone-paper scope (single-task, proprioceptive, benchmark). No accidental semantic drift detected. The weight-decay-vs-projection difference is the one design departure worth documenting in §3.3 (it is already noted there but not cross-referenced to the monograph).

### I.2 Lemma hypothesis consistency

**Lemma 1 (Mollifier smoothness) — hypothesis: `σ > 0` and `ν > 2`**

- Method §3.2 outputs `(μ, log σ, log ν)` as three network heads. The actual `ν(s)` is `exp(head)`, which is positive but **unconstrained below**: as the head → −∞, `ν(s) → 0`. No architecture or loss term enforces `ν(s) > 2`.
- Consequence: Lemma 1's hypothesis can fail at any state where the network outputs a sufficiently negative `log ν` head. The proof sketch explicitly requires `ν > 2` for "finite second moment of the score via the Fisher information formula for the Student-$t$ family" — this is mathematically necessary, not just sufficient. Weakening to `ν > 1` would be incorrect (Fisher information for μ in the Student-t family is finite iff ν > 2).
- **Severity: Medium.** The algorithm as written does not guarantee Lemma 1 holds for all reachable states.
- **Recommended fix (method.tex, not theory.tex):** Replace the `log ν` head with a `softplus + 2` transform: `ν(s) = 2 + softplus(head)`, so `ν(s) ∈ (2, ∞)` always. This is a one-line change in §3.2 and Algorithm 1. The lemma hypothesis is then satisfied by construction.
- **theory.tex fix: NOT applied.** Weakening to `ν > 1` would be mathematically wrong (see above). Strengthening the hypothesis statement (e.g., adding "enforced by a softplus + 2 output transform") requires coordinating with method.tex; left as a recommended fix in F.3/F.7 rather than a silent edit.
- This inconsistency is already partially captured in section F (item 3 mentions the ν(s) mechanism), but the direct link to Lemma 1's formal hypothesis was not previously flagged.

**Lemma 2 (Bounded score under clamp) — depends on `‖s‖` bounded**

- Lemma 2 invokes `‖s‖` in the proof sketch: "`σ` bounded below by `exp(−Σ_ℓ c_ℓ ‖s‖)`". This bound is vacuous if `‖s‖ = ∞`.
- The lemma statement does not explicitly assume `‖s‖ ≤ S_max`; the bound `C` is stated as depending on "`the input bound ‖s‖`" but no value or justification is given.
- For Walker2d-v4 the observation is bounded by simulator constraints: joint angles are clipped by MuJoCo joint limits, velocities are bounded by contact dissipation, torso height is bounded by gravity. The observation vector is therefore bounded for all reachable states, but the paper does not state this.
- **Severity: Low (for Walker2d-v4 specifically).** The bound holds in practice; it just needs to be stated.
- **Recommended fix:** Add one sentence to Lemma 2 statement: "Assume `‖s‖ ≤ S_max` for all reachable states (satisfied for Walker2d-v4 by joint and velocity limits; see §6.1)." This is already flagged in F.7 and B.5 above.

### I.3 Variance bound algebra

§4.3 claims `Var(g^hat) ≤ M² H C`. Re-derivation:

- `g^hat = J_β(τ) · Σ_t ∇_θ log π_θ(a_t | s_t)` where `s_t = ∇_θ log π_θ(a_t | s_t)` is the per-step score.
- `J_β ∈ [−M, 0]` deterministically given the trajectory, so `|J_β|² ≤ M²`.
- By Cauchy–Schwarz: `‖Σ_{t=0}^H s_t‖² ≤ (H+1) Σ_{t=0}^H ‖s_t‖²`. Treating H+1 ≈ H for large H, this gives the linear-in-H factor.
- `E[‖s_t‖²] ≤ C` by Lemma 2 (conditionally on `ν(s) > 2` — see I.2).
- Therefore `Var(g^hat) ≤ E[‖g^hat‖²] ≤ M² · H · H · C / H = M² H C`.

Wait — more carefully: `E[‖g^hat‖²] ≤ M² · E[‖Σ_t s_t‖²] ≤ M² · H · E[Σ_t ‖s_t‖²] ≤ M² · H · H · C`. That is `M² H² C`, not `M² H C`. The paper writes `M² H C` — the algebra as written appears to be off by a factor of H.

Re-check: Cauchy–Schwarz gives `‖Σ_t s_t‖² ≤ (H+1) Σ_t ‖s_t‖²`. So `E[‖Σ_t s_t‖²] ≤ H · H · C = H² C`. Hence `E[‖g^hat‖²] ≤ M² H² C`. The variance bound should read `M² H² C`, not `M² H C`.

**Correction:** The variance bound in §4.3 eq. (variance-bound) loses one factor of H. The correct Cauchy–Schwarz bound is `Var(g^hat) ≤ M² H² C`. This is still finite without a baseline (the key qualitative claim holds), but the quantitative exponent is H² not H.

**Consequence for the paper:** The comparison paragraph in §4.3 ("order-10³ reduction") is comparing `M² H C` against a task-return estimator with scale `(cumulative return)² ≈ O(10⁶)` for H = 1000. With the corrected bound `M² H² C`, the soft-min bound is `O(H²)` = `O(10⁶)` for H = 1000 — the same order as the task-return estimator. The claimed "order-10³ reduction" disappears. This is a material error in §4.3.

**Severity: High.** The variance comparison paragraph's central quantitative claim is based on an incorrect exponent. The paragraph needs to be rewritten or the bound strengthened. (The qualitative claim — "finite without baseline" — still holds, but the quantitative advantage claim does not.)

### I.4 Final verdict

| Item | Status | Severity |
|---|---|---|
| alg:minpg vs alg:loco: all differences intentional | PASS | — |
| Lemma 1 `ν > 2` not enforced by algorithm | FLAG | Medium |
| Lemma 2 observation bound not stated | FLAG | Low |
| Variance bound exponent: H² not H in §4.3 | ERROR | High |

- **Algorithm extraction:** correctly derived from alg:loco; all differences are intentional simplifications for the Walker2d / standalone scope.
- **Lemma 1:** holds conditionally on `ν(s) > 2`. The algorithm does not enforce this. Fix: add `softplus + 2` transform on the `log ν` head in §3.2 / Algorithm 1.
- **Lemma 2:** holds conditionally on `‖s‖ ≤ S_max`. Satisfied by Walker2d-v4 physics, but must be stated explicitly.
- **Variance bound:** the H² vs H discrepancy is a mathematical error that undermines the quantitative comparison in §4.3. Requires a rewrite of that paragraph or a corrected proof. The qualitative finiteness result is unaffected.

---

## J. Status

- Paper draft compiles cleanly: **7 pages**, 0 errors, 0 undefined refs, 0 overfull boxes (Task 9 verification).
- All bibliography entries in references.bib: 17 entries. `henderson2018` appears in the bib but is not cited in any section body — either cite it or remove it before submission.
- Experiments section uses `TBD` placeholders for all numerical cells: 24 TBD entries across 2 tables (Table 1: 4 methods × 4 checkpoints = 16; Table 2: 4 configurations × 2 reward columns = 8). Page count will increase when those land.
- Branch: `paper-minimalist`. Last commit before SELF_REVIEW: `9161cce` (Task 9 compile verification / discussion).
- Section count: 7 sections (Introduction, Related work, Method, Theory, Experiments, Discussion) + Abstract + Algorithm box + 2 Lemmas + 1 Remark + 2 Tables.
- Critical path to submission: (1) run experiments to fill TBD cells; (2) apply F.1–F.4 before any external read; (3) apply F.5–F.10 before camera-ready.
