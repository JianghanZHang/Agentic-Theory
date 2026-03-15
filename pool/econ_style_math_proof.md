# The Sword Is the Mean: A Self-Contained Proof in Economics Language

**For readers with training in Economics and Mathematics.**
No physics background required. All concepts are stated in terms of
dynamic optimisation, principal-agent theory, game theory, and network flows.

---

## Setup

### Primitives

| Symbol | Meaning |
|--------|---------|
| $S$ | State space (all possible configurations of the system) |
| $K \subset S$ | **Feasible set**: the set of states in which the principal retains authority |
| $n$ | Number of agents |
| $U_i \subseteq \mathbb{R}^{d_i}$ | **Action set** of agent $i$ (what agent $i$ can do independently) |
| $\kappa$ | The **principal** (the "king"—a single sovereign decision-maker) |
| $\text{Obs}$ | The principal's **monitoring function** (finite bandwidth: can observe at most $B$ agents) |
| $\bar{U}$ | **Mean autonomous capability**: $\bar{U} = \frac{1}{n}\sum_{i=1}^n \|U_i\|$, where $\|U_i\| = \dim(\text{span}(U_i))$ |

### The System Dynamics

The system evolves in continuous time. At each instant, every agent $i$ picks an action $u_i \in U_i$. The state velocity is:

$$x'(t) \in F(x(t)) := \left\{ \sum_i f_i(x, u_i) : u_i \in U_i \right\}$$

This is a **differential game**: the transition is not a single-valued function but a **correspondence** (set-valued map), because multiple agents choose simultaneously. The principal does not know which action each agent will pick—only that it comes from $U_i$.

Think of it as a continuous-time version of a simultaneous-move game where the state evolves as the sum of everyone's choices.

---

## Axiom 1 (Viability — the "No-Ponzi Condition")

> **For every state $s \in K$, there exists a feasible trajectory $\gamma: [0, \infty) \to K$ with $\gamma(0) = s$.**

In plain language: from any current state, the principal must be able to survive **forever**. There must always exist at least one path that keeps the system inside the feasible set $K$ for all future time.

**Economics analogy.** This is the sovereign-survival version of the **transversality condition** in infinite-horizon optimisation. Just as the transversality condition rules out Ponzi schemes (you can't borrow your way to infinity), the viability axiom rules out states from which no infinite survival path exists. The **viability kernel** $\text{Viab}(K) \subseteq K$ is the largest subset of $K$ from which such a path exists—the set of genuinely sustainable states.

The key technical result (Aubin's Viability Theorem) says: a viable trajectory exists from every $s \in K$ **if and only if** at every state, the set of feasible velocities contains at least one direction that keeps you inside $K$:

$$\forall x \in K: \quad F(x) \cap T_K(x) \neq \varnothing \tag{Tangential Condition}$$

where $T_K(x)$ is the set of directions at $x$ along which you can move without immediately leaving $K$.

This is the infinite-horizon feasibility constraint. Violate it at any point, and the system exits $K$ in finite time—the principal loses authority.

## Axiom 2 (Massless Agents — No Intrinsic Bargaining Weight)

> **An agent's threat capacity is determined entirely by its position in the system (its action set and its connectivity to the principal), not by any intrinsic property.**

**Economics analogy.** This is like assuming no agent has intrinsic bargaining weight—all power comes from **outside options** (what you can do independently). Two agents with the same action set and same network position are interchangeable. There is no "personal charisma" variable; only structural capability matters.

**Formal consequence.** The baseline against which "excess capability" is measured must be the mean $\bar{U}$. Why? Because if agents carry no intrinsic weight, then deviations from any baseline $b$ must sum to zero: $\sum_i (\|U_i\| - b) = 0$, which forces $b = \bar{U}$. Any other baseline would create a systematic bias.

---

## Definition: The Sword (= Credible Threat)

> **An agent $r$ is a *sword* if and only if two conditions hold simultaneously:**
> 1. **Independent capability**: $U_r \neq \varnothing$ — the agent can take actions that do not require the principal's authorisation.
> 2. **Observability**: $r \in \text{Im}(\text{Obs})$ — the principal can detect the agent's capability.

**Condition (1)** is about **outside options**: can you act without the principal's approval? If your entire execution chain requires the principal's sign-off at some point (a "breakpoint"), you cannot act independently, and $U_r = \varnothing$ in the relevant sense.

**Condition (2)** is about **information**: does the principal know you have this capability? An unobserved capable agent is a *pre-sword*—dangerous but outside the principal's strategy space (you can't respond to what you can't see).

**Neither condition alone is sufficient.** Capability without observability is invisible risk. Observability without capability is not a threat.

---

## Theorem 1: Binary Lifecycle (No Third Option)

> **Every sword has exactly two possible outcomes:**
> - **(a) Voluntary relinquishment**: the agent gives up independent capability ($U_r \to \varnothing$).
> - **(b) Forced elimination**: the principal removes the agent using superior control.
>
> **There is no path (c).**

### Proof

**Step 1 (Forcing Lemma).** Suppose the sword persists: both conditions hold for all $t \geq t_0$. The principal must maintain the tangential condition $F(x) \cap T_K(x) \neq \varnothing$ at every instant. Since agent $r$ acts independently, the principal cannot predict which $u_r \in U_r$ the agent will choose. The principal must therefore maintain a **reactive compensation** at every instant—allocating control effort $u^*(t)$ to counteract whatever $r$ does.

The cost of this compensation per unit time is strictly positive (because $r$'s independent actions can push the state toward the boundary of $K$). Over an infinite horizon:

$$\int_{t_0}^{T} \|u^*(t)\| \, dt \to \infty \quad \text{as } T \to \infty$$

**This is the key economic argument**: the present value of indefinite threat-compensation is unbounded. Just as a firm cannot sustain an indefinite cash drain, the principal cannot sustain an indefinite viability cost.

**Step 2 (Exhaustive classification).** The sword persists as long as both conditions hold. Resolution requires at least one condition to fail:

- Condition (1) fails → agent gives up independent capability → **path (a)**.
- Condition (2) fails → agent becomes unobservable → this is not resolution but **deferral** (a sword → pre-sword regression). The agent's capability persists; any future expansion of monitoring re-detects the agent and restarts the clock. The causal envelope does not shrink.
- If neither condition fails voluntarily, the forcing lemma applies: the unbounded cost forces the principal to act. The principal eliminates the agent using superior control → **path (b)**.

The classification is exhaustive. $\blacksquare$

**Economics interpretation.** Think of the sword as an agent with a **credible outside option** that the principal can observe. The principal faces a hold-up problem with unbounded duration cost. The only stable equilibria are: (a) the agent credibly commits to abandoning the outside option, or (b) the principal terminates the relationship. "Trust me, I won't use it" is not a stable equilibrium—see Theorem 2.

---

## Theorem 2: Fixed-Point Impossibility (You Can't Prove Your Sword Is Not a Sword)

> **There is no strategy that "proves your sword is not a sword" while retaining the sword.**
>
> Formally: the map $T: U_r \mapsto \varnothing$ conditional on $U_r \neq \varnothing$ has no fixed point other than $U_r = \varnothing$.

### Proof

**Case 1**: $U_r = \varnothing$. The agent has no independent capability. No proof is needed—the condition is self-certifying.

**Case 2**: $U_r \neq \varnothing$. The sword criterion tests **physical capability**, not **declared intention**. No speech act, promise, or signal can set $U_r \to \varnothing$ while the capability physically persists. The only way to satisfy $T(U_r) = \varnothing$ is to physically relinquish $U_r$—which is path (a).

Moreover, the act of proving itself is a signal: "I need to prove my sword is not a sword" implies suspicion, confirming that $r \in \text{Im}(\text{Obs})$ (condition 2 is reinforced by the attempt to deny it).

$\blacksquare$

**Economics interpretation.** This is a **cheap talk impossibility result**. In the language of mechanism design: when the mechanism screens on capability (a hard variable) rather than intent (a soft variable), no cheap-talk message can change the outcome. The only credible signal is costly—physically giving up the capability. Compare: in a Spence signalling model, you can't signal low ability by saying "I'm low ability"—the signal must be costly. Here, the only costly-enough signal is relinquishment itself.

---

## Theorem 3: Unconstrained Power Paradox

> **If the principal has maximum control ($U = U_{\max}$), the principal must preemptively eliminate every observable autonomous agent:**
>
> $$U = U_{\max} \implies \text{the principal must eliminate all } r \text{ with } U_r \neq \varnothing \wedge r \in \text{Im}(\text{Obs})$$

### Proof

$U_{\max}$ means the principal tolerates **no** autonomous actuation: every such agent is a boundary threat on $\text{Viab}(K)$.

Furthermore, imperfect observability **intensifies** the paradox:

1. The principal knows $\text{Obs}$ is imperfect. Hidden swords are more dangerous than visible ones. The principal has motive and capability to expand $\text{Obs}$.
2. Expanding $\text{Obs}$ does not "discover existing swords"—it **creates new ones** by definition. A hidden agent satisfying condition (1) enters $\text{Im}(\text{Obs})$ upon expansion → both conditions now satisfied → it **becomes** a sword.
3. Positive feedback: more power → more monitoring → more detected swords → more elimination → repeat.

**The unconstrained principal is not free—it is a perpetual elimination machine.**

$\blacksquare$

**Economics interpretation.** This is a **regulatory paradox**: the more authority a regulator has, the more entities it must regulate, because its expanded detection creates new violations. Compare: a tax authority that audits more aggressively doesn't just find existing tax evaders—it reclassifies previously-tolerated arrangements as evasion. The system generates its own workload.

---

## Theorem 4: The Sword Is the Mean (The Central Result)

> **An agent $r$ is a sword if and only if:**
>
> $$U_r \neq \varnothing \quad \text{and} \quad \|U_r\| > \bar{U} + \tau(\text{Obs})$$
>
> **where $\bar{U} = \frac{1}{n}\sum_{i=1}^n \|U_i\|$ is the mean autonomous capability and $\tau(\text{Obs})$ is the detection threshold determined by the principal's monitoring bandwidth.**
>
> **Consequently, regime change is a shift in $\bar{U}$, not a change in any individual $\|U_r\|$.**

### Proof

**Step 1 (Optimal monitoring is a threshold rule).**
The principal has finite monitoring bandwidth $B$: it can observe at most $B$ agents simultaneously. Under the viability axiom, the principal must allocate monitoring to maximise survival probability. The threat from agent $r$ is proportional to $\|U_r\|$ (the dimension of its autonomous action set).

By the massless axiom, the unique unbiased baseline is $\bar{U}$ (proved above: deviations must net to zero). Agents at or below $\bar{U}$ are indistinguishable from the collective and pose zero marginal threat. The **optimal allocation** monitors the $B$ agents with the largest deviation $\|U_r\| - \bar{U}$.

This is a standard **resource allocation under constraint** result: with limited monitoring budget, you monitor the highest-risk agents, where risk is measured by deviation from the population mean. The threshold $\tau(B)$ is the $(n-B)$-th order statistic of $\{\|U_i\| - \bar{U}\}$.

**Step 2 (Substitution).** The sword criterion requires:
1. $U_r \neq \varnothing$ (unchanged)
2. $r \in \text{Im}(\text{Obs})$

By Step 1, condition (2) is equivalent to $\|U_r\| - \bar{U} > \tau(\text{Obs})$. Substituting:

$$r \text{ is a sword} \iff U_r \neq \varnothing \;\wedge\; \|U_r\| > \bar{U} + \tau(\text{Obs})$$

**Step 3 (Regime change is a mean shift).** Let $\bar{U}_1$ be the mean before a regime change and $\bar{U}_2 < \bar{U}_1$ the mean after (e.g., wartime → peacetime demobilisation). An agent with fixed capability $\|U_r\|$ satisfying:

$$\bar{U}_2 + \tau < \|U_r\| \leq \bar{U}_1 + \tau$$

is **not a sword** in regime 1, but **becomes a sword** in regime 2. The agent changed nothing. The mean shifted.

$\blacksquare$

### Economics Interpretation

This is an **endogenous threshold model**:

1. **Efficiency wage analogy.** Whether a worker's wage is "high" depends not on the absolute number but on its deviation from the market average. A salary of \$200k is unremarkable in finance but anomalous in a non-profit—same number, different mean, different classification.

2. **Systemic importance in finance.** A bank is "systemically important" (SIFI) not because of its absolute size but because of its size relative to the system. The SIFI threshold shifts as the industry consolidates or fragments. A mid-size bank can become systemically important without growing—if its competitors shrink.

3. **Exchange rate regime change.** A firm's dollar-denominated debt is manageable under a fixed exchange rate (high $\bar{U}$—everyone is similarly exposed). When the peg breaks (regime change, $\bar{U}$ drops), the same debt becomes a systemic risk. The firm did nothing; the reference frame moved.

**Key implication — the paradox as feedback loop:**

As the principal eliminates swords, $\bar{U}$ drops (you're removing the high-capability agents from the average). The threshold $\bar{U} + \tau$ falls. Agents who were below the old threshold now exceed the new one → new swords → more elimination → lower $\bar{U}$ → ...

This is a **positive feedback loop**. In economics terms: the principal faces a **moving goalpost** problem where each enforcement action shifts the enforcement criterion, generating new violations. The system cannot reach a steady state until either (a) all agents have $U_r = \varnothing$ or (b) the principal installs structural constraints (breakpoints—see below).

---

## Corollary: The Breakpoint Criterion

> **An agent $r$ is *not* a sword if and only if its execution chain contains at least one node controlled by the principal (a *breakpoint*):**
>
> $$r \text{ is not a sword} \iff \exists\; v \in \text{execution chain of } r \text{ s.t. } v \text{ is controlled by the principal}$$

### Proof

If a breakpoint exists, the agent cannot execute independently (condition 1 fails)—every action requires passing through a node the principal controls. If no breakpoint exists, the execution chain is closed and the agent can act autonomously (condition 1 holds). Combined with observability, this makes the agent a sword.

$\blacksquare$

**Economics interpretation.** This is the **vertical integration / supply chain** argument: if a firm's production chain requires a component that only the principal controls (a patent, a license, a critical input), the firm cannot act independently. The principal's optimal strategy is not to be the largest producer (maximum actuator) but to be an **essential intermediary** (cut vertex)—the node whose removal disconnects the network.

---

## Corollary: Cut Vertex $\neq$ Maximum Actuator

> **The principal maximises survival by being the essential node in every execution chain (a *cut vertex* in the network), not by being the strongest agent.**

### Proof

A maximum actuator $v^*$ (the strongest agent) suffers from:
1. **Non-scalability**: a single agent cannot cover the full state space.
2. **Single point of failure**: one performance drop collapses the system.
3. **Self-referential paradox**: if the principal is the strongest autonomous actuator, the principal is itself a sword by definition—and cannot perform viability maintenance on itself.

A cut vertex with near-zero personal capability but routing authority over all chains avoids all three problems. The system is scalable (add more agents), fault-tolerant (losing one agent doesn't disconnect the graph), and the principal is structurally distinct from the threats it must manage.

$\blacksquare$

**Economics interpretation.** This is the **platform vs. producer** distinction. Amazon's power comes from being the marketplace (cut vertex), not from being the best seller (maximum actuator). A franchisor's power comes from owning the brand and supply chain (breakpoint), not from running every store. The optimal principal is a **bottleneck**, not a **strongman**.

---

## Historical Validation: Three Agents, One Principal, Same Regime

All three agents below served the same principal (Liu Bang, founder of the Han dynasty, c. 202 BCE) in the same post-unification phase:

| Agent | $U_r$ (Independent Capability) | $\text{Im}(\text{Obs})$ (Observed?) | Classification | Outcome |
|-------|------|------|------|---------|
| **Han Xin** | $\neq \varnothing$ (commanded armies that obeyed *him*, not the principal) | Yes (famous victories) | **Sword** | Eliminated (path b) |
| **Xiao He** | $\neq \varnothing$ (controlled grain supply and capital administration) | Yes → deliberately reduced (self-corruption) | **Sword → pre-sword regression** | Survived (exited condition 2) |
| **Zhang Liang** | $= \varnothing$ (pure strategist—advice requires principal's army to execute) | Yes (but irrelevant since condition 1 fails) | **Not a sword** | Survived (condition 1 never held) |

**What the framework predicts:**
- Han Xin: both conditions met → binary lifecycle → since he did not relinquish (path a), elimination (path b) followed. Historically: executed.
- Xiao He: both conditions initially met → he deliberately degraded his observability (self-corruption = pulling $\|U_r\|$ toward $\bar{U}$, falling below detection threshold). This is **not** path (c); it is a transition out of the sword classification. Historically: survived, but the principal remained suspicious (the causal envelope persists).
- Zhang Liang: condition 1 never met (his counsel was a pure function—required the principal's apparatus to execute). Not a sword. Historically: retired peacefully.

The framework correctly classifies all three agents and predicts their outcomes from two binary conditions.

---

---

## Instantiation in Standard Economic Models

The framework above is abstract. Below, we instantiate it in six concrete economic models—mapping every primitive, showing how each theorem bites, and writing the key equations in each model's own notation.

---

### Model 1: Real Business Cycle (RBC) with Heterogeneous Firms

**Reference models.** Kydland & Prescott (1982) for the baseline RBC; Hopenhayn (1992) for heterogeneous firms; Acemoglu, Carvalho, Ozdaglar & Tahbaz-Salehi (2012) for network propagation.

#### Mapping

| Framework | RBC Instantiation |
|-----------|-------------------|
| State space $S$ | $(K_t, z_t, \{z_{it}\}_{i=1}^n)$ — aggregate capital, aggregate TFP, firm-level productivities |
| Feasible set $K$ | The set of states from which a balanced growth path exists: $K = \{(K, z) : \exists \text{ feasible path s.t. } \lim_{t\to\infty} \beta^t u'(c_t) K_t = 0\}$ |
| Principal $\kappa$ | The **social planner** (or equivalently, the representative household in the decentralised equilibrium) |
| Agent $i$ | Firm $i$ with production function $y_i = z_i f(k_i, l_i)$ |
| Action set $U_i$ | Firm $i$'s **autonomous investment and production decisions**: $U_i = \{(k_i, l_i) : k_i \leq \bar{k}_i,\; l_i \leq \bar{l}_i\}$ |
| $\|U_i\|$ | Firm $i$'s effective degrees of freedom — its **market share** or **input share** in the production network: $\|U_i\| = \alpha_i$ where $\alpha_i$ is firm $i$'s Domar weight (sales / GDP) |
| $\bar{U}$ | Mean Domar weight: $\bar{U} = \frac{1}{n}\sum_i \alpha_i = \frac{1}{n}$ under symmetry |
| Monitoring $\text{Obs}$ | The planner's (or regulator's) ability to observe firm-level productivity and investment decisions. Finite bandwidth $B$ = limited regulatory capacity |
| Viability axiom | **Transversality condition**: $\lim_{t\to\infty} \beta^t u'(c_t) K_t = 0$. From any state, there must exist a feasible consumption-investment path that satisfies this |
| Tangential condition | At every $(K_t, z_t)$, the set of feasible next-period states must contain at least one element inside $K$: $\exists (c_t, i_t) \text{ s.t. } K_{t+1} = (1-\delta)K_t + i_t \in K$ |

#### Why the standard RBC has no swords

Under the standard assumptions—**perfect competition, atomistic firms, complete markets**—every firm is infinitesimal: $\alpha_i = 1/n \to 0$, so $\|U_i\| \approx \bar{U}$ for all $i$. No firm deviates from the mean. The sword condition $\|U_r\| > \bar{U} + \tau$ is never satisfied.

**This is precisely why the standard RBC model has no instability**: it assumes away the possibility of swords by construction. The representative agent assumption is, in the framework's language, the assumption that $\|U_i\| = \bar{U}$ for all $i$—no agent has independent capability that deviates from the mean.

#### When swords appear: Granular economies

Gabaix (2011, *Econometrica*) shows that when the firm size distribution is fat-tailed (Zipf's law), idiosyncratic shocks to large firms do not average out. In the framework's language:

- Firm $r$ has Domar weight $\alpha_r \gg \bar{U} = 1/n$. Example: in the US, the top 100 firms account for ~30% of GDP, so $\alpha_r \approx 0.003$ vs. $\bar{U} \approx 0.0002$ for ~5 million firms.
- Condition (1): $U_r \neq \varnothing$ — the firm makes autonomous investment, pricing, and employment decisions that the planner does not control.
- Condition (2): $\alpha_r - \bar{U} > \tau(\text{Obs})$ — the firm is large enough to be detected (trivially satisfied for firms in the S&P 500).
- **The firm is a sword**: its autonomous decisions can push aggregate output outside $K$ (recession).

**Theorem 1 (Binary Lifecycle) instantiation:** A granular firm that is a sword has two outcomes:
- **(a) Relinquish**: the firm voluntarily reduces its autonomous capability—e.g., submitting to regulation, breaking itself up, accepting government oversight (consent decree). AT&T's 1984 breakup is path (a).
- **(b) Elimination**: the government forces restructuring or dissolution—e.g., Standard Oil (1911), antitrust enforcement.

**Theorem 4 (Mean-field) instantiation:** Whether a firm is "too big to fail" depends on $\bar{U}$, not on absolute size. A firm with $\alpha_r = 0.01$ is not a sword if $\bar{U} = 0.008$ (concentrated industry where many firms are large). The same firm becomes a sword if $\bar{U} = 0.001$ (fragmented industry). **Industry consolidation shifts $\bar{U}$ without any individual firm changing.**

#### The RBC phase transition

The RBC model's response to a **negative TFP shock** $z_t \to z_t - \Delta$ maps to the framework's phase transition:

1. Before the shock: all firms operate near steady state, $\alpha_i \approx \bar{U}$, no swords.
2. The shock hits asymmetrically (some firms are more exposed). Exposed firms' Domar weights rise (they absorb a larger share of declining output). $\bar{U}$ drops (many small firms shrink or exit).
3. Post-shock: the surviving large firm now satisfies $\alpha_r > \bar{U}_{\text{new}} + \tau$ — it has become a sword, not because it grew, but because the mean shrank.
4. The planner faces the binary lifecycle: regulate/restructure (path a/b) or accept unbounded viability cost.

**This is Acemoglu et al. (2012) in one sentence**: in a production network, aggregate volatility does not vanish at rate $1/\sqrt{n}$ when the network is asymmetric, because a few nodes have Domar weights that exceed the mean by orders of magnitude. Those nodes are swords.

---

### Model 2: New Keynesian DSGE

**Reference models.** Galí (2015) textbook NK model; Calvo (1983) pricing; Blanchard & Galí (2007) for divine coincidence breakdown.

#### Mapping

| Framework | New Keynesian Instantiation |
|-----------|----------------------------|
| State space $S$ | $(\pi_t, \tilde{y}_t, i_t)$ — inflation, output gap, nominal interest rate |
| Feasible set $K$ | The **inflation-targeting band**: $K = \{(\pi, \tilde{y}) : |\pi - \pi^*| < \bar{\pi},\; |\tilde{y}| < \bar{y}\}$. The set of states consistent with the central bank's mandate |
| Principal $\kappa$ | **Central bank** |
| Viability axiom | The central bank can always steer the economy back to $(\pi^*, 0)$ from any $(π_t, \tilde{y}_t) \in K$. This is the **determinacy condition** in NK models |
| Tangential condition | At every state, the Taylor rule $i_t = r^n + \phi_\pi (\pi_t - \pi^*) + \phi_y \tilde{y}_t$ must produce a direction that keeps the system inside $K$. Taylor principle ($\phi_\pi > 1$) ensures this |
| Feedback map $C(x)$ | The **Taylor rule**: $C(\pi_t, \tilde{y}_t) = \{i_t : i_t = r^n + \phi_\pi \pi_t + \phi_y \tilde{y}_t,\; i_t \geq 0\}$ |
| Agent $i$ | **Firm $i$** with price-setting power under monopolistic competition |
| Action set $U_i$ | Firm $i$'s **autonomous pricing decision**: when the Calvo lottery allows firm $i$ to reset its price, it chooses $p_i^*$ independently |
| $\|U_i\|$ | Firm $i$'s **pricing power** — its markup $\mu_i = p_i / mc_i$, or equivalently, its market share in the relevant market |
| $\bar{U}$ | Mean pricing power / mean markup across firms: $\bar{U} = \frac{1}{n}\sum_i \mu_i$ |
| $\tau(\text{Obs})$ | Central bank's detection threshold — the minimum markup deviation it can identify and respond to with targeted policy |

#### The NK Phillips Curve as tangential condition

The NK Phillips Curve:

$$\pi_t = \beta \mathbb{E}_t \pi_{t+1} + \kappa \tilde{y}_t$$

is the aggregate expression of the tangential condition. At every state $(\pi_t, \tilde{y}_t)$, the system's velocity $(\dot{\pi}, \dot{\tilde{y}})$ must have a component inside $T_K(x)$ — a direction that keeps inflation and output gap within bounds.

The **Taylor principle** $\phi_\pi > 1$ is the sufficient condition for the tangential condition to hold: the central bank raises the real interest rate more than one-for-one with inflation, ensuring the system is pulled back toward $K$. When $\phi_\pi < 1$, the tangential condition fails — the system can spiral out of $K$ (indeterminacy).

#### Swords in the NK model

**Under standard NK assumptions (monopolistic competition, symmetric firms):** all firms have the same markup $\mu_i = \mu$ for all $i$, so $\|U_i\| = \bar{U}$. No swords. The central bank's Taylor rule is sufficient.

**When swords appear:**

1. **Sector-specific supply shocks** (oil, food, energy): A sector $r$ with inelastic supply experiences a cost-push shock. Its markup spikes: $\mu_r \gg \bar{U}$. The central bank now faces a **divine coincidence breakdown** (Blanchard & Galí 2007): it cannot simultaneously stabilise inflation and output gap.

    In the framework's language: sector $r$ has become a sword. Its autonomous pricing ($U_r \neq \varnothing$, it sets prices independently) pushes inflation outside $K$, and the central bank's Taylor rule cannot compensate without pushing output gap outside $K$. The tangential condition $F(x) \cap T_K(x) \neq \varnothing$ is violated — there is no interest rate that simultaneously satisfies both bounds.

2. **Dominant platform firms** (Big Tech, OPEC): A firm or cartel with sufficient market share can set prices that move aggregate inflation independently of monetary policy. Amazon's effect on CPI, OPEC's effect on energy prices — these are swords in the NK sense.

**Theorem 1 instantiation:**
- **(a) Relinquish**: the sector/firm accepts price controls, regulation, or antitrust action that reduces its autonomous pricing power ($U_r \to \varnothing$). Example: energy price caps during the 2022 European energy crisis.
- **(b) Elimination**: the central bank forces a recession deep enough to break the sector's pricing power (Volcker disinflation 1979–82 is path (b) applied to the wage-price spiral as a collective sword).

**Theorem 4 instantiation:** Whether a sector is a "sword" depends on $\bar{U}$:
- In a **highly competitive economy** (low $\bar{U}$, low average markup), even moderate pricing power is a sword.
- In a **concentrated economy** (high $\bar{U}$, high average markup), the same pricing power is unremarkable.
- **Deregulation** that increases competition lowers $\bar{U}$, potentially turning previously-normal firms into swords — not because they changed, but because the mean shifted.

#### The zero lower bound as viability boundary

The **ZLB constraint** $i_t \geq 0$ shrinks the feedback map:

$$C_{\text{ZLB}}(x) = C(x) \cap \{i \geq 0\}$$

When the economy is in a liquidity trap, $C_{\text{ZLB}}(x)$ may be empty — the central bank cannot lower rates further, the tangential condition fails, and the system exits $K$ (deflationary spiral). The ZLB is where the viability kernel's boundary is reached: the central bank's control set is truncated, and autonomous agents (firms cutting prices, households hoarding cash) act as swords the central bank cannot compensate.

---

### Model 3: Sovereign Debt Sustainability (Reinhart-Rogoff / Arellano)

**Reference models.** Reinhart & Rogoff (2009) for empirical regularities; Arellano (2008) for sovereign default; Barro (1979) tax-smoothing; the paper's own Appendix (GovFi).

#### Mapping

| Framework | Sovereign Debt Instantiation |
|-----------|------------------------------|
| State space $S$ | $(b_t, y_t, r_t)$ — debt-to-GDP ratio, output, interest rate |
| Feasible set $K$ | $K = \{(b, y, r) : b < \bar{b}(y, r)\}$ where $\bar{b}$ is the debt limit beyond which no sustainable fiscal path exists |
| Principal $\kappa$ | **Sovereign government** |
| Viability axiom | **No-Ponzi condition** (intertemporal budget constraint): $\lim_{T\to\infty} \frac{B_T}{\prod_{s=0}^{T}(1+r_s)} \leq 0$. The government must be able to service its debt forever |
| Tangential condition | At every $(b_t, y_t)$, there exists a fiscal policy $(g_t, \tau_t)$ such that $b_{t+1} = \frac{(1+r_t)b_t + g_t - \tau_t y_t}{1+\gamma_t} \in K$ |
| Feedback map $C(x)$ | The set of feasible fiscal adjustments: $C(b_t, y_t) = \{(\tau, g) : b_{t+1}(b_t, y_t, \tau, g) \in K\}$ |
| Agent $i$ | **Bondholder $i$** (domestic bank, foreign central bank, hedge fund) |
| Action set $U_i$ | Bondholder's autonomous decision: buy, hold, or sell sovereign bonds. $U_i = \{-h_i, \ldots, +h_i\}$ where $h_i$ is the size of the holding |
| $\|U_i\|$ | Bondholder's **market share of outstanding debt**: $\|U_i\| = h_i / B$ |
| $\bar{U}$ | Mean holding share: $\bar{U} = 1/n$ under uniform distribution |
| Sword | A bondholder (or coordinated group) whose sell decision can trigger a **self-fulfilling debt crisis** (Cole & Kehoe 2000) |

#### The self-fulfilling crisis as sword dynamics

In Cole & Kehoe (2000), there exists a **crisis zone** $b \in [\underline{b}, \bar{b}]$ where:
- If bondholders roll over debt → government survives → rolling over was rational.
- If bondholders refuse to roll over → government defaults → refusal was rational.

Both are equilibria. In the framework's language:

- The crisis zone is the **boundary of $K$** — the region where the tangential condition depends on agents' choices.
- A bondholder $r$ with $h_r / B > \bar{U} + \tau$ is a sword: its autonomous sell decision can push the government out of $K$ (trigger default) regardless of what the government does.
- **Small, dispersed bondholders** ($h_i \approx 1/n = \bar{U}$) cannot individually trigger a crisis. Only a **large concentrated holder** or a **coordinated group** can.

**Theorem 1 instantiation:**
- **(a)**: The large bondholder voluntarily commits to holding (e.g., a central bank announcing it will not sell — the ECB's "whatever it takes" in 2012 is the central bank de-swordifying itself as a bondholder by committing to buy, not sell).
- **(b)**: The sovereign restructures debt, imposing losses on the large bondholder (Greece 2012 PSI — forced haircuts on private bondholders).

**Theorem 3 (Power Paradox) instantiation:** A sovereign with $U = U_{\max}$ (unlimited fiscal authority, no constitutional constraints on spending) must monitor all bondholders for potential sell-offs. But its unlimited spending itself creates fiscal risk, which increases bond yields, which makes more bondholders potential sellers → the sovereign's own unconstrained power generates the swords it must fight.

**Theorem 4 (Mean-field) instantiation:** Whether a bondholder is a sword depends on the **concentration of debt holdings**:
- When debt is widely held (pension funds, retail investors): $\bar{U}$ is small, $\|U_i\| \approx \bar{U}$, no swords. Debt is safe.
- When holdings concentrate (hedge funds accumulate large positions): $\bar{U}$ stays the same but some $\|U_r\|$ spike → swords appear.
- **Quantitative easing** by central banks shifts the distribution: the central bank absorbs a large share of bonds, becoming the dominant holder. If the central bank later decides to sell (taper tantrum, 2013), it becomes the sword it was designed to prevent.

#### Water dynamics in sovereign debt

The paper's **Du Mu's Theorem** ($w \to 0 \implies \text{pawn} \to \text{sword} \implies \text{system collapses}$) maps directly:

- **Water** $w(t)$ = **fiscal space** = $\bar{b}(y_t, r_t) - b_t$ (distance between current debt and the debt limit).
- As the government borrows more, $w \to 0$.
- At $w = 0$: the government's action space collapses to $\{\text{default}, \text{hyperinflation}\}$ — the fiscal equivalent of $A_{\text{pawn}} = \{\text{submit}, \text{rebel}\}$.
- **Austerity** that pushes output down ($y_t \downarrow$) lowers the debt limit $\bar{b}$, shrinking $w$ even as debt is nominally reduced. The "austerity death spiral" (Greece 2010–15) is Du Mu's theorem: the extraction (austerity) depletes the water (fiscal space) faster than it reduces the debt.

---

### Model 4: Financial Regulation and Systemic Risk (SIFI)

**Reference models.** Acharya et al. (2017) systemic risk measurement; Basel III SIFI framework; Brunnermeier & Pedersen (2009) liquidity spirals.

This is perhaps the **most literal instantiation** of the framework in modern economics.

#### Mapping

| Framework | Financial Regulation Instantiation |
|-----------|-----------------------------------|
| Principal $\kappa$ | **Financial regulator** (central bank, FSOC, EBA) |
| Feasible set $K$ | **Financial stability region**: the set of states where no systemic crisis occurs |
| Agent $i$ | **Bank $i$** (or financial institution) |
| $U_i$ | Bank $i$'s autonomous risk-taking: proprietary trading, leverage decisions, derivatives positions |
| $\|U_i\|$ | Bank's **systemic risk contribution** — measured by CoVaR (Adrian & Brunnermeier 2016), SRISK (Brownlees & Engle 2017), or simply total assets / GDP |
| $\bar{U}$ | Mean systemic risk contribution: $\bar{U} = \frac{1}{n}\sum_i \|U_i\|$ |
| $\tau(\text{Obs})$ | **SIFI designation threshold** — the cutoff above which a bank is designated "systemically important" |
| Sword | A bank with $\|U_r\| > \bar{U} + \tau$: a **Systemically Important Financial Institution** |
| Viability axiom | The regulator can always prevent a systemic crisis from any state in $K$ |
| Monitoring $\text{Obs}$ | Regulatory examinations, stress tests, reporting requirements. Finite bandwidth = limited examiner resources |

#### The SIFI designation IS the sword criterion

The Basel III / Dodd-Frank SIFI framework literally implements Theorem 4:

$$\text{Bank } r \text{ is SIFI} \iff \text{systemic importance score} > \text{threshold}$$

where the score measures deviation from the industry average across size, interconnectedness, complexity, cross-jurisdictional activity, and substitutability. This **is** the sword criterion $\|U_r\| > \bar{U} + \tau(\text{Obs})$ with a specific choice of norm $\|\cdot\|$.

**Theorem 1 instantiation:**
- **(a) Relinquish**: the bank voluntarily simplifies, divests risky activities, or submits to enhanced regulation. **Living wills** (resolution plans) are formalised path-(a) protocols.
- **(b) Elimination**: the regulator forces resolution — Dodd-Frank Orderly Liquidation Authority (OLA). Lehman Brothers (2008) was an uncontrolled path (b); Dodd-Frank was designed to make future path-(b) resolutions orderly.

**Theorem 2 (Fixed-Point Impossibility) instantiation:** A bank cannot "prove it is not systemically important" while retaining its size and interconnectedness. JPMorgan cannot argue "we're large but not a threat" — the criterion tests capability (size, interconnectedness), not intent. The act of lobbying against SIFI designation itself demonstrates the bank's political influence ($U_r \neq \varnothing$), reinforcing condition (2).

**Theorem 3 (Power Paradox) instantiation — the post-2008 consolidation paradox:**
1. The 2008 crisis eliminated several large banks (Lehman, Bear Stearns, Wachovia, Washington Mutual).
2. The surviving banks absorbed the failed ones → the survivors became **larger** → $\bar{U}$ didn't drop as expected; instead, the surviving banks' $\|U_r\|$ increased.
3. Dodd-Frank expanded $\text{Obs}$ (more reporting, stress tests) → more banks were detected as systemically important → more regulation required.
4. **The regulatory response to the crisis made the SIFI problem worse, not better** — exactly the paradox of Theorem 3.

**Theorem 4 (Mean-field) instantiation — the "too big to fail" threshold is endogenous:**
- In a **fragmented banking system** (Germany's 1,500 Sparkassen): $\bar{U}$ is low, no individual bank is a sword.
- In a **concentrated banking system** (Canada's Big Five, Australia's Big Four): $\bar{U}$ is high, and even the largest bank's deviation from the mean is moderate → fewer swords relative to the system.
- **But**: merger waves lower $n$ and raise individual $\|U_r\|$ while $\bar{U}$ may not rise proportionally → new swords are created.
- The 2008 shotgun mergers (JPMorgan + Bear Stearns, BofA + Merrill, Wells + Wachovia) **created swords by moving the mean**: each merger increased the surviving bank's $\|U_r\|$ while removing competitors, lowering $\bar{U}$ among the remaining institutions.

#### The liquidity spiral as forcing lemma

Brunnermeier & Pedersen (2009): a leveraged institution facing margin calls must sell assets → asset prices drop → more margin calls → more selling → ... The cost of compensating this spiral is unbounded (the forcing lemma). The regulator must resolve the sword in finite time — inject liquidity (temporary path (a), the Fed's emergency lending) or allow failure (path (b)).

---

### Model 5: Industrial Organisation / Antitrust

**Reference models.** Tirole (1988) *Theory of Industrial Organization*; Williamson (1975) transaction cost economics; Hart & Moore (1990) incomplete contracts.

#### Mapping

| Framework | Antitrust Instantiation |
|-----------|------------------------|
| Principal $\kappa$ | **Antitrust authority** (DOJ, FTC, DG Competition) |
| Feasible set $K$ | **Competitive market conditions**: the set of market structures consistent with consumer welfare / competitive process |
| Agent $i$ | **Firm $i$** |
| $U_i$ | Firm's autonomous market actions: pricing, output, foreclosure, tying, exclusive dealing |
| $\|U_i\|$ | **Market share** $s_i$ or **Lerner index** $L_i = (p_i - mc_i)/p_i$ |
| $\bar{U}$ | Mean market share: $\bar{U} = 1/n$ or mean Lerner index |
| $\tau(\text{Obs})$ | Antitrust detection threshold — the market share or HHI level that triggers scrutiny |
| Sword | A **dominant firm** with market power that can unilaterally distort the competitive process |

#### The HHI as mean-field statistic

The **Herfindahl-Hirschman Index** is:

$$\text{HHI} = \sum_{i=1}^n s_i^2 = n \cdot \text{Var}(s_i) + \frac{1}{n}$$

HHI measures the **dispersion of market shares around the mean** $\bar{U} = 1/n$. A high HHI means some firms deviate significantly from the mean — there are swords. The DOJ/FTC merger guidelines use HHI thresholds:
- HHI < 1500: unconcentrated (no swords)
- HHI 1500–2500: moderately concentrated (potential swords)
- HHI > 2500: highly concentrated (swords present)

This **is** the detection equation $\|U_r\| > \bar{U} + \tau(\text{Obs})$, aggregated into a single statistic.

**Theorem 1 instantiation:**
- **(a) Relinquish**: the firm voluntarily divests, licenses essential patents, opens its platform (Microsoft's 2001 consent decree, Google's compliance commitments in EU).
- **(b) Elimination**: the authority forces breakup (Standard Oil 1911, AT&T 1984) or blocks a merger (AT&T/T-Mobile 2011).

**Theorem 2 instantiation:** Microsoft (2001) could not "prove its monopoly is not a monopoly" while retaining its market share. The remedy required **structural changes** (path a), not promises of good behaviour. The EU's Google cases (2017–2019) reached the same conclusion: behavioural remedies (promises) fail because they don't change $U_r$.

**Theorem 4 instantiation — digital markets as regime change:**
- In the **pre-digital economy**: market concentration was moderate, $\bar{U}$ was relatively high (many mid-size firms in each sector), few firms exceeded the threshold.
- **Digitisation** created winner-take-all dynamics → a few platforms captured dominant market shares → $\|U_r\|$ skyrocketed for Big Tech while $\bar{U}$ across the full economy stayed low → Big Tech firms became swords.
- The **EU Digital Markets Act** (2022) is a detection threshold adjustment: it defines "gatekeepers" as firms exceeding specific revenue, user count, and market position thresholds — a formalised $\tau(\text{Obs})$.

#### The breakpoint criterion in vertical integration

Hart & Moore (1990) / Williamson (1975): a vertically integrated firm controls the entire production chain — no breakpoints. A firm relying on independent suppliers has breakpoints (the supplier is a node controlled by someone else).

**Corollary (Cut Vertex $\neq$ Maximum Actuator) instantiation:** Apple's power comes not from manufacturing (it outsources to Foxconn/TSMC) but from controlling the **iOS ecosystem** — the cut vertex through which all app distribution, payment processing, and developer access flows. Apple is the cut vertex, not the maximum actuator. Foxconn has more manufacturing capability but is not a sword because its execution chain passes through Apple (breakpoint).

---

### Model 6: International Political Economy of Energy (Relevant to Energy Policy at Sciences Po)

**Reference models.** Hotelling (1931) exhaustible resources; Hamilton (2003) oil price shocks and GDP; Helm (2017) *Burn Out* on energy policy; Yergin (2020) *The New Map*.

#### Mapping

| Framework | Energy Geopolitics Instantiation |
|-----------|----------------------------------|
| Principal $\kappa$ | **Importing sovereign** (EU, Japan, China — the energy-dependent economy) |
| Feasible set $K$ | The set of energy supply configurations consistent with economic and security viability: $K = \{(E_t, p_t, s_t) : \text{energy supply } E_t \geq E_{\min},\; \text{price } p_t \leq \bar{p}\}$ |
| Viability axiom | The importing sovereign must always have access to sufficient energy at sustainable prices to maintain economic function. **Energy security as no-Ponzi condition**: you cannot indefinitely depend on a single supplier who can cut you off |
| Agent $i$ | **Energy supplier $i$** (state-owned enterprise, producing country, pipeline operator) |
| $U_i$ | Supplier's **autonomous supply decision**: ability to unilaterally cut, redirect, or price energy flows. $U_i = \{q_i \in [0, \bar{q}_i]\}$ (output choices) |
| $\|U_i\|$ | Supplier's **share of the importer's energy mix**: $\|U_i\| = q_i / Q_{\text{total}}$ |
| $\bar{U}$ | Mean supplier share: $\bar{U} = 1/n$ under diversification |
| $\tau(\text{Obs})$ | Detection threshold: the supply share above which the importer identifies the supplier as a potential threat |
| Sword | A supplier whose autonomous supply decisions can push the importer out of $K$ (energy crisis, economic recession) |

#### Europe's Russian gas dependency as sword dynamics

**Pre-2022 regime:**
- Russia supplied ~40% of EU natural gas. $\|U_{\text{Russia}}\| = 0.40$.
- Mean supplier share: $\bar{U} \approx 0.10$ (EU had ~10 significant gas suppliers).
- $\|U_{\text{Russia}}\| - \bar{U} = 0.30 \gg \tau(\text{Obs})$.
- **Russia was a sword**: it satisfied both conditions — autonomous supply decisions ($U_r \neq \varnothing$, Russia can unilaterally cut gas) and observability (the EU knew about the dependency).

**Why was the sword tolerated for so long?** The framework predicts this: during the **"wartime" phase** (Cold War détente → post-Soviet cooperation, $\varphi = \text{engagement}$), the principal's objective function $J_{\text{engagement}}$ included terms where Russia's gas supply had positive utility (cheap energy, diplomatic engagement). Russia was a **tool**, not a sword, under the engagement phase.

**Phase transition (2022):** The regime changed ($\varphi: \text{engagement} \to \text{confrontation}$). Russia's supply capability was physically unchanged, but the principal's objective function shifted to $J_{\text{security}}$, which treats autonomous foreign supply as a threat. **Russia became a sword without changing anything** — the phase shifted, exactly as Theorem 4 predicts.

**Theorem 1 instantiation:**
- **(a) Relinquish**: Russia voluntarily gives up its supply leverage — this did not happen.
- **(b) Elimination**: the EU forced diversification away from Russian gas (LNG terminals, Norwegian pipeline expansion, demand reduction). Nord Stream shutdown (and sabotage) is the physical elimination of the supply channel.
- The EU chose path (b): eliminate the dependency rather than wait for voluntary relinquishment.

**Theorem 3 (Power Paradox) instantiation — the energy transition paradox:**

As the EU expands its monitoring of energy dependencies ($\text{Obs}$ expansion):
1. It detects Russian gas as a sword → diversifies away from Russia.
2. It now depends more heavily on other suppliers (US LNG, Qatar, Norway, Algerian pipeline).
3. Some of these new suppliers may themselves become swords if their share of the new mix exceeds $\bar{U}_{\text{new}} + \tau$.
4. **Diversification does not eliminate swords — it creates new ones**, unless it diversifies below the threshold for every supplier.

This is why the EU's energy security strategy emphasises **renewables and demand reduction** — they reduce $\bar{U}$ by increasing $n$ (every solar panel is an independent "supplier"), making it structurally impossible for any single agent to exceed the threshold.

#### The energy transition as mean-field shift

The global energy transition instantiates Theorem 4's regime change mechanism:

**Fossil fuel era ($\bar{U}_1$ high):**
- Energy production is concentrated among a few major producers (OPEC+, Russia, major IOCs).
- $\bar{U}_1$ is relatively high because there are few suppliers with large shares.
- A producer with 10% global share may not be a sword (many producers have similar shares).

**Renewable era ($\bar{U}_2$ low):**
- Energy production is distributed across millions of producers (rooftop solar, wind farms, distributed storage).
- $\bar{U}_2$ drops toward $1/n$ with very large $n$.
- A fossil fuel producer retaining its 10% share now deviates enormously from $\bar{U}_2$ → it becomes a sword.
- **OPEC's relevance is not determined by OPEC's behaviour but by the mean-field shift** in global energy production.

#### The breakpoint criterion in energy supply chains

A pipeline with no alternative routing is a supply chain without breakpoints — the supplier controls the entire execution chain (wellhead → pipeline → delivery point). Building **LNG terminals** introduces a breakpoint: the importing country can switch suppliers without infrastructure change. **Interconnectors** between national grids introduce additional breakpoints.

The EU's **energy union** strategy is a breakpoint installation program: interconnect national grids (no single supplier is essential), build LNG import capacity (break pipeline lock-in), mandate strategic reserves (buffer against supply cuts).

**Corollary (Cut Vertex) instantiation:** Saudi Arabia's power in oil markets comes not from having the most oil (Venezuela has larger reserves) but from being the **swing producer** — the node whose output adjustment determines the global price. Saudi Arabia is the cut vertex of the oil market, not the maximum actuator.

---

### Cross-Model Comparison: How Each Theorem Instantiates

| Theorem | RBC (Granular) | New Keynesian | Sovereign Debt | SIFI / Financial Reg | Antitrust | Energy Geopolitics |
|---------|------|------|------|------|------|------|
| **Sword** | Firm with Domar weight $\gg 1/n$ | Sector with pricing power $\gg$ mean markup | Bondholder with market share $\gg 1/n$ | Bank with systemic risk $\gg$ mean | Firm with market share $\gg 1/n$ | Supplier with energy share $\gg 1/n$ |
| **Thm 1 (Binary)** | Breakup or regulation | Price cap or Volcker disinflation | PSI haircut or commitment to hold | Living will or OLA resolution | Consent decree or forced breakup | Diversification or voluntary relinquishment |
| **Thm 2 (No cheap talk)** | "We're big but not dangerous" fails | "We have pricing power but won't abuse it" fails | "We'll hold but trust us" fails — Cole-Kehoe | "We're large but not systemic" fails — SIFI criteria test size, not intent | "We're dominant but not abusing it" fails — market share is the criterion | "We supply 40% but won't cut" fails — capability, not intent |
| **Thm 3 (Paradox)** | Post-crisis consolidation creates larger firms | Expanded monetary authority creates new frictions | Unlimited fiscal power generates own debt crisis | Post-2008 mergers created bigger SIFIs | More antitrust enforcement reclassifies firms | Diversification from one supplier may create new dependencies |
| **Thm 4 (Mean)** | Industry consolidation shifts $\bar{U}$, not firms | Deregulation lowers $\bar{U}$, creating new swords | Debt concentration shifts who is a sword | Banking mergers shift the SIFI threshold | Digital markets shift market share distribution | Energy transition shifts $\bar{U}$ via distributed generation |
| **Phase transition** | TFP shock changes firm size distribution | Supply shock breaks divine coincidence | Sudden stop / crisis zone entry | Credit boom → bust | Technological disruption (digital) | Geopolitical regime change (engagement → confrontation) |
| **Water ($w \to 0$)** | Capital depletion ($K_t \to 0$) → recession | Liquidity trap ($i_t = 0$) → deflationary spiral | Fiscal space exhaustion ($b_t \to \bar{b}$) → default | Capital adequacy → 0 → bank run | Consumer surplus → 0 → market failure | Energy reserves → 0 → supply crisis |
| **Breakpoint** | Antitrust consent decree (mandatory licensing) | Macro-prudential regulation (LTV limits) | Collective action clauses in bonds | Ring-fencing (Vickers/Volcker rule) | Interoperability mandates (DMA) | LNG terminals, grid interconnectors |
| **Cut vertex** | Platform firm (marketplace, not producer) | Central bank (monetary transmission, not production) | IMF (crisis coordinator, not creditor) | Central counterparty (CCP in derivatives) | App store / operating system | Swing producer (Saudi Arabia in oil) |

---

## Summary of the Logical Chain

```
Viability Axiom (no-Ponzi for survival)
    │
    ├── Tangential Condition (at every state, a feasible direction must exist)
    │
    ├── Sword Definition (agent with independent capability + observability)
    │       │
    │       ├── Forcing Lemma: indefinite coexistence has unbounded cost
    │       │       │
    │       │       └── Theorem 1: Binary Lifecycle (relinquish or eliminate)
    │       │
    │       ├── Theorem 2: Fixed-Point Impossibility (cheap talk fails)
    │       │
    │       └── Theorem 3: Unconstrained Power Paradox (absolute power = perpetual elimination)
    │
    ├── Massless Axiom (no intrinsic bargaining weight → baseline = mean)
    │       │
    │       └── Theorem 4: The Sword Is the Mean
    │               │
    │               ├── Threat = deviation from mean capability
    │               ├── Regime change = mean shift, not individual change
    │               └── Feedback loop: elimination → lower mean → new swords → ...
    │
    └── Breakpoint Criterion: be the essential node, not the strongest agent
```

---

## Key Takeaway

**The identity of the threat is not a subjective judgement by the principal. It is an endogenous outcome of the system's mean capability, the principal's monitoring bandwidth, and the viability constraint. History, in this framework, is the solution to an infinite-horizon dynamic game under a feasibility constraint—and "who is a threat" is determined by a moving, mean-field threshold.**
