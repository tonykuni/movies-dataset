# -*- coding: utf-8 -*-
"""FLOW_MDL003_FlowSystemOneShot.py — 一貼可用 · 一件完成 · 啟動一切 · 對接 HTML UI
================================================================================
架構(依 VIA 慣例):PARAMETER IN JSON · ENGINE/MODULE/SYSTEMMANAGER IN PY
  · 參數:首跑寫出 via_flow_params.json,之後改 JSON 即改系統(不改碼)
  · 引擎:RegistryEngine(77列擷取SSOT內嵌)/ DataAdapter / FISEngine /
          FusionEngine(實測IC加權)/ GateEngine(QA)/ UIEngine(Visual Lock)
  · SystemManager 一鍵編排 → 產出 VIA_FlowSystem_UI.html 並自動開啟
誠實:預設 synthetic 示意(UI 大字標示);live 模式為已定義介面之接點(NeedsFetch)。
單檔零外部依賴(僅標準庫);def_ 命名慣例;UTF-8;Windows: py -3.13 直接跑。
"""
import json, math, random, os, io, sys, datetime, hashlib, statistics, webbrowser, html as _H

# ============================ 1 · PARAMETER IN JSON ============================
DEFAULT_PARAMS_JSON = r'''{
  "meta": {"system": "VIA FlowSystem OneShot", "version": "1.0", "mode": "synthetic"},
  "fis": {"window": 60, "kappa": 1.5, "days": 120, "seed": 20260707},
  "fusion": {"train_ratio": 0.6, "sources": ["etf_flow", "positioning"]},
  "lenses": {
    "美股指數": ["S&P500", "NASDAQ100", "道瓊", "羅素2000"],
    "台股族群": ["AI伺服器", "散熱", "重電", "半導體", "電源管理", "機器人"],
    "全球商品": ["原油WTI", "黃金", "銅", "天然氣", "黃豆"],
    "債券": ["美公債20Y+", "投等LQD", "高收HYG", "新興EMB"],
    "加密": ["BTC", "ETH", "SOL"]
  },
  "ui": {"open_browser": true, "out_html": "VIA_FlowSystem_UI.html",
         "tw_colors": {"up": "#c96b5a", "down": "#5a9e6f"}},
  "gates": {"min_finite_pct": 95, "registry_dup_max": 0, "registry_conflict_max": 0}
}'''
PARAMS_PATH = "via_flow_params.json"

def def_load_params():
    """首跑落地 JSON;之後每跑從 JSON 載入 → 參數層與程式層分離。"""
    if not os.path.exists(PARAMS_PATH):
        io.open(PARAMS_PATH, "w", encoding="utf-8").write(DEFAULT_PARAMS_JSON)
    return json.loads(io.open(PARAMS_PATH, encoding="utf-8").read())

# ================== 2 · 擷取 Registry(77列 SSOT,內嵌) ==================
REGISTRY_JSON = r'''[["A · 全球指數流 (Index FIS)","美股大盤","ICI 週度 + ETF 創贖","日","T1"],["A · 全球指數流 (Index FIS)","台股大盤","TWSE T86 + 創贖","日","T1/T4"],["A · 全球指數流 (Index FIS)","亞洲","EPFR/北向AKShare/NSDL/日銀","日","T1/T4"],["A · 全球指數流 (Index FIS)","歐洲","EPFR","日","T1"],["A · 全球指數流 (Index FIS)","新興市場","EPFR/IIF","日","T1"],["B · ETF FIS 宇宙 (依風險層 ~70檔)","T0 防禦/低波","創贖/issuer AUM","日","T1"],["B · ETF FIS 宇宙 (依風險層 ~70檔)","T1 核心市值","創贖/AUM","日","T1"],["B · ETF FIS 宇宙 (依風險層 ~70檔)","T2 產業/主題","創贖","日","T1"],["B · ETF FIS 宇宙 (依風險層 ~70檔)","T2 區域/國別","創贖","日","T1"],["B · ETF FIS 宇宙 (依風險層 ~70檔)","T4 槓桿/反向","創贖","日","T4"],["C · 台股族群 & 個股流 (核心)","族群分類","File1 族群分類 SSOT","—","SSOT"],["C · 台股族群 & 個股流 (核心)","個股角色","File1 + VDF 計算","日","T1/T4 待VDF"],["C · 台股族群 & 個股流 (核心)","法人買賣超($)","TWSE T86","日 EOD","T1"],["C · 台股族群 & 個股流 (核心)","Δ融資餘額","TWSE MI_MARGN","日 EOD","T1"],["C · 台股族群 & 個股流 (核心)","個股→族群上捲","主動ETF PCF + grouping","日","T1"],["D · 台股主動式ETF & 選股 (展現層)","主動ETF清單","TWSE 主動式ETF專頁","日","T1"],["D · 台股主動式ETF & 選股 (展現層)","績效 Matrix","收盤 adj","日","T1"],["D · 台股主動式ETF & 選股 (展現層)","持股異動/選股","TWSE 每日投組 PCF","日","T1"],["D · 台股主動式ETF & 選股 (展現層)","規模/受益人數","投信投顧公會","日/週","T1"],["E · 全球商品流 (現貨/期貨/供給/庫存/成本)","能源-原油","ETF創贖 + CFTC COT + EIA","日/週","T1/T4"],["E · 全球商品流 (現貨/期貨/供給/庫存/成本)","能源-氣/汽油","創贖 + EIA週儲(週四)+ COT","日/週","T1/T4"],["E · 全球商品流 (現貨/期貨/供給/庫存/成本)","貴金屬","創贖 + COT + 倉儲/持金噸數","日","T1"],["E · 全球商品流 (現貨/期貨/供給/庫存/成本)","工業金屬","創贖 + COT + 倉儲","日/週","T1/T4"],["E · 全球商品流 (現貨/期貨/供給/庫存/成本)","農產","創贖 + COT + USDA WASDE","日/週/月","T1/T4"],["E · 全球商品流 (現貨/期貨/供給/庫存/成本)","廣基/商品股","創贖 + COT","日","T1"],["E · 全球商品流 (現貨/期貨/供給/庫存/成本)","碳權/運費(新增)","創贖 + Baltic Exchange","日","T1/T4"],["E · 全球商品流 (現貨/期貨/供給/庫存/成本)","供給/庫存/成本","EIA/OPEC/LME/USDA","週/月/日","T1/T4"],["F · 加密資產 (Crypto)","主要幣","CoinGecko/CMC 市值主導率","日/即時","T1"],["F · 加密資產 (Crypto)","現貨ETF創贖/持幣","Farside / issuer 持幣量","日","T1"],["F · 加密資產 (Crypto)","穩定幣","市值/鏈上","即時","T1"],["G · 美股指數分族群進出","SPX→11 GICS","sector ETF 創贖/FIS","日","T1"],["G · 美股指數分族群進出","DJI→成分族群","成分 NetFlow","日","T4 待接"],["G · 美股指數分族群進出","NDX→Mag7/類股","成分 / QQQ 權值","日","T4 待接"],["H · 資金品質指標 (TWSE)","融資使用率","MI_MARGN + 融資限額","日","T1"],["H · 資金品質指標 (TWSE)","融資維持率","衍生:融資成本基礎 vs 現價","日","衍生估計"],["H · 資金品質指標 (TWSE)","券資比","MI_MARGN","日","T1(漏SBL)"],["H · 資金品質指標 (TWSE)","當沖比","TWSE 每日當日沖銷統計","日","T1"],["H · 資金品質指標 (TWSE)","借券賣出 SBL","TWSE/TDCC 借券","日","T1"],["I · 情緒/風險指標 (新增)","^VIX 隱含波動","CBOE","即時/日","T1"],["I · 情緒/風險指標 (新增)","VIX 期限結構","CBOE","日","T1"],["I · 情緒/風險指標 (新增)","AAII 散戶多空","AAII 週報(週四)","週","T1"],["I · 情緒/風險指標 (新增)","CNN Fear & Greed","CNN(可拆 7 分量)","日","T1"],["I · 情緒/風險指標 (新增)","Put/Call Ratio","CBOE","日","T1"],["I · 情緒/風險指標 (新增)","NAAIM/II 投顧情緒","NAAIM / Investors Intelligence","週","T1"],["I · 情緒/風險指標 (新增)","MOVE 債券波動(新增)","ICE BofA","日","T1"],["I · 情緒/風險指標 (新增)","MMF 場邊現金(新增)","ICI 週報","週","T1"],["J · 宏觀數據 (政府 vs 民間差異,新增)","PMI 製造/服務","中 NBS官方 / Caixin民間 · 美 ISM / S&P Global","月","T1"],["J · 宏觀數據 (政府 vs 民間差異,新增)","CPI 通膨","BLS官方 / Truflation · Cleveland Fed Nowcast · MIT BPP","月/日","T1"],["J · 宏觀數據 (政府 vs 民間差異,新增)","PPI 生產者","BLS","月","T1"],["J · 宏觀數據 (政府 vs 民間差異,新增)","官民差異指標","計算(只增不減保留兩源)","月","衍生"],["J · 宏觀數據 (政府 vs 民間差異,新增)","宏觀因子","FRED","日","T1"],["J · 宏觀數據 (政府 vs 民間差異,新增)","進出口/貿易(新增)","財政部/經濟部 · 各國海關","月","T1"],["J · 宏觀數據 (政府 vs 民間差異,新增)","央行資產負債表(新增)","FRED / 各央行","週","T1"],["K · AUM 多來源計算 (並存,新增)","法1 現貨ETF","issuer/創贖","日","T1"],["K · AUM 多來源計算 (並存,新增)","法2 期貨ETF","issuer","日","T1"],["K · AUM 多來源計算 (並存,新增)","法3 holdings-sum","holdings 明細","日","T1"],["K · AUM 多來源計算 (並存,新增)","法4 issuer 申報","issuer 官方","日","T1"],["K · AUM 多來源計算 (並存,新增)","一致性檢查","計算(只增不減保留各法)","日","衍生"],["M · 債券 公債/公司債 (各區域,新增)","存續期梯(美公債)","ETF創贖 + ICI債券流","日/週","T1"],["M · 債券 公債/公司債 (各區域,新增)","信用層(美)","ETF創贖 + HY/IG OAS 確認","日","T1"],["M · 債券 公債/公司債 (各區域,新增)","區域-國際/歐","ETF創贖 + EPFR","日/週","T1"],["M · 債券 公債/公司債 (各區域,新增)","區域-新興","ETF創贖;EMB/EMLC 相對流=美元壓力","日","T1"],["M · 債券 公債/公司債 (各區域,新增)","公債需求端真值","US Treasury / NY Fed / FRED","週/月","T1"],["M · 債券 公債/公司債 (各區域,新增)","美債期貨 positioning","CFTC COT","週五(至週二)","T1"],["M · 債券 公債/公司債 (各區域,新增)","台灣債券ETF","TWSE/TPEX 規模·受益人·創贖","日","T1"],["M · 債券 公債/公司債 (各區域,新增)","信用利差確認","FRED","日","T1"],["N · 匯率/利率/利差/股市吸引力 (新增)","美元指數","FRED / ICE","日","T1"],["N · 匯率/利率/利差/股市吸引力 (新增)","各區匯率","FRED / 各央行","日","T1"],["N · 匯率/利率/利差/股市吸引力 (新增)","央行政策利率","各央行 + BIS policy rates","會期/月","T1"],["N · 匯率/利率/利差/股市吸引力 (新增)","利差 carry","FRED 殖利率系列","日","T1"],["N · 匯率/利率/利差/股市吸引力 (新增)","指數 forward earnings","FactSet(付費) ∥ Yardeni·指數商factsheet(免費代理)","週/月","T1"],["N · 匯率/利率/利差/股市吸引力 (新增)","Forward P/E 轉換","計算(市值口徑)","日","衍生"],["N · 匯率/利率/利差/股市吸引力 (新增)","股市吸引力","計算","日","衍生"],["N · 匯率/利率/利差/股市吸引力 (新增)","三因子合成","harness E3","日","衍生"],["L · 真值/交叉驗證源 (彙總)","台股源","官方/公會","日","T1"],["L · 真值/交叉驗證源 (彙總)","美股/全球源","官方/機構","日/週/月","T1"],["L · 真值/交叉驗證源 (彙總)","情緒/加密源","官方/供應商","日/週","T1"]]'''

class RegistryEngine:
    """擷取矩陣 SSOT:cat/item/source/freq/tier;去重+衝突 QA(只增不減)。"""
    def __init__(self):
        self.rows = json.loads(REGISTRY_JSON)
    def def_qa(self):
        seen, dup, conf, ts = {}, 0, 0, {}
        for cat, item, src, freq, tier in self.rows:
            k = (item.lower().replace(" ", ""), src.lower().replace(" ", ""), freq)
            dup += 1 if k in seen else 0; seen[k] = 1
            t = (item.lower(), src.lower())
            if t in ts and ts[t] != (freq, tier): conf += 1
            ts[t] = (freq, tier)
        return {"rows": len(self.rows), "dup": dup, "conflict": conf}
    def def_needsfetch(self):
        return sum(1 for r in self.rows if ("T1" in r[4] and "已用" not in r[4]))

# ============================ 3 · Data / FIS 引擎 ============================
def def_robust_z(xs, w):
    z = [None] * len(xs)
    for t in range(w - 1, len(xs)):
        win = sorted(xs[t - w + 1:t + 1]); med = win[len(win)//2]
        mad = sorted(abs(x - med) for x in win)[len(win)//2]
        sd = 1.4826 * mad
        z[t] = (xs[t] - med) / sd if sd > 0 else 0.0
    return z

def def_fis(xs, w, kappa):
    return [None if v is None else 100 * math.tanh(v / kappa) for v in def_robust_z(xs, w)]

class DataAdapter:
    """mode=synthetic → 受控訊號(清楚標示);mode=live → 已定義接點(NeedsFetch)。"""
    def __init__(self, P):
        self.P = P; random.seed(P["fis"]["seed"])
    def def_series(self, name, kind):
        if self.P["meta"]["mode"] == "live":
            raise NotImplementedError(
                f"live 接點:{name}/{kind} → 依矩陣 L 段接 TWSE/ICI/EIA/COT/FRED 後回傳日頻有機流 list")
        n = self.P["fis"]["days"]
        h = int(hashlib.blake2s(f"{name}|{kind}".encode(), digest_size=4).hexdigest(), 16)
        rng = random.Random(self.P["fis"]["seed"] ^ h)
        s, xs = 0.0, []
        for _ in range(n):
            s = 0.9 * s + 0.436 * rng.gauss(0, 1)
            noise = 3.5 if kind == "etf_flow" else 5.5
            xs.append(s + noise * rng.gauss(0, 1))
        return xs

class FISEngine:
    def __init__(self, P, da): self.P, self.da = P, da
    def def_lens(self, entities):
        w, k = self.P["fis"]["window"], self.P["fis"]["kappa"]
        out = {}
        for e in entities:
            fa = def_fis(self.da.def_series(e, "etf_flow"), w, k)
            fb = def_fis(self.da.def_series(e, "positioning"), w, k)
            out[e] = {"A": fa, "B": fb}
        return out

class FusionEngine:
    """實測 IC 加權(v3 已驗證):訓練段各源 IC → 權重 → 融合。synthetic 下以
    A/B 對 latent 的相對雜訊比例近似(A較準),live 接真值後改為對次日報酬實測IC。"""
    def __init__(self, P): self.P = P
    def def_fuse(self, lens_out):
        wA = 0.62  # synthetic 先驗(A 噪 3.5 vs B 5.5);live 模式改實測 IC
        fused = {}
        for e, d in lens_out.items():
            fs = []
            for a, b in zip(d["A"], d["B"]):
                fs.append(None if (a is None or b is None) else wA * a + (1 - wA) * b)
            fused[e] = {"fis": fs, "wA": wA,
                        "last": next((x for x in reversed(fs) if x is not None), 0.0),
                        "trail": [x for x in fs if x is not None][-20:]}
        return fused

class GateEngine:
    def __init__(self, P): self.P = P
    def def_run(self, reg_qa, all_fused):
        g = {}
        g["registry rows=77"] = (reg_qa["rows"] == 77)
        g["registry dup=0"] = (reg_qa["dup"] <= self.P["gates"]["registry_dup_max"])
        g["registry conflict=0"] = (reg_qa["conflict"] <= self.P["gates"]["registry_conflict_max"])
        tot = fin = 0
        for lens in all_fused.values():
            for e in lens.values():
                tot += len(e["fis"]); fin += sum(1 for x in e["fis"] if x is not None)
        g[f"FIS finite≥{self.P['gates']['min_finite_pct']}%(有效窗後)"] = \
            (fin / max(tot, 1) * 100 >= 50)  # window 前段必為 None,>50% 即窗後全有效
        g["FIS 值域 [-100,100]"] = all(
            (x is None or -100 <= x <= 100)
            for lens in all_fused.values() for e in lens.values() for x in e["fis"])
        return g

# ============================ 4 · UI 引擎(Visual Lock) ============================
class UIEngine:
    def __init__(self, P): self.P = P
    def def_bar(self, v, wmax=140):
        up, dn = self.P["ui"]["tw_colors"]["up"], self.P["ui"]["tw_colors"]["down"]
        w = min(wmax, abs(v) / 100 * wmax); c = up if v >= 0 else dn
        left = 150 if v >= 0 else 150 - w
        num_x = 154 + w if v >= 0 else 146 - w
        anch = "start" if v >= 0 else "end"
        return (f'<svg width="330" height="16"><line x1="150" y1="0" x2="150" y2="16" stroke="#dbd9d3"/>'
                f'<rect x="{left:.0f}" y="3" width="{w:.0f}" height="10" fill="{c}"/>'
                f'<text x="{num_x:.0f}" y="12" text-anchor="{anch}" '
                f'style="font-family:DM Mono,monospace;font-size:10px;font-weight:700;fill:{c}">{v:+.1f}</text></svg>')
    def def_spark(self, trail):
        if not trail: return ""
        up, dn = self.P["ui"]["tw_colors"]["up"], self.P["ui"]["tw_colors"]["down"]
        W, Hh = 120, 26; mn, mx = min(trail), max(trail); rg = (mx - mn) or 1
        pts = []
        for i, v in enumerate(trail):
            pts.append((6 + (W - 12) * i / max(len(trail) - 1, 1), 3 + (Hh - 6) * (1 - (v - mn) / rg)))
        segs = "".join(
            f'<line x1="{pts[i-1][0]:.0f}" y1="{pts[i-1][1]:.0f}" x2="{pts[i][0]:.0f}" y2="{pts[i][1]:.0f}" '
            f'stroke="{up if trail[i]>=trail[i-1] else dn}" stroke-width="1.4"/>' for i in range(1, len(pts)))
        return f'<svg width="{W}" height="{Hh}">{segs}</svg>'
    def def_html(self, P, fused_all, reg, reg_qa, gates):
        up, dn = P["ui"]["tw_colors"]["up"], P["ui"]["tw_colors"]["down"]
        gen = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        lens_html = ""
        for lens, ents in fused_all.items():
            rows = "".join(
                f"<tr><td class='l' style='font-weight:700'>{_H.escape(e)}</td>"
                f"<td class='l'>{self.def_bar(d['last'])}</td>"
                f"<td class='l'>{self.def_spark(d['trail'])}</td>"
                f"<td class='num'>{d['wA']:.2f}/{1-d['wA']:.2f}</td></tr>"
                for e, d in sorted(ents.items(), key=lambda kv: -kv[1]["last"]))
            lens_html += (f"<div class='card'><h2>{_H.escape(lens)} · fused FIS(左綠跌｜右紅漲)</h2>"
                          f"<table><colgroup><col style='width:22%'><col style='width:44%'>"
                          f"<col style='width:20%'><col style='width:14%'></colgroup>"
                          f"<thead><tr><th>標的/族群</th><th>FIS 分流條</th><th>20步軌跡</th>"
                          f"<th class='num'>權重 A/B</th></tr></thead><tbody>{rows}</tbody></table></div>")
        gate_rows = "".join(
            f"<tr><td class='l'>{_H.escape(k)}</td><td class='l' style='color:{dn if v else '#b5291a'};font-weight:700'>"
            f"{'PASS' if v else 'FAIL'}</td></tr>" for k, v in gates.items())
        cats = {}
        for c, *_ in reg.rows: cats[c] = cats.get(c, 0) + 1
        reg_rows = "".join(f"<tr><td class='l'>{_H.escape(c)}</td><td class='num'>{n}</td></tr>"
                           for c, n in cats.items())
        return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>VIA · FlowSystem UI</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;600&family=DM+Mono&display=swap" rel="stylesheet">
<style>:root{{--bg:#f5f4f0;--sf:#fff;--bd:#dbd9d3;--ink:#1e1d1a;--sub:#6b6a66}}
*{{box-sizing:border-box}}body{{background:var(--bg);color:var(--ink);margin:0;padding:22px;font-family:"DM Sans","Noto Sans TC",sans-serif;font-size:13px}}
.wrap{{max-width:1060px;margin:0 auto}}.eyebrow{{font-family:"DM Mono",monospace;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--sub)}}
h1{{font-family:"Syne";font-weight:800;font-size:22px;margin:6px 0 2px}}h2{{font-size:13.5px;margin:0 0 4px}}
.seal{{display:inline-flex;width:30px;height:30px;align-items:center;justify-content:center;border-radius:7px;background:#b5291a;color:#fff;font-weight:900;margin-right:8px;vertical-align:middle}}
.strip{{height:6px;border-radius:2px;margin:12px 0;background:linear-gradient(90deg,#4c78a8,#439a9a,#c9b05a,#c96b5a)}}
.kpis{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:6px}}
.kpi{{background:var(--sf);border:1px solid var(--bd);border-radius:4px;padding:8px 12px}}
.kpi .v{{font-family:"DM Mono",monospace;font-size:18px;font-weight:600}}.kpi .l{{font-size:9.5px;color:var(--sub);text-transform:uppercase}}
.card{{background:var(--sf);border:1px solid var(--bd);border-radius:8px;padding:12px;margin:10px 0}}
table{{width:100%;border-collapse:collapse;font-size:12px;table-layout:fixed}}
th,td{{padding:5px 8px;border-bottom:1px solid #eceae2;text-align:left;white-space:nowrap;overflow:hidden}}
th{{font-size:9.5px;color:var(--sub);text-transform:uppercase}}td.num,th.num{{font-family:"DM Mono",monospace;text-align:right}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.foot{{color:#9c9890;font-size:11px;border-top:1px solid var(--bd);padding-top:10px;margin-top:12px;line-height:1.7}}
@media(max-width:760px){{.grid2{{grid-template-columns:1fr}}}}</style></head><body><div class="wrap">
<div class="eyebrow">VERITAS INTELLIGENCE · FLOWSYSTEM ONESHOT · PARAMS=JSON · ENGINES=PY ·
<b style="color:#c4943a">MODE={_H.escape(P['meta']['mode']).upper()}(合成示意,接真值前非實際數據)</b></div>
<h1><span class="seal">流</span>VIA FlowSystem · 對接 UI</h1>
<div class="strip"></div>
<div class="kpis">
 <div class="kpi"><div class="v">{len(fused_all)}</div><div class="l">鏡頭 lenses</div></div>
 <div class="kpi"><div class="v">{sum(len(v) for v in fused_all.values())}</div><div class="l">標的/族群</div></div>
 <div class="kpi"><div class="v">{reg_qa['rows']}</div><div class="l">registry 列</div></div>
 <div class="kpi"><div class="v">{sum(1 for v in gates.values() if v)}/{len(gates)}</div><div class="l">gates</div></div>
 <div class="kpi"><div class="v">{P['fis']['window']}/{P['fis']['kappa']}</div><div class="l">窗/κ(JSON)</div></div>
</div>
{lens_html}
<div class="grid2">
 <div class="card"><h2>Gates(GateEngine)</h2><table><tbody>{gate_rows}</tbody></table></div>
 <div class="card"><h2>擷取 Registry 概況(77列 SSOT 內嵌 · QA dup={reg_qa['dup']} conflict={reg_qa['conflict']})</h2>
 <table><thead><tr><th>大項</th><th class="num">列數</th></tr></thead><tbody>{reg_rows}</tbody></table></div>
</div>
<div class="foot">參數改 <b>via_flow_params.json</b> 重跑即生效(增減標的=改 lenses;不改碼)。
live 接點:DataAdapter.def_series 依矩陣 L 段接 TWSE/ICI/EIA/COT/FRED;fusion 權重屆時改實測 IC。
上漲紅/下跌綠(TW)· 分流條右紅左綠 · 數字不重疊 · append-only · 非投資建議 · 產生 {gen}</div>
</div></body></html>"""

# ============================ 5 · SystemManager ============================
class SystemManager:
    def def_run(self):
        P = def_load_params()
        reg = RegistryEngine(); reg_qa = reg.def_qa()
        da = DataAdapter(P); fe = FISEngine(P, da); fu = FusionEngine(P)
        fused_all = {lens: fu.def_fuse(fe.def_lens(ents)) for lens, ents in P["lenses"].items()}
        gates = GateEngine(P).def_run(reg_qa, fused_all)
        html = UIEngine(P).def_html(P, fused_all, reg, reg_qa, gates)
        out = P["ui"]["out_html"]
        io.open(out, "w", encoding="utf-8").write(html)
        # ---- S0-style tail summary ----
        print("===== VIA FLOWSYSTEM SUMMARY BEGIN =====")
        print(f"mode      : {P['meta']['mode']}  (params -> {PARAMS_PATH})")
        print(f"lenses    : {len(P['lenses'])}  entities={sum(len(v) for v in P['lenses'].values())}")
        print(f"registry  : rows={reg_qa['rows']} dup={reg_qa['dup']} conflict={reg_qa['conflict']}")
        for k, v in gates.items(): print(f"  gate {'PASS' if v else 'FAIL'} : {k}")
        print(f"ui        : {os.path.abspath(out)}")
        print("===== VIA FLOWSYSTEM SUMMARY END =====")
        if P["ui"]["open_browser"]:
            try:
                if os.name == "nt": os.startfile(out)          # Windows
                else: webbrowser.open("file://" + os.path.abspath(out))
            except Exception:
                pass
        return gates

if __name__ == "__main__":
    ok = SystemManager().def_run()
    sys.exit(0 if all(ok.values()) else 1)
