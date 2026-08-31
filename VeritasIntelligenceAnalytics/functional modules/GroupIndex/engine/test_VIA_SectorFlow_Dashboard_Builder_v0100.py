# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import importlib.util
import json
import re
import sys

MODULE_PATH = Path(__file__).with_name("VIA_SectorFlow_Dashboard_Builder_v0100.py")
SPEC = importlib.util.spec_from_file_location("via_sectorflow_dashboard_v0100", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_payload_contract() -> None:
    payload = MODULE.def_build_payload()
    assert len(payload["groups"]) >= 10
    assert set(payload["index"].keys()) == set(payload["groups"])
    assert set(payload["flows"].keys()) == set(payload["groups"])
    assert len(payload["heat"]["rows"]) == len(payload["groups"])
    assert payload["rrg"], "RRG points missing"
    assert payload["trades"], "trade ledger empty"
    assert payload["gov"]["testsF"] and payload["gov"]["testsB"]
    # JSON 可序列化(無 NaN/Timestamp 洩漏)。
    text = json.dumps(payload, ensure_ascii=False)
    assert "NaN" not in text


def test_dashboard_html_self_contained() -> None:
    out = MODULE.DEFAULT_OUT
    assert out.exists(), "run builder first"
    html = out.read_text("utf-8")
    for tab in ["總覽", "名單", "鏈接指數", "資金位移", "輪動象限", "交易回測", "治理矩陣"]:
        assert tab in html, tab
    # 名單與詳細結果矩陣required tokens
    for token in ["sec-roster", "ro-table", "gv-detect", "gv-tradebt", "gv-m", "gv-etf", "gv-env",
                  '"members":', '"suite":', "詳細結果矩陣"]:
        assert token in html, token
    # 零外部資產:無 http(s) 連結的 script/link/img。
    assert not re.search(r'<(script|link|img)[^>]+(src|href)="https?://', html)
    # 資料已嵌入。
    assert '"groups":' in html and '"tradeBacktest":' in html
    # 免責與受控標示常駐。
    assert "非實盤" in html and "非投資建議" in html
