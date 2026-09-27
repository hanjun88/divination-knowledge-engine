"""
B3 — 月建日辰旺衰评分 + 旬空月破判定 + 伏神查找。

量化评分模型沿用 deep_distill_v2:
  临月建 +3.0 / 临日辰 +3.0 / 月建生爻 +1.5 / 日辰生爻 +1.5
  月建克爻 -2.0 / 日辰克爻 -1.5 / 爻生月建(泄) -0.5 / 爻生日辰(泄) -0.5

旺衰标签阈值:
  score >= 4.0           -> 旺
  2.0 <= score < 4.0     -> 相
  -1.0 <= score < 2.0    -> 平
  -3.0 <= score < -1.0   -> 囚
  score < -3.0           -> 死
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from liuyao import Yao

# ---------------------------------------------------------------------------
# 五行 / 干支基础表 (自包含, 与 rule_engine 保持一致)
# ---------------------------------------------------------------------------

TIANGAN: List[str] = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI: List[str] = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

ZHI_WX: Dict[str, str] = {
    "寅": "木", "卯": "木",
    "巳": "火", "午": "火",
    "申": "金", "酉": "金",
    "亥": "水", "子": "水",
    "辰": "土", "戌": "土", "丑": "土", "未": "土",
}

# 五行相生: 木 -> 火 -> 土 -> 金 -> 水 -> 木
SHENG_ORDER: List[str] = ["木", "火", "土", "金", "水"]
WUXING_SHENG: Dict[str, str] = {
    a: b for a, b in zip(SHENG_ORDER, SHENG_ORDER[1:] + SHENG_ORDER[:1])
}
# 五行相克: 木 -> 土 -> 水 -> 火 -> 金 -> 木
KE_ORDER: List[str] = ["木", "土", "水", "火", "金"]
WUXING_KE: Dict[str, str] = {a: b for a, b in zip(KE_ORDER, KE_ORDER[1:] + KE_ORDER[:1])}

# 地支六冲
LIUCHONG: Dict[str, str] = {
    "子": "午", "午": "子", "丑": "未", "未": "丑",
    "寅": "申", "申": "寅", "卯": "酉", "酉": "卯",
    "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳",
}

# 六甲旬空
XUNKONG: Dict[str, List[str]] = {
    "甲子": ["戌", "亥"],
    "甲戌": ["申", "酉"],
    "甲申": ["午", "未"],
    "甲午": ["辰", "巳"],
    "甲辰": ["寅", "卯"],
    "甲寅": ["子", "丑"],
}

# 五行墓库 (入墓)
# 金墓丑, 木墓未, 水墓辰, 火墓戌, 土墓辰(寄水)
MU_KU: Dict[str, str] = {
    "金": "丑",
    "木": "未",
    "水": "辰",
    "火": "戌",
    "土": "辰",
}

# 八宫五行
PALACE_WX: Dict[str, str] = {
    "乾宫": "金",
    "坎宫": "水",
    "艮宫": "土",
    "震宫": "木",
    "巽宫": "木",
    "离宫": "火",
    "坤宫": "土",
    "兑宫": "金",
}

# 本宫纯卦 (八纯卦) 六爻纳支表, key=宫名, value=[初爻..上爻] 地支
# 乾震同: 子寅辰 / 午申戌; 坎: 寅辰午 / 申戌子; 艮: 辰午申 / 戌子寅
# 坤: 未巳卯 / 丑亥酉; 巽: 丑亥酉 / 未巳卯; 离: 卯丑亥 / 酉未巳; 兑: 巳卯丑 / 亥酉未
PURE_GUA_ZHI: Dict[str, List[str]] = {
    "乾宫": ["子", "寅", "辰", "午", "申", "戌"],
    "坎宫": ["寅", "辰", "午", "申", "戌", "子"],
    "艮宫": ["辰", "午", "申", "戌", "子", "寅"],
    "震宫": ["子", "寅", "辰", "午", "申", "戌"],
    "巽宫": ["丑", "亥", "酉", "未", "巳", "卯"],
    "离宫": ["卯", "丑", "亥", "酉", "未", "巳"],
    "坤宫": ["未", "巳", "卯", "丑", "亥", "酉"],
    "兑宫": ["巳", "卯", "丑", "亥", "酉", "未"],
}

# 纳甲天干 (本宫纯卦用, 仅做记录, 不参与旺衰)
# 甲壬->乾, 乙癸->坤, 戊->坎, 己->离, 庚->震, 辛->巽, 丙->艮, 丁->兑
NAJIA_TABLE: Dict[str, Dict[str, List[str]]] = {
    "乾宫": {"inner": ["子", "寅", "辰"], "outer": ["午", "申", "戌"]},
    "坎宫": {"inner": ["寅", "辰", "午"], "outer": ["申", "戌", "子"]},
    "艮宫": {"inner": ["辰", "午", "申"], "outer": ["戌", "子", "寅"]},
    "震宫": {"inner": ["子", "寅", "辰"], "outer": ["午", "申", "戌"]},
    "巽宫": {"inner": ["丑", "亥", "酉"], "outer": ["未", "巳", "卯"]},
    "离宫": {"inner": ["卯", "丑", "亥"], "outer": ["酉", "未", "巳"]},
    "坤宫": {"inner": ["未", "巳", "卯"], "outer": ["丑", "亥", "酉"]},
    "兑宫": {"inner": ["巳", "卯", "丑"], "outer": ["亥", "酉", "未"]},
}


# ---------------------------------------------------------------------------
# 六亲装配
# ---------------------------------------------------------------------------

def assign_liuqin(palace_wx: str, yao_wx: str) -> str:
    """以本宫五行为我, 定六亲:
    生我=父母, 我生=子孙, 克我=官鬼, 我克=妻财, 同我=兄弟
    """
    if yao_wx == palace_wx:
        return "兄弟"
    if WUXING_SHENG.get(palace_wx) == yao_wx:   # 我生
        return "子孙"
    if WUXING_SHENG.get(yao_wx) == palace_wx:    # 生我
        return "父母"
    if WUXING_KE.get(palace_wx) == yao_wx:       # 我克
        return "妻财"
    if WUXING_KE.get(yao_wx) == palace_wx:       # 克我
        return "官鬼"
    return ""


# ---------------------------------------------------------------------------
# 1. 旺衰评分
# ---------------------------------------------------------------------------

def _label_for_score(score: float) -> str:
    """旺衰标签阈值:
    >=4.0 旺; [2.0,4.0) 相; [-1.0,2.0) 平; [-3.0,-1.0) 囚; <-3.0 死
    """
    if score >= 4.0:
        return "旺"
    if score >= 2.0:
        return "相"
    if score >= -1.0:
        return "平"
    if score >= -3.0:
        return "囚"
    return "死"


def compute_wangshuai(
    yao_wx: str,
    month_zhi: str,
    day_zhi: str,
    is_dong: bool = False,
    yao_zhi: str = "",
) -> Dict[str, Any]:
    """月建日辰旺衰量化评分。

    参数:
        yao_wx: 爻五行 (木/火/土/金/水)
        month_zhi: 月建地支
        day_zhi: 日辰地支
        is_dong: 是否动爻 (预留, 当前模型不直接加分)
        yao_zhi: 爻地支, 用于判定临月建/临日辰。传入后才能正确给出
                 lin_yue / lin_ri 标志。

    返回:
        {"score": float, "label": str, "yue_sheng": bool, "yue_ke": bool,
         "ri_sheng": bool, "ri_ke": bool, "lin_yue": bool, "lin_ri": bool,
         "xie_yue": bool, "xie_ri": bool}
    """
    m_wx = ZHI_WX.get(month_zhi, "")
    d_wx = ZHI_WX.get(day_zhi, "")

    # 临月建 / 临日辰 (需要爻地支)
    lin_yue = bool(yao_zhi) and yao_zhi == month_zhi
    lin_ri = bool(yao_zhi) and yao_zhi == day_zhi

    # 月建对爻的生克泄
    yue_sheng = WUXING_SHENG.get(m_wx) == yao_wx       # 月建生爻
    yue_ke = WUXING_KE.get(m_wx) == yao_wx             # 月建克爻
    xie_yue = WUXING_SHENG.get(yao_wx) == m_wx         # 爻生月建 (泄)

    # 日辰对爻的生克泄
    ri_sheng = WUXING_SHENG.get(d_wx) == yao_wx        # 日辰生爻
    ri_ke = WUXING_KE.get(d_wx) == yao_wx              # 日辰克爻
    xie_ri = WUXING_SHENG.get(yao_wx) == d_wx          # 爻生日辰 (泄)

    score = 0.0
    if lin_yue:
        score += 3.0
    if lin_ri:
        score += 3.0
    if yue_sheng:
        score += 1.5
    if ri_sheng:
        score += 1.5
    if yue_ke:
        score -= 2.0
    if ri_ke:
        score -= 1.5
    if xie_yue:
        score -= 0.5
    if xie_ri:
        score -= 0.5

    return {
        "score": score,
        "label": _label_for_score(score),
        "yue_sheng": yue_sheng,
        "yue_ke": yue_ke,
        "ri_sheng": ri_sheng,
        "ri_ke": ri_ke,
        "lin_yue": lin_yue,
        "lin_ri": lin_ri,
        "xie_yue": xie_yue,
        "xie_ri": xie_ri,
    }


# ---------------------------------------------------------------------------
# 2. 旬空判定
# ---------------------------------------------------------------------------

def get_xun_shou(day_gan: str, day_zhi: str) -> str:
    """根据日辰干支推算旬首 (甲子/甲戌/甲申/甲午/甲辰/甲寅)。

    原理: 60 甲子按天干 0..9、地支 0..11 双游标同步推进; 每 10 个一旬,
    旬首为该旬第一个 (gan_idx, zhi_idx) 相同的位置。
    """
    if day_gan not in TIANGAN or day_zhi not in DIZHI:
        return ""
    g = TIANGAN.index(day_gan)
    z = DIZHI.index(day_zhi)
    # 60 甲子中, 第 n 项 (n=0..59) 的干支索引为 (n%10, n%12)。
    # 求 n 使 n%10==g 且 n%12==z。
    for n in range(60):
        if n % 10 == g and n % 12 == z:
            xun_start = (n // 10) * 10
            return TIANGAN[xun_start % 10] + DIZHI[xun_start % 12]
    return ""


def check_xun_kong(day_xun: str, zhi: str) -> bool:
    """判定某地支是否在日辰旬空亡中。"""
    return zhi in XUNKONG.get(day_xun, [])


# ---------------------------------------------------------------------------
# 3. 月破 / 日冲 / 日生 / 入墓
# ---------------------------------------------------------------------------

def check_yue_po(month_zhi: str, zhi: str) -> bool:
    """月破: 爻地支与月建相冲。"""
    return LIUCHONG.get(month_zhi) == zhi


def check_ri_chong(day_zhi: str, zhi: str) -> bool:
    """日冲: 爻地支与日辰相冲。"""
    return LIUCHONG.get(day_zhi) == zhi


def check_ri_sheng(day_zhi: str, yao_wx: str) -> bool:
    """日辰生爻: 日辰五行生爻五行。"""
    return WUXING_SHENG.get(ZHI_WX.get(day_zhi, "")) == yao_wx


def check_ru_mu(yao_wx: str, zhi: str) -> bool:
    """入墓: 爻地支为爻五行的墓库。
    金墓丑, 木墓未, 水墓辰, 火墓戌, 土墓辰(寄水)
    """
    return MU_KU.get(yao_wx) == zhi


# ---------------------------------------------------------------------------
# 4. 伏神查找
# ---------------------------------------------------------------------------

def find_fushen(
    yaos: List[Yao], palace: str, target_liuqin: str
) -> Optional[Dict[str, Any]]:
    """用神不现时, 从本宫纯卦对应爻位找伏神。

    1. 若 yaos 中已存在 target_liuqin 的爻, 返回 None (用神已现, 不找伏)。
    2. 否则从本宫纯卦六爻中找 target_liuqin 对应的爻位。
    3. 伏神落在该爻位, 飞神为当前卦同爻位的爻。
    4. 计算飞伏生克关系。

    返回:
        {"pos", "zhi", "wx", "liuqin", "fei_pos", "fei_zhi",
         "fei_ke_fu", "fei_sheng_fu"}
    或 None (用神已现)。
    """
    # 1. 用神已现?
    for y in yaos:
        if y.liuqin == target_liuqin:
            return None

    palace_wx = PALACE_WX.get(palace, "")
    pure_zhis = PURE_GUA_ZHI.get(palace, [])
    if not palace_wx or not pure_zhis:
        return None

    # 2. 在本宫纯卦中找 target_liuqin 所在爻位 (pos 1..6)
    fu_pos = 0
    fu_zhi = ""
    fu_wx = ""
    for idx, zhi in enumerate(pure_zhis):
        wx = ZHI_WX.get(zhi, "")
        lq = assign_liuqin(palace_wx, wx)
        if lq == target_liuqin:
            fu_pos = idx + 1  # 爻位 1..6
            fu_zhi = zhi
            fu_wx = wx
            break

    if fu_pos == 0:
        return None

    # 3. 飞神 = 当前卦同爻位的爻
    fei_yao = next((y for y in yaos if y.pos == fu_pos), None)
    fei_pos = fu_pos
    fei_zhi = fei_yao.zhi if fei_yao else ""
    fei_wx = fei_yao.wx if fei_yao else ""

    # 4. 飞伏生克
    fei_ke_fu = bool(fei_wx) and WUXING_KE.get(fei_wx) == fu_wx
    fei_sheng_fu = bool(fei_wx) and WUXING_SHENG.get(fei_wx) == fu_wx

    return {
        "pos": fu_pos,
        "zhi": fu_zhi,
        "wx": fu_wx,
        "liuqin": target_liuqin,
        "fei_pos": fei_pos,
        "fei_zhi": fei_zhi,
        "fei_ke_fu": fei_ke_fu,
        "fei_sheng_fu": fei_sheng_fu,
    }
