#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [改號接線 2026-10-20] 本檔 = 工作站分支 workstation-20261020 的 VDF_SystemManager v0156 原文,改號 v0160 接到 main 尾版之上(兩條線同號不同內容;操作員裁定「接到 main 上」)。
#   只改寫死的本版版號;文中其他 v0156 字樣指工作站線的同一支(即本線 v0160)。前版照 glob 取本族比本檔小的最大一支 = main 的尾版。
# [本線加段 2026-10-20 · U/I 實測修正] 操作員令「實測實際修正自動完成直到輸出結果驗證結果無誤於HTML U/I」:
#   無頭 Chromium 讀渲染後的資料庫檢查頁 ↔ DB_CHECK_latest.json ↔ DuckDB 唯讀重數,三方比對值全對(65 列 · 34 表重數 0 差),
#   但頁與 CSV 的整數欄印成小數(列數 1163.0 · 最少 1.0;181 格)、空的寫入者格是空白(27 格,其他空值頁內 JS 已改 —)。
#   根因:v0151 _write_db 用 pandas DataFrame,有 None 的整數欄被轉成 float64。本版在 db check 寫檔時接手 CSV 與頁上那張表:
#   整數照整數印、空值頁上一律 —(CSV 留空)、燈色與頁殼照前版;JSON 不動(本來就是整數)。自測 ⑨⑩⑪。
#   截圖再看:頁內燈號列寫「綠 18」,同頁摘要寫「綠 4 · 資訊 14」—— v0154 展現腳本的嚴重度表把 INFO 歸綠(INFO:2),
#   表上 INFO 卻是灰字。本版把 v0154 模組的 _TK_JS 換成 INFO:3(歸灰;字級套件每次產生都讀它)→ 燈號列「綠 4 · 灰 14」與摘要一致。自測 ⑫。
#   手機 390 再看:長欄(> 24 字)套 overflow-wrap:anywhere,表格把「表」「狀態」欄壓到一字一行(aaii_sentiment 拆成 9 行),
#   表也因此永遠不比手機寬、橫捲框不會出現。改 break-word(長字不拆,表變寬 → 字級套件自己的橫捲框接手);CSS 與 JS 兩處。自測 ⑬。
"""VDF_SystemManager v0156 — 薄尾:啟動就緒的短令檢查沿 Register 點源鏈讀(問參數頁「啟動器/鏈缺:Register via-vdffetch」假紅修正)

工作站實錄(2026-10-12 14:59 問參數頁):「啟動就緒 RED · 來源 VDF_SystemManager_v0155.py · [修] 這些是樹上的檔,不是設定:git pull…」。
根因:v0104 read_launch ④ 只讀 Register-VIA-Commands 尾版一檔找 `function global:via-vdffetch {` 等 16 個啟動短令;
  短令冊自 v0244 起是薄尾(`. (Join-Path $PSScriptRoot "…vNNNN.ps1")` 往回接),16 個短令全在 v0243 → 尾版單檔永遠找不到 → 假紅(容器也一樣)。
本版:v0104 本體代答前,把它的 `_src` 換成「Register 冊沿點源鏈讀」的讀器(尾版 → 前版 …;只讀不執行;防環;不是 Register 的檔照舊),
  判準不變(標記本身 `function global:<短令> {`);代答完還原。`all` 的 ready 步也走本版門(v0155 的 READY 指到本版)。
鏈的讀法 = VCGC 唯一入口控制 v0106 命令冊鏈讀的同一條正則(抄尺不抄程式;本檔不載 VCGC 程式,L120 三系統獨立)。
其餘(all · 問參數頁 · 子行程 · 不代設同意閘 · 零網路 · 不碰 TA-Lib)照 v0155。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本檔零網路。"""
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
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[1]
_STEM = "VDF_SystemManager"
TAG = "v0160"
BOOK_RX_V0156 = re.compile(r"^Register-VIA-Commands-v\d{4}\.ps1$")
DOT_RX_V0156 = re.compile(r"""^\s*\.\s*\(?\s*(?:Join-Path\s+\$PSScriptRoot\s+)?["']?(?:\$PSScriptRoot[\\/])?(Register-VIA-Commands-v\d{4}\.ps1)""", re.M)


def _vnum_v0156(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0156(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0156(p) < _vnum_v0156(__file__)), key=_vnum_v0156)
PRIOR = _load_v0156(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


# ---------------------------------------------------------------- Register 冊沿點源鏈讀(只讀不執行;防環)
def _read_text(p) -> str:
    try:
        return Path(p).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def register_chain(book: Path) -> list:
    """短令冊 + 它沿 dot-source 往回接的每一本(尾版在前;同夾;只讀;互相點源也不會無限迴圈)。"""
    book = Path(book)
    out, seen, todo = [], set(), [book]
    while todo:
        p = todo.pop(0)
        key = p.name.lower()
        if key in seen or not p.is_file():
            continue
        seen.add(key)
        out.append(p)
        for name in DOT_RX_V0156.findall(_read_text(p)):
            q = p.parent / name
            if q.name.lower() not in seen:
                todo.append(q)
    return out


def register_chain_text(book: Path) -> str:
    return "\n".join(_read_text(p) for p in register_chain(book))


def _src_chain(p) -> str:
    """v0104 `_src` 的替身:Register 冊 → 整條鏈的文字;其他檔照舊讀單檔。"""
    q = Path(p) if p else None
    if q is not None and BOOK_RX_V0156.match(q.name):
        return register_chain_text(q)
    return _read_text(q) if q is not None else ""


def read_launch(probe: bool = False, environ=None) -> dict:
    """啟動就緒(只量不動手;同意閘永不代設):v0104 本體代答,但短令檢查沿 Register 點源鏈讀;本體缺席照 v0155 回 ABSENT。"""
    m, why = PRIOR._door_v0104()
    if m is None or not callable(getattr(m, "read_launch", None)):
        return PRIOR.read_launch(probe=probe, environ=environ)
    orig = getattr(m, "_src", None)
    m._src = _src_chain
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            r = m.read_launch(probe=probe, environ=environ)
    finally:
        if orig is not None:
            m._src = orig
    r = dict(r)
    r["via"] = TAG
    r["door"] = "v0104 本體代答(v0156;短令沿 Register 點源鏈讀)"
    return r


PRIOR.READY = read_launch          # v0155 `all` 的 ready 步走本版門(自測前版鏈時換回)


# ---------------------------------------------------------------- [本線加段] db check 的 CSV 與頁上表:整數照整數、空值 —
DB_COLS_V0160 = ["庫", "表", "狀態", "燈", "列數", "最少", "上次列數", "最新日", "落後天", "寫入者", "檔"]
LAMP_CSS_V0160 = (("RED", "#dc2626"), ("YELLOW", "#b45309"), ("GREEN", "#16a34a"), ("INFO", "#6b7280"))
DB_MOD_V0160 = PRIOR.DB_MOD                      # v0151 模組(db_check 寫檔呼它的 _write_db / _out)


def _cell_v0160(v, blank: str) -> str:
    """一格的字:None / 空字串 / NaN → blank;整數值的 float(pandas 補過的)→ 整數字。"""
    if v is None or v == "" or (isinstance(v, float) and v != v):
        return blank
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def _table_v0160(rows: list) -> str:
    import html
    head = "".join("<th>%s</th>" % html.escape(c) for c in DB_COLS_V0160)
    body = []
    for r in rows:
        tds = []
        for c in DB_COLS_V0160:
            t = _cell_v0160(r.get(c), "—")
            css = dict(LAMP_CSS_V0160).get(t) if c == "燈" else None
            tds.append("<td style='color:%s;font-weight:600'>%s</td>" % (css, t) if css else "<td>%s</td>" % html.escape(t))
        body.append("<tr>%s</tr>" % "".join(tds))
    return "<table class=\"dataframe m\"><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (head, "".join(body))


def _write_db_v0160(o: dict) -> dict:
    """照前版寫 json / csv / html(頁殼、燈色、摘要照舊),再重寫 CSV 與頁上那張表(值不變,只改印法)。"""
    import csv
    files = _WRITE_DB_PRIOR_V0160(o)
    rows = o.get("rows") or []
    fc, fh = Path(files["csv"]), Path(files["html"])
    with fc.open("w", encoding="utf-8-sig", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(DB_COLS_V0160)
        w.writerows([[_cell_v0160(r.get(c), "") for c in DB_COLS_V0160] for r in rows])
    page = fh.read_text(encoding="utf-8")
    a, b = page.find("<table"), page.rfind("</table>")
    if a >= 0 and b > a:
        fh.write_text(page[:a] + _table_v0160(rows) + page[b + len("</table>"):], encoding="utf-8")
    return files


def _mod_v0160(tag: str):
    """沿前版鏈(各支模組自己的 PRIOR,不走 __getattr__ 轉接)找本族指定版號那支模組。"""
    m = PRIOR
    while m is not None:
        if vars(m).get("TAG") == tag:
            return m
        m = vars(m).get("PRIOR")
    return None


TK_MOD_V0160 = _mod_v0160("v0154")              # 字級套件 v2 本體(typekit_block 每次讀它的 _TK_JS)
_TK_JS_ORIG_V0160 = vars(TK_MOD_V0160).setdefault("_TK_JS_ORIG_V0160", TK_MOD_V0160._TK_JS) if TK_MOD_V0160 else ""
_TK_CSS_ORIG_V0160 = vars(TK_MOD_V0160).setdefault("_TK_CSS_ORIG_V0160", TK_MOD_V0160._TK_CSS) if TK_MOD_V0160 else ""
WRAP_V0160 = ("overflow-wrap:anywhere", "overflow-wrap:break-word")


def _tk_install_v0160():
    """INFO 歸灰(表上本來就是灰字,燈號列與摘要同數)· 長欄 break-word(手機不一字一行;表變寬 → 橫捲框接手)。"""
    if TK_MOD_V0160 is not None:
        TK_MOD_V0160._TK_JS = _TK_JS_ORIG_V0160.replace("INFO:2,", "INFO:3,").replace(*WRAP_V0160)
        TK_MOD_V0160._TK_CSS = _TK_CSS_ORIG_V0160.replace(*WRAP_V0160)


def _tk_restore_v0160():
    if TK_MOD_V0160 is not None:
        TK_MOD_V0160._TK_JS, TK_MOD_V0160._TK_CSS = _TK_JS_ORIG_V0160, _TK_CSS_ORIG_V0160


_tk_install_v0160()


# 原版存在 v0151 模組上(同一行程本檔被載兩次也拿得到原版,不會包兩層);db check 經 DB_MOD._write_db 寫 → 走本版;自測前版鏈時換回
_WRITE_DB_PRIOR_V0160 = vars(DB_MOD_V0160).setdefault("_WRITE_DB_ORIG_V0160", DB_MOD_V0160._write_db)
DB_MOD_V0160._write_db = _write_db_v0160


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    import json
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print("=== %s %s · 薄尾自測(啟動就緒短令沿 Register 點源鏈讀)===" % (_STEM, TAG))
    td = Path(tempfile.mkdtemp(prefix="pv_vdf156_"))
    try:
        b1, b2, b3 = (td / ("Register-VIA-Commands-v%04d.ps1" % i) for i in (1, 2, 3))
        b1.write_text("function global:via-vdffetch {\n  param()\n}\n", encoding="utf-8")
        b2.write_text('. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0001.ps1")\nfunction global:via-x {}\n', encoding="utf-8")
        b3.write_text('. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0002.ps1")\n# 薄尾:這裡沒有 via-vdffetch\n', encoding="utf-8")
        ch = register_chain(b3)
        chk("① 鏈讀:尾版 v0003 → v0002 → v0001(尾版在前 · 只同夾 · 只讀)", [x.name for x in ch] == [b3.name, b2.name, b1.name], [x.name for x in ch])
        rx = re.compile(r"function global:" + re.escape("via-vdffetch") + r"\s*\{")
        chk("② 薄尾單檔找不到 via-vdffetch,沿鏈讀找得到(v0104 ④ 的同一條判準)",
            rx.search(_read_text(b3)) is None and rx.search(_src_chain(b3)) is not None)
        la, lb = td / "Register-VIA-Commands-v0010.ps1", td / "Register-VIA-Commands-v0011.ps1"
        la.write_text('. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0011.ps1")\n', encoding="utf-8")
        lb.write_text('. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0010.ps1")\n', encoding="utf-8")
        other = td / "Invoke-VIA-X-v0100.ps1"
        other.write_text("param()\n", encoding="utf-8")
        chk("③ 防環(互相點源 = 2 本)· 不是 Register 的檔照舊讀單檔 · 缺檔回空字串",
            len(register_chain(la)) == 2 and _src_chain(other) == "param()\n" and _src_chain(td / "nope.ps1") == "" and _src_chain(None) == "")
        rd = read_launch(probe=False)
        la_ = rd.get("launchers") or {}
        chk("④ 真樹:read_launch 由本版門代答,16 個啟動短令沿鏈全找到(cmds_missing 空)· why 不再含「Register via-vdffetch」· 同意閘只讀",
            str(rd.get("door", "")).startswith("v0104 本體代答(v0156") and la_.get("cmds", {}).get("via-vdffetch") is True and not la_.get("cmds_missing")
            and "Register via-vdffetch" not in str(rd.get("why", "")) and all(k in rd for k in ("state", "consent", "python", "hist_limit")),
            {k: rd.get(k) for k in ("state", "why", "door")} | {"missing": la_.get("cmds_missing")})
        m, _ = PRIOR._door_v0104()
        chk("⑤ 代答完 v0104 本體的 _src 還原(不留替身)· v0155 的 READY 指到本版門(all 的 ready 步走本版)",
            m is not None and getattr(m, "_src", None) is not _src_chain and PRIOR.READY is read_launch)
        buf = io.StringIO()
        keep_no_open = os.environ.get("VIA_NO_OPEN")
        os.environ["VIA_NO_OPEN"] = "1"
        try:
            with contextlib.redirect_stdout(buf):
                rc_dry = main(["all", "--dry", "--jobs", "9"])
        finally:
            if keep_no_open is None:
                os.environ.pop("VIA_NO_OPEN", None)
            else:
                os.environ["VIA_NO_OPEN"] = keep_no_open
        chk("⑥ all --dry 經本版 main 直通 v0155(列 9 步 · rc 0 · 不寫檔)", rc_dry == 0 and all(s in buf.getvalue() for s in PRIOR.STEPS_V0155), buf.getvalue()[:200])
        body = Path(__file__).read_text(encoding="utf-8")
        chk("⑦ 橋在(__future__ 之後)· 不碰 TA-Lib · 不代設同意閘 · 不載入 VCGC 程式 · 本檔不起子行程 · 零網路",
            all(x in body for x in ("[VIA:ACCEL-BRIDGE:v0100]", "[VIA:NET-BRIDGE:v0100]")) and body.index("from __future__") < body.index("[VIA:ACCEL-BRIDGE:v0100]")
            and "import " + "talib" not in body and 'environ["VIA_NET_' + 'CONSENT"] = "' not in body and "CGC_MDL" + "1" not in body
            and "import " + "subprocess" not in body and "url" + "lib" not in body and "req" + "uests" not in body)
        cells = [_cell_v0160(1163.0, "—"), _cell_v0160(None, "—"), _cell_v0160(float("nan"), "—"), _cell_v0160("", "—"),
                 _cell_v0160(0, "—"), _cell_v0160(0.5, "—"), _cell_v0160("2026-10-20", "—"), _cell_v0160(None, "")]
        chk("⑨ 一格的字:1163.0 → 1163 · None / NaN / 空字串 → — · 0 → 0 · 0.5 照印 · 日期照印 · CSV 空值留空",
            cells == ["1163", "—", "—", "—", "0", "0.5", "2026-10-20", ""], cells)
        out = td / "out"
        o = {"ts": "2026-10-20T10:00:00", "home": str(td / "home"), "book": "VIA_DB_Table_SSOT_v0102.json",
             "summary": {"RED": 1, "YELLOW": 0, "GREEN": 1, "INFO": 0},
             "rows": [{"庫": "a.duckdb", "表": "t1", "狀態": "OK", "燈": "GREEN", "列數": 1163, "最少": 1, "上次列數": 40.0, "最新日": None, "落後天": float("nan"),
                       "寫入者": "VDF_ENG051", "檔": "/x/a.duckdb"},
                      {"庫": "a.duckdb", "表": "t2", "狀態": "缺表", "燈": "RED", "列數": None, "最少": 1, "上次列數": None, "最新日": "2026-10-17", "落後天": 3,
                       "寫入者": "", "檔": "/x/a.duckdb"}]}
        keep_out = DB_MOD_V0160._out
        DB_MOD_V0160._out = lambda: out
        try:
            fs = DB_MOD_V0160._write_db(o)            # db check 寫檔走的同一個名字
        finally:
            DB_MOD_V0160._out = keep_out
        csv_t = Path(fs["csv"]).read_text(encoding="utf-8-sig")
        page = Path(fs["html"]).read_text(encoding="utf-8")
        tbl = page[page.find("<table"):page.rfind("</table>")]
        chk("⑩ 寫檔(暫存夾):CSV 整數照整數、空值留空、沒有 .0 · 頁上表整數照整數、空值 —、燈色照前版 · 頁殼(標題 · 摘要)照前版 · JSON 照前版",
            "a.duckdb,t1,OK,GREEN,1163,1,40,,,VDF_ENG051,/x/a.duckdb" in csv_t and "a.duckdb,t2,缺表,RED,,1,,2026-10-17,3,,/x/a.duckdb" in csv_t
            and ".0," not in csv_t and "<td>1163</td>" in tbl and "1163.0" not in page and "NaN" not in page and tbl.count("<td>—</td>") == 5
            and "<td style='color:#dc2626;font-weight:600'>RED</td>" in tbl and "<h1>VDF 資料庫檢查" in page and tbl.count("<tr>") == 3
            and json.loads(Path(fs["json"]).read_text(encoding="utf-8"))["rows"][0]["列數"] == 1163,
            csv_t[:300] + " | " + tbl[:300])
        chk("⑪ 接手點:v0151 模組的 _write_db = 本版(db check 經它寫)· 原版存在模組上(再載一次不包兩層)",
            DB_MOD_V0160._write_db is _write_db_v0160 and vars(DB_MOD_V0160).get("_WRITE_DB_ORIG_V0160") is _WRITE_DB_PRIOR_V0160
            and getattr(_WRITE_DB_PRIOR_V0160, "__name__", "") == "_write_db")
        blk = TK_MOD_V0160.typekit_block() if TK_MOD_V0160 is not None else ""
        chk("⑫ 展現腳本:INFO 歸灰(INFO:3)· 綠只算 GREEN / OK / PASS · 原本存在 v0154 模組上 · 只改這一處",
            TK_MOD_V0160 is not None and "INFO:3," in blk and "INFO:2," not in blk and "GREEN:2,OK:2,PASS:2," in blk
            and "INFO:2," in _TK_JS_ORIG_V0160 and TK_MOD_V0160._TK_JS == _TK_JS_ORIG_V0160.replace("INFO:2,", "INFO:3,").replace(*WRAP_V0160),
            blk[blk.find("var SEV"):blk.find("var SEV") + 160] if blk else "v0154 找不到")
        css_b = blk[blk.find("<style"):blk.find("</style>")]
        js_b = blk[blk.find("<script"):]
        chk("⑬ 長欄換行:字級套件 CSS 與 JS 都是 overflow-wrap:break-word、沒有 anywhere(手機不把長字壓成一字一行;表變寬由橫捲框接手)· 前版原文兩處都是 anywhere",
            "overflow-wrap:anywhere" not in blk and "td.via-long{max-width:" in css_b and "overflow-wrap:break-word" in css_b and "overflow-wrap:break-word" in js_b
            and "overflow-wrap:anywhere" in _TK_CSS_ORIG_V0160 and "overflow-wrap:anywhere" in _TK_JS_ORIG_V0160, blk.count("anywhere"))
    finally:
        shutil.rmtree(td, ignore_errors=True)
    print("  ── 前版鏈自測(原樣印出;VIA_SKIP_PRIOR_SELFTEST=1 略過)──")
    PRIOR.READY = PRIOR.read_launch          # 前版自測用它自己的門、它自己的寫檔與它自己的展現腳本
    DB_MOD_V0160._write_db = _WRITE_DB_PRIOR_V0160
    _tk_restore_v0160()
    try:
        prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    finally:
        PRIOR.READY = read_launch
        DB_MOD_V0160._write_db = _write_db_v0160
        _tk_install_v0160()
    chk("⑧ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] %s_%s 自測 %d/%d · %s" % (_STEM, TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
