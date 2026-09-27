"""八字干支历算模块测试: 四柱排盘 / 节气月建 / 真太阳时 / 纳音 / 旬首."""
import os
import sys

import pytest

# 允许从 engine/ 目录直接运行
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bazi.ganzhi import (  # noqa: E402
    NA_YIN,
    TIANGAN,
    DIZHI,
    BaziPillar,
    compute_bazi,
    get_day_xun,
    wuhu_dun,
    wushu_dun,
    wuxing_of_gan,
    wuxing_of_zhi,
)


# ---------------------------------------------------------------------------
# 1. 已知八字: 2000-01-01 12:00 北京时间
# ---------------------------------------------------------------------------
def test_known_bazi_2000_0101_noon():
    """2000-01-01 在立春前, 年柱属 1999 己卯年."""
    c = compute_bazi(2000, 1, 1, 12, 0, longitude=120.0)
    assert c.year.gz == "己卯"      # 立春前属上年
    assert c.month.gz == "丙子"     # 己年寅月丙寅, 逆推至子月=丙子
    assert c.day.gz == "戊午"
    assert c.hour.gz == "戊午"      # 戊日午时=戊午
    assert c.year.na_yin == "城头土"   # 己卯=城头土
    assert c.day.na_yin == "天上火"    # 戊午=天上火


# ---------------------------------------------------------------------------
# 2. 节气边界: 立春当天年柱切换
# ---------------------------------------------------------------------------
def test_lichun_boundary_before():
    """2000 立春 = 2/4 20:40. 当天上午仍属己卯年/丁丑月."""
    c = compute_bazi(2000, 2, 4, 10, 0, longitude=120.0)
    assert c.year.gz == "己卯"
    assert c.month.gz == "丁丑"
    assert c.jieqi == "小寒"


def test_lichun_boundary_after():
    """立春交节后切换为庚辰年/戊寅月."""
    c = compute_bazi(2000, 2, 4, 21, 0, longitude=120.0)
    assert c.year.gz == "庚辰"
    assert c.month.gz == "戊寅"
    assert c.jieqi == "立春"


# ---------------------------------------------------------------------------
# 3. 月柱: 寅月=立春后, 卯月=惊蛰后
# ---------------------------------------------------------------------------
def test_month_yin_after_lichun():
    """2000-03-01 (立春后, 惊蛰前) = 戊寅月."""
    c = compute_bazi(2000, 3, 1, 12, 0, longitude=120.0)
    assert c.month.gz == "戊寅"
    assert c.jieqi == "立春"


def test_month_mao_after_jingzhe():
    """2000 惊蛰 = 3/5 14:42. 当天 20:00 后 = 己卯月."""
    c = compute_bazi(2000, 3, 5, 20, 0, longitude=120.0)
    assert c.month.gz == "己卯"
    assert c.jieqi == "惊蛰"


def test_month_mao_before_jingzhe():
    """惊蛰当天上午仍属戊寅月."""
    c = compute_bazi(2000, 3, 5, 10, 0, longitude=120.0)
    assert c.month.gz == "戊寅"
    assert c.jieqi == "立春"


# ---------------------------------------------------------------------------
# 4. 日柱: 已知日期日柱
# ---------------------------------------------------------------------------
def test_day_pillar_known():
    """2000-01-07 = 甲子日 (已知)."""
    c = compute_bazi(2000, 1, 7, 12, 0, longitude=120.0)
    assert c.day.gz == "甲子"


# ---------------------------------------------------------------------------
# 5. 时柱: 五鼠遁 + 子时换日
# ---------------------------------------------------------------------------
def test_hour_zi_on_jiazi_day():
    """甲子日子时 → 甲子时."""
    c = compute_bazi(2000, 1, 7, 0, 0, longitude=120.0)
    assert c.day.gz == "甲子"
    assert c.hour.gz == "甲子"


def test_hour_wu_on_jiazi_day():
    """甲子日午时 → 庚午时."""
    c = compute_bazi(2000, 1, 7, 12, 0, longitude=120.0)
    assert c.day.gz == "甲子"
    assert c.hour.gz == "庚午"


def test_hour_23_rolls_day():
    """23:30 属次日子时, 日柱推进一天."""
    c = compute_bazi(2000, 1, 1, 23, 30, longitude=120.0)
    # Jan 1 = 戊午, Jan 2 = 己未
    assert c.day.gz == "己未"
    assert c.hour.gz == "甲子"   # 己日子时=甲子


# ---------------------------------------------------------------------------
# 6. 真太阳时修正: 成都 105°E
# ---------------------------------------------------------------------------
def test_true_solar_time_chengdu():
    """成都 105°E 比北京时间晚 (105-120)*4 = -60 分钟, 加均时差."""
    c = compute_bazi(2000, 1, 1, 12, 0, longitude=105.0)
    # 真太阳时 ≈ 12:00 - 60min + EoT(≈-4min) ≈ 10:56
    # 10:56 属巳时 (9-11), 戊日巳时=丁巳
    assert c.hour.gz == "丁巳"
    # 真太阳时字符串应比北京 12:00 晚约 1 小时
    assert c.true_solar_time.endswith("10:56")


# ---------------------------------------------------------------------------
# 7. 旬首
# ---------------------------------------------------------------------------
def test_xun_jiazi():
    assert get_day_xun("甲", "子") == "甲子"
    assert get_day_xun("乙", "丑") == "甲子"
    assert get_day_xun("丙", "寅") == "甲子"
    assert get_day_xun("癸", "酉") == "甲子"  # 癸酉=甲子旬末


def test_xun_jiaxu():
    assert get_day_xun("甲", "戌") == "甲戌"
    assert get_day_xun("乙", "亥") == "甲戌"
    assert get_day_xun("癸", "未") == "甲戌"


def test_xun_from_compute():
    """戊午日属甲寅旬."""
    c = compute_bazi(2000, 1, 1, 12, 0, longitude=120.0)
    assert c.day_xun == "甲寅"


# ---------------------------------------------------------------------------
# 8. 五虎遁
# ---------------------------------------------------------------------------
def test_wuhu_dun():
    assert wuhu_dun("甲", "寅") == "丙"   # 甲己之年丙作首
    assert wuhu_dun("己", "寅") == "丙"
    assert wuhu_dun("乙", "寅") == "戊"   # 乙庚之岁戊为头
    assert wuhu_dun("庚", "寅") == "戊"
    assert wuhu_dun("丙", "寅") == "庚"   # 丙辛必定寻庚起
    assert wuhu_dun("丁", "寅") == "壬"   # 丁壬壬位顺行流
    assert wuhu_dun("戊", "寅") == "甲"   # 戊癸甲寅好追求


# ---------------------------------------------------------------------------
# 9. 五鼠遁
# ---------------------------------------------------------------------------
def test_wushu_dun():
    assert wushu_dun("甲", "子") == "甲"   # 甲己还加甲
    assert wushu_dun("己", "子") == "甲"
    assert wushu_dun("乙", "子") == "丙"   # 乙庚丙作初
    assert wushu_dun("丙", "子") == "戊"   # 丙辛从戊起
    assert wushu_dun("丁", "子") == "庚"   # 丁壬庚子居
    assert wushu_dun("戊", "子") == "壬"   # 戊癸壬子是真途


# ---------------------------------------------------------------------------
# 10. 五行 & 纳音完整性
# ---------------------------------------------------------------------------
def test_wuxing():
    assert wuxing_of_gan("甲") == "木"
    assert wuxing_of_gan("丁") == "火"
    assert wuxing_of_gan("庚") == "金"
    assert wuxing_of_zhi("寅") == "木"
    assert wuxing_of_zhi("午") == "火"
    assert wuxing_of_zhi("辰") == "土"
    assert wuxing_of_zhi("亥") == "水"


def test_nayin_complete():
    """60 甲子纳音表完整, 每对干支同纳音."""
    assert len(NA_YIN) == 60
    # 已知抽查
    assert NA_YIN["甲子"] == "海中金"
    assert NA_YIN["乙丑"] == "海中金"
    assert NA_YIN["丙寅"] == "炉中火"
    assert NA_YIN["戊午"] == "天上火"
    assert NA_YIN["癸亥"] == "大海水"
    # 所有合法干支组合都在表中
    for g in TIANGAN:
        for z in DIZHI:
            if TIANGAN.index(g) % 2 == DIZHI.index(z) % 2:
                assert g + z in NA_YIN, f"纳音缺失: {g}{z}"


# ---------------------------------------------------------------------------
# 11. BaziPillar 结构
# ---------------------------------------------------------------------------
def test_pillar_structure():
    c = compute_bazi(2000, 1, 1, 12, 0, longitude=120.0)
    assert isinstance(c.year, BaziPillar)
    assert c.year.gan == "己"
    assert c.year.zhi == "卯"
    assert c.year.wx == "土"
    assert c.year.gz == "己卯"
