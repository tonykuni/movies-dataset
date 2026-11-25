#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_BooksSync v0100 — 三冊重產器(py 版;取代第五章 Mode C 的 Sync-ViaWikiAndBooks.ps1,倉裡沒有那支)

操作員 2026-11-25:「三冊重產器也寫成 py 版 · 輸入參數整合化管理 · 輸出 dataframe · 參數分類 · 啟動日期統一性設定 · 引擎模塊化 ·
可編輯部份可插入可整合 · ast 導入加速器 · 參數統一管理 · 引擎數量最小最快 · 運作時間列管紀錄 · 一次獨立三步驟進行 · 啟動指令用 py 寫 · ps 啟動」。
三冊 = VIA_Policy_Laws_SSOT · VIA_ToolRoster_SSOT · VIA_VRN_LogicArchitecture_SSOT 的尾版。
  參數   全在 VIA_BooksSync_Params 尾版(run · paths · engines · output 四類);start_date 一處設定、三引擎共用。本檔不寫死參數。
  引擎   一支檔三個引擎(數量最小),同一介面:name · key · book_rows(冊上現況)· current_rows(由程式碼 / 帳本重算)· apply(出新版內容)。
         policy_laws  lessons ← 每日教訓帳(date >= start_date),只增
         tool_roster  envs.*.tools ← 網路工具(AegisNexus 尾版匯入件)補進每個家族境;加速器(Celeritas _LIB_MAP 鍵)本冊四境沒收的列 accelerator_not_in_roster_envs(路由看 Baseline families,不猜境)
         logic_arch   placed_by_batch662 / off_book_pending 的 tail · state ← glob 尾版;role 讀檔頭第一句
         可插入:參數冊 engines 加一列 module=<.py>,外掛先過 ast.parse 再載入,要有同介面的 ENGINE。
  執行   三引擎一次並行(獨立三步),每 20 秒心跳。
  輸出   每引擎三張 DataFrame(book · current · diff;polars,沒有就 pandas)→ <out>/<時間>/<引擎>.<表>.parquet(zstd)+ SUMMARY.json;
         python 呼叫 run() 直接拿到 {引擎: {表: DataFrame}}。
  寫入   預設只檢查(SYNCED / OUT_OF_SYNC)。--apply 才寫:新版號 = max(本機 ∪ origin/main)+1(避開已發布的號)→ 暫存檔原子換名;
         前版一字不動、只增不減(冊上原有的列一列不少);寫前寫後各跑一次 VCGC ssot panorama(主控台不在 = 黃,照寫)。
  運作帳 每次每引擎一列只增到 RUN_LEDGER.jsonl(UTC · 引擎 · 秒 · 列數 · 差異數 · 燈 · 寫了哪個新版 · start_date)。
  網路   三引擎都不對外擷取 → 不接網路工具(CLAUDE.md REQ266:沒有對外擷取的不加)。
用法:python VIA_BooksSync_v0100.py check|apply [--via <VIA 根>] [--params <參數冊>] [--start-date YYYY-MM-DD] [--only a,b] [--out <夾>]
      python VIA_BooksSync_v0100.py --selftest
rc:0 全 SYNCED(或 apply 寫完)· 2 有 OUT_OF_SYNC / 黃 · 1 紅
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] SuperAccel 加速器橋(從 TEMP 跑時改由工作目錄 / VIA_REPO 找倉;graceful) =====
try:
    import os as _sa_os
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_hit = None
    _sa_roots = [_sa_Path(__file__).resolve(), _sa_Path.cwd().resolve()]
    if _sa_os.environ.get("VIA_REPO"):
        _sa_roots.append(_sa_Path(_sa_os.environ["VIA_REPO"]).resolve())
    for _sa_r in _sa_roots:
        for _sa_q in (_sa_r, *_sa_r.parents):
            for _sa_c in (_sa_q / "supportive modules", _sa_q / "VeritasIntelligenceAnalytics" / "supportive modules"):
                if (_sa_c / "VIA_SuperAccel_Module.py").exists():
                    _sa_hit = _sa_c
                    break
            if _sa_hit:
                break
        if _sa_hit:
            break
    if _sa_hit and str(_sa_hit) not in _sa_sys.path:
        _sa_sys.path.insert(0, str(_sa_hit))
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響(自測會把它記成黃)
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import ast
import copy
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path

FAMILY = "VIA_BooksSync"
VERSION = "v0100"
TAG = f"{FAMILY} {VERSION}"
HERE = Path(__file__).resolve()
_T0 = time.time()


def say(msg: str) -> None:
    print(f"[{time.time() - _T0:6.1f}s] {msg}", flush=True)


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


def newest(d: Path, pat: str):
    c = [p for p in d.glob(pat) if _vnum(p) >= 0]
    return max(c, key=_vnum) if c else None


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def find_via(start: Path):
    for q in (start, *start.parents):
        if (q / "supportive modules").is_dir() and (q / "docs").is_dir():
            return q
        if (q / "VeritasIntelligenceAnalytics" / "supportive modules").is_dir():
            return q / "VeritasIntelligenceAnalytics"
    return None


# ---------------------------------------------------------------- 參數(統一管理)
def load_params(via: Path, path=None) -> dict:
    p = Path(path) if path else (newest(via / "docs" / "handoff" / "ai", "VIA_BooksSync_Params_v*.json")
                                 or newest(HERE.parent, "VIA_BooksSync_Params_v*.json"))
    if p is None or not p.is_file():
        raise FileNotFoundError("找不到 VIA_BooksSync_Params 參數冊")
    prm = json.loads(p.read_text(encoding="utf-8"))
    for k in ("run", "paths", "engines", "output"):
        if k not in prm:
            raise ValueError(f"參數冊缺分類 {k}")
    date.fromisoformat(prm["run"]["start_date"])                  # 形不對當場拒絕
    prm["_path"] = str(p)
    return prm


# ---------------------------------------------------------------- DataFrame
FRAME_MISSING: list = []


def frame(rows: list, prm: dict):
    cols = sorted({k for r in rows for k in r}) if rows else ["key"]
    norm = [{c: (json.dumps(r.get(c), ensure_ascii=False) if isinstance(r.get(c), (list, dict)) else r.get(c)) for c in cols} for r in rows]
    for lib in (prm["output"].get("frame", "polars"), prm["output"].get("frame_fallback", "pandas")):
        try:
            if lib == "polars":
                import polars as pl
                return pl.DataFrame(norm, schema={c: pl.Utf8 for c in cols}) if norm else pl.DataFrame(schema={c: pl.Utf8 for c in cols})
            if lib == "pandas":
                import pandas as pd
                return pd.DataFrame(norm, columns=cols).astype("string")
        except ImportError as e:
            FRAME_MISSING.append(f"{lib}: {e}")             # 照實記;兩個都沒有 → 回 None,摘要標黃
    return None


def write_frame(df, path: Path, prm: dict) -> str:
    comp = prm["output"].get("compression", "zstd")
    try:
        if hasattr(df, "write_parquet"):
            df.write_parquet(path, compression=comp)
        else:
            df.to_parquet(path, compression=comp, index=False)
        return "parquet"
    except Exception:  # noqa: BLE001 - 沒有 parquet 寫手(pyarrow)→ 退 jsonl,照實記
        rows = df.to_dicts() if hasattr(df, "to_dicts") else df.to_dict("records")
        path.with_suffix(".jsonl").write_text("".join(json.dumps(r, ensure_ascii=False, default=str) + "\n" for r in rows), encoding="utf-8")
        return "jsonl(退路)"


# ---------------------------------------------------------------- 引擎(同一介面)
def _first_doc_line(p: Path) -> str:
    try:
        d = ast.get_docstring(ast.parse(p.read_text(encoding="utf-8-sig", errors="replace")))
        return (d or "").strip().splitlines()[0][:160] if d else ""
    except SyntaxError:
        return "(SyntaxError)"


class PolicyLaws:
    name, key = "policy_laws", "id"

    def book_rows(self, book, ctx):
        return [{"id": x.get("id"), "batch": x.get("batch"), "cat": x.get("cat"), "zh": x.get("zh")} for x in book.get("lessons", [])]

    def current_rows(self, book, ctx):
        p = ctx["via"] / ctx["prm"]["paths"]["lessons_ledger"]
        rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.is_file() else []
        sd = ctx["start_date"]
        out = []
        for r in rows:
            if str(r.get("date", "")) < sd:
                continue
            zh = f"**{r.get('problem', '')}** 根因:{r.get('cause', '')} · 處理:{r.get('fix', '')} · 防呆:{r.get('guard', '')}"
            if r.get("check"):
                zh += f" · 下次怎麼檢查:{r['check']}"
            out.append({"id": r.get("id"), "batch": f"每日教訓帳 {r.get('date', '')}", "cat": "每日教訓", "zh": zh})
        return self.book_rows(book, ctx) + [r for r in out if r["id"] not in {b["id"] for b in self.book_rows(book, ctx)}]

    def apply(self, book, cur, ctx):
        new = copy.deepcopy(book)
        have = {x.get("id") for x in new.get("lessons", [])}
        new.setdefault("lessons", []).extend(r for r in cur if r["id"] not in have)
        return new


class ToolRoster:
    name, key = "tool_roster", "key"

    def book_rows(self, book, ctx):
        out = [{"key": f"{env}|{t.get('imp') or t.get('pip')}", "env": env, "pip": t.get("pip"), "imp": t.get("imp"), "role": t.get("role")}
               for env, e in (book.get("envs") or {}).items() for t in (e.get("tools") or [])]
        out += [{"key": f"(unrouted)|{m}", "env": "(unrouted)", "pip": m, "imp": m, "role": "加速器(本冊四境未收;路由看 Baseline families)"} for m in book.get("accelerator_not_in_roster_envs", [])]
        return out

    def _lock_tail(self, ctx, k):
        try:
            lock = json.loads((ctx["via"] / ctx["prm"]["paths"]["tool_lock"]).read_text(encoding="utf-8"))
            return ctx["via"].parent / lock[k]["path"]
        except Exception:  # noqa: BLE001
            return None

    def _imports(self, p: Path) -> set:
        out = set()
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8-sig", errors="replace"))):
            if isinstance(n, ast.Import):
                out.update(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
                out.add(n.module.split(".")[0])
        std = set(getattr(sys, "stdlib_module_names", ())) | {"__future__"}
        local = {q.stem for q in p.parent.glob("*.py")}
        return {m for m in out if m not in std and m not in local and not m.startswith(("_", "Veritas", "VIA_", "SUP_", "CGC_"))}

    def _lib_map(self, p: Path) -> set:
        for n in ast.parse(p.read_text(encoding="utf-8-sig", errors="replace")).body:
            tgt = n.target if isinstance(n, ast.AnnAssign) else (n.targets[0] if isinstance(n, ast.Assign) and n.targets else None)
            if getattr(tgt, "id", "") == "_LIB_MAP" and isinstance(n.value, ast.Dict):
                return {k.value for k in n.value.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)}
        return set()

    def current_rows(self, book, ctx):
        rows = self.book_rows(book, ctx)
        have = {r["key"] for r in rows}
        envs = list((book.get("envs") or {}).keys())
        net = self._lock_tail(ctx, "network")
        if net and net.is_file():
            for m in sorted(self._imports(net)):
                for env in envs:
                    k = f"{env}|{m}"
                    if k not in have:
                        rows.append({"key": k, "env": env, "pip": m, "imp": m, "role": "網路(AegisNexus 相依)"})
        acc = self._lock_tail(ctx, "accelerator")
        if acc and acc.is_file():
            routed = {r["imp"] for r in rows}
            for m in sorted(self._lib_map(acc) - routed):
                rows.append({"key": f"(unrouted)|{m}", "env": "(unrouted)", "pip": m, "imp": m, "role": "加速器(本冊四境未收;路由看 Baseline families)"})
        return rows

    def apply(self, book, cur, ctx):
        new = copy.deepcopy(book)
        have = {r["key"] for r in self.book_rows(book, ctx)}
        for r in cur:
            if r["key"] in have:
                continue
            if r["env"] == "(unrouted)":
                new.setdefault("accelerator_not_in_roster_envs", []).append(r["imp"])
            else:
                new["envs"][r["env"]].setdefault("tools", []).append({"pip": r["pip"], "imp": r["imp"], "role": r["role"]})
        return new


class LogicArch:
    name, key = "logic_arch", "key"
    SECTIONS = ("placed_by_batch662", "off_book_pending")

    def book_rows(self, book, ctx):
        return [{"key": f"{s}|{x.get('family')}", "section": s, "family": x.get("family"), "tail": x.get("tail"), "state": x.get("state")}
                for s in self.SECTIONS for x in book.get(s, [])]

    def current_rows(self, book, ctx):
        code = ctx["via"] / ctx["prm"]["paths"]["vrn_code_dir"]
        index: dict = {}
        for p in code.rglob("*_v*.py"):
            fam = re.sub(r"_v\d{4}$", "", p.stem)
            if _vnum(p) >= 0 and (fam not in index or _vnum(p) > _vnum(index[fam])):
                index[fam] = p
        out = []
        for r in self.book_rows(book, ctx):
            p = index.get(r["family"])
            tail = p.relative_to(ctx["via"]).as_posix() if p else r["tail"]
            out.append({**r, "tail": tail, "state": r["state"] if p else "MISSING", "role_now": _first_doc_line(p) if p else ""})
        return out

    def apply(self, book, cur, ctx):
        new = copy.deepcopy(book)
        by = {r["key"]: r for r in cur}
        for s in self.SECTIONS:
            for x in new.get(s, []):
                r = by.get(f"{s}|{x.get('family')}")
                if r:
                    x["tail"], x["state"] = r["tail"], r["state"]
        return new


BUILTIN = {"policy_laws": PolicyLaws, "tool_roster": ToolRoster, "logic_arch": LogicArch}
COMPARE = {"policy_laws": ("batch", "cat", "zh"), "tool_roster": ("env", "pip", "imp", "role"), "logic_arch": ("tail", "state")}


def load_engine(spec: dict, via: Path):
    if not spec.get("module"):
        return BUILTIN[spec["name"]]()
    p = (via / spec["module"]).resolve()
    ast.parse(p.read_text(encoding="utf-8"))                         # 外掛先過語法樹才載入
    sp = importlib.util.spec_from_file_location(f"{FAMILY}_plugin_{spec['name']}", p)
    mod = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(mod)
    eng = mod.ENGINE
    for m in ("name", "key", "book_rows", "current_rows", "apply"):
        if not hasattr(eng, m):
            raise TypeError(f"外掛 {p.name} 的 ENGINE 缺 {m}")
    return eng


def diff_rows(book: list, cur: list, key: str, cmp: tuple) -> list:
    b = {r[key]: r for r in book}
    c = {r[key]: r for r in cur}
    out = [{key: k, "change": "ADDED"} for k in c if k not in b]
    out += [{key: k, "change": "REMOVED"} for k in b if k not in c]
    out += [{key: k, "change": "CHANGED", "fields": [f for f in cmp if b[k].get(f) != c[k].get(f)]}
            for k in c if k in b and any(b[k].get(f) != c[k].get(f) for f in cmp)]
    return out


# ---------------------------------------------------------------- 寫入(新版號 · 原子 · 只增)
def published_max(via: Path, books_dir: str, pat: str) -> int:
    repo = via.parent
    try:
        rel = (via / books_dir).relative_to(repo).as_posix()
        r = subprocess.run(["git", "-C", str(repo), "ls-tree", "--name-only", "origin/main", rel + "/"],
                           capture_output=True, text=True, timeout=30)
        rx = re.compile(pat.replace("v*", r"v(\d{4})").replace(".", r"\."))
        return max([int(m.group(1)) for ln in r.stdout.splitlines() for m in [rx.search(ln)] if m] or [-1])
    except Exception:  # noqa: BLE001 - 沒有 git / origin:只看本機
        return -1


def write_book(via: Path, prm: dict, pat: str, tail: Path, new: dict, why: str) -> Path:
    nv = max(_vnum(tail), published_max(via, prm["paths"]["books_dir"], pat)) + 1
    vs = f"v{nv:04d}"
    dest = tail.with_name(re.sub(r"_v\d{4}\.json$", f"_{vs}.json", tail.name))
    if dest.exists():
        raise FileExistsError(f"{dest.name} 已存在(不覆寫)")
    new = dict(new)
    if "version" in new:
        new["version"] = vs
    if "prior" in new:
        new["prior"] = tail.name
    new["ts"] = now_utc()
    new[f"why_{vs}"] = why
    tmp = dest.with_name(dest.name + f".{os.getpid()}.sdd_tmp")
    tmp.write_text(json.dumps(new, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    json.loads(tmp.read_text(encoding="utf-8"))
    os.replace(tmp, dest)
    return dest


def ssot_panorama(via: Path, label: str) -> str:
    v = newest(via / "supportive modules" / "registry", "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py")
    if v is None:
        return "YELLOW(VCGC 主控台不在:跳過 ssot panorama · 退路)"
    try:
        r = subprocess.run([sys.executable, str(v), "ssot", "panorama"], cwd=str(via.parent), capture_output=True, text=True,
                           timeout=900, env=dict(os.environ, VIA_FROM_VCGC="YES", PYTHONUTF8="1"), encoding="utf-8", errors="replace")
        return f"rc {r.returncode}"
    except Exception as e:  # noqa: BLE001
        return f"YELLOW({type(e).__name__})"


# ---------------------------------------------------------------- 一個引擎一步
def run_engine(spec: dict, ctx: dict) -> dict:
    t0 = time.time()
    eng = load_engine(spec, ctx["via"])
    tail = newest(ctx["via"] / ctx["prm"]["paths"]["books_dir"], spec["book"])
    if tail is None:
        return {"engine": spec["name"], "lamp": "RED", "note": f"冊不在:{spec['book']}", "secs": round(time.time() - t0, 2)}
    book = json.loads(tail.read_text(encoding="utf-8"))
    b, c = eng.book_rows(book, ctx), eng.current_rows(book, ctx)
    d = diff_rows(b, c, eng.key, COMPARE.get(eng.name, ()))
    lost = [x for x in d if x["change"] == "REMOVED"]
    res = {"engine": eng.name, "book": tail.name, "rows_book": len(b), "rows_current": len(c), "diff": len(d), "removed": len(lost),
           "state": "SYNCED" if not d else "OUT_OF_SYNC", "frames": {"book": b, "current": c, "diff": d}}
    if ctx["apply"] and d:
        if lost:
            res.update(lamp="RED", note=f"重算會少 {len(lost)} 列(只增不減)→ 不寫")
        else:
            new = eng.apply(book, c, ctx)
            if len(eng.book_rows(new, ctx)) < len(b):
                res.update(lamp="RED", note="新版列數比前版少 → 不寫")
            else:
                dest = write_book(ctx["via"], ctx["prm"], spec["book"], tail, new,
                                  f"{TAG} 重產:{len(d)} 列差異(start_date {ctx['start_date']});前版 {tail.name} 一字不動")
                res.update(written=dest.name, state="SYNCED(已寫新版)")
    res.setdefault("lamp", "GREEN" if res["state"].startswith("SYNCED") else "YELLOW")
    res["secs"] = round(time.time() - t0, 2)
    return res


def run(via: Path, prm: dict, apply: bool = False, start_date: str = "", only=None, out=None) -> dict:
    """主入口:回 {引擎: 結果(含 frames = {book, current, diff} DataFrame)}。"""
    sd = start_date or prm["run"]["start_date"]
    date.fromisoformat(sd)
    ctx = {"via": via, "prm": prm, "start_date": sd, "apply": apply}
    specs = [e for e in prm["engines"] if e.get("enabled") and (not only or e["name"] in only)]
    if apply:
        say("寫前 ssot panorama:" + ssot_panorama(via, "before"))
    res, stop = {}, threading.Event()

    def heart():
        while not stop.wait(20):
            say("心跳 · 還在跑:" + " · ".join(s["name"] for s in specs if s["name"] not in res))

    threading.Thread(target=heart, daemon=True).start()
    with ThreadPoolExecutor(max_workers=max(1, min(int(prm["run"].get("lanes", 3)), len(specs) or 1))) as ex:
        futs = {s["name"]: ex.submit(run_engine, s, ctx) for s in specs}
        for k, f in futs.items():
            try:
                res[k] = f.result()
            except Exception as e:  # noqa: BLE001 - 一個引擎爆 = 該引擎紅,其他照收
                res[k] = {"engine": k, "lamp": "RED", "note": f"{type(e).__name__}: {e}", "secs": 0}
            r = res[k]
            say(f"{k} · {r['lamp']} · {r.get('state', '')} · 冊 {r.get('rows_book', '-')} 列 · 重算 {r.get('rows_current', '-')} 列 · 差 {r.get('diff', '-')}"
                + (f" · 寫 {r['written']}" if r.get("written") else "") + (f" · {r['note']}" if r.get("note") else "") + f" · {r['secs']}s")
    stop.set()
    if apply and any(r.get("written") for r in res.values()):
        say("寫後 ssot panorama:" + ssot_panorama(via, "after"))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    od = Path(out) if out else via / prm["paths"]["out_dir"] / stamp
    od.mkdir(parents=True, exist_ok=True)
    fmt = set()
    for k, r in res.items():
        fr = r.pop("frames", None) or {}
        r["frames"] = {}
        for t in prm["output"].get("tables", ["book", "current", "diff"]):
            df = frame(fr.get(t, []), prm)
            if df is None:
                fmt.add("沒有 polars / pandas")
                continue
            fmt.add(write_frame(df, od / f"{k}.{t}.parquet", prm))
            r["frames"][t] = df
    summ = {"engine": TAG, "utc": now_utc(), "start_date": sd, "apply": apply, "params": prm.get("_path"), "accel": VIA_ACCEL is not None,
            "formats": sorted(fmt), "counts": {"should": len(specs), "done": sum(1 for r in res.values() if r["lamp"] != "RED"),
                                                "skipped": [e["name"] for e in prm["engines"] if not e.get("enabled")]},
            "engines": {k: {x: v for x, v in r.items() if x != "frames"} for k, r in res.items()}}
    (od / "SUMMARY.json").write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
    led = via / prm["paths"]["run_ledger"]
    led.parent.mkdir(parents=True, exist_ok=True)
    with led.open("a", encoding="utf-8") as f:
        for k, r in res.items():
            f.write(json.dumps({"utc": summ["utc"], "engine": k, "secs": r.get("secs"), "rows_book": r.get("rows_book"),
                                "rows_current": r.get("rows_current"), "diff": r.get("diff"), "lamp": r["lamp"], "state": r.get("state"),
                                "written": r.get("written"), "start_date": sd, "apply": apply}, ensure_ascii=False) + "\n")
    say(f"DataFrame → {od}({' · '.join(sorted(fmt))})· 運作帳 {led}")
    res["_out"] = str(od)
    return res


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv or argv[:1] == ["selftest"]:
        return selftest()
    ap = argparse.ArgumentParser(prog=HERE.name)
    ap.add_argument("verb", choices=["check", "apply"])
    ap.add_argument("--via", default=None)
    ap.add_argument("--params", default=None)
    ap.add_argument("--start-date", default="")
    ap.add_argument("--only", default="")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    via = Path(a.via).resolve() if a.via else find_via(Path.cwd().resolve()) or find_via(HERE)
    if via is None:
        say("[RED] 找不到 VIA 根(用 --via)")
        return 1
    try:
        prm = load_params(via, a.params)
    except Exception as e:  # noqa: BLE001
        say(f"[RED] 參數冊:{type(e).__name__}: {e}")
        return 1
    say(f"{TAG} {a.verb} · VIA {via} · 參數 {Path(prm['_path']).name} · start_date {a.start_date or prm['run']['start_date']} · 加速器 {'載入' if VIA_ACCEL is not None else '沒載到(黃)'}")
    res = run(via, prm, apply=(a.verb == "apply" or bool(prm["run"].get("apply"))), start_date=a.start_date,
              only=[s for s in a.only.split(",") if s] or None, out=a.out)
    lamps = [r["lamp"] for k, r in res.items() if not k.startswith("_")]
    return 1 if "RED" in lamps else (2 if "YELLOW" in lamps or VIA_ACCEL is None else 0)


# ---------------------------------------------------------------- 自測(全在暫存夾造資料)
def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(("  [OK] " if cond else "  [NG] ") + name + (f" · {note}" if note else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    with tempfile.TemporaryDirectory() as td:
        via = Path(td) / "repo" / "VeritasIntelligenceAnalytics"
        reg = via / "supportive modules" / "registry"
        (reg).mkdir(parents=True)
        (via / "docs" / "handoff" / "daily").mkdir(parents=True)
        (via / "docs" / "handoff" / "ai").mkdir(parents=True)
        (via / "functional modules" / "VRN").mkdir(parents=True)
        src = newest(HERE.parent, "VIA_BooksSync_Params_v*.json")
        prm_text = src.read_text(encoding="utf-8") if src else ""
        (via / "docs" / "handoff" / "ai" / "VIA_BooksSync_Params_v0100.json").write_text(prm_text, encoding="utf-8")
        (via / "docs" / "handoff" / "daily" / "VIA_DailyLessons_Ledger_v0100.jsonl").write_text(
            json.dumps({"id": "LL-20261101-01", "date": "2026-11-01", "problem": "舊", "cause": "c", "fix": "f", "guard": "g"}, ensure_ascii=False) + "\n"
            + json.dumps({"id": "LL-20261120-01", "date": "2026-11-20", "problem": "新問題", "cause": "c", "fix": "f", "guard": "g", "check": "k"}, ensure_ascii=False) + "\n",
            encoding="utf-8")
        (reg / "VIA_Policy_Laws_SSOT_v0125.json").write_text(json.dumps({"version": "v0125", "prior": "x", "laws": [{"id": "L1"}],
                                                                         "lessons": [{"id": "LL1", "batch": "b", "cat": "c", "zh": "z"}]}, ensure_ascii=False), encoding="utf-8")
        (via / "supportive modules" / "network").mkdir()
        (via / "supportive modules" / "network" / "VeritasAegisNexus_v1652.py").write_text("import json\nimport requests\ntry:\n    import urllib3\nexcept ImportError:\n    pass\n", encoding="utf-8")
        (via / "supportive modules" / "VeritasCeleritas_v1141.py").write_text("_LIB_MAP: dict = {'numpy': None, 'polars': None, 'duckdb': None}\n", encoding="utf-8")
        (reg / "VIA_ToolVersion_Lock_v0100.json").write_text(json.dumps({
            "network": {"path": "VeritasIntelligenceAnalytics/supportive modules/network/VeritasAegisNexus_v1652.py"},
            "accelerator": {"path": "VeritasIntelligenceAnalytics/supportive modules/VeritasCeleritas_v1141.py"}}), encoding="utf-8")
        (reg / "VIA_ToolRoster_SSOT_v0108.json").write_text(json.dumps({"envs": {"via_vdf_312": {"tools": [{"pip": "duckdb", "imp": "duckdb", "role": "庫"}]},
                                                                                 "via_vrn_312": {"tools": []}}}), encoding="utf-8")
        for v in ("v0100", "v0103"):
            (via / "functional modules" / "VRN" / f"VRN_ENG017_X_{v}.py").write_text(f"'''職責 {v}'''\n", encoding="utf-8")
        (reg / "VIA_VRN_LogicArchitecture_SSOT_v0100.json").write_text(json.dumps({"version": "v0100", "placed_by_batch662": [
            {"family": "VRN_ENG017_X", "tail": "functional modules/VRN/VRN_ENG017_X_v0100.py", "state": "PLACED"},
            {"family": "VRN_GONE", "tail": "functional modules/VRN/VRN_GONE_v0100.py", "state": "PLACED"}], "off_book_pending": []}), encoding="utf-8")
        prm = load_params(via)
        chk("參數冊四類 · start_date 合法", all(k in prm for k in ("run", "paths", "engines", "output")))
        bad_prm = dict(prm, run=dict(prm["run"], start_date="2026/13/01"))
        (Path(td) / "bad.json").write_text(json.dumps(bad_prm), encoding="utf-8")
        try:
            load_params(via, Path(td) / "bad.json")
            chk("錯形起算日當場拒絕", False)
        except ValueError:
            chk("錯形起算日當場拒絕", True)
        res = run(via, prm, out=Path(td) / "o1")
        chk("三引擎並行都有結果", all(k in res for k in ("policy_laws", "tool_roster", "logic_arch")))
        p = res["policy_laws"]
        chk("Policy:只收 start_date 之後的教訓", p["diff"] == 1 and p["state"] == "OUT_OF_SYNC", str(p.get("diff")))
        t = res["tool_roster"]
        cur = {r["key"] for r in t["frames"]["current"].to_dicts()} if hasattr(t["frames"]["current"], "to_dicts") else set(t["frames"]["current"]["key"])
        chk("Roster:網路件補進每個境 · 加速器本冊四境未收另列", {"via_vdf_312|requests", "via_vrn_312|requests", "via_vrn_312|urllib3", "(unrouted)|numpy", "(unrouted)|polars"} <= cur
            and "(unrouted)|duckdb" not in cur)
        la = res["logic_arch"]
        chk("Logic:尾版換新 · 不見的標 MISSING", la["diff"] == 2, str(la.get("diff")))
        chk("輸出 DataFrame(book · current · diff)", all(set(r["frames"]) == {"book", "current", "diff"} for k, r in res.items() if not k.startswith("_")))
        chk("check 不寫冊", not list(reg.glob("*_v0126.json")) and not list(reg.glob("*_v0109.json")))
        led = (via / prm["paths"]["run_ledger"]).read_text(encoding="utf-8").splitlines()
        chk("運作帳每引擎一列(秒 · 燈 · start_date)", len(led) == 3 and all("secs" in json.loads(x) and json.loads(x)["start_date"] == prm["run"]["start_date"] for x in led))
        res2 = run(via, prm, apply=True, out=Path(td) / "o2")
        chk("apply 出新版號(前版一字不動)", (reg / "VIA_Policy_Laws_SSOT_v0126.json").exists() and (reg / "VIA_ToolRoster_SSOT_v0109.json").exists()
            and (reg / "VIA_VRN_LogicArchitecture_SSOT_v0101.json").exists()
            and json.loads((reg / "VIA_Policy_Laws_SSOT_v0125.json").read_text(encoding="utf-8"))["version"] == "v0125")
        nb = json.loads((reg / "VIA_Policy_Laws_SSOT_v0126.json").read_text(encoding="utf-8"))
        chk("新版只增:舊列都在 + 新教訓 + why/prior", [x["id"] for x in nb["lessons"]] == ["LL1", "LL-20261120-01"] and nb["prior"] == "VIA_Policy_Laws_SSOT_v0125.json"
            and "why_v0126" in nb and nb["laws"] == [{"id": "L1"}])
        lb = json.loads((reg / "VIA_VRN_LogicArchitecture_SSOT_v0101.json").read_text(encoding="utf-8"))
        chk("Logic 新版 tail = 尾版", lb["placed_by_batch662"][0]["tail"].endswith("VRN_ENG017_X_v0103.py") and lb["placed_by_batch662"][1]["state"] == "MISSING")
        res3 = run(via, prm, out=Path(td) / "o3")
        chk("寫完再查 = 全 SYNCED", all(r["state"] == "SYNCED" for k, r in res3.items() if not k.startswith("_")), str({k: (r.get("state"), r.get("diff")) for k, r in res3.items() if not k.startswith("_")}))
        no_tmp = not list(reg.glob("*.sdd_tmp"))
        chk("沒有殘留暫存檔", no_tmp)
        plug = via / "docs" / "handoff" / "ai" / "my_plugin.py"
        plug.write_text("class E:\n    name, key = 'mine', 'id'\n    def book_rows(self, b, c): return [{'id': 'a'}]\n"
                        "    def current_rows(self, b, c): return [{'id': 'a'}, {'id': 'b'}]\n    def apply(self, b, c, x): return b\nENGINE = E()\n", encoding="utf-8")
        prm_p = dict(prm, engines=[{"name": "mine", "enabled": True, "book": "VIA_Policy_Laws_SSOT_v*.json", "module": "docs/handoff/ai/my_plugin.py"}])
        rp = run(via, prm_p, out=Path(td) / "o4")
        chk("可插入:外掛引擎過語法樹後載入", rp["mine"]["diff"] == 1 and rp["mine"]["lamp"] == "YELLOW", str(rp["mine"].get("note")))
        plug.write_text("def x(:\n", encoding="utf-8")
        rb = run(via, prm_p, out=Path(td) / "o5")
        chk("壞外掛 = 該引擎紅,不載入", rb["mine"]["lamp"] == "RED")
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
