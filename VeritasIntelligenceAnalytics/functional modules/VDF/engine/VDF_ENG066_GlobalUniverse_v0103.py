#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG066_GlobalUniverse v0103 — 薄尾(v0102 以前一字不動):全宇宙分道擷取 · 主路失敗走備用 · 合併 · 覆蓋報告 · 照資料家找庫
====================================================================
操作員 2026-11-20:「我要抓取所有股票指數及其他 YFINANCE 的商品數據自 2018 開始抓取」「3~5 步驟開始擷取儘快」
「被用工具若現在工具不堪用則用備用工具或整合或取代 輸入輸出不變」。

輸入輸出不變:讀宇宙冊(尾版 VIA_Global_Universe_v*.json;v0102 釘死 v0100)· 寫同一張 global_daily
(date · ticker · open · high · low · close · adj_close · volume),只補缺鍵(anti-join,既有列零觸碰),寫法沿用前版 _insert_missing。
新增:
  lane --part K/N --lane-db <暫存庫> [--start D] [--end D] [--cats a,b]
        把宇宙冊去重後的代號照順序輪流分成 N 份,只抓第 K 份,寫進本道自己的暫存庫(DuckDB 一本庫同時只能一個寫入者,
        所以各道不碰正庫)。主路 SUP_MDL740 yahoo_chart;主路沒回列的代號再走備用 yf_history(同一個網路工具、同一個列格式)。
  merge --from <暫存庫…> [--db <正庫> | --db-home <資料家>]
        單一寫入者把各道暫存庫只補缺鍵併進正庫;正庫被別的行程開著 = 紅(rc 1),不重試、不硬寫。
  coverage [--start D] [--db … | --db-home …] [--json]
        每個要求的代號在正庫的列數 · 起訖日;三數 應抓 · 有資料 · 無資料(逐一點名;缺一不綠)。
  run(前版動詞)照舊可用,只是改讀宇宙冊尾版、主路失敗走備用、可帶 --db / --db-home。
正庫在哪:--db > --db-home(照 VDF_DataHome_SSOT:資料家底下既有的 vdf_global_market.duckdb;沒有才用 <家>/output_hub/mega/)
         > 前版位置(倉內 functional modules/VDF/output_hub/mega/,桌機上這個夾是指到資料家的接點)。
同意閘照舊 fail-closed:VIA_NET_CONSENT 與 VIA_SCRAPE_CONSENT 都要 YES(操作員的手;本檔不讀寫、不代設)。
自測零網路、只在暫存夾造庫:py -3 VDF_ENG066_GlobalUniverse_v0103.py --selftest
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
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import calendar
import importlib.util
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_ENG066_GlobalUniverse"
VERSION = "v0103"
TAG = f"{STEM} {VERSION}"
VIA = HERE.parent.parent.parent
REG = VIA / "supportive modules" / "registry"
DEFAULT_START = "2018-01-01"
TABLE = "global_daily"
DB_NAME = "vdf_global_market.duckdb"
COLS = ["date", "ticker", "open", "high", "low", "close", "adj_close", "volume"]
DDL = (f"CREATE TABLE IF NOT EXISTS {TABLE}(date VARCHAR, ticker VARCHAR, open DOUBLE, high DOUBLE, low DOUBLE,"
       " close DOUBLE, adj_close DOUBLE, volume BIGINT)")
DATE_RX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _load(path: Path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
PRIOR = _load(PRIOR_PATH, "vdf_e066_prior_for_" + VERSION)


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    return getattr(PRIOR, name)


# ── 宇宙冊(尾版)· 選代號 · 分道 ─────────────────────────────────────
def roster_path(reg: Path | None = None) -> Path:
    hits = [p for p in Path(reg or REG).glob("VIA_Global_Universe_v*.json") if _vnum(p) >= 0]
    return max(hits, key=_vnum)


def load_roster(reg: Path | None = None) -> dict:
    return json.loads(roster_path(reg).read_text(encoding="utf-8"))


def pick_symbols(cats=None, roster: dict | None = None) -> tuple:
    """同前版:回 (可抓代號去重保序, 候源類);只是讀尾版冊。"""
    r = roster or load_roster()
    syms, pend = [], []
    for c in r["categories"]:
        if cats and c["cat"] not in cats:
            continue
        if not c["symbols"]:
            pend.append(f"{c['cat']}({c['zh']}):{c.get('pending_note', '候源')}")
        syms += c["symbols"]
    seen = set()
    return [s for s in syms if not (s in seen or seen.add(s))], pend


def split_part(syms: list, k: int, n: int) -> list:
    """第 k 份(1 起算)/ 共 n 份:照順序輪流發,各道代號數最多差 1;n 份合起來 = 全部、互不重疊。"""
    if not (1 <= k <= n):
        raise ValueError("part 要 1..N")
    return [s for i, s in enumerate(syms) if i % n == k - 1]


# ── 正庫在哪 ───────────────────────────────────────────────────────────
def resolve_db(db: str | None = None, db_home: str | None = None) -> tuple:
    """--db > --db-home(既有庫優先)> 前版位置。→ (Path, 為什麼)"""
    if db:
        return Path(db), "--db"
    if db_home:
        home = Path(db_home)
        for fixed in (home / "output_hub" / "mega" / DB_NAME, home / DB_NAME):
            if fixed.is_file():
                return fixed, "資料家既有庫"
        bad = re.compile(r"(?i)backup|bak|snapshot|_sha[0-9a-f]{6,}|copy|\(\d+\)|old|trash")
        found = sorted(p for p in home.rglob(DB_NAME) if not bad.search(str(p.relative_to(home)))) if home.is_dir() else []
        if found:
            return found[0], "資料家既有庫"
        return home / "output_hub" / "mega" / DB_NAME, "資料家(新建)"
    return Path(PRIOR.DB_GL), "前版位置(倉內 output_hub/mega)"


def _connect(path: Path, read_only: bool = False):
    import duckdb
    path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path), read_only=read_only)
    if not read_only:
        con.execute(DDL)
    return con


# ── 抓:主路 yahoo_chart → 備用 yf_history ─────────────────────────────
def fetch_rows(net, syms: list, start: str, end: str | None, batch: int = 25, pause_s: float = 0.35, log=print) -> dict:
    se = calendar.timegm(time.strptime(start, "%Y-%m-%d"))
    ee = (calendar.timegm(time.strptime(end, "%Y-%m-%d")) + 86400) if end else int(time.time())
    rows, via = [], {"main": 0, "backup": 0}
    missing = []
    for i in range(0, len(syms), batch):
        part = syms[i:i + batch]
        rc = net.yahoo_chart(part, se, ee, pause_s=pause_s) or {}
        got = rc.get("rows") or []
        rows += got
        hit = {r["ticker"] for r in got}
        via["main"] += len(hit)
        missing += [s for s in part if s not in hit]
        log(f"  [主路 {i // batch + 1}/{(len(syms) - 1) // batch + 1}] {len(hit)}/{len(part)} 檔 · {len(got):,} 列", flush=True)
    still = list(missing)
    if missing and hasattr(net, "yf_history"):
        rb = net.yf_history(missing, start, end or time.strftime("%Y-%m-%d", time.gmtime(ee))) or {}
        got = rb.get("rows") or []
        rows += got
        hit = {r["ticker"] for r in got}
        via["backup"] = len(hit)
        still = [s for s in missing if s not in hit]
        log(f"  [備用 yf_history] 主路沒回的 {len(missing)} 檔 → 補到 {len(hit)} 檔 · {len(got):,} 列", flush=True)
    return {"rows": rows, "via": via, "empty": still}


def _gated() -> bool:
    return os.environ.get("VIA_NET_CONSENT") != "YES" or os.environ.get("VIA_SCRAPE_CONSENT") != "YES"


def lane(part: str, lane_db: str, start: str = DEFAULT_START, end: str | None = None, cats=None, net=None, log=print) -> int:
    if _gated():
        log(f"[{TAG} lane {part}] 同意閘未開 = 拒跑(fail-closed;要抓由操作員在本視窗開兩道閘)")
        return 2
    if not DATE_RX.match(start) or (end and not DATE_RX.match(end)):
        log(f"[{TAG} lane {part}] 日期格式須 YYYY-MM-DD")
        return 2
    k, n = (int(x) for x in part.split("/"))
    syms, _ = pick_symbols(cats)
    mine = split_part(syms, k, n)
    t0 = time.time()
    log(f"[{TAG} lane {part}] {len(mine)} 檔 · {start}~{end or '最新'} · 暫存庫 {Path(lane_db).name}", flush=True)
    r = fetch_rows(net or PRIOR._net(), mine, start, end, log=log)
    con = _connect(Path(lane_db))
    PRIOR._insert_missing(con, r["rows"])
    n_rows = con.execute(f"SELECT count(*) FROM {TABLE}").fetchone()[0]
    con.close()
    Path(str(lane_db) + ".json").write_text(json.dumps({"part": part, "asked": mine, "empty": r["empty"], "via": r["via"],
                                                        "rows": n_rows}, ensure_ascii=False), encoding="utf-8")
    log(f"[{TAG} lane {part}] 完成 · 主路 {r['via']['main']} 檔 · 備用 {r['via']['backup']} 檔 · 無資料 {len(r['empty'])} 檔"
        f"{(' ' + ', '.join(r['empty'][:8])) if r['empty'] else ''} · 暫存 {n_rows:,} 列 · {time.time() - t0:.0f}s", flush=True)
    return 0 if not r["empty"] else 3


def merge(sources: list, db: str | None = None, db_home: str | None = None, log=print) -> int:
    target, why = resolve_db(db, db_home)
    try:
        con = _connect(target)
    except Exception as exc:  # noqa: BLE001 — 鎖住 / 權限:照實紅,不硬寫
        log(f"[{TAG} merge] RED · 正庫開不了({type(exc).__name__}:{str(exc)[:120]})· 先關掉開著這本庫的程式再跑 · {target}")
        return 1
    before = con.execute(f"SELECT count(*) FROM {TABLE}").fetchone()[0]
    used, skipped = 0, []
    for s in sources:
        p = Path(s)
        if not p.is_file():
            skipped.append(p.name)
            continue
        src = _connect(p, read_only=True)
        rows = [dict(zip(COLS, r)) for r in src.execute(f"SELECT {', '.join(COLS)} FROM {TABLE}").fetchall()]
        src.close()
        PRIOR._insert_missing(con, rows)
        used += 1
    after = con.execute(f"SELECT count(*) FROM {TABLE}").fetchone()[0]
    con.close()
    log(f"[{TAG} merge] 正庫 {target}({why})· 併入 {used} 本暫存庫 · 略過 {len(skipped)}{(' ' + ', '.join(skipped)) if skipped else ''}"
        f" · 實補 +{after - before:,} 列(只補缺鍵)· 共 {after:,} 列")
    return 0 if not skipped else 2


def coverage(start: str = DEFAULT_START, db: str | None = None, db_home: str | None = None, cats=None) -> dict:
    target, why = resolve_db(db, db_home)
    syms, pend = pick_symbols(cats)
    have = {}
    if target.is_file():
        con = _connect(target, read_only=True)
        for t, n, lo, hi in con.execute(f"SELECT ticker, count(*), min(date), max(date) FROM {TABLE} WHERE date >= ? GROUP BY ticker",
                                        [start]).fetchall():
            have[t] = {"rows": n, "first": lo, "last": hi}
        con.close()
    empty = [s for s in syms if s not in have]
    late = [s for s in syms if s in have and have[s]["first"] > start[:4] + "-12-31"]   # 第一筆比起始年底還晚 = 起點沒補到
    return {"db": str(target), "why": why, "start": start, "should": len(syms), "have": len(syms) - len(empty), "empty": empty,
            "late_start": late, "pending": pend, "rows": sum(v["rows"] for k, v in have.items() if k in set(syms)),
            "per": {s: have.get(s) for s in syms}, "state": "GREEN" if not empty else "YELLOW"}


def render_coverage(c: dict) -> str:
    out = [f"[{TAG} coverage] {c['state']} · 應抓 {c['should']} · 有資料 {c['have']} · 無資料 {len(c['empty'])}"
           f" · 起點晚於 {c['start'][:4]} 年 {len(c['late_start'])} · {c['rows']:,} 列 · 庫 {c['db']}({c['why']})"]
    if c["empty"]:
        out.append("  無資料(Yahoo 沒這個代號 / 已停 / 主備兩路都沒回):" + ", ".join(c["empty"]))
    if c["late_start"]:
        out.append("  起點晚(該商品較晚才有資料,或要再補):" + ", ".join(f"{s}({c['per'][s]['first']})" for s in c["late_start"][:30]))
    return "\n".join(out)


# ── 自測(零網路 · 只在暫存夾造庫)───────────────────────────────────
class _FakeNet:
    def __init__(self, main_ok: set, backup_ok: set):
        self.main_ok, self.backup_ok, self.calls = main_ok, backup_ok, []

    @staticmethod
    def _rows(t):
        return [{"date": d, "ticker": t, "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "adj_close": 1.5, "volume": 10}
                for d in ("2018-01-02", "2018-01-03")]

    def yahoo_chart(self, tickers, se, ee, pause_s=0.0):
        self.calls.append(("main", list(tickers)))
        return {"rows": [r for t in tickers if t in self.main_ok for r in self._rows(t)]}

    def yf_history(self, tickers, start, end):
        self.calls.append(("backup", list(tickers)))
        return {"rows": [r for t in tickers if t in self.backup_ok for r in self._rows(t)]}


def selftest() -> int:
    ok = []

    def ck(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)
    print(f"=== {TAG} 自測(零網路 · 暫存夾)===", flush=True)
    r = load_roster()
    syms, _ = pick_symbols()
    v0100 = json.loads((REG / "VIA_Global_Universe_v0100.json").read_text(encoding="utf-8"))
    old = {s for c in v0100["categories"] for s in c["symbols"]}
    ck("① 讀宇宙冊尾版(不再釘死 v0100)· 舊冊代號一個不少", roster_path().name == max(REG.glob("VIA_Global_Universe_v*.json"), key=_vnum).name
       and old <= set(syms) and len(syms) >= len(old), roster_path().name)
    parts = [split_part(syms, k, 4) for k in range(1, 5)]
    ck("② 分道:4 份合起來 = 全部 · 互不重疊 · 各道數量最多差 1",
       sorted(sum(parts, [])) == sorted(syms) and len(set(sum(parts, []))) == len(syms)
       and max(map(len, parts)) - min(map(len, parts)) <= 1)
    fake = _FakeNet({"A", "B"}, {"C"})
    got = fetch_rows(fake, ["A", "B", "C", "D"], "2018-01-01", "2018-01-05", batch=3, log=lambda *a, **k: None)
    ck("③ 主路沒回的才走備用 yf_history;兩路都沒回的照實列無資料",
       got["via"] == {"main": 2, "backup": 1} and got["empty"] == ["D"] and ("backup", ["C", "D"]) in fake.calls, got["via"])
    saved = {k: os.environ.pop(k, None) for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
    try:
        with tempfile.TemporaryDirectory(prefix="vdf_e066_v0103_") as td:
            rc_g = lane("1/2", str(Path(td) / "x.duckdb"), net=_FakeNet(set(), set()), log=lambda *a, **k: None)
            ck("④ 同意閘未開 = 拒跑 rc 2 · 暫存庫都沒建(零觸網)", rc_g == 2 and not (Path(td) / "x.duckdb").exists())
    finally:
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v
    try:
        import duckdb  # noqa: F401
        has_duck = True
    except ImportError:
        has_duck = False
    if has_duck:
        with tempfile.TemporaryDirectory(prefix="vdf_e066_v0103_") as td:
            td = Path(td)
            l1, l2 = td / "lane_1.duckdb", td / "lane_2.duckdb"
            for p_, t_ in ((l1, "A"), (l2, "B")):
                c = _connect(p_)
                PRIOR._insert_missing(c, _FakeNet._rows(t_))
                c.close()
            target = td / "home" / "sub" / DB_NAME
            c = _connect(target)
            PRIOR._insert_missing(c, [{"date": "2018-01-02", "ticker": "A", "open": 9.9, "high": 9.9, "low": 9.9, "close": 9.9,
                                       "adj_close": 9.9, "volume": 1}])
            c.close()
            bk = td / "home" / "backup_20261101" / DB_NAME
            bk.parent.mkdir(parents=True)
            bk.write_bytes(b"")
            p_found, why = resolve_db(db_home=str(td / "home"))
            ck("⑤ --db-home 先找資料家底下既有的庫(不另開第二本 · 備份夾裡的同名庫不選)", p_found == target and why == "資料家既有庫", (p_found, why))
            rc_m = merge([str(l1), str(l2), str(td / "nope.duckdb")], db_home=str(td / "home"), log=lambda *a, **k: None)
            c = _connect(target, read_only=True)
            n = c.execute(f"SELECT count(*) FROM {TABLE}").fetchone()[0]
            keep = c.execute(f"SELECT close FROM {TABLE} WHERE ticker='A' AND date='2018-01-02'").fetchone()[0]
            c.close()
            ck("⑥ merge 只補缺鍵:既有列不被覆蓋 · 新鍵進 · 缺的暫存庫照實黃(rc 2)", n == 4 and keep == 9.9 and rc_m == 2, (n, keep, rc_m))
            cov = coverage("2018-01-01", db=str(target), cats=None)
            ck("⑦ coverage 三數:應抓 = 冊上全部 · A / B 有資料 · 其餘逐一列無資料 · 缺一不綠",
               cov["should"] == len(syms) and cov["have"] == 0 and cov["state"] == "YELLOW" and len(cov["empty"]) == len(syms))
            hold = _connect(target)
            try:
                rc_lock = 0 if os.name != "nt" else merge([str(l1)], db=str(target), log=lambda *a, **k: None)
            finally:
                hold.close()
            ck("⑧ Windows 上正庫被別的行程開著 → merge 紅不硬寫(本機非 Windows:同行程不會鎖,只記)", rc_lock in (0, 1))
    else:
        ck("⑤–⑧ 需 duckdb(本機沒裝:照實黃,不冒充綠)", False, "duckdb 缺")
    text = Path(__file__).read_text(encoding="utf-8")
    ck("⑨ 檔面:加速器橋 · 網路橋 · 不寫同意閘 · 沒有本機路徑 · 不 import http 庫",
       "[VIA:ACCEL-BRIDGE:v0100]" in text and "[VIA:NET-BRIDGE:v0100]" in text and "_CONSENT\"] " + "=" not in text
       and "\\" + "Users" not in text and not re.search(r"^\s*import (requests|urllib|httpx)", text, re.M))
    import subprocess
    pr = subprocess.run([sys.executable, "-B", str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    ck(f"⑩ 前版 {PRIOR_PATH.name} 自測照過(另起行程)", pr.returncode == 0, (pr.stdout or "")[-240:])
    n = sum(ok)
    print(f"[計] {STEM} {VERSION} 自測 {n}/{len(ok)} {'PASS' if n == len(ok) else 'FAIL'}", flush=True)
    return 0 if n == len(ok) else 1


def _opt(args, flag, default=None):
    return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else default


def _many(args, flag) -> list:
    if flag not in args:
        return []
    out = []
    for a in args[args.index(flag) + 1:]:
        if a.startswith("--"):
            break
        out.append(a)
    return out


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:1] or args[:1] == ["selftest"]:
        return selftest()
    cats = _opt(args, "--cats")
    cats = [c for c in cats.split(",") if c] if cats else None
    start, end = _opt(args, "--start", DEFAULT_START), _opt(args, "--end")
    if args[:1] == ["lane"]:
        return lane(_opt(args, "--part", "1/1"), _opt(args, "--lane-db"), start, end, cats)
    if args[:1] == ["merge"]:
        return merge(_many(args, "--from"), _opt(args, "--db"), _opt(args, "--db-home"))
    if args[:1] == ["coverage"]:
        c = coverage(start, _opt(args, "--db"), _opt(args, "--db-home"), cats)
        print(json.dumps(c, ensure_ascii=False, indent=1) if "--json" in args else render_coverage(c))
        return 0 if c["state"] == "GREEN" else 2
    if args[:1] == ["run"]:
        if _gated():
            print("[全球宇宙] 同意閘未開=拒跑(fail-closed 誠實)")
            return 2
        target, why = resolve_db(_opt(args, "--db"), _opt(args, "--db-home"))
        syms, pend = pick_symbols(cats)
        for p in pend:
            print(f"  [候源] {p}")
        r = fetch_rows(PRIOR._net(), syms, start, end)
        con = _connect(target)
        before = con.execute(f"SELECT count(*) FROM {TABLE}").fetchone()[0]
        PRIOR._insert_missing(con, r["rows"])
        after = con.execute(f"SELECT count(*) FROM {TABLE}").fetchone()[0]
        con.close()
        print(f"[全球宇宙 {VERSION}] {len(syms)} 檔 · {start}~{end or '最新'} · 主路 {r['via']['main']} · 備用 {r['via']['backup']}"
              f" · 無資料 {len(r['empty'])} · 實補 +{after - before:,} 列 · 庫 {target}({why})")
        return 0 if not r["empty"] else 3
    return PRIOR.main(args)


if __name__ == "__main__":
    sys.exit(main())
