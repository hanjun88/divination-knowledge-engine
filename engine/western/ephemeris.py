# -*- coding: utf-8 -*-
"""西洋占星历算层（Ephemeris）：基于 pyswisseph(Swiss Ephemeris)。

提供热带黄道(Tropical Zodiac)下的：
  1. 10 大行星黄经计算 get_planet_longitude
  2. 四轴(ASC/MC/DSC/IC)        get_angles
  3. 12 宫宫头(Placidus 等)      get_houses
  4. 行星间主要相位             compute_aspects
  5. 端到端出生星盘             compute_natal_chart

时间约定：所有 hour 参数均为 **UT 世界时**（小时，可带小数）。
地理经纬度：东经为正、西经为负；北纬为正、南纬为负。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import swisseph as swe

from .dignity import (
    ASPECT_ORBS,
    HOUSE_MEANINGS,
    ZODIAC_SIGNS,
    get_dignity,
    get_house_meaning,
)

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

# 10 大行星 -> Swiss Ephemeris 常量（热带黄道，FLG_SIDEREAL 不开启即回归黄道）
PLANET_FLAGS: Dict[str, int] = {
    "太阳": swe.SUN,
    "月亮": swe.MOON,
    "水星": swe.MERCURY,
    "金星": swe.VENUS,
    "火星": swe.MARS,
    "木星": swe.JUPITER,
    "土星": swe.SATURN,
    "天王星": swe.URANUS,
    "海王星": swe.NEPTUNE,
    "冥王星": swe.PLUTO,
}

# 分宫制 -> swe.houses() 的 hsys 字符
HOUSE_SYSTEMS: Dict[str, bytes] = {
    "Placidus": b"P",
    "Equal": b"E",
    "Whole Sign": b"W",
    "Koch": b"K",
    "Regiomontanus": b"R",
    "Campanus": b"C",
}

# 主要相位（合/六分/四分/三分/对分）
MAJOR_ASPECTS: List[str] = ["合相", "六分相", "四分相", "三分相", "对分相"]

# 使用内置 Moshier 星历表，无需外部 ephemeris 文件，离线可用。
# 对本模块精度需求（行星落座/宫位/相位）足够。
# FLG_SPEED 必须显式开启，否则 xx[3..5] 速度分量恒为 0。
_SWE_FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _julday(year: int, month: int, day: int, hour: float) -> float:
    """UT 时刻 -> 儒略日。"""
    return swe.julday(year, month, day, hour)


def _normalize_deg(deg: float) -> float:
    """把角度归一到 [0, 360)。"""
    return deg % 360.0


def split_longitude(longitude: float) -> Tuple[str, float, int]:
    """把黄经拆成 (星座名, 星座内度数 0~30, 星座序号 0~11)。"""
    lon = _normalize_deg(longitude)
    sign_idx = int(lon // 30.0)
    degree_in_sign = round(lon - sign_idx * 30.0, 6)
    return ZODIAC_SIGNS[sign_idx], degree_in_sign, sign_idx


def _planet_calc(flag: int, jd: float) -> Tuple[float, float]:
    """调用 swe.calc_ut，返回 (黄经 0~360, 黄经速度 度/日)。"""
    xx, _ret = swe.calc_ut(jd, flag, _SWE_FLAGS)
    return _normalize_deg(xx[0]), xx[3]


# ---------------------------------------------------------------------------
# 1. 行星黄经
# ---------------------------------------------------------------------------

def get_planet_longitude(planet_name: str, year: int, month: int, day: int,
                         hour: float = 12.0, longitude: float = 0.0) -> Dict[str, Any]:
    """计算行星在指定 UT 时刻的热带黄经。

    Args:
        planet_name: 中文行星名（PLANET_FLAGS 的键）。
        year/month/day/hour: UT 日期时刻。
        longitude:   地理经度（地理心行星黄经与观测点无关，保留参数仅为接口对称）。

    Returns:
        {"planet", "longitude", "sign", "degree_in_sign", "retrograde", "dignity"}
    """
    if planet_name not in PLANET_FLAGS:
        raise ValueError(f"未知行星「{planet_name}」，可选：{list(PLANET_FLAGS)}")

    jd = _julday(year, month, day, hour)
    lon, speed = _planet_calc(PLANET_FLAGS[planet_name], jd)
    sign, deg_in_sign, _ = split_longitude(lon)

    return {
        "planet": planet_name,
        "longitude": round(lon, 6),
        "sign": sign,
        "degree_in_sign": round(deg_in_sign, 6),
        "retrograde": bool(speed < 0.0),
        "speed": round(speed, 6),
        "dignity": get_dignity(planet_name, sign),
    }


# ---------------------------------------------------------------------------
# 2. 四轴
# ---------------------------------------------------------------------------

def _houses_raw(jd: float, lat: float, lon: float,
                house_system: str = "Placidus") -> Tuple[List[float], List[float]]:
    """调用 swe.houses，返回 (cusps[12] 索引0..11 对应宫1..12, ascmc[4])。"""
    hsys = HOUSE_SYSTEMS.get(house_system, b"P")
    cusps, ascmc = swe.houses(jd, lat, lon, hsys)
    # swe 返回 cusps 长度 12（索引0..11 对应宫1..12）
    cusp_list = [_normalize_deg(cusps[i]) for i in range(12)]
    return cusp_list, list(ascmc)


def _angle_block(longitude: float) -> Dict[str, Any]:
    sign, deg_in_sign, _ = split_longitude(longitude)
    return {"longitude": round(_normalize_deg(longitude), 6),
            "sign": sign, "degree_in_sign": round(deg_in_sign, 6)}


def get_angles(year: int, month: int, day: int, hour: float,
               latitude: float, longitude: float) -> Dict[str, Any]:
    """计算 ASC / MC / DSC / IC（Placidus）。

    DSC = ASC + 180；IC = MC + 180。
    """
    jd = _julday(year, month, day, hour)
    _cusps, ascmc = _houses_raw(jd, latitude, longitude, "Placidus")
    asc = _normalize_deg(ascmc[0])
    mc = _normalize_deg(ascmc[1])
    return {
        "asc": _angle_block(asc),
        "mc": _angle_block(mc),
        "dsc": _angle_block(asc + 180.0),
        "ic": _angle_block(mc + 180.0),
    }


# ---------------------------------------------------------------------------
# 3. 分宫
# ---------------------------------------------------------------------------

def get_houses(year: int, month: int, day: int, hour: float,
               latitude: float, longitude: float,
               house_system: str = "Placidus") -> List[Dict[str, Any]]:
    """计算 12 宫宫头位置。"""
    jd = _julday(year, month, day, hour)
    cusps, _ascmc = _houses_raw(jd, latitude, longitude, house_system)

    result: List[Dict[str, Any]] = []
    for i, cusp_lon in enumerate(cusps, start=1):
        sign, deg_in_sign, _ = split_longitude(cusp_lon)
        result.append({
            "house": i,
            "cusp_longitude": round(cusp_lon, 6),
            "sign": sign,
            "degree_in_sign": round(deg_in_sign, 6),
            "name": HOUSE_MEANINGS[i]["name"],
            "area": HOUSE_MEANINGS[i]["area"],
        })
    return result


def _house_of_point(longitude: float, cusps: List[float]) -> int:
    """给定一个黄经，落在 cusps(宫1..12 宫头) 中的第几宫。

    宫 h 的范围：从 cusp[h-1] 起，到 cusp[h % 12] 前止（环形）。
    """
    lon = _normalize_deg(longitude)
    for h in range(1, 13):
        start = cusps[h - 1]
        end = cusps[h % 12]  # 宫12的下一宫头是宫1
        # 处理跨越 0° 的情况
        if start < end:
            if start <= lon < end:
                return h
        else:  # 宫头跨过 0°
            if lon >= start or lon < end:
                return h
    return 12  # 兜底（理论上不会到达）


# ---------------------------------------------------------------------------
# 4. 相位计算
# ---------------------------------------------------------------------------

def compute_aspects(planet_positions: Dict[str, float],
                    planet_speeds: Optional[Dict[str, float]] = None
                    ) -> List[Dict[str, Any]]:
    """计算行星间的主要相位（合/六分/四分/三分/对分）。

    Args:
        planet_positions: {行星名: 黄经 0~360}。
        planet_speeds:    可选 {行星名: 黄经速度 度/日}，用于判断 applying。

    Returns:
        [{"planet1", "planet2", "aspect", "angle", "orb",
          "actual_angle", "applying"}, ...]
    """
    names = list(planet_positions.keys())
    out: List[Dict[str, Any]] = []
    dt = 1.0  # 用 1 天后的角距变化判断是否接近

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            n1, n2 = names[i], names[j]
            lon1, lon2 = planet_positions[n1], planet_positions[n2]

            # 实际最短角距
            sep = abs(lon1 - lon2) % 360.0
            if sep > 180.0:
                sep = 360.0 - sep

            # 找落在容许度内、且为主要相位者
            best: Optional[Dict[str, Any]] = None
            for asp_name in MAJOR_ASPECTS:
                cfg = ASPECT_ORBS[asp_name]
                canonical = float(cfg["angle"])
                orb = float(cfg["orb"])
                delta = abs(sep - canonical)
                if delta <= orb:
                    cand = {"aspect": asp_name, "angle": canonical,
                            "orb": round(delta, 4), "actual_angle": round(sep, 4)}
                    if best is None or cand["orb"] < best["orb"]:
                        best = cand

            if best is None:
                continue

            # applying：比较 t 与 t+dt 的角距是否缩小
            applying = False
            if planet_speeds is not None and n1 in planet_speeds and n2 in planet_speeds:
                s1 = planet_speeds[n1]
                s2 = planet_speeds[n2]
                nlon1 = lon1 + s1 * dt
                nlon2 = lon2 + s2 * dt
                sep2 = abs(nlon1 - nlon2) % 360.0
                if sep2 > 180.0:
                    sep2 = 360.0 - sep2
                applying = sep2 < sep - 1e-6

            out.append({
                "planet1": n1,
                "planet2": n2,
                "aspect": best["aspect"],
                "angle": best["angle"],
                "orb": best["orb"],
                "actual_angle": best["actual_angle"],
                "applying": applying,
            })

    out.sort(key=lambda a: a["orb"])
    return out


# ---------------------------------------------------------------------------
# 5. 完整星盘
# ---------------------------------------------------------------------------

def compute_natal_chart(year: int, month: int, day: int, hour: float,
                        latitude: float, longitude: float) -> Dict[str, Any]:
    """端到端出生星盘（热带黄道 / Placidus）。"""
    jd = _julday(year, month, day, hour)

    # 宫位
    cusps, _ascmc = _houses_raw(jd, latitude, longitude, "Placidus")
    houses = get_houses(year, month, day, hour, latitude, longitude, "Placidus")
    angles = get_angles(year, month, day, hour, latitude, longitude)

    # 行星
    planet_entries: List[Dict[str, Any]] = []
    pos_map: Dict[str, float] = {}
    speed_map: Dict[str, float] = {}
    for pname, flag in PLANET_FLAGS.items():
        lon, speed = _planet_calc(flag, jd)
        sign, deg_in_sign, _ = split_longitude(lon)
        pos_map[pname] = lon
        speed_map[pname] = speed
        planet_entries.append({
            "name": pname,
            "longitude": round(lon, 6),
            "sign": sign,
            "degree": round(deg_in_sign, 6),
            "retrograde": bool(speed < 0.0),
            "speed": round(speed, 6),
            "house": _house_of_point(lon, cusps),
            "dignity": get_dignity(pname, sign),
        })

    aspects = compute_aspects(pos_map, speed_map)

    return {
        "meta": {
            "datetime": f"{year:04d}-{month:02d}-{day:02d}T{hour:07.3f}Z",
            "latitude": latitude,
            "longitude": longitude,
            "system": "Tropical / Placidus",
            "julday": round(jd, 6),
        },
        "planets": planet_entries,
        "angles": angles,
        "houses": houses,
        "aspects": aspects,
    }


__all__ = [
    "PLANET_FLAGS",
    "ZODIAC_SIGNS",
    "HOUSE_SYSTEMS",
    "split_longitude",
    "get_planet_longitude",
    "get_angles",
    "get_houses",
    "compute_aspects",
    "compute_natal_chart",
]
