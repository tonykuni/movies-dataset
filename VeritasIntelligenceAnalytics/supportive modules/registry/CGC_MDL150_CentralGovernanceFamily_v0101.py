#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL150_CentralGovernanceFamily v0101 — 中央治理家族擁有者(批515 工作站實錄修)
v0100→v0101(批515 操作員實錄 via-cgfamily:五成員全 MD5_DRIFT · via-cgconsole RED 192s 只看到 SyntaxWarning · via-cgrouter AMBER 891s):
  ① md5 對冊改「內容正規化」:CRLF→LF、去 BOM 再算(Windows git autocrlf 簽出把 LF 換成 CRLF,位元組變了、內容沒變=假漂移;LL24)
  ② status 把主控台快照的 Gate 矩陣 FAIL/WARN(code/title/detail)、重複家族數、解析失敗數列出來(RED 要看得到理由,不是只看到 rc=1;LL25)
  ③ run_tool 尾行取 stdout 優先(stderr 的 SyntaxWarning 把裁決行擠掉);rc≠0 才附 stderr 尾;十檢 +⑨⑩。
====================================================================
操作員 2026-09-15 上傳五件「中央管理系統」:
  VIA-SYS-MGR-001 VIA_CentralGovernanceConsole.py  主控台:URN 發碼 · 同義字 SSOT · 契約治理 · 環境稽核 · 閘矩陣 · AST 自省 · 拓撲守衛 · 探針 · 呼叫圖
  VIA-GOV-ENG-001 VIA_CentralGovernanceEngine.py   詞彙引擎:regex SSOT · 台股代號鎖 · 時間語彙正規化 · 詞彙 AUTO/ASK/QUARANTINE · 提示詞冊
  VIA-SYS-MGR-003 VIA_DownwardController.py        下行控制:能力冊 append-only · 拓撲分層 · 變更類能力權杖閘 · 並行下行
  VIA-SYS-ENG-003 VIA_FilePriorityRouter.py        檔案優先序:L0 掃描 · L1 格式目錄/magic bytes · P0..P5 · 讀取預算
  (ps1)           VIA_SameNameConsolidator_v0100.ps1 同名整併:IDENTICAL 真重複/DIVERGED 分歧只報告 · 遺失符號 · 權杖+-Commit 才搬
量到:五件 md5 與 new modules engines/ 內 8 個 (1)/(2)/(3)/(4) 副本 byte 全同(批511 衛生報告候歸位)→ 歸位一份於
  supportive modules/VIA_Central_Governance/VIA_CentralGovernanceFamily_b514/(原名零觸碰:套件內以檔名互呼;MANIFEST_b514.json md5 冊),副本刪(docs/VIA_RepoHygiene_B514)。
「不足」=它們在冊上沒有任何登錄(Register/Deck/Grid/Manager/VCGC 皆無)、各自寫死根與輸出、變更類動作沒有統一的閘。本件補上:
  ① 擁有者(L30):啟動路徑/工作夾/閘只寫一處——所有成員經本件起跑;工作夾一律 VIA_Reports/central_governance/<成員>(不入倉);
     主控台只認 --root,其快照落 <root>/output/SYS 與 <root>/configs(.gitignore 已收 output/ 與 configs 預覽/參數;--commit 台帳可入倉)
  ② 閘(L07):預設全 dry-run;--commit / --probe / --token / -Commit / -IncludeDiverged 只在操作員明給才傳;零彈窗(--no-open/-NoBrowser 一律);零網路
  ③ 子行程環境=匯流排 child_env()(L32:PYTHONHOME 不繼承;bootstrap 前置);cwd=工作夾
  ④ status:各成員最新快照 → VIA_Reports/central_governance/FAMILY_latest.json(誠實 ABSENT;VCGC v0105 十一段讀此)
  ⑤ plan:印一貼即用(dry-run 順序:router → engine --selftest → console → downward → samename)
用法:python3 CGC_MDL150_CentralGovernanceFamily_v0100.py status | plan | console [--probe] [--commit] [--root R]
      | engine [引擎旗標…;預設 --selftest] | router [--root R] [--ocr] | downward [--commit --token T] [--strict-chain]
      | samename [--commit --token T] [--diverged] [--root R] [--json] | --selftest(十檢;零網路)
律:只增不減;正本零觸碰(成員件不改,新版=新 _b5NN 夾);尾版律(夾名 glob);Zero-Hydra(成員自己的判斷不重寫);誠實三態;零 CDN;零彈窗;零網路;同意閘/權杖不代設。
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
FAMILY_ROOT = VIA / "supportive modules" / "VIA_Central_Governance"
FAMILY_GLOB = "VIA_CentralGovernanceFamily_b*"
OUT = VIA / "VIA_Reports" / "central_governance"
MEMBERS = {
    "console": ("VIA_CentralGovernanceConsole.py", "VIA-SYS-MGR-001", "中央治理主控台"),
    "engine": ("VIA_CentralGovernanceEngine.py", "VIA-GOV-ENG-001", "中央治理詞彙引擎"),
    "downward": ("VIA_DownwardController.py", "VIA-SYS-MGR-003", "自動下行控制層"),
    "router": ("VIA_FilePriorityRouter.py", "VIA-SYS-ENG-003", "檔案優先序路由器"),
    "samename": ("VIA_SameNameConsolidator_v0100.ps1", "VIA-SUP-TOOL-SAMENAME", "同名整併(ps1)"),
}


def _ts() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def family_home(root: Path = FAMILY_ROOT) -> Path | None:
    """尾版律:夾名 VIA_CentralGovernanceFamily_b<批> 取最大者。"""
    hits = sorted(p for p in root.glob(FAMILY_GLOB) if p.is_dir())
    return hits[-1] if hits else None


def _md5(p: Path) -> str:
    """批515:內容正規化後才算(CRLF→LF、去 UTF-8 BOM):git autocrlf 簽出的 CRLF 副本與 LF 正本同內容=同 md5(冊裡的值以 LF 正本算)。"""
    b = p.read_bytes()
    if b.startswith(b"\xef\xbb\xbf"):
        b = b[3:]
    return hashlib.md5(b.replace(b"\r\n", b"\n")).hexdigest()


def family_files(home: Path | None = None) -> dict:
    """成員在位 × md5 對冊(MANIFEST_b5NN.json);缺=ABSENT、md5 不合=MD5_DRIFT(原名零觸碰律的量尺)。"""
    home = home or family_home()
    out = {"home": str(home) if home else "", "state": "OK" if home else "ABSENT", "members": {}}
    man = {}
    if home:
        mp = sorted(home.glob("MANIFEST_b*.json"))
        if mp:
            try:
                man = {m["file"]: m for m in json.loads(mp[-1].read_text(encoding="utf-8")).get("members", [])}
            except Exception as exc:
                out["manifest_why"] = f"{type(exc).__name__}"
    for key, (fn, urn, zh) in MEMBERS.items():
        p = (home / fn) if home else None
        if p and p.exists():
            h = _md5(p)
            st = "OK" if (fn not in man or man[fn].get("md5") == h) else "MD5_DRIFT"
        else:
            h, st = "", "ABSENT"
        out["members"][key] = {"file": fn, "urn": urn, "zh": zh, "path": str(p) if p else "", "state": st, "md5": h[:8]}
        if st != "OK":
            out["state"] = "PARTIAL" if out["state"] != "ABSENT" else out["state"]
    return out


def _pwsh() -> str:
    return shutil.which("pwsh") or shutil.which("powershell") or "pwsh"


# ---------------------------------------------------------------- argv 建構(閘只在明給時傳)
def console_argv(root: Path = VIA, probe: bool = False, commit: bool = False, home: Path | None = None) -> list:
    home = home or family_home()
    a = [sys.executable, str(home / MEMBERS["console"][0]), "--root", str(root), "--no-open", "--json"]
    if probe:
        a.append("--probe")
    if commit:
        a.append("--commit")
    return a


def engine_argv(extra: list | None = None, work: Path | None = None, home: Path | None = None) -> list:
    home = home or family_home()
    extra = [x for x in (extra or []) if x]
    a = [sys.executable, str(home / MEMBERS["engine"][0]), "--work", str(work or (OUT / "engine"))]
    return a + (extra if extra else ["--selftest", "--json"])


def router_argv(root: Path = VIA, ocr: bool = False, out: Path | None = None, home: Path | None = None) -> list:
    home = home or family_home()
    a = [sys.executable, str(home / MEMBERS["router"][0]), "--root", str(root), "--out", str(out or (OUT / "priority")), "--no-open", "--json"]
    if ocr:
        a.append("--ocr")
    return a


def downward_argv(commit: bool = False, token: str = "", strict: bool = False, work: Path | None = None, home: Path | None = None, root: Path = VIA) -> list:
    home = home or family_home()
    a = [sys.executable, str(home / MEMBERS["downward"][0]), "--root", str(root), "--tools", str(home), "--work", str(work or (OUT / "downward")),
         "--supportive", str(VIA / "supportive modules"), "--pwsh", _pwsh(), "--no-open", "--json"]
    er = os.environ.get("VIA_ENV_ROOT")
    if er:
        a += ["--env-root", er]
    if strict:
        a.append("--strict-chain")
    if commit and token:                       # 權杖+明示才下行變更類能力(L07 同律:不代設)
        a += ["--commit", "--token", token]
    return a


def samename_argv(root: Path = VIA, commit: bool = False, token: str = "", diverged: bool = False, work: Path | None = None, home: Path | None = None) -> list:
    home = home or family_home()
    a = [_pwsh(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(home / MEMBERS["samename"][0]),
         "-Root", str(root), "-WorkRoot", str(work or (OUT / "samename")), "-NoBrowser"]
    if diverged:
        a.append("-IncludeDiverged")
    if commit and token:
        a += ["-Commit", "-Token", token]
    return a


# ---------------------------------------------------------------- 子行程
def _bus_child_env():
    try:
        hits = sorted(HERE.glob("CGC_MDL148_EngineBus_v*.py"))
        if not hits:
            return None
        spec = importlib.util.spec_from_file_location("via_bus_ro_cg", hits[-1])
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return getattr(m, "child_env", None)
    except Exception:
        return None


def child_env() -> dict:
    """L30/L32:子行程環境只寫一處=匯流排 child_env(PYTHONHOME 不繼承、bootstrap 前置);缺匯流排=本地同律。零彈窗;撤同意閘(本家族零網路)。"""
    ce = _bus_child_env()
    env = ce("") if ce is not None else dict(os.environ, PYTHONIOENCODING="utf-8", VIA_ROOT=str(VIA))
    ph = env.pop("PYTHONHOME", None)
    if ph:
        env["VIA_PYTHONHOME_SCRUBBED"] = ph
    env.update({"PYTHONUTF8": "1", "VIA_NO_OPEN": "1"})
    env.pop("VIA_NET_CONSENT", None)
    return env


def run_tool(argv: list, timeout: int = 1800, cwd: Path | None = None, log_dir: Path | None = None) -> dict:
    cwd = cwd or OUT
    try:
        cwd.mkdir(parents=True, exist_ok=True)
    except Exception:
        cwd = VIA
    t0 = _dt.datetime.now()
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL, env=child_env(), cwd=str(cwd),
                           encoding="utf-8", errors="replace")
        rc, out, err = r.returncode, r.stdout or "", r.stderr or ""
        state = "OK" if rc == 0 else "FAIL"
    except subprocess.TimeoutExpired:
        rc, out, err, state = -1, "", "", "TIMEOUT"
    except Exception as exc:
        rc, out, err, state = -1, "", f"{type(exc).__name__}:{str(exc)[:120]}", "FAIL"
    o_lines = [l for l in out.splitlines() if l.strip()]
    e_lines = [l for l in err.splitlines() if l.strip()]
    lines = o_lines if o_lines else e_lines                     # 批515:stdout 優先(SyntaxWarning 走 stderr,不再擠掉裁決行)
    js = None
    for l in reversed(o_lines + e_lines):
        if l.strip().startswith("{"):
            try:
                js = json.loads(l.strip())
                break
            except Exception:
                continue
    res = {"state": state, "rc": rc, "secs": round((_dt.datetime.now() - t0).total_seconds(), 1), "tail": lines[-4:], "json": js, "argv": argv,
           "stderr_tail": e_lines[-3:] if (rc != 0 and o_lines) else []}
    try:
        ld = log_dir or (OUT / "logs")
        ld.mkdir(parents=True, exist_ok=True)
        with (ld / "family.log").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": _ts(), "argv": [Path(argv[0]).name] + [str(x) for x in argv[1:]], "state": state, "rc": rc, "secs": res["secs"], "tail": res["tail"]}, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return res


# ---------------------------------------------------------------- status
def _newest_json(d: Path, pat: str) -> tuple[dict | None, str]:
    try:
        hits = sorted(d.glob(pat))
        if not hits:
            return None, ""
        return json.loads(hits[-1].read_text(encoding="utf-8")), hits[-1].name
    except Exception as exc:
        return None, f"讀不了:{type(exc).__name__}"


def status(out: Path = OUT, root: Path = VIA, do_print: bool = True, home: Path | None = None) -> dict:
    ff = family_files(home)
    s = {"schema": "VIA.CentralGovernanceFamily.v1", "ts": _dt.datetime.now().isoformat(timespec="seconds"), "home": ff["home"], "files": ff, "members": {}}
    j, n = _newest_json(root / "output" / "SYS", "governance_snapshot_*.json")
    if j is None:
        s["members"]["console"] = {"state": "ABSENT", "why": "尚未跑 via-cgconsole(快照落 <root>/output/SYS)"}
    else:
        gates = [g for g in (j.get("gates") or []) if isinstance(g, dict)]
        bad = [{"code": g.get("code"), "title": g.get("title"), "status": g.get("status"), "detail": str(g.get("detail") or "")[:160]} for g in gates if str(g.get("status")).upper() in ("FAIL", "RED", "WARN", "AMBER")]
        s["members"]["console"] = {"state": str(j.get("verdict") or "?"), "snapshot": n, "stamp": j.get("stamp"), "files": j.get("files"),
                                   "gates_n": len(gates), "gates_fail": sum(1 for g in gates if str(g.get("status")).upper() in ("FAIL", "RED")),
                                   "gates_warn": sum(1 for g in gates if str(g.get("status")).upper() in ("WARN", "AMBER")), "gates_bad": bad[:12],
                                   "duplicate_groups": len(j.get("duplicate_groups") or []), "parse_failures": len(j.get("parse_failures") or []),
                                   "contract_mismatches": len(j.get("contract_mismatches") or []), "cycles": len(j.get("cycles") or [])}
    j, n = _newest_json(out / "downward" / "out", "downward_snapshot_*.json")
    s["members"]["downward"] = ({"state": "ABSENT", "why": "尚未跑 via-cgdownward"} if j is None else {"state": str(j.get("verdict") or "?"), "snapshot": n, "keys": sorted(list(j.keys()))[:12]})
    pm = out / "priority" / "priority_manifest.json"
    if pm.exists():
        try:
            j = json.loads(pm.read_text(encoding="utf-8"))
            q = j.get("queue") or j.get("files") or j.get("items") or []
            s["members"]["router"] = {"state": "OK", "queued": len(q) if isinstance(q, list) else j.get("queued"), "keys": sorted(list(j.keys()))[:12], "ts": _dt.datetime.fromtimestamp(pm.stat().st_mtime).isoformat(timespec="seconds")}
        except Exception as exc:
            s["members"]["router"] = {"state": "FAIL", "why": f"priority_manifest 讀不了:{type(exc).__name__}"}
    else:
        s["members"]["router"] = {"state": "ABSENT", "why": "尚未跑 via-cgrouter"}
    eng = out / "engine"
    if eng.exists():
        cfg = sorted((eng / "configs").glob("*.json")) if (eng / "configs").exists() else []
        s["members"]["engine"] = {"state": "OK" if cfg else "DRY", "configs": [p.name for p in cfg][:8], "logs": len(list((eng / "logs").glob("*"))) if (eng / "logs").exists() else 0}
    else:
        s["members"]["engine"] = {"state": "ABSENT", "why": "尚未跑 via-cgengine(--selftest 不落地;--seed --commit 才有 configs)"}
    sn = out / "samename"
    j, n = _newest_json(sn, "*.json") if sn.exists() else (None, "")
    s["members"]["samename"] = ({"state": "ABSENT", "why": "尚未跑 via-samename(需 pwsh 7)"} if j is None else {"state": "PLAN", "snapshot": n, "keys": sorted(list(j.keys()))[:12] if isinstance(j, dict) else []})
    worst = "OK"
    for k, m in s["members"].items():
        st = str(m.get("state"))
        if st in ("FAIL", "RED"):
            worst = "RED"
        elif st in ("ABSENT", "AMBER", "DRY", "PLAN") and worst != "RED":
            worst = "PARTIAL"
    s["state"] = worst if ff["state"] == "OK" else ff["state"]
    try:
        out.mkdir(parents=True, exist_ok=True)
        (out / "FAMILY_latest.json").write_text(json.dumps(s, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    except Exception as exc:
        s["write_why"] = f"{type(exc).__name__}"
    if do_print:
        print(f"=== [via-cgfamily] 中央治理家族 · {s['state']} · 正位 {ff['home'] or 'ABSENT'} ===")
        for k, m in ff["members"].items():
            print(f"  [{m['state']:<9}] {m['urn']:<22} {m['file']} md5 {m['md5'] or '-'}")
        for k, m in s["members"].items():
            print(f"  [{str(m.get('state')):<9}] {k:<9} " + " · ".join(f"{a}={m[a]}" for a in ("snapshot", "stamp", "queued", "configs", "why", "gates_n", "gates_fail", "gates_warn", "duplicate_groups", "parse_failures") if m.get(a) is not None))
            for g in (m.get("gates_bad") or []):
                print(f"             [{str(g.get('status')):<5}] {g.get('code')} {g.get('title')}:{g.get('detail')}")
        print(f"  存證 {out / 'FAMILY_latest.json'} · 一貼即用:via-cgfamily plan")
    return s


def plan(root: Path = VIA, do_print: bool = True) -> list:
    lines = [
        "via-cgrouter                     # 檔案優先序 L0/L1(唯讀掃描;--ocr 才把影像進佇列)→ VIA_Reports\\central_governance\\priority",
        "via-cgengine                     # 詞彙引擎 --selftest(向量測試;--seed/--observe/--normalize 皆 dry-run;--commit=你的手)",
        "via-cgconsole                    # 主控台複驗(dry-run;快照 output\\SYS;--probe 會動態載入模組頂層=你決定;--commit 發 URN 台帳=你的手)",
        "via-cgdownward                   # 下行控制 dry-run(唯讀能力;--commit --token <權杖> 才下行變更類能力)",
        "via-samename                     # 同名整併只報告(IDENTICAL/DIVERGED;--commit --token <計畫權杖> 才搬;pwsh 7)",
        "via-cgfamily                     # 五成員最新快照 → FAMILY_latest.json(VCGC 十一段)",
    ]
    if do_print:
        print("=== [via-cgfamily plan] 一貼即用(dry-run 順序;閘/權杖=你的手)===")
        for l in lines:
            print("  " + l)
    return lines


# ---------------------------------------------------------------- selftest
def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    ff = family_files()
    chk("① 家族正位在位(尾版夾 glob)且五成員 md5 對冊(原名零觸碰律的量尺)", ff["state"] == "OK" and all(m["state"] == "OK" for m in ff["members"].values()), f"({ff['home']})")
    home = family_home()
    with tempfile.TemporaryDirectory() as td:
        T = Path(td)
        r2 = run_tool(engine_argv(work=T / "engine"), timeout=120, cwd=T, log_dir=T / "logs")
        chk("② 詞彙引擎 --selftest(向量測試 PASS;工作夾在暫存;零落地入倉)", r2["state"] == "OK" and any("PASS" in l for l in r2["tail"]), f"({r2['secs']}s)")
        (T / "scan").mkdir()
        (T / "scan" / "a.py").write_text("print('x')\n" * 200, encoding="utf-8")
        (T / "scan" / "b.md").write_text("# b\n" * 400, encoding="utf-8")
        r3 = run_tool(router_argv(root=T / "scan", out=T / "prio"), timeout=120, cwd=T, log_dir=T / "logs")
        chk("③ 檔案優先序路由器(暫存夾 2 檔 → GREEN;priority_manifest/file_index/format_catalog 落 --out)",
            r3["state"] == "OK" and (r3["json"] or {}).get("verdict") == "GREEN" and (T / "prio" / "priority_manifest.json").exists() and (T / "prio" / "format_catalog.json").exists(), f"({r3['json']})")
        a_c, a_e, a_d, a_s = console_argv(root=T), engine_argv(), downward_argv(), samename_argv(root=T)
        chk("④ argv 閘律:預設不帶 --commit/--probe/--token/-Commit;--no-open/-NoBrowser 一律;downward --tools=正位夾;明給才傳",
            "--commit" not in a_c and "--probe" not in a_c and "--no-open" in a_c and "--json" in a_c
            and a_e[-2:] == ["--selftest", "--json"] and "--commit" not in a_d and "--token" not in a_d and a_d[a_d.index("--tools") + 1] == str(home)
            and "-NoBrowser" in a_s and "-Commit" not in a_s
            and "--commit" in console_argv(root=T, commit=True) and "--probe" in console_argv(root=T, probe=True)
            and "--token" in downward_argv(commit=True, token="==X-APPROVE==20260915_000000-abcdef") and "--token" not in downward_argv(commit=True, token="")
            and "-Commit" in samename_argv(root=T, commit=True, token="t") and "-IncludeDiverged" in samename_argv(root=T, diverged=True))
        s5 = status(out=T / "reports", root=T / "emptyroot", do_print=False)
        chk("⑤ status 誠實:沒跑過的成員全 ABSENT(不編)、家族 state PARTIAL、FAMILY_latest.json 落 --out",
            all(m["state"] == "ABSENT" for m in s5["members"].values()) and s5["state"] == "PARTIAL" and (T / "reports" / "FAMILY_latest.json").exists())
        (T / "root2").mkdir()
        (T / "root2" / "x_engine.py").write_text("def run():\n    return 1\n", encoding="utf-8")
        (T / "root2" / "y_tool.py").write_text("import json\n\ndef main():\n    return json.dumps({})\n", encoding="utf-8")
        r6 = run_tool(console_argv(root=T / "root2"), timeout=300, cwd=T, log_dir=T / "logs")
        snaps = sorted((T / "root2" / "output" / "SYS").glob("governance_snapshot_*.json"))
        s6 = status(out=T / "reports", root=T / "root2", do_print=False)
        chk("⑥ 主控台 dry-run 於暫存根(2 檔 → 快照 output/SYS;裁決字串 JSON)且 status 讀到它(verdict/stamp)",
            r6["state"] == "OK" and bool(snaps) and (r6["json"] or {}).get("verdict") in ("GREEN", "AMBER", "RED") and s6["members"]["console"].get("stamp"), f"({r6['json']} · {r6['secs']}s)")
        saved = os.environ.get("PYTHONHOME")
        os.environ["PYTHONHOME"] = "/nonexistent/uv/cpython-3.12"
        try:
            e7 = child_env()
        finally:
            if saved is None:
                os.environ.pop("PYTHONHOME", None)
            else:
                os.environ["PYTHONHOME"] = saved
        chk("⑦ 子行程環境=匯流排 child_env(L32 PYTHONHOME 不繼承、bootstrap 前置)+ 零彈窗 + 撤同意閘",
            "PYTHONHOME" not in e7 and e7.get("VIA_PYTHONHOME_SCRUBBED") == "/nonexistent/uv/cpython-3.12" and e7.get("VIA_NO_OPEN") == "1" and "VIA_NET_CONSENT" not in e7 and "bootstrap" in e7.get("PYTHONPATH", ""),
            f"(bus={'在' if _bus_child_env() else '缺→本地同律'})")
    src = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]     # 不讀自測本身的字串
    chk("⑧ 紀律宣告(只增不減/正本零觸碰/尾版律/Zero-Hydra/誠實三態/零 CDN/零彈窗/零網路/不代設)+ 零 requests/duckdb",
        all(k in src for k in ("只增不減", "正本零觸碰", "尾版律", "Zero-Hydra", "誠實三態", "零 CDN", "零彈窗", "零網路", "不代設")) and "import requests" not in src and "import duckdb" not in src)
    with tempfile.TemporaryDirectory() as td9:
        T9 = Path(td9)
        h9 = T9 / "VIA_CentralGovernanceFamily_b514"; h9.mkdir()
        lf = b"line1\nline2\n"
        (h9 / "VIA_FilePriorityRouter.py").write_bytes(b"\xef\xbb\xbf" + lf.replace(b"\n", b"\r\n"))
        (h9 / "MANIFEST_b514.json").write_text(json.dumps({"members": [{"file": "VIA_FilePriorityRouter.py", "md5": hashlib.md5(lf).hexdigest()}]}), encoding="utf-8")
        ff9 = family_files(h9)
        (T9 / "output" / "SYS").mkdir(parents=True)
        (T9 / "output" / "SYS" / "governance_snapshot_20260915_170320.json").write_text(json.dumps({"verdict": "RED", "stamp": "20260915_170320", "files": 3,
            "gates": [{"code": "G1", "title": "ok gate", "status": "PASS", "detail": ""}, {"code": "G7", "title": "重複家族", "status": "FAIL", "detail": "7 組 30 份"}, {"code": "G9", "title": "探針", "status": "WARN", "detail": "未啟用"}],
            "duplicate_groups": [1, 2], "parse_failures": [], "contract_mismatches": [], "cycles": []}, ensure_ascii=False), encoding="utf-8")
        s10 = status(out=T9 / "rep", root=T9, do_print=False, home=h9)
    chk("⑨ 批515 md5 對冊內容正規化:CRLF+BOM 副本(git autocrlf 簽出)與 LF 正本同 md5=OK,不再假漂移", ff9["members"]["router"]["state"] == "OK" and ff9["members"]["console"]["state"] == "ABSENT")
    c10 = s10["members"]["console"]
    chk("⑩ 批515 主控台 RED 要看得到理由:Gate 矩陣 FAIL/WARN 列 code/title/detail、重複家族/解析失敗數入 status",
        c10["state"] == "RED" and c10["gates_n"] == 3 and c10["gates_fail"] == 1 and c10["gates_warn"] == 1 and c10["gates_bad"][0]["code"] == "G7" and "7 組" in c10["gates_bad"][0]["detail"] and c10["duplicate_groups"] == 2)
    print(f"  [計] 十檢 OK {10 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def _arg(a: list, flag: str, default=None):
    if flag in a:
        i = a.index(flag)
        if i + 1 < len(a):
            return a[i + 1]
    return default


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 中央治理家族擁有者(CGC_MDL150 v0101)· 十檢自測(零網路)===")
        return selftest()
    verb = a[0] if a and not a[0].startswith("-") else "status"
    rest = a[1:] if a and not a[0].startswith("-") else a
    as_json = "--json" in rest
    if verb == "status":
        s = status(do_print=not as_json)
        if as_json:
            print(json.dumps(s, ensure_ascii=False, indent=1))
        return 0 if s["state"] in ("OK", "PARTIAL") else 1
    if verb == "plan":
        plan()
        return 0
    if family_home() is None:
        print(f"  [FAIL] 家族正位不在:{FAMILY_ROOT / FAMILY_GLOB}(誠實;拉最新樹)")
        return 2
    root = Path(_arg(rest, "--root", str(VIA))).resolve()
    if verb == "console":
        argv = console_argv(root=root, probe="--probe" in rest, commit="--commit" in rest)
    elif verb == "engine":
        argv = engine_argv([x for x in rest if x not in ("--json",)] or None)
    elif verb == "router":
        argv = router_argv(root=root, ocr="--ocr" in rest)
    elif verb == "downward":
        argv = downward_argv(commit="--commit" in rest, token=_arg(rest, "--token", "") or "", strict="--strict-chain" in rest, root=root)
    elif verb == "samename":
        argv = samename_argv(root=root, commit="--commit" in rest, token=_arg(rest, "--token", "") or "", diverged="--diverged" in rest)
    else:
        print(__doc__)
        return 2
    gates = [g for g in ("--commit", "--probe", "--token", "-Commit", "-IncludeDiverged") if g in argv]
    print(f"=== [via-cg{verb if verb != 'samename' else ''}{'samename' if verb == 'samename' else ''}] {MEMBERS[verb][1]} {MEMBERS[verb][2]} · {'dry-run' if not gates else '閘:' + ','.join(gates) + '(你的手)'} · cwd {OUT} ===")
    print("  argv: " + " ".join(Path(argv[0]).name if i == 0 else x for i, x in enumerate(argv)))
    r = run_tool(argv, timeout=int(_arg(rest, "--timeout", "1800") or 1800), cwd=OUT / verb if verb != "console" else OUT)
    for l in r["tail"]:
        print("  | " + l[:200])
    print(f"  [{r['state']}] rc={r['rc']} · {r['secs']}s" + (f" · {r['json']}" if r["json"] else ""))
    if verb in ("console", "router", "downward", "engine", "samename"):
        status(do_print=False)
    return 0 if r["state"] == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
