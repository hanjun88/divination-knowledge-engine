#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""端到端集成链路验证脚本。

链路: 生辰 → 八字排盘 → 六爻排盘 → 规则匹配 → AST → UPIV
另含: 西占星盘、Meta-Arbiter 决策路由。

用法:
    cd engine && PYTHONPATH=. python e2e_verify.py
退出码 0 = 全部环节通过; 1 = 任一环节失败。
"""
from __future__ import annotations

import json
import sys
import traceback

RESULTS: list[dict] = []


def record(step: str, ok: bool, summary: str) -> None:
    RESULTS.append({"step": step, "ok": ok, "summary": summary})
    flag = "PASS" if ok else "FAIL"
    print(f"[{flag}] {step}: {summary}")


def main() -> int:
    # ---- (a) 八字排盘 ----
    try:
        from bazi.ganzhi import compute_bazi

        chart = compute_bazi(1990, 5, 15, 14)
        pillars = f"{chart.year.gz} {chart.month.gz} {chart.day.gz} {chart.hour.gz}"
        assert chart.year.gan and chart.day.gan, "四柱干支缺失"
        record("a_bazi_paipan", True,
               f"四柱={pillers_str(pillars)} 节气={chart.jieqi} 真太阳时={chart.true_solar_time}")
        day_gan, month_zhi = chart.day.gan, chart.month.zhi
    except Exception as e:  # noqa: BLE001
        record("a_bazi_paipan", False, f"{e!r}\n{traceback.format_exc()}")
        day_gan, month_zhi = "甲", "申"

    # ---- (b) 六爻排盘 → AST ----
    ast: dict = {}
    try:
        from liuyao.cast import cast_to_ast

        ast = cast_to_ast([7, 8, 9, 6, 7, 8], "庚", "申", "甲", "子")
        assert "rule_facts" in ast, "AST 缺少 rule_facts"
        assert ast["rule_facts"], "rule_facts 为空"
        record("b_liuyao_cast_ast", True,
               f"本卦={ast['hexagram'].get('ben_gua','?')} 变卦={ast['hexagram'].get('bian_gua','?')} "
               f"动爻数={ast['rule_facts'].get('dong_count')} "
               f"rule_facts字段={len(ast['rule_facts'])}")
    except Exception as e:  # noqa: BLE001
        record("b_liuyao_cast_ast", False, f"{e!r}\n{traceback.format_exc()}")

    # ---- (c) 六爻规则匹配 ----
    try:
        from rule_engine import RuleEngine

        eng = RuleEngine()
        m_ly = eng.match(ast["rule_facts"], "liuyao")
        assert m_ly["matched_count"] >= 1, "六爻规则未命中"
        record("c_liuyao_rule_match", True,
               f"命中规则={m_ly['matched_count']}条 总权重={m_ly['total_weight']} "
               f"结论示例={m_ly['conclusions'][:3]}")
    except Exception as e:  # noqa: BLE001
        record("c_liuyao_rule_match", False, f"{e!r}\n{traceback.format_exc()}")

    # ---- (d) 八字调候规则匹配 ----
    try:
        from rule_engine import RuleEngine

        eng = RuleEngine()
        m_bz = eng.match({"day_gan": day_gan, "month_zhi": month_zhi}, "bazi")
        assert m_bz["matched_count"] >= 1, "八字调候规则未命中"
        record("d_bazi_tiaohou_match", True,
               f"day_gan={day_gan} month_zhi={month_zhi} 命中={m_bz['matched_count']}条 "
               f"用神={m_bz['conclusions'][0] if m_bz['conclusions'] else 'n/a'}")
    except Exception as e:  # noqa: BLE001
        record("d_bazi_tiaohou_match", False, f"{e!r}\n{traceback.format_exc()}")

    # ---- (e) 西占星盘 ----
    try:
        from western.ephemeris import compute_natal_chart

        nc = compute_natal_chart(1990, 5, 15, 14.0, 39.9, 116.4)
        assert len(nc["planets"]) >= 7, "行星数量异常"
        sun = next(p for p in nc["planets"] if p["name"] == "太阳")
        record("e_western_natal", True,
               f"行星={len(nc['planets'])}颗 太阳={sun['sign']}{sun['degree']:.2f} "
               f"上升={nc['angles']['asc']['sign']} 相位={len(nc['aspects'])}组")
    except Exception as e:  # noqa: BLE001
        record("e_western_natal", False, f"{e!r}\n{traceback.format_exc()}")

    # ---- (f) Meta-Arbiter 决策路由 ----
    try:
        from meta_arbiter.engine import CaseContext, MetaArbiter, RiskAssessment

        ctx = CaseContext(
            user_id="e2e-user",
            raw_statement="占问事业财运走向",
            risk_assessment=RiskAssessment(lethality_score=0),
            somatic_activation=0.2,
            symbolic_profiles={
                "bazi_chart": {"gods": ["天乙贵人"]},
                "liuyao_hexagram": {"name": ast.get("hexagram", {}).get("ben_gua", "乾为天")},
            },
        )
        chain = MetaArbiter().route(ctx)
        assert chain.nodes, "决策链为空"
        record("f_meta_arbiter_route", True,
               f"节点数={len(chain.nodes)} 终端危机={chain.is_terminal_crisis} "
               f"主技能={chain.nodes[0].primary_skill_id} 动作={chain.nodes[0].action_type} "
               f"置信={chain.nodes[0].confidence_score:.2f} 版本={chain.engine_version}")
    except Exception as e:  # noqa: BLE001
        record("f_meta_arbiter_route", False, f"{e!r}\n{traceback.format_exc()}")

    # ---- (g) UPIV 向量融合 ----
    try:
        from upiv.fusion import DIMENSION_ORDER, fuse_vectors

        def _vec(**kw):
            v = {d: 0.0 for d in DIMENSION_ORDER}
            v.update(kw)
            return v

        fused = fuse_vectors({
            "liuyao": _vec(attachment_anxiety=0.3, relationship_agency=0.6),
            "bazi": _vec(attachment_anxiety=0.4, self_esteem_stability=0.5),
        })
        fv = fused["fused_vector"]
        assert abs(sum(fv.values())) > 0, "融合向量全零"
        record("g_upiv_fusion", True,
               f"维度数={len(fv)} 输入引擎={list(fused['contributions'].keys())} "
               f"依恋焦虑={fv['attachment_anxiety']:.3f} 关系掌控={fv['relationship_agency']:.3f}")
    except Exception as e:  # noqa: BLE001
        record("g_upiv_fusion", False, f"{e!r}\n{traceback.format_exc()}")

    # ---- 汇总 ----
    passed = sum(1 for r in RESULTS if r["ok"])
    total = len(RESULTS)
    print("\n================ E2E SUMMARY ================")
    print(f"stages passed: {passed}/{total}")
    payload = {"passed": passed, "total": total, "results": RESULTS}
    with open("e2e_report.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("wrote e2e_report.json")
    return 0 if passed == total else 1


def pillers_str(p: str) -> str:
    return p


if __name__ == "__main__":
    sys.exit(main())
