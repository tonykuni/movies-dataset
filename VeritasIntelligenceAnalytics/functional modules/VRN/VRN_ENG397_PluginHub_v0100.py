#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VRN_ENG397_PluginHub v0100 — VRN 樂高化外掛中樞:階段 × 積木註冊 · 計畫選積木 · 外部工具偵測不安裝 · AST 盤點 + 功能分類 · 知識物件

操作員 R37(2026-10-01):「優化個引擎模組化樂高化可拔元件注入AST及功能分類及說明 模組化整合 植入去重修復引擎」。規則冊 VIA_VRN_PluginHub_SSOT_v*.json
(本支照冊讀)。另一份 AI 提案的五段式 / 全工具整合管線,本支落成「同一套積木介面」:內部引擎(ENG392–396)是預設積木;
Docling / MinerU / Surya / Marker / pdfplumber / Camelot / Tabula / PaddleOCR / TATR / Unstructured / Nougat / YOLO / Tesseract 是外部積木,
**執行時以 importlib.util.find_spec 偵測**(不匯入重模型、不安裝):有裝才接上,沒裝誠實標 ABSENT 並退回內部積木。
① probe:每塊積木的狀態(內部:尾版在 · 函式在;外部:AVAILABLE / ABSENT + 版本)。
② catalog:AST 盤點內部積木尾版(含薄尾的前版鏈)每個函式 —— 行號 · 簽章 · 說明(docstring 首行,沒有就標「無說明」)· 功能分類(冊 ast_categories 正則)。
③ register / unregister:執行期加掛積木(LEGO);計畫可指名它,run 會照計畫呼叫。
④ run --in <pdf> [--plan default|xcheck] [--pages 1|all]:版面 / 表格 / 本文 / 去重 / 完整度(ENG394 尾版)→ 主標題 + 分類(ENG393)→ 實體(ENG396)
   → 外部表格積木有裝就互核(只比對,不覆蓋)→ 知識物件(meta · body · tables · figures · excluded · completeness · dedup · entities · providers · fallbacks)。
輸出 VIA_Reports/vrn/plugin_hub/:KO_<檔>.json · HUB_latest.json · HUB_latest.html。零網路;不用 TA-Lib;只收 VCGC 呼叫(--selftest 例外)。
CLI:probe · catalog · run --in <pdf> [--plan p] [--pages s] · --selftest
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
import html as _html
import importlib.metadata
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REG = VIA / "supportive modules" / "registry"
OUT = VIA / "VIA_Reports" / "vrn" / "plugin_hub"
ENGINE = Path(__file__).stem
SSOT_GLOB = "VIA_VRN_PluginHub_SSOT_v*.json"
_BOOK: dict | None = None
_MODS: dict = {}
RUNTIME: dict = {}                     # 執行期加掛的積木 {provider_id: {"stages": [...], "fn": callable, "desc": str}}


def book() -> dict:
    global _BOOK
    if _BOOK is None:
        hits = sorted(REG.glob(SSOT_GLOB))
        if not hits:
            raise FileNotFoundError("規則冊 " + SSOT_GLOB + " 不在 registry")
        _BOOK = json.loads(hits[-1].read_text(encoding="utf-8"))
        _BOOK["_path"] = hits[-1].name
    return _BOOK


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


def tail_path(stem: str) -> Path | None:
    hits = [p for p in HERE.glob(stem + "_v*.py") if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def load(stem: str):
    if stem in _MODS:
        return _MODS[stem]
    p = tail_path(stem)
    mod = None
    if p:
        spec = importlib.util.spec_from_file_location("hub_" + p.stem, p)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
    _MODS[stem] = mod
    return mod


# ---------------------------------------------------------------- ③ 執行期加掛(LEGO)

def register(provider_id: str, stages: list, fn, desc: str = "") -> None:
    RUNTIME[provider_id] = {"stages": list(stages), "fn": fn, "desc": desc, "kind": "runtime"}


def unregister(provider_id: str) -> None:
    RUNTIME.pop(provider_id, None)


# ---------------------------------------------------------------- ① probe

def probe() -> list:
    out = []
    for p in book()["providers"]:
        row = {"id": p["id"], "kind": p["kind"], "stages": p["stages"], "desc": p["desc"]}
        if p["kind"] == "internal":
            tp = tail_path(p["module"])
            row["module"] = tp.name if tp else None
            ok = False
            if tp:
                try:
                    ok = hasattr(load(p["module"]), p["call"])
                except Exception as exc:
                    row["error"] = f"{type(exc).__name__}: {str(exc)[:80]}"
            row["state"] = "AVAILABLE" if ok else "ABSENT"
        else:
            found = [n for n in p.get("imports", []) if importlib.util.find_spec(n) is not None]
            row["state"] = "AVAILABLE" if found and len(found) == len(p.get("imports", [])) or (found and p["id"] == "ext.mineru") else "ABSENT"
            ver = ""
            for n in found:
                try:
                    ver = importlib.metadata.version(n)
                except importlib.metadata.PackageNotFoundError:
                    ver = ver or "?"
            row.update(pip=p.get("pip"), version=ver, found=found)
        out.append(row)
    for pid, r in RUNTIME.items():
        out.append({"id": pid, "kind": "runtime", "stages": r["stages"], "desc": r["desc"], "state": "AVAILABLE"})
    return out


# ---------------------------------------------------------------- ② catalog(AST 盤點 + 功能分類 + 說明)

def _category(name: str, doc: str) -> str:
    for c in book()["ast_categories"]:
        if re.search(c["rx"], name, re.I):
            return c["cat"]
    return "工具"


def _chain(stem: str) -> list:
    """尾版 + 它 glob 到的前版(薄尾)—— 由新到舊。"""
    hits = sorted((p for p in HERE.glob(stem + "_v*.py") if _vnum(p) >= 0), key=_vnum, reverse=True)
    return hits


def catalog(stems: list | None = None) -> list:
    stems = stems or list(dict.fromkeys(p["module"] for p in book()["providers"] if p["kind"] == "internal"))
    out = []
    for stem in stems:
        seen = set()
        for path in _chain(stem):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError as exc:
                out.append({"module": path.name, "name": "(SYNTAX)", "category": "錯誤", "desc": str(exc)[:80], "line": exc.lineno})
                continue
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name not in seen:
                    seen.add(node.name)
                    doc = (ast.get_docstring(node) or "").strip().splitlines()
                    args = [a.arg for a in node.args.args] if isinstance(node, ast.FunctionDef) else []
                    out.append({"module": path.name, "stem": stem, "name": node.name, "kind": "class" if isinstance(node, ast.ClassDef) else "def",
                                "line": node.lineno, "sig": f"{node.name}({', '.join(args)})", "category": _category(node.name, doc[0] if doc else ""),
                                "desc": doc[0][:120] if doc else "(無說明)", "public": not node.name.startswith("_")})
            if not any(isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "_PRIOR_PATH" for t in n.targets) for n in tree.body):
                break                                      # 不是薄尾 → 前版鏈到此為止
    return out


# ---------------------------------------------------------------- 外部積木轉接器(有裝才跑;只當第二讀法)

def _ext_tables(pid: str, path: Path, pages: list) -> dict:
    if pid == "ext.pdfplumber":
        import pdfplumber
        out = []
        with pdfplumber.open(str(path)) as pdf:
            for pno in pages:
                for t in pdf.pages[pno - 1].extract_tables() or []:
                    out.append({"page": pno, "rows": [[(c or "").strip() for c in r] for r in t]})
        return {"tables": out}
    if pid == "ext.camelot":
        import camelot
        tabs = camelot.read_pdf(str(path), pages=",".join(str(p) for p in pages))
        return {"tables": [{"page": int(t.page), "rows": t.df.values.tolist()} for t in tabs]}
    if pid == "ext.tabula":
        import tabula
        dfs = tabula.read_pdf(str(path), pages=pages, multiple_tables=True)
        return {"tables": [{"page": None, "rows": d.astype(str).values.tolist()} for d in dfs]}
    raise NotImplementedError(f"{pid} 沒有表格轉接器")


def _pages_sel(spec: str, n: int) -> list:
    if spec == "all":
        return list(range(1, n + 1))
    m = re.fullmatch(r"(\d+)(?:-(\d+))?", spec or "1")
    a, b = (int(m.group(1)), int(m.group(2) or m.group(1))) if m else (1, 1)
    return [p for p in range(a, b + 1) if 1 <= p <= n]


# ---------------------------------------------------------------- ④ run → 知識物件

def run(path: Path, plan: str = "default", pages: str = "1") -> dict:
    B = book()
    P = dict(B["plans"].get(plan) or B["plans"]["default"])
    states = {r["id"]: r["state"] for r in probe()}
    used, fallbacks, notes = [], [], []

    def pick(stage: str) -> str:
        want = P.get(stage)
        if not want:
            return ""
        if states.get(want) == "AVAILABLE":
            return want
        alt = next((p["id"] for p in B["providers"] if p["kind"] == "internal" and stage in p["stages"] and states.get(p["id"]) == "AVAILABLE"), "")
        fallbacks.append({"stage": stage, "wanted": want, "state": states.get(want, "UNKNOWN"), "used": alt or "—"})
        return alt

    import fitz
    path = Path(path)
    with fitz.open(str(path)) as doc:
        sel = _pages_sel(pages, doc.page_count)
    ko = {"engine": ENGINE, "plan": plan, "file": path.name, "pages": sel, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    lay = pick("layout")
    if lay:
        e394 = load("VRN_ENG394_LayoutRestore")
        res = e394.restore_pdf(path, pages if pages != "1" else "1")
        used.append(lay)
        ko["body"] = [{k: b.get(k) for k in ("no", "sec_no", "title", "cat", "subcategory", "anchor", "size", "bold", "text")} for p in res["pages"] for b in p["body"]]
        ko["tables"] = [{k: t.get(k) for k in ("no", "sub2", "table_no", "title", "columns", "rows", "source", "verdict", "identities", "issues", "anchor")}
                        for p in res["pages"] for t in p["info"]]
        ko["figures"] = [{k: f.get(k) for k in ("no", "sub2", "table_no", "title", "note", "anchor")} for p in res["pages"] for f in p["figures"]]
        ko["excluded"] = [{k: e.get(k) for k in ("anchor", "reason", "head")} for p in res["pages"] for e in p["excluded"]]
        ko["completeness"], ko["dedup"], ko["layout_verdict"] = res.get("completeness"), res.get("dedup"), res.get("verdict")
    t_id = pick("title")
    title = ""
    if t_id:
        e393 = load("VRN_ENG393_DocClassVerify")
        title = (e393.page1_title(path) or {}).get("title", "")
        used.append(t_id)
    ko["title"] = title
    c_id = pick("classify")
    if c_id:
        e393 = load("VRN_ENG393_DocClassVerify")
        cl = e393.classify(path.name, title)
        ko["classification"] = {k: cl.get(k) for k in ("doc_class", "doc_class_zh", "class_confidence", "class_rule", "class_evidence", "ticker",
                                                       "broker_raw", "report_date", "needs_review", "conflict")}
        used.append(c_id)
    en_id = pick("entities")
    if en_id:
        e396 = load("VRN_ENG396_ReportEntities")
        ent = e396.analyze_pdf(path, pages if pages != "1" else "1-2")
        ko["entities"] = {"company": ent["identity"], "mentions": ent["mentions"], "target_price": ent["target_price"], "valuation": ent["valuation"]}
        used.append(en_id)
    xc = []
    for pid in P.get("xcheck_table") or []:
        if states.get(pid) != "AVAILABLE":
            fallbacks.append({"stage": "xcheck_table", "wanted": pid, "state": states.get(pid, "UNKNOWN"), "used": "—(只少一個第二讀法)"})
            continue
        try:
            ext = _ext_tables(pid, path, sel)
            n_int = len(ko.get("tables") or [])
            xc.append({"provider": pid, "tables": len(ext["tables"]), "internal_tables": n_int,
                       "diff": "表數一致" if len(ext["tables"]) == n_int else f"表數 內部 {n_int} ≠ {pid} {len(ext['tables'])}"})
            used.append(pid)
        except Exception as exc:                            # 外部工具自己出錯:記下來,不擋內部結果
            xc.append({"provider": pid, "error": f"{type(exc).__name__}: {str(exc)[:80]}"})
    for pid, r in RUNTIME.items():                          # 執行期加掛的積木:計畫有點名的階段才跑
        if any(P.get(s) == pid or pid in (P.get(s) or []) for s in r["stages"]) or P.get("runtime") == pid:
            ko.setdefault("runtime", {})[pid] = r["fn"](path, ko)
            used.append(pid)
    ko["xcheck"] = xc
    ko["providers"] = {"used": used, "fallbacks": fallbacks}
    ko["notes"] = notes
    return ko


def write_outputs(kos: list, out: Path = OUT) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for ko in kos:
        (out / f"KO_{Path(ko['file']).stem}.json").write_text(json.dumps(ko, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    pr, cat = probe(), catalog()
    (out / "HUB_latest.json").write_text(json.dumps({"engine": ENGINE, "book": book().get("_path"), "probe": pr,
                                                      "catalog_n": len(cat), "runs": [{"file": k["file"], "providers": k["providers"],
                                                                                       "completeness": (k.get("completeness") or {}).get("verdict")} for k in kos]},
                                                     ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "HUB_latest.html").write_text(page_html(pr, cat, kos), encoding="utf-8")


def page_html(pr: list, cat: list, kos: list) -> str:
    e = _html.escape

    def tbl(cols, rows):
        return ("<table class='via'><tr>" + "".join(f"<th>{e(str(c))}</th>" for c in cols) + "</tr>"
                + "".join("<tr>" + "".join(f"<td>{e(str(x))}</td>" for x in r) + "</tr>" for r in rows) + "</table>")
    from collections import Counter
    cc = Counter((c["stem"] if "stem" in c else c["module"], c["category"]) for c in cat)
    stems = sorted({k[0] for k in cc})
    cats = sorted({k[1] for k in cc})
    body = ("<h3>積木矩陣(階段 × 積木 · 狀態)</h3>" + tbl(["積木", "類", "階段", "狀態", "版本 / 尾版", "說明"],
                                                     [[r["id"], r["kind"], " / ".join(r["stages"]), r["state"], r.get("version") or r.get("module") or "",
                                                       r["desc"]] for r in pr])
            + "<h3>AST 盤點 · 功能分類矩陣(函式數)</h3>" + tbl(["模組"] + cats, [[s] + [cc.get((s, c), 0) for c in cats] for s in stems])
            + "<h3>AST 盤點明細</h3>" + tbl(["模組", "行", "簽章", "分類", "說明"], [[c["module"], c.get("line"), c.get("sig", c["name"]), c["category"], c["desc"]]
                                                                      for c in cat])
            + "<h3>執行摘要</h3>" + tbl(["檔", "用到的積木", "退回", "截取完整度", "分類", "目標價(調整前)"],
                                      [[k["file"], " · ".join(k["providers"]["used"]), " · ".join(f"{f['wanted']}→{f['used']}" for f in k["providers"]["fallbacks"]),
                                        (k.get("completeness") or {}).get("verdict", "—"), (k.get("classification") or {}).get("doc_class", "—"),
                                        f"{((k.get('entities') or {}).get('target_price') or {}).get('current')}({((k.get('entities') or {}).get('target_price') or {}).get('prior')})"]
                                       for k in kos]))
    return f"<!doctype html><meta charset='utf-8'><title>VRN 外掛中樞</title><style>body{{font-family:system-ui,sans-serif;margin:16px}}table{{border-collapse:collapse;font-size:13px}}td,th{{border:1px solid #ccc;padding:3px 6px}}</style>{body}"


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    verb = args[0] if args else "probe"
    if verb == "probe":
        for r in probe():
            print(f"  {r['state']:<10} {r['id']:<22} {'/'.join(r['stages']):<34} {r.get('version') or r.get('module') or ''}")
        return 0
    if verb == "catalog":
        cat = catalog()
        from collections import Counter
        print(f"[外掛中樞 · AST 盤點] {len(cat)} 個定義 · " + " · ".join(f"{k} {v}" for k, v in Counter(c['category'] for c in cat).most_common()))
        return 0
    if verb == "run":
        given = [args[i + 1] for i, a in enumerate(args) if a == "--in" and i + 1 < len(args)]
        plan = args[args.index("--plan") + 1] if "--plan" in args else "default"
        pages = args[args.index("--pages") + 1] if "--pages" in args else "1"
        kos = []
        for g in given:
            p = Path(g)
            for f in (sorted(p.rglob("*.pdf")) if p.is_dir() else [p]):
                kos.append(run(f, plan, pages))
                k = kos[-1]
                print(f"  {f.name[:60]} · 分類 {(k.get('classification') or {}).get('doc_class')} · 完整度 {(k.get('completeness') or {}).get('verdict')} · "
                      f"積木 {len(k['providers']['used'])} · 退回 {len(k['providers']['fallbacks'])}")
        if not kos:
            print("[外掛中樞] 沒有輸入")
            return 2
        write_outputs(kos)
        print(f"[外掛中樞] {len(kos)} 份 · 頁 {OUT / 'HUB_latest.html'}")
        return 0
    print("用法:probe | catalog | run --in <pdf|夾> [--plan default|xcheck] [--pages 1|all] | --selftest")
    return 2


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    B = book()
    pr = {r["id"]: r for r in probe()}
    chk("規則冊:11 階段 · 6 內部積木 · 13 外部積木 · 2 計畫", len(B["stages"]) == 11 and sum(p["kind"] == "internal" for p in B["providers"]) == 6
        and sum(p["kind"] == "external" for p in B["providers"]) == 13 and set(B["plans"]) >= {"default", "xcheck"})
    chk("probe:內部積木全 AVAILABLE(尾版在 · 函式在)", all(pr[p]["state"] == "AVAILABLE" for p in pr if p.startswith("int.")),
        {p: pr[p]["state"] for p in pr if p.startswith("int.")})
    chk("probe:外部積木只偵測不匯入 —— 狀態只有 AVAILABLE / ABSENT,沒有例外", all(pr[p]["state"] in ("AVAILABLE", "ABSENT") for p in pr if p.startswith("ext.")))
    body = Path(__file__).read_text(encoding="utf-8")
    chk("中樞不安裝套件(沒有 pip install / subprocess)", not re.search(r"pip\s+install|subprocess|os\.system", body.split("def selftest")[0]))
    cat = catalog()
    mods = {c["stem"] for c in cat if "stem" in c}
    chk("AST 盤點:ENG392 / 393 / 394 / 395 / 396 都在 · 含薄尾前版鏈(ENG394 v0101 + v0100 · ENG393 v0101 + v0100)",
        {"VRN_ENG392_TextCompleteness", "VRN_ENG393_DocClassVerify", "VRN_ENG394_LayoutRestore", "VRN_ENG395_ValuationMethodLexicon",
         "VRN_ENG396_ReportEntities"} <= mods and {c["module"] for c in cat if c.get("stem") == "VRN_ENG394_LayoutRestore"}
        >= {"VRN_ENG394_LayoutRestore_v0101.py", "VRN_ENG394_LayoutRestore_v0100.py"}, mods)
    cats = {c["category"] for c in cat}
    chk("功能分類 ≥ 8 類(自測 · 入口 · 輸出 · 去重 · 驗證 · 表格 · 版面 · 擷取 …)", len(cats) >= 8 and {"去重", "表格", "版面", "驗證"} <= cats, cats)
    nodoc = sum(c["desc"] == "(無說明)" for c in cat)
    chk("每個定義都有說明欄(沒有 docstring 誠實標「無說明」,不編造)", all(c["desc"] for c in cat), nodoc)
    with tempfile.TemporaryDirectory() as td:
        pdf = load("VRN_ENG394_LayoutRestore").make_pdf(Path(td) / "南亞(1303,B_買進)-CTBC260918.pdf")
        ko = run(pdf, "default", "1")
        chk("run default:知識物件有 body · tables · figures · excluded · completeness · dedup · title · classification · entities",
            all(k in ko for k in ("body", "tables", "figures", "excluded", "completeness", "dedup", "title", "classification", "entities")), list(ko))
        chk("知識物件:本文一句一列帶 S 編號 · 節.句 · 所屬標題 · 類別", ko["body"] and all(b["no"] and b["sec_no"] and b["title"] and b["cat"] for b in ko["body"]))
        chk("知識物件:截取完整度 GREEN · 分類 STOCK(檔名代號 1303)", (ko["completeness"] or {}).get("verdict") == "GREEN"
            and ko["classification"]["doc_class"] == "STOCK" and ko["classification"]["ticker"] == "1303", (ko.get("completeness", {}).get("verdict"), ko.get("classification")))
        chk("用到的積木 = 計畫 default 的四塊內部積木 · 沒有退回", ko["providers"]["used"] == ["int.eng394.restore", "int.eng393.title", "int.eng393.classify",
                                                                                 "int.eng396.entities"] and not ko["providers"]["fallbacks"], ko["providers"])
        ko2 = run(pdf, "xcheck", "1")
        absent = [f["wanted"] for f in ko2["providers"]["fallbacks"]]
        chk("計畫 xcheck:外部 pdfplumber / camelot 沒裝 → 誠實記退回(只少第二讀法,內部結果不變)",
            all(pr[a]["state"] == "ABSENT" for a in absent) and ko2["body"] == ko["body"], absent)
        B["plans"]["lego"] = {**B["plans"]["default"], "runtime": "rt.wordcount"}
        register("rt.wordcount", ["text"], lambda path, k: {"sentences": len(k.get("body") or [])}, "執行期加掛:句數統計")
        ko3 = run(pdf, "lego", "1")
        chk("LEGO:執行期加掛積木 → 計畫點名就跑 · 結果進知識物件", ko3.get("runtime", {}).get("rt.wordcount", {}).get("sentences") == len(ko["body"])
            and "rt.wordcount" in ko3["providers"]["used"])
        unregister("rt.wordcount")
        chk("LEGO:拔掉後不再出現在 probe", "rt.wordcount" not in {r["id"] for r in probe()})
        B["plans"].pop("lego")
        B["plans"]["broken"] = {**B["plans"]["default"], "layout": "ext.docling"}
        ko4 = run(pdf, "broken", "1")
        chk("計畫指名的外部版面積木 ABSENT → 退回內部 int.eng394.restore(記在 fallbacks)",
            ko4["providers"]["fallbacks"][0]["used"] == "int.eng394.restore" and "body" in ko4, ko4["providers"]["fallbacks"])
        B["plans"].pop("broken")
        write_outputs([ko], Path(td) / "out")
        h = (Path(td) / "out" / "HUB_latest.html").read_text(encoding="utf-8")
        chk("輸出:KO_*.json · HUB_latest.json · HUB_latest.html(積木矩陣 · AST 分類矩陣 · 執行摘要)",
            (Path(td) / "out" / f"KO_{pdf.stem}.json").exists() and "積木矩陣" in h and "功能分類矩陣" in h and "執行摘要" in h)
    chk("帶加速器橋 · VIA_FROM_VCGC 閘 · 不匯入 TA-Lib · 不碰網路", "[VIA:ACCEL-BRIDGE" in body and 'os.environ.get("VIA_FROM_VCGC") != "YES"' in body
        and not re.search(r"^\s*(import|from)\s+(" + "ta" + r"lib|requests|urllib)\b", body, re.M))
    print(f"[VRN_ENG397 v0100 外掛中樞] 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
