# Divination Rule Engine

六爻 / 紫微斗数 / 八字 三域规则引擎。

将已编译的古籍决策树（六爻决策树编译.md、紫微斗数赋文拓扑编译.md、滴天髓阐微/命理约言/造化元钥）
统一编译为 DSL 规则 JSON，由 Python 规则引擎加载并通过 FastAPI 提供 REST 服务。

## 目录结构

```
divination-engine/
├── rules/
│   ├── rules_liuyao.json     # 六爻规则 (82 条)
│   ├── rules_ziwei.json      # 紫微规则 (64 条)
│   └── rules_bazi.json       # 八字规则 (60 条)
├── rule_engine.py            # RuleEngine 核心类
├── main.py                   # FastAPI 服务
├── gen_liuyao.py             # 六爻规则生成脚本
├── gen_ziwei.py              # 紫微规则生成脚本
├── gen_bazi.py               # 八字规则生成脚本
├── requirements.txt
└── README.md
```

## 安装

```bash
cd divination-engine
pip install -r requirements.txt
```

## 启动

```bash
uvicorn main:app --reload
# 或
python main.py
```

服务默认监听 `http://0.0.0.0:8000`，交互式文档见 `http://localhost:8000/docs`。

## API 端点

| Method | Path | 说明 |
|---|---|---|
| GET  | `/health` | 健康检查 + 各领域规则数 |
| GET  | `/api/rules/{domain}` | 列出某领域全部规则 (`domain` ∈ liuyao/ziwei/bazi) |
| POST | `/api/liuyao/analyze` | 六爻断卦分析 |
| POST | `/api/ziwei/analyze` | 紫微命盘分析 |
| POST | `/api/bazi/analyze` | 八字分析 |

每个分析端点统一返回：

```json
{
  "domain": "liuyao",
  "matched_rules": [
    {"rule_id": "LY-M01", "name": "爻临月建旺极", "category": "month",
     "weight": 3, "priority": 10, "source": "增删卜易·卷一·月将章", "detail": "..."}
  ],
  "conclusions": ["用神临月建", ...],
  "total_weight": 3,
  "matched_count": 1
}
```

## DSL 规则格式

```json
{
  "rule_id": "LY-001",
  "domain": "liuyao",
  "category": "month",
  "name": "爻临月建旺极",
  "conditions": [
    {"field": "yong_shen.zhi", "operator": "==", "value": "${month_zh}"}
  ],
  "actions": [
    {"conclusion": "用神临月建", "detail": "旺之极"}
  ],
  "weight": 3,
  "priority": 10,
  "source": "增删卜易·卷一·月将章第十六"
}
```

支持：

- 比较运算：`==, !=, >=, <=, >, <, in, not_in, contains, contains_all, contains_any`
- 五行运算：`wuxing_sheng / wuxing_ke / wuxing_bihe / wuxing_tongqi`
- 地支运算：`liuchong / liuhe / yue_mu / ri_mu / yue_jue / ri_jue`
- 逻辑嵌套：`{"AND": [...]} / {"OR": [...]} / {"NOT": {...}}`
- 模板占位：`${month_zh}`、`${yong_shen.zhi}` 等点路径

## 示例请求

### 六爻

```bash
curl -X POST http://localhost:8000/api/liuyao/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "month_zh": "申", "day_zh": "子",
    "month_wx": "金", "day_wx": "水",
    "yong_shen": {"zhi": "申", "wx": "金", "dong": true, "yue_po": true, "wangshuai": "旺"},
    "has_ri_dong_sheng": false, "net_score": 2
  }'
```

### 紫微

```bash
curl -X POST http://localhost:8000/api/ziwei/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ming_gong": {"palace": "命", "main_stars": ["紫微"], "aux_stars": ["左辅","右弼"],
                  "sha_stars": [], "si_hua": [], "palace_pos": "子", "wang": true}
  }'
```

### 八字

```bash
curl -X POST http://localhost:8000/api/bazi/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "day_gan": "甲", "month_zhi": "寅",
    "ri_zhu_wx": "木", "ri_zhu_wangshuai": "旺",
    "geju": "正官格"
  }'
```

## 规则统计

| 领域 | 规则数 | 覆盖模块 |
|---|---|---|
| liuyao | 82 | 月建9 / 日辰12 / 动爻7 / 变爻13 / 月破旬空叠加10 / 四神联动9 / 应期14 / 旺衰总判5 / 取用3 |
| ziwei | 64 | 格局27 / 命宫主星15 / 四化8 / 煞曜辅曜6 / 十二宫8 |
| bazi | 60 | 滴天髓理气10 / 命理约言格局14 / 造化元钥调候15 / 六亲8 / 大运流年8 / 性情5 |

## 出处

- 六爻：《增删卜易》《卜筮正宗》《黄金策》《易隐》
- 紫微：《紫微斗数全书》（太微赋 / 骨髓赋 / 诸星问答论 / 十二宫诸星断）
- 八字：《滴天髓阐微》（任铁樵）、《命理约言》（陈素庵）、《造化元钥/穷通宝鉴》（余春台）
