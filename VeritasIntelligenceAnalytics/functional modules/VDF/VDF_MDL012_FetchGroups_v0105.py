#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL012_FetchGroups v0105 — 薄尾:ui 左面板 = 全部輸入控制 · 右面板多頁照舊 · 收尾 = 打包備份 VDF / VCGC + 上傳

操作員 2026-10-05:「現在VDF以算收尾階段自己可獨立運作? 建立左面滿輸入控制  有面板多頁顯示  收尾就上傳備份VDF VCGC」。
  · 左面板(由上而下):① 輸入控制(as-of · 模式 · 輸出根 · 族群勾選〔全選 / 清除〕· 成員增減 · 起始日按大類 · 補擷取乾跑 / 真跑)
                      ② 功能(v0101 原十鈕 + 起始日 · 補擷取)③ 收尾 · 備份 ④ Live log ⑤ 頁 ⑥ 回母系統 / 跳到其他系統。
    右面板:頁 ① 改成「運作指令 · 引擎 · 結果」(輸入卡搬到左邊,元素 id 不變,v0101 的頁內程式照用);各族群頁 · 參考頁照舊。
  · 收尾 · 備份(本頁只產生可貼上的指令,本頁與產生器都不執行):
      打包 VDF  = via-vcgc run CGC_MDL256_SubsystemBundle build via_01_vdf --target(冊 VIA_SubsystemBundle_SSOT 尾版;寫到冊上的操作員目標夾)
      打包 VCGC = 同上 via_00_vcgc;驗包 = CGC_MDL256 verify <目標夾>(只算 sha256)
      VCGC 收尾(乾跑)= via-vcgc closeout;收尾上傳 = via-vcgc closeout --apply --push(交接閘 → 重測 → registry-sync → 編號 → SDD → checkpoint → push)
      一鍵收尾備份 = 收尾上傳 → 打包 VDF → 打包 VCGC → 驗兩包(依序,前一步紅就停)。
    推送要明打 --push;同意閘照舊是操作員的手(live / 補擷取 --apply 才要)。
  · 做法:換掉 v0101 模組上的 render(cmd_ui / build_page / --watch 讀的是那個模組的全域);快照多帶 VCGC 尾版名 · 打包冊的包名與目標夾。
其餘動詞全照 v0104 / v0103 / v0102 / v0101 / v0100。
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
# ===== [VIA:NET-BRIDGE:END] =====

import argparse
import html
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _prior_path() -> Path:
    """前版 = 同家族比本檔小的最大版號(不釘名,避免 PINVER)。"""
    me = int(Path(__file__).stem.rsplit("_v", 1)[1])
    hits = [p for p in HERE.glob("VDF_MDL012_FetchGroups_v*.py") if re.search(r"_v\d+$", p.stem) and int(p.stem.rsplit("_v", 1)[1]) < me]
    return max(hits, key=lambda p: int(p.stem.rsplit("_v", 1)[1]))


PRIOR_PATH = _prior_path()
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0105", PRIOR_PATH)
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


def _page_owner():
    """沿前版鏈找到自己定義頁產生器(render · _JS)的那個模組(v0101)。"""
    for m in _chain():          # 各版會把前版名稱抄進自己的全域 → 要找「函式定義在這個模組」的那一版
        fn = vars(m).get("render")
        if callable(fn) and getattr(fn, "__module__", None) == m.__name__ and "_JS" in vars(m):
            return m
    return None


V0101 = _page_owner()
TAG = f"VDF_MDL012_FetchGroups v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
for _m in _chain():
    _m.TAG = TAG
VIA = V0101.VIA
REG = V0101.REG
_RENDER_V0101 = vars(V0101)["render"]

for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)

FUNCS_V0105 = [("start", "起始日(按大類)", "按左面板「起始日」:給日期 = start --category X --set D --apply;空白 = 列各大類現況"),
               ("refill", "補擷取(無資料族群)", "FRED → 政府單位 → AkShare 分層;勾「真跑」才 --apply(要雙閘)")]
BACKUP_FUNCS = [("bundle_vdf", "打包備份 VDF", "via-vcgc run CGC_MDL256_SubsystemBundle build via_01_vdf --target"),
                ("bundle_vcgc", "打包備份 VCGC", "via-vcgc run CGC_MDL256_SubsystemBundle build via_00_vcgc --target"),
                ("verify", "驗兩包(sha256)", "CGC_MDL256 verify <目標夾>(只讀,不需 VCGC)"),
                ("closeout", "VCGC 收尾(乾跑)", "via-vcgc closeout:不寫冊 · 不提交 · 不推"),
                ("closeout_push", "收尾上傳 GitHub", "via-vcgc closeout --apply --push"),
                ("finish_all", "一鍵收尾備份", "收尾上傳 → 打包 VDF → 打包 VCGC → 驗兩包(前一步紅就停)")]


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", p.stem)
    return int(m.group(1)) if m else -1


def _latest(folder: Path, pattern: str):
    hits = [p for p in folder.glob(pattern) if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def backup_info() -> dict:
    """收尾 · 備份要的名字:VCGC 尾版 · 打包工具尾版 · 打包冊尾版的包名 / 目標夾 / 檔數(只讀)。"""
    vc = _latest(REG, "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py")
    bt = _latest(REG, "CGC_MDL256_SubsystemBundle_v*.py")
    bk = _latest(REG, "VIA_SubsystemBundle_SSOT_v*.json")
    info = {"vcgc_tail": vc.name if vc else None, "bundle_tool": bt.name if bt else None,
            "bundle_book": bk.name if bk else None, "bundles": [], "note": ""}
    if bk:
        try:
            book = json.loads(bk.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            info["note"] = f"打包冊讀不到:{type(exc).__name__}"
            return info
        for name, spec in (book.get("bundles") or {}).items():
            info["bundles"].append({"name": name, "target": spec.get("target", ""), "files": len(spec.get("files") or [])})
    return info


_CSS_V0105 = """
.fg{grid-template-columns:340px minmax(0,1fr)}
.fg-left{gap:2px;max-height:calc(100vh - 120px);overflow:auto;position:sticky;top:0}
.fg-left .lf{margin:0 0 7px}
.fg-left .lb{display:flex;justify-content:space-between;align-items:center;color:var(--via-muted);font-size:11px;margin:0 0 2px;white-space:normal}
.fg-left input:not([type=checkbox]),.fg-left select{width:100%;box-sizing:border-box;margin:1px 0}
.fg-left .gsel-list{max-height:210px;overflow:auto;border:1px solid var(--via-rule);border-radius:5px;padding:3px 6px}
.fg-left .gsel-list label{display:block;margin:1px 0;white-space:normal}
.fg-left .mini button{display:inline-block;width:auto;margin:0 0 0 4px;padding:0 6px;font-size:11px}
.fg-left button.bk{border-color:rgba(224,179,65,.55)}
.fg-left button.bk.push{border-color:rgba(224,108,96,.6)}
@media (max-width:900px){.fg-left{position:static;max-height:none}}
"""

_JS_V0105 = r"""
(function () {
  const B = S.backup || {};
  const VC = 'supportive modules/registry/' + (B.vcgc_tail || 'CGC_MDL149_VeritasCentralGovernanceConsole_v0190.py');
  const BT = 'supportive modules/registry/' + (B.bundle_tool || 'CGC_MDL256_SubsystemBundle_v0101.py');
  const tgt = n => ((B.bundles || []).find(b => b.name === n) || {}).target || ('<' + n + ' 目標夾>');
  const win = p => '.\\' + p.replace(/\//g, '\\');
  const CATS = {}; (S.categories || []).forEach(c => { CATS[c.id] = c; });
  const prevCmdOf = cmdOf;
  const mdl = a => `VIA_FROM_VCGC=YES python3 "${PY}" ${a}\n$env:VIA_FROM_VCGC='YES'; python "${win(PY)}" ${a}`;
  const vcgc = a => `VIA_FROM_VCGC=YES python3 "${VC}" ${a}\n$env:VIA_FROM_VCGC='YES'; python "${win(VC)}" ${a}`;
  const GATE = "\n# 真跑先在本視窗開雙閘(操作員的手,頁與產生器永不代設):\n# bash: export VIA_NET_CONSENT=YES VIA_SCRAPE_CONSENT=YES\n# PS:   $env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='YES'";
  cmdOf = function (verb) {
    const gs = $$('.gsel:checked').map(x => x.value).join(',');
    const asof = $('#asof').value || 'latest', home = $('#home').value;
    const H = home ? ` --home "${home}"` : '';
    if (verb === 'start') {
      const cat = $('#cat').value, d = ($('#catdate').value || '').trim();
      return '# 起始日(只能按大類改)\n' + mdl(d ? `start --category ${cat} --set ${d} --apply` : 'start');
    }
    if (verb === 'refill') {
      const ap = $('#rfapply').checked;
      return '# 補擷取' + (ap ? '(真跑)' : '(乾跑 = 只列計畫)') + '\n' + mdl(`refill --groups ${gs || 'ALL'} --as-of ${asof}` + H + (ap ? ' --apply' : '')) + (ap ? GATE : '');
    }
    if (verb === 'bundle_vdf') return '# 打包備份 VDF → ' + tgt('via_01_vdf') + '\n' + vcgc('run CGC_MDL256_SubsystemBundle build via_01_vdf --target');
    if (verb === 'bundle_vcgc') return '# 打包備份 VCGC → ' + tgt('via_00_vcgc') + '\n' + vcgc('run CGC_MDL256_SubsystemBundle build via_00_vcgc --target');
    if (verb === 'verify') return '# 驗兩包(只算 sha256,不需 VCGC)\n' + ['via_01_vdf', 'via_00_vcgc'].map(n => `python "${win(BT)}" verify "${tgt(n)}"`).join('\n');
    if (verb === 'closeout') return '# VCGC 收尾乾跑(不寫冊 · 不提交 · 不推)\n' + vcgc('closeout');
    if (verb === 'closeout_push') return '# 收尾上傳 GitHub(寫冊 · 提交 · 推 origin;不強推)\n' + vcgc('closeout --apply --push');
    if (verb === 'finish_all') {
      const ps = p => `python "${win(VC)}" ${p}; if ($LASTEXITCODE -ne 0) { Write-Host '紅:${p.split(' ')[0]} 停' -ForegroundColor Red; return }`;
      return '# 一鍵收尾備份(PowerShell · 站在 VIA 根;整段包在 & { } 裡,前一步紅就停,後面不跑)\n& {\n$env:VIA_FROM_VCGC=\'YES\'\n'
        + [ps('closeout --apply --push'), ps('run CGC_MDL256_SubsystemBundle build via_01_vdf --target'), ps('run CGC_MDL256_SubsystemBundle build via_00_vcgc --target')].join('\n')
        + '\n' + ['via_01_vdf', 'via_00_vcgc'].map(n => `python "${win(BT)}" verify "${tgt(n)}"`).join('\n') + '\n}';
    }
    return prevCmdOf(verb);
  };
  function catNow() {
    const c = CATS[$('#cat').value];
    $('#catnow').textContent = c ? `現在 ${c.start || '?'}(預設 ${c.default_start || '?'})· 族群 ${(c.groups || []).join(',')}` : '';
  }
  document.addEventListener('DOMContentLoaded', () => {
    const re = () => { if (st.verb) $('#cmd').textContent = cmdOf(st.verb); };
    $$('#cat,#catdate,#rfapply').forEach(x => { x.addEventListener('input', re); x.addEventListener('change', re); });
    $('#cat').addEventListener('change', catNow); catNow();
    const setAll = on => { $$('.gsel').forEach(x => { x.checked = on; }); st.groups = $$('.gsel:checked').map(x => x.value); save(); engines(); re(); };
    $('#gall').addEventListener('click', () => setAll(true));
    $('#gnone').addEventListener('click', () => setAll(false));
    re();
  });
})();
"""


def _btn(fn: str, label: str, tip: str, cls: str = "") -> str:
    klass = f' class="{cls}"' if cls else ""
    return f'<button data-fn="{fn}" title="{html.escape(tip)}"{klass}>{html.escape(label)}</button>'


def left_panel(snap: dict, out: Path, pages: list) -> str:
    """左面板:輸入控制在最上(元素 id 與 v0101 頁內程式相同)→ 功能 → 收尾 · 備份 → Live log → 頁 → 導覽。"""
    cats = snap.get("categories") or []
    cat_opts = "".join(f'<option value="{html.escape(c["id"])}">{html.escape(c.get("zh") or c["id"])}({html.escape(c["id"])})</option>' for c in cats) \
        or '<option value="">(冊上沒有大類)</option>'
    bk = snap.get("backup") or {}
    pk = " · ".join(f'{b["name"]} {b["files"]} 檔' for b in bk.get("bundles", [])) or "(打包冊沒有包)"
    return ('<aside class="fg-left fg-left-v0105">'
            + "<h3>① 輸入控制</h3>"
            + f'<div class="lf"><span class="lb">as-of(全族群同一天)</span><input id="asof" placeholder="latest 或 YYYY-MM-DD">'
              f'<div class="mut">設定 {html.escape(str(snap.get("asof_setting")))} → {html.escape(str(snap.get("as_of")))}</div></div>'
            + '<div class="lf"><span class="lb">模式</span><select id="mode"><option>live</option><option>fixture</option><option>block</option></select></div>'
            + f'<div class="lf"><span class="lb">輸出根</span><input id="home" placeholder="(預設 {html.escape(str(snap.get("home")))})"></div>'
            + '<div class="lf"><span class="lb">族群(🔒 = 固定全部,不給增減)<span class="mini"><button type="button" id="gall">全選</button>'
              '<button type="button" id="gnone">清除</button></span></span><div id="gsel" class="gsel-list"></div></div>'
            + '<div class="lf"><span class="lb">成員增減</span><select id="mgroup"></select><input id="mvals" placeholder="代號或函式名,空白分隔"></div>'
            + f'<div class="lf"><span class="lb">起始日(只能按大類改)</span><select id="cat">{cat_opts}</select>'
              '<input id="catdate" placeholder="YYYY-MM-DD · default = 回預設 · 空白 = 只看"><div class="mut" id="catnow"></div></div>'
            + '<div class="lf"><span class="lb">補擷取(無資料族群)</span><label><input type="checkbox" id="rfapply"> 真跑(--apply;要雙閘)</label></div>'
            + "<h3>② 功能</h3>" + "".join(_btn(v, z, d) for v, z, d in list(V0101.FUNCS) + FUNCS_V0105)
            + "<h3>③ 收尾 · 備份</h3>"
            + "".join(_btn(v, z, d, "bk push" if v in ("closeout_push", "finish_all") else "bk") for v, z, d in BACKUP_FUNCS)
            + f'<div class="mut">打包冊 {html.escape(str(bk.get("bundle_book")))} · {html.escape(pk)}'
              + (f' · {html.escape(bk["note"])}' if bk.get("note") else "") + '</div>'
            + '<h3>Live log</h3><div id="livest" class="mut"></div><label class="mut"><input type="checkbox" id="autoreload"> 擷取中自動重載</label>'
            + '<pre id="loglines" class="log"></pre>'
            + f'<div class="mut">日誌 {html.escape(str((snap.get("live") or {}).get("newest") or "—"))} · 頁 {html.escape(str(snap.get("built")))}</div>'
            + "<h3>頁</h3>" + "".join(f'<button data-pg="{pid}">{html.escape(t)}</button>' for pid, t in pages)
            + V0101._nav_links(out) + "</aside>")


class LayoutError(RuntimeError):
    pass


_ASIDE = re.compile(r'<aside class="fg-left">.*?</aside>', re.S)
_INPUT_CARD = '<div class="card"><h2>輸入</h2>'


def relayout(page: str, snap: dict, out: Path) -> str:
    """v0101 頁 → 左面板換成輸入控制版;頁 ① 拿掉輸入卡(同 id 只留左邊一份);補樣式與指令。"""
    if len(_ASIDE.findall(page)) != 1:
        raise LayoutError("v0101 頁的左面板不是剛好一塊")
    i = page.find(_INPUT_CARD)
    j = page.find('<div class="grid2">', i)
    if i < 0 or j < 0:
        raise LayoutError("頁 ① 找不到輸入卡")
    page = page[:i] + page[j:]
    pages = re.findall(r'<button data-pg="(pg-[^"]+)">([^<]*)</button>', page.split('<div class="tabs">', 1)[1].split("</div>", 1)[0])
    pages = [(pid, "① 運作 · 引擎 · 結果(輸入在左面板)" if pid == "pg-1" else html.unescape(t)) for pid, t in pages]
    page = _ASIDE.sub(lambda _m: left_panel(snap, out, pages), page, count=1)
    page = page.replace('<div class="fg">', f'<style>{_CSS_V0105}</style><div class="fg">', 1)
    k = page.rfind("</body>")
    tail_js = f"<script>{_JS_V0105}</script>"
    page = page[:k] + tail_js + page[k:] if k >= 0 else page + tail_js
    page = page.replace(">① 輸入 · 引擎 · 運作 · 結果<", ">① 運作 · 引擎 · 結果(輸入在左面板)<")
    page = page.replace("運作(左面板按功能 → 這裡出可貼上的指令;本頁不執行)", "運作指令(左面板輸入 + 功能 / 收尾鈕 → 這裡出可貼上的指令;本頁不執行)", 1)
    return page


def render_v0105(snap: dict, out: Path) -> str:
    snap = dict(snap)
    snap["backup"] = backup_info()
    snap["page_tool"] = TAG
    return relayout(_RENDER_V0101(snap, out), snap, out)


V0101.render = render_v0105


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 薄尾自測(左面板輸入控制 · 收尾備份)===")
    chk("① 頁產生器正主(函式定義所在 = v0101)找到並換上 render_v0105", V0101 is not None and "v0101" in V0101.__name__
        and vars(V0101).get("render") is render_v0105, getattr(V0101, "__name__", None))
    bk = backup_info()
    names = {b["name"] for b in bk["bundles"]}
    chk("② 收尾要的名字都讀得到:VCGC 尾版 · 打包工具 · 冊上 via_01_vdf + via_00_vcgc",
        bk["vcgc_tail"] and bk["bundle_tool"] and {"via_01_vdf", "via_00_vcgc"} <= names, (bk["vcgc_tail"], bk["bundle_tool"], sorted(names)))
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "VDF_FetchGroups_selftest.html"
        home = V0101.PRIOR._ctx(argparse.Namespace(home=None))[-1]
        V0101.build_page(home, out)              # 走 ui 真路徑(build_page → 模組全域 render),不直接呼叫本版函式
        page = out.read_text(encoding="utf-8")
    aside = re.search(r'<aside class="fg-left fg-left-v0105">.*?</aside>', page, re.S)
    left = aside.group(0) if aside else ""
    want_ids = ("asof", "mode", "home", "gsel", "mgroup", "mvals", "cat", "catdate", "rfapply")
    chk("③ 輸入元素全在左面板", left and all(f'id="{x}"' in left for x in want_ids), [x for x in want_ids if f'id="{x}"' not in left])
    chk("④ 同一 id 全頁只出現一次(右邊輸入卡已拿掉)", all(page.count(f'id="{x}"') == 1 for x in want_ids) and _INPUT_CARD not in page)
    fns = [v for v, _, _ in BACKUP_FUNCS] + [v for v, _, _ in FUNCS_V0105]
    chk("⑤ 收尾 · 備份與新功能鈕都在左面板", all(f'data-fn="{v}"' in left for v in fns))
    chk("⑥ 右面板多頁照舊(頁籤 ≥ 3 · 頁 ① 運作 / 引擎 / 結果)", page.count('class="pg"') >= 3 and 'id="cmd"' in page and 'id="eng"' in page and 'id="res"' in page)
    m = re.search(r'<script type="application/json" id="SNAPSHOT">(.*?)</script>', page, re.S)
    try:
        emb = json.loads(m.group(1).replace("<\\/", "</")) if m else {}
    except ValueError:
        emb = {}
    chk("⑦ 內嵌快照帶收尾名字(VCGC 尾版 · 打包包名)", (emb.get("backup") or {}).get("vcgc_tail") == bk["vcgc_tail"] and emb.get("page_tool") == TAG)
    chk("⑧ 推送只在明打 --push;頁不執行任何指令", "closeout --apply --push" in _JS_V0105 and "fetch(" not in _JS_V0105 and "XMLHttpRequest" not in _JS_V0105)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 加速器橋 · 網路橋在;前版不動(薄尾)", "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src and PRIOR_PATH.is_file())
    good = all(ok)
    print(f"  [計] {TAG} 薄尾 {sum(ok)}/{len(ok)} · {'PASS' if good else 'FAIL'}")
    if not good:
        return 1
    V0101.render = _RENDER_V0101            # 前版自測驗的是前版版面 → 跑前版鏈期間換回原 render,跑完再換上本版
    try:
        rc = PRIOR.selftest()
    finally:
        V0101.render = render_v0105
    if rc != 0:
        print(f"  [黃] {TAG} 本版 {len(ok)}/{len(ok)} 過 · 前版鏈自測 rc {rc}(前版單獨跑也同樣 FAIL,非本版造成;照實回 2,不算綠)")
        return 2
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
