#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VRN_ENG082_ExtractionLogic v0111 — VRN 擷取**中央邏輯庫**(薄尾:全庫同步每一輪落一份結果報告 SYNCDB_latest.json;R34 收尾實測)
v0110→v0111(R34 收尾實測):
  `sync-db` 的 rc 2 同時涵蓋 SKIP(一本目標庫都沒有)· PARTIAL · BUSY · FAIL,VCGC 的中樞事件只記 rc;SDD 驗證器因此分不出
  「資料家空、沒庫可寫」(要先有資料 = 操作員的手)跟「庫忙 / 寫壞」(要人看)。空資料家的收尾輪裡 VDF-WKF001-STP005
  就停在沒有成因的 FINDING。
  現在每次 sync_db() 都把本輪結果 {ts · state · why · targets · ok / busy / fail · explicit_db · dry_run} 落在存證夾
  (logic_dir():VIA_LOGIC_DIR 或 VIA_Reports/vrn/extraction_logic)的 SYNCDB_latest.json;驗證器(CGC_MDL245 v0102
  finding_cause: syncdb_no_target)只讀這份本輪報告追因。同步本身一字未動(前版照讀,不複製);報告寫不出去不改同步結果,
  照實記在回傳的 report_error。自測零污染律照舊:VIA_SELFTEST=1 而沒有指定暫存存證夾時不寫報告(真目錄零觸碰)。
  掛法:前版 main() 與自測經模組全域叫 sync_db() → 本支換掉它。零網路 · 不用 TA-Lib。
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
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_ENG082_ExtractionLogic"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                  default=HERE / "VRN_ENG082_ExtractionLogic_v0110.py")   # the prior this tail was cut from
_spec = importlib.util.spec_from_file_location("extraction_logic_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


ENGINE = Path(__file__).stem
REPORT_NAME = "SYNCDB_latest.json"
_PRIOR_SYNC_DB = PRIOR.sync_db


def sync_report_path() -> Path:
    return PRIOR.logic_dir() / REPORT_NAME


def _report_allowed() -> bool:
    """自測零污染律:VIA_SELFTEST=1 而沒有指定暫存存證夾(VIA_LOGIC_DIR)時不寫 —— 真目錄零觸碰。"""
    return os.environ.get("VIA_SELFTEST") != "1" or bool(os.environ.get("VIA_LOGIC_DIR", "").strip())


def sync_db(db: str | None = None, dry_run: bool = False, quiet: bool = False) -> dict:
    """v0111:同步照前版;另把本輪結果落成 SYNCDB_latest.json(驗證器追因用)。"""
    out = _PRIOR_SYNC_DB(db, dry_run=dry_run, quiet=quiet)
    if not _report_allowed():
        return out
    rep = {"engine": ENGINE, "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "state": out.get("state"),
           "why": str(out.get("why") or ""), "explicit_db": str(db or ""), "dry_run": bool(dry_run),
           "targets": [str(t.get("db") or "") for t in out.get("targets") or []],
           "ok": out.get("ok", 0), "busy": out.get("busy", 0), "fail": out.get("fail", 0)}
    try:
        p = sync_report_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        out["report"] = str(p)
    except OSError as exc:
        out["report_error"] = f"{type(exc).__name__}: {exc}"[:160]
    return out


PRIOR.sync_db = sync_db


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    import tempfile
    print(f"=== VRN_ENG082 v{ENGINE.rsplit('_v', 1)[-1]} 薄尾 · 全庫同步本輪報告(零網路;暫存夾)===")
    keys = [k for k in os.environ if k.startswith("VIA_DB_")] + ["VIA_LOGIC_DIR", "VIA_DATA_HOME", "VIA_SELFTEST"]
    saved = {k: os.environ.get(k) for k in keys}
    real = PRIOR.VIA / "VIA_Reports" / "vrn" / "extraction_logic"
    before = sorted(x.name for x in real.glob("*")) if real.exists() else []
    global _PRIOR_SYNC_DB
    real_sync = _PRIOR_SYNC_DB
    skip = {"state": "SKIP", "db": "", "logic_rows": 0, "policy_rows": 0, "targets": [], "ok": 0, "busy": 0, "fail": 0,
            "why": "庫缺:env VIA_DB_* / VIA_DATA_HOME / output_hub/mega 皆無 .duckdb(先 via-datahome catalog)"}
    with tempfile.TemporaryDirectory() as td:
        try:
            for k in keys:
                os.environ.pop(k, None)
            os.environ["VIA_SELFTEST"] = "1"
            os.environ["VIA_DATA_HOME"] = str(Path(td) / "home_absent")
            os.environ["VIA_LOGIC_DIR"] = str(Path(td) / "logic")
            _PRIOR_SYNC_DB = lambda db=None, dry_run=False, quiet=False: dict(skip)      # noqa: E731  前版回 SKIP 的樣子(不碰任何庫)
            r = sync_db(None, quiet=True)
            rep = json.loads(sync_report_path().read_text(encoding="utf-8"))
            chk("① 前版回 SKIP(一本目標庫都沒有)→ 本輪報告落在指定存證夾:state SKIP · targets 空 · 原因帶「庫缺」;回傳照前版",
                r["state"] == "SKIP" and rep["state"] == "SKIP" and rep["targets"] == [] and "庫缺" in rep["why"]
                and sync_report_path().parent == Path(td) / "logic" and rep["ts"] and r.get("report") == str(sync_report_path()),
                rep.get("why", "")[:40])
            _PRIOR_SYNC_DB = real_sync
            ok2, ok3, note2 = False, False, "duckdb 缺(本境沒有:誠實不過,不假綠)"
            try:
                import duckdb
                db = Path(td) / "vdf_tw_market.duckdb"
                duckdb.connect(str(db)).close()
                r2 = sync_db(str(db), quiet=True)                                       # 指名暫存庫:真同步,不碰任何真庫
                rep2 = json.loads(sync_report_path().read_text(encoding="utf-8"))
                ok2 = (r2["state"] == "OK" and rep2["state"] == "OK" and rep2["targets"] == [str(db)] and rep2["ok"] == 1
                       and rep2["explicit_db"] == str(db))
                note2 = f"{rep2['state']} · {len(rep2['targets'])} 本"
                sync_db(str(db), dry_run=True, quiet=True)
                rep3 = json.loads(sync_report_path().read_text(encoding="utf-8"))
                ok3 = rep3["dry_run"] is True and rep3["state"] == "DRY"
            except ImportError:
                pass
            chk("② 真同步(指名暫存庫)照前版 OK,報告覆寫成本輪:state OK · targets 列出那一本 · explicit_db 照記", ok2, note2)
            chk("③ 乾跑也照實記(dry_run · state DRY),驗證器據此不把它當成「沒庫」", ok3)
            os.environ.pop("VIA_LOGIC_DIR", None)
            _PRIOR_SYNC_DB = lambda db=None, dry_run=False, quiet=False: dict(skip)      # noqa: E731
            r4 = sync_db(None, quiet=True)
            after = sorted(x.name for x in real.glob("*")) if real.exists() else []
            chk("④ 自測零污染律:VIA_SELFTEST=1 又沒指定存證夾 → 不寫報告,真存證夾零觸碰",
                before == after and not _report_allowed() and "report" not in r4)
        finally:
            _PRIOR_SYNC_DB = real_sync
            for k in list(os.environ):
                if k.startswith("VIA_DB_") or k in ("VIA_LOGIC_DIR", "VIA_DATA_HOME", "VIA_SELFTEST"):
                    os.environ.pop(k, None)
            os.environ.update({k: v for k, v in saved.items() if v is not None})
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 前版 main() / 自測叫到的就是本支 sync_db;本支帶加速器橋、不含 TA-Lib 匯入",
        PRIOR.sync_db is sync_db and "[VIA:ACCEL-BRIDGE" in body
        and not re.search(r"^\s*(?:import|from)\s+" + "ta" + r"lib\b", body, re.M))
    rc = PRIOR.selftest()
    return 0 if all(ok) and rc == 0 else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
