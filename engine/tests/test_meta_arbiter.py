"""Meta-Arbiter v2.1 确定性安全分流总控单元测试。

覆盖 19 项核心断言 + 边界用例:
  危机熔断(4) / 施虐识别(1) / 躯体高唤起(1) / 关系修复(1) /
  象征层旁注(1) / 置信锁(1) / MultiModalRouter 判例1~6(7) /
  命名归一化(1) / 去重(1) + 边界补充用例。
"""
from __future__ import annotations

import pytest

from meta_arbiter import (
    ENGINE_VERSION,
    CaseContext,
    MetaArbiter,
    MultiModalRouter,
    RiskAssessment,
    SafetyLevel,
)


# ---------------------------------------------------------------------------
# 辅助构造
# ---------------------------------------------------------------------------
def _make_ctx(**overrides) -> CaseContext:
    """构造一个默认低风险 CaseContext, 允许覆盖任意字段。"""
    risk = overrides.pop("risk_overrides", {})
    base = dict(
        user_id="u-test",
        raw_statement="测试语句",
        risk_assessment=RiskAssessment(**risk),
        somatic_activation=overrides.pop("somatic_activation", 0.0),
        relational_conflict=overrides.pop("relational_conflict", False),
        symbolic_profiles=overrides.pop("symbolic_profiles", {}),
    )
    base.update(overrides)
    return CaseContext(**base)


@pytest.fixture
def arbiter() -> MetaArbiter:
    return MetaArbiter()


@pytest.fixture
def router() -> MultiModalRouter:
    return MultiModalRouter(MetaArbiter())


# ---------------------------------------------------------------------------
# 1~4. 危机熔断 (0 级硬熔断)
# ---------------------------------------------------------------------------
def test_crisis_suicidal_intent(arbiter: MetaArbiter):
    ctx = _make_ctx(risk_overrides={"has_suicidal_intent": True})
    assert arbiter.evaluate_risk(ctx) == SafetyLevel.CRISIS
    chain = arbiter.route(ctx)
    assert chain.is_terminal_crisis is True
    assert chain.nodes[0].primary_skill_id == "crisis_hotline_protocol"


def test_crisis_strangulation(arbiter: MetaArbiter):
    ctx = _make_ctx(risk_overrides={"has_strangulation": True})
    assert arbiter.evaluate_risk(ctx) == SafetyLevel.CRISIS
    chain = arbiter.route(ctx)
    assert chain.is_terminal_crisis is True
    assert chain.nodes[0].primary_skill_id == "crisis_hotline_protocol"


def test_crisis_weapon_threat(arbiter: MetaArbiter):
    ctx = _make_ctx(risk_overrides={"has_weapon_threat": True})
    assert arbiter.evaluate_risk(ctx) == SafetyLevel.CRISIS
    chain = arbiter.route(ctx)
    assert chain.is_terminal_crisis is True


def test_crisis_fear_of_death(arbiter: MetaArbiter):
    ctx = _make_ctx(risk_overrides={"fear_of_death": True})
    assert arbiter.evaluate_risk(ctx) == SafetyLevel.CRISIS
    chain = arbiter.route(ctx)
    assert chain.is_terminal_crisis is True
    # 危机节点不应挂载象征层旁注
    assert chain.nodes[0].side_annotations is None


# ---------------------------------------------------------------------------
# 5. 施虐识别 (1 级)
# ---------------------------------------------------------------------------
def test_safety_plan_lethality_4(arbiter: MetaArbiter):
    ctx = _make_ctx(risk_overrides={"lethality_score": 4})
    assert arbiter.evaluate_risk(ctx) == SafetyLevel.SAFETY_PLAN
    chain = arbiter.route(ctx)
    assert chain.nodes[0].primary_skill_id == "psych_why_does_he"
    assert chain.is_terminal_crisis is False


# ---------------------------------------------------------------------------
# 6. 躯体高唤起 (2 级)
# ---------------------------------------------------------------------------
def test_stabilize_somatic_07(arbiter: MetaArbiter):
    ctx = _make_ctx(somatic_activation=0.7)
    assert arbiter.evaluate_risk(ctx) == SafetyLevel.STABILIZE
    chain = arbiter.route(ctx)
    assert chain.nodes[0].primary_skill_id == "psych_cptsd"


# ---------------------------------------------------------------------------
# 7. 关系修复 (3 级 默认)
# ---------------------------------------------------------------------------
def test_repair_default(arbiter: MetaArbiter):
    ctx = _make_ctx()
    assert arbiter.evaluate_risk(ctx) == SafetyLevel.REPAIR
    chain = arbiter.route(ctx)
    assert chain.nodes[0].primary_skill_id == "psych_hold_me_tight"


# ---------------------------------------------------------------------------
# 8. 象征层旁注挂载 (5 个引擎全量)
# ---------------------------------------------------------------------------
def test_symbolic_side_annotations_five_engines(arbiter: MetaArbiter):
    profiles = {
        "bazi_chart": {"gods": ["比肩", "正官"]},
        "ziwei_chart": {"stars": ["紫微", "天府"]},
        "liuyao_hexagram": {"name": "水山蹇"},
        "western_natal": {"hard_aspects": ["月亮刑冥王"]},
        "vedic_d9": {"ashtakoota_score": 28},
    }
    ctx = _make_ctx(symbolic_profiles=profiles)
    chain = arbiter.route(ctx)  # 默认 REPAIR, 非危机
    ann = chain.nodes[0].side_annotations or {}
    # 五个旁注键全部存在
    assert set(ann.keys()) == {"bazi", "ziwei", "liuyao", "western_astrology", "vedic_jyotish"}
    # 且每个旁注携带对应引擎标识
    engine_ids = {v["engine"] for v in ann.values()}
    assert "bazi-v3-engine" in engine_ids
    assert "ziwei-v3-engine" in engine_ids
    assert "liuyao-najia-core" in engine_ids
    assert "astrology-v3-engine" in engine_ids
    assert "vedic_jyotish_core" in engine_ids


# ---------------------------------------------------------------------------
# 9. 置信锁断言 [0.36, 0.40] 且 is_symbolic_annotation=True
# ---------------------------------------------------------------------------
def test_symbolic_confidence_lock(arbiter: MetaArbiter):
    profiles = {
        "bazi_chart": {"gods": []},
        "ziwei_chart": {"stars": []},
        "liuyao_hexagram": {"name": ""},
        "western_natal": {"hard_aspects": []},
        "vedic_d9": {"ashtakoota_score": None},
    }
    ann = MetaArbiter._extract_symbolic_annotations(profiles)
    assert MetaArbiter.assert_symbolic_lock(ann) is True
    for entry in ann.values():
        assert 0.36 <= entry["confidence"] <= 0.40
        assert entry["is_symbolic_annotation"] is True


# ---------------------------------------------------------------------------
# 10. MultiModalRouter 判例 1: 危机候选 → primary=crisis, 其他 suppressed
# ---------------------------------------------------------------------------
def test_router_case1_crisis_suppresses_others(router: MultiModalRouter):
    ctx = _make_ctx(risk_overrides={"has_suicidal_intent": True})
    decision = router.arbitrate(ctx, ["psych_cptsd", "psych_hold_me_tight", "psych_why_does_he"])
    assert decision.primary == "crisis_hotline_protocol"
    assert "crisis_hotline_protocol" in decision.rank_order
    # 其他证据候选全部被 suppressed
    for c in ["psych_cptsd", "psych_hold_me_tight", "psych_why_does_he"]:
        assert c in decision.suppressed
    assert "判例1" in decision.rationale


# ---------------------------------------------------------------------------
# 11. 判例 2: boundaries + attached 同时存在 → rationale 含 "判例2"
# ---------------------------------------------------------------------------
def test_router_case2_boundaries_attached(router: MultiModalRouter):
    ctx = _make_ctx()  # 无危机/无虐待/无高唤起
    decision = router.arbitrate(ctx, ["psych_boundaries", "psych_attached"])
    assert "判例2" in decision.rationale
    # boundaries(tier1) 应排在 attached(tier3) 之前
    assert decision.rank_order.index("psych_boundaries") < decision.rank_order.index("psych_attached")


# ---------------------------------------------------------------------------
# 12. 判例 3: abuse_present + psych_nvc → psych_nvc suppressed
# ---------------------------------------------------------------------------
def test_router_case3_abuse_suppresses_nvc(router: MultiModalRouter):
    ctx = _make_ctx(risk_overrides={"lethality_score": 4})
    decision = router.arbitrate(ctx, ["psych_nvc", "psych_why_does_he"])
    assert "psych_nvc" in decision.suppressed
    assert "判例3" in decision.rationale
    # 施虐覆盖守卫: why_does_he 应被提升为 primary
    assert decision.primary == "psych_why_does_he"


# ---------------------------------------------------------------------------
# 13. 判例 4 急性: relational_conflict + high_arousal → seven_principles suppressed
# ---------------------------------------------------------------------------
def test_router_case4_acute_suppresses_seven_principles(router: MultiModalRouter):
    ctx = _make_ctx(somatic_activation=0.8, relational_conflict=True)
    decision = router.arbitrate(
        ctx, ["psych_hold_me_tight", "psych_seven_principles", "psych_cptsd"]
    )
    assert "psych_seven_principles" in decision.suppressed
    assert "判例4" in decision.rationale
    assert "急性" in decision.rationale


# ---------------------------------------------------------------------------
# 14. 判例 4 慢性: 无急性冲突 → hold_me_tight suppressed
# ---------------------------------------------------------------------------
def test_router_case4_chronic_suppresses_hold_me_tight(router: MultiModalRouter):
    ctx = _make_ctx()  # 无 conflict / 无 high_arousal / 无 abuse
    decision = router.arbitrate(ctx, ["psych_hold_me_tight", "psych_seven_principles"])
    assert "psych_hold_me_tight" in decision.suppressed
    assert "判例4" in decision.rationale
    assert "慢性" in decision.rationale
    assert decision.primary == "psych_seven_principles"


# ---------------------------------------------------------------------------
# 15. 判例 5: high_arousal + psych_feeling_good → feeling_good suppressed
# ---------------------------------------------------------------------------
def test_router_case5_high_arousal_suppresses_feeling_good(router: MultiModalRouter):
    ctx = _make_ctx(somatic_activation=0.7)
    decision = router.arbitrate(ctx, ["psych_feeling_good", "psych_cptsd"])
    assert "psych_feeling_good" in decision.suppressed
    assert "判例5" in decision.rationale


# ---------------------------------------------------------------------------
# 16. 判例 6: 仅象征层候选 → symbolic_side_only=True
# ---------------------------------------------------------------------------
def test_router_case6_symbolic_side_only(router: MultiModalRouter):
    ctx = _make_ctx()
    decision = router.arbitrate(ctx, ["bazi_v3_engine", "astrology_v3_engine"])
    assert decision.symbolic_side_only is True
    assert decision.primary == ""
    assert "判例6" in decision.rationale


# ---------------------------------------------------------------------------
# 17. 命名归一化: hyphen/underscore 等效; bazi_mingli → bazi_v3_engine
# ---------------------------------------------------------------------------
def test_router_name_normalization(router: MultiModalRouter):
    assert router._normalize_skill_id("psych-cptsd") == router._normalize_skill_id("psych_cptsd")
    assert router._normalize_skill_id("bazi_mingli") == "bazi_v3_engine"
    # 端到端: 用连字符传入 psych-cptsd, 应与 psych_cptsd 等效去重
    ctx = _make_ctx()
    decision = router.arbitrate(ctx, ["psych-cptsd", "psych_cptsd"])
    # 两者归一化后相同, 只出现一次
    assert decision.rank_order.count("psych_cptsd") == 1


# ---------------------------------------------------------------------------
# 18. 去重: 重复候选只出现一次
# ---------------------------------------------------------------------------
def test_router_dedup_preserves_order(router: MultiModalRouter):
    ctx = _make_ctx()
    decision = router.arbitrate(
        ctx, ["psych_hold_me_tight", "psych_hold_me_tight", "psych_cptsd", "psych_cptsd"]
    )
    assert decision.rank_order.count("psych_hold_me_tight") == 1
    assert decision.rank_order.count("psych_cptsd") == 1
    # tier2(cptsd) 应排在 tier3(hold_me_tight) 之前
    assert decision.rank_order.index("psych_cptsd") < decision.rank_order.index("psych_hold_me_tight")


# ---------------------------------------------------------------------------
# 边界用例
# ---------------------------------------------------------------------------
def test_edge_lethality_below_threshold_no_safety_plan(arbiter: MetaArbiter):
    """lethality_score=3 (<4) 不应触发 SAFETY_PLAN, 落到 REPAIR。"""
    ctx = _make_ctx(risk_overrides={"lethality_score": 3})
    assert arbiter.evaluate_risk(ctx) == SafetyLevel.REPAIR


def test_edge_somatic_below_threshold_no_stabilize(arbiter: MetaArbiter):
    """somatic_activation=0.64 (<0.65) 不应触发 STABILIZE。"""
    ctx = _make_ctx(somatic_activation=0.64)
    assert arbiter.evaluate_risk(ctx) == SafetyLevel.REPAIR


def test_edge_empty_candidates_primary_empty(router: MultiModalRouter):
    ctx = _make_ctx()
    decision = router.arbitrate(ctx, [])
    assert decision.primary == ""
    assert decision.symbolic_side_only is False


def test_edge_engine_version_constant():
    assert ENGINE_VERSION.startswith("meta-arbiter-v2.1")


def test_edge_safety_plan_node_keeps_side_annotations(arbiter: MetaArbiter):
    """Bug3 回归: SAFETY_PLAN 节点应正常挂载 side_annotations, 不被过早 return 截断。"""
    profiles = {"bazi_chart": {"gods": []}}
    ctx = _make_ctx(risk_overrides={"lethality_score": 4}, symbolic_profiles=profiles)
    chain = arbiter.route(ctx)
    assert chain.nodes[0].primary_skill_id == "psych_why_does_he"
    assert chain.nodes[0].side_annotations is not None
    assert "bazi" in chain.nodes[0].side_annotations
