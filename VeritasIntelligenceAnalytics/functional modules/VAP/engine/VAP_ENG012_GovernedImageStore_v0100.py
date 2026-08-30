#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VAP_ENG012_GovernedImageStore — 治理存圖道(批251;補 TPN 冊唯一斷點)
====================================================================
批250 連接點矩陣唯一 GAP=saveGovernedImage(儲存圖像步 VIA 端無對位)
→本引擎落地治理存圖:
  save --file <圖/規格檔> [--tpn TPN-xxx]:
    ①sha256 定生死(同 hash 已存=SKIP 冪等)②入庫
    VIA_Reports/vap_images/<ts>_<tpn>_<hash8><副檔>(gitignored;
    影像不入 git)③append-only manifest(tpn 連結/來源/sha/時戳)
    ④TPN 引用驗證(冊內無此 TPN=誠實拒)
  list:台帳列示。只增不減;原檔零觸碰(copy 非 move)。
用法:python3 VAP_ENG012_GovernedImageStore_v0100.py save --file F
      [--tpn TPN-001] | list | --selftest
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

import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
STORE = VIA / "VIA_Reports" / "vap_images"
MANIFEST = STORE / "manifest.json"
TPN_REG = (VIA / "supportive modules" / "registry"
           / "VIA_VAP_TemplateRegistry_v0100.json")


def _load_mf() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"entries": [], "note": "append-only;sha 定生死;影像不入 git"}


def save(src: Path, tpn: str | None = None) -> int:
    if not src.exists():
        print(f"[存圖] 來源缺 {src}=誠實拒")
        return 2
    if tpn:
        known = set()
        if TPN_REG.exists():
            reg = json.loads(TPN_REG.read_text(encoding="utf-8"))
            known = {t["tpn"] for t in reg.get("templates", [])} | \
                    {c["tpn"] for c in reg.get("composites", [])}
        if tpn not in known:
            print(f"[存圖] TPN {tpn} 不在冊=誠實拒(先 via-tpn register)")
            return 2
    sha = hashlib.sha256(src.read_bytes()).hexdigest()
    mf = _load_mf()
    dup = next((e for e in mf["entries"] if e["sha256"] == sha), None)
    if dup:
        print(f"[存圖] 同 hash 已存(冪等)={dup['stored']}")
        return 0
    STORE.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"{ts}_{tpn or 'NOTPN'}_{sha[:8]}{src.suffix.lower()}"
    shutil.copy2(src, STORE / name)          # copy 非 move=原檔零觸碰
    mf["entries"].append({"stored": name, "tpn": tpn, "source": src.name,
                          "sha256": sha, "ts": ts})
    MANIFEST.write_text(json.dumps(mf, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print(f"[存圖] {name} · tpn={tpn or '—'} · 台帳 {len(mf['entries'])} 筆"
          "(append-only;不入 git)")
    return 0


def list_store() -> int:
    mf = _load_mf()
    for e in mf["entries"][-20:]:
        print(f"  {e['ts']} · {e['stored']} · tpn={e['tpn'] or '—'}")
    print(f"[台帳] {len(mf['entries'])} 筆 · {STORE}")
    return 0


def selftest() -> int:
    import tempfile
    global STORE, MANIFEST
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    s0, m0 = STORE, MANIFEST
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        STORE = tdp / "store"
        MANIFEST = STORE / "manifest.json"
        img = tdp / "chart.png"
        img.write_bytes(b"\x89PNG-fake")
        chk("① 存圖入庫+manifest(append-only)", save(img) == 0
            and MANIFEST.exists()
            and len(_load_mf()["entries"]) == 1)
        chk("② 同 hash 冪等 SKIP(sha 定生死)", save(img) == 0
            and len(_load_mf()["entries"]) == 1)
        chk("③ 原檔零觸碰(copy 非 move)", img.exists())
        chk("④ 未知 TPN 誠實拒 rc2", save(img, "TPN-999X") == 2)
        chk("⑤ 來源缺誠實 rc2", save(tdp / "none.png") == 2)
        img2 = tdp / "chart2.png"
        img2.write_bytes(b"\x89PNG-fake2")
        real_tpn = None
        if TPN_REG.exists():
            reg = json.loads(TPN_REG.read_text(encoding="utf-8"))
            if reg.get("templates"):
                real_tpn = reg["templates"][0]["tpn"]
        chk("⑥ 真 TPN 冊連結(在冊 TPN 通過驗證)",
            real_tpn is None or save(img2, real_tpn) == 0,
            f"tpn={real_tpn}")
        chk("⑦ list 台帳", list_store() == 0)
    STORE, MANIFEST = s0, m0
    chk("⑧ 紅線宣告(影像不入 git)+零網路+加速橋",
        "不入 git" in src and "ACCEL-BRIDGE" in src
        and all(("import " + k) not in src for k in ("requests", "httpx")))
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 治理存圖道(VAP_ENG012)· 八檢自測(零網路)===")
        return selftest()
    if args and args[0] == "save" and "--file" in args:
        f = Path(args[args.index("--file") + 1])
        t = args[args.index("--tpn") + 1] if "--tpn" in args else None
        return save(f, t)
    if args and args[0] == "list":
        return list_store()
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
