#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0287 — 薄尾(v0286 以前一字不動):version --json / health --json 仍是合法 JSON(PR 724 Codex P2)

  v0286 的 health --json 把前版的 JSON 每一行前面加了說明字、尾端又接一行文字摘要 → 輸出不是 JSON;
  version --json 則把 --json 旗標丟了(只叫前版 ["version"])。v0285 這兩個都是合法 JSON,v0286 退步。
  v0286 已鎖成功(sha a153a7f84dc7),修改開新版 → 本版:
  · --json:前版原生處理器的 JSON 原樣解析,每個鍵一字不動保留,新資訊加成欄位 ——
      version --json:live_tail(manager · version · sha256 · prior · native_handler)· chain(count · complete · bad · versions)
      health --json :live_tail · chain · help_missing · scan_cache;lamp = 前版燈與新檢查取較差(前版燈留在 prior_lamp),
                      新理由接在 red / yellow 後面。
  · 文字模式照 v0286 的內容,只是頂端 / 判決行標的是現役尾版(本版),鏈從本版算起。
  · help / verbs 的頂端也標本版;動詞表從本版算起(v0286 的鏈 / 動詞 / 快取函式原樣沿用,只把本版接在鏈頭)。
  引擎矩陣掃描快取照 v0286(載入 v0286 時就已換上)。其餘動詞照 v0286。
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
import importlib.util
import io
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VRN_SystemManager"
TAG = "VRN_SystemManager v0287"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0287", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
NATIVE = PRIOR.PRIOR                                  # v0285:它的 version / health / help 一路交到 v0269 原生處理器
NATIVE_FLOOR = PRIOR.NATIVE_FLOOR


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def chain_modules() -> list:
    return [sys.modules[__name__]] + PRIOR.chain_modules()


def chain_report() -> dict:
    return PRIOR.chain_report(chain_modules())


def verb_table() -> list:
    return PRIOR.verb_table(chain_modules())


def _capture(fn, *a):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*a)
    return rc, buf.getvalue()


def _prior_json(args) -> tuple:
    """前版原生處理器 --json 的輸出原樣解析;解析不了就原文放進 prior_text(不丟)。"""
    rc, out = _capture(NATIVE.main, args)
    try:
        return rc, json.loads(out), None
    except ValueError:
        return rc, None, out


def _late(table) -> list:
    return [r for r in table if _vnum("x_" + r["added"]) > NATIVE_FLOOR]


def cmd_version(args=()) -> int:
    cr = chain_report()
    tail = {"manager": Path(__file__).name, "version": "v%04d" % _vnum(__file__), "sha256": PRIOR._file_sha(Path(__file__)),
            "prior": PRIOR_PATH.name, "native_handler": "v%04d" % NATIVE_FLOOR}
    chain = {"count": cr["count"], "complete": not cr["bad"], "bad": cr["bad"], "versions": [r["version"] for r in cr["rows"]]}
    if "--json" in args:
        rc, body, text = _prior_json(["version", "--json"])
        body = dict(body) if isinstance(body, dict) else {"prior_text": text}
        body["live_tail"], body["chain"] = tail, chain
        print(json.dumps(body, ensure_ascii=False, indent=1))
        return 1 if cr["bad"] else rc
    print("[%s] VRN · 現役尾版 %s · sha %s · 鏈 %d 版(%s → v%04d 原生處理器)· %s" % (
        TAG, tail["manager"], tail["sha256"][:12], cr["count"], cr["tail"], NATIVE_FLOOR,
        "鏈完整" if not cr["bad"] else "鏈有問題:" + ";".join(cr["bad"][:3])))
    rc, out = _capture(NATIVE.main, ["version"])
    for ln in out.splitlines():
        print("  前版原生處理器 · " + ln)
    return 1 if cr["bad"] else rc


def health_extra() -> dict:
    cr = chain_report()
    table = verb_table()
    _, help_out = _capture(NATIVE.main, ["help"])
    help_out += "\n" + " ".join(r["verb"] for r in _late(table)) + " verbs"
    missing = PRIOR.help_coverage(help_out, table)
    sc = PRIOR.scan_cache_status()
    red = ["鏈:" + b for b in cr["bad"]]
    yellow = (["help 漏列:" + " ".join(missing)] if missing else []) + ([] if sc["in_effect"] else ["引擎矩陣掃描快取沒生效"])
    return {"chain": {"count": cr["count"], "complete": not cr["bad"], "bad": cr["bad"], "rows": cr["rows"]},
            "help_missing": missing, "scan_cache": sc, "red": red, "yellow": yellow}


def _worst(*lamps) -> str:
    order = {"GREEN": 0, "GRAY": 0, "YELLOW": 1, "RED": 2}
    return max(lamps, key=lambda x: order.get(x, 1))


RC = {"GREEN": 0, "YELLOW": 2, "RED": 1}


def cmd_health(args) -> int:
    ex = health_extra()
    own = "RED" if ex["red"] else ("YELLOW" if ex["yellow"] else "GREEN")
    if "--json" in args:
        rc0, body, text = _prior_json(["health", *args])
        body = dict(body) if isinstance(body, dict) else {"prior_text": text, "lamp": "YELLOW"}
        prior_lamp = body.get("lamp") or {0: "GREEN", 1: "RED"}.get(rc0, "YELLOW")
        body["prior_lamp"] = prior_lamp
        body["lamp"] = _worst(prior_lamp, own)
        body["red"] = list(body.get("red") or []) + ex["red"]
        body["yellow"] = list(body.get("yellow") or []) + ex["yellow"]
        body["live_tail"] = {"manager": Path(__file__).name, "version": "v%04d" % _vnum(__file__)}
        body["chain"], body["help_missing"], body["scan_cache"] = ex["chain"], ex["help_missing"], ex["scan_cache"]
        print(json.dumps(body, ensure_ascii=False, indent=1))
        return RC.get(body["lamp"], 2)
    rc0, out = _capture(NATIVE.main, ["health", *args])
    for ln in out.splitlines():
        print("  前版原生處理器 · " + ln)
    ch, sc = ex["chain"], ex["scan_cache"]
    parts = ["鏈 %d/%d 版 ✓" % (ch["count"], ch["count"]) if ch["complete"] else "鏈 ✗ " + ";".join(ch["bad"][:3]),
             "help 涵蓋 %s" % ("✓" if not ex["help_missing"] else "✗ 漏 " + " ".join(ex["help_missing"])),
             "引擎矩陣掃描快取 %s · %s 筆" % ("生效" if sc["in_effect"] else "沒生效", sc["entries"] if sc["entries"] is not None else "0")]
    lamp = _worst({0: "GREEN", 1: "RED"}.get(rc0, "YELLOW"), own)
    print("[%s] health %s · %s" % (TAG, lamp, " · ".join(parts)))
    return RC[lamp]


def cmd_help() -> int:
    print("%s(現役尾版)· VRN 自己的入口 · 動詞與處理版:verbs · 鏈與健康:version / health(加 --json 機器可讀)" % TAG)
    rc, out = _capture(NATIVE.main, ["help"])
    print(out, end="")
    print("  ── v0270 以後加的動詞(從各尾版 main() 讀出;前版 help 沒列的補在這裡)──")
    for r in _late(verb_table()):
        print("  %-14s %s 加%s" % (r["verb"], r["added"], (" · 最新 " + r["top"]) if r["top"] != r["added"] else ""))
    print("  verbs [--json]                每個動詞由哪一版處理")
    print("  launch --run                  開閘全跑(v0283 起走 TEMP · 起跑前備份庫);resources [--verify] 看資源與備份")
    return rc


def cmd_verbs(args) -> int:
    table = verb_table()
    if "--json" in args:
        print(json.dumps({"tool": TAG, "verbs": table, "older": "其餘舊動詞由 v0269 原生處理器轉交 v0268 以下(子行程)"}, ensure_ascii=False, indent=1))
        return 0
    print("[%s] verbs · %d 個(加入版 · 最新處理版 · 中間也接手的版)" % (TAG, len(table)))
    for r in table:
        mid = [x for x in r["touched"] if x not in (r["added"], r["top"])]
        print("  %-16s 加 %s · 最新 %s%s · %s" % (r["verb"], r["added"], r["top"], (" · 經 " + " ".join(mid)) if mid else "", r["how"]))
    print("  其餘舊動詞:v0269 原生處理器原樣轉交 v0268 以下(子行程)")
    return 0


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if not args or args[:1] == ["help"]:
        return cmd_help()
    if args[:1] == ["version"] and "--legacy" not in args:
        return cmd_version(args[1:])
    if args[:1] == ["health"] and "--legacy" not in args:
        return cmd_health(args[1:])
    if args[:1] == ["verbs"]:
        return cmd_verbs(args[1:])
    return PRIOR.main(args)


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)

    # v0286 的自測假設自己是磁碟上最新那一版(「磁碟最大版 ≠ 正在跑的版」會亮紅)。測 v0286 本身時,給它看「到 v0286 為止」的版名清單
    # (chain_report 只用 family_dir 數版號、讀檔走模組的 __file__),測完換回;v0286 檔一字不動。
    real_cr = PRIOR.chain_report
    with tempfile.TemporaryDirectory(prefix="via_vrn287_fam_") as fam:
        for p in HERE.glob(FAMILY + "_v*.py"):
            if 0 <= _vnum(p) <= _vnum(PRIOR_PATH):
                (Path(fam) / p.name).write_text("", encoding="utf-8")
        PRIOR.chain_report = lambda mods=None, family_dir=None: real_cr(mods, fam if family_dir is None else family_dir)
        try:
            rc0, out0 = _capture(PRIOR.selftest)
        finally:
            PRIOR.chain_report = real_cr
    print(f"=== {TAG} · 薄尾自測(version / health --json 仍是合法 JSON · 頂端標本版 · 鏈從本版算起;零網路)===")
    chk("⓪ 直接前版 %s 自測過(已鎖 v0286 原封不動)" % PRIOR_PATH.name, rc0 == 0, out0[-300:])
    with tempfile.TemporaryDirectory(prefix="via_vrn287_") as td:          # 快取寫暫存夾,不碰真的 VIA_Reports
        keep = os.environ.get("VIA_VRN_SCAN_CACHE")
        os.environ["VIA_VRN_SCAN_CACHE"] = str(Path(td) / "cache.json")
        try:
            _, p_v, _ = _prior_json(["version", "--json"])
            _, p_h, _ = _prior_json(["health", "--json"])
            rvj, vj = _capture(cmd_version, ["--json"])
            rhj, hj = _capture(cmd_health, ["--json"])
        finally:
            if keep is None:
                os.environ.pop("VIA_VRN_SCAN_CACHE", None)
            else:
                os.environ["VIA_VRN_SCAN_CACHE"] = keep
    try:
        vjd, hjd = json.loads(vj), json.loads(hj)
    except ValueError as exc:
        vjd, hjd = {}, {}
        print("    json:", str(exc)[:120])
    chk("① PR 724 Codex P2:version --json 是合法 JSON · 前版原生處理器每個鍵都在且值不變",
        isinstance(p_v, dict) and bool(vjd) and all(vjd.get(k) == p_v[k] for k in p_v), vj[:200])
    chk("② version --json 新欄位:live_tail = 本版 · chain 完整且從本版算起",
        rvj == 0 and vjd.get("live_tail", {}).get("version") == "v0287" and vjd.get("chain", {}).get("complete") is True
        and (vjd.get("chain", {}).get("versions") or [None])[0] == "v0287")
    chk("③ health --json 是合法 JSON · 前版每個鍵都在 · 新欄位 chain / help_missing / scan_cache / prior_lamp · 真樹綠",
        isinstance(p_h, dict) and bool(hjd) and all(k in hjd for k in p_h) and rhj == 0 and hjd.get("lamp") == "GREEN"
        and hjd.get("chain", {}).get("complete") is True and hjd.get("help_missing") == [] and "scan_cache" in hjd and hjd.get("prior_lamp") == p_h.get("lamp"))
    chk("④ 燈取較差:前版綠 + 新檢查紅 → 紅;黃 + 綠 → 黃", _worst("GREEN", "RED") == "RED" and _worst("YELLOW", "GREEN") == "YELLOW")
    real = NATIVE.main
    NATIVE.main = lambda a=None: print("不是 JSON") or 0
    try:
        _, broken = _capture(cmd_version, ["--json"])
    finally:
        NATIVE.main = real
    chk("⑤ 前版 --json 輸出解析不了 → 原文放進 prior_text、整體仍是合法 JSON(不丟資料)", json.loads(broken).get("prior_text", "").strip() == "不是 JSON")
    rv, vout = _capture(cmd_version, [])
    chk("⑥ 文字模式:第一行標本版 v0287 與整條鏈 · 前版原生處理器那一行照留", rv == 0 and vout.startswith("[%s] VRN · 現役尾版 VRN_SystemManager_v0287.py" % TAG)
        and "鏈完整" in vout and "前版原生處理器 · [VRN_SystemManager v0269]" in vout, vout[:240])
    rh, hout = _capture(cmd_health, [])
    cr = chain_report()
    chk("⑦ 文字模式 health:判決行標本版 · 鏈 %d/%d 版 ✓(從本版算起)" % (cr["count"], cr["count"]),
        rh == 0 and "[%s] health GREEN" % TAG in hout and "鏈 %d/%d 版 ✓" % (cr["count"], cr["count"]) in hout and cr["tail"] == "v0287", hout[-300:])
    _, help_out = _capture(cmd_help)
    table = verb_table()
    chk("⑧ help 頂端標本版 · 每個動詞都列得到", help_out.startswith(TAG) and not PRIOR.help_coverage(help_out, table), PRIOR.help_coverage(help_out, table))
    got = {r["verb"]: r["top"] for r in table}
    chk("⑨ verbs:鏈從本版算起(version / health 最新處理版 = v0287)", got.get("version") == "v0287" and got.get("health") == "v0287" and got.get("verbs") == "v0287", got)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    peer = [k for k in ("VIA_FROM_VCGC", "VIA_FROM_VDFSM") if re.search(r"environ(?:\[[\"']%s[\"']\]\s*=|\.setdefault\([\"']%s)" % (k, k), body)]
    chk("⑩ 系統獨立:本版不替別的系統設入口旗標(VCGC / VDF 的旗標一個都不設)", not peer, peer)
    chk("⑪ 加速器橋在 · 不碰 TA-Lib · 不出網", "[VIA:ACCEL-BRIDGE:v0100]" in src and "talib" not in body.lower()
        and not re.search(r"^\s*(import|from)\s+(requests|urllib|socket|http)\b", src, re.M))
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑫ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), "%d 支" % len(pub))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
