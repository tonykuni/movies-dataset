#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_registry_unionmerge_v0100 — 帳本 JSON 聯集解衝突助手(TOOL-039)
====================================================================
場景:VIA_AutoCode_Registry(append-only ledger)是多會話永恆衝突點
——雙方各自 append,git 合併必撞。本器把「雙方全保留」自動化:
  ① 讀 git index 三態(:2:=ours、:3:=theirs)
  ② ledger 聯集:ours 全序保留 + theirs 中 ours 沒有的條目按序補後
     (逐條 dict 全等判重;append-only 零覆寫零刪除)
  ③ components 聯集:ours 優先,theirs 補缺鍵
  ④ 寫回+git add(標記已解);輸出雙方各貢獻條數(誠實)
  ⑤ 產物必為合法 JSON(寫前 json 驗證;敗=HOLD 不動)
用法:py via_registry_unionmerge_v0100.py            → 解預設帳本衝突
     py via_registry_unionmerge_v0100.py <rel_path> → 指定檔
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

DEFAULT_REL = "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_AutoCode_Registry_v0100.json"


def _show(stage: int, rel: str, repo: Path):
    r = subprocess.run(["git", "-C", str(repo), "show", f":{stage}:{rel}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return json.loads(r.stdout)


def main() -> int:
    rel = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_REL
    repo = Path(__file__).resolve().parents[3]
    print(f"=== 帳本聯集解衝突 v0100 · {rel} ===")
    u = subprocess.run(["git", "-C", str(repo), "diff", "--name-only", "--diff-filter=U"],
                       capture_output=True, text=True).stdout.splitlines()
    if rel not in u:
        print(f"  [SKIP] 該檔無未解衝突(目前未解:{u or '無'})——零動作")
        return 0
    try:
        ours = _show(2, rel, repo)
        theirs = _show(3, rel, repo)
    except json.JSONDecodeError as exc:
        print(f"  [HOLD] 任一側非合法 JSON({exc})——不自動解,人工裁")
        return 1
    if not ours or not theirs:
        print("  [HOLD] 三態缺側——不自動解")
        return 1
    merged = dict(ours)
    o_led, t_led = ours.get("ledger", []), theirs.get("ledger", [])
    add = [e for e in t_led if e not in o_led]
    merged["ledger"] = o_led + add
    comp = dict(ours.get("components", {}))
    t_comp = theirs.get("components", {})
    comp_add = 0
    for k, v in t_comp.items():
        if k not in comp:
            comp[k] = v
            comp_add += 1
    if comp or t_comp:
        merged["components"] = comp
    out = json.dumps(merged, ensure_ascii=False, indent=1)
    json.loads(out)  # 寫前自驗合法性
    (repo / rel).write_text(out, encoding="utf-8")
    r = subprocess.run(["git", "-C", str(repo), "add", rel], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  [FAIL] git add 敗:{r.stderr.strip()[:100]}")
        return 1
    print(f"  [OK  ] 聯集完成:ours {len(o_led)} 條全留 + theirs 補 {len(add)} 條 → {len(merged['ledger'])}"
          f" · components 補 {comp_add} 鍵 · 已 git add(雙方零丟失)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
