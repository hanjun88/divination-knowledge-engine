"""
cast.py — 端到端六爻排盘集成层 (I1)

将 B1~B4 四个模块串联为一条完整管线:

    values + 干支时间
        │
        ▼  B1  hexagram.py
    cast_hexagram            → 本卦/变卦 binary, id, name, 动爻位置
    find_palace_and_shiying  → 八宫, 世应
        │
        ▼  B2  najia.py
    逐爻纳甲 / 五行 / 六亲 / 六神; 动爻取变爻地支
        │
        ▼  B3  wangshuai.py
    旬首 → 逐爻旺衰分 / 旬空 / 月破 / 日冲 / 入墓
        │
        ▼  B4  dongbian.py
    动爻动变力学 → 用神定位(含伏神) → 应期窗口
        │
        ▼
    CastResult  (build_ast 序列化为规则引擎可消费的 AST JSON)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import Fushen, HexagramInfo, Yao, CastResult
from .dongbian import analyze_dongbian, build_ast, compute_yingqi
from .hexagram import cast_hexagram, find_palace_and_shiying
from .najia import (
    assign_liushen,
    assign_liuqin,
    bian_zhi_for_yao,
    najia_for_palace,
    zhi_to_wx,
)
from .wangshuai import (
    check_ru_mu,
    check_ri_chong,
    check_xun_kong,
    check_yue_po,
    compute_wangshuai,
    find_fushen,
    get_xun_shou,
)


# ---------------------------------------------------------------------------
# 占问领域 → 用神六亲 映射
# ---------------------------------------------------------------------------
#: 领域关键词 -> 用神六亲。按关键词命中即返回, 顺序即优先级。
_DOMAIN_KEYWORDS: List[tuple] = [
    # 事业 / 官运 / 官司 -> 官鬼
    (("官运", "事业", "工作", "求职", "升迁", "升职", "仕途", "官非", "官司", "诉讼", "纠纷"), "官鬼"),
    # 财运 / 投资 -> 妻财
    (("财运", "投资", "生意", "交易", "求财", "买卖", "利润"), "妻财"),
    # 感情 / 婚姻 -> 妻财 (男问默认; 女问可传 "官鬼" 覆盖)
    (("感情", "婚姻", "复合", "恋爱", "桃花", "姻缘", "对象"), "妻财"),
    # 健康 / 疾病 -> 官鬼 (病神)
    (("健康", "疾病", "生病", "病", "求医", "身体"), "官鬼"),
    # 学业 / 考试 / 出行 / 迁移 -> 父母
    (("学业", "考试", "升学", "文凭", "证书", "文章", "出行", "迁移", "旅行", "搬家", "调动", "车船"), "父母"),
    # 子女 / 医药 / 解忧 -> 子孙
    (("子女", "后代", "医药", "医生", "解忧", "福德"), "子孙"),
]

#: 缺省用神: 以世应关系为主 (cast() 中无法按六亲命中时回退)
_DEFAULT_YONG_SHEN = "应爻"


def determine_yong_shen(domain: str) -> str:
    """根据占问领域自动确定用神六亲。

    返回值为六亲之一 ("父母"/"兄弟"/"子孙"/"妻财"/"官鬼"); 若领域无法识别,
    返回特殊标记 "应爻" (表示以世应关系论, cast() 会退化到不按六亲取用神)。
    """
    if not domain:
        return _DEFAULT_YONG_SHEN
    text = str(domain)
    for keywords, liuqin in _DOMAIN_KEYWORDS:
        for kw in keywords:
            if kw in text:
                return liuqin
    return _DEFAULT_YONG_SHEN


# ---------------------------------------------------------------------------
# 端到端排盘
# ---------------------------------------------------------------------------
def cast(
    values: List[int],
    month_gan: str,
    month_zhi: str,
    day_gan: str,
    day_zhi: str,
    yong_shen_liuqin: str = "妻财",
    datetime_str: str = "",
) -> CastResult:
    """端到端六爻排盘。

    参数:
        values: 6 个爻值, 初爻->上爻; 6=老阴 7=少阳 8=少阴 9=老阳。
        month_gan/month_zhi: 月建干支。
        day_gan/day_zhi: 日辰干支。
        yong_shen_liuqin: 用神六亲 (默认 "妻财")。
        datetime_str: 占问时间描述 (ISO 或可读串), 仅记录。
    """
    result = CastResult(
        input_values=list(values),
        datetime=datetime_str,
        month_gan=month_gan,
        month_zhi=month_zhi,
        day_gan=day_gan,
        day_zhi=day_zhi,
    )

    # 1) B1 成卦 + 八宫世应 ---------------------------------------------------
    hex_res = cast_hexagram(values)
    palace_res = find_palace_and_shiying(hex_res["ben_binary"], hex_res["bian_binary"])
    palace: str = palace_res["palace"]
    palace_wx: str = palace_res["palace_wx"]
    result.hexagram = HexagramInfo(
        ben_gua_name=hex_res["ben_name"],
        ben_gua_id=hex_res["ben_id"],
        bian_gua_name=hex_res["bian_name"],
        bian_gua_id=hex_res["bian_id"],
        palace=palace,
        palace_wx=palace_wx,
        shi_pos=palace_res["shi_pos"],
        ying_pos=palace_res["ying_pos"],
        shi_type=palace_res["shi_type"],
    )

    # 4) B3 旬首 (先算, 旺衰/动变都要用) --------------------------------------
    day_xun = get_xun_shou(day_gan, day_zhi)
    result.day_xun = day_xun

    # 2)+3) B2 逐爻纳甲 + B3 旺衰 --------------------------------------------
    yaos: List[Yao] = []
    for idx, v in enumerate(values):
        pos = idx + 1
        is_yang = v in (7, 9)
        is_dong = v in (6, 9)

        gan, zhi = najia_for_palace(palace, pos)
        wx = zhi_to_wx(zhi)
        liuqin = assign_liuqin(palace_wx, wx)
        liushen = assign_liushen(day_gan, pos)

        y = Yao(
            pos=pos,
            value=v,
            is_yang=is_yang,
            is_dong=is_dong,
            gan=gan,
            zhi=zhi,
            wx=wx,
            liuqin=liuqin,
            liushen=liushen,
        )

        # 动爻 -> 变爻纳支 / 变爻五行 / 变爻六亲 (六亲仍以本宫五行为"我")
        if is_dong:
            bian_zhi = bian_zhi_for_yao(palace, pos, hex_res["bian_binary"])
            bian_wx = zhi_to_wx(bian_zhi)
            y.bian_zhi = bian_zhi
            y.bian_wx = bian_wx
            y.bian_liuqin = assign_liuqin(palace_wx, bian_wx)

        # B3 旺衰 + 神煞
        ws = compute_wangshuai(wx, month_zhi, day_zhi, is_dong, zhi)
        y.wangshuai_score = float(ws["score"])
        y.wangshuai_label = ws["label"]
        y.yue_sheng = bool(ws["yue_sheng"])
        y.yue_ke = bool(ws["yue_ke"])
        y.ri_sheng = bool(ws["ri_sheng"])
        y.xun_kong = check_xun_kong(day_xun, zhi)
        y.yue_po = check_yue_po(month_zhi, zhi)
        y.ri_chong = check_ri_chong(day_zhi, zhi)
        y.ru_mu = check_ru_mu(wx, zhi)

        yaos.append(y)

    result.yaos = yaos

    # 6) B4 动变力学 (仅动爻) -------------------------------------------------
    for y in yaos:
        if y.is_dong:
            analyze_dongbian(y, month_zhi, day_zhi, day_xun)

    # 7) 用神定位: 优先取本卦首见六亲; 不现则找伏神 ---------------------------
    yong_shen_pos = 0
    fushen: Optional[Fushen] = None
    for y in yaos:
        if y.liuqin == yong_shen_liuqin:
            yong_shen_pos = y.pos
            break

    if yong_shen_pos == 0:
        fs = find_fushen(yaos, palace, yong_shen_liuqin)
        if fs is not None:
            fushen = Fushen(
                pos=fs["pos"],
                zhi=fs["zhi"],
                wx=fs["wx"],
                liuqin=fs["liuqin"],
                fei_pos=fs["fei_pos"],
                fei_zhi=fs["fei_zhi"],
                fei_ke_fu=bool(fs["fei_ke_fu"]),
                fei_sheng_fu=bool(fs["fei_sheng_fu"]),
            )
            yong_shen_pos = fs["pos"]  # 飞神爻位, 供应期/AST 引用真实爻
        # 既无本卦六亲也无伏神 -> yong_shen_pos 保持 0, compute_yingqi 会优雅退化

    result.fushen = fushen
    result.yong_shen_pos = yong_shen_pos

    # 8) B4 应期窗口 ----------------------------------------------------------
    result.ying_qi = compute_yingqi(
        yaos, yong_shen_pos, month_zhi, day_zhi, day_xun
    )

    # 9) 摘要 ---------------------------------------------------------------
    dong_count = sum(1 for y in yaos if y.is_dong)
    result.summary = {
        "palace": palace,
        "palace_wx": palace_wx,
        "ben_gua": result.hexagram.ben_gua_name,
        "bian_gua": result.hexagram.bian_gua_name,
        "shi_pos": result.hexagram.shi_pos,
        "ying_pos": result.hexagram.ying_pos,
        "dong_count": dong_count,
        "yong_shen_liuqin": yong_shen_liuqin,
        "yong_shen_pos": yong_shen_pos,
        "has_fushen": fushen is not None,
    }

    return result


# ---------------------------------------------------------------------------
# 端到端 + AST
# ---------------------------------------------------------------------------
def cast_to_ast(
    values: List[int],
    month_gan: str,
    month_zhi: str,
    day_gan: str,
    day_zhi: str,
    yong_shen_liuqin: str = "妻财",
    datetime_str: str = "",
) -> Dict[str, Any]:
    """端到端排盘并直接输出标准 AST JSON (rule_facts 对接 RuleEngine.match)。"""
    result = cast(
        values, month_gan, month_zhi, day_gan, day_zhi,
        yong_shen_liuqin=yong_shen_liuqin, datetime_str=datetime_str,
    )
    return build_ast(result)
