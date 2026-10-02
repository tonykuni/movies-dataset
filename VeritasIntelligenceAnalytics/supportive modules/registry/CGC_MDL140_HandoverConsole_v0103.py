#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL140_HandoverConsole v0103 — 薄尾:沿用收據時也印機讀判決行(修 closeout「[沿用成功]」誤判紅)

實測(2026-10-02,PR #419 收尾):`handoff test <case>` 判沿用時只印「[沿用成功] …」、rc 0,卻不印實跑才有的
`{"case": …, "rc": …, "marker": …}` 判決行;closeout(CGC_MDL149 v0183 起)只讀這一行,讀不到 = 標記 None = 紅,
收尾停在 ③ / ⑥+,只能手動把工作項轉 VERIFIED 繞過。
  ① run_case():照 v0101 原樣跑(沿用判定仍走 v0102 的 evidence_status:rc 0 + 目標標記 + 相依雜湊 + 相依集合);
     回 0 而收據一個位元組都沒變 = 這次是沿用 → 從收據補印同格式判決行,加 "reused": true。
     marker 取收據的 target_marker_seen 且 rc == 0(不從文字猜);實跑路徑照 v0101 原樣、不多印。
  ② 裝進 v0101 的模組全域,v0101 main() 的 test 動詞直接走本版;其餘照 v0102。只收 VCGC 呼叫。零網路。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import contextlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL140_HandoverConsole"
ENGINE = Path(__file__).stem


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
VIA = PRIOR.VIA
POLICY = PRIOR.POLICY
BASE = PRIOR.PRIOR                              # v0101:main() 的 test 動詞查的是它的模組全域 run_case
_V0101_RUN_CASE = BASE.run_case


def __getattr__(name: str):
    return getattr(PRIOR, name)


def _receipt_bytes_v0103(via, name):
    """收據原始位元組(不在 = None);沿用判定只看「跑前跑後一樣」,不解讀內容。"""
    via = Path(via)
    policy = BASE.read(via / POLICY.relative_to(VIA))
    path = BASE.local(via, policy["evidence_dir"]) / (name + ".json")
    return (path.read_bytes() if path.is_file() else None), path, policy


def run_case(name, via=VIA):
    """v0101 原樣跑;沿用(回 0 且收據沒動)時從收據補印 {"case","rc","marker","scope","reused"} 判決行。"""
    before, path, policy = _receipt_bytes_v0103(via, name)
    rc = _V0101_RUN_CASE(name, via)
    if rc == 0 and before is not None and path.is_file() and path.read_bytes() == before:
        receipt = json.loads(before.decode("utf-8"))
        marker = bool(receipt.get("target_marker_seen")) and receipt.get("rc") == 0
        scope = receipt.get("scope") or (policy.get("test_cases") or {}).get(name, {}).get("scope")
        print(json.dumps({"case": name, "rc": receipt.get("rc"), "marker": marker, "scope": scope,
                          "reused": True}, ensure_ascii=False))
        return 0 if marker else 1
    return rc


BASE.run_case = run_case                        # v0101 main() → test → 本版


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"] and os.environ.get("VIA_FROM_VCGC") == "YES":
        return selftest()
    return PRIOR.main(argv)


def selftest():
    rc = PRIOR.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    with tempfile.TemporaryDirectory() as tmp:
        via = Path(tmp)
        reg = via / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        for fname in ("CGC_MDL999_Demo_v0100.py", "CGC_MDL149_VeritasCentralGovernanceConsole_v0100.py"):
            (reg / fname).write_text("x = 1\n", encoding="utf-8")
        case = {"argv": ["CGC_MDL999_Demo", "--selftest"], "success_marker": "ok", "scope": "demo-scope",
                "timeout_seconds": 5, "dependencies": ["supportive modules/registry/CGC_MDL999_Demo_v*.py"]}
        policy = {"evidence_dir": "docs/handoff/evidence", "test_cases": {"demo": case}}
        (reg / POLICY.name).write_text(json.dumps(policy), encoding="utf-8")
        ev = via / "docs" / "handoff" / "evidence"
        ev.mkdir(parents=True)
        (ev / "demo.txt").write_text("ok\n", encoding="utf-8")
        deps = {rel: BASE.sha(via / rel) for rel in sorted(PRIOR.dependency_set(via, case))}
        receipt = {"schema": "VIA.Handoff.TestReceipt.v1", "case": "demo", "command": ["x"], "case_sha256": BASE.fingerprint(case),
                   "rc": 0, "target_marker_seen": True, "completed_at": "2026-10-02T00:00:00+00:00", "dependencies": deps,
                   "log": "docs/handoff/evidence/demo.txt", "log_sha256": BASE.sha(ev / "demo.txt"), "scope": "demo-scope"}
        (ev / "demo.json").write_text(json.dumps(receipt), encoding="utf-8")
        before = (ev / "demo.json").read_bytes()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            got = run_case("demo", via)
        lines = out.getvalue().splitlines()
        rec = next((json.loads(ln) for ln in lines if ln.startswith("{\"case\"")), {})
        chk("① 沿用:照舊印「[沿用成功]」、回 0", got == 0 and any(ln.startswith("[沿用成功] demo") for ln in lines), lines[:1])
        chk("② 沿用:補印 closeout 讀的判決行(marker true · reused true · scope 照收據)",
            rec.get("case") == "demo" and rec.get("marker") is True and rec.get("reused") is True and rec.get("scope") == "demo-scope", rec)
        chk("③ 沿用不寫收據(位元組一樣)", (ev / "demo.json").read_bytes() == before)
    chk("④ v0101 main() 的 test 動詞走本版", BASE.run_case is run_case)
    chk("⑤ 沿用判定仍走 v0102 的 evidence_status(相依集合檢查還在)", BASE.evidence_status is PRIOR.evidence_status)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 檔頭 · 加速器橋 · 網路橋在;不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"[交接 v0103] 本版 {sum(ok)}/{len(ok)}")
    return 0 if rc == 0 and all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
