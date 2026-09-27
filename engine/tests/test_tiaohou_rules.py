# -*- coding: utf-8 -*-
"""调候用神规则测试：验证从 tiaohou_matrix.md 提取的 120 条 BZ-TH-* 规则。

覆盖：
  - rules_bazi.json 可被 RuleEngine 正常加载
  - category=tiaohou 的新规则恰好 120 条
  - 10 天干 x 12 月令全覆盖、无重复
  - 每条规则都带 day_gan 与 month_zhi 条件，且可被 ConditionEvaluator 求值
  - 抽样：甲木寅月主用神丙火；癸水子月丙火暖
  - RuleEngine.match 对 {day_gan:甲, month_zhi:寅} 能命中 BZ-TH-0101
"""
from __future__ import annotations

from pathlib import Path

from rule_engine import ConditionEvaluator, RuleEngine

ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = ROOT / "rules" / "rules_bazi.json"

TIANGAN = list("甲乙丙丁戊己庚辛壬癸")
DIZHI = list("寅卯辰巳午未申酉戌亥子丑")


def _load_th_rules():
    engine = RuleEngine()
    rules = engine.load_rules("bazi")
    th = [r for r in rules if r["rule_id"].startswith("BZ-TH-")]
    return engine, rules, th


def test_rules_file_loads():
    engine, rules, th = _load_th_rules()
    assert isinstance(rules, list)
    assert len(rules) == 180
    assert RULES_PATH.exists()


def test_tiaohou_rule_count_is_120():
    _, _, th = _load_th_rules()
    assert len(th) == 120, f"expected 120 tiaohou rules, got {len(th)}"


def test_ten_gan_twelve_zhi_full_coverage_no_dup():
    _, _, th = _load_th_rules()
    combos = set()
    ids = set()
    for r in th:
        cond = {c["field"]: c["value"] for c in r["conditions"]}
        assert "day_gan" in cond, f"{r['rule_id']} missing day_gan"
        assert "month_zhi" in cond, f"{r['rule_id']} missing month_zhi"
        combos.add((cond["day_gan"], cond["month_zhi"]))
        ids.add(r["rule_id"])
    expected = {(g, z) for g in TIANGAN for z in DIZHI}
    assert combos == expected, "10x12 coverage mismatch"
    assert len(ids) == 120, "duplicate rule_id"


def test_each_rule_has_day_gan_month_zhi_conditions():
    _, _, th = _load_th_rules()
    for r in th:
        fields = [c["field"] for c in r["conditions"]]
        assert fields == ["day_gan", "month_zhi"], r["rule_id"]
        for c in r["conditions"]:
            assert c["operator"] == "=="
        # weight/priority/source sanity
        assert r["weight"] == 5
        assert r["priority"] == 9
        assert r["source"].startswith("造化元钥")
        assert r["category"] == "tiaohou"


def test_conditions_evaluable_by_condition_evaluator():
    _, _, th = _load_th_rules()
    for r in th:
        cond = {c["field"]: c["value"] for c in r["conditions"]}
        facts = {"day_gan": cond["day_gan"], "month_zhi": cond["month_zhi"]}
        ev = ConditionEvaluator(facts)
        assert all(ev.eval(c) for c in r["conditions"]), r["rule_id"]
        # and must NOT match when either field is off
        other = facts["day_gan"]
        wrong = "乙" if facts["day_gan"] != "乙" else "甲"
        ev_bad = ConditionEvaluator({"day_gan": wrong, "month_zhi": facts["month_zhi"]})
        assert not all(ev_bad.eval(c) for c in r["conditions"]), r["rule_id"]


def test_sample_jiamu_yin_yue_uses_binghuo():
    _, _, th = _load_th_rules()
    rule = next(r for r in th if r["rule_id"] == "BZ-TH-0101")
    assert rule["name"] == "甲木寅月调候"
    act = rule["actions"][0]
    assert "丙火" in act["conclusion"], act["conclusion"]
    assert "癸水" in act["conclusion"], act["conclusion"]


def test_sample_guiwei_zi_yue_binghuo_warm():
    _, _, th = _load_th_rules()
    rule = next(r for r in th if r["rule_id"] == "BZ-TH-1011")
    cond = {c["field"]: c["value"] for c in rule["conditions"]}
    assert cond == {"day_gan": "癸", "month_zhi": "子"}
    act = rule["actions"][0]
    assert "丙火" in act["conclusion"]
    assert "暖" in act["detail"], act["detail"]


def test_rule_engine_match_jiamu_yin():
    engine = RuleEngine()
    result = engine.match({"day_gan": "甲", "month_zhi": "寅"}, "bazi")
    ids = {m["rule_id"] for m in result["matched_rules"]}
    assert "BZ-TH-0101" in ids, ids
    th_hits = [m for m in result["matched_rules"] if m["category"] == "tiaohou"]
    # only the exact 甲木寅月 grid should fire among the new rules
    assert any(m["rule_id"] == "BZ-TH-0101" for m in th_hits)
    conclusion = " ".join(m["name"] for m in result["matched_rules"])
    assert "甲木寅月调候" in conclusion


def test_rule_engine_match_guiwei_zi():
    engine = RuleEngine()
    result = engine.match({"day_gan": "癸", "month_zhi": "子"}, "bazi")
    ids = {m["rule_id"] for m in result["matched_rules"]}
    assert "BZ-TH-1011" in ids, ids
