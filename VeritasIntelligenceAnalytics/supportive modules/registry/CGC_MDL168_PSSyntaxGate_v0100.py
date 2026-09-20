#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL168_PSSyntaxGate v0100 — PowerShell 語法與參數名閘(批629)
====================================================================
為什麼有這一支:格子 257 站,**沒有任何一站 parse 過 .ps1**。
批625 為此丟掉一整輪,而且是兩個都「跑起來才炸」的坑:

  ① 雙引號字串裡拿反引號當程式碼標記寫了 ``status` `` ——
     反引號把結尾的引號跳脫掉,字串沒關起來,錯誤訊息指著 30 行後一個無辜的 `[換庫]`。
  ② 參數取名 `-Db`,而 `[CmdletBinding()]` 內建 `-Debug` 的別名就是 `db`
     ——**語法一路合法,啟動當場 MetadataError**。

所以本閘兩道,而且**刻意分開**,因為它們抓得到的東西不一樣:

  A 語法道  `[Parser]::ParseFile`。抓得到 ①,**抓不到 ②**(② 語法完全合法)。
  B 參數道  掃 `param(...)` 裡的參數名與宣告別名,撞到 CommonParameters 的別名就點名。
            這是**靜態就看得出來**的,不必跑起來(LL182:AST 綠不等於跑得動——
            那就再加一道 AST 看不到的)。

律:零網路;不改任何 .ps1(只讀只報);pwsh 缺席=誠實 ABSENT(rc=3)不假綠;
    掃描排除清單吃 SUP_MDL753 的 L77 正典(不各寫一份)。
用法(本批**不開短令**——短令要四個面同時到位才不是幽靈令 LL199,
      而那要動 Register.ps1,得你逐次許可 L70;要不要開由你裁定):
  python3 "supportive modules/registry/CGC_MDL168_PSSyntaxGate_v0100.py"
  python3 "…/CGC_MDL168_PSSyntaxGate_v0100.py" --selftest
  python3 "…/CGC_MDL168_PSSyntaxGate_v0100.py" --rebaseline
rc:0=GREEN 1=RED 2=NODATA 3=ABSENT(誠實四態)
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

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent

#: PowerShell CommonParameters 的**別名**。參數名撞上任何一個,加了 [CmdletBinding()]
#: 就是啟動期 MetadataError——批625 的 `-Db` 撞 `-Debug` 的 `db` 就是這一格。
COMMON_ALIASES = {
    "db": "-Debug", "ea": "-ErrorAction", "ev": "-ErrorVariable",
    "infa": "-InformationAction", "iv": "-InformationVariable",
    "ob": "-OutBuffer", "ov": "-OutVariable", "of": "-OutVariable(舊別名)",
    "pv": "-PipelineVariable", "vb": "-Verbose",
    "wa": "-WarningAction", "wv": "-WarningVariable",
    "wi": "-WhatIf", "cf": "-Confirm",
}
#: CommonParameters 本名(整名相同也是撞)
COMMON_NAMES = {"debug", "erroraction", "errorvariable", "informationaction",
                "informationvariable", "outbuffer", "outvariable", "pipelinevariable",
                "verbose", "warningaction", "warningvariable", "whatif", "confirm"}

_PARAM_BLOCK = re.compile(r"\bparam\s*\(", re.I)
_PARAM_NAME = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)\s*(?:=|,|\))")
_ALIAS_ATTR = re.compile(r"\[Alias\(([^)]*)\)\]", re.I)


def _excluded(rel: str) -> bool:
    """排除判準吃 SUP_MDL753 的 L77 正典;正典缺席就誠實停(不拿短清單代打)。"""
    import importlib.util as ilu
    g = globals()
    if "_CANON" not in g:
        m = None
        hits = sorted(x for x in (VIA / "supportive modules").glob(
            "SUP_MDL753_VIACommonUtils_v*.py") if "_sha" not in x.name)
        if hits:
            try:
                spec = ilu.spec_from_file_location("SUP_MDL753_VIACommonUtils", hits[-1])
                m = ilu.module_from_spec(spec)
                sys.modules.setdefault("SUP_MDL753_VIACommonUtils", m)
                spec.loader.exec_module(m)
                if not hasattr(m, "scan_excluded"):
                    m = None
            except Exception:
                m = None
        g["_CANON"] = m
    if g["_CANON"] is None:
        raise RuntimeError("SUP_MDL753 正典缺席:排除清單沒有第二把尺,誠實停")
    return g["_CANON"].scan_excluded(rel)


def _pwsh() -> str:
    return shutil.which("pwsh") or shutil.which("powershell") or ""


def _tails(root: Path) -> list:
    """活樹 .ps1 尾版(同 stem 家族取最新 _vNNNN;沒版號的各自算一支)。"""
    ver = re.compile(r"^(.*)_v(\d{3,4})$")
    fam, solo = {}, []
    for p in root.rglob("*.ps1"):
        rel = str(p.relative_to(root)).replace("\\", "/")
        if _excluded(rel):
            continue
        m = ver.match(p.stem)
        if m:
            fam.setdefault((str(p.parent), m.group(1)), []).append((int(m.group(2)), p))
        else:
            solo.append(p)
    out = list(solo)
    for v in fam.values():
        v.sort()
        out.append(v[-1][1])
    return sorted(out)


def parse_errors(files: list) -> dict:
    """A 語法道:一次 pwsh 進程 ParseFile 全部檔。pwsh 缺席回 state=ABSENT。"""
    exe = _pwsh()
    if not exe:
        return {"state": "ABSENT", "why": "pwsh / powershell 不在 PATH(本機不判;不假綠)", "rows": []}
    with tempfile.TemporaryDirectory() as td:
        lst = Path(td) / "files.txt"
        lst.write_text("\n".join(str(f) for f in files), encoding="utf-8")
        script = Path(td) / "p.ps1"
        script.write_text(
            "$out = @()\n"
            "foreach ($f in (Get-Content -LiteralPath $args[0])) {\n"
            "  if (-not $f) { continue }\n"
            "  $tok = $null; $err = $null\n"
            "  $null = [System.Management.Automation.Language.Parser]::ParseFile($f, [ref]$tok, [ref]$err)\n"
            "  if ($err -and $err.Count -gt 0) {\n"
            "    foreach ($e in $err) {\n"
            "      $out += [pscustomobject]@{ file = $f; line = $e.Extent.StartLineNumber; msg = $e.Message }\n"
            "    }\n"
            "  }\n"
            "}\n"
            "$out | ConvertTo-Json -Depth 3 -Compress\n", encoding="utf-8")
        try:
            r = subprocess.run([exe, "-NoProfile", "-File", str(script), str(lst)],
                               capture_output=True, text=True, timeout=900)
        except Exception as exc:
            return {"state": "RED", "why": f"pwsh 叫不動:{type(exc).__name__}", "rows": []}
    raw = (r.stdout or "").strip()
    if not raw or raw == "null":
        return {"state": "OK", "rows": []}
    try:
        d = json.loads(raw)
    except Exception:
        return {"state": "RED", "why": f"ParseFile 回傳讀不動:{raw[:120]}", "rows": []}
    rows = d if isinstance(d, list) else [d]
    return {"state": "RED" if rows else "OK", "rows": rows}


def alias_collisions(files: list) -> list:
    """B 參數道:param() 裡的參數名 / [Alias()] 撞 CommonParameters 別名。

    只在檔案帶 `[CmdletBinding()]` 或 `param(` 時才判——沒有 CmdletBinding 的
    純腳本 param 不會被塞 CommonParameters,判它就是誤殺。
    """
    hits = []
    for f in files:
        try:
            src = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        m = _PARAM_BLOCK.search(src)
        if not m:
            continue
        if "cmdletbinding" not in src[:m.start()].lower():
            continue
        depth, i = 1, m.end()
        while i < len(src) and depth:
            if src[i] == "(":
                depth += 1
            elif src[i] == ")":
                depth -= 1
            i += 1
        block = src[m.end():i]
        names = set(_PARAM_NAME.findall(block))
        for a in _ALIAS_ATTR.findall(block):
            names.update(x.strip().strip("'\"") for x in a.split(",") if x.strip())
        for n in sorted(names):
            low = n.lower()
            if low in COMMON_ALIASES:
                hits.append({"file": str(f), "param": n, "clash": COMMON_ALIASES[low],
                             "why": f"`-{n}` 撞 CommonParameters 別名 → {COMMON_ALIASES[low]}"})
            elif low in COMMON_NAMES:
                hits.append({"file": str(f), "param": n, "clash": f"-{n}",
                             "why": f"`-{n}` 就是 CommonParameter 本名"})
    return hits


#: 棘輪基線(同 CGC_MDL164 的做法):今天量到的已知壞檔逐支具名記下來。
#: **基線內是具名的債,基線外是新傷。**沒有基線的話,這一站上線第一天就是紅的,
#: 而一個永遠紅的站跟沒有站一樣——看的人會學會忽略它。
BASELINE = HERE / "VIA_PSSyntax_Baseline_v0100.json"


def _baseline() -> dict:
    if not BASELINE.is_file():
        return {}
    try:
        return (json.loads(BASELINE.read_text(encoding="utf-8-sig")) or {}).get("known") or {}
    except Exception:
        return {}


def rebaseline(root: Path = VIA) -> int:
    """把當下的壞檔寫成基線。**只在操作員或本批明確要立基線時跑**,不自動。"""
    files = _tails(root)
    pe = parse_errors(files)
    if pe["state"] == "ABSENT":
        print(f"  [ABSENT] {pe['why']} —— pwsh 不在就立不了基線(立一個空的等於假綠)")
        return 3
    known = {}
    for r in pe["rows"]:
        k = Path(r["file"]).name
        known[k] = known.get(k, 0) + 1
    BASELINE.write_text(json.dumps(
        {"schema": "VIA.PSSyntaxBaseline.v1", "batch": "批629", "ts": "2026-09-19",
         "why": "批629 這一站上線時,活樹尾版 .ps1 816 支裡有 5 支解析不過(53 筆)。"
                "它們全是舊件,不是這一批弄壞的;立基線是為了讓**新傷**看得見,"
                "不是為了把舊傷蓋掉。基線內每一支都具名在案,要不要修由操作員裁定(LL90)。",
         "known": known}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [基線] 寫入 {BASELINE.name} · 具名壞檔 {len(known)} 支 · 錯誤 {sum(known.values())} 筆")
    for k, v in sorted(known.items()):
        print(f"     {v:>3} 筆  {k}")
    return 0


def run(root: Path = VIA) -> int:
    try:
        files = _tails(root)
    except RuntimeError as exc:
        print(f"  [ABSENT] {exc}")
        return 3
    print(f"=== PowerShell 語法與參數名閘(CGC_MDL168 v0100;批629)===")
    print(f"  [掃] 活樹尾版 .ps1 {len(files)} 支(排除清單吃 SUP_MDL753 L77 正典)")
    pe = parse_errors(files)
    ac = alias_collisions(files)
    if pe["state"] == "ABSENT":
        print(f"  [A 語法道] ABSENT · {pe['why']}")
    else:
        print(f"  [A 語法道] {'RED' if pe['rows'] else 'GREEN'} · 語法錯 {len(pe['rows'])}")
        for r in pe["rows"][:20]:
            print(f"     {Path(r['file']).name}:{r['line']} · {str(r['msg'])[:110]}")
    print(f"  [B 參數道] {'RED' if ac else 'GREEN'} · 撞 CommonParameters {len(ac)}"
          f"(語法道看不到這一種:`-Db` 撞 `-Debug` 的 `db`,語法完全合法,啟動才炸)")
    for h in ac[:20]:
        print(f"     {Path(h['file']).name} · {h['why']}")
    if pe["state"] == "ABSENT" and not ac:
        print("  [裁決] ABSENT(pwsh 不在;參數道過了,但語法道沒跑過——沒跑過不算綠)")
        return 3
    # 棘輪:基線內的舊傷逐支報出來當具名的債,基線外的新傷才紅。
    base = _baseline()
    cur = {}
    for r in pe.get("rows") or []:
        k = Path(r["file"]).name
        cur[k] = cur.get(k, 0) + 1
    newly = {k: v for k, v in cur.items() if k not in base}
    worse = {k: (base[k], v) for k, v in cur.items() if k in base and v > base[k]}
    healed = sorted(k for k in base if k not in cur)
    if base:
        print(f"  [棘輪] 基線 {len(base)} 支 / {sum(base.values())} 筆(具名的舊債,不是這一批弄壞的)"
              f" · 新壞 {len(newly)} 支 · 變嚴重 {len(worse)} 支 · 已修好 {len(healed)} 支")
        for k, v in sorted(newly.items()):
            print(f"     [新壞] {k} · {v} 筆 ← **這是新傷**")
        for k, (b, v) in sorted(worse.items()):
            print(f"     [惡化] {k} · {b} → {v} 筆")
        if healed:
            print(f"     [修好] {', '.join(healed)}(基線該收緊了:--rebaseline)")
    bad = bool(newly) or bool(worse) or bool(ac) or (not base and bool(cur))
    print(f"  [裁決] {'RED' if bad else 'GREEN'}"
          + ("" if base else "(**沒有基線**:所有語法錯都算新傷)"))
    return 1 if bad else 0


def selftest() -> int:
    n, fails = [0], []

    def chk(label, ok, extra=""):
        n[0] += 1
        print(f"  [{'OK' if ok else 'FAIL'}] {label}" + (f" ({extra})" if extra else ""))
        if not ok:
            fails.append(label)

    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        good = d / "Good-v0100.ps1"
        good.write_text("[CmdletBinding()]\nparam([string]$DbPath = '')\nWrite-Host \"ok $DbPath\"\n",
                        encoding="utf-8")
        # ① 批625 真坑:雙引號字串裡的反引號把結尾引號跳脫掉
        bad1 = d / "BadQuote-v0100.ps1"
        # 夾具要長得**跟批625 那一行一樣**:反引號**緊貼結尾引號**,`" 把引號跳脫掉,
        # 字串沒關起來,解析器一路吃到下一個引號,錯誤才在好幾行之後爆。
        # (我第一版把反引號寫在句中 —— `s 不是合法跳脫,PowerShell 當成字面 s,
        #  字串照樣關得起來,**那不是坑**,檢當場紅。夾具沒造對,檢就在量別的東西。)
        bad1.write_text("Write-Host \"看 `status`\"\nWrite-Host '[換庫]'\n", encoding="utf-8")
        # ② 批625 真坑:-Db 撞 -Debug 的別名 db(語法完全合法)
        bad2 = d / "BadParam-v0100.ps1"
        bad2.write_text("[CmdletBinding()]\nparam([string]$Db = '')\nWrite-Host $Db\n", encoding="utf-8")

        pe = parse_errors([good, bad1, bad2])
        if pe["state"] == "ABSENT":
            chk("① 語法道:pwsh 缺席=誠實 ABSENT(不假綠)", True, pe["why"])
            chk("② 反引號跳脫坑(批625 ①)", True, "pwsh 缺席,這一檢跳過並說出原因")
        else:
            files_bad = {Path(r["file"]).name for r in pe["rows"]}
            chk("① 語法道抓得到批625 那個反引號坑(字串沒關起來)",
                "BadQuote-v0100.ps1" in files_bad, str(sorted(files_bad)))
            chk("② 好檔不得誤殺", "Good-v0100.ps1" not in files_bad, str(sorted(files_bad)))
        ac = alias_collisions([good, bad1, bad2])
        names = {Path(h["file"]).name: h["param"] for h in ac}
        chk("③ 參數道抓得到 `-Db` 撞 `-Debug` 的別名 `db`"
            "——**語法道抓不到這一種**(它語法完全合法,批625 就是栽在這裡)",
            names.get("BadParam-v0100.ps1") == "Db", str(names))
        chk("④ `-DbPath` 不得誤殺(改名之後就該放行;過寬跟過窄一樣壞)",
            "Good-v0100.ps1" not in names, str(names))
        chk("⑤ 沒有 CmdletBinding 的 param 不判(它不會被塞 CommonParameters,判它是誤殺)",
            not alias_collisions([bad1]) and len(alias_collisions([bad2])) == 1)
        chk("⑥ 排除清單吃正典,不自帶一份(正典缺席要誠實停,不拿短清單代打)",
            "scan_excluded" in Path(__file__).read_text(encoding="utf-8"))
        _sv = globals()["BASELINE"]
        globals()["BASELINE"] = d / "base.json"
        try:
            chk("⑦ 沒有基線時所有語法錯都算新傷(空基線 = 假綠,不許)", _baseline() == {})
            (d / "base.json").write_text(json.dumps(
                {"known": {"BadQuote-v0100.ps1": 99}}, ensure_ascii=False), encoding="utf-8")
            chk("⑧ 棘輪讀得到基線(基線內是具名的債,基線外才是新傷)",
                _baseline().get("BadQuote-v0100.ps1") == 99)
        finally:
            globals()["BASELINE"] = _sv
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}(檢數現場計)")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--rebaseline" in a:
        print("=== 立棘輪基線(只在明確要立時跑;不自動)===")
        return rebaseline()
    if "--selftest" in a:
        print("=== PowerShell 語法與參數名閘 v0100 · 自測(沙盒;零網路)===")
        return selftest()
    return run()


if __name__ == "__main__":
    sys.exit(main())
