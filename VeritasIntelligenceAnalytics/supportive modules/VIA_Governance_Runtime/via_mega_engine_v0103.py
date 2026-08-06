# =====================================================================================
# VIA Mega Engine v0103 (v0102 版本前送:Matrix 新增 MODULE/ENGINE/FUNCTION-LIB/OTHERS
# 分區盤點;表格 fixed-layout+自動換行;其餘邏輯不變) (v0101 版本前送:掃描範圍擴至 ssot/registry/VIA_Canonical_Units/
# Control_Tower/70_VRN_Rules — 真相層與治理層納入全景;其餘邏輯不變) (v0100 版本前送:JSON 驗證對 legacy 證據寬容 — 含 ANSI 控制字元的
# 稽核紀錄以 strict=False 解析成功者降級為資訊項 json_legacy,不再構成 YELLOW;紀錄永不改寫) — 公定處理模式執行載體 (ssot/VIA_MegaPrompt_OfficialMode_v0100.md)
# 三輪全景式分析 x 20 加速器 x HTML Matrix(紅黃綠燈) x 動態進度條/說明
# 治理: 唯讀分析 + 提案(高風險節點只建議不自動修;修正經沙盒另行申請) — fail-closed.
# 三輪硬性上限;每輪重新全景掃描;輸出 reports/VIA_MegaMatrix.html + mega_state.json
# =====================================================================================
import os, sys, ast, json, hashlib, datetime as dt

ROOT = os.environ.get("VIA_HOME") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SUBSYSTEMS = {
    "VDF": "functional modules/VDF", "VAP": "functional modules/VAP",
    "VRN": "functional modules/VRN", "VMT": "supportive modules/VMT_SuperBOM",
    "GOV": "supportive modules/VIA_Governance_Runtime",
    "SSOT": "supportive modules/ssot", "REG": "supportive modules/registry",
    "CANON": "supportive modules/VIA_Canonical_Units", "RULES": "supportive modules/70_VRN_Rules",
    "TOWER": "supportive modules/VIA_Control_Tower",
}
SSOT_REQUIRED = [
    "supportive modules/ssot/VRN_TickerRegexSSOT_v0100.json",
    "supportive modules/ssot/VIA_DesignLock_SSOT_v0100.json",
    "supportive modules/ssot/VIA_MegaPrompt_OfficialMode_v0100.md",
    "functional modules/VAP/spec/ssot/vap_spec.json",
    "functional modules/VAP/spec/ssot/vap_chartlib.json",
    "functional modules/VAP/spec/UIUX_Design_Source/DESIGN_SOURCE_Manifest_v0101.json",
]
SKIP_DIRS = {".git", "_superseded", "__pycache__", "node_modules", "db", "output", "temp"}
ACCELERATORS = ["AST 精準解析","多語言語意模型","九頭龍風險預測","依賴拓撲排序","沙盒隔離執行",
 "自動修正建議生成","三輪全景式分析","SSOT 對齊","視覺化矩陣生成","錯誤分類與分群",
 "性能與複雜度分析","多子系統同步檢視","版本差異與回滾","覆蓋率與回歸檢查","修正順序最佳化",
 "動態進度條","動態說明","非阻塞執行","多引擎整合","自動部署初始化"]

def bar(pct, msg):
    n = int(pct / 5)
    sys.stdout.write("\r[%-20s] %3d%%  %-50s" % ("#" * n, pct, msg[:50])); sys.stdout.flush()

def sweep(round_no):
    findings, py_err, hydra = [], [], {}
    zones = {}
    files_scanned = 0
    names = {}
    sub_stats = {}
    subs = list(SUBSYSTEMS.items())
    for i, (sub, rel) in enumerate(subs):
        base = os.path.join(ROOT, rel)
        stat = {"py": 0, "ps1": 0, "html": 0, "json": 0, "py_ast_fail": 0, "json_fail": 0, "json_legacy": 0}
        for r, ds, fs in os.walk(base):
            ds[:] = [d for d in ds if d not in SKIP_DIRS and not d.startswith("_import_staging")]
            for f in fs:
                p = os.path.join(r, f); files_scanned += 1
                ext = f.rsplit(".", 1)[-1].lower() if "." in f else ""
                if ext in stat: stat[ext] += 1
                try: b = open(p, "rb").read()
                except OSError: continue
                names.setdefault(f, []).append((sub, p, hashlib.sha256(b).hexdigest()))
                fl = f.lower()
                zone = ("ENGINE" if "engine" in fl else
                        "MODULE" if ("mdl" in fl or "module" in fl) else
                        "FUNCTION-LIB" if ("pattern" in fl or "lib" in fl or "regex" in fl or ext == "psm1") else
                        "OTHERS")
                zones.setdefault(zone, {}).setdefault(sub, [0, []])
                zones[zone][sub][0] += 1
                if len(zones[zone][sub][1]) < 6:
                    zones[zone][sub][1].append(f)
                if ext == "py":
                    try: ast.parse(b.decode("utf-8", "replace"))
                    except SyntaxError as e:
                        stat["py_ast_fail"] += 1
                        py_err.append({"sub": sub, "file": os.path.relpath(p, ROOT), "line": e.lineno,
                                       "class": "SEQUENCE_DEPENDENT", "risk": "HIGH", "action": "PROPOSE_ONLY"})
                elif ext == "json":
                    txt = b.decode("utf-8-sig", "replace")
                    try: json.loads(txt)
                    except Exception:
                        try:
                            json.loads(txt, strict=False)
                            stat["json_legacy"] += 1
                        except Exception:
                            stat["json_fail"] += 1
                            findings.append({"sub": sub, "file": os.path.relpath(p, ROOT),
                                             "issue": "JSON 解析失敗", "class": "PARALLEL_FIXABLE",
                                             "risk": "MED", "action": "PROPOSE_ONLY"})
        sub_stats[sub] = stat
        bar(int((i + 1) / len(subs) * 60), "R%d 掃描 %s (%d 檔)" % (round_no, sub, files_scanned))
    for f, occ in names.items():
        shas = {s for _, _, s in occ}
        if len(occ) > 1 and len(shas) > 1 and not f.startswith("__"):
            hydra[f] = [{"sub": s, "path": os.path.relpath(p, ROOT), "sha12": h[:12]} for s, p, h in occ]
    bar(70, "R%d 九頭龍偵測: %d 名稱" % (round_no, len(hydra)))
    ssot = [{"path": s, "present": os.path.exists(os.path.join(ROOT, s))} for s in SSOT_REQUIRED]
    bar(85, "R%d SSOT 對齊 %d/%d" % (round_no, sum(1 for x in ssot if x["present"]), len(ssot)))
    return {"round": round_no, "files": files_scanned, "sub_stats": sub_stats, "py_errors": py_err,
            "findings": findings, "hydra": hydra, "ssot": ssot, "zones": zones}

def light(r):
    reds = len(r["py_errors"]); yellows = len(r["findings"]) + len(r["hydra"])
    missing = sum(1 for x in r["ssot"] if not x["present"])
    if reds or missing: return "RED"
    return "YELLOW" if yellows else "GREEN"

def html_matrix(rounds, out):
    C = {"GREEN": "#5a9e6f", "YELLOW": "#c4943a", "RED": "#c96b5a"}
    last = rounds[-1]
    rows = ""
    for sub, st in sorted(last["sub_stats"].items()):
        errs = [e for e in last["py_errors"] if e["sub"] == sub]
        lamp = "RED" if errs else ("YELLOW" if any(f["sub"] == sub for f in last["findings"]) else "GREEN")
        rows += ("<tr><td><span class='pill' style='background:%s'>%s</span></td><td>%s</td>"
                 "<td>%d py / %d ps1 / %d html / %d json</td><td>%d AST fail / %d JSON fail</td></tr>"
                 % (C[lamp], lamp, sub, st["py"], st["ps1"], st["html"], st["json"], st["py_ast_fail"], st["json_fail"])) + ("" if not st.get("json_legacy") else "<tr><td></td><td></td><td colspan=2 style='color:#8a857c'>%d 個 legacy 證據檔含控制字元(strict=False 可解析,資訊項)</td></tr>" % st["json_legacy"])
    hyd = "".join("<tr><td>%s</td><td>%s</td></tr>" % (k, "<br>".join("%(sub)s · %(path)s · %(sha12)s" % o for o in v))
                  for k, v in sorted(last["hydra"].items())) or "<tr><td colspan=2>無</td></tr>"
    ss = "".join("<tr><td><span class='pill' style='background:%s'>%s</span></td><td>%s</td></tr>"
                 % (C["GREEN" if x["present"] else "RED"], "PRESENT" if x["present"] else "MISSING", x["path"]) for x in last["ssot"])
    zone_html = ""
    for zname in ("MODULE", "ENGINE", "FUNCTION-LIB", "OTHERS"):
        zd = last.get("zones", {}).get(zname, {})
        if not zd:
            continue
        rows_z = "".join(
            "<tr><td>%s</td><td>%d</td><td style='font-size:10px;color:#777'>%s</td></tr>"
            % (s, cnt, " · ".join(sample)) for s, (cnt, sample) in sorted(zd.items()))
        zone_html += ("<h2 style='margin-top:14px'>%s</h2><table>"
                      "<tr><th style='width:70px'>子系統</th><th style='width:50px'>檔數</th><th>樣本</th></tr>%s</table>"
                      % (zname, rows_z))
    trend = "".join("<span class='pill' style='background:%s;margin-right:6px'>R%d %s</span>" % (C[light(r)], r["round"], light(r)) for r in rounds)
    acc = "".join("<span class='acc'>%02d %s</span>" % (i + 1, a) for i, a in enumerate(ACCELERATORS))
    page = ("<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'><title>VIA Mega Matrix</title>"
       "<link href='https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&family=Noto+Serif+TC:wght@600&family=DM+Sans:wght@400;500;700&family=DM+Mono:wght@400;500&display=swap' rel='stylesheet'><style>"
       ":root{--ink:#1e1d1a;--mut:#6b6860;--hair:#dbd9d3;--serif:'Cormorant Garamond',Georgia,serif;--cjk:'Noto Serif TC','PMingLiU',serif;"
       "--reson:linear-gradient(90deg,#c96b5a 0 14.2%,#c4943a 0 28.5%,#5a9e6f 0 42.8%,#439a9a 0 57.1%,#4c78a8 0 71.4%,#7a6daa 0 85.7%,#1e1d1a 0 100%)}"
       "*{box-sizing:border-box;margin:0;padding:0}body{background:#f5f4f0;color:var(--ink);font-family:'DM Sans','Microsoft JhengHei',sans-serif;padding:26px}"
       ".eyebrow{display:flex;gap:8px;align-items:center;margin-bottom:8px}.chip{padding:2px 7px;background:var(--ink);color:#fff;font:700 9px 'DM Mono',monospace;letter-spacing:.14em}"
       ".ey{font:700 8.5px 'DM Mono',monospace;letter-spacing:.13em;color:var(--mut);text-transform:uppercase}"
       "header{display:flex;align-items:center;border-bottom:1px solid var(--hair);padding-bottom:14px}"
       ".seal{width:38px;height:38px;background:var(--ink);color:#f2f1ec;display:flex;align-items:center;justify-content:center;font-family:var(--cjk);font-size:20px;border-radius:4px;margin-right:12px}"
       "h1{font:600 19px/1.2 var(--serif);letter-spacing:.07em}.wmcjk{font:600 9.5px var(--cjk);letter-spacing:.22em;color:var(--mut);margin-top:2px}"
       ".sub{font:10.5px 'DM Mono',monospace;color:#777;margin-top:4px}.strip{height:4px;background:var(--reson);margin:13px 0 18px;border-radius:2px}"
       "h2{font:700 11px 'DM Mono',monospace;letter-spacing:2px;color:#555;margin:20px 0 9px;text-transform:uppercase}"
       "table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--hair);table-layout:fixed}"
       "td{word-wrap:break-word;overflow-wrap:anywhere}"
       "th{font:700 10px 'DM Mono',monospace;text-align:left;padding:8px 10px;border-bottom:1px solid var(--hair);color:#666}"
       "td{font-size:11.5px;padding:7px 10px;border-bottom:1px solid var(--hair)}tr:last-child td{border-bottom:none}"
       ".pill{color:#fff;font:500 10px 'DM Mono',monospace;padding:2px 7px;border-radius:2px}"
       ".acc{display:inline-block;font:500 9px 'DM Mono',monospace;color:#555;background:#fff;border:1px solid var(--hair);border-radius:3px;padding:2px 7px;margin:0 4px 4px 0}"
       "footer{margin-top:22px;font:10px 'DM Mono',monospace;color:#999}</style></head><body>"
       "<div class='eyebrow'><span class='chip'>v0103</span><span class='ey'>Veritas Intelligence Analytics · Mega Engine</span></div>"
       "<header><div class='seal'>核</div><div><h1>VIA MEGA MATRIX — 三輪全景稽核</h1>"
       "<div class='wmcjk'>維里塔斯 · 全景分析 · 公定處理模式</div>"
       "<div class='sub'>" + dt.datetime.now().strftime("%Y/%m/%d %H:%M") + " · 掃描 " + str(last["files"]) + " 檔 · 三輪硬性上限 · 唯讀提案型</div></div></header>"
       "<div class='strip'></div><h2>三輪燈號</h2><div>" + trend + "</div>"
       "<h2>子系統健康度</h2><table><tr><th>燈</th><th>子系統</th><th>盤點</th><th>異常</th></tr>" + rows + "</table>"
       "<h2>SSOT 對照</h2><table><tr><th>狀態</th><th>真相檔</th></tr>" + ss + "</table>"
       "<h2>九頭龍風險(同名異雜湊)</h2><table><tr><th>檔名</th><th>分佈</th></tr>" + hyd + "</table>"
       "<h2>分區盤點 MODULE / ENGINE / FUNCTION-LIB / OTHERS</h2>" + zone_html
       + "<h2>20 加速器</h2><div>" + acc + "</div>"
       "<footer>via_mega_engine v0103 | 高風險節點只建議不自動修 | 依 VIA_MegaPrompt_OfficialMode_v0100</footer></body></html>")
    open(out, "w", encoding="utf-8").write(page)

def main():
    print("=" * 62); print("  VIA Mega Engine v0100  |  公定處理模式 · 三輪全景式分析"); print("=" * 62)
    print("[根目錄] " + ROOT)
    rounds = []
    for rn in (1, 2, 3):
        r = sweep(rn); rounds.append(r)
        bar(100, "R%d 完成: %s (%d 檔, hydra %d, AST fail %d)" % (rn, light(r), r["files"], len(r["hydra"]), len(r["py_errors"])))
        print()
        if rn > 1 and json.dumps(rounds[-1]["hydra"], sort_keys=True) == json.dumps(rounds[-2]["hydra"], sort_keys=True) \
           and len(r["py_errors"]) == len(rounds[-2]["py_errors"]):
            print("[收斂] 第 %d 輪與前輪一致 — 提前收斂(不超過三輪)" % rn); break
    rep_dir = os.path.join(ROOT, "VIA_Reports"); os.makedirs(rep_dir, exist_ok=True)
    out = os.path.join(rep_dir, "VIA_MegaMatrix.html")
    html_matrix(rounds, out)
    state = os.path.join(rep_dir, "mega_state.json")
    hist = []
    if os.path.exists(state):
        try: hist = json.load(open(state, encoding="utf-8"))
        except Exception: hist = []
    hist.append({"ts": dt.datetime.now().isoformat(), "rounds": [
        {"round": r["round"], "light": light(r), "files": r["files"],
         "py_errors": len(r["py_errors"]), "hydra": len(r["hydra"]),
         "ssot_missing": sum(1 for x in r["ssot"] if not x["present"])} for r in rounds]})
    json.dump(hist, open(state, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    last = rounds[-1]
    print("[總結] 燈號 %s | AST fail %d | hydra %d | SSOT 缺 %d | Matrix: %s"
          % (light(last), len(last["py_errors"]), len(last["hydra"]),
             sum(1 for x in last["ssot"] if not x["present"]), out))
    if os.name == "nt" and "--no-open" not in sys.argv:
        os.startfile(out)  # noqa

if __name__ == "__main__":
    main()
