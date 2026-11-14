#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL279_MCPServer v0103 — 薄尾(v0102 一字不動):MCP 多露 2026-11-12 這一輪的收據(全部只讀 · 零寫入 · 零網路)。

操作員 2026-11-12:「用最好的版本 · 桌機用 MCP 去連結」。.mcp.json 改指本版(VCGC 只讀 MCP 的尾版),本版只加資源,不加動詞、不改協定:
  agentos/activation     Agent OS 併入 VCGC 的逐項啟用矩陣(CGC_MDL280 activate · 27 工具 + 14 動詞 + MCP 握手 + 中央冊條目 + Graphify)
  agentos/register       VCGC 的 Agent OS 整合冊(27 工具 · 動詞 · 模組 · 正則 · 同義字的穩定 ID)
  vrn2/nonstock-matrix   VRN-2 非個股車道矩陣(一檔一列 · 原句驗證 · 狀態)
  validate/desktop       桌機唯讀驗證收據(VIA_DesktopValidate:三管理器 · 清單股數 · 持股率 · VRN 燈 · VQG 指標冊)
用法同 v0101:--serve [--root] · --client-config [--root] · --selftest(先 v0102 鏈,再本版 3 項)。
"""
from __future__ import annotations
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import importlib.util
import json
import re
import sys
from pathlib import Path

NAME = "CGC_MDL279_MCPServer"
VERSION = "v0103"
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


_PRIOR_FILE = max((p for p in HERE.glob(NAME + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(NAME + "_prior_for_v0103", _PRIOR_FILE)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
P0 = PRIOR.P0                                 # v0100 本體(Server · tool_specs · resource_specs · RECEIPTS)

NEW_RECEIPTS_0103 = {
    "agentos/activation": "VIA_Reports/vcgc/agentos/AOS_ACTIVATION_latest.json",
    "agentos/register": "supportive modules/registry/VIA_VCGC_AgentOS_Integration_SSOT_v0100.json",
    "vrn2/nonstock-matrix": "VIA_Reports/vrn2/nonstock/NONSTOCK_MATRIX.json",
    "validate/desktop": "VIA_Reports/validate/VIA_DesktopValidate_latest.json",
}
_PRIOR_KEYS = set(P0.RECEIPTS)
P0.RECEIPTS.update(NEW_RECEIPTS_0103)
P0.VERSION = VERSION
RECEIPTS, READ_VERBS, PROTOCOL = P0.RECEIPTS, P0.READ_VERBS, P0.PROTOCOL


def client_config(via: Path) -> dict:
    cfg = PRIOR.client_config(via)
    text = json.dumps(cfg, ensure_ascii=False).replace(str(_PRIOR_FILE), str(Path(__file__).resolve())).replace(_PRIOR_FILE.name, Path(__file__).name)
    return json.loads(text)


def selftest() -> int:
    import tempfile
    added = [k for k in NEW_RECEIPTS_0103 if k not in _PRIOR_KEYS]
    for k in added:                                   # 前版自測數資源數要原樣 → 先拿掉本版的 key,跑完再掛回
        P0.RECEIPTS.pop(k, None)
    try:
        rc = PRIOR.selftest()
    finally:
        P0.RECEIPTS.update(NEW_RECEIPTS_0103)
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))
    with tempfile.TemporaryDirectory(prefix="via_mcp103_") as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        (via / "VIA_Reports" / "vcgc" / "agentos").mkdir(parents=True)
        (via / "VIA_Reports" / "vcgc" / "agentos" / "AOS_ACTIVATION_latest.json").write_text('{"lamp": "YELLOW", "tally": {"GREEN": 57}}', encoding="utf-8")
        srv = P0.Server(via, None)
        res = {r["name"] for r in P0.resource_specs(via)}
        chk("ⓐ 資源列 %d 份 = 前版 %d + 本版新 %d · 新 key 全在 · via_receipt enum 含新 key" % (len(res), len(_PRIOR_KEYS), len(added)),
            len(res) == len(_PRIOR_KEYS) + len(added) and set(NEW_RECEIPTS_0103) <= res
            and set(NEW_RECEIPTS_0103) <= set(next(t for t in P0.tool_specs() if t["name"] == "via_receipt")["inputSchema"]["properties"]["key"]["enum"]))
        rr = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "resources/read", "params": {"uri": "via://agentos/activation"}})["result"]["contents"][0]
        miss = srv.handle({"jsonrpc": "2.0", "id": 2, "method": "resources/read", "params": {"uri": "via://validate/desktop"}})["result"]["contents"][0]
        chk("ⓑ 讀新資源:啟用矩陣讀到(綠 57)· 沒有的(validate/desktop)照實說還沒有不炸", '"GREEN": 57' in rr["text"] and "還沒有" in miss["text"])
        cfg = client_config(via)
        chk("ⓒ client-config 的 command 指到本檔(v0103)", Path(__file__).name in json.dumps(cfg) and _PRIOR_FILE.name not in json.dumps(cfg))
    bad = len(ok) - sum(ok)
    print("[%s] %s %s --selftest · 本版 %d 項 · 不過 %d(v0102 鏈 rc %d)" % ("PASS" if not bad and rc == 0 else "FAIL", NAME, VERSION, len(ok), bad, rc), flush=True)
    return 0 if not bad and rc == 0 else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args or (args and args[0] in ("selftest", "test")):
        return selftest()
    if "--client-config" in args:
        root = args[args.index("--root") + 1] if "--root" in args else None
        via = Path(root).resolve() if root else P0.VIA_DEFAULT
        if (via / "VeritasIntelligenceAnalytics").is_dir():
            via = via / "VeritasIntelligenceAnalytics"
        print(json.dumps(client_config(via), ensure_ascii=False, indent=2))
        return 0
    return P0.main(args)


def __getattr__(name):
    return getattr(PRIOR, name)


if __name__ == "__main__":
    sys.exit(main())
