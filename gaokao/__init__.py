"""Gaokao Reform: equal-weight random-band admission model.

Core question: 如果每个城市同等重要, 高考录取会怎样?

Implements the mathematics from Appendix H:
  - Current system disparity measurement (Gini, max/min ratio)
  - Equal-weight reform model: w_i = 100 for all cities
  - Within-band randomization: fine-grained score bands -> random selection
  - Provincial slot allocation with rank-based distribution

Stdlib only -- no external dependencies.
"""

from gaokao.data import Province, PROVINCES, YEAR
from gaokao.model import ReformModel, BandConfig

__all__ = ["Province", "PROVINCES", "YEAR", "ReformModel", "BandConfig"]
