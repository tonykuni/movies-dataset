# -*- coding: utf-8 -*-
"""
VIS_VRN_Q1_AliasRoutePatch_v0100.py

Append-only supportive module generated from VRN post-close Q1 alias patch preview.

Safety:
- no DB write
- no canonical write
- no parser core rewrite
- no delete
- no deploy
- no environment mutation
"""

from __future__ import annotations

MODULE_VERSION = "VIS_VRN_Q1_AliasRoutePatch_v0100"
GENERATED_AT = "2026-06-01 21:46:52"

ELIGIBLE_SINGLE_STOCK_ALIAS_ROWS = [
    {
        'file_name': '【國泰證期研究部】神達(3706 TT)-初次評等買進(+30.4_)-大顯神威，營運騰達-20250822.pdf',
        'broker_alias': '國泰證期',
        'ticker': '3706',
        'company_alias': '【國泰證期研究部】神達',
        'report_date': '2025-08-22',
        'route_policy': 'ELIGIBLE_SINGLE_STOCK',
    },
    {
        'file_name': '3014TT-20231005.pdf',
        'broker_alias': '',
        'ticker': '3014',
        'company_alias': '',
        'report_date': '2023-10-05',
        'route_policy': 'ELIGIBLE_SINGLE_STOCK',
    },
    {
        'file_name': '凱基投顧_3665 貿聯-KY_李承泰_20260519.pdf',
        'broker_alias': '凱基投顧',
        'ticker': '3665',
        'company_alias': '貿聯-KY',
        'report_date': '2026-05-19',
        'route_policy': 'ELIGIBLE_SINGLE_STOCK',
    },
    {
        'file_name': '凱基投顧_6147 頎邦_劉宇程_20260519.pdf',
        'broker_alias': '凱基投顧',
        'ticker': '6147',
        'company_alias': '頎邦',
        'report_date': '2026-05-19',
        'route_policy': 'ELIGIBLE_SINGLE_STOCK',
    },
    {
        'file_name': '瑞基(4171,NR_未評等)-CTBC251208.pdf',
        'broker_alias': '中信投顧',
        'ticker': '4171',
        'company_alias': '瑞基',
        'report_date': '2025-12-08',
        'route_policy': 'ELIGIBLE_SINGLE_STOCK',
    },
    {
        'file_name': 'Citi-3231 20250604.pdf',
        'broker_alias': 'Citi',
        'ticker': '3231',
        'company_alias': '',
        'report_date': '2025-06-04',
        'route_policy': 'ELIGIBLE_SINGLE_STOCK',
    },
    {
        'file_name': 'GS-1590 20231012.pdf',
        'broker_alias': 'Goldman Sachs',
        'ticker': '1590',
        'company_alias': '',
        'report_date': '2023-10-12',
        'route_policy': 'ELIGIBLE_SINGLE_STOCK',
    },
    {
        'file_name': 'GS-1590 20251203.pdf',
        'broker_alias': 'Goldman Sachs',
        'ticker': '1590',
        'company_alias': '',
        'report_date': '2025-12-03',
        'route_policy': 'ELIGIBLE_SINGLE_STOCK',
    },
    {
        'file_name': 'GS-2383 20260519.pdf',
        'broker_alias': 'Goldman Sachs',
        'ticker': '2383',
        'company_alias': '',
        'report_date': '2026-05-19',
        'route_policy': 'ELIGIBLE_SINGLE_STOCK',
    },
    {
        'file_name': 'GS-3706 20251130.pdf',
        'broker_alias': 'Goldman Sachs',
        'ticker': '3706',
        'company_alias': '',
        'report_date': '2025-11-30',
        'route_policy': 'ELIGIBLE_SINGLE_STOCK',
    },
    {
        'file_name': 'GS-6415 20260517.pdf',
        'broker_alias': 'Goldman Sachs',
        'ticker': '6415',
        'company_alias': '',
        'report_date': '2026-05-17',
        'route_policy': 'ELIGIBLE_SINGLE_STOCK',
    },
    {
        'file_name': 'JP-3653 20251003.pdf',
        'broker_alias': 'J.P. Morgan',
        'ticker': '3653',
        'company_alias': '',
        'report_date': '2025-10-03',
        'route_policy': 'ELIGIBLE_SINGLE_STOCK',
    },
    {
        'file_name': 'MQ-1560 20260520.pdf',
        'broker_alias': 'Macquarie',
        'ticker': '1560',
        'company_alias': '',
        'report_date': '2026-05-20',
        'route_policy': 'ELIGIBLE_SINGLE_STOCK',
    },
    {
        'file_name': 'MS-1590 20251202.pdf',
        'broker_alias': 'Morgan Stanley',
        'ticker': '1590',
        'company_alias': '',
        'report_date': '2025-12-02',
        'route_policy': 'ELIGIBLE_SINGLE_STOCK',
    },
    {
        'file_name': 'MS-2308 20251128.pdf',
        'broker_alias': 'Morgan Stanley',
        'ticker': '2308',
        'company_alias': '',
        'report_date': '2025-11-28',
        'route_policy': 'ELIGIBLE_SINGLE_STOCK',
    },
    {
        'file_name': 'MS-3661 20251203.pdf',
        'broker_alias': 'Morgan Stanley',
        'ticker': '3661',
        'company_alias': '',
        'report_date': '2025-12-03',
        'route_policy': 'ELIGIBLE_SINGLE_STOCK',
    },
    {
        'file_name': 'MS-3665 20251202.pdf',
        'broker_alias': 'Morgan Stanley',
        'ticker': '3665',
        'company_alias': '',
        'report_date': '2025-12-02',
        'route_policy': 'ELIGIBLE_SINGLE_STOCK',
    },
    {
        'file_name': 'MS-6669 20251007.pdf',
        'broker_alias': 'Morgan Stanley',
        'ticker': '6669',
        'company_alias': '',
        'report_date': '2025-10-07',
        'route_policy': 'ELIGIBLE_SINGLE_STOCK',
    },
    {
        'file_name': 'MS-8210 20251007.pdf',
        'broker_alias': 'Morgan Stanley',
        'ticker': '8210',
        'company_alias': '',
        'report_date': '2025-10-07',
        'route_policy': 'ELIGIBLE_SINGLE_STOCK',
    },
    {
        'file_name': '6933_AMAX-KY_個股介紹報告.pdf',
        'broker_alias': '',
        'ticker': '6933',
        'company_alias': '',
        'report_date': '',
        'route_policy': 'ELIGIBLE_SINGLE_STOCK',
    },
    {
        'file_name': '凱基投顧_1476 儒鴻_劉昃恩_20260519.pdf',
        'broker_alias': '凱基投顧',
        'ticker': '1476',
        'company_alias': '儒鴻',
        'report_date': '2026-05-19',
        'route_policy': 'ELIGIBLE_SINGLE_STOCK',
    },
]

ROUTE_ONLY_INPUT_POLICY_ROWS = [
    {
        'file_name': '20251205兆豐晨會報告(二)-公司訪談摘要.pdf',
        'broker_alias': '兆豐',
        'ticker': '',
        'company_alias': '',
        'report_date': '2025-12-05',
        'route_policy': 'ROUTE_ONLY_NOT_SINGLE_STOCK',
        'route_reason': 'market/macro/overseas/morning-note report; keep route-only unless company section extraction is added',
    },
    {
        'file_name': 'Daiwa-1319 20231011.pdf',
        'broker_alias': 'Daiwa',
        'ticker': '1319',
        'company_alias': '',
        'report_date': '2023-10-11',
        'route_policy': 'INDUSTRY_REPORT_ROUTE',
        'route_reason': 'industry report; route/quarantine unless company ticker section extraction is added',
    },
    {
        'file_name': 'Daiwa-3653 20251002.pdf',
        'broker_alias': 'Daiwa',
        'ticker': '3653',
        'company_alias': '',
        'report_date': '2025-10-02',
        'route_policy': 'INDUSTRY_REPORT_ROUTE',
        'route_reason': 'industry report; route/quarantine unless company ticker section extraction is added',
    },
    {
        'file_name': 'Daiwa-6278 20260521.pdf',
        'broker_alias': 'Daiwa',
        'ticker': '6278',
        'company_alias': '',
        'report_date': '2026-05-21',
        'route_policy': 'INDUSTRY_REPORT_ROUTE',
        'route_reason': 'industry report; route/quarantine unless company ticker section extraction is added',
    },
    {
        'file_name': '20251205兆豐晨會報告(一)-當日新聞與重要訊息評論.pdf',
        'broker_alias': '兆豐',
        'ticker': '',
        'company_alias': '',
        'report_date': '2025-12-05',
        'route_policy': 'ROUTE_ONLY_NOT_SINGLE_STOCK',
        'route_reason': 'market/macro/overseas/morning-note report; keep route-only unless company section extraction is added',
    },
    {
        'file_name': '20251208_台新台股盤勢分析.pdf',
        'broker_alias': '',
        'ticker': '',
        'company_alias': '',
        'report_date': '2025-12-08',
        'route_policy': 'ROUTE_ONLY_NOT_SINGLE_STOCK',
        'route_reason': 'market/macro/overseas/morning-note report; keep route-only unless company section extraction is added',
    },
    {
        'file_name': '投資早報251209.pdf',
        'broker_alias': '',
        'ticker': '',
        'company_alias': '',
        'report_date': '2025-12-09',
        'route_policy': 'ROUTE_ONLY_NOT_SINGLE_STOCK',
        'route_reason': 'market/macro/overseas/morning-note report; keep route-only unless company section extraction is added',
    },
    {
        'file_name': '第一場 2026年投資大趨勢 - 華南投顧 -1141201.pdf',
        'broker_alias': '華南投顧',
        'ticker': '2026',
        'company_alias': '',
        'report_date': '2025-12-01',
        'route_policy': 'ROUTE_ONLY_NOT_SINGLE_STOCK',
        'route_reason': 'market/macro/overseas/morning-note report; keep route-only unless company section extraction is added',
    },
    {
        'file_name': '第二場 2026海外投資展望 - 華南永昌海外商品部.pdf',
        'broker_alias': '華南投顧',
        'ticker': '2026',
        'company_alias': '',
        'report_date': '',
        'route_policy': 'ROUTE_ONLY_NOT_SINGLE_STOCK',
        'route_reason': 'market/macro/overseas/morning-note report; keep route-only unless company section extraction is added',
    },
    {
        'file_name': '第三場 AI潮流下展望2026半導體產業趨勢 - 陳子昂.pdf',
        'broker_alias': '',
        'ticker': '2026',
        'company_alias': '',
        'report_date': '',
        'route_policy': 'INDUSTRY_REPORT_ROUTE',
        'route_reason': 'industry report; route/quarantine unless company ticker section extraction is added',
    },
    {
        'file_name': '凱基日股分析20251205-軍工股及機器人股上漲推升日股收漲.pdf',
        'broker_alias': '凱基投顧',
        'ticker': '',
        'company_alias': '',
        'report_date': '2025-12-05',
        'route_policy': 'ROUTE_ONLY_NOT_SINGLE_STOCK',
        'route_reason': 'market/macro/overseas/morning-note report; keep route-only unless company section extraction is added',
    },
    {
        'file_name': '凱基投顧_鋼鐵產業_劉昃恩_20260518.pdf',
        'broker_alias': '凱基投顧',
        'ticker': '',
        'company_alias': '',
        'report_date': '2026-05-18',
        'route_policy': 'INDUSTRY_REPORT_ROUTE',
        'route_reason': 'industry report; route/quarantine unless company ticker section extraction is added',
    },
    {
        'file_name': '凱基美股分析20251205-Meta大砍元宇宙預算，標普、那指續漲.pdf',
        'broker_alias': '凱基投顧',
        'ticker': '',
        'company_alias': '',
        'report_date': '2025-12-05',
        'route_policy': 'ROUTE_ONLY_NOT_SINGLE_STOCK',
        'route_reason': 'market/macro/overseas/morning-note report; keep route-only unless company section extraction is added',
    },
    {
        'file_name': '凱基期貨晨間解盤20251205.pdf',
        'broker_alias': '凱基投顧',
        'ticker': '',
        'company_alias': '',
        'report_date': '2025-12-05',
        'route_policy': 'ROUTE_ONLY_NOT_SINGLE_STOCK',
        'route_reason': 'market/macro/overseas/morning-note report; keep route-only unless company section extraction is added',
    },
    {
        'file_name': '凱基港股分析20251205-機器人概念受資金追捧，港股收漲.pdf',
        'broker_alias': '凱基投顧',
        'ticker': '',
        'company_alias': '',
        'report_date': '2025-12-05',
        'route_policy': 'ROUTE_ONLY_NOT_SINGLE_STOCK',
        'route_reason': 'market/macro/overseas/morning-note report; keep route-only unless company section extraction is added',
    },
    {
        'file_name': '統一投顧-20251209投資早報.pdf',
        'broker_alias': '統一投顧',
        'ticker': '',
        'company_alias': '',
        'report_date': '2025-12-09',
        'route_policy': 'ROUTE_ONLY_NOT_SINGLE_STOCK',
        'route_reason': 'market/macro/overseas/morning-note report; keep route-only unless company section extraction is added',
    },
    {
        'file_name': 'Daiwa-PCB 20251204.pdf',
        'broker_alias': 'Daiwa',
        'ticker': '',
        'company_alias': '',
        'report_date': '2025-12-04',
        'route_policy': 'INDUSTRY_REPORT_ROUTE',
        'route_reason': 'industry report; route/quarantine unless company ticker section extraction is added',
    },
    {
        'file_name': 'GF-Thoughts on TPU Competition with GPU 20251126.pdf',
        'broker_alias': 'GF Securities',
        'ticker': '',
        'company_alias': '',
        'report_date': '2025-11-26',
        'route_policy': 'INDUSTRY_REPORT_ROUTE',
        'route_reason': 'industry report; route/quarantine unless company ticker section extraction is added',
    },
    {
        'file_name': 'GS-AI PCB CCL 20251204.pdf',
        'broker_alias': 'Goldman Sachs',
        'ticker': '',
        'company_alias': '',
        'report_date': '2025-12-04',
        'route_policy': 'INDUSTRY_REPORT_ROUTE',
        'route_reason': 'industry report; route/quarantine unless company ticker section extraction is added',
    },
    {
        'file_name': 'MS-ABF 20260518.pdf',
        'broker_alias': 'Morgan Stanley',
        'ticker': '',
        'company_alias': '',
        'report_date': '2026-05-18',
        'route_policy': 'INDUSTRY_REPORT_ROUTE',
        'route_reason': 'industry report; route/quarantine unless company ticker section extraction is added',
    },
    {
        'file_name': 'MS-Automation 20251126.pdf',
        'broker_alias': 'Morgan Stanley',
        'ticker': '',
        'company_alias': '',
        'report_date': '2025-11-26',
        'route_policy': 'INDUSTRY_REPORT_ROUTE',
        'route_reason': 'industry report; route/quarantine unless company ticker section extraction is added',
    },
    {
        'file_name': 'MS-Memory 20251204.pdf',
        'broker_alias': 'Morgan Stanley',
        'ticker': '',
        'company_alias': '',
        'report_date': '2025-12-04',
        'route_policy': 'INDUSTRY_REPORT_ROUTE',
        'route_reason': 'industry report; route/quarantine unless company ticker section extraction is added',
    },
    {
        'file_name': 'MS-Thermal Solutions 20251007.pdf',
        'broker_alias': 'Morgan Stanley',
        'ticker': '',
        'company_alias': '',
        'report_date': '2025-10-07',
        'route_policy': 'INDUSTRY_REPORT_ROUTE',
        'route_reason': 'industry report; route/quarantine unless company ticker section extraction is added',
    },
    {
        'file_name': 'MS-Thermal Solutions 20251208.pdf',
        'broker_alias': 'Morgan Stanley',
        'ticker': '',
        'company_alias': '',
        'report_date': '2025-12-08',
        'route_policy': 'INDUSTRY_REPORT_ROUTE',
        'route_reason': 'industry report; route/quarantine unless company ticker section extraction is added',
    },
    {
        'file_name': 'UBS-Asia Hardware Insights 20251205.pdf',
        'broker_alias': 'UBS',
        'ticker': '',
        'company_alias': '',
        'report_date': '2025-12-05',
        'route_policy': 'INDUSTRY_REPORT_ROUTE',
        'route_reason': 'industry report; route/quarantine unless company ticker section extraction is added',
    },
]


def def_get_eligible_single_stock_alias_rows_v0100():
    return list(ELIGIBLE_SINGLE_STOCK_ALIAS_ROWS)


def def_get_route_only_input_policy_rows_v0100():
    return list(ROUTE_ONLY_INPUT_POLICY_ROWS)


def def_lookup_source_policy_v0100(file_name: str):
    key = str(file_name or "").strip().lower()

    for row in ELIGIBLE_SINGLE_STOCK_ALIAS_ROWS:
        if str(row.get("file_name", "")).strip().lower() == key:
            return {
                "status": "FOUND",
                "risk": "GREEN",
                "policy": "ELIGIBLE_SINGLE_STOCK",
                "row": dict(row),
            }

    for row in ROUTE_ONLY_INPUT_POLICY_ROWS:
        if str(row.get("file_name", "")).strip().lower() == key:
            return {
                "status": "FOUND",
                "risk": "ROUTE",
                "policy": row.get("route_policy", "ROUTE_ONLY"),
                "row": dict(row),
            }

    return {
        "status": "NOT_FOUND",
        "risk": "YELLOW",
        "policy": "UNKNOWN_REVIEW",
        "row": {},
    }


def def_self_check_v0100():
    eligible = def_get_eligible_single_stock_alias_rows_v0100()
    route = def_get_route_only_input_policy_rows_v0100()

    seen = set()
    duplicate = []

    for row in eligible + route:
        key = str(row.get("file_name", "")).strip().lower()
        if not key:
            duplicate.append("<EMPTY_FILE_NAME>")
            continue
        if key in seen:
            duplicate.append(key)
        seen.add(key)

    return {
        "module_version": MODULE_VERSION,
        "hard_pass": len(duplicate) == 0,
        "eligible_single_stock": len(eligible),
        "route_only_input_policy": len(route),
        "duplicate": duplicate,
        "db_write": False,
        "canonical_write": False,
        "parser_core_rewrite": False,
        "delete": False,
        "deploy": False,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(def_self_check_v0100(), ensure_ascii=False, indent=2))
