#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SUP_MDL866 v0109 — 薄尾(v0108 以前一字不動):桌機 NLP 收件整合成四個動詞(只掛收容件,不改它們)

操作員 2026-11-22:「用 VCGC 的全景式檢視分析功能 … 去見識上述功能是否我們現有的引擎有缺漏,將它們整合到現有指令」「完全授權整合」。
先量(VCGC 省 Token 工具 read,21 夾 · 321 行):via_nlp_engine v1.5 / v1.8 / v1.9 · MarkdownEditingEngine · SuperHtmlParser ·
VCGC_LAYOUT_ENGINE · Celeritas · Batch347 · spec_extractor / triengine_hub 倉內都已有(多半更新);倉內**沒有**的四件收進
functional modules/VRN/references/intake/NLP_Desktop_b20261122(只收 .py / .ps1,不收文件與資料),本版掛成動詞:

  reconstruct <檔…> [--out 夾] [--lexicon 詞庫.json]
      v5 內容重建(VIA-ENG-004 5.0.0;疊在 v3 via_content_reconstructor 上):話題段落 · 參數正規化 · 相似指令合併 ·
      增強摘要 · 心智圖投影 · 可重用提示。詞庫(synonyms · stopwords · factors · regex)沒給也找不到 → 空詞庫照跑、標黃
      (只有結構重建,沒有詞庫加權),不冒充。
  unified <檔> [--out 夾] [--quality balanced]
      v8 合併版(v7 → via_nlp_engine VIAEngine + 語法樹清點 + 正規化投影 + 品質閘 + Mermaid 心智圖)。v7 原本讀它自帶的
      vendor/VIA_NLP_Application_System_v1.8.0(沒收進來,是倉內收容件的重複);本版改指倉內收容件同一版的 src 與 config,
      執行期夾(VIAEngine data_dir)改到輸出夾底下 —— 不寫進收容夾。
  scan-folder <夾> [--out 夾] [--max-files N]
      整夾內容脈絡掃描:格式 · 角色 · 匯入 · docx / 壓縮檔清單 → 矩陣(csv · md · html)+ Mermaid 工作流圖 + folder_scan.json。
      只讀;跟 VCGC 省 Token 工具的 read / pack 互補(那兩支只看程式結構,這支連文件內容角色一起看,全在本機)。
  semantic --action A (--text T | --path P | --request 請求.json) [--runtime 夾]
      VUSIPE v0100(通用語意外掛):analyze · keywords · entities · relations · summarize · actions · embed · similarity ·
      classify · retrieve · knowledge_upsert / search · feedback · train / evaluate / evolve。純 CPU、離線、只讀來源;
      知識庫(SQLite)與模型候選寫在 --runtime(預設 VIA_Reports/nlp/vusipe_runtime,不入倉)。
  intake-status
      四件各自的來源檔 · sha256 · 能不能載 · 沒整合的件與理由(JSON)。

沒整合(照實列在 intake-status):
  · v7 / v8 的 HTTP 控制台(via_nlp_control_api*.py):預設綁 0.0.0.0(對外開埠)、依賴 `cgi`(Python 3.13 已移除,桌機 C:\\Python313
    載不起來);功能 = 上面四個動詞 + 網頁殼,VIA 已有自己的 HTML U/I。
  · 各包的 Invoke-*.ps1 啟動器與 tests:由本檔動詞取代;收容件原樣留存供對照。
其餘動詞(--brief · pdf · text · l1-* …)照 v0108 → v0107 → v0106。只收 VCGC 呼叫;零網路;不碰 TA-Lib。
工具鎖冊 nlp 的釘選不由本檔改(換版經 VCGC tools activate)。
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
import hashlib
import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
_STEM = "SUP_MDL866_VIAUnifiedNLPOrchestrator"
ENGINE = Path(__file__).stem
TAG = "SUP_MDL866 v0109"
INTAKE = VIA / "functional modules" / "VRN" / "references" / "intake"
DESK = INTAKE / "NLP_Desktop_b20261122"
V5_ROOT = DESK / "VIA_NLP_v5_Delivery" / "VIA_NLP_v5_Delivery"                      # 有 v3/(v5 要 import 它)
V8_ROOT = DESK / "VIA_Consolidated_NLP_v8_Delivery" / "VIA_Consolidated_NLP_v8_Delivery"
VU_ROOT = DESK / "Veritas_Universal_Semantic_Intelligence_Plugin_Engine_v0100_FINAL" / "Veritas_Universal_Semantic_Intelligence_Plugin_Engine_v0100"
VENDOR = INTAKE / "VIA_NLP_Application_System_v1.8.0"                                 # v7 釘的那一版(倉內收容件)
SOURCES = {
    "reconstruct_v5": V8_ROOT / "v5" / "via_nlp_reconstruction_v5.py",                 # v7 / v8 兩包同一份(位元相同),比 v5 包新(多心智圖 · 可重用提示)
    "reconstruct_v3": V5_ROOT / "v3" / "via_content_reconstructor.py",
    "unified_v7": V8_ROOT / "nlp_v7_upgrade" / "unified" / "via_nlp_unified_v7.py",
    "unified_v8": V8_ROOT / "v8" / "via_consolidated_nlp_v8.py",
    "scan_folder": V8_ROOT / "via_folder_context_scanner.py",
    "semantic_vusipe": VU_ROOT / "VUSIPE.py",
    "vendor_src": VENDOR / "src" / "via_nlp_engine" / "__init__.py",
    "vendor_config": VENDOR / "config" / "default.json",
}
NOT_INTEGRATED = [
    {"file": "via_nlp_control_api.py / via_nlp_control_api_v8.py", "why": "HTTP 控制台:預設綁 0.0.0.0(對外開埠);import cgi(Python 3.13 已移除,桌機 3.13 載不起來);功能 = 四個動詞 + 網頁殼,VIA 已有自己的 HTML U/I"},
    {"file": "Invoke-*.ps1(v5 · v7 · v8 · VUSIPE)", "why": "啟動器;由本檔動詞取代(PS 只進環境 + 呼叫 Python 入口)"},
    {"file": "tests/ · validate_* · benchmark_* · promote_v5_registry.py · v5_audit_new_attachments.py", "why": "收件包自己的測試與登記工具;本檔自測在暫存夾覆蓋四個動詞"},
]
# v5 直接取用(lexicon["regex"][…] · lexicon["version"])的鍵:詞庫缺時用這組最小通用樣式(中英),不含任何市場詞彙
FALLBACK_REGEX = {
    "question": r"[?？]|\b(?:what|why|how|when|which|who|whether|can|could|should)\b|嗎|呢|是否|為什麼|如何|怎麼",
    "command": r"^\s*(?:run|install|execute|python|pwsh|git|pip)\b|^\s*(?:請|執行|啟動|跑)",
    "constraint": r"\b(?:must|never|only|always|do not|don't|shall not)\b|必須|不得|不要|只能|一律|禁止",
    "verification": r"\b(?:test|verify|validate|check|assert|selftest)\b|驗證|測試|自測|檢查|確認",
}
EMPTY_LEXICON = {"version": "via-fallback-0", "synonyms": {}, "stopwords": [], "factors": {}, "regex": dict(FALLBACK_REGEX)}


def _complete_lexicon(lex: dict) -> tuple:
    """補齊 v5 直接取用的鍵;回 (詞庫, 補了哪些鍵)。"""
    lex = dict(lex or {})
    filled = []
    if "version" not in lex:
        lex["version"] = "via-fallback-0"
        filled.append("version")
    rx = dict(lex.get("regex") or {})
    for k, v in FALLBACK_REGEX.items():
        if k not in rx:
            rx[k] = v
            filled.append("regex." + k)
    lex["regex"] = rx
    for k, v in (("synonyms", {}), ("stopwords", []), ("factors", {})):
        lex.setdefault(k, v)
    return lex, filled


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
PRIOR = _load(PRIOR_PATH, _STEM + "_prior_for_" + ENGINE)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _sha(p: Path) -> str | None:
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except OSError:
        return None


def _out_dir(verb: str, out: str | None) -> Path:
    d = Path(out) if out else VIA / "VIA_Reports" / "nlp" / verb / time.strftime("%Y%m%d_%H%M%S")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _ensure_path(p: Path) -> None:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


_CACHE: dict = {}


def _mod(key: str):
    if key not in _CACHE:
        if key == "reconstruct_v5":
            _ensure_path(V5_ROOT)                                       # v5 的 `from v3.via_content_reconstructor import …` 在這裡找到
            _mod("reconstruct_v3")
        if key in ("unified_v7", "unified_v8"):
            _ensure_path(VENDOR / "src")                                # via_nlp_engine = 倉內收容件 v1.8.0(v7 釘的那一版)
        if key == "unified_v8":
            _mod("unified_v7")                                          # 先以 v8 匯入的名字載好 v7,它的 sys.path 插入就無所謂了
        name = {"reconstruct_v3": "v3.via_content_reconstructor", "unified_v7": "via_nlp_unified_v7"}.get(key, "_nlp_intake_" + key)
        if key == "reconstruct_v3":
            import types
            sys.modules.setdefault("v3", types.ModuleType("v3")).__path__ = [str(V5_ROOT / "v3")]
        _CACHE[key] = _load(SOURCES[key], name)
    return _CACHE[key]


# ---------------------------------------------------------------- 四個動詞
def reconstruct(paths: list, out: str | None = None, lexicon: str | None = None) -> dict:
    lex_path = Path(lexicon) if lexicon else next((p for p in (V5_ROOT / "VIA_NLP_SSOT_Lexicon_v5.json", V8_ROOT / "VIA_NLP_SSOT_Lexicon_v5.json") if p.is_file()), None)
    v5 = _mod("reconstruct_v5")
    if lex_path and lex_path.is_file():
        lex, filled = _complete_lexicon(v5.load_lexicon(lex_path))
        lamp = "GREEN" if not filled else "YELLOW"
        why = f"詞庫 {lex_path.name}" + (f" · 缺鍵用內建樣式補:{' · '.join(filled)}" if filled else "")
    else:
        lex, lamp, why = _complete_lexicon(EMPTY_LEXICON)[0], "YELLOW", "詞庫 ABSENT(VIA_NLP_SSOT_Lexicon_v5.json 沒收進來,也沒給 --lexicon)→ 內建最小樣式照跑:只有結構重建,沒有同義字 / 因子加權"
    bundle = v5.reconstruct_v5_paths([str(p) for p in paths], lex)
    d = _out_dir("reconstruct", out)
    written = v5.write_v5_outputs(bundle, d)
    return {"tool": TAG, "verb": "reconstruct", "lamp": lamp, "why": why, "engine": f"{v5.ENGINE_ID} {v5.ENGINE_VERSION}",
            "inputs": [str(p) for p in paths], "out": str(d), "written": str(written),
            "records": len(bundle.get("records", bundle.get("files", [])) or [])}


def unified(path: str, out: str | None = None, quality: str = "balanced") -> dict:
    v7 = _mod("unified_v7")
    d = _out_dir("unified", out)
    v7.VENDOR_CONFIG = SOURCES["vendor_config"]                         # 原本指 vendor/ 底下(沒收進來,是倉內收容件的重複)
    v7.RUNTIME_DIR = d / "_engine_runtime"                                # 原本是收容夾底下 app/v7_runtime → 不寫收容夾
    v8 = _mod("unified_v8")
    try:
        result = v8.process_path_v8(path, quality=quality)
        files = []
        for name, payload in v8.artifact_payloads_v8(result).items():
            p = d / name
            p.write_text(payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
            files.append(name)
    finally:
        try:
            v7.close_engine()
        except Exception:  # noqa: BLE001 — 關引擎失敗不蓋過主結果
            pass
    q = (result.get("projection") or {}).get("quality") or result.get("quality") or {}   # v8 放在 projection.quality(PR 723 Codex P2)
    lamp, why = _unified_lamp(q)
    return {"tool": TAG, "verb": "unified", "lamp": lamp, "why": why,
            "engine": f"v8 → {v7.ENGINE_ID} {v7.ENGINE_VERSION} · via_nlp_engine {VENDOR.name}", "input": str(path),
            "out": str(d), "files": sorted(files), "quality": q}


def _unified_lamp(q: dict) -> tuple:
    """從 v8 的品質報告逐項判燈;報告缺 = 黃(不把「沒有」當成過)。review_required 是 v8 的常數 True,不拿來判。"""
    if not q:
        return "YELLOW", ["品質報告缺(projection.quality 不在)"]
    red, yel = [], []
    for k in ("v8_source_mutated", "source_text_mutated", "automatic_code_merge", "command_execution_authorized", "ast_execution_authorized"):
        if q.get(k) is True:
            red.append(f"{k}=True")
    ast = q.get("ast_parse_status")
    if ast not in (None, "PASS", "not_applicable"):
        yel.append(f"ast_parse_status={ast}")
    for k in ("body_summary_evidence_integrity", "full_summary_evidence_integrity"):
        if k in q and q[k] is not True:
            yel.append(f"{k}={q[k]}")
    if q.get("mind_map_graph_endpoints_valid") is False:
        yel.append("mind_map_graph_endpoints_valid=False")
    if q.get("knowledge_conflicts"):
        yel.append(f"knowledge_conflicts={q['knowledge_conflicts']}")
    return ("RED", red + yel) if red else (("YELLOW", yel) if yel else ("GREEN", []))


def scan_folder(root: str, out: str | None = None, max_files: int = 5000) -> dict:
    sc = _mod("scan_folder")
    d = _out_dir("scan_folder", out)
    r = sc.scan_folder(root, d, max_files=max_files)
    scanned = (r.get("limits") or {}).get("scanned_files", len(r.get("rows") or []))
    truncated = scanned >= max_files and _count_files(sc, root, max_files + 1) > max_files   # 掃描器到上限就停、不報錯(PR 723 Codex P2)
    why = []
    if truncated:
        why.append(f"只掃了前 {max_files} 檔,資料夾還有更多(加大 --max-files 再跑)")
    if r.get("errors"):
        why.append(f"讀檔錯誤 {len(r['errors'])} 筆")
    return {"tool": TAG, "verb": "scan-folder", "lamp": "YELLOW" if why else "GREEN", "why": why, "truncated": truncated,
            "max_files": max_files, "scanned_files": scanned, "root": str(root), "out": str(d),
            "summary": r.get("summary"), "errors": r.get("errors"), "files": sorted(p.name for p in d.iterdir() if p.is_file())}


def _count_files(sc, root, stop: int) -> int:
    """照掃描器同一套排除規則數檔,數到 stop 就停(只判「有沒有超過上限」,不整樹數完)。"""
    n = 0
    for _cur, dirs, files in os.walk(Path(root).expanduser().resolve()):
        dirs[:] = sorted(x for x in dirs if x not in sc.EXCLUDED_DIRS and not x.startswith("."))
        n += len(files)
        if n >= stop:
            return n
    return n


def semantic(request: dict, runtime: str | None = None) -> dict:
    vu = _mod("semantic_vusipe")
    rt = Path(runtime) if runtime else VIA / "VIA_Reports" / "nlp" / "vusipe_runtime"
    rt.mkdir(parents=True, exist_ok=True)
    return json.loads(vu.invoke_json(json.dumps(request, ensure_ascii=False), rt))


def intake_status() -> dict:
    rows = []
    for k, p in SOURCES.items():
        rows.append({"part": k, "file": str(Path(p).relative_to(VIA)), "present": Path(p).is_file(), "sha256": (_sha(p) or "")[:16]})
    lex = [p for p in (V5_ROOT / "VIA_NLP_SSOT_Lexicon_v5.json", V8_ROOT / "VIA_NLP_SSOT_Lexicon_v5.json") if p.is_file()]
    missing = [r["part"] for r in rows if not r["present"]]
    return {"tool": TAG, "lamp": "RED" if missing else ("GREEN" if lex else "YELLOW"), "sources": rows, "missing": missing,
            "lexicon": str(lex[0].relative_to(VIA)) if lex else "ABSENT(reconstruct 用空詞庫照跑)",
            "verbs": ["reconstruct", "unified", "scan-folder", "semantic", "intake-status"], "not_integrated": NOT_INTEGRATED}


# ---------------------------------------------------------------- 入口
def _print(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=1, default=str))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[DENY] only VCGC entry")
        return 2
    if args == ["--selftest"]:
        return selftest()
    verb = args[0] if args else ""
    if verb not in ("reconstruct", "unified", "scan-folder", "semantic", "intake-status"):
        return PRIOR.main(args)
    ap = argparse.ArgumentParser(prog=f"{ENGINE} {verb}")
    if verb == "reconstruct":
        ap.add_argument("paths", nargs="+"); ap.add_argument("--out"); ap.add_argument("--lexicon")
        o = ap.parse_args(args[1:]); r = reconstruct(o.paths, o.out, o.lexicon)
    elif verb == "unified":
        ap.add_argument("path"); ap.add_argument("--out"); ap.add_argument("--quality", default="balanced")
        o = ap.parse_args(args[1:]); r = unified(o.path, o.out, o.quality)
    elif verb == "scan-folder":
        ap.add_argument("root"); ap.add_argument("--out"); ap.add_argument("--max-files", type=int, default=5000)
        o = ap.parse_args(args[1:]); r = scan_folder(o.root, o.out, o.max_files)
    elif verb == "semantic":
        ap.add_argument("--action", default="analyze"); g = ap.add_mutually_exclusive_group(required=True)
        g.add_argument("--text"); g.add_argument("--path"); g.add_argument("--request"); ap.add_argument("--runtime")
        o = ap.parse_args(args[1:])
        if o.request:
            req = json.loads(Path(o.request).read_text(encoding="utf-8"))
        else:
            req = {"action": o.action, "payload": {"text": o.text} if o.text is not None else {"path": o.path}}
        r = semantic(req, o.runtime)
        _print(r)
        return 0 if r.get("gate") in ("PASS", None) else (2 if r.get("gate") == "HOLD" else 1)
    else:
        r = intake_status()
    _print(r)
    return {"GREEN": 0, "YELLOW": 2}.get(r.get("lamp"), 1)


def selftest() -> int:
    import contextlib
    import io
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc0 = PRIOR.selftest()
    print(f"=== {TAG} · 薄尾自測(桌機 NLP 收件四動詞;暫存夾 · 零網路)===")
    chk("⓪ 直接前版 v0108 自測過", rc0 == 0, buf.getvalue()[-300:])
    st = intake_status()
    chk("① 四件來源 + vendor src / config 都在倉內收容夾", not st["missing"], st["missing"])

    def snapshot():
        return sorted(str(p.relative_to(INTAKE)) for p in INTAKE.rglob("*") if p.is_file())
    before = snapshot()
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        src = t / "in"
        src.mkdir()
        note = src / "note.md"
        note.write_text("# 會議紀錄\n講者 A:我們決定把目標價調到 1200 元。\n講者 B:同意,threshold=0.62 照舊。\n"
                        "```python\ndef f(x):\n    return x + 1\n```\n", encoding="utf-8")
        (src / "tool.py").write_text("import json\n\ndef run(path):\n    return json.loads(path)\n", encoding="utf-8")
        r = reconstruct([note], str(t / "rec"))
        chk("② reconstruct:v5 跑完有輸出;詞庫缺 → 黃燈照實標 ABSENT(不冒充綠)", (t / "rec").is_dir() and any((t / "rec").rglob("*"))
            and r["lamp"] == "YELLOW" and "ABSENT" in r["why"], r)
        lex = t / "lex.json"
        full = {"version": "t1", "synonyms": {"threshold": ["閾值", "門檻"]}, "stopwords": [], "factors": {"price": ["目標價"]}, "regex": dict(FALLBACK_REGEX)}
        lex.write_text(json.dumps(full, ensure_ascii=False), encoding="utf-8")
        r2 = reconstruct([note], str(t / "rec2"), str(lex))
        chk("③ reconstruct --lexicon:完整詞庫 → 綠", r2["lamp"] == "GREEN" and "lex.json" in r2["why"], r2)
        lex.write_text(json.dumps({"synonyms": {}}, ensure_ascii=False), encoding="utf-8")
        r2b = reconstruct([note], str(t / "rec3"), str(lex))
        chk("③b 詞庫缺必填鍵 → 用內建樣式補、照實黃並點名補了哪些(v5 原本會 KeyError 崩)", r2b["lamp"] == "YELLOW" and "regex.question" in r2b["why"], r2b)
        r3 = unified(str(note), str(t / "uni"))
        chk("④ unified:v8 → v7 → via_nlp_engine(倉內 v1.8.0)跑完,寫出 v8_unified.json 與 Mermaid 心智圖", "v8_unified.json" in r3["files"]
            and "v8_mind_map.mmd" in r3["files"] and (t / "uni" / "v8_mind_map.mmd").read_text(encoding="utf-8").strip(), r3.get("files"))
        chk("⑤ unified 的引擎執行期夾在輸出夾底下(不寫收容夾)", Path(_mod("unified_v7").RUNTIME_DIR).parent == t / "uni"
            and Path(_mod("unified_v7").VENDOR_CONFIG) == SOURCES["vendor_config"])
        chk("④b unified 的燈讀 v8 真正的品質報告(projection.quality);報告非空、乾淨輸入 → 綠", r3["quality"] and "ast_parse_status" in r3["quality"]
            and r3["lamp"] == "GREEN", (r3["lamp"], r3.get("why")))
        bad = src / "bad.py"
        bad.write_text("def broken(:\n    return\n", encoding="utf-8")
        r3b = unified(str(bad), str(t / "uni_bad"))
        chk("④c PR 723 Codex P2:語法壞的 Python → ast_parse_status=PASS_WITH_REVIEW → 黃(不再回綠)", r3b["lamp"] == "YELLOW"
            and any("PASS_WITH_REVIEW" in x for x in r3b["why"]), (r3b["lamp"], r3b.get("why")))
        chk("④d 品質報告缺 → 黃;來源被改 → 紅", _unified_lamp({})[0] == "YELLOW" and _unified_lamp({"v8_source_mutated": True})[0] == "RED")
        bad.unlink()
        r4 = scan_folder(str(src), str(t / "scan"))
        chk("⑥ scan-folder:矩陣 csv / md / html + 工作流 mmd + folder_scan.json", {"VIA_Module_Matrix.csv", "VIA_Module_Matrix.md", "VIA_Module_Matrix.html",
            "VIA_Folder_Workflow_Chart.mmd", "folder_scan.json"} <= set(r4["files"]), r4["files"])
        r4b = scan_folder(str(src), str(t / "scan_cap"), max_files=1)
        chk("⑥b PR 723 Codex P2:兩檔的夾 --max-files 1 → 黃 · truncated · 點名只掃了前 1 檔", r4b["lamp"] == "YELLOW" and r4b["truncated"] is True
            and r4b["scanned_files"] == 1 and any("前 1 檔" in x for x in r4b["why"]), {k: r4b[k] for k in ("lamp", "why", "truncated", "scanned_files")})
        chk("⑥c 剛好掃完(檔數 = 上限)→ 不算截斷", scan_folder(str(src), str(t / "scan_eq"), max_files=2)["truncated"] is False
            and r4["truncated"] is False and r4["lamp"] == "GREEN")
        r5 = semantic({"action": "analyze", "payload": {"text": "台積電宣布擴產,董事會同意資本支出。TSMC will expand capacity."}}, str(t / "vu"))
        chk("⑦ semantic analyze:VUSIPE gate PASS · 知識庫寫在 --runtime", r5.get("gate") == "PASS" and any((t / "vu").rglob("*")), str(r5)[:200])
        r6 = semantic({"action": "capabilities", "payload": {}}, str(t / "vu"))
        chk("⑧ semantic capabilities:離線 · 只讀來源 · 純 CPU", r6.get("offline") is True and r6.get("source_policy") == "READ_ONLY" and r6.get("cpu_only") is True)
        r7 = semantic({"action": "nope", "payload": {}}, str(t / "vu"))
        chk("⑨ semantic 不支援的動作 → FAIL(不硬做)", r7.get("gate") == "FAIL")
        keep_env = os.environ.get("VIA_FROM_VCGC")
        os.environ.pop("VIA_FROM_VCGC", None)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                deny = main(["intake-status"])
        finally:
            if keep_env is not None:
                os.environ["VIA_FROM_VCGC"] = keep_env
        chk("⑩ 只收 VCGC 呼叫(沒旗標 → DENY rc 2)", deny == 2)
    chk("⑪ 收容夾一個檔都沒多、沒少(收容件只讀)", snapshot() == before, sorted(set(snapshot()) ^ set(before))[:5])
    chk("⑫ 沒整合的件照實列理由(HTTP 控制台:0.0.0.0 · cgi)", any("0.0.0.0" in x["why"] and "cgi" in x["why"] for x in st["not_integrated"]))
    src_text = Path(__file__).read_text(encoding="utf-8")
    body = src_text.split("def selftest", 1)[0]
    chk("⑬ 加速器橋在 · 不碰 TA-Lib · 本檔不起 HTTP 服務", "[VIA:ACCEL-BRIDGE:v0100]" in src_text and "talib" not in body.lower()
        and "serve_forever" not in body and "HTTPServer" not in body)
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑭ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), f"{len(pub)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
