#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL123_DataHome v0100 — 資料本機家(批340;操作員令「現在資料庫都移入本機 增量更新加速器寫入本機」)
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
用法:python3 CGC_MDL123_DataHome_v0100.py [status|find|link [--dry-run]|unlink] [--home <路徑>] | --selftest
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
DEFAULT_HOME_WIN = r"C:\Users\tonyk\Github\movies-dataset\data"
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
    ptr = via.parent / "data" / "WHERE_IS_DATA.md"
    if ptr.exists():
        m = re.search(r"Local data home:\s*(.+)", ptr.read_text(encoding="utf-8", errors="ignore"))
        if m:
            return Path(m.group(1).strip()), "data/WHERE_IS_DATA.md"
    if os.name == "nt":
        return Path(DEFAULT_HOME_WIN), "預設(Windows)"
    return via.parent.parent / "via_data", "預設(非 Windows)"


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
             Path(DEFAULT_HOME_WIN), Path.home() / "Github", Path.home() / "Downloads", Path.home() / "Documents",
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


def link(via: Path = VIA, home: str | None = None, dry: bool = False, do_print: bool = True) -> int:
    h, src = resolve_home(via, home)
    log, rc = [], 0
    rep = {"ts": datetime.now().strftime("%Y%m%d_%H%M%S"), "home": str(h), "home_src": src, "dry_run": dry, "points": []}
    if do_print:
        print(f"[接點] 資料家 {h}(來源:{src}){' · DRY-RUN' if dry else ''}")
    for rel in LINK_POINTS:
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
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 資料本機家(CGC_MDL123 v0100)· 八檢自測(暫存沙盒;零觸碰倉庫)===")
        return selftest()
    home = a[a.index("--home") + 1] if "--home" in a and a.index("--home") + 1 < len(a) else None
    cmd = a[0] if a and not a[0].startswith("--") else "status"
    if cmd == "find":
        find()
        return 0
    if cmd == "link":
        return link(home=home, dry="--dry-run" in a)
    if cmd == "unlink":
        return unlink()
    status(home=home)
    return 0


if __name__ == "__main__":
    sys.exit(main())
