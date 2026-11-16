#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VIA_NearCompleteLock v0101 — 薄尾:入口雜湊改用跨平台的標準位元組(CRLF → LF 後再算 SHA-256)。

為什麼(PR 635 · Codex P2,容器實測屬實):v0100 的 `sha256_file` 直接雜湊工作樹原始位元組。Windows 工作站(CRLF)
建的鎖,拿到 Linux 容器(LF)`check`,三個入口版本都沒變(VCGC v0192 · VDF v0177 · VRN-2 v0262)卻全報「漂移」;
反過來容器建的鎖在工作站也一樣。里程碑本身鎖的是 git tree / blob 雜湊,本來就跨平台,只有「目前狀態」這一段受影響。

本版(v0100 一字不動;只換兩個函式):
  · sha256_file:先把 CRLF 換成 LF 再算(同 FreezeLock 的雜湊規則)→ 之後 build 出的鎖,兩個平台算出同一個值。
  · check:漂移判定多一層「同一個入口檔、只差換行」容忍——鎖上的值等於該檔的標準 / 原始 / CRLF 版任一雜湊,就不算漂移;
    舊鎖(v0100 在 Windows 或 Linux 建的)照樣能驗,不必重新上鎖。真的換版或改了內容照舊報 YELLOW 漂移。
其餘(build · 里程碑 tree / blob 重驗 · 指紋 · md)照 v0100。只用標準庫 + git;不 import 任何系統模組;不用 TA-Lib。
用法同 v0100:python VIA_NearCompleteLock_v0101.py build --milestones <json> [--vrn1 <倉>] · check [--lock <json>] [--vrn1 <倉>] · --selftest
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "v0101"
TAG = "VIA_NearCompleteLock " + VERSION
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})\.py$", str(p))
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob("VIA_NearCompleteLock_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("NearCompleteLock_prior_for_" + VERSION, PRIOR_PATH)
P = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = P
_spec.loader.exec_module(P)
_SHA_V0100 = P.sha256_file
_CHECK_V0100 = P.check
_TAG_V0100 = P.TAG


def _canon(b: bytes) -> bytes:
    return b.replace(b"\r\n", b"\n")


def sha256_file(p: Path) -> str:
    """標準位元組雜湊:CRLF → LF 後再算(Windows / Linux 工作樹算出同一個值)。"""
    return hashlib.sha256(_canon(Path(p).read_bytes())).hexdigest()


def entry_hashes(p: Path) -> set:
    """同一個檔在三種換行表示下的雜湊:標準(LF)· 原始 · CRLF。舊鎖用哪一種都認得出來。"""
    raw = Path(p).read_bytes()
    c = _canon(raw)
    return {hashlib.sha256(c).hexdigest(), hashlib.sha256(raw).hexdigest(), hashlib.sha256(c.replace(b"\n", b"\r\n")).hexdigest()}


def check(lock_path: Path, via_root: Path, vrn1: Path | None) -> dict:
    r = _CHECK_V0100(lock_path, via_root, vrn1)
    lock = json.loads(Path(lock_path).read_text(encoding="utf-8"))
    cur = lock.get("current") or {}
    keep = []
    for d in r["drift"]:
        s = d.split(" 入口 ", 1)[0] if " 入口 " in d else None
        v = cur.get(s) if s else None
        if v and v.get("entry") and v.get("entry_sha256") and s in P.ENTRIES:
            locked_entry = Path(via_root) / v["entry"]
            now_entry = P.tail(Path(via_root), P.ENTRIES[s])
            if now_entry is not None and locked_entry.is_file() and locked_entry.resolve() == Path(now_entry).resolve() \
                    and v["entry_sha256"] in entry_hashes(locked_entry):
                continue                                   # 同一個入口檔,只差換行(鎖在另一平台建)→ 不算漂移
        keep.append(d)
    r["drift"] = keep
    r["lamp"] = "RED" if r["bad"] else ("YELLOW" if keep else "GREEN")
    return r


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱(build · current_state · git · tail · render_md …)經本檔轉接。"""
    return getattr(P, name)


P.sha256_file = sha256_file                                # build / current_state 都經它 → 新鎖存標準雜湊
P.check = check                                            # v0100 main() 依模組全域名找 check → 本版接手
P.TAG = TAG                                                # 新鎖的 tool 欄記本版


def selftest() -> int:
    ok = total = 0

    def chk(name, cond, note=""):
        nonlocal ok, total
        total += 1
        ok += bool(cond)
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:300]) if note and not cond else ""), flush=True)
    print("[%s selftest]" % TAG, flush=True)
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        f1, f2 = t / "a_lf.py", t / "a_crlf.py"
        f1.write_bytes(b"x = 1\ny = 2\n")
        f2.write_bytes(b"x = 1\r\ny = 2\r\n")
        chk("① 標準雜湊:同內容 LF 與 CRLF 算出同一個值 · 三種表示都認得", sha256_file(f1) == sha256_file(f2)
            and _SHA_V0100(f2) in entry_hashes(f1) and _SHA_V0100(f1) in entry_hashes(f2))
        repo = t / "movies-dataset"
        via = repo / "VeritasIntelligenceAnalytics"
        for d in ("functional modules/VDF", "functional modules/VRN", "supportive modules/registry"):
            (via / d).mkdir(parents=True)
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}

        def g(*a):
            subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, env=env)
        g("init", "-q")
        vdf = via / "functional modules/VDF/VDF_SystemManager_v0100.py"
        vdf.write_bytes(b"print('v0100')\nx = 1\n")
        (via / "functional modules/VRN/VRN_SystemManager_v0200.py").write_bytes(b"print('v0200')\n")
        (via / "supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0100.py").write_bytes(b"x=1\n")
        g("add", "-A")
        g("commit", "-q", "-m", "near-complete")
        c1 = P.git(repo, "rev-parse", "HEAD")
        mp = t / "ms.json"
        mp.write_text(json.dumps({"systems": {"VDF": {"milestones": [{"commit": c1, "entry": "VDF_SystemManager_v0100", "lamp": "GREEN"}]}}}),
                      encoding="utf-8")
        out = t / "out"
        vdf.write_bytes(b"print('v0100')\r\nx = 1\r\n")                     # 工作樹是 CRLF(像 Windows)
        lock = P.build(mp, via, None, out)
        chk("② build(CRLF 工作樹)存的是標準雜湊(= LF 內容的雜湊)· tool 欄記本版",
            lock["current"]["VDF"]["entry_sha256"] == hashlib.sha256(b"print('v0100')\nx = 1\n").hexdigest() and lock["tool"] == TAG)
        vdf.write_bytes(b"print('v0100')\nx = 1\n")                         # 同一份鎖拿到 LF 工作樹(像 Linux)
        r = check(out / P.LOCK_NAME, via, None)
        chk("③ 新鎖跨平台:CRLF 建 · LF 驗 → GREEN 沒有漂移", r["lamp"] == "GREEN" and not r["drift"], r)
        lk = json.loads((out / P.LOCK_NAME).read_text(encoding="utf-8"))
        lk["current"]["VDF"]["entry_sha256"] = hashlib.sha256(b"print('v0100')\r\nx = 1\r\n").hexdigest()   # 模擬 v0100 在 Windows 建的舊鎖
        legacy = t / "legacy.json"
        legacy.write_text(json.dumps(lk, ensure_ascii=False), encoding="utf-8")
        r_old = _CHECK_V0100(legacy, via, None)
        r_new = check(legacy, via, None)
        chk("④ 舊鎖(v0100 · Windows CRLF 雜湊)在 LF 工作樹:v0100 誤報漂移 · 本版 GREEN",
            any(d.startswith("VDF 入口") for d in r_old["drift"]) and r_new["lamp"] == "GREEN" and not r_new["drift"], (r_old["drift"], r_new))
        vdf.write_bytes(b"print('v0100')\nx = 2\n")                         # 同版號、內容真的改了
        r2 = check(out / P.LOCK_NAME, via, None)
        chk("⑤ 內容真的改了(同版號)→ 照舊 YELLOW 漂移", r2["lamp"] == "YELLOW" and any(d.startswith("VDF 入口") for d in r2["drift"]), r2)
        vdf.write_bytes(b"print('v0100')\nx = 1\n")
        (via / "functional modules/VDF/VDF_SystemManager_v0101.py").write_bytes(b"print('v0101')\n")
        r3 = check(out / P.LOCK_NAME, via, None)
        chk("⑥ 入口往前換版 → 照舊 YELLOW 漂移", r3["lamp"] == "YELLOW" and any("v0100 → v0101" in d for d in r3["drift"]), r3["drift"])
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([\w.]+)", src, re.M)
    chk("⑦ 獨立:只用標準庫(不 import VCGC / VDF / VRN 任何模組 · 不用 TA-Lib)",
        not any(x.lower().startswith(("cgc", "vdf", "vrn", "via_", "talib")) for x in imports), sorted(set(imports)))
    print("  前版 %s selftest ↓" % PRIOR_PATH.name, flush=True)
    P.sha256_file, P.check, P.TAG = _SHA_V0100, _CHECK_V0100, _TAG_V0100      # 前版自測照前版原行為跑
    try:
        prior_rc = P.selftest()
    finally:
        P.sha256_file, P.check, P.TAG = sha256_file, check, TAG
    chk("⑧ 前版 v0100 自測照過", prior_rc == 0, prior_rc)
    print("[%s] %s selftest · %d/%d" % ("PASS" if ok == total else "FAIL", TAG, ok, total), flush=True)
    return 0 if ok == total else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a or a[:1] == ["selftest"]:
        return selftest()
    return P.main(a)


if __name__ == "__main__":
    sys.exit(main())
