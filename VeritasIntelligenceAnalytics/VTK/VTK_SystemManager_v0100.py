#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VTK_SystemManager v0100 — VIA 省 Token 系統(VTK)的入口。

VTK 是獨立系統(操作員 2026-11-26 14:12 令 · 裁定:新開獨立系統 · 複製過去舊檔留著 · 自己發號 · 短指令先列清單):
  · 省 Token 工具十家(accelerator · network · layout · nlp · token · frame · praddle · pdfplumber · ocr · syscat)
    從 VCGC 鎖冊上的現役檔「整條版本鏈」複製到 VTK/tools/<家>/;VCGC 原檔一字不動、照常可用。
  · 號由 VTK 自己發:VTK-TOOL-####,一家一號永不改;每次同步加一列(只增)。
  · 只寫自己的夾與冊(VTK_Params · VTK_Register · VTK_Requirements);讀 VCGC 鎖冊只讀。
動詞:verbs [--json] · status · tools · sync [--apply] · run <家> [參數…] · drill · commands · --selftest
  sync     看 VCGC 鎖冊 → 列「新增 / 相同 / 衝突」;--apply 才複製。同名不同內容 = 衝突,零寫入。
  run      在 VTK 的副本上跑工具,子行程帶 VTK 自己的入口標記 VIA_FROM_VTK=YES。
  drill    系統獨立演練:在拿掉 supportive modules/registry/CGC_*.py 的暫存樹上逐家載入 VTK 的副本。
  commands 短指令清單(唯讀):Register-VIA-Commands 尾版每個 via-* 的形狀 · 呼叫的引擎 · 歸屬 · 建議。
參數全在 VTK_Params 尾版(SDD v0101 L4);冊不在 = 用內建預設並降黃。
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
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ENGINE = "VTK_SystemManager_v0100"
HERE = Path(__file__).resolve().parent
VERBS = {"verbs": "列動詞(--json 給 AI 路由,裁定 ⑬)", "status": "VTK 自報燈:參數冊 · 號冊 · 各家副本是否齊全一致",
         "tools": "十家清單:VTK 號 · 現役尾版 · 來源", "sync": "從 VCGC 鎖冊複製版本鏈(預設乾跑;--apply 才寫)",
         "run": "在 VTK 副本上跑一家工具(例:run token read <檔>)", "drill": "系統獨立演練(拿掉 VCGC 的 CGC_*.py 後逐家載入)",
         "commands": "短指令清單(唯讀;先列清單不動手)", "selftest": "自測(全在暫存夾造資料)"}
DEFAULTS = {"lock_book": "supportive modules/registry/VIA_ToolVersion_Lock_v0100.json", "extra_sources": {},
            "tools_dir": "tools", "out_dir": "VIA_Reports/vtk", "drill_timeout_s": 120, "code_prefix": "VTK-TOOL-",
            "commands_glob": "Register-VIA-Commands-v[0-9][0-9][0-9][0-9].ps1", "gated_vcgc": []}
VN = re.compile(r"_v(\d{4})")


def via_root(start: Path = HERE) -> Path:
    p = start
    while p.parent != p:
        if (p / "supportive modules").is_dir():
            return p
        p = p.parent
    return start.parents[1]


def tail(d: Path, stem: str, ext: str = ".json"):
    hits = sorted(d.glob(stem + "_v[0-9][0-9][0-9][0-9]" + ext))
    return hits[-1] if hits else None


def sha_lf(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(p: Path, obj) -> None:
    tmp = p.with_name(".%s.%d.%d.tmp" % (p.name, os.getpid(), time.time_ns()))
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    os.replace(str(tmp), str(p))


@contextlib.contextmanager
def book_lock(home: Path, wait_s: float = 10.0):
    """作業系統層的獨占鎖檔;拿不到就放棄,不刪別人的鎖。"""
    lk, t0, fd = home / ".VTK_Register.lock", time.time(), None
    while fd is None:
        try:
            fd = os.open(str(lk), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if time.time() - t0 > wait_s:
                raise TimeoutError("號冊被別的行程鎖著(%s);不刪別人的鎖" % lk.name)
            time.sleep(0.2)
    try:
        os.write(fd, str(os.getpid()).encode())
        yield
    finally:
        os.close(fd)
        os.unlink(str(lk))


class Ctx:
    def __init__(self, home: Path = HERE, via: Path = None):
        self.home, self.via = home, via or via_root(home)
        pb = tail(home, "VTK_Params")
        self.prm, self.param_ok = dict(DEFAULTS), False
        self.param_note = "參數冊 VTK_Params 不在,用內建預設"
        if pb:
            try:
                self.prm.update(json.loads(pb.read_text(encoding="utf-8"))["params"])
                self.param_ok, self.param_note = True, pb.name
            except (OSError, ValueError, KeyError) as e:
                self.param_note = "參數冊 %s 讀不懂(%s),用內建預設" % (pb.name, type(e).__name__)
        self.tools = home / self.prm["tools_dir"]
        self.reg_path = tail(home, "VTK_Register") or home / "VTK_Register_v0100.json"

    def register(self) -> dict:
        if self.reg_path.exists():
            return json.loads(self.reg_path.read_text(encoding="utf-8"))
        return {"schema": "VIA.VTK.Register.v1", "owner": "VTK", "append_only": True,
                "code_prefix": self.prm["code_prefix"], "families": {}, "rows": []}

    def latest(self, reg: dict) -> dict:
        out = {}
        for r in reg["rows"]:
            out[r["family"]] = r
        return out

    def sources(self) -> dict:
        """VCGC 鎖冊(只讀)+ 參數冊列的額外來源 → {家: 尾版檔}。"""
        lock = json.loads((self.via / self.prm["lock_book"]).read_text(encoding="utf-8"))
        out = {}
        for k, v in lock.items():
            if isinstance(v, dict) and "path" in v:
                rel = v["path"].split(self.via.name + "/", 1)[-1]
                out[k] = self.via / rel
        for k, rel in self.prm["extra_sources"].items():
            out.setdefault(k, self.via / rel)
        return out


def chain(tail_file: Path) -> list:
    """尾版所在夾裡、同家族、版號不大於尾版的全部檔(含 _body 這類同號分檔)。"""
    stem, top = VN.split(tail_file.name)[0], int(VN.search(tail_file.name).group(1))
    return sorted(p for p in tail_file.parent.glob(stem + "_v[0-9][0-9][0-9][0-9]*.py")
                  if VN.split(p.name)[0] == stem and int(VN.search(p.name).group(1)) <= top)


def plan(c: Ctx) -> list:
    rows, last = [], c.latest(c.register())
    for fam, src in sorted(c.sources().items()):
        if not src.is_file():
            rows.append({"family": fam, "state": "MISSING_SOURCE", "tail": src.name, "files": []})
            continue
        files, dst = [], c.tools / fam
        for f in chain(src):
            d = dst / f.name
            st = "NEW" if not d.exists() else ("SAME" if sha_lf(d) == sha_lf(f) else "CONFLICT")
            files.append({"name": f.name, "state": st, "src": f})
        states = {x["state"] for x in files}
        fam_state = ("CONFLICT" if "CONFLICT" in states else "NEW" if "NEW" in states
                     else "UNCHANGED" if last.get(fam, {}).get("tail") == src.name else "RELINK")
        rows.append({"family": fam, "state": fam_state, "tail": src.name, "files": files, "source": src})
    return rows


def sync(c: Ctx, apply: bool) -> int:
    rows = plan(c)
    for r in rows:
        n = {s: sum(1 for x in r["files"] if x["state"] == s) for s in ("NEW", "SAME", "CONFLICT")}
        print("  %-11s %-14s %-48s 新 %d · 同 %d · 衝突 %d" % (r["family"], r["state"], r["tail"], n["NEW"], n["SAME"], n["CONFLICT"]))
    bad = [r["family"] for r in rows if r["state"] in ("CONFLICT", "MISSING_SOURCE")]
    if bad:
        print("[sync] RED · 零寫入 · 衝突或來源不在:%s(同名不同內容以 VCGC 已發布為準,VTK 改發新版號)" % "、".join(bad))
        return 1
    todo = [r for r in rows if r["state"] in ("NEW", "RELINK")]
    if not apply:
        print("[sync] 乾跑 · 要寫 %d 家;加 --apply 才複製" % len(todo))
        return 0
    with book_lock(c.home):
        reg = c.register()
        for r in todo:
            (c.tools / r["family"]).mkdir(parents=True, exist_ok=True)
            for x in r["files"]:
                if x["state"] == "NEW":
                    d = c.tools / r["family"] / x["name"]
                    tmp = d.with_name(".%s.%d.tmp" % (d.name, os.getpid()))
                    shutil.copy2(str(x["src"]), str(tmp))
                    os.replace(str(tmp), str(d))
            fams = reg["families"]
            if r["family"] not in fams:
                nums = [int(v.rsplit("-", 1)[1]) for v in fams.values()] or [0]
                fams[r["family"]] = "%s%04d" % (c.prm["code_prefix"], max(nums) + 1)
            reg["rows"].append({"family": r["family"], "code": fams[r["family"]], "tail": r["tail"],
                                "version": "v" + VN.search(r["tail"]).group(1),
                                "files": [{"name": x["name"], "sha256_lf": sha_lf(x["src"])} for x in r["files"]],
                                "source": {"path": str(r["source"].relative_to(c.via)).replace("\\", "/"), "sha256_lf": sha_lf(r["source"])},
                                "copied_at": now(), "by": ENGINE})
        write_json(c.reg_path, reg)
    print("[sync] GREEN · 寫了 %d 家 · 號冊 %s" % (len(todo), c.reg_path.name))
    return 0


def status(c: Ctx, quiet: bool = False) -> int:
    reg, bad, rows = c.register(), [], []
    for fam, r in sorted(c.latest(reg).items()):
        miss = [f["name"] for f in r["files"] if not (c.tools / fam / f["name"]).is_file()
                or sha_lf(c.tools / fam / f["name"]) != f["sha256_lf"]]
        lamp = "RED" if miss else ("GRAY" if fam in c.prm["gated_vcgc"] else "GREEN")
        bad += miss
        rows.append((lamp, fam, r["code"], r["tail"], "缺或被改:" + "、".join(miss) if miss else
                     ("閘只認 VCGC 入口(VTK-REQ004)" if lamp == "GRAY" else "副本 %d 檔一致" % len(r["files"]))))
    lamp = "RED" if bad else ("YELLOW" if not c.param_ok or not rows else "GREEN")
    if not quiet:
        print("[VTK status] %s · %d 家 · 參數 %s · 號冊 %s" % (lamp, len(rows), c.param_note, c.reg_path.name))
        for r in rows:
            print("  %-6s %-11s %-14s %-48s %s" % r)
    return {"GREEN": 0, "YELLOW": 2, "RED": 1}[lamp]


def run(c: Ctx, args: list) -> int:
    r = c.latest(c.register()).get(args[0] if args else "")
    if not r:
        print("[run] 用法:run <%s> [參數…]" % "|".join(sorted(c.latest(c.register()))))
        return 2
    env = dict(os.environ, VIA_FROM_VTK="YES")
    return subprocess.call([sys.executable, str(c.tools / r["family"] / r["tail"])] + args[1:], env=env)


PROBE = ("import importlib.util,json,sys;s=importlib.util.spec_from_file_location('vtk_probe',sys.argv[1]);"
         "m=importlib.util.module_from_spec(s);sys.modules['vtk_probe']=m;s.loader.exec_module(m);"
         "print(json.dumps({'accel':getattr(m,'VIA_ACCEL',None) is not None}))")


def drill(c: Ctx) -> int:
    """暫存樹:VIA 根下每一項用連結代入,只有 supportive modules/registry 拿掉 CGC_*.py、VTK 夾整份複製。"""
    last, tmp = c.latest(c.register()), Path(tempfile.mkdtemp(prefix="vtk_drill_"))
    root, res = tmp / c.via.name, []
    try:
        for top in c.via.iterdir():
            if top.name in ("supportive modules", "functional modules", "VIA_Reports", ".git"):
                continue
            (root).mkdir(parents=True, exist_ok=True)
            os.symlink(str(top), str(root / top.name))
        for top in ("supportive modules", "functional modules"):
            for e in (c.via / top).iterdir():
                (root / top).mkdir(parents=True, exist_ok=True)
                if top == "supportive modules" and e.name == "registry":
                    (root / top / "registry").mkdir()
                    for f in e.iterdir():
                        if not (f.name.startswith("CGC_") and f.suffix == ".py"):
                            os.symlink(str(f), str(root / top / "registry" / f.name))
                elif e.resolve() == c.home.resolve():
                    shutil.copytree(str(e), str(root / top / e.name), ignore=shutil.ignore_patterns("__pycache__", ".*"))
                else:
                    os.symlink(str(e), str(root / top / e.name))
        home2 = root / c.home.relative_to(c.via)
        cgc_left = [p.name for p in (root / "supportive modules" / "registry").glob("CGC_*.py")]
        for fam, r in sorted(last.items()):
            f = home2 / c.prm["tools_dir"] / fam / r["tail"]
            try:
                cp = subprocess.run([sys.executable, "-c", PROBE, str(f)], cwd=str(tmp), capture_output=True, text=True,
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
    n_red = sum(1 for x in res if x[0] == "RED")
    lamp = "RED" if n_red or cgc_left else ("YELLOW" if any(x[0] != "GREEN" for x in res) else "GREEN")
    print("[VTK drill] %s · 應演練 %d · 已演練 %d · 略過 0 · 暫存樹裡 VCGC CGC_*.py = %d" % (lamp, len(last), len(res), len(cgc_left)))
    for x in res:
        print("  %-6s %-11s %-14s %s" % x)
    return {"GREEN": 0, "YELLOW": 2, "RED": 1}[lamp]


LOGIC = re.compile(r"\b(Get-ChildItem|Copy-Item|Remove-Item|Move-Item|New-Item|Set-Content|Add-Content|Out-File|Invoke-WebRequest|"
                   r"Invoke-RestMethod|Start-Process|Compress-Archive|Expand-Archive|while|switch|git\s|pip\s|ConvertFrom-Json|Import-Csv)\b", re.I)
OWNER = (("CGC_", "VCGC"), ("VDF", "VDF"), ("VRN", "VRN"), ("VAP", "VAP"), ("VQG", "VQG"), ("VTK", "VTK"))


def _bodies(text: str):
    for m in re.finditer(r"(?im)^\s*function\s+(?:global:)?(via-[\w-]+)\s*\{", text):
        i, depth, q = m.end(), 1, None
        while i < len(text) and depth:
            ch = text[i]
            if q:
                if ch == "`":
                    i += 1
                elif ch == q:
                    q = None
            elif ch in "\"'":
                q = ch
            elif ch == "#" and text[i - 1] in " \n\t":
                j = text.find("\n", i)
                i = (j if j >= 0 else len(text)) - 1
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            i += 1
        yield m.group(1), text[m.end():i - 1] if not depth else None


def commands(c: Ctx) -> int:
    src = sorted(c.via.glob(c.prm["commands_glob"]))
    if not src:
        print("[commands] 灰 · 找不到 %s" % c.prm["commands_glob"])
        return 2
    seq, f = [], src[-1]
    while f and f.is_file() and f not in seq:  # 尾版 dot-source 前版,一路接到本體;同名函式以最後定義者生效
        seq.append(f)
        m = re.search(r'(?m)^\s*\.\s*\(Join-Path\s+\$PSScriptRoot\s+"([^"]+\.ps1)"\)', f.read_text(encoding="utf-8-sig"))
        f = f.parent / m.group(1) if m else None
    defs, aliases = {}, {}
    for f in reversed(seq):
        text = f.read_text(encoding="utf-8-sig")
        aliases.update(dict((b, a) for a, b in re.findall(r"Set-Alias\s+-Name\s+(\S+)\s+-Value\s+(via-[\w-]+)", text)))
        for name, body in _bodies(text):
            defs[name] = (body, f.name)
    should = len(defs)
    rows, skipped = [], []
    for name, (body, where) in sorted(defs.items()):
        if body is None:
            skipped.append(name)
            continue
        eng = re.findall(r'"([A-Za-z]{2,4}_[A-Za-z0-9]+_[A-Za-z0-9_]+?)_v\*\.py"', body)
        py = bool(re.search(r"Invoke-VIAPython|\bpython3?(\.exe)?\b", body, re.I)) or bool(eng)
        other = sorted(set(re.findall(r"\b(via-[\w-]+)\b", body)) - {name})
        logic = sorted({x.lower().strip() for x in LOGIC.findall(body)} - ({"start-process"} if py else set()))  # PS 開 py 產的頁合 L117
        dep = bool(re.search(r"DEPRECATED|作廢|改用", body))
        shape = ("PY-LAUNCH" if py and not logic else "PS-LOGIC" if logic else "ALIAS" if other else "PS-ONLY")
        own = next((o for p, o in OWNER if eng and eng[0].startswith(p)), "共用" if eng else "?")
        hint = {"PY-LAUNCH": "已是 PS 進環境 + 叫 py(合 L117);留著", "PS-LOGIC": "邏輯搬進 %s 管理器的動詞,PS 只留轉呼叫" % own,
                "ALIAS": "轉叫別的短指令;留著或併", "PS-ONLY": "寫成 py 動詞(歸屬待裁)"}[shape]
        rows.append({"command": name, "shape": shape, "owner": own, "engines": sorted(set(eng)), "calls": other[:6],
                     "logic": logic, "deprecated": dep, "alias": aliases.get(name, ""), "lines": body.count("\n") + 1, "defined_in": where, "next": hint})
    out = c.via / c.prm["out_dir"]
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    meta = {"source": src[-1].name, "chain": [x.name for x in seq], "source_sha256_lf": sha_lf(src[-1]), "made_at": now(), "by": ENGINE,
            "three": {"should": should, "done": len(rows), "skipped": skipped}}
    write_json(out / ("VTK_ShortCommands_%s.json" % stamp), {"meta": meta, "rows": rows})
    cnt = {s: sum(1 for r in rows if r["shape"] == s) for s in ("PY-LAUNCH", "PS-LOGIC", "ALIAS", "PS-ONLY")}
    md = ["# 短指令清單 · %s(%s)" % (src[-1].name, meta["made_at"]), "",
          "唯讀盤點,沒改任何指令。版本鏈 %d 支(%s → %s),同名以最後定義者生效。應列 %d · 已列 %d · 略過 %d。" % (
              len(seq), seq[-1].name, seq[0].name, should, len(rows), len(skipped)), "",
          "形狀:" + " · ".join("%s %d" % kv for kv in cnt.items()), "",
          "| 指令 | 形狀 | 歸屬 | 呼叫的引擎 | PS 內的邏輯 | 生效於 | 建議 |", "|---|---|---|---|---|---|---|"]
    order = {"PS-LOGIC": 0, "PS-ONLY": 1, "ALIAS": 2, "PY-LAUNCH": 3}
    for r in sorted(rows, key=lambda r: (order[r["shape"]], r["owner"], r["command"])):
        md.append("| %s%s | %s | %s | %s | %s | %s | %s |" % (r["command"], " (作廢)" if r["deprecated"] else "", r["shape"], r["owner"],
                  " ".join(e for e in r["engines"][:2]) or "—", " ".join(r["logic"]) or "—", r["defined_in"].replace("Register-VIA-Commands-", ""), r["next"]))
    (out / ("VTK_ShortCommands_%s.md" % stamp)).write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
    ok = should == len(rows) + len(skipped)
    lamp = "RED" if not ok else ("YELLOW" if skipped else "GREEN")
    print("[commands] %s · 應列 %d · 已列 %d · 略過 %d · %s" % (lamp, should, len(rows), len(skipped), " · ".join("%s %d" % kv for kv in cnt.items())))
    print("  清單:%s/VTK_ShortCommands_%s.{md,json}" % (out, stamp))
    return {"GREEN": 0, "YELLOW": 2, "RED": 1}[lamp]


def selftest() -> int:
    res = []

    def chk(name, ok, extra=""):
        res.append(bool(ok))
        print("  [%s] %s%s" % ("過" if ok else "敗", name, "" if ok else " · " + str(extra)[:200]))

    real = via_root()
    tmp = Path(tempfile.mkdtemp(prefix="vtk_selftest_"))
    try:
        via = tmp / "VeritasIntelligenceAnalytics"
        reg = via / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        for f in [real / "supportive modules" / "VIA_SuperAccel_Module.py"] + sorted((real / "supportive modules").glob("SUP_MDL737_SuperAccelModule_v*.py")):
            shutil.copy2(str(f), str(via / "supportive modules"))
        bridge = Path(__file__).read_text(encoding="utf-8").split("# ===== [VIA:ACCEL-BRIDGE:v0100]", 1)[1].split("# ===== [VIA:ACCEL-BRIDGE:END] =====")[0]
        hdr = "# [VIA:ACCEL-BRIDGE:v0111]\n# ===== [VIA:ACCEL-BRIDGE:v0100]" + bridge + "# ===== [VIA:ACCEL-BRIDGE:END] =====\n"
        (reg / "AAA_Tool_v0100.py").write_text(hdr + "import os,sys\nprint('AAA', os.environ.get('VIA_FROM_VTK'), *sys.argv[1:])\n", encoding="utf-8")
        (reg / "AAA_Tool_v0101.py").write_text(hdr + "import runpy,pathlib\nif __name__=='__main__':\n    runpy.run_path(str(pathlib.Path(__file__).with_name('AAA_Tool_v0100.py')),run_name='__main__')\n", encoding="utf-8")
        (reg / "CGC_MDL999_Dep_v0100.py").write_text("X = 1\n", encoding="utf-8")
        (reg / "BBB_Tool_v0100.py").write_text(hdr + "import sys,pathlib\nsys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'supportive modules'/'registry'))\n"
                                               "import importlib;importlib.import_module('CGC_MDL999_Dep_v0100')\n", encoding="utf-8")
        (reg / "VIA_ToolVersion_Lock_v0100.json").write_text(json.dumps({
            "policy": "x", "alpha": {"path": "VeritasIntelligenceAnalytics/supportive modules/registry/AAA_Tool_v0101.py"},
            "beta": {"path": "VeritasIntelligenceAnalytics/supportive modules/registry/BBB_Tool_v0100.py"}}), encoding="utf-8")
        home = via / "functional modules" / "VTK"
        home.mkdir(parents=True)
        pb = json.loads(tail(HERE, "VTK_Params").read_text(encoding="utf-8"))
        pb["params"]["extra_sources"] = {}  # 暫存樹只有兩家假工具
        write_json(home / "VTK_Params_v0100.json", pb)
        before = {p.name: sha_lf(p) for p in reg.glob("*.py")}
        c = Ctx(home, via)
        chk("① 參數從參數冊尾版讀(SDD L4)", c.param_ok and c.prm["code_prefix"] == "VTK-TOOL-", c.param_note)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            r0 = sync(c, False)
        chk("② 乾跑零寫入", r0 == 0 and not (home / "tools").exists() and not c.reg_path.exists(), buf.getvalue()[-200:])
        with contextlib.redirect_stdout(io.StringIO()):
            r1 = sync(c, True)
        g = c.register()
        chk("③ --apply:整條鏈複製、自己發號 VTK-TOOL-0001/0002", r1 == 0 and (home / "tools/alpha/AAA_Tool_v0100.py").is_file()
            and g["families"] == {"alpha": "VTK-TOOL-0001", "beta": "VTK-TOOL-0002"} and len(g["rows"]) == 2, g.get("families"))
        with contextlib.redirect_stdout(io.StringIO()):
            sync(c, True)
        chk("④ 再同步:沒變就不加列、號不變", len(c.register()["rows"]) == 2)
        (reg / "AAA_Tool_v0102.py").write_text((reg / "AAA_Tool_v0101.py").read_text(encoding="utf-8"), encoding="utf-8")
        (reg / "VIA_ToolVersion_Lock_v0100.json").write_text((reg / "VIA_ToolVersion_Lock_v0100.json").read_text(encoding="utf-8").replace("v0101", "v0102"), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            sync(c, True)
        g = c.register()
        chk("⑤ 來源出新版:加檔加一列,號不變(只增)", len(g["rows"]) == 3 and g["rows"][-1]["code"] == "VTK-TOOL-0001" and g["rows"][-1]["tail"] == "AAA_Tool_v0102.py")
        keep = sha_lf(c.reg_path)
        (reg / "BBB_Tool_v0100.py").write_text((reg / "BBB_Tool_v0100.py").read_text(encoding="utf-8") + "# changed\n", encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            r6 = sync(c, True)
        chk("⑥ 同名不同內容 = 衝突 · 紅 · 號冊零寫入", r6 == 1 and "CONFLICT" in buf.getvalue() and sha_lf(c.reg_path) == keep)
        (reg / "BBB_Tool_v0100.py").write_text((reg / "BBB_Tool_v0100.py").read_text(encoding="utf-8").replace("# changed\n", ""), encoding="utf-8")
        cp = subprocess.run([sys.executable, str(home / "tools/alpha/AAA_Tool_v0102.py"), "x1"], capture_output=True, text=True,
                            env=dict(os.environ, VIA_FROM_VTK="YES"))
        chk("⑦ run:跑的是 VTK 副本,參數照傳,帶 VTK 自己的入口標記", cp.returncode == 0 and "AAA YES x1" in cp.stdout, cp.stderr[-200:])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            r8 = drill(c)
        o = buf.getvalue()
        chk("⑧ drill:不靠 VCGC 的家亮綠、靠 CGC_*.py 的家亮紅並點名、暫存樹裡 CGC_*.py = 0",
            r8 == 1 and re.search(r"GREEN\s+alpha", o) and re.search(r"RED\s+beta", o) and "CGC_*.py = 0" in o, o[-300:])
        (via / "Register-VIA-Commands-v0001.ps1").write_text(
            'function global:via-a { $e = Get-VIANewest "$VIA\\x" "CGC_MDL001_Foo_v*.py"; Invoke-VIAPython $e @args }\n'
            'function global:via-b {\n  Get-ChildItem "$VIA" | ForEach-Object { Write-Host "{" }\n}\n'
            'function global:via-c { via-a status }\nfunction global:via-d { Remove-Item x }\nSet-Alias -Name 甲 -Value via-a -Scope Global -Force\n', encoding="utf-8")
        (via / "Register-VIA-Commands-v0002.ps1").write_text('. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0001.ps1")\n'
            'function global:via-d { Invoke-VIAPython (Get-VIANewest "$VIA\\x" "VDF_MDL002_Bar_v*.py") @args }\n', encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            r9 = commands(c)
        j = json.loads(next((via / "VIA_Reports/vtk").glob("VTK_ShortCommands_*.json")).read_text(encoding="utf-8"))
        sh = {r["command"]: (r["shape"], r["owner"]) for r in j["rows"]}
        chk("⑨ 短指令:照 dot-source 版本鏈算,同名以尾版定義生效;三數對得上、形狀與歸屬判對(字串裡的大括號不算)",
            r9 == 0 and j["meta"]["three"]["should"] == 4 and len(j["meta"]["chain"]) == 2 and sh == {
                "via-a": ("PY-LAUNCH", "VCGC"), "via-b": ("PS-LOGIC", "?"), "via-c": ("ALIAS", "?"), "via-d": ("PY-LAUNCH", "VDF")}, sh)
        chk("⑩ 來源檔一字不動(複製不是搬走)", all(sha_lf(reg / n) == h for n, h in before.items() if n != "BBB_Tool_v0100.py"))
        a, b = tmp / "lf.txt", tmp / "crlf.txt"
        a.write_bytes(b"x\ny\n")
        b.write_bytes(b"x\r\ny\r\n")
        chk("⑪ 雜湊先統一 LF(CRLF 檔同值)", sha_lf(a) == sha_lf(b))
        (home / ".VTK_Register.lock").write_text("999")
        try:
            with book_lock(home, 0.5):
                got = True
        except TimeoutError:
            got = False
        chk("⑫ 別人的鎖在:拿不到就放棄,鎖檔不刪", not got and (home / ".VTK_Register.lock").exists())
        (home / ".VTK_Register.lock").unlink()
        chk("⑬ 加速器執行時真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            main(["verbs", "--json"])
        chk("⑭ verbs --json 自報全部動詞(裁定 ⑬ 路由)", set(json.loads(buf.getvalue())["verbs"]) == set(VERBS))
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)
    ok = all(res)
    print("[selftest] %s · %d 敗 · %s" % ("GREEN" if ok else "RED", res.count(False), ENGINE))
    return 0 if ok else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[0] in ("--selftest", "selftest"):
        return selftest() if a else status(Ctx())
    v, rest = a[0], a[1:]
    if v == "verbs":
        if "--json" in rest:
            print(json.dumps({"system": "VTK", "entry": ENGINE, "verbs": VERBS}, ensure_ascii=False))
        else:
            for k, d in VERBS.items():
                print("  %-9s %s" % (k, d))
        return 0
    c = Ctx()
    if v == "status":
        return status(c)
    if v == "tools":
        for fam, r in sorted(c.latest(c.register()).items()):
            print("  %-11s %-14s %-48s ← %s" % (fam, r["code"], r["tail"], r["source"]["path"]))
        return 0
    if v == "sync":
        return sync(c, "--apply" in rest)
    if v == "run":
        return run(c, rest)
    if v == "drill":
        return drill(c)
    if v == "commands":
        return commands(c)
    print("[VTK] 未知動詞 %s;可用:%s" % (v, " · ".join(VERBS)))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
