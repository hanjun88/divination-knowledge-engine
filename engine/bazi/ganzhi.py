"""
ganzhi.py — 八字四柱干支历算模块

职责:
  1. 公历 → 年/月/日/时 四柱干支
  2. 年柱以立春为界, 月柱以十二节令为界 (寅月=立春 ... 丑月=小寒)
  3. 日柱以子时 (23:00) 为界, 23 点后算次日子时
  4. 真太阳时修正: 经度时差 + 均时差
  5. 60 甲子纳音表, 干支五行, 日辰旬首

依赖: sxtwl (寿星天文历) 提供高精度节气时刻与干支计算.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List

import sxtwl

# ---------------------------------------------------------------------------
# 1. 天干 / 地支 表
# ---------------------------------------------------------------------------
TIANGAN: List[str] = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI: List[str] = ["子", "丑", "寅", "卯", "辰", "巳",
                    "午", "未", "申", "酉", "戌", "亥"]

# sxtwl 节气索引 (jqIndex):
#   0=冬至 1=小寒 2=大寒 3=立春 4=雨水 5=惊蛰 6=春分 7=清明 8=谷雨
#   9=立夏 10=小满 11=芒种 12=夏至 13=小暑 14=大暑 15=立秋 16=处暑
#   17=白露 18=秋分 19=寒露 20=霜降 21=立冬 22=小雪 23=大雪
_JIEQI_NAMES: List[str] = [
    "冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
    "春分", "清明", "谷雨", "立夏", "小满", "芒种",
    "夏至", "小暑", "大暑", "立秋", "处暑", "白露",
    "秋分", "寒露", "霜降", "立冬", "小雪", "大雪",
]

# 十二节令 (月建起点, 非中气): 节令 jqIndex -> 所建月支
# 寅月=立春, 卯月=惊蛰, 辰月=清明, 巳月=立夏, 午月=芒种, 未月=小暑
# 申月=立秋, 酉月=白露, 戌月=寒露, 亥月=立冬, 子月=大雪, 丑月=小寒
_JIE_TO_ZHI: Dict[int, int] = {
    3: 2,    # 立春 -> 寅
    5: 3,    # 惊蛰 -> 卯
    7: 4,    # 清明 -> 辰
    9: 5,    # 立夏 -> 巳
    11: 6,   # 芒种 -> 午
    13: 7,   # 小暑 -> 未
    15: 8,   # 立秋 -> 申
    17: 9,   # 白露 -> 酉
    19: 10,  # 寒露 -> 戌
    21: 11,  # 立冬 -> 亥
    23: 0,   # 大雪 -> 子
    1: 1,    # 小寒 -> 丑
}

# 月支 -> 起始节令名 (用于 BaziChart.jieqi)
_ZHI_TO_JIEQI: Dict[int, str] = {
    2: "立春", 3: "惊蛰", 4: "清明", 5: "立夏",
    6: "芒种", 7: "小暑", 8: "立秋", 9: "白露",
    10: "寒露", 11: "立冬", 0: "大雪", 1: "小寒",
}


# ---------------------------------------------------------------------------
# 2. 五行
# ---------------------------------------------------------------------------
def wuxing_of_gan(gan: str) -> str:
    """天干五行: 甲乙木, 丙丁火, 戊己土, 庚辛金, 壬癸水."""
    idx = TIANGAN.index(gan)
    return ["木", "木", "火", "火", "土", "土", "金", "金", "水", "水"][idx]


def wuxing_of_zhi(zhi: str) -> str:
    """地支五行: 寅卯木, 巳午火, 申酉金, 亥子水, 辰戌丑未土."""
    idx = DIZHI.index(zhi)
    # 子0 丑1 寅2 卯3 辰4 巳5 午6 未7 申8 酉9 戌10 亥11
    return ["水", "土", "木", "木", "土", "火",
            "火", "土", "金", "金", "土", "水"][idx]


# ---------------------------------------------------------------------------
# 3. 60 甲子纳音
# ---------------------------------------------------------------------------
# 60 甲子纳音: 30 组, 每组两个干支共用一个纳音
NA_YIN: Dict[str, str] = {
    # 1 海中金
    "甲子": "海中金", "乙丑": "海中金",
    # 2 炉中火
    "丙寅": "炉中火", "丁卯": "炉中火",
    # 3 大林木
    "戊辰": "大林木", "己巳": "大林木",
    # 4 路旁土
    "庚午": "路旁土", "辛未": "路旁土",
    # 5 剑锋金
    "壬申": "剑锋金", "癸酉": "剑锋金",
    # 6 山头火
    "甲戌": "山头火", "乙亥": "山头火",
    # 7 涧下水
    "丙子": "涧下水", "丁丑": "涧下水",
    # 8 城头土
    "戊寅": "城头土", "己卯": "城头土",
    # 9 白蜡金
    "庚辰": "白蜡金", "辛巳": "白蜡金",
    # 10 杨柳木
    "壬午": "杨柳木", "癸未": "杨柳木",
    # 11 泉中水
    "甲申": "泉中水", "乙酉": "泉中水",
    # 12 屋上土
    "丙戌": "屋上土", "丁亥": "屋上土",
    # 13 霹雳火
    "戊子": "霹雳火", "己丑": "霹雳火",
    # 14 松柏木
    "庚寅": "松柏木", "辛卯": "松柏木",
    # 15 长流水
    "壬辰": "长流水", "癸巳": "长流水",
    # 16 沙中金
    "甲午": "沙中金", "乙未": "沙中金",
    # 17 山下火
    "丙申": "山下火", "丁酉": "山下火",
    # 18 平地木
    "戊戌": "平地木", "己亥": "平地木",
    # 19 壁上土
    "庚子": "壁上土", "辛丑": "壁上土",
    # 20 金箔金
    "壬寅": "金箔金", "癸卯": "金箔金",
    # 21 覆灯火
    "甲辰": "覆灯火", "乙巳": "覆灯火",
    # 22 天河水
    "丙午": "天河水", "丁未": "天河水",
    # 23 大驿土
    "戊申": "大驿土", "己酉": "大驿土",
    # 24 钗钏金
    "庚戌": "钗钏金", "辛亥": "钗钏金",
    # 25 桑柘木
    "壬子": "桑柘木", "癸丑": "桑柘木",
    # 26 大溪水
    "甲寅": "大溪水", "乙卯": "大溪水",
    # 27 沙中土
    "丙辰": "沙中土", "丁巳": "沙中土",
    # 28 天上火
    "戊午": "天上火", "己未": "天上火",
    # 29 石榴木
    "庚申": "石榴木", "辛酉": "石榴木",
    # 30 大海水
    "壬戌": "大海水", "癸亥": "大海水",
}


# ---------------------------------------------------------------------------
# 4. 日辰旬首
# ---------------------------------------------------------------------------
def _gz_index(gan: str, zhi: str) -> int:
    """干支在 60 甲子中的序号 (0-59)."""
    g = TIANGAN.index(gan)
    z = DIZHI.index(zhi)
    for k in range(6):
        n = g + 10 * k
        if n % 12 == z:
            return n
    raise ValueError(f"非法干支组合: {gan}{zhi}")


def get_day_xun(day_gan: str, day_zhi: str) -> str:
    """获取日辰旬首 (甲子/甲戌/甲申/甲午/甲辰/甲寅)."""
    n = _gz_index(day_gan, day_zhi)
    xun_head_n = (n // 10) * 10
    return TIANGAN[xun_head_n % 10] + DIZHI[xun_head_n % 12]


# ---------------------------------------------------------------------------
# 5. 五虎遁 / 五鼠遁 (显式实现, 便于测试)
# ---------------------------------------------------------------------------
def wuhu_dun(year_gan: str, month_zhi: str) -> str:
    """五虎遁: 由年干推寅月起干, 再顺数至目标月支, 返回月干."""
    yg = TIANGAN.index(year_gan)
    # 寅月起干: 甲己->丙(2), 乙庚->戊(4), 丙辛->庚(6), 丁壬->壬(8), 戊癸->甲(0)
    yin_gan = (yg % 5) * 2 + 2
    if yin_gan >= 10:
        yin_gan -= 10
    # 寅=地支索引2, 顺数到目标月支
    offset = (DIZHI.index(month_zhi) - 2) % 12
    return TIANGAN[(yin_gan + offset) % 10]


def wushu_dun(day_gan: str, hour_zhi: str) -> str:
    """五鼠遁: 由日干推子时起干, 再顺数至目标时支, 返回时干."""
    dg = TIANGAN.index(day_gan)
    # 子时起干: 甲己->甲(0), 乙庚->丙(2), 丙辛->戊(4), 丁壬->庚(6), 戊癸->壬(8)
    zi_gan = (dg % 5) * 2
    offset = DIZHI.index(hour_zhi)  # 子=0
    return TIANGAN[(zi_gan + offset) % 10]


# ---------------------------------------------------------------------------
# 6. 真太阳时修正
# ---------------------------------------------------------------------------
def _equation_of_time(dt: datetime) -> float:
    """均时差 (分钟), Spencer 近似, 误差 < 30s.

    EoT = 9.87*sin(2B) - 7.53*cos(B) - 1.5*sin(B),
    B = 360/365 * (N - 81) 度, N 为年积日.
    """
    n = dt.timetuple().tm_yday
    import math
    B = math.radians(360.0 / 365.0 * (n - 81))
    return 9.87 * math.sin(2 * B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)


def _true_solar_time(dt: datetime, longitude: float) -> datetime:
    """真太阳时 = 北京时间 + (经度-120)*4 分钟 + 均时差."""
    lon_minutes = (longitude - 120.0) * 4.0
    eot = _equation_of_time(dt)
    return dt + timedelta(minutes=lon_minutes + eot)


# ---------------------------------------------------------------------------
# 7. 数据结构
# ---------------------------------------------------------------------------
@dataclass
class BaziPillar:
    """单柱干支"""
    gan: str       # 天干
    zhi: str       # 地支
    wx: str        # 五行 (柱天干五行)
    na_yin: str    # 纳音 (如 海中金)

    @property
    def gz(self) -> str:
        return self.gan + self.zhi


@dataclass
class BaziChart:
    """四柱八字"""
    year: BaziPillar
    month: BaziPillar
    day: BaziPillar
    hour: BaziPillar
    solar_date: str        # 公历日期 ISO
    lunar_date: str        # 农历日期
    jieqi: str             # 当前节气 (月建节令)
    day_xun: str           # 日辰旬首
    true_solar_time: str   # 真太阳时修正后时间


# ---------------------------------------------------------------------------
# 8. 核心排盘函数
# ---------------------------------------------------------------------------
def _make_pillar(gan_idx: int, zhi_idx: int) -> BaziPillar:
    gan = TIANGAN[gan_idx]
    zhi = DIZHI[zhi_idx]
    return BaziPillar(
        gan=gan,
        zhi=zhi,
        wx=wuxing_of_gan(gan),
        na_yin=NA_YIN[gan + zhi],
    )


def compute_bazi(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int = 0,
    longitude: float = 120.0,
    latitude: float = 0.0,
) -> BaziChart:
    """公历 → 四柱八字.

    参数:
      year/month/day/hour/minute: 公历时间 (北京时间, UTC+8)
      longitude: 经度 (用于真太阳时修正, 默认 120°=北京时间)
      latitude: 纬度 (可选, 当前未参与计算)

    算法:
      1. 真太阳时修正: 真太阳时 = 北京时间 + (经度-120)*4分钟 + 均时差
      2. 年柱: 以立春为界, 立春前属上年
      3. 月柱: 以节气为界 (寅月=立春 ...), 月干用五虎遁
      4. 日柱: 以子时为界, 23 点后算次日子时
      5. 时柱: 时支=子(23-1) ... 亥(21-23); 时干用五鼠遁
    """
    # --- 8.1 真太阳时修正 ---
    bjt = datetime(year, month, day, hour, minute)
    tst = _true_solar_time(bjt, longitude)

    # --- 8.2 子时换日: 23:00 后属次日 ---
    eff_dt = tst
    if eff_dt.hour >= 23:
        eff_dt = eff_dt + timedelta(days=1)
        # 日期已推进; 时支仍为子 (sxtwl 用 hour=0 取次日子时)
        eff_hour_for_sxtwl = 0
    else:
        eff_hour_for_sxtwl = eff_dt.hour

    # --- 8.3 取 sxtwl 日对象 (基于真太阳时日期) ---
    day_obj = sxtwl.fromSolar(eff_dt.year, eff_dt.month, eff_dt.day)

    # --- 8.4 年柱 / 月柱 (处理节气时刻边界) ---
    ygz = day_obj.getYearGZ()
    mgz = day_obj.getMonthGZ()
    year_g, year_z = ygz.tg, ygz.dz
    month_g, month_z = mgz.tg, mgz.dz

    # 若当日有节令 (月建起点), 需精确比较出生时刻与节令交节时刻
    if day_obj.hasJieQi():
        jq_idx = day_obj.getJieQi()
        if jq_idx in _JIE_TO_ZHI:
            # 交节时刻 (北京时间, sxtwl JD2DD 输出)
            jq_jd = day_obj.getJieQiJD()
            jq_dd = sxtwl.JD2DD(jq_jd)
            jq_dt = datetime(
                int(jq_dd.Y), int(jq_dd.M), int(jq_dd.D),
                int(jq_dd.h), int(jq_dd.m), int(jq_dd.s),
            )
            # 出生时刻早于交节时刻 → 月柱/年柱退回一步
            if eff_dt < jq_dt:
                month_g = (month_g - 1) % 10
                month_z = (month_z - 1) % 12
                if jq_idx == 3:  # 立春: 年柱也退回上年
                    year_g = (year_g - 1) % 10
                    year_z = (year_z - 1) % 12

    # --- 8.5 日柱 ---
    dgz = day_obj.getDayGZ()
    day_g, day_z = dgz.tg, dgz.dz

    # --- 8.6 时柱 (sxtwl getHourGZ 已按五鼠遁 + 子时换日处理) ---
    hgz = day_obj.getHourGZ(eff_hour_for_sxtwl)
    hour_g, hour_z = hgz.tg, hgz.dz

    # --- 8.7 组装四柱 ---
    year_pillar = _make_pillar(year_g, year_z)
    month_pillar = _make_pillar(month_g, month_z)
    day_pillar = _make_pillar(day_g, day_z)
    hour_pillar = _make_pillar(hour_g, hour_z)

    # --- 8.8 农历日期 / 当前节气 / 旬首 ---
    lunar_str = (
        f"{day_obj.getLunarYear()}-"
        f"{day_obj.getLunarMonth():02d}-"
        f"{day_obj.getLunarDay():02d}"
    )
    jieqi_name = _ZHI_TO_JIEQI[month_z]
    xun = get_day_xun(TIANGAN[day_g], DIZHI[day_z])

    return BaziChart(
        year=year_pillar,
        month=month_pillar,
        day=day_pillar,
        hour=hour_pillar,
        solar_date=eff_dt.strftime("%Y-%m-%d"),
        lunar_date=lunar_str,
        jieqi=jieqi_name,
        day_xun=xun,
        true_solar_time=tst.strftime("%Y-%m-%d %H:%M"),
    )
