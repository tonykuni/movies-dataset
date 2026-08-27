"""治亂碼層。

台灣的 Excel/CSV 匯出常見 utf-8 / utf-8-sig(BOM) / big5 / cp950 混雜，
一不小心就整片亂碼。這層負責：
  1. 偵測檔案編碼（chardet + 常見編碼回退）
  2. 對已讀進來的字串做 mojibake（雙重解碼亂碼）修復嘗試
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

# 台灣環境最常見的編碼，依序嘗試
_FALLBACK_ENCODINGS = ["utf-8-sig", "utf-8", "cp950", "big5", "gb18030", "latin-1"]


def detect_file_encoding(path: str) -> str:
    """偵測檔案編碼。先用 chardet，再用常見編碼實測回退。"""
    with open(path, "rb") as f:
        raw = f.read()

    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"

    try:
        import chardet
        guess = chardet.detect(raw)
        enc = (guess.get("encoding") or "").lower()
        conf = guess.get("confidence") or 0
        if enc and conf >= 0.7:
            # chardet 對中文有時把 cp950 認成 big5，統一用較寬的
            if enc in ("big5", "big5hkscs"):
                return "cp950"
            return enc
    except Exception:
        pass

    # 回退：哪個編碼能完整解碼就用哪個
    for enc in _FALLBACK_ENCODINGS:
        try:
            raw.decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "utf-8"


def repair_mojibake(text: str) -> str:
    """修復常見『雙重解碼』亂碼，例如 utf-8 被當成 latin-1/cp1252 讀進來。

    保守策略：修復後若中文字（CJK）變多才採用，否則保留原字串，避免越修越壞。
    """
    if not text:
        return text

    def cjk_count(s: str) -> int:
        return sum(1 for ch in s if "\u4e00" <= ch <= "\u9fff")

    best = text
    best_score = cjk_count(text)
    for wrong in ("latin-1", "cp1252"):
        for right in ("utf-8", "cp950"):
            try:
                candidate = text.encode(wrong, errors="strict").decode(right, errors="strict")
            except (UnicodeEncodeError, UnicodeDecodeError, LookupError):
                continue
            score = cjk_count(candidate)
            if score > best_score:
                best, best_score = candidate, score
    return best
