"""
六爻纳甲排盘内核 (liuyao-najia-core)

模块划分:
  hexagram.py  — 成卦算法 + 八宫世应定位
  najia.py     — 纳甲纳支 + 六亲装配 + 六神安起
  wangshuai.py — 月建日辰旺衰 + 旬空月破 + 伏神查找
  dongbian.py  — 动变力学 + 应期法则 + AST输出
  cast.py      — 端到端口径集成
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Yao:
    """单爻状态"""
    pos: int
    value: int
    is_yang: bool
    is_dong: bool
    gan: str = ""
    zhi: str = ""
    wx: str = ""
    liuqin: str = ""
    liushen: str = ""
    bian_zhi: str = ""
    bian_wx: str = ""
    bian_liuqin: str = ""
    wangshuai_score: float = 0.0
    wangshuai_label: str = "平"
    xun_kong: bool = False
    yue_po: bool = False
    ri_chong: bool = False
    ri_sheng: bool = False
    yue_sheng: bool = False
    yue_ke: bool = False
    ru_mu: bool = False
    dongbian_type: str = ""
    dongbian_score: float = 0.0


@dataclass
class HexagramInfo:
    ben_gua_name: str
    ben_gua_id: int
    bian_gua_name: str
    bian_gua_id: int
    palace: str
    palace_wx: str
    shi_pos: int
    ying_pos: int
    shi_type: str


@dataclass
class Fushen:
    pos: int
    zhi: str
    wx: str
    liuqin: str
    fei_pos: int
    fei_zhi: str
    fei_ke_fu: bool = False
    fei_sheng_fu: bool = False


@dataclass
class CastResult:
    input_values: List[int]
    datetime: str
    month_gan: str = ""
    month_zhi: str = ""
    day_gan: str = ""
    day_zhi: str = ""
    day_xun: str = ""
    hexagram: Optional[HexagramInfo] = None
    yaos: List[Yao] = field(default_factory=list)
    fushen: Optional[Fushen] = None
    yong_shen_pos: int = 0
    ying_qi: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
