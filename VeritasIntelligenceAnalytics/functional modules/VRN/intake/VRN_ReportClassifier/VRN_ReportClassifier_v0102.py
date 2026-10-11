#!/usr/bin/env python3
"""VRN four-category classifier. Read-only inputs; evidence-backed routing.
薄尾 v0102(VRN 2026-10-10):檔頭改接正本加速器 VeritasCeleritas_v1141 / 正本網路工具 VeritasAegisNexus_v1652(v0101 是舊橋)(找不到加速器 = 不改任何行為);規則 · Regex · 權重 · 讀取與輸出全與 v0100 相同。"""
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
PARAMS = {
    'engine': 'VRN_ReportClassifier', 'version': 'v0102', 'schema_version': '1.0',
    'max_pdf_pages': 3, 'min_text_chars': 80, 'max_text_chars': 24000,
    'front_chars': 12000, 'header_ratio': 0.42, 'text_header_lines': 16,
    'evidence_chars': 180, 'block_chars': 1600, 'filename_rule_weight': 3,
    'ticker_front_weight': 4, 'ticker_filename_weight': 2, 'valuation_weight': 4, 'financial_weight': 1,
    'news_metadata_weight': 12, 'confidence_base': .60, 'confidence_score_factor': .02,
    'confidence_margin_factor': .005, 'confidence_max': .97,
    'review_confidence_max': .49, 'review_confidence_factor': .025,
    'accept_score': 7, 'accept_margin': 3, 'max_input_mb': 80,
    'max_files': 1000, 'recursive': False, 'supported': ['.pdf', '.txt', '.json'],
    'csv_encoding': 'utf-8-sig',
    'labels': {'SINGLE_STOCK': '個股報告', 'INDUSTRY': '產業報告／展望',
               'OTHER_INVESTMENT': '其他投資報告', 'NEWS': '新聞'},
    'routes': {'SINGLE_STOCK': 'STOCK_REPORT_PIPELINE', 'INDUSTRY': 'INDUSTRY_PIPELINE',
               'OTHER_INVESTMENT': 'INVESTMENT_TOPIC_PIPELINE', 'NEWS': 'NEWS_PIPELINE'},
    'rules': [
        {'id': 'C001', 'category': 'SINGLE_STOCK', 'weight': 8,
         'pattern': r'個股報告|公司研究|公司訪談報告|company\s+(?:research|update|report)|equity\s+update'},
        {'id': 'I001', 'category': 'INDUSTRY', 'weight': 9,
         'pattern': r'產業(?:專題|報告|展望|研究)|行業(?:研究|展望)|(?:industry|sector)\s+(?:outlook|report|review|research)|^[^\n]{1,18}產業\s*$'},
        {'id': 'O001', 'category': 'OTHER_INVESTMENT', 'weight': 9,
         'pattern': r'總經(?:評析|報告|展望)|宏觀(?:研究|報告)|盤勢分析|資產配置|投資策略|債券ETF周報|債券(?:週報|周報|展望)|(?:macro|strategy|asset allocation)\s*(?:outlook|report|research)|ETF\s+(?:weekly|outlook)'},
        {'id': 'O002', 'category': 'OTHER_INVESTMENT', 'weight': 10,
         'pattern': r'晨\s*會\s*報\s*告|morning\s+(?:briefing|meeting|report)|daily\s+brief'},
        {'id': 'N003', 'category': 'NEWS', 'weight': 9,
         'pattern': r'^記者[^\n]{1,24}[/／][^\n]{0,24}報導'},
        {'id': 'N001', 'category': 'NEWS', 'weight': 9,
         'pattern': r'^(?:新聞(?:稿|快訊|報導)?|即時新聞|news\s*(?:article|report|release)|press\s+release)(?:\s|[:：|]|$)'},
    ],
    'valuation_pattern': r'目標價|投資評等|未評等|price\s*target|target\s*price|stock\s*rating|\b(?:overweight|outperform|underweight|underperform)\b',
    'financial_pattern': r'\bEPS\b|每股盈餘|每股淨利|營收|revenue|earnings',
    'ticker_patterns': [r'(?<![\w])([1-9]\d{3})\s*(?:\.TW(?:O)?\b|TT\b)',
                        r'[\u3400-\u9fffA-Za-z][\u3400-\u9fffA-Za-z\- ]{0,24}\(\s*([1-9]\d{3})(?:\s*[,，)]|\s+TT)'],
    'filename_ticker_pattern': r'(?:^|[\s_\-])([1-9]\d{3})(?=[\s_\-(]|$)|\(\s*([1-9]\d{3})(?=[,，)])',
    'date_year_min': 1900, 'date_year_max': 2099,
}
import argparse
import copy
import csv
import hashlib
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path


def def_normalize(value):
    """NFKC + trim, retain line boundaries for heading evidence."""
    value = unicodedata.normalize('NFKC', str(value or '')).replace('\x00', '')
    return '\n'.join(re.sub(r'[^\S\n]+', ' ', line).strip() for line in value.splitlines()).strip()


def def_hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def def_policy_hash():
    return hashlib.sha256(json.dumps(PARAMS, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def def_implementation_hash():
    return def_hash(Path(__file__))


def def_read_document(path):
    """Bounded native reading; OCR is requested as a next action, never fabricated."""
    path = Path(path)
    if path.stat().st_size > PARAMS['max_input_mb'] * 1024 * 1024:
        raise ValueError('INPUT_TOO_LARGE')
    suffix = path.suffix.lower()
    warnings, readers, blocks, metadata = [], [], [], {}
    page_count = None
    if suffix == '.pdf':
        import fitz
        texts, headings = [], []
        with fitz.open(path) as document:
            if document.needs_pass:
                raise ValueError('ENCRYPTED_PDF')
            page_count = len(document)
            for index in range(min(page_count, PARAMS['max_pdf_pages'])):
                page = document[index]
                text = page.get_text('text', sort=True)
                texts.append(text)
                if index == 0:
                    for block in page.get_text('blocks', sort=True):
                        blocks.append({'page': 1, 'bbox': list(block[:4]), 'text': def_normalize(block[4])[:PARAMS['block_chars']]})
                        if block[1] <= page.rect.height * PARAMS['header_ratio']:
                            headings.append(block[4])
        readers.append('PyMuPDF')
        front = texts[0] if texts else ''
        if len(re.sub(r'\s', '', front)) < PARAMS['min_text_chars']:
            import pdfplumber
            with pdfplumber.open(path) as document:
                alternate = [page.extract_text() or '' for page in document.pages[:PARAMS['max_pdf_pages']]]
            readers.append('pdfplumber_fallback')
            if len(''.join(alternate)) > len(''.join(texts)):
                texts, front = alternate, alternate[0] if alternate else ''
                warnings.append('FALLBACK_TEXT_WITHOUT_LAYOUT_COORDINATES')
        body = '\n'.join(texts)
        header = '\n'.join(headings)
        title = ''
    elif suffix in ('.txt', '.json'):
        # Read once, strict encoding; no silent replacement of undecodable bytes.
        data = path.read_text(encoding='utf-8-sig')
        if suffix == '.json':
            metadata = json.loads(data)
            if not isinstance(metadata, dict) or not isinstance(metadata.get('text'), str):
                raise ValueError('JSON_REQUIRES_OBJECT_WITH_STRING_TEXT')
            for key in ('title', 'source_kind', 'source_name', 'published_at', 'url'):
                if key in metadata and not isinstance(metadata[key], str):
                    raise ValueError('JSON_METADATA_MUST_BE_STRING: ' + key)
            body = metadata['text']
            title = metadata.get('title', '')
        else:
            body, title = data, ''
        front = body[:PARAMS['front_chars']]
        header = '\n'.join(front.splitlines()[:PARAMS['text_header_lines']])
        readers.append('UTF8_TEXT' if suffix == '.txt' else 'STRUCTURED_JSON')
    else:
        raise ValueError('UNSUPPORTED_FORMAT')
    return {'filename': path.name, 'title': def_normalize(title),
            'header': def_normalize(header), 'front': def_normalize(front)[:PARAMS['front_chars']],
            'text': def_normalize(body)[:PARAMS['max_text_chars']], 'metadata': metadata,
            'blocks': blocks, 'reader': readers, 'warnings': warnings,
            'page_count': page_count, 'pages_read': min(page_count, PARAMS['max_pdf_pages']) if page_count is not None else None}


def def_tickers(text, filename=False):
    hits = []
    patterns = [PARAMS['filename_ticker_pattern']] if filename else PARAMS['ticker_patterns']
    for pattern in patterns:
        for match in re.finditer(pattern, def_normalize(text), re.I):
            ticker = next(x for x in match.groups() if x)
            # Bare years in filenames are not ticker evidence. Explicit .TW / TT remains valid.
            if filename and PARAMS['date_year_min'] <= int(ticker) <= PARAMS['date_year_max']:
                continue
            if ticker not in hits:
                hits.append(ticker)
    return hits


def def_add_evidence(evidence, scores, category, rule, weight, field, match, document):
    item = {'rule_id': rule, 'category': category, 'weight': weight, 'field': field,
            'matched_text': match[:PARAMS['evidence_chars']], 'page': 1 if field in ('header', 'front') and document.get('page_count') else None,
            'bbox': None}
    if item['page']:
        block = next((x for x in document.get('blocks', []) if match.casefold() in x['text'].casefold()), None)
        if block:
            item['bbox'] = block['bbox']
    evidence.append(item)
    scores[category] += weight


def def_classify(document):
    """Pure deterministic classification; scores are rules, not calibrated probabilities."""
    doc = {**document}
    for key in ('filename', 'title', 'header', 'front', 'text'):
        doc[key] = def_normalize(doc.get(key, ''))
    scores = {category: 0 for category in PARAMS['labels']}
    evidence, strong = [], set()
    for rule in PARAMS['rules']:
        # Each rule contributes once; content has priority over the weaker filename signal.
        for field in ('title', 'header', 'filename'):
            found = re.search(rule['pattern'], doc[field], re.I | re.M)
            if found:
                weight = min(PARAMS['filename_rule_weight'], rule['weight']) if field == 'filename' else rule['weight']
                def_add_evidence(evidence, scores, rule['category'], rule['id'], weight, field, found.group(), doc)
                if field != 'filename':
                    strong.add(rule['category'])
                break
    filename_tickers = def_tickers(doc['filename'], True)
    front_tickers = def_tickers(doc['front'])
    body_tickers = def_tickers(doc['text'])
    primary = filename_tickers[0] if len(filename_tickers) == 1 else front_tickers[0] if len(front_tickers) == 1 else None
    if primary:
        in_front = primary in front_tickers
        def_add_evidence(evidence, scores, 'SINGLE_STOCK', 'C002', PARAMS['ticker_front_weight'] if in_front else PARAMS['ticker_filename_weight'],
                         'front' if in_front else 'filename', primary, doc)
    valuation = re.search(PARAMS['valuation_pattern'], doc['front'], re.I)
    if valuation and primary:
        def_add_evidence(evidence, scores, 'SINGLE_STOCK', 'C003', PARAMS['valuation_weight'], 'front', valuation.group(), doc)
    financial = re.search(PARAMS['financial_pattern'], doc['front'], re.I)
    if financial and primary:
        def_add_evidence(evidence, scores, 'SINGLE_STOCK', 'C004', PARAMS['financial_weight'], 'front', financial.group(), doc)
    if primary and primary in front_tickers and valuation:
        strong.add('SINGLE_STOCK')
    source_kind = doc.get('metadata', {}).get('source_kind', '').strip().upper()
    if source_kind == 'NEWS':
        def_add_evidence(evidence, scores, 'NEWS', 'N002', PARAMS['news_metadata_weight'], 'source_kind', 'NEWS', doc)
        strong.add('NEWS')
    warnings = list(doc.get('warnings', []))
    # Document-wide scope wins over incidental company valuation / peer comparison tables.
    explicit_scope = {e['category'] for e in evidence if e['rule_id'] in ('I001', 'O001', 'O002', 'N001', 'N002', 'N003') and e['field'] != 'filename'}
    explicit_company = any(e['rule_id'] == 'C001' and e['field'] != 'filename' for e in evidence)
    conflict = len(explicit_scope) > 1 or (explicit_company and bool(explicit_scope))
    if len(explicit_scope) == 1 and not conflict:
        candidate = next(iter(explicit_scope))
        if scores['SINGLE_STOCK'] and candidate != 'SINGLE_STOCK':
            warnings.append('DOCUMENT_SCOPE_OVERRIDES_COMPANY_MENTION')
    else:
        candidate = max(scores, key=scores.get) if any(scores.values()) else None
    second = max((value for key, value in scores.items() if key != candidate), default=0)
    margin = scores.get(candidate, 0) - second
    sufficient_text = len(re.sub(r'\s', '', doc['text'])) >= PARAMS['min_text_chars']
    reason = 'RULES_ACCEPTED'
    if not sufficient_text:
        reason = 'INSUFFICIENT_TEXT_NEEDS_OCR' if doc.get('page_count') is not None else 'INSUFFICIENT_TEXT'
    elif conflict:
        reason = 'CONFLICTING_DOCUMENT_SCOPES'
    elif candidate not in strong or scores.get(candidate, 0) < PARAMS['accept_score']:
        reason = 'INSUFFICIENT_CLASSIFICATION_EVIDENCE'
    elif not explicit_scope and margin < PARAMS['accept_margin']:
        reason = 'LOW_SCORE_MARGIN'
    accepted = reason == 'RULES_ACCEPTED'
    category = candidate if accepted else None
    subtype = 'COMPANY_RESEARCH' if category == 'SINGLE_STOCK' else 'INDUSTRY_OUTLOOK' if category == 'INDUSTRY' else 'NEWS_ARTICLE' if category == 'NEWS' else None
    if category == 'OTHER_INVESTMENT':
        subtype = 'MULTI_COMPANY_BRIEFING' if any(e['rule_id'] == 'O002' for e in evidence) else 'INVESTMENT_TOPIC'
    score = scores.get(candidate, 0)
    confidence = round(min(PARAMS['confidence_max'], PARAMS['confidence_base'] + score * PARAMS['confidence_score_factor'] + max(0, margin) * PARAMS['confidence_margin_factor']), 3) if accepted else min(PARAMS['review_confidence_max'], round(score * PARAMS['review_confidence_factor'], 3))
    return {'category': category, 'category_label': PARAMS['labels'].get(category, '待分類'),
            'candidate_category': candidate, 'subtype': subtype, 'status': 'ACCEPTED' if accepted else 'REVIEW',
            'reason': reason, 'confidence': confidence, 'confidence_kind': 'HEURISTIC_NOT_PROBABILITY',
            'scores': scores, 'margin': margin, 'evidence': evidence, 'warnings': warnings,
            'primary_ticker_candidate': primary if category == 'SINGLE_STOCK' else None,
            'related_ticker_candidates': list(dict.fromkeys(front_tickers + body_tickers)),
            'ticker_validation': 'NOT_VERIFIED_WITH_TWSE_TPEX',
            'needs_split': subtype == 'MULTI_COMPANY_BRIEFING',
            'suggested_pipeline': PARAMS['routes'].get(category),
            'dispatch_status': 'NOT_EXECUTED', 'next_action': 'HANDOFF' if accepted else 'OCR_REVIEW' if 'OCR' in reason else 'MANUAL_REVIEW',
            'reader': doc.get('reader', []), 'page_count': doc.get('page_count'), 'pages_read': doc.get('pages_read'),
            'text_chars': len(doc['text']), 'title': doc['title'],
            'source_name': doc.get('metadata', {}).get('source_name', ''),
            'published_at_raw': doc.get('metadata', {}).get('published_at', '')}


def def_collect_inputs(inputs, recursive=False):
    files = []
    for raw in inputs:
        path = Path(raw).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(str(path))
        candidates = sorted(path.rglob('*') if recursive else path.iterdir()) if path.is_dir() else [path]
        for candidate in candidates:
            if candidate.is_file() and candidate.suffix.lower() in PARAMS['supported'] and candidate not in files:
                files.append(candidate)
    if not files:
        raise ValueError('NO_SUPPORTED_INPUTS')
    if len(files) > PARAMS['max_files']:
        raise ValueError('TOO_MANY_INPUTS')
    return files


def def_export(rows, out):
    import polars as pl
    # Nested provenance stays lossless JSON in CSV / Parquet string columns.
    flat = [{key: json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (list, dict)) else value
             for key, value in row.items()} for row in rows]
    (out / 'ReportClassification.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    with (out / 'ReportClassification.csv').open('w', encoding=PARAMS['csv_encoding'], newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(flat[0]))
        writer.writeheader()
        writer.writerows(flat)
    pl.DataFrame(flat, infer_schema_length=None).write_parquet(out / 'ReportClassification.parquet')
    readback = pl.read_parquet(out / 'ReportClassification.parquet').to_dicts()
    if readback != flat:
        raise ValueError('PARQUET_READBACK_MISMATCH')
    with (out / 'ReportClassification.csv').open(encoding=PARAMS['csv_encoding'], newline='') as handle:
        csv_rows = list(csv.DictReader(handle))
    if csv_rows != [{key: '' if value is None else str(value) for key, value in row.items()} for row in flat]:
        raise ValueError('CSV_READBACK_MISMATCH')


def def_run(inputs, output, recursive=False, resume_from=None):
    import polars  # Fail before output processing if a required writer is unavailable.
    files = def_collect_inputs(inputs, recursive)
    out = Path(output).resolve()
    for raw in inputs:
        source = Path(raw).resolve()
        if source.is_dir() and (out == source or out.is_relative_to(source)):
            raise ValueError('OUTPUT_MUST_BE_OUTSIDE_INPUT_DIRECTORY')
    out.mkdir(parents=True, exist_ok=False)  # Append-only run directories.
    policy, implementation = def_policy_hash(), def_implementation_hash()
    cached = {}
    if resume_from:
        prior = json.loads(Path(resume_from).read_text(encoding='utf-8-sig'))
        if not isinstance(prior, list):
            raise ValueError('RESUME_REQUIRES_RESULT_ARRAY')
        for row in prior:
            if row.get('policy_sha256') == policy and row.get('implementation_sha256') == implementation and row.get('status') in ('ACCEPTED', 'REVIEW'):
                cached[(row['source_sha256'], row['filename'])] = row
    rows, seen = [], {}
    for index, path in enumerate(files, 1):
        digest = def_hash(path)
        base = {'engine': PARAMS['engine'], 'version': PARAMS['version'], 'schema_version': PARAMS['schema_version'],
                'policy_sha256': policy, 'implementation_sha256': implementation, 'filename': path.name,
                'source_path': str(path), 'source_sha256': digest, 'size_bytes': path.stat().st_size,
                'duplicate_of': seen.get(digest), 'reused': False}
        try:
            previous = cached.get((digest, path.name))
            result = copy.deepcopy(previous) if previous else def_classify(def_read_document(path))
            result.update(base)
            result['reused'] = bool(previous)
            result['error'] = None
        except Exception as exc:
            result = def_classify({'filename': path.name, 'text': ''})
            result.update(base)
            result.update({'status': 'ERROR', 'reason': 'READ_OR_CLASSIFICATION_ERROR', 'error': type(exc).__name__ + ': ' + str(exc), 'next_action': 'REPAIR_INPUT_OR_READER'})
        rows.append(result)
        seen.setdefault(digest, str(path))
        print(f'[{index}/{len(files)}] {result["status"]} {result["category_label"]}: {path.name}', file=sys.stderr)
    def_export(rows, out)
    errors = sum(row['status'] == 'ERROR' for row in rows)
    reviews = sum(row['status'] == 'REVIEW' for row in rows)
    receipt = {'engine': PARAMS['engine'], 'version': PARAMS['version'], 'completed_utc': datetime.now(timezone.utc).isoformat(),
               'status': 'FAIL' if errors else 'COMPLETED_WITH_REVIEW' if reviews else 'PASS',
               'files': len(rows), 'accepted': len(rows)-errors-reviews, 'review': reviews, 'errors': errors,
               'reused': sum(row['reused'] for row in rows),
               'categories': {key: sum(row['category'] == key for row in rows) for key in PARAMS['labels']},
               'format_readback': 'PASS', 'ocr': 'NOT_EXECUTED', 'downstream_dispatch': 'NOT_EXECUTED',
               'source_files_unchanged': all(def_hash(path) == row['source_sha256'] for path, row in zip(files, rows))}
    if not receipt['source_files_unchanged']:
        receipt['status'] = 'FAIL'
        errors += 1
    (out / 'RUN_STATUS.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    return receipt, 1 if errors else 2 if reviews else 0


def def_main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='VRN 四類報告分類；不執行下游擷取或 OCR')
    parser.add_argument('--input', nargs='+', required=True, help='PDF/TXT/JSON files or directories')
    parser.add_argument('--output', required=True, help='A new directory outside the input folders')
    parser.add_argument('--recursive', action='store_true', default=PARAMS['recursive'])
    parser.add_argument('--resume-from', help='Prior trusted ReportClassification.json, same engine and policy hashes')
    args = parser.parse_args()
    try:
        result, code = def_run(args.input, args.output, args.recursive, args.resume_from)
    except Exception as exc:
        result, code = {'status': 'FAIL', 'error': type(exc).__name__ + ': ' + str(exc)}, 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == '__main__':
    sys.exit(def_main())
