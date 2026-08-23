# -*- coding: utf-8 -*-
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
# VRN D8B All-In-One Reprocessor (READ-ONLY on source; no production write; D9 stays locked)
# argv: VRN_DIR  RUN_DIR  OUT_DIR
import sys, os, csv, json, glob, re, html, datetime

VRN, RUNDIR, OUTDIR = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, VRN)
import vrn_d8b_filename_parser as P

os.makedirs(OUTDIR, exist_ok=True)

def find_csv(rundir, *needles):
    best=None
    for f in glob.glob(os.path.join(rundir, "*.csv")):
        n=os.path.basename(f).lower()
        if all(x in n for x in needles): best=f
    return best

def resolve(headers, *aliases):
    low={re.sub(r"[ _]","",h.lower()):h for h in headers}
    for a in aliases:
        k=re.sub(r"[ _]","",a.lower())
        if k in low: return low[k]
    return None

def read_rows(path):
    if not path or not os.path.exists(path): return [],[]
    with open(path, encoding="utf-8-sig", newline="") as f:
        r=csv.DictReader(f); return list(r), r.fieldnames or []

# ---------- BasicInfo reprocess ----------
bi_path = find_csv(RUNDIR,"basicinfo") or find_csv(RUNDIR,"basic")
bi_rows, bi_hdr = read_rows(bi_path)
c_fn  = resolve(bi_hdr,"filename","file")
c_tk  = resolve(bi_hdr,"ticker")
c_dt  = resolve(bi_hdr,"reportdate","date")
c_yf  = resolve(bi_hdr,"yfinanceticker","yfticker","yfinance")
c_bb  = resolve(bi_hdr,"bloombergticker","bloomberg")
c_nm  = resolve(bi_hdr,"name")
c_bk  = resolve(bi_hdr,"broker")

bi_out=[]; tick_fixed=date_rec=0
for row in bi_rows:
    fn=row.get(c_fn,"") if c_fn else ""
    pr=P.parse_filename(fn)
    old_t=(row.get(c_tk,"") or "").strip() if c_tk else ""
    old_d=(row.get(c_dt,"") or "").strip() if c_dt else ""
    new_t=pr["ticker"]; new_d=pr["date"]
    tchg = new_t!=old_t; drec = (not old_d and bool(new_d))
    if tchg: tick_fixed+=1
    if drec: date_rec+=1
    bi_out.append({
        "filename":fn,"old_ticker":old_t,"new_ticker":new_t,"ticker_changed":"Y" if tchg else "",
        "old_date":old_d,"new_date":new_d,"date_kind":pr["date_kind"],"date_recovered":"Y" if drec else "",
        "yfinance":(new_t+".TW") if new_t else "","bloomberg":(new_t+" TT") if new_t else "",
        "broker":pr["broker"] or (row.get(c_bk,"") if c_bk else ""),
        "name":pr["name"] or (row.get(c_nm,"") if c_nm else ""),
    })

# ---------- FinancialData EPS classify + Basic>=Diluted validate ----------
fd_path = find_csv(RUNDIR,"financialdata") or find_csv(RUNDIR,"financial")
fd_rows, fd_hdr = read_rows(fd_path)
f_tk=resolve(fd_hdr,"ticker"); f_ac=resolve(fd_hdr,"account"); f_yr=resolve(fd_hdr,"year")
f_val=resolve(fd_hdr,"value"); f_ev=resolve(fd_hdr,"evidencetext","evidence","text")

eps_bucket={}   # (ticker,year) -> {basic:[],diluted:[]}
eps_tag=0
for row in fd_rows:
    ac=(row.get(f_ac,"") if f_ac else "") or ""
    ev=(row.get(f_ev,"") if f_ev else "") or ""
    kind=P.classify_eps((ac+" "+ev))
    if kind in ("eps_basic","eps_diluted"):
        eps_tag+=1
        key=((row.get(f_tk,"") if f_tk else ""),(row.get(f_yr,"") if f_yr else ""))
        b=eps_bucket.setdefault(key,{"eps_basic":[],"eps_diluted":[]})
        b[kind].append(row.get(f_val,"") if f_val else "")

eps_checks=[]; eps_flag=0
for (tk,yr),b in eps_bucket.items():
    if b["eps_basic"] and b["eps_diluted"]:
        st,note=P.validate_eps_pair(b["eps_basic"][0], b["eps_diluted"][0])
        if st=="FLAG": eps_flag+=1
        eps_checks.append({"ticker":tk,"year":yr,"basic":b["eps_basic"][0],
                           "diluted":b["eps_diluted"][0],"status":st,"note":note})

# ---------- write corrected CSVs ----------
def write_csv(path,rows):
    if not rows: return
    with open(path,"w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

bi_csv=os.path.join(OUTDIR,"VRN_D8B_BasicInfo_Corrected.csv"); write_csv(bi_csv,bi_out)
eps_csv=os.path.join(OUTDIR,"VRN_D8B_EPS_Validation.csv");      write_csv(eps_csv,eps_checks)

# ---------- HTML report (VIA Visual Lock v1) ----------
def esc(x): return html.escape(str(x) if x is not None else "")
def badge(chg): return '<span class="b chg">FIXED</span>' if chg else '<span class="b ok">keep</span>'
rows_html=[]
for r in bi_out:
    rows_html.append("<tr><td>{fn}</td><td class='m'>{ot}</td><td class='m hi'>{nt}</td><td>{tb}</td>"
                     "<td class='m'>{od}</td><td class='m hi'>{nd}</td><td>{dk}</td><td class='m'>{yf}</td>"
                     "<td class='m'>{bb}</td><td>{bk}</td><td>{nm}</td></tr>".format(
        fn=esc(r["filename"]),ot=esc(r["old_ticker"] or "-"),nt=esc(r["new_ticker"] or "-"),
        tb=badge(r["ticker_changed"]),od=esc(r["old_date"] or "-"),nd=esc(r["new_date"] or "-"),
        dk=esc(r["date_kind"]),yf=esc(r["yfinance"] or "-"),bb=esc(r["bloomberg"] or "-"),
        bk=esc(r["broker"]),nm=esc(r["name"])))
eps_html=[]
for r in eps_checks:
    cls={"PASS":"ok","WARN":"warn","FLAG":"chg","NA":""}.get(r["status"],"")
    eps_html.append("<tr><td class='m'>{t}</td><td class='m'>{y}</td><td class='m'>{b}</td>"
                    "<td class='m'>{d}</td><td><span class='b {c}'>{s}</span></td><td>{n}</td></tr>".format(
        t=esc(r["ticker"]),y=esc(r["year"]),b=esc(r["basic"]),d=esc(r["diluted"]),
        c=cls,s=esc(r["status"]),n=esc(r["note"])))
if not eps_html:
    eps_html.append("<tr><td colspan='6' class='muted'>No basic/diluted pairs in current text candidates "
                    "(both sides needed; D8B table-restore will populate these).</td></tr>")

ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
HTML="""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VRN D8B Reprocess</title>
<style>
:root{--bg:#f5f4f0;--ink:#1a1a1a;--mut:#6b6b6b;--line:#e2e0da;--card:#fffdf8;
--ok:#1f7a4d;--warn:#9a6a00;--chg:#b23a2e;--accent:#2a4a7f;}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font-family:'DM Sans',system-ui,'Microsoft JhengHei',sans-serif;font-size:13px;line-height:1.45}
.wrap{max-width:1280px;margin:0 auto;padding:22px}
h1{font-family:'Syne','DM Sans',sans-serif;font-weight:800;font-size:22px;margin:0}
.sub{color:var(--mut);font-size:12px;margin:4px 0 16px}
.kpis{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0 18px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 14px;min-width:120px}
.kpi .n{font-family:'DM Mono',monospace;font-size:20px;font-weight:600}
.kpi .l{color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.04em}
h2{font-family:'Syne',sans-serif;font-size:15px;margin:20px 0 8px}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#efece4;font-size:11px;text-transform:uppercase;letter-spacing:.03em;color:#444}
tr:last-child td{border-bottom:none}
.m{font-family:'DM Mono',monospace;font-size:12px}
.hi{color:var(--accent);font-weight:600}
.muted{color:var(--mut);text-align:center;padding:14px}
.b{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11px;font-weight:600}
.b.ok{background:#e3f1e9;color:var(--ok)}.b.warn{background:#f6ecd2;color:var(--warn)}
.b.chg{background:#f6dedb;color:var(--chg)}
.foot{color:var(--mut);font-family:'DM Mono',monospace;font-size:11px;margin-top:18px;
border-top:1px solid var(--line);padding-top:10px}
.lock{background:#f6dedb;color:var(--chg);border-radius:8px;padding:8px 12px;display:inline-block;font-size:12px;font-weight:600}
</style></head><body><div class="wrap">
<h1>VeritasReportNova · D8B Reprocess</h1>
<div class="sub">Filename Re-parse · ROC/G6/G8 Date Recovery · EPS Basic≥Diluted Invariant · READ-ONLY · @@TS@@</div>
<div class="kpis">
<div class="kpi"><div class="n">@@NBI@@</div><div class="l">BasicInfo rows</div></div>
<div class="kpi"><div class="n">@@NTF@@</div><div class="l">Ticker fixed</div></div>
<div class="kpi"><div class="n">@@NDR@@</div><div class="l">Date recovered</div></div>
<div class="kpi"><div class="n">@@NET@@</div><div class="l">EPS tagged</div></div>
<div class="kpi"><div class="n">@@NEF@@</div><div class="l">EPS invariant FLAG</div></div>
</div>
<div class="lock">D9 PRODUCTION WRITE — LOCKED (this pass writes only to its own run dir)</div>
<h2>BasicInfo — corrected ticker / date</h2>
<table><tr><th>Filename</th><th>old tk</th><th>new tk</th><th></th><th>old date</th><th>new date</th><th>kind</th><th>YF</th><th>BBG</th><th>Broker</th><th>Name</th></tr>
@@BI@@
</table>
<h2>EPS — Basic ≥ Diluted invariant</h2>
<table><tr><th>Ticker</th><th>Year</th><th>Basic</th><th>Diluted</th><th>Status</th><th>Note</th></tr>
@@EPS@@
</table>
<div class="foot">Veritas Intelligence Analytics │ D8B Reprocessor · TW_TICKER_REGEX locked · SSOT untouched · no production write</div>
</div></body></html>"""
for k,v in {"@@TS@@":ts,"@@NBI@@":str(len(bi_out)),"@@NTF@@":str(tick_fixed),
            "@@NDR@@":str(date_rec),"@@NET@@":str(eps_tag),"@@NEF@@":str(eps_flag),
            "@@BI@@":"\n".join(rows_html),"@@EPS@@":"\n".join(eps_html)}.items():
    HTML=HTML.replace(k,v)
html_path=os.path.join(OUTDIR,"VRN_D8B_Reprocess.html")
with open(html_path,"w",encoding="utf-8") as f: f.write(HTML)

summary={"basicinfo_rows":len(bi_out),"ticker_fixed":tick_fixed,"date_recovered":date_rec,
         "eps_tagged":eps_tag,"eps_flag":eps_flag,"bi_csv":bi_csv,"eps_csv":eps_csv,"html":html_path,
         "bi_src":bi_path,"fd_src":fd_path}
with open(os.path.join(OUTDIR,"VRN_D8B_Reprocess.json"),"w",encoding="utf-8") as f:
    json.dump(summary,f,ensure_ascii=False,indent=2)

print("[D8B] BasicInfo rows  :",len(bi_out))
print("[D8B] Ticker fixed    :",tick_fixed)
print("[D8B] Date recovered  :",date_rec)
print("[D8B] EPS tagged      :",eps_tag," FLAG:",eps_flag)
print("[D8B] HTML            :",html_path)
print("[HTML_PATH]"+html_path)
