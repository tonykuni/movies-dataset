#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL279_MCPServer v0103 — 薄尾(v0102 一字不動):MCP 多露三個省 Token 讀檔動詞 vcgc_read · vcgc_slice · vcgc_digest(只讀)。

操作員 2026-11-13:「接進 VCGC 並補上 MCP 的 read slice digest」。v0102 露 16 個動詞,經 OmniRoute / 各 AI 平台進來的 AI
  拿得到 token 卡(vcgc_token)卻不能用骨架卡讀檔——只好整檔讀,省 Token 白做。本版補上那三支,全部委派**鎖版 token 工具**:
  · 工具路徑與 sha256 取自 VIA_ToolVersion_Lock_v0100.json 的 token 席位;sha 對不上 = 鎖檔被改 → 停,不跑(CLAUDE.md「紅就停」)。
    不自己取尾版(工具換版只經 via-vcgc tools activate)。
  · 路徑只收倉內:相對路徑依序試 VIA 根 → 倉根,resolve 之後(含符號連結)必須仍在倉根底下;
    `.git/` · `private/` · `.env*` · 金鑰檔(.pem .key .p12 .pfx)一律拒讀。
  · 參數照 argv 傳(不經殼),定義名 / etag / depth 各有格式閘。
  · rc 0 = GREEN · rc 1 = digest 判紅日誌(是答案,不是錯)· rc 3 = NODATA / ABSENT(照實,不是錯);其他 rc 才標 isError。
其餘(協定 · stdio · 主控台動詞白名單 · 拒寫 · 收據資源)全部沿用 v0102;--client-config 的 command 指到本檔。
用法同 v0102:--serve [--root] · --client-config [--root] · --selftest(先 v0102 鏈再本版)。
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
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

NAME = "CGC_MDL279_MCPServer"
VERSION = "v0103"
HERE = Path(__file__).resolve().parent


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d{4})$", p.stem)
    return int(m.group(1)) if m else -1


# 前版 = 同家族、版號比本檔小的最大那一支(尾版律 glob,不釘名)
_PRIOR_FILE = max((p for p in HERE.glob(NAME + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(_PRIOR_FILE.stem, _PRIOR_FILE)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_PRIOR_FILE.stem] = PRIOR
_spec.loader.exec_module(PRIOR)
P0 = PRIOR.P0                                  # v0100 本體(Server · tool_specs · resource_specs)

LOCK_BOOK = "supportive modules/registry/VIA_ToolVersion_Lock_v0100.json"
DENY_PARTS = (".git", "private")
DENY_SUFFIX = (".pem", ".key", ".p12", ".pfx")
OK_RC = {0: "GREEN", 1: "RED", 3: "NODATA"}      # digest 判紅日誌回 1、找不到 / 沒這個定義回 3:都是答案
_LOCK_OVERRIDE: dict | None = None             # 只給自測用(模擬鎖檔被改)

FILE_VERBS = {
    "vcgc_read": ("read", "骨架卡(省 Token 第一招):.py/.ps1 定義樹 + AST 問題 · .json 兩層 · .jsonl 欄位;給夾 = 一檔一行全景。參數 path(倉內)· 可選 depth · if_etag"),
    "vcgc_slice": ("slice", "只取一個定義的原始碼(帶行號)或一段 JSON 路徑。參數 path · name(定義名 / Class.method / a.b[0])"),
    "vcgc_digest": ("digest", "跑測日誌只留判決行(紅日誌回 RED,照實)。參數 path(倉內日誌)"),
}


def _spec_of(name: str) -> dict:
    props = {"path": {"type": "string", "description": "倉內路徑(相對倉根或 VIA 根皆可)"}}
    req = ["path"]
    if name == "vcgc_read":
        props["depth"] = {"type": "integer", "minimum": 1, "maximum": 6, "description": ".json 看幾層(預設 2)"}
        props["if_etag"] = {"type": "string", "description": "上一張卡的 etag;原檔沒變回 304"}
    if name == "vcgc_slice":
        props["name"] = {"type": "string", "description": "定義名 · Class.method · JSON 路徑"}
        req.append("name")
    return {"name": name, "description": "%s(只讀 · 鎖版 token 工具)" % FILE_VERBS[name][1],
            "inputSchema": {"type": "object", "properties": props, "required": req, "additionalProperties": False}}


def _lock(via: Path) -> dict:
    if _LOCK_OVERRIDE is not None:
        return _LOCK_OVERRIDE
    return json.loads((via / LOCK_BOOK).read_text(encoding="utf-8"))["token"]


def _err(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}], "isError": True}


def _inside(via: Path, raw: str) -> Path:
    """倉內路徑閘:回解析後的絕對路徑;不合就丟 ValueError(訊息給 AI 看得懂)。"""
    if not raw or len(raw) > 1024 or any(c in raw for c in "\x00\n\r"):
        raise ValueError("path 不合(空 / 太長 / 含控制字元)")
    repo = via.parent.resolve()
    q = Path(raw)
    cands = [q] if q.is_absolute() else [via / q, via.parent / q]
    inside = []                                   # 先判倉內外(realpath 對不存在的路徑也算得出來)→ 倉外一律拒,不透露存在與否
    for c in cands:
        real = Path(os.path.realpath(c))
        if real.is_relative_to(repo):
            inside.append((real, real.relative_to(repo)))
    if not inside:
        raise ValueError("拒讀:倉外路徑(只收倉根 %s 底下)" % repo)
    hit = next(((r, rel) for r, rel in inside if r.exists()), None)
    if hit is None:
        raise FileNotFoundError("找不到 %s(倉內試過:%s)" % (raw, " · ".join(str(rel) for _, rel in inside)))
    real, rel = hit
    if any(part in DENY_PARTS for part in rel.parts) or real.name.startswith(".env") or real.suffix.lower() in DENY_SUFFIX:
        raise ValueError("拒讀:%s 在拒讀清單(.git/ · private/ · .env* · 金鑰檔)" % rel)
    return real


def file_verb(via: Path, name: str, args: dict, timeout: int = 300) -> dict:
    via = Path(via).resolve()
    try:
        real = _inside(via, str(args.get("path") or ""))
    except FileNotFoundError as exc:
        return {"content": [{"type": "text", "text": "[ABSENT] %s" % exc}], "isError": False,
                "structuredContent": {"rc": 3, "lamp": "NODATA", "argv": [FILE_VERBS[name][0]]}}
    except ValueError as exc:
        return _err(str(exc))
    argv = [FILE_VERBS[name][0], str(real)]
    if name == "vcgc_read":
        if args.get("depth") is not None:
            d = int(args["depth"])
            if not 1 <= d <= 6:
                return _err("depth 要 1–6")
            argv += ["--depth", str(d)]
        if args.get("if_etag"):
            et = str(args["if_etag"])
            if not re.fullmatch(r"[0-9a-f]{8,64}", et):
                return _err("if_etag 格式不合(十六進位 8–64 字)")
            argv += ["--if-etag", et]
    if name == "vcgc_slice":
        nm = str(args.get("name") or "")
        if not nm or len(nm) > 300 or any(c in nm for c in "\x00\n\r"):
            return _err("name 不合(空 / 太長 / 含控制字元)")
        argv.append(nm)
    try:
        lk = _lock(via)
        tool = (via.parent / lk["path"]).resolve()
        if not tool.is_file():
            return _err("鎖版 token 工具不在:%s(VCGC 紅就停)" % lk["path"])
        if hashlib.sha256(tool.read_bytes()).hexdigest() != lk["sha256"]:
            return _err("鎖版 token 工具 sha256 與鎖冊不符(鎖檔被改)→ 停,不跑;換版只經 via-vcgc tools activate")
    except (OSError, KeyError, ValueError) as exc:
        return _err("讀不到鎖冊 %s:%s: %s" % (LOCK_BOOK, type(exc).__name__, exc))
    env = dict(os.environ)
    env.update({"VIA_FROM_VCGC": "YES", "PYTHONUTF8": "1", "VIA_NO_OPEN": "1"})
    try:
        p = subprocess.run([sys.executable, str(tool), *argv], cwd=str(via.parent), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return _err("[逾時 %d 秒] %s" % (timeout, " ".join(argv[:1])))
    out = (p.stdout or "") + (p.stderr or "")
    if len(out) > P0.MAX_OUT:
        out = out[:P0.MAX_OUT] + "\n…(截斷:原輸出 %d 字;改用 slice 只取一段)" % len(out)
    return {"content": [{"type": "text", "text": out}], "isError": p.returncode not in OK_RC,
            "structuredContent": {"rc": p.returncode, "lamp": OK_RC.get(p.returncode, "RED"), "argv": [argv[0], str(real.relative_to(via.parent.resolve()))] + argv[2:],
                                  "tool": lk.get("version")}}


# ---------------------------------------------------------------- 掛上 v0100 本體(本體一字不動;前版自測時暫時卸下)
_ORIG_TOOL_SPECS = P0.tool_specs
_ORIG_CALL = P0.Server.call


def tool_specs() -> list:
    return _ORIG_TOOL_SPECS() + [_spec_of(n) for n in FILE_VERBS]


def _call(self, name: str, args: dict) -> dict:
    if name in FILE_VERBS:
        return file_verb(self.via, name, args or {})
    return _ORIG_CALL(self, name, args)


def _mount(on: bool) -> None:
    P0.tool_specs = tool_specs if on else _ORIG_TOOL_SPECS
    P0.Server.call = _call if on else _ORIG_CALL


_mount(True)
P0.VERSION = VERSION
RECEIPTS, READ_VERBS, PROTOCOL = P0.RECEIPTS, P0.READ_VERBS, P0.PROTOCOL


def client_config(via: Path) -> dict:
    cfg = PRIOR.client_config(via)
    text = json.dumps(cfg, ensure_ascii=False).replace(str(_PRIOR_FILE), str(Path(__file__).resolve())).replace(_PRIOR_FILE.name, Path(__file__).name)
    return json.loads(text)


def selftest() -> int:
    global _LOCK_OVERRIDE
    _mount(False)                                     # 前版自測數工具數要原樣 → 先卸下本版,跑完再掛回
    try:
        rc = PRIOR.selftest()
    finally:
        _mount(True)
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))

    via = P0.VIA_DEFAULT
    srv = P0.Server(via, None)

    ids = iter(range(100, 10 ** 6))

    def rpc(name, args):
        return srv.handle({"jsonrpc": "2.0", "id": next(ids), "method": "tools/call", "params": {"name": name, "arguments": args}})["result"]

    names = [t["name"] for t in srv.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})["result"]["tools"]]
    chk("ⓐ tools/list = 前版 %d + 本版 3(vcgc_read · vcgc_slice · vcgc_digest),slice 的 name 必填" % len(_ORIG_TOOL_SPECS()),
        len(names) == len(_ORIG_TOOL_SPECS()) + 3 and set(FILE_VERBS) <= set(names)
        and _spec_of("vcgc_slice")["inputSchema"]["required"] == ["path", "name"])
    me = "supportive modules/registry/" + Path(__file__).name
    r = rpc("vcgc_read", {"path": me})
    chk("ⓑ 經 JSON-RPC tools/call 真跑 vcgc_read(本檔 · VIA 根相對路徑)→ 骨架卡 · GREEN · 署名鎖版工具",
        not r["isError"] and "[py ·" in r["content"][0]["text"] and r["structuredContent"]["lamp"] == "GREEN", r["structuredContent"].get("tool"))
    et = re.search(r"etag=([0-9a-f]+)", r["content"][0]["text"])
    r2 = rpc("vcgc_read", {"path": "VeritasIntelligenceAnalytics/" + me, "if_etag": et.group(1) if et else "00000000"})
    chk("ⓒ 倉根相對路徑也收 · --if-etag 沒變回 304", not r2["isError"] and "304" in r2["content"][0]["text"])
    s = rpc("vcgc_slice", {"path": me, "name": "file_verb"})
    s_miss = rpc("vcgc_slice", {"path": me, "name": "no_such_def"})
    chk("ⓓ vcgc_slice 只回一個定義(帶行號);查無定義 = NODATA(rc 3)不是錯",
        not s["isError"] and "def file_verb" in s["content"][0]["text"] and "def _inside" not in s["content"][0]["text"]
        and not s_miss["isError"] and s_miss["structuredContent"]["lamp"] == "NODATA")
    log = via / "VIA_Reports" / "vcgc" / ("mcp_v0103_selftest_%d.log" % os.getpid())   # VIA_Reports 已被 git 忽略;跑完即刪
    log.parent.mkdir(parents=True, exist_ok=True)
    try:
        log.write_text("  [OK] 甲\n  [FAIL] 乙 真的壞了\n[計] 2 檢 OK 1 · FAIL 1\n", encoding="utf-8")
        d = rpc("vcgc_digest", {"path": str(log)})
    finally:
        log.unlink(missing_ok=True)
    chk("ⓔ vcgc_digest 紅日誌 → RED(是答案不是錯)· 只留判決行", not d["isError"] and d["structuredContent"]["lamp"] == "RED"
        and "乙" in d["content"][0]["text"])
    denied = {k: rpc("vcgc_read", {"path": v}) for k, v in {
        "倉外": "/etc/hostname", "倉外不存在": "/no/such/dir/id_rsa", "跳出": "../../../../../../etc/hostname",
        ".git": ".git/HEAD", "private": "private"}.items()}
    chk("ⓕ 拒讀:倉外絕對路徑(存在與不存在**回同一句**,不透露倉外有沒有那個檔)· ../ 跳出倉根 · .git/ · private/ 全部 isError 且講明原因",
        all(v["isError"] and "拒讀" in v["content"][0]["text"] for v in denied.values())
        and denied["倉外"]["content"][0]["text"] == denied["倉外不存在"]["content"][0]["text"],
        " · ".join("%s=%s" % (k, "拒" if v["isError"] else v["structuredContent"]["lamp"]) for k, v in denied.items()))
    bad_name = rpc("vcgc_slice", {"path": me, "name": "a\nb"})
    bad_etag = rpc("vcgc_read", {"path": me, "if_etag": "zz; rm -rf /"})
    chk("ⓖ 參數閘:定義名含換行 · etag 不是十六進位 → 不跑工具直接拒", bad_name["isError"] and bad_etag["isError"])
    real_lock = _lock(via)
    _LOCK_OVERRIDE = dict(real_lock, sha256="0" * 64)
    try:
        tampered = rpc("vcgc_read", {"path": me})
    finally:
        _LOCK_OVERRIDE = None
    chk("ⓗ 負控:鎖冊 sha 對不上 → 停,不跑(紅就停)", tampered["isError"] and "鎖檔被改" in tampered["content"][0]["text"])
    other = srv.call("via_receipt", {"key": "no-such"})
    chk("ⓘ 前版的動詞照舊走前版(via_receipt 不認得的 key 照前版回錯)", other["isError"] and "unknown receipt key" in other["content"][0]["text"])
    cfg = client_config(via)
    chk("ⓙ client-config 的 command 指到本檔(%s)" % VERSION, Path(__file__).name in json.dumps(cfg) and _PRIOR_FILE.name not in json.dumps(cfg))
    bad = len(ok) - sum(ok)
    print("[%s] %s %s --selftest · 本版 %d 項 · 不過 %d(%s 鏈 rc %d)" % ("PASS" if not bad and rc == 0 else "FAIL", NAME, VERSION, len(ok), bad, _PRIOR_FILE.stem[-5:], rc), flush=True)
    return 0 if not bad and rc == 0 else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args or (args and args[0] in ("selftest", "test")):
        return selftest()
    if "--client-config" in args:
        root = None
        if "--root" in args:
            root = args[args.index("--root") + 1]
        via = Path(root).resolve() if root else P0.VIA_DEFAULT
        if (via / "VeritasIntelligenceAnalytics").is_dir():
            via = via / "VeritasIntelligenceAnalytics"
        print(json.dumps(client_config(via), ensure_ascii=False, indent=2))
        return 0
    return P0.main(args)


def __getattr__(name):
    return getattr(PRIOR, name)


if __name__ == "__main__":
    sys.exit(main())
