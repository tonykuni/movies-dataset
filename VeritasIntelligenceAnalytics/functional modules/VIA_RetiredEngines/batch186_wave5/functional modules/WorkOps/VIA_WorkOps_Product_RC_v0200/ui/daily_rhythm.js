
const $=s=>document.querySelector(s);let lang="zh-TW",plan={},cmt={},kpi={};
const L={"zh-TW":{rhythm:"今日工作節奏",commit:"承諾控制",open:"未完成承諾",due:"即將到期",over:"逾期承諾",rate:"兌現率",current:"目前時段"},
"zh-CN":{rhythm:"今日工作节奏",commit:"承诺控制",open:"未完成承诺",due:"即将到期",over:"逾期承诺",rate:"兑现率",current:"当前时段"},
"en":{rhythm:"Daily Operating Rhythm",commit:"Commitment Control",open:"Open Commitments",due:"Due Soon",over:"Overdue",rate:"Fulfillment Rate",current:"Current Phase"}};
async function j(p){try{return await(await fetch(p,{cache:"no-store"})).json()}catch(e){return{}}}
async function load(){plan=await j("../out/daily_operating_plan.json");cmt=await j("../out/commitment_status.json");kpi=await j("../out/commitment_kpi.json");render()}
function esc(s){return String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]))}
function render(){let t=L[lang],ph=plan.current_phase||"morning",labels=plan.phase_labels||{};
$("#lRhythm").textContent=t.rhythm;$("#lCommit").textContent=t.commit;$("#lOpen").textContent=t.open;$("#lDue").textContent=t.due;$("#lOver").textContent=t.over;$("#lRate").textContent=t.rate;$("#phaseTag").textContent=t.current;
$("#phaseTitle").textContent=(labels[ph]||{})[lang]||ph;$("#phaseHint").textContent=(plan.generated_at||"");
let counts=cmt.counts||{};$("#kOpen").textContent=(counts.OPEN||0)+(counts.DUE_SOON||0)+(counts.OVERDUE||0);$("#kDue").textContent=counts.DUE_SOON||0;$("#kOver").textContent=counts.OVERDUE||0;$("#kRate").textContent=kpi.fulfillment_rate_pct==null?"—":kpi.fulfillment_rate_pct+"%";
let order=["morning","pre_noon","afternoon","eod"];$("#phases").innerHTML=order.map(k=>`<article class="phase ${k===ph?"current":""}"><h3>${esc((labels[k]||{})[lang]||k)}</h3>${((plan.phases||{})[k]||[]).map(x=>`<div class=task><b>${esc((x.recommended_action||{})[lang]||x.kind)}</b><span>${esc(x.project_name||x.commitment_id||"")} ${x.due?(" · "+esc(x.due)):""}</span></div>`).join("")||"<span>—</span>"}</article>`).join("");
$("#commitments").innerHTML=(cmt.items||[]).map(x=>`<div class=row><b>${esc(x.project_name||x.project_id||x.case_id||"")}</b><span>${esc(x.owner||"")}</span><span>${esc(x.commitment_text||"")}</span><span>${esc(x.due_at||"")}</span><span class="status ${esc(x.status)}">${esc(x.status)}</span></div>`).join("")||"<div class=row>—</div>";
}
document.querySelectorAll("[data-lang]").forEach(b=>b.onclick=()=>{lang=b.dataset.lang;render()});load();
