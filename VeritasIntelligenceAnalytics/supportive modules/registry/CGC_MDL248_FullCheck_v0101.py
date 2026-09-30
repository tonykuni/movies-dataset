#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL248_FullCheck v0101 — 薄尾:⓪ 三橋段多一項「PS 自擋開頁」(Z290 · 操作員 2026-09-30)

操作員:「這個ＰＳ指令一定沒有加加速模板自動跳出ＨＴＭＬ」。pwsh 實測屬實:整合全景實測 PS v0100 先設 VIA_NO_OPEN=1
(不讓引擎各自跳頁),到 finally 才還原;同一行程的 PS 加速器模組(PS-ACCEL 橋 · VIA_PS_PyProgress_Module · 命令冊都會載)
裝了零跳出閘(批366),看到 VIA_NO_OPEN=1 就把不帶模組名的 Invoke-Item / Start-Process 頁面目標靜默略過 → 總報告從沒跳出。
全樹掃:唯一入口 v0108 · RunAll v0102 · 兩支收尾鏈 PS 同病;v0100 的 ⓪ 段只數橋掛了沒有,頁被自己吃掉照綠。
  ① ⓪ 段多一項:PS 尾版(家族最新;不含 VIA_Reports / history / intake / SCOPE_COPY)裡「自設 VIA_NO_OPEN=1 之後、沒先換回
     原值,就用不帶模組名的 Invoke-Item / Start-Process / ii 開頁面目標」→ 紅,點名檔 · 行。帶模組名
     (Microsoft.PowerShell.Management\\Invoke-Item)或開頁前已還原 → 不算。報告 BRIDGES_latest.json 多 own_page 欄。
  ② 其餘照 v0100(六段 · 紅了照跑 · 讀正主本輪報告不重判 · 紀錄冊只增)。報告 engine 記本版。只收 VCGC 呼叫;零網路。
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

import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(__file__).stem
_STEM = "CGC_MDL248_FullCheck"
_PY_VNUM = re.compile(r"_v(\d+)$")


def _vn(path) -> int:
    m = _PY_VNUM.search(Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vn(p) < _vn(__file__)), key=_vn)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
PRIOR_ENGINE = PRIOR.ENGINE
VIA = PRIOR.VIA


def __getattr__(name: str):
    return getattr(PRIOR, name)


# ---------------------------------------------------------------- ① PS 自擋開頁
PS_VNUM = re.compile(r"[-_]v(\d{4})$")
SKIP_PARTS = {"history", "VIA_Reports", "SCOPE_COPY", ".git", "intake"}
SET1_RX = re.compile(r"""\$env:VIA_NO_OPEN\s*=\s*["']?1["']?\s*(?:$|[;#)}])""", re.I)
RESTORE_RX = re.compile(r"""\$env:VIA_NO_OPEN\s*=\s*(?!\s)(?!["']?1["']?\s*(?:$|[;#)}]))|Remove-Item\s+(?:-(?:Literal)?Path\s+)?Env:\\?VIA_NO_OPEN"""
                        r"""|\[Environment\]::SetEnvironmentVariable\(\s*["']VIA_NO_OPEN"""
                        r"""|\$env:VIA_NO_OPEN\s*-(?:eq|ne)\b""", re.I)  # 最後一種:開頁前明寫判斷 VIA_NO_OPEN(VIA.ps1 零跳出律)= 有意識處理,不算被閘吃掉
OPEN_RX = re.compile(r"(?<![\\\w$.-])(Invoke-Item|Start-Process|ii)(?=\s)", re.I)
PAGE_RX = re.compile(r"""\.(?:html?|url|svg|pdf)\b|https?:|file:|\$\w*(?:page|html|url|report|prev|verify|summary)\w*|\$u\b""", re.I)


def _ps_tails(via: Path) -> list:
    fam = {}
    for p in via.rglob("*.ps1"):
        rel = p.relative_to(via)
        if SKIP_PARTS & set(rel.parts) or not p.is_file():
            continue
        m = PS_VNUM.search(p.stem)
        key = (str(rel.parent), PS_VNUM.sub("", p.stem))
        n = int(m.group(1)) if m else -1
        if key not in fam or n > fam[key][0]:
            fam[key] = (n, p)
    return sorted(p for _n, p in fam.values())


def own_page_hits(text: str) -> list:
    """(set line, open line, snippet) for every page open that runs after this file set VIA_NO_OPEN=1 without restoring it first."""
    lines = text.splitlines()
    live = [not ln.lstrip().startswith("#") for ln in lines]
    sets = [(i, m.end()) for i, ln in enumerate(lines) if live[i] for m in SET1_RX.finditer(ln)]
    if not sets:
        return []
    hits = []
    for i, ln in enumerate(lines):
        if not live[i] or i < sets[0][0]:
            continue
        for m in OPEN_RX.finditer(ln):
            if not PAGE_RX.search(ln[m.end():]):
                continue
            prior = [s for s in sets if (s[0], s[1]) <= (i, m.start())]
            if not prior:
                continue
            si, sc = prior[-1]  # 開頁前最近一次設 1 的位置;從那裡到開頁之間有還原才算放行
            between = [lines[si][sc:]] + [lines[k] for k in range(si + 1, i) if live[k]] if si < i else []
            between.append(ln[sc if si == i else 0:m.start()])
            if any(RESTORE_RX.search(b) for b in between):
                continue
            hits.append((si + 1, i + 1, ln.strip()[:120]))
            break
    return hits


def own_page_scan(via: Path) -> list:
    out = []
    for p in _ps_tails(Path(via)):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for s, o, snip in own_page_hits(text):
            out.append({"file": str(p.relative_to(via)), "set": s, "open": o, "text": snip})
    return out


_PRIOR_BRIDGES_REPORT = PRIOR.bridges_report
_PRIOR_READ_BRIDGES = PRIOR.read_bridges


def bridges_report(via: Path, out1: str, out2: str) -> dict:
    d = _PRIOR_BRIDGES_REPORT(via, out1, out2)
    d["own_page"] = own_page_scan(via)
    return d


def read_bridges(d: dict) -> tuple:
    lamp, summ, probs = _PRIOR_READ_BRIDGES(d)
    hits = d.get("own_page")
    if hits is None:  # v0100 寫的報告沒量這一項 → 照實說,不冒充 0
        return lamp, summ + " · 自擋開頁 未量", probs
    for h in hits:
        probs.append({"where": "PS 自擋開頁", "item": h["file"], "lamp": "RED", "detail": f"L{h['set']} 設 VIA_NO_OPEN=1 → L{h['open']} {h['text']}",
                      "next": "開自己的頁改用 Microsoft.PowerShell.Management\\Invoke-Item(呼叫端原值不是 1 才開),或開頁前把 VIA_NO_OPEN 換回原值(Z290)"})
    summ += f" · 自擋開頁 {len(hits)}"
    return ("RED" if hits else lamp), summ, probs


def _wire() -> None:
    PRIOR.bridges_report = bridges_report          # 前版 run_step 經模組全域叫
    PRIOR.read_bridges = read_bridges
    PRIOR.READERS_EXTRA = dict(PRIOR.READERS_EXTRA, bridges=read_bridges)  # 前版 _finish 經這張表叫(存的是函式本體)


_wire()


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    PRIOR.ENGINE = ENGINE  # 報告與紀錄冊的 engine 記本版
    return PRIOR.main(args)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    bad_ii = '$env:VIA_NO_OPEN = "1"\n$page = "x.html"\ntry { Invoke-Item -LiteralPath $page } catch { }\n'
    bad_sp = '$env:VIA_FROM_VCGC = "YES"; $env:VIA_NO_OPEN = "1"\nif ($env:OS -eq "Windows_NT") { try { Start-Process -FilePath $page } catch { } }\n$env:VIA_NO_OPEN = $prev\n'
    cases = {
        "launchers/Bad-Ii-v0100.ps1": bad_ii,
        "launchers/Bad-Sp-v0100.ps1": bad_sp,
        "launchers/Good-Qualified-v0100.ps1": '$env:VIA_NO_OPEN = "1"\nMicrosoft.PowerShell.Management\\Invoke-Item -LiteralPath $page\n',
        "launchers/Good-Restored-v0100.ps1": '$env:VIA_NO_OPEN = "1"\n& $py\n$env:VIA_NO_OPEN = $prev.OPEN\nInvoke-Item -LiteralPath $page\n',
        "launchers/Good-SameLine-v0100.ps1": '$env:VIA_NO_OPEN = "1"\n$env:VIA_NO_OPEN = $null; Invoke-Item $page\n',
        "launchers/Good-NoSet-v0100.ps1": 'Invoke-Item -LiteralPath $page\n',
        "launchers/Good-Comment-v0100.ps1": '$env:VIA_NO_OPEN = "1"\n# Invoke-Item -LiteralPath $page\n',
        "launchers/Good-Worker-v0100.ps1": '$env:VIA_NO_OPEN = "1"\nStart-Process -FilePath $py -ArgumentList $a -NoNewWindow\n',
        "launchers/Good-SetLater-v0100.ps1": 'Invoke-Item $page\n$env:VIA_NO_OPEN = "1"\n',
        "launchers/Bad-Reset-v0100.ps1": '$env:VIA_NO_OPEN = "1"\n$env:VIA_NO_OPEN = $prev\n$env:VIA_NO_OPEN = "1"\nInvoke-Item -LiteralPath $page\n',
        "launchers/Bad-SameLine-v0100.ps1": '$env:VIA_NO_OPEN = "1"; Invoke-Item $page\n',
        "launchers/Good-Checked-v0100.ps1": 'if ($env:VIA_OPEN_PAGES -ne "1") { $env:VIA_NO_OPEN = "1" }\nif ($env:VIA_NO_OPEN -eq "1") { Write-Host "未開" }\nelse { Start-Process "http://127.0.0.1:8765/" }\n',
        "Fam-v0100.ps1": bad_ii,
        "Fam-v0101.ps1": '$env:VIA_NO_OPEN = "1"\nMicrosoft.PowerShell.Management\\Invoke-Item $page\n',
        "VIA_Reports/handover/Old.ps1": bad_ii,
        "supportive modules/history/Old-v0100.ps1": bad_ii,
    }
    BAD = sorted(k for k in cases if k.startswith("launchers/Bad-"))
    with tempfile.TemporaryDirectory() as tmp:
        via = Path(tmp)
        for rel, text in cases.items():
            f = via / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding="utf-8")
        got = own_page_scan(via)
        files = sorted(h["file"] for h in got)
        chk("① 自擋開頁:自設 VIA_NO_OPEN=1 後不帶模組名開頁(Invoke-Item / Start-Process)= 抓;帶模組名 · 開頁前已還原(含同一行)· 沒設 · "
            "註解 · 開 python 工人 · 先開後設 · 明寫判斷 VIA_NO_OPEN(零跳出律)= 不抓;還原後又設 1 · 同一行先設後開 = 照抓", files == BAD, files)
        chk("② 只看家族尾版(Fam-v0100 舊版病了不算,尾版 v0101 好的)· VIA_Reports / history 不掃 · 點名到行",
            all("Fam-" not in f and "VIA_Reports" not in f and "history" not in f for f in files)
            and any(h["file"].endswith("Bad-Ii-v0100.ps1") and h["set"] == 1 and h["open"] == 3 for h in got), got[:1])
        d0 = {"rows": [{"kind": "ACCEL", "root": "r", "scanned": 3, "hooked": 3, "missing": 0}, {"kind": "PS-ACCEL", "root": ".", "scanned": 3, "hooked": 3, "missing": 0}],
              "plans": [], "loaded": {"引擎": "VeritasCeleritas_v1141.py", "網路": "VeritasAegisNexus_v1652.py"},
              "latest": {"引擎": "VeritasCeleritas_v1141.py", "網路": "VeritasAegisNexus_v1652.py"}}
        g = read_bridges(dict(d0, own_page=[]))
        r = read_bridges(dict(d0, own_page=got))
        u = read_bridges(d0)
        chk("③ ⓪ 段判燈:橋全掛 + 自擋 0 = 綠 · 有自擋 = 紅且每支進問題清單 · v0100 舊報告沒量 = 照實寫「未量」不冒充 0",
            g[0] == "GREEN" and g[1].endswith("自擋開頁 0") and r[0] == "RED" and sum(p["where"] == "PS 自擋開頁" for p in r[2]) == len(BAD)
            and u[0] == "GREEN" and u[1].endswith("未量"), (g[0], r[0], u[1][-12:]))

        def fake(v, argv, timeout):
            if "CGC_MDL124_BridgeSweeper" in argv:
                head = "  [加速] 引擎 VeritasCeleritas_v1141.py · x\n  [加速] 網路 VeritasAegisNexus_v1652.py · x\n"
                return 0, head + ("[橋掃] PS-ACCEL root=. · 掃 3 · 已掛 3 · 缺 0 · 計畫 0\n" if "--ps" in argv else "[橋掃] ACCEL root=r · 掃 3 · 已掛 3 · 缺 0\n")
            return 0, ""
        (via / "supportive modules" / "registry").mkdir(parents=True, exist_ok=True)
        (via / "supportive modules" / "registry" / "CGC_MDL124_BridgeSweeper_v0108.py").write_text("# stub\n", encoding="utf-8")
        (via / "supportive modules" / "VeritasCeleritas_v1141.py").write_text("#\n", encoding="utf-8")
        (via / "supportive modules" / "VeritasAegisNexus_v1652.py").write_text("#\n", encoding="utf-8")
        rep = PRIOR.run(via, only={0}, record=False, write=True, runner=fake, kit=None)
        b = json.loads((via / "VIA_Reports" / "fullcheck" / "BRIDGES_latest.json").read_text(encoding="utf-8"))
        s0 = rep["steps"][0]
        chk("④ 接線:前版 run → 本版 bridges_report(報告多 own_page)→ 本版 read_bridges(⓪ 紅並點名每一支)",
            len(b.get("own_page") or []) == len(BAD) and s0["lamp"] == "RED" and f"自擋開頁 {len(BAD)}" in s0["summary"]
            and {p["item"] for p in s0["problems"] if p["where"] == "PS 自擋開頁"} == set(BAD), s0["summary"][-40:])
    real = own_page_scan(VIA)
    print(f"  [實樹] PS 尾版自擋開頁 {len(real)} 支" + ("" if not real else ":" + " · ".join(f"{h['file']} L{h['open']}" for h in real[:6])))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 實樹掃得動(PS 尾版全掃不拋錯)· 加速器橋在 · 不碰 TA-Lib · 前版 v0100 在", isinstance(real, list) and "VIA:ACCEL-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and PRIOR_PATH.is_file(), len(_ps_tails(VIA)))
    mine = all(ok)
    PRIOR.ENGINE = PRIOR_ENGINE
    prior_rc = PRIOR.selftest()  # 前版自測在本版接線下照跑(三橋 · 六段 · 紀錄冊 · 頁 · 交接)
    print(f"  {ENGINE} selftest {sum(ok)}/{len(ok)} {'PASS' if mine and prior_rc == 0 else 'FAIL'}(前版 {PRIOR_PATH.stem} rc={prior_rc})")
    return 0 if mine and prior_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
