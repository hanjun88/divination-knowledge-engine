"""六爻纳甲内核 (najia.py) 单元测试。"""
from __future__ import annotations

import pytest

from liuyao.najia import (
    BINARY_TO_PALACE,
    LIUSHEN_ORDER,
    NAJIA_TABLE,
    PALACE_WX,
    ZHI_WX,
    assign_liushen,
    assign_liuqin,
    bian_zhi_for_yao,
    find_palace_of_binary,
    najia_for_palace,
    zhi_to_wx,
)


# ---------------------------------------------------------------------------
# 1. 纳甲表完整性
# ---------------------------------------------------------------------------

def test_najia_table_has_all_8_palaces():
    assert set(NAJIA_TABLE.keys()) == {
        "乾宫", "坤宫", "震宫", "巽宫",
        "坎宫", "离宫", "艮宫", "兑宫",
    }


def test_pure_hexagram_map_covers_64():
    # 八宫 × 八卦 = 64 卦，无重复
    assert len(BINARY_TO_PALACE) == 64


# ---------------------------------------------------------------------------
# 2. 乾宫纳甲：乾为天
# ---------------------------------------------------------------------------

def test_qian_pure_najia_zhi():
    zhī = [najia_for_palace("乾宫", i)[1] for i in range(1, 7)]
    assert zhī == ["子", "寅", "辰", "午", "申", "戌"]


def test_qian_pure_najia_gan():
    gan = [najia_for_palace("乾宫", i)[0] for i in range(1, 7)]
    assert gan == ["甲", "甲", "甲", "壬", "壬", "壬"]


# ---------------------------------------------------------------------------
# 3. 坤宫纳甲：坤为地
# ---------------------------------------------------------------------------

def test_kun_pure_najia():
    gan = [najia_for_palace("坤宫", i)[0] for i in range(1, 7)]
    zhi = [najia_for_palace("坤宫", i)[1] for i in range(1, 7)]
    assert gan == ["乙", "乙", "乙", "癸", "癸", "癸"]
    assert zhi == ["未", "巳", "卯", "丑", "亥", "酉"]


# ---------------------------------------------------------------------------
# 4. 其他宫位抽查
# ---------------------------------------------------------------------------

def test_other_palaces_najia():
    assert [najia_for_palace("坎宫", i)[1] for i in range(1, 7)] == ["寅", "辰", "午", "申", "戌", "子"]
    assert [najia_for_palace("震宫", i)[1] for i in range(1, 7)] == ["子", "寅", "辰", "午", "申", "戌"]
    assert [najia_for_palace("巽宫", i)[1] for i in range(1, 7)] == ["丑", "亥", "酉", "未", "巳", "卯"]
    # 震同乾地支，但天干纳庚
    assert najia_for_palace("震宫", 1) == ("庚", "子")


# ---------------------------------------------------------------------------
# 5. 六亲装配
# ---------------------------------------------------------------------------

def test_liuqin_qian_gong():
    # 本宫金：生我=父母，我生=子孙，克我=官鬼，我克=妻财，同我=兄弟
    assert assign_liuqin("金", "水") == "子孙"   # 金生水
    assert assign_liuqin("金", "木") == "妻财"   # 金克木
    assert assign_liuqin("金", "火") == "官鬼"   # 火克金
    assert assign_liuqin("金", "土") == "父母"   # 土生金
    assert assign_liuqin("金", "金") == "兄弟"   # 同我


def test_liuqin_shun_wuxing_cycle():
    # 木宫自查一圈
    assert assign_liuqin("木", "木") == "兄弟"
    assert assign_liuqin("木", "火") == "子孙"   # 木生火
    assert assign_liuqin("木", "土") == "妻财"   # 木克土
    assert assign_liuqin("木", "金") == "官鬼"   # 金克木
    assert assign_liuqin("木", "水") == "父母"   # 水生木


# ---------------------------------------------------------------------------
# 6. 六神安起
# ---------------------------------------------------------------------------

def test_liushen_jia_yi_day():
    assert assign_liushen("甲", 1) == "青龙"
    assert assign_liushen("乙", 1) == "青龙"
    # 甲乙日上爻为玄武
    assert assign_liushen("甲", 6) == "玄武"
    assert assign_liushen("乙", 6) == "玄武"


def test_liushen_start_positions():
    assert assign_liushen("丙", 1) == "朱雀"
    assert assign_liushen("丁", 1) == "朱雀"
    assert assign_liushen("戊", 1) == "勾陈"
    assert assign_liushen("己", 1) == "螣蛇"
    assert assign_liushen("庚", 1) == "白虎"
    assert assign_liushen("辛", 1) == "白虎"
    assert assign_liushen("壬", 1) == "玄武"
    assert assign_liushen("癸", 1) == "玄武"


def test_liushen_cycle_order():
    # 甲乙日六爻自上而下应严格按六神顺序
    got = [assign_liushen("甲", i) for i in range(1, 7)]
    assert got == LIUSHEN_ORDER == ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]


# ---------------------------------------------------------------------------
# 7. 综合：天风姤（乾宫一世）
# ---------------------------------------------------------------------------

def test_tianfeng_gou_integration():
    # 天风姤 = 上乾下巽 = [初,二,三,四,五,上] = [0,1,1,1,1,1]
    binary = [0, 1, 1, 1, 1, 1]
    assert find_palace_of_binary(binary) == "乾宫"
    assert PALACE_WX["乾宫"] == "金"

    expect = [
        # (pos, gan, zhi, wx, liuqin)
        (1, "甲", "子", "水", "子孙"),
        (2, "甲", "寅", "木", "妻财"),
        (3, "甲", "辰", "土", "父母"),
        (4, "壬", "午", "火", "官鬼"),
        (5, "壬", "申", "金", "兄弟"),
        (6, "壬", "戌", "土", "父母"),
    ]
    for pos, gan, zhi, wx, lq in expect:
        g, z = najia_for_palace("乾宫", pos)
        assert g == gan and z == zhi, (pos, g, z)
        assert zhi_to_wx(zhi) == wx
        assert assign_liuqin("金", wx) == lq


# ---------------------------------------------------------------------------
# 8. 变爻纳支
# ---------------------------------------------------------------------------

def test_bian_zhi_kun_first_line_laoyin():
    # 坤为地初爻老阴(6)动 -> 变地雷复(坤宫一世)
    # 变卦初爻地支 = 坤宫内卦初爻 = 未
    bian_binary = [1, 0, 0, 0, 0, 0]
    assert find_palace_of_binary(bian_binary) == "坤宫"
    assert bian_zhi_for_yao("坤宫", 1, bian_binary) == "未"


def test_bian_zhi_cross_palace():
    # 乾为天上爻老阳(9)动 -> 变泽天夬(坤宫五世)
    # 变卦上爻地支 = 坤宫外卦三爻 = 酉（跨宫：乾 -> 坤）
    bian_binary = [1, 1, 1, 1, 1, 0]
    assert find_palace_of_binary(bian_binary) == "坤宫"
    assert bian_zhi_for_yao("乾宫", 6, bian_binary) == "酉"


def test_zhi_wx_table():
    assert ZHI_WX["子"] == "水"
    assert zhi_to_wx("申") == "金"
    assert zhi_to_wx("卯") == "木"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
