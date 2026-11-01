#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN-2 SystemManager v0248 — 補環(reconstruction bridge · 2026-10-29 · 直通前版 v0245)。

原 v0248(v0249「發布層接進主流程與 U/I」的釘名前版)從未進倉:倉內任何分支與 zip、桌機的 functional modules\\VRN 都沒有
(VRN2_ChainShip v0100 / v0101 check · 桌機 2026-10-29 01:33 ship 後仍缺)。缺了它,v0249「發布層接進主流程與 U/I」 一載入就
FileNotFoundError,VRN-2 薄尾鏈(ChainShip check MISSING)與 VCGC 流程閘(VRN 列)雙紅,連 VDF 的 CI 也被擋。

本檔不宣稱原 v0248 的內容:它是薄尾直通 —— 所有名稱交給前版 VRN_SystemManager_v0245.py,只讓鏈接得起來;
原檔若日後在別處找到(ChainShip recover 會列 [FIND?] 同名不同內容),交人判斷,不自動覆寫。
操作員 2026-10-29 令:「將所有相關未修復衝突全部修復完 結案」。
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

# [VIA:ACCEL-BRIDGE:v0111] The original manager executes its accelerator bridge.
HERE = Path(__file__).resolve().parent
TAG = "v0248"
DISPLAY_NAME = "VRN-2 SystemManager"
PRIOR_NAME = "VRN_SystemManager_v0245.py"
BRIDGE = True                       # 補環,不是原檔
PRIOR_PATH = HERE / PRIOR_NAME
if not PRIOR_PATH.exists():
    raise FileNotFoundError("前版 %s 不在 · v0248(補環)不接" % PRIOR_NAME)
_spec = importlib.util.spec_from_file_location("vrn_manager_prior_for_v0248", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _name, _value in vars(PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def __getattr__(name):
    return getattr(PRIOR, name)


# ===== Headers V3(桌機線 v0248 的東西 · 正本是桌機的 SSOT 冊,不在倉)=====
# 桌機線交接 VRN2_Handover_v0145 §5:「Headers V3(v0248):欄序固定;程式鍵不變,介面 / 匯出用 Formal English Title Case
# (SSOT\VRN2_BasicInfo_Headers_v0100.json · VRN2_BasicInfo_latest_formal.csv)」—— 固定 16 欄 + 7 項 × 三年 + 標註欄 + STATUS = 39 鍵(+ SOURCE = 40 欄)。
# v0254 的 _write_formal_csv_40 讀 globals()["HEADERS_V3"](每筆 (程式鍵, 英文欄名, 其他))。本補環只從那本冊讀,讀不到就空
# (→ v0254 印「正式 CSV 0 欄」,不寫 _formal.csv);不在這裡手編 39 欄的規格。
HEADERS_BOOK = HERE / "SSOT" / "VRN2_BasicInfo_Headers_v0100.json"


def _headers_v3_from_book(path: Path) -> list:
    """接受幾種常見寫法:[[key, title, …], …] · [{"key"/"program"/"name": …, "title"/"en"/"formal": …}, …] · {"headers": [...]} · {key: title}。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:  # noqa: BLE001 — 冊不在 / 壞掉 = 沒有規格
        return []
    if isinstance(data, dict):
        for holder in ("headers", "HEADERS_V3", "columns", "items"):
            if isinstance(data.get(holder), list):
                data = data[holder]
                break
        else:
            return [(str(k), str(v) if not isinstance(v, dict) else str(v.get("title") or v.get("en") or k), "") for k, v in data.items() if not str(k).startswith("_")]
    rows = []
    for item in data if isinstance(data, list) else []:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            rows.append((str(item[0]), str(item[1]), item[2] if len(item) > 2 else ""))
        elif isinstance(item, dict):
            key = item.get("key") or item.get("program") or item.get("name") or item.get("KEY")
            title = item.get("title") or item.get("en") or item.get("formal") or item.get("english") or key
            if key:
                rows.append((str(key), str(title), item.get("type") or item.get("group") or ""))
    return rows


HEADERS_V3 = _headers_v3_from_book(HEADERS_BOOK)


def selftest() -> int:
    checks = [("前版在位", PRIOR_PATH.exists()), ("前版 TAG", getattr(PRIOR, "TAG", "") == "v0245"),
              ("_out_books 直通", callable(getattr(PRIOR, "_out_books", None))), ("completion 直通", callable(getattr(PRIOR, "completion", None))),
              ("main 直通", callable(getattr(PRIOR, "main", None))), ("本檔是補環", BRIDGE is True),
              ("Headers V3 只從冊讀(冊 %s · %d 鍵)" % ("在" if HEADERS_BOOK.is_file() else "不在倉 · 空", len(HEADERS_V3)), isinstance(HEADERS_V3, list) and (HEADERS_V3 == [] or all(len(row) == 3 for row in HEADERS_V3)))]
    import tempfile
    tmp = Path(tempfile.mkdtemp()) / "h.json"
    tmp.write_text(json.dumps({"headers": [["TICKER", "Ticker"], {"key": "RATING", "title": "Rating", "group": "fixed"}]}), encoding="utf-8")
    checks.append(("Headers V3 讀冊(兩種寫法)", _headers_v3_from_book(tmp) == [("TICKER", "Ticker", ""), ("RATING", "Rating", "fixed")] and _headers_v3_from_book(tmp.with_name("none.json")) == []))
    bad = [name for name, ok in checks if not ok]
    print("[計] VRN-2 SystemManager v0248(補環 · 直通 v0245)自測 %d/%d · %s" % (len(checks) - len(bad), len(checks), "PASS" if not bad else "FAIL " + ",".join(bad)))
    return 0 if not bad else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)


if __name__ == "__main__":
    sys.exit(main())
