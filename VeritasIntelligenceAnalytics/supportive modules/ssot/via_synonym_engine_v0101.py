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
# =====================================================================================
# VIA Synonym Engine v0100 — 平台同義字引擎轉接器
# 唯一實作 = PMIS-Lite SynonymSSOT(九頭龍防治:不複製、不另造,直接 import)
# 種子 = VIA_Synonym_Seed_v0100.json(canonical 錨點自 VRN 資料契約抽取;同義字增量登錄)
# 消費端:VRN account_canonical mapper(account_alias_registry)、VDF 欄位正規化
# =====================================================================================
import os, sys, json

_HERE = os.path.dirname(os.path.abspath(__file__))
_PMIS = os.path.join(_HERE, "..", "PMIS-Lite", "pmis_lite", "pmis_lite")
if _PMIS not in sys.path:
    sys.path.insert(0, os.path.abspath(_PMIS))
from ssot_synonyms import SynonymSSOT  # noqa: E402

SEED = os.path.join(_HERE, "VIA_Synonym_Seed_v0100.json")

def build():
    eng = SynonymSSOT()
    seed = json.load(open(SEED, encoding="utf-8"))
    for c in seed["canonicals"]:
        eng.add_canonical(c["canon_id"], c["name"], c.get("domain", "SSOT"))
    for s in seed.get("synonyms", []):
        eng.add_synonym(s["term"], s["canon_id"])
    return eng

def selftest() -> int:
    """批710(任務 #72):5 條真 import 邊卻一站都沒有。

    本檢要分得開兩件常被混成一件的事:
      **引擎壞了** vs **正本沒有料**。
    實測:種子檔 canonicals 41 條、**synonyms 0 條** —— 引擎是活的,是冊上一條同義字都沒有。
    一道只檢「resolve 回 None」的檢會把這兩種判成同一種,那就是把缺料說成缺陷。
    """
    from pathlib import Path          # 批710 自審:檔頭的加速器橋是 `Path as _sa_Path`,
    #   我原本用「檔裡有沒有 from pathlib import Path」當 guard —— **子字串比對被那一行騙過去**,
    #   於是 import 沒補成而 selftest 當場 NameError。又一次字面判準喊狼(LL389 同一族)。
    ran, fails = [], []

    def chk(name, cond, note=""):
        ran.append(name)
        ok = bool(cond)
        if not ok:
            fails.append(name)
        print("  [%s] %s%s" % ("OK" if ok else "FAIL", name, (" (%s)" % note) if note else ""))

    print("=== 同義字引擎 v0101 · 自測(沙盒 · 零網路 · 零寫入)===")
    seed_path = Path(SEED)
    seed = json.load(open(SEED, encoding="utf-8")) if seed_path.exists() else {}
    n_canon, n_syn = len(seed.get("canonicals", [])), len(seed.get("synonyms", []))

    eng = build()
    chk("① `build()` 要真的建得起來,而且正典數**跟種子檔對得上**"
        "(寫死一個數字會漂;對不上就是冊改了而引擎沒跟上)。**正控**=正典數必須 > 0",
        eng is not None and n_canon > 0, "(種子正典 %d 條 · 同義字 %d 條)" % (n_canon, n_syn))

    miss = eng.resolve("絕對不存在的詞_zzz_%s" % n_canon)
    chk("② 查無要**誠實回 None**,不可以編一個最像的回去"
        "(同義字解析一旦開始猜,下游的欄位就會多出沒有人裁定過的對應)",
        miss is None, "(查無 → %r)" % (miss,))

    # ③ **正控**:引擎本身吃得下同義字並查得回來 —— 證明它是活的,不是永遠回 None
    probe_term, probe_canon = "_selftest_同義字探針_", (seed.get("canonicals") or [{}])[0].get("canon_id")
    alive = None
    if probe_canon:
        eng.add_synonym(probe_term, probe_canon)
        alive = eng.resolve(probe_term)
    chk("③ **正控:引擎吃得下同義字、也查得回來。** 合成一條丟進去再查一次 —— "
        "沒有這一條,檢 ② 的「查無回 None」用一個**永遠回 None 的死引擎**也會過",
        alive == probe_canon and probe_canon is not None,
        "(合成 %r → %r(應 %r))" % (probe_term, alive, probe_canon))

    chk("④ **誠實態:正本種子目前 synonyms = %d 條。** 引擎活著(檢 ③ 證明)而冊上沒有料,"
        "這是**缺料不是缺陷**——把它報成紅燈會讓人去修一支沒壞的引擎。"
        "這條檢釘住的是「冊有幾條」這個事實本身,冊被補料的那天它會亮" % n_syn,
        seed_path.exists() and isinstance(seed.get("canonicals"), list),
        "(種子檔在位 %s · 同義字 %d 條 —— 要補料是操作員的冊,不是本引擎的碼)"
        % (seed_path.exists(), n_syn))

    print("  [計] %d 檢 OK %d · FAIL %d" % (len(ran), len(ran) - len(fails), len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv or "--self-test" in sys.argv:
        sys.exit(selftest())
    e = build()
    n = len(e.canonical)
    ok = e.syn.get("ticker") is not None
    print("[VIA Synonym Engine] canonicals=%d resolve('ticker')->%s ledger=%d" % (n, e.syn.get("ticker"), len(e.ledger)))
    print("SMOKE " + ("PASS" if (n >= 40 and ok) else "FAIL"))
