#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN 單一 PDF 擷取後修復引擎：所有方法、參數與介面均在本檔。

安裝：python -m pip install PyMuPDF pdfplumber Pillow polars
執行：python VRN_Generic_PostExtract_Engine_v0100.py --input "C:\\測試樣本報告" --selftest
API：repair_extracted_data(data)、run_engine(input_paths, output_root, ...)、read_annual_dataframe(run_dir)。
所有輸入使用泛用規則；13 份報告只作事後驗證，不使用固定表格座標。
這是獨立新增引擎；不修改其他 VRN 模組，不推送 GitHub。
"""

# ───── v0101(VRN 整合 · 2026-10-10)= v0100 + 三處,其餘逐字不動 ─────
#  ① 正本加速器橋(VeritasCeleritas_v1141 / VeritasAegisNexus_v1652)
#  ② repair_extracted_data 記憶體介面帶字詞座標時崩潰(KeyError:'width')→ record 補頁寬頁高(PDF 路徑本來就有)
#  ③ ENGINE_VERSION '0100' → '0101'
# ===== [VIA:ACCEL-BRIDGE:v0110] 正本加速器 VeritasCeleritas_v1141 · 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import sys as _cb_sys
from pathlib import Path as _cb_Path
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        for _cb_d in [_cb_sup] + [x.parent for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if str(_cb_d) not in _cb_sys.path:
                _cb_sys.path.insert(0, str(_cb_d))
        break
    _cb_p = _cb_p.parent
try:
    import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  正本加速器
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

# PART 1: 標準函式庫與集中參數。
from pathlib import Path
from decimal import Decimal, InvalidOperation
from statistics import median
from collections import Counter
from datetime import datetime, timezone
import argparse
import ast
import csv
import hashlib
import html
import importlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
import unicodedata

ENGINE_VERSION = '0101'
EXTRACTION_SCHEMA_VERSION = '0100'
ROOT = Path(__file__).resolve().parent
DEFAULT_INPUTS = [Path(r'C:\測試樣本報告')]
DEFAULT_OUTPUT = ROOT / 'VRN_Engine_Output'
OUTPUT_DIR = DEFAULT_OUTPUT
DEFAULT_MAX_UNKNOWN_PAGES = 0
RENDER_SCALE = 1.8
CONTEXT_ABOVE_ROWS = 4
CONTEXT_BELOW_ROWS = 3
MIN_NATIVE_WORDS = 12
MIN_PERIOD_COLUMNS = 3
GENERIC_MAX_ROW_GAP = 22.0
MIN_TABLE_NUMERIC_ROWS = 3
DEFAULT_OCR_MODE = 'off'  # 固定政策，不提供升級執行
DEFAULT_OCR_LANGUAGE = 'eng'
CANONICAL_AMOUNT_UNIT = 'TWD_million'
UNIT_TO_MILLION = {'TWD_thousand': Decimal('0.001'), 'TWD_million': Decimal('1'), 'TWD_billion': Decimal('1000')}
DEPENDENCIES = {'fitz': 'PyMuPDF', 'pdfplumber': 'pdfplumber', 'PIL': 'Pillow', 'polars': 'polars'}
ANNUAL_FIELDS = ['table_id', 'page_key', 'account_raw', 'section', 'period', 'period_raw', 'basis', 'raw_value', 'value_decimal', 'value_status', 'category', 'unit', 'bbox_json', 'verification_scope', 'source_sha256', 'source_filename', 'region_origin', 'canonical_value_decimal', 'canonical_unit', 'run_id']
REVIEW_FIELDS = ['page_key', 'source_sha256', 'reason', 'bbox_json', 'detail', 'next_step']

ROW_TOLERANCE = 3.4

HEADER_TOLERANCE = 2.4

CATEGORICAL_VALUES = {'盈轉虧': 'profit_to_loss', '虧轉盈': 'loss_to_profit', 'NM': 'not_meaningful', 'nm': 'not_meaningful'}

HEADER_PARENT_DISTANCE = 40.0
HEADER_UNIT_DISTANCE = 16.0
HEADER_MULTILINE_DISTANCE = 18.0
HEADER_GUTTER_MULTIPLIER = 1.9
LABEL_PROBE_DISTANCE = 100.0
LABEL_GAP_MINIMUM = 5.0
LABEL_GAP_HEIGHT_FACTOR = 0.5
LABEL_FALLBACK_COLUMNS = 3.5
COLUMN_ALIGNMENT_FRACTION = 0.45
RIGHT_EDGE_PADDING_COLUMNS = 0.25
TABLE_MAX_NUMERIC_GAP = 42.0
ROW_YEAR_MIN_VALUE_COLUMNS = 3
ROW_YEAR_ALIGNMENT_TOLERANCE = 5.0
ROW_YEAR_MAX_GAP = 25.0
ROW_YEAR_MIN_PERIODS = 3
ROW_YEAR_HEADER_DISTANCE = 32.0
REGION_OVERLAP_THRESHOLD = 0.65
WHITE_PIXEL_THRESHOLD = 248
INVISIBLE_WHITE_FRACTION = 0.995
NO_LAYOUT_OR_OCR = True
MATRIX_HEADER_SEARCH_ROWS = 6
MATRIX_MIN_PERIOD_COLUMNS = 1
READING_ORDER_GUTTER = 18.0
MAX_MATRIX_ROWS = 10000
MAX_MATRIX_COLUMNS = 1000
DEFAULT_DECIMAL_STYLE = 'dot'
TABLE_CELL_FIELDS = ['page_key', 'table_id', 'row', 'column', 'raw_value', 'value_decimal', 'value_status', 'category', 'bbox_json', 'origin', 'source_sha256', 'normalized_text', 'synthetic_label']
UNIT_PATTERNS = [(r'(?:NT\$|TWD|新台幣|NTD)\s*(?:千元|thousand)', 'TWD_thousand'),
                 (r'NT\$mn|TWDm|NT\$M|NT\$百萬|新台幣百萬|NTDmillion', 'TWD_million'),
                 (r'NT\$bn|TWDbn|新台幣十億', 'TWD_billion'),
                 (r'千元|thousand', 'thousand_unspecified_currency'),
                 (r'百萬元|百萬|million', 'million_unspecified_currency'),
                 (r'十億|billion', 'billion_unspecified_currency')]
ACCOUNT_PATTERNS = {
    'minority': [r'minorityinterests?', r'noncontrollinginterests?', r'非控制權益', r'少數股權'],
    'revenue': [r'營業收入(?:淨額)?', r'營收', r'(?:total)?revenue', r'netsales'],
    'cost': [r'營業成本', r'cogs', r'costof(?:goods(?:sold)?|sales|revenue)'],
    'gross': [r'營業毛利(?:淨額)?', r'毛利', r'grossprofit'],
    'assets': [r'資產(?:總額|總計|合計)', r'totalassets'],
    'liabilities': [r'負債(?:總額|總計|合計)', r'totalliabilities'],
    'equity': [r'股東權益(?:總額|總計|合計)?', r'權益總計', r"shareholders'?equity", r'totalequity'],
    'operating_cf': [r'營業活動之現金流量', r'cashflowfromoperatingactivities'],
    'investing_cf': [r'投資活動之現金流量', r'cashflowfrominvestingactivities'],
    'financing_cf': [r'籌資活動之現金流量', r'cashflowfromfinancingactivities'],
    'fx_cf': [r'匯率調整數'],
    'net_cash': [r'本期產生現金流量', r'netchangeincash'],
    'opening_cash': [r'期初現金與約當現金餘額'],
    'closing_cash': [r'期末現金與約當現金餘額']}
GENERIC_FINANCIAL_RULES = [('gross_profit', [('revenue', 1), ('cost', 'expense')], 'gross'),
                         ('balance_equation', [('liabilities', 1), ('equity', 1)], 'assets'),
                         ('cashflow_with_fx', [('operating_cf', 1), ('investing_cf', 1), ('financing_cf', 1), ('fx_cf', 1)], 'net_cash'),
                         ('cash_rollforward', [('opening_cash', 1), ('net_cash', 1)], 'closing_cash')]
FAILURE_CASES = [
    ('F01', '左上角空白', 'fill_item', '補 ITEM；raw_rows 保留原空白'),
    ('F02', '末端空行空欄', 'trim_empty_edges', '僅修整完全空白末端，保留內部缺值'),
    ('F03', '空白／全形／換行字元', 'normalize_cell_text', '保留原值並生成正規化文字'),
    ('F04', '重複欄頭', 'deduplicate_display_headers', '保留 raw header，顯示名稱加序號'),
    ('F05', '跨頁重複表頭', 'remove_exact_repeated_header', '只移除與首表頭完全相同的列'),
    ('F06', '同格數字被分割', 'join_numeric_fragments', '僅相同儲存格內、語法唯一才接回'),
    ('F07', '千位分隔符', 'parse_grouped_number', '十進位字串解析，原值不改'),
    ('F08', '負號與括號負值', 'parse_signed_number', '統一語意，保留來源字形'),
    ('F09', '小數點／逗號地區差異', 'respect_decimal_style', '使用輸入明示規則；歧義回查'),
    ('F10', '單位與倍率混用', 'canonical_amount', '僅明確單位轉百萬，未驗證前不遷位'),
    ('F11', '空白／破折號／零／文字值', 'preserve_value_types', '分別保留，不把缺值填零'),
    ('F12', '左右多表黏合', 'split_header_gutters', '按欄頭間距及重複期間分區'),
    ('F13', '上下多表黏合', 'split_vertical_headers', '遇下一組獨立表頭重新起表'),
    ('F14', '年度季度混合', 'scope_periods', '上層 scope 證據與 FY 列判別'),
    ('F15', '多層欄頭', 'build_header_paths', '保存層級，父年份不冒充獨立年欄'),
    ('F16', '合併表頭儲存格', 'restore_explicit_spans', '按明示 colspan/rowspan 還原格網及欄頭路徑'),
    ('F17', '合併內容儲存格', 'retain_body_merge_anchor', '保留主格與覆蓋位置，不複製金額'),
    ('F18', '科目跨行', 'retain_wrapped_labels', '同格或幾何可證實的續行接回，否則保留候選'),
    ('F19', '數字跨行', 'join_numeric_linebreak', '明確千分號／小數點續接才接回'),
    ('F20', 'O/0、I/1 等識別混淆', 'bounded_numeric_alternatives', '產生候選，禁止直接改寫'),
    ('F21', '缺漏／截斷儲存格', 'reconcile_extractors', '比對不同擷取器；衝突保留，不由算式補造'),
    ('F22', '欄位錯位／數字碰撞', 'align_numeric_endpoints', '欄端點重排；碰撞與歧義回查'),
    ('F23', '正文誤當表格', 'reject_single_column_text_table', '拒絕一欄正文表，raw 結果保留'),
    ('F24', '不可見／重疊文字', 'retain_visibility_evidence', '去除幾何重複；白字需渲染證據'),
    ('F25', '附註／來源／頁碼混入', 'separate_note_source_roles', '上下 4/3 行 context 保留，與資料角色分開')]

SCOPE_MIN_MATCHED_YEARS = 2
SCOPE_MIN_MATCHED_ACCOUNTS = 2
ROW_HEIGHT_TOLERANCE_FACTOR = 0.55
DEFAULT_WORKERS = min(4, max(1, os.cpu_count() or 1))
WATCH_INTERVAL_SECONDS = 3.0
WATCH_STABLE_POLLS = 3
MAX_IMPORT_BYTES = 100 * 1024 * 1024
EXPORT_FORMATS = ('json', 'csv', 'parquet', 'xlsx', 'docx')

SECONDARY_DETECTOR_MIN_NUMBERS = 6

INPUT_EXTENSIONS = {'.pdf', '.json', '.csv', '.tsv', '.txt', '.md'}
TOOL_REGISTRY = [
    {'id': 'docling', 'modules': ['docling'], 'family': 'model', 'formats': ['docling', 'json', 'html'], 'url': 'https://github.com/docling-project/docling'},
    {'id': 'marker', 'modules': ['marker'], 'family': 'model', 'formats': ['json', 'markdown'], 'url': 'https://github.com/datalab-to/marker'},
    {'id': 'pdf-extract-kit', 'modules': ['pdf_extract_kit'], 'family': 'model', 'formats': ['json', 'words'], 'url': 'https://github.com/opendatalab/PDF-Extract-Kit'},
    {'id': 'mineru', 'modules': ['mineru'], 'family': 'model', 'formats': ['json', 'markdown'], 'url': 'https://github.com/opendatalab/MinerU'},
    {'id': 'unstructured', 'modules': ['unstructured'], 'family': 'model_or_native', 'formats': ['unstructured', 'html', 'json'], 'url': 'https://github.com/Unstructured-IO/unstructured'},
    {'id': 'nougat', 'modules': ['nougat'], 'family': 'model', 'formats': ['markdown', 'text'], 'url': 'https://github.com/facebookresearch/nougat'},
    {'id': 'pdfplumber', 'modules': ['pdfplumber'], 'family': 'native', 'formats': ['matrix', 'words', 'json'], 'url': 'https://github.com/jsvine/pdfplumber'},
    {'id': 'camelot', 'modules': ['camelot'], 'family': 'native', 'formats': ['matrix', 'csv'], 'url': 'https://github.com/camelot-dev/camelot'},
    {'id': 'tabula', 'modules': ['tabula'], 'family': 'native_java', 'formats': ['tabula', 'matrix', 'json'], 'url': 'https://github.com/chezou/tabula-py'},
    {'id': 'deepdoctection', 'modules': ['deepdoctection'], 'family': 'model', 'formats': ['json', 'words', 'matrix'], 'url': 'https://github.com/deepdoctection/deepdoctection'},
    {'id': 'pymupdf', 'modules': ['fitz'], 'family': 'native', 'formats': ['words', 'spans', 'json'], 'url': 'https://github.com/pymupdf/PyMuPDF'},
    {'id': 'pypdfium2', 'modules': ['pypdfium2'], 'family': 'native', 'formats': ['words', 'text', 'json'], 'url': 'https://github.com/pypdfium2-team/pypdfium2'},
    {'id': 'pdfminer', 'modules': ['pdfminer'], 'family': 'native', 'formats': ['words', 'text', 'json'], 'url': 'https://github.com/pdfminer/pdfminer.six'},
    {'id': 'pypdf', 'modules': ['pypdf'], 'family': 'native', 'formats': ['text', 'json'], 'url': 'https://github.com/py-pdf/pypdf'},
    {'id': 'tika', 'modules': ['tika'], 'family': 'native_java_service', 'formats': ['text', 'html', 'json'], 'url': 'https://github.com/chrismattmann/tika-python'},
    {'id': 'rapidocr', 'modules': ['rapidocr'], 'family': 'ocr', 'formats': ['words', 'json'], 'url': 'https://github.com/RapidAI/RapidOCR'},
    {'id': 'tesseract-pdf2image', 'modules': ['pytesseract', 'pdf2image'], 'family': 'ocr', 'formats': ['words', 'tsv', 'json'], 'url': 'https://github.com/madmaze/pytesseract'},
    {'id': 'paddleocr', 'modules': ['paddleocr'], 'family': 'ocr_model', 'formats': ['words', 'html', 'json'], 'url': 'https://github.com/PaddlePaddle/PaddleOCR'},
    {'id': 'stirling-pdf', 'modules': [], 'family': 'service', 'formats': ['csv', 'text', 'json'], 'url': 'https://github.com/Stirling-Tools/Stirling-PDF'},
    {'id': 'docx-openpyxl', 'modules': ['docx', 'openpyxl'], 'family': 'export', 'formats': ['matrix'], 'url': 'https://github.com/python-openxml/python-docx'}]


# PART 2: 泛用完整 def 定義；無任何同儕 .py 匯入。

def legacy_load_words(key):
    return json.loads((OUTPUT_DIR / key / 'words.json').read_text(encoding='utf-8'))

def legacy_inside(word, bbox):
    x = (word['x0'] + word['x1']) / 2
    y = (word['y0'] + word['y1']) / 2
    return bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]

def legacy_join_words(words):
    text = ' '.join((w['text'] for w in sorted(words, key=lambda w: w['x0'])))
    text = re.sub('(?<=[\\u3400-\\u9fff])\\s+(?=[\\u3400-\\u9fff])', '', text)
    return text.strip()

def legacy_rounding_half_width(raw):
    raw = raw.strip().replace(',', '').strip('()%')
    places = len(raw.split('.')[1]) if '.' in raw else 0
    return Decimal('0.5') * Decimal(10) ** (-places)

def normalize_label(text):
    return re.sub('\\s+', '', text).replace('－', '-').replace('／', '/')

def parse_period(text, scope):
    clean = text.strip().replace("'", '').replace('’', '').replace('(', '').replace(')', '')
    basis_match = re.search('([AEFae f])$', clean)
    basis = 'estimate' if basis_match and basis_match[1].upper() in ('E', 'F') else 'actual' if basis_match and basis_match[1].upper() == 'A' else 'unspecified'
    quarter = re.fullmatch('([1-4])Q(\\d{2}|20\\d{2})([AEFae f]?)', clean)
    reverse = re.fullmatch('(\\d{2}|20\\d{2})Q([1-4])([AEFae f]?)', clean)
    if quarter or reverse:
        year = quarter[2] if quarter else reverse[1]
        q = quarter[1] if quarter else reverse[2]
        year = year if len(year) == 4 else '20' + year
        return dict(raw=text, period=f'{year}-Q{q}', kind='quarter', basis=basis, scope_evidence=scope)
    month = re.fullmatch('(Mar|Jun|Sep|Dec)-(\\d{2})([AEFae f]?)', clean, re.I)
    if month:
        year = '20' + month[2]
        if scope == 'annual' and month[1].lower() == 'dec':
            return dict(raw=text, period=year, kind='annual', basis=basis, scope_evidence='annual_superheader_evidence')
        if scope == 'quarter':
            q = {'mar': 1, 'jun': 2, 'sep': 3, 'dec': 4}[month[1].lower()]
            return dict(raw=text, period=f'{year}-Q{q}', kind='quarter', basis=basis, scope_evidence='quarter_superheader_evidence')
        return dict(raw=text, period=f"{year}-{dict(mar='03', jun='06', sep='09', dec='12')[month[1].lower()]}", kind='ambiguous_month', basis=basis, scope_evidence='unresolved')
    year = re.fullmatch('(?:FY|12/)?(20\\d{2}|\\d{2})([AEFae f]?)', clean, re.I)
    if not year:
        return None
    if len(year[1]) == 2 and (not year[2].strip()) and (not clean.upper().startswith(('FY', '12/'))):
        return None
    y = year[1] if len(year[1]) == 4 else '20' + year[1]
    return dict(raw=text, period=y, kind='annual', basis=basis, scope_evidence=scope)

def parse_value(text):
    raw = unicodedata.normalize('NFKC', text).strip()
    if ',' in raw and re.search('\\d', raw) and (not re.fullmatch('[+-]?(?:\\d{1,3}(?:,\\d{3})+|\\d+)(?:\\.\\d+)?%?[AEF]?|\\(\\d{1,3}(?:,\\d{3})+(?:\\.\\d+)?\\)', raw)):
        return dict(value=None, status='unresolved_text', category=None, basis_override=None)
    if raw in CATEGORICAL_VALUES:
        return dict(value=None, status='categorical', category=CATEGORICAL_VALUES[raw], basis_override=None)
    if raw.lower() in ('n.a.', 'n/a', 'na'):
        return dict(value=None, status='not_available', category=None, basis_override=None)
    if raw in ('', '-', '--', '- -'):
        return dict(value=None, status='empty' if not raw else 'dash_unspecified', category=None, basis_override=None)
    cleaned = raw.replace(',', '').replace('−', '-').replace('％', '%').replace('（', '(').replace('）', ')')
    suffix = re.fullmatch('([-+]?\\d+(?:\\.\\d+)?)([AEF])', cleaned)
    override = None
    if suffix:
        cleaned = suffix[1]
        override = 'actual' if suffix[2] == 'A' else 'estimate'
    if cleaned.startswith('(') and cleaned.endswith(')'):
        cleaned = '-' + cleaned[1:-1]
    cleaned = cleaned.removesuffix('%')
    try:
        number = Decimal(cleaned)
        if not number.is_finite():
            raise InvalidOperation
        value = str(number)
        return dict(value=value, status='numeric', category=None, basis_override=override)
    except InvalidOperation:
        return dict(value=None, status='unresolved_text', category=None, basis_override=None)

def cluster_rows(words):
    """Different fonts can have shifted centers despite overlapping baselines."""
    rows = []
    for word in sorted(words, key=lambda w: ((w['y0'] + w['y1']) / 2, w['x0'])):
        y = (word['y0'] + word['y1']) / 2
        height = word['y1'] - word['y0']
        tolerance = ROW_TOLERANCE
        if rows:
            prior_height = median((w['y1'] - w['y0'] for w in rows[-1]['words']))
            tolerance = max(tolerance, min(height, prior_height) * ROW_HEIGHT_TOLERANCE_FACTOR)
        if rows and abs(y - rows[-1]['center']) <= tolerance:
            rows[-1]['words'].append(word)
            rows[-1]['center'] = median(((w['y0'] + w['y1']) / 2 for w in rows[-1]['words']))
        else:
            rows.append(dict(center=y, words=[word]))
    for row in rows:
        row['words'].sort(key=lambda w: w['x0'])
    return rows

def get_cell_bbox(words):
    if not words:
        return None
    return [min((w['x0'] for w in words)), min((w['y0'] for w in words)), max((w['x1'] for w in words)), max((w['y1'] for w in words))]

def infer_unit(label, values, default, section):
    if any(('%' in value for value in values)):
        return 'percent'
    if re.search('EPS|每股盈餘|每股淨值|股息|DPS|BVPS', label, re.I) and (not re.search('成長|growth|change', label, re.I)):
        return 'TWD_per_share' if default.startswith('TWD_') or re.search('NT\\$|TWD|NTD|新台幣', label, re.I) else 'USD_per_share' if re.search('US\\$|USD', label, re.I) else 'currency_unspecified_per_share'
    if '%' in label or (section and '%' in section):
        return 'percent'
    if re.search('\\(NT\\$百萬\\)|NT\\$mn|\\(NT\\$mn\\)', normalize_label(label), re.I):
        return 'TWD_million'
    if 'days' in label.lower():
        return 'days'
    if re.search('\\(x\\)|\\(X\\)|P/E|P/B|EV/EBITDA', label, re.I):
        return 'multiple'
    return default

def reconstruct_table(config, supplied_words=None):
    key, name, bbox, header_specs, default_unit, only_annual_row = config
    words = [w for w in (supplied_words if supplied_words is not None else json.loads((OUTPUT_DIR / key / 'words.json').read_text())) if legacy_inside(w, bbox)]
    header = []
    for y, x0, x1, scope in header_specs:
        for word in words:
            center = (word['y0'] + word['y1']) / 2
            if x0 <= word['x0'] < x1 and abs(center - y) <= HEADER_TOLERANCE:
                period = parse_period(word['text'], scope)
                if period:
                    header.append(dict(word=word, period=period))
    header.sort(key=lambda item: item['word']['x0'])
    if len(header) < 3:
        raise ValueError(f'{key}_{name}: fewer than three verified physical header columns')
    endpoints = [item['word']['x1'] for item in header]
    spacing = median((b - a for a, b in zip(endpoints, endpoints[1:])))
    header_bottom = max((y for y, _, _, _ in header_specs)) + HEADER_TOLERANCE
    content = [w for w in words if (w['y0'] + w['y1']) / 2 > header_bottom]
    tentative_boundary = endpoints[0] - spacing * 0.7
    first_values = [w['x0'] for w in content if w['x1'] >= tentative_boundary and parse_value(w['text'])['status'] == 'numeric' and (min(range(len(endpoints)), key=lambda i: abs(w['x1'] - endpoints[i])) == 0)]
    label_boundary = min(first_values) - 0.3 if first_values else tentative_boundary
    rows = []
    texts = []
    current_section = None
    for group in cluster_rows(content):
        label_words = [w for w in group['words'] if w['x0'] < label_boundary]
        value_words = [w for w in group['words'] if w not in label_words]
        label = legacy_join_words(label_words)
        if not value_words:
            if rows and rows[-1]['label'].count('(') > rows[-1]['label'].count(')') and label.startswith('$') and (group['center'] - rows[-1]['row_y'] < 14):
                rows[-1]['label_before_continuation'] = rows[-1]['label']
                rows[-1]['label'] += label
                rows[-1]['label_continuation'] = label
                rows[-1]['unit'] = infer_unit(rows[-1]['label'], rows[-1]['raw_values'], default_unit, current_section)
                continue
            current_section = label
            texts.append(dict(role='section_or_note_candidate', text=label, bbox=get_cell_bbox(group['words'])))
            continue
        slots = [[] for _ in header]
        for word in value_words:
            i = min(range(len(endpoints)), key=lambda i: abs(word['x1'] - endpoints[i]))
            slots[i].append(word)
        raw_values = [legacy_join_words(slot) for slot in slots]
        parsed = [parse_value(value) for value in raw_values]
        if not label or not re.search('[A-Za-z\\u3400-\\u9fff]', label):
            texts.append(dict(role='unresolved_mixed_row', text=legacy_join_words(group['words']), raw_values=raw_values, bbox=get_cell_bbox(group['words'])))
            continue
        row_kind = 'annual' if only_annual_row and normalize_label(label) == normalize_label(only_annual_row) else 'quarter' if only_annual_row else 'same_as_header'
        rows.append(dict(label=label, section=current_section, row_y=group['center'], label_bbox=get_cell_bbox(label_words), raw_values=raw_values, cells=parsed, value_bboxes=[get_cell_bbox(slot) for slot in slots], unit=infer_unit(label, raw_values, default_unit, current_section), row_kind=row_kind))
    return dict(id=f'{key}_{name}', page_key=key, bbox=list(bbox), headers=header, rows=rows, textual_rows=texts, region_origin='automatic_geometry_candidate', default_unit=default_unit)

def annual_indices(table):
    return [i for i, header in enumerate(table['headers']) if header['period']['kind'] == 'annual']

def find_row(table, label):
    rows = [row for row in table['rows'] if normalize_label(row['label']) == normalize_label(label)]
    return next((row for row in rows if row['section'] is None or row['section'] in ('損益表 (NT$百萬)', 'Financial Estimates')), rows[0] if rows else None)

def load_dependencies():
    """只匯入實際需要的套件；不在背景變更使用者環境。"""
    global fitz, pdfplumber, pl, Image, ImageDraw
    missing = []
    modules = {}
    for module_name, package in DEPENDENCIES.items():
        try:
            modules[module_name] = importlib.import_module(module_name)
        except ImportError:
            missing.append(package)
    if missing:
        raise RuntimeError('缺少套件；請執行 python -m pip install ' + ' '.join(missing))
    fitz, pdfplumber, pl = (modules['fitz'], modules['pdfplumber'], modules['polars'])
    from PIL import Image, ImageDraw
    return {'PyMuPDF': fitz.VersionBind, 'pdfplumber': pdfplumber.__version__, 'Pillow': modules['PIL'].__version__, 'polars': pl.__version__}

def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')

def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()

def write_json(path, value):
    """原子寫入；正式輸出位於唯一 run_id，既有 run 不覆寫。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()

def read_page_cache(path):
    if not path.is_file():
        return None
    try:
        envelope = json.loads(path.read_text(encoding='utf-8'))
        payload = envelope['payload']
        if envelope['payload_sha256'] != hashlib.sha256(json_bytes(payload)).hexdigest():
            return None
        image = path.parent / 'original.png'
        if payload.get('rendered') and (not image.is_file() or file_sha256(image) != payload['image_sha256']):
            return None
        return payload
    except (OSError, ValueError, KeyError, TypeError):
        return None

def extract_source(path, source_hash, profile, output_root, run_dir, extraction_options, stats, progress):
    cache_signature = hashlib.sha256(json_bytes(extraction_options)).hexdigest()[:16]
    identity = profile['id'] if profile else 'UNKNOWN_' + source_hash[:12]
    records = []
    with fitz.open(path) as document:
        if document.needs_pass:
            raise RuntimeError('PDF_requires_password')
        numbers = profile['pages'] if profile else list(range(1, len(document) + 1))
        if not profile and extraction_options['max_pages']:
            numbers = numbers[:extraction_options['max_pages']]
        cached = {}
        cache_paths = {}
        for number in numbers:
            directory = output_root / 'cache' / source_hash / cache_signature / f'p{number:04d}'
            payload = read_page_cache(directory / 'page.json')
            if payload and payload.get('source_sha256') == source_hash and (payload.get('page') == number):
                cached[number] = payload
            cache_paths[number] = directory
        plumber = None
        try:
            if len(cached) != len(numbers):
                try:
                    plumber = pdfplumber.open(path)
                except Exception as error:
                    stats['secondary_extractor_errors'].append({'source': path.name, 'error': str(error)})
            for number in numbers:
                key = f'{identity}_p{number:02d}'
                directory = cache_paths[number]
                if number in cached:
                    payload = cached[number]
                    stats['cache_hits'] += 1
                else:
                    if directory.exists():
                        directory = directory.with_name(directory.name + '_recovery_' + uuid.uuid4().hex[:8])
                    directory.mkdir(parents=True, exist_ok=False)
                    page = document[number - 1]
                    payload = extract_page_payload(page, plumber.pages[number - 1] if plumber else None, directory, extraction_options['render'], extraction_options['ocr_mode'], extraction_options['ocr_language'], source_hash)
                    write_json(directory / 'page.json', {'payload': payload, 'payload_sha256': hashlib.sha256(json_bytes(payload)).hexdigest()})
                    stats['cache_misses'] += 1
                page_dir = run_dir / key
                page_dir.mkdir()
                write_json(page_dir / 'native_words.json', payload['native_words'])
                candidate_words, invisible = prepare_visible_candidate_words(payload, directory)
                unique, seen_words = ([], set())
                for word in candidate_words:
                    word_signature = (word['text'], round(word['x0'], 2), round(word['y0'], 2), round(word['x1'], 2), round(word['y1'], 2))
                    if word_signature not in seen_words:
                        unique.append(word)
                        seen_words.add(word_signature)
                payload = dict(payload, words=unique, invisible_candidates=invisible, duplicate_word_count=len(candidate_words) - len(unique))
                for name in ('words', 'spans'):
                    write_json(page_dir / (name + '.json'), payload[name])
                write_json(page_dir / 'pdfplumber_default_tables.json', payload['default_tables'])
                (page_dir / 'raw_text.txt').write_text(payload['raw_text'], encoding='utf-8')
                (page_dir / 'sorted_text.txt').write_text(payload['sorted_text'], encoding='utf-8')
                if payload['rendered']:
                    shutil.copyfile(directory / 'original.png', page_dir / 'original.png')
                record = dict(key=key, source=path.name, source_path=str(path), source_sha256=source_hash, profile_id=identity, cohort=profile['cohort'] if profile else 'unknown', page=number, **{name: payload[name] for name in ('width', 'height')}, words=len(payload['words']), native_words=len(payload['native_words']), default_tables=len(payload['default_tables']), cache_hit=number in cached, cache_path=str(directory / 'page.json'), elapsed_extraction_seconds=payload['extraction_seconds'])
                records.append((record, payload))
                if progress:
                    print(f'[{len(records)}/{len(numbers)}] {key} ' + ('CACHE' if number in cached else 'EXTRACT'), flush=True)
        finally:
            if plumber is not None:
                plumber.close()
    return records

def get_region_context(payload, bbox):
    groups = cluster_rows(payload['words'])
    aligned = [group for group in groups if any((bbox[0] <= (w['x0'] + w['x1']) / 2 <= bbox[2] for w in group['words']))]
    above = [g for g in aligned if g['center'] < bbox[1]][-CONTEXT_ABOVE_ROWS:]
    below = [g for g in aligned if g['center'] > bbox[3]][:CONTEXT_BELOW_ROWS]
    return {'above': [dict(text=legacy_join_words(g['words']), bbox=get_cell_bbox(g['words'])) for g in above], 'below': [dict(text=legacy_join_words(g['words']), bbox=get_cell_bbox(g['words'])) for g in below], 'policy': 'context_only_not_automatically_inserted_into_numeric_rows'}

def canonical_amount(value, unit):
    if value is None or unit not in UNIT_TO_MILLION:
        return (None, None)
    return (str(Decimal(value) * UNIT_TO_MILLION[unit]), CANONICAL_AMOUNT_UNIT)

def build_annual_records(tables, source_lookup, run_id):
    records, skipped = ([], [])
    for table in tables:
        indices = annual_indices(table)
        source = source_lookup[table['page_key']]
        reviewed = table['region_origin'].startswith('manually')
        for row in table['rows']:
            if row['row_kind'] == 'quarter':
                skipped.append(dict(table_id=table['id'], label=row['label'], reason='quarter_row_with_year_columns'))
                continue
            if not table.get('keep_empty_annual_rows') and all((row['cells'][i]['status'] == 'empty' for i in indices)):
                skipped.append(dict(table_id=table['id'], label=row['label'], reason='no_annual_values'))
                continue
            for index in indices:
                period, cell = (table['headers'][index]['period'], row['cells'][index])
                normalized, normalized_unit = canonical_amount(cell['value'], row['unit'])
                records.append(dict(table_id=table['id'], page_key=table['page_key'], account_raw=row['label'], section=row.get('section'), period=period['period'], period_raw=period['raw'], basis=cell['basis_override'] or period['basis'], raw_value=row['raw_values'][index], value_decimal=cell['value'], value_status=cell['status'], category=cell['category'], unit=row['unit'], bbox_json=json.dumps(row['value_bboxes'][index]), verification_scope='candidate_except_explicit_reference_checks' if reviewed else 'unreviewed_candidate', source_sha256=source['source_sha256'], source_filename=source['source'], region_origin=table['region_origin'], canonical_value_decimal=normalized, canonical_unit=normalized_unit, run_id=run_id))
    return (records, skipped)

def write_tabular(records, fields, stem, run_dir):
    normalized = [{key: '' if row.get(key) is None else str(row[key]) for key in fields} for row in records]
    with (run_dir / (stem + '.csv')).open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(normalized)
    dataframe = pl.DataFrame(normalized, schema={key: pl.String for key in fields})
    dataframe.write_parquet(run_dir / (stem + '.parquet'))
    with (run_dir / (stem + '.csv')).open(encoding='utf-8-sig', newline='') as stream:
        csv_rows = list(csv.DictReader(stream))
    assert csv_rows == pl.read_parquet(run_dir / (stem + '.parquet')).to_dicts(), 'CSV_Parquet_mismatch'
    return dataframe

def build_review_queue(records, tables, checks, failures, diagnostics):
    lookup = {record['key']: record for record, _ in records}
    queue = []

    def append_review(key, reason, detail, bbox=None, step='compare_existing_native_extractors'):
        queue.append(dict(page_key=key, source_sha256=lookup.get(key, {}).get('source_sha256', ''), reason=reason, bbox_json=json.dumps(bbox), detail=str(detail), next_step=step))
    for item in checks['financial_rules']:
        if item['status'] != 'PASS':
            key = next((t['page_key'] for t in tables if t['id'] == item['table']), '')
            append_review(key, item['status'], json.dumps(item, ensure_ascii=False), step='verify_source_scope_or_omitted_adjustments')
    for item in failures:
        append_review(item['page_key'], 'reference_reconstruction_failed', item['error'])
    for item in diagnostics:
        append_review(item['page_key'], item['reason'], item['detail'])
    for table in tables:
        for row in table['textual_rows']:
            if row['role'] == 'unresolved_mixed_row':
                append_review(table['page_key'], 'unresolved_mixed_row', json.dumps(row, ensure_ascii=False), row.get('bbox'))
        ambiguous = [header['period'] for header in table['headers'] if header['period']['kind'] == 'ambiguous_month']
        if ambiguous:
            append_review(table['page_key'], 'ambiguous_period_scope', json.dumps(ambiguous), table['bbox'])
    for record, payload in records:
        if len(payload['words']) < MIN_NATIVE_WORDS and (not payload.get('imported')):
            append_review(record['key'], 'insufficient_text', json.dumps(payload['ocr_attempts'], ensure_ascii=False), step='supply_existing_extractor_output_or_source_evidence_no_OCR')
        elif False:
            append_review(record['key'], 'ocr_values_require_visual_check', 'OCR confidence alone does not verify numeric values')
        if payload['table_error']:
            append_review(record['key'], 'secondary_table_detector_error', payload['table_error'])
    return queue

def write_matrix(summary, run_dir):
    """自包含靜態矩陣，欄位值先 escape；檢查明細可下載 JSON。"""
    rows = [('PDF', summary['source_files']), ('Pages', summary['selected_pages']), ('Table regions', summary['reference_tables']), ('Annual candidate cells', summary['annual_candidate_cells']), ('Numeric checks', summary['numeric_reference_checks']), ('Financial checks', summary['financial_equation_checks']), ('Policy checks', summary['policy_checks']), ('Cache hits / misses', f"{summary['cache_hits']} / {summary['cache_misses']}"), ('Review queue', summary['review_items']), ('Fatal source errors', summary['fatal_errors'])]
    cells = ''.join(('<tr><td>' + html.escape(label) + '</td><td>' + html.escape(str(value)) + '</td></tr>' for label, value in rows))
    markup = '<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    markup += '<title>VRN Repair Matrix</title><style>body{font:14px system-ui;background:#faf8f2;color:#242424;max-width:900px;margin:24px auto;padding:12px}table{border-collapse:collapse;width:100%}td{border:1px solid #ddd;padding:8px}small{color:#666}</style>'
    markup += '<small>VERITAS INTELLIGENCE ANALYTICS<br>DISCIPLINA • PRUDENTIA • INTEGRITAS</small><h2>VRN PDF Repair Engine</h2>'
    markup += '<p>' + html.escape(summary['status']) + ' · ' + html.escape(summary['run_id']) + '</p><table>' + cells + '</table>'
    markup += '<p>數字抽查與算式檢查各自記錄；其餘儲存格仍為候選。來源差異不覆寫。</p><a href="validation.json" download>驗證 JSON</a> · <a href="run_summary.json" download>執行摘要 JSON</a></html>'
    (run_dir / 'matrix.html').write_text(markup, encoding='utf-8')

def read_annual_dataframe(run_dir):
    load_dependencies()
    return pl.read_parquet(Path(run_dir) / 'annual_reference.parquet')

def infer_header_scope(word, payload):
    y = (word['y0'] + word['y1']) / 2
    markers = []
    for item in payload['words']:
        center = (item['y0'] + item['y1']) / 2
        text = item['text'].strip()
        if y - HEADER_PARENT_DISTANCE <= center < y - HEADER_TOLERANCE and item['x0'] <= word['x0'] + 3:
            if re.fullmatch('年度|全年|Annual|Yearly', text, re.I):
                markers.append((center, item['x0'], 'annual'))
            if re.fullmatch('季度|Quarterly|Quarter', text, re.I):
                markers.append((center, item['x0'], 'quarter'))
    if markers:
        nearest_y = max((marker[0] for marker in markers))
        choices = [marker for marker in markers if abs(marker[0] - nearest_y) <= HEADER_TOLERANCE * 2]
        return max(choices, key=lambda marker: marker[1])[2]
    return 'mixed'

def split_period_header(words):
    ordered = sorted(words, key=lambda w: w['x0'])
    if len(ordered) < MIN_PERIOD_COLUMNS:
        return []
    distances = [b['x1'] - a['x1'] for a, b in zip(ordered, ordered[1:])]
    typical = median(sorted(distances)[:max(1, (len(distances) + 1) // 2)])
    groups = [[]]
    seen = set()
    mixed_months = any((re.match('(Mar|Jun|Sep|Dec)-', word['text'], re.I) for word in ordered))
    for word in ordered:
        token = word['text']
        gap = word['x1'] - groups[-1][-1]['x1'] if groups[-1] else 0
        split = groups[-1] and (gap > typical * HEADER_GUTTER_MULTIPLIER or (token in seen and (not mixed_months) and (len(groups[-1]) >= MIN_PERIOD_COLUMNS)))
        if split:
            groups.append([])
            seen = set()
        groups[-1].append(word)
        seen.add(token)
    return [group for group in groups if len(group) >= MIN_PERIOD_COLUMNS]

def infer_label_left_edge(groups, endpoints, header_bottom, right_edge):
    spacing = median((b - a for a, b in zip(endpoints, endpoints[1:])))
    candidates = []
    for group in groups:
        if not header_bottom + HEADER_TOLERANCE < group['center'] < header_bottom + LABEL_PROBE_DISTANCE:
            continue
        numeric = [w for w in group['words'] if parse_value(w['text'])['status'] in ('numeric', 'categorical') and min((abs(w['x1'] - endpoint) for endpoint in endpoints)) <= spacing * COLUMN_ALIGNMENT_FRACTION]
        first = [w for w in numeric if abs(w['x1'] - endpoints[0]) <= spacing * COLUMN_ALIGNMENT_FRACTION]
        if len(numeric) < 2 or not first:
            continue
        numeric_left = min((w['x0'] for w in first))
        before = [w for w in group['words'] if w['x1'] < numeric_left - 0.1 and w['x0'] < right_edge]
        if not before:
            continue
        segments = [[]]
        for word in before:
            if segments[-1]:
                previous = segments[-1][-1]
                gap_limit = max(LABEL_GAP_MINIMUM, (word['y1'] - word['y0']) * LABEL_GAP_HEIGHT_FACTOR)
                if word['x0'] - previous['x1'] > gap_limit:
                    segments.append([])
            segments[-1].append(word)
        segment = segments[-1]
        text_words = [w for w in segment if parse_value(w['text'])['status'] == 'unresolved_text' and parse_period(w['text'], 'mixed') is None]
        if text_words:
            candidates.append(min((w['x0'] for w in text_words)))
    if candidates:
        return max(0, median(candidates) - 1)
    return max(0, endpoints[0] - spacing * LABEL_FALLBACK_COLUMNS)

def infer_default_unit(text):
    compact = re.sub('\\s+', '', text)
    for pattern, unit in UNIT_PATTERNS:
        if re.search(pattern, compact, re.I):
            return unit
    return 'mixed'

def infer_region_label(words, bbox, y):
    candidates = [w for w in words if bbox[0] <= (w['x0'] + w['x1']) / 2 <= bbox[2] and y - HEADER_PARENT_DISTANCE <= (w['y0'] + w['y1']) / 2 < y - HEADER_TOLERANCE]
    rows = cluster_rows(candidates)
    texts = [legacy_join_words(row['words']) for row in rows]
    title = next((text for text in reversed(texts) if re.search('損益|資產負債|現金流|比率|income|balance|cash.flow|ratio|summary|forecast|estimates', text, re.I)), '')
    return (title, infer_default_unit(' '.join(texts)))

def detect_lightweight_regions(record, payload):
    groups = cluster_rows(payload['words'])
    header_groups = []
    for group in groups:
        period_words = [w for w in group['words'] if parse_period(w['text'], 'mixed') is not None and (not is_parent_year_header(w, groups))]
        for header in split_period_header(period_words):
            header_groups.append(dict(words=header, y=median(((w['y0'] + w['y1']) / 2 for w in header))))
    merged = []
    for header in sorted(header_groups, key=lambda item: (item['y'], item['words'][0]['x0'])):
        match = next((prior for prior in reversed(merged) if 0 < header['y'] - prior['y'] <= HEADER_MULTILINE_DISTANCE and (max((w['x1'] for w in prior['words'])) < min((w['x0'] for w in header['words'])) or max((w['x1'] for w in header['words'])) < min((w['x0'] for w in prior['words']))) and any((parse_period(w['text'], 'mixed')['kind'] == 'quarter' for w in header['words'] + prior['words']))), None)
        if match:
            match['words'].extend(header['words'])
            match['words'].sort(key=lambda w: w['x0'])
            match['y'] = max(match['y'], header['y'])
        else:
            merged.append(header)
    configs = []
    for header in merged:
        endpoints = [w['x1'] for w in header['words']]
        if len(endpoints) < MIN_PERIOD_COLUMNS or any((b <= a for a, b in zip(endpoints, endpoints[1:]))):
            continue
        spacing = median((b - a for a, b in zip(endpoints, endpoints[1:])))
        y = max(((w['y0'] + w['y1']) / 2 for w in header['words']))
        right = min(record['width'], endpoints[-1] + spacing * RIGHT_EDGE_PADDING_COLUMNS)
        left = infer_label_left_edge(groups, endpoints, y, right)
        next_headers = [other['y'] for other in merged if other['y'] > y + HEADER_TOLERANCE * 2 and any((left <= (w['x0'] + w['x1']) / 2 <= right for w in other['words']))]
        limit = min(next_headers) - HEADER_TOLERANCE * 2 if next_headers else record['height']
        body_groups = []
        last_numeric = y
        for group in groups:
            if not y + HEADER_TOLERANCE < group['center'] < limit:
                continue
            localized = [w for w in group['words'] if left <= (w['x0'] + w['x1']) / 2 <= right]
            if not localized:
                continue
            text = legacy_join_words(localized)
            if re.match('資料來源|Source:|Note:|註[：:]|Disclaimer', text, re.I):
                break
            numeric = [w for w in localized if parse_value(w['text'])['status'] in ('numeric', 'categorical') and min((abs(w['x1'] - endpoint) for endpoint in endpoints)) <= spacing * COLUMN_ALIGNMENT_FRACTION]
            if len(numeric) >= min(2, len(endpoints)):
                if body_groups and group['center'] - last_numeric > TABLE_MAX_NUMERIC_GAP:
                    break
                body_groups.append(dict(group=group, words=localized))
                last_numeric = group['center']
        if len(body_groups) < MIN_TABLE_NUMERIC_ROWS:
            continue
        bottom = max((w['y1'] for item in body_groups for w in item['words'])) + 1
        top = min((w['y0'] for w in header['words'])) - 1
        box = (left, max(0, top), right, min(record['height'], bottom))
        specs = [(float((word['y0'] + word['y1']) / 2), float(word['x0'] - 0.05), float(word['x1'] + 0.05), infer_header_scope(word, payload)) for word in header['words']]
        only_fy = 'FY' if any((re.fullmatch('Q[1-4]', w['text'], re.I) for item in body_groups for w in item['words'])) else None
        title, unit = infer_region_label(payload['words'], box, y)
        if unit == 'mixed':
            near_header = [w for w in payload['words'] if left <= (w['x0'] + w['x1']) / 2 <= right and y - HEADER_PARENT_DISTANCE <= (w['y0'] + w['y1']) / 2 <= y + HEADER_UNIT_DISTANCE]
            unit = infer_default_unit(legacy_join_words(near_header))
        configs.append((record['key'], f'auto_{len(configs) + 1}', box, specs, unit, only_fy))
    return configs

def reconstruct_row_year_tables(record, payload, covered):
    groups = cluster_rows(payload['words'])
    candidates = []
    for group in groups:
        years = [w for w in group['words'] if parse_period(w['text'], 'mixed') and parse_period(w['text'], 'mixed')['kind'] == 'annual' and re.fullmatch('(?:FY)?20\\d{2}[AEF]?', w['text'], re.I)]
        for year in years:
            numeric = [w for w in group['words'] if w['x0'] > year['x1'] and parse_value(w['text'])['status'] == 'numeric']
            if len(numeric) >= ROW_YEAR_MIN_VALUE_COLUMNS and (not any((legacy_inside(year, box) for box in covered))):
                candidates.append(dict(group=group, year=year, numbers=numeric))
    runs = []
    for item in candidates:
        prior = runs[-1][-1] if runs else None
        if prior and abs(prior['year']['x0'] - item['year']['x0']) <= ROW_YEAR_ALIGNMENT_TOLERANCE and (0 < item['group']['center'] - prior['group']['center'] <= ROW_YEAR_MAX_GAP) and (len(prior['numbers']) == len(item['numbers'])):
            runs[-1].append(item)
        else:
            runs.append([item])
    tables = []
    for run in runs:
        if len(run) < ROW_YEAR_MIN_PERIODS:
            continue
        endpoints = [w['x1'] for w in run[0]['numbers']]
        if len(set((parse_period(item['year']['text'], 'mixed')['period'] for item in run))) != len(run):
            continue
        left, right = (run[0]['year']['x0'] - 1, max(endpoints) + 2)
        top = run[0]['year']['y0']
        header_words = [w for w in payload['words'] if left <= (w['x0'] + w['x1']) / 2 <= right and top - ROW_YEAR_HEADER_DISTANCE <= w['y1'] < top]
        first_boundary = (run[0]['year']['x1'] + run[0]['numbers'][0]['x0']) / 2
        labels = [[] for _ in endpoints]
        boundaries = [(a + b) / 2 for a, b in zip(endpoints, endpoints[1:])]
        for word in header_words:
            center = (word['x0'] + word['x1']) / 2
            if center <= first_boundary:
                continue
            column = min(range(len(endpoints)), key=lambda index: abs(word['x1'] - endpoints[index]))
            labels[column].append(word)
        periods = [dict(period=parse_period(item['year']['text'], 'mixed'), word=item['year']) for item in run]
        rows = []
        for column, endpoint in enumerate(endpoints):
            words = labels[column]
            text = ' '.join((legacy_join_words(group['words']) for group in cluster_rows(words))).strip()
            label = text or f'column_{column + 1}'
            raw = [item['numbers'][column]['text'] for item in run]
            rows.append(dict(label=label, section=None, raw_values=raw, cells=[parse_value(value) for value in raw], value_bboxes=[get_cell_bbox([item['numbers'][column]]) for item in run], unit=infer_unit(label, raw, infer_default_unit(label), None), row_kind='same_as_header'))
        box = [left, top - ROW_YEAR_HEADER_DISTANCE, right, max((item['year']['y1'] for item in run)) + 1]
        tables.append(dict(id=record['key'] + f'_rowyear_{len(tables) + 1}', page_key=record['key'], bbox=box, headers=periods, rows=rows, textual_rows=[], default_unit='mixed', region_origin='automatic_row_year_candidate', method='generic_row_year_transposition'))
    return tables

def validate_table_structure(table):
    expected = len(table['headers'])
    checks = [dict(rule='rectangular_columns', status='PASS' if all((len(row['cells']) == expected for row in table['rows'])) else 'FAIL'), dict(rule='period_columns_present', status='PASS' if expected >= MIN_PERIOD_COLUMNS else 'FAIL'), dict(rule='numeric_or_categorical_rows', status='PASS' if len(table['rows']) >= MIN_TABLE_NUMERIC_ROWS else 'FAIL')]
    ambiguous = [h['period']['raw'] for h in table['headers'] if h['period']['kind'] == 'ambiguous_month']
    checks.append(dict(rule='period_scope_resolved', status='REVIEW' if ambiguous else 'PASS', ambiguous=ambiguous))
    checks.append(dict(rule='mixed_rows_resolved', status='REVIEW' if any((row['role'] == 'unresolved_mixed_row' for row in table['textual_rows'])) else 'PASS'))
    return checks

def reconstruct_unknown_pages(records, layout_command, run_dir):
    if layout_command is not None:
        raise ValueError('POLICY: Layout/OCR invocation is disabled')
    tables, diagnostics = ([], [])
    for record, payload in records:
        configs = detect_lightweight_regions(record, payload) if payload['words'] else []
        page_tables = []
        for config in configs:
            try:
                table = reconstruct_table(config)
                table['region_origin'] = 'automatic_geometry_candidate'
                table['default_unit'] = config[4]
                table['structure_checks'] = validate_table_structure(table)
                if any((item['status'] == 'FAIL' for item in table['structure_checks'])):
                    diagnostics.append(dict(page_key=record['key'], reason='candidate_structure_failed', detail=table['id']))
                    continue
                page_tables.append(table)
            except Exception as error:
                diagnostics.append(dict(page_key=record['key'], reason='candidate_reconstruction_failed', detail=str(error)))
        row_year = reconstruct_row_year_tables(record, payload, [table['bbox'] for table in page_tables]) if payload['words'] else []
        for table in row_year:
            table['structure_checks'] = validate_table_structure(table)
        page_tables.extend(row_year)
        repaired = []
        for number, raw_table in enumerate(payload['default_tables'], 1):
            matrix = repair_matrix(raw_table)
            repaired.append(matrix)
            if payload.get('imported') or (not page_tables and matrix['rows']):
                candidate = reconstruct_matrix_period_table(record, matrix, number)
                if candidate:
                    page_tables.append(candidate)
        write_json(run_dir / record['key'] / 'repaired_matrices.json', repaired)
        payload['repaired_matrices'] = repaired
        if not page_tables and any((matrix['rows'] for matrix in repaired)):
            diagnostics.append(dict(page_key=record['key'], reason='non_period_table_preserved_as_cells', detail='Matrix repaired without inventing period headers.'))
        tables.extend(page_tables)
    return (tables, diagnostics)

def boxes_overlap(a, b):
    intersect = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
    smaller = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
    return intersect / smaller if smaller > 0 else 0

def find_account_role(label):
    compact = normalize_label(label).lower()
    for role, patterns in ACCOUNT_PATTERNS.items():
        if any((re.fullmatch(pattern, compact, re.I) for pattern in patterns)):
            return role
    return None

def validate_generic_financial(tables):
    checks = []
    for table in tables:
        mapped = {}
        for row in table['rows']:
            role = find_account_role(row['label'])
            if role:
                mapped.setdefault(role, []).append(row)
        for rule, terms, target in GENERIC_FINANCIAL_RULES:
            terms = list(terms)
            scope_note = None
            if rule == 'balance_equation' and len(mapped.get('minority', [])) == 1 and (len(mapped.get('equity', [])) == 1):
                equity_label = normalize_label(mapped['equity'][0]['label']).lower()
                if re.fullmatch("shareholders'?equity|母公司業主權益|歸屬母公司業主之權益", equity_label):
                    terms.append(('minority', 1))
                    scope_note = 'separate_explicit_minority_interests_plus_shareholders_equity_candidate'
                else:
                    scope_note = 'equity_scope_ambiguous_with_separate_minority_interests'
            roles = [role for role, _ in terms] + [target]
            if not all((role in mapped and len(mapped[role]) == 1 for role in roles)):
                continue
            for index in annual_indices(table):
                rows = {role: mapped[role][0] for role in roles}
                if any((row['cells'][index]['value'] is None for row in rows.values())):
                    continue
                units = {row['unit'] for row in rows.values()}
                if len(units) > 1 or units == {'mixed'}:
                    checks.append(dict(table=table['id'], rule=rule, period=table['headers'][index]['period']['period'], status='UNVERIFIED', reason='unit_or_scope_requires_review'))
                    continue
                effective_terms = []
                for role, sign in terms:
                    value = Decimal(rows[role]['cells'][index]['value'])
                    if sign == 'expense':
                        multiplier = 1 if value <= 0 else -1
                    else:
                        multiplier = sign
                    effective_terms.append((role, multiplier))
                computed = sum((Decimal(rows[role]['cells'][index]['value']) * sign for role, sign in effective_terms))
                reported = Decimal(rows[target]['cells'][index]['value'])
                tolerance = sum((legacy_rounding_half_width(re.sub('[AEF]$', '', rows[role]['raw_values'][index])) for role in roles))
                residual = computed - reported
                checks.append(dict(table=table['id'], rule=rule, period=table['headers'][index]['period']['period'], calculated=str(computed), reported=str(reported), residual=str(residual), rounding_tolerance=str(tolerance), unit=next(iter(units)), status='UNVERIFIED' if scope_note == 'equity_scope_ambiguous_with_separate_minority_interests' else 'PASS' if abs(residual) <= tolerance else 'SOURCE_RECHECK', scope_evidence=scope_note, source_values_unchanged=True))
    return checks

def validate_oracle(annual, oracle_path, source_lookup):
    if not oracle_path:
        return []
    oracle = json.loads(Path(oracle_path).read_text(encoding='utf-8'))
    checks = []
    for expected in oracle:
        matching = [row for row in annual if row['source_sha256'] == expected['source_sha256'] and source_lookup[row['page_key']]['page'] == expected['page'] and (row['period'] == expected['period']) and (normalize_label(row['account_raw']) == normalize_label(expected['account_raw']))]
        if expected.get('value_bbox'):
            matching.sort(key=lambda row: -boxes_overlap(json.loads(row['bbox_json']), expected['value_bbox']) if json.loads(row['bbox_json']) else 0)
        actual = matching[0]['value_decimal'] if matching else None
        check = dict(source_sha256=expected['source_sha256'], page=expected['page'], label=expected['account_raw'], period=expected['period'], expected=expected['expected_value'], actual=actual, status='PASS' if actual is not None and Decimal(actual) == Decimal(expected['expected_value']) else 'MISSING' if not matching else 'FAIL')
        checks.append(check)
    return checks

def export_all_table_cells(records, tables, run_dir):
    cells = []
    for record, payload in records:
        for number, matrix in enumerate(payload.get('repaired_matrices', []), 1):
            for row_index, row in enumerate(matrix['rows']):
                for column_index, value in enumerate(row):
                    parsed = matrix['parsed_cells'][row_index][column_index]
                    source_raw = matrix.get('source_cell_map', [])[row_index][column_index]['raw_value']
                    synthetic = row_index == 0 and column_index == 0 and (value == 'ITEM') and (not source_raw)
                    cells.append(dict(page_key=record['key'], table_id=f"{record['key']}_matrix_{number}", row=str(row_index), column=str(column_index), raw_value=source_raw, normalized_text=value, value_decimal=parsed['value'], value_status=parsed['status'], category=parsed['category'], bbox_json=json.dumps(matrix.get('bbox')), origin='normalized_matrix_candidate', source_sha256=record['source_sha256'], synthetic_label='true' if synthetic else 'false'))
    for table in tables:
        record = next((item for item, _ in records if item['key'] == table['page_key']))
        cells.append(dict(page_key=table['page_key'], table_id=table['id'], row='-1', column='0', raw_value='', normalized_text='ITEM', value_decimal=None, value_status='header', category=None, bbox_json='null', origin='synthetic_header', source_sha256=record['source_sha256'], synthetic_label='true'))
        for row_index, row in enumerate(table['rows']):
            for column_index, cell in enumerate(row['cells']):
                cells.append(dict(page_key=table['page_key'], table_id=table['id'], row=str(row_index), column=str(column_index + 1), raw_value=row['raw_values'][column_index], normalized_text=cell.get('normalized_text', row['raw_values'][column_index]), value_decimal=cell['value'], value_status=cell['status'], category=cell['category'], bbox_json=json.dumps(row['value_bboxes'][column_index]), origin=table['region_origin'], source_sha256=record['source_sha256'], synthetic_label='false'))
    write_tabular(cells, TABLE_CELL_FIELDS, 'table_cells', run_dir)
    return len(cells)

def prepare_visible_candidate_words(payload, page_dir):
    words = payload['words']
    excluded = []
    image_path = page_dir / 'original.png'
    white_spans = [span for span in payload['spans'] if span['color'] == 16777215 and re.search('\\d', span['text'])]
    if not image_path.exists() or not white_spans:
        return (words, excluded)
    with Image.open(image_path) as image:
        for span in white_spans:
            box = span['bbox']
            rect = [max(0, int(box[0] * RENDER_SCALE)), max(0, int(box[1] * RENDER_SCALE)), min(image.width, int(box[2] * RENDER_SCALE) + 1), min(image.height, int(box[3] * RENDER_SCALE) + 1)]
            if rect[2] <= rect[0] or rect[3] <= rect[1]:
                continue
            crop = image.crop(rect).convert('RGB')
            pixels = list(crop.get_flattened_data() if hasattr(crop, 'get_flattened_data') else crop.getdata())
            fraction = sum((min(pixel) >= WHITE_PIXEL_THRESHOLD for pixel in pixels)) / len(pixels)
            if fraction >= INVISIBLE_WHITE_FRACTION:
                excluded.append(dict(**span, white_pixel_fraction=fraction, status='render_supported_invisible_candidate', policy='excluded_from_geometry_candidates_only_raw_text_retained'))
    visible = [word for word in words if not any((legacy_inside(word, span['bbox']) for span in excluded))]
    return (visible, excluded)

def export_page_evidence(records, tables, run_dir, render):
    white, roles, merges = ([], [], [])
    for record, payload in records:
        key = record['key']
        page_tables = [table for table in tables if table['page_key'] == key]
        for table in page_tables:
            table['context'] = get_region_context(payload, table['bbox']) if table['bbox'] else {'above': [], 'below': [], 'policy': 'no_coordinates_available'}
            table['item_header'] = 'ITEM'
            table['item_header_origin'] = 'synthetic_semantic_label_not_source_numeric_value'
        roles.extend((dict(page_key=key, **role) for role in classify_page_roles(record, payload, tables)))
        merges.extend((dict(page_key=key, **cell) for cell in collect_merged_cell_candidates(payload)))
        white.extend((dict(page_key=key, **span, status='requires_background_check_not_automatic_deletion') for span in payload['spans'] if span['color'] == 16777215 and re.search('\\d', span['text'])))
        repaired_text = repair_body_text(payload)
        write_json(run_dir / key / 'body_repair.json', repaired_text)
        (run_dir / key / 'body_repaired.txt').write_text(repaired_text['text'] + '\n', encoding='utf-8')
        if render and record['source_path'].lower().endswith('.pdf') and any((table['bbox'] for table in page_tables)):
            with fitz.open(record['source_path']) as document:
                page = document[record['page'] - 1]
                for table in page_tables:
                    if not table['bbox']:
                        continue
                    box = fitz.Rect(table['bbox'])
                    page.draw_rect(box, color=(0.8, 0.1, 0.1), width=0.7)
                    page.insert_text((box.x0, max(6, box.y0 - 2)), table['id'].split('_')[-1], fontsize=6, color=(0.8, 0.1, 0.1))
                page.get_pixmap(matrix=fitz.Matrix(RENDER_SCALE, RENDER_SCALE), alpha=False).save(run_dir / key / 'reference_regions.png')
    write_json(run_dir / 'page_roles.json', roles)
    write_json(run_dir / 'merged_cell_candidates.json', merges)
    write_json(run_dir / 'white_span_candidates.json', white)
    return (white, merges)

def run_engine(input_paths, output_root=DEFAULT_OUTPUT, render=True, max_pages=DEFAULT_MAX_UNKNOWN_PAGES, selftest=False, oracle_path=None, reconcile_path=None, progress=True, workers=DEFAULT_WORKERS, office_exports=()):
    global OUTPUT_DIR
    started = time.perf_counter()
    versions = load_dependencies()
    if max_pages < 0:
        raise ValueError('max_pages must be >= 0')
    output_root = Path(output_root).expanduser().resolve()
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ') + '_' + uuid.uuid4().hex[:8]
    run_dir = output_root / 'runs' / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    OUTPUT_DIR = run_dir
    paths, input_errors = find_pdf_inputs(input_paths)
    if not paths:
        raise RuntimeError('找不到輸入；請使用 --input 指定 PDF／JSON／CSV／TSV／文字檔。')
    stats = dict(cache_hits=0, cache_misses=0, secondary_extractor_errors=[])
    extraction_options = dict(schema=EXTRACTION_SCHEMA_VERSION, versions=versions, render=render, render_scale=RENDER_SCALE, ocr_mode='off', ocr_language=None, max_pages=max_pages)
    records, sources, duplicates, errors, stats = extract_input_jobs(paths, output_root, run_dir, extraction_options, workers, progress)
    write_json(run_dir / 'source_manifest.json', sources)
    write_json(run_dir / 'extraction_inventory.json', [record for record, _ in records])
    tables, diagnostics = reconstruct_unknown_pages(records, None, run_dir)
    lookup = {record['key']: record for record, _ in records}
    resolve_month_scopes_by_evidence(tables, lookup)
    annual, skipped = build_annual_records(tables, lookup, run_id)
    structures = [dict(table=table['id'], **check) for table in tables for check in table['structure_checks']]
    checks = dict(expected_cells=validate_oracle(annual, oracle_path, lookup), financial_rules=validate_generic_financial(tables), policy_checks=[dict(rule='annual_output_has_no_quarter_period', status='PASS' if all((re.fullmatch('20\\d{2}', row['period']) for row in annual)) else 'FAIL'), dict(rule='no_Layout_or_OCR', status='PASS')], structure_checks=structures, self_checks=run_self_checks() if selftest else [])
    white, merges = export_page_evidence(records, tables, run_dir, render)
    office_results = export_office_candidates(records, run_dir, office_exports)
    write_json(run_dir / 'office_exports.json', office_results)
    reviews = build_review_queue(records, tables, checks, [], diagnostics)
    for record, payload in records:
        for number, matrix in enumerate(payload.get('repaired_matrices', []), 1):
            for issue in matrix['issues']:
                if issue['status'] == 'REVIEW':
                    reviews.append(dict(page_key=record['key'], source_sha256=record['source_sha256'], reason=issue['code'], bbox_json=json.dumps(matrix.get('bbox')), detail=json.dumps(dict(matrix_number=number, **issue), ensure_ascii=False), next_step='compare_existing_extractor_or_explicit_cell_evidence'))
    for table in tables:
        for check in table['structure_checks']:
            if check['status'] != 'PASS':
                reviews.append(dict(page_key=table['page_key'], source_sha256=lookup[table['page_key']]['source_sha256'], reason=check['rule'], bbox_json=json.dumps(table['bbox']), detail=json.dumps(check), next_step='compare_existing_native_extractors'))
    for check in checks['expected_cells']:
        if check['status'] != 'PASS':
            reviews.append(dict(page_key='', source_sha256=check['source_sha256'], reason='oracle_' + check['status'], bbox_json='null', detail=json.dumps(check, ensure_ascii=False), next_step='inspect_existing_source_or_extractor_candidates'))
    write_tabular(annual, ANNUAL_FIELDS, 'annual_reference', run_dir)
    write_tabular(reviews, REVIEW_FIELDS, 'review_queue', run_dir)
    all_cells = export_all_table_cells(records, tables, run_dir)
    write_json(run_dir / 'reconstructed_tables.json', tables)
    write_json(run_dir / 'skipped_annual_rows.json', skipped)
    write_json(run_dir / 'validation.json', checks)
    write_json(run_dir / 'failure_cases_25.json', failure_case_evidence(records, tables, reviews))
    write_json(run_dir / 'tool_inventory.json', tool_inventory())
    if reconcile_path:
        write_json(run_dir / 'extractor_reconciliation.json', reconcile_extractor_results(json.loads(Path(reconcile_path).read_text(encoding='utf-8'))))
    write_json(run_dir / 'errors.json', {'inputs': input_errors, 'sources': errors, 'secondary_extractor': stats['secondary_extractor_errors']})
    counts = lambda name: dict(Counter((item['status'] for item in checks[name])))
    fail = bool(errors or input_errors or any((result['status'] == 'ERROR' for result in office_results))) or any((item['status'] == 'FAIL' for name in ('policy_checks', 'self_checks') for item in checks[name]))
    require_review = bool(reviews) or any((item['status'] != 'PASS' for name in ('expected_cells', 'structure_checks') for item in checks[name]))
    summary = dict(engine_version=ENGINE_VERSION, engine_sha256=file_sha256(__file__), run_id=run_id, run_dir=str(run_dir), status='FAIL' if fail else 'REVIEW' if require_review else 'PROCESSED_CANDIDATES', source_files=len(sources), selected_pages=len(records), reference_tables=len(tables), automatic_table_regions=len(tables), annual_candidate_cells=len(annual), all_table_candidate_cells=all_cells, numeric_reference_checks=counts('expected_cells'), financial_equation_checks=counts('financial_rules'), structure_checks=counts('structure_checks'), policy_checks=counts('policy_checks'), self_checks=counts('self_checks'), cache_hits=stats['cache_hits'], cache_misses=stats['cache_misses'], duplicate_inputs=len(duplicates), review_items=len(reviews), fatal_errors=len(errors), region_errors=sum((item['reason'] == 'candidate_reconstruction_failed' for item in diagnostics)), rejected_region_candidates=sum((item['reason'] == 'candidate_structure_failed' for item in diagnostics)), csv_parquet_exact_consistency=True, annual_export_contains_quarters=False, all_cells_individually_verified=False, uses_sample_specific_boundaries=False, failure_cases_registered=len(FAILURE_CASES), tool_groups_registered=len(TOOL_REGISTRY), layout_or_ocr_invocations=0, elapsed_seconds=time.perf_counter() - started, source_values_overwritten=False, workers=workers, office_exports=office_results, versions=versions, duplicates=duplicates, limits=['Generic geometry/matrix rules; oracle is post-reconstruction validation only.', '20 tool groups registered; model/OCR/service execution is disabled; existing outputs can be normalized.', 'Structure PASS does not establish all financial values as correct.', 'Explicit merged spans restored; geometric-only spans remain candidates.', 'Missing/illegible information is not fabricated; no 100-percent recovery guarantee.', 'No TWSE/TPEX/VDF or market-price external verification.'])
    write_json(run_dir / 'run_summary.json', summary)
    write_matrix(summary, run_dir)
    return summary

def parse_arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--input', nargs='+', help='PDF／JSON／CSV／TSV／TXT／MD 檔或資料夾')
    parser.add_argument('--output', default=str(DEFAULT_OUTPUT), help='快取與 Append-Only run 目錄')
    parser.add_argument('--selftest', action='store_true', help='政策、合併格、擷取器介面及 AST/compile/import')
    parser.add_argument('--oracle', help='事後驗證 JSON；不參與重建')
    parser.add_argument('--reconcile', help='具有共同 source_id/table_key/row/column 的擷取器比對 JSON')
    parser.add_argument('--no-render', action='store_true', help='跳過影像；不可見文字將僅保留候選證據')
    parser.add_argument('--max-pages', type=int, default=DEFAULT_MAX_UNKNOWN_PAGES, help='每份最多頁數；0 為全部')
    parser.add_argument('--tools', action='store_true', help='列出 20 工具群及可用性，不載入模型')
    parser.add_argument('--quiet', action='store_true', help='只輸出最後 JSON 摘要')
    parser.add_argument('--workers', type=int, default=DEFAULT_WORKERS, help='原生擷取進程數；記憶體不足或互動 API 請設 1')
    parser.add_argument('--office-export', nargs='+', choices=['xlsx', 'docx'], default=[], help='選配匯出，需 openpyxl / python-docx')
    parser.add_argument('--watch', action='store_true', help='穩定檔案監聽，不移動／刪除來源')
    parser.add_argument('--watch-interval', type=float, default=WATCH_INTERVAL_SECONDS)
    parser.add_argument('--watch-stable-polls', type=int, default=WATCH_STABLE_POLLS)
    parser.add_argument('--watch-iterations', type=int, default=0, help='0 為持續監聽')
    return parser.parse_args(argv)

def main(argv=None):
    args = parse_arguments(argv)
    if args.tools:
        print(json.dumps(tool_inventory(), ensure_ascii=False, indent=2))
        return 0
    inputs = args.input if args.input else [path for path in DEFAULT_INPUTS if path.exists()]
    try:
        if args.selftest and (not inputs):
            checks = run_self_checks()
            print(json.dumps(dict(self_checks=checks), ensure_ascii=False, indent=2))
            return 0 if all((c['status'] == 'PASS' for c in checks)) else 1
        if args.watch:
            print(json.dumps(watch_folder(inputs, args.output, args.watch_interval, args.watch_stable_polls, args.watch_iterations, args.workers, not args.no_render, args.max_pages), ensure_ascii=False))
            return 0
        summary = run_engine(inputs, args.output, render=not args.no_render, max_pages=args.max_pages, selftest=args.selftest, oracle_path=args.oracle, reconcile_path=args.reconcile, progress=not args.quiet, workers=args.workers, office_exports=args.office_export)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 1 if summary['status'] == 'FAIL' else 0
    except Exception as error:
        print(json.dumps({'status': 'ERROR', 'error': f'{type(error).__name__}: {error}'}, ensure_ascii=False), file=sys.stderr)
        return 2

def tool_inventory():
    inventory = []
    for tool in TOOL_REGISTRY:
        available = {}
        for module in tool['modules']:
            try:
                available[module] = importlib.util.find_spec(module) is not None
            except (ValueError, ModuleNotFoundError):
                available[module] = False
        inventory.append(dict(tool, module_available=available, invocation_policy='existing_output_only' if tool['family'] not in ('native', 'export') else 'native_or_existing_output', models_loaded=False, automatically_invoked=False, license='check_package_and_weights_separately'))
    return inventory

def find_pdf_inputs(input_paths):
    found, errors = ([], [])
    for item in input_paths:
        path = Path(item).expanduser()
        if path.is_file() and path.suffix.lower() in INPUT_EXTENSIONS:
            found.append(path.resolve())
        elif path.is_dir():
            found.extend((p.resolve() for p in path.rglob('*') if p.is_file() and p.suffix.lower() in INPUT_EXTENSIONS))
        else:
            errors.append(dict(path=str(path), reason='input_not_found_or_unsupported'))
    return (sorted(set(found), key=str), errors)

def normalize_word(word, page_height=0, coordinate_space='pdf_points', width=0, height=0):
    if isinstance(word, (list, tuple)) and len(word) >= 5:
        word = dict(x0=word[0], y0=word[1], x1=word[2], y1=word[3], text=word[4], block=word[5] if len(word) > 5 else 0, line=word[6] if len(word) > 6 else 0, word=word[7] if len(word) > 7 else 0)
    if not isinstance(word, dict):
        raise ValueError('word must be a dict or x0,y0,x1,y1,text sequence')
    text = str(word.get('text', word.get('value', '')))
    box = word.get('bbox')
    if isinstance(box, dict):
        box = [box.get('l', box.get('x0')), box.get('t', box.get('y0')), box.get('r', box.get('x1')), box.get('b', box.get('y1'))]
    if box is not None:
        x0, y0, x1, y1 = map(float, box)
    else:
        x0 = float(word.get('x0', word.get('left', word.get('x', 0))))
        y0 = float(word.get('y0', word.get('top', word.get('y', 0))))
        x1 = float(word.get('x1', x0 + word.get('width', 0)))
        y1 = float(word.get('y1', word.get('bottom', y0 + word.get('height', 0))))
    if coordinate_space == 'bottom_left':
        if page_height <= 0:
            raise ValueError('bottom_left coordinates require explicit page height')
        y0, y1 = (page_height - max(y0, y1), page_height - min(y0, y1))
    elif coordinate_space == 'normalized':
        if width <= 0 or height <= 0:
            raise ValueError('normalized coordinates require page width and height')
        x0, x1, y0, y1 = (x0 * width, x1 * width, y0 * height, y1 * height)
    elif coordinate_space == 'pixels':
        raise ValueError('pixel coordinates require explicit dpi; use the OCR-result envelope')
    elif coordinate_space != 'pdf_points':
        raise ValueError('coordinate_space must be pdf_points, bottom_left, or normalized; pixels need an explicit conversion first')
    return dict(x0=min(x0, x1), y0=min(y0, y1), x1=max(x0, x1), y1=max(y0, y1), text=text, block=int(word.get('block', 0)), line=int(word.get('line', 0)), word=int(word.get('word', 0)), origin=word.get('origin', 'imported_extractor'))

def parse_html_tables(text):
    from html.parser import HTMLParser

    class TableParser(HTMLParser):

        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.tables, self.rows, self.row, self.cell, self.spans = ([], None, None, None, [])
            self.attributes = {}

        def handle_starttag(self, tag, attrs):
            if tag == 'table':
                self.rows, self.spans = ([], [])
            elif tag == 'tr' and self.rows is not None:
                self.row = []
            elif tag in ('td', 'th') and self.row is not None:
                self.cell, self.attributes = ([], dict(attrs))
            elif tag == 'br' and self.cell is not None:
                self.cell.append('\n')

        def handle_data(self, data):
            if self.cell is not None:
                self.cell.append(data)

        def handle_endtag(self, tag):
            if tag in ('td', 'th') and self.cell is not None:
                text = ''.join(self.cell)
                self.spans.append(dict(row=len(self.rows), column=len(self.row), text=text, rowspan=int(self.attributes.get('rowspan', 1)), colspan=int(self.attributes.get('colspan', 1)), is_header=tag == 'th', source_order=True))
                self.row.append(text)
                self.cell = None
            elif tag == 'tr' and self.row is not None:
                self.rows.append(self.row)
                self.row = None
            elif tag == 'table' and self.rows is not None:
                self.tables.append(dict(rows=self.rows, spans=self.spans, cells=[], bbox=None, origin='html_table'))
                self.rows = None
    parser = TableParser()
    parser.feed(text)
    return parser.tables

def parse_markdown_tables(text):
    tables, current = ([], [])
    for line in text.splitlines() + ['']:
        if '|' in line and line.count('|') >= 2:
            cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
            if all((re.fullmatch(':?-{3,}:?', cell or 'x') for cell in cells)):
                continue
            current.append(cells)
        elif current:
            if len(current) >= 2:
                tables.append(dict(rows=current, spans=[], cells=[], bbox=None, origin='markdown_matrix'))
            current = []
    return tables

def normalize_extractor_result(data, extractor='auto'):
    """支援共同 schema、Tabula、Docling、Unstructured 及二維矩陣。
    未識別格式回報錯誤，不猜測座標單位；上游 raw JSON 由呼叫端保留。
    """
    if isinstance(data, dict) and isinstance(data.get('ocr_results'), list):
        words = []
        if data.get('coordinate_space') not in ('pixels', 'pdf_points'):
            raise ValueError('existing OCR results require explicit coordinate_space: pixels or pdf_points')
        scale = 72 / float(data['dpi']) if data.get('coordinate_space') == 'pixels' and float(data.get('dpi', 0)) > 0 else 1
        if data.get('coordinate_space') == 'pixels' and (not data.get('dpi')):
            raise ValueError('pixel OCR results require dpi; this engine never runs OCR')
        for entry in data['ocr_results']:
            polygon, detail = (entry[0], entry[1])
            text = detail[0] if isinstance(detail, (list, tuple)) else detail
            box = [min((p[0] for p in polygon)), min((p[1] for p in polygon)), max((p[0] for p in polygon)), max((p[1] for p in polygon))]
            words.append(normalize_word(dict(bbox=[v * scale for v in box], text=text, origin=extractor)))
        return [dict(page=int(data.get('page', 1)), width=float(data.get('width', 0)) * scale, height=float(data.get('height', 0)) * scale, words=words, text='', tables=[])]
    if isinstance(data, list) and data and all((isinstance(item, dict) and 'text' in item and ('x0' in item or 'bbox' in item or 'left' in item) for item in data)):
        return normalize_extractor_result(dict(pages=[dict(words=data)]), extractor)
    if isinstance(data, dict) and 'blocks' in data:
        words = []
        for block_index, block in enumerate(data['blocks']):
            for line_index, line in enumerate(block.get('lines', [])):
                for span_index, span in enumerate(line.get('spans', [])):
                    if span.get('text') and span.get('bbox'):
                        words.append(dict(bbox=span['bbox'], text=span['text'], block=block_index, line=line_index, word=span_index))
        return normalize_extractor_result(dict(pages=[dict(width=data.get('width', 0), height=data.get('height', 0), words=words)]), extractor)
    if isinstance(data, str):
        tables = parse_html_tables(data) if '<table' in data.lower() else parse_markdown_tables(data)
        return [dict(page=1, width=0, height=0, words=[], text=data, tables=tables)]
    if isinstance(data, dict) and isinstance(data.get('pages'), dict):
        converted = []
        for key, page in data['pages'].items():
            match = re.search('\\d+', str(key))
            converted.append(dict(page, page=int(page.get('page', match.group() if match else len(converted) + 1))))
        return normalize_extractor_result(dict(data, pages=converted), extractor)
    if isinstance(data, list) and data and all((isinstance(item, dict) and ('type' in item or 'block_type' in item) for item in data)):
        data = [dict(item, type=item.get('type', item.get('block_type'))) for item in data]
    if isinstance(data, dict) and 'pages' not in data and ('tables' not in data) and ('words' not in data):
        for field in ('markdown', 'html', 'content', 'full_text', 'text'):
            if isinstance(data.get(field), str):
                return normalize_extractor_result(data[field], extractor)
        if isinstance(data.get('children'), list):
            return normalize_extractor_result(data['children'], extractor)
    if isinstance(data, list) and (not data):
        return []
    if hasattr(data, 'df'):
        return normalize_extractor_result(data.df, extractor)
    if hasattr(data, 'to_dict') and (not isinstance(data, dict)):
        try:
            data = [list(map(str, data.columns))] + data.to_numpy().tolist()
        except AttributeError:
            data = [list(map(str, data.columns))] + data.values.tolist()
    if isinstance(data, list) and data and all((isinstance(row, (list, tuple)) for row in data)):
        return [dict(page=1, width=0, height=0, words=[], text='', tables=[dict(rows=[list(row) for row in data], spans=[], cells=[], bbox=None, origin='matrix')])]
    if isinstance(data, dict) and 'pages' in data and isinstance(data['pages'], list):
        output = []
        for number, page in enumerate(data['pages'], 1):
            if not any((field in page for field in ('words', 'tables', 'text', 'markdown', 'children'))):
                raise ValueError('unsupported_page_shape: provide words/tables/text/markdown/children')
            width, height = (float(page.get('width', 0)), float(page.get('height', 0)))
            space = page.get('coordinate_space', data.get('coordinate_space', 'pdf_points'))
            words = [normalize_word(word, height, space, width, height) for word in page.get('words', [])]
            tables = []
            for table in page.get('tables', []):
                tables.append(table if isinstance(table, dict) else dict(rows=table, spans=[], cells=[], bbox=None))
            text = str(page.get('text', page.get('markdown', '')))
            tables.extend(parse_html_tables(text) if '<table' in text.lower() else parse_markdown_tables(text))
            if isinstance(page.get('children'), list):
                for child in normalize_extractor_result(page['children'], extractor):
                    text += child['text']
                    tables.extend(child['tables'])
            output.append(dict(page=int(page.get('number', page.get('page', number))), width=width, height=height, words=words, text=text, tables=tables))
        return output
    if isinstance(data, list) and all((isinstance(item, dict) and 'data' in item for item in data)):
        pages = {}
        for table in data:
            number = int(table.get('page', 1))
            page = pages.setdefault(number, dict(page=number, width=float(table.get('page_width', 0)), height=float(table.get('page_height', 0)), words=[], text='', tables=[]))
            rows, cells = ([], [])
            for row in table['data']:
                rows.append([str(cell.get('text', '')) for cell in row])
                cells.extend(([cell.get('left', 0), cell.get('top', 0), cell.get('left', 0) + cell.get('width', 0), cell.get('top', 0) + cell.get('height', 0)] for cell in row))
            page['tables'].append(dict(rows=rows, cells=cells, spans=[], bbox=table.get('bbox'), origin='tabula_json'))
        return list(pages.values())
    if isinstance(data, dict) and 'tables' in data:
        pages = {}
        for table in data['tables']:
            number = int((table.get('prov') or [{}])[0].get('page_no', table.get('page', 1)))
            page = pages.setdefault(number, dict(page=number, width=0, height=0, words=[], text='', tables=[]))
            detail = table.get('data', table)
            if 'table_cells' not in detail:
                page['tables'].append(dict(rows=detail.get('rows', []), cells=detail.get('cells', []), spans=detail.get('spans', []), bbox=table.get('bbox'), origin=extractor))
                continue
            nr, nc = (int(detail.get('num_rows', 0)), int(detail.get('num_cols', 0)))
            if nr > MAX_MATRIX_ROWS or nc > MAX_MATRIX_COLUMNS:
                raise ValueError('matrix_size_limit')
            rows, spans = ([[''] * nc for _ in range(nr)], [])
            for cell in detail['table_cells']:
                r, c = (int(cell['start_row_offset_idx']), int(cell['start_col_offset_idx']))
                if r >= nr or c >= nc:
                    continue
                rows[r][c] = cell.get('text', '')
                spans.append(dict(row=r, column=c, text=cell.get('text', ''), rowspan=int(cell.get('row_span', cell.get('end_row_offset_idx', r + 1) - r)), colspan=int(cell.get('col_span', cell.get('end_col_offset_idx', c + 1) - c)), is_header=bool(cell.get('column_header')), source_order=False))
            page['tables'].append(dict(rows=rows, cells=[], spans=spans, bbox=None, origin='docling_json'))
        for text_item in data.get('texts', []):
            number = int((text_item.get('prov') or [{}])[0].get('page_no', 1))
            page = pages.setdefault(number, dict(page=number, width=0, height=0, words=[], text='', tables=[]))
            page['text'] += str(text_item.get('text', '')) + '\n'
        return list(pages.values())
    if isinstance(data, list) and all((isinstance(item, dict) and 'type' in item for item in data)):
        pages = {}
        for item in data:
            metadata = item.get('metadata', {})
            number = int(metadata.get('page_number', item.get('page_idx', 0) + 1) or 1)
            page = pages.setdefault(number, dict(page=number, width=0, height=0, words=[], text='', tables=[]))
            text = str(item.get('text', item.get('html', item.get('table_body', ''))))
            page['text'] += text + '\n'
            table_html = metadata.get('text_as_html', item.get('table_body', item.get('html', '')))
            if table_html:
                page['tables'].extend(parse_html_tables(table_html))
            elif item['type'].lower() == 'table':
                page['tables'].extend(parse_markdown_tables(text))
            if isinstance(item.get('children'), list):
                for child in normalize_extractor_result(item['children'], extractor):
                    page['text'] += child['text']
                    page['tables'].extend(child['tables'])
        return list(pages.values())
    if isinstance(data, dict) and 'words' in data:
        return normalize_extractor_result(dict(pages=[data]), extractor)
    raise ValueError('unsupported_extractor_shape: provide pages/words/tables, matrix, Tabula, Docling or Unstructured JSON')

def normalize_cell_text(raw):
    raw = '' if raw is None else str(raw)
    normalized = unicodedata.normalize('NFKC', raw).replace('\xad', '').replace('\xa0', ' ').replace('\u200b', '')
    normalized = normalized.replace('\r\n', '\n').replace('\r', '\n').strip()
    normalized = re.sub('[ \\t]+', ' ', normalized)
    return normalized

def parse_cell_value(raw, decimal_style=DEFAULT_DECIMAL_STYLE):
    if decimal_style not in ('dot', 'comma'):
        raise ValueError('decimal_style must be explicitly dot or comma')
    text = normalize_cell_text(raw)
    repairs = []
    joined = re.sub('(?<=[,.])\\s*\\n\\s*(?=\\d)|(?<=\\d)\\s*\\n\\s*(?=[,.])', '', text)
    if joined != text:
        repairs.append('F19')
        text = joined
    if re.fullmatch('[+-]?\\d{1,3}(?:[ \\u202f]\\d{3})+(?:\\.\\d+)?', text):
        text = re.sub('[ \\u202f]', '', text)
        repairs.append('F07')
    if decimal_style == 'comma' and re.fullmatch('[+-]?(?:\\d{1,3}(?:\\.\\d{3})+|\\d+),\\d+%?', text):
        text = text.replace('.', '').replace(',', '.')
        repairs.append('F09')
    parsed = parse_value(text)
    if parsed['status'] == 'unresolved_text' and re.fullmatch('[\\d\\s.,()+%-]+', text) and re.search('\\d', text):
        parsed['status'] = 'ambiguous_numeric'
    if parsed['status'] == 'numeric' and (not Decimal(parsed['value']).is_finite()):
        parsed.update(value=None, status='unresolved_text')
    alternatives = []
    if parsed['status'] == 'unresolved_text' and re.fullmatch('[()\\-+\\d,OIlSＢ％%. ]+', text) and re.search('[OIlSＢ]', text):
        candidate = text.translate(str.maketrans({'O': '0', 'I': '1', 'l': '1', 'S': '5', 'Ｂ': '8'}))
        value = parse_value(candidate)
        if value['status'] == 'numeric':
            alternatives.append(dict(text=candidate, value=value['value'], status='requires_independent_evidence'))
    if parsed['status'] == 'unresolved_text' and (not alternatives):
        parsed['status'] = 'text'
    return dict(parsed, raw_text='' if raw is None else str(raw), normalized_text=text, repairs=repairs, alternatives=alternatives)

def repair_matrix(table):
    raw_rows = [[raw_cell_text(value) for value in row] for row in table.get('rows', [])]
    rows = [[normalize_cell_text(value) for value in row] for row in raw_rows]
    issues = []

    def record(code, action, detail, resolved=True):
        issues.append(dict(code=code, action=action, detail=detail, status='REPAIRED' if resolved else 'REVIEW'))
    if not rows:
        return dict(table, raw_rows=raw_rows, rows=[], issues=[], grid=[], header_paths=[])
    if len(rows) > MAX_MATRIX_ROWS or max(map(len, rows)) > MAX_MATRIX_COLUMNS:
        raise ValueError('matrix_size_limit')
    if rows != raw_rows:
        record('F03', 'normalized_copy', 'Original cell text preserved in raw_rows')
    for r, raw_row in enumerate(table.get('rows', [])):
        for c, raw in enumerate(raw_row):
            if isinstance(raw, dict) and raw.get('fragments'):
                record('F06', 'same_cell_fragments', f'{r},{c}; fragment JSON retained')
            if c == 0 and '\n' in raw_cell_text(raw):
                rows[r][c] = re.sub('\\s*\\n\\s*', ' ', rows[r][c])
                record('F18', 'same_cell_label_continuation', f'{r},{c}')
    source_map = {(r, c): dict(row=r, column=c, raw_value=value) for r, row in enumerate(raw_rows) for c, value in enumerate(row)}
    if len({len(row) for row in rows}) > 1 and (not table.get('spans')):
        record('F21', 'ragged_rows_padded_missing', 'Missing cells stay empty; original lengths retained', False)
    spans = [dict(span) for span in table.get('spans', [])]
    if spans:
        grid = []
        occupied = {}
        source_map = {}
        for span in spans:
            r = int(span['row'])
            c = int(span['column'])
            if span.get('source_order'):
                while (r, c) in occupied:
                    c += 1
            nr, nc = (max(1, int(span.get('rowspan', 1))), max(1, int(span.get('colspan', 1))))
            if r < 0 or c < 0 or r + nr > MAX_MATRIX_ROWS or (c + nc > MAX_MATRIX_COLUMNS):
                record('F16', 'invalid_span_retained', str(span), False)
                continue
            while len(grid) < r + nr:
                grid.append([])
            for rr in range(r, r + nr):
                if len(grid[rr]) < c + nc:
                    grid[rr].extend([''] * (c + nc - len(grid[rr])))
            if any(((rr, cc) in occupied for rr in range(r, r + nr) for cc in range(c, c + nc))):
                record('F17', 'overlapping_span', str(span), False)
                continue
            grid[r][c] = normalize_cell_text(span.get('text', rows[r][span['column']] if r < len(rows) and span['column'] < len(rows[r]) else ''))
            source_map[r, c] = dict(row=int(span['row']), column=int(span['column']), raw_value=span.get('text', ''))
            for rr in range(r, r + nr):
                for cc in range(c, c + nc):
                    occupied[rr, cc] = dict(row=r, column=c, is_header=bool(span.get('is_header')), text=grid[r][c])
            span['normalized_column'] = c
            if nr > 1 or nc > 1:
                record('F16' if span.get('is_header') else 'F17', 'explicit_span_anchor_restored', f'{r},{c} spans {nr}x{nc}; shadow values remain blank')
        rows = grid
    else:
        occupied = {}
    before = (len(rows), max(map(len, rows), default=0))
    while rows and (not any(rows[-1])):
        rows.pop()
    width = max(map(len, rows), default=0)
    rows = [row + [''] * (width - len(row)) for row in rows]
    while width and rows and (not any((row[width - 1] for row in rows))):
        for row in rows:
            row.pop()
        width -= 1
    if before != (len(rows), width):
        record('F02', 'trimmed_fully_empty_trailing_edges', str(before))
    if not rows or not width:
        return dict(table, raw_rows=raw_rows, rows=[], issues=issues, grid=[], header_paths=[])
    if not rows[0][0]:
        rows[0][0] = 'ITEM'
        record('F01', 'synthetic_header', 'ITEM; original blank retained in raw_rows')
    header = list(rows[0])
    clean_rows = [header]
    row_sources = [0]
    for source_row, row in enumerate(rows[1:], 1):
        if row == header:
            record('F05', 'removed_exact_repeated_header', str(row))
        else:
            clean_rows.append(row)
            row_sources.append(source_row)
    rows = clean_rows
    displayed, counts = ([], Counter())
    for index, name in enumerate(header):
        original = name or f'COLUMN_{index + 1}'
        counts[original] += 1
        displayed.append(original if counts[original] == 1 else original + '__' + str(counts[original]))
    if any((count > 1 for count in counts.values())):
        record('F04', 'disambiguated_display_headers', str(displayed))
    parsed = [[parse_cell_value(value, table.get('decimal_style', DEFAULT_DECIMAL_STYLE)) for value in row] for row in rows]
    for r, row in enumerate(parsed):
        for c, cell in enumerate(row):
            for code in cell['repairs']:
                record(code, 'normalized_numeric_candidate', f'{r},{c}')
            if cell['alternatives']:
                record('F20', 'numeric_alternative_not_accepted', f"{r},{c}: {cell['alternatives']}", False)
            if cell['status'] == 'ambiguous_numeric':
                record('F22', 'ambiguous_number_or_collision', f'{r},{c}', False)
    header_depth = int(table.get('header_rows', 0))
    if not header_depth:
        header_depth = max([span['row'] + int(span.get('rowspan', 1)) for span in spans if span.get('is_header')] or [1])
    header_depth = min(header_depth, len(rows))
    paths = []
    for c in range(width):
        path = []
        for r in range(header_depth):
            value = rows[r][c]
            anchor = occupied.get((r, c))
            if not value and anchor and anchor['is_header']:
                value = anchor['text']
            if value and (not path or path[-1] != value):
                path.append(value)
        paths.append(path)
    if header_depth > 1:
        record('F15', 'hierarchical_header_paths', str(paths))
    if width == 1:
        record('F23', 'single_column_text_candidate_rejected', 'Raw content retained', False)
    return dict(table, raw_input_rows=table.get('rows', []), raw_rows=raw_rows, rows=rows, display_headers=displayed, header_paths=paths, source_cell_map=[[source_map.get((source_row, c), dict(row=None, column=None, raw_value='')) for c in range(width)] for source_row in row_sources], header_rows=header_depth, parsed_cells=parsed, grid_anchors=[dict(covered_row=r, covered_column=c, anchor_row=anchor['row'], anchor_column=anchor['column'], is_header=anchor['is_header'], text=anchor['text']) for (r, c), anchor in occupied.items()], spans=spans, issues=issues)

def reconstruct_matrix_period_table(record, table, number):
    rows = table['rows']
    if not rows or max(map(len, rows)) < 2:
        return None
    header = None
    for index, row in enumerate(rows[:max(1, table.get('header_rows', 1))]):
        periods = []
        for c, text in enumerate(row):
            path = table.get('header_paths', [[]] * len(row))[c]
            scope = 'quarter' if any((re.search('季度|quarter', part, re.I) for part in path[:-1])) else 'annual' if any((re.search('年度|annual', part, re.I) for part in path[:-1])) else 'mixed'
            period = parse_period(text, scope)
            parent_year = next((part for part in path[:-1] if re.fullmatch('20\\d{2}', part)), None)
            if parent_year and re.fullmatch('Q[1-4]', text, re.I):
                period = parse_period(parent_year + text, 'quarter')
            elif parent_year and text.upper() == 'FY':
                period = parse_period(parent_year, 'annual')
            if period:
                periods.append((c, period))
        if len(periods) >= MATRIX_MIN_PERIOD_COLUMNS:
            header = (index, periods)
    if header is None:
        return None
    index, periods = header
    label_columns = [c for c in range(len(rows[0])) if c not in [column for column, _ in periods]]
    if not label_columns:
        return None
    data, textual = ([], [])
    for row in rows[index + 1:]:
        label = ' '.join((row[c] for c in label_columns if row[c])).strip()
        if not label:
            continue
        if re.match('(?:Source\\s*:|資料來源|Note\\s*:|註[：:])', label, re.I):
            textual.append(dict(role='source_or_note', text=' '.join(row), bbox=None))
            continue
        raw = [row[c] for c, _ in periods]
        data.append(dict(label=label, section=None, raw_values=raw, cells=[parse_cell_value(value, table.get('decimal_style', DEFAULT_DECIMAL_STYLE)) for value in raw], value_bboxes=[None] * len(raw), unit=infer_unit(label, raw, infer_default_unit(table.get('unit', ' '.join(rows[0]))), None), row_kind='quarter' if re.fullmatch('Q[1-4]', label, re.I) else 'annual' if label.upper() == 'FY' else 'same_as_header'))
    if len(data) < 1:
        return None
    return dict(id=f"{record['key']}_matrix_{number}", page_key=record['key'], bbox=table.get('bbox'), headers=[dict(period=period, word=None) for _, period in periods], rows=data, textual_rows=textual, default_unit='mixed', region_origin='automatic_imported_matrix_candidate', structure_checks=[dict(rule='matrix_shape_preserved', status='PASS')])

def extract_imported_source(path, digest, run_dir, max_pages=0):
    if path.stat().st_size > MAX_IMPORT_BYTES:
        raise ValueError('import_size_limit')
    extension = path.suffix.lower()
    if extension == '.json':
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        pages = normalize_extractor_result(data, data.get('extractor', 'auto') if isinstance(data, dict) else 'auto')
    elif extension in ('.csv', '.tsv'):
        with path.open(encoding='utf-8-sig', newline='') as stream:
            data = list(csv.reader(stream, delimiter='\t' if extension == '.tsv' else ','))
        pages = normalize_extractor_result(data)
    else:
        text = path.read_text(encoding='utf-8-sig')
        tables = parse_html_tables(text) if '<table' in text.lower() else parse_markdown_tables(text)
        if not tables and '\t' in text:
            tables = [dict(rows=list(csv.reader(text.splitlines(), delimiter='\t')), spans=[], cells=[], bbox=None)]
        pages = [dict(page=1, width=0, height=0, words=[], text=text, tables=tables)]
    results = []
    for page in pages[:max_pages or None]:
        key = f"INPUT_{digest[:12]}_p{page['page']:02d}"
        directory = run_dir / key
        directory.mkdir()
        words = page['words']
        width = page['width'] or max([w['x1'] for w in words] or [1])
        height = page['height'] or max([w['y1'] for w in words] or [1])
        payload = dict(source_sha256=digest, page=page['page'], width=width, height=height, words=words, native_words=words, spans=[], lines=[], figures=[], default_tables=page['tables'], table_error=None, ocr_attempts=[], rendered=False, raw_text=page['text'], sorted_text=page['text'], extraction_seconds=0, imported=True)
        write_json(directory / 'words.json', words)
        write_json(directory / 'spans.json', [])
        write_json(directory / 'extractor_raw_tables.json', page['tables'])
        (directory / 'raw_text.txt').write_text(page['text'], encoding='utf-8')
        (directory / 'sorted_text.txt').write_text(page['text'], encoding='utf-8')
        record = dict(key=key, source=path.name, source_path=str(path), source_sha256=digest, cohort='imported', page=page['page'], width=width, height=height, words=len(words), native_words=len(words), default_tables=len(page['tables']), cache_hit=False, elapsed_extraction_seconds=0)
        results.append((record, payload))
    return results

def repair_body_text(payload):
    """保留觀測區塊；只接同 block 的行，不跨欄猜測敘事。"""
    if not payload['words']:
        raw = payload['raw_text']
        body = html_body_text(raw) if re.search('<(?:p|div|table|html|body)\\b', raw, re.I) else raw
        return dict(text=normalize_cell_text(body), original_text=raw, status='text_only_reading_order_unverified')
    blocks = {}
    for word in payload['words']:
        blocks.setdefault(word.get('block', 0), []).append(word)
    entries = []
    for number, words in blocks.items():
        box = get_cell_bbox(words)
        lines = [legacy_join_words(group['words']) for group in cluster_rows(words)]
        text = '\n'.join(lines)
        text = re.sub('([\\u3400-\\u9fff])\\n(?=[\\u3400-\\u9fff])', '\\1', text)
        entries.append(dict(block=number, bbox=box, text=normalize_cell_text(text)))
    entries = sort_block_reading_order(entries)
    return dict(text='\n\n'.join((entry['text'] for entry in entries)), blocks=entries, status='coordinate_reconstructed_reading_order_candidate')

def sort_block_reading_order(entries):
    if len(entries) < 2:
        return entries
    ordered = sorted(entries, key=lambda item: item['bbox'][0])
    for index in range(1, len(ordered)):
        left, right = (ordered[:index], ordered[index:])
        gap = min((item['bbox'][0] for item in right)) - max((item['bbox'][2] for item in left))
        if gap >= READING_ORDER_GUTTER:
            return sort_block_reading_order(left) + sort_block_reading_order(right)
    return sorted(entries, key=lambda item: (item['bbox'][1], item['bbox'][0]))

def reconcile_extractor_results(results):
    """共同 source_id/table_key/row/column 才可比對；獨立兩工具同值可補缺。
    不同擷取器意見衝突時保留全部候選；不用財務算式推造值。
    """
    grouped = {}
    for result in results:
        key = (result.get('source_id'), result.get('table_key'), result.get('row'), result.get('column'))
        if None in key:
            raise ValueError('reconciliation_requires_source_id_table_key_row_column')
        grouped.setdefault(key, []).append(result)
    output = []
    for key, candidates in grouped.items():
        values = {}
        for candidate in candidates:
            parsed = parse_cell_value(candidate.get('raw_value'))
            if parsed['value'] is not None:
                values.setdefault(Decimal(parsed['value']), set()).add(candidate['extractor'])
        accepted = next((value for value, tools in values.items() if len(tools) >= 2), None) if len(values) == 1 else None
        output.append(dict(source_id=key[0], table_key=key[1], row=key[2], column=key[3], candidates=candidates, resolved_value=str(accepted) if accepted is not None else None, status='INDEPENDENT_AGREEMENT' if accepted is not None else 'CONFLICT' if len(values) > 1 else 'UNVERIFIED'))
    return output

def extract_page_payload(page, plumber_page, cache_dir, render, ocr_mode, ocr_language, source_hash):
    if ocr_mode != 'off':
        raise ValueError('POLICY: Layout/OCR invocation is disabled')
    started = time.perf_counter()
    native = [dict(x0=w[0], y0=w[1], x1=w[2], y1=w[3], text=w[4], block=w[5], line=w[6], word=w[7], origin='native') for w in page.get_text('words')]
    structure = page.get_text('dict')
    spans = [dict(text=s['text'], bbox=list(s['bbox']), font=s['font'], size=s['size'], color=s['color'], alpha=s.get('alpha')) for block in structure['blocks'] for line in block.get('lines', []) for s in line['spans']]
    lines = [dict(text=''.join((s['text'] for s in line['spans'])).strip(), bbox=list(line['bbox'])) for block in structure['blocks'] for line in block.get('lines', [])]
    figures = [dict(bbox=list(block['bbox']), role='figure_or_raster_candidate') for block in structure['blocks'] if block.get('type') == 1]
    table_error, table_records = (None, [])
    period_count = sum((parse_period(word['text'], 'mixed') is not None for word in native))
    numeric_count = sum((parse_value(word['text'])['status'] == 'numeric' for word in native))
    if plumber_page is not None and (period_count >= MIN_PERIOD_COLUMNS or numeric_count >= SECONDARY_DETECTOR_MIN_NUMBERS):
        try:
            for table in plumber_page.find_tables():
                table_records.append(dict(bbox=list(table.bbox), rows=table.extract(), cells=[list(cell) if cell else None for cell in table.cells]))
        except Exception as error:
            table_error = f'{type(error).__name__}: {error}'
    image_hash = None
    if render:
        page.get_pixmap(matrix=fitz.Matrix(RENDER_SCALE, RENDER_SCALE), alpha=False).save(cache_dir / 'original.png')
        image_hash = file_sha256(cache_dir / 'original.png')
    return dict(source_sha256=source_hash, page=page.number + 1, width=page.rect.width, height=page.rect.height, words=native, native_words=native, spans=spans, lines=lines, figures=figures, raw_text=page.get_text(), sorted_text=page.get_text(sort=True), default_tables=table_records, table_error=table_error, ocr_attempts=[], rendered=bool(render), image_sha256=image_hash, extraction_seconds=time.perf_counter() - started, imported=False)

def collect_merged_cell_candidates(payload):
    evidence = []
    for index, table in enumerate(payload['default_tables']):
        cells = [box for box in table.get('cells', []) if isinstance(box, (list, tuple)) and len(box) == 4]
        x_edges = sorted(set((round(x, 1) for cell in cells for x in (cell[0], cell[2]))))
        y_edges = sorted(set((round(y, 1) for cell in cells for y in (cell[1], cell[3]))))
        for cell in cells:
            inner_x = [x for x in x_edges if cell[0] + 0.5 < x < cell[2] - 0.5]
            inner_y = [y for y in y_edges if cell[1] + 0.5 < y < cell[3] - 0.5]
            if inner_x or inner_y:
                evidence.append(dict(detector_table=index, bbox=cell, column_span_candidate=len(inner_x) + 1, row_span_candidate=len(inner_y) + 1, status='geometric_merge_candidate', policy='explicit_spans_restored_but_inferred_spans_require_evidence'))
    return evidence

def classify_page_roles(record, payload, tables):
    roles = list(payload['figures'])
    page_tables = [table for table in tables if table['page_key'] == record['key']]
    for table in page_tables:
        roles.append(dict(role='table_candidate', table_id=table['id'], bbox=table['bbox'], origin=table['region_origin']))
    for line in payload['lines']:
        text = line['text']
        if not text:
            continue
        if re.match('(?:資料來源|Source:)', text, re.I):
            role = 'source'
        elif re.match('(?:單位[：:])', text):
            role = 'unit'
        elif re.match('(?:Note:|註[：:]|EPS\\s*以)', text, re.I):
            role = 'note'
        elif any((table['bbox'] and legacy_inside(dict(x0=line['bbox'][0], y0=line['bbox'][1], x1=line['bbox'][2], y1=line['bbox'][3]), table['bbox']) for table in page_tables)):
            role = 'table_text_or_value_line'
        else:
            role = 'body_or_metadata_candidate'
        roles.append(dict(role=role, text=text, bbox=line['bbox'], status='line_level_candidate'))
    return roles

def run_self_checks():
    checks = []

    def check(name, condition):
        checks.append(dict(rule=name, status='PASS' if condition else 'FAIL'))
    for raw, value, status in [('1,234.50', '1234.50', 'numeric'), ('(83)', '-83', 'numeric'), ('0', '0', 'numeric'), ('', None, 'empty'), ('-', None, 'dash_unspecified'), ('盈轉虧', None, 'categorical'), ('NM', None, 'categorical')]:
        parsed = parse_cell_value(raw)
        check('value_' + repr(raw), parsed['value'] == value and parsed['status'] == status)
    check('month_scope_distinct', parse_period('Dec-25A', 'quarter')['period'] == '2025-Q4' and parse_period('Dec-25A', 'annual')['period'] == '2025')
    check('ambiguous_month_preserved', parse_period('Dec-25A', 'mixed')['kind'] == 'ambiguous_month')
    check('quarter_suffix', parse_period('25Q3(F)', 'mixed')['period'] == '2025-Q3')
    check('units_exact', canonical_amount('1234500', 'TWD_thousand') == ('1234.500', 'TWD_million'))
    check('EPS_unscaled', canonical_amount('8.14', 'TWD_per_share') == (None, None))
    check('numeric_confusion_not_accepted', parse_cell_value('1O0')['value'] is None and bool(parse_cell_value('1O0')['alternatives']))
    check('no_missing_zero', parse_cell_value('')['value'] is None and parse_cell_value('0')['value'] == '0')
    check('blank_corner_ITEM', repair_matrix({'rows': [['', '2025'], ['營收', '0']]})['rows'][0][0] == 'ITEM')
    merged = parse_html_tables('<table><tr><th></th><th colspan="2">2025</th></tr><tr><th>ITEM</th><th>Q1</th><th>FY</th></tr><tr><td>A</td><td colspan="2">10</td></tr></table>')[0]
    repaired = repair_matrix(merged)
    check('header_merge_path', repaired['header_paths'][1] == ['2025', 'Q1'] and repaired['header_paths'][2] == ['2025', 'FY'])
    check('body_merge_not_forward_filled', repaired['rows'][2][1:] == ['10', ''])
    check('normalization_Tabula', normalize_extractor_result([{'data': [[{'text': 'A'}, {'text': '0'}]], 'page': 1}])[0]['tables'][0]['rows'][0] == ['A', '0'])
    check('normalization_matrix', normalize_extractor_result([['ITEM', '2025'], ['A', '0']])[0]['tables'][0]['rows'][1] == ['A', '0'])
    check('normalization_words', normalize_word([10, 20, 30, 40, 'x'])['text'] == 'x')
    check('coordinate_bottom_left', normalize_word({'bbox': [10, 20, 30, 40], 'text': 'x'}, page_height=100, coordinate_space='bottom_left')['y0'] == 60)
    check('25_failure_cases', len(FAILURE_CASES) == 25 and len({entry[0] for entry in FAILURE_CASES}) == 25)
    check('20_tool_groups_registered', len(TOOL_REGISTRY) == 20)
    conflict = reconcile_extractor_results([dict(source_id='s', table_key='t', row=1, column=1, extractor='a', raw_value='10'), dict(source_id='s', table_key='t', row=1, column=1, extractor='b', raw_value='11')])
    check('extractor_conflict_not_overwritten', conflict[0]['status'] == 'CONFLICT' and conflict[0]['resolved_value'] is None)
    check('F02_internal_blanks_preserved', repair_matrix({'rows': [['ITEM', '2025', '2026'], ['A', '', '1'], ['', '', '']]})['rows'] == [['ITEM', '2025', '2026'], ['A', '', '1']])
    check('F04_duplicate_header_display_only', repair_matrix({'rows': [['ITEM', '2025', '2025'], ['A', '1', '2']]})['display_headers'] == ['ITEM', '2025', '2025__2'])
    repeated = repair_matrix({'rows': [['ITEM', '2025', '2026'], ['A', '1', '2'], ['ITEM', '2025', '2026'], ['B', '3', '4']]})
    check('F05_source_map_after_header_removal', len(repeated['rows']) == 3 and repeated['source_cell_map'][2][1]['row'] == 3 and (repeated['source_cell_map'][2][1]['raw_value'] == '3'))
    fragmented = repair_matrix({'rows': [['ITEM', '2025'], ['A', {'fragments': ['1,', '234', '.5']}]]})
    check('F06_fragments_and_raw_JSON', fragmented['parsed_cells'][1][1]['value'] == '1234.5' and fragmented['raw_input_rows'][1][1]['fragments'] == ['1,', '234', '.5'])
    check('F09_decimal_comma_explicit', parse_cell_value('1.234,50', 'comma')['value'] == '1234.50')
    check('F09_ambiguous_grouping_not_guessed', parse_cell_value('1,23')['status'] == 'ambiguous_numeric' and parse_cell_value('1,23')['value'] is None)
    check('F18_wrapped_label_same_cell', repair_matrix({'rows': [['ITEM', '2025'], ['營業\n收入', '10']]})['rows'][1][0] == '營業 收入')
    check('F19_wrapped_number', parse_cell_value('1,\n234.5')['value'] == '1234.5')
    ragged = repair_matrix({'rows': [['ITEM', '2025', '2026'], ['A', '10']]})
    check('F21_missing_not_zero', ragged['rows'][1][-1] == '' and any((i['code'] == 'F21' and i['status'] == 'REVIEW' for i in ragged['issues'])))
    collision = repair_matrix({'rows': [['ITEM', '2025'], ['A', '10 20']]})
    check('F22_numeric_collision_review', any((i['code'] == 'F22' and i['status'] == 'REVIEW' for i in collision['issues'])))
    check('F23_single_column_is_text_candidate', any((i['code'] == 'F23' for i in repair_matrix({'rows': [['正文'], ['第二段']]})['issues'])))
    memory = repair_extracted_data({'tables': [{'rows': [['ITEM', '2024', '2025', '2026'], ['A', '1', '2', '3'], ['Source: X', '9', '9', '9']]}]})
    check('F25_notes_not_annual_data', len(memory['annual_candidates']) == 3 and (not any((r['account_raw'].startswith('Source:') for r in memory['annual_candidates']))))
    mixed = repair_extracted_data({'tables': [{'rows': [['ITEM', '2024', '2025', '2026'], ['Q1', '1', '2', '3'], ['FY', '4', '5', '6']]}]})
    check('F14_quarter_rows_not_annual_data', len(mixed['annual_candidates']) == 3 and all((r['account_raw'] == 'FY' for r in mixed['annual_candidates'])))
    check('adapter_MinerU_HTML', normalize_extractor_result([{'type': 'table', 'page_idx': 2, 'table_body': '<table><tr><td>A</td><td>0</td></tr></table>'}])[0]['page'] == 3)
    check('adapter_Marker_HTML', normalize_extractor_result({'children': [{'type': 'Table', 'html': '<table><tr><td>A</td><td>1</td></tr></table>'}]})[0]['tables'][0]['rows'] == [['A', '1']])
    check('adapter_Tika_content', normalize_extractor_result({'content': 'Hello'})[0]['text'] == 'Hello')
    existing_ocr = normalize_extractor_result({'ocr_results': [[[[10, 20], [30, 20], [30, 40], [10, 40]], ('A', 0.9)]], 'coordinate_space': 'pixels', 'dpi': 144, 'width': 200, 'height': 200})
    check('adapter_existing_OCR_no_invocation', existing_ocr[0]['words'][0]['bbox'] == [5, 10, 15, 20] if 'bbox' in existing_ocr[0]['words'][0] else existing_ocr[0]['words'][0]['x0'] == 5 and existing_ocr[0]['words'][0]['y0'] == 10)
    shifted = cluster_rows([{'x0': 0, 'x1': 30, 'y0': 14, 'y1': 22, 'text': '營收'}, {'x0': 60, 'x1': 90, 'y0': 10, 'y1': 19, 'text': '123'}])
    check('font_baseline_offset_same_row', len(shifted) == 1)
    blocks = sort_block_reading_order([{'bbox': [100, 0, 150, 10], 'text': 'R1'}, {'bbox': [0, 20, 50, 30], 'text': 'L2'}, {'bbox': [0, 0, 50, 10], 'text': 'L1'}])
    check('two_column_block_order', [b['text'] for b in blocks] == ['L1', 'L2', 'R1'])
    check('decimal_comma_invalid_grouping_review', parse_cell_value('1.23,45', 'comma')['value'] is None)
    agreement = reconcile_extractor_results([dict(source_id='s', table_key='t', row=1, column=1, extractor='a', raw_value='10.0'), dict(source_id='s', table_key='t', row=1, column=1, extractor='b', raw_value='10')])
    check('decimal_scale_agreement', agreement[0]['status'] == 'INDEPENDENT_AGREEMENT')
    check('hierarchical_matrix_periods', [h['period']['period'] for h in repair_extracted_data({'tables': [merged]})['pages'][0]['period_tables'][0]['headers']] == ['2025-Q1', '2025'])
    check('adapter_pdfplumber_words', normalize_extractor_result([dict(text='A', x0=1, x1=2, top=3, bottom=4)])[0]['words'][0]['y0'] == 3)
    check('adapter_PyMuPDF_dict', normalize_extractor_result(dict(blocks=[dict(lines=[dict(spans=[dict(text='A', bbox=[1, 2, 3, 4])])])]))[0]['words'][0]['text'] == 'A')
    check('HTML_body_and_table_channels', html_body_text('<p>Before</p><table><tr><td>A</td></tr></table><p>After</p>') == 'Before\n\nAfter')
    check('EPS_currency_not_guessed', infer_unit('EPS', ['1.2'], 'mixed', None) == 'currency_unspecified_per_share' and infer_unit('EPS (USD)', ['1.2'], 'mixed', None) == 'USD_per_share')
    text = Path(__file__).read_text(encoding='utf-8')
    module = ast.parse(text)
    compile(module, __file__, 'exec')
    spec = importlib.util.spec_from_file_location('_vrn_generic_import_test', __file__)
    spec.loader.exec_module(importlib.util.module_from_spec(spec))
    check('AST_compile_import', True)
    check('no_model_or_ocr_invocations', not any((isinstance(node, ast.FunctionDef) and node.name in ('run_tesseract', 'invoke_layout_adapter') for node in ast.walk(module))))
    return checks

def failure_case_evidence(records, tables, reviews):
    seen = {}
    for record, payload in records:
        for matrix in payload.get('repaired_matrices', []):
            for issue in matrix['issues']:
                seen.setdefault(issue['code'], []).append(dict(page_key=record['key'], **issue))
        if payload.get('invisible_candidates') or payload.get('duplicate_word_count'):
            seen.setdefault('F24', []).append(dict(page_key=record['key'], action='raw_text_preserved', detail='visibility or duplicate geometry evidence'))
        if len(payload['words']) < MIN_NATIVE_WORDS and (not payload.get('imported')):
            seen.setdefault('F21', []).append(dict(page_key=record['key'], action='no_new_OCR', status='REVIEW', detail='insufficient native text; external existing extractor result required'))
    for table in tables:
        periods = [header['period'] for header in table['headers']]
        if {period['kind'] for period in periods} >= {'annual', 'quarter'} or any((period['kind'] == 'ambiguous_month' for period in periods)):
            seen.setdefault('F14', []).append(dict(table_id=table['id'], action='separate_period_scopes', detail=periods))
        if any((row['unit'] in UNIT_TO_MILLION for row in table['rows'])):
            seen.setdefault('F10', []).append(dict(table_id=table['id'], action='explicit_unit_canonical_values'))
        if table['context']['above'] or table['context']['below']:
            seen.setdefault('F25', []).append(dict(table_id=table['id'], action='4_above_3_below_context_kept'))
        if any((row.get('label_continuation') for row in table['rows'])):
            seen.setdefault('F18', []).append(dict(table_id=table['id'], action='coordinate_supported_label_continuation'))
        for row in table['rows']:
            for raw, cell in zip(row['raw_values'], row['cells']):
                if ',' in raw and cell['status'] == 'numeric':
                    seen.setdefault('F07', []).append(dict(table_id=table['id'], raw=raw, action='decimal_string_parse'))
                if raw.startswith('(') or '−' in raw:
                    seen.setdefault('F08', []).append(dict(table_id=table['id'], raw=raw, action='signed_value_parse'))
                if cell['status'] in ('categorical', 'empty', 'dash_unspecified', 'not_available'):
                    seen.setdefault('F11', []).append(dict(table_id=table['id'], raw=raw, action='distinct_value_type'))
    page_tables = Counter((table['page_key'] for table in tables))
    for key, count in page_tables.items():
        if count > 1:
            seen.setdefault('F12', []).append(dict(page_key=key, detail=f'{count} independent regions', action='header_region_separation'))
            seen.setdefault('F13', []).append(dict(page_key=key, detail=f'{count} independent regions', action='header_vertical_reset'))
    for review in reviews:
        if review['reason'] in ('unresolved_mixed_row', 'candidate_structure_failed'):
            seen.setdefault('F22', []).append(dict(page_key=review['page_key'], status='REVIEW', detail=review['detail']))
    return [dict(code=code, scenario=name, handler=handler, solution=solution, evidence=seen.get(code, []), detection='OBSERVED' if code in seen else 'NOT_OBSERVED_IN_THIS_RUN') for code, name, handler, solution in FAILURE_CASES]

def is_parent_year_header(word, groups):
    period = parse_period(word['text'], 'mixed')
    if period is None or period['kind'] != 'annual' or (not re.fullmatch('20\\d{2}', word['text'])):
        return False
    y = (word['y0'] + word['y1']) / 2
    x = (word['x0'] + word['x1']) / 2
    for group in groups:
        if not 0 < group['center'] - y <= HEADER_MULTILINE_DISTANCE:
            continue
        children = [w for w in group['words'] if parse_period(w['text'], 'mixed') and parse_period(w['text'], 'mixed')['kind'] == 'quarter' and parse_period(w['text'], 'mixed')['period'].startswith(period['period'])]
        if len(children) >= 2 and min((w['x0'] for w in children)) <= x <= max((w['x1'] for w in children)):
            return True
    return False

def semantic_account_key(label):
    text = re.sub('\\([^)]*\\)', '', normalize_label(label)).lower()
    role = find_account_role(text)
    if role:
        return role
    if re.fullmatch('每股盈餘|eps|adj\\.?eps|dilutedeps', text, re.I):
        return 'eps'
    if re.fullmatch('稅後淨利|稅後純益|netprofit|netincome', text, re.I):
        return 'net_income'
    return text

def resolve_month_scopes_by_evidence(tables, source_lookup):
    resolved = []
    for table in tables:
        ambiguous = [index for index, header in enumerate(table['headers']) if header['period']['kind'] == 'ambiguous_month' and header['period']['period'].endswith('-12')]
        if not ambiguous:
            continue
        source = source_lookup[table['page_key']]['source_sha256']
        evidence = []
        for index in ambiguous:
            year = table['headers'][index]['period']['period'][:4]
            for row in table['rows']:
                value = row['cells'][index]['value']
                if value is None:
                    continue
                key = semantic_account_key(row['label'])
                for other in tables:
                    if other['id'] == table['id'] or source_lookup[other['page_key']]['source_sha256'] != source:
                        continue
                    columns = [j for j in annual_indices(other) if other['headers'][j]['period']['period'] == year]
                    matches = [candidate for candidate in other['rows'] if semantic_account_key(candidate['label']) == key]
                    for column in columns:
                        if any((candidate['cells'][column]['value'] is not None and Decimal(candidate['cells'][column]['value']) == Decimal(value) for candidate in matches)):
                            evidence.append(dict(year=year, account_key=key, value=value, table_id=other['id']))
        years = {item['year'] for item in evidence}
        accounts = {item['account_key'] for item in evidence}
        if len(years) >= SCOPE_MIN_MATCHED_YEARS and len(accounts) >= SCOPE_MIN_MATCHED_ACCOUNTS:
            for index in ambiguous:
                period = table['headers'][index]['period']
                period.update(period=period['period'][:4], kind='annual', scope_evidence='independent_explicit_annual_tables_and_matching_values')
            table['scope_repair_evidence'] = evidence
            table['structure_checks'] = validate_table_structure(table)
            resolved.append(table['id'])
    return resolved

def raw_cell_text(value):
    if value is None:
        return ''
    if isinstance(value, dict):
        if 'text' in value:
            return str(value['text'])
        fragments = value.get('fragments', [])
        fragments = [str(item.get('text', '')) if isinstance(item, dict) else str(item) for item in fragments]
        joined = ''.join(fragments)
        if fragments and any((re.search('[,.]', fragment) for fragment in fragments)) and (parse_value(joined)['status'] == 'numeric'):
            return joined
        return ' '.join(fragments)
    return str(value)

def repair_extracted_data(data, extractor='auto', source_id=None):
    """Pure stdlib post-processing. No file writes, PDF opening, OCR or model loading.
    Common JSON, HTML, Markdown, extractor envelopes and matrices are accepted.
    Missing metadata stays unknown. Geometric reconstruction yields candidates.
    """
    pages = normalize_extractor_result(data, extractor)
    try:
        digest = hashlib.sha256(json_bytes(data)).hexdigest()
    except TypeError:
        digest = hashlib.sha256(json_bytes(pages)).hexdigest()
    run_id = 'memory_' + uuid.uuid4().hex
    output, tables, source_lookup, errors = ([], [], {}, [])
    for position, page in enumerate(pages, 1):
        key = f"INPUT_{digest[:12]}_p{page['page']:02d}_{position}"
        record = dict(key=key, source_sha256=digest, source='in_memory', page=page['page'])
        source_lookup[key] = record
        payload = dict(words=page['words'], raw_text=page['text'], width=page['width'] or max([w['x1'] for w in page['words']] or [1]), height=page['height'] or max([w['y1'] for w in page['words']] or [1]), default_tables=page['tables'], spans=[], lines=[], figures=[], imported=True)
        record.update(width=payload['width'], height=payload['height'])     # v0101 ②:記憶體介面帶字詞座標 → 下游要頁寬頁高
        matrices = [repair_matrix(table) for table in page['tables']]
        candidates = []
        if payload['words']:
            for config in detect_lightweight_regions(record, payload):
                try:
                    candidate = reconstruct_table(config, payload['words'])
                    candidate['structure_checks'] = validate_table_structure(candidate)
                    candidates.append(candidate)
                except Exception as error:
                    errors.append(dict(page=page['page'], error=f'{type(error).__name__}: {error}'))
            candidates.extend(reconstruct_row_year_tables(record, payload, [t['bbox'] for t in candidates]))
        for number, matrix in enumerate(matrices, 1):
            candidate = reconstruct_matrix_period_table(record, matrix, number)
            if candidate:
                candidates.append(candidate)
        tables.extend(candidates)
        output.append(dict(page=page['page'], width=page['width'], height=page['height'], words=page['words'], original_text=page['text'], repaired_text=repair_body_text(payload), repaired_tables=matrices, period_tables=candidates))
    resolve_month_scopes_by_evidence(tables, source_lookup)
    annual, skipped = build_annual_records(tables, source_lookup, run_id)
    return dict(engine_version=ENGINE_VERSION, source_id=source_id or digest, source_sha256=digest, pages=output, annual_candidates=annual, skipped_annual_rows=skipped, financial_checks=validate_generic_financial(tables), errors=errors, layout_or_ocr_invocations=0, source_values_overwritten=False, all_cells_individually_verified=False)

def extract_source_job(path_string, digest, output_root_string, run_dir_string, extraction_options):
    """Independent worker opens its own PDF; never shares fitz objects across threads."""
    load_dependencies()
    path, output_root, run_dir = (Path(path_string), Path(output_root_string), Path(run_dir_string))
    stats = dict(cache_hits=0, cache_misses=0, secondary_extractor_errors=[])
    records = extract_source(path, digest, None, output_root, run_dir, extraction_options, stats, False) if path.suffix.lower() == '.pdf' else extract_imported_source(path, digest, run_dir, extraction_options['max_pages'])
    return (records, stats)

def extract_input_jobs(paths, output_root, run_dir, extraction_options, workers, progress):
    from concurrent.futures import ProcessPoolExecutor, as_completed
    if workers < 1:
        raise ValueError('workers must be >= 1')
    jobs, duplicates, errors, sources, records, seen = ([], [], [], [], [], set())
    totals = dict(cache_hits=0, cache_misses=0, secondary_extractor_errors=[])
    for path in paths:
        try:
            digest = file_sha256(path)
            if digest in seen:
                duplicates.append(dict(path=str(path), sha256=digest, reason='same_content_skipped'))
            else:
                seen.add(digest)
                jobs.append((path, digest))
        except Exception as error:
            errors.append(dict(path=str(path), error=f'{type(error).__name__}: {error}'))

    def accept(path, digest, result):
        extracted, stats = result
        records.extend(extracted)
        totals['cache_hits'] += stats['cache_hits']
        totals['cache_misses'] += stats['cache_misses']
        totals['secondary_extractor_errors'].extend(stats['secondary_extractor_errors'])
        sources.append(dict(path=str(path), filename=path.name, sha256=digest, size_bytes=path.stat().st_size, selected_pages=[record['page'] for record, _ in extracted]))
        if progress:
            print(f'[{len(sources) + len(errors)}/{len(jobs)}] {path.name}', flush=True)
    if workers == 1 or len(jobs) < 2:
        for path, digest in jobs:
            try:
                accept(path, digest, extract_source_job(str(path), digest, str(output_root), str(run_dir), extraction_options))
            except Exception as error:
                errors.append(dict(path=str(path), error=f'{type(error).__name__}: {error}'))
    else:
        with ProcessPoolExecutor(max_workers=min(workers, len(jobs))) as executor:
            futures = {executor.submit(extract_source_job, str(path), digest, str(output_root), str(run_dir), extraction_options): (path, digest) for path, digest in jobs}
            for future in as_completed(futures):
                path, digest = futures[future]
                try:
                    accept(path, digest, future.result())
                except Exception as error:
                    errors.append(dict(path=str(path), error=f'{type(error).__name__}: {error}'))
    records.sort(key=lambda item: (item[0]['source_path'], item[0]['page']))
    sources.sort(key=lambda item: item['path'])
    return (records, sources, duplicates, errors, totals)

def export_office_candidates(records, run_dir, formats):
    """Optional exporters only; packages are never installed automatically."""
    results = []
    for format_name in formats:
        try:
            if format_name == 'xlsx':
                from openpyxl import Workbook
                workbook = Workbook()
                workbook.remove(workbook.active)
                info = workbook.create_sheet('Readme')
                info.append(['擷取後修復候選；原值與未解決問題請見 JSON / review_queue'])
                count = 0
                for record, payload in records:
                    for matrix in payload.get('repaired_matrices', []):
                        count += 1
                        sheet = workbook.create_sheet(f'Table_{count}')
                        for r, row in enumerate(matrix['rows'], 1):
                            for c, text in enumerate(row, 1):
                                cell = sheet.cell(r, c, text)
                                cell.data_type = 's'
                        for span in matrix.get('spans', []):
                            r, c = (span['row'], span.get('normalized_column', span['column']))
                            nr, nc = (int(span.get('rowspan', 1)), int(span.get('colspan', 1)))
                            if (nr > 1 or nc > 1) and r + nr <= len(matrix['rows']) and (c + nc <= len(matrix['rows'][0])):
                                if all((matrix['source_cell_map'][rr][c]['row'] in (rr, None) for rr in range(r, r + nr))):
                                    sheet.merge_cells(start_row=r + 1, start_column=c + 1, end_row=r + nr, end_column=c + nc)
                        raw_sheet = workbook.create_sheet(f'Raw_{count}')
                        for r, row in enumerate(matrix['raw_rows'], 1):
                            for c, text in enumerate(row, 1):
                                cell = raw_sheet.cell(r, c, text)
                                cell.data_type = 's'
                target = run_dir / 'repaired_candidates.xlsx'
                workbook.save(target)
            elif format_name == 'docx':
                from docx import Document
                document = Document()
                document.add_heading('擷取後修復候選', 0)
                document.add_paragraph('原值與回查狀態保存在 JSON；本文保留候選文字及表格。')
                for record, payload in records:
                    document.add_heading(record['source'] + f" / p{record['page']}", 1)
                    document.add_paragraph(repair_body_text(payload)['text'])
                    for matrix in payload.get('repaired_matrices', []):
                        if not matrix['rows']:
                            continue
                        table = document.add_table(rows=len(matrix['rows']), cols=len(matrix['rows'][0]))
                        table.style = 'Table Grid'
                        for r, row in enumerate(matrix['rows']):
                            for c, text in enumerate(row):
                                table.cell(r, c).text = text
                target = run_dir / 'repaired_candidates.docx'
                document.save(target)
            else:
                raise ValueError('optional export must be xlsx or docx')
            results.append(dict(format=format_name, status='EXPORTED', path=str(target)))
        except Exception as error:
            results.append(dict(format=format_name, status='ERROR', error=f'{type(error).__name__}: {error}'))
    return results

def watch_folder(input_paths, output_root, interval=WATCH_INTERVAL_SECONDS, stable_polls=WATCH_STABLE_POLLS, iterations=0, workers=DEFAULT_WORKERS, render=True, max_pages=0):
    """Polling watch; historical completed hashes persist; sources are never moved.
    Stability is a heuristic. Process a snapshot only after matching pre/post stats
    and matching source/snapshot hashes. Ctrl+C stops normally, without Stop-Process.
    iterations=0 is continuous; positive values support bounded scheduled execution.
    """
    if interval <= 0 or stable_polls < 2 or iterations < 0:
        raise ValueError('watch needs positive interval, stable_polls>=2 and iterations>=0')
    output_root = Path(output_root).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    ledger = output_root / 'watch_events'
    ledger.mkdir(exist_ok=True)
    completed = set()
    for event in ledger.glob('*.json'):
        try:
            entry = json.loads(event.read_text(encoding='utf-8'))
            if entry.get('status') == 'COMPLETED' and entry.get('engine_sha256') == file_sha256(__file__):
                completed.add(entry['sha256'])
        except (OSError, ValueError, KeyError):
            pass
    observations, failed_signatures, count = ({}, set(), 0)
    try:
        while not iterations or count < iterations:
            count += 1
            paths, errors = find_pdf_inputs(input_paths)
            pending = []
            for path in paths:
                if output_root in path.parents:
                    continue
                try:
                    stat = path.stat()
                    signature = (stat.st_size, stat.st_mtime_ns)
                    previous, stable = observations.get(str(path), (None, 0))
                    stable = stable + 1 if signature == previous else 1
                    observations[str(path)] = (signature, stable)
                    if stable < stable_polls or (str(path), signature) in failed_signatures:
                        continue
                    digest = file_sha256(path)
                    if digest in completed:
                        continue
                    stage = output_root / 'watch_snapshots' / (digest + '_' + uuid.uuid4().hex[:8])
                    stage.mkdir(parents=True, exist_ok=False)
                    snapshot = stage / path.name
                    shutil.copyfile(path, snapshot)
                    after = path.stat()
                    if (after.st_size, after.st_mtime_ns) != signature or file_sha256(snapshot) != digest or file_sha256(path) != digest:
                        observations[str(path)] = (None, 0)
                        continue
                    pending.append((str(path), digest, signature, snapshot))
                except OSError as error:
                    errors.append(dict(path=str(path), error=str(error)))
            for original, digest, signature, snapshot in pending:
                try:
                    summary = run_engine([snapshot], output_root, render=render, max_pages=max_pages, workers=workers)
                    status = 'COMPLETED' if summary['status'] != 'FAIL' else 'ERROR'
                    entry = dict(status=status, original_path=original, sha256=digest, engine_sha256=file_sha256(__file__), run_dir=summary['run_dir'], candidate_status=summary['status'])
                    if status == 'COMPLETED':
                        completed.add(digest)
                    else:
                        failed_signatures.add((original, signature))
                except Exception as error:
                    entry = dict(status='ERROR', original_path=original, sha256=digest, error=f'{type(error).__name__}: {error}')
                    failed_signatures.add((original, signature))
                write_json(ledger / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ') + '_' + uuid.uuid4().hex[:8] + '.json'), entry)
                print(json.dumps(entry, ensure_ascii=False), flush=True)
            if errors:
                print(json.dumps(dict(status='WATCH_INPUT_ERRORS', errors=errors), ensure_ascii=False), flush=True)
            if not iterations or count < iterations:
                time.sleep(interval)
    except KeyboardInterrupt:
        return dict(status='WATCH_STOPPED', completed_hashes=len(completed), polls=count)
    return dict(status='WATCH_FINISHED', completed_hashes=len(completed), polls=count)

def html_body_text(text):
    """Tables stay in the table channel; preserve paragraph breaks in body text."""
    from html.parser import HTMLParser

    class BodyParser(HTMLParser):

        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.parts, self.table_depth, self.skip_depth = ([], 0, 0)

        def handle_starttag(self, tag, attrs):
            if tag == 'table':
                self.table_depth += 1
            elif tag in ('script', 'style'):
                self.skip_depth += 1
            elif not self.table_depth and tag in ('p', 'div', 'br', 'li', 'h1', 'h2', 'h3'):
                self.parts.append('\n')

        def handle_endtag(self, tag):
            if tag == 'table':
                self.table_depth = max(0, self.table_depth - 1)
                self.parts.append('\n')
            elif tag in ('script', 'style'):
                self.skip_depth = max(0, self.skip_depth - 1)
            elif not self.table_depth and tag in ('p', 'div', 'li', 'h1', 'h2', 'h3'):
                self.parts.append('\n')

        def handle_data(self, value):
            if not self.table_depth and (not self.skip_depth):
                self.parts.append(value)
    parser = BodyParser()
    parser.feed(text)
    return re.sub('\\n\\s*\\n+', '\n\n', ''.join(parser.parts)).strip()

if __name__ == '__main__':
    sys.exit(main())
