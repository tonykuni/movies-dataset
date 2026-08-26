
const $=s=>document.querySelector(s);
let reg={templates:[]},defs={};
async function init(){
  try{reg=await (await fetch("../templates/template_registry.json",{cache:"no-store"})).json()}catch(e){}
  $("#template").innerHTML=(reg.templates||[]).map(t=>`<option value="${t.key}">${t.display_name["zh-TW"]} / ${t.display_name.en}</option>`).join("");
  for(const t of reg.templates||[]){
    try{defs[t.key]=await (await fetch("../templates/"+t.file,{cache:"no-store"})).json()}catch(e){}
  }
  render();
}
function render(){
  const lang=$("#language").value,key=$("#template").value,t=defs[key]||{};
  const meta=(reg.templates||[]).find(x=>x.key===key)||{};
  $("#tplName").textContent=(meta.display_name||{})[lang]||key;
  const opts=(t.outlook_voting_options||{})[lang]||[];
  $("#preview").innerHTML=`<div class="preview-subject">${esc((t.subject||{})[lang]||"")}</div>
    <p>${esc((t.intro||{})[lang]||"")}</p>
    <div class="muted">Voting / Choice options</div>
    ${opts.map(x=>`<div class="choice">○ ${esc(x)}</div>`).join("")}`;
  $("#cmd").textContent=`py engines/workops_followup_pack_builder.py build --language ${lang} --template ${key}`;
}
function esc(s){return String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]))}
$("#language").onchange=render;$("#template").onchange=render;
$("#build").onclick=()=>{navigator.clipboard?.writeText($("#cmd").textContent);alert("已複製安全執行指令；UI 本身不直接寄信。")};
init();
