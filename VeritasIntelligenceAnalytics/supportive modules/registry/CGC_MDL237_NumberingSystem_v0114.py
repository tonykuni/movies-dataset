#!/usr/bin/env python3
"""CGC237 v0114: governed asset intake; reuse central allocator, never invent IDs."""
from __future__ import annotations
import copy, hashlib, importlib.util, json, os, re, sys, unicodedata
from pathlib import Path
# ----- Parameters / canonical mappings -----
HERE = Path(__file__).resolve()
ENGINE = 'CGC_MDL237_NumberingSystem_v0114'
PRIOR_PATH = HERE.with_name('CGC_MDL237_NumberingSystem_v0113.py')
BOOK_PATTERN = 'VIA_AssetCandidates_SSOT_v*.json'
LOCK_NAME = '.vcgc_numbering_writer.lock'
MAX_CANDIDATES = 256
MAX_BOOK_BYTES = 1048576
MAX_TEXT = 4096
MAX_LIST = 128
MAX_REGEX_WIDTH = 64
OWNERS = {'VCGC', 'VDF', 'VRN', 'VQG', 'VAP', 'SUP', 'CORE'}
RISK_LEVELS = {'LOW', 'MED', 'HIGH'}
TYPE_KIND = {'INPT': 'PRMT', 'CNFG': 'PRMT', 'OUTP': 'LGC', 'LOGIC': 'LGC',
             'INDICATOR': 'LGC', 'REGEX': 'RGX', 'SYNONYM': 'SYN', 'POLICY': 'PLCY',
             'SSOT': 'SSOT', 'WORKFLOW': 'LGC'}
TEXT_FIELDS = ('candidate_id', 'asset_type', 'owner', 'source_id', 'source_pointer',
               'source_sha256', 'version', 'scope', 'semantic_key', 'name', 'risk_level', 'environment')
REQUIRED_FIELDS = set(TEXT_FIELDS) | {'ssot_code', 'supersedes', 'value', 'libraries', 'aliases', 'positive', 'negative'}
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全樹導入令;graceful 零行為變更) =====
try:
    _sa_p = HERE
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ----- Prior engine / immutable identities -----
def _load_prior():
    spec = importlib.util.spec_from_file_location('numbering_prior_v0114', PRIOR_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = _load_prior()
BASE = PRIOR.BASE
_PREVIOUS_COLLECT = BASE.collect


def __getattr__(name):
    return getattr(PRIOR, name)


def normalized(value):
    return unicodedata.normalize('NFKC', value).strip().casefold()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def identity(row):
    return json.dumps([row['source_id'], row['source_pointer'], row['candidate_id']],
                      ensure_ascii=False, separators=(',', ':'))


def version_key(value):
    return tuple(int(x) for x in value.split('.'))


# ----- Strict candidate contract; source supplies no central number -----
def validate_candidate(raw):
    if not isinstance(raw, dict) or set(raw) != REQUIRED_FIELDS:
        raise ValueError('SCHEMA_FIELDS')
    row = copy.deepcopy(raw)
    for key in TEXT_FIELDS:
        if not isinstance(row[key], str) or not row[key].strip() or len(row[key]) > MAX_TEXT:
            raise ValueError('TEXT_FIELD:' + key)
    if row['ssot_code'] is not None:
        raise ValueError('CENTRAL_CODE_MUST_BE_NULL')
    if row['asset_type'] not in TYPE_KIND or row['owner'] not in OWNERS:
        raise ValueError('TYPE_OR_OWNER')
    if not re.fullmatch(r'[A-Za-z0-9_.:-]+', row['candidate_id']):
        raise ValueError('CANDIDATE_ID')
    if not re.fullmatch(r'[a-z0-9_.:-]+', row['scope']):
        raise ValueError('SCOPE')
    if not re.fullmatch(r'\d+\.\d+\.\d+', row['version']):
        raise ValueError('VERSION')
    if row['supersedes'] is not None and (not isinstance(row['supersedes'], str) or
            not re.fullmatch(r'\d+\.\d+\.\d+', row['supersedes'])):
        raise ValueError('SUPERSEDES_VERSION')
    if not re.fullmatch(r'[0-9a-f]{64}', row['source_sha256']):
        raise ValueError('SOURCE_SHA256')
    if row['risk_level'] not in RISK_LEVELS or not re.fullmatch(r'via_[A-Za-z0-9_]+', row['environment']):
        raise ValueError('RISK_OR_ENVIRONMENT')
    for key in ('libraries', 'aliases', 'positive', 'negative'):
        if not isinstance(row[key], list) or len(row[key]) > MAX_LIST or any(
                not isinstance(x, str) or not x.strip() or len(x) > MAX_TEXT for x in row[key]):
            raise ValueError('LIST_FIELD:' + key)
    if any(re.sub(r'[^a-z0-9]', '', x.casefold()) in ('talib', 'libtalib') for x in row['libraries']):
        raise ValueError('FORBIDDEN_LIBRARY')
    if row['asset_type'] == 'SYNONYM' and (not row['aliases'] or not isinstance(row['value'], str) or not row['value'].strip()):
        raise ValueError('SYNONYM_TARGET_OR_WORDS')
    if row['asset_type'] == 'REGEX' and (not isinstance(row['value'], str) or not row['positive'] or not row['negative']):
        raise ValueError('REGEX_CONTRACT')
    if row['asset_type'] == 'INDICATOR':
        fields = {'formula', 'parameters', 'benchmark', 'explanation', 'pros', 'cons', 'alternatives'}
        if not isinstance(row['value'], dict) or not fields.issubset(row['value']):
            raise ValueError('INDICATOR_METADATA')
    digest(row)  # Reject non-JSON / non-finite values before registry comparison.
    return row


# ----- Bounded regex language: exact disjointness, no heuristic GREEN -----
def fixed_language(pattern):
    """Prove anchored fixed-width ASCII languages; unsupported dialects require review."""
    if not pattern.startswith('^') or not pattern.endswith('$'):
        return None
    body, pos, tokens = pattern[1:-1], 0, []
    while pos < len(body):
        char = body[pos]
        if char == '[':
            end = body.find(']', pos + 1)
            if end < 0:
                return None
            group, chars, i = body[pos + 1:end], set(), 0
            if not group or group.startswith('^') or '\\' in group:
                return None
            while i < len(group):
                if i + 2 < len(group) and group[i + 1] == '-':
                    lo, hi = ord(group[i]), ord(group[i + 2])
                    if lo > hi or hi > 126 or lo < 32:
                        return None
                    chars.update(chr(x) for x in range(lo, hi + 1)); i += 3
                else:
                    chars.add(group[i]); i += 1
            pos = end + 1
        elif char == '\\':
            if pos + 1 >= len(body) or body[pos + 1] not in '.^$[]{}()*+?|' + chr(92):
                return None
            chars = {body[pos + 1]}; pos += 2
        elif char in '.^$[]{}()*+?|':
            return None
        else:
            chars = {char}; pos += 1
        if any(ord(x) < 32 or ord(x) > 126 for x in chars):
            return None
        repeat = 1
        if pos < len(body) and body[pos] == '{':
            match = re.match(r'\{([1-9][0-9]?)\}', body[pos:])
            if not match:
                return None
            repeat = int(match.group(1)); pos += len(match.group())
        tokens.extend([frozenset(chars)] * repeat)
        if len(tokens) > MAX_REGEX_WIDTH:
            return None
    return tokens or None


def regex_overlap(left, right):
    a, b = fixed_language(left), fixed_language(right)
    if a is None or b is None:
        return None
    return len(a) == len(b) and all(x & y for x, y in zip(a, b))


def regex_check(row):
    import duckdb
    if fixed_language(row['value']) is None:
        return 'REGEX_PROOF_REQUIRED'
    try:
        with duckdb.connect(':memory:') as conn:
            for expected, samples in ((True, row['positive']), (False, row['negative'])):
                for sample in samples:
                    actual = conn.execute('SELECT regexp_full_match(?, ?)', [sample, row['value']]).fetchone()[0]
                    if actual != expected:
                        return 'REGEX_EXAMPLE_FAILED'
    except duckdb.Error:
        return 'REGEX_INVALID'
    return None


# ----- Conflict planning / registration adapter -----
def make_plan(candidates, registered=(), legacy=()):
    if not isinstance(candidates, list) or len(candidates) > MAX_CANDIDATES:
        raise ValueError('CANDIDATE_LIMIT')
    results, valid = [], []
    history = {}
    for old in registered:
        if old.get('asset_intake'):
            history.setdefault(identity(old['candidate_asset']), []).append(old)
    for raw in candidates:
        result = {'candidate_id': raw.get('candidate_id') if isinstance(raw, dict) else None,
                  'source_id': raw.get('source_id') if isinstance(raw, dict) else None,
                  'ssot_code': None, 'state': 'READY', 'reasons': []}
        results.append(result)
        try:
            row = validate_candidate(raw)
            old_versions = history.get(identity(row), [])
            same = [x for x in old_versions if x['candidate_asset']['version'] == row['version']]
            if same:
                if any(x.get('definition_sha256') != digest(row) for x in same):
                    result['reasons'].append('IMMUTABLE_VERSION_CHANGED')
                else:
                    result['ssot_code'] = same[0]['code']
            elif old_versions:
                latest = max(old_versions, key=lambda x: version_key(x['candidate_asset']['version']))['candidate_asset']
                if row['supersedes'] != latest['version'] or version_key(row['version']) <= version_key(latest['version']):
                    result['reasons'].append('EXPLICIT_NEW_VERSION_REQUIRED')
            elif row['supersedes'] is not None:
                result['reasons'].append('MISSING_PREDECESSOR')
            if row['asset_type'] == 'REGEX':
                reason = regex_check(row)
                if reason:
                    result['reasons'].append(reason)
            valid.append((row, result))
        except (ValueError, TypeError, KeyError) as exc:
            result['reasons'].append(str(exc))
    # Latest registered asset per source identity; no collapse across sources.
    existing = [max(rows, key=lambda x: version_key(x['candidate_asset']['version']))['candidate_asset']
                for rows in history.values()]
    for row, result in valid:
        peers = [x for x in existing if identity(x) != identity(row)]
        peers += [x for x, other in valid if other is not result]
        for peer in peers:
            if identity(peer) == identity(row) and peer['version'] == row['version']:
                result['reasons'].append('DUPLICATE_CANDIDATE_IDENTITY')
                continue
            if (row['owner'], row['scope']) != (peer['owner'], peer['scope']):
                continue
            if row['asset_type'] == peer['asset_type'] == 'SYNONYM':
                words = set(map(normalized, row['aliases'])) & set(map(normalized, peer['aliases']))
                if words and normalized(row['value']) != normalized(peer['value']):
                    result['reasons'].append('ALIAS_MULTIPLE_TARGETS')
            elif row['asset_type'] == peer['asset_type'] == 'REGEX':
                overlap = regex_overlap(row['value'], peer['value'])
                if overlap is None:
                    result['reasons'].append('REGEX_OVERLAP_UNKNOWN')
                elif overlap and row['semantic_key'] != peer['semantic_key']:
                    result['reasons'].append('REGEX_OVERLAP_DIFFERENT_TARGETS')
            elif TYPE_KIND[row['asset_type']] == TYPE_KIND[peer['asset_type']] and row['semantic_key'] == peer['semantic_key'] and digest(row['value']) != digest(peer['value']):
                result['reasons'].append('VALUE_CONFLICT_SAME_BINDING')
        # Legacy authoritative rows are read-only. Unmapped overlapping aliases require review.
        if row['asset_type'] == 'SYNONYM':
            words = set(map(normalized, row['aliases']))
            for old in legacy:
                if old.get('kind') != 'SYN' or not words.intersection(map(normalized, old.get('words') or [])):
                    continue
                oldscope = str(old.get('scope') or str(old.get('cat', '')).removeprefix('中央同義冊/'))
                if old.get('sub') == row['owner'] and oldscope == row['scope']:
                    target = old.get('alias_of') or old.get('name', '')
                    if normalized(target) != normalized(row['value']) or old.get('lamp') != 'GREEN':
                        result['reasons'].append('LEGACY_ALIAS_CONFLICT')
                elif not old.get('scope') and not str(old.get('cat', '')).startswith('中央同義冊/'):
                    result['reasons'].append('LEGACY_ALIAS_SCOPE_UNKNOWN')
                    result.setdefault('conflicts', []).append({'code': old.get('code'), 'source': old.get('source'), 'name': old.get('name'), 'kind': 'SYN', 'scope': oldscope})
                elif oldscope != row['scope']:
                    result.setdefault('notes', []).append('SAME_WORD_OTHER_SCOPE_RETAINED')
        if row['asset_type'] == 'REGEX':
            for old in legacy:
                if old.get('kind') != 'RGX' or old.get('sub') != row['owner']:
                    continue
                if old.get('scope') in (None, row['scope']):
                    pattern = old.get('pattern') or old.get('name', '')
                    overlap = regex_overlap(row['value'], pattern)
                    if overlap is not False and old.get('semantic_key') != row['semantic_key']:
                        result['reasons'].append('LEGACY_REGEX_CONFLICT_OR_UNPROVEN')
                        result.setdefault('conflicts', []).append({'code': old.get('code'), 'source': old.get('source'), 'name': old.get('name'), 'kind': 'RGX', 'scope': old.get('scope')})
    for result in results:
        result['reasons'] = sorted(set(result['reasons']))
        if 'conflicts' in result:
            result['conflict_count'] = len(result['conflicts'])
            result['conflicts'] = result['conflicts'][:MAX_LIST]
        result['state'] = ('REVIEW' if any('PROOF' in x or 'UNKNOWN' in x or 'UNPROVEN' in x for x in result['reasons']) else 'BLOCKED') if result['reasons'] else ('REGISTERED' if result['ssot_code'] else 'READY')
        # A previously assigned identity is retained even when its new proposal is blocked.
    return {'schema': 'VIA.AssetIntakePlan.v1', 'results': results,
            'ready': sum(x['state'] == 'READY' for x in results),
            'blocked': sum(x['state'] in ('BLOCKED', 'REVIEW') for x in results)}


def candidate_items(candidates, source, registered=(), legacy=()):
    plan = make_plan(candidates, registered, legacy)
    items = []
    for raw, result in zip(candidates, plan['results']):
        if result['state'] not in ('READY', 'REGISTERED'):
            continue
        row = validate_candidate(raw)
        items.append(BASE.item(TYPE_KIND[row['asset_type']], 'asset-intake|' + identity(row), row['name'],
            '資產候選/' + row['asset_type'], source, 'assets-plan', '2026-10-03T00:00:00+00:00', row['owner'],
            row['version'], 'GREEN', 'Registration checks passed; not deployment or data-quality approval.',
            asset_intake=True, candidate_asset=row, definition_sha256=digest(row),
            source_identity=row['source_id'], source_pointer=row['source_pointer'], scope=row['scope'],
            semantic_key=row['semantic_key'], risk_level=row['risk_level'], environment=row['environment'],
            libraries=row['libraries'], asset_type=row['asset_type']))
    return items, plan


def read_book(path):
    path = Path(path)
    if path.stat().st_size > MAX_BOOK_BYTES:
        raise ValueError('BOOK_SIZE_LIMIT')
    book = json.loads(path.read_text(encoding='utf-8-sig'))
    if set(book) != {'schema', 'version', 'assets'} or book['schema'] != 'VIA.AssetCandidates.v1':
        raise ValueError('BOOK_SCHEMA')
    return book


def collect():
    items, notes = _PREVIOUS_COLLECT()
    path = BASE._newest(BASE.HERE, BOOK_PATTERN)
    if path is not None:
        added, plan = candidate_items(read_book(path)['assets'], BASE._rel(path),
                                     list(BASE.load_state()['rows'].values()), items)
        items.extend(added)
        notes['asset_intake'] = plan
    return items, notes


BASE.collect = collect


# ----- VCGC commands; normal allocator remains sole writer -----
def assets_plan(path=None):
    path = Path(path) if path else BASE._newest(BASE.HERE, BOOK_PATTERN)
    if path is None:
        raise ValueError('NO_CANDIDATE_BOOK')
    legacy, _ = _PREVIOUS_COLLECT()
    _, plan = candidate_items(read_book(path)['assets'], BASE._rel(path),
                             list(BASE.load_state()['rows'].values()), legacy)
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 2 if plan['blocked'] else 0


def asset_views(registered):
    """Read-only projections of central records; these are not a second database."""
    groups = {}
    versions, tags = [], []
    for record in registered:
        if not record.get('asset_intake'):
            continue
        row = record['candidate_asset']
        key = identity(row)
        groups.setdefault(key, []).append(record)
        versions.append({'ssot_code': record['code'], 'asset_key': key, 'version': row['version'],
                         'value': row['value'], 'source_id': row['source_id'],
                         'source_sha256': row['source_sha256'], 'numbered_at': record['numbered_at']})
        tags.append({'ssot_code': record['code'], 'owner': row['owner'], 'risk_level': row['risk_level'],
                     'environment': row['environment'], 'libraries': row['libraries']})
    assets = []
    for key, records in sorted(groups.items()):
        latest = max(records, key=lambda x: version_key(x['candidate_asset']['version']))
        row = latest['candidate_asset']
        assets.append({'asset_key': key, 'current_code': latest['code'], 'current_version': row['version'],
                       'asset_type': row['asset_type'], 'owner': row['owner'], 'scope': row['scope'],
                       'name': row['name'], 'status': 'REGISTERED_NOT_DEPLOYED'})
    return {'scope': 'asset_intake_only', 'authority': 'VIA_Numbering_SSOT / VIA_NumberBooks',
            'ssot_asset_registry': assets, 'vcgc_version_history': versions, 'asset_execution_tags': tags}


def with_writer_lock(action, lock_path=None):
    lock = Path(lock_path) if lock_path else BASE.HERE / LOCK_NAME
    try:
        fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        print('[HOLD] CENTRAL_WRITER_BUSY; lock retained, no takeover')
        return 2
    try:
        os.write(fd, json.dumps({'pid': os.getpid(), 'engine': ENGINE}).encode())
        os.close(fd)
        return action()
    finally:
        lock.unlink(missing_ok=True)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ['--selftest']:
        return selftest()
    if args == ['assets-view']:
        if os.environ.get('VIA_FROM_VCGC') != 'YES':
            return 2
        print(json.dumps(asset_views(BASE.load_state()['rows'].values()), ensure_ascii=False, indent=2))
        return 0
    if args[:1] == ['assets-plan']:
        if os.environ.get('VIA_FROM_VCGC') != 'YES':
            print('[DENY] VCGC entry required')
            return 2
        if len(args) > 2:
            print('[DENY] assets-plan [candidate_book.json]')
            return 2
        return assets_plan(args[1] if len(args) == 2 else None)
    if '--apply' in args:
        if os.environ.get('VIA_FROM_VCGC') != 'YES':
            print('[DENY] VCGC entry required')
            return 2
        if '--scope' not in args:
            print('[HOLD] Use committed --apply --scope; global refresh is not an intake operation')
            return 2
        return with_writer_lock(lambda: PRIOR.main(args))
    return PRIOR.main(args)


# ----- Isolated synthetic tests: never write production number books -----
def fixture(candidate_id='start', source='fixture:A', asset_type='INPT', **changes):
    row = {'candidate_id': candidate_id, 'ssot_code': None, 'asset_type': asset_type,
        'owner': 'VDF', 'source_id': source, 'source_pointer': '/start', 'source_sha256': 'a' * 64,
        'version': '1.0.0', 'supersedes': None, 'scope': 'daily.start', 'semantic_key': 'start_date',
        'name': '開始日期', 'value': '2026-01-02', 'risk_level': 'LOW', 'environment': 'via_core',
        'libraries': ['polars'], 'aliases': [], 'positive': [], 'negative': []}
    row.update(changes)
    return row


def selftest():
    import tempfile
    checks = []
    def check(name, condition):
        checks.append(bool(condition))
        print(('  [OK] ' if condition else '  [FAIL] ') + name)
    def state():
        return {'rows': {}, 'subs': ['VDF', 'VQG'], 'cats': {}}
    def blocked(rows, old=(), legacy=()):
        return make_plan(rows, old, legacy)['blocked']
    a = fixture()
    b = fixture(source='fixture:B')
    items, plan = candidate_items([a, b], 'fixture.json')
    check('different sources same value accepted independently', len(items) == 2 and plan['blocked'] == 0)
    s = BASE.assign(items, state()); codes = [r['code'] for r in s['rows'].values()]
    check('sole central allocator assigns distinct source numbers', len(set(codes)) == 2)
    again, p = candidate_items([a, b], 'fixture.json', list(s['rows'].values()))
    s2 = BASE.assign(again, copy.deepcopy(s))
    check('idempotent code and first timestamp', s2 == s)
    changed = dict(a, value='2026-01-05')
    check('same version mutation rejected', blocked([changed], list(s['rows'].values())) == 1)
    check('different sources conflicting same binding both held', blocked([a, dict(b, value='2026-01-05')]) == 2)
    check('source number cannot be supplied', blocked([dict(a, ssot_code='VIA-VDF-PRMT001')]) == 1)
    check('nonfinite input rejected', blocked([dict(a, value=float('nan'))]) == 1)
    check('unknown fields rejected', blocked([dict(a, rogue=True)]) == 1)
    check('dependency prohibition', blocked([dict(a, libraries=['TA-Lib'])]) == 1)
    check('environment must use via prefix', blocked([dict(a, environment='prod')]) == 1)
    check('duplicate input identity rejected', blocked([a, a]) == 2)
    # Version progression tested on one source (no cross-source value conflict).
    old = [list(s['rows'].values())[0]]
    newer = dict(a, version='1.0.1', supersedes='1.0.0', value='2026-01-05')
    ni, np = candidate_items([newer], 'fixture2.json', old)
    one = state(); one['rows'] = {k: v for k, v in s['rows'].items() if v['source_identity'] == a['source_id']}
    ns = BASE.assign(ni, copy.deepcopy(one))
    check('new version new number and old retained', len(ns['rows']) == 2 and len({x['code'] for x in ns['rows'].values()}) == 2)
    check('new version needs explicit predecessor', blocked([dict(newer, supersedes=None)], old) == 1)
    check('missing predecessor rejected', blocked([newer]) == 1)
    syn = fixture(asset_type='SYNONYM', scope='rating', semantic_key='buy', value='BUY', aliases=['買進', 'ＢＵＹ'])
    syn2 = dict(syn, source_id='fixture:B', value='SELL', aliases=['buy'])
    check('NFKC same-scope synonym conflict', blocked([syn, syn2]) == 2)
    check('different scopes retain distinct meanings', blocked([syn, dict(syn2, scope='other')]) == 0)
    check('same target from separate sources allowed', blocked([syn, dict(syn2, value='BUY')]) == 0)
    legacy = [{'kind': 'SYN', 'sub': 'VDF', 'scope': 'rating', 'words': ['BUY'], 'name': 'SELL', 'lamp': 'GREEN'}]
    check('legacy alias conflict blocks promotion', blocked([syn], legacy=legacy) == 1)
    rx = fixture(asset_type='REGEX', scope='ticker', semantic_key='twse', value=r'^[1-9][0-9]{3}\.TW$', positive=['2330.TW'], negative=['bad2330.TW'])
    rx2 = dict(rx, source_id='fixture:B', semantic_key='tpex', value=r'^[1-9][0-9]{3}\.TWO$', positive=['6488.TWO'])
    check('regex disjoint languages accepted', blocked([rx, rx2]) == 0)
    check('regex overlap with different target rejected', blocked([rx, dict(rx2, value=rx['value'], positive=['2330.TW'])]) == 2)
    check('regex unsupported proof returns REVIEW', make_plan([dict(rx, value=r'^.*$')])['results'][0]['state'] == 'REVIEW')
    check('regex invalid witness rejected', blocked([dict(rx, negative=['2330.TW'])]) == 1)
    check('regex empty anchored string not supported', fixed_language('^$') is None)
    check('bounded length prevents oversized language', fixed_language('^[0-9]{99}$') is None)
    check('indicator requires formula/pros/cons etc', blocked([fixture(asset_type='INDICATOR')]) == 1)
    check('INPT/CNFG same binding cannot evade conflict', blocked([a, dict(b, asset_type='CNFG', value='different')]) == 2)
    check('read-only three-table projections preserve sources', len(asset_views(s['rows'].values())['ssot_asset_registry']) == 2)
    with tempfile.TemporaryDirectory() as tmp:
        lock = Path(tmp) / 'writer.lock'
        lock.write_text('other writer')
        check('concurrent writer held without touching lock', with_writer_lock(lambda: 9, lock) == 2 and lock.read_text() == 'other writer')
        lock.unlink()
        check('owned lock released', with_writer_lock(lambda: 0, lock) == 0 and not lock.exists())
        p = Path(tmp) / 'book.json'; p.write_text(json.dumps({'schema': 'VIA.AssetCandidates.v1', 'version': '1.0.0', 'assets': [a]}))
        check('book contract', read_book(p)['assets'] == [a])
    print(f'[計] OK {sum(checks)} · FAIL {len(checks)-sum(checks)} · temporary fixtures only')
    return 0 if all(checks) else 1


if __name__ == '__main__':
    sys.exit(main())
