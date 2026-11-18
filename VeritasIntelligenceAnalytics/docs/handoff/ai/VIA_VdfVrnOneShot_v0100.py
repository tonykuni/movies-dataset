#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_VdfVrnOneShot v0100 — 一行跑完 VDF + VRN 流程 → Parquet 資料庫 → 驗證 → 視覺鎖定總覽頁(操作員桌機一鍵)。

操作員令(2026-11-13):「給我一個 PS 指令 可以快速跑完所有 VDF VRN 流程 輸出 PARQUET 資料庫 且驗證無誤 並顯示於 HTML 視覺鎖定 U/I」。
只用子程序呼叫各系統自己的入口(不 import 任何系統的程式 · L123 獨立):
  ① VDF 擷取 + 建湖   VDF_ENG239_ParquetLakeBuild 尾版 run --all --start <起>(14 族群 + 2022 起回補 + Parquet + DuckDB 目錄)
                       同意閘(VIA_NET_CONSENT · VIA_SCRAPE_CONSENT)由操作員自己開;沒開 = GATED,照實黃燈,用庫內現有資料續做。
  ② VDF 驗證          DuckDB 目錄每個 VIEW 實數列數 == LAKE_STATUS 記的列數;每表最早 / 最晚日期;有無早於起始日。
  ③ VRN 輸出矩陣      VRN_ENG049_ContentReconcile 尾版 matrix(個股 + 非個股 → JSON · HTML · CSV · Parquet)
                       --vrn-full 才先跑 VRN 管理器 launch --run(完整 PDF 管線;耗時,桌機用)。
  ④ VRN 驗證          Parquet 列數 == CSV 列數 == JSON 列數(個股 / 非個股各一)。
  ⑤ 兩系統收尾        VDF_SystemManager 尾版 closeout · VRN_SystemManager 尾版 closeout(矩陣頁 + 備份 + 收據)。
  ⑥ 總覽頁            VIA_Reports/oneshot/VDF_VRN_ONESHOT_latest.html(色票讀 VCGC 鎖站 kit;連到兩系統矩陣頁 · 自建工作台 · 各輸出);
                       桌機自動開(VIA_NO_OPEN=1 或 --no-open 不開)。
rc:0 全綠 · 2 有黃(閘沒開 / 缺套件 / 缺料)· 1 有紅(驗證對不上 / 步驟失敗)。不代設同意閘 · 不裝套件 · 不用 TA-Lib。
用法:py VIA_VdfVrnOneShot_v0100.py run [--start 2022-01-01] [--jobs 5] [--skip-fetch] [--vrn-full] [--no-open] · --selftest
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
import csv
import datetime as _dt
import html as _h
import json
import os
import re
import subprocess
import sys
import tempfile
import webbrowser
from pathlib import Path

VERSION = "v0100"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
OUT = VIA / "VIA_Reports" / "oneshot"
ORDER = ["RED", "YELLOW", "GREEN"]


def vnum(p) -> int:
    m = re.search(r"_v(\d{4})\.\w+$", str(p))
    return int(m.group(1)) if m else -1


def tail(folder: Path, pat: str):
    hits = sorted(folder.glob(pat), key=vnum)
    return hits[-1] if hits else None


def worst(lamps) -> str:
    ls = [x for x in lamps if x in ORDER]
    return min(ls, key=ORDER.index) if ls else "YELLOW"


def run_step(name: str, args: list, cwd: Path, log: Path, ok_rc=(0,), soft_rc=(2, 3, 4)) -> dict:
    print(f"\n=== {name} ===\n  {' '.join(Path(a).name if a.endswith('.py') else a for a in args[1:])}", flush=True)
    env = dict(os.environ, PYTHONUTF8="1", VIA_FROM_VCGC=os.environ.get("VIA_FROM_VCGC", "YES"))
    t0 = _dt.datetime.now()
    with log.open("w", encoding="utf-8") as fh:
        p = subprocess.Popen(args, cwd=str(cwd), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        last = ""
        for ln in p.stdout:
            fh.write(ln)
            if ln.strip():
                last = ln.strip()
                print("  │ " + ln.rstrip()[:200], flush=True)
        rc = p.wait()
    lamp = "GREEN" if rc in ok_rc else ("YELLOW" if rc in soft_rc else "RED")
    return {"step": name, "rc": rc, "lamp": lamp, "sec": round((_dt.datetime.now() - t0).total_seconds(), 1), "last": last[:200], "log": log.name}


def verify_vdf(via: Path, start: str) -> dict:
    lake = via / "VIA_Reports" / "vdf_lake"
    cat, st = lake / "VDF_catalog.duckdb", lake / "LAKE_STATUS_latest.json"
    if not cat.is_file() or not st.is_file():
        return {"lamp": "RED", "why": "湖的目錄或狀態檔不在", "tables": []}
    import duckdb
    status = {t["view"]: t for t in json.loads(st.read_text(encoding="utf-8")).get("tables", [])}
    con = duckdb.connect(str(cat), read_only=True)
    rows, bad, early = [], [], []
    try:
        for (v,) in con.execute("select table_name from information_schema.tables where table_type='VIEW' order by 1").fetchall():
            n = con.execute(f'select count(*) from "{v}"').fetchone()[0]
            s = status.get(v, {})
            ok = n == s.get("rows")
            if not ok:
                bad.append(v)
            if s.get("min_date") and str(s["min_date"]) < start and s.get("date_col"):
                early.append(v)
            rows.append({"view": v, "rows": n, "status_rows": s.get("rows"), "min_date": s.get("min_date"), "max_date": s.get("max_date"),
                         "lag_days": s.get("lag_days"), "match": ok})
    finally:
        con.close()
    lamp = "RED" if bad or early or not rows else "GREEN"
    return {"lamp": lamp, "tables": rows, "views": len(rows), "rows_total": sum(r["rows"] for r in rows), "mismatch": bad, "before_start": early,
            "why": ("列數對不上:" + ",".join(bad)) if bad else (("有早於起始日的列:" + ",".join(early)) if early else "")}


def verify_vrn(via: Path) -> dict:
    d = via / "VIA_Reports" / "vrn_reconcile_runs"
    js = sorted(d.glob("matrix_*.json"))
    if not js:
        return {"lamp": "RED", "why": "沒有 matrix_*.json(VRN 矩陣沒產出)", "parts": []}
    j = js[-1]
    data = json.loads(j.read_text(encoding="utf-8"))
    base = str(j)[:-5]
    import duckdb
    parts, bad = [], []
    for kind in ("stock", "nonstock"):
        jn = len(data.get(kind) or [])
        cp, pp = Path(f"{base}_{kind}.csv"), Path(f"{base}_{kind}.parquet")
        cn = (len(list(csv.reader(cp.open(encoding="utf-8-sig")))) - 1) if cp.is_file() else None
        pn = duckdb.connect().execute("select count(*) from read_parquet(?)", [str(pp)]).fetchone()[0] if pp.is_file() else None
        ok = jn == cn == pn
        if not ok:
            bad.append(kind)
        parts.append({"kind": kind, "json": jn, "csv": cn, "parquet": pn, "match": ok})
    return {"lamp": "RED" if bad else "GREEN", "run": j.name, "html": Path(base + ".html").name if Path(base + ".html").is_file() else None,
            "parts": parts, "why": ("列數對不上:" + ",".join(bad)) if bad else ""}


def tokens(via: Path) -> dict:
    t = {"bg": "#f2f1ec", "panel": "#ffffff", "fg": "#33403f", "muted": "#6b6860", "accent": "#1b1a17", "line": "#dbd9d3", "row": "#ebe9e3",
         "green": "#3d7a52", "yellow": "#6f5c31", "red": "#9e2b25", "g_bg": "#e6efec", "y_bg": "#f2ecdd", "r_bg": "#f3e7e6", "_source": "預設(kit 不在)"}
    m = {"--bg": "bg", "--white": "panel", "--ink": "fg", "--muted": "muted", "--title": "accent", "--line": "line", "--row": "row",
         "--green": "green", "--y-ink": "yellow", "--r-ink": "red", "--g-bg": "g_bg", "--y-bg": "y_bg", "--r-bg": "r_bg"}
    try:
        k = json.loads((via / "docs" / "handoff" / "ai" / "VIA_WorkbenchLock_kit_latest.json").read_text(encoding="utf-8"))
        for key, val in (k.get("tokens") or {}).items():
            if key in m and isinstance(val, str) and val.startswith("#"):
                t[m[key]] = val
        t["_source"] = f"VCGC 鎖站 kit(契約 {k.get('ui_contract_version', '—')})"
    except (OSError, ValueError):
        pass
    return t


def page(via: Path, out: Path, rep: dict) -> Path:
    t = tokens(via)
    col = {"GREEN": (t["green"], t["g_bg"]), "YELLOW": (t["yellow"], t["y_bg"]), "RED": (t["red"], t["r_bg"])}
    chip = lambda lamp: f"<span class='chip' style='color:{col.get(lamp, (t['muted'], t['row']))[0]};background:{col.get(lamp, (t['muted'], t['row']))[1]}'>{_h.escape(str(lamp))}</span>"
    rel = lambda p: os.path.relpath(via / p, out).replace(os.sep, "/")
    links = [("VDF 管理器矩陣", "VIA_Reports/vdf/manager/VDF_MANAGER_MATRIX_latest.html"), ("VRN 管理器矩陣", "VIA_Reports/vrn2/manager/VRN_MANAGER_MATRIX_latest.html"),
             ("自建工作台(五系統)", "VIA_Reports/workbench/VIA_Workbench_Hub_latest.html"), ("VDF 擷取矩陣", "VIA_Reports/vdf/FETCH_MATRIX_latest.html")]
    vr = rep["verify_vrn"]
    if vr.get("html"):
        links.append(("VRN 輸出驗證矩陣", "VIA_Reports/vrn_reconcile_runs/" + vr["html"]))
    nav = "".join(f"<a href='{_h.escape(rel(p))}'>{_h.escape(lb)}</a>" if (via / p).is_file() else f"<a class='off'>{_h.escape(lb)}(未產生)</a>" for lb, p in links)
    steps = "".join(f"<tr><td>{_h.escape(s['step'])}</td><td>{chip(s['lamp'])}</td><td>{s['rc']}</td><td>{s['sec']}</td><td>{_h.escape(s['last'])}</td></tr>" for s in rep["steps"])
    vd = rep["verify_vdf"]
    vdf_rows = "".join(f"<tr><td>{_h.escape(r['view'])}</td><td class='n'>{r['rows']:,}</td><td>{r['min_date'] or '—'}</td><td>{r['max_date'] or '—'}</td>"
                       f"<td class='n'>{r['lag_days'] if r['lag_days'] is not None else '—'}</td><td>{chip('GREEN' if r['match'] else 'RED')}</td></tr>" for r in vd.get("tables", []))
    vrn_rows = "".join(f"<tr><td>{'個股' if p['kind'] == 'stock' else '非個股'}</td><td class='n'>{p['json']}</td><td class='n'>{p['csv']}</td><td class='n'>{p['parquet']}</td>"
                       f"<td>{chip('GREEN' if p['match'] else 'RED')}</td></tr>" for p in vr.get("parts", []))
    css = (f"body{{background:{t['bg']};color:{t['fg']};font:14px/1.5 system-ui,'Noto Sans TC',sans-serif;margin:0;padding:16px;"
           "padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}"
           f"h1{{font-size:1.35rem;color:{t['accent']};margin:.2rem 0}}h2{{font-size:1.05rem;color:{t['accent']};margin:1.4rem 0 .4rem}}"
           f"p.sub{{color:{t['muted']};margin:.2rem 0 1rem}}nav a{{display:inline-block;margin:0 .5rem .5rem 0;padding:.3rem .7rem;border:1px solid {t['line']};"
           f"border-radius:6px;background:{t['panel']};color:{t['fg']};text-decoration:none}}nav a.off{{color:{t['muted']};border-style:dashed}}"
           f"table{{border-collapse:collapse;width:100%;background:{t['panel']}}}td,th{{border-bottom:1px solid {t['line']};padding:5px 8px;text-align:left;vertical-align:top}}"
           f"th{{color:{t['muted']};font-size:.8rem;white-space:nowrap}}tr:nth-child(even) td{{background:{t['row']}}}td.n{{text-align:right;font-variant-numeric:tabular-nums}}"
           ".wrap{overflow-x:auto}.chip{display:inline-block;padding:.05rem .5rem;border-radius:999px;font-weight:600;font-size:.82rem}"
           f".kpi{{display:flex;flex-wrap:wrap;gap:.6rem}}.kpi div{{background:{t['panel']};border:1px solid {t['line']};border-radius:8px;padding:.5rem .8rem;min-width:9rem}}"
           f".kpi b{{display:block;font-size:1.25rem;color:{t['accent']}}}.kpi span{{color:{t['muted']};font-size:.8rem}}")
    body = (f"<h1>VDF + VRN 一鍵流程 · 總覽 {chip(rep['lamp'])}</h1><p class='sub'>{_h.escape(rep['at'])} · 起始日 {_h.escape(rep['start'])} · 色票 {_h.escape(t['_source'])} · "
            f"同意閘 NET {_h.escape(rep['gates']['VIA_NET_CONSENT'])} / SCRAPE {_h.escape(rep['gates']['VIA_SCRAPE_CONSENT'])}</p><nav>{nav}</nav>"
            f"<div class='kpi'><div><b>{vd.get('views', 0)}</b><span>VDF 湖內表</span></div><div><b>{vd.get('rows_total', 0):,}</b><span>VDF Parquet 總列數</span></div>"
            f"<div><b>{sum(p['parquet'] or 0 for p in vr.get('parts', []))}</b><span>VRN 矩陣列(個股 + 非個股)</span></div>"
            f"<div><b>{sum(1 for s in rep['steps'] if s['lamp'] == 'GREEN')}/{len(rep['steps'])}</b><span>步驟綠燈</span></div></div>"
            f"<h2>步驟</h2><div class='wrap'><table><tr><th>步驟</th><th>燈</th><th>rc</th><th>秒</th><th>最後一行</th></tr>{steps}</table></div>"
            f"<h2>VDF Parquet 資料庫驗證 {chip(vd['lamp'])}</h2><p class='sub'>DuckDB 目錄實數列數 對 狀態檔列數;{_h.escape(vd.get('why') or '全部相符')}</p>"
            f"<div class='wrap'><table><tr><th>表(VIEW)</th><th>列數</th><th>最早</th><th>最晚</th><th>落後天</th><th>相符</th></tr>{vdf_rows}</table></div>"
            f"<h2>VRN 輸出驗證 {chip(vr['lamp'])}</h2><p class='sub'>{_h.escape(vr.get('run') or '—')} · JSON / CSV / Parquet 三份列數;{_h.escape(vr.get('why') or '全部相符')}</p>"
            f"<div class='wrap'><table><tr><th>類別</th><th>JSON</th><th>CSV</th><th>Parquet</th><th>相符</th></tr>{vrn_rows}</table></div>")
    doc = ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover'>"
           f"<title>VDF + VRN 一鍵總覽</title><style>{css}</style></head><body>{body}</body></html>")
    out.mkdir(parents=True, exist_ok=True)
    p = out / "VDF_VRN_ONESHOT_latest.html"
    p.write_text(doc, encoding="utf-8")
    return p


def run(argv: list) -> int:
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    start, jobs = opt("--start", "2022-01-01"), opt("--jobs", "5")
    vdf, vrn = VIA / "functional modules" / "VDF", VIA / "functional modules" / "VRN"
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    logs = OUT / "logs" / stamp
    logs.mkdir(parents=True, exist_ok=True)
    gates = {k: (os.environ.get(k) or "UNSET") for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
    py, steps = sys.executable, []
    e239, e049 = tail(vdf / "engine", "VDF_ENG239_ParquetLakeBuild_v*.py"), tail(vrn, "VRN_ENG049_ContentReconcile_v*.py")
    mv, mr = tail(vdf, "VDF_SystemManager_v*.py"), tail(vrn, "VRN_SystemManager_v*.py")
    for need, nm in ((e239, "VDF_ENG239"), (e049, "VRN_ENG049"), (mv, "VDF_SystemManager"), (mr, "VRN_SystemManager")):
        if need is None:
            print(f"[一鍵] RED · 找不到 {nm} 尾版(先 git 取得最新)")
            return 1
    a1 = [py, str(e239), "run", "--all", "--start", start, "--jobs", jobs] + (["--skip-fetch"] if "--skip-fetch" in argv else [])
    steps.append(run_step("① VDF 擷取 + 建 Parquet 湖", a1, VIA, logs / "1_vdf_lake.log", soft_rc=(2,)))
    if "--vrn-full" in argv:
        steps.append(run_step("③a VRN 完整管線(launch --run)", [py, str(mr), "launch", "--run"], vrn, logs / "3a_vrn_full.log"))
    steps.append(run_step("③ VRN 輸出矩陣", [py, str(e049), "matrix"], vrn, logs / "3_vrn_matrix.log"))
    steps.append(run_step("⑤ VDF 收尾(矩陣頁 + 備份)", [py, str(mv), "closeout"], vdf, logs / "5_vdf_closeout.log", soft_rc=(2, 3)))
    steps.append(run_step("⑤ VRN 收尾(矩陣頁 + 備份)", [py, str(mr), "closeout"], vrn, logs / "5_vrn_closeout.log", soft_rc=(2, 3)))
    vd, vr = verify_vdf(VIA, start), verify_vrn(VIA)
    rep = {"schema": "via.oneshot/1", "version": VERSION, "at": stamp, "start": start, "gates": gates, "steps": steps, "verify_vdf": vd, "verify_vrn": vr}
    rep["lamp"] = worst([s["lamp"] for s in steps] + [vd["lamp"], vr["lamp"]])
    p = page(VIA, OUT, rep)
    (OUT / "ONESHOT_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n[一鍵] {rep['lamp']} · VDF 湖 {vd.get('views', 0)} 表 {vd.get('rows_total', 0):,} 列 驗證 {vd['lamp']} · VRN 矩陣驗證 {vr['lamp']} · "
          + " · ".join(f"{s['step'].split()[0]} {s['lamp']}" for s in steps) + f"\n[一鍵] 總覽頁 {p}")
    if "--no-open" not in argv and not os.environ.get("VIA_NO_OPEN"):
        try:
            webbrowser.open(p.as_uri())
        except Exception:
            pass
    return {"GREEN": 0, "YELLOW": 2, "RED": 1}[rep["lamp"]]


def selftest() -> int:
    ok = []

    def chk(n, c, note=""):
        ok.append(bool(c))
        print(f"  [{'OK' if c else 'FAIL'}] {n}{(' · ' + str(note)) if note and not c else ''}")
    import duckdb
    with tempfile.TemporaryDirectory() as td:
        v = Path(td)
        lake = v / "VIA_Reports" / "vdf_lake"
        (lake / "db" / "t").mkdir(parents=True)
        pq = lake / "db" / "t" / "part-1.parquet"
        duckdb.connect().execute(f"copy (select '2330' as ticker, date '2022-01-03' as date union all select '2330', date '2026-11-12') to '{pq}' (format parquet)")
        con = duckdb.connect(str(lake / "VDF_catalog.duckdb"))
        con.execute(f"create view \"v_db__t\" as select * from read_parquet('{pq}')")
        con.close()
        st = {"tables": [{"view": "v_db__t", "rows": 2, "date_col": "date", "min_date": "2022-01-03", "max_date": "2026-11-12", "lag_days": 1}]}
        (lake / "LAKE_STATUS_latest.json").write_text(json.dumps(st))
        r = verify_vdf(v, "2022-01-01")
        chk("① VDF 驗證:目錄實數 2 列 == 狀態檔 2 列 → GREEN", r["lamp"] == "GREEN" and r["rows_total"] == 2, r)
        st["tables"][0]["rows"] = 3
        (lake / "LAKE_STATUS_latest.json").write_text(json.dumps(st))
        chk("② 列數對不上 → RED 點名", verify_vdf(v, "2022-01-01")["mismatch"] == ["v_db__t"])
        chk("③ 有早於起始日的列 → RED", verify_vdf(v, "2023-01-01")["lamp"] == "RED")
        d = v / "VIA_Reports" / "vrn_reconcile_runs"
        d.mkdir(parents=True)
        base = d / "matrix_20260101_000000"
        Path(str(base) + ".json").write_text(json.dumps({"stock": [{"a": 1}, {"a": 2}], "nonstock": [{"b": 1}]}))
        Path(str(base) + "_stock.csv").write_text("a\n1\n2\n", encoding="utf-8-sig")
        Path(str(base) + "_nonstock.csv").write_text("b\n1\n", encoding="utf-8-sig")
        duckdb.connect().execute(f"copy (select 1 a union all select 2) to '{base}_stock.parquet' (format parquet)")
        duckdb.connect().execute(f"copy (select 1 b) to '{base}_nonstock.parquet' (format parquet)")
        vr = verify_vrn(v)
        chk("④ VRN 驗證:JSON / CSV / Parquet 三份列數相同 → GREEN", vr["lamp"] == "GREEN" and [p["parquet"] for p in vr["parts"]] == [2, 1], vr)
        Path(str(base) + "_stock.csv").write_text("a\n1\n", encoding="utf-8-sig")
        chk("⑤ CSV 少一列 → RED 點名 stock", verify_vrn(v)["why"].endswith("stock"))
        st["tables"][0]["rows"] = 2
        (lake / "LAKE_STATUS_latest.json").write_text(json.dumps(st))
        rep = {"at": "t", "start": "2022-01-01", "gates": {"VIA_NET_CONSENT": "UNSET", "VIA_SCRAPE_CONSENT": "UNSET"}, "lamp": "YELLOW",
               "steps": [{"step": "① x", "rc": 2, "lamp": "YELLOW", "sec": 1, "last": "GATED", "log": "l"}], "verify_vdf": verify_vdf(v, "2022-01-01"), "verify_vrn": vr}
        pg = page(v, v / "VIA_Reports" / "oneshot", rep).read_text(encoding="utf-8")
        chk("⑥ 總覽頁:標題 · viewport · 步驟表 · VDF 表 · VRN 表 · 未產生的連結標示 · 無外部資源", "<title>" in pg and "viewport" in pg and "v_db__t" in pg
            and "非個股" in pg and "未產生" in pg and "http" not in pg.replace("http-equiv", ""))
    chk("⑦ 燈的合併:有 RED 就 RED · 否則有 YELLOW 就 YELLOW", worst(["GREEN", "YELLOW"]) == "YELLOW" and worst(["GREEN", "RED", "YELLOW"]) == "RED" and worst(["GREEN"]) == "GREEN")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 只用子程序 · 不 import 系統程式 · 不代設同意閘 · 零 TA-Lib · 不裝套件",
        "environ[\"VIA_NET" + "_CONSENT\"] =" not in src and "import " + "talib" not in src and ("pip " + "install") not in src
        and not re.search(r"^\s*(?:import|from)\s+(?:VDF|VRN|VQG|VAP|CGC)_", src, re.M))
    print(f"[selftest] VIA_VdfVrnOneShot {VERSION} {sum(ok)}/{len(ok)}")
    return 0 if all(ok) else 1


def main() -> int:
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        return selftest()
    if a[:1] == ["run"]:
        return run(a[1:])
    print(__doc__)
    return 0 if not a or a[0] in ("-h", "--help") else 2


if __name__ == "__main__":
    sys.exit(main())
