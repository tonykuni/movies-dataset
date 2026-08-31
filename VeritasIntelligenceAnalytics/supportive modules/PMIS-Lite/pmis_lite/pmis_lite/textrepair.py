"""文字修復/簡化層（針對郵件等長文）。

目標：保留完整資訊，但去掉雜訊讓人/系統好讀：
  - 剝除回信引用尾巴（> 引文、On ... wrote:、寄件者:…）
  - 剝除簽名檔與免責聲明
  - 正規化空白/全形空格

保守原則：只切「明確的尾巴」，主體一字不刪 —— 避免誤刪真內容。
回傳 (cleaned, removed_blocks) 讓你能驗證刪了什麼。
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

import re

# 回信引用分隔線（中英）
_REPLY_MARKERS = [
    r"^-{2,}\s*Original Message\s*-{2,}",
    r"^On .+ wrote:$",
    r"^寄件者[:：]",
    r"^From[:：]",
    r"^發件人[:：]",
    r"^________+$",
    r"^>{1,}.*",                       # 引用行
]
# 簽名/免責聲明起點
_SIG_MARKERS = [
    r"^--\s*$",
    r"^Best Regards[,，]?",
    r"^Regards[,，]?",
    r"^敬祝",
    r"^此致",
    r"^本郵件.*機密",
    r"^This e-?mail.*confidential",
    r"^免責聲明",
    r"^Disclaimer",
]

_reply_re = re.compile("|".join(_REPLY_MARKERS), re.IGNORECASE | re.MULTILINE)
_sig_re = re.compile("|".join(_SIG_MARKERS), re.IGNORECASE | re.MULTILINE)


def clean_email_text(text: str) -> tuple[str, list[str]]:
    if not text:
        return "", []
    removed = []

    # 找最早出現的「尾巴」起點（引用 or 簽名），其後全切
    cut = len(text)
    for rx in (_reply_re, _sig_re):
        m = rx.search(text)
        if m and m.start() < cut:
            cut = m.start()

    head = text[:cut]
    tail = text[cut:]
    if tail.strip():
        removed.append(tail.strip()[:200])

    # 正規化空白
    head = head.replace("\u3000", " ")
    head = re.sub(r"[ \t]+", " ", head)
    head = re.sub(r"\n{3,}", "\n\n", head).strip()
    return head, removed
