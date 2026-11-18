#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-ENG023 · VRN_ToolBridge_v0100 v0100 · ENGINE =====
# AST 注入（只加註解，AST 不變）：類別 1 · 函式 12；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""
VRN_ToolBridge v0100 -- VRN-1 的工具橋：借出自己的工具、向別的系統借自己缺的工具（VRN-1 自己寫的；VRN-2 有它自己寫的一支，兩支只靠工具冊對話）。

Operator 2026-10-20: 「VRN-1 VRN-2 工具可相互取用 · 可驗證性高精準度還原後表格可改為資料庫形式 PIVOT ·
兩個系統元主體邏輯不變但各式可以找缺少的工具 · 獨立系統兩個 MAIN」.

  offer    ssot/VRN_ToolManifest_v0100.json（build 寫、check 驗 sha256）：
             table.pivot_db  engine/VRN_PivotDB_v0100.py · build_pivot_db（契約 VIA_PivotFacts/1：驗證過的事實表 → PIVOT 資料庫）
  borrow   VRN-2 的工具冊 <VIA 根>/VIA_Reports/vrn2/tools/VRN2_ToolManifest_v0100.json（VRN-2 啟動器寫的）：
             section.near    段落標題的讀法 —— VRN-1 沒有（MS 3661 第 10 頁：Growth(%) 底下的 Net profits 93.8 被 G21 證實成淨利）。
                             借來交給 G21（VRN_OutputVerify.section_pass）；判準 section_semantic 是 VRN-1 自己的。
             ocr.image       這台機器沒有 VRN-1 自己的 OCR 引擎時，借 VRN-2 的 OCR 隔離環境（G06 / P22 照實寫是誰讀的；OCR 的字照舊不進判讀）。
  rules    別的系統的檔只讀：不改、不複製、不寫它的夾；借之前逐檔核對對方工具冊的 sha256（不符 = 不借，照實寫）；
           用獨立的模組名載入、載入時不寫 __pycache__（不在別的系統的夾裡留檔）；找不到對方 = 只用自己的工具（WARN，不是 FAIL）。

用法：python VRN_ToolBridge_v0100.py manifest | check | peers | --selftest
"""

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

import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

VERSION = "VRN_ToolBridge v0100"
SYSTEM = "VRN-1"
SCHEMA = "VIA_ToolManifest/1"
HERE = Path(__file__).resolve().parent
VRN_ROOT = HERE.parent
REPO_ROOT = VRN_ROOT.parent.parent if VRN_ROOT.parent.name == "functional modules" else VRN_ROOT
MANIFEST = VRN_ROOT / "ssot" / "VRN_ToolManifest_v0100.json"
VRN2_VIA_WINDOWS = r"C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics"   # VRN-2 交接報告第 2 節的 VIA 根
VRN2_MANIFEST = ("VIA_Reports", "vrn2", "tools", "VRN2_ToolManifest_v0100.json")
OFFERS = (
    {"id": "table.pivot_db", "file": "engine/VRN_PivotDB_v0100.py", "entry": "build_pivot_db",
     "signature": "build_pivot_db(facts, out_dir, restored=(), title='', generated_by='') -> summary",
     "contract": "VIA_PivotFacts/1：facts 一格一列（欄位見 FACT_COLS）· 只收 VERIFIED / CORRECTED、有期間、有數值 · 同格不同值留空列衝突 · "
                 "印的位數不同的同一個數取最細的列精度合併 · 寫進呼叫端給的 out_dir（SQLite 一定有 · DuckDB 有才寫 · CSV · Parquet · HTML）",
     "needs": ["（標準庫）", "duckdb（可無）", "pandas + pyarrow（可無）"], "selftest": "--selftest"},
)
BORROWS = ("section.near", "ocr.image")


# [VRN-ID] VRN-ENG023-FNC001 · LOGIC
def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# [VRN-ID] VRN-ENG023-FNC002 · LOGIC
def _load(path: Path, name: str):
    """依路徑載入（獨立模組名 · 載過就沿用）· 載入期間不寫 __pycache__：別的系統的夾不留任何檔。"""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    keep = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    finally:
        sys.dont_write_bytecode = keep
    return module


# =====================================================================
# 1 . 借出：自己的工具冊（build 寫 · check 驗）
# =====================================================================
# [VRN-ID] VRN-ENG023-FNC003 · LOGIC
def manifest() -> Dict[str, Any]:
    """工具冊內容（相對路徑 · 不寫時間：同一份程式 → 同一本冊，git 不會每次 build 都多一筆變動）。"""
    offers = []
    for o in OFFERS:
        p = VRN_ROOT / o["file"]
        rel = (Path("functional modules") / "VRN" / o["file"]).as_posix() if REPO_ROOT != VRN_ROOT else o["file"]
        offers.append(dict(o, file=rel, kind="python", ready=p.is_file(), why="" if p.is_file() else "檔案不在",
                           files=[{"file": rel, "sha256": sha256(p) if p.is_file() else ""}]))
    return {"schema": SCHEMA, "system": SYSTEM, "main": "functional modules/VRN/VRN_Main_v0100.py", "bridge": VERSION,
            "root_rule": "相對路徑以工具冊所在的倉為根（工具冊往上三層：functional modules/VRN/ssot）",
            "rule": "借用端只讀：逐檔核對 sha256（不符 = 不借）· 不改 / 不複製 VRN-1 的檔 · 只寫借用端自己的輸出夾",
            "offers": offers, "borrows": [{"id": b, "from": "VRN-2", "manifest": "/".join(VRN2_MANIFEST)} for b in BORROWS]}


# [VRN-ID] VRN-ENG023-FNC004 · IO
def write_manifest(path: Path = MANIFEST) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(manifest(), ensure_ascii=False, indent=1) + "\n"
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(str(tmp), str(path))
    return path


# [VRN-ID] VRN-ENG023-FNC005 · VALIDATE
def check_manifest(path: Path = MANIFEST, base: Optional[Path] = None) -> List[str]:
    """問題清單（空 = 冊上每支工具的檔都在、sha256 都和冊相同）· base = 冊上相對路徑的根（預設：工具冊所在的倉）。"""
    path = Path(path)
    if not path.is_file():
        return ["工具冊不在：%s（跑 VRN_Main_v0100.py build 寫出）" % path.name]
    try:
        book = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as error:
        return ["工具冊讀不了：%s" % error]
    issues = []
    if book.get("schema") != SCHEMA:
        issues.append("工具冊格式不是 %s" % SCHEMA)
    want = {o["id"] for o in OFFERS}
    have = {o.get("id") for o in book.get("offers") or []}
    if want - have:
        issues.append("工具冊少了 %s" % "、".join(sorted(want - have)))
    if base is None:
        base = path.parents[len(("functional modules", "VRN", "ssot"))] if REPO_ROOT != VRN_ROOT else VRN_ROOT   # 冊在 <倉>/functional modules/VRN/ssot/
    for o in book.get("offers") or []:
        for f in o.get("files") or []:
            p = base / f["file"]
            if not p.is_file():
                issues.append("%s 的檔不在：%s" % (o.get("id"), f["file"]))
            elif sha256(p) != f.get("sha256"):
                issues.append("%s 的 sha256 和工具冊不同（%s）：檔改過沒重寫冊 → 跑 build" % (o.get("id"), f["file"]))
    return issues


# =====================================================================
# 2 . 借入：找 VRN-2 · 讀它的工具冊 · 逐檔核對 · 載入
# =====================================================================
# [VRN-ID] VRN-ENG023-CLS001 · CLASS
class BorrowError(RuntimeError):
    pass


# [VRN-ID] VRN-ENG023-FNC006 · LOGIC
def vrn2_candidates() -> List[Path]:
    """VRN-2 的 VIA 根候選（依序）：VIA_VRN2_ROOT · VRN-2 交接報告的位置 · 家目錄底下 · VRN-1 倉旁邊（同一層 / 上一層）。"""
    home = Path.home()
    c = [os.environ.get("VIA_VRN2_ROOT"), VRN2_VIA_WINDOWS,
         str(home / "OneDrive" / "Documents" / "movies-dataset" / "VeritasIntelligenceAnalytics"),
         str(home / "Documents" / "movies-dataset" / "VeritasIntelligenceAnalytics"), str(home / "movies-dataset" / "VeritasIntelligenceAnalytics")]
    for up in (REPO_ROOT.parent, REPO_ROOT.parent.parent):
        c.append(str(up / "movies-dataset" / "VeritasIntelligenceAnalytics"))
    out, seen = [], set()
    for x in c:
        if x and x not in seen:
            seen.add(x)
            out.append(Path(x))
    return out


# [VRN-ID] VRN-ENG023-FNC007 · LOGIC
def find_vrn2() -> Tuple[Optional[Path], Optional[Path], str]:
    """(VRN-2 的 VIA 根, 工具冊, 說明)· 找不到 → (None, None, 說明)。"""
    tried, here = [], None
    for cand in vrn2_candidates():
        mf = cand.joinpath(*VRN2_MANIFEST)
        if mf.is_file():
            return cand, mf, "VRN-2 工具冊 %s" % mf
        tried.append(str(cand))
        if here is None and (cand / "functional modules" / "VRN").is_dir():
            here = cand
    if here is not None:                                  # VRN-2 在，只是還沒寫工具冊（還沒跑過 v0131 以上的啟動器）→ 說清楚怎麼補
        return None, None, ("VRN-2 在 %s，但還沒有工具冊（%s）→ 先跑一次 VRN-2 一鍵 v0131 以上（啟動器 ② 會寫工具冊），再跑 VRN-1"
                            % (here, "/".join(VRN2_MANIFEST)))
    return None, None, "找不到 VRN-2 的工具冊（%s；試過 %s · 可設 VIA_VRN2_ROOT · VRN-2 啟動器 v0131 起會寫）" % ("/".join(VRN2_MANIFEST), " | ".join(tried[:4]))


# [VRN-ID] VRN-ENG023-FNC008 · IO
def read_peer_manifest(mf: Path) -> Dict[str, Any]:
    book = json.loads(Path(mf).read_text(encoding="utf-8"))
    if book.get("schema") != SCHEMA or not isinstance(book.get("offers"), list):
        raise BorrowError("工具冊格式不是 %s：%s" % (SCHEMA, mf))
    return book


# [VRN-ID] VRN-ENG023-FNC009 · LOGIC
def borrow(tool_id: str, mf: Optional[Path] = None, root: Optional[Path] = None) -> Tuple[Callable[..., Any], Dict[str, Any]]:
    """(函式, 紀錄)：VRN-2 工具冊裡 tool_id 那一支 · 冊上每個檔的 sha256 要相同 · 依路徑載入（獨立模組名）· 不符 / 不在 → BorrowError。"""
    if mf is None:
        root, mf, note = find_vrn2()
        if mf is None:
            raise BorrowError(note)
    mf = Path(mf)
    book = read_peer_manifest(mf)
    base = Path(book["root"]) if book.get("root") and Path(book["root"]).is_dir() else (Path(root) if root else mf.parents[len(VRN2_MANIFEST) - 1])
    tool = next((t for t in book["offers"] if t.get("id") == tool_id), None)
    if tool is None:
        raise BorrowError("%s 的工具冊沒有 %s" % (book.get("system", "?"), tool_id))
    if tool.get("ready") is False:
        raise BorrowError("%s 自己標「不能用」：%s" % (tool_id, tool.get("why", "")))
    for f in tool.get("files") or []:
        p = Path(f["file"]) if Path(f["file"]).is_absolute() else base / f["file"]
        if not p.is_file():
            raise BorrowError("%s 的檔不在：%s" % (tool_id, p))
        got = sha256(p)
        if got != f.get("sha256"):
            raise BorrowError("%s 的 sha256 和工具冊不同（冊 %s · 檔 %s）→ 不借 · VRN-2 的檔換過但工具冊沒重寫：再跑一次 VRN-2 一鍵（啟動器 ② 會重寫工具冊）"
                              % (f["file"], str(f.get("sha256"))[:12], got[:12]))
    src = Path(tool["file"]) if Path(tool["file"]).is_absolute() else base / tool["file"]
    module = _load(src, "vrn1_borrowed_%s_%s" % (re.sub(r"\W", "_", tool_id), sha256(src)[:10]))
    fn = getattr(module, tool.get("entry", ""), None)
    if not callable(fn):
        raise BorrowError("%s 沒有入口 %s" % (tool["file"], tool.get("entry")))
    return fn, {"id": tool_id, "from": book.get("system", ""), "file": str(src), "sha256": sha256(src), "entry": tool["entry"],
                "contract": tool.get("contract", ""), "reader": tool.get("reader", ""), "manifest": str(mf)}


# [VRN-ID] VRN-ENG023-FNC010 · LOGIC
def borrow_all(wanted: Sequence[str] = BORROWS) -> Dict[str, Any]:
    """G23：找 VRN-2 → 每支要借的工具一列（BORROWED / REFUSED / ABSENT）· 借到的函式放在 tools[id]。"""
    root, mf, note = find_vrn2()
    out: Dict[str, Any] = {"peer": "VRN-2", "root": str(root or ""), "manifest": str(mf or ""), "note": note, "tools": {}, "rows": []}
    if mf is None:
        out["rows"] = [{"id": t, "state": "ABSENT", "detail": note} for t in wanted]
        return out
    for t in wanted:
        try:
            fn, rec = borrow(t, mf, root)
        except Exception as error:  # noqa: BLE001 - 借不到 = 只用自己的工具，照實寫
            out["rows"].append({"id": t, "state": "REFUSED", "detail": "%s: %s" % (error.__class__.__name__, error)})
            continue
        out["tools"][t] = fn
        out["rows"].append({"id": t, "state": "BORROWED", "detail": "%s · %s · sha256 %s 與工具冊相同" % (rec["from"], Path(rec["file"]).name, rec["sha256"][:12]),
                            "record": rec})
    return out


# =====================================================================
# 3 . 自測（不需要 VRN-2：假的工具冊 + 假的工具）
# =====================================================================
# [VRN-ID] VRN-ENG023-FNC011 · ENTRY
def selftest(verbose: bool = True) -> int:
    checks: List[Tuple[str, bool]] = []
    book = manifest()
    checks.append(("自己的工具冊：%s · 借出 table.pivot_db（檔在 · sha256 64 碼）" % SCHEMA,
                   book["schema"] == SCHEMA and [o["id"] for o in book["offers"]] == ["table.pivot_db"]
                   and all(len(f["sha256"]) == 64 for o in book["offers"] for f in o["files"])))
    checks.append(("自己的工具冊：同一份程式 → 同一本冊（沒有時間戳）", json.dumps(manifest(), sort_keys=True) == json.dumps(book, sort_keys=True)))
    with tempfile.TemporaryDirectory(prefix="vrn_toolbridge_") as td:
        t = Path(td)
        base = REPO_ROOT if REPO_ROOT != VRN_ROOT else VRN_ROOT
        (t / "good.json").write_text(json.dumps(book), encoding="utf-8")
        bad = dict(book, offers=[dict(o, files=[dict(f, sha256="0" * 64) for f in o["files"]]) for o in book["offers"]])
        (t / "bad.json").write_text(json.dumps(bad), encoding="utf-8")
        checks.append(("check：冊不在 → 說清楚怎麼補", any("不在" in i for i in check_manifest(t / "none.json"))))
        checks.append(("check：剛寫的冊 → 沒有問題；冊上 sha256 和檔不同 → 點名要跑 build",
                       check_manifest(t / "good.json", base) == [] and any("build" in i for i in check_manifest(t / "bad.json", base))))
        via = t / "VIA"
        tool = via / "functional modules" / "VRN" / "fake_section.py"
        tool.parent.mkdir(parents=True)
        tool.write_text("def near(pdf, page, item, value=None):\n    return {'section': 'Growth (%)', 'found': True, 'how': 'fake', 'reader': 'fake'}\n", encoding="utf-8")
        mf = via.joinpath(*VRN2_MANIFEST)
        mf.parent.mkdir(parents=True)
        rel = "functional modules/VRN/fake_section.py"
        peer = {"schema": SCHEMA, "system": "VRN-2", "root": str(via),
                "offers": [{"id": "section.near", "file": rel, "entry": "near", "ready": True, "files": [{"file": rel, "sha256": sha256(tool)}]},
                           {"id": "ocr.image", "file": rel, "entry": "near", "ready": False, "why": "隔離環境不在", "files": []}]}
        mf.write_text(json.dumps(peer), encoding="utf-8")
        keep = os.environ.get("VIA_VRN2_ROOT")
        os.environ["VIA_VRN2_ROOT"] = str(via)
        try:
            got = borrow_all()
            st = {r["id"]: r["state"] for r in got["rows"]}
            checks.append(("找 VRN-2：VIA_VRN2_ROOT 優先 → 讀工具冊", got["manifest"] == str(mf)))
            checks.append(("借：sha256 相同 → BORROWED · 函式可呼叫", st.get("section.near") == "BORROWED"
                           and got["tools"]["section.near"]("x.pdf", 1, "EPS")["section"] == "Growth (%)"))
            checks.append(("借：對方自己標「不能用」→ REFUSED（附對方的理由）", st.get("ocr.image") == "REFUSED"
                           and "隔離環境不在" in next(r["detail"] for r in got["rows"] if r["id"] == "ocr.image")))
            checks.append(("借：載入時不在對方的夾留 __pycache__", not (tool.parent / "__pycache__").exists()))
            tool.write_text(tool.read_text(encoding="utf-8") + "# changed\n", encoding="utf-8")
            again = borrow_all(("section.near",))
            checks.append(("借：對方的檔改過（sha256 和冊不同）→ REFUSED、不載入", again["rows"][0]["state"] == "REFUSED" and "sha256" in again["rows"][0]["detail"]))
            bare = t / "VIA_bare"
            (bare / "functional modules" / "VRN").mkdir(parents=True)
            os.environ["VIA_VRN2_ROOT"] = str(bare)
            nb = borrow_all(("section.near",)) if not any(c.joinpath(*VRN2_MANIFEST).is_file() for c in vrn2_candidates()[1:]) else None
            checks.append(("VRN-2 在、還沒有工具冊 → ABSENT 並說「先跑一次 VRN-2 一鍵 v0131 以上」",
                           nb is None or (nb["rows"][0]["state"] == "ABSENT" and "先跑一次 VRN-2 一鍵" in nb["note"] and str(bare) in nb["note"])))
            os.environ["VIA_VRN2_ROOT"] = str(t / "nowhere")
            gone = borrow_all(("section.near",)) if not any(c.joinpath(*VRN2_MANIFEST).is_file() for c in vrn2_candidates()[1:]) else None
            checks.append(("找不到 VRN-2 → ABSENT（只用自己的工具 · 不是錯）", gone is None or gone["rows"][0]["state"] == "ABSENT"))
        finally:
            if keep is None:
                os.environ.pop("VIA_VRN2_ROOT", None)
            else:
                os.environ["VIA_VRN2_ROOT"] = keep
    for name, ok in checks:
        if verbose:
            print("  [%s] %s" % ("PASS" if ok else "FAIL", name))
    passed = sum(1 for _n, ok in checks if ok)
    print("[計] %s 自測 %d/%d · %s" % (VERSION, passed, len(checks), "PASS" if passed == len(checks) else "FAIL"))
    return 0 if passed == len(checks) else 1


# [VRN-ID] VRN-ENG023-FNC012 · ENTRY
def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["--selftest"]:
        return selftest()
    if args[:1] == ["manifest"]:
        print("[計] VRN-1 借出工具冊 %s" % write_manifest())
        return 0
    if args[:1] == ["check"]:
        issues = check_manifest()
        print("[計] VRN-1 工具冊 %s" % ("相符" if not issues else "；".join(issues)))
        return 1 if issues else 0
    if args[:1] == ["peers"]:
        got = borrow_all()
        print("[計] %s" % got["note"])
        for r in got["rows"]:
            print("  [%s] %s · %s" % (r["state"], r["id"], r["detail"]))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
