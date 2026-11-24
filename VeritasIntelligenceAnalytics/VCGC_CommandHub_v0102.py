#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC_CommandHub_v0102.py — 薄尾(v0101 以前一字不動):短指令全 Python · 模組化指令冊 · 選擇題 · 舊短令去重併入 · 舊版退役閘

操作員 2026-11-23:「PS 指令 PY 化 · PY 指令模塊化 · 類似指令整合去重不遺失 · 檢查無誤刪過去多餘引擎(VCGC 重要檢查)」
                 「短指令 PY 寫完善 · PS 只是啟動用 · 選擇題 · 說明清楚 · 強化短指令及節省 token 及 plug-in 的整合」
                 「ONE PS TO HANDLE ALL」

① 指令冊(COMMANDS):一個短指令 = 一列(名稱 · 群 · 一句話 · 詳細說明 · 例子 · 正主外掛 · 取代哪些舊短令)。
   PS 只照 `names` 動詞印出的清單生函式,每個都轉回 `x <名稱>`;新增指令只改這張冊,PS 不用動。
② 系統入口 Python 化(取代 2,500 行 PS 啟動器 Invoke-VIA-Launch):
     via-vdf / via-vrn  → 各自 SystemManager 尾版 <動詞>(預設 ui);via-vcgc → CGC_MDL149 主控台尾版 <動詞>(VIA_FROM_VCGC=YES);
     via-vqg / via-vap  → 各自尾版。via-view(母系統監控視圖)併入 via-update。
③ 省 Token 外掛:via-tok <read|slice|digest|pack|chain|delta|tools|verbs> … = 鎖冊 token 那一支(CGC_MDL158),不另寫。
④ 舊短令去重:LEGACY 表把舊名(含 Override 改成 DEPRECATED 殘樁的)導到新指令,印一行「舊名 → 新名」;沒對應的照舊殘樁。
⑤ via-prune 舊版退役閘(預設乾跑,照「刪舊版先證明」):
     a 鏈:用省 Token 工具的 chain 判法(glob 取前版 / 釘名 / exec / 本體)從尾版往下走,走得到的都算「用到」;
     b 名:全倉已追蹤檔用 git grep 找檔名引用(程式 · 冊 · 文件);有人點名就不動;
     c 證:把候選拿掉的整樹副本放 TEMP,受影響家族尾版逐支「載入(有 main 守門的才 import)+ compile」,
          五個系統入口跑 --selftest,與原樹同 rc 才算過;
     d 搬:--apply 只搬「沒人點名 + 證過」的,git mv 到 functional modules/VIA_RetiredEngines/<批>/(以搬代刪,
          RETIRE_MANIFEST.json 記 from → to + sha256;CGC_MDL276 restore 可單檔找回);不真刪。
⑥ menu:Python 選擇題主控台(分群、每項一句話說明、要參數的會逐項問並給例子);PS 的 via 只呼叫它。
用法:x <短指令> … | help [短指令] | menu | names [--ps] | sys <VDF|VRN|VCGC|VQG|VAP> [動詞…] | tok <動詞> … |
      prune [--system S] [--prove] [--apply] [--limit N] | 其餘照 v0101 | --selftest
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import ast
import collections
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0102"
FAMILY = "VCGC_CommandHub"
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(FAMILY + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
P0 = PRIOR.PRIOR                                    # v0100(boot / pano / ast 本體)


def __getattr__(name):
    return getattr(PRIOR, name)


CODE_ROOT, DATA_ROOT, IS_WIN = PRIOR.CODE_ROOT, PRIOR.DATA_ROOT, PRIOR.IS_WIN
find_tail, tool_root, _child_env, _rows_print = PRIOR.find_tail, PRIOR.tool_root, PRIOR._child_env, PRIOR._rows_print

# ------------------------------------------------------------------------------
# ① 指令冊(模組化:新增指令只加一列)
# ------------------------------------------------------------------------------
# 欄:name · group · title(一句話)· help(詳細)· examples · ask(選單要問的參數:[(提示, 例子, 轉成參數的樣板)])·
#     target(hub 動詞 + 固定參數)· plugin(正主)· replaces(被併入的舊短令)
COMMANDS: list[dict] = [
    {"name": "via", "group": "主控", "title": "選擇題主控台", "target": ["menu"], "plugin": "本中樞",
     "help": "開 PowerShell 自動進來。分群列出全部短指令,每項一句話;輸入編號就跑,要參數的會逐項問。直接 Enter = 回指令列。",
     "examples": ["via"], "replaces": ["via-status"]},
    {"name": "via-help", "group": "主控", "title": "短指令清單與說明", "target": ["help"], "plugin": "本中樞",
     "help": "不帶參數 = 全部短指令一張表;帶名稱 = 那一個的詳細說明 · 例子 · 正主 · 取代了哪些舊短令。",
     "examples": ["via-help", "via-help via-tok"], "replaces": []},
    {"name": "via-update", "group": "快照", "title": "架構快照(被動:啟動才更新)", "target": ["update"],
     "plugin": "MDL149 ssot panorama · MDL245 SDD · MDL237 audit · MDL158 pack · doctor · MDL230",
     "help": "用 VCGC 現役工具取證,出視覺鎖定 HTML:系統卡 · SSOT(regex 同義字 編號 命名 註冊 連結)· SDD · 燈號 · 整合待辦 · "
             "跟上一份比(綠變差標紅)。不在背景監控;要看最新就再跑一次。",
     "examples": ["via-update", "via-update --no-doctor", "via-update --no-open"],
     "replaces": ["via-view", "via-panorama-all", "via-lanes", "via-six-panorama"]},
    {"name": "via-doctor", "group": "快照", "title": "環境醫生:衝突 · 遺漏 · 加速器 · 工具", "target": ["doctor"],
     "plugin": "MDL240 · MDL056 ×2 · MDL273 · MDL156 · MDL186 · CGC_SystemManager connect",
     "help": "7 支 VCGC 環境工具並行(3 道、30 秒心跳),合成衝突 · 遺漏 · 多層互撞 · 安裝計畫。唯讀零安裝。",
     "examples": ["via-doctor", "via-doctor --only envmgr accel"], "replaces": ["via-env", "via-envcheck"]},
    {"name": "via-install", "group": "快照", "title": "照計畫安裝(走 VCGC 安裝閘)", "target": ["install"], "plugin": "CGC_MDL056 InstallGate",
     "help": "不帶套件 = 照上次 via-doctor 的安裝計畫;你當場輸入 YES 才開同意閘,且只開在安裝子行程。不直接 pip。",
     "examples": ["via-install", "via-install rich libcst"], "replaces": []},
    {"name": "via-vdf", "group": "系統入口", "title": "VDF 自己的入口", "target": ["sys", "VDF"], "plugin": "VDF_SystemManager 尾版",
     "help": "VDF_SystemManager 尾版 <動詞>;不給動詞 = ui(開頁)。常用:help · health · engines · test · launch --run · parquet status。",
     "examples": ["via-vdf", "via-vdf health", "via-vdf parquet status"], "ask": [("動詞(Enter = ui)", "health", "{}")],
     "replaces": ["via-vdffetch-ui"]},
    {"name": "via-vrn", "group": "系統入口", "title": "VRN 自己的入口", "target": ["sys", "VRN"], "plugin": "VRN_SystemManager 尾版",
     "help": "VRN_SystemManager 尾版 <動詞>;不給動詞 = ui。常用:verbs · health · engines · test · synchronizer · resources。",
     "examples": ["via-vrn", "via-vrn verbs", "via-vrn health --json"], "ask": [("動詞(Enter = ui)", "verbs", "{}")], "replaces": []},
    {"name": "via-vcgc", "group": "系統入口", "title": "VCGC 治理主控台", "target": ["sys", "VCGC"], "plugin": "CGC_MDL149 主控台尾版",
     "help": "CGC_MDL149 主控台 <動詞>(自動帶 VIA_FROM_VCGC=YES)。常用:token · handoff check · functions · test --quick · "
             "ssot panorama · run CGC_MDL237_NumberingSystem audit。",
     "examples": ["via-vcgc token", "via-vcgc handoff check", "via-vcgc test --quick"],
     "ask": [("動詞", "handoff check", "{}")], "replaces": ["via-cg", "via-central"]},
    {"name": "via-vqg", "group": "系統入口", "title": "VQG 入口", "target": ["sys", "VQG"], "plugin": "VQG_AllInOne 尾版",
     "help": "VQG_AllInOne 尾版 <動詞>(照它自己的用法)。", "examples": ["via-vqg --selftest"], "replaces": []},
    {"name": "via-vap", "group": "系統入口", "title": "VAP 入口", "target": ["sys", "VAP"], "plugin": "VAP_SystemManager 尾版",
     "help": "VAP_SystemManager 尾版 <動詞>(照它自己的用法)。", "examples": ["via-vap help"], "replaces": []},
    {"name": "via-run", "group": "執行", "title": "全線擷取 VDF → VRN", "target": ["run"], "plugin": "VDF launch --run · VRN_MDL260",
     "help": "先印計畫(入口 · 報告夾 · 庫 · FRED 狀態),你輸入 YES 才開同意閘,且只放進子行程;--vdf-only / --vrn-only / --plan。",
     "examples": ["via-run --plan", "via-run", "via-run --vdf-only"], "replaces": ["via-vdffetch", "via-vrnrun", "via-fetch"]},
    {"name": "via-auth", "group": "執行", "title": "授權(FRED key)", "target": ["auth"], "plugin": "本中樞",
     "help": "看狀態;--fred 遮罩輸入存 Windows 使用者層;--clear 移除。永遠不顯示 key 的任何字元(只給長度 + 指紋)。",
     "examples": ["via-auth", "via-auth --fred"], "replaces": []},
    {"name": "via-tok", "group": "省Token", "title": "省 Token 工具(讀骨架 · 切定義 · 日誌判決)", "target": ["tok"],
     "plugin": "CGC_MDL158(鎖冊 token)",
     "help": "read <檔|夾>(骨架卡)· slice <檔> <定義|JSON 路徑> · digest <日誌> · pack <夾> · chain <家族> · delta · tools · verbs。"
             "大檔 / 整夾 / 日誌一律先走這裡,不整檔讀。",
     "examples": ["via-tok read <檔>", "via-tok chain VDF_SystemManager", "via-tok digest <日誌>"],
     "ask": [("動詞", "read", "{}"), ("路徑 / 家族(可空)", "functional modules/VDF", "{}")], "replaces": ["via-panorama", "via-token"]},
    {"name": "via-bak", "group": "維護", "title": "增量備份 + Graphify / OmniRoute / agency-mem", "target": ["bak"],
     "plugin": "VIA_DailyBackup 尾版 · 各系統 graphify / omniroute",
     "help": "只備變動檔(size+mtime 快取 → SHA-256),交 VIA_DailyBackup 打包;--refresh 先叫各系統重產圖與路由;--note 寫焦點。",
     "examples": ["via-bak", "via-bak --refresh --note 收工"], "replaces": ["via-backup", "via-graphify", "via-omniroute"]},
    {"name": "via-prune", "group": "維護", "title": "舊版退役閘(先證明再搬)", "target": ["prune"], "plugin": "MDL158 chain 判法 · git grep · CGC_MDL276",
     "help": "預設乾跑:列出鏈上走不到、也沒人點名的舊版;--prove 在 TEMP 副本拿掉候選後實跑;--apply 只搬證過的到 VIA_RetiredEngines"
             "(以搬代刪,可用 CGC_MDL276 restore 找回)。--system VDF|VRN|VCGC|VQG|VAP 縮範圍。",
     "examples": ["via-prune", "via-prune --system VDF --prove", "via-prune --system VDF --prove --apply"], "replaces": ["via-dedupe"]},
    {"name": "via-pano", "group": "維護", "title": "全景 AST 檢視(乾跑)", "target": ["pano"], "plugin": "本中樞(libcst / ast)",
     "help": "掃本機程式碼,一輪安全 AST 修復建議;--apply --scope <夾> 才寫,尾版正本一律跳過。",
     "examples": ["via-pano", "via-pano --apply --scope <夾>"], "replaces": ["via-six"]},
    {"name": "via-ast", "group": "維護", "title": "AST 導入(diff 預覽 + 還原)", "target": ["ast"], "plugin": "本中樞",
     "help": "把剪貼簿 / 檔案的函式注入目標檔:先 diff 預覽,確認才寫;--rollback 還原最近一次。",
     "examples": ["via-ast --target <檔> --clipboard", "via-ast --target <檔> --rollback"], "replaces": []},
    {"name": "via-plug", "group": "維護", "title": "外掛清單", "target": ["plug"], "plugin": "本中樞",
     "help": "每支外掛 / 系統入口的尾版路徑與加速器橋(語法樹判)。", "examples": ["via-plug"], "replaces": []},
    {"name": "via-setup", "group": "設定", "title": "常態掛 PS(失敗自動還原)", "target": ["setup"], "plugin": "本中樞 → pwsh",
     "help": "備份 $PROFILE → 寫 VIA 標記區塊 → 舊 PS 短令鏈(Register-VIA-Commands / Override / Invoke-VIA-Launch)那幾行改註解停用"
             "(開 PS 不再 16 秒)→ 剖析 + 連 3 次新開 pwsh 載入 + -NoProfile;改前改後量錯誤數與載入毫秒,任一變差自動還原。"
             "--keep-old 不動舊行 · --unslim 復原舊行 · --check · --uninstall。",
     "examples": ["via-setup", "via-setup --check", "via-setup --unslim"], "replaces": ["via-profile"]},
]
CMD = {c["name"]: c for c in COMMANDS}
LEGACY = {old: c["name"] for c in COMMANDS for old in c["replaces"]}
SYS_ENTRY = {"VDF": ("VDF_SystemManager", "ui", {}), "VRN": ("VRN_SystemManager", "ui", {}),
             "VCGC": ("CGC_MDL149_VeritasCentralGovernanceConsole", "status", {"VIA_FROM_VCGC": "YES"}),
             "VQG": ("VQG_AllInOne", None, {}), "VAP": ("VAP_SystemManager", "help", {})}

P0.SHORT_COMMANDS_SPEC = [(c["name"], c["group"], c["title"], c["plugin"][:14]) for c in COMMANDS]


def dispatch(name: str, args: list[str]) -> int:
    if name in LEGACY:
        print(f"[去重] {name} 已併入 {LEGACY[name]}(說明:via-help {LEGACY[name]})", file=sys.stderr)
        name = LEGACY[name]
    c = CMD.get(name)
    if not c:
        close = [n for n in CMD if n.startswith(name) or name.replace("via-", "") in n]
        print(f"[x] 不認識 {name}" + (f";是不是:{' · '.join(close[:5])}" if close else "") + " · via-help 看清單")
        return 2
    return main(c["target"] + list(args))


# ------------------------------------------------------------------------------
# ② 系統入口 · ③ 省 Token 外掛
# ------------------------------------------------------------------------------
def cmd_sys(sysn: str, args: list[str]) -> int:
    sysn = sysn.upper()
    if sysn not in SYS_ENTRY:
        print(f"[sys] 不認識 {sysn}(VDF · VRN · VCGC · VQG · VAP)")
        return 2
    fam, default, extra = SYS_ENTRY[sysn]
    t = find_tail(fam)
    if not t:
        print(f"[sys] 找不到 {fam}_v*.py(搜尋根:{' | '.join(str(r) for r in PRIOR.search_roots())})")
        return 3
    argv = list(args) or ([default] if default else [])
    env = _child_env(extra, root=tool_root(t))
    env.pop("VIA_NO_MENU", None)
    print(f"[{sysn}] {t.name} {' '.join(argv)}", file=sys.stderr, flush=True)
    return subprocess.run([sys.executable, str(t), *argv], cwd=str(tool_root(t)), env=env).returncode


def cmd_tok(args: list[str]) -> int:
    roots = [r for r in PRIOR.search_roots() if (r / "supportive modules").is_dir()]
    E = next((PRIOR.token_tool(r) for r in roots if PRIOR.token_tool(r)), None)
    if not E:
        print("[tok] 鎖冊 token 那一支找不到(VIA_ToolVersion_Lock_v0100.json → token.path)")
        return 3
    return subprocess.run([sys.executable, str(E), *(args or ["verbs"])], cwd=str(tool_root(E)),
                          env=_child_env(root=tool_root(E))).returncode


# ------------------------------------------------------------------------------
# help · names · menu
# ------------------------------------------------------------------------------
def cmd_help(name: str | None = None) -> int:
    if name:
        n = LEGACY.get(name, name)
        c = CMD.get(n)
        if not c:
            print(f"[help] 沒有 {name};via-help 看清單")
            return 2
        print(f"\n  {c['name']} — {c['title']}({c['group']})")
        print(f"  說明:{c['help']}")
        print(f"  正主:{c['plugin']}")
        print("  例子:" + " | ".join(c["examples"]))
        if c["replaces"]:
            print("  取代的舊短令:" + " · ".join(c["replaces"]))
        return 0
    rows = [{"category": c["group"], "metric": c["name"], "lamp": "GREEN", "detail": c["title"] + " · 例 " + c["examples"][0],
             "action": c["plugin"][:40]} for c in COMMANDS]
    _rows_print(f"VIA 短指令 {len(COMMANDS)} 個(全 Python;PS 只啟動)· via-help <名稱> 看詳細", rows,
                note=f"舊短令併入 {len(LEGACY)} 個")
    return 0


def cmd_names(ps: bool = False) -> int:
    for c in COMMANDS:
        print(f"{c['name']}|{c['name']}" if ps else c["name"])
    for old, new in sorted(LEGACY.items()):
        print(f"{old}|{new}" if ps else f"{old} -> {new}")
    return 0


def _ask(prompt: str) -> str:
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        return ""


def cmd_menu() -> int:
    if not sys.stdin or not sys.stdin.isatty():
        return cmd_help()
    P0.cmd_boot()
    doc = P0._read_json(PRIOR.DOCTOR_DIR / "DOCTOR_latest.json")
    arch = P0._read_json(PRIOR.ARCH_DIR / "ARCH_latest.json")
    print(f"  前次 doctor:{doc.get('at', '沒跑')} · {doc.get('lamp', '-')}   前次架構快照:{arch.get('at', '沒跑')} · {arch.get('lamp', '-')}")
    items = [c for c in COMMANDS if c["name"] not in ("via", "via-help")]
    group = None
    for i, c in enumerate(items, 1):
        if c["group"] != group:
            group = c["group"]
            print(f"\n  ── {group} ──")
        print(f"  {i:>2}. {c['name']:<12} {c['title']}")
    print("\n  直接 Enter = 回 PowerShell 指令列(可貼上任何指令)· h <編號> = 看詳細說明")
    while True:
        s = _ask("\n  請選擇編號:").strip()
        if not s:
            return 0
        if s.lower().startswith("h"):
            k = s[1:].strip()
            if k.isdigit() and 1 <= int(k) <= len(items):
                cmd_help(items[int(k) - 1]["name"])
            continue
        if s.isdigit() and 1 <= int(s) <= len(items):
            c = items[int(s) - 1]
            print(f"\n  ▶ {c['name']}:{c['help']}")
            args: list[str] = []
            for prompt, ex, tpl in c.get("ask", []):
                v = _ask(f"    {prompt}(例 {ex}):").strip()
                if v:
                    args += v.split() if " " in v and not Path(v).exists() else [tpl.format(v)]
            extra = _ask("    其他參數(可空;例 " + " | ".join(c["examples"][1:2] or ["—"]) + "):").strip()
            args += extra.split() if extra else []
            rc = dispatch(c["name"], args)
            print(f"\n  [{c['name']}] rc {rc}")
            return rc
        print("  請輸入清單上的編號,或直接 Enter。")


# ------------------------------------------------------------------------------
# ⑤ prune(舊版退役閘)
# ------------------------------------------------------------------------------
SYS_FOLDERS = {"VCGC": "supportive modules", "VDF": "functional modules/VDF", "VRN": "functional modules/VRN",
               "VQG": "functional modules/VQG", "VAP": "functional modules/VAP"}
_FROZEN = re.compile(r"(^|/)(intake|references|VIA_RetiredEngines|SCOPE_COPY|_archive|ASSETS|backups|VIA_Reports)(/|$)")
PRUNE_DIR = PRIOR.HUB_DIR / "prune"


def _load_token_link(via: Path):
    E = PRIOR.token_tool(via)
    if not E:
        return None
    sp = importlib.util.spec_from_file_location("via_tok_for_prune", E)
    m = importlib.util.module_from_spec(sp)
    with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
        sp.loader.exec_module(m)
    return getattr(m, "_link", None)


def live_versions(stem: str, vs: dict[int, Path], link) -> set[int]:
    """從尾版往下走前版連結(glob / 釘名 / exec),走得到的都算用到;被點名的其他版也走(保守)。"""
    live: set[int] = set()
    todo = [max(vs)]
    while todo:
        cur = todo.pop()
        if cur in live or cur not in vs:
            continue
        live.add(cur)
        text = vs[cur].read_text(encoding="utf-8", errors="replace")
        lk = link(text, stem, vs[cur].name)
        pins = [int(x) for x in re.findall(re.escape(stem) + r"_v(\d{4})\.py", text) if int(x) != cur and int(x) in vs]
        todo += pins
        if lk.startswith("glob"):
            older = [v for v in vs if v < cur]
            if older:
                todo.append(max(older))
    return live


_NAME_OK = set(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")
_BIN_EXT = (b".zip", b".png", b".jpg", b".jpeg", b".pdf", b".parquet", b".duckdb", b".xlsx", b".gif", b".ico", b".whl", b".gz",
            b".db", b".sqlite", b".pkl", b".npy")


def name_refs(via: Path, names: set[str]) -> dict[str, set]:
    """回 {檔名: {點名它的已追蹤檔(相對 via)}};自己點自己不算。"""
    want = {n.encode() for n in names}
    out: dict[str, set] = collections.defaultdict(set)
    for f in subprocess.run(["git", "-C", str(via), "ls-files", "-z"], capture_output=True).stdout.split(b"\0"):
        if not f or f.lower().endswith(_BIN_EXT):
            continue
        try:
            data = (via / f.decode("utf-8", "replace")).read_bytes()
        except OSError:
            continue
        base = f.rsplit(b"/", 1)[-1]
        i = data.find(b".py")
        while i != -1:
            if i >= 6 and data[i - 6:i - 4] == b"_v" and data[i - 4:i].isdigit():
                j = i - 6
                while j > 0 and data[j - 1] in _NAME_OK:
                    j -= 1
                nm = data[j:i + 3]
                if nm in want and nm != base:
                    out[nm.decode()].add(f.decode("utf-8", "replace"))
            i = data.find(b".py", i + 3)
    return out



_SNAP_RX = re.compile(r"(^|/)docs/handoff/(history|evidence)/|(^|/)(all_py|receipt|deck)\.json$|(^|/)[0-9a-f]{64}\.json$|"
                      r"_sha256_(before|after)|(^|/)VIA_Consolidate_Batch_|(^|/)VIA_GovCoreChain_v\d{4}\.json$")


def prune_scan(via: Path, systems: list[str] | None = None) -> dict:
    link = _load_token_link(via)
    if link is None:
        return {"error": "鎖冊 token 工具找不到 → 不判(灰)"}
    files = subprocess.run(["git", "-C", str(via), "ls-files", "*.py"], capture_output=True, text=True).stdout.splitlines()
    top = subprocess.run(["git", "-C", str(via), "rev-parse", "--show-prefix"], capture_output=True, text=True).stdout.strip()
    folders = [SYS_FOLDERS[s] for s in (systems or SYS_FOLDERS)]
    fams: dict[tuple, dict[int, Path]] = collections.defaultdict(dict)
    for f in files:
        rel = f[len(top):] if top and f.startswith(top) else f
        if _FROZEN.search(rel) or not any(rel.startswith(x + "/") for x in folders):
            continue
        m = re.match(r"(.+)_v(\d{4})\.py$", Path(rel).name)
        if m:
            fams[(str(Path(rel).parent), m.group(1))][int(m.group(2))] = via / rel
    dead = []
    multi = 0
    for (d, stem), vs in fams.items():
        if len(vs) < 2:
            continue
        multi += 1
        live = live_versions(stem, vs, link)
        dead += [{"family": stem, "dir": d, "v": v, "path": str(vs[v].relative_to(via))} for v in sorted(vs) if v not in live]
    # 名:全倉已追蹤檔位元組掃描(找 ".py" 再往回取檔名;4 GB ≈ 8 秒),找出誰點名了候選
    refs = name_refs(via, {Path(x["path"]).name for x in dead}) if dead else {}
    by = collections.Counter()
    for x in dead:
        r = refs.get(Path(x["path"]).name, set())
        code = sorted(f for f in r if f.endswith((".py", ".ps1", ".psm1")) and not _FROZEN.search(f))
        reg = sorted(f for f in r if f.endswith((".json", ".jsonl")))
        lock = sorted(f for f in r if "lock" in Path(f).name.lower())
        live_reg = sorted(f for f in reg if not _SNAP_RX.search(f))
        x["kind"] = ("LOCK_REF" if lock else "UNREF" if not r else "CODE_REF" if code else "REG_REF" if live_reg
                     else "SNAP_REF" if reg else "DOC_REF")
        x["refs"] = sorted(r)[:6]
        x["n_refs"] = len(r)
        by[x["kind"]] += 1
    return {"families": len(fams), "multi": multi, "dead": dead, "by_kind": dict(by), "systems": systems or list(SYS_FOLDERS)}


def _has_main_guard(p: Path) -> bool:
    try:
        tree = ast.parse(p.read_text(encoding="utf-8-sig"))
    except (SyntaxError, ValueError):
        return False
    return any(isinstance(n, ast.If) and "__main__" in ast.unparse(n.test) for n in tree.body)


def _probe(tree_root: Path, rel: str, selftest: bool, timeout: int = 600) -> tuple[int, str]:
    p = tree_root / rel
    if selftest:
        cmd = [sys.executable, str(p), "--selftest"]
    elif _has_main_guard(p):
        cmd = [sys.executable, "-c", "import importlib.util,sys;s=importlib.util.spec_from_file_location('m',sys.argv[1]);"
               "m=importlib.util.module_from_spec(s);sys.modules['m']=m;s.loader.exec_module(m);print('IMPORT_OK')", str(p)]
    else:
        cmd = [sys.executable, "-m", "py_compile", str(p)]
    try:
        cp = subprocess.run(cmd, cwd=str(tree_root), capture_output=True, text=True, encoding="utf-8", errors="replace",
                            timeout=timeout, env=_child_env(root=tree_root))
        return cp.returncode, ((cp.stdout or "") + (cp.stderr or ""))[-300:]
    except subprocess.TimeoutExpired:
        return 124, "逾時"


def _vcgc_metrics(via: Path, timeout: int = 900) -> dict:
    """VCGC 自己的檢查(同一棵樹上跑):MDL276 lost · MDL237 audit · 註冊同步 stale · SDD 燈。"""
    V = find_tail("CGC_MDL149_VeritasCentralGovernanceConsole", [via])
    sdd = find_tail("CGC_MDL245_SDDValidator", [via])
    m: dict = {"lost_paths": []}
    if V:
        o = PRIOR._job([sys.executable, str(V), "run", "CGC_MDL276_QuarantineRecover", "lost"], via, timeout)["out"]
        x = re.search(r"登記冊引用但樹上不在\s*(\d+)", o)
        m["lost"] = int(x.group(1)) if x else None
        m["lost_paths"] = re.findall(r"NOT_FOUND\s+(\S.*?)\s+←", o)
        x = re.search(r"'stale':\s*(\d+)", o)
        m["stale"] = int(x.group(1)) if x else None
        o = PRIOR._job([sys.executable, str(V), "run", "CGC_MDL237_NumberingSystem", "audit"], via, timeout)["out"]
        x = re.search(r"遺失\s*(\d+)\s*·\s*改身分\s*(\d+)\s*·\s*重號\s*(\d+)", o)
        m["num"] = [int(x.group(i)) for i in (1, 2, 3)] if x else None
    if sdd:
        r = PRIOR._job([sys.executable, str(sdd)], via, timeout)
        x = re.search(r"\[SDD 驗證\]\s*([A-Z]+)", r["out"])
        m["sdd"] = x.group(1) if x else f"rc {r['rc']}"
        j = P0._read_json(via / "VIA_Reports" / "sdd" / "SDD_CHECK_latest.json")
        m["sdd_rules"] = {f"{row.get('rule')}": f"{row.get('lamp')}|{len(str(row.get('msg', '')))}" for row in j.get("rows", [])}
    return m


def _worse(a: dict, b: dict) -> list[str]:
    out = []
    for k in ("lost", "stale"):
        if a.get(k) is not None and (b.get(k) is None or b[k] > a[k]):
            out.append(f"{k} {a.get(k)} → {b.get(k)}")
    if a.get("num") and (not b.get("num") or any(y > x for x, y in zip(a["num"], b["num"]))):
        out.append(f"遺失/改身分/重號 {a['num']} → {b.get('num')}")
    order = {"GREEN": 0, "YELLOW": 1, "RED": 2}
    if order.get(b.get("sdd"), 3) > order.get(a.get("sdd"), 3):
        out.append(f"SDD {a.get('sdd')} → {b.get('sdd')}")
    for rule, av in (a.get("sdd_rules") or {}).items():
        bv = (b.get("sdd_rules") or {}).get(rule)
        al, alen = av.split("|")
        bl, blen = (bv or "MISSING|0").split("|")
        if order.get(bl, 3) > order.get(al, 3) or (bl == al and al in ("RED", "YELLOW") and int(blen) > int(alen)):
            out.append(f"SDD {rule} {al} → {bl}(訊息 {alen} → {blen} 字)")
    return out


def prune_prove(via: Path, cands: list[dict], log=print, lanes: int = 4) -> dict:
    """刪舊版先證明:同一份 git worktree(TEMP)先量基準 → git rm 候選 → 再量;
       受影響家族尾版載入 · 五個入口 --selftest · VCGC 四項檢查(MDL276 lost · 註冊 stale · MDL237 遺失/改身分/重號 · SDD)
       任何一項變差 → 牽連的候選剔除(lost 點名的)或整批不過(其餘指標)。"""
    from concurrent.futures import ThreadPoolExecutor
    top = Path(subprocess.run(["git", "-C", str(via), "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip())
    sub = via.resolve().relative_to(top.resolve())
    tmp = Path(tempfile.mkdtemp(prefix="via_prune_proof_"))
    wt = tmp / "wt"
    t0 = time.time()
    subprocess.run(["git", "-C", str(top), "worktree", "add", "-q", "--detach", str(wt), "HEAD"], check=True, capture_output=True)
    wvia = wt / sub
    try:
        fams = sorted({(x["dir"], x["family"]) for x in cands})
        tails = []
        for d, stem in fams:
            vs = sorted((via / d).glob(stem + "_v*.py"), key=_vnum)
            if vs:
                tails.append(str(vs[-1].relative_to(via)))
        entries = [str(t.relative_to(via)) for fam, _d, _e in SYS_ENTRY.values() if (t := find_tail(fam, [via]))]
        jobs = [(r, r in entries) for r in tails + entries]

        def run_all():
            with ThreadPoolExecutor(max_workers=max(1, min(6, lanes))) as ex:
                return dict(zip([j[0] for j in jobs], ex.map(lambda j: _probe(wvia, j[0], j[1]), jobs)))
        log(f"[prove] worktree {wt}({time.time() - t0:.0f}s)· 家族尾版 {len(tails)} · 入口 {len(entries)} · 量基準…")
        base_p = run_all()
        base_m = _vcgc_metrics(wvia)
        log(f"[prove] 基準 VCGC:{ {k: v for k, v in base_m.items() if k not in ('lost_paths', 'sdd_rules')} } · git rm {len(cands)} 支…")
        rel = [str(sub / x["path"]) for x in cands]
        for i in range(0, len(rel), 200):
            subprocess.run(["git", "-C", str(wt), "rm", "-q", "--", *rel[i:i + 200]], check=True, capture_output=True)
        after_p = run_all()
        after_m = _vcgc_metrics(wvia)
        log(f"[prove] 拿掉後 VCGC:{ {k: v for k, v in after_m.items() if k not in ('lost_paths', 'sdd_rules')} }")
    finally:
        subprocess.run(["git", "-C", str(top), "worktree", "remove", "--force", str(wt)], capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)
    results, bad = [], []
    for r, st in jobs:
        a, b = base_p[r], after_p[r]
        ok = not (a[0] == 0 and b[0] != 0) and (a[0] == b[0] or st)
        results.append({"file": r, "selftest": st, "rc_before": a[0], "rc_after": b[0], "ok": ok, "out": b[1] if not ok else ""})
        if not ok:
            bad.append(r)
            log(f"  [FAIL] {r} · 拿掉前 rc {a[0]} · 拿掉後 rc {b[0]}")
    new_lost = set(after_m.get("lost_paths", [])) - set(base_m.get("lost_paths", []))
    lost_names = {Path(p).name for p in new_lost}
    worse = [w for w in _worse(base_m, after_m) if not (w.startswith("lost") and lost_names)]
    bad_fams = {(str(Path(r).parent), re.sub(r"_v\d{4}$", "", Path(r).stem)) for r in bad}
    if any(r in entries for r in bad) or worse:
        proven = []
    else:
        proven = [x for x in cands if (x["dir"], x["family"]) not in bad_fams and Path(x["path"]).name not in lost_names]
    log(f"[prove] 尾版 / 入口不過 {len(bad)} · 登記冊新遺失 {len(new_lost)}(剔除)· 其他指標變差 {worse or '無'} · 證過 {len(proven)}")
    return {"checked": len(results), "failed": bad, "new_lost": sorted(new_lost), "worse": worse, "vcgc_before": base_m,
            "vcgc_after": after_m, "proven": proven, "results": results}


def prune_apply(via: Path, proven: list[dict]) -> dict:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dest_root = Path("functional modules") / "VIA_RetiredEngines" / f"prune_{ts}"
    moved = []
    for x in proven:
        src = Path(x["path"])
        dst = dest_root / src
        (via / dst).parent.mkdir(parents=True, exist_ok=True)
        sha = hashlib.sha256((via / src).read_bytes()).hexdigest()
        cp = subprocess.run(["git", "-C", str(via), "mv", str(src), str(dst)], capture_output=True, text=True)
        if cp.returncode == 0:
            moved.append({"from": src.as_posix(), "to": dst.as_posix(), "sha256": sha, "family": x["family"], "v": x["v"]})
    man = {"schema": "VIA.RetireManifest.v1", "batch": f"prune_{ts}", "by": f"{FAMILY} {VERSION} prune",
           "rule": "刪舊版先證明:鏈走不到 + 全倉無檔名引用 + TEMP 副本拿掉後尾版載入 / 入口自測同 rc;以搬代刪",
           "restore": "CGC_MDL276_QuarantineRecover restore <原路徑> --apply(或 git mv 回去)", "moved": moved}
    (via / dest_root).mkdir(parents=True, exist_ok=True)
    (via / dest_root / "RETIRE_MANIFEST.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"dest": dest_root.as_posix(), "moved": len(moved)}


def cmd_prune(systems: list[str] | None, prove: bool, apply: bool, limit: int, kinds: list[str]) -> int:
    via = next((r for r in PRIOR.search_roots() if (r / "supportive modules").is_dir()), CODE_ROOT)
    PRUNE_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rep = prune_scan(via, systems)
    if "error" in rep:
        print(f"[prune] {rep['error']}")
        return 3
    dead = rep["dead"]
    elig = [x for x in dead if x["kind"] in kinds][: limit or None]
    print(f"[prune] 範圍 {' · '.join(rep['systems'])} · 家族 {rep['families']}(多版 {rep['multi']})· 鏈上走不到 {len(dead)} · "
          f"分類 {rep['by_kind']} · 本輪可退役類別 {kinds} → {len(elig)} 支 · {time.time() - t0:.0f}s")
    rep.update({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "eligible": len(elig), "kinds": kinds})
    if prove and elig:
        pv = prune_prove(via, elig)
        if not pv["proven"] and (pv["failed"] or pv["new_lost"]) and not pv["worse"]:
            fam_bad = {(str(Path(r).parent), re.sub(r"_v\d{4}$", "", Path(r).stem)) for r in pv["failed"]}
            lost_names = {Path(p).name for p in pv["new_lost"]}
            retry = [x for x in elig if (x["dir"], x["family"]) not in fam_bad and Path(x["path"]).name not in lost_names]
            entries_bad = any(Path(r).stem.startswith(tuple(f for f, _d, _e in SYS_ENTRY.values())) for r in pv["failed"])
            if retry and len(retry) < len(elig) and not entries_bad:
                print(f"[prove] 重試一次:剔除不過的家族 {len(fam_bad)} 個 · 牽連遺失 {len(lost_names)} 支 → {len(retry)} 支")
                pv = prune_prove(via, retry)
        rep["proof"] = {k: v for k, v in pv.items() if k != "proven"}
        rep["proven"] = len(pv["proven"])
        print(f"[prove] 驗 {pv['checked']} 支 · 不過 {len(pv['failed'])} · 證過可退役 {len(pv['proven'])}")
        if apply:
            if pv["failed"]:
                print("[apply] 有證明不過的家族 → 那些家族的候選不搬;其餘照搬。")
            if pv["proven"]:
                ap = prune_apply(via, pv["proven"])
                rep["applied"] = ap
                print(f"[apply] 已搬 {ap['moved']} 支 → {ap['dest']}(RETIRE_MANIFEST.json;可單檔找回)")
            else:
                print("[apply] 沒有證過的 → 不搬、不建夾。")
    elif apply:
        print("[apply] 沒帶 --prove → 不搬(刪舊版先證明)。")
    (PRUNE_DIR / "PRUNE_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    by_sys = collections.Counter(next((s for s, f in SYS_FOLDERS.items() if x["dir"].startswith(f)), "?") for x in dead)
    rows = [{"category": "PRUNE", "metric": s, "lamp": "YELLOW" if by_sys[s] else "GREEN",
             "detail": f"鏈上走不到 {by_sys[s]} 支", "action": SYS_FOLDERS[s]} for s in rep["systems"]]
    rows += [{"category": "KIND", "metric": k, "lamp": "GREEN" if k == "UNREF" else "YELLOW", "detail": f"{n} 支",
              "action": {"UNREF": "沒人點名 → 可證可搬", "DOC_REF": "只有文件 / 快照提到 → 證過可搬", "REG_REF": "活的冊有登記(編號冊 / 子系統冊 / 交接冊)→ 先由 VCGC 編號標退役",
                         "SNAP_REF": "只在歷史快照 / 收據 → 證過可搬",
                         "CODE_REF": "程式點名 → 先遷引用", "LOCK_REF": "鎖定帳點名 → 永不搬(成功只增不減)"}.get(k, "-")} for k, n in rep["by_kind"].items()]
    _rows_print("VCGC 舊版退役閘(刪舊版先證明)", rows, note="預設乾跑 · 以搬代刪")
    print(f"[報告] {PRUNE_DIR / 'PRUNE_latest.json'}\nNEXT: " + ("via-prune --prove" if not prove else
          "via-prune --prove --apply" if not apply else "via-vcgc run CGC_MDL237_NumberingSystem audit(遺失 0 才算)"))
    return 0



# ------------------------------------------------------------------------------
# setup(v0101 + 瘦身:舊 PS 短令鏈改註解停用,開 PS 不再 16 秒;前後量錯誤數與載入毫秒,變差就還原)
# ------------------------------------------------------------------------------
SLIM_RX = re.compile(r"(Register-VIA-Commands|VIA-Commands-Override|Invoke-VIA-CommandsReset|Invoke-VIA-Launch)", re.I)
SLIM_TAG = "# [VIA-SLIM 停用] "


def slim_text(text: str, on: bool = True) -> str:
    """VIA 標記區塊外、點名舊 PS 短令鏈的行:on = 前面加停用註解;off = 拿掉本工具加的註解。其他行一字不動。"""
    out, inblock = [], False
    for line in text.splitlines():
        if PRIOR.PROFILE_BEGIN in line:
            inblock = True
        if not inblock:
            if on and SLIM_RX.search(line) and not line.lstrip().startswith("#"):
                line = SLIM_TAG + line
            elif not on and line.startswith(SLIM_TAG):
                line = line[len(SLIM_TAG):]
        if PRIOR.PROFILE_END in line:
            inblock = False
        out.append(line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def _profile_stats(env: dict) -> tuple[int, int]:
    rc, out = PRIOR._ps("$e = $Error.Count; $ms = [int]((Get-Date) - (Get-Process -Id $PID).StartTime).TotalMilliseconds; \"$e|$ms\"",
                        profile=True, env=env, timeout=120)
    m = re.search(r"(\d+)\|(\d+)\s*$", out or "")
    return (int(m.group(1)), int(m.group(2))) if m else (999, -1)


def cmd_setup2(check: bool, uninstall: bool, keep_old: bool, unslim: bool) -> int:
    if check or not PRIOR._pwsh():
        return PRIOR.cmd_setup(check, uninstall)
    env = _child_env({"VIA_CODE_ROOT": str(CODE_ROOT)})
    b_err, b_ms = _profile_stats(env)
    print(f"[setup] 改前:新開 pwsh 錯誤 {b_err} · 載入約 {b_ms} ms")
    orig = PRIOR.compose_profile
    if not keep_old:
        on = not (uninstall or unslim)
        PRIOR.compose_profile = lambda o, u=False: orig(slim_text(o, on=on), u)
    try:
        rc = PRIOR.cmd_setup(False, uninstall)
    finally:
        PRIOR.compose_profile = orig
    if rc != 0 or uninstall:
        return rc
    a_err, a_ms = _profile_stats(env)
    print(f"[setup] 改後:新開 pwsh 錯誤 {a_err} · 載入約 {a_ms} ms" + (f"(快 {b_ms - a_ms} ms)" if b_ms > 0 and a_ms >= 0 else ""))
    if a_err > b_err:
        prof = PRIOR.profile_path()
        baks = sorted(prof.parent.glob(prof.name + ".via_backup_*")) if prof else []
        if baks:
            prof.write_text(baks[-1].read_text(encoding="utf-8-sig"), encoding="utf-8-sig")
        print(f"[setup] 錯誤變多({b_err} → {a_err})→ 已還原原 profile。請貼這段給 AI;或用 via-setup --keep-old(不動舊行)。")
        return 1
    print("[setup] ✔ 舊 PS 短令鏈已停用(註解,不刪);要復原:via-setup --unslim")
    return 0

# ------------------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if not a:
        return cmd_menu()
    v, rest = a[0], a[1:]
    if v == "x":
        return dispatch(rest[0], rest[1:]) if rest else cmd_help()
    if v == "help":
        return cmd_help(rest[0] if rest else None)
    if v == "menu":
        return cmd_menu()
    if v == "names":
        return cmd_names("--ps" in rest)
    if v == "sys":
        return cmd_sys(rest[0], rest[1:]) if rest else (print("[sys] 要給系統:VDF · VRN · VCGC · VQG · VAP") or 2)
    if v == "tok":
        return cmd_tok(rest)
    if v == "prune":
        sysx = [rest[rest.index("--system") + 1].upper()] if "--system" in rest else None
        lim = int(rest[rest.index("--limit") + 1]) if "--limit" in rest else 0
        kinds = rest[rest.index("--kinds") + 1].split(",") if "--kinds" in rest else ["UNREF", "DOC_REF", "SNAP_REF"]
        return cmd_prune(sysx, "--prove" in rest, "--apply" in rest, lim, kinds)
    if v == "boot":
        return PRIOR.cmd_boot()
    if v == "setup":
        return cmd_setup2("--check" in rest, "--uninstall" in rest, "--keep-old" in rest, "--unslim" in rest)
    return PRIOR.main(a)


# ------------------------------------------------------------------------------
# selftest(暫存夾造資料;零網路)
# ------------------------------------------------------------------------------
def selftest() -> int:
    ok = bad = 0

    def chk(name, cond, note=""):
        nonlocal ok, bad
        ok += bool(cond)
        bad += not cond
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}", flush=True)

    names = [c["name"] for c in COMMANDS]
    chk("① 指令冊:名稱唯一 · 每列有說明 / 例子 / 正主 / 目標", len(names) == len(set(names))
        and all(c["help"] and c["examples"] and c["plugin"] and c["target"] for c in COMMANDS), f"({len(names)} 個)")
    chk("② 舊短令去重:舊名不跟新名撞、一個舊名只導一處", not (set(LEGACY) & set(names))
        and sum(len(c["replaces"]) for c in COMMANDS) == len(LEGACY), f"(併入 {len(LEGACY)})")
    hub_verbs = {"menu", "help", "update", "doctor", "install", "sys", "run", "auth", "tok", "bak", "prune", "pano", "ast", "plug", "setup"}
    chk("③ 每個短指令都導到中樞現有動詞", all(c["target"][0] in hub_verbs for c in COMMANDS))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cmd_names(ps=True)
    lines = buf.getvalue().splitlines()
    chk("④ names --ps:新指令 + 舊名對照,格式 名|目標", all(l.count("|") == 1 for l in lines)
        and "via-view|via-update" in lines and "via-update|via-update" in lines)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        rc_unknown = dispatch("via-nosuch", [])
    chk("⑤ 不認識的短令不跑、回 2", rc_unknown == 2)
    with tempfile.TemporaryDirectory(prefix="vcgc_prune_st_") as td:
        T = Path(td)
        fam = T / "fam"
        fam.mkdir()
        glob_tail = ("from pathlib import Path\nimport re\ndef _vnum(p):\n    m=re.search(r'_v(\\d{4})$',Path(p).stem);return int(m.group(1))\n"
                     "PRIOR=max((p for p in Path(__file__).parent.glob('F_v*.py') if _vnum(p)<_vnum(__file__)),key=_vnum)\n")
        (fam / "F_v0100.py").write_text("x=1\n", encoding="utf-8")            # 舊本體(被 v0102 取代)
        (fam / "F_v0101.py").write_text("x=2\n", encoding="utf-8")            # 舊本體
        (fam / "F_v0102.py").write_text("y=1\n", encoding="utf-8")            # 新本體(無前版連結)
        (fam / "F_v0103.py").write_text(glob_tail, encoding="utf-8")          # 薄尾 → glob 取前版 v0102
        (fam / "F_v0104.py").write_text("open('F_v0100.py')\n" + glob_tail, encoding="utf-8")  # 尾版又點名 v0100
        link = _load_token_link(CODE_ROOT)
        vs = {_vnum(p): p for p in fam.glob("F_v*.py")}
        live = live_versions("F", vs, link) if link else set()
        chk("⑥ 鏈判:尾版 glob → v0103 → v0102 本體停;被點名的 v0100 也算用到;只剩 v0101 可退",
            link is not None and live == {104, 103, 102, 100}, f"(live {sorted(live)})")
        (fam / "m_v0100.py").write_text("import sys\nif __name__ == '__main__':\n    sys.exit(0)\n", encoding="utf-8")
        chk("⑦ 有 main 守門才 import(沒守門的只 compile)", _has_main_guard(fam / "m_v0100.py") and not _has_main_guard(fam / "F_v0100.py"))
        rc, _o = _probe(T, "fam/m_v0100.py", False)
        chk("⑧ 證明探針:載入成功回 0", rc == 0)
    prof = ("Import-Module X\n. \"$HOME\\Register-VIA-Commands-v0279.ps1\"\n# keep\n" + PRIOR.profile_block() + "\n")
    sl = slim_text(prof)
    chk("⑬ 瘦身:只註解舊鏈那行、VIA 區塊不動、可完整復原",
        sl.count(SLIM_TAG) == 1 and PRIOR.profile_block() in sl and "Import-Module X" in sl and slim_text(sl, on=False) == prof
        and slim_text(sl) == sl)
    chk("⑨ 系統入口五個都有對應尾版家族", all(find_tail(f, [CODE_ROOT]) for f, _d, _e in SYS_ENTRY.values()))
    chk("⑩ 前版鏈在(v0101 → v0100)", hasattr(PRIOR, "cmd_update") and hasattr(P0, "cmd_panorama"))
    chk("⑪ 加速器橋執行時生效", VIA_ACCEL is not None)
    print(f"  [..] 前版 v0101 自測")
    with contextlib.redirect_stdout(io.StringIO()) as pbuf:
        rc = PRIOR.selftest()
    tail = [l for l in pbuf.getvalue().splitlines() if "[計]" in l or "FAIL" in l]
    chk("⑫ 前版 v0101 自測", rc == 0, f"({tail[-1].strip() if tail else rc})")
    print(f"  [計] {FAMILY} {VERSION} 自測 OK {ok} · FAIL {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
