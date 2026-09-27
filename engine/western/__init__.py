"""西洋占星（Western Astrology）规则层。

提供：
  - 行星尊贵体系（Essential Dignities：庙/旺/落/陷）
  - 相位容许度（Aspect Orbs）
  - 后天十二宫位含义（House Meanings）
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

__all__ = [
    "DIGNITY_TABLE",
    "ASPECT_ORBS",
    "HOUSE_MEANINGS",
    "ZODIAC_SIGNS",
    "PLANETS",
    "get_dignity",
    "check_aspect",
    "get_house_meaning",
]
