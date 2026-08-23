"""末日自檢（Doomsday Self-Check）——無網路、無 AI 也能跑的失敗偵測。

設計信條：這套系統在沒有網路、沒有任何 AI 服務的情況下，仍要能自己
『偵測出哪裡壞了、為什麼壞、有哪些解法』。所有檢查都是純 Python 規則，
不呼叫任何外部服務、不依賴任何模型——斷網斷電復電後第一件事就是跑它。

每個 Check 回傳 status(PASS/WARN/FAIL) + 證據 + 多元解法清單。
WARN = 有備援可降級運作；FAIL = 會影響正確性，需處理。
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

import importlib
import os
import shutil
import sys
from dataclasses import dataclass, field


@dataclass
class Check:
    name: str
    status: str            # PASS / WARN / FAIL
    detail: str = ""
    remedies: list = field(default_factory=list)


def _try_import(mod: str) -> bool:
    try:
        importlib.import_module(mod)
        return True
    except Exception:
        return False


def check_environment() -> list[Check]:
    """環境/相依檢查（永遠可跑，不需資料）。"""
    out = []

    # 1. Python 版本
    v = sys.version_info
    if v >= (3, 9):
        out.append(Check("Python 版本", "PASS", f"{v.major}.{v.minor}"))
    else:
        out.append(Check("Python 版本", "FAIL", f"{v.major}.{v.minor}",
                         ["升級至 Python 3.9+", "用 py -3.11/-3.12 啟動"]))

    # 2. 核心相依
    for mod, label in [("pandas", "表格核心"), ("openpyxl", "Excel")]:
        if _try_import(mod):
            out.append(Check(f"核心庫 {mod}", "PASS", label))
        else:
            out.append(Check(f"核心庫 {mod}", "FAIL", f"{label} 缺失",
                             [f"pip install {mod}", "用 START_Windows.bat 自動裝", "改用內建 csv 模組降級讀取"]))

    # 3. 選用相依（缺了走備援，不致命）
    optional = {"pdfplumber": "PDF 文字", "pytesseract": "OCR", "win32com": "Outlook COM",
                "pyarrow": "Parquet"}
    for mod, label in optional.items():
        if _try_import(mod):
            out.append(Check(f"選用庫 {mod}", "PASS", label))
        else:
            out.append(Check(f"選用庫 {mod}", "WARN", f"{label} 不可用（走備援）",
                             [f"需要時 pip install {mod}",
                              "PDF→改純文字附件", "OCR→標記需人工複核", "COM→改讀匯出檔", "Parquet→改 CSV 快照"]))

    # 4. 確認無強制網路相依（末日場景）
    out.append(Check("離線運作保證", "PASS",
                     "全流程為本機規則運算，不呼叫網路或 AI 服務"))
    return out


def check_io(config_path: str = "", store_dir: str = "", min_free_gb: float = 1.0) -> list[Check]:
    out = []
    # 5. 設定檔
    if config_path:
        if os.path.exists(config_path):
            try:
                import json
                with open(config_path, encoding="utf-8") as f:
                    cfg = json.load(f)
                missing = [k for k in ("classification",) if k not in cfg]
                if missing:
                    out.append(Check("設定檔結構", "WARN", f"缺 {missing}（用預設）",
                                     ["用 config_builder.html 重新產生", "引擎會套用泛用預設桶"]))
                else:
                    out.append(Check("設定檔", "PASS", config_path))
            except Exception as e:
                out.append(Check("設定檔解析", "FAIL", f"JSON 損壞: {e.__class__.__name__}",
                                 ["用 config_builder.html 重新產生", "刪除設定檔讓引擎走自動偵測"]))
        else:
            out.append(Check("設定檔", "WARN", "不存在（走自動偵測）",
                             ["執行 run_auto 會自動產生最小設定"]))

    # 6. 磁碟空間
    try:
        target = store_dir or "."
        free_gb = shutil.disk_usage(target).free / (1024 ** 3)
        if free_gb >= min_free_gb:
            out.append(Check("磁碟空間", "PASS", f"剩餘 {free_gb:.1f} GB"))
        else:
            out.append(Check("磁碟空間", "FAIL", f"僅剩 {free_gb:.1f} GB",
                             ["清理舊附件快取", "回收超期未鎖定暫存", "改指向大容量磁碟"]))
    except Exception:
        out.append(Check("磁碟空間", "WARN", "無法量測"))

    # 7. 輸出可寫
    if store_dir:
        try:
            os.makedirs(store_dir, exist_ok=True)
            probe = os.path.join(store_dir, ".write_probe")
            with open(probe, "w") as f:
                f.write("ok")
            os.remove(probe)
            out.append(Check("輸出目錄可寫", "PASS", store_dir))
        except Exception as e:
            out.append(Check("輸出目錄可寫", "FAIL", f"{e.__class__.__name__}",
                             ["改用有權限的資料夾", "以系統管理員身分執行"]))
    return out


def check_data(result: dict | None, min_classify_rate: float = 50.0) -> list[Check]:
    """資料品質檢查（有跑過 pipeline 才檢）。"""
    out = []
    if not result:
        return out
    records = result.get("records", [])

    # 8. 擷取非空
    if records:
        out.append(Check("擷取結果", "PASS", f"{len(records)} 筆事件"))
    else:
        out.append(Check("擷取結果", "FAIL", "0 筆",
                         ["確認來源路徑/權限", "檢查 adapter 是否對應到實際欄位", "看偵測查核報告"]))

    # 9. 完整性 gate
    audit = result.get("audit")
    if audit is not None:
        gap = getattr(audit, "unexplained_gap", None)
        if gap == 0:
            out.append(Check("完整性 gate", "PASS", "未解釋遺漏=0"))
        elif gap is not None:
            out.append(Check("完整性 gate", "FAIL", f"未解釋遺漏={gap}",
                             ["檢視失敗清單原因", "補對應 adapter 的型別支援", "標記不可救回者並人工確認"]))

    # 10. 歸類率
    cs = result.get("classify_stats", {}).get("product", {})
    rate = cs.get("rate")
    if rate is not None:
        if rate >= min_classify_rate:
            out.append(Check("歸類率", "PASS", f"{rate}%"))
        else:
            out.append(Check("歸類率", "WARN", f"{rate}%（偏低）",
                             ["核可自動生成的關鍵字候選", "確認分類桶已從資料長出", "啟用討論串傳播/模糊指派"]))

    # 11. 重複 UID 偵測
    uids = [r.uid for r in records]
    dup = len(uids) - len(set(uids))
    if dup == 0:
        out.append(Check("身分編號唯一性", "PASS", "無重複 UID"))
    else:
        out.append(Check("身分編號唯一性", "FAIL", f"{dup} 筆重複",
                         ["檢查 make_uid 的身分鍵", "確認 content_hash 輸入欄位"]))
    return out


def run_selfcheck(config_path: str = "", store_dir: str = "", result: dict | None = None) -> dict:
    checks = check_environment() + check_io(config_path, store_dir) + check_data(result)
    summary = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for c in checks:
        summary[c.status] = summary.get(c.status, 0) + 1
    overall = "FAIL" if summary["FAIL"] else ("WARN" if summary["WARN"] else "PASS")
    return {"overall": overall, "summary": summary, "checks": checks}


def selfcheck_markdown(report: dict) -> str:
    s = report["summary"]
    L = [f"# 末日自檢報告　總評：{report['overall']}",
         f"_PASS {s['PASS']} · WARN {s['WARN']} · FAIL {s['FAIL']} · 無網路/無 AI 純本機_\n",
         "| 檢查 | 狀態 | 證據 | 解法 |", "|---|---|---|---|"]
    icon = {"PASS": "✅", "WARN": "🟡", "FAIL": "🔴"}
    for c in report["checks"]:
        rem = "；".join(c.remedies) if c.remedies else "—"
        L.append(f"| {c.name} | {icon.get(c.status,'')}{c.status} | {c.detail} | {rem} |")
    return "\n".join(L)
