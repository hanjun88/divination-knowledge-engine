"""UPIV 六维认知特征向量融合模块单元测试。

覆盖:
  单引擎融合 / 多引擎加权 / 归一化钳制 /
  判例1 危机优先 / 判例5 一致性离群降权 /
  判例3 躯体优先 / 判例6 象征侧置 /
  依恋风格判定(4类) / 象征层置信硬锁 /
  AST 输出结构 / 六维完整性 / 空输入兜底。
"""
from __future__ import annotations

import math

import pytest

from upiv import (
    DIMENSION_ORDER,
    ENGINE_WEIGHTS,
    SYMBOLIC_CONFIDENCE_LOCK,
    UPIV_DIMENSIONS,
    classify_attachment,
    fuse_vectors,
    normalize_vector,
    prune_conflicts,
    to_ast,
)


# ---------------------------------------------------------------------------
# 辅助
# ---------------------------------------------------------------------------
def _all_dims(**overrides) -> dict:
    base = {d: 0.5 for d in DIMENSION_ORDER}
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# 1. 六维完整性
# ---------------------------------------------------------------------------
def test_six_dimensions_complete():
    assert len(UPIV_DIMENSIONS) == 6
    assert set(UPIV_DIMENSIONS.keys()) == set(DIMENSION_ORDER)
    for d in DIMENSION_ORDER:
        assert d in ENGINE_WEIGHTS["liuyao"]["dimension_map"]
        assert d in ENGINE_WEIGHTS["bazi"]["dimension_map"]


# ---------------------------------------------------------------------------
# 2. 单引擎融合
# ---------------------------------------------------------------------------
def test_single_engine_fusion_equals_input():
    out = _all_dims(attachment_anxiety=0.7, relationship_agency=0.9)
    res = fuse_vectors({"liuyao": out})
    fused = res["fused_vector"]
    # 单引擎: fused[dim] = out[dim] * w * conf / (w * conf) = out[dim]
    for d in DIMENSION_ORDER:
        assert math.isclose(fused[d], out[d], rel_tol=1e-6), f"{d}: {fused[d]} != {out[d]}"


# ---------------------------------------------------------------------------
# 3. 多引擎加权融合
# ---------------------------------------------------------------------------
def test_multi_engine_weighted_average():
    ly = _all_dims(attachment_anxiety=0.7)
    bz = _all_dims(attachment_anxiety=0.5)
    res = fuse_vectors({"liuyao": ly, "bazi": bz})
    fused = res["fused_vector"]

    # 手工核算 attachment_anxiety
    # liuyao: w=0.6, conf=0.38; bazi: w=0.5, conf=0.39
    num = 0.7 * 0.6 * 0.38 + 0.5 * 0.5 * 0.39
    den = 0.6 * 0.38 + 0.5 * 0.39
    expected = num / den
    assert math.isclose(fused["attachment_anxiety"], expected, rel_tol=1e-6)

    # 融合值应落在两引擎输出之间
    assert 0.5 <= fused["attachment_anxiety"] <= 0.7


# ---------------------------------------------------------------------------
# 4. 归一化钳制
# ---------------------------------------------------------------------------
def test_normalize_clamps_to_unit_interval():
    vec = {"attachment_anxiety": 1.5, "attachment_avoidance": -0.3,
           "emotional_externalization": 0.8, "emotional_internalization": 0.2,
           "relationship_agency": 0.5, "self_esteem_stability": 0.9}
    out = normalize_vector(vec)
    assert out["attachment_anxiety"] == 1.0
    assert out["attachment_avoidance"] == 0.0
    # 未越界值保持
    assert out["emotional_externalization"] == 0.8


def test_fusion_clamps_out_of_range_inputs():
    out = _all_dims(attachment_anxiety=2.0)
    res = fuse_vectors({"liuyao": out})
    assert res["fused_vector"]["attachment_anxiety"] == 1.0


# ---------------------------------------------------------------------------
# 5. 判例1: 危机优先
# ---------------------------------------------------------------------------
def test_prune_case1_crisis_overrides():
    outs = {
        "liuyao": _all_dims(attachment_anxiety=0.95),
        "bazi": _all_dims(attachment_anxiety=0.3),
        "western": _all_dims(attachment_anxiety=0.4),
    }
    res = prune_conflicts(outs)
    pruned = res["pruned_outputs"]
    # 所有引擎的 attachment_anxiety 都应被对齐到 0.95
    for eng in pruned:
        assert math.isclose(pruned[eng]["attachment_anxiety"], 0.95, rel_tol=1e-6)
    assert any("判例1" in r["type"] for r in res["conflicts_found"])
    assert any("判例1" in r for r in res["applied_rules"])


# ---------------------------------------------------------------------------
# 6. 判例5: 一致性 / 离群降权
# ---------------------------------------------------------------------------
def test_prune_case5_consensus_outlier_downweighted():
    # 3 个引擎在 attachment_avoidance 上一致 ~0.3，第 4 个离群 0.9
    outs = {
        "liuyao": _all_dims(attachment_avoidance=0.30),
        "bazi": _all_dims(attachment_avoidance=0.32),
        "western": _all_dims(attachment_avoidance=0.28),
        "vedic": _all_dims(attachment_avoidance=0.90),  # 离群
    }
    res = prune_conflicts(outs)
    pruned = res["pruned_outputs"]
    # 离群值应被向共识均值(~0.30)收缩一半
    assert pruned["vedic"]["attachment_avoidance"] < 0.90
    assert pruned["vedic"]["attachment_avoidance"] > 0.30
    # 3 个共识引擎基本保持
    for e in ("liuyao", "bazi", "western"):
        assert pruned[e]["attachment_avoidance"] == outs[e]["attachment_avoidance"]
    assert any("判例5" in r["type"] for r in res["conflicts_found"])


# ---------------------------------------------------------------------------
# 7. 判例3: 躯体优先
# ---------------------------------------------------------------------------
def test_prune_case3_somatic_priority():
    outs = {
        "liuyao": _all_dims(emotional_internalization=0.85),
        "bazi": _all_dims(emotional_internalization=0.2),
    }
    res = prune_conflicts(outs)
    pruned = res["pruned_outputs"]
    # 高内摄主导：其他引擎该维向高值对齐
    assert pruned["bazi"]["emotional_internalization"] >= 0.85 * 0.9 - 1e-6
    assert any("判例3" in r["type"] for r in res["conflicts_found"])


# ---------------------------------------------------------------------------
# 8. 判例6: 象征侧置
# ---------------------------------------------------------------------------
def test_prune_case6_symbolic_only():
    outs = {e: _all_dims() for e in ("liuyao", "bazi")}
    res = prune_conflicts(outs)
    assert res["symbolic_only"] is True
    assert any("判例6" in r for r in res["applied_rules"])


# ---------------------------------------------------------------------------
# 9. 依恋风格判定
# ---------------------------------------------------------------------------
def test_classify_attachment_secure():
    assert classify_attachment(0.2, 0.2) == "安全型"
    assert classify_attachment(0.3, 0.39) == "安全型"


def test_classify_attachment_anxious():
    assert classify_attachment(0.6, 0.2) == "焦虑型(痴迷型)"


def test_classify_attachment_avoidant():
    assert classify_attachment(0.2, 0.6) == "回避型(疏离型)"


def test_classify_attachment_disorganized():
    assert classify_attachment(0.7, 0.8) == "混乱型(恐惧型)"


# ---------------------------------------------------------------------------
# 10. 象征层置信硬锁
# ---------------------------------------------------------------------------
def test_symbolic_confidence_lock():
    lo, hi = SYMBOLIC_CONFIDENCE_LOCK
    assert (lo, hi) == (0.36, 0.40)
    for eng, cfg in ENGINE_WEIGHTS.items():
        c = cfg["base_confidence"]
        assert lo - 1e-9 <= c <= hi + 1e-9, f"{eng} conf={c} out of lock"


# ---------------------------------------------------------------------------
# 11. AST 输出结构完整
# ---------------------------------------------------------------------------
def test_to_ast_complete():
    outs = {
        "liuyao": _all_dims(attachment_anxiety=0.8, attachment_avoidance=0.7,
                            emotional_internalization=0.85, relationship_agency=0.6),
        "bazi": _all_dims(attachment_anxiety=0.6, attachment_avoidance=0.5),
    }
    pruned = prune_conflicts(outs)
    fused = fuse_vectors(pruned["pruned_outputs"])
    fused["conflict_pruning"] = pruned
    ast = to_ast(fused)

    # 顶层字段
    assert ast["upiv_version"] == "1.0.0"
    assert "fused_vector" in ast
    assert "dimension_labels" in ast
    assert "engine_contributions" in ast
    assert "conflict_pruning" in ast
    assert "summary" in ast

    # fused_vector 六维齐全
    assert set(ast["fused_vector"].keys()) == set(DIMENSION_ORDER)

    # summary 字段
    s = ast["summary"]
    assert s["attachment_style"] in {
        "安全型", "焦虑型(痴迷型)", "回避型(疏离型)", "混乱型(恐惧型)"}
    assert s["emotional_style"] in {"外化型", "内化型", "平衡型"}
    assert s["agency_level"] in {"高", "中", "低"}
    assert isinstance(s["risk_flags"], list)
    assert isinstance(s["primary_pattern"], str) and s["primary_pattern"]

    # conflict_pruning 子结构
    cp = ast["conflict_pruning"]
    assert "applied" in cp and "rules" in cp and "conflicts" in cp


# ---------------------------------------------------------------------------
# 12. 空输入兜底
# ---------------------------------------------------------------------------
def test_empty_engine_outputs():
    res = fuse_vectors({})
    assert res["fused_vector"] == {d: 0.0 for d in DIMENSION_ORDER}
    ast = to_ast(res)
    assert ast["summary"]["attachment_style"] == "安全型"  # 全 0 → 安全型


# ---------------------------------------------------------------------------
# 13. 端到端：剪枝 → 融合 → AST
# ---------------------------------------------------------------------------
def test_end_to_end_pipeline():
    outs = {
        "liuyao": _all_dims(attachment_anxiety=0.95),  # 触发判例1
        "bazi": _all_dims(attachment_anxiety=0.3, emotional_internalization=0.85),  # 触发判例3
        "western": _all_dims(attachment_anxiety=0.4, emotional_internalization=0.3),
        "vedic": _all_dims(attachment_anxiety=0.35, emotional_internalization=0.32),
    }
    pruned = prune_conflicts(outs, threshold=0.4)
    fused = fuse_vectors(pruned["pruned_outputs"])
    fused["conflict_pruning"] = pruned
    ast = to_ast(fused)

    # 危机维应被覆盖到接近 0.95
    assert ast["fused_vector"]["attachment_anxiety"] > 0.9
    # 至少 3 条判例被触发
    assert len(pruned["applied_rules"]) >= 3
    # risk_flags 应包含危机标记
    assert "CRISIS_attachment_panic" in ast["summary"]["risk_flags"]
