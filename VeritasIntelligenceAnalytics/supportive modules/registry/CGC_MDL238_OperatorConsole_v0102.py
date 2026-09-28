#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL238_OperatorConsole v0102 — 操作台 + ENV MANAGER 燈 + 註冊同步燈(模板骨架零改動)

操作員 2026-09-28 R26:「都寫成一個 PS CODE 全部整合唯一解決問題 從 VCGC 的頭跑流程 ENV MANAGER 理應自動檢查上下所有 LIBS 跟環境
都有布建完畢 尤其是加速器 網路工具等輔助工具常被忽略 註冊更新 SYNC 跳出 HTML U/I」。v0101 → v0102:
  ① 總覽 +2 燈:
       環境與工具(ENV MANAGER)— 讀 CGC_MDL240 寫的 VIA_Reports/env_manager/ENVMGR_latest.json(本支不重跑,一把尺)
       註冊同步(SYNC)— 讀本支 `sync-check` 寫的 SYNC_latest.json:VCGC registry-sync 乾跑(新 · 變更 · 退役)·
         VRN 邏輯冊守門 · 格式鎖 · 編號冊碼數;有待同步 = 黃(registry-sync --apply 要操作員批准,Master Prompt)
  ② 驗證頁 + ENV MANAGER 全表(每列帶補法)與註冊同步明細。
  ③ 擷取指令字串改指最新版(v0101 寫死 v0100 檔名;功能同一支,字串不對)。
  模板(無資料)仍與 v0100 逐位元相同 → 骨架 sha 不變 → 格式鎖照舊 GREEN。其餘照 v0101(thin tail;__getattr__ 轉接)。
用法:同 v0101 + `sync-check`(乾跑、寫 SYNC_latest.json;registry-sync 只乾跑,本支永不帶 --apply)
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
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL238_OperatorConsole"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
ENGINE = Path(__file__).stem
_BASE = _PRIOR._PRIOR                                   # v0100 module: its globals are what the v0100 writer resolves
VIA = _BASE.VIA
_e, _lamp = _BASE._e, _BASE._lamp
ENVMGR = VIA / "VIA_Reports" / "env_manager" / "ENVMGR_latest.json"
SYNC = _BASE.OUT / "SYNC_latest.json"
ENV_LAMP = {"GREEN": "OK", "AMBER": "SKIP", "RED": "FAIL", "NODATA": "UNTESTED"}
_V0101 = {k: getattr(_PRIOR, k) for k in ("collect", "overview", "page_html")}
RS_RX = re.compile(r"\[VCGC 元件自動編號冊\]\s*PLAN\s*·\s*活元件\s*(\d+)\s*·\s*新\s*(\d+)\s*·\s*變更\s*(\d+)\s*·\s*退役\s*(\d+)\s*·\s*AST錯\s*(\d+)")


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def _json(p: Path):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _tail(folder: Path, stem: str) -> Path | None:
    hits = sorted(folder.glob(stem + "_v*.py"), key=_vnum)
    return hits[-1] if hits else None


def _run(argv: list, timeout: int = 300) -> tuple:
    if any(a in ("--apply", "--approve", "--execute") for a in argv[1:]):
        return None, "拒跑:本支只乾跑"
    env = dict(os.environ, VIA_FROM_VCGC="YES", VIA_VCGC_PUSH="NO", VIA_NO_OPEN="1", PYTHONIOENCODING="utf-8")
    try:
        p = subprocess.run([sys.executable] + [str(a) for a in argv], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, env=env, cwd=str(VIA))
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except (subprocess.TimeoutExpired, OSError) as exc:
        return None, type(exc).__name__


# ---------------------------------------------------------------- ② SYNC check (dry)

def parse_registry_sync(rc, out: str) -> dict:
    m = RS_RX.search(out or "")
    if not m:
        return {"state": "UNTESTED" if rc is None else "FAIL", "note": f"讀不到 registry-sync 乾跑結果(rc {rc})"}
    live, new, chg, ret, ast = (int(x) for x in m.groups())
    pending = new + chg + ret
    state = "FAIL" if ast else ("OK" if pending == 0 else "SKIP")
    return {"state": state, "live": live, "new": new, "changed": chg, "retired": ret, "ast_errors": ast,
            "note": f"活元件 {live:,} · 新 {new:,} · 變更 {chg:,} · 退役 {ret:,} · AST錯 {ast}"
                    + (" · 待你批准 registry-sync --apply(Master Prompt:VCGC 明確批准才寫)" if pending and not ast else "")}


def sync_check(write: bool = True) -> dict:
    reg = HERE
    rows = []
    t149 = _tail(reg, "CGC_MDL149_VeritasCentralGovernanceConsole")
    rc, out = _run([t149, "registry-sync"]) if t149 else (None, "")
    rs = parse_registry_sync(rc, out)
    rows.append({"item": "VCGC 元件註冊冊(registry-sync 乾跑)", **rs})
    tlb = _tail(reg, "via_vrn_logic_book")
    rc, out = _run([tlb]) if tlb else (None, "")
    ok = rc == 0 and "[計] GREEN" in out
    stale = re.search(r"過期\s*\**\s*(\d+)", out)
    rows.append({"item": "VRN 邏輯冊守門(尾版指標)", "state": "OK" if ok else ("UNTESTED" if rc is None else "FAIL"),
                 "note": f"過期 {stale.group(1) if stale else '?'} · rc {rc}" + ("" if ok else " · 補:via_vrn_logic_book build(進版控,交 AI 開 PR)")})
    fl = _BASE.format_lock()
    rows.append({"item": "版面格式鎖(TemplateSSOT → 骨架 sha)", "state": {"GREEN": "OK", "RED": "FAIL"}.get(fl["state"], "UNTESTED"),
                 "note": f"{fl['state']} · {fl['sha']} / 鎖 {fl['locked_sha']}" + (" · 漂移 " + ", ".join(fl["drift"]) if fl["drift"] else "")})
    books = sorted((reg / "VIA_NumberBooks").glob("*.jsonl"))
    n = 0
    for b in books:
        with b.open(encoding="utf-8") as f:
            n += sum(1 for line in f if line.strip())
    rows.append({"item": "編號冊(CGC_MDL237;新增編號由 AI 開 PR,只增不減)", "state": "OK" if n else "UNTESTED",
                 "note": f"{len(books)} 本 · {n:,} 列(不含 SSOT 冊內 SSOT / RGX / SYN)"})
    worst = min((r["state"] for r in rows), key=lambda k: _BASE.ORDER.get(k, 9))
    rep = {"engine": ENGINE, "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "lamp": worst, "rows": rows}
    if write:
        _BASE.OUT.mkdir(parents=True, exist_ok=True)
        SYNC.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


# ---------------------------------------------------------------- ① lamps · sections

def collect(home_override: str | None = None) -> dict:
    d = _V0101["collect"](home_override)
    me = f"python \"{Path(__file__).relative_to(VIA)}\""
    d["cmd_extract"] = re.sub(r"python \"[^\"]*CGC_MDL238_OperatorConsole_v\d+\.py\"", lambda _m: me, str(d.get("cmd_extract", "")))
    d["envmgr"] = _json(ENVMGR)
    d["sync"] = _json(SYNC)
    return d


def overview(d: dict) -> list:
    rows = _V0101["overview"](d)
    if "envmgr" not in d and "sync" not in d:          # v0101 / v0100-shaped data: their answer, unchanged
        return rows
    ev = d.get("envmgr")
    if ev:
        bad = [r["item"] for r in ev.get("rows") or [] if r.get("state") == "RED"]
        rows.append(("環境與工具(ENV MANAGER)", ENV_LAMP.get(ev.get("verdict"), "UNTESTED"),
                     " · ".join(f"{k} {v}" for k, v in sorted((ev.get("tally") or {}).items())) + (" · 紅:" + "、".join(bad[:3]) if bad else "")
                     + f" · {ev.get('ts', '')}", "p_chk"))
    else:
        rows.append(("環境與工具(ENV MANAGER)", "UNTESTED", "還沒跑 CGC_MDL240(一鍵操作台會先跑它)", "p_chk"))
    sy = d.get("sync")
    if sy:
        rs = next((r for r in sy.get("rows") or [] if r["item"].startswith("VCGC 元件註冊冊")), {})
        rows.append(("註冊同步(SYNC)", sy.get("lamp", "UNTESTED"), (rs.get("note") or "")[:120] + f" · {sy.get('ts', '')}", "p_chk"))
    else:
        rows.append(("註冊同步(SYNC)", "UNTESTED", "還沒跑 sync-check", "p_chk"))
    return rows


_CHK_ANCHOR = "</div><div class='pane' id='p_out'>"


def _sections(d: dict) -> str:
    ev, sy = d.get("envmgr") or {}, d.get("sync") or {}
    er = "".join(f"<tr><td>{_lamp(ENV_LAMP.get(r['state'], 'UNTESTED'), r['state'])}</td><td>{_e(r['group'])}</td><td>{_e(r['item'])}</td>"
                 f"<td>{_e(r['note'])}</td><td>{_e(r['fix'] if r['state'] != 'GREEN' else '')}</td></tr>" for r in ev.get("rows") or [])
    sr = "".join(f"<tr><td>{_lamp(r['state'])}</td><td>{_e(r['item'])}</td><td>{_e(r['note'])}</td></tr>" for r in sy.get("rows") or [])
    return (f"<h3>環境與工具(ENV MANAGER · CGC_MDL240)· 總判 {_e(ev.get('verdict', '—'))} · {_e(ev.get('ts', ''))}</h3>"
            "<div class='note'>只查不裝:補法是你的手;要網路的裝件先由你開同意閘。加速器 · 網路 · LAYOUT · NLP 任一載不起來 = 總判紅。</div>"
            f"<table><tr><th>燈</th><th>區</th><th>項</th><th>現況</th><th>補法</th></tr>{er}</table>"
            f"<h3>註冊同步(SYNC)· {_e(sy.get('ts', '—'))}</h3><table><tr><th>燈</th><th>項</th><th>內容</th></tr>{sr}</table>")


def page_html(data, t) -> str:
    html = _V0101["page_html"](data, t)
    if not data or ("envmgr" not in data and "sync" not in data):
        return html
    if html.count(_CHK_ANCHOR) != 1:
        raise ValueError("驗證頁錨點不是恰好一個(骨架改版了?)")
    html = html.replace(_CHK_ANCHOR, _sections(data) + _CHK_ANCHOR)
    return html.replace(f"· {_e(_PRIOR.ENGINE)} ·", f"· {_e(ENGINE)} ·", 1)


# v0101's write_page / dock resolve collect / overview / page_html through v0101's module globals
_PRIOR.collect, _PRIOR.overview, _PRIOR.page_html = collect, overview, page_html
_BASE.collect, _BASE.overview, _BASE.page_html = collect, overview, page_html


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    if args and args[0] == "sync-check":
        rep = sync_check(write=True)
        for r in rep["rows"]:
            print(f"  {r['state']:<8} {r['item']:<40} {r['note']}")
        print(f"[SYNC] 燈 {rep['lamp']} · JSON {SYNC}")
        return 0 if rep["lamp"] in ("OK", "SKIP") else 2
    return _PRIOR.main(args)


def selftest() -> int:
    saved = {k: (getattr(_PRIOR, k), getattr(_BASE, k)) for k in _V0101}
    for k, f in _V0101.items():                          # v0101 (and through it v0100) measure themselves
        setattr(_PRIOR, k, f)
    base_orig = {k: _PRIOR._V0100[k] for k in ("collect", "overview", "page_html")}
    for k, f in base_orig.items():
        setattr(_BASE, k, f)
    try:
        rc = _PRIOR.selftest()
    finally:
        for k, (a, b) in saved.items():
            setattr(_PRIOR, k, a)
            setattr(_BASE, k, b)
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    t = _BASE.tokens()
    chk("⑲ 模板(無資料)與 v0100 逐位元相同 → 格式鎖照舊", page_html(None, t) == _PRIOR._V0100["page_html"](None, t)
        and _BASE.format_lock()["state"] in ("GREEN", "ABSENT"))
    rs = parse_registry_sync(0, "[VCGC 元件自動編號冊] PLAN · 活元件 11005 · 新 1414 · 變更 521 · 退役 1088 · AST錯 0 · {}")
    rs0 = parse_registry_sync(0, "[VCGC 元件自動編號冊] PLAN · 活元件 10 · 新 0 · 變更 0 · 退役 0 · AST錯 0")
    rsx = parse_registry_sync(2, "[VCGC 元件自動編號冊] PLAN · 活元件 10 · 新 1 · 變更 0 · 退役 0 · AST錯 3")
    chk("⑳ registry-sync 乾跑判讀:有待同步 = 黃(待批准)· 無 = 綠 · AST 錯 = 紅", rs["state"] == "SKIP" and rs["new"] == 1414
        and "待你批准" in rs["note"] and rs0["state"] == "OK" and rsx["state"] == "FAIL")
    fake = {"status": {"gate": "[流程] 政策過", "chains": [], "tools": []}, "format_lock": {"state": "GREEN"}, "folders": {"data_ok": True},
            "lock": {}, "inputs": _BASE.inputs_state(), "built_at": "2026-09-28 18:00:00", "sync_page": "ui/x.html",
            "broker": {"ok": False, "why": "x"},
            "envmgr": {"verdict": "RED", "ts": "t", "tally": {"RED": 1, "GREEN": 3},
                       "rows": [{"group": "Ⓐ 輔助工具", "item": "③ 網路工具載入", "state": "RED", "note": "<x>", "fix": "python y --selftest"}]},
            "sync": {"lamp": "SKIP", "ts": "t", "rows": [{"item": "VCGC 元件註冊冊(registry-sync 乾跑)", "state": "SKIP", "note": rs["note"]}]}}
    ov = {n: k for n, k, _, _ in overview(fake)}
    chk("㉑ 總覽 +2 燈:ENV MANAGER 紅 → 紅 · 註冊同步待批准 → 黃", ov.get("環境與工具(ENV MANAGER)") == "FAIL" and ov.get("註冊同步(SYNC)") == "SKIP")
    live = page_html(fake, t)
    chk("㉒ 驗證頁補 ENV MANAGER 全表(含補法)與註冊同步;字照樣跳脫", "ENV MANAGER · CGC_MDL240" in live and "python y --selftest" in live
        and "<x>" not in live and live.index("ENV MANAGER · CGC_MDL240") < live.index("id='p_out'"))
    d = {"cmd_extract": 'python "supportive modules/registry/CGC_MDL238_OperatorConsole_v0100.py" extract --home "h"'}
    fixed = re.sub(r"python \"[^\"]*CGC_MDL238_OperatorConsole_v\d+\.py\"", lambda _m: f"python \"{Path(__file__).relative_to(VIA)}\"", d["cmd_extract"])
    chk("㉓ 擷取指令字串改指最新版", ENGINE + ".py" in fixed and fixed.endswith('extract --home "h"'), fixed[-60:])
    chk("㉔ 只乾跑:帶 --apply 的呼叫拒跑", _run(["x.py", "registry-sync", "--apply"])[0] is None)
    ok = rc == 0 and all(results)
    print(f"  {ENGINE} selftest +{sum(results)}/{len(results)} · v0101 rc={rc} · {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
