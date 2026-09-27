"""八字大运 / 流年 / 流月 推进器测试.

覆盖:
  - 60 甲子表首尾
  - 流年干支 (1984=甲子, 2000=庚辰, 2024=甲辰)
  - 流月五虎遁 (甲年寅月=丙寅, 甲年卯月=丁卯)
  - 大运按年龄定位 (构造 qiyun_result)
  - 未起运: age < qiyun_age → started=False
  - 综合推进器端到端 (compute_bazi → compute_qiyun → advance_to_date)
  - 大运天干对日主十神判定
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bazi.dayun import (  # noqa: E402
    JIAZI_60,
    advance_to_date,
    get_dayun_at_age,
    get_liunian,
    get_liuyue,
)
from bazi.ganzhi import compute_bazi  # noqa: E402
from bazi.wangshuai import compute_qiyun, get_shishen  # noqa: E402

_SHISHEN_SET = {
    "比肩", "劫财", "食神", "伤官", "偏财",
    "正财", "七杀", "正官", "偏印", "正印",
}


# ---------------------------------------------------------------------------
# 工具: 构造受控的 qiyun_result
# ---------------------------------------------------------------------------
def _fake_qiyun(qiyun_age: float = 5.0, direction: str = "顺排") -> dict:
    """月柱=乙丑, 顺排 → dayun[0]=丙寅(5-14), dayun[1]=丁卯(15-24), ..."""
    dayun = []
    mg, mz = 1, 1  # 乙丑
    for i in range(8):
        step = i + 1
        g = (mg + step) % 10
        z = (mz + step) % 12
        dayun.append({
            "gan": "甲乙丙丁戊己庚辛壬癸"[g],
            "zhi": "子丑寅卯辰巳午未申酉戌亥"[z],
            "start_age": 5 + i * 10,
            "end_age": 5 + (i + 1) * 10 - 1,
        })
    return {"qiyun_age": qiyun_age, "direction": direction, "dayun": dayun}


# ---------------------------------------------------------------------------
# 1. 60 甲子表
# ---------------------------------------------------------------------------
def test_jiazi_60_first():
    assert JIAZI_60[0] == "甲子"


def test_jiazi_60_last():
    assert JIAZI_60[59] == "癸亥"


def test_jiazi_60_length_and_no_repeat():
    assert len(JIAZI_60) == 60
    assert len(set(JIAZI_60)) == 60


# ---------------------------------------------------------------------------
# 2. 流年
# ---------------------------------------------------------------------------
def test_liunian_1984_jiazi():
    r = get_liunian(1984)
    assert r["gan"] == "甲"
    assert r["zhi"] == "子"
    assert r["wx"] == "木"
    assert r["year"] == 1984


def test_liunian_2000_gengchen():
    r = get_liunian(2000)
    assert r["gan"] == "庚"
    assert r["zhi"] == "辰"


def test_liunian_2024_jiachen():
    r = get_liunian(2024)
    assert r["gan"] == "甲"
    assert r["zhi"] == "辰"


# ---------------------------------------------------------------------------
# 3. 流月 (五虎遁)
# ---------------------------------------------------------------------------
def test_liuyue_jia_year_yin():
    """甲年寅月(2月) = 丙寅."""
    r = get_liuyue(1984, 2)  # 1984=甲子年
    assert r["zhi"] == "寅"
    assert r["gan"] == "丙"


def test_liuyue_jia_year_mao():
    """甲年卯月(3月) = 丁卯."""
    r = get_liuyue(1984, 3)
    assert r["zhi"] == "卯"
    assert r["gan"] == "丁"


def test_liuyue_month_zhi_mapping():
    """1月=丑, 12月=子."""
    assert get_liuyue(2000, 1)["zhi"] == "丑"
    assert get_liuyue(2000, 12)["zhi"] == "子"


# ---------------------------------------------------------------------------
# 4. 大运按年龄定位
# ---------------------------------------------------------------------------
def test_dayun_started_first():
    q = _fake_qiyun(qiyun_age=5.0)
    r = get_dayun_at_age(q, 5)
    assert r["started"] is True
    assert r["gan"] == "丙"   # dayun[0] = 丙寅
    assert r["zhi"] == "寅"
    assert r["index"] == 0
    assert r["start_age"] == 5
    assert r["end_age"] == 14


def test_dayun_boundary_age14():
    """age=14 仍在第一步大运 (5-14)."""
    q = _fake_qiyun(qiyun_age=5.0)
    r = get_dayun_at_age(q, 14)
    assert r["index"] == 0


def test_dayun_next_decade():
    q = _fake_qiyun(qiyun_age=5.0)
    r = get_dayun_at_age(q, 15)
    assert r["index"] == 1
    assert r["gan"] == "丁"   # dayun[1] = 丁卯
    assert r["zhi"] == "卯"


def test_dayun_wx():
    q = _fake_qiyun(qiyun_age=5.0)
    r = get_dayun_at_age(q, 5)
    assert r["wx"] == "火"   # 丙 = 火


# ---------------------------------------------------------------------------
# 5. 未起运
# ---------------------------------------------------------------------------
def test_dayun_not_started():
    q = _fake_qiyun(qiyun_age=5.0)
    r = get_dayun_at_age(q, 3)  # 3 < 5
    assert r["started"] is False
    assert r["index"] == -1
    # 月柱 = 乙丑 (顺排, dayun[0]=丙寅 反推 -1 步)
    assert r["gan"] == "乙"
    assert r["zhi"] == "丑"


def test_dayun_not_started_at_birth():
    q = _fake_qiyun(qiyun_age=5.0)
    r = get_dayun_at_age(q, 0)
    assert r["started"] is False


# ---------------------------------------------------------------------------
# 6. 综合推进器端到端
# ---------------------------------------------------------------------------
def test_advance_to_date_end_to_end():
    chart = compute_bazi(2000, 1, 1, 12)
    q = compute_qiyun(chart, gender="男")
    out = advance_to_date(chart, q, 2024, 6, 1)

    # 2000-01-01 出生 → 2024 年 age = 24
    assert out["target_date"] == "2024-06-01"
    assert out["age"] == 24

    # 三块时间字段齐全
    assert "gan" in out["dayun"] and "zhi" in out["dayun"]
    assert "gan" in out["liunian"] and out["liunian"]["year"] == 2024
    assert out["liunian"]["gan"] == "甲"   # 2024=甲辰
    assert out["liunian"]["zhi"] == "辰"
    assert "gan" in out["liuyue"] and out["liuyue"]["month"] == 6

    # 三个十神均为合法十神
    assert out["dayun_shishen"] in _SHISHEN_SET
    assert out["liunian_shishen"] in _SHISHEN_SET
    assert out["liuyue_shishen"] in _SHISHEN_SET


def test_advance_to_date_shishen_correct():
    """大运天干对日主十神 == get_shishen(day_gan, dayun_gan)."""
    chart = compute_bazi(2000, 1, 1, 12)
    q = compute_qiyun(chart, gender="男")
    out = advance_to_date(chart, q, 2024, 6, 1)

    day_gan = chart.day.gan  # 戊午日 → 戊
    assert out["dayun_shishen"] == get_shishen(day_gan, out["dayun"]["gan"])
    assert out["liunian_shishen"] == get_shishen(day_gan, out["liunian"]["gan"])
    assert out["liuyue_shishen"] == get_shishen(day_gan, out["liuyue"]["gan"])


def test_advance_to_date_not_started():
    """目标年龄小于起运岁数 → dayun.started=False."""
    chart = compute_bazi(2000, 1, 1, 12)
    q = compute_qiyun(chart, gender="男")
    # 出生当年 (age=0) 必然未起运
    out = advance_to_date(chart, q, 2000, 6, 1)
    assert out["dayun"]["started"] is False
