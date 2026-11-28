#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF SystemManager v0198 — 薄尾(v0197 以前一字不動):資料家整理動詞 tidy · vv 原因行再修 · 只重跑點名的引擎

一、tidy(操作員 2026-11-28 檢視資料家後定案:「1 移到 VIA_Reports  2 先處理 temp  3 給我指令」)
  缺口:要「挑選搬移執行紀錄 + 隔離暫存副本 + 備份移出 OneDrive」;最接近的現有動作 = `db move`(整個 output_hub 換家),
        差在不能挑、不能還原 → 本版掛 VDF 自己的 tidy 動詞(只動 VDF 自己的資料家;不碰別的系統)。
    tidy plan  [--home 夾]                 乾跑:逐項列「來源 → 目的地 · 檔數 · MB · 理由」+ 不搬的與理由;三數(應搬 / 會搬 / 略過)
    tidy apply --only runs,temp,backup [--home 夾]   照計畫搬(同名已在 → 略過不蓋);每一項寫帳 VIA_Reports/vdf/manager/TIDY_ledger.jsonl
    tidy undo  <run>                       照帳把那一輪搬回原位(原位已有東西 → 略過不蓋)
  三類(只搬、不刪;刪除另外再問):
    runs   執行紀錄 → VIA_Reports/vdf/runs/…(CLAUDE.md 入湖範圍:執行紀錄不當資料入湖)
           output_hub/orders 每個 ORDER_<號> 留最新 3 輪(ENG050 會讀最新一輪的 run.json)· ta_factory · workstation_setup ·
           output_hub/VDF_Manager_v*(舊管理器清點)· usmacro/FETCH_RUN_*.json 留最新 1 份 · output_hub/export → VIA_Reports/vdf/export/legacy_output_hub
    temp   temp/VDF_Manager_v*/setup_*(10-29 的完整程式副本)→ 隔離區(本機、不在 OneDrive:%LOCALAPPDATA%\VIA_quarantine\…),
           先證明:① 現役程式(tidy 所在的管理器家族本身除外)沒有一支提到這條路徑 ② 副本裡的 .py 檔名 ≥95% 在倉裡找得到(= 倉的副本,不是獨有資料)
    backup _backup/… → %USERPROFILE%\_via_backups\vdf\…(備份協議:備份放 OneDrive 外);MDL032 restore 只看 <資料家>/_backup,要還原先 tidy undo
  不搬(照實列理由):history_gap_batches(ENG064 回補續跑日誌)· fiveday(資料湖,ENG090 會檢)· candidates(ENG067 共識暫存資料)·
                    vake(VAKE 自己的執行狀態)· .fred_api_key(鑰匙;改用 VDF_MDL017 個人鑰,見 tidy plan 末行)
  目的地落在 OneDrive 裡的 temp / backup 項一律拒絕(紅),零寫入。
二、vv 原因行(2026-11-28 主機實跑):v0197 把檢查名稱裡帶 FAIL / Error 字樣的「[OK]」行也收了,真正的根因被擠出前兩行。
    → [OK] 行一律不收;全部收完再把根因排前面,收據留 10 行。另加 `vv --only 家族,家族`(只重跑點名的)與 `--engines-only`(略過 ② ③)。
三、outputs:轉不了的筆數旁附「寫法樣式」(數字 → 9 · 英文字 → a;只露格式,不露值)· 不再印 pandas 推格式警告。
零網路 · 不碰 TA-Lib · 不設同意閘 · 不 import VCGC。
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import time
import warnings
from pathlib import Path

VERSION = "v0198"
STEM = "VDF_SystemManager"
TAG = f"VDF_SystemManager {VERSION}"
HERE = Path(__file__).resolve().parent
KEEP_ORDERS = 3


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0197(vv 原因行 · 逾時重跑 · 跨平台 · 轉得了)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


V197 = PRIOR
V194, V195 = V197.V194, V197.V195

# ---------- 二、vv 原因行 ----------
OK_RX = re.compile(r"^\s*\[(OK|已知[^\]]*)\]")


def why_lines(text: str, n: int = 10) -> list:
    """不過行(不收 [OK] / [已知…] 行);全部收完再把根因排前面;一行都沒有 → 最後三行非 [OK] 的非空行。"""
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    hits = []
    for ln in lines:
        if OK_RX.match(ln):
            continue
        if V197.WHY_RX.search(ln) and ln[:220] not in hits:
            hits.append(ln[:220])
    if hits:
        return V197.root_first(hits)[:n]
    rest = [ln[:220] for ln in lines if not OK_RX.match(ln)]
    return rest[-3:]


_ORIG_WHY = V197.why_lines
V197.why_lines = why_lines                                    # v0197 的 one_engine 讀模組層 why_lines
ONLY: set = set()
_ORIG_ITEMS = V194.engine_items


def engine_items(root: Path) -> list:
    items = _ORIG_ITEMS(root)
    if not ONLY:
        return items
    return [it for it in items if it[0] in ONLY or any(o in it[0] for o in ONLY)]


V194.engine_items = engine_items


def _skipped(_root):
    return {"lamp": "GRAY", "parts": {}, "skipped": "--engines-only(略過)", "secs": 0}


# ---------- 三、outputs:轉不了的寫法樣式 ----------


def shape(s: str) -> str:
    return re.sub(r"[A-Za-z]", "a", re.sub(r"\d", "9", str(s)))[:24]


_ORIG_CAST = V197.cast_bad
_SHAPES: dict = {}


def cast_bad(where, col, want):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        bad = _ORIG_CAST(where, col, want)
    _SHAPES.pop((str((where or {}).get("path")), col), None)
    if bad and want in ("date", "datetime") and where:
        try:
            import duckdb
            con = duckdb.connect(where["path"], read_only=True) if where.get("table") else duckdb.connect()
            src = V197._q(where["table"]) if where.get("table") else "read_parquet('" + where["path"].replace("'", "''") + "')"
            v = f"CAST({V197._q(col)} AS VARCHAR)"
            try:
                rows = con.execute(f"SELECT {v}, COUNT(*) FROM {src} WHERE {V197._q(col)} IS NOT NULL AND trim({v}) <> '' "
                                   f"AND TRY_CAST({v} AS TIMESTAMP) IS NULL GROUP BY 1 LIMIT 50000").fetchall()
            finally:
                con.close()
            import pandas as pd
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ok = pd.to_datetime(pd.Series([s for s, _n in rows]).astype(str), errors="coerce").notna()
            agg: dict = {}
            for (s, n), good in zip(rows, ok):
                if not good:
                    agg[shape(s)] = agg.get(shape(s), 0) + n
            _SHAPES[(str(where["path"]), col)] = sorted(agg.items(), key=lambda kv: -kv[1])[:3]
        except Exception:  # noqa: BLE001 — 樣式只是附註;取不到就不附
            pass
    return bad


V197.cast_bad = cast_bad
_ORIG_JUDGE = V197.judge


def judge(spec: dict, m: dict) -> tuple:
    lamp, probs = _ORIG_JUDGE(spec, m)
    w = m.get("_where") or {}
    out = []
    for p in probs:
        mm = re.match(r"^(\S+) 型別 .* 筆轉不了$", p)
        sh = _SHAPES.get((str(w.get("path")), mm.group(1))) if mm else None
        out.append(p + ("(樣式 " + " · ".join(f"{k}×{n}" for k, n in sh) + ")" if sh else ""))
    return lamp, out


V195.judge = judge

# ---------- 一、tidy ----------
EXCLUDE = {"history_gap_batches": "ENG064 回補續跑日誌(搬走 = 整段重抓)", "fiveday": "資料湖(ENG090 資料覆蓋閘會檢)",
           "candidates": "ENG067 共識暫存資料", "vake": "VAKE 自己的執行狀態與資料",
           ".fred_api_key": "鑰匙檔不搬;改用 VDF_MDL017 個人鑰(9 支引擎沒經 MDL017 run 時仍讀它,先別刪)"}


def _du(p: Path) -> tuple:
    if p.is_file():
        return 1, p.stat().st_size
    n = b = 0
    for f in p.rglob("*"):
        if f.is_file():
            n += 1
            try:
                b += f.stat().st_size
            except OSError:
                pass
    return n, b


def quarantine_root() -> Path:
    if os.environ.get("VIA_TIDY_QUARANTINE"):
        return Path(os.environ["VIA_TIDY_QUARANTINE"])
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".local" / "share")
    return Path(base) / "VIA_quarantine"


def backup_root() -> Path:
    return Path(os.environ.get("VIA_TIDY_BACKUP_ROOT") or (Path.home() / "_via_backups"))


def in_onedrive(p: Path) -> bool:
    return any("onedrive" in s.lower() for s in Path(p).parts)


def temp_proof(copy: Path, code_dir: Path, tails_text: str) -> dict:
    """① 現役程式沒提到 temp/VDF_Manager 這條路徑 ② 副本 .py 檔名 ≥95% 在倉裡找得到。"""
    mention = ("temp/VDF_Manager" in tails_text) or ("temp\\\\VDF_Manager" in tails_text) or ("temp\\VDF_Manager" in tails_text)
    names = {f.name for f in copy.rglob("*.py")}
    repo = {f.name for f in code_dir.rglob("*.py")}
    hit = len(names & repo)
    ratio = hit / len(names) if names else 0.0
    return {"ok": (not mention) and ratio >= 0.95, "mention": mention, "py": len(names), "in_repo": hit, "ratio": round(ratio, 3)}


def build_plan(home: Path, via: Path, code_dir: Path, tails_text: str, stamp: str) -> dict:
    items, excluded = [], []
    oh = home / "output_hub"
    runs = via / "VIA_Reports" / "vdf" / "runs"

    def add(cat, src: Path, dst: Path, why: str, ok=True, note=""):
        n, b = _du(src)
        items.append({"cat": cat, "src": str(src), "dst": str(dst), "files": n, "bytes": b, "why": why, "ok": bool(ok), "note": note})

    od = oh / "orders"
    if od.is_dir():
        groups: dict = {}
        for d in od.iterdir():
            m = re.match(r"^ORDER_(\d+)_", d.name)
            if d.is_dir() and m:
                groups.setdefault(m.group(1), []).append(d)
        for _oid, ds in sorted(groups.items()):
            for d in sorted(ds, key=lambda x: x.name)[:-KEEP_ORDERS]:
                add("runs", d, runs / "orders" / d.name, f"執行紀錄(每個 ORDER 留最新 {KEEP_ORDERS} 輪)")
    for name in ("ta_factory", "workstation_setup"):
        if (oh / name).is_dir():
            add("runs", oh / name, runs / name, "執行紀錄(程式沒有讀它)")
    for d in sorted(oh.glob("VDF_Manager_v*")) if oh.is_dir() else []:
        if d.is_dir():
            add("runs", d, runs / d.name, "舊管理器的清點紀錄")
    fr = sorted((oh / "usmacro").glob("FETCH_RUN_*.json")) if (oh / "usmacro").is_dir() else []
    for f in fr[:-1]:
        add("runs", f, runs / "usmacro" / f.name, "擷取紀錄(留最新 1 份)")
    if (oh / "export").is_dir():
        add("runs", oh / "export", via / "VIA_Reports" / "vdf" / "export" / "legacy_output_hub", "匯出成品(ENG237 新版預設就在 VIA_Reports/vdf/export)")
    q = quarantine_root() / f"vdf_temp_{stamp}"
    for c in sorted((home / "temp").glob("VDF_Manager_v*/setup_*")) if (home / "temp").is_dir() else []:
        pr = temp_proof(c, code_dir, tails_text)
        dst = q / c.relative_to(home / "temp")
        bad_dst = in_onedrive(dst)
        add("temp", c, dst, "暫存的整份程式副本 → 隔離區(只搬不刪)", ok=pr["ok"] and not bad_dst,
            note=("目的地在 OneDrive 裡 → 拒絕" if bad_dst else "") + ("" if pr["ok"] else f"證明不過 {pr}") or f"證明過 · py {pr['py']} · 倉裡有 {pr['in_repo']}")
    if (home / "_backup").is_dir():
        for d in sorted((home / "_backup").iterdir()):
            dst = backup_root() / "vdf" / d.name
            add("backup", d, dst, "備份移出 OneDrive(備份協議);MDL032 restore 要還原先 tidy undo", ok=not in_onedrive(dst),
                note="目的地在 OneDrive 裡 → 拒絕" if in_onedrive(dst) else "")
    for name, why in EXCLUDE.items():
        for p in [home / name, oh / name, oh / "mega" / name]:
            if p.exists():
                excluded.append({"path": str(p.relative_to(home)), "why": why})
    return {"home": str(home), "stamp": stamp, "items": items, "excluded": excluded}


def apply_plan(plan: dict, cats: set, ledger: Path) -> dict:
    moved, skipped = [], []
    ledger.parent.mkdir(parents=True, exist_ok=True)
    for it in plan["items"]:
        if it["cat"] not in cats:
            continue
        src, dst = Path(it["src"]), Path(it["dst"])
        why = ("沒過檢查:" + it["note"]) if not it["ok"] else ("目的地已有同名 → 不蓋" if dst.exists() else
                                                             ("來源不在" if not src.exists() else ""))
        if why:
            skipped.append({**it, "skip": why})
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        rec = {"run": plan["stamp"], "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "cat": it["cat"], "src": it["src"],
               "dst": it["dst"], "files": it["files"], "bytes": it["bytes"], "by": TAG}
        with open(ledger, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        moved.append(rec)
    return {"moved": moved, "skipped": skipped}


def undo(run: str, ledger: Path) -> dict:
    back, skipped = [], []
    rows = [json.loads(x) for x in ledger.read_text(encoding="utf-8").splitlines() if x.strip()] if ledger.is_file() else []
    for r in reversed([r for r in rows if r.get("run") == run and not r.get("undo")]):
        src, dst = Path(r["src"]), Path(r["dst"])
        if src.exists() or not dst.exists():
            skipped.append({**r, "skip": "原位已有東西" if src.exists() else "目的地不在"})
            continue
        src.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(dst), str(src))
        rec = {**r, "undo": True, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        with open(ledger, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        back.append(rec)
    return {"back": back, "skipped": skipped}


def _ctx(args: list):
    via = V194._p("sm_via_root")()
    home_arg = args[args.index("--home") + 1] if "--home" in args else None
    h, why = V195.dataplane(via).P.resolve_home(home_arg)
    code_dir = via / "functional modules" / "VDF"
    tails = []
    for _fam, f in V194._p("sm_engines")(via).items():
        if _fam == STEM:                                       # tidy 自己(本家族)的說明與比對字串不算「有人在用」
            continue
        try:
            tails.append((via / f["tail"]).read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            pass
    return via, h, why, code_dir, "\n".join(tails)


def _mb(b) -> str:
    return f"{b / 1048576:,.1f} MB"


def cmd_tidy(args: list) -> int:
    sub = args[0] if args else "plan"
    via, home, why, code_dir, tails_text = _ctx(args)
    out = V194._p("v73_out")(via)
    ledger = out / "TIDY_ledger.jsonl"
    if sub == "undo":
        run = args[1] if len(args) > 1 else ""
        r = undo(run, ledger)
        print(f"[{TAG}] tidy undo {run} · 搬回 {len(r['back'])} · 略過 {len(r['skipped'])}")
        for s in r["skipped"]:
            print(f"  [略過] {s['dst']} · {s['skip']}")
        return 0 if not r["skipped"] else 2
    if home is None:
        print(f"[{TAG}] tidy {sub} · 找不到資料家({why})→ 不做")
        return 3
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    plan = build_plan(home, via, code_dir, tails_text, stamp)
    (out / "TIDY_plan_latest.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    items = plan["items"]
    cats = {"runs", "temp", "backup"}
    if sub == "apply":
        only = args[args.index("--only") + 1] if "--only" in args else ""
        cats = {c.strip() for c in only.split(",") if c.strip()} & {"runs", "temp", "backup"}
        if not cats:
            print(f"[{TAG}] tidy apply 要點名類別:--only runs,temp,backup(沒點名不搬)")
            return 2
    sel = [i for i in items if i["cat"] in cats]
    print(f"[{TAG}] tidy {sub} · 資料家 {home}({why})· 應搬 {len(sel)} · 會搬 {sum(1 for i in sel if i['ok'])} · "
          f"略過 {sum(1 for i in sel if not i['ok'])} · 不搬 {len(plan['excluded'])}")
    for c in ("runs", "temp", "backup"):
        g = [i for i in sel if i["cat"] == c]
        if g:
            print(f"  [{c}] {len(g)} 項 · {sum(i['files'] for i in g):,} 檔 · {_mb(sum(i['bytes'] for i in g))}")
            for i in g[:6]:
                print(f"     {'OK' if i['ok'] else 'NO'} {Path(i['src']).relative_to(home)} → {i['dst']} · {i['files']} 檔 · {_mb(i['bytes'])}"
                      + (f" · {i['note']}" if i["note"] else ""))
            if len(g) > 6:
                print(f"     …其餘 {len(g) - 6} 項(全表 VIA_Reports/vdf/manager/TIDY_plan_latest.json)")
    for e in plan["excluded"]:
        print(f"  [不搬] {e['path']} · {e['why']}")
    if sub != "apply":
        print("  鑰匙改個人鑰(鑰不顯示、不進指令歷史):Get-Content -Raw <資料家>\\output_hub\\mega\\.fred_api_key | "
              "python VDF_MDL017_UserApiKeys_v0100.py set fred --stdin")
        print(f"[乾跑] 沒搬任何檔。要搬:tidy apply --only runs,temp,backup")
        return 0
    r = apply_plan(plan, cats, ledger)
    print(f"  [搬了] {len(r['moved'])} 項 · {sum(x['files'] for x in r['moved']):,} 檔 · {_mb(sum(x['bytes'] for x in r['moved']))} · "
          f"略過 {len(r['skipped'])} · 帳 {ledger.relative_to(via)} · 還原:tidy undo {stamp}")
    for s in r["skipped"]:
        print(f"  [略過] {s['src']} · {s['skip']}")
    return 0 if not r["skipped"] else 2


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 7 項 + 前版 {PRIOR_PATH.name} 自測 · 暫存夾 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路橋在", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)
    txt = ("  [OK] T2 原因行:FAIL / NG / Traceback / Error 都收\n  [FAIL] ⑫ 前版鏈自測照過 · rc 1\n" + "  [FAIL] 前版 x 自測照過 · rc 1\n" * 9
           + "  [已知 · 前版釘舊冊] [FAIL] 舊冊\n  [NG] 找不到 = None\n")
    w = why_lines(txt)
    chk("T2 原因行:[OK] / [已知] 行不收;根因排第一(就算在第 12 行)", w[0] == "[NG] 找不到 = None" and not any(x.startswith("[OK]") for x in w)
        and not any("舊冊" in x for x in w) and len(w) <= 10, w[:3])
    with tempfile.TemporaryDirectory(prefix="vdf_sm198_") as td:
        d = Path(td)
        via, home = d / "via", d / "home"
        code = via / "functional modules" / "VDF"
        code.mkdir(parents=True)
        for n in ("A_v0100.py", "B_v0100.py"):
            (code / n).write_text("x = 1\n", encoding="utf-8")
        oh = home / "output_hub"
        for i in range(5):
            (oh / "orders" / f"ORDER_001_2026090{i}_000000").mkdir(parents=True)
            (oh / "orders" / f"ORDER_001_2026090{i}_000000" / "run.json").write_text("{}", encoding="utf-8")
        (oh / "ta_factory").mkdir()
        (oh / "ta_factory" / "TA_RUN_1.json").write_text("{}", encoding="utf-8")
        (oh / "usmacro").mkdir()
        for i in (1, 2):
            (oh / "usmacro" / f"FETCH_RUN_2026091{i}.json").write_text("{}", encoding="utf-8")
        (oh / "mega" / "history_gap_batches").mkdir(parents=True)
        (oh / "mega" / ".fred_api_key").write_text("x" * 32, encoding="utf-8")
        setup = home / "temp" / "VDF_Manager_v0104" / "setup_abc" / "via_01_vdf"
        setup.mkdir(parents=True)
        for n in ("A_v0100.py", "B_v0100.py"):
            (setup / n).write_text("x = 1\n", encoding="utf-8")
        (home / "_backup" / "tw_price_reconcile").mkdir(parents=True)
        (home / "_backup" / "tw_price_reconcile" / "x_vdf_tw_market.duckdb").write_bytes(b"1")
        os.environ["VIA_TIDY_QUARANTINE"] = str(d / "local" / "VIA_quarantine")
        os.environ["VIA_TIDY_BACKUP_ROOT"] = str(d / "user" / "_via_backups")
        try:
            plan = build_plan(home, via, code, "", "T1")
            by = {}
            for i in plan["items"]:
                by.setdefault(i["cat"], []).append(i)
            orders = [Path(i["src"]).name for i in by.get("runs", []) if "/orders/" in i["src"].replace("\\", "/")]
            chk("T3 計畫:每個 ORDER 留最新 3 輪 · FETCH_RUN 留最新 1 份 · 續跑日誌 / 鑰匙不搬",
                orders == ["ORDER_001_20260900_000000", "ORDER_001_20260901_000000"]
                and any(i["src"].endswith("FETCH_RUN_20260911.json") for i in by["runs"])
                and not any(i["src"].endswith("FETCH_RUN_20260912.json") for i in by["runs"])
                and {e["path"].replace("\\", "/") for e in plan["excluded"]} == {"output_hub/mega/history_gap_batches", "output_hub/mega/.fred_api_key"},
                (orders, plan["excluded"]))
            chk("T4 temp 證明:現役程式沒提路徑 · 副本 .py 全在倉裡 → 過;程式提到 temp/VDF_Manager → 不過",
                by["temp"][0]["ok"] and not build_plan(home, via, code, "x = 'temp/VDF_Manager_v0104'", "T0")["items"][-2]["ok"])
            ledger = d / "TIDY_ledger.jsonl"
            r = apply_plan(plan, {"runs", "temp", "backup"}, ledger)
            chk("T5 搬:只搬計畫上的 · 原位剩最新 3 輪 · 備份與 temp 到 OneDrive 外 · 每項一列帳",
                len(r["moved"]) == len(plan["items"]) and len(list((oh / "orders").iterdir())) == 3 and not (home / "temp" / "VDF_Manager_v0104" / "setup_abc").exists()
                and (d / "user" / "_via_backups" / "vdf" / "tw_price_reconcile" / "x_vdf_tw_market.duckdb").is_file()
                and (oh / "mega" / ".fred_api_key").is_file() and len(ledger.read_text(encoding="utf-8").splitlines()) == len(r["moved"]), r)
            u = undo("T1", ledger)
            chk("T6 undo:照帳全部搬回原位", not u["skipped"] and len(list((oh / "orders").iterdir())) == 5
                and (home / "temp" / "VDF_Manager_v0104" / "setup_abc" / "via_01_vdf" / "A_v0100.py").is_file()
                and (home / "_backup" / "tw_price_reconcile" / "x_vdf_tw_market.duckdb").is_file(), u)
            os.environ["VIA_TIDY_BACKUP_ROOT"] = str(d / "OneDrive" / "_via_backups")
            p2 = build_plan(home, via, code, "", "T2")
            bk = [i for i in p2["items"] if i["cat"] == "backup"]
            r2 = apply_plan(p2, {"backup"}, d / "L2.jsonl")
            chk("T7 目的地在 OneDrive 裡 → 拒絕、零寫入", bk and not bk[0]["ok"] and not r2["moved"] and not (d / "OneDrive").exists(), r2)
        finally:
            os.environ.pop("VIA_TIDY_QUARANTINE", None)
            os.environ.pop("VIA_TIDY_BACKUP_ROOT", None)
    mine = (V197.why_lines, V197.cast_bad, V195.judge, V194.engine_items)
    V197.why_lines, V197.cast_bad, V195.judge, V194.engine_items = _ORIG_WHY, _ORIG_CAST, _ORIG_JUDGE, _ORIG_ITEMS   # 前版自測看它自己的裝法
    try:
        rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 1
    finally:
        V197.why_lines, V197.cast_bad, V195.judge, V194.engine_items = mine
    chk("T8 前版 v0197 自測照過(含整條前版鏈)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if a[:1] == ["tidy"]:
        return cmd_tidy(a[1:])
    if a[:1] == ["vv"]:
        if "--only" in a:
            i = a.index("--only")
            ONLY.update(x.strip() for x in a[i + 1].split(",") if x.strip())
            del a[i:i + 2]
        if "--engines-only" in a:
            a.remove("--engines-only")
            V194.proc_structure = _skipped
            V194.proc_runtime = _skipped
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
