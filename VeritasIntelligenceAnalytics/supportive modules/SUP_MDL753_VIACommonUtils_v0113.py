#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""
SUP_MDL753_VIACommonUtils v0113 — v0112 薄尾(v0112 一字不改):DuckDB 2.x 的「未讀完結果」相容。

操作員 2026-11-04 授權「可動 VDF VCGC 的系統指令並完成四系統收尾」。VCGC 主控台 `run VDF_SystemManager --selftest` 在 DuckDB 2.0 紅:
`upsert_rows` 先 `con.execute('SELECT count(*) …').fetchone()`,再 `con.register(...)` → DuckDB 2.x 拋
`ResourceInUseException: connection has an unfinished result from execute()`(1.x 允許;VDF 版本界線 duckdb>=1.1,<3 → 2.x 在界線內)。
v0112 自己的自測在 DuckDB 2.0 也紅 3 項(㊶ ㊷ ㊸ · 同一個原因)。

做法(只改連線包裝 · 不改 SQL · 不改語意):
  · `upsert_rows` 用的連線、`upsert_select` 收到的連線 → 包一層:`execute(...)` 回的結果 `fetchone()` 會把結果讀完(fetchall 取第一列),
    其餘方法(fetchall / df / register / close …)原樣轉交。DuckDB 1.x 結果相同,2.x 不再拋。
  · 尾版律:`VIA_LibCanon` 與 VRN 的 ENG073 / CodeRegistry 都用 `SUP_MDL753_VIACommonUtils_v*.py` 取最高版 → 自動接上本版。
自測:`python3 SUP_MDL753_VIACommonUtils_v0113.py --selftest`(零網路 · 只在 tempfile 沙盒寫)= v0112 全部自測(經本版包裝)+ 2.x 重現案例。
"""
from __future__ import annotations

import importlib.util as _ilu
import sys as _sys
from pathlib import Path as _Path

VERSION = "v0113"
PRIOR_NAME = "SUP_MDL753_VIACommonUtils_v0112.py"
_HERE = _Path(__file__).resolve().parent


def _load_prior():
    path = _HERE / PRIOR_NAME
    if not path.is_file():
        raise ImportError("[FAIL] 前版 %s 不在 %s(薄尾不假裝有)" % (PRIOR_NAME, _HERE))
    spec = _ilu.spec_from_file_location("SUP_MDL753_VIACommonUtils_v0112", path)
    mod = _ilu.module_from_spec(spec)
    _sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR = _load_prior()
for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


def __getattr__(name):
    """PEP 562 轉接:v0112 的公開名稱上面已拷進本模組;之後才有的名稱也照前版給(不吞錯 · 沒有就 AttributeError)。"""
    return getattr(PRIOR, name)


class _Res:
    """execute() 的結果:fetchone 讀完再取第一列(DuckDB 2.x 不留未讀完的結果);其他照原物件。"""

    def __init__(self, res):
        self._r = res

    def fetchone(self):
        rows = self._r.fetchall()
        return rows[0] if rows else None

    def __getattr__(self, name):
        return getattr(self._r, name)

    def __iter__(self):
        return iter(self._r.fetchall())


class _Con:
    """連線包裝:只換 execute 的回傳;register / unregister / close / sql … 原樣轉交。"""

    def __init__(self, con):
        self._c = con

    def execute(self, *a, **kw):
        return _Res(self._c.execute(*a, **kw))

    def __getattr__(self, name):
        return getattr(self._c, name)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._c.close()
        return False


def _wrap(con):
    return con if isinstance(con, _Con) else _Con(con)


_ORIG_UPSERT_ROWS = PRIOR.upsert_rows
_ORIG_UPSERT_SELECT = PRIOR.upsert_select


def upsert_rows(db, table: str, rows: list, keys: list, *, connect=None, **kw):
    """v0113 = v0112 upsert_rows · 連線包一層(DuckDB 2.x 未讀完結果相容)。參數與回傳同 v0112。"""
    if connect is None:
        import duckdb
        connect = duckdb.connect
    base = connect
    return _ORIG_UPSERT_ROWS(db, table, rows, keys, connect=lambda p: _wrap(base(p)), **kw)


def upsert_select(con, table: str, src: str, keys=None, **kw):
    """v0113 = v0112 upsert_select · 呼叫端的連線包一層(不開不關 · 只換 execute 的回傳)。"""
    return _ORIG_UPSERT_SELECT(_wrap(con), table, src, keys, **kw)


PRIOR.upsert_rows = upsert_rows          # v0112 內部(upsert_rows → upsert_select · 它自己的自測)也走包裝
PRIOR.upsert_select = upsert_select


def selftest() -> int:
    import contextlib
    import io
    import tempfile
    bad = []

    def chk(label, cond):
        print(("  [OK] " if cond else "  [FAIL] ") + label, flush=True)
        if not cond:
            bad.append(label)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = PRIOR.selftest()
    tail = [l for l in buf.getvalue().splitlines() if l.strip()]
    chk("① v0112 全部自測經本版包裝照過(%s)" % (tail[-1].strip()[:60] if tail else "—"), rc == 0)
    try:
        import duckdb
    except ImportError:
        print("  [SKIP] 這個 Python 沒有 duckdb · ②③ 不驗", flush=True)
        duckdb = None
    if duckdb is not None:
        with tempfile.TemporaryDirectory() as td:
            db = _Path(td) / "t.duckdb"
            n1 = upsert_rows(db, "t", [{"k": 1, "v": "a"}, {"k": 2, "v": "b"}], ["k"], counts=True)
            n2 = upsert_rows(db, "t", [{"k": 2, "v": "x"}, {"k": 3, "v": "c"}], ["k"], counts=True)
            n3 = upsert_rows(db, "t", [{"k": 3, "v": None, "w": 1.5}], ["k"], fill=True, counts=True)
            con = duckdb.connect(str(db))
            try:
                rows = con.execute('SELECT k, v FROM "t" ORDER BY k').fetchall()
                con.execute("CREATE TABLE s AS SELECT 4 AS k, 'd' AS v")
                added = upsert_select(con, "t", "s", ["k"])
                after = con.execute('SELECT count(*) FROM "t"').fetchall()[0][0]
            finally:
                con.close()
        chk("② DuckDB %s:連續兩批 upsert_rows(先 count 再 register)不拋 ResourceInUse · 新增 (2, 2) → (1, 3) · 鍵已在不動 · fill 只補空欄" % duckdb.__version__,
            n1 == (2, 2) and n2 == (1, 3) and n3 == (0, 3) and rows == [(1, "a"), (2, "b"), (3, "c")])
        chk("③ upsert_select 用呼叫端連線(包一層 · 不關)→ 新增 1 列 · 之後同一連線照樣能查", added == 1 and after == 4)
    src = _Path(__file__).read_text(encoding="utf-8")
    chk("④ 第 3 行加速器標記 · 前版 v0112 一字不改(本檔不含 SQL 文字)", src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and "SELECT count(*) FROM \"{table}\"" not in src)
    print("[%s] SUP_MDL753_VIACommonUtils %s --selftest · 不過 %d" % ("PASS" if not bad else "FAIL", VERSION, len(bad)), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    if _sys.argv[1:] == ["--selftest"]:
        raise SystemExit(selftest())
    raise SystemExit(PRIOR.main() if hasattr(PRIOR, "main") else 0)
