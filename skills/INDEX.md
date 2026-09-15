# Skill 领域索引

本目录提供一个总入口和八个可独立加载的领域 Skill。每个领域 Skill 的 `SKILL.md` 都包含标准 YAML frontmatter，供运行时按 `name` 与 `description` 进行路由；详细判例和速查资料通过同目录 Markdown 文件按需加载。

| Skill | 领域 | 主要触发词 | 配套资料 |
|---|---|---|---|
| `liuyao-divination` | 六爻纳甲 | 卦象、动爻、世应、六亲、纳甲、应期 | `cases.md`、`rules_reference.md` |
| `ziwei-divination` | 紫微斗数 | 命宫、十二宫、星曜、四化、大限、流年 | `cases.md`、`galaxy_matrix.md` |
| `bazi-mingli` | 八字命理 | 四柱、日主、月令、用神、格局、大运 | `cases.md`、`tiaohou_matrix.md` |
| `vedic-divination` | 吠陀占星 | Vedic、Jyotish、Lagna、Nakshatra、Dasha、D9 | `cases.md`、`reference.md` |
| `western-astrology` | 西方心理占星 | Tropical、上升、相位、Transit、Synastry、Composite | `cases.md`、`reference.md` |
| `attachment-patterns` | 依恋模式 | 焦虑型、回避型、安全型、AAI、分离焦虑 | `cases.md`、`reference.md` |
| `intimate-relationships` | 亲密关系 | 伴侣冲突、追逐退缩、EFT、修复、欲望 | `cases.md`、`reference.md` |
| `trauma-informed-support` | 创伤知情支持 | 创伤、闪回、冻结、解离、CPTSD、IFS | `cases.md`、`reference.md` |

## 路由原则

先根据用户主诉选择一个主要领域，再根据输入中是否存在第二个明确维度加载 `shared/cross_domain.md`。Vedic 与 Western 的黄道坐标系必须分开处理；术数内容表达结构倾向和时间窗口，不作宿命判决；心理关系内容不替代临床诊断、治疗或危机处置。

## 维护命令

在仓库根目录执行：

```bash
python3 tools/validate_skills.py
```

该命令检查所有 Skill 的 frontmatter、描述长度和相对链接。新增领域时，应同时新增 `skills/<domain>/SKILL.md`、本索引条目以及相应判例/参考资料，并通过校验后再提交。
