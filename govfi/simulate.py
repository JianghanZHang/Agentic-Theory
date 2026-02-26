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
from govfi.loss import LossField


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
    print("  Validation Chain: 水电站 with GovFi")
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
    print(f"\n  Step 0: Bond issuance")
    print(f"    省政府 issues bonds: B = {B:.0f}亿元, r = {r:.0%}, T = {T_CONSTRUCTION:.0f}yr")
    print(f"    GovFi ledger created. Obs = F (full observability).")

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
        print(f"    [Disburse] {per_period:.1f}亿: Gov → Companies"
              f"  (cumul: {ledger.total_disbursed(t):.1f})")

        # Verify (with diversion)
        verified = per_period * (1.0 - diversion_rate)
        ledger.verify(
            t=t, amount=verified,
            desc=f"P{i+1}: construction verified",
        )
        print(f"    [Verify]   {verified:.1f}亿 construction confirmed"
              f"  (cumul: {ledger.total_verified(t):.1f})")

        # Loss field
        L_t = lf.L(t)
        ratio = lf.L_ratio(t)
        print(f"    [Loss]     L({t:.1f}) = {ledger.total_disbursed(t):.1f}"
              f" - {ledger.total_verified(t):.1f}"
              f" = {L_t:.1f}亿  (L/B = {ratio:.1%})")

        # Breakpoint check
        msgs = lf.check_breakpoints(t)
        for msg in msgs:
            bp_name = msg.split("=")[0]
            breakpoint_fired_at[bp_name] = t
            print(f"    [BREAK]    ⚠ {msg}")

        # Activation logic: if θ₁ fires, GovFi activates absorption
        if not absorption_activated and "θ_1" in breakpoint_fired_at:
            absorption_activated = True
            a_bar = 3.0
            print(f"    [ACTION]   GovFi activates restructuring:"
                  f" ā = {a_bar:.1f} (absorption begins after"
                  f" δ_lag = {DELTA_LAG}yr)")

    # ── Final state ──
    t_final = T_CONSTRUCTION
    L_final = lf.L(t_final)
    print(f"\n  ── Final Ledger State (t = {t_final:.1f}yr) ──")
    print(f"    Total disbursed:  {ledger.total_disbursed():.1f}亿")
    print(f"    Total verified:   {ledger.total_verified():.1f}亿")
    print(f"    Loss field:       {L_final:.1f}亿"
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
        print(f"    ā > r·L₀·e^(rδ) ?  {a_bar:.1f} > {threshold:.4f}  ✓")
        print(f"    T* ≤ {T_star:.1f} years")
        print(f"    E[T*] = {E_T:.1f}yr,  Var(T*) = {Var_T:.2f}yr²")
        print(f"\n    ┌────────────────────────────────────────────┐")
        print(f"    │  VERDICT: Dam completes. GovFi works.      │")
        print(f"    │  Loss absorbed in ≤ {T_star:.1f} years.              │")
        print(f"    │  Every link auditable on-chain.             │")
        print(f"    └────────────────────────────────────────────┘")
    else:
        print(f"    ā > r·L₀·e^(rδ) ?  {a_bar:.1f} ≤ {threshold:.4f}  ✗")
        print(f"    Loss field DIVERGES.")


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
    print("  Monopoly Test: 地狱公司结构 (垄断 at Layer 1)")
    print("═" * 60)

    project = DAM
    r = project.interest_rate
    B = project.budget
    n_periods = 10
    dt = T_CONSTRUCTION / n_periods
    per_period = B / n_periods
    actual_diversion = 0.30  # monopolist diverts 30%

    # ══ Scenario A: Monopoly WITHOUT GovFi ══
    print(f"\n  ── Scenario A: Monopoly, NO GovFi ──")
    print(f"    Monopolist self-reports verification.")
    print(f"    Actual diversion: {actual_diversion:.0%} of each disbursement")
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
    print(f"    Reported L(t) = {L_a:.1f}亿  (L/B = {L_a/B:.0%})")
    print(f"    Breakpoints fired: {len(msgs_a)}")
    print(f"    REALITY: actual construction = {actual_construction:.0f}亿"
          f"  ({1-actual_diversion:.0%} of budget)")
    print(f"    REALITY: actual loss = {actual_loss:.0f}亿"
          f"  ({actual_diversion:.0%} hidden)")
    print(f"    → Loss field GAMED. Zero detection. 30亿 gone.")

    # ══ Scenario B: Monopoly WITH GovFi ══
    print(f"\n  ── Scenario B: Monopoly, WITH GovFi (Obs = F) ──")
    print(f"    Independent verification: IoT + satellite + inspectors.")
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
            status = f"  ⚠ {msg}"

        print(f"    t={t:.1f}: disburse {per_period:.0f},"
              f" verify {actual_verified:.0f},"
              f" L={L_t:.1f}亿 ({ratio:.1%}){status}")

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

    print(f"\n    ┌────────────────────────────────────────────────────────┐")
    print(f"    │  GovFi under monopoly: DETECTION works (t=1.0yr).      │")
    print(f"    │  ABSORPTION requires breaking the monopoly (θ₃ → ā↑).  │")
    print(f"    │  Obs=F is necessary; political action is sufficient.    │")
    print(f"    └────────────────────────────────────────────────────────┘")

    # ══ Comparison ══
    print(f"\n  ── Comparison ──")
    print(f"    Without GovFi: L_reported = {L_a:.0f}亿,"
          f"  L_actual = {actual_loss:.0f}亿  (hidden)")
    print(f"    With GovFi:    L_reported = {L_b:.0f}亿"
          f"  = L_actual  (transparent)")
    print(f"    Detection time: {min(bp_times.values()):.1f}yr"
          f" (vs never without GovFi)")


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


if __name__ == "__main__":
    main()
