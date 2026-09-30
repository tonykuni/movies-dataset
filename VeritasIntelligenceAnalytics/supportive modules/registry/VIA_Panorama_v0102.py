#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_Panorama v0102 — 全函式記錄 + 教訓學習(LESSONS LEARNED)· 八個本機免費函式庫(薄尾;前版 v0101 → 本體 v0100)

操作員(側線 2026-09-30):「ADD LOGGING FOR ALL · LESSON = LEARN FUNCTION · AND TOP 8 LOCAL FREE LIBS TO BUILD UP THE FUNCTION」
一 · 全函式記錄:v0100 / v0101 的每個函式(含 LocalSource / GitHubSource 方法)都包一層計時與例外記錄;
     panorama.log(JSON 行 · 1 MB × 5 輪替)。熱路徑(每檔一次的呼叫)只累計,不逐筆寫(VIA_PANORAMA_LOG_LEVEL=DEBUG 才逐筆);
     每輪收尾寫一行「函式耗時總表」,儀表板列前 12。例外一律 ERROR(函式名 · 型別 · 訊息;不含原文)。
二 · 教訓學習:每次真的重掃(etag 變)就把前一份與這一份逐列比對(B–F 段),只增寫 lessons.jsonl:
     FIXED 修好 · NEW 新問題 · REGRESSED 修好後又壞 · ESCALATED / EASED 變重 / 變輕 · VERDICT 總判變 · RETROGRESS 棘輪
     · DEGRADE 引擎降級 · PERF 掃描變慢(中位數 + 3×MAD)· BASELINE 首輪基準(一筆摘要,不灌 98 筆 NEW)。
     學習 = 從整本教訓帳算:再犯排行 · 修了又壞(UNSTABLE)· 平均修復時間 MTTR · 同輪一起出事的共病群 · 規則式建議。
     輸出:LESSONS_latest.md(交接用摘要)· lessons.parquet(封存)· 儀表板四張新卡;`lessons` 動詞印 ≤ 12 行卡(省 Token)。
     目標樹裡檔名含 lesson 的 json/jsonl(例:VIA 的中央教訓帳)只讀列出:筆數 · 各類 · 末筆。本引擎不寫它們。
三 · 八個本機免費函式庫(都已裝;缺哪個就標 ABSENT 並退回標準庫,不裝套件、不假綠):
     duckdb(MIT)查詢 · pyarrow(Apache-2.0)封存 · pandas(BSD-3)MTTR · numpy(BSD-3)異常 · networkx(BSD-3)共病群
     · psutil(BSD-3)系統量測 · jinja2(BSD-3)交接報告 · plotly(MIT)教訓圖。
只讀規則同 v0100:不寫目標、不執行目標;教訓與記錄只落輸出夾;不放原文(只有 段:項 · 燈 · 時間 · 簽名)。
用法:VIA_Panorama_v0102.py [scan …] | watch --interval 30 | dashboard | lessons [--out 夾] | --selftest
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

import functools
import hashlib
import html as _html
import importlib
import importlib.util
import inspect
import json
import logging
import logging.handlers
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR_NAME = "VIA_Panorama_v0101.py"  # 釘名:前版(它再釘本體 v0100);不自己取尾版
_spec = importlib.util.spec_from_file_location("VIA_Panorama_v0101", HERE / PRIOR_NAME)
V101 = importlib.util.module_from_spec(_spec)
sys.modules["VIA_Panorama_v0101"] = V101
_spec.loader.exec_module(V101)
BASE = V101.PRIOR  # 本體 v0100
PRIOR = V101
globals().update({k: v for k, v in vars(V101).items() if not k.startswith("_") and k not in ("main", "selftest", "VERSION", "ENGINE", "HERE", "PRIOR", "PRIOR_NAME")})


def __getattr__(name: str):
    """PEP 562:本版沒有的名稱轉給前版 v0101(它再轉本體 v0100)。"""
    try:
        return getattr(V101, name)
    except AttributeError:
        raise AttributeError(f"{__name__} 與前版都沒有 {name}") from None


VERSION = "v0102"
ENGINE = Path(__file__).stem
LESSONS = "lessons.jsonl"
LESSONS_MD = "LESSONS_latest.md"
LESSONS_PQ = "lessons.parquet"
LOG_FILE = "panorama.log"
TRACK = "BCDEF"
BAD = ("RED", "YELLOW", "ABSENT")
BROKE = ("NEW", "REGRESSED", "ESCALATED")
KIND_TEXT = {"FIXED": "修好", "NEW": "新問題", "REGRESSED": "修好後又壞", "ESCALATED": "變重", "EASED": "變輕", "VERDICT": "總判變",
             "RETROGRESS": "棘輪退步", "DEGRADE": "引擎降級", "PERF": "掃描變慢", "BASELINE": "首輪基準"}

# ───────────────────────── 八個本機免費函式庫 ─────────────────────────
LIBS = [("duckdb", "MIT", "查詢:教訓帳 SQL 聚合(再犯 · 排行 · 各類)"),
        ("pyarrow", "Apache-2.0", "封存:教訓帳 Parquet 快照(欄式壓縮)"),
        ("pandas", "BSD-3", "學習:每個項目的修復時間 MTTR"),
        ("numpy", "BSD-3", "偵測:掃描秒數異常(中位數 + 3×MAD)"),
        ("networkx", "BSD-3", "關聯:同輪一起出事 → 共病群(疑似同一根因)"),
        ("psutil", "BSD-3", "系統:CPU · 記憶體 · 磁碟 · 行程 RSS"),
        ("jinja2", "BSD-3", "報告:LESSONS_latest.md 交接摘要"),
        ("plotly", "MIT", "視覺:儀表板教訓圖(js 由 v0101 就地供應)")]
_LIBC: dict = {}


def lib(name: str):
    """回模組或 None(缺席照實;不裝套件)。"""
    if name not in _LIBC:
        try:
            _LIBC[name] = importlib.import_module(name)
        except Exception as e:
            _LIBC[name] = None
            BASE.note(f"函式庫 {name} 缺席,退回標準庫:{type(e).__name__}")
    return _LIBC[name]


def lib_status() -> list:
    out = []
    for name, lic, role in LIBS:
        m = lib(name)
        out.append({"lib": name, "版本": getattr(m, "__version__", "?") if m else "—", "授權": lic, "用途": role,
                    "lamp": "GREEN" if m else "ABSENT"})
    return out


# ───────────────────────── 全函式記錄 ─────────────────────────
LOG = logging.getLogger("via_panorama")
STATS: dict = {}
_LOCK = threading.Lock()
_INSTRUMENTED: list = []


class _JsonFmt(logging.Formatter):
    def format(self, r):
        d = {"ts": datetime.fromtimestamp(r.created, timezone.utc).isoformat(timespec="milliseconds"), "lvl": r.levelname, "msg": r.getMessage()}
        d.update(getattr(r, "extra_json", {}) or {})
        return json.dumps(d, ensure_ascii=False)


def setup_logging(out: Path) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    path = out / LOG_FILE
    for h in list(LOG.handlers):
        if getattr(h, "_via_path", None) == str(path):
            return path
        LOG.removeHandler(h)
        h.close()
    h = logging.handlers.RotatingFileHandler(path, maxBytes=1024 * 1024, backupCount=5, encoding="utf-8")
    h._via_path = str(path)
    h.setFormatter(_JsonFmt())
    LOG.addHandler(h)
    LOG.setLevel(getattr(logging, os.environ.get("VIA_PANORAMA_LOG_LEVEL", "INFO").upper(), logging.INFO))
    LOG.propagate = False
    return path


def logged(fn, name: str):
    """計時 · 計次 · 例外記錄(不吞:照原樣往上丟)。"""
    if getattr(fn, "_via_logged", False):
        return fn

    @functools.wraps(fn)
    def w(*a, **k):
        t = time.perf_counter()
        err = None
        try:
            return fn(*a, **k)
        except Exception as e:
            err = e
            LOG.error(f"{name} 例外", extra={"extra_json": {"fn": name, "err": type(e).__name__, "detail": str(e)[:200]}})
            raise
        finally:
            dt = time.perf_counter() - t
            with _LOCK:
                s = STATS.setdefault(name, [0, 0.0, 0, 0.0])
                s[0] += 1
                s[1] += dt
                s[2] += 1 if err is not None else 0
                s[3] = max(s[3], dt)
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug(f"{name} {dt * 1000:.1f}ms", extra={"extra_json": {"fn": name, "ms": round(dt * 1000, 2)}})
    w._via_logged = True
    return w


def instrument() -> int:
    """把 v0100 · v0101 · 本版的每個函式(與來源類別的方法)包上記錄;冪等。回包了幾個。"""
    if _INSTRUMENTED:
        return _INSTRUMENTED[0]
    n = 0
    me = sys.modules[__name__]
    for mod, tag in ((BASE, "v0100"), (V101, "v0101"), (me, "v0102")):
        for name, obj in list(vars(mod).items()):
            if (inspect.isfunction(obj) and obj.__module__ == mod.__name__ and not name.startswith("__")
                    and name not in ("logged", "instrument", "setup_logging", "_emit_stats", "selftest", "main")):
                setattr(mod, name, logged(obj, f"{tag}.{name}"))
                n += 1
    for cls in (BASE.LocalSource, BASE.GitHubSource):
        for meth in ("listing", "read", "sha256", "exists", "prefetch", "close"):
            f = cls.__dict__.get(meth)
            if inspect.isfunction(f):
                setattr(cls, meth, logged(f, f"v0100.{cls.__name__}.{meth}"))
                n += 1
    _INSTRUMENTED.append(n)
    return n


def top_stats(n: int = 12) -> list:
    with _LOCK:
        items = sorted(STATS.items(), key=lambda kv: -kv[1][1])[:n]
    return [{"函式": k, "次": v[0], "總 ms": round(v[1] * 1000, 1), "最長 ms": round(v[3] * 1000, 1), "錯": v[2]} for k, v in items]


def _emit_stats(tag: str) -> None:
    LOG.info(f"{tag} 函式耗時總表", extra={"extra_json": {"stats": top_stats(40), "wrapped": _INSTRUMENTED[0] if _INSTRUMENTED else 0}})


# ───────────────────────── 系統量測(psutil) ─────────────────────────

def system_metrics(out: Path) -> dict:
    ps = lib("psutil")
    if ps is None:
        return {"lamp": "ABSENT"}
    try:
        vm = ps.virtual_memory()
        du = ps.disk_usage(str(out))
        pr = ps.Process()
        la = os.getloadavg() if hasattr(os, "getloadavg") else (0, 0, 0)
        return {"lamp": "GREEN", "cpu%": ps.cpu_percent(interval=0.1), "cpus": ps.cpu_count(), "mem%": vm.percent,
                "mem_avail_gb": round(vm.available / 2 ** 30, 1), "disk_free_gb": round(du.free / 2 ** 30, 1), "disk%": du.percent,
                "rss_mb": round(pr.memory_info().rss / 2 ** 20, 1), "load1": round(la[0], 2)}
    except Exception as e:
        BASE.note(f"psutil 量測失敗:{e}")
        return {"lamp": "YELLOW", "err": str(e)[:80]}


# ───────────────────────── 教訓:比對 ─────────────────────────

def _rows(rep: dict) -> dict:
    out = {}
    for k in TRACK:
        for r in (rep.get("sections", {}).get(k) or {}).get("rows", []):
            if r.get("lamp") != "HOLD":
                out[f"{k}:{r.get('key')}"] = (r.get("lamp"), str(r.get("value") or r.get("note") or r.get("first_missing") or "")[:80])
    return out


def read_lessons(out: Path, tkey: str | None = None) -> list:
    rows = BASE.read_ledger(out / LESSONS)
    return [x for x in rows if tkey is None or x.get("target_key") == tkey]


def derive(old: dict | None, new: dict, out: Path) -> list:
    """前一份 vs 這一份 → 教訓列(只在真的重掃時;304 不產生)。"""
    now = BASE.now_utc()
    base = {"ts": now, "run": f"{new.get('run')}:{str(new.get('etag', ''))[:6]}", "target_key": new.get("target_key"), "target": new.get("target"),
            "sha16": new.get("sha16"), "etag": new.get("etag")}
    past = read_lessons(out, new.get("target_key"))
    if not old or old.get("target_key") != new.get("target_key") or not past:
        if old and old.get("etag") == new.get("etag") and past:
            return []
        rows = _rows(new)
        bad = sum(1 for v in rows.values() if v[0] in BAD)
        return [dict(base, kind="BASELINE", key="*", section="*", **{"from": "", "to": new.get("verdict")},
                     note=f"首輪基準:非綠 {bad} 列(之後只記變化)", sig="baseline")]
    if old.get("etag") == new.get("etag"):
        return []
    ever_fixed = {x["key"] for x in past if x.get("kind") == "FIXED"}
    a, b = _rows(old), _rows(new)
    out_l = []
    for key in sorted(set(a) | set(b)):
        fa, fb = a.get(key, (None, ""))[0], b.get(key, (None, ""))[0]
        kind = None
        if fa in BAD and fb not in BAD:
            kind = "FIXED"
        elif fb in BAD and fa not in BAD:
            kind = "REGRESSED" if key in ever_fixed else "NEW"
        elif fa in BAD and fb in BAD and fa != fb:
            kind = "ESCALATED" if BASE.SEVER.get(fb, 0) > BASE.SEVER.get(fa, 0) else "EASED"
        if kind:
            out_l.append(dict(base, kind=kind, key=key, section=key[0], **{"from": fa or "—", "to": fb or "—"},
                              note=(b.get(key) or a.get(key))[1], sig=hashlib.sha1(key.encode()).hexdigest()[:12]))
    if old.get("verdict") != new.get("verdict"):
        out_l.append(dict(base, kind="VERDICT", key="總判", section="*", **{"from": old.get("verdict"), "to": new.get("verdict")},
                          note="", sig="verdict"))
    g = (new.get("sections", {}).get("G") or {}).get("summary", {})
    if g.get("verdict") == "RETROGRESS":
        out_l.append(dict(base, kind="RETROGRESS", key="G:棘輪", section="G", **{"from": str(g.get("prev")), "to": str(g.get("now"))},
                          note="紅數比上一筆多", sig="ratchet"))
    for nmsg in [m for m in BASE.NOTES if not m.startswith("函式庫 ")]:  # 函式庫缺席看八函式庫表,不每輪記教訓
        out_l.append(dict(base, kind="DEGRADE", key="H:引擎降級", section="H", **{"from": "", "to": "YELLOW"}, note=nmsg[:80],
                          sig=hashlib.sha1(nmsg[:40].encode()).hexdigest()[:12]))
    perf = perf_anomaly(out, new)
    if perf:
        out_l.append(dict(base, kind="PERF", key="A:掃描秒數", section="A", **{"from": perf["median"], "to": perf["now"]},
                          note=f"中位數 {perf['median']}s · MAD {perf['mad']} · 門檻 {perf['limit']}s", sig="perf"))
    return out_l


def perf_anomaly(out: Path, rep: dict) -> dict | None:
    """numpy:本輪秒數 > 中位數 + 3×MAD(且 > 2 秒)= 異常;缺 numpy 退回 statistics。"""
    hist = [x.get("sec", 0) for x in BASE.read_ledger(out / "universal_ledger.jsonl") if x.get("target_key") == rep.get("target_key")][:-1]
    if len(hist) < 5:
        return None
    np = lib("numpy")
    if np is not None:
        arr = np.asarray(hist[-30:], dtype=float)
        med = float(np.median(arr))
        mad = float(np.median(np.abs(arr - med)))
    else:
        import statistics
        med = statistics.median(hist[-30:])
        mad = statistics.median([abs(x - med) for x in hist[-30:]])
    lim = round(med + 3 * max(mad, 0.5), 1)
    now = float(rep.get("sec") or 0)
    return {"median": round(med, 1), "mad": round(mad, 2), "limit": lim, "now": now} if now > lim and now > 2 else None


def append_lessons(out: Path, rows: list) -> int:
    if not rows:
        return 0
    with open(out / LESSONS, "a", encoding="utf-8") as f:  # 只增
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    for r in rows:
        lvl = logging.WARNING if r["kind"] in BROKE + ("RETROGRESS", "PERF") else logging.INFO
        LOG.log(lvl, f"教訓 {r['kind']} {r['key']}", extra={"extra_json": {"lesson": {k: r[k] for k in ("kind", "key", "from", "to", "sig")}}})
    return len(rows)


# ───────────────────────── 教訓:學習 ─────────────────────────

def learn(out: Path, tkey: str, use_duckdb: bool = True) -> dict:
    rows = read_lessons(out, tkey)
    res = {"n": len(rows), "kinds": {}, "top": [], "mttr": {}, "clusters": [], "advice": [], "engine": "stdlib", "recent": rows[-25:][::-1]}
    if not rows:
        return res
    ddb = lib("duckdb") if use_duckdb else None
    if ddb is not None:
        try:
            con = ddb.connect()
            con.execute("CREATE TABLE L AS SELECT * FROM read_json_auto(?, format='newline_delimited', union_by_name=true)",
                        [str(out / LESSONS)])
            q = "WHERE target_key = ?"
            res["kinds"] = dict(con.execute(f"SELECT kind, count(*) FROM L {q} GROUP BY kind ORDER BY 2 DESC", [tkey]).fetchall())
            top = con.execute(f"""SELECT key, count(*) FILTER (WHERE kind IN ('NEW','REGRESSED','ESCALATED')) AS broke,
                                         count(*) FILTER (WHERE kind = 'FIXED') AS fixed,
                                         count(*) FILTER (WHERE kind = 'REGRESSED') AS regressed, max(ts) AS last
                                  FROM L {q} AND key NOT IN ('*', '總判') GROUP BY key
                                  HAVING broke + fixed > 0 ORDER BY broke DESC, regressed DESC, last DESC, key ASC LIMIT 10""", [tkey]).fetchall()
            res["top"] = [{"key": k, "broke": b, "fixed": f, "regressed": r, "last": str(l)[:19]} for k, b, f, r, l in top]
            res["engine"] = f"duckdb {ddb.__version__}"
            con.close()
        except Exception as e:
            BASE.note(f"duckdb 查詢失敗,退回標準庫:{e}")
            ddb = None
    if ddb is None:
        kinds, per = {}, {}
        for x in rows:
            kinds[x["kind"]] = kinds.get(x["kind"], 0) + 1
            if x.get("key") in ("*", "總判"):
                continue
            p = per.setdefault(x["key"], {"key": x["key"], "broke": 0, "fixed": 0, "regressed": 0, "last": ""})
            p["broke"] += x["kind"] in BROKE
            p["fixed"] += x["kind"] == "FIXED"
            p["regressed"] += x["kind"] == "REGRESSED"
            p["last"] = max(p["last"], str(x.get("ts", ""))[:19])
        res["kinds"] = dict(sorted(kinds.items(), key=lambda kv: -kv[1]))
        cand = sorted((p for p in per.values() if p["broke"] + p["fixed"]), key=lambda p: p["key"])  # 同 SQL 次序:壞↓ 又壞↓ 最後↓ 項↑
        cand.sort(key=lambda p: p["last"], reverse=True)
        cand.sort(key=lambda p: (-p["broke"], -p["regressed"]))
        res["top"] = cand[:10]
    res["mttr"] = mttr(rows)
    res["clusters"] = clusters(rows)
    res["advice"] = advice(res, rows)
    return res


def mttr(rows: list) -> dict:
    """pandas:每個項目從壞(NEW/REGRESSED)到下一次 FIXED 的時間;回 中位數 · 平均 · 次數 · 最慢 5 項。"""
    pairs = []
    opened = {}
    for x in sorted(rows, key=lambda r: r.get("ts", "")):
        k = x.get("key")
        if x["kind"] in ("NEW", "REGRESSED") and k not in opened:
            opened[k] = x["ts"]
        elif x["kind"] == "FIXED" and k in opened:
            t0 = datetime.fromisoformat(opened.pop(k))
            pairs.append({"key": k, "sec": (datetime.fromisoformat(x["ts"]) - t0).total_seconds()})
    if not pairs:
        return {"n": 0, "open": len(opened)}
    pd = lib("pandas")
    if pd is not None:
        df = pd.DataFrame(pairs)
        g = df.groupby("key")["sec"].mean().sort_values(ascending=False).head(5)
        return {"n": int(len(df)), "median_s": round(float(df["sec"].median()), 1), "mean_s": round(float(df["sec"].mean()), 1),
                "slowest": [{"key": k, "mean_s": round(float(v), 1)} for k, v in g.items()], "open": len(opened), "engine": "pandas"}
    import statistics
    secs = [p["sec"] for p in pairs]
    return {"n": len(pairs), "median_s": round(statistics.median(secs), 1), "mean_s": round(sum(secs) / len(secs), 1),
            "slowest": sorted(({"key": p["key"], "mean_s": round(p["sec"], 1)} for p in pairs), key=lambda d: -d["mean_s"])[:5],
            "open": len(opened), "engine": "stdlib"}


def clusters(rows: list) -> list:
    """networkx:同一輪一起壞的項目連邊 → 連通群(≥ 2 項)= 疑似同一根因;缺 networkx 退回聯集找根。"""
    by_run = {}
    for x in rows:
        if x["kind"] in BROKE and x.get("key") not in ("*", "總判"):
            by_run.setdefault(x.get("run"), set()).add(x["key"])
    edges = [(a, b) for ks in by_run.values() for a in ks for b in ks if a < b]
    nx = lib("networkx")
    if nx is not None:
        g = nx.Graph()
        g.add_edges_from(edges)
        comps = [sorted(c) for c in nx.connected_components(g) if len(c) >= 2]
    else:
        parent = {}

        def find(x):
            while parent.setdefault(x, x) != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        for a, b in edges:
            parent[find(a)] = find(b)
        groups = {}
        for k in parent:
            groups.setdefault(find(k), []).append(k)
        comps = [sorted(v) for v in groups.values() if len(v) >= 2]
    return sorted(comps, key=len, reverse=True)[:5]


def advice(res: dict, rows: list) -> list:
    out = []
    for t in res["top"]:
        if t["regressed"] >= 1 and t["fixed"] >= 1:
            out.append(f"UNSTABLE · {t['key']}:修好後又壞 {t['regressed']} 次 → 補守門或測試,讓修正留得住")
    for c in res["clusters"][:3]:
        if len(c) >= 3:
            out.append(f"共病群 · {len(c)} 項同輪出事({' · '.join(c[:4])}{' …' if len(c) > 4 else ''})→ 先查共同根因,別逐項修")
    k = res["kinds"]
    if k.get("PERF", 0) >= 2:
        out.append(f"PERF · 掃描變慢 {k['PERF']} 次 → 看 A 段大檔 / 是否常開 --static")
    if k.get("DEGRADE", 0):
        out.append(f"DEGRADE · 引擎降級 {k['DEGRADE']} 次 → 看 H 段『引擎降級』與 panorama.log")
    if k.get("RETROGRESS", 0):
        out.append(f"RETROGRESS · 棘輪退步 {k['RETROGRESS']} 次 → 本批修改前先跑一次當基準")
    if res["mttr"].get("open"):
        out.append(f"OPEN · 還有 {res['mttr']['open']} 項壞了還沒修好")
    return out or ["目前沒有需要學的:沒有再犯、沒有共病群、沒有退步"]


MD_TMPL = """# LESSONS LEARNED · {{ rep.target }}
- 時間 {{ now }} · profile {{ rep.profile }} · 範圍 {{ rep.scopes|join(',') }} · sha16 `{{ rep.sha16 }}` · 總判 **{{ rep.verdict }}**
- 教訓 {{ L.n }} 筆 · {% for k, v in L.kinds.items() %}{{ k }} {{ v }}{% if not loop.last %} · {% endif %}{% endfor %} · 查詢 {{ L.engine }}
- MTTR:{% if L.mttr.n %}中位數 {{ L.mttr.median_s }}s · 平均 {{ L.mttr.mean_s }}s · {{ L.mttr.n }} 次{% else %}還沒有修好紀錄{% endif %} · 未修 {{ L.mttr.open or 0 }}

## 建議(規則式)
{% for a in L.advice %}- {{ a }}
{% endfor %}
## 再犯排行
| 項 | 壞 | 修好 | 又壞 | 最後 |
|---|---:|---:|---:|---|
{% for t in L.top %}| {{ t.key }} | {{ t.broke }} | {{ t.fixed }} | {{ t.regressed }} | {{ t.last }} |
{% endfor %}
## 共病群
{% for c in L.clusters %}- {{ c|length }} 項:{{ c|join(' · ') }}
{% else %}- (無)
{% endfor %}
## 最近 15 筆
{% for x in L.recent[:15] %}- {{ x.ts[:19] }} · {{ x.kind }} · {{ x.key }} · {{ x['from'] }} → {{ x.to }}
{% endfor %}
_只讀產物:計數 · 段:項 · 燈 · 時間;不含原文。本檔每輪覆寫;完整紀錄在 lessons.jsonl(只增)與 lessons.parquet。_
"""


def write_reports(out: Path, rep: dict, L: dict) -> dict:
    done = {}
    j2 = lib("jinja2")
    if j2 is not None:
        md = j2.Environment(autoescape=False, trim_blocks=False).from_string(MD_TMPL).render(rep=rep, L=L, now=BASE.now_utc())
    else:
        md = (f"# LESSONS LEARNED · {rep.get('target')}\n- 教訓 {L['n']} 筆 · " + " · ".join(f"{k} {v}" for k, v in L["kinds"].items())
              + "\n\n## 建議\n" + "\n".join(f"- {a}" for a in L["advice"]) + "\n")
    (out / LESSONS_MD).write_text(md, encoding="utf-8")
    done["md"] = str(out / LESSONS_MD)
    pa = lib("pyarrow")
    rows = read_lessons(out)
    if pa is not None and rows:
        try:
            import pyarrow.parquet as pq
            cols = sorted({k for r in rows for k in r})
            tbl = pa.Table.from_pylist([{c: (None if r.get(c) is None else str(r.get(c))) for c in cols} for r in rows])
            pq.write_table(tbl, out / LESSONS_PQ)
            done["parquet"] = str(out / LESSONS_PQ)
        except Exception as e:
            BASE.note(f"parquet 封存失敗:{e}")
    return done


# ───────────────────────── 目標樹裡的教訓帳(只讀) ─────────────────────────

def target_lesson_books(rep: dict) -> list:
    if rep.get("source") != "local":
        return []
    root = Path(rep["target"])
    rc, outp, _ = BASE.git(root, "ls-files", "-z", "--", "*[Ll]esson*.json", "*[Ll]esson*.jsonl")
    paths = [p for p in outp.split("\0") if p] if rc == 0 else [str(p.relative_to(root)) for p in root.rglob("*[Ll]esson*.json*")][:20]
    prof = BASE.load_profiles().get(rep.get("profile")) or {}
    paths = [p for p in paths if not BASE._skipped(p, prof)]  # 同 profile 略過規則(退役夾 · 副本 …)
    books = []
    for rel in paths[:6]:
        try:
            txt = (root / rel).read_text(encoding="utf-8-sig")
            if rel.endswith(".jsonl"):
                ents = [json.loads(x) for x in txt.splitlines()[-500:] if x.strip()]
            else:
                d = json.loads(txt)
                ents = d.get("entries") or d.get("lessons") or (d if isinstance(d, list) else [])
                ents = ents if isinstance(ents, list) else list(ents.values())
        except (OSError, ValueError) as e:
            BASE.note(f"教訓帳讀不到:{rel} {type(e).__name__}")
            continue
        kinds = {}
        for x in ents:
            k = str(x.get("kind") or x.get("category") or x.get("type") or "?") if isinstance(x, dict) else "?"
            kinds[k] = kinds.get(k, 0) + 1
        last = [{"kind": str(x.get("kind", ""))[:16], "ts": str(x.get("ts") or x.get("at") or "")[:19],
                 "誰": str(x.get("engine") or x.get("run") or x.get("id") or "")[:40], "判": str(x.get("verdict") or x.get("lamp") or "")[:8]}
                for x in ents[-8:][::-1] if isinstance(x, dict)]
        if not ents:
            continue
        books.append({"path": rel, "n": len(ents), "kinds": sorted(kinds.items(), key=lambda kv: -kv[1])[:6], "last": last})
    return books


# ───────────────────────── 儀表板加卡 ─────────────────────────

def extra_cards(out: Path, rep: dict, L: dict, sysm: dict, books: list) -> tuple:
    e = _html.escape
    tbl, pill = V101.tbl, V101.pill

    def card(title, body, count=""):
        return f"<div class='card'><h2>{e(title)}<span class='c'>{e(count)}</span></h2>{body}</div>"
    kinds = " · ".join(f"{e(KIND_TEXT.get(k, k))} {v}" for k, v in L["kinds"].items()) or "(還沒有教訓)"
    recent = [{"時間": str(x.get("ts", ""))[5:19].replace("T", " "), "類": x.get("kind", ""), "項": x.get("key", ""),
               "變化": f"{x.get('from', '')} → {x.get('to', '')}", "說明": x.get("note", "")} for x in L["recent"]]
    top = [{"項": t["key"], "壞": t["broke"], "修好": t["fixed"], "又壞": t["regressed"], "最後": t["last"][5:]} for t in L["top"]]
    m = L["mttr"]
    mt = f"MTTR 中位數 {m.get('median_s')}s · 平均 {m.get('mean_s')}s · {m.get('n')} 次" if m.get("n") else "MTTR:還沒有修好紀錄"
    adv = "".join(f"<li>{e(a)}</li>" for a in L["advice"])
    cl = "".join(f"<li>{len(c)} 項:{e(' · '.join(c[:6]))}{' …' if len(c) > 6 else ''}</li>" for c in L["clusters"]) or "<li>(無)</li>"
    sysrows = [{"量": k, "值": v} for k, v in sysm.items() if k != "lamp"]
    bk = "".join(f"<div class='meta' style='margin:4px 0 2px;overflow-wrap:anywhere'><span class='mono'>{e(b['path'])}</span> · {b['n']} 筆 · "
                 + " · ".join(f"{e(k)} {v}" for k, v in b["kinds"]) + "</div>"
                 + tbl(["kind", "ts", "誰", "判"], b["last"], lamp_cols=(), widths=["110px", "130px", "auto", "60px"]) for b in books) \
        or "<div class='nop'>目標樹裡沒有檔名含 lesson 的 json/jsonl</div>"
    html = ("<div class='grid'>"
            + card("LESSONS LEARNED · 本引擎", f"<div class='meta' style='margin-bottom:4px'>{kinds} · 查詢 {e(L['engine'])}</div>"
                   + tbl(["時間", "類", "項", "變化", "說明"], recent, lamp_cols=(), widths=["88px", "80px", "30%", "92px", "auto"]), f"{L['n']} 筆")
            + card("學習:再犯排行 · 建議", f"<div class='meta' style='margin-bottom:4px'>{e(mt)}</div>"
                   + tbl(["項", "壞", "修好", "又壞", "最後"], top, lamp_cols=(), num_cols=("壞", "修好", "又壞"),
                         widths=["auto", "40px", "44px", "44px", "110px"])
                   + f"<ul style='margin:6px 0 0 16px;padding:0'>{adv}</ul>")
            + card("教訓 × 輪", "<div id='fig_lessons' class='plot'></div>"
                   + f"<div class='meta' style='margin-top:4px'>共病群(同輪一起壞)</div><ul style='margin:2px 0 0 16px;padding:0'>{cl}</ul>")
            + "</div><div class='grid'>"
            + card("目標樹裡的教訓帳(只讀)", bk, f"{len(books)} 本")
            + card("SYSTEM · psutil", tbl(["量", "值"], sysrows, lamp_cols=(), widths=["45%", "auto"]) if sysrows else "<div class='nop'>psutil 缺席</div>",
                   sysm.get("lamp", ""))
            + card("函式耗時 前 12(全函式記錄)", tbl(["函式", "次", "總 ms", "最長 ms", "錯"], top_stats(12), lamp_cols=(),
                                                  num_cols=("次", "總 ms", "最長 ms", "錯"), widths=["auto", "40px", "58px", "58px", "26px"]),
                   f"包 {_INSTRUMENTED[0] if _INSTRUMENTED else 0} 個 · {LOG_FILE}")
            + card("八個本機免費函式庫", tbl(["lib", "lamp", "用途", "授權", "版本"], lib_status(), widths=["62px", "84px", "auto", "74px", "44px"]))
            + "</div>")
    runs = {}
    for x in read_lessons(out, rep.get("target_key")):
        r = runs.setdefault(x.get("run"), {"at": str(x.get("ts", ""))[5:19].replace("T", " "), "fix": 0, "broke": 0})
        r["fix"] += x["kind"] == "FIXED"
        r["broke"] += x["kind"] in BROKE
    rs = list(runs.values())[-30:]
    lay = {"margin": {"l": 30, "r": 8, "t": 4, "b": 26}, "paper_bgcolor": "#fcfcfb", "plot_bgcolor": "#fcfcfb", "barmode": "group", "bargap": 0.3,
           "bargroupgap": 0.08, "font": {"size": 10, "color": "#52514e"}, "legend": {"orientation": "h", "y": 1.12, "x": 0, "font": {"size": 9}},
           "xaxis": {"gridcolor": "#e1e0d9", "linecolor": "#c3c2b7", "tickfont": {"size": 9}, "nticks": 6},
           "yaxis": {"gridcolor": "#e1e0d9", "linecolor": "#c3c2b7", "tickfont": {"size": 9}, "rangemode": "tozero", "dtick": 1}}
    fig = {"data": [{"type": "bar", "name": "修好 FIXED", "x": [r["at"] for r in rs], "y": [r["fix"] for r in rs], "marker": {"color": "#2a78d6"},
                     "hovertemplate": "%{x}<br>修好 %{y}<extra></extra>"},
                    {"type": "bar", "name": "出事 NEW/REGRESSED/ESCALATED", "x": [r["at"] for r in rs], "y": [r["broke"] for r in rs],
                     "marker": {"color": "#eb6834"}, "hovertemplate": "%{x}<br>出事 %{y}<extra></extra>"}], "layout": lay}
    js = ("<script>(function(){var f=" + json.dumps(fig, ensure_ascii=False) + ",el=document.getElementById('fig_lessons');"
          "if(!el)return;if(window.Plotly){Plotly.newPlot(el,f.data,f.layout,{displayModeBar:false,responsive:true})}"
          "else{el.innerHTML=\"<div class='nop'>沒有 Plotly</div>\"}})();</script>")
    return html, js


def render_page(out: Path, opts: dict, interval: int, L: dict, sysm: dict) -> None:
    ctx = V101.collect(out, opts)
    page = V101.render_dashboard(ctx, interval, V101.ensure_plotly(out))
    add, js = extra_cards(out, ctx["rep"], L, sysm, target_lesson_books(ctx["rep"]))
    page = page.replace("<footer>", add + "<footer>", 1).replace("</body>", js + "</body>", 1)
    page = page.replace("VIA_Panorama v0101(本體 v0100)", f"VIA_Panorama {VERSION}(前版 v0101 · 本體 v0100)· 全函式記錄 {LOG_FILE} · 教訓 {LESSONS}")
    tmp = out / (V101.PAGE_NAME + ".tmp")
    tmp.write_text(page, encoding="utf-8")
    tmp.replace(out / V101.PAGE_NAME)


# ───────────────────────── 動詞 ─────────────────────────

def _latest(out: Path) -> dict | None:
    try:
        return json.loads((out / "panorama_latest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def after_scan(out: Path, old: dict | None) -> tuple:
    new = _latest(out)
    if not new:
        return [], None
    got = derive(old, new, out)
    append_lessons(out, got)
    L = learn(out, new.get("target_key"))
    write_reports(out, new, L)
    return got, L


def one_round(target: str | None, opts: dict, out: Path, interval: int) -> tuple:
    setup_logging(out)
    old = _latest(out)
    BASE.NOTES.clear()
    rc, line = V101.one_round(target, opts, out, interval)
    got, L = after_scan(out, old)
    sysm = system_metrics(out)
    if L is not None:
        render_page(out, opts, interval, L, sysm)
    kinds = {}
    for g in got:
        kinds[g["kind"]] = kinds.get(g["kind"], 0) + 1
    LOG.info("輪", extra={"extra_json": {"rc": rc, "line": line[:160], "lessons": kinds, "system": sysm}})
    _emit_stats("輪")
    return rc, line + (("  教訓 " + " · ".join(f"{k} {v}" for k, v in kinds.items())) if kinds else "")


def dashboard(target: str | None, opts: dict) -> int:
    out = V101.resolve_out(target, opts)
    out.mkdir(parents=True, exist_ok=True)
    rc, line = one_round(target, opts, out, 0)
    print(f"[{ENGINE} dashboard] {line}\n  頁 {out / V101.PAGE_NAME} · 教訓 {out / LESSONS_MD}")
    return rc


def watch(target: str | None, opts: dict) -> int:
    interval = max(5, int(opts.get("interval") or 30))
    rounds = int(opts.get("rounds") or 0)
    out = V101.resolve_out(target, opts)
    out.mkdir(parents=True, exist_ok=True)
    print(f"[{ENGINE} watch] 每 {interval} 秒一輪 · 頁 {out / V101.PAGE_NAME} · 記錄 {out / LOG_FILE}(Ctrl+C 停)")
    n, rc = 0, 2
    try:
        while True:
            n += 1
            t0 = time.time()
            rc, line = one_round(target, opts, out, interval)
            print("  " + line, flush=True)
            if rounds and n >= rounds:
                break
            time.sleep(max(0.0, interval - (time.time() - t0)))
    except KeyboardInterrupt:
        print(f"  停 · {n} 輪")
    return rc


def lessons_card(opts: dict) -> int:
    """省 Token:≤ 12 行;不重掃。"""
    out = Path(opts["out"]).expanduser() if opts.get("out") else None
    cands = [out] if out else [BASE.default_target() / "VIA_Reports" / "panorama", Path.home() / ".via_panorama", Path.cwd() / ".panorama"]
    hits = [c for c in cands if c and (c / "panorama_latest.json").is_file()]
    if not hits:
        print("[VIA_Panorama lessons] 還沒有報告 · NODATA")
        return 2
    o = max(hits, key=lambda p: (p / "panorama_latest.json").stat().st_mtime)
    rep = _latest(o)
    L = learn(o, rep.get("target_key"))
    m = L["mttr"]
    lines = [f"[{ENGINE} lessons] {rep.get('target')} · 教訓 {L['n']} 筆 · " + " · ".join(f"{k} {v}" for k, v in L["kinds"].items())
             + f" · 查詢 {L['engine']}",
             "  MTTR " + (f"中位數 {m['median_s']}s · 平均 {m['mean_s']}s · {m['n']} 次" if m.get("n") else "—") + f" · 未修 {m.get('open', 0)}"]
    lines += [f"  再犯 {t['key']} · 壞 {t['broke']} · 修好 {t['fixed']} · 又壞 {t['regressed']}" for t in L["top"][:4]]
    lines += [f"  建議 {a}" for a in L["advice"][:4]]
    lines.append(f"  全文 {o / LESSONS_MD} · 帳 {o / LESSONS}")
    print("\n".join(lines[:12]))
    return 0


def scan_with_lessons(a: list) -> int:
    """預設 scan 路徑:照 v0100 掃,前後比對寫教訓(不產儀表板)。"""
    rest = a[1:] if a and a[0] == "scan" else a
    opts, pos = BASE.parse_opts(rest)
    target = pos[0] if pos else None
    try:
        out = V101.resolve_out(target, opts)
    except Exception as e:  # 目標讀不到等:照 v0100 原路回報
        BASE.note(f"輸出夾算不出:{e}")
        return BASE.main(a)
    setup_logging(out)
    old = _latest(out)
    BASE.NOTES.clear()
    rc = BASE.main(a)
    got, L = after_scan(out, old)
    _emit_stats("scan")
    if got and not opts.get("json_only"):
        kinds = {}
        for g in got:
            kinds[g["kind"]] = kinds.get(g["kind"], 0) + 1
        print(f"  教訓 +{len(got)}(" + " · ".join(f"{k} {v}" for k, v in kinds.items()) + f")· {out / LESSONS_MD}")
    return rc


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a and a[0] in ("--selftest", "selftest"):
        return selftest()
    instrument()
    if a and a[0] in ("dashboard", "watch"):
        verb, rest = a[0], a[1:]
        extra = {}
        for key in ("--interval", "--rounds"):
            if key in rest:
                i = rest.index(key)
                extra[key[2:]] = int(rest[i + 1]) if i + 1 < len(rest) and rest[i + 1].isdigit() else 0
                del rest[i:i + 2]
        opts, pos = BASE.parse_opts(rest)
        opts.update(extra)
        return (dashboard if verb == "dashboard" else watch)(pos[0] if pos else None, opts)
    if a and a[0] == "lessons":
        return lessons_card(BASE.parse_opts(a[1:])[0])
    if a and a[0] in ("show", "read", "slice", "digest", "pack", "chain", "brief", "verbs", "help", "-h"):
        return BASE.main(a)
    return scan_with_lessons(a)


# ───────────────────────── 自測 ─────────────────────────

def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  {'✓' if cond else '✗'} {name}" + (f" · {note}" if note and not cond else ""))
    import contextlib
    import io
    print(f"=== {ENGINE} 自測(薄尾;先跑前版 v0101 → 本體 v0100)===")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        prc = V101.selftest()
    chk("前版 v0101(含本體 v0100)自測", prc == 0, (buf.getvalue().strip().splitlines() or [""])[-1])
    miss = [k for k in vars(V101) if not k.startswith("_") and k not in globals()]
    chk("尾版不少公開名稱(TAILAPI)", not miss, " · ".join(miss[:5]))
    n = instrument()
    chk("全函式記錄:v0100 + v0101 + v0102 函式與來源方法都包上", n >= 60 and getattr(BASE.scan, "_via_logged", False)
        and getattr(V101.render_dashboard, "_via_logged", False) and getattr(BASE.LocalSource.read, "_via_logged", False), f"包 {n}")
    tmp = Path(tempfile.mkdtemp(prefix="via_pan102_"))
    try:
        t, out = tmp / "t", tmp / "out"
        t.mkdir()
        prof = {"name": "t102", "scopes": {"ALL": ["*"]}, "default_scopes": ["ALL"],
                "markers": [{"id": "MK", "ext": [".py"], "regex": "MARK", "need": True, "severity": "RED", "scopes": ["ALL"]}]}
        pf = tmp / "p.json"
        pf.write_text(json.dumps(prof), encoding="utf-8")
        opts = {"profile": str(pf), "out": str(out), "no_git": True}

        def put(marked: bool):
            for i in range(2):
                (t / f"m{i}.py").write_text('"""m"""\n' + ("# MARK\n" if marked else "") + f"TOP_SECRET = {i}\n", encoding="utf-8")
            time.sleep(0.01)
        seq = [False, True, False, True]
        for marked in seq:
            put(marked)
            with contextlib.redirect_stdout(io.StringIO()):
                dashboard(str(t), opts)
        with contextlib.redirect_stdout(io.StringIO()):
            dashboard(str(t), opts)  # 沒變 → 304 → 不產教訓
        L = read_lessons(out)
        kinds = [x["kind"] for x in L if x["key"] == "C:MK"]
        chk("教訓序列:BASELINE → FIXED → REGRESSED → FIXED;304 不產生", [x["kind"] for x in L][0] == "BASELINE"
            and kinds == ["FIXED", "REGRESSED", "FIXED"], json.dumps([(x["kind"], x["key"]) for x in L], ensure_ascii=False)[:200])
        res = learn(out, L[0]["target_key"])
        res_std = learn(out, L[0]["target_key"], use_duckdb=False)
        chk("學習:C:MK 列為 UNSTABLE(修好後又壞)· MTTR 有值", any("UNSTABLE" in a and "C:MK" in a for a in res["advice"])
            and res["mttr"].get("n", 0) >= 1, json.dumps(res["advice"], ensure_ascii=False)[:160])
        chk("duckdb 與標準庫退路算出同一張再犯排行", [(x["key"], x["broke"], x["fixed"]) for x in res["top"]]
            == [(x["key"], x["broke"], x["fixed"]) for x in res_std["top"]], f"{res['engine']} vs {res_std['engine']}")
        page = (out / V101.PAGE_NAME).read_text(encoding="utf-8")
        md = (out / LESSONS_MD).read_text(encoding="utf-8")
        chk("儀表板加卡:LESSONS · 學習 · 教訓圖 · 教訓帳 · SYSTEM · 函式耗時 · 八函式庫", all(x in page for x in (
            "LESSONS LEARNED", "再犯排行", "fig_lessons", "目標樹裡的教訓帳", "SYSTEM · psutil", "函式耗時", "八個本機免費函式庫")))
        chk("八函式庫逐列標示(有 = GREEN · 缺 = ABSENT)", len(lib_status()) == 8 and all(r["lamp"] in ("GREEN", "ABSENT") for r in lib_status())
            and lib("no_such_lib_via_xyz") is None)
        logl = [json.loads(x) for x in (out / LOG_FILE).read_text(encoding="utf-8").splitlines() if x.strip()]
        chk("panorama.log:JSON 行 · 有教訓行 · 有函式耗時總表(含 v0100.scan)", any("lesson" in x for x in logl)
            and any(any(s["函式"] == "v0100.scan" for s in x.get("stats", [])) for x in logl), f"{len(logl)} 行")
        chk("交接摘要 md + parquet(有 pyarrow 時)", "LESSONS LEARNED" in md and "UNSTABLE" in md
            and ((out / LESSONS_PQ).is_file() or lib("pyarrow") is None))
        chk("不含原文(頁 · md · log · 教訓帳)", all("TOP_SECRET" not in x for x in (
            page, md, (out / LOG_FILE).read_text(encoding="utf-8"), (out / LESSONS).read_text(encoding="utf-8"))))

        def boom():
            raise ValueError("x")
        wb = logged(boom, "t.boom")
        try:
            wb()
            raised = False
        except ValueError:
            raised = True
        chk("記錄層不吞例外(照丟)且計錯", raised and STATS["t.boom"][2] == 1)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"  {ENGINE} selftest {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
