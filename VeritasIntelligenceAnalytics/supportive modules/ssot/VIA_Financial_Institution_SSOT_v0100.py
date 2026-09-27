"""VIA 券商、研究欄位與投資評等單一事實來源（SSOT）。

設計目標：
1. 國內券商、外資券商共用唯一 BrokerContract。
2. 舊鍵 BOA、MCQ、MQ 經由 KEY_MIGRATION_MAP 相容轉換。
3. 目標價與評等採獨立契約，避免名稱、欄位與評等混在同一字典。
4. 提供別名反查、內文擷取、完整性驗證及 JSON 匯出。
5. 以 Email／電話作錨點，關聯附近姓名、券商網域、頁尾與附錄小字評等。
6. 自動學習只寫入 run-local overlay；canonical SSOT 與 Regex authority 保持唯讀。
"""

from __future__ import annotations

# =============================================================================
# 01. 參數區（所有可調參數集中於頂部）
# =============================================================================

import hashlib
import json
import re
import unicodedata
from difflib import SequenceMatcher
from enum import Enum, IntEnum
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, TypeVar, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


SSOT_VERSION = "1.1.0"
DEFAULT_BROKER_CATEGORY = "DOMESTIC_BROKER"
FOREIGN_BROKER_CATEGORY = "FOREIGN_BROKER"
LEGACY_FOREIGN_BROKER_CATEGORY = "LEGACY_FOREIGN_BROKER"
DEFAULT_EXPORT_ENCODING = "utf-8"
DEFAULT_JSON_INDENT = 2
ASCII_WORD_PATTERN = re.compile(r"^[a-z0-9.&'\- ]+$", re.IGNORECASE)
NON_ALNUM_PATTERN = re.compile(r"[^0-9a-z\u3400-\u9fff]+", re.IGNORECASE)
CONTACT_LINE_WINDOW = 2
NAME_MATCH_THRESHOLD = 0.78
AUTO_ALIAS_OVERLAY_THRESHOLD = 0.98
SMALL_FONT_RATIO = 0.82
FOOTER_Y_RATIO = 0.84
MAX_INSTITUTION_ALIAS_LENGTH = 64
GENERIC_EMAIL_LOCAL_PARTS = {
    "admin", "contact", "customer.service", "help", "info", "investor.relations",
    "ir", "media", "research", "sales", "service", "support", "team",
}
FOOTER_MARKERS = (
    "analyst certification", "disclaimer", "important disclosure", "research disclosure",
    "免責聲明", "分析師聲明", "重要聲明", "法定披露", "研究報告聲明",
)
APPENDIX_MARKERS = ("appendix", "附錄", "附表", "disclosure appendix")
SPECIAL_SURNAME_MAP = {
    "oconnor": "O’Connor",
    "oneill": "O’Neill",
    "mcdonald": "McDonald",
    "macdonald": "MacDonald",
    "desouza": "de Souza",
    "jeanpaul": "Jean-Paul",
}
ENGLISH_TO_CHINESE_TOKEN_MAP = {
    "john": "約翰",
    "smith": "史密斯",
    "patrick": "派屈克",
    "paul": "保羅",
    "anna": "安娜",
    "maria": "瑪麗亞",
}

# 舊版或外部來源的鍵值，只在輸入端相容；輸出一律使用 canonical key。
KEY_MIGRATION_MAP: Dict[str, str] = {
    "BOA": "BOFA",
    "ML": "BOFA",
    "MCQ": "MACQUARIE",
    "MQ": "MACQUARIE",
}


# =============================================================================
# 02. 契約 Schema
# =============================================================================

class StrictSSOTModel(BaseModel):
    """禁止未宣告欄位及實例變更，避免執行期悄悄污染 SSOT。"""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class BrokerContract(StrictSSOTModel):
    ssot_key: str = Field(..., min_length=2, description="券商標準英文縮寫（SSOT Key）")
    chinese_name: str = Field(..., min_length=2, description="國內慣用正式中文名稱")
    english_name: str = Field(..., min_length=2, description="正式英文名稱")
    aliases: List[str] = Field(default_factory=list, description="同義字與報告常見簡稱")
    category: str = Field(default=DEFAULT_BROKER_CATEGORY, description="機構分類")
    is_legacy: bool = Field(default=False, description="是否只供歷史報告解析")

    @field_validator("ssot_key")
    @classmethod
    def validate_ssot_key(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", normalized):
            raise ValueError("ssot_key 僅允許大寫英數字與底線")
        return normalized


class ResearchFieldContract(StrictSSOTModel):
    ssot_key: str = Field(..., min_length=2, description="研究欄位標準鍵")
    code: str = Field(..., min_length=1, description="輸出短碼")
    chinese_name: str = Field(..., min_length=2, description="標準中文名稱")
    english_name: str = Field(..., min_length=2, description="標準英文名稱")
    aliases: List[str] = Field(default_factory=list, description="中英文欄位別名")
    category: str = Field(default="RESEARCH_FIELD", description="SSOT 分類")
    value_type: str = Field(default="DECIMAL", description="值型別")
    unit: str = Field(default="LOCAL_CURRENCY_PER_SHARE", description="預設單位")


class RatingCode(IntEnum):
    NOT_RATED = 0
    STRONG_BUY = 1
    BUY = 2
    HOLD = 3
    SELL = 4
    STRONG_SELL = 5


class RatingContract(StrictSSOTModel):
    ssot_key: str = Field(..., min_length=2, description="評等標準鍵")
    code: RatingCode = Field(..., description="固定評等碼 0–5")
    chinese_name: str = Field(..., min_length=2, description="標準中文評等")
    english_name: str = Field(..., min_length=2, description="標準英文評等")
    aliases: List[str] = Field(default_factory=list, description="券商常見評等同義字")
    category: str = Field(default="BROKER_RATING", description="SSOT 分類")
    actionable: bool = Field(default=True, description="是否代表可執行投資方向")
    direction: str = Field(..., description="POSITIVE、NEUTRAL、NEGATIVE 或 UNAVAILABLE")


class RegexContract(StrictSSOTModel):
    ssot_key: str = Field(..., min_length=2, description="Regex 標準鍵")
    pattern: str = Field(..., min_length=1, description="Regex 原始字串")
    flags: int = Field(default=0, description="Python re flags")
    description: str = Field(..., min_length=2, description="規則用途")
    examples: List[str] = Field(default_factory=list, description="正向 corpus 範例")

    def compile(self) -> re.Pattern[str]:
        return re.compile(self.pattern, self.flags)


class DomainContract(StrictSSOTModel):
    domain: str = Field(..., min_length=3, description="標準根網域")
    institution_name: str = Field(..., min_length=2, description="機構顯示名稱")
    institution_type: str = Field(..., min_length=2, description="機構類型")
    broker_ssot_key: Optional[str] = Field(default=None, description="可對應時的券商 SSOT key")
    is_research_domain: bool = Field(default=False, description="是否常見於研究報告聯絡資訊")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="網域歸屬信心")


class TextBlock(StrictSSOTModel):
    text: str = Field(..., description="文字區塊")
    page_number: int = Field(default=1, ge=1)
    line_number: int = Field(default=1, ge=1)
    font_size: Optional[float] = Field(default=None, gt=0)
    median_font_size: Optional[float] = Field(default=None, gt=0)
    y_ratio: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    is_appendix: bool = Field(default=False)


class EntityMention(StrictSSOTModel):
    entity_type: str
    ssot_key: str
    matched_text: str
    page_number: int
    line_number: int
    zone: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class BrokerRatingLink(StrictSSOTModel):
    broker_ssot_key: str
    rating_ssot_key: str
    page_number: int
    broker_line_number: int
    rating_line_number: int
    zone: str
    line_distance: int = Field(..., ge=0)
    confidence: float = Field(..., ge=0.0, le=1.0)


class ContactRecord(StrictSSOTModel):
    anchor_type: str
    email: Optional[str] = None
    email_local_part: Optional[str] = None
    domain: Optional[str] = None
    english_name_guess: Optional[str] = None
    matched_english_name: Optional[str] = None
    matched_chinese_name: Optional[str] = None
    chinese_name_guess: Optional[str] = None
    phones: List[str] = Field(default_factory=list)
    institution: Optional[str] = None
    institution_type: Optional[str] = None
    broker_ssot_key: Optional[str] = None
    is_research: bool = False
    page_number: int
    line_number: int
    zone: str
    name_match_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    rating_keys: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)


class AliasStatus(str, Enum):
    ALREADY_CANONICAL = "ALREADY_CANONICAL"
    OVERLAY_APPLIED = "OVERLAY_APPLIED"
    HUMAN_REVIEW_ONLY = "HUMAN_REVIEW_ONLY"
    REJECTED_CONFLICT = "REJECTED_CONFLICT"


class AliasCandidate(StrictSSOTModel):
    broker_ssot_key: str
    alias: str
    source_domain: str
    page_number: int
    line_number: int
    zone: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    deterministic_domain: bool
    status: AliasStatus
    evidence_hash: str


class DocumentExtractionResult(StrictSSOTModel):
    schema_id: str = "VIA_CONTACT_LAYOUT_EXTRACTION"
    contract_version: str = SSOT_VERSION
    trace_id: str
    contacts: List[ContactRecord] = Field(default_factory=list)
    broker_mentions: List[EntityMention] = Field(default_factory=list)
    rating_mentions: List[EntityMention] = Field(default_factory=list)
    broker_rating_links: List[BrokerRatingLink] = Field(default_factory=list)
    alias_candidates: List[AliasCandidate] = Field(default_factory=list)
    alias_overlay: Dict[str, BrokerContract] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


# =============================================================================
# 03. 台資券商 SSOT
# =============================================================================

VIA_DOMESTIC_BROKER_SSOT_REGISTRY: Dict[str, BrokerContract] = {
    "YUANTA": BrokerContract(
        ssot_key="YUANTA", chinese_name="元大證券", english_name="Yuanta Securities",
        aliases=["元大", "元大證券", "元大投顧", "Yuanta", "Yuanta Securities"],
    ),
    "KGI": BrokerContract(
        ssot_key="KGI", chinese_name="凱基證券", english_name="KGI Securities",
        aliases=["凱基", "凱基證券", "凱基投顧", "KGI", "KGI Securities"],
    ),
    "FUBON": BrokerContract(
        ssot_key="FUBON", chinese_name="富邦證券", english_name="Fubon Securities",
        aliases=["富邦", "富邦證券", "富邦投顧", "Fubon", "Fubon Securities"],
    ),
    "CAPITAL": BrokerContract(
        ssot_key="CAPITAL", chinese_name="群益金鼎證券", english_name="Capital Securities",
        aliases=["群益", "群益金鼎", "群益金鼎證券", "群益投顧", "Capital", "Capital Securities"],
    ),
    "MASTERLINK": BrokerContract(
        ssot_key="MASTERLINK", chinese_name="元富證券", english_name="MasterLink Securities",
        aliases=["元富", "元富證券", "元富投顧", "MasterLink", "MasterLink Securities"],
    ),
    "SINOPAC": BrokerContract(
        ssot_key="SINOPAC", chinese_name="永豐金證券", english_name="SinoPac Securities",
        aliases=["永豐", "永豐金", "永豐金證券", "永豐投顧", "SinoPac", "SinoPac Securities"],
    ),
    "PRESIDENT": BrokerContract(
        ssot_key="PRESIDENT", chinese_name="統一證券", english_name="President Securities",
        aliases=["統一", "統一證券", "統一投顧", "President", "President Securities"],
    ),
    "MEGA": BrokerContract(
        ssot_key="MEGA", chinese_name="兆豐證券", english_name="Mega Securities",
        aliases=["兆豐", "兆豐證券", "兆豐投顧", "Mega", "Mega Securities"],
    ),
    "CATHAY": BrokerContract(
        ssot_key="CATHAY", chinese_name="國泰證券", english_name="Cathay Securities",
        aliases=["國泰", "國泰證券", "國泰期貨", "國泰投顧", "Cathay", "Cathay Securities"],
    ),
    "TAISHIN": BrokerContract(
        ssot_key="TAISHIN", chinese_name="台新證券", english_name="Taishin Securities",
        aliases=["台新", "台新證券", "台新投顧", "Taishin", "Taishin Securities"],
    ),
    "CTBC": BrokerContract(
        ssot_key="CTBC", chinese_name="中國信託綜合證券", english_name="CTBC Securities",
        aliases=["中信", "中信證", "中信證券", "中信投顧", "中國信託", "中國信託證券", "中國信託綜合證券", "CTBC", "CTBC Securities"],
    ),
    "FIRST": BrokerContract(
        ssot_key="FIRST", chinese_name="第一金證券", english_name="First Securities",
        aliases=["第一金", "第一金證券", "第一金投顧", "First", "First Securities"],
    ),
    "HUANAN": BrokerContract(
        ssot_key="HUANAN", chinese_name="華南永昌證券", english_name="Hua Nan Securities",
        aliases=["華南", "華南永昌", "華南永昌證券", "華南投顧", "Hua Nan", "Hua Nan Securities"],
    ),
    "ESUN": BrokerContract(
        ssot_key="ESUN", chinese_name="玉山證券", english_name="E.SUN Securities",
        aliases=["玉山", "玉山證券", "玉山投顧", "E.SUN", "E.SUN Securities"],
    ),
    "WATERLAND": BrokerContract(
        ssot_key="WATERLAND", chinese_name="國票證券", english_name="Waterland Securities",
        aliases=["國票", "國票證券", "國票投顧", "國票華頓", "Waterland", "Waterland Securities"],
    ),
    "CONCORD": BrokerContract(
        ssot_key="CONCORD", chinese_name="康和證券", english_name="Concord Securities",
        aliases=["康和", "康和證券", "康和投顧", "Concord", "Concord Securities"],
    ),
}

# 舊程式名稱相容；兩者指向同一物件，不複製第二份資料。
VIA_BROKER_SSOT_REGISTRY = VIA_DOMESTIC_BROKER_SSOT_REGISTRY


# =============================================================================
# 04. 外資券商 SSOT
# =============================================================================

VIA_FOREIGN_BROKER_SSOT_REGISTRY: Dict[str, BrokerContract] = {
    "MS": BrokerContract(
        ssot_key="MS", chinese_name="摩根士丹利", english_name="Morgan Stanley",
        aliases=["大摩", "摩根士丹利", "Morgan Stanley", "MS"],
        category=FOREIGN_BROKER_CATEGORY,
    ),
    "JPM": BrokerContract(
        ssot_key="JPM", chinese_name="摩根大通", english_name="J.P. Morgan",
        aliases=["小摩", "摩根大通", "摩通", "J.P. Morgan", "JPM"],
        category=FOREIGN_BROKER_CATEGORY,
    ),
    "GS": BrokerContract(
        ssot_key="GS", chinese_name="高盛", english_name="Goldman Sachs",
        aliases=["高盛", "Goldman Sachs", "Goldman", "GS"],
        category=FOREIGN_BROKER_CATEGORY,
    ),
    "UBS": BrokerContract(
        ssot_key="UBS", chinese_name="瑞銀證券", english_name="UBS",
        aliases=["瑞銀", "瑞銀證券", "瑞士銀行", "UBS", "UBS Securities"],
        category=FOREIGN_BROKER_CATEGORY,
    ),
    "BOFA": BrokerContract(
        ssot_key="BOFA", chinese_name="美銀證券", english_name="BofA Securities",
        aliases=["美林", "美林證券", "美銀", "美銀證券", "Bank of America", "BofA", "BofA Securities", "BOA", "Merrill Lynch", "ML"],
        category=FOREIGN_BROKER_CATEGORY,
    ),
    "CITI": BrokerContract(
        ssot_key="CITI", chinese_name="花旗環球證券", english_name="Citigroup",
        aliases=["花旗", "花旗環球", "花旗環球證券", "Citi", "Citigroup"],
        category=FOREIGN_BROKER_CATEGORY,
    ),
    "MACQUARIE": BrokerContract(
        ssot_key="MACQUARIE", chinese_name="麥格理資本", english_name="Macquarie",
        aliases=["麥格理", "麥格理資本", "Macquarie", "Macquarie Capital", "MCQ", "MQ"],
        category=FOREIGN_BROKER_CATEGORY,
    ),
    "NOMURA": BrokerContract(
        ssot_key="NOMURA", chinese_name="野村證券", english_name="Nomura",
        aliases=["野村", "野村證券", "Nomura", "Nomura Securities"],
        category=FOREIGN_BROKER_CATEGORY,
    ),
    "CLSA": BrokerContract(
        ssot_key="CLSA", chinese_name="里昂證券", english_name="CLSA",
        aliases=["里昂", "里昂證券", "CLSA", "CLSA Securities"],
        category=FOREIGN_BROKER_CATEGORY,
    ),
    "HSBC": BrokerContract(
        ssot_key="HSBC", chinese_name="匯豐證券", english_name="HSBC",
        aliases=["匯豐", "匯豐證券", "HSBC", "HSBC Securities"],
        category=FOREIGN_BROKER_CATEGORY,
    ),
    "DAIWA": BrokerContract(
        ssot_key="DAIWA", chinese_name="大和資本", english_name="Daiwa Capital Markets",
        aliases=["大和", "大和資本", "Daiwa", "Daiwa Capital Markets"],
        category=FOREIGN_BROKER_CATEGORY,
    ),
    "CS": BrokerContract(
        ssot_key="CS", chinese_name="瑞士信貸", english_name="Credit Suisse",
        aliases=["瑞信", "瑞士信貸", "Credit Suisse", "CS"],
        category=LEGACY_FOREIGN_BROKER_CATEGORY,
        is_legacy=True,
    ),
}

VIA_ALL_BROKER_SSOT_REGISTRY: Dict[str, BrokerContract] = {
    **VIA_DOMESTIC_BROKER_SSOT_REGISTRY,
    **VIA_FOREIGN_BROKER_SSOT_REGISTRY,
}


# =============================================================================
# 05. 聯絡資訊 Regex 與 Domain SSOT
# =============================================================================

VIA_REGEX_SSOT_REGISTRY: Dict[str, RegexContract] = {
    "taiwan_phone": RegexContract(
        ssot_key="TAIWAN_PHONE",
        pattern=r"(?<!\d)(?:(?:\+?886)[\s().-]*0?|0)(?:9(?:[\s.-]*\d){8}|[2-8](?:[\s().-]*\d){7,8})(?!\d)",
        flags=re.IGNORECASE,
        description="台灣行動電話與市內電話，允許國碼、空白、括號及連字號",
        examples=["0912345678", "+886 912 345 678", "02-2345-6789", "+886-2-2345-6789"],
    ),
    "hong_kong_phone": RegexContract(
        ssot_key="HONG_KONG_PHONE",
        pattern=r"(?<!\d)(?:(?:\+?852)[\s().-]*)?[2356789](?:[\s.-]*\d){7}(?!\d)",
        description="香港八位電話，允許 +852、空白及連字號",
        examples=["2123 4567", "+852 9123 4567"],
    ),
    "email": RegexContract(
        ssot_key="EMAIL",
        pattern=r"(?<![A-Z0-9._%+\-])[A-Z0-9._%+\-]+@[A-Z0-9.-]+\.[A-Z]{2,63}(?![A-Z0-9._%+\-])",
        flags=re.IGNORECASE,
        description="一般電子郵件地址",
        examples=["john.smith@morganstanley.com", "analyst@kgi.com.tw"],
    ),
    "local_part": RegexContract(
        ssot_key="EMAIL_LOCAL_PART",
        pattern=r"^[A-Z0-9]+(?:[._+\-][A-Z0-9]+)*$",
        flags=re.IGNORECASE,
        description="Email @ 左側 local part",
        examples=["john.smith", "p.oconnor", "analyst01"],
    ),
    "domain": RegexContract(
        ssot_key="DOMAIN",
        pattern=r"^(?:[A-Z0-9](?:[A-Z0-9\-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,63}$",
        flags=re.IGNORECASE,
        description="DNS 網域名稱",
        examples=["kgi.com.tw", "research.ubs.com"],
    ),
    "chinese_name": RegexContract(
        ssot_key="CHINESE_NAME",
        pattern=r"^[\u3400-\u9fff]{2,6}$|^[\u3400-\u9fff]{1,3}[·・\s][\u3400-\u9fff]{1,4}$",
        description="完整中文字姓名；只在 Email 或電話鄰近區域使用",
        examples=["王小明", "歐陽明", "阿里・木拉提"],
    ),
    "english_name": RegexContract(
        ssot_key="ENGLISH_NAME",
        pattern=r"^[A-Z](?:[A-Z]|[A-Z'’\-]*[A-Z])?\.?(?:\s+[A-Z](?:[A-Z]|[A-Z'’\-]*[A-Z])?\.?){1,4}$",
        flags=re.IGNORECASE,
        description="二至五段英文姓名，支援縮寫、撇號與連字號",
        examples=["John Smith", "Patrick O'Connor", "J. P. Morgan"],
    ),
    "institution_label": RegexContract(
        ssot_key="INSTITUTION_LABEL",
        pattern=(
            r"(?:[\u3400-\u9fff]{2,16}(?:證券|投顧|銀行|資本)|"
            r"[A-Z][A-Z&.'’\- ]{1,50}(?:Securities|Capital Markets|Research|Bank))"
        ),
        flags=re.IGNORECASE,
        description="Email 鄰近區域的候選機構名稱；僅供 overlay 學習",
        examples=["摩根士丹利證券", "Morgan Stanley Research"],
    ),
}

# 相容舊介面：REGEX 仍可直接以 REGEX["email"].finditer(...) 使用。
REGEX: Dict[str, re.Pattern[str]] = {
    key: contract.compile() for key, contract in VIA_REGEX_SSOT_REGISTRY.items()
}
# 舊版拼法相容；不建立第二份 Regex authority。
REGEX["taipei_phone"] = REGEX["taiwan_phone"]
REGEX["hongkong_phone"] = REGEX["hong_kong_phone"]

VIA_DOMAIN_SSOT_REGISTRY: Dict[str, DomainContract] = {
    "kgi.com.tw": DomainContract(domain="kgi.com.tw", institution_name="凱基證券", institution_type="券商", broker_ssot_key="KGI", is_research_domain=True),
    "fubon.com": DomainContract(domain="fubon.com", institution_name="富邦證券", institution_type="券商", broker_ssot_key="FUBON", is_research_domain=True, confidence=0.90),
    "sinopac.com.tw": DomainContract(domain="sinopac.com.tw", institution_name="永豐金證券", institution_type="券商", broker_ssot_key="SINOPAC", is_research_domain=True),
    "yuanta.com": DomainContract(domain="yuanta.com", institution_name="元大證券", institution_type="券商", broker_ssot_key="YUANTA", is_research_domain=True, confidence=0.90),
    "cathaysec.com.tw": DomainContract(domain="cathaysec.com.tw", institution_name="國泰證券", institution_type="券商", broker_ssot_key="CATHAY", is_research_domain=True),
    "taishinsec.com.tw": DomainContract(domain="taishinsec.com.tw", institution_name="台新證券", institution_type="券商", broker_ssot_key="TAISHIN", is_research_domain=True),
    "citi.com": DomainContract(domain="citi.com", institution_name="花旗銀行", institution_type="外資銀行", broker_ssot_key="CITI", is_research_domain=True, confidence=0.95),
    "ubs.com": DomainContract(domain="ubs.com", institution_name="瑞銀", institution_type="外資券商", broker_ssot_key="UBS", is_research_domain=True),
    "jpmorgan.com": DomainContract(domain="jpmorgan.com", institution_name="摩根大通", institution_type="外資券商", broker_ssot_key="JPM", is_research_domain=True),
    "goldmansachs.com": DomainContract(domain="goldmansachs.com", institution_name="高盛", institution_type="外資券商", broker_ssot_key="GS", is_research_domain=True),
    "ml.com": DomainContract(domain="ml.com", institution_name="美林", institution_type="外資券商", broker_ssot_key="BOFA", is_research_domain=True, confidence=0.95),
    "morganstanley.com": DomainContract(domain="morganstanley.com", institution_name="摩根士丹利", institution_type="外資券商", broker_ssot_key="MS", is_research_domain=True),
    "clsa.com": DomainContract(domain="clsa.com", institution_name="里昂證券", institution_type="外資券商", broker_ssot_key="CLSA", is_research_domain=True),
    "hkex.com.hk": DomainContract(domain="hkex.com.hk", institution_name="香港交易所", institution_type="交易所"),
    "hksfc.org.hk": DomainContract(domain="hksfc.org.hk", institution_name="香港證監會", institution_type="監管機構"),
    "hsbc.com.hk": DomainContract(domain="hsbc.com.hk", institution_name="滙豐銀行", institution_type="銀行"),
}

# 舊常數相容，但真實權威來源只有 VIA_DOMAIN_SSOT_REGISTRY。
DOMAIN_MAP = {key: value.institution_name for key, value in VIA_DOMAIN_SSOT_REGISTRY.items()}
DOMAIN_TYPE = {key: value.institution_type for key, value in VIA_DOMAIN_SSOT_REGISTRY.items()}
RESEARCH_DOMAINS = {key for key, value in VIA_DOMAIN_SSOT_REGISTRY.items() if value.is_research_domain}


# =============================================================================
# 06. 研究欄位 SSOT
# =============================================================================

VIA_RESEARCH_FIELD_SSOT_REGISTRY: Dict[str, ResearchFieldContract] = {
    "TARGET_PRICE": ResearchFieldContract(
        ssot_key="TARGET_PRICE",
        code="TP",
        chinese_name="目標價",
        english_name="Target Price",
        aliases=[
            "Target Price", "Price Target", "TP", "PT", "Target", "Tgt",
            "Fair Value", "FV", "Valuation", "目標價", "目標股價", "目標",
            "合理價", "合理股價", "預期價", "目標區間",
        ],
    ),
}


# =============================================================================
# 07. 券商評等 SSOT（固定碼：0–5）
# =============================================================================

VIA_BROKER_RATING_SSOT_REGISTRY: Dict[str, RatingContract] = {
    "NOT_RATED": RatingContract(
        ssot_key="NOT_RATED", code=RatingCode.NOT_RATED,
        chinese_name="未評等", english_name="Not Rated",
        aliases=[
            "Not Rated", "Non-Rated", "NR", "Under Review", "UR", "Restricted",
            "Rating Suspended", "Suspended Rating", "Coverage Suspended",
            "評等審視中", "評估中", "未評等", "無評等", "暫停評等", "受限", "停止追蹤",
        ],
        actionable=False, direction="UNAVAILABLE",
    ),
    "STRONG_BUY": RatingContract(
        ssot_key="STRONG_BUY", code=RatingCode.STRONG_BUY,
        chinese_name="強力買進", english_name="Strong Buy",
        aliases=[
            "Strong Buy", "Conviction Buy", "Trading Buy", "Top Pick",
            "強力買進", "強烈買進", "確信買進", "核心買進", "首選",
        ],
        direction="POSITIVE",
    ),
    "BUY": RatingContract(
        ssot_key="BUY", code=RatingCode.BUY,
        chinese_name="買進", english_name="Buy",
        aliases=[
            "Buy", "Accumulate", "Add", "Outperform", "Overweight",
            "Market Outperform", "Sector Outperform", "Positive",
            "買進", "買入", "收集", "加碼", "優於大盤", "優於市場", "優於同業",
            "逢低買進", "買進（初次）",
        ],
        direction="POSITIVE",
    ),
    "HOLD": RatingContract(
        ssot_key="HOLD", code=RatingCode.HOLD,
        chinese_name="持有", english_name="Hold",
        aliases=[
            "Hold", "Neutral", "Equal Weight", "Market Perform", "Sector Perform",
            "Peer Perform", "In-Line", "持有", "中立", "中性", "觀望",
            "與大盤同步", "與市場同步", "與同業同步", "區間操作",
        ],
        direction="NEUTRAL",
    ),
    "SELL": RatingContract(
        ssot_key="SELL", code=RatingCode.SELL,
        chinese_name="賣出", english_name="Sell",
        aliases=[
            "Sell", "Reduce", "Underperform", "Underweight", "Negative",
            "Market Underperform", "Sector Underperform", "賣出", "賣超", "減持", "減碼",
            "劣於大盤", "劣於市場", "逢高減碼", "賣出（初次）",
        ],
        direction="NEGATIVE",
    ),
    "STRONG_SELL": RatingContract(
        ssot_key="STRONG_SELL", code=RatingCode.STRONG_SELL,
        chinese_name="強力賣出", english_name="Strong Sell",
        aliases=["Strong Sell", "Conviction Sell", "強力賣出", "強烈賣出", "確信賣出"],
        direction="NEGATIVE",
    ),
}


# =============================================================================
# 08. 正規化、索引與解析函式
# =============================================================================

ContractT = TypeVar("ContractT", bound=StrictSSOTModel)


def normalize_alias(value: str) -> str:
    """將全半形、大小寫、空白與標點差異正規化為可比對鍵。"""

    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    return NON_ALNUM_PATTERN.sub("", normalized)


def canonicalize_broker_key(value: str) -> str:
    """將舊版券商鍵轉為唯一 canonical key。"""

    normalized_key = unicodedata.normalize("NFKC", value).strip().upper()
    return KEY_MIGRATION_MAP.get(normalized_key, normalized_key)


def contract_aliases(contract: ContractT) -> Iterable[str]:
    """取得一筆契約所有可反查名稱。"""

    yield str(getattr(contract, "ssot_key"))
    yield str(getattr(contract, "chinese_name"))
    yield str(getattr(contract, "english_name"))
    yield from getattr(contract, "aliases")


def build_alias_index(registry: Mapping[str, ContractT]) -> Dict[str, str]:
    """建立 normalized alias → ssot_key 索引；發生歧義立即失敗。"""

    index: Dict[str, str] = {}
    for key, contract in registry.items():
        for alias in contract_aliases(contract):
            normalized = normalize_alias(alias)
            if not normalized:
                raise ValueError(f"{key} 含空白別名")
            previous = index.get(normalized)
            if previous is not None and previous != key:
                raise ValueError(f"別名衝突：{alias!r} 同時屬於 {previous} 與 {key}")
            index[normalized] = key
    return index


def resolve_contract(value: str, registry: Mapping[str, ContractT]) -> Optional[ContractT]:
    """以標準鍵、正式名稱或完整別名精確反查契約。"""

    alias_index = build_alias_index(registry)
    key = alias_index.get(normalize_alias(value))
    return registry.get(key) if key else None


def resolve_broker(value: str) -> Optional[BrokerContract]:
    """反查券商；先處理舊鍵，再處理正式名稱及別名。"""

    canonical_key = canonicalize_broker_key(value)
    if canonical_key in VIA_ALL_BROKER_SSOT_REGISTRY:
        return VIA_ALL_BROKER_SSOT_REGISTRY[canonical_key]
    return resolve_contract(value, VIA_ALL_BROKER_SSOT_REGISTRY)


def resolve_research_field(value: str) -> Optional[ResearchFieldContract]:
    """反查研究欄位，例如 TP、PT、目標價或 Fair Value。"""

    return resolve_contract(value, VIA_RESEARCH_FIELD_SSOT_REGISTRY)


def resolve_rating(value: str) -> Optional[RatingContract]:
    """以完整評等詞精確反查標準評等。"""

    return resolve_contract(value, VIA_BROKER_RATING_SSOT_REGISTRY)


def contains_alias(text: str, alias: str) -> bool:
    """判斷內文是否含別名；英數短碼採單字邊界，中文採正規化包含。"""

    normalized_text = unicodedata.normalize("NFKC", text).casefold()
    normalized_alias = unicodedata.normalize("NFKC", alias).casefold().strip()
    if ASCII_WORD_PATTERN.fullmatch(normalized_alias):
        pattern = rf"(?<![a-z0-9]){re.escape(normalized_alias)}(?![a-z0-9])"
        return re.search(pattern, normalized_text, flags=re.IGNORECASE) is not None
    return normalize_alias(alias) in normalize_alias(text)


def extract_contracts(text: str, registry: Mapping[str, ContractT]) -> List[ContractT]:
    """由報告內文擷取契約，較長別名優先，同一 SSOT key 僅回傳一次。"""

    candidates: List[Tuple[int, str, ContractT]] = []
    for key, contract in registry.items():
        aliases = sorted(set(contract_aliases(contract)), key=len, reverse=True)
        for alias in aliases:
            if contains_alias(text, alias):
                candidates.append((len(alias), key, contract))
                break

    seen = set()
    results: List[ContractT] = []
    for _, key, contract in sorted(candidates, key=lambda item: (-item[0], item[1])):
        if key not in seen:
            seen.add(key)
            results.append(contract)
    return results


def extract_brokers(text: str) -> List[BrokerContract]:
    """由研究報告內文擷取所有券商。"""

    return extract_contracts(text, VIA_ALL_BROKER_SSOT_REGISTRY)


def find_alias_spans(text: str, alias: str) -> List[Tuple[int, int]]:
    """找出別名在原文中的位置，供最長詞優先與重疊消歧使用。"""

    normalized_text = unicodedata.normalize("NFKC", text).casefold()
    normalized_alias = unicodedata.normalize("NFKC", alias).casefold().strip()
    if not normalized_alias:
        return []
    if ASCII_WORD_PATTERN.fullmatch(normalized_alias):
        pattern = rf"(?<![a-z0-9]){re.escape(normalized_alias)}(?![a-z0-9])"
    else:
        pattern = re.escape(normalized_alias)
    return [(match.start(), match.end()) for match in re.finditer(pattern, normalized_text)]


def extract_ratings(text: str) -> List[RatingContract]:
    """由研究報告內文擷取所有評等，Strong Buy 不會被降成 Buy。"""

    candidates: List[Tuple[int, int, int, str, RatingContract]] = []
    for key, contract in VIA_BROKER_RATING_SSOT_REGISTRY.items():
        for alias in set(contract_aliases(contract)):
            for start, end in find_alias_spans(text, alias):
                candidates.append((start, end, end - start, key, contract))

    accepted: List[Tuple[int, int, str, RatingContract]] = []
    occupied: List[Tuple[int, int]] = []
    for start, end, _, key, contract in sorted(candidates, key=lambda item: (-item[2], item[0], item[3])):
        if any(start < used_end and end > used_start for used_start, used_end in occupied):
            continue
        occupied.append((start, end))
        accepted.append((start, end, key, contract))

    seen = set()
    results: List[RatingContract] = []
    for _, _, key, contract in sorted(accepted, key=lambda item: item[0]):
        if key not in seen:
            seen.add(key)
            results.append(contract)
    return results


# =============================================================================
# 09. Email／電話／姓名／版面鄰近關聯引擎
# =============================================================================

def normalize_domain(domain: str) -> str:
    """正規化 Email 網域並移除常見外層符號。"""

    return unicodedata.normalize("NFKC", domain).strip().strip(".>)]}，。；;:").casefold()


def resolve_domain(domain: str) -> Optional[DomainContract]:
    """以最長根網域比對，支援 research.example.com 等子網域。"""

    normalized = normalize_domain(domain)
    matches = [
        contract for root, contract in VIA_DOMAIN_SSOT_REGISTRY.items()
        if normalized == root or normalized.endswith("." + root)
    ]
    return max(matches, key=lambda item: len(item.domain)) if matches else None


def normalize_special_surnames(word: str) -> str:
    """恢復常見英文複姓、撇號與連字號大小寫。"""

    compact = normalize_alias(word)
    return SPECIAL_SURNAME_MAP.get(compact, word[:1].upper() + word[1:].lower())


def english_to_chinese(name: str) -> Optional[str]:
    """只在全部 token 皆有 SSOT 對照時提供中文音譯猜測。"""

    tokens = re.findall(r"[A-Za-z]+", unicodedata.normalize("NFKC", name))
    if not tokens:
        return None
    mapped = [ENGLISH_TO_CHINESE_TOKEN_MAP.get(token.casefold()) for token in tokens]
    return "".join(item for item in mapped if item) if all(mapped) else None


def chinese_to_english(name: str) -> Optional[str]:
    """使用已安裝的 pypinyin 或 pinyin；均不存在時明確回傳 None。"""

    try:
        from pypinyin import Style, lazy_pinyin

        return " ".join(lazy_pinyin(name, style=Style.NORMAL)).title()
    except ImportError:
        try:
            import pinyin

            return pinyin.get(name, format="strip", delimiter=" ").title()
        except ImportError:
            return None


def restore_english_name(local_part: str) -> Optional[str]:
    """由 Email local part 還原可解釋的英文姓名，不武斷切割連寫帳號。"""

    normalized = unicodedata.normalize("NFKC", local_part).split("+", 1)[0].strip("._-")
    if not normalized or normalized.casefold() in GENERIC_EMAIL_LOCAL_PARTS:
        return None
    if re.search(r"\d", normalized):
        return None
    parts = [part for part in re.split(r"[._-]+", normalized) if part]
    if not parts:
        return None
    formatted = [normalize_special_surnames(part) for part in parts]
    return " ".join(formatted)


def email_name_match_score(local_part: str, candidate_name: str) -> float:
    """比較 Email 左側與鄰近英文姓名，涵蓋 firstname.lastname、jsmith 等格式。"""

    local = normalize_alias(local_part.split("+", 1)[0])
    name_parts = re.findall(r"[A-Za-z]+", unicodedata.normalize("NFKC", candidate_name).casefold())
    if not local or len(name_parts) < 2:
        return 0.0
    first, last = name_parts[0], name_parts[-1]
    variants = {
        "".join(name_parts),
        "".join(reversed(name_parts)),
        first[:1] + last,
        first + last[:1],
        last + first[:1],
        first[:1] + "".join(name_parts[1:]),
    }
    if local in variants:
        return 1.0
    return max(SequenceMatcher(None, local, variant).ratio() for variant in variants)


def normalize_phone(phone: str) -> str:
    """統一電話為 +886 或 +852 格式；無國碼資料保留區域原始數字。"""

    raw = unicodedata.normalize("NFKC", phone).strip()
    digits = re.sub(r"\D", "", raw)
    if raw.startswith("+") or digits.startswith("886") or digits.startswith("852"):
        if digits.startswith("886"):
            national = digits[3:].lstrip("0")
            return "+886" + national
        if digits.startswith("852"):
            return "+852" + digits[3:]
    return digits


def restore_institution(domain: str) -> Optional[str]:
    """由 Email 右側網域還原機構名稱。"""

    contract = resolve_domain(domain)
    return contract.institution_name if contract else None


def parse_email(email: str) -> Optional[Dict[str, object]]:
    """相容舊介面：Email → 姓名猜測、機構、券商鍵及研究員屬性。"""

    normalized_email = unicodedata.normalize("NFKC", email).strip()
    if REGEX["email"].fullmatch(normalized_email) is None:
        return None
    local_part, domain = normalized_email.rsplit("@", 1)
    domain_contract = resolve_domain(domain)
    english_guess = restore_english_name(local_part)
    return {
        "email": normalized_email,
        "english_name": english_guess,
        "institution": domain_contract.institution_name if domain_contract else None,
        "institution_type": domain_contract.institution_type if domain_contract else None,
        "broker_ssot_key": domain_contract.broker_ssot_key if domain_contract else None,
        "is_research": bool(domain_contract and domain_contract.is_research_domain),
        "chinese_name_guess": english_to_chinese(english_guess) if english_guess else None,
    }


def detect_type(text: str) -> str:
    """偵測單一值類型；Email 優先於姓名，避免 @ 左右片段誤判。"""

    value = unicodedata.normalize("NFKC", text).strip()
    if REGEX["email"].fullmatch(value):
        return "Email"
    if REGEX["taiwan_phone"].fullmatch(value):
        return "TaiwanPhone"
    if REGEX["hong_kong_phone"].fullmatch(value):
        return "HongKongPhone"
    if REGEX["chinese_name"].fullmatch(value):
        return "ChineseName"
    if REGEX["english_name"].fullmatch(value):
        return "EnglishName"
    if REGEX["domain"].fullmatch(value):
        return "Domain"
    return "Unknown"


def coerce_text_blocks(source: Union[str, Sequence[TextBlock]]) -> List[TextBlock]:
    """將純文字或 Layout Engine 區塊統一轉成 TextBlock。"""

    if isinstance(source, str):
        return [
            TextBlock(text=line, page_number=1, line_number=index)
            for index, line in enumerate(source.splitlines(), start=1)
            if line.strip()
        ]
    return list(source)


def classify_text_zone(block: TextBlock) -> str:
    """利用頁型、字級、垂直位置與聲明詞判定本文／頁尾／附錄小字。"""

    lowered = unicodedata.normalize("NFKC", block.text).casefold()
    small_font = bool(
        block.font_size is not None
        and block.median_font_size is not None
        and block.font_size <= block.median_font_size * SMALL_FONT_RATIO
    )
    appendix = block.is_appendix or any(marker in lowered for marker in APPENDIX_MARKERS)
    footer = (
        (block.y_ratio is not None and block.y_ratio >= FOOTER_Y_RATIO)
        or any(marker in lowered for marker in FOOTER_MARKERS)
    )
    if appendix and small_font:
        return "APPENDIX_SMALL_PRINT"
    if appendix:
        return "APPENDIX"
    if footer and small_font:
        return "FOOTER_SMALL_PRINT"
    if footer:
        return "FOOTER"
    if small_font:
        return "SMALL_PRINT"
    return "BODY"


def nearby_blocks(anchor: TextBlock, blocks: Sequence[TextBlock]) -> List[TextBlock]:
    """取得同頁 Email 錨點前後指定行數的文字。"""

    return sorted(
        [
            block for block in blocks
            if block.page_number == anchor.page_number
            and abs(block.line_number - anchor.line_number) <= CONTACT_LINE_WINDOW
        ],
        key=lambda item: item.line_number,
    )


def clean_name_segment(text: str) -> str:
    """移除聯絡資訊及職稱標籤，留下姓名候選。"""

    cleaned = REGEX["email"].sub(" ", unicodedata.normalize("NFKC", text))
    cleaned = REGEX["taiwan_phone"].sub(" ", cleaned)
    cleaned = REGEX["hong_kong_phone"].sub(" ", cleaned)
    cleaned = re.sub(
        r"(?i)\b(?:senior\s+)?(?:research\s+)?analyst\b|分析師|研究員|作者|撰稿人|姓名",
        " ",
        cleaned,
    )
    return cleaned.strip(" \t|,，;；:：()（）[]【】-")


def extract_nearby_name_candidates(blocks: Sequence[TextBlock]) -> Tuple[List[str], List[str]]:
    """只在 Email／電話鄰近窗格抽取姓名，避免把正文一般詞誤認成人名。"""

    english: List[str] = []
    chinese: List[str] = []
    for block in blocks:
        for segment in re.split(r"[|｜;；\t]", block.text):
            candidate = clean_name_segment(segment)
            if REGEX["english_name"].fullmatch(candidate):
                english.append(" ".join(normalize_special_surnames(item) for item in candidate.split()))
            elif REGEX["chinese_name"].fullmatch(candidate):
                chinese.append(candidate.replace(" ", ""))
        for match in re.finditer(
            r"(?i)(?:analyst|research analyst|author|分析師|研究員|作者|姓名)\s*[:：-]?\s*"
            r"([A-Z][A-Z'’\-]+(?:\s+[A-Z][A-Z'’\-]+){1,4}|[\u3400-\u9fff]{2,6})",
            unicodedata.normalize("NFKC", block.text),
        ):
            candidate = match.group(1).strip()
            if REGEX["english_name"].fullmatch(candidate):
                english.append(" ".join(normalize_special_surnames(item) for item in candidate.split()))
            elif REGEX["chinese_name"].fullmatch(candidate):
                chinese.append(candidate)
    return list(dict.fromkeys(english)), list(dict.fromkeys(chinese))


def find_phone_matches(text: str) -> List[Tuple[int, int, str, str]]:
    """找出電話並消除台灣市話與香港八碼電話的重疊命中。"""

    priority = {"taiwan_phone": 0, "hong_kong_phone": 1}
    candidates: List[Tuple[int, int, str, str]] = []
    for regex_key in ("taiwan_phone", "hong_kong_phone"):
        for match in REGEX[regex_key].finditer(text):
            candidates.append((match.start(), match.end(), regex_key, match.group(0)))
    accepted: List[Tuple[int, int, str, str]] = []
    for candidate in sorted(
        candidates,
        key=lambda item: (-(item[1] - item[0]), priority[item[2]], item[0]),
    ):
        start, end, _, _ = candidate
        if any(start < used_end and end > used_start for used_start, used_end, _, _ in accepted):
            continue
        accepted.append(candidate)
    return sorted(accepted, key=lambda item: item[0])


def extract_phones(blocks: Sequence[TextBlock]) -> List[str]:
    """抽取、重疊消歧並去重台灣與香港電話。"""

    phones = [
        normalize_phone(raw)
        for block in blocks
        for _, _, _, raw in find_phone_matches(block.text)
    ]
    return list(dict.fromkeys(phones))


def choose_matching_english_name(local_part: str, candidates: Sequence[str]) -> Tuple[Optional[str], float]:
    """選出與 Email 左側最相符的鄰近英文姓名。"""

    scored = [(email_name_match_score(local_part, candidate), candidate) for candidate in candidates]
    if not scored:
        return None, 0.0
    score, candidate = max(scored, key=lambda item: (item[0], len(item[1])))
    return (candidate, score) if score >= NAME_MATCH_THRESHOLD else (None, score)


def build_contact_record(email: str, anchor: TextBlock, blocks: Sequence[TextBlock]) -> ContactRecord:
    """以 Email 為錨點，組合附近姓名、電話、網域券商與評等。"""

    local_part, domain = email.rsplit("@", 1)
    domain_contract = resolve_domain(domain)
    neighbors = nearby_blocks(anchor, blocks)
    english_candidates, chinese_candidates = extract_nearby_name_candidates(neighbors)
    matched_english, name_score = choose_matching_english_name(local_part, english_candidates)
    english_guess = restore_english_name(local_part)
    ratings = list(dict.fromkeys(
        rating.ssot_key for block in neighbors for rating in extract_ratings(block.text)
    ))
    evidence = [f"EMAIL@p{anchor.page_number}:l{anchor.line_number}"]
    if matched_english:
        evidence.append(f"EMAIL_LOCAL_NAME_MATCH:{name_score:.3f}")
    if domain_contract:
        evidence.append(f"DOMAIN_SSOT:{domain_contract.domain}")
    if chinese_candidates:
        evidence.append("NEARBY_CHINESE_NAME")
    phones = extract_phones(neighbors)
    if phones:
        evidence.append("NEARBY_PHONE")
    confidence_parts = [1.0]
    if domain_contract:
        confidence_parts.append(domain_contract.confidence)
    if matched_english:
        confidence_parts.append(name_score)
    confidence = sum(confidence_parts) / len(confidence_parts)
    chinese_guess_source = matched_english or english_guess
    return ContactRecord(
        anchor_type="EMAIL",
        email=email,
        email_local_part=local_part,
        domain=normalize_domain(domain),
        english_name_guess=english_guess,
        matched_english_name=matched_english,
        matched_chinese_name=chinese_candidates[0] if len(chinese_candidates) == 1 else None,
        chinese_name_guess=english_to_chinese(chinese_guess_source) if chinese_guess_source else None,
        phones=phones,
        institution=domain_contract.institution_name if domain_contract else None,
        institution_type=domain_contract.institution_type if domain_contract else None,
        broker_ssot_key=domain_contract.broker_ssot_key if domain_contract else None,
        is_research=bool(domain_contract and domain_contract.is_research_domain),
        page_number=anchor.page_number,
        line_number=anchor.line_number,
        zone=classify_text_zone(anchor),
        name_match_score=name_score,
        confidence=confidence,
        rating_keys=ratings,
        evidence=evidence,
    )


def build_phone_contact(phone: str, anchor: TextBlock, blocks: Sequence[TextBlock]) -> ContactRecord:
    """以電話為錨點建立部分聯絡人；無網域時不強制指定券商。"""

    neighbors = nearby_blocks(anchor, blocks)
    english_candidates, chinese_candidates = extract_nearby_name_candidates(neighbors)
    brokers = list(dict.fromkeys(
        broker.ssot_key for block in neighbors for broker in extract_brokers(block.text)
    ))
    broker_key = brokers[0] if len(brokers) == 1 else None
    broker = VIA_ALL_BROKER_SSOT_REGISTRY.get(broker_key) if broker_key else None
    ratings = list(dict.fromkeys(
        rating.ssot_key for block in neighbors for rating in extract_ratings(block.text)
    ))
    evidence = [f"PHONE@p{anchor.page_number}:l{anchor.line_number}"]
    if english_candidates or chinese_candidates:
        evidence.append("NEARBY_NAME")
    if broker_key:
        evidence.append(f"UNIQUE_NEARBY_BROKER:{broker_key}")
    confidence = 0.70 + (0.10 if english_candidates or chinese_candidates else 0.0)
    return ContactRecord(
        anchor_type="PHONE",
        english_name_guess=english_candidates[0] if len(english_candidates) == 1 else None,
        matched_english_name=english_candidates[0] if len(english_candidates) == 1 else None,
        matched_chinese_name=chinese_candidates[0] if len(chinese_candidates) == 1 else None,
        chinese_name_guess=english_to_chinese(english_candidates[0]) if len(english_candidates) == 1 else None,
        phones=[normalize_phone(phone)],
        institution=broker.chinese_name if broker else None,
        institution_type=broker.category if broker else None,
        broker_ssot_key=broker_key,
        is_research=bool(ratings),
        page_number=anchor.page_number,
        line_number=anchor.line_number,
        zone=classify_text_zone(anchor),
        name_match_score=0.0,
        confidence=confidence,
        rating_keys=ratings,
        evidence=evidence,
    )


def extract_contacts(blocks: Sequence[TextBlock]) -> List[ContactRecord]:
    """先以 Email 建完整聯絡人，再補沒有被 Email 涵蓋的電話錨點。"""

    contacts: List[ContactRecord] = []
    seen = set()
    for block in blocks:
        for match in REGEX["email"].finditer(block.text):
            email = match.group(0)
            identity = (email.casefold(), block.page_number)
            if identity in seen:
                continue
            seen.add(identity)
            contacts.append(build_contact_record(email, block, blocks))
    linked_phones = {phone for contact in contacts for phone in contact.phones}
    for block in blocks:
        for _, _, _, raw_phone in find_phone_matches(block.text):
            phone = normalize_phone(raw_phone)
            if phone in linked_phones:
                continue
            linked_phones.add(phone)
            contacts.append(build_phone_contact(phone, block, blocks))
    return contacts


def best_matching_alias(text: str, contract: ContractT) -> str:
    """回傳原文實際命中的最長別名，保留稽核證據。"""

    aliases = [alias for alias in contract_aliases(contract) if find_alias_spans(text, alias)]
    return max(aliases, key=len) if aliases else str(contract.ssot_key)


def extract_document_mentions(blocks: Sequence[TextBlock]) -> Tuple[List[EntityMention], List[EntityMention]]:
    """擷取正文、頁尾及附錄中的券商與評等，保留版面位置。"""

    broker_mentions: List[EntityMention] = []
    rating_mentions: List[EntityMention] = []
    for block in blocks:
        zone = classify_text_zone(block)
        for broker in extract_brokers(block.text):
            broker_mentions.append(EntityMention(
                entity_type="BROKER",
                ssot_key=broker.ssot_key,
                matched_text=best_matching_alias(block.text, broker),
                page_number=block.page_number,
                line_number=block.line_number,
                zone=zone,
                confidence=0.99 if zone == "BODY" else 0.90,
            ))
        for rating in extract_ratings(block.text):
            rating_mentions.append(EntityMention(
                entity_type="BROKER_RATING",
                ssot_key=rating.ssot_key,
                matched_text=best_matching_alias(block.text, rating),
                page_number=block.page_number,
                line_number=block.line_number,
                zone=zone,
                confidence=0.98,
            ))
    return broker_mentions, rating_mentions


def link_brokers_to_ratings(
    broker_mentions: Sequence[EntityMention],
    rating_mentions: Sequence[EntityMention],
    contacts: Sequence[ContactRecord],
) -> Tuple[List[BrokerRatingLink], List[str]]:
    """依同頁與行距連結券商評等；候選券商不唯一時拒絕猜測。"""

    links: List[BrokerRatingLink] = []
    warnings: List[str] = []
    for rating in rating_mentions:
        candidates = [
            broker for broker in broker_mentions
            if broker.page_number == rating.page_number
            and abs(broker.line_number - rating.line_number) <= CONTACT_LINE_WINDOW
        ]
        if not candidates:
            candidates = [
                EntityMention(
                    entity_type="BROKER_FROM_EMAIL_DOMAIN",
                    ssot_key=contact.broker_ssot_key,
                    matched_text=contact.domain or contact.broker_ssot_key,
                    page_number=contact.page_number,
                    line_number=contact.line_number,
                    zone=contact.zone,
                    confidence=contact.confidence,
                )
                for contact in contacts
                if contact.broker_ssot_key
                and contact.page_number == rating.page_number
                and abs(contact.line_number - rating.line_number) <= CONTACT_LINE_WINDOW
            ]
        minimum_distance = min(
            (abs(candidate.line_number - rating.line_number) for candidate in candidates),
            default=None,
        )
        nearest = [
            candidate for candidate in candidates
            if abs(candidate.line_number - rating.line_number) == minimum_distance
        ]
        unique_keys = {candidate.ssot_key for candidate in nearest}
        if len(unique_keys) != 1:
            if candidates:
                warnings.append(
                    f"AMBIGUOUS_BROKER_RATING_LINK@p{rating.page_number}:l{rating.line_number}"
                )
            continue
        broker = max(nearest, key=lambda item: item.confidence)
        distance = abs(broker.line_number - rating.line_number)
        links.append(BrokerRatingLink(
            broker_ssot_key=broker.ssot_key,
            rating_ssot_key=rating.ssot_key,
            page_number=rating.page_number,
            broker_line_number=broker.line_number,
            rating_line_number=rating.line_number,
            zone=rating.zone,
            line_distance=distance,
            confidence=max(0.70, min(broker.confidence, rating.confidence) - 0.04 * distance),
        ))
    return links, warnings


def candidate_alias_status(
    broker_key: str,
    alias: str,
    confidence: float,
    deterministic_domain: bool,
    alias_index: Mapping[str, str],
) -> AliasStatus:
    """依 canonical 衝突、證據及門檻判定別名治理狀態。"""

    existing_key = alias_index.get(normalize_alias(alias))
    if existing_key == broker_key:
        return AliasStatus.ALREADY_CANONICAL
    if existing_key is not None and existing_key != broker_key:
        return AliasStatus.REJECTED_CONFLICT
    if deterministic_domain and confidence >= AUTO_ALIAS_OVERLAY_THRESHOLD:
        return AliasStatus.OVERLAY_APPLIED
    return AliasStatus.HUMAN_REVIEW_ONLY


def discover_alias_candidates(
    contacts: Sequence[ContactRecord],
    blocks: Sequence[TextBlock],
) -> List[AliasCandidate]:
    """由 Email 網域與鄰近機構標籤產生同義字候選，不直接改 canonical SSOT。"""

    alias_index = build_alias_index(VIA_ALL_BROKER_SSOT_REGISTRY)
    candidates: List[AliasCandidate] = []
    seen = set()
    for contact in contacts:
        if not contact.broker_ssot_key:
            continue
        anchor = next(
            (block for block in blocks if block.page_number == contact.page_number and block.line_number == contact.line_number),
            None,
        )
        if anchor is None:
            continue
        if not contact.domain:
            continue
        domain_contract = resolve_domain(contact.domain)
        deterministic = bool(domain_contract and domain_contract.broker_ssot_key == contact.broker_ssot_key)
        for block in nearby_blocks(anchor, blocks):
            distance = abs(block.line_number - anchor.line_number)
            proximity_score = 1.0 if distance == 0 else 0.99
            confidence = (domain_contract.confidence if domain_contract else 0.0) * proximity_score
            for match in REGEX["institution_label"].finditer(block.text):
                alias = match.group(0).strip(" |,，;；:：()（）[]【】-")
                if not 2 <= len(alias) <= MAX_INSTITUTION_ALIAS_LENGTH:
                    continue
                identity = (contact.broker_ssot_key, normalize_alias(alias))
                if identity in seen:
                    continue
                seen.add(identity)
                status = candidate_alias_status(
                    contact.broker_ssot_key,
                    alias,
                    confidence,
                    deterministic,
                    alias_index,
                )
                evidence_raw = (
                    f"{contact.broker_ssot_key}|{alias}|{contact.domain}|"
                    f"{block.page_number}|{block.line_number}|{classify_text_zone(block)}"
                )
                candidates.append(AliasCandidate(
                    broker_ssot_key=contact.broker_ssot_key,
                    alias=alias,
                    source_domain=contact.domain,
                    page_number=block.page_number,
                    line_number=block.line_number,
                    zone=classify_text_zone(block),
                    confidence=confidence,
                    deterministic_domain=deterministic,
                    status=status,
                    evidence_hash=hashlib.sha256(evidence_raw.encode("utf-8")).hexdigest()[:16],
                ))
    return candidates


def build_broker_alias_overlay(candidates: Sequence[AliasCandidate]) -> Dict[str, BrokerContract]:
    """只套用高信心 OVERLAY_APPLIED；canonical Registry 保持不變。"""

    overlay = dict(VIA_ALL_BROKER_SSOT_REGISTRY)
    for candidate in candidates:
        if candidate.status != AliasStatus.OVERLAY_APPLIED:
            continue
        contract = overlay[candidate.broker_ssot_key]
        if normalize_alias(candidate.alias) in {normalize_alias(alias) for alias in contract_aliases(contract)}:
            continue
        overlay[candidate.broker_ssot_key] = contract.model_copy(
            update={"aliases": [*contract.aliases, candidate.alias]}
        )
    errors = validate_registry("BROKER_ALIAS_OVERLAY", overlay)
    if errors:
        raise ValueError("Alias overlay 驗證失敗：\n- " + "\n- ".join(errors))
    return overlay


def analyze_contact_document(source: Union[str, Sequence[TextBlock]]) -> DocumentExtractionResult:
    """執行聯絡資訊、券商、評等、版面與同義字 overlay 完整流程。"""

    blocks = coerce_text_blocks(source)
    canonical_text = "\n".join(block.text for block in blocks)
    trace_id = "CONTACT-" + hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()[:16]
    contacts = extract_contacts(blocks)
    broker_mentions, rating_mentions = extract_document_mentions(blocks)
    broker_rating_links, link_warnings = link_brokers_to_ratings(
        broker_mentions, rating_mentions, contacts
    )
    candidates = discover_alias_candidates(contacts, blocks)
    full_overlay = build_broker_alias_overlay(candidates)
    overlay = {
        key: contract for key, contract in full_overlay.items()
        if contract != VIA_ALL_BROKER_SSOT_REGISTRY[key]
    }
    warnings: List[str] = list(link_warnings)
    if not contacts:
        warnings.append("NO_EMAIL_ANCHOR")
    if any(candidate.status == AliasStatus.HUMAN_REVIEW_ONLY for candidate in candidates):
        warnings.append("ALIAS_CANDIDATE_REQUIRES_REVIEW")
    if any(candidate.status == AliasStatus.REJECTED_CONFLICT for candidate in candidates):
        warnings.append("ALIAS_CONFLICT_REJECTED")
    return DocumentExtractionResult(
        trace_id=trace_id,
        contacts=contacts,
        broker_mentions=broker_mentions,
        rating_mentions=rating_mentions,
        broker_rating_links=broker_rating_links,
        alias_candidates=candidates,
        alias_overlay=overlay,
        warnings=warnings,
    )


# =============================================================================
# 10. SSOT 驗證與輸出函式
# =============================================================================

def validate_registry(name: str, registry: Mapping[str, ContractT]) -> List[str]:
    """驗證字典鍵、契約鍵、別名完整性與別名唯一性。"""

    errors: List[str] = []
    for key, contract in registry.items():
        if key != contract.ssot_key:
            errors.append(f"{name}: dict key={key} 與 ssot_key={contract.ssot_key} 不一致")
        explicit_aliases = [normalize_alias(alias) for alias in getattr(contract, "aliases")]
        if any(not alias for alias in explicit_aliases):
            errors.append(f"{name}.{key}: aliases 含空白值")
        if len(explicit_aliases) != len(set(explicit_aliases)):
            errors.append(f"{name}.{key}: aliases 清單內有重複別名")
    try:
        build_alias_index(registry)
    except ValueError as exc:
        errors.append(f"{name}: {exc}")
    return errors


def validate_all_ssot() -> None:
    """驗證全部 Registry；任何問題以單一例外完整列出。"""

    errors: List[str] = []
    registries = {
        "ALL_BROKERS": VIA_ALL_BROKER_SSOT_REGISTRY,
        "RESEARCH_FIELDS": VIA_RESEARCH_FIELD_SSOT_REGISTRY,
        "BROKER_RATINGS": VIA_BROKER_RATING_SSOT_REGISTRY,
    }
    for name, registry in registries.items():
        errors.extend(validate_registry(name, registry))
    for key, contract in VIA_REGEX_SSOT_REGISTRY.items():
        if key != key.casefold():
            errors.append(f"REGEX.{key}: registry key 必須為 lower_snake_case")
        try:
            compiled = contract.compile()
        except re.error as exc:
            errors.append(f"REGEX.{key}: 無法編譯：{exc}")
            continue
        for example in contract.examples:
            if compiled.search(example) is None:
                errors.append(f"REGEX.{key}: 正向範例未命中：{example!r}")
    for domain, contract in VIA_DOMAIN_SSOT_REGISTRY.items():
        if domain != contract.domain or domain != normalize_domain(domain):
            errors.append(f"DOMAIN.{domain}: registry key 與標準網域不一致")
        if REGEX["domain"].fullmatch(domain) is None:
            errors.append(f"DOMAIN.{domain}: 網域格式不合法")
        if contract.broker_ssot_key and contract.broker_ssot_key not in VIA_ALL_BROKER_SSOT_REGISTRY:
            errors.append(f"DOMAIN.{domain}: 未知 broker_ssot_key={contract.broker_ssot_key}")
    rating_codes = [int(contract.code) for contract in VIA_BROKER_RATING_SSOT_REGISTRY.values()]
    if sorted(rating_codes) != list(range(6)):
        errors.append(f"BROKER_RATINGS: 評等碼必須完整且唯一涵蓋 0–5，目前為 {sorted(rating_codes)}")
    if errors:
        raise ValueError("SSOT 驗證失敗：\n- " + "\n- ".join(errors))


def serialize_registry(registry: Mapping[str, ContractT]) -> Dict[str, object]:
    """將 Pydantic Registry 轉成可序列化字典。"""

    return {key: contract.model_dump(mode="json") for key, contract in registry.items()}


def build_ssot_payload() -> Dict[str, object]:
    """建立完整 SSOT 交換格式。"""

    validate_all_ssot()
    return {
        "schema": "VIA_FINANCIAL_INSTITUTION_SSOT",
        "version": SSOT_VERSION,
        "key_migration_map": KEY_MIGRATION_MAP,
        "alias_governance": {
            "canonical_write_mode": "READ_ONLY",
            "automatic_update_target": "RUN_LOCAL_OVERLAY",
            "automatic_threshold": AUTO_ALIAS_OVERLAY_THRESHOLD,
            "conflicts": "REJECTED_CONFLICT",
            "low_confidence": "HUMAN_REVIEW_ONLY",
        },
        "registries": {
            "domestic_brokers": serialize_registry(VIA_DOMESTIC_BROKER_SSOT_REGISTRY),
            "foreign_brokers": serialize_registry(VIA_FOREIGN_BROKER_SSOT_REGISTRY),
            "regex": serialize_registry(VIA_REGEX_SSOT_REGISTRY),
            "domains": serialize_registry(VIA_DOMAIN_SSOT_REGISTRY),
            "research_fields": serialize_registry(VIA_RESEARCH_FIELD_SSOT_REGISTRY),
            "broker_ratings": serialize_registry(VIA_BROKER_RATING_SSOT_REGISTRY),
        },
    }


def export_ssot_json(output_path: Path) -> Path:
    """輸出 UTF-8 JSON，保留繁體中文且採原子替換。"""

    target = output_path.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    payload = build_ssot_payload()
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=DEFAULT_JSON_INDENT) + "\n",
        encoding=DEFAULT_EXPORT_ENCODING,
    )
    temporary.replace(target)
    return target


# =============================================================================
# 11. 可直接執行的自我測試
# =============================================================================

def run_self_test() -> Dict[str, int]:
    """執行 SSOT、Regex、聯絡人、版面關聯、overlay 與消歧測試。"""

    validate_all_ssot()
    sample_blocks = [
        TextBlock(
            text="Appendix — Analyst Contacts", page_number=12, line_number=1,
            font_size=7, median_font_size=10, is_appendix=True,
        ),
        TextBlock(
            text="Morgan Stanley Research", page_number=12, line_number=2,
            font_size=7, median_font_size=10, is_appendix=True,
        ),
        TextBlock(
            text="Analyst: John Smith | 王小明", page_number=12, line_number=3,
            font_size=7, median_font_size=10, is_appendix=True,
        ),
        TextBlock(
            text="john.smith@morganstanley.com | +852 2123 4567",
            page_number=12, line_number=4, font_size=7, median_font_size=10,
            y_ratio=0.90, is_appendix=True,
        ),
        TextBlock(
            text="Rating: Strong Buy | Target Price: 250", page_number=12,
            line_number=5, font_size=7, median_font_size=10, is_appendix=True,
        ),
    ]
    extraction = analyze_contact_document(sample_blocks)
    phone_only = analyze_contact_document(
        "分析師：Maria Paul\n電話：02-2345-6789\n凱基證券\n評等：Sector Perform"
    )
    email_contact = extraction.contacts[0]
    phone_contact = phone_only.contacts[0]
    assertions = {
        "大摩": (resolve_broker("大摩") or BrokerContract).ssot_key == "MS",
        "BOA_migration": (resolve_broker("BOA") or BrokerContract).ssot_key == "BOFA",
        "MCQ_migration": (resolve_broker("MCQ") or BrokerContract).ssot_key == "MACQUARIE",
        "target_price": (resolve_research_field("合理股價") or ResearchFieldContract).code == "TP",
        "under_review": int((resolve_rating("Under Review") or RatingContract).code) == 0,
        "sector_perform": int((resolve_rating("Sector Perform") or RatingContract).code) == 3,
        "reduce": int((resolve_rating("減持") or RatingContract).code) == 4,
        "strong_buy_precedence": [item.ssot_key for item in extract_ratings("GS: Strong Buy; TP 250")] == ["STRONG_BUY"],
        "broker_extract": {item.ssot_key for item in extract_brokers("大摩與凱基投顧同步調高目標價")} == {"MS", "KGI"},
        "subdomain_resolution": (resolve_domain("research.ubs.com") or DomainContract).broker_ssot_key == "UBS",
        "email_type": detect_type("john.smith@morganstanley.com") == "Email",
        "taiwan_phone_type": detect_type("02-2345-6789") == "TaiwanPhone",
        "hong_kong_phone_type": detect_type("+852 2123 4567") == "HongKongPhone",
        "email_name_match": email_contact.matched_english_name == "John Smith" and email_contact.name_match_score == 1.0,
        "nearby_chinese_name": email_contact.matched_chinese_name == "王小明",
        "domain_to_broker": email_contact.broker_ssot_key == "MS",
        "nearby_phone": email_contact.phones == ["+85221234567"],
        "appendix_small_print": email_contact.zone == "APPENDIX_SMALL_PRINT",
        "nearby_rating": email_contact.rating_keys == ["STRONG_BUY"],
        "broker_rating_link": extraction.broker_rating_links[0].broker_ssot_key == "MS",
        "alias_overlay_applied": list(extraction.alias_overlay) == ["MS"],
        "canonical_unchanged": "Morgan Stanley Research" not in VIA_ALL_BROKER_SSOT_REGISTRY["MS"].aliases,
        "phone_overlap_dedup": phone_contact.phones == ["0223456789"] and len(phone_only.contacts) == 1,
        "phone_anchor_name": phone_contact.anchor_type == "PHONE" and phone_contact.matched_english_name == "Maria Paul",
    }
    failed = [name for name, passed in assertions.items() if not passed]
    if failed:
        raise AssertionError("自我測試失敗：" + ", ".join(failed))
    return {
        "domestic_brokers": len(VIA_DOMESTIC_BROKER_SSOT_REGISTRY),
        "foreign_brokers": len(VIA_FOREIGN_BROKER_SSOT_REGISTRY),
        "research_fields": len(VIA_RESEARCH_FIELD_SSOT_REGISTRY),
        "ratings": len(VIA_BROKER_RATING_SSOT_REGISTRY),
        "regex_rules": len(VIA_REGEX_SSOT_REGISTRY),
        "domain_rules": len(VIA_DOMAIN_SSOT_REGISTRY),
        "assertions_passed": len(assertions),
    }


def main() -> None:
    result = run_self_test()
    print(json.dumps({"status": "PASS", **result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
