#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0161 — 薄尾(操作員 2026-10-10):所有引擎都要有版號 · 文字 / 資訊區 / 財務報表三區分開擷取還原。
  engines [--version [--apply]] [--register]
     版號只認正規 [-_]v####(連字號 -v0100 也算;前版誤判);舊式版號換算(_v2_1 → v0201 · _V044 → v0044 · _v112 → v0112 · VRN_v139G_AllInOne → VRN_AllInOne_v0139);
     沒有的給 v0100;做法 = 新增正規版號複本(原檔不動,保留舊參照)→ registry\\VRN_EngineVersioning_Ledger.jsonl;_sha 副本殘檔不給版號(休眠候選)
  首頁資訊區辨識(不靠左右切欄):評等 / 目標價 / 收盤 / 52 週 / 市值 / 分析師 / 電郵 / 電話 等關鍵詞短塊 + 緊鄰的短數值 → INFO(長句留本文)
  layout 之後自動「三區分開擷取」:
     文字 = 首頁本文 + 年度頁本文(句 / 標題 / 條列)→ EXTRACT3_TEXT
     資訊區 = 代號 · 名稱 · 券商 · 日期 · 主標題 · 評等 · 目標價 · 收盤 · 分析師(名 · 職稱 · 電郵 · 電話 · 電郵券商)+ 資料庫對照 + 資訊區原文 → EXTRACT3_INFO
     財務報表 = 財務表 / 估值表逐格(列名 × 期間 · 原值 · 數值 · 單位 · 驗證過)→ EXTRACT3_FIN_CELLS
     各自 csv + parquet;每檔三欄頁(文字 | 資訊區 | 財務報表 各自亮燈);Memo 的資訊區、沒有年度頁的財報 = 灰(不適用)
其餘動詞照前版鏈。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0110] 正本加速器 VeritasCeleritas_v1141 · 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import sys as _cb_sys
from pathlib import Path as _cb_Path
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        for _cb_d in [_cb_sup] + [x.parent for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if str(_cb_d) not in _cb_sys.path:
                _cb_sys.path.insert(0, str(_cb_d))
        break
    _cb_p = _cb_p.parent
try:
    import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  正本加速器
except Exception:  # noqa: BLE001
    _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import csv
import datetime
import hashlib
import html
import importlib.util
import json
import os
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0161"


def _vnum_v0161(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0161(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0161(p) < _vnum_v0161(__file__)), key=_vnum_v0161)
PRIOR = _load_v0161(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name):
    import types
    mod, seen = PRIOR, set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if name in vars(mod):
            return mod
        mod = vars(mod).get("PRIOR")
    return None


def _resolve(name):
    m = _owner(name)
    return vars(m)[name] if m else None


def _job_entry(kind, item):
    return _resolve("_job")(kind, item)


def _init_entry(*args):
    return _resolve("_init_entry")(*args)


_home, _rep = _resolve("_home"), _resolve("_rep")
_ST = {}

# ───────── ① 所有引擎都要有版號:正規 [-_]v####;舊式換算;沒有的給 v0100(新增複本,原檔不動)─────────
_CANON = re.compile(r"[-_][vV]\d{4}$")


def legacy_version(stem: str):
    """回傳 (族名, 正規版號) 或 None。舊式:_v2 → v0200 · _v2_1 / _v2.2 → v0201 / v0202 · _v1.0 → v0100 · _V044 → v0044 · _v112 → v0112 · VRN_v139G_AllInOne → VRN_AllInOne v0139。"""
    if re.search(r"_sha[0-9a-f]{4,}|stub\d*R?$", stem):
        return None
    m = re.match(r"^(?P<a>.+?)_[vV](?P<n>\d{3})[A-Za-z](?P<b>_.+)$", stem)
    if m:
        return m["a"] + m["b"], "v%04d" % int(m["n"])
    m = re.match(r"^(?P<f>.+?)[-_][vV](?P<maj>\d+)(?:[._](?P<min>\d+))?$", stem)
    if m:
        maj, mi = int(m["maj"]), int(m["min"] or 0)
        return m["f"], ("v%04d" % maj) if maj >= 100 or (len(m["maj"]) == 3) else "v%02d%02d" % (maj, mi)
    return None


def version_plan(rows: list) -> list:
    home = _home()
    plan = []
    for r in rows:
        tail = Path(r["tail"])
        p = tail if tail.is_absolute() else home / tail
        if not p.exists() or str(p).startswith(str(Path(os.environ.get("USERPROFILE", "~")) / "Downloads")):
            continue
        if _CANON.search(p.stem):
            continue
        sep = "-" if (p.suffix.lower() == ".ps1" and "-" in p.stem) else "_"
        lv = legacy_version(p.stem)
        if re.search(r"_sha[0-9a-f]{4,}|stub\d*R?$", p.stem):
            plan.append({"src": str(p), "dst": "", "kind": "副本殘檔 → 休眠候選(不給版號)"})
            continue
        fam, ver, kind = (lv[0], lv[1], "舊式版號換算") if lv else (p.stem, "v0100", "沒有版號 → v0100")
        dst = p.with_name("%s%s%s%s" % (fam, sep, ver, p.suffix))
        plan.append({"src": str(p), "dst": str(dst), "kind": kind, "exists": dst.exists()})
    return plan


def version_apply(plan: list) -> dict:
    done, skip = [], 0
    for x in plan:
        if not x["dst"]:
            continue
        d = Path(x["dst"])
        if d.exists():
            skip += 1
            continue
        shutil.copy2(x["src"], d)
        done.append({"original": x["src"], "canonical": x["dst"], "kind": x["kind"], "sha8": hashlib.sha256(d.read_bytes()).hexdigest()[:8]})
    reg = _home() / "registry"
    reg.mkdir(exist_ok=True)
    led = reg / "VRN_EngineVersioning_Ledger.jsonl"
    with led.open("a", encoding="utf-8") as fh:
        for x in done:
            fh.write(json.dumps(dict(x, ts=datetime.datetime.now().isoformat(timespec="seconds"), rule="原檔不動(保留舊參照);正規版號複本為今後的正本"), ensure_ascii=False) + "\n")
    return {"copied": len(done), "skipped": skip, "ledger": led.name}


_PREV_EA = _resolve("engines_audit_v158")


def engines_audit_v161(register: bool = False) -> dict:
    o = _PREV_EA(register)
    home = _home()
    for r in o["rows"]:
        tail = Path(r["tail"])
        stem = tail.stem
        if _CANON.search(stem):
            r["version"], r["version_kind"] = True, "正規"
        elif legacy_version(stem):
            r["version"], r["version_kind"] = False, "舊式(%s)" % legacy_version(stem)[1]
        else:
            r["version"], r["version_kind"] = False, "沒有"
        ok = r["version"] and r["registered"] and r["accel"] and r.get("canon_accel", True) and r.get("net_canon", True)
        r["lamp"] = "GREEN" if ok else ("YELLOW" if r["accel"] else "RED")
    s = o["summary"]
    s["no_version"] = sum(1 for r in o["rows"] if not r["version"])
    s["legacy_version"] = sum(1 for r in o["rows"] if r.get("version_kind", "").startswith("舊式"))
    page = _resolve("_page")
    mark = lambda v: "✓" if v else "✗"  # noqa: E731
    order = {"RED": 0, "YELLOW": 1, "GREEN": 2}
    Path(o["html"]).write_text(page("VRN 引擎稽核 · 版號(正規 [-_]v####)· 註冊 · 加速器 · 正本", "族 %d · 沒正規版號 %d(其中舊式 %d)· 未註冊 %d · 接正本加速器 %s/%d · 修法:engines --version --apply --register(新增正規版號複本,原檔不動)" % (s["families"], s["no_version"], s["legacy_version"], s["not_registered"], s.get("canon_accel", "—"), s["families"]),
                                    ["族", "類", "尾版", "版數", "版號", "註冊", "加速器", "正本加速器", "管線用途"],
                                    [(r["lamp"], [r["family"], r["ext"], r["tail"], r["n"], "✓" if r["version"] else r.get("version_kind", "✗"), mark(r["registered"]), mark(r["accel"]), "✓" if r.get("canon_accel") else ("舊橋" if r.get("old_bridge") else "✗"), r["pipeline"]]) for r in sorted(o["rows"], key=lambda r: (order.get(r["lamp"], 9), r["family"]))]), encoding="utf-8")
    _ST["audit"] = o
    return o


_mo = _owner("engines_audit_v158")
if _mo:
    setattr(_mo, "engines_audit_v158", engines_audit_v161)


# ───────── ② 三區分開擷取還原:文字 / 資訊區 / 財務報表(各自資料集 · 各自燈 · 每檔三欄頁)─────────
def _is_memo(name: str) -> bool:
    return bool(re.search(r"(?i)memo|訪談速報", name)) or Path(name).suffix.lower() in (".docx", ".doc", ".txt", ".md")


def _period_header(rows: list):
    yr = _resolve("_YR158")
    for i in range(min(3, len(rows))):
        if yr and sum(1 for c in rows[i] if yr.search(c or "")) >= 2:
            return i
    return 0


def extract3(rows_l2: list, xc: dict) -> dict:
    pn = _resolve("parse_number")
    texts, infos, cells, files = [], [], [], []
    for r in rows_l2:
        if "cov_min" not in r or not r.get("temp_json") or not Path(r["temp_json"]).exists():
            continue
        full = json.loads(Path(r["temp_json"]).read_text(encoding="utf-8"))
        if full.get("run_id") != r.get("run_id"):
            continue                                                        # 只讀本輪 TEMP 結果
        fn, code = r["file"], r.get("code", "")
        t_n = 0
        for pg in full["pages"]:
            for b in pg["blocks"]:
                if b["kind"] == "text" and b["role"] == "BODY":
                    for k, (typ, txt) in enumerate(b.get("units", [])):
                        if txt.strip():
                            texts.append({"file": fn, "code": code, "page": pg["page"], "block": b["id"], "seq": k, "type": typ, "sub": b.get("sub", ""), "text": txt})
                            t_n += 1
        inf = r.get("info", {})
        x = xc.get(r["path"], {})
        kv = [("代號", code), ("名稱", r.get("name", "")), ("yfinance", r.get("yf", "")), ("Bloomberg", r.get("bbg", "")), ("券商(檔名)", r.get("broker", "")), ("券商(頁尾)", r.get("footer_broker", "")),
              ("報告日(檔名)", r.get("date", "")), ("報告日(首頁)", inf.get("date_p1", "")), ("主標題", r.get("title", "")), ("評等", inf.get("rating", "")), ("評等原文", inf.get("rating_raw", "")),
              ("目標價", inf.get("tp") or ""), ("目標價(剔除)", inf.get("tp_rejected") or ""), ("TP(adj)", x.get("tp_adj") or ""), ("收盤(首頁)", inf.get("close") or ""), ("收盤(剔除)", inf.get("close_rejected") or ""),
              ("報告日前收盤(DB)", x.get("close_before") or ""), ("報告日前 adj close(DB)", x.get("adj_before") or ""), ("最新 adj close(DB)", x.get("adj_latest") or "")]
        for i, a in enumerate(inf.get("analysts", []), 1):
            kv += [("分析師%d" % i, a.get("name") or a.get("name_from_email") or ""), ("分析師%d 職稱" % i, a.get("title", "")), ("分析師%d 電郵" % i, a.get("email", "")), ("分析師%d 電話" % i, a.get("tel", "")), ("分析師%d 電郵券商" % i, a.get("domain_broker", ""))]
        for k, v in kv:
            if v not in ("", None):
                infos.append({"file": fn, "code": code, "key": k, "value": str(v), "source": "首頁資訊區" if k.startswith(("評等", "目標", "收盤(首", "分析師", "報告日(首", "主標")) else ("資料庫" if "DB" in k or k == "TP(adj)" else "檔名 / 名冊")})
        for pg in full["pages"][:1]:
            for b in pg["blocks"]:
                if b["role"] == "INFO" and b["kind"] == "text":
                    raw_lines = [u[1] for u in b.get("units", [])] or [ln.get("text", "") if isinstance(ln, dict) else str(ln) for ln in b.get("lines", [])]
                    for txt in raw_lines:
                        if str(txt).strip():
                            infos.append({"file": fn, "code": code, "key": "資訊區原文", "value": str(txt).strip(), "source": b["id"]})
        f_ok = f_all = c_n = 0
        for pg in full["pages"]:
            for b in pg["blocks"]:
                if b["kind"] != "table" or not b.get("sub", "").startswith(("財務表", "估值表")):
                    continue
                f_all += 1
                ok = bool(b.get("verify", {}).get("ok"))
                f_ok += ok
                rows = b.get("rows", [])
                hi = _period_header(rows)
                hdr = rows[hi] if rows else []
                for ri, row in enumerate(rows[hi + 1:], hi + 1):
                    if not row or not row[0]:
                        continue
                    for j in range(1, len(row)):
                        raw = row[j]
                        if raw in ("", None):
                            continue
                        cells.append({"file": fn, "code": code, "page": pg["page"], "table": b["id"], "category": b["sub"], "unit": b.get("verify", {}).get("unit", ""), "row": ri, "label": row[0], "period": hdr[j] if j < len(hdr) else "",
                                      "raw": raw, "number": pn(raw), "verified": ok, "engine": b.get("engine", "")})
                        c_n += 1
        memo = _is_memo(fn)
        has_info = sum(1 for k in ("rating", "tp") if inf.get(k)) + (1 if inf.get("analysts") else 0)
        lam_t = "GREEN" if r.get("text_ok") and not r.get("sus") else ("YELLOW" if r.get("cov_min", 0) >= 99 else "RED")
        lam_i = "GRAY" if memo else ("GREEN" if has_info >= 3 else ("YELLOW" if has_info else "RED"))
        lam_f = "GRAY" if (not r.get("annual") and not f_all) else ("GREEN" if f_all and f_ok == f_all else ("YELLOW" if f_ok else "RED"))
        files.append({"file": fn, "code": code, "name": r.get("name", ""), "html": r.get("html", ""), "text": lam_t, "info": lam_i, "fin": lam_f, "n_text": t_n, "n_info": len([1 for x in infos if x["file"] == fn and x["key"] != "資訊區原文"]), "fin_tables": "%d/%d" % (f_ok, f_all), "n_cells": c_n, "memo": memo})
    out = _rep() / "extract3"
    out.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, data, cols in (("TEXT", texts, ["file", "code", "page", "block", "seq", "type", "sub", "text"]), ("INFO", infos, ["file", "code", "key", "value", "source"]),
                             ("FIN_CELLS", cells, ["file", "code", "page", "table", "category", "unit", "row", "label", "period", "raw", "number", "verified", "engine"])):
        p = out / ("EXTRACT3_%s_latest.csv" % name)
        with p.open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(data)
        paths[name] = str(p)
        try:
            import duckdb  # noqa: WPS433
            if data:
                duckdb.connect().execute("copy (select * from read_csv_auto('%s', header=true, all_varchar=true)) to '%s' (format parquet)" % (str(p).replace("'", "''"), str(p.with_suffix(".parquet")).replace("'", "''")))
                paths[name + "_parquet"] = str(p.with_suffix(".parquet"))
        except Exception:  # noqa: BLE001
            pass
    page = out / "EXTRACT3_latest.html"
    page.write_text(_page3(files), encoding="utf-8")
    for f in files:
        _file3(f, [t for t in texts if t["file"] == f["file"]], [i for i in infos if i["file"] == f["file"]], [c for c in cells if c["file"] == f["file"]], out)
    lam = lambda k, v: sum(1 for f in files if f[k] == v)  # noqa: E731
    s = {"files": len(files), "text_g": lam("text", "GREEN"), "info_g": lam("info", "GREEN"), "info_y": lam("info", "YELLOW"), "info_na": lam("info", "GRAY"), "fin_g": lam("fin", "GREEN"), "fin_y": lam("fin", "YELLOW"), "fin_r": lam("fin", "RED"), "fin_na": lam("fin", "GRAY"),
         "n_text": len(texts), "n_info": len(infos), "n_cells": len(cells), "n_cells_verified": sum(1 for c in cells if c["verified"]), "html": str(page), "paths": paths}
    _ST["x3"] = s
    return s


_L = {"GREEN": "var(--lamp-green,#16a34a)", "YELLOW": "var(--lamp-yellow,#eab308)", "RED": "var(--lamp-red,#dc2626)", "GRAY": "var(--lamp-gray,#9ca3af)"}
_CSS3 = ("body{font-family:'Microsoft JhengHei UI','Segoe UI',Arial;font-size:12px;color:#1f2937;background:#fafafa;margin:0;padding:12px}h1{font-size:15px;margin:0 0 6px}.meta{color:#6b7280;font-size:11px;margin-bottom:6px}"
         ".lp{display:inline-block;width:11px;height:11px;border-radius:50%;vertical-align:middle;margin-right:3px}.lp.RED{animation:bl 2.4s ease-in-out infinite}@keyframes bl{0%,100%{opacity:1}50%{opacity:.25}}"
         "table{border-collapse:collapse;width:100%;background:#fff;font-size:11.5px}th,td{border:1px solid #eceff3;padding:2px 5px;text-align:left;vertical-align:top}th{background:#111827;color:#fff;position:sticky;top:0}td.n{text-align:right}"
         ".three{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}@media(max-width:1000px){.three{grid-template-columns:1fr}}.pane{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:8px 10px;overflow-x:auto}.pane h2{font-size:13px;margin:0 0 6px}"
         ".u{margin:2px 0}.u .t{display:inline-block;background:#eef2ff;color:#3730a3;border-radius:4px;padding:0 4px;font-size:10px;margin-right:4px}.u.h{font-weight:700}.d{color:#6b7280;font-size:10.5px}")


def _lp(l):
    return "<i class='lp %s' style='background:%s'></i>" % (l, _L.get(l, "#9ca3af"))


def _page3(files: list) -> str:
    e = html.escape
    order = {"RED": 0, "YELLOW": 1, "GREEN": 2, "GRAY": 3}
    trs = "".join("<tr><td><a href='%s'>%s</a></td><td>%s %s</td><td>%s%d 單位</td><td>%s%d 項</td><td>%s%s 表 · %d 格</td></tr>" % (
        e(Path(f["file"]).stem[:40] + "_三區.html"), e(f["file"]), e(f["code"]), e(f["name"]), _lp(f["text"]), f["n_text"], _lp(f["info"]), f["n_info"], _lp(f["fin"]), e(f["fin_tables"]), f["n_cells"])
                  for f in sorted(files, key=lambda f: (min(order[f["text"]], order[f["info"]], order[f["fin"]]), f["file"])))
    return ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>三區分開擷取</title><style>" + _CSS3 + "</style></head><body>"
            "<h1>三區分開擷取還原 · 文字 / 資訊區 / 財務報表</h1><div class='meta'>文字 = 首頁本文 + 年度頁本文(句 / 標題 / 條列);資訊區 = 代號 · 名稱 · 券商 · 日期 · 評等 · 目標價 · 收盤 · 分析師(+ 資料庫對照);財務報表 = 財務表 / 估值表逐格(列名 × 期間 · 原值 · 數值 · 單位 · 是否驗證過)。"
            "灰 = 不適用(Memo 沒有評等 / 沒有年度財報頁)。點檔名看三欄頁。</div><table><thead><tr><th>檔</th><th>股票</th><th>文字</th><th>資訊區</th><th>財務報表</th></tr></thead><tbody>" + trs + "</tbody></table></body></html>")


def _file3(f: dict, texts: list, infos: list, cells: list, out: Path) -> None:
    e = html.escape
    tx = "".join("<div class='u%s'><span class='t'>P%s %s</span>%s</div>" % (" h" if t["type"] == "標題" else "", t["page"], e(t["type"]), e(t["text"])) for t in texts[:800]) or "<div class='d'>—</div>"
    kv = "".join("<tr><td>%s</td><td>%s</td><td class='d'>%s</td></tr>" % (e(i["key"]), e(i["value"]), e(i["source"])) for i in infos if i["key"] != "資訊區原文")
    raw = "".join("<div class='d'>%s</div>" % e(i["value"]) for i in infos if i["key"] == "資訊區原文")
    tabs = {}
    for c in cells:
        tabs.setdefault((c["page"], c["table"], c["category"], c["unit"], c["verified"]), []).append(c)
    fin = ""
    for (pg, tid, cat, unit, ok), cs in tabs.items():
        periods = []
        for c in cs:
            if c["period"] not in periods:
                periods.append(c["period"])
        grid = {}
        for c in cs:
            grid.setdefault((c["row"], c["label"]), {})[c["period"]] = c["raw"]
        fin += "<div style='margin:6px 0'>%s<b>%s</b> <span class='d'>%s · %s · P%s</span><table><tr><th>項目</th>%s</tr>%s</table></div>" % (_lp("GREEN" if ok else "YELLOW"), e(tid), e(cat), e(unit or "單位未標"), pg, "".join("<th>%s</th>" % e(p) for p in periods),
                                                                                                            "".join("<tr><td>%s</td>%s</tr>" % (e(lbl), "".join("<td class='n'>%s</td>" % e(v.get(p, "")) for p in periods)) for (ri, lbl), v in sorted(grid.items())))
    h = ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>" + e(f["file"]) + "</title><style>" + _CSS3 + "</style></head><body>"
         "<h1>" + e(f["file"]) + "</h1><div class='meta'>" + e("%s %s" % (f["code"], f["name"])) + " · 三區分開(文字 / 資訊區 / 財務報表)· <a href='" + e(Path(f["html"]).name) + "'>看版面頁</a></div><div class='three'>"
         "<div class='pane'><h2>" + _lp(f["text"]) + "文字(" + str(f["n_text"]) + " 單位)</h2>" + tx + "</div>"
         "<div class='pane'><h2>" + _lp(f["info"]) + "資訊區(" + str(f["n_info"]) + " 項)</h2><table><tr><th>項目</th><th>值</th><th>來源</th></tr>" + kv + "</table><div style='margin-top:6px'><b class='d'>資訊區原文</b>" + raw + "</div></div>"
         "<div class='pane'><h2>" + _lp(f["fin"]) + "財務報表(" + e(f["fin_tables"]) + " 表驗證過 · " + str(f["n_cells"]) + " 格)</h2>" + (fin or "<div class='d'>—(沒有財務表 / 估值表)</div>") + "</div></div></body></html>")
    (out / (Path(f["file"]).stem[:40] + "_三區.html")).write_text(h, encoding="utf-8")


# ───────── ②-0 首頁資訊區辨識(不靠左右切欄):關鍵詞短塊 + 緊鄰的短數值 → INFO(長句一律留本文)─────────
_INFO_KEY = re.compile(r"(?i)^\s*(?:投資評等|評等|投資建議|建議|目標價格?|收盤價?|股價|市值|股本|發行股數|52\s*[-‐]?\s*(?:週|周|Week|wk)|Rating|Recommendation|Price\s*target|Target\s*price|TP\b|Price\b|Close\b|Market\s*cap|Shares|Free\s*float|Bloomberg|Reuters|Analysts?\b|分析師|研究員|E-?mail|Tel\b|電話|Overweight|Underweight|Neutral|Buy\b|Hold\b|Sell\b|Outperform|Underperform|Equal-?weight|Not\s*Rated|買進|中立|持有|增加持股|減碼|賣出|逢低買進|未評等|區間操作)")
_INFO_CONTACT = re.compile(r"[\w.\-]+@[\w\-]+\.[\w.\-]+|\+?886[-\s]?\d|\(0\d\)\s?\d{3,4}|\b0\d[-\s]\d{4}[-\s]?\d{4}")
_INFO_VALUE = re.compile(r"^[\sA-Za-z$€¥¥%().,:/~\-–—+]*\d[\d\s$€¥%().,:/~\-–—+A-Za-z]{0,30}$")


def info_zone_fix(p: dict) -> int:
    blocks = [b for b in p.get("blocks", []) if b.get("kind") == "text" and b.get("role") == "BODY"]
    H = max([b["bottom"] for b in p.get("blocks", [])] or [800])
    n = 0
    keys = []
    for b in blocks:
        t = (b.get("text") or " ".join(ln.get("text", "") for ln in b.get("lines", []) if isinstance(ln, dict))).strip()
        if not t or b["top"] > 0.88 * H:
            continue
        if (len(t) <= 60 and _INFO_KEY.search(t)) or (len(t) <= 160 and _INFO_CONTACT.search(t) and len(b.get("lines", [])) <= 6):
            b["role"], b["sub"], b["info_by"] = "INFO", "資訊", "關鍵詞"
            keys.append(b)
            n += 1
    for b in blocks:
        if b["role"] != "BODY":
            continue
        t = (b.get("text") or "").strip()
        if not t or len(t) > 40 or not _INFO_VALUE.match(t):
            continue
        size = max(b.get("size") or 8, 6)
        for k in keys:
            near_v = -0.5 * size <= b["top"] - k["bottom"] <= 2.5 * size or abs(b["top"] - k["top"]) <= 0.8 * size
            near_h = b["x0"] < k["x1"] + 3 * size and b["x1"] > k["x0"] - 3 * size
            if near_v and near_h:
                b["role"], b["sub"], b["info_by"] = "INFO", "資訊", "鄰接數值"
                n += 1
                break
    p["info_fixed"] = n
    return n


_PREV_AP = _resolve("analyze_page")


def analyze_page_v161(pdf, pno: int, pdf_path: str, annual: bool, tabula_ok: bool) -> dict:
    p = _PREV_AP(pdf, pno, pdf_path, annual, tabula_ok)
    if not annual:
        info_zone_fix(p)
    return p


_ma = _owner("analyze_page")
if _ma:
    setattr(_ma, "analyze_page", analyze_page_v161)


_PREV_LAYOUT = _resolve("layout_run_v158")


def layout_run_v161(d, opts):
    o = _PREV_LAYOUT(d, opts)
    try:
        s = extract3(o["rows"], o["xc"])
        o["pages"]["extract3"] = s["html"]
    except Exception as exc:  # noqa: BLE001
        _ST["x3"] = {"err": "%s:%s" % (type(exc).__name__, str(exc)[:100])}
    return o


_ml = _owner("layout_run_v158")
if _ml:
    setattr(_ml, "layout_run_v158", layout_run_v161)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["engines"]:
        o = engines_audit_v161(register=False)
        if "--version" in args:
            plan = version_plan(o["rows"])
            todo = [x for x in plan if x["dst"] and not x.get("exists")]
            print("[計] 版號計畫 · 要補 %d(舊式換算 %d · 沒有 → v0100 %d)· 副本殘檔不給版號 %d · %s" % (len(todo), sum(1 for x in todo if x["kind"].startswith("舊式")), sum(1 for x in todo if x["kind"].startswith("沒有")), sum(1 for x in plan if not x["dst"]), "套用" if "--apply" in args else "只列(加 --apply 才寫)"))
            for x in todo[:12]:
                print("[計] 版號 · %s → %s(%s)" % (Path(x["src"]).name, Path(x["dst"]).name, x["kind"]))
            if "--apply" in args:
                res = version_apply(plan)
                print("[計] 版號套用 · 新增正規版號複本 %d · 已在 %d · 原檔不動 · 帳 %s" % (res["copied"], res["skipped"], res["ledger"]))
                o = engines_audit_v161(register="--register" in args)
        elif "--register" in args:
            o = engines_audit_v161(register=True)
        s = o["summary"]
        print("[計] VRN 引擎稽核 · 族 %d · 沒正規版號 %d(舊式 %d)· 未註冊 %d · 接正本加速器 %s/%d · 註冊冊 %s" % (s["families"], s["no_version"], s.get("legacy_version", 0), s["not_registered"], s.get("canon_accel", "—"), s["families"], s.get("register") or "未寫(加 --register)"))
        print("  [U/I] %s" % o["html"])
        return 0
    rc = PRIOR.main(args)
    if args[:1] == ["layout"]:
        x = _ST.get("x3") or {}
        if x.get("err"):
            print("[計] 三區分開擷取 · 失敗 %s" % x["err"])
        elif x:
            print("[計] 三區分開擷取 · 檔 %d · 文字 綠 %d · 資訊區 綠 %d 黃 %d(Memo 不適用 %d)· 財務報表 綠 %d 黃 %d 紅 %d(不適用 %d)· 文字 %d 單位 · 資訊 %d 項 · 財報 %d 格(驗證過 %d)" % (
                x["files"], x["text_g"], x["info_g"], x["info_y"], x["info_na"], x["fin_g"], x["fin_y"], x["fin_r"], x["fin_na"], x["n_text"], x["n_info"], x["n_cells"], x["n_cells_verified"]))
            print("  [U/I] %s" % x["html"])
    return rc


_CACHES = ("_ML_CACHE", "_ENG", "_E394", "_PX", "_CLS", "_CTX", "_ACC", "_TCACHE", "_TR", "_CB", "_LAST", "_NM")


def _reset_chain_caches() -> int:
    """自測順序隔離:鏈上模組層級快取(ENG394 綁定 · 價格來源 · 分類器 · 名冊 …)清空,避免前一段測試的臨時目錄汙染下一段。"""
    import types
    n, mod, seen = 0, PRIOR, set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        for k in _CACHES:
            v = vars(mod).get(k)
            if isinstance(v, dict) and v:
                v.clear()
                n += 1
        mod = vars(mod).get("PRIOR")
    _ST.clear()
    return n


def selftest() -> int:
    import tempfile
    skip_prior = os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1"
    prc = 0
    if not skip_prior:
        print("  ── 前版鏈自測(v0159 以前 · 先跑 · 快取隔離)──")
        _reset_chain_caches()
        try:
            prc = PRIOR.PRIOR.selftest()
        except Exception as exc:  # noqa: BLE001
            prc = 1
            print("  [前版鏈中斷] %s: %s(多半是環境:測試要讀本機名冊 / 字典)" % (type(exc).__name__, str(exc)[:120]))
        print("  ── v0160 自身自測(前版已跑 → 跳過其前版 · 快取隔離)──")
        _reset_chain_caches()
        os.environ["VIA_SKIP_PRIOR_SELFTEST"] = "1"
        try:
            prc = PRIOR.selftest() or prc
        except Exception as exc:  # noqa: BLE001
            prc = 1
            print("  [v0160 自測中斷] %s: %s" % (type(exc).__name__, str(exc)[:120]))
        finally:
            os.environ.pop("VIA_SKIP_PRIOR_SELFTEST", None)
        _reset_chain_caches()
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    chk("① 舊式版號換算:v2_1→v0201 · V044→v0044 · v139G→v0139 · _sha 殘檔不給", legacy_version("VRN_Finalize_AIO_v2_1") == ("VRN_Finalize_AIO", "v0201") and legacy_version("VRN_FINANCIAL_TRUST_POLISH_V044")[1] == "v0044" and legacy_version("VRN_v139G_AllInOne") == ("VRN_AllInOne", "v0139") and legacy_version("panorama_xcheck_v110_shaa9stub110R") is None)
    td = Path(tempfile.mkdtemp(prefix="vrn161-"))
    home = td / "functional modules" / "VRN"
    for d in ("SSOT", "knowledge", "registry", "engine", "intake/VRN_TableRepair"):
        (home / d).mkdir(parents=True, exist_ok=True)
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_SSOT_HOME", "VIA_VRN_HEALTH_OUT", "VIA_VDF_HOME", "VIA_ROOTS_BASE", "VIA_SPILL_DIR", "VIA_DB_ROOT", "USERPROFILE")}
    os.environ.update({"VIA_VRN_SSOT_HOME": str(home), "VIA_VRN_HEALTH_OUT": str(td / "VIA_Reports" / "vrn"), "VIA_VDF_HOME": str(td / "nope"), "VIA_ROOTS_BASE": str(td / "VIA"), "VIA_SPILL_DIR": str(td / "TEMP"), "VIA_DB_ROOT": str(td / "VIA" / "via_database"), "USERPROFILE": str(td)})
    try:
        files = {"engine/VRN_AutoTestLoop.py": "x = 1\n", "Invoke-VRN.ps1": "Write-Host 1\n", "VRN_Finalize_AIO_v2_1.ps1": "Write-Host 2\n", "panorama_xcheck_v110_shaa9stub110R.py": "y = 1\n", "VRN_ENG050_ContentStore_v0107.py": "z = 1\n", "Invoke-VRN-Batch-AllInOne-v0102.ps1": "Write-Host 3\n"}
        for k, v in files.items():
            (home / k).write_text(v, encoding="utf-8")
        rows = [{"tail": k} for k in files]
        plan = version_plan(rows)
        res = version_apply(plan)
        res2 = version_apply(version_plan(rows))
        chk("② 版號套用:沒版號 → _v0100 / -v0100 · 舊式 → v0201 · 正規(含連字號)不動 · _sha 殘檔不給 · 原檔不動 · 重跑不重複",
            (home / "engine" / "VRN_AutoTestLoop_v0100.py").exists() and (home / "Invoke-VRN-v0100.ps1").exists() and (home / "VRN_Finalize_AIO_v0201.ps1").exists() and not (home / "Invoke-VRN-Batch-AllInOne-v0102_v0100.ps1").exists()
            and (home / "engine" / "VRN_AutoTestLoop.py").read_text(encoding="utf-8") == "x = 1\n" and res["copied"] == 3 and res2["copied"] == 0 and (home / "registry" / "VRN_EngineVersioning_Ledger.jsonl").exists() and any(not x["dst"] for x in plan))
        pfx = {"blocks": [{"kind": "text", "role": "BODY", "text": "Overweight", "top": 100, "bottom": 110, "x0": 400, "x1": 460, "size": 9, "lines": []},
                          {"kind": "text", "role": "BODY", "text": "Price target", "top": 120, "bottom": 130, "x0": 400, "x1": 470, "size": 9, "lines": []},
                          {"kind": "text", "role": "BODY", "text": "NT$1,200", "top": 131, "bottom": 141, "x0": 400, "x1": 450, "size": 9, "lines": []},
                          {"kind": "text", "role": "BODY", "text": "Jentech (3653 TT) benefits from the liquid cooling shift; we expect revenue to grow strongly in 2026 as AI servers ramp.", "top": 100, "bottom": 140, "x0": 40, "x1": 380, "size": 9, "lines": []},
                          {"kind": "text", "role": "BODY", "text": "Amy Wang Senior Analyst +886-2-2181-8888 amy.wang@kgi.com", "top": 300, "bottom": 330, "x0": 400, "x1": 560, "size": 8, "lines": [1, 2, 3]},
                          {"kind": "text", "role": "BODY", "text": "2026", "top": 600, "bottom": 610, "x0": 40, "x1": 60, "size": 9, "lines": []}]}
        info_zone_fix(pfx)
        rl = [b["role"] for b in pfx["blocks"]]
        chk("③-1 首頁資訊區辨識(不靠切欄):評等 · 目標價 + 緊鄰數值 · 分析師聯絡 → INFO · 長句本文與遠處數字留 BODY", rl == ["INFO", "INFO", "INFO", "BODY", "INFO", "BODY"])
        chk("③ Memo / docx / txt → 資訊區不適用(灰)· 券商個股報告 → 適用", _is_memo("華南投顧-3038-全台-Memo-20251209.docx") and _is_memo("20251128兆豐訪談速報-神達(3706).pdf") and not _is_memo("GS-3653 20251002.pdf"))
        for src in (HERE / "intake" / "VRN_TableRepair", Path("/tmp/out")):
            for q in sorted(src.glob("VRN_Table*_v010*.py")) if src.is_dir() else []:
                if not (home / "intake" / "VRN_TableRepair" / q.name).exists():
                    shutil.copy(q, home / "intake" / "VRN_TableRepair" / q.name)
        (home / "knowledge" / "VRN_Broker_Dict_v0100.json").write_text(json.dumps({"brokers": {"凱基": {"abbr": "KGI", "aliases": ["凱基", "凱基投顧", "KGI", "KGI Securities"]}}}, ensure_ascii=False), encoding="utf-8")
        (home / "VRN_TWRoster_Offline_v0100.json").write_text(json.dumps({"rows": [{"code": "3653", "name": "健策", "market": "上市"}]}, ensure_ascii=False), encoding="utf-8")
        inp = td / "inbox"
        inp.mkdir()
        _resolve("_mk_pdf_v158")(inp / "凱基投顧_3653 健策_向子慧_20260917.pdf", td)
        o = _resolve("layout_run_v158")(inp, {"workers": 1, "tabula": False, "max": 0, "only": "", "no_ocr": True})
        x = _ST.get("x3") or {}
        out = td / "VIA_Reports" / "vrn" / "extract3"
        import csv as _csv
        cells = list(_csv.DictReader((out / "EXTRACT3_FIN_CELLS_latest.csv").open(encoding="utf-8-sig")))
        infos = list(_csv.DictReader((out / "EXTRACT3_INFO_latest.csv").open(encoding="utf-8-sig")))
        texts = list(_csv.DictReader((out / "EXTRACT3_TEXT_latest.csv").open(encoding="utf-8-sig")))
        rev = [c for c in cells if c["label"] == "Revenue" and c["period"] == "2024A"]
        keys = {i["key"] for i in infos}
        chk("④ 三區分開:財務報表逐格(Revenue × 2024A = 15,678 · 驗證過)· 資訊區(評等 · 目標價 · 分析師1 · 資訊區原文)· 文字(句 / 標題)",
            rev and rev[0]["raw"] == "15,678" and rev[0]["verified"] == "True" and {"評等", "目標價", "分析師1", "資訊區原文"} <= keys and any(t["type"] == "標題" for t in texts) and any(t["type"] == "句" for t in texts))
        f3 = list(out.glob("*_三區.html"))
        h = f3[0].read_text(encoding="utf-8") if f3 else ""
        chk("⑤ 每檔三欄頁(文字 | 資訊區 | 財務報表 各自亮燈)· 總頁 · 文字綠 · 資訊區綠 · 財報綠", f3 and "財務報表(" in h and "資訊區(" in h and "文字(" in h and Path(x.get("html", "")).exists() and x["text_g"] == 1 and x["info_g"] == 1 and x["fin_g"] == 1)
    finally:
        for k, val in saved.items():
            if val is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = val
        shutil.rmtree(td, ignore_errors=True)
    chk("⑥ 前版鏈(v0159 以前 + v0160 自身)自測 rc 0%s" % ("(本次略過)" if skip_prior else ""), prc == 0)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 正本加速器橋 · 自帶多程序墊片", "import VeritasCeleritas_v1141" in me and _job_entry.__module__ in ("__main__", __name__))
    print("[計] VRN_SystemManager_v0161 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
