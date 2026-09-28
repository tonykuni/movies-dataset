#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL229_SweepReport v0100 — VCGC 全景實測的 rich 詳細摘要矩陣(Invoke-VIA-Sweep 的報告正主)
操作員 2026-09-28:「剛才指令你是否沒加入 ps 加速指令模板及 detailed summary matrix summary by rich。把它加上」。
Invoke-VIA-Sweep-v0100 只把各步的重點行抄進貼回包,沒有矩陣。本支把同一次實測收成十張矩陣:

  ① 總判 KPI(每一步一列:狀態 · rc · 秒 · 重點)      ⑥ VDF 鏈跑器站別(讀 VDFCHAIN_latest.json:狀態 · 細節 · 修法)
  ② 加速器(Celeritas PS7 狀態 · 模板助手有沒有套上)    ⑦ VRN 鏈跑器節點(讀 VRNCHAIN_latest.json;非綠列全列、綠的只計數)
  ③ VCGC 子系統燈(系統 × 燈:policy/logic/…/engine)   ⑧ 橋覆蓋(四系 × accel/net)
  ④ VCGC 流程與冊(流程 · 衝突 · SSOT 連動 · 資料庫)     ⑨ 全景治理類別(報/修/免 × 件數)
  ⑤ DB 面板摘要(讀 DBM_PANEL_latest.json summary)       ⑩ 待辦(所有非綠列 → 修法,依嚴重度排)

政策附冊 VIA_Policy_PSCommandGate(PSGATE-1)同步進來:總判第一列「⓪ 政策 · VCGC 流程」—— 附冊在且正本 sha 相符、
側車記到實測第一步 VCGC 的「[流程] 政策過」才算過;沒經 VCGC 流程 = 總判 RED(PowerShell 指令一定要先從 VCGC 跑過流程)。
只讀不寫庫:鏈跑器與 DB 面板的結論讀它們自己落的 JSON(正主各自判,本支不另判 L05);VCGC / 橋 / 全景讀 PS 側車裡該步的原文行。
rich 缺 = 純文字同十張(寬字算 2 格),照實標明降級,不安裝。輸出:VIA_Reports/sweep/SWEEP_REPORT_latest.html / .txt
+ SWEEP_PASTE_latest.txt(貼回包:總判 + 待辦 + 各鏈 tally)。

用法:
  python CGC_MDL229_SweepReport_v0100.py render --side <SWEEP_SIDE_latest.json> [--width N] [--plain] [--rows N]
  python CGC_MDL229_SweepReport_v0100.py --selftest
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

import ast
import io
import json
import re
import sys
import tempfile
import unicodedata
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = VIA / "VIA_Reports"
OUT = REPORTS / "sweep"
VDF_CHAIN = REPORTS / "vdf_chain" / "VDFCHAIN_latest.json"
VRN_CHAIN = REPORTS / "vrn_chain" / "VRNCHAIN_latest.json"
DB_PANEL = REPORTS / "dbmanager" / "DBM_PANEL_latest.json"
REPORT_HTML, REPORT_TXT, PASTE_TXT = "SWEEP_REPORT_latest.html", "SWEEP_REPORT_latest.txt", "SWEEP_PASTE_latest.txt"
ENGINE_TAG = "CGC_MDL229_SweepReport v" + Path(__file__).stem.rsplit("_v", 1)[-1]
SEV = {"RED": 0, "ABSENT": 1, "HIGH": 1, "NODATA": 2, "GATED": 3, "AMBER": 3, "MED": 3, "STALE": 3, "YELLOW": 3,
       "SKIP": 4, "LOW": 4, "INFO": 5, "GREEN": 6, "OK": 6}
STYLE = {"GREEN": "green", "OK": "green", "AMBER": "yellow", "YELLOW": "yellow", "STALE": "yellow", "GATED": "cyan",
         "NODATA": "dark_orange", "RED": "bold red", "ABSENT": "red", "HIGH": "bold red", "MED": "yellow", "SKIP": "dim"}
LAMPS = ("policy", "logic", "factor", "param", "engine", "bridge", "tool", "handover", "records", "ssot")


def _load(p) -> dict | None:
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, TypeError):
        return None


def _worst(states) -> str:
    got = [s for s in states if s]
    return min(got, key=lambda s: SEV.get(s, 5)) if got else "NODATA"


def policy_card(folder: Path = HERE) -> dict:
    """PSGATE-1 附冊(尾版):在 · ACTIVE · 釘的正本 sha 與正本相符(只差 CRLF 行尾 = AMBER 並講 Z231)。"""
    import hashlib
    hits = sorted(folder.glob("VIA_Policy_PSCommandGate_v*.json"))
    if not hits:
        return {"state": "ABSENT", "id": None, "file": None, "why": "政策附冊 VIA_Policy_PSCommandGate 不在(先 git pull)"}
    pol = _load(hits[-1]) or {}
    try:
        raw = (folder / str(pol.get("book") or "")).read_bytes()
    except OSError:
        return {"state": "RED", "id": pol.get("id"), "file": hits[-1].name, "why": "附冊指的正本讀不到"}
    pin = pol.get("book_sha256_16")
    sha = hashlib.sha256(raw).hexdigest()[:16]
    if sha == pin and pol.get("book_edited") is False and pol.get("status") == "ACTIVE":
        return {"state": "GREEN", "id": pol.get("id"), "file": hits[-1].name, "why": "附冊在 · 正本 sha 相符"}
    if hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()[:16] == pin:
        return {"state": "AMBER", "id": pol.get("id"), "file": hits[-1].name, "why": "正本只差 CRLF 行尾(Z231;跑 DB 面板 v0101+ 會換回)"}
    return {"state": "RED", "id": pol.get("id"), "file": hits[-1].name, "why": f"正本 sha {sha} ≠ 附冊所釘 {pin}:停,請 via 審核"}


def _step(side: dict, sid: str) -> dict:
    return next((s for s in side.get("steps") or [] if s.get("id") == sid), {})


# ---------------------------------------------------------------- 各步 → 結構化列
def vcgc_lamps(lines: list) -> list:
    """VCGC status 的「X 系統管理 STATE:燈 {...}」→ [{system, state, lamps{}}]。"""
    out = []
    for ln in lines:
        m = re.search(r"(VDF|VRN|VAP|VCGC)\s*系統管理\s+(\S+?):燈\s*(\{[^}]*\})", ln)
        if not m:
            continue
        try:
            lamps = ast.literal_eval(m.group(3))
        except (ValueError, SyntaxError):
            lamps = {}
        out.append({"system": m.group(1), "state": m.group(2).split("/")[0], "lamps": lamps})
    return out


def vcgc_flow(lines: list) -> list:
    keys = (("[流程]", "流程"), ("[衝突] L", "衝突律"), ("SSOT 連動", "SSOT 連動"), ("資料庫:", "資料庫"), ("多矩陣", "多矩陣"),
            ("[政策] 第二步", "政策"))
    rows = []
    for needle, name in keys:
        ln = next((x for x in lines if needle in x), None)
        if ln is None:
            continue
        st = ("GREEN" if ("政策過" in ln or "OK" in ln and "RED" not in ln) else
              "YELLOW" if "YELLOW" in ln else "ABSENT" if "ABSENT" in ln else "INFO")
        rows.append([name, st, ln.strip()[:160]])
    return rows


def bridge_rows(lines: list) -> list:
    ln = next((x for x in lines if "四系總表" in x), "")
    rows = []
    for sysk, cov, pct in re.findall(r"(\w+/\w+)\s+(\d+/\d+)\s+\(([\d.]+)%\)", ln):
        rows.append([sysk, cov, pct + "%", "GREEN" if float(pct) >= 100.0 else "AMBER"])
    plans = [x.strip()[:150] for x in lines if x.strip().startswith("PLAN")]
    for p in plans[:10]:
        rows.append(["計畫", p, "", "AMBER"])
    return rows


def panorama_rows(lines: list) -> list:
    rows = []
    head = next((x for x in lines if "全景掃描" in x), "")
    for kind, cls, n, desc in re.findall(r"\[(報|修|免)\]\s+(\w+)\s+(\d+)\s+·\s+(.+)", "\n".join(lines)):
        rows.append([cls, kind, int(n), desc.strip()[:110]])
    if head:
        rows.insert(0, ["合計", "—", int((re.search(r"(\d+)\s*問題", head) or [0, 0])[1]), head.strip()[:110]])
    return rows


def chain_rows(rep: dict | None, layer_key: str) -> tuple:
    """鏈跑器 JSON → (tally, 非綠列, 綠列數)。只讀正主落的結論。"""
    if not rep:
        return {}, [], 0
    rows, green = [], 0
    for s in rep.get("stages") or []:
        st = str(s.get("state") or "")
        if st == "GREEN":
            green += 1
            continue
        rows.append([st, str(s.get(layer_key) or s.get("id") or "—"), str(s.get("name") or ""),
                     str(s.get("detail") or "")[:150], str(s.get("fix") or "")[:120]])
    rows.sort(key=lambda r: (SEV.get(r[0], 5), r[1]))
    return rep.get("tally") or {}, rows, green


# ---------------------------------------------------------------- 十張矩陣
def build(side: dict, vdf: dict | None = None, vrn: dict | None = None, db: dict | None = None, limit: int | None = None) -> dict:
    vdf = _load(VDF_CHAIN) if vdf is None else vdf
    vrn = _load(VRN_CHAIN) if vrn is None else vrn
    db = _load(DB_PANEL) if db is None else db
    s1, s2, s3 = _step(side, "vcgc"), _step(side, "vdf_chain"), _step(side, "vrn_chain")
    s4, s5, s6 = _step(side, "bridge"), _step(side, "panorama"), _step(side, "db_panel")
    lamps = vcgc_lamps(s1.get("lines") or [])
    vt, vrows, vgreen = chain_rows(vdf, "id")
    rt, rrows, rgreen = chain_rows(vrn, "layer")
    br = bridge_rows(s4.get("lines") or [])
    pr = panorama_rows(s5.get("lines") or [])
    dbs = (db or {}).get("summary") or []

    def fresh(rep, step):
        """鏈 JSON 是不是這一次跑出來的(side 有記開跑時間就比;沒記就照實說不確定)。"""
        t0, gen = step.get("started_utc"), (rep or {}).get("generated")
        if not rep:
            return "ABSENT"
        if not (t0 and gen):
            return "未比對"
        return "本次" if str(gen)[:19].replace("T", " ") >= str(t0)[:19].replace("T", " ") else "舊的(本次沒寫)"

    kpi = []
    pol = policy_card()
    flow = side.get("flow") or {}
    flow_ok = bool(flow.get("ok"))
    kpi.append(["⓪ 政策 · VCGC 流程", "RED" if not flow_ok else pol["state"], "—", "—",
                f"{pol.get('id') or '—'} {pol['why']} · 流程 {'已過:' + str(flow.get('line', ''))[:60] if flow_ok else '沒經 VCGC 流程(PSGATE-1:PS 指令要先從 VCGC 跑過流程)'}"])

    def k(name, step, state, point):
        if step.get("skipped"):
            state, point = "SKIP", "本次略過"
        elif step and step.get("missing"):
            state, point = "ABSENT", "尾版不在"
        kpi.append([name, state, "—" if step.get("rc") is None else str(step.get("rc")),
                    "—" if step.get("sec") is None else f"{step.get('sec')}s", point])

    k("① VCGC 入口", s1, _worst([l["state"] for l in lamps] + (["GREEN"] if any("政策過" in x for x in s1.get("lines") or []) else [])),
      " · ".join(f"{l['system']} {l['state']}" for l in lamps) or "—")
    k("② VDF 鏈", s2, (vdf or {}).get("rc_name") or "ABSENT", f"{_fmt(vt)} · JSON {fresh(vdf, s2)}")
    k("③ VRN 鏈", s3, (vrn or {}).get("rc_name") or "ABSENT", f"{_fmt(rt)} · JSON {fresh(vrn, s3)}")
    k("④ 橋掃(乾跑)", s4, _worst([r[3] for r in br]) if br else "NODATA", " · ".join(f"{r[0]} {r[2]}" for r in br if r[0] != "計畫") or "—")
    k("⑤ 全景", s5, "INFO" if pr else "NODATA", (pr[0][3] if pr else "—"))
    k("⑥ DB 面板", s6, (db or {}).get("verdict") or "NODATA", " · ".join(f"{d.get('section')} {d.get('state')}" for d in dbs[:6]) or "—")
    verdict = _worst([r[1] for r in kpi if r[1] not in ("INFO", "SKIP")])

    acc = side.get("accel") or {}
    accel = [[a, str(b)] for a, b in acc.items()] or [["加速器", "PowerShell 側車沒給"]]
    lamp_rows = [[l["system"], l["state"]] + [str(l["lamps"].get(x, "—")) for x in LAMPS] for l in lamps]
    todo = []
    for r in vrows:
        todo.append([r[0], "VDF 鏈", f"{r[1]} {r[2]}", r[3][:90], r[4] or "單跑該站 --selftest 看根因"])
    for r in rrows:
        todo.append([r[0], "VRN 鏈", f"{r[1]} {r[2]}", r[3][:90], r[4] or "單跑該支 --selftest 看根因"])
    for l in lamps:
        for x in LAMPS:
            v = str(l["lamps"].get(x, ""))
            if v and v not in ("GREEN", "—"):
                todo.append([v, "VCGC 燈", f"{l['system']} · {x}", "子系統燈非綠", "看上面對應鏈 / 交接"])
    for r in br:
        if r[3] != "GREEN":
            todo.append(["AMBER", "橋", r[0], r[1][:90], "via-bridge-sweep --subsystems --apply(v0108 起不碰鎖冊與版史)"])
    if not flow_ok:
        todo.append(["RED", "政策", "PSGATE-1", "這次實測沒有記到 VCGC 流程已過", "從 VCGC 進:先 status 讀流程(政策過 · 子系統已對齊)再跑"])
    if pol["state"] != "GREEN":
        todo.append([pol["state"], "政策", str(pol.get("file") or "PSGATE"), pol["why"], "git pull;正本 sha 不符就停,請 via 審核"])
    for d in dbs:
        if d.get("state") not in ("GREEN", "OK", "INFO", None):
            todo.append([d.get("state"), "DB 面板", d.get("section"), str(d.get("headline"))[:90], "看 DBM 報告 ⑩ 錯誤矩陣"])
    todo.sort(key=lambda r: (SEV.get(str(r[0]), 5), r[1]))

    def cap(rows, n=None):
        n = n or limit
        return rows if not n or len(rows) <= n else rows[:n] + [[f"… 另 {len(rows) - n} 列(全表在 JSON / log)"] + [""] * (len(rows[0]) - 1)]

    sections = [
        ("① 總判 KPI", ["步驟", "狀態", "rc", "秒", "重點"], kpi, 1),
        ("② 加速器(Celeritas PS7 · 模板助手)", ["項目", "值"], accel, None),
        ("③ VCGC 子系統燈", ["系統", "總燈"] + list(LAMPS), lamp_rows, 1),
        ("④ VCGC 流程與冊", ["項目", "狀態", "原文"], vcgc_flow(s1.get("lines") or []), 1),
        ("⑤ DB 面板摘要", ["區", "狀態", "重點"], [[d.get("section"), d.get("state"), str(d.get("headline"))[:120]] for d in dbs], 1),
        (f"⑥ VDF 鏈跑器(非綠 {len(vrows)} · 綠 {vgreen})", ["狀態", "站", "名稱", "細節", "修法"], cap(vrows), 0),
        (f"⑦ VRN 鏈跑器(非綠 {len(rrows)} · 綠 {rgreen})", ["狀態", "層", "節點", "細節", "修法"], cap(rrows), 0),
        ("⑧ 橋覆蓋(乾跑)", ["系/橋", "覆蓋", "%", "狀態"], br, 3),
        ("⑨ 全景治理類別", ["類", "處置", "件數", "說明"], pr, None),
        (f"⑩ 待辦({len(todo)} 列;依嚴重度)", ["狀態", "來源", "項目", "說明", "下一步"], cap(todo), 0),
    ]
    sections = [(t, c, [[_cell(x) for x in r] for r in rows], s) for t, c, rows, s in sections]
    return {"engine": ENGINE_TAG, "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "verdict": verdict,
            "head": side.get("head", ""), "sections": sections, "todo": todo, "kpi": kpi,
            "tallies": {"vdf": vt, "vrn": rt}}


def _fmt(t: dict) -> str:
    return " · ".join(f"{a} {b}" for a, b in (t or {}).items() if b) or "—"


def _cell(v) -> str:
    if v is None or v == "":
        return "—"
    if isinstance(v, int):
        return f"{v:,}"
    return str(v).replace("\n", " ")


def _w(s: str) -> int:
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in s)


def _fit(s: str, n: int) -> str:
    if _w(s) <= n:
        return s + " " * (n - _w(s))
    out = ""
    for ch in s:
        if _w(out + ch) > n - 1:
            break
        out += ch
    return out + "…" + " " * (n - 1 - _w(out))


def plain(sections: list, width: int = 160, title: str = "") -> str:
    lines = [title, "(rich 缺席或 --plain:純文字;同樣十張矩陣)"] if title else []
    for t, cols, rows, _st in sections:
        lines += ["", f"━━ {t} ━━"]
        if not rows:
            lines.append("  (無)")
            continue
        n = len(cols)
        budget = max(n * 5, width - 2 - 3 * (n - 1))
        widths = [max([_w(c)] + [_w(r[i]) for r in rows if i < len(r)]) for i, c in enumerate(cols)]
        while sum(widths) > budget and max(widths) > 5:
            j = widths.index(max(widths))
            widths[j] -= 2
        lines.append("  " + " │ ".join(_fit(c, widths[i]) for i, c in enumerate(cols)))
        lines.append("  " + "─┼─".join("─" * x for x in widths))
        lines += ["  " + " │ ".join(_fit(r[i] if i < len(r) else "", widths[i]) for i in range(n)) for r in rows]
    return "\n".join(lines)


def paste(rep: dict) -> str:
    """貼回包:總判 + 各鏈 tally + 待辦前 20 列(對話框一次 Ctrl+V)。"""
    o = [f"### VIA 全景實測貼回包 · {rep['engine']} · {rep['ts']} · HEAD {rep['head']}", f"總判 {rep['verdict']}", ""]
    o += [f"  {r[0]:14s} {r[1]:7s} rc {r[2]:>3s} {r[3]:>7s}  {r[4][:120]}" for r in rep["kpi"]]
    o += ["", f"待辦 {len(rep['todo'])} 列(前 20)"]
    o += [f"  {str(r[0]):7s} {r[1]:6s} {str(r[2])[:44]:44s} {str(r[3])[:70]} → {str(r[4])[:60]}" for r in rep["todo"][:20]]
    return "\n".join(o) + "\n"


def render(side: dict, width: int = 160, use_plain: bool = False, out: Path = OUT, echo: bool = True,
           limit: int | None = None, **kw) -> dict:
    rep = build(side, limit=limit, **kw)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    title = f"VIA 全景實測詳細摘要矩陣 · {rep['verdict']} · {rep['ts']} · HEAD {rep['head']}"
    engine = "plain"
    txt = plain(rep["sections"], width, title)
    if not use_plain:
        try:
            from rich import box
            from rich.console import Console
            from rich.table import Table
            from rich.text import Text
            con = Console(record=True, width=max(100, int(width)), force_terminal=echo, color_system="truecolor" if echo else None,
                          legacy_windows=False, file=(sys.stdout if echo else io.StringIO()), soft_wrap=False)
            con.rule(f"[bold]{title}")
            for t, cols, rows, st in rep["sections"]:
                tb = Table(title=t, title_justify="left", title_style="bold cyan", box=box.SIMPLE_HEAVY, header_style="bold", pad_edge=False)
                for c in cols:
                    tb.add_column(c, overflow="fold")
                for r in rows or [["(無)"] + [""] * (len(cols) - 1)]:
                    cells = list(r) + [""] * (len(cols) - len(r))
                    if st is not None and st < len(cells) and STYLE.get(cells[st]):
                        cells[st] = Text(cells[st], style=STYLE[cells[st]])
                    tb.add_row(*cells)
                con.print(tb)
            con.save_html(str(out / REPORT_HTML), inline_styles=True)
            engine = "rich"
        except ImportError:
            engine = "plain"
    if engine == "plain":
        if echo:
            print(txt)
        (out / REPORT_HTML).write_text("<!doctype html><meta charset='utf-8'><title>VIA Sweep Report</title><pre>"
                                       + txt.replace("&", "&amp;").replace("<", "&lt;") + "</pre>", encoding="utf-8")
    (out / REPORT_TXT).write_text(txt, encoding="utf-8")
    (out / PASTE_TXT).write_text(paste(rep), encoding="utf-8")
    return {"engine": engine, "verdict": rep["verdict"], "todo": len(rep["todo"]),
            "paths": {k: str(out / v) for k, v in (("html", REPORT_HTML), ("txt", REPORT_TXT), ("paste", PASTE_TXT))}}


# ---------------------------------------------------------------- 自測(沙盒;不讀真 VIA_Reports、不寫)
def selftest() -> int:
    print(f"=== {ENGINE_TAG} · 自測(沙盒)===")
    res = []

    def chk(name, ok, note=""):
        res.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" ({note})" if note else ""))

    side = {"head": "abc123 test", "flow": {"ok": True, "line": "[流程] 政策過 · 子系統已對齊 · 才執行"},
            "accel": {"加速器": "套對 v1141 · 已套", "模板助手": "Invoke-VIACeleritasScoped 已套"},
            "steps": [
                {"id": "vcgc", "rc": 0, "sec": 3.1, "lines": [
                    "[流程] 政策過 · 子系統已對齊 · 才執行", "  [衝突] L08 L12",
                    "  VRN 系統管理 STALE/NODATA:燈 {'policy': 'GREEN', 'engine': 'RED', 'handover': 'STALE'} · 連結 237",
                    "  VDF 系統管理 GREEN:燈 {'policy': 'GREEN', 'engine': 'GATED', 'bridge': 'GREEN'} · 連結 171",
                    "  SSOT 連動 YELLOW:YELLOW 7 · GREEN 5"]},
                {"id": "vdf_chain", "rc": 4, "sec": 20.0, "started_utc": "2026-09-28 05:00:00", "lines": []},
                {"id": "vrn_chain", "rc": 1, "sec": 40.0, "started_utc": "2026-09-28 05:00:00", "lines": []},
                {"id": "bridge", "rc": 0, "sec": 5.0, "lines": [
                    "[橋掃] 四系總表 VDF/accel 128/128 (100.0%) · VDF/net 127/128 (99.2%) · VRN/accel 146/146 (100.0%)",
                    "    PLAN     functional modules/VDF/engine/X_v0100.py · 插入於字元 1"]},
                {"id": "panorama", "rc": 0, "sec": 17.5, "lines": [
                    "=== 全景掃描 · 1679 檔 · 289 問題 · 17.5s ===", "  [報] PINVER     172 · 釘死版號(違尾版律 L54)",
                    "  [修] ACCEL       32 · 加速器橋缺席"]},
                {"id": "db_panel", "skipped": True}]}
    vdf = {"generated": "2026-09-28 05:19:24Z", "rc_name": "GATED", "tally": {"GREEN": 6, "GATED": 1, "NODATA": 3},
           "stages": [{"id": "0b", "name": "網路工具掛載", "state": "GATED", "detail": "等同意閘", "fix": "操作員開 VIA_NET_CONSENT"},
                      {"id": "2", "name": "邏輯", "state": "GREEN", "detail": "10/10", "fix": ""}]}
    vrn = {"generated": "2026-09-28 04:00:00Z", "rc_name": "RED", "tally": {"GREEN": 32, "RED": 2},
           "stages": [{"layer": "L2", "name": "VRN_ENG067_MindMapSSOT", "state": "RED", "detail": "① 依賴鏈", "fix": ""},
                      {"layer": "L2", "name": "VRN_ENG072_FirstPageText", "state": "ABSENT", "detail": "缺 pdfplumber", "fix": "裝進家族境=你的手"}]}
    rep = build(side, vdf=vdf, vrn=vrn, db={})
    names = [t for t, *_ in rep["sections"]]
    kpi = {r[0]: r for r in rep["kpi"]}
    chk("① 十張矩陣都在(總判 · 加速器 · VCGC 燈 · 流程 · DB · 兩鏈 · 橋 · 全景 · 待辦)", len(names) == 10 and names[0].startswith("①") and names[9].startswith("⑩"), str(len(names)))
    chk("② 總判取最差:VRN 鏈 RED → 全體 RED;略過的步驟標 SKIP 不算進總判", rep["verdict"] == "RED" and kpi["⑥ DB 面板"][1] == "SKIP")
    chk("③ 鏈 JSON 新舊照實比:VDF 本次寫的 = 本次 · VRN 比開跑早 = 舊的(本次沒寫)",
        "本次" in kpi["② VDF 鏈"][4] and "舊的" in kpi["③ VRN 鏈"][4], f"{kpi['② VDF 鏈'][4]} | {kpi['③ VRN 鏈'][4]}")
    pc = policy_card()
    chk("⑩ PSGATE-1 附冊在、正本 sha 相符 → 總判第一列 ⓪ 政策 · VCGC 流程 GREEN(流程已過)",
        pc["state"] == "GREEN" and pc["id"] == "PSGATE-1" and rep["kpi"][0][0].startswith("⓪") and rep["kpi"][0][1] == "GREEN", pc["why"])
    nof = build(dict(side, flow={}), vdf=vdf, vrn=vrn, db={})
    chk("⑪ 沒經 VCGC 流程 = ⓪ 列 RED、總判 RED、待辦第一列就是它(PS 指令要先從 VCGC 跑過流程)",
        nof["kpi"][0][1] == "RED" and nof["verdict"] == "RED" and any(r[2] == "PSGATE-1" for r in nof["todo"][:3]))
    lamps = vcgc_lamps(side["steps"][0]["lines"])
    chk("④ VCGC 燈解析(系統 × 燈)· VRN engine RED · VDF engine GATED", {l["system"]: l["lamps"].get("engine") for l in lamps} == {"VRN": "RED", "VDF": "GATED"})
    br = bridge_rows(side["steps"][3]["lines"])
    chk("⑤ 橋:四系總表逐格 + 計畫列;未滿 100% = AMBER", any(r[0] == "VDF/net" and r[3] == "AMBER" for r in br) and any(r[0] == "計畫" for r in br))
    pr = panorama_rows(side["steps"][4]["lines"])
    chk("⑥ 全景:合計 289 + 各類件數", pr[0][2] == 289 and any(r[0] == "PINVER" and r[2] == 172 for r in pr))
    todo_src = [r[1] for r in rep["todo"]]
    chk("⑦ 待辦收齊非綠:VRN RED 在最前、修法照鏈跑器給的(沒給就「單跑 --selftest」)· 橋未滿 · VCGC 燈非綠",
        rep["todo"][0][0] == "RED" and "VRN 鏈" in todo_src and "橋" in todo_src and "VCGC 燈" in todo_src
        and any("裝進家族境" in r[4] for r in rep["todo"]), f"{len(rep['todo'])} 列")
    with tempfile.TemporaryDirectory() as td:
        buf = io.StringIO()
        import contextlib
        with contextlib.redirect_stdout(buf):
            r = render(side, width=140, use_plain=True, out=Path(td), vdf=vdf, vrn=vrn, db={}, limit=5)
        txt = (Path(td) / REPORT_TXT).read_text(encoding="utf-8")
        pst = (Path(td) / PASTE_TXT).read_text(encoding="utf-8")
        chk("⑧ 純文字降級:十張都印、存 .txt/.html/貼回包;每行不超過指定寬", r["engine"] == "plain" and "⑩ 待辦" in txt
            and "總判 RED" in pst and max(_w(x) for x in txt.splitlines()) <= 142 and (Path(td) / REPORT_HTML).exists())
        try:
            import rich  # noqa: F401
            with contextlib.redirect_stdout(io.StringIO()):
                r2 = render(side, width=150, out=Path(td) / "r", echo=False, vdf=vdf, vrn=vrn, db={})
            chk("⑨ rich:十張矩陣存 HTML(inline 樣式)· echo=False 零輸出", r2["engine"] == "rich"
                and "⑩ 待辦" in (Path(td) / "r" / REPORT_HTML).read_text(encoding="utf-8"))
        except ImportError:
            print("  [SKIP] ⑨ 本環境沒有 rich:rich 版驗不了(誠實 SKIP;純文字已驗)")
    ok = sum(res)
    print(f"  [計] {len(res)} 檢 OK {ok} · FAIL {len(res) - ok}")
    return 0 if ok == len(res) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a or (a and a[0] == "selftest"):
        return selftest()
    if not a or a[0] != "render":
        print(__doc__)
        return 0
    side_p = Path(a[a.index("--side") + 1]) if "--side" in a and a.index("--side") + 1 < len(a) else OUT / "SWEEP_SIDE_latest.json"
    side = _load(side_p)
    if side is None:
        print(f"[SweepReport] 側車不在或讀不動:{side_p}")
        return 2
    width = int(a[a.index("--width") + 1]) if "--width" in a and a.index("--width") + 1 < len(a) else 160
    limit = int(a[a.index("--rows") + 1]) if "--rows" in a and a.index("--rows") + 1 < len(a) else None
    r = render(side, width=width, use_plain="--plain" in a, limit=limit)
    print(f"[SweepReport] {r['engine']} · 總判 {r['verdict']} · 待辦 {r['todo']} · HTML {r['paths']['html']} · 貼回 {r['paths']['paste']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
