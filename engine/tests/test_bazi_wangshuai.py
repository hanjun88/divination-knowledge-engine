"""八字旺衰 / 十神 / 起运模块测试.

覆盖:
  - 十神十种关系 (甲日干为基准)
  - 地支藏干表 (12 地支)
  - 通根本气/中气/余气权重
  - 旺衰身旺 / 身弱 / 中和
  - 用神忌神推断
  - 起运顺排 / 逆排 / 大运干支序列
  - 真实八字端到端 (compute_bazi → compute_wangshuai → compute_qiyun)
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bazi.ganzhi import (  # noqa: E402
    BaziChart,
    BaziPillar,
    DIZHI,
    TIANGAN,
    compute_bazi,
    wuxing_of_gan,
)
from bazi.wangshuai import (  # noqa: E402
    CANG_GAN_WEIGHT,
    GAN_YIN_YANG,
    ZHI_CANG_GAN,
    compute_qiyun,
    compute_wangshuai,
    get_shishen,
)


# ---------------------------------------------------------------------------
# 工具: 由干支字符串直接构造 BaziChart (用于受控旺衰测试)
# ---------------------------------------------------------------------------
def _pillar(gz: str) -> BaziPillar:
    from bazi.ganzhi import NA_YIN, wuxing_of_zhi
    g, z = gz[0], gz[1]
    return BaziPillar(
        gan=g, zhi=z,
        wx=wuxing_of_gan(g),
        na_yin=NA_YIN[gz],
    )


def _chart(year_gz: str, month_gz: str, day_gz: str, hour_gz: str,
           true_solar_time: str = "2000-03-01 12:00") -> BaziChart:
    return BaziChart(
        year=_pillar(year_gz),
        month=_pillar(month_gz),
        day=_pillar(day_gz),
        hour=_pillar(hour_gz),
        solar_date="2000-03-01",
        lunar_date="2000-01-26",
        jieqi="立春",
        day_xun="甲子",
        true_solar_time=true_solar_time,
    )


# ---------------------------------------------------------------------------
# 1. 十神: 甲日干 → 10 种十神全覆盖
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("other_gan,expected", [
    ("甲", "比肩"),
    ("乙", "劫财"),
    ("丙", "食神"),
    ("丁", "伤官"),
    ("戊", "偏财"),
    ("己", "正财"),
    ("庚", "七杀"),
    ("辛", "正官"),
    ("壬", "偏印"),
    ("癸", "正印"),
])
def test_shishen_jia_day_master(other_gan, expected):
    assert get_shishen("甲", other_gan) == expected


def test_shishen_self_is_bijian():
    assert get_shishen("庚", "庚") == "比肩"
    assert get_shishen("辛", "辛") == "比肩"


def test_shishen_yin_day_master():
    """乙(阴木)日干: 丁=食神(阴生阴), 丙=伤官(阴生阳)."""
    assert get_shishen("乙", "丁") == "食神"
    assert get_shishen("乙", "丙") == "伤官"
    assert get_shishen("乙", "戊") == "正财"   # 阴克阳
    assert get_shishen("乙", "己") == "偏财"   # 阴克阴
    assert get_shishen("乙", "庚") == "正官"   # 阳克阴
    assert get_shishen("乙", "辛") == "七杀"   # 阴克阴


# ---------------------------------------------------------------------------
# 2. 地支藏干表
# ---------------------------------------------------------------------------
def test_canggan_zi():
    assert ZHI_CANG_GAN["子"] == ["癸"]


def test_canggan_yin():
    assert ZHI_CANG_GAN["寅"] == ["甲", "丙", "戊"]


def test_canggan_chen():
    assert ZHI_CANG_GAN["辰"] == ["戊", "乙", "癸"]


def test_canggan_all_12():
    """12 地支藏干表完整."""
    assert set(ZHI_CANG_GAN.keys()) == set(DIZHI)
    assert CANG_GAN_WEIGHT == [1.0, 0.5, 0.3]


# ---------------------------------------------------------------------------
# 3. 通根: 甲木日主见寅支(本气根) +1.5
# ---------------------------------------------------------------------------
def test_tonggen_benqi_yin():
    """甲木日主见寅 (本气甲木) → 本气根 +1.5."""
    c = _chart(
        year_gz="甲寅", month_gz="丙寅",
        day_gz="甲寅", hour_gz="甲子",
    )
    w = compute_wangshuai(c)
    # 年支寅(1.5) + 日支寅(1.5) + 时支子(无木根) = 3.0
    assert w["gen_score"] == 3.0
    assert w["tonggen_count"] == 2


def test_tonggen_zhongqi_yuqi():
    """甲木日主见未/辰: 未中乙为余气根(+0.5), 辰中乙为中气根(+0.8)."""
    c = _chart(
        year_gz="丁未", month_gz="甲寅",
        day_gz="甲辰", hour_gz="甲子",
    )
    # 年支未: [己,丁,乙], 乙在 index2 = 余气 +0.5
    # 日支辰: [戊,乙,癸], 乙在 index1 = 中气 +0.8
    # 时支子: 无木根
    w = compute_wangshuai(c)
    assert w["gen_score"] == 1.3
    assert w["tonggen_count"] == 2


# ---------------------------------------------------------------------------
# 4. 旺衰 — 身旺
# ---------------------------------------------------------------------------
def test_wang_shishen_wang():
    """甲木生寅月 + 比劫林立 → 旺."""
    c = _chart(
        year_gz="甲寅", month_gz="丙寅",
        day_gz="甲寅", hour_gz="甲子",
    )
    w = compute_wangshuai(c)
    # 月令临官 +3, 通根 3.0, 比劫(甲年/甲时) +2.0, 食伤(丙) -0.8
    # = 7.2
    assert w["score"] >= 5
    assert w["label"] == "旺"


def test_wang_shishen_pianwang():
    """甲木生寅月, 但只有一个比劫透干 → 偏旺."""
    c = _chart(
        year_gz="甲子", month_gz="丙寅",
        day_gz="甲寅", hour_gz="戊辰",
    )
    w = compute_wangshuai(c)
    # 月令 +3, 通根: 日支寅 1.5 (年支子/时支辰无木本气; 辰余气乙+0.5) = 2.0
    # 比劫 0 (天干甲年? 年干甲=比肩 +1.0), 印 0, 食伤 丙 -0.8, 财 戊 -0.6
    # = 3 + 2.0 + 1.0 - 0.8 - 0.6 = 4.6 → 偏旺
    assert 2 <= w["score"] < 5
    assert w["label"] == "偏旺"


# ---------------------------------------------------------------------------
# 5. 旺衰 — 身弱
# ---------------------------------------------------------------------------
def test_wang_shishen_ruo():
    """甲木生酉月, 官杀围克 → 弱."""
    c = _chart(
        year_gz="庚申", month_gz="辛酉",
        day_gz="甲戌", hour_gz="庚午",
    )
    w = compute_wangshuai(c)
    # 月令酉金克木 -2.5
    # 通根: 申/戌/午 皆无木 = 0
    # 天干: 庚(七杀 -1.0), 辛(正官 -1.0), 庚(七杀 -1.0) = -3.0
    # 总 = -5.5
    assert w["score"] < -5
    assert w["label"] == "弱"


def test_wang_shishen_pianruo():
    """甲木生申月, 多官杀财 → 偏弱."""
    c = _chart(
        year_gz="庚申", month_gz="甲申",
        day_gz="甲戌", hour_gz="庚午",
    )
    w = compute_wangshuai(c)
    # 月令申金克木 -2.5
    # 通根 0, 比劫(月干甲) +1.0, 官杀(庚年/庚时) -2.0
    # 总 = -3.5 → 偏弱
    assert -5 <= w["score"] < -2
    assert w["label"] == "偏弱"


# ---------------------------------------------------------------------------
# 6. 用神 / 忌神
# ---------------------------------------------------------------------------
def test_yongshen_for_wang():
    c = _chart("甲寅", "丙寅", "甲寅", "甲子")
    w = compute_wangshuai(c)
    assert "克泄耗" in w["yongshen"]
    assert "生扶" in w["jishen"]


def test_yongshen_for_ruo():
    c = _chart("庚申", "辛酉", "甲戌", "庚午")
    w = compute_wangshuai(c)
    assert "生扶" in w["yongshen"]
    assert "克泄耗" in w["jishen"]


# ---------------------------------------------------------------------------
# 7. 起运 — 阳年男顺排 / 阴年男逆排
# ---------------------------------------------------------------------------
def test_qiyun_yang_year_male_shun():
    """2000-03-01 = 庚辰年(阳) 男 → 顺排."""
    c = compute_bazi(2000, 3, 1, 12, 0, longitude=120.0)
    q = compute_qiyun(c, gender="男")
    assert q["direction"] == "顺排"
    # 月柱戊寅, 顺排第一柱 = 己卯
    assert q["dayun"][0]["gan"] == "己"
    assert q["dayun"][0]["zhi"] == "卯"
    # 8 步大运
    assert len(q["dayun"]) == 8
    # 每步 10 年, 起始年龄递增 10
    ages = [d["start_age"] for d in q["dayun"]]
    assert ages == list(range(ages[0], ages[0] + 80, 10))
    # 起运岁数: 出生 3/1 → 惊蛰 3/5 14:42 ≈ 4.2 天 / 3 ≈ 1.4 岁
    assert 0.5 < q["qiyun_age"] < 3.0


def test_qiyun_yin_year_male_ni():
    """1999-03-01 = 己卯年(阴) 男 → 逆排."""
    c = compute_bazi(1999, 3, 1, 12, 0, longitude=120.0)
    q = compute_qiyun(c, gender="男")
    assert q["direction"] == "逆排"
    # 月柱丙寅, 逆排第一柱 = 乙丑
    assert q["dayun"][0]["gan"] == "乙"
    assert q["dayun"][0]["zhi"] == "丑"


def test_qiyun_yang_year_female_ni():
    """阳年女 → 逆排."""
    c = compute_bazi(2000, 3, 1, 12, 0, longitude=120.0)
    q = compute_qiyun(c, gender="女")
    assert q["direction"] == "逆排"
    # 月柱戊寅, 逆排第一柱 = 丁丑
    assert q["dayun"][0]["gan"] == "丁"
    assert q["dayun"][0]["zhi"] == "丑"


# ---------------------------------------------------------------------------
# 8. 真实八字端到端
# ---------------------------------------------------------------------------
def test_end_to_end_real_bazi():
    """2000-01-01 12:00 北京 → 完整排盘 + 旺衰 + 起运."""
    c = compute_bazi(2000, 1, 1, 12, 0, longitude=120.0)
    assert c.year.gz == "己卯"
    assert c.day.gz == "戊午"

    w = compute_wangshuai(c)
    assert w["label"] in ("旺", "偏旺", "中和", "偏弱", "弱")
    assert "score" in w and isinstance(w["score"], float)
    assert "yongshen" in w and "jishen" in w

    q = compute_qiyun(c, gender="男")
    # 己卯年(阴) 男 → 逆排
    assert q["direction"] == "逆排"
    assert len(q["dayun"]) == 8
    assert q["qiyun_age"] > 0
