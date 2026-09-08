#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL140_HandoverConsole v0100 — VIA Central Console 接棒狀態台(批392)
====================================================================
操作員令(批392):「VIA Central Console 一定是超詳細的系統狀態,如 handover reports;表格最佳化;分門別類堆疊矩陣一頁
展示;可轉換成 MD 供下一日接棒者繼續接手」。
機制(Zero-Hydra:不另算,只彙整母倉各引擎的 *_latest.json 存證與 git/冊;缺件誠實列「未跑/缺」):
  ① 來源冊(SOURCES):分門別類 → 每類多個來源(JSON 存證/冊/log/表),每來源=一張矩陣(列=字典或清單展開;欄自動)
     倉:git 分支/HEAD/近 8 commit/工作樹 · 環境:EnvGov RUN_latest · 能跑閘:RUNGATE_latest · 家族 U/I:FAMILY_UI_latest
     入口:ENTRY_latest 燈板 · 樞紐:deck_runs log 冊(近 30) · 主控台:CONSOLE_latest(項目可跑態/VRN 跑況摘要)
     庫:VIA_VDFArchitecture 表列(列數/最新日/滯後) · 對齊:ALIGN_latest/UNIVERSE_latest · 本機三庫:RUN_latest/COVERAGE_latest
     VRN:four_point DIGEST_latest 摘要 · VAP:產出頁 · 日更鏈:boot_update_logs 最新 log 步況 · 候操作員:Handover_Gap_Register
     · 次步:自各來源 next/verdict 推導(只列已存證的建議;不發明)
  ② build:VIA_UI_Handover_v0100.html(零 CDN;一頁堆疊;每矩陣篩選/點欄排序/摺疊;「複製 Markdown」鈕)
     + VIA_Reports/handover/HANDOVER_latest.md(同內容 Markdown 表;可直接貼給下一位接棒者)+ HANDOVER_latest.json
  ③ status:印各類來源在位/缺席燈;md:只印 Markdown
紀律:只增不減;正本零觸碰(只讀);誠實三態(來源缺=GREY「未跑」;讀取失敗=YELLOW);零 CDN;零網路;尾版律。
用法:python3 CGC_MDL140_HandoverConsole_v0100.py [build] [--open] | status | md | --selftest
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

import datetime as _dt
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPO = VIA.parent
UI_DIR = VIA / "supportive modules" / "ui_support"
OUT_PAGE = UI_DIR / "VIA_UI_Handover_v0100.html"
REPORTS = VIA / "VIA_Reports" / "handover"
LOG = VIA / "logs" / "handover.log"
BRIDGE = "http://127.0.0.1:8765"
VERBS = ("build", "status", "md")
CDN_RX = re.compile(r"<(?:script|link)[^>]+(?:src|href)=[\"']https?://", re.I)
MAX_ROWS = 400


def _now() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def log_event(kind: str, msg: str, **kw) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": _now(), "kind": kind, "msg": msg, **kw}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _write_text(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, p)


def _read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _git(args: list, cwd: Path) -> str:
    try:
        r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=20, stdin=subprocess.DEVNULL)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def _mtime(p: Path) -> str:
    try:
        return _dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ""


def _cell(v) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "✓" if v else "✗"
    if isinstance(v, float):
        return f"{v:,.4g}" if abs(v) < 1e6 else f"{v:,.0f}"
    if isinstance(v, int):
        return f"{v:,}"
    if isinstance(v, (list, dict)):
        s = json.dumps(v, ensure_ascii=False, default=str)
        return s[:160] + ("…" if len(s) > 160 else "")
    s = str(v)
    return s[:200] + ("…" if len(s) > 200 else "")


# ---------------------------------------------------------------- 來源冊 → 矩陣
def _rows_from(obj, keys: list | None = None) -> list:
    """字典/清單 → 列表(欄自動):dict of dict → 列=鍵+子欄;list of dict → 原列;dict 平面 → 鍵/值兩欄"""
    if isinstance(obj, list):
        rows = [r if isinstance(r, dict) else {"value": r} for r in obj]
    elif isinstance(obj, dict):
        if obj and all(isinstance(v, dict) for v in obj.values()):
            rows = [{"key": k, **v} for k, v in obj.items()]
        else:
            rows = [{"key": k, "value": v} for k, v in obj.items()]
    else:
        rows = [{"value": obj}]
    if keys:
        rows = [{k: r.get(k) for k in keys} for r in rows]
    return rows[:MAX_ROWS]


def matrix(cat: str, title: str, rows: list, lamp: str = "GREEN", note: str = "", src: str = "", cols: list | None = None) -> dict:
    rows = [r for r in (rows or []) if isinstance(r, dict)]
    if cols is None:
        seen = []
        for r in rows:
            for k in r:
                if k not in seen:
                    seen.append(k)
        cols = seen[:14]
    return {"cat": cat, "title": title, "lamp": lamp if rows or lamp != "GREEN" else "GREY", "note": note, "src": src, "cols": cols,
            "rows": [{c: _cell(r.get(c)) for c in cols} for r in rows], "n": len(rows)}


def gather(via: Path = VIA, do_git: bool = True) -> dict:
    """彙整所有來源 → {ts, cats:[{id,zh,matrices:[...]}], summary, next, lamps}"""
    rep = {"schema": "VIA.Handover.v1", "ts": _now(), "via": str(via), "cats": [], "lamps": {}, "next": [], "summary": {}}
    R = via / "VIA_Reports"
    reg = via / "supportive modules" / "registry"

    def cat(cid, zh):
        c = {"id": cid, "zh": zh, "matrices": []}
        rep["cats"].append(c)
        return c

    def add(c, title, obj, src="", note="", lamp="GREEN", cols=None, rows=None):
        if rows is None:
            if obj is None:
                c["matrices"].append(matrix(c["id"], title, [], "GREY", note or f"未跑/缺:{src}", src, cols or []))
                return
            rows = _rows_from(obj)
        c["matrices"].append(matrix(c["id"], title, rows, lamp, note, src, cols))

    # 1 倉
    c = cat("repo", "母倉(git)")
    if do_git:
        br, head = _git(["rev-parse", "--abbrev-ref", "HEAD"], via), _git(["rev-parse", "--short", "HEAD"], via)
        st = _git(["status", "--short"], via)
        logs = _git(["log", "--oneline", "-8"], via).splitlines()
        rep["summary"]["branch"], rep["summary"]["head"] = br, head
        add(c, "分支/HEAD/工作樹", None if not br else [{"branch": br, "head": head, "dirty_files": len(st.splitlines()), "remote": _git(["remote", "get-url", "origin"], via)}], "git", lamp="GREEN" if br else "YELLOW", note="" if br else "非 git 倉或 git 缺")
        add(c, "近 8 次提交", [{"commit": ln[:8], "subject": ln[9:120]} for ln in logs] if logs else None, "git log", cols=["commit", "subject"])
        rep["lamps"]["repo"] = "GREEN" if br else "YELLOW"
    # 2 入口燈板
    c = cat("entry", "單一入口燈板(MDL136)")
    ent = _read_json(R / "entry" / "ENTRY_latest.json")
    add(c, "燈板", [{"lamp": x.get("lamp"), "layer": x.get("layer"), "msg": x.get("msg")} for x in (ent or {}).get("lamps", [])] if ent else None, "VIA_Reports/entry/ENTRY_latest.json", cols=["lamp", "layer", "msg"])
    rep["lamps"]["entry"] = (ent or {}).get("verdict") or ("GREY" if not ent else "GREEN")
    # 3 環境治理
    c = cat("env", "環境治理(MDL135)")
    ev = _read_json(R / "env_governance" / "RUN_latest.json")
    if ev:
        s = ev.get("summary") or {}
        add(c, "上次治理摘要", [{"verdict": ev.get("verdict"), "mode": ev.get("mode"), "ts": ev.get("ts"), **{k: v for k, v in s.items() if not isinstance(v, (dict, list))}}], "VIA_Reports/env_governance/RUN_latest.json")
        stages = ev.get("stages") or ev.get("plan") or []
        if isinstance(stages, list) and stages:
            add(c, "段況", [{k: st.get(k) for k in ("kind", "env", "state", "note", "verdict") if k in st} for st in stages if isinstance(st, dict)][:120], "RUN_latest.stages")
    else:
        add(c, "上次治理摘要", None, "VIA_Reports/env_governance/RUN_latest.json(via-envgov)")
    rep["lamps"]["env"] = (ev or {}).get("verdict", "GREY")
    # 4 能跑閘
    c = cat("rungate", "能跑閘(MDL137)")
    rg = _read_json(R / "rungate" / "RUNGATE_latest.json")
    if rg:
        fams = rg.get("families") or {}
        add(c, "家族判定", [{"family": f, "verdict": v.get("verdict"), "python": (v.get("python") or {}).get("python"), "state": (v.get("python") or {}).get("state"),
                          "required": f"{(v.get('summary') or {}).get('required_ok')}/{(v.get('summary') or {}).get('required_n')}", "engines": f"{(v.get('summary') or {}).get('engines_ok')}/{(v.get('summary') or {}).get('engines_n')}",
                          "reasons": "; ".join(v.get("reasons") or [])} for f, v in fams.items()], "VIA_Reports/rungate/RUNGATE_latest.json")
        add(c, "站況", [{"family": f, **{k: r.get(k) for k in ("station", "state", "secs", "tail") if k in r}} for f, v in fams.items() for r in (v.get("results") or [])][:150], "RUNGATE_latest.results")
    else:
        add(c, "家族判定", None, "VIA_Reports/rungate/RUNGATE_latest.json(via-rungate)")
    rep["lamps"]["rungate"] = (rg or {}).get("verdict", "GREY")
    # 5 家族 U/I
    c = cat("famui", "家族 U/I(MDL138)")
    fu = _read_json(R / "ui" / "FAMILY_UI_latest.json")
    if fu:
        add(c, "頁況", [{"family": f, **{k: it.get(k) for k in ("label", "state", "page", "note", "secs") if k in it}} for f, v in (fu.get("families") or {}).items() for it in (v.get("items") or [])][:100], "VIA_Reports/ui/FAMILY_UI_latest.json")
    else:
        add(c, "頁況", None, "VIA_Reports/ui/FAMILY_UI_latest.json(via-famui)")
    rep["lamps"]["famui"] = (fu or {}).get("verdict", "GREY")
    # 6 樞紐任務
    c = cat("deck", "樞紐任務(DeckServer deck_runs)")
    dr = R / "deck_runs"
    logs = sorted(dr.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)[:30] if dr.exists() else []
    rows = []
    for lp in logs:
        try:
            tail = lp.read_text(encoding="utf-8", errors="ignore").strip().splitlines()[-1:]
        except Exception:
            tail = []
        rows.append({"task": lp.stem, "mtime": _mtime(lp), "kb": lp.stat().st_size // 1024, "last_line": (tail[0] if tail else "")[:140]})
    add(c, "近 30 任務 log", rows if rows else None, "VIA_Reports/deck_runs/*.log", cols=["task", "mtime", "kb", "last_line"])
    # 7 主控台
    c = cat("console", "輸入主控台(MDL139)")
    cs = _read_json(R / "console" / "CONSOLE_latest.json")
    if cs:
        add(c, "項目可跑態", [{"item": k, **{kk: v.get(kk) for kk in ("family", "state", "start", "net", "note") if kk in v}} for k, v in (cs.get("items") or {}).items()], "VIA_Reports/console/CONSOLE_latest.json")
        vs = (cs.get("vrn") or {}).get("summary") or {}
        add(c, "VRN 跑況摘要", [vs] if vs else None, "CONSOLE_latest.vrn.summary")
        fs = cs.get("family_success") or {}
        if fs:
            add(c, "VDF/VRN/VAP 跑成功?", [{"family": f, **v} for f, v in fs.items()], "CONSOLE_latest.family_success")
    else:
        add(c, "項目可跑態", None, "VIA_Reports/console/CONSOLE_latest.json(via-console status)")
    rep["lamps"]["console"] = (cs or {}).get("verdict", "GREY")
    # 8 庫
    c = cat("db", "資料庫(ENG073 架構冊)")
    arch = _read_json(reg / "VIA_VDFArchitecture_v0100.json")
    if arch and isinstance(arch.get("inventory"), dict):
        rows = []
        for dbk, inv in arch["inventory"].items():
            for t, v in (inv.get("tables") or {}).items():
                rows.append({"db": dbk, "table": t, "rows": v.get("rows"), "max": v.get("max"), "lag_days": v.get("lag_days")})
        rows.sort(key=lambda r: -(r.get("rows") or 0))
        add(c, "表列數/最新日/滯後", rows, f"VIA_VDFArchitecture_v0100.json({arch.get('stamp', '')})", cols=["db", "table", "rows", "max", "lag_days"])
        add(c, "資料類別狀態", [{"id": x.get("id"), "zh": x.get("zh"), "state": x.get("state"), "n_targets": x.get("n_targets")} for x in (arch.get("categories") or [])], "categories")
    else:
        add(c, "表列數/最新日/滯後", None, "VIA_VDFArchitecture_v0100.json(via-vdfarch build)")
    # 9 對齊/清單
    c = cat("align", "日交易×籌碼對齊/股票清單(ENG081)")
    al = _read_json(R / "vdf" / "universe" / "ALIGN_latest.json")
    add(c, "對齊判定", [{"verdict": al.get("verdict"), "note": al.get("note"), **(al.get("latest") or {}), **{f"summary.{k}": v for k, v in (al.get("summary") or {}).items()}}] if al else None, "VIA_Reports/vdf/universe/ALIGN_latest.json(via-align check)")
    if al:
        add(c, "逐日", al.get("dates") or [], "ALIGN_latest.dates", cols=["date", "px_n", "chip_n", "both", "px_only", "chip_only", "verdict"])
    un = _read_json(R / "vdf" / "universe" / "UNIVERSE_latest.json")
    add(c, "清單更新", [{"mode": un.get("mode"), "asof": un.get("asof"), "rows": un.get("rows"), "new": un.get("new"), "parquet": un.get("parquet"), "note": un.get("note")}] if un else None, "UNIVERSE_latest.json(via-align update --apply)")
    rep["lamps"]["align"] = {"ALIGNED": "GREEN", "PARTIAL": "YELLOW", "MISALIGNED": "YELLOW", "RED": "RED"}.get((al or {}).get("verdict", ""), "GREY")
    # 10 本機三庫
    c = cat("localdb", "本機三庫整併(ENG079)")
    ld = _read_json(R / "vdf" / "local_db" / "RUN_latest.json")
    add(c, "整併摘要", [{"verdict": ld.get("verdict"), "mode": ld.get("mode"), "ts": ld.get("ts"), **(ld.get("summary") or {})}] if ld else None, "VIA_Reports/vdf/local_db/RUN_latest.json(via-vdfdb)")
    if ld:
        add(c, "單元", [{k: u.get(k) for k in ("part", "unit", "target", "state", "n_rows", "planned_new", "rows_new", "note")} for u in (ld.get("units") or [])][:150], "RUN_latest.units")
    cv = _read_json(R / "vdf" / "local_db" / "COVERAGE_latest.json")
    add(c, "覆蓋", [{"table": t, "rows": v.get("rows"), "tickers": v.get("tickers"), "min": v.get("min"), "max": v.get("max")} for t, v in ((cv or {}).get("tables") or {}).items()] if cv else None, "COVERAGE_latest.json")
    rep["lamps"]["localdb"] = (ld or {}).get("verdict", "GREY")
    # 11 VRN
    c = cat("vrn", "VRN 研究報告")
    fp = _read_json(R / "vrn" / "four_point" / "DIGEST_latest.json")
    add(c, "一題四點摘要", [{"verdict": fp.get("verdict"), "note": fp.get("note", ""), **(fp.get("summary") or {})}] if fp else None, "VIA_Reports/vrn/four_point/DIGEST_latest.json(via-vrn4)")
    if fp and fp.get("rows"):
        add(c, "報告四點", [{k: r.get(k) for k in ("report_file", "ticker", "report_date", "headline", "upside_now", "qc")} for r in fp["rows"]][:100], "DIGEST_latest.rows")
    if cs and (cs.get("vrn") or {}).get("reports"):
        add(c, "跑況矩陣(BASIC INFO/SUMMARY/FINANCIAL DATA)", [{k: r.get(k) for k in ("report_file", "ticker", "report_date", "basic", "summary", "financial", "overall")} for r in cs["vrn"]["reports"]][:150], "CONSOLE_latest.vrn.reports")
    inc = via / "functional modules" / "VRN" / "input" / "incoming"
    files = sorted(f for f in inc.glob("*") if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in (".pdf", ".docx")) if inc.exists() else []   # 批399 自審:.gitkeep 等不算報告
    add(c, "收件夾 incoming", [{"name": f.name, "kb": f.stat().st_size // 1024, "mtime": _mtime(f)} for f in files][:100] or None, str(inc.relative_to(via)), note="" if files else "空(拖曳/選夾入件)")
    co_v = _read_json(R / "closeout" / "VRN_CLOSEOUT_latest.json")   # 批398 收尾閘(via-closeout vrn)
    add(c, "驗證收尾(五段鏈+核對態;via-closeout vrn)", [{k: r.get(k) for k in ("report_file", "ticker", "report_date", "stage_zh", "basic", "financial", "fin_vdf_over", "verdict")} for r in (co_v or {}).get("rows", [])][:150] if co_v else None,
        "VIA_Reports/closeout/VRN_CLOSEOUT_latest.json", lamp=(co_v or {}).get("verdict", "GREY"), note=(co_v or {}).get("note", ""))
    rep["lamps"]["vrn"] = (fp or {}).get("verdict", "GREY")
    # 12 VAP
    c = cat("vap", "VAP 產出")
    pages = ["VIA_UI_Dashboard_v0100.html", "VIA_UI_StdDashboard_v0100.html", "VIA_UI_VapStack_v0100.html", "VIA_UI_InputConsole_v0100.html", "VIA_UI_MasterControl_v0100.html", "VIA_UI_VDFArchitecture_v0100.html", "VIA_UI_VRNControlTower_v0100.html"]
    add(c, "頁面在位", [{"page": p, "exists": (UI_DIR / p).exists(), "mtime": _mtime(UI_DIR / p) if (UI_DIR / p).exists() else ""} for p in pages], "supportive modules/ui_support", cols=["page", "exists", "mtime"])
    led = R / "vap_one" / "vap_one_ledger.jsonl"
    if led.exists():
        try:
            lines = [json.loads(x) for x in led.read_text(encoding="utf-8").strip().splitlines()[-10:]]
            add(c, "VAP ONE 台帳(近 10)", lines, "VIA_Reports/vap_one/vap_one_ledger.jsonl")
        except Exception:
            pass
    co_a = _read_json(R / "closeout" / "VAP_CLOSEOUT_latest.json")   # 批398 收尾閘(via-closeout vap)
    add(c, "產出收尾(逐圖驗;via-closeout vap)", [{k: r.get(k) for k in ("name", "kind", "kb", "mtime", "dims", "valid", "why")} for r in (co_a or {}).get("images", [])][:150] if co_a else None,
        "VIA_Reports/closeout/VAP_CLOSEOUT_latest.json", lamp=(co_a or {}).get("verdict", "GREY"), note=(co_a or {}).get("note", ""))
    co = _read_json(R / "closeout" / "CLOSEOUT_latest.json")
    rep["lamps"]["closeout"] = (co or {}).get("verdict", "GREY")
    # 13 日更鏈
    c = cat("boot", "日更鏈(boot_update_logs)")
    bl = R / "boot_update_logs"
    blogs = sorted([p for p in bl.glob("BOOT_*.log")], key=lambda p: p.stat().st_mtime, reverse=True)[:1] if bl.exists() else []
    if blogs:
        txt = blogs[0].read_text(encoding="utf-8", errors="ignore")
        steps = [ln.strip() for ln in txt.splitlines() if ln.startswith("--- ") or "步" in ln[:6]]
        add(c, f"最新 log {blogs[0].name}(步)", [{"step": s[:160]} for s in steps][:60] or [{"step": "(無步標記)"}], "VIA_Reports/boot_update_logs", note=f"{len(txt.splitlines())} 行 · {_mtime(blogs[0])}")
        rep["summary"]["boot_log"] = blogs[0].name
    else:
        add(c, "最新 log", None, "VIA_Reports/boot_update_logs(via 日更鏈)")
    # 14 候操作員
    c = cat("pending", "候操作員(Handover Gap Register)")
    gap = _read_json(reg / "VIA_Handover_Gap_Register_v0100.json")
    if gap:
        add(c, f"{gap.get('schema', '')} {gap.get('version', '')} · {gap.get('activation_status', '')}", [{k: it.get(k) for k in ("id", "risk", "status", "detail")} for it in (gap.get("items") or [])], "VIA_Handover_Gap_Register_v0100.json", cols=["id", "risk", "status", "detail"])
    else:
        add(c, "候操作員", None, "VIA_Handover_Gap_Register_v0100.json")
    # 15 次步(只列各來源已存證的 next;不發明)
    nxt = []
    for name, obj in (("vdfdb", ld), ("align", al), ("console", cs), ("rungate", rg), ("entry", ent)):
        for n in (obj or {}).get("next", []) or []:
            nxt.append({"source": name, "next": n if isinstance(n, str) else json.dumps(n, ensure_ascii=False)[:160]})
    if al and al.get("verdict") in ("MISALIGNED", "PARTIAL"):
        nxt.append({"source": "align", "next": al.get("note", "")[:160]})
    rep["next"] = nxt
    c = cat("next", "次步(各來源存證之建議)")
    add(c, "次步", nxt or None, "各 *_latest.json .next", cols=["source", "next"])
    lamps = [v for v in rep["lamps"].values() if v in ("RED", "YELLOW", "GREEN")]
    rep["summary"]["verdict"] = "RED" if "RED" in lamps else ("YELLOW" if "YELLOW" in lamps else ("GREEN" if lamps else "GREY"))
    rep["summary"]["matrices"] = sum(len(c["matrices"]) for c in rep["cats"])
    rep["summary"]["missing"] = sum(1 for c in rep["cats"] for m in c["matrices"] if m["lamp"] == "GREY")
    # 批394 工作站實錄:「未跑/缺 1 · 判定 RED」看不出是哪一類 → 點名 RED 燈與缺件來源(操作員一眼知道該跑什麼)
    rep["summary"]["red"] = [k for k, v in rep["lamps"].items() if v == "RED"]
    rep["summary"]["missing_names"] = [f"{c['id']}:{m['title']}" for c in rep["cats"] for m in c["matrices"] if m["lamp"] == "GREY"][:12]
    return rep


def _flags(rep: dict) -> str:
    sm = rep.get("summary") or {}
    out = ""
    if sm.get("red"):
        out += " · RED 燈 " + ",".join(sm["red"])
    if sm.get("missing_names"):
        out += " · 未跑 " + ",".join(sm["missing_names"][:6]) + ("…" if len(sm["missing_names"]) > 6 else "")
    return out


# ---------------------------------------------------------------- Markdown
def to_markdown(rep: dict) -> str:
    L = [f"# VIA 接棒狀態台(Handover)· {rep['ts']} · 判定 {rep['summary'].get('verdict')}", "",
         f"- 母倉:{rep['via']}", f"- 分支 {rep['summary'].get('branch', '?')} · HEAD {rep['summary'].get('head', '?')} · 矩陣 {rep['summary'].get('matrices')} · 未跑/缺 {rep['summary'].get('missing')}",
         "- 燈:" + " · ".join(f"{k}={v}" for k, v in rep["lamps"].items()), ""]
    for c in rep["cats"]:
        L.append(f"## {c['zh']}")
        for m in c["matrices"]:
            L.append(f"### {m['title']}({m['lamp']};{m['n']} 列;{m['src']})" + (f" — {m['note']}" if m["note"] else ""))
            if not m["rows"]:
                L.append("(未跑/缺)")
                L.append("")
                continue
            cols = m["cols"]
            L.append("| " + " | ".join(str(x) for x in cols) + " |")
            L.append("|" + "---|" * len(cols))
            for r in m["rows"][:60]:
                L.append("| " + " | ".join(str(r.get(k, "")).replace("|", "\\|").replace("\n", " ") for k in cols) + " |")
            if m["n"] > 60:
                L.append(f"(… 其餘 {m['n'] - 60} 列見 HANDOVER_latest.json)")
            L.append("")
    if rep.get("next"):
        L.append("## 次步")
        for n in rep["next"]:
            L.append(f"- [{n['source']}] {n['next']}")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- 頁
CSS = r"""
:root{--bg:#f4f6f8;--paper:#fff;--ink:#202833;--mut:#596778;--line:#dfe4ea;--line2:#edf0f3;--soft:#eef3f6;--acc:#315f7d;--acc2:#dce9f1;--ok:#2f7652;--warn:#765418;--bad:#a64f46;--grey:#6e7581}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--ink);font:12px/1.45 "Segoe UI","Noto Sans TC",system-ui,sans-serif}
header{position:sticky;top:0;z-index:5;display:flex;gap:10px;align-items:center;padding:8px 14px;background:var(--paper);border-bottom:1px solid var(--line)}header h1{font-size:14px;margin:0}
.lamp{padding:2px 8px;border-radius:12px;font-weight:600;font-size:11px}.lamp.GREEN{background:#dff3e6;color:var(--ok)}.lamp.YELLOW{background:#fbeccd;color:var(--warn)}.lamp.RED{background:#f6dcd9;color:var(--bad)}.lamp.GREY{background:#e6e8eb;color:var(--grey)}
button{border:1px solid var(--line);background:var(--soft);border-radius:5px;padding:4px 10px;cursor:pointer;font:inherit;min-height:28px}
main{padding:10px 16px;display:grid;gap:10px}
details.cat{border:1px solid var(--line);border-radius:8px;background:var(--paper)}details.cat>summary{cursor:pointer;padding:7px 10px;font-weight:700;background:var(--soft);border-radius:8px 8px 0 0;display:flex;gap:8px;align-items:center}
.mx{padding:6px 10px;border-top:1px solid var(--line2)}.mx h4{margin:4px 0;font-size:12px;display:flex;gap:8px;align-items:center}.mx .src{color:var(--mut);font-weight:400;font-size:11px}
.bar{display:flex;gap:6px;align-items:center;margin:4px 0}.bar input{border:1px solid var(--line);border-radius:4px;padding:3px 6px;font:inherit;min-width:200px}
.tbox{overflow:auto;max-height:46vh;border:1px solid var(--line);border-radius:6px}table{width:100%;border-collapse:collapse;font-size:11.5px;background:var(--paper)}th{position:sticky;top:0;background:var(--soft);text-align:left;padding:4px 6px;border-bottom:1px solid var(--line);cursor:pointer;white-space:nowrap}th.sd::after{content:" ▼"}th.sa::after{content:" ▲"}td{padding:3px 6px;border-bottom:1px solid var(--line2);white-space:nowrap;max-width:420px;overflow:hidden;text-overflow:ellipsis}
td.l-green,td.l-ok,td.l-aligned,td.l-ready,td.l-verified{color:var(--ok);font-weight:600}td.l-red,td.l-fail,td.l-misaligned{color:var(--bad);font-weight:600}td.l-yellow,td.l-partial,td.l-pending{color:var(--warn);font-weight:600}
.kpi{display:flex;gap:8px;flex-wrap:wrap}.kpi div{background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:5px 10px}.kpi b{display:block;font-size:15px}
pre#md{display:none}
"""

JS = r"""
var REP=null;try{REP=JSON.parse(document.getElementById('snap').textContent);}catch(e){}
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function mx(host,m){var st={q:'',k:m.cols[0],desc:true};var bar=document.createElement('div');bar.className='bar';var q=document.createElement('input');q.type='search';q.placeholder='篩選';var cnt=document.createElement('span');bar.appendChild(q);bar.appendChild(cnt);var box=document.createElement('div');box.className='tbox';var t=document.createElement('table');box.appendChild(t);host.appendChild(bar);host.appendChild(box);
 function vis(){var rows=m.rows.filter(function(r){if(!st.q)return true;return m.cols.some(function(c){return String(r[c]||'').toLowerCase().indexOf(st.q)>=0;});});rows.sort(function(a,b){var x=a[st.k]||'',y=b[st.k]||'';var nx=parseFloat(String(x).replace(/,/g,'')),ny=parseFloat(String(y).replace(/,/g,''));if(!isNaN(nx)&&!isNaN(ny))return st.desc?ny-nx:nx-ny;return st.desc?String(y).localeCompare(String(x),'zh-Hant'):String(x).localeCompare(String(y),'zh-Hant');});return rows;}
 function render(){var rows=vis(),h='<thead><tr>';m.cols.forEach(function(c){h+='<th data-k="'+esc(c)+'" class="'+(c===st.k?(st.desc?'sd':'sa'):'')+'">'+esc(c)+'</th>';});h+='</tr></thead><tbody>';if(!rows.length)h+='<tr><td colspan="'+m.cols.length+'">(未跑/缺;誠實)</td></tr>';rows.forEach(function(r){h+='<tr>';m.cols.forEach(function(c){var v=r[c]==null?'':r[c];h+='<td class="l-'+esc(String(v).toLowerCase().slice(0,12))+'" title="'+esc(v)+'">'+esc(v)+'</td>';});h+='</tr>';});t.innerHTML=h+'</tbody>';cnt.textContent=rows.length+' / '+m.rows.length;t.querySelectorAll('th').forEach(function(th){th.onclick=function(){var k=th.getAttribute('data-k');if(st.k===k)st.desc=!st.desc;else{st.k=k;st.desc=true;}render();};});}
 q.addEventListener('input',function(){st.q=q.value.trim().toLowerCase();render();});render();}
function render(){var main=document.getElementById('main');main.innerHTML='';if(!REP){main.textContent='快照缺';return;}var k=document.getElementById('kpi');k.innerHTML='<div><b>'+esc(REP.summary.verdict)+'</b>總判</div><div><b>'+esc(REP.summary.branch||'?')+'</b>分支</div><div><b>'+esc(REP.summary.head||'?')+'</b>HEAD</div><div><b>'+REP.summary.matrices+'</b>矩陣</div><div><b>'+REP.summary.missing+'</b>未跑/缺</div>'+Object.keys(REP.lamps||{}).map(function(x){return '<div><span class="lamp '+esc(REP.lamps[x])+'">'+esc(x)+'</span></div>';}).join('');
 REP.cats.forEach(function(c){var d=document.createElement('details');d.className='cat';d.open=true;d.innerHTML='<summary>'+esc(c.zh)+' <small>('+c.matrices.length+' 矩陣)</small></summary>';c.matrices.forEach(function(m){var box=document.createElement('div');box.className='mx';box.innerHTML='<h4><span class="lamp '+esc(m.lamp)+'">'+esc(m.lamp)+'</span>'+esc(m.title)+' <span class="src">'+esc(m.src)+(m.note?' · '+esc(m.note):'')+' · '+m.n+' 列</span></h4>';mx(box,m);d.appendChild(box);});main.appendChild(d);});}
document.getElementById('copymd').onclick=function(){var md=document.getElementById('md').textContent;if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(md).then(function(){document.getElementById('copymd').textContent='已複製 Markdown ✓';});}else{var ta=document.createElement('textarea');ta.value=md;document.body.appendChild(ta);ta.select();document.execCommand('copy');ta.remove();document.getElementById('copymd').textContent='已複製 Markdown ✓';}};
document.getElementById('showmd').onclick=function(){var p=document.getElementById('md');p.style.display=p.style.display==='block'?'none':'block';};
document.getElementById('all').onclick=function(){document.querySelectorAll('details.cat').forEach(function(d){d.open=true;});};document.getElementById('none').onclick=function(){document.querySelectorAll('details.cat').forEach(function(d){d.open=false;});};
render();
"""

PAGE = r"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><meta name="via-csrf" content="">
<title>VIA 接棒狀態台 · Handover(批392)</title><style>__CSS__</style></head>
<body>
<header><h1>VIA Central Console · 接棒狀態台 <small>分門別類堆疊矩陣 · 批392 · MDL140</small></h1><span class="lamp __VERDICT__">__VERDICT__</span><small>__TS__</small><span style="flex:1"></span><button id="all" type="button">全展開</button><button id="none" type="button">全摺疊</button><button id="showmd" type="button">看 Markdown</button><button id="copymd" type="button">複製 Markdown(接棒)</button></header>
<main>
<div class="kpi" id="kpi"></div>
<div id="main"></div>
<pre id="md" style="white-space:pre-wrap;background:#fff;border:1px solid #dfe4ea;border-radius:6px;padding:10px;font:11px Consolas,monospace">__MD__</pre>
</main>
<script id="snap" type="application/json">__SNAP__</script>
<script>__JS__</script>
</body></html>
"""


def build(out: Path = OUT_PAGE, reports: Path = REPORTS, do_print: bool = True, rep: dict | None = None) -> Path:
    rep = rep or gather()
    md = to_markdown(rep)
    snap = json.dumps(rep, ensure_ascii=False, default=str).replace("</", "<\\/")
    page = (PAGE.replace("__VERDICT__", str(rep["summary"].get("verdict"))).replace("__TS__", rep["ts"])   # 批399 自審:純量占位先換,再拼 MD/快照(資料內同名字串不被改寫)
            .replace("__CSS__", CSS).replace("__JS__", JS).replace("__MD__", html.escape(md)).replace("__SNAP__", snap))
    assert not CDN_RX.search(page), "零 CDN 律"
    _write_text(out, page)
    _write_text(reports / "HANDOVER_latest.md", md)
    _write_text(reports / "HANDOVER_latest.json", json.dumps(rep, ensure_ascii=False, indent=1, default=str))
    log_event("BUILD", str(out), matrices=rep["summary"].get("matrices"), verdict=rep["summary"].get("verdict"))
    if do_print:
        print(f"[via-handover build] {out}({len(page) // 1024} KB;零 CDN)· {rep['summary'].get('matrices')} 矩陣 · 未跑/缺 {rep['summary'].get('missing')} · 判定 {rep['summary'].get('verdict')}{_flags(rep)} · MD {reports / 'HANDOVER_latest.md'} · LIVE {BRIDGE}/handover")
    return out


def status(rep: dict | None = None, do_print: bool = True) -> dict:
    rep = rep or gather()
    if do_print:
        print(f"[via-handover status] {rep['summary'].get('verdict')} · 分支 {rep['summary'].get('branch')} HEAD {rep['summary'].get('head')} · 矩陣 {rep['summary'].get('matrices')} · 未跑/缺 {rep['summary'].get('missing')}{_flags(rep)}")
        for c in rep["cats"]:
            print(f"  {c['zh']:<28} " + " · ".join(f"{m['lamp']} {m['title'][:18]}({m['n']})" for m in c["matrices"]))
    return rep


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    r1 = _rows_from({"a": {"x": 1, "y": 2}, "b": {"x": 3}})
    r2 = _rows_from([{"k": 1}, 5])
    r3 = _rows_from({"k": "v", "n": 2})
    chk("① 冊→列(dict of dict=鍵+子欄;list 混型;平面 dict=鍵/值;上限 400)", r1 == [{"key": "a", "x": 1, "y": 2}, {"key": "b", "x": 3}] and r2 == [{"k": 1}, {"value": 5}] and r3 == [{"key": "k", "value": "v"}, {"key": "n", "value": 2}] and len(_rows_from(list(range(1000)))) == 400)
    m = matrix("t", "T", [{"a": 1, "b": True, "c": None, "d": [1, 2], "e": 3.14159}], "GREEN", src="x")
    m0 = matrix("t", "空", [], "GREEN", src="y")
    chk("② 矩陣格式化(int 千分位/bool ✓/None 空/list JSON 截斷/float 4 位;欄自動;空列=GREY 誠實)", m["rows"] == [{"a": "1", "b": "✓", "c": "", "d": "[1, 2]", "e": "3.142"}] and m["cols"] == ["a", "b", "c", "d", "e"] and m0["lamp"] == "GREY" and m0["n"] == 0)
    rep = gather(do_git=True)
    ids = [c["id"] for c in rep["cats"]]
    chk("③ 來源冊彙整(15 類齊:倉/入口/環境/能跑閘/家族 U/I/樞紐/主控台/庫/對齊/本機三庫/VRN/VAP/日更鏈/候操作員/次步;缺件 GREY 不假綠;燈冊)",
        ids == ["repo", "entry", "env", "rungate", "famui", "deck", "console", "db", "align", "localdb", "vrn", "vap", "boot", "pending", "next"] and rep["summary"]["matrices"] >= 15
        and rep["summary"]["verdict"] in ("GREEN", "YELLOW", "RED", "GREY") and all(m["lamp"] in ("GREEN", "YELLOW", "RED", "GREY") for c in rep["cats"] for m in c["matrices"])
        and isinstance(rep["summary"].get("red"), list) and isinstance(rep["summary"].get("missing_names"), list) and len(rep["summary"]["missing_names"]) == min(12, rep["summary"]["missing"])
        and (("RED 燈" in _flags(rep)) == bool(rep["summary"]["red"])),
        f"({rep['summary']['matrices']} 矩陣;缺 {rep['summary']['missing']};判定 {rep['summary']['verdict']};燈 {rep['lamps']})")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "VIA_Reports").mkdir()
        rep2 = gather(root, do_git=False)
        chk("④ 空母倉誠實(全來源 GREY 未跑;不例外;判定 GREY)", rep2["summary"]["verdict"] == "GREY" and rep2["summary"]["missing"] >= 12 and all(m["lamp"] == "GREY" for c in rep2["cats"] for m in c["matrices"] if c["id"] not in ("vap",)),
            f"(缺 {rep2['summary']['missing']})")
        md = to_markdown(rep)
        chk("⑤ Markdown 匯出(標題/燈/每類 ## /每矩陣 ### 與表頭分隔線/缺=「未跑/缺」/次步清單;'|' 逃逸)", md.startswith("# VIA 接棒狀態台") and md.count("\n## ") >= 15 and "|---|" in md and "(未跑/缺)" in to_markdown(rep2) and "\\|" in to_markdown({"ts": "t", "via": "v", "summary": {}, "lamps": {}, "cats": [{"id": "x", "zh": "X", "matrices": [matrix("x", "T", [{"a": "p|q"}], src="s")]}], "next": []}))
        out = root / "VIA_UI_Handover_v0100.html"
        build(out=out, reports=root / "rep", do_print=False, rep=rep)
        page = out.read_text(encoding="utf-8")
        mm = re.search(r'<script id="snap" type="application/json">(.*?)</script>', page, re.S)
        snap = json.loads(mm.group(1).replace("<\\/", "</")) if mm else None
        chk("⑥ 頁面(零 CDN;一頁堆疊 details;每矩陣篩選/排序;複製 Markdown 鈕;快照 JSON 可解析;CSRF meta;HANDOVER_latest.md/.json 落檔)",
            not CDN_RX.search(page) and 'id="copymd"' in page and "function mx(" in page and snap is not None and snap["schema"] == "VIA.Handover.v1" and '<meta name="via-csrf" content="">' in page
            and (root / "rep" / "HANDOVER_latest.md").exists() and (root / "rep" / "HANDOVER_latest.json").exists() and page.count("<script") == 2, f"({len(page) // 1024} KB)")
    st = status(rep, do_print=False)
    chk("⑦ status 摘要(同彙整;分支/HEAD 自 git)", st is rep and ("branch" in rep["summary"]))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 紀律宣告(只增不減/正本零觸碰/誠實三態/零 CDN/零網路/尾版律/Zero-Hydra/ACCEL-BRIDGE)",
        all(k in src for k in ("只增不減", "正本零觸碰", "誠實三態", "零 CDN", "零網路", "尾版律", "Zero-Hydra", "ACCEL-BRIDGE")))
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 接棒狀態台(CGC_MDL140_HandoverConsole)· 八檢自測(零網路;臨時樹)===")
        return selftest()
    verb = next((x for x in a if x in VERBS), "build")
    try:
        if verb == "status":
            status()
            return 0
        if verb == "md":
            print(to_markdown(gather()))
            return 0
        build()
        if "--open" in a:
            print(f"  [看頁] via-open 接棒(零跳出律;或 {BRIDGE}/handover)")
        return 0
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    sys.exit(main())
