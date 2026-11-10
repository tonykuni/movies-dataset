#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_LakeMatrix v0101 — 薄尾(v0100 一字不動):Codex PR #623 兩項 P2。

① 五系統 × 日 活動矩陣:v0100 只拿每表 first / last 入湖兩個時間點(中間日漏算 · 單分片算兩次)→ 本版逐分片算:
   每個 part-<UTC>-<sha8>.parquet 的檔名戳就是入湖日,一片一計;既有資產照舊以檔案更新日計。
② 湖內部分壞表:v0100 只有「全壞」才 RED,一表好一表壞仍 GREEN,且壞表不出現在報表 → 本版任何壞表 = 非綠
   (全壞 RED · 部分壞 YELLOW),壞表列進資產明細(類 lake(壞)· 狀態 錯:…),說明也點名。
③ 套件改取尾版 glob(VIA_ParquetLake_v0101 起:混型來源 · 微秒戳;Codex #624 P1 要求 v0100 不就地改)。
其餘(入湖 · 盤點 · 工具活動 · HTML / md · 自測 12 項)照 v0100,本版自測 = 前版鏈 + 本版 4 項。
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

import importlib.util
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

VERSION = "v0101"
ENGINE = "VIA_LakeMatrix " + VERSION
HERE = Path(__file__).resolve().parent
_PRIOR_FILE = HERE / "VIA_LakeMatrix_v0100.py"
_spec = importlib.util.spec_from_file_location("VIA_LakeMatrix_v0100", _PRIOR_FILE)
P = importlib.util.module_from_spec(_spec)
sys.modules["VIA_LakeMatrix_v0100"] = P
_spec.loader.exec_module(P)
_prior_system_cards = P.system_cards
_prior_activity = P.activity
_prior_lake_module = P._lake_module


def _lake_module():
    """套件取尾版(VIA_ParquetLake_v*.py 最高版號;Codex #624 P1:v0100 不就地改,新行為在 v0101)。"""
    import glob as _glob
    hits = sorted(_glob.glob(str(P.VIA / "supportive modules" / "VIA_ParquetLake_v*.py")))
    if not hits:
        return _prior_lake_module()
    spec = importlib.util.spec_from_file_location("VIA_ParquetLake_tail", hits[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


P._lake_module = _lake_module
_PART_RX = re.compile(r"^part-(\d{8})T\d{6}")


def system_cards(via: Path, root: Path, now: datetime) -> list[dict]:
    """② 任何湖內壞表 = 非綠;壞表列進資產明細。"""
    cards = _prior_system_cards(via, root, now)
    for c in cards:
        errs = c.get("lake_errors") or []
        if not errs:
            continue
        for t in errs:
            c["legacy"].append({"kind": "lake(壞)", "name": t["table"], "path": str(Path(c["lake_home"]) / t["table"]), "rel": "%s/%s" % (c["system"], t["table"]), "files": t.get("parts", 0),
                                "bytes": 0, "rows": 0, "mtime": "", "age_days": None, "tables": [], "error": t["error"], "bad_files": t.get("parts", 0)})
        if c["lake_tables"]:
            c["lamp"] = "YELLOW" if c["lamp"] == "GREEN" else c["lamp"]
            c["why"] = "%s · 湖內壞表 %d(%s)" % (c["why"], len(errs), " · ".join(t["table"] for t in errs[:3]))
        else:
            c["lamp"] = "RED"
            c["why"] = "湖內表全壞 %d:%s" % (len(errs), "; ".join(t["error"][:60] for t in errs[:2]))
    return cards


def activity(root: Path, cards: list[dict], now: datetime) -> dict:
    """① 五系統 × 日:逐分片(檔名戳)+ 既有資產更新日;不用 first / last 兩點。"""
    out = _prior_activity(root, cards, now)
    days = out["days"]
    for c in cards:
        row = {d: 0 for d in days}
        home = Path(c["lake_home"])
        for t in c.get("lake_tables", []) + c.get("lake_errors", []):
            tdir = home / t["table"]
            if tdir.is_dir():
                for p in tdir.glob("part-*.parquet"):
                    m = _PART_RX.match(p.name)
                    if m:
                        d = "%s-%s-%s" % (m.group(1)[:4], m.group(1)[4:6], m.group(1)[6:8])
                        if d in row:
                            row[d] += 1
        for a in c.get("legacy", []):
            if a.get("kind") == "lake(壞)":
                continue  # 壞表的分片上面已逐片算過
            dd = str(a.get("mtime", ""))[:10]
            if dd in row:
                row[dd] += a.get("files", 1) if a["kind"] == "parquet" else 1
        out["systems_by_day"][c["system"]] = row
    out["proxy_note"] = "五系統 × 日 = 湖分片逐片(檔名入湖戳)+ 既有資產檔案更新日(代理指標 · 照實);工具事件 = VCGC 湖 function_ledger"
    return out


P.system_cards = system_cards
P.activity = activity
P.ENGINE = ENGINE
P.VERSION = VERSION
build, to_md, to_html, write_outputs, resolve_root = P.build, P.to_md, P.to_html, P.write_outputs, P.resolve_root


def run(via: Path, root: str | None = None, no_write: bool = False, open_after: bool = False) -> int:
    return P.run(via, root=root, no_write=no_write, open_after=open_after)


def selftest() -> int:
    rc = P.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))
    import pyarrow as pa
    import pyarrow.parquet as pq
    now = datetime(2026, 11, 10, 3, 0, tzinfo=timezone.utc)
    with tempfile.TemporaryDirectory(prefix="via_lakematrix101_") as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        (via / "supportive modules").mkdir(parents=True)
        import glob as _glob
        for kp in sorted(_glob.glob(str(P.VIA / "supportive modules" / "VIA_ParquetLake_v*.py"))):
            (via / "supportive modules" / Path(kp).name).write_text(Path(kp).read_text(encoding="utf-8"), encoding="utf-8")
        root = via / P.OUT_DIR
        good = root / "VCGC" / "good"
        good.mkdir(parents=True)
        for i, day in enumerate(("20261108", "20261109", "20261110")):
            pq.write_table(pa.table({"id": ["r%d" % i], "_ingested_at": ["%s-%s-%sT01:00:00.000000Z" % (day[:4], day[4:6], day[6:8])]}), good / ("part-%sT010000000000Z-%08d.parquet" % (day, i)), compression="zstd")
        bad = root / "VCGC" / "bad"
        bad.mkdir()
        (bad / "part-20261110T020000000000Z-deadbeef.parquet").write_bytes(b"not a parquet file")
        (root / "VCGC" / "_manifest.jsonl").write_text("", encoding="utf-8")
        b = build(via, root, "--root", now, ingest=False)
        vc = [c for c in b["systems"] if c["system"] == "VCGC"][0]
        chk("ⓐ 一表好一表壞 → VCGC YELLOW(不是 GREEN)· 說明點名壞表 · 壞表列進資產明細 kind lake(壞)帶錯誤",
            vc["lamp"] == "YELLOW" and "bad" in vc["why"] and any(a["kind"] == "lake(壞)" and a["name"] == "bad" and a["error"] for a in vc["legacy"]), (vc["lamp"], vc["why"][:80]))
        row = b["activity"]["systems_by_day"]["VCGC"]
        chk("ⓑ 五系統 × 日 逐分片:11-08 1 · 11-09 1 · 11-10 2(好表 1 + 壞表分片 1)· 不再首尾兩點",
            row.get("2026-11-08") == 1 and row.get("2026-11-09") == 1 and row.get("2026-11-10") == 2, row)
        md, h = to_md(b), to_html(b)
        chk("ⓒ md / html 都出現壞表列與錯誤字樣 · 引擎名 v0101", "lake(壞)" in md and "lake(壞)" in h and "錯:" in md and ENGINE in b["engine"])
        bad_only = root / "VDF" / "broken"
        bad_only.mkdir(parents=True)
        (bad_only / "part-20261110T020000000000Z-00000000.parquet").write_bytes(b"x")
        (root / "VDF" / "_manifest.jsonl").write_text("", encoding="utf-8")
        b2 = build(via, root, "--root", now, ingest=False)
        vd = [c for c in b2["systems"] if c["system"] == "VDF"][0]
        chk("ⓓ 全壞 → RED(v0100 行為保留)", vd["lamp"] == "RED" and "全壞" in vd["why"], vd["why"][:60])
    bad_n = len(ok) - sum(ok)
    print("[%s] %s selftest · 本版 %d/%d · 前版鏈 v0100 %s" % ("PASS" if not bad_n and rc == 0 else "FAIL", ENGINE, sum(ok), len(ok), "PASS" if rc == 0 else "FAIL"), flush=True)
    return 0 if not bad_n and rc == 0 else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args or (args and args[0] == "selftest"):
        return selftest()
    return P.main(args)


def __getattr__(name):
    return getattr(P, name)


if __name__ == "__main__":
    sys.exit(main())
