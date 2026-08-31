'use strict';
const assert = require('assert');
const core = require('../js/vap-core-engine-v025.js');
const renderer = require('../js/vap-plotly-renderer-v025.js');
const bridge = require('../js/vap-runtime-bridge-v025.js');

// def 01 CORE
assert.equal(core.VERSION, 'v025');
assert.equal(core.selfTest().status, 'PASS');
assert.deepEqual(core.fillMissing([10, null, 12], 'adjClose'), [10, 10, 12]);
assert.deepEqual(core.fillMissing([10, null, 12], 'volume'), [10, 0, 12]);
assert.deepEqual(core.stackPanelHeights([{heightMultiple: 0.5}, {heightMultiple: 1}, {heightMultiple: 2}], 280), [140, 280, 560]);
assert.equal(core.commonStackLabels([{labels: ['a', 'b', 'c']}, {labels: ['b', 'c', 'd']}]).join('|'), 'b|c');
assert.equal(core.alignUsToNextTw([{date: '2026-01-02', value: 1}], ['2026-01-02', '2026-01-05'])[0].date, '2026-01-05');

// def 02 RENDERER
assert.equal(renderer.VERSION, 'v025');
assert.equal(renderer.selfTest().status, 'PASS');
const figure = renderer.buildFigure({title: 'Dual', series: [{x: ['a'], y: [1], axis: 'left'}, {x: ['a'], y: [2], axis: 'right', form: 'bar'}]});
assert.equal(figure.data.length, 2);
assert.equal(figure.layout.yaxis2.side, 'right');
assert.equal(figure.layout.yaxis.tickvals.length, 5);
assert.equal(figure.layout.yaxis2.tickvals.length, 5);
const monthly = {x: Array.from({length: 24}, (_, i) => `${2024 + Math.floor(i / 12)}-${String(i % 12 + 1).padStart(2, '0')}`), y: Array.from({length: 24}, (_, i) => 100 + i)};
const quarterly = renderer.prepareObservationSeries(monthly, {timeRange: 'ALL', frequency: 'quarterly', valueMode: 'level'});
assert.equal(quarterly.x.length, 8);
assert.equal(quarterly.y.at(-1), 123);
const yoy = renderer.prepareObservationSeries(monthly, {timeRange: 'ALL', frequency: 'monthly', valueMode: 'yoy_pct'});
assert.equal(yoy.x.length, 12);
assert.ok(Math.abs(yoy.y[0] - 12) < 1e-9);
const change = renderer.prepareObservationSeries({x: ['2025-01', '2025-02', '2025-03'], y: [100, 110, 121]}, {valueMode: 'change_pct'});
assert.equal(change.y.length, 2);
assert.ok(change.y.every(value => Math.abs(value - 10) < 1e-9));

// def 03 BRIDGE
assert.equal(bridge.VERSION, 'v025');
assert.equal(bridge.selfTest().status, 'PASS');
assert.equal(bridge.endpoint('http://localhost:8765'), 'http://localhost:8765');
assert.throws(() => bridge.endpoint('https://example.com'), /LOOPBACK/);
console.log('VAP_CORE_NODE_TESTS_PASS');
