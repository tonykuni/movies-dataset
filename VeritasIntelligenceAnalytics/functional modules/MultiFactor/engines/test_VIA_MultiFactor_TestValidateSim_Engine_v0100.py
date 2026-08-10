#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import importlib.util
import json
import tempfile
import sys
from pathlib import Path

ENGINE_PATH = Path('/mnt/data/VIA_MultiFactor_TestValidateSim_Engine_v0100.py')

spec = importlib.util.spec_from_file_location('via_engine', ENGINE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def test_demo_panel_shape():
    df = mod.generate_demo_panel(n=360, seed=123)
    assert 'date' in df.columns
    assert mod.TARGET_DEFAULT in df.columns
    assert len(df) == 360
    assert len(mod.numeric_factor_columns(df, mod.TARGET_DEFAULT)) >= 6


def test_engine_run_outputs():
    with tempfile.TemporaryDirectory() as td:
        args = mod.parse_args(['--out-base', td, '--demo-rows', '420', '--seed', '123'])
        summary = mod.run_engine(args)
        run_dir = Path(summary['run_dir'])
        required = [
            'engine_summary.json',
            'factor_relation_ledger.csv',
            'anti_validation_ledger.csv',
            'resonance_matrix.csv',
            'hidden_factor_ledger.csv',
            'simulation_ledger.csv',
            'model_permission_ledger.csv',
            'index.html',
        ]
        for name in required:
            assert (run_dir / name).exists(), name
        data = json.loads((run_dir / 'engine_summary.json').read_text(encoding='utf-8'))
        assert data['high_confidence_engine_execution'] is True
        assert data['n_factors'] >= 6
        assert data['outputs']['html_report'] == 'index.html'


def test_projection_not_confirmed_in_outputs():
    with tempfile.TemporaryDirectory() as td:
        args = mod.parse_args(['--out-base', td, '--demo-rows', '420', '--seed', '456'])
        summary = mod.run_engine(args)
        run_dir = Path(summary['run_dir'])
        text = (run_dir / 'simulation_ledger.csv').read_text(encoding='utf-8')
        assert 'Estimated_Model_NotConfirmed' in text

if __name__ == '__main__':
    test_demo_panel_shape()
    test_engine_run_outputs()
    test_projection_not_confirmed_in_outputs()
    print('ALL_TESTS_PASS')
