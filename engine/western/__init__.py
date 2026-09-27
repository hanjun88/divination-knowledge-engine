"""西洋占星（Western Astrology）规则层 + 历算层。

提供：
  - 行星尊贵体系（Essential Dignities：庙/旺/落/陷）
  - 相位容许度（Aspect Orbs）
  - 后天十二宫位含义（House Meanings）
  - 历算接口（pyswisseph）：行星黄经 / 四轴 / 分宫 / 完整星盘
"""
from .dignity import (
    DIGNITY_TABLE,
    ASPECT_ORBS,
    HOUSE_MEANINGS,
    ZODIAC_SIGNS,
    PLANETS,
    get_dignity,
    check_aspect,
    get_house_meaning,
)
from .ephemeris import (
    PLANET_FLAGS,
    compute_aspects,
    compute_natal_chart,
    get_angles,
    get_houses,
    get_planet_longitude,
    split_longitude,
)

__all__ = [
    "DIGNITY_TABLE",
    "ASPECT_ORBS",
    "HOUSE_MEANINGS",
    "ZODIAC_SIGNS",
    "PLANETS",
    "get_dignity",
    "check_aspect",
    "get_house_meaning",
    "PLANET_FLAGS",
    "split_longitude",
    "get_planet_longitude",
    "get_angles",
    "get_houses",
    "compute_aspects",
    "compute_natal_chart",
]
