#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VDF_ENG083_TALibOneBridge v0100 — TA-Lib OneEngine 正主橋(批519;操作員上傳 VIA_TALib_OneEngine_v0100.zip)
====================================================================
收容件:functional modules/TALib/references/intake/VIA_TALib_OneEngine_v0100_b519/VIA_TALib_OneEngine_v0100/(原名零觸碰;_INTAKE_MANIFEST_b519.json md5 冊)
  VIA TA-Lib OneEngine v1.0.0 = 退役件 VIA_ENG003_TALibEngine v0100 的整合升級版:TA-Lib Abstract API 動態發現全函數 · 資料源 Parquet/CSV/DuckDB 唯讀
  · VDF 價格湖欄位(ticker|obs_date|open|high|low|close|adj|volume)直讀 · ADJUSTED_PRICE_ONLY · 量能 raw/ex-daytrade 雙套 · VAP Catalog。
本橋(L30 一功能一正主;Zero-Hydra 零重寫):
  probe            家族境(vdf)python 探 talib 可匯入?版本?(ABSENT 誠實;不代裝;印 pip 令=你的手;requirements 釘 numpy<2/pandas<2.2/TA-Lib<0.5)
  selftest-engine  以家族境跑收容件 self-test(360 筆合成 OHLCV 真跑 TA-Lib)→ JSON 判讀(TA-Lib 缺=ABSENT,不是 FAIL)
  catalog          收容件 catalog(已裝 TA-Lib 的全函數與可改參數)→ VIA_Reports/talib_one/TALib_All_Parameters.json
  run [--db P::T|--source F] [--functions A,B] [--formats parquet,csv]
                   庫解析律(LL27/LL30):--db 明給 > VIA_DB_VDF_TW_MARKET > VIA_DATA_HOME 家內 rglob vdf_tw_market.duckdb > 舊主路徑;表預設 tw_prices_adj(在)否則 tw_daily_prices
                   輸出 VIA_Reports/talib_one/RUN_<ts>/(不入倉);來源唯讀(引擎自述)
  --selftest       六檢(零網路;不需 TA-Lib:argv 建構/庫解析/判讀器/收容件在位/md5 冊/律)
律:只增不減;正本零觸碰;誠實三態(ABSENT=未裝不是壞);零網路(引擎不下載資料);安裝=操作員之手;子行程環境=匯流排 child_env()(L32)。
用法:python3 VDF_ENG083_TALibOneBridge_v0100.py probe|selftest-engine|catalog|run [...] [--json] | --selftest
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
INTAKE_ROOT = VIA / "functional modules" / "TALib" / "references" / "intake"
INTAKE_GLOB = "VIA_TALib_OneEngine_v*_b*"
ENGINE_NAME = "VIA_TALib_OneEngine.py"
OUT = VIA / "VIA_Reports" / "talib_one"
MEGA = VIA / "functional modules" / "VDF" / "output_hub" / "mega"
PINS = "numpy>=1.26,<2.0 pandas>=2.1,<2.2 TA-Lib>=0.4.28,<0.5"   # 收容件 requirements.txt 釘(NumPy<2 ↔ ta-lib<0.5)


def _newest(root: Path, pat: str) -> Path | None:
    hits = sorted(root.glob(pat)) if root.exists() else []
    return hits[-1] if hits else None


def intake_home() -> Path | None:
    pkg = _newest(INTAKE_ROOT, INTAKE_GLOB)
    if not pkg:
        return None
    inner = _newest(pkg, "VIA_TALib_OneEngine_v*")
    return inner if inner and (inner / ENGINE_NAME).exists() else (pkg if (pkg / ENGINE_NAME).exists() else None)


def _bus():
    """匯流排(尾版)= 家族境 python 與子行程環境的唯一來源(L30/L32);缺=None(退 base)。"""
    p = _newest(VIA / "supportive modules" / "registry", "CGC_MDL148_EngineBus_v*.py")
    if not p:
        return None
    try:
        spec = importlib.util.spec_from_file_location("via_bus_for_eng083", p)
        m = importlib.util.module_from_spec(spec)
        sys.modules["via_bus_for_eng083"] = m
        spec.loader.exec_module(m)
        return m
    except Exception:
        return None


def family_python(family: str = "vdf") -> tuple[str, str]:
    env = os.environ.get("VIA_PY_VDF")
    if env and Path(env).exists():
        return env, "VIA_PY_VDF"
    b = _bus()
    if b is not None:
        try:
            r = b.python_for(family)
            return r.get("python") or sys.executable, r.get("state") or r.get("source") or "bus"
        except Exception:
            pass
    return sys.executable, "base 退路"


def child_env(family: str = "vdf") -> dict:
    b = _bus()
    if b is not None:
        try:
            return b.child_env(family)
        except Exception:
            pass
    e = dict(os.environ)
    e.pop("PYTHONHOME", None)
    e["VIA_PYTHONHOME_SCRUBBED"] = "1"
    return e


def resolve_db(explicit: str | None = None) -> tuple[Path | None, str, str]:
    """回 (庫路徑, 表, 解法);表:tw_prices_adj 在則用,否則 tw_daily_prices(引擎會自認欄位)。"""
    if explicit:
        if "::" in explicit:
            p, t = explicit.rsplit("::", 1)
            return Path(p), t, "--db 明給"
        return Path(explicit), "", "--db 明給(表由引擎 --table 預設)"
    e = os.environ.get("VIA_DB_VDF_TW_MARKET")
    if e and Path(e).exists():
        return Path(e), "", "VIA_DB_VDF_TW_MARKET"
    home = os.environ.get("VIA_DATA_HOME")
    if home and Path(home).exists():
        hits = sorted(Path(home).rglob("vdf_tw_market.duckdb"))
        if hits:
            return hits[0], "", "VIA_DATA_HOME 家內 rglob"
    p = MEGA / "vdf_tw_market.duckdb"
    if p.exists():
        return p, "", "舊主路徑 output_hub/mega"
    return None, "", "ABSENT(庫不在;先 via-vdfdb / via-price)"


def pick_table(db: Path, prefer: str = "") -> str:
    if prefer:
        return prefer
    try:
        import duckdb  # type: ignore
        con = duckdb.connect(str(db), read_only=True)
        try:
            names = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        finally:
            con.close()
        for t in ("tw_prices_adj", "tw_daily_prices"):
            if t in names:
                return t
    except Exception:
        pass
    return "tw_daily_prices"


def build_argv(verb: str, py: str, home: Path, db: Path | None = None, table: str = "", source: str = "", functions: str = "", formats: str = "", out_dir: Path | None = None) -> list:
    eng = str(home / ENGINE_NAME)
    cfg = home / "VIA_TALib_OneEngine.config.json"
    a = [py, eng]
    if verb == "probe":
        return [py, "-c", "import talib,numpy;print('talib',getattr(talib,'__version__','?'),'numpy',numpy.__version__)"]
    if verb == "selftest-engine":
        a += ["self-test"]
    elif verb == "catalog":
        a += ["catalog", "--output", str((out_dir or OUT) / "TALib_All_Parameters.json")]
    elif verb == "run":
        a += ["run", "--output-dir", str(out_dir or OUT / f"RUN_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}")]
        if source:
            a += ["--source", source]
        elif db is not None:
            a += ["--database", str(db), "--database-type", "duckdb", "--table", table or "tw_daily_prices"]
        if functions:
            a += ["--functions", functions]
        if formats:
            a += ["--formats", formats]
    else:
        raise ValueError(verb)
    if cfg.exists() and verb != "probe":
        a += ["--config", str(cfg)]
    return a


def judge(verb: str, rc: int | None, out: str, err: str) -> tuple[str, str]:
    """收容件輸出 → (state, why):TA-Lib 缺=ABSENT(不是壞);PASS/GREEN=OK;其餘 FAIL 帶因由。"""
    text = (out or "") + "\n" + (err or "")
    if "找不到 TA-Lib" in text or "No module named 'talib'" in text or "ModuleNotFoundError: No module named 'talib'" in text:
        return "ABSENT", "本境無 TA-Lib(不是壞):裝=你的手 → <vdf python> -m pip install " + PINS
    if rc is None:
        return "TIMEOUT", "逾時"
    if verb == "probe":
        return ("OK", out.strip()[:80]) if rc == 0 else ("ABSENT", (err or out).strip().splitlines()[-1][:120] if (err or out).strip() else "rc≠0")
    try:
        j = json.loads(out.strip().splitlines()[-1]) if out.strip().startswith("{") is False and out.strip() else json.loads(out)
    except Exception:
        try:
            j = json.loads(out)
        except Exception:
            j = {}
    st = str(j.get("status") or "")
    if rc == 0 and st in ("PASS", "GREEN", ""):
        return "OK", f"status={st or 'rc0'}" + (f" · coverage={j.get('function_coverage')}" if j.get("function_coverage") is not None else "") + (f" · rows={j.get('rows')}" if j.get("rows") is not None else "")
    return "FAIL", (j.get("message") or j.get("error_type") or (err.strip().splitlines()[-1] if err.strip() else f"rc={rc}"))[:160]


def run_verb(verb: str, args: list, do_print: bool = True) -> dict:
    home = intake_home()
    rep = {"schema": "VIA.TALibOneBridge.v1", "verb": verb, "ts": _dt.datetime.now().isoformat(timespec="seconds"), "home": str(home) if home else None, "state": "ABSENT", "why": "", "argv": [], "secs": 0.0, "tail": []}
    if home is None:
        rep["why"] = f"收容件不在:{INTAKE_ROOT / INTAKE_GLOB}(拉最新樹)"
        _emit(rep, do_print)
        return rep
    py, src = family_python("vdf")
    rep["python"] = py
    rep["python_source"] = src
    db, table, how = (None, "", "")
    if verb == "run":
        source = _arg(args, "--source", "")
        if not source:
            db, table, how = resolve_db(_arg(args, "--db", None))
            if db is None:
                rep["why"] = f"庫解析:{how}"
                _emit(rep, do_print)
                return rep
            table = pick_table(db, table)
        rep["db"] = {"path": str(db) if db else None, "table": table, "how": how, "source": source}
        argv = build_argv("run", py, home, db=db, table=table, source=source, functions=_arg(args, "--functions", ""), formats=_arg(args, "--formats", "parquet,csv"))
    else:
        argv = build_argv(verb, py, home)
    rep["argv"] = argv
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = _dt.datetime.now()
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=int(_arg(args, "--timeout", "1800") or 1800), env=child_env("vdf"), cwd=str(OUT))
        rc, out, err = r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        rc, out, err = None, "", "timeout"
    except Exception as exc:
        rc, out, err = 1, "", f"{type(exc).__name__}: {exc}"
    rep["secs"] = round((_dt.datetime.now() - t0).total_seconds(), 1)
    rep["rc"] = rc
    rep["state"], rep["why"] = judge(verb, rc, out, err)
    rep["tail"] = [l for l in (out + "\n" + err).splitlines() if l.strip()][-6:]
    (OUT / f"{verb.upper().replace('-', '_')}_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    _emit(rep, do_print)
    return rep


def _emit(rep: dict, do_print: bool) -> None:
    if not do_print:
        return
    print(f"=== [via-taone {rep['verb']}] TA-Lib OneEngine 正主橋 · {rep['state']} · {rep['why'][:160]} · {rep['secs']}s ===")
    if rep.get("db"):
        print(f"  [庫解析] {rep['db']}")
    if rep.get("argv"):
        print("  argv: " + " ".join(Path(x).name if ("/" in x or "\\" in x) and len(x) > 24 else x for x in rep["argv"]))
    for l in rep.get("tail") or []:
        print("  | " + l[:200])
    if rep["state"] == "ABSENT" and "TA-Lib" in rep["why"]:
        print(f"  裝(你的手):& \"{rep.get('python', 'python')}\" -m pip install {PINS}   # numpy 2.x 境需先降;裝完 via-taone selftest-engine")


def _arg(a: list, flag: str, default=None):
    if flag in a:
        i = a.index(flag)
        if i + 1 < len(a):
            return a[i + 1]
    return default


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    home = intake_home()
    chk("① 收容件在位(尾版 glob;原名零觸碰)", home is not None and (home / ENGINE_NAME).exists() and (home / "VIA_TALib_OneEngine.config.json").exists(), f"({home.name if home else 'ABSENT'})")
    man = _newest(INTAKE_ROOT, INTAKE_GLOB)
    mf = (man / "_INTAKE_MANIFEST_b519.json") if man else None
    ok_md5 = False
    if mf and mf.exists():
        j = json.loads(mf.read_text(encoding="utf-8"))
        ok_md5 = all(hashlib.md5((man / f["rel"]).read_bytes()).hexdigest() == f["md5"] for f in j.get("files", []) if (man / f["rel"]).exists()) and len(j.get("files", [])) >= 10
    chk("② md5 冊對得上(收容件零漂移)", ok_md5)
    a = build_argv("run", "py", Path("/x"), db=Path("/d/vdf_tw_market.duckdb"), table="tw_prices_adj", functions="SMA,RSI", formats="csv", out_dir=Path("/o"))
    chk("③ run argv:--database/--database-type duckdb/--table/--functions/--formats/--output-dir 齊;唯讀來源", a[2] == "run" and "--database" in a and a[a.index("--table") + 1] == "tw_prices_adj" and "--functions" in a and "--formats" in a and "--output-dir" in a)
    p = build_argv("probe", "py", Path("/x"))
    chk("④ probe=家族境 -c 匯入 talib/numpy(不裝);selftest-engine=self-test;catalog=--output", p[1] == "-c" and "import talib" in p[2] and build_argv("selftest-engine", "py", Path("/x"))[2] == "self-test" and "--output" in build_argv("catalog", "py", Path("/x")))
    s1 = judge("selftest-engine", 1, "", '{"status": "FAIL", "message": "找不到 TA-Lib。VIA 採 TA-Lib-only"}')
    s2 = judge("selftest-engine", 0, '{"status": "PASS", "rows": 360, "function_coverage": 158}', "")
    s3 = judge("run", 2, '{"status": "YELLOW"}', "")
    s4 = judge("probe", None, "", "")
    chk("⑤ 判讀器:TA-Lib 缺=ABSENT(不是壞)· PASS=OK 帶 coverage/rows · 非 GREEN=FAIL 帶因由 · 逾時=TIMEOUT", s1[0] == "ABSENT" and "pip install" in s1[1] and s2[0] == "OK" and "coverage=158" in s2[1] and s3[0] == "FAIL" and s4[0] == "TIMEOUT")
    _sv = {k: os.environ.get(k) for k in ("VIA_DB_VDF_TW_MARKET", "VIA_DATA_HOME")}
    try:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            os.environ.pop("VIA_DB_VDF_TW_MARKET", None)
            os.environ["VIA_DATA_HOME"] = td
            (Path(td) / "x" / "y").mkdir(parents=True)
            (Path(td) / "x" / "y" / "vdf_tw_market.duckdb").write_bytes(b"")
            d1 = resolve_db(None)
            d2 = resolve_db("/q/a.duckdb::tw_prices_adj")
    finally:
        for k, v in _sv.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    chk("⑥ 庫解析律(LL27/LL30):--db 明給 > VIA_DB_VDF_TW_MARKET > VIA_DATA_HOME rglob > 舊主路徑;::表 拆得開", d1[2] == "VIA_DATA_HOME 家內 rglob" and d1[0].name == "vdf_tw_market.duckdb" and d2[1] == "tw_prices_adj" and d2[2] == "--db 明給")
    src = Path(__file__).read_text(encoding="utf-8").split("def selftest")[0]     # 只看自測段之前(自指字串不算;LL 批516 ⑧ 同病)
    chk("⑦ 律:零網路(無 requests/httpx/urllib)· 不代裝(無 pip install 子行程)· 子行程環境走匯流排 child_env", all(("import " + k) not in src for k in ("requests", "httpx", "urllib")) and "pip install" in src and '"pip", "install"' not in src and "child_env(" in src)
    print(f"  [計] 七檢 OK {7 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== TA-Lib OneEngine 正主橋(VDF_ENG083 v0100)· 七檢自測(零網路;不需 TA-Lib)===")
        return selftest()
    verb = a[0] if a and not a[0].startswith("-") else "probe"
    if verb not in ("probe", "selftest-engine", "catalog", "run"):
        print(__doc__)
        return 2
    rep = run_verb(verb, a[1:], do_print="--json" not in a)
    if "--json" in a:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    return 0 if rep["state"] in ("OK", "ABSENT") else 1


if __name__ == "__main__":
    sys.exit(main())
