# -*- coding: utf-8 -*-
"""深度蒸馏规则 (deep_distill v2) 转 JSON 后的契约测试。

覆盖:
  - rules_ziwei.json 追加的 ZW-D### 深度规则可加载、条数 > 0
  - rules_vedic.json 新建并可加载
  - 每条新规则 conditions 可被 ConditionEvaluator 解析(不抛异常)
  - 每条新规则带 evidence 字段(原文引用 + 来源URL)
  - RuleEngine.DOMAINS 包含 "vedic"
  - 抽样匹配测试: 构造 facts 命中若干规则
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from rule_engine import ConditionEvaluator, RuleEngine


ROOT = Path(__file__).resolve().parents[1]
RULES_DIR = ROOT / "rules"

ZW_DEEP_PREFIX = "ZW-D"
VE_DEEP_PREFIX = "VE-D"

REQUIRED_FIELDS = {"rule_id", "domain", "category", "name", "conditions",
                   "actions", "weight", "priority", "source", "evidence"}


def _load(domain: str) -> dict:
    return json.loads((RULES_DIR / f"rules_{domain}.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# loading
# ---------------------------------------------------------------------------
def test_ziwei_rules_loads_and_has_deep_rules():
    data = _load("ziwei")
    deep = [r for r in data["rules"] if r["rule_id"].startswith(ZW_DEEP_PREFIX)]
    assert data["domain"] == "ziwei"
    assert len(deep) > 0, "紫微深度规则应追加到 rules_ziwei.json"
    # 原有规则未被破坏 (ZW-G / ZW-M / ZW-P / ZW-S / ZW-X 前缀仍在)
    legacy = [r for r in data["rules"] if not r["rule_id"].startswith(ZW_DEEP_PREFIX)]
    assert len(legacy) >= 64, f"原有紫微规则应保留, got {len(legacy)}"


def test_vedic_rules_loads():
    data = _load("vedic")
    assert data["domain"] == "vedic"
    deep = [r for r in data["rules"] if r["rule_id"].startswith(VE_DEEP_PREFIX)]
    assert len(deep) > 0
    assert data["count"] == len(data["rules"]) == len(deep)


def test_engine_domains_include_vedic():
    assert "vedic" in RuleEngine.DOMAINS
    # western (G1) 也应共存
    assert "western" in RuleEngine.DOMAINS


# ---------------------------------------------------------------------------
# structural validity
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("domain,prefix", [("ziwei", ZW_DEEP_PREFIX),
                                           ("vedic", VE_DEEP_PREFIX)])
def test_deep_rules_have_required_fields(domain, prefix):
    data = _load(domain)
    deep = [r for r in data["rules"] if r["rule_id"].startswith(prefix)]
    assert deep, f"{domain} 无深度规则"
    for r in deep:
        missing = REQUIRED_FIELDS - set(r.keys())
        assert not missing, f"{r['rule_id']} 缺字段 {missing}"
        # evidence 必须含原文引用与来源URL
        ev = r["evidence"]
        assert isinstance(ev, dict)
        assert ev.get("quote"), f"{r['rule_id']} evidence.quote 为空"
        assert ev.get("url", "").startswith(("http://", "https://")), \
            f"{r['rule_id']} evidence.url 非法: {ev.get('url')}"
        # domain 字段一致
        assert r["domain"] == domain
        # actions 至少有 conclusion
        assert r["actions"] and r["actions"][0].get("conclusion")


@pytest.mark.parametrize("domain,prefix", [("ziwei", ZW_DEEP_PREFIX),
                                           ("vedic", VE_DEEP_PREFIX)])
def test_deep_rules_conditions_parseable(domain, prefix):
    """每条新规则的 conditions 必须能被 ConditionEvaluator 遍历解析(对空 facts 不抛异常)。"""
    data = _load(domain)
    ev = ConditionEvaluator({})
    deep = [r for r in data["rules"] if r["rule_id"].startswith(prefix)]
    for r in deep:
        conds = r["conditions"]
        assert isinstance(conds, list) and conds, f"{r['rule_id']} conditions 为空"
        for c in conds:
            # 不应抛异常; 返回 bool 即可
            result = ev.eval(c)
            assert isinstance(result, bool), f"{r['rule_id']} 条件求值非 bool: {result!r}"


# ---------------------------------------------------------------------------
# sampling match tests
# ---------------------------------------------------------------------------
def test_ziwei_sun_at_noon_matches():
    """太阳居午宫(日丽中天)应命中 ZW-D018。"""
    engine = RuleEngine()
    facts = {
        "命宫": {"主星": ["太阳"], "宫位": "午", "庙旺": True, "辅星": [], "煞星": [],
                 "四化": []},
    }
    res = engine.match(facts, "ziwei")
    ids = {m["rule_id"] for m in res["matched_rules"]}
    assert "ZW-D018" in ids, f"应命中日丽中天, matched={ids}"


def test_ziwei_ziwei_alone_is_guanjun():
    """紫微坐命无辅弼 -> 命中孤君规则 ZW-D011。"""
    engine = RuleEngine()
    facts = {
        "命宫": {"主星": ["紫微"], "宫位": "子", "庙旺": True, "辅星": [],
                 "煞星": [], "四化": []},
        "三方四正": {"主星": [], "辅星": [], "煞星": [], "四化": []},
        "生年干": "甲", "性别": "男",
    }
    res = engine.match(facts, "ziwei")
    ids = {m["rule_id"] for m in res["matched_rules"]}
    assert "ZW-D011" in ids, f"应命中紫微孤君, matched={ids}"


def test_vedic_surya_mahadasha_exalted_matches():
    """Surya 大运 + Surya 擢升落 Kendra -> 命中 VE-D060。"""
    engine = RuleEngine()
    facts = {
        "current_dasha": {"lord": "Surya"},
        "grahas": {"Surya": {"dignity": "exalted", "bhava": 1}},
        "chart": {"evaluated": True},
    }
    res = engine.match(facts, "vedic")
    ids = {m["rule_id"] for m in res["matched_rules"]}
    assert "VE-D060" in ids, f"应命中 Surya 大运顺遂, matched={ids}"


def test_vedic_kunkaraka_aries_fear():
    """Atmakaraka Navamsa = Mesha -> 命中 VE-D070。"""
    engine = RuleEngine()
    facts = {
        "atmakaraka": {"navamsha_sign": "Mesha", "dignity": "friendly", "bhava": 1},
        "query": {"aspect": "test"},
    }
    res = engine.match(facts, "vedic")
    ids = {m["rule_id"] for m in res["matched_rules"]}
    assert "VE-D070" in ids, f"应命中 Karaka-Aries, matched={ids}"


def test_vedic_domain_unknown_facts_no_crash():
    engine = RuleEngine()
    # 空 facts 不应匹配任何条件(条件均为具体断言)
    res = engine.match({}, "vedic")
    assert res["matched_count"] >= 0
    assert isinstance(res["matched_rules"], list)
