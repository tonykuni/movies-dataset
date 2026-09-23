#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL180_FreezeSealAudit v0100 — 封章對帳閘(批709)

**改號實錄**:本支原編 `CGC_MDL178`,全格子當場報**新撞號**——
`CGC_MDL178_ToolInventoryRatchet` 早就佔著那個號。
`CGC_MDL157` 的「家族編號唯一(帶基線棘輪)」那一檢做對了:
**基線內的舊撞號照實背,基線外新增一個就是紅。** 改成 180(第一個空號)。
這是同一個星期內第二次撞號(批708 是跨分支撞 `_v0460`),兩次都不是自測抓到的。

**題目是怎麼冒出來的**:任務 #72「86 支受治理家族還沒人看」,我照真 import 邊排序,
排第一的是 `VIS_VRN_FinancialSSOT`(47 條邊)。要替它寫自測的時候先看檔,
看到它旁邊躺著一份 `.freeze.lock.json`,裡面寫 `freeze_status: FREEZE_OK` 和一個 sha256。

順手對了一下 —— **對不上**。再往外掃:

    全樹封章 102 份 · OK **0** · 剝掉批102 加速器橋後相符 1 · BROKEN 96 · 目標缺檔 5

**這不是有人竄改了 96 個檔。** 這是「封章從來沒有被驗過」:
`CGC_MDL059_MasterHub` 把「凍結件零觸碰(freeze.lock)」寫成一條政策字串,
但樹上**沒有任何一支程式去比對那個 sha256**。一份沒有人驗的封章,
守的東西早就不是它記的那一份 —— 它是裝飾品,不是閘。

**本閘只做一件事:把那個 sha256 真的算一次,然後照實報。**
不重新封章(那是操作員的裁定,不是我的);不改被封的檔一個位元組;只讀。

態(誠實多態,rc 照家規:0 綠 1 紅 2 NODATA 3 ABSENT):
    OK              算出來的 sha256 == 封章記的
    STALE_BRIDGE    剝掉 `[VIA:ACCEL-BRIDGE]` 區塊之後才相符 —— 封章是**注入前**算的
    BROKEN          兩種都對不上(可能是一連串沒有重新封章的正當修改,也可能不是;本閘不猜)
    TARGET_MISSING  封章指向一支不存在的檔(誠實 ABSENT,不當 OK 也不當 BROKEN)
    LOCK_UNREADABLE 封章自己壞了 / 沒有 sha256 欄

**棘輪(批708 LL387 同一式)**:現況 101 條非 OK 是**實跑量出來的基線**,照實報不算紅;
**基線外再冒出一支 BROKEN/TARGET_MISSING 就是 RED**。
既有債可以背,新增的債不可以悄悄地背。

用法:python3 CGC_MDL180_FreezeSealAudit_v0100.py [--json] | --selftest
律:零網路 · 零寫入(連被封的檔都不碰)· 不重新封章 · 不刪不搬 · 自己不封自己(LL133)。
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from pathlib import Path

ENGINE_ID = "CGC_MDL180_FreezeSealAudit"
VERSION = "v0100"
BATCH = "批709"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
_SELF_FAMILY = re.sub(r"_v\d{1,4}$", "", Path(__file__).stem)

BRIDGE_BEG = "# ===== [VIA:ACCEL-BRIDGE:v0100]"
BRIDGE_END = "# ===== [VIA:ACCEL-BRIDGE:END] =====\n"

#: L77 掃描根一律帶排除清單律:每一條寫得出為什麼,而且**逐條印出吃掉幾份**——
#:   過寬的排除要以數字現形,不是以沉默現形(批705 實錄:我自己寫過一條吃掉整個夾的)。
SEAL_EXCLUDE = [
    ("references/intake/", "收件正本:**零觸碰**,它就該跟外面不一樣"),
    ("__pycache__", "直譯器產物"),
    ("site-packages", "第三方套件"),
    (".venv", "虛擬環境"),
    ("/envs/", "家族環境"),
    ("node_modules", "前端套件"),
    (_SELF_FAMILY, "**本支自己**:封章閘不封自己(LL133)"),
]
#: 基線**不寫在這支 .py 裡**,放在隔壁的資料檔。
#:   批709 自審實錄:第一版我把 102 條路徑字面嵌進原始碼,其中幾條的**目標本身就是 .json 冊**,
#:   於是 `via_params_central` 的檢 ⑩(判準是「有沒有任何 .py 提到這本冊的檔名」)
#:   當場把那 3 本算成「有引擎在讀」,要求它們進參數名冊 —— 全格子多了一盞紅。
#:   **我不是在讀那些冊,我只是記了它們封章的路徑。**又是一次字面喊狼(LL389)。
#:   搬成資料檔之後:本支 .py 不再帶任何冊的檔名字面,而基線也回到它本來該在的地方(資料不是碼)。
BASELINE_FILE = HERE / "VIA_FreezeSealBaseline_v0100.json"


def _load_baseline() -> dict:
    """讀基線;讀不到就**誠實回空**並在跑的時候講出來——不自己編一份出來。"""
    try:
        return dict(json.loads(BASELINE_FILE.read_text(encoding="utf-8"))["baseline"])
    except Exception:
        return {}


SEAL_BASELINE = _load_baseline()


def _strip_bridge(text: str):
    """剝掉批102 全樹注入的 `[VIA:ACCEL-BRIDGE]` 區塊;沒有那個區塊就回 None。

    判準**窄**:必須同時找到起訖兩個標記才剝。寬一點就變成
    「剝到相符為止」——那是一道把 BROKEN 洗成 STALE 的後門,比不判更糟。
    """
    i = text.find(BRIDGE_BEG)
    if i < 0:
        return None
    j = text.find(BRIDGE_END, i)
    if j < 0:
        return None
    return text[:i] + text[j + len(BRIDGE_END):]


def locks(root: Path | None = None, exclude=None) -> list[Path]:
    """掃描面:**全樹 − 具名排除**(L77/LL363),不是手寫清單。"""
    root = root or VIA
    exc = SEAL_EXCLUDE if exclude is None else exclude
    out = []
    for p in sorted(root.rglob("*.freeze.lock.json")):
        s = str(p).replace("\\", "/")
        if any(f and f in s for f, _w in exc):
            continue
        out.append(p)
    return out


def eaten(root: Path | None = None, exclude=None) -> list[tuple]:
    """逐條排除吃掉幾份 —— 吃 0 份的是這棵樹上的死條文,照實報不報紅。"""
    root = root or VIA
    exc = SEAL_EXCLUDE if exclude is None else exclude
    allp = [str(p).replace("\\", "/") for p in root.rglob("*.freeze.lock.json")]
    return [(f, w, sum(1 for s in allp if f and f in s)) for f, w in exc]


def verify_one(lock: Path) -> dict:
    """一份封章 → 一個誠實態。**只讀**,連被封的檔都不碰一個位元組。"""
    rel = str(lock).replace("\\", "/").split("VeritasIntelligenceAnalytics/")[-1]
    try:
        L = json.loads(lock.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"lock": rel, "state": "LOCK_UNREADABLE", "why": f"{type(exc).__name__}: {exc}"}
    want = L.get("sha256")
    if not want:
        return {"lock": rel, "state": "LOCK_UNREADABLE", "why": "封章自己沒有 sha256 欄"}
    tgt = lock.parent / str(L.get("target_file") or "")
    if not L.get("target_file") or not tgt.exists():
        return {"lock": rel, "state": "TARGET_MISSING",
                "why": f"封章指向 {L.get('target_file')!r},樹上沒有這支檔"}
    raw = tgt.read_bytes()
    if hashlib.sha256(raw).hexdigest() == want:
        return {"lock": rel, "state": "OK", "why": ""}
    stripped = _strip_bridge(raw.decode("utf-8", errors="replace"))
    if stripped is not None and hashlib.sha256(stripped.encode("utf-8")).hexdigest() == want:
        return {"lock": rel, "state": "STALE_BRIDGE",
                "why": "剝掉批102 `[VIA:ACCEL-BRIDGE]` 區塊之後相符 —— 封章是**注入前**算的"}
    return {"lock": rel, "state": "BROKEN",
            "why": f"算出來 {hashlib.sha256(raw).hexdigest()[:16]}… · 封章記 {want[:16]}…"}


def ratchet(r: dict) -> dict:
    """基線內=既有債照實報;**基線外再冒出一支就是 RED**(批708 LL387 同一式)。

    為什麼不直接把 96 條 BROKEN 判紅:因為那 96 條**不是這一批弄壞的**,
    而且「要不要重新封章」是操作員的裁定(LL90)——我不代封。
    一道一上線就 96 盞紅燈的閘,跑三次就沒有人看它了(LL272 同族)。
    但**新的一支**必須當場叫,不然這一欄只會越長越長。
    """
    st = r.get("state")
    if st == "OK":
        return r                                  # OK 不受棘輪管轄:一個字都不准被改
    base = SEAL_BASELINE.get(r["lock"])
    if base == st:
        r["why"] = f"**既有債**({BATCH} 基線;重新封章待操作員裁定)· " + r["why"]
        return r
    r["newdebt"] = st
    r["state"] = "RED"
    r["why"] = (f"**基線外新增的 {st}**({BATCH} 棘輪;基線記的是 {base or '沒有這一條'})"
                f":既有債可以背,新增的債不可以悄悄地背。" + r["why"])
    return r


def run(root: Path | None = None, as_json: bool = False) -> int:
    rows = [ratchet(verify_one(p)) for p in locks(root)]
    tally: dict[str, int] = {}
    for r in rows:
        tally[r["state"]] = tally.get(r["state"], 0) + 1
    red = tally.get("RED", 0)
    if as_json:
        print(json.dumps({"engine": ENGINE_ID, "version": VERSION, "tally": tally,
                          "rows": rows}, ensure_ascii=False, indent=1))
        return 1 if red else 0
    print(f"=== 封章對帳閘 {VERSION}({BATCH})· 只讀 · 不重新封章 ===")
    if not SEAL_BASELINE:
        print(f"  [NODATA] 基線檔讀不到:{BASELINE_FILE.name} —— **棘輪這一輪沒有基準**,"
              f"下面每一條非 OK 都會判 RED。不自己編一份基線出來充數。")
    for f, w, n in eaten(root):
        print(f"  [排除] 吃 {n:3d} 份 · {f} —— {w}")
    for r in rows:
        if r["state"] != "OK":
            print(f"  [{r['state']:15s}] {r['lock']}\n        {r['why'][:150]}")
    print(f"[封章計] 共 {len(rows)} 份 · " +
          " · ".join(f"{k} {v}" for k, v in sorted(tally.items())) +
          f"(既有債基線 {len(SEAL_BASELINE)})")
    print("  註:BROKEN **不等於有人竄改**——多半是一連串沒有重新封章的正當修改;本閘不猜,只報對不對得上。")
    print("  註:重新封章是**操作員的裁定**(LL90),本閘不代封、不改被封的檔、不刪不搬。")
    return 1 if red else 0


def selftest() -> int:
    import tempfile
    ran: list[str] = []
    fails: list[str] = []

    def chk(name, cond, note=""):
        ran.append(name)
        ok = bool(cond)
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" ({note})" if note else ""))

    def mk(d: Path, body: str, sha: str | None = None, target: str | None = "t.py") -> Path:
        t = d / "t.py"
        t.write_text(body, encoding="utf-8")
        lk = d / "t.py.freeze.lock.json"
        pay = {"freeze_status": "FREEZE_OK"}
        if target is not None:
            pay["target_file"] = target
        if sha is not None:
            pay["sha256"] = sha
        lk.write_text(json.dumps(pay), encoding="utf-8")
        return lk

    print(f"=== 封章對帳閘 {VERSION} · 自測(沙盒 · 零網路 · 零寫入倉內)===")

    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        body = "print('x')\n"
        good = hashlib.sha256(body.encode()).hexdigest()

        # ── ② sha256 判準:正控 + 反面 ──────────────────────────────
        lk = mk(d, body, good)
        r_ok = verify_one(lk)
        lk2 = mk(d / "b", body + " \n", good) if (d / "b").mkdir() or True else None
        r_bad = verify_one(lk2)
        chk("② sha256 判準:**算出來的**要跟封章記的比。**正控**=乾淨的必須判 OK"
            "(一道永遠紅的閘跟永遠綠的一樣沒有判斷力);多一個位元組就要判 BROKEN",
            r_ok["state"] == "OK" and r_bad["state"] == "BROKEN",
            f"(乾淨 {r_ok['state']} · 多一個位元組 {r_bad['state']})")

        # ── ③ STALE_BRIDGE 判準窄 ────────────────────────────────
        (d / "c").mkdir()
        bridged = BRIDGE_BEG + " x =====\ntry:\n    pass\nexcept Exception:\n    pass\n" + BRIDGE_END + body
        lk3 = mk(d / "c", bridged, good)
        r_stale = verify_one(lk3)
        (d / "e").mkdir()
        lk5 = mk(d / "e", "print('x')\nprint('y')\n", good)      # 內容不符、**沒有橋標記**
        r_nobridge = verify_one(lk5)
        chk("③ **STALE_BRIDGE 判準窄**:只有剝掉 `[VIA:ACCEL-BRIDGE]` 起訖區塊後相符才算。"
            "寬一點就變成「剝到相符為止」——那是一道把 BROKEN 洗成 STALE 的後門。"
            "**負控**:內容不符又沒有橋標記的,必須照樣 BROKEN",
            r_stale["state"] == "STALE_BRIDGE" and r_nobridge["state"] == "BROKEN",
            f"(有橋 {r_stale['state']} · 無橋不符 {r_nobridge['state']})")

        # ── ④ 誠實態:目標缺檔 / 封章壞掉 ──────────────────────────
        (d / "f").mkdir()
        lk6 = mk(d / "f", body, good, target="nope.py")
        (d / "g").mkdir()
        lk7 = mk(d / "g", body, None)                            # 沒有 sha256 欄
        (d / "h").mkdir()
        (d / "h" / "t.py").write_text(body, encoding="utf-8")
        (d / "h" / "t.py.freeze.lock.json").write_text("{ not json", encoding="utf-8")
        r_miss, r_nohash, r_bad_lock = verify_one(lk6), verify_one(lk7), verify_one(d / "h" / "t.py.freeze.lock.json")
        chk("④ 誠實態:封章指向不存在的檔=**TARGET_MISSING**(不當 OK 也不當 BROKEN——"
            "那支檔可能只是還沒進倉);封章自己沒有 sha256 或讀不動=**LOCK_UNREADABLE**",
            r_miss["state"] == "TARGET_MISSING" and r_nohash["state"] == "LOCK_UNREADABLE"
            and r_bad_lock["state"] == "LOCK_UNREADABLE",
            f"({r_miss['state']} · {r_nohash['state']} · {r_bad_lock['state']})")

        # ── ⑤ 棘輪 + 負控 ────────────────────────────────────────
        key_in = next(iter(SEAL_BASELINE))
        r_in = ratchet({"lock": key_in, "state": SEAL_BASELINE[key_in], "why": ""})
        r_new = ratchet({"lock": "沒有這一條/x.freeze.lock.json", "state": "BROKEN", "why": ""})
        r_okk = ratchet({"lock": key_in, "state": "OK", "why": ""})
        r_flip = ratchet({"lock": key_in, "state": "TARGET_MISSING", "why": ""})
        chk("⑤ **棘輪**:基線內照實報不算紅;**基線外再冒出一支就是 RED**;"
            "同一條**態變了**(BROKEN→TARGET_MISSING)也算新的債。"
            "**負控**:OK 不在棘輪管轄內,一個字都不准被改",
            r_in["state"] == SEAL_BASELINE[key_in] and r_new["state"] == "RED"
            and r_okk["state"] == "OK" and not r_okk["why"] and r_flip["state"] == "RED",
            f"(基線內 {r_in['state']} · 基線外 {r_new['state']} · 態變了 {r_flip['state']} · OK {r_okk['state']})")

        # ── ① 掃描面 + 負控 ──────────────────────────────────────
        base_n = len(locks())
        narrowed = len(locks(exclude=SEAL_EXCLUDE + [("70_VRN_Rules", "負控:故意吃掉整個夾")]))
        no_why = [f for f, w in SEAL_EXCLUDE if not w]
        chk("① 掃描面=**全樹 − 具名排除**(L77),不是手寫清單;每條排除寫得出為什麼、"
            "而且逐條印出吃掉幾份 —— 過寬的排除以數字現形,不是以沉默現形。"
            "**負控**:注入一條吃掉整個 `70_VRN_Rules` 的排除,份數必須當場掉下來",
            base_n > 0 and narrowed < base_n and not no_why,
            f"(掃到 {base_n} 份 · 負控後 {narrowed} 份(必須更少)· 因由留空 {no_why or '無'})")

        # ── ⑥ 基線是實跑量出來的 ─────────────────────────────────
        live = {str(p).replace("\\", "/").split("VeritasIntelligenceAnalytics/")[-1] for p in locks()}
        ghost = sorted(set(SEAL_BASELINE) - live)
        chk("⑥ 基線**每一條都要在掃描面上**,而且**基線不可以是空的**:"
            "列一條樹上沒有的,等於發一張永遠用不到的免死金牌;"
            "而基線檔讀不到時如果悄悄退成空字典,這條檢會**空轉著過**"
            "(0 條都在掃描面上=真)——那才是最難發現的假綠。**負控**:餵一份空基線必須當場破",
            not ghost and len(SEAL_BASELINE) > 0 and BASELINE_FILE.exists(),
            f"(基線 {len(SEAL_BASELINE)} 條 · 基線檔在位 {BASELINE_FILE.exists()} · 不在掃描面的 {ghost[:3] or '無'})")

        # ── ⑦ 零寫入 ────────────────────────────────────────────
        src = Path(__file__).read_text(encoding="utf-8")
        code = "\n".join(ln for ln in src.split("\n") if not ln.lstrip().startswith("#"))
        tree = ast.parse(src)
        in_selftest = {n.lineno for f in ast.walk(tree)
                       if isinstance(f, ast.FunctionDef) and f.name == "selftest"
                       for n in ast.walk(f) if hasattr(n, "lineno")}
        banned = ("write_" + "text", "write_" + "bytes", "un" + "link", "rm" + "tree", "sh" + "util")
        # LL384:字面禁用檢要先剝掉註解;而且**自測自己造沙盒檔是許的**,所以只看自測以外的行。
        hits = []
        for i, ln in enumerate(src.split("\n"), 1):
            if ln.lstrip().startswith("#") or i in in_selftest:
                continue
            hits += [b for b in banned if b in ln]
        chk("⑦ **零寫入**:本閘只讀 —— 被封的檔一個位元組都不碰,也不重新封章。"
            "逐行掃**會執行的碼**(剝掉註解;自測自己造沙盒檔是許的,所以只看自測以外)",
            not hits, f"(自測以外的寫檔/刪檔動詞 {sorted(set(hits)) or '無'})")

    print(f"  [計] {len(ran)} 檢 OK {len(ran) - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a or "--self-test" in a:
        return selftest()
    return run(as_json="--json" in a)


if __name__ == "__main__":
    sys.exit(main())
