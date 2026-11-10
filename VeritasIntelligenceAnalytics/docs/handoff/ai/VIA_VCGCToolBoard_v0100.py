#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_VCGCToolBoard v0100 — VCGC 工具看板:燈號放最前面,工具分類放後面(全部只讀 · 零網路 · 零寫冊)。

操作員 2026-11-10:「檢查備份 · 讀取備份 · 顯示 VCGC 有些功能工具 · 分類顯示 · 狀態燈號放一開始」。
本引擎不跑任何站、不發任何燈:只把 VCGC 自己落檔的收據攤開成一張看板——
  第一段 燈號條(worst 總燈 + 每份收據一盞):備份檢查 · 全功能串測 · 省 Token · 流程閘 · 交接快照 · 五系統互監 · 工具鎖
  第二段 工具分類(盤點冊站 × 最後一次串測燈):V 動詞 · S 席位 · E 引擎 · I 整合 · L / L1 律 · P PowerShell · QG · SSOT · C 交接案
  第三段 卡上的工具(鎖版席位 · 省 Token 七工具 · 必用 13 步 · 門 · 禁止)
律:黃不是綠 · 沒收據 = GRAY · 沒跑過的站 = NOT_RUN(不是綠)· 收據超過 48 小時 = 過期(總燈至少黃)。
輸出:VIA_Reports/vcgc/TOOLBOARD_latest.{json,md,html} + toolboard_ledger.jsonl(只增)。
用法:run [--root <VIA 根>] [--no-write] [--open] · --selftest
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import glob
import html
import json
import os
import re
import sys
import tempfile
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0100"
ENGINE = "VIA_VCGCToolBoard " + VERSION
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[2] if HERE.name == "ai" else HERE
STALE_HOURS = 48.0
ORDER = {"GREEN": 0, "YELLOW": 1, "NOT_RUN": 2, "GRAY": 2, "RED": 3}
CATEGORIES = [  # (prefix, 名稱, 一句話)
    ("V", "VCGC 動詞", "主控台指令(token · handoff · test · ssot · 編號 …)"),
    ("S", "席位", "鎖版席位正主自測(管理器 · NLP)"),
    ("E", "VCGC 引擎", "操作台 · 環境 · 掃描 · 橋 · 編號稽核 · MCP"),
    ("I", "整合 / 派送", "項鏈派送計畫(PLAN)"),
    ("L", "律 / 政策", "舊套律引擎(policy · talib · ledger · matrix …)"),
    ("L1", "律 L1", "本地工具整合契約 · 套件資源盤點"),
    ("P", "PowerShell / 平台", "PS 入口與啟動器(語法 + 串測;容器無 pwsh = 黃)"),
    ("QG", "QuantGuard", "量化閘引擎本輪"),
    ("SSOT", "SSOT", "中央資產規劃 / 投影"),
    ("C", "交接案 / 自測", "各家族尾版 --selftest 與交接案(只讀 / 乾跑)"),
]
SOURCES = {
    "backup": "VIA_Reports/backup/CHECK_latest.json",
    "manifest": "docs/handoff/backup/BACKUP_MANIFEST_latest.json",
    "test": "VIA_Reports/vcgc/TEST_latest.json",
    "state": "VIA_Reports/vcgc/TEST_STATE_v*.json",
    "token": "docs/handoff/evidence/token.json",
    "gate": "VIA_Reports/gate/GATE_latest.json",
    "handoff": "docs/handoff/HANDOFF_latest.json",
    "mutual": "VIA_Reports/mutual/MUTUAL_latest.json",
    "lock": "supportive modules/registry/VIA_ToolVersion_Lock_v0100.json",
    "inventory": "supportive modules/registry/VIA_VCGC_FunctionInventory_SSOT_v*.json",
    "card": "supportive modules/registry/VIA_AI_FunctionCard_SSOT_v*.json",
    "mcp": "supportive modules/registry/CGC_MDL279_MCPServer_v*.py",
}
OUT_DIR = "VIA_Reports/vcgc"


# ───────────────────────── 讀檔(只讀 · 缺 = None) ─────────────────────────
def tail(via: Path, pattern: str) -> Path | None:
    hits = sorted(glob.glob(str(via / pattern)))
    return Path(hits[-1]) if hits else None


def load(via: Path, key: str) -> tuple[dict | None, str]:
    pat = SOURCES[key]
    p = tail(via, pat) if "*" in pat else (via / pat)
    if p is None or not p.exists():
        return None, pat
    try:
        return json.loads(p.read_text(encoding="utf-8")), str(p.relative_to(via))
    except Exception as e:  # noqa: BLE001 — 壞檔照實 GRAY,不炸
        return {"_error": str(e)[:160]}, str(p.relative_to(via))


def parse_at(v) -> datetime | None:
    if not v:
        return None
    s = str(v).strip().replace("Z", "+00:00")
    try:
        d = datetime.fromisoformat(s)
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def age_hours(v, now: datetime) -> float | None:
    d = parse_at(v)
    return round((now - d).total_seconds() / 3600.0, 2) if d else None


def seat_path(via: Path, rel: str) -> Path:
    """鎖冊的 path 是倉根相對(VeritasIntelligenceAnalytics/…);先試 VIA 根,再試倉根。"""
    p = via / rel
    return p if p.exists() else (via.parent / rel)


def norm(lamp) -> str:
    s = str(lamp or "").upper()
    if s in ("GREEN", "PASS", "OK"):
        return "GREEN"
    if s in ("YELLOW", "WARN"):
        return "YELLOW"
    if s in ("RED", "FAIL"):
        return "RED"
    if s in ("NOT_RUN", "NOT_OBSERVED"):
        return "NOT_RUN"
    return "GRAY"


def worst(lamps) -> str:
    lamps = [l for l in lamps if l]
    return max(lamps, key=lambda l: ORDER.get(l, 2)) if lamps else "GRAY"


# ───────────────────────── 第一段:燈號條 ─────────────────────────
def lamp_row(key: str, title: str, lamp: str, at, now: datetime, note: str, src: str, present: bool) -> dict:
    age = age_hours(at, now)
    stale = bool(present and age is not None and age > STALE_HOURS)
    return {"key": key, "title": title, "lamp": lamp if present else "GRAY", "at": at, "age_hours": age,
            "stale": stale, "note": note if present else "沒有收據(還沒跑)", "source": src}


def lamps(via: Path, now: datetime) -> list[dict]:
    rows = []
    b, bs = load(via, "backup")
    m, _ = load(via, "manifest")
    ok = b is not None and "_error" not in b
    note = ""
    if ok:
        f = b.get("files") or {}
        note = "%s · 備份 %s · zip %s · 檔同 %s 變 %s 缺 %s" % (b.get("meaning", ""), str(b.get("backup_at", ""))[:16], b.get("zip_state", "?"),
                                                           f.get("same", "?"), f.get("changed", "?"), f.get("missing", "?"))
        if m and "systems" in m:
            note += " · 包 %d 系統 %s 檔" % (len(m["systems"]), m.get("total_files", "?"))
    rows.append(lamp_row("backup", "備份檢查", norm(ok and b.get("lamp")), ok and b.get("at"), now, note, bs, ok))

    t, ts = load(via, "test")
    ok = t is not None and "_error" not in t
    note = ""
    if ok:
        c = t.get("counts") or {}
        note = "%s · 站 %d(綠 %s 黃 %s 紅 %s)· head %s · %ss" % (t.get("mode", ""), len(t.get("rows") or []), c.get("GREEN", 0), c.get("YELLOW", 0), c.get("RED", 0),
                                                          str(t.get("head", ""))[:7], t.get("secs", "?"))
    rows.append(lamp_row("test", "全功能串測", norm(ok and t.get("lamp")), ok and t.get("at"), now, note, ts, ok))

    # 省 Token:以最近一次串測的 V-token 站為主(= token 卡實跑);沒有才退到交接證據 token.json
    st, st_src = load(via, "state")
    vt = (st or {}).get("V-token") if isinstance(st, dict) else None
    k, ks = load(via, "token")
    ok_k = k is not None and "_error" not in k
    if vt:
        lamp = norm(vt.get("lamp"))
        note = "token 卡站 V-token rc %s · %s" % (vt.get("rc"), str(vt.get("last", ""))[:70])
        if ok_k:
            note += " · 交接證據 %s rc %s" % (str(k.get("completed_at", ""))[:10], k.get("rc"))
        rows.append(lamp_row("token", "省 Token 工具", lamp, vt.get("at"), now, note, st_src + " [V-token]", True))
    else:
        lamp = "GRAY"
        note = ""
        if ok_k:
            lamp = "GREEN" if (k.get("rc") == 0 and k.get("target_marker_seen")) else "RED"
            note = "交接證據 rc %s · 標記 %s · %s" % (k.get("rc"), k.get("target_marker_seen"), str(k.get("scope", ""))[:60])
        rows.append(lamp_row("token", "省 Token 工具", lamp, ok_k and k.get("completed_at"), now, note, ks, ok_k))

    g, gs = load(via, "gate")
    ok = g is not None and "_error" not in g
    note = ok and ("%s · blockers %d · %s" % (g.get("run", ""), len(g.get("blockers") or {}), str(g.get("engine", "")).split("_v")[-1][:6])) or ""
    rows.append(lamp_row("gate", "流程閘", norm(ok and g.get("verdict")), ok and g.get("at"), now, note, gs, ok))

    h, hs = load(via, "handoff")
    ok = h is not None and "_error" not in h
    note = ok and ("交接 %s · 驗收 closeout %s · pending %d" % (h.get("lamp"), h.get("closeout_lamp"), len(h.get("pending") or []))) or ""
    rows.append(lamp_row("handoff", "交接快照", norm(ok and h.get("lamp")), ok and h.get("at"), now, note, hs, ok))

    u, us = load(via, "mutual")
    ok = u is not None and "_error" not in u
    note = ok and (" · ".join("%s %s" % (s, v.get("lamp")) for s, v in (u.get("systems") or {}).items()) or "") or ""
    rows.append(lamp_row("mutual", "五系統互監(他系統自報 · 只看不代修)", norm(ok and u.get("lamp")), ok and u.get("at"), now, note, us, ok))

    L, Ls = load(via, "lock")
    ok = L is not None and "_error" not in L
    seats = [(kk, v) for kk, v in (L or {}).items() if isinstance(v, dict) and v.get("path")]
    lamp = "GREEN" if ok and seats and all(seat_path(via, s[1]["path"]).exists() for s in seats) else ("RED" if ok and seats else "GRAY")
    note = ok and ("席位 %d · 正主檔都在 %s" % (len(seats), "是" if lamp == "GREEN" else "否")) or ""
    rows.append(lamp_row("lock", "工具鎖版席位", lamp, None, now, note, Ls, ok))
    for r in rows:
        if r["key"] == "lock":
            r["stale"] = False
    return rows


def overall(rows: list[dict]) -> dict:
    own = [r for r in rows if r["key"] in ("backup", "test", "token", "gate", "handoff", "lock")]
    lamp = worst([r["lamp"] for r in own])
    stale = [r["key"] for r in own if r["stale"]]
    if stale and ORDER[lamp] < ORDER["YELLOW"]:
        lamp = "YELLOW"
    gray = [r["key"] for r in own if r["lamp"] == "GRAY"]
    meaning = "VCGC 自己的收據取最差" + (" · 過期(>%dh):%s" % (int(STALE_HOURS), " ".join(stale)) if stale else "") + (" · 缺收據:%s" % " ".join(gray) if gray else "")
    return {"lamp": lamp, "meaning": meaning, "rule": "黃不是綠 · 互監燈另列不併入(他系統自報)"}


# ───────────────────────── 第二段:工具分類 × 最後一次串測燈 ─────────────────────────
def categories(via: Path) -> dict:
    inv, inv_src = load(via, "inventory")
    st, st_src = load(via, "state")
    stations = (inv or {}).get("stations") or []
    state = st if isinstance(st, dict) else {}
    buckets = {p: [] for p, _, _ in CATEGORIES}
    other = []
    for s in stations:
        sid = s.get("id", "")
        pre = sid.split("-")[0]
        last = state.get(sid) or {}
        row = {"id": sid, "name": s.get("name", ""), "argv": " ".join(s.get("argv") or []) if s.get("argv") else "(%s)" % s.get("kind", "?"),
               "quick": bool(s.get("quick")), "lamp": norm(last.get("lamp")) if last else "NOT_RUN",
               "at": last.get("at"), "secs": last.get("secs"), "last": str(last.get("last", ""))[:140]}
        (buckets if pre in buckets else {pre: other}).setdefault(pre, other).append(row)
    out = []
    for pre, name, desc in CATEGORIES:
        rows = buckets[pre]
        cnt = {k: sum(1 for r in rows if r["lamp"] == k) for k in ("GREEN", "YELLOW", "RED", "NOT_RUN", "GRAY")}
        out.append({"prefix": pre, "name": name, "desc": desc, "count": len(rows), "lamps": cnt, "lamp": worst([r["lamp"] for r in rows]) if rows else "GRAY", "rows": rows})
    gone = sorted(set(state) - {s.get("id") for s in stations} - {k for k in state if k.startswith("upd:")})
    upd = sorted(k for k in state if k.startswith("upd:"))
    return {"inventory": inv_src, "inventory_version": (inv or {}).get("version"), "state": st_src, "stations": len(stations),
            "never_run": sum(1 for c in out for r in c["rows"] if r["lamp"] == "NOT_RUN"),
            "state_not_in_inventory": gone, "updated_tails_in_state": upd, "other": other, "categories": out}


# ───────────────────────── 第三段:卡上的工具 ─────────────────────────
def card_tools(via: Path) -> dict:
    L, _ = load(via, "lock")
    seats = []
    for k, v in (L or {}).items():
        if isinstance(v, dict) and v.get("path"):
            seats.append({"seat": k, "file": Path(v["path"]).name, "exists": seat_path(via, v["path"]).exists(), "activated_at": v.get("activated_at") or v.get("at")})
    c, c_src = load(via, "card")
    c = c or {}
    mcp = tail(via, SOURCES["mcp"])
    return {"seats": seats, "card": c_src, "card_version": c.get("version"),
            "token_tools": c.get("token_tools") or {}, "must_use": c.get("must_use") or [], "doors": c.get("doors") or [], "never": c.get("never") or [],
            "mcp_tail": mcp.name if mcp else None}


# ───────────────────────── 組裝 · 輸出 ─────────────────────────
def build(via: Path, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    rows = lamps(via, now)
    board = {"schema": "VIA-VCGC-TOOLBOARD/1.0", "engine": ENGINE, "at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "via_root": str(via),
             "overall": overall(rows), "lamps": rows, "tools": categories(via), "card": card_tools(via),
             "rule": "只讀收據 · 不跑站 · 不發燈;黃不是綠 · 沒收據 GRAY · 沒跑過 NOT_RUN · 超過 %dh 過期" % int(STALE_HOURS)}
    return board


def e(s) -> str:
    return html.escape(str(s if s is not None else ""))


def to_md(b: dict) -> str:
    L = ["# VCGC 工具看板 · %s · **%s**" % (b["at"], b["overall"]["lamp"]), "", b["overall"]["meaning"] + " · " + b["rule"], "",
         "## 1. 燈號(放最前面)", "", "| 燈 | 項 | 時間 | 幾小時前 | 說明 | 來源 |", "|---|---|---|---|---|---|"]
    for r in b["lamps"]:
        L.append("| **%s**%s | %s | %s | %s | %s | `%s` |" % (r["lamp"], "(過期)" if r["stale"] else "", r["title"], str(r["at"] or "")[:16], r["age_hours"] if r["age_hours"] is not None else "—", r["note"], r["source"]))
    t = b["tools"]
    L += ["", "## 2. 工具分類 × 最後一次串測燈(盤點冊 %s · %d 站 · 沒跑過 %d)" % (t.get("inventory_version"), t["stations"], t["never_run"]), "",
          "| 類 | 站數 | 綠 | 黃 | 紅 | 沒跑過 | 類燈 | 說明 |", "|---|---|---|---|---|---|---|---|"]
    for c in t["categories"]:
        L.append("| %s · %s | %d | %d | %d | %d | %d | **%s** | %s |" % (c["prefix"], c["name"], c["count"], c["lamps"]["GREEN"], c["lamps"]["YELLOW"], c["lamps"]["RED"], c["lamps"]["NOT_RUN"], c["lamp"], c["desc"]))
    for c in t["categories"]:
        if not c["rows"]:
            continue
        L += ["", "### %s · %s(%d 站)" % (c["prefix"], c["name"], c["count"]), "", "| 站 | 名稱 | 指令 | 燈 | 最後跑 | 秒 | 最後一行 |", "|---|---|---|---|---|---|---|"]
        for r in c["rows"]:
            L.append("| %s | %s | `%s` | %s | %s | %s | %s |" % (r["id"], r["name"][:60].replace("|", "/"), r["argv"][:70].replace("|", "/"), r["lamp"], str(r["at"] or "")[:16], r["secs"] if r["secs"] is not None else "", r["last"].replace("|", "/")[:80]))
    if t["state_not_in_inventory"]:
        L += ["", "狀態檔有、盤點冊已無的站(改名或撤站 · 只列不動):" + " · ".join(t["state_not_in_inventory"])]
    k = b["card"]
    L += ["", "## 3. 卡上的工具(%s · MCP 尾版 %s)" % (k.get("card_version"), k.get("mcp_tail")), "", "### 鎖版席位", "", "| 席位 | 現任 | 檔在 | 啟用時間 |", "|---|---|---|---|"]
    for s in k["seats"]:
        L.append("| %s | `%s` | %s | %s |" % (s["seat"], s["file"], "是" if s["exists"] else "否", str(s["activated_at"] or "")[:16]))
    L += ["", "### 省 Token 工具", ""] + ["- `%s`:%s" % (n, (v if isinstance(v, str) else json.dumps(v, ensure_ascii=False))[:120]) for n, v in k["token_tools"].items()]
    L += ["", "### AI 必用步", "", "| 步 | 指令 | 何時 | 做什麼 |", "|---|---|---|---|"]
    for m in k["must_use"]:
        L.append("| %s | `%s` | %s | %s |" % (m.get("step"), str(m.get("cmd", "")).replace("|", "/")[:90], m.get("when", ""), str(m.get("what", "")).replace("|", "/")[:90]))
    L += ["", "### 門", ""] + ["- `%s`:%s" % (d.get("verb"), str(d.get("what", ""))[:120]) for d in k["doors"]]
    L += ["", "### 禁止", ""] + ["- %s" % n for n in k["never"]]
    return "\n".join(L) + "\n"


CSS = """
:root{--bg:#f6f7f9;--fg:#1d2430;--mute:#5d6676;--line:#d9dee6;--card:#fff;--g:#1f9d55;--y:#d99a00;--r:#c62828;--n:#7a8290;--head:56px}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0f1318;--fg:#e6e9ee;--mute:#9aa3b2;--line:#273040;--card:#161c24;color-scheme:dark}}
:root[data-theme=dark]{--bg:#0f1318;--fg:#e6e9ee;--mute:#9aa3b2;--line:#273040;--card:#161c24;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:clamp(14px,.35vw + 13px,15.5px)/1.5 system-ui,-apple-system,"Segoe UI","Noto Sans TC",sans-serif}
header{position:sticky;top:0;z-index:5;height:var(--head);display:flex;align-items:center;gap:.8rem;padding:0 max(16px,env(safe-area-inset-left,0px)) 0 max(16px,env(safe-area-inset-right,0px));background:var(--card);border-bottom:1px solid var(--line)}
header h1{font-size:1.05rem;margin:0;font-weight:650}header .meta{color:var(--mute);font-size:.85rem;margin-left:auto}
main{padding:1rem max(16px,env(safe-area-inset-right,0px)) 2rem max(16px,env(safe-area-inset-left,0px));max-width:1400px;margin:0 auto}
.lamp{display:inline-block;min-width:4.6em;text-align:center;padding:.1em .55em;border-radius:999px;font-weight:650;font-size:.8rem;color:#fff;background:var(--n)}
.lamp.GREEN{background:var(--g)}.lamp.YELLOW{background:var(--y)}.lamp.RED{background:var(--r)}.lamp.GRAY,.lamp.NOT_RUN{background:var(--n)}.lamp.big{font-size:1.1rem;padding:.25em .9em}
.strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:.7rem;margin:.8rem 0 1.4rem}
.tile{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:.7rem .9rem;min-width:0}
.tile .t{font-weight:650;margin:.2rem 0}.tile .s{color:var(--mute);font-size:.82rem;overflow-wrap:anywhere}.tile.stale{border-color:var(--y)}
h2{font-size:1.1rem;margin:1.4rem 0 .5rem}h3{font-size:.98rem;margin:1rem 0 .4rem}
.cats{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:.7rem}
table{border-collapse:collapse;width:100%;font-size:.86rem}th,td{border-bottom:1px solid var(--line);padding:.3rem .45rem;text-align:left;vertical-align:top}th{color:var(--mute);font-weight:600}
.wrap{overflow-x:auto}code{font-size:.85em;background:rgba(127,127,127,.12);padding:.05em .3em;border-radius:4px}details{margin:.5rem 0}summary{cursor:pointer;font-weight:600}
.cnt{display:inline-flex;gap:.35rem;flex-wrap:wrap}.cnt span{font-size:.78rem;padding:.05em .5em;border-radius:999px;border:1px solid var(--line)}
@media(max-width:700px){.strip{grid-template-columns:1fr 1fr}.cats{grid-template-columns:1fr}:root{--head:48px}}
"""


def to_html(b: dict) -> str:
    o = b["overall"]
    H = ['<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">',
         "<title>VCGC 工具看板 · %s</title><style>%s</style></head><body>" % (e(b["at"]), CSS),
         '<header><span class="lamp big %s">%s</span><h1>VCGC 工具看板</h1><span class="meta">%s · %s</span></header><main>' % (e(o["lamp"]), e(o["lamp"]), e(b["at"]), e(ENGINE)),
         '<p style="color:var(--mute);margin:.2rem 0 .6rem">%s · %s</p>' % (e(o["meaning"]), e(b["rule"])),
         '<section id="lamps" class="strip">']
    for r in b["lamps"]:
        H.append('<div class="tile%s"><span class="lamp %s">%s</span>%s<div class="t">%s</div><div class="s">%s</div><div class="s">%s · %s</div></div>' % (
            " stale" if r["stale"] else "", e(r["lamp"]), e(r["lamp"]), ' <span class="s">過期</span>' if r["stale"] else "", e(r["title"]), e(r["note"]),
            e(str(r["at"] or "—")[:16]), ("%s 小時前" % r["age_hours"]) if r["age_hours"] is not None else "—"))
    t = b["tools"]
    H.append('</section><h2 id="tools">工具分類 × 最後一次串測燈 <span class="s" style="color:var(--mute);font-weight:400">盤點冊 %s · %d 站 · 沒跑過 %d</span></h2><div class="cats">' % (e(t.get("inventory_version")), t["stations"], t["never_run"]))
    for c in t["categories"]:
        H.append('<div class="tile"><span class="lamp %s">%s</span> <strong>%s · %s</strong> <span class="s">%d 站</span><div class="s">%s</div><div class="cnt">%s</div></div>' % (
            e(c["lamp"]), e(c["lamp"]), e(c["prefix"]), e(c["name"]), c["count"], e(c["desc"]),
            "".join('<span>%s %d</span>' % (k, c["lamps"][k]) for k in ("GREEN", "YELLOW", "RED", "NOT_RUN") if c["lamps"][k])))
    H.append("</div>")
    for c in t["categories"]:
        if not c["rows"]:
            continue
        H.append('<details%s><summary><span class="lamp %s">%s</span> %s · %s(%d 站)</summary><div class="wrap"><table><thead><tr><th>站</th><th>名稱</th><th>指令</th><th>燈</th><th>最後跑</th><th>秒</th><th>最後一行</th></tr></thead><tbody>' % (
            " open" if c["prefix"] in ("V", "E", "S") else "", e(c["lamp"]), e(c["lamp"]), e(c["prefix"]), e(c["name"]), c["count"]))
        for r in c["rows"]:
            H.append("<tr><td>%s</td><td>%s</td><td><code>%s</code></td><td><span class=\"lamp %s\">%s</span></td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                e(r["id"]), e(r["name"][:80]), e(r["argv"][:80]), e(r["lamp"]), e(r["lamp"]), e(str(r["at"] or "")[:16]), e("" if r["secs"] is None else r["secs"]), e(r["last"][:100])))
        H.append("</tbody></table></div></details>")
    k = b["card"]
    H.append('<h2 id="card">卡上的工具 <span style="color:var(--mute);font-weight:400;font-size:.85rem">%s · MCP 尾版 %s</span></h2><h3>鎖版席位</h3><div class="wrap"><table><tr><th>席位</th><th>現任</th><th>檔在</th><th>啟用時間</th></tr>' % (e(k.get("card_version")), e(k.get("mcp_tail"))))
    for s in k["seats"]:
        H.append("<tr><td>%s</td><td><code>%s</code></td><td>%s</td><td>%s</td></tr>" % (e(s["seat"]), e(s["file"]), "是" if s["exists"] else "否", e(str(s["activated_at"] or "")[:16])))
    H.append("</table></div><h3>省 Token 工具</h3><ul>" + "".join("<li><code>%s</code>:%s</li>" % (e(n), e((v if isinstance(v, str) else json.dumps(v, ensure_ascii=False))[:140])) for n, v in k["token_tools"].items()) + "</ul>")
    H.append('<h3>AI 必用步</h3><div class="wrap"><table><tr><th>步</th><th>指令</th><th>何時</th><th>做什麼</th></tr>' + "".join(
        "<tr><td>%s</td><td><code>%s</code></td><td>%s</td><td>%s</td></tr>" % (e(m.get("step")), e(str(m.get("cmd", ""))[:110]), e(m.get("when", "")), e(str(m.get("what", ""))[:120])) for m in k["must_use"]) + "</table></div>")
    H.append("<h3>門</h3><ul>" + "".join("<li><code>%s</code>:%s</li>" % (e(d.get("verb")), e(str(d.get("what", ""))[:140])) for d in k["doors"]) + "</ul>")
    H.append("<h3>禁止</h3><ul>" + "".join("<li>%s</li>" % e(n) for n in k["never"]) + "</ul>")
    H.append("</main></body></html>")
    return "\n".join(H)


def write_outputs(via: Path, b: dict) -> dict:
    out = via / OUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    (out / "TOOLBOARD_latest.json").write_text(json.dumps(b, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "TOOLBOARD_latest.md").write_text(to_md(b), encoding="utf-8")
    (out / "TOOLBOARD_latest.html").write_text(to_html(b), encoding="utf-8")
    with (out / "toolboard_ledger.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at": b["at"], "engine": ENGINE, "lamp": b["overall"]["lamp"], "lamps": {r["key"]: r["lamp"] for r in b["lamps"]},
                            "stations": b["tools"]["stations"], "never_run": b["tools"]["never_run"]}, ensure_ascii=False) + "\n")
    return {"json": str(out / "TOOLBOARD_latest.json"), "md": str(out / "TOOLBOARD_latest.md"), "html": str(out / "TOOLBOARD_latest.html"), "ledger": str(out / "toolboard_ledger.jsonl")}


def run(via: Path, no_write: bool = False, open_after: bool = False) -> int:
    b = build(via)
    paths = {} if no_write else write_outputs(via, b)
    print("[%s] %s · 總燈 %s · %s" % (b["overall"]["lamp"], ENGINE, b["overall"]["lamp"], b["overall"]["meaning"]))
    for r in b["lamps"]:
        print("  [%s]%s %s · %s" % (r["lamp"], "(過期)" if r["stale"] else "", r["title"], r["note"][:110]))
    t = b["tools"]
    print("  工具 %d 站 · 沒跑過 %d · " % (t["stations"], t["never_run"]) + " · ".join("%s %d(%s)" % (c["prefix"], c["count"], c["lamp"]) for c in t["categories"]))
    if paths:
        print("  落檔:" + " · ".join(paths.values()))
        if open_after:
            webbrowser.open(Path(paths["html"]).as_uri())
    return 0 if b["overall"]["lamp"] in ("GREEN", "YELLOW") else 1


# ───────────────────────── 自測(臨時 VIA 樹 · 零網路) ─────────────────────────
def _fixture(td: Path, *, handoff_at="2026-11-09T16:00:00Z", token_rc=0, with_test=True, vtoken=True) -> Path:
    via = td / "VeritasIntelligenceAnalytics"
    def w(rel, obj):
        p = via / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    w("VIA_Reports/backup/CHECK_latest.json", {"lamp": "YELLOW", "at": "2026-11-10T01:42:23Z", "backup_at": "2026-11-09T15:57:02Z", "meaning": "可開工 · 但:6 檔變了", "zip_state": "OK", "files": {"same": 354, "changed": 6, "missing": 0}})
    w("docs/handoff/backup/BACKUP_MANIFEST_latest.json", {"systems": {"VCGC": {}, "VDF": {}}, "total_files": 360})
    if with_test:
        w("VIA_Reports/vcgc/TEST_latest.json", {"lamp": "YELLOW", "mode": "quick", "at": "2026-11-09T17:00:00Z", "head": "cdfd81da4855", "secs": 200, "counts": {"GREEN": 9, "YELLOW": 2}, "rows": [{}] * 11})
    state = {"C-x": {"lamp": "RED", "at": "2026-11-01T00:00:00Z", "secs": 2, "last": "boom"}, "upd:CGC_MDL224_TestAuto_v0106": {"lamp": "GREEN"}, "V-gone": {"lamp": "GREEN"}}
    if vtoken:
        state["V-token"] = {"lamp": "GREEN", "rc": 0, "at": "2026-11-09T17:00:00Z", "secs": 1.4, "last": "ok"}
    w("VIA_Reports/vcgc/TEST_STATE_v0101.json", state)
    w("docs/handoff/evidence/token.json", {"rc": token_rc, "target_marker_seen": token_rc == 0, "completed_at": "2026-11-09T21:12:14+00:00", "scope": "token v0117"})
    w("VIA_Reports/gate/GATE_latest.json", {"verdict": "GREEN", "at": "2026-11-09T11:46:16+00:00", "run": "gate-1", "blockers": {}, "engine": "CGC_MDL149_x_v0185.py"})
    w("docs/handoff/HANDOFF_latest.json", {"lamp": "GREEN", "closeout_lamp": "YELLOW", "at": handoff_at, "pending": [1, 2]})
    w("VIA_Reports/mutual/MUTUAL_latest.json", {"lamp": "RED", "at": "2026-11-09T16:00:15Z", "systems": {"VCGC": {"lamp": "YELLOW"}, "VDF": {"lamp": "RED"}}})
    (via / "supportive modules/registry").mkdir(parents=True, exist_ok=True)
    (via / "supportive modules/registry/tok.py").write_text("# seat\n", encoding="utf-8")
    w("supportive modules/registry/VIA_ToolVersion_Lock_v0100.json", {"policy": "x", "token": {"path": "supportive modules/registry/tok.py", "activated_at": None}, "nlp": {"path": "supportive modules/registry/tok.py"}})
    w("supportive modules/registry/VIA_VCGC_FunctionInventory_SSOT_v0214.json", {"version": "v0214", "stations": [
        {"id": "V-token", "name": "省 Token 第一步", "argv": ["token"], "quick": True}, {"id": "V-new", "name": "新動詞", "argv": ["new"]},
        {"id": "S-nlp", "name": "席位 NLP", "argv": ["run", "x"]}, {"id": "C-x", "name": "交接案 x", "argv": ["run", "y"]}, {"id": "P-entry", "name": "PS 入口", "kind": "ps"}, {"id": "ZZ-odd", "name": "怪前綴", "argv": ["z"]}]})
    w("supportive modules/registry/VIA_AI_FunctionCard_SSOT_v0102.json", {"version": "v0102", "token_tools": {"read": "骨架卡", "slice": {"what": "切片"}}, "must_use": [{"step": 1, "cmd": "token", "when": "進場", "what": "啟用"}], "doors": [{"verb": "enter", "what": "入口"}], "never": ["TA-Lib 不用"]})
    (via / "supportive modules/registry/CGC_MDL279_MCPServer_v0102.py").write_text("# mcp\n", encoding="utf-8")
    return via


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))
    now = datetime(2026, 11, 10, 2, 0, tzinfo=timezone.utc)
    with tempfile.TemporaryDirectory(prefix="via_toolboard_") as td:
        via = _fixture(Path(td))
        b = build(via, now)
        L = {r["key"]: r for r in b["lamps"]}
        chk("ⓐ 燈號七盞 · 備份 YELLOW · 串測 YELLOW · token GREEN · 閘 GREEN · 交接 GREEN · 互監 RED · 鎖 GREEN",
            [r["key"] for r in b["lamps"]] == ["backup", "test", "token", "gate", "handoff", "mutual", "lock"] and L["backup"]["lamp"] == "YELLOW" and L["test"]["lamp"] == "YELLOW"
            and L["token"]["lamp"] == "GREEN" and L["gate"]["lamp"] == "GREEN" and L["handoff"]["lamp"] == "GREEN" and L["mutual"]["lamp"] == "RED" and L["lock"]["lamp"] == "GREEN")
        chk("ⓑ 總燈 = 自己收據最差 YELLOW(互監 RED 不併入)· 備份 0.29h 不過期 · token 燈取自 V-token 站(帶交接證據日期)",
            b["overall"]["lamp"] == "YELLOW" and not L["backup"]["stale"] and L["backup"]["age_hours"] == 0.29 and "[V-token]" in L["token"]["source"] and "交接證據 2026-11-09" in L["token"]["note"], b["overall"])
        cats = {c["prefix"]: c for c in b["tools"]["categories"]}
        chk("ⓒ 分類:V 2 站(GREEN + NOT_RUN)· S 1 NOT_RUN · C 1 RED · P 1 · 怪前綴進 other · 沒跑過 3 · 狀態多出 V-gone · upd 另列",
            cats["V"]["count"] == 2 and cats["V"]["lamps"]["GREEN"] == 1 and cats["V"]["lamps"]["NOT_RUN"] == 1 and cats["V"]["lamp"] == "NOT_RUN" and cats["C"]["lamp"] == "RED"
            and len(b["tools"]["other"]) == 1 and b["tools"]["never_run"] == 3 and b["tools"]["state_not_in_inventory"] == ["V-gone"] and b["tools"]["updated_tails_in_state"] == ["upd:CGC_MDL224_TestAuto_v0106"],
            {k: (c["count"], c["lamps"]) for k, c in cats.items() if c["count"]})
        chk("ⓓ 卡:席位 2 · 檔都在 · token 工具 2 · 必用 1 · 門 1 · 禁 1 · MCP 尾版 v0102", len(b["card"]["seats"]) == 2 and all(s["exists"] for s in b["card"]["seats"])
            and len(b["card"]["token_tools"]) == 2 and len(b["card"]["must_use"]) == 1 and b["card"]["mcp_tail"] == "CGC_MDL279_MCPServer_v0102.py")
        md = to_md(b)
        h = to_html(b)
        chk("ⓔ md 第一節是燈號 · html 燈號條在工具分類之前 · 一支 style · 七個燈 tile", md.index("## 1. 燈號") < md.index("## 2. 工具分類") and h.index('id="lamps"') < h.index('id="tools"') < h.index('id="card"')
            and h.count("<style>") == 1 and h.count('class="tile') >= 7 and "lamp big YELLOW" in h)
        paths = write_outputs(via, b)
        n1 = len((via / OUT_DIR / "toolboard_ledger.jsonl").read_text(encoding="utf-8").splitlines())
        write_outputs(via, b)
        n2 = len((via / OUT_DIR / "toolboard_ledger.jsonl").read_text(encoding="utf-8").splitlines())
        chk("ⓕ 落檔三份 + 帳只增(1 → 2)· json 可回讀", all(Path(p).exists() for p in paths.values()) and (n1, n2) == (1, 2)
            and json.loads(Path(paths["json"]).read_text(encoding="utf-8"))["overall"]["lamp"] == "YELLOW")
    with tempfile.TemporaryDirectory(prefix="via_toolboard_") as td:
        via = _fixture(Path(td), handoff_at="2026-10-02T21:11:49+00:00", token_rc=1, with_test=False, vtoken=False)
        b = build(via, now)
        L = {r["key"]: r for r in b["lamps"]}
        chk("ⓖ 交接 38 天前 → 過期旗 · 無 V-token 站時退到交接證據 rc 1 → RED · 串測無收據 → GRAY · 總燈 RED(含過期與缺收據說明)",
            L["handoff"]["stale"] and L["token"]["lamp"] == "RED" and "[V-token]" not in L["token"]["source"] and L["test"]["lamp"] == "GRAY" and b["overall"]["lamp"] == "RED"
            and "過期" in b["overall"]["meaning"] and "缺收據:test" in b["overall"]["meaning"], b["overall"]["meaning"])
    with tempfile.TemporaryDirectory(prefix="via_toolboard_") as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        via.mkdir()
        b = build(via, now)
        chk("ⓗ 空樹:七盞全 GRAY · 總燈 GRAY · 0 站 · 不炸", all(r["lamp"] == "GRAY" for r in b["lamps"]) and b["overall"]["lamp"] == "GRAY" and b["tools"]["stations"] == 0)
        rc = run(via, no_write=True)
        chk("ⓘ run --no-write 不落檔 · 總燈 GRAY 回 rc 1(不是綠)", not (via / OUT_DIR).exists() and rc == 1)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest()")[0]
    chk("ⓙ 邊界:本檔不開網路 / 不開子行程 / 不寫冊(只寫 VIA_Reports/vcgc)",
        not re.search(r"^\s*(import|from)\s+(urllib|socket|requests|http\b|subprocess)", body, re.M) and "registry" not in body.split("def write_outputs")[1].split("def run")[0])
    bad = len(ok) - sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if not bad else "FAIL", ENGINE, sum(ok), len(ok)), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="VIA_VCGCToolBoard", description=__doc__.splitlines()[0])
    ap.add_argument("verb", nargs="?", default="run", choices=["run", "selftest"])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--root", default=None, help="VIA 根(預設由本檔位置推)")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--open", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest or a.verb == "selftest":
        return selftest()
    via = Path(a.root).resolve() if a.root else VIA
    if (via / "VeritasIntelligenceAnalytics").is_dir():
        via = via / "VeritasIntelligenceAnalytics"
    return run(via, no_write=a.no_write, open_after=a.open)


if __name__ == "__main__":
    sys.exit(main())
