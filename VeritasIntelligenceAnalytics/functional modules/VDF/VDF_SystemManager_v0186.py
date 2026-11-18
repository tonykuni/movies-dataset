#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF SystemManager v0186 — 薄尾(v0185 一字不動):synchronizer(把 VDF 自己的頁面與收據對齊、連成一頁,並讀同儕自報的同步收據)。

操作員 2026-11-17:「每個系統一個 synchronizer 對 HTML U/I;已經做好的先重用,不要過度複雜」;2026-11-18:「到了 VRN VDF 也會將資訊交換,子系統也有此功能」。
本管理器已經有 sync(自己的冊,乾跑)· health · page(管理器矩陣頁)· peers(同儕只讀監控)· engine-matrix 這些動詞,缺的是:一個動詞把它們照順序跑完、核對「頁面是不是跟收據同一輪」、把自己的頁連成一頁、
並把這一輪寫成一份別的系統讀得到的收據。本版只多這一個動詞,其餘動詞一律交給前版(參數 / rc 不變;只增不減):
  synchronizer [run] [--steps a,b] [--wait 秒] [--no-open]   排隊 → 依序跑自己的既有動詞(都是唯讀 / 乾跑)→ 頁對收據 → 同儕自報 → 連結頁 → 收據
      步驟:books = sync --json(自己的冊有沒有漂移;乾跑)· health · page = page --json · peers
      頁對收據:管理器矩陣頁(page --json 印的結果由本動詞存成它的收據)· 引擎矩陣(html 對 json);核對頁在不在、這一輪有沒有更新、時間、燈、版本。
      同儕自報:只讀 VCGC / VRN-2 各自的 SYNC_latest.json,攤開對方的燈、時間、下一步,連到對方的同步台;不執行、不 import、不寫對方的夾。
      輸出(都在 VIA_Reports/vdf/manager/,不入倉):VDF_UI_Hub_latest.html · SYNC_latest.json(同儕讀這一份)· SYNC_ledger.jsonl(只增)· VDF_PAGE_latest.json。
  synchronizer check | --last | manifest   零寫入重核 | 只印上一輪收據 | 整合說明
兩盞燈分開記:同步燈(rc 由它決定:綠 0 · 黃 2 · 紅 1)與內容燈(各動詞自己報的紅黃)。同儕的燈不算進本系統的燈。
共用段 [VIA:SYNC-CORE:v0100] 三個系統各持有一份、內容相同(同加速器橋的做法);各系統只載自己這一份。樣式讀鎖定模板冊(資料),不 import 任何 VCGC 引擎。
對等:不經 VCGC、不要求任何他系統的旗標;不代跑 sync --apply、launch --run、編號。零網路(兩個標準橋在;本版不出網);不碰 TA-Lib;不讀寫同意閘。
不是 Windows 主機跑的不算主機實測。自測:python VDF_SystemManager_v0186.py --selftest
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
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[1]
TAG = "v0186"
SYSTEM = "VDF"
DISPLAY_NAME = "VDF SystemManager"
FAMILY = "VDF_SystemManager"
REP = "VIA_Reports/vdf/manager/"                                   # 本管理器自己的輸出夾(相對 VIA 夾)


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load(path: Path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
PRIOR = _load(PRIOR_PATH, "vdf_manager_prior_for_" + TAG)


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    return getattr(PRIOR, name)


# ===== [VIA:SYNC-CORE:v0100] 同步器共用段(VCGC · VDF · VRN-2 各自持有一份,內容相同;各系統只載自己這一份,不互相 import) =====
# 一個系統自己的頁面與收據怎麼對齊:依序跑自己的既有動詞 → 頁對收據 → 讀同儕自報的同步收據(只讀)→ 連結頁 → 收據。
# 只吃一個設定(cfg);不認得任何系統名稱。寫檔只經 sy_write / sy_append,都落在 cfg["out"](VIA_Reports 底下,不入倉)。
import datetime as _sy_dt
import hashlib as _sy_hashlib
import html as _sy_html
import json as _sy_json
import os as _sy_os
import platform as _sy_platform
import re as _sy_re
import subprocess as _sy_subprocess
import sys as _sy_sys
import time as _sy_time
from pathlib import Path as _SyPath

SY_CORE = "v0100"
SY_LN = {"g": "綠", "y": "黃", "r": "紅", "x": "灰"}
SY_UP = {"g": "GREEN", "y": "YELLOW", "r": "RED", "x": "GRAY"}
SY_DOWN = {"GREEN": "g", "YELLOW": "y", "RED": "r", "GRAY": "x", "ABSENT": "x", "NODATA": "x"}
SY_SEV = {"r": 3, "y": 2, "g": 1, "x": 0}
SY_RC = {"g": 0, "y": 2, "r": 1, "x": 2}
SY_RECEIPT, SY_LEDGER, SY_LOCK = "SYNC_latest.json", "SYNC_ledger.jsonl", "SYNC.lock"
SY_STALE_H = 24
SY_STAMP = _sy_re.compile(r"(20\d\d-\d\d-\d\d)[T ](\d\d:\d\d(?::\d\d)?)(?:\.\d+)?(Z|\s?[+-]\d\d:?\d\d)?")
SY_TZ8 = _sy_dt.timezone(_sy_dt.timedelta(hours=8))
SY_SCOPE = "同步燈:步驟有沒有跑完、頁與收據是不是同一輪。不是任何系統的業務驗收;內容燈另記;同儕的燈是對方自報,只攤開不代修;不是 Windows 主機跑的不算主機實測。"
SY_NOISE = ("[必用功能]", "[政策]", "[步驟]", "[流程]", "[強制]", "[監控]", "[github]", "[子系統]", "END_PASTE", "實測:", "<unknown>")


def sy_worst(lamps) -> str:
    seen = [x for x in lamps if x in SY_SEV and x != "x"]
    return max(seen, key=lambda x: SY_SEV[x]) if seen else "x"


def sy_json(p):
    try:
        return _sy_json.loads(_SyPath(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def sy_vnum(p) -> int:
    m = _sy_re.search(r"_v(\d{4})$", _SyPath(p).stem)
    return int(m.group(1)) if m else -1


def sy_pick(base, pattern: str):
    """樣式(相對 base)對到的檔取版號最高的;沒有版號的照檔名。"""
    hits = [p for p in _SyPath(base).glob(pattern) if p.is_file()]
    return max(hits, key=lambda p: (sy_vnum(p), p.name)) if hits else None


def sy_get(d, key):
    """a.b.c 取巢狀值;任何一層不在回 None。"""
    for k in str(key).split("."):
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def sy_whens(v) -> list:
    """一個時間字樣可能代表的時刻:有寫時區就一個;沒寫就當本機、+08:00、UTC 三種都算(頁面與收據常常一個寫本機一個寫 UTC)。"""
    m = SY_STAMP.search(str(v or ""))
    if not m:
        return []
    hm = m.group(2) if len(m.group(2)) > 5 else m.group(2) + ":00"
    try:
        d = _sy_dt.datetime.strptime(m.group(1) + " " + hm, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return []
    tz = (m.group(3) or "").strip()
    if tz == "Z":
        return [d.replace(tzinfo=_sy_dt.timezone.utc)]
    if tz:
        sign = 1 if tz[0] == "+" else -1
        digits = tz[1:].replace(":", "")
        return [d.replace(tzinfo=_sy_dt.timezone(sign * _sy_dt.timedelta(hours=int(digits[:2]), minutes=int(digits[2:] or 0))))]
    return [d.astimezone(), d.replace(tzinfo=SY_TZ8), d.replace(tzinfo=_sy_dt.timezone.utc)]


def sy_when(v):
    w = sy_whens(v)
    return w[0] if w else None


def sy_head(text: str) -> str:
    """頁面的開頭那一段(去掉樣式與腳本;有 <header> 就取它)。"""
    body = _sy_re.sub(r"<(style|script)\b.*?</\1>", "", text, flags=_sy_re.S)
    m = _sy_re.search(r"<header\b.*?</header>", body, _sy_re.S)
    return m.group(0) if m else body[:3000]


def sy_time_ok(text: str, rt, start=None, tol: float = 120.0) -> bool:
    """頁上的時間是不是收據那一輪:收據時間原字樣出現在頁上;或頁面開頭有一個時間落在 [start, rt](沒有 start 就 rt 前後 tol 秒)之內。"""
    if not rt:
        return False
    if len(str(rt)) >= 16 and str(rt) in text:
        return True
    ends = sy_whens(rt)
    begins = sy_whens(start) if start else []
    for m in SY_STAMP.finditer(sy_head(text)):
        for p in sy_whens(m.group(0)):
            for e in ends:
                lo = min((b for b in begins), default=e - _sy_dt.timedelta(seconds=tol)) - _sy_dt.timedelta(seconds=60 if begins else 0)
                hi = e + _sy_dt.timedelta(seconds=60 if begins else tol)
                if lo <= p <= hi:
                    return True
    return False


def sy_local(ts: float) -> str:
    return _sy_dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def sy_utc(d=None) -> str:
    return (d or _sy_dt.datetime.now(_sy_dt.timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")


def sy_host() -> dict:
    s = _sy_platform.system()
    box = _SyPath("/.dockerenv").exists() or bool(_sy_os.environ.get("CLAUDE_CODE_REMOTE") or _sy_os.environ.get("container"))
    return {"system": s, "container": box, "counts_as_host_run": s == "Windows" and not box}


def sy_hostline(h: dict) -> str:
    return "Windows 主機實跑" if h.get("counts_as_host_run") else "%s%s:這一輪不算主機實測" % (h.get("system") or "不明", "(容器)" if h.get("container") else "")


def sy_step_json(text: str):
    """子行程印的 JSON(第一個 { 到最後一個 });不是 JSON 回 None。"""
    try:
        d = _sy_json.loads(text[text.index("{"):text.rindex("}") + 1])
    except ValueError:
        return None
    return d if isinstance(d, dict) else None


def sy_verdict_line(text: str) -> str:
    """子行程輸出只留一行判決。"""
    lines = [x.strip() for x in text.splitlines() if x.strip() and not x.strip().startswith(SY_NOISE) and "SyntaxWarning" not in x]
    keys = ("RED", "YELLOW", "GREEN", "紅", "黃", "綠", "[同步]", "→", "NEXT")
    hit = [x for x in lines if any(k in x for k in keys) and not x.startswith(("{", "}", '"'))]
    d = sy_step_json(text)
    if not hit and d is not None:
        return ("lamp %s · " % d.get("lamp") if d.get("lamp") else "") + " · ".join("%s %s" % (k, v) for k, v in d.items() if k != "lamp" and not isinstance(v, (dict, list)))[:120]
    return ((hit or lines or ["(沒有輸出)"])[-1])[:150]


def sy_spawn(cmd: list, env: dict, timeout: float, label: str, cwd=None, beat: float = 20.0):
    """跑一個子行程;每 beat 秒印一行還在跑;逾時就停。回 (rc 或 None, 文字)。"""
    p = _sy_subprocess.Popen(cmd, env=env, cwd=cwd, stdout=_sy_subprocess.PIPE, stderr=_sy_subprocess.STDOUT)
    t0 = _sy_time.time()
    while True:
        try:
            data, _ = p.communicate(timeout=beat)
            return p.returncode, (data or b"").decode("utf-8", "replace")
        except _sy_subprocess.TimeoutExpired:
            el = _sy_time.time() - t0
            if el > timeout:
                p.kill()
                data, _ = p.communicate()
                return None, (data or b"").decode("utf-8", "replace")
            print("      … %s 還在跑 %d 秒(上限 %d)" % (label, el, timeout), flush=True)


def sy_judge_step(step: dict, rc, text: str, base, t0: float, secs: float) -> dict:
    """一步的兩盞燈:lamp = 同步(跑完 + 該更新的檔有更新);content = 這個動詞自己報的紅黃。books 類的步驟看它印的內容,不只看 rc。"""
    miss = []
    for pat in step.get("out") or []:
        p = sy_pick(base, pat)
        if p is None or p.stat().st_mtime < t0 - 2:
            miss.append(pat.rsplit("/", 1)[-1])
    row = {"id": step["id"], "name": step["name"], "argv": " ".join(step["argv"]), "rc": rc, "secs": round(secs, 1), "line": sy_verdict_line(text), "content": None, "note": ""}
    if rc is None:
        row["lamp"], row["note"] = "r", "逾時(超過 %d 秒,已停)" % step["timeout"]
    elif rc not in step["ok"]:
        row["lamp"], row["note"] = "r", "沒跑完(rc %s)" % rc
    elif miss:
        row["lamp"], row["note"] = "r", "跑完但沒更新:" + "、".join(miss)
    elif step.get("state"):
        why = step["state"](text)
        row["lamp"] = "g" if not why else "y"
        row["note"] = "" if not why else "%s(%s;要操作員批准才寫冊,本動詞不代跑)" % (step.get("state_zh", "冊與樹不同步"), why)
        if why:
            row["line"] = why
    else:
        row["lamp"] = "g"
        d = sy_step_json(text) or {}
        row["content"] = SY_DOWN.get(str(d.get("lamp")), None) if step.get("json_lamp") and d.get("lamp") else None
        if row["content"] is None:
            row["content"] = (step.get("rc_lamp") or {0: "g", 2: "y", 1: "r"}).get(rc, "y")
        if row["content"] == "x":
            row["content"] = "y"
    return row


def sy_run_step(cfg: dict, step: dict, actor: str = "") -> dict:
    argv = list(step["argv"]) + (["--actor", actor] if actor and step.get("actor") else [])
    out = _SyPath(cfg["out"])
    t0, started = _sy_time.time(), sy_utc()
    if cfg.get("prior") is None:
        rc, text = 3, "要轉交的前版不在"
    else:
        rc, text = sy_spawn([_sy_sys.executable, str(cfg["prior"]), *argv], cfg["env"](), step["timeout"], step["name"], cwd=str(cfg["base"]))
    sy_write(out / ("SYNC_step_%s.log" % step["id"]), text)
    d = sy_step_json(text)
    if step.get("save") and d is not None and rc is not None and rc in step["ok"]:
        sy_write(_SyPath(cfg["base"]) / step["save"], _sy_json.dumps(dict(d, started=started, at=sy_utc(), verb=" ".join(argv), saved_by=cfg["engine"]), ensure_ascii=False, indent=1))
    return sy_judge_step(step, rc, text, cfg["base"], t0, _sy_time.time() - t0)


def sy_pair_check(spec: dict, base, t0=None, ran=(), now=None, tail: str = "", version: str = "") -> dict:
    """一張頁對它的收據。t0 / ran 有給 = 這一輪剛跑完(要求有更新);沒給 = 只核對現況。"""
    now = now or _sy_dt.datetime.now(_sy_dt.timezone.utc)
    base = _SyPath(base)
    row = {"id": spec["id"], "name": spec["name"], "page": "", "path": "", "receipt": (spec.get("receipt") or "").rsplit("/", 1)[-1], "lamp": "g", "page_time": "", "receipt_time": "", "version": "", "note": ""}
    pg = sy_pick(base, spec["page"])
    if pg is None:
        own = spec.get("step") is not None
        row.update(lamp="r" if own else "x", note="頁不在" + ("" if own else "(還沒跑過 %s)" % spec.get("by", "它的動詞")))
        return row
    row["page"], row["path"], row["page_time"] = pg.name, str(pg), sy_local(pg.stat().st_mtime)
    try:
        text = pg.read_text(encoding="utf-8", errors="replace")
    except OSError:
        row.update(lamp="r", note="頁讀不到")
        return row
    notes, lamp = [], "g"
    if t0 is not None and spec.get("step") in ran and pg.stat().st_mtime < t0 - 2:
        lamp = "r"
        notes.append("這一輪沒更新")
    if not spec.get("receipt"):
        has_t, has_v = bool(SY_STAMP.search(text)), bool(_sy_re.search(r"(?<![A-Za-z0-9])v\d{4}(?!\d)", text))
        if not (has_t and has_v):
            lamp = sy_worst([lamp, "y"])
            notes.append("頁上沒有" + "、".join(n for n, ok in (("產生時間", has_t), ("版本", has_v)) if not ok) + "(只能看檔案時間)")
        row.update(lamp=lamp, note=";".join(notes))
        return row
    rec = sy_json(base / spec["receipt"])
    if not isinstance(rec, dict):
        own = spec.get("step") is not None
        row.update(lamp="r" if own else "y", note="收據不在或讀不懂")
        return row
    rt = sy_get(rec, spec["time"]) if spec.get("time") else None
    row["receipt_time"] = str(rt or "")
    if spec.get("time") and not sy_time_ok(text, rt, sy_get(rec, spec["time_start"]) if spec.get("time_start") else None):
        lamp = "r"
        notes.append("頁上的時間對不上收據(不是同一輪)")
    if spec.get("lamp"):
        want = str(sy_get(rec, spec["lamp"]) or "")
        if spec.get("lamp_re"):
            m = _sy_re.search(spec["lamp_re"], text)
            got = m.group(1) if m else ""
            good = bool(want) and got == want
        else:
            got, good = want, bool(want) and want in sy_head(text) + text[:20000]
        if not good:
            lamp = "r"
            notes.append("頁上的燈(%s)不是收據的燈(%s)" % (got or "沒有", want or "沒有"))
    if spec.get("parts"):
        parts = sy_get(rec, spec["parts"]) or {}
        bad = [k for k, v in parts.items() if not _sy_re.search(_sy_re.escape(str(k)) + r"\s*</td>\s*<td[^>]*>\s*" + _sy_re.escape(str(v)) + r"\s*</td>", text)]
        if bad or not parts:
            lamp = "r"
            notes.append("頁上這幾項的燈不是收據的燈:" + "、".join(bad[:6]) if bad else "收據沒有分項")
    if spec.get("ver"):
        v = str(sy_get(rec, spec["ver"]) or "")
        m = _sy_re.search(r"v\d{4}", v)
        tag = (spec.get("ver_prefix", "") + v) if spec.get("ver_prefix") else (m.group(0) if m else v)
        row["version"] = tag
        if not tag or tag not in text:
            lamp = sy_worst([lamp, "y"])
            notes.append("頁上沒有收據的版本(%s)" % (tag or "收據沒寫"))
    d = sy_when(rt)
    if lamp != "r" and spec.get("step") not in ran and d is not None and (now - d).total_seconds() > SY_STALE_H * 3600:
        lamp = sy_worst([lamp, "y"])
        notes.append("證據超過 %d 小時(%d 小時前)" % (SY_STALE_H, (now - d).total_seconds() // 3600))
    if spec.get("tail_key") and lamp != "r" and tail and _SyPath(str(sy_get(rec, spec["tail_key"]) or "")).stem not in ("", tail):
        lamp = sy_worst([lamp, "y"])
        notes.append("%s是 %s 跑的,入口現在是 %s(重跑 %s)" % (spec["name"], row["version"] or "前一版", version, spec.get("by", "它")))
    row.update(lamp=lamp, note=";".join(notes))
    return row


def sy_link_rows(base, links) -> list:
    rows = []
    for name, rel in links:
        p = sy_pick(base, rel) if "*" in rel else _SyPath(base) / rel
        ok = p is not None and p.is_file()
        rows.append({"name": name, "path": str(p) if ok else "", "exists": ok, "time": sy_local(p.stat().st_mtime) if ok else "", "lamp": "x",
                     "note": "有檔;不在本輪同步範圍" if ok else "沒跑過(檔不在)"})
    return rows


def sy_peer_rows(base, peers, now=None) -> list:
    """同儕自報的同步收據(只讀:不執行、不 import、不寫對方的夾)。燈是對方自己報的,不算進本系統的同步燈。"""
    now = now or _sy_dt.datetime.now(_sy_dt.timezone.utc)
    rows = []
    for peer in peers:
        rp, hub = _SyPath(base) / peer["receipt"], _SyPath(base) / peer["hub"]
        rec = sy_json(rp)
        row = {"system": peer["system"], "zh": peer.get("zh", ""), "lamp": "x", "content": "", "at": "", "engine": "", "next": "", "note": "", "hub": str(hub) if hub.is_file() else ""}
        if not isinstance(rec, dict):
            row["note"] = "對方的同步收據讀不懂" if rp.is_file() else "對方還沒有同步收據(它自己的 synchronizer 還沒跑過)"
        else:
            d = sy_when(rec.get("at"))
            old = d is None or (now - d).total_seconds() > SY_STALE_H * 3600
            row.update(lamp=str(rec.get("lamp_raw") or "x") if str(rec.get("lamp_raw")) in SY_LN else "x", content=str(rec.get("content_raw") or ""), at=str(rec.get("at") or ""),
                       engine=str(rec.get("engine") or ""), next=str(rec.get("next") or "")[:160], note=("超過 %d 小時沒更新;" % SY_STALE_H if old else "") + sy_hostline(rec.get("host") or {}))
        rows.append(row)
    return rows


def sy_template_css(base):
    """鎖定模板的樣式(讀冊,不 import 任何引擎):VIA_UI_WorkPlatform_TemplateLock 尾版的 css + 它釘住的 token 冊。雜湊不符或冊不在 → 不套樣式並照實說。回 (css, 說明)。"""
    reg = _SyPath(base) / "supportive modules" / "registry"
    lock = sy_pick(reg, "VIA_UI_WorkPlatform_TemplateLock_v*.json")
    if lock is None:
        return "", "模板鎖冊不在(頁面不套樣式)"
    try:
        b = _sy_json.loads(lock.read_text(encoding="utf-8"))
        css = b["css"]
        if _sy_hashlib.sha256(css.encode("utf-8")).hexdigest() != b.get("css_sha256"):
            return "", "%s 的 css 與鎖的雜湊不符(頁面不套樣式)" % lock.name
        tf = b["tokens_from"]
        tb = reg / ("%s_%s.json" % (tf["family"], tf["pinned"]))
        if not tb.exists():
            return "", "釘住的 token 冊 %s 不在(頁面不套樣式)" % tb.name
        if _sy_hashlib.sha256(tb.read_bytes().replace(b"\r\n", b"\n")).hexdigest() != tf.get("sha256"):
            return "", "token 冊 %s 與鎖的雜湊不符(頁面不套樣式)" % tb.name
        tokens = _sy_json.loads(tb.read_text(encoding="utf-8"))["tokens"]
        root = ":root{" + ";".join("--%s:%s" % (k, v) for k, v in tokens.items() if "<" not in str(v) and "}" not in str(v)) + "}"
        return root + "\n" + css, "%s · token %s" % (lock.stem, tb.stem)
    except (OSError, ValueError, KeyError, TypeError) as e:
        return "", "模板讀不到(%s;頁面不套樣式)" % type(e).__name__


def sy_href(target, basedir) -> str:
    try:
        rel = _sy_os.path.relpath(str(target), str(basedir)).replace(_sy_os.sep, "/")
    except ValueError:                                   # Windows 不同磁碟
        return _SyPath(target).resolve().as_uri()
    return "/".join(_sy_html.escape(seg, quote=True).replace(" ", "%20") for seg in rel.split("/"))


def sy_render(rec: dict, out, css: str, tpl_note: str, cfg: dict) -> str:
    E = _sy_html.escape

    def lampc(k):
        return '<span class="lamp %s">%s</span>' % (k if k in SY_LN else "x", SY_LN.get(k, "灰"))

    def tr(cells):
        return "<tr>" + "".join('<td class="l">%s</td>' % c if i == 0 else "<td>%s</td>" % c for i, c in enumerate(cells)) + "</tr>"

    def link(path, label):
        return '<a href="%s">%s</a>' % (sy_href(path, out), E(label)) if path else E(label)

    steps = "".join(tr([lampc(s["lamp"]), E(s["name"]), '<span class="mono">%s</span>' % E(s["argv"]), lampc(s["content"]) if s.get("content") else "—",
                        E("—" if s.get("rc") is None else str(s["rc"])), E("%s 秒" % s["secs"]), E(s.get("note") or s.get("line") or "")]) for s in rec["steps"])
    pages = "".join(tr([lampc(p["lamp"]), link(p.get("path"), p["name"]), '<span class="mono">%s</span>' % E(p["page"] or "—"), '<span class="mono">%s</span>' % E(p["receipt"] or "沒有收據"),
                        E(p["page_time"] or "—"), E(p["receipt_time"] or "—"), E(p["version"] or "—"), E(p["note"] or "頁與收據同一輪")]) for p in rec["pages"])
    peers = "".join(tr([lampc(k["lamp"]), link(k.get("hub"), "%s %s" % (k["system"], k.get("zh") or "")), lampc(k["content"]) if k.get("content") else "—", E(k["at"] or "—"),
                        '<span class="mono">%s</span>' % E(k["engine"] or "—"), E(k["next"] or "—"), E(k["note"])]) for k in rec["peers"])
    links = "".join(tr([lampc(k["lamp"]), link(k["path"] if k["exists"] else "", k["name"]), E(k["time"] or "—"), E(k["note"])]) for k in rec["links"])
    cli = cfg["cli"]
    return ('<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            "<title>%s 同步台 · 頁面與收據</title><style>%s</style></head><body><div class=\"wrap\">"
            '<header><div class="caps">VIA · %s · SYNCHRONIZER</div><h1>%s 同步台 · 頁面與收據</h1>'
            '<div class="note">%s · 收據 %s · %s · 模板 %s · %s</div></header>'
            '<div class="verdict"><span class="lamp %s">%s</span><b>同步 %s · 內容 %s</b><span>%s</span></div>'
            '<section class="card"><h2>① 頁面(點名稱開頁;每一張都對過它的收據)</h2><div class="scroll"><table><thead><tr><th class="l">燈</th><th>頁</th><th>檔</th><th>收據</th>'
            "<th>頁的時間</th><th>收據的時間</th><th>版本</th><th>說明</th></tr></thead><tbody>%s</tbody></table></div></section>"
            '<section class="card"><h2>② 同步步驟(依序;同步燈與內容燈分開)</h2><div class="scroll"><table><thead><tr><th class="l">同步</th><th>步驟</th><th>動詞</th><th>內容</th>'
            "<th>rc</th><th>耗時</th><th>說明</th></tr></thead><tbody>%s</tbody></table></div>"
            '<div class="note">排隊:%s。子行程不逐頁跳出;%s</div></section>'
            '<section class="card"><h2>③ 其他系統自報的同步(只讀;點名稱開對方的同步台)</h2><div class="scroll"><table><thead><tr><th class="l">同步</th><th>系統</th><th>內容</th><th>對方收據時間</th>'
            "<th>對方入口</th><th>對方的下一步</th><th>說明</th></tr></thead><tbody>%s</tbody></table></div>"
            '<div class="note">各系統對等:這裡只讀對方自己寫的收據,不執行、不改對方;對方的燈不算進本系統的同步燈。</div></section>'
            '<section class="card"><h2>④ 其他頁與檔(只連結,不在本輪同步範圍)</h2><div class="scroll"><table><thead><tr><th class="l">燈</th><th>頁</th><th>檔案時間</th><th>說明</th></tr></thead>'
            "<tbody>%s</tbody></table></div></section>"
            '<section class="card"><h2>⑤ 指令</h2><div class="note mono">%s synchronizer · %s synchronizer check · %s synchronizer --last · %s synchronizer manifest</div>'
            '<div class="note">%s</div></section></div></body></html>') % (
        E(cfg["system"]), css, E(cfg["system"]), E(cfg["system"]), E(rec["local"]), E(rec["at"]), E(rec["engine"]), E(tpl_note), E(sy_hostline(rec["host"])),
        rec["lamp_raw"], SY_LN[rec["lamp_raw"]], SY_LN[rec["lamp_raw"]], SY_LN.get(rec["content_raw"], "灰"), E("NEXT: " + rec["next"]), pages, steps, E(rec["lock"]),
        E(cfg.get("does_not_zh", "")), peers, links, cli, cli, cli, cli, E(SY_SCOPE))


def sy_next_line(steps: list, pages: list, partial: bool) -> str:
    for want in ("r", "y"):
        for s in steps:
            if s["lamp"] == want:
                return "步驟「%s」%s:%s" % (s["name"], SY_LN[want], s.get("note") or s.get("line"))
        for p in pages:
            if p["lamp"] == want:
                return "頁「%s」%s:%s" % (p["name"], SY_LN[want], p["note"])
    if partial:
        return "這一輪只跑了部分步驟;要完整同步就不帶 --steps 再跑一次。"
    bad = [s["name"] for s in steps if s.get("content") in ("r", "y")]
    return ("頁與收據都同一輪。內容仍有紅黃(%s),到各頁看細項。" % "、".join(bad)) if bad else "頁與收據都同一輪,沒有要處理的。"


def sy_print_card(rec: dict, cfg: dict, ran: bool) -> None:
    out = _SyPath(cfg["out"])
    print("[%s synchronizer] 同步 %s · 內容 %s · %d 步 %s 秒%s" % (cfg["system"], SY_LN.get(rec.get("lamp_raw"), "灰"), SY_LN.get(rec.get("content_raw"), "灰"),
                                                          len(rec.get("steps") or []), rec.get("secs"), "" if ran else " · 上一輪 %s" % rec.get("at")))
    for s in rec.get("steps") or []:
        print("  [%s] %s%s · %s" % (SY_LN.get(s["lamp"], "灰"), s["name"], (" · 內容 %s" % SY_LN[s["content"]]) if s.get("content") else "", s.get("note") or s.get("line") or ""))
    pg = rec.get("pages") or []
    cnt = {k: sum(1 for p in pg if p["lamp"] == k) for k in "gyrx"}
    print("  [頁] %d 張:綠 %d · 黃 %d · 紅 %d · 灰 %d" % (len(pg), cnt["g"], cnt["y"], cnt["r"], cnt["x"]))
    for p in pg:
        if p["lamp"] in ("r", "y"):
            print("       %s %s:%s" % (SY_LN[p["lamp"]], p["name"], p["note"]))
    for k in rec.get("peers") or []:
        print("  [同儕] %s %s%s · %s" % (k["system"], SY_LN.get(k["lamp"], "灰"), (" · 內容 %s" % SY_LN.get(k["content"], "灰")) if k.get("content") else "", k["at"] or k["note"]))
    print("[主機] %s" % sy_hostline(rec.get("host") or {}))
    print("[U/I] %s" % (out / cfg["hub"]))
    print("[收據] %s" % (out / SY_RECEIPT))
    print("NEXT: %s" % rec.get("next"))


def sy_write(p, text: str) -> None:
    p = _SyPath(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = _SyPath(str(p) + ".%d.tmp" % _sy_os.getpid())
    tmp.write_text(text, encoding="utf-8", newline="\n")
    _sy_os.replace(tmp, p)


def sy_append(p, line: str) -> None:
    with open(p, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(line + "\n")


def sy_run(cfg: dict, actor: str = "", no_open: bool = False, only=None, wait: float = 5.0, runner=None, locker=None) -> int:
    out, base = _SyPath(cfg["out"]), _SyPath(cfg["base"])
    out.mkdir(parents=True, exist_ok=True)
    runner = runner or sy_run_step
    cm, lock_note = (locker or cfg["locker"])(out, wait)
    chosen = [s for s in cfg["steps"] if not only or s["id"] in only]
    if only and len(chosen) != len(set(only)):
        print("[%s] 黃 · --steps 有不認得的名稱;可用:%s" % (cfg["tag"], "、".join(s["id"] for s in cfg["steps"])))
        return 2

    def body() -> int:
        t0 = _sy_time.time()
        at = _sy_dt.datetime.now(_sy_dt.timezone.utc).replace(microsecond=0)
        print("[%s] synchronizer:%d 步依序跑" % (cfg["tag"], len(chosen)), flush=True)
        steps = []
        for i, s in enumerate(chosen, 1):
            print("  %d/%d(%d%%) %s …" % (i, len(chosen), (i - 1) * 100 // len(chosen), s["name"]), flush=True)
            steps.append(runner(cfg, s, actor))
        ran = {s["id"] for s in steps}
        pages = [sy_pair_check(p, base, t0, ran, tail=cfg["engine"], version=cfg["version"]) for p in cfg["pages"]]
        partial = len(chosen) < len(cfg["steps"])
        lamp = sy_worst([s["lamp"] for s in steps] + [p["lamp"] for p in pages] + (["y"] if partial else []))
        content = sy_worst([s["content"] for s in steps if s.get("content")])
        rec = {"schema": "VIA.Synchronizer.Receipt.v1", "core": SY_CORE, "system": cfg["system"], "receipt": "ui-sync", "engine": cfg["engine"], "version": cfg["version"],
               "lamp": SY_UP[lamp], "lamp_raw": lamp, "lamp_scope": SY_SCOPE, "content_lamp": SY_UP[content], "content_raw": content,
               "at": sy_utc(at), "ts": sy_utc(at), "local": at.astimezone().strftime("%Y-%m-%d %H:%M"),
               "secs": round(_sy_time.time() - t0, 1), "actor": actor, "host": sy_host(), "lock": lock_note, "partial": partial, "steps": steps, "pages": pages,
               "peers": sy_peer_rows(base, cfg["peers"]), "links": sy_link_rows(base, cfg["links"]), "next": sy_next_line(steps, pages, partial),
               "summary": "步驟 %s · 頁 %s" % (" ".join("%s%s" % (SY_LN[s["lamp"]], s["id"]) for s in steps), " ".join("%s%s" % (SY_LN[p["lamp"]], p["id"]) for p in pages)),
               "paths": {"hub": str(out / cfg["hub"]), "receipt": str(out / SY_RECEIPT), "ledger": str(out / SY_LEDGER)}}
        css, tpl_note = sy_template_css(base)
        rec["template"] = tpl_note
        sy_write(out / cfg["hub"], sy_render(rec, out, css, tpl_note, cfg))
        sy_write(out / SY_RECEIPT, _sy_json.dumps(rec, ensure_ascii=False, indent=1))
        sy_append(out / SY_LEDGER, _sy_json.dumps({k: rec[k] for k in ("at", "system", "engine", "lamp", "content_lamp", "secs", "summary", "partial")} | {"host": rec["host"]["system"]}, ensure_ascii=False))
        sy_print_card(rec, cfg, True)
        if not no_open and not _sy_os.environ.get("VIA_NO_OPEN"):
            try:
                import webbrowser
                webbrowser.open((out / cfg["hub"]).resolve().as_uri())
            except Exception:
                print("[U/I] 開不起來,請手動開上面那一頁")
        return SY_RC[lamp]

    if cm is None:
        return body()
    try:
        with cm:
            return body()
    except TimeoutError:
        print("[%s] 黃 · 另一輪 synchronizer 正在跑(等了 %.0f 秒);這一輪沒有動任何東西" % (cfg["tag"], wait))
        return 2


def sy_check(cfg: dict, last_only: bool = False) -> int:
    """零寫入:讀上一輪收據;last_only 之外再重核一次頁對收據、連結頁,並重讀同儕的收據。"""
    out, base = _SyPath(cfg["out"]), _SyPath(cfg["base"])
    rec = sy_json(out / SY_RECEIPT)
    if rec is None:
        there = (out / SY_RECEIPT).is_file()
        print("[%s synchronizer] %s" % (cfg["system"], "紅 · 收據讀不懂:%s" % (out / SY_RECEIPT) if there else "灰 · 還沒有同步收據(先跑 %s synchronizer)" % cfg["cli"]))
        return 1 if there else 2
    if last_only:
        sy_print_card(rec, cfg, False)
        return SY_RC.get(rec.get("lamp_raw"), 2)
    now = _sy_dt.datetime.now(_sy_dt.timezone.utc)
    pages = [sy_pair_check(p, base, now=now, tail=cfg["engine"], version=cfg["version"]) for p in cfg["pages"]]
    extra = []
    hub = out / cfg["hub"]
    text = hub.read_text(encoding="utf-8", errors="replace") if hub.is_file() else ""
    if not text:
        extra.append(("r", "連結頁不在"))
    elif str(rec.get("at")) not in text or str(rec.get("engine")) not in text or ('<div class="verdict"><span class="lamp %s">' % rec.get("lamp_raw")) not in text:
        extra.append(("r", "連結頁與同步收據不是同一輪"))
    d = sy_when(rec.get("at"))
    if d is None or (now - d).total_seconds() > SY_STALE_H * 3600:
        extra.append(("y", "同步收據超過 %d 小時" % SY_STALE_H))
    lamp = sy_worst([s.get("lamp") for s in rec.get("steps") or []] + [p["lamp"] for p in pages] + [k for k, _ in extra] + (["y"] if rec.get("partial") else []))
    now_rec = dict(rec, pages=pages, lamp_raw=lamp, peers=sy_peer_rows(base, cfg["peers"], now),
                   next=sy_next_line(rec.get("steps") or [], pages, bool(rec.get("partial"))) if not extra else extra[0][1])
    print("[重核] 不跑步驟、不寫檔;步驟的燈取自上一輪收據,頁對收據與同儕收據是現在重讀的")
    sy_print_card(now_rec, cfg, False)
    for k, why in extra:
        print("  [%s] %s" % (SY_LN[k], why))
    return SY_RC[lamp]


def sy_manifest(cfg: dict) -> dict:
    cli = cfg["cli"]
    return {"name": "%s synchronizer(頁面 · 收據 · 連結頁 · 同儕自報)" % cfg["system"], "core": SY_CORE, "engine": cfg["engine"], "system": cfg["system"], "manager_family": cfg["family"],
            "verbs": {"synchronizer [run]": "排隊 → 依序跑自己的既有動詞 → 頁對收據 → 讀同儕收據 → 連結頁 → 收據", "synchronizer check": "零寫入:讀收據並重核",
                      "synchronizer --last": "零寫入:只印上一輪收據", "synchronizer manifest": "印這份說明"},
            "flags": {"--actor <名>": "轉給收 --actor 的步驟", "--steps a,b": "只跑部分步驟(這一輪最高黃)", "--wait <秒>": "排隊等多久,預設 5", "--no-open": "不開連結頁", "--out <夾>": "輸出夾"},
            "steps": [{"id": s["id"], "name": s["name"], "argv": s["argv"], "timeout": s["timeout"], "updates": s.get("out") or [], "saves": s.get("save")} for s in cfg["steps"]],
            "pages": [{"id": p["id"], "name": p["name"], "page": p["page"], "receipt": p.get("receipt"), "made_by": p.get("step") or p.get("by")} for p in cfg["pages"]],
            "peers": [{"system": p["system"], "reads": p["receipt"]} for p in cfg["peers"]], "links": [{"name": n, "path": r} for n, r in cfg["links"]],
            "does_not": cfg["does_not"], "outputs": {cfg["hub"]: "連結頁", SY_RECEIPT: "收據(同儕讀這一份)", SY_LEDGER: "只增帳", "SYNC_step_<步驟>.log": "每一步的原始輸出(只留最新)", SY_LOCK: "排隊鎖檔(不刪)"},
            "out_dir": str(_SyPath(cfg["out"])), "rc": {"0": "同步綠", "2": "黃 / 還沒有收據 / 另一輪在跑", "1": "紅", "3": "前版不在"}, "cli": cli,
            "receipt_fields": ["schema", "core", "system", "receipt", "engine", "version", "lamp", "lamp_raw", "lamp_scope", "content_lamp", "at", "ts", "secs", "host", "lock", "partial", "steps", "pages", "peers", "links", "next", "summary", "paths"],
            "lamp_scope": SY_SCOPE}


def sy_opt(args: list, flag: str):
    return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else None


def sy_command(cfg: dict, args: list) -> int:
    sub = args[0] if args and not args[0].startswith("-") else "run"
    rest = args[1:] if args and args[0] == sub else list(args)
    if sy_opt(rest, "--out"):
        cfg = dict(cfg, out=_SyPath(sy_opt(rest, "--out")))
    if sub == "manifest":
        print(_sy_json.dumps(sy_manifest(cfg), ensure_ascii=False, indent=1))
        return 0
    if sub == "check" or "--last" in rest:
        return sy_check(cfg, last_only="--last" in rest)
    if sub != "run":
        print("[%s] 黃 · synchronizer 沒有子動詞 %s;可用:run · check · --last · manifest" % (cfg["tag"], sub))
        return 2
    only = [x for x in (sy_opt(rest, "--steps") or "").split(",") if x] or None
    try:
        wait = float(sy_opt(rest, "--wait") or 5)
    except ValueError:
        wait = 5.0
    return sy_run(cfg, actor=sy_opt(rest, "--actor") or _sy_os.environ.get("VIA_ACTOR", ""), no_open="--no-open" in rest, only=only, wait=wait)


def sy_selftest(chk) -> None:
    """共用段自測:假系統 + 暫存夾 + 假步驟(零網路 · 不碰真樹 · 不起子行程)。chk(name, cond, note)。"""
    import contextlib
    import tempfile
    now = _sy_dt.datetime.now(_sy_dt.timezone.utc).replace(microsecond=0)

    def fixture(base, at, lamp="r", page_lamp=None, page_at=None, tester="X_Manager_v0002.py", part="GREEN"):
        o = _SyPath(base) / "rep"
        o.mkdir(parents=True, exist_ok=True)
        shown = (page_at or at).astimezone().strftime("%Y-%m-%d %H:%M")
        (o / "STATUS.json").write_text(_sy_json.dumps({"at": sy_utc(at), "lamp_raw": lamp, "engine": "X_ENG001_Status_v0104"}), encoding="utf-8")
        (o / "STATUS.html").write_text('<html><style>.a{}</style><header><div class="note">%s · X_ENG001_Status_v0104</div></header><div class="verdict"><span class="lamp %s">x</span></div></html>'
                                       % (shown, page_lamp or lamp), encoding="utf-8")
        (o / "PAGE.json").write_text(_sy_json.dumps({"started": sy_utc(at - _sy_dt.timedelta(seconds=300)), "at": sy_utc(at), "parts": {"health": "GREEN", "sdd": "YELLOW"}}), encoding="utf-8")
        (o / "PAGE.html").write_text("<html><p>%s +00:00</p><table><tr><td><b>●</b> health</td><td>%s</td></tr><tr><td>● sdd</td><td>YELLOW</td></tr></table></html>"
                                     % ((page_at or at - _sy_dt.timedelta(seconds=200)).astimezone(_sy_dt.timezone.utc).strftime("%Y-%m-%d %H:%M"), part), encoding="utf-8")
        (o / "TEST.json").write_text(_sy_json.dumps({"at": at.isoformat(), "lamp": "GREEN", "console": tester}), encoding="utf-8")
        (o / "TEST_v0101.html").write_text("<html>%s GREEN v0002</html>" % at.isoformat(), encoding="utf-8")
        (o / "FLOW_v0100.html").write_text("<html>GREEN X_Manager_v0115</html>", encoding="utf-8")

    P = [{"id": "status", "name": "現況", "page": "rep/STATUS.html", "receipt": "rep/STATUS.json", "step": "status", "time": "at", "lamp": "lamp_raw", "lamp_re": r'class="verdict"><span class="lamp (\w)"', "ver": "engine"},
         {"id": "page", "name": "矩陣", "page": "rep/PAGE.html", "receipt": "rep/PAGE.json", "step": "page", "time": "at", "time_start": "started", "parts": "parts"},
         {"id": "test", "name": "串測", "page": "rep/TEST_v*.html", "receipt": "rep/TEST.json", "step": None, "time": "at", "lamp": "lamp", "ver": "console", "tail_key": "console", "by": "test"},
         {"id": "flow", "name": "流程", "page": "rep/FLOW_v*.html", "receipt": None, "step": "page"}]
    S = [{"id": "books", "name": "冊", "argv": ["sync"], "timeout": 9, "ok": (0, 2), "state": lambda t: "" if '"pending": false' in t else "待同步"},
         {"id": "status", "name": "現況", "argv": ["status"], "timeout": 9, "ok": (0, 1, 2), "out": ["rep/STATUS.json", "rep/STATUS.html"]},
         {"id": "page", "name": "矩陣", "argv": ["page", "--json"], "timeout": 9, "ok": (0, 2), "json_lamp": True, "out": ["rep/PAGE.html"]}]
    quiet = contextlib.redirect_stdout(open(_sy_os.devnull, "w", encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="via_sync_core_") as td, quiet:
        root = _SyPath(td)
        a = root / "a"
        fixture(a, now)
        kw = {"tail": "X_Manager_v0002", "version": "v0002"}
        rows = {p["id"]: sy_pair_check(p, a, **kw) for p in P}
        b = root / "b"
        fixture(b, now, page_at=now - _sy_dt.timedelta(hours=37))    # 37 小時:任何時區解讀都對不上
        late = {p["id"]: sy_pair_check(p, b, **kw) for p in P[:2]}
        c = root / "c"
        fixture(c, now, lamp="r", page_lamp="g", part="RED")
        wrong = {p["id"]: sy_pair_check(p, c, **kw) for p in P[:2]}
        d = root / "d"
        fixture(d, now - _sy_dt.timedelta(hours=30), tester="X_Manager_v0001.py")
        old = sy_pair_check(P[2], d, **kw)
        (d / "rep" / "STATUS.html").unlink()
        (d / "rep" / "TEST_v0101.html").unlink()
        gone = (sy_pair_check(P[0], d, **kw)["lamp"], sy_pair_check(P[2], d, **kw)["lamp"])
        t0 = _sy_time.time()
        j1 = sy_judge_step(S[1], 1, "真紅 3", a, t0 - 60, 1.0)
        j2 = sy_judge_step(S[1], 1, "", a, t0 + 60, 1.0)
        j3 = sy_judge_step(S[1], 7, "", a, t0 - 60, 1.0)
        j4 = sy_judge_step(S[1], None, "", a, t0 - 60, 1.0)
        j5 = sy_judge_step(S[2], 2, '{"lamp": "YELLOW", "page": "x"}', a, t0 - 60, 1.0)
        k1 = sy_judge_step(S[0], 0, '{"pending": true}', a, t0, 1.0)
        k2 = sy_judge_step(S[0], 2, '{"pending": false}', a, t0, 1.0)
        e = root / "e"
        plan = {"books": '{"pending": true}', "status": 1, "page": 0}
        peers = [{"system": "PEER", "zh": "同儕", "receipt": "peer/SYNC_latest.json", "hub": "peer/HUB.html"}, {"system": "NONE", "receipt": "none/SYNC_latest.json", "hub": "none/HUB.html"}]
        (e / "peer").mkdir(parents=True)
        (e / "peer" / "SYNC_latest.json").write_text(_sy_json.dumps({"lamp_raw": "y", "content_raw": "r", "at": sy_utc(now), "engine": "P_Manager_v0009", "next": "對方的下一步", "host": {"system": "Windows", "counts_as_host_run": True}}), encoding="utf-8")
        (e / "peer" / "HUB.html").write_text("<html></html>", encoding="utf-8")
        peer_before = {p.name: (p.stat().st_mtime_ns, p.stat().st_size) for p in (e / "peer").iterdir()}
        cfg = {"system": "X", "tag": "X_Manager v0002", "engine": "X_Manager_v0002", "version": "v0002", "family": "X_Manager", "cli": "via-x", "base": e, "out": e / "rep", "hub": "X_UI_Hub_latest.html",
               "prior": None, "env": dict, "steps": S, "pages": P, "links": [("別頁", "rep/TEST_v*.html"), ("沒有的頁", "rep/NOPE.html")], "peers": peers, "does_not": ["寫他系統的樹"],
               "does_not_zh": "", "locker": lambda o, w: (None, "自測不排隊")}

        def fake(cf, step, actor=""):
            t = _sy_time.time()
            fixture(cf["base"], _sy_dt.datetime.now(_sy_dt.timezone.utc).replace(microsecond=0))
            v = plan[step["id"]]
            return sy_judge_step(step, v if isinstance(v, int) else 0, v if isinstance(v, str) else "", cf["base"], t, 0.1)

        rc1 = sy_run(cfg, runner=fake, no_open=True)
        rec = sy_json(e / "rep" / SY_RECEIPT) or {}
        hub = (e / "rep" / cfg["hub"]).read_text(encoding="utf-8") if (e / "rep" / cfg["hub"]).is_file() else ""
        plan["books"] = '{"pending": false}'
        rc2 = sy_run(cfg, runner=fake, no_open=True)
        rec2 = sy_json(e / "rep" / SY_RECEIPT) or {}
        n_led = len((e / "rep" / SY_LEDGER).read_text(encoding="utf-8").splitlines())
        before = {p.name: (p.stat().st_mtime_ns, p.stat().st_size) for p in (e / "rep").iterdir()}
        rc3, rc4 = sy_check(cfg), sy_check(cfg, last_only=True)
        after = {p.name: (p.stat().st_mtime_ns, p.stat().st_size) for p in (e / "rep").iterdir()}
        peer_after = {p.name: (p.stat().st_mtime_ns, p.stat().st_size) for p in (e / "peer").iterdir()}
        (e / "rep" / "STATUS.html").write_text("<html><header>1999-01-01 00:00</header></html>", encoding="utf-8")
        rc5 = sy_check(cfg)
        rc6 = sy_check(dict(cfg, out=root / "none"))
        rc7 = sy_run(cfg, runner=fake, no_open=True, only=["status"])
        rc8 = sy_run(cfg, runner=fake, no_open=True, only=["nope"])

        class Busy:
            def __enter__(self):
                raise TimeoutError("busy")

            def __exit__(self, *x):
                return False

        ran_busy = []
        rc9 = sy_run(cfg, runner=lambda cf, s, a="": ran_busy.append(s["id"]) or fake(cf, s), locker=lambda o, w: (Busy(), "忙"), no_open=True)
        man = sy_manifest(cfg)
        m1, m2 = sy_command(cfg, ["--last", "--out", str(root / "none")]), sy_command(cfg, ["bogus"])
        tz = (sy_whens("2026-11-18T08:27:40Z"), sy_whens("2026-11-18 09:07 +00:00"), sy_whens("2026-11-18 16:27"), sy_whens("沒有時間"))
    chk("核① 頁與收據同一輪(時間 · 燈 · 分項 · 版本都對)→ 綠;沒有收據的頁沒寫產生時間 → 黃", rows["status"]["lamp"] == "g" and rows["page"]["lamp"] == "g" and rows["test"]["lamp"] == "g" and rows["flow"]["lamp"] == "y",
        {k: (v["lamp"], v["note"]) for k, v in rows.items()})
    chk("核② 頁上的時間對不上收據 → 紅(只寫到分的時間、帶時區的時間、起訖區間都認得)", late["status"]["lamp"] == "r" and late["page"]["lamp"] == "r", late)
    chk("核③ 頁上的燈或分項的燈不是收據的 → 紅", wrong["status"]["lamp"] == "r" and wrong["page"]["lamp"] == "r" and "health" in wrong["page"]["note"], wrong)
    chk("核④ 不是本動詞產的頁:收據超過 24 小時、或是前一版入口跑的 → 黃;自己該產的頁不在 → 紅;別人的頁沒跑過 → 灰", old["lamp"] == "y" and "小時" in old["note"] and "重跑 test" in old["note"] and gone == ("r", "x"), (old, gone))
    chk("核⑤ 步驟兩盞燈分開:跑完且有更新 = 同步綠、內容照 rc 或它印的 lamp;沒更新 / rc 不認得 / 逾時 = 同步紅",
        (j1["lamp"], j1["content"]) == ("g", "r") and j2["lamp"] == "r" and j3["lamp"] == "r" and j4["lamp"] == "r" and (j5["lamp"], j5["content"]) == ("g", "y"), (j1, j2["note"], j3["note"], j4["note"], j5))
    chk("核⑥ 冊的步驟看它印的內容,不只看 rc:內容說待同步 → 黃(rc 0 也一樣);內容說好 → 綠(rc 2 也一樣)", k1["lamp"] == "y" and k1["content"] is None and k2["lamp"] == "g", (k1, k2))
    chk("核⑦ 整輪:收據 · 連結頁 · 只增帳都寫出;冊黃 → rc 2;內容紅不染同步燈", rc1 == 2 and rec.get("lamp_raw") == "y" and rec.get("content_raw") == "r" and len(rec.get("pages") or []) == 4, (rc1, rec.get("summary")))
    chk("核⑧ 連結頁帶收據時間 · 入口版本 · 同一盞燈;連結都是相對路徑;不在的頁不給連結", bool(hub) and str(rec.get("at")) in hub and "X_Manager_v0002" in hub and '<div class="verdict"><span class="lamp y">' in hub
        and 'href="STATUS.html"' in hub and 'href="../peer/HUB.html"' in hub and "file:///" not in hub and "NOPE.html" not in hub)
    chk("核⑨ 同儕:讀得到對方自報的燈 · 時間 · 下一步;對方沒有收據照實灰;對方的黃不算進自己的同步燈;對方的夾一個位元都沒動",
        [(k["system"], k["lamp"]) for k in rec.get("peers") or []] == [("PEER", "y"), ("NONE", "x")] and "對方的下一步" in hub and peer_before == peer_after and rec2.get("lamp_raw") == "y" and "流程" in str(rec2.get("next")),
        (rec.get("peers"), rec2.get("next")))
    chk("核⑩ 冊轉綠後只剩沒寫產生時間的頁 → 仍是黃(rc 2),不放水;只增帳 2 行", rc2 == 2 and n_led == 2, (rc2, n_led))
    chk("核⑪ check / --last 零寫入(夾內每個檔的時間與大小不變),rc 照燈;事後被換掉的頁抓得到(紅);沒有收據 → rc 2", before == after and rc3 == 2 and rc4 == 2 and rc5 == 1 and rc6 == 2 and m1 == 2, (rc3, rc4, rc5, rc6, m1))
    chk("核⑫ --steps 只跑部分 → 最高黃;不認得的步驟名或子動詞 → rc 2 不跑;另一輪在跑 → rc 2 一步都沒跑", rc7 == 2 and rc8 == 2 and m2 == 2 and rc9 == 2 and ran_busy == [], (rc7, rc8, m2, rc9, ran_busy))
    chk("核⑬ manifest 列出步驟 · 頁 · 同儕 · 不做清單 · 收據欄位", len(man["steps"]) == 3 and len(man["pages"]) == 4 and len(man["peers"]) == 2 and "lamp" in man["receipt_fields"] and man["does_not"])
    chk("核⑭ 時間字樣:Z / 帶位移各一種解讀;沒寫時區三種都試;不是時間回空", len(tz[0]) == 1 and len(tz[1]) == 1 and len(tz[2]) == 3 and tz[3] == [] and tz[0][0].utcoffset().total_seconds() == 0)
# ===== [VIA:SYNC-CORE:END] =====


RC_LAMP = {0: "g", 2: "y", 1: "r", 3: "y", 4: "y"}   # 本管理器的 rc:0 綠 · 1 紅 · 2 黃 · 3 缺件 · 4 等同意閘


def books_state(text: str) -> str:
    """sync --json 自己怎麼說(不只看 rc):自己的冊有漂移 / 尾版沒編號 / 上次之後有變 → 回原因;都好回空字串;讀不到也算原因。"""
    d = sy_step_json(text)
    if d is None:
        return "讀不到 sync 的結果"
    why = []
    if d.get("own_drift"):
        why.append("自己的冊與正本有漂移:" + "、".join(map(str, d["own_drift"])))
    if d.get("unnumbered"):
        why.append("尾版沒編號 %s" % d["unnumbered"])
    if d.get("changed"):
        why.append("上次之後有變 %s" % d["changed"])
    if not why and str(d.get("lamp")) != "GREEN":
        why.append("sync 的燈是 %s" % d.get("lamp"))
    return " · ".join(why)


# 依序跑的既有動詞(都以子行程叫前版 = 本管理器自己的動詞;ok = 算跑完的 rc;out = 這一步該更新的檔;save = 把它印的 JSON 存成這張頁的收據)
STEPS = [
    {"id": "books", "name": "自己的冊(SSOT 副本 · 編號;乾跑)", "argv": ["sync", "--json"], "timeout": 900, "ok": (0, 1, 2, 3, 4), "state": books_state, "state_zh": "自己的冊有漂移"},
    {"id": "health", "name": "管理器自檢", "argv": ["health"], "timeout": 900, "ok": (0, 1, 2, 3, 4), "rc_lamp": RC_LAMP},
    {"id": "page", "name": "管理器矩陣頁", "argv": ["page", "--json"], "timeout": 900, "ok": (0, 1, 2, 3, 4), "rc_lamp": RC_LAMP, "json_lamp": True, "save": REP + "VDF_PAGE_latest.json", "out": [REP + "VDF_MANAGER_MATRIX_latest.html"]},
    {"id": "peers", "name": "同儕只讀監控", "argv": ["peers"], "timeout": 900, "ok": (0, 1, 2, 3, 4), "rc_lamp": RC_LAMP},
]
# 頁對收據
PAGES = [
    {"id": "matrix", "name": "管理器矩陣頁", "page": REP + "VDF_MANAGER_MATRIX_latest.html", "receipt": REP + "VDF_PAGE_latest.json", "step": "page", "time": "at", "time_start": "started", "parts": "parts"},
    {"id": "engines", "name": "引擎矩陣", "page": "VIA_Reports/vdf/engine_matrix/VDF_EngineMatrix_latest.html", "receipt": "VIA_Reports/vdf/engine_matrix/VDF_EngineMatrix_latest.json", "step": "page", "time": "summary.updated_at", "lamp": "summary.lamp", "ver": "summary.manager"},
]
# 只連結、不納入本輪同步的頁與檔(在就連,不在就照實灰)
LINKS = [
    ("VDF 工作台頁", "VIA_Reports/workbench/VIA_Workbench_VDF_latest.html"),
    ("VDF 擷取矩陣", "VIA_Reports/vdf/FETCH_MATRIX_latest.html"),
    ("資料庫狀態矩陣", "VIA_Reports/vdf/DB_STATUS_MATRIX_latest.html"),
    ("VDF 管理範圍", "VIA_Reports/vdf/VDF_SCOPE_latest.html"),
    ("Parquet 湖狀態", "VIA_Reports/vdf_lake/LAKE_STATUS_latest.json"),
    ("健康總檢收據", "VIA_Reports/vdf/HEALTH_latest.json"),
    ("啟動收據", "VIA_Reports/vdf/activate/VDF_ACTIVATE_latest.json"),
    ("自建工作台(五系統)", "VIA_Reports/workbench/VIA_Workbench_Hub_latest.html"),
    ("VDF + VRN 一鍵總覽", "VIA_Reports/oneshot/VDF_VRN_ONESHOT_latest.html"),
]
# 同儕自報的同步收據(只讀:不執行、不 import、不寫對方的夾)
PEERS = [
    {"system": "VCGC", "zh": "中央治理主控台", "receipt": "VIA_Reports/vcgc/SYNC_latest.json", "hub": "VIA_Reports/vcgc/VCGC_UI_Hub_latest.html"},
    {"system": "VRN-2", "zh": "券商報告", "receipt": "VIA_Reports/vrn2/manager/SYNC_latest.json", "hub": "VIA_Reports/vrn2/manager/VRN_UI_Hub_latest.html"},
]
DOES_NOT = ["sync --apply(寫冊)", "launch --run(真的啟動擷取 / 管線)", "編號", "git commit / push", "執行或改寫他系統(只讀對方自報的收據)"]


def child_env() -> dict:
    """同步步驟的子行程環境:照前版的 sm_child_env(只補本系統自己的入口旗標),另加不逐頁跳出與 UTF-8 輸出。"""
    base = PRIOR.sm_child_env() if callable(getattr(PRIOR, "sm_child_env", None)) else dict(os.environ)
    return dict(base, VIA_NO_OPEN="1", PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")


def manager_lock(out, wait: float):
    """排隊鎖:用本管理器自己的作業系統檔案鎖(前版鏈的 em_locked)。回 (context manager 或 None, 說明)。"""
    fn = getattr(PRIOR, "em_locked", None)
    if not callable(fn):
        return None, "沒排隊(本管理器的前版鏈沒有 em_locked)"
    try:
        return fn(Path(out) / SY_LOCK, wait=wait), "%s 自己的作業系統檔案鎖" % FAMILY
    except Exception as e:                               # 鎖拿不到照實記,不擋同步
        return None, "沒排隊(鎖用不了:%s)" % type(e).__name__


def config() -> dict:
    return {"system": SYSTEM, "zh": "資料擷取", "tag": FAMILY + " " + TAG, "engine": Path(__file__).stem, "version": TAG, "family": FAMILY, "cli": "via-vdf",
            "base": VIA_ROOT, "out": VIA_ROOT / REP, "hub": "VDF_UI_Hub_latest.html", "prior": PRIOR_PATH, "env": child_env,
            "steps": STEPS, "pages": PAGES, "links": LINKS, "peers": PEERS, "does_not": DOES_NOT,
            "does_not_zh": "不寫冊、不啟動擷取或管線;冊有漂移只亮黃,寫冊要操作員批准。", "locker": manager_lock}


def collect() -> dict:
    """VCGC 子系統對接口(照前版 · 只讀)· served_by 記本版。前版鏈沒有這個接口就照實回 ABSENT(不讓呼叫端炸)。"""
    try:
        out = PRIOR.collect()
    except AttributeError as e:
        return {"state": "ABSENT", "why": "前版鏈沒有 collect 接口(%s)" % str(e)[:90], "served_by": {"tail": FAMILY + "_" + TAG}}
    if isinstance(out, dict):
        out = dict(out)
        sb = dict(out.get("served_by") or {})
        sb["tail"] = FAMILY + "_" + TAG
        out["served_by"] = sb
    return out


def help_extra() -> None:
    print("  ── %s synchronizer(%s 自己的頁面與收據;VCGC 與另一個系統各自有同名動詞,互相只讀對方的收據)──" % (TAG, SYSTEM))
    print("  synchronizer [--steps %s] [--no-open]   依序跑自己的既有動詞 → 頁對收據 → 同儕自報 → 連結頁 VDF_UI_Hub_latest.html(rc 綠 0 · 黃 2 · 紅 1)" % ",".join(s["id"] for s in STEPS))
    print("  synchronizer check | synchronizer --last | synchronizer manifest   零寫入重核 | 只讀上一輪收據 | 整合說明")


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("=== %s %s 自測(薄尾 · synchronizer 一個動詞 + 其餘照前版;夾具 · 零網路 · 不碰真樹)===" % (DISPLAY_NAME, TAG), flush=True)
    chk("① 前版在且是本家族上一版", _vnum(PRIOR_PATH) == _vnum(__file__) - 1 and callable(getattr(PRIOR, "main", None)), PRIOR_PATH.name)
    sy_selftest(chk)
    cfg = config()
    ids, sids = [p["id"] for p in cfg["pages"]], [s["id"] for s in cfg["steps"]]
    own = ("VIA_Reports/vdf", "VIA_Reports/vdf")
    chk("② 設定:步驟與頁的名稱不重複 · 每張頁指到的步驟都在 · 自己寫的檔都在自己的 VIA_Reports 夾 · 同儕只列別的系統、只讀",
        len(set(ids)) == len(ids) and len(set(sids)) == len(sids) and all(p.get("step") in sids + [None] for p in cfg["pages"])
        and all(o.startswith(own) for s in cfg["steps"] for o in (s.get("out") or []) + ([s["save"]] if s.get("save") else [])) and REP.startswith(own)
        and all(p["system"] != SYSTEM and not p["receipt"].startswith(own) for p in cfg["peers"]))
    chk("③ 步驟只用唯讀動詞:沒有 --apply · 沒有 --run", not any(a in ("--apply", "--run") for s in cfg["steps"] for a in s["argv"]))
    chk("④ books 看 sync 自己印的內容:有漂移 → 有原因;全好 → 空;讀不到 → 有原因",
        "sdd" in books_state('{"lamp": "YELLOW", "own_drift": ["sdd"], "unnumbered": 0, "changed": 0}') and books_state('{"lamp": "GREEN", "own_drift": [], "unnumbered": 0, "changed": 0}') == "" and books_state("x") != "")
    css, tnote = sy_template_css(VIA_ROOT)
    chk("⑤ 連結頁樣式取自鎖定模板(讀冊;雜湊對得上;本檔沒有自訂色碼)", bool(css) and ".lamp" in css and not re.search(r"#[0-9a-fA-F]{6}\b", repr(sy_render.__code__.co_consts)), tnote)
    with tempfile.TemporaryDirectory(prefix="via_vdf_sync_") as td:
        cm, note = manager_lock(Path(td), 1.0)
        got = cm is None
        if cm is not None:
            with cm:
                got = (Path(td) / SY_LOCK).is_file()
    chk("⑥ 排隊鎖:本管理器自己的檔案鎖拿得到(前版鏈沒有就照實說沒排隊)", got, note)
    env = child_env()
    peer_flags = [k for k in ("VIA_FROM_VCGC", "VIA_FROM_VDFSM", "VIA_FROM_VRN", "VIA_VCGC_PUSH") if k in env and k not in os.environ and k != (getattr(PRIOR, "SM_CONFIG", None) or {}).get("own_entry_flag")]
    chk("⑦ 子行程環境:VIA_NO_OPEN=1 · 不多設任何他系統的旗標", env.get("VIA_NO_OPEN") == "1" and not peer_flags, peer_flags)
    seen = []
    real = PRIOR.main
    PRIOR.main = lambda a=None: seen.append(list(a or [])) or 0
    try:
        m1 = main(["health"])
        m2 = main(["engine-matrix", "--json"])
        with open(os.devnull, "w", encoding="utf-8") as nul:
            keep, sys.stdout = sys.stdout, nul
            try:
                m3 = main(["synchronizer", "manifest"])
                m4 = main(["synchronizer", "--last", "--out", str(Path(tempfile.gettempdir()) / "via_sync_none_vdf")])
            finally:
                sys.stdout = keep
    finally:
        PRIOR.main = real
    chk("⑧ 只有 synchronizer 留在本版;其餘動詞原樣交給前版(參數不變)", seen == [["health"], ["engine-matrix", "--json"]] and m1 == 0 and m2 == 0 and m3 == 0 and m4 == 2, (seen, m3, m4))
    c = collect()
    chk("⑨ 前版公開名稱都在(TAILAPI)· collect 記本版(前版鏈沒有這個接口就照實回 ABSENT,不炸)· 入口契約照前版", all(callable(getattr(sys.modules[__name__], n, None)) for n in ("collect", "main", "selftest")) and callable(PRIOR.main)
        and isinstance(c, dict) and (c.get("served_by") or {}).get("tail") == FAMILY + "_" + TAG and (not callable(getattr(PRIOR, "entry_contract_ok", None)) or PRIOR.entry_contract_ok()))
    src = Path(__file__).read_text(encoding="utf-8")
    live = src.split("def sy_selftest")[0] + src.split("# ===== [VIA:SYNC-CORE:END] =====")[1].split("def selftest")[0]
    chk("⑩ 兩個標準橋在 · 零網路 · 不用 TA-Lib · 不 import 他系統 · 不寫同意閘 · 寫檔只經 sy_write / sy_append",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src
        and not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib|socket|CGC_|VRN_|VIA_AgentOS)", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src) and live.count(".write_text(") == 1 and live.count('open(p, "a"') == 1)
    print("  ── 前版 %s 自測 ──" % PRIOR_PATH.name, flush=True)
    rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 3
    chk("⑪ 前版 %s 自測照過" % PRIOR_PATH.name, rc == 0, "rc %s" % rc)
    n = sum(ok)
    print("[%s] %s %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", DISPLAY_NAME, TAG, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"] or "--selftest" in args[:1]:
        return selftest()
    if args[:1] == ["synchronizer"]:
        return sy_command(config(), args[1:])
    rc = PRIOR.main(args)
    if not args or args[:1] == ["help"]:
        help_extra()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
