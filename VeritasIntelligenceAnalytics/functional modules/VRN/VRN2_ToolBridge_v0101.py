#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN2_ToolBridge_v0101 — VRN-2 的工具橋(VRN-2 自己的 · 啟動器 v0132 內嵌、落在 VRN-2 程式夾 · VRN-1 另有它自己寫的一支)。
v0101(2026-10-20 · 操作員「一路實測修復到底 … FACILITATE … 授權全自動完成」)= v0100 + 找不到對方工具冊時說清楚下一步:
  VRN-1 的倉在、但那一版沒有工具冊(VRN-1 第十三輪起才有)→ 印出 cd / git fetch / git switch 的指令;
  VRN-1 的檔換過、工具冊沒重寫(sha256 不符)→ 印出在 VRN-1 倉重寫工具冊的指令(VRN_Main_v0100.py build)。
  只改提示字,借用規則(逐檔核對 sha256 · 只讀對方的檔 · 借不到只用自己的)與 v0100 相同;v0100 照舊留在原處(只增不改)。

操作員 2026-10-20:「VRN-1 VRN-2 工具可相互取用 · 可驗證性高精準度還原後表格可改為資料庫形式 PIVOT ·
兩個系統元主體邏輯不變但各式可以找缺少的工具 · 獨立系統兩個 MAIN」。

借出(VRN-2 → 別的系統)· 工具冊 <VIA 根>\\VIA_Reports\\vrn2\\tools\\VRN2_ToolManifest_v0100.json(每支:檔 · sha256 · 入口 · 契約 · 能不能用):
  section.near    section_near(pdf, page, item, value=None) → {"section", "found", "how", "rows", "reader"}
                  科目那一列上方、同一個科目欄最近的段落標題 —— VRN-2 SystemManager 自己的第三讀法(pdfplumber 字詞框 _g3_page)
                  + v0239 修 SECTION 用的同一支 _sec_near(到本欄的期間表頭為止 · 公式項不算)· 只餵科目欄起點以右的字(並排表左邊那張不混進來)·
                  有給值 → 只用有這個值的那一列(值不在科目那一列 = 轉置表 / 欄頭在上 → 不定)· 仍不一致 → 不回標題(found False)
  ocr.image       ocr_read(path) → {"engine", "lines", "text", "chars", "source": "OCR", "lossy_cjk": True, "lang", "error"}
                  VRN-2 的 OCR 隔離環境(envs\\vrn2_ocr · rapidocr)跑 VRN2_OCRBridge(借用端主環境不用裝 OCR)· PDF 先用 pypdfium2 轉圖
借入(別的系統 → VRN-2)· VRN-1 的工具冊 <VRN-1 倉>\\functional modules\\VRN\\ssot\\VRN_ToolManifest_v0100.json:
  table.pivot_db  VRN-1 VRN_PivotDB.build_pivot_db(契約 VIA_PivotFacts/1):驗證過的年度數據 → 資料庫形式 PIVOT
                  pivot_vrn2(v2):VRN-2 年度數據冊 + ⑪ 獨立驗證判決(冊指紋相同才用)→ 事實表 → <VIA_Reports\\vrn2>\\pivot\\
規則:別的系統的檔只讀(不改 · 不複製 · 不寫它的夾);借之前逐檔核對對方工具冊的 sha256(不符 = 不借 · 照實說);
      用獨立的模組名載入;VRN-2 的主體(SystemManager · ENG397 · 驗證器)一行不改,只多這一支。

用法:python VRN2_ToolBridge_v0101.py manifest [<VIA 根>]          寫借出工具冊
      python VRN2_ToolBridge_v0101.py peers                       找 VRN-1 · 讀它的工具冊 · 逐檔核對 sha256
      python VRN2_ToolBridge_v0101.py pivot [<VIA_Reports\\vrn2>]  借 VRN-1 PIVOT → <vrn2>\\pivot
      python VRN2_ToolBridge_v0101.py section <pdf> <頁> <科目> [值]
      python VRN2_ToolBridge_v0101.py --selftest
"""
VERSION = "VRN2_ToolBridge_v0101"


# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本支不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====


import datetime
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

SYSTEM = "VRN-2"
SCHEMA = "VIA_ToolManifest/1"
MANIFEST_NAME = "VRN2_ToolManifest_v0100.json"
HERE = Path(__file__).resolve().parent
VIA_HARD = r"C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics"   # 交接報告第 2 節的 VIA 根(使用者機器)
VRN1_HARD = r"C:\Users\tonyk\VIA-VDF-VRN"                                                      # VRN-1 = 另一團隊的倉(交接報告 L16)
VRN1_MANIFEST = ("functional modules", "VRN", "ssot", "VRN_ToolManifest_v0100.json")
OCR_BRIDGE_NAME = "VRN2_OCRBridge_v0100.py"
OK_VERDICTS = ("ALIGNED", "SUBALIGNED", "TRANSALIGNED")                                        # ⑪ 獨立驗證:值在原檔那一列、那一欄(含子欄 / 轉置表)
FACT_COLS = ("system", "file", "ticker", "broker", "report_date", "page", "table_id", "metric", "metric_raw", "unit", "period_key",
             "period_label", "period_type", "fiscal_year", "fiscal_quarter", "estimate_flag", "value", "value_raw", "status", "note", "source_id")


def nfk(t) -> str:
    return unicodedata.normalize("NFKC", "" if t is None else str(t)).strip()


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _latest(folder: Path, pat: str):
    c = sorted(Path(folder).glob(pat), key=_vnum)
    return c[-1] if c else None


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _load(path: Path, name: str):
    """依路徑載入(獨立的模組名 · 載過就沿用)· 載入期間不寫 __pycache__(借別的系統的檔時不在它的夾留檔)。"""
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, str(path))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        keep, sys.dont_write_bytecode = sys.dont_write_bytecode, True
        try:
            spec.loader.exec_module(mod)
        except BaseException:
            sys.modules.pop(name, None)
            raise
        finally:
            sys.dont_write_bytecode = keep
    return sys.modules[name]


def via_root() -> Path:
    """本支落在 <VIA 根>\\functional modules\\VRN → VIA 根;不是(單獨拿出來跑)→ VIA_ROOT / 交接報告的 VIA 根。"""
    if HERE.name == "VRN" and HERE.parent.name == "functional modules":
        return HERE.parent.parent
    return Path(os.environ.get("VIA_ROOT") or VIA_HARD)


def v2_dir(root: Path = None) -> Path:
    return Path(os.environ.get("VIA_VRN_HEALTH_OUT") or (Path(root or via_root()) / "VIA_Reports" / "vrn2"))


# =====================================================================
# 1 . 借出:section.near(VRN-2 SystemManager 的第三讀法 + _sec_near)
# =====================================================================
def _mgr():
    """VRN-2 SystemManager 尾版(本夾 · 薄尾鏈 · 前版照它自己的規則載入)· 只讀取函式,不跑任何動詞。"""
    tail = _latest(HERE, "VRN_SystemManager_v[0-9][0-9][0-9][0-9].py")
    if tail is None:
        raise RuntimeError("本夾沒有 VRN-2 SystemManager(VRN_SystemManager_v####.py)")
    m = _load(tail, "vrn2_toolbridge_mgr_" + tail.stem)
    for fn in ("_g3_page", "_xv_sq", "_sec_span", "_sec_near"):
        if not callable(getattr(m, fn, None)):
            raise RuntimeError("%s 沒有 %s(段落標題要 v0239 以後的管理器)" % (tail.name, fn))
    return m


def section_near(pdf, page, item, value=None) -> dict:
    """科目 item 那一列上方、同一個科目欄最近的段落標題(到本欄的期間表頭為止)。
    回 {"section": 標題字(沒有標題 = ""), "found": 有沒有定出來, "how": 說明, "rows": 科目那一列有幾處, "reader": 讀法}。"""
    m = _mgr()
    out = {"section": "", "found": False, "how": "", "rows": 0, "reader": "pdfplumber 字詞框(VRN-2 第三讀法 · %s)" % Path(m.__file__).name}
    g = m._g3_page(Path(pdf), int(page))
    if not g:
        out["how"] = "pdfplumber 讀不到這一頁"
        return out
    lines = g[0]
    si = m._xv_sq(item)
    labs = [(k, x0) for k, (_t, tk) in enumerate(lines) for x0 in m._sec_span(tk, si)] if si else []
    out["rows"] = len(labs)
    if not labs:
        out["how"] = "這一頁找不到科目「%s」那一列" % nfk(item)[:30]
        return out
    sv = m._xv_sq(nfk(value)) if value not in (None, "") else ""
    if sv:
        sc = [sum(1 for _, _, w in lines[k][1] if m._xv_sq(w) == sv) for k, _ in labs]
        if max(sc) == 0:                                                  # 值不在科目那一列:轉置表(科目是欄頭、值在下面幾列)或值與科目上下錯開 → 段落標題不適用 · 不定
            out["how"] = "值 %s 不在科目「%s」那一列(轉置表 / 欄頭在上)→ 段落標題不適用、不定" % (nfk(value)[:16], nfk(item)[:30])
            return out
        labs = [l_ for l_, c_ in zip(labs, sc) if c_ == max(sc)]
    # 只看科目欄起點(往左 6 pt)以右的字:並排表左邊那張表的最後一欄常落在科目欄 ±40 pt 內(MS 3661 第 10 頁:左表數值 x 282 · 右表科目 x 319),
    # 整列餵給 _sec_near 會把左表的數字當成這一列的科目 → 判成數據列、一路走到期間表頭 → 回空白。_sec_near 本身照用、不改。
    cand = {m._sec_near([(t, [z for z in tk if z[0] >= cx - 6]) for t, tk in lines], k, cx) for k, cx in labs}
    if len(cand) == 1:
        out.update(section=cand.pop(), found=True,
                   how="科目那一列 %d 處%s · 上方同一個科目欄最近的段落標題(到期間表頭為止)" % (len(labs), "(有這個值的那一列)" if sv else ""))
    else:
        out["how"] = "科目那一列 %d 處、段落標題不一致(%s)→ 不定" % (len(labs), " / ".join(sorted(repr(c) for c in cand))[:120])
    return out


# =====================================================================
# 2 . 借出:ocr.image(VRN-2 的 OCR 隔離環境)
# =====================================================================
_OCR = {}
_OCR_CHK = ("import importlib,sys\nok=0\nfor n in ('rapidocr_onnxruntime','rapidocr'):\n    try:\n        importlib.import_module(n); ok=1; break\n"
            "    except Exception: pass\nsys.exit(0 if ok else 3)")


def ocr_paths() -> tuple:
    """(隔離 python, 橋):VIA_VRN2_OCR_PY / VIA_VRN2_OCR_BRIDGE(啟動器 ③b 設的)→ 否則 <VIA_ENVS_HOME 或 ~\\envs>\\vrn2_ocr(啟動器 ③b 建的同一個夾)。"""
    py, br = os.environ.get("VIA_VRN2_OCR_PY"), os.environ.get("VIA_VRN2_OCR_BRIDGE")
    if py and br:
        return Path(py), Path(br)
    vdir = Path(os.environ.get("VIA_ENVS_HOME") or (Path.home() / "envs")) / "vrn2_ocr"
    return vdir / ("Scripts/python.exe" if os.name == "nt" else "bin/python"), vdir / OCR_BRIDGE_NAME


def ocr_ready() -> tuple:
    """(能不能用, 說明)· 隔離環境裡真的 import 得到 rapidocr 才算能用(同一行程只查一次)。"""
    if "ready" in _OCR:
        return _OCR["ready"]
    py, br = ocr_paths()
    if not py.exists():
        res = (False, "VRN-2 的 OCR 隔離環境不在(%s · VRN-2 啟動器 ③b 會建)" % py)
    elif not br.exists():
        res = (False, "VRN-2 的 OCR 橋不在(%s)" % br)
    else:
        try:
            rc = subprocess.run([str(py), "-c", _OCR_CHK], capture_output=True, timeout=180).returncode
        except (OSError, subprocess.SubprocessError) as exc:
            rc = "%s" % type(exc).__name__
        res = (rc == 0, ("VRN-2 OCR 隔離環境就緒 %s" % py) if rc == 0 else ("VRN-2 OCR 隔離環境裡沒有 rapidocr(rc %s)" % rc))
    _OCR["ready"] = res
    return res


def _pdf_images(pdf: Path, td: Path, max_pages: int) -> list:
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(pdf))
    out = []
    try:
        for i in range(min(len(doc), max_pages)):
            p_ = td / ("p%03d.png" % (i + 1))
            doc[i].render(scale=2.0).to_pil().save(str(p_))
            out.append(str(p_))
    finally:
        doc.close()
    return out


def ocr_read(path, timeout: int = 900) -> dict:
    """影像(或沒有文字層的 PDF,先轉圖)→ 文字。形狀同 VRN-1 VRN_Ocr.read(借用端不用改讀法)· 讀不到不丟例外,照實回 error。
    OCR 的字一律 source=OCR · lossy_cjk=True(rapidocr 中文會掉字:不能當 VERIFIED 的兩條讀法之一)。"""
    out = {"engine": "", "lines": [], "text": "", "chars": 0, "source": "OCR", "lossy_cjk": True, "lang": "rapidocr 內建中英(VRN-2 OCR 隔離環境)", "error": ""}
    ok, why = ocr_ready()
    if not ok:
        out["error"] = why
        return out
    py, br = ocr_paths()
    p = Path(path)
    try:
        with tempfile.TemporaryDirectory(prefix="vrn2_ocr_borrow_") as td:
            td = Path(td)
            imgs = _pdf_images(p, td, int(os.environ.get("VIA_VRN2_OCR_MAXPAGES") or 4)) if p.suffix.lower() == ".pdf" else [str(p)]
            (td / "job.json").write_text(json.dumps({"images": imgs}, ensure_ascii=False), encoding="utf-8")
            r = subprocess.run([str(py), str(br), str(td / "job.json"), str(td / "out.json")], capture_output=True, timeout=timeout,
                               env=dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1"))
            if r.returncode != 0 or not (td / "out.json").exists():
                out["error"] = "VRN2_OCRBridge rc %s · %s" % (r.returncode, r.stderr.decode("utf-8", "replace").strip()[-160:])
                return out
            got = json.loads((td / "out.json").read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - 一張圖讀不出來不該讓借用端倒掉
        out["error"] = ("%s: %s" % (type(exc).__name__, exc))[:200]
        return out
    out["engine"] = "VRN-2 %s" % got.get("engine", "rapidocr")
    out["lines"] = [x["text"] for r_ in got.get("results", []) for x in r_.get("lines", []) if str(x.get("text", "")).strip()]
    out["text"] = "\n".join(out["lines"])
    out["chars"] = len(out["text"])
    return out


# =====================================================================
# 3 . 借出工具冊
# =====================================================================
def _rel(p: Path, root: Path) -> str:
    try:
        return Path(p).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return str(p)


def offers(root: Path = None) -> list:
    """VRN-2 借出的工具(只列本機真的在的檔)。"""
    root = Path(root or via_root())
    me = Path(__file__).resolve()
    tail = _latest(HERE, "VRN_SystemManager_v[0-9][0-9][0-9][0-9].py")
    py, br = ocr_paths()
    ready, why = ocr_ready()
    tools = []
    if tail is not None:
        tools.append({"id": "section.near", "kind": "python", "file": _rel(me, root), "entry": "section_near",
                      "signature": "section_near(pdf, page, item, value=None) -> {section, found, how, rows, reader}",
                      "contract": "科目那一列上方、同一個科目欄最近的段落標題(到本欄的期間表頭為止 · 公式項不算 · 不一致 → found False)",
                      "reader": "pdfplumber 字詞框(VRN-2 SystemManager 第三讀法 _g3_page)", "needs": ["pdfplumber", "pypdfium2"],
                      "files": [{"file": _rel(me, root), "sha256": _sha(me)}, {"file": _rel(tail, root), "sha256": _sha(tail)}],
                      "ready": True, "why": "VRN-2 SystemManager %s" % tail.name})
    tools.append({"id": "ocr.image", "kind": "python", "file": _rel(me, root), "entry": "ocr_read",
                  "signature": "ocr_read(path) -> {engine, lines, text, chars, source='OCR', lossy_cjk=True, lang, error}",
                  "contract": "影像 / 沒有文字層的 PDF → 文字 · OCR 的字不能當 VERIFIED 的兩條讀法之一",
                  "reader": "rapidocr(VRN-2 OCR 隔離環境 envs\\vrn2_ocr · 借用端主環境不用裝)", "needs": ["pypdfium2(PDF 轉圖)"],
                  "files": [{"file": _rel(me, root), "sha256": _sha(me)}] + ([{"file": str(br), "sha256": _sha(br)}] if br.exists() else []),
                  "ready": ready, "why": why})
    return tools


def manifest(root: Path = None) -> dict:
    root = Path(root or via_root())
    return {"schema": SCHEMA, "system": SYSTEM, "main": "ActivateVRN-2.py → VRN-2 SystemManager", "bridge": VERSION, "root": str(root),
            "written": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rule": "借用端只讀:逐檔核對 sha256(不符 = 不借)· 不改 / 不複製 VRN-2 的檔 · 只寫借用端自己的輸出夾",
            "offers": offers(root), "borrows": [{"id": "table.pivot_db", "from": "VRN-1", "manifest": "/".join(VRN1_MANIFEST)}]}


def write_manifest(root: Path = None, out: Path = None) -> Path:
    """寫 <VIA_Reports\\vrn2>\\tools\\VRN2_ToolManifest_v0100.json(VRN-2 自己的輸出夾 · 不寫進 functional modules 的共用家族)。"""
    root = Path(root or via_root())
    out = Path(out) if out else v2_dir(root) / "tools" / MANIFEST_NAME
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text(json.dumps(manifest(root), ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(out)
    return out


# =====================================================================
# 4 . 借入:找 VRN-1 · 讀它的工具冊 · 逐檔核對 · 載入
# =====================================================================
class BorrowError(RuntimeError):
    pass


def vrn1_candidates(root: Path = None) -> list:
    """VRN-1 倉的候選位置(依序):VIA_VRN1_ROOT · 交接報告的 VRN-1 位置 · 家目錄 · VIA 倉旁邊(同一層 / 上一層)。"""
    root = Path(root or via_root())
    c = [os.environ.get("VIA_VRN1_ROOT"), VRN1_HARD, str(Path.home() / "VIA-VDF-VRN")]
    for up in list(root.parents)[:3]:
        c.append(str(up / "VIA-VDF-VRN"))
    seen, out = set(), []
    for x in c:
        if x and x not in seen:
            seen.add(x)
            out.append(Path(x))
    return out


def find_vrn1(root: Path = None) -> tuple:
    """(VRN-1 倉, 工具冊路徑, 說明)· 找不到 → (None, None, 說明)。"""
    tried, here = [], None
    for cand in vrn1_candidates(root):
        mf = cand.joinpath(*VRN1_MANIFEST)
        if mf.is_file():
            return cand, mf, "VRN-1 工具冊 %s" % mf
        tried.append(str(cand))
        if here is None and cand.joinpath("functional modules", "VRN", "VRN_Main_v0100.py").is_file():
            here = cand
    if here is not None:                                                  # VRN-1 的倉在,只是目前的版本還沒有工具冊 → 說清楚怎麼補
        # 指令放前面、路徑只出現一次:啟動器的 ⑫ 那一行最多顯示 260 字(長路徑時後半會被截掉)
        return None, None, ("VRN-1 這一版沒有工具冊(第十三輪起才有)→ cd %s; git fetch origin; "
                            "git switch claude/optimistic-goodall-yhalc5(已合併進 main:git pull)→ 再跑 VRN-2" % here)
    return None, None, "找不到 VRN-1 的工具冊(試過 %s · 可設 VIA_VRN1_ROOT)" % " / ".join(tried[:5])


def read_manifest(mf: Path) -> dict:
    d = json.loads(Path(mf).read_text(encoding="utf-8"))
    if d.get("schema") != SCHEMA or not isinstance(d.get("offers"), list):
        raise BorrowError("工具冊格式不是 %s:%s" % (SCHEMA, mf))
    return d


def borrow(tool_id: str, mf: Path = None, root: Path = None) -> tuple:
    """(函式, 紀錄):VRN-1 工具冊裡 tool_id 那一支 · 每個檔的 sha256 要和工具冊相同 · 依路徑載入(獨立模組名)· 不符 / 不在 → BorrowError。"""
    peer = None
    if mf is None:
        peer, mf, note = find_vrn1(root)
        if mf is None:
            raise BorrowError(note)
    mf = Path(mf)
    d = read_manifest(mf)
    if d.get("root") and Path(d["root"]).is_dir():
        base = Path(d["root"])
    else:                                                                 # 工具冊沒寫根(VRN-1 的冊用相對路徑)或那個根不在這台機器 → 以工具冊所在的倉為根
        base = peer or mf.parents[len(VRN1_MANIFEST) - 1]
    t = next((x for x in d["offers"] if x.get("id") == tool_id), None)
    if t is None:
        raise BorrowError("%s 的工具冊沒有 %s" % (d.get("system", "?"), tool_id))
    for f in t.get("files") or [{"file": t["file"], "sha256": ""}]:
        p = base / f["file"]
        if not p.is_file():
            raise BorrowError("%s 不在(%s)" % (f["file"], p))
        got = _sha(p)
        if f.get("sha256") and got != f["sha256"]:
            raise BorrowError("%s 的 sha256 和工具冊不同(工具冊 %s · 檔 %s)→ 不借 · VRN-1 的檔改過沒重寫工具冊:"
                              "cd <VRN-1 倉>\\functional modules\\VRN; python VRN_Main_v0100.py build" % (f["file"], f["sha256"][:12], got[:12]))
    src = base / t["file"]
    mod = _load(src, "vrn2_borrowed_%s_%s" % (re.sub(r"\W", "_", tool_id), _sha(src)[:10]))
    fn = getattr(mod, t["entry"], None)
    if not callable(fn):
        raise BorrowError("%s 沒有入口 %s" % (t["file"], t["entry"]))
    return fn, {"id": tool_id, "from": d.get("system", ""), "file": str(src), "sha256": _sha(src), "entry": t["entry"],
                "contract": t.get("contract", ""), "manifest": str(mf), "module": mod}


# =====================================================================
# 5 . 借 VRN-1 PIVOT:VRN-2 年度數據冊 → 契約 VIA_PivotFacts/1
# =====================================================================
_PER_Y = re.compile(r"(?i)^(?:FY|CY)?['’]?((?:19|20)?\d{2})\s*(\(?[AEFPH]\)?|CT|C)?$")
_PER_MY = re.compile(r"(?i)^(?:(\d{1,2})/|([A-Z][a-z]{2})-)((?:19|20)?\d{2})([AEFPe]?)$")
_PER_Q = re.compile(r"(?i)^([1-4])Q((?:19|20)?\d{2})([AEFP]?)$")


def period_of(per) -> dict:
    """VRN-2 的期間字 → {period_key, period_type, fiscal_year, fiscal_quarter, estimate_flag}。
    2025E / 2025A / 2025CT / 2025(F) / FY25E / 25E → 年;12/25E · Dec-25F(會計年度結束的月-年)→ 年;1Q26 → 2026-03(季)· 其他(1H26 · TTM)→ 空(不進 PIVOT)。"""
    t = nfk(per)
    out = {"period_key": "", "period_type": "", "fiscal_year": "", "fiscal_quarter": "", "estimate_flag": ""}

    def yy(s):
        return int(s) if len(s) == 4 else 2000 + int(s)
    m = _PER_Q.match(t)
    if m:
        y = yy(m.group(2))
        out.update(period_key="%d-%02d" % (y, 3 * int(m.group(1))), period_type="FQ", fiscal_year=str(y), fiscal_quarter="%d-%02d" % (y, 3 * int(m.group(1))),
                   estimate_flag=m.group(3).upper())
        return out
    m = _PER_Y.match(t)
    if m:
        y = yy(m.group(1))
        out.update(period_key=str(y), period_type="FY", fiscal_year=str(y), estimate_flag=(m.group(2) or "").strip("()").upper())
        return out
    m = _PER_MY.match(t)
    if m:
        y = yy(m.group(3))
        out.update(period_key=str(y), period_type="FY", fiscal_year=str(y), estimate_flag=m.group(4).upper())
    return out


def _num(v):
    t = nfk(v).replace("−", "-").replace("–", "-").replace(",", "")
    neg = t.startswith("(") and t.rstrip("%").endswith(")")
    t = t.strip("()% ")
    try:
        x = float(t)
    except ValueError:
        return None
    return -abs(x) if neg else x


def book_fp(rows: list) -> str:
    """年度數據冊指紋 —— 用 VRN-2 獨立驗證器自己的算法(落地的 VRN2_IndependentVerifier 尾版 book_fp · 同一支 · 不另寫)。"""
    ver = _latest(HERE, "VRN2_IndependentVerifier_v[0-9][0-9][0-9][0-9].py")
    if ver is None:
        raise RuntimeError("本夾沒有 VRN2_IndependentVerifier(算不出冊指紋 · 判決對不上冊)")
    return _load(ver, "vrn2_toolbridge_iv_" + ver.stem).book_fp(rows)


def verdicts(v2: Path, rows: list) -> tuple:
    """⑪ 最新一份獨立驗證報告 · 冊指紋與筆數都和這本冊相同才用 → ({序號: (判決, 說明)}, 說明)。"""
    vd = Path(v2) / "verify_independent"
    reps = sorted(vd.glob("VRN2_IndependentVerify_*.json"), key=lambda p: p.stat().st_mtime) if vd.is_dir() else []
    if not reps:
        return {}, "沒有 ⑪ 獨立驗證報告 → 每筆 UNVERIFIED(不進 PIVOT)"
    fp = book_fp(rows)
    for rp in reversed(reps):
        try:
            d = json.loads(rp.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if d.get("fp") == fp and d.get("n") == len(rows):
            return {int(i): (v, n) for i, v, n in d.get("fin_rows") or [] if isinstance(i, int)}, "⑪ %s(冊指紋 %s 相同)" % (rp.name, fp)
    return {}, "⑪ 的報告都不是這本冊(冊指紋 %s 對不上)→ 每筆 UNVERIFIED(不進 PIVOT)" % fp


def vrn2_facts(rows: list, vd: dict) -> list:
    """VRN-2 年度數據冊 → 契約 VIA_PivotFacts/1(VRN-2 這邊自己對欄位 · VRN-1 的工具只認契約)。
    科目照原文(VRN-2 沒有標準科目);段落標題 / 子欄是不同的量 → 寫進 metric_raw(「段落 › 科目 [子欄]」)· 判決照 ⑪。
    同一張表裡同一個科目字出現在好幾列(現金流量表的 Other adjustments · 每個科目底下的 Percent of Revenues)→ 是不同的量,
    科目後面加「#列號」分開(VRN-2 獨立驗證器 DUPKEY 也是用 檔 · 表 · 列 · 科目 · 期間 · 子欄 當一格)。"""
    out = []
    rows_of = {}
    for r in rows:
        rows_of.setdefault((nfk(r.get("FILENAME")), nfk(r.get("TABLE")), nfk(r.get("ITEM")), nfk(r.get("SECTION")), nfk(r.get("SUBCOL"))), set()).add(nfk(r.get("ROW")))
    for i, r in enumerate(rows):
        item, sec, sub = nfk(r.get("ITEM")), nfk(r.get("SECTION")), nfk(r.get("SUBCOL"))
        many = len(rows_of[(nfk(r.get("FILENAME")), nfk(r.get("TABLE")), item, sec, sub)]) > 1
        raw = (sec + " › " if sec else "") + item + (" #%s" % nfk(r.get("ROW")) if many else "") + (" [%s]" % sub if sub else "")
        v, n = vd.get(i, ("", ""))
        p = period_of(r.get("PERIOD"))
        out.append(dict(p, system=SYSTEM, file=nfk(r.get("FILENAME")), ticker=nfk(r.get("TICKER")), broker=nfk(r.get("BROKER")),
                        report_date=nfk(r.get("REPORT_DATE")), page=nfk(r.get("PAGE")), table_id=nfk(r.get("TABLE")), metric=item, metric_raw=raw,
                        unit="", period_label=nfk(r.get("PERIOD")), value=_num(r.get("VALUE")), value_raw=nfk(r.get("VALUE")),
                        status=("VERIFIED" if v in OK_VERDICTS else (v or "UNVERIFIED")),
                        note=("⑪ %s · %s" % (v, n) if v else "⑪ 沒有判決") + (" · VRN-2 %s" % nfk(r.get("VERIFY")) if r.get("VERIFY") else ""),
                        source_id="I%05d" % i))
    return out


def pivot_vrn2(v2: Path = None, mf: Path = None) -> dict:
    """⑫ 借 VRN-1 的 PIVOT 工具 → <vrn2>\\pivot\\(VRN-2 自己的輸出夾)。回 build_pivot_db 的摘要 + 借用紀錄。"""
    v2 = Path(v2 or v2_dir())
    book = v2 / "output" / "VRN2_FinancialData_latest.json"
    rows = json.loads(book.read_text(encoding="utf-8"))
    vd, how = verdicts(v2, rows)
    fn, rec = borrow("table.pivot_db", mf)
    facts = vrn2_facts(rows, vd)
    s = fn(facts, v2 / "pivot", (), title="VRN-2 · %s" % book.name, generated_by="VRN-2 ⑫(借用 VRN-1 table.pivot_db)")
    rec = {k: v for k, v in rec.items() if k != "module"}
    s["borrow"], s["verdicts"] = rec, how
    (v2 / "pivot" / "VRN2_Pivot_Borrow_latest.json").write_text(json.dumps({"borrow": rec, "verdicts": how, "counts": s.get("counts"),
                                                                            "fingerprint": s.get("fingerprint"), "duckdb_check": s.get("duckdb_check")},
                                                                           ensure_ascii=False, indent=1), encoding="utf-8")
    return s


# =====================================================================
# 6 . 自測(不需要 PDF / VRN-1:假的工具冊 + 假的工具)
# =====================================================================
def selftest() -> int:
    ok_all = []

    def chk(name, cond):
        ok_all.append(bool(cond))
        print("  [%s] %s" % ("PASS" if cond else "FAIL", name))
    chk("期間:2025E → 2025 · E", period_of("2025E")["period_key"] == "2025" and period_of("2025E")["estimate_flag"] == "E")
    chk("期間:FY25A · 25E · 2025CT · 2025(F) → 年", [period_of(x)["period_key"] for x in ("FY25A", "25E", "2025CT", "2025(F)")] == ["2025"] * 4)
    chk("期間:12/25E · Dec-25F(月-年)→ 2025", [period_of(x)["period_key"] for x in ("12/25E", "Dec-25F", "Mar-26")] == ["2025", "2025", "2026"])
    chk("期間:1Q26 → 2026-03(季)· 1H26 / TTM → 空", period_of("1Q26")["period_key"] == "2026-03" and period_of("1H26")["period_key"] == "" and period_of("TTM")["period_key"] == "")
    rows = [{"FILENAME": "a.pdf", "TICKER": "1234", "BROKER": "B", "REPORT_DATE": "2026-01-01", "PAGE": 3, "TABLE": "T", "ITEM": "Net profit", "PERIOD": "2025E",
             "VALUE": "(1,234.5)", "SECTION": "Growth (%)", "SUBCOL": "New"},
            {"FILENAME": "a.pdf", "TICKER": "1234", "BROKER": "B", "REPORT_DATE": "2026-01-01", "PAGE": 3, "TABLE": "T", "ITEM": "Net profit", "PERIOD": "2026E",
             "VALUE": "-", "SECTION": "", "SUBCOL": None}]
    rows += [dict(rows[1], ITEM="Other adjustments", ROW=4, PERIOD="2025E", VALUE="7"), dict(rows[1], ITEM="Other adjustments", ROW=9, PERIOD="2025E", VALUE="8")]
    f = vrn2_facts(rows, {0: ("ALIGNED", "dx 0.5")})
    chk("事實表:同一張表同一個科目字在兩列 → 加「#列號」分開(不是衝突)", [x["metric_raw"] for x in f[2:]] == ["Other adjustments #4", "Other adjustments #9"])
    chk("事實表:欄位就是契約 VIA_PivotFacts/1", all(set(FACT_COLS) <= set(x) for x in f))
    chk("事實表:段落 › 科目 [子欄] · 值 (1,234.5) → -1234.5 · ALIGNED → VERIFIED",
        f[0]["metric_raw"] == "Growth (%) › Net profit [New]" and f[0]["value"] == -1234.5 and f[0]["status"] == "VERIFIED")
    chk("事實表:沒有判決 → UNVERIFIED · 「-」→ 值 None", f[1]["status"] == "UNVERIFIED" and f[1]["value"] is None)
    with tempfile.TemporaryDirectory(prefix="vrn2_bridge_") as td:
        td = Path(td)
        peer = td / "VIA-VDF-VRN"
        tool = peer / "functional modules" / "VRN" / "engine" / "fake_pivot.py"
        tool.parent.mkdir(parents=True)
        tool.write_text("def build(facts, out, restored=(), title='', generated_by=''):\n    return {'n': len(facts), 'by': generated_by}\n", encoding="utf-8")
        mfp = peer.joinpath(*VRN1_MANIFEST)
        mfp.parent.mkdir(parents=True)
        man = {"schema": SCHEMA, "system": "VRN-1", "root": str(peer),
               "offers": [{"id": "table.pivot_db", "kind": "python", "file": "functional modules/VRN/engine/fake_pivot.py", "entry": "build",
                           "files": [{"file": "functional modules/VRN/engine/fake_pivot.py", "sha256": _sha(tool)}]}]}
        mfp.write_text(json.dumps(man), encoding="utf-8")
        os.environ["VIA_VRN1_ROOT"] = str(peer)
        try:
            r_, mf_, _n = find_vrn1(td)
            chk("找 VRN-1:VIA_VRN1_ROOT 優先 → 工具冊", mf_ == mfp)
            fn, rec = borrow("table.pivot_db")
            chk("借:sha256 相同 → 載入 · 入口可呼叫 · 紀錄來源", fn([1, 2], td, generated_by="x") == {"n": 2, "by": "x"} and rec["from"] == "VRN-1")
            tool.write_text(tool.read_text(encoding="utf-8") + "# changed\n", encoding="utf-8")
            try:
                borrow("table.pivot_db")
                chk("借:檔被改過(sha256 不同)→ 不借", False)
            except BorrowError as exc:
                chk("借:檔被改過(sha256 不同)→ 不借", "sha256" in str(exc))
            try:
                borrow("no.such.tool")
                chk("借:工具冊沒有這支 → 不借", False)
            except BorrowError as exc:
                chk("借:工具冊沒有這支 → 不借", "沒有" in str(exc))
            with tempfile.TemporaryDirectory(prefix="vrn2_bridge_bare_") as td2:   # 另一個夾:上面那個假 VRN-1 不在它的候選路徑上
                bare = Path(td2) / "VIA-VDF-VRN"
                bare.joinpath("functional modules", "VRN").mkdir(parents=True)
                bare.joinpath("functional modules", "VRN", "VRN_Main_v0100.py").write_text("# main\n", encoding="utf-8")
                os.environ["VIA_VRN1_ROOT"] = str(bare)
                _r, mf2, n2 = find_vrn1(Path(td2) / "VIA" / "elsewhere")
                real = any(c.joinpath(*VRN1_MANIFEST).is_file() for c in vrn1_candidates(Path(td2) / "VIA" / "elsewhere")[1:])
                chk("VRN-1 的倉在、目前版本沒有工具冊 → 說清楚要切到哪個版本(git switch · 整條指令在啟動器顯示的 260 字內)",
                    real or (mf2 is None and "git switch" in n2 and str(bare) in n2 and "optimistic-goodall-yhalc5" in ("⑫ 借不到 VRN-1 的 PIVOT 工具 · " + n2)[:260]))
        finally:
            os.environ.pop("VIA_VRN1_ROOT", None)
        os.environ["VIA_VRN2_OCR_PY"], os.environ["VIA_VRN2_OCR_BRIDGE"] = str(td / "no_py"), str(td / "no_bridge.py")
        _OCR.clear()
        try:
            got = ocr_read(td / "x.png")
            chk("OCR:隔離環境不在 → 不丟例外 · 照實回 error · 標 source=OCR", got["error"] and got["source"] == "OCR" and got["lossy_cjk"] is True)
            mft = write_manifest(td, td / "m.json")
            md = json.loads(mft.read_text(encoding="utf-8"))
            ocr_t = next((x for x in md["offers"] if x["id"] == "ocr.image"), {})
            chk("工具冊:%s · 借出 ocr.image 標「不能用」與理由 · 檔都有 sha256" % SCHEMA,
                md["schema"] == SCHEMA and ocr_t.get("ready") is False and ocr_t.get("why") and all(len(f_["sha256"]) == 64 for t_ in md["offers"] for f_ in t_["files"]))
        finally:
            os.environ.pop("VIA_VRN2_OCR_PY", None)
            os.environ.pop("VIA_VRN2_OCR_BRIDGE", None)
            _OCR.clear()
    n = sum(ok_all)
    print("[計] %s 自測 %d/%d · %s" % (VERSION, n, len(ok_all), "PASS" if n == len(ok_all) else "FAIL"))
    return 0 if n == len(ok_all) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if a[0] == "--selftest":
        return selftest()
    if a[0] == "manifest":
        p = write_manifest(Path(a[1]) if len(a) > 1 else None)
        d = json.loads(p.read_text(encoding="utf-8"))
        print("[計] VRN-2 借出工具冊 %s · %s" % (p, " · ".join("%s %s" % (t["id"], "能用" if t["ready"] else "不能用(%s)" % t["why"]) for t in d["offers"])))
        return 0
    if a[0] == "peers":
        _r, mf, note = find_vrn1()
        print("[計] %s" % note)
        if mf is None:
            return 1
        rc = 0
        for t in read_manifest(mf).get("offers", []):
            try:
                _fn, rec = borrow(t["id"], mf)
                print("  [可借] %s · %s · sha %s" % (t["id"], rec["file"], rec["sha256"][:12]))
            except Exception as exc:  # noqa: BLE001
                rc = 1
                print("  [不借] %s · %s" % (t.get("id"), exc))
        return rc
    if a[0] == "pivot":
        try:
            s = pivot_vrn2(Path(a[1]) if len(a) > 1 else None)
        except BorrowError as exc:                                        # 3 = 借不到(VRN-1 不在 / 工具冊沒有 / sha256 不同):VRN-2 照常 · 只是沒有 PIVOT
            print("[計] ⑫ 借不到 VRN-1 的 PIVOT 工具 · %s" % exc)
            return 3
        except FileNotFoundError as exc:                                  # 4 = 本輪沒有年度數據冊
            print("[計] ⑫ 沒有年度數據冊 · %s" % exc)
            return 4
        c = s["counts"]
        print("[計] ⑫ PIVOT(借用 VRN-1 table.pivot_db · sha256 %s)· 事實 %d/%d 收進 · 年度 %d 列 · 季度 %d 列(表層 %d / %d)· 衝突 %d · 精度合併 %d · "
              "DuckDB %s · 指紋 %s · %s" % (s["borrow"]["sha256"][:12], c["kept"], c["facts"], c["pivot_report_annual"], c["pivot_report_quarterly"],
                                            c["pivot_annual"], c["pivot_quarterly"], c["conflicts"], c.get("precision_merges", 0),
                                            (s.get("duckdb_check") or {}).get("pivot_check", "沒有 duckdb") if s.get("duckdb") else "沒有 duckdb(SQLite 已寫)",
                                            s["fingerprint"], s["verdicts"]))
        print("[計] ⑫ HTML %s" % s["html"])
        return 0
    if a[0] == "section" and len(a) >= 4:
        print(json.dumps(section_near(a[1], int(a[2]), a[3], a[4] if len(a) > 4 else None), ensure_ascii=False))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
