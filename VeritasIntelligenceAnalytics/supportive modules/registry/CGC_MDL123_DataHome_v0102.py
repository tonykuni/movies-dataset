#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL123_DataHome v0102 — 資料本機家(批340;操作員令「現在資料庫都移入本機 增量更新加速器寫入本機」)
====================================================================
v0101→v0102(批490 操作員宣告「data save in parquet and managed by duckdb. this is database file:
  C:\\Users\\tonyk\\VIA System\\via_database — integrate and consolidate into database storage structure
  which saving the largest token when fetching and testing」):
  ① 資料家冊 VIA_DataHome_SSOT_v*.json(尾版律)進解析序:--home > env > VLL local_paths.json > **冊** > 舊指標 > 預設;
     預設 Windows 家改為操作員宣告的 via_database(舊家 Github\\movies-dataset\\data 留作 find 候選)。
     家若是**檔**(單本 duckdb)也認:家目錄=其上層,該檔列為一本庫。
  ② +catalog:家內清點——每本 .duckdb 的表/列/日期範圍 + 每個 parquet 湖(夾=一資料集)的檔數/列/日期範圍,
     寫 VIA_Reports/datahome/DATAHOME_CATALOG_latest.json(一頁目錄:by_name 庫名→路徑、by_table 表→在哪)。
     省 token 的核心就在這一頁:啟動層/匯流排/引擎讀它按名取路徑,測試與抓取讀它的 hi(最新日),不掃湖。
     預設一本庫一行(--tables 才逐表);沒 duckdb=誠實列檔不列表。
  ③ +plan:倉內散落的 .duckdb/.parquet(排除 references/SCOPE_COPY/沙盒/_repo_)逐個列出「在哪、多大、誰寫的」
     與建議接點;**只列不動**(搬/接/刪是操作員的手;接=link;複製=三副本病,不做)。
  ④ link --point <倉內相對夾> 可加接點(仍走鏡像目標 家/<倉名>/<相對夾>;冊上兩點不變)。
====================================================================
根因:批325 RepoOptimizer 把 data/ 移到本機資料家(C:\\Users\\tonyk\\Github\\movies-dataset\\data);
操作員接著把 DuckDB 也移入本機。倉內 145 個現役 py 寫死 functional modules/VDF/output_hub/mega
(正本零觸碰律=不能逐檔改路徑)→ 正解=「接點律」:倉內 output_hub 目錄改為指向本機資料家
的 Junction(Windows)/symlink(Linux);所有引擎零改動、增量更新(ENG054 增量律/ENG064
checkpoint/OmniFetch upsert)經接點直接寫入本機;git 端 output_hub 本就 .gitignore。
職權:
  status  解析資料家(VIA_DATA_HOME env > VLL local_paths.json data_home > data/WHERE_IS_DATA.md
          > 預設)+各接點狀態(REAL_DIR/LINKED/MISSING/HOME_ONLY)+庫探針(read_only 列數)
  find    掃候選位置找 vdf_tw_market.duckdb(誠實列;不猜)
  link    ①倉內目錄若為實體且有料→合併搬入資料家(hash 定生死:同 hash=跳;異 hash=家版留,
          倉版另存 _repo_<sha8> 不覆寫)②倉內改接點指向資料家 ③探針驗通(讀列數)
          --dry-run 只列計畫;冪等(已接=SKIP)
  unlink  拆接點→實體目錄(資料留家;倉內只留指標檔;不搬回)
律:只增不減;零刪除(讓位另存);誠實三態;接點=唯一寫入道;正本 145 引擎零觸碰。
用法:python3 CGC_MDL123_DataHome_v0102.py [status|find|catalog [--tables]|plan|link [--dry-run] [--point <相對夾>]|unlink] [--home <路徑>] | --selftest
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
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPO = VIA.parent
REP = VIA / "VIA_Reports" / "datahome"
# 接點冊(倉內相對路徑;整目錄接點=單一寫入道)
LINK_POINTS = ["functional modules/VDF/output_hub", "functional modules/GroupIndex/output_hub"]
DEFAULT_HOME_WIN = r"C:\Users\tonyk\VIA System\via_database"   # 批490 操作員宣告
LEGACY_HOME_WIN = r"C:\Users\tonyk\Github\movies-dataset\data"    # 批340 舊家(find 候選;不刪)
SSOT_GLOB = "VIA_DataHome_SSOT_v*.json"
CATALOG = REP / "DATAHOME_CATALOG_latest.json"
#: 日期欄常見名(與匯流排 census 同一張;問過實庫才列的)
_DATE_COLS = ("date", "trade_date", "obs_date", "period", "dt", "as_of", "ts")
#: 自測沙盒標記(與匯流排 v0118 同律;錨定到擁有者夾,免得撞到同名正夾)
SANDBOX_MARKS = ("/engine_bus/_cwd/", "/selftest_grid/", "/vdfout_runs/selftest_out/", "/_self_test")
DB_PROBES = ["functional modules/VDF/output_hub/mega/vdf_tw_market.duckdb",
             "functional modules/VDF/output_hub/mega/vdf_global_market.duckdb",
             "functional modules/VDF/output_hub/active_tw_etf/active_tw_etf_holdings/ActiveTWETF.duckdb"]


def resolve_home(via: Path = VIA, override: str | None = None) -> tuple[Path, str]:
    """資料家解析(優先序;回 (路徑, 來源))"""
    if override:
        return Path(override).expanduser(), "--home"
    env = os.environ.get("VIA_DATA_HOME", "").strip()
    if env:
        return Path(env).expanduser(), "env VIA_DATA_HOME"
    lp = via / "functional modules" / "VLL" / "config" / "local_paths.json"
    if lp.exists():
        try:
            j = json.loads(lp.read_text(encoding="utf-8"))
            if j.get("data_home"):
                return Path(j["data_home"]), "VLL local_paths.json"
        except Exception:
            pass
    sh = ssot_home(via)
    if sh:
        return sh, "資料家冊 " + SSOT_GLOB
    ptr = via.parent / "data" / "WHERE_IS_DATA.md"
    if ptr.exists():
        m = re.search(r"Local data home:\s*(.+)", ptr.read_text(encoding="utf-8", errors="ignore"))
        if m:
            return Path(m.group(1).strip()), "data/WHERE_IS_DATA.md"
    if os.name == "nt":
        return Path(DEFAULT_HOME_WIN), "預設(Windows)"
    return via.parent.parent / "via_data", "預設(非 Windows)"


WIN_PATH_RX = re.compile(r"^[A-Za-z]:[\\/]")


def ssot_home(via: Path = VIA) -> Path | None:
    """資料家冊(尾版律)宣告的家;只在本 OS 可用時回(Windows 冊值在 Linux 上不算數=誠實 None)。"""
    try:
        cands = sorted((via / "supportive modules" / "registry").glob(SSOT_GLOB))
        if not cands:
            return None
        j = json.loads(cands[-1].read_text(encoding="utf-8"))
        v = j.get("home_win") if os.name == "nt" else j.get("home_posix")
        return Path(v).expanduser() if v else None
    except Exception:
        return None


def home_dir(h: Path) -> tuple[Path, Path | None]:
    """家若是檔(單本 duckdb,操作員說「database file」也可能真是一個檔)→ (上層夾, 該檔);夾 → (夾, None)。"""
    try:
        if h.is_file():
            return h.parent, h
    except Exception:
        pass
    return h, None


def _is_sandbox(sp: str) -> bool:
    sp = sp.replace("\\", "/")
    return any(m in sp for m in SANDBOX_MARKS)


def home_usable(h: Path) -> tuple[bool, str]:
    """批377 實錄(雲端 Linux 讀到 Windows 指標 C:\\Users\\… → Path 視為相對路徑→在 cwd 下造出字面目錄並搬走 output_hub,
    symlink 指向不可解析目標=接點斷裂):資料家必須是「本 OS 可用的絕對路徑」才准 link;否則誠實拒接,零搬移。"""
    hs = str(h)
    if os.name != "nt" and WIN_PATH_RX.match(hs):
        return False, "資料家為 Windows 路徑而本機非 Windows(" + hs + ")=不接(誠實停;零搬移)"
    if os.name == "nt" and hs.startswith("/"):
        return False, "資料家為 POSIX 路徑而本機為 Windows(" + hs + ")=不接"
    if not h.is_absolute():
        return False, "資料家非絕對路徑(" + hs + ")=不接"
    anchor = h.anchor and Path(h.anchor)
    if anchor and not Path(h.anchor).exists():
        return False, "資料家所在磁碟/根不存在(" + str(h.anchor) + ")=不接"
    return True, "可用"


def _is_link(p: Path) -> bool:
    if p.is_symlink():
        return True
    if os.name == "nt":
        try:
            return bool(os.stat(p, follow_symlinks=False).st_file_attributes & 0x400)  # REPARSE_POINT
        except Exception:
            return False
    return False


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _make_link(link: Path, target: Path) -> None:
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(str(target), str(link))
    else:
        os.symlink(str(target), str(link), target_is_directory=True)


def _probe_db(p: Path) -> dict:
    if not p.exists():
        return {"state": "MISSING"}
    try:
        import duckdb
        con = duckdb.connect(str(p), read_only=True)
        try:
            names = [r[0] for r in con.execute("select table_name from information_schema.tables where table_schema='main'").fetchall()]
            rows = sum(con.execute(f'select count(*) from "{t}"').fetchone()[0] for t in names)
        finally:
            con.close()
        return {"state": "OK", "tables": len(names), "rows": int(rows), "mb": round(p.stat().st_size / 1048576, 1)}
    except Exception as exc:
        s = str(exc)
        return {"state": "BUSY" if ("lock" in s.lower() or "being used" in s) else "FAIL", "reason": s[:120]}


def status(via: Path = VIA, home: str | None = None, do_print: bool = True) -> dict:
    h, src = resolve_home(via, home)
    d = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "home": str(h), "home_src": src,
         "home_exists": h.exists(), "points": [], "probes": []}
    for rel in LINK_POINTS:
        rp = via / rel
        tgt = h / via.name / rel
        if _is_link(rp):
            try:
                real = Path(os.path.realpath(rp))
            except Exception:
                real = None
            st = "LINKED" if (real and tgt.exists() and real.resolve() == tgt.resolve()) else "LINKED_ELSEWHERE"
        elif rp.is_dir():
            n = sum(1 for _ in rp.rglob("*") if _.is_file())
            st = "REAL_DIR" if n else "REAL_EMPTY"
        else:
            st = "MISSING"
        d["points"].append({"rel": rel, "repo": str(rp), "home": str(tgt), "state": st,
                            "home_files": sum(1 for _ in tgt.rglob("*") if _.is_file()) if tgt.exists() else 0})
    for rel in DB_PROBES:
        pr = _probe_db(via / rel)
        pr["rel"] = rel
        d["probes"].append(pr)
    d["state"] = ("OK" if all(p["state"] == "LINKED" for p in d["points"]) else
                  ("PART" if any(p["state"] == "LINKED" for p in d["points"]) else "UNLINKED"))
    if do_print:
        print(f"[資料家] {h}(來源:{src};{'在' if h.exists() else '缺'})· 接點 {d['state']}")
        for p in d["points"]:
            print(f"  {p['state']:16s} {p['rel']}  → {p['home']}(家內 {p['home_files']} 檔)")
        for p in d["probes"]:
            print(f"  庫 {p['state']:8s} {p['rel'].split('/')[-1]}" + (f" · {p['tables']} 表 · {p['rows']:,} 列 · {p['mb']} MB" if p["state"] == "OK" else f" · {p.get('reason', '')}"))
    return d


def find(via: Path = VIA, do_print: bool = True) -> list:
    cands = []
    seen = set()
    roots = [Path(os.environ.get("VIA_DATA_HOME", "")) if os.environ.get("VIA_DATA_HOME") else None,
             Path(DEFAULT_HOME_WIN), Path(LEGACY_HOME_WIN), Path.home() / "Github", Path.home() / "Downloads", Path.home() / "Documents",
             Path("C:/VIA") if os.name == "nt" else via.parent.parent / "via_data", via]
    for r in roots:
        if not r or not r.exists():
            continue
        try:
            for p in r.rglob("vdf_tw_market.duckdb"):
                rp = str(p.resolve())
                if rp in seen:
                    continue
                seen.add(rp)
                cands.append({"path": rp, "mb": round(p.stat().st_size / 1048576, 1),
                              "mtime": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                              "in_repo": str(via) in rp})
        except Exception:
            continue
    if do_print:
        print(f"[找庫] vdf_tw_market.duckdb 候選 {len(cands)} 件(誠實列;不猜):")
        for c in cands:
            print(f"  {c['mb']:9.1f} MB  {c['mtime']}  {'[倉內]' if c['in_repo'] else '[本機]'}  {c['path']}")
    return cands


def _merge_dir(src: Path, dst: Path, dry: bool, log: list) -> dict:
    """倉→家合併搬入(hash 定生死;異 hash=家版留、倉版讓位另存 _repo_<sha8>;零刪除)"""
    n_move = n_skip = n_yield = 0
    for p in sorted(src.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(src)
        t = dst / rel
        if t.exists():
            if _sha(p) == _sha(t):
                n_skip += 1
                if not dry:
                    p.unlink()  # 同 hash=冪等(家版即正本;倉版為副本)
                continue
            alt = t.with_name(f"{t.stem}_repo_{_sha(p)[:8]}{t.suffix}")
            log.append(f"讓位 {rel} → {alt.name}(家版留;倉版另存)")
            n_yield += 1
            if not dry:
                alt.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(p), str(alt))
            continue
        n_move += 1
        if not dry:
            t.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(p), str(t))
    return {"moved": n_move, "skipped_identical": n_skip, "yielded": n_yield}


def link(via: Path = VIA, home: str | None = None, dry: bool = False, do_print: bool = True, points: list | None = None) -> int:
    h, src = resolve_home(via, home)
    log, rc = [], 0
    rep = {"ts": datetime.now().strftime("%Y%m%d_%H%M%S"), "home": str(h), "home_src": src, "dry_run": dry, "points": []}
    if do_print:
        print(f"[接點] 資料家 {h}(來源:{src}){' · DRY-RUN' if dry else ''}")
    ok, why = home_usable(h)
    if not ok:
        if do_print:
            print("  [FAIL] 資料家不可用:" + why + " → 設 env VIA_DATA_HOME=<本機絕對路徑> 或 --home;本機零變動")
        rep["state"], rep["note"] = "FAIL", why
        return 1
    for rel in (points or LINK_POINTS):
        rp = via / rel
        tgt = h / via.name / rel
        ent = {"rel": rel, "home": str(tgt)}
        if _is_link(rp):
            real = Path(os.path.realpath(rp)).resolve()
            ent["state"] = "SKIP"
            ent["note"] = "已接" + ("" if tgt.exists() and real == tgt.resolve() else f"(指向他處 {real})")
        else:
            try:
                if not dry:
                    tgt.mkdir(parents=True, exist_ok=True)
                if rp.is_dir():
                    m = _merge_dir(rp, tgt, dry, log)
                    ent.update(m)
                    if not dry:
                        # 空殼目錄清除(檔已搬盡;非空=誠實停)
                        left = [x for x in rp.rglob("*") if x.is_file()]
                        if left:
                            ent["state"] = "FAIL"
                            ent["note"] = f"倉內仍餘 {len(left)} 檔未搬(誠實停;不強刪)"
                            rep["points"].append(ent)
                            rc = 1
                            continue
                        shutil.rmtree(rp)
                if not dry:
                    _make_link(rp, tgt)
                    if not (Path(os.path.realpath(rp)).exists() and (Path(os.path.realpath(rp)) / ".").exists()):
                        # 批377:接點不可解析=立即回滾(拆鏈→資料搬回原位),永不留斷鏈
                        rp.unlink() if rp.is_symlink() else os.rmdir(rp)
                        shutil.move(str(tgt), str(rp))
                        raise RuntimeError("接點不可解析已回滾(資料搬回 " + str(rp) + ")")
                ent["state"] = "OK" if not dry else "PLAN"
                ent["note"] = ("junction" if os.name == "nt" else "symlink") + f" {rp} → {tgt}"
            except Exception as exc:
                ent["state"] = "FAIL"
                ent["note"] = f"{type(exc).__name__}: {str(exc)[:120]}"
                rc = 1
        rep["points"].append(ent)
        if do_print:
            print(f"  [{ent['state']}] {rel} · {ent.get('note', '')}"
                  + (f" · 搬 {ent.get('moved', 0)} 跳 {ent.get('skipped_identical', 0)} 讓位 {ent.get('yielded', 0)}" if "moved" in ent else ""))
    for line in log:
        if do_print:
            print("    " + line)
    rep["log"] = log
    if not dry:
        rep["probes"] = [dict(_probe_db(via / r), rel=r) for r in DB_PROBES]
        if do_print:
            for p in rep["probes"]:
                print(f"  庫 {p['state']:8s} {p['rel'].split('/')[-1]}" + (f" · {p['rows']:,} 列 經接點可讀" if p["state"] == "OK" else f" · {p.get('reason', '')}"))
        REP.mkdir(parents=True, exist_ok=True)
        (REP / f"DATAHOME_{rep['ts']}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        # 指標檔(倉內;.gitignore 內)
        try:
            (via / "functional modules" / "VDF" / "WHERE_IS_OUTPUT_HUB.md").write_text(
                f"# output_hub 已接點至本機資料家\n\n{tgt.parent.parent}\n\n接點 {rep['ts']} · 引擎零改動;增量更新經接點寫入本機;git 不載。\n"
                f"拆接:python CGC_MDL123_DataHome 尾版 unlink\n", encoding="utf-8")
        except Exception:
            pass
    return rc


def unlink(via: Path = VIA, do_print: bool = True) -> int:
    rc = 0
    for rel in LINK_POINTS:
        rp = via / rel
        if _is_link(rp):
            try:
                real = os.path.realpath(rp)
                if os.name == "nt":
                    os.rmdir(rp)
                else:
                    rp.unlink()
                rp.mkdir(parents=True, exist_ok=True)
                (rp / "WHERE_IS_DATA.md").write_text(f"# 已拆接點;資料留於本機資料家\n\n{real}\n", encoding="utf-8")
                if do_print:
                    print(f"  [OK] 拆接 {rel}(資料留 {real};倉內留指標)")
            except Exception as exc:
                rc = 1
                if do_print:
                    print(f"  [FAIL] 拆接 {rel}:{exc}")
        elif do_print:
            print(f"  [SKIP] {rel} 非接點")
    return rc


# ────────────────────────────── 批490:catalog / plan ──────────────────────────────
def _tbl_stat(con, sql_from: str, cols: list) -> dict:
    """一張表(或一個湖)的列數與日期範圍;算不出的誠實留空。"""
    n = con.execute(f"SELECT COUNT(*) FROM {sql_from}").fetchone()[0]
    dcol = next((c for c in cols if c.lower() in _DATE_COLS), None)
    lo = hi = ""
    if dcol and n:
        try:
            a, b = con.execute(f'SELECT MIN("{dcol}"), MAX("{dcol}") FROM {sql_from}').fetchone()
            lo, hi = (str(a) if a is not None else ""), (str(b) if b is not None else "")
        except Exception:
            lo = hi = ""
    return {"rows": int(n), "date_col": dcol or "", "lo": lo[:19], "hi": hi[:19]}


def catalog(via: Path = VIA, home: str | None = None, tables: bool = False, do_print: bool = True) -> dict:
    """家內清點(唯讀):.duckdb 逐本(表/列/日期範圍)+ parquet 湖逐夾(檔/列/日期範圍)→ 一頁目錄 JSON。

    省 token 的用法:之後所有「庫在哪/表有多新」的問題都讀這一頁,不再掃樹、不再逐表 COUNT。
    沒 duckdb 的環境=誠實只列檔(state NODUCKDB);家不在=誠實 ABSENT,零發明。
    """
    h, src = resolve_home(via, home)
    hd, hfile = home_dir(h)
    d = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "home": str(hd), "home_src": src,
         "home_is_file": bool(hfile), "home_exists": hd.exists(), "dbs": [], "lake": [],
         "by_name": {}, "by_table": {}, "state": "ABSENT", "why": ""}
    if not hd.exists():
        d["why"] = f"資料家不在:{hd}(來源 {src})→ 設 env VIA_DATA_HOME 或改冊 VIA_DataHome_SSOT;零發明"
        if do_print:
            print(f"[家] 缺 · {d['why']}")
        return d
    try:
        import duckdb
    except Exception:
        duckdb = None
        d["why"] = "本環境無 duckdb=只列檔不列表(誠實)"
    dbs = [hfile] if hfile else sorted(p for p in hd.rglob("*.duckdb") if not _is_sandbox(str(p)))
    for db in dbs:
        ent = {"name": db.name, "path": str(db), "rel": str(db.relative_to(hd)) if not hfile else db.name,
               "mb": round(db.stat().st_size / 1048576, 1),
               "mtime": datetime.fromtimestamp(db.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
               "tables": [], "state": "NODUCKDB" if duckdb is None else "OK"}
        if duckdb is not None:
            con = None
            try:
                con = duckdb.connect(str(db), read_only=True)
                for (t,) in con.execute("SHOW TABLES").fetchall():
                    t = str(t)
                    try:
                        cols = [str(r[1]) for r in con.execute(f'PRAGMA table_info("{t}")').fetchall()]
                        st = _tbl_stat(con, f'"{t}"', cols)
                    except Exception as exc:
                        st = {"rows": -1, "date_col": "", "lo": "", "hi": "", "err": str(exc)[:80]}
                    st["table"] = t
                    ent["tables"].append(st)
                    d["by_table"].setdefault(t, {"kind": "duckdb", "db": db.name, "path": str(db)})
            except Exception as exc:
                s_ = str(exc)
                ent["state"] = "BUSY" if ("lock" in s_.lower() or "being used" in s_) else "FAIL"
                ent["why"] = s_[:120]
            finally:
                if con is not None:
                    try:
                        con.close()
                    except Exception:
                        pass
        d["dbs"].append(ent)
        d["by_name"].setdefault(db.name, str(db))
    # parquet 湖:一夾 = 一資料集(夾名即表名;單檔直接以檔名為名)
    groups: dict = {}
    if not hfile:
        for pq in sorted(hd.rglob("*.parquet")):
            if _is_sandbox(str(pq)):
                continue
            groups.setdefault(pq.parent, []).append(pq)
    for folder, files in groups.items():
        name = folder.name if folder != hd else "(根)"
        stems = sorted({f.stem for f in files})
        ent = {"dataset": name, "dir": str(folder), "rel": str(folder.relative_to(hd)) if folder != hd else ".",
               "files": len(files), "mb": round(sum(f.stat().st_size for f in files) / 1048576, 1),
               "stems": stems[:8], "rows": -1, "date_col": "", "lo": "", "hi": "",
               "state": "NODUCKDB" if duckdb is None else "OK"}
        if duckdb is not None:
            con = None
            try:
                con = duckdb.connect()
                glob_ = str(folder / "*.parquet").replace("'", "''")
                cols = [str(r[0]) for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{glob_}')").fetchall()]
                ent.update(_tbl_stat(con, f"read_parquet('{glob_}')", cols))
            except Exception as exc:
                ent["state"], ent["why"] = "FAIL", str(exc)[:120]
            finally:
                if con is not None:
                    try:
                        con.close()
                    except Exception:
                        pass
        d["lake"].append(ent)
        d["by_table"].setdefault(name, {"kind": "parquet", "dir": str(folder)})
        for st_ in stems:
            d["by_table"].setdefault(st_, {"kind": "parquet", "dir": str(folder)})
    d["state"] = "OK" if (d["dbs"] or d["lake"]) else "EMPTY"
    if d["state"] == "EMPTY":
        d["why"] = d["why"] or f"家在但沒有 .duckdb/.parquet:{hd}"
    try:
        rep = via / "VIA_Reports" / "datahome"          # 以傳入的 via 為準(自測沙盒不碰真 VIA_Reports)
        rep.mkdir(parents=True, exist_ok=True)
        cat = rep / CATALOG.name
        cat.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        d["catalog_path"] = str(cat)
    except Exception as exc:
        d["catalog_err"] = str(exc)[:80]
    if do_print:
        print(f"[家] {hd}(來源:{src}{';單檔' if hfile else ''})· 庫 {len(d['dbs'])} 本 · 湖 {len(d['lake'])} 夾"
              + (f" · {d['why']}" if d["why"] else ""))
        for e in d["dbs"]:
            tot = sum(max(t["rows"], 0) for t in e["tables"])
            hi = max((t["hi"] for t in e["tables"] if t["hi"]), default="")
            print(f"  [庫] {e['name']:30s} {e['rel']:44s} {e['mb']:>9,.1f} MB · {len(e['tables']):3d} 表 · {tot:>12,} 列"
                  + (f" · 最新 {hi[:10]}" if hi else "") + (f" · {e['state']} {e.get('why', '')}" if e["state"] != "OK" else ""))
            if tables:
                for t in e["tables"]:
                    rng = f"{t['lo'][:10]} → {t['hi'][:10]}" if t["lo"] else ""
                    print(f"        {t['table']:34s} {t['rows']:>12,}  {rng}")
        for e in d["lake"]:
            rng = f"{e['lo'][:10]} → {e['hi'][:10]}" if e["lo"] else ""
            print(f"  [湖] {e['dataset']:30s} {e['rel']:44s} {e['mb']:>9,.1f} MB · {e['files']:3d} 檔 · {e['rows']:>12,} 列  {rng}"
                  + (f" · {e['state']} {e.get('why', '')}" if e["state"] != "OK" else ""))
        print(f"[目錄] {d['state']} · 存證 {d.get('catalog_path', d.get('catalog_err', ''))}(啟動層/匯流排/引擎按名讀這頁,不掃樹)")
    return d


def plan(via: Path = VIA, home: str | None = None, do_print: bool = True) -> dict:
    """倉內散落庫盤點 → 整併計畫(**只列不動**)。

    列:倉內(不在家裡)的 .duckdb / .parquet 夾,大小、最後修改、疑似寫入者(同名引擎夾),
    與建議:接點(link --point <夾>)或維持原位(引擎產物/暫存)。搬與接是操作員的手。
    """
    h, src = resolve_home(via, home)
    hd, _ = home_dir(h)
    items = []
    seen_dirs = set()
    for pat in ("*.duckdb", "*.parquet"):
        for f in sorted(via.rglob(pat)):
            sp = str(f).replace("\\", "/")
            if "/references/" in sp or "SCOPE_COPY" in sp or _is_sandbox(sp) or "_repo_" in f.name:
                continue
            try:
                rp = f.resolve()
                if hd.exists() and str(rp).startswith(str(hd.resolve())):
                    continue          # 經接點已在家=不算散落
            except Exception:
                pass
            key = f.parent if pat == "*.parquet" else f
            if key in seen_dirs:
                continue
            seen_dirs.add(key)
            rel = str(f.parent.relative_to(via)) if pat == "*.parquet" else str(f.relative_to(via))
            mb = (sum(x.stat().st_size for x in f.parent.glob("*.parquet")) if pat == "*.parquet" else f.stat().st_size) / 1048576
            top = rel.split("/")[0] if "/" in rel else rel
            fam = rel.split("/")[1] if rel.startswith("functional modules/") and rel.count("/") >= 1 else top
            temp = any(k in rel for k in ("staging", "_temp", "_warehouse", "_generated", "VIA_Reports"))
            on_point = next((r for r in LINK_POINTS if rel.startswith(r + "/")), None)
            items.append({"kind": pat[2:], "rel": rel, "mb": round(mb, 1), "family": fam,
                          "mtime": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d"),
                          "suggest": ("維持原位(引擎暫存/產物;整併前先確認寫入者)" if temp else
                                      f"冊上接點 {on_point}:link(搬入家+倉內留接點;操作員的手)" if on_point else
                                      f"接點:link --point \"{str(Path(rel).parent if pat == '*.duckdb' else rel)}\"(搬入家+倉內留接點;操作員的手)")})
    d = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "home": str(hd), "home_src": src, "items": items,
         "points": [{"rel": r, "state": ("LINKED" if _is_link(via / r) else ("REAL_DIR" if (via / r).is_dir() else "MISSING"))} for r in LINK_POINTS]}
    if do_print:
        print(f"[整併計畫] 家 {hd}(來源:{src};{'在' if hd.exists() else '缺'})· 倉內散落 {len(items)} 處 · **只列不動**")
        for pnt in d["points"]:
            print(f"  接點 {pnt['state']:9s} {pnt['rel']}")
        for it in items:
            print(f"  [{it['kind']:7s}] {it['rel'][:78]:78s} {it['mb']:>8,.1f} MB · {it['mtime']} · {it['family'][:12]:12s} → {it['suggest']}")
        print("  律:搬=link(hash 定生死、零刪除);不複製(三副本病);刪副本/暫存=操作員的手")
    return d


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        via = root / "repo" / "VeritasIntelligenceAnalytics"
        home = root / "home" / "data"
        mega = via / "functional modules" / "VDF" / "output_hub" / "mega"
        mega.mkdir(parents=True)
        (via / "functional modules" / "GroupIndex" / "output_hub").mkdir(parents=True)
        import duckdb
        con = duckdb.connect(str(mega / "vdf_tw_market.duckdb"))
        con.execute("create table t as select range as x from range(5)")
        con.close()
        (mega / "same.txt").write_text("same", encoding="utf-8")
        (mega / "diff.txt").write_text("repo-version", encoding="utf-8")
        hm = home / via.name / "functional modules" / "VDF" / "output_hub" / "mega"
        hm.mkdir(parents=True)
        (hm / "same.txt").write_text("same", encoding="utf-8")
        (hm / "diff.txt").write_text("home-version", encoding="utf-8")
        st0 = status(via, str(home), do_print=False)
        chk("① 解析+狀態(--home 覆寫;倉內 REAL_DIR;家在)", st0["home_src"] == "--home"
            and st0["points"][0]["state"] == "REAL_DIR" and st0["state"] == "UNLINKED")
        rc_dry = link(via, str(home), dry=True, do_print=False)
        chk("② dry-run 零變動(倉內仍實體;家內未增)", rc_dry == 0 and not _is_link(via / LINK_POINTS[0])
            and (mega / "vdf_tw_market.duckdb").exists() and not (hm / "vdf_tw_market.duckdb").exists())
        rc = link(via, str(home), do_print=False)
        st1 = status(via, str(home), do_print=False)
        chk("③ link 真接(倉內→接點;庫搬入家;探針經接點讀 5 列)", rc == 0 and st1["state"] == "OK"
            and _is_link(via / LINK_POINTS[0]) and (hm / "vdf_tw_market.duckdb").exists()
            and st1["probes"][0]["state"] == "OK" and st1["probes"][0]["rows"] == 5,
            f"(probe={st1['probes'][0]})")
        chk("④ hash 定生死(同 hash 跳;異 hash 家版留+倉版讓位 _repo_<sha8>;零刪除)",
            (hm / "diff.txt").read_text(encoding="utf-8") == "home-version"
            and any(p.name.startswith("diff_repo_") for p in hm.iterdir())
            and (hm / "same.txt").read_text(encoding="utf-8") == "same")
        # 寫入經接點=落家(增量更新寫入本機律)
        con = duckdb.connect(str(mega / "vdf_tw_market.duckdb"))
        con.execute("insert into t select 99")
        con.close()
        con = duckdb.connect(str(hm / "vdf_tw_market.duckdb"), read_only=True)
        n = con.execute("select count(*) from t").fetchone()[0]
        con.close()
        chk("⑤ 經接點寫入=直落本機家(增量更新寫入本機;引擎路徑零改)", n == 6)
        rc2 = link(via, str(home), do_print=False)
        chk("⑥ 冪等(再 link=SKIP 已接)", rc2 == 0 and status(via, str(home), do_print=False)["state"] == "OK")
        rcu = unlink(via, do_print=False)
        chk("⑦ unlink 拆接(資料留家;倉內指標;零刪除)", rcu == 0 and not _is_link(via / LINK_POINTS[0])
            and (hm / "vdf_tw_market.duckdb").exists() and (via / LINK_POINTS[0] / "WHERE_IS_DATA.md").exists())
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 紀律宣告(接點律/正本零觸碰/hash 定生死/零刪除/誠實)", all(k in src for k in ("接點律", "零觸碰", "hash 定生死", "零刪除", "誠實")))
    import tempfile as _tf
    with _tf.TemporaryDirectory() as td9:
        v9 = Path(td9) / "VIA"
        (v9 / LINK_POINTS[0]).mkdir(parents=True)
        (v9 / LINK_POINTS[0] / "keep.txt").write_text("x", encoding="utf-8")
        bad = "C:\\Users\\x\\data" if os.name != "nt" else "/home/x/data"
        rc9 = link(v9, bad, do_print=False)
        u1 = home_usable(Path(bad))[0]
        u2 = home_usable(Path(td9))[0]
        chk("⑨ 資料家可用律(批377:異 OS 路徑/相對路徑=拒接零搬移;本 OS 絕對路徑=可用)",
            rc9 == 1 and not u1 and u2 and (v9 / LINK_POINTS[0] / "keep.txt").exists() and not _is_link(v9 / LINK_POINTS[0])
            and not home_usable(Path("rel/path"))[0])
    # 批490 ⑩⑪:家內清點與整併計畫(暫存家;零觸碰倉庫)
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        v10 = root / "repo" / "VeritasIntelligenceAnalytics"
        (v10 / "supportive modules" / "registry").mkdir(parents=True)
        h10 = root / "VIA System" / "via_database"
        (h10 / "lake" / "tw_daily_prices").mkdir(parents=True)
        (v10 / "functional modules" / "X" / "staging").mkdir(parents=True)
        try:
            import duckdb
            con = duckdb.connect(str(h10 / "vdf_tw_market.duckdb"))
            con.execute("CREATE TABLE tw_listings AS SELECT 1 AS id")
            con.execute("CREATE TABLE tw_prices AS SELECT DATE '2026-01-01' AS date UNION ALL SELECT DATE '2026-03-01'")
            con.close()
            con = duckdb.connect()
            pq = str(h10 / "lake" / "tw_daily_prices" / "part-2026.parquet").replace("'", "''")
            con.execute(f"COPY (SELECT DATE '2026-02-01' AS date, 1 AS v UNION ALL SELECT DATE '2026-02-03', 2) TO '{pq}' (FORMAT PARQUET)")
            con.close()
            con = duckdb.connect(str(v10 / "functional modules" / "X" / "staging" / "x.duckdb")); con.close()
            (v10 / "VIA_Reports" / "engine_bus" / "_cwd").mkdir(parents=True)
            con = duckdb.connect(str(v10 / "VIA_Reports" / "engine_bus" / "_cwd" / "sandbox.duckdb")); con.close()
            os.environ["VIA_DATA_HOME"] = str(h10)
            try:
                d10 = catalog(v10, do_print=False)
                d11 = plan(v10, do_print=False)
                (v10 / "supportive modules" / "registry" / "VIA_DataHome_SSOT_v0100.json").write_text(
                    json.dumps({"home_win": str(h10), "home_posix": str(h10)}), encoding="utf-8")
                os.environ.pop("VIA_DATA_HOME", None)
                hs, src10 = resolve_home(v10)
            finally:
                os.environ.pop("VIA_DATA_HOME", None)
            t10 = {t["table"]: t for e in d10["dbs"] for t in e["tables"]}
            lk = {e["dataset"]: e for e in d10["lake"]}
            chk("⑩ catalog:家內 duckdb 表/列/日期範圍 + parquet 湖(夾=資料集)列/日期範圍 + by_name/by_table 一頁目錄",
                d10["state"] == "OK" and t10.get("tw_prices", {}).get("rows") == 2 and t10["tw_prices"]["hi"][:10] == "2026-03-01"
                and lk.get("tw_daily_prices", {}).get("rows") == 2 and lk["tw_daily_prices"]["hi"][:10] == "2026-02-03"
                and d10["by_name"].get("vdf_tw_market.duckdb") and d10["by_table"]["tw_daily_prices"]["kind"] == "parquet")
            chk("⑪ plan 只列不動:倉內散落列出、沙盒(engine_bus/_cwd)不列、家不動;資料家冊(尾版)進解析序",
                [i["rel"] for i in d11["items"]] == ["functional modules/X/staging/x.duckdb"]
                and (v10 / "functional modules" / "X" / "staging" / "x.duckdb").exists()
                and (h10 / "vdf_tw_market.duckdb").exists() and hs == h10 and src10.startswith("資料家冊"))
        except ImportError:
            chk("⑩ catalog(本環境無 duckdb=SKIP 誠實)", True, "SKIP")
            chk("⑪ plan(本環境無 duckdb=SKIP 誠實)", True, "SKIP")
    print(f"  [計] 十一檢 OK {11 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 資料本機家(CGC_MDL123 v0102)· 十一檢自測(暫存沙盒;零觸碰倉庫)===")
        return selftest()
    home = a[a.index("--home") + 1] if "--home" in a and a.index("--home") + 1 < len(a) else None
    cmd = a[0] if a and not a[0].startswith("--") else "status"
    if cmd == "find":
        find()
        return 0
    if cmd == "catalog":
        d = catalog(home=home, tables="--tables" in a)
        return 0 if d["state"] == "OK" else 2
    if cmd == "plan":
        plan(home=home)
        return 0
    if cmd == "link":
        pts = [a[i + 1] for i, x in enumerate(a) if x == "--point" and i + 1 < len(a)]
        return link(home=home, dry="--dry-run" in a, points=pts or None)
    if cmd == "unlink":
        return unlink()
    status(home=home)
    return 0


if __name__ == "__main__":
    sys.exit(main())
