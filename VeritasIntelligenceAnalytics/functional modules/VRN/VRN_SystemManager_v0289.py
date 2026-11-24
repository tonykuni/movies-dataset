#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0289 — 薄尾(v0287 以前一字不動;v0288 號被開著的 PR #722 佔用 → 本版取 v0289):自測在主機逾時 · bridges 網路橋誤判(操作員 2026-11-24 主機憲法矩陣)

  主機實跑 VIA_FiveSystemConstitution(2026-11-24 11:35):VRN v0287 --selftest 跑滿 900 秒逾時(容器 61~125 秒)。
  量測(容器 cProfile):自測一層套一層到 v0272(16 層),每層的 main() 都對引擎矩陣再掃一次 → 語法樹掃描 2591 次
  (引擎約 170 檔),佔 175 秒裡的 117 秒。v0286 的掃描快取存在檔案,但每層自測都把快取路徑換到新的暫存夾 → 層層冷啟。
  本版兩件事(只動 VRN 自己的範圍):
  ① 行程內掃描記憶:v0277 bridge_scan(純函數:同文字 + 同掃描規則 → 同結果)前面加一層記憶,同一行程同一份文字只掃一次;
     v0286 的檔案快取照舊(命中 / 未命中照算),只是未命中時不再重掃已掃過的文字。
  ② bridges 改用語法樹:v0269 的 v74_bridges 用字串搜尋找出網呼叫(只去掉註解與 docstring),
     VRN_MDL002_LayoutExtractor_v0101 自測裡的 "urlopen(" 字串被當成出網 → bridges YELLOW(net_callers 0/1)。
     本版:加速器 = 語法樹裡真的 import VIA_SuperAccel_Module;出網 = v0277 bridge_scan 的 net_libs(真的匯入網路套件 / 真的開 socket);
     網路橋 = 標記 [VIA:NET-BRIDGE] 或 bridge_scan 的 net_bridge。輸出鍵照 v0269,多 method / marker_only_accel 兩欄。
  version / health / help / verbs 照 v0287 的寫法(函式原樣沿用,現役尾版標本版)。其餘動詞照 v0287。
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
import re
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VRN_SystemManager"
TAG = "VRN_SystemManager v%04d" % int(re.search(r"_v(\d{4})$", Path(__file__).stem).group(1))


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0289", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
# 顯示函式的本體是 v0287(cmd_health · cmd_version …);在鏈上找「自己定義 cmd_health 的那一版」,不假設直接前版就是它
# (開著的 PR #722 若之後併進來、v0288 夾在中間,本版照樣接得上)。
P287 = next(m for m in PRIOR.chain_modules() if "cmd_health" in vars(m) and "health_extra" in vars(m))
P286 = P287.PRIOR                                     # v0287 的直接前版(鏈 / 動詞表 / 掃描快取的本體)
NATIVE = P287.NATIVE                                  # v0269 原生處理器
NATIVE_FLOOR = P287.NATIVE_FLOOR


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def chain_modules() -> list:
    return [sys.modules[__name__]] + PRIOR.chain_modules()


# v0287 的 version / health / help / verbs 原樣沿用:同一份程式碼,只把「本版」換成本版(TAG · 檔名 · 鏈從本版算起)。
_G = dict(vars(P287))
_G.update(TAG=TAG, __file__=__file__, __name__=__name__, PRIOR_PATH=PRIOR_PATH, chain_modules=chain_modules)
for _n in ("chain_report", "verb_table", "cmd_version", "health_extra", "cmd_health", "cmd_help", "cmd_verbs"):
    _f = vars(P287)[_n]
    _G[_n] = types.FunctionType(_f.__code__, _G, _n, _f.__defaults__, _f.__closure__)
    globals()[_n] = _G[_n]
_capture, _worst = P287._capture, P287._worst
VERSION = "v%04d" % _vnum(__file__)


# ─────────────────────────── ① 行程內掃描記憶 ───────────────────────────
SCAN_MOD = P286.SCAN_MOD                              # v0277(bridge_scan 本體所在)
_RAW = getattr(P286, "_RAW_SCAN", None)
MEMO = {"data": {}, "hits": 0, "misses": 0}


def _rules() -> str:
    return "%s|%s|%s|%s" % (getattr(SCAN_MOD, "ACCEL_MOD", ""), sorted(getattr(SCAN_MOD, "NET_TOP", ()) or ()),
                            tuple(getattr(SCAN_MOD, "NET_FULL", ()) or ()), sorted(getattr(SCAN_MOD, "SOCK_CALLS", ()) or ()))


def memo_scan(text: str) -> dict:
    """同一份文字 + 同一套掃描規則 → 同一行程只掃一次;回傳複本(呼叫端改了也不汙染記憶)。"""
    key = hashlib.sha256((_rules() + "\0" + text).encode("utf-8", "surrogatepass")).hexdigest()
    hit = MEMO["data"].get(key)
    if hit is None:
        MEMO["misses"] += 1
        hit = MEMO["data"][key] = json.loads(json.dumps(_RAW(text)))
    else:
        MEMO["hits"] += 1
    return json.loads(json.dumps(hit))


if _RAW is not None:
    P286._RAW_SCAN = memo_scan                        # v0286 bridge_scan 未命中時叫模組全域 _RAW_SCAN → 換上記憶版


# ─────────────────────────── ② bridges 改用語法樹 ───────────────────────────
BR_MOD = next((m for m in PRIOR.chain_modules() if "v74_bridges" in vars(m)), None)   # v0269
_RAW_BRIDGES = BR_MOD.v74_bridges if BR_MOD is not None else None


def ast_bridges(root: Path, engines: dict | None = None) -> dict:
    eng = BR_MOD.sm_engines(root) if engines is None else engines
    acc, net_need, net_have, miss_a, miss_n, marker_only, unreadable = 0, 0, 0, [], [], [], []
    scan = SCAN_MOD.bridge_scan
    for fam, f in eng.items():
        p = Path(root) / f["tail"]
        try:
            src = p.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            unreadable.append("%s:%s" % (p.name, type(exc).__name__))
            continue
        s = scan(src)
        if s.get("accel_import"):
            acc += 1
        else:
            miss_a.append(p.name)
            if "VIA:ACCEL-BRIDGE" in src:
                marker_only.append(p.name)                # 只有標記那一行 = 黃(CLAUDE.md 2026-11-18 補強三)
        if s.get("net_libs"):
            net_need += 1
            if "VIA:NET-BRIDGE" in src or s.get("net_bridge"):
                net_have += 1
            else:
                miss_n.append(p.name)
    exempt = set()
    bl = BR_MOD.v73_tail(Path(root) / "supportive modules" / "registry", "VIA_CeleritasPolicy_Baseline_v*.json") if engines is None else None
    with contextlib.suppress(ValueError, OSError, AttributeError):
        exempt = {Path(x).name for x in json.loads(bl.read_text(encoding="utf-8")).get("py_readonly", {}).get("files", [])} if bl else set()
    ex = sorted(x for x in miss_a + miss_n if x in exempt)
    miss_a = [x for x in miss_a if x not in exempt]
    miss_n = [x for x in miss_n if x not in exempt]
    lamp = "GREEN" if not miss_a and not miss_n and not unreadable else "YELLOW"
    return {"lamp": lamp, "accel": f"{acc}/{len(eng)}", "unreadable": unreadable[:20], "net_callers": f"{net_have}/{net_need}", "missing_accel": miss_a[:20], "missing_net": miss_n[:20],
            "exempt_readonly": sorted(set(ex)), "method": "ast(v0277 bridge_scan)", "marker_only_accel": marker_only[:20]}


if BR_MOD is not None:
    BR_MOD.v74_bridges = ast_bridges                  # v0269 bridges / status 叫模組全域 v74_bridges → 換上語法樹版


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
    import os
    import tempfile
    import time
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)

    # v0287 的自測假設自己是磁碟上最新那一版:測它時給它看「到 v0287 為止」的版名(同 v0287 測 v0286 的作法),測完換回。
    real_cr = P286.chain_report
    m0 = MEMO["misses"]
    t0 = time.time()
    with tempfile.TemporaryDirectory(prefix="via_vrn289_fam_") as fam:
        for p in HERE.glob(FAMILY + "_v*.py"):
            if 0 <= _vnum(p) <= _vnum(PRIOR_PATH):
                (Path(fam) / p.name).write_text("", encoding="utf-8")
        P286.chain_report = lambda mods=None, family_dir=None: real_cr(mods, fam if family_dir is None else family_dir)
        try:
            rc0, out0 = _capture(PRIOR.selftest)
        finally:
            P286.chain_report = real_cr
    secs0 = time.time() - t0
    print(f"=== {TAG} · 薄尾自測(行程內掃描記憶 · bridges 語法樹 · 前版原封不動;暫存夾 · 零網路)===")
    chk("⓪ 直接前版 %s 自測過(整條前版鏈 · %.0f 秒)" % (PRIOR_PATH.name, secs0), rc0 == 0, out0[-300:])
    raw_calls = MEMO["misses"] - m0
    chk("① 掃描記憶生效:前版整條鏈自測裡真的去掃的次數 %d · 記憶命中 %d(v0287 在容器要掃 2591 次)" % (raw_calls, MEMO["hits"]),
        P286._RAW_SCAN is memo_scan and MEMO["hits"] > 0 and raw_calls < 1200, MEMO)
    a = "import VIA_SuperAccel_Module as A\nimport requests\n"
    n1 = MEMO["misses"]
    r1, r2 = memo_scan(a), memo_scan(a)
    r1["net_libs"].append("x")
    chk("② 記憶版結果與原掃描器一字相同 · 同文字只掃一次 · 回傳複本(改了不汙染)",
        _RAW(a) == memo_scan(a) == r2 and MEMO["misses"] - n1 == 1 and "x" not in memo_scan(a)["net_libs"])
    with tempfile.TemporaryDirectory(prefix="via_vrn289_br_") as td:
        t = Path(td)
        acc = "# [VIA:ACCEL-BRIDGE:v0100]\nimport VIA_SuperAccel_Module as VIA_ACCEL\n"
        files = {
            "a_string_only.py": acc + "BAD = ('import urllib', 'urlopen(', 'requests.get(')\n",                 # MDL002 情境:只有字串
            "b_net_nobridge.py": acc + "import requests\nrequests.get('x')\n",
            "c_net_bridged.py": acc + "# [VIA:NET-BRIDGE:v0100]\nimport requests\n",
            "d_marker_only.py": "# [VIA:ACCEL-BRIDGE:v0100]\nx = 1\n",
        }
        for k, v in files.items():
            (t / k).write_text(v, encoding="utf-8")
        br = ast_bridges(t, {k: {"tail": k} for k in files})
    chk("③ 語法樹判出網:只有字串的不算(MDL002 誤判情境)· 真匯入沒橋 → 點名 · 有橋 → 算有",
        br["net_callers"] == "1/2" and br["missing_net"] == ["b_net_nobridge.py"], br)
    chk("④ 加速器以語法樹為準:只有標記沒匯入 → 缺 · 另列 marker_only_accel", br["accel"] == "3/4" and br["marker_only_accel"] == ["d_marker_only.py"], br)
    real = ast_bridges(BR_MOD.sm_root() if hasattr(BR_MOD, "sm_root") else HERE.parents[1])
    old = _RAW_BRIDGES(HERE.parents[1])
    chk("⑤ 真樹 bridges:語法樹版綠 · MDL002 不再被點名 · 加速器數 = 引擎數(v0269 字串版:%s · net %s)" % (old["lamp"], old["net_callers"]),
        real["lamp"] == "GREEN" and not any("MDL002" in x for x in real["missing_net"]) and real["accel"].split("/")[0] == real["accel"].split("/")[1], real)
    with tempfile.TemporaryDirectory(prefix="via_vrn289_c_") as td:
        keep = os.environ.get("VIA_VRN_SCAN_CACHE")
        os.environ["VIA_VRN_SCAN_CACHE"] = str(Path(td) / "cache.json")
        try:
            rvj, vj = _capture(cmd_version, ["--json"])
            rhj, hj = _capture(cmd_health, ["--json"])
        finally:
            if keep is None:
                os.environ.pop("VIA_VRN_SCAN_CACHE", None)
            else:
                os.environ["VIA_VRN_SCAN_CACHE"] = keep
    try:
        vjd, hjd = json.loads(vj), json.loads(hj)
    except ValueError:
        vjd, hjd = {}, {}
    chk("⑥ version / health --json 合法 JSON · 現役尾版 = 本版 · 鏈從本版算起且完整 · health 綠",
        rvj == 0 and vjd.get("live_tail", {}).get("version") == VERSION and (vjd.get("chain", {}).get("versions") or [None])[0] == VERSION
        and vjd.get("chain", {}).get("complete") is True and rhj == 0 and hjd.get("lamp") == "GREEN", (vj[:160], hj[:160]))
    got = {r["verb"]: r["top"] for r in verb_table()}
    chk("⑦ verbs:version / health / verbs 最新處理版 = 本版 %s" % VERSION, got.get("version") == VERSION and got.get("health") == VERSION and got.get("verbs") == VERSION, got)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    peer = [k for k in ("VIA_FROM_VCGC", "VIA_FROM_VDFSM") if re.search(r"environ(?:\[[\"']%s[\"']\]\s*=|\.setdefault\([\"']%s)" % (k, k), body)]
    chk("⑧ 系統獨立:本版不替別的系統設入口旗標", not peer, peer)
    chk("⑨ 加速器橋在 · 不碰 TA-Lib · 不出網", "[VIA:ACCEL-BRIDGE:v0100]" in src and "talib" not in body.lower()
        and not re.search(r"^\s*(import|from)\s+(requests|urllib|socket|http)\b", src, re.M))
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑩ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), "%d 支" % len(pub))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
