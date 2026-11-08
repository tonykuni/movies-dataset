#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_FiveSystemChain v0100 — 五系統自動串測:VCGC → VDF → VRN → VQG → VAP(各走自己的入口)

操作員 2026-11-08 令:「自動測試 VCGC to VDF to VRN to VQG to VAP」+ ChatGPT 分享頁的三行 Header
與多頁式矩陣報告規格。

**「串」是回報次序,不是閘。**(政策 L123 / 五系統對等獨立)
  五個系統各是自己系統的入口,互不干涉。所以上游紅**不會**擋下游 —— 五個一律都跑完,
  每個自報自己的燈。把它做成閘就等於讓 VCGC 變成其他四個的門,那違反對等獨立。
  本引擎只做兩件事:① 依序叫每個系統「自己的」入口跑「它自己的」自測 ② 把它自己印的判決行逐字收下來。

判燈四條,一條都不放寬:
  ABSENT   入口檔不在          → GRAY(沒量到,不是紅)
  TIMEOUT  逾時沒拿到判決       → GRAY + 記實際秒數(沒拿到判決就不准猜)
  rc != 0                      → RED
  rc == 0 但找不到它自己的判決行 → **YELLOW UNVERIFIED**
           rc 0 本身不是證據 —— 系統得自己印出判決才算(跟交接閘的 target_marker_seen 同一條規矩)
  rc == 0 且判決行說 PASS / GREEN → GREEN;判決行說 YELLOW / RED → 照它說的,不漂白

總燈 = 五個之中最壞的那一個。零網路 · 零安裝 · 不代設同意閘。

動詞:run [--apply] [--only VCGC,VDF] | plan | ui | header | --selftest
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

import argparse
import html
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "VIA.FiveSystemChain.v1"
HERE = Path(__file__).resolve().parent                 # docs/handoff/ai
VIA = HERE.parent.parent.parent                        # VeritasIntelligenceAnalytics
TAG = "VIA_FiveSystemChain v" + Path(__file__).stem.rsplit("_v", 1)[-1]
BOOK_DIR = VIA / "supportive modules" / "registry"
BOOK_STEM = "VIA_FiveSystemChain_SSOT_v"
UI_NAME = "VIA_FiveSystemChain_UI.html"

RANK = {"GREEN": 0, "YELLOW": 1, "GRAY": 2, "RED": 3}
LAMPS = tuple(RANK)

# 三行 Header 正本 —— 操作員 2026-11-08 在 ChatGPT 分享頁定案的文案。
# 第二行:**VCGC 分寫,其餘四個連寫**(操作員原話「除了 VCGC 外其他的第二行都要連結在一起」)。
HEADER_UI_VERSION = "v0106.4"
SYSTEMS: list[dict] = [
    {
        "code": "VCGC", "brand": "Veritas Central Governance Console",
        "scope": "Policy Management · Workflow Orchestration · Tool Administration",
        "zh": "中央治理主控台", "concat": False,
        "dir": "supportive modules/registry",
        "stem": "CGC_MDL149_VeritasCentralGovernanceConsole_v",
        "argv": ["test", "--quick"], "env": {"VIA_FROM_VCGC": "YES"},
        "verdict": r"^\[VCGC 全功能串測\].*$", "timeout": 1500,
    },
    {
        "code": "VDF", "brand": "VeritasDataForge",
        "scope": "Financial Data Repository · Source Integration · Database Management",
        "zh": "資料鍛造", "concat": True,
        "dir": "functional modules/VDF", "stem": "VDF_SystemManager_v",
        "argv": ["--selftest"], "env": {"VIA_FROM_VDFSM": "YES"},
        "verdict": r"^\s*\[計\] VDF_SystemManager .*$", "timeout": 600,
    },
    {
        "code": "VRN", "brand": "VeritasReportNova",
        "scope": "Research Library · Document Intelligence · Knowledge Management",
        "zh": "研報擷取(VRN-2)", "concat": True,
        "dir": "functional modules/VRN", "stem": "VRN_SystemManager_v",
        "argv": ["--selftest"], "env": {},
        "verdict": r"^\s*\[計\] VRN-2 SystemManager .*$", "timeout": 900,
    },
    {
        "code": "VQG", "brand": "VeritasQuantGuard",
        "scope": "Factor Analytics · Model Development · Model Validation",
        "zh": "量化守門", "concat": True,
        "dir": "functional modules/VQG", "stem": "VQG_AllInOne_v",
        "argv": ["--selftest"], "env": {},
        "verdict": r"^\s*\[(PASS|FAIL)\] VQG .*selftest.*$", "timeout": 600,
    },
    {
        "code": "VAP", "brand": "VeritasAutoPlot",
        "scope": "Visual Analytics · Asset Comparison · Dashboard Automation",
        "zh": "自動製圖", "concat": True,
        "dir": "functional modules/VAP/intake/allinone_v0300", "stem": "VAP_AllInOne_v",
        "argv": ["--run-self-test"], "env": {"VIA_FROM_VCGC": "YES"},
        # VAP 的判決是 JSON 的頂層 status,不是一行中文 —— 照它實際印的格式抓,不要求它改。
        "verdict": r'^\s*"status":\s*"(PASS|FAIL|[A-Z_]+)"\s*,?\s*$', "timeout": 900,
    },
]


# ───────────────────────── 入口解析(家族尾版,不釘版號) ─────────────────────────
def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d{3,4})\.py$", p.name)
    return int(m.group(1)) if m else -1


def resolve_entry(sysrow: dict, via: Path = VIA) -> Path | None:
    """各系統入口一律解析家族尾版(避免 PINVER;版號寫死就會指到舊版)。"""
    d = via / sysrow["dir"]
    if not d.is_dir():
        return None
    c = sorted((p for p in d.glob(f"{sysrow['stem']}*.py") if _vnum(p) >= 0), key=_vnum)
    return c[-1] if c else None


# ───────────────────────── 判燈(純函式,可餵夾具) ─────────────────────────
GREENISH = re.compile(r"\b(PASS|GREEN)\b")
YELLOWISH = re.compile(r"\b(YELLOW|AMBER|WARN)\b")
REDISH = re.compile(r"\b(RED|FAIL)\b")


def judge(sysrow: dict, rc: int | None, out: str, elapsed: float,
          entry: Path | None, timed_out: bool = False) -> dict:
    """一個系統的燈 + 它自己印的判決行(逐字)。

    次序刻意:入口不在 → 逾時 → rc → 有沒有判決行 → 判決行說什麼。
    rc 0 排在「有沒有判決行」之前,就是為了讓「rc 0 但沒印判決」落在 YELLOW 而不是 GREEN。
    """
    base = {"code": sysrow["code"], "entry": (str(entry.relative_to(VIA)) if entry else ""),
            "argv": list(sysrow["argv"]), "elapsed_s": round(elapsed, 1),
            "rc": rc, "verdict_line": "", "lamp": "GRAY", "why": ""}
    if entry is None:
        base["why"] = f"入口不在:{sysrow['dir']}/{sysrow['stem']}*.py 找不到尾版 —— 沒量到,不當紅"
        return base
    if timed_out:
        base["why"] = f"逾時 {sysrow['timeout']}s 沒拿到判決(實跑 {base['elapsed_s']}s)—— 沒拿到判決就不猜"
        return base
    hit = ""
    for line in out.splitlines():
        if re.match(sysrow["verdict"], line):
            hit = line.strip()                       # 最後一條勝(自測通常最後才印總結)
    base["verdict_line"] = hit
    if rc != 0:
        base["lamp"] = "RED"
        base["why"] = f"它自己的入口回 rc {rc}" + (f";判決行:{hit}" if hit else ";而且沒印判決行")
        return base
    if not hit:
        base["lamp"] = "YELLOW"
        base["why"] = ("rc 0 但找不到它自己的判決行 —— **rc 0 本身不是證據**,"
                       "系統得自己印出判決才算(同交接閘 target_marker_seen 規矩)")
        return base
    if REDISH.search(hit) and not GREENISH.search(hit):
        base["lamp"] = "RED"
    elif YELLOWISH.search(hit):
        base["lamp"] = "YELLOW"
    elif GREENISH.search(hit):
        base["lamp"] = "GREEN"
    else:
        base["lamp"] = "YELLOW"
        base["why"] = "判決行認不出 PASS / GREEN / YELLOW / RED 任何一個字 —— 不替它決定,留黃"
    if not base["why"]:
        base["why"] = "照它自己印的判決行"
    return base


def roll_up(rows: list[dict]) -> str:
    lamp = "GREEN"
    for r in rows:
        if RANK[r["lamp"]] > RANK[lamp]:
            lamp = r["lamp"]
    return lamp if rows else "GRAY"


# ───────────────────────── 實跑 ─────────────────────────
def run_one(sysrow: dict, via: Path = VIA) -> dict:
    entry = resolve_entry(sysrow, via)
    if entry is None:
        return judge(sysrow, None, "", 0.0, None)
    env = dict(os.environ)
    env.update(sysrow.get("env") or {})
    env["PYTHONIOENCODING"] = "utf-8"
    t0 = time.monotonic()
    try:
        p = subprocess.run([sys.executable, str(entry), *sysrow["argv"]], cwd=str(via),
                           env=env, capture_output=True, text=True, errors="replace",
                           timeout=sysrow["timeout"])
        el = time.monotonic() - t0
        return judge(sysrow, p.returncode, (p.stdout or "") + "\n" + (p.stderr or ""), el, entry)
    except subprocess.TimeoutExpired:
        return judge(sysrow, None, "", time.monotonic() - t0, entry, timed_out=True)


def run_chain(only: list[str] | None = None, via: Path = VIA) -> dict:
    """五個一律都跑 —— 上游紅不擋下游(對等獨立)。only 只給人手動縮範圍用。"""
    pick = [s for s in SYSTEMS if not only or s["code"] in only]
    rows = [run_one(s, via) for s in pick]            # 不 break:這是刻意的
    return {
        "schema": SCHEMA, "engine": TAG,
        "ran_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "order": [s["code"] for s in pick],
        "chain_lamp": roll_up(rows),
        "independence": "「串」是回報次序不是閘:上游紅不擋下游,五個一律都跑完(政策 L123 五系統對等獨立)",
        "systems": rows,
        "counts": {k: sum(1 for r in rows if r["lamp"] == k) for k in LAMPS},
        "net": "零外呼 · 零安裝 · 不代設同意閘",
    }


# ───────────────────────── 三行 Header ─────────────────────────
def header_lines(sysrow: dict, engine_ver: str, date: str,
                 ui_ver: str = HEADER_UI_VERSION) -> list[str]:
    """三行 Header。第二行:VCGC 分寫,其餘四個連寫(操作員定案)。"""
    brand = sysrow["brand"] if sysrow["concat"] or sysrow["code"] == "VCGC" else sysrow["brand"]
    return [f"VIA · {sysrow['code']} · {date} · ENGINE {engine_ver}",
            brand,
            f"{sysrow['scope']} · UI {ui_ver}"]


def all_headers(engine_ver: str = "v0103", date: str = "2026-11-05") -> list[dict]:
    return [{"code": s["code"], "lines": header_lines(s, engine_ver, date)} for s in SYSTEMS]


# ───────────────────────── 盤冊(add-only) ─────────────────────────
def substance(rep: dict) -> str:
    import hashlib
    key = sorted((r["code"], r["lamp"], r["verdict_line"]) for r in rep["systems"])
    return hashlib.sha256(json.dumps(key, ensure_ascii=False).encode("utf-8")).hexdigest()


def write_book(rep: dict, dirpath: Path = BOOK_DIR) -> tuple[Path, str]:
    rep = {**rep, "substance_sha256": substance(rep)}
    cands = sorted(dirpath.glob(f"{BOOK_STEM}*.json"),
                   key=lambda p: int(re.search(r"_v(\d{4})\.", p.name).group(1)))
    if cands:
        prev = json.loads(cands[-1].read_text(encoding="utf-8"))
        if prev.get("substance_sha256") == rep["substance_sha256"]:
            return cands[-1], "UNCHANGED"
        nxt = int(re.search(r"_v(\d{4})\.", cands[-1].name).group(1)) + 1
    else:
        nxt = 100
    p = dirpath / f"{BOOK_STEM}{nxt:04d}.json"
    if p.exists():
        raise SystemExit(f"[紅] {p.name} 已存在 —— 已發布版號不覆寫")
    p.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return p, "WRITTEN"


# ───────────────────────── 六分頁 U/I(分享頁規格) ─────────────────────────
TABS = [("io", "首頁與 I/O"), ("ssot", "SSOT 與政策"), ("regex", "REGEX 與同義字"),
        ("exec", "執行與衝突"), ("test", "測試與輸出"), ("detail", "詳細報告 🔒")]


def ui_html(rep: dict) -> str:
    e = html.escape
    cls = {"GREEN": "ok", "YELLOW": "yel", "RED": "red", "GRAY": "gry"}
    sysmap = {s["code"]: s for s in SYSTEMS}
    hdr = []
    for h in all_headers():
        s = sysmap[h["code"]]
        row = next((r for r in rep["systems"] if r["code"] == h["code"]), None)
        lamp = row["lamp"] if row else "GRAY"
        hdr.append(
            f'<div class="sys"><div class="h1">{e(h["lines"][0])}</div>'
            f'<div class="h2">{e(h["lines"][1])}</div>'
            f'<div class="h3">{e(h["lines"][2])}</div>'
            f'<div class="lamp {cls[lamp]}">{e(lamp)}</div></div>')
    tr = "".join(
        f'<tr><td class="m">{e(r["code"])}</td><td class="{cls[r["lamp"]]}">{e(r["lamp"])}</td>'
        f'<td class="m">{e(str(r["rc"]))}</td><td class="m">{r["elapsed_s"]}s</td>'
        f'<td class="s">{e(r["entry"])} {e(" ".join(r["argv"]))}</td>'
        f'<td class="s">{e(r["verdict_line"] or "(沒印判決行)")}</td>'
        f'<td class="s">{e(r["why"])}</td></tr>' for r in rep["systems"])
    ex = []
    for s in SYSTEMS:
        envs = s.get("env") or {}
        flags = " ".join(f"{k}={v}" for k, v in envs.items()) or "—"
        ex.append(f'<tr><td class="m">{e(s["code"])}</td>'
                  f'<td class="s">{e(s["dir"] + "/" + s["stem"] + "*.py")}</td>'
                  f'<td class="m">{e(flags)}</td>'
                  f'<td class="m">{s["timeout"]}s</td></tr>')
    ex_rows = "".join(ex)
    cnt = rep["counts"]
    chips = [("總燈", rep["chain_lamp"]), ("GREEN", cnt["GREEN"]), ("YELLOW", cnt["YELLOW"]),
             ("RED", cnt["RED"]), ("GRAY", cnt["GRAY"]), ("次序", " → ".join(rep["order"]))]
    tabs = "".join(
        f'<button class="tab{" on" if i == 0 else ""}" data-t="{k}">{i+1}｜{e(v)}</button>'
        for i, (k, v) in enumerate(TABS))
    return f"""<title>VIA 五系統串測</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
:root{{--vl-bg:#f7f8fa;--vl-white:#fff;--vl-ink:#15181d;--vl-muted:#5b6472;
--vl-border:#d8dde5;--vl-border-soft:#eceff4;--vl-row:#fafbfd;
--vl-success-bg:#e8f6ee;--vl-success-ink:#0f5c37;
--vl-warning-bg:#fdf4e3;--vl-warning-ink:#7a5410;
--vl-danger-bg:#fdecec;--vl-danger-ink:#8d1f1f;
--vl-font-cjk:"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif;
--vl-font-mono:ui-monospace,SFMono-Regular,Menlo,monospace;
--vl-size-title:20px;--vl-size-primary:15px;--vl-size-base:13px;--vl-size-label:11px;
color-scheme:light}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{
--vl-bg:#111419;--vl-white:#181c22;--vl-ink:#e7ebf1;--vl-muted:#9aa5b4;
--vl-border:#2b313a;--vl-border-soft:#22272e;--vl-row:#1d2128;
--vl-success-bg:#12301f;--vl-success-ink:#7fd6a4;
--vl-warning-bg:#332a12;--vl-warning-ink:#e8c377;
--vl-danger-bg:#3a1a1a;--vl-danger-ink:#f0a0a0;color-scheme:dark}}}}
:root[data-theme="dark"]{{--vl-bg:#111419;--vl-white:#181c22;--vl-ink:#e7ebf1;--vl-muted:#9aa5b4;
--vl-border:#2b313a;--vl-border-soft:#22272e;--vl-row:#1d2128;
--vl-success-bg:#12301f;--vl-success-ink:#7fd6a4;
--vl-warning-bg:#332a12;--vl-warning-ink:#e8c377;
--vl-danger-bg:#3a1a1a;--vl-danger-ink:#f0a0a0;color-scheme:dark}}
body{{background:var(--vl-bg);color:var(--vl-ink);font-family:var(--vl-font-cjk);
font-size:var(--vl-size-base);margin:0}}
.wrap{{padding-left:max(16px,env(safe-area-inset-left,0px));
padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:24px;max-width:1180px;margin:0 auto}}
h1{{font-size:var(--vl-size-title);margin:0 0 4px;text-wrap:balance}}
.sub{{color:var(--vl-muted);font-size:var(--vl-size-label);margin-bottom:16px}}
.chips{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px}}
.chip{{background:var(--vl-white);border:1px solid var(--vl-border);border-radius:8px;padding:8px 12px;min-width:0}}
.chip b{{display:block;font-size:var(--vl-size-primary);font-family:var(--vl-font-mono)}}
.chip span{{color:var(--vl-muted);font-size:var(--vl-size-label);letter-spacing:.04em}}
.hdrs{{display:grid;gap:10px;margin-bottom:18px}}
.sys{{background:var(--vl-white);border:1px solid var(--vl-border);border-radius:10px;
padding:12px 14px;display:grid;grid-template-columns:1fr auto;gap:4px 12px;align-items:center;min-width:0}}
.sys .h1{{grid-column:1;font-size:var(--vl-size-label);color:var(--vl-muted);
font-family:var(--vl-font-mono);letter-spacing:.04em}}
.sys .h2{{grid-column:1;font-size:var(--vl-size-primary);font-weight:700}}
.sys .h3{{grid-column:1;font-size:var(--vl-size-label);color:var(--vl-muted)}}
.sys .lamp{{grid-column:2;grid-row:1/4;align-self:center;padding:6px 12px;border-radius:7px;
font-family:var(--vl-font-mono);font-weight:700;white-space:nowrap}}
.tabs{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}}
.tab{{background:var(--vl-white);color:var(--vl-muted);border:1px solid var(--vl-border);
border-radius:7px;padding:7px 11px;font-family:inherit;font-size:var(--vl-size-label);cursor:pointer}}
.tab.on{{color:var(--vl-ink);font-weight:700;border-color:var(--vl-muted)}}
.card{{background:var(--vl-white);border:1px solid var(--vl-border);border-radius:10px;
padding:14px;margin-bottom:16px;min-width:0}}
h2{{font-size:var(--vl-size-primary);margin:0 0 10px}}
.scroll{{overflow-x:auto}}
table{{border-collapse:collapse;width:100%;font-size:var(--vl-size-base)}}
th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--vl-border-soft);vertical-align:top}}
th{{color:var(--vl-muted);font-size:var(--vl-size-label);letter-spacing:.04em;white-space:nowrap}}
tr:nth-child(even) td{{background:var(--vl-row)}}
td.m{{font-family:var(--vl-font-mono);white-space:nowrap}}
td.s{{color:var(--vl-muted);font-size:var(--vl-size-label)}}
.ok{{background:var(--vl-success-bg);color:var(--vl-success-ink);font-weight:700}}
.yel{{background:var(--vl-warning-bg);color:var(--vl-warning-ink);font-weight:700}}
.red{{background:var(--vl-danger-bg);color:var(--vl-danger-ink);font-weight:700}}
.gry{{color:var(--vl-muted)}}
.note{{color:var(--vl-muted);font-size:var(--vl-size-label);line-height:1.7}}
</style>
<div class="wrap">
<h1>VIA 五系統串測</h1>
<div class="sub">{e(rep['engine'])} · 次序 {e(' → '.join(rep['order']))} · {e(rep['ran_at_utc'])} · {e(rep['net'])}</div>
<div class="chips">{''.join(f'<div class="chip"><b>{e(str(v))}</b><span>{e(str(k))}</span></div>' for k, v in chips)}</div>
<div class="hdrs">{''.join(hdr)}</div>
<div class="tabs">{tabs}</div>
<div class="card" data-p="io"><h2>1｜首頁與 I/O ——每個系統自己印的判決</h2><div class="scroll"><table>
<thead><tr><th>系統</th><th>燈</th><th>rc</th><th>耗時</th><th>入口 + 動詞</th><th>它自己的判決行(逐字)</th><th>判燈理由</th></tr></thead>
<tbody>{tr}</tbody></table></div>
<p class="note">{e(rep['independence'])}</p></div>
<div class="card" data-p="ssot" hidden><h2>2｜SSOT 與政策</h2>
<p class="note">五系統對等獨立(政策 L123):各是自己系統的入口,互不干涉、互相只讀監控。<br>
本頁的「候選 ID → 正式 SSOT ID → 回填」流程由 VCGC 的 <code>ssot panorama</code> 與
<code>CGC_MDL237_NumberingSystem</code> 自報,本引擎不代算、不代寫。</p></div>
<div class="card" data-p="regex" hidden><h2>3｜REGEX 與同義字</h2>
<p class="note">正本在各系統自己的冊(VDF 的 <code>VDF_InputUniverse_SSOT</code> code_regex、
VCGC 的同義字冊)。本引擎只讀不改,也不在這裡抄一份 —— 抄一份就會有兩個正本。</p></div>
<div class="card" data-p="exec" hidden><h2>4｜執行與衝突</h2><div class="scroll"><table>
<thead><tr><th>系統</th><th>入口(家族尾版)</th><th>環境旗標</th><th>逾時上限</th></tr></thead><tbody>
{ex_rows}
</tbody></table></div>
<p class="note">入口一律解析家族尾版,不釘版號 —— 釘死就會指到舊版(PINVER)。</p></div>
<div class="card" data-p="test" hidden><h2>5｜測試與輸出</h2>
<p class="note">判燈四條:入口不在 = GRAY · 逾時 = GRAY 並記實際秒數 · rc≠0 = RED ·
<b>rc 0 但沒印判決行 = YELLOW UNVERIFIED</b>(rc 0 本身不是證據,同交接閘 target_marker_seen)。<br>
判決行說 YELLOW 就留 YELLOW,不漂白成綠。總燈 = 五個之中最壞的那一個。</p></div>
<div class="card" data-p="detail" hidden><h2>6｜詳細報告 🔒</h2>
<p class="note">逐字原文(每個系統的完整 stdout / stderr)**不進這一頁** ——
它們可能含本機路徑與環境值,寫進可分享的頁面等於外洩。<br>
完整原文留在盤冊 <code>{e(BOOK_STEM)}*.json</code> 的 <code>verdict_line</code> 與各系統自己的日誌裡,
要看請在本機開。這一頁只說它在哪裡,不把它搬過來。</p></div>
</div>
<script>
document.querySelectorAll('.tab').forEach(function (b) {{
  b.addEventListener('click', function () {{
    document.querySelectorAll('.tab').forEach(function (x) {{ x.classList.remove('on'); }});
    b.classList.add('on');
    document.querySelectorAll('[data-p]').forEach(function (p) {{
      p.hidden = (p.getAttribute('data-p') !== b.getAttribute('data-t'));
    }});
  }});
}});
</script>
"""


# ───────────────────────── 自測 ─────────────────────────
def selftest() -> int:
    ok = fail = 0

    def chk(name, cond, extra=""):
        nonlocal ok, fail
        if cond:
            ok += 1
            print(f"  ✔ {name}")
        else:
            fail += 1
            print(f"  ✘ {name}{(' —— ' + str(extra)) if extra else ''}")

    print(f"[{TAG} 自測]")
    S = {s["code"]: s for s in SYSTEMS}

    # ① 五系統都在、次序照操作員寫的
    chk("① 五系統都在且次序 VCGC → VDF → VRN → VQG → VAP",
        [s["code"] for s in SYSTEMS] == ["VCGC", "VDF", "VRN", "VQG", "VAP"])

    # ② 入口解析家族尾版,不釘版號
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        d = root / "functional modules/VDF"
        d.mkdir(parents=True)
        for v in (100, 168, 99):
            (d / f"VDF_SystemManager_v{v:04d}.py").write_text("", encoding="utf-8")
        got = resolve_entry(S["VDF"], root)
        chk("② 入口取家族尾版(v0168 不是 v0100)", got and got.name.endswith("v0168.py"), got)
        chk("③ 入口不在回 None(不丟例外)", resolve_entry(S["VQG"], root) is None)

    # ④–⑧ 判燈四條,每條正反面
    j = judge(S["VDF"], None, "", 0.0, None)
    chk("④ 入口不在 = GRAY(沒量到,不當紅)", j["lamp"] == "GRAY" and "不當紅" in j["why"])
    j = judge(S["VDF"], None, "", 601.2, Path(__file__), timed_out=True)
    chk("⑤ 逾時 = GRAY 且記實際秒數(不猜)",
        j["lamp"] == "GRAY" and "601.2" in j["why"] and "不猜" in j["why"])
    j = judge(S["VDF"], 1, "  [計] VDF_SystemManager v0168 本版 6/6 · 合計 PASS", 1.0, Path(__file__))
    chk("⑥ rc≠0 = RED,即使判決行寫 PASS 也不翻綠", j["lamp"] == "RED", j)
    j = judge(S["VDF"], 0, "跑完了,沒有判決行", 1.0, Path(__file__))
    chk("⑦ rc 0 但沒印判決行 = YELLOW UNVERIFIED(rc 0 不是證據)",
        j["lamp"] == "YELLOW" and "rc 0 本身不是證據" in j["why"], j)
    j = judge(S["VDF"], 0, "  [計] VDF_SystemManager v0168 本版 6/6 · 前版鏈 PASS · 合計 PASS", 1.0, Path(__file__))
    chk("⑧ rc 0 + 判決行 PASS = GREEN,且判決行逐字收下",
        j["lamp"] == "GREEN" and j["verdict_line"].endswith("合計 PASS"), j)

    # ⑨–⑪ 判決行說什麼就是什麼,不漂白
    j = judge(S["VCGC"], 0, "[VCGC 全功能串測] YELLOW · 站 11(綠 9 · 黃 2 · 紅 0)", 1.0, Path(__file__))
    chk("⑨ 判決行說 YELLOW 就留 YELLOW(不漂白成綠)", j["lamp"] == "YELLOW", j)
    j = judge(S["VCGC"], 0, "[VCGC 全功能串測] RED · 站 11(綠 8 · 黃 2 · 紅 1)", 1.0, Path(__file__))
    chk("⑩ 判決行說 RED 就是 RED", j["lamp"] == "RED", j)
    j = judge(S["VCGC"], 0, "[VCGC 全功能串測] 站 11 跑完了", 1.0, Path(__file__))
    chk("⑪ 判決行認不出任何燈字 → 留黃,不替它決定",
        j["lamp"] == "YELLOW" and "不替它決定" in j["why"], j)

    # ⑫ 每個系統的判決正則都對得上它實際印的格式(這五條是實測抓回來的)
    real = {
        "VCGC": "[VCGC 全功能串測] YELLOW · 站 11(綠 9 · 黃 2 · 紅 0 · 沿用 0)· 212.2s",
        "VDF": "  [計] VDF_SystemManager v0168 本版 6/6 · 前版鏈 PASS · 合計 PASS",
        "VRN": "[計] VRN-2 SystemManager v0262(VRN_SystemManager_v0262.py)自測 5/5 · PASS · 前版鏈 rc 0",
        "VQG": "[PASS] VQG v0107 selftest · 12/12(含 v0105 全部)· 零網路 · 只在沙盒寫",
        "VAP": '      "status": "PASS",',
    }
    for code, line in real.items():
        chk(f"⑫ {code} 的判決正則對得上它實際印的那一行",
            bool(re.match(S[code]["verdict"], line)), line)

    # ⑬ 最後一條判決勝(自測通常最後才印總結)
    j = judge(S["VQG"], 0, "[PASS] VQG v0105 selftest · 9/9\n[PASS] VQG v0107 selftest · 12/12", 1.0, Path(__file__))
    chk("⑬ 多條判決行取最後一條(總結在最後)", "v0107" in j["verdict_line"], j)

    # ⑭–⑯ 總燈 = 最壞的那一個
    mk = lambda *ls: [{"code": f"S{i}", "lamp": l} for i, l in enumerate(ls)]
    chk("⑭ 全綠 → 總燈 GREEN", roll_up(mk("GREEN", "GREEN", "GREEN")) == "GREEN")
    chk("⑮ 有黃 → 總燈 YELLOW;有紅 → RED(紅勝過灰)",
        roll_up(mk("GREEN", "YELLOW")) == "YELLOW" and roll_up(mk("GRAY", "RED")) == "RED")
    chk("⑯ 灰勝過黃(沒量到比量到有問題更該被看見)", roll_up(mk("YELLOW", "GRAY")) == "GRAY")

    # ⑰ 獨立性:上游紅不擋下游 —— 用 AST 檢 run_chain,不用字面檢。
    #    字面檢在這裡必紅:原始碼註解本來就寫著「不 break:這是刻意的」,
    #    字面檢會把「我宣告我不 break」當成「我 break 了」(技能引擎那次同一類錯)。
    import ast as _a, inspect as _i, textwrap as _t
    fn = _a.parse(_t.dedent(_i.getsource(run_chain))).body[0]
    breaks = [n for n in _a.walk(fn) if isinstance(n, (_a.Break, _a.Continue))]
    loops = [n for n in _a.walk(fn) if isinstance(n, (_a.For, _a.While))]
    early = [n for lp in loops for n in _a.walk(lp) if isinstance(n, _a.Return)]
    chk("⑰ run_chain 的 AST 裡沒有 break / continue,迴圈內也沒有 return(上游紅不擋下游)",
        not breaks and not early, (len(breaks), len(early)))
    chk("⑱ 報告明寫獨立性(不是閘)",
        "不是閘" in run_chain.__doc__ or "不擋下游" in run_chain.__doc__)

    # ⑲–㉑ 三行 Header 照操作員定案
    hs = {h["code"]: h["lines"] for h in all_headers()}
    chk("⑲ 第一行格式 VIA · 代號 · 日期 · ENGINE 版號",
        all(re.match(r"^VIA · [A-Z]+ · \d{4}-\d{2}-\d{2} · ENGINE v\d{4}$", v[0]) for v in hs.values()),
        hs["VDF"][0])
    chk("⑳ VCGC 第二行分寫(Veritas Central Governance Console)",
        hs["VCGC"][1] == "Veritas Central Governance Console")
    chk("㉑ 其餘四個第二行連寫(操作員:除 VCGC 外都要連在一起)",
        [hs[c][1] for c in ("VDF", "VRN", "VQG", "VAP")]
        == ["VeritasDataForge", "VeritasReportNova", "VeritasQuantGuard", "VeritasAutoPlot"],
        [hs[c][1] for c in ("VDF", "VRN", "VQG", "VAP")])
    chk("㉒ 第三行帶 UI 版號且三行都有", all(len(v) == 3 and v[2].endswith("UI " + HEADER_UI_VERSION)
                                       for v in hs.values()))
    chk("㉓ 五個第三行互不相同(只看第三行也分得出誰是誰)",
        len({v[2] for v in hs.values()}) == 5)

    # ㉔–㉘ U/I 契約 + 六分頁
    rep = {"schema": SCHEMA, "engine": TAG, "ran_at_utc": "2026-11-08T00:00:00Z",
           "order": [s["code"] for s in SYSTEMS], "chain_lamp": "YELLOW",
           "independence": "x", "net": "零外呼",
           "systems": [judge(S[c], 0, real[c], 1.0, Path(__file__)) for c in
                       ("VCGC", "VDF", "VRN", "VQG", "VAP")],
           "counts": {k: 0 for k in LAMPS}}
    h = ui_html(rep)
    chk("㉔ U/I 不含骨架標籤", not any(t in h.lower() for t in ("<!doctype", "<html", "<body", "<head")))
    chk("㉕ U/I 六分頁都在", all(z in h for _, z in TABS) and h.count('data-p=') == 6)
    chk("㉖ U/I 色值只走 Atlas --vl-* 且兩主題都定義",
        h.count("--vl-") > 30 and "prefers-color-scheme" in h and 'data-theme="dark"' in h)
    hx = ui_html({**rep, "systems": [{**rep["systems"][0], "verdict_line": "<script>x</script>",
                                      "why": "<b>y</b>"}]})
    chk("㉗ U/I 逸出使用者內容", "<script>x</script>" not in hx and "&lt;script&gt;" in hx)
    chk("㉘ 末頁明說逐字原文不搬進可分享的頁面(含本機路徑 / 環境值)",
        "不進這一頁" in h and "外洩" in h)

    # ㉙ 盤冊 add-only
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        p1, s1 = write_book(rep, d)
        p2, s2 = write_book(rep, d)
        chk("㉙ 第一次寫 v0100;實質沒變 → UNCHANGED 不出新版號",
            s1 == "WRITTEN" and p1.name.endswith("v0100.json") and s2 == "UNCHANGED" and p2 == p1)
        rep2 = {**rep, "systems": [{**rep["systems"][0], "lamp": "RED"}]}
        p3, s3 = write_book(rep2, d)
        chk("㉚ 實質變了 → 出 v0101,不覆寫 v0100",
            s3 == "WRITTEN" and p3.name.endswith("v0101.json") and p1.is_file())

    # ㉛ 禁令:不裝件 · 不代設同意閘(AST 檢,不用會自我誤判的字面檢)
    import ast as _ast
    tree = _ast.parse(Path(__file__).read_text(encoding="utf-8"))
    wrote_env = [1 for n in _ast.walk(tree)
                 if isinstance(n, _ast.Assign)
                 and any(isinstance(t, _ast.Subscript) and isinstance(t.value, _ast.Attribute)
                         and t.value.attr == "environ" for t in n.targets)]
    chk("㉛ 不代設同意閘(AST:沒有一處寫 os.environ[...])", not wrote_env)
    # ㉜ 改成「資料驅動」的檢:只准設入口旗標,不准設任何同意閘。
    #    原本寫成「掃原始碼有沒有出現 VIA_NET_CONSENT 這個字串」—— 必紅,
    #    因為那個檢查式自己就含有這個字串。**掃檔案找某個字的檢查,自己不能含那個字**
    #    (這類自我誤判今天第三次了:技能引擎兩次、這裡一次,所以改成檢資料不檢文字)。
    keys = sorted({k for s in SYSTEMS for k in (s.get("env") or {})})
    chk("㉜ SYSTEMS 的 env 只設入口旗標 VIA_FROM_*,沒有任何 *_CONSENT",
        keys and all(k.startswith("VIA_FROM_") for k in keys)
        and not any("CONSENT" in k for k in keys), keys)
    chk("㉜b 入口旗標的值只有 YES(不夾帶別的設定)",
        {v for s in SYSTEMS for v in (s.get("env") or {}).values()} <= {"YES"})
    shells = [n for n in _ast.walk(tree) if isinstance(n, _ast.keyword)
              and n.arg == "shell" and getattr(n.value, "value", False) is True]
    chk("㉜c 派子行程不走 shell(shell=True 一處都沒有)", not shells)
    imported = {a.name.split(".")[0] for n in _ast.walk(tree) if isinstance(n, _ast.Import)
                for a in n.names}
    chk("㉝ 不碰 TA-Lib", not {"talib", "ta_lib"} & imported, sorted(imported))

    print(f"[計] {TAG} 自測 OK {ok} · FAIL {fail} · {'PASS' if fail == 0 else 'FAIL'}")
    return 0 if fail == 0 else 1


# ───────────────────────── 入口 ─────────────────────────
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog=TAG)
    ap.add_argument("verb", nargs="?", default="run", choices=["run", "plan", "ui", "header"])
    ap.add_argument("--only", default="")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(list(sys.argv[1:] if argv is None else argv))
    if a.selftest:
        return selftest()

    if a.verb == "header":
        for h in all_headers():
            print()
            for ln in h["lines"]:
                print(ln)
        return 0
    if a.verb == "plan":
        print(f"[{TAG}] 次序 " + " → ".join(s["code"] for s in SYSTEMS)
              + "(各走自己的入口;上游紅不擋下游)")
        for s in SYSTEMS:
            p = resolve_entry(s)
            print(f"  {s['code']:5} {('✔ ' + str(p.relative_to(VIA))) if p else '✘ 入口不在'}"
                  f"  {' '.join(s['argv'])}  逾時 {s['timeout']}s")
        return 0

    only = [x.strip().upper() for x in a.only.split(",") if x.strip()] or None
    rep = run_chain(only)
    print(f"[{TAG}] 總燈 {rep['chain_lamp']} · " + " → ".join(rep["order"])
          + " · " + json.dumps(rep["counts"], ensure_ascii=False))
    for r in rep["systems"]:
        print(f"  [{r['lamp']:6}] {r['code']:5} rc={r['rc']} {r['elapsed_s']:>7}s  "
              f"{r['verdict_line'][:110] or '(沒印判決行)'}")
        if r["lamp"] != "GREEN":
            print(f"            └ {r['why'][:160]}")
    if a.verb == "ui" or a.apply:
        out = HERE / UI_NAME
        out.write_text(ui_html(rep), encoding="utf-8")
        print(f"  [U/I] {out}")
    if a.apply:
        p, st = write_book(rep)
        print(f"  [盤冊] {st} {p.name}")
    return 0 if rep["chain_lamp"] in ("GREEN", "YELLOW") else 1


if __name__ == "__main__":
    sys.exit(main())
