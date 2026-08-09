"""rule_id 註冊表。

每一筆 Patch 都必須引用一個已註冊的 rule_id。這條約束的目的不是形式主義：

1. rule_id 是人工複核時唯一能批次裁決的鍵（「接受全部 12 筆 fullwidth_ascii」）。
2. Python 版與 JavaScript 版對同一規則必須使用同一 rule_id，才能交叉驗證。
3. 沒有註冊表，規則命名會隨著實作漂移，patch log 的歷史查詢就會斷。

新增規則時**必須同時**更新 `@dg-in/vtr-js` 的 `rules/registry.ts`；CI 比對兩邊。
"""

from __future__ import annotations

import re
from typing import NamedTuple

RULE_ID_RE = re.compile(r"^VTR\.[A-Z_]+\.[a-z0-9_]+$")


class Rule(NamedTuple):
    rule_id: str
    stage: str
    summary: str
    #: 兩版引擎都必須實作；False 代表僅 Python 版（模型層）。
    cross_engine: bool = True


_RULES: tuple[Rule, ...] = (
    # -- 步驟 1：語言偵測（不改文字，因此不產生 patch，僅登錄供量測引用）------ #
    Rule("VTR.LANG_DETECT.script_run", "LANG_DETECT",
         "script run 切分與 lang 判定（annotation only，不產生文字 patch）"),

    # -- 步驟 2：正規化 ------------------------------------------------------ #
    Rule("VTR.NORMALIZE.nfkc", "NORMALIZE",
         "Unicode NFKC；刻意跳過 CJK 標點，避免全形標點被拉成 ASCII"),
    Rule("VTR.NORMALIZE.fullwidth_ascii", "NORMALIZE",
         "全形英數 → 半形"),
    Rule("VTR.NORMALIZE.cjk_punct", "NORMALIZE",
         "CJK 語境中的半形標點 → 全形"),
    Rule("VTR.NORMALIZE.opencc_s2twp", "NORMALIZE",
         "簡體 → 台灣正體（含用語轉換）；opencc 未安裝時降級並標記"),
    Rule("VTR.NORMALIZE.whitespace", "NORMALIZE",
         "空白正規化：CJK 之間移除、CJK–Latin 邊界單一空白、行首行尾修剪"),
    Rule("VTR.NORMALIZE.filler_mark", "NORMALIZE",
         "ASR 語助詞：提出刪除建議但不自動套用（一律 review）"),

    # -- P0：保護遮罩 -------------------------------------------------------- #
    Rule("VTR.PROTECT.pattern_url", "PROTECT", "URL 遮罩"),
    Rule("VTR.PROTECT.pattern_email", "PROTECT", "Email 遮罩"),
    Rule("VTR.PROTECT.pattern_timestamp", "PROTECT", "時間碼遮罩"),
    Rule("VTR.PROTECT.pattern_part_number", "PROTECT",
         "料號 / 版本碼遮罩（未知料號同時標記 unresolved_entity，不猜測）"),
    Rule("VTR.PROTECT.pattern_code_ident", "PROTECT",
         "CamelCase 識別字遮罩（VeritasAutoPlot 這類專名的第一道防線）"),
    Rule("VTR.PROTECT.pattern_number_unit", "PROTECT", "數量＋單位遮罩"),
    Rule("VTR.PROTECT.lexicon_exact", "PROTECT",
         "SSOT Lexicon 精確命中遮罩（待 LEXICON 模組接上）"),
    Rule("VTR.UNPROTECT.restore", "UNPROTECT",
         "sentinel 還原成 canonical 形式"),
    Rule("VTR.PROTECT.sentinel_violation", "PROTECT",
         "sentinel 完整性違反 —— 該 Stage 全部 patch 回退"),
)

RULE_REGISTRY: dict[str, Rule] = {r.rule_id: r for r in _RULES}


class UnknownRuleError(KeyError):
    """使用了未註冊的 rule_id。"""


def require(rule_id: str, stage: str | None = None) -> Rule:
    """取用規則；未註冊或與 stage 不符即拋錯。"""
    if not RULE_ID_RE.match(rule_id):
        raise UnknownRuleError(
            f"rule_id 格式不合法: {rule_id!r}（應為 VTR.<STAGE>.<rule>）")
    rule = RULE_REGISTRY.get(rule_id)
    if rule is None:
        raise UnknownRuleError(
            f"未註冊的 rule_id: {rule_id!r}。新增規則必須同時登錄於 "
            "vtr_py/rules.py 與 vtr-js/rules/registry.ts。")
    if stage is not None and rule.stage != stage:
        raise UnknownRuleError(
            f"{rule_id!r} 屬於 {rule.stage}，不得由 {stage} 產生")
    return rule


def cross_engine_rule_ids() -> list[str]:
    """兩版引擎都必須實作的規則；CI 用來比對 JS 版註冊表。"""
    return sorted(r.rule_id for r in _RULES if r.cross_engine)
