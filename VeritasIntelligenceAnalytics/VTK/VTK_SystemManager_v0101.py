#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VTK_SystemManager v0101 — 薄尾(v0100 一字不動):解除限制,讓 VTK 成為能單獨用的工具系統。

操作員 2026-11-26 14:31「解除限制成為獨立新系統工具」:
  ① 位置:VTK 在 VIA 根下 VTK/,每家工具在 VTK/<家>/。副本用 HERE.parents[1] 推 VIA 根,深度對齊後推得對、副本不用改。
  ② 入口:參數冊 adapt 規則改 VTK 自己的副本(例:閘也收 VIA_FROM_VTK)。改法、處數、來源雜湊、改後雜湊全登號冊;
     .py 改完先在記憶體 ast.parse + compile,有一檔不過就整批零寫入。VCGC 原檔永遠不動。
  ③ 附帶冊:extra_files 把工具要讀的冊一起帶過來(syscat 的參數冊),也照 adapt 改(輸出夾改到 VIA_Reports/vtk/)。
  ④ drill 改成通用擺法:VTK 在哪裡都整份複製,只拿掉 supportive modules/registry/CGC_*.py。
動詞同 v0100;sync · status · drill 換成本版,其餘轉給 v0100。
"""
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
import ast
import contextlib
import fnmatch
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
from pathlib import Path

ENGINE = "VTK_SystemManager_v0101"
PRIOR_NAME = "VTK_SystemManager_v0100.py"
HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("VTK_SystemManager_v0100", HERE / PRIOR_NAME)
BASE = importlib.util.module_from_spec(_spec)
sys.modules["VTK_SystemManager_v0100"] = BASE
_spec.loader.exec_module(BASE)
VERBS = dict(BASE.VERBS, sync="從 VCGC 鎖冊複製版本鏈 + 附帶冊,照參數冊 adapt 改 VTK 副本(預設乾跑;--apply 才寫)",
             status="VTK 自報燈:副本對號冊上的改後雜湊;改過幾處一併列")


def _sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()


def _recorded(reg: dict) -> dict:
    out = {}
    for r in reg["rows"]:
        for f in r["files"]:
            out[(r["family"], f["name"])] = (f["sha256_lf"], f.get("vtk_sha256_lf", f["sha256_lf"]))
    return out


def adapt(c, fam: str, name: str, raw: bytes):
    """照參數冊 adapt 規則改內容;回 (新內容, [(規則, 處數)])。規則沒對到就原樣。"""
    rules = [r for r in (c.prm.get("adapt") or {}).get(fam, []) if fnmatch.fnmatch(name, r["files"])]
    if not rules:
        return raw, []
    text, done = raw.decode("utf-8"), []
    for r in rules:
        n = text.count(r["find"])
        if n:
            text = text.replace(r["find"], r["replace"])
            done.append([r["id"], n])
    return text.encode("utf-8"), done


def _files(c, fam: str, src: Path) -> list:
    """(來源檔, 在 VTK/<家>/ 底下的相對路徑, 是否附帶)。附帶項可以是檔或整個夾(保留相對結構)。"""
    out = [(f, f.name, False) for f in BASE.chain(src)]
    for x in (c.prm.get("extra_files") or {}).get(fam, []):
        p = c.via / x
        if p.is_dir():
            out += [(q, (Path(p.name) / q.relative_to(p)).as_posix(), True) for q in sorted(p.rglob("*"))
                    if q.is_file() and "__pycache__" not in q.parts and not q.name.startswith(".")]
        else:
            out.append((p, p.name, True))
    return out


def plan(c) -> list:
    reg = c.register()
    rec, last, rows = _recorded(reg), c.latest(reg), []
    for fam, src in sorted(c.sources().items()):
        if not src.is_file():
            rows.append({"family": fam, "state": "MISSING_SOURCE", "tail": src.name, "files": []})
            continue
        files = []
        for f, rel, extra in _files(c, fam, src):
            if not f.is_file():
                files.append({"name": rel, "state": "MISSING_SOURCE", "src": f})
                continue
            raw = f.read_bytes()
            want, done = adapt(c, fam, f.name, raw)
            d, r = c.tools / fam / rel, rec.get((fam, rel))
            if not d.exists():
                st = "NEW"
            elif BASE.sha_lf(d) == _sha_bytes(want):
                st = "SAME"
            elif r and r[0] == _sha_bytes(raw) and BASE.sha_lf(d) == r[1]:
                st = "ADAPT"  # VTK 自己寫的、沒被動過,只是改法變了
            else:
                st = "CONFLICT"  # 被手改,或同名來源內容變了
            files.append({"name": rel, "state": st, "src": f, "want": want, "done": done, "raw": raw, "extra": extra})
        states = {x["state"] for x in files}
        fam_state = ("CONFLICT" if "CONFLICT" in states else "MISSING_SOURCE" if "MISSING_SOURCE" in states
                     else "NEW" if "NEW" in states else "ADAPT" if "ADAPT" in states
                     else "UNCHANGED" if last.get(fam, {}).get("tail") == src.name else "RELINK")
        rows.append({"family": fam, "state": fam_state, "tail": src.name, "files": files, "source": src})
    return rows


def sync(c, apply: bool) -> int:
    rows = plan(c)
    for r in rows:
        n = {s: sum(1 for x in r["files"] if x["state"] == s) for s in ("NEW", "SAME", "ADAPT", "CONFLICT")}
        k = sum(m for x in r["files"] for _, m in x.get("done", []))
        print("  %-11s %-14s %-48s 新 %d · 同 %d · 改法 %d · 衝突 %d · VTK 改 %d 處" % (
            r["family"], r["state"], r["tail"], n["NEW"], n["SAME"], n["ADAPT"], n["CONFLICT"], k))
    bad = [r["family"] for r in rows if r["state"] in ("CONFLICT", "MISSING_SOURCE")]
    if bad:
        print("[sync] RED · 零寫入 · 衝突或來源不在:%s" % "、".join(bad))
        return 1
    todo = [r for r in rows if r["state"] in ("NEW", "ADAPT", "RELINK")]
    broken = []
    for r in todo:  # 先全部驗過才寫:語法樹 + 編譯
        for x in r["files"]:
            if x["name"].endswith(".py") and x["state"] in ("NEW", "ADAPT") and x["done"]:
                try:
                    compile(ast.parse(x["want"].decode("utf-8")), x["name"], "exec")
                except SyntaxError as e:
                    broken.append("%s/%s(%s)" % (r["family"], x["name"], e.msg))
    if broken:
        print("[sync] RED · 零寫入 · 改完過不了語法樹或編譯:%s" % "、".join(broken))
        return 1
    if not apply:
        print("[sync] 乾跑 · 要寫 %d 家;加 --apply 才寫" % len(todo))
        return 0
    with BASE.book_lock(c.home):
        reg = c.register()
        for r in todo:
            (c.tools / r["family"]).mkdir(parents=True, exist_ok=True)
            for x in r["files"]:
                if x["state"] in ("NEW", "ADAPT"):
                    d = c.tools / r["family"] / x["name"]
                    d.parent.mkdir(parents=True, exist_ok=True)
                    tmp = d.with_name(".%s.%d.tmp" % (d.name, os.getpid()))
                    tmp.write_bytes(x["want"])
                    shutil.copystat(str(x["src"]), str(tmp))
                    os.replace(str(tmp), str(d))
            fams = reg["families"]
            if r["family"] not in fams:
                nums = [int(v.rsplit("-", 1)[1]) for v in fams.values()] or [0]
                fams[r["family"]] = "%s%04d" % (c.prm["code_prefix"], max(nums) + 1)
            reg["rows"].append({"family": r["family"], "code": fams[r["family"]], "tail": r["tail"],
                                "version": "v" + BASE.VN.search(r["tail"]).group(1),
                                "files": [dict({"name": x["name"], "sha256_lf": _sha_bytes(x["raw"]), "vtk_sha256_lf": _sha_bytes(x["want"])},
                                               **({"adapted": x["done"]} if x["done"] else {}),
                                               **({"extra": True} if x.get("extra") else {})) for x in r["files"]],
                                "source": {"path": str(r["source"].relative_to(c.via)).replace("\\", "/"), "sha256_lf": BASE.sha_lf(r["source"])},
                                "copied_at": BASE.now(), "by": ENGINE})
        BASE.write_json(c.reg_path, reg)
    print("[sync] GREEN · 寫了 %d 家 · 號冊 %s" % (len(todo), c.reg_path.name))
    return 0


def status(c) -> int:
    reg, bad, rows = c.register(), [], []
    for fam, r in sorted(c.latest(reg).items()):
        miss = [f["name"] for f in r["files"] if not (c.tools / fam / f["name"]).is_file()
                or BASE.sha_lf(c.tools / fam / f["name"]) != f.get("vtk_sha256_lf", f["sha256_lf"])]
        k = sum(n for f in r["files"] for _, n in f.get("adapted", []))
        gated = fam in c.prm.get("gated_vcgc", [])
        lamp = "RED" if miss else ("GRAY" if gated else "GREEN")
        bad += miss
        rows.append((lamp, fam, r["code"], r["tail"], "缺或被改:" + "、".join(miss) if miss else
                     "副本 %d 檔一致%s" % (len(r["files"]), " · VTK 改 %d 處" % k if k else "")))
    lamp = "RED" if bad else ("YELLOW" if not c.param_ok or not rows else "GREEN")
    print("[VTK status] %s · %d 家 · 位置 %s · 參數 %s · 號冊 %s" % (
        lamp, len(rows), str(c.home.relative_to(c.via)).replace("\\", "/"), c.param_note, c.reg_path.name))
    for r in rows:
        print("  %-6s %-11s %-14s %-48s %s" % r)
    return {"GREEN": 0, "YELLOW": 2, "RED": 1}[lamp]


def drill(c) -> int:
    """暫存樹:VTK 整份複製(在哪都一樣),registry 拿掉 CGC_*.py,其餘一律用連結代入。"""
    last, tmp = c.latest(c.register()), Path(tempfile.mkdtemp(prefix="vtk_drill_"))
    home, regdir = c.home.resolve(), (c.via / "supportive modules" / "registry").resolve()

    def place(src: Path, dst: Path, top: bool = False):
        rs = src.resolve()
        if rs == home:
            shutil.copytree(str(src), str(dst), ignore=shutil.ignore_patterns("__pycache__", ".*"))
        elif src.is_dir() and (home.is_relative_to(rs) or regdir.is_relative_to(rs)):
            dst.mkdir(parents=True, exist_ok=True)
            for e in src.iterdir():
                if (top and e.name in (".git", "VIA_Reports")) or (rs == regdir and e.name.startswith("CGC_") and e.suffix == ".py"):
                    continue
                place(e, dst / e.name)
        else:
            os.symlink(str(src), str(dst))

    res = []
    try:
        root = tmp / c.via.name
        place(c.via, root, True)
        home2 = root / c.home.relative_to(c.via)
        cgc_left = [p.name for p in (root / "supportive modules" / "registry").glob("CGC_*.py")]
        for fam, r in sorted(last.items()):
            f = home2 / c.prm["tools_dir"] / fam / r["tail"]
            try:
                cp = subprocess.run([sys.executable, "-c", BASE.PROBE, str(f)], cwd=str(tmp), capture_output=True, text=True,
                                    timeout=c.prm["drill_timeout_s"], env=dict(os.environ, VIA_FROM_VTK="YES"))
                ok = cp.returncode == 0
                acc = ok and json.loads(cp.stdout.strip().splitlines()[-1]).get("accel")
                why = "" if ok else (cp.stderr.strip().splitlines() or ["?"])[-1][:140]
            except subprocess.TimeoutExpired:
                ok, acc, why = False, False, "逾時 %ss" % c.prm["drill_timeout_s"]
            res.append(("GREEN" if ok and acc else "YELLOW" if ok else "RED", fam, r["code"],
                        "載入過 · 加速器在" if ok and acc else ("載入過但加速器載不到" if ok else why)))
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)
    lamp = "RED" if any(x[0] == "RED" for x in res) or cgc_left else ("YELLOW" if any(x[0] != "GREEN" for x in res) else "GREEN")
    print("[VTK drill] %s · 應演練 %d · 已演練 %d · 略過 0 · 暫存樹裡 VCGC CGC_*.py = %d" % (lamp, len(last), len(res), len(cgc_left)))
    for x in res:
        print("  %-6s %-11s %-14s %s" % x)
    return {"GREEN": 0, "YELLOW": 2, "RED": 1}[lamp]


def __getattr__(name):
    return getattr(BASE, name)


def selftest() -> int:
    res = []

    def chk(name, ok, extra=""):
        res.append(bool(ok))
        print("  [%s] %s%s" % ("過" if ok else "敗", name, "" if ok else " · " + str(extra)[:240]))

    keep_here, ptmp = BASE.HERE, Path(tempfile.mkdtemp(prefix="vtk_prior_"))
    try:  # 甲 裁定:只驗自己與直接前版;前版吃它自己那一版的參數冊
        shutil.copy2(str(HERE / "VTK_Params_v0100.json"), str(ptmp))
        BASE.HERE = ptmp
        with contextlib.redirect_stdout(io.StringIO()):
            rp = BASE.selftest()
    finally:
        BASE.HERE = keep_here
        shutil.rmtree(str(ptmp), ignore_errors=True)
    chk("① 直接前版 v0100 自測過", rp == 0)
    real = BASE.via_root()
    tmp = Path(tempfile.mkdtemp(prefix="vtk_selftest_"))
    try:
        via = tmp / "VeritasIntelligenceAnalytics"
        reg = via / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        for f in [real / "supportive modules" / "VIA_SuperAccel_Module.py"] + sorted((real / "supportive modules").glob("SUP_MDL737_SuperAccelModule_v*.py")):
            shutil.copy2(str(f), str(via / "supportive modules"))
        bridge = Path(__file__).read_text(encoding="utf-8").split("# ===== [VIA:ACCEL-BRIDGE:v0100]", 1)[1].split("# ===== [VIA:ACCEL-BRIDGE:END] =====")[0]
        hdr = "# [VIA:ACCEL-BRIDGE:v0111]\n# ===== [VIA:ACCEL-BRIDGE:v0100]" + bridge + "# ===== [VIA:ACCEL-BRIDGE:END] =====\n"
        (reg / "GGG_Gate_v0100.py").write_text(hdr + "import os,sys\nfrom pathlib import Path\nHERE=Path(__file__).resolve().parent\nVIA=HERE.parents[1]\n"
                                               "if __name__=='__main__':\n    if os.environ.get(\"VIA_FROM_VCGC\") != \"YES\":\n"
                                               "        print('DENY');sys.exit(2)\n    print('ALLOW', VIA.name, (VIA/'supportive modules'/'registry').is_dir())\n", encoding="utf-8")
        (reg / "XXX_Params_v0100.json").write_text('{"out_dir": "VIA_Reports/vcgc/x"}\n', encoding="utf-8")
        (reg / "gate_parts" / "sub").mkdir(parents=True)
        (reg / "gate_parts" / "sub" / "part_v0100.py").write_text("Y = 2\n", encoding="utf-8")
        (reg / "VIA_ToolVersion_Lock_v0100.json").write_text(json.dumps(
            {"policy": "x", "gate": {"path": "VeritasIntelligenceAnalytics/supportive modules/registry/GGG_Gate_v0100.py"}}), encoding="utf-8")
        home = via / "VTK"
        home.mkdir()
        pb = json.loads(BASE.tail(HERE, "VTK_Params").read_text(encoding="utf-8"))
        p = pb["params"]
        p["extra_sources"], p["extra_files"] = {}, {"gate": ["supportive modules/registry/XXX_Params_v0100.json", "supportive modules/registry/gate_parts"]}
        p["adapt"] = {"gate": p["adapt"]["layout"][:1] + [dict(p["adapt"]["syscat"][0], files="XXX_Params_v*.json",
                                                          find='"VIA_Reports/vcgc/x"', replace='"VIA_Reports/vtk/x"')]}
        BASE.write_json(home / "VTK_Params_v0101.json", pb)
        before = {f.name: BASE.sha_lf(f) for f in reg.iterdir() if f.is_file()}
        c = BASE.Ctx(home, via)
        chk("② 參數冊尾版:工具直接放 VTK/<家>/", c.param_ok and c.tools == home)
        with contextlib.redirect_stdout(io.StringIO()):
            r1 = sync(c, True)
        g = c.register()["rows"][-1]
        fx = {f["name"]: f for f in g["files"]}
        chk("③ 同步:閘改 1 處、附帶冊改 1 處,號冊登來源與改後兩個雜湊", r1 == 0 and fx["GGG_Gate_v0100.py"].get("adapted") == [["GATE-VTK", 1]]
            and fx["XXX_Params_v0100.json"].get("adapted") == [["OUT-VTK", 1]] and fx["XXX_Params_v0100.json"].get("extra")
            and fx["GGG_Gate_v0100.py"]["sha256_lf"] != fx["GGG_Gate_v0100.py"]["vtk_sha256_lf"], g)
        tool = home / "gate" / "GGG_Gate_v0100.py"
        env = {k: v for k, v in os.environ.items() if k not in ("VIA_FROM_VCGC", "VIA_FROM_VTK")}
        a = subprocess.run([sys.executable, str(tool)], capture_output=True, text=True, env=dict(env, VIA_FROM_VTK="YES"))
        chk("④ VTK 入口放行;副本推出的 VIA 根是真的 VIA 根(深度對齊)", a.returncode == 0 and "ALLOW VeritasIntelligenceAnalytics True" in a.stdout, a.stdout + a.stderr)
        b = subprocess.run([sys.executable, str(tool)], capture_output=True, text=True, env=env)
        chk("⑤ 沒有任何入口標記照樣擋", b.returncode == 2 and "DENY" in b.stdout)
        chk("⑥ 附帶冊的輸出夾改成 VTK 自己的;附帶夾照相對結構帶過來並登號冊", '"VIA_Reports/vtk/x"' in (home / "gate" / "XXX_Params_v0100.json").read_text(encoding="utf-8")
            and (home / "gate" / "gate_parts" / "sub" / "part_v0100.py").is_file() and fx.get("gate_parts/sub/part_v0100.py", {}).get("extra"))
        n = len(c.register()["rows"])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            r2 = sync(c, True)
        chk("⑦ 再同步:改過的副本算「相同」,不加列", r2 == 0 and len(c.register()["rows"]) == n and "UNCHANGED" in buf.getvalue(), buf.getvalue())
        chk("⑧ VCGC 原檔一字不動", all(BASE.sha_lf(reg / k) == v for k, v in before.items()))
        tool.write_text(tool.read_text(encoding="utf-8") + "# hand edit\n", encoding="utf-8")
        keep = BASE.sha_lf(c.reg_path)
        with contextlib.redirect_stdout(io.StringIO()):
            r3, r4 = status(c), sync(c, True)
        chk("⑨ 副本被手改:status 紅、sync 衝突零寫入", r3 == 1 and r4 == 1 and BASE.sha_lf(c.reg_path) == keep)
        tool.write_text(tool.read_text(encoding="utf-8").replace("# hand edit\n", ""), encoding="utf-8")
        pb2 = json.loads((home / "VTK_Params_v0101.json").read_text(encoding="utf-8"))
        pb2["params"]["adapt"]["gate"].append({"id": "BAD", "files": "*.py", "find": "print('DENY')", "replace": "print('DENY'"})
        BASE.write_json(home / "VTK_Params_v0101.json", pb2)
        keep_tool = BASE.sha_lf(tool)
        with contextlib.redirect_stdout(io.StringIO()):
            r5 = sync(BASE.Ctx(home, via), True)
        chk("⑩ 改法會弄壞語法:整批零寫入", r5 == 1 and BASE.sha_lf(tool) == keep_tool and BASE.sha_lf(c.reg_path) == keep)
        BASE.write_json(home / "VTK_Params_v0101.json", pb)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            r6 = drill(BASE.Ctx(home, via))
        chk("⑪ drill:VTK 在 VIA 根下也整份複製、CGC_*.py = 0、副本載得起來", r6 == 0 and "CGC_*.py = 0" in buf.getvalue(), buf.getvalue())
        chk("⑫ 加速器執行時真的載到", VIA_ACCEL is not None)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            main(["verbs", "--json"])
        chk("⑬ verbs --json 自報", set(json.loads(buf.getvalue())["verbs"]) == set(VERBS))
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)
    ok = all(res)
    print("[selftest] %s · %d 敗 · %s" % ("GREEN" if ok else "RED", res.count(False), ENGINE))
    return 0 if ok else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a and a[0] in ("--selftest", "selftest"):
        return selftest()
    v, rest = (a[0], a[1:]) if a else ("status", [])
    if v == "verbs":
        if "--json" in rest:
            print(json.dumps({"system": "VTK", "entry": ENGINE, "verbs": VERBS}, ensure_ascii=False))
        else:
            for k, d in VERBS.items():
                print("  %-9s %s" % (k, d))
        return 0
    if v == "status":
        return status(BASE.Ctx(HERE))
    if v == "sync":
        return sync(BASE.Ctx(HERE), "--apply" in rest)
    if v == "drill":
        return drill(BASE.Ctx(HERE))
    return BASE.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
