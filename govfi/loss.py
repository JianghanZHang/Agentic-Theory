"""Loss field computation, DIDE dynamics, breakpoints, and convergence analysis.

Implements the mathematics from Appendix G (govfi.tex):
  - Loss field L(t) = B_disbursed(t) - C_verified(t)       (eq:loss-field)
  - DIDE dynamics L'(t) = r L(t) - a(t - delta_lag)        (eq:loss-dide)
  - Absorption time bound T*                         (thm:absorption-time)
  - Stochastic moments E[T*], Var(T*)               (prop:stochastic-loss)
  - Optimal trigger L* <= rho kappa / r              (thm:optimal-trigger)

Note: the simulation uses constant absorption rate a with step-function
lag (a(t) = a_bar * 1_{t > delta_lag}), not the general time-varying
a(t - delta_lag) from the paper's DIDE.  This is the special case under
which Prop G.11's closed-form bounds hold exactly.

Stdlib only — no external dependencies.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from govfi.ledger import Ledger


@dataclass
class BreakpointEvent:
    """A threshold exceedance event."""

    threshold_name: str
    threshold_value: float
    time: float
    loss_ratio: float


@dataclass
class LayerDamping:
    """Proportional damping rates for the three-layer system.

    Each kᵢ is a proportional damping rate: dᵢ(Lᵢ) = kᵢ · Lᵢ.
    The layer dynamics are Lᵢ' = (r - kᵢ) · Lᵢ.
    Lyapunov stability requires kᵢ > r for all i.
    """

    k0: float  # Layer 0: market damping (bonds public → fast)
    k1: float  # Layer 1: GovFi verification (engineered)
    k2: float  # Layer 2: physics constraint (slow but inevitable)

    def certified(self, r: float) -> bool:
        """Lyapunov stability: all kᵢ > r?"""
        return all(k > r for k in (self.k0, self.k1, self.k2))

    def margins(self, r: float) -> tuple[float, float, float]:
        """Grace margins εᵢ = kᵢ - r.  Positive = stable at layer i."""
        return (self.k0 - r, self.k1 - r, self.k2 - r)

    def beta(self, r: float) -> tuple[float, float, float]:
        """RG beta function βᵢ = r - kᵢ.  Negative = irrelevant."""
        return (r - self.k0, r - self.k1, r - self.k2)


class LossField:
    """Real-time loss field computation with breakpoints.

    The loss field is the gap between disbursed funds and verified construction,
    adjusted for the planned schedule gap.  Loss = actual gap - planned gap.
    """

    def __init__(
        self,
        ledger: Ledger,
        thresholds: tuple[float, ...] = (0.05, 0.10, 0.15),
    ) -> None:
        self.ledger = ledger
        self.thresholds = thresholds
        self._breakpoint_events: list[BreakpointEvent] = []
        self._fired: set[int] = set()

    # ── Core loss field (eq G.3) ──

    def L(self, t: float | None = None) -> float:
        """L(t) = max(B_disbursed(t) - C_verified(t), 0)."""
        return max(
            self.ledger.total_disbursed(t) - self.ledger.total_verified(t),
            0.0,
        )

    def L_bond(self, t: float | None = None) -> float:
        """L_bond(t) = max(B_issued(t) - B_disbursed(t), 0).
        Layer 0 loss: money raised but never disbursed."""
        return max(
            self.ledger.total_issued(t) - self.ledger.total_disbursed(t),
            0.0,
        )

    def L_total(self, t: float | None = None) -> float:
        """L_total = L_bond + L = B_issued - C_verified.
        Total loss across all layers."""
        return self.L_bond(t) + self.L(t)

    def L_ratio(self, t: float | None = None) -> float:
        """L(t) / B — loss as fraction of total budget."""
        B = self.ledger.project.budget
        if B <= 0:
            return 0.0
        return self.L(t) / B

    # ── Three-layer Lyapunov analysis ──

    @staticmethod
    def lyapunov_V(L: tuple[float, float, float]) -> float:
        """V(L) = ½||L||² = ½(L₀² + L₁² + L₂²).

        The gradient ∇V = L gives the steepest-descent direction.
        With damping K = diag(k₀,k₁,k₂), the dynamics L' = -(K-rI)L
        are gradient flow on V when K > rI.
        """
        return 0.5 * sum(x**2 for x in L)

    @staticmethod
    def lyapunov_Vdot(
        L: tuple[float, float, float],
        r: float,
        damping: LayerDamping,
    ) -> float:
        """V̇ = Σᵢ (r - kᵢ) Lᵢ².  Negative definite iff all kᵢ > r."""
        k = (damping.k0, damping.k1, damping.k2)
        return sum((r - ki) * Li**2 for ki, Li in zip(k, L))

    @staticmethod
    def damping_half_life(ki: float, r: float) -> float:
        """Half-life of Lᵢ under damping: ln2 / (kᵢ - r).

        Returns inf if kᵢ ≤ r (layer not stable).
        """
        margin = ki - r
        if margin <= 0:
            return float("inf")
        return math.log(2) / margin

    # ── Breakpoint checking ──

    def check_breakpoints(self, t: float = 0.0) -> list[str]:
        """Check which thresholds are exceeded.  Returns list of messages."""
        ratio = self.L_ratio(t)
        messages: list[str] = []
        for i, theta in enumerate(self.thresholds):
            if ratio >= theta and i not in self._fired:
                self._fired.add(i)
                name = f"θ_{i + 1}"
                evt = BreakpointEvent(
                    threshold_name=name,
                    threshold_value=theta,
                    time=t,
                    loss_ratio=ratio,
                )
                self._breakpoint_events.append(evt)
                messages.append(
                    f"{name}={theta:.0%} fired at t={t:.1f} "
                    f"(L/B={ratio:.1%})"
                )
        return messages

    @property
    def breakpoint_events(self) -> list[BreakpointEvent]:
        return list(self._breakpoint_events)

    # ── DIDE simulation (eq G.6) ──
    #   L'(t) = r L(t) - a(t - delta_lag)  [+ sigma dW]

    def simulate_dynamics(
        self,
        L0: float,
        r: float,
        a: float,
        delta_lag: float,
        sigma: float = 0.0,
        dt: float = 0.01,
        T: float = 10.0,
        seed: int | None = None,
    ) -> tuple[list[float], list[float], list[str]]:
        """Solve L'(t) = r L(t) - a(t - delta_lag) [+ sigma dW].

        Returns (t_arr, L_arr, events).
        The delay term a(t - delta_lag) kicks in only after t > delta_lag.
        """
        if seed is not None:
            random.seed(seed)

        B = self.ledger.project.budget
        n_steps = int(T / dt)
        t_arr = [0.0]
        L_arr = [L0]

        # Reset breakpoints for simulation
        self._fired.clear()
        self._breakpoint_events.clear()
        events: list[str] = []

        L_t = L0
        for i in range(1, n_steps + 1):
            t = i * dt

            # Deterministic drift: r * L - a (after lag)
            absorption = a if t > delta_lag else 0.0
            dL = (r * L_t - absorption) * dt

            # Stochastic term
            if sigma > 0:
                dW = random.gauss(0, math.sqrt(dt))
                dL += sigma * dW

            L_t = max(L_t + dL, 0.0)

            t_arr.append(t)
            L_arr.append(L_t)

            # Check breakpoints (using L/B ratio)
            if B > 0:
                ratio = L_t / B
                for j, theta in enumerate(self.thresholds):
                    if ratio >= theta and j not in self._fired:
                        self._fired.add(j)
                        name = f"θ_{j + 1}"
                        evt = BreakpointEvent(
                            threshold_name=name,
                            threshold_value=theta,
                            time=t,
                            loss_ratio=ratio,
                        )
                        self._breakpoint_events.append(evt)
                        msg = f"{name}={theta:.0%} fired at t={t:.2f}"
                        events.append(msg)

        return t_arr, L_arr, events

    # ── Absorption time bound (Prop G.11) ──

    @staticmethod
    def absorption_bound(L0: float, r: float, a_bar: float, delta_lag: float) -> float:
        """T* <= delta_lag + L0 e^{r delta_lag} / (a_bar - r L0 e^{r delta_lag}).

        Returns T* bound, or float('inf') if convergence condition not met.
        Convergence requires: a_bar > r * L0 * e^{r * delta_lag}.
        """
        L0_compounded = L0 * math.exp(r * delta_lag)
        denominator = a_bar - r * L0_compounded
        if denominator <= 0:
            return float("inf")
        return delta_lag + L0_compounded / denominator

    # ── Stochastic moments (Prop G.13) ──

    @staticmethod
    def stochastic_moments(
        L0: float, r: float, a: float, sigma: float
    ) -> tuple[float, float]:
        """E[T*] = L0 / (a - r L0),  Var(T*) = sigma^2 L0 / (a - r L0)^3.

        Returns (E[T*], Var(T*)).  Requires a > r L0.
        These are *conditional* moments post-lag (control already active).
        For total time from t_0, add delta_lag and compound L0 through the
        lag period: L0_eff = L0 * exp(r * delta_lag).
        """
        drift = a - r * L0
        if drift <= 0:
            return float("inf"), float("inf")
        E_T = L0 / drift
        Var_T = (sigma**2 * L0) / drift**3
        return E_T, Var_T

    # ── Optimal trigger (Thm G.14) ──

    @staticmethod
    def optimal_trigger(r: float, rho: float, kappa: float) -> float:
        """Upper bound on the optimal trigger: L* <= rho kappa / r.

        The actual optimal L* is strictly below this when sigma > 0
        (Thm G.14(c): higher volatility lowers the trigger).
        This bound is the deterministic case (sigma = 0).
        """
        if r <= 0:
            return float("inf")
        return rho * kappa / r

    # ── Convergence test ──

    @staticmethod
    def converges(L0: float, r: float, a_bar: float, delta_lag: float) -> bool:
        """Test: a_bar > r * L0 * e^{r * delta_lag}?"""
        return a_bar > r * L0 * math.exp(r * delta_lag)
