#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""CGC_MDL280_VCGCAgentOSHub v0101 — v0100 薄尾(v0100 一字不動):自測 ⑥ ⑦ 改成封閉夾具。

實錄(2026-11-12 handoff test C-vcgc-agentos-hub-v0100):register --apply 真的寫出中央冊 v0108(+13 AOS 條目)之後,
v0100 自測拿「中央冊尾版」(已含 AOS 條目)當夾具 → 沒東西可補 → ⑥ ⑦ FAIL(10/12)。功能沒錯,是自測不封閉。
本版只改自測:夾具 = 中央冊尾版拿掉 AOS_* 鍵(還原成登錄前的樣子)再存成暫存夾裡的上一版號 → register 必須補回全部 AOS 條目、
原有條目一字不動、再跑一次不出新版。其餘動詞(inventory · register · activate · graphify)全部照 v0100(轉交)。
邊界同 v0100:零網路([VIA:NET-BRIDGE] 留名)· 不用 TA-Lib · 不寫同意閘 · Agent OS 一律子行程。
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
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "v0101"
_STEM = "CGC_MDL280_VCGCAgentOSHub"
TAG = _STEM + " " + VERSION
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    print("=== %s 自測(封閉夾具 · 其餘照 v0100)===" % TAG, flush=True)
    inv = PRIOR.inventory()
    c = inv.get("counts", {})
    chk("① 靜態盤點 Agent OS 尾版(不執行)", inv["lamp"] == "GREEN", inv.get("agent_os", {}).get("file"))
    chk("② 8 Skill · 9 MCP 工具 · 10 slash 技能 = 27 工具", (c.get("skills"), c.get("mcp_tools"), c.get("slash_skills"), c.get("tools_total")) == (8, 9, 10, 27), c)
    chk("③ 14 個 CLI 動詞 · 4 個內建模組 · ≥ 3 條遮罩正則", c.get("verbs") == 14 and c.get("modules") == 4 and c.get("regex", 0) >= 3, c)
    ids = [t["id"] for t in inv["tools"]] + [x["id"] for x in inv["verbs"] + inv["modules"] + inv["regex"] + inv["synonyms"]]
    chk("④ 穩定 ID 不重號", len(ids) == len(set(ids)), len(ids))
    chk("⑤ MCP 工具 ↔ CLI 動詞同義對照都指得到真的動詞", all(s["aliases"][1].split()[0] in {v["verb"] for v in inv["verbs"]} for s in inv["synonyms"]))
    aos_keys = {r["key"] for r in inv["regex"]} | {s["key"] for s in inv["synonyms"]}
    with tempfile.TemporaryDirectory() as td:
        fake = Path(td)
        tail = PRIOR._tail(PRIOR.HERE, PRIOR.CENTRAL_STEM, ".json")
        base = json.loads(tail.read_text(encoding="utf-8"))
        for sec in ("regex", "synonyms", "synonyms_meta"):          # 還原成登錄前:拿掉 AOS_* 鍵
            base[sec] = {k: v for k, v in (base.get(sec) or {}).items() if k not in aos_keys}
        fixture = fake / ("%s_v%04d.json" % (PRIOR.CENTRAL_STEM, max(1, _vnum(tail) - 1)))
        fixture.write_text(json.dumps(base, ensure_ascii=False, indent=1), encoding="utf-8")
        keep = PRIOR.HERE
        PRIOR.HERE = fake
        try:
            r1 = PRIOR.register(apply=True)
            r2 = PRIOR.register(apply=True)
        finally:
            PRIOR.HERE = keep
        newc = sorted(fake.glob(PRIOR.CENTRAL_STEM + "_v*.json"), key=_vnum)
        nxt = json.loads(newc[-1].read_text(encoding="utf-8")) if len(newc) > 1 else {}
        chk("⑥ register --apply(登錄前夾具):整合冊 v0100 + 中央冊下一版", (fake / (PRIOR.REG_STEM + "_v0100.json")).is_file() and len(newc) == 2, r1.get("central"))
        chk("⑦ 中央冊只增:原有條目一字不動 · AOS 條目全補(%d)" % len(aos_keys),
            nxt and all(nxt["regex"].get(k) == v for k, v in base["regex"].items()) and all(nxt["synonyms"].get(k) == v for k, v in base["synonyms"].items())
            and set(r1["central_added"]) == aos_keys, "+%d" % len(r1.get("central_added", [])))
        chk("⑧ 再跑一次不重出版(冪等)", "不出新版" in r2["register"] and "不出新版" in r2["central"], (r2["register"][:20], r2["central"][:20]))
        chk("⑨ 新正則都可編譯", all(re.compile(nxt["regex"][k]["pattern"]) for k in r1["central_added"] if k in nxt.get("regex", {})))
        res = {"at": PRIOR._utc(), "lamp": "YELLOW", "counts": c, "tally": {"GREEN": 1, "YELLOW": 0, "RED": 0, "ABSENT": 1},
               "rows": [{"id": "X", "kind": "k", "name": "<b>", "how": "h", "rc": 0, "lamp": "GREEN", "note": "n"}]}
        PRIOR.write_matrix(res, fake / "m")
        chk("⑩ 矩陣 JSON / CSV / HTML 寫出 · HTML 跳脫", all((fake / "m" / f).is_file() for f in ("AOS_ACTIVATION_latest.json", "AOS_ACTIVATION_latest.csv", "AOS_ACTIVATION_latest.html"))
            and "&lt;b&gt;" in (fake / "m" / "AOS_ACTIVATION_latest.html").read_text(encoding="utf-8"))
    real = PRIOR._tail(PRIOR.HERE, PRIOR.CENTRAL_STEM, ".json")
    have = json.loads(real.read_text(encoding="utf-8"))
    chk("⑪ 倉內中央冊尾版已含全部 AOS 條目(register --apply 已做)", aos_keys <= (set(have.get("regex", {})) | set(have.get("synonyms", {}))), real.name)
    g = PRIOR.graphify_status()
    chk("⑫ Graphify 偵測照實(READY / ABSENT 附建法)", g["state"] in ("READY", "ABSENT", "BROKEN") and (g["state"] != "ABSENT" or "VIA_NET_CONSENT" in g["why"]), g["state"])
    cp = subprocess.run([sys.executable, str(PRIOR_PATH), "inventory"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    chk("⑬ 其餘動詞照 v0100(inventory rc 0)", cp.returncode == 0)
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑭ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), "%d 支" % len(names))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑮ 不 import Agent OS · 零網路 · 不用 TA-Lib · 不寫同意閘",
        not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib|VIA_AgentOS)", src, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src))
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", TAG, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("--selftest", "selftest"):
        return selftest()
    return PRIOR.main(args)


if __name__ == "__main__":
    sys.exit(main())
