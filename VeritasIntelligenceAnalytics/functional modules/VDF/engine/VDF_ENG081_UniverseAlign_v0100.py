#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG081_UniverseAlign v0100 — 台股每日交易資訊×籌碼 數量對齊與股票清單更新引擎(批390)
====================================================================
操作員令(批390):「台股每日交易資訊及籌碼最後要對齊數量,作為更新股票清單,及核對分別數量一致;
輸出資料都採 parquet 增量擷取、DuckDB 管理」。
機制(Zero-Hydra:只讀正主表,不另抓;鍵律=價表 ticker(1101.TW/.TWO 批307)vs 籌碼 (code,market)→ tw_listings.yf_ticker
      對映,無冊=code+市場後綴推定):
  ① check  逐日核對(最近 N 個交易日;交易日曆=價表實際日期):價表票數 px_n vs 籌碼票數 chip_n(tw_chip_inst ∪ tw_chip_margin)
           → both/px_only/chip_only → 每日判定 ALIGNED(兩側票集合相等)/PARTIAL(交集≥90%)/MISALIGNED;最新日列不一致清單;
           籌碼最新日落後價表=誠實 MISALIGNED 並指路 via-chip run(ENG056)→ VIA_Reports/vdf/universe/ALIGN_latest.json
  ② update 股票清單=基準日(價表∪籌碼)∩ tw_listings(缺冊=價表∪籌碼全員)→ tw_universe(asof_date,ticker,code,market,name,
           in_prices,in_chips,aligned,updated_at);--apply 才寫:DuckDB anti-join 只增(鍵 asof_date,ticker)+ parquet 增量
           (output_hub/mega/tw_universe_<ts>.parquet 只含本次新增列;0 新增=不落檔);預設 dry-run 只印
           基準日律(批393 工作站實錄:最新價日 2026-09-07 只 399 票、籌碼 0,曾以此建清單 399 列=殘缺):預設=最新「雙側齊日」
           (價表票數 ≥ 窗內最大 60% 且籌碼有票且判定 ALIGNED/PARTIAL 的最新日);最新價日 價未齊/籌碼缺=誠實 YELLOW 改以雙側齊日為基準並印修法;
           --asof YYYY-MM-DD 指定基準日;--allow-latest 強制最新價日;status 標殘缺快照(列數 < 最大快照 60%)並報現役基準日 current_asof
  ③ status 上次 ALIGN_latest 摘要 + tw_universe 表現況
紀律:只增不減;正本零觸碰(不改價表/籌碼表);誠實三態(GREEN/YELLOW/RED;庫缺/表缺不假綠);零網路;尾版律;
      讓庫律(批391 工作站實錄:日更鏈/回補持單寫者鎖 → update --apply 曾 IOException traceback):開庫短等重試 6×3s,逾額誠實
      [FAIL] 庫忙 rc3 印修法(等日更鏈/回補跑完再 update --apply;check 唯讀)不再 traceback;持鎖者解析(批393:IOException 內 PID n →
      命令列 → 引擎名+動詞,印一次 [庫忙] 持鎖者;指路 via-bg 背景引擎進程唯讀一覽,絕不 Stop-Process;實錄:via-status 開的是同步頁不是進程表)。
用法:python3 VDF_ENG081_UniverseAlign_v0100.py check [--days N] [--db PATH] [--json]
      | update [--apply] [--asof YYYY-MM-DD] [--allow-latest] [--db PATH] [--json] | status [--db PATH] | --selftest
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
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
MEGA = VIA / "functional modules" / "VDF" / "output_hub" / "mega"
DB_TW = MEGA / "vdf_tw_market.duckdb"
REPORTS = VIA / "VIA_Reports" / "vdf" / "universe"
LOG = VIA / "logs" / "vdf_universe_align.log"
PX = "tw_daily_prices"
CHIPS = ("tw_chip_inst", "tw_chip_margin")
UNIVERSE = "tw_universe"
VERBS = ("check", "update", "status")
DAYS_DEFAULT = 20
PARTIAL_FLOOR = 0.90
PX_FULL_FLOOR = 0.60   # 批393:價表票數 ≥ 窗內最大 60% 才算「價齊日」(日更未齊/來源缺=殘缺日,不作清單基準)
_PID_RX = re.compile(r"PID\s*(\d+)")
_ENGINE_RX = re.compile(r"((?:VDF|VRN|VAP|CGC|SUP)_(?:ENG|MDL)\d{3}_[A-Za-z0-9]+(?:_v\d{4})?\.py|via_boot_update\.(?:ps1|sh)|VIA\.ps1|VIA_SYSTEM_MANAGER_v\d{4}\.py)")


# ---------------------------------------------------------------- 基礎
def _ts() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def _now() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def log_event(kind: str, msg: str, **kw) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": _now(), "kind": kind, "msg": msg, **kw}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    os.replace(tmp, p)


def _duckdb():
    try:
        import duckdb
        return duckdb
    except Exception:
        return None


def _proc_cmdline(pid: int) -> str:
    """持鎖進程命令列(唯讀;Windows=Get-CimInstance Win32_Process;POSIX=ps;失敗=空字串;零第三方依賴;絕不動進程)"""
    import subprocess
    try:
        if os.name == "nt":
            cmd = ["powershell", "-NoProfile", "-Command", f"(Get-CimInstance Win32_Process -Filter 'ProcessId={int(pid)}').CommandLine"]
        else:
            cmd = ["ps", "-o", "args=", "-p", str(int(pid))]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout
        return " ".join(out.split())[:240]
    except Exception:
        return ""


def _holder_label(cmdline: str) -> str:
    """命令列 → 引擎名(+動詞):…VDF_ENG064_HistoryBackfill_v0102.py run --resume → 'VDF_ENG064_HistoryBackfill_v0102.py run'"""
    if not cmdline:
        return ""
    m = _ENGINE_RX.search(cmdline)
    if not m:
        return cmdline[:80]
    tail = cmdline[m.end():].strip().strip('"').split()
    verb = tail[0] if tail and not tail[0].startswith("-") else ""
    return (m.group(1) + (" " + verb if verb else "")).strip()


def _holder_of(msg: str) -> tuple:
    """IOException 文字 → (pid, 引擎標籤);無 PID=(None, '')(批393 工作站實錄:File is already open in python.exe (PID 7396))"""
    m = _PID_RX.search(msg or "")
    if not m:
        return (None, "")
    pid = int(m.group(1))
    return (pid, _holder_label(_proc_cmdline(pid)))


def _connect(db: Path, read_only: bool, retries: int = 6, wait: float = 3.0, sleep_fn=None, resolver=None):
    """讓庫律(批391;ENG064/ENG079 同律):DuckDB 單寫者鎖=短等重試;逾額誠實 RuntimeError(主程式印 [FAIL] rc3,零 traceback)
    批393:持鎖者解析(IOException 內 PID n → 命令列 → 引擎名)印一次 [庫忙] 持鎖者;[FAIL] 句指路 via-bg(唯讀一覽;絕不 Stop-Process)"""
    import time
    duckdb = _duckdb()
    last = ""
    holder = None
    for i in range(retries):
        try:
            return duckdb.connect(str(db), read_only=read_only)
        except duckdb.IOException as exc:
            last = str(exc)
            low = last.lower()
            if not any(k in low for k in ("lock", "already open", "being used", "另一個程序", "cannot open file")):
                raise
            if holder is None:
                holder = (resolver or _holder_of)(last)
                if holder[0]:
                    print(f"  [庫忙] 持鎖者 PID {holder[0]}:{holder[1] or '(命令列不可讀)'}(等其跑完;絕不 Stop-Process;via-bg 看全部背景引擎)", flush=True)
            print(f"  [庫忙] {i + 1}/{retries}:{last.splitlines()[0][:90]} → 等 {wait}s", flush=True)
            (sleep_fn or time.sleep)(wait)
    who = f"持鎖者 PID {holder[0]}:{holder[1] or '?'};" if holder and holder[0] else ""
    raise RuntimeError(f"庫忙逾 {retries}×{wait}s({who}日更鏈/歷史回補持單寫者鎖;等其跑完再 via-align {'update --apply' if not read_only else 'check'};via-bg 看背景引擎進程):{last.splitlines()[0][:120]}")


def _q(s: str) -> str:
    return "'" + str(s).replace("'", "''") + "'"


def _qi(c) -> str:
    """欄名引號;缺欄=NULL(f-string 內不放反斜線=3.11 相容)"""
    return ('"' + str(c).replace('"', '""') + '"') if c else "NULL"


def _tables(con) -> set:
    return {r[0] for r in con.execute("SHOW TABLES").fetchall()}


def _cols(con, t: str) -> dict:
    return {r[0].lower(): r[0] for r in con.execute(f'DESCRIBE "{t}"').fetchall()}


# ---------------------------------------------------------------- 對映(籌碼 code,market → 價表 ticker)
def listings_map(con) -> dict:
    """code → (yf_ticker, name, market);tw_listings 冊優先(批307 鍵律);缺冊=空"""
    m = {}
    if "tw_listings" not in _tables(con):
        return m
    cols = _cols(con, "tw_listings")
    if "code" not in cols:
        return m
    yf = cols.get("yf_ticker")
    sel = f'SELECT {_qi(cols["code"])}, {_qi(yf)}, {_qi(cols.get("name"))}, {_qi(cols.get("market"))} FROM tw_listings'
    for code, y, name, mk in con.execute(sel).fetchall():
        code = str(code).strip()
        mk = str(mk or "").upper()
        y = str(y) if y else (code + (".TW" if mk == "TWSE" else ".TWO" if mk == "TPEX" else ""))
        m[code] = (y, str(name or ""), mk)
    return m


def chip_ticker(code: str, market: str, lst: dict) -> str:
    code = str(code).strip()
    if code in lst and lst[code][0]:
        return lst[code][0]
    mk = str(market or "").upper()
    return code + (".TW" if mk == "TWSE" else ".TWO" if mk in ("TPEX", "OTC") else ".TW")


def _daily_sets(con, have: set, lst: dict, days: int) -> tuple:
    """最近 N 個交易日(交易日曆=價表)→ (px_dates 新→舊, 日→價表票集合, 日→籌碼票集合(inst∪margin 經冊對映), 籌碼最新日)"""
    chips = [t for t in CHIPS if t in have]
    px_dates = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(date AS VARCHAR) d FROM {PX} WHERE ticker <> '_NOOP_' ORDER BY d DESC LIMIT {int(days)}").fetchall()]
    chip_max = None
    chip_sets: dict = {}
    for t in chips:
        cols = _cols(con, t)
        dc, cc, mc = cols.get("date"), cols.get("code"), cols.get("market")
        if not (dc and cc):
            continue
        mx = con.execute(f'SELECT max(CAST("{dc}" AS VARCHAR)) FROM "{t}"').fetchone()[0]
        if mx and (chip_max is None or str(mx) > chip_max):
            chip_max = str(mx)[:10]
        if px_dates:
            rows = con.execute(f'SELECT CAST({_qi(dc)} AS VARCHAR), {_qi(cc)}, {_qi(mc)} FROM {_qi(t)} WHERE CAST({_qi(dc)} AS VARCHAR) >= {_q(min(px_dates))}').fetchall()
            for d, code, mk in rows:
                chip_sets.setdefault(str(d)[:10], set()).add(chip_ticker(code, mk, lst))
    px_sets: dict = {}
    if px_dates:
        for d, tk in con.execute(f"SELECT CAST(date AS VARCHAR), ticker FROM {PX} WHERE ticker <> '_NOOP_' AND CAST(date AS VARCHAR) >= {_q(min(px_dates))}").fetchall():
            px_sets.setdefault(str(d)[:10], set()).add(str(tk))
    return px_dates, px_sets, chip_sets, chip_max


def _verdict(p: set, c: set) -> str:
    if not c:
        return "MISALIGNED"
    if p == c:
        return "ALIGNED"
    if len(p & c) >= PARTIAL_FLOOR * max(len(p), len(c)):
        return "PARTIAL"
    return "MISALIGNED"


def _pick_asof(px_dates: list, px_sets: dict, chip_sets: dict, px_top: int, asof: str | None = None, allow_latest: bool = False) -> dict:
    """基準日律(批393):--asof 指定 > --allow-latest 最新價日 > 最新雙側齊日(價 ≥ 窗內最大 60%、籌碼有票、ALIGNED/PARTIAL)
    > 最新雙側有票日 > 最新價日(籌碼全缺);非雙側齊日一律 YELLOW 並印修法(誠實三態;殘缺日不假綠)"""
    def row(d):
        p, c = px_sets.get(d, set()), chip_sets.get(d, set())
        return len(p), len(c), _verdict(p, c), len(p) >= PX_FULL_FLOOR * px_top
    d_latest = px_dates[0]
    n0, m0, v0, full0 = row(d_latest)
    if asof:
        if asof not in px_dates:
            return {"asof": None, "lamp": "RED", "rule": "--asof", "why": "", "error": f"基準日 {asof} 不在價表交易日(窗內 {px_dates[-1]}…{d_latest} 共 {len(px_dates)} 日)"}
        n, m, v, full = row(asof)
        good = bool(m) and v != "MISALIGNED" and full
        return {"asof": asof, "lamp": "GREEN" if good else "YELLOW", "rule": "--asof 指定",
                "why": "" if good else f"指定基準日 {asof} 價 {n} 籌碼 {m} {v}{'' if full else '(價未齊)'}=非雙側齊日(操作員指定,照辦)"}
    good0 = bool(m0) and v0 != "MISALIGNED" and full0
    if allow_latest or good0:
        return {"asof": d_latest, "lamp": "GREEN" if good0 else "YELLOW", "rule": "最新價日" if good0 else "--allow-latest 強制最新價日",
                "why": "" if good0 else f"最新價日 {d_latest} 價 {n0} 籌碼 {m0} {v0}{'' if full0 else '(價未齊)'}=非雙側齊日(--allow-latest 強制)"}
    flaw = ("(價未齊<窗內最大 " + str(px_top) + " 之 60%)" if not full0 else "") + ("(籌碼缺/落後)" if not m0 else "")
    for d in px_dates:
        n, m, v, full = row(d)
        if m and v != "MISALIGNED" and full:
            return {"asof": d, "lamp": "YELLOW", "rule": "最新雙側齊日",
                    "why": f"最新價日 {d_latest} 價 {n0} 籌碼 {m0}{flaw}=殘缺日不作基準 → 基準日改最新雙側齊日 {d}(價 {n} 籌碼 {m} {v});--asof 指定;--allow-latest 強制最新價日"}
    for d in px_dates:
        n, m, v, full = row(d)
        if m and n:
            return {"asof": d, "lamp": "YELLOW", "rule": "最新雙側有票日(窗內無齊日)",
                    "why": f"窗內無雙側齊日 → 基準日改最新雙側有票日 {d}(價 {n} 籌碼 {m} {v});先 via-chip run(ENG056)補籌碼再 update"}
    return {"asof": d_latest, "lamp": "YELLOW", "rule": "最新價日(窗內籌碼全缺)",
            "why": f"窗內籌碼全缺 → 清單只含價表側(asof {d_latest} 價 {n0});先 via-chip run(ENG056)補籌碼再 update"}


# ---------------------------------------------------------------- ① check
def check(db: Path = DB_TW, days: int = DAYS_DEFAULT, reports: Path = REPORTS, do_print: bool = True) -> dict:
    rep = {"schema": "VIA.UniverseAlign.v1", "ts": _now(), "db": str(db), "days": days, "verdict": "GREEN", "note": "", "dates": [], "mismatch": {"px_only": [], "chip_only": []},
           "latest": {}, "summary": {}}

    def say(s):
        if do_print:
            print(s, flush=True)

    duckdb = _duckdb()
    if duckdb is None:
        rep["verdict"], rep["note"] = "RED", "duckdb 缺(於 via_vdf_312 境跑:via-align;或 via-py vdf)"
        say(f"RED     {rep['note']}")
        _finish(rep, reports, "ALIGN")
        return rep
    if not db.exists():
        rep["verdict"], rep["note"] = "RED", f"庫缺 {db}(先 via-vdfdb run --apply / ENG054)"
        say(f"RED     {rep['note']}")
        _finish(rep, reports, "ALIGN")
        return rep
    con = _connect(db, read_only=True)
    try:
        have = _tables(con)
        if PX not in have:
            rep["verdict"], rep["note"] = "RED", f"價表缺 {PX}"
            say(f"RED     {rep['note']}")
            _finish(rep, reports, "ALIGN")
            return rep
        chips = [t for t in CHIPS if t in have]
        if not chips:
            rep["verdict"], rep["note"] = "RED", f"籌碼表缺 {CHIPS}(先 via-chip run=ENG056)"
            say(f"RED     {rep['note']}")
        lst = listings_map(con)
        rep["summary"]["listings"] = len(lst)
        px_dates, px_sets, chip_sets, chip_max = _daily_sets(con, have, lst, days)
        rep["summary"]["px_max"] = px_dates[0] if px_dates else None
        rep["summary"]["chip_max"] = chip_max
        px_top = max((len(px_sets.get(d, set())) for d in px_dates), default=0)
        rep["summary"]["px_top"] = px_top
        n_al = n_part = n_mis = 0
        for d in px_dates:
            p, c = px_sets.get(d, set()), chip_sets.get(d, set())
            both = p & c
            v = _verdict(p, c)
            n_al += v == "ALIGNED"
            n_part += v == "PARTIAL"
            n_mis += v == "MISALIGNED"
            rep["dates"].append({"date": d, "px_n": len(p), "chip_n": len(c), "both": len(both), "px_only": len(p - c), "chip_only": len(c - p), "verdict": v,
                                 "px_full": len(p) >= PX_FULL_FLOOR * px_top})
        if px_dates:
            d0 = px_dates[0]
            p, c = px_sets.get(d0, set()), chip_sets.get(d0, set())
            rep["latest"] = {"date": d0, "px_n": len(p), "chip_n": len(c), "both": len(p & c), "verdict": rep["dates"][0]["verdict"]}
            rep["mismatch"] = {"px_only": sorted(p - c)[:200], "chip_only": sorted(c - p)[:200], "px_only_n": len(p - c), "chip_only_n": len(c - p)}
        rep["summary"].update({"dates": len(px_dates), "aligned": n_al, "partial": n_part, "misaligned": n_mis})
        if rep["verdict"] != "RED":
            if not px_dates:
                rep["verdict"], rep["note"] = "RED", "價表無交易日"
            elif chip_max and rep["summary"]["px_max"] and chip_max < rep["summary"]["px_max"]:
                lag = (_dt.date.fromisoformat(rep["summary"]["px_max"]) - _dt.date.fromisoformat(chip_max)).days
                rep["verdict"] = "MISALIGNED"
                rep["note"] = f"籌碼最新日 {chip_max} 落後價表 {rep['summary']['px_max']}({lag} 日)→ via-chip run(ENG056 籌碼增量;交易日曆=價表,回補新增日後需重跑)後重核"
            elif n_mis:
                rep["verdict"] = "MISALIGNED"
                rep["note"] = f"{n_mis}/{len(px_dates)} 日票集合不一致(最新日 只有價 {rep['mismatch'].get('px_only_n', 0)} · 只有籌碼 {rep['mismatch'].get('chip_only_n', 0)})→ 差集見 mismatch;更新清單 via-align update --apply"
            elif n_part:
                rep["verdict"] = "PARTIAL"
                rep["note"] = f"{n_part}/{len(px_dates)} 日交集 ≥ {int(PARTIAL_FLOOR * 100)}% 但未全等(最新日 只有價 {rep['mismatch'].get('px_only_n', 0)} · 只有籌碼 {rep['mismatch'].get('chip_only_n', 0)})"
            else:
                rep["verdict"] = "ALIGNED"
                rep["note"] = f"{len(px_dates)} 日票集合全等(最新日 {rep['latest'].get('px_n', 0)} 票)"
            if rep["dates"] and not rep["dates"][0]["px_full"]:
                if rep["verdict"] == "ALIGNED":
                    rep["verdict"] = "PARTIAL"
                rep["note"] = f"最新價日 {rep['dates'][0]['date']} 價 {rep['dates'][0]['px_n']} < 窗內最大 {px_top} 之 60%=日更未齊(via-price run=ENG054 增量補齊;清單基準日自動改雙側齊日)· " + rep["note"]
    finally:
        con.close()
    _finish(rep, reports, "ALIGN")
    if do_print:
        lamp = {"ALIGNED": "GREEN", "PARTIAL": "YELLOW", "MISALIGNED": "YELLOW"}.get(rep["verdict"], rep["verdict"])
        say(f"[via-align check] {rep['verdict']}({lamp})· {rep['note']}")
        for d in rep["dates"][:10]:
            say(f"  {d['date']}  價 {d['px_n']:>5}  籌碼 {d['chip_n']:>5}  皆有 {d['both']:>5}  只價 {d['px_only']:>4}  只籌 {d['chip_only']:>4}  {d['verdict']}{'' if d.get('px_full', True) else '  價未齊'}")
        if len(rep["dates"]) > 10:
            say(f"  … 其餘 {len(rep['dates']) - 10} 日見 ALIGN_latest.json")
        say(f"  存證 {reports / 'ALIGN_latest.json'}")
    return rep


# ---------------------------------------------------------------- ② update
def update(db: Path = DB_TW, apply: bool = False, reports: Path = REPORTS, mega: Path | None = None, do_print: bool = True, asof: str | None = None, allow_latest: bool = False) -> dict:
    rep = {"schema": "VIA.UniverseUpdate.v1", "ts": _now(), "db": str(db), "mode": "apply" if apply else "dry-run", "verdict": "GREEN", "note": "", "asof": None, "latest_px_date": None, "asof_rule": "", "rows": 0, "new": 0, "parquet": "", "summary": {}}

    def say(s):
        if do_print:
            print(s, flush=True)

    duckdb = _duckdb()
    if duckdb is None or not db.exists():
        rep["verdict"], rep["note"] = "RED", ("duckdb 缺(via_vdf_312 境)" if duckdb is None else f"庫缺 {db}")
        say(f"RED     {rep['note']}")
        _finish(rep, reports, "UNIVERSE")
        return rep
    con = _connect(db, read_only=not apply)
    try:
        have = _tables(con)
        if PX not in have:
            rep["verdict"], rep["note"] = "RED", f"價表缺 {PX}"
            say(f"RED     {rep['note']}")
            _finish(rep, reports, "UNIVERSE")
            return rep
        lst = listings_map(con)
        days = DAYS_DEFAULT
        if asof:   # 指定基準日=窗擴到含該日(上限 3650 交易日)
            k = con.execute(f"SELECT count(DISTINCT CAST(date AS VARCHAR)) FROM {PX} WHERE ticker <> '_NOOP_' AND CAST(date AS VARCHAR) >= {_q(str(asof)[:10])}").fetchone()[0]
            days = max(DAYS_DEFAULT, min(3650, int(k or 0) + 1))
        px_dates, px_sets, chip_sets, chip_max = _daily_sets(con, have, lst, days)
        if not px_dates:
            rep["verdict"], rep["note"] = "RED", "價表空"
            say(f"RED     {rep['note']}")
            _finish(rep, reports, "UNIVERSE")
            return rep
        px_top = max(len(px_sets.get(d, set())) for d in px_dates)
        pick = _pick_asof(px_dates, px_sets, chip_sets, px_top, asof=str(asof)[:10] if asof else None, allow_latest=allow_latest)
        rep.update({"latest_px_date": px_dates[0], "asof_rule": pick["rule"], "px_top": px_top, "chip_max": chip_max})
        if pick.get("error"):
            rep["verdict"], rep["note"] = "RED", pick["error"]
            say(f"RED     {rep['note']}")
            _finish(rep, reports, "UNIVERSE")
            return rep
        d0 = pick["asof"]
        px = set(px_sets.get(d0, set()))
        chips = set(chip_sets.get(d0, set()))
        by_yf = {v[0]: (k, v[1], v[2]) for k, v in lst.items()}
        union = px | chips
        rows = []
        for tk in sorted(union):
            code, name, mk = by_yf.get(tk, (tk.split(".")[0], "", "TWSE" if tk.endswith(".TW") else "TPEX" if tk.endswith(".TWO") else ""))
            if lst and tk not in by_yf:
                continue   # 有冊=∩ tw_listings(下市/非股票碼不入清單)
            rows.append((d0, tk, code, mk, name, tk in px, tk in chips, tk in px and tk in chips, rep["ts"]))
        rep.update({"asof": d0, "rows": len(rows), "summary": {"px": len(px), "chips": len(chips), "union": len(union), "listed": len(rows), "aligned": sum(1 for r in rows if r[7]), "listings": len(lst)}})
        if not rows:
            rep["verdict"], rep["note"] = "RED", "最新日無票(價表/籌碼皆空)"
            say(f"RED     {rep['note']}")
            _finish(rep, reports, "UNIVERSE")
            return rep
        con.execute("CREATE OR REPLACE TEMP TABLE _uni(asof_date VARCHAR, ticker VARCHAR, code VARCHAR, market VARCHAR, name VARCHAR, in_prices BOOLEAN, in_chips BOOLEAN, aligned BOOLEAN, updated_at VARCHAR)")
        con.executemany("INSERT INTO _uni VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
        if UNIVERSE in have:
            n_new = con.execute(f"SELECT count(*) FROM _uni s WHERE NOT EXISTS (SELECT 1 FROM {UNIVERSE} t WHERE t.asof_date = s.asof_date AND t.ticker = s.ticker)").fetchone()[0]
        else:
            n_new = len(rows)
        rep["new"] = n_new
        if apply:
            if UNIVERSE not in have:
                con.execute(f"CREATE TABLE {UNIVERSE} AS SELECT * FROM _uni WHERE 1=0")
            con.execute(f"CREATE OR REPLACE TEMP TABLE _uni_new AS SELECT s.* FROM _uni s WHERE NOT EXISTS (SELECT 1 FROM {UNIVERSE} t WHERE t.asof_date = s.asof_date AND t.ticker = s.ticker)")
            if n_new:
                con.execute(f"INSERT INTO {UNIVERSE} SELECT * FROM _uni_new")
                mega = mega or MEGA
                mega.mkdir(parents=True, exist_ok=True)
                pq = mega / f"tw_universe_{_ts()}.parquet"
                try:
                    con.execute(f"COPY _uni_new TO {_q(str(pq).replace(chr(92), '/'))} (FORMAT PARQUET)")
                    rep["parquet"] = str(pq)
                except Exception as exc:
                    rep["note"] += f";parquet 落檔失敗 {str(exc)[:60]}"
            rep["verdict"] = "GREEN"
            rep["note"] = (f"tw_universe +{n_new} 列(asof {d0};anti-join 只增;parquet 增量 {Path(rep['parquet']).name if rep['parquet'] else '0 新增=不落檔'})" + rep["note"]) if True else ""
        else:
            rep["verdict"] = "GREEN"
            rep["note"] = f"dry-run:清單 {len(rows)} 票(asof {d0};價 {len(px)} ∪ 籌碼 {len(chips)} ∩ 冊 {len(lst) or '無冊'})· 計畫新增 {n_new}(--apply 才寫)"
        if rep["summary"]["aligned"] < rep["summary"]["listed"]:
            rep["note"] += f" · 未對齊 {rep['summary']['listed'] - rep['summary']['aligned']} 票(in_prices/in_chips 單側)"
        if pick["lamp"] == "YELLOW":   # 批393 基準日律:非雙側齊日=誠實 YELLOW 印修法(仍可寫;只增不減)
            rep["verdict"] = "YELLOW"
            rep["note"] += " · " + pick["why"]
    finally:
        con.close()
    _finish(rep, reports, "UNIVERSE")
    say(f"[via-align update] {rep['verdict']} · {rep['note']} · 存證 {reports / 'UNIVERSE_latest.json'}")
    return rep


def status(db: Path = DB_TW, reports: Path = REPORTS, do_print: bool = True) -> dict:
    out = {"align": None, "universe": None}
    p = reports / "ALIGN_latest.json"
    if p.exists():
        try:
            a = json.loads(p.read_text(encoding="utf-8"))
            out["align"] = {"ts": a.get("ts"), "verdict": a.get("verdict"), "note": a.get("note"), "latest": a.get("latest")}
        except Exception:
            pass
    duckdb = _duckdb()
    if duckdb and db.exists():
        try:
            con = _connect(db, read_only=True, retries=2, wait=1.0)
            try:
                if UNIVERSE in _tables(con):
                    n, mx, k = con.execute(f"SELECT count(*), max(asof_date), count(DISTINCT asof_date) FROM {UNIVERSE}").fetchone()
                    snaps = con.execute(f"SELECT asof_date, count(*), sum(CASE WHEN aligned THEN 1 ELSE 0 END) FROM {UNIVERSE} GROUP BY asof_date ORDER BY asof_date DESC").fetchall()
                    top = max((int(x[1]) for x in snaps), default=0)
                    det = [{"asof": str(x[0]), "rows": int(x[1]), "aligned": int(x[2] or 0), "state": "OK" if int(x[1]) >= PX_FULL_FLOOR * top else "PARTIAL(殘缺日快照;列數<最大快照 60%;批393)"} for x in snaps]
                    out["universe"] = {"rows": n, "asof_max": mx, "snapshots": k, "detail": det[:12], "current_asof": next((d["asof"] for d in det if d["state"] == "OK"), None)}
            finally:
                con.close()
        except Exception:
            pass
    if do_print:
        a = out["align"]
        print(f"[via-align status] 對齊 {a['verdict'] + ' ' + str(a['note'])[:100] if a else '未跑(via-align check)'} · 清單 {out['universe'] or '未建(via-align update --apply)'}")
    return out


def _finish(rep: dict, reports: Path, stem: str) -> None:
    try:
        _write_json(reports / f"{stem}_{_ts()}.json", rep)
        _write_json(reports / f"{stem}_latest.json", rep)
    except Exception as exc:
        rep["note"] += f";存證失敗 {str(exc)[:60]}"
    log_event(stem, rep.get("verdict", "?"), note=rep.get("note", "")[:200])


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    duckdb = _duckdb()
    if duckdb is None:
        print("  [FAIL] duckdb 缺=本引擎不可測(於 via_vdf_312 境跑)")
        return 1
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        db, reports, mega = root / "vdf_tw_market.duckdb", root / "reports", root / "mega"
        c = duckdb.connect(str(db))
        c.execute("CREATE TABLE tw_listings(code VARCHAR, name VARCHAR, market VARCHAR, yf_ticker VARCHAR)")
        c.executemany("INSERT INTO tw_listings VALUES (?, ?, ?, ?)", [("2330", "台積電", "TWSE", "2330.TW"), ("2454", "聯發科", "TWSE", "2454.TW"), ("6488", "環球晶", "TPEX", "6488.TWO"), ("2317", "鴻海", "TWSE", "2317.TW")])
        c.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, close DOUBLE)")
        c.executemany("INSERT INTO tw_daily_prices VALUES (?, ?, ?)", [
            ("2026-09-01", "2330.TW", 1.0), ("2026-09-01", "2454.TW", 1.0), ("2026-09-01", "6488.TWO", 1.0),
            ("2026-09-02", "2330.TW", 1.0), ("2026-09-02", "2454.TW", 1.0), ("2026-09-02", "6488.TWO", 1.0), ("2026-09-02", "2317.TW", 1.0),
            ("2026-09-03", "2330.TW", 1.0), ("2026-09-03", "2454.TW", 1.0), ("2026-09-03", "6488.TWO", 1.0), ("2026-09-03", "9999.TW", 1.0)])
        c.execute("CREATE TABLE tw_chip_inst(date DATE, code VARCHAR, market VARCHAR, foreign_net DOUBLE)")
        c.executemany("INSERT INTO tw_chip_inst VALUES (?, ?, ?, ?)", [
            ("2026-09-01", "2330", "TWSE", 1.0), ("2026-09-01", "2454", "TWSE", 1.0), ("2026-09-01", "6488", "TPEX", 1.0),
            ("2026-09-02", "2330", "TWSE", 1.0), ("2026-09-02", "2454", "TWSE", 1.0), ("2026-09-02", "6488", "TPEX", 1.0), ("2026-09-02", "2317", "TWSE", 1.0),
            ("2026-09-03", "2330", "TWSE", 1.0), ("2026-09-03", "2454", "TWSE", 1.0)])
        c.execute("CREATE TABLE tw_chip_margin(date DATE, code VARCHAR, market VARCHAR, margin_bal DOUBLE)")
        c.executemany("INSERT INTO tw_chip_margin VALUES (?, ?, ?, ?)", [("2026-09-03", "6488", "TPEX", 1.0), ("2026-09-03", "2317", "TWSE", 1.0)])
        c.close()
        r = check(db, days=5, reports=reports, do_print=False)
        by = {d["date"]: d for d in r["dates"]}
        chk("① check 逐日核對(交易日曆=價表;籌碼 inst∪margin 經 tw_listings 對映 yahoo 票;01/02 全等 ALIGNED;03 價 9999 無籌碼、籌碼 2317 無價=MISALIGNED;差集清單;ALIGN_latest.json)",
            r["summary"]["dates"] == 3 and by["2026-09-01"]["verdict"] == "ALIGNED" and by["2026-09-02"]["verdict"] == "ALIGNED" and by["2026-09-02"]["px_n"] == 4
            and by["2026-09-03"]["verdict"] == "MISALIGNED" and by["2026-09-03"]["px_only"] == 1 and by["2026-09-03"]["chip_only"] == 1
            and r["mismatch"]["px_only"] == ["9999.TW"] and r["mismatch"]["chip_only"] == ["2317.TW"] and r["verdict"] == "MISALIGNED" and (reports / "ALIGN_latest.json").exists(),
            f"({r['verdict']};{[(d['date'], d['verdict'], d['px_n'], d['chip_n']) for d in r['dates']]})")
        u0 = update(db, apply=False, reports=reports, mega=mega, do_print=False, allow_latest=True)
        u1 = update(db, apply=True, reports=reports, mega=mega, do_print=False, allow_latest=True)
        c2 = duckdb.connect(str(db), read_only=True)
        rows = c2.execute(f"SELECT ticker, code, market, in_prices, in_chips, aligned FROM {UNIVERSE} ORDER BY ticker").fetchall()
        c2.close()
        pq = sorted(mega.glob("tw_universe_*.parquet"))
        chk("② update 股票清單(--allow-latest 最新日 價∪籌碼 ∩ 冊:9999 非冊不入;2317 只籌碼 in_prices=False;dry-run 零寫;--apply 建表 4 列 + parquet 增量 1 檔)",
            u0["mode"] == "dry-run" and u0["rows"] == 4 and u0["new"] == 4 and u1["new"] == 4 and len(rows) == 4
            and rows == [("2317.TW", "2317", "TWSE", False, True, False), ("2330.TW", "2330", "TWSE", True, True, True), ("2454.TW", "2454", "TWSE", True, True, True), ("6488.TWO", "6488", "TPEX", True, True, True)]
            and len(pq) == 1, f"(dry {u0['rows']}/{u0['new']};apply +{u1['new']};rows {rows};pq {len(pq)})")
        u2 = update(db, apply=True, reports=reports, mega=mega, do_print=False, allow_latest=True)
        chk("③ 重跑冪等(anti-join 0 新增;不落新 parquet)", u2["new"] == 0 and len(sorted(mega.glob("tw_universe_*.parquet"))) == 1 and (reports / "UNIVERSE_latest.json").exists(), f"(+{u2['new']})")
        st = status(db, reports=reports, do_print=False)
        chk("④ status(對齊摘要+清單現況+快照明細/現役基準日)", st["align"]["verdict"] == "MISALIGNED" and st["universe"]["rows"] == 4 and st["universe"]["snapshots"] == 1
            and st["universe"]["current_asof"] == "2026-09-03" and st["universe"]["detail"][0]["state"] == "OK")
        c3 = duckdb.connect(str(db))
        c3.execute("DELETE FROM tw_chip_inst WHERE CAST(date AS VARCHAR) = '2026-09-03'")
        c3.execute("DELETE FROM tw_chip_margin WHERE CAST(date AS VARCHAR) = '2026-09-03'")
        c3.close()
        r2 = check(db, days=5, reports=reports, do_print=False)
        chk("⑤ 籌碼落後價表=誠實 MISALIGNED 指路 via-chip run(ENG056)", r2["verdict"] == "MISALIGNED" and "落後" in r2["note"] and "via-chip" in r2["note"] and r2["summary"]["chip_max"] == "2026-09-02", f"({r2['note'][:80]})")
        u4 = update(db, apply=False, reports=reports, mega=mega, do_print=False)
        u5 = update(db, apply=False, reports=reports, mega=mega, do_print=False, allow_latest=True)
        u6 = update(db, apply=False, reports=reports, mega=mega, do_print=False, asof="2026-09-01")
        u7 = update(db, apply=False, reports=reports, mega=mega, do_print=False, asof="2026-12-31")
        c5 = duckdb.connect(str(db))
        c5.execute("INSERT INTO tw_daily_prices VALUES ('2026-09-04', '2330.TW', 1.0)")   # 殘缺日:只 1 票(<60% 窗內最大 4)
        c5.close()
        r4 = check(db, days=5, reports=reports, do_print=False)
        u8 = update(db, apply=False, reports=reports, mega=mega, do_print=False)
        chk("⑩ 基準日律(批393 實錄:最新價日只價無籌碼/價未齊=殘缺日不作清單基準 → 最新雙側齊日 09-02 YELLOW 印修法;check 標「價未齊」;--allow-latest 強制最新價日;--asof 指定;壞基準日 RED)",
            u4["asof"] == "2026-09-02" and u4["verdict"] == "YELLOW" and "基準日改" in u4["note"] and u4["latest_px_date"] == "2026-09-03" and u4["rows"] == 4
            and u5["asof"] == "2026-09-03" and u5["verdict"] == "YELLOW" and u6["asof"] == "2026-09-01" and u6["rows"] == 3 and u6["verdict"] == "GREEN" and u7["verdict"] == "RED"
            and r4["dates"][0]["date"] == "2026-09-04" and r4["dates"][0]["px_full"] is False and "日更未齊" in r4["note"] and u8["asof"] == "2026-09-02" and "價未齊" in u8["note"],
            f"(u4 {u4['asof']} {u4['verdict']};u5 {u5['asof']};u6 {u6['asof']}/{u6['rows']};u7 {u7['verdict']};r4 {r4['dates'][0]['px_n']}/{r4['summary'].get('px_top')} {r4['verdict']};u8 {u8['asof']})")
        miss = check(root / "no.duckdb", reports=reports, do_print=False)
        chk("⑥ 庫缺誠實 RED(不假綠)", miss["verdict"] == "RED")
        c4 = duckdb.connect(str(root / "nolist.duckdb"))
        c4.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, close DOUBLE)")
        c4.execute("INSERT INTO tw_daily_prices VALUES ('2026-09-03', '2330.TW', 1.0), ('2026-09-03', '6488.TWO', 1.0)")
        c4.execute("CREATE TABLE tw_chip_inst(date DATE, code VARCHAR, market VARCHAR, foreign_net DOUBLE)")
        c4.execute("INSERT INTO tw_chip_inst VALUES ('2026-09-03', '2330', 'TWSE', 1.0), ('2026-09-03', '6488', 'TPEX', 1.0)")
        c4.close()
        r3 = check(root / "nolist.duckdb", days=3, reports=reports, do_print=False)
        u3 = update(root / "nolist.duckdb", apply=False, reports=reports, mega=mega, do_print=False)
        chk("⑦ 無 tw_listings 冊=市場後綴推定(TWSE→.TW/TPEX→.TWO)仍 ALIGNED;清單=價∪籌碼全員", r3["verdict"] == "ALIGNED" and u3["rows"] == 2 and u3["summary"]["listings"] == 0, f"({r3['verdict']};{u3['rows']})")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 紀律宣告(只增不減/正本零觸碰/誠實三態/零網路/尾版律/Zero-Hydra/ACCEL-BRIDGE)",
        all(k in src for k in ("只增不減", "正本零觸碰", "誠實三態", "零網路", "尾版律", "Zero-Hydra", "ACCEL-BRIDGE")))
    # ⑨ 讓庫律(批391 工作站實錄:單寫者鎖 IOException):鎖兩次後放行=重試成功;永鎖=誠實 RuntimeError(主程式 rc3);非鎖 IOException 原樣拋
    calls = {"n": 0}
    real_connect = duckdb.connect

    def locked_twice(path, read_only=False):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise duckdb.IOException('IO Error: Cannot open file "x.duckdb": 程序無法存取檔案，因為檔案正由另一個程序使用。 File is already open in python.exe (PID 1)')
        return real_connect(path, read_only=read_only)

    def locked_forever(path, read_only=False):
        raise duckdb.IOException("IO Error: Could not set lock on file")

    def other_io(path, read_only=False):
        raise duckdb.IOException("IO Error: disk full")

    with tempfile.TemporaryDirectory() as td2:
        dbp = Path(td2) / "t.duckdb"
        real_connect(str(dbp)).close()
        duckdb.connect = locked_twice
        try:
            c_ok = _connect(dbp, read_only=True, retries=4, wait=0.0, sleep_fn=lambda s: None, resolver=lambda m: (None, ""))
            c_ok.close()
            ok_retry = calls["n"] == 3
            duckdb.connect = locked_forever
            try:
                _connect(dbp, read_only=False, retries=2, wait=0.0, sleep_fn=lambda s: None, resolver=lambda m: (None, ""))
                ok_forever = False
            except RuntimeError as exc:
                ok_forever = "庫忙逾" in str(exc) and "update --apply" in str(exc)
            duckdb.connect = other_io
            try:
                _connect(dbp, read_only=True, retries=2, wait=0.0, sleep_fn=lambda s: None, resolver=lambda m: (None, ""))
                ok_other = False
            except duckdb.IOException:
                ok_other = True
        finally:
            duckdb.connect = real_connect
    chk("⑨ 讓庫律(單寫者鎖 IOException 短等重試;鎖兩次後放行;永鎖=誠實 RuntimeError 指路等日更鏈/回補跑完;非鎖 IOException 原樣拋)", ok_retry and ok_forever and ok_other,
        f"(retry {calls['n']};forever {ok_forever};other {ok_other})")
    # ⑪ 持鎖者解析(批393 工作站實錄:File is already open in C:\Python313\python.exe (PID 7396);via-status 開的是同步頁不是進程表)
    lab = _holder_label(r'C:\Python313\python.exe "C:\Users\tonyk\Github\movies-dataset\VeritasIntelligenceAnalytics\functional modules\VDF\engine\VDF_ENG064_HistoryBackfill_v0102.py" run --resume')
    lab2 = _holder_label("powershell -NoProfile -ExecutionPolicy Bypass -File C:\\x\\supportive modules\\registry\\via_boot_update.ps1")
    lab3 = _holder_label("")
    pid_none = _holder_of("IO Error: Could not set lock on file")
    pid_hit = _PID_RX.search('IO Error: Cannot open file "x.duckdb": 程序無法存取檔案 File is already open in C:\\Python313\\python.exe (PID 7396)')

    def locked_pid(path, read_only=False):
        raise duckdb.IOException('IO Error: Cannot open file "x.duckdb": File is already open in C:\\Python313\\python.exe (PID 7396)')

    msg = ""
    with tempfile.TemporaryDirectory() as td3:
        dbp3 = Path(td3) / "t.duckdb"
        real_connect(str(dbp3)).close()
        duckdb.connect = locked_pid
        try:
            _connect(dbp3, read_only=True, retries=1, wait=0.0, sleep_fn=lambda s: None, resolver=lambda m: (7396, "VDF_ENG064_HistoryBackfill_v0102.py run"))
        except RuntimeError as exc:
            msg = str(exc)
        finally:
            duckdb.connect = real_connect
    chk("⑪ 持鎖者解析(IOException PID n → 命令列 → 引擎名+動詞;boot 鏈 ps1;空=空;無 PID=(None,''))+ [FAIL] 句含持鎖者 PID/引擎與 via-bg 指路(取代 via-status)",
        lab == "VDF_ENG064_HistoryBackfill_v0102.py run" and lab2 == "via_boot_update.ps1" and lab3 == "" and pid_none == (None, "") and pid_hit and pid_hit.group(1) == "7396"
        and "持鎖者 PID 7396" in msg and "VDF_ENG064" in msg and "via-bg" in msg and "via-status" not in msg, f"({lab};{lab2};{msg[:70]})")
    print(f"  [計] 十一檢 OK {11 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


# ---------------------------------------------------------------- CLI
def _arg(a: list, flag: str, default=None):
    if flag in a:
        i = a.index(flag)
        if i + 1 < len(a):
            return a[i + 1]
    return default


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 台股日交易×籌碼對齊與清單更新引擎(VDF_ENG081_UniverseAlign)· 十一檢自測(零網路;臨時庫)===")
        return selftest()
    verb = next((x for x in a if x in VERBS), "check")   # 動詞白名單
    db = Path(_arg(a, "--db", str(DB_TW)))
    as_json = "--json" in a
    try:
        if verb == "check":
            d = _arg(a, "--days", str(DAYS_DEFAULT))
            rep = check(db, days=max(1, min(3650, int(d))) if str(d).isdigit() else DAYS_DEFAULT, do_print=not as_json)
            if as_json:
                print(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
            return 0 if rep["verdict"] != "RED" else 2
        if verb == "update":
            asof = _arg(a, "--asof")
            if asof and not re.match(r"^\d{4}-\d{2}-\d{2}$", str(asof)):
                print(f"[FAIL] --asof 需 YYYY-MM-DD:{asof}")
                return 2
            rep = update(db, apply="--apply" in a, do_print=not as_json, asof=asof, allow_latest="--allow-latest" in a)
            if as_json:
                print(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
            return 0 if rep["verdict"] != "RED" else 2
        st = status(db, do_print=not as_json)
        if as_json:
            print(json.dumps(st, ensure_ascii=False, indent=1, default=str))
        return 0
    except RuntimeError as exc:
        print(f"[FAIL] {exc}")
        log_event("FAIL", str(exc)[:200])
        return 3
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    sys.exit(main())
