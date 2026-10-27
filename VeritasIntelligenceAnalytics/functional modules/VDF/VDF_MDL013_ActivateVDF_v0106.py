#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL013_ActivateVDF v0106 — 薄尾:跑完自動跳出的總覽頁直接清點資料庫(不只一條連結)+ 收尾判定

操作員令(2026-10-19):「這裡專注 修正獨立系統VDF 自動跳出HTML U/I清點資料庫沒問題就是收尾」。
  工作站真跑(launcher v0104):db_check RED,但終端那一行被截斷,總覽頁(ACTIVATE_VDF_latest.html)只有一條
  「資料庫閘(db check)」連結 → 看不到哪幾張表、為什麼紅,也沒有「可不可以收尾」的判定。
本版:
  ① 總覽 JSON 多一節 db:本輪 db check 寫出的 DB_CHECK_latest.json(檔時間 ≥ 本輪起跑才算本輪;舊檔不冒充)
     → 燈 · 家 · 冊 · 紅 / 黃 / 綠 / 他系統 列數 · VDF 自己的紅黃列 · 收尾判定(VDF 自己的表 0 紅 = 可收尾)。
  ② 自動跳出的總覽頁最上方加「資料庫清點」一節:判定一句話 + 計數卡 + VDF 紅黃表逐列(庫 · 表 · 狀態 · 列數 / 上次 · 最新日 ·
     寫入者 · 怎麼補)+ 收合的綠列與他系統表(只攤開不代修,L120)。本輪沒清點(資料庫流程沒跑 / 中斷)照實寫,不拿舊結果冒充。
  ②b 本輪判定用指紋:起跑記 DB_CHECK_latest.json 的 mtime_ns · 大小 · sha256,寫總覽時一樣 = 本輪沒重寫 → NOT_RUN(沒有時間容差);
     落檔前先標 schema / tag = v0106 再交 v0100 原版寫(v0102 外層會把落檔標回 v0102)—— 都是 PR #535 Codex P2。
  ③ 頁面:卡片內長路徑可折行(手機寬 390 px 原本被 temp 路徑撐到 418 px 橫捲)。
  ④ 他系統表 / 冊上最少 0 列的判法在 VDF_SystemManager v0155(db check 本身);本檔只讀它寫的 JSON,不重判。
其餘全照 v0105。VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib。
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
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
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

import datetime as _dt
import hashlib
import html
import importlib.util
import json
import os
import re
import sys
import tempfile
import threading
import time
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL013_ActivateVDF"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0106(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0106(p) < _vnum_v0106(__file__)), key=_vnum_v0106)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():                    # 同 v0102:前版鏈只擋載入那一刻的編譯警告
    warnings.simplefilter("ignore", SyntaxWarning)
    warnings.simplefilter("ignore", DeprecationWarning)
    _spec.loader.exec_module(PRIOR)
V0100 = PRIOR.V0100


def __getattr__(name):
    return getattr(PRIOR, name)


LAMP_ORDER = {"RED": 0, "YELLOW": 1, "GREEN": 2, "INFO": 3}
_RUN = {"t0": None, "pre": None}                   # 本輪起跑時間 + 起跑當下 DB_CHECK_latest.json 的指紋(判是不是本輪寫的)
_UNSET = object()
_RUN_LOCK = threading.Lock()


def db_report_dir(ui_dir: Path | None = None) -> Path:
    """管理員 db check 的輸出夾:VIA_VDF_HEALTH_OUT > 總覽的 ui_dir > VIA_Reports/vdf(同管理員 _out 的規則)。"""
    if os.environ.get("VIA_VDF_HEALTH_OUT"):
        return Path(os.environ["VIA_VDF_HEALTH_OUT"])
    return Path(ui_dir) if ui_dir else (V0100.VIA / "VIA_Reports" / "vdf")


def _fix_hint(r: dict) -> str:
    st, w = str(r.get("狀態") or ""), str(r.get("寫入者") or "").strip()
    who = ("跑寫入者 " + w) if w else "冊上沒登寫入者(先查誰寫)"
    if "待首寫" in st:
        return "可為空的表,還沒建:" + who
    if st.startswith("缺庫"):
        return "庫檔不在資料家:確認 --db-home / VIA_VDF_DB_HOME 指對;" + who
    if st.startswith("庫打不開"):
        return "關掉占用這個庫的程式(DuckDB 一次一個寫)再重跑"
    if st in ("過舊", "列數比上次少"):
        return "開閘後 refill --apply 補到最新;" + who
    return "開閘(操作員親手)後 refill --apply;" + who


def db_signature(j: Path) -> tuple | None:
    """檔的指紋(mtime_ns · 大小 · sha256);不在 = None。起跑記一次,寫總覽時比對 → 沒變 = 不是本輪寫的。"""
    try:
        b = j.read_bytes()
        return (j.stat().st_mtime_ns, len(b), hashlib.sha256(b).hexdigest())
    except OSError:
        return None


def db_inventory(ui_dir: Path | None = None, pre=_UNSET) -> dict:
    """讀本輪 db check 的 JSON → 清點摘要;不是本輪寫的(或不在)= NOT_RUN,不冒充。
    pre = 起跑當下同一檔的指紋(None = 起跑時檔不在);檔的指紋跟起跑時一樣 = 本輪沒重寫 → NOT_RUN(不靠時間容差,PR #535 Codex P2)。"""
    d = db_report_dir(ui_dir)
    j = d / "DB_CHECK_latest.json"
    if pre is _UNSET:
        pre = _RUN["pre"] if _RUN["t0"] is not None else _UNSET
    base = {"json": str(j), "page": str(d / "DB_CHECK_latest.html")}
    if not j.is_file():
        return dict(base, lamp="NOT_RUN", closeout=False, why="本輪沒有 db check 結果(資料庫流程沒跑 / 被中斷)")
    if pre is not _UNSET and pre is not None and db_signature(j) == pre:
        return dict(base, lamp="NOT_RUN", closeout=False,
                    why="DB_CHECK_latest.json 本輪起跑後沒重寫(上一輪 %s 寫的);本輪資料庫流程沒寫出新結果 → 不拿舊結果冒充"
                    % _dt.datetime.fromtimestamp(j.stat().st_mtime).isoformat(timespec="seconds"))
    try:
        o = json.loads(j.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return dict(base, lamp="RED", closeout=False, why="DB_CHECK_latest.json 讀不了:%s" % type(exc).__name__)
    rows = [r for r in (o.get("rows") or []) if isinstance(r, dict)]
    mine = [r for r in rows if not str(r.get("狀態") or "").startswith("他系統表")]
    other = [r for r in rows if str(r.get("狀態") or "").startswith("他系統表")]
    cnt = {k: sum(1 for r in mine if r.get("燈") == k) for k in ("RED", "YELLOW", "GREEN", "INFO")}
    probs = sorted((r for r in mine if r.get("燈") in ("RED", "YELLOW")), key=lambda r: LAMP_ORDER.get(r.get("燈"), 9))
    lamp = str(o.get("lamp") or "NODATA")
    closeout = lamp in ("GREEN", "YELLOW") and cnt["RED"] == 0 and bool(mine)
    return dict(base, lamp=lamp, closeout=closeout, ts=o.get("ts"), tag=o.get("tag"), home=o.get("home"), book=o.get("book"),
                why=o.get("why"), counts=cnt, other=len(other), tables=len(mine),
                problems=[{k: r.get(k) for k in ("燈", "庫", "表", "狀態", "列數", "上次列數", "最新日", "落後天", "寫入者")}
                          | {"怎麼補": _fix_hint(r)} for r in probs],
                ok=[{k: r.get(k) for k in ("庫", "表", "列數", "最新日")} for r in mine if r.get("燈") == "GREEN"],
                other_rows=[{k: r.get(k) for k in ("庫", "表", "狀態", "寫入者")} for r in other])


def _e(x) -> str:
    return "—" if x is None or x == "" else html.escape(str(x))


def db_section(db: dict | None) -> str:
    """總覽頁的「資料庫清點」一節(HTML 片段;全部字串跳脫)。"""
    lampc = {"GREEN": "#1a7f37", "YELLOW": "#9a6700", "INFO": "#6e7781", "NOT_RUN": "#6e7781", "NODATA": "#6e7781"}

    def lamp(x):
        return f'<span class="lamp" style="background:{lampc.get(x, "#cf222e")}">{html.escape(str(x))}</span>'
    if not db:
        return ""
    if db.get("lamp") == "NOT_RUN" or "counts" not in db:
        return (f'<section id="db-inventory" class="card" style="margin:12px 0"><h2 style="margin:0 0 6px">資料庫清點 {lamp(db.get("lamp"))}</h2>'
                f'<p><b>不能收尾:</b>{_e(db.get("why"))}</p><p class="mut">上一輪的清點頁(可能不是本輪):{_e(db.get("page"))}</p></section>')
    c = db["counts"]
    verdict = ("<b style='color:#1a7f37'>資料庫清點沒問題 → 可收尾</b>(VDF 自己的表 0 紅" + (f";黃 {c['YELLOW']} 列待補,不擋收尾" if c["YELLOW"] else "") + ")"
               if db.get("closeout") else f"<b style='color:#cf222e'>還不能收尾</b>:VDF 自己的表 紅 {c['RED']} 列(看下表「怎麼補」)")
    trs = "".join(f"<tr><td>{lamp(r['燈'])}</td><td>{_e(r['庫'])}</td><td>{_e(r['表'])}</td><td>{_e(r['狀態'])}</td>"
                  f"<td>{_e(r['列數'])} / {_e(r['上次列數'])}</td><td>{_e(r['最新日'])}</td><td>{_e(r['寫入者'])}</td><td>{_e(r['怎麼補'])}</td></tr>"
                  for r in db.get("problems") or [])
    ok = "".join(f"<tr><td>{_e(r['庫'])}</td><td>{_e(r['表'])}</td><td>{_e(r['列數'])}</td><td>{_e(r['最新日'])}</td></tr>" for r in db.get("ok") or [])
    oth = "".join(f"<tr><td>{_e(r['庫'])}</td><td>{_e(r['表'])}</td><td>{_e(r['狀態'])}</td><td>{_e(r['寫入者'])}</td></tr>" for r in db.get("other_rows") or [])
    page = Path(str(db.get("page") or ""))
    try:
        href = os.path.relpath(page, V0100.REPORT_DIR)
    except ValueError:
        href = page.as_uri() if page.is_absolute() else str(page)
    return f"""<section id="db-inventory" class="card" style="margin:12px 0">
<h2 style="margin:0 0 6px">資料庫清點 {lamp(db['lamp'])}</h2>
<p>{verdict}</p>
<div class="mut">家 {_e(db.get('home'))} · 冊 {_e(db.get('book'))} · {_e(db.get('ts'))} · {_e(db.get('tag'))} · <a href="{html.escape(href)}">全表(DB_CHECK_latest.html)</a></div>
<div class="grid"><div class="card"><b>VDF 自己的表</b> {db['tables']}<br>紅 {c['RED']} · 黃 {c['YELLOW']} · 綠 {c['GREEN']} · 冊外 {c['INFO']}</div>
<div class="card"><b>他系統表</b> {db['other']}<br><span class="mut">VRN / VCGC 寫的表:只攤開不代修,不計 VDF 的燈(L120)</span></div></div>
{('<div class="wrap"><table><tr><th>燈</th><th>庫</th><th>表</th><th>狀態</th><th>列數 / 上次</th><th>最新日</th><th>寫入者</th><th>怎麼補</th></tr>' + trs + '</table></div>') if trs else '<p>VDF 自己的表沒有紅黃列。</p>'}
<details><summary>綠的表({len(db.get('ok') or [])})</summary><div class="wrap"><table><tr><th>庫</th><th>表</th><th>列數</th><th>最新日</th></tr>{ok}</table></div></details>
<details><summary>他系統表({db['other']})</summary><div class="wrap"><table><tr><th>庫</th><th>表</th><th>狀態</th><th>寫入者</th></tr>{oth}</table></div></details>
</section>
"""


_RENDER_V0100 = V0100.render_html
_WRITE_REPORT_PRIOR = V0100.write_report          # = v0102 的 write_report(跑時把 schema 標成 v0102 再寫)


def _chain_var(name: str, default=None):
    """沿前版鏈找第一個自己定義 name 的模組,回那個值(v0102 的 _WRITE_REPORT_V0100 · _IN_RUN)。"""
    m = PRIOR
    for _ in range(16):
        if name in vars(m):
            return vars(m)[name]
        m = vars(m).get("PRIOR")
        if m is None:
            break
    return default


# v0102 存下的 v0100 原版 write_report;本版先標 v0106 再直接交它寫,免得 v0102 外層把落檔標回 v0102(PR #535 Codex P2)
_WRITE_REPORT_V0100 = _chain_var("_WRITE_REPORT_V0100", _WRITE_REPORT_PRIOR)


PAGE_CSS = ".grid>.card{overflow-wrap:anywhere;min-width:0}details{margin:6px 0}"   # 長路徑(temp 夾)在手機寬不撐出橫捲


def render_html(card: dict, ui_dir: Path) -> str:
    h = _RENDER_V0100(card, ui_dir).replace("</style>", PAGE_CSS + "</style>", 1)
    sec = db_section(card.get("db"))
    if not sec:
        return h
    i = h.find('<div class="wrap"><table>')
    return (h[:i] + sec + h[i:]) if i >= 0 else h.replace("</body>", sec + "</body>")


def write_report(card: dict, ui_dir: Path | None = None) -> dict:
    if _RUN["t0"] is None:                         # 不在本版的一輪裡(前版自測直呼)= 照前版
        return _WRITE_REPORT_PRIOR(card, ui_dir) if ui_dir is not None else _WRITE_REPORT_PRIOR(card)
    card["db"] = db_inventory(ui_dir)
    card["schema"], card["tag"] = "VDF_ActivateVDF_v0106", TAG   # 先標本版再落檔(JSON 與頁頭都是 v0106)
    return _WRITE_REPORT_V0100(card, ui_dir) if ui_dir is not None else _WRITE_REPORT_V0100(card)


V0100.render_html = render_html
V0100.write_report = write_report

_ACTIVATE_V0105 = PRIOR.activate


def activate(opt, manager: Path | None = None, py: str | None = None, temp: Path | None = None) -> dict:
    """同 v0105 activate;記本輪起跑時間給 db_inventory 判新舊;跑完印清點一行。"""
    keep = PRIOR.TAG
    PRIOR.TAG = TAG
    with _RUN_LOCK:
        _RUN["t0"] = time.time()
        _RUN["pre"] = db_signature(db_report_dir() / "DB_CHECK_latest.json")
    try:
        card = _ACTIVATE_V0105(opt, manager, py, temp)
    finally:
        PRIOR.TAG = keep
        with _RUN_LOCK:
            _RUN["t0"], _RUN["pre"] = None, None
    db = card.get("db") or {}
    c = db.get("counts") or {}
    print(f"  [資料庫清點] {db.get('lamp')} · " + (f"VDF 表 紅 {c.get('RED')} · 黃 {c.get('YELLOW')} · 綠 {c.get('GREEN')} · 他系統 {db.get('other')} · "
          + ("可收尾" if db.get("closeout") else "還不能收尾") if c else str(db.get("why"))) + f" · 頁 {card.get('report', {}).get('html')}", flush=True)
    return card


for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 薄尾自測(總覽頁清點資料庫 + 收尾判定;沙盒 · 零網路)===")
    keep_env = os.environ.get("VIA_VDF_HEALTH_OUT")
    keep_rep = V0100.REPORT_DIR
    try:
        with tempfile.TemporaryDirectory(prefix="activatevdf106_") as td:
            t = Path(td)
            os.environ.pop("VIA_VDF_HEALTH_OUT", None)
            ui = t / "vdf"
            ui.mkdir()
            rows = [{"庫": "vdf_tw_market.duckdb", "表": "tw_daily_prices", "狀態": "OK", "燈": "GREEN", "列數": 10, "最新日": "2026-10-17", "寫入者": "VDF_ENG073"},
                    {"庫": "vdf_tw_market.duckdb", "表": "tw_chip_inst<script>", "狀態": "缺表", "燈": "RED", "列數": None, "上次列數": 5, "寫入者": "VDF_ENG056"},
                    {"庫": "vdf_global_market.duckdb", "表": "us_macro", "狀態": "過舊", "燈": "YELLOW", "列數": 9, "寫入者": "VDF_ENG073"},
                    {"庫": "vdf_tw_market.duckdb", "表": "vrn_report_basic", "狀態": "他系統表(VRN 寫)· 缺表 · VDF 只攤開不代修", "燈": "INFO", "寫入者": ""}]
            red = {"ts": "2026-10-19T10:00:00", "tag": "VDF_SystemManager v0155", "home": "H", "book": "B", "lamp": "RED", "rows": rows}
            j = ui / "DB_CHECK_latest.json"
            pre0 = db_signature(j)                     # 起跑時檔不在 = None
            j.write_text(json.dumps(red, ensure_ascii=False), encoding="utf-8")
            d1 = db_inventory(ui, pre=pre0)
            pre1 = db_signature(j)                     # 上一輪剛寫完(< 2 秒)就起下一輪
            green = dict(red, lamp="YELLOW", rows=[r for r in rows if r["燈"] != "RED"])
            j.write_text(json.dumps(green, ensure_ascii=False), encoding="utf-8")
            d2 = db_inventory(ui, pre=pre1)
            d3 = db_inventory(ui, pre=db_signature(j))  # 起跑後沒重寫:就算檔是 1 秒前寫的也不算本輪
            d4 = db_inventory(t / "nowhere", pre=None)
            chk("㉕ 清點摘要:本輪的 DB_CHECK JSON → VDF 表紅黃綠 · 他系統另計;VDF 0 紅才可收尾(黃不擋);"
                "起跑後沒重寫(指紋同起跑時,沒有時間容差)/ 沒檔 = NOT_RUN 不能收尾(不拿舊結果冒充)",
                d1["lamp"] == "RED" and not d1["closeout"] and d1["counts"] == {"RED": 1, "YELLOW": 1, "GREEN": 1, "INFO": 0}
                and d1["other"] == 1 and [r["表"] for r in d1["problems"]] == ["tw_chip_inst<script>", "us_macro"]
                and "refill --apply" in d1["problems"][0]["怎麼補"]
                and d2["closeout"] and d2["counts"]["RED"] == 0 and d3["lamp"] == "NOT_RUN" and not d3["closeout"]
                and d4["lamp"] == "NOT_RUN", {"紅": d1["lamp"], "黃": d2["lamp"], "舊": d3["lamp"], "沒檔": d4["lamp"]})
            s1, s3 = db_section(d1), db_section(d3)
            chk("㉖ 頁上「資料庫清點」一節:判定一句話 + 計數 + 紅黃逐列(含怎麼補)+ 收合的綠 / 他系統;表名跳脫;NOT_RUN 照實寫不能收尾",
                "還不能收尾" in s1 and "tw_chip_inst&lt;script&gt;" in s1 and "<script>" not in s1 and "他系統表" in s1
                and "怎麼補" in s1 and "DB_CHECK_latest.html" in s1 and "可收尾" in db_section(d2) and "不能收尾" in s3
                and "上一輪" in s3)
            V0100.REPORT_DIR = t / "activate"
            j.write_text(json.dumps(red, ensure_ascii=False), encoding="utf-8")
            res = V0100.optimize_resources(want=3, stamp="20261019_100000", root=t / "tmp")
            card = {"schema": "x", "tag": "x", "stamp": "20261019_100000", "ts": "2026-10-19T10:00:00", "manager": "m", "mode": "fixture", "dry": True,
                    "resources": res, "memgate": {"min_avail_mb": 1, "waits": []},
                    "lists": {"lamp": "YELLOW", "note": "n", "runs": [], "verify": {"lamp": "GREEN", "step": "lists_verify", "rc": 0, "secs": 1}},
                    "flows": [{"flow": "db", "lamp": "RED", "steps": [{"lamp": "RED", "step": "db_check", "rc": 1, "secs": 2, "summary": "s"}]}],
                    "ui": None, "lamp": "RED"}
            in_run_v0102 = _chain_var("_IN_RUN")          # 真跑時 v0102 activate 開著它 → 它的外層會改 schema;照真跑開著測
            _RUN["t0"], _RUN["pre"] = time.time() - 5, None
            if in_run_v0102 is not None:
                in_run_v0102.set()
            try:
                rep = V0100.write_report(card, ui)
            finally:
                _RUN["t0"], _RUN["pre"] = None, None
                if in_run_v0102 is not None:
                    in_run_v0102.clear()
            h = Path(rep["html"]).read_text(encoding="utf-8")
            js = json.loads(Path(rep["json"]).read_text(encoding="utf-8"))
            chk("㉗ 前版鏈寫總覽時走本版:落檔 JSON 的 schema / tag 是本版(不是 v0102)· 有 db 節(燈 · 計數 · 收尾判定)· 自動跳出的那一頁在步驟表之前就有資料庫清點;卡片長路徑可折行",
                js.get("db", {}).get("lamp") == "RED" and js["db"]["closeout"] is False and card["tag"] == TAG
                and js.get("schema") == "VDF_ActivateVDF_v0106" and js.get("tag") == TAG and TAG in h
                and 'id="db-inventory"' in h and h.index('id="db-inventory"') < h.index("<th>流程</th>") and PAGE_CSS in h, js.get("db", {}).get("lamp"))
    finally:
        V0100.REPORT_DIR = keep_rep
        if keep_env is None:
            os.environ.pop("VIA_VDF_HEALTH_OUT", None)
        else:
            os.environ["VIA_VDF_HEALTH_OUT"] = keep_env
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    chk("㉘ 加速器橋 · 網路橋在;不匯入他系統程式;不碰 TA-Lib;同意閘不寫",
        "VIA:ACCEL-BRIDGE" in src and "def _via_net" in src
        and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VCGC"))]
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
        and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src))
    n = sum(ok)
    print(f"  [計] {TAG} 本版 {n}/{len(ok)} · {'PASS' if n == len(ok) else 'FAIL'}")
    if n != len(ok):
        return 1
    rc1 = PRIOR.selftest()
    return rc1 if rc1 in (0, 1, 2, 3) else 1        # 前版紅照實回(同 v0102;PR #528 Codex P1)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    opt = V0100.parse(argv)
    if opt.verb != "run":
        return V0100.main(argv)
    card = activate(opt)
    return {"GREEN": 0, "YELLOW": 2, "INTERRUPTED": 130}.get(card["lamp"], 1)


if __name__ == "__main__":
    raise SystemExit(main())
