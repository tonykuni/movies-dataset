#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG047_USMacroDetailFetcher — 美國經濟細目擷取引擎(批109;via-usmacro)
====================================================================
令:「通膨就業都有很詳細的細目,包括 PMI 在內;就業還有各業失業、
勞參率、職缺率等等都要抓」。
冊:VDF_USMacro_Detail_Fetch_Roster(glob 最新版;增量不重複 MDL003 46 序列)。
法遵雙閘(鐵律):VIA_NET_CONSENT=YES 且 FRED_API_KEY 在 env 才實連;
否則 --fetch 誠實 FAIL-CLOSED 列印待抓清單,絕不假抓。
id 驗證:VERIFY_PENDING 首抓時打 FRED series API,404=BAD_ID 誠實記冊層
報告(不寫回冊;冊為操作員核定 SSOT,更正走版本前進)。
輸出:functional modules/VDF/output_hub/usmacro/(csv utf-8-sig+json;
parquet 有 pandas 才出,缺=SKIP 誠實)。
用法:
  via-usmacro --list              → 冊細目盤點(零網路)
  via-usmacro --fetch [--start YYYY-MM-DD]
  via-usmacro --selftest          → 八檢(沙盒零網路)
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

import csv
import io
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
OUT = VDF / "output_hub" / "usmacro"
FRED_URL = "https://api.stlouisfed.org/fred/series/observations"
ROSTER_GLOB = "VDF_USMacro_Detail_Fetch_Roster_v*.json"
DEFAULT_START = "2004-01-01"


def load_roster(root: Path = VDF) -> dict | None:
    hits = sorted(root.glob(ROSTER_GLOB))
    if not hits:
        return None
    return json.loads(hits[-1].read_text(encoding="utf-8-sig"))


def roster_items(roster: dict) -> list[dict]:
    out = []
    for sec, items in roster.get("sections", {}).items():
        for it in items:
            out.append({**it, "section": sec})
    return out


def gate_status() -> dict:
    consent = os.environ.get("VIA_NET_CONSENT", "") == "YES"
    key = bool(os.environ.get("FRED_API_KEY", ""))
    return {"consent": consent, "fred_key": key, "open": consent and key}


def _http_get_json(url: str, params: dict, timeout: int = 30):
    """實連道(僅法遵閘開啟後由 fetch 呼叫);獨立函式=selftest 可注入替身"""
    import urllib.parse
    import urllib.request
    full = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(full, headers={"User-Agent": "Mozilla/5.0 VeritasDataForge/VDF"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_series(fred_id: str, start: str, api_key: str, http=_http_get_json) -> dict:
    """單序列抓取;404/error=誠實 BAD_ID/FAIL,不假資料"""
    try:
        data = http(FRED_URL, {"series_id": fred_id, "api_key": api_key,
                               "file_type": "json", "observation_start": start})
    except Exception as exc:
        msg = str(exc)
        state = "BAD_ID" if "400" in msg or "404" in msg else "FAIL"
        return {"fred_id": fred_id, "state": state, "note": msg[:100], "rows": 0}
    obs = data.get("observations", [])
    rows = [{"date": o["date"], "value": (None if o.get("value") in (".", "", None) else float(o["value"]))}
            for o in obs]
    return {"fred_id": fred_id, "state": "OK", "rows": len(rows), "data": rows}


def write_outputs(fred_id: str, key: str, rows: list[dict], out_dir: Path = OUT) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    jp = out_dir / f"{fred_id}.json"
    jp.write_text(json.dumps({"fred_id": fred_id, "key": key, "rows": rows},
                             ensure_ascii=False), encoding="utf-8")
    written.append(jp.name)
    cp = out_dir / f"{fred_id}.csv"
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["date", "value"])
    for r in rows:
        w.writerow([r["date"], "" if r["value"] is None else r["value"]])
    cp.write_text(buf.getvalue(), encoding="utf-8-sig")
    written.append(cp.name)
    try:
        import pandas as pd
        df = pd.DataFrame(rows)
        df.to_parquet(out_dir / f"{fred_id}.parquet", index=False)
        written.append(f"{fred_id}.parquet")
    except Exception:
        pass  # parquet 缺件=SKIP 誠實(csv/json 已落)
    return written


def cmd_list() -> int:
    roster = load_roster()
    if roster is None:
        print("[FAIL] 細目冊缺(VDF_USMacro_Detail_Fetch_Roster_v*.json)")
        return 1
    items = roster_items(roster)
    by_conf = {}
    for it in items:
        by_conf.setdefault(it["confidence"], []).append(it)
    print(f"=== 美國經濟細目冊 · {len(items)} 項(批109)===")
    for conf in ("CONFIRMED", "VERIFY_PENDING", "PROXY_SOURCE", "COVERED_ELSEWHERE", "TODO"):
        rows = by_conf.get(conf, [])
        if not rows:
            continue
        print(f"  [{conf}] {len(rows)} 項")
        for it in rows:
            print(f"    {it.get('fred_id') or '(候定id)':<22} {it['zh']}({it['maps_to']})")
    g = gate_status()
    print(f"  [閘] VIA_NET_CONSENT={'YES' if g['consent'] else '未設'} · FRED_API_KEY={'在' if g['fred_key'] else '缺'}"
          f" → {'可實抓' if g['open'] else '實抓候雙閘(誠實 FAIL-CLOSED)'}")
    return 0


def cmd_fetch(start: str, http=_http_get_json, env=None) -> int:
    env = env if env is not None else os.environ
    roster = load_roster()
    if roster is None:
        print("[FAIL] 細目冊缺")
        return 1
    consent = env.get("VIA_NET_CONSENT", "") == "YES"
    key = env.get("FRED_API_KEY", "")
    if not (consent and key):
        print("[FAIL-CLOSED] 法遵雙閘未開:需 VIA_NET_CONSENT=YES + FRED_API_KEY(絕不代設)")
        print("  待抓清單(--list 檢視細目);零外呼結束(誠實)")
        return 2
    items = [it for it in roster_items(roster)
             if it.get("fred_id") and it["confidence"] in ("CONFIRMED", "VERIFY_PENDING")]
    ok = bad = fail = 0
    results = []
    for i, it in enumerate(items, 1):
        r = fetch_series(it["fred_id"], start, key, http=http)
        results.append({**{k: it[k] for k in ("key", "zh", "confidence", "maps_to")}, **
                        {k: r[k] for k in ("fred_id", "state", "rows")}})
        if r["state"] == "OK":
            ok += 1
            write_outputs(it["fred_id"], it["key"], r["data"])
        elif r["state"] == "BAD_ID":
            bad += 1
        else:
            fail += 1
        bar = "█" * int(24 * i / len(items)) + "░" * (24 - int(24 * i / len(items)))
        sys.stdout.write(f"\r  [{bar}] {i}/{len(items)} OK {ok} · BAD_ID {bad} · FAIL {fail}   ")
        sys.stdout.flush()
        time.sleep(0.1)  # FRED 禮貌節流
    print()
    OUT.mkdir(parents=True, exist_ok=True)
    rp = OUT / f"FETCH_RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    rp.write_text(json.dumps({"schema": "vdf.usmacro.fetchrun.v1", "start": start,
                              "results": results,
                              "counts": {"ok": ok, "bad_id": bad, "fail": fail}},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [計] OK {ok} · BAD_ID {bad}(冊更正走版本前進)· FAIL {fail} · 存證 {rp.name}")
    return 0 if fail == 0 else 1


# ── 八檢自測(沙盒零網路)────────────────────────────────────────
def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    roster = load_roster()
    chk("① 細目冊在位(glob 最新版)", roster is not None)
    items = roster_items(roster)
    chk("② 細目數與 changelog 相符", len(items) == 43, f"({len(items)} 項)")
    ids = [it["fred_id"] for it in items if it.get("fred_id")]
    chk("③ fred_id 唯一零重複", len(ids) == len(set(ids)))
    # ④ 與 MDL003 零重複(增量鐵則;僅檢實抓圈=CONFIRMED/VERIFY_PENDING,
    #    COVERED_ELSEWHERE 為交叉參照件本就指向 MDL003)
    fetch_ids = [it["fred_id"] for it in items if it.get("fred_id")
                 and it["confidence"] in ("CONFIRMED", "VERIFY_PENDING")]
    mdl3 = (VDF / "engine" / "VDF_MDL003_SentimentMacroEngine.py").read_text(encoding="utf-8", errors="replace")
    dup = [i for i in fetch_ids if f'"{i}"' in mdl3]
    chk("④ 實抓圈不重複 MDL003 既有序列", not dup, f"(重複:{dup[:3]})" if dup else "")
    # ⑤ 法遵閘 fail-closed(空環境)
    rc = cmd_fetch(DEFAULT_START, env={})
    chk("⑤ 雙閘未開=FAIL-CLOSED rc2", rc == 2)
    # ⑥ 替身 http:OK/BAD_ID/FAIL 三態
    def fake_http(url, params, timeout=30):
        sid = params["series_id"]
        if sid == "U6RATE":
            return {"observations": [{"date": "2026-01-01", "value": "7.5"},
                                     {"date": "2026-02-01", "value": "."}]}
        raise RuntimeError("HTTP Error 400: Bad Request")
    r_ok = fetch_series("U6RATE", "2026-01-01", "k", http=fake_http)
    r_bad = fetch_series("NOPE", "2026-01-01", "k", http=fake_http)
    chk("⑥ 抓取三態(OK/缺值 None/BAD_ID)",
        r_ok["state"] == "OK" and r_ok["rows"] == 2 and r_ok["data"][1]["value"] is None
        and r_bad["state"] == "BAD_ID")
    # ⑦ 輸出落檔(csv utf-8-sig+json;parquet 缺件誠實跳)
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        w = write_outputs("U6RATE", "US.Employ.U6", r_ok["data"], out_dir=Path(td))
        cp = Path(td) / "U6RATE.csv"
        chk("⑦ 輸出 csv(sig)+json", "U6RATE.csv" in w and "U6RATE.json" in w
            and cp.read_bytes()[:3] == b"\xef\xbb\xbf")
    # ⑧ --list 零網路可跑
    chk("⑧ --list 零網路", cmd_list() == 0)
    n = 8 - len(fails)
    print(f"  [計] 八檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== ENG047 美國經濟細目擷取 · 八檢自測(沙盒零網路)===")
        return selftest()
    if "--fetch" in args:
        start = DEFAULT_START
        if "--start" in args:
            i = args.index("--start")
            start = args[i + 1] if i + 1 < len(args) else DEFAULT_START
        return cmd_fetch(start)
    return cmd_list()


if __name__ == "__main__":
    sys.exit(main())
