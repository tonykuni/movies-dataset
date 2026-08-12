"""superextract — Word/Excel/CSV text & table extractor with encoding
repair, validation and comparison (擷取 → 修復 → 驗證 → 對照).

Stdlib-only at its core; optional local free libraries (pandas, openpyxl,
python-docx, docx2python, ftfy, charset_normalizer, datacompy, xlrd,
msoffcrypto-tool) are auto-detected and upgrade the experience.

Quick start
-----------
    from superextract import extract_any, compare_files

    result = extract_any("contract.docx")      # extract + repair + validate
    print(result.text)
    for grid in result.tables:
        print(grid.to_markdown())
    for issue in result.issues:
        print(issue)

    report = compare_files("old.docx", "new.docx")   # 對照
"""
from .availability import doctor, doctor_text, has
from .compare import (compare_grids, compare_texts, crosscheck_docx,
                      pair_tables)
from .csv_extract import extract_csv
from .encoding import decode_bytes, detect_encoding, read_text_auto
from .excel_extract import extract_excel
from .pipeline import ExtractionResult, compare_files, extract_any
from .tableops import Grid, coerce_number, dedupe_headers
from .textclean import clean_text, fix_mojibake, normalize_for_compare
from .validate import Issue, validate_grid, validate_text
from .word_extract import ExtractionError, extract_docx

__version__ = "1.0.0"

__all__ = [
    "extract_any", "compare_files", "ExtractionResult",
    "extract_docx", "extract_excel", "extract_csv",
    "compare_texts", "compare_grids", "pair_tables", "crosscheck_docx",
    "clean_text", "fix_mojibake", "normalize_for_compare",
    "detect_encoding", "decode_bytes", "read_text_auto",
    "validate_grid", "validate_text", "Issue",
    "Grid", "dedupe_headers", "coerce_number",
    "ExtractionError", "doctor", "doctor_text", "has",
    "__version__",
]
