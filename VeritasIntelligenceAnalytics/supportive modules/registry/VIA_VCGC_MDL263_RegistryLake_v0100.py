#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_VCGC_MDL263_RegistryLake v0100 — 註冊總帳入湖:一切資料 · 資訊 · 輸入 · 輸出 · 參數 · 日期的註冊紀錄存成 Parquet + HTML U/I。

操作員 2026-11-16:「一切資料資訊輸入輸出參數日期都要註冊且有註冊紀錄 parquet 儲存 繼續完成 跳出 HTML U/I 給我看」。
做法(只讀他系統的冊 · 只寫 VCGC 自己的湖與報表夾;L123):
  ① 收:中央號冊 VIA_NumberBooks/*.jsonl(每一列 = 一個已發號的東西)· VIA_Numbering_SSOT rows(SSOT 冊 · 正則 · 同義字)·
        各系統參數列管冊尾版(VDF / VRN 的 *_ParamControl_SSOT;輸入參數 / 輸出參數 / 時間範圍 · 可動 / 不可動)·
        VQG 指標登錄冊尾版(指標 · 輸入欄位 · 時間參數)· 擷取資料矩陣(擷取目標 · 商品代號 · 來源)·
        註冊收據帳 VIA_RegistrationReceipts(到分鐘的註冊時間 · 位元組 · 格式 · sha256)。
  ② 分:每列給一個角色 role —— input 輸入 · output 輸出 · parameter 參數 · date 日期 / 時間範圍 · data 資料欄位 / 指標 ·
        instrument 金融商品 · source 資料來源 · code 程式(模組 / 引擎 / 函式 / 類別)· governance 治理(政策 / 需求 / 工作流 / 冊)。
        名字 / 鍵 / 路徑帶日期字樣(date · 日期 · 起始 · 期間 · start · end · as-of …)的參數一律另記 date。
  ③ 驗:每列要有 號(code 或冊上 id)· 註冊時間 · 版本 · 來源;缺哪一項照實記 missing(不補、不猜)。
  ④ 存:經五系統共用套件 VIA_ParquetLake(增量 Parquet · zstd · manifest 只增 · 同主鍵不重入 · DuckDB 管家 VIEW)寫進
        <湖根>/VCGC/registry_items · registry_receipts · registry_runs;湖根預設 VIA_Reports/lake(VIA_DATA_HOME 有設就用它)。
  ⑤ 看:VIA_Reports/registry_lake/REGISTRY_LAKE_latest.html(角色 × 系統矩陣 · 燈號最前 · 缺漏清單 · 可搜尋明細)+ 同名 .json。
用法:python <本檔> build [--root <湖根>] [--no-lake] · status · --selftest
零網路 · 不用 TA-Lib · 不寫同意閘 · 不裝套件(缺 pyarrow / duckdb = ABSENT rc 3,照實說)。
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

import html
import importlib.util
import json
import os
import re
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0100"
ENGINE = "VIA_VCGC_MDL263_RegistryLake " + VERSION
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REG = VIA / "supportive modules" / "registry"
ROLES = ("input", "output", "parameter", "date", "data", "instrument", "source", "code", "governance")
ROLE_ZH = {"input": "輸入", "output": "輸出", "parameter": "參數", "date": "日期 / 時間範圍", "data": "資料欄位 / 指標",
           "instrument": "金融商品", "source": "資料來源", "code": "程式", "governance": "治理"}
KIND_ROLE = {"PRMT": "parameter", "ENV": "parameter", "OPT": "parameter", "LGC": "parameter",
             "FD": "data", "MRC": "data", "BI": "data", "IDX": "data", "FAC": "data", "XSRC": "source", "SRC": "source",
             "FM": "instrument", "MDL": "code", "ENG": "code", "FNC": "code", "CLS": "code", "LIB": "code", "TOOL": "code", "TST": "code",
             "PLCY": "governance", "REQ": "governance", "WKF": "governance", "STP": "governance", "SSOT": "governance",
             "RGX": "governance", "SYN": "governance"}
DATE_RX = re.compile(r"(?i)(\bdate\b|_date|date_|\bdt\b|start|end_?date|\bperiod|as[-_ ]?of|\bts\b|timestamp|year|month|quarter|"
                     r"日期|起始|起日|迄|期間|時間範圍|年度|季度|月份|時點|交易日|基準日)")
REQUIRED = ("code", "registered_at", "version", "source")


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d{4})\.\w+$", p.name)
    return int(m.group(1)) if m else -1


def _tail(folder: Path, stem: str, ext: str = "json") -> Path | None:
    c = [p for p in folder.glob(stem + "_v*." + ext) if _vnum(p) >= 0]
    return max(c, key=_vnum) if c else None


def _utc(raw) -> str | None:
    """各冊的時間寫法不一(ISO Z · 'YYYY-MM-DD HH:MM +00:00' · 'YYYY-MM-DD HH:MM:SS +0000' · 只有日期)→ UTC ISO;認不得回 None(不猜)。"""
    if raw in (None, ""):
        return None
    s = str(raw).strip().replace("Z", "+00:00")
    s = re.sub(r"\s+([+-]\d{2}):?(\d{2})$", r"\1:\2", s)
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S%z", "%Y-%m-%d %H:%M%z", "%Y-%m-%dT%H:%M%z"):
        try:
            return datetime.strptime(s, fmt).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            pass
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s + "T00:00:00Z"
    return None


def _sys_of(code: str, source: str = "") -> str:
    m = re.match(r"VIA-([A-Z0-9]+)-", code or "")
    if m:
        return {"VRN2": "VRN"}.get(m.group(1), m.group(1))
    for s in ("VDF", "VRN", "VQG", "VAP"):
        if "/%s/" % s in "/" + (source or ""):
            return s
    return "VCGC"


def _row(origin, code, name, role, *, system=None, kind="", source="", version="", registered=None, key="", cls="", value=None, mutable=None):
    r = {"reg_id": "%s|%s" % (origin, code or key or name), "origin": origin, "system": system or _sys_of(code, source), "kind": kind,
         "role": role, "code": code or "", "name": str(name or "")[:300], "source": source or "", "version": version or "",
         "registered_raw": "" if registered is None else str(registered), "registered_at": _utc(registered), "key": key or "",
         "class": cls or "", "value": None if value is None else json.dumps(value, ensure_ascii=False, default=str)[:500], "mutable": mutable}
    r["missing"] = ",".join(f for f in REQUIRED if not r.get(f))
    return r


def _role_with_date(role: str, *texts) -> list[str]:
    roles = [role]
    if role in ("parameter", "input", "output", "data") and any(DATE_RX.search(str(t or "")) for t in texts):
        roles.append("date")
    return roles


# ───────────────────────────────── ① 收
def collect(via: Path = VIA) -> tuple[list[dict], list[dict], list[str]]:
    reg = via / "supportive modules" / "registry"
    rows, receipts, notes = [], [], []
    # 中央號冊
    for f in sorted((reg / "VIA_NumberBooks").glob("VIA_NumberBook_*_v*.jsonl")):
        kind = f.name.split("VIA_NumberBook_")[1].split("_")[0]
        base = KIND_ROLE.get(kind, "governance")
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            x = json.loads(line)
            if kind in ("FNC", "CLS"):            # 精簡列:函式 / 類別(版本 · 時間跟著模組列)
                rows.append(_row("numberbook:" + kind, x.get("code"), x.get("q"), "code", kind=kind, source=x.get("api", ""),
                                 version="(隨模組)", registered="(隨模組)", key=x.get("q", "")))
                rows[-1]["registered_at"] = None
                rows[-1]["missing"] = ""             # 精簡列照號冊規格不帶時間 · 版本(模組列帶),不算缺
                continue
            for role in _role_with_date(base, x.get("name"), x.get("key"), x.get("api")):
                rows.append(_row("numberbook:" + kind, x.get("code"), x.get("name"), role, kind=kind, source=x.get("source", ""),
                                 version=x.get("version", ""), registered=x.get("numbered_at") or x.get("updated_at"),
                                 key=x.get("key", ""), cls=x.get("cat", "")))
    # Numbering SSOT 列
    ns = reg / "VIA_Numbering_SSOT_v0100.json"
    if ns.exists():
        d = json.loads(ns.read_text(encoding="utf-8"))
        for kind, lst in (d.get("rows") or {}).items():
            for x in lst:
                rows.append(_row("numbering_ssot:" + kind, x.get("code"), x.get("name"), KIND_ROLE.get(kind, "governance"), kind=kind,
                                 source=x.get("source", ""), version=x.get("version", ""),
                                 registered=x.get("numbered_at") or x.get("updated_at"), key=x.get("key", ""), cls=x.get("cat", "")))
    # 參數列管冊(各系統自己的冊;只讀)
    cls_role = {"輸入參數": "input", "輸出參數": "output", "時間範圍": "date", "時間參數": "date", "日期": "date"}
    for sysname, folder, stem in (("VDF", via / "functional modules" / "VDF", "VDF_ParamControl_SSOT"),
                                  ("VRN", via / "functional modules" / "VRN", "VRN_ParamControl_SSOT")):
        t = _tail(folder, stem)
        if not t:
            notes.append("%s 參數列管冊不在" % sysname)
            continue
        d = json.loads(t.read_text(encoding="utf-8"))
        for x in d.get("params") or []:
            role = next((v for k, v in cls_role.items() if k in str(x.get("class", ""))), "parameter")
            for rl in _role_with_date(role, x.get("name"), x.get("path")) if role != "date" else ["date"]:
                rows.append(_row("paramcontrol:" + sysname, x.get("id"), x.get("name"), rl, system=sysname, kind="PAR",
                                 source="%s#%s" % (x.get("book", ""), x.get("path", "")), version=x.get("version", ""),
                                 registered=x.get("registered_at"), cls=x.get("class", ""), value=x.get("value"), mutable=x.get("mutable")))
    # VQG 指標登錄冊(VQG 自己的冊;只讀)
    t = _tail(via / "functional modules" / "VQG", "VQG_IndicatorRegister_SSOT")
    if t:
        d = json.loads(t.read_text(encoding="utf-8"))
        ver, when = d.get("version", ""), d.get("issued_at")
        for x in d.get("entries") or []:
            k = str(x.get("kind", "indicator"))
            role = "input" if k.startswith("input") else "data"
            code = x.get("vqg_no") or x.get("code") or x.get("stable_id")
            rows.append(_row("vqg_register", code, x.get("name_zh") or x.get("name_en") or x.get("stable_id"), role, system="VQG",
                             kind=k.upper()[:12], source=t.name, version=x.get("version") or ver, registered=x.get("registered_at") or when,
                             key=x.get("stable_id", ""), cls=x.get("category", "")))
            if x.get("time_params"):
                rows.append(_row("vqg_register:time", code, "%s · 時間參數" % (x.get("name_zh") or x.get("stable_id")), "date", system="VQG",
                                 kind="TIME", source=t.name, version=x.get("version") or ver, registered=x.get("registered_at") or when,
                                 key=x.get("stable_id", ""), value=x.get("time_params")))
    else:
        notes.append("VQG 指標登錄冊不在")
    # 擷取資料矩陣(VCGC 登錄)
    t = _tail(reg, "VIA_SSOT_FetchTargetMatrix_SSOT")
    if t:
        d = json.loads(t.read_text(encoding="utf-8"))
        ver, when = d.get("version", ""), d.get("ts")
        for x in d.get("rows") or []:
            rows.append(_row("fetch_target", x.get("no"), "%s · %s" % (x.get("item", ""), x.get("target", "")), "input", system="VCGC",
                             kind="FTM", source=t.name, version=ver, registered=when, cls=x.get("major", ""), value=x.get("frequency")))
        for x in d.get("symbols") or []:
            rows.append(_row("fetch_target:symbol", x.get("no"), x.get("symbol"), "instrument", system="VCGC", kind="FTM-S",
                             source=t.name, version=ver, registered=when, cls=x.get("kind", ""), value=x.get("dedupe")))
        for x in d.get("sources") or []:
            rows.append(_row("fetch_target:source", x.get("no"), x.get("key"), "source", system="VCGC", kind="FTM-SRC",
                             source=t.name, version=ver, registered=when))
    # 註冊收據帳(到分鐘)
    rc = reg / "VIA_RegistrationReceipts_v0100.jsonl"
    if rc.exists():
        for line in rc.read_text(encoding="utf-8").splitlines():
            if line.strip():
                x = json.loads(line)
                x["registered_utc"] = _utc(x.get("registered_at"))
                receipts.append(x)
    return rows, receipts, notes


# ───────────────────────────────── ③ 驗 + 矩陣
def matrix(rows: list[dict]) -> dict:
    cell = defaultdict(lambda: {"n": 0, "missing": 0, "with_time": 0})
    systems = sorted({r["system"] for r in rows})
    for r in rows:
        c = cell[(r["role"], r["system"])]
        c["n"] += 1
        c["missing"] += 1 if r["missing"] else 0
        c["with_time"] += 1 if r["registered_at"] else 0
    out = {}
    for (role, s), c in cell.items():
        c["lamp"] = "GREEN" if c["missing"] == 0 else ("YELLOW" if c["missing"] < c["n"] else "RED")
        out["%s|%s" % (role, s)] = c
    return {"systems": systems, "cells": out}


def summarize(rows, receipts, notes) -> dict:
    by_role = Counter(r["role"] for r in rows)
    miss = [r for r in rows if r["missing"]]
    lamp = "GREEN" if rows and not miss else ("YELLOW" if rows else "GRAY")
    return {"engine": ENGINE, "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "lamp": lamp,
            "rows": len(rows), "by_role": dict(by_role), "missing_rows": len(miss),
            "missing_by_field": dict(Counter(f for r in miss for f in r["missing"].split(",") if f)),
            "receipts": len(receipts), "notes": notes, "matrix": matrix(rows)}


# ───────────────────────────────── ④ 存
def _lake_mod(via: Path):
    c = [p for p in (via / "supportive modules").glob("VIA_ParquetLake_v*.py") if _vnum(p) >= 0]
    if not c:
        return None
    p = max(c, key=_vnum)
    spec = importlib.util.spec_from_file_location("via_parquet_lake_for_mdl263", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def lake_root(via: Path = VIA) -> Path:
    home = os.environ.get("VIA_DATA_HOME")
    return Path(home) / "lake" if home else via / "VIA_Reports" / "lake"


def store(rows, receipts, summary, root: Path, via: Path = VIA) -> dict:
    mod = _lake_mod(via)
    if mod is None:
        return {"state": "ABSENT", "why": "VIA_ParquetLake 不在"}
    try:
        lake = mod.Lake(root, "VCGC")
        a = lake.append("registry_items", rows, ["reg_id", "role"])
        b = lake.append("registry_receipts", receipts, ["uuid"]) if receipts else {"added": 0, "skipped": 0}
        run = {"run_at": summary["at"], "engine": ENGINE, "rows": summary["rows"], "missing_rows": summary["missing_rows"],
               "by_role": summary["by_role"], "receipts": summary["receipts"], "lamp": summary["lamp"]}
        c = lake.append("registry_runs", [run], ["run_at"])
        return {"state": "OK", "root": str(root), "items": a, "receipts": b, "runs": c, "status": lake.status()}
    except ImportError as exc:
        return {"state": "ABSENT", "why": "缺套件:%s(不代裝)" % exc}


# ───────────────────────────────── ⑤ 看
def _esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


def render(summary: dict, rows: list[dict], lake: dict) -> str:
    m = summary["matrix"]
    systems = m["systems"]
    lamp_cls = {"GREEN": "g", "YELLOW": "y", "RED": "r", "GRAY": "n"}
    head = "".join("<th>%s</th>" % _esc(s) for s in systems)
    body = []
    for role in ROLES:
        tds = []
        for s in systems:
            c = m["cells"].get("%s|%s" % (role, s))
            if not c:
                tds.append('<td class="n">—</td>')
            else:
                tds.append('<td class="%s" title="缺 %d · 帶時間 %d">%d%s</td>' % (lamp_cls[c["lamp"]], c["missing"], c["with_time"], c["n"],
                           (' <small>缺 %d</small>' % c["missing"]) if c["missing"] else ""))
        body.append("<tr><th>%s <small>%s</small></th>%s</tr>" % (_esc(ROLE_ZH[role]), role, "".join(tds)))
    # 明細:非程式列全給(程式列太多,只給模組 / 引擎)
    show = [r for r in rows if r["role"] != "code" or r["kind"] in ("MDL", "ENG")]
    data = [[r["role"], r["system"], r["kind"], r["code"], r["name"], r["version"], r["registered_at"] or "", r["source"], r["missing"]] for r in show]
    miss = Counter((r["role"], f) for r in rows if r["missing"] for f in r["missing"].split(","))
    misshtml = "".join("<li>%s · 缺 <b>%s</b> · %d 列</li>" % (_esc(ROLE_ZH[a]), _esc(b), n) for (a, b), n in miss.most_common()) or "<li>無</li>"
    lk = lake or {}
    lakehtml = ("<b>%s</b> · 湖根 <code>%s</code> · items +%s(略過重複 %s)· 收據 +%s · 本輪 run 1 列" % (
        _esc(lk.get("state")), _esc(lk.get("root", "")), _esc((lk.get("items") or {}).get("added")), _esc((lk.get("items") or {}).get("skipped")),
        _esc((lk.get("receipts") or {}).get("added")))) if lk.get("state") == "OK" else "<b>%s</b> %s" % (_esc(lk.get("state", "未寫")), _esc(lk.get("why", "")))
    roles_line = " · ".join("%s %d" % (ROLE_ZH[k], summary["by_role"].get(k, 0)) for k in ROLES)
    return TEMPLATE.replace("@LAMP@", summary["lamp"]).replace("@LAMPCLS@", lamp_cls[summary["lamp"]]).replace("@AT@", _esc(summary["at"])) \
        .replace("@ROWS@", str(summary["rows"])).replace("@MISS@", str(summary["missing_rows"])).replace("@RCPT@", str(summary["receipts"])) \
        .replace("@ROLES@", _esc(roles_line)).replace("@HEAD@", head).replace("@BODY@", "".join(body)).replace("@MISSLIST@", misshtml) \
        .replace("@LAKE@", lakehtml).replace("@ENGINE@", _esc(ENGINE)).replace("@NOTES@", _esc(" · ".join(summary["notes"]) or "無")) \
        .replace("@DATA@", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))


TEMPLATE = """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>註冊總帳入湖</title><style>
:root{--bg:#f7f8fa;--fg:#1d2330;--mut:#5b6475;--card:#fff;--line:#dfe3ea;--g:#e3f4e8;--gf:#17663a;--y:#fff4d6;--yf:#8a5a00;--r:#fde4e4;--rf:#a12020;--n:#f0f1f4}
@media (prefers-color-scheme:dark){:root{--bg:#12151b;--fg:#e6e9ef;--mut:#9aa3b2;--card:#1b1f27;--line:#2c3340;--g:#173524;--gf:#7fd8a1;--y:#3a2f12;--yf:#f1c96b;--r:#3d1a1a;--rf:#f19a9a;--n:#20252e}}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,"Noto Sans TC",sans-serif}
.w{max-width:1200px;margin:0 auto;padding:16px}h1{font-size:20px;margin:0 0 4px}.mut{color:var(--mut)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin:12px 0;overflow-x:auto}
.lamp{display:inline-block;padding:2px 10px;border-radius:99px;font-weight:700}.g{background:var(--g);color:var(--gf)}.y{background:var(--y);color:var(--yf)}
.r{background:var(--r);color:var(--rf)}.n{background:var(--n);color:var(--mut)}
table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
#mx td{text-align:center;font-variant-numeric:tabular-nums}.kpi{display:flex;flex-wrap:wrap;gap:10px}.kpi div{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 12px}
.kpi b{font-size:18px;display:block}input,select{font:inherit;padding:6px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg)}
#dt td{font-size:12px;word-break:break-all}code{font-size:12px}
</style></head><body><div class="w">
<h1>註冊總帳入湖 <span class="lamp @LAMPCLS@">@LAMP@</span></h1>
<div class="mut">@ENGINE@ · @AT@ · 一切資料 / 輸入 / 輸出 / 參數 / 日期:有號 · 有註冊時間 · 有版本 · 有來源;Parquet 只增入湖</div>
<div class="kpi" style="margin-top:10px"><div><span class="mut">已註冊列</span><b>@ROWS@</b></div><div><span class="mut">缺註冊欄位的列</span><b>@MISS@</b></div>
<div><span class="mut">註冊收據(到分鐘)</span><b>@RCPT@</b></div></div>
<div class="card"><b>Parquet 湖</b><br>@LAKE@</div>
<div class="card"><b>角色 × 系統</b> <span class="mut">(數字 = 列數;綠 = 每列都有號 · 時間 · 版本 · 來源;黃 = 有缺)</span>
<table id="mx"><tr><th>角色</th>@HEAD@</tr>@BODY@</table><div class="mut" style="margin-top:6px">@ROLES@</div></div>
<div class="card"><b>缺漏(照實記,不補不猜)</b><ul>@MISSLIST@</ul><div class="mut">備註:@NOTES@ · 函式 / 類別精簡列依號冊規格不帶時間版本(隨模組列),不算缺。</div></div>
<div class="card"><b>明細</b> <span class="mut">(函式 / 類別列太多,只在 Parquet;這裡列其餘全部)</span><div style="margin:8px 0;display:flex;gap:8px;flex-wrap:wrap">
<input id="q" placeholder="搜尋 號 / 名稱 / 來源" style="flex:1;min-width:200px"><select id="fr"><option value="">全部角色</option></select>
<select id="fs"><option value="">全部系統</option></select><label><input type="checkbox" id="fm"> 只看有缺</label></div>
<div id="cnt" class="mut"></div><table id="dt"><thead><tr><th>角色</th><th>系統</th><th>類</th><th>號</th><th>名稱</th><th>版本</th><th>註冊時間 UTC</th><th>來源</th><th>缺</th></tr></thead><tbody></tbody></table></div>
</div><script>
const D=@DATA@;const tb=document.querySelector('#dt tbody'),q=document.getElementById('q'),fr=document.getElementById('fr'),fs=document.getElementById('fs'),fm=document.getElementById('fm');
[...new Set(D.map(r=>r[0]))].sort().forEach(v=>fr.add(new Option(v,v)));[...new Set(D.map(r=>r[1]))].sort().forEach(v=>fs.add(new Option(v,v)));
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function draw(){const t=q.value.toLowerCase();const out=D.filter(r=>(!fr.value||r[0]==fr.value)&&(!fs.value||r[1]==fs.value)&&(!fm.checked||r[8])&&(!t||(r[3]+' '+r[4]+' '+r[7]).toLowerCase().includes(t)));
document.getElementById('cnt').textContent=out.length+' 列'+(out.length>500?'(顯示前 500)':'');tb.innerHTML=out.slice(0,500).map(r=>'<tr>'+r.map(esc).map(x=>'<td>'+x+'</td>').join('')+'</tr>').join('')}
[q,fr,fs,fm].forEach(e=>e.addEventListener('input',draw));draw();
</script></body></html>"""


# ───────────────────────────────── CLI
def build(root: Path | None, no_lake: bool = False, out_dir: Path | None = None, via: Path = VIA) -> tuple[int, dict]:
    rows, receipts, notes = collect(via)
    summary = summarize(rows, receipts, notes)
    lake = {"state": "SKIPPED"} if no_lake else store(rows, receipts, summary, root or lake_root(via), via)
    summary["lake"] = {k: v for k, v in lake.items() if k != "status"}
    out = out_dir or (via / "VIA_Reports" / "registry_lake")
    out.mkdir(parents=True, exist_ok=True)
    (out / "REGISTRY_LAKE_latest.html").write_text(render(summary, rows, lake), encoding="utf-8")
    (out / "REGISTRY_LAKE_latest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    rc = 3 if lake.get("state") == "ABSENT" else (0 if summary["lamp"] == "GREEN" else 2)
    return rc, summary


def selftest() -> int:
    res = []

    def chk(name, ok, note=""):
        res.append(ok)
        print("  [%s] %s%s" % ("OK" if ok else "FAIL", name, (" · " + str(note)) if note and not ok else ""), flush=True)

    print("=== %s 自測 ===" % ENGINE, flush=True)
    chk("① 時間正規化:ISO Z · 'YYYY-MM-DD HH:MM +00:00' · 只有日期 → UTC;亂字 → None",
        _utc("2026-11-10 15:23 +00:00") == "2026-11-10T15:23:00Z" and _utc("2026-11-15T18:09:43Z") == "2026-11-15T18:09:43Z"
        and _utc("2026-11-14") == "2026-11-14T00:00:00Z" and _utc("昨天") is None)
    r = _row("t", "VIA-VDF-PRMT001", "start_date", "parameter", version="v0100", source="x.json", registered="2026-11-16T00:00:00Z")
    chk("② 完整列 missing 空;缺版本 → missing=version", r["missing"] == "" and
        _row("t", "VIA-VDF-PRMT002", "x", "parameter", source="x", registered="2026-11-16")["missing"] == "version")
    chk("③ 日期字樣的參數另記 date 角色(start_date · 起始日 · 期間);普通名不記", _role_with_date("parameter", "start_date") == ["parameter", "date"]
        and _role_with_date("parameter", "群組起始日") == ["parameter", "date"] and _role_with_date("parameter", "檔名協定") == ["parameter"])
    chk("④ 系統判定:號前綴 · VRN2 歸 VRN · 無號看來源路徑", _sys_of("VIA-VRN2-ENG001") == "VRN" and _sys_of("", "functional modules/VQG/a.json") == "VQG")
    rows, receipts, notes = collect(VIA)
    roles = {r["role"] for r in rows}
    chk("⑤ 真倉收集:號冊 + 參數列管 + VQG + 擷取矩陣 + 收據都有列", len(rows) > 1000 and {"parameter", "input", "output", "date", "instrument", "code"} <= roles
        and len(receipts) > 0, "roles %s · receipts %d" % (sorted(roles), len(receipts)))
    tmp = Path(tempfile.mkdtemp(prefix="mdl263_"))
    sample = rows[:200]
    lk = store(sample, receipts[:20], summarize(sample, receipts[:20], []), tmp / "lake", VIA)
    if lk.get("state") == "ABSENT":
        chk("⑥ 入湖(ABSENT = 缺套件,照實黃,不算過)", False, lk.get("why"))
    else:
        lk2 = store(sample, receipts[:20], summarize(sample, receipts[:20], []), tmp / "lake", VIA)
        chk("⑥ 入湖:第一次寫 200 列 · 第二次同主鍵全略過(只增不重入)· manifest 有紀錄",
            lk["items"]["added"] == 200 and lk2["items"]["added"] == 0 and lk2["items"]["skipped"] == 200
            and (tmp / "lake" / "VCGC" / "_manifest.jsonl").exists(), (lk.get("items"), lk2.get("items")))
    rc, s = build(tmp / "lake2", no_lake=True, out_dir=tmp / "out")
    page = (tmp / "out" / "REGISTRY_LAKE_latest.html").read_text(encoding="utf-8")
    chk("⑦ HTML:燈號 · 角色 × 系統矩陣 · 明細資料都在;不帶外部腳本", "角色 × 系統" in page and "const D=[" in page and "<script src" not in page)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 檔面:加速器橋 · 零網路字樣 · 不碰 TA-Lib · 不寫同意閘", "[VIA:ACCEL-BRIDGE:v0100]" in text
        and not re.search(r"^\s*(import|from)\s+(talib|requests|urllib)", text, re.M) and ("VIA_NET_" + "CONSENT=") not in text and ("VIA_SCRAPE_" + "CONSENT=") not in text)
    n = sum(res)
    print("[計] %s 自測 %d/%d %s" % (ENGINE, n, len(res), "PASS" if n == len(res) else "FAIL"), flush=True)
    return 0 if n == len(res) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if a[0] in ("--selftest", "selftest"):
        return selftest()
    if a[0] == "build":
        root = Path(a[a.index("--root") + 1]) if "--root" in a else None
        rc, s = build(root, no_lake="--no-lake" in a)
        lk = s.get("lake", {})
        print("[%s] build %s · 列 %d · 缺 %d · 收據 %d · 湖 %s · %s" % (ENGINE, s["lamp"], s["rows"], s["missing_rows"], s["receipts"],
              lk.get("state"), " · ".join("%s %d" % (ROLE_ZH[k], s["by_role"].get(k, 0)) for k in ROLES)), flush=True)
        print("  → VIA_Reports/registry_lake/REGISTRY_LAKE_latest.html", flush=True)
        return rc
    if a[0] == "status":
        mod = _lake_mod(VIA)
        print(json.dumps(mod.Lake(lake_root(VIA), "VCGC").status() if mod else {"state": "ABSENT"}, ensure_ascii=False, indent=1, default=str))
        return 0
    print("未知動詞:%s(build · status · --selftest)" % a[0])
    return 2


if __name__ == "__main__":
    sys.exit(main())
