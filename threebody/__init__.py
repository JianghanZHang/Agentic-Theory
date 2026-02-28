"""Three-body problem: Lagrange fixed points, mass gap, and gravitational closure.

Core question: 三体问题能做吗？ 放一个 fixed point, 打开一个 mass gap, 用引力合上.

Implements the restricted circular three-body problem in the co-rotating frame:
  - Lagrange points L1–L5 (fixed points of the effective potential)
  - Mass gap Δ(μ) = C_J(L1) - C_J(L4)         (energy barrier)
  - Routh critical ratio μ_crit ≈ 0.0385       (stability boundary)
  - Phase transition: vacuum → gap open → gap closed by gravity

Stdlib only — no external dependencies.
"""

from threebody.dynamics import (
    RestrictedThreeBody,
    LagrangePoint,
    MassGapResult,
    MU_CRIT,
)

__all__ = ["RestrictedThreeBody", "LagrangePoint", "MassGapResult", "MU_CRIT"]
