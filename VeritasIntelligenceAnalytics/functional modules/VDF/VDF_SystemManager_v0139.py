#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0139 — 薄尾:三標準橋回歸(CI SDD 驗證 X-ACCEL「VDF_SystemManager_v0137 缺網路橋」:v0131–v0138 只帶加速器橋,本版補回 NET-BRIDGE(via_net_unified 尾版)+ LIB-BRIDGE(VIA_LibCanon),與 v0130 同款;最高政策 L103 ② VDF 導入網路工具);table matrix(操作員令 2026-10-06:把 VDF 輸入/輸出 HEADER 彙整表列)。自管自報:只讀自己的 VDF_TableHeader 尾版冊。
  table matrix [--json]   每表一列:燈 · 表號 · tid · 類別(INPUT / OUTPUT / SSOT / REGISTRY / LEDGER / OTHER,依來源路徑與冊名判)· 來源冊 · 鍵 · 欄數 · 欄(名:型,前 12)· 狀態
                          → VIA_Reports/vdf/HEADER_MATRIX_latest.{html,json,md}(淺色緊湊自適應;燈第一欄;可按類別篩)+ 貼回包 ≤300 行
其餘動詞照前版鏈。沙盒鍵:VIA_VDF_HOME · VIA_VDF_HEALTH_OUT(輸出夾)。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====

import datetime
import html
import importlib.util
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_SystemManager"
TAG = "v0139"
LAMP = {"GREEN": "#16a34a", "YELLOW": "#f59e0b", "RED": "#dc2626", "GRAY": "#9ca3af"}


def _vnum_v0139(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0139(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0139(p) < _vnum_v0139(__file__)), key=_vnum_v0139)
PRIOR = _load_v0139(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


_CAT = [("INPUT", re.compile(r"(?i)(input|incoming|seed|raw|fetch|download|source|_in\b|universe|params)")), ("LEDGER", re.compile(r"(?i)(ledger|log|history|audit)")), ("SSOT", re.compile(r"(?i)(ssot|synonym|regex|lexicon|dict|canon)")),
        ("REGISTRY", re.compile(r"(?i)(registry|register|functionmatrix|tableheader|manifest|catalog|index|numbers)")), ("OUTPUT", re.compile(r"(?i)(output|result|report|export|out\b|final|matrix|summary|coverage|stage)"))]


def _cat_of(tid: str, source: str) -> str:
    probe = (source or "") + " " + tid
    for cat, rx in _CAT:
        if rx.search(probe):
            return cat
    return "OTHER"


def table_matrix() -> dict:
    home = Path(os.environ.get("VIA_VDF_HOME") or HERE)
    reg = home / "registry"
    hits = sorted(reg.glob("VDF_TableHeader_v*.json"), key=lambda q: _vnum_v0139(q.stem)) if reg.is_dir() else []
    out_dir = Path(os.environ.get("VIA_VDF_HEALTH_OUT") or (home.parents[1] / "VIA_Reports" / "vdf"))
    out = {"verb": "table_matrix", "sub": "VDF", "ts": datetime.datetime.now().isoformat(timespec="seconds"), "book": (hits[-1].name if hits else None), "rows": [], "_notes": []}
    if not hits:
        out["_notes"].append("VDF_TableHeader 冊不在(先 table register --apply)")
        out["lamp"] = "GRAY"
        return out
    book = json.loads(hits[-1].read_text(encoding="utf-8-sig"))
    for tid, e in sorted((book.get("tables") or {}).items()):
        cols = e.get("columns") or []
        src = e.get("source", "")
        status = e.get("status", "ACTIVE")
        lamp = "GRAY" if status == "RETIRED" else ("GREEN" if e.get("table_no") and e.get("keys") else ("YELLOW" if e.get("keys") or e.get("table_no") else "RED"))
        out["rows"].append({"tid": tid, "table_no": e.get("table_no") or "", "cat": _cat_of(tid, src), "source": Path(src).name if src else "", "table": e.get("table", ""), "keys": e.get("keys") or [], "key_ruling": e.get("key_ruling", ""),
                            "n_cols": len(cols), "cols": ["%s:%s" % (c.get("name"), c.get("dtype")) for c in cols], "rows_seen": e.get("rows", e.get("n_rows", "")), "status": status, "replaced_by": e.get("replaced_by", ""), "lamp": lamp})
    out["per_cat"] = dict(Counter(r["cat"] for r in out["rows"]))
    out["counts"] = dict(Counter(r["lamp"] for r in out["rows"]))
    out["lamp"] = "RED" if out["counts"].get("RED") else ("YELLOW" if out["counts"].get("YELLOW") else "GREEN")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "HEADER_MATRIX_latest.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "HEADER_MATRIX_latest.html").write_text(_html_v0139(out), encoding="utf-8")
    md = ["# VDF 輸入/輸出 HEADER 彙整(%s)" % out["ts"], "", "| 燈 | 類別 | 表號 | tid | 來源冊 | 鍵 | 欄數 | 欄(前 8) | 狀態 |", "|---|---|---|---|---|---|---|---|---|"]
    for r in out["rows"]:
        md.append("| %s | %s | %s | %s | %s | %s | %d | %s | %s |" % (r["lamp"], r["cat"], r["table_no"] or "留白", r["tid"], r["source"], "+".join(r["keys"]) or "—", r["n_cols"], ", ".join(r["cols"][:8]).replace("|", "¦"), r["status"]))
    (out_dir / "HEADER_MATRIX_latest.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    out["html"] = str(out_dir / "HEADER_MATRIX_latest.html")
    return out


def _html_v0139(o: dict) -> str:
    def lp(l):
        return "<i class='lp %s' style='background:%s'></i>" % (l, LAMP[l])
    cats = sorted(o["per_cat"])
    trs = "\n".join("<tr data-c='%s' data-l='%s'><td>%s</td><td>%s</td><td class='code'>%s</td><td><b>%s</b><div class='dim'>%s · %s</div></td><td>%s%s</td><td class='n'>%d</td><td class='cols'>%s</td><td>%s%s</td></tr>"
                     % (r["cat"], r["lamp"], lp(r["lamp"]), r["cat"], html.escape(r["table_no"] or "留白"), html.escape(r["tid"]), html.escape(r["source"]), html.escape(str(r["table"])), html.escape("+".join(r["keys"]) or "—"), (" <small>(%s)</small>" % r["key_ruling"]) if r["key_ruling"] else "", r["n_cols"],
                        html.escape(", ".join(r["cols"][:12])) + (" …+%d" % (r["n_cols"] - 12) if r["n_cols"] > 12 else ""), r["status"], (" → " + html.escape(r["replaced_by"])) if r["replaced_by"] else "") for r in o["rows"])
    chips = "".join("<button onclick=\"flt('%s')\">%s · %d</button>" % (c, c, o["per_cat"][c]) for c in cats)
    return """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VDF HEADER 彙整</title>
<style>body{font-family:"Microsoft JhengHei UI","Segoe UI",Arial;color:#1f2937;margin:0;padding:12px;font-size:12px;background:#fff}h1{font-size:16px;margin:0 0 4px}.meta{color:#6b7280;font-size:11px;margin-bottom:8px}
button{margin:0 4px 6px 0;padding:3px 8px;border:1px solid #e0e0e0;background:#f7f7f7;border-radius:6px;cursor:pointer;font-size:11px}.wrap{overflow-x:auto}table{border-collapse:collapse;width:100%%;table-layout:auto}th,td{border:1px solid #e0e0e0;padding:2px 5px;text-align:left;vertical-align:top;white-space:nowrap}
th{background:#111827;color:#fff;position:sticky;top:0}tr:nth-child(even){background:#fafafa}td.code{font-family:Consolas,monospace}td.n{text-align:right}td.cols{white-space:normal;max-width:560px;color:#374151}.dim{color:#6b7280;font-size:10.5px}
.lp{display:inline-block;width:11px;height:11px;border-radius:50%%;vertical-align:middle}.lp.RED{animation:bl 2.4s ease-in-out infinite}@keyframes bl{0%%,100%%{opacity:1}50%%{opacity:.25}}@media(max-width:700px){th,td{font-size:10.5px;padding:2px 3px}}</style></head><body>
<h1>VDF 輸入 / 輸出 HEADER 彙整</h1><div class="meta">%s · 冊 %s · 表 %d · <span style="color:#16a34a">●</span>綠 有號有鍵 <span style="color:#f59e0b">●</span>黃 缺其一 <span style="color:#dc2626">●</span>紅 都缺 <span style="color:#9ca3af">●</span>灰 已退役 · 鍵後 (composite/synthetic) = 母系統裁定鍵</div>
<div>%s <button onclick="flt('')">全部</button> <button onclick="lampf('YELLOW')">只看黃</button> <button onclick="lampf('RED')">只看紅</button></div>
<div class="wrap"><table id="m"><thead><tr><th>燈</th><th>類別</th><th>表號</th><th>tid / 來源冊 · 表</th><th>鍵</th><th>欄數</th><th>欄(名:型)</th><th>狀態</th></tr></thead><tbody>%s</tbody></table></div>
<script>function flt(c){document.querySelectorAll('#m tbody tr').forEach(function(t){t.style.display=(!c||t.dataset.c===c)?'':'none'})}function lampf(l){document.querySelectorAll('#m tbody tr').forEach(function(t){t.style.display=(t.dataset.l===l)?'':'none'})}</script></body></html>""" % (o["ts"], o["book"], len(o["rows"]), chips, trs)


def _print_matrix_v0139(o: dict) -> None:
    print("[計] VDF table matrix · 冊 %s · 表 %d · %s · 類別 %s · %s" % (o["book"], len(o["rows"]), " ".join("%s=%d" % kv for kv in sorted(o.get("counts", {}).items())), json.dumps(o.get("per_cat", {}), ensure_ascii=False), o["lamp"]))
    for cat in sorted(o.get("per_cat", {})):
        print("[計] ── %s ──" % cat)
        for r in [x for x in o["rows"] if x["cat"] == cat][:60]:
            print("  [%s] %s · %s · %s · 鍵 %s · 欄 %d:%s" % ({"GREEN": "OK", "YELLOW": "YEL", "RED": "RED", "GRAY": "GRAY"}[r["lamp"]], r["table_no"] or "留白", r["tid"][:48], r["source"][:40], "+".join(r["keys"]) or "—", r["n_cols"], ",".join(c.split(":")[0] for c in r["cols"][:8]) + ("…" if r["n_cols"] > 8 else "")))
    for n in o.get("_notes", []):
        print("  [注] %s" % n)
    if o.get("html"):
        print("  [MATRIX] %s" % o["html"])


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if "--selftest" in args[:2]:
        return selftest()
    if args[:2] == ["table", "matrix"]:
        o = table_matrix()
        if "--json" in args:
            print(json.dumps(o, ensure_ascii=False))
        _print_matrix_v0139(o)
        return 0
    return PRIOR.main(args)


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    td = Path(tempfile.mkdtemp(prefix="vdfhm-"))
    home = td / "functional modules" / "VDF"
    (home / "registry").mkdir(parents=True)
    saved = {k: os.environ.get(k) for k in ("VIA_VDF_HOME", "VIA_VDF_HEALTH_OUT")}
    os.environ["VIA_VDF_HOME"] = str(home)
    os.environ["VIA_VDF_HEALTH_OUT"] = str(td / "out")
    (home / "registry" / "VDF_TableHeader_v0100.json").write_text(json.dumps({"tables": {
        "vdf_input_seed": {"source": "functional modules/VDF/input/seed_v0100.json", "table": "rows", "keys": ["ticker"], "table_no": "SSOT-VCGC-VDF-TBL0001", "columns": [{"name": "ticker", "dtype": "str"}, {"name": "px", "dtype": "float"}], "status": "ACTIVE"},
        "vdf_result_summary": {"source": "VIA_Reports/vdf/RESULT_x.json", "table": "rows", "keys": [], "table_no": "", "columns": [{"name": "a", "dtype": "int"}], "status": "ACTIVE"},
        "vdf_old_registry": {"source": "functional modules/VDF/registry/old.json", "table": "items", "keys": ["k"], "table_no": "SSOT-VCGC-VDF-TBL0002", "columns": [], "status": "RETIRED", "replaced_by": "new"}}}), encoding="utf-8")
    o = table_matrix()
    R = {r["tid"]: r for r in o["rows"]}
    chk("① 分類:seed → INPUT · RESULT → OUTPUT · registry → REGISTRY", R["vdf_input_seed"]["cat"] == "INPUT" and R["vdf_result_summary"]["cat"] == "OUTPUT" and R["vdf_old_registry"]["cat"] == "REGISTRY")
    chk("② 燈:有號有鍵綠 · 都缺紅 · 退役灰", R["vdf_input_seed"]["lamp"] == "GREEN" and R["vdf_result_summary"]["lamp"] == "RED" and R["vdf_old_registry"]["lamp"] == "GRAY")
    htm = Path(o["html"]).read_text(encoding="utf-8")
    chk("③ 輸出:HTML 四色 · viewport · 燈第一欄 · 類別篩 · md · json", all(c in htm for c in LAMP.values()) and "viewport" in htm and "flt('INPUT')" in htm and (td / "out" / "HEADER_MATRIX_latest.md").exists() and (td / "out" / "HEADER_MATRIX_latest.json").exists())
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("④ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 三標準橋齊:ACCEL · NET(via_net_unified 尾版)· LIB(VIA_LibCanon)· glob 取前版", "[VIA:ACCEL-BRIDGE:v0100]" in body and "[VIA:NET-BRIDGE:v0100]" in body and "[VIA:LIB-BRIDGE:v0100]" in body and "_via_net" in body)
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VDF_SystemManager_v0139 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
