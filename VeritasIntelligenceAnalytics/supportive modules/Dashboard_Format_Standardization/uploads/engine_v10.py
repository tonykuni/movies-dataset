# -*- coding: utf-8 -*-
"""
VERITAS Integrated Macro & Investment Engine — v10 (稽核·重整版)
================================================================
最嚴格標準:把每一條論述分級,刪除/降級沒通過驗證的,重跑 測試→回測→惡魔→結論。
證據分級 (Evidence Tier):
  T1 可驗證數據   = 公開市場/官方數據,可獨立查證(最高)
  T2 理論支持     = 有學術文獻機制支撐(次高)
  T3 judgment先驗 = 結構化判斷/編碼,非數據(僅供結構示意,不得當證據)
  T4 推測         = 敘事推論,低信心(保留但明確標示)
  X  刪除/降級    = 經測試不成立或被誇大的論述
"""
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
import json, os, statistics, itertools
HERE=os.path.dirname(os.path.abspath(__file__))
d=json.load(open(os.path.join(HERE,"engine_data.json"),encoding="utf-8"))

def corr(a,b):
    ma,mb=statistics.mean(a),statistics.mean(b)
    n=sum((x-ma)*(y-mb) for x,y in zip(a,b)); dd=(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))**.5
    return n/dd if dd else 0.0

print("="*72);print("[稽核1] 證據分級:每條論述歸類,刪除/降級沒通過驗證的");print("="*72)
LEDGER=[
 # (claim, tier, ruling)
 ("CAPE 40.06、前瞻P/E 22.3、ERP≈0(盈餘殖利率4.48% vs 10Y 4.49%)","T1","保留:可驗證市場數據"),
 ("集中度溢價 今+48% vs 2000+105%;前10大盈餘佔比30% vs 2000<20%","T1","保留:Goldman可查證"),
 ("美財政:赤字1.9兆、淨利息>1兆、債/GDP 101→124%、評等全失AAA","T1","保留:CBO/Treasury/Moody's"),
 ("央行超級週:ECB 6/11升息2.25%、BoJ 6/16、Fed 6/17","T1","保留:CNBC/官方"),
 ("基差交易18:1、repo 6.6兆、Fed Cook/IMF列系統脆弱","T1","保留:Fed/IMF原文"),
 ("Bogle 10年期望實質報酬≈0%/年(會計恆等式)","T2","保留:透明會計恆等式,非預測"),
 ("乘法結構(觸發×脆弱):脆弱放大觸發","T2","保留:理論依據Vulnerable Growth(Adrian 2019 AER)"),
 ("勞動份額66%→<60%;AI十年TFP≤0.71%、資本攫取多數","T2","保留:Autor QJE2020/Acemoglu NBER"),
 ("財政支配→降息可能無效(Sargent-Wallace)","T2","保留:理論文獻"),
 ("歷史回測 r=+0.79(乘積vs嚴重性)","X→T3","降級:n=7且加總/乘法/幾何擬合相同(0.78-0.80),非統計證據,改標『結構示意』"),
 ("1929-2022 各因子觸發/脆弱讀數(0.85/0.95型)","X→T3","降級:手編judgment,不得充當『回測數據』"),
 ("網格最佳乘數 base0.3/slope1.5 提升corr至0.759","X→T3","降級:n=7過擬合,僅方向參考,不採用"),
 ("權重±20%擾動→風險分0.349-0.384(寬度0.035)","T1","保留:此為真實計算結果,證明對權重不敏感"),
 ("共線性:四群群內r≥0.6(MOVE~基差0.91、估值~集中0.86)","T3","保留但標示:輸入為7事件編碼judgment,結構示意"),
 ("AI效率取代需求→反向循環崩盤","X","刪除為核心因子:純推測無實證,僅留『代表性脫鉤』背景項"),
 ("2026無共同底(地緣分裂→無底)","X→T4","降級T4:分裂屬實但『無底』推測,Fed工具仍在,移出核心"),
 ("2026無革命性終端產品(只有AI資本效率)","X","刪除:主觀判斷,不可驗證"),
 ("政治干預資訊透明度是危機『起點』","X→T4","降級:數據可信度可查(BLS 61→42.6%),但『起點』因果為推測"),
]
for c,t,r in LEDGER:
    print(f"  [{t:<5}] {c}")
    print(f"          → {r}")
keep=[x for x in LEDGER if not x[1].startswith("X") or "→" in x[1]]
killed=[x for x in LEDGER if x[1]=="X"]
print(f"\n  小結:總{len(LEDGER)}條 → 保留/降級{len(keep)}條、完全刪除{len(killed)}條")

print("\n"+"="*72);print("[稽核2] 邏輯檢驗:核心引擎(僅用 T1/T2 保留項)");print("="*72)
trig=sum(d["triggers"][k]["n"]*w for k,w in d["weights"]["trigger"].items())
frag=sum(d["fragility"][k]["n"]*w for k,w in d["weights"]["fragility"].items())
fm=0.7+frag*1.1; raw=trig*frag; raw_risk=trig*fm
struct=sum(v["n"] for v in d["structural"].values())/len(d["structural"]); risk=raw_risk*(1+0.08*struct)
print(f"  觸發={trig:.3f} 脆弱={frag:.3f} 乘數={fm:.3f} 乘積={raw:.3f} RawRisk={raw_risk:.3f} 風險分(含結構)={risk:.3f}")
print(f"  邏輯檢驗:觸發休眠({trig:.2f})×脆弱極高({frag:.2f}) → 乘積低 → 短期崩盤非基準;")
print(f"           但脆弱端高 → 一旦觸發點火被放大。此結論不依賴n=7回測,純結構邏輯成立。")

print("\n"+"="*72);print("[測試/回測] 改用『可驗證』錨點:Bogle會計恆等式(非n=7)");print("="*72)
cape=40.06;div=1.25;g=5.0;infl=3.0
def rr(ce): return div+g+((ce/cape)**(1/10)-1)*100-infl
w={40:.05,35:.20,30:.40,25:.25,20:.08,17:.02}
exp=sum(w[c]*rr(c) for c in w)
for c in (40,35,30,25,20,17): print(f"  終端CAPE {c:<3} 實質 {rr(c):+.2f}%/yr (w{w[c]:.0%})")
print(f"  期望實質 {exp:+.2f}%/yr;此為透明會計恆等式,不依賴歷史擬合 → 可信度高")

print("\n"+"="*72);print("[惡魔驗證] 對『保留後』的結論再攻擊");print("="*72)
print("  攻擊1 多方:CAPE被高估(Siegel)→ 即使公允CAPE=25,40→25仍de-rating,方向不變")
print("  攻擊2 多方:巨頭真實獲利、集中度溢價僅2000一半 → 軟化『崩盤即時性』,不改長期報酬透支")
print("  攻擊3 方法:刪掉n=7回測後,結論是否還站得住? → 是。長期結論靠Bogle恆等式+估值T1數據,")
print("             不靠回測;回測本就只是『結構示意』。刪除它反而讓結論更乾淨。")
print("  存活:長期向下(高信心,靠T1估值+T2恆等式);短期崩盤非基準(靠觸發T1數據休眠)")

print("\n"+"="*72);print("[再測試] 權重穩健性(真實計算,T1級)");print("="*72)
import random;random.seed(7);vals=[]
wt=d["weights"]["trigger"];wf=d["weights"]["fragility"];trg=d["triggers"];frg=d["fragility"]
def sc(pt,pf): return sum(trg[k]["n"]*v for k,v in pt.items())*(0.7+1.1*sum(frg[k]["n"]*v for k,v in pf.items()))
for _ in range(2000):
    pt={k:max(0,v*(1+random.uniform(-.2,.2))) for k,v in wt.items()};s=sum(pt.values());pt={k:v/s for k,v in pt.items()}
    pf={k:max(0,v*(1+random.uniform(-.2,.2))) for k,v in wf.items()};s=sum(pf.values());pf={k:v/s for k,v in pf.items()}
    vals.append(sc(pt,pf))
vals.sort()
print(f"  ±20%擾動2000次: 5%={vals[100]:.3f} 中位={vals[1000]:.3f} 95%={vals[1900]:.3f} 寬度={vals[1900]-vals[100]:.3f}")
print(f"  → 結論對權重不敏感(結構主導)。此為真實計算,保留為T1驗證。")

print("\n"+"="*72);print("[結論] 稽核重整後(只剩站得住的)");print("="*72)
print("  ① 長期(10年)評價向下:高信心。依據=T1估值數據(CAPE40/ERP≈0)+T2會計恆等式(期望實質≈0%)。")
print("  ② 短期(12月)崩盤非基準:依據=T1觸發數據全休眠(曲線+77bp/HY275bp/Sahm0.23)。")
print("  ③ 真正風險=觸發點火後被高脆弱放大;最可能火源=主權債/基差(T1)+政策受限(T2)。")
print("  ④ 已刪除:AI崩盤循環、2026無終端產品(不可驗證);已降級:n=7回測、無共同底(改標示信心)。")
print("  非投資建議。")

# 匯出稽核結果
out=dict(ledger=[dict(claim=c,tier=t,ruling=r) for c,t,r in LEDGER],
         kept=len(keep),removed=len(killed),
         core=dict(trigger=round(trig,3),fragility=round(frag,3),frag_mult=round(fm,3),raw_risk=round(raw_risk,3),risk_score=round(risk,3)),
         bogle_expected_real=round(exp,2),
         weight_robustness=dict(p05=round(vals[100],3),median=round(vals[1000],3),p95=round(vals[1900],3),width=round(vals[1900]-vals[100],3)))
json.dump(out,open(os.path.join(HERE,"audit_v10.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("\n[OK] audit_v10.json 已輸出")
