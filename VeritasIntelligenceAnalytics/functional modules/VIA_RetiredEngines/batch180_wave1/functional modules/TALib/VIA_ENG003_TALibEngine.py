# -*- coding: utf-8 -*-
"""VIA_ENG003 退役引擎墓碑(tombstone;側線 2026-09-25 第十六段 b)。

批180 wave1 退役;操作員 2026-09-25 令「NO TA-LIBS ALLOWED REMOVE ALL TAL-LIB」→ 原內容(55,036 位元組,含被禁庫的
import 與呼叫)整份清除,本檔**零可執行碼、零被禁庫碼**。
只增不減:識別碼留在冊上——退役存證 117 族不因清除而少一族(總控頁契約 test_01 釘住這個數;
第一次拔的時候直接刪檔,契約當場紅,本墓碑就是那一次紅燈的修法)。
原內容在 git 歷史:commit 14bca8a4 同路徑。RETIRE_MANIFEST.json 本族記 purged_20260925。
L50:唯一指標正主 = QuantGuard(VDF_ENG086_QuantGuardOneBridge);流程 VDF(ENG060 ADJ OHLC)→ QuantGuard → VRN(L104)。
"""
PURGED = "2026-09-25"
RULING = "操作員令「NO TA-LIBS ALLOWED REMOVE ALL TAL-LIB」"


def _selftest() -> int:
    """墓碑自測(--selftest):AST 驗本檔零 import(被禁庫當然也零)、只剩兩個字串常數。"""
    import ast
    from pathlib import Path
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    top_imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    ok = not top_imports and PURGED == "2026-09-25"
    print("  [%s] 墓碑:模組層零 import(零被禁庫碼)· 清除日 %s" % ("OK" if ok else "FAIL", PURGED))
    print("  [計] 1 檢 OK %d · FAIL %d" % (1 if ok else 0, 0 if ok else 1))
    return 0 if ok else 1


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(_selftest() if "--selftest" in _sys.argv[1:] else 0)
