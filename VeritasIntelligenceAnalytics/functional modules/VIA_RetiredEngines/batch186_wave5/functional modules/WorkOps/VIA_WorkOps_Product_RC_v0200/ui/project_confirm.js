
const $=s=>document.querySelector(s);
let data={items:[]};
async function load(){
  try{data=await (await fetch("../out/project_candidates.json",{cache:"no-store"})).json()}
  catch(e){data={items:[]}}
  render();
}
function render(){
  const items=data.items||[];
  $("#nAll").textContent=items.length;
  $("#nStrong").textContent=items.filter(x=>x.gate==="REVIEW_STRONG").length;
  $("#nNew").textContent=items.filter(x=>x.gate==="NEW_OR_UNCERTAIN").length;
  $("#cards").innerHTML=items.map((x,i)=>`<article class="card">
    <h3>${esc(x.subject||"(無主旨)")}</h3>
    <div class="meta">${esc(x.conversation_id)} · ${esc(x.folder||"未識別資料夾")}</div>
    <div class="chips">${(x.product_codes||[]).map(c=>`<span class="chip">${esc(c)}</span>`).join("")}</div>
    ${(x.candidates||[]).map((c,j)=>`<label class="candidate">
      <input type="radio" name="p${i}" value="${esc(c.project_id)}" ${j===0?"checked":""}>
      <span><b>${esc(c.display_name)}</b><div class="evidence">${esc((c.evidence||[]).join(" · "))}</div></span>
      <span class="score">${Math.round((c.score||0)*100)}%</span></label>`).join("")}
    <div class="actions"><button class="primary" onclick="confirmExisting(${i})">確認歸戶</button><button class="new" onclick="openNew(${i})">建立新專案</button></div>
  </article>`).join("") || `<article class="card">目前沒有待確認候選。</article>`;
}
function esc(s){return String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]))}
function confirmExisting(i){
  const x=data.items[i]; const r=document.querySelector(`input[name=p${i}]:checked`);
  if(!r)return alert("請先選擇專案");
  navigator.clipboard?.writeText(`py engines/workops_project_registration.py accept "${x.conversation_id}" "${r.value}"`);
  alert("已準備確認指令並複製。此靜態 UI 不直接修改 SSOT。");
}
let newIdx=-1;
function openNew(i){newIdx=i;$("#newName").value="";$("#newDialog").showModal()}
$("#createBtn").addEventListener("click",e=>{
  const name=$("#newName").value.trim(); if(!name){e.preventDefault();return}
  navigator.clipboard?.writeText(`py engines/workops_project_registration.py create "${name.replaceAll('"','')}"`);
  setTimeout(()=>alert("已複製建立專案指令；建立後再確認此郵件歸戶。"),0);
});
$("#reload").onclick=load; load();
