#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""
VDF_ENG060_AdjPriceLayer v0109 — 調整後價格標準層引擎(薄尾:自測只在暫存夾造雙庫,不看本機有沒有正式庫)

v0108 → v0109(2026-11-19 容器實測紅):
  壞在哪:`VIA_FROM_VCGC=YES python3 VDF_ENG060_AdjPriceLayer_v0108.py --selftest` 串到 v0107 的自測後倒在
      File ".../VDF_ENG060_AdjPriceLayer_v0107.py", line 255, in selftest
          f"全 {r['gl']['adj_rows']:,})")
      KeyError: 'gl'
  根因:v0107 的自測讀的是**這台機器的正式庫**。它只看台股庫(v0107:236 `_missing_tables(DB_TW, …)`)決定要不要走有料路,
      build()(v0107:143)只有全球庫 `vdf_global_market.duckdb` 在才放進 'gl';而 ① 的說明字串(v0107:254-255)在
      `"gl" in r` 那道判斷之前就無條件取 r['gl'] → 有台股庫、沒有全球庫的機器(本容器:output_hub/mega 只有
      vdf_tw_market.duckdb)自測直接丟 KeyError,連 FAIL 都報不出來。兩本都在或兩本都不在的機器才過 ——
      自測結果取決於本機剛好有什麼資料,這本身就是錯的。
  本版改什麼(只改自測;build / status / main / guard 一字不動,照 v0108 → v0107):
      · 自測在 tempfile 暫存夾自己造一套台股 + 全球的合成原始庫,把 v0107 模組全域的 DB_TW / DB_GL 暫換成那兩本,
        再串前一版(v0108:FRAME 守門 + v0107 九檢)整套自測;跑完把路徑換回原值。
      · 正式庫(DB_TW / DB_GL 原路徑)前後比 在不在 · 大小 · mtime,一樣才算過;不開、不建、不改。
      · 反證:同一套前版自測對「只有台股庫」的暫存湖照原樣跑,要重現 KeyError 'gl';本版在模組路徑正指著那種
        湖時照樣全綠(本版不看當下指的是哪裡)。
      · 缺料路:暫存路徑不在 → 前版回 2(NODATA),不炸。
  v0108 / v0107 及更早各版未改一個位元組(已發布檔凍結)。零網路 · 不安裝 · 不用 TA-Lib · 不設任何同意閘。
用法:python3 VDF_ENG060_AdjPriceLayer_v0109.py [build | --status | --selftest](非 --selftest 一律交 v0108 的 main())
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

import contextlib
import importlib.util
import io
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG060_AdjPriceLayer"
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


def _holder():
    """沿 PRIOR 鏈往下找,回**真正擁有** DB_TW / DB_GL 全域的那一版模組(現為 v0107;它的函式讀的是自己的全域)。"""
    m = PRIOR
    while m is not None:
        if "DB_TW" in vars(m) and "DB_GL" in vars(m) and callable(vars(m).get("build")):
            return m
        m = vars(m).get("PRIOR")
    raise RuntimeError("前版鏈裡找不到擁有 DB_TW / DB_GL 的模組")


def main() -> int:
    return PRIOR.main()


# ---------------------------------------------------------------- 自測(只在暫存夾)
_COLS = ("date VARCHAR, ticker VARCHAR, open DOUBLE, high DOUBLE, low DOUBLE, "
         "close DOUBLE, adj_close DOUBLE, volume DOUBLE")
# 合成列:每列 high ≥ max(open,close)、low ≤ min(open,close)(原始層零異常);兩支都有 factor ≠ 1 的調整日。
_TW_ROWS = [("2026-09-01", "2330.TW", 1000, 1010, 990, 1000, 980, 5000),
            ("2026-09-02", "2330.TW", 1002, 1015, 995, 1005, 990, 5200),
            ("2026-09-03", "2330.TW", 1006, 1020, 1000, 1010, 1010, 5100),
            ("2026-09-01", "1294.TWO", 100, 101, 99, 100, 98, 1000),
            ("2026-09-02", "1294.TWO", 100, 102, 98, 100, 100, 1000)]
_GL_ROWS = [("2026-09-01", "NVDA", 180, 183, 178, 182, 181.5, 9000),
            ("2026-09-02", "NVDA", 182, 186, 181, 185, 185, 9100)]


def _make_db(p: Path, table: str, rows) -> None:
    import duckdb
    con = duckdb.connect(str(p))
    try:
        con.execute(f"CREATE TABLE {table}({_COLS})")
        con.executemany(f"INSERT INTO {table} VALUES (?,?,?,?,?,?,?,?)", rows)
    finally:
        con.close()


@contextlib.contextmanager
def _lake(tw: Path, gl: Path):
    """把擁有者模組的 DB_TW / DB_GL 暫換成 tw / gl;離開一定換回原值。"""
    h = _holder()
    saved = (h.DB_TW, h.DB_GL)
    h.DB_TW, h.DB_GL = tw, gl
    try:
        yield h
    finally:
        h.DB_TW, h.DB_GL = saved


def _core() -> int:
    """本版自測核心:不管模組此刻指著哪本庫,自己在暫存夾造台股 + 全球雙庫,再串前一版整套自測。"""
    with tempfile.TemporaryDirectory(prefix="via_eng060_lake_") as td:
        tw, gl = Path(td) / "vdf_tw_market.duckdb", Path(td) / "vdf_global_market.duckdb"
        _make_db(tw, "tw_daily_prices", _TW_ROWS)
        _make_db(gl, "global_daily", _GL_ROWS)
        with _lake(tw, gl):
            return PRIOR.selftest()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    def snap(p: Path):
        return (p.stat().st_size, p.stat().st_mtime_ns) if p.is_file() else None

    print(f"=== {Path(__file__).stem} · 薄尾自測(雙庫只在暫存夾;正式庫零觸碰;再串 {PRIOR_PATH.stem} 全部檢)===")
    h = _holder()
    formal = (h.DB_TW, h.DB_GL)
    before = {str(p): snap(p) for p in formal}
    try:
        import duckdb  # noqa: F401
    except ImportError:
        chk("⓪ duckdb 在(本引擎與自測都靠它)", False, "duckdb 缺:誠實不過,不假綠")
        print(f"  [計] {_STEM} v{VERSION} 本版 {sum(ok)}/{len(ok)} · FAIL")
        return 1

    # ① 反證:前版(v0107 本體)自測對「只有台股庫」的暫存湖 → 原樣重現 KeyError 'gl'
    neg, neg_note = None, ""
    with tempfile.TemporaryDirectory(prefix="via_eng060_twonly_") as td:
        tw_only, gl_absent = Path(td) / "vdf_tw_market.duckdb", Path(td) / "vdf_global_market.duckdb"
        _make_db(tw_only, "tw_daily_prices", _TW_ROWS)
        buf = io.StringIO()
        with _lake(tw_only, gl_absent) as hh:
            try:
                with contextlib.redirect_stdout(buf):
                    hh.selftest()
                neg, neg_note = False, "前版沒丟例外(重現不出原故障)"
            except KeyError as e:
                neg, neg_note = (e.args == ("gl",)), f"KeyError {e.args!r}"
            except Exception as e:  # noqa: BLE001 — 反證只認 KeyError 'gl';別的例外照實點名
                neg, neg_note = False, f"{type(e).__name__}: {e}"
        chk(f"① 反證:{Path(h.__file__).stem} 前版自測對「只有台股庫」的暫存湖照原樣跑 → 重現 KeyError 'gl'"
            "(v0107:255 原故障)", neg, neg_note)

        # ② 本版在模組路徑正指著那個「只有台股庫」的湖(= 本容器的狀態)時照跑:自己造雙庫 → 前一版整套自測 rc 0
        with _lake(tw_only, gl_absent) as hh:
            rc2 = _core()
            still = (hh.DB_TW, hh.DB_GL) == (tw_only, gl_absent)
        chk("② 同一個「只有台股庫」狀態下本版自測照跑:暫存雙庫 → 前一版(FRAME 守門 + v0107 九檢)rc 0;跑完路徑換回原指向",
            rc2 == 0 and still, f"rc={rc2}")

    # ③ 從模組原本的正式路徑出發跑一次(實際上 --selftest 走的就是這條)
    rc3 = _core()
    chk("③ 從正式路徑出發:暫存雙庫 → 前一版整套自測 rc 0(九檢含 ① 雙庫調整層 · ③ 因子數學 · ⑥ 冪等 · ⑨ 因子具名)",
        rc3 == 0, f"rc={rc3}")

    # ④ 缺料路:暫存路徑不在 → 前版誠實 NODATA rc 2(不炸)
    with tempfile.TemporaryDirectory(prefix="via_eng060_empty_") as td:
        buf = io.StringIO()
        with _lake(Path(td) / "absent_tw.duckdb", Path(td) / "absent_gl.duckdb") as hh:
            with contextlib.redirect_stdout(buf):
                rc4 = hh.selftest()
        chk("④ 缺料路:暫存路徑庫不在 → 前版回 2(NODATA,誠實不炸)", rc4 == 2 and "[NODATA]" in buf.getvalue(), f"rc={rc4}")

    # ⑤ 正式庫零觸碰 + 路徑換回
    after = {str(p): snap(p) for p in formal}
    chk("⑤ 正式庫零觸碰:DB_TW / DB_GL 自測前後 在不在 · 大小 · mtime 完全一樣;模組全域換回正式路徑",
        after == before and (h.DB_TW, h.DB_GL) == formal,
        " · ".join(f"{Path(k).name}={'不在' if v is None else str(v[0]) + 'B'}" for k, v in before.items()))

    # ⑥ 本支帶橋、零網路、無 TA-Lib、無本機路徑
    body = Path(__file__).read_text(encoding="utf-8")
    lines = body.splitlines()
    chk("⑥ 本支第 3 行 ACCEL 標記 · 加速器橋 · 網路橋在;零網路(不 import 抓取套件)· 無 TA-Lib 匯入 · 無本機使用者路徑",
        len(lines) > 2 and lines[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]"
        and "[VIA:ACCEL-BRIDGE:v0100]" in body and "[VIA:NET-BRIDGE:v0100]" in body
        and not re.search(r"^\s*(?:import|from)\s+(?:requests|httpx|urllib)\b", body, re.M)
        and not re.search(r"^\s*(?:import|from)\s+" + "ta" + r"lib\b", body, re.M)
        and ("C:" + "\\Users") not in body and ("/home/" + "user") not in body,
        f"ACCEL={'載得到' if VIA_ACCEL is not None else '缺'} · NET={Path(VIA_NET_TOOL_PATH).name if VIA_NET_TOOL_PATH else '缺'}")

    print(f"  [計] {_STEM} v{VERSION} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv[1:] else main())
