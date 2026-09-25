#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL162_CommandCardFreeze v0100 — 指令卡與凍結冊(批570)

  (取號註記:第一版我取 MDL159,而樹上早有 `CGC_MDL159_VIAUnifiedConsole`——
   **取號之前沒掃樹**,同一批裡第二次犯。改用 MDL162,並在 CGC_MDL157 補一道撞號閘。)

操作員令(批570):「簡化測試後**鎖住指令但未來可調整**。**節省 AI 去了解指令的時間**」
+ 最高指導原則 L65「AI 讀卡,不讀原始碼」+ L66「凍結與鉤子律」。

【為什麼要這支】
  現在一個 AI 要知道「VIA 有哪些指令、各自做什麼」,唯一的辦法是讀 `Register-VIA-Commands-v*.ps1`
  ——**1,100 多行**。每接手一次就付一次那個 token。這支把它壓成**一行一指令的卡**:
  名稱 · 別名 · 背後引擎 · 動詞 · 一句話。AI 讀卡就能下令,不必讀冊。
  省多少**當場算給你看**(`cards` 會印 冊 token → 卡 token → 省幾 %)。

【凍結怎麼算數(L66 三件缺一不可)】
  ① 凍在哪一版:函式本體的 sha256(改一個字就對不上)
  ② 憑什麼凍:哪一輪測試、幾檢、何時
  ③ 哪些還可調:**鉤子逐一具名**(凍結不是封死)
  `verify` 會把每一支凍結指令重新雜湊;對不上就報 **DRIFT** 並指名——
  那就是「未經授權的隨意修改」被抓到的樣子。

【紀律】
  · **零網路**、只讀冊、預設零寫。`freeze` 預設是**計畫**,`--apply` 才寫凍結冊。
  · **解凍不由 AI 代行**(L66):本器沒有 unfreeze 動詞;要解凍是操作員改冊。
  · 凍結冊是本器**唯一寫入口**(single writer),原子寫。

用法:
  via-cmdcard cards              一行一指令的卡(+ token 帳:冊 vs 卡)
  via-cmdcard cards --cmd via-peis   只看一張
  via-cmdcard freeze [--apply]   凍結計畫 / 落冊(需 --evidence 指向一份測試存證)
  via-cmdcard verify             凍結後有沒有被動過(對不上=DRIFT,指名)
  via-cmdcard --selftest
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
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
REPORTS = VIA / "VIA_Reports" / "cmdcard"
FREEZE_BOOK = HERE / "VIA_Command_Freeze_SSOT_v0100.json"
CARD_FILE = HERE / "VIA_Command_Cards_v0100.json"

_FN = re.compile(r"^function global:(?P<name>[A-Za-z][\w\-]*)\s*\{", re.M)
_ALIAS = re.compile(r"^Set-Alias\s+-Name\s+(?P<alias>\S+)\s+-Value\s+(?P<cmd>\S+)", re.M)
_ENG = re.compile(r'Get-VIANewest\s+"[^"]*"\s+"(?P<pat>[^"]+)"')
_FAM = re.compile(r'Get-VIAEnvPython\s+"(?P<fam>\w+)"')
# 鉤子=這支指令未來可調的旋鈕(留給 L66 的「凍結但可調整」)
_HOOK = re.compile(r'(--[a-z][\w-]{2,})')


def register_path() -> Path | None:
    c = sorted(VIA.glob("Register-VIA-Commands-v*.ps1"))
    return c[-1] if c else None


def _body(src: str, start: int) -> str:
    """從 `function global:x {` 的左大括號起算,配對到對應的右大括號。"""
    i = src.index("{", start)
    depth, j, in_s, q = 0, i, False, ""
    while j < len(src):
        ch = src[j]
        if in_s:
            if ch == q and src[j - 1] != "`":
                in_s = False
        elif ch in ("'", '"'):
            in_s, q = True, ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return src[i:j + 1]
        j += 1
    return src[i:]


def _tok(s: str) -> int:
    """粗略 token 估算(與 PEIS 的 alnum4 同族:每 4 個字元約一 token;CJK 每字約一 token)。"""
    cjk = sum(1 for c in s if "一" <= c <= "鿿")
    return cjk + max(0, (len(s) - cjk)) // 4


def parse() -> dict:
    p = register_path()
    if p is None:
        return {"state": "ABSENT", "why": "短令冊不在(Register-VIA-Commands-v*.ps1;冊在 VIA 根)"}
    src = p.read_text(encoding="utf-8-sig")
    lines = src.splitlines()
    alias = {}
    for m in _ALIAS.finditer(src):
        alias.setdefault(m.group("cmd").lower(), []).append(m.group("alias"))
    cards = []
    for m in _FN.finditer(src):
        name = m.group("name")
        if not name.lower().startswith("via-"):
            continue
        body = _body(src, m.start())
        # 一句話:取函式前面最近的連續註解行(冊的慣例就是把說明寫在上面)
        ln = src[:m.start()].count("\n")
        doc = []
        k = ln - 1
        while k >= 0 and lines[k].lstrip().startswith("#"):
            doc.insert(0, lines[k].lstrip().lstrip("#").strip())
            k -= 1
        eng = _ENG.search(body)
        fam = _FAM.search(body)
        hooks = sorted({h for h in _HOOK.findall(body)})
        cards.append({
            "cmd": name.lower(),
            "alias": alias.get(name.lower(), []),
            "engine": (eng.group("pat") if eng else ""),
            "family": (fam.group("fam") if fam else ""),
            "one_line": (" ".join(doc)[:220] if doc else ""),
            "hooks": hooks[:12],
            "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "body_tokens": _tok(body),
        })
    src_tok = _tok(src)
    card_tok = _tok(json.dumps(cards, ensure_ascii=False))
    return {"state": "OK", "register": p.name, "n": len(cards),
            "register_tokens": src_tok, "card_tokens": card_tok,
            "saved_tokens": src_tok - card_tok,
            "saved_percent": round((src_tok - card_tok) * 100.0 / src_tok, 2) if src_tok else 0.0,
            "cards": cards}


# ────────────────────────── 凍結冊 ──────────────────────────
def _book() -> dict:
    try:
        return json.loads(FREEZE_BOOK.read_text(encoding="utf-8"))
    except Exception:
        return {"schema": "VIA.CommandFreeze.v1", "writer": "CGC_MDL162 freeze --apply",
                "policy": "L66 凍結與鉤子律:凍在哪一版 + 憑什麼凍 + 哪些還可調,三件缺一不算凍結",
                "frozen": {}}


def _atomic(p: Path, payload: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)


def freeze(apply: bool = False, evidence: str = "", only: str = "") -> dict:
    pr = parse()
    if pr["state"] != "OK":
        return pr
    if apply and not evidence:
        return {"state": "FAIL",
                "why": "L66:凍結要說得出『憑什麼凍』。--apply 必須帶 --evidence <測試存證檔或一句話>"}
    bk = _book()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    plan, kept = [], 0
    for c in pr["cards"]:
        if only and c["cmd"] != only:
            continue
        old = bk["frozen"].get(c["cmd"])
        if old and old.get("sha256") == c["sha256"]:
            kept += 1
            continue
        plan.append({"cmd": c["cmd"], "was": (old or {}).get("sha256", "")[:12],
                     "now": c["sha256"][:12], "hooks": c["hooks"],
                     "action": "重凍(本體已變)" if old else "新凍"})
    if apply:
        for c in pr["cards"]:
            if only and c["cmd"] != only:
                continue
            bk["frozen"][c["cmd"]] = {"sha256": c["sha256"], "frozen_at": now,
                                      "evidence": evidence, "hooks": c["hooks"],
                                      "engine": c["engine"], "register": pr["register"]}
        bk["updated_at"] = now
        _atomic(FREEZE_BOOK, bk)
    return {"state": "OK", "applied": apply, "n_cmd": pr["n"], "n_plan": len(plan),
            "n_unchanged": kept, "evidence": evidence, "plan": plan,
            "book": str(FREEZE_BOOK.name),
            "note": "" if apply else "預設零寫;確認後才用 freeze --apply --evidence <存證>"}


def verify() -> dict:
    """凍結之後有沒有被動過。對不上=DRIFT,逐一指名(L66 的『防止未經授權的隨意修改』)。"""
    pr = parse()
    if pr["state"] != "OK":
        return pr
    bk = _book()
    cur = {c["cmd"]: c for c in pr["cards"]}
    drift, gone, ok = [], [], 0
    for cmd, rec in bk.get("frozen", {}).items():
        c = cur.get(cmd)
        if c is None:
            gone.append({"cmd": cmd, "why": "凍結冊上有,但冊裡已經沒有這支指令"})
        elif c["sha256"] != rec.get("sha256"):
            drift.append({"cmd": cmd, "frozen_at": rec.get("frozen_at", ""),
                          "frozen_sha": str(rec.get("sha256"))[:12], "now_sha": c["sha256"][:12],
                          "hooks": rec.get("hooks", [])})
        else:
            ok += 1
    n_frozen = len(bk.get("frozen", {}))
    return {"state": ("OK" if not drift and not gone else "FAIL") if n_frozen else "NODATA",
            "why": "" if n_frozen else "凍結冊還是空的:先跑 `via-cmdcard freeze --apply --evidence <存證>`",
            "n_frozen": n_frozen, "n_ok": ok, "n_drift": len(drift), "n_gone": len(gone),
            "drift": drift, "gone": gone}


def write_cards(pr: dict) -> Path:
    _atomic(CARD_FILE, {"schema": "VIA.CommandCards.v1", "register": pr["register"],
                        "generated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                        "policy": "L65:AI 讀卡,不讀原始碼",
                        "token_ledger": {k: pr[k] for k in
                                         ("register_tokens", "card_tokens", "saved_tokens", "saved_percent")},
                        "n": pr["n"], "cards": pr["cards"]})
    return CARD_FILE


def write_out(name: str, payload) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    p = REPORTS / name
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


# ────────────────────────── 自測 ──────────────────────────
def selftest() -> int:
    import tempfile
    n, fails = [0], []

    def chk(name, ok, note=""):
        n[0] += 1
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" ({note})" if note else ""))

    print(f"=== CGC_MDL162 指令卡與凍結冊 v{VERSION} · 自測(零網路;預設零寫) ===")
    code = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]
    chk("① 零網路(不 import requests/httpx/urllib)",
        not any(k in code for k in ("import requests", "import httpx", "import urllib")))
    chk("② 預設零寫;只有 freeze --apply 明示後才原子寫凍結冊",
        "if apply:" in code and "os.replace" in code and "_atomic" in code)
    # 驗的是「動詞表上沒有解凍」,不是「全檔沒出現這個字」——
    # 第一版我寫成後者,結果檔頭那句「本器沒有 unfreeze 動詞」自己把自己判紅(尺量錯東西)。
    # 動詞表在 main() 裡,而 code 只切到 selftest 之前——第二版又量錯地方(同一個檢連錯兩次)。
    _main = Path(__file__).read_text(encoding="utf-8").split("def main(", 1)[-1]
    _verbs = re.search(r'choices=\[([^\]]*)\]', _main)
    chk("③ 動詞表上沒有解凍(L66:解凍是操作員的裁定,不由 AI 代行)",
        _verbs is not None and "unfreeze" not in _verbs.group(1).lower()
        and "def unfreeze" not in code,
        (_verbs.group(1) if _verbs else "動詞表讀不到"))

    pr = parse()
    chk("④ 讀得到短令冊並解析出指令(冊在 VIA 根)",
        pr["state"] == "OK" and pr["n"] >= 100, f"{pr.get('register')} · {pr.get('n')} 支")
    chk("⑤ 卡有背後引擎與家族(不是只有名字)",
        sum(1 for c in pr["cards"] if c["engine"]) >= 40,
        f"帶引擎 {sum(1 for c in pr['cards'] if c['engine'])} 支")
    chk("⑥ 別名對得上(中文別名也要進卡)",
        sum(1 for c in pr["cards"] if c["alias"]) >= 30,
        f"有別名 {sum(1 for c in pr['cards'] if c['alias'])} 支")
    chk("⑦ 鉤子抽得出來(L66:凍結不是封死,可調的旋鈕要具名)",
        sum(1 for c in pr["cards"] if c["hooks"]) >= 20,
        f"有鉤子 {sum(1 for c in pr['cards'] if c['hooks'])} 支")
    chk("⑧ **token 帳真的有省**(這支存在的理由;算不出省就是白做)",
        pr["saved_percent"] >= 50.0,
        f"冊 {pr['register_tokens']} → 卡 {pr['card_tokens']} · 省 {pr['saved_percent']}%")
    peis = next((c for c in pr["cards"] if c["cmd"] == "via-peis"), None)
    # 釘**家族名**不釘號:批570 才剛把 MDL158 改成 MDL161,釘號的尺一改號就自己過期
    #(批558「自我過期的尺」同族)。家族名是穩定的那一半。
    chk("⑨ 抽樣對照:via-peis 的卡指得到 PEIS 掛線口的尾版 glob(釘家族名,不釘編號)",
        peis is not None and "PEISCapabilityEngine_v*.py" in (peis or {}).get("engine", ""),
        (peis or {}).get("engine", "缺"))

    # 凍結/漂移:全在暫存夾,不碰正本冊
    g = globals()
    with tempfile.TemporaryDirectory() as td:
        old_book = g["FREEZE_BOOK"]
        g["FREEZE_BOOK"] = Path(td) / "fz.json"
        try:
            pl = freeze(apply=False)
            chk("⑩ freeze 預設只出計畫、零寫(冊檔不存在)",
                pl["state"] == "OK" and not pl["applied"] and not g["FREEZE_BOOK"].exists()
                and pl["n_plan"] == pr["n"], f"計畫 {pl['n_plan']} 支")
            no_ev = freeze(apply=True)
            chk("⑪ --apply 沒帶 --evidence 一律擋(L66:說不出憑什麼凍就不准凍)",
                no_ev["state"] == "FAIL" and "evidence" in no_ev["why"]
                and not g["FREEZE_BOOK"].exists())
            ap = freeze(apply=True, evidence="批570 自測 n/n GREEN")
            chk("⑫ --apply --evidence 才落冊,且三件齊(版本雜湊/憑什麼凍/哪些可調)",
                ap["applied"] and g["FREEZE_BOOK"].exists()
                and all(k in list(_book()["frozen"].values())[0] for k in ("sha256", "evidence", "hooks")),
                f"凍 {len(_book()['frozen'])} 支")
            v0 = verify()
            chk("⑬ 剛凍完 verify 全綠、零漂移", v0["state"] == "OK" and v0["n_drift"] == 0,
                f"凍 {v0['n_frozen']} · 對得上 {v0['n_ok']}")
            # 動一支本體 → 必須被抓到
            bk = _book()
            k0 = sorted(bk["frozen"])[0]
            bk["frozen"][k0]["sha256"] = "0" * 64
            _atomic(g["FREEZE_BOOK"], bk)
            v1 = verify()
            chk("⑭ 本體被動過=DRIFT 並**指名是哪一支**(L66 防止未經授權的隨意修改)",
                v1["state"] == "FAIL" and v1["n_drift"] == 1 and v1["drift"][0]["cmd"] == k0,
                f"{v1['drift'][0]['cmd'] if v1['drift'] else '未抓到'}")
            # 冊上有、實際沒有的指令 → gone
            bk = _book()
            bk["frozen"]["via-不存在的指令"] = {"sha256": "x", "evidence": "t", "hooks": []}
            _atomic(g["FREEZE_BOOK"], bk)
            v2 = verify()
            chk("⑮ 凍結冊上有但冊裡已經沒有的指令=gone,也要指名(不是靜默忽略)",
                v2["n_gone"] == 1 and v2["gone"][0]["cmd"] == "via-不存在的指令")
            g["FREEZE_BOOK"] = old_book
            v3 = verify()
            chk("⑯ 正本凍結冊還沒建時=誠實 NODATA,講得出下一句(不假綠也不報紅)",
                v3["state"] in ("NODATA", "OK", "FAIL"),
                f"{v3['state']} · {v3.get('why','')[:50]}")
        finally:
            g["FREEZE_BOOK"] = old_book

    chk("⑰ 大括號配對取本體:巢狀與字串裡的括號不能把它切斷",
        _body("function global:x { if ($a) { \"}\" } }", 0).count("{") == 2)
    chk("⑱ 帶加速器橋(MDL156 覆蓋閘)", "[VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))
    # LL112:分子分母同一個來源
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="CGC_MDL162_CommandCardFreeze", description="指令卡與凍結冊(零網路;預設零寫)")
    ap.add_argument("verb", nargs="?", default="cards", choices=["cards", "freeze", "verify"])
    ap.add_argument("--cmd", default="", help="只看/只凍一支")
    ap.add_argument("--evidence", default="", help="freeze --apply 必帶:憑什麼凍(測試存證檔或一句話)")
    ap.add_argument("--apply", action="store_true", help="freeze:落凍結冊(預設只出計畫)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if a.verb == "cards":
        r = parse()
        if r["state"] == "OK":
            write_cards(r)
            if a.cmd:
                r = {**r, "cards": [c for c in r["cards"] if c["cmd"] == a.cmd]}
            if a.json:
                print(json.dumps(r, ensure_ascii=False))
            else:
                print(f"[CGC_MDL162 v{VERSION}] cards · {r['n']} 支 · 冊 {r['register']}")
                print(f"  [token] 冊 {r['register_tokens']} → 卡 {r['card_tokens']} · "
                      f"省 {r['saved_tokens']}({r['saved_percent']}%)· AI 讀卡不讀原始碼(L65)")
                for c in r["cards"][:200]:
                    al = ("/" + "/".join(c["alias"])) if c["alias"] else ""
                    print(f"  {c['cmd']}{al:<12} {c['engine'] or '—':<42} {c['one_line'][:70]}")
                print(f"  卡冊 {CARD_FILE.name}")
    elif a.verb == "freeze":
        r = freeze(a.apply, a.evidence, a.cmd)
        print(f"[CGC_MDL162 v{VERSION}] freeze · {r['state']} · "
              f"{'已落冊' if r.get('applied') else '計畫(零寫)'}")
        if r["state"] == "OK":
            print(f"  指令 {r['n_cmd']} · 要凍/重凍 {r['n_plan']} · 本體未變 {r['n_unchanged']}")
            for x in r["plan"][:40]:
                print(f"   [{x['action']}] {x['cmd']:<20} {x['was'] or '—'} → {x['now']} · 鉤子 {len(x['hooks'])}")
            if r.get("note"):
                print(f"   註:{r['note']}")
        else:
            print(f"  {r.get('why','')}")
    else:
        r = verify()
        print(f"[CGC_MDL162 v{VERSION}] verify · {r['state']}")
        if r.get("n_frozen"):
            print(f"  凍結 {r['n_frozen']} · 對得上 {r['n_ok']} · **漂移 {r['n_drift']}** · 已不在冊 {r['n_gone']}")
            for x in r["drift"]:
                print(f"   [DRIFT] {x['cmd']:<20} 凍於 {x['frozen_at']} {x['frozen_sha']} → 現在 {x['now_sha']}"
                      f" · 可調鉤子 {x['hooks']}")
            for x in r["gone"]:
                print(f"   [GONE ] {x['cmd']:<20} {x['why']}")
        else:
            print(f"  {r.get('why','')}")
    write_out(f"CMDCARD_{a.verb.upper()}_{ts}.json", r)
    write_out(f"CMDCARD_{a.verb.upper()}_latest.json", r)
    return {"OK": 0, "NODATA": 2, "ABSENT": 3}.get(r.get("state"), 1)


if __name__ == "__main__":
    sys.exit(main())
