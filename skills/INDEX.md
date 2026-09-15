# Skill 统一索引

仓库的 Skill 资产统一收敛在 `skills/` 下，分为三层：**总入口**负责路由，**八个领域包**负责日常加载，`_catalog/` 保存可追溯的批量蒸馏与编译资产。除 `_catalog/` 外，不再新增平行的 Skill 根目录。

## 目录规范

```text
skills/
├── SKILL.md                         # 唯一总入口
├── INDEX.md                         # 本索引
├── <domain>/SKILL.md                # 八个日常领域 Skill
├── <domain>/{cases,reference}.md    # 领域资料
├── shared/                          # 跨领域术语和联动规则
└── _catalog/cangjie/                # 编译资产与来源证据归档
    ├── compiled/                    # 可加载的 Cangjie 子 Skill
    ├── bundles/                     # verified.yaml 与能力卡事实源
    ├── docs/                        # 流水线文档
    ├── evidence/                    # 开放来源证据
    └── reports/                     # 审查与修复报告
```

`_catalog/` 是**参考与来源层**，不是第二个运行时 Skill 根目录。运行时首先使用 `skills/SKILL.md` 路由到八个领域包；只有在需要更细能力、来源证据或 Cangjie 编译产物时，才进入 `skills/_catalog/cangjie/`。

## 日常领域 Skill

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

校验器会递归检查总入口、八个领域包和 Cangjie 编译子 Skill 的 frontmatter、重复名称、相对链接以及必需目录。新增日常领域时，应新增 `skills/<domain>/SKILL.md`；新增批量来源资产时，应放入 `skills/_catalog/cangjie/` 的对应层，不得再创建新的平行目录。
