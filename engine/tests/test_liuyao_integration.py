# -*- coding: utf-8 -*-
"""端到端集成测试: liuyao.cast 串联 B1~B4 完整排盘管线 + 规则引擎对接。

运行:
    cd engine && PYTHONPATH=. python -m pytest tests/test_liuyao_integration.py -v
"""
from __future__ import annotations

from liuyao import Yao
from liuyao.cast import cast, cast_to_ast, determine_yong_shen
from liuyao.wangshuai import find_fushen
from rule_engine import RuleEngine


# 固定时间: 庚申月 甲子日 (月建=申, 日辰=子)
MG, MZ = "庚", "申"
DG, DZ = "甲", "子"


def _basic():
    return cast([7, 8, 9, 6, 7, 8], MG, MZ, DG, DZ,
                yong_shen_liuqin="妻财", datetime_str="2026-09-27T12:00:00")


# ---------------------------------------------------------------------------
# 1. 完整排盘
# ---------------------------------------------------------------------------
def test_full_cast_hexagram_names():
    r = _basic()
    h = r.hexagram
    assert h.ben_gua_name == "水火既济"
    assert h.bian_gua_name == "泽雷随"          # 有动爻 -> 变卦 != 本卦
    assert h.ben_gua_id == 63
    assert h.bian_gua_id == 17


def test_full_cast_palace_and_shiying():
    r = _basic()
    h = r.hexagram
    assert h.palace == "坎宫"
    assert h.palace_wx == "水"
    assert h.shi_pos == 3
    assert h.ying_pos == 6
    assert h.shi_type == "三世"


def test_full_cast_six_lines_najia_liushen_liuqin():
    r = _basic()
    assert len(r.yaos) == 6
    for y in r.yaos:
        assert y.gan, f"pos{y.pos} 缺天干"
        assert y.zhi, f"pos{y.pos} 缺地支"
        assert y.liuqin in ("父母", "兄弟", "子孙", "妻财", "官鬼"), y.liuqin
        assert y.liushen in ("青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武")


def test_full_cast_dong_lines_have_bian_info():
    r = _basic()
    dong = [y for y in r.yaos if y.is_dong]
    assert {y.pos for y in dong} == {3, 4}     # 9=老阳(pos3), 6=老阴(pos4)
    for y in dong:
        assert y.bian_zhi, f"动爻 pos{y.pos} 缺变爻地支"
        assert y.bian_wx
        assert y.bian_liuqin


def test_full_cast_wangshuai_computed():
    r = _basic()
    for y in r.yaos:
        assert isinstance(y.wangshuai_score, float)
        assert y.wangshuai_label in ("旺", "相", "平", "囚", "死")
    # 临日辰(子)的上爻 pos6=戊子水 应为旺; 临月建(申)的 pos4=戊申金 应为相
    by_pos = {y.pos: y for y in r.yaos}
    assert by_pos[6].wangshuai_label == "旺"
    assert by_pos[4].wangshuai_label == "相"


def test_full_cast_yong_shen_and_yingqi():
    r = _basic()
    # 妻财首现于 pos3 (戊午火)
    assert r.yong_shen_pos == 3
    assert r.fushen is None
    assert r.ying_qi["method"]
    assert "primary_window" in r.ying_qi


def test_full_cast_dongbian_mechanics():
    r = _basic()
    by_pos = {y.pos: y for y in r.yaos}
    # pos4 戊申金 动 -> 变午火; 火克金 = 回头克
    assert by_pos[4].dongbian_type == "回头克"
    assert by_pos[4].dongbian_score < 0


# ---------------------------------------------------------------------------
# 2. 乾为天全静
# ---------------------------------------------------------------------------
def test_qian_all_quiet():
    r = cast([7, 7, 7, 7, 7, 7], MG, MZ, DG, DZ)
    assert r.hexagram.ben_gua_name == "乾为天"
    assert r.hexagram.bian_gua_name == "乾为天"     # 无动爻 -> 变卦=本卦
    assert all(not y.is_dong for y in r.yaos)
    assert all(not y.bian_zhi for y in r.yaos)


# ---------------------------------------------------------------------------
# 3. AST 输出 + 规则引擎对接
# ---------------------------------------------------------------------------
def test_ast_contains_required_fields():
    ast = cast_to_ast([7, 8, 9, 6, 7, 8], MG, MZ, DG, DZ, "妻财")
    for k in ("meta", "hexagram", "time", "yaos", "fushen",
              "yong_shen", "ying_qi", "summary", "rule_facts"):
        assert k in ast, f"AST 缺字段 {k}"
    assert len(ast["yaos"]) == 6
    assert "lines" in ast["rule_facts"]
    assert ast["rule_facts"]["month_zh"] == "申"
    assert ast["rule_facts"]["day_zh"] == "子"


def test_rule_engine_match_on_ast_facts():
    ast = cast_to_ast([7, 8, 9, 6, 7, 8], MG, MZ, DG, DZ, "妻财")
    engine = RuleEngine()
    result = engine.match(ast["rule_facts"], "liuyao")
    assert set(result) == {"matched_rules", "conclusions",
                           "total_weight", "matched_count"}
    assert isinstance(result["matched_rules"], list)
    assert result["matched_count"] == len(result["matched_rules"])


# ---------------------------------------------------------------------------
# 4. 伏神场景: 本卦无用神 -> find_fushen 从本宫纯卦找伏神
# ---------------------------------------------------------------------------
def test_fushen_lookup_when_yongshen_absent():
    r = _basic()
    palace = r.hexagram.palace
    # 模拟"用神不现": 滤掉本卦所有妻财爻
    filtered = [Yao(pos=y.pos, value=y.value, is_yang=y.is_yang,
                    is_dong=y.is_dong, gan=y.gan, zhi=y.zhi, wx=y.wx,
                    liuqin="兄弟") for y in r.yaos]
    fs = find_fushen(filtered, palace, "妻财")
    assert fs is not None
    assert fs["liuqin"] == "妻财"
    assert fs["zhi"]
    assert fs["wx"]
    assert fs["pos"] >= 1


# ---------------------------------------------------------------------------
# 5. 用神自动判定
# ---------------------------------------------------------------------------
def test_determine_yong_shen_domain_mapping():
    assert determine_yong_shen("财运投资") == "妻财"
    assert determine_yong_shen("事业官运") == "官鬼"
    assert determine_yong_shen("感情婚姻") == "妻财"
    assert determine_yong_shen("学业考试") == "父母"
    assert determine_yong_shen("出行迁移") == "父母"
    assert determine_yong_shen("官司诉讼") == "官鬼"
    assert determine_yong_shen("随便问点别的") == "应爻"
