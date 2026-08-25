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
  cd "$ENG" || exit 1
  echo "--- ① OmniFetch 全車道";        python3 "$(newest 'VDF_ENG055_OmniFetch_v*.py')" run
  echo "--- ② 價格增量";                python3 "$(newest 'VDF_ENG054_TWDailyBackfill_v*.py')" run
  echo "--- ③ 籌碼增量+衍生";           python3 "$(newest 'VDF_ENG056_ChipBackfill_v*.py')" run
  python3 "$(newest 'VDF_ENG056_ChipBackfill_v*.py')" --derive
  echo "--- ④ 主動 ETF 持股(PARTIAL 屬常態)"; python3 "$ENG/VDF_ENG051_ActiveTWETF_Holdings.py"
  echo "--- ⑤ 對帳";                    python3 "$(newest 'VDF_ENG055_OmniFetch_v*.py')" --status
  echo "=== 畢(誠實三態見上)==="
} >> "$LOG" 2>&1
exit 0
