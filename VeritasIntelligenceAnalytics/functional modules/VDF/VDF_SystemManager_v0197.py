#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF SystemManager v0197 — 薄尾(v0196 以前一字不動):2026-11-28 主機第一次實跑 vv / outputs 抓到的五件事

主機(Windows · OneDrive)實跑 vv RED 630.8s、outputs YELLOW;同一批在容器是綠 / 黃。逐件對過根因:
  ① 主機 vv 只印「[不過] 家族 · rc 1」,看不到哪一檢不過(要另外抓;而且有的引擎不印 [FAIL] 印 [NG])。
     → 本版:每支不過 / 逾時的引擎,把它自測輸出裡的不過行(FAIL · NG · Traceback · Error · 逾時)存進收據
       VV_latest.json 的 engine_rows[].why_lines,畫面在 [不過] 底下印最像根因的兩行(先印不是「前版自測沒過」的那種包裝行)。
  ② 5 支 rc 124:單支上限 120 秒在主機(OneDrive · 3 道並行)不夠,沒跑完不等於壞了。
     → 本版:沒帶 --timeout 時預設 300 秒;逾時的那幾支在並行跑完後「一支一支」再跑一次(上限 ×2,最多 900 秒),
       重跑過了就照實記「PASS(重跑)」,重跑還是逾時才算不過。
  ③ ② 結構確認的 regex / synonyms 在主機黃、容器綠:VDF 自有冊記的是來源檔的 sha256,Windows 取出時換行變 CRLF,
     原始位元組雜湊必然不同(CLAUDE.md「跨平台位元組:算雜湊前先統一成 LF」)。
     → 本版:原始雜湊對不上時,再用「CRLF → LF」後的雜湊比一次;相同 = 綠(記 eol=CRLF);真的換了內容照舊黃。
  ④ ② 的 number 在主機黃、容器綠:比對編號冊時,尾版路徑用 str(relative_to) —— Windows 是反斜線,
     編號冊的 source 是正斜線 → 主機上每一支都被當成「沒編號」。→ 本版:兩邊一律轉成正斜線再比;雜湊也統一 LF。
     另外 vv 的 ② / ③ 原本在子行程跑「前版檔」(v0193),本版的修正到不了 → 本版改跑家族尾版(glob 取最大版號)。
  ⑤ outputs 的「date 型別 str≠date」:v0195 判的是儲存型別,比表頭冊自己的檢查工具(VCGC CGC_MDL249 _castable)嚴。
     → 本版照 MDL249 同一判法(不 import VCGC,系統獨立):非空值裡轉不了的筆數 = 0 才算對;
       int/float 用數值轉換,int 另檢小數(forward_pe 存成小數、表頭寫整數 → 檢查值是不是都是整數);
       date/datetime 先在庫裡 TRY_CAST,轉不了的再用 pandas.to_datetime(與 MDL249 同)複核。只讀;數字與筆數不離開本機。
其餘照 v0196 / v0195 / v0194。零網路 · 不碰 TA-Lib · 不設同意閘 · 不 import VCGC。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

VERSION = "v0197"
STEM = "VDF_SystemManager"
TAG = f"VDF_SystemManager {VERSION}"
HERE = Path(__file__).resolve().parent
VV_TIMEOUT_DEFAULT = 300
RETRY_MAX = 900


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0196(outputs 未量 · find_dbs)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def chain() -> list:
    """前版鏈上每一版的模組(v0196 → v0195 → …),照 PRIOR 往下走。"""
    out, m = [], PRIOR
    while m is not None and all(m is not x for x in out):
        out.append(m)
        m = vars(m).get("PRIOR")
    return out


def owners(name: str, also: str | None = None) -> list:
    return [m for m in chain() if name in vars(m) and (also is None or also in vars(m))]


def tail_path() -> Path:
    """家族尾版(glob 取最大版號;之後出新版也跟著走)。"""
    return max(HERE.glob(STEM + "_v*.py"), key=_vnum)


V194 = owners("one_engine", "cmd_vv")[0]
V195 = owners("judge", "h_type")[0]
V196 = PRIOR

# ---------- ① 不過的原因 ----------
WHY_RX = re.compile(r"\[(?:FAIL|NG|ERR|ERROR|紅)\]|Traceback|\b\w*Error\b|逾時|TIMEOUT")
WRAP_RX = re.compile(r"前版.{0,40}(自測|鏈)")


def why_lines(text: str, n: int = 8) -> list:
    """自測輸出裡的不過行(去重、照出現順序);一行都沒有 → 最後三行非空行(照實,不猜)。"""
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    hits = []
    for ln in lines:
        if WHY_RX.search(ln) and ln[:220] not in hits:
            hits.append(ln[:220])
    return hits[:n] if hits else [ln[:220] for ln in lines[-3:]]


def root_first(lines: list) -> list:
    """最像根因的排前面:不是「前版自測沒過」那種包裝行的先印。"""
    return sorted(lines, key=lambda ln: 1 if WRAP_RX.search(ln) else 0)


def _txt(x) -> str:
    if x is None:
        return ""
    return x.decode("utf-8", "replace") if isinstance(x, bytes) else str(x)


def one_engine(fam: str, p: Path, timeout: int, env: dict, rc_map: dict, missing_lib) -> dict:
    """照 v0194 的判法;多記不過 / 逾時的原因行。"""
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, str(p), "--selftest"], cwd=tempfile.gettempdir(), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, env=env, stdin=subprocess.DEVNULL)
        res = rc_map.get(r.returncode, "FAIL")
        text = (r.stdout or "") + "\n" + (r.stderr or "")
        lib = missing_lib(text) if res == "FAIL" else ""
        row = {"family": fam, "rc": r.returncode, "result": "ABSENT" if lib else res}
        if lib:
            row["why"] = "缺套件 " + lib
        elif res == "FAIL":
            row["why_lines"] = why_lines(text)
    except subprocess.TimeoutExpired as exc:
        row = {"family": fam, "rc": 124, "result": "TIMEOUT", "timeout": timeout,
               "why_lines": ["逾時 %ss · 停在:" % timeout + " | ".join(why_lines(_txt(exc.stdout) + "\n" + _txt(exc.stderr), 3)
                                                                         if (exc.stdout or exc.stderr) else ["(沒有輸出)"])]}
    row["secs"] = round(time.time() - t0, 1)
    return row


_ORIG_RUN_ENGINES = V194.run_engines


def summarize(rows: list, lanes: int, secs: float, retried: list) -> dict:
    fail = [r for r in rows if r["result"] in ("FAIL", "TIMEOUT")]
    soft = [r for r in rows if r["result"] in ("NODATA", "ABSENT", "GATED")]
    lamp = "RED" if fail else ("YELLOW" if soft or not rows else "GREEN")
    slow = sorted(rows, key=lambda r: -r["secs"])[:3]
    return {"lamp": lamp, "tested": len(rows), "pass": sum(1 for r in rows if r["result"] == "PASS"), "fail": fail, "soft": soft,
            "lanes": lanes, "secs": round(secs, 1), "slowest": [(r["family"], r["secs"]) for r in slow], "rows": rows,
            "retried": retried}


def run_engines(items: list, lanes: int, timeout: int, env: dict, rc_map: dict, missing_lib, beat=None, guard=None) -> dict:
    """v0194 並行跑完 → 逾時的一支一支重跑(上限 ×2,最多 900 秒)→ 重算燈。"""
    t0 = time.time()
    kw = {"beat": beat} if guard is None else {"beat": beat, "guard": guard}
    res = _ORIG_RUN_ENGINES(items, lanes, timeout, env, rc_map, missing_lib, **kw)
    rows, retried = list(res["rows"]), []
    path = {fam: p for fam, p in items}
    t2 = min(RETRY_MAX, max(timeout * 2, timeout + 1))
    for i, r in enumerate(rows):
        if r["result"] != "TIMEOUT" or r["family"] not in path:
            continue
        if beat is not None:
            beat.state["①"] = f"重跑逾時的 {r['family']}({t2}s)"
        r2 = one_engine(r["family"], path[r["family"]], t2, env, rc_map, missing_lib)
        r2["retry_of"] = {"rc": r["rc"], "secs": r["secs"], "timeout": timeout}
        retried.append({"family": r["family"], "first": r["result"], "retry": r2["result"], "secs": r2["secs"]})
        rows[i] = r2
    return summarize(rows, res.get("lanes", lanes), time.time() - t0, retried)


def verb(args: list, timeout: int = 1800) -> tuple:
    """v0194 的子行程動詞,改跑家族尾版(本版以後的修正才到得了 closeout / health …)。"""
    env = dict(os.environ, PYTHONWARNINGS="ignore", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT"):
        env.pop(k, None)
    try:
        r = subprocess.run([sys.executable, str(tail_path()), *args], cwd=str(HERE), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, env=env, stdin=subprocess.DEVNULL)
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", "[逾時]"


V194.one_engine = one_engine
V194.run_engines = run_engines
V194.verb = verb

# ---------- ③ ④ 跨平台位元組與路徑 ----------


def lf_sha(b: bytes) -> str:
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()


def posix(rel: str) -> str:
    return str(rel).replace("\\", "/")


def _make_own_book(m):
    orig = vars(m)["v73_own_book"]

    def v73_own_book(root: Path, key: str) -> dict:
        r = orig(root, key)
        if not r.get("drift"):
            return r
        try:
            p = m.v73_tail(m.v73_dir(root) / "SSOT", m.V73_OWN[key])
            d = json.loads(p.read_text(encoding="utf-8"))
            src = root / d.get("source", "")
            if src.is_file() and lf_sha(src.read_bytes()) == d.get("source_sha256"):
                r = {**r, "lamp": "GREEN", "drift": False, "why": "", "eol": "CRLF 取出(換行統一成 LF 後雜湊相同)"}
        except (OSError, ValueError, KeyError, TypeError):
            pass                                               # 讀不了 → 照前版的黃(不放水)
        return r
    v73_own_book.__wrapped__ = orig
    return v73_own_book


def _make_number(m):
    def v73_number(root: Path) -> dict:
        """照 v0184 的判法;路徑一律正斜線、雜湊統一 LF(Windows 取出不再全部算「沒編號」)。"""
        eng = m.sm_engines(root)
        num = set()
        for p in (root / "supportive modules" / "registry" / "VIA_NumberBooks").glob("*.jsonl"):
            for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                if '"source"' in ln:
                    try:
                        r = json.loads(ln)
                    except ValueError:
                        continue
                    if not r.get("gone_since") and r.get("source"):
                        num.add(posix(r.get("source")))
        out = m.v73_out(root, "number")
        last_p = out / "VDF_NumberWatch_latest.json"
        last = json.loads(last_p.read_text(encoding="utf-8")).get("sha", {}) if last_p.is_file() else {}
        last = {posix(k): v for k, v in last.items()}
        sha, changed, unnum = {}, [], []
        for _fam, f in eng.items():
            rel = posix(f["tail"])
            p = root / rel
            if not p.is_file():
                continue
            h = lf_sha(p.read_bytes())
            sha[rel] = h
            if last and last.get(rel) != h:
                changed.append(rel)
            if rel not in num:
                unnum.append(rel)
        rec = {"at": m.sm_utc(), "tails": len(sha), "changed": changed, "unnumbered": unnum, "sha": sha, "eol": "LF", "sep": "/"}
        last_p.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        if unnum:
            (out / f"VDF_NumberRequest_{m.v73_stamp()}.json").write_text(json.dumps(
                {"system": "VDF", "law": "L125", "request": unnum, "how": "VCGC:run CGC_MDL237_NumberingSystem --apply --scope <檔>"},
                ensure_ascii=False, indent=1), encoding="utf-8")
        return {"lamp": "YELLOW" if unnum else "GREEN", "tails": len(sha), "changed_since_last": len(changed), "unnumbered": len(unnum),
                "first_run": not last, "examples": unnum[:5]}
    return v73_number


for _m in owners("v73_own_book"):
    _m.v73_own_book = _make_own_book(_m)
for _m in owners("v73_number"):
    _m.v73_number = _make_number(_m)

# ---------- ⑤ outputs:照 MDL249 的「轉得了」判法 ----------
CAST_FROM = {"date": {"str", "datetime"}, "datetime": {"str", "date"}, "int": {"str", "float"}, "float": {"str"}}
_ORIG_MEASURE = V195.measure                                   # = v0196.measure(find_dbs 找位置)


def measure(o: dict, home: Path) -> dict:
    m = _ORIG_MEASURE(o, home)
    if m.get("exists") is True:
        name = str(o.get("db") or o.get("file") or "")
        hit = V196.locate(home, name, V196._dp_p()) or (home / name)
        m["_where"] = {"path": str(hit), "table": o.get("table") if o.get("db") else None}
    return m


def _q(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def cast_bad(where: dict | None, col: str, want: str):
    """非空值裡轉不了 want 的筆數(與 MDL249 _castable 同判法);讀不了 → None(照舊黃)。只讀。"""
    if not where:
        return None
    import duckdb
    try:
        if where.get("table"):
            con = duckdb.connect(where["path"], read_only=True)
            src = _q(where["table"])
        else:
            con = duckdb.connect()
            src = "read_parquet('" + where["path"].replace("'", "''") + "')"
        try:
            c = _q(col)
            v = f"CAST({c} AS VARCHAR)"
            nonempty = f"{c} IS NOT NULL AND trim({v}) <> ''"
            if want in ("int", "float"):
                d = f"TRY_CAST({v} AS DOUBLE)"
                nonempty += f" AND NOT ({d} IS NOT NULL AND isnan({d}))"
                bad = con.execute(f"SELECT COUNT(*) FILTER (WHERE {d} IS NULL) FROM {src} WHERE {nonempty}").fetchone()[0]
                if want == "int":
                    bad += con.execute(f"SELECT COUNT(*) FILTER (WHERE {d} IS NOT NULL AND {d} % 1 <> 0) FROM {src} WHERE {nonempty}").fetchone()[0]
                return int(bad)
            if want in ("date", "datetime"):
                rows = con.execute(f"SELECT {v} AS s, COUNT(*) FROM {src} WHERE {nonempty} AND TRY_CAST({v} AS TIMESTAMP) IS NULL "
                                   f"GROUP BY 1 LIMIT 50001").fetchall()
                if not rows:
                    return 0
                if len(rows) > 50000:
                    return int(sum(n for _s, n in rows))     # 太多種寫法 → 不複核,照實算轉不了
                import pandas as pd
                parsed = pd.to_datetime(pd.Series([s for s, _n in rows]).astype(str), errors="coerce")
                return int(sum(n for (_s, n), ok in zip(rows, parsed.notna()) if not ok))
            return None
        finally:
            con.close()
    except Exception:  # noqa: BLE001 — 庫被占用 / 缺套件:照舊黃,不放水
        return None


def judge(spec: dict, m: dict) -> tuple:
    """v0195 的判法 + 型別對不上時看值轉不轉得了(MDL249 同判法)。"""
    got = {n: t for n, t, _raw in m["columns"]}
    red, yellow, notes = [], [], []
    for c in spec.get("columns") or []:
        n, want = c["name"], c.get("dtype", "str")
        if n not in got:
            (red if (c.get("required") or c.get("key")) else yellow).append(f"缺{'鍵' if c.get('key') else '必填' if c.get('required') else ''}欄 {n}")
        elif not V195.type_ok(want, got[n]):
            bad = cast_bad(m.get("_where"), n, want) if got[n] in CAST_FROM.get(want, ()) else None
            if bad == 0:
                notes.append(f"{n} 存成 {got[n]} · 值全部轉得了 {want}")
            elif bad is None:
                yellow.append(f"{n} 型別 {got[n]}≠{want}")
            else:
                yellow.append(f"{n} 型別 {got[n]}≠{want} · {bad} 筆轉不了")
    mr = spec.get("min_rows")
    if isinstance(mr, int) and m["rows"] < mr:
        yellow.append(f"列 {m['rows']} < min_rows {mr}")
    m["cast_notes"] = notes
    return ("RED" if red else "YELLOW" if yellow else "GREEN"), red + yellow


V195.measure = measure
V195.judge = judge


def print_reasons(root: Path) -> None:
    """vv 跑完:在畫面補印每支不過的原因(收據 engine_rows[].why_lines)。"""
    try:
        rep = json.loads((V194._p("v73_out")(root) / "VV_latest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    rows = rep.get("engine_rows") or []
    bad = [r for r in rows if r.get("result") in ("FAIL", "TIMEOUT")]
    re_ok = [r for r in rows if r.get("retry_of")]
    if re_ok:
        print(f"  [重跑] 逾時的 {len(re_ok)} 支一支一支重跑:" + " · ".join(f"{r['family']}→{r['result']}({r['secs']}s)" for r in re_ok))
    for r in bad:
        lines = root_first(r.get("why_lines") or [])[:2]
        print(f"  [原因] {r['family']} · rc {r.get('rc')}" + ("".join(f"\n         {ln}" for ln in lines) if lines else " · (沒有輸出)"))


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 8 項 + 前版 {PRIOR_PATH.name} 自測 · 暫存夾 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路橋在", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)
    txt = "  [OK] a\n  [FAIL] ⑫ 前版鏈自測照過 · rc 1\n  [NG] 真正不過的那檢\nTraceback (most recent call last):\nValueError: x\n"
    w = why_lines(txt)
    chk("T2 原因行:FAIL / NG / Traceback / Error 都收;根因排前面;沒有一行時取最後三行",
        w[:2] == ["[FAIL] ⑫ 前版鏈自測照過 · rc 1", "[NG] 真正不過的那檢"] and root_first(w)[0] == "[NG] 真正不過的那檢"
        and why_lines("a\nb\nc\nd") == ["b", "c", "d"], w)
    rc_map = {0: "PASS", 2: "NODATA", 3: "ABSENT", 4: "GATED"}
    with tempfile.TemporaryDirectory(prefix="vdf_sm197_") as td:
        d = Path(td)
        bad = d / "FX_bad_v0100.py"
        bad.write_text("import sys\nprint('  [OK] x')\nprint('  [NG] y 不過')\nsys.exit(1)\n", encoding="utf-8")
        slow = d / "FX_slow_v0100.py"
        slow.write_text("import sys,time\nprint('起', flush=True)\ntime.sleep(2.5)\nsys.exit(0)\n", encoding="utf-8")
        r = one_engine("FX_bad", bad, 30, dict(os.environ), rc_map, lambda t: "")
        chk("T3 不過的引擎:收據帶原因行(印 [NG] 的也抓得到)", r["result"] == "FAIL" and "[NG] y 不過" in r.get("why_lines", []), r)
        res = run_engines([("FX_slow", slow), ("FX_bad", bad)], 2, 2, dict(os.environ), rc_map, lambda t: "", guard=lambda: False)
        by = {x["family"]: x for x in res["rows"]}
        chk("T4 逾時的一支一支重跑(上限 ×2):重跑過了記 PASS(重跑)· 真不過的照紅 · 燈重算",
            by["FX_slow"]["result"] == "PASS" and by["FX_slow"].get("retry_of", {}).get("rc") == 124
            and res["retried"][0]["retry"] == "PASS" and res["lamp"] == "RED" and [x["family"] for x in res["fail"]] == ["FX_bad"], res)
        # ③ 自有冊 CRLF
        m184 = owners("v73_own_book")[0]
        root = d / "via"
        sd = m184.v73_dir(root) / "SSOT"
        sd.mkdir(parents=True)
        (root / "x").mkdir()
        body = b'{"a": 1}\n{"b": 2}\n'
        (root / "x" / "src.json").write_bytes(body.replace(b"\n", b"\r\n"))
        pat = m184.V73_OWN["regex"].replace("v*", "v0100")
        (sd / pat).write_text(json.dumps({"source": "x/src.json", "source_sha256": hashlib.sha256(body).hexdigest(), "body": {"a": 1}}),
                              encoding="utf-8")
        g = m184.v73_own_book(root, "regex")
        (root / "x" / "src.json").write_bytes(b'{"a": 9}\r\n')
        y = m184.v73_own_book(root, "regex")
        chk("T5 自有冊:Windows 取出的 CRLF 來源 → 綠(eol 註記);內容真的換了 → 照舊黃", g["lamp"] == "GREEN" and g.get("eol")
            and y["lamp"] == "YELLOW" and y["drift"] is True, (g, y))
        # ④ 編號比對路徑分隔
        mn = owners("v73_number")[0]
        eng = root / "functional modules" / "VDF" / "VDF_FX_v0100.py"
        eng.parent.mkdir(parents=True, exist_ok=True)
        eng.write_bytes(b"x = 1\r\n")
        nb = root / "supportive modules" / "registry" / "VIA_NumberBooks"
        nb.mkdir(parents=True)
        (nb / "fx.jsonl").write_text(json.dumps({"source": "functional modules/VDF/VDF_FX_v0100.py"}) + "\n", encoding="utf-8")
        keep = getattr(mn, "sm_engines")
        mn.sm_engines = lambda r: {"VDF_FX": {"tail": "functional modules\\VDF\\VDF_FX_v0100.py", "tail_ver": 100, "versions": 1}}
        try:
            n1 = mn.v73_number(root)
        finally:
            mn.sm_engines = keep
        chk("T6 編號比對:Windows 反斜線尾版路徑對得上冊上的正斜線 → 0 支沒編號 · 雜湊統一 LF",
            n1["lamp"] == "GREEN" and n1["unnumbered"] == 0 and n1["tails"] == 1, n1)
        # ⑤ outputs 轉得了
        import duckdb
        dbp = d / "fx.duckdb"
        c = duckdb.connect(str(dbp))
        c.execute("CREATE TABLE t(date VARCHAR, d2 VARCHAR, pe DOUBLE, pe2 DOUBLE)")
        c.execute("INSERT INTO t VALUES ('2026-01-02','2026-01-02',15.0,15.0),('20260105','x',16.0,16.5),(NULL,'',NULL,NULL)")
        c.close()
        mm = {"exists": True, "rows": 3, "columns": [("date", "str", "VARCHAR"), ("d2", "str", "VARCHAR"), ("pe", "float", "DOUBLE"),
                                                     ("pe2", "float", "DOUBLE")], "_where": {"path": str(dbp), "table": "t"}}
        spec = {"columns": [{"name": "date", "dtype": "date", "key": True}, {"name": "d2", "dtype": "date"},
                            {"name": "pe", "dtype": "int"}, {"name": "pe2", "dtype": "int"}], "min_rows": 1}
        lamp, probs = judge(spec, mm)
        chk("T7 outputs:字串日期全部轉得了 → 對(含 20260105 這種寫法)· 轉不了的照筆數黃 · 小數存整數欄要全是整數",
            lamp == "YELLOW" and probs == ["d2 型別 str≠date · 1 筆轉不了", "pe2 型別 float≠int · 1 筆轉不了"]
            and len(mm["cast_notes"]) == 2, (lamp, probs, mm.get("cast_notes")))
    chk("T8 vv 的 ② / ③ 子行程跑家族尾版;並行 / 逐支 / 判法換成本版", V194.verb is verb and tail_path() == max(HERE.glob(STEM + "_v*.py"), key=_vnum)
        and V194.run_engines is run_engines and V195.judge is judge and V195.measure is measure)
    rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 1
    chk("T9 前版 v0196 自測照過(含整條前版鏈)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if a[:1] == ["vv"]:
        if "--timeout" not in a:
            a += ["--timeout", str(VV_TIMEOUT_DEFAULT)]
        rc = PRIOR.main(a)
        if "--json" not in a:
            print_reasons(V194._p("sm_via_root")())
        return rc
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
