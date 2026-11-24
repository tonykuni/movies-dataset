#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL157: VIA unique entry-point control plane.

This is a deterministic, offline, read-only gate. It does not execute market
engines. It proves that VRN, VDF and QuantGuard are reached through the VIA
command book and the single Invoke-VIAPython/bootstrap path, with the network
consent gate remaining fail-closed.
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
import hashlib
import html
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
# 批564:CGC_MDL157 v0102→v0103 —— 加「一貼即用區塊裡的短令必須真的存在」。
#   實錄:批563 我立了 VDF_ENG088 共識融合橋,**卻沒跑功能註冊七處**,
#   然後在回覆與 docs 裡叫操作員跑 `via-consensus`。他照打了兩次,兩次都是
#   「無法將 'via-consensus' 字詞辨識為…」。冊上沒有那個函式,身邊也沒有梭。
#   批543 那兩檢管的是「冊 → 梭」,管不到「我在文件裡叫了一個冊上沒有的名字」。
#
#   **這一檢我試了三把尺才留下一把,前兩把當場丟掉**(LL86:尺錯了量出來的全不可信):
#     ① 「可跑引擎都要有短令」→ 273 個家族裡 194 個冊上沒有 = 一面假紅牆。
#        多數是內部件/樞紐,本來就不該有短令。
#     ② 「自測格點名 + 只有 v0100 + 冊上沒有」→ 還有 19 支,
#        而那 19 支多半是別人 import 的樞紐(MarkdownStructureHub…),照樣是假紅。
#     ③ **只量一貼即用區塊裡真的被呼叫的短令** → 430 次呼叫,只有 3 個對不上,
#        而那 3 個全部可解釋:`via-envmanager-governance-7cls8h` 是**分支名**
#        (出現在 `git pull origin claude/…` 裡,被我的 regex 誤抓),
#        `via-talib` / `via-taone` 是 **L50 退役**的 TA-Lib 令(在歷史交接裡是史料,
#        冊上沒有才是對的——真的回來了反而該紅)。扣掉這兩類 = **零噪音**。
#   釘住的是我真正犯的那件事:**寫進一貼即用、要操作員照打的名字,必須真的叫得出來。**
# 批543:CGC_MDL157 v0102→v0102 —— 加「短令必有梭」兩檢(操作員打 via-pyprog 當場叫不出來:
# 冊上有函式、身邊沒有同名 .cmd,七處只做了六處。查出冊上 133 個短令只有 93 個有梭)。
COMMAND_BOOK = sorted(ROOT.glob("Register-VIA-Commands-v*.ps1"))[-1] if list(ROOT.glob("Register-VIA-Commands-v*.ps1")) else ROOT / "Register-VIA-Commands-v0208.ps1"   # 批534 尾版律
PY_HELPER = ROOT / "supportive modules" / "VIA_PS_PyProgress_Module.ps1"
BOOTSTRAP = ROOT / "supportive modules" / "bootstrap" / "sitecustomize.py"
POLICY = ROOT / "supportive modules" / "registry" / "VIA_QuantGuard_TA_Lib_Policy_v0100.json"
INPUT_CONSOLE = ROOT / "supportive modules" / "registry" / "VIA_InputConsole_Spec_v0100.json"
WORKFLOW = ROOT / "supportive modules" / "registry" / "VIA_Workflow_SSOT_v0100.json"
TOOL_ROSTER = ROOT / "supportive modules" / "registry" / "VIA_ToolRoster_SSOT_v0100.json"
REPORT_DIR = ROOT / "VIA_Reports" / "entry"
LATEST_JSON = REPORT_DIR / "VIA_UNIQUE_ENTRY_CONTROL_latest.json"
LATEST_HTML = REPORT_DIR / "VIA_UNIQUE_ENTRY_CONTROL_latest.html"
DISPATCH_JSON = REPORT_DIR / "VIA_UNIQUE_ENTRY_DISPATCH_latest.json"

TARGET_ENTRYPOINTS = (
    "via-nlpvrn",
    "via-nlpunified",
    "via-vrn4",
    "via-vdfarch",
    "via-vdfdb",
    "via-quantguard",
)
TARGET_TOKENS = ("VRN_ENG", "VDF_ENG", "SUP_MDL", "CGC_MDL")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {"name": name, "state": "PASS" if ok else "FAIL", "ok": bool(ok), "detail": detail}


def function_bodies(text: str) -> dict[str, str]:
    pattern = re.compile(r"(?ms)^function\s+global:(via-[\w-]+)\s*\{(?P<body>.*?)(?=^function\s+global:|\Z)")
    return {m.group(1): m.group("body") for m in pattern.finditer(text)}


def run_checks() -> list[dict[str, Any]]:
    book = read(COMMAND_BOOK)
    helper = read(PY_HELPER)
    boot = read(BOOTSTRAP)
    bodies = function_bodies(book)
    checks: list[dict[str, Any]] = [
        check("VIA command book exists", COMMAND_BOOK.is_file(), str(COMMAND_BOOK)),
        check("VIA Python helper exists", PY_HELPER.is_file(), str(PY_HELPER)),
        check("single Invoke-VIAPython helper is defined", "function Invoke-VIAPython" in helper, "VIA_PS_PyProgress_Module.ps1"),
        check("helper owns process start", "Start-Process -FilePath $exe" in helper, "central process wrapper"),
        check("bootstrap exists", BOOTSTRAP.is_file(), str(BOOTSTRAP)),
        check("bootstrap carries central entry identity", "VIA_ENTRY_CONTROL" in boot and "CGC_MDL157" in boot and "VIA_CENTRAL_ENTRY" in boot, "sitecustomize.py"),
        check("network default is fail-closed in command book", 'VIA_NET_CONSENT = "OFF"' in book and 'VIA_SCRAPE_CONSENT = "OFF"' in book, "Set-VIAGateDefaults"),
        check("command book never auto-opens consent", 'VIA_NET_CONSENT = "YES"' not in book and 'VIA_SCRAPE_CONSENT = "YES"' not in book, "operator consent only"),
        check("command book has unique central dispatcher", "function global:via-central" in book and "function global:via-unique-check" in book, "VIA central command"),
    ]
    central = bodies.get("via-central", "")
    checks.append(check("central dispatcher routes VRN/VDF/QuantGuard", all(x in central for x in ("via-nlpvrn", "via-vdfarch", "via-quantguard")), "via-central child routes"))
    checks.append(check("central dispatcher gates before child route", "CGC157 未 GREEN" in central and "Invoke-VIAPython" in central, "pre-dispatch gate"))
    missing = [name for name in TARGET_ENTRYPOINTS if name not in bodies]
    checks.append(check("VRN/VDF/QuantGuard target entries exist", not missing, "missing=" + ",".join(missing)))
    bypasses: list[str] = []
    for name in TARGET_ENTRYPOINTS:
        body = bodies.get(name, "")
        if body and "Invoke-VIAPython" not in body and "via-closeout" not in body:
            bypasses.append(name)
    checks.append(check("target entries dispatch only through VIA Python helper", not bypasses, "bypass=" + ",".join(bypasses)))
    direct_engine_lines = []
    for name in TARGET_ENTRYPOINTS:
        body = bodies.get(name, "")
        for line in body.splitlines():
            if any(token in line for token in TARGET_TOKENS) and "Invoke-VIAPython" not in line and "Get-VIANewest" not in line and "FAIL:" not in line and not line.lstrip().startswith("#"):
                direct_engine_lines.append(f"{name}:{line.strip()[:140]}")
    checks.append(check("no target engine line bypasses Invoke-VIAPython", not direct_engine_lines, "; ".join(direct_engine_lines[:4])))
    checks.append(check("fail-closed helper does not direct-fallback", "中央 helper 缺失" in book and "& $exe @Rest" not in book, "missing helper must stop"))
    checks.append(check("policy SSOT is active and one-way", POLICY.is_file() and '"direction": "VDF_DUCKDB_TO_QUANTGUARD"' in read(POLICY) and '"source_mutation": "FORBIDDEN"' in read(POLICY), "QuantGuard policy"))
    checks.append(check("central registries contain unique entry contract", all(token in read(path) for path, token in ((INPUT_CONSOLE, "via_unique_entry_control"), (WORKFLOW, "via_unique_entry_control"), (TOOL_ROSTER, "unique_entry_control"))), "InputConsole/Workflow/ToolRoster"))
    checks.append(check("entry-control report directory is writable", REPORT_DIR.parent.is_dir(), str(REPORT_DIR)))
    # ── 批543:短令必有梭 ────────────────────────────────────────────────
    # 操作員實錄:`via-pyprog` 打下去「無法將 'via-pyprog' 字詞辨識為 Cmdlet…」。
    # 根因不是短令寫錯,是**七處只做了六處**——冊上有函式,身邊沒有同名 .cmd 梭。
    # 沒有梭的短令,在 cmd 殼永遠叫不出來;在 PS 殼也要人記得重新點源冊。
    # 查出來冊上 133 個短令只有 93 個有梭,缺 40 個(via-vcgc / via-panorama / via-ryg 都在內)。
    # 這一檢把它釘住:冊上每一個 `function global:via-*` 都必須有同名 .cmd(大小寫不計)。
    import re as _re
    fns = sorted(set(_re.findall(r"^function global:(via-[A-Za-z0-9-]+)", book, _re.M)))
    shims = {q.stem.lower() for q in ROOT.glob("*.cmd")}
    no_shim = [f for f in fns if f.lower() not in shims]
    # ── 批564:一貼即用區塊裡的短令必須真的存在 ────────────────────────────
    import re as _re4
    _BLK = _re4.compile(r"```(?:powershell|ps1|pwsh)\n(.*?)```", _re4.S | _re4.I)
    #: L50 退役令:冊上沒有才是對的(真的回來了是另一種紅,不是這一檢的事)
    _RETIRED = {"via-talib", "via-taone"}
    _calls, _ghost = 0, {}
    for _doc in sorted((ROOT / "docs").glob("*.md")):
        try:
            _t = _doc.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for _blk in _BLK.findall(_t):
            for _ln in _blk.splitlines():
                _ln = _ln.split("#")[0]
                if "claude/" in _ln or "origin " in _ln:      # 分支名不是短令
                    continue
                for _c in _re4.findall(r"(?<![\w-])(via-[a-z0-9]+(?:-[a-z0-9]+)*)", _ln):
                    _calls += 1
                    if _c in _RETIRED or _c in fns:
                        continue
                    _ghost.setdefault(_c, set()).add(_doc.name)
    checks.append(check("every via-* call inside a paste-ready block resolves to a real command",
                        not _ghost,
                        (f"calls={_calls} ghost=" + "; ".join(f"{k}←{sorted(v)[0]}" for k, v in sorted(_ghost.items())[:4]))
                        if _ghost else f"calls={_calls} · all resolve(retired L50 excluded: {sorted(_RETIRED)})"))
    checks.append(check("every via-* command in the book has a same-named .cmd shim",
                        not no_shim,
                        f"book={len(fns)} shims={len(shims)} missing={','.join(no_shim[:8])}" if no_shim
                        else f"book={len(fns)} · all shimmed"))
    # 梭要驗的是「到得了」,不是「長得一樣」。第一版我要求每個梭都得走
    # `點源冊尾版 + %~n0` 那個樣板,結果六個檔被判紅——查完全是**獨立啟動器**:
    # VIA-ALL(git 自癒+全跑)· VIA-ROOTCHECK · VIA-TOWER-RESET · via-pipeline / via-ppp /
    # via-repo-optimize(各自 glob 自己的 Invoke-VIA-*.ps1)。它們用另一條路到達,一樣到得了;
    # 拿樣板去量它們就是我造的判錯紅燈(LL86 尺錯了,量出來的全不可信)。
    # 真正該擋的只有一件:**版號寫死**——尾版律一旦被寫死,升版那天梭就指向舊檔或空氣。
    import re as _re2
    pinned = []
    for f in fns:
        q = next((x for x in ROOT.glob("*.cmd") if x.stem.lower() == f.lower()), None)
        if q is None:
            continue
        t = q.read_text(encoding="utf-8", errors="replace")
        # 第二版我又量錯一次,兩處:
        #   · 正則只認 `-v*.ps1`,漏掉 `VIA_WinIO_InputPicker_v*.ps1` 這種**底線**接 v 的寫法
        #     → via-vrnin 明明有動態 glob 卻被判紅
        #   · 硬要求「一定要解析到某個 ps1」,但 VIA-ROOTCHECK / VIA-TOWER-RESET 是**把事情寫在自己身上**的
        #     獨立腳本,根本沒有目標要解析,不可能會過期
        # 真正會咬人的只有一件:**版號釘死**。留這一條就好,其餘不是我該管的形狀。
        hard = _re2.findall(r"[A-Za-z0-9_-]+[-_]v\d{3,4}\.ps1", t)
        if hard:
            pinned.append(q.name + "(釘死 " + hard[0] + ")")
    checks.append(check("no shim pins a version (tail-version law):升版那天釘死的梭會指向舊檔或空氣",
                        not pinned, "pinned=" + ",".join(pinned[:6]) if pinned else f"{len(fns)} shims · 零釘死"))
    # 負控:上面兩檢要是永遠會過,那就只是兩盞假綠燈(LL89)。拿合成資料當場證明它們咬得住。
    _fake_fns = ["via-zzz-nonexistent"]
    _fake_shims = {q.stem.lower() for q in ROOT.glob("*.cmd")}
    _catch_missing = [f for f in _fake_fns if f.lower() not in _fake_shims] == _fake_fns
    _catch_pinned = bool(_re2.findall(r"[A-Za-z0-9_-]+[-_]v\d{3,4}\.ps1",
                                      'set "PS1=%VIA%Invoke-VIA-RepoOptimizer-v0100.ps1"'))
    checks.append(check("both shim checks are proven to bite (synthetic negative control)",
                        _catch_missing and _catch_pinned,
                        f"缺梭咬得住={_catch_missing} · 釘死咬得住={_catch_pinned}"))
    return checks


def run(write: bool = True) -> dict[str, Any]:
    checks = run_checks() + _b534_checks()
    passed = sum(1 for item in checks if item["ok"])
    failed = len(checks) - passed
    verdict = "GREEN" if failed == 0 else "RED"
    payload = {
        "schema": "VIA.CGC157.UniqueEntryControl.v1",
        "engine": "CGC_MDL157_VIAUniqueEntryControl_v0100",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "verdict": verdict,
        "control_state": "ONLY_VIA_ENTRY" if verdict == "GREEN" else "DO_NOT_ROUTE",
        "scope": {"vrn": list(TARGET_ENTRYPOINTS[:3]), "vdf": list(TARGET_ENTRYPOINTS[3:5]), "quantguard": [TARGET_ENTRYPOINTS[5]]},
        "checks": checks,
        "counts": {"total": len(checks), "pass": passed, "fail": failed},
        "network": {"default": "OFF", "consent": "operator_owned", "silent_open": False},
        "data_flow": "VDF_DUCKDB_TO_QUANTGUARD",
        "source_mutation": "FORBIDDEN",
        "artifacts": {name: {"path": str(path), "sha256": sha256(path)} for name, path in {"command_book": COMMAND_BOOK, "python_helper": PY_HELPER, "bootstrap": BOOTSTRAP, "policy": POLICY}.items()},
    }
    if write:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        LATEST_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        LATEST_HTML.write_text(render_html(payload), encoding="utf-8")
    return payload



def _b534_checks() -> list[dict[str, Any]]:
    """批534 新增三檢:尾版命令冊 · 家族境派送 · 誠實四態判讀。"""
    books = sorted(ROOT.glob("Register-VIA-Commands-v*.ps1"))
    newest_book = books[-1].name if books else ""
    a = judge_route(3, "=== ABSENT · 本境無 polars ===")
    b = judge_route(1, "Traceback\nModuleNotFoundError: No module named 'polars'")
    c = judge_route(2, "[NODATA] input not found")
    d = judge_route(1, "AssertionError: boom")
    e = judge_route(None, "TIMEOUT after 900s")
    v_green = verdict_of([{"state": "GREEN"}])
    v_yellow = verdict_of([{"state": "GREEN"}, {"state": "ABSENT"}])
    v_red = verdict_of([{"state": "GREEN"}, {"state": "RED"}])
    src = Path(__file__).read_text(encoding="utf-8")
    return [
        check("批534 命令冊走尾版 glob(不釘死版號)", COMMAND_BOOK.name == newest_book and 'Register-VIA-Commands-v*.ps1' in src, f"{COMMAND_BOOK.name} = newest {newest_book}"),
        check("批534 子路由用家族境 python(匯流排 python_for;非 sys.executable 一律)", "family_python(fam)" in src and "python_for" in src and "child_env(fam)" in src, f"vrn→{family_python('vrn')[1]} · quantguard→{family_python('quantguard')[1]}"),
        check("批534 誠實四態:缺件 ABSENT · 缺料 NODATA · 逾時 TIMEOUT · 真壞才 RED;裁決 GREEN/YELLOW/RED",
              a[0] == "ABSENT" and b[0] == "ABSENT" and c[0] == "NODATA" and d[0] == "RED" and e[0] == "TIMEOUT"
              and v_green == "GREEN" and v_yellow == "YELLOW" and v_red == "RED",
              f"{a[0]}/{b[0]}/{c[0]}/{d[0]}/{e[0]} → {v_green}/{v_yellow}/{v_red}"),
    ]

def render_html(payload: dict[str, Any]) -> str:
    rows = "".join(f"<tr><td>{html.escape(x['name'])}</td><td class='{x['state']}'>{x['state']}</td><td>{html.escape(x['detail'])}</td></tr>" for x in payload["checks"])
    c = payload["counts"]
    return f"""<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><title>VIA Unique Entry Control</title><style>body{{font:14px system-ui,sans-serif;margin:30px;color:#172033}}h1{{margin-bottom:4px}}.pill{{padding:5px 12px;border-radius:999px;font-weight:700}}.GREEN,.PASS{{background:#d9f2e9;color:#08745b}}.RED,.FAIL{{background:#ffe1df;color:#a52b25}}table{{border-collapse:collapse;width:100%;margin-top:20px}}th,td{{border-bottom:1px solid #dfe5ee;padding:9px;text-align:left;vertical-align:top}}th{{background:#f4f7fb}}</style></head><body><h1>VIA 唯一接觸口控制</h1><p><span class='pill {payload['verdict']}'>{payload['verdict']}</span> <b>{payload['control_state']}</b> · {payload['timestamp']}</p><p>PASS {c['pass']} / {c['total']} · data flow: <b>VDF/DuckDB → QuantGuard</b> · network: <b>OFF</b></p><table><thead><tr><th>檢查</th><th>狀態</th><th>細節</th></tr></thead><tbody>{rows}</tbody></table></body></html>"""



# 批564:版號從**檔名**取,不再手抄。v0103 這一版我一開始照抄成 "v0102",
# 檔是 v0103 而橫幅印 v0102——一個會說謊的版號,下次就是有人拿它去對版本。
import re as _rev
VERSION = (_rev.search(r"_v(\d{4})\.py$", Path(__file__).name).group(0)[1:-3]
           if _rev.search(r"_v(\d{4})\.py$", Path(__file__).name) else "v0000")


def newest(folder: Path, pattern: str) -> str:
    """尾版律:同名不同版取字典序最後一個;缺=回 pattern 本身(下游 judge 判 ABSENT/RED,不假裝在)。"""
    hits = sorted(folder.glob(pattern))
    return str(hits[-1]) if hits else str(folder / pattern)


_BUS = {"mod": None, "tried": False}


def _bus():
    """匯流排(CGC_MDL148)=家族境 python 與子行程環境的正主(L30 一功能一主);缺席=None。"""
    if not _BUS["tried"]:
        _BUS["tried"] = True
        try:
            import importlib.util
            cands = sorted((ROOT / "supportive modules" / "registry").glob("CGC_MDL148_EngineBus_v*.py"))
            if cands:
                spec = importlib.util.spec_from_file_location("via_bus_for_157", cands[-1])
                m = importlib.util.module_from_spec(spec)
                sys.modules["via_bus_for_157"] = m
                spec.loader.exec_module(m)
                _BUS["mod"] = m
        except Exception:
            _BUS["mod"] = None
    return _BUS["mod"]


_FAMILY_ENV = {"vrn": "VIA_PY_VRN", "vdf": "VIA_PY_VDF", "quantguard": "VIA_PY_VDF", "vap": "VIA_PY_VAP", "core": "VIA_PY_CORE"}


def family_python(family: str) -> tuple[str, str]:
    """家族境 python:env 明給 > 匯流排 python_for > 目前解譯器。QuantGuard 住 vdf 境。"""
    key = _FAMILY_ENV.get(family, "")
    e = os.environ.get(key) if key else None
    if e and Path(e).exists():
        return e, key
    b = _bus()
    if b is not None:
        try:
            got = b.python_for("vdf" if family == "quantguard" else family)
            py = (got or {}).get("python")
            if py and Path(py).exists():
                return py, f"bus:{(got or {}).get('source') or 'python_for'}"
        except Exception:
            pass
    return sys.executable, "sys.executable(退路)"


def child_env(family: str) -> dict:
    b = _bus()
    if b is not None:
        try:
            return dict(b.child_env("vdf" if family == "quantguard" else family))
        except Exception:
            pass
    e = dict(os.environ)
    e.pop("PYTHONHOME", None)           # L32 PYTHONHOME 清洗
    e["VIA_PYTHONHOME_SCRUBBED"] = "1"
    return e


_ABSENT_MARK = ("ModuleNotFoundError", "[ABSENT]", "· ABSENT ·", "ABSENT(", "No module named")
_NODATA_MARK = ("[NODATA]", "[NEED_INPUT]", "NODATA", "NEED_INPUT")


def judge_route(rc: int | None, output: str) -> tuple[str, str]:
    """誠實四態:缺件=ABSENT、缺料=NODATA、逾時=TIMEOUT、真壞才 RED(判錯的紅燈和假綠一樣傷)。"""
    if rc is None:
        return "TIMEOUT", output.splitlines()[-1][:160] if output else "逾時"
    if rc == 0:
        return "GREEN", "rc0"
    tail = output[-2000:]
    if rc == 3 or any(k in tail for k in _ABSENT_MARK):
        line = next((l for l in reversed(tail.splitlines()) if any(k in l for k in _ABSENT_MARK)), "")
        return "ABSENT", ("本境缺件(不是壞):" + line.strip()[:150]) if line else f"本境缺件 rc={rc}"
    if rc == 2 or any(k in tail for k in _NODATA_MARK):
        line = next((l for l in reversed(tail.splitlines()) if any(k in l for k in _NODATA_MARK)), "")
        return "NODATA", ("資料側(不是壞):" + line.strip()[:150]) if line else f"缺料 rc={rc}"
    return "RED", (tail.splitlines()[-1].strip()[:160] if tail.strip() else f"rc={rc}")


def verdict_of(routes: list[dict[str, Any]]) -> str:
    if not routes:
        return "RED"
    states = {r["state"] for r in routes}
    if states <= {"GREEN"}:
        return "GREEN"
    if states & {"RED", "TIMEOUT"}:
        return "RED"
    return "YELLOW"


_FLAG_VERBS = {"--selftest": "selftest", "--status": "status", "--manifest": "manifest", "--routes": "routes", "--dispatch": "dispatch"}


def _normalise_argv(argv: list[str]) -> list[str]:
    out, verb = [], None
    for a in argv:
        if a in _FLAG_VERBS and verb is None:
            verb = _FLAG_VERBS[a]
        else:
            out.append(a)
    return ([verb] + out) if verb else out


def dispatch(family: str, timeout: int = 0) -> dict[str, Any]:
    """Run only fixed, offline child routes after the unique-entry gate (family-env aware)."""
    timeout = int(timeout or os.environ.get("VIA_CENTRAL_TIMEOUT") or 900)
    gate = run(write=True)
    if gate["verdict"] != "GREEN":
        result = {"schema": "VIA.CGC157.UniqueEntryDispatch.v1", "verdict": "BLOCKED", "gate": gate, "routes": []}
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        DISPATCH_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result
    VRN = ROOT / "functional modules" / "VRN"
    VDFE = ROOT / "functional modules" / "VDF" / "engine"
    commands: dict[str, list[tuple[str, list[str]]]] = {                  # 批534:一律尾版 glob(釘死版號=新版出了中央還跑舊的)
        "vrn": [("VRN_ENG087_NLP", [newest(VRN, "VRN_ENG087_NLPTextSummaryBridge_v*.py"), "selftest"])],
        "vdf": [
            ("VDF_ENG073_DataArchitecture", [newest(VDFE, "VDF_ENG073_DataArchitecture_v*.py"), "--selftest"]),
            ("VDF_ENG087_MarketListGovernance", [newest(VDFE, "VDF_ENG087_MarketListGovernance_v*.py"), "--selftest"]),
        ],
        "quantguard": [("VDF_ENG086_QuantGuard", [newest(VDFE, "VDF_ENG086_QuantGuardOneBridge_v*.py"), "selftest"])],
    }
    families = ["vrn", "vdf", "quantguard"] if family == "all" else [family]
    routes: list[dict[str, Any]] = []
    for fam in families:
        py, py_src = family_python(fam)
        env = child_env(fam)
        env["VIA_ROOT"] = str(ROOT)
        env["VIA_CENTRAL_ENTRY"] = "1"
        env["VIA_ENTRY_CONTROL"] = f"CGC_MDL157_VIAUniqueEntryControl_{VERSION}"
        env.setdefault("VIA_NET_CONSENT", "OFF")
        env.setdefault("VIA_SCRAPE_CONSENT", "OFF")
        env["PYTHONPATH"] = str(BOOTSTRAP) + os.pathsep + env.get("PYTHONPATH", "")
        for label, argv in commands[fam]:
            try:
                proc = subprocess.run([py, *argv], cwd=str(ROOT), env=env, text=True, capture_output=True, timeout=timeout)
                rc, output = proc.returncode, (proc.stdout + ("\n" + proc.stderr if proc.stderr else "")).strip()
            except subprocess.TimeoutExpired:
                rc, output = None, f"TIMEOUT after {timeout}s"
            except FileNotFoundError as exc:
                rc, output = None, f"family python not found: {exc}"
            state, why = judge_route(rc, output)
            routes.append({"family": fam, "engine": label, "argv": argv, "python": py, "python_source": py_src,
                           "returncode": rc, "state": state, "why": why, "output_tail": output[-4000:]})
    result = {
        "schema": "VIA.CGC157.UniqueEntryDispatch.v1",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "gate": {"engine": gate["engine"], "verdict": gate["verdict"], "control_state": gate["control_state"]},
        "family": family,
        "routes": routes,
        "network": {"default": "OFF", "consent": env.get("VIA_NET_CONSENT"), "silent_open": False},
        "data_flow": "VDF_DUCKDB_TO_QUANTGUARD",
        "verdict": verdict_of(routes),
        "counts": {st: sum(1 for x in routes if x["state"] == st) for st in ("GREEN", "ABSENT", "NODATA", "TIMEOUT", "RED")},
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    DISPATCH_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="VIA unique entry-point control plane")
    parser.add_argument("command", choices=("selftest", "status", "manifest", "routes", "dispatch"))
    parser.add_argument("--family", choices=("vrn", "vdf", "quantguard", "all"), default="all")
    parser.add_argument("--timeout", type=int, default=0)
    args = parser.parse_args(_normalise_argv(sys.argv[1:]))
    if args.command == "dispatch":
        result = dispatch(args.family, args.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        c = result.get("counts") or {}
        print(f"[CGC_MDL157 {VERSION}] dispatch {args.family} · {result['verdict']} · " +
              " · ".join(f"{k}={v}" for k, v in c.items() if v))
        for r in result.get("routes", []):
            print(f"  [{r['state']:<7}] {r['family']:<10} {r['engine']:<32} rc={r['returncode']} · {str(r.get('why', ''))[:90]}")
            print(f"            python={r.get('python_source')} → {r.get('python')}")
        return {"GREEN": 0, "YELLOW": 0}.get(result["verdict"], 2)
    payload = run(write=True)
    if args.command == "selftest":
        print(f"[CGC_MDL157 {VERSION}] {payload['verdict']} · {payload['counts']['pass']}/{payload['counts']['total']} · ONLY_VIA_ENTRY")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["verdict"] == "GREEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
