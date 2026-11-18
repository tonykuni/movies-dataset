# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-ENG020 · VRN_Ocr_v0100 v0100 · ENGINE =====
# AST 注入（只加註解，AST 不變）：類別 0 · 函式 10；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""影像檔的 OCR：找得到引擎就讀，找不到就照實說找不到。

**這一支不做判讀。** 它只把影像變成文字，交給上游去看 —— 所以它不是
PageRegions／TitleTrim 之外的第二套讀法，那兩支照舊判斷「文字層有沒有字」。

為什麼要分三層引擎：操作員的機器與這個容器裝得起來的東西不一樣。
依序試，第一個能用的就用，並且**把用了哪一支寫進結果**，看報告的人才知道那段字是誰讀的：

    pymupdf-tesseract   PyMuPDF 內建，但要系統裝 Tesseract（Windows 常見）
    rapidocr            純 pip，不需要系統二進位檔（容器裡裝得起來）
    pytesseract         Tesseract 的 Python 包裝

**失真的方式每支引擎不一樣**，2026-10-19 在同一張已知圖上實測（selftest 每輪重測）：

    pymupdf-tesseract   數字與拉丁字全中；中文有 chi_tra 語言包時不掉字，
                        但會把一個詞斷成兩行（「目標價」→「目標\n價」）並夾雜雜訊（|]、。）
    rapidocr            數字與拉丁字全中；中文**真的掉字** ——
                        「台積電」→「台電」、「投資評等」→「投資等」

所以不要寫「OCR 中文會掉字」這種通則 —— 那是 rapidocr 的行為。共通的只有一件事：
**OCR 的字不等於文字層的字**。結果一律帶 `source="OCR"` 與 `lossy_cjk=True`，
下游要當成一條比較不可信的讀法，永遠不可以拿它當 VERIFIED 的兩條讀法之一。

兩個踩過的坑，寫下來免得再踩：

1. `page.get_textpage_ocr()` 對**影像檔**要 `full=True`，否則丟
   `RuntimeError: source or target not a PDF`，一個字都讀不到（而且例外被吞掉，看起來像「讀到空的」）。
2. 它的 `language` 預設是 `eng`。對中文頁面不指定語言，讀出來是
   「6MB( 2330 / Simanaeia / HAS」這種垃圾，不是掉字而是整段錯。
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

import importlib.util
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List

ENGINE_VERSION = "v0100"
# 一條讀法一個名字；順序就是優先序，不另外做設定檔（多一個設定檔就多一個會跟程式說不一樣的地方）。
ENGINE_ORDER = ("pymupdf-tesseract", "rapidocr", "pytesseract")
# Tesseract 的中文語言包，依偏好排序。沒有它，中文頁面讀出來是整段錯字而不是掉字。
CJK_PACKS = ("chi_tra", "chi_sim")
_TESS_LANGS: List[str] | None = None


# [VRN-ID] VRN-ENG020-FNC001 · LOGIC
def def_have(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


# [VRN-ID] VRN-ENG020-FNC005 · LOGIC
def def_tess_langs() -> List[str]:
    """系統 Tesseract 裝了哪些語言包（問它自己，不猜 tessdata 目錄）。問一次就記住。"""
    global _TESS_LANGS
    if _TESS_LANGS is not None:
        return _TESS_LANGS
    _TESS_LANGS = []
    exe = shutil.which("tesseract")
    if exe:
        try:
            done = subprocess.run([exe, "--list-langs"], capture_output=True, text=True, timeout=20, check=False)
            _TESS_LANGS = [ln.strip() for ln in (done.stdout or "").splitlines()[1:] if ln.strip()]
        except (OSError, subprocess.SubprocessError):
            _TESS_LANGS = []
    return _TESS_LANGS


# [VRN-ID] VRN-ENG020-FNC006 · LOGIC
def def_cjk_pack() -> str:
    """挑得出來的中文語言包名字；一個都沒有就回空字串。"""
    langs = def_tess_langs()
    return next((p for p in CJK_PACKS if p in langs), "")


# [VRN-ID] VRN-ENG020-FNC007 · LOGIC
def def_tess_lang() -> str:
    """丟給 Tesseract 的 language 字串。有中文包就中文＋英文，沒有就只有英文。"""
    pack = def_cjk_pack()
    return f"{pack}+eng" if pack else "eng"


# [VRN-ID] VRN-ENG020-FNC002 · LOGIC
def available() -> Dict[str, Any]:
    """哪一支 OCR 引擎能用。回 {engine, why, checked, cjk}；都沒有時 engine 是空字串。

    `cjk` 是「這個組合讀不讀得了中文」—— rapidocr 自帶中文；Tesseract 要有 chi_tra／chi_sim
    語言包，沒有的話它會把中文讀成整段錯字，那種結果不該拿去跟已知答案比。
    """
    checked: List[Dict[str, str]] = []
    tess = shutil.which("tesseract")
    pack = def_cjk_pack() if tess else ""
    usable: List[tuple] = []
    for name in ENGINE_ORDER:
        if name == "pymupdf-tesseract":
            ok = bool(tess) and def_have("pymupdf")
            why = (f"PyMuPDF 有、系統 Tesseract 有、中文語言包 {pack}" if pack else
                   "PyMuPDF 有、系統 Tesseract 有，但沒有中文語言包（中文會整段讀錯）") if ok else (
                "系統沒有 tesseract 執行檔" if def_have("pymupdf") else "PyMuPDF 不在")
            cjk = bool(pack)
        elif name == "rapidocr":
            ok = def_have("rapidocr_onnxruntime")
            why = "純 pip 的 ONNX 版，自帶中文" if ok else "沒裝 rapidocr_onnxruntime"
            cjk = True
        else:
            ok = def_have("pytesseract") and bool(tess)
            why = (f"pytesseract 與 Tesseract 都有、中文語言包 {pack}" if pack else
                   "pytesseract 與 Tesseract 都有，但沒有中文語言包") if ok else "pytesseract 或系統 tesseract 不在"
            cjk = bool(pack)
        checked.append({"engine": name, "ok": "是" if ok else "否", "why": why})
        if ok:
            usable.append((name, why, cjk))
    if not usable:
        return {"engine": "", "why": "三支都不在：" + "；".join(f"{c['engine']} {c['why']}" for c in checked),
                "checked": checked, "cjk": False}
    # **讀得了中文的優先**，不照 ENGINE_ORDER 硬排（Codex PR #63 P2）：
    # 這個系統讀的是台股中文報告。沒有中文語言包的 Tesseract 讀中文是整段錯字
    # （「6MB( 2330 / Simanaeia / HAS」），那不是降級，是垃圾。
    # 同一台機器上要是還裝著自帶中文的 rapidocr，挑它才對。
    name, why, cjk = next((u for u in usable if u[2]), usable[0])
    if not cjk:
        why += "；三支能用的都讀不了中文，只好用它"
    elif usable[0][0] != name:
        why += f"；比 {usable[0][0]} 優先，因為那支在這台機器讀不了中文"
    return {"engine": name, "why": why, "checked": checked, "cjk": cjk}


# [VRN-ID] VRN-ENG020-FNC003 · LOGIC
def read(path: str | Path, engine: str = "") -> Dict[str, Any]:
    """影像 → 文字。回 {engine, lines, text, chars, source, lossy_cjk, lang, error}。

    讀不到不丟例外 —— 一張圖讀不出來不該讓整輪倒掉，照實回 error 讓閘門去判。
    """
    out: Dict[str, Any] = {"engine": "", "lines": [], "text": "", "chars": 0,
                           "source": "OCR", "lossy_cjk": True, "lang": "", "error": ""}
    pick = engine or available()["engine"]
    if not pick:
        out["error"] = "沒有可用的 OCR 引擎"
        return out
    out["engine"] = pick
    p = str(Path(path))
    try:
        if pick == "rapidocr":
            from rapidocr_onnxruntime import RapidOCR          # noqa: PLC0415
            out["lang"] = "內建中英"
            res, _elapsed = RapidOCR()(p)
            out["lines"] = [str(r[1]) for r in (res or [])]
        elif pick == "pymupdf-tesseract":
            import pymupdf                                      # noqa: PLC0415
            out["lang"] = def_tess_lang()
            with pymupdf.open(p) as doc:
                for page in doc:
                    # full=True 是必要的：影像檔不給它會丟「source or target not a PDF」，一個字都讀不到。
                    tp = page.get_textpage_ocr(language=out["lang"], full=True)
                    out["lines"] += [ln for ln in tp.extractText().splitlines() if ln.strip()]
        else:
            import pytesseract                                  # noqa: PLC0415
            from PIL import Image                               # noqa: PLC0415
            out["lang"] = def_tess_lang()
            with Image.open(p) as im:
                text = pytesseract.image_to_string(im, lang=out["lang"])
            out["lines"] = [ln for ln in text.splitlines() if ln.strip()]
    except Exception as error:  # noqa: BLE001 - 一張圖讀不出來不該讓整輪倒掉
        out["error"] = f"{error.__class__.__name__}: {error}"[:200]
        return out
    out["text"] = "\n".join(out["lines"])
    out["chars"] = len(out["text"])
    return out


# 已知圖上該讀對的東西。數字與拉丁字是**每支引擎都該全中**的，掉了就是引擎壞了。
KNOWN_LINES = ("台積電(2330 TT) 營運動能延續",
               "投資評等：買進  目標價：NT$1250.0",
               "分析師 王小明  (02)2181-8888")
KNOWN_HARD = ("2330", "1250.0", "2181-8888", "TT")
KNOWN_CJK = ("台積電", "營運動能延續", "投資評等", "買進", "目標價", "分析師", "王小明")


# [VRN-ID] VRN-ENG020-FNC008 · LOGIC
def def_known_image(folder: Path) -> Path:
    """畫一張內容已知的圖給 selftest 用。畫不出來就丟例外，由呼叫端決定怎麼報。"""
    import pymupdf                                              # noqa: PLC0415
    img = folder / "known.png"
    doc = pymupdf.open()
    try:
        page = doc.new_page(width=600, height=220)
        y = 50
        for line in KNOWN_LINES:
            page.insert_text((30, y), line, fontname="china-t", fontsize=20)
            y += 55
        page.get_pixmap(dpi=200).save(str(img))
    finally:
        doc.close()
    return img


# [VRN-ID] VRN-ENG020-FNC009 · LOGIC
def def_checks() -> List[tuple]:
    """已知答案逐條，回 [(名字, 狀態, 細節)]，狀態是 PASS／FAIL／GAP。

    三態而不是兩態，是因為「這台機器驗不到」既不是過也不是壞：
    把它算成 FAIL，lock 就會因為環境條件而紅（Codex #61 那個坑）；
    算成 PASS，又是把沒驗到的東西講成驗過了。所以它自己一個狀態，
    閘門把它畫成 WARN，報告上看得見。

    失真**只量不判**：每支引擎掉字的方式不一樣（rapidocr 掉字、Tesseract 斷行加雜訊），
    把某一種失真寫成「必須發生」，等於要求引擎永遠不要變好 —— 那是另一種假綠燈。
    所以硬性要求的只有兩件：數字與拉丁字全中、中文不能整段讀錯；
    實際掉了什麼，每一輪量出來印在旁邊。
    """
    checks: List[tuple] = []
    av = available()
    # [VRN-ID] VRN-ENG020-FNC010 · VALIDATE
    def verdict(ok: bool) -> str:
        return "PASS" if ok else "FAIL"

    checks.append(("三支引擎都查過、順序固定", verdict([c["engine"] for c in av["checked"]] ==
                   list(ENGINE_ORDER)[:len(av["checked"])]), [c["engine"] for c in av["checked"]]))
    checks.append(("查不到就說查不到，不亂指一支",
                   verdict(bool(av["engine"]) or "三支都不在" in av["why"]), av["why"]))
    none = read(__file__, engine="")
    if not av["engine"]:
        checks.append(("沒有引擎時：回 error、不丟例外",
                       verdict(none["error"] == "沒有可用的 OCR 引擎"), none["error"]))
        # 沒有引擎 ＝ 讀取那一條**根本沒跑**。不記成 GAP 的話，統計那行會寫「沒驗到 0」，
        # 而 lock 收到 rc=0 就把 ocr 當成證過了 —— 那正是這個倉一再踩的
        # 「驗一個沒跑到的東西，等於沒驗」。（Codex PR #63 P2）
        checks.append(("沒有引擎 —— 真的讀一張已知圖那一條完全沒跑", "GAP",
                       "裝 Tesseract＋中文語言包、或 pip install rapidocr_onnxruntime 才驗得到"))
    checks.append(("結果一律標 source=OCR 且 lossy_cjk=True（不可當成文字層）",
                   verdict(none["source"] == "OCR" and none["lossy_cjk"] is True),
                   (none["source"], none["lossy_cjk"])))
    bad = read("/does/not/exist.png")
    checks.append(("讀不到的檔：回 error，不丟例外",
                   verdict(isinstance(bad.get("error"), str)), bad.get("error", "")[:60]))

    if av["engine"]:
        import tempfile                                          # noqa: PLC0415
        got, why = None, ""
        try:
            with tempfile.TemporaryDirectory(prefix="vrn_ocr_") as td:
                got = read(def_known_image(Path(td)))
        except Exception as error:                               # noqa: BLE001
            # 畫圖要 PyMuPDF。裝了 rapidocr 卻沒裝 PyMuPDF 的機器畫不出來 ——
            # 那是「這一條沒驗到」，要說出來，不是讓整輪倒掉。
            why = f"{error.__class__.__name__}: {error}"[:120]
            checks.append(("有引擎但畫不出已知圖 —— 讀取那一條這台機器沒驗到", "GAP",
                           f"{why} · 裝 pymupdf 才畫得出來"))
        if got is not None:
            joined = got["text"].replace(" ", "")
            miss_hard = [k for k in KNOWN_HARD if k.replace(" ", "") not in joined]
            checks.append((f"有引擎（{got['engine']}／{got['lang']}）：數字與拉丁字全讀對",
                           verdict(not miss_hard),
                           f"缺 {miss_hard}" if miss_hard else "2330 · 1250.0 · 2181-8888 · TT"))
            hit = [k for k in KNOWN_CJK if k in joined]
            if av["cjk"]:
                # 不要求全中（會斷行、會掉字），但整段讀錯（像沒給語言包的 Tesseract 讀出 0/7）要紅。
                checks.append(("有引擎：中文讀得出大半（整段錯字才算壞）", verdict(len(hit) >= 4),
                               f"{len(hit)}/{len(KNOWN_CJK)} · 缺 {[k for k in KNOWN_CJK if k not in joined]}"))
                checks.append((f"量到的中文失真（只量不判）：{len(hit)}/{len(KNOWN_CJK)}", "PASS",
                               repr(got["text"][:80])))
            else:
                checks.append(("這台機器的 Tesseract 沒有中文語言包 —— 中文那條沒驗到", "GAP",
                               "裝 chi_tra 才驗得到；現在只驗數字與拉丁字"))

    return checks


# [VRN-ID] VRN-ENG020-FNC004 · ENTRY
def selftest(verbose: bool = True) -> int:
    """印出每一條已知答案，回 0／1。GAP（這台機器驗不到）不算紅 —— 見 def_checks 的理由。"""
    checks = def_checks()
    bad_n = sum(1 for _n, state, _d in checks if state == "FAIL")
    gap_n = sum(1 for _n, state, _d in checks if state == "GAP")
    for name, state, detail in checks:
        if verbose:
            print(f"  [{state}] {name}" + (f" · {detail}" if detail else ""))
    if verbose:
        av = available()
        print(f"[OCR] {ENGINE_VERSION} · 過 {len(checks) - bad_n - gap_n}／紅 {bad_n}／沒驗到 {gap_n}"
              f" · 共 {len(checks)} · 引擎 {av['engine'] or '（都不在）'}")
    return 1 if bad_n else 0


if __name__ == "__main__":
    import sys
    raise SystemExit(selftest(verbose="--quiet" not in sys.argv))
