"""紫微斗数排盘内核测试: 农历换算 / 五行局 / 紫府定位 / 十四主星 / 辅佐煞曜 / 四化."""
import os
import sys

import pytest

# 允许从 engine/ 目录直接运行
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ziwei.chart import (  # noqa: E402
    PALACE_ZHI,
    SIHUA_YEAR,
    determine_wuxing_ju,
    locate_ziwei,
    place_aux_stars,
    place_main_stars,
    sanfang_sizheng,
    setup_palaces,
    solar_to_lunar,
)


# ---------------------------------------------------------------------------
# 1. 农历换算
# ---------------------------------------------------------------------------
def test_solar_to_lunar_1990_0601():
    """1990-06-01 = 庚午年五月初九 (非闰月)."""
    r = solar_to_lunar(1990, 6, 1)
    assert r["lunar_year_ganzhi"] == "庚午"
    assert r["lunar_month"] == 5
    assert r["lunar_day"] == 9
    assert r["is_leap"] is False


def test_solar_to_lunar_leap_month():
    """2023-04-15 = 癸卯年闰二月廿五."""
    r = solar_to_lunar(2023, 4, 15)
    assert r["lunar_month"] == 2
    assert r["is_leap"] is True
    assert r["lunar_day"] == 25


# ---------------------------------------------------------------------------
# 2. 五行局
# ---------------------------------------------------------------------------
def test_wuxing_ju_different_combos():
    """不同年干+时支应得到不同局 (甲寅时 vs 甲午时)."""
    a = determine_wuxing_ju("甲", "寅")
    b = determine_wuxing_ju("甲", "午")
    assert a["ju_name"] != b["ju_name"]
    assert a["ju_num"] in (2, 3, 4, 5, 6)
    assert b["ju_num"] in (2, 3, 4, 5, 6)


def test_wuxing_ju_gan_mapping():
    """甲寅时五虎遁得丙 -> 丙丁木三局."""
    r = determine_wuxing_ju("甲", "寅")
    assert r["gan_at_hour"] == "丙"
    assert r["ju_name"] == "木三局"
    assert r["ju_num"] == 3


# ---------------------------------------------------------------------------
# 3. 起紫微 / 天府
# ---------------------------------------------------------------------------
def test_ziwei_pos_day1_water2():
    """水二局 + 农历初一日 -> 紫微在寅 (索引0)."""
    pos = locate_ziwei(1, 2)
    assert pos["ziwei_pos"] == 0
    assert PALACE_ZHI[pos["ziwei_pos"]] == "寅"


def test_tianfu_mirror_of_ziwei():
    """紫微在寅(0) -> 天府在申(6)."""
    pos = locate_ziwei(1, 2)
    assert pos["tianfu_pos"] == 6
    assert PALACE_ZHI[pos["tianfu_pos"]] == "申"


# ---------------------------------------------------------------------------
# 4. 安十四主星
# ---------------------------------------------------------------------------
def test_ziwei_series_distribution():
    """紫微在寅(0): 紫微系顺时针隔一宫 -> 紫0 机2 日4 武6 同8 贞10."""
    board = place_main_stars(0, 6)
    assert "紫微" in board[0]
    assert "天机" in board[2]
    assert "太阳" in board[4]
    assert "武曲" in board[6]
    assert "天同" in board[8]
    assert "廉贞" in board[10]


def test_main_stars_total_14():
    """十四主星全部被安置 (含同宫多星)."""
    board = place_main_stars(0, 6)
    total = sum(len(v) for v in board.values())
    assert total == 14


# ---------------------------------------------------------------------------
# 5. 禄存 / 擎羊 / 陀罗
# ---------------------------------------------------------------------------
def test_lucun_jia_year():
    """甲年禄存在寅(0)."""
    aux = place_aux_stars("甲", 1, "子", "子")
    assert aux["禄存"] == 0
    assert PALACE_ZHI[aux["禄存"]] == "寅"


def test_qingyang_tuoluo_jia():
    """甲年禄存寅 -> 擎羊前一位卯(1), 陀罗后一位丑(11)."""
    aux = place_aux_stars("甲", 1, "子", "子")
    assert aux["擎羊"] == 1
    assert PALACE_ZHI[aux["擎羊"]] == "卯"
    assert aux["陀罗"] == 11
    assert PALACE_ZHI[aux["陀罗"]] == "丑"


# ---------------------------------------------------------------------------
# 6. 天魁 / 天钺
# ---------------------------------------------------------------------------
def test_kuiyue_jia_year():
    """甲年 -> 魁在丑(11), 钺在未(5)."""
    aux = place_aux_stars("甲", 1, "子", "子")
    assert aux["天魁"] == 11
    assert PALACE_ZHI[aux["天魁"]] == "丑"
    assert aux["天钺"] == 5
    assert PALACE_ZHI[aux["天钺"]] == "未"


# ---------------------------------------------------------------------------
# 7. 生年四化
# ---------------------------------------------------------------------------
def test_sihua_jia_year():
    """甲年: 廉贞化禄, 破军化权, 武曲化科, 太阳化忌."""
    s = SIHUA_YEAR["甲"]
    assert s == {"化禄": "廉贞", "化权": "破军",
                 "化科": "武曲", "化忌": "太阳"}


def test_sihua_table_ten_gan():
    """十干四化表完整 (10 个天干)."""
    assert len(SIHUA_YEAR) == 10
    for gan in SIHUA_YEAR:
        assert set(SIHUA_YEAR[gan].keys()) == {"化禄", "化权", "化科", "化忌"}


# ---------------------------------------------------------------------------
# 8. 完整排盘
# ---------------------------------------------------------------------------
def test_setup_palaces_full():
    """setup_palaces 输出 12 宫, 每宫有 name 与 zhi."""
    chart = setup_palaces(year_gan="甲", year_zhi="子",
                          lunar_month=1, lunar_day=1,
                          hour_zhi="子", gender="男")
    assert len(chart["palaces"]) == 12
    for p in chart["palaces"]:
        assert "name" in p and "zhi" in p
        assert isinstance(p["main_stars"], list)
        assert isinstance(p["aux_stars"], list)
        assert isinstance(p["sha_stars"], list)
        assert isinstance(p["sihua"], list)


def test_setup_palaces_nonempty_stars():
    """星盘非空: 至少安置 14 颗主星."""
    chart = setup_palaces(year_gan="甲", year_zhi="子",
                          lunar_month=1, lunar_day=1,
                          hour_zhi="子")
    total_main = sum(len(p["main_stars"]) for p in chart["palaces"])
    assert total_main == 14
    assert chart["wuxing_ju"]["num"] in (2, 3, 4, 5, 6)


def test_sihua_attached_to_palaces():
    """甲年四化应落到具体宫位 (廉贞化禄/破军化权/武曲化科/太阳化忌)."""
    chart = setup_palaces(year_gan="甲", year_zhi="子",
                          lunar_month=1, lunar_day=1, hour_zhi="子")
    all_sihua = [s for p in chart["palaces"] for s in p["sihua"]]
    assert "廉贞化禄" in all_sihua
    assert "破军化权" in all_sihua
    assert "武曲化科" in all_sihua
    assert "太阳化忌" in all_sihua


def test_sanfang_sizheng():
    """命宫三方四正: 命0 财4 官8 迁6."""
    sf = sanfang_sizheng(0)
    assert sf == {"命宫": 0, "财帛": 4, "官禄": 8, "迁移": 6}
