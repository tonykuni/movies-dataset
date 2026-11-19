#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL158_VIAPanoramaAuditRepair v0119 — 薄尾:動詞表寫在本檔(修舊主控台字串門回歸)· tools 工具註冊清單 · verbs(v0118 以前一字不動)

  ① 回歸修正:主控台舊本體(CGC_MDL149 v0131 ~ v0142)的 require_token_gate 用「字串」在目錄裡版號最新的 MDL158 檔找
     "read" / "slice" / "digest" / --if-etag / def pack_payload。v0118 是轉接薄尾,這些字都在前版 → 自 PR #682 起
     status 等落到舊本體 main 的動詞一律 rc 2(容器 2026-11-19 實測 status rc 2)。本版把動詞表 VERBS 與 pack_payload 轉接
     明寫在本檔,舊門判綠;門的判法不改(主控台 101 版鏈經子行程轉交,換不到門所在的行程)。之後 MDL158 每一版都要保有 VERBS。
  ② tools:省 Token 與支援工具註冊清單(操作員 2026-11-19 18:17「這些工具是否弄一個註冊清單顯示依竊功能方便 AI 省 TOKEN」)。
     讀三本冊合成一張卡,不另立正本:鎖冊 VIA_ToolVersion_Lock(哪一支現役)× 引擎版本冊(VIA-TOOL 席位號)×
     AI 功能卡 VIA_AI_FunctionCard_SSOT 尾版的 tool_registry(每家做什麼 · AI 什麼時候用 · 指令)。三數:應列 · 已列 · 略過。
  ③ verbs:本工具全部動詞一行一個(用法 · 何時用 · 做什麼),來源就是本檔 VERBS。
其餘動詞原樣轉交 v0118(TEMP 快取 · delta · fix 加固照舊)。唯讀:tools / verbs 只讀冊,不寫任何檔。零網路 · 不碰 TA-Lib。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import functools
import importlib.util
import io
import json
import re
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
_STEM = "CGC_MDL158_VIAPanoramaAuditRepair"
_V0119 = "v0119"
LOCK_BOOK = "VIA_ToolVersion_Lock_v0100.json"
REGISTER_BOOK = "VIA_EngineVersion_Register_v0100.json"
CARD_GLOB = "VIA_AI_FunctionCard_SSOT_v*.json"

# 本工具全部動詞(唯一來源;tools / verbs / 功能卡都照這張)。用法裡的 $E = 鎖冊 token 那一支。
VERBS = {
    "read": ("read <檔或夾…> [--depth N] [--if-etag <etag>]", "讀任何約 >200 行的檔、整夾、.json / .jsonl 之前",
             "骨架卡:匯入 · 定義樹(行號 · 簽章 · 首行說明)· AST 問題;夾 = 一檔一行;.json 看兩層、.jsonl 看欄位次數與首末列"),
    "slice": ("slice <檔> <定義名|Class.method|JSON 路徑> [--if-etag <etag>]", "只要看或改其中一段",
              "只取一個定義的原始碼(帶行號);JSON 路徑 a.b[0] · [-1] · [*] · [鍵=值]"),
    "digest": ("digest <日誌>", "看跑測 / 執行日誌", "只留判決行;紅日誌誠實回 rc 1"),
    "pack": ("pack <夾> [--limit N] [--if-etag <etag>]", "第一次看一整個資料夾", "整夾索引(大到小 · 入口檔優先 · 略過原因計數)"),
    "--if-etag": ("<read|slice|pack> … --if-etag <上次的 etag>", "同一對話重讀同一檔", "位元沒變回 304,沿用上一張卡;新對話不要帶"),
    "chain": ("chain <家族名|任一版的檔> [--all]", "改任何薄尾家族(出新版號檔)之前", "版本鏈圖:誰是本體、誰蓋了誰、誰釘死前版名"),
    "scan": ("scan [--json]", "要全倉問題清單時(走 TEMP 快取)", "全景稽核:治理七類 + 通用 AST 類,只報位置不改"),
    "report": ("report", "要給人看的全景報告", "全景稽核的報告版(同 scan 的資料)"),
    "delta": ("delta [--max N]", "每次接手:只看這輪跟上輪比新增 / 已解的問題", "全景走快取跑一輪,只印差異與三數(應掃 · 已掃 · 略過);快照存 TEMP"),
    "fix": ("fix [--apply]", "批次修補(先乾跑看清單,操作員或規則允許才 --apply)",
            "先備份到 TEMP → 改 → ast.parse + compile + 重新稽核不變差,任一關不過自動還原;原子換檔"),
    "tests": ("tests", "要看哪些檔有對應測試", "測試覆蓋清單"),
    "cache": ("cache [status|clear]", "懷疑快取過舊或要騰空間", "看 / 清 TEMP 稽核快取(%TEMP%\\VIA_token_cache\\MDL158;VIA_TOKEN_CACHE 可改位置)"),
    "tools": ("tools [--json]", "進場第一次、或不確定有沒有現成工具時", "省 Token 與支援工具註冊清單:每家現役檔 · VIA-TOOL 號 · 做什麼 · 何時用 · 指令"),
    "verbs": ("verbs", "要查本工具某個動詞怎麼用", "本表:全部動詞 · 用法 · 何時用 · 做什麼"),
    "--selftest": ("--selftest", "換版或懷疑工具壞了", "本版自測 + 前版鏈自測"),
}
OWN = ("tools", "verbs")


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                  default=HERE / "CGC_MDL158_VIAPanoramaAuditRepair_v0118.py")
_spec = importlib.util.spec_from_file_location("panorama_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


@functools.wraps(PRIOR.pack_payload)
def pack_payload(root, limit: int = 200) -> dict:
    """整夾索引:原樣轉交前版鏈(明寫在本檔,讓只認字串的舊門也看得到)。"""
    return PRIOR.pack_payload(root, limit)


def digest_log(text: str) -> dict:
    """日誌摘要:原樣轉交前版鏈。"""
    return PRIOR.digest_log(text)


# ── ② 工具註冊清單 ───────────────────────────────────────────────────────
def _json(path: Path) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}


def _newest_card(here: Path) -> Path | None:
    hits = [p for p in Path(here).glob(CARD_GLOB) if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def registry(here: Path | None = None, repo: Path | None = None) -> dict:
    """鎖冊 × 引擎版本冊 × 功能卡 tool_registry → 一張註冊清單。只讀。"""
    here = Path(here or HERE)
    repo = Path(repo or here.parents[2])
    lock = _json(here / LOCK_BOOK)
    reg = _json(here / REGISTER_BOOK)
    card_path = _newest_card(here)
    card = _json(card_path) if card_path else {}
    desc = card.get("tool_registry") or {}
    fams = [k for k, v in lock.items() if isinstance(v, dict) and v.get("path")]
    rows, skipped = [], []
    for fam in fams:
        ent = lock[fam]
        path = repo / str(ent["path"])
        seat = next((r for r in reg.get("rows") or [] if r.get("family") == fam and r.get("role") == "engine"), None)
        d = desc.get(fam) or {}
        lamp = "GREEN"
        why = []
        if not path.is_file():
            lamp, why = "RED", why + ["鎖冊那一支不在"]
        if not seat:
            lamp, why = ("RED" if lamp == "RED" else "YELLOW"), why + ["引擎版本冊沒有席位列"]
        if not d:
            lamp, why = ("RED" if lamp == "RED" else "YELLOW"), why + ["功能卡 tool_registry 沒寫這家"]
        rows.append({"family": fam, "lamp": lamp, "file": Path(str(ent["path"])).name, "version": ent.get("version"),
                     "code": (seat or {}).get("code", ""), "what": d.get("what", ""), "when": d.get("when", ""),
                     "use": d.get("use", ""), "functions": d.get("functions") or {}, "why": why})
    for fam in sorted(set(desc) - set(fams)):
        skipped.append({"family": fam, "why": "功能卡有、鎖冊沒有(不是 VCGC 啟用的工具,只列不算)"})
    state = "RED" if any(r["lamp"] == "RED" for r in rows) else ("YELLOW" if any(r["lamp"] == "YELLOW" for r in rows) else "GREEN")
    return {"state": state, "should": len(fams), "listed": len(rows), "skipped": skipped, "rows": rows,
            "card": card_path.name if card_path else "", "lock": LOCK_BOOK, "register": REGISTER_BOOK}


def render_registry(r: dict) -> str:
    out = ["[工具註冊清單] %s · 應列 %d · 已列 %d · 略過 %d · 來源:%s × %s × %s"
           % (r["state"], r["should"], r["listed"], len(r["skipped"]), r["lock"], r["register"], r["card"] or "功能卡 ABSENT")]
    for x in r["rows"]:
        out.append("  %-6s %-11s %s · %s · %s" % (x["lamp"], x["family"], x["file"], x["code"] or "無號", x["what"]))
        if x["when"]:
            out.append("         何時:%s" % x["when"])
        if x["use"]:
            out.append("         指令:%s" % x["use"])
        for k, v in x["functions"].items():
            out.append("         · %s:%s" % (k, v))
        for w in x["why"]:
            out.append("         ! %s" % w)
    for s in r["skipped"]:
        out.append("  略過   %-11s %s" % (s["family"], s["why"]))
    out.append("  [本工具動詞] python3 \"$E\" verbs(%d 個)· 全卡:VIA_FROM_VCGC=YES python3 \"$V\" functions" % len(VERBS))
    return "\n".join(out)


def render_verbs() -> str:
    out = ["[%s %s 動詞表] %d 個 · $E = 鎖冊 token 那一支" % (_STEM, _V0119, len(VERBS))]
    for k, (usage, when, what) in VERBS.items():
        out.append("  %-10s python3 \"$E\" %s" % (k, usage))
        out.append("             何時:%s · 做什麼:%s" % (when, what))
    return "\n".join(out)


def main() -> int:
    argv = sys.argv[1:]
    if argv == ["--selftest"]:
        return selftest()
    verb = argv[0] if argv else ""
    if verb == "tools":
        r = registry()
        print(json.dumps(r, ensure_ascii=False, indent=1) if "--json" in argv else render_registry(r))
        return 0 if r["state"] != "RED" else 1
    if verb == "verbs":
        print(render_verbs())
        return 0
    return PRIOR.main()


def legacy_gate_sees(path: Path) -> dict:
    """照抄主控台舊本體 token_roster 的判法(同針、同上限),看本檔在舊門眼中齊不齊。"""
    def has(needle: str, limit: int = 8000) -> bool:
        seen = 0
        with Path(path).open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                seen += len(line)
                if needle in line:
                    return True
                if seen > limit * 80:
                    return False
        return False
    return {"read": has('"read"'), "slice": has('"slice"'), "digest": has('"digest"'),
            "etag": has("--if-etag"), "pack": has("def pack_payload")}


def selftest() -> int:
    rc_prior = PRIOR.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note and not cond else ""))
    need = {"read", "slice", "digest", "pack", "chain", "scan", "report", "fix", "tests", "cache", "delta"}
    chk("① 動詞表涵蓋前版鏈全部動詞(本體 8 · v0117 chain · v0118 cache / delta)", need <= set(VERBS), sorted(need - set(VERBS)))
    g = legacy_gate_sees(Path(__file__))
    chk("② 主控台舊本體字串門(token_roster 同判法)對本檔全綠", all(g.values()), g)
    with tempfile.TemporaryDirectory(prefix="via_mdl158_v0119_") as td:
        root = Path(td)
        (root / "a_v0100.py").write_text("def f():\n    return 1\n", encoding="utf-8")
        (root / "b.txt").write_text("x\n", encoding="utf-8")
        chk("③ pack_payload 明寫轉接 · 結果與前版逐筆相同", pack_payload(root, 50) == PRIOR.pack_payload(root, 50))
        log = "[計] X 本版 3/3 · PASS\nnoise\n"
        chk("④ digest_log 明寫轉接 · 結果與前版相同", digest_log(log) == PRIOR.digest_log(log))
        reg = root / "registry"
        reg.mkdir()
        (root / "tools").mkdir()
        (root / "tools" / "t_v0101.py").write_text("x = 1\n", encoding="utf-8")
        (reg / LOCK_BOOK).write_text(json.dumps({"schema": "x", "alpha": {"version": "v0101", "path": "tools/t_v0101.py"},
                                                 "beta": {"version": "v0100", "path": "tools/missing_v0100.py"}}), encoding="utf-8")
        (reg / REGISTER_BOOK).write_text(json.dumps({"rows": [{"family": "alpha", "role": "engine", "code": "VIA-TOOL-0001"},
                                                              {"family": "alpha", "role": "candidate", "code": "VIA-TOOL-0002"}]}), encoding="utf-8")
        (reg / "VIA_AI_FunctionCard_SSOT_v0100.json").write_text(json.dumps({"tool_registry": {
            "alpha": {"what": "A", "when": "W", "use": "U", "functions": {"f": "g"}}, "gamma": {"what": "G"}}}), encoding="utf-8")
        r = registry(here=reg, repo=root)
        a = next(x for x in r["rows"] if x["family"] == "alpha")
        b = next(x for x in r["rows"] if x["family"] == "beta")
        chk("⑤ 註冊清單:席位號取 role=engine · 三本冊都對上 = 綠", a["lamp"] == "GREEN" and a["code"] == "VIA-TOOL-0001", a)
        chk("⑥ 鎖冊那一支不在 = 紅 · 沒席位 / 沒說明照實點名;總燈紅", b["lamp"] == "RED" and len(b["why"]) == 3 and r["state"] == "RED", b)
        chk("⑦ 三數對得上:應列 = 鎖冊家數 · 功能卡多寫的家列進略過不算", r["should"] == 2 and r["listed"] == 2
            and [s["family"] for s in r["skipped"]] == ["gamma"], r)
    buf = io.StringIO()
    with redirect_stdout(buf):
        sys_argv, sys.argv = sys.argv, [sys.argv[0], "verbs"]
        try:
            rc_v = main()
        finally:
            sys.argv = sys_argv
    chk("⑧ verbs 印出全部動詞", rc_v == 0 and all(("python3 \"$E\" " + VERBS[k][0]) in buf.getvalue() for k in VERBS))
    real = registry()
    chk("⑨ 真冊:鎖冊每一家都列出、鎖冊那一支都在(說明缺的照實黃)", real["listed"] == real["should"] > 0
        and not any("鎖冊那一支不在" in w for x in real["rows"] for w in x["why"]), real["state"])
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑩ 檔頭:加速器橋 · 網路橋在(__future__ 之後)· 不碰 TA-Lib",
        "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text and text.index("from __future__") < text.index("[VIA:ACCEL-BRIDGE")
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    passed = rc_prior == 0 and all(ok)
    print("[計] %s %s 本版 %d/%d · 前版 %s · %s" % (_STEM, _V0119, sum(ok), len(ok), "PASS" if rc_prior == 0 else "FAIL", "PASS" if passed else "FAIL"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
