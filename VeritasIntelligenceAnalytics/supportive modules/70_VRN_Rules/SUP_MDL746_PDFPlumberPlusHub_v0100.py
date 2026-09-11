#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""SUP_MDL746 · PDFPlumberPlusHub v0100 —— PDFPlumber-Plus 收容件統轄橋

操作員 2026-09-12 上傳 `VIA_PDFPlumberPlusEngine.py`(1196 行)並令「接上去」。

**先查再造(第五次)——而且這一次我先講錯,改回來:**

  我上一輪對操作員說「這包真正庫裡沒有的,是它**真的會去建構** PaddleOCR /
  PP-Structure」。**那句是錯的。** 查了 GLE v2.1.0 的 all_backend_engines.py
  才知道:`PaddleOcrEngine.extract()` 第 1334-1348 行同樣真的 `from paddleocr
  import PaddleOCR` 並建構,而且**連 3.x 新 API 都接**(PPStructureV3 /
  LayoutDetection / engine.predict());這包只接得動 2.x(`PPStructure`、
  `use_gpu`、`show_log` 都是 2.x 才有的鍵)。論 OCR 建構,**庫裡那支比較新**。

  逐項對照之後,這包真正非重疊的是三件:

  ① **逐頁分流 + 字元密度閘**(`TRIAGE_MIN_CHAR_DENSITY = 0.0002`)
     ——這是本批真正的收穫,而且**一個新套件都不必裝**。
     ENG072 今天的判準是 `if txt: return txt`:只要抽得到**一個字**就算有文字層。
     一頁只有浮水印文字層(「機密」「DRAFT」十來個字)的掃描頁,今天會被判成
     「有文字」而**直接放行**,首頁引擎再從那十來個字裡找目標價——那是假綠。
     密度閘把「字數/頁面點面積」一起看:15 字 ÷ 500000 點² = 3e-5 < 2e-4 → 掃描頁。
     GLE 沒有這一道,ENG072 也沒有。
  ② **pdfplumber 四策略表格抽取 + 重疊率去重 + 表頭回溯 + 填充率平方化評分**
     ——GLE 的 pdfplumber 轉接器(第 353 行)只跑 `lines/lines` 單一策略。
  ③ **OCR 車道的另一條路**:記憶體內 fitz→NumPy 渲染(GLE 是 fitz→PNG 落地),
     以及 `_build()` 逐鍵剝除不支援 kwargs——2.x 各小版差異它擋得比 GLE 細。
     **這條是補位不是取代**:paddleocr 3.x 走 GLE、2.x 走這包,誰在位誰上。

紀律:
  · **收容件原地不動**——不改它一個位元。它 `_PARAMS["VIA_ROOT"]` 硬寫
    `C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics`(操作員實際機是
    `...\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics`,不合),
    本橋一律用 `CFG["out_dir"]` 蓋過去,**絕不讓它往那個硬寫路徑寫任何東西**。
  · 零網路、零彈窗(它只寫 report.html,不會自己開窗;進度條走 stderr,
    服務車道在**記憶體內**把 `PROGRESS_ENABLED` 關掉,檔案一位元不動)
  · 掛不上就誠實回 ABSENT/FAILED 並講出因由——不靜默退後備(批419e)
  · 尾版律:同名多版取語意版號最大者
  · Zero-Hydra:本橋不自己再寫一套 OCR / 表格抽取,只把收容件的接出來
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
INTAKE = VIA / "functional modules" / "VRN" / "references" / "intake"

MODULE_ID = "SUP_MDL746"
HUB_NAME = "PDFPlumberPlusHub"
HUB_VERSION = "v0100"
PKG_GLOB = "VIA_PDFPlumberPlusEngine_v*"
PKG_MARKER = Path("VIA_PDFPlumberPlusEngine.py")

#: 正式跑全檔時的落地根。VIA_Reports/* 已在 .gitignore,產出不入 git(批232 紅線同族)
OUT_ROOT = VIA / "VIA_Reports" / "pdfplumber_plus"

#: **本橋自訂的絕對字數底線**——收容件沒有這個鍵,是本批從真檔量出來加上的。
#:
#: 為什麼要加:收容件的 `TRIAGE_MIN_CHAR_DENSITY = 0.0002` 單獨用會誤殺。
#: 全庫 20 件 PDF 掃過一輪,`supportive modules/specs/Veritas Intelligence
#: Analytics Brief.pdf` 是 **949×7448 點的長捲頁**(14.1 倍 A4 面積),首頁有
#: 862 個字的 8-11pt 正文——真真正正的文字層,密度卻只有 1.22e-04 < 2e-04,
#: 光看密度會被判成掃描頁。**那是假紅。**
#: 這正是批440 那一課:改嚴一道閘之前要有真檔證據,合成測資只證明碼會動。
#:
#: 修法:密度只當**訊號**不當**判決**。絕對字數夠多就不許只憑密度降級。
#: 界線取 300——全庫最低的真文字首頁是 442 字(synthetic_financial_report),
#: 浮水印/戳章那種頁在 100 字以下,300 兩邊都留得住餘裕。
SPARSE_CHARS = 300

#: 服務車道(只要文字/表格,不要落地件)的參數覆寫
SERVICE_OVERRIDE = {
    "EMIT_JSON": False, "EMIT_CSV": False, "EMIT_MARKDOWN": False,
    "EMIT_HTML_REPORT": False, "PROGRESS_ENABLED": False,
}

_CACHE: dict = {}


def _ver(d: Path) -> tuple:
    """語意版號。字母序陷阱:'v1.10.0' < 'v1.9.0' 為字串真、語意假。"""
    vs = [(int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))
          for m in re.finditer(r"v(\d+)\.(\d+)(?:\.(\d+))?", d.name)]
    return max(vs) if vs else (0, 0, 0)


def roots() -> list[Path]:
    if not INTAKE.is_dir():
        return []
    return [d for d in sorted(INTAKE.glob(PKG_GLOB))
            if d.is_dir() and (d / PKG_MARKER).is_file()]


def newest() -> Path | None:
    c = roots()
    return max(c, key=_ver) if c else None


def mount() -> dict:
    """掛載尾版收容件。只 import,不執行它的 main/CLI。"""
    if "mount" in _CACHE:
        return _CACHE["mount"]
    d = newest()
    if d is None:
        st = {"state": "ABSENT", "dir": "", "dir_name": "", "version": "",
              "why": f"intake 下找不到 {PKG_GLOB}/{PKG_MARKER}({INTAKE})"}
        _CACHE["mount"] = st
        return st
    try:
        import importlib.util
        f = d / PKG_MARKER
        spec = importlib.util.spec_from_file_location("via_pdfplumber_plus", f)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        need = ("_PARAMS", "_Triage", "_DigitalExtractor", "_ScannedExtractor",
                "_probe_capabilities", "PDFPlumberPlusEngine")
        miss = [n for n in need if not hasattr(mod, n)]
        if miss:
            st = {"state": "FAILED", "dir": str(d), "dir_name": d.name,
                  "version": ".".join(str(x) for x in _ver(d)),
                  "why": f"收容件在位但缺件 {miss}(版本不合?)"}
        else:
            # 記憶體內關掉 stderr 進度條:_progress/_log 讀的是模組級 _PARAMS,
            # 沒有別的把手。**檔案不動**,只動這個已載入的模組物件。
            try:
                mod._PARAMS["PROGRESS_ENABLED"] = False
            except Exception:
                pass
            _CACHE["mod"] = mod
            st = {"state": "VERIFIED", "dir": str(d), "dir_name": d.name,
                  "version": str(mod._PARAMS.get("ENGINE_VERSION") or ""), "why": ""}
    except Exception as exc:
        st = {"state": "FAILED", "dir": str(d), "dir_name": d.name,
              "version": ".".join(str(x) for x in _ver(d)),
              "why": f"載入失敗 {type(exc).__name__}:{str(exc)[:90]}"}
    _CACHE["mount"] = st
    return st


def _mod():
    mount()
    return _CACHE.get("mod")


def params(**over) -> dict:
    """收容件 _PARAMS 的**副本**加覆寫。絕不就地改它的字典(除進度旗標外)。"""
    m = _mod()
    if m is None:
        return {}
    p = dict(m._PARAMS)
    p.update(SERVICE_OVERRIDE)
    p.update(over)
    return p


# ---------- ① 逐頁分流 + 字元密度閘(本批真正的收穫;零新套件) ----------

def triage(pdf: Path | str, page_no: int = 1) -> dict:
    """這一頁到底是**有文字層**還是**掃描影像**?

    **誠實三態**(不是兩態——分不出來的時候不許硬分):
      DIGITAL 有文字層,照抽
      THIN    文字層在、字數也夠,但**每單位面積稀薄**(長捲頁/海報/投影片那種)。
              照抽,但把「稀薄」講出來,不要假裝它和一般頁一樣。
      SCANNED 幾乎沒有文字層 → 該走 OCR
      UNKNOWN 探不動(檔不在/頁數不足/收容件缺席)——不猜

    回 {"state", "n_chars", "area", "density", "min_chars", "min_density",
        "sparse_chars", "backend", "why"}

    ENG072 今天只問 `if txt:`——抽得到一個字就算有文字層。一頁只有浮水印
    文字層的掃描頁會被那一問放行,首頁引擎再從那十來個字裡找目標價,**那是假綠**。
    這一道把「字數 ÷ 頁面點面積」一起看。但密度**只當訊號不當判決**:
    字數夠多(>= SPARSE_CHARS)就只標 THIN,不准降級成 SCANNED——理由見上面
    SPARSE_CHARS 的真檔證據(949×7448 長捲頁那件,光看密度會假紅)。
    """
    m = _mod()
    p = Path(str(pdf))
    if m is None:
        return {"state": "UNKNOWN", "n_chars": 0, "area": 0.0, "density": 0.0,
                "min_chars": 0, "min_density": 0.0, "sparse_chars": SPARSE_CHARS,
                "backend": "",
                "why": mount().get("why") or "收容件缺席"}
    if not p.is_file():
        return {"state": "UNKNOWN", "n_chars": 0, "area": 0.0, "density": 0.0,
                "min_chars": 0, "min_density": 0.0, "sparse_chars": SPARSE_CHARS,
                "backend": "",
                "why": f"檔不在:{p}"}
    P = params()
    idx = max(0, int(page_no) - 1)
    native, area, backend, why = "", 0.0, "", ""
    tr = None
    try:
        tr = m._Triage(p, P)
        if tr.available:
            backend = tr.backend
            if idx >= tr.page_count():
                return {"state": "UNKNOWN", "n_chars": 0, "area": 0.0, "density": 0.0,
                        "min_chars": P["TRIAGE_MIN_CHARS"],
                        "min_density": P["TRIAGE_MIN_CHAR_DENSITY"],
                        "sparse_chars": SPARSE_CHARS,
                        "backend": backend, "why": f"只有 {tr.page_count()} 頁,取不到第 {page_no} 頁"}
            native = tr.native_text(idx)
            area = tr.page_area(idx)
        else:
            import pdfplumber
            backend = "pdfplumber"
            with pdfplumber.open(str(p)) as doc:
                if idx >= len(doc.pages):
                    return {"state": "UNKNOWN", "n_chars": 0, "area": 0.0, "density": 0.0,
                            "min_chars": P["TRIAGE_MIN_CHARS"],
                            "min_density": P["TRIAGE_MIN_CHAR_DENSITY"],
                            "sparse_chars": SPARSE_CHARS,
                            "backend": backend,
                            "why": f"只有 {len(doc.pages)} 頁,取不到第 {page_no} 頁"}
                pg = doc.pages[idx]
                native = (pg.extract_text() or "").strip()
                area = max(1.0, float(pg.width) * float(pg.height))
    except Exception as exc:
        _CACHE["why_triage"] = f"{type(exc).__name__}:{str(exc)[:70]}"
        return {"state": "UNKNOWN", "n_chars": 0, "area": 0.0, "density": 0.0,
                "min_chars": P.get("TRIAGE_MIN_CHARS", 0),
                "min_density": P.get("TRIAGE_MIN_CHAR_DENSITY", 0.0),
                "sparse_chars": SPARSE_CHARS,
                "backend": backend, "why": f"分流失敗 {type(exc).__name__}:{str(exc)[:70]}"}
    finally:
        try:
            if tr is not None:
                tr.close()
        except Exception:
            pass
    area = max(1.0, float(area))
    n = len(native)
    dens = n / area
    dense_ok = dens >= P["TRIAGE_MIN_CHAR_DENSITY"]
    if n < P["TRIAGE_MIN_CHARS"]:
        state = "SCANNED"
        why = f"字數 {n} < {P['TRIAGE_MIN_CHARS']}=幾乎無文字層,判掃描頁"
    elif dense_ok:
        state = "DIGITAL"
    elif n >= SPARSE_CHARS:
        # 密度不足但字數夠——長捲頁/海報/投影片。**不准只憑密度降級**(假紅)
        state = "THIN"
        why = (f"密度 {dens:.2e} < {P['TRIAGE_MIN_CHAR_DENSITY']:.0e} 但字數 {n} "
               f">= {SPARSE_CHARS}=長捲頁/大版面的真文字層,照抽並標稀薄(不降級)")
    else:
        state = "SCANNED"
        why = (f"字數 {n} < {SPARSE_CHARS} 且密度 {dens:.2e} < "
               f"{P['TRIAGE_MIN_CHAR_DENSITY']:.0e}=浮水印/戳章那種假文字層,判掃描頁")
    return {"state": state, "n_chars": n,
            "area": round(area, 1), "density": dens,
            "min_chars": P["TRIAGE_MIN_CHARS"],
            "min_density": P["TRIAGE_MIN_CHAR_DENSITY"],
            "sparse_chars": SPARSE_CHARS,
            "backend": backend, "why": why}


# ---------- ② 四策略表格(GLE 的 pdfplumber 轉接器只跑 lines/lines 一種) ----------

def tables(pdf: Path | str, page_no: int = 1) -> list[dict]:
    """四策略抽表 + 重疊率去重 + 表頭回溯。缺席回空清單並留因由,不自己切一套。"""
    m = _mod()
    p = Path(str(pdf))
    if m is None or not p.is_file():
        _CACHE["why_tables"] = (mount().get("why") or "") if m is None else f"檔不在:{p}"
        return []
    try:
        import pdfplumber
        P = params()
        de = m._DigitalExtractor(P)
        idx = max(0, int(page_no) - 1)
        with pdfplumber.open(str(p)) as doc:
            if idx >= len(doc.pages):
                _CACHE["why_tables"] = f"只有 {len(doc.pages)} 頁"
                return []
            res = de.extract(doc.pages[idx], int(page_no))
        return list(res.get("tables") or [])
    except Exception as exc:
        _CACHE["why_tables"] = f"{type(exc).__name__}:{str(exc)[:70]}"
        return []


def page_text(pdf: Path | str, page_no: int = 1) -> tuple[str, str]:
    """有文字層時的取文(pdfplumber 車道)。回 (文字, 標記)。"""
    m = _mod()
    p = Path(str(pdf))
    if m is None:
        return "", f"PPP_ABSENT({mount().get('why') or ''})"
    if not p.is_file():
        return "", f"PPP_NO_FILE({p.name})"
    try:
        import pdfplumber
        P = params()
        de = m._DigitalExtractor(P)
        idx = max(0, int(page_no) - 1)
        with pdfplumber.open(str(p)) as doc:
            if idx >= len(doc.pages):
                return "", f"PPP_NO_PAGE({len(doc.pages)} 頁)"
            res = de.extract(doc.pages[idx], int(page_no))
        t = (res.get("text") or "").strip()
        return t, ("PPP_PDFPLUMBER" if t else "PPP_EMPTY(有頁無字)")
    except Exception as exc:
        return "", f"PPP_RUN_FAIL({type(exc).__name__}:{str(exc)[:60]})"


# ---------- ③ OCR 補位車道(paddleocr 2.x;3.x 走 GLE) ----------

def ocr_ready() -> tuple[bool, str]:
    """這條 OCR 車道現在到底跑不跑得動?**不裝作跑得動**。"""
    m = _mod()
    if m is None:
        return False, f"收容件缺席({mount().get('why') or ''})"
    caps = capabilities()
    miss = [k for k in ("paddleocr", "numpy") if str(caps.get(k, "MISSING")).startswith("MISSING")]
    if str(caps.get("pymupdf", "MISSING")).startswith("MISSING"):
        miss.append("pymupdf(渲染掃描頁要它)")
    if miss:
        return False, f"缺 {', '.join(miss)}"
    return True, ""


def ocr_page(pdf: Path | str, page_no: int = 1) -> tuple[str, str]:
    """掃描影像頁的 OCR(記憶體內 fitz→NumPy 渲染,不落暫存圖)。

    回 (文字, 標記)。一個件都沒裝就回 ("", "PPP_OCR_ABSENT(缺 …)")——**絕不假抽**。
    """
    m = _mod()
    p = Path(str(pdf))
    if m is None:
        return "", f"PPP_ABSENT({mount().get('why') or ''})"
    if not p.is_file():
        return "", f"PPP_NO_FILE({p.name})"
    ready, why = ocr_ready()
    if not ready:
        return "", f"PPP_OCR_ABSENT({why})"
    P = params()
    idx = max(0, int(page_no) - 1)
    tr = None
    try:
        tr = m._Triage(p, P)
        if not tr.available:
            return "", "PPP_RENDER_ABSENT(PyMuPDF 掛不動,渲染不了掃描頁)"
        if idx >= tr.page_count():
            return "", f"PPP_NO_PAGE({tr.page_count()} 頁)"
        img = tr.render_rgb(idx)
        sc = m._ScannedExtractor(P)
        res = sc.extract(img, int(page_no))
        del img
    except Exception as exc:
        return "", f"PPP_OCR_FAIL({type(exc).__name__}:{str(exc)[:60]})"
    finally:
        try:
            if tr is not None:
                tr.close()
        except Exception:
            pass
    t = (res.get("text") or "").strip()
    eng = res.get("engine") or "?"
    note = res.get("note") or ""
    if t:
        return t, f"PPP_OCR_{eng}"
    if note:
        return "", f"PPP_OCR_{note}({eng})"
    return "", f"PPP_OCR_EMPTY({eng};跑了但零字=影像可能不可辨)"


# ---------- 全檔跑(操作員自用;落地到 VIA_Reports,不入 git) ----------

def run_full(pdf: Path | str, out_dir: Path | str | None = None) -> dict:
    """整份跑並落地 JSON/CSV/Markdown/HTML + G00-G12 閘報。

    **落地根一律由本橋給**——收容件 _PARAMS["VIA_ROOT"] 硬寫的那個 Windows 路徑
    在操作員實際機上不存在,放它自己決定就會寫到錯的地方或直接炸。
    """
    m = _mod()
    if m is None:
        return {"ok": False, "errors": [f"HUB_ABSENT: {mount().get('why') or ''}"]}
    out = Path(str(out_dir)) if out_dir else OUT_ROOT
    try:
        return m.PDFPlumberPlusEngine({
            "pdf_path": str(Path(str(pdf))),
            "out_dir": str(out),
            "params": {"PROGRESS_ENABLED": False},
        }).run()
    except Exception as exc:
        return {"ok": False, "errors": [f"RUN_FAILED: {type(exc).__name__}: {exc}"]}


# ---------- 診斷面 ----------

def capabilities() -> dict:
    """收容件自己的能力探針(誠實回報哪些第三方引擎真的在場)。"""
    m = _mod()
    if m is None:
        return {}
    try:
        return dict(m._probe_capabilities(dict(m._PARAMS)))
    except Exception as exc:
        _CACHE["why_caps"] = f"{type(exc).__name__}:{str(exc)[:60]}"
        return {}


def why() -> dict:
    """上一次各道為何回空(空=沒問題)。捕捉到就要顯示(批419e)。"""
    return {k: v for k, v in _CACHE.items() if k.startswith("why_")}


def status() -> dict:
    st = mount()
    rdy, rwhy = ocr_ready()
    return {"module": MODULE_ID, "hub": HUB_NAME, "version": HUB_VERSION,
            "mount": st, "candidates": [d.name for d in roots()],
            "out_root": str(OUT_ROOT), "ocr_ready": rdy, "ocr_why": rwhy,
            "capabilities": capabilities(), "why": why()}


def _print_status() -> int:
    st = mount()
    print(f"=== {MODULE_ID} {HUB_NAME} {HUB_VERSION} · PDFPlumber-Plus 統轄橋 ===")
    print(f"  掛載態  {st['state']}  夾={st['dir_name'] or '-'}  版={st['version'] or '-'}")
    if st["why"]:
        print(f"  因由    {st['why']}")
    print(f"  候選    {len(roots())} 套:{', '.join(d.name for d in roots()) or '-'}")
    print(f"  落地根  {OUT_ROOT}(蓋過收容件硬寫的 Windows VIA_ROOT)")
    if st["state"] == "VERIFIED":
        caps = capabilities()
        keys = ("pdfplumber", "pymupdf", "paddleocr", "numpy", "cv2", "pandas")
        for k in keys:
            v = str(caps.get(k, "?"))
            print(f"    {k:<12} {'缺' if v.startswith('MISSING') else '在'}  {v}")
        rdy, rwhy = ocr_ready()
        print(f"  OCR 車道 {'可跑' if rdy else '不可跑'}{('(' + rwhy + ')') if rwhy else ''}")
    return 0


def selftest() -> int:
    fails, done = [], []

    def chk(name, cond, note=""):
        done.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    st = mount()
    src = Path(__file__).read_text(encoding="utf-8")

    chk("① 收容件掛得上且版本說得出(尾版律;字母序陷阱已避開)",
        st["state"] in ("VERIFIED", "ABSENT"),
        f"(態={st['state']} 夾={st['dir_name'] or '-'} 版={st['version'] or '-'}"
        + (f" 因由={st['why']}" if st["why"] else "") + ")")

    # ② 收容件原地不動:兩面證——(a) 全部服務道跑過一輪後收容件 SHA-256 不變;
    #    (b) 原始碼裡凡提到 INTAKE 的行,一行都沒有寫檔動詞。
    #    (規矩宣告不算證據;要能指著雜湊說「跑完還是同一個位元組」才算。)
    _f746 = (newest() / PKG_MARKER) if newest() else None
    _sha0 = hashlib.sha256(_f746.read_bytes()).hexdigest() if (_f746 and _f746.is_file()) else ""
    _ghost = VIA / "__no_such_file_mdl746__.pdf"
    triage(_ghost); tables(_ghost); page_text(_ghost); ocr_page(_ghost)
    capabilities(); params(); ocr_ready()
    _sha1 = hashlib.sha256(_f746.read_bytes()).hexdigest() if (_f746 and _f746.is_file()) else ""
    _VERBS = ("write", "mkdir", "unlink", "rmtree", "copy", "move", "touch", "rename")
    _bad = [ln.strip()[:60] for ln in src.splitlines()
            if "INTAKE" in ln and any(v in ln for v in _VERBS)]
    chk("② 收容件原地不動——全部服務道跑過一輪後 SHA-256 不變,且提到 INTAKE 的行零寫檔動詞",
        bool(_sha0) and _sha0 == _sha1 and not _bad,
        f"(sha={_sha0[:12]}→{_sha1[:12]} · 可疑行 {len(_bad)})")

    # ③ 硬寫 Windows 根一律蓋掉
    chk("③ 落地根一律由本橋給(收容件 _PARAMS[\"VIA_ROOT\"] 硬寫的 "
        "OneDrive\\VeritasIntelligenceAnalytics 在操作員實機不存在,放它自己決定會寫錯地方)",
        'CFG["out_dir"]' in src or '"out_dir": str(out)' in src,
        f"(本橋落地根={OUT_ROOT.name} 在 VIA_Reports 下,已在 .gitignore)")

    # ④ 缺席時每一道誠實回空
    ghost = VIA / "__no_such_file_mdl746__.pdf"
    t4, g4 = ocr_page(ghost)
    tx4, gx4 = page_text(ghost)
    tri4 = triage(ghost)
    chk("④ 檔不在/件不在時每一道誠實回空並講得出為何(不假抽、不靜默退後備)",
        t4 == "" and tx4 == "" and g4.startswith("PPP_") and gx4.startswith("PPP_")
        and tri4["state"] == "UNKNOWN" and bool(tri4["why"]) and tables(ghost) == [],
        f"(ocr={g4[:46]} · text={gx4[:30]} · 分流={tri4['state']})")

    # ⑤ OCR 就緒與否誠實
    rdy, rwhy = ocr_ready()
    caps = capabilities()
    has_paddle = not str(caps.get("paddleocr", "MISSING")).startswith("MISSING")
    chk("⑤ OCR 車道就緒與否照實說(paddleocr 在位才說可跑;不在位就把缺什麼點名)",
        (rdy is True and has_paddle) or (rdy is False and bool(rwhy)),
        f"(可跑={rdy} 因由={rwhy or '-'})")

    # ⑥ 密度閘真的擋得住浮水印假文字層(**用庫裡的真檔**,不是合成測資)
    real = sorted(VIA.rglob("*.pdf"))
    seen = {}
    for f6 in real:
        t6 = triage(f6)
        seen.setdefault(t6["state"], []).append((f6.name, t6["n_chars"], t6["density"]))
    n_scan = len(seen.get("SCANNED", []))
    n_dig = len(seen.get("DIGITAL", []))
    chk("⑥ 字元密度閘在**真檔**上分得開(ENG072 今天的 `if txt:` 只要一個字就放行,"
        f"那是假綠)——全庫 {len(real)} 件 PDF 掃過一輪",
        len(real) >= 5 and n_scan >= 1 and n_dig >= 5,
        f"(DIGITAL {n_dig} · THIN {len(seen.get('THIN', []))} · SCANNED {n_scan} · "
        f"UNKNOWN {len(seen.get('UNKNOWN', []))})")

    # ⑦ 真檔證出來的假紅:長捲頁不准只憑密度降級
    thin6 = seen.get("THIN", [])
    lo_real = min([c for _, c, _ in seen.get("DIGITAL", [])] or [0])
    chk("⑦ 密度只當訊號不當判決——949×7448 長捲頁那件有 862 字真正文、密度 1.22e-04 "
        f"低於門檻,光看密度會**假紅**;字數 >= {SPARSE_CHARS} 只標 THIN 不降級"
        "(批440 那一課:改嚴一道閘之前要有真檔證據)",
        all(c >= SPARSE_CHARS for _, c, _ in thin6)
        and all(c < SPARSE_CHARS for _, c, _ in seen.get("SCANNED", []))
        and (lo_real == 0 or lo_real > SPARSE_CHARS),
        f"(THIN {len(thin6)} 件:{', '.join(f'{n[:22]}={c}字' for n, c, _ in thin6[:2]) or '-'}"
        f" · 全庫最低真文字首頁 {lo_real} 字 > 界線 {SPARSE_CHARS})")

    # ⑧ 補位不取代:不宣稱比 GLE 的 OCR 新

    chk("⑧ 先查再造把話講回來——GLE v2.1.0 同樣真的建構 PaddleOCR 且**連 3.x 都接**,"
        "本包只接 2.x;所以這條是**補位**不是取代(誰在位誰上)",
        "補位不是取代" in src and "3.x" in src and "all_backend_engines.py" in src, "")

    # ⑨ 紀律宣告在檔
    chk("⑨ 紀律宣告(收容件原地不動/零網路/零彈窗/尾版律/Zero-Hydra/誠實降級留因由 在檔)",
        all(k in src for k in ("收容件原地不動", "零網路", "零彈窗", "尾版律",
                               "Zero-Hydra", "誠實")), "")

    print(f"  [計] 九檢({len(done)} 檢) OK {len(done) - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print(f"=== {MODULE_ID} {HUB_NAME} · 九檢自測(零網路)===")
        return selftest()
    if "--json" in args:
        print(json.dumps(status(), ensure_ascii=False, indent=1, default=str))
        return 0
    if "--triage" in args:
        i = args.index("--triage")
        if i + 1 < len(args):
            print(json.dumps(triage(args[i + 1]), ensure_ascii=False, indent=1))
            return 0
        print("--triage 後面要接一個 .pdf 路徑")
        return 2
    if "--run" in args:
        i = args.index("--run")
        if i + 1 < len(args):
            r = run_full(args[i + 1])
            print(json.dumps({"ok": r.get("ok"), "out_dir": r.get("out_dir"),
                              "errors": r.get("errors")}, ensure_ascii=False, indent=1))
            return 0 if r.get("ok") else 1
        print("--run 後面要接一個 .pdf 路徑")
        return 2
    return _print_status()


if __name__ == "__main__":
    sys.exit(main())
