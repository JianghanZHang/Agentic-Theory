"""Gaokao reform model: equal-weight random-band admission.

Implements the reform proposal from Appendix H:

Current system:
  - Each province gets fixed 招生计划 (admission quotas) from each university.
  - Quotas are NOT proportional to population → structural disparity.
  - Same-score students in different provinces have vastly different outcomes.

Reform model:
  1. Fair exam: no cheating, national standardization.
  2. Equal city weights: w_i = 100 for every city/province.
     Meaning: every province is equally important.
  3. Within-band randomization: in each fine-grained score band [s, s+Δ],
     students are selected at random (not by exact rank).
     This removes the "one point = one fate" problem.
  4. Provincial slot allocation: each province gets slots proportional
     to its population share × university capacity.
  5. Students rank within their province's distribution.

Mathematical formulation:
  - Let N_i = exam takers in province i, R_i = 985 admission rate.
  - Current: slots_i ~ fixed quotas (strongly favors small provinces).
  - Reform: slots_i = w_i × C / Σ w_j, with w_i = const → slots_i = C / n.
  - Disparity index: D = max(R_i) / min(R_i).
  - Gini coefficient of R across provinces.

Stdlib only -- no external dependencies.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Sequence

from gaokao.data import Province, PROVINCES


@dataclass
class BandConfig:
    """Configuration for score-band randomization.

    band_width: width of each score band (e.g., 5 points).
        Within each band, students are shuffled randomly.
    """
    band_width: int = 5  # points


@dataclass
class SlotAllocation:
    """Result of slot allocation for one province under reform."""
    province: Province
    current_985_slots: int
    reform_985_slots: int
    current_rate: float
    reform_rate: float
    delta_rate: float       # reform - current (positive = province gains)
    delta_slots: int


class ReformModel:
    """Equal-weight random-band admission model.

    Core idea: if every province has equal weight w_i = w,
    then the total 985 capacity C is split equally:
        slots_i = C / n  (n = number of provinces)

    The reform rate for province i is then:
        R_i^reform = slots_i / N_i = C / (n × N_i)

    This naturally gives HIGHER rates to SMALLER provinces
    (which is the current system's effect too, but the reform
    makes it principled rather than arbitrary).

    The key difference: the RATIO max/min is bounded by
    population ratio alone, not by political allocation.
    """

    def __init__(
        self,
        provinces: Sequence[Province] | None = None,
        total_985_capacity: int | None = None,
    ) -> None:
        self.provinces = list(provinces or PROVINCES)
        self.n = len(self.provinces)

        # Total 985 slots nationally: sum of current allocations
        if total_985_capacity is not None:
            self.C = total_985_capacity
        else:
            self.C = sum(
                round(p.exam_takers * p.rate_985) for p in self.provinces
            )

    # ── Current system metrics ──

    def current_slots(self, p: Province) -> int:
        """Estimated current 985 slots for province p."""
        return round(p.exam_takers * p.rate_985)

    def current_rates(self) -> list[float]:
        """Current 985 admission rates."""
        return [p.rate_985 for p in self.provinces]

    def disparity_ratio(self, rates: list[float] | None = None) -> float:
        """max(R) / min(R) — the disparity index."""
        rates = rates or self.current_rates()
        return max(rates) / min(rates) if min(rates) > 0 else float("inf")

    def gini(self, rates: list[float] | None = None) -> float:
        """Gini coefficient of admission rates across provinces.

        Gini = 0 means perfect equality (all provinces same rate).
        Gini = 1 means maximum inequality.
        """
        rates = rates or self.current_rates()
        n = len(rates)
        if n == 0:
            return 0.0
        sorted_r = sorted(rates)
        mean_r = sum(sorted_r) / n
        if mean_r == 0:
            return 0.0
        # Standard Gini formula
        numerator = sum(
            abs(sorted_r[i] - sorted_r[j])
            for i in range(n) for j in range(n)
        )
        return numerator / (2 * n * n * mean_r)

    def coefficient_of_variation(self, rates: list[float] | None = None) -> float:
        """CV = std(R) / mean(R)."""
        rates = rates or self.current_rates()
        n = len(rates)
        mean_r = sum(rates) / n
        if mean_r == 0:
            return 0.0
        var = sum((r - mean_r) ** 2 for r in rates) / n
        return math.sqrt(var) / mean_r

    # ── Reform model ──

    def equal_weight_slots(self) -> list[int]:
        """Equal-weight allocation: C / n slots per province."""
        base = self.C // self.n
        remainder = self.C - base * self.n
        # Distribute remainder to provinces with most exam takers
        slots = [base] * self.n
        sorted_idx = sorted(
            range(self.n),
            key=lambda i: self.provinces[i].exam_takers,
            reverse=True,
        )
        for i in range(remainder):
            slots[sorted_idx[i]] += 1
        return slots

    def population_proportional_slots(self) -> list[int]:
        """Population-proportional allocation: slots_i = C × N_i / Σ N_j."""
        total_N = sum(p.exam_takers for p in self.provinces)
        raw = [self.C * p.exam_takers / total_N for p in self.provinces]
        # Round while preserving total
        slots = [int(r) for r in raw]
        remainder = self.C - sum(slots)
        fracs = [(raw[i] - slots[i], i) for i in range(self.n)]
        fracs.sort(reverse=True)
        for j in range(remainder):
            slots[fracs[j][1]] += 1
        return slots

    def reform_rates(self, method: str = "equal") -> list[float]:
        """Admission rates under reform.

        method: "equal" (equal weight) or "proportional" (population-proportional).
        """
        if method == "equal":
            slots = self.equal_weight_slots()
        elif method == "proportional":
            slots = self.population_proportional_slots()
        else:
            raise ValueError(f"Unknown method: {method}")
        return [
            s / p.exam_takers if p.exam_takers > 0 else 0.0
            for s, p in zip(slots, self.provinces)
        ]

    def compute_allocation(self, method: str = "equal") -> list[SlotAllocation]:
        """Full allocation comparison: current vs reform."""
        reform_slots = (
            self.equal_weight_slots()
            if method == "equal"
            else self.population_proportional_slots()
        )
        results = []
        for i, p in enumerate(self.provinces):
            cur_slots = self.current_slots(p)
            ref_slots = reform_slots[i]
            cur_rate = p.rate_985
            ref_rate = ref_slots / p.exam_takers if p.exam_takers > 0 else 0.0
            results.append(SlotAllocation(
                province=p,
                current_985_slots=cur_slots,
                reform_985_slots=ref_slots,
                current_rate=cur_rate,
                reform_rate=ref_rate,
                delta_rate=ref_rate - cur_rate,
                delta_slots=ref_slots - cur_slots,
            ))
        return results

    # ── Band randomization ──

    @staticmethod
    def band_shuffle(
        scores: list[int],
        band_width: int = 5,
        seed: int | None = None,
    ) -> list[int]:
        """Shuffle students within each score band.

        Given a list of scores, groups them into bands of width `band_width`
        and randomly permutes within each band. Returns new ordering indices.

        This models the "within-band randomization" that removes
        the one-point-one-fate problem.
        """
        if seed is not None:
            random.seed(seed)

        n = len(scores)
        indexed = list(range(n))

        # Group by band
        def band_key(i: int) -> int:
            return scores[i] // band_width

        bands: dict[int, list[int]] = {}
        for i in indexed:
            bk = band_key(i)
            bands.setdefault(bk, []).append(i)

        # Shuffle within each band
        result: list[int] = []
        for bk in sorted(bands.keys(), reverse=True):
            group = bands[bk]
            random.shuffle(group)
            result.extend(group)

        return result

    # ── Summary statistics ──

    def summary(self, method: str = "equal") -> dict:
        """Compute summary statistics for current vs reform."""
        cur = self.current_rates()
        ref = self.reform_rates(method)

        return {
            "method": method,
            "n_provinces": self.n,
            "total_985_capacity": self.C,
            "current": {
                "disparity_ratio": self.disparity_ratio(cur),
                "gini": self.gini(cur),
                "cv": self.coefficient_of_variation(cur),
                "max_rate": max(cur),
                "min_rate": min(cur),
                "max_province": self.provinces[cur.index(max(cur))].name_zh,
                "min_province": self.provinces[cur.index(min(cur))].name_zh,
            },
            "reform": {
                "disparity_ratio": self.disparity_ratio(ref),
                "gini": self.gini(ref),
                "cv": self.coefficient_of_variation(ref),
                "max_rate": max(ref),
                "min_rate": min(ref),
                "max_province": self.provinces[ref.index(max(ref))].name_zh,
                "min_province": self.provinces[ref.index(min(ref))].name_zh,
            },
        }
