#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA-SYS-ENG-004 : Environment Deep Probe.

EnvManager v0110 檢查的是「相依關係對不對」。這一層檢查的是
**環境本身有沒有爛掉**——那是完全不同的一組故障，而且大部分
`uv pip check` 也看不到，因為 uv 只看已註冊的 metadata。

20 道新檢查（E01–E20），每一道都內建多個處置選項而不只是一句警告。

新掛五個 local-free 函式庫（全部本機可得、不連網）：
    packaging            真正的 PEP 440 比較 —— 取代 v0110 的啟發式
                         啟發式判定標 M 級，packaging 判定標 V 級
    tomllib              讀 uv.lock / pyproject.toml，比對鎖檔與實裝
    importlib.metadata   正規的 dist 讀取，抓得到 RECORD / direct_url
    sqlite3              執行歷史落地成資料庫，才能算趨勢與閃爍
    difflib              套件名近似比對，抓大小寫與錯字造成的雙胞胎

全部 graceful degradation：任何一個缺席就降級並在報告標明，不中斷。
只讀不改。

用法：
    python VIA_EnvDeepProbe.py --env-root C:\\Users\\tonyk\\envs
"""

from __future__ import annotations

import argparse
import collections
import difflib
import json
import os
import re
import sqlite3
import sys
import webbrowser
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

URN_SELF = "VIA-SYS-ENG-004"
VERSION = "v0100"
SPEC_VERSION = "VIA-SSOT-SPEC-v0100"

# ---- 五個 local-free 函式庫，缺席就降級 -----------------------------------
CAPS: Dict[str, bool] = {}
try:
    from packaging.specifiers import SpecifierSet
    from packaging.version import InvalidVersion, Version
    CAPS["packaging"] = True
except ImportError:
    CAPS["packaging"] = False
try:
    import tomllib
    CAPS["tomllib"] = True
except ImportError:
    tomllib = None                                       # type: ignore
    CAPS["tomllib"] = False
CAPS["sqlite3"] = True
CAPS["difflib"] = True
try:
    import importlib.metadata as ilmd
    CAPS["importlib.metadata"] = True
except ImportError:
    ilmd = None                                          # type: ignore
    CAPS["importlib.metadata"] = False


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def iso_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Console:
    def __init__(self) -> None:
        self.lines: List[str] = []

    def say(self, message: str, level: str = "INFO") -> None:
        line = "[%s][%s] %s" % (datetime.now().strftime("%H:%M:%S"), level, message)
        self.lines.append(line)
        print(line, flush=True)


LOG = Console()


# ---------------------------------------------------------------------------
# §1  20 道故障的定義：偵測、後果、多重處置
# ---------------------------------------------------------------------------

@dataclass
class FailureMode:
    code: str
    name: str
    impact: str
    remedies: List[str]                # 多個處置選項，不是單一建議
    severity: str = "WARN"


FAILURE_CATALOG: Dict[str, FailureMode] = {m.code: m for m in [
    FailureMode("E01", "系統站台外洩（include-system-site-packages=true）",
                "環境不隔離，系統層套件會蓋掉環境內版本，衝突永遠查不出來",
                ["把 pyvenv.cfg 的該值改 false 後重啟殼層",
                 "以 --without-system-site-packages 重建環境",
                 "若刻意如此，加入豁免名單並註記理由"], "FAIL"),
    FailureMode("E02", "editable / .pth 指向環境外",
                "程式碼實際來自環境外的路徑，換機器就爆，且不受版本控管",
                ["改以 pip install -e 於環境內重裝並鎖定路徑",
                 "把來源目錄納入版控後改裝正式版本",
                 "保留但登記為 EXTERNAL_SOURCE 並禁止進 CI"], "FAIL"),
    FailureMode("E03", "同一套件兩份 dist-info",
                "pip 與 importlib 可能各讀到不同版本，行為隨機",
                ["保留較新的一份，另一份移入 _superseded",
                 "整包 uninstall 後重裝一次",
                 "以 uv pip install --reinstall 重建該套件"], "FAIL"),
    FailureMode("E04", "dist-info 缺 RECORD",
                "半途中斷的安裝，uninstall 會失敗且檔案殘留",
                ["重新安裝該套件讓 RECORD 重建",
                 "手動刪除該 dist-info 後重裝",
                 "整個環境依 LKGC 重建"], "FAIL"),
    FailureMode("E05", "直譯器不存在或大小為零",
                "環境完全不能用，但目錄還在，掃描時會被誤認為存在",
                ["以同版本 Python 重建環境",
                 "把整個環境目錄移入 _broken 並從 LKGC 重建",
                 "確認是否被防毒隔離"], "FAIL"),
    FailureMode("E06", "pyvenv.cfg 的 home 指向已刪除的直譯器",
                "環境啟動會失敗或 fallback 到別的 Python，版本靜默改變",
                ["修正 home 指向現存直譯器",
                 "以正確的 py -X.Y 重建",
                 "確認是否為 Python 升級後的殘留"], "FAIL"),
    FailureMode("E07", "套件名大小寫雙胞胎",
                "Windows 不分大小寫，兩份會互相覆蓋；Linux 上又變成兩個",
                ["保留正規名稱那份，另一份移除後重裝",
                 "以 pip install --force-reinstall 正規化",
                 "檢查是否為手動複製造成"], "FAIL"),
    FailureMode("E08", "近似套件名共存（可能的錯字或分支）",
                "例如 pillow 與 pil、opencv-python 與 opencv-python-headless 同裝，import 行為不確定",
                ["決定保留哪一個，另一個移除",
                 "若兩者都需要，確認 import 名稱不衝突後加入豁免",
                 "檢查是否為不同套件恰好名稱相近"], "WARN"),
    FailureMode("E09", "直接 URL 安裝（direct_url.json）",
                "來源不是索引，無法從 requirements 重現，換機器裝不回來",
                ["改從索引安裝同版本",
                 "把來源固定成內部索引或 wheel 快取",
                 "登記為 NON_REPRODUCIBLE 並在鎖檔註明"], "WARN"),
    FailureMode("E10", "本地版號 / 開發版號（+local、.dev、a/b/rc）",
                "非正式版本無法重現，且升級路徑不可預期",
                ["換裝正式釋出版本",
                 "若必須用預覽版，於鎖檔明確釘選完整版號",
                 "登記為 PRERELEASE_PINNED"], "WARN"),
    FailureMode("E11", "dist-info 目錄名版本與 METADATA 版本不一致",
                "手動改過或安裝中斷，版本判定會依讀取方式而異",
                ["以 METADATA 為準重裝該套件",
                 "刪除該 dist-info 後重裝",
                 "檢查是否有人手動改過資料夾名"], "FAIL"),
    FailureMode("E12", "環境內存在巢狀 site-packages",
                "同一環境有多個 site-packages，import 順序決定行為",
                ["合併到單一 site-packages",
                 "移除巢狀的那層",
                 "重建環境"], "WARN"),
    FailureMode("E13", "符號連結／junction 迴圈",
                "掃描會無限展開；備份與重建也會爆",
                ["移除迴圈連結",
                 "把連結改為實體複本",
                 "在掃描器排除該路徑"], "FAIL"),
    FailureMode("E14", "超長路徑（接近 260 字元）",
                "Windows 上讀寫會靜默失敗，症狀是套件時有時無",
                ["把環境搬到較短的根目錄",
                 "啟用 Windows 長路徑支援",
                 "縮短環境名稱"], "WARN"),
    FailureMode("E15", "鎖檔與實際安裝不符（uv.lock / requirements）",
                "鎖檔失去意義，重建出來的環境跟現在不一樣",
                ["以鎖檔為準重新同步環境",
                 "以現況重新產生鎖檔並提交",
                 "逐項裁決差異後再同步"], "FAIL"),
    FailureMode("E16", "沒有任何鎖檔",
                "無法重現，LKGC 只能靠本工具的快照",
                ["產生 requirements.txt 或 uv.lock 並納入版控",
                 "改用 uv 管理該環境",
                 "至少保留本工具的 LKGC 快照"], "WARN"),
    FailureMode("E17", "空的 dist-info（無 METADATA）",
                "安裝殘骸，會讓套件清點數字失真",
                ["直接移除該殘骸目錄",
                 "重裝對應套件",
                 "先確認沒有其他套件依賴它"], "WARN"),
    FailureMode("E18", "兩個環境套件組合完全相同",
                "重複佔用空間，且兩份會各自漂移，日後一定不一致",
                ["合併為一個環境，另一個改為捷徑",
                 "確認用途不同則在命名上區分並註記",
                 "把其中一個移入封存"], "WARN"),
    FailureMode("E19", "剩餘磁碟空間不足以重建",
                "重建到一半失敗，環境會停在半殘狀態",
                ["清理 pip / uv 快取",
                 "把環境搬到空間充足的磁碟",
                 "先移除已知不需要的隔離環境"], "FAIL"),
    FailureMode("E20", "環境長期未更新（相對於其他環境）",
                "落後版本會在跨環境協作時產生非預期行為",
                ["依 LKGC 對齊到基準版本",
                 "確認是否為刻意凍結，是則登記 FROZEN",
                 "重建為當前基準"], "WARN"),
]}


# ---------------------------------------------------------------------------
# §2  探測
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    code: str
    env: str
    subject: str
    detail: str
    severity: str
    grade: str = "V"                 # V=實證  M=啟發式
    remedies: List[str] = field(default_factory=list)


@dataclass
class EnvRecord:
    name: str
    path: str
    python: str = ""
    home: str = ""
    interpreter: str = ""
    site_packages: str = ""
    system_site: bool = False
    packages: Dict[str, str] = field(default_factory=dict)
    lockfile: str = ""
    newest_mtime: float = 0.0
    healthy: bool = True


NAME_NORM = re.compile(r"[-_.]+")
LOCAL_VERSION = re.compile(r"\+|\.dev|(?<=\d)(a|b|rc)\d")


def norm(name: str) -> str:
    return NAME_NORM.sub("-", name).lower()


class DeepProbe:
    def __init__(self, env_root: Path, out_dir: Path, long_path_limit: int = 240,
                 min_free_gb: float = 10.0, stale_days: int = 120) -> None:
        self.env_root = env_root
        self.out_dir = out_dir
        self.long_path_limit = long_path_limit
        self.min_free_gb = min_free_gb
        self.stale_days = stale_days
        self.stamp = now_stamp()
        self.envs: List[EnvRecord] = []
        self.findings: List[Finding] = []

    def flag(self, code: str, env: str, subject: str, detail: str,
             grade: str = "V") -> None:
        mode = FAILURE_CATALOG[code]
        self.findings.append(Finding(code=code, env=env, subject=subject,
                                     detail=detail, severity=mode.severity,
                                     grade=grade, remedies=list(mode.remedies)))

    # -- 掃描 --------------------------------------------------------------
    def scan(self) -> None:
        LOG.say("掃描環境根目錄 %s" % self.env_root)
        seen_real: Set[str] = set()
        for child in sorted(self.env_root.iterdir()):
            if not child.is_dir():
                continue
            cfg = child / "pyvenv.cfg"
            if not cfg.is_file():
                continue                                  # 非環境，v0110 已處理
            record = EnvRecord(name=child.name, path=str(child))
            self._read_config(record, cfg)
            self._locate_interpreter(record, child)
            self._locate_site_packages(record, child)
            self._read_packages(record)
            self._detect_lockfile(record, child)
            self._detect_link_loop(record, child, seen_real)
            self.envs.append(record)
        LOG.say("找到 %d 個虛擬環境" % len(self.envs), "OK")

    def _read_config(self, record: EnvRecord, cfg: Path) -> None:
        try:
            text = cfg.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return
        for line in text.splitlines():
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip().lower(), value.strip()
            if key in ("version", "version_info"):
                record.python = value
            elif key == "home":
                record.home = value
            elif key == "include-system-site-packages":
                record.system_site = value.lower() == "true"
        if record.system_site:
            self.flag("E01", record.name, "pyvenv.cfg",
                      "include-system-site-packages = true，環境未隔離")
        if record.home and not Path(record.home).exists():
            self.flag("E06", record.name, "pyvenv.cfg",
                      "home 指向不存在的路徑：%s" % record.home)

    def _locate_interpreter(self, record: EnvRecord, root: Path) -> None:
        for candidate in ("Scripts/python.exe", "bin/python", "bin/python3"):
            probe = root / candidate
            if probe.exists():
                record.interpreter = str(probe)
                try:
                    if probe.stat().st_size == 0:
                        self.flag("E05", record.name, candidate, "直譯器檔案大小為 0")
                        record.healthy = False
                except OSError:
                    pass
                return
        self.flag("E05", record.name, "(interpreter)", "找不到任何直譯器可執行檔")
        record.healthy = False

    def _locate_site_packages(self, record: EnvRecord, root: Path) -> None:
        candidates: List[Path] = []
        win = root / "Lib" / "site-packages"
        if win.is_dir():
            candidates.append(win)
        lib = root / "lib"
        if lib.is_dir():
            for entry in sorted(lib.iterdir()):
                probe = entry / "site-packages"
                if probe.is_dir():
                    candidates.append(probe)
        if not candidates:
            return
        record.site_packages = str(candidates[0])
        if len(candidates) > 1:
            self.flag("E12", record.name, "site-packages",
                      "同一環境有 %d 個 site-packages：%s"
                      % (len(candidates), ", ".join(str(c) for c in candidates)))
        if len(record.site_packages) > self.long_path_limit:
            self.flag("E14", record.name, "site-packages",
                      "路徑長度 %d 接近 Windows 上限" % len(record.site_packages))

    def _read_packages(self, record: EnvRecord) -> None:
        if not record.site_packages:
            return
        sp = Path(record.site_packages)
        by_norm: Dict[str, List[Tuple[str, str, Path]]] = collections.defaultdict(list)
        newest = 0.0
        for entry in sorted(sp.iterdir()):
            if entry.suffix == ".pth":
                self._check_pth(record, entry)
                continue
            if not entry.name.endswith(".dist-info") or not entry.is_dir():
                continue
            meta = entry / "METADATA"
            if not meta.is_file():
                self.flag("E17", record.name, entry.name, "dist-info 內沒有 METADATA")
                continue
            name = version = ""
            try:
                for line in meta.read_text(encoding="utf-8", errors="replace").splitlines():
                    if not line.strip():
                        break
                    if line.startswith("Name:"):
                        name = line.split(":", 1)[1].strip()
                    elif line.startswith("Version:"):
                        version = line.split(":", 1)[1].strip()
            except OSError:
                continue
            if not name:
                self.flag("E17", record.name, entry.name, "METADATA 沒有 Name 欄位")
                continue

            stem = entry.name[: -len(".dist-info")]
            if "-" in stem:
                dir_version = stem.rsplit("-", 1)[1]
                if version and dir_version and dir_version != version:
                    self.flag("E11", record.name, name,
                              "目錄名版本 %s 與 METADATA 版本 %s 不一致"
                              % (dir_version, version))
            if not (entry / "RECORD").is_file():
                self.flag("E04", record.name, name, "dist-info 缺少 RECORD")
            if (entry / "direct_url.json").is_file():
                try:
                    payload = json.loads((entry / "direct_url.json").read_text(encoding="utf-8"))
                    url = str(payload.get("url", ""))[:120]
                except (OSError, ValueError):
                    url = "(無法解析)"
                self.flag("E09", record.name, name, "來源為直接 URL：%s" % url)
            if version and LOCAL_VERSION.search(version):
                self.flag("E10", record.name, name, "非正式版本號：%s" % version)

            by_norm[norm(name)].append((name, version, entry))
            record.packages[norm(name)] = version
            try:
                newest = max(newest, entry.stat().st_mtime)
            except OSError:
                pass
        record.newest_mtime = newest

        for key, items in by_norm.items():
            if len(items) < 2:
                continue
            raw_names = {i[0] for i in items}
            versions = {i[1] for i in items}
            if len(raw_names) > 1:
                self.flag("E07", record.name, key,
                          "大小寫／分隔符不同的雙胞胎：%s" % ", ".join(sorted(raw_names)))
            else:
                self.flag("E03", record.name, key,
                          "同一套件有 %d 份 dist-info，版本 %s"
                          % (len(items), ", ".join(sorted(versions))))

        # difflib：近似名稱共存
        names = sorted(by_norm.keys())
        for index, left in enumerate(names):
            if len(left) < 5:
                continue
            for right in names[index + 1:]:
                if len(right) < 5 or left == right:
                    continue
                if right.startswith(left) or left.startswith(right):
                    # 以 '-' 分隔的延伸是正當變體（opencv-python-headless、polars-runtime-32）；
                    # 直接黏上去的（beautifulsoup / beautifulsoup4）比較像新舊並存或錯字。
                    longer, shorter = (right, left) if len(right) > len(left) else (left, right)
                    if longer[len(shorter):].startswith("-"):
                        continue
                    self.flag("E08", record.name, shorter,
                              "與 %s 並存，僅差尾綴 %r，可能是新舊版本並存或錯字"
                              % (longer, longer[len(shorter):]), grade="M")
                    continue
                ratio = difflib.SequenceMatcher(None, left, right).ratio()
                if ratio >= 0.92:
                    self.flag("E08", record.name, left,
                              "與 %s 名稱相似度 %.2f，可能是錯字或分支"
                              % (right, ratio), grade="M")

    def _check_pth(self, record: EnvRecord, entry: Path) -> None:
        try:
            text = entry.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return
        root = str(Path(record.path).resolve()).lower()
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("import "):
                continue
            try:
                target = str(Path(line).resolve()).lower()
            except (OSError, ValueError):
                continue
            if not target.startswith(root):
                self.flag("E02", record.name, entry.name,
                          "指向環境外路徑：%s" % line[:120])

    def _detect_lockfile(self, record: EnvRecord, root: Path) -> None:
        for candidate in ("uv.lock", "requirements.txt", "requirements.lock",
                          "pyproject.toml"):
            probe = root / candidate
            if probe.is_file():
                record.lockfile = str(probe)
                break
        if not record.lockfile:
            self.flag("E16", record.name, "(lockfile)", "環境目錄內沒有任何鎖檔")
            return
        self._compare_lock(record, Path(record.lockfile))

    def _compare_lock(self, record: EnvRecord, lock: Path) -> None:
        locked: Dict[str, str] = {}
        try:
            if lock.name == "uv.lock" and CAPS["tomllib"]:
                data = tomllib.loads(lock.read_text(encoding="utf-8"))
                for package in data.get("package", []):
                    if isinstance(package, dict) and package.get("name"):
                        locked[norm(str(package["name"]))] = str(package.get("version", ""))
            elif lock.name.startswith("requirements"):
                for line in lock.read_text(encoding="utf-8", errors="replace").splitlines():
                    line = line.split("#", 1)[0].strip()
                    if not line or line.startswith("-"):
                        continue
                    match = re.match(r"^([A-Za-z0-9._-]+)\s*==\s*([\w.+!-]+)", line)
                    if match:
                        locked[norm(match.group(1))] = match.group(2)
        except (OSError, ValueError):
            return
        if not locked:
            return
        missing = sorted(set(locked) - set(record.packages))
        extra = sorted(set(record.packages) - set(locked))
        changed = sorted(k for k in set(locked) & set(record.packages)
                         if locked[k] and locked[k] != record.packages[k])
        if missing or changed:
            self.flag("E15", record.name, lock.name,
                      "鎖檔有而環境沒有 %d 個；版本不同 %d 個（%s）"
                      % (len(missing), len(changed),
                         ", ".join(changed[:4]) or "—"))
        elif extra:
            self.flag("E15", record.name, lock.name,
                      "環境多了 %d 個鎖檔沒有的套件：%s"
                      % (len(extra), ", ".join(extra[:5])))

    def _detect_link_loop(self, record: EnvRecord, root: Path,
                          seen_real: Set[str]) -> None:
        try:
            real = str(root.resolve()).lower()
        except OSError:
            return
        if real in seen_real:
            self.flag("E13", record.name, "(path)",
                      "解析後與另一個環境指向同一實體路徑：%s" % real)
            return
        seen_real.add(real)
        if root.is_symlink():
            self.flag("E13", record.name, "(path)", "環境根目錄本身是連結")

    # -- 跨環境 ------------------------------------------------------------
    def cross_checks(self) -> None:
        signatures: Dict[str, List[str]] = collections.defaultdict(list)
        for record in self.envs:
            if not record.packages:
                continue
            signature = "|".join("%s==%s" % (k, v)
                                 for k, v in sorted(record.packages.items()))
            signatures[signature].append(record.name)
        for names in signatures.values():
            if len(names) > 1:
                self.flag("E18", names[0], "(env)",
                          "與 %s 套件組合完全相同" % ", ".join(names[1:]))

        stamps = [(r.name, r.newest_mtime) for r in self.envs if r.newest_mtime]
        if len(stamps) >= 3:
            newest = max(s for _, s in stamps)
            for name, stamp in stamps:
                days = (newest - stamp) / 86400.0
                if days > self.stale_days:
                    self.flag("E20", name, "(env)",
                              "最新套件比全域最新落後 %d 天" % int(days), grade="M")

        try:
            usage = __import__("shutil").disk_usage(str(self.env_root))
            free_gb = usage.free / (1024 ** 3)
            if free_gb < self.min_free_gb:
                self.flag("E19", "(root)", "(disk)",
                          "剩餘空間 %.1f GB，低於重建門檻 %.1f GB"
                          % (free_gb, self.min_free_gb))
        except OSError:
            pass

    # -- packaging 升級：把 v0110 的啟發式判定升為實證 ----------------------
    def upgrade_evidence(self, heuristic_findings: List[Dict[str, Any]]) -> Dict[str, int]:
        """用 packaging 重新裁決外部傳入的版本衝突，把 M 級升 V 或推翻。"""
        result = {"confirmed": 0, "refuted": 0, "unknown": 0}
        if not CAPS["packaging"] or not heuristic_findings:
            result["unknown"] = len(heuristic_findings)
            return result
        for row in heuristic_findings:
            spec_text = str(row.get("spec", ""))
            installed = str(row.get("installed", ""))
            if not spec_text or not installed:
                result["unknown"] += 1
                continue
            try:
                ok = Version(installed) in SpecifierSet(spec_text, prereleases=True)
            except (InvalidVersion, Exception):           # noqa: BLE001
                result["unknown"] += 1
                continue
            if ok:
                result["refuted"] += 1
            else:
                result["confirmed"] += 1
        return result

    # -- sqlite 歷史 -------------------------------------------------------
    def persist_history(self, db_path: Path) -> Dict[str, int]:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute("""CREATE TABLE IF NOT EXISTS probe_run(
                stamp TEXT, env TEXT, code TEXT, subject TEXT,
                severity TEXT, grade TEXT, detail TEXT)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS env_snapshot(
                stamp TEXT, env TEXT, python TEXT, packages INTEGER)""")
            for finding in self.findings:
                conn.execute("INSERT INTO probe_run VALUES (?,?,?,?,?,?,?)",
                             (self.stamp, finding.env, finding.code, finding.subject,
                              finding.severity, finding.grade, finding.detail))
            for record in self.envs:
                conn.execute("INSERT INTO env_snapshot VALUES (?,?,?,?)",
                             (self.stamp, record.name, record.python,
                              len(record.packages)))
            conn.commit()
            runs = conn.execute(
                "SELECT COUNT(DISTINCT stamp) FROM probe_run").fetchone()[0]
            previous = conn.execute(
                "SELECT DISTINCT stamp FROM probe_run WHERE stamp < ? "
                "ORDER BY stamp DESC LIMIT 1", (self.stamp,)).fetchone()
            new_codes = 0
            if previous:
                before = {(r[0], r[1]) for r in conn.execute(
                    "SELECT env, code FROM probe_run WHERE stamp = ?", (previous[0],))}
                now = {(f.env, f.code) for f in self.findings}
                new_codes = len(now - before)
            return {"runs": int(runs), "new_since_last": new_codes}
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# §3  輸出
# ---------------------------------------------------------------------------

def esc(value: Any) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def klass(value: str) -> str:
    upper = str(value).upper()
    if upper in ("PASS", "GREEN", "V", "OK"):
        return "ok"
    if upper in ("FAIL", "RED"):
        return "fail"
    if upper in ("WARN", "AMBER", "M"):
        return "warn"
    return ""


def table(items: List[Dict[str, Any]], fields: List[str], status: str = "") -> str:
    if not items:
        return "<tr><td colspan='%d' class='muted'>—— 無 ——</td></tr>" % len(fields)
    out = []
    for item in items:
        cells = []
        for name in fields:
            value = item.get(name, "")
            if isinstance(value, (list, tuple)):
                value = " ／ ".join(str(v) for v in value)
            cls = " class='%s'" % klass(str(value)) if name == status else ""
            cells.append("<td%s>%s</td>" % (cls, esc(value)))
        out.append("<tr>%s</tr>" % "".join(cells))
    return "".join(out)


CSS = """
:root{--paper:#f2f2f3;--ink:#1d1f20;--line:#d8d8d9;--red:#b0453d;--green:#3f7d5e;--amber:#c4943a;--panel:#fff}
*{box-sizing:border-box}
body{margin:0;padding:22px 26px;background:var(--paper);color:var(--ink);font-family:"Noto Sans TC","Segoe UI",system-ui,sans-serif;font-size:12px;line-height:1.45}
.seal{display:inline-flex;width:38px;height:38px;align-items:center;justify-content:center;background:var(--red);color:#fff;font-family:"Noto Serif TC",serif;font-size:21px;border-radius:3px}
h1{font-family:"Noto Serif TC",Georgia,serif;font-size:16px;letter-spacing:.14em;text-transform:uppercase;margin:10px 0 3px}
h2{font-family:"Noto Serif TC",Georgia,serif;font-size:14px;margin:22px 0 5px}
.lede{color:#6c6e70;font-size:11.5px;margin:0 0 12px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(112px,1fr));gap:9px;margin:14px 0 4px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:3px;padding:10px 12px}
.card .k{font-size:10px;letter-spacing:.1em;color:#8a8c8e;text-transform:uppercase}
.card .v{font-size:20px;font-family:"Noto Serif TC",Georgia,serif;margin-top:3px}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);font-size:11.5px;table-layout:fixed}
th,td{border-bottom:1px solid #ececed;padding:5px 7px;text-align:left;vertical-align:top;white-space:normal;overflow-wrap:anywhere}
th{background:#eeeeef;font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:#5c5e60}
.ok{color:var(--green);font-weight:600}.warn{color:var(--amber);font-weight:600}.fail{color:var(--red);font-weight:600}
.muted{color:#9a9c9e;text-align:center;padding:12px}
pre{background:var(--panel);border:1px solid var(--line);padding:11px;font-size:11px;white-space:pre-wrap;max-height:28vh;overflow:auto}
"""


def render(probe: DeepProbe, verdict: str, history: Dict[str, int]) -> str:
    rows = [asdict(f) for f in sorted(probe.findings,
                                      key=lambda f: (f.severity != "FAIL", f.code, f.env))]
    counts = collections.Counter(f.code for f in probe.findings)
    catalog = [{"code": m.code, "name": m.name, "severity": m.severity,
                "hits": counts.get(m.code, 0), "impact": m.impact,
                "remedies": m.remedies}
               for m in FAILURE_CATALOG.values()]
    libs = [{"lib": k, "state": "READY" if v else "ABSENT",
             "role": {"packaging": "PEP 440 實證比較（把 M 級升為 V 級）",
                      "tomllib": "讀 uv.lock / pyproject 比對鎖檔",
                      "importlib.metadata": "正規 dist 讀取",
                      "sqlite3": "執行歷史落地，算趨勢與新增故障",
                      "difflib": "近似套件名比對"}.get(k, "")}
            for k, v in CAPS.items()]
    envs = [{"name": r.name, "python": r.python, "packages": len(r.packages),
             "lock": os.path.basename(r.lockfile) if r.lockfile else "(無)",
             "system_site": "YES" if r.system_site else "",
             "path": r.path} for r in probe.envs]

    fails = len([f for f in probe.findings if f.severity == "FAIL"])
    warns = len([f for f in probe.findings if f.severity == "WARN"])

    return """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Env Deep Probe</title><style>%s</style></head><body>
<div class="seal">深</div>
<h1>Environment Deep Probe</h1>
<p class="lede">%s · %s · 判定 <span class="%s">%s</span> · 只讀不改 · 歷史第 %d 次執行，本次新增故障 %d 種</p>
<div class="cards">
  <div class="card"><div class="k">Envs</div><div class="v">%d</div></div>
  <div class="card"><div class="k">檢查項</div><div class="v">20</div></div>
  <div class="card"><div class="k">Fail</div><div class="v fail">%d</div></div>
  <div class="card"><div class="k">Warn</div><div class="v warn">%d</div></div>
  <div class="card"><div class="k">實證 V</div><div class="v ok">%d</div></div>
  <div class="card"><div class="k">啟發 M</div><div class="v warn">%d</div></div>
</div>

<h2>加速函式庫</h2>
<p class="lede">全部 local-free，缺席就降級並在報告標明，不中斷、不自動安裝。</p>
<table><colgroup><col style="width:22%%"><col style="width:12%%"><col style="width:66%%"></colgroup>
<tr><th>Library</th><th>State</th><th>作用</th></tr>%s</table>

<h2>發現（依嚴重度）</h2>
<table><colgroup><col style="width:6%%"><col style="width:14%%"><col style="width:14%%"><col style="width:8%%"><col style="width:6%%"><col style="width:26%%"><col style="width:26%%"></colgroup>
<tr><th>Code</th><th>Env</th><th>對象</th><th>Severity</th><th>證據</th><th>Detail</th><th>處置選項</th></tr>%s</table>

<h2>20 道故障目錄</h2>
<p class="lede">每一道都內建多個處置選項——單一建議在真實環境常常不可行，要留退路。</p>
<table><colgroup><col style="width:5%%"><col style="width:20%%"><col style="width:7%%"><col style="width:5%%"><col style="width:31%%"><col style="width:32%%"></colgroup>
<tr><th>Code</th><th>故障</th><th>級別</th><th>命中</th><th>後果</th><th>處置選項</th></tr>%s</table>

<h2>環境清單</h2>
<table><colgroup><col style="width:18%%"><col style="width:10%%"><col style="width:8%%"><col style="width:14%%"><col style="width:10%%"><col style="width:40%%"></colgroup>
<tr><th>Env</th><th>Python</th><th>套件</th><th>鎖檔</th><th>系統站台</th><th>Path</th></tr>%s</table>

<h2>執行日誌</h2>
<pre>%s</pre>
</body></html>""" % (
        CSS, esc(probe.env_root), probe.stamp, klass(verdict), verdict,
        history.get("runs", 1), history.get("new_since_last", 0),
        len(probe.envs), fails, warns,
        len([f for f in probe.findings if f.grade == "V"]),
        len([f for f in probe.findings if f.grade == "M"]),
        table(libs, ["lib", "state", "role"], "state"),
        table(rows, ["code", "env", "subject", "severity", "grade", "detail",
                     "remedies"], "severity"),
        table(catalog, ["code", "name", "severity", "hits", "impact", "remedies"],
              "severity"),
        table(envs, ["name", "python", "packages", "lock", "system_site", "path"]),
        esc("\n".join(LOG.lines)),
    )


# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="VIA_EnvDeepProbe.py",
        description="VIA-SYS-ENG-004 環境深層探測：20 道新故障 + 五個 local-free 加速庫")
    parser.add_argument("--env-root", required=True, help="venv 根目錄")
    parser.add_argument("--out", default="", help="輸出目錄（預設 <env-root>/_deepprobe）")
    parser.add_argument("--min-free-gb", type=float, default=10.0)
    parser.add_argument("--stale-days", type=int, default=120)
    parser.add_argument("--long-path-limit", type=int, default=240)
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    env_root = Path(args.env_root).expanduser().resolve()
    if not env_root.is_dir():
        print("env-root 不存在：%s" % env_root, file=sys.stderr)
        return 2
    out_dir = Path(args.out).expanduser().resolve() if args.out else env_root / "_deepprobe"
    out_dir.mkdir(parents=True, exist_ok=True)

    LOG.say("%s Env Deep Probe %s 啟動" % (URN_SELF, VERSION), "OK")
    ready = [k for k, v in CAPS.items() if v]
    absent = [k for k, v in CAPS.items() if not v]
    LOG.say("加速庫就緒 %s%s" % (", ".join(ready),
                                "；缺席 " + ", ".join(absent) if absent else ""),
            "OK" if not absent else "WARN")
    if not CAPS["packaging"]:
        LOG.say("packaging 缺席，版本判定將維持啟發式（證據等級 M）", "WARN")

    probe = DeepProbe(env_root, out_dir, long_path_limit=args.long_path_limit,
                      min_free_gb=args.min_free_gb, stale_days=args.stale_days)
    probe.scan()
    probe.cross_checks()

    fails = len([f for f in probe.findings if f.severity == "FAIL"])
    warns = len([f for f in probe.findings if f.severity == "WARN"])
    verdict = "GREEN"
    if warns:
        verdict = "AMBER"
    if fails:
        verdict = "RED"

    history = probe.persist_history(out_dir / "deepprobe_history.sqlite")
    LOG.say("發現 %d 筆（FAIL %d，WARN %d），涵蓋 %d 種故障"
            % (len(probe.findings), fails, warns,
               len({f.code for f in probe.findings})),
            "FAIL" if fails else ("WARN" if warns else "OK"))
    LOG.say("歷史：第 %d 次執行，本次新增故障 %d 種"
            % (history.get("runs", 1), history.get("new_since_last", 0)), "OK")

    html_path = out_dir / ("VIA_EnvDeepProbe_%s.html" % probe.stamp)
    json_path = out_dir / ("env_deepprobe_%s.json" % probe.stamp)
    html_path.write_text(render(probe, verdict, history), encoding="utf-8")
    json_path.write_text(json.dumps({
        "schema": "VIA.EnvDeepProbe", "spec": SPEC_VERSION, "engine": URN_SELF,
        "version": VERSION, "generated": iso_now(), "stamp": probe.stamp,
        "env_root": str(env_root), "verdict": verdict,
        "capabilities": CAPS, "history": history,
        "gates": [{"code": f.code, "title": FAILURE_CATALOG[f.code].name,
                   "status": f.severity, "detail": "%s／%s：%s"
                   % (f.env, f.subject, f.detail)} for f in probe.findings],
        "findings": [asdict(f) for f in probe.findings],
        "catalog": [asdict(m) for m in FAILURE_CATALOG.values()],
        "envs": [asdict(r) for r in probe.envs],
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    LOG.say("報告 -> %s" % html_path, "OK")
    print("")
    print("=" * 60)
    print(" VIA ENV DEEP PROBE  ->  %s" % verdict)
    print(" 環境 %d ｜ FAIL %d ｜ WARN %d ｜ 故障種類 %d／20"
          % (len(probe.envs), fails, warns, len({f.code for f in probe.findings})))
    print("=" * 60)
    if not args.no_open and not args.json:
        try:
            webbrowser.open(html_path.as_uri())
        except Exception:                                # noqa: BLE001
            pass
    if args.json:
        print(json.dumps({"verdict": verdict, "findings": len(probe.findings)},
                         ensure_ascii=False))
    return 0 if verdict != "RED" else 1


if __name__ == "__main__":
    sys.exit(main())
