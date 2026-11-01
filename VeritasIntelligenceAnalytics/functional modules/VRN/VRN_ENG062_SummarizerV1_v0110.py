#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN 四點摘要 v0110(候選句品質:① 後援:原路徑候選句 <4 才把逐行區塊接回段落(凱基 PDF 每行一塊 · 約 37 字 · 句子中間斷開 → 原本全被 <40 字門檻丟掉 · 只剩表格 / 圖例可選)· 同頁 · 上下相鄰 · 左緣對齊才接 ② 圖例不當句((左軸)/(右軸)/LHS/RHS)③ 表格列不當句(數字 / ppts 佔 ≥45%)④ 免責 / 來源句不當重點(中英)⑤ 重點只從前段選(首頁~第 3 頁或前 30%)⑥ 有空點時才放寬短風險句(≥12 字)補點 ⑦ 候選不夠時相似度放寬到 0.9 再挑(避免空點)
v0109(① 影像頁 OCR 只做前 2 頁 · 與 ENG397 共用 OCR 快取(PDF 雜湊 + 頁 + 200 DPI · VIA_VRN2_OCR_CACHE)· 首頁直接沿用擷取階段結果 ② 標題後援接續同區塊同字級的上下行(GS-2382 跨兩行只取到下半句)
v0108(標題後援:頂部大字區排除券商橫幅後若沒有標題(GS-1590 / GS-2382 只剩「Sachs I Research」)→ 首頁上 60% 左 65% 找字級 ≥10.5 · ≥20 字 · 非橫幅 / 代號列 / 免責 / 分析師行的區塊 · 粗體加權 · 取最大字 · 同字取最上)
v0107(① 影像頁(沒有文字層)走 VRN-2 OCR 隔離橋(VIA_VRN2_OCR_PY / VIA_VRN2_OCR_BRIDGE · 200 DPI)取文字區塊 · reader 標 OCR · 未就緒照舊 NO_TEXT ② 頁首券商橫幅(Goldman Sachs | Research → 「Sachs I Research」/ Equity Research)不當標題)
v0106(① 中文標題 ≥8 字即可(凱基「獲利將創四年新高，但評價已高」14 字被英文 >18 字門檻擋掉)② 成長率章節判斷支援「科目 + 數字同一行」與文字型數值(盈轉虧 / 虧轉盈)③ 目標價排除「前次 / 上次」(往前 60 字可跨行 · 兆豐)· 允許「目標價至 208 元」· 同義字「目標」(≤2 中文字)不當目標價標籤· 現價允許標籤後夾英文日期(凱基)④ 中文標題 ≥5 字且總長 ≥8(凱基儒鴻「2H26 獲利展望平淡」)(國泰神達 年成長率(%)→ 每股盈餘 -22.3 / -80.81 被當 EPS)· v0105 原檔不動)
v0105(VRN-2 接入:① 標題略過只有符號的大字行(JP 首頁「•」12.3pt 大於標題 11.9pt)· 門檻 12 → 11.5pt(取最大字級 · ≥12pt 的標題不會被取代)② 沒有 polars 時 Parquet 跳過並記錄 · 不中斷 ③ 年度 EPS 不取「成長率章節」底下的每股盈餘列(國泰 3014 P7 年成長率(%)→ 每股盈餘 26.06 / 15.42 是成長率 · 實際 EPS 9.53 / 11.00)④ 價格候選排除日期 / 期間(國泰「目標價⏎2023/10/05」· UBS「valuation⏎12/23」造成目標價衝突留空)⑤ 完整 rule_catalog.json 不在 → 用 rule_catalog_runtime.json(只留執行期 5 鍵 · 輸出逐字相同 · JP-2330 實證)· v0104 原檔不動)
v0104:四點摘要候選新版：來源數字鎖定、年度 EPS、語境同義字、本地 NLP。

不調用網路或 LLM。原版 API 透過惰性 __getattr__ 保留；新契約由
summarize_document / summarize_pdf / --input 提供。中央註冊與啟用須另走 VCGC。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== 01｜所有可調參數 =====
VERSION = 'v0110'
CONFIG = {
    'max_pdf_pages': 24, 'max_pdf_bytes': 40 * 1024 * 1024,
    'max_block_chars': 16000, 'max_sentences': 800, 'max_payload_chars': 2400,
    'max_sentence_chars': 750, 'similarity_cutoff': 0.70,
    'eps_header_window': 65, 'max_eps_years': 8,
    'upside_tolerance_pp': 1.0, 'catalog': 'rule_catalog.json',
    'encoding': 'utf-8-sig', 'result_root': 'results',
    'company_master': None, 'language': 'zh-TW',
}
ALIASES = {
    'target': ['target price', 'price target', '目標價', '目标价', 'TP'],
    'current': ['share price', 'shr price, close', 'current price', '股價', '股价', 'Price', '收盤價'],
    'old_target': ['prior target price', 'old target price', 'previous target price', '原目標價', '舊目標價'],
    'upside': ['upside', 'up/downside', 'up/downside to price target', '上漲空間', '潛在上漲空間'],
}
TOPIC_WORDS = {
    'growth': ['growth', 'demand', 'revenue', 'shipments', 'orders', 'ASP', '成長', '需求', '營收', '出貨', '訂單', '動能'],
    'margin': ['margin', 'profitability', 'product mix', '毛利', '利潤', '產品組合'],
    'moat': ['market share', 'penetration', 'competitive', 'technology', '市佔', '護城河', '競爭', '滲透率', '技術'],
    'risk': ['downside risk', 'key risks', 'weaker-than-expected', 'headwind', 'uncertainty', 'risk to', '風險', '逆風', '不確定', '瓶頸'],
    'catalyst': ['catalyst', 'launch', 'production', 'project', 'wins', '催化', '量產', '新產品', '專案', '合作'],
}
NUMBER = r'[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?'
CURRENCY = r'(?:NT\s*\$|TWD|USD|US\s*\$|HK\s*\$|HKD|RMB|CNY|JPY|美元|新台幣|港元|元|\$)'
BOILERPLATE = r'^(?:See (?:important )?disclosures|For analyst certification|For Reg AC|Morgan Stanley does|Goldman Sachs does|Analysts employed|Disclaimer|Disclosures?\s*$|免責聲明|分析師認證|評等定義)'
PERIOD_TOKEN = r'(?:FY[- ]?)?(?:(?:12|Dec)[/-])?((?:20)?\d{2})([AEFae f]?)'

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import re
import sys
import unicodedata
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

# ===== 02｜工具橋及旧版公開面 =====
_BODY = None


def load_accelerator():
    """沿既有橋找加速器；缺席明示，無自動安裝及假成功。"""
    for parent in Path(__file__).resolve().parents:
        bridge = parent / 'supportive modules' / 'VIA_SuperAccel_Module.py'
        if bridge.is_file():
            spec = importlib.util.spec_from_file_location('VIA_ACCEL_SUMMARY', bridge)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    return None


def load_previous():
    global _BODY
    if _BODY is not None:
        return _BODY
    local = Path(__file__).with_name('VRN_ENG062_SummarizerV1_v0103.py')
    archived = Path(__file__).parent / 'sources/VeritasIntelligenceAnalytics/functional modules/VRN/VRN_ENG062_SummarizerV1_v0103.py'
    path = local if local.is_file() else archived
    if not path.is_file():
        raise ImportError('前版來源缺席；新契約可獨立使用，舊 API 不假裝存在')
    name = '_VRN_ENG062_previous'
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    _BODY = module
    return module


def __getattr__(name):
    if name.startswith('__'):
        raise AttributeError(name)
    return getattr(load_previous(), name)


def load_catalog(path=None):
    path = Path(path or Path(__file__).with_name(CONFIG['catalog']))
    if not path.exists() and path.name == CONFIG['catalog']:
        path = path.with_name('rule_catalog_runtime.json')
    result = json.loads(path.read_text(encoding='utf-8'))
    if result.get('schema') != 'VRN_SUMMARY_RULE_CATALOG/1':
        raise ValueError('規則契約錯誤')
    return result


# ===== 03｜文字與證據 =====
def clean_text(text):
    """NFKC/trim/中文小間隔修復；保留英文詞界、數字小數與原始證據。"""
    text = unicodedata.normalize('NFKC', str(text)).replace('\u00ad', '')
    text = re.sub(r'([A-Za-z])-\s*\n\s*([a-z])', r'\1\2', text)
    text = re.sub(r'(?<=[\u3400-\u9fff])[^\S\n]+(?=[\u3400-\u9fff])', '', text)
    return '\n'.join(re.sub(r'[^\S\n]+', ' ', line).strip() for line in text.splitlines()).strip()


def number_decimal(text):
    value = str(text).strip().replace(',', '')
    if value.startswith('(') and value.endswith(')'):
        value = '-' + value[1:-1]
    result = Decimal(value)
    if not result.is_finite():
        raise ValueError('非有限數字')
    return result


def currency_code(raw):
    s = raw.casefold().replace(' ', '')
    if re.search(r'nt\$|twd|新台幣|^元$', s):
        return 'TWD'
    if re.search(r'us\$|usd|美元', s):
        return 'USD'
    if re.search(r'hk\$|hkd|港元', s):
        return 'HKD'
    if re.search(r'rmb|cny', s):
        return 'CNY'
    if 'jpy' in s:
        return 'JPY'
    return None


def evidence(block, quote, start=None, end=None):
    return {'block_id': block['id'], 'page': block.get('page'), 'bbox': block.get('bbox'),
            'quote': quote, 'normalized_start': start, 'normalized_end': end,
            'source': block.get('source', 'input'), 'raw_sha256': hashlib.sha256(block['text'].encode()).hexdigest()}


def alias_pattern(aliases):
    out = []
    for alias in sorted(set(aliases), key=len, reverse=True):
        pattern = re.escape(alias).replace(r'\ ', r'\s*')
        if re.match(r'[A-Za-z]', alias):
            pattern = r'(?<![A-Za-z])' + pattern
        if re.search(r'[A-Za-z]$', alias):
            pattern += r'(?![A-Za-z])'
        out.append(pattern)
    return '(?:' + '|'.join(out) + ')'


def metric_candidates(blocks, key, catalog):
    aliases = list(ALIASES[key])
    if key == 'target':
        aliases += [x for x in catalog['central_synonyms'].get('TARGET_PRICE', []) if isinstance(x, str) and len(x) < 40 and not (re.fullmatch(r'[\u4e00-\u9fff]{1,2}', x))]   # v0106 「目標」太寬(目標 2027 / 目標 41)
    label = alias_pattern(aliases)
    if key == 'upside':
        pattern = label + r'\s*(?:\(%\)|\(\s*%\s*\))?\s*[:：]?\s*(?P<n>' + NUMBER + r')\s*(?P<unit>%?)'
    else:
        pattern = label + r'(?:\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{1,2}(?:,\s*\d{4})?)?\s*(?:\((?P<pc>[^\n)]{0,32})\))?\s*(?:to\s*|至\s*)?[:：]?\s*(?P<c>' + CURRENCY + r')?\s*(?P<n>' + NUMBER + r')(?P<suffix>\s*(?:元|美元|港元))?'   # v0106 收盤價 September 15 (NT$) 96.90
    result = []
    for block in blocks:
        if block.get('page') not in (None, 1):
            continue
        text = clean_text(block['text'])
        if key == 'old_target':
            old_pattern = alias_pattern(ALIASES['target']) + r'[\s\S]{0,65}?(?:from|prior|previous|原為|由)\s*(?P<c>' + CURRENCY + r')?\s*(?P<n>' + NUMBER + r')'
            for old in re.finditer(old_pattern, text, re.I):
                result.append({'value': str(number_decimal(old.group('n'))), 'currency': currency_code(old.group('c') or ''), 'price_basis': 'REPORT', 'evidence': evidence(block, old.group(), old.start(), old.end())})
        for match in re.finditer(pattern, text, re.I):
            # 目標/舊價/情境不共享候選；裸 Price 必須是行首標籤。
            prefix = text[max(0, match.start()-35, text.rfind('\n',0,match.start())+1):match.start()]
            if key == 'target' and re.search(r'old|prior|previous|舊|原|前次|上次|bear|bull|scenario|情境|牛市|熊市|up/downside to|upside to', prefix, re.I):
                continue
            if key == 'target' and re.search(r'前次|上次|previous|prior', text[max(0, match.start() - 60):match.start()], re.I) and not re.search(r'[。.]\s*$', text[max(0, match.start() - 60):match.start()]):
                continue   # v0106 兆豐「前次投資建議 ⏎ 目標價:$345」跨行
            if key == 'current' and (re.search(r'target\s*$', prefix, re.I) or (match.group().lower().startswith('price') and prefix.strip() and not prefix.endswith('\n'))):
                continue
            if key == 'upside' and '%' not in match.group() and '%' not in prefix and 'price target' not in match.group().lower():
                continue
            if re.match(r'/\d', text[match.end():match.end() + 2]):
                continue   # v0105 日期 / 期間(2023/10/05 · 12/23)不是價格
            raw_currency = (match.groupdict().get('c') or '') + (match.groupdict().get('suffix') or '')
            if not currency_code(raw_currency) and match.groupdict().get('pc') and currency_code(match.group('pc')):
                raw_currency = match.group('pc')                       # v0106 括號裡的幣別 (NT$)
            result.append({'value': str(number_decimal(match.group('n'))),
                           'currency': currency_code(raw_currency), 'price_basis': 'REPORT',
                           'evidence': evidence(block, match.group(), match.start(), match.end())})
    return result


def resolve_metric(candidates, key, issues):
    groups = {}
    for item in candidates:
        groups.setdefault((number_decimal(item['value']), item.get('currency')), []).append(item)
    if not groups:
        return None
    values = {x[0] for x in groups}
    currencies = {x[1] for x in groups if x[1]}
    if len(values) > 1 or len(currencies) > 1:
        issues.append({'code': 'METRIC_CONFLICT', 'field': key, 'candidates': candidates})
        return None
    selected = next((x for x in candidates if x['currency']), candidates[0])
    return {**selected, 'evidence_all': [x['evidence'] for x in candidates]}


# ===== 04｜年度 EPS 表格；舊值／共識／季度不混入 =====
def parse_period(token):
    token = token.strip()
    match = re.fullmatch(PERIOD_TOKEN, token)
    if not match:
        return None
    # 裸兩碼是數值，不是年份；兩碼年必須有年度日期前綴或 E/F 標記。
    if len(match.group(1)) == 2 and not match.group(2).strip() and not re.match(r'(?:FY|12[/-]|Dec[/-])', token, re.I):
        return None
    year = int(match.group(1))
    year = year + 2000 if year < 100 else year
    if not 1990 <= year <= 2100:
        return None
    return {'year': year, 'forecast': match.group(2).strip().casefold() in ('e', 'f'), 'raw': token}


def period_runs(lines):
    result, run = [], []
    for i, line in enumerate(lines + ['END']):
        parts = line.split()
        periods = [parse_period(p) for p in parts]
        if parts and all(periods):
            run.extend((i, p) for p in periods)
        else:
            if 2 <= len(run) <= CONFIG['max_eps_years'] and len({p['year'] for _, p in run}) == len(run):
                result.append((run[0][0], run[-1][0], [p for _, p in run]))
            run = []
    return result


def _is_num_line(x):
    x = re.sub(r'盈轉虧|虧轉盈|轉虧|轉盈|N\.?A\.?|N\.?M\.?', '0', x)          # 文字型數值(國泰:盈轉虧 / 虧轉盈)
    return bool(re.fullmatch(r'(?:' + NUMBER + r'|\(' + NUMBER + r'\)|--|-)(?:\s+(?:' + NUMBER + r'|\(' + NUMBER + r'\)|--|-))*', x.strip()))


def _has_nums(x):
    """v0106:行尾帶數字(科目 + 數字同一行)= 資料列。"""
    tk = re.sub(r'盈轉虧|虧轉盈|轉虧|轉盈', '0', x).split()
    return bool(tk) and bool(re.fullmatch(r'(?:' + NUMBER + r'|\(' + NUMBER + r'\)|--|-)', tk[-1]))


def _in_growth_section(lines, lo, idx):
    """v0105:列標籤所屬章節(往上找:後面緊接另一個文字列的標題列)是成長率類 → 這一列是成長率不是 EPS(國泰 3014 P7「年成長率(%)」下的「每股盈餘」)。"""
    for j in range(idx - 1, lo - 1, -1):
        if _is_num_line(lines[j]) or _has_nums(lines[j]) or j + 1 >= len(lines) or _is_num_line(lines[j + 1]):
            continue
        if re.search(r'成長率|增率|growth|yoy|y/y|%\)|（%）|\(%\)', lines[j], re.I):
            return True
        return False
    return False


def extract_annual_eps(blocks, catalog, issues):
    annual = []
    for block in blocks:
        lines = [x.strip() for x in clean_text(block['text']).splitlines() if x.strip()]
        runs = period_runs(lines)
        for ri, (_, end, periods) in enumerate(runs):
            stop = min(len(lines), end + CONFIG['eps_header_window'])
            if ri + 1 < len(runs):
                stop = min(stop, runs[ri+1][0])
            for idx in range(end+1, stop):
                label = lines[idx]
                if not re.search(r'\bEPS\b|每股盈餘|每股收益', label, re.I):
                    continue
                if re.search(r'change|growth|yoy|qoq|consensus|cons\.|vs\.?|revision|old|prior|%|§|年增|季增|成長|舊|原|共識', label, re.I):
                    continue
                if _in_growth_section(lines, end + 1, idx):
                    continue
                cells = []
                for line in lines[idx+1:idx+1+CONFIG['max_eps_years']+12]:
                    if re.fullmatch(r'(?:' + NUMBER + r'|\(' + NUMBER + r'\)|--|-)', line):
                        cells.append(line)
                    else:
                        split_cells = line.split()
                        if split_cells and all(re.fullmatch(r'(?:' + NUMBER + r'|\(' + NUMBER + r'\)|--|-)', x) for x in split_cells):
                            cells.extend(split_cells)
                        break
                if len(cells) != len(periods) or not all(re.fullmatch(r'(?:' + NUMBER + r'|\(' + NUMBER + r'\)|--|-)', x) for x in cells):
                    continue
                currency = currency_code(label)
                if currency is None:
                    # Daiwa 的單位由 financial summary 表題明示，不從股票市場猜幣別。
                    before = '\n'.join(lines[max(0, idx-45):idx])
                    matches = re.findall(r'Financial summary\s*\(([^)]+)\)', before, re.I)
                    currency = currency_code(matches[-1]) if matches else None
                eps_type = 'DILUTED' if re.search(r'dilut|\bFD\b|稀釋', label, re.I) else 'UNSPECIFIED'
                if 'Core' in label or 'core' in label:
                    eps_type = 'CORE_DILUTED' if eps_type == 'DILUTED' else 'CORE'
                for period, cell in zip(periods, cells):
                    if cell in ('-', '--'):
                        continue
                    annual.append({'year': period['year'], 'forecast': period['forecast'],
                                   'value': str(number_decimal(cell)), 'currency': currency,
                                   'eps_type': eps_type, 'period_type': 'ANNUAL', 'row_label': label,
                                   'evidence': evidence(block, '\n'.join(lines[end+1:idx+1+len(periods)])),
                                   'header': [p['raw'] for p in periods], 'raw_value': cell})
                break
    by_year = {}
    for item in annual:
        by_year.setdefault(item['year'], []).append(item)
    result = []
    for year, items in sorted(by_year.items()):
        values = {(x['value'], x['eps_type'], x['currency'], x['forecast']) for x in items}
        if len(values) > 1:
            issues.append({'code': 'EPS_CONFLICT', 'year': year, 'candidates': items})
            continue
        result.append({**items[0], 'evidence_all': [x['evidence'] for x in items]})
    # 計算保留原精度，負值基期不稱成長率。
    for i, item in enumerate(result):
        item['yoy_calculated'] = None
        if i and result[i-1]['year'] == item['year']-1 and result[i-1]['eps_type'] == item['eps_type'] and result[i-1]['currency'] == item['currency']:
            prior = number_decimal(result[i-1]['value'])
            if prior > 0:
                item['yoy_calculated'] = str((number_decimal(item['value'])/prior-1)*100)
    return result


def extract_valuation(blocks, catalog):
    result = []
    for block in blocks:
        if block.get('role') in ('table', 'header', 'layout_fragment', 'disclosure'):
            continue
        text = re.sub(r'\s*\n\s*', ' ', clean_text(block['text']))
        if re.search(r'percentile|factor profile|rating definition|definition of|disclaimer', text, re.I):
            continue
        sentences = re.split(r'(?<!\d)\.\s+(?=[A-Z])|(?<=\d)\.\s+(?=[A-Z])|(?<=[。!?！？])\s*', text)
        for context in sentences:
            if not re.search(r'based|target|\bTP\b|valuation|valued|DCF|SOTP|基於|採用|評價|估值|applied|trades at|trading at', context, re.I):
                continue
            role = 'CURRENT_TRADING' if re.search(r'trades at|trading at|currently|current P/E', context, re.I) else 'TARGET_BASIS'
            for method in catalog['valuation_methods']:
                aliases = sum((method.get(k, []) for k in ('en', 'zh_tw', 'zh_hk', 'zh_cn')), []) + method.get('en_case_sensitive', [])
                matched = next((alias for alias in sorted(set(aliases), key=len, reverse=True) if re.search(alias_pattern([alias]), context, 0 if alias in method.get('en_case_sensitive', []) else re.I)), None)
                inferred = method['id'] == 'VAL_PE' and re.search(r'\bTP\b|price target|目標價', context, re.I) and re.search(r'\d+(?:\.\d+)?x\s+(?:FY)?(?:20)?\d{2}[EFef]?\s+EPS', context)
                if not matched and not inferred:
                    continue
                if matched in method.get('context_required', {}) and not re.search(r'\d+(?:\.\d+)?\s*[x倍]|valu|目標|本益', context, re.I):
                    continue
                # 沒有價格／目標／基準情境的純估值描述只是提及。
                if role == 'TARGET_BASIS' and not re.search(r'\bTP\b|target|base case|based on|基於|採用|目標', context, re.I):
                    role = 'MENTION'
                multiples = re.findall(r'(\d+(?:\.\d+)?)\s*[x倍](?![A-Za-z])', context)
                # 只在單一倍數時建立數值欄位；同業多倍數只保留原文，防混配。
                multiple = multiples[0] if len(multiples) == 1 and method['group'].endswith('MULTIPLE') else None
                years = re.findall(r'\d+(?:\.\d+)?x\s+(?:FY)?(20\d{2}|\d{2})[EFef]\s+(?:EPS|P/E|PER)', context, re.I)
                years += re.findall(r'(?:FY)?(20\d{2}|\d{2})[EFef]\s+(?:P/E|PER)\s+(?:of\s+)?\d+(?:\.\d+)?x', context, re.I)
                years = sorted({int(y) if len(y)==4 else int(y)+2000 for y in years})
                result.append({'id': method['id'], 'name': method['primary_name'], 'zh_name': method['zh_name'],
                               'role': role, 'multiple': multiple, 'years': years,
                               'forward_basis': '1-year forward EPS' if re.search(r'1-year forward EPS', context, re.I) else None,
                               'inferred_from_explicit_tp_eps_formula': bool(inferred and not matched),
                               'evidence': evidence(block, context), 'quote': context})
    dedup = {}
    for row in result:
        dedup.setdefault((row['id'], row['quote']), row)
    return list(dedup.values())


# ===== 05｜語境別名、NLP 候選與去重 =====
def match_scoped_aliases(text, catalog, scope, namespace='freetext'):
    result = []
    entries = catalog['active_union'].get(scope, {}).get(namespace, {})
    for alias, row in entries.items():
        if len(alias) <= 2 and scope != 'broker':
            # OW/PE 等縮寫只可由明確欄位上下文處理，不能全文裸掃。
            continue
        if re.search(alias_pattern([alias]), text, re.I):
            result.append({'alias': alias, 'canonical': row['canonical'], 'provenance': row['provenance']})
    return result


def _merge_lines(blocks):
    """v0110 逐行區塊接回段落:同頁 · 一般角色 · 下一塊頂端距上一塊底 ≤ 行高 × 0.9 · 左緣差 ≤ 14pt · 上一塊不是句尾才接(中文直接接 · 英文補空格)。"""
    out = []
    for b in blocks:
        prev = out[-1] if out else None
        if (prev is not None and b.get('bbox') and prev.get('bbox') and b.get('page') == prev.get('page') and not b.get('role') and not prev.get('role')
                and 0 <= b['bbox'][1] - prev['bbox'][3] <= 0.9 * max(4.0, (prev['bbox'][3] - prev['bbox'][1]) / max(1, prev['text'].count('\n') + 1))
                and abs(b['bbox'][0] - prev['bbox'][0]) <= 14 and not re.search(r'[。!?！？]\s*$', prev['text'])):
            joiner = '' if re.search(r'[\u3400-\u9fff，、]$', prev['text'].strip()) or re.match(r'[\u3400-\u9fff]', b['text'].strip()) else ' '
            m = dict(prev)
            m['id'] = prev['id'] + '+' + b['id']
            m['text'] = prev['text'].rstrip() + joiner + b['text'].lstrip()
            m['bbox'] = [min(prev['bbox'][0], b['bbox'][0]), prev['bbox'][1], max(prev['bbox'][2], b['bbox'][2]), b['bbox'][3]]
            out[-1] = m
        else:
            out.append(b)
    return out


def sentence_candidates(blocks, catalog=None, short_risk=False):
    words_by_topic = {k:list(v) for k,v in TOPIC_WORDS.items()}
    if catalog:
        topic_fields = {'growth': ['revenue'], 'margin': ['gross_margin','operating_margin','net_margin']}
        for topic, fields in topic_fields.items():
            for row in catalog['financial_lexicon']:
                if row.get('std') in fields:
                    words_by_topic[topic].extend(row.get('zh',[]) + row.get('en',[]))
            for field in fields:
                words_by_topic[topic].extend(catalog['central_synonyms'].get('FINANCIAL_FIELD_'+field.upper(), []))
    sentences = []
    _np = max([b.get('page') or 1 for b in blocks] or [1])
    _front = max(3, int(_np * 0.3 + 0.999))                               # v0110 重點只從前段選(首頁 ~ 第 3 頁或前 30%)· 後段多為免責
    for block in blocks:
        if block.get('role') in ('table', 'disclosure', 'contact', 'header', 'layout_fragment'):
            continue
        if (block.get('page') or 1) > _front:
            continue
        text = clean_text(block['text'])
        if re.search(BOILERPLATE, text, re.I | re.M) or len(text) < (12 if short_risk and re.search(r'風險|risk', text, re.I) else 40):   # v0110 短風險區塊(後援)
            continue
        text = re.sub(r'\s*\n\s*', ' ', text)
        parts = re.split(r'(?<=[。!?！？])\s*|(?<!\d)\.\s+(?=[A-Z\u3400-\u9fff])|(?<=\d)\.\s+(?=[A-Z\u3400-\u9fff])', text)
        for part in parts:
            part = part.strip()
            if not (12 if short_risk and re.search(r'風險|risk', part, re.I) else 35) <= len(part) <= CONFIG['max_sentence_chars']:   # v0110 有空點時才放寬短風險句
                continue
            if re.search(r'[（(]\s*[左右]軸\s*[)）]|\b(?:LHS|RHS)\b', part):                    # v0110 圖例
                continue
            if re.search(r"本刊所刊載|僅做為參考|恕不負擔|投資人需自行|並不適合每一個投資人|從事特定交易|資料來源\s*[:：]|研究網站|免責|著作權|Analysts?'? Compensation|research analysts responsible|please contact your sales|research material available|important disclosures|see the (?:end|last page) of this report|refer to (?:the )?important|not an offer to (?:buy|sell)", part, re.I):
                continue                                                                     # v0110 免責 / 來源句(任何文件都不當重點)
            toks = part.split()
            if len(toks) >= 6 and sum(bool(re.fullmatch(r'[\(\-−+]?[\d,.]+%?\)?|ppts?|\(x\)|\(%\)|x', t, re.I)) for t in toks) / len(toks) >= 0.45:
                continue                                                                     # v0110 表格列
            if re.search(r'@|certification|conflict of interest|FINRA|analyst survey|request your ballot', part, re.I):
                continue
            block_risk = bool(re.search(r'key risks|downside risks|principal risks|主要風險', text, re.I))
            tags = {k: sum(bool(re.search(alias_pattern([w]), part, re.I)) for w in words) for k, words in words_by_topic.items()}
            if re.search(r'\b(?:GM|OM)\b', part) and re.search(r'%|improv|margin|expand', part, re.I):
                tags['margin'] += 1
            if block_risk:
                tags['risk'] += 1
            if not any(tags.values()):
                continue
            valuation = bool(re.search(r'target price|price target|\bTP\b|EPS|\bP/E\b|\bPER\b|目標價|每股盈餘', part, re.I))
            score = 2*sum(tags.values()) + 2*bool(re.search(r'\d|%', part)) + (6 if block.get('page') == 1 else 0) - len(part)/600
            sentences.append({'text': part, 'tags': tags, 'score': score, 'valuation': valuation,
                              'evidence': evidence(block, part)})
    # 完全相同句只留一份，但來源列表不丟。
    merged = {}
    for s in sentences[:CONFIG['max_sentences']]:
        key = s['text'].casefold()
        if key in merged:
            merged[key].setdefault('additional_evidence', []).append(s['evidence'])
        else:
            merged[key] = s
    return list(merged.values())


def similarity_matrix(sentences):
    """用 TF-IDF char ngram + cosine 做語意近重複代理；缺庫明示 fallback。"""
    if not sentences:
        return [], 'NO_SENTENCES'
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        sets = [set(re.findall(r'[A-Za-z]+|[\u3400-\u9fff]', s['text'].casefold())) for s in sentences]
        matrix = [[len(a & b)/max(1, len(a | b)) for b in sets] for a in sets]
        return matrix, 'TOKEN_JACCARD_FALLBACK'
    vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(3,5), max_features=18000)
    matrix = cosine_similarity(vectorizer.fit_transform([s['text'] for s in sentences])).tolist()
    return matrix, 'SKLEARN_TFIDF_COSINE'


def select_insights(sentences):
    matrix, method = similarity_matrix(sentences)
    selected = []
    growth = [i for i,s in enumerate(sentences) if s['tags']['growth'] and not s['tags']['risk'] and not s['valuation']]
    if growth:
        selected.append(max(growth, key=lambda i: sentences[i]['score']))
    rest = [i for i,s in enumerate(sentences) if not s['valuation'] and i not in selected]
    for _ in range(2):
        options = [i for i in rest if all(matrix[i][j] < CONFIG['similarity_cutoff'] for j in selected)]
        if not options:                                                   # v0110 候選不夠 → 相似度放寬到 0.9 再挑(避免空點)
            options = [i for i in rest if all(matrix[i][j] < 0.9 for j in selected)]
        if not options:
            break
        # 有來源風險時至少選一條；沒有時按內容挑主題，不強制虛構風險。
        risk = [i for i in options if sentences[i]['tags']['risk']]
        pool = risk if risk and len(selected) >= 1 and not any(sentences[i]['tags']['risk'] for i in selected) else options
        def candidate_score(i):
            diversification = 3 if (sentences[i]['tags']['margin'] or sentences[i]['tags']['moat']) and not any(sentences[j]['tags']['margin'] or sentences[j]['tags']['moat'] for j in selected) else 0
            quantitative = 2 if re.search(r'\d+(?:\.\d+)?%', sentences[i]['text']) else 0
            return sentences[i]['score'] + diversification + quantitative - 3*max((matrix[i][j] for j in selected), default=0)
        chosen = max(pool, key=candidate_score)
        selected.append(chosen)
        rest.remove(chosen)
    return [sentences[i] for i in selected], method


# ===== 06｜摘要契約、數字驗算與輸出 =====
def display_decimal(value, places=1):
    return str(number_decimal(value).quantize(Decimal('1').scaleb(-places), rounding=ROUND_HALF_UP))


def format_metric(metric):
    return str(metric['value']) + (' ' + metric['currency'] if metric.get('currency') else '')


def summarize_document(document, catalog=None):
    catalog = catalog or load_catalog()
    blocks = document.get('blocks', [])
    if not blocks and document.get('text'):
        blocks = [{'id': 'text-1', 'text': document['text'], 'page': 1, 'source': 'text'}]
    if not blocks:
        raise ValueError('沒有來源文字；影像 PDF 請先經既有 OCR 車道，不以空白摘要假成功')
    if len({b['id'] for b in blocks}) != len(blocks):
        raise ValueError('block id 重複')
    _ids = {b['id'] for b in blocks}
    blocks_s = blocks
    if len(sentence_candidates(blocks, catalog)) < 4:                   # v0110 後援:原路徑候選句 <4(凱基逐行 PDF 0~2 句 · 其他券商 11~103 句)才接段落
        blocks_s = blocks + [dict(b, merged_lines=True) for b in _merge_lines(blocks) if b['id'] not in _ids]
    issues = []
    metrics = {key: resolve_metric(metric_candidates(blocks, key, catalog), key, issues) for key in ALIASES}
    eps = extract_annual_eps(document.get('table_blocks', blocks), catalog, issues)
    methods = extract_valuation(blocks, catalog)
    target, current, upside = metrics['target'], metrics['current'], metrics['upside']
    validation = {'upside': 'MISSING', 'calculated_upside': None, 'price_basis': 'REPORT_ONLY', 'llm_calls': 0}
    if target and current:
        if (target['currency'] == current['currency'] or not target['currency'] or not current['currency']) and number_decimal(current['value']) > 0:   # v0106 一邊沒寫幣別 = 同報告同幣別 · 兩邊明寫且不同才不可比
            calc = (number_decimal(target['value'])/number_decimal(current['value'])-1)*100
            validation['calculated_upside'] = str(calc)
            digits = len(upside['value'].split('.')[1]) if upside and '.' in upside['value'] else 0
            tolerance = min(Decimal(str(CONFIG['upside_tolerance_pp'])), Decimal('0.5').scaleb(-digits))
            validation['reported_rounding_tolerance_pp'] = str(tolerance)
            validation['upside'] = 'PASS' if upside and abs(calc-number_decimal(upside['value'])) <= tolerance else ('CALCULATED' if not upside else 'REVIEW')
            if validation['upside'] == 'REVIEW':
                issues.append({'code': 'UPSIDE_MISMATCH', 'reported': upside['value'], 'calculated': str(calc)})
        else:
            validation['upside'] = 'INCOMPARABLE_BASIS_OR_CURRENCY'
    # 外部 adj close 只能另立行情分析口徑；一律不覆蓋報告內股價與目標價。
    if document.get('adj_close') is not None:
        issues.append({'code': 'EXTERNAL_ADJ_PRICE_NOT_USED', 'reason': '未提供同日同幣別且一致拆股調整證據'})
    full_text = '\n'.join(clean_text(b['text']) for b in blocks)
    filename = document.get('filename', '')
    filename_prefix = re.split(r'[-_\s\d(（]', Path(filename).stem)[0]
    brokers = match_scoped_aliases(filename_prefix, catalog, 'broker', 'filename')
    if not brokers:
        brokers = match_scoped_aliases(filename_prefix, catalog, 'broker')
    if not brokers:
        brokers = match_scoped_aliases(full_text[:4000], catalog, 'broker')
    candidates = sentence_candidates(blocks_s, catalog)                 # v0110
    insights, nlp_method = select_insights(candidates)
    parts, p1_evidence = [], []
    if target:
        parts.append('目標價 ' + format_metric(target))
        p1_evidence += target['evidence_all']
    if metrics['old_target']:
        parts.append('原目標價 ' + format_metric(metrics['old_target']))
        p1_evidence += metrics['old_target']['evidence_all']
    if upside:
        parts.append('報告潛在上漲空間 ' + upside['value'] + '%')
        p1_evidence += upside['evidence_all']
    elif validation['upside'] == 'CALCULATED':
        parts.append('依報告同口徑價格計算上漲空間 ' + display_decimal(validation['calculated_upside'])+'%')
        p1_evidence += current['evidence_all']
    if methods:
        # 保留完整原文評價句，避免誤配倍數；同一報告有多法時全列、證據分立。
        basis = [m for m in methods if m['role'] == 'TARGET_BASIS']
        chosen = basis if basis else [m for m in methods if m['role'] == 'CURRENT_TRADING']
        used = set()
        for method in chosen:
            if method['id'] in used:
                continue
            used.add(method['id'])
            wording = ('目標價依據' if method['role'] == 'TARGET_BASIS' else '目前交易估值') + ' ' + method['zh_name']
            if method['multiple']:
                wording += ' ' + method['multiple'] + ' 倍'
            if method.get('forward_basis'):
                wording += '（1 年遠期 EPS）'
            if method['years']:
                wording += '（' + '/'.join(str(y) for y in method['years']) + 'E）'
            parts.append(wording)
            p1_evidence.append(method['evidence'])
    points = [{'index': 1, 'topic': 'valuation', 'text': '，'.join(parts)+'。' if parts else None,
               'status': 'EVIDENCE_FOUND' if parts else 'MISSING', 'evidence': p1_evidence}]
    forecast = [x for x in eps if x['forecast']]
    eps_parts = []
    for x in forecast:
        kind = {'DILUTED': 'Diluted EPS', 'CORE_DILUTED': 'Core Diluted EPS', 'CORE': 'Core EPS', 'UNSPECIFIED': 'EPS（原文未標示稀釋）'}[x['eps_type']]
        eps_parts.append(f'{x["year"]} 年 {kind} {x["value"]}' + (' '+x['currency'] if x['currency'] else '') + ('（計算 YoY '+display_decimal(x['yoy_calculated'])+'%）' if x['yoy_calculated'] is not None else ''))
    growth = insights[0] if insights and insights[0]['tags']['growth'] else None
    p2 = ((growth['text'] + '；') if growth else '') + '；'.join(eps_parts)
    points.append({'index': 2, 'topic': 'growth_and_annual_eps', 'text': p2 or None,
                   'status': 'EVIDENCE_FOUND' if p2 else 'MISSING',
                   'source_language': 'mixed' if growth and re.search('[A-Za-z]', growth['text']) else 'zh-TW',
                   'evidence': ([growth['evidence']] if growth else []) + [x['evidence'] for x in forecast]})
    rest = insights[1:] if growth else insights
    if len(rest) < 2:                                                     # v0110 有空點 → 短風險句後援(投資風險:氣候變化、中東衝突…)
        _used = {x['text'] for x in insights}
        _extra = [x for x in sentence_candidates(blocks_s, catalog, short_risk=True) if x['text'] not in _used and (not x['valuation'] or x['tags']['risk']) and x['text'] not in (p.get('text') for p in points)]
        _extra.sort(key=lambda x: (-int(bool(x['tags']['risk'])), -x['score']))
        rest = list(rest) + _extra[:2 - len(rest)]
    for i in range(2):
        row = rest[i] if i < len(rest) else None
        points.append({'index': i+3, 'topic': ('risk' if row['tags']['risk'] else max(row['tags'], key=row['tags'].get)) if row else 'unavailable',
                       'text': row['text'] if row else None, 'status': 'EXTRACTIVE' if row else 'MISSING',
                       'source_language': 'en' if row and re.search('[A-Za-z]', row['text']) else 'zh-TW',
                       'evidence': [row['evidence']] if row else []})
    # 本地 NLP 是原文萃取；不冒稱已翻譯。中文公司名稱只接受明示主檔欄位。
    original_title = clean_text(document.get('title_original', '')) or None
    company_zh = document.get('company_name_zh') or None
    title = f'{company_zh}: {original_title}' if company_zh and original_title else original_title
    missing = [f'point_{p["index"]}' for p in points if p['text'] is None]
    if company_zh is None:
        missing.append('company_name_zh_master')
    if original_title is None:
        missing.append('title_original')
    payload_rows = [p for p in points[2:] if p['text']]
    payload = [{'point': p['index'], 'text': p['text'], 'evidence': p['evidence']} for p in payload_rows]
    # 只準備可追溯的完整句，避免硬截後丟掉條件與否定詞。
    while sum(len(x['text']) for x in payload) > CONFIG['max_payload_chars']:
        payload.pop()
    result = {'schema': 'VRN_REPORT_SUMMARY/2', 'engine': 'VRN_ENG062_SummarizerV1', 'version': VERSION,
              'repository_commit': catalog['commit'], 'filename': filename, 'title': title,
              'title_original': original_title, 'company_name_zh': company_zh,
              'metrics': metrics, 'annual_eps': eps, 'valuation_evidence': methods,
              'broker_candidates': brokers, 'points': points, 'missing': missing,
              'issues': issues, 'validation': validation,
              'nlp': {'method': nlp_method, 'candidate_sentences': len(candidates),
                      'translation_status': 'NOT_TRANSLATED' if any(p.get('source_language') in ('en', 'mixed') for p in points) else 'SOURCE_ZH',
                      'micro_payload': payload, 'payload_chars': sum(len(x['text']) for x in payload), 'llm_calls': 0},
              'status': 'REVIEW' if issues or missing else 'EXTRACTED'}
    validate_summary(result, blocks_s)
    return result


def validate_summary(result, blocks):
    ids = {b['id']: b for b in blocks}
    if len(result['points']) != 4 or [x['index'] for x in result['points']] != [1,2,3,4]:
        raise ValueError('四點摘要契約錯誤')
    for p in result['points']:
        if p['text'] and not p['evidence']:
            raise ValueError('摘要缺來源證據')
        for e in p['evidence']:
            if e['block_id'] not in ids:
                raise ValueError('證據 block 不存在')
            block = ids[e['block_id']]
            # 換行只影響格式；數字/文字不准自行改寫。
            compact_quote = re.sub(r'\s+', '', clean_text(e['quote']))
            compact_block = re.sub(r'\s+', '', clean_text(block['text']))
            if compact_quote not in compact_block:
                raise ValueError(f'證據片段不在原文: {e["block_id"]}')
    return True


# ===== 07｜PDF 前處理：兩種文字工具互核，不假裝 OCR =====

def reconstruct_prose(blocks):
    """只連同頁同欄相鄰的散行；每組記錄來源 block，不跨欄拼接。"""
    eligible = []
    for b in blocks:
        text = clean_text(b['text'])
        if b.get('role') != 'table' and b['max_font_size'] <= 13.5 and len(text) > 30 and len(re.findall(r'[A-Za-z]{2,}', text)) >= 5 and not re.search(r'@|disclosure|FINRA|certification', text, re.I):
            eligible.append(b)
    groups = []
    for block in sorted(eligible, key=lambda x: (x['page'], round(x['bbox'][0]/20), x['bbox'][1])):
        if groups:
            prior = groups[-1][-1]
            gap = block['bbox'][1] - prior['bbox'][3]
            same = block['page'] == prior['page'] and abs(block['bbox'][0]-prior['bbox'][0]) <= 12 and abs(block['max_font_size']-prior['max_font_size']) <= 1 and 0 <= gap <= 10
        else:
            same = False
        if same:
            groups[-1].append(block)
        else:
            groups.append([block])
    result = []
    for gi, group in enumerate(groups):
        if len(group) < 2:
            continue
        for b in group:
            b['role'] = 'layout_fragment'
        result.append({'id': f'prose-{gi}', 'page': group[0]['page'], 'text': '\n'.join(x['text'] for x in group),
                       'source': group[0]['source'], 'bbox': [min(x['bbox'][0] for x in group), min(x['bbox'][1] for x in group), max(x['bbox'][2] for x in group), max(x['bbox'][3] for x in group)],
                       'source_block_ids': [x['id'] for x in group], 'role': 'prose'})
    return result

_BANNER = re.compile(r'(?i)^\s*(?:goldman\s+)?sachs\s*[|I｜l]?\s*(?:equity\s+)?research\s*$|^\s*(?:equity|global\s+investment)\s+research\s*$|^\s*research\s*$')


def _ocr_blocks(path, page_indexes):
    """v0107 影像頁 → VRN-2 OCR 隔離橋(子行程 · 主環境不 import OCR 套件)→ {頁: [(bbox, 文字, 估計字級)]}。"""
    import json as _j
    import os as _o
    import subprocess as _sp
    import tempfile as _tf
    py, br = _o.environ.get('VIA_VRN2_OCR_PY'), _o.environ.get('VIA_VRN2_OCR_BRIDGE')
    if not (py and br and Path(py).exists() and Path(br).exists()) or not page_indexes:
        return {}
    import fitz
    import hashlib as _h
    page_indexes = list(page_indexes)[:2]                                   # v0109 摘要只需首頁 + 第 2 頁
    d = Path(_o.environ.get('VIA_SPILL_DIR') or _tf.gettempdir()) / ('eng062_ocr_%d' % _o.getpid())
    d.mkdir(parents=True, exist_ok=True)
    cdir = _o.environ.get('VIA_VRN2_OCR_CACHE')
    try:
        ph = _h.sha1(Path(path).read_bytes()).hexdigest()[:16]
    except OSError:
        ph = None
    def cfile(i):
        if not (cdir and ph):
            return None
        Path(cdir).mkdir(parents=True, exist_ok=True)
        return Path(cdir) / ('%s_p%d_200.json' % (ph, i + 1))
    got, need = {}, []
    for i in page_indexes:
        cf = cfile(i)
        if cf and cf.exists():
            try:
                got[i] = ((_j.loads(cf.read_text(encoding='utf-8')).get('results') or [{}])[0])
                continue
            except Exception:  # noqa: BLE001
                pass
        need.append(i)
    if need:
        imgs = []
        with fitz.open(path) as pdf:
            for i in need:
                p = d / ('p%d.png' % (i + 1))
                pdf[i].get_pixmap(dpi=200).save(str(p))
                imgs.append(str(p))
        jf, of = d / 'job.json', d / 'out.json'
        jf.write_text(_j.dumps({'images': imgs}), encoding='utf-8')
        try:
            _sp.run([py, br, str(jf), str(of)], capture_output=True, timeout=600)
            o = _j.loads(of.read_text(encoding='utf-8'))
        except Exception:  # noqa: BLE001
            o = {}
        for i, r in zip(need, o.get('results') or []):
            got[i] = r
            cf = cfile(i)
            if cf:
                cf.write_text(_j.dumps({'engine': o.get('engine', ''), 'results': [r]}, ensure_ascii=False), encoding='utf-8')
    res = [got.get(i) or {} for i in page_indexes]
    out, k = {}, 72.0 / 200
    for i, r in zip(page_indexes, res):
        ls = []
        for x in r.get('lines') or []:
            xs, ys = [p[0] * k for p in x['box']], [p[1] * k for p in x['box']]
            ls.append(([min(xs), min(ys), max(xs), max(ys)], x['text'], (max(ys) - min(ys)) * 0.82))
        ls.sort(key=lambda t: (round(t[0][1] / 3), t[0][0]))
        blocks = []
        for bb, tx, sz in ls:
            hit = None
            for b in blocks:
                ov = min(bb[2], b[0][2]) - max(bb[0], b[0][0])
                if -1 <= bb[1] - b[0][3] <= max(4.0, 0.9 * (bb[3] - bb[1])) and ov >= 0.3 * min(bb[2] - bb[0], b[0][2] - b[0][0]):
                    hit = b
            if hit:
                hit[0] = [min(hit[0][0], bb[0]), hit[0][1], max(hit[0][2], bb[2]), max(hit[0][3], bb[3])]
                hit[1].append(tx)
                hit[2] = max(hit[2], sz)
            else:
                blocks.append([list(bb), [tx], sz])
        rows = []
        for bb, tx, sz in sorted(ls, key=lambda t: (t[0][1] + t[0][3]) / 2):
            yc = (bb[1] + bb[3]) / 2
            if rows and abs(rows[-1][0] - yc) <= max(3.0, 0.45 * (bb[3] - bb[1])):
                rows[-1][1].append((bb[0], tx))
            else:
                rows.append([yc, [(bb[0], tx)]])
        rowtext = '\n'.join('   '.join(t for _, t in sorted(r_[1])) for r_ in rows)     # 同一水平列:左欄標籤 + 右欄數值
        out[i] = {'blocks': [(b[0], '\n'.join(b[1]), b[2]) for b in blocks], 'rows': rowtext}
    return out


_NOT_TITLE = re.compile(r'(?i)\(\d{4}\.(?:TW|TWO)\)|\b\d{4}\s+TT\b|for the exclusive use|this report|investors should|disclosure|analyst|@|\+\d{2,3}[\s-]?\d|price target|target price|rating|^\s*(?:buy|sell|neutral|overweight|underweight)\s*$')

_NOT_TITLE_NB = re.compile(r'(?i)for the exclusive use|this report|investors should|disclosure|analyst|@|\+\d{2,3}[\s-]?\d|^\s*(?:buy|sell|neutral|overweight|underweight)\s*$')   # 接續行可含代號(GS:Quanta (2382.TW): …)


def _title_fallback(p1raw):
    """v0108 標題後援(頂部大字區沒有標題時):首頁上 60% · 左 65% · 字級 ≥10.5 · ≥20 字 · 非橫幅 / 代號 / 免責 / 分析師 · 粗體 +1.5 · 最大字 · 同字取最上。"""
    best = None
    for raw, w, h in p1raw:
        if raw['bbox'][1] > h * 0.6 or raw['bbox'][0] > w * 0.65:
            continue
        for line in raw['lines']:
            t = ''.join(s['text'] for s in line['spans']).strip()
            if len(t) < 20 or len(t) > 240 or _BANNER.match(t) or _NOT_TITLE.search(t) or not re.search(r'[A-Za-z\u4e00-\u9fff]{3}', t):
                continue
            size = max(s['size'] for s in line['spans'])
            bold = any(int(s.get('flags', 0)) & 16 for s in line['spans'])
            if size < 10.5:
                continue
            score = (size + (1.5 if bold else 0), -line['bbox'][1])
            if best is None or score > best[0]:
                li = raw['lines'].index(line)
                parts = [t]
                for step in (-1, 1):                                       # v0109 接同區塊同字級的上下行(跨行標題)
                    j = li + step
                    while 0 <= j < len(raw['lines']):
                        lj = raw['lines'][j]
                        tj = ''.join(s['text'] for s in lj['spans']).strip()
                        if not tj or abs(max(s['size'] for s in lj['spans']) - size) > 0.6 or _NOT_TITLE_NB.search(tj) or _BANNER.match(tj):
                            break
                        parts = ([tj] + parts) if step < 0 else (parts + [tj])
                        j += step
                best = (score, ' '.join(parts)[:240])
    return best[1] if best else ''


def pdf_document(path):
    path = Path(path)
    if path.stat().st_size > CONFIG['max_pdf_bytes']:
        raise ValueError('PDF 超過位元組上限')
    import fitz
    blocks, tables, headings, warnings, p1raw = [], [], [], [], []
    with fitz.open(path) as pdf:
        if pdf.is_encrypted:
            raise ValueError('PDF 加密，無法擷取')
        limit = min(len(pdf), CONFIG['max_pdf_pages'])
        if len(pdf) > limit:
            warnings.append('PAGE_LIMIT_REACHED')
        for page_index in range(limit):
            page = pdf[page_index]
            table_text = page.get_text('text')
            if table_text.strip():
                tables.append({'id': f'page-{page_index+1}', 'page': page_index+1, 'text': table_text,
                               'role': 'table_context', 'source': str(path), 'bbox': list(page.rect)})
            for bi, raw in enumerate(page.get_text('dict')['blocks']):
                if 'lines' not in raw:
                    continue
                text = '\n'.join(''.join(s['text'] for s in line['spans']) for line in raw['lines'])
                if not text.strip():
                    continue
                sizes = [s['size'] for line in raw['lines'] for s in line['spans']]
                block = {'id': f'p{page_index+1}-b{bi}', 'page': page_index+1, 'bbox': list(raw['bbox']),
                         'text': text, 'source': str(path), 'max_font_size': max(sizes)}
                if sum(bool(re.fullmatch(NUMBER + r'|--|-', line.strip())) for line in text.splitlines()) >= 2:
                    block['role'] = 'table'
                blocks.append(block)
                if page_index == 0:
                    p1raw.append((raw, page.rect.width, page.rect.height))
                if page_index == 0 and raw['bbox'][0] < page.rect.width*0.65 and raw['bbox'][1] < 260 and 11.5 <= max(sizes) <= 35 and (len(text.strip()) > 18 or (len(re.findall(r'[\u4e00-\u9fff]', text)) >= 5 and len(text.strip()) >= 8)) and not re.search(r'\(\d{4}\.(?:TW|TWO)\)|\(\d{4} TT\)|target price|share price|up/downside|price target', text, re.I):
                    candidate = dict(block)
                    big = [l for l in raw['lines'] if re.search(r'[A-Za-z\u4e00-\u9fff]', ''.join(s['text'] for s in l['spans']))]
                    if not big:
                        continue
                    top = max(s['size'] for l in big for s in l['spans'])
                    candidate['text'] = '\n'.join(''.join(s['text'] for s in line['spans']) for line in big if max(s['size'] for s in line['spans']) >= top-1)
                    candidate['max_font_size'] = top
                    if top >= 11.5 and 6 <= len(re.sub(r'\W', '', candidate['text'])) and len(candidate['text']) <= 240 and not _BANNER.match(candidate['text']):
                        headings.append(candidate)
        noText = [i for i in range(limit) if not pdf[i].get_text('text').strip()]
        ocr = _ocr_blocks(path, noText) if noText else {}
        for page_index, ob in sorted(ocr.items()):                     # v0107 影像頁 OCR 文字區塊
            bl = ob['blocks']
            warnings.append('OCR_TEXT_P%d' % (page_index + 1))
            tables.append({'id': f'page-{page_index+1}', 'page': page_index+1, 'text': ob['rows'],
                           'role': 'table_context', 'source': str(path), 'bbox': list(pdf[page_index].rect)})
            for bi, (bb, text, size) in enumerate(bl):
                block = {'id': f'p{page_index+1}-ocr{bi}', 'page': page_index+1, 'bbox': bb, 'text': text, 'source': str(path), 'max_font_size': size, 'reader': 'OCR'}
                if sum(bool(re.fullmatch(NUMBER + r'|--|-', line.strip())) for line in text.splitlines()) >= 2:
                    block['role'] = 'table'
                blocks.append(block)
                if page_index == 0 and bb[1] < 260 and 11.5 <= size <= 35:
                    for ln in text.splitlines():                                   # 逐行挑標題(公司名 + 標題常在同一區塊)
                        if len(ln.strip()) >= 12 and not _BANNER.match(ln) and not re.fullmatch(r'[\d\s,.%()-]+', ln):
                            hd = dict(block)
                            hd['text'] = ln.strip()
                            headings.append(hd)
        tables.sort(key=lambda x: x['page'])
        if not tables:
            raise ValueError('NO_TEXT_REVIEW_ONLY：沒有文字層，需既有 OCR 車道')
    # 本次標題候選依首頁大字定位，仍保留候選證據供人工核对。
    title = max(headings, key=lambda b: b['max_font_size'])['text'] if headings else _title_fallback(p1raw)
    blocks.extend(reconstruct_prose(blocks))
    # Finance row stacks以 raw page context 解析；指標候選也可使用頁級字串，兼容跨行標籤。
    first_page = next(x for x in tables if x['page'] == 1)
    first_page['role'] = 'header'
    blocks.append(first_page)
    blocks.extend(x for x in tables if x['page'] != 1)
    # 頁級段落不用再做質化 NLP，避免重複及跨欄拼接。
    for b in tables:
        b['role'] = 'header' if b['page'] == 1 else 'table'
    document = {'filename': path.name, 'title_original': clean_text(title),
                'blocks': blocks, 'table_blocks': tables, 'reader': 'PYMUPDF_LAYOUT' + (' + OCR' if any(w.startswith('OCR_TEXT') for w in warnings) else ''), 'reader_warnings': warnings}
    try:
        import pdfplumber
    except ImportError:
        document['reader_crosscheck'] = {'status': 'NODATA', 'reason': 'pdfplumber missing'}
    else:
        with pdfplumber.open(path) as other:
            secondary = other.pages[0].extract_text() or ''
        nums_primary = set(re.findall(NUMBER, first_page['text']))
        nums_other = set(re.findall(NUMBER, secondary))
        document['reader_crosscheck'] = {'status': 'OBSERVED', 'primary_unique_numbers': len(nums_primary),
                                        'secondary_unique_numbers': len(nums_other),
                                        'shared_unique_numbers': len(nums_primary & nums_other),
                                        'meaning': '讀取器交集只驗證文字層可讀，非整份財表財務驗算'}
    return document


def summarize_pdf(path, catalog=None, company_name_zh=None):
    document = pdf_document(path)
    document['company_name_zh'] = company_name_zh
    result = summarize_document(document, catalog)
    result['reader_crosscheck'] = document['reader_crosscheck']
    result['reader_warnings'] = document['reader_warnings']
    if document['reader_warnings']:
        result['status'] = 'REVIEW'
    return result


def export_result(result, output_root=None):
    """只增寫：內容哈希目錄、同結果沿用；CSV 與 Parquet 同時產生。"""
    output_root = Path(output_root or Path(__file__).parent / CONFIG['result_root'])
    content = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)
    key = hashlib.sha256((VERSION + content + hashlib.sha256(Path(__file__).read_bytes()).hexdigest()).encode()).hexdigest()[:20]
    target = output_root / key
    if (target / 'result.json').is_file():
        if (target / 'result.json').read_text(encoding='utf-8') != content:
            raise ValueError('快取內容衝突')
        return {'status': 'CACHED', 'directory': str(target)}
    try:
        import polars as pl
    except ImportError:
        pl = None
    target.mkdir(parents=True, exist_ok=False)
    rows = [{'filename': result['filename'], 'point': p['index'], 'topic': p['topic'],
             'text': p['text'], 'status': p['status'], 'evidence_json': json.dumps(p['evidence'], ensure_ascii=False)} for p in result['points']]
    try:
        with (target / 'summary.csv').open('w', encoding=CONFIG['encoding'], newline='') as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        if pl is not None:
            pl.DataFrame(rows).write_parquet(target / 'summary.parquet')
        else:
            (target / 'PARQUET_SKIPPED.txt').write_text('polars 未安裝 · CSV / JSON 已寫', encoding='utf-8')
        (target / 'result.json').write_text(content, encoding='utf-8')
    except BaseException:
        # 部分結果保留可診斷，下一輪以缺 result.json 識別，不回報成功。
        (target / 'FAILED.txt').write_text('export incomplete', encoding='utf-8')
        raise
    return {'status': 'WRITTEN', 'directory': str(target), 'parquet': 'WRITTEN' if pl is not None else 'SKIPPED(polars 未安裝)'}


def main():
    if any(flag in sys.argv for flag in ('--ticker', '--status', '--test')):
        return load_previous().main() or 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, help='PDF 或包含 blocks 的 JSON')
    parser.add_argument('--catalog', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--company-name-zh', default=None, help='經官方主檔核對的中文公司名稱')
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()
    if args.selftest:
        import unittest
        suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent), pattern='test_summary*.py')
        runner = unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if runner.wasSuccessful() and runner.testsRun else 1
    if not args.input:
        parser.error('請指定 --input 或 --selftest')
    catalog = load_catalog(args.catalog)
    if args.input.suffix.lower() == '.pdf':
        result = summarize_pdf(args.input, catalog, args.company_name_zh)
    else:
        document = json.loads(args.input.read_text(encoding='utf-8-sig'))
        result = summarize_document(document, catalog)
    receipt = export_result(result, args.output)
    print(json.dumps({'version': VERSION, 'status': result['status'], 'export': receipt,
                      'issues': result['issues'], 'missing': result['missing']}, ensure_ascii=False))
    return 0 if result['status'] == 'EXTRACTED' else 2


if __name__ == '__main__':
    raise SystemExit(main())
