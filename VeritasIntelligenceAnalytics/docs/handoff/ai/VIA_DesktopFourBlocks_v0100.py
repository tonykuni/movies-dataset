#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0100]
r"""VIA_DesktopFourBlocks v0100 — 桌機四段一次自動跑完(操作員 2026-11-07「繼續桌機四段自動完成」)。

交接 §34 / §35 的四段原本要操作員一段一段貼;本支把它們包成一支 Python,桌機只貼一行,
每段有閘、有守門、有收據、可續跑;紅的照實印紅,從不把未知或缺席當綠。

段:
  ① 降壓 + 環境總檢(只讀):量 CPU / DRAM / TEMP · 列吃記憶體的前幾支(只列不殺;殺行程是操作員的手)
     → 主控台 token(閘:紅就停)· run CGC_MDL240_EnvManager(只查不裝)· env
  ② 環境布建:CGC_MDL135_EnvGovernance run → tools(只出計畫)→ conflicts;
     只有 --install 且 conflicts 沒紅、計畫有段,才跑 tools --apply --approve(VCGC 的手;本支不自己 pip)
  ③ MCP 對接:CGC_MDL279_MCPServer 尾版 --selftest → --client-config → 併進 Claude Desktop 設定檔
     (先備份 · 只動 "vcgc" 這一鍵 · 其他 server 一字不動 · 冪等);Manus 片段寫到輸出夾由操作員貼
  ④ VDF 擷取:VDF_MDL012_FetchGroups 尾版 run --dry(看道)→ 真跑(--jobs 五流 · CPU / DRAM / TEMP 守門 ·
     增量 anti-join · TEMP 為主);中斷後再跑同一行即續(已落庫的不重抓)
  ⑤ 全景三輪(選用 · 要 pwsh):Invoke-VCGC-Panorama 尾版 ps1 掃兩根

收尾:每段收據 → DESKTOP_FOUR_BLOCKS.json / .md · 貼回包 zip · 最後一行 NEXT: 給下一動。
零網路由本支發起(真抓是 VDF 自己經鎖版網路工具);只在輸出夾與(③ 明示時)用戶端設定檔寫入。
自測:python VIA_DesktopFourBlocks_v0100.py --selftest(夾具 · 零網路 · 只寫沙盒)。
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

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0100"
TAG = "VIA_DesktopFourBlocks " + VERSION
HEARTBEAT_SECONDS = 20.0
GROUPS_DEFAULT = "TW_EQUITY,TW_ETF,US_MACRO_FRED,CN_AKSHARE,GLOBAL_INDEX"
LAMP_ORDER = {"RED": 0, "YELLOW": 1, "GRAY": 2, "GREEN": 3}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def tail_of(folder: Path, pattern: str):
    """家族尾版(版號最大);沒有回 None(誠實缺席,不猜)。"""
    files = [p for p in folder.glob(pattern) if p.is_file()]
    return max(files, key=vnum) if files else None


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def read_json(path: Path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default


# ---------------------------------------------------------------- 行程 · 資源
def killpg(pid: int, sig) -> bool:
    try:
        os.killpg(pid, sig)
        return True
    except (ProcessLookupError, OSError):
        return False


def terminate_owned(proc: subprocess.Popen, grace: float = 10.0) -> None:
    """逾時:殺整個 owned process group(忽略 SIGTERM 的孫行程也帶走);Windows 用 taskkill /T /F。"""
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, timeout=30, check=False)
    else:
        killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            pass
        killpg(proc.pid, signal.SIGKILL)
    if proc.poll() is None:
        proc.kill()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass


def resources(temp_root: Path | None = None) -> dict:
    """CPU% · DRAM 可用 / 總量 GB · TEMP 可用 GB;psutil 有就用,沒有退 stdlib;量不到的回 None(不擋)。"""
    out = {"via": "stdlib", "cpu_pct": None, "mem_avail_gb": None, "mem_total_gb": None, "temp_free_gb": None}
    try:
        import psutil  # type: ignore
        out["via"] = "psutil"
        out["cpu_pct"] = round(psutil.cpu_percent(interval=0.3), 1)
        vm = psutil.virtual_memory()
        out["mem_avail_gb"] = round(vm.available / 2 ** 30, 2)
        out["mem_total_gb"] = round(vm.total / 2 ** 30, 2)
    except Exception:
        try:
            load = os.getloadavg()[0]
            out["cpu_pct"] = round(min(100.0, 100.0 * load / (os.cpu_count() or 1)), 1)
        except Exception:
            pass
        try:
            info = {}
            for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
                k, _, rest = line.partition(":")
                info[k] = int(rest.split()[0]) if rest.split() else 0
            if "MemAvailable" in info:
                out["mem_avail_gb"] = round(info["MemAvailable"] / 2 ** 20, 2)
            if "MemTotal" in info:
                out["mem_total_gb"] = round(info["MemTotal"] / 2 ** 20, 2)
        except Exception:
            pass
    try:
        target = temp_root if temp_root and Path(temp_root).exists() else Path(os.environ.get("TEMP") or "/tmp")
        out["temp_free_gb"] = round(shutil.disk_usage(str(target)).free / 2 ** 30, 2)
    except Exception:
        pass
    return out


def heavy_processes(limit: int = 8) -> list:
    """吃記憶體的前幾支(只列不殺;殺行程是操作員的手 · G4)。"""
    rows = []
    try:
        import psutil  # type: ignore
        for p in psutil.process_iter(["pid", "name", "memory_info"]):
            try:
                mi = p.info.get("memory_info")
                rows.append({"pid": p.info["pid"], "name": p.info.get("name") or "?",
                             "rss_mb": int((mi.rss if mi else 0) / 2 ** 20)})
            except Exception:
                continue
    except Exception:
        try:
            cmd = (["tasklist", "/FO", "CSV", "/NH"] if os.name == "nt"
                   else ["ps", "-eo", "pid=,rss=,comm="])
            txt = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False).stdout
            for line in txt.splitlines():
                if os.name == "nt":
                    parts = [x.strip('" ') for x in line.split('","')]
                    if len(parts) >= 5:
                        rows.append({"pid": parts[1], "name": parts[0],
                                     "rss_mb": int(re.sub(r"[^0-9]", "", parts[4]) or 0) // 1024})
                else:
                    bits = line.split(None, 2)
                    if len(bits) == 3:
                        rows.append({"pid": bits[0], "name": bits[2].strip(), "rss_mb": int(bits[1]) // 1024})
        except Exception:
            return []
    rows.sort(key=lambda r: r.get("rss_mb") or 0, reverse=True)
    return rows[:limit]


# ---------------------------------------------------------------- 一段一段跑
class Runner:
    def __init__(self, out: Path, env: dict, default_timeout: int = 1800, resume_from: dict | None = None):
        self.out = out
        self.env = env
        self.default_timeout = default_timeout
        self.receipts: list = []
        self.resume_from = resume_from or {}

    def reusable(self, label: str) -> dict | None:
        prev = self.resume_from.get(label)
        if prev and prev.get("rc") == 0 and prev.get("state") == "RETURNED_ZERO":
            row = dict(prev)
            row["reused"] = True
            self.receipts.append(row)
            write_json(self.out / "COMMANDS.json", self.receipts)
            print("[沿用] %s 前一輪已綠(rc 0)· 本輪不重跑" % label, flush=True)
            return row
        return None

    def run(self, label: str, command: list, cwd: Path, timeout: int | None = None, allow_reuse: bool = True) -> dict:
        if allow_reuse:
            got = self.reusable(label)
            if got:
                return got
        log = self.out / "logs" / (re.sub(r"[^A-Za-z0-9_.-]", "_", label) + ".log")
        log.parent.mkdir(parents=True, exist_ok=True)
        start = time.monotonic()
        row = {"id": label, "command": [str(x) for x in command], "cwd": str(cwd), "at": utc_now(),
               "log": str(log), "state": "RUNNING", "rc": None}
        self.receipts.append(row)
        write_json(self.out / "COMMANDS.json", self.receipts)
        print("[起] %s" % label, flush=True)
        limit = timeout or self.default_timeout
        try:
            with log.open("wb") as stream:
                opts = {} if os.name == "nt" else {"start_new_session": True}
                proc = subprocess.Popen([str(x) for x in command], cwd=str(cwd), env=self.env,
                                        stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, **opts)
                beat = start + HEARTBEAT_SECONDS
                while proc.poll() is None:
                    if time.monotonic() - start >= limit:
                        terminate_owned(proc)
                        row.update(rc=124, state="TIMEOUT")
                        break
                    if time.monotonic() >= beat:
                        print("[心跳] %s %.0fs · 日誌 %d 位元組" % (label, time.monotonic() - start, log.stat().st_size), flush=True)
                        beat += HEARTBEAT_SECONDS
                    time.sleep(0.25)
                if row["rc"] is None:
                    row.update(rc=proc.returncode, state="RETURNED_ZERO" if proc.returncode == 0 else "NONZERO")
        except (OSError, subprocess.SubprocessError) as exc:
            row.update(rc=125, state="ERROR", error=str(exc))
        row["seconds"] = round(time.monotonic() - start, 2)
        row["tail"] = log_tail(log)
        write_json(self.out / "COMMANDS.json", self.receipts)
        print("[完] %s rc=%s %.1fs" % (label, row["rc"], row["seconds"]), flush=True)
        return row

    def by_label(self) -> dict:
        return {r["id"]: r for r in self.receipts}


def log_tail(log: Path, lines: int = 12, width: int = 400) -> list:
    try:
        text = log.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []
    return [x[:width] for x in text[-lines:] if x.strip()]


def said_red(row: dict) -> bool:
    """收據的尾巴有沒有自報紅(RED / BLOCK / 擋下)。"""
    return any(("RED" in x) or ("BLOCK" in x) or ("擋下" in x) for x in row.get("tail") or [])


# ---------------------------------------------------------------- ③ 用戶端設定
def default_client_config_path() -> Path | None:
    if os.name == "nt":
        base = os.environ.get("APPDATA")
        return Path(base) / "Claude" / "claude_desktop_config.json" if base else None
    home = Path.home()
    mac = home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    return mac if mac.parent.exists() else home / ".config" / "Claude" / "claude_desktop_config.json"


def merge_client_config(target: Path, snippet: dict, backups: Path) -> dict:
    """把 snippet 的 mcpServers 併進用戶端設定檔:先備份 · 只動 snippet 的那幾鍵 · 其他一字不動 · 冪等。"""
    out = {"path": str(target), "backup": None, "added": [], "updated": [], "unchanged": [], "kept": []}
    servers = (snippet or {}).get("mcpServers") or {}
    if not servers:
        out["why"] = "片段沒有 mcpServers(不猜)"
        return out
    current = read_json(target, None)
    if current is None:
        current = {}
        out["created"] = True
    elif not isinstance(current, dict):
        out["why"] = "設定檔不是 JSON 物件:不動它(誠實停)"
        return out
    else:
        backups.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        copy = backups / (target.name + "." + stamp + ".bak")
        copy.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        out["backup"] = str(copy)
    existing = dict(current.get("mcpServers") or {})
    out["kept"] = sorted(k for k in existing if k not in servers)
    for name, spec in servers.items():
        if name not in existing:
            out["added"].append(name)
        elif existing[name] == spec:
            out["unchanged"].append(name)
        else:
            out["updated"].append(name)
        existing[name] = spec
    current["mcpServers"] = existing
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out["ok"] = True
    return out


def first_json_object(text: str):
    """從輸出裡取第一個完整 JSON 物件(主控台會在前面印卡片的行)。"""
    start = text.find("{")
    while start >= 0:
        try:
            obj, _ = json.JSONDecoder().raw_decode(text[start:])
            if isinstance(obj, dict):
                return obj
        except ValueError:
            pass
        start = text.find("{", start + 1)
    return None


# ---------------------------------------------------------------- 主流程
def console_of(via: Path) -> Path | None:
    return tail_of(via / "supportive modules" / "registry", "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py")


def build_env(extra: dict | None = None) -> dict:
    env = os.environ.copy()
    env.update({"VIA_FROM_VCGC": "YES", "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1",
                "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"})
    env.update(extra or {})
    return env


def worst(lamps: list) -> str:
    return min(lamps, key=lambda x: LAMP_ORDER.get(x, 1)) if lamps else "GRAY"


def run_blocks(args) -> dict:
    repo = Path(args.root).resolve()
    via = repo / "VeritasIntelligenceAnalytics" if (repo / "VeritasIntelligenceAnalytics").is_dir() else repo
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    env_root = args.env_root or os.environ.get("VIA_ENV_ROOT") or str(Path.home() / "envs")
    env = build_env({"VIA_ENV_ROOT": env_root})
    prev = {}
    if args.resume:
        for row in (read_json(Path(args.resume) / "COMMANDS.json", []) or []):
            if isinstance(row, dict) and row.get("id"):
                prev[row["id"]] = row
    runner = Runner(out, env, args.step_timeout, prev)
    report = {"tool": TAG, "at": utc_now(), "repo": str(repo), "via": str(via), "out": str(out),
              "env_root": env_root, "python": sys.version.split()[0], "os": os.name,
              "blocks": {}, "lamps": {}, "next": "", "resume_from": args.resume or None}
    console = console_of(via)
    if console is None:
        report["blocks"]["gate"] = {"lamp": "RED", "why": "找不到 VCGC 主控台尾版(CGC_MDL149_*):倉根給錯?"}
        report["lamps"]["gate"] = "RED"
        finish(report, runner, out, args)
        return report
    report["console"] = str(console)
    want = {int(x) for x in str(args.blocks).replace(" ", "").split(",") if x.isdigit()}

    def call(label, words, timeout=None, allow_reuse=True):
        return runner.run(label, [sys.executable, str(console), *words], repo, timeout, allow_reuse)

    # ① 降壓 + 環境總檢(只讀)
    if 1 in want:
        res = resources()
        heavy = heavy_processes()
        print("[① 資源] CPU %s%% · DRAM 可用 %s/%s GB · TEMP 可用 %s GB · 量測 %s"
              % (res["cpu_pct"], res["mem_avail_gb"], res["mem_total_gb"], res["temp_free_gb"], res["via"]), flush=True)
        for row in heavy[:5]:
            print("   吃記憶體 %s (pid %s) %s MB" % (row["name"], row["pid"], row["rss_mb"]), flush=True)
        token = call("01_token", ["token"], args.step_timeout)
        envman = call("02_envmanager", ["run", "CGC_MDL240_EnvManager"], args.step_timeout)
        envcard = call("03_env", ["env"], args.step_timeout)
        lamp = "GREEN" if token["rc"] == 0 else "RED"
        if lamp == "GREEN" and (envman["rc"] not in (0, 2) or envcard["rc"] not in (0, 2)):
            lamp = "YELLOW"
        report["blocks"]["1_pressure_env_audit"] = {
            "lamp": lamp, "resources": res, "heavy_processes": heavy,
            "token_rc": token["rc"], "envmanager_rc": envman["rc"], "env_rc": envcard["rc"],
            "note": "只列不殺行程(殺行程是操作員的手);EnvManager 只查不裝"}
        report["lamps"]["1"] = lamp
        if token["rc"] != 0:
            report["next"] = "NEXT: [RED] ① token 閘紅 —— 先修省 Token 步(via-vcgc token),其餘段不跑"
            finish(report, runner, out, args)
            return report

    # ② 環境布建(零安裝預設;裝要 --install 且無衝突)
    if 2 in want:
        gov = "CGC_MDL135_EnvGovernance"
        plan = call("04_envgov_run", ["run", gov, "run", "--env-root", env_root]
                    + (["--base-python", args.base_python] if args.base_python else []), args.gov_timeout)
        tools = call("05_envgov_tools", ["run", gov, "tools", "--env-root", env_root], args.gov_timeout)
        conf = call("06_envgov_conflicts", ["run", gov, "conflicts"], args.step_timeout)
        blocked = said_red(conf) or said_red(plan)
        applied = None
        if args.install and not blocked:
            applied = call("07_envgov_tools_apply",
                           ["run", gov, "tools", "--apply", "--approve", "--env-root", env_root],
                           args.gov_timeout, allow_reuse=False)
        lamp = "GREEN"
        if blocked:
            lamp = "RED"
        elif applied is None:
            lamp = "YELLOW"      # 計畫出了但沒裝(--no-install 或被擋)
        elif applied["rc"] not in (0, 2):
            lamp = "RED"
        report["blocks"]["2_environment"] = {
            "lamp": lamp, "env_root": env_root, "base_python": args.base_python,
            "run_rc": plan["rc"], "tools_plan_rc": tools["rc"], "conflicts_rc": conf["rc"],
            "apply_rc": (applied or {}).get("rc"), "install_requested": bool(args.install),
            "blocked_by_conflicts": blocked,
            "note": "零安裝零刪除預設;破壞段永不自動;裝只經 VCGC 的 tools --apply --approve",
            "plan_file": str(via / "VIA_Reports" / "env_governance" / "TOOLS_PLAN_latest.json")}
        report["lamps"]["2"] = lamp

    # ③ MCP 對接
    if 3 in want:
        reg = via / "supportive modules" / "registry"
        server = tail_of(reg, "CGC_MDL279_MCPServer_v*.py")
        if server is None:
            report["blocks"]["3_mcp"] = {"lamp": "GRAY", "why": "找不到 CGC_MDL279_MCPServer 尾版"}
            report["lamps"]["3"] = "GRAY"
        else:
            st = runner.run("08_mcp_selftest", [sys.executable, str(server), "--selftest"], repo, args.step_timeout)
            cc = runner.run("09_mcp_client_config", [sys.executable, str(server), "--client-config", "--root", str(repo)],
                            repo, args.step_timeout, allow_reuse=False)
            snippet = first_json_object(Path(cc["log"]).read_text(encoding="utf-8", errors="replace")) if cc["rc"] == 0 else None
            if snippet:
                write_json(out / "MCP_CLIENT_CONFIG.json", snippet)
            merged = {"skipped": True, "why": "--no-mcp-write"}
            if snippet and args.mcp_write:
                target = Path(args.mcp_config) if args.mcp_config else default_client_config_path()
                merged = ({"skipped": True, "why": "這台找不到用戶端設定檔路徑"} if target is None
                          else merge_client_config(target, snippet, out / "client_config_backups"))
            lamp = "GREEN" if (st["rc"] == 0 and snippet and (merged.get("ok") or merged.get("skipped"))) else "RED"
            if lamp == "GREEN" and merged.get("skipped"):
                lamp = "YELLOW"
            report["blocks"]["3_mcp"] = {"lamp": lamp, "server": str(server), "selftest_rc": st["rc"],
                                         "client_config_rc": cc["rc"], "snippet_written": bool(snippet),
                                         "client_config_merge": merged,
                                         "manus_note": "Manus 加自訂 MCP server:command / args 同本片段(stdio · 只讀)"}
            report["lamps"]["3"] = lamp

    # ④ VDF 擷取(先 --dry 看道,再真跑;中斷再跑同一行即續)
    if 4 in want:
        vdf = via / "functional modules" / "VDF"
        mdl012 = tail_of(vdf, "VDF_MDL012_FetchGroups_v*.py")
        if mdl012 is None:
            report["blocks"]["4_vdf_fetch"] = {"lamp": "GRAY", "why": "找不到 VDF_MDL012_FetchGroups 尾版"}
            report["lamps"]["4"] = "GRAY"
        else:
            base = [sys.executable, str(mdl012), "run", "--groups", args.groups, "--jobs", str(args.jobs),
                    "--mode", args.mode, "--cpu-max", str(args.cpu_max), "--mem-min-gb", str(args.mem_min_gb),
                    "--temp-min-gb", str(args.temp_min_gb)]
            dry = runner.run("10_vdf_dry", base + ["--dry"], vdf, args.step_timeout)
            live = None
            if not args.dry_only and dry["rc"] in (0, 2):
                live = runner.run("11_vdf_live", list(base), vdf, args.fetch_timeout, allow_reuse=False)
            lamp = "GREEN"
            if dry["rc"] not in (0, 2):
                lamp = "RED"
            elif live is None:
                lamp = "YELLOW"
            elif live["rc"] not in (0, 2):
                lamp = "RED"
            report["blocks"]["4_vdf_fetch"] = {
                "lamp": lamp, "engine": str(mdl012), "groups": args.groups, "jobs": args.jobs, "mode": args.mode,
                "governor": {"cpu_max": args.cpu_max, "mem_min_gb": args.mem_min_gb, "temp_min_gb": args.temp_min_gb},
                "dry_rc": dry["rc"], "live_rc": (live or {}).get("rc"), "dry_only": bool(args.dry_only),
                "note": "增量 anti-join:中斷後再跑同一行即續,已落庫的不重抓;TEMP 為主(VIA_TEMP_ROOT)"}
            report["lamps"]["4"] = lamp

    # ⑤ 全景三輪(選用;要 pwsh)
    if 5 in want:
        pwsh = args.pwsh or shutil.which("pwsh") or shutil.which("powershell")
        ps1 = tail_of(via / "docs" / "handoff" / "ai" / "vcgc_panorama_v0100", "Invoke-VCGC-Panorama-v*.ps1")
        if not pwsh or ps1 is None:
            report["blocks"]["5_panorama"] = {"lamp": "GRAY",
                                              "why": ("沒有 pwsh(不裝)" if not pwsh else "找不到 Invoke-VCGC-Panorama ps1")}
            report["lamps"]["5"] = "GRAY"
        else:
            cmd = [pwsh, "-NoLogo", "-NoProfile", "-NonInteractive", "-File", str(ps1),
                   "-Roots", str(via), "-ViaRoot", str(via), "-NoOpen"]
            pano = runner.run("12_panorama", cmd, repo, args.panorama_timeout)
            lamp = "GREEN" if pano["rc"] == 0 else ("YELLOW" if pano["rc"] in (2, 5) else "RED")
            report["blocks"]["5_panorama"] = {"lamp": lamp, "ps1": str(ps1), "rc": pano["rc"],
                                              "note": "v0101 預設沿用相依未變的站收據;要全站重跑加 -ForceFull"}
            report["lamps"]["5"] = lamp

    finish(report, runner, out, args)
    return report


def finish(report: dict, runner: Runner, out: Path, args) -> None:
    report["commands"] = runner.receipts
    report["overall"] = worst(list(report["lamps"].values()))
    report["finished_at"] = utc_now()
    if not report.get("next"):
        reds = [k for k, v in report["lamps"].items() if v == "RED"]
        yellows = [k for k, v in report["lamps"].items() if v == "YELLOW"]
        if reds:
            report["next"] = "NEXT: [RED] 段 %s 紅 —— 看 %s 的 logs,修完再跑同一行(綠的段會沿用)" % (",".join(reds), out)
        elif yellows:
            report["next"] = "NEXT: [YELLOW] 段 %s 黃(沒裝 / 沒真跑 / 沒寫設定)—— 要補就加 --install · --mcp-write · 去掉 --dry-only" % ",".join(yellows)
        else:
            report["next"] = "NEXT: [GREEN] 四段都綠 —— 把 %s 的 zip 貼回給 AI" % out
    write_json(out / "DESKTOP_FOUR_BLOCKS.json", report)
    (out / "DESKTOP_FOUR_BLOCKS.md").write_text(render_md(report), encoding="utf-8")
    bundle = out / ("VIA_DesktopFourBlocks_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".zip")
    try:
        with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(out.rglob("*")):
                if path.is_file() and path != bundle and path.suffix != ".zip":
                    zf.write(path, str(path.relative_to(out)))
        report["bundle"] = str(bundle)
        write_json(out / "DESKTOP_FOUR_BLOCKS.json", report)
    except OSError as exc:
        report["bundle_error"] = str(exc)
    print(render_md(report), flush=True)
    print(report["next"], flush=True)


def render_md(report: dict) -> str:
    rows = ["# %s · 桌機四段" % report.get("tool", TAG), "",
            "- 時間 %s → %s · 倉 %s · 境根 %s" % (report.get("at"), report.get("finished_at", "(跑中)"),
                                               report.get("repo"), report.get("env_root")),
            "- 總燈 **%s**" % report.get("overall", "?"), "", "| 段 | 燈 | 重點 |", "|---|---|---|"]
    names = {"1_pressure_env_audit": "① 降壓 + 環境總檢", "2_environment": "② 環境布建",
             "3_mcp": "③ MCP 對接", "4_vdf_fetch": "④ VDF 擷取", "5_panorama": "⑤ 全景三輪", "gate": "閘"}
    for key, block in (report.get("blocks") or {}).items():
        bits = []
        for field in ("why", "token_rc", "conflicts_rc", "apply_rc", "selftest_rc", "dry_rc", "live_rc", "rc", "note"):
            if field in block and block[field] is not None:
                bits.append("%s=%s" % (field, block[field]))
        rows.append("| %s | %s | %s |" % (names.get(key, key), block.get("lamp", "?"), " · ".join(bits)[:300]))
    rows += ["", "收據:COMMANDS.json · logs/ · 貼回包 %s" % report.get("bundle", "(沒出)"), "", report.get("next", "")]
    return "\n".join(rows) + "\n"


# ---------------------------------------------------------------- 自測(夾具 · 零網路 · 只寫沙盒)
def selftest() -> int:
    import tempfile
    from unittest.mock import patch
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    print("=== %s 自測 ===" % TAG, flush=True)
    with tempfile.TemporaryDirectory(prefix="dfb_") as td:
        root = Path(td)
        via = root / "repo" / "VeritasIntelligenceAnalytics"
        reg = via / "supportive modules" / "registry"
        vdf = via / "functional modules" / "VDF"
        for d in (reg, vdf):
            d.mkdir(parents=True, exist_ok=True)
        log = root / "verbs.log"
        console = reg / "CGC_MDL149_VeritasCentralGovernanceConsole_v0001.py"
        console.write_text(
            "import sys\nfrom pathlib import Path\n"
            "args = sys.argv[1:]\n"
            "Path(%r).open('a', encoding='utf-8').write(' '.join(args) + '\\n')\n"
            "print('FIXTURE', args)\n"
            "if args[:3] == ['run', 'CGC_MDL135_EnvGovernance', 'conflicts']:\n"
            "    print('[VCGC 衝突閘] GREEN 現況乾淨')\n"
            "raise SystemExit(0)\n" % str(log), encoding="utf-8")
        server = reg / "CGC_MDL279_MCPServer_v0009.py"
        server.write_text(
            "import json, sys\n"
            "if '--selftest' in sys.argv:\n    print('[PASS] fixture selftest')\n    raise SystemExit(0)\n"
            "print('卡片一行,不是 JSON')\n"
            "print(json.dumps({'mcpServers': {'vcgc': {'command': 'python', 'args': ['x.py', '--serve']}}}, ensure_ascii=False, indent=2))\n"
            "raise SystemExit(0)\n", encoding="utf-8")
        fetch = vdf / "VDF_MDL012_FetchGroups_v0009.py"
        fetch.write_text(
            "import sys\nfrom pathlib import Path\n"
            "Path(%r).open('a', encoding='utf-8').write('MDL012 ' + ' '.join(sys.argv[1:]) + '\\n')\n"
            "print('[run · 並行] 夾具')\nraise SystemExit(0)\n" % str(log), encoding="utf-8")
        out1 = root / "out1"

        def make_args(**over):
            base = dict(root=str(root / "repo"), out=str(out1), env_root=str(root / "envs"), base_python=None,
                        blocks="1,2,3,4,5", install=False, mcp_write=False, mcp_config=None, groups=GROUPS_DEFAULT,
                        jobs=5, mode="live", cpu_max=80.0, mem_min_gb=3.0, temp_min_gb=8.0, dry_only=True,
                        pwsh="", step_timeout=120, gov_timeout=120, fetch_timeout=120, panorama_timeout=120,
                        resume=None, selftest=False)
            base.update(over)
            return argparse.Namespace(**base)

        rep = run_blocks(make_args())
        verbs = log.read_text(encoding="utf-8").splitlines()
        chk("① token → EnvManager → env 都經主控台;只列不殺行程",
            verbs[:3] == ["token", "run CGC_MDL240_EnvManager", "env"]
            and "heavy_processes" in rep["blocks"]["1_pressure_env_audit"], verbs[:3])
        chk("② 預設不裝:run / tools / conflicts 跑了,沒有 --apply --approve",
            any(v.startswith("run CGC_MDL135_EnvGovernance run") for v in verbs)
            and any("tools --env-root" in v for v in verbs)
            and not any("--apply --approve" in v for v in verbs)
            and rep["blocks"]["2_environment"]["lamp"] == "YELLOW")
        chk("③ client-config 的 JSON 從夾雜輸出裡取出 · 片段落地 · 預設不寫用戶端設定檔",
            (out1 / "MCP_CLIENT_CONFIG.json").is_file()
            and read_json(out1 / "MCP_CLIENT_CONFIG.json")["mcpServers"]["vcgc"]["command"] == "python"
            and rep["blocks"]["3_mcp"]["client_config_merge"].get("skipped") is True
            and rep["blocks"]["3_mcp"]["lamp"] == "YELLOW")
        chk("④ --dry-only 只跑 --dry(不真跑)· 五流與守門照帶",
            any("MDL012 run --groups" in v and "--jobs 5" in v and "--cpu-max 80" in v and v.endswith("--dry") for v in verbs)
            and not any(v.startswith("MDL012") and not v.endswith("--dry") for v in verbs)
            and rep["blocks"]["4_vdf_fetch"]["lamp"] == "YELLOW")
        chk("⑤ 沒有 pwsh → GRAY(不裝 · 不冒充綠)",
            rep["blocks"]["5_panorama"]["lamp"] == "GRAY" and "pwsh" in rep["blocks"]["5_panorama"]["why"])
        chk("總燈 = 最差的那一盞(有黃無紅 → YELLOW)", rep["overall"] == "YELLOW", rep["overall"])
        chk("收據 · 報告 · 貼回包都在輸出夾",
            (out1 / "COMMANDS.json").is_file() and (out1 / "DESKTOP_FOUR_BLOCKS.json").is_file()
            and (out1 / "DESKTOP_FOUR_BLOCKS.md").is_file() and str(rep.get("bundle", "")).endswith(".zip")
            and zipfile.ZipFile(rep["bundle"]).namelist())
        chk("NEXT: 一行在最後 · 黃的段點名", rep["next"].startswith("NEXT: [YELLOW]"), rep["next"][:60])

        # 第二輪:--install + 寫設定 + 真跑 + 續跑沿用
        cfg = root / "claude_desktop_config.json"
        cfg.write_text(json.dumps({"mcpServers": {"other": {"command": "node"}}, "theme": "dark"},
                                  ensure_ascii=False, indent=2), encoding="utf-8")
        out2 = root / "out2"
        log.write_text("", encoding="utf-8")
        rep2 = run_blocks(make_args(out=str(out2), install=True, mcp_write=True, mcp_config=str(cfg),
                                    dry_only=False, resume=str(out1)))
        verbs2 = log.read_text(encoding="utf-8").splitlines()
        merged = read_json(cfg)
        chk("② --install 且 conflicts 沒紅 → 才跑 tools --apply --approve",
            any("--apply --approve" in v for v in verbs2) and rep2["blocks"]["2_environment"]["lamp"] == "GREEN")
        chk("③ 併設定:vcgc 加進去 · 別人的 server 與其他鍵一字不動 · 有備份",
            merged["mcpServers"]["vcgc"]["command"] == "python" and merged["mcpServers"]["other"]["command"] == "node"
            and merged.get("theme") == "dark"
            and rep2["blocks"]["3_mcp"]["client_config_merge"]["added"] == ["vcgc"]
            and Path(rep2["blocks"]["3_mcp"]["client_config_merge"]["backup"]).is_file())
        chk("④ 去掉 --dry-only → 看道過了就真跑一次(帶 --resume 時看道那段照沿用,真跑永不沿用)",
            rep2["blocks"]["4_vdf_fetch"]["dry_rc"] == 0
            and any(r.get("id") == "10_vdf_dry" and r.get("reused") for r in rep2["commands"])
            and any(v.startswith("MDL012") and not v.endswith("--dry") for v in verbs2)
            and rep2["blocks"]["4_vdf_fetch"]["lamp"] == "GREEN")
        chk("續跑:前一輪綠的只讀段沿用(01_token 不重跑)· 會變的段照跑",
            any(r.get("id") == "01_token" and r.get("reused") for r in rep2["commands"])
            and "token" not in verbs2
            and any(r.get("id") == "11_vdf_live" and not r.get("reused") for r in rep2["commands"]))
        out3 = root / "out3"
        rep3 = run_blocks(make_args(out=str(out3), mcp_write=True, mcp_config=str(cfg), blocks="3"))
        chk("③ 冪等:同一片段再併一次 = unchanged,不重複寫壞",
            rep3["blocks"]["3_mcp"]["client_config_merge"]["unchanged"] == ["vcgc"]
            and read_json(cfg)["mcpServers"]["other"]["command"] == "node")
        # 閘:token 紅就停
        bad = reg / "CGC_MDL149_VeritasCentralGovernanceConsole_v0002.py"
        bad.write_text("import sys\nprint('token RED')\nraise SystemExit(1)\n", encoding="utf-8")
        out4 = root / "out4"
        rep4 = run_blocks(make_args(out=str(out4), blocks="1,2,3,4"))
        chk("閘:token 紅 → 停,② ③ ④ 都不跑",
            rep4["lamps"]["1"] == "RED" and set(rep4["blocks"]) == {"1_pressure_env_audit"}
            and rep4["overall"] == "RED" and rep4["next"].startswith("NEXT: [RED]"))
        # 逾時殺整組
        with tempfile.TemporaryDirectory(prefix="dfb_to_") as td2:
            folder = Path(td2)
            pid_file = folder / "child.pid"
            child = folder / "child.py"
            child.write_text("import os, signal, sys, time\nsignal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                             "open(sys.argv[1], 'w').write(str(os.getpid()))\ntime.sleep(60)\n", encoding="utf-8")
            parent = folder / "parent.py"
            parent.write_text("import subprocess, sys, time\n"
                              "subprocess.Popen([sys.executable, %r, %r])\ntime.sleep(60)\n"
                              % (str(child), str(pid_file)), encoding="utf-8")
            r = Runner(folder / "out", build_env(), 2)
            row = r.run("timeout_probe", [sys.executable, str(parent)], folder, 2)
            alive = True
            if os.name != "nt" and pid_file.is_file():
                pid = int(pid_file.read_text())
                for _ in range(40):
                    try:
                        os.kill(pid, 0)
                    except ProcessLookupError:
                        alive = False
                        break
                    time.sleep(0.25)
            else:
                alive = False
            chk("逾時:rc 124 · 忽略 SIGTERM 的孫行程也被帶走", row["rc"] == 124 and row["state"] == "TIMEOUT" and not alive)
        # 壞設定檔不動它
        broken = root / "broken.json"
        broken.write_text("[1,2,3]", encoding="utf-8")
        res = merge_client_config(broken, {"mcpServers": {"vcgc": {"command": "python"}}}, root / "bk")
        chk("③ 設定檔不是 JSON 物件 → 誠實停,不覆蓋",
            res.get("ok") is None and broken.read_text(encoding="utf-8") == "[1,2,3]")
        text = Path(__file__).read_text(encoding="utf-8")
        chk("本支帶加速器橋(標記 + 真載)· 第 3 行標記 · 不含 TA-Lib · 沒有自己 pip",
            "[VIA:ACCEL-BRIDGE" in text and "VIA_ACCEL in globals()".replace("X", "") and ("VIA_ACCEL" in globals())
            and text.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0100]"
            and not re.search(r"^\s*(?:import|from)\s+talib\b", text, re.M)
            and not re.search(r"pip\s+install", text))
    bad_n = len([x for x in ok if not x])
    print("[計] %s 自測 %d/%d · %s" % (TAG, len(ok) - bad_n, len(ok), "PASS" if not bad_n else "FAIL"), flush=True)
    return 0 if not bad_n else 1


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog=TAG, description="桌機四段一次自動跑完(降壓 / 環境 / MCP / VDF 擷取 + 選用全景)")
    home = str(Path.home())
    p.add_argument("--root", default=str(Path(home) / "OneDrive" / "Documents" / "movies-dataset"), help="倉根(含 VeritasIntelligenceAnalytics)")
    p.add_argument("--out", default="", help="輸出夾(預設 <倉根>/VIA_Reports/desktop_four_blocks/<時戳>)")
    p.add_argument("--env-root", default="", help="受管境根(預設 %USERPROFILE%\\envs)")
    p.add_argument("--base-python", default="", help="系統 base 的 python.exe(給 ② 用;不給就不帶)")
    p.add_argument("--blocks", default="1,2,3,4,5", help="要跑哪幾段(預設全跑;例 --blocks 3,4)")
    p.add_argument("--install", action="store_true", help="② 無衝突時真的裝(tools --apply --approve);預設只出計畫")
    p.add_argument("--mcp-write", action="store_true", help="③ 把 vcgc 併進用戶端設定檔(先備份 · 只動這一鍵)")
    p.add_argument("--mcp-config", default="", help="③ 用戶端設定檔路徑(預設 Claude Desktop 的位置)")
    p.add_argument("--groups", default=GROUPS_DEFAULT, help="④ 要跑的資料集族群")
    p.add_argument("--jobs", type=int, default=5, help="④ 同時幾流(1~5)")
    p.add_argument("--mode", default="live", choices=["live", "fixture", "block"], help="④ 擷取模式")
    p.add_argument("--cpu-max", type=float, default=80.0)
    p.add_argument("--mem-min-gb", type=float, default=3.0)
    p.add_argument("--temp-min-gb", type=float, default=8.0)
    p.add_argument("--dry-only", action="store_true", help="④ 只看道不真跑")
    p.add_argument("--pwsh", default="", help="⑤ pwsh 路徑(不給就自己找;找不到 GRAY)")
    p.add_argument("--step-timeout", type=int, default=1800)
    p.add_argument("--gov-timeout", type=int, default=5400)
    p.add_argument("--fetch-timeout", type=int, default=43200)
    p.add_argument("--panorama-timeout", type=int, default=43200)
    p.add_argument("--resume", default="", help="沿用前一輪輸出夾裡綠的只讀段")
    p.add_argument("--selftest", action="store_true")
    return p


def main(argv=None) -> int:
    args = make_parser().parse_args(argv)
    if args.selftest:
        return selftest()
    if not args.out:
        repo = Path(args.root).resolve()
        via = repo / "VeritasIntelligenceAnalytics" if (repo / "VeritasIntelligenceAnalytics").is_dir() else repo
        args.out = str(via / "VIA_Reports" / "desktop_four_blocks" / datetime.now().strftime("%Y%m%d_%H%M%S"))
    args.base_python = args.base_python or None
    report = run_blocks(args)
    return {"GREEN": 0, "YELLOW": 2, "GRAY": 2, "RED": 1}.get(report.get("overall", "RED"), 1)


if __name__ == "__main__":
    sys.exit(main())
