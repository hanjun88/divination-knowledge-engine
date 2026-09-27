# -*- coding: utf-8 -*-
"""西洋占星规则层：行星尊贵表 / 相位容许度 / 宫位含义。

数据来源：传统西洋占星 Essential Dignities 体系（Rulership / Exaltation /
Detriment / Fall），托勒密《四书》传承并加入现代三王星（天王/海王/冥王）的
现代守护分配。

本模块同时承担两件事：
  1. 运行时查表函数（get_dignity / check_aspect / get_house_meaning）；
  2. 供规则引擎消费的结构化常量表（DIGNITY_TABLE / ASPECT_ORBS / HOUSE_MEANINGS），
     由 scripts 生成 engine/rules/rules_western.json。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# 常量：12 星座 / 10 行星
# ---------------------------------------------------------------------------

ZODIAC_SIGNS: List[str] = [
    "白羊座", "金牛座", "双子座", "巨蟹座", "狮子座", "处女座",
    "天秤座", "天蝎座", "射手座", "摩羯座", "水瓶座", "双鱼座",
]

# ---------------------------------------------------------------------------
# 1. 行星尊贵表（Essential Dignities）
# ---------------------------------------------------------------------------
# ruler       庙（Rulership / 入庙）：行星在该星座能量最强，score = +5
# exaltation  旺（Exaltation / 旺相）：行星在该星座被提升，score = +4
# detriment   落（Detriment / 失势）：庙位对宫，能量弱，score = -4
# fall        陷（Fall / 落陷）：旺位对宫，能量最弱，score = -5

DIGNITY_TABLE: Dict[str, Dict[str, List[str]]] = {
    "太阳": {
        "ruler": ["狮子座"],
        "exaltation": ["白羊座"],
        "detriment": ["水瓶座"],
        "fall": ["天秤座"],
    },
    "月亮": {
        "ruler": ["巨蟹座"],
        "exaltation": ["金牛座"],
        "detriment": ["摩羯座"],
        "fall": ["天蝎座"],
    },
    "水星": {
        "ruler": ["双子座", "处女座"],
        "exaltation": ["处女座"],
        "detriment": ["射手座", "双鱼座"],
        "fall": ["双鱼座"],
    },
    "金星": {
        "ruler": ["金牛座", "天秤座"],
        "exaltation": ["双鱼座"],
        "detriment": ["天蝎座", "白羊座"],
        "fall": ["处女座"],
    },
    "火星": {
        "ruler": ["白羊座", "天蝎座"],
        "exaltation": ["摩羯座"],
        "detriment": ["天秤座", "金牛座"],
        "fall": ["巨蟹座"],
    },
    "木星": {
        "ruler": ["射手座", "双鱼座"],
        "exaltation": ["巨蟹座"],
        "detriment": ["双子座", "处女座"],
        "fall": ["摩羯座"],
    },
    "土星": {
        "ruler": ["摩羯座", "水瓶座"],
        "exaltation": ["天秤座"],
        "detriment": ["巨蟹座", "狮子座"],
        "fall": ["白羊座"],
    },
    # 现代三王星
    "天王星": {
        "ruler": ["水瓶座"],
        "exaltation": ["天蝎座"],
        "detriment": ["狮子座"],
        "fall": ["金牛座"],
    },
    "海王星": {
        "ruler": ["双鱼座"],
        "exaltation": ["狮子座", "巨蟹座"],
        "detriment": ["处女座"],
        "fall": ["水瓶座"],
    },
    "冥王星": {
        "ruler": ["天蝎座"],
        "exaltation": ["白羊座"],
        "detriment": ["金牛座"],
        "fall": ["天秤座"],
    },
}

PLANETS: List[str] = list(DIGNITY_TABLE.keys())

# dignity level -> (数值权重, 中文描述)
_DIGNITY_META: Dict[str, Dict[str, Any]] = {
    "ruler": {"score": 5, "label": "入庙（庙）", "en": "Rulership"},
    "exaltation": {"score": 4, "label": "旺相（旺）", "en": "Exaltation"},
    "detriment": {"score": -4, "label": "失势（落）", "en": "Detriment"},
    "fall": {"score": -5, "label": "落陷（陷）", "en": "Fall"},
    "none": {"score": 0, "label": "中性（游走）", "en": "Peregrine"},
}

# 优先级：阳性尊贵取最强（ruler > exaltation），阴性取最弱（fall < detriment）。
# 同一星座理论上不会同时命中正负两类（落/陷分别是庙/旺的对宫），
# 但水星在处女座同时是 ruler 与 exaltation，此时按 ruler 优先。
_DIGNITY_PRECEDENCE: List[str] = ["ruler", "exaltation", "detriment", "fall"]


# ---------------------------------------------------------------------------
# 2. 相位容许度表（Aspect Orbs）
# ---------------------------------------------------------------------------

ASPECT_ORBS: Dict[str, Dict[str, Any]] = {
    "合相": {"angle": 0, "orb": 8},
    "六分相": {"angle": 60, "orb": 4},
    "四分相": {"angle": 90, "orb": 6},
    "三分相": {"angle": 120, "orb": 6},
    "梅花相": {"angle": 150, "orb": 2},
    "对分相": {"angle": 180, "orb": 8},
    # 次要相位
    "半六分": {"angle": 30, "orb": 1.5},
    "八分体": {"angle": 45, "orb": 2},
    "补八分": {"angle": 135, "orb": 2},
}


# ---------------------------------------------------------------------------
# 3. 后天十二宫位含义
# ---------------------------------------------------------------------------

HOUSE_MEANINGS: Dict[int, Dict[str, str]] = {
    1: {"name": "命宫", "area": "自我、外貌、性格、人生态度"},
    2: {"name": "财帛宫", "area": "金钱、物质、价值观、自我价值"},
    3: {"name": "兄弟宫", "area": "沟通、学习、兄弟姐妹、短途旅行"},
    4: {"name": "田宅宫", "area": "家庭、根基、房产、内心、父母"},
    5: {"name": "子女宫", "area": "恋爱、创造、娱乐、子女、自我表达"},
    6: {"name": "奴仆宫", "area": "工作、健康、日常、服务、宠物"},
    7: {"name": "夫妻宫", "area": "婚姻、伴侣、合作、公开敌人"},
    8: {"name": "疾厄宫", "area": "死亡、重生、性、他人资源、深度转化"},
    9: {"name": "迁移宫", "area": "高等教育、哲学、远行、信仰、法律"},
    10: {"name": "官禄宫", "area": "事业、社会地位、名誉、权威、父母"},
    11: {"name": "福德宫", "area": "朋友、团体、希望、理想、社交"},
    12: {"name": "玄秘宫", "area": "潜意识、隐秘、灵性、自我毁灭、隔离"},
}


# ---------------------------------------------------------------------------
# 查表函数
# ---------------------------------------------------------------------------

def get_dignity(planet: str, sign: str) -> Dict[str, Any]:
    """返回行星在某星座的尊贵状态。

    Returns:
        {"level": "ruler|exaltation|detriment|fall|none",
         "score": 5|4|-4|-5|0,
         "detail": str}
    """
    info = DIGNITY_TABLE.get(planet)
    if info is None:
        return {"level": "none", "score": 0,
                "detail": f"未知行星「{planet}」，无尊贵数据"}

    for level in _DIGNITY_PRECEDENCE:
        if sign in info.get(level, []):
            meta = _DIGNITY_META[level]
            detail = (f"{planet}在{sign}{meta['label']}"
                      f"（{meta['en']}），score={meta['score']:+d}")
            return {"level": level, "score": meta["score"], "detail": detail}

    meta = _DIGNITY_META["none"]
    return {
        "level": "none",
        "score": 0,
        "detail": f"{planet}在{sign}无尊贵位（{meta['en']}），能量中性",
    }


def _angular_separation(angle1: float, angle2: float) -> float:
    """两个黄经之间的最短角距，落在 [0, 180]。"""
    diff = abs(angle1 - angle2) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff
    return diff


def check_aspect(angle1: float, angle2: float, aspect: str = "") -> Dict[str, Any]:
    """检查两个黄经是否形成相位。

    Args:
        angle1: 行星1黄经（度，0~360）。
        angle2: 行星2黄经（度，0~360）。
        aspect: 指定相位名（如 "四分相"）。为空则返回实际角距最接近且在
                容许度内的相位；若无一在容许度内则 matched=False。

    Returns:
        {"aspect": str, "angle": float, "orb": float,
         "actual_angle": float, "delta": float, "matched": bool}
    """
    sep = _angular_separation(angle1, angle2)

    candidates: List[Dict[str, Any]] = []
    for name, cfg in ASPECT_ORBS.items():
        canonical = float(cfg["angle"])
        orb = float(cfg["orb"])
        delta = abs(sep - canonical)
        candidates.append({
            "aspect": name,
            "angle": canonical,
            "orb": orb,
            "actual_angle": round(sep, 4),
            "delta": round(delta, 4),
            "matched": delta <= orb,
        })

    if aspect:
        for c in candidates:
            if c["aspect"] == aspect:
                return c
        # 指定相位名不存在
        return {
            "aspect": aspect,
            "angle": None,
            "orb": None,
            "actual_angle": round(sep, 4),
            "delta": None,
            "matched": False,
        }

    matched = [c for c in candidates if c["matched"]]
    if not matched:
        return {
            "aspect": "",
            "angle": None,
            "orb": None,
            "actual_angle": round(sep, 4),
            "delta": None,
            "matched": False,
        }
    # 取角距差最小者
    return min(matched, key=lambda c: c["delta"])


def get_house_meaning(house_num: int) -> Dict[str, str]:
    """返回后天宫位含义。house_num ∈ [1, 12]。"""
    if house_num not in HOUSE_MEANINGS:
        raise ValueError(f"宫位编号须为 1~12，收到 {house_num}")
    info = HOUSE_MEANINGS[house_num]
    return {"house": str(house_num), "name": info["name"], "area": info["area"]}
