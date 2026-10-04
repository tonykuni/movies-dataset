#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC v0143. One chain over the v0142 console. It does not apply or delete."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_BODY = HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0142.py"
_spec = importlib.util.spec_from_file_location("vcgc_v0142", _BODY)
body = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = body
_spec.loader.exec_module(body)

ALLOW = {
    "invoke-viaceleritasscoped { via-envgov tools }": "via-envgov tools",
    "via-envgov tools": "via-envgov tools",
}


def next_command(text: str) -> str:
    line = ""
    for raw in text.splitlines():
        if raw.strip().startswith("NEXT:"):
            line = raw.split("NEXT:", 1)[1].strip()
    return ALLOW.get(" ".join(line.lower().split()), "")


def param_ids() -> dict:
    path = body._newest(HERE, "VIA_Central_Params_SSOT_v*.json")
    if not path:
        return {"state": "ABSENT", "books": 0, "missing": 0}
    data = json.loads(path.read_text(encoding="utf-8"))
    books = [x for x in data.get("books") or [] if isinstance(x, dict)]
    missing = [str(x.get("path") or "?") for x in books if not str(x.get("id") or "").strip()]
    return {"state": "OK" if not missing else "GAP", "books": len(books), "missing": len(missing), "conflicts": len(data.get("conflicts") or [])}


def chain() -> int:
    rc = 0
    if body.require_token_gate() or body.policy_step() or body.env_step():
        return 2
    reg = body.registry_sync(apply=False)
    print(f"[鏈] 編號計畫 · 新 {reg['new']} · 變更 {reg['changed']} · 退役 {reg['stale']} · AST錯 {len(reg['parse_errors'])} · 不寫入")
    if reg["parse_errors"] or reg["stale"]:
        rc = 2
    params = param_ids()
    print(f"[鏈] 參數冊 {params['state']} · 冊 {params['books']} · 缺編號 {params['missing']} · 衝突 {params.get('conflicts', 0)}")
    if params["missing"]:
        rc = 2
    snap = body.snapshot()
    res = body.write_outputs(snap, body.OUTDIR, publish=False)
    reply = body.OUTDIR / "REPLY_latest.txt"
    body.OUTDIR.mkdir(parents=True, exist_ok=True)
    reply.write_text("NEXT: 無。這一輪已跑完。\n", encoding="utf-8")
    print(f"[鏈] 頁 {res['out']}")
    print("[回覆] 只執行允許清單。不執行 --apply,不刪境。")
    print("NEXT: 無。這一輪已跑完。")
    return rc


def selftest() -> int:
    ok = next_command("NEXT: Invoke-VIACeleritasScoped { via-envgov tools }") == "via-envgov tools"
    ok = ok and next_command("NEXT: via-vcgc registry-sync --apply") == ""
    params = param_ids()
    ok = ok and params["state"] == "OK" and params["missing"] == 0
    print(f"[鏈] 允許清單 {'過' if ok else '失敗'} · 參數冊 {params['books']} 缺編號 {params['missing']}")
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


def main() -> int:
    args = sys.argv[1:]
    if args[:1] == ["chain"]:
        if "--selftest" in args:
            return selftest()
        return chain()
    return body.main()


if __name__ == "__main__":
    sys.exit(main())
