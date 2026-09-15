#!/usr/bin/env python3
"""Normalize repository skill metadata without changing skill bodies."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = {
    "skills/SKILL.md": (
        "divination-psychology",
        "八领域术数与心理关系技能总入口。Use for routing requests across 六爻、紫微斗数、八字、吠陀占星、西方占星、依恋、亲密关系与创伤疗愈, and for cross-domain analysis boundaries.",
    ),
    "skills/liuyao/SKILL.md": (
        "liuyao-divination",
        "六爻纳甲排盘后的结构化断卦与应期分析。Use when the user provides a hexagram, moving lines, 世应、六亲、纳甲 or asks about a specific divination question.",
    ),
    "skills/ziwei/SKILL.md": (
        "ziwei-divination",
        "紫微斗数已安星命盘的格局、十二宫、四化与限运分析。Use when the user provides a Ziwei chart or asks about 命宫、星曜、四化、十二宫、大限或流年.",
    ),
    "skills/bazi/SKILL.md": (
        "bazi-mingli",
        "子平八字四柱的旺衰、用神、格局、调候与大运分析。Use when the user provides 八字、四柱、干支、日主、月令 or asks about 用神、格局、流年或大运.",
    ),
    "skills/vedic/SKILL.md": (
        "vedic-divination",
        "印度吠陀占星恒星黄道本命盘、Nakshatra、Dasha、D9 与 Yogas 分析。Use when the user asks about Vedic/Jyotish、Lagna、Rashi、Nakshatra、Dasha or Navamsha.",
    ),
    "skills/western/SKILL.md": (
        "western-astrology",
        "西方热带黄道心理占星的本命盘、相位、宫位、行运、次限与关系盘分析。Use when the user asks about Western astrology、natal chart、上升、行星相位、Transit、Synastry or Composite.",
    ),
    "skills/attachment/SKILL.md": (
        "attachment-patterns",
        "成人依恋风格、内部工作模型与关系互动模式分析。Use when the user asks about 焦虑型、回避型、安全型、混乱型、分离焦虑、AAI or attachment dynamics.",
    ),
    "skills/intimate/SKILL.md": (
        "intimate-relationships",
        "亲密关系冲突循环、EFT 对话、欲望张力、阶段评估与修复策略。Use when the user asks about 伴侣冲突、追逐退缩、冷战、沟通、信任修复、婚姻或欲望与亲密.",
    ),
    "skills/trauma/SKILL.md": (
        "trauma-informed-support",
        "创伤知情的 4F 反应、神经系统状态、SE、IFS、CPTSD 图谱与稳定化支持。Use when the user mentions 创伤、闪回、冻结、解离、CPTSD、躯体反应、IFS or polyvagal regulation; do not use as a diagnosis or crisis substitute.",
    ),
}


def normalize(path: Path, name: str, description: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            text = text[end + len("\n---\n") :]
    path.write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n{text.lstrip()}",
        encoding="utf-8",
    )


for relative, (name, description) in SKILLS.items():
    normalize(ROOT / relative, name, description)
print(f"normalized {len(SKILLS)} skill metadata files")
