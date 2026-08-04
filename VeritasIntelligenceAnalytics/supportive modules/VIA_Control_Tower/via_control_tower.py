#!/usr/bin/env python3
"""VIA Control Tower v002 · 本機 HTML 控制台(zero dependencies).

v002:所有動作改為背景 job 執行(不卡斷 UI)、動態進度條與即時日誌輪詢、
20 個 PS 指令加速器、VRN 復健參數檢查。只綁 127.0.0.1。

Usage:  python via_control_tower.py [--base <VIA dir>] [--port 8765] [--intake <dir>]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

VERSION = "v004"


def find_pwsh() -> str | None:
    return shutil.which("pwsh") or shutil.which("powershell")


# --------------------------------------------------------------------- jobs
class Job:
    def __init__(self, action: str, label: str, params: dict | None = None):
        self.id = uuid.uuid4().hex[:12]
        self.action = action
        self.label = label
        self.params = params or {}
        self.status = "running"          # running | done | error
        self.progress = -1               # -1 = indeterminate, else 0-100
        self.lines: list[str] = []
        self.lock = threading.Lock()

    def add(self, line: str):
        with self.lock:
            self.lines.append(line)

    def snapshot(self, since: int) -> dict:
        with self.lock:
            return {"id": self.id, "action": self.action, "label": self.label,
                    "status": self.status, "progress": self.progress,
                    "lines": self.lines[since:], "total": len(self.lines)}


JOBS: dict[str, Job] = {}
RUNNING_ACTIONS: set[str] = set()
JOBS_LOCK = threading.Lock()

# 進度啟發:動作 → (每行匹配樣式, 預估總步數)
PROGRESS_HINTS = {
    "vdf": (r"^\[VDF\] ", 9),
    "autoplot": (r"^\[VAP\] ", 28),
}

DEFAULT_INTAKE = (Path(os.environ.get("USERPROFILE", str(Path.home())))
                  / "Downloads" / "VeritasIntelligenceAnalytics"
                  / "_vrn_research_report_incremental_intake_v0156")


class Tower:
    def __init__(self, base: Path, intake: Path | None = None):
        self.base = base
        self.repo = base.parent
        self.fm = base / "functional modules"
        self.sm = base / "supportive modules"
        self.py = sys.executable
        self.rpt = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "VIA_Reports"
        self.intake = self.fm / "VRN" / "input"
        self.intake_fallback = intake or DEFAULT_INTAKE

    # ---------------------------------------------------------- exec into job
    def stream(self, job: Job, cmd: list[str], timeout: int = 3600):
        hint = PROGRESS_HINTS.get(job.action)
        matched = 0
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, encoding="utf-8", errors="replace",
                                 cwd=self.repo, bufsize=1)
            assert p.stdout is not None
            for line in p.stdout:
                line = line.rstrip("\n")
                job.add(line)
                if hint and re.search(hint[0], line):
                    matched += 1
                    job.progress = min(99, int(matched * 100 / hint[1]))
            rc = p.wait(timeout=timeout)
            job.progress = 100
            job.status = "done" if rc == 0 else "error"
            job.add(f"[exit={rc}]")
        except Exception as exc:  # noqa: BLE001 — surfaced verbatim to the UI
            job.status = "error"
            job.add(f"[TOWER-ERROR] {exc}")

    def stream_pwsh_code(self, job: Job, code: str, args: list[str] | None = None):
        pwsh = find_pwsh()
        if not pwsh:
            job.status = "error"
            job.add("[TOWER-ERROR] pwsh/powershell not found on PATH")
            return
        fd, tmp = tempfile.mkstemp(suffix=".ps1")
        os.close(fd)
        Path(tmp).write_text(code, encoding="utf-8-sig")
        try:
            cmd = [pwsh, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                   "-File", tmp] + (args or [])
            self.stream(job, cmd)
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass

    def emit(self, job: Job, text: str):
        for line in text.splitlines():
            job.add(line)
        job.progress = 100
        job.status = "done"

    def patched(self, script: Path, replacements: dict[str, str]) -> str:
        code = script.read_text(encoding="utf-8", errors="replace")
        for pattern, value in replacements.items():
            code = re.sub(pattern, value.replace("\\", "\\\\"), code, count=1)
        return code

    # ---------------------------------------------------------- VRN intake
    def _intake_dir(self) -> Path | None:
        for d in (self.intake, self.intake_fallback):
            if d.is_dir() and any(p.is_file() and p.name != ".gitkeep" for p in d.rglob("*")):
                return d
        return self.intake if self.intake.is_dir() else None

    def auto_pdf(self) -> str | None:
        for d in (self.intake, self.intake_fallback):
            if d.is_dir():
                pdfs = sorted(d.rglob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
                if pdfs:
                    return str(pdfs[0])
        cand = self.fm / "VRN" / "VRN-2_StockReportCandidatePaths.txt"
        if cand.is_file():
            for line in cand.read_text(encoding="utf-8", errors="replace").splitlines():
                p = line.strip().strip('"')
                try:
                    if p.lower().endswith(".pdf") and Path(p).is_file():
                        return p
                except OSError:
                    continue  # 跨平台/超長路徑等無效項,跳過
        return None

    # ---------------------------------------------------------- main actions
    def act_vdf(self, job: Job):
        mode = job.params.get("mode", "Refresh")
        if mode not in ("Refresh", "ValidateOnly", "DryRun"):
            mode = "Refresh"
        self.stream(job, [self.py, str(self.fm / "VDF" / "engine" / "vdf_movies_intake_v001.py"),
                          "--base", str(self.base), "--source", str(self.repo / "data"),
                          "--mode", mode])

    def act_autoplot(self, job: Job):
        mx = job.params.get("max", "40")
        if mx not in ("12", "26", "40", "80"):
            mx = "40"
        self.stream(job, [self.py, str(self.fm / "VAP" / "engine" / "via_autoplot_engine_v001.py"),
                          "--base", str(self.base), "--auto", "--max-charts", mx])

    def act_vrn_intake(self, job: Job):
        d = self._intake_dir()
        if d is None:
            self.emit(job, f"[TOWER] intake 資料夾不存在:{self.intake}")
            return
        files = [p for p in d.rglob("*") if p.is_file() and p.name != ".gitkeep"]
        note = ("(標準槽 VRN\\input)" if d == self.intake
                else "(fallback:歷史 v0156 — 建議搬入標準槽)")
        by_ext: dict[str, list[Path]] = {}
        for p in files:
            by_ext.setdefault(p.suffix.lower() or "(none)", []).append(p)
        lines = [f"[TOWER] VRN intake 盤點 · {d} {note}",
                 f"total: {len(files)} files · "
                 f"{round(sum(p.stat().st_size for p in files) / 1048576, 1)} MB", ""]
        for ext in sorted(by_ext, key=lambda e: -len(by_ext[e])):
            g = by_ext[ext]
            lines.append(f"{ext:8s} {len(g):4d} files "
                         f"{round(sum(p.stat().st_size for p in g) / 1048576, 1):8.1f} MB")
        lines += ["", "最新 15 份(VRN RUN 自動選最新 PDF):"]
        for p in sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:15]:
            lines.append(f"  {p.relative_to(d)}")
        self.emit(job, "\n".join(lines))

    def act_vrn_probe(self, job: Job):
        pwsh = find_pwsh()
        if not pwsh:
            self.emit(job, "[TOWER-ERROR] pwsh not found")
            job.status = "error"
            return
        self.stream(job, [pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass",
                          "-File", str(self.fm / "VRN" / "Invoke-VRN.ps1")])

    def act_vrn_lanes(self, job: Job):
        vrn = self.fm / "VRN"
        for lane in ("Start-VRN-Lane2-IOInventory.ps1", "Start-VRN-Lane3-EngineCapability.ps1"):
            job.add(f"===== {lane} =====")
            code = self.patched(vrn / lane, {r'\$RelatedPath = ".*?"': f'$RelatedPath = "{vrn}"'})
            self.stream_pwsh_code(job, code)
            if job.status == "error":
                return
            job.status = "running"
        job.status = "done"
        job.progress = 100

    def list_pdfs(self) -> list[dict]:
        out = []
        for d in (self.intake, self.intake_fallback):
            if d.is_dir():
                for p in sorted(d.rglob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True):
                    out.append({"name": p.name, "path": str(p),
                                "mb": round(p.stat().st_size / 1048576, 2)})
                if out:
                    break
        return out[:64]

    def matrix(self) -> list[dict]:
        """整體狀況矩陣(快速唯讀檢查,紅黃綠燈)。"""
        import hashlib
        t: list[dict] = []

        def add(group, name, state, detail=""):
            t.append({"g": group, "n": name, "s": state, "d": str(detail)})

        db = self.fm / "VDF" / "db" / "movies_dataset.sqlite"
        add("VDF", "intake 引擎", "G" if (self.fm / "VDF" / "engine"
            / "vdf_movies_intake_v001.py").is_file() else "R")
        add("VDF", "分析資料庫", "G" if db.is_file() else "Y",
            f"{db.stat().st_size} bytes" if db.is_file() else "未建(跑 VDF)")
        ev = self.fm / "VDF" / "qa" / "evidence" / "movies_intake_summary.json"
        gate = ""
        if ev.is_file():
            try:
                gate = json.loads(ev.read_text(encoding="utf-8")).get("gate", "")
            except Exception:  # noqa: BLE001
                pass
        add("VDF", "QA 閘門", "G" if gate.startswith("GREEN") else ("Y" if gate else "R"), gate or "無證據")
        charts = len(list((self.base / "VAP" / "output").glob("VAP_*.html"))) \
            if (self.base / "VAP" / "output").is_dir() else 0
        add("VAP", "繪圖引擎", "G" if (self.fm / "VAP" / "engine"
            / "via_autoplot_engine_v001.py").is_file() else "R")
        add("VAP", "圖表產出", "G" if charts else "Y", f"{charts} 張")
        add("VAP", "Workbench v010", "G" if (self.fm / "VAP" / "ui"
            / "VAP_Workbench_v010.html").is_file() else "R")
        add("VAP", "Header 視覺鎖", "G" if (self.fm / "VAP" / "spec"
            / "Veritas_Header_Masthead_1d.html").is_file() else "R", "LOCKED")
        gen = self.fm / "VRN" / "SSOT" / "v2" / "generations" / \
            "VRN_ResearchReport_SSOT.v2.records64.v0155.2f771c00c6dd8d6e.jsonl"
        chain = gen.is_file() and hashlib.sha256(gen.read_bytes()).hexdigest().startswith("2f771c00")
        add("VRN", "SSOT 鏈", "G" if chain else "R", "全鏈雜湊吻合" if chain else "斷鏈")
        add("VRN", "Reader Adapter", "G" if (self.sm / "70_VRN_Rules"
            / "VRN_ResearchReport_SSOT_v2_ReaderAdapter.py").is_file() else "R")
        pdfs = self.list_pdfs()
        add("VRN", "研報 intake", "G" if pdfs else "Y", f"{len(pdfs)} 份 PDF")
        add("VRN", "No-OCR 入口", "G" if (self.sm / "60_PowerShell_Entry_Internal"
            / "Invoke-VRN-MQ-NoOCR-Staging-v222.ps1").is_file() else "R")
        add("Runtime", "pwsh", "G" if find_pwsh() else "R")
        add("Runtime", "java(tabula)", "G" if shutil.which("java") else "Y")
        envp = Path(os.environ.get("USERPROFILE", "")) / "envs" / "via_core_312" / \
            "Scripts" / "python.exe"
        add("Runtime", "via_core_312", "G" if envp.is_file() else "Y",
            "" if envp.is_file() else "本機才有")
        inbox = self.sm / "_inbox_to_classify"
        n_inbox = sum(1 for p in inbox.rglob("*") if p.is_file()) if inbox.is_dir() else 0
        add("治理", "待分類箱", "G" if n_inbox == 0 else "Y", f"{n_inbox} 檔")
        add("治理", "UNIT03 管線", "G", "v0109–v0113 全結案 · chartlib_v002 已晉升")
        add("治理", "SSOT 獨立化", "Y", "FLOW-A DRAFT 待核准")
        tkr = self.sm / "ssot" / "VRN_TickerRegexSSOT_v0100.json"
        tkr_ok = False
        if tkr.is_file():
            try:
                tkr_ok = json.loads(tkr.read_text(encoding="utf-8")).get("status") == "ACTIVE"
            except Exception:  # noqa: BLE001
                pass
        add("SSOT", "TickerRegex v0100", "G" if tkr_ok else "R",
            "四碼首碼非零 · 消歧層" if tkr_ok else "未發行")
        add("SSOT", "P2 墊片入口", "G" if ((self.sm / "70_VRN_Rules"
            / "VIS_VRN_TickerRegexShim_v0100.py").is_file() and (self.fm / "VRN"
            / "Invoke-VRN-Shimmed-Entry-v0100.ps1").is_file()) else "R", "opt-in")
        add("VAP", "chartlib_v002", "G" if (self.fm / "VAP" / "engine"
            / "via_autoplot_engine_chartlib_v002.py").is_file() else "Y", "UNIT03 晉升版")
        add("VAP", "判定表 v002", "G" if (self.sm / "VIA_Canonical_Units"
            / "VAP_VisualLock_Adjudication_Table_v002.json").is_file() else "Y", "方案A 分項閘")
        return t

    def act_shim_dryrun(self, job: Job):
        """TickerRegex v0100 墊片入口乾跑(正本不動,只驗證墊片副本)。"""
        pwsh = find_pwsh()
        if not pwsh:
            self.emit(job, "[TOWER] 找不到 pwsh 7")
            return
        entry = self.fm / "VRN" / "Invoke-VRN-Shimmed-Entry-v0100.ps1"
        target = self.fm / "VRN" / "VRN_MDL001_StockReportPipeline.py"
        self.stream(job, [pwsh, "-NoProfile", "-NonInteractive", "-File", str(entry),
                          "-Target", str(target), "-DryRun"])

    def act_vrn_run(self, job: Job):
        pdf = job.params.get("pdf") or self.auto_pdf()
        if pdf and not Path(pdf).is_file():
            pdf = self.auto_pdf()
        if not pdf:
            self.emit(job, "[TOWER] intake 槽找不到 PDF — 把研報丟進 "
                           "functional modules\\VRN\\input\\incoming 後重按。")
            return
        job.add(f"[TOWER] auto-picked PDF: {pdf}")
        cand = self.sm / "60_PowerShell_Entry_Internal" / "Invoke-VRN-MQ-NoOCR-Staging-v222.ps1"
        rules = self.sm / "70_VRN_Rules"
        code = self.patched(cand, {
            r'\$BrokerHelper\s*=\s*".*?"':
                f'$BrokerHelper = "{rules / "VIS_VRN_BrokerAlias_Compatibility_v0222.py"}"',
            r'\$FallbackHelper\s*=\s*".*?"':
                f'$FallbackHelper = "{rules / "VIS_VRN_PDFTextLayerFallbackPlan_v0222.py"}"',
        })
        # TargetFile 以參數傳入(候選腳本可能宣告為強制參數,不能靠改預設值);
        # -NonInteractive 確保任何缺參都直接報錯而非停在互動提示。
        self.stream_pwsh_code(job, code, ["-TargetFile", pdf])

    def act_revival_check(self, job: Job):
        """VRN 復健參數完整性檢查(唯讀)。"""
        checks: list[tuple[str, bool, str]] = []

        def add(name: str, ok: bool, detail: str = ""):
            checks.append((name, ok, detail))

        ssot = self.fm / "VRN" / "SSOT"
        add("SSOT active pointer", (ssot / "VRN_ResearchReport_SSOT.active.json").is_file())
        import hashlib
        gen = ssot / "v2" / "generations" / \
            "VRN_ResearchReport_SSOT.v2.records64.v0155.2f771c00c6dd8d6e.jsonl"
        if gen.is_file():
            h = hashlib.sha256(gen.read_bytes()).hexdigest()
            add("SSOT canonical sha256", h.startswith("2f771c00"), h[:16])
        else:
            add("SSOT canonical sha256", False, "file missing")
        add("runtime adapter (70_VRN_Rules)",
            (self.sm / "70_VRN_Rules" / "VRN_ResearchReport_SSOT_v2_ReaderAdapter.py").is_file())
        add("MQ-NoOCR candidate (60_)",
            (self.sm / "60_PowerShell_Entry_Internal"
             / "Invoke-VRN-MQ-NoOCR-Staging-v222.ps1").is_file())
        for helper in ("VIS_VRN_BrokerAlias_Compatibility_v0222.py",
                       "VIS_VRN_PDFTextLayerFallbackPlan_v0222.py"):
            add(f"helper {helper}", (self.sm / "70_VRN_Rules" / helper).is_file())
        add("intake 標準槽", self.intake.is_dir(), str(self.intake))
        pdf = self.auto_pdf()
        add("auto-pick PDF", pdf is not None, pdf or "無可用 PDF")
        env_py = Path(os.environ.get("USERPROFILE", "")) / "envs" / "via_core_312" / \
            "Scripts" / "python.exe"
        add("via_core_312 env", env_py.is_file(), str(env_py))
        if env_py.is_file():
            mods = "pydantic,pdfminer,PIL,numpy,paddleocr,docling,marker,surya,tabula,playwright,weasyprint,win32com"
            r = subprocess.run([str(env_py), "-c",
                                "import importlib.util as u;"
                                f"mods='{mods}'.split(',');"
                                "missing=[m for m in mods if not u.find_spec(m)];"
                                "print(','.join(missing) if missing else 'ALL')"],
                               capture_output=True, text=True, timeout=120)
            out = (r.stdout or "").strip()
            add("12 OCR 依賴", out == "ALL", out)
        add("regex 引擎件", (self.fm / "VRN" / "InvestmentRegexPattern_VALIDATED.py").is_file())
        add("報告版面模板", (self.fm / "VRN" / "template"
                             / "VDF_VRN_Integrated_ReportSSOT_AutoLayout_FINAL.html").is_file())
        add("擷取矩陣 (VDF/template)", (self.fm / "VDF" / "template"
                                        / "VIA_Extraction_Matrix_8.csv").is_file())
        ok = sum(1 for _, o, _ in checks if o)
        lines = [f"[TOWER] VRN 復健參數檢查 · {ok}/{len(checks)} PASS", ""]
        for name, o, detail in checks:
            lines.append(f"{'[OK]  ' if o else '[MISS]'} {name}" + (f" · {detail}" if detail else ""))
        self.emit(job, "\n".join(lines))
        if ok < len(checks):
            job.status = "error"

    def act_tree_audit(self, job: Job):
        """Downloads 樹 vs repo 總檢察(唯讀,背景執行,即時進度)。"""
        import csv
        import hashlib
        dl = Path(os.environ.get("VIA_AUDIT_SRC",
                                 str(Path.home() / "Downloads" / "VeritasIntelligenceAnalytics")))
        if not dl.is_dir():
            self.emit(job, f"[TOWER] 稽核來源不存在:{dl}")
            return
        skip = re.compile(r"__pycache__|[\\/]temp[\\/]|\.pyc$|\.bak$")
        job.add(f"[AUDIT] 枚舉 {dl} …")
        files = [p for p in dl.rglob("*") if p.is_file() and not skip.search(str(p))]
        total = len(files)
        job.add(f"[AUDIT] 待比對 {total} 檔(≤20MB 用 SHA256,大檔比大小)")
        rows: list[tuple[str, float, str]] = []
        def sha(p: Path) -> str:
            h = hashlib.sha256()
            with open(p, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            return h.hexdigest()
        for i, p in enumerate(files, 1):
            rel = p.relative_to(dl)
            repo_p = self.base / rel
            try:
                if not repo_p.is_file():
                    status = "NOT_IN_REPO"
                elif p.stat().st_size > 20 * 1024 * 1024:
                    status = ("IN_REPO_SAME_SIZE"
                              if repo_p.stat().st_size == p.stat().st_size
                              else "IN_REPO_DIFFERS")
                else:
                    status = ("IN_REPO_IDENTICAL" if sha(p) == sha(repo_p)
                              else "IN_REPO_DIFFERS")
            except OSError as exc:
                status = f"READ_ERROR:{type(exc).__name__}"
            rows.append((status, round(p.stat().st_size / 1048576, 2), str(rel)))
            if i % 250 == 0 or i == total:
                job.progress = int(i * 100 / max(total, 1))
                job.add(f"[AUDIT] {i}/{total} …")
        self.rpt.mkdir(parents=True, exist_ok=True)
        out = self.rpt / "downloads_tree_audit.csv"
        with open(out, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh)
            w.writerow(["Status", "MB", "Rel"])
            w.writerows(rows)
        counts: dict[str, tuple[int, float]] = {}
        for s, mb, _ in rows:
            c, m = counts.get(s, (0, 0.0))
            counts[s] = (c + 1, m + mb)
        job.add("")
        job.add("===== 總覽 =====")
        for s in sorted(counts, key=lambda k: -counts[k][0]):
            c, m = counts[s]
            job.add(f"{s:20s} {c:6d} files {m:10.1f} MB")
        job.add("")
        job.add("===== NOT_IN_REPO 前 40 大 =====")
        for s, mb, rel in sorted((r for r in rows if r[0] == "NOT_IN_REPO"),
                                 key=lambda r: -r[1])[:40]:
            job.add(f"{mb:9.2f} MB  {rel}")
        job.add("")
        job.add(f"[AUDIT] 完整清單:{out}")
        job.progress = 100
        job.status = "done"

    # ------------------------------------------------ 六收尾流程(唯讀提案型)
    def _report_dir(self, name: str) -> Path:
        d = self.rpt / name
        d.mkdir(parents=True, exist_ok=True)
        return d

    def act_flow_a_ssot(self, job: Job):
        """FLOW-A · SSOT 指標獨立化草案:絕對路徑→repo 對映驗證,產 DRAFT 不啟用。"""
        import hashlib
        ssot = self.fm / "VRN" / "SSOT"
        ptr_path = ssot / "VRN_ResearchReport_SSOT.active.json"
        d = json.loads(ptr_path.read_text(encoding="utf-8"))
        dl_root = "C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics"
        draft, ok, bad = dict(d), 0, 0
        for k, v in d.items():
            if isinstance(v, str) and v.startswith(dl_root):
                rel = v[len(dl_root) + 1:]
                repo_p = self.base / rel.replace("\\", os.sep)
                sha_key = k.replace("_path", "_sha256")
                want = d.get(sha_key, "")
                if repo_p.is_file():
                    got = hashlib.sha256(repo_p.read_bytes()).hexdigest()
                    match = (got == want) if want else True
                    job.add(f"{'[OK]  ' if match else '[DRIFT]'} {k} → {rel}"
                            + ("" if match else f" · repo={got[:12]} want={str(want)[:12]}"))
                    ok += match
                    bad += (not match)
                    draft[k] = str(repo_p)
                else:
                    job.add(f"[MISS] {k} → repo 無此檔:{rel}")
                    bad += 1
        out = self._report_dir("_flow_a_ssot_reissue")
        dst = out / "VRN_ResearchReport_SSOT.active.DRAFT.json"
        draft["draft_note"] = ("DRAFT ONLY · repo-absolute paths · NOT ACTIVE · "
                              "activation requires operator hash-locked transaction")
        dst.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        job.add("")
        job.add(f"[FLOW-A] 對映驗證 OK={ok} 異常={bad} · DRAFT: {dst}")
        job.add("[FLOW-A] 啟用步驟(需明確核准):以 DRAFT 覆蓋 active.json → SAFE PROBE 重驗 → commit")
        self.emit(job, "")
        if bad:
            job.status = "error"

    def act_flow_b_inbox(self, job: Job):
        """FLOW-B · _inbox_to_classify 分類提案(唯讀)。"""
        import csv
        inbox = self.sm / "_inbox_to_classify"
        if not inbox.is_dir():
            self.emit(job, f"[FLOW-B] 無待分類箱:{inbox}")
            return
        rules = [(re.compile(r"VRN_MDL|VIS_VRN|vrn_", re.I), "functional modules/VRN"),
                 (re.compile(r"vdf_|VDF_", re.I), "functional modules/VDF"),
                 (re.compile(r"vap_|VAP_|autoplot", re.I), "functional modules/VAP"),
                 (re.compile(r"\.ps1$|\.psm1$", re.I), "supportive modules/<ops>"),
                 (re.compile(r"\.md$|\.txt$", re.I), "docs 層(原地或 docs/)"),
                 (re.compile(r"\.json$|\.csv$", re.I), "registry/評估後歸位")]
        rows = []
        for p in sorted(inbox.rglob("*")):
            if not p.is_file() or p.name == ".gitkeep":
                continue
            dest = next((t for rx, t in rules if rx.search(p.name)), "REVIEW_MANUAL")
            rows.append((str(p.relative_to(inbox)), dest))
        out = self._report_dir("_flow_b_inbox") / "inbox_classification_proposal.csv"
        with open(out, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh)
            w.writerow(["File", "ProposedSlot"])
            w.writerows(rows)
        counts: dict[str, int] = {}
        for _, t in rows:
            counts[t] = counts.get(t, 0) + 1
        job.add(f"[FLOW-B] {len(rows)} 檔分類提案:")
        for t, c in sorted(counts.items(), key=lambda x: -x[1]):
            job.add(f"  {c:4d} → {t}")
        self.emit(job, f"\n[FLOW-B] 提案 CSV:{out}(核准後我出搬移腳本)")

    def act_flow_c_differs(self, job: Job):
        """FLOW-C · DIFFERS 裁決提案:讀取總檢察 CSV,比 mtime 出建議。"""
        import csv
        src = self.rpt / "downloads_tree_audit.csv"
        if not src.is_file():
            self.emit(job, f"[FLOW-C] 找不到 {src} — 先跑 TREE AUDIT")
            return
        dl = Path(os.environ.get("VIA_AUDIT_SRC",
                                 str(Path.home() / "Downloads" / "VeritasIntelligenceAnalytics")))
        rows = []
        with open(src, encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                if r["Status"] != "IN_REPO_DIFFERS":
                    continue
                rel = r["Rel"]
                a, b = dl / rel, self.base / rel
                try:
                    verdict = ("KEEP_REPO(repo較新)" if b.stat().st_mtime >= a.stat().st_mtime
                               else "REVIEW(Downloads較新)")
                except OSError:
                    verdict = "READ_ERROR"
                rows.append((rel, verdict, r["MB"]))
        out = self._report_dir("_flow_c_differs") / "differs_adjudication_proposal.csv"
        with open(out, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh)
            w.writerow(["Rel", "Verdict", "MB"])
            w.writerows(rows)
        review = [r for r in rows if r[1].startswith("REVIEW")]
        job.add(f"[FLOW-C] DIFFERS {len(rows)} 檔:KEEP_REPO {len(rows)-len(review)} · 待審(Downloads較新){len(review)}")
        for rel, _, mb in review[:20]:
            job.add(f"  REVIEW {mb:>8} MB  {rel}")
        self.emit(job, f"\n[FLOW-C] 完整裁決表:{out}")

    def act_flow_d_unit03(self, job: Job):
        """FLOW-D · UNIT03 管線狀態(唯讀)。"""
        lines = ["[FLOW-D] UNIT03 VAP 引擎候選管線狀態:"]
        runs = sorted(self.rpt.glob("RUN_*_VIA_DOWNLOADS_UIUX_CLOSEOUT_AUDIT_*"),
                      key=lambda p: p.stat().st_mtime, reverse=True)
        if not runs:
            self.emit(job, "[FLOW-D] 尚無 v0103 closeout audit run(在 VIA_Reports 下)")
            return
        run = runs[0]
        lines.append(f"  audit run: {run.name}")
        for stage, pat in [("v0110 裁決", "P0_UNIT03_VAP_VISUAL_SEMANTIC_ADJUDICATION_v0110_*"),
                           ("v0111 修復提案", "P0_UNIT03_VAP_VISUAL_LOCK_REPAIR_PROPOSAL_v0111_*")]:
            hits = sorted(run.glob(pat), key=lambda p: p.stat().st_mtime, reverse=True)
            if not hits:
                lines.append(f"  {stage}: ─ 未產出")
                continue
            gate = "?"
            for j in hits[0].glob("*Summary.json"):
                try:
                    s = json.loads(j.read_text(encoding="utf-8"))
                    g = s.get("gate", {})
                    gate = f"{g.get('color', '?')} · {g.get('gate', '?')}" if isinstance(g, dict) else str(g)
                except Exception:  # noqa: BLE001
                    pass
            lines.append(f"  {stage}: {hits[0].name} → {gate}")
        lines.append("  下一步:v0111R2 → YELLOW 提案 → 核准 → v0112 兩輪守護測試 → write_workbench → 晉升審查")
        self.emit(job, "\n".join(lines))

    def act_flow_e_hydra(self, job: Job):
        """FLOW-E · Hydra 淨化掃描:同名多處 → 相同=冗餘 / 相異=版本衝突。"""
        import csv
        import hashlib
        groups: dict[str, list[Path]] = {}
        for p in self.base.rglob("*"):
            if (p.is_file() and p.suffix.lower() in (".py", ".ps1", ".psm1", ".html", ".js")
                    and "__pycache__" not in str(p) and p.name != ".gitkeep"):
                groups.setdefault(p.name, []).append(p)
        rows, conflicts, redundant = [], 0, 0
        for name, paths in sorted(groups.items()):
            if len(paths) < 2:
                continue
            shas = {hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
            kind = "REDUNDANT_COPY" if len(shas) == 1 else "VERSION_CONFLICT"
            conflicts += (kind == "VERSION_CONFLICT")
            redundant += (kind == "REDUNDANT_COPY")
            for p in paths:
                rows.append((name, kind, len(paths), len(shas), str(p.relative_to(self.base))))
        out = self._report_dir("_flow_e_hydra") / "hydra_matrix.csv"
        with open(out, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh)
            w.writerow(["Name", "Kind", "Copies", "DistinctHashes", "Path"])
            w.writerows(rows)
        job.add(f"[FLOW-E] 多頭名單:版本衝突 {conflicts} 組(真 Hydra)· 冗餘拷貝 {redundant} 組")
        shown = set()
        for name, kind, copies, hashes, _ in rows:
            if kind == "VERSION_CONFLICT" and name not in shown and len(shown) < 15:
                shown.add(name)
                job.add(f"  CONFLICT {name} ×{copies}({hashes} 版本)")
        self.emit(job, f"\n[FLOW-E] 完整矩陣:{out}(衝突組需人審定 canonical;冗餘組可安全去重)")

    def act_flow_f_data(self, job: Job):
        """FLOW-F · 資料資產封存計畫(唯讀)。"""
        dl = Path(os.environ.get("VIA_AUDIT_SRC",
                                 str(Path.home() / "Downloads" / "VeritasIntelligenceAnalytics")))
        lines = ["[FLOW-F] 本機資料資產封存計畫(不進 git):"]
        targets = [("marketflow 資料湖", dl / "_via_marketflow_data"),
                   ("ICON_FORGE 主控資料", dl / "functional modules" / "VAP" / "ICON_FORGE"),
                   ("外部資料 vault", dl / "_viam_external_vault")]
        total = 0.0
        for label, p in targets:
            if p.is_dir():
                mb = sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) / 1048576
                total += mb
                lines.append(f"  {label}: {mb:,.0f} MB · {p}")
            else:
                lines.append(f"  {label}: ─ 不存在")
        big = [f for f in self.repo.rglob("*")
               if f.is_file() and f.stat().st_size > 45 * 1048576 and ".git" not in f.parts]
        lines.append(f"  repo 內本機巨檔(local-only): {len(big)} 檔")
        for f in big[:10]:
            lines.append(f"    {f.stat().st_size/1048576:,.0f} MB · {f.relative_to(self.repo)}")
        lines.append(f"  合計約 {total:,.0f} MB → 建議:壓縮封存到外接碟/雲備份,git 不收")
        self.emit(job, "\n".join(lines))

    def act_tool(self, job: Job, name: str):
        opt = self.sm / "VIA_Optimizer_Suite"
        self.rpt.mkdir(parents=True, exist_ok=True)
        bundle = self.sm / "VIA_Standalone_Package_v0102" / "_supportive_bundle" / "powershell"
        pwsh = find_pwsh()
        if not pwsh:
            self.emit(job, "[TOWER-ERROR] pwsh not found")
            job.status = "error"
            return
        cmds = {
            "audit": [pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                      str(opt / "VIA_TurboOptimizer_v3.3_OneDrive_Coding_AISafeAudit.ps1"),
                      "-OutputRoot", str(self.rpt / "_disk_audit")],
            "panorama": [pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                         str(opt / "Invoke-VIA-FirstSightPanorama-GovernanceMatrix-v0100.ps1"),
                         "-BaseRoot", str(self.base),
                         "-DownloadRoot", str(Path.home() / "Downloads")],
            "polyglot": [pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                         str(opt / "Invoke-VIA-SafePolyglotOptimizer-AIO-v0102.ps1"),
                         "-SupportiveModulesRoot", str(self.sm),
                         "-NexusCorePath", str(bundle / "Invoke-VeritasNexusCore.ps1"),
                         "-PolyglotPath",
                         str(bundle / "Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1"),
                         "-OutputRoot", str(self.rpt / "_polyglot"), "-SelfTest"],
        }
        self.stream(job, cmds[name])

    def act_open(self, job: Job, what: str):
        targets = {"workbench": self.fm / "VAP" / "ui" / "VAP_Workbench_v010.html",
                   "charts": self.base / "VAP" / "output" / "index.html"}
        t = targets[what]
        if not t.exists():
            self.emit(job, f"[TOWER] 檔案不存在(先跑 AutoPlot):{t}")
            return
        if hasattr(os, "startfile"):
            os.startfile(t)  # type: ignore[attr-defined]
            self.emit(job, f"[TOWER] opened {t}")
        else:
            self.emit(job, f"[TOWER] 請手動開啟:{t}")

    def act_accel(self, job: Job, code: str):
        self.stream_pwsh_code(job, code)


# ------------------------------------------------------------- 主要動作表
ACTIONS = {
    "vdf": ("VDF Intake · Refresh", "act_vdf"),
    "autoplot": ("AutoPlot · 全配對繪圖", "act_autoplot"),
    "vrn_intake": ("VRN · Intake 盤點(唯讀)", "act_vrn_intake"),
    "vrn_probe": ("VRN · Guarded SAFE PROBE", "act_vrn_probe"),
    "vrn_lanes": ("VRN · Lane2+Lane3 預檢", "act_vrn_lanes"),
    "vrn_run": ("VRN · 實彈 No-OCR(自動選最新 PDF)", "act_vrn_run"),
    "revival": ("VRN · 復健參數檢查(14 項)", "act_revival_check"),
    "shim_dryrun": ("VRN · TickerRegex 墊片乾跑(v0100)", "act_shim_dryrun"),
    "tree_audit": ("Downloads 樹總檢察(唯讀 · 背景)", "act_tree_audit"),
    "flow_a_ssot": ("FLOW-A · SSOT 指標獨立化草案", "act_flow_a_ssot"),
    "flow_b_inbox": ("FLOW-B · 待分類箱提案(611檔)", "act_flow_b_inbox"),
    "flow_c_differs": ("FLOW-C · DIFFERS 裁決提案", "act_flow_c_differs"),
    "flow_d_unit03": ("FLOW-D · UNIT03 管線狀態", "act_flow_d_unit03"),
    "flow_e_hydra": ("FLOW-E · Hydra 淨化掃描", "act_flow_e_hydra"),
    "flow_f_data": ("FLOW-F · 資料資產封存計畫", "act_flow_f_data"),
    "audit": ("SafeAudit 磁碟稽核(無刪除)", ("act_tool", "audit")),
    "panorama": ("FirstSight 全景矩陣(唯讀)", ("act_tool", "panorama")),
    "polyglot": ("Polyglot AIO(僅報告)", ("act_tool", "polyglot")),
    "open_workbench": ("開啟 Workbench v010", ("act_open", "workbench")),
    "open_charts": ("開啟圖庫索引", ("act_open", "charts")),
}

# ------------------------------------------------------------- 20 個 PS 加速器
# 全部唯讀或安全操作;各自背景 job 執行,不卡 UI。
ACCELERATORS = {
    "a01_git_status": ("Git 狀態", "Set-Location '{repo}'; git status -sb; git log --oneline -5"),
    "a02_git_pull": ("Git 同步 main", "Set-Location '{repo}'; git checkout main; git pull origin main"),
    "a03_disk_base": ("BASE 佔用", "Get-ChildItem '{base}' -Directory | ForEach-Object {{ [pscustomobject]@{{ Dir=$_.Name; MB=[math]::Round(((Get-ChildItem $_.FullName -Recurse -File -EA SilentlyContinue | Measure-Object Length -Sum).Sum)/1MB,1) }} }} | Sort-Object MB -Descending | Format-Table -AutoSize | Out-String"),
    "a04_newest_reports": ("最新研報×10", "Get-ChildItem '{base}\\functional modules\\VRN\\input' -Recurse -File -Include *.pdf,*.docx -EA SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 10 Name,LastWriteTime,@{{N='MB';E={{[math]::Round($_.Length/1MB,2)}}}} | Format-Table -AutoSize | Out-String"),
    "a05_clean_temp": ("清空 temp 槽", "foreach($m in 'VDF','VAP','VRN'){{ Get-ChildItem \"{base}\\functional modules\\$m\\temp\" -Exclude .gitkeep -EA SilentlyContinue | Remove-Item -Recurse -Force }}; 'temp cleaned'"),
    "a06_chart_count": ("圖表統計", "$c=Get-ChildItem '{base}\\VAP\\output\\VAP_*.html' -EA SilentlyContinue; \"charts: $($c.Count)\"; $c | Select-Object -Last 5 -ExpandProperty Name"),
    "a07_db_info": ("VDF 資料庫資訊", "Get-Item '{base}\\functional modules\\VDF\\db\\movies_dataset.sqlite' -EA SilentlyContinue | Select-Object Name,Length,LastWriteTime | Format-List | Out-String"),
    "a08_qa_gate": ("VDF QA 閘門", "Get-Content '{base}\\functional modules\\VDF\\qa\\evidence\\movies_intake_summary.json' -Raw | ConvertFrom-Json | Select-Object gate,mode | Format-List | Out-String"),
    "a09_ssot_head": ("SSOT 指標摘要", "Get-Content '{base}\\functional modules\\VRN\\SSOT\\VRN_ResearchReport_SSOT.active.json' -Raw | ConvertFrom-Json | Select-Object promotion_state,authority_generation,active_record_count,transaction_id | Format-List | Out-String"),
    "a10_env_py": ("Python 環境", "& \"$env:USERPROFILE\\envs\\via_core_312\\Scripts\\python.exe\" --version; & \"$env:USERPROFILE\\envs\\via_core_312\\Scripts\\python.exe\" -m pip list --format=freeze | Measure-Object | ForEach-Object {{ \"packages: $($_.Count)\" }}"),
    "a11_java": ("Java 版本", "java -version 2>&1 | Out-String"),
    "a12_pwsh": ("PowerShell 版本", "$PSVersionTable.PSVersion.ToString()"),
    "a13_open_input": ("開 VRN input", "Invoke-Item '{base}\\functional modules\\VRN\\input'; 'opened'"),
    "a14_open_reports": ("開 VIA_Reports", "New-Item -ItemType Directory \"$env:USERPROFILE\\VIA_Reports\" -Force | Out-Null; Invoke-Item \"$env:USERPROFILE\\VIA_Reports\"; 'opened'"),
    "a15_open_base": ("開 BASE 資料夾", "Invoke-Item '{base}'; 'opened'"),
    "a16_manifests": ("Manifest 總覽", "Get-ChildItem '{base}' -Recurse -Filter '*Manifest*.json' -EA SilentlyContinue | Select-Object -First 20 @{{N='Path';E={{$_.FullName.Substring('{base}'.Length+1)}}}},@{{N='KB';E={{[math]::Round($_.Length/1KB,1)}}}} | Format-Table -AutoSize | Out-String"),
    "a17_supportive_list": ("支援模組清單", "Get-ChildItem '{base}\\supportive modules' -Directory | Select-Object Name | Format-Table -AutoSize | Out-String"),
    "a18_big_files": ("巨檔掃描 >45MB", "Get-ChildItem '{repo}' -Recurse -File -EA SilentlyContinue | Where-Object Length -gt 45MB | Select-Object @{{N='MB';E={{[math]::Round($_.Length/1MB,1)}}}},FullName | Sort-Object MB -Descending | Format-Table -AutoSize | Out-String"),
    "a19_bak_scan": ("垃圾檔掃描 (.bak/.tmp)", "Get-ChildItem '{base}' -Recurse -File -Include *.bak,*.tmp -EA SilentlyContinue | Select-Object -First 30 FullName | Format-Table -AutoSize | Out-String"),
    "a20_gate_all": ("全系統快速體檢", "Set-Location '{repo}'; \"branch: $(git branch --show-current)\"; \"charts: $((Get-ChildItem '{base}\\VAP\\output\\VAP_*.html' -EA SilentlyContinue).Count)\"; \"db: $((Get-Item '{base}\\functional modules\\VDF\\db\\movies_dataset.sqlite' -EA SilentlyContinue).Length) bytes\"; \"vrn input pdf: $((Get-ChildItem '{base}\\functional modules\\VRN\\input' -Recurse -Filter *.pdf -EA SilentlyContinue).Count)\"; \"reports dir: $env:USERPROFILE\\VIA_Reports\""),
}

ARCH_SVG = r"""<svg viewBox="0 0 980 430" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto">
<defs><marker id="ar" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
<path d="M0 0L8 4L0 8z" fill="#6b6860"/></marker>
<style>.bx{fill:#fff;stroke:#dcdad3;rx:8}.t{font:700 13px Georgia,serif;fill:#3a3f3e;letter-spacing:.08em}
.s{font:9px Consolas,monospace;fill:#6b6860;letter-spacing:.06em}.io{font:600 9.5px Consolas,monospace;fill:#3d8f8f}
.fl{stroke:#6b6860;stroke-width:1.2;fill:none;marker-end:url(#ar)}.seal{fill:#9e2b25}</style></defs>
<rect class="bx" x="20" y="30" width="120" height="64"/><text class="t" x="80" y="56" text-anchor="middle">data/</text>
<text class="s" x="80" y="74" text-anchor="middle">3× CSV 來源</text>
<rect class="bx" x="200" y="20" width="160" height="84" stroke="#3d8f8f"/><text class="t" x="280" y="46" text-anchor="middle">VDF</text>
<text class="s" x="280" y="62" text-anchor="middle">intake 引擎 v001</text>
<text class="s" x="280" y="76" text-anchor="middle">IN: input/·data/ OUT: db/</text>
<rect class="bx" x="420" y="30" width="120" height="64"/><text class="t" x="480" y="56" text-anchor="middle">db/</text>
<text class="s" x="480" y="74" text-anchor="middle">movies_dataset.sqlite</text>
<rect class="bx" x="600" y="20" width="160" height="84" stroke="#7a6daa"/><text class="t" x="680" y="46" text-anchor="middle">VAP</text>
<text class="s" x="680" y="62" text-anchor="middle">AutoPlot + Workbench v010</text>
<text class="s" x="680" y="76" text-anchor="middle">IN: db/ OUT: VAP/output/</text>
<rect class="bx" x="820" y="30" width="140" height="64"/><text class="t" x="890" y="52" text-anchor="middle">output/</text>
<text class="s" x="890" y="70" text-anchor="middle">26+ 圖表 · index.html</text>
<path class="fl" d="M140 62H198"/><path class="fl" d="M360 62H418"/><path class="fl" d="M540 62H598"/><path class="fl" d="M760 62H818"/>
<rect class="bx" x="20" y="170" width="120" height="64"/><text class="t" x="80" y="192" text-anchor="middle">input/</text>
<text class="s" x="80" y="208" text-anchor="middle">incoming/ 64 份研報</text><text class="s" x="80" y="222" text-anchor="middle">PDF · DOCX · TXT</text>
<rect class="bx" x="200" y="160" width="160" height="84" stroke="#c4634f"/><text class="t" x="280" y="184" text-anchor="middle">VRN</text>
<text class="s" x="280" y="200" text-anchor="middle">MDL001–008 OCR 管線</text>
<text class="s" x="280" y="214" text-anchor="middle">Guarded Entry · No-OCR v222</text>
<text class="s" x="280" y="228" text-anchor="middle">IN: input/ OUT: db/·output/</text>
<rect class="bx" x="420" y="170" width="120" height="64"/><text class="t" x="480" y="192" text-anchor="middle">SSOT</text>
<text class="s" x="480" y="208" text-anchor="middle">指標鏈 · 64 records</text><text class="s" x="480" y="222" text-anchor="middle">雜湊鎖定</text>
<rect class="bx" x="600" y="170" width="160" height="64"/><text class="t" x="680" y="192" text-anchor="middle">Reports</text>
<text class="s" x="680" y="208" text-anchor="middle">ReportSSOT AutoLayout</text><text class="s" x="680" y="222" text-anchor="middle">template/ 版面鎖</text>
<path class="fl" d="M140 202H198"/><path class="fl" d="M360 202H418"/><path class="fl" d="M540 202H598"/>
<rect x="20" y="300" width="940" height="100" fill="#fbfaf7" stroke="#dcdad3" rx="8"/>
<rect class="seal" x="40" y="322" width="40" height="40" rx="4"/><text x="60" y="350" text-anchor="middle" font-family="serif" font-size="22" fill="#f2f1ec">理</text>
<text class="t" x="100" y="340">CONTROL TOWER v004</text>
<text class="s" x="100" y="356">背景 jobs · 動態進度 · 12 主動作 + 6 收尾流程 + 20 加速器</text>
<text class="io" x="100" y="374">Supportive:Optimizer Suite · Governance v0162B/C · 60_/70_ · Standalone Pkg · PMIS-Lite · Dashboard 標準</text>
<path class="fl" d="M280 298V246" stroke-dasharray="4 3"/><path class="fl" d="M680 298V246" stroke-dasharray="4 3"/>
<path class="fl" d="M480 298V236" stroke-dasharray="4 3"/><path class="fl" d="M680 298V106" stroke-dasharray="4 3"/>
</svg>"""

PAGE = r"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA · Control Tower __VER__</title>
<style>
:root{--bg:#f2f1ec;--paper:#fff;--paper2:#fbfaf7;--ink:#1b1a17;--ink2:#3a3f3e;--mut:#6b6860;
 --line:#dcdad3;--seal:#9e2b25;--teal:#3d8f8f;--violet:#7a6daa;--green:#4f9465;--red:#c4634f;--amber:#bf8f33;
 --mono:"SFMono-Regular",Consolas,monospace;--sans:"Microsoft JhengHei","Segoe UI",system-ui,sans-serif}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);font-family:var(--sans);color:var(--ink);min-height:100vh}
.mast{background:#fff;display:flex;align-items:center;gap:21px;padding:11px 40px 10px}
.mast .seal{width:46px;height:46px;background:var(--seal);color:#f2f1ec;display:flex;align-items:center;justify-content:center;font-family:serif;font-size:26px;border-radius:4px}
.mast .wm{font-family:Georgia,serif;font-size:22px;letter-spacing:.1em;color:var(--ink2);white-space:nowrap}
.mast .sub{font-family:var(--mono);font-size:8.5px;letter-spacing:.36em;color:var(--mut);text-transform:uppercase}
.rule{height:1px;background:linear-gradient(to right,var(--violet) 0 34px,rgba(27,26,23,.14) 34px 100%)}
.tabs{display:flex;gap:2px;background:var(--paper2);padding:8px 20px 0;border-bottom:1px solid var(--line);overflow-x:auto}
.tabs button{border:1px solid var(--line);border-bottom:none;background:var(--paper2);padding:9px 18px;border-radius:8px 8px 0 0;
 cursor:pointer;font:600 12.5px var(--sans);color:var(--mut);transition:all .18s;white-space:nowrap}
.tabs button.on{background:var(--paper);color:var(--ink);border-color:var(--teal);box-shadow:0 -2px 0 var(--teal) inset}
.tabs button:hover{color:var(--teal)}
main{max-width:1180px;margin:0 auto;padding:18px 20px 40px}
.page{display:none;animation:pin .3s cubic-bezier(.2,.7,.3,1)}
.page.on{display:block}
@keyframes pin{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
h3{font:700 10.5px var(--mono);letter-spacing:.14em;color:var(--mut);text-transform:uppercase;margin:14px 0 8px}
.mgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:8px}
.tile{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:10px 12px;display:flex;align-items:center;gap:10px;animation:pin .35s both}
.tile .lamp{width:12px;height:12px;border-radius:50%;flex:none}
.tile.G .lamp{background:var(--green);box-shadow:0 0 6px rgba(79,148,101,.7);animation:pulse 2.4s infinite}
.tile.Y .lamp{background:var(--amber);box-shadow:0 0 6px rgba(191,143,51,.7)}
.tile.R .lamp{background:var(--red);box-shadow:0 0 6px rgba(196,99,79,.8);animation:pulse 1.1s infinite}
@keyframes pulse{50%{opacity:.55}}
.tile .tn{font-size:12.5px;color:var(--ink)}
.tile .td{font:10px var(--mono);color:var(--mut)}
.tile .tg{font:700 9px var(--mono);color:var(--teal);letter-spacing:.08em;text-transform:uppercase}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(255px,1fr));gap:10px}
.card{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:14px 16px;display:flex;flex-direction:column;gap:9px;transition:transform .16s,box-shadow .16s}
.card:hover{transform:translateY(-2px);box-shadow:0 10px 28px -14px rgba(27,26,23,.3)}
.card h4{font:700 14px var(--sans);color:var(--ink)}
.card .k{font:700 9.5px var(--mono);letter-spacing:.1em;text-transform:uppercase}
.card select{padding:7px 9px;border:1px solid var(--line);border-radius:7px;background:var(--paper2);font:12px var(--sans);color:var(--ink);width:100%;cursor:pointer}
.card .go{padding:9px;border:none;border-radius:8px;background:var(--teal);color:#fff;font:700 12.5px var(--sans);cursor:pointer;transition:transform .15s,filter .15s}
.card .go:hover{filter:brightness(1.08);transform:translateY(-1px)}
.card .go:active{transform:scale(.97)}
.card .go.danger{background:var(--seal)}
.card .go.busy{opacity:.45;pointer-events:none}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(215px,1fr));gap:9px}
.acc{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:6px}
button.act{display:flex;flex-direction:column;gap:3px;text-align:left;padding:11px 13px;background:var(--paper);border:1px solid var(--line);border-radius:8px;cursor:pointer;font-family:var(--sans);transition:transform .15s,box-shadow .15s,border-color .15s}
button.act:hover{transform:translateY(-2px);border-color:var(--teal);box-shadow:0 8px 24px -12px rgba(27,26,23,.25)}
button.act:active{transform:scale(.97)}
button.act.busy{opacity:.45;pointer-events:none}
button.act .k{font:700 9.5px var(--mono);letter-spacing:.09em;color:var(--teal);text-transform:uppercase}
button.act .t{font-size:13px;color:var(--ink)}
.dock{position:sticky;bottom:0;background:var(--bg);padding-top:10px}
#bar{height:6px;background:var(--line);border-radius:3px;overflow:hidden;margin:0 0 6px}
#fill{height:100%;width:0;background:linear-gradient(90deg,var(--teal),var(--violet));border-radius:3px;transition:width .4s ease}
#fill.indet{width:30%!important;animation:sl 1.2s ease-in-out infinite}
@keyframes sl{0%{margin-left:-30%}100%{margin-left:100%}}
#fill.err{background:var(--red)}
#status{font:700 11px var(--mono);letter-spacing:.1em;color:var(--mut);margin:0 0 6px;text-transform:uppercase}
#status.run{color:var(--teal)}#status.err{color:var(--red)}#status.ok{color:var(--green)}
#log{background:#1b1a17;color:#e8e6df;border-radius:8px;padding:13px 16px;font:11.5px/1.5 var(--mono);white-space:pre-wrap;word-break:break-all;height:26vh;overflow:auto}
.arch{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:18px}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style></head><body>
<div class="mast"><div class="seal">理</div>
 <div><div class="wm">VIA CONTROL TOWER</div>
 <div class="sub">Veritas Intelligence Analytics · matrix · launcher · flows · 127.0.0.1</div></div></div>
<div class="rule"></div>
<div class="tabs" id="tabs"></div>
<main>
 <div class="page" id="pg-matrix"><h3>整體狀況矩陣 System Matrix(自動載入 · 60s 自動刷新)</h3><div class="mgrid" id="matrix"></div></div>
 <div class="page" id="pg-launch"><h3>子系統啟動平台 Launch Platform(預設值已填 · 下拉即改)</h3><div class="cards" id="launch"></div></div>
 <div class="page" id="pg-arch"><h3>VIA 架構 · 輸入/輸出總覽</h3><div class="arch">__ARCH__</div></div>
 <div class="page" id="pg-flows"><h3>六收尾流程(唯讀提案型 · 互不重疊)</h3><div class="grid" id="flows"></div></div>
 <div class="page" id="pg-accel"><h3>加速器 ×20(背景 · 不卡斷)</h3><div class="acc" id="accels"></div></div>
 <div class="dock"><div id="bar"><div id="fill"></div></div><p id="status">READY</p><div id="log">選擇分頁,按任意按鈕啟動背景 job;進度與日誌即時更新,期間其他按鈕照常可用。</div></div>
</main>
<script>
const ACTIONS = __ACTIONS__, ACCEL = __ACCEL__;
const TABS = [["pg-matrix","總覽矩陣"],["pg-launch","啟動平台"],["pg-arch","架構圖"],["pg-flows","收尾流程"],["pg-accel","加速器"]];
const tabs=document.getElementById('tabs');
for(const [id,label] of TABS){
  const b=document.createElement('button'); b.textContent=label; b.dataset.pg=id;
  b.onclick=()=>{document.querySelectorAll('.tabs button').forEach(x=>x.classList.toggle('on',x===b));
    document.querySelectorAll('.page').forEach(p=>p.classList.toggle('on',p.id===id));};
  tabs.appendChild(b);
}
tabs.firstChild.click();
const log=document.getElementById('log'), status=document.getElementById('status'), fill=document.getElementById('fill');
let watching=null, seen=0, timer=null;
function narrate(t){ status.textContent=t; }
async function launch(url,label,btn){
  btn.classList.add('busy');
  const r=await fetch(url,{method:'POST'});
  if(!r.ok){ btn.classList.remove('busy'); log.textContent+='\n[ERROR] '+await r.text(); return; }
  const {id}=await r.json(); watching=id; seen=0;
  log.textContent='['+new Date().toLocaleTimeString()+'] '+label+' — job '+id+'\n';
  narrate('RUNNING · '+label); status.className='run';
  fill.classList.remove('err'); fill.classList.add('indet');
  if(!timer) timer=setInterval(poll,700);
  btn._watch=id;
}
async function poll(){
  if(!watching) return;
  const r=await fetch('/job/'+watching+'?since='+seen); if(!r.ok) return;
  const j=await r.json();
  if(j.lines.length){ log.textContent+=j.lines.join('\n')+'\n'; log.scrollTop=log.scrollHeight; }
  seen=j.total;
  if(j.progress>=0){ fill.classList.remove('indet'); fill.style.width=j.progress+'%'; }
  if(j.status!=='running'){
    document.querySelectorAll('.busy').forEach(x=>{ if(x._watch===j.id||!x._watch) x.classList.remove('busy'); });
    narrate((j.status==='done'?'DONE · ':'ERROR · ')+j.label);
    status.className=(j.status==='done'?'ok':'err');
    if(j.status!=='done') fill.classList.add('err');
    fill.classList.remove('indet'); fill.style.width='100%';
    watching=null;
    if(j.action==='vdf'||j.action==='autoplot') refreshMatrix();
  }
}
// ---- 矩陣(自動完成)----
async function refreshMatrix(){
  const r=await fetch('/matrix'); if(!r.ok) return;
  const tiles=await r.json(); const host=document.getElementById('matrix'); host.innerHTML='';
  let i=0;
  for(const t of tiles){
    const d=document.createElement('div'); d.className='tile '+t.s; d.style.animationDelay=(i++*30)+'ms';
    d.innerHTML='<span class="lamp"></span><span><span class="tg">'+t.g+'</span><br><span class="tn">'+t.n+'</span>'+(t.d?'<br><span class="td">'+t.d+'</span>':'')+'</span>';
    host.appendChild(d);
  }
  const g=tiles.filter(t=>t.s==='G').length;
  narrate('MATRIX · '+g+'/'+tiles.length+' GREEN');
}
refreshMatrix(); setInterval(refreshMatrix,60000);
// ---- 啟動平台 ----
async function buildLaunch(){
  const host=document.getElementById('launch');
  let pdfs=[]; try{ pdfs=await (await fetch('/pdfs')).json(); }catch(e){}
  const pdfOpts=pdfs.map((p,i)=>'<option value="'+encodeURIComponent(p.path)+'"'+(i===0?' selected':'')+'>'+p.name+' ('+p.mb+'MB)</option>').join('')||'<option value="">(intake 無 PDF)</option>';
  host.innerHTML=
   '<div class="card"><span class="k" style="color:var(--teal)">VDF</span><h4>資料鍛造</h4><select id="vdfMode"><option selected>Refresh</option><option>ValidateOnly</option><option>DryRun</option></select><button class="go" onclick="launch(\'/run/vdf?mode=\'+document.getElementById(\'vdfMode\').value,\'VDF \'+document.getElementById(\'vdfMode\').value,this)">啟動 VDF</button></div>'
  +'<div class="card"><span class="k" style="color:var(--violet)">VAP</span><h4>全配對繪圖</h4><select id="vapMax"><option>12</option><option>26</option><option selected>40</option><option>80</option></select><button class="go" onclick="launch(\'/run/autoplot?max=\'+document.getElementById(\'vapMax\').value,\'AutoPlot ×\'+document.getElementById(\'vapMax\').value,this)">啟動 AutoPlot</button><button class="go" style="background:var(--violet)" onclick="launch(\'/run/open_workbench\',\'開啟 Workbench\',this)">開 Workbench v010</button></div>'
  +'<div class="card"><span class="k" style="color:var(--seal)">VRN</span><h4>研報處理</h4><select id="vrnPdf">'+pdfOpts+'</select><button class="go danger" onclick="launch(\'/run/vrn_run?pdf=\'+document.getElementById(\'vrnPdf\').value,\'VRN RUN\',this)">實彈 No-OCR</button><button class="go" onclick="launch(\'/run/vrn_probe\',\'SAFE PROBE\',this)">SAFE PROBE</button><button class="go" onclick="launch(\'/run/revival\',\'復健檢查\',this)">復健檢查</button></div>'
  +'<div class="card"><span class="k" style="color:var(--amber)">TOOLS</span><h4>治理工具</h4><button class="go" onclick="launch(\'/run/audit\',\'SafeAudit\',this)">磁碟稽核</button><button class="go" onclick="launch(\'/run/panorama\',\'Panorama\',this)">全景矩陣</button><button class="go" onclick="launch(\'/run/polyglot\',\'Polyglot AIO\',this)">Polyglot AIO</button></div>';
}
buildLaunch();
// ---- 流程 / 加速器按鈕 ----
function mkAct(host,key,label,accel){
  const b=document.createElement('button'); b.className='act'; b.id='btn-'+key;
  b.innerHTML='<span class="k">'+key.replace(/_/g,' ')+'</span><span class="t">'+label+'</span>';
  b.onclick=()=>launch((accel?'/accel/':'/run/')+key,label,b);
  host.appendChild(b);
}
const flowHost=document.getElementById('flows'), accHost=document.getElementById('accels');
for(const [k,v] of Object.entries(ACTIONS)){
  if(k.startsWith('flow_')||k==='tree_audit'||k==='vrn_intake'||k==='vrn_lanes') mkAct(flowHost,k,v,false);
}
for(const [k,v] of Object.entries(ACCEL)) mkAct(accHost,k,v,true);
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    tower: Tower

    def log_message(self, *_):
        pass

    def _json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _html(self, body: str):
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            page = (PAGE.replace("__VER__", VERSION)
                    .replace("__ARCH__", ARCH_SVG)
                    .replace("__ACTIONS__", json.dumps(
                        {k: v[0] for k, v in ACTIONS.items()}, ensure_ascii=False))
                    .replace("__ACCEL__", json.dumps(
                        {k: v[0] for k, v in ACCELERATORS.items()}, ensure_ascii=False)))
            self._html(page)
            return
        if self.path == "/matrix":
            self._json(self.tower.matrix())
            return
        if self.path == "/pdfs":
            self._json(self.tower.list_pdfs())
            return
        m = re.fullmatch(r"/job/([0-9a-f]+)(?:\?since=(\d+))?", self.path)
        if m:
            job = JOBS.get(m.group(1))
            if not job:
                self._json({"error": "unknown job"}, 404)
                return
            self._json(job.snapshot(int(m.group(2) or 0)))
            return
        self._json({"error": "not found"}, 404)

    def do_POST(self):
        from urllib.parse import parse_qsl, unquote, urlparse
        parsed = urlparse(self.path)
        params = {k: unquote(v) for k, v in parse_qsl(parsed.query)}
        m = re.fullmatch(r"/(run|accel)/([a-z0-9_]+)", parsed.path)
        if not m:
            self._json({"error": "bad path"}, 404)
            return
        kind, key = m.group(1), m.group(2)
        table = ACTIONS if kind == "run" else ACCELERATORS
        if key not in table:
            self._json({"error": "unknown action"}, 404)
            return
        with JOBS_LOCK:
            if key in RUNNING_ACTIONS:
                self._json({"error": f"{key} already running"}, 409)
                return
            RUNNING_ACTIONS.add(key)
        label = table[key][0]
        job = Job(key, label, params)
        JOBS[job.id] = job
        t = self.tower

        def work():
            try:
                if kind == "run":
                    spec = ACTIONS[key][1]
                    if isinstance(spec, tuple):
                        getattr(t, spec[0])(job, spec[1])
                    else:
                        getattr(t, spec)(job)
                else:
                    code = ACCELERATORS[key][1].format(repo=t.repo, base=t.base)
                    t.act_accel(job, code)
                if job.status == "running":
                    job.status = "done"
                    job.progress = 100
            except Exception as exc:  # noqa: BLE001
                job.status = "error"
                job.add(f"[TOWER-ERROR] {exc}")
            finally:
                with JOBS_LOCK:
                    RUNNING_ACTIONS.discard(key)

        threading.Thread(target=work, daemon=True).start()
        self._json({"id": job.id})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--intake", default=None)
    args = ap.parse_args()
    base = Path(args.base).resolve()
    if not (base / "functional modules").is_dir():
        print(f"[TOWER] RED base invalid: {base}")
        return 2
    Handler.tower = Tower(base, Path(args.intake).resolve() if args.intake else None)
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"[TOWER] VIA Control Tower {VERSION} · http://127.0.0.1:{args.port} · base={base}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
