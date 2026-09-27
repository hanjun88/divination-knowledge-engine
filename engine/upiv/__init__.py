"""
engine/upiv — UPIV (Universal Psychological Interpretation Vector) 六维认知特征向量融合模块。

模块划分:
  fusion.py — 六维定义、加权融合、冲突剪枝、归一化、AST 输出、依恋风格判定
"""
from .fusion import (
    DIMENSION_ORDER,
    UPIV_DIMENSIONS,
    ENGINE_WEIGHTS,
    SYMBOLIC_CONFIDENCE_LOCK,
    fuse_vectors,
    prune_conflicts,
    normalize_vector,
    classify_attachment,
    to_ast,
)

__all__ = [
    "DIMENSION_ORDER",
    "UPIV_DIMENSIONS",
    "ENGINE_WEIGHTS",
    "SYMBOLIC_CONFIDENCE_LOCK",
    "fuse_vectors",
    "prune_conflicts",
    "normalize_vector",
    "classify_attachment",
    "to_ast",
]
