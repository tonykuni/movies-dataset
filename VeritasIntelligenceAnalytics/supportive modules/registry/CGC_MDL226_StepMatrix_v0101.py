#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL226_StepMatrix v0101 — 薄尾:省 Token 工具是 VCGC 第一步 · 經 VCGC 啟用(鎖版)· 實測可用 · 要求 AI 先用

操作員 2026-09-29:「token saving tools registered. activate them and request ai to utilize them as the first step in vcgc.」
v0100 的省 Token 排第二步,而且只「嗅」全景檔裡有沒有 "read" 這幾個字——字在 ≠ 工具能用,也沒有一句話叫 AI 先用。本尾版:
  ① 次序:1 token → 2 enter → 3 accel_net → 4 policy → … → 8 subsystem。一步不刪,只把 token 提到最前;
     via-vcgc 這扇門仍在所有步之前擋直呼(門不是步,步是進門之後做的事)。前三步照舊不開子系統檔。
  ② 啟用 = 鎖冊說了算:全景取 CGC_MDL233 pinned('token')、NLP 取 pinned('nlp'),位元要等於鎖上的 sha
     (CRLF 工作複本照 CGC_MDL225 v0102 容忍);沒啟用 / 被改過 = 紅,卡上印啟用短令。
  ③ 實測:對鎖上的那一支真的跑 read · slice · digest · pack · read --if-etag(要回 304)· NLP text --brief,
     各認一個判讀記號(樣本在暫存夾,零寫樹)。同一組位元(兩支鎖檔 + 全景本體 + 本檔的 sha)只測一次,
     結果快取在 VIA_Reports/vcgc/token_activation_latest.json;沒過的不快取,下一次照測。
  ④ 要求 AI 先用:卡上 ai_directive(第一步做什麼 · 指令原樣可貼 · 什麼時候不用);ai_line 是 VCGC 每個動作第一行印的短版。
  ⑤ 政策小冊 VIA_Policy_TokenFirst_v0100.json(TOKEN-1;不改鎖住的法冊)寫著同一個次序與六件工具;自測 ⑩ 核對兩邊一字不差。
其餘照 v0100(thin tail;__getattr__ 轉接 accel_net / subsystem_sync / write_page)。零網路 · 不安裝 · 不寫冊。
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

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL226_StepMatrix"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

VIA = PRIOR.VIA
REPO = VIA.parent
TOKEN_TOOLS = PRIOR.TOKEN_TOOLS
CACHE = VIA / "VIA_Reports" / "vcgc" / "token_activation_latest.json"
ACTIVATE_STEM = "CGC_MDL233_ToolActivate"
_ZH = {"token": "省 Token 工具:經 VCGC 啟用(鎖版)· 實測 · AI 先用"}
_V0100_ORDER = tuple(PRIOR.ORDER)     # 改次序之前的原樣(自測拿它比「一步不少」)
ORDER = tuple((i + 1, name, "first" if name == "token" else when, _ZH.get(name, zh))
              for i, (_s, name, when, zh) in enumerate(sorted(_V0100_ORDER, key=lambda r: (r[1] != "token", r[0]))))
LAST: dict = {}


def __getattr__(name: str):
    return getattr(PRIOR, name)


def _activator():
    """工具啟用閘尾版(pinned 的唯一答案;L05 一把尺)。不在回 None。"""
    hits = sorted(HERE.glob(ACTIVATE_STEM + "_v*.py"), key=_vnum)
    if not hits:
        return None
    name = "tool_activate_for_" + Path(__file__).stem
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, hits[-1])
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


def _sha_ok(path: Path | None, want: str | None) -> bool:
    if path is None or not want or not path.is_file():
        return False
    raw = path.read_bytes()
    return want in (hashlib.sha256(raw).hexdigest(), hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest())


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO).as_posix()
    except ValueError:
        return str(path)


def _key(files: list) -> str:
    h = hashlib.sha256()
    for f in files:
        h.update(f.name.encode("utf-8") + b"\0" + (f.read_bytes() if f and f.is_file() else b"-") + b"\0")
    return h.hexdigest()[:24]


def _smoke(pano: Path | None, nlp: Path | None) -> dict:
    """對鎖上的那一支真的跑六件;回 {工具: bool}。樣本在暫存夾,零寫樹。"""
    res = {name: False for name in TOKEN_TOOLS}
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "s.py").write_text('def alpha(x):\n    """first."""\n    return x + 1\n\n\ndef beta():\n    return alpha(1)\n',
                                encoding="utf-8")
        (d / "t.log").write_text("  [OK] ① a\n  [FAIL] ② b\n  [計] 2 檢 OK 1 · FAIL 1\n", encoding="utf-8")
        (d / "n.txt").write_text("台積電第三季營收成長 12%,毛利率 58%,優於市場預期。\n管理層上調全年資本支出。\n", encoding="utf-8")

        def run(args, timeout=120):
            env = dict(os.environ, VIA_FROM_VCGC="YES", PYTHONIOENCODING="utf-8")
            try:
                p = subprocess.run([sys.executable, *args], cwd=str(d), capture_output=True, timeout=timeout, env=env)
                return p.returncode, (p.stdout + p.stderr).decode("utf-8", errors="replace")
            except Exception as exc:                       # 逾時 / 起不來 = 這一件不能用(不是通過)
                return 127, f"{type(exc).__name__}: {exc}"

        if pano is not None:
            rc, out = run([str(pano), "read", "s.py"])
            res["read"] = rc == 0 and "[token 帳]" in out and "def beta" in out
            m = re.search(r"etag=([0-9a-f]{8,})", out)
            rc, out = run([str(pano), "read", "s.py", "--if-etag", m.group(1)]) if m else (1, "")
            res["etag"] = rc == 0 and "304" in out
            rc, out = run([str(pano), "slice", "s.py", "beta"])
            res["slice"] = rc == 0 and "return alpha(1)" in out and "def alpha" not in out
            rc, out = run([str(pano), "digest", "t.log"])
            res["digest"] = rc in (0, 1) and "[摘] RED" in out and "[真 FAIL] ② b" in out   # 紅日誌誠實回 rc1
            rc, out = run([str(pano), "pack", "."])
            res["pack"] = rc == 0 and "省Token 索引" in out
        if nlp is not None:
            rc, out = run([str(nlp), "text", "--file", "n.txt", "--brief"], timeout=240)
            res["brief"] = rc == 0 and '"state"' in out
    return res


def _directive(pano: Path, nlp: Path, n_ok: int) -> list:
    p, n = _rel(pano), _rel(nlp)
    return [
        f"[AI 第一步 · 省 Token(L65;操作員 2026-09-29 令)] 已啟用 {n_ok}/{len(TOKEN_TOOLS)} · 全景 {pano.name} · NLP {nlp.name} · 從倉根照貼:",
        f'  大檔(約 >200 行)或整夾 → python3 "{p}" read <檔或夾>        骨架卡,不整檔讀',
        f'  要看某段內文           → python3 "{p}" slice <檔> <定義名>     一次一個定義',
        f'  跑測日誌               → python3 "{p}" digest <日誌>           只留判決行',
        "  同一支再讀             → 原指令加 --if-etag <上一張卡的 etag>  回 304 = 沒變,沿用上一張卡",
        f'  整夾索引               → python3 "{p}" pack <夾>',
        f'  長文摘要               → VIA_FROM_VCGC=YES python3 "{n}" text --file <檔> --brief',
        "  不用的時候:原檔比卡片小(約 40 行內)直接看;不把原文貼回對話;先卡、再切片,最後才整檔(L65 ①)",
    ]


def token_tools(act=None, cache: Path | None = None) -> dict:
    """第一步:鎖上的省 Token 工具有沒有啟用、能不能用;順手產出給 AI 的指令卡。"""
    act = act if act is not None else _activator()
    cache = cache or CACHE
    pano = act.pinned("token") if act else None
    nlp = act.pinned("nlp") if act else None
    lock = (act._json(act.lock_path()) if act else {}) or {}
    activated = {"token": _sha_ok(pano, (lock.get("token") or {}).get("sha256")),
                 "nlp": _sha_ok(nlp, (lock.get("nlp") or {}).get("sha256"))}
    hint = []
    if not activated["token"]:
        tail = sorted(HERE.glob("CGC_MDL158_VIAPanoramaAuditRepair_v*.py"), key=_vnum)
        hint.append(("via-vcgc tools activate token " + (tail[-1].name if tail else "<CGC_MDL158_…_vNNNN.py>") + " --apply")
                    + ("(鎖上的那支位元被改過)" if pano is not None else ""))
    if not activated["nlp"]:
        hint.append("via-vcgc tools activate nlp <SUP_MDL866_…_vNNNN.py> --apply")
    smoke = {"cached": False, "key": "", "at": "", "secs": 0.0}
    res = {name: False for name in TOKEN_TOOLS}
    if activated["token"] and activated["nlp"]:
        body = act._body_of(pano) if hasattr(act, "_body_of") else pano
        key = _key([pano, body, nlp, Path(__file__)])
        prev = {}
        try:
            prev = json.loads(cache.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        if prev.get("key") == key and all(prev.get("tools", {}).get(n) for n in TOKEN_TOOLS):
            res, smoke = dict(prev["tools"]), {"cached": True, "key": key, "at": prev.get("at", ""), "secs": 0.0}
        else:
            t0 = time.time()
            res = _smoke(pano, nlp)
            smoke = {"cached": False, "key": key, "at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                     "secs": round(time.time() - t0, 1)}
            if all(res.values()):                         # 沒過的不快取:下一次照測
                try:
                    cache.parent.mkdir(parents=True, exist_ok=True)
                    cache.write_text(json.dumps({"key": key, "at": smoke["at"], "tools": res,
                                                 "panorama": _rel(pano), "nlp": _rel(nlp)},
                                                ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
                except OSError:
                    pass
    missing = [name for name in TOKEN_TOOLS if not res.get(name)]
    n_ok = len(TOKEN_TOOLS) - len(missing)
    if not missing:
        directive = _directive(pano, nlp, n_ok)
        line = (f"[第一步 · 省Token] 已啟用 {n_ok}/{len(TOKEN_TOOLS)}(鎖版 {pano.stem[-5:]} · NLP {nlp.stem[-5:]})"
                "· AI 先用:read → slice → digest · --if-etag 免重讀 · pack 整夾 · --brief 長文(via-vcgc token 看整張卡)")
    else:
        directive = [f"[AI 第一步 · 省 Token] 紅:{', '.join(missing)} 不能用——先修這一步,不讀政策、不開子系統"] + [
            "  " + h for h in hint]
        line = f"[第一步 · 省Token] 紅 {n_ok}/{len(TOKEN_TOOLS)} · 不能用:{', '.join(missing)} · " + ("; ".join(hint) or "見 via-vcgc token")
    return {
        "panorama": pano.name if pano else "",
        "nlp": nlp.name if nlp else "",
        "pinned": {"token": _rel(pano) if pano else "", "nlp": _rel(nlp) if nlp else ""},
        "activated": activated,
        "tools": res,
        "missing": missing,
        "smoke": smoke,
        "activate_hint": hint,
        "ai_directive": directive,
        "ai_line": line,
    }


PRIOR.ORDER = ORDER                   # 前一版的 front() 照新次序排列
PRIOR.token_tools = token_tools       # 前一版的 front() 第一步改問啟用與實測(不再嗅字串)


def front() -> dict:
    """第一步到第三步。子系統冊照舊不開。"""
    card = PRIOR.front()
    tok = card["token"]
    card.update({
        "door": Path(__file__).stem,
        "ai_directive": tok["ai_directive"],
        "ai_line": tok["ai_line"],
        "activate_hint": tok["activate_hint"],
        "do_not": list(card["do_not"]) + ["read a large file whole before step 1's read / slice"],
    })
    if tok["missing"]:
        card["next"] = "; ".join(tok["activate_hint"]) or "fix step 1 (token tools) before policy"
    LAST.clear()
    LAST.update(card)
    return card


def step_line(card: dict | None = None) -> str:
    rows = {r["id"]: r["lamp"] for r in (card or LAST).get("rows", [])}
    return (f"[步驟] 1 省Token {rows.get('token', '?')} · 2 入口 {rows.get('enter', '?')} · "
            f"3 加速器與網路 {rows.get('accel_net', '?')} · 政策與子系統在後")


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    card = front()
    PRIOR.write_page(card)
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["front_pass"] else 2


def selftest() -> int:
    global CACHE
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    real_cache = CACHE
    before = real_cache.read_bytes() if real_cache.is_file() else None
    act = _activator()
    lock_p = act.lock_path() if act else None
    lock_before = lock_p.read_bytes() if lock_p and lock_p.is_file() else None
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    chk("① 門:沒經 via-vcgc(沒有 VIA_FROM_VCGC)直呼 → DENY rc2", denied)
    ids, prev_ids = [r[1] for r in ORDER], [r[1] for r in _V0100_ORDER]
    chk("② 次序:第一步是 token;v0100 的八步一步不少、步號 1..8 連續;前三步不開子系統",
        ids[0] == "token" and sorted(ids) == sorted(prev_ids) and [r[0] for r in ORDER] == list(range(1, len(ORDER) + 1))
        and ids[1:3] == ["enter", "accel_net"], " → ".join(ids))
    try:
        with tempfile.TemporaryDirectory() as td:
            CACHE = Path(td) / "token_activation_latest.json"
            t0 = time.time()
            card = front()
            t1 = time.time() - t0
            tok = card["token"]
            t0 = time.time()
            card2 = front()
            t2 = time.time() - t0
            chk("③ 啟用:鎖冊 token(全景)與 nlp 都指到檔、位元吻合", tok["activated"] == {"token": True, "nlp": True},
                f"{tok['panorama'] or '-'} · {tok['nlp'] or '-'}")
            chk("④ 實測六件全過(read · slice · digest · pack · --if-etag 304 · NLP --brief)→ 第一步 GREEN、前三步放行",
                not tok["missing"] and card["front_pass"] and card["rows"][0]["id"] == "token"
                and card["rows"][0]["lamp"] == "GREEN" and card["opened_subsystem"] is False,
                " ".join(f"{k}={'✓' if v else '✗'}" for k, v in tok["tools"].items()) + f" · {t1:.1f}s")
            data = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.is_file() else {}
            data["key"] = "stale"
            CACHE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            card3 = front()
            chk("⑤ 快取:同一組位元第二次不重測(cached)· 位元組鍵一換就重測",
                card2["token"]["smoke"]["cached"] and t2 < t1 and not card3["token"]["smoke"]["cached"]
                and not card3["token"]["missing"], f"首測 {t1:.1f}s · 快取 {t2:.2f}s")
            text = "\n".join(card["ai_directive"])
            chk("⑥ AI 指令卡:鎖上的全景 / NLP 路徑原樣可貼 · 六個動詞 · 什麼時候不用;ai_line 以「[第一步 · 省Token]」開頭",
                tok["pinned"]["token"] in text and tok["pinned"]["nlp"] in text
                and all(v in text for v in (" read ", " slice ", " digest ", "--if-etag", " pack ", "--brief", "不用的時候"))
                and card["ai_line"].startswith("[第一步 · 省Token] 已啟用 6/6") and step_line(card).startswith("[步驟] 1 省Token GREEN"))
            none = SimpleNamespace(pinned=lambda fam, root=None: None, lock_path=lambda root=None: None, _json=lambda p: {})
            neg = token_tools(act=none, cache=CACHE)
            chk("⑦ 負控 沒啟用(鎖冊沒有 token / nlp):第一步紅、六件全列不能用、卡上印 via-vcgc tools activate token … --apply",
                neg["missing"] == list(TOKEN_TOOLS) and any("tools activate token" in h for h in neg["activate_hint"])
                and neg["ai_line"].startswith("[第一步 · 省Token] 紅"))
            fake = Path(td) / "CGC_MDL158_VIAPanoramaAuditRepair_v9999.py"
            fake.write_text("print('')\n", encoding="utf-8")
            bad = _smoke(fake, None)
            tamper = Path(td) / "copy.py"
            tamper.write_bytes((act.pinned("token") or fake).read_bytes() + b"\n# x\n")
            chk("⑧ 負控 工具壞 / 鎖檔被改:只印空行的假全景六件全 ✗;多一個位元的檔 sha 對不上 = 沒啟用",
                not any(bad.values()) and not _sha_ok(tamper, (act._json(act.lock_path()).get("token") or {}).get("sha256")))
    finally:
        CACHE = real_cache
    pol = {}
    try:
        pol = json.loads((HERE / "VIA_Policy_TokenFirst_v0100.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    chk("⑩ 政策小冊 TOKEN-1 與本矩陣一字不差:次序 · 六件工具 · ACTIVE · 法冊沒被改寫(book_edited=false)",
        pol.get("id") == "TOKEN-1" and pol.get("status") == "ACTIVE" and pol.get("order") == [r[1] for r in ORDER]
        and pol.get("tools") == list(TOKEN_TOOLS) and pol.get("book_edited") is False,
        f"冊 {pol.get('order', '讀不到')}")
    after = real_cache.read_bytes() if real_cache.is_file() else None
    lock_after = lock_p.read_bytes() if lock_p and lock_p.is_file() else None
    chk("⑨ 零足跡:真快取檔、真鎖冊一個位元不動(自測的快取落暫存夾)", after == before and lock_after == lock_before)
    ok = all(results)
    print(f"  {Path(__file__).stem} selftest {sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
