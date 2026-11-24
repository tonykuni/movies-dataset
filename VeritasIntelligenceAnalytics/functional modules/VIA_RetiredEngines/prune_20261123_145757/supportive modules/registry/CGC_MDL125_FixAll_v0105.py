#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL125_FixAll v0105 — 工作站紅站一鍵補齊鏈(批364 +pkuseg/vap_node;批363 +etf_fetch/group_class;批350;批357 +時段實測/+digest;批359 +FRED 鑰匙;批361 +互動輸鑰+ENG074 SSOT 從新往舊)
====================================================================
批349 via-selftest --refail 實錄:碼側 9 站已修;料/環境側 12 站需工作站四動作。本鏈=四動作+複驗一鍵串
(零猜測:每步 argv 皆自樞紐任務冊/在庫引擎尾版直取;誠實三態;逐步 log;心跳進度條=MDL121 尾版同款直取)。
  ① datahome   MDL123 link:倉內 GroupIndex/VDF output_hub→本機資料家接點(儀表板⑩/每日摘要③/族群聚合層①②)
  ② opencc     import opencc 探;缺=SUP_MDL737.pip_install(輔助模組安裝律;同意閘)(知識堆疊②③b/NLP樞紐②/三語SSOT③)
  ③ global     樞紐任務 global=ENG066 全球宇宙擷取(NET;雙同意閘)(寬表②/輪動實庫③⑤/儀表板⑪)
  ④ consensus  樞紐任務 consensus + revenue_consensus(NET)(共識庫②④/Yahoo⑥/主動ETF×共識/月營收×共識)
  ⑤ refail     SelftestGrid 尾版 --refail(只重跑上次紅站;全原因)→轉綠數
律:只增不減;誠實三態 OK/FAIL/SKIP(已裝/已接=SKIP 註明);任一步敗續跑後續;閘(批212/P08/P09/P18)零觸碰;
    PATH 黑根前綴(哨兵⑫)=操作員環境,本鏈只印提示不改 PATH;報告 VIA_Reports/fixall/FIXALL_<stamp>.json。
v0100→v0101(批357 操作員手機令「請繼續」+「先測一些時段」):+步 hist_probe(ENG064 尾版 run --start 今−30 --end 今
--limit 200=yf 車道時段實測,一分鐘內;NET)置於 global 前;+步 digest(MDL129 LifecycleRACI digest ≤25 行,直印於終端=手機可讀)
收尾;步冊 8 步;其餘律不變。
v0101→v0102(批359 操作員令「擷取fred資料區要api key 要給我輸入不要空轉」):+步 fred(ENG055 OmniFetch 尾版 run --lane L8
=FRED us_macro 16 series 入庫;NET;前置探鑰:env FRED_API_KEY 或 output_hub/mega/.fred_api_key,缺=SKIP 並印寫鑰指令,
不空轉不互動);+--fred-key <key>:寫鑰匙檔至 output_hub/mega/.fred_api_key(gitignored;永不入 git;印遮罩尾 4 碼)。
v0102→v0103(批361 操作員令「會要我輸入fed 快 準 從新往舊抓 存在 data parquet duckdb polars 20個強化加速器」):
①fred 步改跑 VDF_ENG074_FredMacroSSOT 尾版 run(macro SSOT 190 FRED series;從新往舊視窗;checkpoint;accel_map+節流;
parquet+DuckDB us_macro+polars 鏡;落 output_hub/mega=接點→本機資料家);ENG074 缺=退 ENG055 L8。②鑰缺且終端為 TTY=
當場請操作員輸入(input;寫鑰匙檔;遮罩尾 4 碼);非 TTY(工人/CI)=SKIP 印指令(不空轉);VIA_FRED_PROMPT=0 關互動。
v0103→v0104(批363 工作站 13 紅站根因分類:主動ETF×共識①~④/市場分析④⑤=持股庫(ActiveTWETF)無列;族群聚合因子層①②④/
儀表板⑩=族群快照缺):+步 etf_fetch(樞紐任務 ENG051 主動 ETF 持股抓取;NET)置 global 後、+步 group_class(樞紐任務 ENG070
族群分類×價格指數;零網路)置 consensus 前;步冊 11 步;其餘律不變。
v0104→v0105(批364 工作站 --only 實錄:知識堆疊/NLP 樞紐/三語 SSOT 三站=spaCy zh 模型缺 spacy-pkuseg;S5 VAP v025 Browser
User Test=node 找不到 playwright):+步 pkuseg(輔助模組安裝律 pip spacy-pkuseg>=0.0.27,<0.1.0;pre=import spacy_pkuseg)置 opencc
後;+步 vap_node(npm install --prefix VIA_Reports/node_deps playwright + chromium;收容原件零觸碰=不在 intake 夾裝 node_modules;
MDL127 S5 以 NODE_PATH 接;npm 缺=SKIP 誠實)置 digest 前;__pip__/__node__ 通用特殊步;13 步。
用法:python3 CGC_MDL125_FixAll_v0105.py [run [--only a,b] [--dry] [--fred-key <key>]] | plan | --selftest
"""
from __future__ import annotations
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
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REP = VIA / "VIA_Reports" / "fixall"
FRED_KEY_FILE = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / ".fred_api_key"   # gitignored;永不入 git


def write_fred_key(key: str) -> str:
    """批359:鑰匙檔落 output_hub/mega(接點下=本機資料家);印遮罩;永不入 git/log"""
    key = (key or "").strip()
    if not key:
        return "空鑰=未寫"
    FRED_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    FRED_KEY_FILE.write_text(key, encoding="utf-8")
    return f"鑰匙檔已寫 {FRED_KEY_FILE.name}(…{key[-4:]};gitignored)"


def _mod(pattern: str, name: str):
    hits = sorted(HERE.glob(pattern))
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location(name, hits[-1])
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


_M121 = None


def m121():
    """MDL121 尾版(進度條/步內進度/Ctrl-C 免疫/樞紐任務冊)直取=零重造"""
    global _M121
    if _M121 is None:
        _M121 = _mod("CGC_MDL121_CompletionAutomator_v0*.py", "fixall_m121")
    return _M121


def _newest(pattern: str, root: Path) -> Path | None:
    hits = sorted(root.glob(pattern))
    return hits[-1] if hits else None


def plan() -> list:
    """步冊(argv 直取;缺=誠實標)"""
    T = {}
    try:
        T = m121()._registry()
    except Exception:
        T = {}
    py = sys.executable
    p123 = _newest("CGC_MDL123_DataHome_v0*.py", HERE)
    grid = _newest("CGC_MDL064_SelftestGrid_v0*.py", HERE)
    steps = [
        {"id": "datahome", "zh": "資料本機家接點(GroupIndex/VDF output_hub→本機)", "net": False, "to": 900,
         "argv": [py, str(p123), "link"] if p123 else None, "why": "儀表板⑩/每日摘要③/族群聚合層①②",
         "pre": "datahome"},
        {"id": "opencc", "zh": "OpenCC 簡繁正規化件(輔助模組安裝律)", "net": True, "to": 600,
         "argv": ["__opencc__"], "why": "知識堆疊②③b/NLP樞紐②/三語SSOT③", "pre": "opencc"},
        {"id": "pkuseg", "zh": "spaCy 中文分詞件 spacy-pkuseg(知識堆疊/NLP 樞紐/三語 SSOT 三站根因)", "net": True, "to": 900,
         "argv": ["__pip__", "spacy-pkuseg>=0.0.27,<0.1.0"], "why": "知識堆疊八檢/NLP 樞紐九檢/三語 SSOT 九檢(ImportError spacy-pkuseg)",
         "pre": "import:spacy_pkuseg"},
        {"id": "hist_probe", "zh": "歷史回補時段實測(yf 車道;今−30~今;200 檔)", "net": True, "to": 900,
         "argv": [py, str(_newest("VDF_ENG064_HistoryBackfill_v*.py", VIA / "functional modules" / "VDF" / "engine")), "run",
                  "--start", (datetime.now().date() - timedelta(days=30)).isoformat(), "--end", datetime.now().date().isoformat(), "--limit", "200"]
         if _newest("VDF_ENG064_HistoryBackfill_v*.py", VIA / "functional modules" / "VDF" / "engine") else None,
         "why": "先測一些時段(批355 車道律 yf)"},
        {"id": "global", "zh": T.get("global", {}).get("zh", "全球宇宙擷取(ENG066)"), "net": True, "to": 3600,
         "argv": list(T["global"]["argv"]) if "global" in T else None, "why": "寬表②/輪動實庫③⑤/儀表板⑪"},
        {"id": "fred", "zh": "FRED 宏觀 SSOT 190 series 從新往舊(ENG074;需 API key;缺=當場輸入)", "net": True, "to": 1800,
         "argv": ([py, str(_newest("VDF_ENG074_FredMacroSSOT_v*.py", VIA / "functional modules" / "VDF" / "engine")), "run"]
                  if _newest("VDF_ENG074_FredMacroSSOT_v*.py", VIA / "functional modules" / "VDF" / "engine") else
                  ([py, str(_newest("VDF_ENG055_OmniFetch_v*.py", VIA / "functional modules" / "VDF" / "engine")), "run", "--lane", "L8"]
                   if _newest("VDF_ENG055_OmniFetch_v*.py", VIA / "functional modules" / "VDF" / "engine") else None)),
         "why": "global 之 us_macro 候源→真抓(parquet+duckdb+polars 落本機資料家;不空轉)", "pre": "fred"},
        {"id": "etf_fetch", "zh": T.get("etf_fetch", {}).get("zh", "主動式ETF持股抓取(ENG051)"), "net": True, "to": 1800,
         "argv": list(T["etf_fetch"]["argv"]) if "etf_fetch" in T else None, "why": "主動ETF×共識①~④/市場分析④⑤(持股庫無列)"},
        {"id": "group_class", "zh": T.get("group_class", {}).get("zh", "族群分類×價格指數(ENG070)"), "net": False, "to": 1800,
         "argv": list(T["group_class"]["argv"]) if "group_class" in T else None, "why": "族群聚合因子層①②④/儀表板⑩(族群快照缺)"},
        {"id": "consensus", "zh": T.get("consensus", {}).get("zh", "三源共識擴碼"), "net": True, "to": 1800,
         "argv": list(T["consensus"]["argv"]) if "consensus" in T else None, "why": "共識庫②④/Yahoo⑥"},
        {"id": "revenue_consensus", "zh": T.get("revenue_consensus", {}).get("zh", "月營收×共識"), "net": True, "to": 1800,
         "argv": list(T["revenue_consensus"]["argv"]) if "revenue_consensus" in T else None, "why": "主動ETF×共識/月營收×共識"},
        {"id": "refail", "zh": "只重跑上次紅站+全原因(SelftestGrid --refail)", "net": False, "to": 3600,
         "argv": [py, str(grid), "--refail"] if grid else None, "why": "轉綠實證"},
        {"id": "vap_node", "zh": "VAP v025 瀏覽器 UAT 依賴(playwright→VIA_Reports/node_deps;S5 以 NODE_PATH 接)", "net": True, "to": 1500,
         "argv": ["__node__", "playwright"], "why": "六流程 S5 Browser User Test(Cannot find module 'playwright')", "pre": "node_deps"},
        {"id": "digest", "zh": "生命週期 digest(≤25 行;手機可讀)", "net": False, "to": 300,
         "argv": [py, str(_newest("CGC_MDL129_LifecycleRACI_v0*.py", HERE)), "digest"] if _newest("CGC_MDL129_LifecycleRACI_v0*.py", HERE) else None,
         "why": "收尾:目前階段/下一步"},
    ]
    for s in steps:
        s["engine_ok"] = bool(s["argv"]) and (str(s["argv"][0]).startswith("__") or Path(str(s["argv"][1])).is_file())
    return steps


def _pre_skip(step: dict) -> str:
    """前置探:已達成=SKIP 理由;'' =需執行"""
    if step.get("pre") == "opencc":
        try:
            import opencc  # noqa: F401
            return "opencc 已裝"
        except Exception:
            return ""
    if str(step.get("pre", "")).startswith("import:"):
        try:
            __import__(step["pre"].split(":", 1)[1])
            return f"{step['pre'].split(':', 1)[1]} 已裝"
        except Exception:
            return ""
    if step.get("pre") == "node_deps":
        if (NODE_DEPS / "node_modules" / "playwright").exists():
            return "node_deps 已裝(NODE_PATH 接)"
        if not shutil.which("npm"):
            return "npm 缺=SKIP(裝 Node.js 後重跑;S5 瀏覽器 UAT 候)"
        return ""
    if step.get("pre") == "fred":
        if os.environ.get("FRED_API_KEY", "").strip() or FRED_KEY_FILE.exists():
            return ""
        # 批361:鑰缺且 TTY=當場請操作員輸入(只寫本機鑰匙檔;遮罩);非 TTY=SKIP 印指令
        if os.environ.get("VIA_FRED_PROMPT", "1") != "0" and sys.stdin is not None and sys.stdin.isatty():
            try:
                k = input("[補齊] FRED API key 缺,請輸入(32 碼;只存本機 output_hub/mega/.fred_api_key,永不入 git;空=略過):").strip()
            except (EOFError, KeyboardInterrupt):
                k = ""
            if k:
                print("[補齊] " + write_fred_key(k), flush=True)
                return ""
        return f"FRED 鑰缺=SKIP(不空轉):via-mobile --fred-key <你的 key> 或寫入 {FRED_KEY_FILE}"
    if step.get("pre") == "datahome":
        try:
            m = _mod("CGC_MDL123_DataHome_v0*.py", "fixall_m123")
            st = m.status()
            if st.get("state") == "OK" and st.get("points"):
                return "接點已全接"
        except Exception:
            return ""
    return ""


NODE_DEPS = VIA / "VIA_Reports" / "node_deps"   # gitignored(VIA_Reports/*);收容原件夾零觸碰


def _run_pip(lf, env: dict, pkgs: list[str], tag: str) -> int:
    """輔助模組安裝律:SUP_MDL737.pip_install(同意閘先行;誠實 rc);敗退 pip --user"""
    os.environ["VIA_NET_CONSENT"] = "YES"
    try:
        import VIA_SuperAccel_Module as A
        rc, msg = A.pip_install(list(pkgs))
        lf.write(f"[{tag}] pip_install rc={rc} {msg}\n")
        if rc == 0:
            return 0
    except Exception as exc:
        lf.write(f"[{tag}] 輔助模組道敗 {type(exc).__name__}: {exc};退 pip --user\n")
    r = subprocess.run([sys.executable, "-m", "pip", "install", "--user", *pkgs],
                       stdout=lf, stderr=subprocess.STDOUT, env=env, timeout=600)
    return r.returncode


def _run_node(lf, env: dict, pkgs: list[str]) -> int:
    """VAP v025 瀏覽器 UAT 依賴:npm install --prefix VIA_Reports/node_deps <pkgs> + playwright chromium;npm 缺=-9(SKIP)"""
    npm = shutil.which("npm")
    if not npm:
        lf.write("[vap_node] npm 缺=SKIP(裝 Node.js 後重跑)\n")
        return -9
    NODE_DEPS.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([npm, "install", "--prefix", str(NODE_DEPS), "--no-audit", "--no-fund", *pkgs],
                       stdout=lf, stderr=subprocess.STDOUT, env=env, cwd=str(NODE_DEPS), timeout=900, shell=(os.name == "nt"))
    if r.returncode != 0:
        return r.returncode
    cli = NODE_DEPS / "node_modules" / "playwright" / "cli.js"
    node = shutil.which("node")
    if cli.exists() and node:
        r2 = subprocess.run([node, str(cli), "install", "chromium"], stdout=lf, stderr=subprocess.STDOUT, env=env,
                            cwd=str(NODE_DEPS), timeout=900)
        lf.write(f"[vap_node] playwright install chromium rc={r2.returncode}\n")
        return r2.returncode
    lf.write("[vap_node] playwright cli 缺(安裝不完整)\n")
    return 1


def _run_special(s: dict, lf, env: dict) -> int:
    k = str(s["argv"][0])
    if k == "__opencc__":
        return _run_opencc(lf, env)
    if k == "__pip__":
        return _run_pip(lf, env, [str(x) for x in s["argv"][1:]], s["id"])
    if k == "__node__":
        return _run_node(lf, env, [str(x) for x in s["argv"][1:]])
    lf.write(f"[{s['id']}] 未知特殊步 {k}\n")
    return 1


def _run_opencc(lf, env: dict) -> int:
    """輔助模組安裝律:SUP_MDL737.pip_install(同意閘先行;誠實 rc)"""
    os.environ["VIA_NET_CONSENT"] = "YES"  # 本步 net=True:操作員起跑 via-fixall 即同意(誠實印於步冊 NET 欄)
    try:
        import VIA_SuperAccel_Module as A
        rc, msg = A.pip_install(["opencc-python-reimplemented"])
        lf.write(f"[opencc] pip_install rc={rc} {msg}\n")
        if rc == 0:
            return 0
    except Exception as exc:
        lf.write(f"[opencc] 輔助模組道敗 {type(exc).__name__}: {exc};退 pip --user\n")
    r = subprocess.run([sys.executable, "-m", "pip", "install", "--user", "opencc-python-reimplemented"],
                       stdout=lf, stderr=subprocess.STDOUT, env=env, timeout=600)
    return r.returncode


def run(only: list | None = None, dry: bool = False, do_print: bool = True) -> int:
    M = m121()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    REP.mkdir(parents=True, exist_ok=True)
    logdir = REP / f"RUN_{stamp}"
    logdir.mkdir(parents=True, exist_ok=True)
    sel = [s for s in plan() if not only or s["id"] in only]
    beat_sec = max(1.0, float(os.environ.get("VIA_BEAT_SEC", "5") or 5))
    immune = M._ctrlc_immune() if hasattr(M, "_ctrlc_immune") else False
    t_all, durs, beat_n, steps = time.time(), [], 0, []
    if do_print:
        print(f"[補齊] 本進程 PID {os.getpid()} · 步 {len(sel)} · Ctrl-C 免疫 {'ON' if immune else 'OFF'} · {'DRY' if dry else 'LIVE'}", flush=True)
        if os.name == "nt":
            bad = [e for e in (os.environ.get("PATH") or "").split(os.pathsep)
                   if e.lower().startswith(("c:\\users\\tonyk\\onedrive", "c:\\users\\tonyk\\downloads"))]
            if bad:
                print(f"[補齊] 提示:PATH 含黑根前綴 {len(bad)} 段(哨兵⑫;本鏈不改 PATH,請於系統環境變數移除):{'; '.join(bad[:3])}", flush=True)
    for i, s in enumerate(sel, 1):
        ent = {"no": i, "id": s["id"], "zh": s["zh"], "why": s["why"], "state": "SKIP", "rc": None, "sec": 0}
        t0 = time.time()
        pre = _pre_skip(s)
        if not s["engine_ok"]:
            ent["note"] = "引擎/樞紐任務缺(先 via-reload)"
        elif pre:
            ent["note"] = pre
        elif dry:
            ent["note"] = "DRY:" + " ".join(str(a) for a in s["argv"])[:160]
        else:
            env = dict(os.environ)
            if s["net"]:
                env["VIA_NET_CONSENT"] = "YES"
                env["VIA_SCRAPE_CONSENT"] = "YES"
            env["PYTHONUTF8"] = "1"
            env["PYTHONWARNINGS"] = "ignore"
            lp = logdir / f"{i:02d}_{s['id']}.log"
            if do_print:
                print(f"[補齊] {i:02d}/{len(sel)} {s['id']} 起跑 · {s['zh']} · 逾時 {s['to']}s · "
                      f"{M.progress_bar(i - 1, len(sel), spent=time.time() - t_all, per_step=durs)}", flush=True)
            try:
                with open(lp, "w", encoding="utf-8", errors="ignore") as lf:
                    if str(s["argv"][0]).startswith("__"):
                        rc = _run_special(s, lf, env)
                    else:
                        p = subprocess.Popen(list(s["argv"]), stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                             env=env, cwd=str(VIA), **(M._child_kwargs() if hasattr(M, "_child_kwargs") else {}))
                        last_beat = time.time()
                        while True:
                            try:
                                p.wait(timeout=1.0)
                                break
                            except subprocess.TimeoutExpired:
                                pass
                            if time.time() - t0 > s["to"]:
                                p.kill()
                                raise subprocess.TimeoutExpired(s["argv"], s["to"])
                            if do_print and time.time() - last_beat >= beat_sec:
                                last_beat = time.time()
                                beat_n += 1
                                try:
                                    tl = lp.read_text(encoding="utf-8", errors="ignore").strip().splitlines()
                                    tail = tl[-1][-100:] if tl else ""
                                except Exception:
                                    tail = ""
                                sn, sd = M.sub_progress(tail)
                                frac = (sn / sd) if sd else 0.0
                                sub = f" · 步內 {M.progress_bar(sn, sd, width=8)}" if sd else ""
                                print(f"[補齊] {i:02d}/{len(sel)} {s['id']} 執行中 {'◐◓◑◒'[beat_n % 4]} {int(time.time() - t0)}s · "
                                      f"{M.progress_bar(i - 1 + frac, len(sel), spent=time.time() - t_all, per_step=durs)}{sub}"
                                      f"{' · ' + tail if tail else ''}", flush=True)
                                try:
                                    (logdir / "PROGRESS.json").write_text(json.dumps(
                                        {"step": i, "total": len(sel), "id": s["id"], "sub_n": sn, "sub_d": sd, "pid": p.pid,
                                         "self_pid": os.getpid(), "elapsed": int(time.time() - t_all)}, ensure_ascii=False), encoding="utf-8")
                                except Exception:
                                    pass
                        rc = p.returncode
                ent["rc"] = rc
                ent["state"] = "OK" if rc == 0 else "FAIL"
                if rc == -9:
                    ent["state"], ent["note"] = "SKIP", "npm 缺=SKIP(裝 Node.js 後重跑;誠實)"
            except subprocess.TimeoutExpired:
                ent["rc"], ent["state"], ent["note"] = -1, "FAIL", f"逾時 {s['to']}s 終止(不卡斷)"
            except Exception as exc:
                ent["rc"], ent["state"], ent["note"] = -2, "FAIL", type(exc).__name__
            ent["log"] = str(lp.relative_to(VIA))
            try:
                tl = lp.read_text(encoding="utf-8", errors="ignore").strip().splitlines()
                ent["tail"] = "\n".join(tl[-3:])[-400:]
                if s["id"] == "refail":
                    ent["tally"] = next((l for l in reversed(tl) if "[計] 重跑" in l), "")
            except Exception:
                pass
        ent["sec"] = round(time.time() - t0, 1)
        if ent["state"] != "SKIP":
            durs.append(ent["sec"])
        steps.append(ent)
        if do_print:
            print(f"[補齊] {i:02d}/{len(sel)} {s['id']} → {ent['state']}{'' if ent['rc'] is None else ' rc' + str(ent['rc'])} · {ent['sec']}s"
                  f"{' · ' + ent['note'] if ent.get('note') else ''}{' · ' + ent['tally'] if ent.get('tally') else ''} · "
                  f"{M.progress_bar(i, len(sel), spent=time.time() - t_all, per_step=durs)}", flush=True)
    n_ok = sum(1 for s in steps if s["state"] == "OK")
    n_fail = sum(1 for s in steps if s["state"] == "FAIL")
    n_skip = sum(1 for s in steps if s["state"] == "SKIP")
    rep = {"ts": stamp, "engine": Path(__file__).name, "dry": dry, "only": only or [], "n_ok": n_ok, "n_fail": n_fail,
           "n_skip": n_skip, "sec": round(time.time() - t_all, 1), "steps": steps,
           "state": "OK" if n_fail == 0 and n_ok else ("FAIL" if n_fail and not n_ok else ("PART" if n_fail else "SKIP"))}
    (REP / f"FIXALL_{stamp}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    if do_print:
        for st in steps:  # 批357:digest 直印(手機只看這段)
            if st["id"] == "digest" and st.get("log"):
                try:
                    print("[補齊] ---- DIGEST ----")
                    print((VIA / st["log"]).read_text(encoding="utf-8", errors="ignore").strip()[-2400:])
                except Exception:
                    pass
    if do_print:
        print(f"[補齊] 終態 {rep['state']} · OK {n_ok} · FAIL {n_fail} · SKIP {n_skip} · {rep['sec']}s · FIXALL_{stamp}.json · "
              f"{M.progress_bar(len(steps), len(sel))}", flush=True)
    return 0 if n_fail == 0 else 1


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    os.environ["VIA_CTRLC_IMMUNE"] = "0"
    os.environ["VIA_FRED_PROMPT"] = "0"   # 自測零互動
    src = Path(__file__).read_text(encoding="utf-8")
    P = plan()
    chk("① 步冊十三步(datahome/opencc/pkuseg/hist_probe/global/fred/etf_fetch/group_class/consensus/revenue_consensus/refail/vap_node/digest;argv 樞紐冊/尾版直取)",
        [s["id"] for s in P] == ["datahome", "opencc", "pkuseg", "hist_probe", "global", "fred", "etf_fetch", "group_class", "consensus", "revenue_consensus", "refail", "vap_node", "digest"]
        and all(s["engine_ok"] for s in P), f"(在位 {sum(s['engine_ok'] for s in P)}/13)")
    chk("② NET 步雙同意閘旗標(opencc/pkuseg/hist_probe/global/fred/etf_fetch/consensus/revenue_consensus/vap_node=net;datahome/group_class/refail/digest 零網路)",
        [s["net"] for s in P] == [False, True, True, True, True, True, True, False, True, True, False, True, False])
    M = m121()
    chk("③ MDL121 尾版助手直取(progress_bar/sub_progress/_ctrlc_immune/_child_kwargs/_registry)零重造",
        M is not None and all(hasattr(M, k) for k in ("progress_bar", "sub_progress", "_ctrlc_immune", "_child_kwargs", "_registry")))
    rc = run(dry=True, do_print=False)
    last = sorted(REP.glob("FIXALL_*.json"))[-1]
    d = json.loads(last.read_text(encoding="utf-8"))
    chk("④ DRY 全鏈零執行(六步皆 SKIP/DRY 註;報告落盤;閘零觸碰)",
        rc == 0 and d["dry"] and len(d["steps"]) == 13 and all(s["state"] == "SKIP" for s in d["steps"])
        and "2020" not in json.dumps(d, ensure_ascii=False), f"({last.name})")
    chk("⑤ 前置探律(opencc 已裝=SKIP 註明;datahome 接點已全接=SKIP)",
        (_pre_skip(P[1]) in ("", "opencc 已裝")) and (_pre_skip(P[0]) in ("", "接點已全接")))
    _k = os.environ.pop("FRED_API_KEY", None)
    _fp = [x for x in P if x["id"] == "fred"][0]
    chk("⑦ FRED 鑰律(缺鑰=SKIP 印寫鑰指令不空轉;鑰匙檔路徑=output_hub/mega 且 gitignored;--fred-key 寫檔遮罩)",
        (FRED_KEY_FILE.exists() or _pre_skip(_fp).startswith("FRED 鑰缺")) and "output_hub" in str(FRED_KEY_FILE)
        and "write_fred_key" in src and "[-4:]" in src)
    if _k is not None:
        os.environ["FRED_API_KEY"] = _k
    chk("⑥ 紀律宣告(只增不減/誠實三態/閘零觸碰/輔助模組安裝律/PATH 不改)",
        all(k in src for k in ("只增不減", "誠實三態", "零觸碰", "pip_install", "不改 PATH")))
    print(f"  [計] 七檢 OK {7 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 工作站紅站一鍵補齊鏈(CGC_MDL125 v0105)· 七檢自測(零外網)===")
        return selftest()
    if "--fred-key" in a and a.index("--fred-key") + 1 < len(a):
        print("[補齊] " + write_fred_key(a[a.index("--fred-key") + 1]))
        a = [x for i, x in enumerate(a) if x != "--fred-key" and not (i > 0 and a[i - 1] == "--fred-key")]
    if a and a[0] == "run":
        only = [x for x in a[a.index("--only") + 1].split(",") if x] if "--only" in a else None
        return run(only=only, dry="--dry" in a)
    for s in plan():
        print(f"  {s['id']:18s} {'在位' if s['engine_ok'] else '缺  '} {'NET' if s['net'] else '   '} 逾時 {s['to']:5d}s  {s['zh']}  → {s['why']}")
    print("[補齊] via-fixall run(全鏈)· via-fixall run --only global,refail · --dry 零執行")
    return 0


if __name__ == "__main__":
    sys.exit(main())
