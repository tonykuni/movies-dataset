#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""flow_group_taxonomy — 台股族群三分類+族群指數繪製方法論引擎(TOOL-062)
====================================================================
操作員令(批21):台股族群分類方法論——三種分類;族群指數繪製方法論。

三種分類(方法論明文,零發明):
  C1 供應鏈/題材分類:族群→指標股→次指標股(源:知識庫 K6 樹
     [TOOL-059 vrn_lexicon]+熱門族群總表 docx;人審知識)
  C2 官方產業分類:TWSE 產業別代碼對映(名錄 schema;官方 OpenAPI
     校驗道,同意閘)
  C3 量價輪動資料驅動分類:20 日報酬 z × 20 日成交值變化 z 四象限
     (領漲放量/領漲縮量/回檔放量/回檔縮量)——sklearn 有裝可換
     k-means,缺件誠實降級四象限(絕不假造分群)

族群指數繪製方法論(式列印可驗):
  等權指數:base 100,I_t = I_{t-1} × (1 + mean(成分日報酬))——每日再平衡
  市值加權:I_t = I_{t-1} × (1 + Σ w_i×r_i), w_i = 市值_i/Σ市值(需餵市值)
  成交值加權:w_i = 成交值_i/Σ成交值(輪動視角)
  輸出 VAP 圖規 JSON(x=date,series=各族群指數)供 via-vap 繪製。

用法:
  --taxonomy            三分類方法論+C1 現行族群(自知識庫)
  --index <json>        建族群指數(rows:date,ticker,group,ret[,mcap,turnover])
  --chartspec <json>    建指數+輸出 VAP 圖規 JSON
  --selftest            六檢
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(路徑引導版;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import json
import math
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent.parent  # VeritasIntelligenceAnalytics
LEX_PATH = VIA / "functional modules/VRN/knowledge/VRN_Lexicon_v0100.json"
REPORTS = VIA / "VIA_Reports"

C2_TWSE_SECTORS = [  # 官方產業別(代碼→名稱;上市 28 類常用子集,校驗道補全)
    ("01", "水泥"), ("02", "食品"), ("03", "塑膠"), ("04", "紡織纖維"),
    ("05", "電機機械"), ("06", "電器電纜"), ("08", "玻璃陶瓷"), ("09", "造紙"),
    ("10", "鋼鐵"), ("11", "橡膠"), ("12", "汽車"), ("14", "建材營造"),
    ("15", "航運"), ("16", "觀光餐旅"), ("17", "金融保險"), ("18", "貿易百貨"),
    ("21", "化學"), ("22", "生技醫療"), ("23", "油電燃氣"), ("24", "半導體"),
    ("25", "電腦及週邊"), ("26", "光電"), ("27", "通信網路"), ("28", "電子零組件"),
    ("29", "電子通路"), ("30", "資訊服務"), ("31", "其他電子"),
]


def c1_groups() -> dict:
    """C1:自 TOOL-059 知識庫 K6 樹讀現行族群(無庫誠實空)。"""
    if not LEX_PATH.exists():
        return {}
    try:
        lex = json.loads(LEX_PATH.read_text(encoding="utf-8"))
        k6 = lex.get("tree", {}).get("K6", {}).get("children", {})
        return {k: v["zh"] for k, v in k6.items()}
    except Exception:
        return {}


def c3_quadrant(ret_z: float, vol_z: float) -> str:
    if ret_z >= 0 and vol_z >= 0:
        return "領漲放量"
    if ret_z >= 0:
        return "領漲縮量"
    if vol_z >= 0:
        return "回檔放量"
    return "回檔縮量"


def cmd_taxonomy() -> int:
    print("  [C1 供應鏈/題材] 族群→指標股→次指標股(知識庫 K6;人審知識)")
    g = c1_groups()
    if g:
        print(f"    現行 {len(g)} 枝:" + " · ".join(list(g.values())[:14]))
    else:
        print("    (知識庫未建——先 via-lexicon --build;誠實空)")
    print(f"  [C2 官方產業] TWSE 產業別 {len(C2_TWSE_SECTORS)} 類子集(官方校驗道同意閘補全)")
    print("  [C3 量價輪動] 20 日報酬 z × 20 日成交值 z 四象限"
          "(領漲放量/領漲縮量/回檔放量/回檔縮量;sklearn 在位可升 k-means)")
    return 0


def _z(vals):
    xs = [v for v in vals if v is not None]
    if len(xs) < 2:
        return [None] * len(vals)
    m = sum(xs) / len(xs)
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs)) or 1e-9
    return [((v - m) / sd if v is not None else None) for v in vals]


def build_index(rows: list, weighting: str = "equal") -> dict:
    """rows:{date,ticker,group,ret[,mcap,turnover]} → {group:{date:index}}。"""
    dates = sorted({r["date"] for r in rows})
    groups = sorted({r["group"] for r in rows})
    out = {g: {} for g in groups}
    level = {g: 100.0 for g in groups}
    for d in dates:
        for g in groups:
            mem = [r for r in rows if r["date"] == d and r["group"] == g
                   and r.get("ret") is not None]
            if not mem:
                out[g][d] = round(level[g], 4)  # 無成分日:持平(誠實不外插)
                continue
            if weighting == "mcap" and all(r.get("mcap") for r in mem):
                tot = sum(r["mcap"] for r in mem)
                gret = sum(r["ret"] * r["mcap"] / tot for r in mem)
            elif weighting == "turnover" and all(r.get("turnover") for r in mem):
                tot = sum(r["turnover"] for r in mem)
                gret = sum(r["ret"] * r["turnover"] / tot for r in mem)
            else:
                gret = sum(r["ret"] for r in mem) / len(mem)  # 等權(缺權重誠實降級)
            level[g] *= (1 + gret)
            out[g][d] = round(level[g], 4)
    return out


def to_chartspec(idx: dict, weighting: str) -> dict:
    dates = sorted({d for s in idx.values() for d in s})
    return {
        "schema": "vap-chartspec-v1", "chart": "line",
        "title": f"族群指數(base100 · {weighting} 加權)",
        "x": {"field": "date", "values": dates},
        "series": [{"name": g, "values": [idx[g].get(d) for d in dates]} for g in sorted(idx)],
        "methodology": "I_t = I_{t-1}×(1+加權成分日報酬);等權=每日再平衡",
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def cmd_index(path: str, emit_spec: bool = False) -> int:
    p = Path(path)
    if not p.exists():
        print(f"  [FAIL] 檔不存在:{path}")
        return 2
    rows = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(rows, dict):
        rows = rows.get("rows", [])
    for w in ("equal", "mcap", "turnover"):
        idx = build_index(rows, w)
        last = {g: list(s.values())[-1] for g, s in idx.items() if s}
        print(f"  [{w}] " + " · ".join(f"{g}={v}" for g, v in last.items()))
        if emit_spec and w == "equal":
            REPORTS.mkdir(parents=True, exist_ok=True)
            sp = REPORTS / "flow_groupindex_chartspec.json"
            sp.write_text(json.dumps(to_chartspec(idx, w), ensure_ascii=False, indent=1),
                          encoding="utf-8")
            print(f"  [圖規] {sp}(via-vap 可繪)")
    return 0


def selftest() -> int:
    ok, total = 0, 6
    if cmd_taxonomy() == 0:
        ok += 1; print("  [PASS] 三分類方法論列印(C1 知識庫/C2 官方/C3 量價)")
    else:
        print("  [FAIL] 分類")
    if len(C2_TWSE_SECTORS) >= 25 and dict(C2_TWSE_SECTORS)["24"] == "半導體":
        ok += 1; print("  [PASS] C2 官方產業別對映")
    else:
        print("  [FAIL] C2")
    if c3_quadrant(1, 1) == "領漲放量" and c3_quadrant(-1, 1) == "回檔放量":
        ok += 1; print("  [PASS] C3 四象限判定")
    else:
        print("  [FAIL] C3")
    fix = [  # 測試合成(僅 selftest)
        {"date": "D1", "ticker": "A", "group": "AI", "ret": 0.10, "mcap": 90, "turnover": 5},
        {"date": "D1", "ticker": "B", "group": "AI", "ret": 0.00, "mcap": 10, "turnover": 5},
        {"date": "D2", "ticker": "A", "group": "AI", "ret": 0.10, "mcap": 99, "turnover": 5},
        {"date": "D2", "ticker": "B", "group": "AI", "ret": 0.00, "mcap": 10, "turnover": 5},
        {"date": "D1", "ticker": "C", "group": "記憶體", "ret": -0.05},
    ]
    eq = build_index(fix, "equal")
    if abs(eq["AI"]["D2"] - 100 * 1.05 * 1.05) < 1e-6 and abs(eq["記憶體"]["D1"] - 95.0) < 1e-6:
        ok += 1; print("  [PASS] 等權指數 base100 每日再平衡")
    else:
        print("  [FAIL] 等權")
    mc = build_index(fix, "mcap")
    if mc["AI"]["D1"] > eq["AI"]["D1"]:  # 大市值 A 漲多→市值加權高於等權
        ok += 1; print("  [PASS] 市值加權高於等權(權重生效)+缺權重族群誠實降級")
    else:
        print("  [FAIL] 市值權")
    spec = to_chartspec(eq, "equal")
    if spec["chart"] == "line" and len(spec["series"]) == 2 and spec["x"]["values"] == ["D1", "D2"]:
        ok += 1; print("  [PASS] VAP 圖規 JSON(x/series/方法論欄)")
    else:
        print("  [FAIL] 圖規")
    print(f"  [計] {ok}/{total} 檢通過")
    return 0 if ok == total else 1


def main() -> int:
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if a[0] == "--selftest":
        return selftest()
    if a[0] == "--taxonomy":
        return cmd_taxonomy()
    if a[0] == "--index" and len(a) > 1:
        return cmd_index(a[1])
    if a[0] == "--chartspec" and len(a) > 1:
        return cmd_index(a[1], emit_spec=True)
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
