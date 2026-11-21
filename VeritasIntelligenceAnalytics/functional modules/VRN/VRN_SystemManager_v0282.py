#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0282 — 薄尾(v0281 以前一字不動):monitor 的過期判斷改成「每一格看它自己用到的收據」(PR 712 Codex P2)

  v0281 全部收據格共用 Activate / Closeout 裡較新那份的年齡 → Activate 一更新,冪等閘 · 完成判定 · 收尾頁的舊收據也被標成新的、綠燈照留。
  本版:每一步記住它來自哪一份收據;每一格取它用到的每份收據裡最舊的年齡;任一份超過 48 小時 → 綠降黃並標過期;格上寫最舊那份。
  其餘(九格 · 只讀收據 + 零寫入動詞 · 鎖定模板頁 · 不出網)全照 v0281。用法同 v0281:monitor [--lanes N] [--json] · --selftest
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
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VRN_SystemManager"
TAG = "VRN_SystemManager v0282"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0282", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_FROM_RECEIPTS_V0281 = PRIOR.from_receipts


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _load(p):
    """(內容, 年齡小時, 檔名);不在 / 讀不懂 → (None, None, 檔名)。"""
    if p is None or not Path(p).is_file():
        return None, None, (Path(p).name if p else "")
    return PRIOR._read(Path(p)), PRIOR._age_h(Path(p)), Path(p).name


def from_receipts(base: Path) -> dict:
    stale_h = PRIOR.STALE_H
    act, a_act, n_act = _load(base / "VRN2_Activate_latest.json")
    clo, a_clo, n_clo = _load(PRIOR._newest(base, "VRN2_Closeout_v*.json", exclude="before"))
    steps = [dict(s, _age=a_act, _src=n_act) for s in PRIOR._steps(act)] + [dict(s, _age=a_clo, _src=n_clo) for s in PRIOR._steps(clo)]
    rows = {}

    def cell(name, items, line, empty):
        """items = [(燈, 年齡, 收據名)];年齡取最舊;任一份過期 → 綠降黃。"""
        items = [x for x in items if x[0]]
        if not items:
            rows[name] = {"lamp": "GRAY", "line": empty}
            return
        lamp = PRIOR._worst([x[0] for x in items])
        aged = [x for x in items if x[1] is not None]
        if aged:
            _, oldest, src = max(aged, key=lambda x: x[1])
            line += f" · 最舊收據 {src} {oldest:.0f}h 前"
            if oldest > stale_h:
                line += f" · 過期(>{stale_h:.0f}h)"
                lamp = PRIOR._worst([lamp, "YELLOW"]) if lamp == "GREEN" else lamp
        rows[name] = {"lamp": lamp, "line": line}

    u = PRIOR._pick(steps, "自測", "快速測試")
    cell("UNIT", [(s["lamp"], s["_age"], s["_src"]) for s in u], f"自測步 {len(u)} · " + " · ".join(f"{s['step']} {s['lamp']}" for s in u[:3]), "沒有自測步收據")
    ide, a_ide, n_ide = _load(base / "IDEMPOTENCE_latest.json")
    cell("INTEGRATION", [(ide.get("lamp"), a_ide, n_ide)] if ide else [], f"冪等閘 {ide.get('lamp') if ide else ''}", "沒有冪等閘收據")
    comp, a_comp, n_comp = _load(base / "VRN2_Completion_latest.json")
    ver = PRIOR._pick(steps, "獨立驗證")
    oc = ([("RED" if comp.get("red") else "YELLOW" if comp.get("yellow") else "GREEN", a_comp, n_comp)] if comp else []) \
        + [(s["lamp"], s["_age"], s["_src"]) for s in ver]
    cell("OUTPUT_CHECK", oc, (f"完成判定 {comp.get('verdict')} 紅 {comp.get('red')} 黃 {comp.get('yellow')}" if comp else "沒有完成判定收據")
         + (f" · 獨立驗證 {ver[-1]['lamp']}" if ver else ""), "沒有完成判定 / 獨立驗證收據")
    ui, a_ui, n_ui = _load(base / "VRN2_CloseoutUI_latest.json")
    st = (ui or {}).get("state")
    cell("UI_SYNC", [({"CLOSED": "GREEN", "DONE": "GREEN", "BLOCKED": "RED"}.get(str(st).upper(), "YELLOW"), a_ui, n_ui)] if ui else [],
         f"收尾頁 {st}" + (f" · {str(ui.get('state_label') or '')[:40]}" if ui else ""), "沒有收尾頁收據")
    acc = PRIOR._pick(steps, "加速器覆蓋", "加速器 / 網路工具匯入")
    cell("ACCEL_NET", [(s["lamp"], s["_age"], s["_src"]) for s in acc], " · ".join(f"{s['step']} {s['lamp']}" for s in acc), "沒有加速器步收據")
    db = PRIOR._pick(steps, "⑬ 輸出位置", "增量庫")
    cell("DB", [(s["lamp"], s["_age"], s["_src"]) for s in db], " · ".join(f"{s['step']} {s['lamp']}" for s in db[:2]), "沒有增量庫步收據")
    return rows


PRIOR.from_receipts = from_receipts                # v0281 的 monitor 取模組全域 from_receipts → 換上本版


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    PRIOR.TAG = TAG
    return PRIOR.main(a)


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    keep = PRIOR.from_receipts
    PRIOR.from_receipts = _FROM_RECEIPTS_V0281
    try:
        rc0 = PRIOR.selftest()
    finally:
        PRIOR.from_receipts = keep
    print(f"=== {TAG} · 薄尾自測(每一格看自己的收據年齡;暫存夾 · 零網路)===")
    chk("⓪ 直接前版 %s 自測過" % PRIOR_PATH.name, rc0 == 0, f"rc {rc0}")
    with tempfile.TemporaryDirectory() as td:
        r = Path(td)
        (r / "VRN2_Activate_latest.json").write_text(json.dumps({"steps": [{"step": "④ 加速器覆蓋", "lamp": "GREEN"}, {"step": "⑥ ENG397 自測", "lamp": "GREEN"}]}), encoding="utf-8")
        (r / "VRN2_Closeout_v0178.json").write_text(json.dumps({"steps": [{"step": "⑪ 獨立驗證", "lamp": "GREEN"}, {"step": "⑬ 輸出位置 · 增量庫", "lamp": "GREEN"}]}), encoding="utf-8")
        (r / "IDEMPOTENCE_latest.json").write_text(json.dumps({"lamp": "GREEN"}), encoding="utf-8")
        (r / "VRN2_Completion_latest.json").write_text(json.dumps({"verdict": "完成", "red": 0, "yellow": 0}), encoding="utf-8")
        (r / "VRN2_CloseoutUI_latest.json").write_text(json.dumps({"state": "CLOSED"}), encoding="utf-8")
        g = from_receipts(r)
        chk("① 全部新鮮 → 收據六格綠", all(g[c]["lamp"] == "GREEN" for c in ("UNIT", "INTEGRATION", "OUTPUT_CHECK", "UI_SYNC", "ACCEL_NET", "DB")), g)
        old = time.time() - 72 * 3600
        for n in ("IDEMPOTENCE_latest.json", "VRN2_Completion_latest.json", "VRN2_CloseoutUI_latest.json"):
            os.utime(r / n, (old, old))
        g = from_receipts(r)
        chk("② Activate 新鮮 · 冪等 / 完成判定 / 收尾頁 72h 前 → 這三格各自降黃(Codex 重現情境)",
            all(g[c]["lamp"] == "YELLOW" and "過期" in g[c]["line"] for c in ("INTEGRATION", "OUTPUT_CHECK", "UI_SYNC")), {c: g[c] for c in ("INTEGRATION", "OUTPUT_CHECK", "UI_SYNC")})
        chk("③ 只來自 Activate 的格(自測 · 加速器)照綠 · 寫自己的收據名", g["UNIT"]["lamp"] == "GREEN" and "VRN2_Activate_latest.json" in g["UNIT"]["line"]
            and g["ACCEL_NET"]["lamp"] == "GREEN")
        os.utime(r / "VRN2_Closeout_v0178.json", (old, old))
        g = from_receipts(r)
        chk("④ Closeout 過期 → 增量庫格降黃(它的步只來自 Closeout)", g["DB"]["lamp"] == "YELLOW" and "VRN2_Closeout_v0178.json" in g["DB"]["line"])
    chk("⑤ 換裝:v0281 的 monitor 叫到的 from_receipts = 本版", PRIOR.from_receipts is from_receipts)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    peer = [k for k in ("VIA_FROM_VCGC", "VIA_FROM_VDFSM") if re.search(r"environ(?:\[[\"']%s[\"']\]\s*=|\.setdefault\([\"']%s)" % (k, k), body)]
    chk("⑥ 系統獨立:不設他系統的入口旗標(本檔是 VRN 自己的入口;VCGC 只支援不干涉)", not peer, peer)
    chk("⑦ 加速器橋在;不出網 · 不碰 TA-Lib · 不寫契約檔 / 資產冊", "[VIA:ACCEL-BRIDGE:v0100]" in src and "_via_net()." not in body
        and "talib" not in body.lower() and "VRN_NUMBER_REQUEST" not in body and "Asset_Register" not in body)
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑧ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), f"{len(pub)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
