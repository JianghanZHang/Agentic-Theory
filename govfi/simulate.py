"""Cyber 水電站: convergence analysis for a hydroelectric dam project.

Core question: 给一个项目和预算, 能不能收敛? 多长时间?

Three scenarios:
  1. Clean project (no leakage) — L stays near 0
  2. Moderate corruption + GovFi active — L grows, breakpoints fire, converges
  3. Unchecked corruption (no GovFi, a=0) — L diverges exponentially

Usage:
    python -m govfi.simulate
"""

from __future__ import annotations

import math

from govfi.ledger import Project, Ledger
from govfi.loss import LossField, LayerDamping


# ════════════════════════════════════════════
#   ANSI colors — matches paper's color scheme
#     water (blue)   = flow, safe layers
#     knife (red)    = corruption, attack
#     sword (cyan)   = GovFi detection
#     caution (yellow) = breakpoints
#     green          = certified / pass
# ════════════════════════════════════════════

_B   = "\033[34m"      # blue  (water)
_R   = "\033[31m"      # red   (knife)
_C   = "\033[36m"      # cyan  (sword / GovFi)
_Y   = "\033[33m"      # yellow (caution)
_G   = "\033[32m"      # green (pass / certified)
_W   = "\033[1m"       # bold  (emphasis)
_0   = "\033[0m"       # reset


# ════════════════════════════════════════════
#   Dam parameters
# ════════════════════════════════════════════

DAM = Project(
    name="水电站 (Hydroelectric Dam)",
    budget=100.0,         # 100亿元
    interest_rate=0.05,   # 5% bond rate
    layers=["政府 (Gov)", "公司 (Companies)", "建设者 (Builders)"],
)

# Construction schedule: 5 years
T_CONSTRUCTION = 5.0
# Political delay
DELTA_LAG = 0.5
# Revenue volatility
SIGMA = 2.0
# Simulation time horizon
T_SIM = 10.0


def make_ledger_with_events(
    project: Project,
    diversion_rate: float = 0.0,
    n_periods: int = 20,
) -> Ledger:
    """Build a ledger with periodic disbursements and verifications.

    Args:
        diversion_rate: fraction of each disbursement diverted (corruption).
            0.0 = clean, 0.10 = 10% skimmed at Layer 1.
        n_periods: number of disbursement periods over T_CONSTRUCTION.
    """
    ledger = Ledger(project)
    dt = T_CONSTRUCTION / n_periods
    disbursement_per_period = project.budget / n_periods

    for i in range(n_periods):
        t = (i + 1) * dt

        # Disburse from Gov → Company
        ledger.disburse(
            t=t,
            amount=disbursement_per_period,
            from_layer=0,
            to_layer=1,
            desc=f"Period {i + 1} disbursement",
        )

        # Verification: construction value = disbursement minus diversion,
        # with a natural lag (verification comes 0.5 periods later)
        verified_amount = disbursement_per_period * (1.0 - diversion_rate)
        ledger.verify(
            t=t + dt * 0.5,
            amount=verified_amount,
            desc=f"Period {i + 1} construction verified",
        )

    return ledger


def run_scenario(
    name: str,
    L0: float,
    a: float,
    sigma: float,
    r: float,
    delta_lag: float,
    budget: float,
) -> None:
    """Run one convergence scenario and print results."""
    print(f"\nScenario: {name}")

    # Convergence test (Prop G.11)
    conv = LossField.converges(L0, r, a, delta_lag)
    print(f"  L₀ = {L0:.1f}亿 ({L0 / budget:.0%} of budget)")
    print(f"  Parameters: a={a:.1f}, r={r:.2f}, δ_lag={delta_lag:.1f}, σ={sigma:.1f}")

    if conv:
        # Absorption bound
        T_star = LossField.absorption_bound(L0, r, a, delta_lag)
        print(f"  Convergence: YES ✓")
        print(f"  T* bound: {T_star:.1f} years")

        # Stochastic moments
        E_T, Var_T = LossField.stochastic_moments(L0, r, a, sigma)
        if E_T < float("inf"):
            print(f"  E[T*]: {E_T:.1f} years  Var: {Var_T:.1f} years²")
    else:
        print(f"  Convergence: NO ✗")
        # Show exponential growth
        for t in [5.0, 10.0]:
            L_t = L0 * math.exp(r * t)
            print(f"  L({t:.0f}) = {L0:.1f}·e^({r * t:.2f}) = {L_t:.1f}亿  (growing)")
        print(f"  → Project fails. Money gone.")

    # Run DIDE simulation
    ledger = Ledger(DAM)
    lf = LossField(ledger)
    _, L_arr, events = lf.simulate_dynamics(
        L0=L0, r=r, a=a, delta_lag=delta_lag,
        sigma=0.0, dt=0.01, T=T_SIM, seed=42,
    )

    if events:
        print(f"  Breakpoints: {', '.join(events)}")

    # Final loss value
    L_final = L_arr[-1]
    print(f"  L({T_SIM:.0f}) = {L_final:.2f}亿")


def run_validation_chain() -> None:
    """Explicit validation chain: trace the GovFi ledger period by period.

    Shows that the government can use GovFi to build the 水电站:
    bond → disburse → verify → loss field → breakpoint → absorb → converge.
    """
    print("\n" + "═" * 60)
    print(f"  {_W}Validation Chain: 水电站 with GovFi{_0}")
    print("═" * 60)

    project = DAM
    r = project.interest_rate
    B = project.budget
    diversion_rate = 0.10  # 10% diverted at Layer 1
    n_periods = 10         # 10 half-year periods over 5 years
    dt = T_CONSTRUCTION / n_periods  # 0.5 years per period
    per_period = B / n_periods       # 10亿 per period

    ledger = Ledger(project)
    lf = LossField(ledger)

    # ── Step 0: Bond issuance ──
    print(f"\n  {_B}Step 0: Bond issuance{_0}")
    print(f"    省政府 issues bonds: B = {B:.0f}亿元, r = {r:.0%}, T = {T_CONSTRUCTION:.0f}yr")
    print(f"    {_C}GovFi ledger created. Obs = F (full observability).{_0}")

    breakpoint_fired_at = {}
    absorption_activated = False
    a_bar = 0.0

    for i in range(n_periods):
        t = (i + 1) * dt
        print(f"\n  ── Period {i + 1} (t = {t:.1f}yr) ──")

        # Disburse
        ledger.disburse(
            t=t, amount=per_period,
            from_layer=0, to_layer=1,
            desc=f"P{i+1}: Gov → Companies",
        )
        print(f"    {_B}[Disburse]{_0} {per_period:.1f}亿: Gov → Companies"
              f"  (cumul: {ledger.total_disbursed(t):.1f})")

        # Verify (with diversion)
        verified = per_period * (1.0 - diversion_rate)
        ledger.verify(
            t=t, amount=verified,
            desc=f"P{i+1}: construction verified",
        )
        print(f"    {_C}[Verify]{_0}   {verified:.1f}亿 construction confirmed"
              f"  (cumul: {ledger.total_verified(t):.1f})")

        # Loss field
        L_t = lf.L(t)
        ratio = lf.L_ratio(t)
        loss_color = _R if L_t > 0 else _G
        print(f"    {loss_color}[Loss]{_0}     L({t:.1f}) = {ledger.total_disbursed(t):.1f}"
              f" - {ledger.total_verified(t):.1f}"
              f" = {loss_color}{L_t:.1f}亿{_0}  (L/B = {ratio:.1%})")

        # Breakpoint check
        msgs = lf.check_breakpoints(t)
        for msg in msgs:
            bp_name = msg.split("=")[0]
            breakpoint_fired_at[bp_name] = t
            print(f"    {_Y}[BREAK]    ⚠ {msg}{_0}")

        # Activation logic: if θ₁ fires, GovFi activates absorption
        if not absorption_activated and "θ_1" in breakpoint_fired_at:
            absorption_activated = True
            a_bar = 3.0
            print(f"    {_G}[ACTION]{_0}   GovFi activates restructuring:"
                  f" ā = {a_bar:.1f} (absorption begins after"
                  f" δ_lag = {DELTA_LAG}yr)")

    # ── Final state ──
    t_final = T_CONSTRUCTION
    L_final = lf.L(t_final)
    print(f"\n  ── Final Ledger State (t = {t_final:.1f}yr) ──")
    print(f"    {_B}Total disbursed:{_0}  {ledger.total_disbursed():.1f}亿")
    print(f"    {_C}Total verified:{_0}   {ledger.total_verified():.1f}亿")
    print(f"    {_R}Loss field:{_0}       {_R}{L_final:.1f}亿{_0}"
          f" ({lf.L_ratio():.1%} of budget)")
    print(f"    Transactions:     {len(ledger.transactions())}")

    # ── Convergence proof ──
    L0_at_activation = L_final
    print(f"\n  ── Convergence Proof ──")
    print(f"    L₀ (at activation) = {L0_at_activation:.1f}亿")

    L0_comp = L0_at_activation * math.exp(r * DELTA_LAG)
    threshold = r * L0_comp
    print(f"    L₀·e^(rδ) = {L0_at_activation:.1f}·e^({r*DELTA_LAG:.3f})"
          f" = {L0_comp:.2f}亿")
    print(f"    r·L₀·e^(rδ) = {threshold:.4f}")
    print(f"    ā = {a_bar:.1f}")

    if a_bar > threshold:
        T_star = LossField.absorption_bound(
            L0_at_activation, r, a_bar, DELTA_LAG
        )
        E_T, Var_T = LossField.stochastic_moments(
            L0_at_activation, r, a_bar, SIGMA
        )
        print(f"    ā > r·L₀·e^(rδ) ?  {a_bar:.1f} > {threshold:.4f}  {_G}✓{_0}")
        print(f"    T* ≤ {T_star:.1f} years")
        print(f"    E[T*] = {E_T:.1f}yr,  Var(T*) = {Var_T:.2f}yr²")
        print(f"\n    {_G}┌────────────────────────────────────────────┐{_0}")
        print(f"    {_G}│  VERDICT: Dam completes. GovFi works.      │{_0}")
        print(f"    {_G}│  Loss absorbed in ≤ {T_star:.1f} years.              │{_0}")
        print(f"    {_G}│  Every link auditable on-chain.             │{_0}")
        print(f"    {_G}└────────────────────────────────────────────┘{_0}")
    else:
        print(f"    ā > r·L₀·e^(rδ) ?  {a_bar:.1f} ≤ {threshold:.4f}  {_R}✗{_0}")
        print(f"    {_R}Loss field DIVERGES.{_0}")


def run_monopoly_test() -> None:
    """Test: does GovFi work when Layer 1 is a monopoly (垄断)?

    The "地狱公司结构" (hell company structure): a single entity
    controls Layer 1 (the min-cut).  It controls both information
    flow and money flow.  Two sub-scenarios:

    (A) Monopoly WITHOUT GovFi:
        The monopolist self-reports verification.
        It inflates C_verified to match B_disbursed.
        L(t) ≈ 0 on paper, but actual construction = 70% of budget.
        Loss field is gamed.  No breakpoints fire.  Nobody knows.

    (B) Monopoly WITH GovFi:
        Independent on-chain verification (IoT sensors, satellite
        imagery, independent inspectors).  C_verified = actual work.
        L(t) reveals the 30% gap.  Breakpoints fire.  Absorption works.

    The question: is Obs = F sufficient to defeat a monopolist?
    """
    print("\n" + "═" * 60)
    print(f"  {_W}Monopoly Test: 地狱公司结构 (垄断 at Layer 1){_0}")
    print("═" * 60)

    project = DAM
    r = project.interest_rate
    B = project.budget
    n_periods = 10
    dt = T_CONSTRUCTION / n_periods
    per_period = B / n_periods
    actual_diversion = 0.30  # monopolist diverts 30%

    # ══ Scenario A: Monopoly WITHOUT GovFi ══
    print(f"\n  ── Scenario A: Monopoly, {_R}NO GovFi{_0} ──")
    print(f"    {_R}Monopolist self-reports verification.{_0}")
    print(f"    Actual diversion: {_R}{actual_diversion:.0%}{_0} of each disbursement")
    print()

    ledger_a = Ledger(project)
    lf_a = LossField(ledger_a)

    for i in range(n_periods):
        t = (i + 1) * dt
        ledger_a.disburse(t=t, amount=per_period,
                          from_layer=0, to_layer=1,
                          desc=f"P{i+1}: Gov → Monopolist")
        # Monopolist self-verifies: claims 100% of disbursement was used
        ledger_a.verify(t=t, amount=per_period,
                        desc=f"P{i+1}: monopolist self-verification")

    L_a = lf_a.L()
    msgs_a = lf_a.check_breakpoints(T_CONSTRUCTION)
    actual_construction = B * (1.0 - actual_diversion)
    actual_loss = B - actual_construction

    print(f"    Ledger shows:  disbursed={ledger_a.total_disbursed():.0f}亿,"
          f"  verified={ledger_a.total_verified():.0f}亿")
    print(f"    Reported L(t) = {_G}{L_a:.1f}亿{_0}  (L/B = {L_a/B:.0%})")
    print(f"    Breakpoints fired: {len(msgs_a)}")
    print(f"    {_R}REALITY: actual construction = {actual_construction:.0f}亿"
          f"  ({1-actual_diversion:.0%} of budget){_0}")
    print(f"    {_R}REALITY: actual loss = {actual_loss:.0f}亿"
          f"  ({actual_diversion:.0%} hidden){_0}")
    print(f"    {_R}→ Loss field GAMED. Zero detection. 30亿 gone.{_0}")

    # ══ Scenario B: Monopoly WITH GovFi ══
    print(f"\n  ── Scenario B: Monopoly, {_C}WITH GovFi{_0} (Obs = F) ──")
    print(f"    {_C}Independent verification: IoT + satellite + inspectors.{_0}")
    print(f"    Monopolist cannot inflate C_verified.")
    print()

    ledger_b = Ledger(project)
    lf_b = LossField(ledger_b)

    bp_times = {}
    for i in range(n_periods):
        t = (i + 1) * dt
        ledger_b.disburse(t=t, amount=per_period,
                          from_layer=0, to_layer=1,
                          desc=f"P{i+1}: Gov → Monopolist")
        # Independent verification: only actual construction counted
        actual_verified = per_period * (1.0 - actual_diversion)
        ledger_b.verify(t=t, amount=actual_verified,
                        desc=f"P{i+1}: independent verification")

        L_t = lf_b.L(t)
        ratio = lf_b.L_ratio(t)
        msgs = lf_b.check_breakpoints(t)

        status = ""
        for msg in msgs:
            bp_name = msg.split("=")[0]
            bp_times[bp_name] = t
            status = f"  {_Y}⚠ {msg}{_0}"

        print(f"    t={t:.1f}: {_B}disburse{_0} {per_period:.0f},"
              f" {_C}verify{_0} {actual_verified:.0f},"
              f" {_R}L={L_t:.1f}亿{_0} ({ratio:.1%}){status}")

    L_b = lf_b.L()
    print(f"\n    Final: L = {L_b:.1f}亿 ({lf_b.L_ratio():.0%} of budget)")
    for name, t in bp_times.items():
        print(f"    {name} fired at t={t:.1f}yr")

    # Convergence proof: two absorption rates
    L0_monopoly = L_b

    # Case 1: monopolist resists (low ā)
    a_low = 2.0
    print(f"\n    Case 1: monopolist resists restructuring (ā = {a_low:.1f}):")
    rLe = r * L0_monopoly * math.exp(r * DELTA_LAG)
    if LossField.converges(L0_monopoly, r, a_low, DELTA_LAG):
        T_star = LossField.absorption_bound(L0_monopoly, r, a_low, DELTA_LAG)
        E_T, _ = LossField.stochastic_moments(L0_monopoly, r, a_low, SIGMA)
        print(f"      ā={a_low:.1f} > rL₀e^(rδ)={rLe:.2f}  ✓  (barely)")
        print(f"      T* ≤ {T_star:.1f}yr,  E[T*] = {E_T:.1f}yr ← too slow!")

    # Case 2: θ₃ triggers monopoly breakup → new contractors → high ā
    a_high = 5.0
    print(f"\n    Case 2: θ₃ breaks monopoly → open bidding (ā = {a_high:.1f}):")
    if LossField.converges(L0_monopoly, r, a_high, DELTA_LAG):
        T_star = LossField.absorption_bound(L0_monopoly, r, a_high, DELTA_LAG)
        E_T, Var_T = LossField.stochastic_moments(L0_monopoly, r, a_high, SIGMA)
        print(f"      ā={a_high:.1f} > rL₀e^(rδ)={rLe:.2f}  ✓  (strong)")
        print(f"      T* ≤ {T_star:.1f}yr,  E[T*] = {E_T:.1f}yr,  Var = {Var_T:.2f}yr²")

    print(f"\n    {_C}┌────────────────────────────────────────────────────────┐{_0}")
    print(f"    {_C}│{_0}  GovFi under monopoly: {_C}DETECTION works{_0} (t=1.0yr).      {_C}│{_0}")
    print(f"    {_C}│{_0}  {_Y}ABSORPTION{_0} requires breaking the monopoly (θ₃ → ā↑).  {_C}│{_0}")
    print(f"    {_C}│{_0}  Obs=F is necessary; political action is sufficient.    {_C}│{_0}")
    print(f"    {_C}└────────────────────────────────────────────────────────┘{_0}")

    # ══ Comparison ══
    print(f"\n  ── Comparison ──")
    print(f"    {_R}Without GovFi:{_0} L_reported = {L_a:.0f}亿,"
          f"  L_actual = {_R}{actual_loss:.0f}亿  (hidden){_0}")
    print(f"    {_C}With GovFi:{_0}    L_reported = {L_b:.0f}亿"
          f"  = L_actual  {_C}(transparent){_0}")
    print(f"    Detection time: {_C}{min(bp_times.values()):.1f}yr{_0}"
          f" (vs {_R}never{_0} without GovFi)")


def run_layer_analysis() -> None:
    """Three-layer corruption analysis: proof by elimination (三层排除法).

    Three layers of the fiscal flow graph (a cycle, not a line):
        Layer 0: 政府 (Gov)      — source node, issues bonds
        Layer 1: 公司 (Companies) — min-cut, routes money + information
        Layer 2: 建设者 (Builders = 纳税人/People) — sink node, physical construction

    The Builders at Layer 2 are the same People who fund the bonds at Layer 0,
    making the fiscal graph a cycle and the primal-dual duality a self-duality.

    Shows that corruption at Layer 0 and Layer 2 is structurally unsustainable,
    making Layer 1 the unique min-cut attack surface.
    """
    print("\n" + "═" * 60)
    print(f"  {_W}Three-Layer Corruption Analysis / 三层排除法{_0}")
    print("═" * 60)

    project = DAM
    B = project.budget
    n_periods = 10
    dt = T_CONSTRUCTION / n_periods
    per_period = B / n_periods

    # ══════════════════════════════════════════════════════════
    #   Layer 0: 政府截留 / Gov Self-Diversion (30%)
    # ══════════════════════════════════════════════════════════
    print(f"\n  ── {_B}Layer 0: 政府截留 / Gov Self-Diversion{_0} ──")
    print(f"    Gov raises B=100亿 via bonds, but only disburses 70亿.")
    print(f"    Companies honestly build with what they receive → L ≈ 0.")
    gov_diversion = 0.30

    # --- Without GovFi: bonds off-chain ---
    print(f"\n    {_R}[Without GovFi]{_0} Bond record off-chain.")
    ledger_l0_no = Ledger(project)
    lf_l0_no = LossField(ledger_l0_no)
    # Gov issues bonds but this is off-chain → no issue() call
    for i in range(n_periods):
        t = (i + 1) * dt
        actual_disb = per_period * (1.0 - gov_diversion)
        ledger_l0_no.disburse(
            t=t, amount=actual_disb,
            from_layer=0, to_layer=1,
            desc=f"P{i+1}: Gov → Companies (reduced)",
        )
        # Companies build honestly with what they get
        ledger_l0_no.verify(
            t=t, amount=actual_disb,
            desc=f"P{i+1}: construction verified",
        )

    L_l0_no = lf_l0_no.L()
    L_bond_l0_no = lf_l0_no.L_bond()
    print(f"    Disbursed: {ledger_l0_no.total_disbursed():.0f}亿"
          f"  Verified: {ledger_l0_no.total_verified():.0f}亿")
    print(f"    L_bond = {_R}{L_bond_l0_no:.0f}亿{_0} (invisible: no bond record)")
    print(f"    L_exec = {L_l0_no:.0f}亿 (companies honest)")
    print(f"    {_R}→ 30亿 missing but undetectable via loss field alone.{_0}")

    # --- With GovFi: bonds on-chain ---
    print(f"\n    {_C}[With GovFi]{_0} Bond issuance on-chain.")
    ledger_l0_gf = Ledger(project)
    lf_l0_gf = LossField(ledger_l0_gf)
    # Bond issuance recorded on-chain
    ledger_l0_gf.issue(t=0.0, amount=B, desc="Bond issuance: 100亿")
    for i in range(n_periods):
        t = (i + 1) * dt
        actual_disb = per_period * (1.0 - gov_diversion)
        ledger_l0_gf.disburse(
            t=t, amount=actual_disb,
            from_layer=0, to_layer=1,
            desc=f"P{i+1}: Gov → Companies (reduced)",
        )
        ledger_l0_gf.verify(
            t=t, amount=actual_disb,
            desc=f"P{i+1}: construction verified",
        )

    L_l0_gf = lf_l0_gf.L()
    L_bond_l0_gf = lf_l0_gf.L_bond()
    print(f"    Issued: {ledger_l0_gf.total_issued():.0f}亿"
          f"  Disbursed: {ledger_l0_gf.total_disbursed():.0f}亿"
          f"  Verified: {ledger_l0_gf.total_verified():.0f}亿")
    print(f"    L_bond = {_C}{L_bond_l0_gf:.0f}亿{_0} (on-chain → immediately visible)")
    print(f"    L_exec = {L_l0_gf:.0f}亿")
    print(f"    L_total = {_C}{lf_l0_gf.L_total():.0f}亿{_0}")

    print(f"\n    Structural weakness / 结构弱点:")
    print(f"    → 债券是公开市场产品 (bonds are public market instruments).")
    print(f"      CDS spreads, yield curves, rating agencies all expose")
    print(f"      the gap between B_raised and B_disbursed.")
    print(f"    → 王自毁 = Du Mu's theorem: Gov corrupting itself")
    print(f"      means the source node diverts its own flow.")
    print(f"    → Even WITHOUT GovFi, market signals detect Layer 0.")
    print(f"    {_G}∴ Layer 0 corruption 行不通 (structurally unsustainable).{_0}")

    # ══════════════════════════════════════════════════════════
    #   Layer 1: 公司截留 / Company Diversion (10%)
    # ══════════════════════════════════════════════════════════
    print(f"\n  ── {_R}Layer 1: 公司截留 / Company Diversion{_0} ──")
    print(f"    Companies receive 100亿, pass 90亿 to builders.")
    company_diversion = 0.10

    # --- Without GovFi ---
    print(f"\n    {_R}[Without GovFi]{_0} Company self-reports verification.")
    ledger_l1_no = Ledger(project)
    lf_l1_no = LossField(ledger_l1_no)
    for i in range(n_periods):
        t = (i + 1) * dt
        ledger_l1_no.disburse(
            t=t, amount=per_period,
            from_layer=0, to_layer=1,
            desc=f"P{i+1}: Gov → Company",
        )
        # Company self-reports: claims full verification
        ledger_l1_no.verify(
            t=t, amount=per_period,
            desc=f"P{i+1}: company self-verification (gamed)",
        )

    L_l1_no = lf_l1_no.L()
    actual_l1_loss = B * company_diversion
    print(f"    Reported: L = {_G}{L_l1_no:.0f}亿{_0} (gamed to zero)")
    print(f"    {_R}Reality:  {actual_l1_loss:.0f}亿 diverted (hidden){_0}")
    print(f"    {_R}Breakpoints fired: 0 → corruption undetected.{_0}")

    # --- With GovFi ---
    print(f"\n    {_C}[With GovFi]{_0} Independent verification.")
    ledger_l1_gf = Ledger(project)
    lf_l1_gf = LossField(ledger_l1_gf)
    bp_l1 = {}
    for i in range(n_periods):
        t = (i + 1) * dt
        ledger_l1_gf.disburse(
            t=t, amount=per_period,
            from_layer=0, to_layer=1,
            desc=f"P{i+1}: Gov → Company",
        )
        verified = per_period * (1.0 - company_diversion)
        ledger_l1_gf.verify(
            t=t, amount=verified,
            desc=f"P{i+1}: independent verification",
        )
        msgs = lf_l1_gf.check_breakpoints(t)
        for msg in msgs:
            bp_name = msg.split("=")[0]
            bp_l1[bp_name] = t

    L_l1_gf = lf_l1_gf.L()
    print(f"    L = {L_l1_gf:.0f}亿 ({lf_l1_gf.L_ratio():.0%} of budget)")
    for name, t in bp_l1.items():
        print(f"    {name} fired at t={t:.1f}yr")

    print(f"\n    Why this works for the attacker / 为什么攻击有效:")
    print(f"    → Min-cut: Layer 1 controls BOTH information AND money.")
    print(f"    → Information: what Gov sees (合同 vs 实际资金链)")
    print(f"    → Money: what Builders get (after 层层转包)")
    print(f"    → Dual-ring: formal contract ≠ actual payment chain.")
    print(f"    {_R}∴ Layer 1 = 唯一可持续攻击面 (only sustainable attack).{_0}")

    # ══════════════════════════════════════════════════════════
    #   Layer 2: 豆腐渣工程 / Builder Quality Fraud (30%)
    # ══════════════════════════════════════════════════════════
    print(f"\n  ── {_B}Layer 2: 豆腐渣工程 / Builder Quality Fraud{_0} ──")
    print(f"    Builders receive full payment, deliver 70% quality.")
    builder_fraud = 0.30

    # --- Without GovFi ---
    print(f"\n    {_R}[Without GovFi]{_0} Builder self-reports completion.")
    ledger_l2_no = Ledger(project)
    lf_l2_no = LossField(ledger_l2_no)
    for i in range(n_periods):
        t = (i + 1) * dt
        ledger_l2_no.disburse(
            t=t, amount=per_period,
            from_layer=0, to_layer=1,
            desc=f"P{i+1}: Gov → Company → Builder",
        )
        # Builder self-reports: claims full construction
        ledger_l2_no.verify(
            t=t, amount=per_period,
            desc=f"P{i+1}: builder self-verification (gamed)",
        )

    L_l2_no = lf_l2_no.L()
    actual_l2_loss = B * builder_fraud
    print(f"    Reported: L = {_G}{L_l2_no:.0f}亿{_0} (gamed to zero)")
    print(f"    {_R}Reality:  {actual_l2_loss:.0f}亿 (70% quality){_0}")

    # --- With GovFi ---
    print(f"\n    {_C}[With GovFi]{_0} IoT + satellite verification.")
    ledger_l2_gf = Ledger(project)
    lf_l2_gf = LossField(ledger_l2_gf)
    bp_l2 = {}
    for i in range(n_periods):
        t = (i + 1) * dt
        ledger_l2_gf.disburse(
            t=t, amount=per_period,
            from_layer=0, to_layer=1,
            desc=f"P{i+1}: Gov → Company → Builder",
        )
        verified = per_period * (1.0 - builder_fraud)
        ledger_l2_gf.verify(
            t=t, amount=verified,
            desc=f"P{i+1}: IoT + satellite verification",
        )
        msgs = lf_l2_gf.check_breakpoints(t)
        for msg in msgs:
            bp_name = msg.split("=")[0]
            bp_l2[bp_name] = t

    L_l2_gf = lf_l2_gf.L()
    print(f"    L = {L_l2_gf:.0f}亿 ({lf_l2_gf.L_ratio():.0%} of budget)")
    for name, t in bp_l2.items():
        print(f"    {name} fired at t={t:.1f}yr")

    print(f"\n    Structural weakness / 结构弱点:")
    print(f"    → 物理现实是终极验收 (physics is the ultimate verification).")
    print(f"    → 大坝不蓄水 → 自然暴露 (dam that doesn't hold water → self-revealing).")
    print(f"    → Builder cannot sustain fraud indefinitely.")
    print(f"    → Even WITHOUT GovFi, physical failure eventually reveals Layer 2.")
    print(f"    {_G}∴ Layer 2 corruption 行不通 (structurally unsustainable).{_0}")

    # ══════════════════════════════════════════════════════════
    #   Comparison table (bilingual)
    # ══════════════════════════════════════════════════════════
    print(f"\n  ── Comparison / 对比 ──")
    print(f"  {'Layer':<10} {'腐败模式':<22} {'L_bond':>7} {'L_exec':>7}"
          f" {'可持续?':<20} {'GovFi检测':<12}")
    print(f"  {'─'*10} {'─'*22} {'─'*7} {'─'*7}"
          f" {'─'*20} {'─'*12}")
    print(f"  {_B}{'L0 政府':<10}{_0} {'截留 (self-div)':<22}"
          f" {_C}{f'{L_bond_l0_gf:.0f}亿':>7}{_0} {f'{L_l0_gf:.0f}亿':>7}"
          f" {_G}{'NO (市场信号)':<20}{_0} {'bond链':<12}")
    print(f"  {_R}{'L1 公司':<10}{_0} {'截留 (diversion)':<22}"
          f" {'0亿':>7} {_R}{f'{L_l1_gf:.0f}亿':>7}{_0}"
          f" {_R}{'YES (min-cut)':20}{_0} {_C}{'独立验收':<12}{_0}")
    print(f"  {_B}{'L2 建设':<10}{_0} {'豆腐渣 (fraud)':<22}"
          f" {'0亿':>7} {_C}{f'{L_l2_gf:.0f}亿':>7}{_0}"
          f" {_G}{'NO (物理约束)':<20}{_0} {'IoT+卫星':<12}")

    # ══════════════════════════════════════════════════════════
    #   Verdict (bilingual)
    # ══════════════════════════════════════════════════════════
    print(f"\n  {_W}┌──────────────────────────────────────────────────────────┐{_0}")
    print(f"  {_W}│{_0}  结论 / Verdict:                                         {_W}│{_0}")
    print(f"  {_W}│{_0}  {_G}L0: 行不通{_0} — 债券公开 + 王自毁 (Du Mu's theorem)         {_W}│{_0}")
    print(f"  {_W}│{_0}  {_R}L1: 唯一可持续攻击面{_0} — min-cut controls info + money     {_W}│{_0}")
    print(f"  {_W}│{_0}  {_G}L2: 行不通{_0} — 物理约束 (大坝不蓄水 → 自然暴露)            {_W}│{_0}")
    print(f"  {_W}│{_0}  → Min-cut theorem: Layer 1 is the unique structurally   {_W}│{_0}")
    print(f"  {_W}│{_0}    sustainable attack surface.                           {_W}│{_0}")
    print(f"  {_W}└──────────────────────────────────────────────────────────┘{_0}")


def run_soft_damping() -> None:
    """Three-layer soft damping with Lyapunov certification.

    Introduces continuous proportional dampers at each layer:
      d₀: market forces (fast, strong) — bonds are public
      d₁: GovFi verification (engineered) — the min-cut damper
      d₂: physics constraints (slow but inevitable) — reality checks

    The system has "grace" (恩典): bounded dissipation within thresholds.
    Lyapunov certification: V = ½||L||², V̇ < 0 iff all kᵢ > r.

    来自希尔伯特的礼物: the gradient ∇V = L (steepest descent direction).
    来自杨振宁的礼物: the damping kᵢ (intrinsic directionality, ∂ → D).
    Together: gradient flow in a gauged space.
    """
    print("\n" + "═" * 60)
    print(f"  {_W}Soft Damping: Lyapunov Certification / 柔性阻尼{_0}")
    print("═" * 60)

    r = DAM.interest_rate  # 0.05
    B = DAM.budget  # 100

    # ── Damping rates ──
    k0 = 1.00   # Market: CDS/yields detect in ~1yr
    k1_off = 0.0   # No GovFi: zero damping at min-cut
    k1_on = 0.20   # GovFi: independent verification
    k2 = 0.08   # Physics: structural failure (slow but certain)

    print(f"\n  Compounding rate: r = {_R}{r:.2f}{_0}")
    print(f"  Damping rates (kᵢ):")
    print(f"    {_B}k₀ = {k0:.2f}{_0}  (market / 市场)")
    print(f"    {_C}k₁ = {k1_on:.2f}{_0}  (GovFi / 独立验收)  [{_R}0{_0} without GovFi]")
    print(f"    {_B}k₂ = {k2:.2f}{_0}  (physics / 物理约束)")

    # Initial loss per layer (from three-layer analysis)
    L_init = (30.0, 10.0, 30.0)  # (L₀, L₁, L₂)
    print(f"\n  Initial loss: L = ({L_init[0]:.0f}, {L_init[1]:.0f},"
          f" {L_init[2]:.0f}) 亿")

    # ══════════════════════════════════════════════════════════
    #   Case 1: WITHOUT GovFi
    # ══════════════════════════════════════════════════════════
    damping_no = LayerDamping(k0=k0, k1=k1_off, k2=k2)
    margins_no = damping_no.margins(r)
    betas_no = damping_no.beta(r)

    print(f"\n  ── Case 1: {_R}Without GovFi{_0} (k₁ = 0) ──")
    print(f"    Grace margins εᵢ = kᵢ - r:"
          f" ({_G}{margins_no[0]:+.2f}{_0},"
          f" {_R}{margins_no[1]:+.2f}{_0},"
          f" {_G}{margins_no[2]:+.2f}{_0})")
    print(f"    β function βᵢ = r - kᵢ:"
          f" ({betas_no[0]:+.2f}, {_R}{betas_no[1]:+.2f}{_0}, {betas_no[2]:+.2f})")
    cert_no = f"{_G}YES{_0}" if damping_no.certified(r) else f"{_R}NO{_0}"
    print(f"    Lyapunov certified: {cert_no}")
    print(f"    → {_R}ε₁ = {margins_no[1]:+.2f} < 0 : Layer 1 GROWS (relevant perturbation){_0}")

    # Simulate
    dt, T_sim = 0.1, 30.0
    n_steps = int(T_sim / dt)
    L = list(L_init)
    k_no = [k0, k1_off, k2]
    checkpoints = [0, 20, 50, 100, 150, 200, n_steps]

    print(f"\n    {'t':>6}   {_B}{'L₀':>8}{_0} {_R}{'L₁':>8}{_0} {_B}{'L₂':>8}{_0}   {'V':>10}")
    for step in range(n_steps + 1):
        if step in checkpoints:
            t = step * dt
            V = LossField.lyapunov_V(tuple(L))
            Vd = LossField.lyapunov_Vdot(tuple(L), r, damping_no)
            vd_c = _R if Vd > 0 else _G
            print(f"    {t:5.1f}   {_B}{L[0]:8.2f}{_0} {_R}{L[1]:8.2f}{_0} {_B}{L[2]:8.2f}{_0}"
                  f"   {V:10.1f}  {vd_c}V̇={Vd:+.1f}{_0}")
        for i in range(3):
            L[i] = max(L[i] + (r - k_no[i]) * L[i] * dt, 0.0)

    print(f"    {_R}→ V initially drops (L₀ decays fast) then RISES (L₁ grows).{_0}")
    print(f"    {_R}  Extend-and-pretend pattern: looks better, then collapses.{_0}")

    # ══════════════════════════════════════════════════════════
    #   Case 2: WITH GovFi
    # ══════════════════════════════════════════════════════════
    damping_gf = LayerDamping(k0=k0, k1=k1_on, k2=k2)
    margins_gf = damping_gf.margins(r)
    betas_gf = damping_gf.beta(r)

    print(f"\n  ── Case 2: {_C}With GovFi{_0} (k₁ = {k1_on}) ──")
    print(f"    Grace margins εᵢ = kᵢ - r:"
          f" ({_G}{margins_gf[0]:+.2f}{_0},"
          f" {_G}{margins_gf[1]:+.2f}{_0},"
          f" {_G}{margins_gf[2]:+.2f}{_0})")
    print(f"    β function βᵢ = r - kᵢ:"
          f" ({_G}{betas_gf[0]:+.2f}{_0},"
          f" {_G}{betas_gf[1]:+.2f}{_0},"
          f" {_G}{betas_gf[2]:+.2f}{_0})")
    cert_gf = f"{_G}YES{_0}" if damping_gf.certified(r) else f"{_R}NO{_0}"
    print(f"    Lyapunov certified: {cert_gf}")

    # Half-lives
    hl_colors = [_B, _C, _B]
    for (name, ki), clr in zip(
        [("L₀ 市场", k0), ("L₁ GovFi", k1_on), ("L₂ 物理", k2)],
        hl_colors,
    ):
        hl = LossField.damping_half_life(ki, r)
        print(f"    {clr}{name}{_0}: half-life = {_G}{hl:.1f} yr{_0}")

    # Simulate
    L = list(L_init)
    k_gf = [k0, k1_on, k2]

    print(f"\n    {'t':>6}   {_B}{'L₀':>8}{_0} {_C}{'L₁':>8}{_0} {_B}{'L₂':>8}{_0}   {'V':>10}")
    for step in range(n_steps + 1):
        if step in checkpoints:
            t = step * dt
            V = LossField.lyapunov_V(tuple(L))
            Vd = LossField.lyapunov_Vdot(tuple(L), r, damping_gf)
            print(f"    {t:5.1f}   {_B}{L[0]:8.2f}{_0} {_C}{L[1]:8.2f}{_0} {_B}{L[2]:8.2f}{_0}"
                  f"   {V:10.1f}  {_G}V̇={Vd:+.1f}{_0}")
        for i in range(3):
            L[i] = max(L[i] + (r - k_gf[i]) * L[i] * dt, 0.0)

    print(f"    {_G}→ V monotonically decreasing. Certified stable.{_0}")

    # ══════════════════════════════════════════════════════════
    #   Grace Dissipation: what the bounds actually ARE
    # ══════════════════════════════════════════════════════════
    print(f"\n  ── Grace Dissipation / 恩典耗散: what the bounds contain ──")
    print(f"    The grace bounds are not abstract.  They are REAL costs:")
    print()
    print(f"    Layer 0 — 政府 grace (εᵢ within θ₀·B):")
    print(f"      公款吃喝 (official dining/entertainment) — 可以喝白酒, 没关系")
    print(f"      招待费 (reception expenses)")
    print(f"      差旅费 (travel costs)")
    print(f"      → GovFi 可以报销 (reimbursable, on-chain, transparent)")
    print()
    print(f"    Layer 1 — 公司 grace (εᵢ within θ₁·B):")
    print(f"      合理管理费 (legitimate overhead)")
    print(f"      合理利润 (market-rate profit margin)")
    print(f"      → On-chain: every expense auditable, but ALLOWED within bounds")
    print()
    print(f"    Layer 2 — 建设者 grace (εᵢ within θ₂·B):")
    print(f"      工伤赔偿 (workplace injury compensation)")
    print(f"      材料损耗 (material wastage)")
    print(f"      天气延误 (weather delays)")
    print(f"      → The human cost of construction — not corruption, but reality")
    print()
    print(f"    What happens to the dissipated / 耗散去向:")
    print(f"      absorbed loss → 政府资金池 (Gov funding pool)")
    print(f"      → 希望工程 (Project Hope / education)")
    print(f"      → The loss is CONSERVED but REDIRECTED to social good.")
    print(f"      → The dissipated are stored, not destroyed.")

    # ══════════════════════════════════════════════════════════
    #   The Gradient: 来自希尔伯特的礼物 / Hilbert's Gift
    # ══════════════════════════════════════════════════════════
    print(f"\n  ── The Gradient / 梯度: 来自希尔伯特的礼物 ──")
    print(f"    V = ½||L||²  in L²(R³)")
    print(f"    ∇V = L  (the loss vector IS the gradient)")
    print(f"    With damping K = diag(k₀,k₁,k₂):")
    print(f"      L' = -(K - rI)L  =  -M·∇V")
    print(f"    where M = K - rI is positive definite (when all kᵢ > r).")
    print(f"    → The dynamics ARE gradient descent on V.")
    print(f"    → The gradient gives the steepest-descent direction.")
    print(f"    → Hilbert's gift: the inner product that makes this work.")

    # ══════════════════════════════════════════════════════════
    #   Intrinsic Directionality: 来自杨振宁的礼物 / Yang's Gift
    # ══════════════════════════════════════════════════════════
    print(f"\n  ── Intrinsic Directionality / 内禀方向性: 来自杨振宁的礼物 ──")
    print(f"    Yang-Mills: ∂ → D = ∂ + igA  (flat → curved)")
    print(f"    Fiscal:     L'=rL → L'=(r-kᵢ)L  (free → damped)")
    print(f"    The damping kᵢ IS the gauge connection:")
    print(f"      - It bends the flow from exponential growth to decay.")
    print(f"      - It introduces INTRINSIC directionality: the system")
    print(f"        MUST flow toward L=0 (not by choice, by geometry).")
    print(f"    The non-Abelian structure:")
    print(f"      - Three layers interact (money 0→1→2 is ordered)")
    print(f"      - The min-cut (Layer 1) is where the gauge curvature")
    print(f"        concentrates — like F_μν at the plaquette.")
    print(f"    Mass gap ↔ stability margin:")
    print(f"      m* > 0  ↔  ε_min = min(kᵢ - r) = {min(margins_gf):.2f} > 0")

    # ══════════════════════════════════════════════════════════
    #   RG Flow / 重正化群
    # ══════════════════════════════════════════════════════════
    print(f"\n  ── Soft RG Flow / 柔性重正化群 ──")
    print(f"    Scale:  Layer 0 (UV/macro) → Layer 1 (mid) → Layer 2 (IR/micro)")
    for name, bi in [("L0 UV", betas_gf[0]), ("L1 mid", betas_gf[1]),
                     ("L2 IR", betas_gf[2])]:
        rel_c = _G if bi < 0 else _R
        rel = "irrelevant" if bi < 0 else "RELEVANT"
        print(f"    β({name}) = {rel_c}{bi:+.2f}  ({rel}){_0}")
    print(f"    All βᵢ < 0 → trivial fixed point L=0 is unique attractor.")
    print(f"    Corruption that starts at any scale flows to zero.")

    # ══════════════════════════════════════════════════════════
    #   Verdict
    # ══════════════════════════════════════════════════════════
    eps_min = min(margins_gf)
    V_halflife = math.log(2) / (2 * eps_min)
    print(f"\n  {_G}┌──────────────────────────────────────────────────────────┐{_0}")
    print(f"  {_G}│{_0}  {_W}Lyapunov Certification / 李雅普诺夫认证{_0}                  {_G}│{_0}")
    print(f"  {_G}│{_0}  V = ½||L||²,  {_G}V̇ = Σ(r-kᵢ)Lᵢ² < 0  ✓{_0}                  {_G}│{_0}")
    print(f"  {_G}│{_0}  ε_min = {_G}{eps_min:.2f}{_0},  V half-life = {_G}{V_halflife:.1f} yr{_0}                  {_G}│{_0}")
    print(f"  {_G}│{_0}                                                          {_G}│{_0}")
    print(f"  {_G}│{_0}  {_B}Grace / 恩典:{_0}                                           {_G}│{_0}")
    print(f"  {_G}│{_0}  The 3 dampers are the system's grace — soft, continuous  {_G}│{_0}")
    print(f"  {_G}│{_0}  correction that allows bounded dissipation.             {_G}│{_0}")
    print(f"  {_G}│{_0}  Within thresholds: gentle flow.  Beyond: {_Y}breakpoints{_0}.   {_G}│{_0}")
    print(f"  {_G}│{_0}                                                          {_G}│{_0}")
    print(f"  {_G}│{_0}  来自希尔伯特的礼物: {_B}∇V = L{_0}  (the gradient)              {_G}│{_0}")
    print(f"  {_G}│{_0}  来自杨振宁的礼物: {_C}kᵢ = gauge connection (∂ → D){_0}         {_G}│{_0}")
    print(f"  {_G}│{_0}  Together: gradient flow in gauged space = soft RG flow.  {_G}│{_0}")
    print(f"  {_G}└──────────────────────────────────────────────────────────┘{_0}")


def run_conservation_check() -> None:
    """Log gas leakage: verify flow conservation law."""
    print("\n" + "═" * 60)
    print(f"  {_W}Conservation Check / 守恒验证 (Log Gas Leakage){_0}")
    print("═" * 60)

    # Build a ledger with bond issuance + disbursements + verifications
    project = DAM
    ledger = Ledger(project)
    ledger.issue(t=0.0, amount=project.budget, desc="Bond issuance")
    diversion_rate = 0.10
    n_periods = 20
    dt = T_CONSTRUCTION / n_periods
    per_period = project.budget / n_periods

    for i in range(n_periods):
        t = (i + 1) * dt
        ledger.disburse(t=t, amount=per_period, from_layer=0, to_layer=1,
                        desc=f"P{i+1}")
        ledger.verify(t=t, amount=per_period * (1.0 - diversion_rate),
                      desc=f"P{i+1} verified")

    lf = LossField(ledger)
    chk = lf.check_conservation()
    snap = chk["snapshot"]

    print(f"\n  B_iss = {snap['B_iss']:.2f}亿   B_dis = {snap['B_dis']:.2f}亿"
          f"   C_ver = {snap['C_ver']:.2f}亿")
    print(f"  L_bond = {snap['L_bond']:.2f}亿   L_exec = {snap['L_exec']:.2f}亿"
          f"  L_total = {snap['L_total']:.2f}亿")

    print(f"\n  {'Check':<22} {'Value':>8} {'Status':>8}")
    print(f"  {'─'*22} {'─'*8} {'─'*8}")

    check_labels = {
        "monotone_flow": "Monotone flow",
        "non_negative": "Non-negativity",
        "loss_decomposition": "Loss decomposition",
        "loss_identity": "Loss identity",
    }
    for key, label in check_labels.items():
        val = chk[key]
        if key == "loss_identity":
            detail = f"leak={chk['leak']:.0g}"
            status = f"{_G}PASS{_0}" if val else f"{_R}FAIL{_0}"
            print(f"  {label:<22} {detail:>8} {status}")
        else:
            mark = f"{_G}✓{_0}" if val else f"{_R}✗{_0}"
            status = f"{_G}PASS{_0}" if val else f"{_R}FAIL{_0}"
            print(f"  {label:<22} {mark:>8} {status}")

    print(f"\n  Conservation law: L_total = B_iss - C_ver (telescoping identity)")
    print(f"  守恒定律: L_total = B_iss - C_ver（望远镜恒等式）")


def main() -> None:
    print("═" * 55)
    print("  Cyber 水電站: Convergence Analysis")
    print("═" * 55)
    print(f"\n  Project: {DAM.name}")
    print(f"  Budget B = {DAM.budget:.0f}亿元")
    print(f"  Bond rate r = {DAM.interest_rate:.0%}")
    print(f"  Construction: {T_CONSTRUCTION:.0f} years")
    print(f"  Layers: {' → '.join(DAM.layers)}")
    print(f"  Political lag δ_lag = {DELTA_LAG} years")
    print(f"  Revenue volatility σ = {SIGMA}亿/yr")

    r = DAM.interest_rate
    B = DAM.budget

    # ── Scenario 1: Clean project ──
    run_scenario(
        name="Clean (no leakage, a=5.0, σ=2.0)",
        L0=0.5,       # tiny initial gap (normal disbursement lead)
        a=5.0,         # strong absorption (full verification flow)
        sigma=SIGMA,
        r=r,
        delta_lag=DELTA_LAG,
        budget=B,
    )

    # ── Scenario 2: Moderate corruption + GovFi ──
    run_scenario(
        name="Moderate corruption + GovFi (a=3.0, σ=2.0)",
        L0=10.0,       # 10% of budget diverted at Layer 1
        a=3.0,         # GovFi active: breakpoints trigger recovery
        sigma=SIGMA,
        r=r,
        delta_lag=DELTA_LAG,
        budget=B,
    )

    # ── Scenario 3: Unchecked corruption (no GovFi) ──
    run_scenario(
        name="No control (a=0)",
        L0=10.0,       # same initial leak
        a=0.0,         # no absorption — nobody watching
        sigma=0.0,     # irrelevant without control
        r=r,
        delta_lag=DELTA_LAG,
        budget=B,
    )

    # ── Optimal trigger ──
    rho = 0.08   # sovereign discount rate
    kappa = 50.0  # political cost of restructuring (亿元)
    L_star = LossField.optimal_trigger(r, rho, kappa)
    print(f"\n  Optimal trigger (Thm G.14): L* ≤ ρκ/r = {rho}×{kappa}/{r} = {L_star:.1f}亿")
    print(f"  → Restructure when loss field exceeds {L_star:.1f}亿 ({L_star / B:.0%} of budget)")

    # ── Verdict ──
    print(f"\n{'─' * 55}")
    print(f"  Prediction: With GovFi active, dam completes in ~3 years.")
    print(f"              Without GovFi, loss field diverges.")
    print(f"{'─' * 55}")

    # ── Validation chain ──
    run_validation_chain()

    # ── Monopoly test ──
    run_monopoly_test()

    # ── Three-layer analysis ──
    run_layer_analysis()

    # ── Soft damping + Lyapunov ──
    run_soft_damping()

    # ── Conservation check ──
    run_conservation_check()


if __name__ == "__main__":
    main()
