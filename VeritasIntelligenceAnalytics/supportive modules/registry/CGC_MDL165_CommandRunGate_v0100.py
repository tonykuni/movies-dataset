#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL165:短令能跑閘(批584;操作員令「我不懂程式系統,請幫我完成這些」)。

操作員貼回整份短令清單(110+ 個)說「請幫我完成」。那句話的可執行版本是:
**每一個登錄在冊的短令,打下去都要真的有東西跑起來。**

本閘做三件事,全程**只讀** `Register-VIA-Commands-v*.ps1`(L70:.ps1 是操作員的手,絕不改):
  ① 解析:逐 `function global:<令>` 抽出它要呼叫的目標
     (Get-VIANewest 的 資料夾×glob / Invoke-VIAPython 的路徑 / pwsh -File 的腳本 / 轉呼別的短令)
  ② 解析得到的目標**在不在**(glob 解得到尾版嗎)
  ③ 解得到的 Python 目標**讀得進來嗎**(AST 解析;`--deep` 才真的跑 --selftest)

誠實多態(不判假綠也不判假紅):
  OK          目標解析得到且檔在(Python 目標另加 AST 綠)
  MISSING     解析得到目標,但 glob 解不到任何檔=**打下去會炸**(真死令)
  DELEGATE    轉呼另一個短令(它的死活看被呼的那一個)
  INLINE      純 PowerShell 行內邏輯,沒有外部目標(不需要檔)
  UNPARSED    本閘讀不懂它的寫法=**誠實說讀不懂**,不猜、也不算它過

紀律:零網路 · 零寫入(無寫入旗標)· 不改任何 .ps1 · 不代跑需要同意閘的令。
用法:
  via-selftest 會帶到本站;直接跑:python3 CGC_MDL165_CommandRunGate_v0100.py [scan|plan] [--deep]
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

import argparse
import ast
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
REPORTS = VIA / "VIA_Reports" / "cmdrun"

#: 冊上**刻意不定義**的名(批358 讓位律:同名=九頭龍→讓位給操作員自己 PATH 上的檔)
YIELDED = {"via-go"}
#: 不是短令的東西(函式庫/輔助函式),不進分母——具名豁免(L68)
NOT_A_COMMAND = {
    "Invoke-VIAPython": "潑灑器輔助函式,不是短令",
    "Set-VIAGateDefaults": "同意閘預設值設定器(不代設,只補未設者)",
    "Set-VIABoot": "開機旗標設定器",
    "Import-VIAGrokMatrix": "Grok 矩陣載入器",
    "Get-VIAEnvPython": "家族境 python 解析器",
    "Get-VIANewest": "尾版 glob 解析器",
    "ConvertTo-VIACleanArgs": "參數清理器(PowerShell 逗號陣列陷阱;LL118)",
    "Get-VIAPinnedDir": "本窗副本解析器",
}


def register() -> Path | None:
    hits = sorted(VIA.glob("Register-VIA-Commands-v*.ps1"))
    return hits[-1] if hits else None


def _bodies(src: str) -> dict[str, str]:
    """逐 `function global:<名> { … }` 抽出主體(括號配對,容巢狀)。"""
    out: dict[str, str] = {}
    for m in re.finditer(r"function\s+global:([A-Za-z0-9\-_]+)\s*\{", src):
        name = m.group(1)
        i, depth = m.end(), 1
        while i < len(src) and depth:
            if src[i] == "{":
                depth += 1
            elif src[i] == "}":
                depth -= 1
            i += 1
        out[name] = src[m.end():i - 1]
    return out


def _aliases(src: str) -> dict[str, str]:
    return {m.group(1): m.group(2)
            for m in re.finditer(r"Set-Alias\s+-Name\s+(\S+)\s+-Value\s+(\S+)", src)}


_RX_NEWEST = re.compile(r'Get-VIANewest\s+"?\$VIA(?:\\([^"]*?))?"?\s+"([^"]+)"')
_RX_FILE = re.compile(r'-File\s+"\$VIA\\([^"]+)"')
_RX_PY = re.compile(r'Invoke-VIAPython[^\n]*?"\$VIA\\([^"]+\.py)"')
_RX_DELEG = re.compile(r"\b(via-[a-z0-9\-]+)\b")


def _resolve_glob(folder: str, pattern: str) -> Path | None:
    """解析 Get-VIANewest <資料夾> <樣式>。

    批584 第一版的洞:**資料夾那一段自己就可能帶 `*`**,例如
    `...\\references\\intake\\VIA_VES_EngineStandardizer_b*` + `via_engine_standardizer.py`。
    當成 literal 路徑去 `.exists()` 就永遠 False → 生出一個**假死令**。
    (via-ves 就是這樣被我判死的;檔其實好端端在 b370 夾裡。)
    """
    rel = folder.replace("\\", "/").strip("/") if folder else ""
    bases: list[Path] = []
    if not rel:
        bases = [VIA]
    elif "*" in rel or "?" in rel:
        bases = [p for p in sorted(VIA.glob(rel)) if p.is_dir()]
    else:
        d = VIA / rel
        bases = [d] if d.exists() else []
    hits: list[Path] = []
    for b in bases:
        hits.extend(b.glob(pattern))
    return sorted(hits)[-1] if hits else None


def classify(name: str, body: str) -> dict:
    """一個短令解析成什麼、目標在不在。**讀不懂就說讀不懂**,不猜。"""
    r = {"cmd": name, "kind": "", "target": "", "state": "", "why": ""}
    m = _RX_NEWEST.search(body)
    if m:
        folder, pat = (m.group(1) or ""), m.group(2)
        p = _resolve_glob(folder, pat)
        r.update(kind="newest", target=f"{folder or '.'}/{pat}")
        if p:
            r.update(state="OK", why=str(p.relative_to(VIA)).replace("\\", "/"))
        else:
            r.update(state="MISSING", why=f"glob 解不到任何檔:{folder or '.'}/{pat}")
        return r
    m = _RX_PY.search(body) or _RX_FILE.search(body)
    if m:
        rel = m.group(1).replace("\\", "/")
        p = VIA / rel
        r.update(kind="path", target=rel,
                 state="OK" if p.is_file() else "MISSING",
                 why=rel if p.is_file() else f"檔不在:{rel}")
        return r
    # 批584:`& cmd /c "$VIA\X.cmd"` 這種梭型寫法(via-rootcheck / via-tower-reset)
    m = re.search(r'cmd\s+/c\s+"\$VIA\\([^"]+)"', body)
    if m:
        rel = m.group(1).replace("\\", "/")
        p = VIA / rel
        r.update(kind="cmd", target=rel,
                 state="OK" if p.is_file() else "MISSING",
                 why=rel if p.is_file() else f"梭不在:{rel}")
        return r
    dele = [x for x in _RX_DELEG.findall(body) if x != name]
    if dele:
        r.update(kind="delegate", target=" / ".join(sorted(set(dele))[:3]),
                 state="DELEGATE", why="轉呼其他短令")
        return r
    if re.search(r"Write-Host|Get-ChildItem|\$env:|Set-Location|Push-Location|return", body):
        r.update(kind="inline", state="INLINE", why="純 PowerShell 行內邏輯,無外部目標")
        return r
    r.update(kind="?", state="UNPARSED", why="本閘讀不懂這種寫法(誠實:不猜、也不算過)")
    return r


def _ast_ok(p: Path) -> tuple[bool, str]:
    try:
        ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {str(exc)[:70]}"


def scan(deep: bool = False) -> dict:
    reg = register()
    if not reg:
        return {"state": "ABSENT", "why": "Register-VIA-Commands-v*.ps1 不在"}
    src = reg.read_text(encoding="utf-8", errors="replace")
    bodies = _bodies(src)
    rows, tally = [], {}
    for name, body in sorted(bodies.items()):
        if name in NOT_A_COMMAND:
            continue
        r = classify(name, body)
        if r["state"] == "OK" and r["why"].endswith(".py"):
            ok, err = _ast_ok(VIA / r["why"])
            if not ok:
                r.update(state="BROKEN", why=f"檔在但讀不進來 · {err}")
            elif deep:
                try:
                    cp = subprocess.run([sys.executable, str(VIA / r["why"]), "--selftest"],
                                        capture_output=True, timeout=300, cwd=str(VIA))
                    if cp.returncode not in (0, 2, 3):
                        # 批584:**把引擎自己印的 FAIL 行帶出來**。
                        # 只回一個 rc=1 等於只講了一半(批582 同一條教訓):
                        # 引擎的 1 常常是「缺料」而不是「壞掉」,不指名就分不出來。
                        out = (cp.stdout or b"").decode("utf-8", "replace") + \
                              (cp.stderr or b"").decode("utf-8", "replace")
                        fails = [ln.strip() for ln in out.splitlines() if "[FAIL]" in ln][:3]
                        # 批584:變數名不可與外層的 tally(態計數 dict)撞名——
                        # 撞了就是 'list' object has no attribute 'get',而且要跑完十分鐘才炸。
                        tally_ln = [ln.strip() for ln in out.splitlines() if "[計]" in ln][-1:]
                        r.update(state="SELFTEST_RED",
                                 why=f"{r['why']} · rc={cp.returncode}",
                                 engine_says=(tally_ln + fails) or ["(引擎沒印任何 FAIL 行)"])
                except Exception as exc:
                    r.update(state="SELFTEST_RED", why=f"{r['why']} · {type(exc).__name__}",
                             engine_says=[str(exc)[:120]])
        rows.append(r)
        tally[r["state"]] = tally.get(r["state"], 0) + 1
    al = _aliases(src)
    return {"state": "OK", "register": reg.name, "n": len(rows), "tally": tally,
            "rows": rows, "aliases": len(al),
            "yielded": sorted(YIELDED), "exempt": NOT_A_COMMAND,
            "note": ("MISSING / BROKEN / SELFTEST_RED = 打下去會出事,要修。"
                     "DELEGATE 看被呼的那一個。INLINE 不需要外部檔。"
                     "**UNPARSED = 本閘讀不懂,不算它過也不算它壞**(誠實;L57)。"
                     "本閘只讀 .ps1,絕不改(L70)。")}


def plan(deep: bool = False) -> dict:
    s = scan(deep)
    if s["state"] != "OK":
        return s
    bad = [r for r in s["rows"] if r["state"] in ("MISSING", "BROKEN", "SELFTEST_RED", "UNPARSED")]
    for r in bad:
        r["fix"] = {
            "MISSING": "目標 glob 解不到:要嘛引擎沒推上來,要嘛冊裡的 glob 打錯 → 補引擎或更正 glob(改 .ps1 是操作員的手)",
            "BROKEN": "檔在但 Python 讀不進來(語法壞)→ 修那支引擎",
            "SELFTEST_RED": "檔在、讀得進來,但自測不過 → **看下面它自己印的 FAIL 行**;引擎的 rc=1 常常是缺料不是壞掉(L57),要逐行看才分得出來",
            "UNPARSED": "本閘讀不懂這種寫法 → 補本閘的解析器(不是短令的錯)",
        }[r["state"]]
    return {"state": "OK" if not bad else "FAIL", "n_total": s["n"], "n_bad": len(bad),
            "tally": s["tally"], "todo": bad, "note": s["note"]}


def write_out(name: str, payload) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    p = REPORTS / name
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def selftest() -> int:
    fails, n = [], [0]

    def chk(name, cond, note=""):
        n[0] += 1
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    reg = register()
    chk("① 短令冊在位(尾版 glob)", reg is not None, f"({reg.name if reg else 'ABSENT'})")
    src = reg.read_text(encoding="utf-8", errors="replace") if reg else ""
    b = _bodies(src)
    # 合成驗:巢狀括號要吃得下,不能 regex 抓到第一個 } 就收工。
    # (不拿「真冊每一條括號都配對」當判準——PowerShell 字串裡本來就會有單邊 { },
    #  拿那個當尺會生假紅;那是**字串內容**,不是語法失衡。)
    _syn = 'function global:x-demo { if ($a) { "{" } else { "}" } ; Get-Item }\nfunction global:y { 1 }'
    _sb = _bodies(_syn)
    _skew = sum(1 for x in b.values() if x.count("{") != x.count("}"))
    chk("② 逐令抽得出主體,且括號配對**容巢狀**(合成驗:巢狀 if/else + 字串裡的單邊括號)",
        len(b) >= 100 and set(_sb) == {"x-demo", "y"} and "Get-Item" in _sb["x-demo"],
        f"({len(b)} 令 · 字串內單邊括號 {_skew} 條,屬內容非語法)")
    s = scan()
    chk("③ 掃得到且逐令有態", s["state"] == "OK" and s["n"] >= 100, f"({s['n']} 令)")
    chk("④ 誠實多態:**讀不懂就說讀不懂**,不預設當它過(UNPARSED 不計入 OK)",
        "OK" in s["tally"] and all(r["state"] in
                                   ("OK", "MISSING", "DELEGATE", "INLINE", "UNPARSED",
                                    "BROKEN", "SELFTEST_RED") for r in s["rows"]),
        f"({s['tally']})")
    chk("⑤ 具名豁免:非短令的輔助函式逐條附理由(L68 分母要攤得開)",
        all(v for v in NOT_A_COMMAND.values()) and len(NOT_A_COMMAND) >= 6,
        f"({len(NOT_A_COMMAND)} 條)")
    chk("⑥ 讓位律記在冊:via-go 是操作員自己 PATH 上的檔,短令冊**刻意不定義**(批358)",
        "via-go" in YIELDED and "via-go" not in b)
    src_self = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ **只讀不改 .ps1**(L70:那是操作員的手)",
        ".ps1" in src_self and "write_text" not in src_self.split("def write_out")[0])
    chk("⑧ 零網路(不匯入任何網路庫)",
        not re.search(r"^\s*(?:import|from)\s+(urllib|requests|httpx|aiohttp)", src_self, re.M))
    p = plan()
    chk("⑨ plan 只列會出事的,而且每一列講得出下一步",
        p["state"] in ("OK", "FAIL") and all("fix" in r for r in p.get("todo", [])),
        f"(待修 {p.get('n_bad', 0)})")
    chk("⑩ 帶加速器橋(MDL156 覆蓋閘)", "[VIA:ACCEL-BRIDGE" in src_self)
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="CGC_MDL165_CommandRunGate",
                                 description="短令能跑閘(零網路;只讀 .ps1)")
    ap.add_argument("verb", nargs="?", default="scan", choices=["scan", "plan"])
    ap.add_argument("--deep", action="store_true", help="真的跑每支 Python 目標的 --selftest(慢)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    r = scan(a.deep) if a.verb == "scan" else plan(a.deep)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_out(f"CMDRUN_{a.verb.upper()}_{ts}.json", r)
    write_out(f"CMDRUN_{a.verb.upper()}_latest.json", r)
    if a.json:
        print(json.dumps(r, ensure_ascii=False))
        return 0
    if r["state"] == "ABSENT":
        print(f"[CGC_MDL165 v{VERSION}] ABSENT · {r['why']}")
        return 3
    if a.verb == "scan":
        t = r["tally"]
        print(f"[CGC_MDL165 v{VERSION}] scan · {r['register']} · 短令 {r['n']} 個 · 別名 {r['aliases']}")
        print("  " + " · ".join(f"{k} {v}" for k, v in sorted(t.items())))
        print("  " + r["note"])
        for x in r["rows"]:
            if x["state"] not in ("OK", "INLINE", "DELEGATE"):
                print(f"  [{x['state']:<13}] {x['cmd']:<26} {x['why']}")
        return 0 if not any(x["state"] in ("MISSING", "BROKEN", "SELFTEST_RED") for x in r["rows"]) else 2
    print(f"[CGC_MDL165 v{VERSION}] plan · {r['state']} · 短令 {r['n_total']} · **待修 {r['n_bad']}**")
    print("  " + " · ".join(f"{k} {v}" for k, v in sorted(r["tally"].items())))
    for x in r["todo"]:
        print(f"  [{x['state']:<13}] {x['cmd']:<26} {x['why']}")
        for line in x.get("engine_says", []):
            print(f"                 | {line[:150]}")
        print(f"                 → {x['fix']}")
    return 0 if r["state"] == "OK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
