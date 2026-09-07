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
紀律:只增不減;正本零觸碰(只讀庫/只讀夾);誠實三態;零 CDN(驗圖亦以此為律);零網路;尾版律(MDL139 尾版 glob);Zero-Hydra;ACCEL-BRIDGE。
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


def vrn_closeout(spec: dict | None = None, db: Path = DB_TW, zones: Path | None = None, report_dirs: list | None = None,
                 reports_dir: Path = REPORTS, do_print: bool = True, mod=None) -> dict:
    mod = mod or console_mod()
    spec = spec or mod.load_spec()
    fam = spec["families"]["vrn"]
    zones = zones if zones is not None else VIA / fam["input"]["sidecars"]
    dirs = report_dirs if report_dirs is not None else [VIA / fam["input"]["dir_default"], VIA / fam["input"]["incoming"]]
    exts = tuple(str(x).lower() for x in fam["input"].get("extensions", [".pdf", ".docx"]))
    rep = {"schema": "VIA.Closeout.vrn.v1", "ts": _now(), "family": "vrn", "verdict": "GREY", "note": "", "db": str(db), "dirs": [str(d) for d in dirs],
           "zones": str(zones), "rows": [], "summary": {}, "next": [], "fail": []}
    files: dict = {}
    for d in dirs:
        if d.exists():
            for f in sorted(d.iterdir()):
                if f.is_file() and f.suffix.lower() in exts:
                    files.setdefault(f.name, f)
    tabs = {"reports": [], "basic": [], "summary_matrix": [], "financial": []}
    fp_files: set = set()
    duckdb = _duckdb()
    db_state = "OK"
    if duckdb is None:
        db_state, rep["note"] = "GREY", "duckdb 缺(於 via_vrn_312 境跑:via-closeout vrn)"
    elif not db.exists():
        db_state, rep["note"] = "GREY", f"庫缺 {db}(先 via-vdfdb run --apply / 日更鏈)"
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
    for name in names:
        stem = Path(name).stem
        if stem in seen_stems:
            continue
        seen_stems.add(stem)
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
        fb = fin_by.get(rf, {"n": 0, "consistent": 0, "vdf_over": 0, "no_ref": 0})
        row = {"report_file": name, "ticker": (r or {}).get("ticker", ""), "report_date": (r or {}).get("report_date", ""), "in_folder": in_folder, "sidecar": side,
               "basic_row": r is not None, "n_metrics": n_met, "n_financial": n_fin, "four_point": four, "stage": stage, "stage_zh": STAGES[stage],
               "basic": b_state, "summary": s_state, "financial": f_state, "fin_consistent": fb["consistent"], "fin_vdf_over": fb["vdf_over"], "fin_no_ref": fb["no_ref"],
               "upside_state": (r or {}).get("upside_state", ""), "price_state": (r or {}).get("price_state", ""), "verdict": verdict}
        rep["rows"].append(row)
        if verdict == "FAIL":
            rep["fail"].append({"report_file": name, "basic": b_state, "financial": f_state, "upside_state": row["upside_state"], "price_state": row["price_state"]})
    n = len(rep["rows"])
    done = sum(1 for x in rep["rows"] if x["verdict"] == "DONE")
    fail = sum(1 for x in rep["rows"] if x["verdict"] == "FAIL")
    pend = n - done - fail
    hist = {STAGES[i]: sum(1 for x in rep["rows"] if x["stage"] == i) for i in range(5)}
    rep["summary"] = {"files_in_folder": len(files), "reports": n, "done": done, "fail": fail, "pending": pend, "sidecars": sum(1 for x in rep["rows"] if x["sidecar"]),
                      "basic_rows": sum(1 for x in rep["rows"] if x["basic_row"]), "four_point": sum(1 for x in rep["rows"] if x["four_point"]), "stage_hist": hist,
                      "basic_verified": sum(1 for x in rep["rows"] if x["basic"] == "VERIFIED"), "financial_verified": sum(1 for x in rep["rows"] if x["financial"] == "VERIFIED"),
                      "fin_rows_consistent": sum(v["consistent"] for v in fin_by.values()), "fin_rows_vdf_over": sum(v["vdf_over"] for v in fin_by.values()),
                      "fin_rows_no_ref": sum(v["no_ref"] for v in fin_by.values()), "db_state": db_state}
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
            rep["note"] = f"{fail}/{n} 份核對 FAIL(報告值 vs VDF 不符或無指標;見 fail 清單 upside_state/price_state)" + (f";另 {pend} 份未跑完" if pend else "")
            nxt.append("TAB2 核對態 FAIL=報告 upside 公式不符或價表無對照:財報數以 VDF 歷史值為主(fin_final),報告本身問題誠實留 FAIL;確認 tw_daily_prices 覆蓋報告日(via-price run)後 via-console run --item vrn_structdb 重核")
        elif pend:
            rep["verdict"] = "YELLOW"
            rep["note"] = f"{pend}/{n} 份鏈未跑完(最低停在「{STAGES[low]}」)· DONE {done}"
        else:
            rep["verdict"] = "GREEN"
            rep["note"] = f"{done}/{n} 份 收件→首頁→入庫→財報頁→四點 全通且 BASIC INFO/FINANCIAL VERIFIED"
        if pend:
            item = {0: "vrn_firstpage", 1: "vrn_firstpage", 2: "vrn_structdb", 3: "vrn_finpages"}.get(low, "vrn_fourpoint")
            nxt.append(f"via-console run --item {item}(或 via-closeout vrn --run;冊 chain_default 五段自動接續)")
    rep["next"] = nxt
    _write_family(rep, reports_dir, "VRN")
    if do_print:
        print(f"[via-closeout vrn] {rep['verdict']} · {rep['note']} · 報告 {n}(DONE {done} · FAIL {fail} · PENDING {pend})· 段:{hist}")
        for x in rep["rows"][:30]:
            print(f"  {x['verdict']:<7} {x['report_file'][:40]:<40} 段 {x['stage']}/{4}({x['stage_zh']}) BASIC {x['basic']:<8} FIN {x['financial']:<8} 夾{'✓' if x['in_folder'] else '-'} 頁{'✓' if x['sidecar'] else '-'} 庫{'✓' if x['basic_row'] else '-'} 四點{'✓' if x['four_point'] else '-'}")
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


def run_chain(mod, spec: dict, family: str, report_dir: str | None = None, do_print: bool = True) -> list:
    """--run:經 MDL139 run --item(同一啟動道;家族境 python 由 MDL139 解析);任一段 rc≠0 即停(誠實)"""
    if family == "vrn":
        items = list(spec["families"]["vrn"].get("chain_default", []))
    else:
        items = ["vap_one_render"]
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


def closeout(verb: str = "all", run: bool = False, report_dir: str | None = None, reports_dir: Path = REPORTS, do_print: bool = True, mod=None, **kw) -> dict:
    mod = mod or console_mod()
    spec = mod.load_spec()
    rep = {"schema": "VIA.Closeout.v1", "ts": _now(), "verb": verb, "verdict": "GREY", "families": {}, "run": {}}
    fams = ["vrn", "vap"] if verb == "all" else [verb]
    for f in fams:
        if run:
            rep["run"][f] = run_chain(mod, spec, f, report_dir, do_print)
        if f == "vrn":
            dirs = [Path(report_dir)] if report_dir else None
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
    import io
    import tempfile
    fails = []

    def chk(name, cond, note=""):
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

            def vrn_tabs(self, con, z):
                return mod.vrn_tabs(con, z)

            def run(self, s, item, params):
                calls.append((item, dict(params)))
                return 0 if item != "vrn_finpages" else 3
        fm = FakeMod()
        rr = run_chain(fm, spec, "vrn", report_dir=str(rdir), do_print=False)
        rv = run_chain(fm, spec, "vap", do_print=False)
        chk("⑥ --run 經 MDL139 run --item 同一啟動道(vrn 冊 chain_default 依序;--dir 只給有 dir 參數的段;rc≠0 即停=誠實;vap=vap_one_render)",
            [x["item"] for x in rr] == ["vrn_firstpage", "vrn_structdb", "vrn_finpages"] and rr[-1]["rc"] == 3 and calls[0][1].get("dir") == str(rdir) and calls[1][1] == {}
            and [x["item"] for x in rv] == ["vap_one_render"], f"({[x['item'] for x in rr]})")
        allrep = closeout("all", reports_dir=out, do_print=False, mod=fm, db=db, zones=zones, image_dirs=[img], specs_csv=csvp, ledger=img / "vap_one_ledger.jsonl")
        chk("⑦ 總閘 all(兩族併列;總判取最壞 RED;CLOSEOUT_latest.json/.md 落檔;log)",
            set(allrep["families"]) == {"vrn", "vap"} and allrep["verdict"] == "RED" and (out / "CLOSEOUT_latest.json").exists() and (out / "CLOSEOUT_latest.md").exists(),
            f"({allrep['verdict']})")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 紀律宣告(只增不減/正本零觸碰/誠實三態/零 CDN/零網路/尾版律/Zero-Hydra/ACCEL-BRIDGE)",
        all(k in src for k in ("只增不減", "正本零觸碰", "誠實三態", "零 CDN", "零網路", "尾版律", "Zero-Hydra", "ACCEL-BRIDGE")))
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
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
        print("=== 收尾閘(CGC_MDL141_ClosingGate)· 八檢自測(零網路;臨時庫/臨時夾/假圖)===")
        return selftest()
    verb = next((x for x in a if x in VERBS), "all")
    as_json = "--json" in a
    try:
        rep = closeout(verb, run="--run" in a, report_dir=_arg(a, "--dir"), do_print=not as_json)
    except RuntimeError as exc:
        print(f"[FAIL] {exc}")
        return 3
    if as_json:
        print(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
    return {"GREEN": 0, "YELLOW": 0, "GREY": 0}.get(rep["verdict"], 2)


if __name__ == "__main__":
    sys.exit(main())
