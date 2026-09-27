"""六爻排盘内核 B1 测试: 成卦算法 + 八宫世应定位."""
import os
import sys

import pytest

# 允许从 engine/ 目录直接运行
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from liuyao.hexagram import (  # noqa: E402
    BINARY_TO_ID,
    HEXAGRAM_NAMES,
    cast_hexagram,
    find_palace_and_shiying,
)


def _gong(values):
    """便捷: 成卦 + 宫位世应 一站式."""
    c = cast_hexagram(values)
    p = find_palace_and_shiying(c["ben_binary"], c["bian_binary"])
    return c, p


# --- 乾宫八卦 (京房八宫一世~归魂序列) ---

def test_qian_pure():
    c, p = _gong([7, 7, 7, 7, 7, 7])
    assert c["ben_id"] == 1
    assert c["ben_name"] == "乾为天"
    assert c["dong_positions"] == []
    assert c["bian_id"] == 1  # 无动爻, 变卦即本卦
    assert p == {"palace": "乾宫", "palace_wx": "金",
                 "shi_pos": 6, "ying_pos": 3, "shi_type": "本宫"}


def test_kun_pure():
    c, p = _gong([8, 8, 8, 8, 8, 8])
    assert c["ben_id"] == 2
    assert c["ben_name"] == "坤为地"
    assert p["palace"] == "坤宫"
    assert p["palace_wx"] == "土"
    assert p["shi_pos"] == 6
    assert p["ying_pos"] == 3
    assert p["shi_type"] == "本宫"


def test_gou_yi_shi():
    # 天风姤 44, 乾宫一世
    c, p = _gong([8, 7, 7, 7, 7, 7])
    assert c["ben_id"] == 44
    assert c["ben_name"] == "天风姤"
    assert p["palace"] == "乾宫"
    assert p["shi_type"] == "一世"
    assert p["shi_pos"] == 1
    assert p["ying_pos"] == 4


def test_dun_er_shi():
    # 天山遁 33, 乾宫二世
    c, p = _gong([8, 8, 7, 7, 7, 7])
    assert c["ben_id"] == 33
    assert c["ben_name"] == "天山遁"
    assert p["palace"] == "乾宫"
    assert p["shi_type"] == "二世"
    assert p["shi_pos"] == 2
    assert p["ying_pos"] == 5


def test_pi_san_shi():
    # 天地否 12, 乾宫三世
    c, p = _gong([8, 8, 8, 7, 7, 7])
    assert c["ben_id"] == 12
    assert c["ben_name"] == "天地否"
    assert p["palace"] == "乾宫"
    assert p["shi_type"] == "三世"
    assert p["shi_pos"] == 3
    assert p["ying_pos"] == 6


def test_guan_si_shi():
    # 风地观 20, 乾宫四世
    c, p = _gong([8, 8, 8, 8, 7, 7])
    assert c["ben_id"] == 20
    assert c["ben_name"] == "风地观"
    assert p["palace"] == "乾宫"
    assert p["shi_type"] == "四世"
    assert p["shi_pos"] == 4
    assert p["ying_pos"] == 1


def test_bo_wu_shi():
    # 山地剥 23, 乾宫五世
    c, p = _gong([8, 8, 8, 8, 8, 7])
    assert c["ben_id"] == 23
    assert c["ben_name"] == "山地剥"
    assert p["palace"] == "乾宫"
    assert p["shi_type"] == "五世"
    assert p["shi_pos"] == 5
    assert p["ying_pos"] == 2


def test_jin_you_hun():
    # 火地晋 35, 乾宫游魂
    c, p = _gong([8, 8, 8, 7, 8, 7])
    assert c["ben_id"] == 35
    assert c["ben_name"] == "火地晋"
    assert p["palace"] == "乾宫"
    assert p["shi_type"] == "游魂"
    assert p["shi_pos"] == 4
    assert p["ying_pos"] == 1


def test_dayou_gui_hun():
    # 火天大有 14, 乾宫归魂
    c, p = _gong([7, 7, 7, 7, 8, 7])
    assert c["ben_id"] == 14
    assert c["ben_name"] == "火天大有"
    assert p["palace"] == "乾宫"
    assert p["shi_type"] == "归魂"
    assert p["shi_pos"] == 3
    assert p["ying_pos"] == 6


# --- 动爻变卦 ---

def test_dong_yao_bian_gua():
    # 初爻(老阴6)与四爻(老阳9)动
    c = cast_hexagram([6, 7, 8, 9, 7, 8])
    assert c["dong_positions"] == [1, 4]
    # 本卦: 6阴 7阳 8阴 9阳 7阳 8阴 -> [0,1,0,1,1,0]
    assert c["ben_binary"] == [0, 1, 0, 1, 1, 0]
    # 变卦: 初爻0->1, 四爻1->0 -> [1,1,0,0,1,0]
    assert c["bian_binary"] == [1, 1, 0, 0, 1, 0]
    # 本卦 = 泽水困(47), 变卦 = 水泽节(60)
    assert c["ben_id"] == 47
    assert c["ben_name"] == "泽水困"
    assert c["bian_id"] == 60
    assert c["bian_name"] == "水泽节"


def test_lao_yang_bian_yin_lao_yin_bian_yang():
    # 老阳 9 应变阴, 老阴 6 应变阳
    c = cast_hexagram([9, 9, 9, 9, 9, 9])
    assert c["ben_binary"] == [1, 1, 1, 1, 1, 1]  # 乾
    assert c["bian_binary"] == [0, 0, 0, 0, 0, 0]  # 变坤
    assert c["ben_id"] == 1
    assert c["bian_id"] == 2
    assert c["dong_positions"] == [1, 2, 3, 4, 5, 6]


# --- 64 卦表完整性 ---

def test_hexagram_table_complete():
    assert len(HEXAGRAM_NAMES) == 64
    assert set(HEXAGRAM_NAMES.keys()) == set(range(1, 65))
    # 每个卦序号都能通过 binary 反查回来
    seen = set()
    for hid, name in HEXAGRAM_NAMES.items():
        # 反查: 找到该 id 对应的 binary
        keys = [b for b, h in BINARY_TO_ID.items() if h == hid]
        assert len(keys) == 1, f"卦 {hid}({name}) binary 反查异常: {keys}"
        assert BINARY_TO_ID[keys[0]] == hid
        seen.add(keys[0])
    assert len(BINARY_TO_ID) == 64
    assert len(seen) == 64


def test_known_binary_mapping():
    assert BINARY_TO_ID[(1, 1, 1, 1, 1, 1)] == 1   # 乾
    assert BINARY_TO_ID[(0, 0, 0, 0, 0, 0)] == 2   # 坤
    assert BINARY_TO_ID[(1, 0, 1, 0, 1, 0)] == 63  # 既济
    assert BINARY_TO_ID[(0, 1, 0, 1, 0, 1)] == 64  # 未济


def test_invalid_value_rejected():
    with pytest.raises(ValueError):
        cast_hexagram([7, 7, 7, 7, 7, 5])


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
