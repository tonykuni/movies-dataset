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
# =====================================================================================
# VIA Mega Engine v0106 (v0105 版本前送:掃描期 SyntaxWarning 靜音 —
#   受測檔的 ast.parse 警告(如 invalid escape sequence)不再滲出污染進度條;
#   語法「錯誤」仍照常計 AST fail,只靜音「警告」)
# (v0104 版本前送:hydra 偵測預設僅限平台域 —
#   附掛層(ATT:)的部署副本與平台正本天然同名,不再構成九頭龍 YELLOW;
#   跨域同名改列資訊項;params 加 hydra_include_attachments 可還原舊行為)
# (v0103 版本前送:
#   [1] PARAMS 參數區塊置頂 — 預設值可依需求增減;旁置 via_mega_params.json 或 --set k=v 覆寫
#   [2] attachments 附掛掃描根 — 平台外目錄(如 VMT_ROOT)納入全景,params 可增減
#   [3] 增量性輸出維護 parquet — 每輪產出 per-file 記錄,record_hash 去重後僅新增/變更列
#       落 VIA_Reports/mega_store/run_*.parquet(run-local 不入庫);工具用 DuckDB
#   [4] rich 摘要矩陣 — 詳細分區×子系統矩陣 + 健康度表 + 三輪燈號(缺 rich 優雅降級純文字)
#   [5] HTML Matrix 換 Porcelain 色系(DesignLock SSOT v0101 適用政策第 2 條)
#   其餘邏輯不變) — 公定處理模式執行載體 (ssot/VIA_MegaPrompt_OfficialMode_v0100.md)
# 三輪全景式分析 x 20 加速器 x HTML Matrix(紅黃綠燈) x 動態進度條/說明
# 治理: 唯讀分析 + 提案(高風險節點只建議不自動修) — fail-closed;紀錄永不改寫。
# 回退:bin/via-mega.cmd 改指 SUP_MDL142_MegaEngine_v0103.py
# =====================================================================================
import os, sys, ast, json, glob as _glob, hashlib, warnings, datetime as dt

ROOT = os.environ.get("VIA_HOME") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# ---------------------------------------------------------------- PARAMS(置頂;預設值可增減)
# 覆寫順序:PARAMS 預設 < 引擎旁 via_mega_params.json < 命令列 --set key.path=value(JSON 值)
PARAMS = {
    "rounds_max": 3,                       # 三輪硬性上限(公定模式;調小可,調大無效仍取 3)
    "hydra_include_attachments": False,    # True=附掛域也算九頭龍(舊 v0104 行為);預設僅平台域
    "subsystems": {                        # 平台內掃描域 — 可增減
        "VDF": "functional modules/VDF", "VAP": "functional modules/VAP",
        "VRN": "functional modules/VRN", "VMT": "supportive modules/VMT_SuperBOM",
        "GOV": "supportive modules/VIA_Governance_Runtime",
        "CGE": "supportive modules/VIA_Central_Governance",
        "SSOT": "supportive modules/ssot", "REG": "supportive modules/registry",
        "CANON": "supportive modules/VIA_Canonical_Units", "RULES": "supportive modules/70_VRN_Rules",
        "TOWER": "supportive modules/VIA_Control_Tower",
    },
    "attachments": {},                     # 附掛掃描根(絕對路徑)— 可增減,如 {"DOWNLOADS": "C:/Users/tonyk/Downloads/VIA_batch"}
    "attach_vmt_root": True,               # 便捷附掛:env VMT_ROOT(或預設 C:/VIA/VeritasMailTracker)存在即納入
    "skip_dirs": [".git", "_superseded", "__pycache__", "node_modules", "db", "output", "temp", "VIA_Reports"],
    "ssot_required": [
        "supportive modules/ssot/VRN_TickerRegexSSOT_v0100.json",
        "supportive modules/ssot/VIA_DesignLock_SSOT_v0101.json",
        "supportive modules/ssot/VIA_MegaPrompt_OfficialMode_v0100.md",
        "supportive modules/ssot/VIA_AICodegen_Prompt_SSOT_v0100.md",
        "functional modules/VAP/spec/ssot/vap_spec.json",
        "functional modules/VAP/spec/ssot/vap_chartlib.json",
        "functional modules/VAP/spec/UIUX_Design_Source/DESIGN_SOURCE_Manifest_v0101.json",
    ],
    "parquet": {"enabled": True, "dir": "VIA_Reports/mega_store"},   # 增量 store(run-local 不入庫);工具 DuckDB
    "rich_summary": True,                  # rich 摘要矩陣(未安裝則降級純文字,誠實標 SKIP)
    "html_report": "VIA_Reports/VIA_MegaMatrix.html",
    "open_report": True,                   # --no-open 亦可關
}

ACCELERATORS = ["AST 精準解析","多語言語意模型","九頭龍風險預測","依賴拓撲排序","沙盒隔離執行",
 "自動修正建議生成","三輪全景式分析","SSOT 對齊","視覺化矩陣生成","錯誤分類與分群",
 "性能與複雜度分析","多子系統同步檢視","版本差異與回滾","覆蓋率與回歸檢查","修正順序最佳化",
 "動態進度條","動態說明","非阻塞執行","多引擎整合","自動部署初始化"]

# ---------------------------------------------------------------- 參數載入/覆寫
def _deep_merge(dst, src):
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict): _deep_merge(dst[k], v)
        else: dst[k] = v

def load_params():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "via_mega_params.json")
    if os.path.exists(p):
        try:
            _deep_merge(PARAMS, json.load(open(p, encoding="utf-8")))
            print("[參數] 已合併 via_mega_params.json")
        except Exception as e:
            print("[參數] via_mega_params.json 解析失敗(%s)— 用預設" % type(e).__name__)
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == "--set" and i + 1 < len(argv) and "=" in argv[i + 1]:
            key, _, val = argv[i + 1].partition("=")
            try: val = json.loads(val)
            except Exception: pass
            cur = PARAMS; parts = key.split(".")
            for seg in parts[:-1]: cur = cur.setdefault(seg, {})
            cur[parts[-1]] = val
            print("[參數] --set %s = %r" % (key, val))
    if PARAMS.get("attach_vmt_root"):
        vr = os.environ.get("VMT_ROOT") or r"C:\VIA\VeritasMailTracker"
        if os.path.isdir(vr) and "VMT_ROOT" not in PARAMS["attachments"]:
            PARAMS["attachments"]["VMT_ROOT"] = vr

def show_params():
    print("-" * 62)
    print("  PARAMS(預設值;via_mega_params.json / --set k=v 可增減)")
    print("-" * 62)
    for k in ("rounds_max", "attach_vmt_root", "rich_summary", "open_report"):
        print("   %-16s = %r" % (k, PARAMS[k]))
    print("   %-16s = %d 域" % ("subsystems", len(PARAMS["subsystems"])))
    print("   %-16s = %s" % ("attachments", ", ".join("%s→%s" % kv for kv in PARAMS["attachments"].items()) or "(無)"))
    print("   %-16s = enabled=%r dir=%s (DuckDB)" % ("parquet", PARAMS["parquet"]["enabled"], PARAMS["parquet"]["dir"]))
    print("-" * 62)

# ---------------------------------------------------------------- 掃描
def bar(pct, msg):
    n = int(pct / 5)
    sys.stdout.write("\r[%-20s] %3d%%  %-50s" % ("#" * n, pct, msg[:50])); sys.stdout.flush()

def zone_of(fname, ext):
    fl = fname.lower()
    return ("ENGINE" if "engine" in fl else
            "MODULE" if ("mdl" in fl or "module" in fl) else
            "FUNCTION-LIB" if ("pattern" in fl or "lib" in fl or "regex" in fl or ext == "psm1") else
            "OTHERS")

def sweep(round_no):
    findings, py_err, hydra = [], [], {}
    zones, names, sub_stats, records = {}, {}, {}, []
    files_scanned = 0
    skip = set(PARAMS["skip_dirs"])
    domains = [(s, os.path.join(ROOT, rel), "PLATFORM") for s, rel in PARAMS["subsystems"].items()]
    domains += [("ATT:" + n, p, "ATTACHMENT") for n, p in PARAMS["attachments"].items() if os.path.isdir(p)]
    for i, (sub, base, kind) in enumerate(domains):
        stat = {"py": 0, "ps1": 0, "html": 0, "json": 0, "py_ast_fail": 0, "json_fail": 0, "json_legacy": 0}
        for r, ds, fs in os.walk(base):
            ds[:] = [d for d in ds if d not in skip and not d.startswith("_import_staging")]
            for f in fs:
                p = os.path.join(r, f); files_scanned += 1
                ext = f.rsplit(".", 1)[-1].lower() if "." in f else ""
                if ext in stat: stat[ext] += 1
                try: b = open(p, "rb").read()
                except OSError: continue
                sha = hashlib.sha256(b).hexdigest()
                names.setdefault(f, []).append((sub, p, sha, kind))
                zone = zone_of(f, ext)
                zones.setdefault(zone, {}).setdefault(sub, [0, []])
                zones[zone][sub][0] += 1
                if len(zones[zone][sub][1]) < 6: zones[zone][sub][1].append(f)
                flag = ""
                if ext == "py":
                    try:
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore", SyntaxWarning)
                            ast.parse(b.decode("utf-8", "replace"))
                    except SyntaxError as e:
                        stat["py_ast_fail"] += 1; flag = "AST_FAIL"
                        py_err.append({"sub": sub, "file": os.path.relpath(p, ROOT) if kind == "PLATFORM" else p,
                                       "line": e.lineno, "class": "SEQUENCE_DEPENDENT", "risk": "HIGH", "action": "PROPOSE_ONLY"})
                elif ext == "json":
                    txt = b.decode("utf-8-sig", "replace")
                    try: json.loads(txt)
                    except Exception:
                        try: json.loads(txt, strict=False); stat["json_legacy"] += 1; flag = "JSON_LEGACY"
                        except Exception:
                            stat["json_fail"] += 1; flag = "JSON_FAIL"
                            findings.append({"sub": sub, "file": os.path.relpath(p, ROOT) if kind == "PLATFORM" else p,
                                             "issue": "JSON 解析失敗", "class": "PARALLEL_FIXABLE", "risk": "MED", "action": "PROPOSE_ONLY"})
                rel = os.path.relpath(p, ROOT) if kind == "PLATFORM" else p
                rh = hashlib.sha256(("%s|%s|%s|%s" % (rel, sha, zone, flag)).encode()).hexdigest()[:24]
                records.append((rh, sub, kind, zone, rel, ext, len(b), sha[:12], flag))
        sub_stats[sub] = stat
        bar(int((i + 1) / max(1, len(domains)) * 60), "R%d 掃描 %s (%d 檔)" % (round_no, sub, files_scanned))
    att_kin = 0
    for f, occ in names.items():
        pool = occ if PARAMS.get("hydra_include_attachments") else [o for o in occ if o[3] == "PLATFORM"]
        shas = {s for _, _, s, _ in pool}
        if len(pool) > 1 and len(shas) > 1 and not f.startswith("__"):
            hydra[f] = [{"sub": s, "path": (os.path.relpath(p, ROOT) if p.startswith(ROOT) else p), "sha12": h[:12]} for s, p, h, _ in pool]
        elif len({s for _, _, s, _ in occ}) > 1 and len(pool) <= 1:
            att_kin += 1
    bar(70, "R%d 九頭龍偵測: %d 名稱" % (round_no, len(hydra)))
    ssot = [{"path": s, "present": os.path.exists(os.path.join(ROOT, s))} for s in PARAMS["ssot_required"]]
    bar(85, "R%d SSOT 對齊 %d/%d" % (round_no, sum(1 for x in ssot if x["present"]), len(ssot)))
    return {"round": round_no, "files": files_scanned, "sub_stats": sub_stats, "py_errors": py_err,
            "findings": findings, "hydra": hydra, "att_kin": att_kin, "ssot": ssot, "zones": zones, "records": records}

def light(r):
    reds = len(r["py_errors"]); yellows = len(r["findings"]) + len(r["hydra"])
    missing = sum(1 for x in r["ssot"] if not x["present"])
    if reds or missing: return "RED"
    return "YELLOW" if yellows else "GREEN"

# ---------------------------------------------------------------- parquet 增量 store(DuckDB)
def parquet_store(last):
    if not PARAMS["parquet"]["enabled"]:
        return "SKIP(params 停用)"
    try:
        import duckdb
    except ImportError:
        return "SKIP(duckdb 未安裝:py -m pip install duckdb)"
    sdir = os.path.join(ROOT, PARAMS["parquet"]["dir"]); os.makedirs(sdir, exist_ok=True)
    store_glob = os.path.join(sdir, "run_*.parquet").replace("\\", "/").replace("'", "''")
    con = duckdb.connect()
    existing = set()
    if _glob.glob(os.path.join(sdir, "run_*.parquet")):
        existing = {row[0] for row in con.execute(
            "SELECT DISTINCT record_hash FROM read_parquet('%s')" % store_glob).fetchall()}
    fresh = [rec for rec in last["records"] if rec[0] not in existing]
    if not fresh:
        n = con.execute("SELECT COUNT(*) FROM read_parquet('%s')" % store_glob).fetchone()[0] if existing else 0
        return "增量 0 新列(去重跳過 %d;store 共 %d 列)" % (len(last["records"]), n)
    run_ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    con.execute("CREATE TABLE r(record_hash VARCHAR, sub VARCHAR, kind VARCHAR, zone VARCHAR, "
                "relpath VARCHAR, ext VARCHAR, bytes BIGINT, sha12 VARCHAR, flag VARCHAR, run_ts VARCHAR)")
    con.executemany("INSERT INTO r VALUES (?,?,?,?,?,?,?,?,?,?)", [rec + (run_ts,) for rec in fresh])
    out = os.path.join(sdir, "run_%s.parquet" % run_ts).replace("\\", "/").replace("'", "''")
    con.execute("COPY r TO '%s' (FORMAT PARQUET)" % out)
    total = con.execute("SELECT COUNT(*) FROM read_parquet('%s')" % store_glob).fetchone()[0]
    return "增量 +%d 新/變更列(去重跳過 %d;store 共 %d 列,%d 個 run 檔)" % (
        len(fresh), len(last["records"]) - len(fresh), total,
        len(_glob.glob(os.path.join(sdir, "run_*.parquet"))))

# ---------------------------------------------------------------- rich 摘要矩陣
def rich_summary(rounds, pq_msg):
    last = rounds[-1]
    if not PARAMS["rich_summary"]:
        return False
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
    except ImportError:
        print("[rich] SKIP(rich 未安裝:py -m pip install rich)— 以下為純文字摘要")
        return False
    LC = {"GREEN": "green4", "YELLOW": "dark_goldenrod", "RED": "red3"}
    con = Console()
    trend = "  ".join("[%s]R%d %s[/]" % (LC[light(r)], r["round"], light(r)) for r in rounds)
    con.print(Panel.fit("[bold]VIA MEGA MATRIX[/] · 三輪燈號:%s · 掃描 %d 檔 · %s" %
                        (trend, last["files"], dt.datetime.now().strftime("%Y/%m/%d %H:%M")),
                        border_style="red3", title="核", subtitle="唯讀提案型"))
    t = Table(title="子系統健康度", header_style="bold", title_justify="left")
    for c in ("燈", "子系統", "py", "ps1", "html", "json", "AST fail", "JSON fail", "legacy"): t.add_column(c, justify="right")
    for sub, st in sorted(last["sub_stats"].items()):
        errs = any(e["sub"] == sub for e in last["py_errors"])
        lamp = "RED" if errs else ("YELLOW" if any(f["sub"] == sub for f in last["findings"]) else "GREEN")
        t.add_row("[%s]%s[/]" % (LC[lamp], lamp), sub, str(st["py"]), str(st["ps1"]), str(st["html"]),
                  str(st["json"]), str(st["py_ast_fail"]), str(st["json_fail"]), str(st["json_legacy"]))
    con.print(t)
    zt = Table(title="分區 × 子系統矩陣(檔數)", header_style="bold", title_justify="left")
    subs = sorted(last["sub_stats"].keys())
    zt.add_column("分區")
    for s in subs: zt.add_column(s, justify="right")
    for zname in ("MODULE", "ENGINE", "FUNCTION-LIB", "OTHERS"):
        zd = last.get("zones", {}).get(zname, {})
        zt.add_row(zname, *[str(zd.get(s, [0])[0]) if s in zd else "·" for s in subs])
    con.print(zt)
    st = Table(title="SSOT 對照 + 九頭龍 + 增量 store", header_style="bold", title_justify="left")
    st.add_column("項"); st.add_column("值")
    miss = [x["path"] for x in last["ssot"] if not x["present"]]
    st.add_row("SSOT", "[green4]%d/%d PRESENT[/]" % (len(last["ssot"]) - len(miss), len(last["ssot"])) +
               (" [red3]缺:%s[/]" % "; ".join(miss) if miss else ""))
    st.add_row("九頭龍(同名異雜湊,平台域)", str(len(last["hydra"])) +
               ("(附掛跨域同名 %d 為資訊項)" % last.get("att_kin", 0) if last.get("att_kin") else ""))
    st.add_row("parquet store(DuckDB)", pq_msg)
    con.print(st)
    return True

def plain_summary(rounds, pq_msg):
    last = rounds[-1]
    print("[摘要] 燈號:%s | 檔數 %d | hydra %d | AST fail %d | parquet:%s" %
          (" ".join("R%d=%s" % (r["round"], light(r)) for r in rounds),
           last["files"], len(last["hydra"]), len(last["py_errors"]), pq_msg))

# ---------------------------------------------------------------- HTML Matrix(Porcelain)
def html_matrix(rounds, out):
    C = {"GREEN": "#3d7a52", "YELLOW": "#8a6420", "RED": "#a4472f"}
    last = rounds[-1]
    rows = ""
    for sub, st in sorted(last["sub_stats"].items()):
        errs = [e for e in last["py_errors"] if e["sub"] == sub]
        lamp = "RED" if errs else ("YELLOW" if any(f["sub"] == sub for f in last["findings"]) else "GREEN")
        rows += ("<tr><td><span class='pill' style='background:%s'>%s</span></td><td>%s</td>"
                 "<td>%d py / %d ps1 / %d html / %d json</td><td>%d AST fail / %d JSON fail</td></tr>"
                 % (C[lamp], lamp, sub, st["py"], st["ps1"], st["html"], st["json"], st["py_ast_fail"], st["json_fail"])) \
               + ("" if not st.get("json_legacy") else
                  "<tr><td></td><td></td><td colspan=2 style='color:#9aa5a1'>%d 個 legacy 證據檔含控制字元(strict=False 可解析,資訊項)</td></tr>" % st["json_legacy"])
    hyd = "".join("<tr><td>%s</td><td>%s</td></tr>" % (k, "<br>".join("%(sub)s · %(path)s · %(sha12)s" % o for o in v))
                  for k, v in sorted(last["hydra"].items())) or "<tr><td colspan=2>無</td></tr>"
    ss = "".join("<tr><td><span class='pill' style='background:%s'>%s</span></td><td>%s</td></tr>"
                 % (C["GREEN" if x["present"] else "RED"], "PRESENT" if x["present"] else "MISSING", x["path"]) for x in last["ssot"])
    zone_html = ""
    for zname in ("MODULE", "ENGINE", "FUNCTION-LIB", "OTHERS"):
        zd = last.get("zones", {}).get(zname, {})
        if not zd: continue
        rows_z = "".join("<tr><td>%s</td><td>%d</td><td style='font-size:10px;color:#9aa5a1'>%s</td></tr>"
                         % (s, cnt, " · ".join(sample)) for s, (cnt, sample) in sorted(zd.items()))
        zone_html += ("<h2 style='margin-top:14px'>%s</h2><table>"
                      "<tr><th style='width:80px'>子系統</th><th style='width:50px'>檔數</th><th>樣本</th></tr>%s</table>" % (zname, rows_z))
    trend = "".join("<span class='pill' style='background:%s;margin-right:6px'>R%d %s</span>" % (C[light(r)], r["round"], light(r)) for r in rounds)
    acc = "".join("<span class='acc'>%02d %s</span>" % (i + 1, a) for i, a in enumerate(ACCELERATORS))
    att = ", ".join(PARAMS["attachments"].keys()) or "無"
    page = ("<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'><title>VIA Mega Matrix</title>"
       "<link href='https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&family=Noto+Serif+TC:wght@500;600&display=swap' rel='stylesheet'><style>"
       ":root{--ink:#1b1a17;--mut:#6b6860;--mut2:#9aa5a1;--hair:#dcdad3;--seal:#9e2b25;--teal:#3d8f8f;"
       "--serif:'Cormorant Garamond',Georgia,serif;--cjk:'Noto Serif TC','Noto Serif CJK TC','Songti TC','PMingLiU',serif;"
       "--mono:'SFMono-Regular',Consolas,'Liberation Mono',monospace;"
       "--brand6:linear-gradient(90deg,#24457f 0 16.6%,#3c6660 0 33.3%,#4a6b45 0 50%,#8a7340 0 66.6%,#5e5540 0 83.3%,#3f4f78 0 100%)}"
       "*{box-sizing:border-box;margin:0;padding:0}body{background:#f0efeb;color:var(--ink);font-family:'Microsoft JhengHei','Segoe UI',system-ui,sans-serif;padding:26px}"
       ".eyebrow{display:flex;gap:8px;align-items:center;margin-bottom:8px}.chip{padding:2px 7px;background:var(--ink);color:#fbfaf7;font:700 9px var(--mono);letter-spacing:.14em}"
       ".ey{font:700 8.5px var(--mono);letter-spacing:.13em;color:var(--mut);text-transform:uppercase}"
       "header{display:flex;align-items:center;border-bottom:3px solid var(--seal);padding-bottom:14px}"
       ".seal{width:38px;height:38px;background:var(--seal);color:#fbfaf7;display:flex;align-items:center;justify-content:center;font-family:var(--cjk);font-size:20px;border-radius:4px;margin-right:12px}"
       "h1{font:500 19px/1.2 var(--serif);letter-spacing:.055em}.wmcjk{font:600 9.5px var(--cjk);letter-spacing:.22em;color:var(--teal);margin-top:2px}"
       ".sub{font:10.5px var(--mono);color:var(--mut);margin-top:4px}.strip{height:4px;background:var(--brand6);margin:13px 0 18px;border-radius:2px}"
       "h2{font:700 11px var(--mono);letter-spacing:2px;color:var(--mut);margin:20px 0 9px;text-transform:uppercase}"
       "table{width:100%;border-collapse:collapse;background:#fbfaf7;border:1px solid var(--hair);table-layout:fixed}"
       "td{word-wrap:break-word;overflow-wrap:anywhere}"
       "th{font:700 10px var(--mono);text-align:left;padding:8px 10px;border-bottom:1px solid var(--hair);color:var(--mut)}"
       "td{font-size:11.5px;padding:7px 10px;border-bottom:1px solid var(--hair)}tr:last-child td{border-bottom:none}"
       ".pill{color:#fbfaf7;font:500 10px var(--mono);padding:2px 7px;border-radius:2px}"
       ".acc{display:inline-block;font:500 9px var(--mono);color:var(--mut);background:#fbfaf7;border:1px solid var(--hair);border-radius:3px;padding:2px 7px;margin:0 4px 4px 0}"
       "footer{margin-top:22px;font:10px var(--mono);color:var(--mut2)}</style></head><body>"
       "<div class='eyebrow'><span class='chip'>v0106</span><span class='ey'>Veritas Intelligence Analytics · Mega Engine · Porcelain</span></div>"
       "<header><div class='seal'>核</div><div><h1>VIA MEGA MATRIX — 三輪全景稽核</h1>"
       "<div class='wmcjk'>維里塔斯 · 全景分析 · 公定處理模式</div>"
       "<div class='sub'>" + dt.datetime.now().strftime("%Y/%m/%d %H:%M") + " · 掃描 " + str(last["files"]) +
       " 檔 · 附掛:" + att + " · 三輪硬性上限 · 唯讀提案型</div></div></header>"
       "<div class='strip'></div><h2>三輪燈號</h2><div>" + trend + "</div>"
       "<h2>子系統健康度</h2><table><tr><th style='width:70px'>燈</th><th style='width:110px'>子系統</th><th>盤點</th><th>異常</th></tr>" + rows + "</table>"
       "<h2>SSOT 對照</h2><table><tr><th style='width:90px'>狀態</th><th>真相檔</th></tr>" + ss + "</table>"
       "<h2>九頭龍風險(同名異雜湊)</h2><table><tr><th style='width:220px'>檔名</th><th>分佈</th></tr>" + hyd + "</table>"
       "<h2>分區盤點 MODULE / ENGINE / FUNCTION-LIB / OTHERS</h2>" + zone_html
       + "<h2>20 加速器</h2><div>" + acc + "</div>"
       "<footer>via_mega_engine v0106 · Porcelain(DesignLock v0101)| 參數置頂可增減 · 附掛掃描 · parquet 增量 store(DuckDB)· rich 摘要 | 高風險節點只建議不自動修 | 回退 v0105</footer></body></html>")
    open(out, "w", encoding="utf-8").write(page)

# ---------------------------------------------------------------- 主流程
def main():
    print("=" * 62); print("  VIA Mega Engine v0106  |  公定處理模式 · 三輪全景式分析"); print("=" * 62)
    print("[根目錄] " + ROOT)
    load_params(); show_params()
    rounds = []
    rmax = max(1, min(3, int(PARAMS.get("rounds_max", 3))))
    for rn in range(1, rmax + 1):
        r = sweep(rn); rounds.append(r)
        bar(100, "R%d 完成: %s (%d 檔, hydra %d, AST fail %d)" % (rn, light(r), r["files"], len(r["hydra"]), len(r["py_errors"])))
        print()
        if rn > 1 and json.dumps(rounds[-1]["hydra"], sort_keys=True) == json.dumps(rounds[-2]["hydra"], sort_keys=True) \
           and len(r["py_errors"]) == len(rounds[-2]["py_errors"]):
            print("[收斂] 第 %d 輪與前輪一致 — 提前收斂(不超過 %d 輪)" % (rn, rmax)); break
    rep_dir = os.path.join(ROOT, "VIA_Reports"); os.makedirs(rep_dir, exist_ok=True)
    last = rounds[-1]
    pq_msg = parquet_store(last)
    print("[parquet] " + pq_msg)
    out = os.path.join(ROOT, PARAMS["html_report"])
    html_matrix(rounds, out)
    state = os.path.join(rep_dir, "mega_state.json")
    hist = []
    if os.path.exists(state):
        try: hist = json.load(open(state, encoding="utf-8"))
        except Exception: hist = []
    hist.append({"ts": dt.datetime.now().isoformat(), "engine": "v0106",
                 "attachments": list(PARAMS["attachments"].keys()), "rounds": [
        {"round": r["round"], "light": light(r), "files": r["files"],
         "py_errors": len(r["py_errors"]), "hydra": len(r["hydra"]),
         "ssot_missing": sum(1 for x in r["ssot"] if not x["present"])} for r in rounds]})
    json.dump(hist, open(state, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if not rich_summary(rounds, pq_msg):
        plain_summary(rounds, pq_msg)
    print("[總結] 燈號 %s | AST fail %d | hydra %d | SSOT 缺 %d | Matrix: %s"
          % (light(last), len(last["py_errors"]), len(last["hydra"]),
             sum(1 for x in last["ssot"] if not x["present"]), out))
    if os.name == "nt" and PARAMS.get("open_report") and "--no-open" not in sys.argv:
        os.startfile(out)  # noqa

if __name__ == "__main__":
    main()
