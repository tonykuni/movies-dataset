# -*- coding: utf-8 -*-
r"""VDF 審計閘 v0100(批610)— 「VDF 通過審計且跑得起來」這句話,做成一支可重跑的引擎。

操作員令(批610):「vdf pass audit and run perfectly」。
在此之前 VDF 的「跑得起來」只存在於我一次性的便條腳本裡 —— 便條會過期,引擎不會。

它做三件事,一件都不許用猜的:
  ① 列冊    尾版律列出 VDF 活樹該審的 .py(L77 排除清單 + 本檔審計豁免冊,豁免必附理由)
  ② 逐支跑  每支 `--selftest`(L53 全樹契約),平行跑;rc 誠實多態,不吃掉任何原因行
  ③ 複判    平行段判敗的,**逐支序跑再判一次**——鎖撞造成的紅是假紅(批610 實測:我自己的
            便條尺一開始 6 路平行跑,DuckDB 鎖撞讓 ENG060/ENG062/ENG072 三支全紅;
            單獨跑三支全是綠/NODATA。**壞的是尺,不是引擎。**)

rc 誠實多態:0=GREEN · 1=RED(有真紅或有未豁免的缺動詞) · 2=NODATA(只有缺料/缺套件)

動詞:
  --audit              審計(預設);--workers N / --timeout S / --root PATH / --json PATH
  --selftest           自測(零連線、零寫樹;只在暫存夾裡合成假樹)
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except Exception:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(本閘零連線,橋只為全樹契約齊備) =====
VIA_NET_TOOL_PATH = None


def _via_net():
    """本閘**零連線**:本函式永遠回 None,存在只為讓網路橋契約檢查通過。"""
    return None
# ===== [VIA:NET-BRIDGE:END] =====

import argparse
import concurrent.futures as _cf
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

VERSION = Path(__file__).stem.split("_v")[-1]

# ── L77 掃描根排除清單(退役件/收容正本/凍結快照/第三方樹,一律不入審) ─────────────
EXCLUDE_PARTS = (
    "references/intake",        # 收容正本零觸碰
    "_superseded",              # 退役件不是活樹
    "_rebuilds_superseded",
    "RetiredEngines",
    "_backup",
    "SCOPE_COPY",
    "__pycache__",
    "node_modules",
    "site-packages",
)
EXCLUDE_NAME = ("_sha",)        # 凍結快照:改了 sha 就對不上

# ── 審計豁免冊:豁免一定要有理由,沒理由的豁免等於假綠 ───────────────────────────
AUDIT_EXEMPT = (
    ("/_from_vap_iso_cleanup/",
     "VAP 隔離清理殘件:非活樹,留作回溯;正本在 VDF 根與 engine/"),
    ("/macro_manifest_fetch_runs/",
     "跑次產物快照(RUN_* 夾):那是一次跑留下的輸出,不是活引擎"),
    ("/engine/candidates/",
     "候選夾:尚未升正的試作;升正那一刻才套全樹契約"),
    ("/tools/VDF_InjectAccelNetBridges",
     "一次性注入工具,跑完即退場(同批605 `_patches/` 豁免理由)"),
    ("/_vdf_engines/sentiment_strength/",
     "純函式庫模組(無 main;由 SUP_MDL566 SentimentStrengthRouter 呼叫):自測歸呼叫端"),
)

# ── LL133 自我指涉:判定器不自判 ──────────────────────────────────────────────
# 排掉的是**整個家族**,不是只排 `__file__` 這一支——只排一支的話,一開新版號,
# 舊版就變成被自己數進去的受審者。豁免不等於沒人看:本閘的自測由格子站
# 「VDF 審計閘十檢」跑,覆蓋一格沒掉,而且下面照樣把它連理由印出來(L87)。
_SELF_FAMILY = Path(__file__).stem.rsplit("_v", 1)[0]
SELF_WHY = ("本閘自己(整個 %s 家族):判定器不自判(LL133);"
            "它的自測由格子站「VDF 審計閘十檢」跑,覆蓋沒有掉" % _SELF_FAMILY)


def is_self_family(p: Path) -> bool:
    return p.stem.rsplit("_v", 1)[0] == _SELF_FAMILY


RC_NAME = {0: "GREEN", 1: "RED", 2: "NODATA", 3: "ABSENT", 4: "GATED"}
VER_RE = re.compile(r"^(?P<fam>.+)_v(?P<num>\d{4})$")


def _posix(p: Path, root: Path) -> str:
    try:
        return p.relative_to(root).as_posix()
    except Exception:
        return p.as_posix()


def is_excluded(p: Path) -> bool:
    s = "/" + p.as_posix().strip("/") + "/"
    if any(("/" + e.strip("/") + "/") in s for e in EXCLUDE_PARTS):
        return True
    return any(e in p.name for e in EXCLUDE_NAME)


def exempt_reason(p: Path):
    s = "/" + p.as_posix().lstrip("/")
    for pat, why in AUDIT_EXEMPT:
        if pat in s:
            return why
    return None


def tail_versions(paths):
    """尾版律:同家族(同夾 + 同 `NAME_vNNNN`)只留號碼最大的那一支;無版號者全留。"""
    best = {}
    plain = []
    for p in paths:
        m = VER_RE.match(p.stem)
        if not m:
            plain.append(p)
            continue
        key = (p.parent.as_posix(), m.group("fam"))
        n = int(m.group("num"))
        if key not in best or n > best[key][0]:
            best[key] = (n, p)
    return sorted(plain + [v[1] for v in best.values()], key=lambda x: x.as_posix())


def enumerate_vdf(root: Path):
    """回傳 (要審的檔, [(檔, 豁免理由)])。"""
    allpy = [p for p in sorted(root.rglob("*.py")) if not is_excluded(p)]
    keep = tail_versions(allpy)
    audit, exempt = [], []
    for p in keep:
        if is_self_family(p):
            exempt.append((p, SELF_WHY))
            continue
        why = exempt_reason(p)
        (exempt.append((p, why)) if why else audit.append(p))
    return audit, exempt


def has_verb(p: Path) -> bool:
    try:
        s = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False
    return ("--selftest" in s) or ("--self-test" in s) or (re.search(r"def\s+_?selftest", s) is not None)


def run_one(p: Path, cwd: Path, timeout: int) -> dict:
    """跑一支 `--selftest`。回傳誠實態 + 說得出原因的尾段(L86:紅燈那幾行不受上限)。"""
    rel = p.as_posix()
    if not has_verb(p):
        return {"file": rel, "state": "NO_SELFTEST", "rc": None, "why": ""}
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    flag = "--selftest" if "--selftest" in p.read_text(encoding="utf-8", errors="replace") else "--self-test"
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, "-u", str(p), flag], capture_output=True, text=True,
                           timeout=timeout, stdin=subprocess.DEVNULL, cwd=str(cwd), env=env, errors="replace")
    except subprocess.TimeoutExpired:
        return {"file": rel, "state": "TIMEOUT", "rc": None, "why": "逾時 %ds" % timeout, "sec": round(time.time() - t0, 1)}
    except Exception as e:
        return {"file": rel, "state": "EXC", "rc": None, "why": "%s: %s" % (type(e).__name__, e), "sec": round(time.time() - t0, 1)}
    lines = [l for l in ((r.stdout or "") + (r.stderr or "")).strip().splitlines() if l.strip()]
    bad = [l for l in lines if l.lstrip().startswith(("[FAIL", "[錯", "FAIL", "Traceback")) or "Error:" in l]
    tally = [l for l in lines[-3:] if "FAIL" in l and ("計" in l or "檢" in l) and l not in bad]
    why = (bad[:2] + tally[:1]) or lines[-2:]
    return {"file": rel, "state": RC_NAME.get(r.returncode, "RC%d" % r.returncode), "rc": r.returncode,
            "why": " / ".join(x.strip()[:180] for x in why), "sec": round(time.time() - t0, 1)}


BADSTATES = ("RED", "TIMEOUT", "EXC")


def audit(root: Path, cwd: Path, workers: int = 6, timeout: int = 300, quiet: bool = False) -> dict:
    """列冊 → 平行跑 → **序跑複判**。複判是本閘的骨頭,不是選配。"""
    todo, exempt = enumerate_vdf(root)
    say = (lambda *a: None) if quiet else print
    say("[列冊] 活樹 %d 支待審 · 豁免 %d 支(附理由)" % (len(todo), len(exempt)))
    with _cf.ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        res = list(ex.map(lambda p: run_one(p, cwd, timeout), todo))
    flips = []
    bad = [x for x in res if x["state"] in BADSTATES]
    if bad:
        say("[複判] 平行段敗 %d 支 → 逐支序跑再判(鎖撞 = 假紅)" % len(bad))
        for i, x in enumerate(res):
            if x["state"] in BADSTATES:
                y = run_one(Path(x["file"]), cwd, timeout)
                y["reran"] = True
                y["flip"] = "轉綠" if y["state"] not in BADSTATES else "仍紅"
                if y["flip"] == "轉綠":
                    flips.append({"file": x["file"], "平行": x["state"], "序跑": y["state"]})
                res[i] = y
    breach = [x["file"] for x in res if x["state"] == "NO_SELFTEST"]
    tally = Counter(x["state"] for x in res)
    real_red = [x for x in res if x["state"] in BADSTATES]
    rc = 1 if (real_red or breach) else (2 if tally.get("NODATA") else 0)
    return {"root": root.as_posix(), "tally": dict(tally), "results": res, "flips": flips,
            "exempt": [{"file": p.as_posix(), "why": w} for p, w in exempt],
            "breach": breach, "rc": rc, "state": RC_NAME[rc]}


def report(rep: dict) -> None:
    print("\n=== VDF 審計閘 v%s ===" % VERSION)
    print("[計] " + " · ".join("%s %d" % (k, v) for k, v in sorted(rep["tally"].items())))
    for x in rep["results"]:
        if x["state"] in ("GREEN",):
            continue
        tag = x["state"]
        if x.get("reran"):
            tag += "/複判" + x.get("flip", "")
        print("  [%-10s] %s" % (tag, x["file"].split("/")[-1]))
        if x.get("why"):
            print("             " + x["why"][:220])
    if rep["flips"]:
        print("[複判] 平行假紅 %d 支已轉綠(鎖撞;不是引擎壞):" % len(rep["flips"]))
        for f in rep["flips"]:
            print("   · %s  %s → %s" % (f["file"].split("/")[-1], f["平行"], f["序跑"]))
    if rep["breach"]:
        print("[FAIL] L53 全樹契約:%d 支活樹檔無 `--selftest` 且不在豁免冊" % len(rep["breach"]))
        for b in rep["breach"]:
            print("   · " + b)
    print("[豁免] %d 支(每支都附理由,沒理由的豁免等於假綠):" % len(rep["exempt"]))
    for e in rep["exempt"]:
        print("   · %-58s %s" % (e["file"].split("/VDF/")[-1][:58], e["why"]))
    print("[裁決] rc=%d (%s)" % (rep["rc"], rep["state"]))


# ══════════════════════════════════════════════════════════════════════════════
def _selftest() -> int:
    ok, bad, nod = [], [], []

    def chk(n, c, why=""):
        (ok if c else bad).append(n)
        print(("  ✓ " + n) if c else "  [FAIL] %s — %s" % (n, why))

    print("🧪 VDF_ENG091_VdfAuditGate v%s --selftest(零連線、零寫樹)" % VERSION)

    # ① 豁免冊格式:沒理由的豁免等於假綠
    okfmt = all(isinstance(p, str) and p and isinstance(w, str) and len(w.strip()) >= 8 for p, w in AUDIT_EXEMPT)
    chk("① 豁免冊每筆都附非空理由", okfmt, "有豁免沒寫理由")

    # ② L77 排除清單齊備
    need = ("references/intake", "_superseded", "RetiredEngines", "_backup", "SCOPE_COPY",
            "__pycache__", "node_modules", "site-packages")
    miss = [n for n in need if n not in EXCLUDE_PARTS]
    chk("② L77 排除清單八項齊備", not miss and "_sha" in EXCLUDE_NAME, "缺 %s" % miss)

    # ③④⑤⑥ 合成一棵假樹,驗列冊三律
    with tempfile.TemporaryDirectory() as td:
        R = Path(td) / "VDF"
        for rel in ("E_v0100.py", "E_v0102.py", "E_v0101.py", "plain.py",
                    "_superseded/old.py", "frozen_sha256.py", "__pycache__/x.py",
                    "engine/candidates/cand.py", "_vdf_engines/sentiment_strength/VDF_Engine_x.py",
                    "noverb.py"):
            f = R / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("import sys\nif '--selftest' in sys.argv: sys.exit(0)\n", encoding="utf-8")
        (R / "noverb.py").write_text("print('沒有動詞')\n", encoding="utf-8")
        todo, exempt = enumerate_vdf(R)
        names = sorted(p.name for p in todo)
        chk("③ 尾版律只取最新版", "E_v0102.py" in names and "E_v0100.py" not in names and "E_v0101.py" not in names,
            "列到 %s" % names)
        chk("④ 排除清單真的排除(_superseded/_sha/__pycache__)",
            not any(n in ("old.py", "frozen_sha256.py", "x.py") for n in names), "列到 %s" % names)
        exnames = sorted(p.name for p, _ in exempt)
        chk("⑤ 豁免命中 candidates/ 與函式庫模組",
            exnames == ["VDF_Engine_x.py", "cand.py"], "豁免到 %s" % exnames)
        rep = audit(R, R, workers=2, timeout=60, quiet=True)
        chk("⑥ 未豁免的缺動詞判違約(不是靜靜放過)",
            rep["breach"] == [(R / "noverb.py").as_posix()] and rep["rc"] == 1, "breach=%s rc=%s" % (rep["breach"], rep["rc"]))

    # ⑦ rc 對照表
    chk("⑦ rc 誠實多態對照表", RC_NAME == {0: "GREEN", 1: "RED", 2: "NODATA", 3: "ABSENT", 4: "GATED"})

    # ⑧⑨ 兩條路都要走(L83):鎖撞假紅要轉綠,真紅不准被洗綠
    with tempfile.TemporaryDirectory() as td:
        R = Path(td) / "VDF"
        R.mkdir(parents=True)
        lock = (R / "held.lock").as_posix()
        (R / "A_holder.py").write_text(
            "import sys,os,time\n"
            "if '--selftest' in sys.argv:\n"
            "    open(%r,'w').write('1')\n"
            "    time.sleep(3.0)\n"
            "    os.remove(%r)\n"
            "    sys.exit(0)\n" % (lock, lock), encoding="utf-8")
        (R / "B_contended.py").write_text(
            "import sys,os,time\n"
            "if '--selftest' in sys.argv:\n"
            "    t0=time.time()\n"
            "    while time.time()-t0 < 2.0:\n"
            "        if os.path.exists(%r):\n"
            "            print('[FAIL] 庫被鎖住(模擬 DuckDB 鎖撞)'); sys.exit(1)\n"
            "        time.sleep(0.05)\n"
            "    print('OK 1'); sys.exit(0)\n" % (lock,), encoding="utf-8")
        (R / "C_reallybad.py").write_text(
            "import sys\n"
            "if '--selftest' in sys.argv:\n"
            "    print('[FAIL] 這支是真的壞'); sys.exit(1)\n", encoding="utf-8")
        rep = audit(R, R, workers=3, timeout=60, quiet=True)
        st = {Path(x["file"]).name: x for x in rep["results"]}
        chk("⑧ 鎖撞假紅經序跑複判轉綠",
            st["B_contended.py"]["state"] == "GREEN" and st["B_contended.py"].get("flip") == "轉綠",
            "B=%s flip=%s(平行段沒撞到就不算走過這條路)" % (st["B_contended.py"]["state"], st["B_contended.py"].get("flip")))
        chk("⑨ 真紅不被複判洗綠",
            st["C_reallybad.py"]["state"] == "RED" and st["C_reallybad.py"].get("flip") == "仍紅",
            "C=%s" % st["C_reallybad.py"]["state"])

    # ⑩ 本閘零連線:自測期間不得有任何 connect
    import socket as _sk
    hit = []
    _orig = _sk.socket.connect

    def _blocked(self, *a, **k):
        hit.append(a[0] if a else "?")
        raise OSError("VIA selftest: 零連線閘攔截")

    _sk.socket.connect = _blocked
    try:
        enumerate_vdf(Path(tempfile.gettempdir()) / "___via_nope___")
        _via_net()
    finally:
        _sk.socket.connect = _orig
    chk("⑩ 零連線實證", not hit, "列冊/網路橋嘗試連線 %s" % hit[:2])

    # ⑪ LL133:本閘不自判,而且排的是整個家族不是單一支
    with tempfile.TemporaryDirectory() as td:
        R = Path(td) / "VDF"
        R.mkdir(parents=True)
        for nm in (_SELF_FAMILY + "_v0100.py", _SELF_FAMILY + "_v0199.py", "other_v0100.py"):
            (R / nm).write_text("import sys\nif '--selftest' in sys.argv: sys.exit(0)\n", encoding="utf-8")
        todo, exempt = enumerate_vdf(R)
        exn = sorted(p.name for p, _ in exempt)
        chk("⑪ 本閘不自判且排掉整個家族(LL133)",
            [p.name for p in todo] == ["other_v0100.py"] and exn == [_SELF_FAMILY + "_v0199.py"]
            and all(w == SELF_WHY for _, w in exempt),
            "待審 %s · 豁免 %s(尾版律先收斂家族,所以只會看到最新那一支)" % ([p.name for p in todo], exn))

    rc = 1 if bad else (2 if nod else 0)
    print("[計] OK %d · FAIL %d · NODATA %d → rc=%d (%s)" % (len(ok), len(bad), len(nod), rc, RC_NAME[rc]))
    return rc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="VDF_ENG091_VdfAuditGate", add_help=True)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--self-test", dest="selftest", action="store_true")
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--root", default="")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--json", default="")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()

    here = Path(__file__).resolve()
    root = Path(a.root).resolve() if a.root else here.parent.parent          # …/functional modules/VDF
    via = here
    while via.parent != via and not (via / "supportive modules").is_dir():
        via = via.parent
    if not root.is_dir():
        print("[ABSENT] VDF 樹不在:%s" % root)
        print("         **缺樹不是壞掉**:先把 --root 指對再跑。誠實停,不裸噴 traceback。")
        return 3
    rep = audit(root, via if (via / "supportive modules").is_dir() else root,
                workers=a.workers, timeout=a.timeout)
    report(rep)
    out = Path(a.json) if a.json else (via / "VIA_Reports" / "VDF_Audit" / "VDF_AUDIT_LATEST.json")
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        print("[報告] " + out.as_posix())
    except Exception as e:
        print("[警] 報告寫不出來(不影響裁決):%s" % e)
    return rep["rc"]


if __name__ == "__main__":
    sys.exit(main())
