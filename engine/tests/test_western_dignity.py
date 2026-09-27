# -*- coding: utf-8 -*-
"""西洋占星规则层测试：尊贵表 / 相位容许度 / 宫位含义 / 规则引擎加载。

运行：
    cd engine && PYTHONPATH=. python -m pytest tests/test_western_dignity.py -v
"""
from __future__ import annotations

from pathlib import Path

import pytest

from rule_engine import RuleEngine
from western.dignity import (
    DIGNITY_TABLE,
    ASPECT_ORBS,
    HOUSE_MEANINGS,
    PLANETS,
    ZODIAC_SIGNS,
    get_dignity,
    check_aspect,
    get_house_meaning,
)

RULES_PATH = Path(__file__).resolve().parents[1] / "rules" / "rules_western.json"


# ---------------------------------------------------------------------------
# 1. 行星尊贵表
# ---------------------------------------------------------------------------

def test_sun_in_leo_is_ruler():
    r = get_dignity("太阳", "狮子座")
    assert r["level"] == "ruler"
    assert r["score"] == 5


def test_sun_in_aries_is_exaltation():
    r = get_dignity("太阳", "白羊座")
    assert r["level"] == "exaltation"
    assert r["score"] == 4


def test_sun_in_aquarius_is_detriment():
    r = get_dignity("太阳", "水瓶座")
    assert r["level"] == "detriment"
    assert r["score"] == -4


def test_sun_in_libra_is_fall():
    r = get_dignity("太阳", "天秤座")
    assert r["level"] == "fall"
    assert r["score"] == -5


def test_neutral_sign_is_none():
    r = get_dignity("太阳", "巨蟹座")
    assert r["level"] == "none"
    assert r["score"] == 0


def test_dignity_table_completeness():
    # 10 行星，每行星含四类尊贵
    assert len(PLANETS) == 10
    for planet, levels in DIGNITY_TABLE.items():
        for key in ("ruler", "exaltation", "detriment", "fall"):
            assert key in levels and len(levels[key]) >= 1, (planet, key)
            for sign in levels[key]:
                assert sign in ZODIAC_SIGNS


# ---------------------------------------------------------------------------
# 2. 相位容许度
# ---------------------------------------------------------------------------

def test_conjunction_within_orb():
    # 0° ± 8°
    assert check_aspect(0, 3)["aspect"] == "合相"
    assert check_aspect(0, 3)["matched"] is True
    assert check_aspect(0, 7.9)["aspect"] == "合相"


def test_conjunction_out_of_orb():
    # 0° 容许度 8°，9° 应不再是合相
    r = check_aspect(0, 9.5)
    assert r["matched"] is False or r["aspect"] != "合相"


def test_square_exact_and_inside_orb():
    # 90° ± 6°
    assert check_aspect(0, 90)["aspect"] == "四分相"
    assert check_aspect(0, 90)["delta"] == 0
    assert check_aspect(0, 95)["aspect"] == "四分相"  # delta=5 <= 6


def test_square_out_of_orb():
    # 97° 距 90° 为 7° > 6°，不成四分相
    r = check_aspect(0, 97)
    assert r["aspect"] != "四分相"


def test_named_aspect_specific_check():
    # 指定合相时，90° 不应判为合相
    r = check_aspect(0, 90, aspect="合相")
    assert r["matched"] is False
    # 指定四分相时，90° 命中
    r2 = check_aspect(0, 90, aspect="四分相")
    assert r2["matched"] is True and r2["aspect"] == "四分相"


def test_aspect_table_completeness():
    assert len(ASPECT_ORBS) == 9
    for name, cfg in ASPECT_ORBS.items():
        assert "angle" in cfg and "orb" in cfg


# ---------------------------------------------------------------------------
# 3. 宫位含义
# ---------------------------------------------------------------------------

def test_house1_is_self():
    m = get_house_meaning(1)
    assert m["name"] == "命宫"
    assert "自我" in m["area"]


def test_house7_is_partner():
    m = get_house_meaning(7)
    assert m["name"] == "夫妻宫"
    assert "婚姻" in m["area"]


def test_house12_is_unknown():
    m = get_house_meaning(12)
    assert m["name"] == "玄秘宫"


def test_house_out_of_range_raises():
    with pytest.raises(ValueError):
        get_house_meaning(13)
    with pytest.raises(ValueError):
        get_house_meaning(0)


def test_house_table_completeness():
    assert len(HOUSE_MEANINGS) == 12
    for i in range(1, 13):
        assert i in HOUSE_MEANINGS


# ---------------------------------------------------------------------------
# 4. 规则引擎集成
# ---------------------------------------------------------------------------

def test_domains_include_western():
    assert "western" in RuleEngine.DOMAINS


def test_rules_western_json_loads():
    engine = RuleEngine()
    rules = engine.load_rules("western")
    assert isinstance(rules, list)
    assert len(rules) == 72
    cats = {r["category"] for r in rules}
    assert cats == {"dignity", "aspect", "house"}


def test_engine_match_dignity_facts():
    engine = RuleEngine()
    res = engine.match({"planet": "太阳", "sign": "狮子座"}, "western")
    assert "ruler" in res["conclusions"]
    res2 = engine.match({"planet": "太阳", "sign": "天秤座"}, "western")
    assert "fall" in res2["conclusions"]


def test_engine_match_aspect_and_house_facts():
    engine = RuleEngine()
    assert "合相" in engine.match({"aspect": "合相"}, "western")["conclusions"]
    assert "夫妻宫" in engine.match({"house": 7}, "western")["conclusions"]
