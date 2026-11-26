#!/usr/bin/env python3
"""SUP866 v0107: local L1 cleaning and optional review adapters; central numbering stays in VCGC."""
from __future__ import annotations
import argparse, datetime, decimal, functools, hashlib, importlib.util, importlib.metadata, json, os, sys, tempfile, unicodedata
from pathlib import Path
# ----- All operation limits / library identities / fixed extraction rules -----
HERE = Path(__file__).resolve().parent
PRIOR_PATH = HERE / 'SUP_MDL866_VIAUnifiedNLPOrchestrator_v0106.py'
BODY_PATH = HERE / 'SUP_MDL866_VIAUnifiedNLPOrchestrator_v0103.py'
REGISTRY = HERE.parent / 'registry'
ENGINE = 'SUP_MDL866_VIAUnifiedNLPOrchestrator_v0107'
MAX_ROWS = 1000
MAX_TEXT_CHARS = 32768
MAX_ALIASES = 50000
MAX_TERM_CHARS = 64
MAX_UNKNOWN_TERMS = 32
MAX_REVIEW_CHOICES = 256
MAX_INPUT_BYTES = 33554432
MAX_MODEL_BYTES = 134217728
MAX_VECTOR_WORDS = 100000
MAX_VECTOR_DIMS = 2048
MATCHER_CACHE_SIZE = 8
FUZZY_CUTOFF = 90.0
FUZZY_TIMEOUT_S = 0.02
TOP_K = 5
EXACT_BACKENDS = ('aho', 'flashtext', 'polars')
ROW_STATES = ('CLEAN_CANDIDATE', 'REVIEW', 'QUARANTINE', 'NODATA')
TOOL_MODULES = {'flashtext':'flashtext', 'google-re2':'re2', 'regex':'regex', 'pyahocorasick':'ahocorasick',
 'rapidfuzz':'rapidfuzz', 'jellyfish':'jellyfish', 'polyfuzz':'polyfuzz', 'recordlinkage':'recordlinkage',
 'spacy':'spacy', 'gensim':'gensim', 'fasttext-wheel':'fasttext', 'nltk':'nltk', 'polars':'polars',
 'duckdb':'duckdb', 'pydantic':'pydantic', 'pandera':'pandera'}
EXTRACTION_PATTERNS = {
 'date': r'[0-9]{4}[-/][0-9]{1,2}[-/][0-9]{1,2}',
 'ticker': r'(?i)[A-Za-z0-9]+\.(?:TWO|TW)',
 'percent': r'[+-]?[0-9]+(?:\.[0-9]+)?\s*%',
 'money': r'(?i)(?:NT\$|US\$|TWD|USD)\s*[0-9][0-9,.]*'}
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
# ===== [VIA:ACCEL-BRIDGE:END]

# ----- Existing APIs remain delegated; only L1 commands are additive -----
@functools.lru_cache(maxsize=3)
def load_prior(path=PRIOR_PATH):
    spec = importlib.util.spec_from_file_location('via_nlp_' + Path(path).stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def __getattr__(name):
    prior = load_prior()
    return getattr(prior, name) if hasattr(prior, name) else getattr(load_prior(BODY_PATH), name)


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def norm(value):
    return unicodedata.normalize('NFKC', value).strip().casefold()


# ----- Pydantic input and Pandera/Polars output contracts -----
@functools.lru_cache(maxsize=1)
def input_model():
    from pydantic import ConfigDict, create_model, field_validator
    def nonempty(value):
        if not value.strip():
            raise ValueError('EMPTY_ID_OR_SCOPE')
        return value
    validators = {'nonempty': field_validator('record_id', 'source_id', 'scope')(nonempty)}
    return create_model('L1Input', __config__=ConfigDict(strict=True, extra='forbid'),
        __validators__=validators, record_id=(str, ...), source_id=(str, ...), scope=(str, ...), text=(str | None, ...))


def validate_frame(rows):
    import polars as pl
    import pandera.polars as pa
    columns = ['record_id', 'source_id', 'scope', 'normalized_text', 'canonical_text', 'status', 'ssot_code']
    frame = pl.DataFrame([{k: row[k] for k in columns} for row in rows], schema={k: pl.String for k in columns})
    schema = pa.DataFrameSchema({k: pa.Column(pl.String, nullable=k in ('normalized_text', 'canonical_text', 'ssot_code'),
        checks=pa.Check.isin(ROW_STATES) if k == 'status' else None) for k in columns}, strict=True, coerce=False)
    schema.validate(frame, lazy=True)
    if not frame['ssot_code'].is_null().all():
        raise ValueError('L1_CANNOT_ISSUE_SSOT')
    return frame


# ----- Central approved synonym projection; no independent identity dictionary -----
def central_alias_rows(registry=REGISTRY):
    book = json.loads((Path(registry) / 'VIA_Numbering_SSOT_v0100.json').read_text(encoding='utf-8'))
    rows = []
    for item in book.get('rows', {}).get('SYN', []):
        category = str(item.get('cat', ''))
        if not category.startswith('中央同義冊/') or item.get('lamp') != 'GREEN' or item.get('gone_since'):
            continue
        scope = category.split('/', 1)[1]
        target = item.get('alias_of') or item['name']
        for word in item.get('words', []):
            if isinstance(word, str) and word.strip() and not norm(word).isdigit():
                rows.append({'scope': scope, 'term': word, 'canonical': target, 'rule_code': item['code']})
    if len(rows) > MAX_ALIASES:
        raise ValueError('ALIAS_LIMIT')
    return rows


def alias_table(rows, scope):
    table, conflicts = {}, {}
    for row in rows:
        if row['scope'] != scope:
            continue
        term = norm(row['term'])
        if not term or len(term) > MAX_TERM_CHARS:
            continue
        prior = table.get(term)
        if prior and norm(prior['canonical']) != norm(row['canonical']):
            conflicts.setdefault(term, {prior['canonical']}).add(row['canonical'])
        else:
            table[term] = {'canonical': row['canonical'], 'rule_code': row['rule_code']}
    for term in conflicts:
        table.pop(term, None)
    return table, {term: sorted(values) for term, values in conflicts.items()}


def ascii_word(char):
    return bool(char) and char.isascii() and (char.isalnum() or char == '_')


def token_boundary(text, start, end):
    return not ((start > 0 and ascii_word(text[start - 1]) and ascii_word(text[start])) or
                (end < len(text) and ascii_word(text[end - 1]) and ascii_word(text[end])))


@functools.lru_cache(maxsize=MATCHER_CACHE_SIZE)
def matcher(backend, terms):
    if backend == 'aho':
        import ahocorasick
        obj = ahocorasick.Automaton()
        for term in terms:
            obj.add_word(term, term)
        if terms:
            obj.make_automaton()
        return obj
    if backend == 'flashtext':
        from flashtext import KeywordProcessor
        obj = KeywordProcessor(case_sensitive=True)
        for term in terms:
            obj.add_keyword(term, term)
        return obj
    if backend == 'polars':
        return terms
    raise ValueError('UNKNOWN_EXACT_BACKEND')


def exact_matches(text, table, backend='aho'):
    terms = tuple(sorted(table, key=lambda s: (-len(s), s)))
    if not terms:
        return []
    obj = matcher(backend, terms)
    if backend == 'aho':
        found = [(end - len(term) + 1, end + 1, term) for end, term in obj.iter(text)]
    elif backend == 'flashtext':
        found = [(start, end, term) for term, start, end in obj.extract_keywords(text, span_info=True)]
    else:
        import polars as pl
        series = pl.Series([text])
        words = series.str.extract_many(terms, overlapping=True).to_list()[0]
        positions = series.str.find_many(terms, overlapping=True).to_list()[0]
        raw = text.encode('utf-8')
        found = []
        for pos, word in zip(positions, words):
            if raw[pos:pos + len(word.encode())] != word.encode():
                raise ValueError('POLARS_MATCH_ALIGNMENT')
            start = len(raw[:pos].decode('utf-8'))
            found.append((start, start + len(word), word))
    accepted, last = [], -1
    for start, end, term in sorted(found, key=lambda row: (row[0], -(row[1] - row[0]), row[2])):
        if start >= last and token_boundary(text, start, end):
            accepted.append({'start': start, 'end': end, 'term': term, **table[term], 'span_basis': 'normalized_text'})
            last = end
    return accepted


def replace_spans(text, matches):
    chunks, cursor = [], 0
    for match in matches:
        chunks.extend([text[cursor:match['start']], match['canonical']])
        cursor = match['end']
    return ''.join(chunks) + text[cursor:]


def normalize_fields(values, aliases):
    """Exact-field Polars conversion: no substring entity resolution."""
    import polars as pl
    mapping = {}
    for term, target in aliases.items():
        key = norm(term)
        if key in mapping and mapping[key] != target:
            raise ValueError('AMBIGUOUS_ALIAS')
        mapping[key] = target
    return pl.Series([norm(x) if x is not None else None for x in values], dtype=pl.String).replace_strict(mapping, default=None).to_list()


# ----- RE2 extraction plus calendar/number validation; no PCRE assumption -----
@functools.lru_cache(maxsize=1)
def extractors():
    import re2
    return {kind: re2.compile(pattern) for kind, pattern in EXTRACTION_PATTERNS.items()}


def regex_hits(text, kind, backend):
    if backend == 're2':
        return [(m.start(), m.end(), m.group()) for m in extractors()[kind].finditer(text)]
    if backend != 'duckdb':
        raise ValueError('REGEX_BACKEND')
    import duckdb
    with duckdb.connect(':memory:', config={'enable_external_access': False}) as connection:
        values = connection.execute('SELECT regexp_extract_all(?, ?)', [text, EXTRACTION_PATTERNS[kind]]).fetchone()[0]
    hits, cursor = [], 0
    for value in values:
        start = text.find(value, cursor)
        if start < 0:
            raise ValueError('DUCKDB_MATCH_ALIGNMENT')
        cursor = start + len(value)
        hits.append((start, cursor, value))
    return hits


def extract_values(text, backend='re2'):
    import re2
    values, errors = [], []
    for kind in EXTRACTION_PATTERNS:
        for start, end, raw in regex_hits(text, kind, backend):
            if not token_boundary(text, start, end):
                continue
            try:
                if kind == 'date':
                    value = datetime.date(*[int(x) for x in raw.replace('/', '-').split('-')]).isoformat()
                elif kind == 'ticker':
                    value = raw.upper()
                    if not re2.fullmatch(r'[1-9][0-9]{3}\.(?:TW|TWO)', value):
                        raise ValueError('NOT_ORDINARY_STOCK_TICKER')
                elif kind == 'percent':
                    value = str(decimal.Decimal(raw.replace('%', '').strip()) / 100)
                else:
                    currency = re2.match(r'(?i)(nt\$|us\$|twd|usd)', raw).group().lower()
                    number = raw[len(currency):].strip()
                    if not re2.fullmatch(r'(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]+)?', number):
                        raise ValueError('INVALID_GROUPED_AMOUNT')
                    value = {'currency': 'TWD' if currency in ('nt$', 'twd') else 'USD',
                             'amount': str(decimal.Decimal(number.replace(',', '')))}
                values.append({'kind': kind, 'raw': raw, 'value': value, 'start': start, 'end': end,
                               'span_basis': 'normalized_text', 'state': 'CANDIDATE_NOT_VERIFIED'})
            except (ValueError, decimal.InvalidOperation) as exc:
                errors.append({'kind': kind, 'raw': raw, 'reason': str(exc)})
    return values, errors


# ----- Fuzzy / clustering / multi-field lanes only produce review proposals -----
def fuzzy_candidates(term, table, cutoff=FUZZY_CUTOFF):
    from rapidfuzz import fuzz, process
    if len(term) > MAX_TERM_CHARS or not term:
        return []
    matches = process.extract(norm(term), list(table), scorer=fuzz.ratio, limit=TOP_K, score_cutoff=cutoff)
    return [{'term': term, 'matched_alias': word, 'canonical': table[word]['canonical'], 'score': float(score),
             'backend': 'RapidFuzz.ratio', 'state': 'REVIEW_ONLY', 'ssot_code': None, 'auto_apply': False}
            for word, score, _ in matches]


def fuzzy_regex_candidates(term, choices):
    import regex
    if len(term) > MAX_TERM_CHARS or len(choices) > MAX_REVIEW_CHOICES:
        raise ValueError('FUZZY_REGEX_LIMIT')
    rows = []
    for choice in choices:
        if len(choice) > MAX_TERM_CHARS:
            continue
        try:
            match = regex.fullmatch('(?:' + regex.escape(norm(choice)) + '){e<=1}', norm(term), timeout=FUZZY_TIMEOUT_S)
            if match:
                rows.append({'term': term, 'candidate': choice, 'edits': list(match.fuzzy_counts), 'state': 'REVIEW_ONLY'})
        except TimeoutError:
            rows.append({'term': term, 'candidate': choice, 'state': 'TIMEOUT'})
    return rows


def phonetic_candidates(term, choices):
    import jellyfish
    if len(choices) > MAX_REVIEW_CHOICES:
        raise ValueError('REVIEW_LIMIT')
    english = term.isascii() and term.isalpha()
    rows = []
    for choice in choices:
        row = {'candidate': choice, 'jaro_winkler': jellyfish.jaro_winkler_similarity(norm(term), norm(choice)),
               'soundex_equal': None, 'state': 'REVIEW_ONLY'}
        if english and choice.isascii() and choice.isalpha():
            row['soundex_equal'] = jellyfish.soundex(term) == jellyfish.soundex(choice)
        rows.append(row)
    return sorted(rows, key=lambda x: -x['jaro_winkler'])[:TOP_K]


def cluster_candidates(terms, choices):
    if len(terms) > MAX_REVIEW_CHOICES or len(choices) > MAX_REVIEW_CHOICES:
        raise ValueError('CLUSTER_LIMIT')
    from polyfuzz import PolyFuzz
    from polyfuzz.models import TFIDF
    if not terms or not choices:
        return []
    model = PolyFuzz(TFIDF(n_gram_range=(2, 3), min_similarity=0.0))
    model.match(terms, choices)
    return [{**row, 'state': 'REVIEW_ONLY', 'auto_apply': False} for row in model.get_matches().to_dict('records')]


def link_records(left, right):
    import pandas as pd
    import recordlinkage
    if len(left) > MAX_REVIEW_CHOICES or len(right) > MAX_REVIEW_CHOICES:
        raise ValueError('LINK_LIMIT')
    for rows in (left, right):
        if any(set(x) != {'id', 'market', 'name'} or not all(isinstance(v, str) and v.strip() for v in x.values()) for x in rows):
            raise ValueError('LINK_SCHEMA')
        if len({x['id'] for x in rows}) != len(rows):
            raise ValueError('LINK_DUPLICATE_ID')
    if not left or not right:
        return []
    a, b = pd.DataFrame(left).set_index('id'), pd.DataFrame(right).set_index('id')
    index = recordlinkage.Index(); index.block('market')
    pairs = index.index(a, b)
    compare = recordlinkage.Compare(); compare.string('name', 'name', method='jarowinkler', label='name_score')
    scores = compare.compute(pairs, a, b)
    return [{'left': str(i), 'right': str(j), 'score': float(row['name_score']), 'state': 'REVIEW_ONLY', 'auto_apply': False}
            for (i, j), row in scores.iterrows()]


# ----- Offline NLP resource adapters; semantics never establish identity -----
def lemma_candidates(text, lookup):
    import spacy
    from spacy.lookups import Lookups
    nlp = spacy.blank('en')
    pipe = nlp.add_pipe('lemmatizer', config={'mode': 'lookup'})
    tables = Lookups(); tables.add_table('lemma_lookup', lookup); pipe.initialize(lookups=tables)
    return [{'text': tok.text, 'lemma': tok.lemma_, 'state': 'LEXICAL_LOOKUP_ONLY'} for tok in nlp(text)]


def vector_candidates(word, resource, expected_sha256, backend='gensim'):
    resource = Path(resource)
    if not resource.is_file():
        return {'state': 'RESOURCE_MISSING', 'candidates': []}
    if resource.stat().st_size > MAX_MODEL_BYTES or file_hash(resource) != expected_sha256:
        return {'state': 'RESOURCE_REJECTED', 'candidates': []}
    if backend == 'gensim':
        from gensim.models import KeyedVectors
        import numpy as np
        data = json.loads(resource.read_text(encoding='utf-8'))  # No untrusted pickle loads.
        if set(data) != {'words', 'vectors'} or not data['words'] or len(data['words']) > MAX_VECTOR_WORDS:
            raise ValueError('VECTOR_SCHEMA')
        values = np.asarray(data['vectors'], dtype=np.float32)
        if values.ndim != 2 or len(values) != len(data['words']) or values.shape[1] > MAX_VECTOR_DIMS or not np.isfinite(values).all():
            raise ValueError('VECTOR_SHAPE')
        if values.shape[1] == 0 or any(not isinstance(x, str) or not x for x in data['words']) or len(set(data['words'])) != len(data['words']) or not (np.linalg.norm(values, axis=1) > 0).all():
            raise ValueError('VECTOR_WORDS_OR_ZERO_VECTOR')
        model = KeyedVectors(vector_size=values.shape[1]); model.add_vectors(data['words'], values)
        candidates = model.most_similar(word, topn=min(TOP_K, len(data['words']) - 1)) if word in model else []
    elif backend == 'fasttext':
        import fasttext
        model = fasttext.load_model(str(resource))
        candidates = [(name, score) for score, name in model.get_nearest_neighbors(word, k=TOP_K)]
    else:
        raise ValueError('VECTOR_BACKEND')
    return {'state': 'REVIEW_ONLY', 'candidates': [{'term': name, 'similarity': float(score), 'auto_apply': False}
                                                 for name, score in candidates]}


def wordnet_candidates(word, corpus_dir=None):
    from nltk.corpus.reader import WordNetCorpusReader
    if corpus_dir is None or not Path(corpus_dir, 'index.noun').is_file():
        return {'state': 'RESOURCE_MISSING', 'candidates': []}
    corpus = WordNetCorpusReader(str(corpus_dir), None)
    words = sorted({lemma.name() for synset in corpus.synsets(word) for lemma in synset.lemmas()})
    return {'state': 'REVIEW_ONLY', 'candidates': words[:MAX_REVIEW_CHOICES], 'auto_apply': False}


# ----- Bounded hot path: preserve source text and identifiers -----
def clean_batch(records, aliases, backend='aho', fuzzy=True, regex_backend='re2'):
    import polars as pl
    import re2
    from pydantic import ValidationError
    if not isinstance(records, list) or len(records) > MAX_ROWS or len(aliases) > MAX_ALIASES:
        raise ValueError('BATCH_LIMIT')
    if backend not in EXACT_BACKENDS:
        raise ValueError('BACKEND')
    checked, bad, seen = [], [], {}
    for index, raw in enumerate(records):
        try:
            row = input_model().model_validate(raw).model_dump()
            if row['text'] is not None and len(row['text']) > MAX_TEXT_CHARS:
                raise ValueError('TEXT_LIMIT')
            key = (row['source_id'], row['record_id'])
            sha = digest(row)
            if key in seen:
                if seen[key]['input_sha256'] != sha:
                    seen[key]['errors'].append({'reason': 'SOURCE_RECORD_ID_COLLISION'})
                    bad.append({'index': index, 'reason': 'SOURCE_RECORD_ID_COLLISION', 'input_sha256': sha})
                else:
                    seen[key]['input_indexes'].append(index)
                continue
            row.update({'input_indexes': [index], 'input_sha256': sha, 'errors': []})
            checked.append(row); seen[key] = row
        except (ValidationError, ValueError, TypeError) as exc:
            bad.append({'index': index, 'reason': str(exc), 'input_sha256': digest(raw)})
    texts = pl.Series([x['text'] for x in checked], dtype=pl.String).str.normalize('NFKC').str.strip_chars().to_list()
    output, scopes = [], {}
    for row, text in zip(checked, texts):
        normalized = text.casefold() if text is not None else None
        if row['scope'] not in scopes:
            scopes[row['scope']] = alias_table(aliases, row['scope'])
        table, conflicts = scopes[row['scope']]
        matches, extractions, proposals = [], [], []
        errors = list(row['errors'])
        if normalized:
            matches = exact_matches(normalized, table, backend)
            extractions, extraction_errors = extract_values(normalized, regex_backend)
            errors.extend(extraction_errors)
            for term, targets in conflicts.items():
                if term in normalized:
                    errors.append({'reason': 'AMBIGUOUS_CENTRAL_ALIAS', 'term': term, 'targets': targets})
            if fuzzy:
                terms = re2.findall(r'[A-Za-z][A-Za-z0-9._-]{1,63}|[\p{Han}]{2,16}', normalized)
                for term in list(dict.fromkeys(terms))[:MAX_UNKNOWN_TERMS]:
                    if term not in table:
                        proposals.extend(fuzzy_candidates(term, table))
        status = 'QUARANTINE' if errors else 'REVIEW' if proposals else 'NODATA' if not normalized else 'CLEAN_CANDIDATE'
        output.append({**row, 'original_text': row['text'], 'normalized_text': normalized,
            'canonical_text': replace_spans(normalized, matches) if normalized is not None else None,
            'exact_matches': matches, 'extractions': extractions, 'review_candidates': proposals,
            'errors': errors, 'status': status, 'ssot_code': None})
    validate_frame(output)
    return {'engine': ENGINE, 'state': 'PARTIAL' if bad or any(x['status'] == 'QUARANTINE' for x in output) else 'CANDIDATE',
            'backend': backend, 'regex_backend': regex_backend, 'source_count': len(records), 'deduplicated_rows': len(output),
            'rules_sha256': digest(aliases), 'rows': output, 'quarantine': bad,
            'registration': 'VCGC_CONFLICT_CHECK_REQUIRED', 'network_used': False}


# ----- Deterministic dual export / verified resume -----
def export_batch(result, folder):
    import polars as pl
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    names = {'parquet': folder / 'L1_Normalized.parquet', 'csv': folder / 'L1_Normalized.csv'}
    manifest_path = folder / 'L1_Manifest.json'; request_hash = digest(result)
    if manifest_path.exists():
        try:
            old = json.loads(manifest_path.read_text(encoding='utf-8'))
        except (ValueError, UnicodeError):
            old = {}
        if isinstance(old, dict) and isinstance(old.get('files'), dict) and old.get('request_sha256') == request_hash and all(p.is_file() and file_hash(p) == old['files'].get(k) for k, p in names.items()):
            return {'state': 'REUSED', 'manifest': str(manifest_path)}
    columns = ['record_id', 'source_id', 'scope', 'original_text', 'normalized_text', 'canonical_text', 'status', 'ssot_code']
    rows = [{**{k: x[k] for k in columns}, 'evidence_json': json.dumps(x, ensure_ascii=False, sort_keys=True)} for x in result['rows']]
    frame = pl.DataFrame(rows, schema={k: pl.String for k in columns + ['evidence_json']})
    temp_paths = []
    try:
        for kind, path in names.items():
            fd, temp = tempfile.mkstemp(prefix='l1_', dir=folder); os.close(fd); temp = Path(temp); temp_paths.append(temp)
            if kind == 'parquet':
                frame.write_parquet(temp)
            else:
                safe = frame.with_columns([pl.when(pl.col(k).str.starts_with('=') | pl.col(k).str.starts_with('+') |
                    pl.col(k).str.starts_with('-') | pl.col(k).str.starts_with('@')).then(pl.lit("'") + pl.col(k)).otherwise(pl.col(k)).alias(k)
                    for k in columns])
                temp.write_text(safe.write_csv(), encoding='utf-8-sig')
            os.replace(temp, path)
        manifest = {'engine': ENGINE, 'request_sha256': request_hash, 'files': {k: file_hash(p) for k, p in names.items()},
                    'csv_spreadsheet_formula_neutralization': True, 'registration': 'NOT_REQUESTED'}
        fd, temp = tempfile.mkstemp(prefix='l1_manifest_', dir=folder); os.close(fd); temp = Path(temp); temp_paths.append(temp)
        temp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)); os.replace(temp, manifest_path)
    finally:
        for path in temp_paths:
            path.unlink(missing_ok=True)
    return {'state': 'WRITTEN', 'manifest': str(manifest_path)}


def tool_inventory():
    rows = []
    for distribution, module in TOOL_MODULES.items():
        try:
            version = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            version = None
        rows.append({'distribution': distribution, 'module': module, 'version': version,
                     'state': 'AVAILABLE_NOT_ACTIVATION_PROOF' if version else 'ABSENT'})
    return rows


def read_json(path):
    path = Path(path)
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError('FILE_SIZE_LIMIT')
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main(argv=None):
    """L1 verbs; legacy --brief / -Brief and pdf arguments delegate unchanged to v0106."""
    args = list(sys.argv[1:] if argv is None else argv)
    if os.environ.get('VIA_FROM_VCGC') != 'YES':
        print('[DENY] only VCGC entry'); return 2
    if args == ['--selftest']:
        return selftest()
    if args == ['l1-tools']:
        print(json.dumps(tool_inventory(), ensure_ascii=False, indent=2)); return 0
    if args[:1] == ['l1-clean']:
        parser = argparse.ArgumentParser(prog=ENGINE + ' l1-clean')
        parser.add_argument('--input', required=True); parser.add_argument('--out')
        parser.add_argument('--backend', choices=EXACT_BACKENDS, default='aho')
        parser.add_argument('--regex-backend', choices=('re2', 'duckdb'), default='re2')
        options = parser.parse_args(args[1:])
        result = clean_batch(read_json(options.input), central_alias_rows(), options.backend, regex_backend=options.regex_backend)
        if options.out:
            result['export'] = export_batch(result, options.out)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result['state'] == 'PARTIAL' else 0
    if args[:1] == ['l1-review']:
        parser = argparse.ArgumentParser(prog=ENGINE + ' l1-review')
        parser.add_argument('--input', required=True)
        options = parser.parse_args(args[1:]); request = read_json(options.input)
        result = review_request(request)
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 2 if result.get('state') == 'RESOURCE_MISSING' else 0
    prior_argv = sys.argv[:]
    try:
        sys.argv = [str(PRIOR_PATH), *args]
        return load_prior().main()
    finally:
        sys.argv = prior_argv


def review_request(request):
    fields = {'regex': {'term','choices'}, 'jellyfish': {'term','choices'}, 'polyfuzz': {'terms','choices'},
              'recordlinkage': {'left','right'}, 'spacy': {'text','lookup'},
              'gensim': {'term','path','sha256'}, 'fasttext': {'term','path','sha256'}, 'wordnet': {'term','corpus_dir'}}
    if not isinstance(request, dict) or request.get('lane') not in fields:
        raise ValueError('REVIEW_LANE')
    lane = request['lane']
    if set(request) - (fields[lane] | {'lane'}):
        raise ValueError('REVIEW_EXTRA_FIELDS')
    for key in ('term','text','path','sha256','corpus_dir'):
        if key in request and (not isinstance(request[key], str) or len(request[key]) > (MAX_TEXT_CHARS if key == 'text' else 4096 if key in ('path','corpus_dir') else MAX_TERM_CHARS)):
            raise ValueError('REVIEW_STRING_LIMIT')
    for key in ('terms','choices'):
        if key in request and (not isinstance(request[key], list) or len(request[key]) > MAX_REVIEW_CHOICES or any(not isinstance(x,str) or not x or len(x)>MAX_TERM_CHARS for x in request[key])):
            raise ValueError('REVIEW_CHOICES_LIMIT')
    if 'lookup' in request:
        lookup=request['lookup']
        if not isinstance(lookup,dict) or len(lookup)>MAX_REVIEW_CHOICES or any(not isinstance(x,str) or len(x)>MAX_TERM_CHARS for pair in lookup.items() for x in pair):
            raise ValueError('REVIEW_LOOKUP_LIMIT')
    if lane == 'regex':
        result = fuzzy_regex_candidates(request['term'], request['choices'])
    elif lane == 'jellyfish':
        result = phonetic_candidates(request['term'], request['choices'])
    elif lane == 'polyfuzz':
        result = cluster_candidates(request['terms'], request['choices'])
    elif lane == 'recordlinkage':
        result = link_records(request['left'], request['right'])
    elif lane == 'spacy':
        result = lemma_candidates(request['text'], request['lookup'])
    elif lane in ('gensim', 'fasttext'):
        return vector_candidates(request['term'], request['path'], request['sha256'], lane)
    elif lane == 'wordnet':
        return wordnet_candidates(request['term'], request.get('corpus_dir'))
    else:
        raise ValueError('REVIEW_LANE')
    return {'state': 'REVIEW_ONLY', 'lane': lane, 'result': result, 'ssot_code': None, 'auto_apply': False}


def selftest():
    import time
    checks, measurements = [], {}
    def check(name, condition):
        checks.append(bool(condition)); print(('  [OK] ' if condition else '  [FAIL] ') + name)
    aliases = [
        {'scope': 'fixture', 'term': '台積', 'canonical': 'SHORT', 'rule_code': 'FIXTURE-SYN1'},
        {'scope': 'fixture', 'term': '台積電', 'canonical': 'TSMC', 'rule_code': 'FIXTURE-SYN2'},
        {'scope': 'fixture', 'term': 'buy', 'canonical': 'BUY', 'rule_code': 'FIXTURE-SYN3'},
        {'scope': 'fixture', 'term': 'Bloomberg', 'canonical': 'BLOOMBERG', 'rule_code': 'FIXTURE-SYN4'}]
    table, conflicts = alias_table(aliases, 'fixture')
    source = '台積電 buy buyback 2330.TW 2026/01/02 NT$1,250.50 +5%'
    rows = [{'record_id': 'r1', 'source_id': 'fixture:A', 'scope': 'fixture', 'text': source}]
    results = {}
    for backend in EXACT_BACKENDS:
        start = time.perf_counter(); result = clean_batch(rows, aliases, backend, fuzzy=False)
        measurements[backend] = round(time.perf_counter() - start, 6); results[backend] = result['rows'][0]
        check(backend + ' longest/CJK/boundary', result['rows'][0]['canonical_text'].startswith('TSMC BUY buyback'))
        check(backend + ' original/source preserved', result['rows'][0]['original_text'] == source and result['rows'][0]['source_id'] == 'fixture:A')
    check('three exact backends identical matches', results['aho']['exact_matches'] == results['polars']['exact_matches'] == results['flashtext']['exact_matches'])
    check('UTF8 span is normalized character index', any(m['start'] == 4 and m['term'] == 'buy' for m in results['polars']['exact_matches']))
    values = results['aho']['extractions']
    check('google-re2 / DuckDB raw match parity', extract_values(source.casefold(),'re2') == extract_values(source.casefold(),'duckdb'))
    check('calendar date normalized', any(x['kind'] == 'date' and x['value'] == '2026-01-02' for x in values))
    check('money Decimal currency retained', any(x['value'] == {'currency':'TWD','amount':'1250.50'} for x in values))
    check('percent becomes decimal ratio', any(x['kind'] == 'percent' and x['value'] == '0.05' for x in values))
    check('ordinary ticker uppercase', any(x['kind'] == 'ticker' and x['value'] == '2330.TW' for x in values))
    check('L1 never gives central number', all(x['ssot_code'] is None for x in results.values()))
    check('invalid calendar quarantined', clean_batch([dict(rows[0], text='2026/02/30')],aliases)['rows'][0]['status'] == 'QUARANTINE')
    check('bad comma grouping quarantined', clean_batch([dict(rows[0], text='NT$1,23')],aliases)['rows'][0]['status'] == 'QUARANTINE')
    check('ticker prefix not truncated', not any(x['kind']=='ticker' for x in extract_values('12330.TW')[0]))
    null = clean_batch([dict(rows[0],text=None)], aliases)['rows'][0]
    check('null stays null/NODATA', null['normalized_text'] is None and null['status']=='NODATA')
    check('Pydantic strict rejects numeric text', len(clean_batch([dict(rows[0],text=123)], aliases)['quarantine']) == 1)
    check('Pydantic rejects extra ssot_code field', len(clean_batch([dict(rows[0],ssot_code='fake')], aliases)['quarantine']) == 1)
    check('different sources never merge', clean_batch(rows+[dict(rows[0],source_id='fixture:B')],aliases)['deduplicated_rows']==2)
    repeated = clean_batch(rows+rows,aliases)
    check('identical same-source repeat deduplicated with lineage', repeated['rows'][0]['input_indexes']==[0,1])
    check('same source/id different text held', clean_batch(rows+[dict(rows[0],text='other')],aliases)['rows'][0]['status']=='QUARANTINE')
    conflict = aliases+[dict(aliases[2],canonical='SELL')]
    check('ambiguous alias cannot be applied', clean_batch(rows,conflict)['rows'][0]['status']=='QUARANTINE')
    check('exact-field NFKC mapping', normalize_fields(['ＢＵＹ','buyback',None],{'BUY':'BUY'})==['BUY',None,None])
    fuzzy = fuzzy_candidates('Bloombergg',table)
    check('RapidFuzz high score remains review', bool(fuzzy) and all(x['state']=='REVIEW_ONLY' and not x['auto_apply'] for x in fuzzy))
    check('regex typo matching one edit', bool(fuzzy_regex_candidates('台基電',['台積電'])))
    check('Jellyfish phonetics not applied to Chinese', phonetic_candidates('台積電',['台基電'])[0]['soundex_equal'] is None)
    check('Jellyfish English soundex comparison', phonetic_candidates('Smith',['Smyth'])[0]['soundex_equal'] is True)
    clusters = cluster_candidates(['Bloombergg'],['Bloomberg','Reuters'])
    check('PolyFuzz real TFIDF candidate', clusters[0]['To']=='Bloomberg' and not clusters[0]['auto_apply'])
    links = link_records([{'id':'a','market':'TW','name':'Taiwan Semiconductor'}],
                         [{'id':'b','market':'TW','name':'Taiwan Semiconductor'},{'id':'c','market':'US','name':'Taiwan Semiconductor'}])
    check('recordlinkage blocks by market; no auto merge', len(links)==1 and links[0]['right']=='b' and not links[0]['auto_apply'])
    check('spaCy local explicit lemmas', [x['lemma'] for x in lemma_candidates('bought buying',{'bought':'buy','buying':'buy'})]==['buy','buy'])
    wordnet = wordnet_candidates('buy')
    check('NLTK absent corpus is honest missing', wordnet['state']=='RESOURCE_MISSING' and not wordnet['candidates'])
    import duckdb
    with duckdb.connect(':memory:', config={'enable_external_access':False}) as connection:
        check('DuckDB RE2 extraction cross-check', connection.execute("SELECT regexp_extract(?, ?)", ['2330.TW',r'[1-9][0-9]{3}\.TW']).fetchone()[0]=='2330.TW')
    with tempfile.TemporaryDirectory(prefix='via_l1_test_') as tmp:
        tmp=Path(tmp)
        vectors=tmp/'vectors.json';vectors.write_text(json.dumps({'words':['buy','bought','sell'],'vectors':[[1,0],[.99,.01],[0,1]]}))
        semantic=vector_candidates('buy',vectors,file_hash(vectors))
        check('Gensim local JSON vectors reviewed', semantic['state']=='REVIEW_ONLY' and semantic['candidates'][0]['term']=='bought')
        check('model SHA drift denied', vector_candidates('buy',vectors,'0'*64)['state']=='RESOURCE_REJECTED')
        import fasttext
        corpus=tmp/'tiny.txt';corpus.write_text(('buy growth stock\nsell risk bond\n'*20))
        model=fasttext.train_unsupervised(str(corpus),model='skipgram',dim=8,epoch=2,thread=1,minCount=1,bucket=100,verbose=0)
        binary=tmp/'model.bin';model.save_model(str(binary))
        neighbors=vector_candidates('buy',binary,file_hash(binary),'fasttext')
        check('FastText local synthetic model executes', neighbors['state']=='REVIEW_ONLY' and bool(neighbors['candidates']))
        result=clean_batch(rows,aliases,fuzzy=False)
        first=export_batch(result,tmp/'out');second=export_batch(result,tmp/'out')
        check('dual export verified resume',first['state']=='WRITTEN' and second['state']=='REUSED')
        import polars as pl
        check('Parquet original text roundtrip',pl.read_parquet(tmp/'out/L1_Normalized.parquet')['original_text'][0]==source)
        check('CSV UTF8 BOM', (tmp/'out/L1_Normalized.csv').read_bytes().startswith(b'\xef\xbb\xbf'))
        (tmp/'out/L1_Normalized.csv').write_text('damaged')
        check('partial/corrupt export not falsely reused',export_batch(result,tmp/'out')['state']=='WRITTEN')
        (tmp/'out/L1_Manifest.json').write_text('{broken')
        check('corrupt manifest rebuilt',export_batch(result,tmp/'out')['state']=='WRITTEN')
    try:
        validate_frame([dict(results['aho'],ssot_code='fake')]);check('Pandera egress has no number',False)
    except ValueError:
        check('Pandera egress has no number',True)
    for request in ({'lane':'regex','term':'buy','choices':['buy'],'ssot_code':'fake'},
                    {'lane':'spacy','text':'x'*(MAX_TEXT_CHARS+1),'lookup':{}}):
        try:
            review_request(request); check('review contract rejects excessive/extra input',False)
        except ValueError:
            check('review contract rejects excessive/extra input',True)
    from unittest.mock import patch
    with patch('socket.socket.connect',side_effect=AssertionError('NETWORK_FORBIDDEN')):
        check('clean path succeeds with sockets blocked',clean_batch(rows,aliases)['state']=='CANDIDATE')
    check('all 16 package distributions installed', all(x['version'] for x in tool_inventory()))
    print('[測量] tiny fixture seconds (includes warm-up; not a speed ranking): '+json.dumps(measurements))
    print('[資源] WordNet corpus RESOURCE_MISSING; semantic vectors were synthetic fixtures, not production models')
    print(f'[計] L1 OK {sum(checks)} · FAIL {len(checks)-sum(checks)}')
    return 0 if all(checks) else 1


if __name__ == '__main__':
    sys.exit(main())
