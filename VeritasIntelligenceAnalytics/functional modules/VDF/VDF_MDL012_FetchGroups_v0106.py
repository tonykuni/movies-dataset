#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL012_FetchGroups v0106 — 薄尾:find_db 家優先(--home / VIA_VDF_DB_HOME 的庫先於倉內 output_hub)

實測(2026-10-15 VDF 獨立實測):v0105 --selftest 在有倉內 output_hub 庫的機器上崩潰(KeyError 'lag_days')。
  根因  v0100 find_db 把所有根(家 → 倉內 output_hub)的命中混在一起,只按「在 output_hub 夾內 · 檔案大小」排序;
        倉內舊庫(15 MB)比家裡的新庫大 → monitor 讀到倉內舊庫,表不在 → NODATA(自測沙盒家被蓋過)。
        正式路徑同病:操作員用 --home 指新家,族群監控卻讀倉內舊庫(v0151 db check 文件明定 家:--home > env > 倉內)。
  修法  根的順序就是優先序:第一個有命中的根勝;同一根內才比「在 output_hub 夾內 · 大小」(與 v0100 同式)。
        換到前版鏈上每一個自己定義 find_db 的模組(monitor 讀的是那個模組的全域),不改前版檔。
其餘動詞全照 v0105 / v0104 / … / v0100。不抓網、不代設同意閘、不碰 TA-Lib。VDF 自己的模組,不載入他系統程式。
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
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _prior_path() -> Path:
    """前版 = 同家族比本檔小的最大版號(不釘名,避免 PINVER)。"""
    me = int(Path(__file__).stem.rsplit("_v", 1)[1])
    hits = [p for p in HERE.glob("VDF_MDL012_FetchGroups_v*.py") if re.search(r"_v\d+$", p.stem) and int(p.stem.rsplit("_v", 1)[1]) < me]
    return max(hits, key=lambda p: int(p.stem.rsplit("_v", 1)[1]))


PRIOR_PATH = _prior_path()
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0106", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


def _chain() -> list:
    mods, m = [], PRIOR
    while m is not None and m not in mods:
        mods.append(m)
        m = vars(m).get("PRIOR")
    return mods


TAG = f"VDF_MDL012_FetchGroups v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


_SEAL_REPO_HUB = False          # 只在本版自測跑前版鏈期間為 True:倉內 output_hub 不當根(自測不碰真庫)
REPO_HUB = HERE / "output_hub"


def find_db(name: str, roots: list) -> Path | None:
    """根的順序 = 優先序(家 → 倉內);第一個有命中的根勝,同根內照 v0100 同式(output_hub 夾內優先 · 大檔優先)。"""
    for root in roots:
        root = Path(root)
        if _SEAL_REPO_HUB and root.resolve() == REPO_HUB.resolve():
            continue
        if not root.is_dir():
            continue
        hits = [p for p in root.rglob(name)
                if p.is_file() and "_quarantine" not in str(p) and "selftest" not in p.name]
        if hits:
            hits.sort(key=lambda p: ("output_hub" not in p.parts, -p.stat().st_size))
            return hits[0]
    return None


_FIND_DB_OLD = {}
for _m in _chain():
    _m.TAG = TAG
    fn = vars(_m).get("find_db")
    if callable(fn) and getattr(fn, "__module__", None) == _m.__name__:
        _FIND_DB_OLD[_m.__name__] = fn
        _m.find_db = find_db

for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


def selftest() -> int:
    global _SEAL_REPO_HUB
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 薄尾自測(find_db 家優先)===")
    with tempfile.TemporaryDirectory(prefix="mdl012_v0106_") as td:
        t = Path(td)
        home, repo = t / "home", t / "repo"
        (home / "output_hub" / "mega").mkdir(parents=True)
        (repo / "output_hub" / "mega").mkdir(parents=True)
        (home / "output_hub" / "mega" / "x.duckdb").write_bytes(b"s" * 10)
        (repo / "output_hub" / "mega" / "x.duckdb").write_bytes(b"b" * 5000)
        chk("① 家的小庫勝過倉內大庫(根序 = 優先序;v0100 會挑倉內大庫)",
            find_db("x.duckdb", [home, repo]) == home / "output_hub" / "mega" / "x.duckdb")
        old = next(iter(_FIND_DB_OLD.values()), None)
        chk("② 對照:前版同輸入挑倉內大庫(重現根因)", old is not None
            and old("x.duckdb", [home, repo]) == repo / "output_hub" / "mega" / "x.duckdb")
        (home / "loose").mkdir()
        (home / "loose" / "y.duckdb").write_bytes(b"z" * 9000)
        (home / "output_hub" / "y.duckdb").write_bytes(b"z" * 10)
        (repo / "output_hub" / "_quarantine").mkdir()
        (repo / "output_hub" / "_quarantine" / "q.duckdb").write_bytes(b"q")
        chk("③ 同一根內照舊:output_hub 夾內優先於大檔;_quarantine 不收;家沒有才退倉內",
            find_db("y.duckdb", [home, repo]) == home / "output_hub" / "y.duckdb"
            and find_db("q.duckdb", [home, repo]) is None
            and find_db("x.duckdb", [t / "none", repo]) == repo / "output_hub" / "mega" / "x.duckdb")
        _SEAL_REPO_HUB = True
        try:
            sealed = find_db("vdf_tw_market.duckdb", [t / "none", REPO_HUB])
        finally:
            _SEAL_REPO_HUB = False
        chk("⑥ 封倉:自測期間倉內 output_hub 不當根(真庫不被自測摸到);封完復原", sealed is None and not _SEAL_REPO_HUB)
    owners = [m for m in _chain() if m.__name__ in _FIND_DB_OLD]
    chk("④ 前版鏈上定義 find_db 的模組全換成本版(monitor 讀模組全域)",
        owners and all(vars(m)["find_db"] is find_db for m in owners), [m.__name__ for m in owners])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 加速器橋 · 網路橋在;前版不動(薄尾);不碰 TA-Lib · 不寫同意閘",
        "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src and PRIOR_PATH.is_file()
        and ("import " + "talib") not in src and not re.search("CONSENT" + r"['\"]\]\s*=", src))
    good = all(ok)
    print(f"  [計] {TAG} 薄尾 {sum(ok)}/{len(ok)} · {'PASS' if good else 'FAIL'}")
    if not good:
        return 1
    _SEAL_REPO_HUB = True                   # 前版鏈自測的 monitor / optimize --apply 只碰沙盒,不碰倉內真庫
    try:
        rc = PRIOR.selftest()
    finally:
        _SEAL_REPO_HUB = False
    if rc != 0:
        print(f"  [黃] {TAG} 本版 {len(ok)}/{len(ok)} 過 · 前版鏈自測 rc {rc}(照實回 2,不算綠)")
    return 0 if rc == 0 else 2


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
