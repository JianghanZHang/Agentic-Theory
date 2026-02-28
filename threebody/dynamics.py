"""Three-body gravitational dynamics: Lagrange points, mass gap, and viability.

Implements the restricted circular three-body problem in the co-rotating frame:
  - Effective potential Ω(x,y;μ)                      (eq:eff-potential)
  - Lagrange points L1–L5 (fixed points of Ω)         (prop:lagrange)
  - Jacobi constant C_J = 2Ω at equilibrium           (eq:jacobi)
  - Mass gap Δ(μ) = C_J(L1) - C_J(L4)                (def:mass-gap)
  - Routh critical ratio μ_crit ≈ 0.0385              (thm:routh)
  - Stability eigenvalues at each Lagrange point       (prop:stability)

The core result: the mass gap opens at μ = 0⁺ (vacuum → fixed point)
and closes at μ = μ_crit (gravitational coupling kills stability).

Convention (Szebehely):
  M1 (mass 1-μ) at (-μ, 0)
  M2 (mass μ)   at (1-μ, 0)
  Unit of length = distance M1–M2
  Unit of time   = 1/ω (orbital period = 2π)
  G(M1+M2) = 1

Stdlib only — no external dependencies.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


# ── Routh critical mass ratio ────────────────────────────────
# L4/L5 are linearly stable iff μ < MU_CRIT.
# Exact value: μ_crit = ½(1 − √(69)/9) ≈ 0.03852…
MU_CRIT = 0.5 * (1.0 - math.sqrt(69) / 9)


@dataclass(frozen=True)
class LagrangePoint:
    """A Lagrange point (fixed point) of the restricted three-body problem."""

    name: str
    x: float
    y: float
    jacobi: float                   # Jacobi constant C_J = 2Ω
    stable: bool                    # linearly stable?
    eigenvalues: tuple[complex, ...]


@dataclass(frozen=True)
class MassGapResult:
    """Mass gap measurement at a given mass ratio."""

    mu: float             # mass ratio M2/(M1+M2)
    delta: float          # energy gap Δ = C_J(L1) − C_J(L4)
    C_L1: float           # Jacobi constant at L1
    C_L4: float           # Jacobi constant at L4
    L4_stable: bool       # is L4 linearly stable?
    gap_open: bool        # is the gap effectively open (Δ > 0 and L4 stable)?


class RestrictedThreeBody:
    """Restricted circular three-body problem in the co-rotating frame."""

    def __init__(self, mu: float) -> None:
        """Initialise with mass ratio μ = M2/(M1+M2) ∈ (0, 1)."""
        if not 0.0 < mu < 1.0:
            raise ValueError(f"mass ratio μ must be in (0,1), got {mu}")
        self.mu = mu

    # ── Effective potential ──────────────────────────────────

    def omega(self, x: float, y: float) -> float:
        """Effective potential Ω(x,y) in the co-rotating frame.

        Ω = ½(x² + y²) + (1−μ)/r₁ + μ/r₂
        """
        mu = self.mu
        r1 = math.sqrt((x + mu) ** 2 + y ** 2)
        r2 = math.sqrt((x - 1 + mu) ** 2 + y ** 2)
        return 0.5 * (x ** 2 + y ** 2) + (1 - mu) / r1 + mu / r2

    def jacobi_constant(
        self, x: float, y: float, vx: float = 0.0, vy: float = 0.0,
    ) -> float:
        """Jacobi constant C_J = 2Ω − v².  At equilibrium (v=0), C_J = 2Ω."""
        return 2 * self.omega(x, y) - (vx ** 2 + vy ** 2)

    # ── Gradient of Ω ────────────────────────────────────────

    def grad_omega(self, x: float, y: float) -> tuple[float, float]:
        """(∂Ω/∂x, ∂Ω/∂y)."""
        mu = self.mu
        r1 = math.sqrt((x + mu) ** 2 + y ** 2)
        r2 = math.sqrt((x - 1 + mu) ** 2 + y ** 2)
        r1_3 = r1 ** 3
        r2_3 = r2 ** 3
        dOdx = x - (1 - mu) * (x + mu) / r1_3 - mu * (x - 1 + mu) / r2_3
        dOdy = y - (1 - mu) * y / r1_3 - mu * y / r2_3
        return dOdx, dOdy

    # ── Hessian of Ω ─────────────────────────────────────────

    def hessian_omega(
        self, x: float, y: float,
    ) -> tuple[float, float, float]:
        """(Ω_xx, Ω_yy, Ω_xy) — second partial derivatives."""
        mu = self.mu
        r1 = math.sqrt((x + mu) ** 2 + y ** 2)
        r2 = math.sqrt((x - 1 + mu) ** 2 + y ** 2)
        r1_3, r1_5 = r1 ** 3, r1 ** 5
        r2_3, r2_5 = r2 ** 3, r2 ** 5

        Oxx = (
            1
            - (1 - mu) / r1_3 + 3 * (1 - mu) * (x + mu) ** 2 / r1_5
            - mu / r2_3 + 3 * mu * (x - 1 + mu) ** 2 / r2_5
        )
        Oyy = (
            1
            - (1 - mu) / r1_3 + 3 * (1 - mu) * y ** 2 / r1_5
            - mu / r2_3 + 3 * mu * y ** 2 / r2_5
        )
        Oxy = (
            3 * (1 - mu) * (x + mu) * y / r1_5
            + 3 * mu * (x - 1 + mu) * y / r2_5
        )
        return Oxx, Oyy, Oxy

    # ── Stability eigenvalues ────────────────────────────────

    def stability_eigenvalues(
        self, x: float, y: float,
    ) -> tuple[complex, ...]:
        """Eigenvalues of the linearised system at (x, y).

        Equations of motion in the co-rotating frame:
          ẍ − 2ẏ = Ω_x,   ÿ + 2ẋ = Ω_y

        Characteristic equation at equilibrium:
          λ⁴ + (4 − Ω_xx − Ω_yy)λ² + (Ω_xx·Ω_yy − Ω_xy²) = 0
        """
        Oxx, Oyy, Oxy = self.hessian_omega(x, y)

        # Coefficients of λ⁴ + a·λ² + b = 0
        a = 4.0 - Oxx - Oyy
        b = Oxx * Oyy - Oxy ** 2

        # Solve quadratic in s = λ²
        disc = a ** 2 - 4 * b
        eigenvalues: list[complex] = []

        if disc >= 0:
            sqrt_disc = math.sqrt(disc)
            for sign in (+1, -1):
                s = (-a + sign * sqrt_disc) / 2
                eigenvalues.extend(_sqrt_roots(s))
        else:
            # Complex conjugate pair for s
            sr = -a / 2
            si = math.sqrt(-disc) / 2
            for s in (complex(sr, si), complex(sr, -si)):
                eigenvalues.extend(_sqrt_roots_complex(s))

        return tuple(eigenvalues)

    def is_stable(self, x: float, y: float, tol: float = 1e-10) -> bool:
        """True if all eigenvalues have non-positive real part."""
        return all(
            ev.real <= tol for ev in self.stability_eigenvalues(x, y)
        )

    # ── Lagrange point computation ───────────────────────────

    def _find_collinear(
        self, x0: float, tol: float = 1e-12, max_iter: int = 200,
    ) -> float:
        """Find a collinear Lagrange point (y=0) near x0 via Newton's method.

        Solves ∂Ω/∂x = 0 at y = 0.
        """
        mu = self.mu
        x = x0
        for _ in range(max_iter):
            r1 = abs(x + mu)
            r2 = abs(x - 1 + mu)

            # f(x) = ∂Ω/∂x at y=0
            s1 = 1.0 if x + mu > 0 else -1.0
            s2 = 1.0 if x - 1 + mu > 0 else -1.0
            f = x - (1 - mu) * s1 / r1 ** 2 - mu * s2 / r2 ** 2

            # f'(x) = ∂²Ω/∂x² at y=0
            fp = 1 + 2 * (1 - mu) / r1 ** 3 + 2 * mu / r2 ** 3

            dx = -f / fp
            x += dx
            if abs(dx) < tol:
                break
        return x

    def _make_lagrange(self, name: str, x: float, y: float) -> LagrangePoint:
        cj = self.jacobi_constant(x, y)
        eigs = self.stability_eigenvalues(x, y)
        stable = self.is_stable(x, y)
        return LagrangePoint(name, x, y, cj, stable, eigs)

    def lagrange_L1(self) -> LagrangePoint:
        """L1: between M1 and M2 (saddle point)."""
        mu = self.mu
        x0 = 1 - mu - (mu / 3) ** (1 / 3)
        return self._make_lagrange("L1", self._find_collinear(x0), 0.0)

    def lagrange_L2(self) -> LagrangePoint:
        """L2: beyond M2, away from M1 (saddle point)."""
        mu = self.mu
        x0 = 1 - mu + (mu / 3) ** (1 / 3)
        return self._make_lagrange("L2", self._find_collinear(x0), 0.0)

    def lagrange_L3(self) -> LagrangePoint:
        """L3: beyond M1, away from M2 (saddle point)."""
        mu = self.mu
        x0 = -(1 + 5 * mu / 12)
        return self._make_lagrange("L3", self._find_collinear(x0), 0.0)

    def lagrange_L4(self) -> LagrangePoint:
        """L4: leading equilateral triangle point."""
        return self._make_lagrange(
            "L4", 0.5 - self.mu, math.sqrt(3) / 2,
        )

    def lagrange_L5(self) -> LagrangePoint:
        """L5: trailing equilateral triangle point."""
        return self._make_lagrange(
            "L5", 0.5 - self.mu, -math.sqrt(3) / 2,
        )

    def all_lagrange_points(self) -> list[LagrangePoint]:
        """Compute all five Lagrange points."""
        return [
            self.lagrange_L1(),
            self.lagrange_L2(),
            self.lagrange_L3(),
            self.lagrange_L4(),
            self.lagrange_L5(),
        ]

    # ── Mass gap ─────────────────────────────────────────────

    def mass_gap(self) -> MassGapResult:
        """Compute the mass gap Δ = C_J(L1) − C_J(L4).

        The gap is "open" when Δ > 0 and L4 is stable: the energy barrier
        between the saddle point L1 and the stable equilibrium L4 protects
        the fixed point.  The gap "closes" when L4 loses stability at
        μ = μ_crit ≈ 0.0385 (Routh's criterion).
        """
        L1 = self.lagrange_L1()
        L4 = self.lagrange_L4()
        delta = L1.jacobi - L4.jacobi
        gap_open = delta > 0 and L4.stable
        return MassGapResult(
            mu=self.mu,
            delta=delta,
            C_L1=L1.jacobi,
            C_L4=L4.jacobi,
            L4_stable=L4.stable,
            gap_open=gap_open,
        )

    # ── Orbit integration ────────────────────────────────────

    def integrate(
        self,
        x0: float,
        y0: float,
        vx0: float,
        vy0: float,
        dt: float = 0.001,
        T: float = 10.0,
    ) -> tuple[list[float], list[float], list[float]]:
        """Integrate equations of motion (symplectic Euler).

        Returns (t_arr, x_arr, y_arr).
        """
        n_steps = int(T / dt)
        t_arr = [0.0]
        x_arr = [x0]
        y_arr = [y0]
        x, y, vx, vy = x0, y0, vx0, vy0

        for i in range(1, n_steps + 1):
            dOdx, dOdy = self.grad_omega(x, y)
            ax = dOdx + 2 * vy
            ay = dOdy - 2 * vx
            vx += ax * dt
            vy += ay * dt
            x += vx * dt
            y += vy * dt
            t_arr.append(i * dt)
            x_arr.append(x)
            y_arr.append(y)

        return t_arr, x_arr, y_arr


# ── Helper: square roots of real / complex values ────────────

def _sqrt_roots(s: float) -> list[complex]:
    """Given s = λ², return the two roots λ = ±√s."""
    if s > 0:
        r = math.sqrt(s)
        return [complex(r, 0), complex(-r, 0)]
    elif s == 0:
        return [complex(0, 0), complex(0, 0)]
    else:
        r = math.sqrt(-s)
        return [complex(0, r), complex(0, -r)]


def _sqrt_roots_complex(s: complex) -> list[complex]:
    """Given complex s = λ², return the two roots λ = ±√s."""
    r = abs(s) ** 0.5
    theta = math.atan2(s.imag, s.real) / 2
    lam = complex(r * math.cos(theta), r * math.sin(theta))
    return [lam, complex(-lam.real, -lam.imag)]
