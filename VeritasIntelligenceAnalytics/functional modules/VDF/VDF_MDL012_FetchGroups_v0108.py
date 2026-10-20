#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [接線 2026-10-20] 本檔 = 工作站分支 workstation-20261020 的同號原文(main 沒有此版,不撞號)。工作站 v0106(自測鏈隔離活資料樞)不搬:
#   main v0106 已在前版鏈自測期間封倉(_SEAL_REPO_HUB),同一目的;本檔前版照 glob 取 main v0106。
# [接回 main 修正 2026-10-20 · U/I 實測] 手機 390:v0105 無條件寫 .fg{grid-template-columns:340px …},蓋掉 v0101 的 900px 一欄規則 →
#   左面板 340px、右側只剩 30px 一字一行。本版版面 CSS(在頁尾,層疊最後)補 @media (max-width:900px) 一欄 + 左面板不黏頂。自測 ⑧。
"""VDF_MDL012_FetchGroups v0108 — 薄尾:族群頁版面最佳化(字級套件 · 左面板摺疊 · 短欄不換行 · 燈欄第一 · 空值 — · 路徑縮檔名)

操作員(2026-10-12,工作站 via-groups-ui 跳出的頁看過):「字體大小有位階但畫面凌亂,要用工具最佳化」。
容器實看(headless 截圖 1600×2400):左面板一條到底約 2000px(輸入 → 15 個功能鍵 → 6 個收尾鍵 → Live log → 17 個頁鈕(與上方頁籤重複)→ 母系統 / 他系統連結);
  引擎表的短欄(最後跑 · 模式 · rc · 燈)被擠成逐字直排、檔名欄在字中間斷行;結果表燈欄在最後一欄;空格空白。
工具 = VDF 自己的字級套件與版面規則(VIA_UI_Template_SSOT 尾版 tokens / auto_layout;VDF_SystemManager v0153 起的 typekit_book / typekit_block /
  typekit_apply_text,R69 已套在 VDF 全景 · 健康 · UIEngine 頁)。本版把同一份套到族群頁,外加左面板摺疊與展現規則:
  ① 字級套件(四級字 · 兩種字重 · 一種主字體 · 短欄不換行 · 長欄限寬 · 寬表橫捲 · 頁面之後長出來的內容照樣吸附);套件缺席照實寫在頁上,其餘照做
  ② 左面板每節 <details>:① 輸入控制 · ② 功能 開;③ 收尾 · 備份 · 頁(與上方頁籤重複)· 回母系統 · 跳到其他系統 收(收著的節標示鈕數);Live log 擷取中才開
  ③ 展現規則(頁內一小段 JS,只動 DOM 不動資料,之後長出來的表照樣套):燈欄移到第一欄 · 空值印 — · 路徑縮成檔名(全路徑在 title)· 表頭不換行
正式路徑一字不動(run · usertest · 各動詞照 v0107);頁的 id / 功能鍵 / 頁籤一個不少(v0105 ③④⑤ · v0107 ⑦ 的檢查在鏈裡照過)。
只收 VCGC 呼叫;零網路;不碰 TA-Lib。交接案:vdf_fetch_groups_v0107 的標記在本版前版鏈裡照印(TAG_V0107 不蓋);新案 vdf_fetch_groups_v0108 釘本版 [計] 行。
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
    """統包唯一網路工具惰性載入;本檔零網路(連網全在 MDL008 子行程)。"""
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
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG_V0108 = f"VDF_MDL012_FetchGroups v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
SECTIONS_OPEN_V0108 = ("① 輸入控制", "② 功能")            # 其餘節收著(③ 收尾 · 頁 · 回母系統 · 跳到其他系統);Live log 擷取中才開


def _vnum_v0108(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _prior_path() -> Path:
    """前版 = 同家族比本檔小的最大版號(不釘名,避免 PINVER)。"""
    me = _vnum_v0108(__file__)
    hits = [p for p in HERE.glob("VDF_MDL012_FetchGroups_v*.py") if 0 <= _vnum_v0108(p) < me]
    return max(hits, key=_vnum_v0108)


PRIOR_PATH = _prior_path()
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0108", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


def _chain() -> list:
    mods, m = [], PRIOR
    while m is not None and m not in mods:
        mods.append(m)
        m = vars(m).get("PRIOR")
    return mods


def _owner(*names):
    """沿前版鏈找「這些名稱都定義在自己模組裡」的那一版。"""
    for m in _chain():
        if all(callable(vars(m).get(n)) and getattr(vars(m).get(n), "__module__", None) == m.__name__ for n in names):
            return m
    return None


V0107 = _owner("render_v0107", "inject_left_v0107", "usertest_static")   # 並行擷取 · USER-TEST 頁本體
V0101 = V0107.V0101 if V0107 is not None else None                        # 頁產生器本體(render 由本版換裝)
V0105 = V0107.V0105 if V0107 is not None else None                        # 左面板 · relayout · LayoutError
_RENDER_V0107 = vars(V0107)["render_v0107"] if V0107 is not None else None

for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


# ---------------------------------------------------------------- 工具:VDF 自己的字級套件(VDF_SystemManager 尾版)
_SM = {"mod": None, "path": None, "tried": False}


def typekit_source():
    """→ (module, path):VDF_SystemManager 尾版裡有 typekit_block / typekit_apply_text 的那一版(v0153 起);載不到回 (None, None),照實。"""
    if _SM["tried"]:
        return _SM["mod"], _SM["path"]
    _SM["tried"] = True
    for p in sorted(HERE.glob("VDF_SystemManager_v*.py"), key=_vnum_v0108, reverse=True):
        try:
            spec = importlib.util.spec_from_file_location("vdf_sm_for_mdl012_v0108", p)
            m = importlib.util.module_from_spec(spec)
            with contextlib.redirect_stdout(io.StringIO()):
                spec.loader.exec_module(m)
            if callable(getattr(m, "typekit_block", None)) and callable(getattr(m, "typekit_apply_text", None)) and callable(getattr(m, "typekit_book", None)):
                _SM.update(mod=m, path=p)
                return m, p
        except Exception:
            continue
    return None, None


def apply_typekit(page: str) -> tuple:
    """套字級套件 → (頁, 說明)。套件缺席:頁不動,說明寫缺席原因(不編)。"""
    m, p = typekit_source()
    if m is None:
        return page, "字級套件缺席:VDF_SystemManager 尾版沒有 typekit_block(v0153 起才有)"
    tk = m.typekit_book()
    page, how = m.typekit_apply_text(page, m.typekit_block(tk))
    return page, f"{tk.get('book') or '內建預設'} · {how} · 經 {p.name}" + (f" · {tk.get('why')}" if tk.get("why") else "")


# ---------------------------------------------------------------- 左面板摺疊 · 展現規則
_CSS_V0108 = """
.fg-left details.fg-sec{border:0;margin:0;padding:0;min-width:0}
.fg-left details.fg-sec>summary{cursor:pointer;list-style:none;margin:10px 0 4px;font-size:var(--via-t4,11px);letter-spacing:1px;color:var(--via-muted);text-transform:uppercase;user-select:none}
.fg-left details.fg-sec>summary::-webkit-details-marker{display:none}
.fg-left details.fg-sec>summary::before{content:"▸ ";opacity:.75}
.fg-left details.fg-sec[open]>summary::before{content:"▾ "}
.fg-left details.fg-sec>summary .cnt{float:right;opacity:.6;letter-spacing:0;text-transform:none}
.fg-left details.fg-sec>summary .st{float:right;opacity:.8;letter-spacing:0;text-transform:none;margin-left:6px}
.fg-left a,.fg-left button{padding:3px 8px;margin:1px 0;line-height:1.25}
.fg-left .lf{margin:2px 0 4px}
.fg-right th{white-space:nowrap}
.fg-right td.via-path{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:28ch}
.tabs{gap:3px}.tabs button{padding:3px 8px}
.via-layout-note{opacity:.6;font-size:var(--via-t4,11px);margin:0 0 6px}
@media (max-width:900px){.fg{grid-template-columns:1fr}.fg-left{position:static;max-height:none}}
"""

_JS_V0108 = r"""
(function () {
  var PATH_RX = /^[\w.\-]+(?:[\/\\][\w.\-]+)+\.(?:py|json|jsonl|duckdb|parquet|csv|html|txt|log)$/;
  function lampFirst(root) {
    root.querySelectorAll('table').forEach(function (t) {
      var hr = t.querySelector('tr'); if (!hr) return;
      var ths = Array.prototype.slice.call(hr.children);
      var li = -1; ths.forEach(function (th, i) { if (li < 0 && th.textContent.trim() === '燈') li = i; });
      if (li <= 0) return;
      t.querySelectorAll('tr').forEach(function (tr) { var c = tr.children[li]; if (c) tr.insertBefore(c, tr.firstChild); });
    });
  }
  function paths(root) {
    root.querySelectorAll('td').forEach(function (td) {
      if (td.children.length || td.classList.contains('via-path')) return;
      var s = td.textContent.trim();
      if (s.length > 24 && PATH_RX.test(s)) { td.title = s; td.textContent = s.split(/[\/\\]/).pop(); td.classList.add('via-path'); }
    });
  }
  function dash(root) {
    root.querySelectorAll('td').forEach(function (td) { if (!td.children.length && !td.textContent.trim()) td.textContent = '—'; });
  }
  var busy = false;
  function applyAll() {
    if (busy) return; busy = true;
    try { document.querySelectorAll('.pg').forEach(function (pg) { lampFirst(pg); paths(pg); dash(pg); }); } finally { busy = false; }
  }
  var t = 0;
  function schedule() { if (t) return; t = setTimeout(function () { t = 0; applyAll(); }, 30); }
  applyAll();
  var mo = new MutationObserver(function () { if (!busy) schedule(); });
  document.querySelectorAll('.pg').forEach(function (pg) { mo.observe(pg, {childList: true, subtree: true}); });
})();
"""


def fold_left_v0108(page: str, live_running: bool = False) -> str:
    """左面板每個 <h3> 節 → <details class="fg-sec">;① 輸入控制 · ② 功能 開,Live log 擷取中才開,其餘收(標鈕數)。id / 鈕 / 頁籤一個不動。"""
    m = re.search(r'<aside class="fg-left fg-left-v0105">(.*?)</aside>', page, re.S)
    if not m:
        raise V0105.LayoutError("找不到 v0105 左面板(fg-left-v0105)")
    inner = m.group(1)
    parts = re.split(r"(<h3>[^<]*</h3>)", inner)
    if len(parts) < 3:
        raise V0105.LayoutError("左面板沒有 <h3> 節")
    out = [parts[0]]
    for i in range(1, len(parts), 2):
        title = re.sub(r"</?h3>", "", parts[i])
        body = parts[i + 1] if i + 1 < len(parts) else ""
        is_open = title in SECTIONS_OPEN_V0108 or (title == "Live log" and live_running)
        n = len(re.findall(r"<(?:button|a)\b", body))
        extra = (f'<span class="cnt">{n}</span>' if n and not is_open else "") + ('<span class="st">擷取中</span>' if title == "Live log" and live_running else "")
        out.append(f'<details class="fg-sec"{" open" if is_open else ""}><summary>{title}{extra}</summary>{body}</details>')
    return page[:m.start(1)] + "".join(out) + page[m.end(1):]


def render_v0108(snap: dict, out: Path) -> str:
    page = _RENDER_V0107(snap, out)
    page, note = apply_typekit(page)
    page = fold_left_v0108(page, bool((snap.get("live") or {}).get("running")))
    page = page.replace(f'"page_tool": "{V0107.TAG_V0107}"', f'"page_tool": "{TAG_V0108}"', 1)      # 內嵌快照報本尾版(v0107 的 TAG 不蓋)
    tail = f'<style>{_CSS_V0108}</style><script>{_JS_V0108}</script><div class="via-layout-note" hidden data-via-layout="{TAG_V0108}">版面:{note}</div>'
    k = page.rfind("</body>")
    return page[:k] + tail + page[k:] if k >= 0 else page + tail


V0101.render = render_v0108                                    # build_page → 模組全域 render → 本版頁(ui · usertest 真路徑)

# ---------------------------------------------------------------- usertest 瀏覽器實測:探針讀法放寬(字級套件會給 <pre> 補 style)
_UT_RX_V0108 = re.compile(r'<pre[^>]*\bid="VIA_UT"[^>]*>(.*?)</pre>', re.S)
_USERTEST_BROWSER_V0107 = vars(V0107)["usertest_browser"] if V0107 is not None else None


def usertest_browser_v0108(page_path: Path, timeout: int = 120):
    """同 v0107,但讀回 <pre id="VIA_UT"> 時容許其他屬性(字級套件的頁內程式會給每個 <pre> 補 style="font-family:…",v0107 的精確比對會以為探針沒回)。"""
    import subprocess
    exe = V0107.find_browser()
    if exe is None:
        return None
    page = page_path.read_text(encoding="utf-8")
    k = page.rfind("</body>")
    harness = page_path.with_name(page_path.stem + "_usertest_harness.html")
    harness.write_text((page[:k] + f"<script>{V0107._HARNESS_JS}</script>" + page[k:]) if k >= 0 else page + f"<script>{V0107._HARNESS_JS}</script>", encoding="utf-8")
    try:
        with tempfile.TemporaryDirectory() as prof:
            cmd = [str(exe), "--headless", "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage", "--allow-file-access-from-files",
                   f"--user-data-dir={prof}", "--virtual-time-budget=8000", "--dump-dom", harness.resolve().as_uri()]
            try:
                pr = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
                                    errors="replace", timeout=timeout)
            except Exception as exc:
                return {"exe": str(exe), "error": f"{type(exc).__name__}: {exc}"}
    finally:
        with contextlib.suppress(OSError):
            harness.unlink()
    m = _UT_RX_V0108.search(pr.stdout)
    if not m:
        return {"exe": str(exe), "error": f"瀏覽器沒回 VIA_UT(rc {pr.returncode});stderr 尾:{pr.stderr[-240:].strip()}"}
    try:
        import html as _html
        data = json.loads(_html.unescape(m.group(1)))
    except ValueError as exc:
        return {"exe": str(exe), "error": f"VIA_UT 解析失敗 {exc}"}
    data["exe"] = str(exe)
    return data


if V0107 is not None:
    V0107.usertest_browser = usertest_browser_v0108            # v0107 cmd_usertest 讀模組全域 → 走本版讀法


# ---------------------------------------------------------------- 自測 · 入口
def selftest() -> int:
    import argparse
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    print(f"=== {TAG_V0108} · 薄尾自測(族群頁版面最佳化)===")
    chk("① 沿鏈找到 v0107(render_v0107 · usertest)· v0101 · v0105 本體;render 已換上本版;TAG_V0107 / 鏈 TAG 不蓋(前版案標記照印)",
        V0107 is not None and "v0107" in V0107.__name__ and V0101 is not None and V0105 is not None and V0101.render is render_v0108
        and V0107.TAG_V0107.endswith("v0107") and PRIOR.TAG.endswith("v0106"), (getattr(V0107, "__name__", None), getattr(PRIOR, "TAG", None)))
    sm, smp = typekit_source()
    blk = sm.typekit_block(sm.typekit_book()) if sm is not None else ""
    once, how1 = sm.typekit_apply_text("<html><head></head><body>x</body></html>", blk) if sm is not None else ("", "")
    twice, how2 = sm.typekit_apply_text(once, blk) if sm is not None else ("", "")
    chk("② 字級套件來自 VDF_SystemManager 尾版(typekit_block · 冊 VIA_UI_Template_SSOT);套兩次不重複(inserted → same)",
        sm is not None and "<!--via-typekit:begin" in blk and how1 == "inserted" and how2 == "same" and twice.count("via-typekit:begin") == 1,
        (getattr(smp, "name", None), how1, how2))
    fake = ('<html><body><aside class="fg-left fg-left-v0105"><h3>① 輸入控制</h3><input id="asof"><h3>② 功能</h3><button data-fn="run">跑</button>'
            '<h3>③ 收尾 · 備份</h3><button data-fn="verify">驗</button><button data-fn="closeout">收</button><h3>Live log</h3><pre id="loglines"></pre>'
            '<h3>頁</h3><button data-pg="pg-1">1</button><a href="x">n</a></aside><div class="fg-right"></div></body></html>')
    f_idle, f_live = fold_left_v0108(fake, False), fold_left_v0108(fake, True)
    chk("③ 摺疊(替身):5 節 → 5 個 <details>;① ② 開、其餘收且標鈕數(收尾 2 · 頁 2);Live log 擷取中才開並標「擷取中」;id / 鈕一個不少",
        f_idle.count('<details class="fg-sec"') == 5 and f_idle.count('<details class="fg-sec" open>') == 2
        and '<summary>③ 收尾 · 備份<span class="cnt">2</span></summary>' in f_idle and '<summary>頁<span class="cnt">2</span></summary>' in f_idle
        and '<summary>Live log</summary>' in f_idle and f_live.count('<details class="fg-sec" open>') == 3 and '擷取中' in f_live
        and all(x in f_idle for x in ('id="asof"', 'data-fn="run"', 'data-fn="verify"', 'data-pg="pg-1"', 'id="loglines"')) and "<h3>" not in f_idle,
        f_idle[:400])
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "VDF_FetchGroups_selftest.html"
        home = V0107.V0100._ctx(argparse.Namespace(home=None))[-1]
        V0101.build_page(home, out)                              # ui 真路徑(build_page → 模組全域 render = 本版)
        page = out.read_text(encoding="utf-8")
        base = _RENDER_V0107(V0101.gather(home, None), out)      # 同一份快照照 v0107 產的頁(對照:鈕 / 頁籤 / id 集合要一樣)
    fns = lambda h: sorted(set(re.findall(r'data-fn="([^"]+)"', h)))
    pgs = lambda h: sorted(set(re.findall(r'data-pg="([^"]+)"', h)))
    aside = re.search(r'<aside class="fg-left fg-left-v0105">.*?</aside>', page, re.S)
    left = aside.group(0) if aside else ""
    opens = re.findall(r'<details class="fg-sec" open><summary>([^<]*)', left)
    m = re.search(r'<script type="application/json" id="SNAPSHOT">(.*?)</script>', page, re.S)
    try:
        emb = json.loads(m.group(1).replace("<\\/", "</")) if m else {}
    except ValueError:
        emb = {}
    want_ids = ("asof", "mode", "home", "gsel", "mgroup", "mvals", "cat", "catdate", "rfapply", "jobs", "cmd", "eng", "res")
    st_rows = V0107.usertest_static(page)
    chk("④ 真頁:字級套件在(一次)· 左面板 7 節摺疊且只開 ① ②(閒置)· 鈕 / 頁籤集合與 v0107 相同 · 輸入 id 唯一 · 展現規則 JS 在 · 快照頁工具 = 本版 · 靜態驗全綠",
        page.count("via-typekit:begin") == 1 and left.count('<details class="fg-sec"') == 7 and opens == ["① 輸入控制", "② 功能"]
        and fns(page) == fns(base) and pgs(page) == pgs(base) and all(page.count(f'id="{x}"') == 1 for x in want_ids)
        and "MutationObserver" in page and "lampFirst" in page and emb.get("page_tool") == TAG_V0108 and not [r for r in st_rows if r["lamp"] == "RED"],
        (page.count("via-typekit:begin"), left.count('<details class="fg-sec"'), opens, fns(page) == fns(base), pgs(page) == pgs(base), emb.get("page_tool"),
         [r for r in st_rows if r["lamp"] == "RED"]))
    chk("⑥ usertest 探針讀法放寬:<pre id=\"VIA_UT\"> 有沒有套件補的 style 都讀得到;v0107 的讀法已換成本版",
        _UT_RX_V0108.search('<pre id="VIA_UT">{"a":1}</pre>') is not None and _UT_RX_V0108.search('<pre id="VIA_UT" style="font-family: var(--via-mono);">{"a":1}</pre>') is not None
        and _UT_RX_V0108.search('<pre id="OTHER">x</pre>') is None and V0107.usertest_browser is usertest_browser_v0108)
    narrow = "@media (max-width:900px){.fg{grid-template-columns:1fr}"
    chk("⑧ 窄版一欄:頁尾版面 CSS 有 900px 一欄規則,而且排在 v0105 的 340px 規則之後(層疊勝出)",
        narrow in page and page.rfind(narrow) > page.find(".fg{grid-template-columns:340px"), (narrow in page,))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 加速器橋 · 網路橋在;前版不動(薄尾);不碰 TA-Lib;頁內程式只動 DOM(無 fetch / XMLHttpRequest / eval)",
        "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src and PRIOR_PATH.is_file() and "import " + "talib" not in src
        and all(x not in _JS_V0108 for x in ("fetch(", "XMLHttpRequest", "eval(")))
    good = all(ok)
    if not good:
        print(f"  [計] {TAG_V0108} 本版 {sum(ok)}/{len(ok)} · FAIL")
        return 1
    V0101.render = _RENDER_V0107                                 # 前版鏈驗的是前版版面(v0107 ① 要 render 是它的)→ 跑鏈期間換回,跑完換上本版
    try:
        rc = PRIOR.selftest()
    finally:
        V0101.render = render_v0108
    chk("⑦ 前版鏈自測(v0107 → … → v0100)rc 0;跑完 render 已換回本版", rc == 0 and V0101.render is render_v0108, f"rc {rc}")
    good = all(ok)
    print(f"  [計] {TAG_V0108} 本版 {sum(ok)}/{len(ok)} · 前版鏈 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
