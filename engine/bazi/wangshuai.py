"""
wangshuai.py — 八字旺衰判定 / 十神装配 / 起运岁数模块

职责:
  1. 地支藏干表 (本气/中气/余气) 与权重
  2. 以日干为"我"的十神判定 (比肩/劫财/食神/伤官/偏财/正财/七杀/正官/偏印/正印)
  3. 日主旺衰综合评分: 月令 + 通根 + 透干 + 生扶 + 克泄耗
  4. 用神/忌神推断
  5. 起运岁数计算 + 8 步大运排列 (顺排/逆排)

依赖: bazi.ganzhi (BaziChart / BaziPillar / TIANGAN / DIZHI / 五行函数)
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import sxtwl

from .ganzhi import (
    BaziChart,
    BaziPillar,
    DIZHI,
    TIANGAN,
    wuxing_of_gan,
    wuxing_of_zhi,
)

# ---------------------------------------------------------------------------
# 1. 地支藏干表
# ---------------------------------------------------------------------------
ZHI_CANG_GAN: Dict[str, List[str]] = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "戊", "庚"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}

# 藏干权重: 本气 1.0, 中气 0.5, 余气 0.3
CANG_GAN_WEIGHT: List[float] = [1.0, 0.5, 0.3]

# ---------------------------------------------------------------------------
# 2. 天干阴阳 + 五行生克
# ---------------------------------------------------------------------------
GAN_YIN_YANG: Dict[str, int] = {
    "甲": 1, "乙": 0, "丙": 1, "丁": 0,
    "戊": 1, "己": 0, "庚": 1, "辛": 0,
    "壬": 1, "癸": 0,
}  # 1=阳, 0=阴

# A 生 B
_WX_SHENG: Dict[str, str] = {
    "木": "火", "火": "土", "土": "金", "金": "水", "水": "木",
}
# A 克 B
_WX_KE: Dict[str, str] = {
    "木": "土", "土": "水", "水": "火", "火": "金", "金": "木",
}


# ---------------------------------------------------------------------------
# 3. 十神判定
# ---------------------------------------------------------------------------
def get_shishen(day_gan: str, other_gan: str) -> str:
    """以日干为"我", 判定 other_gan 相对于日干的十神.

    返回: 比肩 / 劫财 / 食神 / 伤官 / 偏财 / 正财 / 七杀 / 正官 / 偏印 / 正印
    """
    if day_gan == other_gan:
        return "比肩"

    d_wx = wuxing_of_gan(day_gan)
    o_wx = wuxing_of_gan(other_gan)
    same_polarity = GAN_YIN_YANG[day_gan] == GAN_YIN_YANG[other_gan]

    if d_wx == o_wx:
        return "比肩" if same_polarity else "劫财"
    if _WX_SHENG[d_wx] == o_wx:            # 我生
        return "食神" if same_polarity else "伤官"
    if _WX_KE[d_wx] == o_wx:               # 我克 = 财
        return "偏财" if same_polarity else "正财"
    if _WX_SHENG[o_wx] == d_wx:            # 生我 = 印
        return "偏印" if same_polarity else "正印"
    if _WX_KE[o_wx] == d_wx:               # 克我 = 官杀
        return "七杀" if same_polarity else "正官"
    raise ValueError(f"无法判定十神: day={day_gan}, other={other_gan}")


# ---------------------------------------------------------------------------
# 4. 旺衰评分
# ---------------------------------------------------------------------------
def _root_score_for_zhi(zhi: str, day_wx: str) -> float:
    """单个地支对日主的通根得分 (按藏干位置取最高权重匹配).

    本气根 1.5, 中气根 0.8, 余气根 0.5.
    """
    cangs = ZHI_CANG_GAN.get(zhi, [])
    for idx, cg in enumerate(cangs):
        if wuxing_of_gan(cg) == day_wx:
            if idx == 0:
                return 1.5
            if idx == 1:
                return 0.8
            return 0.5
    return 0.0


def compute_wangshuai(chart: BaziChart) -> Dict[str, Any]:
    """综合判定日主旺衰.

    评分维度:
      1. 月令 (权重最高): 临月令 +3, 月令生我 +2, 我生月令 -1.5,
         月令克我 -2.5, 我克月令 -1
      2. 通根: 年支/日支/时支藏干含日主五行 (本气 1.5 / 中气 0.8 / 余气 0.5)
      3. 透干: 天干比劫 (年/月/时干), 每个 +1.0
      4. 生扶: 天干印星, 每个 +0.8
      5. 克泄耗: 官杀 -1.0 / 食伤 -0.8 / 财星 -0.6

    旺衰标签:
      score >= 5           → 旺
      2 <= score < 5       → 偏旺
      -2 <= score < 2      → 中和
      -5 <= score < -2     → 偏弱
      score < -5           → 弱
    """
    day_gan = chart.day.gan
    day_wx = wuxing_of_gan(day_gan)
    month_zhi = chart.month.zhi
    month_wx = wuxing_of_zhi(month_zhi)

    # ---- 4.1 月令得分 ----
    if month_wx == day_wx:
        month_score = 3.0
    elif _WX_SHENG[month_wx] == day_wx:    # 月令生我
        month_score = 2.0
    elif _WX_SHENG[day_wx] == month_wx:    # 我生月令 (泄气)
        month_score = -1.5
    elif _WX_KE[month_wx] == day_wx:        # 月令克我
        month_score = -2.5
    elif _WX_KE[day_wx] == month_wx:       # 我克月令 (耗气)
        month_score = -1.0
    else:
        month_score = 0.0

    # ---- 4.2 通根得分 (年支 / 日支 / 时支, 不含月支) ----
    gen_score = 0.0
    tonggen_count = 0
    for pillar in (chart.year, chart.day, chart.hour):
        s = _root_score_for_zhi(pillar.zhi, day_wx)
        if s > 0:
            gen_score += s
            tonggen_count += 1

    # ---- 4.3 透干 / 生扶 / 克泄耗 (年/月/时三干, 不含日干) ----
    tougan_count = 0     # 比劫
    shengfu_count = 0    # 印
    kexiehao_count = 0   # 官杀 + 食伤 + 财
    other_stems: List[str] = [chart.year.gan, chart.month.gan, chart.hour.gan]
    tg_score = 0.0
    sf_score = 0.0
    kxh_score = 0.0

    for g in other_stems:
        ss = get_shishen(day_gan, g)
        if ss in ("比肩", "劫财"):
            tg_score += 1.0
            tougan_count += 1
        elif ss in ("正印", "偏印"):
            sf_score += 0.8
            shengfu_count += 1
        elif ss in ("正官", "七杀"):
            kxh_score -= 1.0
            kexiehao_count += 1
        elif ss in ("食神", "伤官"):
            kxh_score -= 0.8
            kexiehao_count += 1
        elif ss in ("正财", "偏财"):
            kxh_score -= 0.6
            kexiehao_count += 1

    total = month_score + gen_score + tg_score + sf_score + kxh_score

    # ---- 4.4 标签 ----
    if total >= 5:
        label = "旺"
    elif total >= 2:
        label = "偏旺"
    elif total > -2:
        label = "中和"
    elif total > -5:
        label = "偏弱"
    else:
        label = "弱"

    # ---- 4.5 用神 / 忌神 ----
    if label in ("旺", "偏旺"):
        yongshen = "克泄耗(官杀/食伤/财星)"
        jishen = "生扶(印星/比劫)"
    elif label in ("弱", "偏弱"):
        yongshen = "生扶(印星/比劫)"
        jishen = "克泄耗(官杀/食伤/财星)"
    else:
        yongshen = "调候优先(参考rules_bazi tiaohou规则)"
        jishen = "随局而定"

    return {
        "score": round(total, 3),
        "label": label,
        "month_score": month_score,
        "gen_score": round(gen_score, 3),
        "tonggen_count": tonggen_count,
        "tougan_count": tougan_count,
        "shengfu_count": shengfu_count,
        "kexiehao_count": kexiehao_count,
        "yongshen": yongshen,
        "jishen": jishen,
    }


# ---------------------------------------------------------------------------
# 5. 起运岁数 + 大运
# ---------------------------------------------------------------------------
# 12 节令 (非中气) 的 sxtwl jqIndex, 与 ganzhi._JIE_TO_ZHI 一致
_JIE_SET = {1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23}


def _birth_dt_from_chart(chart: BaziChart) -> datetime:
    """从 chart.true_solar_time 解析出生真太阳时."""
    return datetime.strptime(chart.true_solar_time, "%Y-%m-%d %H:%M")


def _find_jieqi_near_birth(
    birth_dt: datetime, direction: str
) -> datetime:
    """顺排找下一个节令时刻, 逆排找上一个节令时刻.

    若出生当天恰逢节令:
      顺排 — 出生时刻在交节之前 → 该节令即目标; 已过交节 → 继续往下找
      逆排 — 出生时刻在交节之后 → 该节令即目标; 未到交节 → 继续往上找
    """
    def _jie_dt_of(cur) -> Optional[datetime]:
        if not cur.hasJieQi():
            return None
        if cur.getJieQi() not in _JIE_SET:
            return None
        dd = sxtwl.JD2DD(cur.getJieQiJD())
        return datetime(int(dd.Y), int(dd.M), int(dd.D),
                        int(dd.h), int(dd.m), int(dd.s))

    cur = sxtwl.fromSolar(birth_dt.year, birth_dt.month, birth_dt.day)

    for _ in range(0, 45):
        jdt = _jie_dt_of(cur)
        if jdt is not None:
            if direction == "顺排" and jdt > birth_dt:
                return jdt
            if direction == "逆排" and jdt < birth_dt:
                return jdt
        cur = cur.after(1) if direction == "顺排" else cur.before(1)

    raise RuntimeError("未找到附近节令, 请检查出生日期")


def compute_qiyun(chart: BaziChart, gender: str = "男") -> Dict[str, Any]:
    """计算起运岁数与 8 步大运.

    规则:
      - 阳年男 / 阴年女 = 顺排 (顺数到下一个节令)
      - 阴年男 / 阳年女 = 逆排 (逆数到上一个节令)
      - 3 天 = 1 岁, 1 天 = 4 个月, 1 时辰 = 10 天
      - 大运从月柱起, 顺/逆排 60 甲子, 每柱管 10 年
    """
    year_gan = chart.year.gan
    year_yang = GAN_YIN_YANG[year_gan] == 1
    male = (gender == "男")

    # 阳年男 / 阴年女 → 顺; 其余 → 逆
    if (year_yang and male) or ((not year_yang) and (not male)):
        direction = "顺排"
    else:
        direction = "逆排"

    birth_dt = _birth_dt_from_chart(chart)
    jie_dt = _find_jieqi_near_birth(birth_dt, direction)

    delta_days = abs((jie_dt - birth_dt).total_seconds()) / 86400.0
    qiyun_age = delta_days / 3.0

    # ---- 大运: 从月柱起顺/逆排 ----
    mg = TIANGAN.index(chart.month.gan)
    mz = DIZHI.index(chart.month.zhi)
    start_age = int(qiyun_age)  # 起运整数岁 (传统截断)
    dayun: List[Dict[str, Any]] = []
    for i in range(8):
        step = i + 1
        if direction == "顺排":
            g = (mg + step) % 10
            z = (mz + step) % 12
        else:
            g = (mg - step) % 10
            z = (mz - step) % 12
        dayun.append({
            "gan": TIANGAN[g],
            "zhi": DIZHI[z],
            "start_age": start_age + i * 10,
            "end_age": start_age + (i + 1) * 10 - 1,
        })

    return {
        "qiyun_age": round(qiyun_age, 2),
        "direction": direction,
        "dayun": dayun,
    }


__all__ = [
    "ZHI_CANG_GAN",
    "CANG_GAN_WEIGHT",
    "GAN_YIN_YANG",
    "get_shishen",
    "compute_wangshuai",
    "compute_qiyun",
]
