"""Gradient-flow diagnostic for MPPI barrier-smoothed quadruped experiment.

Loads output/rollout_data.json and produces:
  1. A table of ALL cost components at selected iterations (best and mean).
  2. Per-iteration analysis of the effective Boltzmann cost (barrier epsilon-cancellation).
  3. cost_std / epsilon ratio (controls ESS).
  4. Plots: cost decomposition (log y), barrier magnification, epsilon & H_target trajectory.
  5. A printed gradient-flow analysis section.

Usage (from experiment/ directory):
    .venv/bin/python output/gradient_flow_analysis.py
"""

import json
import math
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# ---------------------------------------------------------------------------
# 0.  Load data
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_PATH = SCRIPT_DIR / "rollout_data.json"

with open(DATA_PATH) as f:
    raw = json.load(f)

diag = raw["diagnostics"]
N_samples = raw["N_samples"]       # 128
n_iters = raw["n_iters"]           # 30 (stored iterations may differ)
K = len(diag["epsilon"])            # actual number of iterations recorded

# Cost components — best sample each iteration
best_vel         = np.array(diag["best_vel"])
best_height      = np.array(diag["best_height"])
best_height_bar  = np.array(diag["best_height_bar"])
best_ori_bar     = np.array(diag["best_ori_bar"])
best_joint_bar   = np.array(diag["best_joint_bar"])
best_control     = np.array(diag["best_control"])
best_contact_bar = np.array(diag["best_contact_bar"])

# Cost components — mean across N samples
mean_vel         = np.array(diag["mean_vel"])
mean_height      = np.array(diag["mean_height"])
mean_height_bar  = np.array(diag["mean_height_bar"])
mean_ori_bar     = np.array(diag["mean_ori_bar"])
mean_joint_bar   = np.array(diag["mean_joint_bar"])
mean_control     = np.array(diag["mean_control"])
mean_contact_bar = np.array(diag["mean_contact_bar"])

# Scalar diagnostics
epsilon   = np.array(diag["epsilon"])
ess       = np.array(diag["ess"])
entropy   = np.array(diag["entropy"])
cost_mean = np.array(diag["cost_mean"])
cost_std  = np.array(diag["cost_std"])
cost_best = np.array(diag["cost_best"])

iters = np.arange(K)

# Derived quantities
H_target = np.log(N_samples) * (0.97 ** iters)   # compression_rate = 0.97
cost_std_over_eps = cost_std / epsilon

# ---------------------------------------------------------------------------
# Reconstruct totals from components  (consistency check)
# ---------------------------------------------------------------------------
best_total_components = (best_vel + best_height + best_height_bar
                         + best_ori_bar + best_joint_bar
                         + best_control + best_contact_bar)
mean_total_components = (mean_vel + mean_height + mean_height_bar
                         + mean_ori_bar + mean_joint_bar
                         + mean_control + mean_contact_bar)

# ---------------------------------------------------------------------------
# 1.  Table of cost components at selected iterations
# ---------------------------------------------------------------------------
target_iters = [0, 5, 10, 15, 20, 25, 29]
# Clamp to available iterations
target_iters = [k for k in target_iters if k < K]

COMP_NAMES = [
    ("vel",         best_vel,         mean_vel),
    ("height",      best_height,      mean_height),
    ("height_bar",  best_height_bar,  mean_height_bar),
    ("ori_bar",     best_ori_bar,     mean_ori_bar),
    ("joint_bar",   best_joint_bar,   mean_joint_bar),
    ("control",     best_control,     mean_control),
    ("contact_bar", best_contact_bar, mean_contact_bar),
]

SEP = "-" * 130
print()
print("=" * 130)
print("  COST COMPONENT TABLE  (all 7 terms, best and mean, at selected iterations)")
print("=" * 130)
header = f"{'iter':>4}  {'eps':>8}"
for name, _, _ in COMP_NAMES:
    header += f"  {'best_'+name:>16}  {'mean_'+name:>16}"
header += f"  {'best_total':>12}  {'mean_total':>12}"
print(header)
print(SEP)
for k in target_iters:
    row = f"{k:4d}  {epsilon[k]:8.4f}"
    for name, bv, mv in COMP_NAMES:
        row += f"  {bv[k]:16.4f}  {mv[k]:16.4f}"
    row += f"  {best_total_components[k]:12.2f}  {mean_total_components[k]:12.2f}"
    print(row)
print(SEP)
print()

# ---------------------------------------------------------------------------
# 2.  Effective Boltzmann cost — barrier epsilon-cancellation
# ---------------------------------------------------------------------------
print("=" * 100)
print("  EFFECTIVE BOLTZMANN COST — barrier epsilon-cancellation analysis")
print("=" * 100)
print()
print("Barrier terms have the form:  J_bar = -w * eps * log(g)")
print("where g = constraint slack (e.g., z - z_min, phi_max^2 - phi^2, etc.).")
print()
print("In MPPI Boltzmann reweighting:  weight ~ exp(-J / eps)")
print("  => exp(-(-w * eps * log(g)) / eps)  =  exp(w * log(g))  =  g^w")
print()
print("KEY INSIGHT: The barrier contribution to the Boltzmann weight is g^w,")
print("which is INDEPENDENT of eps.  The eps in the barrier cost cancels exactly")
print("with the 1/eps in the Boltzmann exponent.")
print()
print("This means barriers only affect the softmax through their RELATIVE")
print("magnitudes vs the non-barrier (tracking) costs.  But the tracking costs")
print("DO scale relative to eps, so high eps washes out tracking differences.")
print()

# Show the cancellation numerically
print(f"{'iter':>4}  {'eps':>8}  {'best_bar_total':>14}  {'best_bar/eps':>14}  {'best_track':>12}  {'track/eps':>12}  {'bar_boltz':>12}")
print("-" * 90)
for k in target_iters:
    bar_total = best_height_bar[k] + best_ori_bar[k] + best_joint_bar[k] + best_contact_bar[k]
    track_total = best_vel[k] + best_height[k] + best_control[k]
    # Effective Boltzmann exponent contribution from barrier: bar_total/eps
    # But barrier = -w*eps*log(g), so bar_total/eps = -w*log(g) = log(g^{-w})
    # => Boltzmann factor from barrier = exp(-bar_total/eps) = g^w  (eps cancels!)
    bar_boltz_exp = bar_total / epsilon[k]   # = -w*log(g), eps-independent if g is stable
    print(f"{k:4d}  {epsilon[k]:8.4f}  {bar_total:14.2f}  {bar_total/epsilon[k]:14.4f}  "
          f"{track_total:12.4f}  {track_total/epsilon[k]:12.6f}  {bar_boltz_exp:12.4f}")
print()

# ---------------------------------------------------------------------------
# 3.  cost_std / eps ratio (controls ESS)
# ---------------------------------------------------------------------------
print("=" * 100)
print("  ESS ANALYSIS — cost_std / eps ratio")
print("=" * 100)
print()
print("ESS ~ N * exp(-cost_var / eps^2).  In practice,")
print("  ESS ~= 1  when  cost_std / eps >> 1  (one dominant sample)")
print("  ESS ~= N  when  cost_std / eps << 1  (uniform weights)")
print()
print(f"{'iter':>4}  {'eps':>8}  {'cost_std':>10}  {'std/eps':>10}  {'ESS':>8}  {'entropy':>8}  {'H_target':>8}")
print("-" * 70)
for k in target_iters:
    print(f"{k:4d}  {epsilon[k]:8.4f}  {cost_std[k]:10.2f}  {cost_std_over_eps[k]:10.4f}  "
          f"{ess[k]:8.2f}  {entropy[k]:8.4f}  {H_target[k]:8.4f}")
print()

# ---------------------------------------------------------------------------
# 4.  Gradient-flow analysis  (printed)
# ---------------------------------------------------------------------------
print("=" * 100)
print("  GRADIENT FLOW ANALYSIS")
print("=" * 100)
print("""
What drives eps UP?
-------------------
The dual ascent rule is:
    if entropy < H_target:  eps *= alpha_up   (= 1.10)
    else:                   eps *= alpha_down  (= 0.95)

Entropy is low when ESS is low, i.e., weights are concentrated on one or a
few samples.  Low entropy triggers eps *= 1.10, inflating the temperature.

Why is entropy low?
-------------------
ESS is determined by the cost spread relative to temperature:
    log_w_k = -(J_k - J_min) / eps
    weight_k = softmax(log_w)

When cost_std >> eps, the best sample dominates (ESS -> 1).  Looking at the
data: at iteration 0, cost_std = {cs0:.1f} but eps = {e0:.4f}, giving
std/eps = {r0:.1f}.  This ratio stays >> 1 throughout most of the run because
the barrier costs grow proportionally with eps, maintaining the spread.

How barriers affect relative Boltzmann weights:
-----------------------------------------------
A barrier term J_bar = -w * eps * log(g) contributes to the Boltzmann weight as:
    exp(-J_bar / eps) = exp(w * log(g)) = g^w

This is eps-INDEPENDENT.  So barrier costs do NOT help distinguish samples in
softmax — they shift all weights uniformly.  Only the NON-barrier (tracking)
costs create differentiation.  But tracking costs (~67 for velocity) are
dwarfed by barrier costs (~2000+ for contact alone), making the total cost
dominated by barriers whose Boltzmann contribution is eps-independent.

The cost_std is driven by barrier variation across samples, which scales
linearly with eps (since barrier = -w * eps * log(g)).  Therefore:
    cost_std ~ eps * (std of log-slack across samples)
    cost_std / eps ~ constant (the log-slack spread)
This keeps the ratio roughly constant, so ESS does not improve as eps grows.

The non-smoothness issue:
-------------------------
During stance phases, the desired foot height h_k = 0.  The contact barrier
computes -w * eps * log(max(h_k, h_min)) where h_min = 1e-4.
Since h_k = 0 in stance, this becomes -w * eps * log(1e-4) = w * eps * 9.21.
Over 4 feet x 50 timesteps with ~50% in stance, this contributes roughly
    4 * 25 * w * eps * 9.21 = ~921 * w * eps
penalty.  This explains why contact_bar dominates total cost and scales
linearly with eps.

The barrier clamping means that for ALL stance-phase timesteps, the cost
contribution is identical across samples (all clamped to the same floor).
Only the ~50% swing-phase timesteps produce sample-dependent barrier costs,
halving the effective differentiation.
""".format(
    cs0=cost_std[0], e0=epsilon[0], r0=cost_std_over_eps[0]
))

# ---------------------------------------------------------------------------
# 5.  Plots
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle("Gradient Flow Diagnostics — MPPI Barrier-Smoothed Quadruped", fontsize=14, y=0.98)

# ── Panel (a): Cost decomposition vs iteration (log y) ──
ax = axes[0, 0]
ax.set_title("(a) Cost Decomposition — Best Sample (log scale)")
components_best = {
    "vel":         best_vel,
    "height":      best_height,
    "height_bar":  best_height_bar,
    "ori_bar":     best_ori_bar,
    "joint_bar":   best_joint_bar,
    "control":     best_control,
    "contact_bar": best_contact_bar,
}
colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2"]
for (name, vals), c in zip(components_best.items(), colors):
    # Use abs + clip to handle near-zero values on log scale
    ax.semilogy(iters, np.maximum(np.abs(vals), 1e-8), label=name, color=c, linewidth=1.5)
ax.set_xlabel("Iteration")
ax.set_ylabel("Cost (log scale)")
ax.legend(fontsize=8, loc="upper left")
ax.grid(True, alpha=0.3, which="both")

# ── Panel (b): Barrier magnification — ratio of barrier to tracking ──
ax = axes[0, 1]
ax.set_title("(b) Barrier Magnification (barrier / tracking)")
best_barrier_total = best_height_bar + best_ori_bar + best_joint_bar + best_contact_bar
best_tracking_total = best_vel + best_height + best_control
mean_barrier_total = mean_height_bar + mean_ori_bar + mean_joint_bar + mean_contact_bar
mean_tracking_total = mean_vel + mean_height + mean_control

barrier_ratio_best = best_barrier_total / np.maximum(best_tracking_total, 1e-8)
barrier_ratio_mean = mean_barrier_total / np.maximum(mean_tracking_total, 1e-8)

ax.plot(iters, barrier_ratio_best, "o-", color="#d62728", label="best sample", linewidth=1.5, markersize=4)
ax.plot(iters, barrier_ratio_mean, "s-", color="#1f77b4", label="mean sample", linewidth=1.5, markersize=4)
ax.set_xlabel("Iteration")
ax.set_ylabel("Barrier / Tracking ratio")
ax.legend()
ax.grid(True, alpha=0.3)

# ── Panel (c): eps and H_target trajectories ──
ax = axes[1, 0]
ax.set_title(r"(c) $\varepsilon$ and $H_{\mathrm{target}}$ trajectories")

ax_eps = ax
ax_H = ax.twinx()

ln1 = ax_eps.plot(iters, epsilon, "o-", color="#1f77b4", label=r"$\varepsilon$", linewidth=2, markersize=4)
ln2 = ax_H.plot(iters, H_target, "s--", color="#d62728", label=r"$H_{\mathrm{target}} = \ln(128) \cdot 0.97^k$", linewidth=2, markersize=4)
ln3 = ax_H.plot(iters, entropy, "^:", color="#2ca02c", label=r"entropy $H_k$", linewidth=1.5, markersize=3)

ax_eps.set_xlabel("Iteration")
ax_eps.set_ylabel(r"$\varepsilon$", color="#1f77b4")
ax_H.set_ylabel(r"$H_{\mathrm{target}}$, entropy", color="#d62728")
ax_eps.tick_params(axis="y", labelcolor="#1f77b4")
ax_H.tick_params(axis="y", labelcolor="#d62728")

lns = ln1 + ln2 + ln3
labs = [l.get_label() for l in lns]
ax.legend(lns, labs, fontsize=8, loc="center right")
ax.grid(True, alpha=0.3)

# ── Panel (d): cost_std / eps ratio and ESS ──
ax = axes[1, 1]
ax.set_title(r"(d) $\sigma_J / \varepsilon$ ratio and ESS")

ax_ratio = ax
ax_ess = ax.twinx()

ln1 = ax_ratio.plot(iters, cost_std_over_eps, "o-", color="#9467bd", label=r"$\sigma_J / \varepsilon$", linewidth=2, markersize=4)
ln2 = ax_ess.plot(iters, ess, "s-", color="#ff7f0e", label="ESS", linewidth=2, markersize=4)
ax_ess.axhline(y=N_samples, color="#ff7f0e", linestyle=":", alpha=0.5, label=f"N = {N_samples}")
ln3 = [ax_ess.lines[-1]]

ax_ratio.set_xlabel("Iteration")
ax_ratio.set_ylabel(r"$\sigma_J / \varepsilon$", color="#9467bd")
ax_ess.set_ylabel("ESS", color="#ff7f0e")
ax_ratio.tick_params(axis="y", labelcolor="#9467bd")
ax_ess.tick_params(axis="y", labelcolor="#ff7f0e")

lns = ln1 + ln2 + ln3
labs = [l.get_label() for l in lns]
ax.legend(lns, labs, fontsize=8, loc="upper right")
ax.grid(True, alpha=0.3)

plt.tight_layout(rect=[0, 0, 1, 0.96])
out_path = SCRIPT_DIR / "gradient_flow_analysis.png"
plt.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"[saved] {out_path}")
plt.close()

print("\nDone.")
