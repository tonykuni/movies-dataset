#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL262_DuckTempHook v0100 — DuckDB「TEMP 為主 · 記憶體為輔」環境掛鉤(L107 · L111 ④ VCGC 代裝環境)

操作員令(2026-10-05):「VCGC VDF VRN 有很多種型引擎 · 善用 TEMP 為主記憶體為輔 · 思考最佳解決方式加快 ·
  TEMP 的使用及輕框方式管理方式 · DUCKDB 管理資料庫顯示方式」。

量測(容器 · 呼叫 duckdb.connect 的尾版):VCGC 30 支設 temp_directory 0 · VDF 46 支 7 · VRN 32 支 0 · SUP 70 支 2。
  共用件 SUP_MDL867_TempSpill.connect() 早就有,缺的是「採用」;178 支逐支改 = 子系統正本(L111 不准 VCGC 動)且慢。
最佳解:不改任何引擎,改**環境**。VCGC 代裝一個 .pth 啟動鉤進各家族境(像 tabula 境的 Java 鉤):
  ① duckdb 被 import 的那一刻才掛(沒用 duckdb 的行程零成本,不預先 import)
  ② 之後每個 duckdb.connect():呼叫端沒給的才補 —
       temp_directory = $VIA_DUCKDB_TEMP_DIR(PS 骨架每輪設)或 VIA_TEMP_ROOT/duckdb · 再分 p<pid> 子夾(多行程不撞檔)
       memory_limit   = $VIA_DUCKDB_MEM(例 8GB)或實體記憶體 × VIA_DUCKDB_MEM_PCT(預設 50%)→ 超過就落 TEMP
     呼叫端自己給的 config / 之後自己 SET 的一律優先(那 9 支有設的照舊)
  ③ 開關:VIA_DUCK_TEMP=0 整個不掛(回原生 duckdb)
輕框管理(TEMP 只是工作區、不是資料):
  · DuckDB 關連線時自己清它的暫存檔;本支只清「行程已死 · 還留東西」的 p<pid> 夾,留最近 5 個(VIA_TEMP_KEEP)
  · 每刪一筆追加 purge_ledger.jsonl(L107 ④);三不刪:VIA_Reports · registry · 任何冊 / 帳 / 正本樹
  · TEMP 根預設 %LOCALAPPDATA%\Temp\VIA_progress(本機 SSD · 不在 OneDrive · 不進 git;同 SUP_MDL867)

用法(都經 VCGC:via-vcgc run CGC_MDL262_DuckTempHook …):
  status [--json]              各境:duckdb 版 · 鉤在不在 · 活體量 temp_directory / memory_limit · TEMP 根用量 · 引擎採用率
  install [--env 名 …] [--apply]  代裝鉤(預設乾跑;只裝有 duckdb 的境)· 帳 install_ledger.jsonl
  uninstall --env 名 [--apply]  拔鉤(可逆)
  purge [--apply]              輕框清理(乾跑先列)
  --selftest
境根:VIA_ENVS_ROOT(分號 / 冒號隔)→ /root/envs · ~/envs · ~/anaconda3/envs · ~/miniconda3/envs(有的都掃)。
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
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ENGINE = Path(__file__).stem
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
HOOK_NAME = "via_duck_temp"
FORBIDDEN = ("VIA_Reports", "supportive modules", "functional modules", ".git", "registry")   # 三不刪

# ---- 裝進各境 site-packages 的鉤(單檔 · 全包 try · 不預先 import duckdb) ----
HOOK_SRC = r'''# via_duck_temp — CGC_MDL262_DuckTempHook 代裝(L107 TEMP 為主 · 記憶體為輔);VIA_DUCK_TEMP=0 關。不要手改:重裝會蓋。
import os, sys
HOOK_VERSION = "v0100"


def _temp_dir():
    base = os.environ.get("VIA_DUCKDB_TEMP_DIR")
    if not base:
        root = os.environ.get("VIA_TEMP_ROOT")
        if not root:
            import tempfile
            root = os.path.join(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir(), "Temp", "VIA_progress")
        base = os.path.join(root, "duckdb")
    return os.path.join(base, "p%d" % os.getpid())


def _phys_bytes():
    try:
        if os.name == "nt":
            import ctypes

            class _M(ctypes.Structure):
                _fields_ = [("l", ctypes.c_ulong), ("m", ctypes.c_ulong), ("t", ctypes.c_ulonglong), ("a", ctypes.c_ulonglong),
                            ("tp", ctypes.c_ulonglong), ("ap", ctypes.c_ulonglong), ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong),
                            ("ae", ctypes.c_ulonglong)]
            m = _M(); m.l = ctypes.sizeof(_M)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return int(m.t)
        return int(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))
    except Exception:
        return 0


def _mem_limit():
    v = os.environ.get("VIA_DUCKDB_MEM")
    if v:
        return v
    try:
        pct = float(os.environ.get("VIA_DUCKDB_MEM_PCT") or 50)
    except Exception:
        pct = 50.0
    b = _phys_bytes()
    return ("%dMB" % max(256, int(b * pct / 100 / 1048576))) if b else None


def defaults():
    d = {}
    t = _temp_dir()
    try:
        os.makedirs(os.path.dirname(t), exist_ok=True)   # DuckDB 只建最末層;上層建不了就不設(回原生行為,不弄壞連線)
        d["temp_directory"] = t
    except Exception:
        pass
    m = _mem_limit()
    if m:
        d["memory_limit"] = m
    return d


def patch(mod):
    if getattr(mod, "_via_duck_temp", None):
        return mod
    orig = mod.connect

    def connect(*args, **kw):
        try:
            a = list(args)
            cfg = a[2] if len(a) >= 3 else kw.get("config")
            cfg = dict(cfg or {})
            for k, v in defaults().items():
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
    mod._via_duck_temp = HOOK_VERSION
    return mod


class _Finder:
    """duckdb 被 import 時才掛;找到真 spec 後包 exec_module。"""

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
                patch(module)
            except Exception:
                pass
        spec.loader.exec_module = exec_module
        return spec


def install():
    if os.environ.get("VIA_DUCK_TEMP", "1") == "0":
        return
    if "duckdb" in sys.modules:
        patch(sys.modules["duckdb"])
    elif not any(isinstance(f, _Finder) for f in sys.meta_path):
        sys.meta_path.insert(0, _Finder())


try:
    install()
except Exception:
    pass
'''
PTH_SRC = "import via_duck_temp\n"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def hook_sha() -> str:
    return hashlib.sha256(HOOK_SRC.encode("utf-8")).hexdigest()[:16]


def temp_root() -> Path:
    r = os.environ.get("VIA_TEMP_ROOT")
    if not r:
        r = str(Path(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()) / "Temp" / "VIA_progress")
    return Path(r)


def duck_temp_base() -> Path:
    return Path(os.environ.get("VIA_DUCKDB_TEMP_DIR") or (temp_root() / "duckdb"))


def env_roots() -> list[Path]:
    raw = os.environ.get("VIA_ENVS_ROOT")
    cands = [Path(p) for p in re.split(r"[;" + (":" if os.name != "nt" else "") + r"]", raw) if p] if raw else []
    home = Path.home()
    cands += [Path("/root/envs"), home / "envs", home / "anaconda3" / "envs", home / "miniconda3" / "envs"]
    out, seen = [], set()
    for c in cands:
        try:
            k = str(c.resolve())
        except Exception:
            continue
        if c.is_dir() and k not in seen:
            seen.add(k); out.append(c)
    return out


def env_python(env: Path) -> Path | None:
    for rel in ("bin/python", "python.exe", "Scripts/python.exe"):
        p = env / rel
        if p.exists():
            return p
    return None


def list_envs(names: list[str] | None = None) -> list[Path]:
    out = []
    for root in env_roots():
        for e in sorted(root.iterdir()):
            if e.is_dir() and env_python(e) and (not names or e.name in names):
                out.append(e)
    return out


PROBE = (
    "import json,sys,sysconfig\n"
    "r={'purelib':sysconfig.get_paths()['purelib'],'py':sys.version.split()[0],'hooked':None}\n"
    "try:\n"
    "    import duckdb\n"
    "    r['duckdb']=duckdb.__version__; r['hooked']=getattr(duckdb,'_via_duck_temp',None)\n"
    "    c=duckdb.connect(); r['temp_directory'],r['memory_limit']=c.execute(\"select current_setting('temp_directory'),current_setting('memory_limit')\").fetchone(); c.close()\n"
    "except Exception as e:\n"
    "    r['duckdb']=None; r['err']=type(e).__name__\n"
    "print(json.dumps(r))\n"
)


def probe(py: Path, extra_env: dict | None = None) -> dict:
    env = dict(os.environ, **(extra_env or {}))
    try:
        p = subprocess.run([str(py), "-c", PROBE], capture_output=True, text=True, timeout=120, env=env)
        return json.loads(p.stdout.strip().splitlines()[-1])
    except Exception as e:
        return {"duckdb": None, "err": f"{type(e).__name__}: {str(e)[:120]}"}


def hook_state(purelib: str) -> str:
    f = Path(purelib) / (HOOK_NAME + ".py")
    if not f.exists():
        return "ABSENT"
    return "OK" if hashlib.sha256(f.read_bytes()).hexdigest()[:16] == hook_sha() else "STALE"


def _ledger(name: str, row: dict) -> None:
    try:
        d = VIA / "VIA_Reports" / "vcgc" / "duck_temp"
        d.mkdir(parents=True, exist_ok=True)
        with open(d / name, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as e:  # 帳寫不進去照實報,不擋動作
        print(f"  [帳] {name} 寫不進:{type(e).__name__}")


def write_hook(purelib: Path) -> None:
    purelib.mkdir(parents=True, exist_ok=True)
    (purelib / (HOOK_NAME + ".py")).write_text(HOOK_SRC, encoding="utf-8")
    (purelib / (HOOK_NAME + ".pth")).write_text(PTH_SRC, encoding="utf-8")


def remove_hook(purelib: Path) -> list[str]:
    gone = []
    for n in (HOOK_NAME + ".py", HOOK_NAME + ".pth"):
        f = purelib / n
        if f.exists():
            f.unlink(); gone.append(n)
    return gone


# ---- 引擎採用率(唯讀掃尾版;給子系統的資訊,不改它們) ----
FAMILY_DIRS = {"VCGC": ["supportive modules/registry"], "VDF": ["functional modules/VDF"],
               "VRN": ["functional modules/VRN"], "SUP": ["supportive modules"]}
SKIP = ("/references/", "/intake/", "/archive", "/frozen", "/_legacy")


def _tails(files: list[Path]) -> list[Path]:
    best: dict[str, Path] = {}
    for f in files:
        m = re.match(r"(.+)_v(\d{4})$", f.stem)
        k = str(f.parent / (m.group(1) if m else f.stem))
        if k not in best or f.name > best[k].name:
            best[k] = f
    return list(best.values())


def adoption() -> dict:
    out = {}
    for fam, dirs in FAMILY_DIRS.items():
        files = []
        for d in dirs:
            base = VIA / d
            it = base.glob("*.py") if fam == "SUP" else base.rglob("*.py")
            files += [f for f in it if not any(s in f.as_posix() for s in SKIP)]
        n = t = m = 0
        for f in _tails(files):
            try:
                s = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            if "duckdb.connect" not in s:
                continue
            n += 1; t += "temp_directory" in s; m += "memory_limit" in s
        out[fam] = {"connect_tails": n, "explicit_temp": t, "explicit_mem": m}
    return out


def du(p: Path) -> tuple[int, int]:
    n = b = 0
    if p.exists():
        for f in p.rglob("*"):
            if f.is_file():
                n += 1
                try:
                    b += f.stat().st_size
                except OSError:
                    pass
    return n, b


def _alive(pid: int) -> bool:
    if pid == os.getpid():
        return True
    try:
        if os.name == "nt":
            out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True, timeout=20).stdout
            return str(pid) in out
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except Exception:
        return False


def purge_plan(base: Path | None = None, keep: int | None = None) -> list[Path]:
    base = base or duck_temp_base()
    keep = keep if keep is not None else int(os.environ.get("VIA_TEMP_KEEP") or 5)
    if not base.exists():
        return []
    dead = []
    for d in base.iterdir():
        m = re.fullmatch(r"p(\d+)", d.name)
        if d.is_dir() and m and not _alive(int(m.group(1))):
            dead.append(d)
    dead.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    return [d for d in dead[keep:] if not any(s in d.as_posix() for s in FORBIDDEN)] + \
           [d for d in dead[:keep] if not any(d.iterdir())]          # 空夾不算一輪,直接清


def purge(apply: bool, base: Path | None = None, keep: int | None = None) -> list[Path]:
    plan = purge_plan(base, keep)
    for d in plan:
        n, b = du(d)
        print(f"  {'清' if apply else '會清'} {d}  ({n} 檔 · {b / 1048576:.1f} MB)")
        if apply:
            shutil.rmtree(d, ignore_errors=True)
            try:
                with open((base or duck_temp_base()) / "purge_ledger.jsonl", "a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"ts": _now(), "tool": ENGINE, "path": str(d), "files": n, "bytes": b}) + "\n")
            except Exception:
                pass
    if not plan:
        print("  沒有要清的(DuckDB 關連線會自清;只清死行程留下的 p<pid> 夾)")
    return plan


def cmd_status(as_json: bool) -> int:
    rows = []
    for e in list_envs():
        r = probe(env_python(e))
        r["env"] = e.name
        r["hook"] = hook_state(r["purelib"]) if r.get("purelib") else "?"
        rows.append(r)
    ado = adoption()
    tb = du(duck_temp_base())
    res = {"engine": ENGINE, "ts": _now(), "hook_sha": hook_sha(), "temp_root": str(temp_root()),
           "duck_temp_base": str(duck_temp_base()), "duck_temp_files": tb[0], "duck_temp_mb": round(tb[1] / 1048576, 1),
           "envs": rows, "adoption": ado}
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=1)); return 0
    print(f"[{ENGINE}] TEMP 根 {res['temp_root']} · duckdb 夾 {res['duck_temp_base']}({tb[0]} 檔 · {res['duck_temp_mb']} MB)")
    print(f"  {'境':<20}{'py':<9}{'duckdb':<9}{'鉤':<8}{'temp_directory(活體)':<52}memory_limit")
    for r in rows:
        if r.get("duckdb") is None:
            print(f"  {r['env']:<20}{r.get('py', '?'):<9}{'—':<9}{r['hook']:<8}(沒有 duckdb,不用裝)"); continue
        print(f"  {r['env']:<20}{r['py']:<9}{r['duckdb']:<9}{r['hook']:<8}{str(r.get('temp_directory'))[-50:]:<52}{r.get('memory_limit')}")
    have = [r for r in rows if r.get("duckdb")]
    ok = [r for r in have if r["hook"] == "OK" and r.get("hooked")]
    print(f"  境覆蓋:{len(ok)}/{len(have)} 個有 duckdb 的境已掛鉤")
    for fam, a in ado.items():
        print(f"  引擎 {fam:<5} 開 duckdb 的尾版 {a['connect_tails']:>3} · 自己設 temp_directory {a['explicit_temp']:>2} · memory_limit {a['explicit_mem']:>2}"
              f" → 其餘 {a['connect_tails'] - a['explicit_temp']} 支由鉤補(呼叫端有給的照舊)")
    print(f"[計] {ENGINE} 境覆蓋 {len(ok)}/{len(have)} · {'GREEN' if have and len(ok) == len(have) else 'YELLOW'}")
    return 0


def cmd_install(names: list[str], apply: bool, remove: bool = False) -> int:
    envs = list_envs(names or None)
    if names and len(envs) != len(set(names)):
        print(f"  找不到境:{sorted(set(names) - {e.name for e in envs})}"); return 2
    rc = 0
    for e in envs:
        r = probe(env_python(e))
        if not r.get("purelib"):
            print(f"  {e.name}: 探不到 site-packages({r.get('err')})"); rc = 1; continue
        if r.get("duckdb") is None and not remove:
            print(f"  {e.name}: 沒有 duckdb → 不裝"); continue
        pl = Path(r["purelib"]); st = hook_state(r["purelib"])
        if remove:
            print(f"  {e.name}: {'拔' if apply else '會拔'} 鉤({st})")
            if apply:
                gone = remove_hook(pl); _ledger("install_ledger.jsonl", {"ts": _now(), "op": "uninstall", "env": e.name, "removed": gone})
            continue
        if st == "OK":
            print(f"  {e.name}: 鉤已在且一致(sha {hook_sha()})"); continue
        print(f"  {e.name}: {'裝' if apply else '會裝'} 鉤 → {pl}({st} → OK)")
        if apply:
            write_hook(pl)
            after = probe(env_python(e))
            good = after.get("hooked") == "v0100" and "duckdb" in str(after.get("temp_directory", ""))
            print(f"    實測:hooked={after.get('hooked')} · temp_directory={after.get('temp_directory')} · memory_limit={after.get('memory_limit')} → {'OK' if good else 'FAIL'}")
            _ledger("install_ledger.jsonl", {"ts": _now(), "op": "install", "env": e.name, "purelib": str(pl), "sha": hook_sha(),
                                             "verified": good, "temp_directory": after.get("temp_directory"), "memory_limit": after.get("memory_limit")})
            rc = rc or (0 if good else 1)
    if not apply:
        print("  (乾跑;加 --apply 才寫)")
    return rc


def selftest() -> int:
    res = []

    def chk(name, cond, note=""):
        res.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""))

    try:
        import duckdb  # noqa: F401
        have_duck = True
    except Exception:
        have_duck = False
    chk("① 本機 python 有 duckdb(自測要它)", have_duck)
    with tempfile.TemporaryDirectory(prefix="mdl262_") as td:
        site_dir = Path(td) / "site"; troot = Path(td) / "temproot"
        write_hook(site_dir)
        boot = f"import site; site.addsitedir({str(site_dir)!r})\n"
        env = dict(os.environ, VIA_TEMP_ROOT=str(troot), VIA_DUCKDB_MEM="300MB")
        env.pop("VIA_DUCKDB_TEMP_DIR", None); env.pop("VIA_DUCK_TEMP", None)

        def run(code, extra=None):
            e = dict(env, **(extra or {}))
            p = subprocess.run([sys.executable, "-c", boot + code], capture_output=True, text=True, timeout=300, env=e)
            return p.returncode, (p.stdout.strip().splitlines() or [""])[-1], p.stderr[-300:]

        rc, out, err = run("import sys; print('duckdb' in sys.modules)")
        chk("② 不預先 import duckdb(沒用的行程零成本)", rc == 0 and out == "False", out + err)
        rc, out, err = run("import duckdb,os,json; c=duckdb.connect(); print(json.dumps([duckdb._via_duck_temp, os.getpid()]+list(c.execute(\"select current_setting('temp_directory'),current_setting('memory_limit')\").fetchone())))")
        try:
            hv, pid, tdir, mem = json.loads(out)
        except Exception:
            hv = pid = tdir = mem = None
        chk("③ import 時掛上 · temp_directory = VIA_TEMP_ROOT/duckdb/p<pid>", rc == 0 and hv == "v0100"
            and Path(str(tdir)) == troot / "duckdb" / f"p{pid}", out + err)
        chk("④ memory_limit 走 VIA_DUCKDB_MEM(300MB)", rc == 0 and mem and mem.replace(" ", "").upper().startswith(("286", "300")), mem)
        rc, out, err = run("import duckdb; c=duckdb.connect(':memory:', False, {'temp_directory': '/tmp/x_mine', 'memory_limit': '1GB'}); "
                           "print(c.execute(\"select current_setting('temp_directory')||'|'||current_setting('memory_limit')\").fetchone()[0])")
        chk("⑤ 呼叫端自己給的 config 優先(位置引數也行)", rc == 0 and out.startswith("/tmp/x_mine|")
            and any(t in out.replace(" ", "") for t in ("953.6MiB", "1.0GiB", "1GB", "1000.0MB")), out + err)
        rc, out, err = run("import duckdb; print(getattr(duckdb,'_via_duck_temp',None))", {"VIA_DUCK_TEMP": "0"})
        chk("⑥ VIA_DUCK_TEMP=0 不掛(原生 duckdb)", rc == 0 and out == "None", out + err)
        spill = ("import duckdb,os,glob,json; c=duckdb.connect(config={'memory_limit':'64MB','threads':1,'preserve_insertion_order':False}); "
                 "td=c.execute(\"select current_setting('temp_directory')\").fetchone()[0]; "
                 "n=c.execute('select count(*), sum(x) from (select * from range(4000000) t(x) order by hash(x))').fetchone(); "
                 "c.close(); print(json.dumps([n[0], int(n[1]), td, os.path.isdir(td) and len(os.listdir(td))]))")
        rc, out, err = run(spill)
        try:
            cnt, sm, tdir2, left = json.loads(out)
        except Exception:
            cnt = sm = tdir2 = left = None
        chk("⑦ 64MB 上限做 400 萬列排序照算對(落 TEMP 不爆記憶體)", rc == 0 and cnt == 4000000 and sm == 4000000 * 3999999 // 2, out + err)
        chk("⑧ 關連線後暫存檔清乾淨(輕框:DuckDB 自清)", rc == 0 and left in (False, 0), left)
        base = troot / "duckdb"; base.mkdir(parents=True, exist_ok=True)
        deadpids = [p for p in range(4000000, 4000000 + 8)]
        for i, p in enumerate(deadpids):
            d = base / f"p{p}"; d.mkdir(); (d / "x.tmp").write_bytes(b"0" * 10)
            os.utime(d, (time.time() - 100 + i, time.time() - 100 + i))
        (base / f"p{os.getpid()}").mkdir()
        (base / "keepme").mkdir()
        plan = purge_plan(base, keep=5)
        chk("⑨ 輕框:只清死行程的 p<pid> 夾 · 留最近 5 · 活行程與別的夾不碰",
            sorted(p.name for p in plan) == [f"p{p}" for p in deadpids[:3]], [p.name for p in plan])
        buf_rc = purge(True, base, keep=5)
        chk("⑩ purge --apply 寫 purge_ledger.jsonl", (base / "purge_ledger.jsonl").exists() and len(buf_rc) == 3
            and (base / f"p{os.getpid()}").exists() and (base / "keepme").exists())
    ado = adoption()
    chk("⑪ 採用率掃得到四族(唯讀)", set(ado) == {"VCGC", "VDF", "VRN", "SUP"} and sum(a["connect_tails"] for a in ado.values()) > 0, ado)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑫ L103 PY 加速器橋在(__future__ 之後)",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and src.index("from __future__") < src.index("[VIA:ACCEL-BRIDGE:v0100]"))
    ok = sum(res)
    print(f"[計] {ENGINE} 自測 {ok}/{len(res)} · {'PASS' if ok == len(res) else 'FAIL'}")
    return 0 if ok == len(res) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[0] in ("-h", "--help", "help"):
        print(__doc__); return 0
    if a == ["--selftest"]:
        return selftest()
    verb, rest = a[0], a[1:]
    apply = "--apply" in rest
    names = [rest[i + 1] for i, x in enumerate(rest) if x == "--env" and i + 1 < len(rest)]
    if verb == "status":
        return cmd_status("--json" in rest)
    if verb == "install":
        return cmd_install(names, apply)
    if verb == "uninstall":
        if not names:
            print("  uninstall 要 --env 名"); return 2
        return cmd_install(names, apply, remove=True)
    if verb == "purge":
        purge(apply); return 0
    print(f"  不認得的動詞:{verb}(status · install · uninstall · purge · --selftest)"); return 2


if __name__ == "__main__":
    raise SystemExit(main())
