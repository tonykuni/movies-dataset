#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN2_NonStockSummarizer v0101 — 薄尾(v0100 一字不動):非個股車道改用操作員正式核心 NON_STOCK_CORE_v0400,不再用暫代核心

操作員 2026-11-22:上傳 NON_STOCK_CORE_v0400.zip(SHA-256 918d74d5…)+「整合去重 · 整合成功後刪除」+「授權照最佳決定處理」。
需求冊 VCGC-REQ195 / VRN-REQ018 等的就是這一支:v0310 摘要器的硬閘要 internal/NON_STOCK_CORE_v0200.py,倉內一直沒有,
v0100 只好用 VRN 自建的暫代核心 VRN2_NonStockCore_v0100(每列標「暫代」)。v0400 是 v0200 的相容新版(v0310 要的 16 個名稱全有)。

本版(v0100 · v0310 · v0400 檔都一字不動;只在執行期換):
  ① 核心:functional modules/VRN/nonstock_core_v0400/NON_STOCK_CORE_v0400.py(操作員原件,逐位元入倉;SHA 照 RELEASE_MANIFEST,算前統一 LF)。
     執行期把 v0310 的 BUNDLED_CORE 那一行指向 v0400(與 v0100 暫代模式同一個換法)→ 模式 ORIGINAL · 核心 NON_STOCK_CORE_v0400,矩陣「核心」欄 = 原件。
     v0400 不在 → 照實報錯(不退回暫代核心:刪暫代核心前要證明本版完全不碰它)。
  ② 讀檔 + 路由:v0400 只讀 pdf / txt / html / docx / enex / json 區塊;VRN 自己的讀檔層(圖片 OCR · 影像 PDF · .eml · Office · LINE 訊息 ·
     新聞路由)搬到 VRN2_NonStockReaders(自暫代核心逐字搬出),綁到 v0400 後掛上 v0400 的 def_extract_input / def_profile_router /
     def_parse_messenger_blocks → 讀得到的格式只增不減。宣告式抽句 · 故事 · 方向 · 期間 · 證據一律用 v0400。
  ③ 報告類型標籤照舊(下游 VRN2_ReportRows 不用改):v0400 的 INDUSTRY_OUTLOOK / MESSENGER_INTELLIGENCE / EVERNOTE_INTELLIGENCE
     → INDUSTRY_REPORT / MESSENGER / EVERNOTE;新聞照舊 NEWS(子類型)。NLP_ENGINE 欄標 NON_STOCK_CORE_v0400(不再寫 v0200)。
  ④ doctor 用掛好讀檔層的 v0400 報讀取器 / OCR 車道 / 支援格式。
  ⑤ 自測含「拿掉暫代核心的副本」演練(CLAUDE.md「刪舊版先證明」):沙盒裡沒有 VRN2_NonStockCore_v0100.py,本版自測 + doctor 照樣過。
暫代核心檔本版不刪:VCGC 盤點冊 C-vrn2-nonstock-core-v0100 / C-vrn2-nonstock-summarizer-v0100 兩站與交接冊的已鎖成功還指著它,
  刪了那兩站會紅(成功只增不減);等 VCGC 自己把兩站換成本版再刪。
邊界:只讀輸入檔;只寫 --out 夾;零網路(v0400 NETWORK_ALLOWED=False · OCR 只借鎖冊路徑);不用 TA-Lib;不 import VCGC。
用法同 v0100:python VRN2_NonStockSummarizer_v0101.py run <檔或夾…> [--out D] [--all] · doctor · --selftest
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "v0101"
ENGINE = "VRN2_NonStockSummarizer " + VERSION
HERE = Path(__file__).resolve().parent
FAMILY = "VRN2_NonStockSummarizer"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0101", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

CORE_DIR = HERE / "nonstock_core_v0400"
CORE_FILE = CORE_DIR / "NON_STOCK_CORE_v0400.py"
CORE_SHA = "b85c58ef669336bb1a9af86614374af99f9a0b8ce640b9f5270278b8b2003ad4"    # RELEASE_MANIFEST.json(操作員 v0400 包)
STANDIN_NAME = "VRN2_NonStockCore_v0100.py"
SANDBOX_ENV = "VRN2_NS_PROOF_SANDBOX"
NLP_LABEL = "VRN_M07_EXTRACTIVE+NON_STOCK_CORE_v0400"
REUSE_CANON = ("VRN_MDL003_TableRestorer.py",)               # nonstock_v0310/reuse/vrn2 轉接殼載入的本系統正本
KNOWN_DIFF = {"⑤": "主題由 v0400 的故事權重判(散熱樣本判 AI Infrastructure;路由 INDUSTRY_REPORT 不變)"}


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _sha_lf(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest() if p.is_file() else ""


def readers_path() -> Path | None:
    hits = sorted(HERE.glob("VRN2_NonStockReaders_v*.py"), key=_vnum)
    return hits[-1] if hits else None


# ── ① 核心狀態 / 載入 ───────────────────────────────────────────────────────
def core_state() -> dict:
    rp = readers_path()
    if not CORE_FILE.is_file():
        return {"mode": "ABSENT", "core": "NON_STOCK_CORE_v0400", "path": str(CORE_FILE), "sha_match": None,
                "why": "缺 nonstock_core_v0400/NON_STOCK_CORE_v0400.py · 本版不退回暫代核心", "readers": rp.name if rp else None}
    sha = _sha_lf(CORE_FILE)
    return {"mode": "ORIGINAL", "core": "NON_STOCK_CORE_v0400", "path": str(CORE_FILE), "sha_match": sha == CORE_SHA,
            "why": "操作員原件 v0400(取代 v0200 / 暫代核心)" + ("" if sha == CORE_SHA else "(SHA 與 RELEASE_MANIFEST 不同 · 照實記)"),
            "readers": rp.name if rp else None}


_ENGINE_CACHE: dict = {}
_LABELS: dict = {}


def load_engine():
    """回 (v0310 模組, core_state)。v0310 / v0400 檔不動:執行期把 BUNDLED_CORE 指向 v0400,再把 VRN 讀檔層綁上 v0400。"""
    if "e" in _ENGINE_CACHE:
        return _ENGINE_CACHE["e"], _ENGINE_CACHE["st"]
    st = core_state()
    if st["mode"] != "ORIGINAL":
        raise RuntimeError(st["why"])
    rp = readers_path()
    if rp is None:
        raise RuntimeError("缺 VRN2_NonStockReaders_v*.py(VRN 讀檔層)")
    st["engine_sha_match"] = PRIOR._sha(PRIOR.NS_ENGINE) == PRIOR.NS_ENGINE_SHA
    src = PRIOR.NS_ENGINE.read_text(encoding="utf-8")
    if src.count(PRIOR.CORE_LINE) != 1:
        raise RuntimeError("v0310 的 BUNDLED_CORE 行對不上(檔被換過?)→ 不硬套")
    src = src.replace(PRIOR.CORE_LINE, "BUNDLED_CORE = Path(%r)" % str(CORE_FILE), 1)
    spec = importlib.util.spec_from_loader("vrn2_nonstock_v0310_core_v0400", loader=None, origin=str(PRIOR.NS_ENGINE))
    eng = importlib.util.module_from_spec(spec)
    eng.__file__ = str(PRIOR.NS_ENGINE)                         # ROOT = nonstock_v0310(reuse/vrn2 照原路徑找)
    sys.modules[spec.name] = eng
    exec(compile(src, str(PRIOR.NS_ENGINE), "exec"), eng.__dict__)  # noqa: S102 — 倉內 SHA 釘住的 v0310 原檔
    core = eng.CORE
    rd = PRIOR._load("vrn2_nonstock_readers_for_v0101", rp)
    st["bind"] = rd.bind(core)
    for name in ("def_extract_input", "def_profile_router", "def_parse_messenger_blocks", "ALL_EXT", "FORMAT_OF", "ReaderUnavailable", "_ocr_module"):
        setattr(core, name, getattr(rd, name))                  # 只改這一次載入的模組物件,不寫檔
    st["readers"] = rp.name
    _LABELS.clear()
    _LABELS.update({core.PROFILE_INDUSTRY: "INDUSTRY_REPORT", core.PROFILE_MESSENGER: "MESSENGER", core.PROFILE_EVERNOTE: "EVERNOTE"})
    _ENGINE_CACHE.update(e=eng, st=st)
    return eng, st


# ── ③ 報告類型標籤照舊 · NLP_ENGINE 標 v0400 ─────────────────────────────────
_ANALYZE_V0100 = PRIOR.analyze


def analyze(eng, path: Path) -> dict:
    res = _ANALYZE_V0100(eng, path)
    rep = res.get("report")
    if rep:
        rep["REPORT_TYPE"] = _LABELS.get(rep.get("REPORT_TYPE"), rep.get("REPORT_TYPE"))
        rep["NLP_ENGINE"] = NLP_LABEL
    return res


# ── ④ doctor:用掛好讀檔層的 v0400 ─────────────────────────────────────────────
_DOCTOR_V0100 = PRIOR.doctor


def doctor() -> dict:
    eng, st = load_engine()
    real = PRIOR._load
    PRIOR._load = lambda name, path: eng.CORE if name == "vrn2_nonstock_core_doctor" else real(name, path)
    try:
        d = _DOCTOR_V0100()
    finally:
        PRIOR._load = real
    d["engine"], d["core"] = ENGINE, st
    d["core_sha_match"] = st["sha_match"]
    return d


def _install() -> None:
    """把本版的 core_state / load_engine / analyze / doctor / ENGINE 換進 v0100 的模組(run / write_all / render_html 照 v0100)。"""
    PRIOR.core_state, PRIOR.load_engine, PRIOR.analyze, PRIOR.doctor, PRIOR.ENGINE = core_state, load_engine, analyze, doctor, ENGINE


_install()


def run(inputs: list, out: Path, include_stock: bool = False) -> dict:
    return PRIOR.run(inputs, out, include_stock)


def _capture(fn, *a):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*a)
    return rc, buf.getvalue()


# ── ⑤ 刪暫代核心前的證明:拿掉它的副本照樣跑 ───────────────────────────────────
def proof_without_standin() -> dict:
    """沙盒 = 本系統夾裡非個股車道真正要的檔(沒有暫代核心)→ 子行程跑本版 --selftest 與 doctor。回 {rc_selftest, rc_doctor, files, tail}。"""
    lane = PRIOR.LANE_FILE
    m = re.search(r'^CLASSIFIER_SRC\s*=\s*"([^"]+)"', lane.read_text(encoding="utf-8"), re.M) if lane.is_file() else None
    files = [PRIOR_PATH, Path(__file__), readers_path(), lane] + ([HERE / m.group(1)] if m and (HERE / m.group(1)).is_file() else [])
    files += [p for p in (HERE / n for n in REUSE_CANON) if p.is_file()]        # v0310 reuse/vrn2 轉接殼要的本系統正本
    with tempfile.TemporaryDirectory(prefix="vrn2_ns_proof_") as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        vrn = via / "functional modules" / "VRN"
        vrn.mkdir(parents=True)
        sup = HERE.parents[1] / "supportive modules"
        if sup.is_dir():                                        # 支援工具(版面 / NLP / 加速器 / 鎖冊)只讀借用;VRN 夾是挑檔複製、沒有暫代核心
            (via / "supportive modules").symlink_to(sup, target_is_directory=True)
        for f in files:
            shutil.copy2(f, vrn / f.name)
        for d in (PRIOR.NS_DIR, CORE_DIR):
            shutil.copytree(d, vrn / d.name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "output"))
        env = dict(os.environ, **{SANDBOX_ENV: "1", "PYTHONDONTWRITEBYTECODE": "1"})
        me = vrn / Path(__file__).name
        r1 = subprocess.run([sys.executable, "-B", str(me), "--selftest"], capture_output=True, text=True, env=env, timeout=900, cwd=td)
        r2 = subprocess.run([sys.executable, "-B", str(me), "doctor"], capture_output=True, text=True, env=env, timeout=300, cwd=td)
        present = (vrn / STANDIN_NAME).exists()
    return {"rc_selftest": r1.returncode, "rc_doctor": r2.returncode, "standin_in_sandbox": present,
            "files": sorted(f.name for f in files) + [PRIOR.NS_DIR.name + "/", CORE_DIR.name + "/"],
            "tail": (r1.stdout + r1.stderr)[-600:], "doctor_tail": (r2.stdout + r2.stderr)[-300:]}


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("=== %s 自測(v0100 / v0310 / v0400 不改 · 核心 v0400 + VRN 讀檔層 · 零網路)===" % ENGINE, flush=True)
    st = core_state()
    chk("⓪ v0400 原件在 · SHA(統一 LF)= RELEASE_MANIFEST", st["mode"] == "ORIGINAL" and st["sha_match"] is True, st["why"])
    chk("⓪b VRN 讀檔層在(%s)" % st.get("readers"), readers_path() is not None)
    rc0, out0 = _capture(PRIOR.selftest)
    fails = [ln.strip() for ln in out0.splitlines() if ln.strip().startswith("[FAIL]") and "selftest ·" not in ln]
    unexpected = [ln for ln in fails if not any(ln.startswith("[FAIL] " + k) for k in KNOWN_DIFF)]
    known = [ln for ln in fails if ln not in unexpected]
    for ln in known:
        print("    [INFO] 預期差異(核心換成 v0400):%s → %s" % (ln[:160], KNOWN_DIFF[ln.split()[1][:1]]), flush=True)
    chk("① v0100 的 18 檢在 v0400 核心上:除已登記的預期差異外全過(%d 項預期差異)" % len(known), not unexpected and len(fails) <= len(KNOWN_DIFF),
        unexpected or out0[-300:])
    m5 = re.search(r"\[(?:OK|FAIL)\] ⑤[^\n]*?\('([^']*)', '([^']*)'\)", out0) or re.search(r"\[OK\] ⑤", out0)
    chk("①b 預期差異只在主題:產業報告路由仍是 INDUSTRY_REPORT · 主題非空",
        bool(m5) and (m5.lastindex is None or (m5.group(1) == "INDUSTRY_REPORT" and bool(m5.group(2)))), m5.groups() if m5 and m5.lastindex else m5)
    eng, st = load_engine()
    chk("② 引擎的 CORE 是 v0400(不是暫代核心)· 讀檔層已掛上",
        Path(getattr(eng.CORE, "__file__", "")).name == CORE_FILE.name and getattr(eng.CORE.def_extract_input, "__module__", "") == "vrn2_nonstock_readers_for_v0101",
        (getattr(eng.CORE, "__file__", ""), getattr(eng.CORE.def_extract_input, "__module__", "")))
    loaded = [n for n, m in list(sys.modules.items()) if Path(str(getattr(m, "__file__", "") or "")).name == STANDIN_NAME]
    chk("③ 全程沒有載入暫代核心 %s" % STANDIN_NAME, not loaded, loaded)
    with tempfile.TemporaryDirectory(prefix="vrn2_ns101_") as td:
        d = Path(td) / "in"
        d.mkdir()
        (d / "產業專題_記憶體.txt").write_text("記憶體產業專題\n\n結論:HBM 供給吃緊,推升 DRAM 報價上漲 15%。\n\n"
                                         "由於 AI 伺服器需求成長,南亞科(2408)2026年獲利可望轉佳。\n\n若終端需求不如預期,下半年報價可能回落。", encoding="utf-8")
        out = Path(td) / "out"
        run([str(d)], out)
        res = json.loads((out / "RESULTS.json").read_text(encoding="utf-8"))
        rs = res.get("report_summary") or [{}]
        mx0 = (json.loads((out / "NONSTOCK_MATRIX.json").read_text(encoding="utf-8")).get("matrix") or [{}])[0]
    chk("④ 報告類型 / 格式標籤照舊(INDUSTRY_REPORT · TEXT)· NLP_ENGINE 標 v0400", rs[0].get("REPORT_TYPE") == "INDUSTRY_REPORT" and rs[0].get("NLP_ENGINE") == NLP_LABEL
        and mx0.get("FORMAT") == "TEXT", (rs[0].get("REPORT_TYPE"), rs[0].get("NLP_ENGINE"), mx0.get("FORMAT")))
    doc = doctor()
    chk("⑤ doctor:核心 v0400 · 支援格式含圖片 / 郵件 / Office(讀檔層)", doc["core"]["core"] == "NON_STOCK_CORE_v0400"
        and {".png", ".eml", ".doc", ".pdf", ".docx"} <= set(doc.get("formats", [])), (doc["core"].get("core"), doc.get("formats")))
    if os.environ.get(SANDBOX_ENV) == "1":
        print("  [GRAY] ⑥ 沙盒裡的子行程:不再巢狀演練", flush=True)
    else:
        pr = proof_without_standin()
        chk("⑥ 刪舊版先證明:拿掉暫代核心的副本裡,本版 --selftest 與 doctor 都 rc 0", pr["rc_selftest"] == 0 and pr["rc_doctor"] == 0 and not pr["standin_in_sandbox"],
            {k: pr[k] for k in ("rc_selftest", "rc_doctor", "standin_in_sandbox", "tail")})
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑦ 零網路 · 不用 TA-Lib · 不 import VCGC · 加速器橋在 · 程式碼不載入暫代核心",
        not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib|socket|http|CGC_)", body, re.M) and "[VIA:ACCEL-BRIDGE:v0100]" in src
        and not re.search(r"_load\([^)]*STANDIN", body))
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑧ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), "%d 支" % len(pub))
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", ENGINE, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[:1] in (["selftest"], ["--selftest"]) or "--selftest" in a:
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    sys.exit(main())
