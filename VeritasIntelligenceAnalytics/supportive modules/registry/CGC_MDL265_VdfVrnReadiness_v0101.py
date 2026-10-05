#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL265_VdfVrnReadiness v0101 — 薄尾:監控提速(各探測同時跑 · 覆蓋率依程式樹狀態快取)

操作員 2026-10-05:「PS PY 都有加加速器?VDF 都有加網路工具?剛才很慢」。
  實測 v0100(容器):① 監控 120s = 覆蓋率 68s(每次全樹重掃 bridge · celer · accel)+ 環境 27 + 13 + 3s(依序)+ token 2.5s。
  本版只蓋 readiness:
  · token · RunGate vdf · RunGate vrn · LKGC · 覆蓋率 五個探測彼此獨立 → 同時起(執行緒各起一個 VCGC 子行程);
    顯示照原順序、燈與判定一字照 v0100(p_token / p_rungate / p_lkgc / p_coverage / repair_plan 都用前版的)。
  · 覆蓋率快取:鍵 = git HEAD + 工作區變動清單 + 每個變動 / 未追蹤的程式 · 設定檔內容指紋(執行時寫的帳本 / 收據除外)的 sha;樹沒變且 24h 內 = 沿用上次報告(照實標「沿用 · 幾時掃的」);
    有改檔 / 換 HEAD / 過期 / 讀不到 git = 重掃。--fresh 一律重掃。快取在 VIA_Reports/activate_vdf/coverage_cache.json(不進 git)。
  · --repair 照 v0100 依序(修了環境要重探,不並行)。
用法:via-vcgc run CGC_MDL265_VdfVrnReadiness [--repair] [--fresh] [--only 步,步] [--json] · --selftest
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
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
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _prior_path() -> Path:
    """前版 = 同家族比本檔小的最大版號(不釘名,避免 PINVER)。"""
    me = int(Path(__file__).stem.rsplit("_v", 1)[1])
    hits = [p for p in HERE.glob("CGC_MDL265_VdfVrnReadiness_v*.py") if re.search(r"_v\d+$", p.stem) and int(p.stem.rsplit("_v", 1)[1]) < me]
    return max(hits, key=lambda p: int(p.stem.rsplit("_v", 1)[1]))


PRIOR_PATH = _prior_path()
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0101", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


ENGINE = Path(__file__).stem
VIA = PRIOR.VIA
OUT_DIR = PRIOR.OUT_DIR
STEPS = PRIOR.STEPS
FAMILIES = PRIOR.FAMILIES
CACHE = OUT_DIR / "coverage_cache.json"
CACHE_TTL_S = int(os.environ.get("VIA_COVERAGE_CACHE_S") or 24 * 3600)
PRECHECK_ARGS = ["run", "CGC_MDL263_Precheck", "--only", "bridge,celer,accel"]
PRECHECK_REPORT = VIA / "VIA_Reports" / "precheck" / "PRECHECK_latest.json"
RUN = PRIOR.run_vcgc          # 自測可換


# ---------- 覆蓋率快取 ----------
def _file_sig(path: Path) -> str:
    """改過 / 沒進版控的檔的內容指紋:8MB 內讀全檔 sha256;更大用 大小 + 修改時間(ns);讀不到 = 標記。"""
    try:
        st = path.stat()
        if not path.is_file():
            return "dir"
        if st.st_size > 8 * 1024 * 1024:
            return f"big:{st.st_size}:{st.st_mtime_ns}"
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return "gone"


SIG_SUFFIX = {".py", ".ps1", ".psm1", ".psd1", ".json", ".jsonl", ".yml", ".yaml", ".toml"}   # 會影響覆蓋率掃描的檔
VOLATILE = re.compile(r"Ledger|/evidence/|_latest\.|Lessons", re.I)   # 每次 VCGC 執行都會寫的帳本 / 收據:內容不進鍵(清單照進)


def tree_key(root: Path | None = None) -> str | None:
    """git HEAD + 工作區變動清單 + 每個變動 / 未追蹤檔的內容指紋 的 sha;讀不到 git = None(= 不用快取,照掃)。
    只看清單不夠:已改過的檔再改,清單一字不變(Codex 審查 #495)→ 內容指紋一定要進鍵。"""
    root = Path(root or VIA)
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(root), capture_output=True, text=True, timeout=60)
        st = subprocess.run(["git", "status", "--porcelain", "-uall", "-z"], cwd=str(root), capture_output=True, timeout=120)
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=str(root), capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if head.returncode or st.returncode or top.returncode:
        return None
    h = hashlib.sha256(head.stdout.strip().encode() + b"\n" + st.stdout)
    base = Path(top.stdout.strip())
    entries = st.stdout.split(b"\0")
    i = 0
    while i < len(entries):
        e = entries[i]
        i += 1
        if len(e) < 4:
            continue
        code, rel = e[:2], e[3:].decode("utf-8", "replace")
        if code[:1] in (b"R", b"C"):            # 改名 / 複製:-z 下來源路徑另佔一格
            i += 1
        sig = _file_sig(base / rel) if Path(rel).suffix.lower() in SIG_SUFFIX and not VOLATILE.search(rel) else "-"
        h.update(rel.encode("utf-8", "replace") + b"=" + sig.encode())
    return h.hexdigest()[:20]


def cache_get(key: str | None, now: float | None = None) -> dict | None:
    if not key:
        return None
    try:
        c = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    now = time.time() if now is None else now
    if c.get("key") != key or now - float(c.get("at") or 0) > CACHE_TTL_S or not isinstance(c.get("report"), dict):
        return None
    return c


def cache_put(key: str | None, report: dict, sec: float) -> None:
    if not key or not report:
        return
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps({"key": key, "at": time.time(), "sec": sec, "report": report}, ensure_ascii=False, default=str), encoding="utf-8")


def _rel(p: Path) -> str:
    try:
        return Path(p).resolve().relative_to(VIA.resolve()).as_posix()
    except ValueError:
        return str(p)


# ---------- 主流程(探測並行;顯示 · 判定照前版) ----------
def readiness(repair: bool = False, only: set | None = None, fresh: bool = False) -> dict:
    t0 = time.time()
    want = (lambda k: (not only) or k in only)
    rows: list = []
    stamp = PRIOR.stamp
    print(f"=== VCGC 母系統監控 · {ENGINE} · VRN / VDF 工具 · 環境 · 加速器 / 網路工具覆蓋(探測並行 · 覆蓋率快取)===", flush=True)

    key = None if fresh else tree_key()
    cached = cache_get(key) if want("coverage") else None
    jobs = {}
    if want("vcgc"):
        jobs["token"] = (["token"], 600)
    if want("env") or want("repair"):
        for fam in FAMILIES:
            jobs["rg_" + fam] = (["run", "CGC_MDL137_RunGate", "probe", "--family", fam], 900)
        jobs["lkgc"] = (["run", "CGC_MDL135_EnvGovernance", "lkgc", "status"], 600)
    if want("coverage") and not cached:
        jobs["coverage"] = (PRECHECK_ARGS, PRIOR.TIMEOUT)
    pool = ThreadPoolExecutor(max_workers=max(1, len(jobs)))
    fut = {k: pool.submit(RUN, a, t) for k, (a, t) in jobs.items()}
    try:
        if want("vcgc"):
            print("  [1/4] VCGC 啟動(省 Token 工具卡:工具經鎖冊啟用 · 實測過)", flush=True)
            rc, out, sec = fut["token"].result()
            lamp, summ = PRIOR.p_token(rc, out)
            stamp(rows, "vcgc", lamp, f"token {summ}", sec)

        env_lamps, lkgc = {}, {}
        if want("env") or want("repair"):
            print("  [2/4] 環境檢查(VDF · VRN 家族境 RunGate probe · LKGC 版本鎖)", flush=True)
            for fam in FAMILIES:
                rc, out, sec = fut["rg_" + fam].result()
                lamp, summ = PRIOR.p_rungate(rc, out)
                env_lamps[fam] = lamp
                stamp(rows, "env", lamp, f"{fam} {summ}", sec, family=fam)
            rc, out, sec = fut["lkgc"].result()
            lkgc = PRIOR.p_lkgc(rc, out)
            stamp(rows, "env", "GREEN" if lkgc.get("eligible") else "YELLOW",
                  f"LKGC {lkgc.get('latest')} · verdict {lkgc.get('verdict')}(你測過全綠時存的版本鎖;非 GREEN = 修理改走 RunGate 補缺件)", sec, family="lkgc")

        if want("repair"):
            gate = PRIOR.consent_open()
            plan = PRIOR.repair_plan(env_lamps, lkgc, gate)
            if not plan:
                stamp(rows, "repair", "GREEN", "家族境都綠 → 不用修")
            elif not repair:
                stamp(rows, "repair", "YELLOW", f"有 {len(plan)} 項待修;加 --repair 才動手(只裝進 via_* 隔離境,不刪 base)", plan=plan)
            elif not gate:
                stamp(rows, "repair", "YELLOW", "GATED:安裝要連網,本視窗先開雙閘(操作員的手,本令永不代設):"
                      "$env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='YES' → 再跑 via_activate_vdf --repair", plan=plan)
            else:
                done = []
                for act in plan:                       # 修理照前版依序(修了要重探,不並行)
                    rc, out, sec = RUN(act["argv"], PRIOR.TIMEOUT)
                    act.update({"state": "DONE" if rc == 0 else "FAIL", "rc": rc, "sec": sec, "tail": PRIOR.clean(out)[-3:]})
                    done.append(act)
                for fam in list(env_lamps):
                    rc, out, sec = RUN(["run", "CGC_MDL137_RunGate", "probe", "--family", fam, "--fresh"], 900)
                    env_lamps[fam] = PRIOR.p_rungate(rc, out)[0]
                ok = all(a["state"] == "DONE" for a in done) and all(v == "GREEN" for v in env_lamps.values())
                stamp(rows, "repair", "GREEN" if ok else "RED", f"修理 {len(done)} 項 · 修後 RunGate {env_lamps}", plan=done)

        if want("coverage"):
            print("  [3/4] 覆蓋率(PY 加速器 · VDF 網路工具 · PS 模板 · 25 加速器控制面)", flush=True)
            if cached:
                rep, sec = cached["report"], 0.0
                when = datetime.fromtimestamp(float(cached["at"]), timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                tag = f" · 沿用(程式樹沒變 · {when} 掃的 {cached.get('sec')}s;--fresh 重掃)"
            else:
                rc, out, sec = fut["coverage"].result()
                try:
                    rep = json.loads(PRECHECK_REPORT.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    rep = {}
                if rc in (0, 1, 2) and rep:
                    cache_put(key, rep, sec)
                tag = ""
            lamp, summ, fnd = PRIOR.p_coverage(rep)
            by = {}
            for f in fnd:
                by.setdefault(PRIOR.finding_owner(f), []).append(f"{f.get('id')} {f.get('lamp')} {f.get('class') or f.get('cls')} {PRIOR.where_of(f) or f.get('detail', '')}")
            note = " · ".join(f"{k} {len(v)}" for k, v in by.items())
            stamp(rows, "coverage", lamp, summ + tag + (f" · 黃紅歸屬 {note}(L111:子系統的由子系統修,VCGC 出資訊卡)" if note else ""), sec,
                  findings=by, cached=bool(cached))
    finally:
        pool.shutdown(wait=True)

    lamps = [r["lamp"] for r in rows]
    overall = "RED" if "RED" in lamps else ("YELLOW" if "YELLOW" in lamps else "GREEN")
    rep = {"engine": ENGINE, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "overall": overall,
           "repair": repair, "consent_open": PRIOR.consent_open(), "parallel": True, "coverage_cached": bool(cached),
           "steps": rows, "sec": round(time.time() - t0, 1)}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "READINESS_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"  [4/4] [VCGC 監控] {overall} · 站 {len(rows)}(綠 {lamps.count('GREEN')} · 黃 {lamps.count('YELLOW')} · 紅 {lamps.count('RED')})"
          f" · {rep['sec']}s(探測並行{' · 覆蓋率沿用' if cached else ''})· 報告 {_rel(OUT_DIR / 'READINESS_latest.json')}", flush=True)
    return rep


# ---------- 自測 ----------
def selftest() -> int:
    import shutil
    import tempfile
    res = []

    def chk(name, cond, note=""):
        res.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""))

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        prior_rc = PRIOR.selftest()
    for ln in buf.getvalue().splitlines():           # 前版成功標記照印(舊交接案認的是它)
        if ln.strip().startswith("[計]"):
            print(ln)
    chk("① v0100 自測照過(11 檢 · 含 pwsh mock)", prior_rc == 0, buf.getvalue()[-300:])
    global RUN, OUT_DIR, CACHE, PRECHECK_REPORT
    keep = (RUN, OUT_DIR, CACHE, PRECHECK_REPORT, PRIOR.OUT_DIR)
    tmp = Path(tempfile.mkdtemp(prefix="mdl265v1_"))
    try:
        OUT_DIR = PRIOR.OUT_DIR = tmp / "out"
        CACHE = OUT_DIR / "coverage_cache.json"
        PRECHECK_REPORT = tmp / "PRECHECK_latest.json"
        calls, starts = [], {}
        fake_rep = {"stations": [], "findings": []}

        def fake(args, timeout=0):
            k = " ".join(map(str, args[:3]))
            starts[k] = time.time()
            calls.append(k)
            time.sleep(0.6)
            if args[:2] == ["run", "CGC_MDL263_Precheck"]:
                PRECHECK_REPORT.write_text(json.dumps(fake_rep), encoding="utf-8")
                return 0, "", 0.6
            if args[:2] == ["run", "CGC_MDL137_RunGate"]:
                return 0, "[RunGate] GREEN", 0.6
            return 0, "", 0.6

        ran_pre = (lambda: any(c.startswith("run CGC_MDL263_Precheck") for c in calls))
        RUN = fake
        t0 = time.time()
        with contextlib.redirect_stdout(io.StringIO()):
            rep1 = readiness()
        wall = time.time() - t0
        chk("② 五個探測同時起(token · RunGate vdf / vrn · LKGC · 覆蓋率):各 0.6s,整輪 < 2s(依序要 3s)",
            len(calls) == 5 and wall < 2.0 and max(starts.values()) - min(starts.values()) < 0.5, (round(wall, 2), calls))
        chk("③ 顯示照原順序、判定照前版:vcgc → env×3 → repair → coverage;報告標 parallel", [r["step"] for r in rep1["steps"]] ==
            ["vcgc", "env", "env", "env", "repair", "coverage"] and rep1["parallel"] is True and rep1["coverage_cached"] is False, rep1["steps"])
        key = tree_key()
        hit = cache_get(key)
        chk("④ 掃完存快取(鍵 = git HEAD + 工作區變動);同一棵樹再讀 = 命中", key and hit and hit["report"] == fake_rep, (key, hit))
        calls.clear()
        with contextlib.redirect_stdout(io.StringIO()):
            rep2 = readiness()
        chk("⑤ 樹沒變再跑 = 覆蓋率沿用、不再起 precheck;燈照算;報告標 coverage_cached",
            calls and not ran_pre() and rep2["coverage_cached"] is True and rep2["steps"][-1]["step"] == "coverage", calls)
        calls.clear()
        with contextlib.redirect_stdout(io.StringIO()):
            readiness(fresh=True)
        chk("⑥ --fresh 一律重掃", ran_pre(), calls)
        repo = tmp / "repo"
        repo.mkdir()
        g = (lambda *x: subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *x], cwd=str(repo), capture_output=True))
        g("init", "-q")
        (repo / "a.py").write_text("x = 1\n", encoding="utf-8")
        g("add", "a.py")
        g("commit", "-q", "-m", "init")
        (repo / "a.py").write_text("x = 2\n", encoding="utf-8")
        (repo / "new.py").write_text("y = 1\n", encoding="utf-8")
        k1 = tree_key(repo)
        (repo / "a.py").write_text("x = 3\n", encoding="utf-8")          # 已改過的檔再改:清單不變
        k2 = tree_key(repo)
        (repo / "new.py").write_text("y = 2\n", encoding="utf-8")        # 未追蹤檔再改:清單不變
        k3 = tree_key(repo)
        k3b = tree_key(repo)
        (repo / "VIA_Lessons_Ledger_v0100.json").write_text("[1]", encoding="utf-8")
        k4 = tree_key(repo)
        (repo / "VIA_Lessons_Ledger_v0100.json").write_text("[1, 2]", encoding="utf-8")   # 每次執行都會寫的帳本:內容變不換鍵
        k5 = tree_key(repo)
        chk("⑩ 快取鍵含內容指紋:已改過 / 未追蹤的檔再改 → 鍵變(清單一字不變也一樣);沒動 → 鍵不變;執行時寫的帳本只進清單不進內容(Codex #495 P1)",
            k1 and k2 and k3 and len({k1, k2, k3}) == 3 and k3 == k3b and k4 == k5 and k4 != k3, (k1, k2, k3, k3b, k4, k5))
        chk("⑦ 鍵不同 / 過期 / 空鍵都不命中", cache_get("other-key") is None and cache_get(key, now=time.time() + CACHE_TTL_S + 5) is None
            and cache_get(None) is None)
        calls.clear()
        with contextlib.redirect_stdout(io.StringIO()):
            rep3 = readiness(only={"coverage"})
        chk("⑧ --only coverage 只跑覆蓋率(命中快取 = 零子行程)", not calls and [r["step"] for r in rep3["steps"]] == ["coverage"], calls)
    finally:
        RUN, OUT_DIR, CACHE, PRECHECK_REPORT, PRIOR.OUT_DIR = keep
        shutil.rmtree(tmp, ignore_errors=True)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 加速器橋 · 網路工具橋在;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", text))
    ok = sum(res)
    print(f"[計] {ENGINE} 自測 {ok}/{len(res)} · v0100 鏈 {'PASS' if prior_rc == 0 else 'FAIL'} · {'PASS' if ok == len(res) else 'FAIL'}")
    return 0 if ok == len(res) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    if a[:1] in (["-h"], ["--help"]):
        print(__doc__)
        return 0
    only = set(a[a.index("--only") + 1].split(",")) if "--only" in a and a.index("--only") + 1 < len(a) else None
    if only and not only <= set(STEPS):
        print(f"  [VCGC 監控] --only 只收 {','.join(STEPS)};收到 {sorted(only - set(STEPS))}")
        return 2
    rep = readiness(repair="--repair" in a, only=only, fresh="--fresh" in a)
    if "--json" in a:
        print(json.dumps(rep, ensure_ascii=False, default=str))
    return {"GREEN": 0, "YELLOW": 2, "RED": 1}[rep["overall"]]


if __name__ == "__main__":
    raise SystemExit(main())
