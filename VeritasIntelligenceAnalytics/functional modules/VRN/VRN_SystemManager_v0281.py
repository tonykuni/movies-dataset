#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0281 — 薄尾(v0280 以前一字不動):monitor 動詞(CLAUDE.md 2026-11-16 待登需求 · 2026-11-21 晨檢 B)

  monitor [--lanes N] [--json]   只讀彙總:
      ① VRN-2 執行期自己寫的收據(VIA_Reports/vrn2:Activate · Closeout 尾版 · IDEMPOTENCE · Completion · CloseoutUI)
         UNIT=自測步 · INTEGRATION=冪等閘 · 輸出驗證=完成判定 + 獨立驗證 · HTML U/I=收尾頁 · 加速器/網路=④ 覆蓋 + ⑥ 匯入 · 增量庫=⑬
      ② 前版零寫入動詞:SYSTEM=catalog · 輸入輸出連結=links(實測不寫契約檔 / 資產冊)
      USER-TEST = 灰(人做的驗收);沒有收據 = 灰;收據超過 48 小時 = 黃(過期)。總燈取最差;rc 綠 0 · 黃 2 · 紅 1。
  收據 + 頁 VIA_Reports/vrn/monitor/VRN_MONITOR_latest.json / .html(不入倉;頁只用鎖定模板)。不出網 · 不寫別系統的檔 · 不跑 launch。其餘動詞一律交給前版。自測:--selftest
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

import glob
import importlib.util
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[1]
FAMILY = "VRN_SystemManager"
TAG = "VRN_SystemManager v0281"
RCPT = "VIA_Reports/vrn2"                    # VRN-2 執行期自己寫的收據夾(只讀)
OUT_DIR = "VIA_Reports/vrn/monitor"          # 本動詞的收據夾(不入倉)


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0281", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


# ── monitor:只彙總既有引擎 ── 兩種來源都唯讀:
#    ① 前版零寫入的動詞(catalog · links;實測不寫契約檔、不寫資產冊)
#    ② VRN-2 執行期自己寫的收據(Activate · Closeout · IDEMPOTENCE · Completion · CloseoutUI · 獨立驗證)
VERBS = {"SYSTEM": ["catalog"], "PARAMS": ["links"]}
ORDER = ["UNIT", "INTEGRATION", "SYSTEM", "USER_TEST", "OUTPUT_CHECK", "UI_SYNC", "PARAMS", "ACCEL_NET", "DB"]
ZH = {"UNIT": "UNIT 單元自測", "INTEGRATION": "INTEGRATION 冪等重跑", "SYSTEM": "SYSTEM 目錄 · 冊 · 引擎", "USER_TEST": "USER-TEST 操作員",
      "OUTPUT_CHECK": "輸出驗證(完成判定 + 獨立驗證)", "UI_SYNC": "HTML U/I 收尾頁", "PARAMS": "輸入輸出連結",
      "ACCEL_NET": "加速器 · 網路工具(生效)", "DB": "增量庫"}
RANK = {"GREEN": 0, "GRAY": 0, "YELLOW": 1, "RED": 2}
STALE_H = 48.0


def _worst(lamps) -> str:
    lamps = [x for x in lamps if x in RANK]
    if not lamps:
        return "GRAY"
    w = max(lamps, key=lambda x: RANK[x])
    return "GREEN" if w == "GRAY" and "GREEN" in lamps else w


def _read(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _newest(base: Path, pattern: str, exclude: str = ""):
    hits = [Path(x) for x in glob.glob(str(base / pattern)) if not (exclude and exclude in Path(x).name)]
    return max(hits, key=lambda p: p.stat().st_mtime) if hits else None


def _age_h(p) -> float:
    return (time.time() - p.stat().st_mtime) / 3600.0 if p else 1e9


def _steps(*docs) -> list:
    out = []
    for d in docs:
        for s in (d or {}).get("steps") or []:
            if isinstance(s, dict) and s.get("step"):
                out.append(s)
    return out


def _pick(steps, *keys) -> list:
    return [s for s in steps if any(k in str(s.get("step")) for k in keys)]


def _verb_lamp(text: str, rc) -> tuple:
    lines = [x for x in (text or "").splitlines() if x.strip() and "SyntaxWarning" not in x and not x.startswith("<unknown>")]
    v = next((x for x in reversed(lines) if "VRN_SystemManager" in x), lines[-1] if lines else "")
    m = re.search(r"\b(GREEN|YELLOW|RED)\b", v)
    lamp = m.group(1) if m else ("GREEN" if rc == 0 else "YELLOW" if rc in (2, 3) else "RED")
    return lamp, v.strip()[:180]


def _run(args: list, timeout: float = 600.0) -> tuple:
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), *args], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout, cwd=str(HERE))
        return r.returncode, (r.stdout or "") + (r.stderr or ""), round(time.time() - t0, 1)
    except subprocess.TimeoutExpired:
        return None, "逾時", round(time.time() - t0, 1)


def from_receipts(base: Path) -> dict:
    """VRN-2 執行期收據 → 格。沒有收據 = 灰(先跑 launch);收據超過 48 小時 = 黃(過期)。"""
    rows = {}
    act_p = base / "VRN2_Activate_latest.json"
    clo_p = _newest(base, "VRN2_Closeout_v*.json", exclude="before")
    act, clo = _read(act_p) if act_p.is_file() else None, _read(clo_p) if clo_p else None
    steps = _steps(act, clo)
    age = min(_age_h(act_p if act_p.is_file() else None), _age_h(clo_p))
    tag = f"收據 {age:.0f}h 前" if age < 1e8 else "沒有收據"

    def cell(name, lamps, line):
        lamp = _worst(lamps)
        if lamp != "GRAY" and age > STALE_H:
            lamp, line = _worst([lamp, "YELLOW"]), line + f" · 過期(>{STALE_H:.0f}h)"
        rows[name] = {"lamp": lamp, "line": f"{line} · {tag}"}

    u = _pick(steps, "自測", "快速測試")
    cell("UNIT", [s["lamp"] for s in u], f"自測步 {len(u)} · " + " · ".join(f"{s['step']} {s['lamp']}" for s in u[:3]))
    ide = _read(base / "IDEMPOTENCE_latest.json") if (base / "IDEMPOTENCE_latest.json").is_file() else None
    cell("INTEGRATION", [ide.get("lamp")] if ide else [], f"冪等閘 {ide.get('lamp') if ide else '沒有收據'}")
    comp = _read(base / "VRN2_Completion_latest.json") if (base / "VRN2_Completion_latest.json").is_file() else None
    ver = _pick(steps, "獨立驗證")
    cl = ([] if not comp else ["RED" if comp.get("red") else "YELLOW" if comp.get("yellow") else "GREEN"]) + [s["lamp"] for s in ver]
    cell("OUTPUT_CHECK", cl, (f"完成判定 {comp.get('verdict')} 紅 {comp.get('red')} 黃 {comp.get('yellow')}" if comp else "沒有完成判定收據")
         + (f" · 獨立驗證 {ver[-1]['lamp']}" if ver else ""))
    ui = _read(base / "VRN2_CloseoutUI_latest.json") if (base / "VRN2_CloseoutUI_latest.json").is_file() else None
    st = (ui or {}).get("state")
    cell("UI_SYNC", [{"CLOSED": "GREEN", "DONE": "GREEN", "BLOCKED": "RED"}.get(str(st).upper(), "YELLOW")] if ui else [],
         f"收尾頁 {st or '沒有收據'}" + (f" · {str(ui.get('state_label') or '')[:40]}" if ui else ""))
    acc = _pick(steps, "加速器覆蓋", "加速器 / 網路工具匯入")
    cell("ACCEL_NET", [s["lamp"] for s in acc], " · ".join(f"{s['step']} {s['lamp']}" for s in acc) or "沒有加速器步")
    db = _pick(steps, "⑬ 輸出位置", "增量庫")
    cell("DB", [s["lamp"] for s in db], " · ".join(f"{s['step']} {s['lamp']}" for s in db[:2]) or "沒有增量庫步")
    return rows


def monitor(lanes: int = 2, runner=None, rcpt_dir=None, out_dir=None) -> dict:
    runner = runner or _run
    base = Path(rcpt_dir) if rcpt_dir else VIA_ROOT / RCPT
    rows = from_receipts(base)
    with ThreadPoolExecutor(max_workers=max(1, min(int(lanes), len(VERBS)))) as ex:
        futs = {c: ex.submit(runner, a) for c, a in VERBS.items()}
        for c, a in VERBS.items():
            rc, text, secs = futs[c].result()
            lamp, line = _verb_lamp(text, rc)
            rows[c] = {"lamp": lamp, "line": f"({' '.join(a)} · {secs}s) {line}"}
    rows["USER_TEST"] = {"lamp": "GRAY", "line": "操作員用滑鼠走 U/I(人做的驗收,機器不代)"}
    lamp = _worst([rows[c]["lamp"] for c in rows])
    lamp = "GREEN" if lamp == "GRAY" else lamp
    res = {"tool": TAG, "system": "VRN", "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "lamp": lamp,
           "rows": [dict(cell=c, **rows[c]) for c in ORDER],
           "counts": {k: sum(1 for c in rows if rows[c]["lamp"] == k) for k in ("GREEN", "YELLOW", "RED", "GRAY")},
           "rule": "只讀 VRN-2 收據 + 前版零寫入動詞(catalog · links);沒有收據的格亮灰;收據超過 48 小時亮黃"}
    od = Path(out_dir) if out_dir else VIA_ROOT / OUT_DIR
    try:
        od.mkdir(parents=True, exist_ok=True)
        (od / "VRN_MONITOR_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        res["receipt"] = str(od / "VRN_MONITOR_latest.json")
        (od / "VRN_MONITOR_latest.html").write_text(render_html(res), encoding="utf-8")
        res["page"] = str(od / "VRN_MONITOR_latest.html")
    except OSError as exc:
        res["receipt"] = f"寫不出收據:{type(exc).__name__}"
    return res


def render_html(res: dict) -> str:
    """monitor 頁:骨架與 class 同 synchronizer 頁(wrap · card · lamp g/y/r/x · scroll);樣式只讀鎖定模板冊(VRN 自己那份 SYNC-CORE),不自訂顏色。"""
    import html as _h
    css, note = PRIOR.sy_template_css(VIA_ROOT) if callable(getattr(PRIOR, "sy_template_css", None)) else ("", "模板冊讀不到")
    k = {"GREEN": "g", "YELLOW": "y", "RED": "r", "GRAY": "x"}
    zh = {"g": "綠", "y": "黃", "r": "紅", "x": "灰"}

    def lamp(x):
        c = k.get(x, "x")
        return '<span class="lamp %s">%s</span>' % (c, zh[c])
    rows = "".join('<tr><td class="l">%s</td><td>%s</td><td>%s</td></tr>' % (lamp(r["lamp"]), _h.escape(ZH[r["cell"]]), _h.escape(r["line"]))
                   for r in res["rows"])
    c = res["counts"]
    return ('<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            "<title>VRN 監控台 · 系統狀態</title><style>%s</style></head><body><div class=\"wrap\">"
            '<header><div class="caps">VIA · VRN · MONITOR</div><h1>VRN 監控台 · 系統狀態</h1>'
            '<div class="note">%s · %s · 模板 %s</div></header>'
            '<div class="verdict">%s<b>綠 %d · 黃 %d · 紅 %d · 灰 %d</b><span>%s</span></div>'
            '<section class="card"><h2>九格(VRN-2 收據 + 零寫入動詞;灰 = 沒有對應引擎或沒有收據)</h2><div class="scroll"><table><thead><tr>'
            '<th class="l">燈</th><th>格</th><th>結果</th></tr></thead><tbody>%s</tbody></table></div></section>'
            "</div></body></html>") % (css, _h.escape(TAG), _h.escape(res["at"]), _h.escape(note), lamp(res["lamp"]), c["GREEN"], c["YELLOW"], c["RED"], c["GRAY"],
                                       _h.escape(res["rule"]), rows)


def _print(res: dict) -> None:
    c = res["counts"]
    print(f"[{TAG}] monitor {res['lamp']} · 綠 {c['GREEN']} · 黃 {c['YELLOW']} · 紅 {c['RED']} · 灰 {c['GRAY']} · 收據 {res.get('receipt')}", flush=True)
    for r in res["rows"]:
        print(f"  {r['lamp']:<6} {ZH[r['cell']]:<22} {r['line']}", flush=True)


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if a[:1] == ["monitor"]:
        lanes = int(a[a.index("--lanes") + 1]) if "--lanes" in a and a.index("--lanes") + 1 < len(a) else 2
        res = monitor(lanes=lanes)
        if "--json" in a:
            print(json.dumps(res, ensure_ascii=False, indent=1))
        else:
            _print(res)
        return {"GREEN": 0, "YELLOW": 2, "RED": 1}[res["lamp"]]
    return PRIOR.main(a)


def selftest() -> int:
    import os
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    rc0 = PRIOR.selftest()
    print(f"=== {TAG} · 薄尾自測(monitor 只讀收據 + 零寫入動詞;暫存夾 · 假子行程 · 零網路)===")
    chk("⓪ 直接前版 %s 自測過" % PRIOR_PATH.name, rc0 == 0, f"rc {rc0}")
    seen = []

    def fake(args):
        seen.append(" ".join(args))
        return {"catalog": (0, "[VRN_SystemManager v0269] catalog GREEN · books 54"),
                "links": (2, "[VRN_SystemManager v0269] links YELLOW · missing 118")}[" ".join(args)] + (0.01,)
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        res0 = monitor(runner=fake, rcpt_dir=t / "none", out_dir=t / "o0")
        by0 = {r["cell"]: r for r in res0["rows"]}
        chk("① 沒有收據 → 收據類六格灰(不冒充綠)", all(by0[c]["lamp"] == "GRAY" for c in ("UNIT", "INTEGRATION", "OUTPUT_CHECK", "UI_SYNC", "ACCEL_NET", "DB")))
        chk("② 只叫零寫入動詞 catalog · links", sorted(seen) == ["catalog", "links"], seen)
        r = t / "r"; r.mkdir()
        (r / "VRN2_Activate_latest.json").write_text(json.dumps({"steps": [{"step": "④ 加速器覆蓋", "lamp": "GREEN"}, {"step": "⑥ ENG397 自測", "lamp": "GREEN"},
                                                                          {"step": "⑥ 加速器 / 網路工具匯入", "lamp": "GREEN"}]}), encoding="utf-8")
        (r / "VRN2_Closeout_v0178.json").write_text(json.dumps({"steps": [{"step": "⑪ 獨立驗證(背景 · 只讀)", "lamp": "GREEN"},
                                                                         {"step": "⑬ 輸出位置 · 增量庫", "lamp": "GREEN"}]}), encoding="utf-8")
        (r / "VRN2_Closeout_v0178.before_roundall.json").write_text(json.dumps({"steps": [{"step": "⑬ 輸出位置", "lamp": "RED"}]}), encoding="utf-8")
        (r / "IDEMPOTENCE_latest.json").write_text(json.dumps({"lamp": "GREEN"}), encoding="utf-8")
        (r / "VRN2_Completion_latest.json").write_text(json.dumps({"verdict": "完成", "red": 0, "yellow": 3}), encoding="utf-8")
        (r / "VRN2_CloseoutUI_latest.json").write_text(json.dumps({"state": "REVIEW", "state_label": "等人工核對"}), encoding="utf-8")
        res = monitor(runner=fake, rcpt_dir=r, out_dir=t / "o1")
        by = {x["cell"]: x for x in res["rows"]}
        chk("③ 收據 → 加速器綠 · 冪等綠 · 增量庫綠(不讀 before_roundall 舊收據)", by["ACCEL_NET"]["lamp"] == "GREEN" and by["INTEGRATION"]["lamp"] == "GREEN"
            and by["DB"]["lamp"] == "GREEN", by["DB"])
        chk("④ 完成判定黃 3 → 輸出驗證黃;收尾頁 REVIEW → 黃;links 黃", by["OUTPUT_CHECK"]["lamp"] == "YELLOW" and by["UI_SYNC"]["lamp"] == "YELLOW"
            and by["PARAMS"]["lamp"] == "YELLOW")
        chk("⑤ 總燈取最差 = 黃 · 九格都在 · 收據寫在指定夾", res["lamp"] == "YELLOW" and [x["cell"] for x in res["rows"]] == ORDER
            and (t / "o1" / "VRN_MONITOR_latest.json").is_file())
        pg = (t / "o1" / "VRN_MONITOR_latest.html").read_text(encoding="utf-8") if (t / "o1" / "VRN_MONITOR_latest.html").is_file() else ""
        chk("⑤b 頁寫出 · 只用鎖定模板的 class(沒有自訂色碼)· 九列", 'class="lamp' in pg and pg.count("<tr>") >= 10
            and not re.search(r"(color|background)\s*:\s*#", pg.split("</style>")[-1]))
        old = time.time() - 72 * 3600
        for f in r.iterdir():
            os.utime(f, (old, old))
        res3 = monitor(runner=fake, rcpt_dir=r, out_dir=t / "o2")
        chk("⑥ 收據超過 48 小時 → 綠格降黃(標過期)", {x["cell"]: x for x in res3["rows"]}["ACCEL_NET"]["lamp"] == "YELLOW")
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑦ 加速器橋在;本動詞不出網 · 不碰 TA-Lib · 不寫契約檔 / 資產冊", "[VIA:ACCEL-BRIDGE:v0100]" in src and "_via_net()." not in body
        and "talib" not in body.lower() and "VRN_NUMBER_REQUEST" not in body and "Asset_Register" not in body)
    peer = [k for k in ("VIA_FROM_VCGC", "VIA_FROM_VDFSM") if re.search(r"environ(?:\[[\"']%s[\"']\]\s*=|\.setdefault\([\"']%s)" % (k, k), body)]
    chk("⑩ 系統獨立:不設他系統的入口旗標(本檔是 VRN 自己的入口;VCGC 只支援不干涉)", not peer, peer)
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑧ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), f"{len(pub)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
