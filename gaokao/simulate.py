"""Gaokao Reform: disparity analysis and equal-weight simulation.

Core question: 如果每个省同等重要, 985录取率会怎样变化?

Two models:
  1. Current system (现行制度) — fixed quotas, structural disparity
  2. Equal-weight reform (等权改革) — w_i = const, C/n per province
  3. Population-proportional (人口比例) — slots ∝ exam takers

Usage:
    python -m gaokao.simulate
"""

from __future__ import annotations

from gaokao.data import Province, PROVINCES, YEAR, total_exam_takers
from gaokao.model import ReformModel


# ════════════════════════════════════════════
#   ANSI colors — matches paper's color scheme
# ════════════════════════════════════════════

_B   = "\033[34m"      # blue  (water)
_R   = "\033[31m"      # red   (knife / disparity)
_C   = "\033[36m"      # cyan  (reform)
_Y   = "\033[33m"      # yellow (caution)
_G   = "\033[32m"      # green (improvement)
_W   = "\033[1m"       # bold  (emphasis)
_0   = "\033[0m"       # reset


def run_current_system() -> None:
    """Display current system disparity analysis."""
    print("\n" + "═" * 65)
    print(f"  {_W}Current System / 现行制度: 2024 Disparity Analysis{_0}")
    print("═" * 65)

    model = ReformModel()
    stats = model.summary()
    cur = stats["current"]

    print(f"\n  Total exam takers / 考生总数:  {total_exam_takers():>12,}")
    print(f"  Total 985 capacity / 985总容量: {model.C:>12,}")
    print(f"  National avg 985 rate:         {model.C / total_exam_takers():>11.2%}")
    print(f"  Number of provinces:           {stats['n_provinces']:>12}")

    # Disparity metrics
    print(f"\n  {_W}Disparity Metrics / 不平等指标:{_0}")
    print(f"    Max/Min ratio: {_R}{cur['disparity_ratio']:.1f}x{_0}"
          f"  ({cur['max_province']} {cur['max_rate']:.2%}"
          f" vs {cur['min_province']} {cur['min_rate']:.2%})")
    print(f"    Gini coefficient: {_R}{cur['gini']:.4f}{_0}")
    print(f"    Coefficient of variation: {_R}{cur['cv']:.4f}{_0}")

    # Top 5 and bottom 5
    sorted_p = sorted(PROVINCES, key=lambda p: p.rate_985, reverse=True)

    print(f"\n  {_G}Top 5 — 985录取率最高 / Highest 985 admission rate:{_0}")
    for i, p in enumerate(sorted_p[:5]):
        slots = round(p.exam_takers * p.rate_985)
        print(f"    {i+1}. {p.name_zh} ({p.name_en}): "
              f"{_G}{p.rate_985:.2%}{_0}  "
              f"({slots:,} / {p.exam_takers:,})")

    print(f"\n  {_R}Bottom 5 — 985录取率最低 / Lowest 985 admission rate:{_0}")
    for i, p in enumerate(sorted_p[-5:]):
        slots = round(p.exam_takers * p.rate_985)
        print(f"    {31-4+i}. {p.name_zh} ({p.name_en}): "
              f"{_R}{p.rate_985:.2%}{_0}  "
              f"({slots:,} / {p.exam_takers:,})")

    # The core inequality
    top = sorted_p[0]
    bot = sorted_p[-1]
    ratio = top.rate_985 / bot.rate_985
    print(f"\n  {_R}┌──────────────────────────────────────────────────────────┐{_0}")
    print(f"  {_R}│{_0}  核心不平等 / Core Inequality:                           {_R}│{_0}")
    print(f"  {_R}│{_0}  {top.name_zh} ({top.name_en}): {top.rate_985:.2%}"
          f" — {top.exam_takers:,} takers             {_R}│{_0}")
    print(f"  {_R}│{_0}  {bot.name_zh} ({bot.name_en}): {bot.rate_985:.2%}"
          f" — {bot.exam_takers:,} takers          {_R}│{_0}")
    print(f"  {_R}│{_0}  Ratio: {_R}{ratio:.1f}x{_0}"
          f"  — same country, same exam, {ratio:.1f}x difference  {_R}│{_0}")
    print(f"  {_R}│{_0}  河南 has {_R}{bot.exam_takers/top.exam_takers:.0f}x{_0}"
          f" more students but {_R}{ratio:.1f}x{_0} worse rate.        {_R}│{_0}")
    print(f"  {_R}└──────────────────────────────────────────────────────────┘{_0}")


def run_reform_comparison() -> None:
    """Compare current system with equal-weight and proportional reforms."""
    print("\n" + "═" * 65)
    print(f"  {_W}Reform Comparison / 改革对比{_0}")
    print("═" * 65)

    model = ReformModel()

    for method, label_en, label_zh in [
        ("equal", "Equal Weight", "等权"),
        ("proportional", "Population Proportional", "人口比例"),
    ]:
        stats = model.summary(method)
        cur = stats["current"]
        ref = stats["reform"]

        print(f"\n  ── Method: {_C}{label_en} / {label_zh}{_0} ──")
        print(f"    {'Metric':<28} {'Current':>10} {'Reform':>10} {'Change':>10}")
        print(f"    {'─'*28} {'─'*10} {'─'*10} {'─'*10}")

        # Disparity ratio
        d_cur = cur["disparity_ratio"]
        d_ref = ref["disparity_ratio"]
        d_chg = d_ref - d_cur
        chg_c = _G if d_chg < 0 else _R
        print(f"    {'Max/Min ratio':<28} {d_cur:>9.1f}x {d_ref:>9.1f}x"
              f" {chg_c}{d_chg:>+9.1f}x{_0}")

        # Gini
        g_cur = cur["gini"]
        g_ref = ref["gini"]
        g_chg = g_ref - g_cur
        chg_c = _G if g_chg < 0 else _R
        print(f"    {'Gini coefficient':<28} {g_cur:>10.4f} {g_ref:>10.4f}"
              f" {chg_c}{g_chg:>+10.4f}{_0}")

        # CV
        cv_cur = cur["cv"]
        cv_ref = ref["cv"]
        cv_chg = cv_ref - cv_cur
        chg_c = _G if cv_chg < 0 else _R
        print(f"    {'Coeff. of variation':<28} {cv_cur:>10.4f} {cv_ref:>10.4f}"
              f" {chg_c}{cv_chg:>+10.4f}{_0}")

        # Max/Min provinces
        print(f"\n    Highest rate: {ref['max_province']} {ref['max_rate']:.2%}"
              f"  (was: {cur['max_province']} {cur['max_rate']:.2%})")
        print(f"    Lowest rate:  {ref['min_province']} {ref['min_rate']:.2%}"
              f"  (was: {cur['min_province']} {cur['min_rate']:.2%})")


def run_province_detail() -> None:
    """Show per-province impact of equal-weight reform."""
    print("\n" + "═" * 65)
    print(f"  {_W}Per-Province Impact / 各省影响 (Equal Weight){_0}")
    print("═" * 65)

    model = ReformModel()
    allocs = model.compute_allocation("equal")

    # Sort by delta_rate (biggest gainers first)
    allocs.sort(key=lambda a: a.delta_rate, reverse=True)

    print(f"\n  {'Province':<14} {'中文':<5} {'Takers':>10}"
          f" {'Cur%':>7} {'Ref%':>7} {'Δ%':>8} {'ΔSlots':>8}")
    print(f"  {'─'*14} {'─'*5} {'─'*10}"
          f" {'─'*7} {'─'*7} {'─'*8} {'─'*8}")

    gainers = 0
    losers = 0
    for a in allocs:
        p = a.province
        delta_c = _G if a.delta_rate > 0 else _R if a.delta_rate < 0 else ""
        delta_r = _0 if delta_c else ""
        if a.delta_rate > 0.0001:
            gainers += 1
        elif a.delta_rate < -0.0001:
            losers += 1
        print(f"  {p.name_en:<14} {p.name_zh:<5} {p.exam_takers:>10,}"
              f" {a.current_rate:>6.2%} {a.reform_rate:>6.2%}"
              f" {delta_c}{a.delta_rate:>+7.2%}{delta_r}"
              f" {delta_c}{a.delta_slots:>+8,}{delta_r}")

    print(f"\n  Gainers: {_G}{gainers}{_0}  |  Losers: {_R}{losers}{_0}"
          f"  |  Unchanged: {len(allocs) - gainers - losers}")

    # Biggest gainer and biggest loser
    biggest_gain = allocs[0]
    biggest_loss = allocs[-1]
    print(f"\n  Biggest gainer: {_G}{biggest_gain.province.name_zh}{_0}"
          f" ({biggest_gain.province.name_en}):"
          f" {biggest_gain.current_rate:.2%} → {biggest_gain.reform_rate:.2%}"
          f" ({biggest_gain.delta_rate:+.2%})")
    print(f"  Biggest loser:  {_R}{biggest_loss.province.name_zh}{_0}"
          f" ({biggest_loss.province.name_en}):"
          f" {biggest_loss.current_rate:.2%} → {biggest_loss.reform_rate:.2%}"
          f" ({biggest_loss.delta_rate:+.2%})")


def run_viability_connection() -> None:
    """Connect to viability theory: the knife is the mean."""
    print("\n" + "═" * 65)
    print(f"  {_W}Viability Connection / 理论联系{_0}")
    print("═" * 65)

    model = ReformModel()
    cur_rates = model.current_rates()
    mean_rate = sum(cur_rates) / len(cur_rates)
    weighted_mean = model.C / total_exam_takers()

    print(f"\n  {_B}Mean field / 平均场:{_0}")
    print(f"    Unweighted mean rate (arithmetic): {mean_rate:.2%}")
    print(f"    Weighted mean rate (national):     {weighted_mean:.2%}")

    # Who is above/below the knife
    above = [(p, p.rate_985) for p in PROVINCES if p.rate_985 > weighted_mean]
    below = [(p, p.rate_985) for p in PROVINCES if p.rate_985 <= weighted_mean]

    print(f"\n    Above the mean (985 rate > {weighted_mean:.2%}): "
          f"{_G}{len(above)}{_0} provinces")
    print(f"    Below the mean (985 rate ≤ {weighted_mean:.2%}): "
          f"{_R}{len(below)}{_0} provinces")

    pop_above = sum(p.exam_takers for p, _ in above)
    pop_below = sum(p.exam_takers for p, _ in below)
    print(f"\n    Population above mean: {pop_above:>10,} ({pop_above/total_exam_takers():.1%})")
    print(f"    Population below mean: {pop_below:>10,} ({pop_below/total_exam_takers():.1%})")

    print(f"\n  {_W}The knife is the mean / 刀就是平均值:{_0}")
    print(f"    The national average 985 rate ({weighted_mean:.2%}) is the knife.")
    print(f"    {_R}{len(below)}{_0} provinces with {_R}{pop_below/total_exam_takers():.0%}{_0}"
          f" of all students are below it.")
    print(f"    The viability kernel K = provinces with rate ≥ mean.")
    print(f"    Temporal linearity: every year the exam happens, irreversibly.")
    print(f"    The reform's goal: bring the knife to equal-weight = flatten it.")

    # Compare all three: current, equal-weight, population-proportional
    print(f"\n  {_W}Equity measures / 公平指标:{_0}")
    gini_cur = model.gini()
    gini_eq = model.gini(model.reform_rates("equal"))
    gini_pp = model.gini(model.reform_rates("proportional"))

    dr_cur = model.disparity_ratio()
    dr_eq = model.disparity_ratio(model.reform_rates("equal"))
    dr_pp = model.disparity_ratio(model.reform_rates("proportional"))

    print(f"    {'Model':<28} {'Gini':>8} {'Max/Min':>8}")
    print(f"    {'─'*28} {'─'*8} {'─'*8}")
    print(f"    {_R}{'Current / 现行':28}{_0} {_R}{gini_cur:>8.4f}{_0} {_R}{dr_cur:>7.1f}x{_0}")
    print(f"    {'Equal-weight / 等权':28} {_Y}{gini_eq:>8.4f}{_0} {_Y}{dr_eq:>7.1f}x{_0}")
    print(f"    {_G}{'Pop-proportional / 人口比例':28}{_0} {_G}{gini_pp:>8.4f}{_0} {_G}{dr_pp:>7.1f}x{_0}")

    print(f"\n    {_Y}Surprise / 意外发现:{_0}")
    print(f"    Equal-weight makes Gini WORSE ({gini_cur:.3f} → {gini_eq:.3f}).")
    print(f"    Why? C/31 slots → 西藏 (36k students) gets 14.7%,")
    print(f"    while 河南 (1.36M students) gets 0.39%. Population")
    print(f"    disparity dominates when slots are equal.")
    print(f"\n    The correct reform: population-proportional allocation.")
    print(f"    Every student has equal probability ≈ {model.C/total_exam_takers():.2%},")
    print(f"    regardless of province. Gini → {gini_pp:.4f} ≈ 0.")

    print(f"\n  {_C}┌──────────────────────────────────────────────────────────┐{_0}")
    print(f"  {_C}│{_0}  Reform verdict / 改革结论:                               {_C}│{_0}")
    print(f"  {_C}│{_0}  Equal-weight (等权) ≠ equal-probability (等概率).        {_C}│{_0}")
    print(f"  {_C}│{_0}  Equal weight per province + unequal population           {_C}│{_0}")
    print(f"  {_C}│{_0}  → WORSE per-capita equity (Gini ↑).                     {_C}│{_0}")
    print(f"  {_C}│{_0}                                                           {_C}│{_0}")
    print(f"  {_C}│{_0}  The correct reform: slots ∝ exam_takers.                {_C}│{_0}")
    print(f"  {_C}│{_0}  This gives every student equal probability ~{model.C/total_exam_takers():.2%}.      {_C}│{_0}")
    print(f"  {_C}│{_0}  Gini: {_R}{gini_cur:.3f}{_0} → {_G}{gini_pp:.4f}{_0}  "
          f"(reduction: {(1 - gini_pp/gini_cur)*100:.0f}%)                    {_C}│{_0}")
    print(f"  {_C}│{_0}  Max/Min: {_R}{dr_cur:.1f}x{_0} → {_G}{dr_pp:.1f}x{_0}  "
          f"(from {dr_cur:.1f}x disparity to ~{dr_pp:.1f}x)                 {_C}│{_0}")
    print(f"  {_C}│{_0}                                                           {_C}│{_0}")
    print(f"  {_C}│{_0}  The knife: provincial quota ≠ population share.          {_C}│{_0}")
    print(f"  {_C}│{_0}  Reform: align quotas to population → knife disappears.   {_C}│{_0}")
    print(f"  {_C}└──────────────────────────────────────────────────────────┘{_0}")


def main() -> None:
    print("═" * 65)
    print(f"  {_W}Gaokao Reform Analysis / 高考改革分析{_0}")
    print(f"  Data year: {YEAR}")
    print("═" * 65)

    run_current_system()
    run_reform_comparison()
    run_province_detail()
    run_viability_connection()


if __name__ == "__main__":
    main()
