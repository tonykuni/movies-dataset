#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN-2 SystemManager v0253 — 補環(reconstruction bridge · 2026-10-29 · 直通前版 v0249)。

原 v0253(v0254「收尾規格 · 剔除冊二次回查」的釘名前版)從未進倉:倉內任何分支與 zip、桌機的 functional modules\\VRN 都沒有
(VRN2_ChainShip v0100 / v0101 check · 桌機 2026-10-29 01:33 ship 後仍缺)。缺了它,v0254「收尾規格 · 剔除冊二次回查」 一載入就
FileNotFoundError,VRN-2 薄尾鏈(ChainShip check MISSING)與 VCGC 流程閘(VRN 列)雙紅,連 VDF 的 CI 也被擋。

本檔不宣稱原 v0253 的內容:它是薄尾直通 —— 所有名稱交給前版 VRN_SystemManager_v0249.py,只讓鏈接得起來;
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
TAG = "v0253"
DISPLAY_NAME = "VRN-2 SystemManager"
PRIOR_NAME = "VRN_SystemManager_v0249.py"
BRIDGE = True                       # 補環,不是原檔
PRIOR_PATH = HERE / PRIOR_NAME
if not PRIOR_PATH.exists():
    raise FileNotFoundError("前版 %s 不在 · v0253(補環)不接" % PRIOR_NAME)
_spec = importlib.util.spec_from_file_location("vrn_manager_prior_for_v0253", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _name, _value in vars(PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def __getattr__(name):
    return getattr(PRIOR, name)


# ===== v0254 從原 v0253 接來的六個名稱(原檔遺失 · 依 v0254 的呼叫處還原最小語意;不宣稱與原檔相同)=====
# v0254 _out_books:na = _fill_analyst(basic, acc) · nf = _fin_v2_shape(fin) · ns = _summ_status(summ) → 印「v0253 補位:分析師回填 na · 年度數據 V2 欄位補 nf 列 · 摘要 STATUS ns」
# v0254 second_chance:_blank(b.get(fld)) → 空才回填 · _status_append(b, "欄:理由")
# v0254 _out_books:line, _ = blank_audit(basic, fin, summ, market, od, gaps) → 印「[計] v0254 <line>」
_BLANK_TOKENS = {"", "-", "—", "–", "n.a.", "n/a", "na", "nan", "none", "null", "n.m.", "nm"}


def _blank(value) -> bool:
    """空值記號(None · 空白 · - · n.a. · nan …)= 空。數字 0 不是空。"""
    if value is None:
        return True
    text = str(value).strip().lower()
    return text in _BLANK_TOKENS


def _status_append(row: dict, text: str) -> None:
    """把一段狀態文字接到 row['STATUS'](以 · 分隔 · 不重複)。"""
    current = str(row.get("STATUS") or "").strip()
    if text and text not in current:
        row["STATUS"] = (current + " · " + text) if current else text
    elif "STATUS" not in row:
        row["STATUS"] = current


def _acc_analyst(entry) -> str:
    """從一筆驗收紀錄裡找分析師名(幾種可能的擺法 · 找不到回空字串)。"""
    if not isinstance(entry, dict):
        return ""
    for key in ("ANALYST", "analyst"):
        if not _blank(entry.get(key)):
            return str(entry[key]).strip()
    for holder in ("basic", "basic_info", "fields", "p1", "first_page"):
        inner = entry.get(holder)
        if isinstance(inner, dict):
            for key in ("ANALYST", "analyst"):
                if not _blank(inner.get(key)):
                    return str(inner[key]).strip()
    return ""


def _fill_analyst(basic: list, acc) -> int:
    """基本資料列 ANALYST 空白 → 用同一份的驗收紀錄回填(標 STATUS)。回填幾列。"""
    by_file = {}
    for entry in (acc or []):
        if isinstance(entry, dict):
            name = str(entry.get("file") or entry.get("FILENAME") or "")
            if name:
                by_file[name] = entry
    filled = 0
    for row in basic or []:
        if not isinstance(row, dict) or not _blank(row.get("ANALYST")):
            continue
        found = _acc_analyst(by_file.get(str(row.get("FILENAME") or "")))
        if found:
            row["ANALYST"] = found
            _status_append(row, "ANALYST:補位(驗收紀錄)")
            filled += 1
    return filled


_FIN_V2_KEYS = ("SUBCOL", "VERIFY", "NOTE")


def _fin_v2_shape(fin: list) -> int:
    """年度數據列補齊 V2 欄位(SUBCOL · VERIFY · NOTE;v0254 _mk_fin 的形狀)。回補了幾列。"""
    touched = 0
    for row in fin or []:
        if not isinstance(row, dict):
            continue
        missing = [key for key in _FIN_V2_KEYS if key not in row]
        for key in missing:
            row[key] = ""
        touched += 1 if missing else 0
    return touched


def _summ_status(summ: list) -> int:
    """摘要列補 STATUS 欄(沒有才補 · 空字串)。回補了幾列。"""
    added = 0
    for row in summ or []:
        if isinstance(row, dict) and "STATUS" not in row:
            row["STATUS"] = ""
            added += 1
    return added


_AUDIT_FIELDS = {"basic": ("TICKER", "BROKER", "REPORT_DATE", "TARGET_PRICE", "CURRENT_PRICE_REPORT", "UPSIDE_PCT", "RATING", "ANALYST"),
                 "fin": ("ITEM", "PERIOD", "VALUE"), "summ": ("TITLE", "POINT_1", "POINT_2", "POINT_3", "POINT_4")}


def blank_audit(basic: list, fin: list, summ: list, market, od, gaps) -> tuple:
    """三本冊的空格稽核(只數 · 不改值)→ (一行文字, 稽核 dict);寫 <od>/VRN2_BlankAudit_latest.json。"""
    def count(rows, fields):
        cells = {field: 0 for field in fields}
        for row in rows or []:
            if isinstance(row, dict):
                for field in fields:
                    if _blank(row.get(field)):
                        cells[field] += 1
        return cells
    audit = {"manager": "VRN-2 SystemManager v0253(補環)", "basic": count(basic, _AUDIT_FIELDS["basic"]), "fin": count(fin, _AUDIT_FIELDS["fin"]), "summ": count(summ, _AUDIT_FIELDS["summ"]),
             "rows": {"basic": len(basic or []), "fin": len(fin or []), "summ": len(summ or [])}, "market_rows": len(market) if isinstance(market, (dict, list)) else 0, "gaps": len(gaps or []) if isinstance(gaps, (list, dict)) else 0}
    try:
        Path(od).mkdir(parents=True, exist_ok=True)
        (Path(od) / "VRN2_BlankAudit_latest.json").write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:  # noqa: BLE001 — 稽核寫不進去不擋收尾
        pass
    line = "空格稽核 · 基本資料 %d 格(%s)· 年度數據 %d 格 · 摘要 %d 格 · 缺項 %d → VRN2_BlankAudit_latest.json" % (
        sum(audit["basic"].values()), " ".join("%s %d" % (k, v) for k, v in audit["basic"].items() if v) or "無", sum(audit["fin"].values()), sum(audit["summ"].values()), audit["gaps"])
    return line, audit


def selftest() -> int:
    checks = [("前版在位", PRIOR_PATH.exists()), ("前版 TAG", getattr(PRIOR, "TAG", "") == "v0249"),
              ("_out_books 直通", callable(getattr(PRIOR, "_out_books", None))), ("completion 直通", callable(getattr(PRIOR, "completion", None))),
              ("main 直通", callable(getattr(PRIOR, "main", None))), ("本檔是補環", BRIDGE is True)]
    import tempfile
    row = {"FILENAME": "a.pdf", "ANALYST": "", "UPSIDE_PCT": "", "STATUS": ""}
    n = _fill_analyst([row], [{"file": "a.pdf", "basic": {"ANALYST": "Lucas Liu"}}])
    _status_append(row, "UPSIDE_PCT:推算"); _status_append(row, "UPSIDE_PCT:推算")
    fin = [{"ITEM": "Revenue", "PERIOD": "2025E", "VALUE": "1"}]; summ = [{"TITLE": "t"}]
    od = Path(tempfile.mkdtemp())
    line, audit = blank_audit([row], fin, summ, {}, od, [])
    checks += [("_blank", _blank(None) and _blank(" ") and _blank("n.a.") and not _blank(0) and not _blank("18.8")),
               ("_fill_analyst 回填 + STATUS", n == 1 and row["ANALYST"] == "Lucas Liu" and "ANALYST:補位" in row["STATUS"]),
               ("_status_append 不重複", row["STATUS"].count("UPSIDE_PCT:推算") == 1),
               ("_fin_v2_shape / _summ_status", _fin_v2_shape(fin) == 1 and fin[0]["SUBCOL"] == "" and _summ_status(summ) == 1 and summ[0]["STATUS"] == ""),
               ("blank_audit 一行 + json", "空格稽核" in line and (od / "VRN2_BlankAudit_latest.json").is_file() and audit["rows"]["fin"] == 1)]
    bad = [name for name, ok in checks if not ok]
    print("[計] VRN-2 SystemManager v0253(補環 · 直通 v0249)自測 %d/%d · %s" % (len(checks) - len(bad), len(checks), "PASS" if not bad else "FAIL " + ",".join(bad)))
    return 0 if not bad else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)


if __name__ == "__main__":
    sys.exit(main())
