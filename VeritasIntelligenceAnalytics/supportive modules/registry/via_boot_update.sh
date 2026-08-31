#!/usr/bin/env bash
# via_boot_update.sh — VIA 開機自動更新器(批150;操作員令:不用固定時間,開啟系統即更新)
# SessionStart hook 背景喚起;每日首開才實跑(marker 防重複);log 落 VIA_Reports/boot_update_logs/
# 同意閘:操作員批123/137/150 自動更新常令授權,本腳本屬該令執行面。
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"   # repo 根
VIA="$ROOT/VeritasIntelligenceAnalytics"
ENG="$VIA/functional modules/VDF/engine"
MARK="$VIA/functional modules/VDF/output_hub/mega/.last_boot_update"
LOGDIR="$VIA/VIA_Reports/boot_update_logs"
TODAY="$(date +%Y-%m-%d)"

mkdir -p "$LOGDIR" "$(dirname "$MARK")"
if [ -f "$MARK" ] && [ "$(cat "$MARK" 2>/dev/null)" = "$TODAY" ]; then
  echo "[boot-update] $TODAY 已更(marker)=SKIP" >> "$LOGDIR/skip.log"
  exit 0
fi
echo "$TODAY" > "$MARK"    # 先佔位防並發雙跑
LOG="$LOGDIR/BOOT_$(date +%Y%m%d_%H%M%S).log"
export VIA_NET_CONSENT=YES VIA_SCRAPE_CONSENT=YES

newest() { ls "$ENG"/$1 2>/dev/null | sort | tail -1; }
{
  echo "=== VIA 開機更新 $TODAY(批150)==="
  # ⓪ 批164 環境自補(容器非持久=每日檢缺才裝;等效根+套件冊)
  echo "--- ⓪ 環境自補(批164)"
  mkdir -p /root/Downloads "/root/OneDrive/VeritasIntelligenceAnalytics/module"
  python3 - <<'PYENV'
import importlib.util, subprocess, sys
from pathlib import Path
need = [("networkx","networkx"),("dateparser","dateparser"),("spacy","spacy"),
        ("sumy","sumy"),("yake","yake"),("quantulum3","quantulum3")]
missing = [pip for mod,pip in need if importlib.util.find_spec(mod) is None]
req = Path(__file__).resolve()  # placeholder
if missing:
    subprocess.run([sys.executable,"-m","pip","install","--quiet","docopt-ng"],check=False)
    subprocess.run([sys.executable,"-m","pip","install","--quiet","--no-deps",*missing],check=False)
    subprocess.run([sys.executable,"-m","pip","install","--quiet","segtok","jellyfish","regex","tzlocal"],check=False)
if importlib.util.find_spec("spacy") is not None:
    try:
        import spacy; spacy.load("zh_core_web_sm")
    except Exception:
        subprocess.run([sys.executable,"-m","pip","install","--quiet",
          "https://github.com/explosion/spacy-models/releases/download/zh_core_web_sm-3.8.0/zh_core_web_sm-3.8.0-py3-none-any.whl"],check=False)
try:
    import duckdb
    p="/root/OneDrive/VeritasIntelligenceAnalytics/module/via.duckdb"
    if not Path(p).exists():
        duckdb.connect(p).close()
except Exception: pass
print("[env] 檢缺自補畢(pkuseg=C 輪誠實除外)")
PYENV
  cd "$ENG" || exit 1
  echo "--- ① OmniFetch 全車道";        python3 "$(newest 'VDF_ENG055_OmniFetch_v*.py')" run
  echo "--- ② 價格增量";                python3 "$(newest 'VDF_ENG054_TWDailyBackfill_v*.py')" run
  echo "--- ②b 調整後價格層(批178)";   python3 "$(newest 'VDF_ENG060_AdjPriceLayer_v*.py')" build
  echo "--- ②c 因子庫(批188)";         python3 "$(newest 'VDF_ENG061_FeatureStore_v*.py')" build
  echo "--- ③ 籌碼增量+衍生";           python3 "$(newest 'VDF_ENG056_ChipBackfill_v*.py')" run
  python3 "$(newest 'VDF_ENG056_ChipBackfill_v*.py')" --derive
  echo "--- ④ 主動 ETF 持股(PARTIAL 屬常態)"; python3 "$ENG/VDF_ENG051_ActiveTWETF_Holdings.py"
  # 批161 update:日更管線收編批154-155 引擎(checkpoint 增量制=每日只補新)
  echo "--- ⑥ 逐股成交值增量(批154)";  python3 "$(newest 'VDF_ENG057_TradingValueBackfill_v*.py')" run
  echo "--- ⑦ 分析師估值快照(批155)";  python3 "$(newest 'VDF_ENG059_EstimateBands_v*.py')" run
  echo "--- ⑦b 驗證共識庫(批176)";     python3 "$(ls "$VIA/functional modules/VRN"/VRN_ENG069_ConsensusDB_v*.py | sort | tail -1)" build
  echo "--- ⑦c Yahoo 共識(批194)";     python3 "$(ls "$VIA/functional modules/VRN"/VRN_ENG070_YahooConsensus_v*.py | sort | tail -1)" run
  echo "--- ⑦d 月營收(批194)";         python3 "$(newest 'VDF_ENG063_MonthlyRevenue_v*.py')" run
  echo "--- ⑦e 鉅亨 FactSet 共識(批199)"; python3 "$(ls "$VIA/functional modules/VRN"/VRN_ENG071_CnyesFusion_v*.py | sort | tail -1)" run
  echo "--- ⑧ 台股輪動日快照(批153)";  python3 "$(ls "$VIA/functional modules/GroupIndex/engine"/GRP_ENG040_GroupingRotationRunner_v*.py | sort | tail -1)" run tw
  echo "--- ⑧b 族群因子層(批193;於輪動快照後=成員冊當日鮮)"; python3 "$(newest 'VDF_ENG062_GroupFeatureLayer_v*.py')" build
  echo "--- ⑤ 對帳";                    python3 "$(newest 'VDF_ENG055_OmniFetch_v*.py')" --status
  # 批168:⑨ 同步 UI 重生(樞紐+五系統分頁=存證/庫/冊 join,與系統連動)
  echo "--- ⑨ 同步 UI 重生(批168)"
  REG="$VIA/supportive modules/registry"
  python3 "$(ls "$REG"/CGC_MDL088_SystemTestPages_v*.py | sort | tail -1)" run
  python3 "$(ls "$REG"/CGC_MDL090_SystemHub_v*.py | sort | tail -1)" run
  python3 "$(ls "$VIA/functional modules/VAP/engine"/VAP_ENG009_DashboardUI_v*.py | sort | tail -1)" run
  python3 "$(ls "$VIA/functional modules/VRN"/VRN_ENG068_DailyBrief_v*.py | sort | tail -1)" run
  echo "=== 畢(誠實三態見上)==="
} >> "$LOG" 2>&1
exit 0
