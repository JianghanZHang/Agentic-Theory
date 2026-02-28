"""三体: mass gap phase transition in the restricted three-body problem.

Core question: 放一个 fixed point, 打开一个 mass gap, 用引力把它合上.

Three scenarios:
  1. Lagrange points — fixed points of the effective potential
  2. Mass gap scan — Δ(μ) as a function of mass ratio
  3. Phase transition — vacuum → gap open → gap closed by gravity

Usage:
    python -m threebody.simulate
"""

from __future__ import annotations

import math

from threebody.dynamics import RestrictedThreeBody, MU_CRIT


# ═══════════════════════════════════════════════
#   ANSI colours — matches paper's colour scheme
#     water (blue)   = stable / flow
#     knife (red)    = unstable / break
#     sword (cyan)   = gap / transition
#     caution (yellow) = threshold
#     green          = open / pass
# ═══════════════════════════════════════════════

_B = "\033[34m"       # blue  (water)
_R = "\033[31m"       # red   (knife)
_C = "\033[36m"       # cyan  (sword)
_Y = "\033[33m"       # yellow (caution)
_G = "\033[32m"       # green (pass)
_W = "\033[1m"        # bold  (emphasis)
_0 = "\033[0m"        # reset


# ═══════════════════════════════════════════════
#   Scenario 1: Lagrange points
# ═══════════════════════════════════════════════

def run_lagrange_points(mu: float = 0.01) -> None:
    """Display all five Lagrange points for a given mass ratio."""
    sys = RestrictedThreeBody(mu)
    points = sys.all_lagrange_points()

    print(f"\n{_W}━━━ Scenario 1: Lagrange Points (μ = {mu}) ━━━{_0}")
    print(f"\n  {'Point':<6} {'x':>10} {'y':>10} {'C_J':>10} {'Stable':>10}")
    print(f"  {'─' * 6} {'─' * 10} {'─' * 10} {'─' * 10} {'─' * 10}")

    for lp in points:
        colour = _G if lp.stable else _R
        tag = f"{colour}Yes ✓{_0}" if lp.stable else f"{colour}No ✗{_0}"
        print(
            f"  {lp.name:<6} {lp.x:>10.4f} {lp.y:>10.4f} "
            f"{lp.jacobi:>10.4f} {tag:>20}"
        )

    gap = sys.mass_gap()
    print(f"\n  {_C}Mass gap: Δ = C_J(L1) − C_J(L4) = {gap.delta:.4f}{_0}")
    print(f"  {_C}Routh critical ratio: μ_crit = {MU_CRIT:.6f}{_0}")


# ═══════════════════════════════════════════════
#   Scenario 2: Mass gap scan
# ═══════════════════════════════════════════════

def run_mass_gap_scan() -> None:
    """Scan the mass gap Δ(μ) as μ varies from near 0 to beyond μ_crit."""
    print(f"\n{_W}━━━ Scenario 2: Mass Gap vs Mass Ratio ━━━{_0}")
    print(
        f"\n  {'μ':>8} {'Δ(μ)':>8} {'L4 stable':>10} {'Gap':>12}"
    )
    print(f"  {'─' * 8} {'─' * 8} {'─' * 10} {'─' * 12}")

    mu_values = [
        0.001, 0.005, 0.010, 0.015, 0.020, 0.025, 0.030,
        0.035, 0.037, 0.038, MU_CRIT, 0.039, 0.040, 0.050,
        0.100, 0.200,
    ]

    for mu in mu_values:
        # Clamp to valid range
        mu_val = max(1e-6, min(mu, 1 - 1e-6))
        sys = RestrictedThreeBody(mu_val)
        gap = sys.mass_gap()

        stable_str = f"{_G}Yes ✓{_0}" if gap.L4_stable else f"{_R}No ✗{_0}"

        if gap.gap_open:
            gap_str = f"{_G}OPEN{_0}"
        elif gap.L4_stable:
            gap_str = f"{_Y}MARGINAL{_0}"
        else:
            gap_str = f"{_R}CLOSED{_0}"

        marker = ""
        if abs(mu - MU_CRIT) < 1e-6:
            marker = f"  {_Y}← μ_crit{_0}"

        print(
            f"  {mu_val:>8.4f} {gap.delta:>8.4f} "
            f"{stable_str:>20} {gap_str:>22}{marker}"
        )


# ═══════════════════════════════════════════════
#   Scenario 3: The vacuum → fixed point → closure story
# ═══════════════════════════════════════════════

def run_vacuum_story() -> None:
    """Demonstrate the three phases: vacuum, gap open, gap closed."""
    print(f"\n{_W}━━━ Scenario 3: Vacuum → Fixed Point → Closure ━━━{_0}\n")

    # Phase 1: Vacuum (μ → 0⁺)
    mu_vac = 1e-6
    sys_vac = RestrictedThreeBody(mu_vac)
    gap_vac = sys_vac.mass_gap()
    print(f"  {_B}Phase 1 — VACUUM{_0} (μ = {mu_vac:.1e})")
    print(f"    Δ = {gap_vac.delta:.6f}  (gap vanishes as μ → 0)")
    print(f"    L4 stable: {gap_vac.L4_stable}")
    print(f"    In the vacuum limit, the fixed point carries no mass gap.")
    print(f"    The three-body problem degenerates to two-body Kepler.\n")

    # Phase 2: Gap open (0 < μ < μ_crit)
    mu_open = 0.01
    sys_open = RestrictedThreeBody(mu_open)
    result_open = sys_open.mass_gap()
    print(f"  {_G}Phase 2 — GAP OPEN{_0} (μ = {mu_open})")
    print(f"    Δ = {result_open.delta:.4f}  (mass gap protects L4)")
    print(f"    C_J(L1) = {result_open.C_L1:.4f},  C_J(L4) = {result_open.C_L4:.4f}")
    print(f"    L4 stable: {_G}{result_open.L4_stable}{_0}")
    print(f"    The gravitational source opened a fixed point in the vacuum.")
    print(f"    Energy barrier Δ prevents escape from L4 neighbourhood.\n")

    # Phase 3: Gap closed (μ ≥ μ_crit)
    mu_closed = 0.05
    sys_closed = RestrictedThreeBody(mu_closed)
    result_closed = sys_closed.mass_gap()
    print(f"  {_R}Phase 3 — GAP CLOSED{_0} (μ = {mu_closed})")
    print(f"    Δ = {result_closed.delta:.4f}  (energy gap still positive)")
    print(f"    C_J(L1) = {result_closed.C_L1:.4f},  C_J(L4) = {result_closed.C_L4:.4f}")
    print(f"    L4 stable: {_R}{result_closed.L4_stable}{_0}")
    print(f"    Gravity killed the stability.  Coriolis coupling exceeds")
    print(f"    the Routh bound: μ = {mu_closed} > μ_crit = {MU_CRIT:.6f}.")
    print(f"    The energy barrier exists but is dynamically ineffective.\n")

    # Summary box
    print(f"  {_W}┌──────────────────────────────────────────────────────────────┐{_0}")
    print(f"  {_W}│{_0}  {_C}三体问题能做.{_0}                                              {_W}│{_0}")
    print(f"  {_W}│{_0}                                                              {_W}│{_0}")
    print(f"  {_W}│{_0}  How to open a fixed-point mass in vacuum:                   {_W}│{_0}")
    print(f"  {_W}│{_0}    Introduce mass μ > 0 into the two-body vacuum.            {_W}│{_0}")
    print(f"  {_W}│{_0}    Lagrange points emerge; L4/L5 are stable fixed points.    {_W}│{_0}")
    print(f"  {_W}│{_0}    The Jacobi constant gap Δ = C_J(L1) − C_J(L4) > 0        {_W}│{_0}")
    print(f"  {_W}│{_0}    protects the fixed point with an energy barrier.          {_W}│{_0}")
    print(f"  {_W}│{_0}                                                              {_W}│{_0}")
    print(f"  {_W}│{_0}  How gravity closes the gap:                                 {_W}│{_0}")
    print(f"  {_W}│{_0}    As μ → μ_crit ≈ {MU_CRIT:.4f}, Coriolis coupling kills    {_W}│{_0}")
    print(f"  {_W}│{_0}    L4 stability.  The energy barrier persists but the         {_W}│{_0}")
    print(f"  {_W}│{_0}    fixed point is no longer viable: gravity closed the gap.  {_W}│{_0}")
    print(f"  {_W}│{_0}                                                              {_W}│{_0}")
    print(f"  {_W}│{_0}  Viability connection (Thm I.3):                             {_W}│{_0}")
    print(f"  {_W}│{_0}    μ < μ_crit ⟺ L4 ∈ Viab(K) — the fixed point is viable.  {_W}│{_0}")
    print(f"  {_W}│{_0}    μ ≥ μ_crit ⟺ L4 ∉ Viab(K) — viability lost by gravity.  {_W}│{_0}")
    print(f"  {_W}└──────────────────────────────────────────────────────────────┘{_0}")


# ═══════════════════════════════════════════════
#   Main entry point
# ═══════════════════════════════════════════════

def main() -> None:
    print(f"\n{_W}{'═' * 62}{_0}")
    print(f"{_W}  三 体 — Three-Body Problem: Fixed Points & Mass Gap{_0}")
    print(f"{_W}{'═' * 62}{_0}")

    run_lagrange_points()
    run_mass_gap_scan()
    run_vacuum_story()

    print()


if __name__ == "__main__":
    main()
