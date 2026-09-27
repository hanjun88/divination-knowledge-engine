"""
B4 — 动变力学分析 + 16应期法则状态机 + 标准化 AST 输出。

职责:
  1. analyze_dongbian: 对动爻的变爻做力学判定
     (回头生/回头克/化进/化退/化绝/化空/化墓)，累计量化分。
  2. compute_yingqi:    基于用神状态机锁定应期窗口 (地支)。
  3. build_ast:         将 CastResult 序列化为标准化 AST JSON，
                        rule_facts 字段直接对接 RuleEngine.match()。

量化分值 (沿用 deep_distill_v2 / INTERFACE_SPEC):
  回头生 +2.5 | 回头克 -3.0 | 化进 +1.5 | 化退 -1.5
  化绝 -2.0   | 化空 -1.0   | 化墓 -1.0

主要类型优先级:
  回头生/回头克 > 化绝 > 化进/退 > 化空/化墓
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from liuyao import CastResult, Fushen, Yao
from liuyao.najia import zhi_to_wx

# ---------------------------------------------------------------------------
# 基础常量表 (自包含)
# ---------------------------------------------------------------------------

#: 十二地支顺序
DIZHI: List[str] = ["子", "丑", "寅", "卯", "辰", "巳",
                    "午", "未", "申", "酉", "戌", "亥"]

#: 五行相生: a 生 b  (木->火->土->金->水->木)
WX_SHENG: Dict[str, str] = {
    "木": "火", "火": "土", "土": "金", "金": "水", "水": "木",
}
#: 五行相克: a 克 b  (木->土->水->火->金->木)
WX_KE: Dict[str, str] = {
    "木": "土", "土": "水", "水": "火", "火": "金", "金": "木",
}

#: 地支六冲
LIUCHONG: Dict[str, str] = {
    "子": "午", "午": "子", "丑": "未", "未": "丑",
    "寅": "申", "申": "寅", "卯": "酉", "酉": "卯",
    "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳",
}

#: 地支六合
LIUHE: Dict[str, str] = {
    "子": "丑", "丑": "子", "寅": "亥", "亥": "寅",
    "卯": "戌", "戌": "卯", "辰": "酉", "酉": "辰",
    "巳": "申", "申": "巳", "午": "未", "未": "午",
}

#: 十二长生 — 绝位 (金绝寅, 木绝申, 水绝巳, 火绝亥, 土绝巳寄水)
JUE_POS: Dict[str, str] = {
    "金": "寅", "木": "申", "水": "巳", "火": "亥", "土": "巳",
}

#: 十二长生 — 墓库 (金墓丑, 木墓未, 水墓辰, 火墓戌, 土墓辰)
MU_POS: Dict[str, str] = {
    "金": "丑", "木": "未", "水": "辰", "火": "戌", "土": "辰",
}

#: 十二长生 — 长生位 (化绝取长生为应期)
CHANGSHENG_POS: Dict[str, str] = {
    "金": "巳", "木": "亥", "水": "申", "火": "寅", "土": "申",
}

#: 化进神对 (动爻地支 -> 变爻地支)，按帝旺方向:
#:   木 寅->卯, 火 巳->午, 金 申->酉, 水 亥->子 (土寄水, 不单独论进退)
JINSHEN_PAIRS = {("寅", "卯"), ("巳", "午"), ("申", "酉"), ("亥", "子")}

#: 六甲旬空
XUNKONG: Dict[str, List[str]] = {
    "甲子": ["戌", "亥"], "甲戌": ["申", "酉"], "甲申": ["午", "未"],
    "甲午": ["辰", "巳"], "甲辰": ["寅", "卯"], "甲寅": ["子", "丑"],
}

#: 分值表
SCORE_HUITOU_SHENG = 2.5
SCORE_HUITOU_KE = -3.0
SCORE_HUAJIN = 1.5
SCORE_HUATUI = -1.5
SCORE_HUAJUE = -2.0
SCORE_HUAKONG = -1.0
SCORE_HUAMU = -1.0

TIMING_HINT = "近应日时, 远应年月"


# ---------------------------------------------------------------------------
# 1. 动变力学分析
# ---------------------------------------------------------------------------

def analyze_dongbian(
    yao: Yao,
    month_zhi: str,
    day_zhi: str,
    day_xun: str = "",
) -> Dict[str, Any]:
    """对动爻进行动变力学分析 (仅 is_dong=True 有意义)。

    一个动爻可能同时有多种变化，全部累计入 score；``type`` 按优先级取主要类型。

    返回:
        {"type": str, "score": float, "detail": str,
         "all_effects": [{"effect": str, "score": float}]}
    """
    effects: List[Dict[str, Any]] = []

    if not yao.is_dong or not yao.bian_zhi:
        result = {"type": "无", "score": 0.0,
                  "detail": "静爻或无变爻", "all_effects": effects}
        yao.dongbian_type = result["type"]
        yao.dongbian_score = 0.0
        return result

    yao_wx = yao.wx or zhi_to_wx(yao.zhi)
    bian_wx = yao.bian_wx or zhi_to_wx(yao.bian_zhi)

    def add(effect: str, score: float) -> None:
        effects.append({"effect": effect, "score": score})

    # --- 回头生 / 回头克 (最高优先级) ---
    hui_tou: str = ""
    if WX_SHENG.get(bian_wx) == yao_wx:
        hui_tou = "回头生"
        add("回头生", SCORE_HUITOU_SHENG)
    elif WX_KE.get(bian_wx) == yao_wx:
        hui_tou = "回头克"
        add("回头克", SCORE_HUITOU_KE)

    # 回头生/克 为最高优先级: 出现时不再叠加同级的化绝/化进退 (其力学方向已被
    # 回头生克主导); 化空/化墓为低级叠加项, 仍累计 (对应"回头生+化空"等情形)。
    if not hui_tou:
        # --- 化绝 ---
        hua_jue = JUE_POS.get(yao_wx) == yao.bian_zhi
        if hua_jue:
            add("化绝", SCORE_HUAJUE)

        # --- 化进 / 化退 (同五行相邻, 按帝旺方向) ---
        hua_jin = hua_tui = False
        if bian_wx == yao_wx:
            pair = (yao.zhi, yao.bian_zhi)
            if pair in JINSHEN_PAIRS:
                hua_jin = True
                add("化进", SCORE_HUAJIN)
            elif (yao.bian_zhi, yao.zhi) in JINSHEN_PAIRS:
                hua_tui = True
                add("化退", SCORE_HUATUI)
    else:
        hua_jue = hua_jin = hua_tui = False

    # --- 化空 (变爻旬空) ---
    hua_kong = bool(day_xun) and yao.bian_zhi in XUNKONG.get(day_xun, [])
    if hua_kong:
        add("化空", SCORE_HUAKONG)

    # --- 化墓 (变爻为动爻五行墓地) ---
    hua_mu = MU_POS.get(yao_wx) == yao.bian_zhi
    if hua_mu:
        add("化墓", SCORE_HUAMU)

    # --- 主要类型: 回头生/克 > 化绝 > 化进/退 > 化空/化墓 ---
    if hui_tou:
        main_type = hui_tou
    elif hua_jue:
        main_type = "化绝"
    elif hua_jin:
        main_type = "化进"
    elif hua_tui:
        main_type = "化退"
    elif hua_kong:
        main_type = "化空"
    elif hua_mu:
        main_type = "化墓"
    else:
        main_type = "无"

    total = round(sum(e["score"] for e in effects), 2)
    detail = (
        f"动爻{yao.zhi}({yao_wx})变{yao.bian_zhi}({bian_wx}): "
        + ("、".join(f"{e['effect']}{e['score']:+g}" for e in effects) or "无明显动变")
    )

    yao.dongbian_type = main_type if main_type != "无" else ""
    yao.dongbian_score = total

    return {
        "type": main_type,
        "score": total,
        "detail": detail,
        "all_effects": effects,
    }


# ---------------------------------------------------------------------------
# 2. 16 应期法则状态机
# ---------------------------------------------------------------------------

def _find_yao(yaos: List[Yao], pos: int) -> Optional[Yao]:
    return next((y for y in yaos if y.pos == pos), None)


def compute_yingqi(
    yaos: List[Yao],
    yong_shen_pos: int,
    month_zhi: str,
    day_zhi: str,
    day_xun: str = "",
) -> Dict[str, Any]:
    """基于用神和动爻状态锁定应期窗口 (地支)。

    状态机优先级 (越特殊越靠前):
      旬空 > 月破 > 化绝 > 回头克 > 回头生 > 化进 > 化退 > 入墓 > 发动 > 安静
    """
    empty = {
        "primary_window": "",
        "secondary_windows": [],
        "method": "未定",
        "timing_hint": TIMING_HINT,
    }
    yong = _find_yao(yaos, yong_shen_pos)
    if yong is None or not yong.zhi:
        return empty

    yz = yong.zhi
    primary = ""
    secondary: List[str] = []
    method = ""

    def push_secondary(z: str) -> None:
        if z and z not in secondary and z != primary:
            secondary.append(z)

    chong = LIUCHONG.get(yz, "")
    he = LIUHE.get(yz, "")

    # 3. 用神旬空 -> 出空 (填实=用神本支, 冲实=逢冲之支)
    if yong.xun_kong:
        primary = yz
        push_secondary(chong)
        method = "用神旬空出空(填实/冲实)"
    # 4. 用神月破 -> 破而逢合
    elif yong.yue_po:
        primary = he
        method = "用神月破逢合"
    # 8. 用神化绝 -> 待长生之地
    elif yong.dongbian_type == "化绝":
        primary = CHANGSHENG_POS.get(yong.wx or zhi_to_wx(yz), "")
        method = "用神化绝待长生"
    # 10. 用神回头克 -> 克神(变爻)受制逢冲
    elif yong.dongbian_type == "回头克" and yong.bian_zhi:
        primary = LIUCHONG.get(yong.bian_zhi, "")
        method = "用神回头克待克神受制"
    # 9. 用神回头生 -> 生神(变爻)当值
    elif yong.dongbian_type == "回头生" and yong.bian_zhi:
        primary = yong.bian_zhi
        method = "用神回头生待生神当值"
    # 6. 用神化进 -> 进神当值
    elif yong.dongbian_type == "化进" and yong.bian_zhi:
        primary = yong.bian_zhi
        method = "用神化进待进神当值"
    # 7. 用神化退 -> 退神当值
    elif yong.dongbian_type == "化退" and yong.bian_zhi:
        primary = yong.bian_zhi
        method = "用神化退待退神当值"
    # 5. 用神入墓 -> 冲墓之日
    elif yong.ru_mu:
        tomb = MU_POS.get(yong.wx or zhi_to_wx(yz), "")
        primary = LIUCHONG.get(tomb, "")
        method = "用神入墓待冲墓"
    # 2. 用神发动 -> 逢合之日
    elif yong.is_dong:
        primary = he
        push_secondary(chong)
        method = "用神发动逢合"
    # 1. 用神安静 -> 逢冲之日
    else:
        primary = chong
        push_secondary(he)
        method = "用神安静逢冲"

    # 次要窗口兜底: 冲/合始终作为参考
    if chong:
        push_secondary(chong)
    if he:
        push_secondary(he)
    # 排除当月/当日地支 (已临, 不待)
    secondary = [z for z in secondary if z not in (month_zhi, day_zhi)]

    return {
        "primary_window": primary,
        "secondary_windows": secondary,
        "method": method,
        "timing_hint": TIMING_HINT,
    }


# ---------------------------------------------------------------------------
# 3. 标准化 AST 输出
# ---------------------------------------------------------------------------

def _fushen_to_dict(fs: Optional[Fushen]) -> Optional[Dict[str, Any]]:
    if fs is None:
        return None
    return {
        "pos": fs.pos,
        "zhi": fs.zhi,
        "wx": fs.wx,
        "liuqin": fs.liuqin,
        "fei_pos": fs.fei_pos,
        "fei_zhi": fs.fei_zhi,
        "fei_ke_fu": fs.fei_ke_fu,
        "fei_sheng_fu": fs.fei_sheng_fu,
    }


def _yao_to_dict(y: Yao) -> Dict[str, Any]:
    return {
        "pos": y.pos,
        "value": y.value,
        "is_yang": y.is_yang,
        "is_dong": y.is_dong,
        "gan": y.gan,
        "zhi": y.zhi,
        "wx": y.wx,
        "liuqin": y.liuqin,
        "liushen": y.liushen,
        "wangshuai_score": y.wangshuai_score,
        "wangshuai_label": y.wangshuai_label,
        "xun_kong": y.xun_kong,
        "yue_po": y.yue_po,
        "ri_chong": y.ri_chong,
        "dongbian_type": y.dongbian_type or "",
        "dongbian_score": y.dongbian_score,
        "bian_zhi": y.bian_zhi,
        "bian_wx": y.bian_wx,
        "bian_liuqin": y.bian_liuqin,
    }


def _yao_to_line(y: Yao, day_zhi: str) -> Dict[str, Any]:
    """对齐 main.py LineState 的 facts 结构。"""
    return {
        "pos": y.pos,
        "zhi": y.zhi,
        "wx": y.wx,
        "liuqin": y.liuqin,
        "dong": y.is_dong,
        "bian": bool(y.bian_zhi),
        "an_dong": y.ri_chong and not y.is_dong,       # 静爻逢日冲=暗动
        "ri_po": y.ri_chong and not y.is_dong,          # 日破
        "yue_po": y.yue_po,
        "xun_kong": y.xun_kong,
        "mu": y.ru_mu,
        "jue": y.dongbian_type == "化绝",
        "jin_tui": y.dongbian_type in ("化进", "化退"),
        "wangshuai": y.wangshuai_label,
    }


def build_ast(cast_result: CastResult) -> Dict[str, Any]:
    """将完整排盘结果转为标准化 AST JSON，对接规则引擎 facts 格式。"""
    yaos = cast_result.yaos or []
    hx = cast_result.hexagram

    # 用神
    yong = _find_yao(yaos, cast_result.yong_shen_pos)
    yong_dict: Dict[str, Any] = {}
    if yong is not None:
        yong_dict = {
            "pos": yong.pos,
            "zhi": yong.zhi,
            "wx": yong.wx,
            "liuqin": yong.liuqin,
            "wangshuai_score": yong.wangshuai_score,
            "wangshuai_label": yong.wangshuai_label,
            "dong": yong.is_dong,
            "xun_kong": yong.xun_kong,
            "yue_po": yong.yue_po,
        }

    # 应期: 若集成层未填则现场计算
    ying_qi = dict(cast_result.ying_qi) if cast_result.ying_qi else compute_yingqi(
        yaos, cast_result.yong_shen_pos,
        cast_result.month_zhi, cast_result.day_zhi, cast_result.day_xun,
    )

    # 摘要
    wang_total = round(sum(y.wangshuai_score for y in yaos), 2)
    dong_count = sum(1 for y in yaos if y.is_dong)

    if yong is not None:
        if yong.xun_kong:
            kong_po_type = "用神旬空"
        elif yong.yue_po:
            kong_po_type = "用神月破"
        elif yong.ru_mu:
            kong_po_type = "用神入墓"
        else:
            kong_po_type = "无"
        if yong.wangshuai_score >= 2.0:
            daxiang = "吉"
        elif yong.wangshuai_score <= -2.0:
            daxiang = "凶"
        else:
            daxiang = "平"
        key_conclusion = (
            f"用神{yong.liuqin or ''}{yong.zhi}({yong.wx}){yong.wangshuai_label}，"
            f"应期约在{ying_qi.get('primary_window') or '未定'}支前后"
            f"（{ying_qi.get('method', '')}）"
        )
    else:
        kong_po_type = "无"
        daxiang = "平"
        key_conclusion = "用神未指定"

    # --- rule_facts: 扁平化对接 LiuyaoInput / RuleEngine.match() ---
    types = {y.dongbian_type for y in yaos if y.dongbian_type}
    yong_wx = yong.wx if yong is not None else ""

    def _dong_sheng_ke() -> Dict[str, int]:
        sheng = ke = 0
        for y in yaos:
            if not y.is_dong or y is yong or not y.wx:
                continue
            if WX_SHENG.get(y.wx) == yong_wx:
                sheng += 1
            elif WX_KE.get(y.wx) == yong_wx:
                ke += 1
        return {"sheng": sheng, "ke": ke}

    dsk = _dong_sheng_ke() if yong is not None else {"sheng": 0, "ke": 0}

    rule_facts: Dict[str, Any] = {
        "month_zh": cast_result.month_zhi,
        "day_zh": cast_result.day_zhi,
        "month_wx": zhi_to_wx(cast_result.month_zhi) if cast_result.month_zhi else "",
        "day_wx": zhi_to_wx(cast_result.day_zhi) if cast_result.day_zhi else "",
        "day_xun": cast_result.day_xun,
        "lines": [_yao_to_line(y, cast_result.day_zhi) for y in yaos],
        "yong_shen": _yao_to_line(yong, cast_result.day_zhi) if yong is not None else {},
        "dong_count": dong_count,
        # 动变标志
        "hua_jin_shen": "化进" in types,
        "hua_tui_shen": "化退" in types,
        "hua_jue": "化绝" in types,
        "hua_mu": "化墓" in types,
        "hua_kong": "化空" in types,
        "bian_sheng_benwei": "回头生" in types,
        "bian_ke_benwei": "回头克" in types,
        "dong_lines_sheng_yong": dsk["sheng"],
        "dong_lines_ke_yong": dsk["ke"],
        "ke_yong_dong_count": dsk["ke"],
        # 用神状态
        "yong_bu_xian": yong is None,
        "yong_two_xian": yong is not None and cast_result.fushen is None,
        "ru_mu": bool(yong.ru_mu) if yong else False,
        "shi_kong": False,
        "yuepo_feng_he": bool(yong.yue_po) if yong else False,
        "daxiang": daxiang,
        "net_score": int(round(wang_total)),
    }

    ast: Dict[str, Any] = {
        "meta": {
            "engine": "liuyao-najia-core",
            "version": "1.0.0",
            "input_values": list(cast_result.input_values),
            "datetime": cast_result.datetime,
        },
        "hexagram": {
            "ben_gua": hx.ben_gua_name if hx else "",
            "ben_id": hx.ben_gua_id if hx else 0,
            "bian_gua": hx.bian_gua_name if hx else "",
            "bian_id": hx.bian_gua_id if hx else 0,
            "palace": hx.palace if hx else "",
            "palace_wx": hx.palace_wx if hx else "",
            "shi_pos": hx.shi_pos if hx else 0,
            "ying_pos": hx.ying_pos if hx else 0,
            "shi_type": hx.shi_type if hx else "",
        },
        "time": {
            "month_gan": cast_result.month_gan,
            "month_zhi": cast_result.month_zhi,
            "month_wx": zhi_to_wx(cast_result.month_zhi) if cast_result.month_zhi else "",
            "day_gan": cast_result.day_gan,
            "day_zhi": cast_result.day_zhi,
            "day_wx": zhi_to_wx(cast_result.day_zhi) if cast_result.day_zhi else "",
            "day_xun": cast_result.day_xun,
        },
        "yaos": [_yao_to_dict(y) for y in yaos],
        "fushen": _fushen_to_dict(cast_result.fushen),
        "yong_shen": yong_dict,
        "ying_qi": ying_qi,
        "summary": {
            "wang_shuai_total": wang_total,
            "dong_count": dong_count,
            "kong_po_type": kong_po_type,
            "daxiang": daxiang,
            "key_conclusion": key_conclusion,
        },
        "rule_facts": rule_facts,
    }
    return ast
