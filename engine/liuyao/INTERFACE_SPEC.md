# 六爻纳甲排盘内核 — 模块接口规范 (v1.0)

> 本规范定义 liuyao 包内各模块的数据结构与函数契约。
> B1/B2/B3/B4 四个子代理按此规范并行实现，最终由 cast.py 端到端集成。

## 目录结构

```
engine/liuyao/
├── __init__.py          # 包导出 + 共享数据模型
├── hexagram.py          # B1: 成卦算法 + 八宫世应定位
├── najia.py             # B2: 纳甲纳支 + 六亲装配 + 六神安起
├── wangshuai.py         # B3: 月建日辰旺衰 + 旬空月破 + 伏神查找
├── dongbian.py          # B4: 动变力学 + 应期法则 + AST输出
└── cast.py              # 端到端口径 (集成层，I1 负责)
```

## 共享数据模型 (定义在 __init__.py)

```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class Yao:
    """单爻状态"""
    pos: int              # 爻位 1-6 (1=初爻, 6=上爻)
    value: int            # 6=老阴, 7=少阳, 8=少阴, 9=老阳
    is_yang: bool         # True=阳爻, False=阴爻
    is_dong: bool         # True=动爻 (6或9)
    # 纳甲结果 (B2填充)
    gan: str = ""         # 天干
    zhi: str = ""         # 地支
    wx: str = ""          # 五行
    liuqin: str = ""      # 六亲 (父母/兄弟/子孙/妻财/官鬼)
    liushen: str = ""     # 六神 (青龙/朱雀/勾陈/螣蛇/白虎/玄武)
    # 变爻 (动爻才有, B2填充)
    bian_zhi: str = ""    # 变爻地支
    bian_wx: str = ""     # 变爻五行
    bian_liuqin: str = "" # 变爻六亲
    # 旺衰 (B3填充)
    wangshuai_score: float = 0.0   # 量化旺衰分
    wangshuai_label: str = "平"     # 旺/相/休/囚/死/平
    xun_kong: bool = False          # 旬空
    yue_po: bool = False            # 月破
    ri_chong: bool = False          # 日冲
    ri_sheng: bool = False          # 日生
    yue_sheng: bool = False         # 月生
    yue_ke: bool = False            # 月克
    ru_mu: bool = False             # 入墓
    # 动变力学 (B4填充)
    dongbian_type: str = ""         # 回头生/回头克/化进/化退/化绝/化空/无
    dongbian_score: float = 0.0     # 动变影响力分

@dataclass
class HexagramInfo:
    """卦象信息"""
    ben_gua_name: str       # 本卦名 (如 "天风姤")
    ben_gua_id: str         # 本卦64卦编号 (1-64)
    bian_gua_name: str      # 变卦名 (无动爻则同本卦)
    bian_gua_id: str        # 变卦编号
    palace: str             # 八宫 (乾宫/坎宫/艮宫/震宫/巽宫/离宫/坤宫/兑宫)
    palace_wx: str          # 本宫五行
    shi_pos: int            # 世爻位置 (1-6)
    ying_pos: int           # 应爻位置 (1-6)
    shi_type: str           # 世爻类型 (一世/二世/三世/四世/五世/游魂/归魂)

@dataclass
class Fushen:
    """伏神信息"""
    pos: int                # 伏神所在爻位
    zhi: str                # 伏神地支
    wx: str                 # 伏神五行
    liuqin: str             # 伏神六亲
    fei_pos: int            # 飞神爻位
    fei_zhi: str            # 飞神地支
    fei_ke_fu: bool         # 飞克伏
    fei_sheng_fu: bool      # 飞生伏

@dataclass
class CastResult:
    """完整排盘结果 (AST)"""
    input_values: List[int]          # 输入 [6,7,8,9,7,8]
    datetime: str                    # 占问时间 ISO
    month_gan: str = ""              # 月建天干
    month_zhi: str = ""              # 月建地支
    day_gan: str = ""                # 日辰天干
    day_zhi: str = ""                # 日辰地支
    day_xun: str = ""                # 日辰旬首 (如 甲子)
    hexagram: Optional[HexagramInfo] = None
    yaos: List[Yao] = field(default_factory=list)
    fushen: Optional[Fushen] = None
    yong_shen_pos: int = 0           # 用神爻位 (由占问域确定)
    ying_qi: Dict[str, Any] = field(default_factory=dict)  # 应期窗口
    summary: Dict[str, Any] = field(default_factory=dict)   # 摘要
```

## 各模块函数契约

### hexagram.py (B1)
```python
def cast_hexagram(values: List[int]) -> Dict[str, Any]:
    """输入6个值(6/7/8/9)，返回本卦/变卦的阴阳序列与编号"""
    # 返回: {"ben_binary": [1,0,1,1,0,1], "bian_binary": [...], "ben_id": int, "bian_id": int}

def find_palace_and_shiying(ben_binary: List[int], bian_binary: List[int]) -> Dict[str, Any]:
    """八宫世应定位，用口诀: 天同二世天变五，地同四世地变初，本宫六世三世异，人同游魂人变归"""
    # 返回: {"palace": str, "palace_wx": str, "shi_pos": int, "ying_pos": int, "shi_type": str}

HEXAGRAM_NAMES: Dict[int, str]  # 64卦名表 key=1..64
```

### najia.py (B2)
```python
def najia_for_palace(palace: str, is_inner: bool, yao_pos: int) -> tuple[str, str]:
    """根据八宫和内外卦、爻位返回纳甲(天干, 地支)"""
    # 乾内子寅辰外午申戌; 坤内未巳卯外丑亥酉; 艮内辰午申外戌子寅; etc.

def assign_liuqin(palace_wx: str, yao_wx: str) -> str:
    """以本宫五行为我，定六亲: 生我=父母, 我生=子孙, 克我=官鬼, 我克=妻财, 同我=兄弟"""

def assign_liushen(day_gan: str, yao_pos: int) -> str:
    """六神安起: 甲乙青龙起初爻, 丙丁朱雀, 戊勾陈, 己螣蛇, 庚辛白虎, 壬癸玄武"""

NAJIA_TABLE: Dict[str, Dict[str, List[str]]]  # 8宫×内外卦×6爻的地支表
```

### wangshuai.py (B3)
```python
def compute_wangshuai(yao_wx: str, month_zhi: str, day_zhi: str, 
                      is_dong: bool = False) -> Dict[str, Any]:
    """月建日辰旺衰评分: 月建+3, 日辰+3, 月生+1.5, 日生+1.5, 月克-2, 日克-1.5"""
    # 返回: {"score": float, "label": str, "yue_sheng": bool, "yue_ke": bool, ...}

def check_xun_kong(day_xun: str, zhi: str) -> bool:
    """旬空判定: 日辰旬首对应的空亡地支"""

def check_yue_po(month_zhi: str, zhi: str) -> bool:
    """月破判定: 与月建相冲"""

def find_fushen(yaos: List[Yao], palace: str, target_liuqin: str) -> Optional[Dict]:
    """用神不现时，从本宫纯卦对应爻位找伏神"""
```

### dongbian.py (B4)
```python
def analyze_dongbian(yao: Yao, month_zhi: str, day_zhi: str) -> Dict[str, Any]:
    """动变力学分析: 回头生(+2.5)/回头克(-3.0)/化进(+1.5)/化退(-1.5)/化绝(-2)/化空(-1)"""
    # 返回: {"type": str, "score": float, "detail": str}

def compute_yingqi(yaos: List[Yao], yong_shen_pos: int, 
                   month_zhi: str, day_zhi: str) -> Dict[str, Any]:
    """16应期法则状态机: 静而逢冲, 动而逢合, 空而逢值, 破而逢合..."""
    # 返回: {"primary_window": str, "secondary_windows": [...], "method": str}

def build_ast(cast_result: CastResult) -> Dict[str, Any]:
    """输出标准化AST JSON，对接规则引擎的facts格式"""
```

## 量化评分模型 (deep_distill_v2 沿用)

| 因素 | 分值 |
|------|------|
| 临月建 | +3.0 |
| 临日辰 | +3.0 |
| 月建生 | +1.5 |
| 日辰生 | +1.5 |
| 月建克 | -2.0 |
| 日辰克 | -1.5 |
| 回头生 | +2.5 |
| 回头克 | -3.0 |
| 化进神 | +1.5 |
| 化退神 | -1.5 |
| 化绝 | -2.0 |
| 化空 | -1.0 |
| 旬空(真空) | -5.0 |
| 月破 | -3.0 |
| 入墓 | -1.0 |

旺衰标签阈值: score>=4 旺, 2~4 相, -1~2 平, -3~-1 囚, <=-3 死
