/** VRN knowledge SSOT. 陸券已刪；GS=高盛；MS/大摩；JPM/小摩；「摩根」刪。 */
export type BrokerHit = { alias: string; name: string; canonical: string; abbr: string };

export const YEAR_SUSPECT = /^(202[1-9]|2030)$/;
export const BASIC_INFO_COLUMNS = [
	"report_date",
	"report_code",
	"filename",
	"broker",
	"analyst",
	"ticker",
	"yfinance_ticker",
	"bloomberg_ticker",
	"name",
	"name_en",
	"rating",
	"rating_cat",
	"target_price",
	"consensus_target_high",
	"consensus_target_low",
	"consensus_target_mean",
	"consensus_target_median",
	"consensus_rating",
	"consensus_rating_mean",
	"analyst_count",
	"analyst_strong_buy",
	"analyst_buy",
	"analyst_hold",
	"analyst_sell",
	"analyst_strong_sell",
	"adj_close",
	"adj_close_date",
	"upside_pct",
	"upside_source",
	"summary"
];
export const FINANCIAL_DATA_COLUMNS = [
	"report_date",
	"report_code",
	"filename",
	"broker",
	"ticker",
	"yfinance_ticker",
	"bloomberg_ticker",
	"name",
	"category",
	"time_period",
	"data_label",
	"unit",
	"value",
	"source",
	"verification_confidence"
];
export const METHOD_PILLARS = [
	"五區抽取",
	"雙層保存",
	"官方對照",
	"算術勾稽",
	"證據仲裁"
];
export const DIGEST_SLOTS = [
	{
		"id": "K1",
		"zh": "潛在上漲空間",
		"en": "Upside vs adj close"
	},
	{
		"id": "K2",
		"zh": "稀釋EPS n～n+3",
		"en": "Diluted EPS n..n+3"
	},
	{
		"id": "K3",
		"zh": "首頁其餘甲",
		"en": "Page-1 remainder A"
	},
	{
		"id": "K4",
		"zh": "首頁其餘乙",
		"en": "Page-1 remainder B"
	},
	{
		"id": "K5",
		"zh": "風險因子",
		"en": "Risk Factors"
	}
];
export const NON_STOCK = [
	"Insights",
	"Thoughts on",
	"展望",
	"日股",
	"早報",
	"晨報",
	"晨會",
	"晨訊",
	"晨間",
	"期貨",
	"港股",
	"產業",
	"盤前",
	"盤勢",
	"美股",
	"解盤",
	"講座",
	"趨勢",
	"完善化",
	"Roadmap",
	"Minutes",
	"Brief"
];
export const STMT = {
	"BALANCE_SHEET": {
		"zh": "資產負債表",
		"en": "Balance Sheet"
	},
	"INCOME_STATEMENT": {
		"zh": "損益表",
		"en": "Income Statement"
	},
	"CASH_FLOW": {
		"zh": "現金流量表",
		"en": "Cash Flow Statement"
	},
	"EQUITY_CHANGE": {
		"zh": "權益變動表",
		"en": "Statement of Changes in Equity"
	},
	"RATIO": {
		"zh": "財務比率",
		"en": "Financial Ratios"
	},
	"PER_SHARE": {
		"zh": "每股分析",
		"en": "Per-Share Metrics"
	},
	"NOTES": {
		"zh": "附註",
		"en": "Notes"
	}
};
export const ANNUAL = {
	"revenue": {
		"block": "IS",
		"zh": "營業收入合計",
		"en": "Total Revenue",
		"fin": "revenue"
	},
	"gross_profit": {
		"block": "IS",
		"zh": "營業毛利(利益)",
		"en": "Gross Profit",
		"fin": "gross_profit"
	},
	"operating_income": {
		"block": "IS",
		"zh": "營業利益(損失)",
		"en": "Operating Income",
		"fin": "operating_income"
	},
	"net_income": {
		"block": "IS",
		"zh": "母公司業主淨利",
		"en": "Net Income Common Stockholders",
		"fin": "net_income"
	},
	"cash": {
		"block": "BS",
		"zh": "現金及約當現金",
		"en": "Cash And Cash Equivalents",
		"fin": "cash"
	},
	"assets": {
		"block": "BS",
		"zh": "資產總額",
		"en": "Total Assets",
		"fin": "assets"
	},
	"equity_total": {
		"block": "BS",
		"zh": "權益總額",
		"en": "Total Equity",
		"fin": "equity_total"
	},
	"cfo": {
		"block": "CF",
		"zh": "營業活動之淨現金流入(流出)",
		"en": "Operating Cash Flow",
		"fin": "cfo"
	},
	"fcf": {
		"block": "CF",
		"zh": "自由現金流量",
		"en": "Free Cash Flow",
		"fin": "fcf"
	},
	"diluted_eps": {
		"block": "PERSHARE",
		"zh": "稀釋每股盈餘合計",
		"en": "Diluted EPS",
		"fin": "diluted_eps"
	}
};
export const CANON = {
	"basic_eps": {
		"zh": "基本每股盈餘",
		"en": "Basic EPS",
		"statement": "PER_SHARE"
	},
	"capex": {
		"zh": "購置不動產廠房設備",
		"en": "Capital Expenditure (CapEx)",
		"statement": "CASH_FLOW"
	},
	"cash": {
		"zh": "現金及約當現金",
		"en": "Cash and Cash Equivalents",
		"statement": "BALANCE_SHEET"
	},
	"cogs": {
		"zh": "營業成本",
		"en": "Cost of Revenue",
		"statement": "INCOME_STATEMENT"
	},
	"diluted_eps": {
		"zh": "稀釋每股盈餘",
		"en": "Diluted EPS",
		"statement": "PER_SHARE"
	},
	"eps": {
		"zh": "基本每股盈餘",
		"en": "Basic EPS",
		"statement": "PER_SHARE"
	},
	"fcf": {
		"zh": "自由現金流",
		"en": "Free Cash Flow (FCF)",
		"statement": "CASH_FLOW"
	},
	"gross_profit": {
		"zh": "營業毛利",
		"en": "Gross Profit",
		"statement": "INCOME_STATEMENT"
	},
	"net_income": {
		"zh": "本期淨利",
		"en": "Net Income",
		"statement": "INCOME_STATEMENT"
	},
	"ocf": {
		"zh": "營業現金流",
		"en": "Operating Cash Flow (OCF)",
		"statement": "CASH_FLOW"
	},
	"operating_income": {
		"zh": "營業利益",
		"en": "Operating Income",
		"statement": "INCOME_STATEMENT"
	},
	"revenue": {
		"zh": "營業收入",
		"en": "Revenue",
		"statement": "INCOME_STATEMENT"
	},
	"total_assets": {
		"zh": "資產總計",
		"en": "Total Assets",
		"statement": "BALANCE_SHEET"
	},
	"total_equity": {
		"zh": "權益總計",
		"en": "Total Equity",
		"statement": "BALANCE_SHEET"
	}
};
export const PARSER_RATINGS = {
	"strong_buy": [
		"強力買進",
		"strong buy",
		"strong-buy"
	],
	"buy": [
		"買進",
		"買入",
		"buy",
		"overweight",
		"outperform",
		"增持",
		"加碼"
	],
	"hold": [
		"中立",
		"持有",
		"hold",
		"neutral",
		"equal-weight",
		"market perform"
	],
	"sell": [
		"賣出",
		"sell",
		"underweight",
		"underperform",
		"減碼"
	],
	"not_rated": [
		"未評等",
		"無評等",
		"not rated",
		"nr"
	]
} as const;
export const BROKER_PREFIX = {
	"MS": "Morgan Stanley",
	"GS": "Goldman Sachs",
	"JP": "J.P. Morgan",
	"Citi": "Citigroup",
	"CLST": "CLSA Taiwan",
	"Daiwa": "Daiwa 大和",
	"UBS": "UBS",
	"MQ": "Macquarie 麥格理",
	"KGI": "凱基投顧",
	"CTBC": "中國信託證券"
} as const;
export const BROKERS: BrokerHit[] = [
  {
    "alias": "First Financial Holding",
    "name": "FFHC",
    "canonical": "FFHC",
    "abbr": "FFHC"
  },
  {
    "alias": "Capital Securities Corp",
    "name": "CSC",
    "canonical": "CSC",
    "abbr": "CSC"
  },
  {
    "alias": "daiwa capital markets",
    "name": "Daiwa",
    "canonical": "Daiwa",
    "abbr": "Daiwa"
  },
  {
    "alias": "president securities",
    "name": "統一",
    "canonical": "統一",
    "abbr": "統一"
  },
  {
    "alias": "Taishin Securities",
    "name": "台新",
    "canonical": "台新",
    "abbr": "TSC"
  },
  {
    "alias": "SinoPac Securities",
    "name": "永豐",
    "canonical": "永豐",
    "abbr": "SJP"
  },
  {
    "alias": "Capital Securities",
    "name": "群益",
    "canonical": "群益",
    "abbr": "CP"
  },
  {
    "alias": "Yuanta Securities",
    "name": "元大",
    "canonical": "元大",
    "abbr": "YT"
  },
  {
    "alias": "Cathay Securities",
    "name": "國泰",
    "canonical": "國泰",
    "abbr": "CT"
  },
  {
    "alias": "Nomura Securities",
    "name": "NMR",
    "canonical": "野村",
    "abbr": "NOM"
  },
  {
    "alias": "Macquarie Capital",
    "name": "Macquarie",
    "canonical": "Macquarie",
    "abbr": "MQ"
  },
  {
    "alias": "morganstanley.com",
    "name": "MS",
    "canonical": "MS",
    "abbr": "MS"
  },
  {
    "alias": "Fubon Securities",
    "name": "富邦",
    "canonical": "富邦",
    "abbr": "FB"
  },
  {
    "alias": "E.SUN Securities",
    "name": "玉山",
    "canonical": "玉山",
    "abbr": "ESB"
  },
  {
    "alias": "First Securities",
    "name": "第一",
    "canonical": "第一",
    "abbr": "FCB"
  },
  {
    "alias": "Daiwa Securities",
    "name": "DAIWA",
    "canonical": "大和",
    "abbr": "DAI"
  },
  {
    "alias": "goldmansachs.com",
    "name": "GS",
    "canonical": "GS",
    "abbr": "GS"
  },
  {
    "alias": "cathaysec.com.tw",
    "name": "CATHAY",
    "canonical": "CATHAY",
    "abbr": "CATHAY"
  },
  {
    "alias": "Mega Securities",
    "name": "兆豐",
    "canonical": "兆豐",
    "abbr": "MKC"
  },
  {
    "alias": "Bank of America",
    "name": "BAML",
    "canonical": "美林",
    "abbr": "ML"
  },
  {
    "alias": "KGI Securities",
    "name": "凱基",
    "canonical": "凱基",
    "abbr": "KGI"
  },
  {
    "alias": "Morgan Stanley",
    "name": "MS",
    "canonical": "摩根士丹利",
    "abbr": "MS"
  },
  {
    "alias": "JPMorgan Chase",
    "name": "JPM",
    "canonical": "摩根大通",
    "abbr": "JPM"
  },
  {
    "alias": "capital.com.tw",
    "name": "CSC",
    "canonical": "CSC",
    "abbr": "CSC"
  },
  {
    "alias": "entrust.com.tw",
    "name": "HNCB",
    "canonical": "HNCB",
    "abbr": "HNCB"
  },
  {
    "alias": "megasec.com.tw",
    "name": "MEGA",
    "canonical": "MEGA",
    "abbr": "MEGA"
  },
  {
    "alias": "Merrill Lynch",
    "name": "BAML",
    "canonical": "美林",
    "abbr": "ML"
  },
  {
    "alias": "Goldman Sachs",
    "name": "GS",
    "canonical": "高盛",
    "abbr": "GS"
  },
  {
    "alias": "Deutsche Bank",
    "name": "DB",
    "canonical": "德意志",
    "abbr": "DB"
  },
  {
    "alias": "daiwa capital",
    "name": "Daiwa",
    "canonical": "Daiwa",
    "abbr": "Daiwa"
  },
  {
    "alias": "citigroup.com",
    "name": "CITI",
    "canonical": "CITI",
    "abbr": "CITI"
  },
  {
    "alias": "UBS Group AG",
    "name": "UBS",
    "canonical": "瑞銀",
    "abbr": "UBS"
  },
  {
    "alias": "jpmorgan.com",
    "name": "JPM",
    "canonical": "JPM",
    "abbr": "JPM"
  },
  {
    "alias": "J.P. Morgan",
    "name": "J.P. Morgan",
    "canonical": "J.P. Morgan",
    "abbr": "JP"
  },
  {
    "alias": "ctbcsec.com",
    "name": "CTBC",
    "canonical": "CTBC",
    "abbr": "CTBC"
  },
  {
    "alias": "JP Morgan",
    "name": "JPM",
    "canonical": "摩根大通",
    "abbr": "JPM"
  },
  {
    "alias": "UBS Group",
    "name": "UBS",
    "canonical": "瑞銀",
    "abbr": "UBS"
  },
  {
    "alias": "Citigroup",
    "name": "CITI",
    "canonical": "花旗",
    "abbr": "CITI"
  },
  {
    "alias": "Macquarie",
    "name": "Macquarie",
    "canonical": "Macquarie",
    "abbr": "MQ"
  },
  {
    "alias": "President",
    "name": "President",
    "canonical": "President",
    "abbr": "President"
  },
  {
    "alias": "JPMorgan",
    "name": "JPM",
    "canonical": "摩根大通",
    "abbr": "JPM"
  },
  {
    "alias": "美國銀行美林證券",
    "name": "BAML",
    "canonical": "美林",
    "abbr": "ML"
  },
  {
    "alias": "Megabank",
    "name": "Megabank",
    "canonical": "Megabank",
    "abbr": "Megabank"
  },
  {
    "alias": "citi.com",
    "name": "CITI",
    "canonical": "CITI",
    "abbr": "CITI"
  },
  {
    "alias": "clsa.com",
    "name": "CSC",
    "canonical": "CSC",
    "abbr": "CSC"
  },
  {
    "alias": "Taishin",
    "name": "台新",
    "canonical": "台新",
    "abbr": "TSC"
  },
  {
    "alias": "SinoPac",
    "name": "永豐",
    "canonical": "永豐",
    "abbr": "SJP"
  },
  {
    "alias": "Capital",
    "name": "群益",
    "canonical": "群益",
    "abbr": "CP"
  },
  {
    "alias": "Goldman",
    "name": "GS",
    "canonical": "高盛",
    "abbr": "GS"
  },
  {
    "alias": "hua nan",
    "name": "華南",
    "canonical": "華南",
    "abbr": "華南"
  },
  {
    "alias": "Yuanta",
    "name": "元大",
    "canonical": "元大",
    "abbr": "YT"
  },
  {
    "alias": "Cathay",
    "name": "國泰",
    "canonical": "國泰",
    "abbr": "CT"
  },
  {
    "alias": "Nomura",
    "name": "NMR",
    "canonical": "野村",
    "abbr": "NOM"
  },
  {
    "alias": "HuaNan",
    "name": "HuaNan",
    "canonical": "HuaNan",
    "abbr": "HuaNan"
  },
  {
    "alias": "群益金鼎證券",
    "name": "CSC",
    "canonical": "CSC",
    "abbr": "CSC"
  },
  {
    "alias": "gs.com",
    "name": "GS",
    "canonical": "GS",
    "abbr": "GS"
  },
  {
    "alias": "Fubon",
    "name": "富邦",
    "canonical": "富邦",
    "abbr": "FB"
  },
  {
    "alias": "永豐金證券",
    "name": "永豐",
    "canonical": "永豐",
    "abbr": "SJP"
  },
  {
    "alias": "E.SUN",
    "name": "玉山",
    "canonical": "玉山",
    "abbr": "ESB"
  },
  {
    "alias": "First",
    "name": "第一",
    "canonical": "第一",
    "abbr": "FCB"
  },
  {
    "alias": "第一金證券",
    "name": "第一",
    "canonical": "第一",
    "abbr": "FCB"
  },
  {
    "alias": "第一金投顧",
    "name": "第一",
    "canonical": "第一",
    "abbr": "FCB"
  },
  {
    "alias": "摩根士丹利",
    "name": "MS",
    "canonical": "摩根士丹利",
    "abbr": "MS"
  },
  {
    "alias": "摩根史坦利",
    "name": "MS",
    "canonical": "摩根士丹利",
    "abbr": "MS"
  },
  {
    "alias": "德意志銀行",
    "name": "DB",
    "canonical": "德意志",
    "abbr": "DB"
  },
  {
    "alias": "DAIWA",
    "name": "DAIWA",
    "canonical": "大和",
    "abbr": "DAI"
  },
  {
    "alias": "麥格理資本",
    "name": "Macquarie",
    "canonical": "Macquarie",
    "abbr": "MQ"
  },
  {
    "alias": "元大證券",
    "name": "元大",
    "canonical": "元大",
    "abbr": "YT"
  },
  {
    "alias": "元大投顧",
    "name": "元大",
    "canonical": "元大",
    "abbr": "YT"
  },
  {
    "alias": "元大金控",
    "name": "元大",
    "canonical": "元大",
    "abbr": "YT"
  },
  {
    "alias": "凱基證券",
    "name": "凱基",
    "canonical": "凱基",
    "abbr": "KGI"
  },
  {
    "alias": "凱基投顧",
    "name": "凱基",
    "canonical": "凱基",
    "abbr": "KGI"
  },
  {
    "alias": "富邦證券",
    "name": "富邦",
    "canonical": "富邦",
    "abbr": "FB"
  },
  {
    "alias": "富邦投顧",
    "name": "富邦",
    "canonical": "富邦",
    "abbr": "FB"
  },
  {
    "alias": "富邦金控",
    "name": "富邦",
    "canonical": "富邦",
    "abbr": "FB"
  },
  {
    "alias": "國泰證券",
    "name": "國泰",
    "canonical": "國泰",
    "abbr": "CT"
  },
  {
    "alias": "國泰投顧",
    "name": "國泰",
    "canonical": "國泰",
    "abbr": "CT"
  },
  {
    "alias": "國泰金控",
    "name": "國泰",
    "canonical": "國泰",
    "abbr": "CT"
  },
  {
    "alias": "CTBC",
    "name": "CTBC",
    "canonical": "中信",
    "abbr": "CTBC"
  },
  {
    "alias": "台新證券",
    "name": "台新",
    "canonical": "台新",
    "abbr": "TSC"
  },
  {
    "alias": "台新投顧",
    "name": "台新",
    "canonical": "台新",
    "abbr": "TSC"
  },
  {
    "alias": "永豐投顧",
    "name": "永豐",
    "canonical": "永豐",
    "abbr": "SJP"
  },
  {
    "alias": "ESUN",
    "name": "玉山",
    "canonical": "玉山",
    "abbr": "ESB"
  },
  {
    "alias": "玉山證券",
    "name": "玉山",
    "canonical": "玉山",
    "abbr": "ESB"
  },
  {
    "alias": "玉山投顧",
    "name": "玉山",
    "canonical": "玉山",
    "abbr": "ESB"
  },
  {
    "alias": "HNSC",
    "name": "華南",
    "canonical": "華南",
    "abbr": "HNSC"
  },
  {
    "alias": "Mega",
    "name": "兆豐",
    "canonical": "兆豐",
    "abbr": "MKC"
  },
  {
    "alias": "兆豐證券",
    "name": "兆豐",
    "canonical": "兆豐",
    "abbr": "MKC"
  },
  {
    "alias": "兆豐投顧",
    "name": "兆豐",
    "canonical": "兆豐",
    "abbr": "MKC"
  },
  {
    "alias": "群益證券",
    "name": "群益",
    "canonical": "群益",
    "abbr": "CP"
  },
  {
    "alias": "群益投顧",
    "name": "群益",
    "canonical": "群益",
    "abbr": "CP"
  },
  {
    "alias": "摩根大通",
    "name": "JPM",
    "canonical": "摩根大通",
    "abbr": "JPM"
  },
  {
    "alias": "JP摩根",
    "name": "JPM",
    "canonical": "摩根大通",
    "abbr": "JPM"
  },
  {
    "alias": "瑞銀集團",
    "name": "UBS",
    "canonical": "瑞銀",
    "abbr": "UBS"
  },
  {
    "alias": "BAML",
    "name": "BAML",
    "canonical": "美林",
    "abbr": "ML"
  },
  {
    "alias": "BofA",
    "name": "BAML",
    "canonical": "美林",
    "abbr": "ML"
  },
  {
    "alias": "美銀美林",
    "name": "BAML",
    "canonical": "美林",
    "abbr": "ML"
  },
  {
    "alias": "CITI",
    "name": "CITI",
    "canonical": "花旗",
    "abbr": "CITI"
  },
  {
    "alias": "花旗銀行",
    "name": "CITI",
    "canonical": "花旗",
    "abbr": "CITI"
  },
  {
    "alias": "花旗集團",
    "name": "CITI",
    "canonical": "花旗",
    "abbr": "CITI"
  },
  {
    "alias": "高盛集團",
    "name": "GS",
    "canonical": "高盛",
    "abbr": "GS"
  },
  {
    "alias": "野村證券",
    "name": "NMR",
    "canonical": "野村",
    "abbr": "NOM"
  },
  {
    "alias": "野村控股",
    "name": "NMR",
    "canonical": "野村",
    "abbr": "NOM"
  },
  {
    "alias": "大和證券",
    "name": "DAIWA",
    "canonical": "大和",
    "abbr": "DAI"
  },
  {
    "alias": "CLSA",
    "name": "里昂",
    "canonical": "里昂",
    "abbr": "CLSA"
  },
  {
    "alias": "CLST",
    "name": "CLST",
    "canonical": "CLST",
    "abbr": "CLST"
  },
  {
    "alias": "國泰證期",
    "name": "Cathay",
    "canonical": "Cathay",
    "abbr": "Cathay"
  },
  {
    "alias": "統一投顧",
    "name": "President",
    "canonical": "President",
    "abbr": "President"
  },
  {
    "alias": "統一證券",
    "name": "President",
    "canonical": "President",
    "abbr": "President"
  },
  {
    "alias": "華南投顧",
    "name": "HuaNan",
    "canonical": "HuaNan",
    "abbr": "HuaNan"
  },
  {
    "alias": "華南永昌",
    "name": "HuaNan",
    "canonical": "HuaNan",
    "abbr": "HuaNan"
  },
  {
    "alias": "中國信託",
    "name": "CTBC",
    "canonical": "CTBC",
    "abbr": "CTBC"
  },
  {
    "alias": "大和資本",
    "name": "Daiwa",
    "canonical": "Daiwa",
    "abbr": "Daiwa"
  },
  {
    "alias": "FFHC",
    "name": "FFHC",
    "canonical": "FFHC",
    "abbr": "FFHC"
  },
  {
    "alias": "群益金鼎",
    "name": "CSC",
    "canonical": "CSC",
    "abbr": "CSC"
  },
  {
    "alias": "HNCB",
    "name": "HNCB",
    "canonical": "HNCB",
    "abbr": "HNCB"
  },
  {
    "alias": "中信投顧",
    "name": "CTBC",
    "canonical": "中信",
    "abbr": "CTBC"
  },
  {
    "alias": "KGI",
    "name": "凱基",
    "canonical": "凱基",
    "abbr": "KGI"
  },
  {
    "alias": "TSC",
    "name": "台新",
    "canonical": "台新",
    "abbr": "TSC"
  },
  {
    "alias": "SJP",
    "name": "永豐",
    "canonical": "永豐",
    "abbr": "SJP"
  },
  {
    "alias": "ESB",
    "name": "玉山",
    "canonical": "玉山",
    "abbr": "ESB"
  },
  {
    "alias": "MKC",
    "name": "兆豐",
    "canonical": "兆豐",
    "abbr": "MKC"
  },
  {
    "alias": "FCB",
    "name": "第一",
    "canonical": "第一",
    "abbr": "FCB"
  },
  {
    "alias": "TCB",
    "name": "合庫",
    "canonical": "合庫",
    "abbr": "TCB"
  },
  {
    "alias": "PSC",
    "name": "統一",
    "canonical": "統一",
    "abbr": "PSC"
  },
  {
    "alias": "JPM",
    "name": "JPM",
    "canonical": "摩根大通",
    "abbr": "JPM"
  },
  {
    "alias": "UBS",
    "name": "UBS",
    "canonical": "瑞銀",
    "abbr": "UBS"
  },
  {
    "alias": "德意志",
    "name": "DB",
    "canonical": "德意志",
    "abbr": "DB"
  },
  {
    "alias": "NMR",
    "name": "NMR",
    "canonical": "野村",
    "abbr": "NOM"
  },
  {
    "alias": "NOM",
    "name": "NMR",
    "canonical": "野村",
    "abbr": "NOM"
  },
  {
    "alias": "DAI",
    "name": "DAIWA",
    "canonical": "大和",
    "abbr": "DAI"
  },
  {
    "alias": "麥格理",
    "name": "麥格理",
    "canonical": "麥格理",
    "abbr": "MAQ"
  },
  {
    "alias": "MAQ",
    "name": "麥格理",
    "canonical": "麥格理",
    "abbr": "MAQ"
  },
  {
    "alias": "中信金",
    "name": "CTBC",
    "canonical": "CTBC",
    "abbr": "CTBC"
  },
  {
    "alias": "第一金",
    "name": "FFHC",
    "canonical": "FFHC",
    "abbr": "FFHC"
  },
  {
    "alias": "CSC",
    "name": "CSC",
    "canonical": "CSC",
    "abbr": "CSC"
  },
  {
    "alias": "元大",
    "name": "元大",
    "canonical": "元大",
    "abbr": "YT"
  },
  {
    "alias": "YT",
    "name": "元大",
    "canonical": "元大",
    "abbr": "YT"
  },
  {
    "alias": "凱基",
    "name": "凱基",
    "canonical": "凱基",
    "abbr": "KGI"
  },
  {
    "alias": "富邦",
    "name": "富邦",
    "canonical": "富邦",
    "abbr": "FB"
  },
  {
    "alias": "FB",
    "name": "富邦",
    "canonical": "富邦",
    "abbr": "FB"
  },
  {
    "alias": "國泰",
    "name": "國泰",
    "canonical": "國泰",
    "abbr": "CT"
  },
  {
    "alias": "CT",
    "name": "國泰",
    "canonical": "國泰",
    "abbr": "CT"
  },
  {
    "alias": "中信",
    "name": "CTBC",
    "canonical": "中信",
    "abbr": "CTBC"
  },
  {
    "alias": "台新",
    "name": "台新",
    "canonical": "台新",
    "abbr": "TSC"
  },
  {
    "alias": "永豐",
    "name": "永豐",
    "canonical": "永豐",
    "abbr": "SJP"
  },
  {
    "alias": "日盛",
    "name": "日盛",
    "canonical": "日盛",
    "abbr": "JS"
  },
  {
    "alias": "JS",
    "name": "日盛",
    "canonical": "日盛",
    "abbr": "JS"
  },
  {
    "alias": "玉山",
    "name": "玉山",
    "canonical": "玉山",
    "abbr": "ESB"
  },
  {
    "alias": "華南",
    "name": "華南",
    "canonical": "華南",
    "abbr": "HNSC"
  },
  {
    "alias": "兆豐",
    "name": "兆豐",
    "canonical": "兆豐",
    "abbr": "MKC"
  },
  {
    "alias": "第一",
    "name": "第一",
    "canonical": "第一",
    "abbr": "FCB"
  },
  {
    "alias": "合庫",
    "name": "合庫",
    "canonical": "合庫",
    "abbr": "TCB"
  },
  {
    "alias": "群益",
    "name": "群益",
    "canonical": "群益",
    "abbr": "CP"
  },
  {
    "alias": "CP",
    "name": "群益",
    "canonical": "群益",
    "abbr": "CP"
  },
  {
    "alias": "統一",
    "name": "統一",
    "canonical": "統一",
    "abbr": "PSC"
  },
  {
    "alias": "大華",
    "name": "大華",
    "canonical": "大華",
    "abbr": "DH"
  },
  {
    "alias": "GS",
    "name": "GS",
    "canonical": "高盛",
    "abbr": "GS"
  },
  {
    "alias": "康和",
    "name": "康和",
    "canonical": "康和",
    "abbr": "CH"
  },
  {
    "alias": "CH",
    "name": "康和",
    "canonical": "康和",
    "abbr": "CH"
  },
  {
    "alias": "宏遠",
    "name": "宏遠",
    "canonical": "宏遠",
    "abbr": "HY"
  },
  {
    "alias": "HY",
    "name": "宏遠",
    "canonical": "宏遠",
    "abbr": "HY"
  },
  {
    "alias": "MS",
    "name": "MS",
    "canonical": "摩根士丹利",
    "abbr": "MS"
  },
  {
    "alias": "大摩",
    "name": "MS",
    "canonical": "摩根士丹利",
    "abbr": "MS"
  },
  {
    "alias": "小摩",
    "name": "JPM",
    "canonical": "摩根大通",
    "abbr": "JPM"
  },
  {
    "alias": "瑞銀",
    "name": "UBS",
    "canonical": "瑞銀",
    "abbr": "UBS"
  },
  {
    "alias": "美林",
    "name": "BAML",
    "canonical": "美林",
    "abbr": "ML"
  },
  {
    "alias": "ML",
    "name": "BAML",
    "canonical": "美林",
    "abbr": "ML"
  },
  {
    "alias": "花旗",
    "name": "CITI",
    "canonical": "花旗",
    "abbr": "CITI"
  },
  {
    "alias": "高盛",
    "name": "GS",
    "canonical": "高盛",
    "abbr": "GS"
  },
  {
    "alias": "DB",
    "name": "DB",
    "canonical": "德意志",
    "abbr": "DB"
  },
  {
    "alias": "德銀",
    "name": "DB",
    "canonical": "德意志",
    "abbr": "DB"
  },
  {
    "alias": "野村",
    "name": "NMR",
    "canonical": "野村",
    "abbr": "NOM"
  },
  {
    "alias": "大和",
    "name": "DAIWA",
    "canonical": "大和",
    "abbr": "DAI"
  },
  {
    "alias": "里昂",
    "name": "里昂",
    "canonical": "里昂",
    "abbr": "CLSA"
  },
  {
    "alias": "MQ",
    "name": "Macquarie",
    "canonical": "Macquarie",
    "abbr": "MQ"
  },
  {
    "alias": "JP",
    "name": "J.P. Morgan",
    "canonical": "J.P. Morgan",
    "abbr": "JP"
  }
];

export function matchBroker(name: string): BrokerHit | null {
	const drop = ["中信證券", "中信建投", "國泰君安", "廣發", "中金", "海通", "citic", "guotai junan", "haitong", "cicc"];
	const low = name.toLowerCase();
	if (drop.some((k) => low.includes(k.toLowerCase()))) return null;
	for (const b of BROKERS) {
		const a = b.alias;
		if (a.length < 2) continue;
		if (/\.com|@/i.test(a)) continue;
		if (a.length <= 3) {
			const esc = a.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
			if (new RegExp(`(^|[^A-Za-z0-9])${esc}([^A-Za-z0-9]|$)`, "i").test(name)) return b;
		} else if (name.toLowerCase().includes(a.toLowerCase())) return b;
	}
	return null;
}
export function classifyRating(text: string): { cat: string; word: string } | null {
	const t = text.toLowerCase();
	for (const [cat, words] of Object.entries(PARSER_RATINGS)) for (const w of words) if (t.includes(String(w).toLowerCase())) return {
		cat,
		word: String(w)
	};
	return null;
}
export function isNonStock(name: string): boolean {
	return NON_STOCK.some((k) => name.includes(k));
}
export function canonLabel(key: string): { zh: string; en: string; statement: string } {
	const c = (CANON as Record<string, { zh?: string; en?: string; statement?: string }>)[key];
	const a = (ANNUAL as Record<string, { zh?: string; en?: string; block?: string }>)[key];
	return {
		zh: c?.zh ?? a?.zh ?? key,
		en: c?.en ?? a?.en ?? key,
		statement: c?.statement ?? a?.block ?? ""
	};
}
export const KNOWLEDGE_SOURCES = [
	{
		id: "parser",
		file: "SSOT/VRN_Report_Parser_Integrated_SSOT.json",
		role: "BASIC INFO／財務欄"
	},
	{
		id: "ticker",
		file: "knowledge/VRN_TickerDate_Regex_v0100.json",
		role: "ticker／日期 regex"
	},
	{
		id: "annual",
		file: "knowledge/VRN_AnnualExtract_SSOT_v0100.json",
		role: "年報科目"
	},
	{
		id: "broker",
		file: "knowledge/VRN_Broker_Dict_v0100.json",
		role: "券商字典"
	},
	{
		id: "tri",
		file: "knowledge/VRN_Canonical_Trilingual_Fill_v0100.json",
		role: "三語 canonical"
	},
	{
		id: "digest",
		file: "knowledge/VRN_Digest_Params_v0100.json",
		role: "摘要參數"
	},
	{
		id: "findata",
		file: "knowledge/VRN_FinData_Synonym_v0100.json",
		role: "科目同義"
	},
	{
		id: "finstmt",
		file: "knowledge/VRN_FinStatement_Synonym_v0100.json",
		role: "報表層"
	},
	{
		id: "lexfill",
		file: "knowledge/VRN_Lexicon_Fill_Template_v0100.json",
		role: "詞庫模板"
	},
	{
		id: "lex",
		file: "knowledge/VRN_Lexicon_v0100.json",
		role: "K1–K6 詞庫"
	},
	{
		id: "method",
		file: "knowledge/VRN_Method_SSOT_v0100.json",
		role: "方法 def01–20"
	},
	{
		id: "rating",
		file: "knowledge/VRN_Rating_Dict_v0100.json",
		role: "評等字庫"
	}
];
