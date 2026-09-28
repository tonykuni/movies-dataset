#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL228_VIADBManager v0103 — VIA 資料庫中央管控:rich 詳細摘要矩陣報告(薄尾,本體 v0102)
v0102→v0103(側線 2026-09-28;操作員令「全部整合成一支 PowerShell · 用加速器的功能 · rich 詳細摘要矩陣報告」;
           工作站首跑實量:目錄 OK · 正庫 5 · 71 表 · 15,783,873 列 · 清單 GREEN 1981 / 22 · 判定 RED):
  ① 新動詞 report:讀面板 JSON(DBM_PANEL_latest.json)+ PowerShell 側車 JSON(加速器狀態 · 行尾檢查 · 步驟耗時)+ 資料家目錄,
     用 rich 畫十二張矩陣(總判 KPI · 加速器 · 行尾 · 摘要 · 資料庫 · 核對 · 兩張清單 · 清單檢查 · mega 日期診斷 · 錯誤矩陣 ·
     AST 檔 · AST 問題),同時存 DBM_REPORT_latest.html / .txt。rich 缺 = 照實降級純文字表(同樣十二張,同樣存 .txt)。
  ② 政策附冊核對分得出「只差行尾」:正本 sha 不符時,再把 CRLF 換成 LF 算一次;相符 = AMBER「只差行尾(Z231),內容同正本」,
     不相符才是內容真的被動過。面板那一列直接講原因與修法。
  ③ mega 日期診斷:工作站實錄 20 張表合併計畫全是「— → —」(退成 part-all)。逐表列出目錄記到的日期欄 / 起迄 / 缺在哪一層
     (沒認到日期欄 · 認到欄但檔內沒有 min/max 統計),給出下一步。
  其餘(overview / reconcile / plan / export / ui / panel)一律交 v0102 本體(模組層 __getattr__ 轉接,公開面零損失)。

用法:
  python CGC_MDL228_VIADBManager_v0103.py report [--side <側車.json>] [--width N] [--rows N] [--plain]
  python CGC_MDL228_VIADBManager_v0103.py panel | overview | reconcile | plan | export … | ui     # = v0102
  python CGC_MDL228_VIADBManager_v0103.py --selftest
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

import hashlib
import importlib.util
import io
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
# 前一版 = 同族裡檔名比自己小的最新一支(glob,不釘版號 L54)
_PRIOR = [p for p in sorted(HERE.glob("CGC_MDL228_VIADBManager_v*.py")) if p.name < Path(__file__).name][-1]
_SPEC = importlib.util.spec_from_file_location("vdbm_prior_of_v0103", _PRIOR)
BASE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = BASE
_SPEC.loader.exec_module(BASE)

VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
ENGINE_TAG = "CGC_MDL228_VIADBManager v" + VERSION
OUT = BASE.OUT
REPORT_HTML = "DBM_REPORT_latest.html"
REPORT_TXT = "DBM_REPORT_latest.txt"
SIDE_JSON = "DBM_PS_SIDE_latest.json"
STATE_STYLE = {"GREEN": "green", "OK": "green", "PASS": "green", "AMBER": "yellow", "MED": "yellow", "BAD": "yellow",
               "EOL_ONLY": "yellow", "FIXED": "cyan", "RED": "bold red", "HIGH": "bold red", "ABSENT": "red",
               "UNREADABLE": "red", "CONTENT_DIFF": "bold red", "NODATA": "dark_orange", "LOW": "dim", "INFO": "dim"}


def __getattr__(name: str):
    """PEP 562:v0102 的公開面照舊可叫(panel / overview / reconcile / export …)。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(BASE, name)


# ---------------------------------------------------------------- ② 政策附冊:分得出「只差行尾」
def panel_policy(folder: Path = HERE) -> dict:
    """v0102 同判,另加:sha 不符時把 CRLF→LF 再算一次。相符 = 只差行尾(Z231;Windows autocrlf 取出),內容與正本同。"""
    res = BASE.__dict__["_v0102_panel_policy"](folder)
    if res.get("book_sha_ok") or res.get("state") in ("ABSENT", "RED"):
        return res
    book = folder / str(res.get("book") or "")
    try:
        pol = json.loads(BASE._tail(folder, "VIA_Policy_DBPanel_v*.json").read_text(encoding="utf-8"))
        raw = book.read_bytes()
    except (OSError, ValueError, AttributeError):
        return res
    lf = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()[:16]
    if lf == pol.get("book_sha256_16"):
        res.update(state="AMBER", eol_only=True,
                   why=f"只差行尾(CRLF,Z231):內容與正本 {lf} 相同 → 跑 Invoke-VIA-DBPanel-v0101(預設就修:先備份再寫回倉裡原位元;-NoEolFix 只檢查)")
    else:
        res.update(eol_only=False, why=res["why"] + " · 換成 LF 也不符 = 內容真的被動過,停,請 via 審核")
    return res


# 裝進本體:v0102 的 panel() 以模組全域名叫 panel_policy,換成這一把(原版留在 _v0102_panel_policy 供本函式委派)
if "_v0102_panel_policy" not in BASE.__dict__:
    BASE._v0102_panel_policy = BASE.panel_policy
BASE.panel_policy = panel_policy


# ---------------------------------------------------------------- ③ mega 日期診斷
def mega_diag(cat: dict | None) -> list:
    """mega 夾逐表:目錄記到的日期欄 / 起迄 → 為什麼合併計畫退成 part-all。只讀目錄頁,不開檔。"""
    groups: dict = {}
    for lk in (cat or {}).get("lake") or []:
        if str(lk.get("dataset")) != "mega":
            continue
        for m in lk.get("members") or []:
            mm = BASE.MEGA_TS_RX.match(str(m.get("table") or ""))
            stem = mm.group("stem") if mm else str(m.get("table"))
            g = groups.setdefault(stem, {"stem": stem, "files": 0, "rows": 0, "cols": set(), "dated": 0, "lo": "", "hi": ""})
            g["files"] += 1
            g["rows"] += int(m.get("rows") or 0)
            if m.get("date_col"):
                g["cols"].add(str(m["date_col"]))
            lo, hi = str(m.get("lo") or ""), str(m.get("hi") or "")
            if lo and hi:                                  # 起迄都有才算「有日期」(Codex #335:缺一邊的檔分不到年)
                g["dated"] += 1
                if lo and (not g["lo"] or lo < g["lo"]):
                    g["lo"] = lo
                g["hi"] = max(g["hi"], hi)
    out = []
    for g in sorted(groups.values(), key=lambda x: -x["files"]):
        iso = bool(BASE.ISO_RX.match(g["lo"])) and bool(BASE.ISO_RX.match(g["hi"]))
        if not g["cols"]:
            st, why, nxt = "AMBER", "目錄沒認到日期欄(欄名不在 DataHome 日期欄冊)", "把這張表的日期欄名補進 DataHome 日期欄冊,重跑 via-datahome catalog -Tables"
        elif not g["dated"]:
            st, why, nxt = "AMBER", "認到日期欄,但檔內沒有 min/max 統計", "寫檔端開 parquet 統計;或合併時用 SQL 實算 MIN/MAX(計畫 SQL 已含)"
        elif g["dated"] < g["files"]:
            st, why, nxt = ("AMBER", f"只有 {g['dated']}/{g['files']} 檔有完整起迄;其餘檔分不到年",
                            "沒日期統計的那幾檔先用 SQL 實算 MIN/MAX(或重寫開統計),全部齊了才按年切")
        elif not iso:
            st, why, nxt = "AMBER", f"日期不是西元 ISO({g['lo'][:10]}…)", "先轉西元再按年切;轉之前只能 part-all"
        else:
            st, why, nxt = "GREEN", "日期齊,可按年切 part-YYYY", "照計畫 4 的 SQL"
        out.append({"stem": g["stem"], "files": g["files"], "rows": g["rows"], "date_col": ", ".join(sorted(g["cols"])) or "—",
                    "dated_files": g["dated"], "lo": g["lo"][:10] or "—", "hi": g["hi"][:10] or "—", "state": st, "why": why, "next": nxt})
    return out


# ---------------------------------------------------------------- ① rich 報告
def _cell(v) -> str:
    if v is None or v == "":
        return "—"
    if isinstance(v, bool):
        return "OK" if v else "NG"
    if isinstance(v, int):
        return f"{v:,}"
    if isinstance(v, dict):
        return " · ".join(f"{k} {_cell(x)}" for k, x in v.items()) or "—"
    return str(v).replace("\n", " ")


def _cap(rows: list, limit: int | None, ncols: int) -> list:
    """長表只留前 limit 列,尾巴補一列「另 N 列」(Codex #335:-Rows 要真的生效;全表在面板 JSON)。"""
    if not limit or len(rows) <= limit:
        return rows
    return rows[:limit] + [[f"… 另 {len(rows) - limit} 列(全表在 {BASE.PANEL_JSON};-Rows 可加大)"] + [""] * (ncols - 1)]


def _sections(pan: dict, side: dict, diag: list, limit: int | None = None) -> list:
    """十二張矩陣:(標題, 欄, 列, 狀態欄序或 None)。列都是字串;rich 與純文字共用這一份。limit = 每張長表最多幾列。"""
    ov, k = pan.get("overview") or {}, (pan.get("overview") or {}).get("kpi") or {}
    lst, ast, pol = pan.get("lists") or {}, pan.get("ast") or {}, pan.get("policy") or {}
    sev = {s: sum(1 for r in pan.get("errors") or [] if r.get("sev") == s) for s in ("HIGH", "MED", "LOW")}
    lsum = {i["list"]: i for i in lst.get("summary") or []}
    kpi = [["總判", pan.get("verdict"), f"{pan.get('engine')} · {pan.get('ts')}"],
           ["政策", pol.get("state"), f"{pol.get('id') or '—'} · {pol.get('why', '')}"],
           ["目錄", ov.get("state"), f"{ov.get('catalog_ts') or '—'} · {ov.get('catalog_state')}"],
           ["資料庫", "OK" if k else "NODATA", f"正庫 {k.get('dbs', 0)} · 副本 {k.get('replicas', 0)} · {k.get('tables', 0)} 表 · {k.get('rows', 0):,} 列 · 最新 {k.get('latest') or '—'}"],
           ["湖", "AMBER" if k.get("bad_files") else "GREEN", f"{k.get('lakes', 0)} 夾 · {k.get('lake_files', 0)} 檔 · 壞 {k.get('bad_files', 0)}"],
           ["全部台股", (lsum.get("tw_stock") or {}).get("state", lst.get("state")), (lsum.get("tw_stock") or {}).get("why", lst.get("why", ""))],
           ["主動式台股 ETF", (lsum.get("active_tw_etf") or {}).get("state", lst.get("state")), (lsum.get("active_tw_etf") or {}).get("why", "")],
           ["錯誤矩陣", "RED" if sev["HIGH"] else ("AMBER" if sev["MED"] else "GREEN"), f"HIGH {sev['HIGH']} · MED {sev['MED']} · LOW {sev['LOW']}"],
           ["AST", "RED" if (ast.get("by_sev") or {}).get("HIGH") else ("AMBER" if (ast.get("by_sev") or {}).get("MED") else "GREEN"),
            f"{len(ast.get('files') or [])} 檔 · " + _cell(ast.get("by_class") or {})]]
    acc = side.get("accel") or {}
    accel = [[str(a), _cell(b)] for a, b in acc.items()] or [["加速器", "PowerShell 側車沒給(直接跑 python 時正常)"]]
    eol = [[e.get("file"), e.get("state"), e.get("raw16"), e.get("lf16"), e.get("head16"), e.get("action")] for e in side.get("eol") or []]
    steps = [[s.get("step"), s.get("rc"), f"{float(s.get('sec') or 0):.1f}s", s.get("note")] for s in side.get("steps") or []]
    rows_db = [[d.get("role"), d.get("name"), d.get("tables"), d.get("rows"), d.get("latest"), _cell(d.get("counts") or {})] for d in ov.get("dbs") or []]
    rec = [[r.get("state"), r.get("db"), r.get("table"), r.get("rows_now"), r.get("why")] for r in (pan.get("reconcile") or {}).get("rows") or []]
    lists_ = [[i.get("list"), i.get("state"), i.get("n"), i.get("table"), _cell(i.get("counts") or {}), _cell(i.get("dropped") or {}), i.get("why")]
              for i in lst.get("summary") or []]
    checks = [[i.get("list"), c.get("check"), "OK" if c.get("ok") else "NG", c.get("detail")] for i in lst.get("summary") or [] for c in i.get("checks") or []]
    mg = [[d["stem"], d["files"], d["rows"], d["date_col"], d["dated_files"], f"{d['lo']} → {d['hi']}", d["state"], d["why"], d["next"]] for d in diag]
    errs = [[r.get("sev"), r.get("source"), r.get("item"), r.get("desc"), r.get("action")] for r in pan.get("errors") or []]
    af = [[f.get("file"), f.get("lang"), f.get("lines"), f.get("defs"), f.get("issues"), f.get("high"), f.get("state")] for f in ast.get("files") or []]
    ai = [[i.get("sev"), i.get("cls"), f"{i.get('file')}:{i.get('line')}", i.get("desc"), i.get("action")] for i in ast.get("issues") or []]
    out = [("① 總判 KPI", ["區", "狀態", "重點"], kpi, 1),
           ("② 加速器(Celeritas PS7)", ["項目", "值"], accel, None),
           ("③ 鎖定檔行尾檢查(Z231)", ["檔", "狀態", "工作複本 sha16", "換 LF 後", "倉裡 blob", "處置"], eol, 1),
           ("④ 步驟耗時", ["步驟", "rc", "秒", "註"], steps, None),
           ("⑤ 資料庫", ["角色", "庫", "表", "列", "最新", "三態"], rows_db, None),
           ("⑥ 數量核對(非綠)", ["狀態", "庫", "表", "現在", "原因"], rec, 0),
           ("⑦ 兩張清單", ["清單", "狀態", "檔數", "表", "數", "剔除", "說明"], lists_, 1),
           ("⑧ 清單檢查", ["清單", "檢查", "結果", "細節"], checks, 2),
           ("⑨ mega 日期診斷(合併計畫為何退成 part-all)", ["表", "檔", "列", "日期欄", "有日期檔", "起 → 迄", "狀態", "原因", "下一步"], mg, 6),
           ("⑩ 錯誤矩陣", ["嚴重度", "來源", "項目", "說明", "建議處置"], errs, 0),
           ("⑪ AST 檔", ["檔", "語言", "行數", "定義", "問題", "HIGH", "狀態"], af, 6),
           ("⑫ AST 問題(含類別說明)", ["嚴重度", "類別", "檔:行", "類別說明", "建議處置"], ai, 0)]
    return [(t, c, _cap([[_cell(x) for x in r] for r in rows], limit, len(c)), s) for t, c, rows, s in out]


def _plain(sections: list, width: int) -> str:
    """rich 缺席:同樣十二張,純文字對齊(寬字算 2 格),照實標明降級。"""
    import unicodedata

    def w(s):
        return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in s)

    def fit(s, n):
        if w(s) <= n:
            return s + " " * (n - w(s))
        out = ""
        for ch in s:
            if w(out + ch) > n - 1:
                break
            out += ch
        return out + "…" + " " * (n - 1 - w(out))

    lines = ["(rich 缺席:純文字降級;同樣十二張矩陣)"]
    for title, cols, rows, _st in sections:
        lines += ["", f"━━ {title} ━━"]
        if not rows:
            lines.append("  (無)")
            continue
        n = len(cols)
        budget = max(n * 6, width - 2 - 3 * (n - 1))
        natural = [max([w(c)] + [w(r[i]) for r in rows]) for i, c in enumerate(cols)]
        widths = natural[:]
        while sum(widths) > budget:
            j = widths.index(max(widths))
            widths[j] = max(6, widths[j] - 2)
            if all(x == 6 for x in widths):
                break
        lines.append("  " + " │ ".join(fit(c, widths[i]) for i, c in enumerate(cols)))
        lines.append("  " + "─┼─".join("─" * x for x in widths))
        lines += ["  " + " │ ".join(fit(r[i], widths[i]) for i in range(n)) for r in rows]
    return "\n".join(lines)


def render_report(pan: dict, side: dict | None = None, cat: dict | None = None, width: int = 160,
                  plain: bool = False, out: Path = OUT, echo: bool = True, limit: int | None = None) -> dict:
    """十二張矩陣 → 終端 + DBM_REPORT_latest.html / .txt。回 {engine: rich|plain, paths, sections}。"""
    side = side or {}
    diag = mega_diag(cat)
    secs = _sections(pan, side, diag, limit)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    html_p, txt_p = out / REPORT_HTML, out / REPORT_TXT
    engine = "plain"
    rich = None
    if not plain:
        try:
            from rich import box
            from rich.console import Console
            from rich.table import Table
            from rich.text import Text
            rich = True
        except Exception:
            rich = None
    if rich:
        con = Console(record=True, width=max(100, int(width)), force_terminal=echo, color_system="truecolor" if echo else None,
                      legacy_windows=False, file=(sys.stdout if echo else io.StringIO()), soft_wrap=False)
        con.rule(f"[bold]VIA 資料庫詳細摘要矩陣 · {pan.get('verdict')} · {pan.get('ts')}")
        for title, cols, rows, st in secs:
            t = Table(title=title, title_justify="left", title_style="bold cyan", box=box.SIMPLE_HEAVY,
                      header_style="bold", show_lines=False, expand=False, pad_edge=False)
            for c in cols:
                t.add_column(c, overflow="fold")
            for r in rows or [["(無)"] + [""] * (len(cols) - 1)]:
                cells = list(r)
                style = STATE_STYLE.get(cells[st]) if st is not None and st < len(cells) else None
                if style:
                    cells[st] = Text(cells[st], style=style)
                t.add_row(*cells)
            con.print(t)
        con.save_html(str(html_p), inline_styles=True)
        txt_p.write_text(_plain(secs, width), encoding="utf-8")     # .txt 一律純文字對齊版(貼回、grep 都好讀)
        engine = "rich"
    else:
        text = _plain(secs, width)
        if echo:
            print(text)
        txt_p.write_text(text, encoding="utf-8")
        html_p.write_text("<!doctype html><meta charset='utf-8'><title>VIA DB Report</title><pre>"
                          + text.replace("&", "&amp;").replace("<", "&lt;") + "</pre>", encoding="utf-8")
    return {"engine": engine, "paths": {"html": str(html_p), "txt": str(txt_p)}, "sections": len(secs), "mega_diag": diag}


# ---------------------------------------------------------------- 自測(沙盒;L17 零污染)
def selftest() -> int:
    print(f"=== {ENGINE_TAG} · rich 報告 + 行尾判別 + mega 診斷自測(沙盒)===")
    res = []

    def chk(name, ok, note=""):
        res.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" ({note})" if note else ""))

    mod = sys.modules.get(__name__)
    chk("① 轉接:v0102 公開面(panel / reconcile / export / parse_flags)叫得到(TAILAPI 零損失)",
        all(callable(getattr(mod, n, None)) for n in ("panel", "reconcile", "export", "parse_flags", "ast_matrix", "error_matrix")))
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        book = b'{"laws": [1, 2]}\n{"x": 1}\n'
        (root / "VIA_Policy_Laws_SSOT_v0100.json").write_bytes(book.replace(b"\n", b"\r\n"))
        pin = hashlib.sha256(book).hexdigest()[:16]
        (root / "VIA_Policy_DBPanel_v0100.json").write_text(json.dumps({"id": "DBPANEL-1", "status": "ACTIVE", "book": "VIA_Policy_Laws_SSOT_v0100.json",
                                                                          "book_edited": False, "book_sha256_16": pin}), encoding="utf-8")
        p1 = panel_policy(root)
        (root / "VIA_Policy_Laws_SSOT_v0100.json").write_bytes(b'{"laws": [9]}\r\n')
        p2 = panel_policy(root)
        (root / "VIA_Policy_Laws_SSOT_v0100.json").write_bytes(book)
        p3 = panel_policy(root)
        chk("② 政策:只差行尾(CRLF)= AMBER 並講 Z231 修法 · 內容真的不同 = 照實講「內容被動過」· LF 原位元 = GREEN",
            p1["state"] == "AMBER" and p1.get("eol_only") is True and "Z231" in p1["why"]
            and p2.get("eol_only") is False and "內容真的被動過" in p2["why"] and p3["state"] == "GREEN", f"{p1['state']} · {p2['state']} · {p3['state']}")
        chk("② 面板用的是新一把(v0102 panel() 以全域名叫 panel_policy)", BASE.panel_policy is panel_policy)
        cat = {"lake": [{"dataset": "mega", "members": [
            {"table": "tw_daily_prices_20260901_1200", "file": "a.parquet", "rows": 5, "date_col": "date", "lo": "2026-08-25", "hi": "2026-08-29"},
            {"table": "tw_daily_prices_20260902_1200", "file": "b.parquet", "rows": 5, "date_col": "date", "lo": "2026-08-26", "hi": "2026-08-30"},
            {"table": "tw_listings_20260901_1200", "file": "c.parquet", "rows": 9, "date_col": "", "lo": "", "hi": ""},
            {"table": "tw_chip_inst_20260901_1200", "file": "d.parquet", "rows": 7, "date_col": "date", "lo": "", "hi": ""},
            {"table": "tw_rest_20260901_1200", "file": "e.parquet", "rows": 3, "date_col": "date", "lo": "115/09/01", "hi": "115/09/05"},
            {"table": "tw_margin_20260901_1200", "file": "f.parquet", "rows": 4, "date_col": "date", "lo": "2026-08-25", "hi": "2026-08-29"},
            {"table": "tw_margin_20260902_1200", "file": "g.parquet", "rows": 4, "date_col": "date", "lo": "", "hi": ""}]}]}
        dg = {d["stem"]: d for d in mega_diag(cat)}
        chk("③ mega 診斷:日期齊 = GREEN(可按年切)· 沒認到日期欄 · 有欄沒統計 · 非西元 各自講清楚",
            dg["tw_daily_prices"]["state"] == "GREEN" and dg["tw_daily_prices"]["lo"] == "2026-08-25" and dg["tw_daily_prices"]["hi"] == "2026-08-30"
            and "沒認到日期欄" in dg["tw_listings"]["why"] and "min/max" in dg["tw_chip_inst"]["why"] and "西元" in dg["tw_rest"]["why"]
            and dg["tw_margin"]["state"] == "AMBER" and "1/2" in dg["tw_margin"]["why"],
            str({k_: v["state"] for k_, v in dg.items()}))
        pan = {"verdict": "RED", "ts": "2026-09-28 12:16:17", "engine": "x",
               "overview": {"state": "OK", "catalog_ts": "t", "catalog_state": "OK", "kpi": {"dbs": 5, "rows": 15783873, "tables": 71},
                            "dbs": [{"role": "正庫", "name": "a.duckdb", "tables": 3, "rows": 10, "latest": "2026-09-25", "counts": {"GREEN": 3}}]},
               "policy": p1, "reconcile": {"rows": [{"state": "RED", "db": "a", "table": "t", "rows_now": None, "why": "冊上宣告,庫裡沒有這張表"}]},
               "lists": {"state": "GREEN", "summary": [{"list": "tw_stock", "state": "GREEN", "n": 1981, "table": "tw_listings_industry",
                                                       "counts": {"TWSE": 1089, "TPEX": 892}, "dropped": {}, "why": "股票清單 1981 檔",
                                                       "checks": [{"check": "兩所都在", "ok": True, "detail": "加權 1089 · 櫃買 892"}]}]},
               "errors": [{"sev": "HIGH", "source": "核對", "item": "a · t", "desc": "冊上宣告", "action": "補跑"}],
               "ast": {"files": [{"file": "x.py", "lang": "py", "lines": 10, "defs": 1, "issues": 0, "high": 0, "state": "GREEN"}], "issues": [], "by_class": {}, "by_sev": {}}}
        side = {"accel": {"Version": "v1141", "Cores": 8}, "eol": [{"file": "VIA_Policy_Laws_SSOT_v0100.json", "state": "FIXED", "raw16": "c7aab42f",
                                                                    "lf16": "c7aab42f", "head16": "c7aab42f", "action": "已換回倉裡原位元(備份在 restore)"}],
                "steps": [{"step": "目錄", "rc": 0, "sec": 12.5, "note": ""}]}
        out = root / "out"
        buf = io.StringIO()
        import contextlib
        with contextlib.redirect_stdout(buf):
            r_plain = render_report(pan, side, cat, width=140, plain=True, out=out)
        txt = (out / REPORT_TXT).read_text(encoding="utf-8")
        chk("④ 純文字降級:十二張矩陣都在(總判 · 加速器 · 行尾 · 步驟 · 資料庫 · 核對 · 清單 · 檢查 · mega · 錯誤 · AST×2)· 存 .txt/.html 到指定 out",
            r_plain["engine"] == "plain" and r_plain["sections"] == 12 and all(s in txt for s in ("① 總判 KPI", "② 加速器", "③ 鎖定檔行尾", "⑨ mega 日期診斷", "⑫ AST 問題"))
            and "1,981" in txt and (out / REPORT_HTML).is_file() and "純文字降級" in buf.getvalue(), f"{r_plain['engine']} · {r_plain['sections']} 張")
        many = dict(pan, errors=[{"sev": "MED", "source": "核對", "item": f"t{i}", "desc": "d", "action": "a"} for i in range(40)])
        with contextlib.redirect_stdout(io.StringIO()):
            render_report(many, side, cat, width=140, plain=True, out=out / "cap", limit=10)
        ctxt = (out / "cap" / REPORT_TXT).read_text(encoding="utf-8")
        chk("④ -Rows 生效:長表只留前 N 列 + 「另 N 列」(Codex #335)", "t9 " in ctxt and "t10 " not in ctxt and "另 30 列" in ctxt)
        chk("④ 純文字寬度:中文按 2 格算,每行不超過指定寬(140)",
            max(sum(2 if __import__('unicodedata').east_asian_width(c) in 'WF' else 1 for c in ln) for ln in txt.splitlines()) <= 142)
        try:
            import rich  # noqa: F401
            has_rich = True
        except ImportError:
            has_rich = False
        if has_rich:
            buf2 = io.StringIO()
            with contextlib.redirect_stdout(buf2):
                r_rich = render_report(pan, side, cat, width=150, out=out / "r", echo=False)
            html = (out / "r" / REPORT_HTML).read_text(encoding="utf-8")
            chk("⑤ rich:十二張矩陣存 HTML(inline 樣式,狀態上色)· echo=False 時終端零輸出",
                r_rich["engine"] == "rich" and "⑩ 錯誤矩陣" in html and "1,981" in html and "color" in html and buf2.getvalue() == "", r_rich["engine"])
        else:
            print("  [SKIP] ⑤ 本環境沒有 rich:rich 版渲染驗不了(誠實 SKIP,不當綠;純文字降級已驗)")
    ok = sum(res)
    print(f"  [計] {len(res)} 檢 OK {ok} · FAIL {len(res) - ok}")
    return 0 if ok == len(res) else 1


# ---------------------------------------------------------------- CLI
def _load_json(p: Path):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a or (a and a[0] == "selftest"):
        return selftest()
    if not a or a[0] != "report":
        return BASE.main(a)
    pan = _load_json(OUT / BASE.PANEL_JSON)
    if pan is None:
        print(f"[DBM report] 面板 JSON 不在或讀不動:{OUT / BASE.PANEL_JSON}(先跑 dbm panel)")
        return 2
    side_p = Path(a[a.index("--side") + 1]) if "--side" in a and a.index("--side") + 1 < len(a) else OUT / SIDE_JSON
    side = _load_json(side_p) or {}
    width = int(a[a.index("--width") + 1]) if "--width" in a and a.index("--width") + 1 < len(a) else int(os.environ.get("COLUMNS") or 160)
    limit = int(a[a.index("--rows") + 1]) if "--rows" in a and a.index("--rows") + 1 < len(a) else None
    cat, _st, _why = BASE.load_catalog()
    r = render_report(pan, side, cat, width=width, plain="--plain" in a, limit=limit)
    print(f"[DBM report] {r['engine']} · {r['sections']} 張矩陣 · HTML {r['paths']['html']} · TXT {r['paths']['txt']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
