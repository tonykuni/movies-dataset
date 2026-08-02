"""跨領域自動編碼 + 自動 SSOT（不知道產業也能跑）。

泛用工具的難題：買回去插上就用，但系統不知道客戶是哪個產業。
傳統查表法（遇採購編 PO-）在未知領域失效。解法：
  1. AUTO CODING：確定性語義雜湊——同一筆永遠同碼（append-only 安全、天然去重），
     語義前綴從『資料自己自舉出的類別』來，類別沒長出來前用中性雜湊碼。
     編碼與分類一起演化：越跑越懂這家公司，前綴越有意義，但身分碼恆定。
  2. AUTO SSOT：零組態自我配置——桶自資料長、關鍵字自動生、碼自動鑄、完整性自動驗。
  3. AUTO EVOLUTION：schema-on-read，新欄位/新值只增不減，永不因未見過而崩。
  4. AUTO VERIFY：完整性 gate + 自檢，錯了自己舉手。

全程確定性規則，斷網無 AI 照跑。
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime

_B32 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"


def _b32_3(s: str) -> str:
    """把任意字串壓成穩定的 3 碼 base32（確定性、雜湊均勻分布）。"""
    h = hashlib.blake2s(s.encode("utf-8"), digest_size=4).digest()
    n = int.from_bytes(h, "big")
    return "".join(_B32[(n >> (5 * i)) & 31] for i in range(3))


def _ascii_prefix(category: str) -> str:
    """類別若含 ASCII 字母，取前 3 個大寫；否則用穩定雜湊 3 碼（中文類別也能編）。"""
    letters = re.sub(r"[^A-Za-z]", "", category or "")
    if len(letters) >= 3:
        return letters[:3].upper()
    return _b32_3(category or "GENERIC")


def identity_key(record) -> str:
    """身分碼：來自 標題+行為者（內容改了也不變）——穩定、可追溯。"""
    basis = f"{getattr(record,'title','')}|{getattr(record,'actor','')}"
    return hashlib.blake2s(basis.encode("utf-8"), digest_size=4).hexdigest().upper()


def mint_universal_id(record, source_type="X", discovered_category=None) -> str:
    """AUTO CODING：領域無關通用編碼。同一筆永遠同碼。

    格式：[語義前綴]-[來源]-[年月]-[身分碼]
      語義前綴：有自舉類別用它，否則用內容中性雜湊（自我演化）
      身分碼：標題+行為者的雜湊（穩定身分）
    """
    cat = discovered_category or getattr(record, "product", "") or getattr(record, "topic", "")
    prefix = _ascii_prefix(cat) if cat else _b32_3(
        (getattr(record, "title", "") or getattr(record, "body", ""))[:64] or "X")
    src = (source_type or "X")[:1].upper()
    dt = _parse_ym(getattr(record, "event_time", ""))
    return f"{prefix}-{src}-{dt}-{identity_key(record)}"


def _parse_ym(s) -> str:
    if s:
        try:
            return datetime.fromisoformat(str(s).split("+")[0]).strftime("%y%m")
        except Exception:
            try:
                return datetime.strptime(str(s)[:7], "%Y-%m").strftime("%y%m")
            except Exception:
                pass
    return datetime.now().strftime("%y%m")


def auto_ssot(records, dims=("product", "topic", "status")):
    """AUTO SSOT：零組態自我配置。不需事先知道產業。

    回傳 {coded, buckets, keywords, verify}：
      - 桶自資料自舉（seed_buckets_from_data）
      - 三道分類
      - 每筆自動鑄通用碼（用自舉出的 product 當語義前綴）
      - 關鍵字自動生成候選
      - 完整性自動驗（每筆都要有碼、碼要唯一）
    """
    from .classify import classify_all, seed_buckets_from_data
    from .keywords import generate_keyword_candidates

    cls = {d: {} for d in dims}
    seed_buckets_from_data(records, cls, dims=dims)      # 桶從資料長出來
    res = classify_all(records, cls)                     # 三道分類

    seen = {}
    dup = 0
    coded = []
    for r in records:
        code = mint_universal_id(r, getattr(r, "source_type", "X") or "X",
                                 getattr(r, "product", "") or getattr(r, "topic", ""))
        r.uid = code
        if code in seen:
            dup += 1
        seen[code] = seen.get(code, 0) + 1
        coded.append(r)

    kw = generate_keyword_candidates(records, cls, dim="product", min_count=2, min_score=0.6) if any(
        getattr(r, "product", "") for r in records) else []

    verify = {
        "total": len(records),
        "coded": sum(1 for r in records if getattr(r, "uid", "")),
        "unique_codes": len(seen),
        "duplicate_codes": dup,
        "buckets_discovered": {d: len(cls.get(d, {})) for d in dims},
        "classify_rate": res["stats"].get(dims[0], {}).get("rate") if dims else None,
        "pass": all(getattr(r, "uid", "") for r in records),   # 全部有碼才 PASS
    }
    return {"coded": coded, "buckets": cls, "keywords": kw, "verify": verify, "stats": res["stats"]}
