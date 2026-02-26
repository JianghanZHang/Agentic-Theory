"""2024 Gaokao provincial data -- compiled from public Chinese education sources.

Sources (all accessed February 2026):
  - Zhihu: https://zhuanlan.zhihu.com/p/702863920  (报名人数)
  - Zhihu: https://zhuanlan.zhihu.com/p/717369168  (985/211/一本/本科 rates)
  - 163.com: https://www.163.com/dy/article/JF1LAEF80549R6EJ.html
  - Gotohui (聚汇数据): https://www.gotohui.com/edu/topic-4285  (985 rates)
  - Pagetu (数据兔): https://www.pagetu.com/2024/08/30/08/1970/  (本科/一本 rates)
  - Sohu: https://www.sohu.com/a/818682618_120927771
  - Yidianedu: https://www.yidianedu.com/xuexiao/article?id=2579
  - EOL (中国教育在线): https://gaokao.eol.cn/news/202406/t20240607_2614842.shtml
  - GK100: https://www.gk100.com/read_11404026.htm
  - Gaokao Zhitongche: https://app.gaokaozhitongche.com/news/h/VOYqJ6bO

Methodology notes:
  - 报名人数 (exam takers): official provincial announcements. Some provinces report
    total registrations (含高职单招); others report only summer-exam sitters.
    We record the widely-cited figure for each province.
  - 985/211 rates: computed as (admitted to 985/211 universities) / (exam takers).
    Sourced primarily from gotohui.com and cross-referenced with zhihu/163.
  - 一本率 (first-tier rate): proportion scoring above the 特殊类型招生控制线
    (special-type enrollment control line), which replaced the old 一本线.
  - 本科率 (undergraduate rate): proportion scoring above the 本科批次控制线.
  - Where an exact 2024 number was unavailable from web search snippets,
    we used the best available estimate (marked with comments).
    Some 985/211 rate figures use 2023 data when 2024 was not separately confirmed.
  - Fine-grained score-distribution tables (一分一段表) are publicly available
    for ~29 provinces (all except Tibet and Xinjiang) from provincial education
    examination authority websites and aggregator sites like gaokaozhitongche.com,
    eol.cn, and gk100.com.

IMPORTANT: This data is collected from secondary sources (media, data aggregators)
rather than primary government statistical yearbooks. Figures are approximate and
suitable for research illustration, not for official policy analysis. The 985/211
admission rates in particular vary across sources due to differences in denominator
(total registrants vs actual exam sitters) and numerator (regular admission only
vs all pathways including 强基计划, 专项计划, etc.).
"""

from __future__ import annotations
from typing import NamedTuple

YEAR = 2024

class Province(NamedTuple):
    """One province's Gaokao statistics for a single year."""
    name_zh: str          # 省/市/自治区 Chinese name
    name_en: str          # English name
    exam_takers: int      # 报名人数 (approximate, in persons)
    rate_985: float       # 985 university admission rate (0-1 scale)
    rate_211: float       # 211 university admission rate (0-1 scale)
    rate_first_tier: float  # 一本/特控线 admission rate (0-1 scale)
    rate_undergrad: float   # 本科 admission rate (0-1 scale)
    exam_type: str        # "new_ph" (物理/历史), "old_wl" (文理), "new_nosp" (不分科)
    notes: str = ""       # additional context


# ============================================================================
# 2024 data for all 31 provinces / municipalities / autonomous regions
# ============================================================================
# Rates are expressed as fractions (e.g., 0.058 = 5.8%).
#
# exam_type key:
#   "new_ph"   = New Gaokao with Physics/History tracks
#                (Guangdong, Fujian, Hubei, Hunan, Hebei, Chongqing,
#                 Liaoning, Jiangsu, Jilin, Heilongjiang, Jiangxi,
#                 Guangxi, Guizhou, Anhui, Gansu)
#   "old_wl"   = Traditional Liberal-arts / Science tracks
#                (Henan, Sichuan, Yunnan, Shaanxi, Qinghai, Ningxia,
#                 Inner Mongolia, Xinjiang, Tibet, Shanxi)
#   "new_nosp" = New Gaokao without subject grouping (3+3)
#                (Beijing, Tianjin, Shanghai, Zhejiang, Shandong, Hainan)
# ============================================================================

PROVINCES: list[Province] = [
    # ---- Direct-administered municipalities (直辖市) ----
    Province(
        name_zh="北京", name_en="Beijing",
        exam_takers=67_000,
        rate_985=0.053,   # ~5.3%, ~3604 admitted
        rate_211=0.140,   # ~14.0%
        rate_first_tier=0.4017,  # 40.17%
        rate_undergrad=0.63,
        exam_type="new_nosp",
        notes="985 admissions ~3604; 211 rate highest nationally",
    ),
    Province(
        name_zh="天津", name_en="Tianjin",
        exam_takers=70_800,
        rate_985=0.0581,  # ~5.81%, ~4410 admitted (highest nationally)
        rate_211=0.1399,  # ~13.99%
        rate_first_tier=0.3028,  # 30.28%
        rate_undergrad=0.62,
        exam_type="new_nosp",
        notes="985 rate highest nationally; 985 admissions ~4410",
    ),
    Province(
        name_zh="上海", name_en="Shanghai",
        exam_takers=54_000,
        rate_985=0.044,   # ~4.4%, ~2541 admitted
        rate_211=0.1358,  # ~13.58%
        rate_first_tier=0.3475,  # 34.75%
        rate_undergrad=0.7703,   # 77.03% (highest nationally)
        exam_type="new_nosp",
        notes="Highest 本科率 nationally; 985 admissions ~2541",
    ),
    Province(
        name_zh="重庆", name_en="Chongqing",
        exam_takers=203_000,
        rate_985=0.0185,  # ~1.85%
        rate_211=0.060,   # ~6.0%  (est.)
        rate_first_tier=0.3698,  # 36.98% (highest among new_ph provinces)
        rate_undergrad=0.6401,
        exam_type="new_ph",
        notes="Highest 一本率 among history/physics-track provinces",
    ),

    # ---- Northeast (东北) ----
    Province(
        name_zh="辽宁", name_en="Liaoning",
        exam_takers=197_000,
        rate_985=0.0207,  # ~2.07%
        rate_211=0.065,   # ~6.5%  (est.)
        rate_first_tier=0.28,    # ~28%  (est.)
        rate_undergrad=0.7191,   # 71.91% (highest among new_ph provinces)
        exam_type="new_ph",
        notes="Highest 本科率 among history/physics-track provinces",
    ),
    Province(
        name_zh="吉林", name_en="Jilin",
        exam_takers=130_100,
        rate_985=0.0356,  # ~3.56%
        rate_211=0.090,   # ~9.0%  (est.)
        rate_first_tier=0.3113,  # 31.13%
        rate_undergrad=0.7042,   # 70.42%
        exam_type="new_ph",
        notes="2024 first year of new gaokao for Jilin",
    ),
    Province(
        name_zh="黑龙江", name_en="Heilongjiang",
        exam_takers=192_000,
        rate_985=0.0172,  # ~1.72%
        rate_211=0.058,   # ~5.8%  (est.)
        rate_first_tier=0.24,    # ~24%  (est.)
        rate_undergrad=0.55,     # ~55%
        exam_type="new_ph",
        notes="2024 first year of new gaokao for Heilongjiang",
    ),

    # ---- North China (华北) ----
    Province(
        name_zh="河北", name_en="Hebei",
        exam_takers=928_000,
        rate_985=0.0096,  # ~0.96%
        rate_211=0.040,   # ~4.0%  (est.)
        rate_first_tier=0.20,    # ~20%  (est.)
        rate_undergrad=0.38,     # ~38%
        exam_type="new_ph",
    ),
    Province(
        name_zh="山西", name_en="Shanxi",
        exam_takers=353_800,
        rate_985=0.012,   # ~1.2%  (est.)
        rate_211=0.045,   # ~4.5%  (est.)
        rate_first_tier=0.18,    # ~18%  (est.)
        rate_undergrad=0.44,     # ~44%
        exam_type="old_wl",
        notes="Increased 6.17万 over 2023",
    ),
    Province(
        name_zh="内蒙古", name_en="Inner Mongolia",
        exam_takers=218_000,  # 报名21.8万, 实际参考16.3万
        rate_985=0.016,   # ~1.6%  (est.)
        rate_211=0.048,   # ~4.8%  (est.)
        rate_first_tier=0.22,    # ~22%  (est.)
        rate_undergrad=0.46,     # ~46%
        exam_type="old_wl",
        notes="Actual exam sitters ~163,000",
    ),

    # ---- East China (华东) ----
    Province(
        name_zh="山东", name_en="Shandong",
        exam_takers=998_000,
        rate_985=0.0115,  # ~1.15%  (est.)
        rate_211=0.042,   # ~4.2%  (est.)
        rate_first_tier=0.20,    # ~20%  (est.)
        rate_undergrad=0.37,     # ~37%
        exam_type="new_nosp",
    ),
    Province(
        name_zh="江苏", name_en="Jiangsu",
        exam_takers=477_000,
        rate_985=0.017,   # ~1.7%
        rate_211=0.055,   # ~5.5%  (est.)
        rate_first_tier=0.3168,  # 31.68%
        rate_undergrad=0.54,     # ~54%
        exam_type="new_ph",
        notes="Increased 3.5万 over 2023",
    ),
    Province(
        name_zh="浙江", name_en="Zhejiang",
        exam_takers=396_000,
        rate_985=0.015,   # ~1.5%  (est.)
        rate_211=0.050,   # ~5.0%  (est.)
        rate_first_tier=0.1501,  # ~15.01%  (special-type line)
        rate_undergrad=0.45,     # ~45%
        exam_type="new_nosp",
        notes="Zhejiang uses integrated 一段线/二段线 system",
    ),
    Province(
        name_zh="安徽", name_en="Anhui",
        exam_takers=654_000,  # 报名65.4万, 实际参考49.5万
        rate_985=0.011,   # ~1.1%  (est.)
        rate_211=0.040,   # ~4.0%  (est., near bottom nationally)
        rate_first_tier=0.20,    # ~20%  (est.)
        rate_undergrad=0.42,     # ~42%
        exam_type="new_ph",
        notes="2024 first year of new gaokao; actual sitters ~495,000",
    ),
    Province(
        name_zh="福建", name_en="Fujian",
        exam_takers=242_000,
        rate_985=0.017,   # ~1.7%
        rate_211=0.045,   # ~4.5%
        rate_first_tier=0.25,    # ~25%  (est.)
        rate_undergrad=0.55,     # ~55%
        exam_type="new_ph",
    ),
    Province(
        name_zh="江西", name_en="Jiangxi",
        exam_takers=642_100,
        rate_985=0.010,   # ~1.0% (lowest tier nationally)
        rate_211=0.035,   # ~3.5%  (est.)
        rate_first_tier=0.1485,  # 14.85% (lowest among new_ph provinces)
        rate_undergrad=0.34,     # ~34%
        exam_type="new_ph",
        notes="2024 first year of new gaokao; increased 11.43万 over 2023",
    ),

    # ---- Central China (华中) ----
    Province(
        name_zh="河南", name_en="Henan",
        exam_takers=1_360_000,
        rate_985=0.0084,  # ~0.84% (among lowest nationally)
        rate_211=0.040,   # ~4.0%
        rate_first_tier=0.078,   # ~7.8% (some sources; refers to old 一本线)
        rate_undergrad=0.3772,   # 37.72%
        exam_type="old_wl",
        notes="Largest province by exam takers; 一本率 data varies by source (7.8-16%)",
    ),
    Province(
        name_zh="湖北", name_en="Hubei",
        exam_takers=525_000,
        rate_985=0.018,   # ~1.8%
        rate_211=0.046,   # ~4.6%
        rate_first_tier=0.1573,  # 15.73%
        rate_undergrad=0.36,     # ~36%
        exam_type="new_ph",
    ),
    Province(
        name_zh="湖南", name_en="Hunan",
        exam_takers=727_000,
        rate_985=0.014,   # ~1.4%  (est.)
        rate_211=0.040,   # ~4.0%  (est.)
        rate_first_tier=0.18,    # ~18%  (est.)
        rate_undergrad=0.38,     # ~38%
        exam_type="new_ph",
        notes="Increased 4.3万 over 2023",
    ),

    # ---- South China (华南) ----
    Province(
        name_zh="广东", name_en="Guangdong",
        exam_takers=768_000,
        rate_985=0.0098,  # ~0.98%
        rate_211=0.0274,  # ~2.74% (lowest 211 rate nationally)
        rate_first_tier=0.1504,  # 15.04%
        rate_undergrad=0.37,     # ~37%
        exam_type="new_ph",
        notes="Lowest 211 rate nationally",
    ),
    Province(
        name_zh="广西", name_en="Guangxi",
        exam_takers=467_000,  # Some sources: 69.7万 (incl. vocational)
        rate_985=0.010,   # ~1.0%  (est.)
        rate_211=0.035,   # ~3.5%  (est.)
        rate_first_tier=0.1736,  # 17.36%
        rate_undergrad=0.44,     # ~44%
        exam_type="new_ph",
        notes="2024 first year of new gaokao; registration may include vocational track (~69.7万 total)",
    ),
    Province(
        name_zh="海南", name_en="Hainan",
        exam_takers=74_096,
        rate_985=0.020,   # ~2.0%  (est.)
        rate_211=0.065,   # ~6.5%  (est.)
        rate_first_tier=0.25,    # ~25%  (est.)
        rate_undergrad=0.50,     # ~50%
        exam_type="new_nosp",
    ),

    # ---- Southwest (西南) ----
    Province(
        name_zh="四川", name_en="Sichuan",
        exam_takers=835_200,
        rate_985=0.012,   # ~1.2%  (est.)
        rate_211=0.042,   # ~4.2%  (est.)
        rate_first_tier=0.17,    # ~17%  (est.)
        rate_undergrad=0.42,     # ~42%
        exam_type="old_wl",
    ),
    Province(
        name_zh="贵州", name_en="Guizhou",
        exam_takers=472_500,
        rate_985=0.0098,  # ~0.98%  (est.)
        rate_211=0.042,   # ~4.2%  (est.)
        rate_first_tier=0.20,    # ~20%  (est.)
        rate_undergrad=0.52,     # ~52%
        exam_type="new_ph",
        notes="2024 first year of new gaokao",
    ),
    Province(
        name_zh="云南", name_en="Yunnan",
        exam_takers=395_000,
        rate_985=0.010,   # ~1.0%  (est.)
        rate_211=0.038,   # ~3.8%  (est.)
        rate_first_tier=0.1569,  # 15.69% (lowest among old_wl provinces)
        rate_undergrad=0.3798,   # 37.98%
        exam_type="old_wl",
        notes="Lowest 本科率 among old exam provinces",
    ),
    Province(
        name_zh="西藏", name_en="Tibet",
        exam_takers=36_000,
        rate_985=0.025,   # ~2.5%  (est., benefiting from small cohort + policy)
        rate_211=0.100,   # ~10%  (est., relatively high due to small base)
        rate_first_tier=0.25,    # ~25%  (est.)
        rate_undergrad=0.45,     # ~45%  (est.)
        exam_type="old_wl",
        notes="Very small cohort; 一分一段表 not publicly released for 2024",
    ),

    # ---- Northwest (西北) ----
    Province(
        name_zh="陕西", name_en="Shaanxi",
        exam_takers=270_000,
        rate_985=0.018,   # ~1.8%  (est.)
        rate_211=0.055,   # ~5.5%  (est.)
        rate_first_tier=0.28,    # ~28%
        rate_undergrad=0.6655,   # 66.55% (highest among old_wl provinces)
        exam_type="old_wl",
        notes="Highest 本科率 among traditional exam provinces",
    ),
    Province(
        name_zh="甘肃", name_en="Gansu",
        exam_takers=226_439,  # 报名22.6万, 实际参考17.68万
        rate_985=0.011,   # ~1.1%  (est., near bottom)
        rate_211=0.038,   # ~3.8%  (est., near bottom)
        rate_first_tier=0.22,    # ~22%  (est.)
        rate_undergrad=0.47,     # ~47%
        exam_type="new_ph",
        notes="2024 first year of new gaokao; actual sitters ~176,800",
    ),
    Province(
        name_zh="青海", name_en="Qinghai",
        exam_takers=65_600,
        rate_985=0.0336,  # ~3.36%
        rate_211=0.085,   # ~8.5%  (est.)
        rate_first_tier=0.4269,  # 42.69% (highest nationally among old_wl)
        rate_undergrad=0.5192,   # 51.92%
        exam_type="old_wl",
        notes="Highest 一本率 nationally (old exam regions)",
    ),
    Province(
        name_zh="宁夏", name_en="Ningxia",
        exam_takers=73_000,
        rate_985=0.0231,  # ~2.31%
        rate_211=0.075,   # ~7.5%  (est.)
        rate_first_tier=0.25,    # ~25%  (est.)
        rate_undergrad=0.44,     # ~44%
        exam_type="old_wl",
    ),
    Province(
        name_zh="新疆", name_en="Xinjiang",
        exam_takers=232_600,
        rate_985=0.013,   # ~1.3%  (est.)
        rate_211=0.045,   # ~4.5%  (est.)
        rate_first_tier=0.20,    # ~20%  (est.)
        rate_undergrad=0.44,     # ~44%
        exam_type="old_wl",
        notes="一分一段表 not publicly released for 2024",
    ),
]

# ---------------------------------------------------------------------------
# Convenience lookups
# ---------------------------------------------------------------------------

PROVINCE_BY_NAME: dict[str, Province] = {}
for _p in PROVINCES:
    PROVINCE_BY_NAME[_p.name_zh] = _p
    PROVINCE_BY_NAME[_p.name_en] = _p


def total_exam_takers() -> int:
    """Sum of all provincial exam taker counts."""
    return sum(p.exam_takers for p in PROVINCES)


def national_avg_985() -> float:
    """Weighted-average 985 rate across all provinces."""
    num = sum(p.exam_takers * p.rate_985 for p in PROVINCES)
    den = sum(p.exam_takers for p in PROVINCES)
    return num / den


def national_avg_211() -> float:
    """Weighted-average 211 rate across all provinces."""
    num = sum(p.exam_takers * p.rate_211 for p in PROVINCES)
    den = sum(p.exam_takers for p in PROVINCES)
    return num / den


# ---------------------------------------------------------------------------
# Score distribution (一分一段表) availability
# ---------------------------------------------------------------------------

SCORE_TABLE_AVAILABILITY = """
Fine-grained score distribution tables (一分一段表) for 2024 are publicly
available for approximately 29 of 31 provinces. Tibet (西藏) and Xinjiang
(新疆) did not publish their 2024 tables.

Download sources:
  - 高考直通车: https://app.gaokaozhitongche.com/news/h/p2NMVDyw
  - 中国教育在线: https://www.eol.cn/e_html/gk/gkfsd/2024.shtml
  - 高考100: https://m.gk100.com/read_6304352.htm
  - 大学生必备网: https://www.dxsbb.com/news/137109.html
  - Individual provincial education examination authority (教育考试院) websites

Each table maps raw scores to cumulative rank (位次), enabling precise
percentile calculations. In new-gaokao provinces, separate tables exist
for Physics-track and History-track (or equivalent subject groups).
"""


if __name__ == "__main__":
    # Quick sanity check
    print(f"Year: {YEAR}")
    print(f"Provinces: {len(PROVINCES)}")
    print(f"Total exam takers: {total_exam_takers():,}")
    print(f"National avg 985 rate: {national_avg_985():.2%}")
    print(f"National avg 211 rate: {national_avg_211():.2%}")
    print()
    header = f"{'Province':<16} {'中文':<5} {'Takers':>10} {'985%':>7} {'211%':>7} {'一本%':>7} {'本科%':>7}"
    print(header)
    print("-" * len(header))
    for p in sorted(PROVINCES, key=lambda x: x.rate_985, reverse=True):
        print(
            f"{p.name_en:<16} {p.name_zh:<5} "
            f"{p.exam_takers:>10,} "
            f"{p.rate_985:>6.2%} "
            f"{p.rate_211:>6.2%} "
            f"{p.rate_first_tier:>6.2%} "
            f"{p.rate_undergrad:>6.2%}"
        )
