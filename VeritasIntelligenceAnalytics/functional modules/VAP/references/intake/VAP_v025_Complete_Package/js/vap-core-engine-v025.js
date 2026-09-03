(function (root, factory) {
  const api = factory(root);
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.VAPCoreEngine = Object.freeze(api);
})(typeof globalThis !== 'undefined' ? globalThis : this, function (root) {
  'use strict';

  // def 01 PARAMETERS
  const VERSION = 'v025';
  const SCHEMA = 'VIA-VAP-CORE-ENGINE/1.0';
  const HEIGHT_MULTIPLIERS = Object.freeze([0.5, 0.75, 1, 1.25, 1.5, 2, 2.5, 3, 4]);
  const VOLUME_PATTERN = /volume|turnover|成交量|成交值/i;
  const PRICE_PATTERN = /adj[_ ]?(open|high|low|close)|open|high|low|close|price|價格|收盤/i;

  // def 02 CANONICAL CONTRACT
  function def_canonicalize(value) {
    if (Array.isArray(value)) return value.map(def_canonicalize);
    if (value && typeof value === 'object') {
      return Object.keys(value).sort().reduce((output, key) => {
        if (value[key] !== undefined) output[key] = def_canonicalize(value[key]);
        return output;
      }, {});
    }
    return value;
  }
  function def_canonical_json(value) { return JSON.stringify(def_canonicalize(value)); }
  async function def_sha256_text(value) {
    if (!root.crypto || !root.crypto.subtle) throw new Error('WEB_CRYPTO_REQUIRED');
    const bytes = new TextEncoder().encode(String(value));
    const digest = await root.crypto.subtle.digest('SHA-256', bytes);
    return [...new Uint8Array(digest)].map(item => item.toString(16).padStart(2, '0')).join('');
  }
  function def_safe_identifier(value, fallback) {
    const cleaned = String(value || '').replace(/[^0-9A-Za-z_\-\u4e00-\u9fff]+/g, '_').replace(/^_+|_+$/g, '');
    return cleaned.slice(0, 96) || fallback || 'VAP_ITEM';
  }

  // def 03 DATA SEMANTICS
  function def_infer_semantic(field) {
    const name = String(field || '');
    if (/date|datetime|timestamp|time|period|日期|時間/i.test(name)) return { subject: name, unit: 'Date', dataType: 'Date', role: 'X_TIME', aggregation: 'NONE' };
    if (VOLUME_PATTERN.test(name)) return { subject: name, unit: 'Shares', dataType: 'Integer', role: 'RIGHT_VALUE', aggregation: 'SUM' };
    if (/pct|percent|percentage|rate|yield|ratio|報酬率|殖利率|比率/i.test(name)) return { subject: name, unit: '%', dataType: 'Percentage', role: 'LEFT_VALUE', aggregation: 'LAST' };
    if (PRICE_PATTERN.test(name)) return { subject: name, unit: 'TWD', dataType: 'Currency', role: 'LEFT_VALUE', aggregation: 'LAST' };
    return { subject: name, unit: 'Unitless', dataType: 'Number', role: 'LEFT_VALUE', aggregation: 'LAST' };
  }
  function def_fill_missing(values, semantic) {
    const input = Array.from(values || []);
    const isVolume = semantic === 'volume' || VOLUME_PATTERN.test(String(semantic || ''));
    const output = [];
    let prior = null;
    for (const value of input) {
      const missing = value === null || value === undefined || value === '' || (typeof value === 'number' && !Number.isFinite(value));
      if (isVolume) output.push(missing ? 0 : Number(value));
      else {
        const next = missing ? prior : Number(value);
        output.push(Number.isFinite(next) ? next : null);
        if (Number.isFinite(next)) prior = next;
      }
    }
    return output;
  }
  function def_next_target_day(sourceDay, targetDays) {
    const source = String(sourceDay);
    return [...targetDays].map(String).sort().find(day => day > source) || null;
  }
  function def_align_us_to_next_tw(sourceRows, targetDays, dateField) {
    const dateKey = dateField || 'date';
    return (sourceRows || []).map(row => {
      const target = def_next_target_day(row[dateKey], targetDays);
      return target ? { ...row, sourceDate: row[dateKey], [dateKey]: target, timingPolicy: 'US_T_TO_NEXT_TW_TRADING_DAY' } : null;
    }).filter(Boolean);
  }

  // def 04 STACK AND REFRESH
  function def_common_stack_labels(records) {
    if (!records || !records.length) return [];
    let common = new Set(records[0].labels || []);
    for (const record of records.slice(1)) common = new Set((record.labels || []).filter(label => common.has(label)));
    return (records[0].labels || []).filter(label => common.has(label));
  }
  function def_normalize_height(value) {
    const numeric = Number(value);
    return HEIGHT_MULTIPLIERS.reduce((best, item) => Math.abs(item - numeric) < Math.abs(best - numeric) ? item : best, 1);
  }
  function def_stack_panel_heights(records, baseHeight) {
    const base = [240, 280, 320, 360].includes(Number(baseHeight)) ? Number(baseHeight) : 280;
    return (records || []).map(record => Math.round(base * def_normalize_height(record.heightMultiple || 1)));
  }
  function def_dedupe_saved_images(records) {
    const seen = new Set();
    return (records || []).filter(record => {
      const key = record.savedImageId || record.id || def_canonical_json(record);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }
  function def_build_refresh_request(targets, mode, requestId) {
    const normalizedTargets = [...new Set((targets || []).map(String).filter(Boolean))];
    return {
      schema: 'VIA-VAP-REFRESH-REQUEST/1.0',
      version: VERSION,
      requestId: def_safe_identifier(requestId, 'VAP-REFRESH-' + Date.now()),
      targets: normalizedTargets.length ? normalizedTargets : ['ALL'],
      mode: String(mode || 'INCREMENTAL').toUpperCase() === 'FULL' ? 'FULL' : 'INCREMENTAL',
      readOnly: true,
      requestedAt: new Date().toISOString()
    };
  }
  function def_self_test() {
    const checks = {
      canonical: def_canonical_json({ b: 2, a: 1 }) === '{"a":1,"b":2}',
      priceForwardFill: def_fill_missing([10, null, 12], 'close').join('|') === '10|10|12',
      volumeZeroFill: def_fill_missing([10, null, 12], 'volume').join('|') === '10|0|12',
      nextTradingDay: def_next_target_day('2026-01-02', ['2026-01-02', '2026-01-05']) === '2026-01-05',
      strictCommonTime: def_common_stack_labels([{ labels: ['a', 'b'] }, { labels: ['b', 'c'] }]).join('') === 'b',
      standardHeights: def_stack_panel_heights([{ heightMultiple: 0.5 }, { heightMultiple: 2 }], 280).join('|') === '140|560'
    };
    return { schema: SCHEMA, version: VERSION, status: Object.values(checks).every(Boolean) ? 'PASS' : 'FAIL', checks };
  }
  return {
    VERSION, SCHEMA, HEIGHT_MULTIPLIERS,
    canonicalize: def_canonicalize,
    canonicalJson: def_canonical_json,
    sha256Text: def_sha256_text,
    safeIdentifier: def_safe_identifier,
    inferSemantic: def_infer_semantic,
    fillMissing: def_fill_missing,
    nextTargetDay: def_next_target_day,
    alignUsToNextTw: def_align_us_to_next_tw,
    commonStackLabels: def_common_stack_labels,
    normalizeHeight: def_normalize_height,
    stackPanelHeights: def_stack_panel_heights,
    dedupeSavedImages: def_dedupe_saved_images,
    buildRefreshRequest: def_build_refresh_request,
    selfTest: def_self_test
  };
});
