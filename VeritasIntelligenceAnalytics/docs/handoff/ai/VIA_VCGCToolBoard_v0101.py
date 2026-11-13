#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_VCGCToolBoard v0101 — v0100 薄尾(前版一字不動):VRN / VDF 工具矩陣(vrnvdf 動詞)。

操作員 2026-11-13:「VDF VRN 現在用的工具 … 同類型留下一個 · 有版本號根據 VCGC 規範註冊 · 用 VCGC 檢視 …
VDF/VRN 間註冊目前成功的指令是否成功啟動 · 檢視輸出 · 檢驗註冊」「VRN VDF 就好」「VRN-2 為主 VRN-1 為輔,整合後通稱 VRN」。

一個家族一列(VDF / VRN 各自的管理器 engines 清單為準),欄:
  系統 · 家族 · 版本數 · 尾版 · 實測燈(管理器 test 的 PASS / ABSENT / NODATA / FAIL / 沒測)· rc ·
  VCGC 編號(編號冊有沒有這支尾版)· 元件冊(在 / 不在)· git 追蹤 · 同內容複本數 · 整理建議
整理建議只照證據寫,不自動刪任何檔:
  保留            尾版 · 有號 · 實測過
  修 / 補件       FAIL → 要修;ABSENT / NODATA → 缺套件或缺料(L16 不是壞)
  補登記          沒號或不在元件冊 → via-vcgc run CGC_MDL237_NumberingSystem --apply --scope <檔>
  不動(凍結)     同內容複本在 references / intake(凍結來源)
  遷移引用後可刪   系統夾裡同內容複本仍被引用 → 先把引用改指保留檔,再刪
另有兩塊:輸出(VRN-2 輸出冊列數 / 時間 · ENG049 報告矩陣燈 · VDF 擷取字典檔)· 重複檔分類統計。

資料來源(只讀):VIA_Reports/vcgc/VRNVDF_{engines,test}_<sys>_latest.{json,txt}(--refresh 時才跑兩個管理器重產,
  不帶 --refresh 就用上次的收據 → 收據超過 48 小時 = 過期)· 編號冊 · 元件冊 · git ls-files。
輸出:VIA_Reports/vcgc/VRNVDF_BOARD_latest.{json,html} + vrnvdf_ledger.jsonl(只增)。零網路 · 不寫冊 · 不用 TA-Lib。
用法:vrnvdf [--refresh] [--root D] [--no-write] · 其餘照 v0100(run · selftest)· --selftest
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
# [VIA:NET-BRIDGE] 留名:本版不出網
import collections
import glob
import hashlib
import html
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0101"
ENGINE = "VIA_VCGCToolBoard " + VERSION
HERE = Path(__file__).resolve().parent
STEM = "VIA_VCGCToolBoard"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
VIA = PRIOR.VIA

SYSTEMS = {  # 系統 → (管理器家族 glob, 系統夾, 顯示名)
    "VDF": ("functional modules/VDF/VDF_SystemManager_v*.py", "functional modules/VDF", "VDF"),
    "VRN": ("functional modules/VRN/VRN_SystemManager_v*.py", "functional modules/VRN", "VRN(VRN-2 為主 + VRN-1 為輔)"),
}
STATE_RX = re.compile(r"^\s*(PASS|FAIL|ABSENT|NODATA|SKIP|TIMEOUT|GATE)\s+(\S+)\s+·\s+rc\s+(-?\d+)")
FROZEN_RX = re.compile(r"/(references|intake)/")
OUT_DIR = "VIA_Reports/vcgc"


def __getattr__(name):
    return getattr(PRIOR, name)


def e(s) -> str:
    return html.escape("" if s is None else str(s))


# ───────── 收據(--refresh 才重跑管理器) ─────────
def manager(via: Path, sysn: str) -> Path | None:
    hits = sorted(glob.glob(str(via / SYSTEMS[sysn][0])), key=_vnum)
    return Path(hits[-1]) if hits else None


def refresh(via: Path, sysn: str, timeout: int = 5400) -> dict:
    sm = manager(via, sysn)
    out = via / OUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, VIA_FROM_VCGC="YES", PYTHONUTF8="1")
    res = {}
    for verb, args, ext in (("engines", ["engines", "--json"], "json"), ("test", ["test", "--max", "999"], "txt")):
        try:
            p = subprocess.run([sys.executable, str(sm)] + args, capture_output=True, text=True, timeout=timeout, cwd=str(via), env=env)
            txt, rc = p.stdout, p.returncode
        except subprocess.TimeoutExpired as ex:
            txt, rc = (ex.stdout or "") if isinstance(ex.stdout, str) else "", 124
        (out / f"VRNVDF_{verb}_{sysn}_latest.{ext}").write_text(txt, encoding="utf-8")
        res[verb] = rc
    return res


def parse_test(txt: str) -> dict:
    out = {}
    for line in txt.splitlines():
        m = STATE_RX.match(line)
        if m:
            out[m.group(2)] = {"state": m.group(1), "rc": int(m.group(3))}
    return out


def receipts(via: Path, sysn: str) -> tuple:
    out = via / OUT_DIR
    ej, tt = out / f"VRNVDF_engines_{sysn}_latest.json", out / f"VRNVDF_test_{sysn}_latest.txt"
    try:
        eng = json.loads(ej.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        eng = {}
    try:
        txt = tt.read_text(encoding="utf-8")
    except OSError:
        txt = ""
    at = datetime.fromtimestamp(tt.stat().st_mtime, timezone.utc) if tt.is_file() else None
    summary = next((l.strip() for l in reversed(txt.splitlines()) if " test " in l and "測 " in l), "")
    return eng, parse_test(txt), at, summary


# ───────── 註冊 · 追蹤 · 重複 ─────────
def numbered(via: Path) -> dict:
    out = {}
    for p in glob.glob(str(via / "supportive modules/registry/VIA_NumberBooks/VIA_NumberBook_*_v0100.jsonl")):
        if "_FNC_" in p or "_CLS_" in p:
            continue
        for line in open(p, encoding="utf-8"):
            if line.strip():
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                out.setdefault(r.get("source"), r.get("code"))
    return out


def tracked(via: Path, folders: list) -> set:
    try:
        p = subprocess.run(["git", "ls-files", *folders], capture_output=True, text=True, cwd=str(via), timeout=120)
        return set(p.stdout.splitlines())
    except (OSError, subprocess.TimeoutExpired):
        return set()


def duplicates(via: Path, files: set) -> dict:
    """{path: [同內容的其他路徑]} —— 只看 git 追蹤的 .py。"""
    by = collections.defaultdict(list)
    for f in files:
        if f.endswith(".py") and (via / f).is_file():
            by[hashlib.sha256((via / f).read_bytes()).hexdigest()].append(f)
    out = {}
    for group in by.values():
        if len(group) > 1:
            for f in group:
                out[f] = sorted(x for x in group if x != f)
    return out


def advise(row: dict) -> str:
    if row["state"] == "FAIL":
        return "修(實測失敗)"
    if not row["code"] or not row["in_inventory"]:
        return "補登記(--apply --scope 尾版)"
    if row["state"] in ("ABSENT", "NODATA"):
        return "補件 / 補料(L16 不是壞)"
    if row["dups"]:
        return "不動(凍結複本)" if all(FROZEN_RX.search(d) for d in row["dups"]) else "遷移引用後可刪複本"
    if row["state"] == "沒測":
        return "待測"
    return "保留"


def outputs(via: Path) -> list:
    rows = []
    for p in sorted(glob.glob(str(via / "VIA_Reports/vrn2/output/VRN2_*_latest.json"))):
        try:
            d = json.loads(Path(p).read_text(encoding="utf-8"))
            n = len(d if isinstance(d, list) else (d.get("rows") or []))
        except (OSError, ValueError):
            n = None
        rows.append({"系統": "VRN", "輸出": Path(p).name, "列數": n, "時間": datetime.fromtimestamp(os.path.getmtime(p), timezone.utc).strftime("%Y-%m-%d %H:%M")})
    mx = sorted(glob.glob(str(via / "VIA_Reports/vrn_reconcile_runs/matrix_*.json")))
    if mx:
        try:
            s = json.loads(Path(mx[-1]).read_text(encoding="utf-8")).get("summary", {})
            rows.append({"系統": "VRN", "輸出": Path(mx[-1]).name + "(報告矩陣)", "列數": f"個股 {s.get('stock', {}).get('lamps')} · 非個股 {s.get('nonstock', {}).get('lamps')}",
                         "時間": datetime.fromtimestamp(os.path.getmtime(mx[-1]), timezone.utc).strftime("%Y-%m-%d %H:%M")})
        except (OSError, ValueError):
            pass
    for p in sorted(glob.glob(str(via / "VIA_Reports/vdf_fetch/dict/*/*.parquet")) + glob.glob(str(via / "VIA_Reports/vdf_fetch/dict/*.duckdb"))):
        rows.append({"系統": "VDF", "輸出": str(Path(p).relative_to(via / "VIA_Reports/vdf_fetch")), "列數": "—",
                     "時間": datetime.fromtimestamp(os.path.getmtime(p), timezone.utc).strftime("%Y-%m-%d %H:%M")})
    return rows


def build_vrnvdf(via: Path, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    nb = numbered(via)
    inv_p = via / "supportive modules/registry/VIA_Component_Inventory_SSOT_v0100.json"
    inv = inv_p.read_text(encoding="utf-8") if inv_p.is_file() else ""
    tr = tracked(via, [v[1] for v in SYSTEMS.values()])
    dups = duplicates(via, tr)
    rows, systems = [], {}
    for sysn, (_, folder, label) in SYSTEMS.items():
        eng, tests, at, summ = receipts(via, sysn)
        age = round((now - at).total_seconds() / 3600, 1) if at else None
        for fam, f in sorted(eng.items()):
            t = f.get("tail", "")
            ts = tests.get(fam, {})
            r = {"系統": sysn, "家族": fam, "版本數": f.get("versions"), "尾版": t, "state": ts.get("state", "沒測"), "rc": ts.get("rc", "—"),
                 "code": nb.get(t), "in_inventory": bool(t) and t in inv, "tracked": t in tr, "dups": dups.get(t, [])}
            r["建議"] = advise(r)
            rows.append(r)
        mine = [r for r in rows if r["系統"] == sysn]
        cnt = collections.Counter(r["state"] for r in mine)
        lamp = "RED" if cnt.get("FAIL") else ("GRAY" if not mine or not at else ("YELLOW" if (age or 0) > PRIOR.STALE_HOURS or cnt.get("沒測") or
                                                                                cnt.get("ABSENT") or cnt.get("NODATA") else "GREEN"))
        systems[sysn] = {"label": label, "families": len(mine), "states": dict(cnt), "lamp": lamp, "receipt_at": at.isoformat() if at else None,
                         "age_hours": age, "summary": summ, "unnumbered": sum(1 for r in mine if not r["code"]),
                         "not_in_inventory": sum(1 for r in mine if not r["in_inventory"]), "advice": dict(collections.Counter(r["建議"] for r in mine))}
    groups = collections.Counter()
    seen = set()
    for f, others in dups.items():
        key = tuple(sorted([f] + others))
        if key in seen:
            continue
        seen.add(key)
        groups["凍結(references / intake)" if all(FROZEN_RX.search(x) for x in key) else "系統夾(仍被引用 → 先遷移)"] += len(key) - 1
    overall = PRIOR.worst([s["lamp"] for s in systems.values()]) if hasattr(PRIOR, "worst") else "YELLOW"
    return {"engine": ENGINE, "at": now.isoformat(timespec="seconds"), "systems": systems, "rows": rows, "outputs": outputs(via),
            "duplicates": {"extra_copies": dict(groups), "tracked_py": sum(1 for f in tr if f.endswith(".py"))}, "overall": overall,
            "rule": "黃不是綠 · 沒收據 = GRAY · 沒測 ≠ 綠 · 收據超過 48 小時 = 過期 · 本引擎不刪任何檔,只寫建議"}


COLS = ["系統", "家族", "版本數", "尾版", "state", "rc", "code", "in_inventory", "tracked", "dups", "建議"]
HEAD = {"state": "實測", "code": "VCGC 編號", "in_inventory": "元件冊", "tracked": "追蹤", "dups": "同內容複本"}


def to_html_vrnvdf(b: dict) -> str:
    color = {"PASS": "#2e7d32", "GREEN": "#2e7d32", "FAIL": "#c62828", "RED": "#c62828", "ABSENT": "#b26a00", "NODATA": "#b26a00",
             "YELLOW": "#b26a00", "沒測": "#6b7280", "GRAY": "#6b7280"}

    def cell(r, c):
        v = r.get(c)
        if c == "dups":
            v = f"{len(v)}" if v else "—"
        elif isinstance(v, bool):
            v = "在" if v else "不在"
        elif v in (None, ""):
            v = "—"
        sty = f' style="color:{color[v]};font-weight:600"' if isinstance(v, str) and v in color else ""
        tip = f' title="{e(chr(10).join(r["dups"]))}"' if c == "dups" and r.get("dups") else ""
        return f"<td{sty}{tip}>{e(v)}</td>"
    tiles = "".join(f'<div class="tile"><b style="color:{color.get(s["lamp"], "#000")}">{e(s["lamp"])}</b> {e(s["label"])}<br>家族 {s["families"]} · '
                    f'{e(json.dumps(s["states"], ensure_ascii=False))}<br>未編號 {s["unnumbered"]} · 不在元件冊 {s["not_in_inventory"]}<br>'
                    f'收據 {e(str(s["receipt_at"] or "—")[:16])}({e(s["age_hours"])} 小時前)<br><small>{e(s["summary"])}</small></div>'
                    for s in b["systems"].values())
    adv = "".join(f"<li>{e(k)}:{v}</li>" for s in b["systems"].values() for k, v in sorted(s["advice"].items()))
    rows = "".join("<tr>" + "".join(cell(r, c) for c in COLS) + "</tr>" for r in b["rows"])
    outs = "".join("<tr>" + "".join(f"<td>{e(o.get(c))}</td>" for c in ("系統", "輸出", "列數", "時間")) + "</tr>" for o in b["outputs"])
    dup = " · ".join(f"{k} 多出 {v} 份" for k, v in b["duplicates"]["extra_copies"].items()) or "沒有"
    return ("<!doctype html><html lang=zh-Hant><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>VRN / VDF 工具矩陣</title><style>body{font:13px system-ui;margin:16px;color:#1f2328;background:#fff}"
            ".tiles{display:flex;flex-wrap:wrap;gap:10px}.tile{border:1px solid #d0d7de;border-radius:8px;padding:8px 12px;min-width:260px}"
            ".w{overflow-x:auto}table{border-collapse:collapse}td,th{border:1px solid #d0d7de;padding:3px 6px;white-space:nowrap}th{background:#f6f8fa;position:sticky;top:0}"
            "</style>"
            f"<h2>VRN / VDF 工具矩陣 · 總燈 {e(b['overall'])} · {e(b['at'])} · {e(ENGINE)}</h2><p>{e(b['rule'])}</p>"
            f"<div class=tiles>{tiles}</div><h3>整理建議統計</h3><ul>{adv}</ul>"
            f"<h3>重複檔(git 追蹤 .py {b['duplicates']['tracked_py']} 支)</h3><p>{e(dup)}</p>"
            f"<h3>每個家族</h3><div class=w><table><tr>{''.join(f'<th>{e(HEAD.get(c, c))}</th>' for c in COLS)}</tr>{rows}</table></div>"
            f"<h3>輸出</h3><div class=w><table><tr><th>系統</th><th>輸出</th><th>列數</th><th>時間</th></tr>{outs}</table></div></html>")


def run_vrnvdf(via: Path, do_refresh: bool = False, no_write: bool = False) -> int:
    if do_refresh:
        for s in SYSTEMS:
            print(f"  [refresh] {s} 管理器 engines + test --max 999 · rc {refresh(via, s)}")
    b = build_vrnvdf(via)
    print(f"[{b['overall']}] {ENGINE} vrnvdf · {b['at']}")
    for s in b["systems"].values():
        print(f"  [{s['lamp']}] {s['label']} · 家族 {s['families']} · {json.dumps(s['states'], ensure_ascii=False)} · 未編號 {s['unnumbered']} · "
              f"不在元件冊 {s['not_in_inventory']} · 建議 {json.dumps(s['advice'], ensure_ascii=False)}")
    print(f"  重複檔:{json.dumps(b['duplicates'], ensure_ascii=False)} · 輸出 {len(b['outputs'])} 項")
    if not no_write:
        out = via / OUT_DIR
        out.mkdir(parents=True, exist_ok=True)
        (out / "VRNVDF_BOARD_latest.json").write_text(json.dumps(b, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        (out / "VRNVDF_BOARD_latest.html").write_text(to_html_vrnvdf(b), encoding="utf-8")
        with (out / "vrnvdf_ledger.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"at": b["at"], "engine": ENGINE, "overall": b["overall"],
                                 "systems": {k: {"lamp": v["lamp"], "states": v["states"]} for k, v in b["systems"].items()}}, ensure_ascii=False) + "\n")
        print("  落檔:" + str(out / "VRNVDF_BOARD_latest.html"))
    return 1 if b["overall"] == "RED" else 0


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")
    txt = "  PASS    VDF_ENG045_OutputHub · rc 0\n  NODATA  VDF_ENG071_GroupBacktest · rc 2\n  FAIL    VDF_ENG099_X · rc 1\n雜訊行"
    pt = parse_test(txt)
    chk("① 管理器 test 行解析:PASS / NODATA / FAIL + rc · 雜訊行略過", pt.get("VDF_ENG045_OutputHub") == {"state": "PASS", "rc": 0}
        and pt["VDF_ENG071_GroupBacktest"]["state"] == "NODATA" and pt["VDF_ENG099_X"]["rc"] == 1 and len(pt) == 3)
    base = {"state": "PASS", "code": "VIA-VDF-ENG1", "in_inventory": True, "dups": []}
    chk("② 建議:FAIL → 修 · 沒號 → 補登記 · NODATA → 補件 · 凍結複本 → 不動 · 系統夾複本 → 遷移引用 · 其餘保留",
        advise(dict(base, state="FAIL")).startswith("修") and advise(dict(base, code=None)).startswith("補登記")
        and advise(dict(base, state="NODATA")).startswith("補件") and advise(dict(base, dups=["x/references/intake/a.py"])).startswith("不動")
        and advise(dict(base, dups=["functional modules/VDF/a.py"])).startswith("遷移") and advise(base) == "保留")
    with tempfile.TemporaryDirectory() as td:
        via = Path(td)
        (via / OUT_DIR).mkdir(parents=True)
        (via / "functional modules/VDF").mkdir(parents=True)
        (via / "functional modules/VDF/VDF_ENG045_OutputHub_v0102.py").write_text("x=1\n", encoding="utf-8")
        (via / OUT_DIR / "VRNVDF_engines_VDF_latest.json").write_text(json.dumps({"VDF_ENG045_OutputHub": {"versions": 3, "tail": "functional modules/VDF/VDF_ENG045_OutputHub_v0102.py"},
                                                                                "VDF_ENG071_GroupBacktest": {"versions": 1, "tail": "functional modules/VDF/VDF_ENG071_GroupBacktest_v0100.py"}}), encoding="utf-8")
        (via / OUT_DIR / "VRNVDF_test_VDF_latest.txt").write_text(txt, encoding="utf-8")
        b = build_vrnvdf(via)
        v = b["systems"]["VDF"]
        chk("③ 夾具:VDF 2 家族 · 沒號 → 補登記(不冒充保留)· NODATA 系統燈不綠 · VRN 沒收據 = GRAY",
            v["families"] == 2 and v["unnumbered"] == 2 and v["lamp"] == "YELLOW" and b["systems"]["VRN"]["lamp"] == "GRAY"
            and all(r["建議"].startswith("補登記") for r in b["rows"]), v)
        h = to_html_vrnvdf(b)
        chk("④ HTML:系統磚 · 建議統計 · 家族表 · 輸出表 · VRN 標示 VRN-2 為主 + VRN-1 為輔",
            "每個家族" in h and "VRN-2 為主" in h and "整理建議統計" in h and "<th>實測</th>" in h)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 不刪檔 · 不出網 · 不用 TA-Lib · 不寫同意閘", "os.remove" + "(" not in src and "unlink" + "(" not in src and "urlopen" + "(" not in src
        and "import " + "talib" not in src and "VIA_NET_" + "CONSENT=" not in src)
    print(f"[selftest] {VERSION} 本版 {sum(ok)}/{len(ok)}")
    if not all(ok):
        return 1
    return PRIOR.selftest()


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if a[:1] == ["vrnvdf"]:
        root = a[a.index("--root") + 1] if "--root" in a else None
        via = Path(root).resolve() if root else VIA
        if (via / "VeritasIntelligenceAnalytics").is_dir():
            via = via / "VeritasIntelligenceAnalytics"
        return run_vrnvdf(via, do_refresh="--refresh" in a, no_write="--no-write" in a)
    return PRIOR.main(a)


if __name__ == "__main__":
    sys.exit(main())
