# -*- coding: utf-8 -*-
"""西洋占星历算层测试：行星黄经 / 四轴 / 分宫 / 相位 / 完整星盘。

运行：
    cd engine && PYTHONPATH=. python -m pytest tests/test_western_ephemeris.py -v
"""
from __future__ import annotations

import math

from western.dignity import get_dignity
from western.ephemeris import (
    PLANET_FLAGS,
    ZODIAC_SIGNS,
    compute_aspects,
    compute_natal_chart,
    get_angles,
    get_houses,
    get_planet_longitude,
    split_longitude,
)


# ---------------------------------------------------------------------------
# 1. 行星黄经：2000-01-01 12:00 UT 太阳约 280° 摩羯座
# ---------------------------------------------------------------------------

def test_sun_2000_jan_1_in_capricorn():
    r = get_planet_longitude("太阳", 2000, 1, 1, 12.0)
    # 2000-01-01 太阳黄经约 280.37°（摩羯座 10° 附近）
    assert 279.0 <= r["longitude"] <= 282.0
    assert r["sign"] == "摩羯座"
    assert 8.0 <= r["degree_in_sign"] <= 13.0
    # 太阳永远顺行
    assert r["retrograde"] is False


# ---------------------------------------------------------------------------
# 2. 星座归属：0°=白羊, 30°=金牛, 330°=双鱼
# ---------------------------------------------------------------------------

def test_zodiac_sign_split():
    assert split_longitude(0.0)[0] == "白羊座"
    assert split_longitude(30.0)[0] == "金牛座"
    assert split_longitude(330.0)[0] == "双鱼座"
    # 边界：29.999 仍白羊，30.0 金牛
    assert split_longitude(29.999)[0] == "白羊座"
    # 360 回绕到 0
    assert split_longitude(360.0)[0] == "白羊座"
    assert split_longitude(359.999)[0] == "双鱼座"


# ---------------------------------------------------------------------------
# 3. 逆行：水星在逆行窗口内 retrograde=True
# ---------------------------------------------------------------------------

def test_mercury_retrograde():
    # 2023-12-13 ~ 2024-01-02 水星逆行（摩羯座/射手座区间）
    r = get_planet_longitude("水星", 2023, 12, 25, 12.0)
    assert r["retrograde"] is True
    assert r["speed"] < 0.0

    # 选一个顺行时段对照：2024-03-15 水星顺行
    r2 = get_planet_longitude("水星", 2024, 3, 15, 12.0)
    assert r2["retrograde"] is False
    assert r2["speed"] > 0.0


# ---------------------------------------------------------------------------
# 4. 四轴：给定经纬度计算 ASC/MC/DSC/IC
# ---------------------------------------------------------------------------

def test_angles_beijing():
    # 北京 1990-01-01 12:00 UT（正午 UTC，北京约 20:00 地方时）
    a = get_angles(1990, 1, 1, 12.0, latitude=39.9, longitude=116.4)
    # 四个轴都在 0~360
    for k in ("asc", "mc", "dsc", "ic"):
        assert 0.0 <= a[k]["longitude"] < 360.0
        assert a[k]["sign"] in ZODIAC_SIGNS
    # DSC = ASC + 180
    assert math.isclose((a["asc"]["longitude"] + 180.0) % 360.0,
                        a["dsc"]["longitude"], abs_tol=1e-4)
    # IC = MC + 180
    assert math.isclose((a["mc"]["longitude"] + 180.0) % 360.0,
                        a["ic"]["longitude"], abs_tol=1e-4)


# ---------------------------------------------------------------------------
# 5. 分宫：12 宫宫头全部计算
# ---------------------------------------------------------------------------

def test_houses_twelve_cusps():
    houses = get_houses(1990, 1, 1, 12.0, latitude=39.9, longitude=116.4)
    assert len(houses) == 12
    for i, h in enumerate(houses, start=1):
        assert h["house"] == i
        assert 0.0 <= h["cusp_longitude"] < 360.0
        assert h["sign"] in ZODIAC_SIGNS
        assert "name" in h and h["name"]  # 宫位中文名非空
    # 1 宫宫头 ≈ ASC
    asc = get_angles(1990, 1, 1, 12.0, 39.9, 116.4)["asc"]
    assert math.isclose(houses[0]["cusp_longitude"],
                        asc["longitude"], abs_tol=1e-3)


# ---------------------------------------------------------------------------
# 6. 完整星盘：compute_natal_chart 字段齐全
# ---------------------------------------------------------------------------

def test_natal_chart_structure():
    chart = compute_natal_chart(1990, 1, 1, 12.0, latitude=39.9, longitude=116.4)

    # meta
    assert chart["meta"]["system"] == "Tropical / Placidus"
    assert chart["meta"]["latitude"] == 39.9
    assert chart["meta"]["longitude"] == 116.4

    # 10 大行星
    assert len(chart["planets"]) == len(PLANET_FLAGS) == 10
    for p in chart["planets"]:
        for key in ("name", "longitude", "sign", "degree",
                    "retrograde", "house", "dignity"):
            assert key in p, f"行星缺少字段 {key}"
        assert 1 <= p["house"] <= 12
        assert "level" in p["dignity"] and "score" in p["dignity"]

    # 四轴
    for k in ("asc", "mc", "dsc", "ic"):
        assert k in chart["angles"]
        assert "longitude" in chart["angles"][k]

    # 12 宫
    assert len(chart["houses"]) == 12

    # 相位（真实星盘应至少有若干主要相位）
    assert isinstance(chart["aspects"], list)
    if chart["aspects"]:
        a0 = chart["aspects"][0]
        for key in ("planet1", "planet2", "aspect", "orb", "applying"):
            assert key in a0


# ---------------------------------------------------------------------------
# 7. 相位：0°=合相，90°=四分相
# ---------------------------------------------------------------------------

def test_aspects_conjunction_and_square():
    # 构造两颗理想行星：A 在 0°，B 在 0° -> 合相
    asp = compute_aspects({"X": 0.0, "Y": 0.0})
    assert len(asp) == 1
    assert asp[0]["aspect"] == "合相"
    assert asp[0]["orb"] < 1e-6

    # A 在 0°，B 在 90° -> 四分相
    asp2 = compute_aspects({"X": 0.0, "Y": 90.0})
    assert len(asp2) == 1
    assert asp2[0]["aspect"] == "四分相"
    assert asp2[0]["orb"] < 1e-6

    # A 在 0°，B 在 180° -> 对分相
    asp3 = compute_aspects({"X": 0.0, "Y": 180.0})
    assert asp3[0]["aspect"] == "对分相"

    # A 在 0°，B 在 45°（八分体，不在主要相位）-> 无相位
    asp4 = compute_aspects({"X": 0.0, "Y": 45.0})
    assert asp4 == []


# ---------------------------------------------------------------------------
# 8. dignity 集成：行星星座的 dignity 被正确附加
# ---------------------------------------------------------------------------

def test_dignity_attached():
    # 太阳在狮子座入庙 -> ruler
    r = get_planet_longitude("太阳", 1990, 8, 10, 12.0)
    # 8 月 10 日太阳在狮子座（约 17° 狮子）
    assert r["sign"] == "狮子座"
    assert r["dignity"]["level"] == "ruler"
    assert r["dignity"]["score"] == 5

    # 月亮在金牛座旺相
    # 找一个月亮在金牛座的时刻：粗算用 2000-01-08 附近（月相）
    # 直接通过 get_dignity 校验逻辑一致性 + 真实调用一次
    moon = get_planet_longitude("月亮", 2000, 1, 8, 12.0)
    expected = get_dignity("月亮", moon["sign"])
    assert moon["dignity"]["level"] == expected["level"]
    assert moon["dignity"]["score"] == expected["score"]
