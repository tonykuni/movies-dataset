#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VIA_PanoramaFusion_SuperEngine v0304 — 薄尾(v0300–v0303 一字不動):第三輪兩修(PR #782 Codex 2×P2),都在 prepare_file_task

① (P2)補丁核對範圍 = 實際要換掉的位元區間:v0300 的 `before` 取整行(含結尾註解、空白),編輯卻只到 end_col_offset,
     函式最後一行帶註解(例 `return x + 1  # keep`)就 PATCH_TOKEN_DRIFT,整批卡住。改成用同一個位元區間算 `before`,區間外的註解原樣留著。
② (P2)MCP 模組的 print 只轉 stderr「確定是診斷訊息」的(引數全是字串常數 / f-string);`print(json.dumps(response))` 這類
     可能是協定輸出的不動,記成 MCP_PRINT_LEFT_FOR_REVIEW 留給人看(不再把 JSON-RPC 回應送到 stderr)。
做法(CLAUDE.md「AST 節點手術」):只把 v0300 的 prepare_file_task 這一個節點抄進本檔改兩處,再用 types.FunctionType 綁回 v0300 的模組全域
  (不用 exec);v0300 其他函式照舊呼叫到它。其餘照 v0303 → v0302 → v0301 → v0300。自測零網路 · 暫存資料 · 不碰 TA-Lib · 不設同意閘。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import ast
import importlib.util
import re
import sys
import types
from pathlib import Path

VERSION = "v0304"
STEM = "VIA_PanoramaFusion_SuperEngine"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0303
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V300 = PRIOR.V300


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _v0304_exact_span(source: str, start: int, end_line: int, end_col: int) -> str:
    """與 ast_byte_edits 同一套位元座標:第 start 行行首 → 第 end_line 行的 end_col(UTF-8 位元)。"""
    lines = source.encode("utf-8").splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    return source.encode("utf-8")[offsets[start - 1]:offsets[end_line - 1] + end_col].decode("utf-8")


def _v0304_mcp_diagnostic(call: ast.Call) -> bool:
    """確定是給人看的診斷訊息:有引數、全是字串常數或 f-string、關鍵字只限 sep / end / flush。"""
    return bool(call.args) and all(isinstance(a, ast.JoinedStr) or (isinstance(a, ast.Constant) and isinstance(a.value, str))
                                   for a in call.args) and all(k.arg in {"sep", "end", "flush"} for k in call.keywords)


# ---- v0300 prepare_file_task 節點(第 2033–2080 行)抄入,改 ① ② 兩處 ----
def _prepare_file_task_v0304(cfg: dict, name: str, raw: bytes, patches: list[dict]) -> dict:
    """同檔所有錯誤合成一次 AST 手術，原版保持不動。"""
    source,encoding=source_text(raw);tree=ast.parse(source);edits=[];changes=[]
    for patch in patches:
        if patch.get('before_sha256')!=sha(raw):raise ValueError('PATCH_SOURCE_HASH')
        nodes=[n for n in tree.body if isinstance(n,FUN) and n.name==patch['symbol']]
        replacement=ast.parse(patch['replacement_def'])
        if len(nodes)!=1 or len(replacement.body)!=1 or not isinstance(replacement.body[0],FUN):raise ValueError('PATCH_SYMBOL_SCOPE')
        old=nodes[0];new=replacement.body[0]
        if api_shape(old)!=api_shape(new):raise ValueError('PATCH_API_BINDING')
        validate_patch_effects(cfg,old,new)
        start=min([old.lineno,*[d.lineno for d in old.decorator_list]])
        window=''.join(source.splitlines(keepends=True)[start-1:old.end_lineno])
        anchors=[t.string for t in tokenize.generate_tokens(io.StringIO(window).readline) if t.type==tokenize.COMMENT and re.search(r'\[(?:AST-ANCHOR|ANCHOR):',t.string)]
        if any(a not in patch['replacement_def'] for a in anchors):raise ValueError('PATCH_ANCHOR_LOSS')
        edits.append({'line':start,'col':0,'end_line':old.end_lineno,'end_col':old.end_col_offset,'text':patch['replacement_def'].rstrip(),'before':_v0304_exact_span(source,start,old.end_lineno,old.end_col_offset)})
        changes.append({'kind':'SCOPED_COMPLETE_DEF','symbol':old.name,'line':start,'end':old.end_lineno})
    # 自動手術不與完整 def 範圍重疊；重疊者留給該 def 一次解決。
    occupied=[(e['line'],e['end_line']) for e in edits]
    mcp=name in set(cfg['fusion'].get('mcp_modules',[]));need_helper=False
    helper_nodes=[n for n in tree.body if isinstance(n,FUN) and n.name=='_via_mcp_log']
    if helper_nodes and ast.dump(helper_nodes[0])!=ast.dump(ast.parse(MCP_LOG_HELPER).body[0]):raise ValueError('MCP_HELPER_COLLISION')
    for n in ast.walk(tree):
        if any(a<=getattr(n,'lineno',0)<=b for a,b in occupied):continue
        if mcp and isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='print' and not any(k.arg=='file' or k.arg is None for k in n.keywords) and not _v0304_mcp_diagnostic(n):
            changes.append({'kind':'MCP_PRINT_LEFT_FOR_REVIEW','line':n.lineno});continue
        if mcp and isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='print' and not any(k.arg=='file' or k.arg is None for k in n.keywords):
            f=n.func;edits.append({'line':f.lineno,'col':f.col_offset,'end_line':f.end_lineno,'end_col':f.end_col_offset,'before':'print','text':'_via_mcp_log'})
            need_helper=True;changes.append({'kind':'MCP_STDERR','line':f.lineno})
    for old,new in zip(tree.body,tree.body[1:]):
        if isinstance(old,ast.Import) and isinstance(new,ast.Import) and ast.dump(old)==ast.dump(new) and new.lineno==old.end_lineno+1 and not any(a<=new.lineno<=b for a,b in occupied):
            edits.append({'line':new.lineno,'col':new.col_offset,'end_line':new.end_lineno,'end_col':new.end_col_offset,'before':ast.get_source_segment(source,new),'text':''})
            changes.append({'kind':'ADJACENT_DUPLICATE_IMPORT','line':new.lineno})
    value=ast_byte_edits(source,edits) if edits else source
    if need_helper and not helper_nodes:
        # helper 必須在頂層呼叫前可用，插在 module doc / future 後，不能只附檔尾。
        current=ast.parse(value);at=0
        for n in current.body:
            if isinstance(n,ast.ImportFrom) and n.module=='__future__':at=max(at,n.end_lineno)
            elif n is current.body[0] and isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str):at=max(at,n.end_lineno)
        value=apply_spans(value,[(at,at,MCP_LOG_HELPER)])
    value_raw=value.encode(encoding)
    old_red=counted_red({name:raw},cfg['fusion']['mcp_modules']);new_red=counted_red({name:value_raw},cfg['fusion']['mcp_modules'])
    # 行號因 helper 位移時比較 rule/symbol 身分，不用行數位移誤判為新錯。
    before_count=collections.Counter((a[1],a[2]) for a in old_red.elements())
    after_count=collections.Counter((a[1],a[2]) for a in new_red.elements())
    if after_count-before_count:raise ValueError('PATCH_NEW_STATIC_RED')
    return {'path':name,'before_sha256':sha(raw),'after_sha256':sha(value_raw),'changes':changes,'data':value_raw}




prepare_file_task = types.FunctionType(_prepare_file_task_v0304.__code__, V300.__dict__, "prepare_file_task")
_ORIG = {k: getattr(V300, k) for k in ("prepare_file_task", "ENGINE_FILE", "__file__")}


def install() -> None:
    V300._v0304_exact_span = _v0304_exact_span
    V300._v0304_mcp_diagnostic = _v0304_mcp_diagnostic
    V300.prepare_file_task = prepare_file_task
    V300.ENGINE_FILE = Path(__file__).name
    V300.__file__ = str(Path(__file__).resolve())


def uninstall() -> None:
    for k, v in _ORIG.items():
        setattr(V300, k, v)


install()


def selftest() -> int:
    ok = []

    def chk(label, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + label + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 5 項 + 前版 {PRIOR_PATH.name} 自測 · 暫存資料 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路工具橋", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)
    cfg = {"fusion": {"mcp_modules": ["srv.py"]}, "workflow": {}}
    raw = "def f(x):\n    return x + 1  # keep this comment\n".encode()
    patch = [{"before_sha256": V300.sha(raw), "symbol": "f", "replacement_def": "def f(x: int):\n    return x + 1\n"}]
    try:
        _ORIG["prepare_file_task"](cfg, "m.py", raw, patch)
        old_err = "NO_ERROR"
    except ValueError as exc:
        old_err = str(exc)
    new = prepare_file_task(cfg, "m.py", raw, patch)
    out = new["data"].decode()
    chk("T2 (P2)結尾帶註解的函式:前版 PATCH_TOKEN_DRIFT;本版照補、註解原樣留著、可編譯",
        old_err == "PATCH_TOKEN_DRIFT" and "def f(x: int):" in out and "# keep this comment" in out and compile(out, "t", "exec") is not None,
        (old_err, out))
    mraw = ('import json\n\n\ndef send(r):\n    print(json.dumps(r), flush=True)\n\n\ndef log():\n    print("starting")\n').encode()
    old_m = _ORIG["prepare_file_task"](cfg, "srv.py", mraw, [])["data"].decode()
    res = prepare_file_task(cfg, "srv.py", mraw, [])
    new_m = res["data"].decode()
    kinds = [c["kind"] for c in res["changes"]]
    chk("T3 (P2)MCP:協定輸出 print(json.dumps(...)) 不動並列入待看;診斷字串照轉 stderr;前版兩個都轉",
        "print(json.dumps(r), flush=True)" in new_m and '_via_mcp_log("starting")' in new_m
        and "MCP_PRINT_LEFT_FOR_REVIEW" in kinds and "MCP_STDERR" in kinds
        and "_via_mcp_log(json.dumps(r), flush=True)" in old_m, (kinds, new_m[-160:]))
    chk("T4 v0300 其他函式呼叫到的是本版 prepare_file_task(綁 v0300 全域)· 子行程 / 綁定指本檔",
        V300.prepare_file_task is prepare_file_task and prepare_file_task.__globals__ is V300.__dict__
        and V300.ENGINE_FILE == Path(__file__).name and Path(V300.__file__).resolve() == Path(__file__).resolve())
    tree = ast.parse(src)
    chk("T5 本檔不用 eval / exec(語法樹)", not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in {"eval", "exec"}
                                            for n in ast.walk(tree)))
    uninstall()
    try:
        rc = PRIOR.selftest()
    finally:
        install()
    chk("T6 前版 v0303 自測照過(含 v0302 · v0301 · v0300 原有 107 項)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
