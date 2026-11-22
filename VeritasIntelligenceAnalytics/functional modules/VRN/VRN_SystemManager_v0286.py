#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0286 — 薄尾(v0285 以前一字不動):管理器自己的「看得見 · 量得到 · 快」三補強

  2026-11-22 操作員令「檢視 VRN SYSTEM MANAGER 功能夠不夠強、能不能管全部;補強它,不要用舊的」。實測(容器)找到三個弱點:
  ① version / health 講的是 v0269 不是現役尾版:v0263~v0269 的原生處理器把自己的版號寫死,health 只核 v0269 對 v0268,
     上面 16 支尾版(v0270~v0285:extract · engine-matrix · synchronizer · monitor · launch --run · 備份 · resources)一支都沒核。
  ② help 漏列動詞:monitor · resources · engine-matrix · extract · provenance · launch --run 都不在 help 上。
  ③ 每個指令(連 version / help)都先把 527 支引擎檔整檔 ast.parse 一遍(v0272 起每次執行自動登記引擎矩陣,v0277 加 accel / net 兩欄)
     → 一個指令約 10 秒(容器實測;cProfile 9x% 在 v0277 bridge_scan)。
  本版:
  · version:先印現役尾版(本檔 · sha · 整條鏈幾版 · 鏈是否完整),再印前版原生那一行(標明是 v0269 處理器)。
  · health:前版 health 照跑,再加「鏈健康」:v0269~本版每一支都載得起來 · 有 main · 前版是緊鄰的上一版(沒有插號 / 跳號)·
    有加速器橋;另加「help 涵蓋」:鏈上每個動詞 help 都列得到;引擎矩陣掃描快取狀態。燈取最差。
  · help:頂端先標現役尾版,前版 help 照印,尾端補上 v0270 以後加的動詞(從各尾版 main() 的語法樹讀出來,不是手抄)。
  · verbs(新動詞):每個動詞由哪一版處理(語法樹 + v0269 原生表);--json 機器可讀。
  · 引擎矩陣掃描快取:v0277 bridge_scan 是「檔案文字 → 結果」的純函式 → 以文字 sha256 為鍵快取在自己的
    VIA_Reports/vrn/engine_matrix/_bridge_scan_cache.json(原子換檔 · 每行程唯一暫存檔名);掃描器原始碼一變整份作廢。
    結果與不快取逐檔相同(自測整樹比對),只是不再每次重解析沒變的檔。
  其餘動詞照 v0285。
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

import ast
import contextlib
import hashlib
import importlib.util
import inspect
import io
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[1]
FAMILY = "VRN_SystemManager"
TAG = "VRN_SystemManager v0286"
NATIVE_FLOOR = 269                                   # v0263~v0269 是原生處理器(版號寫死在它自己身上);v0270 起是薄尾
CACHE_REL = "VIA_Reports/vrn/engine_matrix/_bridge_scan_cache.json"
CACHE_CAP = 5000


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0286", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


# ─────────────────────────── 鏈:已載入的每一版 ───────────────────────────
def chain_modules() -> list:
    """本檔 → 前版 → … 一路沿 PRIOR 往下,到沒有 PRIOR 的那一版(v0269 原生處理器)為止。只看已載入的模組,不再載任何檔。"""
    out, m, seen = [sys.modules[__name__]], PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        out.append(m)
        m = vars(m).get("PRIOR")
    return out


def _file_sha(p: Path) -> str:
    try:
        return hashlib.sha256(Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    except OSError:
        return ""


def chain_report(mods=None, family_dir: Path | None = None) -> dict:
    mods = chain_modules() if mods is None else mods
    fam_dir = HERE if family_dir is None else Path(family_dir)
    on_disk = sorted(_vnum(p) for p in fam_dir.glob(FAMILY + "_v*.py") if _vnum(p) >= 0)
    rows, bad = [], []
    for i, m in enumerate(mods):
        f = Path(getattr(m, "__file__", "") or "")
        v = _vnum(f)
        below = mods[i + 1] if i + 1 < len(mods) else None
        want = max((x for x in on_disk if x < v), default=None)
        got = _vnum(getattr(below, "__file__", "")) if below is not None else None
        try:
            src = f.read_text(encoding="utf-8")
        except OSError:
            src = ""
        r = {"version": "v%04d" % v, "file": f.name, "main": callable(vars(m).get("main")),
             "accel": "[VIA:ACCEL-BRIDGE:v0100]" in src,
             "prior": ("v%04d" % got) if got is not None else None,
             "prior_ok": below is None or got == want}
        rows.append(r)
        why = [k for k, ok in (("沒有 main", r["main"]), ("沒有加速器橋", r["accel"]),
                               ("前版不是緊鄰的上一版(%s · 應為 v%04d)" % (r["prior"], want or 0), r["prior_ok"])) if not ok]
        if why:
            bad.append("%s:%s" % (r["version"], " · ".join(why)))
    top = max(on_disk) if on_disk else -1
    tail_v = _vnum(getattr(mods[0], "__file__", "")) if mods else -1
    if tail_v != top:
        bad.append("磁碟上最大版是 v%04d,但跑的是 v%04d" % (top, tail_v))
    return {"rows": rows, "bad": bad, "count": len(rows), "tail": "v%04d" % tail_v, "on_disk": len(on_disk),
            "lamp": "RED" if bad else "GREEN"}


# ─────────────────────────── 動詞表:從各尾版 main() 的語法樹讀出來 ───────────────────────────
def _main_verbs(src: str) -> list:
    """main() 裡 `args[:1] == ["x"]` / `args[:1] in (["x"], ["y"])` 的 x(只取 == / in;!= 是排除,不算)。"""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    fn = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main"), None)
    if fn is None:
        return []
    found = []
    for n in ast.walk(fn):
        if not (isinstance(n, ast.Compare) and len(n.ops) == 1 and isinstance(n.ops[0], (ast.Eq, ast.In))):
            continue
        left = n.left
        if not (isinstance(left, ast.Subscript) and isinstance(left.slice, ast.Slice) and isinstance(left.slice.upper, ast.Constant)
                and left.slice.upper.value == 1 and left.slice.lower is None):
            continue
        comp = n.comparators[0]
        lists = comp.elts if isinstance(comp, (ast.Tuple, ast.Set)) else [comp]
        for lst in lists:
            if isinstance(lst, ast.List) and len(lst.elts) == 1 and isinstance(lst.elts[0], ast.Constant) and isinstance(lst.elts[0].value, str):
                found.append(lst.elts[0].value)
    return found


def verb_table(mods=None) -> list:
    """每個動詞:哪一版加的(added)· 最上面哪一版還在處理它(top)· 中間哪些版也接手(touched)。新的先排。"""
    mods = chain_modules() if mods is None else mods
    seen = {}
    for m in mods:
        f = Path(getattr(m, "__file__", "") or "")
        v = _vnum(f)
        if v > NATIVE_FLOOR:
            try:
                names = _main_verbs(f.read_text(encoding="utf-8"))
            except OSError:
                names = []
        else:
            names = list(vars(m).get("SM_NATIVE") or ())
        for name in names:
            if name.startswith("-") or name in ("selftest", "_extract_worker"):
                continue
            seen.setdefault(name, []).append(v)
        if v <= NATIVE_FLOOR:
            break
    seen.setdefault("verbs", []).append(_vnum(__file__))
    rows = []
    for name, vs in seen.items():
        vs = sorted(set(vs))
        rows.append({"verb": name, "added": "v%04d" % vs[0], "top": "v%04d" % vs[-1], "touched": ["v%04d" % x for x in vs],
                     "how": "原生處理器" if vs[0] <= NATIVE_FLOOR else "薄尾 main()"})
    rows.sort(key=lambda r: (r["added"], r["verb"]), reverse=True)
    return rows


# ─────────────────────────── 引擎矩陣掃描快取 ───────────────────────────
def _owner(name: str):
    """鏈上自己定義 name 的那一版(vars 只看自己,不跟 __getattr__ 轉交)。"""
    for m in chain_modules()[1:]:
        if name in vars(m):
            return m
    return None


SCAN_MOD = _owner("bridge_scan")                     # v0277
_RAW_SCAN = SCAN_MOD.bridge_scan if SCAN_MOD is not None else None
_RAW_DECORATE = SCAN_MOD.decorate if SCAN_MOD is not None and "decorate" in vars(SCAN_MOD) else None


def _scanner_id() -> str:
    if _RAW_SCAN is None:
        return ""
    try:
        src = inspect.getsource(_RAW_SCAN)
    except (OSError, TypeError):
        src = repr(_RAW_SCAN.__code__.co_code)
    extra = "%s|%s|%s" % (getattr(SCAN_MOD, "ACCEL_MOD", ""), getattr(getattr(SCAN_MOD, "_STAMP", None), "pattern", ""),
                          sorted(getattr(SCAN_MOD, "SOCK_CALLS", ()) or ()))
    return hashlib.sha256((src + extra).encode("utf-8")).hexdigest()[:16]


SCANNER_ID = _scanner_id()
CACHE = {"path": None, "data": None, "used": set(), "hits": 0, "misses": 0, "dirty": False, "loaded_from": None, "note": ""}


def cache_path() -> Path:
    env = os.environ.get("VIA_VRN_SCAN_CACHE")
    return Path(env) if env else VIA_ROOT / CACHE_REL


def _cache_load() -> dict:
    p = cache_path()
    if CACHE["data"] is not None and CACHE["path"] == p:
        return CACHE["data"]
    CACHE.update(path=p, data={}, used=set(), dirty=False, loaded_from=None, note="")
    try:
        body = json.loads(p.read_text(encoding="utf-8"))
        if body.get("scanner") == SCANNER_ID and isinstance(body.get("entries"), dict):
            CACHE["data"], CACHE["loaded_from"] = body["entries"], str(p)
        else:
            CACHE["note"] = "掃描器原始碼變了 → 整份快取作廢重算"
    except FileNotFoundError:
        CACHE["note"] = "沒有快取檔(第一次跑)"
    except (OSError, ValueError, AttributeError) as exc:
        CACHE["note"] = "快取檔讀不了(%s)→ 當作沒有、照算" % type(exc).__name__
    return CACHE["data"]


def cache_save() -> dict:
    data = CACHE["data"]
    if data is None or not CACHE["dirty"]:
        return {"saved": False}
    keep = {k: data[k] for k in CACHE["used"] if k in data}
    if len(keep) < len(data) and len(CACHE["used"]) < 50:          # 這輪只掃了幾支 → 舊的也留(上限 CACHE_CAP)
        for k, v in data.items():
            if len(keep) >= CACHE_CAP:
                break
            keep.setdefault(k, v)
    p = cache_path()
    tmp = p.with_name("%s.%d.%d.tmp" % (p.name, os.getpid(), time.time_ns()))
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps({"scanner": SCANNER_ID, "by": TAG, "entries": keep}, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, p)                                          # 原子換檔:別的行程讀到的不是舊檔就是新檔
        CACHE["dirty"] = False
        return {"saved": True, "entries": len(keep), "path": str(p)}
    except OSError as exc:
        with contextlib.suppress(OSError):
            tmp.unlink()
        return {"saved": False, "error": "%s:%s" % (type(exc).__name__, str(exc)[:120])}


def bridge_scan(text: str) -> dict:
    """v0277 bridge_scan 加快取:同樣的文字 → 同樣的結果(回傳複本,呼叫端改了也不汙染快取)。"""
    data = _cache_load()
    key = hashlib.sha256(text.encode("utf-8", "surrogatepass")).hexdigest()
    CACHE["used"].add(key)
    hit = data.get(key)
    if hit is not None:
        CACHE["hits"] += 1
        return json.loads(json.dumps(hit))
    CACHE["misses"] += 1
    res = _RAW_SCAN(text)
    data[key] = json.loads(json.dumps(res))
    CACHE["dirty"] = True
    return res


def decorate(summary, root):
    try:
        return _RAW_DECORATE(summary, root)
    finally:
        CACHE["last_save"] = cache_save()                          # 整輪掃完存一次


if SCAN_MOD is not None and _RAW_SCAN is not None:
    SCAN_MOD.bridge_scan = bridge_scan                              # decorate 叫的是 v0277 模組全域 bridge_scan → 換上快取版
    if _RAW_DECORATE is not None:
        SCAN_MOD.decorate = decorate                                # v0277 _wrap 叫模組全域 decorate → 掃完存檔


def scan_cache_status() -> dict:
    p = cache_path()
    n = None
    with contextlib.suppress(OSError, ValueError, AttributeError):
        body = json.loads(p.read_text(encoding="utf-8"))
        n = len(body.get("entries") or {}) if body.get("scanner") == SCANNER_ID else 0
    return {"in_effect": SCAN_MOD is not None and getattr(SCAN_MOD, "bridge_scan", None) is bridge_scan,
            "scanner": SCANNER_ID, "path": str(p), "entries": n, "hits": CACHE["hits"], "misses": CACHE["misses"]}


# ─────────────────────────── 動詞 ───────────────────────────
def _capture(fn, *a):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*a)
    return rc, buf.getvalue()


def cmd_version() -> int:
    cr = chain_report()
    print("[%s] VRN · 現役尾版 %s · sha %s · 鏈 %d 版(%s → v%04d 原生處理器)· %s" % (
        TAG, Path(__file__).name, _file_sha(Path(__file__))[:12], cr["count"], cr["tail"], NATIVE_FLOOR,
        "鏈完整" if not cr["bad"] else "鏈有問題:" + ";".join(cr["bad"][:3])))
    rc, out = _capture(PRIOR.main, ["version"])
    for ln in out.splitlines():
        print("  前版原生處理器 · " + ln)
    return 1 if cr["bad"] else rc


def help_coverage(help_text: str, table=None) -> list:
    table = verb_table() if table is None else table
    return [r["verb"] for r in table if not re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(r["verb"]), help_text)]


def cmd_help() -> int:
    print("%s(現役尾版)· VRN 自己的入口 · 動詞與處理版:verbs · 鏈與健康:version / health" % TAG)
    rc, out = _capture(PRIOR.main, ["help"])
    print(out, end="")
    table = verb_table()
    late = [r for r in table if _vnum("x_" + r["added"]) > NATIVE_FLOOR]
    print("  ── v0270 以後加的動詞(從各尾版 main() 讀出;前版 help 沒列的補在這裡)──")
    for r in late:
        print("  %-14s %s 加%s" % (r["verb"], r["added"], (" · 最新 " + r["top"]) if r["top"] != r["added"] else ""))
    print("  verbs [--json]                每個動詞由哪一版處理(%s 新增)" % TAG)
    print("  launch --run                  開閘全跑(v0283 起走 TEMP · 起跑前備份庫);resources [--verify] 看資源與備份")
    return rc


def cmd_verbs(args) -> int:
    table = verb_table()
    if "--json" in args:
        print(json.dumps({"tool": TAG, "verbs": table, "older": "其餘舊動詞由 v0269 原生處理器轉交 v0268 以下(子行程)"}, ensure_ascii=False, indent=1))
        return 0
    print("[%s] verbs · %d 個(加入版 · 最新處理版 · 中間也接手的版)" % (TAG, len(table)))
    for r in table:
        mid = [x for x in r["touched"] if x not in (r["added"], r["top"])]
        print("  %-16s 加 %s · 最新 %s%s · %s" % (r["verb"], r["added"], r["top"], (" · 經 " + " ".join(mid)) if mid else "", r["how"]))
    print("  其餘舊動詞:v0269 原生處理器原樣轉交 v0268 以下(子行程)")
    return 0


def cmd_health(args) -> int:
    rc0, out = _capture(PRIOR.main, ["health", *args])
    for ln in out.splitlines():
        print("  前版原生處理器 · " + ln)
    cr = chain_report()
    _, help_out = _capture(PRIOR.main, ["help"])
    help_out += "\n" + " ".join(r["verb"] for r in verb_table() if _vnum("x_" + r["added"]) > NATIVE_FLOOR) + " verbs"
    missing = help_coverage(help_out)
    sc = scan_cache_status()
    parts = ["鏈 %d/%d 版 ✓" % (cr["count"] - sum(1 for b in cr["bad"] if b.startswith("v")), cr["count"]) if not cr["bad"] else "鏈 ✗ " + ";".join(cr["bad"][:3]),
             "help 涵蓋 %s" % ("✓" if not missing else "✗ 漏 " + " ".join(missing)),
             "引擎矩陣掃描快取 %s · %s 筆" % ("生效" if sc["in_effect"] else "沒生效", sc["entries"] if sc["entries"] is not None else "0")]
    lamp = "RED" if (cr["bad"] or rc0 == 1) else ("YELLOW" if (missing or not sc["in_effect"] or rc0 not in (0,)) else "GREEN")
    print("[%s] health %s · %s" % (TAG, lamp, " · ".join(parts)))
    return {"GREEN": 0, "YELLOW": 2, "RED": 1}[lamp]


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if not args or args[:1] == ["help"]:
        return cmd_help()
    if args[:1] == ["version"] and "--legacy" not in args:
        return cmd_version()
    if args[:1] == ["health"] and "--legacy" not in args:
        return cmd_health(args[1:])
    if args[:1] == ["verbs"]:
        return cmd_verbs(args[1:])
    return PRIOR.main(args)


# ─────────────────────────── 自測 ───────────────────────────
def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)

    rc0, out0 = _capture(PRIOR.selftest)
    print(f"=== {TAG} · 薄尾自測(version / health 看現役尾版與整條鏈 · help 補齊 · verbs · 引擎矩陣掃描快取;暫存夾 · 零網路)===")
    chk("⓪ 直接前版 %s 自測過" % PRIOR_PATH.name, rc0 == 0, out0[-300:])
    keep_env = os.environ.get("VIA_VRN_SCAN_CACHE")
    with tempfile.TemporaryDirectory(prefix="via_vrn286_") as td:
        os.environ["VIA_VRN_SCAN_CACHE"] = str(Path(td) / "cache.json")
        CACHE.update(data=None, path=None, hits=0, misses=0, used=set())
        try:
            files = [p for p in HERE.rglob("*.py") if not any(s in p.parts for s in ("__pycache__", "VIA_Reports"))]
            texts = [p.read_text(encoding="utf-8", errors="replace") for p in files]
            import warnings
            warnings.simplefilter("ignore", SyntaxWarning)                  # 被掃的引擎檔自己的跳脫字元警告,與本自測無關
            t0 = time.perf_counter()
            raw = [_RAW_SCAN(t) for t in texts]
            t_raw = time.perf_counter() - t0
            cold = [bridge_scan(t) for t in texts]
            saved = cache_save()
            CACHE.update(data=None, path=None, hits=0, misses=0, used=set())          # 模擬下一個行程:從檔案讀快取
            t1 = time.perf_counter()
            warm = [bridge_scan(t) for t in texts]
            t_warm = time.perf_counter() - t1
            chk("① 快取結果與不快取逐檔相同(VRN 夾全部 %d 支 .py:冷 · 從檔讀回的熱都比)" % len(texts), raw == cold == warm)
            chk("② 第二個行程全部命中、不再解析(命中 %d · 未命中 %d)· 時間 %.2fs → %.2fs" % (CACHE["hits"], CACHE["misses"], t_raw, t_warm),
                saved.get("saved") and CACHE["misses"] == 0 and CACHE["hits"] == len(texts) and t_warm < t_raw, saved)
            warm[0]["net_libs"].append("x")
            chk("③ 回傳複本:呼叫端改結果不汙染快取", bridge_scan(texts[0]) == raw[0])
            Path(os.environ["VIA_VRN_SCAN_CACHE"]).write_text("{壞掉", encoding="utf-8")
            CACHE.update(data=None, path=None, hits=0, misses=0, used=set())
            chk("④ 快取檔壞掉 → 當作沒有、照算(結果不變)", bridge_scan(texts[0]) == raw[0] and CACHE["misses"] == 1 and "讀不了" in CACHE["note"], CACHE["note"])
            cache_save()
            body = json.loads(Path(os.environ["VIA_VRN_SCAN_CACHE"]).read_text(encoding="utf-8"))
            body["scanner"] = "old"
            Path(os.environ["VIA_VRN_SCAN_CACHE"]).write_text(json.dumps(body), encoding="utf-8")
            CACHE.update(data=None, path=None, hits=0, misses=0, used=set())
            bridge_scan(texts[0])
            chk("⑤ 掃描器原始碼變了 → 整份作廢重算", CACHE["misses"] == 1 and CACHE["hits"] == 0 and "作廢" in CACHE["note"], CACHE["note"])
            leftovers = [p.name for p in Path(td).iterdir() if p.name.endswith(".tmp")]
            chk("⑥ 原子換檔不留暫存檔", not leftovers, leftovers)
        finally:
            if keep_env is None:
                os.environ.pop("VIA_VRN_SCAN_CACHE", None)
            else:
                os.environ["VIA_VRN_SCAN_CACHE"] = keep_env
            CACHE.update(data=None, path=None, hits=0, misses=0, used=set(), dirty=False)
    chk("⑦ 快取真的生效:v0277 模組的 bridge_scan / decorate 已換成本版(不是只有標記)",
        SCAN_MOD is not None and SCAN_MOD.bridge_scan is bridge_scan and SCAN_MOD.decorate is decorate and "v0277" in Path(SCAN_MOD.__file__).name)
    chk("⑧ 預設快取檔在 VRN 自己的 VIA_Reports/vrn 夾", str(VIA_ROOT / CACHE_REL).replace("\\", "/").endswith("VIA_Reports/vrn/engine_matrix/_bridge_scan_cache.json"))

    cr = chain_report()
    chk("⑨ 真鏈:本檔 → … → v0269 全載入、每版有 main、前版都是緊鄰上一版、都有加速器橋(%d 版)" % cr["count"],
        not cr["bad"] and cr["tail"] == "v0286" and cr["rows"][-1]["version"] == "v%04d" % NATIVE_FLOOR and cr["count"] == 286 - NATIVE_FLOOR + 1, cr["bad"])
    with tempfile.TemporaryDirectory(prefix="via_vrn286_fam_") as td:
        fam = Path(td)
        for v in (269, 270, 271, 272):
            (fam / ("%s_v%04d.py" % (FAMILY, v))).write_text("# [VIA:ACCEL-BRIDGE:v0100]\ndef main(a=None):\n    return 0\n", encoding="utf-8")
        mk = []
        for v in (272, 270, 269):                     # 假鏈跳過 v0271(插號 / 鏈斷)
            m = type(sys)("fake%d" % v)
            m.__file__ = str(fam / ("%s_v%04d.py" % (FAMILY, v)))
            m.main = lambda a=None: 0
            mk.append(m)
        bad = chain_report(mk, fam)
        chk("⑩ 鏈跳過一版(v0272 的前版是 v0270,磁碟上有 v0271)→ 紅並點名", bad["lamp"] == "RED" and any("v0272" in b and "v0271" in b for b in bad["bad"]), bad["bad"])
        del mk[0].main
        chk("⑪ 某版沒有 main → 紅並點名", any("沒有 main" in b for b in chain_report(mk, fam)["bad"]))

    table = verb_table()
    got = {r["verb"]: (r["added"], r["top"]) for r in table}
    want = {"monitor": ("v0281", "v0281"), "resources": ("v0283", "v0284"), "launch": ("v0269", "v0283"), "engine-matrix": ("v0272", "v0277"),
            "extract": ("v0270", "v0276"), "provenance": ("v0270", "v0277"), "synchronizer": ("v0278", "v0278"), "verbs": ("v0286", "v0286")}
    chk("⑫ verbs:從各尾版 main() 語法樹讀出 · 加入版與最新處理版分開列", all(got.get(k) == v for k, v in want.items()) and "status" in got and "backup" in got,
        {k: got.get(k) for k in want})
    chk("⑬ 語法樹讀動詞:== / in 才算 · != 是排除不算 · [:1] 以外的切片不算",
        _main_verbs("def main(args):\n    if args[:1] == ['a']: pass\n    if args[:1] in (['b'], ['c']): pass\n"
                    "    if args[:1] != ['z']: pass\n    if args[:2] == ['q']: pass\n") == ["a", "b", "c"])
    _, hout = _capture(cmd_help)
    miss = help_coverage(hout)
    chk("⑭ help 列得到每個動詞(%d 個)· 頂端標現役尾版" % len(table), not miss and hout.startswith(TAG), miss)
    rcv, vout = _capture(cmd_version)
    chk("⑮ version 第一行是現役尾版 v0286 與整條鏈;前版那一行照留並標明", rcv == 0 and vout.startswith("[%s] VRN · 現役尾版 VRN_SystemManager_v0286.py" % TAG)
        and "鏈完整" in vout and "前版原生處理器 · [VRN_SystemManager v0269]" in vout, vout[:300])
    rch, hlt = _capture(cmd_health, [])
    chk("⑯ health 加鏈健康 · help 涵蓋 · 快取狀態;真樹綠", rch == 0 and "health GREEN" in hlt and "鏈 %d/%d 版 ✓" % (cr["count"], cr["count"]) in hlt
        and "help 涵蓋 ✓" in hlt and "快取 生效" in hlt, hlt[-400:])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑰ 加速器橋在 · 不碰 TA-Lib · 不出網", "[VIA:ACCEL-BRIDGE:v0100]" in src and "talib" not in src.split("def selftest", 1)[0].lower()
        and not re.search(r"^\s*(import|from)\s+(requests|urllib|socket|http)\b", src, re.M))
    body = src.split("def selftest", 1)[0]
    peer = [k for k in ("VIA_FROM_VCGC", "VIA_FROM_VDFSM") if re.search(r"environ(?:\[[\"']%s[\"']\]\s*=|\.setdefault\([\"']%s)" % (k, k), body)]
    chk("⑲ 系統獨立:本版不替別的系統設入口旗標(VCGC / VDF 的旗標一個都不設)", not peer, peer)
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑱ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), "%d 支" % len(pub))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
