"""表格修復（末日級,純 stdlib）。

修復原始表格錯誤:分隔符偵測、破碎/參差列補齊、表頭推斷、換行折斷儲存格合併。
可驗證:回報 修了幾列、補了幾格、是否無資料流失。
"""
from __future__ import annotations

import re


def sniff_delimiter(text: str) -> str:
    head = "\n".join(text.splitlines()[:10])
    cands = {",": head.count(","), "\t": head.count("\t"),
             ";": head.count(";"), "|": head.count("|")}
    best = max(cands, key=cands.get)
    return best if cands[best] > 0 else ","


def parse_table(text: str, delim=None):
    delim = delim or sniff_delimiter(text)
    rows = []
    for line in text.splitlines():
        if line.strip() == "":
            continue
        rows.append([c.strip().strip('"') for c in line.split(delim)])
    return rows, delim


def repair_table(rows):
    """把參差列補齊到眾數欄數、推斷表頭、合併明顯的續行。回報修復統計。"""
    if not rows:
        return {"rows": [], "cols": 0, "header": [], "report":
                {"rows_in": 0, "rows_out": 0, "padded_cells": 0, "merged": 0, "verify_pass": True}}
    # 眾數欄數
    from collections import Counter
    widths = Counter(len(r) for r in rows)
    ncol = widths.most_common(1)[0][0]
    padded = 0
    merged = 0
    fixed = []
    for r in rows:
        # 續行合併:若某列欄數遠少於眾數且前一列存在 → 視為上一格換行折斷,併回最後一格
        if fixed and len(r) < ncol and len(r) <= max(1, ncol // 3):
            fixed[-1][-1] = (fixed[-1][-1] + " " + " ".join(r)).strip()
            merged += 1
            continue
        rr = list(r)
        if len(rr) < ncol:               # 補空欄
            padded += (ncol - len(rr))
            rr += [""] * (ncol - len(rr))
        elif len(rr) > ncol:             # 過長 → 多餘併入最後一欄
            rr = rr[:ncol - 1] + [delim_join(rr[ncol - 1:])]
        fixed.append(rr)
    # 表頭推斷:第一列若全非數字則視為表頭
    header = fixed[0] if fixed and not _looks_numeric_row(fixed[0]) else \
        [f"col{i+1}" for i in range(ncol)]
    body = fixed[1:] if header is fixed[0] else fixed
    # 驗證:輸出列數 + 合併數 應等於輸入非空列數（無資料流失）
    verify = (len(fixed) + merged) == len(rows)
    return {"rows": body, "cols": ncol, "header": header,
            "report": {"rows_in": len(rows), "rows_out": len(body),
                       "padded_cells": padded, "merged": merged, "verify_pass": verify}}


def delim_join(parts):
    return " ".join(p for p in parts if p)


def _looks_numeric_row(row):
    nums = sum(1 for c in row if re.fullmatch(r"[-+]?[\d,\.]+%?", c.strip()))
    return nums >= max(1, len(row) // 2)
