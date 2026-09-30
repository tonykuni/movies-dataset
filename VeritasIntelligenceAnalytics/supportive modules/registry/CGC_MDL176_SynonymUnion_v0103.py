#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL176_SynonymUnion v0103 — 薄尾:券商正典鍵對映再補 8 條(R34 重號裁定;前版 v0102 本體照讀)
操作員(R34,2026-09-30):「重號問題授權你可改 依據可用測試樣本如果跟他有關」。
實錄:編號稽核的冊內紅列 21 中 15 列是同義冊「一詞兩主(待裁定 key_alias)」—— 同一家券商在不同冊用了兩三種正典鍵拼法,
  一個詞就同時掛在兩三個主底下。與測試樣本直接相關:樣本索引 functional modules/VRN/StockReportBasicInfo.json(76 份)
  Broker 欄 Morgan Stanley 13 份 · Citi 2 份 —— 「morgan stanley」掛 MORGAN STANLEY / MS 兩主、「citi」掛 CITI / CITIGROUP 兩主,
  樣本的券商解不成一個主。
裁定(規則同批 665 / 678 已裁的 MEGABANK→MEGA · J.P. MORGAN→JPM:正典唯讀 = institution 冊的正典鍵才是正本命名空間,
  別的拼法降為別名,**不刪詞、不改號**):
  BAML · ML → BOFA(美國銀行美林證券;institution.foreign_brokers 正典鍵 BOFA;正典自己的 key_migration_map 早有 ML→BOFA)
  CITIGROUP → CITI(花旗;institution.foreign_brokers)
  FCB · FIRSTSEC → FIRST(第一金證券;institution.domestic_brokers)
  HNSC → HUANAN(華南永昌證券;institution.domestic_brokers)
  MORGAN STANLEY · MORGANSTANLEY → MS(摩根士丹利;institution.foreign_brokers)
評等的「強力賣出 → SELL / STRONG_SELL」不是兩主而是粗細兩軸(冊政策:評等記最細的鍵,粗尺當場投影),不在本表;由編號系統 v0111 判粒度。
本支只擴充前版的 KEY_ALIAS_RULINGS(同一張表:建冊 · 一扇門 resolve · 疊加層提案都讀它);其餘照 v0102。VIA_FROM_VCGC:經 VCGC run。不用 TA-Lib。
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
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL176_SynonymUnion"


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                  default=HERE / "CGC_MDL176_SynonymUnion_v0102.py")   # the prior this tail was cut from
_spec = importlib.util.spec_from_file_location("synunion_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


ENGINE = Path(__file__).stem
R34_WHO = "AI(R34 2026-09-30 操作員授權「重號問題授權你可改」;正典鍵為準 · 不刪詞 · 不改號)"
R34_RULINGS = {
    "BAML": ("BOFA", "美國銀行美林證券:knowledge.broker_dict_ext 的 BAML 與 institution 正典鍵 BOFA 是同一家;正典自己的 key_migration_map 已有 BOA/ML→BOFA"),
    "ML": ("BOFA", "美林(Merrill Lynch)併入美銀;knowledge.broker_dict 的 ML 與正典鍵 BOFA 同一家(正典 key_migration_map ML→BOFA)"),
    "CITIGROUP": ("CITI", "花旗:broker_list 的 CITIGROUP 與 institution 正典鍵 CITI 同一家;樣本索引 Citi 2 份"),
    "FCB": ("FIRST", "第一金證券:knowledge.broker_dict 的 FCB 與 institution.domestic_brokers 正典鍵 FIRST 同一家"),
    "FIRSTSEC": ("FIRST", "第一金證券:規則冊 extra_table 的 FIRSTSEC 與正典鍵 FIRST 同一家"),
    "HNSC": ("HUANAN", "華南永昌證券:knowledge.broker_dict 的 HNSC 與 institution.domestic_brokers 正典鍵 HUANAN 同一家"),
    "MORGAN STANLEY": ("MS", "摩根士丹利(大摩):broker_list 的 MORGAN STANLEY 與 institution 正典鍵 MS 同一家;樣本索引 Morgan Stanley 13 份"),
    "MORGANSTANLEY": ("MS", "同上;規則冊 extra_table 的 MORGANSTANLEY 拼法"),
}
for _k, (_c, _why) in R34_RULINGS.items():
    PRIOR.KEY_ALIAS_RULINGS.setdefault(_k, (_c, _why + " · 裁定 " + R34_WHO))


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    return PRIOR.main(a)


def selftest() -> int:
    import contextlib
    import io
    import json
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")
    def fails_of(mod) -> list:
        b = io.StringIO()
        with contextlib.redirect_stdout(b):
            mod.selftest()
        return sorted(ln.split("]", 1)[1].strip()[:12] for ln in b.getvalue().splitlines() if "[FAIL]" in ln)
    _sp = importlib.util.spec_from_file_location("synunion_baseline_" + ENGINE, _PRIOR_PATH)   # 前版單獨一份(不帶 R34 裁定)
    _base = importlib.util.module_from_spec(_sp)
    _sp.loader.exec_module(_base)
    before, after = fails_of(_base), fails_of(PRIOR)
    new_fail = [x for x in after if x not in before]
    chk("前版 v0102 自測:加了 R34 裁定沒有新增任何失敗項", not new_fail, "新增 " + " · ".join(new_fail))
    if before:
        print("  [既有] 前版單獨跑就紅的項(非本版造成,照實列出):" + " · ".join(before))
    ka = PRIOR.KEY_ALIAS_RULINGS
    chk("前版 6 條原樣在(只增)", all(k in ka for k in ("MEGABANK", "DAIWA SECURITIES", "J.P. MORGAN", "JPMORGAN", "JP", "IBF")))
    chk("R34 八條在,且都指向 institution 正典鍵", all(ka.get(k, ("",))[0] == c for k, (c, _) in R34_RULINGS.items()))
    chk("別名不指向別名(正典鍵自己不是別名)", not ({c for c, _ in ka.values()} & set(ka)))
    samples = {"Morgan Stanley": "MS", "Citi": "CITI", "美林": "BOFA", "第一金": "FIRST", "華南": "HUANAN", "大摩": "MS"}
    got = {}
    for tok, want in samples.items():
        with contextlib.redirect_stdout(io.StringIO()):
            r = PRIOR.resolve("broker", tok)
        got[tok] = (r.get("canonical"), r.get("state"))
    chk("樣本券商(StockReportBasicInfo 的 Morgan Stanley · Citi 等)經一扇門解成一個正典鍵",
        all(got[t][0] == w for t, w in samples.items()), json.dumps(got, ensure_ascii=False))
    body = Path(__file__).read_text(encoding="utf-8")
    chk("帶加速器橋 · VIA_FROM_VCGC 標記 · 不匯入 TA-Lib", "[VIA:ACCEL-BRIDGE" in body and "VIA_FROM_VCGC" in body
        and not re.search(r"^\s*(import|from)\s+" + "ta" + r"lib\b", body, re.M))
    print(f"[同義聯集 v0103] 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
