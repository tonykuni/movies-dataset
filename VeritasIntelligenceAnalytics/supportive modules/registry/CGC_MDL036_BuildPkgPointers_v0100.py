# -*- coding: utf-8 -*-
"""build_pkg_pointers_v0100.py — 商品指針產生器(操作員商品化令;FlowSystem 先不列入)。

每商品一指針 PKG_###_Pointer.json:內容物 path+sha256(現有代碼舉證)、install 規約
(PS7+/python/pip/bin 動詞)、shared_supportive 共用族(組合安裝去重)、
base=C:\\VeritasIntelligenceAnalytics、first_page 規約。只增不減 — 重跑=重生指針(版本前進)。
"""
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
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = HERE / "pkg_pointers"

SKIP_DIRS = {"__pycache__", "node_modules", ".git", "temp", "qa_work", "_generated", "runs"}
SKIP_SUFF = {".pyc", ".duckdb", ".sqlite"}
MAX_MB = 60

# 商品定義(FlowSystem=PKG-005 既有,操作員令先不列入本波)
PRODUCTS = [
    ("PKG-009", "WorkOps 母版(郵件×專案治理+指揮板)", "functional modules/WorkOps",
     ["治理/登錄", "執行入口"], ["via-workops", "via-boardqa", "via-usertest"], [],
     "Invoke-VIA-WorkOps-CommandBoard-v0132.ps1 產 board;紅線:絕不代寄 .Send()"),
    ("PKG-010", "VAP 繪圖(chartlib+seaborn/plotly 雙線+SSOT)", "functional modules/VAP",
     ["治理/登錄", "執行入口"], ["via-vap", "via-plot"],
     ["seaborn", "plotly", "pandas", "duckdb", "pyarrow"],
     "ui/VAP_Workbench_v010.html;28 圖型 SSOT vap_chartlib.json"),
    ("PKG-011", "VRN 研報萃取治理(OCR/表格還原/交叉驗證)", "functional modules/VRN",
     ["治理/登錄", "執行入口", "規則庫"], ["via-batch", "via-shim", "via-probe", "via-extract", "via-ocr"],
     ["pandas"],
     "OCR 重依賴(paddleocr/surya)依 VRN_Production_README 另裝;執行端在工作站"),
    ("PKG-012", "VDF 資料鍛造(取數契約 SSOT+intake)", "functional modules/VDF",
     ["治理/登錄", "執行入口"], ["via-vdf"],
     ["pandas", "pyarrow", "duckdb", "yfinance", "plotly", "rich"],
     "誠實註記:README 21 模組庫內缺 11+v0160 三本體候上傳 — 指針僅舉證在庫者"),
    ("PKG-013", "ChipWar 晶片戰情指標族", "functional modules/ChipWar",
     ["治理/登錄", "執行入口"], ["via-wf"], ["pandas"],
     "12 引擎;harness L1/L2 全綠存證"),
    ("PKG-014", "MultiFactor 多因子驗證模擬", "functional modules/MultiFactor",
     ["治理/登錄", "執行入口"], ["via-wf"], ["pandas", "numpy"],
     "test v0101 動態路徑"),
    ("PKG-015", "TALib 技術指標 64 式", "functional modules/TALib",
     ["治理/登錄", "執行入口"], ["via-wf"], ["pandas", "numpy"],
     "adj 鐵律:一律用還原價"),
]


def walk(root: Path):
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in SKIP_SUFF:
            continue
        if p.stat().st_size > MAX_MB * 1024 * 1024:
            yield p, None  # 超大檔:列名不 hash(誠實標 SKIP_LARGE)
            continue
        yield p, hashlib.sha256(p.read_bytes()).hexdigest()


def build():
    OUT.mkdir(exist_ok=True)
    summary = []
    for code, name, rel, shared, verbs, pip, note in PRODUCTS:
        root = VIA / rel
        if not root.exists():
            print("[FAIL]", code, rel, "不在位")
            continue
        contents = []
        for p, sha in walk(root):
            contents.append({"path": str(p.relative_to(VIA)),
                             "sha256": sha or "SKIP_LARGE",
                             "bytes": p.stat().st_size})
        ptr = {
            "pkg_code": code, "name": name, "version": "v0100",
            "generated": "2026-08-12", "subsystem_root": rel,
            "base": "C:\\VeritasIntelligenceAnalytics",
            "contents_n": len(contents),
            "contents_bytes": sum(c["bytes"] for c in contents),
            "shared_supportive": shared,
            "install": {"ps_min": "7.0", "python_min": "3.10",
                        "pip": pip, "bin_verbs": verbs,
                        "installer": "Install-VIA-Product-v0100.ps1 -Pointer <本檔>"},
            "ui_contract": {"first_page": "設定+輸入現況+輸入前檢查+運作結果",
                            "matrix_pages": "分類矩陣", "docs_pages": "末尾可隱藏"},
            "precheck": ["重複輸入", "缺欄", "路徑不存在"],
            "note": note,
            "contents": contents,
        }
        out = OUT / ("%s_Pointer.json" % code.replace("-", "_"))
        out.write_text(json.dumps(ptr, ensure_ascii=False, indent=1), encoding="utf-8")
        summary.append((code, name, len(contents), ptr["contents_bytes"] // 1024))
        print("[OK  ] %s %s → %d 件 %d KB" % (code, name, len(contents),
                                              ptr["contents_bytes"] // 1024))
    print("-" * 60)
    print("指針 %d 件 → %s" % (len(summary), OUT))
    return 0 if len(summary) == len(PRODUCTS) else 1


if __name__ == "__main__":
    sys.exit(build())
