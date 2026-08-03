# ================================================
# VDF_ANCHOR_SAFETY v4.1 - 2026.02.13
# 禁止直接修改此區塊上方內容
# ================================================
# 快速修復 - main_accelerated.py Polars 語法錯誤
# 使用方式：.\Fix_Polars_Syntax.ps1

$ProjectRoot = 'C:\Users\tonyk\OneDrive\Desktop\VeritasReportNova'
$MainPy = Join-Path $ProjectRoot 'main_accelerated.py'
$BackupPy = Join-Path $ProjectRoot 'main_accelerated.py.backup'

Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        修復 Polars 語法錯誤                                  ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 備份原檔案
if (Test-Path $MainPy) {
    Write-Host "📋 備份原檔案..." -ForegroundColor Yellow
    Copy-Item -Path $MainPy -Destination $BackupPy -Force
    Write-Host "✅ 已備份至: $BackupPy" -ForegroundColor Green
}

Write-Host "🔧 寫入修復後的程式碼..." -ForegroundColor Cyan

$fixedCode = @'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPU Accelerator Demo - Polars First, Pandas Fallback (FIXED)
- 使用多核心 CPU 進行大資料聚合測試
- 優先使用 Polars；若無法匯入則 fallback 到 Pandas
- 修復版本：正確的 Polars DataFrame 建立語法
"""

import os
import sys
import time
import math

def detect_engine():
    try:
        import polars as pl
        return "polars", pl
    except Exception as e:
        print("[WARN] Polars 無法載入，改用 Pandas：", e)
        import pandas as pd
        return "pandas", pd

def main():
    cpu_cores = os.cpu_count() or 1
    print("════════════════════════════════════════════")
    print("  CPU Accelerator Demo (Polars → Pandas)")
    print("════════════════════════════════════════════")
    print(f"  CPU Cores detected : {cpu_cores}")
    print("")

    engine_name, engine = detect_engine()

    # 設定 Polars 最大執行緒數（若使用 Polars）
    if engine_name == "polars":
        os.environ["POLARS_MAX_THREADS"] = str(cpu_cores)
        print(f"[INFO] 使用 Polars 作為引擎，最大執行緒數：{cpu_cores}")
    else:
        print("[INFO] 使用 Pandas 作為兼容引擎")

    # 建立測試資料
    n_rows = 2_000_000
    n_groups = 1000
    print(f"[INFO] 準備產生測試資料：{n_rows:,} 列，{n_groups:,} 個 group")

    t0 = time.time()
    if engine_name == "polars":
        import polars as pl
        import numpy as np
        
        # 修復：使用 NumPy 建立資料，再轉換為 Polars DataFrame
        # 不能直接使用 pl.arange() 在 DataFrame 建構式中
        df = pl.DataFrame({
            "group": np.arange(n_rows, dtype=np.int64) % n_groups,
            "value": np.arange(n_rows, dtype=np.int64)
        })
    else:
        import pandas as pd
        import numpy as np
        df = pd.DataFrame({
            "group": np.arange(n_rows, dtype=np.int64) % n_groups,
            "value": np.arange(n_rows, dtype=np.int64)
        })
    t1 = time.time()
    print(f"[INFO] 建立 DataFrame 耗時：{t1 - t0:.3f} 秒")

    # 聚合計算（sum / mean / count）
    print("[INFO] 開始執行 groupby 聚合 (sum / mean / count)...")
    t2 = time.time()
    if engine_name == "polars":
        import polars as pl
        # Polars groupby + agg
        result = (
            df.group_by("group")
              .agg([
                  pl.col("value").sum().alias("sum_value"),
                  pl.col("value").mean().alias("mean_value"),
                  pl.len().alias("cnt")
              ])
              .sort("group")
        )
    else:
        result = (
            df
            .groupby("group", as_index=False)
            .agg(sum_value=("value", "sum"),
                 mean_value=("value", "mean"),
                 cnt=("value", "count"))
            .sort_values("group")
        )
    t3 = time.time()
    elapsed = t3 - t2

    print(f"[INFO] 聚合完成，耗時：{elapsed:.3f} 秒")
    print("")

    # 顯示前幾列結果
    print("[INFO] 聚合結果（前 5 列）：")
    print(result.head(5))

    # 粗略估算吞吐量（列/秒）
    rows_per_sec = n_rows / elapsed if elapsed > 0 else float("inf")
    print("")
    print("════════════════════════════════════════════")
    print("  Summary")
    print("════════════════════════════════════════════")
    print(f"  Engine       : {engine_name}")
    print(f"  Rows         : {n_rows:,}")
    print(f"  Groups       : {n_groups:,}")
    print(f"  CPU Cores    : {cpu_cores}")
    print(f"  Time (s)     : {elapsed:.3f}")
    print(f"  Rows / sec   : {rows_per_sec:,.0f}")
    print("════════════════════════════════════════════")
    print("")
    
    # 效能分析
    if elapsed > 0:
        if engine_name == "polars":
            print("✅ Polars 效能測試完成！")
            if elapsed < 1.0:
                print("⚡ 極速處理！Polars 多核心加速效果顯著")
            elif elapsed < 3.0:
                print("🚀 高速處理！充分利用 CPU 多核心")
            else:
                print("✓ 處理完成")
        else:
            print("✅ Pandas 效能測試完成！")
            print("💡 提示：安裝 Polars 可獲得更好的效能")

if __name__ == "__main__":
    main()
'@

Set-Content -LiteralPath $MainPy -Value $fixedCode -Encoding UTF8
Write-Host "✅ 修復完成！" -ForegroundColor Green
Write-Host ""

Write-Host "現在可以執行:" -ForegroundColor Yellow
Write-Host "  .\CPU_ACCEL_VENV\Scripts\python.exe main_accelerated.py" -ForegroundColor White
Write-Host ""
Write-Host "或使用虛擬環境:" -ForegroundColor Yellow
Write-Host "  .\CPU_ACCEL_VENV\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  python main_accelerated.py" -ForegroundColor White

