#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL253_ToolingInventory v0102 — 薄尾:備料卡補 ⑧ 輸出 · ⑨ 掛入的工具 · ⑩ AST 定位與編號;新子令 engine tools(VRN / VDF 工具鏈全景)

操作員(2026-10-03,VCGC-REQ134):「全景式檢視 VRN VDF 一切輸入 參數 輸出 · VRN 有 NLP / LAYOUT 支援確保版本都要註冊 ·
PRADDLE PDFPLUMBER 相關 OCR 工具都有掛入並編號 · AST 定位好編號好」。v0101(①–⑦ 輸入參數 · 環境變數 · SSOT · regex · 同義字 ·
工作流步 · 短令)一字不動;本版在同一張卡上加三段(都沿薄尾鏈收,只讀):
  ⑧ 輸出:原始碼裡的 SQL 寫表(CREATE [OR REPLACE] TABLE · INSERT INTO)· 輸出檔(VIA_Reports/ · output_hub/ · .duckdb · .parquet 字面;
     f-string 另計動態)· 中央表頭冊 VIA_Output_Header_SSOT 尾版裡 owner = 本家族的輸出表(欄數 · 下限列數 · 來源)· VDF 輸入範圍冊 writes
  ⑨ 掛入的工具:工具鎖冊各家(layout · nlp · praddle · pdfplumber · ocr · frame …)本支有沒有用到(原始碼提到該家檔名幹)
     與該家鎖版狀態(PINNED 版號 / 冊上沒有);PDF / OCR 套件匯入(fitz · pdfplumber · pypdf · rapidocr · paddleocr · pytesseract · easyocr · cv2)
  ⑩ AST 定位 · 編號:鏈上每一版的中央編號(VIA_NumberBooks)與全景 AST 問題(類別 · 行號)
新子令(只讀):
  engine tools [--json]   工具鏈全景:VRN = layout · nlp · praddle · pdfplumber · ocr 與其樞紐(NLP 應用樞紐 SUP_MDL744 · 結構樞紐 SUP_MDL745 ·
                          LAYOUT 子檔 SUP_MDL743_Layout* · 版面還原 VRN_ENG394 · NLP 橋 VRN_ENG087);VDF = accelerator · network · frame
                          每一家每一版:中央編號 · 元件冊自己的紀錄(沒有 = 同名函式身分歸新版,照實標)· 鎖冊(現役 / 前版 / 沒鎖)· AST 問題 ·
                          加速器橋;寫 VIA_Reports/tooling/TOOLS_<子系統>_latest.json / .html
燈:紅 = 尾版沒編號或 AST 讀不過;黃 = 該鎖沒鎖 / 尾版不是鎖冊現役 / 有 AST 提醒;綠 = 都齊。只讀;零網路;不用 TA-Lib;不代設同意閘。
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

import ast
import contextlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL253_ToolingInventory"
_VRX_V0102 = re.compile(r"[-_]v(\d{4})$")


def _vnum_v0102(p) -> int:
    m = _VRX_V0102.search(Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0102(p) < _vnum_v0102(__file__)), key=_vnum_v0102)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0101:params / prep(①–⑦)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.PRIOR                                      # v0100:盤點 · engines · gate · _card · number_index
VIA = PRIOR.VIA
ENGINE = Path(__file__).stem
SQL_RX_V0102 = re.compile(r"(?i)\b(?:CREATE\s+(?:OR\s+REPLACE\s+)?(?:TEMP(?:ORARY)?\s+)?TABLE(?:\s+IF\s+NOT\s+EXISTS)?|INSERT\s+(?:OR\s+\w+\s+)?INTO)\s+\"?([A-Za-z_][\w.]*)")
OUT_RX_V0102 = re.compile(r"(VIA_Reports[/\\]|output_hub[/\\]|\.duckdb$|\.parquet$)")
OCR_PKGS_V0102 = ("fitz", "pymupdf", "pdfplumber", "pypdf", "pdfminer", "camelot", "rapidocr_onnxruntime", "rapidocr", "paddleocr", "paddle",
                  "pytesseract", "easyocr", "cv2", "doctr")
TOOL_SETS_V0102 = {
    "VRN": {"locked": ("layout", "nlp", "praddle", "pdfplumber", "ocr"),
            "hubs": (("supportive modules/70_VRN_Rules", "SUP_MDL744_NLPApplicationHub"), ("supportive modules/70_VRN_Rules", "SUP_MDL745_MarkdownStructureHub"),
                     ("supportive modules/70_VRN_Rules/layout_repair_v0100", "SUP_MDL743_Layout*"), ("functional modules/VRN", "VRN_ENG394_LayoutRestore"),
                     ("functional modules/VRN", "VRN_ENG087_NLPTextSummaryBridge"))},
    "VDF": {"locked": ("accelerator", "network", "frame"), "hubs": ()},
}


def __getattr__(name):
    return getattr(PRIOR, name)


def _lock_v0102() -> dict:
    try:
        return json.loads(BASE.LOCK.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _stem_of_v0102(path: str) -> str:
    return re.sub(r"_v\d{4}$", "", Path(str(path)).stem)


# ---------------------------------------------------------------- ⑧ 輸出
def outputs_v0102(tree, family: str, sub: str, universe: list | None = None) -> dict:
    tables, files, dyn = set(), set(), 0
    in_fstr = {id(v) for n in (ast.walk(tree) if tree else []) if isinstance(n, ast.JoinedStr) for v in n.values}
    for node in ast.walk(tree) if tree else []:
        if isinstance(node, ast.JoinedStr):
            txt = "".join(v.value for v in node.values if isinstance(v, ast.Constant) and isinstance(v.value, str))
            if OUT_RX_V0102.search(txt) or SQL_RX_V0102.search(txt):
                dyn += 1
                vals = node.values
                for k, part in enumerate(vals):          # 表名後面緊接 {…} = 名字有一段是動態的 → 記成 名字*
                    if isinstance(part, ast.Constant) and isinstance(part.value, str):
                        for m in SQL_RX_V0102.finditer(part.value):
                            glued = m.end() == len(part.value) and k + 1 < len(vals) and isinstance(vals[k + 1], ast.FormattedValue)
                            tables.add(m.group(1) + ("*" if glued else ""))
            continue
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and len(node.value) < 4000 and id(node) not in in_fstr:
            for m in SQL_RX_V0102.finditer(node.value):
                tables.add(m.group(1))
            v = node.value.replace("\\", "/")
            if len(v) < 240 and OUT_RX_V0102.search(v) and "\n" not in v:
                files.add(v)
    header = []
    hb = sorted((VIA / "supportive modules" / "registry").glob("VIA_Output_Header_SSOT_v*.json"), key=_vnum_v0102)
    if hb:
        try:
            for name, t in (json.loads(hb[-1].read_text(encoding="utf-8")).get("tables") or {}).items():
                if isinstance(t, dict) and str(t.get("owner", "")) == family:
                    src = t.get("source") or {}
                    header.append({"table": name, "columns": len(t.get("columns") or []), "min_rows": t.get("min_rows"),
                                   "store": f"{src.get('kind', '')}:{src.get('path', '')}::{src.get('table', '')}"})
        except (OSError, ValueError):
            pass
    writes = sorted({w for u in (universe or []) for w in (u.get("writes") or [])})
    return {"sql_tables": sorted(tables)[:40], "files": sorted(files)[:40], "dynamic": dyn, "header_book": hb[-1].name if hb else "",
            "header_tables": header, "universe_writes": writes}


# ---------------------------------------------------------------- ⑨ 掛入的工具
def tools_used_v0102(src: str, tree, lock: dict) -> dict:
    fams = []
    for fam, ent in lock.items():
        if not isinstance(ent, dict) or not ent.get("path"):
            continue
        stem = _stem_of_v0102(ent["path"])
        if stem and stem in src:
            fams.append({"family": fam, "stem": stem, "pinned": ent.get("version", "")})
    pkgs = set()
    for node in ast.walk(tree) if tree else []:
        if isinstance(node, ast.Import):
            pkgs.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            pkgs.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("import_module", "find_spec") \
                and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            pkgs.add(node.args[0].value.split(".")[0])
    return {"locked_tools": fams, "pdf_ocr_packages": sorted(p for p in pkgs if p in OCR_PKGS_V0102)}


# ---------------------------------------------------------------- ⑩ AST 定位 · 編號
def ast_numbers_v0102(chain: list, nums: dict) -> list:
    out = []
    for q in chain:
        r = BASE.rel(q)
        try:
            card = BASE._card(str(q))
        except Exception as e:                          # 讀卡失敗照實記,不中斷整張
            card = {"issues": [{"cls": "READ", "line": 0, "detail": type(e).__name__}]}
        iss = [i for i in card.get("issues", []) if not i.get("exempt")]
        out.append({"version": f"v{_vnum_v0102(q):04d}", "path": r, "code": (nums.get(r) or {}).get("code") or "未編號",
                    "issues": [f"{i['cls']} L{i.get('line', 0)} {str(i.get('detail', ''))[:60]}" for i in iss][:12],
                    "red": any(i["cls"] in BASE.RED_CLS for i in iss)})
    return out


# ---------------------------------------------------------------- 卡:v0101 的 ①–⑦ + ⑧⑨⑩
def params_card_v0102(row: dict, sub: str, central: dict | None = None, idx: dict | None = None,
                      lock: dict | None = None, nums: dict | None = None) -> dict:
    c = PRIOR.params_card_v0101(row, sub, central, idx)
    chain = [VIA / row["path"]]
    chain = PRIOR.chain_files_v0101(chain[0])
    mods, srcs = [], []
    for q in chain:
        txt = q.read_text(encoding="utf-8", errors="replace")
        srcs.append(txt)
        try:
            mods.extend(ast.parse(txt).body)
        except SyntaxError:
            pass
    tree = ast.Module(body=mods, type_ignores=[]) if mods else None
    src = "\n".join(srcs)
    lock = lock if lock is not None else _lock_v0102()
    nums = nums if nums is not None else BASE.number_index()
    c["outputs"] = outputs_v0102(tree, row["family"], sub.upper(), (c.get("workflow") or {}).get("universe"))
    c["tools"] = tools_used_v0102(src, tree, lock)
    c["ast_numbers"] = ast_numbers_v0102(chain, nums)
    if any(a["red"] for a in c["ast_numbers"]):
        c["notes"].append("鏈上有 AST 讀不過的版:" + " · ".join(a["version"] for a in c["ast_numbers"] if a["red"]))
        if c["lamp"] in ("GREEN", "YELLOW"):
            c["lamp"] = "RED"
    if c["ast_numbers"] and c["ast_numbers"][0]["code"] == "未編號":
        c["notes"].append("尾版未編號(下一輪 closeout 的編號會補)")
        if c["lamp"] == "GREEN":
            c["lamp"] = "YELLOW"
    return c


def _print_card_v0102(c: dict, tag: str) -> None:
    PRIOR._print_card_v0101(c, tag)
    o = c["outputs"]
    print(f"  ⑧ 輸出 寫表 {' · '.join(o['sql_tables'][:10]) or '—'}" + (f" · 動態 {o['dynamic']} 處" if o["dynamic"] else ""))
    for f in o["files"][:10]:
        print(f"     檔 {f}")
    for h in o["header_tables"]:
        print(f"     表頭冊 {h['table']}:{h['columns']} 欄 · 下限 {h['min_rows']} 列 · {h['store']}")
    if o["universe_writes"]:
        print(f"     輸入範圍冊 writes {' · '.join(o['universe_writes'])}")
    t = c["tools"]
    print(f"  ⑨ 掛入的工具 " + (" · ".join(f"{x['family']}({x['stem']} 鎖 {x['pinned']})" for x in t["locked_tools"]) or "—")
          + f" · PDF/OCR 套件 {' '.join(t['pdf_ocr_packages']) or '—'}")
    print("  ⑩ AST 定位 · 編號 " + " → ".join(f"{a['version']} {a['code']}" + (f" ⚠{len(a['issues'])}" if a["issues"] else "") for a in c["ast_numbers"]))
    for a in c["ast_numbers"]:
        for i in a["issues"][:4]:
            print(f"     {a['path']}  {i}")


# ---------------------------------------------------------------- engine tools:工具鏈全景
def _family_files_v0102(folder: Path, stem_glob: str) -> list:
    out = []
    for p in folder.glob(stem_glob + "_v*.py") if "*" not in stem_glob else folder.glob(stem_glob + ".py"):
        if _vnum_v0102(p) >= 0 and not re.search(r"_sha[0-9a-f]{6,}$", p.stem):
            out.append(p)
    return out


def tool_panorama_v0102(sub: str) -> dict:
    sub = sub.upper()
    spec = TOOL_SETS_V0102.get(sub, {"locked": (), "hubs": ()})
    lock = _lock_v0102()
    nums = BASE.number_index()
    inv_srcs = set()
    inv_path = HERE / "VIA_Component_Inventory_SSOT_v0100.json"
    try:
        inv_srcs = {r.get("source") for r in json.loads(inv_path.read_text(encoding="utf-8")).get("records") or []}
    except (OSError, ValueError):
        pass
    pan, _ = BASE.panorama_path()
    if pan is not None:
        BASE._pan_init(str(pan))
    groups = []
    targets = []
    for fam in spec["locked"]:
        ent = lock.get(fam) or {}
        p = BASE.REPO / str(ent.get("path") or "")
        if ent.get("path") and p.is_file():
            targets.append((fam, p.parent, _stem_of_v0102(p), ent))
        else:
            targets.append((fam, None, "", ent))
    for folder, stem in spec["hubs"]:
        targets.append(("hub", VIA / folder, stem, {}))
    for fam, folder, stem, ent in targets:
        files = []
        if folder is not None:
            files = _family_files_v0102(folder, stem) if "*" not in stem else [p for p in folder.glob(stem + "_v*.py") if _vnum_v0102(p) >= 0]
        by_stem = {}
        for p in files:
            by_stem.setdefault(_stem_of_v0102(p), []).append(p)
        if not by_stem:
            groups.append({"family": fam, "stem": stem or "—", "lock": ent.get("version", ""), "lamp": "RED" if fam != "hub" else "YELLOW",
                           "why": "鎖冊沒有這一家" if fam != "hub" and not ent else "檔不在", "versions": []})
            continue
        for st, ps in sorted(by_stem.items()):
            ps = sorted(ps, key=_vnum_v0102, reverse=True)
            prev = (ent.get("previous") or {}).get("path", "")
            vers = []
            for p in ps:
                r = BASE.rel(p)
                try:
                    card = BASE._card(str(p))
                    iss = [i for i in card.get("issues", []) if not i.get("exempt")]
                except Exception:
                    iss = [{"cls": "READ", "line": 0}]
                text = p.read_text(encoding="utf-8", errors="replace")
                role = "現役" if ent.get("path", "").endswith("/" + p.name) else ("前版" if prev.endswith("/" + p.name) else "")
                vers.append({"version": f"v{_vnum_v0102(p):04d}", "path": r, "code": (nums.get(r) or {}).get("code") or "未編號",
                             "own_record": r in inv_srcs, "lock_role": role, "accel": BASE.PY_MARK in text,
                             "issues": [f"{i['cls']} L{i.get('line', 0)}" for i in iss][:8], "red": any(i["cls"] in BASE.RED_CLS for i in iss)})
            tail = vers[0]
            why = []
            if tail["code"] == "未編號":
                why.append("尾版未編號")
            if tail["red"]:
                why.append("尾版 AST 讀不過")
            if fam not in ("hub",) and not tail["lock_role"]:
                why.append("尾版不是鎖冊現役(" + (ent.get("version") or "沒鎖") + ")")
            if not tail["accel"]:
                why.append("尾版缺加速器橋")
            soft = [v["version"] for v in vers if v["issues"]]
            lamp = "RED" if any(w.startswith("尾版未編號") or "讀不過" in w for w in why) else ("YELLOW" if why or soft else "GREEN")
            groups.append({"family": fam, "stem": st, "lock": ent.get("version", ""), "lamp": lamp,
                           "why": "; ".join(why + ([f"AST 提醒在 {' '.join(soft[:6])}"] if soft else [])), "versions": vers})
    lamps = {k: sum(1 for g in groups if g["lamp"] == k) for k in ("GREEN", "YELLOW", "RED")}
    allv = [v for g in groups for v in g["versions"]]
    summary = {"groups": len(groups), "lamps": lamps, "versions": len(allv), "numbered": sum(1 for v in allv if v["code"] != "未編號"),
               "own_record": sum(1 for v in allv if v["own_record"]), "locked_families": sum(1 for g in groups if g["family"] != "hub" and g["lock"])}
    return {"sub": sub, "at": time.strftime("%Y-%m-%d %H:%M:%S"), "by": ENGINE, "summary": summary, "groups": groups}


def write_tools_page_v0102(doc: dict, out_dir: Path) -> Path:
    spec = BASE._load(BASE._newest("CGC_MDL173_MatrixReportSpec_v*.py"), "_mdl253_spec_v0102")
    rows = []
    for g in doc["groups"]:
        for v in g["versions"] or [{"version": "—", "code": "—", "own_record": False, "lock_role": "", "accel": False, "issues": [], "path": ""}]:
            rows.append([{"t": g["lamp"], "s": g["lamp"]}, g["family"], g["stem"], v["version"], v["code"], "有" if v["own_record"] else "身分歸新版",
                         v["lock_role"] or "—", "✓" if v["accel"] else "✗", " ".join(v["issues"]) or "—", g["why"] or "—"])
    s = doc["summary"]
    body = spec.html_table(["燈", "家", "檔名幹", "版", "中央編號", "元件冊紀錄", "鎖冊", "加速器橋", "AST", "說明"], rows,
                           caption=f"{doc['sub']} 工具鏈全景:{s['groups']} 組 · {s['versions']} 版", center_cols={0})
    kpis = [{"label": "組", "value": s["groups"], "state": "NA"}, {"label": "版", "value": s["versions"], "state": "NA"},
            {"label": "已編號", "value": s["numbered"], "state": "GREEN" if s["numbered"] == s["versions"] else "RED"},
            {"label": "紅", "value": s["lamps"]["RED"], "state": "RED" if s["lamps"]["RED"] else "GREEN"}]
    return spec.page_html(body, title=f"{doc['sub']} 工具鏈全景(鎖冊 · 編號 · AST)", out=out_dir / f"TOOLS_{doc['sub']}_latest.html", kpis=kpis,
                          payload={"summary": s}, md="", subtitle=f"{doc['at']} · engine tools · {ENGINE}",
                          law="只讀;元件冊以「家族:函式名」為身分,舊版同名函式的紀錄歸新版 = 照實標「身分歸新版」,版號本身由中央編號冊編號。")


# ---------------------------------------------------------------- 動詞
def prep_v0102(sub: str, write: bool = True, out_dir: Path | None = None) -> dict:
    doc = PRIOR.prep_v0101(sub, write=False)
    lock, nums = _lock_v0102(), BASE.number_index()
    rows = BASE.engines(sub.upper())
    by_path = {r["path"]: r for r in rows}
    cards = []
    for c in doc["cards"]:
        r = by_path.get(c["path"])
        if r is None:
            cards.append(c)
            continue
        short = c["launch"]["short"]
        c2 = params_card_v0102(r, sub, lock=lock, nums=nums)
        c2["launch"]["short"] = short
        cards.append(c2)
    doc["cards"] = cards
    s = doc["summary"]
    s["lamps"] = {k: sum(1 for c in cards if c["lamp"] == k) for k in ("GREEN", "YELLOW", "RED", "NA")}
    s["with_outputs"] = sum(1 for c in cards if c.get("outputs", {}).get("sql_tables") or c.get("outputs", {}).get("files") or c.get("outputs", {}).get("header_tables"))
    s["uses_locked_tools"] = sum(1 for c in cards if c.get("tools", {}).get("locked_tools"))
    s["unnumbered_tails"] = sum(1 for c in cards if c.get("ast_numbers") and c["ast_numbers"][0]["code"] == "未編號")
    doc["by"] = ENGINE
    if write:
        od = Path(out_dir or BASE.OUT)
        od.mkdir(parents=True, exist_ok=True)
        (od / f"ENGINE_PARAMS_{doc['sub']}_latest.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        doc["page"] = str(PRIOR.write_params_page_v0101(doc, od))
    return doc


def engine_main(sub: str, args: list, tag: str) -> int:
    verb, rest = (args[0], list(args[1:])) if args else ("list", [])
    as_json = "--json" in rest
    if verb == "tools":
        doc = tool_panorama_v0102(sub)
        od = BASE.OUT
        od.mkdir(parents=True, exist_ok=True)
        (od / f"TOOLS_{doc['sub']}_latest.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        page = write_tools_page_v0102(doc, od)
        s = doc["summary"]
        if as_json:
            print(json.dumps({"engine_tools": doc}, ensure_ascii=False))
        else:
            print(f"[{tag} 工具鏈全景] {doc['sub']} {s['groups']} 組 · {s['versions']} 版 · 已編號 {s['numbered']} · 元件冊自有紀錄 {s['own_record']}"
                  f" · 鎖冊家 {s['locked_families']} · 綠 {s['lamps']['GREEN']} · 黃 {s['lamps']['YELLOW']} · 紅 {s['lamps']['RED']}")
            for g in doc["groups"]:
                mark = {"GREEN": "綠", "YELLOW": "黃", "RED": "紅"}[g["lamp"]]
                vs = " · ".join(f"{v['version']} {v['code']}{'*' if v['lock_role'] == '現役' else ''}" for v in g["versions"][:6])
                print(f"  {mark} {g['family']:<10} {g['stem'][:40]:<40} 鎖 {g['lock'] or '—':<6} {vs}" + (f"  ← {g['why']}" if g["why"] else ""))
            print(f"  [頁] {page}")
        return 1 if doc["summary"]["lamps"]["RED"] else 0
    if verb == "prep":
        doc = prep_v0102(sub, write="--no-page" not in rest)
        s = doc["summary"]
        if as_json:
            print(json.dumps({"engine_prep": {k: v for k, v in doc.items() if k != "cards"}}, ensure_ascii=False))
        else:
            print(f"[{tag} 單引擎備料] {doc['sub']} {s['engines']} 支 · 綠 {s['lamps']['GREEN']} · 黃 {s['lamps']['YELLOW']} · 紅 {s['lamps']['RED']} · 庫 {s['lamps']['NA']}"
                  f" · 有參數 {s['with_cli']} · 讀冊 {s['with_books']} · 有輸出 {s['with_outputs']} · 用鎖冊工具 {s['uses_locked_tools']}"
                  f" · 尾版未編號 {s['unnumbered_tails']} · 本地同義字表 {s['local_synonym_tables']} · 要同意閘 {s['consent']} 支")
            if doc.get("page"):
                print(f"  [頁] {doc['page']}")
        return 1 if s["lamps"]["RED"] else 0
    if verb == "params":
        rows_rest = [a for a in rest if a != "--json"]
        if not rows_rest:
            return PRIOR.engine_main(sub, list(args), tag)
        try:
            rows = BASE.engines(sub.upper())
        except RuntimeError as e:
            print(json.dumps({"engine_params": {"sub": sub.upper(), "lamp": "RED", "why": str(e)}}, ensure_ascii=False))
            return 1
        row, cands = BASE.resolve(rows, rows_rest[0])
        if row is None:
            return PRIOR.engine_main(sub, list(args), tag)
        c = params_card_v0102(row, sub)
        if not as_json:
            _print_card_v0102(c, tag)
        print(json.dumps({"engine_params": c}, ensure_ascii=False))
        return {"GREEN": 0, "YELLOW": 2, "RED": 1, "NA": 2}[c["lamp"]]
    return PRIOR.engine_main(sub, list(args), tag)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    rc = PRIOR.selftest()
    print(f"=== {ENGINE} · 薄尾自測(⑧ 輸出 · ⑨ 掛入的工具 · ⑩ AST 定位與編號 · engine tools)===")
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    chk("① 前版 v0101 自測過(①–⑦ 照舊)", rc == 0, f"rc {rc}")
    demo = ("import pdfplumber, fitz\nimport importlib\nOUT = 'VIA_Reports/vrn/demo/DEMO_latest.json'\nDB = 'functional modules/VRN/output_hub/demo.duckdb'\n"
            "LAY = 'supportive modules/70_VRN_Rules/SUP_MDL743_GenericLayoutHub_v0110.py'\n"
            "def run(con, day):\n    con.execute('CREATE TABLE IF NOT EXISTS demo_rows(a INT)')\n    con.execute(\"INSERT INTO demo_rows VALUES (1)\")\n"
            "    con.execute(f'CREATE OR REPLACE TABLE demo_{day} AS SELECT 1')\n    importlib.util.find_spec('rapidocr_onnxruntime')\n")
    tree = ast.parse(demo)
    o = outputs_v0102(tree, "VRN_ENG999_Demo", "VRN")
    chk("② 輸出:SQL 寫表(CREATE / INSERT)· 輸出檔(VIA_Reports · .duckdb)· f-string 動態另計",
        set(o["sql_tables"]) == {"demo_rows", "demo_*"} and "VIA_Reports/vrn/demo/DEMO_latest.json" in o["files"]
        and "functional modules/VRN/output_hub/demo.duckdb" in o["files"] and o["dynamic"] >= 1, o)
    lock = {"layout": {"path": "VeritasIntelligenceAnalytics/supportive modules/70_VRN_Rules/SUP_MDL743_GenericLayoutHub_v0110.py", "version": "v0110"},
            "nlp": {"path": "x/SUP_MDL866_VIAUnifiedNLPOrchestrator_v0106.py", "version": "v0106"}}
    t = tools_used_v0102(demo, tree, lock)
    chk("③ 掛入的工具:提到 LAYOUT 檔名幹 = 用到鎖冊 layout(帶鎖版號)· 沒提 NLP = 不列 · PDF/OCR 套件匯入(含 find_spec)",
        [x["family"] for x in t["locked_tools"]] == ["layout"] and t["locked_tools"][0]["pinned"] == "v0110"
        and t["pdf_ocr_packages"] == ["fitz", "pdfplumber", "rapidocr_onnxruntime"], t)
    try:
        vrn = BASE.engines("VRN")
        one, _ = BASE.resolve(vrn, "VRN_ENG398_PraddleExtractor")
        c = params_card_v0102(one, "VRN") if one else {}
        chk("④ 實樹 VRN:ENG398 卡多 ⑧⑨⑩ · 用到 layout(鎖冊)· 匯入層 OCR 套件不在主行程(只列字面)· 尾版有中央編號",
            bool(one) and all(k in c for k in ("outputs", "tools", "ast_numbers")) and c["ast_numbers"][0]["code"].startswith("VIA-"),
            (c.get("lamp"), [x["family"] for x in c.get("tools", {}).get("locked_tools", [])], c.get("ast_numbers", [{}])[0].get("code")))
        doc = tool_panorama_v0102("VRN")
        fams = {g["family"] for g in doc["groups"]}
        chk("⑤ engine tools(VRN):layout · nlp · praddle · pdfplumber · ocr 五家都在組裡 · 每一版都有中央編號",
            {"layout", "nlp", "praddle", "pdfplumber", "ocr"} <= fams and doc["summary"]["numbered"] == doc["summary"]["versions"],
            (sorted(fams), doc["summary"]))
        lay = next((g for g in doc["groups"] if g["family"] == "layout"), {})
        chk("⑥ LAYOUT 組:鎖冊現役那一版標「現役」· 前版標「前版」", any(v["lock_role"] == "現役" for v in lay.get("versions", []))
            and any(v["lock_role"] == "前版" for v in lay.get("versions", [])), [(v["version"], v["lock_role"]) for v in lay.get("versions", [])][:4])
        with tempfile.TemporaryDirectory() as tmp:
            pd = prep_v0102("VRN", write=True, out_dir=Path(tmp))
            wrote = (Path(tmp) / "ENGINE_PARAMS_VRN_latest.html").is_file()
        chk("⑦ prep 每張卡帶 ⑧⑨⑩;頁落地;燈數加總 = 支數",
            wrote and all("outputs" in c for c in pd["cards"]) and sum(pd["summary"]["lamps"].values()) == pd["summary"]["engines"],
            {k: pd["summary"][k] for k in ("engines", "lamps", "with_outputs", "uses_locked_tools", "unnumbered_tails")})
    except RuntimeError as e:
        chk("④–⑦ 全景鎖版不在 → 照實失敗(不冒充)", False, str(e))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 加速器橋 · 網路橋在 · 不碰 TA-Lib · 不代設同意閘",
        "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"environ\[[\"'](VIA_NET_CONSENT|VIA_SCRAPE_CONSENT)[\"']\]\s*=(?!=)", src))
    print(f"  [計] {ENGINE} 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if rc == 0 else 'rc=' + str(rc)} · 合計 {'PASS' if all(ok) and rc == 0 else 'FAIL'}")
    return 0 if all(ok) and rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
