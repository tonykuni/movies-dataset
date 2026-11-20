#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL226_StepMatrix v0104 — 薄尾:步驟矩陣頁帶上「產生時間 · 版本」(機讀 meta;前版一字不動,視覺零改)
操作員 2026-11-20「收尾 VCGC ONLY AND HTML U/I」。VCGC synchronizer(CGC_MDL149 v0198 起)核頁對收據時,
這張頁沒有收據,只能看頁上有沒有「產生時間」與「版本」(SY_STAMP 時間樣式 + vNNNN);前版的頁兩樣都沒有 → 同步燈黃。
本版只做一件事:頁照前版產生,寫頁那一層(本體的 write_page)寫完就在頁的 <head> 裡插一行
  <meta name="via-generated" content="<UTC 時間> · CGC_MDL226_StepMatrix v0104">
(已有就換成這一輪的;沒有 <head> 就放最前面)。不加任何樣式、不動任何顏色 / 字體 / 版面(HTML U/I 視覺鎖定)。
頁沒在這一輪更新(前版沒寫頁)就不蓋章,免得把舊頁冒充成這一輪;前版自測在這一輪重寫了頁也照樣蓋(串測會跑前版自測)。其餘公開名稱、main、selftest 全部原樣轉給前版。
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

import datetime as _dt
import importlib.util
import os
import re
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL226_StepMatrix"
VERSION = "v0104"
META_RE = re.compile(r'<meta name="via-generated" content="[^"]*">')


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_v0104", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def page_path():
    """沿前版鏈找 PAGE(本體才有這個常數)。"""
    b = page_module()
    return Path(vars(b)["PAGE"]) if b is not None else None


def page_module():
    """前版鏈上真正寫頁的那一個模組(自己的全域裡有 PAGE 與 write_page;薄尾的 __getattr__ 轉接不算)。"""
    p = PRIOR
    for _ in range(12):
        if p is None:
            return None
        if "PAGE" in vars(p) and "write_page" in vars(p):
            return p
        p = vars(p).get("PRIOR") or vars(p).get("_BASE")
    return None


def stamp(path: Path, when: str | None = None) -> bool:
    """在頁的 <head> 插 / 換一行機讀 meta;原子換檔。檔不在或讀不到回 False。"""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    when = when or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    tag = '<meta name="via-generated" content="%s · %s %s">' % (when, _STEM, VERSION)
    if META_RE.search(text):
        new = META_RE.sub(lambda _m: tag, text, count=1)
    else:
        m = re.search(r"<head[^>]*>", text, re.I)
        new = text[:m.end()] + tag + text[m.end():] if m else tag + text
    fd, tmp = tempfile.mkstemp(prefix=".via_stamp_", dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(new)
    os.replace(tmp, path)
    return True


def _install_stamp():
    """把蓋章裝在真正寫頁的那一層(主控台的中央頁 / 流程閘直接叫模組函式,不經 main;教訓 LL-20261119-17)。"""
    b = page_module()
    if b is None or getattr(vars(b)["write_page"], "_via_stamped", False):
        return False
    orig = vars(b)["write_page"]

    def write_page(card, *a, **k):
        r = orig(card, *a, **k)
        stamp(Path(vars(b)["PAGE"]))
        return r
    write_page._via_stamped = True
    write_page._via_orig = orig
    b.write_page = write_page
    return True


_install_stamp()


def main() -> int:
    t0 = time.time()
    rc = PRIOR.main()
    pg = page_path()
    if pg is not None and pg.is_file() and pg.stat().st_mtime >= t0 - 1:
        stamp(pg)
    return rc


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note and not cond else ""), flush=True)

    print("=== %s %s 薄尾自測(頁帶產生時間 · 版本;視覺零改)===" % (_STEM, VERSION))
    stamp_re = re.compile(r"(20\d\d-\d\d-\d\d)[T ](\d\d:\d\d(?::\d\d)?)(?:\.\d+)?(Z|\s?[+-]\d\d:?\d\d)?")
    with tempfile.TemporaryDirectory(prefix="stamp_0104_") as td:
        f = Path(td) / "p.html"
        body = '<html><head><style>.x{color:#123}</style></head><body><p class="x">內容</p></body></html>'
        f.write_text(body, encoding="utf-8")
        stamp(f, "2026-11-20T00:00:00Z")
        t1 = f.read_text(encoding="utf-8")
        chk("① 插在 <head> 後 · 時間與版本都抓得到(與 synchronizer 同一把尺)",
            t1.startswith('<html><head><meta name="via-generated"') and stamp_re.search(t1) and re.search(r"(?<![A-Za-z0-9])v\d{4}(?!\d)", t1), t1[:120])
        chk("② 視覺零改:去掉那一行 meta 後與原頁逐字相同", META_RE.sub("", t1) == body)
        stamp(f, "2026-11-21T01:02:03Z")
        t2 = f.read_text(encoding="utf-8")
        chk("③ 再蓋一次是換掉、不疊加(只有一行 · 時間是新的)", len(META_RE.findall(t2)) == 1 and "2026-11-21T01:02:03Z" in t2)
        g = Path(td) / "nohead.html"
        g.write_text("<p>x</p>", encoding="utf-8")
        stamp(g, "2026-11-20T00:00:00Z")
        chk("④ 沒有 <head> → 放最前面", g.read_text(encoding="utf-8").startswith('<meta name="via-generated"'))
        chk("⑤ 檔不在 → 回 False(不丟例外)", stamp(Path(td) / "none.html") is False)
    pg = page_path()
    chk("⑥ 沿前版鏈找得到 PAGE", pg is not None and pg.name.endswith(".html"), pg)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 加速器橋真的匯入 · 不碰 TA-Lib · 不含本機路徑", "import VIA_SuperAccel_Module as VIA_ACCEL" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and ("C:" + "\\Users") not in src)
    t0 = time.time()
    rc = PRIOR.selftest()
    chk("⑧ 前版 %s 自測照過" % PRIOR_PATH.stem, rc == 0, "rc %s" % rc)
    if pg is not None and pg.is_file() and pg.stat().st_mtime >= t0 - 1:
        stamp(pg)                       # 前版自測這一輪重寫了頁 → 照樣蓋這一輪的章(不然最後寫頁的是沒章的前版)
    b = page_module()
    chk("⑩ 寫頁那一層已裝上蓋章(主控台直接叫 write_page 也會蓋)· 原函式保留",
        b is not None and getattr(vars(b)["write_page"], "_via_stamped", False) and callable(getattr(vars(b)["write_page"], "_via_orig", None)))
    chk("⑨ 前版自測這一輪若重寫了頁,頁上照樣有本輪的產生時間與版本",
        pg is None or not pg.is_file() or pg.stat().st_mtime < t0 - 1 or (META_RE.search(pg.read_text(encoding="utf-8")) is not None))
    good = all(ok)
    print("[計] %s %s 本版 %d/%d · %s" % (_STEM, VERSION, sum(ok), len(ok), "PASS" if good else "FAIL"))
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
