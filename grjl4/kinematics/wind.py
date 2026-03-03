"""
Stochastic wind field — the adversary.

Wind is a random external wrench applied to placed blocks via
data.xfrc_applied.  It tests grasp/stack stability and forces
the controller to detect and recover from perturbations.

Three regimes (from contact_laplacian.lambda1_effective):
    λ₁_eff ≥ ε    → stable, no action needed
    0 < λ₁_eff < ε → sliding, regrasp may save it
    λ₁_eff ≤ 0     → toppled, REPLAN required

The wind magnitude F_max is annealed during curriculum training.
"""

import numpy as np


def _random_unit_vector_on_S2(rng: np.random.Generator) -> np.ndarray:
    """Uniform random unit vector on the 2-sphere."""
    # Marsaglia's method
    while True:
        u = rng.uniform(-1, 1, size=2)
        s = u[0]**2 + u[1]**2
        if s < 1.0:
            break
    sq = np.sqrt(1 - s)
    return np.array([2 * u[0] * sq, 2 * u[1] * sq, 1 - 2 * s])


class Wind:
    """Stochastic wind field applied to placed blocks.

    Parameters
    ----------
    F_max : float
        Maximum gust magnitude (N).  0 = no wind.
    horizontal_only : bool
        If True, wind direction is restricted to the xy-plane.
        Horizontal gusts are the primary destabiliser for stacks.
    seed : int or None
        RNG seed for reproducibility.
    """

    def __init__(self, F_max: float = 0.0, horizontal_only: bool = True,
                 seed: int | None = None):
        self.F_max = F_max
        self.horizontal_only = horizontal_only
        self._rng = np.random.default_rng(seed)
        self._last_force = np.zeros(3)

    def sample(self) -> np.ndarray:
        """Sample a random gust: magnitude * direction."""
        if self.F_max <= 0:
            self._last_force[:] = 0
            return self._last_force.copy()

        A = self._rng.uniform(0, self.F_max)

        if self.horizontal_only:
            theta = self._rng.uniform(0, 2 * np.pi)
            direction = np.array([np.cos(theta), np.sin(theta), 0.0])
        else:
            direction = _random_unit_vector_on_S2(self._rng)

        self._last_force = A * direction
        return self._last_force.copy()

    def apply(self, data, placed_body_ids: list[int]):
        """Apply wind to all placed blocks via xfrc_applied.

        Parameters
        ----------
        data : MjData
            MuJoCo simulation data.
        placed_body_ids : list[int]
            Body IDs of blocks that have been placed (not being held).
        """
        F = self.sample()
        for bid in placed_body_ids:
            data.xfrc_applied[bid, :3] = F    # force (world frame)
            data.xfrc_applied[bid, 3:] = 0.0  # no torque

    def clear(self, data, body_ids: list[int]):
        """Remove wind force from specified bodies."""
        for bid in body_ids:
            data.xfrc_applied[bid, :] = 0.0

    @property
    def last_force(self) -> np.ndarray:
        """Last sampled wind force vector (for logging/display)."""
        return self._last_force.copy()
