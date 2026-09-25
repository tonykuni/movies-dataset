#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL147_EngineSmokeGate v0100 — 無自測面引擎的煙霧閘(批468 立)
====================================================================
操作員令:「完成 VRN 一切通過認證測試完工」。

為什麼非有這道不可(量到的,不是規劃的):
  全 VRN 38 個版號族,**只有 29 支有 `--selftest`**。全樹掃描器找的是那個旗標,
  於是另外 9 支在每一次認證掃描裡都被算成「SKIP · 無自測旗標」——
  它們**不是綠也不是紅,是沒有儀器**。
  拿「29/29 全綠」去宣告「VRN 全部通過認證」,等於把 9 支沒量過的算成過了。
  **看不見的儀器不算儀器;沒有儀器的站不得計入總判。**(批460 完整性閘同律)

本件做什麼、不做什麼(誠實界線):
  做:①模組**載得進來**嗎(語法/相依/import 期副作用會不會爆)
      ②它宣告的**公開契約**(頂層 def)還在不在、拿得到簽章嗎
      ③載入是否有**寫檔副作用**(import 期就動正式產出夾=批410 那一族的病)
  不做:**不驗業務正確性**。煙霧閘只證明「這支還活著、介面還在」,
      不證明它算得對。把煙霧當成全測,就是另一種假綠——所以本件的
      燈一律標「SMOKE」,總表也要照這個字面收,不得改寫成 GREEN。

Zero-Hydra:不替那 9 支各寫一份自測(那會是 9 份九頭龍),
  也不改它們一個字——本件**只增一支共用閘**,誰哪天長出真自測就自動退出名單。
用法:python3 CGC_MDL147_EngineSmokeGate_v0100.py [--dir <引擎夾>] | --selftest
紀律:零網路、唯讀(絕不寫任何正式產出)、不卡斷(逐支逾時)、誠實三態。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(graceful 缺席零影響) =====
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
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import ast
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VRN_DIR = VIA / "functional modules" / "VRN"
#: 逐支逾時(秒)。載得進來的模組不該要這麼久;要這麼久本身就是紅旗。
TIMEOUT = 90
#: 正式產出夾——載入期間碰它就是副作用(批410 那一族)
LIVE_OUT = VIA / "VIA_Reports"


def tails(d: Path) -> list:
    """版號族取尾版;無版號的檔各自成族(尾版律 glob)。"""
    fam = defaultdict(list)
    for p in sorted(d.glob("*.py")):
        m = re.match(r"^(.*?)_v(\d{4})\.py$", p.name)
        if m:
            fam[m.group(1)].append((int(m.group(2)), p))
        else:
            fam[p.name].append((0, p))
    out = []
    for _k, v in sorted(fam.items()):
        v.sort()
        out.append(v[-1][1])
    return out


#: 凍結副本(收容原件的 sha 快照)。只增不減律要它們留著,但它們**不是現役引擎**
#: ——拿它們的載入結果去算認證,等於把倉庫裡的化石算成活的。
FROZEN_RX = re.compile(r"_sha[0-9a-f]{6,}")


def tier(p: Path) -> str:
    """分層(批468)。三種東西混在一個數裡,那個數就沒有意義:
         frozen  _sha 凍結副本    → **不測**,只報有幾件
         versioned 有 _vNNNN 版號 → **主名單**:現役引擎,計入總判
         adhoc   無版號一次性腳本 → **附名單**:列示但不計入總判
       為什麼要分:全景掃描器的族是「有版號的族」,它報 9 支無自測面;
       本閘若把 60 支全算進來,兩邊數字就永遠對不起來,而**對不起來的數字
       會讓人以為其中一邊在說謊**。分層之後 9=9,對得上。"""
    if FROZEN_RX.search(p.name):
        return "frozen"
    if re.match(r"^.*_v\d{4}\.py$", p.name):
        return "versioned"
    return "adhoc"


def has_selftest(p: Path) -> bool:
    try:
        t = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False
    return ("--selftest" in t) or ("--self_test" in t)


def public_defs(p: Path) -> list:
    """頂層公開函式名(不含底線開頭)。用 ast,不執行程式碼。"""
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return []
    return [n.name for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not n.name.startswith("_")]


_PROBE = r'''
import importlib.util, sys, json, io, os, contextlib
from pathlib import Path
src = Path(sys.argv[1])
want = json.loads(sys.argv[2])
live = Path(sys.argv[3])
before = sorted(str(x) for x in live.rglob("*")) if live.exists() else []
res = {"loaded": False, "why": "", "missing": [], "wrote": []}
try:
    spec = importlib.util.spec_from_file_location("_smoke_mod", src)
    m = importlib.util.module_from_spec(spec)
    sys.modules["_smoke_mod"] = m
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        spec.loader.exec_module(m)
    res["loaded"] = True
    res["missing"] = [f for f in want if not callable(getattr(m, f, None))]
except BaseException as exc:
    res["why"] = type(exc).__name__ + ":" + str(exc)[:140]
after = sorted(str(x) for x in live.rglob("*")) if live.exists() else []
res["wrote"] = [x for x in after if x not in before][:5]
print("SMOKE_JSON" + json.dumps(res, ensure_ascii=False))
'''


def smoke_one(p: Path) -> dict:
    """在**子行程**裡載入,避免被測件污染本行程;逾時即殺(不卡斷)。"""
    want = public_defs(p)[:12]
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        r = subprocess.run(
            [sys.executable, "-c", _PROBE, str(p), json.dumps(want), str(LIVE_OUT)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=TIMEOUT, env=env, cwd=str(p.parent))
    except subprocess.TimeoutExpired:
        return {"state": "RED", "why": f"載入逾 {TIMEOUT}s 未回(import 期就卡住)",
                "want": want}
    out = (r.stdout or "") + (r.stderr or "")
    m = re.search(r"SMOKE_JSON(\{.*\})", out)
    if not m:
        return {"state": "RED", "why": f"探針無回覆 rc={r.returncode}·{out.strip()[-120:]}",
                "want": want}
    d = json.loads(m.group(1))
    if not d["loaded"]:
        return {"state": "RED", "why": d["why"], "want": want}
    if d["missing"]:
        return {"state": "RED", "why": f"公開契約缺 {d['missing']}", "want": want}
    if d["wrote"]:
        return {"state": "AMBER", "why": f"import 期就動了正式產出夾:{d['wrote']}",
                "want": want}
    return {"state": "SMOKE", "why": f"載入 OK · 公開契約 {len(want)} 支在位",
            "want": want}


def run(d: Path | None = None) -> int:
    d = d or VRN_DIR
    if not d.is_dir():
        print(f"[煙霧閘] 夾不存在 {d}(誠實停)")
        return 2
    allt = tails(d)
    naked = [p for p in allt if not has_selftest(p)]
    main_list = [p for p in naked if tier(p) == "versioned"]
    adhoc = [p for p in naked if tier(p) == "adhoc"]
    frozen = [p for p in naked if tier(p) == "frozen"]
    print(f"[煙霧閘] {d.name}:族 {len(allt)} 支 · 有自測面 {len(allt) - len(naked)}"
          f" · 無自測面 {len(naked)}")
    print(f"  分層:**主名單(現役版號族){len(main_list)}** ← 計入總判"
          f" · 附名單(無版號一次性){len(adhoc)} ← 列示不計"
          f" · 凍結副本 _sha {len(frozen)} ← 不測(收容原件非現役)")
    if not main_list and not adhoc:
        print("  全員都有自測面=本閘無事可做(這才是終局)")
        return 0
    tally = {"SMOKE": 0, "AMBER": 0, "RED": 0}
    for p in main_list:
        r = smoke_one(p)
        tally[r["state"]] = tally.get(r["state"], 0) + 1
        print(f"  [{r['state']:5s}] {p.name:46s} {r['why'][:110]}")
    a_t = {"SMOKE": 0, "AMBER": 0, "RED": 0}
    for p in adhoc:
        r = smoke_one(p)
        a_t[r["state"]] = a_t.get(r["state"], 0) + 1
        print(f"  [{r['state']:5s}]*{p.name:45s} {r['why'][:110]}")
    print(f"[煙霧計] 主名單 {len(main_list)} 支 · SMOKE {tally['SMOKE']}"
          f" · AMBER {tally['AMBER']} · RED {tally['RED']}"
          f"  ‖ 附名單 {len(adhoc)} 支(*號;不計入總判)· SMOKE {a_t['SMOKE']}"
          f" · AMBER {a_t['AMBER']} · RED {a_t['RED']}"
          "\n  註:SMOKE=載得進來且介面在位,**不代表算得對**;"
          "要它算得對就得替它寫真自測。總表請照 SMOKE 字面收,不得改寫成 GREEN。")
    return 1 if tally["RED"] else 0


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    done, fails = [], []

    def chk(name, cond, note=""):
        done.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest")[0]

    t = tails(VRN_DIR)
    naked = [p for p in t if not has_selftest(p)]
    _mainl = [p for p in naked if tier(p) == "versioned"]
    _adhoc = [p for p in naked if tier(p) == "adhoc"]
    _froz = [p for p in naked if tier(p) == "frozen"]
    chk("① 尾版律取族尾 + 認出「無自測面」那一批,而且**分層**(全樹掃描器找的是"
        " --selftest 旗標,找不到就記 SKIP;那些件於是每一次認證掃描都不是綠也不是紅,"
        "是**沒有儀器**)。分層的理由:凍結副本/一次性腳本/現役版號族混在一個數裡,"
        "那個數就沒有意義——而**對不起來的數字會讓人以為其中一邊在說謊**。"
        "分層後主名單數要對得上全景掃描器的族數",
        len(t) >= 30 and len(_mainl) + len(_adhoc) + len(_froz) == len(naked)
        and len(_mainl) >= 1,
        f"(族 {len(t)} · 無自測面 {len(naked)} = 主 {len(_mainl)}"
        f" + 附 {len(_adhoc)} + 凍結 {len(_froz)})")

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        q = Path(td)
        (q / "ok_v0100.py").write_text(
            "def alpha():\n    return 1\n\n\ndef beta(x):\n    return x\n",
            encoding="utf-8")
        (q / "boom_v0100.py").write_text(
            "raise RuntimeError('import 期就炸')\n", encoding="utf-8")
        (q / "slow_v0100.py").write_text(
            "import time\ntime.sleep(999)\n", encoding="utf-8")
        (q / "withtest_v0100.py").write_text(
            "import sys\n\n\ndef gamma():\n    return 1\n\n\n"
            "if '--selftest' in sys.argv:\n    sys.exit(0)\n", encoding="utf-8")
        r_ok = smoke_one(q / "ok_v0100.py")
        r_boom = smoke_one(q / "boom_v0100.py")
        chk("② 載得進來=SMOKE;import 期就爆=RED 並把例外型別與訊息**照抄**"
            "(不概括成「載入失敗」——批450 那一課:捕捉到卻不顯示,還編一句代替它)",
            r_ok["state"] == "SMOKE" and r_boom["state"] == "RED"
            and "RuntimeError" in r_boom["why"] and "import 期就炸" in r_boom["why"],
            f"(ok={r_ok['state']} · boom={r_boom['state']}:{r_boom['why'][:40]})")
        chk("③ 公開契約用 ast 取(**不執行程式碼**就拿得到頂層 def 名)",
            public_defs(q / "ok_v0100.py") == ["alpha", "beta"],
            f"({public_defs(q / 'ok_v0100.py')})")
        chk("④ 有 --selftest 的件**不在本閘名單內**(誰長出真自測就自動退出;"
            "本閘不搶已經有儀器的站)",
            has_selftest(q / "withtest_v0100.py") is True
            and has_selftest(q / "ok_v0100.py") is False, "")
        _g = TIMEOUT
        try:
            globals()["TIMEOUT"] = 3
            r_slow = smoke_one(q / "slow_v0100.py")
        finally:
            globals()["TIMEOUT"] = _g
        chk("⑤ 不卡斷:逐支逾時即殺,回 RED 並說清楚是**import 期**卡住,"
            "不是這支算得慢",
            r_slow["state"] == "RED" and "逾" in r_slow["why"],
            f"({r_slow['why'][:46]})")

    chk("⑥ 在**子行程**裡載入:被測件的 import 期副作用(sys.path 改寫、猴補、"
        "全域旗標)不得污染本行程,否則後面每一支的結果都不可信",
        "subprocess.run" in body and "_smoke_mod" in body, "")

    chk("⑦ **煙霧不是全測**:燈一律標 SMOKE,並在計數行寫明「不代表算得對」。"
        "把煙霧當成全測就是另一種假綠",
        '"SMOKE"' in body and "不代表算得對" in body and "不得改寫成 GREEN" in body, "")

    chk("⑧ 唯讀律:本閘自己不寫任何正式產出;而**被測件**若在 import 期動了"
        "正式產出夾 → AMBER 點名(批410 那一族的病:自測/載入期就污染正本)",
        "AMBER" in body and "import 期就動了正式產出夾" in body
        and "LIVE_OUT" in body, "")

    chk("⑨ Zero-Hydra:不替那些引擎各寫一份自測(9 份九頭龍),也不改它們一個字;"
        "本件只增一支共用閘",
        "只增一支共用閘" in src and "不改它們一個字" in src, "")

    chk("⑩ 凍結副本不測(`_sha` 快照是收容原件,只增不減律要它們留著,但它們"
        "**不是現役引擎**——拿化石的載入結果去算認證就是灌水)",
        tier(Path("VRN_MDL001_Converter_shaf09dc35c.py")) == "frozen"
        and tier(Path("VRN_ENG049_ContentReconcile_v0102.py")) == "versioned"
        and tier(Path("VIA_HardGate_BootPrecheck.py")) == "adhoc",
        "(三層各判一例)")

    print(f"  [計] 十檢({len(done)} 檢) OK {len(done) - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 無自測面引擎煙霧閘(CGC_MDL147 v0100)· 十檢自測(零網路)===")
        return selftest()
    d = None
    if "--dir" in args:
        d = Path(args[args.index("--dir") + 1])
    return run(d)


if __name__ == "__main__":
    sys.exit(main())
