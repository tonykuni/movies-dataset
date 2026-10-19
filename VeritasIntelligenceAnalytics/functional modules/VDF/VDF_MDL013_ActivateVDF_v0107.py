#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL013_ActivateVDF v0107 — 薄尾:記憶體 / TEMP 本輪真生效(DuckDB 溢寫到本機 TEMP · 記憶體與執行緒照每條流程預算)+ 起跑實測

操作員令(2026-10-19):「繼續 跑完貼回結果 對於記憶體跟TEMP支援方式用最快最佳的方法 自動完成」。
量測(改前):v0100 起每條流程已給子行程 TMP / TEMP / TMPDIR / POLARS_TEMP_DIR / VIA_DUCKDB_TEMP_DIR(本輪 temp 夾)·
  VIA_DUCKDB_MEM(每條預算)· 執行緒上限;但 VDF 有 267 支直接 duckdb.connect(),**DuckDB 不讀環境變數** ——
  只有 VCGC 的 CGC_MDL262_DuckTempHook 代裝進環境(.pth)後,connect 才會補 temp_directory / memory_limit。
  沒裝那個鉤的境:DuckDB 溢寫檔落在**資料庫旁邊**(工作站 = OneDrive 夾,同步拖慢)、每支行程各吃實體記憶體 80%、
  執行緒 = 全部核(三條流程並行時互搶)。
最快最佳解(不改任何引擎、不裝進環境、不改他系統):
  ① 每輪把一支小啟動鉤寫進**本輪 temp 夾**(<temp>/ActivateVDF/run_*/pyhook/sitecustomize.py;不在倉內,舊輪照滾動清),
     放在子行程 PYTHONPATH **最後**。中央 bootstrap 的 sitecustomize 本來就會接力「sys.path 上下一份同名檔」→ 跑到本鉤;
     沒有 bootstrap 時本鉤就是那一份。本鉤跑完再往**後面**接力(原本會載的那一份照載,不遞迴、不回頭)。
  ② 鉤只在 duckdb 被 import 那一刻掛(沒用 duckdb 的行程零成本);每個 connect() 呼叫端沒給的才補:
     temp_directory = VIA_DUCKDB_TEMP_DIR/p<pid>(本機 TEMP · 每行程一夾不撞檔)· memory_limit = VIA_DUCKDB_MEM(每條預算,超過落 TEMP)·
     threads = VIA_DUCKDB_THREADS(每條執行緒;三條並行不互搶)。呼叫端自己給的照舊優先。子行程再起的孫行程同樣生效(環境繼承)。
  ③ 環境已裝 VCGC 的 via_duck_temp 鉤 → 本鉤讓位(不疊兩層);VIA_DUCK_TEMP=0 → 整個不掛(回原生 duckdb)。
  ④ 起跑實測(約 1 秒):用流程同一支 python 起子行程開一次 duckdb,讀回 temp_directory · memory_limit · threads 與是哪個鉤生效;
     temp 根在 OneDrive / 剩餘空間 < 2 GB 照實標黃。結果進總覽 JSON(resources.memtemp)、終端一行、總覽頁一張卡。
  ⑤ 只在本版的一輪裡生效(前版自測照舊,不碰它們驗的 PYTHONPATH)。
其餘全照 v0106。VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib;不裝套件、不寫環境。
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
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
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

import html
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL013_ActivateVDF"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0107(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0107(p) < _vnum_v0107(__file__)), key=_vnum_v0107)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():                    # 同 v0102:前版鏈只擋載入那一刻的編譯警告
    warnings.simplefilter("ignore", SyntaxWarning)
    warnings.simplefilter("ignore", DeprecationWarning)
    _spec.loader.exec_module(PRIOR)
V0100 = PRIOR.V0100


def __getattr__(name):
    return getattr(PRIOR, name)


HOOK_TAG = "vdf-activate-v0107"
HOOK_SRC = r"""# VDF ActivateVDF 本輪 DuckDB TEMP / 記憶體 / 執行緒掛鉤(VDF_MDL013_ActivateVDF v0107 每輪寫進本輪 temp 夾;不在倉內、不進環境)
# 中央 bootstrap 接力到本檔,或本檔就是第一份 sitecustomize;跑完往 sys.path 後面接力(不回頭、不遞迴)。VIA_DUCK_TEMP=0 不掛。
import os, sys
_TAG = "vdf-activate-v0107"


def _defaults():
    d = {}
    base = os.environ.get("VIA_DUCKDB_TEMP_DIR")
    if base and os.path.isdir(base):
        d["temp_directory"] = os.path.join(base, "p%d" % os.getpid())
    if os.environ.get("VIA_DUCKDB_MEM"):
        d["memory_limit"] = os.environ["VIA_DUCKDB_MEM"]
    try:
        th = int(os.environ.get("VIA_DUCKDB_THREADS") or 0)
    except ValueError:
        th = 0
    if th > 0:
        d["threads"] = th
    return d


def _patch(mod):
    if getattr(mod, "_via_duck_temp", None):
        return mod
    orig = mod.connect

    def connect(*args, **kw):
        try:
            a = list(args)
            cfg = dict((a[2] if len(a) >= 3 else kw.get("config")) or {})
            for k, v in _defaults().items():
                cfg.setdefault(k, v)
            if len(a) >= 3:
                a[2] = cfg
            else:
                kw["config"] = cfg
            return orig(*a, **kw)
        except TypeError:
            return orig(*args, **kw)

    connect.__doc__ = orig.__doc__
    connect.__wrapped__ = orig
    mod.connect = connect
    mod._via_duck_temp = _TAG
    return mod


class _VdfDuckFinder:
    def find_spec(self, name, path=None, target=None):
        if name != "duckdb":
            return None
        try:
            sys.meta_path.remove(self)
        except ValueError:
            pass
        import importlib.util
        spec = importlib.util.find_spec("duckdb")
        if spec is None or spec.loader is None or not hasattr(spec.loader, "exec_module"):
            return spec
        real = spec.loader.exec_module

        def exec_module(module):
            real(module)
            try:
                _patch(module)
            except Exception:  # noqa: BLE001 — 掛不上 = 原生 duckdb 照用
                return
        spec.loader.exec_module = exec_module
        return spec


def _install():
    if os.environ.get("VIA_DUCK_TEMP", "1") == "0" or "via_duck_temp" in sys.modules:
        return                                     # 關掉 / 環境已有 VCGC 的鉤 → 讓它管,不疊兩層
    if "duckdb" in sys.modules:
        _patch(sys.modules["duckdb"])
    elif not any(type(f).__name__ == "_VdfDuckFinder" for f in sys.meta_path):
        sys.meta_path.insert(0, _VdfDuckFinder())


def _chain_after_me():
    here = os.path.dirname(os.path.abspath(__file__))
    seen = False
    for d in list(sys.path):
        if d and os.path.abspath(d) == here:
            seen = True
            continue
        if not seen or not d:
            continue
        cand = os.path.join(d, "sitecustomize.py")
        if os.path.isfile(cand):
            import runpy
            try:
                runpy.run_path(cand, run_name="sitecustomize_after_vdf")
            except Exception:  # noqa: BLE001 — 後面那份壞了不連累本行程
                return
            return


try:
    _install()
except Exception:  # noqa: BLE001
    pass
try:
    _chain_after_me()
except Exception:  # noqa: BLE001
    pass
"""

PROBE = r"""
import json, os, sys
out = {"python": sys.version.split()[0], "hook": None}
try:
    import duckdb
except ImportError:
    out["duckdb"] = None
else:
    out["duckdb"] = duckdb.__version__
    out["hook"] = getattr(duckdb, "_via_duck_temp", None)
    c = duckdb.connect()
    for k in ("temp_directory", "memory_limit", "threads"):
        try:
            out[k] = str(c.execute("select current_setting('%s')" % k).fetchone()[0])
        except Exception as exc:
            out[k] = "?" + type(exc).__name__
    c.close()
print("VDFPROBE " + json.dumps(out))
"""

_RUN7 = {"on": False, "py": None}
_LOCK7 = threading.Lock()


def hook_dir(res: dict) -> Path:
    """本輪鉤夾 = <本輪 temp>/pyhook;沒有就寫(冪等;內容不同就換新)。"""
    d = Path(res["temp_run"]) / "pyhook"
    f = d / "sitecustomize.py"
    if not (f.is_file() and f.read_text(encoding="utf-8") == HOOK_SRC):
        d.mkdir(parents=True, exist_ok=True)
        f.write_text(HOOK_SRC, encoding="utf-8")
    return d


def with_hook(env: dict, res: dict) -> dict:
    """子行程環境加本輪鉤:鉤夾放 PYTHONPATH 最後(中央 bootstrap 在前就由它接力;沒有就本鉤是第一份)。"""
    d = str(hook_dir(res))
    parts = [p for p in (env.get("PYTHONPATH") or "").split(os.pathsep)] if env.get("PYTHONPATH") else []
    if d not in parts:
        parts.append(d)
    env["PYTHONPATH"] = os.pathsep.join(parts)
    env["VIA_VDF_DUCK_HOOK"] = d
    return env


_FLOW_ENV_PRIOR = V0100.flow_env                   # = v0104 的 flow_env(v0102 numexpr + bootstrap 去重)


def flow_env(res: dict, flow: str, base_env: dict | None = None) -> dict:
    """同前版 flow_env;本版一輪裡多加本輪 DuckDB 鉤(前版自測照舊,不加)。"""
    env = _FLOW_ENV_PRIOR(res, flow, base_env)
    return with_hook(env, res) if _RUN7["on"] else env


def _bytes(s) -> float | None:
    """大小字串 → 位元組:'687MB' 十進位(DuckDB 的 MB = 1000²)· '655.1 MiB' 二進位;認不出 = None。"""
    m = re.match(r"\s*([\d.]+)\s*([KMGT])(i?)B", str(s or ""), re.I)
    if not m:
        return None
    n = "KMGT".index(m.group(2).upper()) + 1
    return float(m.group(1)) * ((1024 if m.group(3) else 1000) ** n)


def probe_memtemp(res: dict, py: str | None = None, timeout: float = 60) -> dict:
    """起跑實測:用流程同一支 python、同一份流程環境起子行程開一次 duckdb,讀回實際生效的 temp / 記憶體 / 執行緒。"""
    env = flow_env(res, "probe")
    plan = res["plan"]
    want_tmp = env.get("VIA_DUCKDB_TEMP_DIR") or ""
    root = str(Path(res["temp_run"]).parent.parent)
    out = {"temp_root": root, "temp_free_mb": res.get("temp_free_mb"), "want_mem_mb": plan.get("duckdb_mem_mb"),
           "want_threads": plan.get("threads_per_flow"), "hook_dir": env.get("VIA_VDF_DUCK_HOOK")}
    try:
        cp = subprocess.run([py or sys.executable, "-c", PROBE], env=env, capture_output=True, text=True, timeout=timeout,
                            encoding="utf-8", errors="replace")
        line = next((ln for ln in cp.stdout.splitlines() if ln.startswith("VDFPROBE ")), None)
        got = json.loads(line[9:]) if line else {}
        if not line:
            out["why"] = "子行程沒回實測(rc %s):%s" % (cp.returncode, (cp.stderr or "").strip()[-160:])
    except subprocess.TimeoutExpired:
        got, out["why"] = {}, "子行程實測逾時 %d 秒" % timeout
    except OSError as exc:
        got, out["why"] = {}, "起不了子行程:%s" % type(exc).__name__
    out.update(got)
    td = str(got.get("temp_directory") or "")
    mem = _bytes(got.get("memory_limit"))
    want_mem = _bytes(env.get("VIA_DUCKDB_MEM"))
    notes, lamp = [], "GREEN"
    if got.get("duckdb") is None:
        lamp, notes = "YELLOW", ["這支 python 沒有 duckdb(不代裝)"]
    else:
        out["temp_ok"] = bool(want_tmp) and os.path.normcase(os.path.abspath(td)).startswith(os.path.normcase(os.path.abspath(want_tmp)))
        out["mem_ok"] = mem is not None and bool(want_mem) and abs(mem - want_mem) <= 0.05 * want_mem
        out["threads_ok"] = str(got.get("threads")) == str(plan.get("threads_per_flow"))
        if not (out["temp_ok"] and out["mem_ok"] and out["threads_ok"]):
            lamp = "YELLOW"
            notes.append("沒生效:" + " · ".join(k for k, ok in (("TEMP", out["temp_ok"]), ("記憶體", out["mem_ok"]), ("執行緒", out["threads_ok"])) if not ok))
    if "onedrive" in root.lower():
        lamp = "YELLOW"
        notes.append("temp 根在 OneDrive(同步拖慢):設 VIA_TEMP_ROOT 指到本機磁碟")
    if res.get("temp_low"):
        lamp = "YELLOW"
        notes.append("temp 剩 %s MB(< 2 GB)" % res.get("temp_free_mb"))
    out["lamp"] = lamp if not out.get("why") else "YELLOW"
    hook = {HOOK_TAG: "VDF 本輪鉤"}.get(str(out.get("hook")), ("VCGC 環境鉤 " + str(out.get("hook"))) if out.get("hook") else "無")
    out["summary"] = ("DuckDB 溢寫 → %s · 記憶體 %s(預算 %s MB)· 執行緒 %s · 鉤 %s · temp 剩 %s MB" % (
        td or "—", got.get("memory_limit") or "—", plan.get("duckdb_mem_mb"), got.get("threads") or "—", hook, res.get("temp_free_mb"))
        + (" · " + ";".join(notes) if notes else "") + (" · " + out["why"] if out.get("why") else ""))
    return out


_OPT_PRIOR = V0100.optimize_resources


def optimize_resources(want: int = 3, stamp: str | None = None, root: Path | None = None) -> dict:
    """同 v0100;本版一輪裡多做起跑實測(記憶體 / TEMP 真生效嗎),結果放 res['memtemp']。"""
    res = _OPT_PRIOR(want=want, stamp=stamp, root=root)
    if _RUN7["on"]:
        res["memtemp"] = probe_memtemp(res, _RUN7["py"])
        print(f"  ①b 記憶體 / TEMP {res['memtemp']['lamp']}:{res['memtemp']['summary']}", flush=True)
    return res


def _chain_modules():
    m, out = PRIOR, []
    for _ in range(16):
        out.append(m)
        m = vars(m).get("PRIOR")
        if m is None:
            break
    return out


for _m in _chain_modules():                        # 前版鏈各自叫模組全域的 flow_env / optimize_resources → 換上本版(冪等)
    if "flow_env" in vars(_m):
        _m.flow_env = flow_env
    if "optimize_resources" in vars(_m):
        _m.optimize_resources = optimize_resources

_RENDER_V0106 = V0100.render_html


def memtemp_card(mt: dict | None) -> str:
    if not mt:
        return ""
    c = {"GREEN": "#1a7f37", "YELLOW": "#9a6700"}.get(mt.get("lamp"), "#cf222e")
    return (f'<section id="mem-temp" class="card" style="margin:12px 0"><b>記憶體 / TEMP</b> '
            f'<span class="lamp" style="background:{c}">{html.escape(str(mt.get("lamp")))}</span><br>'
            f'{html.escape(str(mt.get("summary")))}<br><span class="mut">DuckDB 溢寫到本機 TEMP(不落資料庫旁的 OneDrive 夾)· 記憶體與執行緒照每條流程預算 · '
            f'呼叫端自己給的設定優先 · VIA_DUCK_TEMP=0 可關</span></section>')


def render_html(card: dict, ui_dir: Path) -> str:
    h = _RENDER_V0106(card, ui_dir)
    sec = memtemp_card((card.get("resources") or {}).get("memtemp"))
    if not sec:
        return h
    i = h.find('<section id="db-inventory"')
    if i < 0:
        i = h.find('<div class="wrap"><table>')
    return (h[:i] + sec + h[i:]) if i >= 0 else h.replace("</body>", sec + "</body>")


V0100.render_html = render_html
_ACTIVATE_V0106 = PRIOR.activate


def activate(opt, manager: Path | None = None, py: str | None = None, temp: Path | None = None) -> dict:
    """同 v0106 activate;本輪開記憶體 / TEMP 鉤與起跑實測(只在本輪)。"""
    keep = PRIOR.TAG
    PRIOR.TAG = TAG
    with _LOCK7:
        _RUN7["on"], _RUN7["py"] = True, py
    try:
        card = _ACTIVATE_V0106(opt, manager, py, temp)
    finally:
        PRIOR.TAG = keep
        with _LOCK7:
            _RUN7["on"], _RUN7["py"] = False, None
    return card


_WRITE_REPORT_V0106 = V0100.write_report


def write_report(card: dict, ui_dir: Path | None = None) -> dict:
    """同 v0106(先標本版再落檔);本版一輪裡 schema 標 v0107。"""
    if _RUN7["on"]:
        prev = PRIOR._WRITE_REPORT_V0100

        def _stamp_then_write(c, u=None):
            c["schema"], c["tag"] = "VDF_ActivateVDF_v0107", TAG
            return prev(c, u) if u is not None else prev(c)
        PRIOR._WRITE_REPORT_V0100 = _stamp_then_write
        try:
            return _WRITE_REPORT_V0106(card, ui_dir) if ui_dir is not None else _WRITE_REPORT_V0106(card)
        finally:
            PRIOR._WRITE_REPORT_V0100 = prev
    return _WRITE_REPORT_V0106(card, ui_dir) if ui_dir is not None else _WRITE_REPORT_V0106(card)


V0100.write_report = write_report

for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


# ---------------------------------------------------------------- 自測
_FAKE_BOOT = """import os, runpy, sys
open(os.environ['VDF_T_MARK'], 'a').write('boot\\n')
here = os.path.dirname(os.path.abspath(__file__))
for d in list(sys.path):
    if not d or os.path.abspath(d) == here:
        continue
    c = os.path.join(d, 'sitecustomize.py')
    if os.path.isfile(c):
        runpy.run_path(c, run_name='sitecustomize_shadowed')
        break
"""
_FAKE_TAIL = "import os\nopen(os.environ['VDF_T_MARK'], 'a').write('tail\\n')\n"
_FAKE_VCGC = "import via_duck_temp\n" + _FAKE_BOOT          # 環境鉤(.pth)先載 via_duck_temp,bootstrap 照樣接力到本鉤
_GRANDCHILD = ("import subprocess, sys, os\n"
               "print(subprocess.run([sys.executable, '-c', sys.argv[1]], capture_output=True, text=True, env=os.environ).stdout)")


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 薄尾自測(記憶體 / TEMP 本輪鉤 + 起跑實測;沙盒 · 零網路)===")
    try:
        import duckdb  # noqa: F401
        have_duck = True
    except ImportError:
        have_duck = False
    with tempfile.TemporaryDirectory(prefix="activatevdf107_") as td:
        t = Path(td)
        res = V0100.optimize_resources(want=3, stamp="20261019_120000", root=t)
        plan = res["plan"]
        base = dict(os.environ)
        for k in ("PYTHONPATH", "VIA_DUCK_TEMP", "VIA_VDF_DUCK_HOOK"):   # 自測可能在一輪真跑裡被啟動(引擎啟動檢查)→ 父輪的鉤標記不帶進來
            base.pop(k, None)
        mark = t / "mark.txt"
        _RUN7["on"] = True
        try:
            env = flow_env(res, "engines", base_env=dict(base))
            env_off = dict(env, VIA_DUCK_TEMP="0")
            probe = probe_memtemp(res) if have_duck else {}
        finally:
            _RUN7["on"] = False
        plain = flow_env(res, "engines", base_env=dict(base))
        hd = env.get("VIA_VDF_DUCK_HOOK", "")

        def run(e, code=PROBE, extra=()):
            e = dict(e, VDF_T_MARK=str(mark))
            cp = subprocess.run([sys.executable, *extra, "-c", code] if not extra else [sys.executable, "-c", _GRANDCHILD, PROBE],
                                env=e, capture_output=True, text=True, timeout=120)
            line = next((ln for ln in cp.stdout.splitlines() if ln.startswith("VDFPROBE ")), None)
            return json.loads(line[9:]) if line else {"rc": cp.returncode, "err": cp.stderr[-300:]}

        chk("㉙ 本輪環境:鉤夾在本輪 temp(不在倉內)且排 PYTHONPATH 最後;前版自測的環境不加鉤(它們驗的 PYTHONPATH 照舊)",
            hd and Path(hd).is_relative_to(Path(res["temp_run"])) and env["PYTHONPATH"].split(os.pathsep)[-1] == hd
            and (Path(hd) / "sitecustomize.py").read_text(encoding="utf-8") == HOOK_SRC and "VIA_VDF_DUCK_HOOK" not in plain
            and hd not in (plain.get("PYTHONPATH") or ""), env.get("PYTHONPATH"))
        if not have_duck:
            chk("㉟ duckdb 不在本境 → 只驗環境與接力(不代裝;㉚ ㉜ 要 duckdb 才跑)", True)
        else:
            want_tmp = env["VIA_DUCKDB_TEMP_DIR"]
            got, grand, off = run(env), run(env, extra=("grand",)), run(env_off)
            mem = _bytes(got.get("memory_limit"))
            chk("㉚ 子行程與孫行程的 duckdb.connect() 都生效:溢寫夾 = 本輪流程 temp/p<pid> · 記憶體 = 每條預算 · 執行緒 = 每條執行緒;"
                "VIA_DUCK_TEMP=0 → 不掛(回原生);起跑實測 GREEN 且三項都 ok",
                got.get("hook") == HOOK_TAG and str(got.get("temp_directory", "")).startswith(want_tmp)
                and mem and abs(mem - plan["duckdb_mem_mb"] * 1e6) <= 0.05 * plan["duckdb_mem_mb"] * 1e6
                and str(got.get("threads")) == str(plan["threads_per_flow"])
                and grand.get("hook") == HOOK_TAG and str(grand.get("temp_directory", "")).startswith(want_tmp)
                and off.get("hook") is None and not str(off.get("temp_directory", "")).startswith(want_tmp)
                and probe.get("lamp") == "GREEN" and probe.get("temp_ok") and probe.get("mem_ok") and probe.get("threads_ok"),
                {"子": {k: got.get(k) for k in ("hook", "memory_limit", "threads")}, "孫": grand.get("hook"), "關": off.get("hook"),
                 "實測": probe.get("summary")})
        # 接力:假 bootstrap 在前 + 假「發行版」sitecustomize 在後 → 三份各跑一次、照順序
        boot, tail = t / "boot", t / "tail"
        boot.mkdir()
        tail.mkdir()
        (boot / "sitecustomize.py").write_text(_FAKE_BOOT, encoding="utf-8")
        (tail / "sitecustomize.py").write_text(_FAKE_TAIL, encoding="utf-8")
        code = "import sys; print('duckdb loaded' if 'duckdb' in sys.modules else 'no duckdb')"

        outs = []

        def marks(pp):
            mark.write_text("", encoding="utf-8")
            e = dict(env, PYTHONPATH=os.pathsep.join(pp), VDF_T_MARK=str(mark))
            cp = subprocess.run([sys.executable, "-c", code], env=e, capture_output=True, text=True, timeout=60)
            outs.append(cp.stdout.strip())
            return mark.read_text(encoding="utf-8").split()

        with_boot = marks([str(boot), hd, str(tail)])
        alone = marks([hd, str(tail)])
        chk("㉛ 接力:中央 bootstrap 在前 → bootstrap 跑一次、接力到本鉤、本鉤再往後接力(後面那份照跑一次,不遞迴不回頭);"
            "沒有 bootstrap → 本鉤就是第一份,後面那份照跑一次;沒用 duckdb 的行程不預先 import duckdb",
            with_boot == ["boot", "tail"] and alone == ["tail"] and outs == ["no duckdb", "no duckdb"],
            {"有 bootstrap": with_boot, "沒有": alone, "duckdb 預載": outs})
        if have_duck:
            vc = t / "vcgc"
            vc.mkdir()
            (vc / "via_duck_temp.py").write_text("HOOK_VERSION = 'v0100'\n", encoding="utf-8")
            (vc / "sitecustomize.py").write_text(_FAKE_VCGC, encoding="utf-8")
            e = dict(env, PYTHONPATH=os.pathsep.join([str(vc), hd]), VDF_T_MARK=str(mark))
            got2 = run(e)
            chk("㉜ 環境已有 VCGC 的 via_duck_temp 鉤 → 本鉤讓位(不疊兩層):本行程 duckdb 不被本鉤包",
                got2.get("hook") != HOOK_TAG and "duckdb" in json.dumps(got2), got2.get("hook"))
        mt = {"lamp": "YELLOW", "summary": "DuckDB 溢寫 → <x> · 記憶體 1 MiB"}
        page = memtemp_card(mt)
        chk("㉝ 總覽頁「記憶體 / TEMP」卡:燈 + 實測一句(跳脫);沒實測 = 不出卡",
            'id="mem-temp"' in page and "&lt;x&gt;" in page and "<x>" not in page and memtemp_card(None) == "")
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    chk("㉞ 加速器橋 · 網路橋在;不匯入他系統程式;不碰 TA-Lib;同意閘不寫;不裝套件、不寫環境(鉤只寫本輪 temp 夾)",
        "VIA:ACCEL-BRIDGE" in src and "def _via_net" in src
        and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VCGC"))]
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
        and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src)
        and ("pip" + " install") not in src and ("site" + "-packages") not in src)
    n = sum(ok)
    print(f"  [計] {TAG} 本版 {n}/{len(ok)} · {'PASS' if n == len(ok) else 'FAIL'}")
    if n != len(ok):
        return 1
    rc1 = PRIOR.selftest()
    return rc1 if rc1 in (0, 1, 2, 3) else 1        # 前版紅照實回(同 v0102;PR #528 Codex P1)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    opt = V0100.parse(argv)
    if opt.verb != "run":
        return V0100.main(argv)
    card = activate(opt)
    return {"GREEN": 0, "YELLOW": 2, "INTERRUPTED": 130}.get(card["lamp"], 1)


if __name__ == "__main__":
    raise SystemExit(main())
