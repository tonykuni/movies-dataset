#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL094_CommandDeck — VIA 指揮台(批204;操作員令)
====================================================================
操作員令:「輸入用 Windows I/O 拖曳式、下拉選單、勾選等簡單操作法;
越少操作越自動化」。
產出 VIA_UI_CommandDeck_v0100.html(零 CDN 自包含;token 冊樣式):
  ① 一鍵任務卡:點卡=指令入剪貼簿(貼到 PowerShell 按 Enter 即跑)
     ——全自動日更/歷史回補/三源共識/月營收全市場/重生全部 UI
  ② 組合器:下拉選引擎×勾選動詞×股票碼 chips→即時生成指令+複製
  ③ 拖曳收件區:檔案拖入→依副檔名自動生成收容+處理指令
  ④ Root 欄:預設=操作員裁定 Active Root(批196);可改=零寫死鎖定
瀏覽器沙盒誠實界線:HTML 不能直接執行本機程式——本台=「零打字
指令產生器」(複製→貼上→Enter 三動作);真正零操作=每日開機
boot 自動鏈+桌面 VIA-Start.bat 雙擊(同批交付)。
用法:python3 CGC_MDL094_CommandDeck_v0100.py run | --selftest
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
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
UI_OUT = VIA / "supportive modules" / "ui_support" / "VIA_UI_CommandDeck_v0100.html"
DEFAULT_ROOT = r"C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics"

# 任務冊(單一 SSOT;{R}=Root 佔位由 JS 帶入)
TASKS = [
 {"id": "boot", "zh": "全自動日更(建議每日一次)", "icon": "🔄",
  "cmd": 'powershell -ExecutionPolicy Bypass -File "{R}\\launch.ps1"',
  "note": "背景跑全鏈+自動開 UI;終端不卡"},
 {"id": "backfill", "zh": "歷史回補 2020~(可中斷續跑)", "icon": "📥",
  "cmd": '$env:VIA_NET_CONSENT="YES"; $env:VIA_SCRAPE_CONSENT="YES"; python "{R}\\functional modules\\VDF\\engine\\VDF_ENG064_HistoryBackfill_v0100.py" run',
  "note": "由新到舊;斷了再點一次=接著跑"},
 {"id": "consensus", "zh": "三源共識更新(鉅亨 FactSet)", "icon": "🎯",
  "cmd": '$env:VIA_NET_CONSENT="YES"; $env:VIA_SCRAPE_CONSENT="YES"; python "{R}\\functional modules\\VRN\\VRN_ENG071_CnyesFusion_v0100.py" run {CODES}',
  "note": "預設 2330 2317 2454;可在組合器改碼"},
 {"id": "revenue", "zh": "月營收全市場(MOPS 官方)", "icon": "🏢",
  "cmd": '$env:VIA_NET_CONSENT="YES"; $env:VIA_SCRAPE_CONSENT="YES"; python "{R}\\functional modules\\VDF\\engine\\VDF_ENG063_MonthlyRevenue_v0102.py" run',
  "note": "上市+上櫃+證券商 1,377 檔一次入庫"},
 {"id": "ui", "zh": "重生全部 UI 頁", "icon": "🖥️",
  "cmd": 'python "{R}\\supportive modules\\registry\\CGC_MDL090_SystemHub_v0101.py" run; python "{R}\\supportive modules\\registry\\CGC_MDL093_GovernanceMatrix_v0100.py" run; start "" "{R}\\supportive modules\\ui_support\\VIA_UI_SystemHub_v0100.html"',
  "note": "重生+自動開樞紐母頁"},
]
ENGINES = [
 {"zh": "月營收分析", "path": "functional modules\\VDF\\engine\\VDF_ENG063_MonthlyRevenue_v0102.py",
  "verbs": ["run", "--analyze", "--status"], "codes": True},
 {"zh": "鉅亨共識", "path": "functional modules\\VRN\\VRN_ENG071_CnyesFusion_v0100.py",
  "verbs": ["run", "--status"], "codes": True},
 {"zh": "Yahoo 共識", "path": "functional modules\\VRN\\VRN_ENG070_YahooConsensus_v0101.py",
  "verbs": ["run", "--status"], "codes": True},
 {"zh": "歷史回補", "path": "functional modules\\VDF\\engine\\VDF_ENG064_HistoryBackfill_v0100.py",
  "verbs": ["run", "--status"], "codes": False},
 {"zh": "因子庫", "path": "functional modules\\VDF\\engine\\VDF_ENG061_FeatureStore_v0100.py",
  "verbs": ["build", "--status"], "codes": False},
]
# 拖曳收件對映(副檔名→處置)
DROP_MAP = {
 "pdf": {"zh": "券商報告 PDF", "dest": "functional modules\\VRN\\input_reports",
         "after": "python \"{R}\\functional modules\\VRN\\vrn_report_digest_v0107.py\""},
 "docx": {"zh": "Word 報告", "dest": "functional modules\\VRN\\input_reports",
          "after": "python \"{R}\\functional modules\\VRN\\vrn_report_digest_v0107.py\""},
 "py": {"zh": "Python 引擎(候收容)", "dest": "supportive modules\\_inbox_to_classify",
        "after": "rem 收容後由治理批次分類"},
 "csv": {"zh": "資料表", "dest": "functional modules\\VDF\\input_inbox",
         "after": "rem 入庫由 VDF 攝入引擎處理"},
}


def _tk():
    p = sorted(HERE.glob("CGC_MDL089_UIBaseTemplate_v*.py"))[-1]
    spec = importlib.util.spec_from_file_location("mdl089_deck", p)
    m = importlib.util.module_from_spec(spec)
    sys.modules["mdl089_deck"] = m
    spec.loader.exec_module(m)
    return m, m.load_tokens()


def render() -> str:
    T, tk = _tk()
    st = tk["status"]
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    cards = "".join(
        f'<button class="card" data-cmd="{t["cmd"].replace(chr(34), "&quot;")}">'
        f'<div class="ci">{t["icon"]}</div><div class="ct">{t["zh"]}</div>'
        f'<div class="mut">{t["note"]}</div></button>'
        for t in TASKS)
    eng_opts = "".join(f'<option value="{i}">{e["zh"]}</option>'
                       for i, e in enumerate(ENGINES))
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 指揮台 v0100</title><style>{T.base_css(tk)}
.deck{{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px}}
.card{{text-align:left;padding:12px;border:1px solid #e0e0e0;border-radius:8px;
background:#fff;cursor:pointer;min-height:44px}}
.card:hover{{border-color:{st["OK"]};box-shadow:0 1px 6px rgba(0,0,0,.12)}}
.ci{{font-size:22px}}.ct{{font-weight:bold;margin:4px 0}}
.row{{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:6px 0}}
select,input[type=text]{{padding:8px;border:1px solid #ccc;border-radius:6px;
min-height:40px;font-size:13px}}
label.ck{{display:inline-flex;align-items:center;gap:4px;padding:6px 8px;
border:1px solid #e0e0e0;border-radius:6px;cursor:pointer}}
#drop{{border:2px dashed #bbb;border-radius:10px;padding:26px;text-align:center;
color:#888;transition:.15s}}
#drop.on{{border-color:{st["OK"]};background:#f0fff4;color:#333}}
#cmdout{{width:100%;font-family:monospace;font-size:11px;padding:8px;
border:1px solid #ccc;border-radius:6px;min-height:56px;word-break:break-all}}
.copybtn{{background:{st["OK"]};color:#fff;border:0;border-radius:6px;
padding:10px 16px;cursor:pointer;min-height:44px}}
#toast{{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);
background:#333;color:#fff;padding:10px 18px;border-radius:20px;display:none}}
</style></head><body><div class="wrap">
<h1>🎛️ VIA 指揮台(零打字操作)</h1>
<div class="mut">{ts} · 點卡/下拉/勾選/拖曳 → 指令自動入剪貼簿 → 貼到
PowerShell 按 Enter · 誠實界線:瀏覽器不能直接執行本機程式,本台=
三動作極簡(複製→貼上→Enter);真零操作=每日開機自動鏈+桌面
VIA-Start.bat 雙擊</div>
<section class="page on"><h2>⚙️ Root(批196 裁定 Active Root;可改)</h2>
<input type="text" id="root" value="{DEFAULT_ROOT}" style="width:100%"></section>
<section class="page on"><h2>① 一鍵任務卡(點=複製指令)</h2>
<div class="deck">{cards}</div></section>
<section class="page on"><h2>② 組合器(下拉×勾選×代碼)</h2>
<div class="row">
<select id="eng">{eng_opts}</select>
<span id="verbs"></span>
<input type="text" id="codes" placeholder="股票碼(空白分隔,如 2330 2317)" value="2330 2317 2454">
<label class="ck"><input type="checkbox" id="consent" checked>同意閘(網路任務必勾)</label>
</div></section>
<section class="page on"><h2>③ 拖曳收件(把檔案拖進來)</h2>
<div id="drop">把 PDF/Word/Python/CSV 檔拖到這裡 → 自動生成收容指令</div></section>
<section class="page on"><h2>📋 指令輸出</h2>
<div id="cmdout">(點任務卡或調整組合器)</div>
<div class="row"><button class="copybtn" id="copy">複製指令</button>
<span class="mut">→ 開 PowerShell 貼上按 Enter 即執行</span></div></section>
<div id="toast">已複製!到 PowerShell 貼上按 Enter</div>
</div><script>
const ENGINES = {json.dumps(ENGINES, ensure_ascii=False)};
const DROPMAP = {json.dumps(DROP_MAP, ensure_ascii=False)};
const $ = id => document.getElementById(id);
const R = () => $("root").value.trim().replace(/\\\\+$/, "");
let current = "";
function setCmd(c) {{ current = c; $("cmdout").textContent = c; }}
function toast() {{ const t = $("toast"); t.style.display = "block";
  setTimeout(() => t.style.display = "none", 1800); }}
function copyCmd() {{
  if (!current) return;
  const ta = document.createElement("textarea");
  ta.value = current; document.body.appendChild(ta); ta.select();
  try {{ navigator.clipboard ? navigator.clipboard.writeText(current) :
        document.execCommand("copy"); }} catch (e) {{ document.execCommand("copy"); }}
  document.body.removeChild(ta); toast();
}}
$("copy").onclick = copyCmd;
document.querySelectorAll(".card").forEach(b => b.onclick = () => {{
  setCmd(b.dataset.cmd.replaceAll("{{R}}", R())
        .replaceAll("{{CODES}}", $("codes").value.trim())); copyCmd(); }});
function renderVerbs() {{
  const e = ENGINES[$("eng").value];
  $("verbs").innerHTML = e.verbs.map((v, i) =>
    `<label class="ck"><input type="radio" name="vb" value="${{v}}"
     ${{i === 0 ? "checked" : ""}}>${{v}}</label>`).join("");
  document.querySelectorAll('input[name=vb]').forEach(r => r.onchange = combo);
  combo();
}}
function combo() {{
  const e = ENGINES[$("eng").value];
  const vb = document.querySelector('input[name=vb]:checked');
  const verb = vb ? vb.value : e.verbs[0];
  let c = "";
  if ($("consent").checked)
    c += '$env:VIA_NET_CONSENT="YES"; $env:VIA_SCRAPE_CONSENT="YES"; ';
  c += `python "${{R()}}\\\\${{e.path}}" ${{verb}}`;
  if (e.codes && (verb === "run" || verb === "--analyze"))
    c += " " + $("codes").value.trim();
  setCmd(c.trim());
}}
$("eng").onchange = renderVerbs;
$("codes").oninput = combo; $("consent").onchange = combo;
$("root").oninput = combo;
renderVerbs();
const dz = $("drop");
["dragover", "dragenter"].forEach(ev => dz.addEventListener(ev, e => {{
  e.preventDefault(); dz.classList.add("on"); }}));
["dragleave", "drop"].forEach(ev => dz.addEventListener(ev, e => {{
  e.preventDefault(); dz.classList.remove("on"); }}));
dz.addEventListener("drop", e => {{
  const fs = [...e.dataTransfer.files];
  if (!fs.length) return;
  const lines = [];
  fs.forEach(f => {{
    const ext = f.name.split(".").pop().toLowerCase();
    const m = DROPMAP[ext];
    if (!m) {{ lines.push(`rem ${{f.name}}:未支援副檔名(誠實跳過)`); return; }}
    lines.push(`Copy-Item "<拖入檔原始路徑>\\\\${{f.name}}" "${{R()}}\\\\${{m.dest}}\\\\" # ${{m.zh}}`);
    lines.push(m.after.replaceAll("{{R}}", R()));
  }});
  lines.unshift("rem 瀏覽器安全沙盒不給完整路徑=請把 <拖入檔原始路徑> 改成檔案所在資料夾(誠實界線)");
  setCmd(lines.join("\\n")); copyCmd();
  dz.textContent = fs.map(f => "📄 " + f.name).join("  ") + " → 指令已複製";
}});
</script></body></html>"""


def build() -> Path:
    UI_OUT.write_text(render(), encoding="utf-8")
    return UI_OUT


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    p = build()
    h = p.read_text(encoding="utf-8")
    chk("① 一鍵任務卡 5 張(日更/回補/共識/月營收/重生 UI;點=複製)",
        h.count('class="card"') == 5 and "launch.ps1" in h
        and "VDF_ENG064" in h and "VRN_ENG071" in h)
    chk("② 組合器三件套(下拉引擎×動詞勾選×代碼欄+同意閘勾選)",
        'id="eng"' in h and 'name="vb"' in h and 'id="codes"' in h
        and 'id="consent"' in h and "VIA_NET_CONSENT" in h)
    chk("③ 拖曳收件區(dragover/drop+副檔名對映 4 類+未支援誠實跳過)",
        'id="drop"' in h and "dataTransfer" in h and "誠實跳過" in h
        and all(k in h for k in ("pdf", "docx", "csv")))
    chk("④ 剪貼簿雙軌(navigator.clipboard+execCommand 後備)+toast 回饋",
        "navigator.clipboard" in h and "execCommand" in h and 'id="toast"' in h)
    chk("⑤ Root 可改零鎖死(預設=批196 裁定;input 綁 combo)",
        DEFAULT_ROOT.replace("\\", "\\\\") in h or DEFAULT_ROOT in h
        and '$("root").oninput' in h)
    chk("⑥ 誠實界線宣告(瀏覽器不能直接執行本機程式;三動作極簡)",
        "不能直接執行本機程式" in h and "三動作" in h)
    chk("⑦ 零 CDN 零外鏈+token 冊樣式+行動 44px 觸控最小高",
        "http://" not in h and "https://" not in h and "min-height:44px" in h)
    bat = VIA / "VIA-Start.bat"
    chk("⑧ 桌面雙擊啟動器在位(VIA-Start.bat=真零打字入口)",
        bat.exists() and "launch.ps1" in bat.read_text(encoding="utf-8", errors="ignore"))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 紀律宣告(任務冊 SSOT/誠實界線/加速橋)",
        "任務冊(單一 SSOT" in src and "VIA:ACCEL-BRIDGE" in src)
    print(f"  [計] 九檢 OK {9 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== VIA 指揮台(CGC_MDL094)· 九檢自測(零網路)===")
        return selftest()
    p = build()
    print(f"[UI] {p.name} · 一鍵卡×組合器×拖曳收件(零打字)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
