# -*- coding: utf-8 -*-
"""build_subsystem_pages_v0100.py — 子系統分開模板產生器 v0100(操作員令:視覺鎖定子系統模板分開分別加入功能)。

每個功能子系統(01-07)產一頁獨立模板(視覺鎖=Veritas Header;零 CDN;LF 固定;內容未變不重寫):
  masthead(印章「理」+ 編號 + 襯線題)· 狀態/證據 · 動詞卡(一鍵複製)· 拖曳輸入+precheck ·
  正典深層 UI 連結(在庫才列 — 誠實缺席不佔位)。
資料源:動態吸取最新 build_via_mother_v0*.py 的 SUBS/T(單一資料源;嚴禁雙軌維護)。
產出:<VIA根>/supportive modules/ui_support/subsystem_pages/VIA_Sub_<pid>.html(追蹤)。
"""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUTDIR = VIA / "supportive modules" / "ui_support" / "subsystem_pages"


def load_mother():
    cands = sorted(HERE.glob("build_via_mother_v0*.py"))
    spec = importlib.util.spec_from_file_location("via_mother_gen", cands[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PAGE = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(num)s %(zh)s · VIA 子系統模板</title><style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:%(bg)s;color:%(ink2)s;font-family:"Microsoft JhengHei","Segoe UI",system-ui,sans-serif;font-size:clamp(12px,.6vw + 10.5px,13.5px);padding:14px 18px;max-width:1080px;margin:0 auto}
.mast{display:flex;align-items:flex-end;gap:14px;border-bottom:1px solid %(line)s;padding-bottom:11px;margin-bottom:14px}
.seal{width:38px;height:38px;background:%(seal)s;border-radius:5px;color:%(bg)s;font-family:%(cjkserif)s;font-weight:600;font-size:21px;line-height:38px;text-align:center;flex:none}
.mast .num{font-family:%(mono)s;font-size:10px;letter-spacing:.16em;color:%(mut)s;text-transform:uppercase}
.mast h1{font-family:%(serif)s;font-size:clamp(16px,1.2vw + 12px,21px);font-weight:500;letter-spacing:.055em;color:%(ink)s;line-height:1.15}
.mast .zh{font-size:12px;color:%(mut)s;margin-top:2px}
.mast .st{margin-left:auto;font-family:%(mono)s;font-size:11px;color:%(down)s;white-space:nowrap}
.bar{height:4px;border-radius:2px;background:%(teal)s;width:56px;margin:6px 0 0}
.card{background:%(paper)s;border:1px solid %(line)s;border-radius:8px;padding:13px 16px;margin-bottom:12px;box-shadow:0 1px 2px rgba(27,26,23,.04);transition:box-shadow .18s ease,transform .18s ease}
.card:hover{box-shadow:0 4px 14px rgba(27,26,23,.09);transform:translateY(-2px)}
.card h3{font-family:%(serif)s;font-size:14px;font-weight:600;color:%(ink)s;margin-bottom:8px;border-bottom:2px solid %(line)s;padding-bottom:5px}
h3::before{content:"";display:inline-block;width:7px;height:7px;background:%(seal)s;border-radius:1px;margin-right:7px;vertical-align:1px}
.cmdrow{display:flex;gap:8px;align-items:flex-start;margin:5px 0}
.cmd{flex:1;font-family:%(mono)s;font-size:11.5px;background:%(paper2)s;border:1px solid %(line2)s;border-left:3px solid %(teal)s;border-radius:6px;padding:7px 10px;user-select:all;word-break:break-all}
.btn{padding:6px 12px;border:1px solid %(line)s;border-radius:6px;background:%(paper)s;color:%(ink2)s;font-family:inherit;font-size:11.5px;cursor:pointer;flex:none;transition:background .15s ease,border-color .15s ease}
.btn:hover{background:%(paper2)s;border-color:%(teal)s}
.btn.pri{background:%(seal)s;border-color:%(seal)s;color:#fff}
.small{font-size:11px;color:%(mut)s}
.drop{border:2px dashed %(line)s;border-radius:8px;padding:18px;text-align:center;color:%(mut)s;transition:border-color .18s ease,background .18s ease}
.drop.over{border-color:%(seal)s;background:%(paper2)s;color:%(ink)s}
.drop ul{list-style:none;margin-top:8px;text-align:left}
.drop li{font-family:%(mono)s;font-size:11px;padding:2px 0;color:%(ink2)s}
a.link{color:%(accent)s}
.ft{font-family:%(mono)s;font-size:9.5px;color:%(mut)s;border-top:1px solid %(line)s;padding-top:9px;margin-top:16px;text-align:center}
@keyframes fadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
body{animation:fadeUp .32s ease-out}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
@media (max-width:760px){body{padding:10px}.mast{flex-wrap:wrap}.mast .st{margin-left:0;width:100%%}}
</style></head><body>
<div class="mast"><span class="seal">理</span>
<div><div class="num">Veritas Intelligence Analytics · %(num)s %(en)s</div>
<h1>%(en_title)s</h1><div class="zh">%(zh)s — %(role)s</div><div class="bar"></div></div>
<div class="st">%(st)s</div></div>
<div class="card"><h3>證據(誠實燈 — 實測/存證口徑)</h3><p class="small">%(ev)s</p></div>
<div class="card"><h3>功能動詞(滑鼠一鍵複製)</h3>%(cmds)s
<p class="small">複製後貼 PowerShell 執行;或於母頁指令組合器下載 .cmd 批次。</p></div>
<div class="card"><h3>輸入資料(拖曳式加入 → 輸入前檢查)</h3>
<div class="drop" id="dz">csv / json / parquet <b>拖曳到此</b><ul id="dl"></ul></div>
<div class="cmd" id="pc" style="display:none;margin-top:6px"></div></div>
%(uicard)s
<div class="ft">VIA 子系統模板 · %(num)s %(zh)s · 視覺鎖 Veritas Header · 零 CDN 離線 · 母頁一窗返回</div>
<script>
document.querySelectorAll('.cmdrow .btn').forEach(function(b){
 b.addEventListener('click',function(){
  var t=b.parentElement.querySelector('.cmd').textContent;
  function done(ok){b.textContent=ok?'已複製 ✓':'失敗';setTimeout(function(){b.textContent='複製';},1500);}
  if(navigator.clipboard&&navigator.clipboard.writeText){
   navigator.clipboard.writeText(t).then(function(){done(true);},function(){done(false);});}
  else{var ta=document.createElement('textarea');ta.value=t;document.body.appendChild(ta);ta.select();
   var ok=false;try{ok=document.execCommand('copy');}catch(e){}
   document.body.removeChild(ta);done(ok);}});});
var dz=document.getElementById('dz'),dl=document.getElementById('dl'),pc=document.getElementById('pc');
['dragenter','dragover'].forEach(function(ev){dz.addEventListener(ev,function(e){e.preventDefault();dz.classList.add('over');});});
['dragleave','drop'].forEach(function(ev){dz.addEventListener(ev,function(e){e.preventDefault();dz.classList.remove('over');});});
dz.addEventListener('drop',function(e){
 if(!e.dataTransfer)return;dl.innerHTML='';var cs=[];
 Array.prototype.forEach.call(e.dataTransfer.files,function(f){
  var li=document.createElement('li');li.textContent='▣ '+f.name;dl.appendChild(li);
  cs.push('via-precheck --file "'+f.name+'"');});
 if(cs.length){pc.style.display='block';pc.textContent=cs.join(' && ');}});
</script></body></html>"""


def build():
    m = load_mother()
    OUTDIR.mkdir(parents=True, exist_ok=True)
    en_titles = {
        "workops": "WORKOPS GOVERNANCE & COMMAND BOARD",
        "vap": "VERITAS ANALYTICS PLOTTING ENGINE",
        "vrn": "VERITAS RESEARCH NOTES FORGE",
        "vdf": "VERITAS DATA FORGE",
        "chipwar": "CHIPWAR INTELLIGENCE DASHBOARD",
        "multifactor": "MULTIFACTOR VALIDATION LAB",
        "talib": "TECHNICAL ANALYSIS LIBRARY 64",
    }
    # 正典深層 UI(在庫正本;母 SUBS.ui 已改指本模板,故深層連結由此映射,嚴禁自指)
    deep_ui = {
        "workops": "functional modules/WorkOps/VIA_WorkOps_主力包與對照卡_v002.html",
        "vap": "functional modules/VAP/ui/VAP_Workbench_v010.html",
        "vrn": "functional modules/VRN/template/VDF_VRN_Integrated_ReportSSOT_AutoLayout_FINAL.html",
        "vdf": "functional modules/VDF/VDF_VRN_Integrated_ReportSSOT_AutoLayout_FINAL.html",
        "chipwar": "functional modules/ChipWar/docs/VIA_FOMO_Index_Report_sample_20260812.html",
        "multifactor": "",
        "talib": "",
    }
    n_new = n_same = 0
    for pid, num, zh, role, st, ev, cmds, _mother_ui in m.SUBS:
        ui = deep_ui.get(pid, "")
        cmdhtml = "".join(
            '<div class="cmdrow"><div class="cmd">%s</div><button class="btn">複製</button></div>'
            % m.esc(c.split("→")[0].strip()) for c in cmds)
        if ui and (VIA / ui).exists():
            uicard = ('<div class="card"><h3>正典深層介面(在庫正本)</h3>'
                      '<p><a class="link" href="../../../%s">%s</a></p></div>'
                      % (m.esc(ui.replace(" ", "%20")), m.esc(ui)))
        else:
            uicard = ('<div class="card"><h3>正典深層介面</h3>'
                      '<p class="small">本子系統以命令列動詞+產出報告呈現(誠實缺席,不佔位假圖)。</p></div>')
        html = PAGE % dict(m.T, num=num, zh=m.esc(zh), role=m.esc(role), st=m.esc(st),
                           ev=m.esc(ev), cmds=cmdhtml, uicard=uicard,
                           en=pid.upper(), en_title=en_titles.get(pid, pid.upper()))
        out = OUTDIR / ("VIA_Sub_%s.html" % pid)
        data = html.encode("utf-8")
        if out.exists() and out.read_bytes() == data:
            n_same += 1
        else:
            out.write_bytes(data)
            n_new += 1
    print("[子模板] %s · 重生 %d · 未變 %d(共 %d 頁;視覺鎖 Veritas Header)"
          % (OUTDIR, n_new, n_same, len(m.SUBS)))
    return 0


if __name__ == "__main__":
    sys.exit(build())
