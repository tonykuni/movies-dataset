#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL056_InstallGate v0105 — 薄尾(v0104 一字不動):先三鏡像查衝突 → 環境確認無誤 → 依計畫一次裝 → 裝後一次驗

操作員 2026-11-24 主機實跑 via-health 後原文:「速度太慢 … 加速器跟網路工具 LIB 環境都有透過 VCGC 安裝無衝突嗎
  更快先檢查經過衝突檢測三鏡像共同檢查衝突後環境確認無誤進行安裝計畫 依計畫安裝不用邊裝邊測 這個流程要寫入環境安裝規範」。
  主機那一輪:doctor 計畫 10 件一起丟進 v0104 → 21.7 秒 rc 1(一件解不出就整批不裝,也不知道是哪一件);
  v0104 是「裝前 pip check → 裝 → 裝後 pip check」,衝突要裝下去才看得到。
本版加兩個動作(都不改 v0104 的安裝路):
  --plan-check <件…>  零安裝。① 三鏡像(清華 · 阿里 · 官方 PyPI;正本 VIA_EnvGovernance_Baseline 的 mirror_chain)
                      同時 pip install --dry-run --report 解析整份計畫;② 解不出 → 逐件再解,把解不出的件點名剔除、其餘再解一次;
                      ③ 三鏡像結果互相比(版本不同 = 鏡像不同步,以官方 PyPI 為準);④ 把解出的版本疊到「現在已裝的」上
                      推算裝後會不會新增相依衝突(套件自己宣告的 requires_dist,用 packaging 判);⑤ 要從原始碼建置的件(sdist)點名。
                      結果寫 VIA_Reports/install_gate/PLANCHECK_latest.json:燈 · 每個鏡像 · 計畫(全部釘版)· 剔除 · 預估新衝突。
                      ⑥ 特殊環境及分類一律單獨安裝:Baseline 的 package_env_overrides / families 成員不進 base 計畫,
                      列出目標境(via-envgov plan → apply --approve 逐境裝)。
  --from-plan         只照最新一份 PLANCHECK 裝:燈紅 / 灰 / 過期(6 小時)/ 別台機器的 → 拒絕(零安裝)。
                      計畫已檢測無誤 → 直接執行、不再測(操作員 2026-11-24「直接執行計畫無須再測」):
                      一次裝完整份釘版計畫(--no-deps,不讓 pip 臨場改計畫;索引用計畫的參考鏡像)。append-only 記進 VIA_Lib_Registry。
網路:兩個動作都要 VIA_NET_CONSENT=YES(由 VCGC 中樞只在本子行程設;本檔不設、不寫);沒開 → 灰 NOT_RUN,零安裝。
不 import 他系統。零 TA-Lib。
用法:CGC_MDL056_InstallGate_v0105.py --plan-check <件…> | --from-plan | --selftest | (其餘照 v0104)
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
import platform
import re
import site
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve()
FAMILY = "CGC_MDL056_InstallGate"
TAG = "CGC_MDL056_InstallGate v0105"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0105", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
VIA = PRIOR.VIA
BASELINE = HERE.parent / "VIA_EnvGovernance_Baseline_v0100.json"
DEFAULT_MIRRORS = [("tsinghua", "https://pypi.tuna.tsinghua.edu.cn/simple"), ("aliyun", "https://mirrors.aliyun.com/pypi/simple/"),
                   ("pypi-official", "https://pypi.org/simple")]
REFERENCE = "pypi-official"
PLAN_MAX_AGE = 6 * 3600
RESOLVE_TIMEOUT = 300
_NET_RX = re.compile(r"ConnectionError|NewConnectionError|Max retries|timed out|ProxyError|SSLError|Temporary failure|"
                     r"Name or service not known|getaddrinfo|ConnectTimeout|ReadTimeout|Network is unreachable|403 Forbidden|407", re.I)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def out_dir() -> Path:
    return Path(os.environ.get("VIA_ROOT") or VIA) / "VIA_Reports" / "install_gate"


def canon(name: str) -> str:
    return re.sub(r"[-_.]+", "-", str(name)).lower()


def mirrors() -> list:
    """正本:VIA_EnvGovernance_Baseline 的 mirror_chain(清華 → 阿里 → 官方);讀不到用同樣三個。"""
    try:
        mc = json.loads(BASELINE.read_text(encoding="utf-8")).get("mirror_chain") or {}
        got = list(zip(mc.get("labels") or [], mc.get("order") or []))
        if len(got) >= 3:
            return got
    except (OSError, ValueError):
        pass
    return list(DEFAULT_MIRRORS)


_TEST = {}                                                # 只給自測換掉同意閘判讀(不碰環境變數)


def route(pkgs: list) -> tuple:
    """特殊環境及分類一律單獨安裝(操作員 2026-11-24):Baseline 的 package_env_overrides / families 成員 → 不進 base,
    列出它的目標境(由 via-envgov 逐境裝);其餘才是 base 計畫。回 (base 件, [{pkg, family, env}])。"""
    try:
        b = json.loads(BASELINE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return list(pkgs), []
    ov = {canon(k): v for k, v in (b.get("package_env_overrides") or {}).items()}
    fam = {}
    for fk, f in (b.get("families") or {}).items():
        for m in f.get("members") or []:
            fam.setdefault(canon(m), (fk, f.get("target_env")))
    base, special = [], []
    for p in pkgs:
        n = canon(re.split(r"[<>=!~;\[ ]", p, maxsplit=1)[0])
        if n in ov:
            special.append({"pkg": p, "family": "override", "env": ov[n]})
        elif n in fam:
            special.append({"pkg": p, "family": fam[n][0], "env": fam[n][1]})
        else:
            base.append(p)
    return base, special


def _consent() -> bool:
    if "consent" in _TEST:
        return _TEST["consent"]
    return os.environ.get("VIA_NET_CONSENT", "").upper() == "YES"


def _user_flag() -> list:
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    return ["--user"] if (not in_venv and site.ENABLE_USER_SITE) else []


def resolve_argv(pkgs: list, url: str, report: Path) -> list:
    return [sys.executable, "-m", "pip", "install", "--dry-run", "--quiet", "--disable-pip-version-check", "--no-input",
            "--report", str(report), "--index-url", url, "--timeout", "20", "--retries", "1", *_user_flag(), *pkgs]


def _run_bounded(argv, timeout: float, late=lambda: False):
    """子行程跑到結束 / 逾時 / 別的鏡像早就答完(late)為止;超時整個砍掉。回跟 subprocess.run 一樣的欄位。"""
    with tempfile.TemporaryFile() as fo, tempfile.TemporaryFile() as fe:
        p = subprocess.Popen(argv, stdout=fo, stderr=fe, stdin=subprocess.DEVNULL)
        t0 = time.time()
        while p.poll() is None:
            if time.time() - t0 > timeout or late():
                p.kill()
                p.wait()
                raise subprocess.TimeoutExpired(argv, timeout)
            time.sleep(0.3)
        fo.seek(0)
        fe.seek(0)
        R = type("R", (), {})
        r = R()
        r.returncode = p.returncode
        r.stdout, r.stderr = fo.read().decode("utf-8", "replace"), fe.read().decode("utf-8", "replace")
        return r


def resolve(pkgs: list, label: str, url: str, timeout: int = RESOLVE_TIMEOUT, run=None, late=lambda: False) -> dict:
    """一個鏡像解一次(零安裝)。回 state:RESOLVED · FAIL(套件解不出)· UNREACHABLE(連不到 / 逾時 / 比別的鏡像慢太多)。"""
    t0 = time.time()
    with tempfile.TemporaryDirectory(prefix="via_plancheck_") as td:
        rep = Path(td) / "report.json"
        try:
            if run is None:
                r = _run_bounded(resolve_argv(pkgs, url, rep), timeout, late)
            else:
                r = run(resolve_argv(pkgs, url, rep), capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
            text = (r.stdout or "") + (r.stderr or "")
            items = []
            if r.returncode == 0 and rep.exists():
                items = json.loads(rep.read_text(encoding="utf-8")).get("install") or []
                state = "RESOLVED"
            else:
                state = "UNREACHABLE" if (_NET_RX.search(text) and not re.search(r"ResolutionImpossible|No matching distribution|"
                                                                                   r"Could not find a version", text, re.I)) else "FAIL"
        except subprocess.TimeoutExpired:
            secs = time.time() - t0
            state, text, items = "UNREACHABLE", ("逾時 %ds" % timeout) if secs >= timeout else ("%ds 還沒答完,別的鏡像早已答完 → 視為沒回應" % secs), []
    plan = {}
    meta = {}
    for it in items:
        md = it.get("metadata") or {}
        n, v = canon(md.get("name", "")), md.get("version", "")
        if n:
            plan[n] = v
            url_ = ((it.get("download_info") or {}).get("url") or "")
            meta[n] = {"requires": md.get("requires_dist") or [], "sdist": not url_.split("?")[0].endswith(".whl"),
                       "requested": bool(it.get("requested"))}
    tail = [ln for ln in text.strip().splitlines() if ln.strip()][-3:]
    return {"label": label, "url": url, "state": state, "secs": round(time.time() - t0, 1), "plan": plan, "meta": meta,
            "tail": [t[:200] for t in tail]}


def installed_env() -> dict:
    """現在生效的發行版(sys.path 先到先算,跟 import 時看到的一樣):{canon 名: (版本, requires)}。"""
    from importlib.metadata import distributions
    env = {}
    for d in distributions():
        n = canon(d.metadata.get("Name") or "")
        if n and n not in env:
            env[n] = (d.version, list(d.requires or []))
    return env


def _req_tools():
    try:
        from packaging.requirements import Requirement
        from packaging.version import Version
    except ImportError:                                     # pip 自帶一份
        from pip._vendor.packaging.requirements import Requirement
        from pip._vendor.packaging.version import Version
    return Requirement, Version


def conflicts(env: dict) -> set:
    """跟 pip check 同一個判準:每個已裝件宣告的相依(markers 照本機算、extras 不算)缺件或版本不合。"""
    Requirement, Version = _req_tools()
    bad = set()
    for name, (ver, reqs) in env.items():
        for raw in reqs:
            try:
                r = Requirement(raw)
                if r.marker is not None and not r.marker.evaluate({"extra": ""}):
                    continue
            except Exception:                               # noqa: BLE001 — 宣告寫壞的行:照實略過,不猜
                continue
            dep = env.get(canon(r.name))
            if dep is None:
                bad.add("%s %s 缺 %s" % (name, ver, r.name))
            elif str(r.specifier) and not r.specifier.contains(dep[0], prereleases=True):
                bad.add("%s %s 要 %s%s,會是 %s" % (name, ver, r.name, r.specifier, dep[0]))
    return bad


def predict(env: dict, res: dict) -> tuple:
    """把解出的計畫疊到現況上 → (現況衝突, 裝後新增的衝突)。"""
    sim = dict(env)
    for n, v in res["plan"].items():
        sim[n] = (v, res["meta"].get(n, {}).get("requires", []))
    base = conflicts(env)
    return base, sorted(conflicts(sim) - base)


def consensus(results: list) -> dict:
    """三鏡像共同判:參考 = 官方 PyPI(有解出的話),否則最快解出的那個;其他解出的跟參考比版本。"""
    ok = [r for r in results if r["state"] == "RESOLVED"]
    reach = [r for r in results if r["state"] != "UNREACHABLE"]
    if not ok:
        return {"ref": None, "lag": [], "reached": len(reach), "resolved": 0}
    ref = next((r for r in ok if r["label"] == REFERENCE), None) or min(ok, key=lambda r: r["secs"])
    lag = []
    for r in ok:
        if r is ref:
            continue
        diff = sorted("%s %s≠%s" % (n, r["plan"].get(n, "—"), v) for n, v in ref["plan"].items() if r["plan"].get(n) != v)
        if diff:
            lag.append({"label": r["label"], "diff": diff[:8]})
    lag += [{"label": r["label"], "diff": ["解不出(參考鏡像解得出)"]} for r in reach if r["state"] == "FAIL"]
    return {"ref": ref, "lag": lag, "reached": len(reach), "resolved": len(ok)}


LATE_MIN, LATE_X = 90, 4                                  # 第一個鏡像答完後,其他鏡像最多再等 max(90 秒, 4 倍)


def _all_mirrors(pkgs: list, ms: list, run) -> list:
    t0, first = time.time(), {}

    def late() -> bool:
        return "secs" in first and time.time() - t0 > max(LATE_MIN, LATE_X * first["secs"])

    def one(m):
        r = resolve(pkgs, m[0], m[1], run=run, late=late)
        if r["state"] == "RESOLVED":
            first.setdefault("secs", r["secs"])
        return r
    with ThreadPoolExecutor(max_workers=len(ms)) as ex:
        return list(ex.map(one, ms))


def plan_check(pkgs: list, run=None, env: dict | None = None, say=print) -> dict:
    ms = mirrors()
    rep = {"schema": "VIA.InstallPlanCheck.v1", "engine": TAG, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "machine": PRIOR.machine_hash(), "python": platform.python_version(), "request": list(pkgs), "mirrors": [],
           "blocked": [], "plan": [], "requested_pins": [], "ref": None, "lag": [], "sdist": [], "base_conflicts": 0,
           "new_conflicts": [], "special": [], "lamp": "GRAY", "why": []}
    pkgs, rep["special"] = route(pkgs)
    sp_note = ("%d 件屬特殊環境 / 分類 → 單獨安裝(不進 base):%s" % (len(rep["special"]), " · ".join("%s→%s" % (x["pkg"], x["env"]) for x in rep["special"][:6]))
               if rep["special"] else "")
    if not pkgs and rep["special"]:
        rep.update(lamp="YELLOW", why=[sp_note])
        return rep
    if not pkgs:
        rep.update(lamp="GREEN", why=["計畫是空的:沒有要裝的"])
        return rep
    if not _consent():
        rep["mirrors"] = [{"label": l, "url": u, "state": "NOT_RUN", "secs": 0} for l, u in ms]
        rep["why"] = ["網路同意閘沒開(VIA_NET_CONSENT)→ 三鏡像都沒解(零網路 · 零安裝);經 VCGC 中樞 via-install 跑"]
        return rep
    say("[plan-check] 三鏡像同時解析 %d 件:%s" % (len(pkgs), " ".join(pkgs)))
    res = _all_mirrors(pkgs, ms, run)
    want = list(pkgs)
    if not any(r["state"] == "RESOLVED" for r in res) and any(r["state"] == "FAIL" for r in res):
        lab, url = next((m for m in ms if m[0] == REFERENCE), None) or next((r["label"], r["url"]) for r in res if r["state"] == "FAIL")
        say("[plan-check] 整份解不出 → 逐件在 %s 再解,找出是哪一件" % lab)
        with ThreadPoolExecutor(max_workers=min(4, len(pkgs))) as ex:
            one = list(ex.map(lambda p: (p, resolve([p], lab, url, run=run)), pkgs))
        rep["blocked"] = [{"pkg": p, "state": r["state"], "tail": r["tail"]} for p, r in one if r["state"] != "RESOLVED"]
        want = [p for p, r in one if r["state"] == "RESOLVED"]
        if want and rep["blocked"]:
            say("[plan-check] 剔除 %s · 其餘 %d 件三鏡像再解" % (" ".join(b["pkg"] for b in rep["blocked"]), len(want)))
            res = _all_mirrors(want, ms, run)
    rep["mirrors"] = [{k: r[k] for k in ("label", "url", "state", "secs", "tail")} | {"count": len(r["plan"])} for r in res]
    c = consensus(res)
    rep["lag"] = c["lag"]
    if c["ref"] is None:
        rep["lamp"] = "RED" if c["reached"] else "GRAY"
        rep["why"].append("三鏡像都沒解出(%s)" % ("套件解不出" if c["reached"] else "都連不到 · NOT_RUN"))
        return rep
    ref = c["ref"]
    rep["ref"] = {"label": ref["label"], "url": ref["url"]}
    base, new = predict(installed_env() if env is None else env, ref)
    rep["base_conflicts"], rep["new_conflicts"] = len(base), new
    rep["plan"] = ["%s==%s" % (n, v) for n, v in sorted(ref["plan"].items())]
    rep["requested_pins"] = ["%s==%s" % (n, v) for n, v in sorted(ref["plan"].items()) if ref["meta"][n]["requested"]]
    rep["sdist"] = sorted(n for n, m in ref["meta"].items() if m["sdist"])
    if new:
        rep["lamp"] = "RED"
        rep["why"].append("裝下去會新增 %d 條相依衝突 → 不裝" % len(new))
    elif not rep["plan"]:
        rep["lamp"] = "RED" if rep["blocked"] else "GREEN"
        rep["why"].append("全部剔除,沒有能裝的" if rep["blocked"] else "要的都已經裝好(解析結果不用動)")
    else:
        notes = [sp_note] if sp_note else []
        if rep["blocked"]:
            notes.append("剔除 %d 件(解不出)" % len(rep["blocked"]))
        if c["lag"]:
            notes.append("鏡像不同步 %d 個(照 %s 的版本)" % (len(c["lag"]), ref["label"]))
        if c["resolved"] + len([x for x in c["lag"] if x["diff"] == ["解不出(參考鏡像解得出)"]]) < len(ms):
            notes.append("只有 %d/%d 個鏡像回應" % (c["reached"], len(ms)))
        if rep["sdist"]:
            notes.append("%d 件要從原始碼建置:%s" % (len(rep["sdist"]), " ".join(rep["sdist"][:6])))
        rep["lamp"] = "YELLOW" if notes else "GREEN"
        rep["why"] += notes or ["三鏡像一致 · 裝後零新增衝突"]
    return rep


def write_plan(rep: dict) -> Path:
    od = out_dir()
    od.mkdir(parents=True, exist_ok=True)
    p = od / "PLANCHECK_latest.json"
    tmp = od / ("PLANCHECK_%d.tmp" % os.getpid())
    tmp.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)
    return p


def print_plan(rep: dict, say=print) -> None:
    say("[plan-check] %s · %s" % (rep["lamp"], " · ".join(rep["why"])))
    for m in rep["mirrors"]:
        say("   鏡像 %-14s %-11s %5.1fs · 解出 %s 件%s" % (m["label"], m["state"], m.get("secs", 0), m.get("count", 0),
                                                    ("" if m["state"] in ("RESOLVED", "NOT_RUN") or not m.get("tail") else " · " + m["tail"][-1][:90])))
    for b in rep["blocked"]:
        say("   剔除 %s(%s)%s" % (b["pkg"], b["state"], (" · " + b["tail"][-1][:110]) if b["tail"] else ""))
    for x in rep["lag"]:
        say("   不同步 %s:%s" % (x["label"], " · ".join(x["diff"][:4])))
    for x in rep["new_conflicts"][:8]:
        say("   ✗ 裝後新增衝突:%s" % x)
    for x in rep.get("special") or []:
        say("   單獨環境 %s → %s(%s)" % (x["pkg"], x["env"], x["family"]))
    if rep["plan"]:
        say("   計畫(釘版 %d 件 · 要求的 %d 件):%s" % (len(rep["plan"]), len(rep["requested_pins"]), " ".join(rep["requested_pins"])))
    say("NEXT: %s" % ("via-install --from-plan(照這份計畫一次裝 · 不再測)" if rep["lamp"] in ("GREEN", "YELLOW") and rep["plan"]
                       else "先處理上面的紅 / 灰再重跑 --plan-check(零安裝)" if rep["lamp"] in ("RED", "GRAY") else "base 沒有要裝的"))
    if rep.get("special"):
        say("NEXT(特殊環境):via-envgov plan → via-envgov apply --approve(逐境單獨裝 · 該境先過八路檢查)")


def load_plan(now: float | None = None) -> tuple:
    p = out_dir() / "PLANCHECK_latest.json"
    try:
        rep = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, "沒有 PLANCHECK_latest.json → 先跑 --plan-check"
    age = (now or time.time()) - datetime.fromisoformat(rep["ts"]).timestamp()
    if rep.get("machine") != PRIOR.machine_hash():
        return None, "計畫是別台機器做的 → 本機重跑 --plan-check"
    if age > PLAN_MAX_AGE:
        return None, "計畫已過 %d 小時 → 重跑 --plan-check" % (age // 3600)
    if rep.get("lamp") not in ("GREEN", "YELLOW") or rep.get("new_conflicts"):
        return None, "計畫燈 %s(%s)→ 不裝" % (rep.get("lamp"), " · ".join(rep.get("why") or []))
    if not rep.get("plan"):
        return None, "計畫是空的:沒有要裝的"
    return rep, ""


def install_argv(rep: dict) -> list:
    return ["--no-deps", "--index-url", rep["ref"]["url"], *rep["plan"]]


def from_plan(installer=None, say=print) -> int:
    rep, why = load_plan()
    if rep is None:
        say("[from-plan] 拒絕(零安裝):%s" % why)
        return 0 if why.startswith("計畫是空的") else 3
    if not _consent():
        say("[from-plan] 網路同意閘沒開 → 零安裝(經 VCGC 中樞 via-install 跑)")
        return 3
    if installer is None:
        import VIA_SuperAccel_Module as _accel           # 照 v0104:經輔助模組裝(同意閘 + 重試退避)
        installer = _accel.pip_install
    say("[from-plan] 計畫已在 --plan-check 檢測無誤 → 直接執行,不再測 · 一次裝 %d 件(釘版 · --no-deps · 索引 %s)" % (len(rep["plan"]), rep["ref"]["label"]))
    t0 = time.time()
    rc, tail = installer(install_argv(rep))
    say("[from-plan] 安裝 rc %s · %.1fs · %s" % (rc, time.time() - t0, (tail or "").splitlines()[-1][:120] if tail else ""))
    got = {pin.split("==")[0]: pin.split("==")[1] for pin in rep["requested_pins"]}
    reg = {"schema": "VIA.LibRegistry.v1", "ledger": []}
    try:
        reg = json.loads(PRIOR.LIBREG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    reg["ledger"].append({"ts": datetime.now().strftime("%Y%m%d_%H%M%S"), "machine": PRIOR.machine_hash(), "mode": "install_from_plan",
                          "packages": got, "plan": rep["plan"], "index": rep["ref"]["label"], "rc": rc,
                          "plan_ts": rep["ts"], "plan_lamp": rep["lamp"], "provenance": TAG})
    PRIOR.LIBREG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0 if rc == 0 else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if "--plan-check" in a:
        pkgs = [x for x in a if not x.startswith("--")]
        print("=== %s · 先查衝突(三鏡像 · 零安裝)===" % TAG)
        rep = plan_check(pkgs)
        print_plan(rep)
        print("[plan-check] 寫 %s" % write_plan(rep))
        return {"GREEN": 0, "YELLOW": 0, "GRAY": 2}.get(rep["lamp"], 1)
    if "--from-plan" in a:
        print("=== %s · 依計畫一次裝 ===" % TAG)
        return from_plan()
    keep = sys.argv
    sys.argv = [keep[0] if keep else str(HERE)] + a
    try:
        return PRIOR.main()
    finally:
        sys.argv = keep


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 11 項 · 前版 %s · 零網路 · 零安裝)" % (TAG, PRIOR_PATH.name), flush=True)
    ms = mirrors()
    chk("T1 鏈:前版 v0104 · 三鏡像取自 Baseline mirror_chain(清華 · 阿里 · 官方)",
        PRIOR_PATH.name == "CGC_MDL056_InstallGate_v0104.py" and [m[0] for m in ms] == ["tsinghua", "aliyun", "pypi-official"], ms)
    av = resolve_argv(["rich"], "https://x/simple", Path("r.json"))
    chk("T2 解析命令只做 --dry-run --report(零安裝)· 指定鏡像索引", "--dry-run" in av and "--report" in av and av[av.index("--index-url") + 1] == "https://x/simple"
        and "install" in av and av[-1] == "rich", av)

    def fake_run(versions: dict, fail_pkgs=(), unreach=()):
        def run(argv, **kw):
            url, pkgs, rep = argv[argv.index("--index-url") + 1], [x for x in argv[argv.index("--retries") + 2:] if not x.startswith("--")], Path(argv[argv.index("--report") + 1])
            label = next(l for l, u in ms if u == url)
            R = type("R", (), {})
            r = R()
            if label in unreach:
                r.returncode, r.stdout, r.stderr = 1, "", "ConnectionError: Max retries exceeded"
                return r
            if any(p in fail_pkgs for p in pkgs):
                r.returncode, r.stdout, r.stderr = 1, "", "ERROR: ResolutionImpossible: for help visit ..."
                return r
            v = versions.get(label, versions["*"])
            items = [{"metadata": {"name": p, "version": v.get(p, "1.0"), "requires_dist": ["dep>=2"] if p == "app" else []},
                      "download_info": {"url": "https://h/%s.%s" % (p, "tar.gz" if p == "srcpkg" else "whl")}, "requested": True} for p in pkgs]
            if "app" in pkgs:
                items.append({"metadata": {"name": "dep", "version": v.get("dep", "2.0"), "requires_dist": []},
                              "download_info": {"url": "https://h/dep.whl"}, "requested": False})
            rep.write_text(json.dumps({"install": items}), encoding="utf-8")
            r.returncode, r.stdout, r.stderr = 0, "", ""
            return r
        return run

    env0 = {"dep": ("1.0", []), "old": ("1.0", ["dep<2"])}
    try:
        _TEST["consent"] = False
        calls = []
        r0 = plan_check(["app"], run=lambda *a, **k: calls.append(a), env=env0, say=lambda *_: None)
        chk("T3 同意閘沒開:灰 NOT_RUN · 一個 pip 都沒起(零網路)", r0["lamp"] == "GRAY" and not calls and all(m["state"] == "NOT_RUN" for m in r0["mirrors"]), r0)
        _TEST["consent"] = True
        r1 = plan_check(["app"], run=fake_run({"*": {}}), env=env0, say=lambda *_: None)
        chk("T4 疊到現況上推算:app 拉 dep 2.0 → 已裝的 old 要 dep<2 → 紅(不裝)· 列出那條衝突",
            r1["lamp"] == "RED" and any("old" in x and "dep" in x for x in r1["new_conflicts"]) and r1["plan"] == ["app==1.0", "dep==2.0"], r1)
        r2 = plan_check(["app", "rich"], run=fake_run({"*": {}}), env={"dep": ("1.0", [])}, say=lambda *_: None)
        chk("T5 三鏡像一致 · 零新增衝突 → 綠 · 計畫全部釘版 · 要求的件另列",
            r2["lamp"] == "GREEN" and r2["plan"] == ["app==1.0", "dep==2.0", "rich==1.0"] and r2["requested_pins"] == ["app==1.0", "rich==1.0"]
            and r2["ref"]["label"] == "pypi-official", r2)
        r3 = plan_check(["rich", "bad", "srcpkg"], run=fake_run({"*": {}, "aliyun": {"rich": "0.9"}}, fail_pkgs=("bad",), unreach=("tsinghua",)),
                        env={}, say=lambda *_: None)
        chk("T6 一件解不出:逐件找出 bad 剔除 · 其餘再解 · 阿里版本不同步照官方 · 清華連不到 · srcpkg 要建置 → 黃(仍可裝)",
            r3["lamp"] == "YELLOW" and [b["pkg"] for b in r3["blocked"]] == ["bad"] and r3["plan"] == ["rich==1.0", "srcpkg==1.0"]
            and r3["lag"] and r3["lag"][0]["label"] == "aliyun" and r3["sdist"] == ["srcpkg"]
            and next(m for m in r3["mirrors"] if m["label"] == "tsinghua")["state"] == "UNREACHABLE", r3)
        r4 = plan_check(["x"], run=fake_run({"*": {}}, unreach=("tsinghua", "aliyun", "pypi-official")), env={}, say=lambda *_: None)
        chk("T7 三個都連不到 → 灰(不是綠,也不裝)", r4["lamp"] == "GRAY" and not r4["plan"], r4)
        with tempfile.TemporaryDirectory(prefix="gate105_") as td:
            keep_root = os.environ.get("VIA_ROOT")
            os.environ["VIA_ROOT"] = td
            try:
                got = []
                write_plan(r1)
                rc_red = from_plan(installer=lambda a: got.append(a) or (0, ""), say=lambda *_: None)
                write_plan(dict(r2, ts="2000-01-01T00:00:00+00:00"))
                rc_old = from_plan(installer=lambda a: got.append(a) or (0, ""), say=lambda *_: None)
                write_plan(r2)
                keep_lr, keep_pc = PRIOR.LIBREG, PRIOR.pip_check
                tested = []
                PRIOR.LIBREG, PRIOR.pip_check = Path(td) / "libreg.json", (lambda: tested.append(1) or [])
                try:
                    rc_ok = from_plan(installer=lambda a: got.append(a) or (0, "ok"), say=lambda *_: None)
                finally:
                    PRIOR.LIBREG, PRIOR.pip_check = keep_lr, keep_pc
                led = json.loads((Path(td) / "libreg.json").read_text(encoding="utf-8"))["ledger"][-1]
            finally:
                os.environ.pop("VIA_ROOT", None) if keep_root is None else os.environ.__setitem__("VIA_ROOT", keep_root)
        chk("T8 --from-plan:紅計畫 / 過期計畫拒絕(零安裝)· 綠計畫直接一次裝整份釘版(--no-deps · 參考鏡像 · 不再測)· 只增記帳",
            rc_red == 3 and rc_old == 3 and rc_ok == 0 and len(got) == 1
            and got[0] == ["--no-deps", "--index-url", "https://pypi.org/simple", "app==1.0", "dep==2.0", "rich==1.0"]
            and led["mode"] == "install_from_plan" and not tested, (rc_red, rc_old, rc_ok, got, tested))
    finally:
        _TEST.clear()
    src = HERE.read_text(encoding="utf-8")
    chk("T9 檔面:加速器橋 · 零 TA-Lib · 本檔不設同意閘 · 不 import 他系統",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src) and "__setitem__(\"VIA_NET" not in src
        and not re.search(r"^\s*(import|from)\s+(VDF_|VRN_|VQG_|VAP_)", src, re.M))
    b_, sp_ = route(["rich", "paddleocr", "spacy==3.8.0", "catboost", "numpy"])
    _TEST["consent"] = True
    try:
        r5 = plan_check(["paddleocr", "spacy"], run=lambda *a, **k: (_ for _ in ()).throw(AssertionError("不該解析")), env={}, say=lambda *_: None)
    finally:
        _TEST.clear()
    chk("T11 特殊環境單獨安裝:paddleocr→via_paddle_311 · spacy→via_nlp · catboost→via_catboost 不進 base;rich · numpy 留 base;"
        "全是特殊件 → 黃 · base 計畫空 · 一個 pip 都不起",
        b_ == ["rich", "numpy"] and [(x["pkg"], x["env"]) for x in sp_] == [("paddleocr", "via_paddle_311"), ("spacy==3.8.0", "via_nlp"), ("catboost", "via_catboost")]
        and r5["lamp"] == "YELLOW" and not r5["plan"] and len(r5["special"]) == 2, (b_, sp_, r5))
    t0 = time.time()
    try:
        _run_bounded([sys.executable, "-c", "import time; time.sleep(30)"], 60, late=lambda: time.time() - t0 > 1.0)
        cut = False
    except subprocess.TimeoutExpired:
        cut = time.time() - t0 < 10
    chk("T10 慢鏡像不拖整輪:別的鏡像答完後超過等待上限就砍掉子行程(不等滿 300 秒)", cut)
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
