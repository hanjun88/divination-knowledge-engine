# -*- coding: utf-8 -*-
"""深度规则(deep_distill_v2)固化测试：六爻 LY-D001.. 与 八字 BZ-D001..。

验证：
  1. rules_liuyao.json / rules_bazi.json 可正常加载，新增深度规则数 > 0；
  2. 每条新规则的 conditions 可被 ConditionEvaluator 解析(不抛异常)；
  3. 每条新规则都带 evidence(原文引用 + 来源)；
  4. 现有规则不被破坏(数量只增不减、旧 rule_id 仍在)；
  5. 抽样：构造输入命中某条六爻深度规则与某条八字深度规则。
"""
from __future__ import annotations

import json
from pathlib import Path

from rule_engine import ConditionEvaluator, RuleEngine

RULES_DIR = Path(__file__).resolve().parents[1] / "rules"

LIUYAO_NEW = [f"LY-D{i:03d}" for i in range(1, 111)]   # 110 条
BAZI_NEW = [f"BZ-D{i:03d}" for i in range(1, 115)]     # 114 条


def _load(domain: str):
    with open(RULES_DIR / f"rules_{domain}.json", encoding="utf-8") as f:
        return json.load(f)


def _check_conditions_parseable(rules):
    """对每条规则的每个 condition，用 ConditionEvaluator 跑一遍空 facts，不得抛异常。"""
    ev = ConditionEvaluator({})
    for r in rules:
        conds = r.get("conditions", [])
        assert isinstance(conds, list) and len(conds) > 0, f"{r['rule_id']} 条件为空"
        for c in conds:
            try:
                ev.eval(c)
            except Exception as e:  # pragma: no cover - 失败即报错
                raise AssertionError(f"{r['rule_id']} condition 无法解析: {c!r} -> {e}")


def test_liuyao_deep_rules_loaded():
    data = _load("liuyao")
    ids = {r["rule_id"] for r in data["rules"]}
    present = [rid for rid in LIUYAO_NEW if rid in ids]
    assert len(present) >= 110, f"六爻深度规则缺失: {len(present)}/110"
    # count 字段与实际一致
    assert data["count"] == len(data["rules"])
    # 旧规则仍在
    assert "LY-M01" in ids and "LY-U03" in ids


def test_bazi_deep_rules_loaded():
    data = _load("bazi")
    ids = {r["rule_id"] for r in data["rules"]}
    present = [rid for rid in BAZI_NEW if rid in ids]
    assert len(present) >= 114, f"八字深度规则缺失: {len(present)}/114"
    assert data["count"] == len(data["rules"])
    # 旧规则(含任务C调候)仍在
    assert "BZ-D01" in ids and "BZ-TH-0101" in ids


def test_new_rules_have_evidence():
    for domain, new_ids in (("liuyao", LIUYAO_NEW), ("bazi", BAZI_NEW)):
        data = _load(domain)
        by_id = {r["rule_id"]: r for r in data["rules"]}
        for rid in new_ids:
            r = by_id.get(rid)
            assert r is not None, f"{rid} 缺失"
            evd = r.get("evidence")
            assert isinstance(evd, dict), f"{rid} evidence 非对象"
            assert evd.get("quote"), f"{rid} evidence.quote 为空"
            assert evd.get("source_url") or evd.get("book"), f"{rid} evidence 缺来源"
            assert r.get("source"), f"{rid} 缺 source 字段"


def test_new_rules_conditions_parseable():
    for domain, new_ids in (("liuyao", LIUYAO_NEW), ("bazi", BAZI_NEW)):
        data = _load(domain)
        by_id = {r["rule_id"]: r for r in data["rules"]}
        subset = [by_id[rid] for rid in new_ids if rid in by_id]
        _check_conditions_parseable(subset)


def test_sample_match_liuyao_rule():
    """用神临月建(LY-D011)：month_zh == yong_shen.zhi 应命中。"""
    eng = RuleEngine()
    facts = {
        "month_zh": "寅", "day_zh": "子",
        "month_wx": "木", "day_wx": "水",
        "yong_shen": {"zhi": "寅", "wx": "木", "dong": False,
                      "xun_kong": False, "yue_po": False, "wangshuai": "旺"},
    }
    res = eng.match(facts, "liuyao")
    matched_ids = {m["rule_id"] for m in res["matched_rules"]}
    assert "LY-D011" in matched_ids, f"应命中 LY-D011, 实际命中: {sorted(matched_ids)}"


def test_sample_match_bazi_rule():
    """中和为贵(BZ-D003)：wuxing_zhonghe==True 应命中。"""
    eng = RuleEngine()
    facts = {"wuxing_zhonghe": True, "sizhu_liutong": True, "shun_ni": "顺"}
    res = eng.match(facts, "bazi")
    matched_ids = {m["rule_id"] for m in res["matched_rules"]}
    assert "BZ-D003" in matched_ids, f"应命中 BZ-D003, 实际命中: {sorted(matched_ids)}"
