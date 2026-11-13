#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0165 — 薄尾:VDF 操作頁多一個「擷取矩陣」頁籤(預設打開)+ fetchmatrix 動詞 + VDF 頁一律套 VRN-2 視覺規格(鎖)

操作員令(2026-11-01):「參考這種方式有架構地呈現擷取項目於 HTML U/I」。
本版(其餘全照 v0164;並行 engine launch · fetch 不補套 · Windows 自測接點照舊):
  ① ui 動詞跑完:先經 VDF_ENG236_FetchMatrixUI 尾版產 VIA_Reports/vdf/FETCH_MATRIX_latest.{html,json}(庫況讀同夾 DB_CHECK_latest.json ——
     ActivateVDF 一輪裡 ui 在 db check 之後,所以燈是這一輪的),再把 VDF_UI_latest.html 的右側頁籤補一個「擷取矩陣」(iframe 指同夾那一頁)
     並設為預設打開;已經有就換新不疊(冪等)。ENG236 不在 / 產頁失敗 → 頁籤照補、頁內寫說明(不留白頁),燈黃照實。
  ② fetchmatrix 動詞:只產擷取矩陣(不跑整個 ui);印一行總結。
  ④ export · tables 動詞(操作員令「使用者可透過系統進入資料庫擷取所需範圍內特定資料 · 轉換格式儲存在雲端硬碟」):
     轉給 VDF_ENG237_DataExport 尾版(唯讀附掛 · 期間 / 代號 / 欄位 · csv / parquet / json / xlsx / md · onedrive / gdrive / 夾)。
  ③ 操作員令(2026-11-01)「U/I 同 VRN-2 HTML U/I 相同視覺規格鎖死」:ui 跑完,VIA_Reports/vdf 底下每一頁 *_latest.html 經 ENG236.apply_spec
     套 VDF_UI_VisualSpec_SSOT(= VRN-2 vrn2-professional-v0242 鎖定原文)+ VDF 色票對照;鎖對不上就不套(照實黃)。冪等。
不匯入他系統程式;零網路;同意閘不讀不寫;不碰 TA-Lib。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本檔零網路。"""
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

import html as _html
import importlib.util
import os
import re
import sys
import types
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_SystemManager"
TAG = "v" + Path(__file__).stem.rsplit("_v", 1)[-1]
FM_GLOB_V0165 = "VDF_ENG236_FetchMatrixUI_v*.py"
EX_GLOB_V0165 = "VDF_ENG237_DataExport_v*.py"
FM_PAGE_V0165 = "FETCH_MATRIX_latest.html"
TAB_LABEL_V0165 = "擷取矩陣"
TAB_MARK_V0165 = 'data-via-v0165="fetchmatrix"'


def _vnum_v0165(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0165(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            warnings.simplefilter("ignore", DeprecationWarning)
            spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0165(p) < _vnum_v0165(__file__)), key=_vnum_v0165)
PRIOR = _load_v0165(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def fm_module():
    """VDF_ENG236_FetchMatrixUI 尾版(engine/ 底下;不在 → None)。"""
    hits = [p for p in (HERE / "engine").glob(FM_GLOB_V0165) if _vnum_v0165(p) >= 0]
    if not hits:
        return None
    p = max(hits, key=_vnum_v0165)
    return _load_v0165(p, "_vdf_sm_fm_" + p.stem)


def ex_module():
    """VDF_ENG237_DataExport 尾版(engine/;不在 → None)。"""
    hits = [p for p in (HERE / "engine").glob(EX_GLOB_V0165) if _vnum_v0165(p) >= 0]
    if not hits:
        return None
    p = max(hits, key=_vnum_v0165)
    return _load_v0165(p, "_vdf_sm_ex_" + p.stem)


def build_matrix(out: Path | None = None, db_check: Path | None = None) -> dict:
    out = Path(out or PRIOR._out_dir())
    fm = fm_module()
    if fm is None:
        return {"lamp": "YELLOW", "line": "[擷取矩陣] YELLOW · %s 不在(engine/)" % FM_GLOB_V0165, "html": None}
    try:
        r = fm.build(out=out, db_check=db_check or (out / "DB_CHECK_latest.json"))
    except Exception as exc:  # noqa: BLE001 — 產頁失敗不擋 ui(照實黃)
        return {"lamp": "YELLOW", "line": "[擷取矩陣] YELLOW · 產頁失敗 %s: %s" % (type(exc).__name__, str(exc)[:120]), "html": None}
    return r


def inject_tab(page: Path, note: str | None = None) -> str:
    """VDF 操作頁補「擷取矩陣」頁籤(放最後 · 預設打開);已有就換新。回 inserted / replaced / same / missing / no-tabs。"""
    page = Path(page)
    if not page.is_file():
        return "missing"
    h = page.read_text(encoding="utf-8")
    base = re.sub(r'<button[^>]*%s[^>]*>.*?</button>' % re.escape(TAB_MARK_V0165), "", h, flags=re.S)
    base = re.sub(r'<div class="page[^"]*" %s>.*?</iframe></div>' % re.escape(TAB_MARK_V0165), "", base, flags=re.S)
    mt = re.search(r'<div class="tabs">(.*?)</div>', base, re.S)
    mp = re.search(r'<div class="pages">', base)
    if not mt or not mp:
        return "no-tabs"
    n = len(re.findall(r'<button\b', mt.group(1)))
    pages_end = base.find("</main>", mp.end())
    close = base.rfind("</div>", mp.end(), pages_end) if pages_end > 0 else -1
    if close < 0:
        return "no-tabs"
    src_attr = ('src="%s"' % FM_PAGE_V0165) if (page.parent / FM_PAGE_V0165).is_file() else ('src="" srcdoc="%s"' % _html.escape(
        "<!doctype html><meta charset=utf-8><body style='font:13px system-ui;margin:24px'><b>擷取矩陣還沒產生</b><p>%s</p><p>產生它:"
        "<code>python VDF_SystemManager_%s.py fetchmatrix</code></p>" % (_html.escape(note or ""), TAG), quote=True))
    btn = '<button class="on" %s onclick="tab(%d,this)">%s</button>' % (TAB_MARK_V0165, n, TAB_LABEL_V0165)
    pg = '<div class="page on" %s><iframe id="f_fm" %s></iframe></div>' % (TAB_MARK_V0165, src_attr)
    if close <= mt.end():
        return "no-tabs"
    tabs_html = mt.group(1).replace('<button class="on"', '<button')
    mid = base[mt.end(1):close].replace('<div class="page on">', '<div class="page">')
    new = base[:mt.start(1)] + tabs_html + btn + mid + pg + base[close:]
    if new == h:
        return "same"
    page.write_text(new, encoding="utf-8")
    return "replaced" if TAB_MARK_V0165 in h else "inserted"


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] in (["export"], ["tables"]):
        ex = ex_module()
        if ex is None:
            print("[VDF 取資料] RED · %s 不在(engine/)" % EX_GLOB_V0165)
            return 1
        return ex.main(args)
    if args[:1] == ["fetchmatrix"]:
        r = build_matrix()
        print(r["line"])
        return 0 if r.get("html") else 2
    rc = PRIOR.main(args)
    if args[:1] == ["ui"]:
        r = build_matrix()
        how = inject_tab(PRIOR._out_dir() / "VDF_UI_latest.html", r["line"])
        print(r["line"])
        sp = apply_spec_all(PRIOR._out_dir())
        print("[計] VDF ui %s · 擷取矩陣頁籤 %s · VRN-2 視覺規格 %s · %s" % (TAG, how, sp["line"],
              "GREEN" if r.get("html") and how in ("inserted", "replaced", "same") and sp["ok"] else "YELLOW"))
    return rc


def apply_spec_all(out: Path) -> dict:
    """VIA_Reports/vdf 底下每一頁 *_latest.html 套 VRN-2 視覺規格(經 ENG236.apply_spec;鎖對不上就不套)。"""
    fm = fm_module()
    if fm is None:
        return {"ok": False, "line": "ENG236 不在 → 沒套", "pages": {}}
    spec = fm.visual_spec()
    pages = {}
    for pg in sorted(Path(out).rglob("*_latest.html")):
        pages[str(pg.relative_to(out))] = fm.apply_spec(pg, spec)
    bad = [k for k, v in pages.items() if v in ("lock-bad",)]
    ok = spec.get("ok") and not bad
    return {"ok": bool(ok), "pages": pages, "line": ("%s · %d 頁(新套 %d · 換新 %d · 不變 %d)" % (
        spec.get("book"), len(pages), sum(1 for v in pages.values() if v == "inserted"), sum(1 for v in pages.values() if v == "replaced"),
        sum(1 for v in pages.values() if v == "same"))) if spec.get("ok") else ("鎖對不上 → 沒套(%s)" % spec.get("why"))}


_UI_SAMPLE_V0165 = ('<!doctype html><html><head><meta charset="utf-8"></head><body><main><div class="tabs"><button class="on" onclick="tab(0,this)">健康</button>'
                    '<button onclick="tab(1,this)">表頭彙整</button></div>\n  <div class="pages">\n    <div class="page on"><iframe id="f0" src="a.html"></iframe></div>\n'
                    '    <div class="page"><iframe id="f1" src="b.html"></iframe></div>\n  </div>\n</main><script>function tab(i,b){}</script></body></html>')


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print("=== %s %s · 薄尾自測(擷取矩陣頁籤 · fetchmatrix)===" % (_STEM, TAG))
    tmp = Path(tempfile.mkdtemp(prefix="vdf_sm0165_"))
    try:
        ui = tmp / "VDF_UI_latest.html"
        ui.write_text(_UI_SAMPLE_V0165, encoding="utf-8")
        how0 = inject_tab(ui, "測試")
        h0 = ui.read_text(encoding="utf-8")
        chk("① 頁籤補在最後 · 預設打開(原本的 on 拿掉)· 矩陣頁還沒產 → srcdoc 寫說明(不留白頁)· %s" % how0,
            how0 == "inserted" and h0.count(TAB_MARK_V0165) == 2 and 'onclick="tab(2,this)">擷取矩陣' in h0 and h0.count('class="on"') == 1
            and h0.count('class="page on"') == 1 and "srcdoc=" in h0 and '<div class="page"><iframe id="f0"' in h0, h0[-600:])
        r = build_matrix(out=tmp)
        how1 = inject_tab(ui)
        how2 = inject_tab(ui)
        h1 = ui.read_text(encoding="utf-8")
        chk("② 產矩陣(%s)後再補 → iframe 指 %s · 再跑一次不疊(%s → %s)" % (r.get("lamp"), FM_PAGE_V0165, how1, how2),
            r.get("html") and (tmp / FM_PAGE_V0165).is_file() and how1 == "replaced" and how2 == "same" and h1.count(TAB_MARK_V0165) == 2
            and 'src="%s"' % FM_PAGE_V0165 in h1 and "srcdoc" not in h1.split(TAB_MARK_V0165, 2)[-1][:200], (how1, how2))
        chk("③ 頁不在 → missing;沒有頁籤結構 → no-tabs(不亂改)", inject_tab(tmp / "nope.html") == "missing"
            and (lambda q: (q.write_text("<html><body>x</body></html>", encoding="utf-8"), inject_tab(q))[1])(tmp / "plain.html") == "no-tabs")
        chk("④ ENG236 / ENG237 尾版找得到(%s · %s)" % (getattr(fm_module(), "TAG", None), getattr(ex_module(), "TAG", None)),
            fm_module() is not None and ex_module() is not None)
        sp = apply_spec_all(tmp)
        sp2 = apply_spec_all(tmp)
        hh = ui.read_text(encoding="utf-8")
        chk("④b VDF 頁一律套 VRN-2 視覺規格(%s → 再跑 %s)· 操作頁帶鎖定原文 + 色票對照" % (sp["line"], sp2["line"]),
            sp["ok"] and sp2["ok"] and all(v == "same" for v in sp2["pages"].values()) and 'id="vrn2-professional-v0242"' in hh and "vdf-vrn2-bridge" in hh)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑤ 不匯入他系統程式 · 兩座橋在 · 同意閘不寫 · 零網路",
        not re.search(r"^\s*(import|from)\s+(CGC_|VRN_|VCGC|requests|httpx|urllib\.request)", src, re.M) and "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
        and "_CONSENT\"] =" not in body)
    print("  ── 前版鏈自測(原樣印出;VIA_SKIP_PRIOR_SELFTEST=1 略過)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑥ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] %s_%s 自測 %d/%d · %s" % (_STEM, TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
