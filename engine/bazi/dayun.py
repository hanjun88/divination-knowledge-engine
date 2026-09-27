"""
dayun.py — 八字大运 / 流年 / 流月 推进器模块

职责:
  1. 60 甲子表 (甲子 ... 癸亥)
  2. 按目标年龄定位当前大运干支 (顺排/逆排, 未起运回月柱)
  3. 公历年 → 流年干支 ((year-4)%60)
  4. 公历年月 → 流月干支 (月支固定月建, 月干用五虎遁)
  5. 综合时间推进器: 输入出生盘 + 起运信息, 输出目标时点的
     大运 / 流年 / 流月 及各自天干对日主的十神

依赖: bazi.ganzhi (BaziChart / TIANGAN / DIZHI / 五行 / 五虎遁)
      bazi.wangshuai (get_shishen)
"""
from __future__ import annotations

from typing import Any, Dict, List

from .ganzhi import (
    BaziChart,
    DIZHI,
    TIANGAN,
    wuhu_dun,
    wuxing_of_gan,
)
from .wangshuai import get_shishen

# ---------------------------------------------------------------------------
# 1. 60 甲子表
# ---------------------------------------------------------------------------
JIAZI_60: List[str] = [
    gan + zhi
    for gan, zhi in zip(
        [TIANGAN[i % 10] for i in range(60)],
        [DIZHI[i % 12] for i in range(60)],
    )
]

# 合法十神集合 (用于结果校验)
_SHISHEN_SET = {
    "比肩", "劫财", "食神", "伤官", "偏财",
    "正财", "七杀", "正官", "偏印", "正印",
}


# ---------------------------------------------------------------------------
# 2. 大运推进
# ---------------------------------------------------------------------------
def _month_pillar_from_qiyun(qiyun_result: Dict[str, Any]):
    """由起运结果反推月柱 (未起运时返回月柱作为占位).

    compute_qiyun 中:
      顺排: dayun[i] = 月柱 + (i+1) 步  → 月柱 = dayun[0] - 1 步
      逆排: dayun[i] = 月柱 - (i+1) 步  → 月柱 = dayun[0] + 1 步
    """
    direction = qiyun_result["direction"]
    first = qiyun_result["dayun"][0]
    g = TIANGAN.index(first["gan"])
    z = DIZHI.index(first["zhi"])
    if direction == "顺排":
        mg = (g - 1) % 10
        mz = (z - 1) % 12
    else:
        mg = (g + 1) % 10
        mz = (z + 1) % 12
    return TIANGAN[mg], DIZHI[mz]


def get_dayun_at_age(qiyun_result: Dict[str, Any], age: int) -> Dict[str, Any]:
    """根据起运信息和目标年龄, 返回当前大运干支.

    参数:
      qiyun_result: compute_qiyun 的返回值
      age: 目标年龄 (整数)

    逻辑:
      - age < qiyun_age → 尚未起运, 返回月柱作为"未起运"状态 (started=False)
      - 否则在 dayun 列表中找到 start_age <= age <= end_age 的大运柱
      - 若超出所有大运 (age 过大), 回退到最后一步大运

    返回: {"gan", "zhi", "start_age", "end_age", "index", "started", "wx"}
    """
    qiyun_age = qiyun_result["qiyun_age"]
    dayun_list = qiyun_result["dayun"]

    # ---- 未起运: 返回月柱占位 ----
    if age < qiyun_age:
        mg, mz = _month_pillar_from_qiyun(qiyun_result)
        pre_end = int(qiyun_age) - 1
        if pre_end < 0:
            pre_end = 0
        return {
            "gan": mg,
            "zhi": mz,
            "start_age": 0,
            "end_age": pre_end,
            "index": -1,
            "started": False,
            "wx": wuxing_of_gan(mg),
        }

    # ---- 定位当前大运 ----
    for i, d in enumerate(dayun_list):
        if d["start_age"] <= age <= d["end_age"]:
            return {
                "gan": d["gan"],
                "zhi": d["zhi"],
                "start_age": d["start_age"],
                "end_age": d["end_age"],
                "index": i,
                "started": True,
                "wx": wuxing_of_gan(d["gan"]),
            }

    # ---- 超出全部大运: 回退最后一步 ----
    last = dayun_list[-1]
    return {
        "gan": last["gan"],
        "zhi": last["zhi"],
        "start_age": last["start_age"],
        "end_age": last["end_age"],
        "index": len(dayun_list) - 1,
        "started": True,
        "wx": wuxing_of_gan(last["gan"]),
    }


# ---------------------------------------------------------------------------
# 3. 流年推算
# ---------------------------------------------------------------------------
def get_liunian(year: int) -> Dict[str, Any]:
    """根据公历年返回流年干支.

    公式: (year - 4) % 60 → 60甲子序号 (0=甲子)
    1984 年 = 甲子年 ((1984-4)%60 = 0)

    返回: {"gan", "zhi", "wx", "year"}
    """
    idx = (year - 4) % 60
    gz = JIAZI_60[idx]
    gan, zhi = gz[0], gz[1]
    return {
        "gan": gan,
        "zhi": zhi,
        "wx": wuxing_of_gan(gan),
        "year": year,
    }


# ---------------------------------------------------------------------------
# 4. 流月推算
# ---------------------------------------------------------------------------
# 公历月 → 月支 (简化近似, 以公历月替代节气月建):
#   1月=丑, 2月=寅, 3月=卯, 4月=辰, 5月=巳, 6月=午,
#   7月=未, 8月=申, 9月=酉, 10月=戌, 11月=亥, 12月=子
# 月支地支索引: 丑=1 寅=2 ... 子=0 → zhi_idx = month % 12
def get_liuyue(year: int, month: int) -> Dict[str, Any]:
    """根据公历年月返回流月干支 (以节气为界, 此处用公历月近似).

    月支固定: 寅月=立春后(约2/4) ... 丑月=小寒后(约1/6)
    月干用五虎遁: 甲/己→寅月丙, 乙/庚→寅月戊, 丙/辛→寅月庚,
                  丁/壬→寅月壬, 戊/癸→寅月甲

    返回: {"gan", "zhi", "wx", "month"}
    """
    if not (1 <= month <= 12):
        raise ValueError(f"month 必须在 1-12 之间, 收到: {month}")

    year_gan = get_liunian(year)["gan"]
    zhi_idx = month % 12  # 1->丑(1), 2->寅(2), ..., 12->子(0)
    month_zhi = DIZHI[zhi_idx]
    month_gan = wuhu_dun(year_gan, month_zhi)

    return {
        "gan": month_gan,
        "zhi": month_zhi,
        "wx": wuxing_of_gan(month_gan),
        "month": month,
    }


# ---------------------------------------------------------------------------
# 5. 综合时间推进器
# ---------------------------------------------------------------------------
def advance_to_date(
    birth_chart: BaziChart,
    qiyun_result: Dict[str, Any],
    target_year: int,
    target_month: int = 1,
    target_day: int = 1,
) -> Dict[str, Any]:
    """输入出生盘和目标日期, 输出该时点的大运+流年+流月.

    age = target_year - 出生年 (周岁近似, 不细分月日)

    返回: {
        "target_date": "YYYY-MM-DD",
        "age": int,
        "dayun": {"gan","zhi","start_age","end_age","wx", ...},
        "liunian": {"gan","zhi","wx","year"},
        "liuyue": {"gan","zhi","wx","month"},
        "dayun_shishen": str,    # 大运天干对日主的十神
        "liunian_shishen": str,  # 流年天干对日主的十神
        "liuyue_shishen": str,   # 流月天干对日主的十神
    }
    """
    day_gan = birth_chart.day.gan

    # 出生年: 从 solar_date (ISO "YYYY-MM-DD") 取前 4 位
    birth_year = int(birth_chart.solar_date[:4])
    age = target_year - birth_year

    dayun = get_dayun_at_age(qiyun_result, age)
    liunian = get_liunian(target_year)
    liuyue = get_liuyue(target_year, target_month)

    return {
        "target_date": f"{target_year:04d}-{target_month:02d}-{target_day:02d}",
        "age": age,
        "dayun": dayun,
        "liunian": liunian,
        "liuyue": liuyue,
        "dayun_shishen": get_shishen(day_gan, dayun["gan"]),
        "liunian_shishen": get_shishen(day_gan, liunian["gan"]),
        "liuyue_shishen": get_shishen(day_gan, liuyue["gan"]),
    }


__all__ = [
    "JIAZI_60",
    "get_dayun_at_age",
    "get_liunian",
    "get_liuyue",
    "advance_to_date",
]
