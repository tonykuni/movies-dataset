#!/usr/bin/env python3
"""VIA_UploadsWorkbench v0100 — 操作員上傳檔 → 視覺鎖定的離線 HTML 工作台(0 token · 不連網 · 不執行)。

操作員 2026-11-10 令:「整合在一起 自建HTML U/I不燒任何TOKEN」「以此為U/I視覺鎖定」(審查包
VIA_Subsystem_Workspaces_Review_Kit_v0106_4_20261106.zip,sha256 77d8feb5…,= review/VIA_Workbench_LockSite_v0106_4 的來源)。

做什麼(全部只讀):
  1. 掃 --in 資料夾(例:%USERPROFILE%\\Downloads 或雲端上傳夾),把 Windows「 (n)」與上傳「_n」複本歸回 17 份正本,
     逐份算 SHA-256;同名不同內容 = RED;有 .sha256 側檔就核對。
  2. 審查包 zip:外部 SHA ↔ 側檔 ↔ 鎖站 manifest;包內 SHA256SUMS 逐檔核對(只在記憶體讀,不解壓、不執行)。
  3. 矩陣稽核 xlsx:UI_* 九張表 = 鎖定 U/I 的 LAST_MATRIX 列(status · id · ssot_name …),逐列轉成 bundle。
  4. 每個 system 出一頁(鎖站 html / css / js 原樣 + v0102 響應式覆蓋層),另出 index.html 總覽(無腳本)。

邊界:不執行任何上傳的 .py / .ps1 / .html;不連網;不寫任何系統的冊 / 正本 / 號(L123 · L125);
資料是上傳的外部證據,不是本倉實測,頁面上明示。來源 system 欄照原文(例「VRN」),總覽標「VRN(未分辨)」(L123 ②)。
"""
from __future__ import annotations

import argparse
import base64
import datetime as _dt
import glob
import hashlib
import html
import importlib.util
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree.ElementTree import iterparse

VERSION = "v0100"
ENGINE = f"VIA_UploadsWorkbench_{VERSION}"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent                       # …/VeritasIntelligenceAnalytics
UI_CONTRACT_VERSION = "v0106.4"

# 操作員 2026-11-10 列出的 22 個路徑 → 17 份正本(複本字尾已去掉)
EXPECTED = [
    "VIA v0105 實際ZIP完整矩陣與欄位燈號稽核 v0105.2.md",
    "VIA_Matrix_Audit_v0105_1_20261106.xlsx",
    "VIA VCGC · AI handover · v0106.4.md",
    "subsystem_v0106_4_final_actual_zip_receipt.json",
    "VIA_Subsystem_Workspaces_Review_Kit_v0106_4_20261106.zip.sha256",
    "VIA 六系統獨立工作台與 AI 交接指南 v0106.4.md",
    "viaatlas.zip",
    "VIA_Subsystem_Workspaces_Review_Kit_v0106_4_20261106.zip",
    "VIA_Workbench_Hub_latest.html",
    "VIA_MatrixGovernance_Review_Addon_v0105_20261106.zip.sha256",
    "VIA Matrix Governance v0105 — 現況與安全接入.md",
    "VIA Governance MCP v0105 — Windows 手動接入.md",
    "mcp_stdio_smoke_v0105_2.py",
    "VIA_Matrix_Audit_v0105_1_20261106.json",
    "VIA 五系統 RED 阻礙與安全修復計畫 v0105.2.md",
    "matrix_detail_v0105_2_final_receipt.json",
    "VIA_Matrix_Governance_Full_Model_v0105_1_20261106.json.gz",
]
KNOWN_SHA = {  # 來源文件自報的外部 SHA(交叉核對用,不是本工具算出來的)
    "VIA_Subsystem_Workspaces_Review_Kit_v0106_4_20261106.zip": "77d8feb5b5825f5e0f5d0c15914b87ae9f49b4aab6bd34a848b1f2883afa8746",
    "VIA_MatrixGovernance_Review_Addon_v0105_20261106.zip": "bf5ac1a16667e2a2f9c8928a2102d6ca191dea07caab5e888f3eb16a596d6be2",
}
KIT = "VIA_Subsystem_Workspaces_Review_Kit_v0106_4_20261106.zip"
XLSX = "VIA_Matrix_Audit_v0105_1_20261106.xlsx"
UI_SHEETS = {"UI_全部文件": "files", "UI_參數_IO": "io", "UI_指令定位": "commands", "UI_環境工具": "environment",
             "UI_衝突": "conflicts", "UI_政策": "policy", "UI_測試驗證": "tests", "UI_VAP需求": "requirements", "UI_系統": "systems"}
CATEGORIES = list(UI_SHEETS.values())
PAGE_SYSTEMS = ["VCGC", "VDF", "VRN", "VQG", "VAP"]
LABEL = {"VRN": "VRN(未分辨 · 來源原文寫 VRN)"}
HEAVY = {"io", "commands"}                              # 共用列不放進每一頁(太大),只計數
DOC_EXT = {".md"}
WARNINGS: list[str] = []


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def key(name: str) -> str:
    return re.sub(r"[^0-9a-z]+", "", name.lower())


_EXP_KEYS = {key(n): n for n in EXPECTED}
assert len(_EXP_KEYS) == len(EXPECTED), "EXPECTED 正規化後撞名"


def canonical(name: str) -> str | None:
    """實際檔名 → 正本名;認 Windows「 (n)」、上傳前綴「xxxxxxxx-」與上傳複本「_n」。不認得回 None。"""
    n = re.sub(r"^[0-9a-f]{8}-", "", name)
    n = re.sub(r" \(\d+\)", "", n)
    if key(n) in _EXP_KEYS:
        return _EXP_KEYS[key(n)]
    m = re.sub(r"_\d{1,2}(?=\.[A-Za-z0-9]+$)", "", n)   # 只去最後一個副檔名前的 _n
    return _EXP_KEYS.get(key(m))


def load_lock():
    p = sorted(glob.glob(str(HERE / "VIA_WorkbenchLock_v0*.py")))[-1]
    spec = importlib.util.spec_from_file_location("via_workbench_lock_tail", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod, Path(p).name


# ---------- 1. 清點 ----------
def inventory(src: Path) -> dict:
    groups: dict[str, list] = {n: [] for n in EXPECTED}
    unknown = []
    for p in sorted(src.iterdir()):
        if not p.is_file() or p.name.startswith("."):
            continue
        c = canonical(p.name)
        if c is None:
            unknown.append(p.name)
            continue
        groups[c].append({"path": p, "name": p.name, "bytes": p.stat().st_size, "sha256": sha256_file(p)})
    items = []
    for n in EXPECTED:
        cs = groups[n]
        shas = sorted({c["sha256"] for c in cs})
        item = {"canonical": n, "copies": [{k: v for k, v in c.items() if k != "path"} for c in cs],
                "distinct_sha256": shas, "path": cs[0]["path"] if cs else None}
        if not cs:
            item.update(status="YELLOW", note="未上傳(本次 --in 夾內沒有)")
        elif len(shas) > 1:
            item.update(status="RED", note=f"同名 {len(cs)} 份、{len(shas)} 種內容:不能當同一份")
        else:
            item.update(status="GREEN", note=f"{len(cs)} 份複本內容相同" if len(cs) > 1 else "")
        items.append(item)
    by = {i["canonical"]: i for i in items}
    for i in items:  # 側檔核對
        if not i["canonical"].endswith(".sha256") or not i["path"]:
            continue
        target = i["canonical"][: -len(".sha256")]
        want = i["path"].read_text(encoding="utf-8", errors="replace").split()[0].lower() if i["path"].stat().st_size else ""
        t = by.get(target)
        checks = [f"側檔值 {want[:12]}…"]
        if target in KNOWN_SHA:
            checks.append("= 來源文件自報值" if want == KNOWN_SHA[target] else "≠ 來源文件自報值")
        if t and t["distinct_sha256"]:
            ok = t["distinct_sha256"] == [want]
            checks.append("= 實檔" if ok else "≠ 實檔")
            if not ok:
                i["status"] = t["status"] = "RED"
        else:
            checks.append("實檔沒上傳,只能對自報值")
        i["sidecar"] = {"target": target, "expect": want, "checks": checks}
    return {"items": items, "unknown": unknown}


# ---------- 2. 審查包 ----------
def kit_checks(item: dict) -> dict:
    out = {"present": bool(item["path"])}
    if not item["path"]:
        return out
    sha = item["distinct_sha256"][0]
    man = json.loads((VIA / "review" / "VIA_Workbench_LockSite_v0106_4" / "manifest.json").read_text(encoding="utf-8"))
    out["sha256"] = sha
    out["eq_known"] = sha == KNOWN_SHA[KIT]
    out["eq_locksite_source"] = sha == man.get("source_zip_sha256")
    z = zipfile.ZipFile(item["path"])
    sums = {}
    for line in z.read("SHA256SUMS").decode("utf-8").splitlines():
        if line.strip():
            h, _, n = line.partition("  ")
            sums[n.strip()] = h.strip()
    bad = [n for n, h in sums.items() if n in z.namelist() and hashlib.sha256(z.read(n)).hexdigest() != h]
    miss = [n for n in sums if n not in z.namelist()]
    out.update(members=len(z.namelist()), sums=len(sums), sums_ok=len(sums) - len(bad) - len(miss), bad=bad, missing=miss)
    lock = man.get("source_in_zip", {})
    lfiles = man.get("files", {})
    out["lock_bytes_equal"] = {k: hashlib.sha256(z.read(v)).hexdigest() == lfiles.get(k) for k, v in lock.items()}
    docs = {}
    for n in z.namelist():
        if n.endswith(".md"):
            docs["審查包/" + n] = z.read(n).decode("utf-8", errors="replace")
    out["docs"] = docs
    return out


# ---------- 3. xlsx(串流解析,不需 openpyxl) ----------
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def _col(ref: str) -> int:
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n - 1


def xlsx_sheets(path: Path) -> dict:
    z = zipfile.ZipFile(path)
    ss: list[str] = []
    if "xl/sharedStrings.xml" in z.namelist():
        for _, el in iterparse(z.open("xl/sharedStrings.xml")):
            if el.tag == NS + "si":
                ss.append("".join(t.text or "" for t in el.iter(NS + "t")))
                el.clear()
    import xml.etree.ElementTree as ET
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    target = {r.get("Id"): r.get("Target") for r in rels}
    out = {}
    for sh in wb.iter(NS + "sheet"):
        t = target[sh.get(RNS + "id")].lstrip("/")
        out[sh.get("name")] = (z, t if t.startswith("xl/") else "xl/" + t, ss)
    return out


def sheet_rows(ref) -> list:
    z, part, ss = ref
    rows = []
    for _, el in iterparse(z.open(part)):
        if el.tag != NS + "row":
            continue
        vals: dict[int, str] = {}
        for c in el.iter(NS + "c"):
            t, r = c.get("t"), c.get("r")
            v = c.find(NS + "v")
            if t == "s" and v is not None:
                s = ss[int(v.text)]
            elif t == "inlineStr":
                s = "".join(x.text or "" for x in c.iter(NS + "t"))
            else:
                s = v.text if v is not None and v.text is not None else ""
            vals[_col(r) if r else len(vals)] = s
        rows.append([vals.get(i, "") for i in range(max(vals) + 1)] if vals else [])
        el.clear()
    return rows


def as_dicts(rows: list) -> list:
    if not rows:
        return []
    head = rows[0]
    return [{h: (r[i] if i < len(r) else "") for i, h in enumerate(head) if h} for r in rows[1:] if any(r)]


def matrix_from_xlsx(path: Path) -> dict:
    sh = xlsx_sheets(path)
    res = {"sheets": list(sh), "tables": {}, "rows": {c: [] for c in CATEGORIES}}
    for name in ("讀我與來源", "矩陣燈號總覽", "RED阻礙與修復"):
        if name in sh:
            res["tables"][name] = sheet_rows(sh[name])
    for name, cat in UI_SHEETS.items():
        if name not in sh:
            WARNINGS.append(f"xlsx 缺表 {name}")
            continue
        for d in as_dicts(sheet_rows(sh[name])):
            for k in ("status", "id", "ssot_name", "version", "tools", "error_detail", "system"):
                d.setdefault(k, "")
            if not d.get("completion_time"):
                d["completion_time"] = "NOT_OBSERVED"
            res["rows"][cat].append(d)
    return res


# ---------- 4. 出頁 ----------
def lamp_count(rows: list) -> dict:
    c: dict[str, int] = {}
    for r in rows:
        s = str(r.get("status", "")).upper() or "NOT_SET"
        c[s] = c.get(s, 0) + 1
    return c


def render_system(lock, site: Path, system: str, bundle: dict, gen: str) -> str:
    F = lock.LOCK_FILES
    tpl = (site / F["html"]).read_text(encoding="utf-8")
    css = (site / F["css"]).read_text(encoding="utf-8")
    js = (site / F["js"]).read_text(encoding="utf-8").replace("__SYSTEM__", system)
    logo = base64.b64encode((site / F["logo"]).read_bytes()).decode("ascii")
    page = tpl.replace("__CSP__", lock.csp_for(js)).replace("__CSS__", css).replace("__BRAND_LOGO__", logo)
    page = page.replace("__PAYLOAD__", json.dumps(lock.envelope(bundle), separators=(",", ":"))).replace("__JS__", js)
    page = page.replace("__SYSTEM__", system)
    # 只換連結與自報標籤,樣式 / 結構 / 腳本不動(鎖的是正本三檔)
    page = page.replace('href="subsystems-v0106.4.html"', 'href="index.html"')
    page = page.replace('href="governance-preview-v0105.3.html"', 'href="uploads_receipt.json"')
    page = page.replace("Global/common governance · existing read-only route", "上傳整合收據(json)")
    page = page.replace("v0106.4 CANDIDATE</span>", f"上傳整合 · {ENGINE}</span>")
    page = page.replace("ACTUAL · RED / BLOCKED</span>", "上傳證據原文 · RED / BLOCKED</span>")
    page = page.replace("VIA · ARCHITECTURE BASELINE · 2026-11-05 · ENGINE v0103", f"VIA · 上傳整合工作台 · {gen[:10]} · {ENGINE}")
    page = page.replace("v0106.4 CANDIDATE · original snapshot", f"{ENGINE} · 來源 = 上傳的 {XLSX}")
    page = page.replace("GitHub health 由 parent 外部提供；此頁只標示原始 snapshot provenance。",
                        "資料是操作員上傳的外部證據(矩陣稽核 xlsx 的 UI_* 表),不是本倉實測;0 token、不連網、不執行。")
    if hasattr(lock, "apply_responsive"):
        page, _ = lock.apply_responsive(page)
    return page


def md_html(text: str) -> str:
    """極簡 Markdown → 安全 HTML:全部先跳脫;連結只留文字;不產生任何 href / src / script。"""
    out, para, code, table = [], [], None, []

    def flush():
        if para:
            out.append("<p>" + "<br>".join(para) + "</p>")
            para.clear()
        if table:
            out.append('<pre class="u-pre">' + "\n".join(table) + "</pre>")
            table.clear()

    for raw in text.splitlines():
        if code is not None:
            if raw.strip().startswith("```"):
                out.append('<pre class="u-pre">' + html.escape("\n".join(code)) + "</pre>")
                code = None
            else:
                code.append(raw)
            continue
        if raw.strip().startswith("```"):
            flush()
            code = []
            continue
        line = html.escape(re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", raw))
        line = re.sub(r"`([^`]+)`", r"<code>\1</code>", line)
        line = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", line)
        if raw.lstrip().startswith("|"):
            if para:
                flush()
            table.append(html.escape(raw))
            continue
        if table:
            flush()
        m = re.match(r"^(#{1,6})\s+(.*)", raw)
        if m:
            flush()
            lv = min(len(m.group(1)) + 2, 6)
            out.append(f"<h{lv}>{line.lstrip('#').strip()}</h{lv}>")
        elif re.match(r"^\s*([-*]|\d+\.)\s+", raw):
            flush()
            out.append("<div class=\"u-li\">• " + re.sub(r"^\s*([-*]|\d+\.)\s+", "", line) + "</div>")
        elif not raw.strip():
            flush()
        else:
            para.append(line)
    if code is not None:
        out.append('<pre class="u-pre">' + html.escape("\n".join(code)) + "</pre>")
    flush()
    return "\n".join(out)


def badge(status: str) -> str:
    s = str(status).upper()
    cls = {"GREEN": "success", "RED": "danger", "YELLOW": "warning"}.get(s, "lock")
    return f'<span class="badge {cls}">{html.escape(s)}</span>'


def tbl(rows: list, head: bool = True, limit: int = 400) -> str:
    if not rows:
        return "<p class=\"subtitle\">(無)</p>"
    h = ["<table class=\"u-t\">"]
    for i, r in enumerate(rows[:limit]):
        tag = "th" if head and i == 0 else "td"
        h.append("<tr>" + "".join(f"<{tag}>{html.escape(str(c))[:600]}</{tag}>" for c in r) + "</tr>")
    h.append("</table>")
    if len(rows) > limit:
        h.append(f"<p class=\"subtitle\">只列前 {limit} 列,共 {len(rows)} 列</p>")
    return "".join(h)


HUB_CSS = """
main.u{padding:18px 24px 40px;max-width:1500px} section.u-s{background:var(--white);border:1px solid var(--line);border-radius:8px;padding:14px 16px;margin:0 0 14px}
.u-t{border-collapse:collapse;width:100%;font-size:10px;margin:6px 0} .u-t th,.u-t td{border-bottom:1px solid var(--line);padding:4px 6px;text-align:left;vertical-align:top;overflow-wrap:anywhere}
.u-t th{background:var(--row);font-weight:600} .u-pre{font:10px/1.5 var(--mono);background:var(--row);padding:8px;border-radius:6px;white-space:pre-wrap;overflow-wrap:anywhere}
.u-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px} .u-card{border:1px solid var(--line);border-radius:8px;padding:10px;background:var(--bg)}
.u-card a{color:var(--g-ink);font-weight:600} .u-li{margin:2px 0 2px 8px} details{margin:6px 0} summary{cursor:pointer;color:var(--g-ink)}
@media (max-width:720px){main.u{padding:12px 16px} header{flex-wrap:wrap}}
"""


def render_hub(lock, site: Path, inv: dict, kit: dict, mx: dict | None, pages: dict, docs: dict, gen: str, lock_ok: bool) -> str:
    css = (site / lock.LOCK_FILES["css"]).read_text(encoding="utf-8")
    logo = base64.b64encode((site / lock.LOCK_FILES["logo"]).read_bytes()).decode("ascii")
    up = sum(1 for i in inv["items"] if i["copies"])
    red = sum(1 for i in inv["items"] if i["status"] == "RED")
    rows = [["燈", "正本", "已上傳複本", "SHA-256(前 16)", "說明 / 側檔核對"]]
    for i in inv["items"]:
        cop = " · ".join(f"{c['name']} ({c['bytes']:,} B)" for c in i["copies"]) or "—"
        note = " ｜ ".join(x for x in (i.get("note", ""), " · ".join(i.get("sidecar", {}).get("checks", []))) if x)
        rows.append([i["status"], i["canonical"], cop, " / ".join(s[:16] for s in i["distinct_sha256"]) or "—", note])
    inv_html = tbl(rows).replace("<td>GREEN</td>", "<td>" + badge("GREEN") + "</td>") \
        .replace("<td>RED</td>", "<td>" + badge("RED") + "</td>").replace("<td>YELLOW</td>", "<td>" + badge("YELLOW") + "</td>")
    if kit.get("present"):
        k = [["檢查", "結果"],
             ["外部 SHA-256", kit["sha256"]],
             ["= 來源文件自報(77d8feb5…)", "是" if kit["eq_known"] else "否"],
             ["= 鎖站 manifest 來源", "是" if kit["eq_locksite_source"] else "否"],
             ["包內 SHA256SUMS", f"{kit['sums_ok']}/{kit['sums']} 相符" + (f" · 不符 {kit['bad']}" if kit["bad"] else "") + (f" · 缺 {kit['missing']}" if kit["missing"] else "")],
             ["鎖站四檔 = 包內位元組", " · ".join(f"{a} {'✓' if b else '✗'}" for a, b in kit["lock_bytes_equal"].items())]]
        kit_html = tbl(k)
    else:
        kit_html = "<p class=\"subtitle\">審查包 zip 沒在 --in 夾內,未核對。</p>"
    cards = []
    for s, p in pages.items():
        cnt = " · ".join(f"{c} {n}" for c, n in p["rows"].items() if n)
        lamps = " ".join(f"{k} {v}" for k, v in sorted(p["lamps"].items()))
        cards.append(f'<div class="u-card"><a href="{html.escape(p["file"])}">{html.escape(LABEL.get(s, s))}</a>'
                     f'<div class="subtitle">{html.escape(lamps)}</div><div class="eyebrow">{html.escape(cnt)}</div></div>')
    mx_html = ""
    if mx:
        for name, t in mx["tables"].items():
            mx_html += f"<h3>{html.escape(name)}</h3>" + tbl(t)
        other = sorted({str(r.get('system')) for c in CATEGORIES for r in mx["rows"][c]} - set(PAGE_SYSTEMS))
        mx_html += f"<p class=\"subtitle\">共用 / 其他 system 值(不出獨立頁,{', '.join(c for c in CATEGORIES if c not in HEAVY)} 類放進各頁 Shared evidence):{html.escape(' · '.join(other))}</p>"
    doc_html = "".join(f"<details><summary>{html.escape(n)}</summary>{md_html(t)}</details>" for n, t in docs.items())
    csp = "default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'"
    return f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{csp}">
<title>VIA 上傳整合工作台</title><style>{css}</style><style>{HUB_CSS}</style></head>
<body><header><div class="brand"><img class="brand-logo" alt="Veritas" src="data:image/png;base64,{logo}">
<div class="brand-copy"><p class="eyebrow">VIA · 上傳整合工作台 · {gen[:10]} · {ENGINE}</p><h1>上傳檔整合 · 視覺鎖定 v0106.4</h1>
<p class="subtitle">0 token · 不連網 · 不執行任何上傳的程式 · 資料是外部證據,不是本倉實測</p></div></div>
<div class="mast-actions"><span class="badge {'success' if lock_ok else 'danger'}">鎖站 {'4/4 位元組相符' if lock_ok else 'SHA 不符'}</span>
<span class="badge">已上傳 {up}/{len(inv['items'])} 份正本</span><span class="badge {'danger' if red else 'success'}">同名異內容 / 側檔不符 {red}</span>
<span class="badge danger">上傳證據原文 · RED / BLOCKED</span></div></header>
<main class="u">
<section class="u-s"><h2>一 · 上傳清單(22 個路徑 → 17 份正本)</h2>{inv_html}
<p class="subtitle">不認得的檔:{html.escape(' · '.join(inv['unknown']) or '無')}</p></section>
<section class="u-s"><h2>二 · 審查包 = 視覺鎖定來源</h2>{kit_html}</section>
<section class="u-s"><h2>三 · 各系統工作台(鎖定 U/I)</h2><div class="u-grid">{''.join(cards) or '<p class="subtitle">矩陣 xlsx 沒上傳,未出系統頁。</p>'}</div>
<p class="subtitle">L123 / L125:五系統各自獨立;此處只攤開上傳證據,不裁定、不代修、不發號。VRN-1 在倉外,只讀。</p></section>
<section class="u-s"><h2>四 · 矩陣稽核摘要(xlsx)</h2>{mx_html or '<p class="subtitle">未上傳。</p>'}</section>
<section class="u-s"><h2>五 · 文件(Markdown,純文字顯示,連結不可點)</h2>{doc_html or '<p class="subtitle">無</p>'}</section>
</main></body></html>"""


def build(src: Path, out: Path) -> dict:
    gen = utc_now()
    lock, lock_name = load_lock()
    site = lock.lock_site(VIA)
    lv = lock.verify_lock_site(VIA)
    lock_ok = bool(lv.get("ok"))
    if not lock_ok:
        return {"lamp": "RED", "engine": ENGINE, "reason": "鎖站 SHA 不過,不出頁", "lock_site": lv}
    inv = inventory(src)
    by = {i["canonical"]: i for i in inv["items"]}
    kit = kit_checks(by[KIT])
    docs = {}
    for i in inv["items"]:
        if i["path"] and Path(i["canonical"]).suffix in DOC_EXT:
            docs["上傳/" + i["canonical"]] = i["path"].read_text(encoding="utf-8", errors="replace")
    docs.update(kit.pop("docs", {}))
    mx = matrix_from_xlsx(by[XLSX]["path"]) if by[XLSX]["path"] else None
    out.mkdir(parents=True, exist_ok=True)
    pages = {}
    if mx:
        shared = [{"category": c, "row": r} for c in CATEGORIES if c not in HEAVY
                  for r in mx["rows"][c] if str(r.get("system")) not in PAGE_SYSTEMS]
        for s in PAGE_SYSTEMS:
            M = {c: [r for r in mx["rows"][c] if str(r.get("system")) == s] for c in CATEGORIES}
            if not any(M.values()):
                continue
            bundle = {"version": UI_CONTRACT_VERSION, "workbench_engine": ENGINE, "system": s, "LAST_MATRIX": M,
                      "SHARED_EVIDENCE": shared, "SHARED_CANDIDATE_OR_SESSION_OBSERVATIONS": {}, "DATABASE_HISTORICAL_GOVERNANCE": {},
                      "source": {"engine": ENGINE, "generated_utc": gen, "xlsx": XLSX, "xlsx_sha256": by[XLSX]["distinct_sha256"][0],
                                 "kind": "UPLOADED_EXTERNAL_EVIDENCE", "lock_site": "review/VIA_Workbench_LockSite_v0106_4",
                                 "lock_tool": lock_name}}
            fn = f"VIA_Uploads_{s}.html"
            (out / fn).write_text(render_system(lock, site, s, bundle, gen), encoding="utf-8")
            pages[s] = {"file": fn, "rows": {c: len(v) for c, v in M.items()},
                        "lamps": lamp_count([r for v in M.values() for r in v])}
    (out / "index.html").write_text(render_hub(lock, site, inv, kit, mx, pages, docs, gen, lock_ok), encoding="utf-8")
    receipt = {"engine": ENGINE, "generated_utc": gen, "in": str(src), "out": str(out), "lock_tool": lock_name,
               "lock_site_ok": lock_ok, "uploaded": sum(1 for i in inv["items"] if i["copies"]), "expected": len(EXPECTED),
               "items": [{k: v for k, v in i.items() if k != "path"} for i in inv["items"]], "unknown": inv["unknown"],
               "kit": kit, "pages": pages, "docs": list(docs), "warnings": WARNINGS,
               "boundary": "只讀;未執行任何上傳的 .py/.ps1/.html;未連網;未寫任何系統的冊 / 正本 / 號"}
    red = any(i["status"] == "RED" for i in inv["items"]) or (kit.get("present") and (kit["bad"] or kit["missing"]))
    receipt["lamp"] = "RED" if red else ("GREEN" if receipt["uploaded"] == len(EXPECTED) else "YELLOW")
    (out / "uploads_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=1), encoding="utf-8")
    return receipt


def selftest() -> int:
    cases = {
        "4f2a7283-VIA_Subsystem_Workspaces_Review_Kit_v0106_4_20261106_3.zip": KIT,
        "1bf87659-VIA_Subsystem_Workspaces_Review_Kit_v0106_4_20261106.zip_2.sha256": KIT + ".sha256",
        "VIA_Subsystem_Workspaces_Review_Kit_v0106_4_20261106.zip (1).sha256": KIT + ".sha256",
        "42a75dc1-VIA_Matrix_Audit_v0105_1_20261106_2.xlsx": XLSX,
        "VIA_Matrix_Audit_v0105_1_20261106 (1).xlsx": XLSX,
        "3c641c2f-VIA_VCGC___AI_handover___v0106.4_4.md": "VIA VCGC · AI handover · v0106.4.md",
        "71331385-VIA_Governance_MCP_v0105___Windows_____.md": "VIA Governance MCP v0105 — Windows 手動接入.md",
        "mcp_stdio_smoke_v0105_2.py": "mcp_stdio_smoke_v0105_2.py",
        "mcp_stdio_smoke_v0105_2 (1).py": "mcp_stdio_smoke_v0105_2.py",
        "VIA 五系統 RED 阻礙與安全修復計畫 v0105.2.md": "VIA 五系統 RED 阻礙與安全修復計畫 v0105.2.md",
        "random.txt": None,
    }
    bad = {k: (canonical(k), v) for k, v in cases.items() if canonical(k) != v}
    s = md_html("# T\n[x](javascript:alert(1)) <script>a</script>\n```\n<b>\n```")
    safe = "<script>" not in s and "href" not in s and "javascript" not in s
    ok = not bad and safe and len(_EXP_KEYS) == 17
    print(json.dumps({"engine": ENGINE, "selftest": "PASS" if ok else "FAIL", "canonical_bad": bad, "md_safe": safe}, ensure_ascii=False))
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--in", dest="src", help="上傳檔所在資料夾(例 %%USERPROFILE%%\\Downloads)")
    ap.add_argument("--out", default="VIA_Uploads_Workbench_out", help="輸出資料夾(index.html + 各系統頁 + 收據)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.src:
        ap.error("--in 必填")
    r = build(Path(a.src).expanduser(), Path(a.out).expanduser())
    print(json.dumps({k: r.get(k) for k in ("lamp", "engine", "uploaded", "expected", "out", "pages", "warnings", "reason")},
                     ensure_ascii=False, indent=1, default=str))
    return 0 if r.get("lamp") in ("GREEN", "YELLOW") else 1


if __name__ == "__main__":
    sys.exit(main())
