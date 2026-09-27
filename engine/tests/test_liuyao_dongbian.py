"""B4 动变力学 / 16应期法则 / 标准化AST 单元测试。"""
from __future__ import annotations

from liuyao import CastResult, HexagramInfo, Yao
from liuyao.dongbian import (
    analyze_dongbian,
    build_ast,
    compute_yingqi,
)
from liuyao.najia import zhi_to_wx
from rule_engine import RuleEngine


# ---------------------------------------------------------------------------
# 工具构造
# ---------------------------------------------------------------------------

def _dong_yao(pos: int, zhi: str, bian_zhi: str, value: int = 9) -> Yao:
    """构造一个动爻 (默认老阳 9 变阴)。"""
    return Yao(
        pos=pos,
        value=value,
        is_yang=value in (7, 9),
        is_dong=True,
        zhi=zhi,
        wx=zhi_to_wx(zhi),
        bian_zhi=bian_zhi,
        bian_wx=zhi_to_wx(bian_zhi),
    )


def _jing_yao(pos: int, zhi: str, **flags) -> Yao:
    y = Yao(
        pos=pos, value=7, is_yang=True, is_dong=False,
        zhi=zhi, wx=zhi_to_wx(zhi), liuqin="兄弟",
    )
    for k, v in flags.items():
        setattr(y, k, v)
    return y


def _six_yaos(yong: Yao) -> list:
    """以 yong 为 pos=3 的用神, 补全其余五爻静爻。"""
    zhis = ["子", "寅", None, "辰", "午", "申"]
    yaos = []
    for pos in range(1, 7):
        if pos == yong.pos:
            yaos.append(yong)
        else:
            yaos.append(_jing_yao(pos, zhis[pos - 1]))
    return yaos


# ---------------------------------------------------------------------------
# 1. 动变力学分析 (6 种变化)
# ---------------------------------------------------------------------------

def test_huitou_sheng():
    """回头生: 动爻子水(水)变申金(金) -> 金生水 = 回头生, +2.5。"""
    y = _dong_yao(1, "子", "申")
    r = analyze_dongbian(y, "寅", "卯")
    assert r["type"] == "回头生"
    assert r["score"] == 2.5
    assert y.dongbian_type == "回头生"


def test_huitou_ke():
    """回头克: 动爻寅木变申金 -> 金克木 = 回头克, -3.0。"""
    y = _dong_yao(2, "寅", "申")
    r = analyze_dongbian(y, "寅", "卯")
    assert r["type"] == "回头克"
    assert r["score"] == -3.0


def test_hua_jin():
    """化进神: 动爻寅木变卯木 -> 同五行且帝旺方向, +1.5。"""
    y = _dong_yao(3, "寅", "卯")
    r = analyze_dongbian(y, "寅", "卯")
    assert r["type"] == "化进"
    assert r["score"] == 1.5


def test_hua_tui():
    """化退神: 动爻卯木变寅木 -> -1.5。"""
    y = _dong_yao(3, "卯", "寅")
    r = analyze_dongbian(y, "寅", "卯")
    assert r["type"] == "化退"
    assert r["score"] == -1.5


def test_hua_jue():
    """化绝: 动爻申金(金)变寅木 -> 金绝寅 = 化绝, -2.0。"""
    y = _dong_yao(4, "申", "寅")
    r = analyze_dongbian(y, "寅", "卯")
    assert r["type"] == "化绝"
    assert r["score"] == -2.0


def test_hua_kong():
    """化空: 动爻申金变亥水, 甲子旬空戌亥 -> 变爻亥水旬空, -1.0。"""
    y = _dong_yao(5, "申", "亥")
    r = analyze_dongbian(y, "寅", "卯", day_xun="甲子")
    assert r["type"] == "化空"
    assert r["score"] == -1.0


def test_hua_mu():
    """化墓: 动爻寅木变未土 -> 木墓未, -1.0。"""
    y = _dong_yao(5, "寅", "未")
    r = analyze_dongbian(y, "寅", "卯")
    assert r["type"] == "化墓"
    assert r["score"] == -1.0


def test_combined_huitou_sheng_jia_hua_kong():
    """回头生 + 化空: 动爻寅木变亥水(水生木=回头生), 甲子旬空亥 -> 累计 +2.5-1.0=1.5, 主要类型回头生。"""
    y = _dong_yao(2, "寅", "亥")
    r = analyze_dongbian(y, "寅", "卯", day_xun="甲子")
    assert r["type"] == "回头生"
    assert r["score"] == 1.5
    effects = {e["effect"]: e["score"] for e in r["all_effects"]}
    assert effects == {"回头生": 2.5, "化空": -1.0}


def test_static_yao_no_dongbian():
    """静爻: type=无, score=0。"""
    y = _jing_yao(1, "子")
    r = analyze_dongbian(y, "寅", "卯")
    assert r["type"] == "无"
    assert r["score"] == 0.0


# ---------------------------------------------------------------------------
# 2. 应期法则状态机
# ---------------------------------------------------------------------------

def test_yingqi_an_jing():
    """用神安静: 用神子水安静 -> 逢冲(午)为应期。"""
    yong = _jing_yao(3, "子")
    yaos = _six_yaos(yong)
    r = compute_yingqi(yaos, 3, month_zhi="卯", day_zhi="巳")
    assert r["primary_window"] == "午"
    assert "安静" in r["method"]
    assert r["timing_hint"]


def test_yingqi_dong():
    """用神发动: 用神发动 -> 逢合(子丑合)为应期。"""
    yong = _dong_yao(3, "子", "申")
    yaos = _six_yaos(yong)
    r = compute_yingqi(yaos, 3, month_zhi="卯", day_zhi="巳")
    assert r["primary_window"] == "丑"
    assert "发动" in r["method"]


def test_yingqi_xun_kong():
    """用神旬空: 用神旬空 -> 出空(填实=子)为应期, 次要=冲实(午)。"""
    yong = _jing_yao(3, "子", xun_kong=True)
    yaos = _six_yaos(yong)
    r = compute_yingqi(yaos, 3, month_zhi="卯", day_zhi="巳", day_xun="甲寅")
    assert r["primary_window"] == "子"
    assert "午" in r["secondary_windows"]
    assert "旬空" in r["method"]


def test_yingqi_yue_po():
    """用神月破: 用神午火月破(子月) -> 破而逢合(午未合=未)。"""
    yong = _jing_yao(3, "午", yue_po=True)
    yaos = _six_yaos(yong)
    r = compute_yingqi(yaos, 3, month_zhi="子", day_zhi="巳")
    assert r["primary_window"] == "未"
    assert "月破" in r["method"]


def test_yingqi_huitou_ke():
    """用神回头克: 变爻申金克用神 -> 克神受制(冲申=寅)为应期。"""
    yong = _dong_yao(3, "寅", "申")
    yong.dongbian_type = "回头克"
    yaos = _six_yaos(yong)
    r = compute_yingqi(yaos, 3, month_zhi="卯", day_zhi="巳")
    assert r["primary_window"] == "寅"
    assert "回头克" in r["method"]


# ---------------------------------------------------------------------------
# 3. 标准化 AST 输出
# ---------------------------------------------------------------------------

def _build_sample_cast() -> CastResult:
    """构造一个完整的 CastResult 样本。"""
    yaos = [
        Yao(pos=1, value=7, is_yang=True, is_dong=False, gan="戊", zhi="寅",
            wx="木", liuqin="子孙", liushen="青龙", wangshuai_score=1.5,
            wangshuai_label="相"),
        Yao(pos=2, value=9, is_yang=True, is_dong=True, gan="戊", zhi="辰",
            wx="土", liuqin="兄弟", liushen="朱雀", wangshuai_score=0.0,
            wangshuai_label="平", bian_zhi="卯", bian_wx="木", bian_liuqin="妻财",
            dongbian_type="化退", dongbian_score=-1.5),
        Yao(pos=3, value=7, is_yang=True, is_dong=False, gan="戊", zhi="午",
            wx="火", liuqin="妻财", liushen="勾陈", wangshuai_score=3.0,
            wangshuai_label="旺"),
        Yao(pos=4, value=8, is_yang=False, is_dong=False, gan="丙", zhi="申",
            wx="金", liuqin="官鬼", liushen="螣蛇", wangshuai_score=-1.5,
            wangshuai_label="囚"),
        Yao(pos=5, value=7, is_yang=True, is_dong=False, gan="丙", zhi="戌",
            wx="土", liuqin="兄弟", liushen="白虎", wangshuai_score=0.0,
            wangshuai_label="平"),
        Yao(pos=6, value=8, is_yang=False, is_dong=False, gan="丙", zhi="子",
            wx="水", liuqin="父母", liushen="玄武", wangshuai_score=1.5,
            wangshuai_label="相", ri_chong=True),
    ]
    hx = HexagramInfo(
        ben_gua_name="水天需", ben_gua_id=5,
        bian_gua_name="水地比", bian_gua_id=8,
        palace="坤宫", palace_wx="土",
        shi_pos=5, ying_pos=2, shi_type="四世",
    )
    return CastResult(
        input_values=[7, 9, 7, 8, 7, 8],
        datetime="2026-09-27T12:00:00+07:00",
        month_gan="甲", month_zhi="寅",
        day_gan="丙", day_zhi="申", day_xun="甲子",
        hexagram=hx, yaos=yaos, fushen=None,
        yong_shen_pos=3,
    )


def test_build_ast_structure():
    """build_ast 输出包含所有必要顶层字段。"""
    ast = build_ast(_build_sample_cast())

    for key in ("meta", "hexagram", "time", "yaos", "fushen",
                "yong_shen", "ying_qi", "summary", "rule_facts"):
        assert key in ast, f"缺少顶层字段 {key}"

    assert ast["meta"]["engine"] == "liuyao-najia-core"
    assert ast["meta"]["input_values"] == [7, 9, 7, 8, 7, 8]
    assert ast["hexagram"]["ben_gua"] == "水天需"
    assert ast["hexagram"]["palace_wx"] == "土"
    assert ast["time"]["month_wx"] == "木"   # 寅=木
    assert ast["time"]["day_wx"] == "金"     # 申=金
    assert len(ast["yaos"]) == 6

    y1 = ast["yaos"][0]
    for f in ("pos", "value", "is_yang", "is_dong", "gan", "zhi", "wx",
              "liuqin", "liushen", "wangshuai_score", "wangshuai_label",
              "xun_kong", "yue_po", "ri_chong", "dongbian_type",
              "dongbian_score", "bian_zhi", "bian_wx", "bian_liuqin"):
        assert f in y1, f"爻字段缺少 {f}"

    assert ast["yong_shen"]["pos"] == 3
    assert ast["yong_shen"]["zhi"] == "午"
    assert ast["summary"]["dong_count"] == 1
    assert ast["summary"]["daxiang"] in ("吉", "凶", "平")
    assert ast["ying_qi"]["primary_window"]


def test_build_ast_rule_facts_accepted_by_engine():
    """rule_facts 可直接传给 RuleEngine.match() 不报错。"""
    ast = build_ast(_build_sample_cast())
    rf = ast["rule_facts"]

    # 关键字段对齐 LiuyaoInput
    assert rf["month_zh"] == "寅"
    assert rf["day_zh"] == "申"
    assert rf["month_wx"] == "木"
    assert rf["day_wx"] == "金"
    assert rf["day_xun"] == "甲子"
    assert rf["yong_shen"]["zhi"] == "午"
    assert rf["yong_shen"]["wangshuai"] == "旺"
    assert rf["hua_tui_shen"] is True
    assert rf["dong_count"] == 1

    engine = RuleEngine()
    result = engine.match(rf, "liuyao")
    assert set(result.keys()) >= {"matched_rules", "conclusions",
                                  "total_weight", "matched_count"}
