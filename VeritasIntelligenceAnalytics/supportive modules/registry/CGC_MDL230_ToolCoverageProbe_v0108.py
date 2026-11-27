#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL230_ToolCoverageProbe v0108 — 薄尾(v0100–v0107 一字不動):自測改在暫存樹上比對,不再把前版鏈在真樹上跑兩遍

主機 2026-11-27 實錄(VCGC 快測):`upd:CGC_MDL230_ToolCoverageProbe_v0107 rc 124 · 1216.4s · TIMEOUT` → 串測紅站。
原因:v0107 的自測 T1 為了證明「快取 / 並行不改判定」,把前版 v0106 的整條鏈自測跑兩遍(子行程一遍 + 本行程一遍),
     每一遍都掃整棵真樹(容器 9 分 35 秒;工作倉在 OneDrive 上超過 20 分鐘)。而且它吃本機狀態:真樹長什麼樣,自測就算什麼。
本版(判法 · matrix · 快取 · 並行一行不改,全部沿用 v0107):
  ① --selftest:在暫存夾造一棵小樹(版號檔 · 無版號檔 · 剖析不過的檔 · CRLF 檔 · PS 檔),拿「原判法 matrix」與「v0107 快取版 matrix」逐欄比;
     第二遍要全由快取取而且結果相同。不讀真樹、不寫真的快取檔。
  ② --selftest --full:照舊跑 v0107 的自測(前版鏈在真樹上跑兩遍)。要拿真樹當對照時才用,時間以十分鐘計。
  ③ 其餘動詞原樣交給 v0107。
  ④ 並行照舊:v0107 的 _can_pool 在 Windows(spawn)只認「主程式就是 v0107」;本版當主程式時要自己接上,不然主機冷跑會退回逐檔算。
     spawn 的子行程會重跑本檔 → 本檔載入 v0107 → 工人函式照模組名找得到。
用法:VIA_FROM_VCGC=YES python CGC_MDL230_ToolCoverageProbe_v0108.py matrix [--no-pwsh] [--json] · --selftest [--full]
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

import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "CGC_MDL230_ToolCoverageProbe"
ENGINE_TAG = "CGC_MDL230_ToolCoverageProbe v0108"
VERBS = ("matrix", "--selftest", "--selftest --full")
FAST_BUDGET_S = 120          # 快自測的時間上限(秒);超過 = 這一版的目的沒達到
VOLATILE = ("speed", "ts_utc")   # 兩次 matrix 之間本來就會不同的欄(計時 · 時間戳)


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0108", PRIOR_PATH)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(_PRIOR, name)


def _main_is_me() -> bool:
    f = getattr(sys.modules.get("__main__"), "__file__", None)
    return bool(f and Path(f).resolve() == Path(__file__).resolve())


def _can_pool() -> bool:
    """能不能起行程池。fork 平台照 v0107;spawn(Windows)要主程式是本檔(子行程重跑本檔才載得到 v0107 的工人函式)。"""
    if os.environ.get("VIA_MDL230_SERIAL") == "1":
        return False
    import multiprocessing as mp
    if mp.get_start_method(allow_none=True) in (None, "fork") and sys.platform != "win32":
        return True
    return _main_is_me()


_PRIOR._can_pool = _can_pool          # v0107 的 warm() 從它自己的全域取這個名字


def route(a: list) -> str:
    """參數 → 走哪一條:fast(本版快自測)· full(v0107 的整鏈自測)· prior(其餘原樣轉交)。"""
    if "--selftest" in a or a[:1] in (["selftest"], ["test"]):
        return "full" if "--full" in a else "fast"
    return "prior"


def build_fixture(root: Path) -> list:
    """在 root 底下造一棵小樹;回寫出的相對路徑。內容全是合成的,不取自真樹。"""
    files = {
        "functional modules/VDF/VDF_ENG900_Fixture_v0100.py":
            '"""fx:直接出網、沒有橋。"""\nimport requests\n\n\ndef fetch_data():\n    return requests.get("https://example.invalid")\n',
        "functional modules/VDF/VDF_ENG900_Fixture_v0101.py":
            '# -*- coding: utf-8 -*-\n# x\n# [VIA:ACCEL-BRIDGE:v0111]\n"""fx:有橋。"""\ntry:\n    import VIA_SuperAccel_Module as VIA_ACCEL\n'
            'except Exception:\n    VIA_ACCEL = None\n\n\nclass Repo:\n    def load(self):\n        return 1\n',
        "functional modules/VRN/VRN_ENG900_Fixture_v0100.py": '"""fx:只有定義。"""\ndef parse_report(x):\n    return x\n',
        "supportive modules/registry/CGC_MDL900_Broken_v0100.py": "def f(:\n",
        "supportive modules/registry/CGC_MDL901_Crlf_v0100.py": '"""fx:CRLF 換行。"""\r\nimport json\r\n\r\ndef dump(x):\r\n    return json.dumps(x)\r\n',
        "supportive modules/registry/unversioned_helper.py": "X = 1\n",
        "supportive modules/registry/Fx-Tool-v0100.ps1": "function Get-Fx { param($a) Write-Output $a }\n",
        "supportive modules/registry/Fx-Old.ps1": "Write-Output 'old'\n",
    }
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))
    return sorted(files)


def _stable(rep: dict) -> dict:
    return {k: v for k, v in rep.items() if k not in VOLATILE}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "ABSENT"


def selftest() -> int:
    ok = []
    t_start = time.time()

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print(f"[計] {ENGINE_TAG} 自測開始(暫存樹 · 不讀真樹 · 零網路;整鏈對照用 --selftest --full)", flush=True)
    import contextlib
    import io
    P = _PRIOR
    real_cache = P.CACHE_PATH
    real_cache_sha = _sha(real_cache)
    ssot, _n = P.M_AST.load_ssot()
    cats = P.M_DESC.categories()
    with tempfile.TemporaryDirectory(prefix="mdl230_108_") as td:
        fx = Path(td) / "VeritasIntelligenceAnalytics"
        made = build_fixture(fx)
        P.CACHE_PATH = Path(td) / "cache.json"
        try:
            sink = io.StringIO()
            with contextlib.redirect_stdout(sink):
                hooked = (P.M_AST.py_ast, P.M_DESC.describe)
                P.M_AST.py_ast, P.M_DESC.describe = P._ORIG_PY_AST, P._ORIG_DESCRIBE     # 對照組:把 v0107 的掛鉤拆掉,真的走原判法
                try:
                    orig = P._ORIG_MATRIX(fx, ssot=None, no_pwsh=True)
                finally:
                    P.M_AST.py_ast, P.M_DESC.describe = hooked
                cold = P.matrix(fx, None, True)                             # v0107:沒快取
                cold_stats = dict(P.STATS)
                warm = P.matrix(fx, None, True)                             # v0107:全由快取
                warm_stats = dict(P.STATS)
                raw = json.loads(P.CACHE_PATH.read_text(encoding="utf-8"))
                flipped = sum(1 for v in raw.values() if isinstance(v, dict) and isinstance(v.get("accel"), bool))
                for v in raw.values():
                    if isinstance(v, dict) and isinstance(v.get("accel"), bool):
                        v["accel"] = not v["accel"]
                P.CACHE_PATH.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
                poisoned = P.matrix(fx, None, True)                         # 反控:快取被改壞,比對要抓得到
                P.CACHE_PATH.unlink()                                       # 改壞的快取用完就丟,後面幾項從空的開始
                P._load_cache()
            rows = orig.get("rows") or []
            chk("S1 暫存樹真的被掃到(列數 > 0 · 造了 %d 檔)" % len(made), len(rows) > 0 and len(made) == 8, (len(rows), made))
            diff = [k for k in _stable(orig) if _stable(orig)[k] != _stable(cold).get(k)] + [k for k in _stable(cold) if k not in orig]
            chk("S2 v0107 快取版 matrix 與原判法逐欄相同(只有計時 · 時間戳兩欄不比)", not diff, diff)
            chk("S2b 反控:把快取裡 %d 筆的加速器判定反過來,同一個比對就不相同(比對不是擺著好看的)" % flipped,
                flipped > 0 and _stable(poisoned) != _stable(orig), flipped)
            chk("S3 第一遍沒有命中、第二遍全由快取取,結果與第一遍相同",
                cold_stats["hit"] == 0 and cold_stats["par"] + cold_stats["serial"] > 0
                and warm_stats["hit"] == cold_stats["par"] + cold_stats["serial"] and warm_stats["par"] + warm_stats["serial"] == 0
                and _stable(warm) == _stable(cold), (cold_stats, warm_stats))
            samples = ['"""d."""\nimport requests\nVIA_ACCEL.x()\n', "x = 1\n", "def f(:\n", '"""doc."""\ndef fetch_data():\n    pass\nclass Repo:\n    pass\n',
                       '"""crlf."""\r\nimport json\r\n']
            a1 = [P.py_ast(s, ssot) for s in samples]
            d1 = [P.describe(s, cats) for s in samples]
            chk("S4 逐檔判讀與原判法相同(py_ast · describe;含剖析不過的檔與 CRLF 檔)",
                a1 == [P._ORIG_PY_AST(s, ssot) for s in samples] and d1 == [P._ORIG_DESCRIBE(s, cats) for s in samples])
            cfg2 = dict(ssot, ast=dict(ssot["ast"], py_net_need_mods=list(ssot["ast"]["py_net_need_mods"]) + ["zzz_fx"]))
            chk("S5 設定一改鍵就變(不拿舊設定的結果)",
                P._key(P._cfg_key("ast", cfg2["ast"]), samples[0]) != P._key(P._cfg_key("ast", ssot["ast"]), samples[0]))
            jobs = [("ast", "k%d" % i, samples[i % 4] + f"# {i}\n", ssot) for i in range(48)]
            from concurrent.futures import ProcessPoolExecutor
            if _main_is_me():
                import multiprocessing as mp
                with ProcessPoolExecutor(max_workers=2, mp_context=mp.get_context("spawn")) as ex:      # Windows 的起法,任何平台都照這條測
                    par = dict(ex.map(P._work, jobs, chunksize=8))
                how = "spawn 2 道"
            elif P._can_pool():
                with ProcessPoolExecutor(max_workers=2) as ex:
                    par = dict(ex.map(P._work, jobs, chunksize=8))
                how = "行程池 2 道"
            else:
                par = dict(map(P._work, jobs))
                how = "行程池起不來,逐檔算"
            chk("S6 並行算的結果與逐檔算相同(48 檔 · %s)" % how, par == {k: P._ORIG_PY_AST(t, c) for _kind, k, t, c in jobs})
            chk("S6b 本版當主程式時行程池起得來(v0107 的 warm 取到的是本版的判法)", P._can_pool is _can_pool and (_can_pool() or not _main_is_me()))
        finally:
            P.CACHE_PATH = real_cache
            P._load_cache()
    chk("S7 真的快取檔沒被這次自測動到(前後雜湊相同)", _sha(real_cache) == real_cache_sha, (real_cache_sha[:12], _sha(real_cache)[:12]))
    calls = []
    keep = P.selftest
    P.selftest = lambda: calls.append("full") or 7
    try:
        rc_full = main(["--selftest", "--full"])
    finally:
        P.selftest = keep
    chk("S8 分流:--selftest 走本版 · --selftest --full 走 v0107 整鏈(rc 原樣帶回)· 其餘轉交",
        route(["--selftest"]) == "fast" and route(["selftest"]) == "fast" and route(["--selftest", "--full"]) == "full"
        and route(["matrix", "--no-pwsh"]) == "prior" and calls == ["full"] and rc_full == 7, (calls, rc_full))
    lost = [n for n in dir(P) if not n.startswith("_") and callable(getattr(P, n)) and not hasattr(sys.modules[__name__], n)]
    chk("S9 前版公開名稱都還拿得到(經本檔轉接)", not lost and callable(sys.modules[__name__].matrix), lost[:6])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("S10 第 3 行加速器標記且載入生效(VIA_ACCEL 非空)· 零 TA-Lib · 不 import 他系統",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_ACCEL is not None
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and not re.search(r"^\s*(import|from)\s+(VDF|VRN|VQG|VAP)", src, re.M),
        "VIA_ACCEL %s" % (VIA_ACCEL is not None))
    took = time.time() - t_start
    chk("S11 快自測在 %d 秒內跑完(v0107 整鏈:容器 575 秒 · 主機逾時 1216 秒)" % FAST_BUDGET_S, took < FAST_BUDGET_S, round(took, 1))
    print(f"[計] {ENGINE_TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'} · {took:.1f}s", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    way = route(a)
    if way == "fast":
        return selftest()
    if way == "full":
        return _PRIOR.selftest()
    return _PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
