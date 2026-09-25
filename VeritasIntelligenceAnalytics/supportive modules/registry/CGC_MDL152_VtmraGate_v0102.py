#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
  批539(操作員令「禁止使用 TA-LIB 將 TA-LIB 刪除 該境改用 QUANTGUARD」):
  TA-Lib 的引擎檔在批534 就刪了,但**接線沒拔乾淨**——名冊、站點、稽核冊、家族成員、工具階梯裡
  還指著 CGC_MDL151 / VDF_ENG083 / VAP_ENG004_TAFactory / VDF_ENG048_TAFactory 這些已不存在的檔。
  留著的後果不是「缺件誠實」,是**把人帶回退役路**:操作員今天就貼了一份含 `pip install TA-Lib` 與
  `via-taone` 的舊區塊回來。這一版把該處的接線切掉,改指 QuantGuard 正主橋(L50 唯一活動技術分析路徑)。
  退役帳記在 docs/VIA_Retired_TALib_B534.json 的 wave2(只增不減要有帳;LL54)。
CGC_MDL152_VtmraGate v0101 — VTMRA(Veritas Taiwan Monthly Revenue Analysis)家族測試閘(批516 操作員令「除錯成功後才 VTMRA … 確認測試無誤」)(批519:+第八成員 talib_one)
v0100→v0101(批519 操作員上傳 VIA_TALib_OneEngine_v0100.zip → 收容 _b519 + 正主橋 VDF_ENG083):家族 +成員 talib_one(橋 selftest-engine --json:
  家族境真跑收容件 360 筆合成 OHLCV;TA-Lib 缺=ABSENT 軟缺席同 talib,不拉 RED);七員→八員;①⑥ 檢追上。
CGC_MDL152_VtmraGate v0100 — VTMRA(Veritas Taiwan Monthly Revenue Analysis)家族測試閘(批516 操作員令「除錯成功後才 VTMRA … 確認測試無誤」)
====================================================================
VTMRA 不是第四套引擎(L30):它是台股月營收分析**家族名**,成員早在冊上——
  ENG063 MonthlyRevenue(月營收擷取;冊 tw_revenue_codes)· ENG075 MonthlyRevenueBackfill(史深回補;tw_revenue_backfill)
  ENG069 RevenueConsensusAnalysis(營收×共識四象限)· ENG076 ETFRevenueMomentum(ETF 營收動能;etf_revenue)
  TWREV v2.7(收容包 b477;via-twrev;twrevenue.cli selftest)· CrossGroupPhase v030(收容包 b481;via-revphase -SelfTest;族群輪動相位)
  TA-Lib(CGC_MDL151 閘;技術指標;ABSENT=未裝不是壞)
本件只做一件事:用家族境(vdf)python **真跑**每個成員自己的自測,收成一張矩陣(OK/FAIL/TIMEOUT/ABSENT/SKIP),落
  VIA_Reports/vtmra/VTMRA_latest.json + .html(零 CDN);判定=全 OK(ABSENT 只在 TA-Lib 允許)才 GREEN,任一 FAIL/TIMEOUT=RED。
用法:python3 CGC_MDL152_VtmraGate_v0100.py test [--json] [--timeout 600] | status | --selftest(七檢;零網路;假跑器)
律:只增不減;正本零觸碰(收容包不改;工作家 VIA_Reports/vtmra/twrev 首建時從包種入 config+data);零網路(成員自測皆零網路;TWREV selftest 不 fetch);
    零 CDN;零彈窗;同意閘不代設;尾版律(glob);Zero-Hydra(成員判斷不重寫);誠實三態;子行程環境=匯流排 child_env(L32)。
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


import datetime as _dt
import html
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Reports" / "vtmra"
VDF_ENGINE = VIA / "functional modules" / "VDF" / "engine"
INTAKE = VIA / "functional modules" / "VDF" / "references" / "intake"
TWREV_PKG_GLOB = "TWREV_v*_FULL_b*"
REVPHASE_PKG_GLOB = "VDF_TW_MonthlyRevenue_CrossGroupPhase_v*_b*"


# ===== [VIA:TAILPICK-BRIDGE:v0100] 尾版取用正典橋(批590/591;正典 SUP_MDL751_VIATailPick)=====
# 本群原本的行為:newest(dirp, pat)
# 批590 量過:CGC 族 32 份 `newest` 是 **13 個行為群**,不是同一件事(最大兩群參數順序相反、
# 兩支走 rglob、一支缺件回 pattern、一支按 mtime 排序)。所以正典把差異變成**明示選項**,
# 並逐群重放證零損失(15 種具名變體 × 6 組語料,90 組全同)。
# 這裡是**綁定**不是再定義一支 def:寫 def 的話能力庫裡這一家族還在,家族數不會掉(LL143)。
import importlib.util as _tp_ilu
from pathlib import Path as _tp_Path
_TP_MOD = None
_tp_p = _tp_Path(__file__).resolve()
while _tp_p.parent != _tp_p:
    _tp_hits = sorted((_tp_p / "supportive modules").glob("SUP_MDL751_VIATailPick_v*.py"))
    if _tp_hits:
        _tp_spec = _tp_ilu.spec_from_file_location("VIA_TAILPICK", _tp_hits[-1])
        _TP_MOD = _tp_ilu.module_from_spec(_tp_spec)
        _tp_spec.loader.exec_module(_TP_MOD)
        break
    _tp_p = _tp_p.parent
if _TP_MOD is None:      # 大聲壞掉:尾版取錯是無聲的錯(整條鏈指到舊引擎,沒人會發現)
    raise RuntimeError("[FAIL] 尾版取用正典缺席:supportive modules/SUP_MDL751_VIATailPick_v*.py")
_newest = _TP_MOD.bind(order="rp")
# ===== [VIA:TAILPICK-BRIDGE:END] =====


def _bus():
    try:
        p = _newest(HERE, "CGC_MDL148_EngineBus_v*.py")
        if p:
            spec = importlib.util.spec_from_file_location("via_bus_ro_vtmra", p)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            return m
    except Exception:
        return None
    return None


def family_python() -> str:
    """家族境 python:MDL137 RunGate python_for("vdf")(它再委派 MDL136);缺=本解譯器誠實。"""
    try:
        p = _newest(HERE, "CGC_MDL137_RunGate_v*.py")
        if p:
            spec = importlib.util.spec_from_file_location("via_rungate_ro_vtmra", p)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            r = m.python_for("vdf")
            if isinstance(r, dict) and r.get("python"):
                return r["python"]
    except Exception:
        pass
    return sys.executable


def child_env() -> dict:
    b = _bus()
    env = b.child_env("vdf") if (b is not None and hasattr(b, "child_env")) else dict(os.environ, VIA_ROOT=str(VIA), VIA_FAMILY="vdf")
    env.pop("PYTHONHOME", None)
    env.update({"PYTHONUTF8": "1", "VIA_NO_OPEN": "1", "VIA_SELFTEST": "1"})
    env.pop("VIA_NET_CONSENT", None)               # 家族測試零網路
    env.pop("VIA_SCRAPE_CONSENT", None)
    return env


def members(py: str | None = None, out: Path = OUT) -> list:
    """成員 × 自測 argv(尾版 glob;缺=ABSENT 誠實)。"""
    py = py or family_python()
    rows = []
    for key, pat, args, zh in (("eng063", "VDF_ENG063_MonthlyRevenue_v*.py", ["--selftest"], "月營收擷取"),
                               ("eng075", "VDF_ENG075_MonthlyRevenueBackfill_v*.py", ["--selftest"], "月營收史深回補"),
                               ("eng069", "VDF_ENG069_RevenueConsensusAnalysis_v*.py", ["--selftest"], "營收×共識四象限"),
                               ("eng076", "VDF_ENG076_ETFRevenueMomentum_v*.py", ["--selftest"], "ETF 營收動能")):
        p = _newest(VDF_ENGINE, pat)
        rows.append({"id": key, "zh": zh, "file": p.name if p else pat, "argv": [py, str(p), *args] if p else None, "cwd": None, "env_extra": {}, "timeout": 300})
    pkg = _newest(INTAKE, TWREV_PKG_GLOB)
    if pkg and (pkg / "twrevenue" / "cli.py").exists():
        home = out / "twrev"
        rows.append({"id": "twrev", "zh": "TWREV v2.7 月營收動能(收容包;工作家種入)", "file": pkg.name, "argv": [py, "-m", "twrevenue.cli", "selftest"], "cwd": str(home),
                     "env_extra": {"PYTHONPATH_PREPEND": str(pkg)}, "seed": {"pkg": str(pkg), "home": str(home)}, "timeout": 300})
    else:
        rows.append({"id": "twrev", "zh": "TWREV v2.7 月營收動能", "file": TWREV_PKG_GLOB, "argv": None, "cwd": None, "env_extra": {}, "timeout": 300})
    rp = _newest(INTAKE, REVPHASE_PKG_GLOB)
    eng = _newest(rp, "vdf_tw_monthly_revenue_cross_group_phase_engine_v*.py") if rp else None
    rows.append({"id": "revphase", "zh": "族群輪動相位 CrossGroupPhase(收容包)", "file": eng.name if eng else REVPHASE_PKG_GLOB,
                 "argv": [py, str(eng), "--self-test", "--output-dir", str(out / "revphase" / "out"), "--log-level", "WARNING"] if eng else None, "cwd": None, "env_extra": {}, "timeout": 300})
    # 批539:talib / talib_one 兩個成員隨 TA-Lib 退役(L50)自家族拔除——它們指的 CGC_MDL151 / VDF_ENG083 早已刪除,
    # 留著只會讓家族態永遠掛一個 ABSENT,看起來像缺件,其實是退役。技術分析走 VDF_ENG086 QuantGuard。
    return rows


def _seed_twrev(seed: dict) -> None:
    """工作家首建:config.yaml + data 從收容包種入(包零觸碰;已建不動)。"""
    pkg, home = Path(seed["pkg"]), Path(seed["home"])
    home.mkdir(parents=True, exist_ok=True)
    if not (home / "config.yaml").exists() and (pkg / "config.yaml").exists():
        shutil.copy2(pkg / "config.yaml", home / "config.yaml")
    if not (home / "data").exists() and (pkg / "data").is_dir():
        shutil.copytree(pkg / "data", home / "data")


def run_member(row: dict, timeout: int | None = None, runner=None) -> dict:
    res = {"id": row["id"], "zh": row["zh"], "file": row["file"], "state": "ABSENT", "secs": 0.0, "tail": [], "why": ""}
    if not row.get("argv"):
        res["why"] = "尾版缺(誠實;收容包/引擎不在)"
        return res
    env = child_env()
    pp = row.get("env_extra", {}).get("PYTHONPATH_PREPEND")
    if pp:
        env["PYTHONPATH"] = pp + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    if row.get("seed"):
        try:
            _seed_twrev(row["seed"])
        except Exception as exc:
            res["why"] = f"工作家種入失敗 {type(exc).__name__}"
    cwd = row.get("cwd") or str(OUT)
    try:
        Path(cwd).mkdir(parents=True, exist_ok=True)
    except Exception:
        cwd = str(VIA)
    t0 = _dt.datetime.now()
    try:
        if runner is not None:
            rc, out_s, err_s = runner(row["argv"], env, cwd)
        else:
            r = subprocess.run(row["argv"], capture_output=True, text=True, timeout=timeout or row.get("timeout", 300), stdin=subprocess.DEVNULL, env=env, cwd=cwd, encoding="utf-8", errors="replace")
            rc, out_s, err_s = r.returncode, r.stdout or "", r.stderr or ""
        lines = [l for l in (out_s + "\n" + err_s).splitlines() if l.strip()]
        res["tail"] = lines[-3:]
        if row["id"] in ("talib", "talib_one"):                # 批519:正主橋 --json 同形(state/why)
            js = None
            for l in reversed(out_s.splitlines()):
                if l.strip().startswith("{"):
                    try:
                        js = json.loads(l); break
                    except Exception:
                        continue
            if js is None:
                try:
                    js = json.loads(out_s[out_s.index("{"):]) if "{" in out_s else None
                except Exception:
                    js = None
            st = (js or {}).get("state", "FAIL" if rc != 0 else "OK")
            res["state"] = st if st in ("OK", "ABSENT", "FAIL") else ("OK" if rc == 0 else "FAIL")
            res["why"] = (js or {}).get("why", "") if res["state"] != "OK" else f"版本 {(js or {}).get('version', '?')}"
        else:
            res["state"] = "OK" if rc == 0 else "FAIL"
            if rc != 0:
                res["why"] = f"rc={rc}"
    except subprocess.TimeoutExpired:
        res["state"], res["why"] = "TIMEOUT", f"逾時 {timeout or row.get('timeout', 300)}s(不卡斷;kill)"
    except Exception as exc:
        res["state"], res["why"] = "FAIL", f"{type(exc).__name__}:{str(exc)[:100]}"
    res["secs"] = round((_dt.datetime.now() - t0).total_seconds(), 1)
    return res


def verdict(results: list) -> tuple[str, list]:
    reasons = []
    bad = [r for r in results if r["state"] in ("FAIL", "TIMEOUT")]
    absent = [r for r in results if r["state"] == "ABSENT"]
    if bad:
        reasons.append("成員自測非 OK:" + ",".join(f"{r['id']}({r['state']})" for r in bad))
    # 批539:talib / talib_one 的「軟缺席」豁免隨 L50 退役一併拔除——家族裡已經沒有那兩個成員,
    # 留著豁免等於替不存在的成員開一個後門,哪天有人用同一個 id 塞回來就會被默默放行。
    hard_absent = list(absent)
    if hard_absent:
        reasons.append("成員缺席:" + ",".join(r["id"] for r in hard_absent))
    if bad or hard_absent:
        return "RED", reasons
    return ("YELLOW" if reasons else "GREEN"), reasons


def render_html(rep: dict) -> str:
    rows = "".join(f"<tr><td>{html.escape(r['id'])}</td><td>{html.escape(r['zh'])}</td><td class='{html.escape(r['state'])}'>{html.escape(r['state'])}</td><td>{r['secs']}</td><td>{html.escape(r['file'])}</td><td>{html.escape(r.get('why') or ' | '.join(r.get('tail') or []))[:200]}</td></tr>" for r in rep["results"])
    return ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><title>VTMRA 測試閘</title><style>body{font-family:'Segoe UI',system-ui,sans-serif;margin:20px;background:#0f172a;color:#e5e7eb}"
            "table{border-collapse:collapse;width:100%;font-size:13px}th,td{border:1px solid #334155;padding:5px 8px;text-align:left}td.OK{color:#22c55e}td.FAIL,td.TIMEOUT{color:#ef4444}td.ABSENT{color:#94a3b8}h1{font-size:18px}</style></head><body>"
            f"<h1>VTMRA · Veritas Taiwan Monthly Revenue Analysis · 測試閘 {html.escape(rep['ts'])} · <b>{html.escape(rep['verdict'])}</b></h1><p>python={html.escape(rep['python'])} · {html.escape('; '.join(rep['reasons']) or '全 OK')}</p>"
            f"<table><tr><th>成員</th><th>說明</th><th>態</th><th>秒</th><th>尾版</th><th>理由/尾行</th></tr>{rows}</table></body></html>")


def test(do_print: bool = True, out: Path = OUT, timeout: int | None = None, runner=None, py: str | None = None) -> dict:
    py = py or family_python()
    rep = {"schema": "VIA.VtmraGate.v1", "ts": _dt.datetime.now().isoformat(timespec="seconds"), "python": py, "results": [], "verdict": "GREEN", "reasons": []}
    if do_print:
        print(f"=== [via-vtmra] VTMRA 家族測試閘 · 家族境 python={py} · 零網路 ===")
    for row in members(py, out):
        r = run_member(row, timeout=timeout, runner=runner)
        rep["results"].append(r)
        if do_print:
            print(f"  [{r['state']:<7}] {r['id']:<9} {r['zh']} · {r['secs']}s · {r['file']} · {r.get('why') or ' | '.join(r.get('tail') or [])}"[:220])
    rep["verdict"], rep["reasons"] = verdict(rep["results"])
    try:
        out.mkdir(parents=True, exist_ok=True)
        (out / "VTMRA_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        (out / "VTMRA_latest.html").write_text(render_html(rep), encoding="utf-8")
    except Exception as exc:
        rep["reasons"].append(f"存證失敗 {type(exc).__name__}")
    if do_print:
        print(f"[via-vtmra] 判定 {rep['verdict']} · {'; '.join(rep['reasons']) or '成員自測全 OK'} · 存證 {out / 'VTMRA_latest.json'}")
    return rep


def status(out: Path = OUT, do_print: bool = True) -> dict:
    p = out / "VTMRA_latest.json"
    if not p.exists():
        s = {"state": "ABSENT", "why": "VTMRA_latest.json 不在(via-vtmra 跑一次即有)"}
    else:
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
            s = {"state": j.get("verdict"), "ts": j.get("ts"), "members": {r["id"]: r["state"] for r in j.get("results", [])}, "reasons": j.get("reasons", [])}
        except Exception as exc:
            s = {"state": "FAIL", "why": f"讀不了 {type(exc).__name__}"}
    if do_print:
        print(f"[via-vtmra status] {s.get('state')} · {s.get('ts') or s.get('why')} · {s.get('members') or ''}")
    return s


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    rows = members(sys.executable)
    ids = [r["id"] for r in rows]
    chk("① 批539 成員冊六員(ENG063/075/069/076 · TWREV · CrossGroupPhase)尾版 glob 解析;缺=argv None 誠實"
        "(TA-Lib 兩員隨 L50 退役拔除:它們指的 CGC_MDL151 / VDF_ENG083 早已刪除)",
        ids == ["eng063", "eng075", "eng069", "eng076", "twrev", "revphase"],
        f"({ids} · 在位 {sum(1 for r in rows if r['argv'])}/6)")
    e = child_env()
    chk("② 子行程環境:家族 vdf · L32 無 PYTHONHOME · VIA_SELFTEST=1 · 零彈窗 · 撤雙同意閘(家族測試零網路)",
        e.get("VIA_FAMILY") == "vdf" and "PYTHONHOME" not in e and e.get("VIA_SELFTEST") == "1" and e.get("VIA_NO_OPEN") == "1" and "VIA_NET_CONSENT" not in e and "VIA_SCRAPE_CONSENT" not in e)

    def fake(argv, env, cwd):
        s = " ".join(map(str, argv))
        if "ENG069" in s:
            return 1, "  [FAIL] x\n", ""
        if "NEVER_TALIB_b539" in s:      # 批539:退役 id 不再有假跑器分支
            return 0, json.dumps({"state": "ABSENT"}), ""
        if "twrevenue" in s:
            return (0, "ok", "") if (Path(cwd) / "config.yaml").exists() or not Path(cwd).exists() else (0, "ok(no cfg)", "")
        return 0, "  [計] OK\n", ""
    with tempfile.TemporaryDirectory() as td:
        rep = test(do_print=False, out=Path(td), runner=fake, py=sys.executable)
        st = {r["id"]: r["state"] for r in rep["results"]}
        html_ok = (Path(td) / "VTMRA_latest.html").exists() and 'src="http' not in (Path(td) / "VTMRA_latest.html").read_text(encoding="utf-8")
        twrev_home = Path(td) / "twrev"
        seeded = (not any(r["id"] == "twrev" and r["argv"] for r in rows)) or ((twrev_home / "config.yaml").exists() or not (Path(rows[4].get("seed", {}).get("pkg", "/nonexistent")) / "config.yaml").exists())
        s2 = status(out=Path(td), do_print=False)
    chk("③ 批539 假跑器矩陣:ENG069 FAIL → RED 理由點名;JSON+HTML(零 CDN)落 --out",
        st.get("eng069") == "FAIL" and "talib" not in st and rep["verdict"] == "RED" and any("eng069" in x for x in rep["reasons"]) and html_ok, f"({st})")
    chk("④ TWREV 工作家首建從收容包種入 config.yaml/data(包零觸碰;已建不動)", seeded)
    chk("⑤ status 讀回矩陣(缺=ABSENT 誠實)", s2.get("state") == "RED" and "talib" not in (s2.get("members") or {}) and status(out=Path("/nonexistent_vtmra"), do_print=False)["state"] == "ABSENT")
    v_f, _ = verdict([{"id": "eng063", "state": "FAIL"}, {"id": "twrev", "state": "OK"}])
    v_g, _ = verdict([{"id": "eng063", "state": "OK"}, {"id": "twrev", "state": "OK"}])
    v_r, _ = verdict([{"id": "eng063", "state": "OK"}, {"id": "twrev", "state": "ABSENT"}])
    v_t, _ = verdict([{"id": "talib", "state": "ABSENT"}])   # 批539:退役 id 不再有豁免口
    chk("⑥ 批539 判定律:全 OK=GREEN;任一 FAIL/TIMEOUT 或成員缺席=RED"
        "(原本給 TA-Lib 的『軟缺席=YELLOW』豁免隨退役拔除——不留後門給不存在的成員)",
        v_g == "GREEN" and v_r == "RED" and v_f == "RED" and v_t == "RED", f"({v_g}/{v_r}/{v_f}/退役id={v_t})")
    src = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]
    chk("⑦ 紀律宣告(只增不減/正本零觸碰/零網路/零 CDN/零彈窗/不代設/尾版律/Zero-Hydra/誠實三態)", all(k in src for k in ("只增不減", "正本零觸碰", "零網路", "零 CDN", "零彈窗", "不代設", "尾版律", "Zero-Hydra", "誠實三態")))
    print(f"  [計] 七檢 OK {7 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def _arg(a: list, flag: str, default=None):
    if flag in a and a.index(flag) + 1 < len(a):
        return a[a.index(flag) + 1]
    return default


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== VTMRA 家族測試閘(CGC_MDL152 v0101)· 七檢自測(零網路;假跑器)===")
        return selftest()
    verb = a[0] if a and not a[0].startswith("-") else "test"
    if verb == "status":
        return 0 if status()["state"] in ("GREEN", "YELLOW", "ABSENT") else 1
    if verb == "test":
        tmo = int(_arg(a, "--timeout", "0") or 0) or None
        rep = test(do_print="--json" not in a, timeout=tmo)
        if "--json" in a:
            print(json.dumps(rep, ensure_ascii=False, indent=1))
        return 0 if rep["verdict"] != "RED" else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
