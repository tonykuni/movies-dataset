#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# v0102→v0103(側線 2026-09-21 c):自測 ⑤ 自己寫著「缺=誠實」卻把關鍵庫不足 5 個判成 FAIL——改成 [ABSENT] rc3(四態律:缺件≠壞掉),
#   點名缺哪幾個;套件齊時九檢照跑一字不動。
"""
CGC_MDL088_SystemTestPages v0104(批701:接上批672 的矩陣規格) — 系統測試結果分頁 UI(批163;via-syspages)
====================================================================
v0103→v0104(批701 操作員令「MULTI-TAB · 字小一點更專業 · DETAILED MATRIX SUMMARY REPORT BY RICH LIB」):
  盤點先做(零 Hydra),量到的是——**這三件事樹上都已經有了,缺的是一條接線**:
    批672 CGC_MDL173_MatrixReportSpec:docstring 逐字寫著同一句原令「以後跑完都要生成矩陣式
      報告 BY RICH,字小,優化矩陣排版規格」;字級 10.5px、SIMPLE_HEAD、六態色、MD/JSON/複製三鈕全在它手上。
    批163 本檔:五系統分頁(tab)UI,資料走 battery×GRID 存證 join,零重測。
    批267 CGC_MDL110:三軌 RYG 矩陣。
  而量出來的缺口很具體:**本檔引用 MDL173 的次數 = 0、引用 rich 的次數 = 0**。
  MDL173 是有人用的(Grid v0433/0448/0449 · MDL174 · MDL175),唯獨這張「測試結果分頁」沒接上——
  跟批698 同一個形狀:引擎做出來了、規格立好了,沒掛在一起,對操作員而言就等於不存在(LL359)。
  本版做的就是那條接線:
    ① 矩陣與頁殼改由 MDL173 供給(page_html + html_table)——**一份 CSS,不長第三份**。
       MDL173 的 docstring 自己說了:「四支落頁引擎各帶一份 CSS…規格散在四處就不是規格」。
    ② tab 那一層 MDL173 沒有(css() 裡沒有 .tab),由本檔補;但字級與顏色一律讀 SPEC,
       不自己寫死視覺值——補的是版面不是規格。
    ③ MDL173 缺席=誠實退回 MDL089 原路(v0103 那條),並印出走了哪一條。缺件≠壞掉。
    ④ 系統列序改成操作員指定的三家在前(VCGC · VDF · VRN),其餘照列不刪(只增不減)。
    ⑤ `--open` 跑完自動開頁(操作員令「測試完自動跳出」);零彈窗律照舊,頁上不長 UI。
操作員令:UI 基本功能=版面與系統連動;每系統一頁測試結果(上到下
多指標),顯示引擎/庫×環境×紅黃綠三色現況;五系統(VIA Supportive
Toolkits/VIA Central Governance/VDF/VAP/VRN)**同一測試模板**;
版面未定前不雕視覺——字小、專業、自動化。
機制(零重測=連動存證):
  站表=grid 尾版 battery()(114 站含 path)× 最新 GRID_*.json 實跑
  存證(name join)→按引擎路徑自動歸屬五系統(+OTHER 附錄=
  GroupIndex 等 functional 未列系統,誠實不塞併)
  顏色:綠=OK/黃=SKIP(環境缺件誠實)/紅=FAIL
  環境列=python/平台+關鍵庫版本實測(importlib.metadata;缺=誠實)
  --fresh=重跑 grid 後再產頁;預設=讀最新存證(秒級)
產出:ui_support/VIA_UI_SystemTestPages_v0100.html(單檔分頁 tab)
用法:via-syspages run [--fresh] [--open] | --status | --selftest
v0100→v0101(批166):切換消費 CGC_MDL089 原始模板正主——CSS/三態
  色碼/六槽 section 全由 MDL089+token 冊(VIA_UI_TemplateSSOT)供給,
  本引擎內零寫死視覺值;版面定案後改 token 冊即全站換裝,不動引擎。
  資料層(battery×GRID 存證 join/歸屬判準/環境收割)零變更。
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
import platform
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
UI_OUT = VIA / "supportive modules" / "ui_support" / "VIA_UI_SystemTestPages_v0100.html"
GRID_RUNS = VIA / "VIA_Reports" / "selftest_runs"

# 批701:操作員指定「只要完成 VCGC / VDF / VRN」→ 這三家排前面。
#   其餘**照列不刪**(只增不減):刪掉等於把它們的紅燈藏起來,而藏起來的紅燈跟假綠一樣傷。
SYSTEMS = [  # (key, 顯名;順序=操作員列序)
    ("CGC", "VCGC 中央治理"),
    ("VDF", "VDF 資料工廠"),
    ("VRN", "VRN 報告智能"),
    ("SUP", "VIA Supportive Toolkits"),
    ("VAP", "VAP 自動繪圖"),
    ("OTHER", "其他功能系統(附錄)"),
]
FOCUS = ("CGC", "VDF", "VRN")   # 操作員指定的三家;只影響列序與 KPI,不影響誰被收錄
KEY_LIBS = ("pandas", "numpy", "duckdb", "scikit-learn", "matplotlib",
            "jieba", "opencc-python-reimplemented", "requests", "pyarrow")
_CGC_RX = re.compile(r"CGC_MDL|Central|central|mother|autorun|command_center|"
                     r"governance|ssot|selftest_grid|conflict_guard", re.I)


def classify(path_str: str) -> str:
    """站→系統歸屬(路徑判準;誠實 OTHER 不塞併)"""
    p = (path_str or "").replace("\\", "/")  # 批349:Windows 反斜線路徑正規化(工作站實錄 VDF/VAP/VRN 全歸 OTHER)
    if "functional modules/VRN" in p:
        return "VRN"
    if "functional modules/VDF" in p:
        return "VDF"
    if "functional modules/VAP" in p:
        return "VAP"
    if "supportive modules" in p:
        return "CGC" if _CGC_RX.search(Path(p).stem or "") else "SUP"
    if p == "PYCODE":
        return "OTHER"
    return "OTHER"


def _grid_module():
    hits = sorted(HERE.glob("CGC_MDL064_SelftestGrid_v*.py"))
    spec = importlib.util.spec_from_file_location("via_grid_dyn88", hits[-1])
    m = importlib.util.module_from_spec(spec)
    sys.modules["via_grid_dyn88"] = m
    spec.loader.exec_module(m)
    return m, hits[-1].name


def _latest_grid_json() -> tuple[Path | None, list]:
    hits = sorted(GRID_RUNS.glob("GRID_*.json"))
    if not hits:
        return None, []
    d = json.loads(hits[-1].read_text(encoding="utf-8"))
    items = d if isinstance(d, list) else d.get("stations") or d.get("results") or []
    return hits[-1], items


def assemble() -> dict:
    """battery(path)×GRID 存證(state)name join→六區歸屬"""
    gm, grid_name = _grid_module()
    battery = gm.battery(fast=False)
    src, items = _latest_grid_json()
    state_by = {i["name"]: i for i in items}
    pages = {k: [] for k, _ in SYSTEMS}
    for b in battery:
        st = state_by.get(b["name"], {})
        pages[classify(str(b.get("path") or ""))].append({
            "name": b["name"],
            "engine": Path(str(b.get("path"))).name if b.get("path") and b["path"] != "PYCODE" else "內聯檢",
            "state": st.get("state", "UNTESTED"),
            "secs": st.get("secs"), "note": str(st.get("note", ""))[:110]})
    return {"grid": grid_name, "evidence": src.name if src else None,
            "evidence_missing": src is None, "pages": pages}


def harvest_env() -> dict:
    import importlib.metadata as md
    libs = {}
    for lib in KEY_LIBS:
        try:
            libs[lib] = md.version(lib)
        except Exception:
            libs[lib] = "缺(誠實)"
    return {"python": platform.python_version(), "platform": platform.platform(terse=True),
            "libs": libs}


def _mdl089():
    """glob 尾版動態載入 CGC_MDL089 原始模板正主(token 冊+CSS+六槽 render)"""
    p = sorted(HERE.glob("CGC_MDL089_UIBaseTemplate_v*.py"))[-1]
    spec = importlib.util.spec_from_file_location("cgc_mdl089", p)
    m = importlib.util.module_from_spec(spec)
    sys.modules["cgc_mdl089"] = m
    spec.loader.exec_module(m)
    return m


def _mdl173():
    """批701:glob 尾版載入矩陣排版規格正主 CGC_MDL173(批672)。
    缺席回 (None, 因由) —— 缺件≠壞掉,退回 MDL089 那條原路,並且印出來。"""
    hits = sorted(HERE.glob("CGC_MDL173_MatrixReportSpec_v*.py"))
    if not hits:
        return None, "CGC_MDL173_MatrixReportSpec_v*.py 缺"
    try:
        spec = importlib.util.spec_from_file_location("cgc_mdl173_88", hits[-1])
        m = importlib.util.module_from_spec(spec)
        sys.modules["cgc_mdl173_88"] = m
        spec.loader.exec_module(m)
        return m, hits[-1].name
    except Exception as exc:          # 裝了但壞掉 ≠ 沒裝(LL360):前綴 BROKEN 讓上游分得出來
        return None, f"BROKEN {type(exc).__name__}:{str(exc)[:90]}"


def _tab_css(M) -> str:
    """tab 那一層 MDL173 的 css() 沒有(它管矩陣不管分頁),由本檔補。
    但字級與顏色一律讀 SPEC —— 補的是**版面**,不是另立一份規格。"""
    f, st = M.SPEC["font"], M.SPEC["states"]
    return (f".tabs{{display:flex;flex-wrap:wrap;gap:4px;margin:10px 0 6px}}"
            f".tab{{font:{f['note_px']}px/{f['matrix_line']} {f['stack']};padding:3px 9px;"
            f"border:1px solid #2a2f45;background:transparent;color:inherit;cursor:pointer;border-radius:3px}}"
            f".tab b{{margin-left:5px;opacity:.75;font-weight:600}}"
            f".tab.on{{border-color:{st['GREEN']};color:{st['GREEN']}}}"
            f".tab.focus{{border-left:3px solid {st['GATED']}}}"
            f".pane{{display:none}}.pane.on{{display:block}}")


# 批701 自審實錄:第一版把站的態直接丟進 SPEC 的燈色,結果 294 站只有 9 格上了色。
#   根因是**兩套字彙**:格子說 OK/FAIL/SKIP/UNTESTED/TIMEOUT/LOCKED/NOT_RUN,
#   而 SPEC 說 GREEN/RED/NODATA/GATED/ABSENT/SKIP —— 只有 SKIP 剛好同名,所以只有它有色。
#   這正是批700 LL365 的那一族:一個態生得出來,就要有一張表接得住它。差別只在
#   那次接不住是整跑炸掉或整站消失,這次是**安安靜靜不上色** —— 更難發現的那一種。
#   所以這張表要蓋住格子生得出來的每一態,而且沒見過的態**不准默默吞掉**,要現形。
_STATE_MAP = {
    "OK": "GREEN", "FAIL": "RED", "SKIP": "SKIP",
    "UNTESTED": "NODATA",      # 沒測 ≠ 沒問題
    "TIMEOUT": "NODATA",       # 逾時=沒有結論(批616)
    "LOCKED": "GATED",         # 批700:庫被佔住,這一跑量不到
    "NOT_RUN": "ABSENT",       # 中斷時沒跑到
}


def _lamp(M, st: str) -> str:
    """態 → SPEC 燈色鍵。沒見過的態回 NA(灰)而不是無色 —— 無色看起來像正常。"""
    k = _STATE_MAP.get(st, st if st in M.SPEC["states"] else "NA")
    return k if k in M.SPEC["states"] else "NA"


def _matrix_rows(M, rows: list) -> list:
    """一站一列。態經 _STATE_MAP 換成 SPEC 的燈色鍵(顏色在 SPEC 定一次)。"""
    out = []
    for r in rows:
        st = str(r.get("state") or "UNTESTED")
        shown = _lamp(M, st)
        secs = r.get("secs")
        out.append([r["name"][:78], r["engine"][:46],
                    {"t": st, "s": shown},   # 文字印格子的原話,顏色走 SPEC 的鍵
                    (f"{secs}s" if secs is not None else "—"),
                    (r.get("note") or "")[:96]])
    return out


def build_ui_matrix(data: dict, env: dict, M, src_name: str) -> Path:
    """批701 矩陣車道:殼與 CSS 全部委派 MDL173(page_html),本檔只拼 body。
    body = tab 列 + 每系統一張 html_table。**零寫死視覺值**。"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    live = [(k, t) for k, t in SYSTEMS if data["pages"][k]]
    tabs = "".join(
        f'<button class="tab{" focus" if k in FOCUS else ""}" id="tab-{k}" '
        f'onclick="vshow(\'{k}\')">{t}<b>{len(data["pages"][k])}</b></button>'
        for k, t in live)
    panes = []
    for k, t in live:
        rows = data["pages"][k]
        panes.append(
            f'<div class="pane" id="pane-{k}">'
            + M.html_table(["站", "引擎", "態", "秒", "註記"], _matrix_rows(M, rows),
                           caption=f"{t} · {len(rows)} 站",
                           num_cols={3}, center_cols={2})
            + "</div>")
    # KPI:只算操作員指定的三家 —— 數字要講得出它在算誰
    fo = [r for k in FOCUS for r in data["pages"].get(k, [])]
    n_ok = sum(1 for r in fo if r["state"] == "OK")
    n_fail = sum(1 for r in fo if r["state"] == "FAIL")
    n_skip = sum(1 for r in fo if r["state"] == "SKIP")
    n_un = sum(1 for r in fo if r["state"] == "UNTESTED")
    kpis = [{"label": "VCGC+VDF+VRN 站", "value": len(fo), "state": "GATED"},
            {"label": "OK", "value": n_ok, "state": "GREEN"},
            {"label": "FAIL", "value": n_fail, "state": "RED" if n_fail else "GREEN"},
            {"label": "SKIP 環境缺件", "value": n_skip, "state": "SKIP"},
            {"label": "UNTESTED 未測", "value": n_un, "state": "NODATA" if n_un else "GREEN"}]
    warn = ('<div class="law">⚠ 無 GRID 存證(先跑 via-selftest)—— 各站 UNTESTED **誠實不假測**</div>'
            if data["evidence_missing"] else "")
    body = (f"<style>{_tab_css(M)}</style>{warn}"
            f'<div class="tabs">{tabs}</div>{"".join(panes)}'
            "<script>function vshow(k){"
            "document.querySelectorAll('.pane').forEach(p=>p.classList.remove('on'));"
            "document.querySelectorAll('.tab').forEach(t=>t.classList.remove('on'));"
            "document.getElementById('pane-'+k).classList.add('on');"
            "document.getElementById('tab-'+k).classList.add('on');}"
            f"vshow('{live[0][0] if live else 'CGC'}');</script>")
    md = ["# VIA 系統測試分頁(矩陣規格 " + src_name + ")", "",
          f"- 時刻 {ts} · grid={data['grid']} · 存證={data['evidence']}",
          f"- 三家(VCGC/VDF/VRN)站 {len(fo)} · OK {n_ok} · FAIL {n_fail} · SKIP {n_skip} · UNTESTED {n_un}",
          f"- python {env['python']} · {env['platform']}", ""]
    for k, t in live:
        md.append(f"## {t}")
        for r in data["pages"][k]:
            md.append(f"- [{r['state']}] {r['name']} · {r['engine']}")
        md.append("")
    return M.page_html(
        body, title="VIA 系統測試分頁 · 矩陣報告",
        subtitle=(f"批701 · {ts} · grid={data['grid']} · 存證={data['evidence']} · "
                  f"排版規格={src_name} · 資料=存證 join 零重測"),
        md="\n".join(md),
        payload={"ts": ts, "grid": data["grid"], "evidence": data["evidence"],
                 "focus": list(FOCUS), "env": env,
                 "pages": {k: data["pages"][k] for k, _ in live}},
        kpis=kpis,
        law=("誠實六態:綠=OK · 紅=FAIL · 黃 SKIP=環境缺件不假綠 · 灰 UNTESTED=沒測不假測。"
             "零重測(讀最新 GRID 存證)· 零 CDN · 一頁一檔 · 頁上不長 UI(零彈窗律)。"),
        out=UI_OUT)


def build_ui(data: dict, env: dict) -> Path:
    """v0101:視覺全數委派 MDL089 模板正主(CSS 純 token 冊生成+
    六槽 render_section);本引擎零寫死視覺值=改冊即全站換裝"""
    T = _mdl089()
    tokens = T.load_tokens()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    tabs = "".join(
        f'<button class="tab" onclick="show(\'{k}\')" id="tab-{k}">{t.split("(")[0]}'
        f'<b>{len(data["pages"][k])}</b></button>'
        for k, t in SYSTEMS if data["pages"][k])
    pages = "".join(T.render_section(k, t, data["pages"][k], env, tokens)
                    for k, t in SYSTEMS if data["pages"][k])
    warn = ('<div class="warn">⚠ 無 GRID 存證(先跑 via-selftest)=各站 UNTESTED 誠實</div>'
            if data["evidence_missing"] else "")
    html = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 系統測試分頁 v0101</title><style>{T.base_css(tokens)}</style></head>
<body><div class="wrap">
<h1>VIA 系統測試分頁(五系統同一模板)</h1>
<div class="mut">批166 · {ts} · grid={data['grid']} · 存證={data['evidence']} ·
模板正主={T.SSOT.name} · 綠=OK/黃=SKIP 環境缺件誠實/紅=FAIL</div>
{warn}
<div class="tabs">{tabs}</div>
{pages}
<div class="foot">視覺單源=token 冊(改冊即全站換裝,不動引擎)· 頁面=存證
join 零重測 · 誠實三態:黃 SKIP 不假綠/灰 UNTESTED 不假測</div>
<script>
function show(k){{document.querySelectorAll('.page').forEach(p=>p.classList.remove('on'));
document.querySelectorAll('.tab').forEach(t=>t.classList.remove('on'));
document.getElementById(k).classList.add('on');
document.getElementById('tab-'+k).classList.add('on');}}
show('SUP');
</script></div></body></html>"""
    UI_OUT.write_text(html, encoding="utf-8")
    return UI_OUT


def run(fresh: bool = False) -> int:
    if fresh:
        gm_path = sorted(HERE.glob("CGC_MDL064_SelftestGrid_v*.py"))[-1]
        print(f"[fresh] 重跑 grid {gm_path.name}(數分鐘)…", flush=True)
        subprocess.run([sys.executable, str(gm_path)], cwd=HERE)
    data = assemble()
    env = harvest_env()
    for k, t in SYSTEMS:
        rows = data["pages"][k]
        if not rows:
            continue
        ok = sum(1 for r in rows if r["state"] == "OK")
        fail = sum(1 for r in rows if r["state"] == "FAIL")
        skip = sum(1 for r in rows if r["state"] == "SKIP")
        print(f"  [{k}] {t}:{len(rows)} 站 · 綠 {ok} 黃 {skip} 紅 {fail}")
    # 批701:矩陣車道優先(批672 規格正主);缺席誠實退回 MDL089 原路,並印出走了哪一條
    M, src = _mdl173()
    if M is not None:
        ok_rich, why_rich = M.rich_ok()
        p = build_ui_matrix(data, env, M, src)
        lane = f"矩陣規格 {src} · rich {'在' if ok_rich else 'NODATA(' + why_rich + ')'}"
    else:
        p = build_ui(data, env)
        lane = f"MDL089 原路(矩陣規格{'壞掉' if str(src).startswith('BROKEN') else '缺席'}:{src})"
    print(f"[UI] {p.name} · 存證 {data['evidence']} · 車道 {lane}")
    if "--open" in sys.argv[1:]:
        try:
            import webbrowser
            webbrowser.open(p.resolve().as_uri())
            print("  [開頁] 已用系統預設瀏覽器開啟(file://;零 server 零 CDN)")
        except Exception as exc:
            print(f"  [開頁] 開不起來({type(exc).__name__});路徑在上一行,自己點開即可")
    return 0


def status() -> int:
    src, items = _latest_grid_json()
    print(f"UI={'在' if UI_OUT.exists() else '未生'} · 最新存證={src.name if src else '缺'}"
          f"({len(items)} 站)")
    return 0


def selftest() -> int:
    fails, absent = [], []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① grid 尾版+GRID 存證在位",
        bool(sorted(HERE.glob("CGC_MDL064_SelftestGrid_v*.py")))
        and _latest_grid_json()[0] is not None)
    chk("② 歸屬判準真值(五系統+OTHER)",
        classify("x/functional modules/VRN/a.py") == "VRN"
        and classify("x/functional modules/VDF/engine/a.py") == "VDF"
        and classify("x/functional modules/VAP/engine/a.py") == "VAP"
        and classify("x/supportive modules/registry/CGC_MDL064_SelftestGrid_v1.py") == "CGC"
        and classify("x/supportive modules/network/SUP_MDL740_NetUnified_v1.py") == "SUP"
        and classify("x/functional modules/GroupIndex/engine/a.py") == "OTHER"
        and classify("C:\\x\\functional modules\\VDF\\engine\\a.py") == "VDF")
    data = assemble()
    n = sum(len(v) for v in data["pages"].values())
    chk("③ 站表合流(battery×存證 join≥110 站)", n >= 110,
        f"({n} 站·存證 {data['evidence']})")
    chk("④ 五系統皆有站(SUP/CGC/VDF/VAP/VRN 非空)",
        all(data["pages"][k] for k in ("SUP", "CGC", "VDF", "VAP", "VRN")),
        f"({ {k: len(v) for k, v in data['pages'].items()} })")
    env = harvest_env()
    _have5 = sum(1 for v in env["libs"].values() if "缺" not in v)
    if env["python"] and _have5 >= 5:
        chk("⑤ 環境收割(python+關鍵庫版本;缺=誠實)", True)
    else:
        absent.append("⑤")
        print(f"  [ABSENT] ⑤ 環境收割:關鍵庫只在 {_have5}/{len(env['libs'])}(缺 {[k for k, v in env['libs'].items() if '缺' in v]};套件不在本境=缺件≠壞掉)")
    import tempfile
    global UI_OUT
    _u = UI_OUT
    with tempfile.TemporaryDirectory() as td:
        UI_OUT = Path(td) / "ui.html"
        p = build_ui(data, env)
        h = p.read_text(encoding="utf-8")
        chk("⑥ 同一模板五頁(render_page 同構;section×tab 對齊)",
            h.count('<section id=') >= 5 and h.count('class="tab"') >= 5
            and h.count("多指標,上→下") >= 5)
        T = _mdl089()
        tk = T.load_tokens()
        chk("⑦ 三色+響應式(色碼=token 冊值+冊定字級+viewport+auto wrap)",
            all(c in h for c in tk["status"].values())
            and tk["font"]["fs"] in h and "viewport" in h
            and "overflow-wrap:anywhere" in h)
        _src = Path(__file__).read_text(encoding="utf-8")
        chk("⑨ 模板正主消費(CSS 純冊生成+卡片化媒體查詢+本檔零寫死視覺)",
            tk["palette"]["bg"] in h and "table.cards" in h
            and T.SSOT.name in h
            and not any(v in _src for v in tk["status"].values())
            and tk["palette"]["bg"] not in _src)
    UI_OUT = _u
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 紀律宣告(同一測試模板/誠實 OTHER/存證連動零重測/改冊不動引擎)",
        all(k in src for k in ("同一測試模板", "OTHER 不塞併", "存證", "改冊即全站換裝")))
    print(f"  [計] 九檢 OK {9 - len(fails) - len(absent)} · FAIL {len(fails)} · ABSENT {len(absent)}")
    return 1 if fails else (3 if absent else 0)


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print(f"=== 系統測試分頁(CGC_MDL088 v{Path(__file__).stem.rsplit(chr(95) + chr(118), 1)[-1]})· 自測 ===")
        return selftest()
    if "--status" in args:
        return status()
    if "run" in args:
        return run(fresh="--fresh" in args)
    print(__doc__.split("用法:")[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
