#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL096_SyncStatus v0102 — 全景同步狀態台+完成度儀表
====================================================================
操作員令:「一個指令連上 GITHUB 及雲端看目前系統整合最詳細的狀態,
包含目前電腦中的資料夾;多矩陣報告一頁堆疊自動最佳化;矩陣也最佳
化;字小一點較專業。」
機制:
  GitHub/雲端=git fetch(唯一外通道=git 子行程;離線=誠實降級標示)
  →HEAD↔origin 雙分支 ahead/behind+雲端最近 commit;
  雲端工作記錄=台帳尾+問題冊(唯讀 join);
  本機=雙 DuckDB 各表列數+價格年分佈+回補斷點(唯讀;鎖=誠實 busy)
  +資料夾矩陣(top-level 檔數/容量)+引擎名冊計數+執行狀態
  (boot marker/deck_runs 近況/grid 最新存證)。
輸出:VIA_UI_SyncStatus_v0100.html——六矩陣一頁堆疊(auto-fit 自適應
  /10.5px 小字專業/anywhere 換行零水平溢出/零 CDN 零外鏈)。
紅線(批218 操作員令):USD FX & Rates 模板=未經操作員允許不碰
  (P18 候令;本站僅列示不觸)。
批219 追令:「系統完成狀態 DASHBOARD;擷取資料庫按鍵;子系統整合
狀態及接續完成方法;RAW HTML UI SYNC」→新增 ⓪ 完成度儀表:各子系
統完成率進度條(全部自實證計算:斷點/庫列數/grid 存證,零發明)+
擷取資料庫按鍵(接 127.0.0.1:8765 指揮台橋=按下直跑;無橋=誠實提
示雙擊 VIA 啟橋)+子系統整合現況×接續完成方法矩陣。
批次修正：同步前只還原明確的 MasterControl 衍生頁，不再重置整個
ui_support，保護使用者可編輯的 Dashboard 模板與其他 UI 正本。
用法:python3 CGC_MDL096_SyncStatus_v0102.py [--open] [--no-fetch]
      | --selftest
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

import html
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
MEGA = VIA / "functional modules" / "VDF" / "output_hub" / "mega"
OUT = VIA / "supportive modules" / "ui_support" / "VIA_UI_SyncStatus_v0100.html"
BRANCH = "claude/via-system-followup-tz7k9t"


def _git(*args) -> str:
    try:
        r = subprocess.run(["git", "-C", str(VIA)] + list(args),
                           capture_output=True, text=True, timeout=60)
        return r.stdout.strip()
    except Exception:
        return ""


def gather_git(fetch: bool = True) -> dict:
    g = {"fetched": False, "fetch_attempted": fetch}
    if fetch:
        try:
            r = subprocess.run(["git", "-C", str(VIA), "fetch", "origin", "--quiet"],
                               capture_output=True, timeout=90)
            g["fetched"] = r.returncode == 0
        except Exception:
            pass  # 離線=誠實降級(頁面標示「本地快照」)
    # 狀態頁必須唯讀；更新工作樹僅能由明確的同步命令執行。
    g["head"] = _git("rev-parse", "--short", "HEAD")
    g["branch"] = _git("rev-parse", "--abbrev-ref", "HEAD")
    for label, ref in (("main", "origin/main"), ("followup", "origin/" + BRANCH)):
        lr = _git("rev-list", "--left-right", "--count", f"HEAD...{ref}")
        parts = lr.split() if lr else []
        g[label] = {"ahead": parts[0] if len(parts) == 2 else "?",
                    "behind": parts[1] if len(parts) == 2 else "?"}
    log = _git("log", "origin/main", "-6", "--pretty=%h|%ad|%s",
               "--date=format:%m-%d %H:%M")
    g["cloud_log"] = [dict(zip(("h", "ad", "s"), ln.split("|", 2)))
                      for ln in log.splitlines() if ln.count("|") >= 2]
    st = _git("status", "--short")
    g["dirty"] = len([ln for ln in st.splitlines() if ln.strip()])
    return g


def gather_ledgers() -> dict:
    out = {"ledger_tail": [], "ledger_n": 0, "problems": [], "prob_open": 0}
    try:
        reg = json.loads((HERE / "VIA_AutoCode_Registry_v0100.json")
                         .read_text(encoding="utf-8"))
        led = reg.get("ledger", [])
        out["ledger_n"] = len(led)
        out["ledger_tail"] = [{"code": e.get("code"), "kind": e.get("kind"),
                               "name": (e.get("name") or "")[:64]}
                              for e in led[-8:]][::-1]
    except Exception:
        pass
    try:
        pl = json.loads((HERE / "VIA_Problem_Ledger_v0100.json")
                        .read_text(encoding="utf-8"))
        probs = pl.get("problems", [])
        out["problems"] = [{"id": p.get("id"), "status": p.get("status"),
                            "title": (p.get("title") or "")[:56]}
                           for p in probs if "RESOLVED" not in str(p.get("status", ""))]
        out["prob_open"] = len(out["problems"])
    except Exception:
        pass
    return out


def gather_db() -> dict:
    out = {"dbs": [], "years": [], "ckpt": []}
    try:
        import duckdb
    except Exception:
        return out
    for label, name in (("台股", "vdf_tw_market.duckdb"),
                        ("全球", "vdf_global_market.duckdb")):
        p = MEGA / name
        if not p.exists():
            out["dbs"].append({"label": label, "state": "缺庫(fresh 未自舉)",
                               "tables": []})
            continue
        try:
            con = duckdb.connect(str(p), read_only=True)
            ts = sorted(r[0] for r in con.execute("SHOW TABLES").fetchall())
            tbl = [{"t": t, "n": con.execute(
                f'SELECT count(*) FROM "{t}"').fetchone()[0]} for t in ts]
            out["dbs"].append({"label": label, "state": "OK", "tables": tbl})
            if label == "台股" and any(x["t"] == "tw_daily_prices" for x in tbl):
                out["years"] = con.execute(
                    "SELECT substr(CAST(date AS VARCHAR),1,4) y, count(*) "
                    "FROM tw_daily_prices GROUP BY y ORDER BY y").fetchall()
            con.close()
        except Exception as exc:  # 鎖=誠實 busy 非假數
            out["dbs"].append({"label": label,
                               "state": f"busy/鎖({type(exc).__name__})=稍後再看",
                               "tables": []})
    try:
        ck = json.loads((MEGA / "history_backfill_checkpoint.json")
                        .read_text(encoding="utf-8"))
        out["ckpt"] = [{"k": k, "n": len(v)} for k, v in
                       sorted(ck.get("segments", {}).items())]
    except Exception:
        pass
    return out


def gather_fs() -> dict:
    out = {"folders": [], "engines": []}
    for d in sorted(VIA.iterdir()):
        if not d.is_dir() or d.name in (".git", "__pycache__"):
            continue
        n, sz = 0, 0
        for f in d.rglob("*"):
            if f.is_file() and ".git" not in f.parts:
                n += 1
                try:
                    sz += f.stat().st_size
                except OSError:
                    pass
        out["folders"].append({"d": d.name, "n": n, "mb": round(sz / 1e6, 1)})
    for label, root, pat in (
            ("VDF 引擎", VIA / "functional modules" / "VDF" / "engine", "VDF_ENG*.py"),
            ("VRN 引擎", VIA / "functional modules" / "VRN", "VRN_ENG*.py"),
            ("VAP 引擎", VIA / "functional modules" / "VAP", "**/*.py"),
            ("CGC 治理", HERE, "CGC_MDL*.py"),
            ("SUP 網路/支援", VIA / "supportive modules" / "network", "SUP_MDL*.py"),
            ("UI 頁", VIA / "supportive modules" / "ui_support", "*.html")):
        try:
            out["engines"].append({"g": label, "n": len(list(root.glob(pat)))})
        except Exception:
            out["engines"].append({"g": label, "n": 0})
    return out


def gather_runs() -> dict:
    out = {"boot": "無 marker", "grid": None, "deck": []}
    m = MEGA / ".last_boot_update"
    if m.exists():
        out["boot"] = m.read_text(encoding="utf-8").strip()
    runs = sorted((VIA / "VIA_Reports" / "selftest_runs").glob("GRID_*.json"))
    if runs:
        try:
            gv = json.loads(runs[-1].read_text(encoding="utf-8"))
            out["grid"] = {"f": runs[-1].name, "ok": gv.get("ok"),
                           "fail": gv.get("fail"), "skip": gv.get("skip")}
        except Exception:
            out["grid"] = {"f": runs[-1].name, "ok": "?", "fail": "?", "skip": "?"}
    dr = VIA / "VIA_Reports" / "deck_runs"
    if dr.exists():
        logs = sorted(dr.glob("*.log"), key=lambda p: p.stat().st_mtime)[-6:]
        for p in logs[::-1]:
            out["deck"].append({"f": p.name,
                                "ts": datetime.fromtimestamp(p.stat().st_mtime)
                                .strftime("%m-%d %H:%M"),
                                "kb": round(p.stat().st_size / 1024, 1)})
    return out


def gather_completion(db: dict, runs: dict) -> dict:
    """只在分母有證據時顯示比例；存在不等於完成，未知不畫假綠。"""
    tw = next((d for d in db["dbs"] if d["label"] == "台股"), {})
    tn = {t["t"]: t["n"] for t in tw.get("tables", [])}
    listings = tn.get("tw_listings", 0)
    ck = {c["k"]: c["n"] for c in db["ckpt"]}
    seg23, seg22 = ck.get("台股:2023", 0), ck.get("台股:2022", 0)
    grid = runs.get("grid") or {}
    def count(value):
        return value if isinstance(value, int) and not isinstance(value, bool) \
            and value >= 0 else None
    gok, gfail, gskip = (count(grid.get(key)) for key in ("ok", "fail", "skip"))
    gtot = gok + gfail + gskip if None not in (gok, gfail, gskip) else 0
    def pct(a, b):
        valid = (isinstance(a, (int, float)) and not isinstance(a, bool)
                 and isinstance(b, (int, float)) and not isinstance(b, bool)
                 and a >= 0 and b > 0 and a <= b)
        return round(100 * a / b, 1) if valid else None
    def ratio_text(a, b, unit="檔"):
        if b and isinstance(a, (int, float)) and a > b:
            return f"{a}/{b} {unit}（分子超過分母，資料待校驗）"
        return f"{a}/{b} {unit}"
    factor_n = tn.get("features_daily", 0)
    price_n = tn.get("tw_daily_prices", 0)
    rows = [
        {"sub": "VDF 價格庫 2023 段", "pct": pct(seg23, listings),
         "now": ratio_text(seg23, listings),
         "next": "按[歷史回補]鍵或雙擊 VIA=自動續(零列檔重探一次)"},
        {"sub": "VDF 價格庫 2022 段", "pct": pct(seg22, listings),
         "now": ratio_text(seg22, listings),
         "next": "按[歷史回補]鍵=接 checkpoint 續跑到齊"},
        {"sub": "VDF 2020/2021 段", "pct": None,
         "now": "批212 操作員終止(TERMINATED)",
         "next": "永久 SKIP;解除=僅憑操作員明令出新版"},
        {"sub": "因子相對價格列覆蓋率", "pct": pct(factor_n, price_n),
         "now": ratio_text(factor_n, price_n, "列"),
         "next": "按[日更]鍵=boot 鏈自動重建(價格新列後)"},
        {"sub": "族群聚合層", "pct": None,
         "now": f"{tn.get('group_features_daily', 0):,} 列",
         "next": "boot ⑧b 自動;月營收族群榜=按[月營收]鍵"},
        {"sub": "月營收庫(MOPS 官方)", "pct": None,
         "now": f"{tn.get('tw_monthly_revenue', 0):,} 點",
         "next": "每月 10 日後按[月營收]鍵=增量更新"},
        {"sub": "三源共識庫", "pct": None,
         "now": f"{tn.get('consensus_daily', 0):,} 筆",
         "next": "按[共識]鍵擴碼(預設 2330 2317 2454)"},
        {"sub": "沙盒 grid 綠燈率", "pct": pct(gok or 0, gtot),
         "now": f"OK {gok}/FAIL {gfail}(最新存證)",
         "next": "FAIL>0 時看治理矩陣黃紅燈明細"},
    ]
    done = [r["pct"] for r in rows if isinstance(r["pct"], (int, float))]
    measured_mean = round(sum(done) / len(done), 1) if done else None
    return {"rows": rows,
            # 任一項缺可靠分母時，不把已知子集均值冒充全系統完成度。
            "overall": measured_mean if len(done) == len(rows) else None,
            "measured_mean": measured_mean,
            "measured": len(done),
            "total": len(rows)}


def _rows(rows: list[list], head: list[str]) -> str:
    h = "".join(f"<th>{html.escape(str(c))}</th>" for c in head)
    b = "".join("<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in r) + "</tr>"
                for r in rows) or "<tr><td colspan='9'>(空=誠實)</td></tr>"
    return f"<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"


def render(g: dict, led: dict, db: dict, fs: dict, runs: dict,
           comp: dict | None = None) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    sync_state = ("已連 GitHub(fetch 成功)" if g.get("fetched") else
                  "本地快照(本次未執行 fetch)" if not g.get("fetch_attempted") else
                  "離線快照(fetch 未達=誠實標示)")
    m_git = _rows(
        [["HEAD", g.get("head", "?"), f"分支 {g.get('branch', '?')}",
          f"未提交變更 {g.get('dirty', 0)} 件"],
         ["↔ origin/main", f"領先 {g['main']['ahead']}",
          f"落後 {g['main']['behind']}", sync_state],
         ["↔ followup", f"領先 {g['followup']['ahead']}",
          f"落後 {g['followup']['behind']}", BRANCH]],
        ["項", "值", "值", "註"])
    m_cloud = _rows([[c["h"], c["ad"], c["s"][:76]] for c in g.get("cloud_log", [])],
                    ["commit", "時間", "主旨(雲端 origin/main 最近)"])
    m_led = _rows([[e["code"], e["kind"], e["name"]] for e in led["ledger_tail"]],
                  ["台帳", "類", f"最近 8 筆(全 {led['ledger_n']} 筆 append-only)"])
    dbrows = []
    for d in db["dbs"]:
        if d["tables"]:
            for t in d["tables"]:
                dbrows.append([d["label"], t["t"], f"{t['n']:,}"])
        else:
            dbrows.append([d["label"], "—", d["state"]])
    m_db = _rows(dbrows, ["庫", "表", "列數(唯讀;鎖=誠實 busy)"])
    m_yr = _rows([[y, f"{n:,}"] for y, n in db["years"]], ["年", "價格列數"]) \
        + _rows([[c["k"], c["n"]] for c in db["ckpt"]],
                ["回補斷點段", "已成檔數(2020/21=批212 終止)"])
    m_fs = _rows([[f["d"], f["n"], f["mb"]] for f in fs["folders"]],
                 ["資料夾(本機工作根)", "檔數", "MB"]) \
        + _rows([[e["g"], e["n"]] for e in fs["engines"]], ["名冊", "件數"])
    grid = runs.get("grid") or {}
    m_run = _rows(
        [["boot 日更 marker", runs["boot"], ""],
         ["grid 最新存證", grid.get("f", "無"),
          f"OK {grid.get('ok') if grid.get('ok') is not None else '未知'}/"
          f"FAIL {grid.get('fail') if grid.get('fail') is not None else '未知'}/"
          f"SKIP {grid.get('skip') if grid.get('skip') is not None else '未知'}"]]
        + [["deck 任務 log", d["f"], f"{d['ts']} · {d['kb']}KB"]
           for d in runs["deck"]],
        ["執行面", "值", "註"])
    m_hold = _rows(
        [[p["id"], p["status"], p["title"]] for p in led["problems"]]
        + [["P18(本批)", "AWAITING_OPERATOR",
            "USD FX & Rates 模板一致性最佳化=未經允許不碰(批218 紅線)"],
           ["批212 終止令", "ENFORCED", "2020/2021 年段續補=永久 SKIP(解除憑明令)"]],
        ["候令/凍結", "狀態", "說明"])
    comp = comp or {"rows": [], "overall": None, "measured_mean": None,
                    "measured": 0, "total": 0}
    def bar(v):
        if not isinstance(v, (int, float)):
            return ("<div class='bar unknown'><i></i></div>"
                    "<b>完整度未知</b>")
        c = "#22c55e" if v >= 99.9 else ("#f0b429" if v >= 50 else "#dc2626")
        return (f"<div class='bar'><i style='width:{min(v,100)}%;"
                f"background:{c}'></i></div><b>{v}%</b>")
    m_comp = "<table><thead><tr><th>子系統</th><th>完成度(實證)</th>"              "<th>現況</th><th>接續完成方法</th></tr></thead><tbody>" + "".join(
        f"<tr><td>{html.escape(str(r['sub']))}</td><td class='pv'>{bar(r['pct'])}</td>"
        f"<td>{html.escape(str(r['now']))}</td><td>{html.escape(str(r['next']))}</td></tr>"
        for r in comp["rows"]) + "</tbody></table>"
    m_act = ("<div class='sub' id='bstate'>本頁為唯讀快照；執行工作請進入同源安全主控台。</div>"
             "<div class='btnrow'><button class='act' id='openMaster' type='button'>"
             "開啟 VIA 安全主控台</button></div>")
    if isinstance(comp.get("overall"), (int, float)):
        overall_text = f"{comp['overall']}%（全部項目均有可靠分母）"
    elif isinstance(comp.get("measured_mean"), (int, float)):
        overall_text = ("完整度未知；"
                        f"{comp.get('measured', 0)}/{comp.get('total', 0)} 項可量測，"
                        f"其均值 {comp['measured_mean']}%")
    else:
        overall_text = "完整度未知；目前沒有可靠分母"
    sec0 = (f"<section class='full'><h2>⓪ 系統完成狀態 DASHBOARD"
            f"（總完成度 {overall_text}）</h2>"
            f"{bar(comp['overall'])}{m_act}{m_comp}</section>")
    secs = [("① GitHub↔雲端同步矩陣", m_git + m_cloud),
            ("② 雲端工作台帳矩陣(唯讀 join)", m_led),
            ("③ 本機資料庫矩陣", m_db),
            ("④ 年分佈+回補斷點矩陣", m_yr),
            ("⑤ 本機資料夾+名冊矩陣", m_fs),
            ("⑥ 執行狀態+候令凍結矩陣", m_run + m_hold)]
    body = sec0 + "".join(f"<section><h2>{t}</h2>{h}</section>" for t, h in secs)
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA SyncStatus · 全景同步狀態台</title>
<style>
:root{{--bg:#0b1220;--card:#111a2e;--line:#1e2a44;--tx:#c7d3e8;--dim:#7e8db0;
--ac:#4f8ef7;--ok:#22c55e;--warn:#f0b429}}
*{{box-sizing:border-box;margin:0}}
body{{background:var(--bg);color:var(--tx);font:10.5px/1.5 "Segoe UI",
"Noto Sans TC",sans-serif;padding:14px}}
h1{{font-size:14px;color:#e8eefb;letter-spacing:.4px}}
.sub{{color:var(--dim);font-size:10px;margin:2px 0 12px}}
main{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));
gap:10px;align-items:start}}
section{{background:var(--card);border:1px solid var(--line);border-radius:8px;
padding:10px;overflow:auto}}
h2{{font-size:11px;color:var(--ac);margin-bottom:6px;letter-spacing:.3px}}
table{{width:100%;border-collapse:collapse;margin-bottom:6px}}
th{{text-align:left;color:var(--dim);font-weight:600;font-size:9.5px;
border-bottom:1px solid var(--line);padding:2px 6px 3px 0}}
td{{padding:2px 6px 2px 0;border-bottom:1px dashed var(--line);
overflow-wrap:anywhere;font-variant-numeric:tabular-nums}}
tr:last-child td{{border-bottom:0}}
section.full{{grid-column:1/-1}}
.bar{{display:inline-block;width:120px;height:7px;background:#1e2a44;
border-radius:4px;overflow:hidden;vertical-align:middle;margin-right:6px}}
.bar i{{display:block;height:100%}}
.bar.unknown i{{width:0;background:var(--dim)}}
.pv b{{font-size:9.5px;color:#e8eefb}}
.btnrow{{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}}
.act{{background:#16233d;color:#c7d3e8;border:1px solid #2a3c61;
border-radius:6px;padding:5px 10px;font-size:10.5px;cursor:pointer}}
.act:hover{{border-color:var(--ac);color:#fff}}
</style></head><body>
<h1>VIA 全景同步狀態台(GitHub↔雲端↔本機)</h1>
<div class="sub">{ts} · 一頁六矩陣堆疊 · auto-fit 自適應 · 10.5px 專業小字
· anywhere 換行零水平溢出 · 零 CDN 零外鏈 · 唯讀聚合零重測</div>
<main>{body}</main>
<script>
document.getElementById("openMaster").addEventListener("click", () => {{
  window.open("http://127.0.0.1:8765/master", "_blank", "noopener");
}});
</script>
</body></html>"""


def run(fetch: bool = True, open_after: bool = False) -> int:
    g = gather_git(fetch)
    db, runs = gather_db(), gather_runs()
    html = render(g, gather_ledgers(), db, gather_fs(), runs,
                  gather_completion(db, runs))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp_name = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=OUT.parent,
                                         prefix=OUT.name + ".", suffix=".tmp",
                                         delete=False) as fh:
            fh.write(html)
            fh.flush()
            os.fsync(fh.fileno())
            tmp_name = fh.name
        os.replace(tmp_name, OUT)
    finally:
        if tmp_name and Path(tmp_name).exists():
            Path(tmp_name).unlink()
    cloud_state = ("已連" if g["fetched"] else
                   "本地快照" if not g.get("fetch_attempted") else "離線快照")
    print(f"[UI] {OUT.name} · 六矩陣一頁堆疊(GitHub {cloud_state})")
    if open_after:
        try:
            import webbrowser
            webbrowser.open(OUT.as_uri())
        except Exception:
            pass
    return 0


def regen_all() -> int:
    """批219:重生全部 UI 統一道(尾版動態解析;各生成器獨立跑,
    一站失敗不擋其餘=誠實逐報)"""
    import subprocess as sp
    jobs = [("supportive modules/registry", "CGC_MDL090_SystemHub_v*.py", []),
            ("supportive modules/registry", "CGC_MDL093_GovernanceMatrix_v*.py", []),
            ("supportive modules/registry", "CGC_MDL088_SystemTestPages_v*.py", []),
            ("supportive modules/registry", "CGC_MDL094_CommandDeck_v*.py", []),
            ("supportive modules/registry", "CGC_MDL097_PortalUI_v*.py", []),
            ("supportive modules/registry", "CGC_MDL098_DataCatalog_v*.py", []),
            ("supportive modules/registry", "CGC_MDL099_GlobalMarkets_v*.py", []),
            ("supportive modules/registry", "CGC_MDL100_ReportCards_v*.py", [])]
    jobs.append(("", "VIA_SYSTEM_MANAGER_v*.py", ["--no-open"]))
    bad = 0
    for d, pat, extra in jobs:
        cand = sorted((VIA / d).glob(pat))
        if not cand:
            print(f"  [SKIP] {pat}(無件=誠實)")
            continue
        r = sp.run([sys.executable, str(cand[-1])] + extra,
                   capture_output=True, text=True, timeout=300)
        print(f"  [{'OK' if r.returncode == 0 else 'FAIL'}] {cand[-1].name}")
        bad += 1 if r.returncode != 0 else 0
    run(fetch=False)   # 本站頁最後重生(含最新存證)
    return 1 if bad else 0


def selftest() -> int:
    global OUT
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    chk("① 外通道唯一=git 子行程(無 http 庫;離線=誠實降級)",
        all(("import " + k) not in src for k in ("requests", "httpx", "aiohttp"))
        and "誠實降級" in src)
    original_out = OUT
    with tempfile.TemporaryDirectory() as directory:
        OUT = Path(directory) / "VIA_UI_SyncStatus_v0100.html"
        try:
            rc = run(fetch=False)
            page = OUT.read_text(encoding="utf-8")
        finally:
            OUT = original_out
    chk("② 六矩陣區段在頁(git/台帳/資料庫/年分佈/資料夾/執行候令)",
        rc == 0 and all(f"{i}" in page for i in "①②③④⑤⑥"))
    chk("③ 小字專業排版(10.5px+auto-fit+anywhere+零水平溢出)",
        all(k in page for k in ("10.5px", "auto-fit", "anywhere")))
    chk("④ 台帳/問題冊唯讀 join(TOOL 尾筆+候令列示)",
        "TOOL-" in page and "P18" in page)
    chk("⑤ DB 唯讀+鎖容錯(busy=誠實非假數)",
        "read_only=True" in src and "誠實 busy" in src)
    chk("⑥ 模板紅線宣告(批218:未經操作員允許不碰)",
        "未經" in page and "不碰" in page and "AWAITING_OPERATOR" in page)
    chk("⑦ 零 CDN 零外鏈(頁內無外部資源引用 src=/href=/@import)",
        all(k not in page for k in ('src="http', "src='http", 'href="http',
                                    "href='http", "@import")))
    chk("⑧ 加速橋掛載+離線快照誠實標示",
        "ACCEL-BRIDGE" in src and any(label in page for label in
                                      ("本地快照", "離線快照", "已連 GitHub")))
    chk("⑨ 完成度儀表+安全主控入口在頁(狀態頁唯讀、不發 mutation GET)",
        "⓪ 系統完成狀態 DASHBOARD" in page and "openMaster" in page
        and "/run?task=" not in page and "class='bar" in page)
    chk("⑩ 接續完成方法矩陣(有據才算比例+終止段誠實標示+方法欄)",
        "接續完成方法" in page and "TERMINATED" in page
        and "完整度未知" in page and "接 checkpoint 續跑到齊" in page)
    print(f"  [計] 十檢 OK {10 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 全景同步狀態台+完成度儀表(CGC_MDL096 v0102)· 十檢自測(零觸網)===")
        return selftest()
    if "--regen-all" in args:
        return regen_all()
    return run(fetch="--no-fetch" not in args, open_after="--open" in args)


if __name__ == "__main__":
    sys.exit(main())
