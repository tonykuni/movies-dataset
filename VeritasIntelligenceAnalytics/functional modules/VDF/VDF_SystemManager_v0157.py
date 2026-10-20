#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0157 — 薄尾:db verify 獨立核對資料庫清點(每列每欄重算比對)+ 冊上沒登寫入者的表列候選寫入者

操作員令(2026-10-20):「好,把檢查器加進 VDF 指令並開 PR 合併  善用VCGC的全景式分析  定位分類錯誤  安全第一輪修復」
  (前一句:「run VDF again to output summary of database(verified 100% correct)」)。
db verify [--json]:讀本輪 DB_CHECK_latest.json,**不用 db check 的程式**,自己重新推一遍再逐列逐欄比:
  ① 照冊(VIA_DB_Table_SSOT 尾版)與 check 記錄的家,唯讀開每本 DuckDB,自己算:檔 · 表在不在 · 列數 · 最新日 · 狀態 · 燈;
     他系統表分類(VRN-1 / VRN-2 / VCGC / VRN 未分辨,L123)與冊上最少 0 列規則也自己推(他系統先標,最少 0 列只改 VDF 自己的紅列)。
  ② 比對 65 表 × 5 欄(檔 · 列數 · 最新日 · 狀態 · 燈)+ 摘要計數 + 總燈 + 他系統逐系統計數;差異逐列列出。
  ③ 0 差異 = PASS(rc 0);有差異 = FAIL(rc 1);沒有本輪 check 結果 = NODATA(rc 2)。結果寫 VERIFY_latest.json / .html(同 check 的輸出夾)。
  ④ 定位分類錯誤(只攤開,不改燈、不改冊):冊上沒登寫入者的表 → 掃本倉各家族尾版程式碼(CREATE TABLE · INSERT INTO · to_sql · upsert_*),
     列「候選寫入者 · 系統 · 檔:行」;排除 VDF 管理員與 ActivateVDF 自己(自測沙盒建的表不算)。候選要操作員確認後才登冊(分類靠冊,不靠猜)。
只讀;不抓網、不碰 TA-Lib、不寫他系統的檔。只收 VIA_FROM_VCGC=YES(舊名;= 經任一系統自己的 manager / 啟動器啟動,L120 ⑥ · L123 ③)。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
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
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====


import datetime
import html
import json
import os
import re
import sys
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[1]
_STEM = "VDF_SystemManager"
TAG = "v0157"
SELF_ID = "VDF"
FIELDS = ("檔", "列數", "最新日", "狀態", "燈")
V_DATE_COLS = ("date", "trade_date", "dt", "asof_date", "as_of", "holding_date", "ym", "period", "published", "ts")
V_STALE = {"daily": 10, "monthly": 62, "other": 120}
SCAN_ROOTS = (VIA_ROOT / "functional modules", VIA_ROOT / "supportive modules")
SCAN_SKIP = ("VDF_SystemManager_", "VDF_MDL013_ActivateVDF_", "test_", "uxtest_")   # 管理員 / 啟動器自測沙盒 · 測試檔會建同名表,不算寫入者


def _vnum_v0157(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0157(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0157(p) < _vnum_v0157(__file__)), key=_vnum_v0157)
PRIOR = _load_v0157(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


DB_MOD = PRIOR.DB_MOD                              # v0151:_out() · REG(只拿路徑;核對的算法全在本檔,不用 db check 的函式)


# ---------------------------------------------------------------- 獨立重推(本檔自己的實作)
def _cad(col: str) -> str:
    return "monthly" if col in ("ym", "period") else ("daily" if col in ("date", "trade_date", "dt") else "other")


def _day(v):
    m = re.match(r"^(\d{4})-?(\d{2})(?:-?(\d{2}))?", str(v or "").strip())
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3) or 1))
    except ValueError:
        return None


def _locate(home: Path, name: str):
    hits = [p for p in home.rglob(name) if "_repo_" not in p.name and "stash" not in str(p).lower() and "selftest" not in str(p).lower()]
    hits.sort(key=lambda p: (("mega" in p.parts) or ("active_tw_etf" in str(p)), p.stat().st_size), reverse=True)
    return hits[0] if hits else None


def _vkeys(name: str) -> set:
    stem = re.sub(r"_v\d{4}$", "", Path(name).stem)
    out = {stem}
    m = re.match(r"(VRN2?_[A-Za-z]+\d+)", stem)
    if m:
        out.add(m.group(1))
    return out


def _vrn2(vrn_dir: Path, bundle: Path) -> set:
    keys = set()
    if vrn_dir.is_dir():
        for p in vrn_dir.iterdir():
            if p.name.startswith(("VRN_", "VRN2_")) and p.suffix in (".py", ".ps1"):
                keys |= _vkeys(p.name)
    try:
        j = json.loads(bundle.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        j = {}
    for k in ("files", "depends_on_tracked"):
        for it in j.get(k) or []:
            path = it.get("path") if isinstance(it, dict) else it
            if path:
                keys |= _vkeys(str(path).replace("\\", "/").rsplit("/", 1)[-1])
    return keys


def _wsys(w: str, v2: set):
    if w.startswith("CGC_"):
        return "VCGC"
    if w.startswith("VRN2_"):
        return "VRN-2"
    if w.startswith("VRN_"):
        return "VRN-2" if _vkeys(w) & v2 else "VRN-1"
    return None


def _osys(table: str, writers: list, v2: set):
    if writers:
        if any(w.startswith("VDF_") for w in writers):
            return None
        names = [_wsys(w, v2) for w in writers]
        if None in names:
            return None
        return " + ".join(sorted(set(names), key=["VRN-1", "VRN-2", "VCGC"].index))
    return "VRN 未分辨" if table.startswith("vrn_") else None


def rederive(home: Path, book: list, today: datetime.date, v2: set) -> dict:
    """照冊與家,唯讀重推每一列(本檔自己的算法;不呼叫 db check)。回 {(庫, 表): 列}。"""
    import duckdb
    out = {}
    for dbname in sorted({t["db"] for t in book}):
        tables = [t for t in book if t["db"] == dbname]
        path = _locate(home, dbname)
        have, con = {}, None
        if path is not None:
            try:
                con = duckdb.connect(str(path), read_only=True)
                have = {r[0]: r[1] for r in con.execute("select table_name, table_schema from information_schema.tables").fetchall()}
            except Exception as exc:                   # 打不開 = 每列照實記「庫打不開」(跟 check 比);他系統表照樣標 INFO(check 的 split_rows 也套在這些列)
                for t in tables:
                    tn, writers = t["table"], t.get("writers") or []
                    st, lamp, osys = "庫打不開:%s" % type(exc).__name__, "RED", _osys(tn, writers, v2)
                    if osys:
                        why = "· 冊上沒登寫入者,表名 vrn_ 開頭 " if osys == "VRN 未分辨" else ""
                        st, lamp = "他系統表(%s 寫)%s· %s · VDF 只攤開不代修" % (osys, why, st), "INFO"
                    out[(dbname, tn)] = {"檔": str(path), "列數": None, "最新日": None, "狀態": st, "燈": lamp,
                                         "_writers": writers, "_min": t.get("min_rows", 1), "_osys": osys}
                continue
        for t in tables:
            tn, mn, writers = t["table"], t.get("min_rows", 1), t.get("writers") or []
            e = {"檔": str(path) if path else "", "列數": None, "最新日": None}
            if path is None:
                st, lamp = "缺庫", "RED"
            elif tn not in have:
                st, lamp = "缺表", "RED"
            else:
                q = '"%s"."%s"' % (have[tn], tn)
                n = con.execute("select count(*) from %s" % q).fetchone()[0]
                cols = [c[0] for c in con.execute("select column_name from information_schema.columns where table_name=? and table_schema=?",
                                                   [tn, have[tn]]).fetchall()]
                dcol = next((c for c in V_DATE_COLS if c in cols), None)
                hi = None
                if dcol and n:
                    try:
                        hi = _day(con.execute("select max(cast(%s as varchar)) from %s where cast(%s as varchar) not like '1900%%'" % (dcol, q, dcol)).fetchone()[0])
                    except Exception:                   # 日期欄型別怪 = 不判新鮮度(同 check 的規則)
                        hi = None
                lag = (today - hi).days if hi else None
                st, lamp = "OK", "GREEN"
                if n < int(mn or 1):
                    st, lamp = ("空表" if n == 0 else "列數不足"), "RED"
                elif t.get("rows_seen") and n < 0.9 * int(t["rows_seen"]):
                    st, lamp = "列數比上次少", "YELLOW"
                elif lag is not None and lag > V_STALE[_cad(dcol)]:
                    st, lamp = "過舊", "YELLOW"
                e["列數"], e["最新日"] = n, (str(hi) if hi else None)
            osys = _osys(tn, writers, v2)
            if not osys and lamp == "RED" and mn is not None and int(mn) == 0:
                if st == "空表":
                    st, lamp = "空表 · 冊上最少 0 列(允許)", "GREEN"
                elif st in ("缺表", "缺庫"):
                    st, lamp = st + " · 冊上最少 0 列 → 待首寫(寫入者 %s 跑過才有)" % (" ".join(writers) or "冊上沒登"), "YELLOW"
            if osys:
                why = "· 冊上沒登寫入者,表名 vrn_ 開頭 " if osys == "VRN 未分辨" else ""
                st, lamp = "他系統表(%s 寫)%s· %s · VDF 只攤開不代修" % (osys, why, st), "INFO"
            e.update({"狀態": st, "燈": lamp, "_writers": writers, "_min": mn, "_osys": osys})
            out[(dbname, tn)] = e
        if con is not None:
            for extra in sorted(set(have) - {t["table"] for t in tables}):
                out[(dbname, extra)] = {"檔": str(path), "列數": None, "最新日": None, "狀態": "冊上沒列", "燈": "INFO"}
            con.close()
    return out


def _tails(roots) -> list:
    fam = {}
    for root in roots:
        for f in Path(root).rglob("*.py"):
            if any(part.startswith("_") and part != "__init__.py" for part in f.relative_to(root).parts[:-1]):
                continue
            m = re.match(r"(.*)_v(\d{4})$", f.stem)
            key = (str(f.parent), m.group(1) if m else f.stem)
            v = int(m.group(2)) if m else -1
            if key not in fam or v > fam[key][0]:
                fam[key] = (v, f)
    return [f for _v, f in fam.values() if not f.name.startswith(SCAN_SKIP)]


def writer_candidates(tables: list, v2: set, roots=SCAN_ROOTS) -> dict:
    """冊上沒登寫入者的表 → 各家族尾版程式碼裡寫它的檔(只攤開,不改燈、不改冊)。回 {表: [{檔, 行, 系統}]}。"""
    pats = {t: re.compile(r"(CREATE\s+(?:OR\s+REPLACE\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"']?(?:main\.)?%s\b"
                          r"|INSERT\s+(?:OR\s+REPLACE\s+)?INTO\s+[\"']?%s\b|to_sql\(\s*[\"']%s[\"']|upsert_\w*\([^)\n]*[\"']%s[\"'])"
                          % ((re.escape(t),) * 4), re.I) for t in tables}
    out = {t: [] for t in tables}
    if not tables:
        return out
    seen = set()
    for f in sorted(_tails(roots)):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        hit = [t for t in tables if t in text]         # 先看表名在不在檔裡,在才逐行比(快)
        if not hit:
            continue
        lines = text.splitlines()
        for t in hit:
            for n, line in enumerate(lines, 1):
                if pats[t].search(line):
                    if (t, f.name, n) not in seen:      # 同名檔在兩個夾(副本)只記一次
                        seen.add((t, f.name, n))
                        w = re.sub(r"_v\d{4}$", "", f.stem)
                        out[t].append({"檔": f.name, "行": n, "系統": _wsys(w, v2) or ("VDF" if w.startswith("VDF_") else "其他")})
                    break
    return out


def verify(out_dir: Path | None = None, reg: Path | None = None, roots=SCAN_ROOTS, write: bool = True,
           vrn_dir: Path | None = None, bundle: Path | None = None) -> dict:
    out_dir = Path(out_dir or DB_MOD._out())
    j = out_dir / "DB_CHECK_latest.json"
    base = {"verb": "db verify", "tag": "%s %s" % (_STEM, TAG), "ts": datetime.datetime.now().isoformat(timespec="seconds"), "check": str(j)}
    if not j.is_file():
        return dict(base, lamp="NODATA", why="沒有 DB_CHECK_latest.json(先跑 db check)", mismatches=[], rows_compared=0)
    chk_o = json.loads(j.read_text(encoding="utf-8"))
    rows = chk_o.get("rows") or []
    if not rows:
        return dict(base, lamp="NODATA", why="db check 沒有列(%s)" % chk_o.get("why"), mismatches=[], rows_compared=0, check_ts=chk_o.get("ts"))
    reg = Path(reg or DB_MOD.REG)
    books = sorted(reg.glob("VIA_DB_Table_SSOT_v*.json"), key=_vnum_v0157)
    book_p = next((b for b in books if b.name == chk_o.get("book")), books[-1] if books else None)
    book = json.loads(book_p.read_text(encoding="utf-8")).get("tables") or []
    v2 = _vrn2(vrn_dir or (VIA_ROOT / "functional modules" / "VRN"),
               bundle or (VIA_ROOT / "docs" / "handoff" / "ai" / "vrn2_ship" / "VRN2_Bundle_latest.json"))
    exp = rederive(Path(chk_o["home"]), book, datetime.date.fromisoformat(str(chk_o["ts"])[:10]), v2)
    got = {(r.get("庫"), r.get("表")): r for r in rows}
    mism = []
    for k in sorted(set(exp) | set(got), key=str):
        e, g = exp.get(k), got.get(k)
        if e is None or g is None:
            mism.append({"庫": k[0], "表": k[1], "欄": "(列)", "重推": "有" if e else "無", "check": "有" if g else "無"})
            continue
        for f in FIELDS:
            if (e.get(f) or None) != (g.get(f) or None):
                mism.append({"庫": k[0], "表": k[1], "欄": f, "重推": e.get(f), "check": g.get(f)})
    tally = {x: sum(1 for r in rows if r.get("燈") == x) for x in ("RED", "YELLOW", "GREEN", "INFO")}
    if tally != chk_o.get("summary"):
        mism.append({"庫": "(摘要)", "表": "", "欄": "summary", "重推": tally, "check": chk_o.get("summary")})
    lamp_r = "RED" if tally["RED"] else ("YELLOW" if tally["YELLOW"] else "GREEN")
    if lamp_r != chk_o.get("lamp"):
        mism.append({"庫": "(摘要)", "表": "", "欄": "lamp", "重推": lamp_r, "check": chk_o.get("lamp")})
    by = {}
    for e in exp.values():
        if e.get("_osys") and e.get("燈") == "INFO":
            by[e["_osys"]] = by.get(e["_osys"], 0) + 1
    ck_by = (chk_o.get("other_system") or {}).get("by_system")
    if ck_by is not None and ck_by != by:
        mism.append({"庫": "(摘要)", "表": "", "欄": "other_system.by_system", "重推": by, "check": ck_by})
    nowr = sorted({t["table"] for t in book if not (t.get("writers") or [])})
    cands = writer_candidates(nowr, v2, roots)
    o = dict(base, lamp="PASS" if not mism else "FAIL", check_ts=chk_o.get("ts"), check_tag=chk_o.get("tag"), home=chk_o["home"],
             book=book_p.name, rows_compared=len(exp), fields_compared=len(exp) * len(FIELDS), mismatches=mism,
             summary=tally, check_lamp=chk_o.get("lamp"), total_rows=sum(e.get("列數") or 0 for e in exp.values()),
             no_writer=len(nowr), candidates=cands)
    if write:
        o["files"] = _write_verify(o, out_dir)
    return o


def _write_verify(o: dict, out_dir: Path) -> dict:
    f = {"json": out_dir / "VERIFY_latest.json", "html": out_dir / "VERIFY_latest.html"}
    f["json"].write_text(json.dumps(o, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    e = lambda x: "—" if x is None or x == "" else html.escape(str(x))     # noqa: E731
    mm = "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (e(m["庫"]), e(m["表"]), e(m["欄"]), e(m["重推"]), e(m["check"]))
                 for m in o["mismatches"])
    cd = "".join("<tr><td>%s</td><td>%s</td></tr>" % (e(t), e(" · ".join("%s(%s)%s:%d" % (c["系統"], "候選", c["檔"], c["行"]) for c in cs) or "程式碼裡找不到寫入者"))
                 for t, cs in sorted(o["candidates"].items()))
    page = ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>VDF 資料庫獨立核對</title>"
            "<style>body{font:14px system-ui;margin:16px;background:#fafafa;overflow-wrap:anywhere}table{border-collapse:collapse;background:#fff;font-size:12px}"
            "td,th{padding:3px 6px;border-bottom:1px solid #eee;text-align:left}.wrap{overflow-x:auto}</style>"
            "<h1>VDF 資料庫獨立核對 · %s</h1><p>核對 %s(%s)· 家 %s · 冊 %s</p><p><b>%d 表 × %d 欄 = %d 欄比對 · 差異 %d</b> · 摘要 %s · 總列數 %s</p>"
            "<h2>差異</h2>%s<h2>冊上沒登寫入者的表(%d)· 候選寫入者(程式碼佐證,只攤開,待確認後登冊)</h2><div class=wrap><table><tr><th>表</th><th>候選</th></tr>%s</table></div>"
            % (e(o["lamp"]), e(o["check"]), e(o["check_ts"]), e(o["home"]), e(o["book"]), o["rows_compared"], len(FIELDS), o["fields_compared"],
               len(o["mismatches"]), e(json.dumps(o["summary"], ensure_ascii=False)), "{:,}".format(o["total_rows"]),
               ("<div class=wrap><table><tr><th>庫</th><th>表</th><th>欄</th><th>重推</th><th>check</th></tr>%s</table></div>" % mm) if mm else "<p>0 差異。</p>",
               o["no_writer"], cd))
    f["html"].write_text(page, encoding="utf-8")
    return {k: str(v) for k, v in f.items()}


def _print_verify(o: dict) -> None:
    for m in o.get("mismatches", [])[:40]:
        print("  [差異] %s · %s · %s · 重推 %s · check %s" % (m["庫"], m["表"], m["欄"], m["重推"], m["check"]))
    if o.get("candidates"):
        found = {t: cs for t, cs in o["candidates"].items() if cs}
        print("  [候選寫入者] 冊上沒登寫入者 %d 表 · 程式碼找到候選 %d 表(只攤開,待確認後登冊)" % (o.get("no_writer", 0), len(found)))
        for t, cs in sorted(found.items()):
            print("    %s ← %s" % (t, " · ".join("%s %s:%d" % (c["系統"], c["檔"], c["行"]) for c in cs[:4]) + (" …" if len(cs) > 4 else "")))
    if o.get("lamp") == "NODATA":
        print("[計] VDF db verify · NODATA · %s" % o.get("why"))
        return
    print("[計] VDF db verify · %d 表 × %d 欄 = %d 欄比對 · 差異 %d · 核對 %s(%s)· %s"
          % (o["rows_compared"], len(FIELDS), o["fields_compared"], len(o["mismatches"]), o.get("check_tag"), o.get("check_ts"), o["lamp"]))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    if args[:2] == ["db", "verify"]:
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print("[VDF] 拒絕。只能經 VDF 啟動器 / via-vcgc(VIA_FROM_VCGC=YES)。")
            return 2
        o = verify()
        if "--json" in args:
            print(json.dumps({k: v for k, v in o.items() if k != "candidates"}, ensure_ascii=False, default=str))
        _print_verify(o)
        return {"PASS": 0, "NODATA": 2}.get(o["lamp"], 1)
    return PRIOR.main(args)


def selftest() -> int:
    import contextlib
    import io
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print("=== %s %s · 薄尾自測(db verify 獨立核對 · 候選寫入者;沙盒 · 零網路)===" % (_STEM, TAG))
    td = Path(tempfile.mkdtemp(prefix="vdfmgr157_"))
    keep = {k: os.environ.get(k) for k in ("VIA_VDF_HEALTH_OUT", "VIA_FROM_VCGC", "VIA_DATA_HOME", "VIA_VDF_DB_HOME")}
    try:
        import duckdb
    except ImportError:
        duckdb = None
    try:
        for k in ("VIA_DATA_HOME", "VIA_VDF_DB_HOME"):
            os.environ.pop(k, None)
        out = td / "out"
        out.mkdir()
        os.environ["VIA_VDF_HEALTH_OUT"] = str(out)
        code = td / "code"
        (code / "VDF").mkdir(parents=True)
        (code / "VDF" / "VDF_ENG900_Writer_v0101.py").write_text("x = 1\ncon.execute('CREATE TABLE IF NOT EXISTS tw_nowriter (d DATE)')\n", encoding="utf-8")
        (code / "VDF" / "VDF_ENG900_Writer_v0100.py").write_text("con.execute('INSERT INTO tw_old_only VALUES (1)')\n", encoding="utf-8")
        (code / "VDF" / "VDF_SystemManager_v0999.py").write_text("con.execute('CREATE TABLE tw_nowriter (d DATE)')\n", encoding="utf-8")
        (code / "VDF" / "_archive").mkdir()
        (code / "VDF" / "_archive" / "VRN_ENG901_Old_v0100.py").write_text("con.execute('CREATE TABLE tw_nowriter (d DATE)')\n", encoding="utf-8")
        (code / "VRN").mkdir()
        (code / "VRN" / "VRN_ENG074_FinancialPages_v0114.py").write_text("df.to_sql('vrn_report_basic', con)\n", encoding="utf-8")
        (code / "VRN" / "copy").mkdir()
        (code / "VRN" / "copy" / "VRN_ENG074_FinancialPages_v0114.py").write_text("df.to_sql('vrn_report_basic', con)\n", encoding="utf-8")
        (code / "VDF" / "test_via_x_v0100.py").write_text("con.execute('CREATE TABLE tw_nowriter (d DATE)')\n", encoding="utf-8")
        v2s = {"VRN_ENG074"}
        cands = writer_candidates(["tw_nowriter", "tw_old_only", "vrn_report_basic", "tw_ghost"], v2s, roots=(code,))
        chk("① 候選寫入者:只掃家族尾版(舊版 · 底線夾不算)· 排除管理員自測沙盒與測試檔 · 同名副本只記一次;列 系統 · 檔:行;找不到 = 空(不猜)",
            cands["tw_nowriter"] == [{"檔": "VDF_ENG900_Writer_v0101.py", "行": 2, "系統": "VDF"}] and cands["tw_old_only"] == []
            and cands["vrn_report_basic"] == [{"檔": "VRN_ENG074_FinancialPages_v0114.py", "行": 1, "系統": "VRN-2"}] and cands["tw_ghost"] == [], cands)
        if duckdb is None:
            chk("⑦ duckdb 不在本境 → 只驗候選與 NODATA(不代裝)", verify(td / "none", write=False)["lamp"] == "NODATA")
        else:
            home = td / "home" / "mega"
            home.mkdir(parents=True)
            reg = td / "reg"
            reg.mkdir()
            con = duckdb.connect(str(home / "vdf_tw_market.duckdb"))
            con.execute("create table tw_daily_prices(date date, v int)")
            con.execute("insert into tw_daily_prices values (current_date, 1), (current_date - 1, 2)")
            con.execute("create table tw_empty0(date date)")
            con.execute("create table tw_old(date date)")
            con.execute("insert into tw_old values ('2020-01-02')")
            con.execute("create table extra_tbl(x int)")
            con.close()
            (home / "vdf_broken.duckdb").write_bytes(b"not a duckdb file" * 64)     # 打不開的庫:他系統表照樣標 INFO(PR #538 Codex P2)
            book = [{"db": "vdf_tw_market.duckdb", "table": "tw_daily_prices", "writers": ["VDF_ENG073"], "min_rows": 1},
                    {"db": "vdf_broken.duckdb", "table": "cgc_gate_log", "writers": ["CGC_MDL149"], "min_rows": 1},
                    {"db": "vdf_broken.duckdb", "table": "tw_broken", "writers": ["VDF_ENG073"], "min_rows": 1},
                    {"db": "vdf_tw_market.duckdb", "table": "tw_empty0", "writers": ["VDF_ENG082"], "min_rows": 0},
                    {"db": "vdf_tw_market.duckdb", "table": "tw_old", "writers": ["VDF_ENG056"], "min_rows": 1},
                    {"db": "vdf_tw_market.duckdb", "table": "tw_missing", "writers": ["VDF_ENG056"], "min_rows": 1},
                    {"db": "vdf_tw_market.duckdb", "table": "vrn_report_arith_check", "writers": ["VRN_ENG074"], "min_rows": 0},
                    {"db": "vdf_tw_market.duckdb", "table": "vrn_report_basic", "writers": [], "min_rows": 1},
                    {"db": "vdf_hub.duckdb", "table": "digest_vdf_rows", "writers": ["VDF_ENG045"], "min_rows": 1}]
            (reg / "VIA_DB_Table_SSOT_v0100.json").write_text(json.dumps({"tables": book}), encoding="utf-8")
            o = PRIOR.db_check(str(td / "home"), reg)
            v = verify(out, reg, roots=(code,))
            rows_o = {r["表"]: r for r in o["rows"]}
            chk("② 真庫:db check 寫的清點,本版自己重推每列每欄 → 0 差異 = PASS(含缺庫 · 缺表 · 空表 · 過舊 · 最少 0 列 · 他系統 · 冊外表 · 庫打不開:VDF 表紅、他系統表 INFO)",
                v["lamp"] == "PASS" and v["rows_compared"] == 10 and v["fields_compared"] == 50 and not v["mismatches"]
                and rows_o["cgc_gate_log"]["燈"] == "INFO" and "庫打不開" in rows_o["cgc_gate_log"]["狀態"] and rows_o["tw_broken"]["燈"] == "RED"
                and v["check_ts"] == o["ts"] and Path(v["files"]["html"]).is_file(), (v["lamp"], v["mismatches"][:3], v["rows_compared"]))
            j = out / "DB_CHECK_latest.json"
            orig = j.read_text(encoding="utf-8")
            kinds = {}
            for name, mut in (("列數", lambda d: d["rows"][[r["表"] for r in d["rows"]].index("tw_daily_prices")].update({"列數": 3})),
                              ("燈", lambda d: d["rows"][[r["表"] for r in d["rows"]].index("tw_old")].update({"燈": "GREEN"})),
                              ("狀態", lambda d: d["rows"][[r["表"] for r in d["rows"]].index("vrn_report_basic")].update({"狀態": "他系統表(VRN-2 寫)· 缺表"})),
                              ("(列)", lambda d: d["rows"].pop()),
                              ("summary", lambda d: d["summary"].update({"RED": 99}))):
                d = json.loads(orig)
                mut(d)
                j.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
                vv = verify(out, reg, roots=(code,), write=False)
                kinds[name] = vv["lamp"] == "FAIL" and any(m["欄"] == name for m in vv["mismatches"])
            j.write_text(orig, encoding="utf-8")
            chk("③ 竄改清點就抓得到:列數 · 燈 · 狀態(他系統分類)· 少一列 · 摘要計數 → 各自 FAIL 並點名那一欄", all(kinds.values()), kinds)
            os.environ["VIA_FROM_VCGC"] = "YES"
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                keep_reg = DB_MOD.REG
                DB_MOD.REG = reg
                try:
                    rc = main(["db", "verify", "--json"])
                finally:
                    DB_MOD.REG = keep_reg
            s = buf.getvalue()
            chk("④ db verify 動詞:印 JSON 與「[計] VDF db verify · 10 表 × 5 欄 = 50 欄比對 · 差異 0 … PASS」;rc 0;候選寫入者一行",
                rc == 0 and json.loads(s.splitlines()[0])["lamp"] == "PASS" and "[計] VDF db verify · 10 表 × 5 欄 = 50 欄比對 · 差異 0" in s
                and "[候選寫入者]" in s, s[-400:])
            (out / "DB_CHECK_latest.json").unlink()
            with contextlib.redirect_stdout(io.StringIO()):
                rc2 = main(["db", "verify"])
            chk("⑤ 沒有本輪 check 結果 → NODATA rc 2(不冒充)", rc2 == 2)
        src = Path(__file__).read_text(encoding="utf-8")
        imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
        body_src = src[src.index("# ---------------------------------------------------------------- 獨立重推"):src.index("def _write_verify")]
        chk("⑥ 獨立:重推段不呼叫 db check 的函式(db_check · _find_db · split_rows · min0_rows · other_system);加速器橋 · 網路橋在;"
            "不匯入他系統程式;不碰 TA-Lib;同意閘不寫",
            not re.search(r"\b(db_check|_find_db|split_rows|min0_rows|other_system)\(", body_src)
            and "VIA:ACCEL-BRIDGE" in src and "def _via_net" in src
            and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VRN2_", "VCGC"))]
            and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
            and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src))
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(td, ignore_errors=True)
    print("  [計] %s %s 本版 %d/%d · %s" % (_STEM, TAG, p, p + f, "PASS" if not f else "FAIL"))
    if f:
        return 1
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    return 0 if prc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
