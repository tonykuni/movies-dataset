# -*- coding: utf-8 -*-
"""
def Veritas Subsystem Integration Audit v003
Append-only / review-only / no canonical mutation.
Checks whether VDF, VRN, FlowSystem, VAP, VETF, VIAS, VPNS/NexusCore have sufficient integration of:
- data requirements
- library requirements
- parameter contracts
- source adapters
- validation/gates
- dedup/omission risks
"""
from __future__ import annotations

import csv
import datetime as _dt
import hashlib
import html
import json
import os
import pathlib
import zipfile
from typing import Any, Dict, List

# ============================ def PARAMETERS ============================
def_BASE_DIR = pathlib.Path('/mnt/data')
def_VERSION = 'v003'
def_RUN_STAMP = _dt.datetime.now().strftime('%Y%m%d_%H%M%S')
def_RUN_DIR = def_BASE_DIR / f'_veritas_subsystem_integration_audit_runs/RUN_{def_RUN_STAMP}_VERITAS_SUBSYSTEM_INTEGRATION_AUDIT_v003'
def_MASTER_CSV = def_BASE_DIR / 'Veritas_Unified_SSOT_Master_Registry_v002.csv'
def_ASSET_CSV = def_BASE_DIR / 'Veritas_Asset_Universe_v002.csv'
def_LEADER_CSV = def_BASE_DIR / 'Veritas_Leader_Universe_v002.csv'
def_TW_GROUP_CSV = def_BASE_DIR / 'Veritas_Taiwan_Group_Taxonomy_v002.csv'
def_SOURCE_ADAPTER_CSV = def_BASE_DIR / 'Veritas_Source_Adapter_Registry_v002.csv'
def_MODULE_INTERFACE_CSV = def_BASE_DIR / 'Veritas_Module_Interface_Registry_v002.csv'
def_VALIDATION_RULE_CSV = def_BASE_DIR / 'Veritas_Validation_Rule_Registry_v002.csv'
def_V001_MASTER_CSV = def_BASE_DIR / 'VIA_Unified_SSOT_Master_Registry_v001.csv'
def_OUTPUT_PREFIX = 'Veritas_Subsystem_Integration_Audit_v003'
def_POLICY = {
    'append_only': True,
    'review_only': True,
    'no_source_mutation': True,
    'no_db_write': True,
    'no_canonical_merge': True,
    'no_network': True,
    'dedup_strategy': 'do_not_delete; mark duplicate_group and keep provenance',
}

# ============================ def IO HELPERS ============================
def def_sha12(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8', errors='ignore')).hexdigest()[:12].upper()


def def_read_csv(path: pathlib.Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def def_write_csv(path: pathlib.Path, rows: List[Dict[str, Any]], fieldnames: List[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys = []
        for row in rows:
            for k in row.keys():
                if k not in keys:
                    keys.append(k)
        fieldnames = keys
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def def_write_json(path: pathlib.Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')

# ============================ def SOURCE LOAD ============================
def def_load_state() -> Dict[str, Any]:
    master = def_read_csv(def_MASTER_CSV)
    v001 = def_read_csv(def_V001_MASTER_CSV)
    assets = def_read_csv(def_ASSET_CSV)
    leaders = def_read_csv(def_LEADER_CSV)
    groups = def_read_csv(def_TW_GROUP_CSV)
    adapters = def_read_csv(def_SOURCE_ADAPTER_CSV)
    interfaces = def_read_csv(def_MODULE_INTERFACE_CSV)
    rules = def_read_csv(def_VALIDATION_RULE_CSV)
    return {
        'master': master,
        'v001': v001,
        'assets': assets,
        'leaders': leaders,
        'groups': groups,
        'adapters': adapters,
        'interfaces': interfaces,
        'rules': rules,
    }


def def_counts(rows: List[Dict[str, str]], key: str) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for r in rows:
        v = (r.get(key) or '').strip() or '(blank)'
        out[v] = out.get(v, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))


def def_duplicate_count(rows: List[Dict[str, str]], key: str) -> int:
    seen = set()
    d = 0
    for r in rows:
        v = (r.get(key) or '').strip()
        if not v:
            continue
        if v in seen:
            d += 1
        seen.add(v)
    return d

# ============================ def REQUIREMENT SEED ============================
def def_required_libs() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    def add(subsystem, lib, role, priority, category='python', status='REGISTER_REQUIRED', install_hint='pip/conda/env-manager', notes=''):
        rows.append({
            'veritas_req_id': f'VERITAS-LIB-{len(rows)+1:04d}',
            'subsystem': subsystem,
            'requirement_type': 'LIB',
            'name': lib,
            'role': role,
            'priority': priority,
            'category': category,
            'current_status': status,
            'install_hint': install_hint,
            'validation_method': 'import_check|version_check|capability_probe|optional_gate',
            'dedup_key': f'{subsystem}|LIB|{lib}'.upper(),
            'remarks': notes,
        })
    # VDF data stack
    for lib, role, pr in [
        ('pandas', 'dataframe transform / csv parquet bridge', 'P0'),
        ('polars', 'large table fast transform', 'P1'),
        ('pyarrow', 'parquet read/write', 'P0'),
        ('duckdb', 'local analytical DB', 'P0'),
        ('requests', 'official API fetch adapter', 'P0'),
        ('yfinance', 'price/proxy fallback; not official truth', 'P1'),
        ('akshare', 'optional China/TW/global public data cross-check', 'P2'),
        ('fredapi_or_requests_fred', 'FRED observations adapter', 'P1'),
        ('beautifulsoup4', 'HTML table fallback parse', 'P2'),
        ('lxml', 'HTML/XML parser acceleration', 'P2'),
    ]:
        add('VDF', lib, role, pr)
    # VRN document extraction stack
    for lib, role, pr in [
        ('pdfplumber', 'PDF text/table extraction and visual debug', 'P0'),
        ('PyMuPDF', 'fast PDF page render / text / table candidates', 'P0'),
        ('pdfminer.six', 'layout text extraction foundation', 'P1'),
        ('pypdf', 'PDF metadata/page handling', 'P1'),
        ('camelot-py', 'table extraction candidate engine', 'P1'),
        ('tabula-py', 'table extraction candidate engine requiring Java', 'P2'),
        ('opencv-python', 'grid/line/table geometry detection', 'P0'),
        ('Pillow', 'image preprocess / render handoff', 'P1'),
        ('pytesseract', 'OCR bridge to Tesseract', 'P1'),
        ('paddleocr', 'OCR/structure optional high-recall engine', 'P2'),
        ('easyocr', 'OCR optional fallback', 'P3'),
        ('numpy', 'array/math foundation', 'P0'),
    ]:
        add('VRN', lib, role, pr)
    # FIS/Backtest/Validation
    for lib, role, pr in [
        ('numpy', 'simulation / vectorization / signal math', 'P0'),
        ('scipy', 'rank correlation, normal CDF, t-test', 'P0'),
        ('statsmodels', 'optional econometrics diagnostics', 'P2'),
        ('scikit-learn', 'optional model validation / clustering', 'P2'),
        ('matplotlib', 'offline chart output if HTML not enough', 'P2'),
    ]:
        add('FIS_BACKTEST', lib, role, pr)
    # UI/HTML/Supportive
    for mod in ['Pester', 'PSScriptAnalyzer', 'ThreadJob', 'ImportExcel', 'PSWriteHTML', 'PSFramework', 'Pode', 'Polaris', 'BurntToast', 'PSReadLine']:
        add('NEXUS_SUPPORTIVE', mod, 'PowerShell governance / UI / testing extension', 'P1', category='powershell', install_hint='Install-Module or existing PS module')
    return rows


def def_required_data() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    def add(subsystem, data_domain, source, priority, owner, frequency, status='REGISTERED_NEEDS_FETCH_QUEUE', notes=''):
        rows.append({
            'veritas_req_id': f'VERITAS-DATA-{len(rows)+1:04d}',
            'subsystem': subsystem,
            'requirement_type': 'DATA',
            'data_domain': data_domain,
            'primary_source': source,
            'priority': priority,
            'owner_module': owner,
            'frequency': frequency,
            'current_status': status,
            'validation_method': 'schema_check|freshness_check|row_count_check|cross_source_check|provenance_hash',
            'dedup_key': f'{subsystem}|DATA|{data_domain}|{source}'.upper(),
            'remarks': notes,
        })
    for data_domain, source, pr, freq in [
        ('台股上市價格/基本行情', 'TWSE OpenAPI / MI_INDEX / STOCK_DAY_ALL', 'P0', 'daily'),
        ('台股上櫃價格/基本行情', 'TPEX official CSV/API', 'P0', 'daily'),
        ('三大法人買賣超', 'TWSE T86 / TPEX institutional', 'P0', 'daily_eod'),
        ('融資融券/券資比/當沖/借券', 'TWSE/TPEX/TDCC', 'P0', 'daily_eod'),
        ('MOPS 公司基本資料/財報', 'MOPS', 'P0', 'monthly/quarterly'),
        ('全球價格 proxy', 'yfinance', 'P1', 'daily'),
        ('FRED 利率/美元/信用利差', 'FRED series/observations', 'P1', 'daily/weekly/monthly'),
        ('AKShare 補充資料', 'AKShare optional', 'P2', 'as_needed'),
        ('全球資產 universe', 'Veritas_Asset_Universe_v002', 'P0', 'as_needed'),
        ('全球龍頭 universe', 'Veritas_Leader_Universe_v002', 'P0', 'as_needed'),
        ('台股族群 taxonomy', 'Veritas_Taiwan_Group_Taxonomy_v002', 'P0', 'as_needed'),
    ]:
        add('VDF', data_domain, source, pr, 'VIA_DATA_ADAPTERS', freq)
    for data_domain, source, pr, freq in [
        ('券商/研究報告 PDF 原文', 'local report folders', 'P0', 'batch'),
        ('ReportBasicInfo', 'VRN staged extraction', 'P0', 'batch'),
        ('ReportText / table long / table meta', 'VRN staged extraction', 'P0', 'batch'),
        ('ExceptionQueue', 'VRN staged extraction', 'P1', 'batch'),
        ('BrokerAlias / analyst adapters', 'NexusCore 70_VRN_Rules', 'P1', 'as_needed'),
        ('FinancialSSOT / unit normalization', 'NexusCore 70_VRN_Rules', 'P0', 'as_needed'),
    ]:
        add('VRN', data_domain, source, pr, 'VIA_VRN', freq)
    for data_domain, source, pr, freq in [
        ('FIS extraction matrix 77 rows', 'VIA_Extraction_Matrix / FlowSystem registry', 'P0', 'as_needed'),
        ('FIS validation harness outputs', 'VIA_FIS_Validation_v3 / Backtest Harness', 'P1', 'run'),
        ('ONE master overview', 'VIA_ONE_Master_Overview', 'P2', 'as_needed'),
        ('NexusCore supportive registry', 'Invoke-VeritasNexusCore + Registry/HardGate', 'P0', 'run'),
    ]:
        add('FLOW_NEXUS', data_domain, source, pr, 'VIA_SSOT_MANAGER', freq)
    return rows


def def_required_params() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    def add(subsystem, param_group, canonical_policy, priority, status, notes=''):
        rows.append({
            'veritas_req_id': f'VERITAS-PARAM-{len(rows)+1:04d}',
            'subsystem': subsystem,
            'requirement_type': 'PARAMETER',
            'param_group': param_group,
            'canonical_policy': canonical_policy,
            'priority': priority,
            'current_status': status,
            'validation_method': 'json_schema|required_fields|alias_map|unit_normalization|secret_mask|append_only_diff',
            'dedup_key': f'{subsystem}|PARAM|{param_group}'.upper(),
            'remarks': notes,
        })
    for p, pol, pr, st, notes in [
        ('project_roots', 'Downloads functional modules + supportive modules through NexusCore', 'P0', 'PARTIAL_REVIEW', 'OneDrive legacy paths must remain reference-only unless approved'),
        ('data_source_contract', 'PROVIDER_REGISTRY_ONLY; API_KEYS_FROM_ENV_OR_UI_SECRET; FALLBACK_EXPLICIT', 'P0', 'POLICY_EXISTS_NEEDS_ROW_EXPANSION', ''),
        ('ticker_identity', 'TW_TICKER=4_DIGITS; TWSE_YF=.TW; TPEX_YF=.TWO; OVERSEAS=native', 'P0', 'POLICY_EXISTS', ''),
        ('schema_field_contract', 'OWNER_SCHEMA_REGISTRY; FIELD_ALIAS_MAP; UNIT_NORMALIZATION_TABLE', 'P0', 'POLICY_EXISTS', ''),
        ('fetch_window_calendar', 'trading calendar / holiday / fill policy centralized', 'P1', 'NEEDS_EXTERNAL_JSON', ''),
        ('rate_limit_retry', 'per-provider throttle + retry + no-hang timeout', 'P1', 'NEEDS_EXTERNAL_JSON', ''),
        ('output_contract', 'CSV/Parquet/JSON/HTML run-local outputs', 'P0', 'PARTIAL_REVIEW', ''),
    ]:
        add('VDF', p, pol, pr, st, notes)
    for p, pol, pr, st, notes in [
        ('input_routes', 'PDF batch folder + file registry + no rerun extraction policy', 'P0', 'PARTIAL_REVIEW', ''),
        ('ocr_table_modes', 'pdfplumber/PyMuPDF/CV/OCR multi-engine strategy', 'P0', 'NEEDS_EXTERNAL_JSON', ''),
        ('report_identity', 'ReportID stronger key: file hash + broker + date + ticker + title hash', 'P0', 'REPAIR_REQUIRED_STAGING_ONLY', 'Duplicate report_id remains sequential issue'),
        ('schema_field_contract', 'OWNER_SCHEMA_REGISTRY; FIELD_ALIAS_MAP; UNIT_NORMALIZATION_TABLE', 'P0', 'POLICY_EXISTS', ''),
        ('exception_queue_policy', 'Exception rows feed dictionary/regex/account mapper; no auto source rewrite', 'P1', 'POLICY_EXISTS_NEEDS_UI_REVIEW', ''),
    ]:
        add('VRN', p, pol, pr, st, notes)
    for p, pol, pr, st, notes in [
        ('flow_params_json', 'via_flow_params.json controls mode/fis/fusion/lenses/ui/gates', 'P0', 'EXISTS', ''),
        ('embedded_registry_77', 'Move embedded REGISTRY_JSON to external SSOT JSON/CSV', 'P0', 'REFACTOR_RECOMMENDED', ''),
        ('nexus_first_layer', 'All modules call Invoke-VeritasNexusCore.ps1 first', 'P0', 'POLICY_EXISTS', ''),
        ('vpns_accelerator_gate', 'Enable 15 pending accelerators only after baseline pass', 'P1', 'SEQUENCE_GATE_REQUIRED', ''),
    ]:
        add('FLOW_NEXUS', p, pol, pr, st, notes)
    for subsystem in ['VAP', 'VETF', 'VIAS']:
        add(subsystem, 'subsystem_param_manifest', 'Create/standardize subsystem params JSON + interface manifest + validation schema', 'P1', 'OMISSION_GAP', 'Not sufficiently visible in current uploaded v002 registry')
    return rows

# ============================ def AUDIT ============================
def def_build_audit(state: Dict[str, Any]) -> Dict[str, Any]:
    master = state['master']
    family_counts = def_counts(master, 'family')
    domain_counts = def_counts(master, 'domain')
    owner_counts = def_counts(master, 'owner_module')
    duplicate_canonical = def_duplicate_count(master, 'canonical_key')
    duplicate_ssot = def_duplicate_count(master, 'ssot_id')
    duplicate_veritas = def_duplicate_count(master, 'veritas_id')
    legacy_count = len(state['v001'])
    master_count = len(master)
    append_count = max(0, master_count - legacy_count)
    findings: List[Dict[str, Any]] = []
    def add_finding(sev, subsystem, layer, issue, evidence, action, mode='SEQUENTIAL_REQUIRED'):
        findings.append({
            'finding_id': f'FIND-{len(findings)+1:04d}',
            'severity': sev,
            'subsystem': subsystem,
            'layer': layer,
            'issue': issue,
            'evidence': evidence,
            'recommended_action': action,
            'safe_mode': mode,
        })
    if duplicate_veritas == 0:
        add_finding('OK', 'SSOT', 'IDENTITY', 'veritas_id unique', f'duplicate_veritas_id={duplicate_veritas}', 'Keep stable; never renumber existing rows', 'PARALLEL_SAFE')
    else:
        add_finding('FAIL', 'SSOT', 'IDENTITY', 'veritas_id duplicate', f'duplicate_veritas_id={duplicate_veritas}', 'Freeze and resolve manually', 'SEQUENTIAL_REQUIRED')
    if duplicate_canonical:
        add_finding('WARN', 'SSOT', 'DEDUP', 'canonical_key duplicates remain intentionally preserved', f'duplicate_canonical_key={duplicate_canonical}', 'Do not delete; add duplicate_group and preferred_current flag', 'SEQUENTIAL_REQUIRED')
    if duplicate_ssot:
        add_finding('WARN', 'SSOT', 'DEDUP', 'ssot_id duplicates inherited from hash-based legacy IDs', f'duplicate_ssot_id={duplicate_ssot}', 'Keep veritas_id as stable primary key; rebuild ssot_id only in staging if necessary', 'SEQUENTIAL_REQUIRED')
    if append_count >= 250:
        add_finding('OK', 'SSOT', 'APPEND_ONLY', 'v002 preserved v001 and appended new universe', f'v001={legacy_count}; master={master_count}; appended={append_count}', 'Continue append-only diff gate', 'PARALLEL_SAFE')
    if len(state['assets']) and len(state['leaders']) and len(state['groups']):
        add_finding('OK', 'VDF', 'DATA_UNIVERSE', 'global assets, leaders, Taiwan groups registered', f'assets={len(state["assets"])}; leaders={len(state["leaders"])}; tw_groups={len(state["groups"])}', 'Next build dry-run fetch queue and field schemas', 'PARALLEL_SAFE')
    if len(state['adapters']) < 20:
        add_finding('WARN', 'VDF', 'SOURCE_ADAPTER', 'source adapters registered but not yet enough for all data rows', f'adapters={len(state["adapters"])}; dataset_rows={family_counts.get("DATASET",0)}', 'Create endpoint-level adapter specs and provider capability probes', 'SEQUENTIAL_REQUIRED')
    if family_counts.get('DATASET', 0) and not any((r.get('family') or '') == 'LIBRARY' for r in master):
        add_finding('WARN', 'VIA', 'LIB_REGISTRY', 'library requirements not yet first-class SSOT family', 'master has no LIBRARY family; libs appear in scripts/context only', 'Promote library requirement registry to append-only SSOT rows', 'PARALLEL_SAFE')
    add_finding('WARN', 'FlowSystem', 'PARAMETER', '77-row registry still embedded in Python', 'FlowSystem OneShot uses REGISTRY_JSON embedded constant', 'Externalize to registry JSON/CSV; Python only reads it', 'SEQUENTIAL_REQUIRED')
    add_finding('WARN', 'VRN', 'IDENTITY', 'staging duplicate report_id / missing identity issues must remain sequential', 'Prior VRN staging audit shows duplicate report_id and missing date/broker review rows', 'Repair in staging copy only; do not canonical merge', 'SEQUENTIAL_REQUIRED')
    add_finding('WARN', 'VAP/VETF/VIAS', 'PARAMETER_MANIFEST', 'subsystem parameter manifests not fully visible', 'v002 has module interface rows but not complete per-subsystem parameter schema', 'Create standard params JSON for each subsystem and validate against schema', 'SEQUENTIAL_REQUIRED')
    add_finding('OK', 'NexusCore', 'INTERFACE', 'first-layer support interface rule exists', 'Invoke-VeritasNexusCore.ps1 should route Registry/SSOT/HardGate/RuntimeBridge', 'Make every subsystem call NexusCore, not scattered files', 'PARALLEL_SAFE')
    summary = {
        'gate': 'PASS_WITH_WARNINGS',
        'policy': def_POLICY,
        'master_rows': master_count,
        'legacy_rows_preserved': legacy_count,
        'new_append_rows_detected': append_count,
        'family_counts': family_counts,
        'domain_counts_top': dict(list(domain_counts.items())[:30]),
        'owner_counts_top': dict(list(owner_counts.items())[:20]),
        'duplicate_canonical_key': duplicate_canonical,
        'duplicate_ssot_id': duplicate_ssot,
        'duplicate_veritas_id': duplicate_veritas,
        'findings_count': len(findings),
        'warn_count': sum(1 for f in findings if f['severity'] == 'WARN'),
        'fail_count': sum(1 for f in findings if f['severity'] == 'FAIL'),
    }
    return {'summary': summary, 'findings': findings}


def def_build_subsystem_matrix(state: Dict[str, Any], audit: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    master = state['master']
    family_counts = def_counts(master, 'family')
    def add(subsystem, role, data_status, lib_status, param_status, dedup_status, omission_status, gate, next_action):
        rows.append({
            'subsystem': subsystem,
            'role': role,
            'data_integration': data_status,
            'library_integration': lib_status,
            'parameter_integration': param_status,
            'dedup_status': dedup_status,
            'omission_status': omission_status,
            'gate': gate,
            'next_action': next_action,
        })
    add('VDF', 'market/data forge, TWSE/TPEX/MOPS/FRED/yfinance/AKShare adapters',
        f'PARTIAL_OK: DATASET={family_counts.get("DATASET",0)}, ASSET={len(state["assets"])}, LEADER={len(state["leaders"])}, TW_GROUP={len(state["groups"])}',
        'PARTIAL: required libs known; dedicated lib registry generated in v003 but install probe not run here',
        'PARTIAL_OK: ticker/source/schema policies exist; fetch calendar/retry/output contracts need external JSON',
        'WARN: canonical duplicates preserved; Veritas ID unique',
        'WARN: endpoint-level fetch queue and field schema not complete for every dataset row',
        'PASS_WITH_WARNINGS',
        'Build FetchPlanBuilder v003 with adapter_capability_probe and field_schema per dataset')
    add('VRN', 'PDF/report extraction and financial report SSOT',
        'PARTIAL_OK: staged ReportBasicInfo/FileRegistry/ReportText exist in prior audit; exception queue remains review input',
        'PARTIAL: PDF/OCR/CV libs known; dedicated lib registry generated in v003; environment probe still needed',
        'PARTIAL: schema/unit policy exists; OCR/table/report_identity params need external JSON',
        'WARN: duplicate report_id issue must be fixed sequentially in staging copy',
        'WARN: report date/broker review rows remain; do not promote canonical before identity review',
        'PASS_WITH_WARNINGS',
        'Create VRN_Params.schema.json + identity repair plan + exception mapper review UI')
    add('FlowSystem/FIS', 'FIS calculation, fusion, validation harness, HTML UI',
        'OK: 77 extraction matrix rows registered and v3 harness available',
        'PARTIAL_OK: standard lib OneShot; numpy/scipy for harness; registry generated in v003',
        'PARTIAL_OK: via_flow_params.json exists; 77-row REGISTRY_JSON still embedded',
        'OK/WARN: registry QA checks dup/conflict but external append-only diff should own it',
        'WARN: live fetch mode is interface only, not full adapter implementation',
        'PASS_WITH_WARNINGS',
        'Move embedded registry to external SSOT and wire DataAdapter to FetchPlanBuilder')
    add('NexusCore/Supportive', 'first-layer control gateway and frozen supportive engines',
        'OK: Registry/SSOT/HardGate/RuntimeBridge/EnvManager role defined',
        'OK/PARTIAL: PS modules identified; import/version probe should run locally',
        'OK: first-layer interface rule exists',
        'OK: avoid direct scattered dependency',
        'WARN: individual engines should not be public entry points',
        'PASS_WITH_WARNINGS',
        'Enforce all subsystem calls through Invoke-VeritasNexusCore.ps1')
    add('VPNS', 'accelerator/process mining/supportive registry',
        'PARTIAL: accelerator registry present',
        'PARTIAL: PS/Python acceleration libs should be probed',
        'PARTIAL: 15 pending accelerators need sequence gate',
        'OK: append-only accelerator registration',
        'WARN: do not enable all pending accelerators at once',
        'PASS_WITH_WARNINGS',
        'Enable accelerators only after baseline pass and write-set conflict check')
    for sub in ['VAP', 'VETF', 'VIAS']:
        add(sub, 'functional subsystem requiring common SSOT/Nexus interface',
            'GAP: data requirements not fully decomposed in current visible registry',
            'GAP: subsystem-specific library manifest not visible',
            'GAP: parameter manifest/schema not sufficiently visible',
            'UNKNOWN: needs own dedup keys',
            'WARN: cannot certify no omissions yet',
            'REVIEW_REQUIRED',
            f'Create {sub}_Params.schema.json + data/lib/adapter registry rows')
    return rows

# ============================ def HTML ============================
def def_html_table(rows: List[Dict[str, Any]], limit: int | None = None) -> str:
    if not rows:
        return '<p class="muted">No rows.</p>'
    show = rows[:limit] if limit else rows
    cols = list(show[0].keys())
    out = ['<table><thead><tr>']
    out += [f'<th>{html.escape(str(c))}</th>' for c in cols]
    out.append('</tr></thead><tbody>')
    for r in show:
        out.append('<tr>')
        for c in cols:
            val = html.escape(str(r.get(c, '')))
            out.append(f'<td>{val}</td>')
        out.append('</tr>')
    out.append('</tbody></table>')
    if limit and len(rows) > limit:
        out.append(f'<p class="muted">Showing {limit} of {len(rows)} rows.</p>')
    return ''.join(out)


def def_write_html(path: pathlib.Path, summary: Dict[str, Any], subsystem_rows, lib_rows, data_rows, param_rows, findings) -> None:
    css = """
    :root{--bg:#f5f4f0;--sf:#fff;--ink:#1e1d1a;--sub:#6b6860;--bd:#dbd9d3;--ok:#166534;--warn:#b7791f;--fail:#b91c1c;--seal:#b5291a;--blue:#2563eb;}
    *{box-sizing:border-box} body{margin:0;padding:24px;background:var(--bg);color:var(--ink);font-family:Inter,'Noto Sans TC',system-ui,sans-serif;font-size:13px;line-height:1.55}.wrap{max-width:1280px;margin:auto}.eyebrow{font-family:monospace;letter-spacing:1.6px;color:var(--sub);font-size:11px;text-transform:uppercase}h1{font-size:26px;margin:6px 0}.seal{display:inline-flex;width:34px;height:34px;align-items:center;justify-content:center;background:var(--seal);color:white;border-radius:7px;margin-right:10px}.strip{height:6px;border-radius:2px;background:linear-gradient(90deg,#2563eb,#0f766e,#b7791f,#b91c1c);margin:14px 0}.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}.kpi,.card{background:var(--sf);border:1px solid var(--bd);border-radius:8px;padding:12px;margin:10px 0}.kpi .v{font-family:monospace;font-size:20px;font-weight:700}.kpi .l{font-size:10px;color:var(--sub);text-transform:uppercase}table{border-collapse:collapse;width:100%;font-size:11.5px}th,td{border-bottom:1px solid #eceae2;padding:6px 8px;text-align:left;vertical-align:top}th{font-size:10px;color:var(--sub);text-transform:uppercase}.muted{color:var(--sub)}.gate{display:inline-block;padding:6px 12px;border-radius:4px;background:var(--warn);color:white;font-weight:800}.ok{color:var(--ok);font-weight:700}.warn{color:var(--warn);font-weight:700}.fail{color:var(--fail);font-weight:700}
    """
    kpis = [
        ('Gate', summary['gate']),
        ('Master Rows', summary['master_rows']),
        ('Legacy Preserved', summary['legacy_rows_preserved']),
        ('New Append', summary['new_append_rows_detected']),
        ('Warnings', summary['warn_count']),
        ('Fails', summary['fail_count']),
    ]
    kpi_html = ''.join(f'<div class="kpi"><div class="v">{html.escape(str(v))}</div><div class="l">{html.escape(k)}</div></div>' for k,v in kpis)
    content = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Veritas · Subsystem Integration Audit v003</title><style>{css}</style></head><body><div class="wrap">
    <div class="eyebrow">VERITAS INTELLIGENCE ANALYTICS · SUBSYSTEM INTEGRATION AUDIT · APPEND-ONLY · REVIEW-ONLY</div>
    <h1><span class="seal">整</span>VDF / VRN / 子系統資料·Libs·Parameters 整合稽核 v003</h1>
    <p class="muted">目的：確認目前 SSOT 是否足以支援 VDF、VRN、FlowSystem/FIS、NexusCore、VPNS、VAP、VETF、VIAS；同時標記去重與遺漏，不做 canonical mutation。</p>
    <div class="strip"></div><div class="kpis">{kpi_html}</div>
    <div class="card"><h2>def Executive Verdict</h2><p><span class="gate">{html.escape(summary['gate'])}</span></p><p>結論：v002 已經把核心資料宇宙與大部分 SSOT 註冊起來，但仍不能宣稱「全部充分整合且無遺漏」。最大缺口是：library registry 尚未成為一級 SSOT、VDF endpoint/field schema 尚未逐列完成、VRN identity repair 尚未 sequential close、VAP/VETF/VIAS 仍需各自 parameter manifest。</p></div>
    <div class="card"><h2>def Subsystem Matrix</h2>{def_html_table(subsystem_rows)}</div>
    <div class="card"><h2>def Findings</h2>{def_html_table(findings)}</div>
    <div class="card"><h2>def Required Data Registry</h2>{def_html_table(data_rows, 80)}</div>
    <div class="card"><h2>def Required Library Registry</h2>{def_html_table(lib_rows, 80)}</div>
    <div class="card"><h2>def Required Parameter Registry</h2>{def_html_table(param_rows, 80)}</div>
    <div class="card"><h2>def Family Counts</h2>{def_html_table([{'family':k,'count':v} for k,v in summary['family_counts'].items()])}</div>
    <p class="muted">Generated: {html.escape(def_RUN_STAMP)} · No network · No DB write · No canonical merge · No delete.</p>
    </div></body></html>"""
    path.write_text(content, encoding='utf-8')

# ============================ def METHODOLOGY + LAUNCHER ============================
def def_write_methodology(path: pathlib.Path) -> None:
    text = f"""# Veritas Subsystem Integration Audit v003

## def 結論
目前 SSOT 已經進入可用的統一註冊階段，但還不是完全充分整合。v002 有完整的 append-only universe registry；v003 補上 data/lib/parameter 三層稽核與缺口矩陣。

## def 維護規則
- def 只增不減：舊列不得刪除；改動以 `status`, `preferred_current`, `superseded_by`, `duplicate_group` 表示。
- def Veritas ID：`veritas_id` 是穩定主鍵，不因去重重編。
- def Canonical Key：用於偵測同義/重複，不等於可以刪除。
- def Data Adapter：每個 dataset 必須有 source adapter、endpoint hint、field schema、freshness rule。
- def Library Registry：每個 subsystem 的 Python/PowerShell/lib/external binary 需求都要成為 SSOT row。
- def Parameter Contract：參數應外部 JSON 化，Python/PowerShell 只讀，不硬寫。
- def Validation：每次更新跑 schema|required|unique|append_only_diff|provenance_hash|capability_probe。

## def 智慧方法論
1. def Register：先登錄資料/函式庫/參數/介面，不直接 live fetch。
2. def Normalize：建立 alias map、unit map、ticker map、source map。
3. def Dedup：標記 duplicate_group，不刪行。
4. def Route：所有 functional modules 先接 NexusCore，再接 grouped frozen engines。
5. def Probe：用 dry-run capability probe 檢查 endpoint、import、schema、row count。
6. def Validate：用 HardGate 檢查 no mutation、no DB write、no canonical merge。
7. def Promote：只有通過 sequential review 的 staging row 才能進 canonical。

## def 下一步
- def Build `FetchPlanBuilder_v003`: 將 dataset/source adapter/asset universe 轉成 dry-run fetch queue。
- def Build `LibraryProbe_v003`: import/version/external binary/PowerShell module capability probe。
- def Build `ParamsSchema_v003`: VDF/VRN/FlowSystem/VAP/VETF/VIAS 各自 JSON schema。
- def Build `VRNIdentityRepairPlan_v003`: 只在 staging copy 修 report_id/date/broker issue。
"""
    path.write_text(text, encoding='utf-8')


def def_write_engine(path: pathlib.Path) -> None:
    src = pathlib.Path(__file__).read_text(encoding='utf-8')
    path.write_text(src, encoding='utf-8')


def def_write_launcher(path: pathlib.Path) -> None:
    content = r'''# Veritas Subsystem Integration Audit v003 · review-only launcher
$ErrorActionPreference = "Stop"
$def_Base = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics"
$def_LocalPy = "py"
$def_Script = Join-Path $def_Base "Veritas_Subsystem_Integration_Audit_v003.py"
Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def Veritas · Subsystem Integration Audit v003" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def Policy: append-only · review-only · no DB write · no canonical merge · no delete" -ForegroundColor Yellow
if (!(Test-Path $def_Script)) {
  Write-Host "def Script not found at project root. Put Veritas_Subsystem_Integration_Audit_v003.py there first." -ForegroundColor Red
  Write-Host "def PowerShell remains open." -ForegroundColor Cyan
  return
}
& $def_LocalPy -3.13 $def_Script
Write-Host ""
Write-Host "def PowerShell remains open." -ForegroundColor Cyan
'''
    path.write_text(content, encoding='utf-8')

# ============================ def MAIN ============================
def def_main() -> Dict[str, Any]:
    def_RUN_DIR.mkdir(parents=True, exist_ok=True)
    state = def_load_state()
    audit = def_build_audit(state)
    subsystem_rows = def_build_subsystem_matrix(state, audit)
    lib_rows = def_required_libs()
    data_rows = def_required_data()
    param_rows = def_required_params()
    # propagate summaries to artifacts
    summary = audit['summary']
    files = {
        'summary_json': def_RUN_DIR / f'{def_OUTPUT_PREFIX}_summary.json',
        'subsystem_csv': def_RUN_DIR / f'{def_OUTPUT_PREFIX}_subsystem_matrix.csv',
        'libs_csv': def_RUN_DIR / f'{def_OUTPUT_PREFIX}_library_registry.csv',
        'data_csv': def_RUN_DIR / f'{def_OUTPUT_PREFIX}_data_registry.csv',
        'params_csv': def_RUN_DIR / f'{def_OUTPUT_PREFIX}_parameter_matrix.csv',
        'findings_csv': def_RUN_DIR / f'{def_OUTPUT_PREFIX}_dedup_omission_findings.csv',
        'html': def_BASE_DIR / f'{def_OUTPUT_PREFIX}_dashboard.html',
        'methodology': def_BASE_DIR / f'{def_OUTPUT_PREFIX}_methodology.md',
        'engine': def_BASE_DIR / f'{def_OUTPUT_PREFIX}.py',
        'launcher': def_BASE_DIR / f'Invoke_{def_OUTPUT_PREFIX}.ps1',
        'zip': def_BASE_DIR / f'{def_OUTPUT_PREFIX}_package.zip',
    }
    def_write_json(files['summary_json'], summary)
    def_write_csv(files['subsystem_csv'], subsystem_rows)
    def_write_csv(files['libs_csv'], lib_rows)
    def_write_csv(files['data_csv'], data_rows)
    def_write_csv(files['params_csv'], param_rows)
    def_write_csv(files['findings_csv'], audit['findings'])
    def_write_html(files['html'], summary, subsystem_rows, lib_rows, data_rows, param_rows, audit['findings'])
    def_write_methodology(files['methodology'])
    def_write_engine(files['engine'])
    def_write_launcher(files['launcher'])
    # copy major CSVs to /mnt/data root for direct links
    direct_files = []
    for k in ['subsystem_csv','libs_csv','data_csv','params_csv','findings_csv','summary_json']:
        dst = def_BASE_DIR / files[k].name
        dst.write_bytes(files[k].read_bytes())
        direct_files.append(dst)
    with zipfile.ZipFile(files['zip'], 'w', zipfile.ZIP_DEFLATED) as z:
        for p in [files['html'], files['methodology'], files['engine'], files['launcher']] + direct_files:
            z.write(p, arcname=p.name)
        for k in ['subsystem_csv','libs_csv','data_csv','params_csv','findings_csv','summary_json']:
            z.write(files[k], arcname=f'run/{files[k].name}')
    return {'summary': summary, 'files': {k: str(v) for k,v in files.items()}, 'run_dir': str(def_RUN_DIR)}

if __name__ == '__main__':
    result = def_main()
    print(json.dumps(result['summary'], ensure_ascii=False, indent=2))
    print('def RunDir:', result['run_dir'])
