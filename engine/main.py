"""
FastAPI service for the Divination Rule Engine.

Endpoints:
  GET  /health
  GET  /api/rules/{domain}
  POST /api/liuyao/analyze
  POST /api/ziwei/analyze
  POST /api/bazi/analyze

Run:
  uvicorn main:app --reload
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from rule_engine import RuleEngine, get_engine

app = FastAPI(
    title="Divination Rule Engine",
    description="六爻 / 紫微 / 八字 规则引擎服务 (DSL -> JSON -> FastAPI)",
    version="1.0.0",
)

engine: RuleEngine = get_engine()


# ---------------------------------------------------------------------------
# Pydantic input models
# ---------------------------------------------------------------------------

class LineState(BaseModel):
    pos: int = Field(0, description="爻位 1~6")
    zhi: str = Field("", description="地支")
    wx: str = Field("", description="五行")
    liuqin: str = Field("", description="六亲")
    dong: bool = False
    bian: bool = False
    an_dong: bool = False
    ri_po: bool = False
    yue_po: bool = False
    xun_kong: bool = False
    mu: bool = False
    jue: bool = False
    jin_tui: bool = False
    wangshuai: str = "平"


class LiuyaoInput(BaseModel):
    month_zh: str = Field(..., description="月建地支 如 寅")
    day_zh: str = Field(..., description="日辰地支 如 申")
    month_wx: str = Field("", description="月建五行")
    day_wx: str = Field("", description="日辰五行")
    day_xun: str = Field("", description="旬首")
    lines: List[LineState] = Field(default_factory=list)
    yong_shen: LineState
    yuan_shen: Optional[LineState] = None
    ji_shen: Optional[LineState] = None
    chou_shen: Optional[LineState] = None
    has_ri_dong_sheng: bool = False
    ke_yong_dong_count: int = 0
    yuepo_feng_he: bool = False
    bian_sheng_benwei: bool = False
    bian_ke_benwei: bool = False
    bian_chong_benwei: bool = False
    bian_he_benwei: bool = False
    hua_jin_shen: bool = False
    hua_tui_shen: bool = False
    hua_diwang: bool = False
    hua_mu: bool = False
    hua_jue: bool = False
    hua_kong: bool = False
    hua_guan_gui: bool = False
    fu_yin: bool = False
    he_ban: bool = False
    dong_lines_sheng_yong: int = 0
    dong_lines_ke_yong: int = 0
    dong_lines_he_dong: int = 0
    dong_lines_he_jing: int = 0
    dong_lines_chong_jing: int = 0
    dong_lines_chong_dong: int = 0
    dong_lines_tan_wang: int = 0
    yuan_shen_you_li: bool = False
    yuan_shen_wu_li: bool = False
    ji_shen_you_li: bool = False
    ji_shen_wu_li: bool = False
    yuan_shen: Optional[LineState] = None  # noqa: F811 - intentional override
    yong_two_xian: bool = False
    yong_bu_xian: bool = False
    du_fa_or_du_jing: bool = False
    daxiang: str = "平"
    net_score: int = 0
    ru_mu: bool = False
    feng_he: bool = False
    shi_kong: bool = False


class PalaceInput(BaseModel):
    palace: str
    main_stars: List[str] = Field(default_factory=list)
    aux_stars: List[str] = Field(default_factory=list)
    sha_stars: List[str] = Field(default_factory=list)
    si_hua: List[str] = Field(default_factory=list)
    palace_pos: str = ""
    wang: bool = True

    class Config:
        extra = "allow"


class ZiweiInput(BaseModel):
    ming_gong: PalaceInput
    xiandi_gong: Optional[PalaceInput] = None  # 对宫
    sanfang_sizheng: List[str] = Field(default_factory=list, description="三方四正主星合集")
    sanfang_sizheng_sihua: List[str] = Field(default_factory=list)
    yutai_gong: Optional[PalaceInput] = None
    guanlu_gong: Optional[PalaceInput] = None
    caibo_gong: Optional[PalaceInput] = None
    tianzhai_gong: Optional[PalaceInput] = None
    fude_gong: Optional[PalaceInput] = None
    jie_gong: Optional[PalaceInput] = None
    fuqi_gong: Optional[PalaceInput] = None
    fu_mu_gong: Optional[PalaceInput] = None
    taiyang_gong: Optional[PalaceInput] = None
    taiyin_gong: Optional[PalaceInput] = None
    da_xian: Optional[PalaceInput] = None
    liu_nian: Optional[PalaceInput] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class BaziInput(BaseModel):
    year_gan: str = ""
    year_zhi: str = ""
    month_gan: str = ""
    month_zhi: str = ""
    day_gan: str = ""
    day_zhi: str = ""
    hour_gan: str = ""
    hour_zhi: str = ""
    dayun: str = ""
    liunian: str = ""
    geju: str = ""
    ri_zhu_wx: str = ""
    ri_zhu_wangshuai: str = "平"
    ri_zhu_wang_ji: str = ""
    has_water: bool = False
    has_mu: bool = False
    has_huo: bool = False
    has_tu: bool = False
    has_jin: bool = False
    tu_zhong: bool = False
    cai_xing_you: bool = False
    cai_xing_zhong: bool = False
    cai_xing_ruo: bool = False
    cai_xing_duo: bool = False
    guan_sha_you: bool = False
    sha_xing_zhong: bool = False
    yin_xing_you: bool = False
    shi_shang_you: bool = False
    bi_jie_zhong: bool = False
    zheng_guan_you: bool = False
    qi_sha_you: bool = False
    xiao_yin_you: bool = False
    shi_shen_you: bool = False
    dayun_sheng_yongshen: bool = False
    dayun_ke_yongshen: bool = False
    dayun_ni_shi: bool = False
    dayun_xi: bool = False
    dayun_ji: bool = False
    dayun_bu_que: bool = False
    liunian_xi: bool = False
    liunian_ji: bool = False
    yuanju_que_xing: bool = False
    wuxing_zhonghe: bool = False
    sizhu_liutong: bool = False
    shun_ni: str = ""
    guoji_buji: bool = False
    extra: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Response shape
# ---------------------------------------------------------------------------

class AnalyzeResponse(BaseModel):
    domain: str
    matched_rules: List[Dict[str, Any]]
    conclusions: List[str]
    total_weight: int
    matched_count: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _flat_ziwei(d: ZiweiInput) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    palace_map = {
        "命宫": d.ming_gong,
        "对宫": d.xiandi_gong,
        "财帛宫": d.caibo_gong,
        "官禄宫": d.guanlu_gong,
        "田宅宫": d.tianzhai_gong,
        "福德宫": d.fude_gong,
        "疾厄宫": d.jie_gong,
        "夫妻宫": d.fuqi_gong,
        "父母宫": d.fu_mu_gong,
    }
    for name, p in palace_map.items():
        if p is None:
            continue
        out[name] = {
            "主星": p.main_stars,
            "辅星": p.aux_stars,
            "煞星": p.sha_stars,
            "四化": p.si_hua,
            "宫位": p.palace_pos,
            "庙旺": p.wang,
        }
        out[f"{name}.主星"] = p.main_stars
        out[f"{name}.辅星"] = p.aux_stars
        out[f"{name}.煞星"] = p.sha_stars
        out[f"{name}.四化"] = p.si_hua
        out[f"{name}.宫位"] = p.palace_pos
        out[f"{name}.庙旺"] = p.wang
        out[f"{name}.煞星_count"] = len(p.sha_stars)
        out[f"{name}.吉星_count"] = len([s for s in p.aux_stars
                                          if s in ("左辅", "右弼", "文昌", "文曲",
                                                   "天魁", "天钺", "禄存", "化禄",
                                                   "化权", "化科")])
    out["三方四正.主星"] = d.sanfang_sizheng
    out["三方四正.四化"] = d.sanfang_sizheng_sihua
    if d.taiyang_gong:
        out["太阳.宫位"] = d.taiyang_gong.palace_pos
    if d.taiyin_gong:
        out["太阴.宫位"] = d.taiyin_gong.palace_pos
    if d.da_xian:
        out["大限.四化"] = d.da_xian.si_hua
    if d.liu_nian:
        out["流年.四化"] = d.liu_nian.si_hua
    out.update(d.extra or {})
    return out


def _flat_bazi(d: BaziInput) -> Dict[str, Any]:
    out = d.dict()
    out["ri_zhu.gan"] = d.day_gan
    out["ri_zhu.wx"] = d.ri_zhu_wx
    out["ri_zhu.wang_shuai"] = d.ri_zhu_wangshuai
    out["ri_zhu.wang_ji"] = d.ri_zhu_wang_ji
    out["month.zhi"] = d.month_zhi
    out["cai_xing.you"] = d.cai_xing_you
    out["cai_xing.duo"] = d.cai_xing_duo
    out["cai_xing.zhong"] = d.cai_xing_zhong
    out["cai_xing.ruo"] = d.cai_xing_ruo
    out["guan_sha.you"] = d.guan_sha_you
    out["sha_xing.zhong"] = d.sha_xing_zhong
    out["yin_xing.you"] = d.yin_xing_you
    out["shi_shang.you"] = d.shi_shang_you
    out["zheng_guan.you"] = d.zheng_guan_you
    out["qi_sha.you"] = d.qi_sha_you
    out["xiao_yin.you"] = d.xiao_yin_you
    out["shi_shen.you"] = d.shi_shen_you
    out["dayun.xi"] = d.dayun_xi
    out["dayun.ji"] = d.dayun_ji
    out["liunian.xi"] = d.liunian_xi
    out["liunian.ji"] = d.liunian_ji
    out["yuanju.que_xing"] = d.yuanju_que_xing
    out["dayun.bu_que"] = d.dayun_bu_que
    out["dayun.ke"] = d.dayun_ke_yongshen
    out.update(d.extra or {})
    return out


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "domains": {
            "liuyao": len(engine.load_rules("liuyao")),
            "ziwei": len(engine.load_rules("ziwei")),
            "bazi": len(engine.load_rules("bazi")),
        },
    }


@app.get("/api/rules/{domain}")
def list_rules(domain: str) -> Dict[str, Any]:
    try:
        return engine.list_rules(domain)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/liuyao/analyze", response_model=AnalyzeResponse)
def liuyao_analyze(payload: LiuyaoInput) -> AnalyzeResponse:
    facts = payload.dict()
    res = engine.match(facts, "liuyao")
    return AnalyzeResponse(domain="liuyao", **res)


@app.post("/api/ziwei/analyze", response_model=AnalyzeResponse)
def ziwei_analyze(payload: ZiweiInput) -> AnalyzeResponse:
    facts = _flat_ziwei(payload)
    res = engine.match(facts, "ziwei")
    return AnalyzeResponse(domain="ziwei", **res)


@app.post("/api/bazi/analyze", response_model=AnalyzeResponse)
def bazi_analyze(payload: BaziInput) -> AnalyzeResponse:
    facts = _flat_bazi(payload)
    res = engine.match(facts, "bazi")
    return AnalyzeResponse(domain="bazi", **res)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
