#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL277_AiOps v0100 — AI 常做動作的引擎:AI 叫一個動詞 → 拿一張小卡(判決 + 指紋)→ 下一步,不再整檔讀報告

操作員 2026-10-14:「回顧對話紀錄 AI 常做的動作做引擎讓 AI 啟動接受結果在反饋以節省 TOKEN」
「DATABASE 結構最佳化省 API 擷取 TOKEN 及 AI 讀取現況」。回顧對話紀錄,AI 每輪都重做這幾件(每次幾萬 token):
  status            掃 VIA_Reports 的 *_latest.json(判決 · 燈 · 時間 · sha16)+ 交接頭(lamp · closeout_lamp · summary)+ git 分支對 main
                    → VIA_Reports/aiops/STATUS_INDEX_latest.json(一個小檔取代讀 93 份報告與 600 KB 交接檔)。--if-etag <sha16> 沒變回 304
  dbcard            VDF 主庫唯讀卡:每表列數 · 欄數 · 日期欄最小/最大(期間正典的日期欄)→ VIA_Reports/aiops/DB_CARD_latest.json
                    (AI 先看卡再決定要不要抓 —— 已有的日期段不再打 API)
  collide [--base <ref>]   引擎 / 模組編號撞號(同號不同名);給 --base 只報**這次新增**的撞號(推之前 LL334 掃描)
  pslint            PS 尾版:缺 PS-ACCEL 加速器橋 · 自己壓掉自己的頁(重用 CGC_MDL248 FullCheck 尾版的 own_page_scan)
  killgate [--base <ref>]  包 CGC_MDL187 刪除閘尾版(--run-selftest),只回判決行
  report <stages.json>     整合啟動器各段結果 → VIA_Reports/aiops/AIOPS_RUN_latest.html(與 FullCheck 同款燈號表)
只收 VCGC 呼叫;零網路;庫一律 read_only;不改任何報告、不改登記冊(只寫 VIA_Reports/aiops/)。
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

import hashlib
import html
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
ENGINE = Path(__file__).stem
OUT = "VIA_Reports/aiops"
HANDOFF = "docs/handoff/HANDOFF_latest.json"
JUDGE_KEYS = ("verdict", "lamp", "closeout_lamp", "state", "overall", "status", "rc")
TIME_KEYS = ("at", "generated_at", "ts", "time", "utc", "generated")
SKIP_PARTS = {".git", "VIA_RetiredEngines", "_archive", "node_modules", "__pycache__", "SCOPE_COPY"}
NUM_RX = re.compile(r"^([A-Z]{2,5}_(?:MDL|ENG)\d{3})_([A-Za-z0-9]+)_v\d+\.(?:py|ps1)$")
DB_GLOBS = ("functional modules/VDF/output_hub/**/*.duckdb", "functional modules/VDF/registry_output/**/*.duckdb",
            "functional modules/VRN/db/*.duckdb", "functional modules/VRN/output_hub/**/*.duckdb")
DB_SKIP = ("_self_test", "selftest", "_tmp", "_repo_")


def output_dbs(via: Path) -> tuple:
    """VDF / VRN output databases on this tree (self-test and temp copies left out)."""
    via = Path(via)
    found = {str(p.relative_to(via)) for g in DB_GLOBS for p in via.glob(g) if p.is_file()}
    return tuple(sorted(x for x in found if not any(k in x for k in DB_SKIP)))
DATE_COLS = ("trade_date", "date", "portfolio_date", "data_date", "as_of", "asof", "asof_date", "snapshot_date", "snapshot_at",
             "last_seen", "run_at", "list_date", "fetched_at", "updated_at")
PS_ACCEL = "[VIA:PS-ACCEL:"
LAMP = {"GREEN": "#1a7f37", "YELLOW": "#9a6700", "RED": "#cf222e", "SKIP": "#57606a"}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha16(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def _tail(stem: str, via: Path = VIA) -> Path | None:
    vn = re.compile(re.escape(stem) + r"_v(\d+)\.py$")
    c = [(int(m.group(1)), p) for p in (Path(via) / "supportive modules" / "registry").glob(stem + "_v*.py")
         if (m := vn.search(p.name))]
    return max(c)[1] if c else None


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem.replace(".", "_") + "_for_" + ENGINE, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write(via: Path, name: str, obj) -> Path:
    p = Path(via) / OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def _git(via: Path, *args) -> str:
    try:
        return subprocess.run(["git", "-C", str(via), *args], capture_output=True, text=True, timeout=60).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


# ---------------------------------------------------------------- status
def status(via: Path = VIA) -> dict:
    via = Path(via)
    rows = []
    for p in sorted((via / "VIA_Reports").rglob("*_latest.json")):
        if SKIP_PARTS & set(p.relative_to(via).parts) or p.parent.name == "aiops":
            continue
        try:
            raw = p.read_bytes()
            d = json.loads(raw.decode("utf-8"))
        except (OSError, ValueError, UnicodeDecodeError):
            rows.append({"path": str(p.relative_to(via)), "error": "UNREADABLE"})
            continue
        row = {"path": str(p.relative_to(via)), "sha16": sha16(raw), "kb": round(len(raw) / 1024, 1)}
        if isinstance(d, dict):
            for k in JUDGE_KEYS:
                if k in d and isinstance(d[k], (str, int, float, bool)):
                    row[k] = d[k]
            for k in TIME_KEYS:
                if isinstance(d.get(k), str):
                    row["at"] = d[k]
                    break
        rows.append(row)
    ho = {}
    hp = via / HANDOFF
    if hp.exists():
        d = json.loads(hp.read_text(encoding="utf-8")) if hp.stat().st_size else {}
        ho = {k: d.get(k) for k in ("at", "lamp", "closeout_lamp", "summary") if k in d}
    head = _git(via, "rev-parse", "--short=12", "HEAD")
    ahead = _git(via, "rev-list", "--left-right", "--count", "origin/main...HEAD").split()
    red = [r["path"] for r in rows if any(str(r.get(k, "")).upper() in ("RED", "FAIL", "BLOCKED") for k in JUDGE_KEYS)]
    body = {"reports": rows, "handoff": ho,
            "git": {"head": head, "branch": _git(via, "rev-parse", "--abbrev-ref", "HEAD"),
                    "behind_main": int(ahead[0]) if len(ahead) == 2 else None,
                    "ahead_main": int(ahead[1]) if len(ahead) == 2 else None},
            "red": red}
    etag = sha16(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    return {"schema": "VIA_AiOps_StatusIndex_v0100", "engine": ENGINE, "at": now_utc(), "etag": etag, **body}


# ---------------------------------------------------------------- dbcard
def dbcard(via: Path = VIA, dbs=None) -> dict:
    via = Path(via)
    dbs = output_dbs(via) if dbs is None else dbs
    try:
        import duckdb
    except ImportError:
        return {"schema": "VIA_AiOps_DbCard_v0100", "at": now_utc(), "lamp": "YELLOW", "why": "duckdb 未裝", "dbs": []}
    out = []
    for rel in dbs:
        p = via / rel
        if not p.exists():
            out.append({"db": rel, "state": "ABSENT"})
            continue
        try:
            con = duckdb.connect(str(p), read_only=True)
        except Exception as e:  # noqa: BLE001 — 鎖住 / 版本不合 → 誠實記一筆
            out.append({"db": rel, "state": "LOCKED_OR_BAD", "why": str(e)[:160]})
            continue
        tabs = []
        try:
            for (t,) in con.execute("select table_name from information_schema.tables "
                                    "where table_schema='main' order by 1").fetchall():
                cols = [c for (c,) in con.execute("select column_name from information_schema.columns "
                                                  "where table_schema='main' and table_name=? order by ordinal_position", [t]).fetchall()]
                n = con.execute(f'select count(*) from "{t}"').fetchone()[0]
                row = {"table": t, "rows": n, "cols": len(cols)}
                dc = next((c for c in DATE_COLS if c in cols), None)
                if dc and n:
                    lo, hi = con.execute(f'select min("{dc}"), max("{dc}") from "{t}"').fetchone()
                    row.update({"date_col": dc, "min": str(lo)[:19], "max": str(hi)[:19]})
                tabs.append(row)
        finally:
            con.close()
        out.append({"db": rel, "state": "OK", "kb": p.stat().st_size // 1024, "tables": tabs})
    return {"schema": "VIA_AiOps_DbCard_v0100", "engine": ENGINE, "at": now_utc(),
            "lamp": "GREEN" if all(d["state"] == "OK" for d in out) else "YELLOW", "dbs": out}


# ---------------------------------------------------------------- collide
def _num_map(names) -> dict:
    m = {}
    for n in names:
        hit = NUM_RX.match(Path(n).name)
        if hit and not (SKIP_PARTS & set(Path(n).parts)):
            m.setdefault(hit.group(1), set()).add(hit.group(2))
    return m


def collide(via: Path = VIA, base: str | None = None) -> dict:
    via = Path(via)
    now = _num_map(str(p.relative_to(via)) for p in via.rglob("*") if p.suffix in (".py", ".ps1") and p.is_file())
    dup = {k: sorted(v) for k, v in now.items() if len(v) > 1}
    new = dup
    if base:
        old = _num_map(_git(via, "ls-tree", "-r", "--name-only", base, "--", ".").splitlines())
        new = {k: v for k, v in dup.items() if set(v) - old.get(k, set())}  # 這個撞號裡有 base 沒有的名字 = 這次造成的
    return {"schema": "VIA_AiOps_Collide_v0100", "engine": ENGINE, "at": now_utc(), "base": base,
            "numbers": len(now), "collisions": len(dup), "new": new,
            "lamp": "RED" if (base and new) else ("YELLOW" if dup and not base else "GREEN")}


# ---------------------------------------------------------------- pslint
def pslint(via: Path = VIA) -> dict:
    via = Path(via)
    fc = _tail("CGC_MDL248_FullCheck", via) or _tail("CGC_MDL248_FullCheck", VIA)
    m = _load(fc)
    tails = m._ps_tails(via)
    tail_rel = {str(p.relative_to(via)) for p in tails}
    bs = _tail("CGC_MDL124_BridgeSweeper", via)
    sweep = _load(bs) if bs else None
    while sweep is not None and not hasattr(sweep, "scan_ps"):       # 薄尾往回找到真正的 scan_ps(豁免名冊與 BridgeSweeper 同一份)
        sweep = getattr(sweep, "PRIOR", None)
    if sweep is not None and Path(sweep.VIA).resolve() == via.resolve():
        no_accel = sorted(r["file"] for r in sweep.scan_ps(".") if r["state"] == "MISSING" and r["file"] in tail_rel)
    else:                                                          # 暫存樹 / BridgeSweeper 不在:只看標記
        no_accel = sorted(str(p.relative_to(via)) for p in tails
                          if PS_ACCEL not in p.read_text(encoding="utf-8", errors="replace"))
    own = m.own_page_scan(via)
    return {"schema": "VIA_AiOps_PsLint_v0100", "engine": ENGINE, "at": now_utc(), "by": fc.name + (" · " + bs.name if bs else ""),
            "tails": len(tails), "no_accel": no_accel, "own_page": own,
            "lamp": "RED" if own or no_accel else "GREEN"}


# ---------------------------------------------------------------- killgate
def killgate(via: Path = VIA, base: str = "origin/main") -> dict:
    kg = _tail("CGC_MDL187_ModuleChangeKillGate", via)
    if kg is None:
        return {"lamp": "YELLOW", "why": "CGC_MDL187 不在"}
    r = subprocess.run([sys.executable, str(kg), "--base", base, "--run-selftest"], cwd=str(via),
                       capture_output=True, text=True, timeout=1800, env={**os.environ, "VIA_FROM_VCGC": "YES"})
    keep = [ln for ln in (r.stdout + r.stderr).splitlines() if re.search(r"KILL-\d+|判決|VERDICT|PASS|FAIL|\bRED\b|\bGREEN\b", ln)]
    return {"engine": ENGINE, "by": kg.name, "rc": r.returncode, "lines": keep[-40:],
            "lamp": "GREEN" if r.returncode == 0 else "RED"}


# ---------------------------------------------------------------- report
def report(via: Path, stages: list, title: str = "VIA 一鍵整合") -> Path:
    via = Path(via)
    lamps = [str(s.get("lamp", "SKIP")).upper() for s in stages]
    overall = "RED" if "RED" in lamps else ("YELLOW" if "YELLOW" in lamps else "GREEN")
    tr = "".join(
        f"<tr><td>{i + 1}</td><td>{html.escape(str(s.get('name', '')))}</td>"
        f"<td><span class=l style='background:{LAMP.get(lamps[i], '#57606a')}'>{lamps[i]}</span></td>"
        f"<td>{html.escape(str(s.get('by', '')))}</td><td>{s.get('sec', '')}</td>"
        f"<td><pre>{html.escape(str(s.get('note', ''))[:1200])}</pre></td></tr>" for i, s in enumerate(stages))
    page = f"""<!doctype html><html lang=zh-Hant><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>
:root{{--bg:#fff;--fg:#1f2328;--mute:#57606a;--line:#d0d7de}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0d1117;--fg:#e6edf3;--mute:#8d96a0;--line:#30363d}}}}
body{{background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,"Noto Sans TC",sans-serif;margin:0;padding:16px}}
table{{border-collapse:collapse;width:100%}}td,th{{border-bottom:1px solid var(--line);padding:6px;text-align:left;vertical-align:top}}
.l{{color:#fff;border-radius:4px;padding:1px 8px;font-weight:600}}pre{{margin:0;white-space:pre-wrap;font-size:12px;color:var(--mute)}}
</style></head><body><h1>{html.escape(title)} <span class=l style='background:{LAMP[overall]}'>{overall}</span></h1>
<p>{now_utc()} · {ENGINE} · {len(stages)} 段 · GREEN {lamps.count('GREEN')} · YELLOW {lamps.count('YELLOW')} · RED {lamps.count('RED')} · SKIP {lamps.count('SKIP')}</p>
<table><tr><th>#</th><th>段</th><th>燈</th><th>正主</th><th>秒</th><th>摘要</th></tr>{tr}</table></body></html>"""
    p = Path(via) / OUT / "AIOPS_RUN_latest.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(page, encoding="utf-8")
    _write(via, "AIOPS_RUN_latest.json", {"schema": "VIA_AiOps_Run_v0100", "at": now_utc(), "lamp": overall, "stages": stages})
    return p


# ---------------------------------------------------------------- cli
def _arg(a, k, d=None):
    return a[a.index(k) + 1] if k in a and len(a) > a.index(k) + 1 else d


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(f"[{ENGINE}] 只收 VCGC 呼叫(VIA_FROM_VCGC=YES)")
        return 2
    verb = a[0] if a else ""
    if verb == "status":
        d = status(VIA)
        if _arg(a, "--if-etag") == d["etag"]:
            print(f"304 status etag={d['etag']}")
            return 0
        p = _write(VIA, "STATUS_INDEX_latest.json", d)
        ho = d["handoff"]
        print(f"[狀態索引] {len(d['reports'])} 份報告 · 紅 {len(d['red'])} · 交接 lamp={ho.get('lamp')} "
              f"closeout={ho.get('closeout_lamp')} · git {d['git']['branch']}@{d['git']['head']} "
              f"落後 main {d['git']['behind_main']} 領先 {d['git']['ahead_main']} · etag={d['etag']} → {p.relative_to(VIA)}")
        for r in d["red"][:20]:
            print(f"  RED  {r}")
        return 1 if d["red"] else 0
    if verb == "dbcard":
        d = dbcard(VIA)
        p = _write(VIA, "DB_CARD_latest.json", d)
        for db in d["dbs"]:
            print(f"  {db['state']:<13} {db['db']}" + (f" · {len(db.get('tables', []))} 表" if db.get("tables") else ""))
            for t in db.get("tables", []):
                rng = f" · {t['date_col']} {t['min']}→{t['max']}" if t.get("date_col") else ""
                print(f"      {t['table']:<34} {t['rows']:>10} 列 · {t['cols']} 欄{rng}")
        print(f"[庫卡] {d['lamp']} → {p.relative_to(VIA)}")
        return 0 if d["lamp"] == "GREEN" else 2
    if verb == "collide":
        d = collide(VIA, _arg(a, "--base"))
        for k, v in (d["new"] or {}).items():
            print(f"  {'NEW ' if d['base'] else ''}{k}: {' · '.join(v)}")
        print(f"[撞號] {d['lamp']} · 編號 {d['numbers']} · 同號不同名 {d['collisions']}"
              + (f" · 對 {d['base']} 新增 {len(d['new'])}" if d["base"] else ""))
        return {"GREEN": 0, "YELLOW": 2}.get(d["lamp"], 1)
    if verb == "pslint":
        d = pslint(VIA)
        _write(VIA, "PSLINT_latest.json", d)
        for f in d["no_accel"]:
            print(f"  NO-ACCEL  {f}")
        for h in d["own_page"]:
            print(f"  OWN-PAGE  {h['file']}:{h['open']} (第 {h['set']} 行設 VIA_NO_OPEN=1 後沒還原)")
        print(f"[PS 檢查] {d['lamp']} · 尾版 {d['tails']} · 缺加速器 {len(d['no_accel'])} · 自壓頁 {len(d['own_page'])}")
        return 0 if d["lamp"] == "GREEN" else 1
    if verb == "killgate":
        d = killgate(VIA, _arg(a, "--base", "origin/main"))
        for ln in d.get("lines", []):
            print("  " + ln)
        print(f"[刪除閘] {d['lamp']} · {d.get('by')} rc={d.get('rc')}")
        return 0 if d["lamp"] == "GREEN" else 1
    if verb == "report" and len(a) > 1:
        stages = json.loads(Path(a[1]).read_text(encoding="utf-8"))
        p = report(VIA, stages, _arg(a, "--title", "VIA 一鍵整合"))
        print(f"[總頁] {p}")
        return 0
    print("用法:status [--if-etag <sha16>] | dbcard | collide [--base <ref>] | pslint | killgate [--base <ref>] | report <stages.json> | --selftest")
    return 2


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    with tempfile.TemporaryDirectory() as tmp:
        via = Path(tmp)
        (via / "VIA_Reports" / "a").mkdir(parents=True)
        (via / "VIA_Reports" / "a" / "A_latest.json").write_text(json.dumps({"verdict": "GREEN", "at": "t1", "big": [1] * 999}), encoding="utf-8")
        (via / "VIA_Reports" / "a" / "B_latest.json").write_text(json.dumps({"lamp": "RED"}), encoding="utf-8")
        (via / "VIA_Reports" / "a" / "C_latest.json").write_text("{bad", encoding="utf-8")
        (via / "docs" / "handoff").mkdir(parents=True)
        (via / HANDOFF).write_text(json.dumps({"lamp": "GREEN", "closeout_lamp": "YELLOW", "summary": {"pending": 3},
                                               "work_items": ["x"] * 999}), encoding="utf-8")
        d1, d2 = status(via), status(via)
        rows = {Path(r["path"]).name: r for r in d1["reports"]}
        chk("① 狀態索引:只留判決鍵與時間(大欄位不進卡)· 壞檔標 UNREADABLE · 紅燈列出 · 交接只留頭",
            rows["A_latest.json"].get("verdict") == "GREEN" and "big" not in rows["A_latest.json"]
            and rows["C_latest.json"].get("error") == "UNREADABLE" and d1["red"] == ["VIA_Reports/a/B_latest.json"]
            and d1["handoff"] == {"lamp": "GREEN", "closeout_lamp": "YELLOW", "summary": {"pending": 3}}, d1["red"])
        (via / "VIA_Reports" / "a" / "B_latest.json").write_text(json.dumps({"lamp": "GREEN"}), encoding="utf-8")
        chk("② etag:沒變同值(可回 304)· 報告一變 etag 就變", d1["etag"] == d2["etag"] and status(via)["etag"] != d1["etag"])
        reg = via / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        for n in ("CGC_MDL901_Alpha_v0100.py", "CGC_MDL901_Alpha_v0101.py", "CGC_MDL902_Beta_v0100.py", "CGC_MDL902_Gamma_v0100.py"):
            (reg / n).write_text("x=1\n", encoding="utf-8")
        (via / "functional modules" / "VIA_RetiredEngines").mkdir(parents=True)
        (via / "functional modules" / "VIA_RetiredEngines" / "CGC_MDL901_Old_v0100.py").write_text("", encoding="utf-8")
        c = collide(via)
        chk("③ 撞號:同號不同名才算(換版不算 · 隔離區不算)", c["new"] == {"CGC_MDL902": ["Beta", "Gamma"]}, c["new"])
        try:
            import duckdb
            db = via / "t.duckdb"
            con = duckdb.connect(str(db))
            con.execute("create table px(trade_date date, v int)")
            con.execute("insert into px values ('2026-10-01',1),('2026-10-13',2)")
            con.execute("create table meta(k varchar)")
            con.close()
            card = dbcard(via, ("t.duckdb", "nope.duckdb"))
            t = {x["table"]: x for x in card["dbs"][0]["tables"]}
            chk("④ 庫卡:唯讀開 · 列數 / 欄數 / 日期欄區間 · 缺庫標 ABSENT(黃不紅)",
                t["px"]["rows"] == 2 and t["px"]["max"].startswith("2026-10-13") and "date_col" not in t["meta"]
                and card["dbs"][1]["state"] == "ABSENT" and card["lamp"] == "YELLOW", t)
        except ImportError:
            chk("④ 庫卡:duckdb 未裝 → 誠實黃", dbcard(via)["lamp"] == "YELLOW")
        p = report(via, [{"name": "入口", "lamp": "GREEN", "by": "X", "sec": 1.0, "note": "<b>ok</b>"},
                         {"name": "清單", "lamp": "SKIP", "note": "沒同意"}, {"name": "閘", "lamp": "RED"}])
        txt = p.read_text(encoding="utf-8")
        chk("⑤ 總頁:有紅整體紅 · 內容跳脫 · 同步寫 json · 有暗色",
            "RED</span></h1>" in txt and "&lt;b&gt;" in txt and (via / OUT / "AIOPS_RUN_latest.json").exists()
            and "prefers-color-scheme:dark" in txt)
    pl = pslint(VIA)
    src = Path(__file__).read_text(encoding="utf-8")
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main(["status"]) == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    chk("⑥ 實樹 PS 檢查跑得動(重用 FullCheck 尾版)· 只收 VCGC · 加速器橋在 · 不碰 TA-Lib",
        pl["tails"] > 100 and denied and "VIA:ACCEL-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M),
        f"尾版 {pl['tails']} · 自壓頁 {len(pl['own_page'])}")
    print(f"  {ENGINE} selftest {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
