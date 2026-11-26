#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SUP_MDL755_VIAPolarsFrame v0100 — Polars 表格層 · 記憶體不足轉 temp(操作員 2026-09-29「go on add polars to all necessary
engines 記憶體不足可用temp替代用」)

先量再寫(容器實量,本批文件 docs/VIA_S20260929c_PolarsFrame.md 有全表):
  ① 全樹把大表撈進 Python 的引擎只有 4 支(N1);另 7 支在 DuckDB 裡對全歷史重算或整表複製(N2)。其餘讀小表、只計數、逐日抓取。
  ② DuckDB 本來就會溢寫:檔案庫寫到「庫檔旁 .tmp」(輸出夾裡),記憶體庫寫到「目前工作夾 .tmp」(常是倉根);
     上限預設「總記憶體 80%」,不看當下還剩多少 —— 別的程式吃掉一半時,DuckDB 仍以為有 80% 可用。
  ③ 把 `.df()` 改走 temp parquet 再讀回:峰值反而高(761 MB 對 642 MB),沒 ORDER BY 時列序還會變 → pandas 端不走這條。
  ④ 記憶體庫(:memory:)的表資料不能溢寫:上限收小會直接 Out of Memory → 記憶體庫只換溢寫夾、不收上限。
  ⑤ 真庫副本實證(ENG061 全歷史因子庫,放大 8 倍 = 470 萬列):上限 256 MiB 時峰值 RSS 1138 → 583 MiB、照樣算完、溢寫進受管 temp;
     11 欄裡 9 欄位元級一致,用 stddev_samp 視窗的 2 欄在最後幾位不同(最大相對誤差 8.4e-15)—— 溢寫改了 DuckDB 的合併順序。
     記憶體夠(不溢寫)時位元級不變(不設限重跑兩次同雜湊)。ENG070 面板在 64 MiB(低於下限)會 Out of Memory → 下限 512 MiB。

所以本件做四件事,別的不做:
  polars()               polars 探針(經 VIA_Toolkit 取件;缺 = None,因由在 POLARS_ERR;VIA_FRAME_BACKEND=pandas = 操作員強制退回)
  budget()               記憶體預算 = 當下可用 × 比例(VIA_FRAME_MEM_FRACTION,預設 0.5;下限 512 MiB)
  spill_dir() / sweep()  受管 temp:VIA_TEMP_ROOT(SUP_MDL738 既有名)或系統 temp 下的 VIA_spill/;用完即刪;當掉留下的夾由 sweep 清
  install_duckdb_guard() 本行程之後開的每條 DuckDB 連線:溢寫夾 → 受管 temp;檔案庫上限收到預算(記憶體不足就改寫 temp,不吃光 RAM);
                         有 polars 的境,Polars 串流也寫同一夾(POLARS_TEMP_DIR)。呼叫端 config 自己給了的設定照它的。
                         VIA_FRAME_GUARD=off = 操作員關掉守門(不改碼;連線照 DuckDB 預設)。
  frame()                DuckDB 查詢 → 表格:want="pandas" 與 `.df()` 一字不差;want="polars"/"auto" 估算 ≤ 預算走 `.pl()`,
                         超過就 COPY 到 temp parquet、回 LazyFrame(scan_parquet,collect() 走串流引擎)。估算的變長欄
                         (字串 · 二進位 · 巢狀)照實量內文(Codex #369 P2:一律算 32 位元組會把百萬筆 1 KiB 字串估成 32 MiB)。

必要引擎名冊 NECESSARY(11 支)與正典橋塊 BRIDGE_BLOCK 在本檔;coverage() 逐支看尾版有沒有橋與守門(格子站 + 自測 ⑬)。
不代裝(L19):polars 缺席 = 誠實 ABSENT + 裝令(probe 動詞 rc 3);零網路;自測零足跡。
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

import atexit
import contextlib
import importlib
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import time
import uuid
from pathlib import Path

ENGINE_ID = "SUP_MDL755_VIAPolarsFrame"
VERSION = "v0100"
HERE = Path(__file__).resolve().parent            # supportive modules/
VIA = HERE.parent
POLARS_PIN = "polars>=1.21,<2"                     # 與 QuantGuard(VDF_ENG086)同一根釘
ENV_FRACTION = "VIA_FRAME_MEM_FRACTION"
ENV_BACKEND = "VIA_FRAME_BACKEND"                  # auto | polars | pandas
ENV_TEMP = "VIA_TEMP_ROOT"                         # SUP_MDL738 既有名,不另取
ENV_GUARD = "VIA_FRAME_GUARD"                      # off = 不裝守門(操作員的閥)
SPILL_NAME = "VIA_spill"
MARKER = ".via_spill.json"
DEFAULT_FRACTION = 0.5
FRACTION_RANGE = (0.05, 0.9)
MIB = 1024 ** 2
FLOOR = 512 * MIB                                  # 預算下限:再小就不是省記憶體,是逼它 OOM
BRIDGE_MARK = "[VIA:FRAME-BRIDGE:v0100]"
_OURS = re.compile(r"^[A-Za-z0-9_.-]*_(?P<pid>\d+)_[a-z0-9_]{8}$")   # <tag>_<pid>_<mkdtemp 八碼尾(尾碼裡也可能有底線)>

#: 必要引擎名冊:(家族 stem, 夾(相對 VIA), 類, 量到的理由)。N1 = 把全市場表撈進 Python;N2 = DuckDB 內全歷史重算 / 整表複製。
NECESSARY = (
    ("VDF_ENG070_GroupClassificationIndex", "functional modules/VDF/engine", "N1",
     "全市場面板(日價 ⋈ 還原價 ⋈ 名冊)撈進 pandas;容器實量 58.8 萬列 · 載入峰值 RSS +343 MB"),
    ("VDF_ENG072_StoryRotationBridge", "functional modules/VDF/engine", "N1", "價 · 法人 · 融資券整表撈進 pandas"),
    ("GRP_ENG041_RotationMethodLab", "functional modules/GroupIndex/engine", "N1", "價 · 成交 · 法人面板撈進 pandas(滾動 17 處)"),
    ("GRP_ENG040_GroupingRotationRunner", "functional modules/GroupIndex/engine", "N1", "台股 / 全球價面板撈進 pandas"),
    ("VDF_ENG060_AdjPriceLayer", "functional modules/VDF/engine", "N2", "全歷史還原價層 CREATE OR REPLACE TABLE … AS"),
    ("VDF_ENG061_FeatureStore", "functional modules/VDF/engine", "N2", "全歷史因子庫(視窗函數 27 處)"),
    ("VDF_ENG062_GroupFeatureLayer", "functional modules/VDF/engine", "N2", "族群因子層 CTAS"),
    ("VDF_ENG064_HistoryBackfill", "functional modules/VDF/engine", "N2", "回補批次對全價表 anti-join 落庫"),
    ("VDF_ENG079_LocalDbConsolidate", "functional modules/VDF/engine", "N2", "本機庫合併(CTAS 42 處)"),
    ("VDF_ENG081_UniverseAlign", "functional modules/VDF/engine", "N2", "全市場對齊 CTAS + INSERT … SELECT"),
    ("VDF_ENG085_VatetfBridge", "functional modules/VDF/engine", "N2", "全價表複製成 VATETF 暫存庫(CTAS 16 處)"),
)

#: 正典橋塊(引擎照抄這段,一字不改;coverage() 逐字比)。鎖冊 frame 優先(R20c:只有 VCGC 啟用能動),沒有才取尾版。
BRIDGE_BLOCK = '''# ===== [VIA:FRAME-BRIDGE:v0100] Polars 表格層橋(操作員 2026-09-29 記憶體不足可用temp替代用;graceful) =====
VIA_FRAME_PATH = None
try:
    import json as _fb_json
    from pathlib import Path as _fb_Path
    _fb_p = _fb_Path(__file__).resolve()
    while _fb_p.parent != _fb_p:
        _fb_sup = _fb_p / "supportive modules"
        if (_fb_sup / "registry").is_dir():
            _fb_locks = sorted((_fb_sup / "registry").glob("VIA_ToolVersion_Lock_v*.json"))
            _fb_rel = ((_fb_json.loads(_fb_locks[-1].read_text(encoding="utf-8")).get("frame") or {}).get("path")
                       if _fb_locks else None)
            _fb_hit = (_fb_p.parent / _fb_rel) if _fb_rel else None
            if _fb_hit is None or not _fb_hit.is_file():
                _fb_tails = sorted(_fb_sup.glob("SUP_MDL755_VIAPolarsFrame_v*.py"))
                _fb_hit = _fb_tails[-1] if _fb_tails else None
            VIA_FRAME_PATH = str(_fb_hit) if _fb_hit else None
            break
        _fb_p = _fb_p.parent
except Exception:
    VIA_FRAME_PATH = None


def _via_frame():
    """Polars 表格層惰性載入(鎖冊 frame 優先,缺則尾版);缺席回 None(誠實,引擎照舊跑)"""
    if VIA_FRAME_PATH is None:
        return None
    try:
        import importlib.util as _fb_ilu
        import sys as _fb_sys
        _fb_mod = _fb_sys.modules.get("VIA_FRAME")
        if _fb_mod is None or getattr(_fb_mod, "__file__", None) != VIA_FRAME_PATH:
            _fb_spec = _fb_ilu.spec_from_file_location("VIA_FRAME", VIA_FRAME_PATH)
            _fb_mod = _fb_ilu.module_from_spec(_fb_spec)
            _fb_spec.loader.exec_module(_fb_mod)
            _fb_sys.modules["VIA_FRAME"] = _fb_mod
        return _fb_mod
    except Exception:
        return None
# ===== [VIA:FRAME-BRIDGE:END] =====
'''


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


# ── 取件:一律經 VIA_Toolkit(TOOL-040 Top-10 統一導入層;缺席 None,永不代裝)──
_TOOLKIT: list = []


def _toolkit():
    if not _TOOLKIT:
        mod = None
        p = HERE / "SUP_MDL163_Toolkit.py"
        if p.is_file():
            try:
                spec = importlib.util.spec_from_file_location("VIA_Toolkit_for_frame", p)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
            except Exception:
                mod = None
        _TOOLKIT.append(mod)
    return _TOOLKIT[0]


def _get(name: str):
    """模組或 None。Toolkit 在就經它(一個出處),不在才直接試匯入。"""
    tk = _toolkit()
    if tk is not None:
        return tk.get(name)
    try:
        return importlib.import_module(name)
    except Exception:
        return None


POLARS_ERR = ""


def polars():
    """polars 模組;缺 = None(因由在 POLARS_ERR)。VIA_FRAME_BACKEND=pandas → None(操作員強制退回)。不代裝(L19)。"""
    global POLARS_ERR
    if os.environ.get(ENV_BACKEND, "auto").strip().lower() == "pandas":
        POLARS_ERR = f"{ENV_BACKEND}=pandas(操作員強制退回 pandas)"
        return None
    mod = _get("polars")
    POLARS_ERR = "" if mod is not None else "polars 不在本境(VIA_Toolkit.get('polars') 回 None)"
    return mod


def install_hint() -> str:
    return (f'via-install polars(經閘;先 via-plan 實測)· 或 & <vdf python> -m pip install "{POLARS_PIN}"'
            "   # 裝 = 操作員的手(L19),本件不代裝")


# ── 記憶體 ──
def _mem_psutil():
    ps = _get("psutil")
    if ps is None:
        return None
    vm = ps.virtual_memory()
    return int(vm.available), int(vm.total)


def _mem_proc():
    p = Path("/proc/meminfo")
    if not p.is_file():
        return None
    got = {}
    for line in p.read_text(encoding="ascii", errors="ignore").splitlines():
        k, _, v = line.partition(":")
        if k in ("MemAvailable", "MemTotal"):
            got[k] = int(v.split()[0]) * 1024
    return (got["MemAvailable"], got["MemTotal"]) if len(got) == 2 else None


def _mem_windows():
    if os.name != "nt":
        return None
    import ctypes                                   # 只在 Windows、只在函式裡載(匯入層不載二進位)

    class _MemStatus(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

    st = _MemStatus()
    st.dwLength = ctypes.sizeof(st)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
        return None
    return int(st.ullAvailPhys), int(st.ullTotalPhys)


_PROBES = [_mem_psutil, _mem_proc, _mem_windows]


def _mem() -> tuple:
    for probe in _PROBES:
        try:
            got = probe()
        except Exception:
            got = None
        if got:
            return got[0], got[1], probe.__name__.lstrip("_")
    return None, None, "unknown"


def mem_available() -> int | None:
    """當下可用記憶體(位元組);量不到 = None(誠實,不猜)。"""
    return _mem()[0]


def fraction() -> float:
    raw = os.environ.get(ENV_FRACTION, "").strip()
    try:
        f = float(raw) if raw else DEFAULT_FRACTION
    except ValueError:
        return DEFAULT_FRACTION
    return min(max(f, FRACTION_RANGE[0]), FRACTION_RANGE[1])


def budget(frac: float | None = None, available: int | None = None) -> int | None:
    """記憶體預算 = 可用 × 比例(下限 FLOOR);可用量不到 = None(不收上限,照 DuckDB 預設)。"""
    a = available if available is not None else mem_available()
    if a is None:
        return None
    f = fraction() if frac is None else min(max(float(frac), FRACTION_RANGE[0]), FRACTION_RANGE[1])
    return max(int(a * f), FLOOR)


# ── 受管 temp ──
def spill_root() -> Path:
    base = os.environ.get(ENV_TEMP, "").strip()
    return Path(base if base else tempfile.gettempdir()) / SPILL_NAME


def _make_spill(tag: str) -> Path:
    root = spill_root()
    root.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", tag or "frame")[:40] or "frame"
    d = Path(tempfile.mkdtemp(prefix=f"{safe}_{os.getpid()}_", dir=root))
    (d / MARKER).write_text(json.dumps({"engine": ENGINE_ID, "version": VERSION, "pid": os.getpid(),
                                        "tag": tag, "ts": time.time()}), encoding="utf-8")
    return d


def _remove(d) -> None:
    if not d:
        return
    d = Path(d)
    if d.parent == spill_root() and _OURS.match(d.name):     # 只刪自己做的那種夾
        shutil.rmtree(d, ignore_errors=True)


@contextlib.contextmanager
def spill_dir(tag: str = "frame"):
    """受管溢寫夾;離開(含例外)即刪。"""
    d = _make_spill(tag)
    try:
        yield d
    finally:
        _remove(d)


def _alive(pid: int) -> bool | None:
    ps = _get("psutil")
    if ps is None:
        return None                      # 量不到就不猜;Windows 上 os.kill(pid, 0) 會真的把行程殺掉,不能拿來探
    try:
        return bool(ps.pid_exists(int(pid)))
    except Exception:
        return None


def sweep(max_age_hours: float = 24.0, *, apply: bool = False, now: float | None = None) -> list:
    """清當掉留下的溢寫夾:只看 VIA_spill/ 底下本件命名的夾;有標記或是空的才算本件的;行程還活著、還新的不碰。"""
    root = spill_root()
    if not root.is_dir():
        return []
    now = time.time() if now is None else now
    rows = []
    for d in sorted(root.iterdir()):
        if not d.is_dir() or not _OURS.match(d.name):
            continue
        meta = {}
        mk = d / MARKER
        if mk.is_file():
            try:
                meta = json.loads(mk.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                meta = {}
        try:
            empty = not any(d.iterdir())
        except OSError:
            empty = False
        pid = int(meta.get("pid") or _OURS.match(d.name).group("pid"))
        ts = float(meta.get("ts") or d.stat().st_mtime)
        age_h = (now - ts) / 3600.0
        alive = _alive(pid)
        if not mk.is_file() and not empty:
            why, go = "沒有標記又不是空的:不是本件的,不碰", False
        elif pid == os.getpid() or alive:
            why, go = "行程還活著", False
        elif age_h < max_age_hours:
            why, go = f"還新({age_h:.1f} 小時 < {max_age_hours:g})", False
        else:
            why, go = f"殘留 {age_h:.1f} 小時,行程已不在" + ("" if alive is False else "(量不到行程,只看時間)"), True
        if go and apply:
            shutil.rmtree(d, ignore_errors=True)
        rows.append({"dir": d.name, "pid": pid, "age_h": round(age_h, 2), "remove": go,
                     "removed": bool(go and apply and not d.exists()), "why": why})
    return rows


# ── DuckDB 守門 ──
_UNITS = {"bytes": 1, "byte": 1, "b": 1, "kb": 1000, "mb": 1000 ** 2, "gb": 1000 ** 3, "tb": 1000 ** 4,
          "kib": 1024, "mib": MIB, "gib": 1024 ** 3, "tib": 1024 ** 4}


def _limit_bytes(text) -> int | None:
    m = re.match(r"^\s*([\d.]+)\s*([A-Za-z]+)\s*$", str(text or ""))
    if not m or m.group(2).lower() not in _UNITS:
        return None
    return int(float(m.group(1)) * _UNITS[m.group(2).lower()])


def _setting(con, name: str):
    return con.execute("SELECT current_setting(?)", [name]).fetchone()[0]


def _sql_str(s: str) -> str:
    return "'" + str(s).replace("'", "''") + "'"


def _is_memory(database) -> bool:
    s = ":memory:" if database is None else str(database)
    return s == "" or s.startswith(":memory:")


def duck_guard(con, spill, *, budget_bytes: int | None = None, in_memory: bool = False, explicit=None) -> dict:
    """一條連線:溢寫夾 → spill;檔案庫上限收到預算(預算比現值小才收)。呼叫端 config 給了的照它的。"""
    ex = {str(k).lower() for k in (explicit or {})}
    out = {"temp_directory": None, "memory_limit": None, "tightened": False, "notes": []}
    if "temp_directory" in ex:
        out["notes"].append("呼叫端 config 已給 temp_directory:照它的")
    else:
        try:
            con.execute("SET temp_directory = " + _sql_str(str(spill)))
        except Exception as exc:          # 已溢寫過的庫 DuckDB 不准換夾:保留原夾(實量 NotImplementedException)
            out["notes"].append(f"溢寫夾保留原值:{type(exc).__name__}")
    if in_memory:
        out["notes"].append("記憶體庫:表資料不能溢寫,上限不收(收了會 Out of Memory)")
    elif ex & {"memory_limit", "max_memory"}:
        out["notes"].append("呼叫端 config 已給記憶體上限:照它的")
    else:
        b = budget_bytes if budget_bytes is not None else budget()
        cur = _limit_bytes(_setting(con, "memory_limit"))
        if b and cur and b < cur:
            con.execute(f"SET memory_limit = '{max(b // MIB, 1)}MiB'")
            out["tightened"] = True
    out["temp_directory"] = _setting(con, "temp_directory")
    out["memory_limit"] = _setting(con, "memory_limit")
    return out


_STATE: dict = {}


def install_duckdb_guard(tag: str = "", *, budget_bytes: int | None = None) -> dict:
    """本行程之後開的每條 DuckDB 連線都過 duck_guard(冪等;同一行程只裝一次,不論載入幾份本件)。"""
    if os.environ.get(ENV_GUARD, "").strip().lower() in ("off", "0", "no", "false"):
        return {"state": "OFF", "why": f"{ENV_GUARD}=off(操作員關掉守門;連線照 DuckDB 預設)"}
    duckdb = _get("duckdb")
    if duckdb is None:
        return {"state": "ABSENT", "why": "duckdb 不在本境"}
    cur = duckdb.connect
    if getattr(cur, "_via_frame_guard", False):
        return dict(getattr(cur, "_via_frame_state", {}), again=True)
    spill = _make_spill(tag or "duckdb")
    b = budget_bytes if budget_bytes is not None else budget()
    state = {"state": "ON", "tag": tag, "spill": str(spill), "budget": b, "connections": 0, "tightened": 0, "notes": []}

    def connect(*args, **kwargs):
        con = cur(*args, **kwargs)
        database = args[0] if args else kwargs.get("database", ":memory:")
        config = kwargs["config"] if "config" in kwargs else (args[2] if len(args) > 2 else None)
        try:
            r = duck_guard(con, spill, budget_bytes=b, in_memory=_is_memory(database), explicit=config)
            state["connections"] += 1
            state["tightened"] += int(r["tightened"])
            state["notes"] = (state["notes"] + [n for n in r["notes"] if n not in state["notes"]])[:6]
        except Exception as exc:          # 守門失手不擋引擎:連線照給,原因記下
            state["notes"] = (state["notes"] + [f"{type(exc).__name__}: {exc}"[:160]])[:6]
        return con

    connect._via_frame_guard = True
    connect._via_frame_state = state
    connect.__wrapped__ = cur
    duckdb.connect = connect
    _STATE.update(module=duckdb, real=cur, spill=spill, state=state, polars_env=False)
    if "POLARS_TEMP_DIR" not in os.environ:
        os.environ["POLARS_TEMP_DIR"] = str(spill)
        _STATE["polars_env"] = True
    if not _STATE.get("atexit"):
        atexit.register(uninstall_duckdb_guard)
        _STATE["atexit"] = True
    return state


def uninstall_duckdb_guard() -> bool:
    mod, real = _STATE.get("module"), _STATE.get("real")
    if mod is None or real is None:
        return False
    if getattr(mod.connect, "_via_frame_guard", False):
        mod.connect = real
    if _STATE.get("polars_env"):
        os.environ.pop("POLARS_TEMP_DIR", None)
    _remove(_STATE.get("spill"))
    _STATE.update(module=None, real=None, spill=None, state=None, polars_env=False)
    return True


def guard_state() -> dict | None:
    mod = _get("duckdb")
    fn = getattr(mod, "connect", None) if mod is not None else None
    return getattr(fn, "_via_frame_state", None) if getattr(fn, "_via_frame_guard", False) else None


# ── 表格 ──
class FrameAbsent(RuntimeError):
    """要 polars 但本境沒有(訊息附裝令;不代裝)。"""


_WIDTH = {"BOOLEAN": 1, "TINYINT": 1, "UTINYINT": 1, "SMALLINT": 2, "USMALLINT": 2, "INTEGER": 4, "UINTEGER": 4,
          "FLOAT": 4, "DATE": 4, "BIGINT": 8, "UBIGINT": 8, "DOUBLE": 8, "TIME": 8, "HUGEINT": 16, "UHUGEINT": 16,
          "UUID": 16, "INTERVAL": 16}
VIEW_WIDTH = 16    # 變長值(字串 · 二進位 · 巢狀)每值固定的視圖 / 指標;內文另實量(Codex #369 P2:原本一律算 32 會低估)


def _width(type_name: str) -> int:
    t = str(type_name).upper()
    if t in _WIDTH:
        return _WIDTH[t]
    if t.startswith("TIMESTAMP"):
        return 8
    if t.startswith("DECIMAL"):
        m = re.search(r"\((\d+)", t)
        return 8 if m and int(m.group(1)) <= 18 else 16
    return VIEW_WIDTH


def _varlen(type_name: str) -> str | None:
    """變長型別 → 量一個值內文位元組的 SQL 樣板;定長 → None。巢狀以文字長度近似(照實說,不是 Arrow 的精確佔用)。"""
    t = str(type_name).upper()
    if t.startswith("VARCHAR"):
        return "strlen({})"
    if t in ("BLOB", "BIT"):
        return "octet_length({})"
    if t == "JSON" or t.endswith("]") or t.startswith(("STRUCT", "MAP", "UNION", "LIST")):
        return "strlen(CAST({} AS VARCHAR))"
    return None


def _run(con, sql: str, params=None):
    return con.execute(sql) if params is None else con.execute(sql, params)


def estimate(con, sql: str, params=None) -> dict:
    """位元組 = 列數 × 定長寬度 + 變長欄內文**實量**(同一趟算列數與內文;欄照位置改名,重名 · 怪名都不怕)。查詢會多跑一次。"""
    desc = _run(con, f"SELECT * FROM ({sql}) AS _via_frame_q LIMIT 0", params).description
    cols = [(d[0], str(d[1])) for d in desc]
    names = ", ".join(f"_c{i}" for i in range(len(cols)))
    probes = [(i, f) for i, f in ((i, _varlen(t)) for i, (_n, t) in enumerate(cols)) if f]
    aggs = ", ".join(["count(*)"] + [f"sum({f.format(f'_c{i}')})" for i, f in probes])
    row = _run(con, f"SELECT {aggs} FROM ({sql}) AS _via_frame_q({names})", params).fetchone()
    rows = int(row[0])
    payload = sum(int(v or 0) for v in row[1:])
    width = sum(_width(t) for _n, t in cols)
    return {"rows": rows, "width": width, "payload": payload, "bytes": rows * width + payload,
            "columns": [n for n, _t in cols], "varlen": [cols[i][0] for i, _f in probes]}


def plan(est_bytes: int, budget_bytes: int | None) -> str:
    """估算 ≤ 預算 = "memory"(`.pl()`);超過 = "temp"(COPY 到 temp parquet → LazyFrame);預算量不到 = "memory"(不收上限,照實)。"""
    return "memory" if budget_bytes is None or est_bytes <= budget_bytes else "temp"


def nbytes(obj) -> int | None:
    try:
        if hasattr(obj, "memory_usage"):
            return int(obj.memory_usage(deep=True).sum())
        if hasattr(obj, "estimated_size"):
            return int(obj.estimated_size())
    except Exception:
        return None
    return None


def frame(con, sql: str, params=None, *, want: str = "pandas", spill=None, budget_bytes: int | None = None):
    """DuckDB 查詢 → (表格, 說明)。
    pandas:`.df()` 一字不差(查詢端溢寫由守門管)。polars / auto(有 polars):估 ≤ 預算走 `.pl()`;
    超過 → COPY 到 spill 夾的 parquet,回 LazyFrame(scan_parquet)。auto 沒 polars = pandas;polars 沒 polars = FrameAbsent。"""
    want = (want or "pandas").strip().lower()
    if want not in ("pandas", "polars", "auto"):
        raise ValueError(f"want 只收 pandas / polars / auto:{want!r}")
    pl = polars() if want in ("polars", "auto") else None
    if want == "polars" and pl is None:
        raise FrameAbsent(f"要 polars 但本境沒有:{POLARS_ERR} · 裝令:{install_hint()}")
    b = budget_bytes if budget_bytes is not None else budget()
    if pl is None:
        df = _run(con, sql, params).df()
        return df, {"backend": "pandas", "plan": "memory", "rows": len(df), "bytes": nbytes(df), "budget": b}
    est = estimate(con, sql, params)
    info = {"backend": "polars", "rows": est["rows"], "est_bytes": est["bytes"], "est_payload": est["payload"], "budget": b}
    if plan(est["bytes"], b) == "memory":
        return _run(con, sql, params).pl(), dict(info, plan="memory")
    if spill is None:
        raise ValueError("估算超過預算、要走 temp:請在 session() 裡呼叫,或傳 spill=")
    path = Path(spill) / f"frame_{uuid.uuid4().hex[:12]}.parquet"
    _run(con, f"COPY ({sql}) TO {_sql_str(str(path))} (FORMAT PARQUET)", params)
    return pl.scan_parquet(str(path)), dict(info, plan="temp", path=str(path))


def collect(obj):
    """LazyFrame → DataFrame:先串流引擎(polars ≥1.23 engine="streaming"),舊版退 streaming=True;別的原樣回。"""
    pl = polars()
    if pl is None or not isinstance(obj, pl.LazyFrame):
        return obj
    try:
        return obj.collect(engine="streaming")
    except Exception:
        return obj.collect(streaming=True)


def to_pandas(obj):
    pl = polars()
    if pl is not None and isinstance(obj, pl.LazyFrame):
        obj = collect(obj)
    if pl is not None and isinstance(obj, pl.DataFrame):
        return obj.to_pandas()
    return obj


class FrameSession:
    """一個受管溢寫夾 + 在夾裡的守門與取表(離開 session 即刪夾;先關連線再離開)。"""

    def __init__(self, d: Path, tag: str):
        self.dir, self.tag, self.applied = d, tag, []

    def guard(self, con, *, in_memory: bool = False, budget_bytes: int | None = None) -> dict:
        r = duck_guard(con, self.dir, in_memory=in_memory, budget_bytes=budget_bytes)
        self.applied.append(r)
        return r

    def frame(self, con, sql: str, params=None, *, want: str = "auto", budget_bytes: int | None = None):
        return frame(con, sql, params, want=want, spill=self.dir, budget_bytes=budget_bytes)


@contextlib.contextmanager
def session(tag: str = "frame"):
    with spill_dir(tag) as d:
        yield FrameSession(d, tag)


# ── 必要引擎覆蓋 ──
def coverage(via: Path | None = None) -> list:
    base = via or VIA
    rows = []
    for stem, folder, kind, why in NECESSARY:
        hits = [p for p in (base / folder).glob(stem + "_v*.py") if _vnum(p) >= 0]
        if not hits:
            rows.append({"family": stem, "tail": None, "kind": kind, "state": "ABSENT", "why": why})
            continue
        tail = max(hits, key=_vnum)
        text = tail.read_text(encoding="utf-8", errors="replace")
        if BRIDGE_BLOCK in text and "install_duckdb_guard" in text:
            state = "HAS"
        elif BRIDGE_MARK in text:
            state = "DRIFT"                 # 有標記但橋塊不是正典原文
        else:
            state = "MISSING"
        rows.append({"family": stem, "tail": tail.name, "kind": kind, "state": state, "why": why})
    return rows


# ── 狀態 / 探針 ──
def _ver(name: str) -> str | None:
    try:
        from importlib.metadata import version
        return version(name)
    except Exception:
        return None


def status() -> dict:
    avail, total, how = _mem()
    b = budget(available=avail) if avail else None
    pl = polars()
    stale = [r for r in sweep() if r["remove"]]
    cov = coverage()
    return {
        "engine": ENGINE_ID, "version": VERSION,
        "polars": {"state": "OK" if pl is not None else "ABSENT", "version": _ver("polars"),
                   "why": POLARS_ERR or None, "hint": None if pl is not None else install_hint()},
        "libs": {n: _ver(n) for n in ("duckdb", "pandas", "pyarrow", "psutil")},
        "memory": {"available": avail, "total": total, "probe": how, "fraction": fraction(), "budget": b},
        "temp": {"root": str(spill_root()), "from": ENV_TEMP if os.environ.get(ENV_TEMP, "").strip() else "system temp",
                 "stale_dirs": len(stale)},
        "guard": guard_state(),
        "coverage": {"has": sum(r["state"] == "HAS" for r in cov), "total": len(cov),
                     "missing": [r["family"] for r in cov if r["state"] != "HAS"]},
    }


def _mb(n) -> str:
    return "?" if n is None else f"{n / MIB:,.0f} MiB"


def print_status(st: dict | None = None) -> None:
    st = st or status()
    p, m, t, c = st["polars"], st["memory"], st["temp"], st["coverage"]
    print(f"=== {ENGINE_ID} {VERSION} · Polars 表格層 · 記憶體不足轉 temp ===")
    print(f"  polars    : {'OK ' + str(p['version']) if p['state'] == 'OK' else 'ABSENT · ' + str(p['why'])}")
    if p["hint"]:
        print(f"              裝令:{p['hint']}")
    print("  其他庫    : " + " · ".join(f"{k} {v or '缺'}" for k, v in st["libs"].items()))
    print(f"  記憶體    : 可用 {_mb(m['available'])} / 總 {_mb(m['total'])}({m['probe']})· "
          f"預算 {_mb(m['budget'])}(× {m['fraction']:g};{ENV_FRACTION})")
    print(f"  temp      : {t['root']}({t['from']})· 殘留夾 {t['stale_dirs']}(sweep --apply 清)")
    print(f"  必要引擎  : {c['has']}/{c['total']} 尾版帶 FRAME 橋與守門" + (f" · 缺 {', '.join(c['missing'])}" if c["missing"] else ""))


def probe() -> int:
    """環境能力:有 polars rc 0;沒有 = ABSENT rc 3(不是壞;裝是操作員的手)。"""
    pl = polars()
    if pl is not None:
        print(f"[OK] polars {_ver('polars')} · 表格層走 Polars 優先(記憶體不足時 LazyFrame 串流 + temp)")
        return 0
    print(f"[ABSENT] {POLARS_ERR} · 表格層退 pandas(`.df()` 零差異),DuckDB 守門照常 · 裝令:{install_hint()}")
    return 3


# ── 自測 ──
def selftest() -> int:
    results: list = []
    absent: list = []

    def chk(name, cond, note=""):
        results.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    import threading
    duckdb = _get("duckdb")
    pd = _get("pandas")
    print(f"=== {ENGINE_ID} {VERSION} · 自測(零網路;只在沙盒寫;檢數現場計)===")
    saved_env = {k: os.environ.get(k) for k in (ENV_TEMP, ENV_FRACTION, ENV_BACKEND, ENV_GUARD, "POLARS_TEMP_DIR")}
    saved_probes = list(_PROBES)
    cwd_before = set(os.listdir(os.getcwd()))
    sandbox = tempfile.mkdtemp(prefix="via_frame_selftest_")
    try:
        os.environ[ENV_TEMP] = os.path.join(sandbox, "root")
        for k in (ENV_FRACTION, ENV_BACKEND, ENV_GUARD):
            os.environ.pop(k, None)

        # ① polars 探針誠實
        pl = polars()
        os.environ[ENV_BACKEND] = "pandas"
        forced = polars()
        forced_err = POLARS_ERR
        os.environ.pop(ENV_BACKEND, None)
        pl = polars()
        chk("① polars 探針:有就回模組、沒有回 None 並留因由;VIA_FRAME_BACKEND=pandas 強制退回;裝令帶同一根釘、不代裝",
            (pl is not None or (POLARS_ERR and POLARS_PIN in install_hint())) and forced is None and "pandas" in forced_err,
            f"polars {'OK' if pl is not None else 'ABSENT'}")

        # ② 記憶體探針三條路
        a_ps = _mem()
        _PROBES[:] = [_mem_proc, _mem_windows]
        a_fb = _mem()
        _PROBES[:] = []
        a_none = _mem()
        _PROBES[:] = saved_probes
        chk("② 記憶體探針:psutil → /proc/meminfo → Windows API 依序退;全量不到 = None(不猜)",
            bool(a_ps[0]) and a_ps[0] > 0 and a_fb[0] is not None and a_fb[0] > 0 and a_none == (None, None, "unknown"),
            f"可用 {_mb(a_ps[0])} via {a_ps[2]} · 退路 {a_fb[2]}")

        # ③ 預算
        g = 1024 ** 3
        b_def = budget(available=8 * g)
        os.environ[ENV_FRACTION] = "0.25"
        b_env = budget(available=8 * g)
        os.environ[ENV_FRACTION] = "5"
        b_hi = budget(available=8 * g)
        os.environ[ENV_FRACTION] = "abc"
        b_bad = budget(available=8 * g)
        os.environ.pop(ENV_FRACTION, None)
        _PROBES[:] = []
        b_unknown = budget()
        _PROBES[:] = saved_probes
        chk("③ 預算 = 可用 × 比例(預設 0.5;環境變數可調;夾在 0.05–0.9;亂填回預設;下限 512 MiB;量不到 = None)",
            b_def == 4 * g and b_env == 2 * g and b_hi == int(8 * g * 0.9) and b_bad == 4 * g
            and budget(available=100 * MIB) == FLOOR and b_unknown is None,
            f"8 GiB → {_mb(b_def)}")

        # ④ 溢寫夾
        with spill_dir("selftest ④") as d4:
            inside = d4.parent == spill_root() and (d4 / MARKER).is_file() and _OURS.match(d4.name) is not None
        gone = not d4.exists()
        boom = ""
        try:
            with spill_dir("boom") as d4b:
                raise RuntimeError("boom")
        except RuntimeError as exc:          # 刻意丟的例外:要驗的是夾照樣刪、例外照樣往外傳
            boom = str(exc)
        chk("④ 溢寫夾:建在 VIA_TEMP_ROOT/VIA_spill 下(環境變數真的被聽)、帶標記;離開即刪,例外也刪(例外照樣往外傳)",
            spill_root() == Path(sandbox, "root", SPILL_NAME) and inside and gone and not d4b.exists() and boom == "boom",
            str(spill_root()))

        # ⑤ sweep
        root = spill_root()
        old = _make_spill("old")
        (old / MARKER).write_text(json.dumps({"pid": 999999999, "ts": time.time() - 48 * 3600}), encoding="utf-8")
        fresh = _make_spill("fresh")
        (fresh / MARKER).write_text(json.dumps({"pid": 999999999, "ts": time.time()}), encoding="utf-8")
        mine = _make_spill("mine")
        (mine / MARKER).write_text(json.dumps({"pid": os.getpid(), "ts": time.time() - 48 * 3600}), encoding="utf-8")
        foreign = root / "someone_123_abc"
        foreign.mkdir()
        (foreign / "keep.txt").write_text("x", encoding="utf-8")
        lookalike = root / "other_999999998_abcdefgh"          # 名字像本件、沒有標記、不是空的 = 別人的
        lookalike.mkdir()
        (lookalike / "keep.txt").write_text("x", encoding="utf-8")
        os.utime(lookalike, (time.time() - 72 * 3600,) * 2)
        empty_old = root / "lost_999999997_abcdefgh"           # 本件命名、空的、夠舊 = 當掉留下的空殼
        empty_old.mkdir()
        os.utime(empty_old, (time.time() - 72 * 3600,) * 2)
        dry = sweep(24, apply=False)
        still = all(p.exists() for p in (old, fresh, mine, foreign, lookalike, empty_old))
        done = sweep(24, apply=True)
        chk("⑤ sweep:只清「有標記或空、夠舊、行程已不在」的本件夾;乾跑不刪;新的、自己的、別人的(含名字像的)都不碰",
            still and not old.exists() and not empty_old.exists() and fresh.exists() and mine.exists()
            and foreign.exists() and lookalike.exists()
            and sum(r["remove"] for r in dry) == 2 and sum(r["removed"] for r in done) == 2)
        for p in (fresh, mine):
            _remove(p)
        for p in (foreign, lookalike):
            shutil.rmtree(p, ignore_errors=True)

        # ⑥ duck_guard(單條連線)
        dbp = os.path.join(sandbox, "g.duckdb")
        with spill_dir("guard") as d6:
            c = duckdb.connect(dbp)
            cur6 = _limit_bytes(_setting(c, "memory_limit"))
            r_small = duck_guard(c, d6, budget_bytes=256 * MIB)
            c.close()
            c = duckdb.connect(dbp)
            r_big = duck_guard(c, d6, budget_bytes=cur6 * 2)
            c.close()
            c = duckdb.connect(dbp, config={"memory_limit": "300MiB"})
            r_ex = duck_guard(c, d6, budget_bytes=64 * MIB, explicit={"memory_limit": "300MiB"})
            c.close()
            m = duckdb.connect()
            r_mem = duck_guard(m, d6, budget_bytes=64 * MIB, in_memory=True)
            mem_lim = _limit_bytes(r_mem["memory_limit"])
            m.close()
        chk("⑥ duck_guard:溢寫夾換成受管 temp;預算比現值小才收上限、大就不動;呼叫端 config 給的照它;記憶體庫只換夾不收上限",
            r_small["tightened"] and _limit_bytes(r_small["memory_limit"]) == 256 * MIB
            and r_small["temp_directory"] == str(d6) and not r_big["tightened"]
            and _limit_bytes(r_ex["memory_limit"]) == 300 * MIB and not r_ex["tightened"]
            and r_mem["temp_directory"] == str(d6) and not r_mem["tightened"] and mem_lim and mem_lim > 64 * MIB,
            f"現值 {_mb(cur6)} → {r_small['memory_limit']}")

        # ⑦ 行程守門裝 / 卸(先驗操作員的閥:off 就不裝)
        real = duckdb.connect
        os.environ[ENV_GUARD] = "off"
        st_off = install_duckdb_guard("off")
        off_ok = st_off["state"] == "OFF" and duckdb.connect is real
        os.environ.pop(ENV_GUARD, None)
        st = install_duckdb_guard("selftest⑦", budget_bytes=256 * MIB)
        again = install_duckdb_guard("again")

        def _local_open(path):
            import duckdb as _d          # 引擎都是函式裡才 import:要看得到守門
            return _d.connect(path)
        c = _local_open(dbp)
        t7 = _setting(c, "temp_directory")
        l7 = _limit_bytes(_setting(c, "memory_limit"))
        c.close()
        m = duckdb.connect()
        tm7 = _setting(m, "temp_directory")
        m.close()
        pol_env = os.environ.get("POLARS_TEMP_DIR")
        spill7 = Path(st["spill"])
        n_conn = st["connections"]
        un = uninstall_duckdb_guard()
        chk("⑦ 行程守門:VIA_FRAME_GUARD=off 不裝;函式裡 import 的 duckdb 也被守;檔案庫收上限、記憶體庫換夾;重裝冪等;"
            "POLARS_TEMP_DIR 同夾;卸下還原原函式、刪夾、還原環境",
            off_ok and st["state"] == "ON" and again.get("again") and t7 == str(spill7) and l7 == 256 * MIB and tm7 == str(spill7)
            and pol_env == str(spill7) and n_conn == 2 and un and duckdb.connect is real
            and not spill7.exists() and os.environ.get("POLARS_TEMP_DIR") == saved_env["POLARS_TEMP_DIR"])

        # ⑧ 記憶體不足 → temp(操作員令的本體)。GROUP BY 可以整段溢寫;視窗函數 DuckDB 不能全溢寫
        #    (實量 300 萬列 64 MiB 會 Out of Memory、128 MiB 過;1000 萬列 256 MiB 過)→ 預算下限 512 MiB 就是為它留的。
        big = os.path.join(sandbox, "big.duckdb")
        c = duckdb.connect(big)
        c.execute("CREATE TABLE t AS SELECT range AS i, repeat('x', 40) || range AS s FROM range(3000000)")
        q_agg = "SELECT count(*), sum(k % 97) FROM (SELECT s, min(i) AS k FROM t GROUP BY s)"
        q_win = ("SELECT count(*), sum(rn * (i % 97)) FROM "
                 "(SELECT i, row_number() OVER (ORDER BY s DESC) AS rn FROM t)")
        ref = c.execute(q_agg).fetchone()
        ref_win = c.execute(q_win).fetchone()
        c.close()

        def run_watch(budget_b, q8=q_agg):
            st8 = install_duckdb_guard("selftest⑧", budget_bytes=budget_b)
            sp = Path(st8["spill"])
            seen, stop = set(), [False]

            def watch():
                while not stop[0] and sp.is_dir():
                    seen.update(f for f in os.listdir(sp) if f.startswith("duckdb_temp"))
                    time.sleep(0.005)
            th = threading.Thread(target=watch, daemon=True)
            th.start()
            try:
                cc = duckdb.connect(big, read_only=True)
                got = cc.execute(q8).fetchone()
                lim = cc.execute("SELECT current_setting('memory_limit')").fetchone()[0]
                cc.close()
            finally:
                stop[0] = True
                th.join()
                uninstall_duckdb_guard()
            return got, seen, lim
        t0 = time.time()
        got_low, seen_low, lim_low = run_watch(64 * MIB)
        secs = time.time() - t0
        got_hi, seen_hi, _lim_hi = run_watch(None)
        got_win, _seen_win, lim_win = run_watch(FLOOR, q_win)
        chk("⑧ 記憶體不足 → temp:預算 64 MiB 時 300 萬組 GROUP BY 溢寫進受管 temp,結果與不設限一字不差;"
            "負控:預算充足時不溢寫;視窗函數(不能全溢寫)在預算下限 512 MiB 照樣過、結果一字不差",
            got_low == ref and got_hi == ref and bool(seen_low) and not seen_hi
            and got_win == ref_win and _limit_bytes(lim_win) == FLOOR,
            f"上限 {lim_low} · 溢寫檔 {len(seen_low)} 種 · {secs:.1f}s")

        # ⑨ pandas 取表與 .df() 一字不差
        c = duckdb.connect()
        c.execute("CREATE TABLE m AS SELECT range::INTEGER AS i, (range * 1.5)::DECIMAL(18,4) AS d, 'abc' || range AS s, "
                  "DATE '2024-01-01' + range::INTEGER AS dt, TIMESTAMP '2024-01-01' + INTERVAL (range) SECOND AS ts, "
                  "(range % 3 = 0) AS b, (range::HUGEINT * 10) AS h, NULL::BOOLEAN AS nb FROM range(50)")
        q9 = "SELECT * FROM m WHERE i >= ? ORDER BY i"
        os.environ[ENV_BACKEND] = "pandas"
        f9, i9 = frame(c, q9, [7])
        fa, ia = frame(c, q9, [7], want="auto")
        os.environ.pop(ENV_BACKEND, None)
        ok9 = True
        try:
            pd.testing.assert_frame_equal(f9, c.execute(q9, [7]).df())
            pd.testing.assert_frame_equal(fa, c.execute(q9, [7]).df())
        except AssertionError:
            ok9 = False
        chk("⑨ want=pandas(與 auto 在強制退回時)= `.df()` 一字不差(型別 · 順序 · 參數);說明帶列數與位元組",
            ok9 and i9["backend"] == ia["backend"] == "pandas" and i9["rows"] == 43 and i9["bytes"] > 0)

        # ⑩ 誠實路(一條檢,依本境有沒有 polars 判)
        fa2, ia2 = frame(c, q9, [7], want="auto")
        if pl is None:
            try:
                frame(c, q9, [7], want="polars")
                raised = ""
            except FrameAbsent as exc:
                raised = str(exc)
            ok10, note10 = ia2["backend"] == "pandas" and POLARS_PIN in raised, "本境沒 polars:auto 退 pandas、want=polars 拋 FrameAbsent 附裝令"
        else:
            ok10, note10 = ia2["backend"] == "polars" and ia2["plan"] == "memory", "本境有 polars:auto 走記憶體內 .pl()"
        chk("⑩ 誠實路:沒 polars → auto 退 pandas(零差異)、want=polars 誠實拋 FrameAbsent 附裝令;有 polars → auto 走 `.pl()`",
            ok10, note10)

        # ⑪ 估算:定長寬度 + 變長欄內文實量(Codex #369 P2)· 決策 plan()。期望值全寫死(自測拿常數比常數是恆真)
        e = estimate(c, "SELECT * FROM m WHERE i >= ?", [7])
        c.execute("CREATE TABLE w AS SELECT range::INTEGER AS i, repeat('é', 512) AS s, encode(repeat('y', 100))::BLOB AS bl, "
                  "[range, range + 1] AS li, NULL::VARCHAR AS nv FROM range(2000)")
        ew = estimate(c, "SELECT * FROM w")
        ed = estimate(c, 'SELECT s AS a, s AS a, s AS "x""y" FROM w')
        parts11 = {
            # INTEGER 4 · DECIMAL 8 · VARCHAR 視圖 16 · DATE 4 · TIMESTAMP 8 · BOOL 1 · HUGEINT 16 · BOOL 1;內文 'abc7'…'abc9' 3×4 + 'abc10'…'abc49' 40×5
            "定長": e["rows"] == 43 and e["width"] == 58 and e["payload"] == 212 and e["bytes"] == 2706,
            # 'é'×512 = 1 KiB(UTF-8 位元組,不是字元數)2,048,000 · BLOB 100×2000 · BIGINT[] 文字 21,783 · 全 NULL 0;寬 4+16+16+16+16
            "變長": ew["rows"] == 2000 and ew["width"] == 68 and ew["payload"] == 2_269_783 and ew["bytes"] == 2_405_783,
            "重名怪名": ed["bytes"] == 6_240_000 and ed["varlen"] == ["a", "a_1", 'x"y'],   # 3 × 2,048,000 + 2000 × 48
            "決策": (plan(ew["bytes"], 1 << 20) == "temp" and plan(2000 * 116, 1 << 20) == "memory"
                     and plan(10, 10) == "memory" and plan(11, 10) == "temp" and plan(10 ** 12, None) == "memory"),
        }
        chk("⑪ estimate:列數實數、參數照帶;位元組 = 列數 × 定長寬度 + 變長欄內文實量(1 KiB 字串 · BLOB · 巢狀 · 全 NULL · 重名欄);"
            "plan():≤ 預算走記憶體、超過走 temp、預算量不到不收",
            all(parts11.values()),
            " · ".join(k for k, v in parts11.items() if not v) or f"1 KiB 字串 2000 列估 {ew['bytes']:,} B(舊法一律 32 B 只估 232,000 B,1 MiB 預算下會誤走 .pl())")

        # ⑫ polars 一致性(只在有 polars 的境跑;沒有 = ABSENT,不算綠也不算紅)
        q12 = "SELECT i, s, dt, b FROM m WHERE i >= ? ORDER BY i"
        if pl is not None:
            with session("selftest⑫") as fs:
                mem_df, mi = fs.frame(c, q12, [3], want="polars")
                lf, ti = fs.frame(c, q12, [3], want="polars", budget_bytes=1)
                rows_ref = c.execute(q12, [3]).fetchall()
                spilled = Path(ti.get("path", "")).is_file()
                ok12 = (mi["plan"] == "memory" and ti["plan"] == "temp" and spilled
                        and mem_df.rows() == rows_ref and collect(lf).rows() == rows_ref)
            chk("⑫ polars 一致:記憶體內 `.pl()` 與 temp parquet → LazyFrame 串流,兩路逐列 = DuckDB 原值;離開 session 刪檔",
                ok12 and not Path(ti["path"]).exists())
        else:
            absent.append("⑫")
            print("  [ABSENT] ⑫ polars 一致性(記憶體內 .pl() · temp parquet → LazyFrame 串流)· 本境沒有 polars;"
                  "裝了之後自測自動跑這一檢(probe 動詞 rc 3 = 本境能力缺,不是壞)")
        c.close()

        # ⑬ 必要引擎覆蓋
        cov = coverage()
        bad = [f"{r['family']}={r['state']}" for r in cov if r["state"] != "HAS"]
        fake = Path(sandbox, "fakevia")                          # 負控:改過一個字的橋 = DRIFT;沒橋 = MISSING;沒檔 = ABSENT
        s0, f0 = NECESSARY[0][0], NECESSARY[0][1]
        s1, f1 = NECESSARY[1][0], NECESSARY[1][1]
        (fake / f0).mkdir(parents=True, exist_ok=True)
        (fake / f1).mkdir(parents=True, exist_ok=True)
        (fake / f0 / f"{s0}_v0100.py").write_text("x = 1\n", encoding="utf-8")
        (fake / f0 / f"{s0}_v0101.py").write_text(BRIDGE_BLOCK.replace("graceful", "gracefull")
                                                   + "install_duckdb_guard\n", encoding="utf-8")
        (fake / f1 / f"{s1}_v0100.py").write_text("install_duckdb_guard\n", encoding="utf-8")
        neg = {r["family"]: r["state"] for r in coverage(fake)}
        chk(f"⑬ 必要引擎 {len(NECESSARY)} 支:尾版都帶正典 FRAME 橋並裝守門(N1 撈大表 4 · N2 全歷史重算 7);"
            "負控:橋改一個字 = DRIFT、沒橋 = MISSING、沒檔 = ABSENT(只看尾版)",
            not bad and neg.get(s0) == "DRIFT" and neg.get(s1) == "MISSING" and neg.get(NECESSARY[2][0]) == "ABSENT",
            "; ".join(bad[:6]) or f"{len(cov)}/{len(cov)}")
    finally:
        _PROBES[:] = saved_probes
        uninstall_duckdb_guard()
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        leftovers = [str(p) for p in Path(sandbox, "root", SPILL_NAME).glob("*")] if os.path.isdir(sandbox) else []
        shutil.rmtree(sandbox, ignore_errors=True)
    new_in_cwd = sorted(set(os.listdir(os.getcwd())) - cwd_before)
    chk("⑭ 零足跡:沙盒溢寫夾全清、工作夾沒多出 .tmp、環境變數還原", not leftovers and not new_in_cwd,
        "; ".join((leftovers + new_in_cwd)[:4]))
    passed = all(results)
    tail = f" · ABSENT {len(absent)}({'、'.join(absent)}:本境無 polars)" if absent else ""
    print(f"  {ENGINE_ID}_{VERSION} selftest {sum(results)}/{len(results)} {'PASS' if passed else 'FAIL'}{tail}")
    return 0 if passed else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args or args[:1] == ["selftest"]:
        return selftest()
    verb = args[0] if args else "status"
    if verb == "status":
        if "--json" in args:
            print(json.dumps(status(), ensure_ascii=False, indent=1))
        else:
            print_status()
        return 0
    if verb == "probe":
        return probe()
    if verb == "sweep":
        hours = 24.0
        if "--hours" in args and args.index("--hours") + 1 < len(args):
            hours = float(args[args.index("--hours") + 1])
        rows = sweep(hours, apply="--apply" in args)
        print(f"=== {ENGINE_ID} sweep · {spill_root()} · {'清' if '--apply' in args else '乾跑'} · 門檻 {hours:g} 小時 ===")
        for r in rows:
            print(f"  [{'清' if r['remove'] else '留'}] {r['dir']} · pid {r['pid']} · {r['why']}")
        print(f"  共 {len(rows)} 夾 · 該清 {sum(r['remove'] for r in rows)} · 已清 {sum(r['removed'] for r in rows)}")
        return 0
    if verb == "coverage":
        rows = coverage()
        for r in rows:
            print(f"  [{r['state']:7s}] {r['kind']} {r['family']} · {r['tail'] or '-'} · {r['why']}")
        print(f"  必要引擎 {sum(r['state'] == 'HAS' for r in rows)}/{len(rows)} 帶 FRAME 橋與守門")
        return 0 if all(r["state"] == "HAS" for r in rows) else 1
    print("用法:status [--json] | probe | sweep [--apply] [--hours N] | coverage | --selftest")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
