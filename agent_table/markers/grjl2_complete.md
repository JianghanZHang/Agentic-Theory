# GRJL 2.0 — Completion Marker

**Completed**: 2026-02-28T17:xx:xx

## Files created

```
grjl2/
  __init__.py
  order_parameter.py        # 160 lines — core ρ computation + smooth w(ρ)
  rho_sampler.py             # 190 lines — MPPI with continuous ρ
  pmp_rho_solver.py          # 340 lines — PMP with ρ-weighted Laplacian
  threebody_rho.py           # 570 lines — main simulator (reactive + PMP)
  compare_v1_v2.py           # 110 lines — 1.0 vs 2.0 comparison
  dribble.xml                # 80 lines  — MuJoCo ball-dribble scene
  dribble_controller.py      # 380 lines — three-term dribble controller
  bspline_trajectory.py -> ../grjl/bspline_trajectory.py
  spectral_analytical.py -> ../grjl/spectral_analytical.py
```

## Verification Results

| ID   | Criterion                    | Result |
|------|------------------------------|--------|
| V2.1 | Reactive runs headless       | PASS   |
| V2.2 | PMP runs headless            | PASS   |
| V2.4 | ρ phase crossings            | 16     |
| V2.5 | dw/dρ analytical accuracy    | 7.5e-9 |
| V2.6 | Cost finite                  | J=2.90 |
| V2.7 | Comparison plot              | PASS   |
| V2.8 | Bang fraction (reactive)     | 2.3%   |
| V2.8 | Bang fraction (PMP)          | 16.1%  |
| V3.1 | Dribble runs headless        | PASS   |
| V3.2 | Ball bounces ≥ 3             | 33     |
| V3.3 | ρ spikes at bounce           | PASS (ρ_max=436) |
| V3.5 | Singular ≫ bang              | PASS (bang=8.3%) |

## Key design decision

ρ = w_damper / w_natural (ratio of tidal coupling weights), not force ratio.
This ensures ρ crosses 1.0 at the meaningful phase transition.
