# -*- coding: utf-8 -*-
"""pytest 入口:把引擎的離線自測掛成一個測試(不連網、不碰真實設定檔)。
   直接跑:python3 VIA_MCP_Engine_v0101.py selftest    或    python3 -m pytest VIA_MCP_Engine/tests -q
"""
import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("via_mcp_engine", HERE / "VIA_MCP_Engine_v0101.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["via_mcp_engine"] = mod
spec.loader.exec_module(mod)  # type: ignore[union-attr]


def test_selftest_passes():
    assert mod.selftest() == 0


def test_limit_is_five():
    assert mod.MAX_SERVERS_PER_PLATFORM == 5


def test_no_plaintext_secret_mode():
    api = mod.Api()
    code, _ = api.handle("POST", "/api/secret-mode", {}, {"mode": "plain"})
    assert code == 400


if __name__ == "__main__":
    sys.exit(mod.selftest())
