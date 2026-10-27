#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_ENG050_OrderFetch v0102 — 薄尾:擷取單 TWSE 道每日請求出錯不再默默吞掉(VCGC 全景 SWALLOW · 第二輪 2026-10-20)

操作員令(2026-10-20):「繼續第二輪修復 SWALLOW 與 TAILAPI」。
v0101 fetch_twse_lane 帶 {YYYYMMDD} 的端點逐日請求,`except Exception: continue` 把每一天的錯都吞掉:
全部日子都連不上(403 / 逾時 / JSON 壞)時照樣記 EMPTY(「交易所那幾天沒資料」),跟真的沒資料分不出來。本版(只改這一支):
  ① 每天的錯照實記:errors 筆數 · error_examples(前 3 筆:日期 + 錯誤類別 + 訊息)· note 一行。
  ② 全部日子都出錯、一筆也沒拿到 = FAIL(與不帶日期端點出錯同一判法);有拿到 = OK;沒出錯也沒資料 = EMPTY(照舊)。
  ③ 拿到的資料、欄位、順序一字不改;run() 只數 OK,總結行不變。
換在 v0101 模組全域(run() 走這支);其餘全照 v0101。VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib;不裝套件、不寫環境。
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

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG050_OrderFetch"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0102(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0102(p) < _vnum_v0102(__file__)), key=_vnum_v0102)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_FETCH_TWSE_LANE_V0101 = PRIOR.fetch_twse_lane


def __getattr__(name):
    return getattr(PRIOR, name)


def fetch_twse_lane(targets: list, days: list, http=None) -> dict:
    """同 v0101;逐日請求出錯照實記(errors · error_examples · note),全部日子出錯又沒拿到 = FAIL。"""
    results = []
    for t in targets:
        ep = t["endpoint"]
        if "{YYYYMMDD}" in ep:
            got, errs = [], []
            for d in days:
                try:
                    data = PRIOR._http_json(ep.replace("{YYYYMMDD}", d), http=http)
                    if data and (data.get("data") or data.get("tables")):
                        got.append({"date": d, "payload": data})
                except Exception as exc:          # noqa: BLE001 — 單日出錯不擋其他日子;照實記下(v0101 在這裡吞掉)
                    errs.append("%s %s: %s" % (d, type(exc).__name__, str(exc)[:80]))
            state = "OK" if got else ("FAIL" if errs and len(errs) == len(days) else "EMPTY")
            r = {"key": t["key"], "state": state, "days": len(got), "data": got}
            if errs:
                r.update(errors=len(errs), error_examples=errs[:3], note="%d/%d 天請求出錯(%s)" % (len(errs), len(days), errs[0]))
            results.append(r)
        else:
            try:
                data = PRIOR._http_json(ep, http=http)
                results.append({"key": t["key"], "state": "OK",
                                "rows": len(data) if isinstance(data, list) else 1,
                                "data": data})
            except Exception as exc:              # noqa: BLE001 — 同 v0101:照實記 FAIL
                results.append({"key": t["key"], "state": "FAIL", "note": str(exc)[:100]})
    return {"results": results}


PRIOR.fetch_twse_lane = fetch_twse_lane


def own_checks() -> int:
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    days = ["20261014", "20261015", "20261016"]
    tgt = [{"key": "t86", "endpoint": "https://x/T86?date={YYYYMMDD}"}]

    def flaky(url):
        if "20261015" in url:
            raise RuntimeError("CONNECT 403 Forbidden(沙盒)")
        return {"data": [["r"]]}

    def dead(url):
        raise TimeoutError("read timed out")

    def safe(fn, *a, **k):
        try:
            return fn(*a, **k)
        except Exception as exc:                  # noqa: BLE001 — 自測裡崩了也照實算 FAIL(不讓整支自測掛掉)
            return {"_crash": "%s %s" % (type(exc).__name__, str(exc)[:120])}
    a = safe(lambda: fetch_twse_lane(tgt, days, http=flaky)["results"][0])
    b = safe(lambda: fetch_twse_lane(tgt, days, http=dead)["results"][0])
    c = safe(lambda: fetch_twse_lane(tgt, days, http=lambda u: {"data": []})["results"][0])
    old_b = _FETCH_TWSE_LANE_V0101(tgt, days, http=dead)["results"][0]
    chk("① 有一天出錯:照實記 errors 1 · 示例帶日期與錯誤類別;其餘兩天照收、state OK(資料一字不改)",
        a.get("state") == "OK" and a.get("days") == 2 and a.get("errors") == 1 and "20261015 RuntimeError" in (a.get("error_examples") or [""])[0]
        and [g["date"] for g in a.get("data") or []] == ["20261014", "20261016"], a)
    chk("② 全部日子都出錯、一筆沒拿到 = FAIL(errors 3 · note 一行);v0101 在同一情況記 EMPTY(假裝沒資料)",
        b.get("state") == "FAIL" and b.get("errors") == 3 and "3/3 天請求出錯" in str(b.get("note")) and old_b["state"] == "EMPTY", (b, old_b["state"]))
    chk("③ 沒出錯也沒資料 = EMPTY 照舊(不多 errors 欄);不帶日期端點出錯照舊 FAIL + note",
        c.get("state") == "EMPTY" and "errors" not in c
        and fetch_twse_lane([{"key": "all", "endpoint": "https://x/ALL"}], days, http=dead)["results"][0]["state"] == "FAIL")
    chk("④ v0101 模組全域換成本版(run() 走這支)", PRIOR.fetch_twse_lane is fetch_twse_lane)
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    chk("⑤ 加速器橋 · 網路橋在;不匯入他系統程式;不碰 TA-Lib;同意閘不寫",
        "VIA:ACCEL-BRIDGE" in src and "def _via_net" in src
        and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VRN2_", "VCGC"))]
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
        and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src))
    print("  [計] %s 本版 %d/%d · %s" % (TAG, p, p + f, "PASS" if not f else "FAIL"), flush=True)
    return 0 if not f else 1


def selftest() -> int:
    rc = own_checks()
    return rc or PRIOR.selftest()


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== %s · 薄尾自測(TWSE 道逐日出錯照實記;沙盒零網路)===" % TAG, flush=True)
        if own_checks():
            return 1
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
