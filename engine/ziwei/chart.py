"""
chart.py — 紫微斗数排盘内核

职责:
  1. 公历 → 农历 (sxtwl)
  2. 定五行局 (五虎遁 + 生时)
  3. 起紫微 / 天府星系 (依五行局数 + 农历日)
  4. 安十四主星 (紫微系 6 / 天府系 8)
  5. 安辅佐煞曜 (左右昌曲魁钺禄羊陀火铃空劫)
  6. 十二宫定位 + 三方四正
  7. 生年四化飞星

坐标约定 (本内核的简化模型):
  十二地支固定环, 寅为 0, 顺时针递增:
    0寅 1卯 2辰 3巳 4午 5未 6申 7酉 8戌 9亥 10子 11丑
  十二宫名固定自寅起顺布: 0命宫 1兄弟 ... 11父母
  (注: 此为教学/拓扑简化版, 命宫恒起寅; 实战派以生月+生时移宫, 此处不展开。)

参考: skills/ziwei/galaxy_matrix.md (安星诀/十干化曜表)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import sxtwl

# ---------------------------------------------------------------------------
# 0. 常量表
# ---------------------------------------------------------------------------
TIANGAN: List[str] = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 十二地支固定环 (0 = 寅, 顺时针)
PALACE_ZHI: List[str] = ["寅", "卯", "辰", "巳", "午", "未",
                         "申", "酉", "戌", "亥", "子", "丑"]

# 十二宫名 (0 = 命宫, 顺时针)
PALACES_12: List[str] = ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
                         "迁移", "交友", "官禄", "田宅", "福德", "父母"]

# 地支 -> 固定环索引
_ZHI_TO_IDX: Dict[str, int] = {z: i for i, z in enumerate(PALACE_ZHI)}

# 标准时支序号 (子=0 ... 亥=11), 用于数生时
_HOUR_ZHI_ORDER: List[str] = ["子", "丑", "寅", "卯", "辰", "巳",
                              "午", "未", "申", "酉", "戌", "亥"]

# 五行局: 名 -> 局数 (起紫微/起大限之用)
WU_XING_JU: Dict[str, int] = {
    "水二局": 2, "木三局": 3, "金四局": 4, "土五局": 5, "火六局": 6,
}

# 紫微星系 (随紫微顺时针, 隔一宫安一星)
ZIWEI_SERIES: List[str] = ["紫微", "天机", "太阳", "武曲", "天同", "廉贞"]
# 天府星系 (随天府逆时针, 隔一宫安一星)
TIANFU_SERIES: List[str] = ["天府", "太阴", "贪狼", "巨门",
                            "天相", "天梁", "七杀", "破军"]

# 生年十干四化 (化禄 / 化权 / 化科 / 化忌)
SIHUA_YEAR: Dict[str, Dict[str, str]] = {
    "甲": {"化禄": "廉贞", "化权": "破军", "化科": "武曲", "化忌": "太阳"},
    "乙": {"化禄": "天机", "化权": "天梁", "化科": "紫微", "化忌": "太阴"},
    "丙": {"化禄": "天同", "化权": "天机", "化科": "文昌", "化忌": "廉贞"},
    "丁": {"化禄": "太阴", "化权": "天同", "化科": "天机", "化忌": "巨门"},
    "戊": {"化禄": "贪狼", "化权": "太阴", "化科": "右弼", "化忌": "天机"},
    "己": {"化禄": "武曲", "化权": "贪狼", "化科": "天梁", "化忌": "文曲"},
    "庚": {"化禄": "太阳", "化权": "武曲", "化科": "太阴", "化忌": "天同"},
    "辛": {"化禄": "巨门", "化权": "太阳", "化科": "文曲", "化忌": "文昌"},
    "壬": {"化禄": "天梁", "化权": "紫微", "化科": "左辅", "化忌": "武曲"},
    "癸": {"化禄": "破军", "化权": "巨门", "化科": "太阴", "化忌": "贪狼"},
}


# ---------------------------------------------------------------------------
# 1. 公历 → 农历
# ---------------------------------------------------------------------------
def solar_to_lunar(year: int, month: int, day: int) -> Dict[str, Any]:
    """公历 → 农历.

    返回:
      lunar_year: 农历年 (干支年数, 以正月初一为界)
      lunar_month: 农历月 (1-12)
      lunar_day: 农历日 (1-30)
      is_leap: 是否闰月
      lunar_year_ganzhi: 年干支, 如 "甲子"
    """
    d = sxtwl.fromSolar(year, month, day)
    ygz = d.getYearGZ()
    gan = TIANGAN[ygz.tg]
    zhi = _HOUR_ZHI_ORDER[ygz.dz]  # sxtwl 地支序 0=子 ... 11=亥
    return {
        "lunar_year": d.getLunarYear(),
        "lunar_month": d.getLunarMonth(),
        "lunar_day": d.getLunarDay(),
        "is_leap": bool(d.isLunarLeap()),
        "lunar_year_ganzhi": gan + zhi,
        "year_gan": gan,
        "year_zhi": zhi,
    }


# ---------------------------------------------------------------------------
# 2. 定五行局
# ---------------------------------------------------------------------------
def _wuhu_dun_gan(year_gan: str, target_zhi: str) -> str:
    """五虎遁: 由年干推寅月起干, 再顺数至目标地支, 返回该地支上的天干.

    寅月起干: 甲己->丙, 乙庚->戊, 丙辛->庚, 丁壬->壬, 戊癸->甲.
    """
    yg = TIANGAN.index(year_gan)
    yin_gan = (yg % 5) * 2 + 2
    if yin_gan >= 10:
        yin_gan -= 10
    # 寅在固定环索引为 0; target_zhi 与寅的顺时针距离即偏移
    offset = _ZHI_TO_IDX[target_zhi] - _ZHI_TO_IDX["寅"]
    return TIANGAN[(yin_gan + offset) % 10]


# 数到的天干 -> 五行局 (简化规则: 不直接用命宫纳音)
_GAN_TO_JU: Dict[str, str] = {
    "甲": "水二局", "乙": "水二局",
    "丙": "木三局", "丁": "木三局",
    "戊": "金四局", "己": "金四局",
    "庚": "土五局", "辛": "土五局",
    "壬": "火六局", "癸": "火六局",
}


def determine_wuxing_ju(year_gan: str, hour_zhi: str,
                        month_zhi: str = "寅") -> Dict[str, Any]:
    """定五行局.

    简化规则: 五虎遁得寅月天干, 从寅起顺数到生时地支, 所得天干按
      甲乙->水二 / 丙丁->木三 / 戊己->金四 / 庚辛->土五 / 壬癸->火六
    定局。(实战派以命宫纳音为准, 此处为拓扑简化版。)
    """
    gan_at_hour = _wuhu_dun_gan(year_gan, hour_zhi)
    ju_name = _GAN_TO_JU[gan_at_hour]
    return {
        "ju_name": ju_name,
        "ju_num": WU_XING_JU[ju_name],
        "gan_at_hour": gan_at_hour,
    }


# ---------------------------------------------------------------------------
# 3. 起紫微 / 天府
# ---------------------------------------------------------------------------
def locate_ziwei(lunar_day: int, wuxing_ju_num: int) -> Dict[str, int]:
    """起紫微 / 天府.

    紫微: 从寅宫(0)起, 步长=局数, 按农历日定位:
        宫位序号 = (农历日 - 1) // 局数   (从寅起顺时针数, 0=寅)
    天府: 与紫微以寅申线对称 (寅->申, 卯->未 ...):
        tianfu_idx = (6 - ziwei_idx) % 12
    """
    ziwei_idx = ((lunar_day - 1) // wuxing_ju_num) % 12
    tianfu_idx = (6 - ziwei_idx) % 12
    return {"ziwei_pos": ziwei_idx, "tianfu_pos": tianfu_idx}


# ---------------------------------------------------------------------------
# 4. 安十四主星
# ---------------------------------------------------------------------------
def place_main_stars(ziwei_pos: int, tianfu_pos: int) -> Dict[int, List[str]]:
    """安十四主星, 返回 {宫位索引: [主星名, ...]}.

    紫微系 6 星: 从紫微起顺时针, 隔一宫安一星 (步长 +2).
    天府系 8 星: 从天府起逆时针, 隔一宫安一星 (步长 -2).
    """
    board: Dict[int, List[str]] = {i: [] for i in range(12)}

    # 紫微星系 (顺时针 +2)
    for k, star in enumerate(ZIWEI_SERIES):
        idx = (ziwei_pos + 2 * k) % 12
        board[idx].append(star)

    # 天府星系 (逆时针 -2)
    for k, star in enumerate(TIANFU_SERIES):
        idx = (tianfu_pos - 2 * k) % 12
        board[idx].append(star)

    return board


# ---------------------------------------------------------------------------
# 5. 安辅佐煞曜
# ---------------------------------------------------------------------------
# 禄存起宫 (年干 -> 地支)
_LUCUN: Dict[str, str] = {
    "甲": "寅", "乙": "卯", "丙": "巳", "戊": "巳",
    "丁": "午", "己": "午", "庚": "申", "辛": "酉",
    "壬": "亥", "癸": "子",
}

# 天魁 / 天钺 (年干 -> (魁, 钺))
_KUI_YUE: Dict[str, tuple] = {
    "甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
    "乙": ("子", "申"), "己": ("子", "申"),
    "丙": ("亥", "酉"), "丁": ("亥", "酉"),
    "辛": ("午", "寅"),
    "壬": ("卯", "巳"), "癸": ("卯", "巳"),
}

# 火星 / 铃星起宫 (年支三合局 -> (火, 铃))
_HUO_LING: Dict[str, tuple] = {
    "寅": ("卯", "丑"), "午": ("卯", "丑"), "戌": ("卯", "丑"),
    "申": ("寅", "戌"), "子": ("寅", "戌"), "辰": ("寅", "戌"),
    "巳": ("卯", "丑"), "酉": ("卯", "丑"), "丑": ("卯", "丑"),
    "亥": ("寅", "戌"), "卯": ("寅", "戌"), "未": ("寅", "戌"),
}


def place_aux_stars(year_gan: str, lunar_month: int, hour_zhi: str,
                    year_zhi: str = "") -> Dict[str, int]:
    """安辅佐煞曜, 返回 {星名: 宫位索引}.

    - 左辅: 辰起正月顺时针数至生月
    - 右弼: 戌起正月逆时针数至生月
    - 文昌: 戌起子时顺时针数至生时
    - 文曲: 辰起子时逆时针数至生时
    - 天魁/天钺: 依年干查表
    - 禄存: 依年干; 擎羊=禄存前一(顺), 陀罗=禄存后一(逆)
    - 火星/铃星: 依年支三合起, 顺数至生时 (需 year_zhi)
    - 地空: 亥起子时顺数至生时; 地劫: 子起子时顺数至生时
    """
    out: Dict[str, int] = {}
    m = lunar_month - 1                 # 正月 -> 0
    h = _HOUR_ZHI_ORDER.index(hour_zhi)  # 子 -> 0

    # 左辅 / 右弼
    out["左辅"] = (_ZHI_TO_IDX["辰"] + m) % 12
    out["右弼"] = (_ZHI_TO_IDX["戌"] - m) % 12

    # 文昌 / 文曲
    out["文昌"] = (_ZHI_TO_IDX["戌"] + h) % 12
    out["文曲"] = (_ZHI_TO_IDX["辰"] - h) % 12

    # 天魁 / 天钺
    kui, yue = _KUI_YUE[year_gan]
    out["天魁"] = _ZHI_TO_IDX[kui]
    out["天钺"] = _ZHI_TO_IDX[yue]

    # 禄存 / 擎羊 / 陀罗
    lucun = _ZHI_TO_IDX[_LUCUN[year_gan]]
    out["禄存"] = lucun
    out["擎羊"] = (lucun + 1) % 12
    out["陀罗"] = (lucun - 1) % 12

    # 地空 / 地劫
    out["地空"] = (_ZHI_TO_IDX["亥"] + h) % 12
    out["地劫"] = (_ZHI_TO_IDX["子"] + h) % 12

    # 火星 / 铃星 (需要年支)
    if year_zhi:
        huo_start, ling_start = _HUO_LING[year_zhi]
        out["火星"] = (_ZHI_TO_IDX[huo_start] + h) % 12
        out["铃星"] = (_ZHI_TO_IDX[ling_start] + h) % 12

    return out


# ---------------------------------------------------------------------------
# 6. 三方四正
# ---------------------------------------------------------------------------
def sanfang_sizheng(palace_idx: int) -> Dict[str, int]:
    """三方四正: 本宫 + 财帛(+4) + 官禄(+8) + 迁移对宫(+6)."""
    return {
        "命宫": palace_idx % 12,
        "财帛": (palace_idx + 4) % 12,
        "官禄": (palace_idx + 8) % 12,
        "迁移": (palace_idx + 6) % 12,
    }


# ---------------------------------------------------------------------------
# 7. 完整排盘入口
# ---------------------------------------------------------------------------
# 辅曜 (吉) / 煞曜 分类
_AUX_STARS = {"左辅", "右弼", "文昌", "文曲", "天魁", "天钺", "禄存"}
_SHA_STARS = {"擎羊", "陀罗", "火星", "铃星", "地空", "地劫"}


def setup_palaces(year_gan: str, year_zhi: str, lunar_month: int,
                  lunar_day: int, hour_zhi: str,
                  gender: str = "男") -> Dict[str, Any]:
    """完整排盘入口.

    流程: 定五行局 -> 起紫微天府 -> 安十四主星 -> 安辅佐煞曜 -> 安生年四化.
    """
    # 1. 五行局
    wx = determine_wuxing_ju(year_gan, hour_zhi)
    ju_name, ju_num = wx["ju_name"], wx["ju_num"]

    # 2. 紫微 / 天府
    pos = locate_ziwei(lunar_day, ju_num)
    zw, tf = pos["ziwei_pos"], pos["tianfu_pos"]

    # 3. 十四主星
    main_board = place_main_stars(zw, tf)

    # 4. 辅佐煞曜
    aux_pos = place_aux_stars(year_gan, lunar_month, hour_zhi, year_zhi)

    # 5. 生年四化
    sihua_year = SIHUA_YEAR[year_gan]
    # 反查: 化X星 -> 所在宫位 (主星或辅曜)
    star_to_palace: Dict[str, int] = {}
    for idx, stars in main_board.items():
        for s in stars:
            star_to_palace[s] = idx
    for star, idx in aux_pos.items():
        star_to_palace[star] = idx

    # 组装十二宫
    palaces: List[Dict[str, Any]] = []
    sihua_by_palace: Dict[int, List[str]] = {i: [] for i in range(12)}
    for hua_type, star in sihua_year.items():
        p = star_to_palace.get(star)
        if p is not None:
            sihua_by_palace[p].append(f"{star}{hua_type}")

    for i in range(12):
        aux_here = [s for s, p in aux_pos.items() if p == i and s in _AUX_STARS]
        sha_here = [s for s, p in aux_pos.items() if p == i and s in _SHA_STARS]
        palaces.append({
            "index": i,
            "name": PALACES_12[i],
            "zhi": PALACE_ZHI[i],
            "main_stars": main_board[i],
            "aux_stars": sorted(aux_here, key=lambda s: list(_AUX_STARS).index(s)),
            "sha_stars": sorted(sha_here, key=lambda s: list(_SHA_STARS).index(s)),
            "sihua": sihua_by_palace[i],
        })

    return {
        "wuxing_ju": {"name": ju_name, "num": ju_num},
        "ziwei_pos": zw,
        "tianfu_pos": tf,
        "ziwei_zhi": PALACE_ZHI[zw],
        "tianfu_zhi": PALACE_ZHI[tf],
        "gender": gender,
        "palaces": palaces,
        "sihua_year": sihua_year,
        "sanfang_sizheng": sanfang_sizheng(0),  # 命宫(0)三方四正
    }
