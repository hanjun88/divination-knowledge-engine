"""
hexagram.py — 六爻排盘内核 B1 模块

职责:
  1. 64 卦表 (HEXAGRAM_NAMES) 与二进制反查表 (BINARY_TO_ID)
  2. 成卦算法 cast_hexagram: 由 6 个爻值(6/7/8/9)推出本卦/变卦
  3. 八宫世应定位 find_palace_and_shiying: 京房八宫归属与世应爻位

爻位约定:
  - values 顺序从初爻(1)到上爻(6)
  - binary 列表顺序同样从初爻到上爻, 1=阳, 0=阴
  - tuple key = (初爻, 二爻, 三爻, 四爻, 五爻, 上爻)
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
# 1. 64 卦名表 (周易卦序 1-64)
# ---------------------------------------------------------------------------
HEXAGRAM_NAMES: Dict[int, str] = {
    1: "乾为天", 2: "坤为地", 3: "水雷屯", 4: "山水蒙",
    5: "水天需", 6: "天水讼", 7: "地水师", 8: "水地比",
    9: "风天小畜", 10: "天泽履", 11: "地天泰", 12: "天地否",
    13: "天火同人", 14: "火天大有", 15: "地山谦", 16: "雷地豫",
    17: "泽雷随", 18: "山风蛊", 19: "地泽临", 20: "风地观",
    21: "火雷噬嗑", 22: "山火贲", 23: "山地剥", 24: "地雷复",
    25: "天雷无妄", 26: "山天大畜", 27: "山雷颐", 28: "泽风大过",
    29: "坎为水", 30: "离为火", 31: "泽山咸", 32: "雷风恒",
    33: "天山遁", 34: "雷天大壮", 35: "火地晋", 36: "地火明夷",
    37: "风火家人", 38: "火泽睽", 39: "水山蹇", 40: "雷水解",
    41: "山泽损", 42: "风雷益", 43: "泽天夬", 44: "天风姤",
    45: "泽地萃", 46: "地风升", 47: "泽水困", 48: "水风井",
    49: "泽火革", 50: "火风鼎", 51: "震为雷", 52: "艮为山",
    53: "风山渐", 54: "雷泽归妹", 55: "雷火丰", 56: "火山旅",
    57: "巽为风", 58: "兑为泽", 59: "风水涣", 60: "水泽节",
    61: "风泽中孚", 62: "雷山小过", 63: "水火既济", 64: "火水未济",
}

# 八卦象形 -> 三爻二进制 (从下到上, 1=阳, 0=阴)
# 乾111 兑110 离101 震100 巽011 坎010 艮001 坤000
_TRIGRAM: Dict[str, Tuple[int, int, int]] = {
    "天": (1, 1, 1),  # 乾
    "泽": (1, 1, 0),  # 兑
    "火": (1, 0, 1),  # 离
    "雷": (1, 0, 0),  # 震
    "风": (0, 1, 1),  # 巽
    "水": (0, 1, 0),  # 坎
    "山": (0, 0, 1),  # 艮
    "地": (0, 0, 0),  # 坤
}

# 由卦名自动构建 6 位二进制 -> 卦序号 反查表
# 卦名形如 "上卦象下卦象", 纯卦形如 "X为Y"
BINARY_TO_ID: Dict[Tuple[int, ...], int] = {}
for _hid, _name in HEXAGRAM_NAMES.items():
    if "为" in _name:
        # 纯卦: 上下卦同为最后一个字 (如 乾为天 -> 天)
        upper_ch = lower_ch = _name[-1]
    else:
        upper_ch, lower_ch = _name[0], _name[1]
    # 全卦 = 下卦(初爻起) + 上卦
    BINARY_TO_ID[_TRIGRAM[lower_ch] + _TRIGRAM[upper_ch]] = _hid
del _hid, _name, upper_ch, lower_ch


# ---------------------------------------------------------------------------
# 2. 成卦函数
# ---------------------------------------------------------------------------
def cast_hexagram(values: List[int]) -> Dict[str, Any]:
    """输入 6 个爻值 (从初爻到上爻), 6=老阴 7=少阳 8=少阴 9=老阳.

    - 本卦阴阳: 7/9=阳(1), 6/8=阴(0)
    - 动爻: 6(老阴)变阳, 9(老阳)变阴; 7/8 不变
    """
    if len(values) != 6:
        raise ValueError("values 必须包含 6 个爻值 (初爻到上爻)")

    ben_binary: List[int] = []
    bian_binary: List[int] = []
    dong_positions: List[int] = []

    for idx, v in enumerate(values):
        if v not in (6, 7, 8, 9):
            raise ValueError(f"非法爻值 {v!r}, 必须为 6/7/8/9")
        pos = idx + 1
        is_yang = 1 if v in (7, 9) else 0
        ben_binary.append(is_yang)
        if v in (6, 9):  # 动爻
            dong_positions.append(pos)
            bian_binary.append(1 - is_yang)
        else:
            bian_binary.append(is_yang)

    ben_id = BINARY_TO_ID[tuple(ben_binary)]
    bian_id = BINARY_TO_ID[tuple(bian_binary)]

    return {
        "ben_binary": ben_binary,
        "bian_binary": bian_binary,
        "ben_id": ben_id,
        "bian_id": bian_id,
        "ben_name": HEXAGRAM_NAMES[ben_id],
        "bian_name": HEXAGRAM_NAMES[bian_id],
        "dong_positions": dong_positions,
    }


# ---------------------------------------------------------------------------
# 3. 八宫世应定位
# ---------------------------------------------------------------------------
# 八宫纯卦 (本宫六爻) 与本宫五行
_PALACE_PURE: Dict[str, Tuple[int, ...]] = {
    "乾宫": (1, 1, 1, 1, 1, 1),  # 金
    "坎宫": (0, 1, 0, 0, 1, 0),  # 水
    "艮宫": (0, 0, 1, 0, 0, 1),  # 土
    "震宫": (1, 0, 0, 1, 0, 0),  # 木
    "巽宫": (0, 1, 1, 0, 1, 1),  # 木
    "离宫": (1, 0, 1, 1, 0, 1),  # 火
    "坤宫": (0, 0, 0, 0, 0, 0),  # 土
    "兑宫": (1, 1, 0, 1, 1, 0),  # 金
}

_PALACE_WX: Dict[str, str] = {
    "乾宫": "金", "坎宫": "水", "艮宫": "土", "震宫": "木",
    "巽宫": "木", "离宫": "火", "坤宫": "土", "兑宫": "金",
}


def _flip(bits: Tuple[int, ...], idxs: Tuple[int, ...]) -> Tuple[int, ...]:
    lst = list(bits)
    for i in idxs:
        lst[i] = 1 - lst[i]
    return tuple(lst)


# 由本宫纯卦派生本宫八卦 (相对纯卦翻转的爻位索引, 0=初爻)
# 一世: 初爻变; 二世: 初二; 三世: 初二三; 四世: 初二三四; 五世: 初二三四五
# 游魂: 四世卦四爻变回 -> 翻 0,1,2,4 (三/五爻变, 四爻复原)
# 归魂: 游魂卦内卦三爻全变回 -> 仅翻 index4 (五爻)
_PALACE_VARIANTS: List[Tuple[Tuple[int, ...], str, int]] = [
    ((),            "本宫", 6),
    ((0,),          "一世", 1),
    ((0, 1),        "二世", 2),
    ((0, 1, 2),     "三世", 3),
    ((0, 1, 2, 3),  "四世", 4),
    ((0, 1, 2, 3, 4), "五世", 5),
    ((0, 1, 2, 4),  "游魂", 4),
    ((4,),          "归魂", 3),
]

# 全量反查表: 6 位二进制 -> (宫, 五行, 世位, 世类型)
_PALACE_LOOKUP: Dict[Tuple[int, ...], Dict[str, Any]] = {}
for _pname, _pure in _PALACE_PURE.items():
    for _idxs, _stype, _shipos in _PALACE_VARIANTS:
        _b = _flip(_pure, _idxs)
        _PALACE_LOOKUP[_b] = {
            "palace": _pname,
            "palace_wx": _PALACE_WX[_pname],
            "shi_pos": _shipos,
            "shi_type": _stype,
        }
del _pname, _pure, _idxs, _stype, _shipos, _b


def find_palace_and_shiying(
    ben_binary: List[int], bian_binary: List[int]
) -> Dict[str, Any]:
    """京房八宫世应定位.

    palace 归属与世爻位置由本卦决定; 应爻 = 世爻 + 3 (超过 6 减 6).
    bian_binary 保留入参以兼容调用方, 不参与宫位计算.
    """
    key = tuple(ben_binary)
    if key not in _PALACE_LOOKUP:
        raise KeyError(f"未在八宫表中找到本卦: {key}")
    info = _PALACE_LOOKUP[key]
    shi = info["shi_pos"]
    ying = shi + 3
    if ying > 6:
        ying -= 6
    return {
        "palace": info["palace"],
        "palace_wx": info["palace_wx"],
        "shi_pos": shi,
        "ying_pos": ying,
        "shi_type": info["shi_type"],
    }
