#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG115_HeaderFrameTemp v0102 — 薄尾:duckdb 2.0 拿掉了 Relation.fetchone(),補回相容墊片

根因(容器實測 2026-11-08):duckdb 2.0.0 起 `DuckDBPyRelation` 不再有 `fetchone()`,
官方訊息要求改用 `rel.limit(1).fetchall()`。本家族 v0100 的自測第 332 行寫的是
`duckdb.sql(...).fetchone()[0]`,於是 v0101 的「舊尺仍過」第一檢就炸 AttributeError,
整支自測連 `[計]` 總表行都印不出來 → 交接案 vrn_header_frame 的成功標記永遠看不到。

本版做法(v0100 / v0101 一個位元都不改,照版本律):
  ① 進自測前把 `DuckDBPyRelation.fetchone` 用官方指定的替代寫法補回去(只在原本缺席時補)
  ② 跑前版鏈(v0101 → v0100),它們的程式碼完全照原樣
  ③ 跑完**一定還原**(本來就有就不動;是本版補的就移除),不留全域副作用
  ④ 自己再驗:墊片語意正確、缺席才補、跑完乾淨、v0100 那一行真的能過

公開面照 v0101(PEP 562 轉接),本版只覆寫 selftest。
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

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _vnum(q: Path) -> int:
    """從檔名取版號;取不到回 -1(誠實,不猜)"""
    m = re.search(r"_v(\d{4})\.py$", q.name)
    return int(m.group(1)) if m else -1


_STEM = re.sub(r"_v\d{4}$", "", Path(__file__).stem)
# 家族式取前版:比自己小的最大版號(不把版號字串釘死在程式裡 → 不觸 PINVER)
_PRIOR_PATH = max((q for q in HERE.glob(_STEM + "_v*.py")
                   if 0 <= _vnum(q) < _vnum(Path(__file__))),
                  key=_vnum, default=HERE / (_STEM + "_v0100.py"))


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = _load(_PRIOR_PATH, "vrn_eng115_prior_for_" + Path(__file__).stem)


def __getattr__(name: str):
    """PEP 562:v0101(以及它再往回的 v0100)公開面照舊可叫。"""
    return getattr(PRIOR, name)


# ────────────────────────────────── duckdb 相容墊片
def _shim_relation_fetchone():
    """duckdb 2.0 拿掉的 Relation.fetchone() 用官方指定寫法補回。
    回 (restore, installed):restore() 還原;installed=True 表示是本版補的。"""
    try:
        import duckdb
    except Exception:
        return (lambda: None), False
    rel_cls = getattr(duckdb, "DuckDBPyRelation", None)
    if rel_cls is None:
        return (lambda: None), False
    if hasattr(rel_cls, "fetchone"):
        return (lambda: None), False          # 本來就有:一個字都不動

    def fetchone(self):
        # 官方訊息指定的替代:relation 不留結果,所以取第一列要自己 limit
        rows = self.limit(1).fetchall()
        return rows[0] if rows else None

    rel_cls.fetchone = fetchone

    def restore():
        try:
            del rel_cls.fetchone
        except Exception as e:  # noqa: BLE001
            # 不吞原因:還原失敗要講出來(別的行程可能已經先拿掉了)
            print(f"  [還原] 墊片移除沒成功:{type(e).__name__} {str(e)[:80]}"
                  f" —— 照實記,不當成功")

    return restore, True


def selftest() -> int:
    fails: list[str] = []

    def chk(name, ok, note=""):
        print(("  [OK] " if ok else "  [FAIL] ") + name + (f" {note}" if note else ""))
        if not ok:
            fails.append(name)

    try:
        import duckdb
        ver = duckdb.__version__
        had = hasattr(duckdb.DuckDBPyRelation, "fetchone")
    except Exception as e:
        print(f"  [缺件] duckdb 不在({type(e).__name__})→ 本版無事可做,照前版跑")
        return PRIOR.selftest()

    restore, installed = _shim_relation_fetchone()
    try:
        chk(f"① duckdb {ver}:原本缺 Relation.fetchone 才補(本來就有就不動)",
            installed == (not had), f"had={had} installed={installed}")
        if installed or had:
            got = duckdb.sql("SELECT 42").fetchone()
            chk("② 墊片語意對:取第一列、回 tuple", got == (42,), str(got))
            empty = duckdb.sql("SELECT 1 WHERE 1=0").fetchone()
            chk("③ 零列回 None(不炸、不編一個出來)", empty is None, repr(empty))
            many = duckdb.sql("SELECT * FROM (VALUES (1),(2),(3)) t(x)").fetchone()
            chk("④ 多列只取第一列", many == (1,), str(many))
        rc_prior = PRIOR.selftest()
        chk("⑤ 前版鏈 v0101 → v0100 在墊片下全過(v0100 第 332 行那句不再炸)",
            rc_prior == 0, f"rc={rc_prior}")
    finally:
        restore()

    now_has = hasattr(duckdb.DuckDBPyRelation, "fetchone")
    chk("⑥ 跑完一定還原:本版補的要移除,本來就有的要留著",
        now_has == had, f"had={had} now={now_has}")

    print(f"  [計] VRN_ENG115_HeaderFrameTemp v0102 薄尾 {6 - len(fails)}/6 · "
          + ("PASS" if not fails else "FAIL"))
    return 1 if fails else 0


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main() if hasattr(PRIOR, "main") else 0


if __name__ == "__main__":
    sys.exit(main())
