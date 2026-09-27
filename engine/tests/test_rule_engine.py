"""Rule engine contract tests for the divination knowledge service."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from rule_engine import RuleEngine


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "rules_manifest.json"


def _file_rule_counts() -> dict:
    """从磁盘规则实体文件动态读取各 domain 的规则数 (避免硬编码, 随规则集增长自动同步)。"""
    counts = {}
    for d in RuleEngine.DOMAINS:
        path = Path(RuleEngine().rules_file_path(d))
        counts[d] = len(json.loads(path.read_text(encoding="utf-8"))["rules"])
    return counts


def test_all_domain_rule_counts():
    engine = RuleEngine()
    actual = {d: len(engine.load_rules(d)) for d in engine.DOMAINS}
    assert actual == _file_rule_counts()


def test_unknown_domain_fails_closed():
    with pytest.raises(ValueError, match="unknown domain"):
        RuleEngine().load_rules("no_such_domain")


def test_empty_facts_do_not_match():
    engine = RuleEngine()
    result = engine.match({}, "bazi")
    assert result["matched_count"] == 0
    assert result["matched_rules"] == []


def test_liuyao_smoke_match_shape():
    engine = RuleEngine()
    result = engine.match(
        {
            "month_zh": "申",
            "day_zh": "子",
            "month_wx": "金",
            "day_wx": "水",
            "yong_shen": {"zhi": "申", "wx": "金", "dong": True, "yue_po": True},
            "net_score": 2,
        },
        "liuyao",
    )
    assert set(result) == {"matched_rules", "conclusions", "total_weight", "matched_count"}
    assert isinstance(result["matched_rules"], list)
    assert result["matched_count"] == len(result["matched_rules"])


def test_rule_manifest_hashes():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for entry in manifest["rules"]:
        path = ROOT / entry["path"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == entry["sha256"], entry["path"]
