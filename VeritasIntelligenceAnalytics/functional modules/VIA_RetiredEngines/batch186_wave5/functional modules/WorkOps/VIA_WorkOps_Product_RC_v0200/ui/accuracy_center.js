
const $=s=>document.querySelector(s);let lang="zh-TW",health=[],integrity=[],progress=[],cal=[];
const L={"zh-TW":{review:"需覆核專案",conflict:"證據衝突",low:"低可信分類",delta:"進度差異 >15%"},
"zh-CN":{review:"需复核项目",conflict:"证据冲突",low:"低可信分类",delta:"进度差异 >15%"},
"en":{review:"Projects needing review",conflict:"Evidence conflicts",low:"Low-confidence classification",delta:"Progress delta >15%"}};
async function j(p){try{return await(await fetch(p,{cache:"no-store"})).json()}catch(e){return{}}}
async function load(){health=(await j("../out/project_health.json")).items||[];integrity=(await j("../out/evidence_integrity.json")).items||[];progress=(await j("../out/project_progress_estimate.json")).items||[];cal=(await j("../out/project_candidates_calibrated.json")).items||[];render()}
function esc(s){return String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]))}
function render(){let t=L[lang],im=Object.fromEntries(integrity.map(x=>[x.project_id,x])),pm=Object.fromEntries(progress.map(x=>[x.project_id,x]));
$("#lReview").textContent=t.review;$("#lConflict").textContent=t.conflict;$("#lLow").textContent=t.low;$("#lDelta").textContent=t.delta;
$("#mReview").textContent=health.filter(x=>x.review_required).length;$("#mConflict").textContent=integrity.reduce((a,x)=>a+(x.contradiction_count||0),0);
$("#mLow").textContent=cal.filter(x=>x.calibrated_gate==="UNCERTAIN").length;$("#mDelta").textContent=progress.filter(x=>Math.abs(x.progress_delta_pct||0)>15).length;
let q=$("#q").value.toLowerCase(),g=$("#gate").value;let rows=health.filter(x=>(!q||(`${x.project_name} ${x.project_id}`).toLowerCase().includes(q))&&(g==="ALL"||(g==="REVIEW"&&x.review_required)||(g==="PASS"&&!x.review_required)));
$("#rows").innerHTML=rows.map(x=>{let i=im[x.project_id]||{},p=pm[x.project_id]||{};return `<article class="row ${x.review_required?"review":""}"><div class=name><b>${esc(x.project_name)}</b><span class=small>${esc(x.project_id)}</span></div><div><span class=small>Health</span><br><b>${x.health_score}%</b><div class=bar><i style="--w:${x.health_score}%"></i></div></div><div><span class=small>Accuracy</span><br><b class="${x.accuracy_confidence_pct<65?"bad":"good"}">${x.accuracy_confidence_pct}%</b></div><div><span class=small>Evidence</span><br>${Math.round((i.field_coverage||0)*100)}% · ${i.contradiction_count||0} conflict</div><div><span class=small>Progress</span><br>User ${p.user_progress_pct??"—"}% / System ${p.system_estimated_progress_pct??"—"}%<br><span class=small>Δ ${p.progress_delta_pct??"—"}%</span>${x.review_reasons?.length?`<br><span class="bad small">${esc(x.review_reasons.join(" · "))}</span>`:""}</div></article>`}).join("")}
$("#q").addEventListener("input",render);$("#gate").addEventListener("change",render);document.querySelectorAll("[data-lang]").forEach(b=>b.addEventListener("click",()=>{lang=b.dataset.lang;render()}));load();
