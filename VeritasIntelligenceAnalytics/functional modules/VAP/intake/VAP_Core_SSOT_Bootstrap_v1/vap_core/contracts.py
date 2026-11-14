"""SSOT-driven configuration foundation; not an analytics or rendering engine.

Authoritative v1 JSON is never modified. Renderer verification requires a separate
future evidence-backed plugin registry; a chart declaration is not executable.
"""
from pathlib import Path
import copy
import hashlib
import json
import math
import re


class ContractError(ValueError):
    pass


def _number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _load(path):
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ContractError('Duplicate JSON key: ' + k)
            result[k] = v
        return result
    try:
        return json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=pairs,
                          parse_constant=lambda v: (_ for _ in ()).throw(ContractError('Non-finite JSON: ' + v)))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(str(exc)) from exc


class VAPContracts:
    def __init__(self, root=None):
        self.root = Path(root) if root else Path(__file__).resolve().parents[1]
        self.spec_path = self.root / 'ssot' / 'vap_spec.json'
        self.library_path = self.root / 'ssot' / 'vap_chartlib.json'
        self._spec = _load(self.spec_path)
        self._library = _load(self.library_path)
        self._validate()
        self._charts = {c['code']: copy.deepcopy(c) for g in self._library['groups'] for c in g['charts']}
        self.source_hashes = {
            'spec': hashlib.sha256(self.spec_path.read_bytes()).hexdigest(),
            'chartlib': hashlib.sha256(self.library_path.read_bytes()).hexdigest(),
        }

    @property
    def spec(self):
        return copy.deepcopy(self._spec)

    @property
    def library(self):
        return copy.deepcopy(self._library)

    def _validate(self):
        s, lib = self._spec, self._library
        if not isinstance(s, dict) or s.get('$schema') != 'VIA-VAP-SPEC/1.0':
            raise ContractError('Unsupported spec schema')
        if not isinstance(lib, dict) or lib.get('$schema') != 'VIA-VAP-CHARTLIB/1.0':
            raise ContractError('Unsupported chart library schema')
        try:
            for m in (s['meta'], lib['meta']):
                if not re.fullmatch(r'\d+\.\d+\.\d+', m['version']):
                    raise ContractError('Invalid version')
            if lib['meta']['specRef'] != 'ssot/vap_spec.json':
                raise ContractError('specRef does not resolve to canonical spec')
            for obj in (s, lib):
                if not obj.get('changelog') or not any(c.get('version') == obj['meta']['version'] for c in obj['changelog']):
                    raise ContractError('Missing current-version changelog')
            line = s['line']
            lo, hi = line['widthRange']
            if not all(_number(x) for x in (lo, hi, line['width'], line['widthStep'])) or not 0 < lo <= line['width'] <= hi or line['widthStep'] <= 0:
                raise ContractError('Invalid line width constraints')
            for x in [line['opacity'], *[v for k, v in s['fill'].items() if k != 'note'], s['bar']['edge']['opacity']]:
                if not _number(x) or not 0 <= x <= 1:
                    raise ContractError('Opacity must be finite and within [0,1]')
            if any(not _number(x) or not 0 < x <= 1 for x in s['bar']['gapFactor'].values()):
                raise ContractError('Invalid bar gap factors')
            if any(not _number(x) or x <= 0 for x in s['axis']['tickStepMultiples']):
                raise ContractError('Invalid tick multiples')
            combos = s['palette']['combos']
            if s['palette']['default'] not in combos:
                raise ContractError('Unknown default palette')
            for palette in combos.values():
                if not palette or any(not re.fullmatch(r'#[0-9A-Fa-f]{6}', x) for x in palette):
                    raise ContractError('Invalid palette')
            codes, chart_ids, group_ids = set(), set(), set()
            for group in lib['groups']:
                if group['id'] in group_ids:
                    raise ContractError('Duplicate group id')
                group_ids.add(group['id'])
                for chart in group['charts']:
                    if not re.fullmatch(r'VAP-CH-\d{2}', chart['code']):
                        raise ContractError('Invalid chart code')
                    if chart['code'] in codes or chart['id'] in chart_ids:
                        raise ContractError('Duplicate chart code or id')
                    codes.add(chart['code']); chart_ids.add(chart['id'])
                    if not isinstance(chart['fields'], list) or not chart['fields'] or len(set(chart['fields'])) != len(chart['fields']) or any(not isinstance(x, str) or not x for x in chart['fields']):
                        raise ContractError('Invalid required chart fields')
                    if isinstance(chart['axes'], bool) or chart['axes'] not in (0, 1, 2):
                        raise ContractError('Invalid axis count')
                    for key, value in chart.get('override', {}).items():
                        if key == 'bar.gapFactor':
                            if value not in s['bar']['gapFactor']:
                                raise ContractError('Unknown chart bar gap preset')
                        elif key == 'grid':
                            if not isinstance(value, str) or not re.fullmatch(r'\d+x\d+', value):
                                raise ContractError('Invalid grid override')
                        else:
                            node = s
                            for segment in key.split('.'):
                                node = node[segment]
                            if isinstance(node, (dict, list)) or not _number(value) or not 0 <= value <= 1:
                                raise ContractError('Invalid chart scalar override')
            required = {'VAP-CH-' + str(i).zfill(2) for i in range(1, 29)}
            if not required.issubset(codes):
                raise ContractError('Original chart codes may not be removed')
        except (KeyError, TypeError, IndexError) as exc:
            raise ContractError('Incomplete or malformed SSOT: ' + str(exc)) from exc

    def chart(self, code):
        if code not in self._charts:
            raise ContractError('Chart code not declared: ' + str(code))
        return copy.deepcopy(self._charts[code])

    def resolve(self, code, overrides=None):
        chart = self.chart(code)
        resolved = self.spec
        extension = {}
        used = {}
        # Only library-defined overrides are authoritative in this bootstrap.
        # gapFactor in the library is a named SELECTOR, not replacement of its map.
        for key, value in chart.get('override', {}).items():
            used[key] = value
            if key == 'bar.gapFactor':
                extension['bar_gap_preset'] = value
                extension['bar_gap_factor'] = self._spec['bar']['gapFactor'][value]
            elif key == 'grid':
                extension['grid'] = value
            else:
                node = resolved
                parts = key.split('.')
                for part in parts[:-1]:
                    node = node[part]
                node[parts[-1]] = value
        # Explicit API overrides are intentionally narrow until policy is agreed.
        allowed = {'line.opacity', 'line.width', 'fill.areaUnderLine', 'fill.areaUnderLineWithShadow',
                   'fill.barFace', 'fill.barFaceDense', 'fill.eventBand'}
        for key, value in (overrides or {}).items():
            if key not in allowed:
                raise ContractError('Unregistered user override: ' + key)
            if not _number(value):
                raise ContractError('Override must be finite numeric: ' + key)
            if key == 'line.width':
                # Fixed-width prose and widthRange coexist in v1. Do not silently
                # decide how interactive overrides can relax the fixed-width rule.
                if value != self._spec['line']['width']:
                    raise ContractError('line.width: v1 fixed-width/interactive-range policy unresolved; canonical default only')
            elif not 0 <= value <= 1:
                raise ContractError('Opacity override outside [0,1]: ' + key)
            parent, leaf = key.split('.')
            resolved[parent][leaf] = value
            used[key] = value
        return {
            'chart_code': code, 'chart_definition': chart,
            'spec_version': self._spec['meta']['version'],
            'library_version': self._library['meta']['version'],
            'source_hashes': dict(self.source_hashes),
            'resolved_spec': resolved, 'chart_extensions': extension,
            'parameters_used': used,
            'execution_status': 'declared_only',
            'rendering_verified': False, 'calculation_verified': False,
            'notes': ['Chart rules in prose remain unresolved unless a future renderer explicitly implements and tests them.'],
        }

    def catalog(self):
        return [{
            'code': c['code'], 'id': c['id'], 'name': c['zh'],
            'group_id': g['id'], 'group_name': g['zh'],
            'axes': c['axes'], 'data_shape': c['dataShape'],
            'required_fields': list(c['fields']),
            'declaration_status': 'validated',
            'computation_status': 'not_verified', 'renderer_status': 'not_verified',
            'template_status': 'not_bound',
            'execution_status': 'declared_only',
        } for g in self._library['groups'] for c in g['charts']]

    def report(self):
        catalog = self.catalog()
        return {
            'product': 'VeritasAutoPlot',
            'pipeline': ['data', 'analysis', 'chart', 'analysis_stack', 'template', 'dashboard'],
            'spec_version': self._spec['meta']['version'],
            'library_version': self._library['meta']['version'],
            'source_hashes': dict(self.source_hashes),
            'declared_chart_count': len(catalog),
            'core_contract_status': 'validated',
            'verified_chart_engine_count': 0,
            'scope': 'SSOT contract validation and configuration resolution only; no market analysis or chart execution.',
            'groups': {g['id']: len(g['charts']) for g in self._library['groups']},
            'catalog': catalog,
        }
