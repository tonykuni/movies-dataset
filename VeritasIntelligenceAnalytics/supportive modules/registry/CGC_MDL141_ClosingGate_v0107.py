#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL141_ClosingGate v0100 — 收尾閘(批398 操作員令「將 VRN VAL 收個尾吧」;via-closeout / via-vrnval / via-vapval)
====================================================================
收尾=「跑成功了嗎」的最後一道誠實閘:不另算、不另抓,只彙整母倉現役引擎的落檔與判準,逐份/逐圖給 DONE|FAIL|PENDING,
給總判 GREEN|YELLOW|RED|GREY,給下一步短令;落 JSON+Markdown 供接棒台/主控台讀。
  ① vrn  VRN 驗證收尾(VAL):報告夾(input_reports ∪ input/incoming)每一份 → 五段鏈 收件→首頁(ENG072 sidecar)→入庫(ENG073
         vrn_report_basic)→財報頁(ENG074 vrn_report_financial / ENG073 metrics)→四點(ENG080 vrn_four_point_digest);
         核對態沿用 MDL139 正本判準(basic_verified / classify_report / fin_final:TAB2 BASIC INFO VERIFIED|FAIL|PENDING,
         TAB4 FINANCIAL 報告值 vs VDF 歷史值 一致|不同→VDF 為主|無對照);逐份 DONE(五段全通且 VERIFIED)|FAIL|PENDING;
         總判:無報告=YELLOW(候操作員丟 PDF)· 有 FAIL=RED · 有未跑完=YELLOW · 全 DONE=GREEN · 庫缺/duckdb 缺=GREY。
  ② vap  VAP 產出收尾:規格冊(VIA_VAP_All_Chart_Specs)計數 + 產出夾(vap_one / vap_stack)逐圖驗:SVG 有 <svg> 與繪圖元素且無外鏈、
         PNG 簽章與 IHDR 尺寸、HTML 有圖且零 CDN、PDF 簽章;VAP ONE 台帳末筆;逐圖 OK|FAIL;總判:夾缺=GREY · 無圖=YELLOW ·
         有壞圖=RED · 全好=GREEN。
  ③ all  兩族併列,總判取最壞;CLOSEOUT_latest.json/.md(+VRN_/VAP_ 各自)落 VIA_Reports/closeout。
  --run   先跑鏈再收尾(Zero-Hydra:經 MDL139 run --item 逐段,同一啟動道;vrn=冊 chain_default 五段(--dir 報告夾);vap=vap_one_render);
          任一段 rc≠0 即停(誠實)。--dir 指定報告夾。--json 印 JSON。
          批400 工作站實錄修:vrn 報告夾(--dir > user.vrn_dir > 冊 dir_default;∪ incoming)無 .pdf/.docx=不跑鏈、一行誠實指路(零 NEED_DIR 噪音;收尾照跑);
          vap 無 config(user.vap.config 空/檔缺;判準=MDL139 resolve_argv vapone 種類 NEED_CONFIG,零重寫)=改跑 vap_one_demo(ENG016 --demo 產
          demo_config.json+示範圖入 user.vap.out)並印明取道;有 config=vap_one_render(零 NEED_CONFIG 噪音)。
紀律:只增不減;正本零觸碰(只讀庫/只讀夾);誠實三態;零 CDN(驗圖亦以此為律);零網路;尾版律(MDL139 尾版 glob);Zero-Hydra;ACCEL-BRIDGE。
沿革:批398 初版(vrn/vap/all 三動詞+--run);批399 自審(次步冊 off-by-one;報告夾律 _report_dirs);批400 工作站實錄(vap --run 無 config 誤跑 render →
      NEED_CONFIG、vrn --run 空夾 → NEED_DIR 噪音:run_chain 取道律 _vap_run_item/_report_files;八檢 ⑥ 擴)。
v0100→v0101(批403 操作員問「VRN 有無檔名/首頁/財報頁表格相互對照的引擎」):
  ENG074 v0102 補上第三邊(vrn_report_crosscheck:檔名 × 首頁 × 財報頁表格),
  收尾閘同步認得——逐份併列 對照 欄(AGREE/DIVERGE/ONLY_TABLE/單邊 計數 +
  ticker_on_fin_page、report_date_vs_periods 兩態);DIVERGE 屬「資訊級誠實旗標」
  (首頁 rx 與表格值不合=待人工核,非鏈路失敗)故不降 verdict,但總結行點名、
  次步指路 --crosscheck 重算;表未建=誠實 '未對照'(先跑 ENG074 v0102)。九檢。
用法:python3 CGC_MDL141_ClosingGate_v0100.py [vrn|vap|all] [--run] [--dir 夾] [--json] | --selftest
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import csv
import datetime as _dt
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = VIA / "VIA_Reports" / "closeout"
MEGA = VIA / "functional modules" / "VDF" / "output_hub" / "mega"
DB_TW = MEGA / "vdf_tw_market.duckdb"
LOG = VIA / "logs" / "closeout.log"
VERBS = ("vrn", "vap", "all")
STAGES = ("收件", "首頁", "入庫", "財報頁", "四點")
IMG_EXT = (".svg", ".png", ".html", ".pdf")
LAMP_ORDER = {"GREEN": 0, "GREY": 1, "YELLOW": 2, "RED": 3}


def _now() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _mtime(p: Path) -> str:
    try:
        return _dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    except OSError:
        return ""


def _age_days(p: Path) -> int | None:
    try:
        return int((_dt.datetime.now() - _dt.datetime.fromtimestamp(p.stat().st_mtime)).total_seconds() // 86400)
    except OSError:
        return None


def log_event(kind: str, msg: str, **kw) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": _now(), "kind": kind, "msg": msg, **kw}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _duckdb():
    try:
        import duckdb
        return duckdb
    except Exception:
        return None


def _newest(pat: str, d: Path) -> Path | None:
    hits = sorted(d.glob(pat)) if d.exists() else []
    return hits[-1] if hits else None


def console_mod():
    """MDL139 輸入主控台正本(尾版 glob;in-process):判準 basic_verified/classify_report/fin_final/vrn_tabs 與 run --item 同源(Zero-Hydra)"""
    p = _newest("CGC_MDL139_InputConsole_v*.py", HERE)
    if not p:
        raise RuntimeError("MDL139 輸入主控台缺(尾版 glob 無命中)")
    spec = importlib.util.spec_from_file_location("via_console_mod_for_closeout", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _worst(*lamps: str) -> str:
    return max([x for x in lamps if x in LAMP_ORDER] or ["GREY"], key=lambda x: LAMP_ORDER[x])


# ---------------------------------------------------------------- ① VRN 驗證收尾
def _stage_of(side: bool, basic: bool, n_met: int, n_fin: int, four: bool) -> int:
    st = 0
    if side:
        st = 1
    if basic:
        st = 2
        if n_met > 0 or n_fin > 0:
            st = 3
            if four:
                st = 4
    return st


def _report_exts(spec: dict) -> tuple:
    """冊 families.vrn.input.extensions(小寫;冊缺=.pdf/.docx;批400 抽出供 vrn_closeout 與 run_chain 同源)"""
    return tuple(str(x).lower() for x in spec["families"]["vrn"]["input"].get("extensions", [".pdf", ".docx"]))


# 批410:VRN_ENG072 v0105 以前自測留在正式產出夾的 fixture 檔名(非真報告)
SELFTEST_FIXTURE_STEMS = ("fx_report", "fx_scan", "fx_twocol")


def _report_files(dirs: list, exts: tuple) -> dict:
    """報告夾內報告檔(檔名→路徑;同名先見者為主;只計冊 extensions;夾缺=跳過;批400 抽出供 vrn_closeout 與 run_chain 空夾判定同源)"""
    files: dict = {}
    for d in dirs:
        if d.exists():
            for f in sorted(d.iterdir()):
                if f.is_file() and f.suffix.lower() in exts:
                    files.setdefault(f.name, f)
    return files


def vrn_closeout(spec: dict | None = None, db: Path | None = None, zones: Path | None = None, report_dirs: list | None = None,
                 reports_dir: Path = REPORTS, do_print: bool = True, mod=None) -> dict:
    mod = mod or console_mod()
    spec = spec or mod.load_spec()
    fam = spec["families"]["vrn"]
    zones = zones if zones is not None else VIA / fam["input"]["sidecars"]
    dirs = report_dirs if report_dirs is not None else _report_dirs(spec, None)
    # 批446:db 預設由 None 改成走替根探測。舊簽名寫死 `db: Path = DB_TW`,
    # 主路徑缺就一路判 GREY——而庫其實在家目錄那份 clone。
    db_why = ""
    if db is None:
        db, db_why = _mega_db()
        if db_why:
            print(f"[庫解析] {db_why}(誠實提示)")
    db = Path(db) if db is not None else DB_TW
    exts = _report_exts(spec)
    rep = {"schema": "VIA.Closeout.vrn.v1", "ts": _now(), "family": "vrn", "verdict": "GREY", "note": "", "db": str(db), "db_why": db_why, "dirs": [str(d) for d in dirs],
           "zones": str(zones), "rows": [], "summary": {}, "next": [], "fail": []}
    files = _report_files(dirs, exts)   # 批400:與 run_chain 空夾判定同源(語意不變)
    tabs = {"reports": [], "basic": [], "summary_matrix": [], "financial": []}
    fp_files: set = set()
    fp_tp: dict = {}                                 # 批438-B3:四點的 TP 合理性態
    cross_by: dict = {}                              # 批403:report_file → {state: n}
    kind_by: dict = {}                               # 批418:report_file → 報告型別
    duckdb = _duckdb()
    db_state = "OK"
    if duckdb is None:
        db_state, rep["note"] = "GREY", "duckdb 缺(於 via_vrn_312 境跑:via-closeout vrn)"
    elif not db.exists():
        db_state, rep["note"] = "GREY", (f"庫缺 {db}(主路徑與替根皆已探過"
                                         + (f";{db_why}" if db_why else "")
                                         + ");先 via-vdfdb run --apply / 日更鏈)")
    else:
        try:
            con = duckdb.connect(str(db), read_only=True)
        except Exception as exc:   # 讓庫律:單寫者鎖=誠實黃,不 traceback
            con = None
            db_state, rep["note"] = "YELLOW", f"庫忙/開啟失敗(日更鏈/回補持鎖?等其跑完再 via-closeout vrn;via-bg 看進程):{str(exc)[:80]}"
        if con is not None:
            try:
                have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
                tabs = mod.vrn_tabs(con, zones)
                if "vrn_four_point_digest" in have:
                    fp_files = {str(r[0]) for r in con.execute("SELECT DISTINCT report_file FROM vrn_four_point_digest").fetchall()}
                    # 批422→批438-B3(操作員 2026-09-12 明令「好」):
                    # 四點文摘自己有一道 TP 合理性閘(ENG080 的 tp_state,TP_SUSPECT=
                    # 目標價與現價比值荒謬),而 DONE_NS 的守衛**只讀 vrn_report_basic
                    # 的 upside_state,從來沒讀過它**。於是「四點說目標價有問題」這件事
                    # 抓到了、寫進庫了,收尾閘卻看不到——批422 記的那個假綠就是這個。
                    # 燈會變(DONE 少、FAIL 多),所以等操作員點頭才動。
                    try:
                        fp_tp = {str(a): str(b or "") for a, b in con.execute(
                            "SELECT report_file, COALESCE(tp_state,'') "
                            "FROM vrn_four_point_digest").fetchall()}
                    except Exception as _exc:
                        fp_tp, fp_tp_why = {}, (f"四點 tp_state 讀取失敗 "
                                                f"{type(_exc).__name__}(欄位未建?)")
                        rep.setdefault("notes", []).append(fp_tp_why)
                if "vrn_report_basic" in have:       # 批418:報告型別(ENG073 v0108 新欄)
                    try:
                        for _rf, _kd in con.execute(
                                "SELECT report_file, COALESCE(report_kind,'') FROM vrn_report_basic").fetchall():
                            kind_by[str(_rf)] = str(_kd)
                    except Exception:
                        pass                          # 舊庫沒有這欄=誠實空,照舊判(只增不減)
                if "vrn_report_crosscheck" in have:   # 批403:ENG074 v0102 第三邊
                    for _rf, _st, _n in con.execute(
                            "SELECT report_file, state, count(*) FROM vrn_report_crosscheck GROUP BY 1,2").fetchall():
                        cross_by.setdefault(str(_rf), {})[str(_st)] = int(_n)
            finally:
                con.close()
    by_file = {r["report_file"]: r for r in tabs["reports"]}
    by_stem = {Path(k).stem: v for k, v in by_file.items()}
    basic_state = {b["report_file"]: b["verified"] for b in tabs["basic"]}
    fin_by: dict = {}
    for f in tabs["financial"]:
        d = fin_by.setdefault(f["report_file"], {"n": 0, "consistent": 0, "vdf_over": 0, "no_ref": 0})
        d["n"] += 1
        rule = str(f.get("rule") or "")
        if rule.startswith("一致"):
            d["consistent"] += 1
        elif rule.startswith("不同"):
            d["vdf_over"] += 1
        else:
            d["no_ref"] += 1
    names = sorted(set(files) | set(by_file))
    seen_stems: set = set()
    fixture_leak: list = []      # 批410:自測 fixture 外流件(不是真報告,不進判定)
    for name in names:
        stem = Path(name).stem
        if stem in seen_stems:
            continue
        seen_stems.add(stem)
        if stem in SELFTEST_FIXTURE_STEMS:
            # 批410:VRN_ENG072 v0105 以前的自測會把 fx_report/fx_scan/fx_twocol
            # 寫進正式首頁產出夾,ENG073 隨後把它們當真報告收進正本庫。它們不是
            # 報告,卻會被算成 FAIL/PENDING,把「尚無報告」的誠實態變成假象。
            # 這裡認出來、單列說明、**不計入判定**;清理由操作員自己下(見下方指路)。
            fixture_leak.append(name)
            continue
        r = by_file.get(name) or by_stem.get(stem)
        rf = r["report_file"] if r else name
        side = (zones / f"{stem}.json").exists() or (zones / f"{name}.json").exists() if zones.exists() else False
        in_folder = name in files or any(Path(k).stem == stem for k in files)
        n_met = int(r["n_metrics"]) if r else 0
        n_fin = int(r["n_financial"]) if r else 0
        four = rf in fp_files or stem in {Path(x).stem for x in fp_files}
        stage = _stage_of(side, r is not None, n_met, n_fin, four)
        b_state = basic_state.get(rf, "PENDING") if r else "PENDING"
        f_state = r["financial"] if r else "PENDING"
        s_state = r["summary"] if r else "PENDING"
        if r and (b_state == "FAIL" or f_state == "FAIL"):
            verdict = "FAIL"
        elif r and stage == 4 and b_state == "VERIFIED" and f_state == "VERIFIED":
            verdict = "DONE"
        else:
            verdict = "PENDING"
        # 批418:操作員給的 63 份真報告裡有 19 份本來就不是個股報告(產業/大盤晨報/
        # 海外/研討會)。它們沒有代號、沒有目標價、沒有上漲空間可核——**這是對的**,
        # 不是缺陷。但 basic_verified 要 VDF 價表核對成立才給 VERIFIED,於是這 19 份
        # 會永遠停在 PENDING:一面永遠不會轉綠的黃牆,跟假紅一樣糟。
        # 所以:非個股型只要「首頁抽出來了、也進了庫」,對它適用的鏈就走完了=DONE_NS。
        # 收得很緊——真的失敗(basic/financial FAIL)照舊是 FAIL,不因為非個股就放過。
        kind = str(kind_by.get(rf) or kind_by.get(stem) or "")
        if kind and kind != "個股" and verdict in ("PENDING", "FAIL") and side and r is not None:
            # 為什麼 FAIL 也要收:MDL139 classify_report 在「零 metrics 且零 financial」時
            # 直接判 financial=FAIL。產業/晨報/研討會報告本來就沒有 EPS 與財報表,
            # 所以它們不是黃著,是**紅著**——19 份真報告會變成一整面假紅。
            # 但收得很緊:只要是**真的核對不符**(價表查無對照 DB_NO_MATCH,或上漲空間
            # 落在 FAIL 態),那是真失敗,非個股也照樣 FAIL,不因為型別就放過。
            # 批419d(工作站實錄修):v0103 這道守衛太寬,把 22 份非個股全擋回 FAIL。
            # MDL139 的 FAIL_STATES 含 MISSING_SOURCE,而「沒有目標價、沒有價」
            # **正是**產業/晨報/研討會報告的正常狀態——拿它當失敗,等於又走回假紅。
            # DB_NO_MATCH 同理:沒有代號就沒有價表可對。
            # 真正該留 FAIL 的只有「數字抽出來了而且對不起來」:公式不符與解析可疑。
            # (我 v0103 的 fixture upside_state 用空字串,所以檢過了、真跑沒過——
            #  fixture 不帶真實狀態,測的就不是真的那條路。)
            _REAL_BAD_STATES = ("FORMULA_MISMATCH", "FORMULA_MISMATCH_DB", "PARSE_SUSPECT")
            _us = str((r or {}).get("upside_state") or "")
            # 批438-B3:四點的 tp_state 也算數。TP_SUSPECT=目標價與現價比值荒謬,
            # 那是**數字抽出來了而且對不起來**——正好是 _REAL_BAD_STATES 的定義,
            # 只是它住在另一張表。同一個判準,兩個來源,不能只讀一個。
            _ts = str(fp_tp.get(rf) or fp_tp.get(stem) or "")
            if _us not in _REAL_BAD_STATES and _ts != "TP_SUSPECT":
                verdict = "DONE_NS"
        fb = fin_by.get(rf, {"n": 0, "consistent": 0, "vdf_over": 0, "no_ref": 0})
        cb = cross_by.get(rf) or cross_by.get(stem) or {}
        cross_state = ("未對照" if not cb else
                       f"DIVERGE {cb.get('DIVERGE', 0)}" if cb.get("DIVERGE") else
                       f"AGREE {cb.get('AGREE', 0)}" if cb.get("AGREE") else "單邊")
        row = {"report_file": name, "ticker": (r or {}).get("ticker", ""), "report_date": (r or {}).get("report_date", ""), "in_folder": in_folder, "sidecar": side,
               "basic_row": r is not None, "n_metrics": n_met, "n_financial": n_fin, "four_point": four, "stage": stage, "stage_zh": STAGES[stage],
               "basic": b_state, "summary": s_state, "financial": f_state, "fin_consistent": fb["consistent"], "fin_vdf_over": fb["vdf_over"], "fin_no_ref": fb["no_ref"],
               "upside_state": (r or {}).get("upside_state", ""), "price_state": (r or {}).get("price_state", ""),
               "fp_tp_state": str(fp_tp.get(rf) or fp_tp.get(stem) or ""),   # 批438-B3
               "cross_agree": cb.get("AGREE", 0), "cross_diverge": cb.get("DIVERGE", 0), "cross_rounding": cb.get("ROUNDING", 0),
               "cross_unit_scale": cb.get("UNIT_SCALE", 0), "cross_only_table": cb.get("ONLY_TABLE", 0),
               "cross_only_firstpage": cb.get("ONLY_FIRSTPAGE", 0), "cross_ticker": next((k for k in cb if k.startswith("TICKER_") or k == "NO_TICKER"), ""),
               "cross_date": next((k for k in cb if k.startswith("DATE_") or k.startswith("NO_")), ""), "cross_state": cross_state,
               "kind": kind or "—", "verdict": verdict}
        rep["rows"].append(row)
        if verdict == "FAIL":
            rep["fail"].append({"report_file": name, "basic": b_state, "financial": f_state, "upside_state": row["upside_state"], "price_state": row["price_state"]})
    n = len(rep["rows"])
    done = sum(1 for x in rep["rows"] if x["verdict"] == "DONE")
    done_ns = sum(1 for x in rep["rows"] if x["verdict"] == "DONE_NS")   # 批418:非個股完成
    fail = sum(1 for x in rep["rows"] if x["verdict"] == "FAIL")
    pend = n - done - done_ns - fail
    kind_hist: dict = {}
    for x in rep["rows"]:
        kind_hist[x.get("kind") or "—"] = kind_hist.get(x.get("kind") or "—", 0) + 1
    hist = {STAGES[i]: sum(1 for x in rep["rows"] if x["stage"] == i) for i in range(5)}
    rep["summary"] = {"files_in_folder": len(files), "reports": n, "done": done, "done_non_stock": done_ns, "fail": fail, "pending": pend, "kind_hist": kind_hist, "sidecars": sum(1 for x in rep["rows"] if x["sidecar"]),
                      "basic_rows": sum(1 for x in rep["rows"] if x["basic_row"]), "four_point": sum(1 for x in rep["rows"] if x["four_point"]), "stage_hist": hist,
                      "basic_verified": sum(1 for x in rep["rows"] if x["basic"] == "VERIFIED"), "financial_verified": sum(1 for x in rep["rows"] if x["financial"] == "VERIFIED"),
                      "fin_rows_consistent": sum(v["consistent"] for v in fin_by.values()), "fin_rows_vdf_over": sum(v["vdf_over"] for v in fin_by.values()),
                      "fin_rows_no_ref": sum(v["no_ref"] for v in fin_by.values()), "db_state": db_state,
                      "cross_reports": sum(1 for x in rep["rows"] if x["cross_state"] != "未對照"),          # 批403 三方對照
                      "cross_agree": sum(x["cross_agree"] for x in rep["rows"]), "cross_diverge": sum(x["cross_diverge"] for x in rep["rows"]),
                      "cross_only_table": sum(x["cross_only_table"] for x in rep["rows"]),
                      "cross_unit_scale": sum(x["cross_unit_scale"] for x in rep["rows"])}
    rep["fixture_leak"] = fixture_leak      # 批410:自測 fixture 外流件(不進判定,單列說明)
    nxt: list = []
    if db_state == "GREY":
        rep["verdict"] = "GREY"
        nxt.append(rep["note"])
    elif db_state == "YELLOW":
        rep["verdict"] = "YELLOW"
        nxt.append(rep["note"])
    elif n == 0:
        rep["verdict"], rep["note"] = "YELLOW", "尚無報告(報告夾與庫皆空)→ 拖 PDF/選夾進主控台即整條鏈;或 via-closeout vrn --run --dir <報告夾>"
        nxt.append("via-console --open(拖曳/選夾入件即跑)")
    else:
        low = min((x["stage"] for x in rep["rows"] if x["verdict"] == "PENDING"), default=4)
        if fail:
            rep["verdict"] = "RED"
            rep["note"] = (f"{fail}/{n} 份核對 FAIL(報告值 vs VDF 不符或無指標;見 fail 清單 upside_state/price_state)"
                           + (f";另 {pend} 份未跑完" if pend else "")
                           + (f";另 {done_ns} 份非個股已完成" if done_ns else ""))
            nxt.append("TAB2 核對態 FAIL=報告 upside 公式不符或價表無對照:財報數以 VDF 歷史值為主(fin_final),報告本身問題誠實留 FAIL;確認 tw_daily_prices 覆蓋報告日(via-price run)後 via-console run --item vrn_structdb 重核")
        elif pend:
            rep["verdict"] = "YELLOW"
            rep["note"] = (f"{pend}/{n} 份鏈未跑完(最低停在「{STAGES[low]}」)· DONE {done}"
                           + (f" · 非個股完成 {done_ns}" if done_ns else ""))
        else:
            rep["verdict"] = "GREEN"
            # 批418:非個股完成要講白是哪一類完成的,不能混進「全通且 VERIFIED」裡充數
            rep["note"] = (f"{done}/{n} 份 收件→首頁→入庫→財報頁→四點 全通且 BASIC INFO/FINANCIAL VERIFIED"
                           + (f";另 {done_ns} 份非個股(產業/大盤晨報/海外/研討會)"
                              "已走完對它適用的鏈——那類報告本來就沒有代號與目標價可核" if done_ns else ""))
        if pend:
            item = {0: "vrn_firstpage", 1: "vrn_structdb", 2: "vrn_finpages", 3: "vrn_fourpoint"}.get(low, "vrn_ui")   # 批399 自審:stage=已完成段 → 次步=下一段
            nxt.append(f"via-console run --item {item}(或 via-closeout vrn --run;冊 chain_default 五段自動接續)")
        # 批403:三方對照=資訊級旗標(待人工核),不降 verdict,只點名指路
        cs = rep["summary"]
        if cs["cross_reports"] == 0 and n:
            nxt.append("尚未三方對照(檔名×首頁×財報頁表格)→ VRN_ENG074_FinancialPages 尾版 --crosscheck(或重跑 vrn_finpages 內建同輪)")
        elif cs["cross_diverge"]:
            dv = sorted((x for x in rep["rows"] if x["cross_diverge"]), key=lambda z: -z["cross_diverge"])[:5]
            rep["cross_diverge_top"] = [{"report_file": x["report_file"], "n": x["cross_diverge"]} for x in dv]
            nxt.append("三方對照 DIVERGE " + str(cs["cross_diverge"]) + " 處(首頁 rx 值 vs 財報頁表格值不合;資訊級=待人工核,非鏈路失敗):"
                       + "、".join(f"{x['report_file'][:28]}×{x['cross_diverge']}" for x in dv))
    rep["next"] = nxt
    _write_family(rep, reports_dir, "VRN")
    if do_print:
        print(f"[via-closeout vrn] {rep['verdict']} · {rep['note']} · 報告 {n}(DONE {done} · FAIL {fail} · PENDING {pend})· 段:{hist}")
        _cs = rep["summary"]
        print(f"  [三方對照] 已對照 {_cs['cross_reports']}/{n} 份 · AGREE {_cs['cross_agree']} · DIVERGE {_cs['cross_diverge']}"
              f" · 單位差 {_cs['cross_unit_scale']} · 表格獨有 {_cs['cross_only_table']}(檔名×首頁×財報頁表格;DIVERGE=待人工核不判死)")
        for x in rep["rows"][:30]:
            print(f"  {x['verdict']:<7} {x['report_file'][:40]:<40} 段 {x['stage']}/{4}({x['stage_zh']}) BASIC {x['basic']:<8} FIN {x['financial']:<8} 夾{'✓' if x['in_folder'] else '-'} 頁{'✓' if x['sidecar'] else '-'} 庫{'✓' if x['basic_row'] else '-'} 四點{'✓' if x['four_point'] else '-'}")
        for nm in rep.get("fixture_leak", []):
            print(f"  FIXTURE {nm[:40]:<40} 自測 fixture 外流件=不是真報告,已排除於判定外(批410)")
        if rep.get("fixture_leak"):
            print("  → 清理(我不代刪):python \"functional modules/VRN/VRN_ENG072_FirstPageText_v0106.py\" "
                  "purge-selftest --apply;庫側該下的 SQL 同一支會印出來")
        if n > 30:
            print(f"  … 其餘 {n - 30} 份見 VRN_CLOSEOUT_latest.json")
        for s in nxt:
            print(f"  → {s}")
    return rep


# ---------------------------------------------------------------- ② VAP 產出收尾
def check_image(p: Path) -> dict:
    kind = p.suffix.lower().lstrip(".")
    row = {"file": str(p), "name": p.name, "kind": kind, "kb": 0, "mtime": _mtime(p), "age_days": _age_days(p), "valid": False, "why": "", "dims": ""}
    try:
        data = p.read_bytes()
    except OSError as exc:
        row["why"] = f"讀取失敗 {str(exc)[:40]}"
        return row
    row["kb"] = len(data) // 1024
    why = ""
    if len(data) == 0:
        why = "空檔"
    elif kind == "svg":
        txt = data[:400000].decode("utf-8", "ignore")
        if "<svg" not in txt:
            why = "非 SVG(無 <svg>)"
        elif not re.search(r"<(path|rect|circle|ellipse|polyline|polygon|line|text|image|use)\b", txt):
            why = "無繪圖元素(空圖)"
        elif re.search(r"""(href|src)\s*=\s*["']https?://""", txt):
            why = "含外部連結(零 CDN 律)"
        else:
            m = re.search(r'viewBox\s*=\s*["\']([^"\']+)', txt)
            row["dims"] = m.group(1) if m else ""
    elif kind == "png":
        if data[:8] != b"\x89PNG\r\n\x1a\n" or len(data) < 24:
            why = "非 PNG 簽章"
        else:
            w, h = int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
            row["dims"] = f"{w}x{h}"
            if w == 0 or h == 0:
                why = "尺寸 0"
    elif kind == "html":
        txt = data[:600000].decode("utf-8", "ignore")
        if re.search(r"""<script[^>]+src\s*=\s*["']https?://""", txt, re.I) or re.search(r"""<link[^>]+href\s*=\s*["']https?://""", txt, re.I):
            why = "含 CDN 外鏈(零 CDN 律)"
        elif "<svg" not in txt and "plotly" not in txt.lower() and "<canvas" not in txt.lower():
            why = "無圖(無 svg/plotly/canvas)"
    elif kind == "pdf":
        if not data.startswith(b"%PDF"):
            why = "非 PDF 簽章"
    row["valid"] = not why
    row["why"] = why or "OK"
    return row


def vap_closeout(spec: dict | None = None, image_dirs: list | None = None, specs_csv: Path | None = None, reports_dir: Path = REPORTS,
                 do_print: bool = True, mod=None, ledger: Path | None = None) -> dict:
    mod = mod or console_mod()
    spec = spec or mod.load_spec()
    fam = spec["families"]["vap"]
    dirs = image_dirs if image_dirs is not None else [VIA / d for d in fam.get("image_dirs", [])]
    csvp = specs_csv if specs_csv is not None else VIA / fam.get("specs_csv", "")
    rep = {"schema": "VIA.Closeout.vap.v1", "ts": _now(), "family": "vap", "verdict": "GREY", "note": "", "dirs": [str(d) for d in dirs], "specs_csv": str(csvp),
           "specs": [], "images": [], "ledger": {}, "summary": {}, "next": [], "fail": []}
    specs = []
    if csvp and Path(csvp).exists():
        try:
            with open(csvp, encoding="utf-8-sig", newline="") as f:
                specs = [{"code": r.get("code", ""), "id": r.get("id", ""), "zh": r.get("zh", ""), "renderer": r.get("renderer", "")} for r in csv.DictReader(f)]
        except Exception as exc:
            rep["note"] = f"規格冊讀取失敗 {str(exc)[:60]}"
    rep["specs"] = specs
    seen: set = set()
    files: list = []
    for d in dirs:
        if not d.exists():
            continue
        for f in sorted(d.rglob("*")):
            if f.is_file() and f.suffix.lower() in IMG_EXT and f.name != "vap_one_ledger.jsonl":
                rp = str(f.resolve())
                if rp not in seen:
                    seen.add(rp)
                    files.append(f)
    rows = [check_image(f) for f in files[:500]]
    rep["images"] = rows
    rep["fail"] = [{"name": r["name"], "kind": r["kind"], "why": r["why"], "file": r["file"]} for r in rows if not r["valid"]]
    led = ledger if ledger is not None else (VIA / "VIA_Reports" / "vap_one" / "vap_one_ledger.jsonl")
    if led.exists():
        try:
            lines = [json.loads(x) for x in led.read_text(encoding="utf-8").strip().splitlines() if x.strip()]
            last = next((x for x in reversed(lines) if x.get("action") == "RENDER"), lines[-1] if lines else {})
            rep["ledger"] = {"entries": len(lines), "last": last}
        except Exception as exc:
            rep["ledger"] = {"error": str(exc)[:60]}
    by_kind: dict = {}
    for r in rows:
        by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + 1
    newest = max((r["mtime"] for r in rows), default="")
    n_valid = sum(1 for r in rows if r["valid"])
    rep["summary"] = {"specs": len(specs), "dirs_exist": sum(1 for d in dirs if d.exists()), "images": len(rows), "valid": n_valid, "invalid": len(rows) - n_valid, "by_kind": by_kind,
                      "newest": newest, "ledger_last_status": (rep["ledger"].get("last") or {}).get("status", "") if isinstance(rep["ledger"].get("last"), dict) else ""}
    nxt: list = []
    if rep["summary"]["dirs_exist"] == 0:
        rep["verdict"], rep["note"] = "GREY", "產出夾皆缺(尚未跑 VAP)→ via-console run --item vap_one_render / via-vapone"
        nxt.append("via-console run --item vap_one_render(VAP ONE;via_vap_312)")
    elif not rows:
        rep["verdict"], rep["note"] = "YELLOW", "產出夾在但無圖 → via-console run --item vap_one_render / vap_stack"
        nxt.append("via-console run --item vap_one_render")
    elif rep["fail"]:
        rep["verdict"] = "RED"
        rep["note"] = f"{len(rep['fail'])}/{len(rows)} 圖不合格(" + "; ".join(f"{x['name']}:{x['why']}" for x in rep["fail"][:5]) + ("…" if len(rep["fail"]) > 5 else "") + ")"
        nxt.append("壞圖=重跑該產出(vap_one_render / vap_stack);含 CDN 外鏈=違零 CDN 律,改用母倉本地渲染道")
    else:
        rep["verdict"] = "GREEN"
        rep["note"] = f"{n_valid}/{len(rows)} 圖合格(規格冊 {len(specs)} 條;最新 {newest};台帳末筆 {rep['summary']['ledger_last_status'] or '無'})"
    if specs == []:
        nxt.append("規格冊缺或空(VIA_VAP_All_Chart_Specs)=只驗圖不驗規格覆蓋(誠實)")
    rep["next"] = nxt
    _write_family(rep, reports_dir, "VAP")
    if do_print:
        print(f"[via-closeout vap] {rep['verdict']} · {rep['note']} · 圖 {len(rows)}(合格 {n_valid})· 種類 {by_kind} · 規格 {len(specs)}")
        for r in rows[:20]:
            print(f"  {'OK  ' if r['valid'] else 'FAIL'} {r['name'][:44]:<44} {r['kind']:<4} {r['kb']:>6} KB {r['mtime']}  {r['dims']}  {'' if r['valid'] else r['why']}")
        if len(rows) > 20:
            print(f"  … 其餘 {len(rows) - 20} 圖見 VAP_CLOSEOUT_latest.json")
        for s in nxt:
            print(f"  → {s}")
    return rep


# ---------------------------------------------------------------- 落檔 / Markdown / --run / 總閘
def _write_family(rep: dict, reports_dir: Path, tag: str) -> None:
    try:
        reports_dir.mkdir(parents=True, exist_ok=True)
        (reports_dir / f"{tag}_CLOSEOUT_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        (reports_dir / f"{tag}_CLOSEOUT_latest.md").write_text(to_markdown({"ts": rep["ts"], "verdict": rep["verdict"], "families": {rep["family"]: rep}}), encoding="utf-8")
    except OSError:
        pass


def _md_table(rows: list, cols: list) -> list:
    if not rows:
        return ["(無)", ""]
    esc = lambda v: str("" if v is None else v).replace("|", "\\|").replace("\n", " ")  # noqa: E731
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join(esc(r.get(c, "")) for c in cols) + " |")
    out.append("")
    return out


def to_markdown(rep: dict) -> str:
    L = [f"# VIA 收尾閘(Closeout)· {rep.get('ts', '')} · 總判 {rep.get('verdict', '')}", ""]
    fams = rep.get("families") or {}
    if "vrn" in fams:
        v = fams["vrn"]
        L += [f"## VRN 驗證收尾 · {v['verdict']}", f"- {v['note']}", f"- 摘要:{json.dumps(v.get('summary', {}), ensure_ascii=False)}", ""]
        L += _md_table(v.get("rows", []), ["report_file", "ticker", "report_date", "stage_zh", "basic", "summary", "financial", "fin_consistent", "fin_vdf_over", "fin_no_ref", "verdict"])
        if v.get("fail"):
            L += ["### FAIL 清單", ""] + _md_table(v["fail"], ["report_file", "basic", "financial", "upside_state", "price_state"])
        L += ["### 次步", ""] + [f"- {x}" for x in v.get("next", [])] + [""]
    if "vap" in fams:
        v = fams["vap"]
        L += [f"## VAP 產出收尾 · {v['verdict']}", f"- {v['note']}", f"- 摘要:{json.dumps(v.get('summary', {}), ensure_ascii=False)}", ""]
        L += _md_table(v.get("images", [])[:200], ["name", "kind", "kb", "mtime", "dims", "valid", "why"])
        L += ["### 次步", ""] + [f"- {x}" for x in v.get("next", [])] + [""]
    L += ["---", "紀律:只增不減 · 正本零觸碰(只讀) · 誠實三態 · 零 CDN · 零網路 · 尾版律 · Zero-Hydra(判準沿用 MDL139 正本)"]
    return "\n".join(L) + "\n"


def _vap_run_item(mod, spec: dict) -> tuple:
    """批400 vap --run 取道律(工作站實錄:無 config 誤跑 vap_one_render → NEED_CONFIG 噪音)。Zero-Hydra:判準=MDL139 resolve_argv vapone 種類
    (check_files=False 只判參數不判引擎;config 空/相對/絕對解析零重寫):NEED_CONFIG(user.vap.config 空/檔缺)→ ('vap_one_demo', 取道說明);
    其餘(READY/BAD_PARAM/NEED_DATA)→ ('vap_one_render', '')(引擎缺/參數不合仍由 MDL139 run 誠實印 rc=2);MDL139 無 resolve_argv=維持原道(只增不減)"""
    fn = getattr(mod, "resolve_argv", None)
    if fn is None:
        return "vap_one_render", ""
    try:
        st = (fn(spec, "vap_one_render", {}, check_files=False) or {}).get("state", "")
    except Exception as exc:   # 判準例外=誠實印明並維持原道,不吞錯
        return "vap_one_render", f"vap 取道判準例外({str(exc)[:60]})→ 維持 vap_one_render"
    if st == "NEED_CONFIG":
        return "vap_one_demo", "vap 無 config → 以 --demo 產生 demo_config 與示範圖(vap_one_demo → user.vap.out);要用自訂 config:via-console set vap-config=<path>"
    return "vap_one_render", ""


def run_chain(mod, spec: dict, family: str, report_dir: str | None = None, do_print: bool = True) -> list:
    """--run:經 MDL139 run --item(同一啟動道;家族境 python 由 MDL139 解析);任一段 rc≠0 即停(誠實)
    批400:vrn 報告夾(_report_dirs 律)無 .pdf/.docx=不跑鏈、一行誠實指路、回 [](零 NEED_DIR 噪音;收尾照跑);vap=_vap_run_item 取道(無 config=vap_one_demo 並印明)"""
    if family == "vrn":
        dirs = _report_dirs(spec, report_dir)
        if not _report_files(dirs, _report_exts(spec)):
            if do_print:
                print(f"[via-closeout --run] 報告夾空/缺:{' ∪ '.join(str(d) for d in dirs)} → 放入 PDF 後重跑(或 via-console --open 拖曳/選夾入件)")
            return []
        items = list(spec["families"]["vrn"].get("chain_default", []))
    else:
        item, why = _vap_run_item(mod, spec)
        if why and do_print:
            print(f"[via-closeout --run] {why}")
        items = [item]
    idx = mod.items_index(spec)
    out = []
    for it in items:
        params = {}
        ent = idx.get(it) or {}
        if report_dir and "dir" in ((ent.get("item") or ent).get("params") or []):   # items_index 條目={family,group,item,fam_python}
            params["dir"] = report_dir
        rc = mod.run(spec, it, params)
        out.append({"item": it, "rc": rc})
        if rc != 0:
            if do_print:
                print(f"[via-closeout --run] {it} rc={rc} → 停(誠實;修後重跑)")
            break
    return out


def _report_dirs(spec: dict, given: str | None) -> list:
    """報告夾律——**改叫冊擁有者的正本**(批446)。

    原本這裡自己抄了一份,docstring 還寫「同 MDL139 dir 參數」——而那句是**假的**:
    本檔併 incoming,MDL139 的 `kind == "dir"` 不併,只認 dir_default。工作站 64 份
    報告全在 incoming,於是本檔看得見「夾✓ 64」,MDL139 回 NEED_DIR 讓鏈第一段就停。
    「同某某」寫在註解裡不會讓它真的相同;要相同就得是同一支函式。

    舊版 MDL139 掛上來時沒有這支 → 退回本地實作,零回歸(批419e:退後備要講得出來)。
    """
    m = console_mod()
    fn = getattr(m, "vrn_report_dirs", None) if m is not None else None
    if fn is not None:
        try:
            return list(fn(spec, given))
        except Exception as exc:
            print(f"[報告夾律] 正本呼叫失敗 {type(exc).__name__} → 退本地實作(誠實提示)")
    fam = spec["families"]["vrn"]
    raw = str(given or spec.get("user", {}).get("vrn_dir") or "").strip()
    out = []
    if raw:
        pth = Path(raw)
        out.append(pth if pth.is_absolute() else VIA / pth)
    else:
        out.append(VIA / fam["input"]["dir_default"])
    inc = VIA / fam["input"]["incoming"]
    if inc not in out:
        out.append(inc)
    return out


def _mega_db(explicit=None):
    """VDF 主庫路徑——**改叫冊擁有者的正本**,主路徑缺要探替根(批446)。

    工作站實錄:同一次跑,ENG073/ENG074 印「主路徑缺→改用替根庫」並寫進 59 列 basic、
    7,024 列財報值,而本檔印「庫缺 …(先 via-vdfdb run --apply / 日更鏈)」判 GREY。
    **庫就在那裡,是本檔沒去找。** 批443 那一課(「資料已經在庫裡,是我找不到那個庫」)
    第二次現身,這次在收尾閘。

    這也是為什麼它一直沒被自測抓到:**沙盒的主路徑有庫,工作站沒有**——
    「跑得到就算過」的檢在沙盒永遠綠。
    """
    m = console_mod()
    fn = getattr(m, "mega_db", None) if m is not None else None
    if fn is not None:
        try:
            return fn(explicit)
        except Exception as exc:
            print(f"[主庫路徑律] 正本呼叫失敗 {type(exc).__name__} → 退主路徑(誠實提示)")
    p0 = Path(explicit) if explicit is not None else DB_TW
    return (p0, "") if p0.exists() else (None, f"主路徑缺且無替根探測:{p0}")


def closeout(verb: str = "all", run: bool = False, report_dir: str | None = None, reports_dir: Path = REPORTS, do_print: bool = True, mod=None, **kw) -> dict:
    mod = mod or console_mod()
    spec = mod.load_spec()
    rep = {"schema": "VIA.Closeout.v1", "ts": _now(), "verb": verb, "verdict": "GREY", "families": {}, "run": {}}
    fams = ["vrn", "vap"] if verb == "all" else [verb]
    for f in fams:
        if run:
            rep["run"][f] = run_chain(mod, spec, f, report_dir, do_print)
        if f == "vrn":
            dirs = _report_dirs(spec, report_dir)
            rep["families"]["vrn"] = vrn_closeout(spec, report_dirs=dirs, reports_dir=reports_dir, do_print=do_print, mod=mod, **{k: v for k, v in kw.items() if k in ("db", "zones")})
        else:
            rep["families"]["vap"] = vap_closeout(spec, reports_dir=reports_dir, do_print=do_print, mod=mod, **{k: v for k, v in kw.items() if k in ("image_dirs", "specs_csv", "ledger")})
    rep["verdict"] = _worst(*[v["verdict"] for v in rep["families"].values()])
    try:
        reports_dir.mkdir(parents=True, exist_ok=True)
        (reports_dir / "CLOSEOUT_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        (reports_dir / "CLOSEOUT_latest.md").write_text(to_markdown(rep), encoding="utf-8")
    except OSError:
        pass
    log_event("CLOSEOUT", verb, verdict=rep["verdict"], families={k: v["verdict"] for k, v in rep["families"].items()})
    if do_print:
        print(f"[via-closeout] 總判 {rep['verdict']} · " + " · ".join(f"{k} {v['verdict']}" for k, v in rep["families"].items()) + f" · 存證 {reports_dir / 'CLOSEOUT_latest.md'}")
    return rep


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import contextlib
    import copy
    import io
    import tempfile
    fails = []

    done = []

    def chk(name, cond, note=""):
        # 批438 自審:檢數原本手寫(「十三檢 OK 12」),加一檢忘了改就自打嘴巴。
        # 同一個病這一批在首頁全能引擎也修了一次——會被忘記的數字就不該用手寫。
        done.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    mod = console_mod()
    spec = mod.load_spec()
    chk("① 冊/正本綁定(MDL139 尾版 in-process;vrn chain_default 五段;vap image_dirs/specs_csv 在冊;判準函式 basic_verified/classify_report/fin_final/vrn_tabs 皆正本)",
        len(spec["families"]["vrn"]["chain_default"]) == 5 and spec["families"]["vap"].get("image_dirs") and spec["families"]["vap"].get("specs_csv")
        and all(hasattr(mod, f) for f in ("basic_verified", "classify_report", "fin_final", "vrn_tabs", "run", "items_index", "load_spec")), f"({spec['families']['vrn']['chain_default']})")
    duckdb = _duckdb()
    if duckdb is None:
        print("  [FAIL] duckdb 缺=本閘不可測(於 via_vrn_312 境跑)")
        return 1
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        db = root / "t.duckdb"
        c = duckdb.connect(str(db))
        c.execute("CREATE TABLE vrn_report_basic(report_file VARCHAR, ticker VARCHAR, name_official VARCHAR, broker VARCHAR, report_date VARCHAR, rating_raw VARCHAR, target_price DOUBLE, price DOUBLE, upside_report DOUBLE, upside_calc DOUBLE, upside_state VARCHAR, title_head VARCHAR, summary_head VARCHAR, conflicts VARCHAR, extracted_at VARCHAR, price_db DOUBLE, upside_db DOUBLE, price_state VARCHAR)")
        c.execute("INSERT INTO vrn_report_basic VALUES ('r1.pdf','2330','台積電','A','2026-09-01','BUY',1200,1000,20,20,'EXACT_MATCH_DB','標','摘要','','t',990,21.2,'P_CONFIRMED_DB'), ('r2.pdf','2454','聯發科','B','2026-08-01','HOLD',1500,1400,7,7,'FORMULA_MISMATCH','標2','','','t',NULL,NULL,'DB_NO_MATCH')")
        c.execute("CREATE TABLE vrn_report_metrics(report_file VARCHAR, metric VARCHAR, period VARCHAR, status VARCHAR, value DOUBLE, raw_text VARCHAR)")
        c.execute("INSERT INTO vrn_report_metrics VALUES ('r1.pdf','eps','2026','ESTIMATE',60.5,'EPS 60.5')")
        c.execute("CREATE TABLE vrn_report_financial(report_file VARCHAR, page INTEGER, canonical VARCHAR, raw_label VARCHAR, period VARCHAR, status VARCHAR, value DOUBLE, raw_text VARCHAR)")
        c.execute("INSERT INTO vrn_report_financial VALUES ('r1.pdf',3,'revenue','營收','2026-07','REPORT_STATED',2500,'…'), ('r1.pdf',3,'gross_margin','毛利率','2026-07','REPORT_STATED',55,'…')")
        c.execute("CREATE TABLE tw_monthly_revenue(code VARCHAR, ym VARCHAR, revenue DOUBLE, source VARCHAR, fetched_at VARCHAR)")
        c.execute("INSERT INTO tw_monthly_revenue VALUES ('2330','2026-07',2600,'MOPS','')")
        c.execute("CREATE TABLE vrn_four_point_digest(report_file VARCHAR, headline VARCHAR, k1 VARCHAR, k2 VARCHAR, k3 VARCHAR, k4 VARCHAR, k5 VARCHAR, qc VARCHAR, upside_now DOUBLE)")
        c.execute("INSERT INTO vrn_four_point_digest VALUES ('r1.pdf','標題','k1','k2','k3','k4','','OK',20.0)")
        c.close()
        zones = root / "zones"; zones.mkdir()
        (zones / "r1.json").write_text("{}", encoding="utf-8"); (zones / "r2.json").write_text("{}", encoding="utf-8")
        rdir = root / "reports"; rdir.mkdir()
        for n in ("r1.pdf", "r2.pdf", "r3.pdf"):
            (rdir / n).write_bytes(b"%PDF-1.4 fixture")
        (rdir / "notes.txt").write_text("x", encoding="utf-8")
        out = root / "closeout"
        v = vrn_closeout(spec, db=db, zones=zones, report_dirs=[rdir], reports_dir=out, do_print=False, mod=mod)
        by = {r["report_file"]: r for r in v["rows"]}
        chk("② VRN 逐份五段鏈+核對態(r1 收件→首頁→入庫→財報頁→四點 全通 BASIC/FIN VERIFIED=DONE;r2 入庫後 FORMULA_MISMATCH/DB_NO_MATCH=FAIL;r3 只收件=PENDING 段 0;非 pdf/docx 不計;總判 RED;fail 清單;次步指 vrn_firstpage)",
            v["verdict"] == "RED" and by["r1.pdf"]["verdict"] == "DONE" and by["r1.pdf"]["stage"] == 4 and by["r1.pdf"]["basic"] == "VERIFIED" and by["r1.pdf"]["financial"] == "VERIFIED"
            and by["r1.pdf"]["fin_vdf_over"] >= 1 and by["r2.pdf"]["verdict"] == "FAIL" and by["r2.pdf"]["stage"] == 2 and by["r3.pdf"]["verdict"] == "PENDING" and by["r3.pdf"]["stage"] == 0
            and "notes.txt" not in by and v["summary"]["files_in_folder"] == 3 and v["summary"]["done"] == 1 and v["summary"]["fail"] == 1 and v["summary"]["pending"] == 1
            and len(v["fail"]) == 1 and any("vrn_firstpage" in s for s in v["next"]) and (out / "VRN_CLOSEOUT_latest.json").exists() and (out / "VRN_CLOSEOUT_latest.md").exists(),
            f"({v['verdict']};{[(r['report_file'], r['stage'], r['verdict']) for r in v['rows']]})")
        db0 = root / "empty.duckdb"; duckdb.connect(str(db0)).close()
        e0 = root / "empty"; e0.mkdir()
        v0 = vrn_closeout(spec, db=db0, zones=zones, report_dirs=[e0], reports_dir=out, do_print=False, mod=mod)
        vg = vrn_closeout(spec, db=root / "no.duckdb", zones=zones, report_dirs=[e0], reports_dir=out, do_print=False, mod=mod)
        db1 = root / "one.duckdb"
        c1 = duckdb.connect(str(db1))
        c1.execute("CREATE TABLE vrn_report_basic AS SELECT * FROM (SELECT 'r1.pdf' report_file, '2330' ticker, '台積電' name_official, 'A' broker, '2026-09-01' report_date, 'BUY' rating_raw, 1200.0 target_price, 1000.0 price, 20.0 upside_report, 20.0 upside_calc, 'EXACT_MATCH_DB' upside_state, '標' title_head, '摘要' summary_head, '' conflicts, 't' extracted_at, 990.0 price_db, 21.2 upside_db, 'P_CONFIRMED_DB' price_state)")
        c1.execute("CREATE TABLE vrn_report_metrics(report_file VARCHAR, metric VARCHAR, period VARCHAR, status VARCHAR, value DOUBLE, raw_text VARCHAR)")
        c1.execute("INSERT INTO vrn_report_metrics VALUES ('r1.pdf','eps','2026','ESTIMATE',60.5,'x')")
        c1.execute("CREATE TABLE vrn_four_point_digest(report_file VARCHAR, headline VARCHAR, k1 VARCHAR, k2 VARCHAR, k3 VARCHAR, k4 VARCHAR, k5 VARCHAR, qc VARCHAR, upside_now DOUBLE)")
        c1.execute("INSERT INTO vrn_four_point_digest VALUES ('r1.pdf','標題','k1','k2','k3','k4','','OK',20.0)")
        c1.close()
        r1dir = root / "one"; r1dir.mkdir(); (r1dir / "r1.pdf").write_bytes(b"%PDF")
        v1 = vrn_closeout(spec, db=db1, zones=zones, report_dirs=[r1dir], reports_dir=out, do_print=False, mod=mod)
        chk("③ VRN 三態誠實(無報告=YELLOW 候操作員;庫缺=GREY;全 DONE=GREEN)",
            v0["verdict"] == "YELLOW" and "尚無報告" in v0["note"] and vg["verdict"] == "GREY" and v1["verdict"] == "GREEN" and v1["summary"]["done"] == 1,
            f"({v0['verdict']};{vg['verdict']};{v1['verdict']})")
        img = root / "vap_one"; (img / "RUN_1").mkdir(parents=True)
        (img / "RUN_1" / "good.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><path d="M0 0L1 1"/></svg>', encoding="utf-8")
        (img / "RUN_1" / "empty.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>', encoding="utf-8")
        (img / "RUN_1" / "ok.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\x0dIHDR" + (640).to_bytes(4, "big") + (480).to_bytes(4, "big") + b"\x08\x06\x00\x00\x00")
        (img / "RUN_1" / "cdn.html").write_text('<html><script src="https://cdn.plot.ly/plotly.js"></script><svg></svg></html>', encoding="utf-8")
        (img / "RUN_1" / "page.html").write_text("<html><body><svg><rect/></svg></body></html>", encoding="utf-8")
        (img / "RUN_1" / "doc.pdf").write_bytes(b"%PDF-1.4")
        (img / "vap_one_ledger.jsonl").write_text(json.dumps({"ts": "t", "action": "RENDER", "status": "OK", "run_dir": "RUN_1"}) + "\n", encoding="utf-8")
        csvp = root / "specs.csv"
        csvp.write_text("code,id,group,zh,en,renderer\nVAP-CH-01,line,單軸,折線圖,Line,go.Scatter\nVAP-CH-02,area,單軸,面積,Area,go.Scatter\n", encoding="utf-8-sig")
        a = vap_closeout(spec, image_dirs=[img], specs_csv=csvp, reports_dir=out, do_print=False, mod=mod, ledger=img / "vap_one_ledger.jsonl")
        byi = {r["name"]: r for r in a["images"]}
        good = root / "good"; good.mkdir(); (good / "g.svg").write_text('<svg><rect width="1" height="1"/></svg>', encoding="utf-8")
        ag = vap_closeout(spec, image_dirs=[good], specs_csv=csvp, reports_dir=out, do_print=False, mod=mod, ledger=root / "none.jsonl")
        am = vap_closeout(spec, image_dirs=[root / "nodir"], specs_csv=csvp, reports_dir=out, do_print=False, mod=mod, ledger=root / "none.jsonl")
        emp = root / "emp"; emp.mkdir()
        ae = vap_closeout(spec, image_dirs=[emp], specs_csv=root / "nocsv.csv", reports_dir=out, do_print=False, mod=mod, ledger=root / "none.jsonl")
        chk("④ VAP 逐圖驗(SVG 繪圖元素/空圖 FAIL;PNG 簽章+IHDR 640x480;HTML 含 CDN=FAIL、本地 svg OK;PDF 簽章;台帳末筆 RENDER OK;規格 2)+三態(壞圖=RED;全好=GREEN;夾缺=GREY;無圖=YELLOW;規格冊缺誠實註)",
            a["verdict"] == "RED" and byi["good.svg"]["valid"] and not byi["empty.svg"]["valid"] and byi["ok.png"]["valid"] and byi["ok.png"]["dims"] == "640x480"
            and not byi["cdn.html"]["valid"] and "CDN" in byi["cdn.html"]["why"] and byi["page.html"]["valid"] and byi["doc.pdf"]["valid"] and a["summary"]["invalid"] == 2
            and a["summary"]["ledger_last_status"] == "OK" and a["summary"]["specs"] == 2 and ag["verdict"] == "GREEN" and am["verdict"] == "GREY" and ae["verdict"] == "YELLOW"
            and any("規格冊" in s for s in ae["next"]) and (out / "VAP_CLOSEOUT_latest.md").exists(),
            f"({a['verdict']} 壞 {a['summary']['invalid']};{ag['verdict']}/{am['verdict']}/{ae['verdict']})")
        md = to_markdown({"ts": "t", "verdict": "RED", "families": {"vrn": v, "vap": a}})
        chk("⑤ Markdown 匯出(總判/## VRN/## VAP/表頭分隔線/FAIL 清單/次步;'|' 逃逸)",
            md.startswith("# VIA 收尾閘") and "## VRN 驗證收尾 · RED" in md and "## VAP 產出收尾 · RED" in md and "|---|" in md and "### FAIL 清單" in md and "### 次步" in md
            and "\\|" in to_markdown({"ts": "t", "verdict": "GREEN", "families": {"vap": {"verdict": "GREEN", "note": "", "summary": {}, "images": [{"name": "a|b", "kind": "svg", "kb": 1, "mtime": "", "dims": "", "valid": True, "why": "OK"}], "next": []}}}))
        calls = []

        class FakeMod:
            def load_spec(self):
                return spec

            def items_index(self, s):
                return mod.items_index(s)

            def resolve_argv(self, s, item, params=None, environ=None, check_files=True):   # 批400:vap 取道判準沿用正本(NEED_CONFIG|READY)
                return mod.resolve_argv(s, item, params, environ, check_files)

            def vrn_tabs(self, con, z):
                return mod.vrn_tabs(con, z)

            def run(self, s, item, params):
                calls.append((item, dict(params)))
                return 0 if item != "vrn_finpages" else 3
        fm = FakeMod()
        rr = run_chain(fm, spec, "vrn", report_dir=str(rdir), do_print=False)
        sp0 = copy.deepcopy(spec); sp0["user"]["vap"]["config"] = ""; sp0["families"]["vrn"]["input"]["incoming"] = str(e0)   # 批400:無 config;incoming 指空夾(工作站 incoming 有無 PDF 不影響自測)
        cfgp = root / "demo_config.json"; cfgp.write_text("{}", encoding="utf-8")
        sp1 = copy.deepcopy(sp0); sp1["user"]["vap"]["config"] = str(cfgp)   # 平台無關:當前 OS 的絕對路徑
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rv0 = run_chain(fm, sp0, "vap", do_print=True)                       # 無 config → vap_one_demo 並印明取道
            rv1 = run_chain(fm, sp1, "vap", do_print=True)                       # 有 config → vap_one_render(不印取道)
            re0 = run_chain(fm, sp0, "vrn", report_dir=str(e0), do_print=True)   # 空夾 → [] 一行「報告夾空」不跑鏈
        cap = buf.getvalue()
        d_abs = _report_dirs(spec, str(rdir)); d_rel = _report_dirs(spec, "functional modules/VRN/x"); d_dft = _report_dirs({"families": spec["families"], "user": {}}, None)
        d_usr = _report_dirs({"families": spec["families"], "user": {"vrn_dir": str(root / "usr")}}, None)   # 平台無關:當前 OS 的絕對路徑
        chk("⑥ --run 經 MDL139 run --item 同一啟動道(vrn 冊 chain_default 依序;--dir 只給有 dir 參數的段;rc≠0 即停=誠實;vap 有 config=vap_one_render)+ 批400 取道律(vap 無 config=vap_one_demo 並印明;vrn 報告夾空=[] 一行「報告夾空」不跑鏈、零 NEED_DIR)+ 報告夾律(絕對/母倉相對/user.vrn_dir/冊預設;incoming 併入)",
            [x["item"] for x in rr] == ["vrn_firstpage", "vrn_structdb", "vrn_finpages"] and rr[-1]["rc"] == 3 and calls[0][1].get("dir") == str(rdir) and calls[1][1] == {}
            and [x["item"] for x in rv0] == ["vap_one_demo"] and "--demo" in cap and "vap-config" in cap and [x["item"] for x in rv1] == ["vap_one_render"] and rv1[0]["rc"] == 0
            and re0 == [] and "報告夾空" in cap and "NEED_DIR" not in cap and all(c[1].get("dir") != str(e0) for c in calls)
            and d_abs[0] == rdir and d_rel[0] == VIA / "functional modules/VRN/x" and d_dft[0] == VIA / spec["families"]["vrn"]["input"]["dir_default"]
            and d_usr[0] == root / "usr" and all(d[-1] == VIA / spec["families"]["vrn"]["input"]["incoming"] for d in (d_abs, d_rel, d_dft, d_usr)),
            f"({[x['item'] for x in rr]};vap {[x['item'] for x in rv0]}/{[x['item'] for x in rv1]};vrn 空夾 {re0};{[str(d[0]) for d in (d_abs, d_rel, d_dft)]})")
        allrep = closeout("all", reports_dir=out, do_print=False, mod=fm, db=db, zones=zones, image_dirs=[img], specs_csv=csvp, ledger=img / "vap_one_ledger.jsonl")
        chk("⑦ 總閘 all(兩族併列;總判取最壞 RED;CLOSEOUT_latest.json/.md 落檔;log)",
            set(allrep["families"]) == {"vrn", "vap"} and allrep["verdict"] == "RED" and (out / "CLOSEOUT_latest.json").exists() and (out / "CLOSEOUT_latest.md").exists(),
            f"({allrep['verdict']})")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 紀律宣告(只增不減/正本零觸碰/誠實三態/零 CDN/零網路/尾版律/Zero-Hydra/ACCEL-BRIDGE)",
        all(k in src for k in ("只增不減", "正本零觸碰", "誠實三態", "零 CDN", "零網路", "尾版律", "Zero-Hydra", "ACCEL-BRIDGE")))
    # --- 批403 ⑨:三方對照認得(ENG074 v0102 vrn_report_crosscheck)-----
    with tempfile.TemporaryDirectory() as td9:
        r9 = Path(td9)
        z9 = r9 / "zones"; z9.mkdir(); (z9 / "r1.json").write_text("{}", encoding="utf-8")
        d9 = r9 / "rep"; d9.mkdir(); (d9 / "r1.pdf").write_bytes(b"%PDF-1.4 fx")
        db9 = r9 / "c.duckdb"
        c9 = duckdb.connect(str(db9))
        c9.execute("CREATE TABLE vrn_report_basic AS SELECT * FROM (SELECT 'r1.pdf' report_file, '2330' ticker, '台積電' name_official, 'A' broker, "
                   "'2026-09-01' report_date, 'BUY' rating_raw, 1200.0 target_price, 1000.0 price, 20.0 upside_report, 20.0 upside_calc, "
                   "'EXACT_MATCH' upside_state, '標' title_head, '摘' summary_head, '' conflicts, 't' extracted_at)")
        c9.execute("CREATE TABLE vrn_report_metrics(report_file VARCHAR, metric VARCHAR, period VARCHAR, status VARCHAR, value DOUBLE, raw_text VARCHAR)")
        c9.execute("CREATE TABLE vrn_report_crosscheck(report_file VARCHAR, ticker VARCHAR, dimension VARCHAR, period VARCHAR, "
                   "first_page_value DOUBLE, table_value DOUBLE, ratio DOUBLE, state VARCHAR, note VARCHAR, checked_at VARCHAR)")
        c9.execute("INSERT INTO vrn_report_crosscheck VALUES "
                   "('r1.pdf','2330','eps','2026',60.5,60.5,1.0,'AGREE','',''),"
                   "('r1.pdf','2330','eps','2027',70.0,7.0,0.1,'DIVERGE','',''),"
                   "('r1.pdf','2330','revenue','2026',NULL,3000.0,NULL,'ONLY_TABLE','',''),"
                   "('r1.pdf','2330','ticker_on_fin_page','',NULL,NULL,NULL,'TICKER_ON_FIN_PAGE','',''),"
                   "('r1.pdf','2330','report_date_vs_periods','2026-09-01',2026.0,2025.0,NULL,'DATE_CONSISTENT','','')")
        c9.close()
        v9 = vrn_closeout(spec, db=db9, zones=z9, report_dirs=[d9], reports_dir=r9 / "out", do_print=False, mod=mod)
        w9 = v9["rows"][0]
        c9b = duckdb.connect(str(db9))          # 對照組:同一 fixture 拿掉對照表
        c9b.execute("DROP TABLE vrn_report_crosscheck")
        c9b.close()
        v9n = vrn_closeout(spec, db=db9, zones=z9, report_dirs=[d9], reports_dir=r9 / "out2", do_print=False, mod=mod)
        chk("⑨ 三方對照認得(檔名×首頁×財報頁表格:逐份 AGREE/DIVERGE/ONLY_TABLE+ticker/date 態;總結統計;DIVERGE=資訊級不降 verdict(有無對照表 verdict 相同);次步點名;無對照=指路 --crosscheck)",
            w9["cross_agree"] == 1 and w9["cross_diverge"] == 1 and w9["cross_only_table"] == 1
            and w9["cross_ticker"] == "TICKER_ON_FIN_PAGE" and w9["cross_date"] == "DATE_CONSISTENT"
            and w9["cross_state"].startswith("DIVERGE") and v9["summary"]["cross_reports"] == 1
            and v9["summary"]["cross_diverge"] == 1
            and v9["verdict"] == v9n["verdict"]          # DIVERGE 不改判定=資訊級
            and any("DIVERGE" in x for x in v9["next"]) and v9.get("cross_diverge_top")
            and v9n["summary"]["cross_reports"] == 0
            and v9n["rows"][0]["cross_state"] == "未對照"
            and any("--crosscheck" in x for x in v9n["next"]),
            f"(有對照 {v9['verdict']}=無對照 {v9n['verdict']};{w9['cross_state']})")
    # --- 批410 ⑩:自測 fixture 外流件不得算成真報告(不進判定、單列說明、指路清理)---
    with tempfile.TemporaryDirectory() as td10:
        r10 = Path(td10)
        z10 = r10 / "zones"; z10.mkdir()
        d10 = r10 / "rep"; d10.mkdir()
        db10 = r10 / "c.duckdb"
        c10 = duckdb.connect(str(db10))
        c10.execute("CREATE TABLE vrn_report_basic AS SELECT * FROM (SELECT 'r1.pdf' report_file, '2330' ticker, '台積電' name_official, 'A' broker, "
                    "'2026-09-01' report_date, 'BUY' rating_raw, 1200.0 target_price, 1000.0 price, 20.0 upside_report, 20.0 upside_calc, "
                    "'EXACT_MATCH' upside_state, '標' title_head, '摘' summary_head, '' conflicts, 't' extracted_at)")
        c10.execute("CREATE TABLE vrn_report_metrics(report_file VARCHAR, metric VARCHAR, period VARCHAR, status VARCHAR, value DOUBLE, raw_text VARCHAR)")
        c10.close()          # DuckDB 單寫者:讀之前要先放手(否則乾淨組讀到空,判準會假紅)
        v10_clean = vrn_closeout(spec, db=db10, zones=z10, report_dirs=[d10], reports_dir=r10 / "o1", do_print=False, mod=mod)
        c10b = duckdb.connect(str(db10))
        c10b.execute("INSERT INTO vrn_report_basic SELECT 'fx_report.pdf','','','','','',NULL,NULL,NULL,NULL,'','','','','t'")
        c10b.execute("INSERT INTO vrn_report_basic SELECT 'fx_twocol.pdf','','','','','',NULL,NULL,NULL,NULL,'','','','','t'")
        c10b.close()
        v10_leak = vrn_closeout(spec, db=db10, zones=z10, report_dirs=[d10], reports_dir=r10 / "o2", do_print=False, mod=mod)
        chk("⑩ 自測 fixture 外流件不算真報告(批410:fx_report/fx_scan/fx_twocol 不進 rows 與判定;"
            "單列 fixture_leak 說明並指路清理;有無外流件 verdict 與報告數皆相同)",
            sorted(x["report_file"] for x in v10_leak["rows"]) == sorted(x["report_file"] for x in v10_clean["rows"])
            and v10_leak["summary"]["reports"] == v10_clean["summary"]["reports"]
            and v10_leak["verdict"] == v10_clean["verdict"]
            and sorted(Path(x).stem for x in v10_leak.get("fixture_leak", [])) == ["fx_report", "fx_twocol"]
            and v10_clean.get("fixture_leak") == [],
            f"(乾淨 {v10_clean['summary']['reports']} 份/{v10_clean['verdict']} · 有外流 {v10_leak['summary']['reports']} 份/{v10_leak['verdict']} · 外流 {len(v10_leak.get('fixture_leak', []))})")

    # --- 批418 ⑪:非個股報告不得永遠停在 PENDING(對照組:同一份檔案有無 report_kind)---
    with tempfile.TemporaryDirectory() as td11:
        r11 = Path(td11)
        z11 = r11 / "zones"; z11.mkdir()
        d11 = r11 / "rep"; d11.mkdir()
        # 檔名取自操作員給的 63 份真報告:一份個股、一份產業(沒有代號是對的)
        for stem in ("MS-3665 20251202", "MS-Thermal Solutions 20251007", "Daiwa-PCB 20251204"):
            (d11 / f"{stem}.pdf").write_text("x", encoding="utf-8")
            (z11 / f"{stem}.json").write_text("{}", encoding="utf-8")
        db11 = r11 / "k.duckdb"
        c11 = duckdb.connect(str(db11))
        c11.execute("CREATE TABLE vrn_report_basic(report_file VARCHAR, ticker VARCHAR, name_official VARCHAR, broker VARCHAR, "
                    "report_date VARCHAR, rating_raw VARCHAR, target_price DOUBLE, price DOUBLE, upside_report DOUBLE, "
                    "upside_calc DOUBLE, upside_state VARCHAR, title_head VARCHAR, summary_head VARCHAR, conflicts VARCHAR, extracted_at VARCHAR)")
        c11.execute("INSERT INTO vrn_report_basic VALUES ('MS-3665 20251202.pdf','3665','貿聯-KY','MS','2025-12-02','BUY',NULL,NULL,NULL,NULL,'','','','','t')")
        # 批419d:非個股的真實狀態就是 MISSING_SOURCE(沒代號→沒目標價→沒價),
        # 不是空字串。v0103 的 fixture 用空字串,於是檢過了而真跑沒過。
        c11.execute("INSERT INTO vrn_report_basic VALUES ('MS-Thermal Solutions 20251007.pdf','','','MS','2025-10-07','',NULL,NULL,NULL,NULL,'MISSING_SOURCE','','','','t')")
        # 另加一份非個股但**數字真的對不起來**的,證明守衛沒被拆掉
        c11.execute("INSERT INTO vrn_report_basic VALUES ('Daiwa-PCB 20251204.pdf','','','Daiwa','2025-12-04','',NULL,NULL,NULL,NULL,'FORMULA_MISMATCH','','','','t')")
        c11.execute("CREATE TABLE vrn_report_metrics(report_file VARCHAR, metric VARCHAR, period VARCHAR, status VARCHAR, value DOUBLE, raw_text VARCHAR)")
        c11.close()
        v11_old = vrn_closeout(spec, db=db11, zones=z11, report_dirs=[d11], reports_dir=r11 / "o1", do_print=False, mod=mod)
        c11b = duckdb.connect(str(db11))          # 加上 ENG073 v0108 的型別欄
        c11b.execute("ALTER TABLE vrn_report_basic ADD COLUMN report_kind VARCHAR")
        c11b.execute("UPDATE vrn_report_basic SET report_kind='個股' WHERE ticker<>''")
        c11b.execute("UPDATE vrn_report_basic SET report_kind='產業' WHERE ticker=''")
        c11b.execute("UPDATE vrn_report_basic SET report_kind='大盤晨報' WHERE report_file LIKE 'Daiwa-PCB%'")
        c11b.close()
        v11 = vrn_closeout(spec, db=db11, zones=z11, report_dirs=[d11], reports_dir=r11 / "o2", do_print=False, mod=mod)
        ns = [x for x in v11["rows"] if x["kind"] == "產業"]
        st = [x for x in v11["rows"] if x["kind"] == "個股"]
        nsbad = [x for x in v11["rows"] if x["kind"] == "大盤晨報"]
        chk("⑪ 非個股報告不得被判成假紅(批418:操作員 63 份真報告裡 19 份是產業/大盤晨報/"
            "海外/研討會——沒有代號、沒有目標價、沒有 EPS 是對的,而 MISSING_SOURCE 正是它們的正常態;"
            "MDL139 classify_report "
            "在『零 metrics 且零 financial』時直接判 financial=FAIL,於是這 19 份會變成一整面**假紅**)。"
            "無型別欄=行為逐字不變(只增不減);有型別欄=非個股只要首頁抽出且入庫即 DONE_NS,"
            "個股照舊要核對、不受影響",
            all(x["verdict"] == "FAIL" for x in v11_old["rows"])             # 舊庫無欄=行為不變(且證明假紅真的存在)
            and v11_old["summary"].get("done_non_stock", 0) == 0
            and v11_old["summary"]["fail"] == 3
            and len(ns) == 1 and ns[0]["verdict"] == "DONE_NS"               # MISSING_SOURCE=非個股的正常態
            and len(st) == 1 and st[0]["verdict"] == "FAIL"                  # 個股照舊要核對
            and len(nsbad) == 1 and nsbad[0]["verdict"] == "FAIL"            # 非個股但數字對不起來=照樣 FAIL
            and v11["summary"]["done_non_stock"] == 1
            and v11["summary"]["fail"] == 2
            and v11["summary"]["kind_hist"].get("產業") == 1,
            f"(無欄 {[x['verdict'] for x in v11_old['rows']]} → 有欄 產業={ns[0]['verdict']}/個股={st[0]['verdict']})")

    # ⑫ 批425:--db/--zones 必須真的傳到 vrn_closeout。攔真實呼叫來證明,
    # 不掃原始碼字串(那只證明字在,不證明會生效)。
    _seen = {}
    _real_co, _real_argv = globals()["closeout"], sys.argv
    try:
        globals()["closeout"] = lambda verb="all", **kw: (_seen.update(kw) or
                                                          {"verdict": "GREEN"})
        sys.argv = ["x", "vrn", "--db", "/tmp/_x_.duckdb", "--zones", "/tmp/_z_"]
        _rc = main()
        _seen2 = {}
        globals()["closeout"] = lambda verb="all", **kw: (_seen2.update(kw) or
                                                          {"verdict": "GREEN"})
        sys.argv = ["x", "vrn"]                       # 不給旗標=不得硬塞 None 進去
        _rc2 = main()
    finally:
        globals()["closeout"], sys.argv = _real_co, _real_argv
    chk("⑫ CLI --db/--zones 真的傳到 vrn_closeout(批425:v0104 以前 main() 不解析,"
        "收尾閘永遠讀寫死的預設庫;實跑證據=ENG080 報 GREEN/上漲已算 3/3,"
        "收尾卻三份都印「四點-」,因為兩邊讀的不是同一個庫。"
        "不給旗標時不得硬塞 None,以免覆蓋函式預設值)",
        _rc == 0 and str(_seen.get("db")) == "/tmp/_x_.duckdb"
        and str(_seen.get("zones")) == "/tmp/_z_"
        and _rc2 == 0 and "db" not in _seen2 and "zones" not in _seen2,
        f"(db={_seen.get('db')} zones={_seen.get('zones')};"
        f"無旗標時 kw={sorted(_seen2)})")


    # --- 批438-B3 ⑬:四點的 TP 合理性態也算數(批422 假綠;操作員 2026-09-12 明令「好」)---
    with tempfile.TemporaryDirectory() as td13:
        r13 = Path(td13)
        z13 = r13 / "zones"; z13.mkdir()
        d13 = r13 / "rep"; d13.mkdir()
        for stem in ("MS-Thermal Solutions 20251007", "MS-Memory 20251204"):
            (d13 / f"{stem}.pdf").write_text("x", encoding="utf-8")
            (z13 / f"{stem}.json").write_text("{}", encoding="utf-8")
        db13 = r13 / "k.duckdb"
        c13 = duckdb.connect(str(db13))
        c13.execute("CREATE TABLE vrn_report_basic(report_file VARCHAR, ticker VARCHAR, name_official VARCHAR, "
                    "broker VARCHAR, report_date VARCHAR, rating_raw VARCHAR, target_price DOUBLE, price DOUBLE, "
                    "upside_report DOUBLE, upside_calc DOUBLE, upside_state VARCHAR, title_head VARCHAR, "
                    "summary_head VARCHAR, conflicts VARCHAR, extracted_at VARCHAR, report_kind VARCHAR)")
        # 兩份都是非個股、upside_state 都是正常的 MISSING_SOURCE——
        # 舊碼只看這一欄,所以兩份都會拿到 DONE_NS。
        for f in ("MS-Thermal Solutions 20251007.pdf", "MS-Memory 20251204.pdf"):
            c13.execute("INSERT INTO vrn_report_basic VALUES (?,'','','MS','2025-10-07','',NULL,NULL,"
                        "NULL,NULL,'MISSING_SOURCE','','','','t','產業')", [f])
        c13.execute("CREATE TABLE vrn_report_metrics(report_file VARCHAR, metric VARCHAR, period VARCHAR, "
                    "status VARCHAR, value DOUBLE, raw_text VARCHAR)")
        # 四點文摘:一份 OK、一份 TP_SUSPECT(目標價與現價比值荒謬=數字抽出來了卻對不起來)
        c13.execute("CREATE TABLE vrn_four_point_digest(report_file VARCHAR, headline VARCHAR, "
                    "k1 VARCHAR, k2 VARCHAR, k3 VARCHAR, k4 VARCHAR, k5 VARCHAR, qc VARCHAR, "
                    "upside_now DOUBLE, tp_state VARCHAR)")
        c13.execute("INSERT INTO vrn_four_point_digest VALUES "
                    "('MS-Thermal Solutions 20251007.pdf','散熱','','','','','','',NULL,'OK'),"
                    "('MS-Memory 20251204.pdf','記憶體','','','','','','',NULL,'TP_SUSPECT')")
        c13.close()
        v13 = vrn_closeout(spec, db=db13, zones=z13, report_dirs=[d13],
                           reports_dir=r13 / "o", do_print=False, mod=mod)
        ok13 = next(x for x in v13["rows"] if x["report_file"].startswith("MS-Thermal"))
        bad13 = next(x for x in v13["rows"] if x["report_file"].startswith("MS-Memory"))
    chk("⑬ 四點的 TP 合理性態也算數(批422 記的假綠,操作員 2026-09-12 明令修:"
        "ENG080 四點文摘自己有一道 TP 合理性閘(tp_state=TP_SUSPECT 表示目標價與現價"
        "比值荒謬),而 DONE_NS 的守衛**只讀 vrn_report_basic 的 upside_state,"
        "從來沒讀過它**。於是「四點說目標價有問題」抓到了、也寫進庫了,收尾閘卻看不到。"
        "TP_SUSPECT 的定義正是 _REAL_BAD_STATES 講的「數字抽出來了而且對不起來」,"
        "只是它住在另一張表——同一個判準兩個來源,不能只讀一個。"
        "這一修會讓燈變(DONE 少、FAIL 多),所以等操作員點頭才動)",
        ok13["verdict"] == "DONE_NS" and bad13["verdict"] != "DONE_NS"
        and ok13.get("fp_tp_state") == "OK" and bad13.get("fp_tp_state") == "TP_SUSPECT",
        f"(四點 OK→{ok13['verdict']} · 四點 TP_SUSPECT→{bad13['verdict']}"
        f"(舊碼會給 DONE_NS=假綠))")

    # ⑭ 兩律都要**真的**由冊擁有者供應,不是各抄一份(批446)
    _m46 = console_mod()
    _has = {k: (getattr(_m46, k, None) is not None) for k in ("vrn_report_dirs", "mega_db")}
    _sp46 = {"families": {"vrn": {"input": {"dir_default": "fx_d", "incoming": "fx_i"}}},
             "user": {"vrn_dir": ""}}
    _mine = [str(x) for x in _report_dirs(_sp46, None)]
    _theirs = ([str(x) for x in _m46.vrn_report_dirs(_sp46, None)]
               if _has["vrn_report_dirs"] else None)
    # 舊版 MDL139 掛上來(沒有這兩支)時要退本地實作,零回歸——**真的走一遍**,
    # 不用「原始碼裡有沒有這串字」當證據:那種判準會match 到檢自己的敘述文字
    # (本檔這一段就含著它要找的字串),等於恆真。
    class _OldConsole:
        load_spec = staticmethod(lambda *a, **k: _sp46)
    _keep141 = globals()["console_mod"]
    try:
        globals()["console_mod"] = lambda *a, **k: _OldConsole()
        _fb_dirs = [str(x) for x in _report_dirs(_sp46, None)]
        _fb_db = _mega_db()
    finally:
        globals()["console_mod"] = _keep141
    chk("⑭ 報告夾律與主庫路徑律由**冊擁有者 MDL139 供應**,本檔只轉呼叫(批446:"
        "原本這裡自己抄了一份,docstring 還寫「同 MDL139 dir 參數」——**那句是假的**,"
        "本檔併 incoming、MDL139 不併;工作站 64 份報告全在 incoming,於是本檔看得見"
        "「夾✓ 64」而 MDL139 回 NEED_DIR 把鏈第一段停掉。「同某某」寫在註解裡不會讓它"
        "真的相同,要相同就得是同一支函式)。舊版 MDL139 掛上來時退本地實作並印因由",
        _has["vrn_report_dirs"] and _has["mega_db"] and _mine == _theirs
        and _fb_dirs == _mine and isinstance(_fb_db, tuple) and len(_fb_db) == 2,
        f"(正本在位={_has} · 兩邊解出一致={_mine == _theirs} · "
        f"夾={[Path(x).name for x in _mine]} · 舊版退路解出一致={_fb_dirs == _mine})")

    print(f"  [計] 十四檢({len(done)} 檢) OK {len(done) - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


# ---------------------------------------------------------------- CLI
def _arg(a: list, flag: str, default=None):
    if flag in a:
        i = a.index(flag)
        if i + 1 < len(a):
            return a[i + 1]
    return default


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 收尾閘(CGC_MDL141_ClosingGate v0105)· 十二檢自測(零網路;臨時庫/臨時夾/假圖)===")
        return selftest()
    verb = next((x for x in a if x in VERBS), "all")
    as_json = "--json" in a
    # 批425(沙盒實跑整條鏈時發現):vrn_closeout(..., db=DB_TW, zones=...) 兩個參數
    # 一直都在,closeout(**kw) 也一直會轉發,**但 main() 從來沒把 --db/--zones 放進去**
    # =收尾閘寫死預設庫。後果:④ ENG080 明明 GREEN 且上漲已算 3/3,收尾卻三份都印
    # 「四點-」——因為它讀的是另一個庫(還殘留著自測的 fx_*/synthetic 遺留件)。
    # 與批423 $StageTimeoutSec、批425 ENG073 --dir/--db 同一家族:宣告了、沒接線。
    _kw = {}
    for _flag, _key in (("--db", "db"), ("--zones", "zones")):
        _v = _arg(a, _flag)
        if _v:
            _kw[_key] = Path(_v)
    try:
        rep = closeout(verb, run="--run" in a, report_dir=_arg(a, "--dir"), do_print=not as_json, **_kw)
    except RuntimeError as exc:
        print(f"[FAIL] {exc}")
        return 3
    if as_json:
        print(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
    return {"GREEN": 0, "YELLOW": 0, "GREY": 0}.get(rep["verdict"], 2)


if __name__ == "__main__":
    sys.exit(main())
