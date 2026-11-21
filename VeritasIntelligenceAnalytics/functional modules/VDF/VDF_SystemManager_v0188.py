#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF SystemManager v0188 — 薄尾(v0186 以前一字不動;v0187 留給開著的 PR 690):monitor 動詞(CLAUDE.md 2026-11-16 待登需求 · 2026-11-21 晨檢 B)

  monitor [--lanes N] [--json]   並行(預設 3 道)跑本管理器既有的五個唯讀動詞,彙總成一張格:
      UNIT=test · SYSTEM=health · 參數/regex/同義字/SDD=status · 加速器/網路(生效)=bridges --json · HTML U/I 同步=synchronizer check
      輸出驗證=db verify 收據 · 資料庫=DuckDB 狀態矩陣 + db check + parquet 增量庫(MDL020)收據(VDF 資料庫引擎自己寫的,只讀;超過 48 小時亮黃)
      INTEGRATION · USER-TEST:沒有對應唯讀引擎 → 灰,寫原因(不新增引擎、不另做掃描器)
  總燈取最差(灰不算綠也不算紅);rc 綠 0 · 黃 2 · 紅 1;收據 + 頁 VIA_Reports/vdf/monitor/VDF_MONITOR_latest.json / .html(不入倉;頁只用鎖定模板)。
  不出網 · 不寫別系統的檔 · 不碰同意閘 · 不跑 launch / sync --apply / db。其餘動詞一律交給前版。自測:--selftest
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本版兩扇門都不出網。"""
    return None if VIA_NET_TOOL_PATH is None else VIA_NET_TOOL_PATH
# ===== [VIA:NET-BRIDGE:END] =====

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
FAMILY = "VDF_SystemManager"
TAG = "VDF_SystemManager v0188"
OUT_DIR = "VIA_Reports/vdf/monitor"                         # 本動詞的收據夾(相對 VIA 夾;不入倉)


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0188", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


# ── monitor:只彙總既有唯讀動詞(不新增引擎、不寫別系統的檔、不出網)──
#   (格, 動詞參數, 說明)── 動詞都是前版已有、實測零寫入的
SOURCES = [
    ("SYSTEM", ["health"], "health:自己的夾 · 前版 · SSOT · 對等規則"),
    ("PARAMS", ["status"], "status:參數 · regex · 同義字 · SDD · parity"),
    ("ACCEL_NET", ["bridges", "--json"], "bridges:加速器 / 網路工具(語法樹匯入 + 執行時載得到)"),
    ("UNIT", ["test"], "test:各引擎自測(缺件 / 缺料照實記)"),
    ("UI_SYNC", ["synchronizer", "check"], "synchronizer check:HTML U/I 頁對收據(零寫入重核)"),
]
GRAY = {   # 沒有對應唯讀引擎的格:亮灰並寫原因(不另做掃描器)
    "INTEGRATION": "沒有唯讀的整合測試動詞(launch --run 會擷取寫庫)",
    "USER_TEST": "操作員用滑鼠走 U/I(人做的驗收,機器不代)",
}
RCPT = "VIA_Reports/vdf"          # VDF 資料庫引擎自己寫的收據(只讀):VERIFY · DB_STATUS_MATRIX · DB_CHECK
STALE_H = 48.0
ORDER = ["UNIT", "INTEGRATION", "SYSTEM", "USER_TEST", "OUTPUT_CHECK", "UI_SYNC", "PARAMS", "ACCEL_NET", "DB"]
ZH = {"UNIT": "UNIT 單元自測", "INTEGRATION": "INTEGRATION 整合", "SYSTEM": "SYSTEM 系統健康", "USER_TEST": "USER-TEST 操作員",
      "OUTPUT_CHECK": "輸出驗證", "UI_SYNC": "HTML U/I 同步", "PARAMS": "參數 · regex · 同義字 · SDD",
      "ACCEL_NET": "加速器 · 網路工具(生效)", "DB": "資料庫"}
RANK = {"GREEN": 0, "GRAY": 0, "YELLOW": 1, "RED": 2}


def _lamp_of(text: str, rc) -> str:
    lines = [x for x in (text or "").splitlines() if x.strip()]
    for line in reversed(lines[-6:]):                       # 中文燈標(synchronizer 等印 [紅] / [黃] / [綠])
        for tag, lamp in (("[紅]", "RED"), ("[黃]", "YELLOW"), ("[綠]", "GREEN")):
            if tag in line:
                return lamp
    for line in reversed(lines):
        m = re.search(r"\b(GREEN|YELLOW|RED)\b", line)
        if m and ("VDF_SystemManager" in line or "[橋閘]" in line or line.lstrip().startswith("[")):
            return m.group(1)
    if rc == 0:
        return "GREEN"
    return "YELLOW" if rc in (2, 3) else "RED"


def _summary(cell: str, text: str, rc) -> tuple:
    """回 (lamp, 一行摘要)。bridges 讀 JSON;其他讀判決行。"""
    if cell == "ACCEL_NET":
        try:
            j = json.loads(text[text.index("{"):text.rindex("}") + 1])
            miss = len(j.get("missing_accel") or []) + len(j.get("missing_net") or [])
            lamp = "GREEN" if not miss and rc == 0 else ("RED" if miss else "YELLOW")
            return lamp, f"加速器 {j.get('accel')} · 網路 {j.get('net_callers')} · 缺橋 {miss}"
        except (ValueError, TypeError, AttributeError):
            return ("RED" if rc not in (0, None) else "YELLOW"), "bridges --json 讀不到 JSON"
    lines = [x for x in (text or "").splitlines() if x.strip() and "SyntaxWarning" not in x and not x.startswith("<unknown>")]
    verdict = next((x for x in reversed(lines) if "VDF_SystemManager" in x or x.lstrip().startswith(("[黃]", "[紅]", "NEXT"))), lines[-1] if lines else "")
    return _lamp_of(text, rc), verdict.strip()[:180]


def _rjson(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8")), (time.time() - p.stat().st_mtime) / 3600.0
    except (OSError, ValueError):
        return None, None


def _norm(lamp) -> str:
    return {"PASS": "GREEN", "OK": "GREEN", "NODATA": "YELLOW", "FAIL": "RED"}.get(str(lamp).upper(), str(lamp).upper())


def from_receipts(base: Path) -> dict:
    """VDF 資料庫引擎的收據 → 輸出驗證 / 資料庫兩格。沒收據 = 灰;超過 48 小時 = 黃(過期)。"""
    rows = {}
    ver, a1 = _rjson(base / "VERIFY_latest.json")
    if ver is None:
        rows["OUTPUT_CHECK"] = {"lamp": "GRAY", "line": "沒有 VERIFY_latest.json(先經啟動器跑 db check → db verify)"}
    else:
        lamp = _norm(ver.get("lamp"))
        line = f"db verify {ver.get('lamp')} · 比對 {ver.get('rows_compared')} 表 · 差異 {len(ver.get('mismatches') or [])} · 收據 {a1:.0f}h 前"
        if a1 > STALE_H and lamp == "GREEN":
            lamp, line = "YELLOW", line + f" · 過期(>{STALE_H:.0f}h)"
        rows["OUTPUT_CHECK"] = {"lamp": lamp if lamp in RANK else "YELLOW", "line": line}
    mat, a2 = _rjson(base / "DB_STATUS_MATRIX_latest.json")
    chk, a3 = _rjson(base / "DB_CHECK_latest.json")
    if mat is None and chk is None:
        rows["DB"] = {"lamp": "GRAY", "line": "沒有 DB_STATUS_MATRIX / DB_CHECK 收據(先經啟動器跑 db check)"}
    else:
        lamps = [_norm(x.get("lamp")) for x in (mat, chk) if x]
        lamp = max([x for x in lamps if x in RANK] or ["YELLOW"], key=lambda x: RANK[x])
        age = min(x for x in (a2, a3) if x is not None)
        line = (f"DuckDB {mat.get('db_found')}/{mat.get('db_total')} 庫 · 表 {(lambda t: t if isinstance(t, int) else len(t or []))(mat.get('tables'))} · 矩陣 {mat.get('lamp')}" if mat else "沒有狀態矩陣")
        line += f" · db check {chk.get('lamp')} {json.dumps(chk.get('summary'), ensure_ascii=False)}" if chk else ""
        pq, a4 = _rjson(base / "VDF_PARQUET_VIEW_latest.json")      # parquet 增量庫(MDL020 DataPlane · DuckDB → parquet 只寫新鍵)
        if pq:
            lamp = max([lamp, _norm(pq.get("lamp")) if _norm(pq.get("lamp")) in RANK else "YELLOW"], key=lambda x: RANK[x])
            line += f" · parquet {pq.get('lamp')} {pq.get('start')}–{pq.get('end')} {json.dumps(pq.get('counts'), ensure_ascii=False)}"
        line += f" · 收據 {age:.0f}h 前"
        if age > STALE_H and lamp == "GREEN":
            lamp, line = "YELLOW", line + f" · 過期(>{STALE_H:.0f}h)"
        rows["DB"] = {"lamp": lamp, "line": line}
    return rows


def _run(args: list, timeout: float = 600.0) -> tuple:
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), *args], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout, cwd=str(HERE))
        return r.returncode, (r.stdout or "") + (r.stderr or ""), round(time.time() - t0, 1)
    except subprocess.TimeoutExpired:
        return None, "逾時", round(time.time() - t0, 1)


def monitor(lanes: int = 3, runner=None, out_dir=None, rcpt_dir=None) -> dict:
    runner = runner or _run
    rows = {}
    try:
        rec = from_receipts(Path(rcpt_dir) if rcpt_dir else VIA_ROOT / RCPT)
    except Exception as exc:  # noqa: BLE001 — 收據格式讀不懂:照實亮黃,不讓整張格掛掉
        rec = {c: {"lamp": "YELLOW", "line": f"收據讀不懂 {type(exc).__name__}: {str(exc)[:80]}"} for c in ("OUTPUT_CHECK", "DB")}
    for cell, r in rec.items():
        rows[cell] = {"rc": None, "secs": 0, "verb": "", "source": "收據(只讀)", **r}
    with ThreadPoolExecutor(max_workers=max(1, min(int(lanes), len(SOURCES)))) as ex:
        futs = {cell: ex.submit(runner, args) for cell, args, _ in SOURCES}
        for cell, args, why in SOURCES:
            rc, text, secs = futs[cell].result()
            lamp, line = _summary(cell, text, rc)
            rows[cell] = {"lamp": lamp, "rc": rc, "secs": secs, "verb": " ".join(args), "source": why, "line": line}
    for cell, why in GRAY.items():
        rows[cell] = {"lamp": "GRAY", "rc": None, "secs": 0, "verb": "", "source": "", "line": why}
    worst = max((rows[c]["lamp"] for c in rows), key=lambda x: RANK[x])
    lamp = "GREEN" if worst in ("GREEN", "GRAY") else worst
    res = {"tool": TAG, "system": "VDF", "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "lamp": lamp,
           "rows": [dict(cell=c, **rows[c]) for c in ORDER],
           "counts": {k: sum(1 for c in rows if rows[c]["lamp"] == k) for k in ("GREEN", "YELLOW", "RED", "GRAY")},
           "rule": "只彙總既有唯讀動詞;沒有對應引擎的格亮灰;灰不算綠也不算紅"}
    od = Path(out_dir) if out_dir else VIA_ROOT / OUT_DIR
    try:
        od.mkdir(parents=True, exist_ok=True)
        (od / "VDF_MONITOR_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        res["receipt"] = str(od / "VDF_MONITOR_latest.json")
        (od / "VDF_MONITOR_latest.html").write_text(render_html(res), encoding="utf-8")
        res["page"] = str(od / "VDF_MONITOR_latest.html")
    except OSError as exc:
        res["receipt"] = f"寫不出收據:{type(exc).__name__}"
    return res


def render_html(res: dict) -> str:
    """monitor 頁:骨架與 class 同 synchronizer 頁(wrap · card · lamp g/y/r/x · scroll);樣式只讀鎖定模板冊,不自訂任何顏色。"""
    import html as _h
    css, note = PRIOR.sy_template_css(VIA_ROOT) if callable(getattr(PRIOR, "sy_template_css", None)) else ("", "模板冊讀不到")
    k = {"GREEN": "g", "YELLOW": "y", "RED": "r", "GRAY": "x"}
    zh = {"g": "綠", "y": "黃", "r": "紅", "x": "灰"}

    def lamp(x):
        c = k.get(x, "x")
        return '<span class="lamp %s">%s</span>' % (c, zh[c])
    rows = "".join('<tr><td class="l">%s</td><td>%s</td><td><span class="mono">%s</span></td><td>%s</td></tr>'
                   % (lamp(r["lamp"]), _h.escape(ZH[r["cell"]]), _h.escape(r.get("verb") or r.get("source") or "—"), _h.escape(r["line"]))
                   for r in res["rows"])
    c = res["counts"]
    return ('<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            "<title>VDF 監控台 · 系統狀態</title><style>%s</style></head><body><div class=\"wrap\">"
            '<header><div class="caps">VIA · VDF · MONITOR</div><h1>VDF 監控台 · 系統狀態</h1>'
            '<div class="note">%s · %s · 模板 %s</div></header>'
            '<div class="verdict">%s<b>綠 %d · 黃 %d · 紅 %d · 灰 %d</b><span>%s</span></div>'
            '<section class="card"><h2>九格(只彙總既有引擎與收據;灰 = 沒有對應引擎或沒有收據)</h2><div class="scroll"><table><thead><tr>'
            '<th class="l">燈</th><th>格</th><th>來源</th><th>結果</th></tr></thead><tbody>%s</tbody></table></div></section>'
            "</div></body></html>") % (css, _h.escape(TAG), _h.escape(res["at"]), _h.escape(note), lamp(res["lamp"]), c["GREEN"], c["YELLOW"], c["RED"], c["GRAY"],
                                       _h.escape(res["rule"]), rows)


def _print(res: dict) -> None:
    c = res["counts"]
    print(f"[{TAG}] monitor {res['lamp']} · 綠 {c['GREEN']} · 黃 {c['YELLOW']} · 紅 {c['RED']} · 灰 {c['GRAY']} · 收據 {res.get('receipt')}", flush=True)
    for r in res["rows"]:
        print(f"  {r['lamp']:<6} {ZH[r['cell']]:<22} {('(' + r['verb'] + ' · ' + str(r['secs']) + 's)') if r['verb'] else ''} {r['line']}", flush=True)


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    if a[:1] == ["monitor"]:
        lanes = int(a[a.index("--lanes") + 1]) if "--lanes" in a and a.index("--lanes") + 1 < len(a) else 3
        res = monitor(lanes=lanes)
        if "--json" in a:
            print(json.dumps(res, ensure_ascii=False, indent=1))
        else:
            _print(res)
        return {"GREEN": 0, "YELLOW": 2, "RED": 1}[res["lamp"]]
    return PRIOR.main(a)


def selftest() -> int:
    import tempfile
    import threading
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    rc0 = PRIOR.selftest()
    print(f"=== {TAG} · 薄尾自測(monitor 只彙總既有唯讀動詞;零網路 · 假子行程)===")
    chk("⓪ 直接前版 %s 自測過" % PRIOR_PATH.name, rc0 == 0, f"rc {rc0}")
    canned = {
        "health": (0, "[VDF_SystemManager v0184] health GREEN · own_dir ✓"),
        "status": (2, "[VDF_SystemManager v0184] status YELLOW · health GREEN · sdd YELLOW"),
        "bridges --json": (0, 'x\n{"accel": "112/112", "net_callers": "9/9", "missing_accel": [], "missing_net": []}'),
        "test": (2, "[VDF_SystemManager v0184] test YELLOW · 測 25 · 通過 21 · 失敗 0"),
        "synchronizer check": (1, "NEXT: 同步收據超過 24 小時\n  [黃] 同步收據超過 24 小時"),
    }
    seen, lock, live = [], threading.Lock(), {"now": 0, "max": 0}

    def fake(args):
        with lock:
            seen.append(" ".join(args)); live["now"] += 1; live["max"] = max(live["max"], live["now"])
        time.sleep(0.05)
        with lock:
            live["now"] -= 1
        rc, text = canned[" ".join(args)]
        return rc, text, 0.05
    with tempfile.TemporaryDirectory() as td:
        res = monitor(lanes=2, runner=fake, out_dir=td, rcpt_dir=Path(td) / "no_receipts")
        by = {r["cell"]: r for r in res["rows"]}
        chk("① 只叫前版已有的五個唯讀動詞(沒有 launch / sync --apply / db)", sorted(seen) == sorted(canned), seen)
        chk("② 道數照 --lanes(2 道同時最多 2 支)", live["max"] <= 2, live)
        chk("③ 沒有對應引擎的兩格 + 沒收據的輸出驗證 / 資料庫亮灰並寫原因",
            all(by[c]["lamp"] == "GRAY" and by[c]["line"] for c in list(GRAY) + ["OUTPUT_CHECK", "DB"]))
        chk("④ bridges 讀 JSON:加速器 112/112 · 網路 9/9 · 缺橋 0 → 綠", by["ACCEL_NET"]["lamp"] == "GREEN" and "112/112" in by["ACCEL_NET"]["line"])
        chk("⑤ 總燈取最差(灰不算綠也不算紅)→ 黃;九格都在", res["lamp"] == "YELLOW" and [r["cell"] for r in res["rows"]] == ORDER)
        pg = (Path(td) / "VDF_MONITOR_latest.html").read_text(encoding="utf-8") if (Path(td) / "VDF_MONITOR_latest.html").is_file() else ""
        chk("⑥ 收據 + 頁寫在指定夾(不入倉)· 頁只用鎖定模板的 class(沒有自訂色碼)", (Path(td) / "VDF_MONITOR_latest.json").is_file()
            and 'class="lamp' in pg and pg.count("<tr>") >= 10 and not re.search(r"(color|background)\s*:\s*#", pg.split("</style>")[-1]))
        bad = dict(canned); bad["bridges --json"] = (1, '{"accel": "112/115", "net_callers": "9/9", "missing_accel": ["X.py"], "missing_net": []}')
        canned.clear(); canned.update(bad); seen.clear()
        rd = Path(td) / "rc"; rd.mkdir()
        (rd / "VERIFY_latest.json").write_text(json.dumps({"lamp": "PASS", "rows_compared": 51, "mismatches": []}), encoding="utf-8")
        (rd / "DB_STATUS_MATRIX_latest.json").write_text(json.dumps({"lamp": "GREEN", "db_found": 3, "db_total": 3, "tables": 2}), encoding="utf-8")
        (rd / "DB_CHECK_latest.json").write_text(json.dumps({"lamp": "RED", "summary": {"RED": 2}}), encoding="utf-8")
        rr = from_receipts(rd)
        chk("⑥b 收據 → 輸出驗證 PASS 綠 · 資料庫取最差(db check 紅 → 紅)", rr["OUTPUT_CHECK"]["lamp"] == "GREEN" and rr["DB"]["lamp"] == "RED", rr)
        res2 = monitor(lanes=3, runner=fake, out_dir=td, rcpt_dir=Path(td) / "no_receipts")
        chk("⑦ 缺橋 → 加速器格紅 · 總燈紅", res2["lamp"] == "RED" and {r["cell"]: r for r in res2["rows"]}["ACCEL_NET"]["lamp"] == "RED")
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑧ 加速器橋 · 網路橋在;本動詞不出網(沒有 _via_net() 呼叫)· 不碰 TA-Lib",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src and "_via_net()." not in body and "talib" not in body.lower())
    peer = [k for k in ("VIA_FROM_VCGC", "VIA_FROM_VRN") if re.search(r"environ(?:\[[\"']%s[\"']\]\s*=|\.setdefault\([\"']%s)" % (k, k), body)]
    chk("⑩ 系統獨立:不設他系統的入口旗標(本檔是 VDF 自己的入口;VCGC 只支援不干涉)", not peer, peer)
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑨ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), f"{len(pub)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
