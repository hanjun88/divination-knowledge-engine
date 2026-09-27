"""
纳甲纳支 + 六亲装配 + 六神安起 (B2)

依据京房纳甲法：
  - 八宫各卦的地支按"内卦三爻 / 外卦三爻"排列（初爻 -> 上爻）。
  - 天干纳甲：乾纳甲壬(内甲外壬)、坤纳乙癸(内乙外癸)、艮丙、兑丁、坎戊、
    离己、震庚、巽辛（后六宫内外卦同干）。
  - 六亲以本宫五行为"我"：生我=父母，我生=子孙，克我=官鬼，我克=妻财，同我=兄弟。
  - 六神以日干起初爻，依次上行：甲乙青龙、丙丁朱雀、戊勾陈、己螣蛇、庚辛白虎、壬癸玄武。
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# 基础常量表
# ---------------------------------------------------------------------------

#: 十二地支五行
ZHI_WX: Dict[str, str] = {
    "子": "水",
    "丑": "土",
    "寅": "木",
    "卯": "木",
    "辰": "土",
    "巳": "火",
    "午": "火",
    "未": "土",
    "申": "金",
    "酉": "金",
    "戌": "土",
    "亥": "水",
}

#: 八宫本宫五行
PALACE_WX: Dict[str, str] = {
    "乾宫": "金",
    "兑宫": "金",
    "离宫": "火",
    "震宫": "木",
    "巽宫": "木",
    "坎宫": "水",
    "艮宫": "土",
    "坤宫": "土",
}

#: 京房纳甲表：内卦=初/二/三爻，外卦=四/五/上爻（从初爻到上爻）
NAJIA_TABLE: Dict[str, Dict[str, object]] = {
    "乾宫": {
        "inner": ["子", "寅", "辰"],
        "outer": ["午", "申", "戌"],
        "gan_inner": "甲",
        "gan_outer": "壬",
    },
    "坤宫": {
        "inner": ["未", "巳", "卯"],
        "outer": ["丑", "亥", "酉"],
        "gan_inner": "乙",
        "gan_outer": "癸",
    },
    "艮宫": {
        "inner": ["辰", "午", "申"],
        "outer": ["戌", "子", "寅"],
        "gan_inner": "丙",
        "gan_outer": "丙",
    },
    "兑宫": {
        "inner": ["巳", "卯", "丑"],
        "outer": ["亥", "酉", "未"],
        "gan_inner": "丁",
        "gan_outer": "丁",
    },
    "坎宫": {
        "inner": ["寅", "辰", "午"],
        "outer": ["申", "戌", "子"],
        "gan_inner": "戊",
        "gan_outer": "戊",
    },
    "离宫": {
        "inner": ["卯", "丑", "亥"],
        "outer": ["酉", "未", "巳"],
        "gan_inner": "己",
        "gan_outer": "己",
    },
    "震宫": {
        "inner": ["子", "寅", "辰"],
        "outer": ["午", "申", "戌"],
        "gan_inner": "庚",
        "gan_outer": "庚",
    },
    "巽宫": {
        "inner": ["丑", "亥", "酉"],
        "outer": ["未", "巳", "卯"],
        "gan_inner": "辛",
        "gan_outer": "辛",
    },
}

# 五行相生: a 生 b
_WX_SHENG: Dict[str, str] = {
    "木": "火",
    "火": "土",
    "土": "金",
    "金": "水",
    "水": "木",
}
# 五行相克: a 克 b
_WX_KE: Dict[str, str] = {
    "木": "土",
    "土": "水",
    "水": "火",
    "火": "金",
    "金": "木",
}

#: 六神固定顺序（循环）
LIUSHEN_ORDER: List[str] = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]

#: 日干 -> 初爻起始六神在 LIUSHEN_ORDER 中的下标
_DAY_GAN_START: Dict[str, int] = {
    "甲": 0, "乙": 0,          # 青龙
    "丙": 1, "丁": 1,          # 朱雀
    "戊": 2,                    # 勾陈
    "己": 3,                    # 螣蛇
    "庚": 4, "辛": 4,          # 白虎
    "壬": 5, "癸": 5,          # 玄武
}


# ---------------------------------------------------------------------------
# 八宫 binary -> palace 查找表（用于变卦纳甲）
# ---------------------------------------------------------------------------
# 纯卦（八纯卦），二进制列表下标 0=初爻 ... 5=上爻，1=阳 0=阴
_PURE_BINARY: Dict[str, List[int]] = {
    "乾宫": [1, 1, 1, 1, 1, 1],
    "兑宫": [1, 1, 0, 1, 1, 0],
    "离宫": [1, 0, 1, 1, 0, 1],
    "震宫": [1, 0, 0, 1, 0, 0],
    "巽宫": [0, 1, 1, 0, 1, 1],
    "坎宫": [0, 1, 0, 0, 1, 0],
    "艮宫": [0, 0, 1, 0, 0, 1],
    "坤宫": [0, 0, 0, 0, 0, 0],
}

#: 每宫八卦相对纯卦所翻转的爻位下标集合（0=初爻）
#: 纯卦(六世) / 一世 / 二世 / 三世 / 四世 / 五世 / 游魂 / 归魂
_FLIP_SETS: List[set] = [
    set(),            # 纯卦
    {0},              # 一世
    {0, 1},           # 二世
    {0, 1, 2},        # 三世
    {0, 1, 2, 3},     # 四世
    {0, 1, 2, 3, 4},  # 五世
    {0, 1, 2, 4},     # 游魂（五世后将四爻翻回）
    {4},              # 归魂（游魂后将下卦三爻翻回）
]

#: 二进制六爻序列 -> 八宫名
BINARY_TO_PALACE: Dict[Tuple[int, ...], str] = {}
for _palace, _pure in _PURE_BINARY.items():
    for _flips in _FLIP_SETS:
        _lines = [(1 - b) if i in _flips else b for i, b in enumerate(_pure)]
        BINARY_TO_PALACE[tuple(_lines)] = _palace
del _palace, _pure, _flips, _lines


# ---------------------------------------------------------------------------
# 纳甲函数
# ---------------------------------------------------------------------------

def najia_for_palace(palace: str, yao_pos: int) -> Tuple[str, str]:
    """根据八宫和爻位(1-6)返回(天干, 地支)。

    1-3 爻为内卦（下卦），4-6 爻为外卦（上卦）。
    """
    if palace not in NAJIA_TABLE:
        raise ValueError(f"未知宫位: {palace!r}")
    if not 1 <= yao_pos <= 6:
        raise ValueError(f"爻位必须在 1-6 之间: {yao_pos!r}")

    entry = NAJIA_TABLE[palace]
    if yao_pos <= 3:
        zhi = entry["inner"][yao_pos - 1]  # type: ignore[index]
        gan = entry["gan_inner"]           # type: ignore[assignment]
    else:
        zhi = entry["outer"][yao_pos - 4]  # type: ignore[index]
        gan = entry["gan_outer"]           # type: ignore[assignment]
    return gan, zhi


# ---------------------------------------------------------------------------
# 六亲装配
# ---------------------------------------------------------------------------

def assign_liuqin(palace_wx: str, yao_wx: str) -> str:
    """以本宫五行为"我"，判定六亲。

    生我者=父母, 我生者=子孙, 克我者=官鬼, 我克者=妻财, 同我者=兄弟。
    """
    if yao_wx == palace_wx:
        return "兄弟"
    if _WX_SHENG.get(palace_wx) == yao_wx:   # 我生
        return "子孙"
    if _WX_SHENG.get(yao_wx) == palace_wx:   # 生我
        return "父母"
    if _WX_KE.get(palace_wx) == yao_wx:      # 我克
        return "妻财"
    if _WX_KE.get(yao_wx) == palace_wx:      # 克我
        return "官鬼"
    raise ValueError(f"未知五行: palace_wx={palace_wx!r}, yao_wx={yao_wx!r}")


# ---------------------------------------------------------------------------
# 六神安起
# ---------------------------------------------------------------------------

def assign_liushen(day_gan: str, yao_pos: int) -> str:
    """以日干起初爻，依次上行安六神。

    甲乙日初爻青龙；丙丁日初爻朱雀；戊日初爻勾陈；己日初爻螣蛇；
    庚辛日初爻白虎；壬癸日初爻玄武。六神顺序循环。
    """
    if day_gan not in _DAY_GAN_START:
        raise ValueError(f"未知日干: {day_gan!r}")
    if not 1 <= yao_pos <= 6:
        raise ValueError(f"爻位必须在 1-6 之间: {yao_pos!r}")
    start = _DAY_GAN_START[day_gan]
    idx = (start + (yao_pos - 1)) % 6
    return LIUSHEN_ORDER[idx]


# ---------------------------------------------------------------------------
# 变爻纳支
# ---------------------------------------------------------------------------

def find_palace_of_binary(binary: List[int]) -> str:
    """由六爻阴阳序列(1=阳,0=阴, 下标0=初爻)反查八宫。"""
    key = tuple(binary)
    if key not in BINARY_TO_PALACE:
        raise ValueError(f"无法确定宫位的卦象二进制: {binary!r}")
    return BINARY_TO_PALACE[key]


def bian_zhi_for_yao(palace: str, yao_pos: int, bian_binary: List[int]) -> str:
    """计算动爻变后的地支（变卦对应爻位的纳甲地支）。

    变卦可能属于不同宫位，需先由 bian_binary 反查变卦所属宫位，再取该宫
    对应爻位的纳甲地支。``palace`` 为本卦宫位（上下文/兜底用）。
    """
    bian_palace = find_palace_of_binary(bian_binary)
    _, zhi = najia_for_palace(bian_palace, yao_pos)
    return zhi


def zhi_to_wx(zhi: str) -> str:
    """地支 -> 五行（便捷查表）。"""
    if zhi not in ZHI_WX:
        raise ValueError(f"未知地支: {zhi!r}")
    return ZHI_WX[zhi]
