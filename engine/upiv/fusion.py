#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
upiv/fusion.py — UPIV (Universal Psychological Interpretation Vector)
六维认知特征向量加权融合 + Meta-Arbiter 判例冲突剪枝 + 归一化 AST 输出。

设计基线:
  - 六个心理维度全部取值 [0, 1]，越高代表该特征越强。
  - 象征层引擎(liuyao/bazi/ziwei/western/vedic)置信度硬锁 [0.36, 0.40]，
    与 meta_arbiter.engine.SYMBOLIC_CONFIDENCE_LOCK 对齐。
  - 融合公式为加权平均:
        fused[dim] = Σ(out[dim] * w[dim] * conf) / Σ(w[dim] * conf)
  - 冲突剪枝落地 Meta-Arbiter 6 大判例中的可在向量层实现的 1/2/3/5/6 条。
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

# 复用 Meta-Arbiter 的象征层置信硬锁，保持全局一致
try:  # pragma: no cover - 仅为容错导入
    from meta_arbiter.engine import SYMBOLIC_CONFIDENCE_LOCK  # type: ignore
except Exception:  # pragma: no cover
    SYMBOLIC_CONFIDENCE_LOCK: Tuple[float, float] = (0.36, 0.40)


# ---------------------------------------------------------------------------
# 1. UPIV 六维定义
# ---------------------------------------------------------------------------
UPIV_DIMENSIONS: Dict[str, str] = {
    "attachment_anxiety": "依恋焦虑度",        # 对被抛弃的恐惧
    "attachment_avoidance": "依恋回避度",      # 对亲密的回避
    "emotional_externalization": "情绪外化度",  # 情绪向外表达/爆发
    "emotional_internalization": "情绪内化度",  # 情绪向内压抑/反刍
    "relationship_agency": "关系掌控感",       # 在关系中的主导/控制倾向
    "self_esteem_stability": "自尊稳定性",     # 自我价值感的波动程度
}

DIMENSION_ORDER: List[str] = list(UPIV_DIMENSIONS.keys())


# 各引擎对六维的贡献权重
# 象征层置信硬锁 [0.36, 0.40]，心理层 [0.70, 0.95]
ENGINE_WEIGHTS: Dict[str, Dict[str, Any]] = {
    "liuyao": {
        "base_confidence": 0.38,
        "dimension_map": {
            "attachment_anxiety": {"trigger": "官鬼旺动克世", "weight": 0.6},
            "attachment_avoidance": {"trigger": "应爻化退/化绝", "weight": 0.5},
            "emotional_externalization": {"trigger": "世爻旺动冲应", "weight": 0.5},
            "emotional_internalization": {"trigger": "世爻休囚被克", "weight": 0.4},
            "relationship_agency": {"trigger": "世克应/世旺应衰", "weight": 0.6},
            "self_esteem_stability": {"trigger": "世爻临月建日辰", "weight": 0.4},
        },
    },
    "bazi": {
        "base_confidence": 0.39,
        "dimension_map": {
            "attachment_anxiety": {"trigger": "官杀旺/日弱", "weight": 0.5},
            "attachment_avoidance": {"trigger": "比劫旺/食伤旺", "weight": 0.4},
            "emotional_externalization": {"trigger": "食伤透干/伤官见官", "weight": 0.5},
            "emotional_internalization": {"trigger": "印星旺/七杀藏支", "weight": 0.4},
            "relationship_agency": {"trigger": "日主旺/比劫林立", "weight": 0.5},
            "self_esteem_stability": {"trigger": "日主通根透干", "weight": 0.4},
        },
    },
    "ziwei": {
        "base_confidence": 0.36,
        "dimension_map": {
            "attachment_anxiety": {"trigger": "巨门化忌/夫妻宫煞星", "weight": 0.5},
            "attachment_avoidance": {"trigger": "武曲七杀坐命/夫妻宫空", "weight": 0.4},
            "emotional_externalization": {"trigger": "破军化禄/贪狼化忌", "weight": 0.4},
            "emotional_internalization": {"trigger": "太阴化忌/天梁坐命", "weight": 0.4},
            "relationship_agency": {"trigger": "紫微化权/武曲化权", "weight": 0.5},
            "self_esteem_stability": {"trigger": "禄存化禄守命", "weight": 0.4},
        },
    },
    "western": {
        "base_confidence": 0.38,
        "dimension_map": {
            "attachment_anxiety": {"trigger": "月亮刑土星/金星落陷", "weight": 0.5},
            "attachment_avoidance": {"trigger": "金星水瓶/月亮摩羯", "weight": 0.5},
            "emotional_externalization": {"trigger": "火星合金星/月亮白羊", "weight": 0.5},
            "emotional_internalization": {"trigger": "月亮天蝎/土星合月亮", "weight": 0.4},
            "relationship_agency": {"trigger": "太阳狮子/火星一宫", "weight": 0.5},
            "self_esteem_stability": {"trigger": "太阳庙旺/金星庙旺", "weight": 0.4},
        },
    },
    "vedic": {
        "base_confidence": 0.37,
        "dimension_map": {
            "attachment_anxiety": {"trigger": "7宫主受克/月亮凶星", "weight": 0.4},
            "attachment_avoidance": {"trigger": "土星7宫/1宫主入6", "weight": 0.4},
            "emotional_externalization": {"trigger": "火星旺/罗睺合月亮", "weight": 0.4},
            "emotional_internalization": {"trigger": "土星合月亮/计都1宫", "weight": 0.4},
            "relationship_agency": {"trigger": "太阳旺/1宫主旺", "weight": 0.4},
            "self_esteem_stability": {"trigger": "1宫主庙旺/木星1宫", "weight": 0.4},
        },
    },
}

# 象征层引擎集合（与 meta_arbiter 对齐的语义子集）
SYMBOLIC_ENGINES = frozenset(ENGINE_WEIGHTS.keys())


# ---------------------------------------------------------------------------
# 4. 归一化
# ---------------------------------------------------------------------------
def normalize_vector(vector: Dict[str, float]) -> Dict[str, float]:
    """将六维向量归一化到 [0, 1]，逐维钳制到区间内。"""
    out: Dict[str, float] = {}
    for dim in DIMENSION_ORDER:
        val = vector.get(dim, 0.0)
        if val is None:
            val = 0.0
        try:
            v = float(val)
        except (TypeError, ValueError):
            v = 0.0
        out[dim] = max(0.0, min(1.0, v))
    return out


# ---------------------------------------------------------------------------
# 2. 加权融合
# ---------------------------------------------------------------------------
def fuse_vectors(engine_outputs: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """
    将多个引擎的六维输出加权融合。

    fused[dim] = Σ(out[dim] * w[dim] * conf) / Σ(w[dim] * conf)
    """
    if not engine_outputs:
        empty = {d: 0.0 for d in DIMENSION_ORDER}
        return {
            "fused_vector": empty,
            "contributions": {},
            "effective_weights": {},
            "dimension_labels": UPIV_DIMENSIONS,
        }

    # 先归一化各引擎输入，避免越界
    cleaned: Dict[str, Dict[str, float]] = {
        eng: normalize_vector(out) for eng, out in engine_outputs.items()
    }

    fused: Dict[str, float] = {}
    contributions: Dict[str, Dict[str, float]] = {}
    effective_weights: Dict[str, float] = {}

    for dim in DIMENSION_ORDER:
        numerator = 0.0
        denominator = 0.0
        for eng, out in cleaned.items():
            eng_cfg = ENGINE_WEIGHTS.get(eng)
            if eng_cfg is None:
                # 未知引擎：等权、无置信硬锁，按 0.38 兜底置信
                w = 1.0
                conf = 0.38
            else:
                dim_map = eng_cfg["dimension_map"].get(dim, {})
                w = dim_map.get("weight", 0.4)
                conf = float(eng_cfg["base_confidence"])
                # 判例2: 象征层置信硬锁 [0.36, 0.40]
                if eng in SYMBOLIC_ENGINES:
                    lo, hi = SYMBOLIC_CONFIDENCE_LOCK
                    conf = max(lo, min(hi, conf))

            val = out.get(dim, 0.0)
            contrib = val * w * conf
            numerator += contrib
            denominator += w * conf

            contributions.setdefault(eng, {})[dim] = contrib

        fused[dim] = (numerator / denominator) if denominator > 0 else 0.0

    # 各引擎有效权重 = avg(w_dim) * conf
    for eng, out in cleaned.items():
        eng_cfg = ENGINE_WEIGHTS.get(eng)
        if eng_cfg is None:
            effective_weights[eng] = 0.38
            continue
        conf = float(eng_cfg["base_confidence"])
        if eng in SYMBOLIC_ENGINES:
            lo, hi = SYMBOLIC_CONFIDENCE_LOCK
            conf = max(lo, min(hi, conf))
        dims = eng_cfg["dimension_map"]
        avg_w = sum(dims[d]["weight"] for d in DIMENSION_ORDER if d in dims) / max(1, len(dims))
        effective_weights[eng] = round(avg_w * conf, 6)

    return {
        "fused_vector": normalize_vector(fused),
        "contributions": contributions,
        "effective_weights": effective_weights,
        "dimension_labels": UPIV_DIMENSIONS,
    }


# ---------------------------------------------------------------------------
# 3. 冲突剪枝（基于 Meta-Arbiter 6 大判例）
# ---------------------------------------------------------------------------
def prune_conflicts(
    engine_outputs: Dict[str, Dict[str, float]],
    threshold: float = 0.4,
) -> Dict[str, Any]:
    """
    基于 Meta-Arbiter 6 大判例的冲突剪枝。

    落地判例:
      判例1 (危机优先): 任一引擎 attachment_anxiety > 0.9 → 该维全部对齐到危机值。
      判例2 (安全优先): 象征层置信度硬锁 [0.36, 0.40]（在 fuse 中执行，此处记录）。
      判例3 (躯体优先): 任一引擎 emotional_internalization > 0.8 → 高内摄主导，
                       其他引擎该维向高值对齐（抑制认知重构类外化信号）。
      判例5 (一致性): 3+ 引擎在某维差异 < 0.2 → 离群引擎降权 50%（数值向共识均值收缩一半）。
      判例6 (象征侧置): 仅象征层输入 → symbolic_only=True 标记。
      判例4 (急性优先): 高冲突维上，偏高(更急性/修复)的一侧占优——取 max 方向收缩。
    """
    pruned: Dict[str, Dict[str, float]] = {
        eng: normalize_vector(out) for eng, out in engine_outputs.items()
    }
    conflicts_found: List[Dict[str, Any]] = []
    applied_rules: List[str] = []

    engines = list(pruned.keys())
    if not engines:
        return {
            "pruned_outputs": pruned,
            "conflicts_found": conflicts_found,
            "applied_rules": applied_rules,
            "symbolic_only": False,
        }

    # 判例6: 仅象征层输入
    symbolic_only = all(e in SYMBOLIC_ENGINES for e in engines) and engines != []
    if symbolic_only:
        applied_rules.append("判例6: 象征侧置（仅象征层输入，全部维度标记 symbolic_only）")

    # 逐维剪枝
    for dim in DIMENSION_ORDER:
        values = {e: pruned[e].get(dim, 0.0) for e in engines}
        if not values:
            continue

        # ---- 判例1: 危机优先 ----
        crisis_engines = [e for e, v in values.items() if v > 0.9]
        if crisis_engines:
            crisis_val = max(values[e] for e in crisis_engines)
            for e in engines:
                pruned[e][dim] = crisis_val
            conflicts_found.append({
                "dimension": dim,
                "type": "判例1_危机优先",
                "crisis_engines": crisis_engines,
                "overridden": [e for e in engines if e not in crisis_engines],
                "value": crisis_val,
                "action": "危机信号压倒一切，该维全部对齐到危机值",
            })
            if "判例1: 危机优先（attachment_anxiety>0.9 覆盖其他引擎）" not in applied_rules:
                applied_rules.append("判例1: 危机优先（attachment_anxiety>0.9 覆盖其他引擎）")

        # ---- 判例3: 躯体优先 ----
        if dim == "emotional_internalization":
            somatic_engines = [e for e, v in values.items() if v > 0.8]
            if somatic_engines:
                somatic_val = max(values[e] for e in somatic_engines)
                for e in engines:
                    # 高内摄主导：其他引擎该维向高值对齐（躯体唤起优先，抑制认知重构）
                    pruned[e][dim] = max(pruned[e][dim], somatic_val * 0.9)
                conflicts_found.append({
                    "dimension": dim,
                    "type": "判例3_躯体优先",
                    "somatic_engines": somatic_engines,
                    "value": somatic_val,
                    "action": "高躯体唤起(emotional_internalization>0.8)，认知重构类信号被抑制",
                })
                if "判例3: 躯体优先（高内摄>0.8 抑制认知重构）" not in applied_rules:
                    applied_rules.append("判例3: 躯体优先（高内摄>0.8 抑制认知重构）")

        # ---- 判例5: 一致性 / 离群降权 ----
        dim_vals = [pruned[e][dim] for e in engines]
        if len(engines) >= 3:
            lo_v, hi_v = min(dim_vals), max(dim_vals)
            spread = hi_v - lo_v
            if spread >= threshold:
                # 找最大一致性簇（>=3 个引擎两两差 < 0.2）
                consensus: List[str] = []
                for e in engines:
                    others = [pruned[o][dim] for o in engines if o != e]
                    close = sum(1 for v in others if abs(v - pruned[e][dim]) < 0.2)
                    if close >= 2:  # 与至少2个其他引擎一致 → 该引擎在簇内
                        consensus.append(e)
                if len(consensus) >= 3:
                    consensus_mean = sum(pruned[e][dim] for e in consensus) / len(consensus)
                    outliers = [e for e in engines if e not in consensus]
                    for e in outliers:
                        old = pruned[e][dim]
                        # 降权 50%：向共识均值收缩一半
                        pruned[e][dim] = round((old + consensus_mean) / 2.0, 6)
                        conflicts_found.append({
                            "dimension": dim,
                            "type": "判例5_一致性",
                            "outlier_engine": e,
                            "consensus_engines": consensus,
                            "old_value": old,
                            "new_value": pruned[e][dim],
                            "delta": abs(pruned[e][dim] - old),
                            "action": "3+ 引擎一致，离群引擎降权50%（向共识均值收缩一半）",
                        })
                    if outliers:
                        if "判例5: 一致性（3+引擎一致，离群降权50%）" not in applied_rules:
                            applied_rules.append("判例5: 一致性（3+引擎一致，离群降权50%）")

        # ---- 判例4: 急性优先（高冲突维向偏高/修复方向收缩） ----
        cur_vals = [pruned[e][dim] for e in engines]
        if len(cur_vals) >= 2 and (max(cur_vals) - min(cur_vals)) >= threshold:
            high_val = max(cur_vals)
            # 仅在非危机维上做温和收缩，避免与判例1重复
            if dim != "attachment_anxiety":
                for e in engines:
                    pruned[e][dim] = round((pruned[e][dim] + high_val) / 2.0, 6)
                conflicts_found.append({
                    "dimension": dim,
                    "type": "判例4_急性优先",
                    "spread": round(max(cur_vals) - min(cur_vals), 4),
                    "action": "急性冲突场景，修复信号优先于维护信号（向高值方向收缩）",
                })
                if "判例4: 急性优先（修复信号优先于维护信号）" not in applied_rules:
                    applied_rules.append("判例4: 急性优先（修复信号优先于维护信号）")

    # 判例2 在 fuse 中执行硬锁；此处仅在存在跨层冲突时记录
    if applied_rules:
        applied_rules.append("判例2: 安全优先（象征层置信硬锁 [0.36,0.40]，由 fuse 强制执行）")

    return {
        "pruned_outputs": pruned,
        "conflicts_found": conflicts_found,
        "applied_rules": applied_rules,
        "symbolic_only": symbolic_only,
    }


# ---------------------------------------------------------------------------
# 5. 依恋风格判定
# ---------------------------------------------------------------------------
def classify_attachment(anxiety: float, avoidance: float) -> str:
    """
    根据依恋焦虑和回避度判定依恋风格:
      anxiety < 0.4 且 avoidance < 0.4 → 安全型
      anxiety >= 0.4 且 avoidance < 0.4 → 焦虑型(痴迷型)
      anxiety < 0.4 且 avoidance >= 0.4 → 回避型(疏离型)
      anxiety >= 0.4 且 avoidance >= 0.4 → 混乱型(恐惧型)
    """
    a = max(0.0, min(1.0, float(anxiety)))
    v = max(0.0, min(1.0, float(avoidance)))
    if a < 0.4 and v < 0.4:
        return "安全型"
    if a >= 0.4 and v < 0.4:
        return "焦虑型(痴迷型)"
    if a < 0.4 and v >= 0.4:
        return "回避型(疏离型)"
    return "混乱型(恐惧型)"


# ---------------------------------------------------------------------------
# 6. AST 输出
# ---------------------------------------------------------------------------
def _emotional_style(ext: float, internal: float) -> str:
    if abs(ext - internal) < 0.15:
        return "平衡型"
    return "外化型" if ext > internal else "内化型"


def _agency_level(agency: float) -> str:
    if agency >= 0.6:
        return "高"
    if agency >= 0.4:
        return "中"
    return "低"


def _risk_flags(vec: Dict[str, float]) -> List[str]:
    flags: List[str] = []
    if vec.get("attachment_anxiety", 0.0) >= 0.7:
        flags.append("high_attachment_anxiety")
    if vec.get("attachment_avoidance", 0.0) >= 0.7:
        flags.append("high_attachment_avoidance")
    if vec.get("emotional_internalization", 0.0) >= 0.8:
        flags.append("high_somatic_internalization")
    if vec.get("emotional_externalization", 0.0) >= 0.8:
        flags.append("high_emotional_activation")
    if vec.get("self_esteem_stability", 0.0) <= 0.3:
        flags.append("low_self_esteem_stability")
    if vec.get("attachment_anxiety", 0.0) >= 0.9:
        flags.append("CRISIS_attachment_panic")
    return flags


def _primary_pattern(vec: Dict[str, float]) -> str:
    top = sorted(DIMENSION_ORDER, key=lambda d: vec.get(d, 0.0), reverse=True)[:2]
    labels = [UPIV_DIMENSIONS[d] for d in top]
    return "+".join(labels)


def to_ast(fusion_result: Dict[str, Any]) -> Dict[str, Any]:
    """输出标准化 AST JSON，供下游消费。"""
    fused = normalize_vector(fusion_result.get("fused_vector", {}))
    vec = fused

    anxiety = vec.get("attachment_anxiety", 0.0)
    avoidance = vec.get("attachment_avoidance", 0.0)
    ext = vec.get("emotional_externalization", 0.0)
    internal = vec.get("emotional_internalization", 0.0)
    agency = vec.get("relationship_agency", 0.0)

    pruning = fusion_result.get("conflict_pruning", {}) or {}

    return {
        "upiv_version": "1.0.0",
        "fused_vector": fused,
        "dimension_labels": UPIV_DIMENSIONS,
        "engine_contributions": fusion_result.get("contributions", {}),
        "effective_weights": fusion_result.get("effective_weights", {}),
        "conflict_pruning": {
            "applied": bool(pruning.get("applied_rules")),
            "rules": pruning.get("applied_rules", []),
            "conflicts": pruning.get("conflicts_found", []),
            "symbolic_only": pruning.get("symbolic_only", False),
        },
        "summary": {
            "primary_pattern": _primary_pattern(vec),
            "attachment_style": classify_attachment(anxiety, avoidance),
            "emotional_style": _emotional_style(ext, internal),
            "agency_level": _agency_level(agency),
            "risk_flags": _risk_flags(vec),
        },
    }
