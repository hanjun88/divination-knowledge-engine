"""B3 旺衰 / 旬空 / 月破 / 日冲 / 入墓 / 伏神 单元测试。"""
from __future__ import annotations

from liuyao import Yao
from liuyao.wangshuai import (
    PURE_GUA_ZHI,
    PALACE_WX,
    ZHI_WX,
    assign_liuqin,
    check_ri_chong,
    check_ri_sheng,
    check_ru_mu,
    check_xun_kong,
    check_yue_po,
    compute_wangshuai,
    find_fushen,
    get_xun_shou,
)


def _yao(pos: int, zhi: str, wx: str, liuqin: str) -> Yao:
    return Yao(
        pos=pos,
        value=7,
        is_yang=True,
        is_dong=False,
        zhi=zhi,
        wx=wx,
        liuqin=liuqin,
    )


# ---------------------------------------------------------------------------
# 1. 旺衰评分
# ---------------------------------------------------------------------------

def test_lin_yue():
    """临月建: 爻=申(金), 月建=申 → +3.0, lin_yue=True。"""
    # 日辰取卯(木), 对金不生不克不泄, 隔离临月建贡献
    r = compute_wangshuai("金", "申", "卯", yao_zhi="申")
    assert r["lin_yue"] is True
    assert r["score"] == 3.0
    # 3.0 落在 [2.0, 4.0) → 相
    assert r["label"] == "相"


def test_lin_yue_then_wang_with_day_sheng():
    """临月建 + 日辰生 → 旺。爻=申(金), 月=申, 日=辰(土生金)。"""
    r = compute_wangshuai("金", "申", "辰", yao_zhi="申")
    assert r["lin_yue"] is True
    assert r["ri_sheng"] is True  # 土生金
    assert r["score"] == 3.0 + 1.5
    assert r["label"] == "旺"


def test_yue_sheng():
    """月建生爻: 爻=木(寅), 月建=水(子) → 月生 +1.5。"""
    r = compute_wangshuai("木", "子", "卯", yao_zhi="寅")
    assert r["yue_sheng"] is True
    assert r["yue_ke"] is False
    assert r["score"] == 1.5


def test_yue_ke_qiu():
    """月建克爻: 爻=木(寅), 月建=金(申) → 月克 -2.0 → 囚。"""
    r = compute_wangshuai("木", "申", "卯", yao_zhi="寅")
    assert r["yue_ke"] is True
    assert r["score"] == -2.0
    assert r["label"] == "囚"


def test_ri_sheng():
    """日辰生爻: 爻=火(午), 日辰=木(寅) → 日生 +1.5。

    月建取酉(金), 金对火不生不克不泄, 隔离日辰贡献。
    """
    r = compute_wangshuai("火", "酉", "寅", yao_zhi="午")
    assert r["ri_sheng"] is True
    assert r["score"] == 1.5


def test_ri_ke():
    """日辰克爻: 爻=金(申), 日辰=火(午) → 日克 -1.5。"""
    r = compute_wangshuai("金", "卯", "午", yao_zhi="申")
    assert r["ri_ke"] is True
    assert r["score"] == -1.5


def test_xie_yue_and_xie_ri():
    """爻生月建/日辰(泄气): 爻=金(申), 月=水(子), 日=水(子) → 各 -0.5。"""
    r = compute_wangshuai("金", "子", "子", yao_zhi="申")
    # 金生水 → 爻生月建、爻生日辰
    assert r["xie_yue"] is True
    assert r["xie_ri"] is True
    assert r["score"] == -1.0


# ---------------------------------------------------------------------------
# 标签阈值边界
# ---------------------------------------------------------------------------

def test_label_boundaries():
    from liuyao.wangshuai import _label_for_score

    assert _label_for_score(4.0) == "旺"
    assert _label_for_score(3.99) == "相"
    assert _label_for_score(2.0) == "相"
    assert _label_for_score(1.99) == "平"
    assert _label_for_score(-1.0) == "平"
    assert _label_for_score(-1.01) == "囚"
    assert _label_for_score(-3.0) == "囚"
    assert _label_for_score(-3.01) == "死"


# ---------------------------------------------------------------------------
# 2. 旬空
# ---------------------------------------------------------------------------

def test_get_xun_shou():
    assert get_xun_shou("甲", "子") == "甲子"
    assert get_xun_shou("甲", "戌") == "甲戌"
    assert get_xun_shou("甲", "申") == "甲申"
    assert get_xun_shou("甲", "午") == "甲午"
    assert get_xun_shou("甲", "辰") == "甲辰"
    assert get_xun_shou("甲", "寅") == "甲寅"
    # 癸酉日属甲子旬
    assert get_xun_shou("癸", "酉") == "甲子"


def test_xun_kong_jiazi():
    """甲子日, 戌亥为空; 子丑不为空。"""
    assert check_xun_kong("甲子", "戌") is True
    assert check_xun_kong("甲子", "亥") is True
    assert check_xun_kong("甲子", "子") is False
    assert check_xun_kong("甲子", "丑") is False
    assert check_xun_kong("甲子", "寅") is False


def test_xun_kong_other_xun():
    assert check_xun_kong("甲戌", "申") is True
    assert check_xun_kong("甲申", "午") is True
    assert check_xun_kong("甲午", "辰") is True
    assert check_xun_kong("甲辰", "寅") is True
    assert check_xun_kong("甲寅", "子") is True


# ---------------------------------------------------------------------------
# 3. 月破 / 日冲 / 日生 / 入墓
# ---------------------------------------------------------------------------

def test_yue_po():
    assert check_yue_po("子", "午") is True
    assert check_yue_po("午", "子") is True
    assert check_yue_po("子", "子") is False
    assert check_yue_po("申", "寅") is True


def test_ri_chong():
    assert check_ri_chong("子", "午") is True
    assert check_ri_chong("卯", "酉") is True
    assert check_ri_chong("子", "丑") is False


def test_ri_sheng_helper():
    # 日辰寅(木) 生火爻
    assert check_ri_sheng("寅", "火") is True
    # 日辰午(火) 不生金爻
    assert check_ri_sheng("午", "金") is False


def test_ru_mu():
    """入墓: 金墓丑, 木墓未, 水墓辰, 火墓戌, 土墓辰。"""
    assert check_ru_mu("金", "丑") is True
    assert check_ru_mu("金", "未") is False
    assert check_ru_mu("木", "未") is True
    assert check_ru_mu("水", "辰") is True
    assert check_ru_mu("火", "戌") is True
    assert check_ru_mu("土", "辰") is True


# ---------------------------------------------------------------------------
# 4. 六亲装配 (辅助)
# ---------------------------------------------------------------------------

def test_assign_liuqin():
    # 乾宫金
    assert assign_liuqin("金", "金") == "兄弟"   # 同我
    assert assign_liuqin("金", "水") == "子孙"   # 我生
    assert assign_liuqin("金", "木") == "妻财"    # 我克
    assert assign_liuqin("金", "土") == "父母"    # 生我
    assert assign_liuqin("金", "火") == "官鬼"    # 克我


# ---------------------------------------------------------------------------
# 5. 伏神查找
# ---------------------------------------------------------------------------

def _qian_pure_yaos_no_qicai() -> list:
    """构造乾宫某卦, 六爻均无妻财。

    乾宫纯卦纳支: [子,寅,辰,午,申,戌], 六亲依次:
      子水->子孙, 寅木->妻财, 辰土->父母,
      午火->官鬼, 申金->兄弟, 戌土->父母
    这里把 pos2 的飞神换成申金(兄弟), 使卦中不现妻财。
    """
    return [
        _yao(1, "子", "水", "子孙"),
        _yao(2, "申", "金", "兄弟"),   # 飞神位 (原纯卦应为寅木妻财)
        _yao(3, "辰", "土", "父母"),
        _yao(4, "午", "火", "官鬼"),
        _yao(5, "申", "金", "兄弟"),
        _yao(6, "戌", "土", "父母"),
    ]


def test_find_fushen_when_yongshen_missing():
    yaos = _qian_pure_yaos_no_qicai()
    fs = find_fushen(yaos, "乾宫", "妻财")
    assert fs is not None
    # 乾宫纯卦妻财在 pos2 寅木
    assert fs["pos"] == 2
    assert fs["zhi"] == "寅"
    assert fs["wx"] == "木"
    assert fs["liuqin"] == "妻财"
    assert fs["fei_pos"] == 2
    assert fs["fei_zhi"] == "申"
    # 飞神申金 克 伏神寅木
    assert fs["fei_ke_fu"] is True
    assert fs["fei_sheng_fu"] is False


def test_find_fushen_returns_none_when_yongshen_present():
    yaos = _qian_pure_yaos_no_qicai()
    # 把 pos4 官鬼改成妻财, 使妻财已现
    yaos[3] = _yao(4, "寅", "木", "妻财")
    assert find_fushen(yaos, "乾宫", "妻财") is None


def test_pure_gua_table_consistency():
    """本宫纯卦六支的六亲应覆盖全部五种六亲(八纯卦)。"""
    for palace, zhis in PURE_GUA_ZHI.items():
        pw = PALACE_WX[palace]
        liuqins = {assign_liuqin(pw, ZHI_WX[z]) for z in zhis}
        # 八纯卦六亲齐全
        assert liuqins == {"兄弟", "父母", "子孙", "妻财", "官鬼"}, palace
