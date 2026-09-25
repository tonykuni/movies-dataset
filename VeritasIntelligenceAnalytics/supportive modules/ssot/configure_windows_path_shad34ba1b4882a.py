#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN Ultimate - Windows 路徑配置更新腳本
======================================

自動更新 VRN 配置以使用正確的 Windows 路徑
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
import sys
from pathlib import Path

print("="*80)
print(" VRN Ultimate - Windows 路徑配置更新 ".center(80, "="))
print("="*80 + "\n")

# 目標路徑
TARGET_PATH = Path(r"C:\VeritasIntelligenceSystem\VeritasReportNova")

print(f"目標路徑: {TARGET_PATH}\n")

# 檢查路徑是否存在
if not TARGET_PATH.exists():
    print(f"⚠️ 目錄不存在: {TARGET_PATH}")
    create = input("是否創建目錄? [Y/N]: ").strip().upper()
    if create == 'Y':
        try:
            TARGET_PATH.mkdir(parents=True, exist_ok=True)
            print(f"✓ 目錄已創建")
        except Exception as e:
            print(f"❌ 創建失敗: {e}")
            sys.exit(1)
    else:
        print("❌ 無法繼續，目錄不存在")
        sys.exit(1)

# 創建子目錄
subdirs = ['input', 'output', 'logs', 'db', 'temp', '.cache']
print("\n創建子目錄...")
for subdir in subdirs:
    subdir_path = TARGET_PATH / subdir
    subdir_path.mkdir(parents=True, exist_ok=True)
    print(f"  ✓ {subdir}")

# 檢查主程式文件
vrn_file = TARGET_PATH / "vrn_ultimate_integrated_all_in_one.py"
if not vrn_file.exists():
    print(f"\n⚠️ 找不到主程式文件: {vrn_file}")
    print("請確認文件已複製到目標目錄")
    input("\n按 Enter 繼續...")
    sys.exit(1)

print(f"\n✓ 主程式文件存在")

# 創建配置測試腳本
print("\n創建配置測試腳本...")
test_config_script = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN 配置測試 - Windows 路徑
"""

import sys
from pathlib import Path

# 添加 VRN 路徑
sys.path.insert(0, r"{TARGET_PATH}")

try:
    from vrn_ultimate_integrated_all_in_one import VRNConfig, VRNProcessor
    
    print("="*60)
    print(" VRN 配置測試 ".center(60, "="))
    print("="*60 + "\\n")
    
    # 創建配置
    config = VRNConfig()
    config.base_dir = Path(r"{TARGET_PATH}")
    
    print("配置路徑:")
    print(f"  基礎目錄: {{config.base_dir}}")
    print(f"  輸入目錄: {{config.input_dir}}")
    print(f"  輸出目錄: {{config.output_dir}}")
    print(f"  日誌目錄: {{config.logs_dir}}")
    
    print("\\n目錄檢查:")
    for dir_name, dir_path in [
        ("基礎", config.base_dir),
        ("輸入", config.input_dir),
        ("輸出", config.output_dir),
        ("日誌", config.logs_dir)
    ]:
        exists = "✓" if dir_path.exists() else "✗"
        print(f"  {{exists}} {{dir_name}}: {{dir_path}}")
    
    print("\\n處理配置:")
    print(f"  並行工作數: {{config.max_workers}}")
    print(f"  DPI: {{config.dpi}}")
    print(f"  CPU加速: {{'✓' if config.enable_cpu_acceleration else '✗'}}")
    
    print("\\n輸出格式:")
    formats = []
    if config.use_csv: formats.append("CSV")
    if config.use_excel: formats.append("Excel")
    if config.use_parquet: formats.append("Parquet")
    if config.use_json: formats.append("JSON")
    if config.use_html: formats.append("HTML")
    print(f"  {{', '.join(formats)}}")
    
    print("\\n" + "="*60)
    print("✅ 配置測試通過！".center(60))
    print("="*60)
    
    # 保存配置
    config_file = config.base_dir / "config.json"
    config.save(config_file)
    print(f"\\n✓ 配置已保存: {{config_file}}")
    
except Exception as e:
    print(f"\\n❌ 錯誤: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\\n✅ 系統配置完成！")
print("\\n下一步:")
print("  1. 運行: run_test.bat")
print("  2. 處理PDF: run_vrn.bat")

input("\\n按 Enter 結束...")
'''

test_config_file = TARGET_PATH / "test_config.py"
with open(test_config_file, 'w', encoding='utf-8') as f:
    f.write(test_config_script)

print(f"✓ 配置測試腳本已創建: {test_config_file}")

# 創建快速使用範例
print("\n創建使用範例...")
example_script = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN 使用範例 - Windows 版本
"""

import sys
from pathlib import Path

# 添加 VRN 路徑
sys.path.insert(0, r"{TARGET_PATH}")

from vrn_ultimate_integrated_all_in_one import VRNConfig, VRNProcessor

def main():
    print("="*60)
    print(" VRN Ultimate - 使用範例 ".center(60, "="))
    print("="*60 + "\\n")
    
    # 配置
    config = VRNConfig()
    config.base_dir = Path(r"{TARGET_PATH}")
    config.max_workers = 4  # 調整為您的CPU核心數
    config.dpi = 200
    config.enable_repair = True
    config.enable_cross_validation = True
    
    # 創建處理器
    processor = VRNProcessor(config)
    
    # 範例 1: 處理單個文件
    # pdf_file = r"C:\\path\\to\\your\\document.pdf"
    # report = processor.process_pdf(pdf_file)
    
    # 範例 2: 處理 input 目錄
    input_dir = config.input_dir
    print(f"處理目錄: {{input_dir}}\\n")
    
    # 檢查是否有PDF文件
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print("⚠️ input 目錄中沒有PDF文件")
        print(f"請將PDF文件放入: {{input_dir}}")
        return
    
    print(f"找到 {{len(pdf_files)}} 個PDF文件:")
    for pdf in pdf_files:
        print(f"  • {{pdf.name}}")
    
    print("\\n開始處理...\\n")
    reports = processor.process_directory(str(input_dir))
    
    # 統計
    total_tables = sum(r.tables_extracted for r in reports)
    total_time = sum(r.processing_time for r in reports)
    
    print("\\n" + "="*60)
    print(" 處理完成 ".center(60, "="))
    print("="*60)
    print(f"\\n處理文件數: {{len(reports)}}")
    print(f"提取表格數: {{total_tables}}")
    print(f"總耗時: {{total_time:.2f}} 秒")
    print(f"\\n結果位置:")
    print(f"  表格: {{config.output_dir / 'tables'}}")
    print(f"  報告: {{config.output_dir / 'reports'}}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\\n\\n⚠️ 用戶中斷")
    except Exception as e:
        print(f"\\n❌ 錯誤: {{e}}")
        import traceback
        traceback.print_exc()
    finally:
        input("\\n按 Enter 結束...")
'''

example_file = TARGET_PATH / "example_usage.py"
with open(example_file, 'w', encoding='utf-8') as f:
    f.write(example_script)

print(f"✓ 使用範例已創建: {example_file}")

# 總結
print("\n" + "="*80)
print(" 配置完成 ".center(80, "="))
print("="*80)

print(f"\n✅ 系統已配置到: {TARGET_PATH}")
print(f"\n創建的文件:")
print(f"  • test_config.py - 配置測試腳本")
print(f"  • example_usage.py - 使用範例")

print(f"\n下一步:")
print(f"  1. 測試配置: python test_config.py")
print(f"  2. 運行系統測試: run_test.bat")
print(f"  3. 開始處理: run_vrn.bat")
print(f"  4. 或查看範例: python example_usage.py")

print(f"\n快速開始:")
print(f"  cd {TARGET_PATH}")
print(f"  run_test.bat")

input("\n按 Enter 結束...")
