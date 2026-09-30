#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC v0179 — 薄尾:元件註冊新時間寫 UTC(registry-sync --apply 寫完,本輪新增 / 變更的記錄時間補時區)

實測(側線 2026-09-30 a,風險 R08;正本 VIA_Registry_Architecture_SSOT 的 time 節):元件冊 first_seen · changed_at · retired_at ·
recoded_at 由 datetime.now() 寫成「無時區本地時間」—— 容器是 UTC、工作站是 UTC+8,同一本冊混兩種鐘,跨機不能比、不能排序。
  ① registry-sync … --apply 經 v0178 照舊寫完之後,只把「本輪新出現或本輪改過」的時間欄從寫入那台機器的本地時間換成
     UTC ISO 帶時區(YYYY-MM-DDTHH:MM:SS+00:00);舊記錄一字不改寫(舊值是誰的鐘無從得知,改了反而造假)。
  ② 冊的寫法照舊(indent 1 · UTF-8 · 結尾換行 · 原子替換);乾跑(沒有 --apply)不碰冊。
  ③ help 目錄記時間規範。其餘照 v0178(入口 · 省 Token 第一步 · 功能卡 · 全景 · 管理器沿鏈讀)。零網路。
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
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"
PRIOR_PATH = max(p for p in HERE.glob(_STEM + "_v*.py") if p.name < Path(__file__).name)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_v0179", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
TIME_FIELDS = ("first_seen", "changed_at", "retired_at", "recoded_at")
NAIVE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")
TIME_RULE = "新寫入 UTC ISO 帶時區 YYYY-MM-DDTHH:MM:SS+00:00;舊的無時區本地時間照舊保留(正本 VIA_Registry_Architecture_SSOT time 節)"


def __getattr__(name):
    return getattr(PRIOR, name)


def to_utc(value: str) -> str:
    """A naive local timestamp written moments ago on this machine → the same instant in UTC with an explicit offset."""
    return datetime.fromisoformat(value).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def _snapshot(path: Path) -> tuple:
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}, None
    return {r.get("key"): {f: r.get(f) for f in TIME_FIELDS} for r in doc.get("records") or []}, doc.get("updated_at")


def stamp_utc(path: Path, before: dict, before_updated) -> int:
    """Rewrite only the time fields this run created or changed (naive → UTC with offset). Returns how many fields moved."""
    path = Path(path)
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0
    n = 0
    for r in doc.get("records") or []:
        old = before.get(r.get("key")) or {}
        for f in TIME_FIELDS:
            v = r.get(f)
            if isinstance(v, str) and NAIVE.match(v) and old.get(f) != v:
                r[f] = to_utc(v)
                n += 1
    upd = doc.get("updated_at")
    if isinstance(upd, str) and NAIVE.match(upd) and upd != before_updated:
        doc["updated_at"] = to_utc(upd)
        n += 1
    if n:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        os.replace(tmp, path)
    return n


def stamps(args: list) -> bool:
    return args[:1] == ["registry-sync"] and "--apply" in args and os.environ.get("VIA_FROM_VCGC") == "YES"


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not stamps(args):
        return PRIOR.main(args)
    path = Path(PRIOR.COMPONENT_REGISTRY)
    before, before_updated = _snapshot(path)
    rc = PRIOR.main(args)
    n = stamp_utc(path, before, before_updated)
    print(f"[元件註冊 · 時間] 本輪新增 / 變更的時間欄補 UTC 時區 {n} 個(舊記錄不改寫;{TIME_RULE})")
    return rc


def help_catalog():
    card = PRIOR.help_catalog()
    card.update(entry=Path(__file__).name, previous=PRIOR_PATH.name, registry_time=TIME_RULE)
    return card


def selftest():
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    got = to_utc("2026-09-30T08:00:00")
    want = datetime(2026, 9, 30, 8, 0, 0).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    chk("① 本地無時區時間 → 同一瞬間的 UTC 帶時區", got == want and got.endswith("+00:00"), got)
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "inv.json"
        doc = {"updated_at": "2026-09-29T10:00:00", "records": [
            {"key": "a", "code": "VIA-FNC-0001", "first_seen": "2026-09-01T01:00:00"},
            {"key": "b", "code": "VIA-FNC-0002", "first_seen": "2026-09-01T01:00:00", "changed_at": "2026-09-02T01:00:00"},
            {"key": "c", "code": "VIA-FNC-0003", "first_seen": "2026-09-01T01:00:00+00:00"}]}
        p.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        before, before_updated = _snapshot(p)
        doc["records"][1]["changed_at"] = "2026-09-30T09:00:00"
        doc["records"].append({"key": "d", "code": "VIA-FNC-0004", "first_seen": "2026-09-30T09:00:00"})
        doc["updated_at"] = "2026-09-30T09:00:00"
        p.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        n = stamp_utc(p, before, before_updated)
        after = json.loads(p.read_text(encoding="utf-8"))
        again = stamp_utc(p, _snapshot(p)[0], _snapshot(p)[1])
        raw = p.read_text(encoding="utf-8")
    recs = {r["key"]: r for r in after["records"]}
    chk("② 只補本輪新增 / 變更的時間:舊記錄原樣 · 新記錄與變更欄 · updated_at 補 +00:00",
        n == 3 and recs["a"]["first_seen"] == "2026-09-01T01:00:00" and recs["b"]["first_seen"] == "2026-09-01T01:00:00"
        and recs["b"]["changed_at"].endswith("+00:00") and recs["d"]["first_seen"].endswith("+00:00")
        and recs["c"]["first_seen"] == "2026-09-01T01:00:00+00:00" and after["updated_at"].endswith("+00:00"), f"補 {n}")
    chk("③ 重跑不重補(已帶時區的不動)· 冊寫法 indent 1 結尾換行", again == 0 and raw.endswith("\n") and raw.startswith('{\n "updated_at"'))
    env_ok = os.environ.get("VIA_FROM_VCGC")
    os.environ["VIA_FROM_VCGC"] = "YES"
    try:
        wires = [stamps(["registry-sync", "--apply"]), stamps(["registry-sync"]), stamps(["registry-sync", "--layout-only", "--apply"]),
                 stamps(["status"])]
    finally:
        if env_ok is None:
            os.environ.pop("VIA_FROM_VCGC", None)
        else:
            os.environ["VIA_FROM_VCGC"] = env_ok
    chk("④ 只有 registry-sync … --apply 才補時間;乾跑與其他動詞不碰冊", wires == [True, False, True, False], wires)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ help 目錄記時間規範 · 加速器橋 · 網路橋在;不碰 TA-Lib", help_catalog().get("registry_time") == TIME_RULE
        and "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    print(f"[VCGC v0179] 本版 {sum(ok)}/{len(ok)}")
    if not all(ok):
        return 1
    return PRIOR.selftest()


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
