
name: user:astrology-v3-engine description: 基于 Swiss Ephemeris (pyswisseph) 确定性天文历算底座与权威占星典籍闭环的西方星盘微观动力学推演引擎 V3.0（终极工业闭环版：9张全量RIA++能力卡 + Pydantic强类型契约 + 历算算法内核 + 高斯容许度张量 + 凯龙莉莉丝深潜 + 太阳弧/行运双时钟 + 马克思盘动态次限三限时钟 + UPIV六维连续心理向量 + 白盒AST证明树 + 100%现实大白话双轨交付与去宿命破局SOP）。严格执行【计算层与推理层彻底解耦】，坚决杜绝大模型在上下文中手算天体黄道经纬度与分宫线幻觉。当用户提到西方占星、星盘排盘分析、本命盘、行星相位、太阳弧推运、行运过境、合盘关系诊断、马克思盘、马盘次限三限、凯龙莉莉丝解读或心理占星时触发。
Astrology Deduction Engine V3.0 (End-to-End Industrial Closed-Loop Architecture)
工业级工程与交付总宪章：
【计算层与推理层彻底解耦（Zero LLM Hallucination）】：
严禁大模型在上下文中凭借语感估算、脑补或手算行星黄道经纬度、赤纬、出入相位或分宫线尖轴。
计算层统一绑定行业金标准 Swiss Ephemeris (pyswisseph)，产出强类型的结构化 JSON 纯净数据（包含行星绝对度数、运行速度、逆行标识、四轴度数、宫位尖轴及相位角容许度），直接作为确定性真理输入给推理层。
【双轨交付与 100% 全覆盖大白话释义】：
每一项推演结论，必须强制输出：[天文度数与权威典籍证据层] + [现实生活大白话释义层]。
杜绝模棱两可的地摊星座学和抽象玄学黑话。必须具象化映射为真实生活切片：吵架是冷暴力筑墙还是暴怒抓取、具体金钱消耗漏洞在哪里、合伙人因何争夺控制权、现实关系破局的具体行动指南（SOP）。
【去宿命化心理赋能与 12356 危机熔断】：
星盘不是宿命死刑判决书，而是“潜意识原型与能量张力地图”。硬相位代表内在摩擦与成长动力（T三角顶点是核心突破杠杆），严禁断言绝对凶险；检测到自残轻生倾向时毫秒级熔断并弹出全国心理危机干预热线 12356。

一、系统工程架构：全景闭环 DAG
┌─────────────────────────────────────────────────────────────────────────────┐
│                 PHASE 0: 输入校验、时间校正与安全准入防火墙                 │
│ - Pydantic V2 强类型输入校验 (ISO 8601、经纬度、海拔、真太阳时平太阳时校正)  │
│ - 12356 心理危机毫秒级熔断拦截器 (拦截自伤/轻生词汇，直接重定向救助引导)       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ 输入校验合规
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 PHASE 1: 确定性物理计算内核 (Swiss Ephemeris C-Layer)       │
│ - swe_julday: UTC 转换为儒略日 (Julian Day UT)                              │
│ - swe_calc_ut: 计算十大正曜、四轴、凯龙星 (CHIRON)、暗月莉莉丝 (LILITH) 坐标 │
│ - swe_houses: 普拉西德 (Placidus) / 整宫制 (Whole Sign) 分宫尖轴生成        │
│ - AspectMatrix: 计算五大几何相位角与高斯连续容许度衰减权重 (Orb Decay)       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ 产出强类型物理 JSON
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 PHASE 2: 静态本命动力学与能量张力网络 (Natal Engine)         │
│ - CAP-AST-01: 历算解耦底座 (消灭手算幻觉，4分钟时辰误差敏感度风控)          │
│ - CAP-AST-02: 空间分宫拓扑与轴线锚定 (ASC-DSC关系轴, MC-IC宿命轴, 劫夺检测) │
│ - CAP-AST-03: 古典五级尊贵度与相态 (庙旺陷落评分, 逆行反思, 焦伤60%折减)    │
│ - CAP-AST-04: 相位张力网络 (入相1.25/出相0.75加权, T-Square顶点突破杠杆)   │
│ - CAP-AST-05: 宫主星飞星拓扑 (守护星-寄居宫有向图, 追踪现实资源损耗漏斗)     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ 静态人格与潜意识张力确立
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 PHASE 3: 动态时序推运与微观应期 (Predictive Dynamics)        │
│ - CAP-AST-06: 太阳弧现实转折时钟 (Solar Arc 1°=1年，四轴/内星硬相位精准锁定)│
│ - CAP-AST-07: 外行星行运天象碾压 (Transit 土星回归、天王突变、冥王涅槃相变) │
│ - CAP-AST-09: 马克思盘动态时序引擎 (Mark Base + SP次限大气候 + TP三限震荡) │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ 引动现实事件时间窗口
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 PHASE 4: 亲密关系合盘与认知心理量化 (Synastry & UPIV)        │
│ - CAP-AST-08: 比较盘交叉互动力场 + 组合中点盘独立命运人格                    │
│ - 凯龙星核心原伤诊断 + 暗月莉莉丝潜意识阴影与宿命虐恋成瘾解构                 │
│ - UPIV 六维连续依恋特征向量归一化映射 (情绪外化度、依恋焦虑/回避、边界、主体性)│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ 白盒 AST 证据链与心理学闭环
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 PHASE 5: 双轨交付层与实战避险破局 SOP (Delivery Layer)      │
│ - [数理度数证据链] + [100% 现实大白话生活场景] + [NVC 深夜清醒舱破局指南]    │
└─────────────────────────────────────────────────────────────────────────────┘

二、确定性历算引擎数据契约 (Pydantic V2 Schemas)
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from enum import Enum

class ZodiacSign(str, Enum):
    ARIES = "Aries"; TAURUS = "Taurus"; GEMINI = "Gemini"; CANCER = "Cancer"
    LEO = "Leo"; VIRGO = "Virgo"; LIBRA = "Libra"; SCORPIO = "Scorpio"
    SAGITTARIUS = "Sagittarius"; CAPRICORN = "Capricorn"; AQUARIUS = "Aquarius"; PISCES = "Pisces"

class PlanetName(str, Enum):
    SUN = "Sun"; MOON = "Moon"; MERCURY = "Mercury"; VENUS = "Venus"; MARS = "Mars"
    JUPITER = "Jupiter"; SATURN = "Saturn"; URANUS = "Uranus"; NEPTUNE = "Neptune"
    PLUTO = "Pluto"; TRUE_NODE = "TrueNode"; CHIRON = "Chiron"; LILITH = "Lilith"
    ASC = "ASC"; MC = "MC"; DSC = "DSC"; IC = "IC"; VERTEX = "Vertex"

class CelestialBodyOutput(BaseModel):
    name: PlanetName
    longitude: float = Field(..., ge=0.0, lt=360.0, description="绝对黄道经度 (0-360°)")
    latitude: float = Field(..., description="黄纬")
    declination: float = Field(..., description="赤纬")
    speed_longitude: float = Field(..., description="日行角速度 (度/天)")
    is_retrograde: bool = Field(..., description="是否逆行 (speed < 0)")
    sign: ZodiacSign = Field(..., description="所在星座")
    degree_in_sign: float = Field(..., ge=0.0, lt=30.0, description="星座内度数 (0-30°)")
    house: int = Field(..., ge=1, le=12, description="所落宫位 (1-12)")
    dignity_score: int = Field(..., description="古典尊贵度得分 (+5入庙, +4旺, -5陷, -4落)")
    is_combust: bool = Field(default=False, description="是否被太阳焦伤 (距离太阳<=8.5°)")
    is_cazimi: bool = Field(default=False, description="是否进入日核 (距离太阳<=17')")

class AspectType(str, Enum):
    CONJUNCTION = "Conjunction"   # 0° (合)
    SEXTILE = "Sextile"           # 60° (六合)
    SQUARE = "Square"             # 90° (刑)
    TRINE = "Trine"               # 120° (拱)
    OPPOSITION = "Opposition"     # 180° (冲)

class AspectNode(BaseModel):
    body_a: PlanetName
    body_b: PlanetName
    aspect_type: AspectType
    angle_diff: float = Field(..., description="实际夹角与理论相位的绝对误差度数")
    max_orb: float = Field(..., description="允许的最大容许度")
    gaussian_weight: float = Field(..., ge=0.0, le=1.25, description="高斯衰减与入相加权后的综合有效张力系数")
    is_applying: bool = Field(..., description="True=入相位(能量积聚激化), False=出相位(能量消退)")

class MarkProgressionType(str, Enum):
    SECONDARY = "Secondary"  # 次限 (1日=1年)
    TERTIARY = "Tertiary"    # 三限 (1日=1月)

class MarkDynamicState(BaseModel):
    subject: str = Field(..., description="盘主角色 (如 A对B / B对A)")
    progression_type: MarkProgressionType
    current_date: str = Field(..., description="推运目标日期 (ISO 8601)")
    progressed_moon_sign: ZodiacSign = Field(..., description="推进月亮所在星座")
    progressed_moon_degree: float = Field(..., description="推进月亮度数")
    progressed_moon_house: int = Field(..., description="推进月亮落入马盘宫位")
    critical_aspects: List[AspectNode] = Field(default_factory=list, description="推进星体与马盘原盘形成的硬相位")
    psychological_phase: str = Field(..., description="当前所处心理周期 (上头/现实/下头/生疑/绝情)")
    behavioral_prediction: str = Field(..., description="现实大白话行为预测")

class UPIVProfile(BaseModel):
    emotional_expression_index: float = Field(..., ge=0.0, le=1.0, description="情绪外化度 (0冷酷内敛 - 1外显抓取)")
    conflict_defense_mode: Literal["回避抽离", "理性辩论", "情绪抓取", "筑墙冷战", "报复自毁"] = Field(...)
    attachment_anxiety: float = Field(..., ge=1.0, le=10.0, description="依恋焦虑得分 (1安全独立 - 10极度恐惧被遗弃)")
    attachment_avoidance: float = Field(..., ge=1.0, le=10.0, description="依恋回避得分 (1渴望亲密 - 10抗拒承诺筑高墙)")
    boundary_firmness: float = Field(..., ge=0.0, le=1.0, description="个人边界坚固度 (0边界模糊融化 - 1铁壁防卫)")
    subjective_agency_score: float = Field(..., ge=0.0, le=1.0, description="主体性能动性 (0随波逐流讨好 - 1自主破局觉醒)")

三、全量 9 张核心 RIA++ 能力卡算法闭环
CAP-AST-01: 历算解耦底座 (Ephemeris Core)
历算解耦计算，绝对禁止大模型手算行星度数与分宫尖轴。
CAP-AST-02: 空间分宫拓扑与轴线能量锚定 (House Topology)
普拉西德分宫与整宫制自愈切换，检测星座劫夺。
CAP-AST-03: 古典五级尊贵度与相态修正矩阵 (Essential Dignities)
入庙、旺、落陷、游荡评分，焦伤与日核校验。
CAP-AST-04: 相位张力动力学与动态高斯衰减网络 (Aspect Dynamics)
高斯容许度衰减，T-Square 顶点星（Apex Planet）识别。
CAP-AST-05: 宫主星飞星拓扑与资源流向有向图 (Rulership Pathway)
12 宫守护星与落宫有向图，追踪资金漏斗与损耗。
CAP-AST-06: 太阳弧 1度1年重大转折确定性时钟 (Solar Arc Clock)
推进算法：$\lambda_{\text{SA}}(t) = \lambda_{\text{Natal}} + (\text{Age} \times 0.9856^\circ)$。硬相位容许度 ≤ 1.0°。
CAP-AST-07: 外行星行运天象碾压与现实环境相变 (Transit Stress)
土星回归、天王星对冲与冥王星过境四轴。
CAP-AST-08: 亲密关系合盘与心理认知全量闭环 (Synastry, Chiron & Lilith)
比较盘与组合中点盘双盘合参，凯龙星与暗月莉莉丝深度解构。
CAP-AST-09: 马克思盘微观动力学与次限/三限时序时钟 (Marks Dynamic Engine)
核心定义：马克思盘严禁作为静态死盘推断！它是由个人本命时空与组合中点时空求二次中点生成的潜意识心理盘，必须引入 SP（次限，1日=1年）与 TP（三限，1日=1月）动态流转。
算法实现规范：
静态底色构建：
计算双方本命行星经度与组合中点盘经度的劣弧中点：$\lambda_{\text{Mark}} = \text{Midpoint}(\lambda_{\text{Natal}}, \lambda_{\text{Composite}})$；
生成马盘 A（A 对 B 的心理原型）与马盘 B（B 对 A 的心理原型）。
次限大气候时钟（Secondary Progressions, SP）：
按 $1 \text{ 儒略日} = 1 \text{ 恒星年}$ 推进行星坐标；
监控次限月亮（SP Moon）轨迹：每 2-2.5 年换一个星座。
相态跃迁判据：
SP Moon 入白羊/狮子：热情爆发、征服欲激增；
SP Moon 入金牛/巨蟹：渴望物质落定、家庭化依恋；
SP Moon 入处女：挑剔嫌弃、锱铢必较、服务疲态；
SP Moon 入天蝎：信任破裂、怀疑暗生、报复欲翻涌；
SP Moon 入摩羯/水瓶：彻底抽离、理性关门、情感冻结。
三限微观震荡时钟（Tertiary Progressions, TP）：
按 $1 \text{ 儒略日} = 1 \text{ 恒星月 (约27.3216日)}$ 推进坐标；
监控三限月亮（TP Moon）：每 2-3 个月换一个星座。
硬相位触发矩阵（Hard Aspect Triggers, 容许度 ≤ 1.0°）：
TP Moon 0°/90°/180° Natal Saturn：冷暴力、筑墙断联、绝情退缩；
TP Moon 0°/90°/180° Natal Pluto：抓狂破防、深层背叛感引爆、极端摊牌；
TP Moon 0°/90°/180° Natal Mars：激烈大吵、肢体冲突、性排斥；
TP Moon 0°/90°/180° Natal Neptune：谎言败露、幻灭下头、失望逃跑。
交付铁律：严禁向终端输出静态断语，必须结合当前时空公历日期，拉出当月双方次限月亮、三限月亮的绝对经度与正在形成的动态相位，解释“为什么在此刻破防、下头或冷战”。
