#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_MDL008_FetchSystem v0113 — 薄尾(v0100–v0112 一字不動):沒指定擷取家時,寫進資料家(不再落倉內暫存)

同 VDF_MDL012_FetchGroups v0113 的病(桌機 2026-11-26 lakeall 實錄:每支引擎「output_hub 歸位 → 倉內 VIA_Reports\vdf_fetch\dict」,
資料家 via_database\vdf_database 的庫沒讀到 → 從 2018 整段重抓、兩份庫)。
v0100 home_dir = --home > env VIA_VDF_FETCH_HOME > 倉內 VIA_Reports/vdf_fetch/dict。
本版只換 home_dir:--home > env VIA_VDF_FETCH_HOME > 資料家擷取根(env VIA_VDF_DB_HOME > 資料家冊 fetch_home · db_home;
底下要有 output_hub)> 倉內暫存(前版)。其餘動詞照 v0112(--home 先轉絕對路徑也照舊)。
新動詞 home(唯讀)。零網路自測(暫存夾);不設同意閘;不用 TA-Lib。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


def _load_prior(stem: str):
    path = max((p for p in HERE.glob(stem + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
    spec = importlib.util.spec_from_file_location(stem + "_prior_for_" + Path(__file__).stem, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _body(stem: str, attr: str):
    """前版鏈裡定義 attr 的本體模組(v0100;依檔名找,已由前版鏈載入)。"""
    for m in list(sys.modules.values()):
        f = str(getattr(m, "__file__", "") or "")
        if Path(f).name == stem + "_v0100.py" and callable(vars(m).get(attr)):
            return m
    return None


def datahome_fetch_root(env=None, book_dir: Path = HERE) -> tuple:
    """資料家的擷取根(底下有 output_hub 的那一層):env VIA_VDF_DB_HOME > VDF_DataHome_SSOT 尾版冊的 fetch_home · db_home(依序,
    這台機器存在的第一個);給的路徑本身沒有 output_hub、但底下 vdf_database 有 → 用 vdf_database。→ (Path | None, 為什麼)"""
    env = os.environ if env is None else env
    cands = []
    if env.get("VIA_VDF_DB_HOME"):
        cands.append((Path(env["VIA_VDF_DB_HOME"]), "env VIA_VDF_DB_HOME"))
    books = sorted(Path(book_dir).glob("VDF_DataHome_SSOT_v*.json"), key=_vnum)
    if books:
        try:
            for h in json.loads(books[-1].read_text(encoding="utf-8")).get("homes") or []:
                for k in ("fetch_home", "db_home"):
                    if h.get(k):
                        cands.append((Path(h[k]), f"{books[-1].name} · {h.get('id')} · {k}"))
        except (OSError, ValueError):
            pass
    for p, why in cands:
        for q in (p, p / "vdf_database"):
            try:
                if (q / "output_hub").is_dir():
                    return q, why
            except OSError:
                continue
    return None, "沒有資料家(env VIA_VDF_DB_HOME 與資料家冊上的家,這台機器都沒有 output_hub)"


_STEM = "VDF_MDL008_FetchSystem"
TAG = f"{_STEM} v0113"
PRIOR = _load_prior(_STEM)
BODY = _body(_STEM, "home_dir")
_ORIG_HOME_DIR = BODY.home_dir if BODY is not None else None


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def resolve_home(arg=None, env=None, book_dir: Path = HERE) -> tuple:
    env = os.environ if env is None else env
    if arg:
        return Path(arg), "--home"
    if env.get("VIA_VDF_FETCH_HOME"):
        return Path(env["VIA_VDF_FETCH_HOME"]), "env VIA_VDF_FETCH_HOME"
    root, why = datahome_fetch_root(env, book_dir)
    if root is not None:
        return root, "資料家 · " + why
    return Path(BODY.DEFAULT_HOME), "倉內暫存 VIA_Reports/vdf_fetch/dict(" + why + ")"


def home_dir(arg=None) -> Path:
    return resolve_home(arg)[0]


if BODY is not None:
    BODY.home_dir = home_dir                         # v0100 main · v0101 / v0103 經 PRIOR / BASE.home_dir 取 → 本版接手


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    print(f"=== {TAG} · 薄尾自測(暫存夾;不讀本機資料家)===", flush=True)
    chk("① 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("② 網路工具橋在位(載入不出網)", VIA_NET_TOOL_PATH is not None)
    chk("③ 已換裝:本體 home_dir 指到本版", BODY is not None and BODY.home_dir is home_dir)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        home = td / "via_database" / "vdf_database"
        (home / "output_hub" / "mega").mkdir(parents=True)
        bookdir = td / "books"
        bookdir.mkdir()
        (bookdir / "VDF_DataHome_SSOT_v0101.json").write_text(json.dumps({"homes": [{"id": "ws", "db_home": str(home)}]}), encoding="utf-8")
        r = [resolve_home("x", {}, bookdir), resolve_home(None, {"VIA_VDF_FETCH_HOME": str(td / "f")}, bookdir),
             resolve_home(None, {}, bookdir), resolve_home(None, {"VIA_VDF_DB_HOME": str(td / "via_database")}, td / "nobook"),
             resolve_home(None, {}, td / "nobook")]
        chk("④ 順序:--home > env FETCH_HOME > 資料家冊 > env DB_HOME(via_database 一層也找得到 vdf_database)> 倉內暫存",
            [x[0] for x in r] == [Path("x"), td / "f", home, home, Path(BODY.DEFAULT_HOME)] and "倉內暫存" in r[4][1], r)
    import contextlib
    import io
    import subprocess
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            rc = PRIOR.selftest()
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"  [註] 前版鏈自測丟例外:{type(exc).__name__}: {str(exc)[:120]}", flush=True)
    alone = subprocess.run([sys.executable, str(PRIOR.__file__), "--selftest"], capture_output=True, text=True, timeout=900).returncode
    chk("⑤ 前版鏈自測在本版下的結果 = 單獨跑 v0112 的結果(本版不讓前版變壞)", (rc == 0) == (alone == 0), (rc, alone))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 檔面:第 3 行加速器標記 · 雙橋 · glob 取前版 · 零 TA-Lib · 不設同意閘",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "[VIA:NET-BRIDGE:v0100]" in src and "HERE.glob(stem" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    print(f"[selftest] {TAG} {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}" + ("" if rc == 0 else " · 前版鏈自測本來就不綠(範圍外,照實回黃)"),
          flush=True)
    if not all(ok):
        return 1
    return 0 if rc == 0 else 2


def main() -> int:
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        return selftest()
    if a[:1] == ["home"]:
        p, why = resolve_home(None)
        print(f"[{TAG}] 擷取家 {p} · 來源 {why} · output_hub {'在' if (p / 'output_hub').is_dir() else '不在'}")
        return 0 if why.startswith(("資料家", "env")) else 2
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
