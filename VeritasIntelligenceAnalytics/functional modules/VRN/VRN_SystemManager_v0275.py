#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VRN-2 SystemManager v0275 — 薄尾:HTML U/I 顯示名「VRN」(引擎矩陣頁);檔名 · 資料照舊是 VRN-2。

操作員令(2026-11-14):「Yes add difference to VRN-2 … VRN only exist in html ui」。
VRN-1 補 VRN-2 的差異走 VRN2_PeerBridge(v0102 整合冊 · 借用釘指紋 · 不複製檔);「VRN」這個統一名稱只出現在 HTML U/I。
本版(前版 v0274 一字不動;只換前版鏈上 em_html 一個名字 + 矩陣標頭記本版):
  · 引擎矩陣頁(VIA_Reports/vrn/engine_matrix/VRN_EngineMatrix_latest.html)看得到的文字 VRN-2 → VRN
    (<title> · <h1> · 內文);標籤屬性 · <script> · <style> · VRN-2_ 識別字 · VRN-1 不動。
  · JSON / CSV 登記冊的 system 欄、檔名、路徑照舊 VRN-2(資料不改名;四系統分開命名 L123 照守)。
平行 extract · 引擎矩陣 · 作業系統檔案鎖其餘行為照前版。零網路 · 不碰 TA-Lib · 不讀寫同意閘。號:前版 v0274(main);本版 v0275。
用法同前版;自測 python VRN_SystemManager_v0275.py --selftest(本版 + 前版 v0274)。
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
import contextlib
import importlib.util
import os
import re
import sys
import tempfile
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[1]
import json

TAG = "v0275"
DISPLAY_NAME = "VRN-2 SystemManager"
FAMILY = "VRN_SystemManager"
EM_TAG = DISPLAY_NAME + " " + TAG


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load(path: Path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
PRIOR = _load(PRIOR_PATH, "vrn_manager_prior_for_" + TAG)


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    return getattr(PRIOR, name)


def _owner(name: str):
    m, seen = PRIOR, []
    while m is not None and m not in seen:
        if name in vars(m):
            return m
        seen.append(m)
        m = vars(m).get("PRIOR")
    return None


EM_CFG, EM_STATE = PRIOR.EM_CFG, PRIOR.EM_STATE
HTML_OWNER = _owner("em_html")                                 # 引擎矩陣頁在前版鏈哪一版畫(v0272);它的 em_write 從自己模組上找 em_html


# ────────────────── HTML U/I 顯示名(操作員 2026-11-14:「VRN only exist in html ui」)──────────────────
# 只換「看得到的文字」:<title> / 標題 / 內文裡的 VRN-2 → VRN。標籤屬性(href / src / class / data-*)· <script> · <style> 不動;
# 後面接英數或底線的(VRN-2_xxx 這種識別字 / 檔名)不動;VRN-1 不動。檔名 · 路徑 · JSON / CSV 資料照舊是 VRN-2。
_UI_SPLIT = re.compile(r"(<script\b.*?</script\s*>|<style\b.*?</style\s*>|<!--.*?-->|<[^>]*>)", re.S | re.I)
_UI_NAME = re.compile(r"VRN-2(?![\w-])")


def vrn_ui_label(html: str) -> str:
    parts = _UI_SPLIT.split(html)
    for i in range(0, len(parts), 2):                     # 偶數段 = 標籤之間的文字
        parts[i] = _UI_NAME.sub("VRN", parts[i])
    return "".join(parts)


def ui_label_selftest(chk) -> None:
    src = ("<html><head><title>VRN-2 引擎矩陣</title><style>.x{content:'VRN-2'}</style></head><body>"
           "<h1 class='VRN-2'>VRN-2 引擎矩陣 · VRN-2 SystemManager v0274</h1><a href='VRN-2_x.html' data-k=\"VRN-2\">VRN-2 報告</a>"
           "<p>VRN-2_EngineMatrix_latest.json · VRN-1 借用 · VRN-2-alpha</p><script>var s='VRN-2';</script><!-- VRN-2 --></body></html>")
    out = vrn_ui_label(src)
    chk("U1 顯示名:<title> / <h1> / 連結文字的 VRN-2 → VRN",
        "<title>VRN 引擎矩陣</title>" in out and ">VRN 引擎矩陣 · VRN SystemManager v0274</h1>" in out and ">VRN 報告</a>" in out, out[:300])
    chk("U2 不動:標籤屬性 · <style> · <script> · 註解 · VRN-2_ 識別字 · VRN-1 · VRN-2-alpha",
        "class='VRN-2'" in out and "href='VRN-2_x.html'" in out and 'data-k="VRN-2"' in out and "content:'VRN-2'" in out
        and "var s='VRN-2'" in out and "<!-- VRN-2 -->" in out and "VRN-2_EngineMatrix_latest.json" in out and "VRN-1 借用" in out
        and "VRN-2-alpha" in out, out)
    chk("U3 冪等:再套一次不變 · 沒有 VRN-2 的頁原樣", vrn_ui_label(out) == out and vrn_ui_label("<p>VDF</p>") == "<p>VDF</p>")


def em_html(body: dict) -> str:
    return vrn_ui_label(_ORIG["em_html"](body))


_ORIG = {}


def install() -> None:
    """把顯示名掛上前版鏈(冪等):換前版鏈上畫矩陣頁的 em_html;矩陣標頭記本版。"""
    if _ORIG:
        return
    PRIOR.install()                                            # 前版(作業系統檔案鎖)先掛好
    _ORIG.update(em_html=HTML_OWNER.em_html, manager=EM_CFG["manager"])
    HTML_OWNER.em_html = em_html
    EM_CFG["manager"] = EM_TAG


def uninstall() -> None:
    if not _ORIG:
        return
    HTML_OWNER.em_html = _ORIG["em_html"]
    EM_CFG["manager"] = _ORIG["manager"]
    _ORIG.clear()


install()


# ────────────────── 動詞 ──────────────────
def collect() -> dict:
    """VCGC 子系統對接口(照前版 · 只讀)· served_by 記本版。"""
    out = PRIOR.collect()
    if isinstance(out, dict):
        out = dict(out)
        sb = dict(out.get("served_by") or {})
        sb["tail"] = FAMILY + "_" + TAG
        out["served_by"] = sb
    return out


def provenance(args: list) -> int:
    """同前版:直送 ENG114 尾版;`--selftest` 之後再跑本版自測,回傳碼取大。"""
    h = PRIOR.host()
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    rc = int(h._load_engine(h.provenance_engine_path()).main(list(args)) or 0)
    if "--selftest" in args:
        print("  ── 來源回歸之後:本版管理器自測 ──", flush=True)
        rc = max(rc, int(selftest() or 0))
    return rc


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["provenance"]:
        return provenance(args[1:])
    if args == ["--selftest"] or "--selftest" in args[:1]:
        return selftest()
    return PRIOR.main(args)                                       # engine-matrix / 自動登記 / extract … 照前版,矩陣頁顯示名走本版


def selftest() -> int:
    print("[計] %s %s 自測開始(本版 7 項 · 再前版 %s)" % (DISPLAY_NAME, TAG, PRIOR_PATH.name), flush=True)
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)
    install()
    chk("D0 換裝在位:前版鏈畫矩陣頁的 em_html 是本版 · 矩陣標頭記本版 · 前版作業系統檔案鎖仍在",
        HTML_OWNER is not None and HTML_OWNER.em_html is em_html and EM_CFG["manager"] == EM_TAG and PRIOR.PRIOR.em_locked is PRIOR.em_locked)
    ui_label_selftest(chk)
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        own = root / EM_CFG["dir"]
        own.mkdir(parents=True)
        (own / (EM_CFG["prefixes"][0] + "ENG951_Label_v0100.py")).write_text("x = 1\n", encoding="utf-8")
        import contextlib as _cl
        import io as _io
        with _cl.redirect_stdout(_io.StringIO()):
            rc = PRIOR.em_cmd(["--no-git"], root)
        od = PRIOR.em_out_dir(root)
        stem = EM_CFG.get("stem", EM_CFG["system"])
        page = (od / ("%s_EngineMatrix_latest.html" % stem)).read_text(encoding="utf-8")
        data = json.loads((od / ("%s_EngineMatrix_latest.json" % stem)).read_text(encoding="utf-8"))
        csv_txt = (od / ("%s_EngineMatrix_latest.csv" % stem)).read_text(encoding="utf-8-sig")
    vis = PRIOR.re.sub(r"<[^>]*>", " ", page) if hasattr(PRIOR, "re") else re.sub(r"<[^>]*>", " ", page)
    rows = data.get("rows") or {}
    chk("D1 實跑 engine-matrix(暫存夾):頁面看得到的字只有 VRN、沒有 VRN-2 · 標題「VRN 引擎矩陣 · VRN SystemManager %s」" % TAG,
        rc in (0, 2) and "VRN-2" not in re.sub(r"<style\b.*?</style>", "", vis, flags=re.S) and ("VRN SystemManager " + TAG) in page and "VRN 引擎矩陣" in page, page[:400])
    chk("D2 資料照舊:JSON 每列 system = VRN-2 · CSV 照寫 · 檔名 VRN_EngineMatrix_latest.*",
        rows and all(r.get("system") == "VRN-2" for r in rows.values()) and "VRN-2" in csv_txt, (list(rows.values())[:1], csv_txt[:120]))
    text = Path(__file__).read_text(encoding="utf-8")
    chk("D3 檔面:def main / def selftest / def collect · 第 3 行加速器標記 · __main__ provenance 守門在 --selftest 之前 · VIA_FROM_VCGC · 零 TA-Lib · 不寫同意閘",
        "\ndef main(" in text and "\ndef selftest(" in text and "\ndef collect(" in text and text.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]"
        and text.index('sys.argv[1:2] == ["provenance"]') < text.index('"--selftest" in sys.argv:') and "VIA_FROM_VCGC" in text
        and "import " + "talib" not in text and "environ[\"VIA_NET" + "_CONSENT\"] =" not in text)
    print("  ── 前版 %s 自測(本版換裝卸下,照前版原行為)──" % PRIOR_PATH.name, flush=True)
    uninstall()
    try:
        prior_rc = int(PRIOR.selftest() or 0)
    finally:
        install()
    chk("D4 前版 %s 自測照過 · 跑完本版又換上" % PRIOR_PATH.name, prior_rc == 0 and HTML_OWNER.em_html is em_html, prior_rc)
    n = sum(ok)
    print("[計] %s %s(%s_%s.py)自測 %d/%d · %s" % (DISPLAY_NAME, TAG, FAMILY, TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["provenance"]:     # 同前版:provenance 先於任何 --selftest 攔截
        sys.exit(provenance(sys.argv[2:]))
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main(sys.argv[1:]))
