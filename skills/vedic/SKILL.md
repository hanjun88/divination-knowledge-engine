---
name: vedic-divination
description: 印度吠陀占星恒星黄道本命盘、Nakshatra、Dasha、D9 与 Yogas 分析。Use when the user asks about Vedic/Jyotish、Lagna、Rashi、Nakshatra、Dasha or Navamsha.
---

# 吠陀占星 / 印度星盘解读技能 (Vedic Astrology · Jyotish Skill)

> **体系**：Parashari 吠陀占星（Sidereal Zodiac，Lahiri / Chitrapaksha ayanamsa）
> **义理母本**：BPHS（Brihat Parashara Hora Shastra，《婆罗门 parashara 大经》）、Jaimini Sutras
> **蒸馏来源**：磁盘已有 `vedic_jyotish_core` 能力卡（bphs-sidereal / nine-graha / nakshatra-27 / d9-navamsha / yogas / ashtakoota）+ 公版梵文典籍核心概念
> **版本**：v1.0 | 2026-09-15

---

## 1. 技能名称与描述

**vedic-divination**：基于印度吠陀占星（Vedic Jyotish，亦称 Hindu / Indian Astrology）的本命盘解读引擎。输入出生信息（或已排好的 D1 / D9 盘、Lagna、Rashi），按 Parashari 体系输出上升与月亮定位、行星入宫与庙旺落陷、Nakshatra 二十七宿、Vimshottari Dasha 大运、Yogas 格局的结构化论断。

本技能**只在恒星黄道（Sidereal，Lahiri 岁差修正）语义内说话**，不做与西方回归黄道（Tropical）的星座翻译。所有征象按"自我观察的隐喻镜子"读取，置信带硬锁在低区间（is_actionable=false），不构成医疗 / 法律 / 财务 / 婚恋决策依据。

---

## 2. 触发条件

当用户提出以下需求时触发本技能：

- 提供出生日期 / 时间 / 地点，要求**吠陀盘 / 印度星盘**解读（明确说"吠陀""Vedic""印度占星""Jyotish"）
- 问 **Dasha 大运**（Vimshottari Dasha、Mahadasha / Antardasha、"我现在走什么大运"）
- 问 **Nakshatra 星宿 / 二十七宿 / 生宿（Janma Nakshatra）/ Pada**
- 问 **Yogas 格局**（Raja Yoga、Dhana Yoga、Gajakesari、Pancha Mahapurusha、Budha-Aditya、Vargottama 等）
- 问 **分盘 Varga**（D9 Navamsha 九分盘、D10 Dashamsha 等"这个分盘看什么"）
- 问 **Lagna 上升 / Rashi 月亮星座 / Bhava 宫位 / Graha 行星**在吠陀体系下的含义
- 问"为什么我在印度占星和西方占星里星座不一样"（坐标系差异）

**不触发**：仅问西方热带黄道本命盘（走 `western` 技能）、问八字 / 紫微 / 六爻、要求把西方盘度数直接"翻译"成吠陀星座（拒绝翻译，见第 7 节）。

---

## 3. 输入参数说明

```json
{
  "birth_date": "1990-08-15",          // 公历出生日期
  "birth_time": "14:35",               // 当地钟表时间（须注明是否夏令时）
  "birth_place": "New Delhi, IN",      // 出生城市 + 经纬度（用于定 Lagna）
  "ayanamsa": "Lahiri",                // 岁差体系，默认 Lahiri，不混用
  "lagna_rashi": "Simha (Leo)",        // 上升 Lagna / 命宫星座（恒星黄道）
  "lagna_degree": "12.40",             // 上升度数
  "rashi_moon": "Karka (Cancer)",      // 月亮 Rashi（月亮星座，恒星黄道）
  "janma_nakshatra": "Pushya",         // 生宿（出生时月亮所在 Nakshatra）
  "nakshatra_pada": 2,                 // 生宿 Pada（1-4）
  "grahas_in_rashi": {                 // 九 Graha 所在 Rashi（恒星黄道）
    "Surya": "Simha", "Chandra": "Karka", "Mangala": "Mesha",
    "Budha": "Kanya", "Guru": "Dhanus", "Shukra": "Mithuna",
    "Shani": "Kumbha", "Rahu": "Vrishabha", "Ketu": "Vrischika"
  },
  "d1_houses": {},                     // D1 本命盘行星入宫（整宫制 Whole Sign）
  "d9_navamsha": {},                   // D9 九分盘行星位置（可选，婚恋/灵魂契约验证用）
  "current_dasha": "Guru Mahadasha",   // 当前大运（可选，应期分析用）
  "question_type": "yoga"              // lagna / graha / nakshatra / dasha / yoga / d9 / 综合
}
```

**关键前提**：出生日期时间必须精确到分钟并做夏令时（DST）校正，否则 Lagna 每约 2 小时走一宫，误差极大。Rahu/Ketu 为月球交点（非实体行星），与 Surya~Shani 并列计入九 Graha。

---

## 4. 核心断法步骤

### Step 1：确定 Lagna 上升与 Rashi 月亮星座

- **Lagna（Ascendant / 命宫）**：出生时东方地平线升起的恒星黄道星座，是整张 D1 盘的第一宫（Bhava 1），代表身体、外形、自我呈现与人生起点。
- **Rashi（月亮星座）**：出生时月亮所在的恒星黄道星座，是吠陀传统的第二参照系（与 Lagna 并列"双锚"），代表心意、情绪、潜意识。
- 先立坐标系：确认全盘使用 **Lahiri 恒星黄道**，与西方热带黄道差约 **24°**（不做星座翻译）。
- 整宫制（Whole Sign Bhava）为 Parashari 主流口径：Lagna 所在 Rashi 即第 1 宫，其余宫位顺次排列。

### Step 2：D1 本命盘行星入宫与庙旺落陷判定

- 列出九 Graha 在十二 Rashi 与十二 Bhava 的位置。
- 判定每颗 Graha 的 ** dignity（尊严状态）**：
  - **庙旺（Exaltation / Ucha）**：最强；**落陷（Debilitation / Neecha）**：最弱。
  - **入垣 / 自己守护（Own Sign / Swakshetra）**：次强；**友 / 敌 / 中性宫**：一般。
  - **Moolatrikona（根本三角）**：介于庙旺与 own sign 之间。
- Graha 吉凶**不固定**，须"四者合参"：位置（宫）＋关联（相位 / 合相）＋分盘（D9 等）＋Dasha（时间）。Rahu/Ketu/Shani **不得**渲染为凶星。

### Step 3：D9 九分盘（Navamsha）验证婚恋与灵魂契约

- 计算：每个 Rashi 30° 均分为 9 份，每份 3°20′，重排星图。
- 传统格言：**D1 是花，D9 是果**。D1 看似得位的 Graha 若在 D9 失势，其象征力量打折。
- **内外对照**：同一 Graha 在 D1 与 D9 状态一致 → "内外合"；不一致 → "内外有别"。
- **Vargottama**：某 Graha 在 D1 与 D9 同 Rashi，读作稳定、内外一致的象征（非"祝福"）。
- D9 第七宫 / Dara Pada 用于婚姻与深层关系的**对话入口**——但单宫不立断，须 D1/D9 合参；**禁止**用 D9 判断婚姻成败、配偶外貌 / 性格 / 职业。

### Step 4：Nakshatras 二十七宿定位（含 Pada 四分）

- 黄道带按月亮每日运行约 **13°20′** 分 27 段（27 × 13°20′ = 360°）。
- **Janma Nakshatra（生宿）**：出生时月亮所在宿，是个人气质与时间展开的象征锚点，**决定 Vimshottari Dasha 起点**。
- 每宿分 **4 个 Pada（步）**，每 Pada 3°20′，Pada 与 Navamsha 存在对应。
- 把生宿读作"月亮气质"的隐喻词汇库，**禁止**简化为 27 种性格标签，**禁止**用 Yoni 动物 / 神祇象征做现实判决。

### Step 5：Dasha 大运系统（Vimshottari 百二十分期为主）

- **Vimshottari Dasha**：总周期 **120 年**，由九 Graha 分段主掌，从 Janma Nakshatra 起算。
- 层级：**Mahadasha（主大运，年）→ Antardasha（子运，月）→ Pratyantardasha（孙运）**。
- 静态 Yoga 结构在 Dasha 大运中被"点亮"——某 Graha 的 Mahadasha 期间，该 Graha 所主宫位与象征主题被激活。
- 应期读法：Dasha 主 Graha 与 Lagna / 月亮的关系（角宫主 / 三角宫主 /  dusthana 宫主）决定该期基调，但**只读季节不写剧本**。

### Step 6：Yogas 格局判定（Raja / Dhana / Gajakesari 等）

- **Raja Yoga（王瑜伽）**：角宫主（1/4/7/10）与三角宫主（1/5/9）发生关联 → 自主与责任的组合。
- **Dhana Yoga（财富瑜伽）**：资源宫主（2/11）与三角 / 角宫主关联 → 资源流动顺畅意象。
- **Gajakesari Yoga（象狮瑜伽）**：Chandra（月）与 Guru（木）呈角位（1/4/7/10） → 月木互照。
- **Pancha Mahapurusha Yoga（五大人人格瑜伽）**：Mangala/Budha/Guru/Shukra/Shani 各自在 own/exalt 且居角宫（Ruchaka/Bhadra/Hamsa/Malavya/Sasa）。
- 另见 Budha-Aditya（水日合）、Parivartana（互换）、Kemadruma（月两侧空）、Neecha Bhanga（落陷取消）、Vipareeta Raja（反向王瑜伽）。
- **Yoga 是模式语言不是成绩单**：禁止用 Yoga 数量堆砌奉承；"王/财/福"现代化为"自主/资源流动/自我实现"。

### Step 7：综合论断

按"Lagna 锚定 → Graha 入宫与尊严 → D9 内外对照 → Nakshatra 气质 → Dasha 时间点亮 → Yoga 结构叠加"六层合参，输出一段**镜像式综合描述**：哪几股力量同时在场、当下被哪个 Dasha 主题激活、内外是否一致。落点始终是"自我观察的隐喻入口"，不给宿命判决。

---

## 5. 经典判例引用

> 完整 12 例见 [cases.md](./cases.md)，此处列 5 例索引（BPHS / Jaimini 为公版古典梵文典籍）：

1. **[BPHS·Graha  dignity 章]**：Graha 在 Ucha / Swakshetra / Moolatrikona 为有力，在 Neecha / dusthana 为弱力；但吉凶须四者合参，不孤立断吉凶。
2. **[BPHS·Navamsha 章]**：D1 为花、D9 为果；Graha 在 D1 有力而 D9 无力者，其果实不熟——Vargottama（D1=D9 同座）为内外一致之征。
3. **[BPHS·Nakshatra 章]**：二十七宿各 13°20′，Janma Nakshatra 由月亮定位，Vimshottari Dasha 一百二十年周期即从此起算。
4. **[BPHS·Yoga 章]**：角宫主与三角宫主相会成 Raja Yoga，象征自主与领导力；财富宫主（2/11）与三角主相会成 Dhana Yoga。
5. **[Jaimini Sutras·Drishti 章]**：Graha 以 Drishti（对视 / aspect）作用于所照宫位，非以合相为唯一关联；Jaimini 体系另以 Karaka（象征星）与 Pada 论断。

---

## 6. 输出格式规范

```json
{
  "skill": "vedic-divination",
  "zodiac_system": "sidereal",
  "ayanamsa": "Lahiri",
  "lagna": { "rashi": "Simha", "degree": "12.40", "house": 1 },
  "chandra_moon": { "rashi": "Karka", "janma_nakshatra": "Pushya", "pada": 2, "nakshatra_lord": "Shani" },
  "grahas": [
    { "name": "Guru", "rashi": "Dhanus", "house": 5, "dignity": "Swakshetra", "aspect_on": [9, 11] }
  ],
  "d9_navamsha": {
    "lagna": "Makara",
    "vargottama": ["Guru", "Shukra"],
    "note": "Guru D1/D9 同座，内外一致；D9 第7宫状态见 cases.md"
  },
  "active_dasha": { "mahadasha": "Guru", "antardasha": "Shani", "lord_house": 5 },
  "yogas_hit": [
    { "name": "Gajakesari Yoga", "condition": "Chandra 与 Guru 角位", "tone": "心智清明、受人敬重的镜像" }
  ],
  "synthesis": "Lagna 狮子 + 月亮巨蟹，自我呈现外向而情绪内核滋养；Guru 大运期间第五宫智慧/创造主题被点亮；盘内 Raja Yoga 提示自主与责任并存的张力。",
  "source_cases": ["[BPHS·Navamsha 章]", "[BPHS·Yoga 章]", "[Jaimini·Drishti 章]"],
  "boundary_notes": "恒星黄道(Lahiri)，不与热带黄道混用；征象为自我观察镜像，非宿命判决；Rahu/Ketu/Shani 不作凶星渲染。"
}
```

---

## 7. 注意事项与边界

1. **恒星黄道 vs 回归黄道**：本技能一律用 Lahiri 恒星黄道，与西方 Tropical 差约 24°。**禁止**把西方盘度数直接套入吠陀术语，**禁止**"星座翻译"（如热带巨蟹=吠陀双子），不评价两体系优劣。
2. **坐标系物理隔离**：西方盘数据提问时先提示 24° 岁差差，不直接套用。
3. **夏令时校正**：出生时间必须做 DST 校正；Lagna 约 2 小时走一宫，时间错 1 小时上升可能错一宫，全盘重排。
4. **Graha 非吉凶二分**：Rahu=执念/扩张，Ketu=出离/切断，Shani=延迟/纪律；**不得**渲染为凶星恐吓用户，Guru 也非纯吉（过犹不及）。
5. **D9 不立婚姻断**：D9 是关系对话工具不是审批表；禁止判断婚姻成败、配偶外貌性格职业；"业力"仅作"重复模式"隐喻，不作前世判决。
6. **Yoga 非成绩单**：禁止用 Yoga 数量堆砌奉承或自我否定；前现代"王/财/福"须现代化为"自主/资源流动/自我实现"。
7. **Nakshatra 拒标签化**：不把 27 宿扁平化 27 种性格标签，不用生宿做性格判决。
8. **象征层只读**：盘图是自我观察的隐喻镜子，不构成医疗 / 法律 / 财务 / 婚恋决策依据；置信带硬锁低区间，is_actionable 恒为 false。

---

*本技能为 Parashari 吠陀占星（Lahiri 恒星黄道）体系，核心概念取自 BPHS / Jaimini 公版梵文典籍，现代心理对齐已蒸馏为镜像式断法。速查表见 [reference.md](./reference.md)，判例见 [cases.md](./cases.md)。*
