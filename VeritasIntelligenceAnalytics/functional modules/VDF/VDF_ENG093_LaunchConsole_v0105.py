#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== VDF_ENG093_LaunchConsole_v0105(2026-10-13)=====
# 薄尾:問參數頁的矩陣把清單先行的兩步(tw_list = VDF_MDL009 台股個股清單自動更新 · etf_list = VDF_MDL010 主動式台股 ETF 清單自動更新)
# 放在最前面、鎖定必跑(勾不掉、不經 -Steps:CGC_MDL134 v0102 在並行道自動先跑),逐一引擎自測也能測它們。
#
# 操作員令(2026-10-13):「要先確令台股個股清單生成引擎自動更新以及主動式台股ETF清單自動更新生成引擎正常作業  輸出作為其他引擎的輸入  VDF 一鍵啟動」。
# 根因:矩陣只列啟動器 $stepBook 的 11 步(Invoke-VIA-VdfFetch v0107),清單兩步不在那一行;v0103 的 validate 只收 $stepBook 的步,
#   所以頁上不能把它們送進 -Steps。本版:steps_matrix() 把兩步放最前(步冊 CGC_MDL125 v0112 起才有;冊上沒有就不列);
#   _matrix_rows() 把它們畫成鎖定列(checked · disabled · class lock,JS 的 boxes() 只數 .stp,「已勾 n/m」與 -Steps 不含它們);
#   decision / validate / 啟動器 / 其餘動詞全照 v0104。
# [接回 main · VDF 自足 2026-10-20 · 四系統對等獨立 L123] 工作站版要 VCGC 的步冊 CGC_MDL125 v0112(有清單兩步)與並行道 CGC_MDL134 v0102
#   (自動先跑清單);main 的 VCGC 還在 v0111 / v0101,本線不改他系統的檔。本線改法(VDF 自己做到「清單先行」):
#   ① VCGC 步冊有清單兩步 → 照工作站版(列 VCGC 的列,VCGC 並行道先跑)。
#   ② VCGC 步冊沒有 → 清單兩列改由 VDF 自己的擷取冊(VDF_FetchSystem_SSOT 尾版的 009 · 010)列出,同樣鎖定在最前;
#      你在頁上按「啟動」後、啟動器起跑之前,ask 先用 VDF 族群引擎的清單先行(VDF_MDL012_FetchGroups 尾版 run_parallel)跑 009 → 010:
#      全綠才放行;紅 → 決定檔改 lists_failed(rc 5)、雙閘沒開 → lists_gated(rc 4),開啟器照決定不是 launch 就不啟動;只看計畫(dry)不跑。
#   清單兩步仍不送 -Steps(validate 照舊);同意閘不讀寫以外不碰(只看在不在)。
# [U/I 實測 2026-10-20] 手機寬(390)問參數頁橫向溢出到 660:資料庫卡上的目錄路徑 <code> 一長串不斷行(v0104 起就有)。
#   本版在問參數頁與資料庫狀況頁頭加一行 code{overflow-wrap:anywhere}(只加樣式,不改內容)。
"""VDF_ENG093_LaunchConsole — VDF 一鍵啟動台(問參數頁 + 資料庫狀況頁)
本版 v0105 薄尾見上方檔頭;用法見 USAGE(python VDF_ENG093_LaunchConsole_v0105.py help)。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
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
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG093_LaunchConsole"
TAG = "v0105"
LIST_STEPS_V0105 = ("tw_list", "etf_list")
LOCK_NOTE_V0105 = "清單先行 · 必跑(CGC_MDL134 v0102 在並行道自動先跑,不經 -Steps;每次啟動都更新清單)"
LOCK_NOTE_VDF_V0105 = "清單先行 · 必跑(VDF 自己先跑:按「啟動」後、啟動器起跑前先跑這兩支,紅就不啟動;不經 -Steps;每次啟動都更新清單)"
LIST_ENGINES_V0105 = {"tw_list": ("009", "台股個股清單自動更新(VDF_MDL009)"), "etf_list": ("010", "主動式台股 ETF 清單自動更新(VDF_MDL010)")}
ASK_CEIL_V0105 = 1250                         # 開啟器給 ask 的天花板 1320s,留 70s 收尾:清單跑在剩下的時間裡


def _vnum_v0105(p) -> int:
    import re
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0105(p) < _vnum_v0105(__file__)), key=_vnum_v0105)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + TAG, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner_v0105(name: str):
    import types
    m = PRIOR
    while isinstance(m, types.ModuleType):
        if name in vars(m):
            return m
        m = getattr(m, "PRIOR", None)
    return None


_OWN = _owner_v0105("steps_matrix")          # v0103 本體(問參數頁 · 矩陣 · 動詞)
_ORIG_MATRIX, _ORIG_ROWS, _ORIG_VERSION = _OWN.steps_matrix, _OWN._matrix_rows, _OWN.VERSION
_ORIG_ASK = _OWN.cmd_ask
_ORIG_RENDER_ASK, _ORIG_RENDER_STATUS = _OWN.render_ask, _OWN.render_status
NARROW_CSS_V0105 = "<style id='via-v0105-narrow'>code{overflow-wrap:anywhere}</style>"


def _narrow_v0105(page: str) -> str:
    """長路徑 <code> 在窄螢幕斷行(手機不橫向溢出);已有就不重加。"""
    if "via-v0105-narrow" in page:
        return page
    i = page.find("</head>")
    return page[:i] + NARROW_CSS_V0105 + page[i:] if i >= 0 else NARROW_CSS_V0105 + page


def render_ask(ctx: dict, token: str) -> str:
    return _narrow_v0105(_ORIG_RENDER_ASK(ctx, token))


def render_status(*a, **k) -> str:
    return _narrow_v0105(_ORIG_RENDER_STATUS(*a, **k))


def _fg_v0105():
    """VDF 族群擷取尾版(VDF_MDL012_FetchGroups_v*.py;清單先行 run_parallel 在它的鏈上)。載不到回 None。"""
    hits = [p for p in HERE.glob("VDF_MDL012_FetchGroups_v*.py") if _vnum_v0105(p) >= 0]
    if not hits:
        return None
    p = max(hits, key=_vnum_v0105)
    name = "vdf_eng093_fg_for_" + TAG + "_" + p.stem[-5:]
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, p)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


def vdf_list_rows(fg=None) -> list:
    """清單兩列(VDF 自己的擷取冊 009 · 010):矩陣列的欄位同 v0103(id · zh · 引擎 · 參數 · 觸網 · 鏈);冊上沒有就不列。"""
    fg = fg or _fg_v0105()
    if fg is None:
        return []
    fb_p = fg.V0100.tail(fg.V0100.FETCH_GLOB)
    fb = json.loads(fb_p.read_text(encoding="utf-8")) if fb_p else {}
    by = {e.get("id"): e for e in fb.get("engines") or []}
    rows = []
    for sid in LIST_STEPS_V0105:
        eid, zh = LIST_ENGINES_V0105[sid]
        e = by.get(eid)
        if not e:
            continue
        ep = HERE / str(e.get("file") or "")
        body = ep.read_text(encoding="utf-8", errors="replace") if ep.is_file() else ""
        rows.append({"id": sid, "zh": zh, "why": str(e.get("role") or ""), "net": True, "to": e.get("timeout_s"),
                     "engine": ep.name, "engine_path": str(ep), "engine_ok": ep.is_file(),
                     "args": [{"t": str(x), "k": ""} for x in (e.get("run_args") or [])], "chain": "lists", "after": [],
                     "accel": "[VIA:ACCEL-BRIDGE" in body, "netbridge": "[VIA:NET-BRIDGE" in body, "missing": False, "by": "VDF"})
    return rows


def lists_owner(since: str) -> str:
    """誰負責清單先行:VCGC 步冊有清單兩步 → "VCGC";沒有 → "VDF"(本版自己跑)。"""
    try:
        mx = _ORIG_MATRIX(since, list(LIST_STEPS_V0105))
    except Exception:
        return "VDF"
    have = {r.get("id") for r in mx.get("rows") or [] if not r.get("missing")}
    return "VCGC" if all(x in have for x in LIST_STEPS_V0105) else "VDF"


def steps_matrix(since: str, steps: list | None) -> dict:
    """前版矩陣;清單兩步放最前(啟動器步清單沒列也放;步冊沒有就不列,照實)。"""
    want = None
    if steps:
        want = [x for x in LIST_STEPS_V0105 if x not in steps] + list(steps)
    mx = _ORIG_MATRIX(since, want)
    rows, vdf = [], None
    for r in mx.get("rows") or []:
        if r.get("id") in LIST_STEPS_V0105:
            if r.get("missing"):                 # VCGC 步冊沒有清單步 → VDF 自己的擷取冊列(VDF 自己先跑)
                if vdf is None:
                    vdf = {x["id"]: x for x in vdf_list_rows()}
                r = vdf.get(r["id"])
                if r is None:
                    continue                     # VDF 冊也沒有 → 不列、不假裝
                r = dict(r, lock=True, why=((r.get("why") or "") + " · " + LOCK_NOTE_VDF_V0105).strip(" ·"))
            else:
                r = dict(r, lock=True, why=((r.get("why") or "") + " · " + LOCK_NOTE_V0105).strip(" ·"))
        rows.append(r)
    mx["rows"] = rows
    mx["lists_by"] = "VDF" if vdf is not None else "VCGC"
    return mx


def _matrix_rows(mx: dict, allowed: list) -> str:
    """前版畫列(清單步算 allowed 才有自測鈕與勾);再把清單列改成鎖定列(checked · disabled · class lock)。"""
    html = _ORIG_ROWS(mx, list(allowed) + [x for x in LIST_STEPS_V0105 if x not in allowed])
    note = LOCK_NOTE_VDF_V0105 if (mx.get("lists_by") == "VDF") else LOCK_NOTE_V0105
    for sid in LIST_STEPS_V0105:
        html = html.replace(f"<input type='checkbox' class='stp' value='{sid}' checked>",
                            f"<input type='checkbox' class='lock' value='{sid}' checked disabled title='{note}'>")
    return html


def run_lists(dec: dict, budget_s: float, fg=None) -> dict:
    """VDF 自己的清單先行:009 → 010(VDF_MDL012_FetchGroups 尾版 run_parallel,只放清單、不放擷取道;紅就停)。
    回 {by, state(OK · FAIL · GATED · SKIP_DRY · NO_TIME · ABSENT), rows, why}。只看計畫(dry)不跑;雙閘沒開不跑(同意閘不代設)。"""
    if dec.get("dry"):
        return {"by": "VDF", "state": "SKIP_DRY", "rows": [], "why": "只看計畫:清單不跑"}
    fg = fg or _fg_v0105()
    if fg is None:
        return {"by": "VDF", "state": "ABSENT", "rows": [], "why": "VDF_MDL012_FetchGroups_v*.py 不在,清單先行跑不了"}
    V = fg.V0100
    if not V.gates_open():
        return {"by": "VDF", "state": "GATED", "rows": [],
                "why": "雙閘沒開 —— 清單引擎要連網,零子行程;要擷取請操作員自己在本視窗開雙閘 VIA_NET_CONSENT · VIA_SCRAPE_CONSENT(操作員的手,本檔永不代設)"}
    if budget_s < 120:
        return {"by": "VDF", "state": "NO_TIME", "rows": [], "why": "問參數頁等太久,剩 %ds 不夠跑清單(再開一次)" % budget_s}
    fb_p = V.tail(V.FETCH_GLOB)
    fb = json.loads(fb_p.read_text(encoding="utf-8")) if fb_p else {}
    by = {e.get("id"): e for e in fb.get("engines") or []}
    lists = [dict(by[LIST_ENGINES_V0105[s][0]], run_args=list(by[LIST_ENGINES_V0105[s][0]].get("run_args") or []), timeout_s=0, needs=[])
             for s in LIST_STEPS_V0105 if LIST_ENGINES_V0105[s][0] in by]
    mp = V.tail(V.MDL008_GLOB)
    if not lists or mp is None:
        return {"by": "VDF", "state": "ABSENT", "rows": [], "why": "擷取冊沒有 009 / 010 或 MDL008 不在"}
    home = V.default_home(fb)
    tp = fg.temp_plan()
    per = max(60, int(budget_s // max(1, len(lists))))
    out = fg.run_parallel({"lists": lists, "lanes": []}, mp, "live", home, home.parent / "_logs", per, 1, None, lambda rows: rows, tp, True)
    rows = [{"id": x.get("id"), "rc": x.get("rc"), "sec": x.get("sec"), "log": x.get("log")} for x in out.get("lists") or []]
    bad = [r["id"] for r in rows if r["rc"] not in (0, None)]
    if bad or len(rows) < len(lists):
        return {"by": "VDF", "state": "FAIL", "rows": rows, "why": "清單引擎紅 %s → 不啟動(清單是全部引擎的前提)" % (bad or "沒跑完")}
    return {"by": "VDF", "state": "OK", "rows": rows, "why": ""}


_LISTS_RC_V0105 = {"OK": 0, "SKIP_DRY": 0, "VCGC": 0, "FAIL": 5, "ABSENT": 5, "NO_TIME": 5, "GATED": 4}
_LISTS_ACT_V0105 = {"FAIL": "lists_failed", "ABSENT": "lists_failed", "NO_TIME": "lists_failed", "GATED": "lists_gated"}


def cmd_ask(a: list) -> int:
    """前版 ask(頁 · 決定檔)照舊;決定是 launch 而且清單歸 VDF 管 → 啟動器起跑前先跑清單,結果寫回決定檔(紅就把 action 改掉,開啟器就不啟動)。"""
    t0 = time.time()
    rc = _ORIG_ASK(a)
    out = Path(_OWN._arg(a, "--out") or (_OWN.OUT_DIR / "ASK_DECISION_latest.json"))
    if rc != 0 or not out.is_file():
        return rc
    try:
        dec = json.loads(out.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return rc
    if dec.get("action") != "launch":
        return rc
    owner = lists_owner(str(dec.get("since") or ""))
    if owner == "VCGC":
        r = {"by": "VCGC", "state": "VCGC", "rows": [], "why": "VCGC 步冊有清單兩步,由 VCGC 並行道先跑"}
    else:
        print("  [VDF 啟動台] 清單先行(VDF 自己跑):009 台股個股清單 → 010 主動式台股 ETF 清單 · 啟動器起跑前 …", flush=True)
        r = run_lists(dec, ASK_CEIL_V0105 - (time.time() - t0))
    dec["lists"] = r
    if r["state"] in _LISTS_ACT_V0105:
        dec["action"] = _LISTS_ACT_V0105[r["state"]]
        dec["why"] = r["why"]
    _OWN._write_json(out, dec)
    tag = {"OK": "全綠 → 放行啟動器", "SKIP_DRY": "只看計畫,沒跑", "VCGC": "交 VCGC 並行道"}.get(r["state"], "→ 不啟動")
    print("  [VDF 啟動台] 清單先行 %s · %s%s%s" % (r["state"], tag, (" · " + " · ".join("%s rc %s" % (x["id"], x["rc"]) for x in r["rows"])) if r["rows"] else "",
                                            (" · " + r["why"]) if r["why"] else ""), flush=True)
    return _LISTS_RC_V0105.get(r["state"], 1)


def _patch_v0105(on: bool) -> None:
    _OWN.steps_matrix = steps_matrix if on else _ORIG_MATRIX
    _OWN._matrix_rows = _matrix_rows if on else _ORIG_ROWS
    _OWN.cmd_ask = cmd_ask if on else _ORIG_ASK
    _OWN.render_ask = render_ask if on else _ORIG_RENDER_ASK
    _OWN.render_status = render_status if on else _ORIG_RENDER_STATUS
    _OWN.VERSION = TAG[1:] if on else _ORIG_VERSION


_patch_v0105(True)


def main() -> int:
    if "--selftest" in sys.argv[1:] or "--self-test" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · %s" % (note,)) if note != "" else ""))

    print("=== %s %s · 薄尾自測(清單先行鎖定列)===" % (_STEM, TAG))
    d = PRIOR.launcher_defaults()
    mx = steps_matrix(d["since"], d["steps"] or None)
    ids = [r["id"] for r in mx["rows"]]
    note = LOCK_NOTE_VDF_V0105 if mx.get("lists_by") == "VDF" else LOCK_NOTE_V0105
    chk("v0105-① 真樹:矩陣最前兩列 tw_list · etf_list(鎖定 · 引擎在位 · 註記照誰先跑)· 啟動器的步照舊在後 · lists_by 與 lists_owner 一致",
        ids[:2] == ["tw_list", "etf_list"] and all(r.get("lock") and r.get("engine_ok") and note in r["why"] for r in mx["rows"][:2])
        and ids[2:] == list(d["steps"]) and mx.get("lists_by") == lists_owner(d["since"]), (ids[:4], mx.get("lists_by"), mx.get("src")))
    allowed = [s for s in d["steps"] if any(r["id"] == s and not r.get("missing") and r.get("engine_ok") for r in mx["rows"])]
    html = _matrix_rows(mx, allowed)
    chk("v0105-② 鎖定列:兩列 class lock · checked · disabled · 提示 = 誰先跑的註記;其餘 .stp 數 = allowed 數(JS boxes() 與 -Steps 不含清單步)",
        all(f"class='lock' value='{s}' checked disabled title='{note}'" in html for s in LIST_STEPS_V0105) and html.count("class='stp'") == len(allowed)
        and "value='tw_list' checked>" not in html, (html.count("class='stp'"), len(allowed)))
    from datetime import date
    ok1, r1 = PRIOR.validate({"action": "launch", "mode": "custom", "since": "2024-03-15", "steps": list(allowed[:2]), "dry": True, "noheal": False}, d, allowed, date(2026, 10, 13))
    ok2, r2 = PRIOR.validate({"action": "launch", "mode": "custom", "since": "2024-03-15", "steps": ["tw_list"], "dry": True, "noheal": False}, d, allowed, date(2026, 10, 13))
    chk("v0105-③ 決定不變:頁上勾的步照舊送 -Steps;清單步不送(validate 照舊只收啟動器的步 → 'tw_list' 被拒;清單由 ask 先跑或 VCGC 並行道先跑)",
        ok1 and r1.get("action") == "launch" and "tw_list" not in r1.get("steps", []) and not ok2, (r1.get("steps"), r2))
    chk("v0105-④ 本體已換:v0103 的 steps_matrix / _matrix_rows 指到本版 · 頁首版號 = 本版",
        _OWN.steps_matrix is steps_matrix and _OWN._matrix_rows is _matrix_rows and _OWN.VERSION == TAG[1:])
    ctx = {"ts": "2026-10-13 00:00:00", "defaults": d, "matrix": mx, "allowed": allowed,
           "db": {"state": "ABSENT", "why": "自測不讀目錄", "categories": [], "gaps": [], "frozen": []}, "ready": {"state": "GATED", "gates": {}, "next": []}}
    try:
        page = PRIOR.render_ask(ctx, "t0ken")
    except Exception as exc:
        page = "RENDER FAIL " + type(exc).__name__
    chk("v0105-⑤ 問參數頁渲染:v0105 字樣 · 兩列鎖定在矩陣最前 · 清單先行註記在頁上",
        "VDF_ENG093 v0105" in page and "class='lock' value='tw_list'" in page and "class='lock' value='etf_list'" in page and note in page
        and page.index("value='etf_list'") < page.index("value='datahome'"), page[:80] if page.startswith("RENDER") else "")
    chk("v0105-⑤b 窄螢幕:問參數頁頭有 code 斷行樣式(一次)· 資料庫狀況頁同一支 · 重套不重複 · 沒 </head> 也加",
        page.count("via-v0105-narrow") == 1 and page.index("via-v0105-narrow") < page.index("</head>")
        and _OWN.render_ask is render_ask and _OWN.render_status is render_status
        and _narrow_v0105(page) == page and _narrow_v0105("<p>x</p>").startswith(NARROW_CSS_V0105))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("v0105-⑥ 檔頭:加速器橋 · 網路橋在(__future__ 之後)· 不碰 TA-Lib · 不代設同意閘 · 不直派子行程",
        "[VIA:ACCEL-BRIDGE:" in src and "[VIA:NET-BRIDGE:" in src and src.index("from __future__") < src.index("[VIA:ACCEL-BRIDGE:")
        and "import " + "talib" not in src and 'environ["VIA_NET_' + 'CONSENT"] = "' not in src and "import " + "subprocess" not in src)
    _selftest_lists_v0105(chk)
    print("  ── 前版鏈自測(用它們自己的矩陣;VIA_SKIP_PRIOR_SELFTEST=1 略過)──")
    _patch_v0105(False)
    try:
        prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    finally:
        _patch_v0105(True)
    chk("v0105-⑦ 前版 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("  [計] %s %s 薄尾 %d/%d · %s" % (_STEM, TAG, sum(ok), len(ok), "PASS" if all(ok) else "FAIL"))
    return 0 if all(ok) else 1


def _selftest_lists_v0105(chk) -> None:
    """清單先行(VDF 自己跑)的自測:替身啟動(不起真子行程)· 暫存資料家 · 雙閘只換判斷函式(同意閘不代設)。"""
    import contextlib
    import io
    import tempfile
    fg = _fg_v0105()
    if fg is None:
        chk("v0105-⑧0 VDF 族群引擎尾版在位(清單先行要它;不在就只報這一條)", False)
        return
    V = fg.V0100
    host = sys.modules[fg.run_parallel.__module__]
    calls, rc_of = [], {}

    def stub(mdl008, r, mode, home, logs, timeout, env):
        calls.append({"id": r["id"], "mode": mode, "home": str(home), "logs": str(logs), "timeout": timeout, "lane": env.get("VIA_FG_LANE")})
        return {"id": r["id"], "mdl": r.get("mdl"), "rc": rc_of.get(r["id"], 0), "sec": 0.0, "log": "", "tail": []}

    keep = {"LAUNCH": host.LAUNCH, "gates": V.gates_open, "home": os.environ.get("VIA_VDF_FETCH_HOME"),
            "ask": _ORIG_ASK, "owner": lists_owner, "matrix": _ORIG_MATRIX}
    gate = [True]
    with tempfile.TemporaryDirectory() as td:
        home = Path(td) / "home"
        os.environ["VIA_VDF_FETCH_HOME"] = str(home)
        host.LAUNCH = stub
        V.gates_open = lambda: gate[0]
        try:
            r_ok = run_lists({"action": "launch"}, 600, fg)
            c_ok, calls[:] = list(calls), []
            chk("v0105-⑧ 清單先行全綠:009 → 010 依序 · 清單道 · live · 只放清單不放擷取道 · 日誌在資料家旁(暫存)· 每支時限 = 預算均分",
                r_ok["state"] == "OK" and [c["id"] for c in c_ok] == ["009", "010"] and all(c["lane"] == "lists" and c["mode"] == "live" for c in c_ok)
                and all(c["home"] == str(home) and c["logs"] == str(home.parent / "_logs") and c["timeout"] == 300 for c in c_ok)
                and [x["id"] for x in r_ok["rows"]] == ["009", "010"], (r_ok["state"], [c["id"] for c in c_ok]))
            rc_of["009"] = 1
            r_bad = run_lists({"action": "launch"}, 600, fg)
            c_bad, calls[:] = list(calls), []
            rc_of.clear()
            chk("v0105-⑨ 009 紅 → 停在 009(010 不起)· 狀態 FAIL",
                r_bad["state"] == "FAIL" and [c["id"] for c in c_bad] == ["009"] and "009" in r_bad["why"], (r_bad["state"], [c["id"] for c in c_bad]))
            gate[0] = False
            r_gate = run_lists({"action": "launch"}, 600, fg)
            gate[0] = True
            r_dry = run_lists({"action": "launch", "dry": True}, 600, fg)
            r_time = run_lists({"action": "launch"}, 60, fg)
            chk("v0105-⑩ 不跑的三種:雙閘沒開 GATED(提示只點名閘名)· 只看計畫 SKIP_DRY · 時間不夠 NO_TIME —— 全都零子行程",
                r_gate["state"] == "GATED" and "VIA_NET_CONSENT" in r_gate["why"] and r_dry["state"] == "SKIP_DRY" and r_time["state"] == "NO_TIME"
                and not calls, (r_gate["state"], r_dry["state"], r_time["state"], len(calls)))

            out = Path(td) / "ASK_DECISION.json"
            dec0 = [{}]

            def fake_ask(a):
                _OWN._write_json(Path(_OWN._arg(a, "--out")), dict(dec0[0]))
                return 0

            g = globals()
            g["_ORIG_ASK"] = fake_ask
            res = {}
            for case, d0, own, rcs in (("ok", {"action": "launch", "since": "2024-03-15"}, "VDF", {}),
                                       ("bad", {"action": "launch", "since": "2024-03-15"}, "VDF", {"010": 2}),
                                       ("cancel", {"action": "cancel"}, "VDF", {}),
                                       ("vcgc", {"action": "launch", "since": "2024-03-15"}, "VCGC", {})):
                dec0[0], calls[:] = d0, []
                rc_of.clear(); rc_of.update(rcs)
                g["lists_owner"] = lambda since, _o=own: _o
                with contextlib.redirect_stdout(io.StringIO()):
                    rc = cmd_ask(["--out", str(out)])
                res[case] = (rc, json.loads(out.read_text(encoding="utf-8")), [c["id"] for c in calls])
            rc_of.clear()
            ok_, bad_, can_, vc_ = res["ok"], res["bad"], res["cancel"], res["vcgc"]
            chk("v0105-⑪ ask 包裝:launch + 清單綠 → rc 0 · 決定照舊 launch · lists OK 寫回;010 紅 → rc 5 · action lists_failed(開啟器不啟動);"
                "不是 launch → 不碰;清單歸 VCGC → 零子行程 rc 0",
                ok_[0] == 0 and ok_[1]["action"] == "launch" and ok_[1]["lists"]["state"] == "OK" and ok_[2] == ["009", "010"]
                and bad_[0] == 5 and bad_[1]["action"] == "lists_failed" and bad_[1]["lists"]["state"] == "FAIL" and bad_[2] == ["009", "010"]
                and can_[0] == 0 and can_[1] == {"action": "cancel"} and not can_[2]
                and vc_[0] == 0 and vc_[1]["action"] == "launch" and vc_[1]["lists"]["by"] == "VCGC" and not vc_[2],
                {k: (v[0], v[1].get("action"), v[2]) for k, v in res.items()})
            dec0[0] = {"action": "launch", "since": "2024-03-15"}
            g["lists_owner"] = lambda since: "VDF"
            gate[0] = False
            with contextlib.redirect_stdout(io.StringIO()):
                rc_g = cmd_ask(["--out", str(out)])
            gate[0] = True
            d_g = json.loads(out.read_text(encoding="utf-8"))
            chk("v0105-⑫ 雙閘沒開 → rc 4 · action lists_gated(不代設同意閘)",
                rc_g == 4 and d_g["action"] == "lists_gated" and d_g["lists"]["state"] == "GATED", (rc_g, d_g.get("action")))

            def vcgc_matrix(since, want):
                return {"rows": [{"id": s, "why": "VCGC", "engine_ok": True} for s in LIST_STEPS_V0105] + [{"id": "x", "why": ""}], "src": "fake"}

            g["lists_owner"] = keep["owner"]
            g["_ORIG_MATRIX"] = vcgc_matrix
            mx_v = steps_matrix("2024-03-15", None)
            owner_v = lists_owner("2024-03-15")
            chk("v0105-⑬ VCGC 步冊有清單兩步 → 照工作站版(lists_by VCGC · VCGC 註記 · 不換 VDF 列)· lists_owner = VCGC",
                mx_v["lists_by"] == "VCGC" and owner_v == "VCGC" and all(LOCK_NOTE_V0105 in r["why"] and r.get("by") != "VDF" for r in mx_v["rows"][:2]),
                (mx_v["lists_by"], owner_v))
        finally:
            host.LAUNCH, V.gates_open = keep["LAUNCH"], keep["gates"]
            g = globals()
            g["_ORIG_ASK"], g["lists_owner"], g["_ORIG_MATRIX"] = keep["ask"], keep["owner"], keep["matrix"]
            if keep["home"] is None:
                os.environ.pop("VIA_VDF_FETCH_HOME", None)
            else:
                os.environ["VIA_VDF_FETCH_HOME"] = keep["home"]


if __name__ == "__main__":
    sys.exit(main())
