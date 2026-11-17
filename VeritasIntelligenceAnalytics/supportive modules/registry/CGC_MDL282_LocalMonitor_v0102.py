#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL282_LocalMonitor v0102 — 薄尾(v0101 · v0100 一字不動):延伸偵測加增量快取,彙總列標明「不另計」。

操作員 2026-11-18:「現況顯示功能引擎及展現方式最佳化準備被整合」。
  ① 增量快取:橋覆蓋的語法樹掃描與號冊讀取最花時間。每支檔以「大小 + 修改時間」為憑,沒變就沿用上一輪的結果,只重掃變過的。
     快取放 VIA_Reports/vcgc/monitor_cache_v1.json(倉裡已忽略);壞掉、版本不合或讀不到就當成沒有,整輪重掃,不影響結果。
     快取查找在主行程做,只有沒命中的才交給平行 map,所以加速器用行程或執行緒都一樣對。
  ② 彙總列標 rollup:號冊彙總(該類的問題已在「號冊待辦」逐列時)與橋覆蓋彙總,問題已經逐列各算一項;彙總列帶 rollup = true,
     讓平台引擎(CGC_MDL283 v0103 起)不再把它們另算一項。政策等「黃列沒有逐列」的號冊彙總不標,仍照算。
  其餘偵測內容與 v0101 相同。唯讀倉;只寫 VIA_Reports/vcgc 的快取。不發號 · 不裝套件 · 不連網 · 不載 TA-Lib。
動詞  run · extra · selftest · version(同 v0101)
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
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

ENGINE = "CGC_MDL282_LocalMonitor_v0102"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "CGC_MDL282_LocalMonitor_v0101.py"
_PRIOR_FILE = HERE / PRIOR_NAME
_spec = importlib.util.spec_from_file_location("CGC_MDL282_LocalMonitor_v0101", _PRIOR_FILE)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["CGC_MDL282_LocalMonitor_v0101"] = PRIOR
_spec.loader.exec_module(PRIOR)
P0 = PRIOR.PRIOR                      # v0100 本體;v0101 的平行 map 走 P0.pmap
PRIOR.ENGINE = P0.ENGINE = ENGINE
CACHE_TAG = "CGC_MDL282 cache v1 · " + PRIOR_NAME   # 判別式(v0101)換版 → 快取作廢
CACHED = ("_scan_py", "_read_book")
STATE = {"d": None, "hit": 0, "miss": 0, "note": ""}
_PM = P0.pmap


def _cache_file(via: Path) -> Path:
    return Path(via) / "VIA_Reports" / "vcgc" / "monitor_cache_v1.json"


def cache_load(via: Path):
    STATE.update(d={}, hit=0, miss=0, note="")
    p = _cache_file(via)
    if not p.is_file():
        STATE["note"] = "沒有快取(第一輪)"
        return
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
        if doc.get("tag") == CACHE_TAG and isinstance(doc.get("d"), dict):
            STATE["d"] = doc["d"]
        else:
            STATE["note"] = "快取版本不合,整輪重掃"
    except (OSError, ValueError):
        STATE["note"] = "快取讀不懂,整輪重掃"


def cache_save(via: Path):
    if STATE["d"] is None:
        return
    p = _cache_file(via)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_name(p.name + ".%d.tmp" % os.getpid())
        tmp.write_text(json.dumps({"tag": CACHE_TAG, "d": STATE["d"]}, ensure_ascii=False), encoding="utf-8")
        os.replace(str(tmp), str(p))  # 原子換檔
    except OSError as e:
        STATE["note"] = "快取寫不進去(%s),下一輪會整輪重掃" % type(e).__name__


def cached_pmap(fn, items):
    """只接 v0101 的兩支重活;其餘照舊。命中與否在主行程判,沒命中的才平行。"""
    name = getattr(fn, "__name__", "")
    if name not in CACHED or STATE["d"] is None:
        return _PM(fn, items)
    items = list(items)
    out, miss = [None] * len(items), []
    for i, x in enumerate(items):
        path = (Path(x[0]) / x[1]) if name == "_scan_py" else Path(x)
        key = "%s|%s" % (name, x[1] if name == "_scan_py" else path.name)
        try:
            st = path.stat()
            sig = [st.st_size, st.st_mtime_ns]
        except OSError:
            sig = None
        hit = STATE["d"].get(key)
        if sig is not None and hit and hit[0] == sig:
            out[i] = tuple(hit[1])
            STATE["hit"] += 1
        else:
            miss.append((i, x, key, sig))
    if miss:
        STATE["miss"] += len(miss)
        for (i, _, key, sig), r in zip(miss, _PM(fn, [m[1] for m in miss])):
            out[i] = r
            if sig is not None:
                STATE["d"][key] = [sig, list(r)]
    return out


P0.pmap = cached_pmap


def mark_rollup(items):
    for it in items:
        if it.get("section") == "橋覆蓋" and str(it.get("id", "")).startswith("彙總|"):
            it["rollup"] = True
        elif it.get("section") == "號冊":
            kind = str(it.get("id", "")).split("|")[0]
            if it.get("lamp") in ("y", "r") and (kind in PRIOR.ROWWISE or " 黃 0 " in it.get("detail", "")) and "壞列" not in it.get("detail", ""):
                it["rollup"] = True  # 這一類的黃 / 紅都已在「號冊待辦」逐列
    return items


def sec_extra(via, tails=None):
    via = Path(via)
    t0 = time.time()
    cache_load(via)
    try:
        items = mark_rollup(PRIOR.sec_extra(via, tails))
    finally:
        cache_save(via)
    print("[延伸] 快取:沿用 %d · 重掃 %d%s · %.1f 秒 · 彙總列 %d(不另計)" % (
        STATE["hit"], STATE["miss"], (" · " + STATE["note"]) if STATE["note"] else "", time.time() - t0, sum(1 for it in items if it.get("rollup"))), flush=True)
    return items


def __getattr__(name):  # 薄尾轉接
    return getattr(PRIOR, name)


def selftest() -> int:
    fails = []

    def chk(name, cond, got=None):
        print("  [%s] %s%s" % ("過" if cond else "敗", name, "" if cond else " · 得到 %r" % (got,)), flush=True)
        if not cond:
            fails.append(name)
    chk("v0101(含 v0100)的自測在本版掛上後仍全過", PRIOR.selftest() == 0)
    tmp = Path(tempfile.mkdtemp(prefix="via_lm102_st_"))
    try:
        via = tmp / "via"
        nb, fm = via / "supportive modules" / "registry" / "VIA_NumberBooks", via / "functional modules" / "VDF"
        nb.mkdir(parents=True)
        fm.mkdir(parents=True)
        (nb / "VIA_NumberBook_REQ_v0100.jsonl").write_text(json.dumps({"code": "R1", "sub": "VDF", "name": "需求", "lamp": "AMBER"}) + "\n", encoding="utf-8")
        (nb / "VIA_NumberBook_PLCY_v0100.jsonl").write_text(json.dumps({"code": "P1", "sub": "CORE", "name": "律", "lamp": "AMBER"}) + "\n", encoding="utf-8")
        (nb / "VIA_NumberBook_FM_v0100.jsonl").write_text(json.dumps({"code": "F1", "sub": "VDF", "name": "名", "lamp": "RED"}) + "\n", encoding="utf-8")
        (fm / "A_v0100.py").write_text("x = 1\n", encoding="utf-8")
        (fm / "B_v0100.py").write_text("import VIA_SuperAccel_Module\n", encoding="utf-8")
        (via / "supportive modules" / "VIA_SuperAccel_Module.py").write_text("y = 1\n", encoding="utf-8")

        def strip(items):
            return json.dumps(sorted((json.dumps(x, ensure_ascii=False, sort_keys=True) for x in items if x["section"] not in ("版本線", "執行環境"))), ensure_ascii=False)
        a = sec_extra(via)
        h1, m1 = STATE["hit"], STATE["miss"]
        chk("第一輪全部重掃並寫出快取", h1 == 0 and m1 == 5 and _cache_file(via).is_file(), (h1, m1))
        b = sec_extra(via)
        chk("第二輪沒變的全部沿用,結果一字不差", STATE["miss"] == 0 and STATE["hit"] == 5 and strip(a) == strip(b), (STATE["hit"], STATE["miss"]))
        time.sleep(0.02)
        (fm / "A_v0100.py").write_text("import VIA_SuperAccel_Module\nz = 2\n", encoding="utf-8")
        c = sec_extra(via)
        ids = {x["id"] for x in c}
        chk("改過的那一支才重掃,結果跟著變", STATE["miss"] == 1 and STATE["hit"] == 4 and "加速器|functional modules/VDF/A_v0100.py" not in ids and "加速器|functional modules/VDF/A_v0100.py" in {x["id"] for x in a}, (STATE["hit"], STATE["miss"]))
        _cache_file(via).write_text("壞掉的快取", encoding="utf-8")
        d = sec_extra(via)
        chk("快取壞掉:整輪重掃、結果不變、照實註明", STATE["miss"] == 5 and "讀不懂" in STATE["note"] and strip(c) == strip(d), STATE["note"])
        _cache_file(via).write_text(json.dumps({"tag": "別的版本", "d": {"x": 1}}), encoding="utf-8")
        sec_extra(via)
        chk("快取版本不合:作廢重掃", STATE["miss"] == 5 and "版本不合" in STATE["note"], STATE["note"])
        k = {x["id"]: x for x in d}
        chk("彙總列:需求類(黃已逐列)與名單類(紅已逐列)標不另計;政策類的黃沒逐列,不標", k["REQ|VDF"].get("rollup") is True and k["FM|VDF"].get("rollup") is True and not k["PLCY|CORE"].get("rollup"),
            [(i, k[i].get("rollup")) for i in ("REQ|VDF", "FM|VDF", "PLCY|CORE")])
        chk("橋覆蓋彙總標不另計,逐列的不標", k["彙總|VDF"].get("rollup") is True and not any(x.get("rollup") for x in d if x["section"] == "號冊待辦"))
        chk("其他平行工作不走快取", cached_pmap(lambda v: v * 2, [1, 2, 3]) == [2, 4, 6])
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)
    print("[selftest] %s · %d 敗 · %s" % ("GREEN" if not fails else "RED", len(fails), ENGINE), flush=True)
    return 0 if not fails else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    verb = a[0] if a and not a[0].startswith("-") else "run"
    if verb == "selftest" or "--selftest" in a:
        return selftest()
    if verb == "version":
        print("%s · %s(薄尾,前版 %s)" % (Path(__file__).name, ENGINE, PRIOR_NAME))
        return 0
    if verb == "extra":
        via = PRIOR.find_via(a[a.index("--root") + 1] if "--root" in a and a.index("--root") + 1 < len(a) else "")
        if via is None:
            print("[紅] 找不到 VIA 夾")
            return 3
        cnt = {}
        for it in sec_extra(via):
            d = cnt.setdefault(it["section"], {"g": 0, "y": 0, "r": 0, "x": 0})
            d[it["lamp"]] += 1
        for s, d in cnt.items():
            print("[區塊] %s:紅 %d · 黃 %d · 綠 %d · 灰 %d" % (s, d["r"], d["y"], d["g"], d["x"]))
        return 0
    return PRIOR.main(a)


if __name__ == "__main__":
    sys.exit(main())
