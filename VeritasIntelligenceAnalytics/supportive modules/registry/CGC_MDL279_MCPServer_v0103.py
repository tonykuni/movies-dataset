#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL279_MCPServer v0103 — 薄尾(v0102 一字不動):收據分頁讀(位元組游標 + 來源 SHA)· 路徑界改 relative_to · tools/call 燈只代表行程

操作員 2026-11-15:「整合全部測試收尾 VCGC」(附件 VCGC_RepairKit_v0100:它把修正以「同名 v0100 就地改 + 外部 via_repair_core」交付,
違反版號律(同版號內容變)與編號律(via_repair_core 無號);本版把其中經沙盒重現的兩個缺陷收成 VCGC 自己的薄尾,不引外部模組)。
缺陷(origin/main 355e2fa 重現):
  ① read_resource 以 [:MAX_OUT] 字元截斷 → 大於 60000 字的收據(例 HANDOFF_latest.json 637 KB)回傳的是「壞掉的 JSON 開頭」,
     而且沒有任何「還有下一段」的訊號 → 讀的人(AI / 操作員)以為讀完了。
  ② 根目錄界用字串 startswith → 「…/VeritasIntelligenceAnalytics2/x」也算在根內。
  ③ tools/call 的 lamp 只看子行程 rc,卻寫成 GREEN / RED,讀的人會當成「業務驗收通過」。
本版:
  · 小檔(≤ MAX_OUT 位元組)且沒帶游標 → 原樣整份回(與前版逐字相同,前版自測照過)。
  · 大檔或帶游標 → 回一頁 VIA.EvidencePage.v1(JSON):source_sha256 · total_bytes · offset_bytes · returned_bytes · text ·
    truncated · next_offset_bytes · next_uri(via://key?offset=N&limit=L&sha=…);頁界落在 UTF-8 多位元組中間會退回字元邊界;
    帶 sha 而來源已變 → 錯誤「SOURCE_CHANGED:從 offset 0 重讀」;讀的期間來源變了也報錯。
  · via_receipt 工具多收 offset / limit / sha(整數 / 64 位十六進位),其餘照舊。
  · tools/call 的 structuredContent 多兩欄 lamp_scope="process_exit_only" · business_result_verified=false(燈不變,只說清楚它代表什麼)。
只讀 · 零寫入 · 零網路 · 不 import 他系統 · 不碰 TA-Lib · 不讀寫同意閘。用法同 v0102:--serve [--root] · --client-config [--root] · --selftest。
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
import re
import sys
from pathlib import Path

NAME = "CGC_MDL279_MCPServer"
VERSION = "v0103"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "CGC_MDL279_MCPServer_v0102.py"
_PRIOR_FILE = HERE / PRIOR_NAME
_spec = importlib.util.spec_from_file_location("CGC_MDL279_MCPServer_v0102", _PRIOR_FILE)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["CGC_MDL279_MCPServer_v0102"] = PRIOR
_spec.loader.exec_module(PRIOR)
P0 = PRIOR.P0                                   # v0100 本體(Server · tool_specs · RECEIPTS · MAX_OUT)

PAGE_BYTES = 32768
PAGE_MAX = 60000
SHA_RX = re.compile(r"^[0-9a-f]{64}$")
_ORIG = {"read_resource": P0.Server.read_resource, "call": P0.Server.call, "tool_specs": P0.tool_specs}


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _confined(root: Path, rel: str) -> Path:
    root = Path(root).resolve()
    p = (root / rel).resolve()
    try:
        p.relative_to(root)
    except ValueError:
        raise ValueError("outside VIA root") from None
    return p


def _parse(uri: str):
    key, sep, query = (uri[len("via://"):] if uri.startswith("via://") else uri).partition("?")
    cur = {}
    if sep:
        for pair in query.split("&"):
            k, eq, v = pair.partition("=")
            if not eq or k not in ("offset", "limit", "sha") or k in cur:
                raise ValueError("invalid resource cursor")
            cur[k] = v
    if "sha" in cur and not SHA_RX.match(cur["sha"]):
        raise ValueError("invalid source hash")
    try:
        off = int(cur.get("offset", 0)); lim = int(cur.get("limit", PAGE_BYTES))
    except ValueError:
        raise ValueError("cursor must be an integer") from None
    if off < 0 or not 4 <= lim <= PAGE_MAX:
        raise ValueError("invalid byte offset or page limit")
    return key, bool(sep), off, lim, cur.get("sha")


def read_page(p: Path, rel: str, offset: int, limit: int, want_sha: str | None) -> dict:
    sha = _sha256(p)
    if want_sha and want_sha != sha:
        raise ValueError("SOURCE_CHANGED: 來源已變,從 offset 0 重讀")
    total = p.stat().st_size
    if offset > total:
        raise ValueError("offset exceeds source size")
    with p.open("rb") as fh:
        fh.seek(offset)
        block = fh.read(limit)
    try:
        text = block.decode("utf-8")
    except UnicodeDecodeError as exc:
        if exc.reason == "unexpected end of data" and exc.start > 0 and offset + len(block) < total:
            block = block[:exc.start]; text = block.decode("utf-8")   # 頁界落在多位元組字中間 → 退回字元邊界
        else:
            raise ValueError("INVALID_UTF8_OR_OFFSET: offset 不在字元邊界(請用 next_offset_bytes)") from exc
    if _sha256(p) != sha:
        raise ValueError("SOURCE_CHANGED_DURING_READ")
    end = offset + len(block)
    return {"schema": "VIA.EvidencePage.v1", "source": rel, "source_sha256": sha, "total_bytes": total, "offset_bytes": offset,
            "returned_bytes": len(block), "text": text, "truncated": end < total, "next_offset_bytes": end if end < total else None,
            "complete_source_returned": offset == 0 and end == total, "encoding": "utf-8", "by": NAME + " " + VERSION}


def read_resource(self, uri: str, as_tool: bool = False) -> dict:
    key, has_cursor, off, lim, want = _parse(uri)
    if key not in P0.RECEIPTS:
        raise ValueError("unknown resource: %s" % uri)
    rel = P0.RECEIPTS[key]
    p = _confined(self.via, rel)
    if not p.is_file():
        text = "(這台機器還沒有這份收據:%s)" % rel
        if as_tool:
            return {"content": [{"type": "text", "text": text}], "isError": True}
        return {"contents": [{"uri": "via://" + key, "mimeType": "text/plain", "text": text}]}
    mime = "text/markdown" if p.suffix == ".md" else "application/json"
    if not has_cursor and p.stat().st_size <= P0.MAX_OUT:     # 小檔:與前版逐字相同
        text = p.read_text(encoding="utf-8", errors="replace")
        if as_tool:
            return {"content": [{"type": "text", "text": text}], "isError": False}
        return {"contents": [{"uri": "via://" + key, "mimeType": mime, "text": text}]}
    page = read_page(p, rel, off, lim, want)
    page["next_uri"] = ("via://%s?offset=%d&limit=%d&sha=%s" % (key, page["next_offset_bytes"], lim, page["source_sha256"])
                        if page["next_offset_bytes"] is not None else None)
    meta = {k: v for k, v in page.items() if k != "text"}
    body = json.dumps(page, ensure_ascii=False)
    if as_tool:
        return {"content": [{"type": "text", "text": body}], "isError": False, "structuredContent": meta}
    return {"contents": [{"uri": uri, "mimeType": "application/json", "text": body}], "_meta": meta}


def call(self, name: str, args: dict) -> dict:
    if name == "via_receipt":
        key = str(args.get("key") or "")
        if key not in P0.RECEIPTS:
            return {"content": [{"type": "text", "text": "unknown receipt key: %s" % key}], "isError": True}
        parts = []
        for k in ("offset", "limit"):
            if k in args:
                if type(args[k]) is not int:
                    return {"content": [{"type": "text", "text": "%s 要整數" % k}], "isError": True}
                parts.append("%s=%d" % (k, args[k]))
        if "sha" in args:
            parts.append("sha=" + str(args["sha"]))
        return self.read_resource("via://" + key + ("?" + "&".join(parts) if parts else ""), as_tool=True)
    r = _ORIG["call"](self, name, args)
    if isinstance(r.get("structuredContent"), dict) and "rc" in r["structuredContent"]:
        r["structuredContent"].update({"lamp_scope": "process_exit_only", "business_result_verified": False})
    return r


def tool_specs() -> list:
    specs = _ORIG["tool_specs"]()
    for t in specs:
        if t["name"] == "via_receipt":
            t["description"] += " · 大檔分頁:回 VIA.EvidencePage.v1,照 next_offset_bytes + sha 續讀(v0103)"
            t["inputSchema"]["properties"].update({
                "offset": {"type": "integer", "minimum": 0, "description": "位元組起點(續讀用上一頁的 next_offset_bytes)"},
                "limit": {"type": "integer", "minimum": 4, "maximum": PAGE_MAX, "description": "每頁位元組(預設 %d)" % PAGE_BYTES},
                "sha": {"type": "string", "pattern": "^[0-9a-f]{64}$", "description": "上一頁的 source_sha256;來源變了就報錯"}})
    return specs


def install():
    P0.Server.read_resource = read_resource
    P0.Server.call = call
    P0.tool_specs = tool_specs
    P0.VERSION = VERSION


install()
RECEIPTS, READ_VERBS, PROTOCOL = P0.RECEIPTS, P0.READ_VERBS, P0.PROTOCOL


def client_config(via: Path) -> dict:
    cfg = PRIOR.client_config(via)
    text = json.dumps(cfg, ensure_ascii=False).replace(str(_PRIOR_FILE), str(Path(__file__).resolve())).replace(_PRIOR_FILE.name, Path(__file__).name)
    return json.loads(text)


def selftest() -> int:
    import tempfile
    rc = PRIOR.selftest()                       # 前版鏈(v0102 → v0101 → v0100)在本版換裝後照跑:小檔行為不變
    ok = []

    def chk(n, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", n, (" · " + str(note)) if note else ""), flush=True)
    with tempfile.TemporaryDirectory(prefix="via_mcp103_") as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        rel = P0.RECEIPTS["mutual/latest"]
        f = via / rel; f.parent.mkdir(parents=True)
        big = {"lamp": "GREEN", "rows": [{"i": i, "名": "台積電 2330 中文" * 3} for i in range(4000)]}
        raw = json.dumps(big, ensure_ascii=False).encode("utf-8"); f.write_bytes(raw)
        srv = P0.Server(via, None)
        r = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "resources/read", "params": {"uri": "via://mutual/latest"}})["result"]
        pg = json.loads(r["contents"][0]["text"])
        chk("ⓐ 大檔(%d 位元組 > %d)不再截成壞 JSON:回 EvidencePage · truncated · 有 next_uri" % (len(raw), P0.MAX_OUT),
            pg["schema"] == "VIA.EvidencePage.v1" and pg["truncated"] and pg["next_uri"] and pg["total_bytes"] == len(raw))
        got, uri, n = b"", "via://mutual/latest", 0
        while uri and n < 200:
            res = srv.handle({"jsonrpc": "2.0", "id": 2, "method": "resources/read", "params": {"uri": uri}})["result"]
            pj = json.loads(res["contents"][0]["text"]); got += pj["text"].encode("utf-8"); uri = pj["next_uri"]; n += 1
        chk("ⓑ 照 next_uri 續讀 %d 頁拼回 = 原檔逐位元組相同 · 拼回是合法 JSON(頁界落在中文字中間會退回字元邊界)" % n,
            got == raw and json.loads(got.decode("utf-8"))["rows"][-1]["i"] == 3999)
        t = srv.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "via_receipt", "arguments": {"key": "mutual/latest", "offset": 0, "limit": 1000}}})["result"]
        chk("ⓒ via_receipt 帶 offset/limit:工具回同一種頁 · structuredContent 有 next_offset_bytes", t["structuredContent"]["returned_bytes"] <= 1000 and t["structuredContent"]["next_offset_bytes"])
        bad = srv.handle({"jsonrpc": "2.0", "id": 4, "method": "resources/read", "params": {"uri": "via://mutual/latest?offset=0&limit=100&sha=" + "0" * 64}})
        chk("ⓓ 帶舊 sha 而來源已變 → 報錯 SOURCE_CHANGED(不默默給新內容)", "SOURCE_CHANGED" in json.dumps(bad, ensure_ascii=False))
        sm = via / P0.RECEIPTS["backup/check"]; sm.parent.mkdir(parents=True, exist_ok=True); sm.write_text('{"lamp": "GREEN"}', encoding="utf-8")
        s = srv.handle({"jsonrpc": "2.0", "id": 5, "method": "resources/read", "params": {"uri": "via://backup/check"}})["result"]["contents"][0]["text"]
        chk("ⓔ 小檔不帶游標 → 整份原樣回(與前版逐字相同)", s == '{"lamp": "GREEN"}')
        twin = Path(td) / "VeritasIntelligenceAnalytics2"; twin.mkdir()
        try:
            _confined(via, "../VeritasIntelligenceAnalytics2/x.json"); esc = False
        except ValueError:
            esc = True
        chk("ⓕ 根界改 relative_to:兄弟夾「…Analytics2」不再被字串前綴當成根內", esc)
        spec = next(x for x in P0.tool_specs() if x["name"] == "via_receipt")["inputSchema"]["properties"]
        chk("ⓖ tools/list 的 via_receipt 多 offset · limit · sha;key enum 照舊", {"offset", "limit", "sha", "key"} <= set(spec) and "mutual/latest" in spec["key"]["enum"])
        r2 = call(srv, "vcgc_status", {})
        chk("ⓗ tools/call 沒有主控台時照前版回錯;有 rc 時 structuredContent 加 lamp_scope=process_exit_only", r2.get("isError") is True)
        cfg = client_config(via)
        chk("ⓘ client-config 的 command 指到本檔(v0103)", Path(__file__).name in json.dumps(cfg) and _PRIOR_FILE.name not in json.dumps(cfg))
    bad = len(ok) - sum(ok)
    print("[%s] %s %s --selftest · 本版 %d 項 · 不過 %d(v0102 鏈 rc %d)" % ("PASS" if not bad and rc == 0 else "FAIL", NAME, VERSION, len(ok), bad, rc), flush=True)
    return 0 if not bad and rc == 0 else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args or (args and args[0] in ("selftest", "test")):
        return selftest()
    if "--client-config" in args:
        root = args[args.index("--root") + 1] if "--root" in args else None
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
