#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  VDF_MDL001_TWEquityEngine.py
================================================================================
  VERITAS DATA FRAMEWORK - MDL001  TW Equity Engine (Full-Market)
  Version    : 17.0.0   |   Module ID : VDF-MDL001-EQT-001
  Asset ID   : VDF-MDL001-CLS-001
  Policy     : 功能只增不減 · append-only · SSOT · LL-compliant
  Lineage    : v16 (smart_tw_system) → v17 (VDF_MDL001 全市場個股)

ARCHITECTURE
================================================================================
  指令架構不變 · 最少改變 (architecture preserved):
    v16 全部 9 個區塊 100% 保留:
      [1] 頂部參數區
      [2] IntelligentDependencyChecker
      [3] IntelligentModuleImporter (含 Veritas 載入)
      [4] 抓取工具函式 (日期/log/診斷)
      [5] IndexFileManager
      [6] RealIndexFetcher (TAIEX + TPEX 指數)
      [7] SmartAutoDeployController
      [8] EnhancedStockProcessor
      [9] main()

  v17 新增 (only-additive):
      [5b] EquityFileManager      — 全市場個股檔管理
      [6b] RealEquityFetcher      — TWSE/TPEX 全上市櫃個股每日量價
      [+]  Rich Summary Matrix    — 詳細彙總表

COVERAGE (擷取資料)
================================================================================
  個股層:
    - TWSE 全上市 (~1000 檔) 每日 OHLCV + 成交量 + 成交金額 + 漲跌
    - TPEX 全上櫃 (~800 檔)  每日 OHLCV + 成交量 + 成交金額 + 漲跌
  指數層 (v16 保留):
    - TAIEX (加權指數) 收盤 + 漲跌 + 成交值 + 成交股數 + 成交筆數
    - TPEX  (櫃買指數) 收盤 + 漲跌 + 成交值 + 成交股數
  籌碼層 (v16 保留):
    - 三大法人買賣超 (Foreign / Trust / Dealer)
    - 融資餘額 / 融券餘額 / 券資比
    - 當沖總值 / 當沖佔比
    - 融資維持率 (60 日均線推估)

HOLIDAY HANDLING (假日處理)
================================================================================
  - 自動跳過 (SKIP_WEEKENDS = True)
  - 已知法定假日預過濾 (TW_KNOWN_HOLIDAYS)
  - 動態 holiday cache (兩指數皆 None 即標 holiday)
  - 假日長度不設限 (MAX_CONSECUTIVE_HOLIDAYS = 0 → 無上限)
  - 污染 cache 自動偵測 + 重置

PARAMETERS
================================================================================
  ★ ALL PARAMETERS ON THE TOP (第 80-260 行)
  - 路徑: OUTPUT_DIR / INDEX_OUTPUT_DIR / EQUITY_OUTPUT_DIR / VERITAS_MODULE_PATH
  - 時間: INDEX_START_DATE / INDEX_END_DATE / USE_CURRENT_DATE_AS_END
  - 開關: FETCH_TAIEX / FETCH_TPEX / FETCH_ALL_EQUITIES_TWSE / FETCH_ALL_EQUITIES_TPEX
  - 加速: ENABLE_ASYNC_BATCH / ASYNC_MAX_CONCURRENT / REQUEST_INTERVAL_SEC
  - 網路: HTTP_FALLBACK_ENABLED / TWSE_PUBLIC_STOCK_DAY / TPEX_PUBLIC_STOCK_DAY

USAGE
================================================================================
  python VDF_MDL001_TWEquityEngine.py
  python VDF_MDL001_TWEquityEngine.py --reset-holidays
  python VDF_MDL001_TWEquityEngine.py --reset-all
  python VDF_MDL001_TWEquityEngine.py --equity-only
  python VDF_MDL001_TWEquityEngine.py --index-only
  python VDF_MDL001_TWEquityEngine.py --no-pause
"""

import os, sys, time, json, subprocess, platform, asyncio
import random, re, csv, importlib, warnings
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union, Set
import logging

warnings.filterwarnings("ignore")

# 版本和基本信息
SYSTEM_VERSION = "v17.0"
SYSTEM_NAME = "🏛️ VDF MDL001 - TW Equity Engine (Full-Market)"
AUTHOR = "VERITAS Intelligence System · VDF"
BUILD_DATE = datetime.now().strftime("%Y-%m-%d")

# =====================================================================================
# 📋 [PARAM-1/8] 系統依賴 (v16 原樣保留 + 微調)
# =====================================================================================

REQUIRED_PACKAGES = {
    'critical': {
        'pandas':  {'min_version': '1.3.0',  'import_name': 'pandas'},
        'numpy':   {'min_version': '1.20.0', 'import_name': 'numpy'},
        'aiohttp': {'min_version': '3.7.0',  'import_name': 'aiohttp'},
        'requests':{'min_version': '2.25.0', 'import_name': 'requests'},
    },
    'performance': {
        'polars':  {'min_version': '0.15.0', 'import_name': 'polars',  'optional': True},
        'pyarrow': {'min_version': '5.0.0',  'import_name': 'pyarrow', 'optional': True},
        'rich':    {'min_version': '12.0.0', 'import_name': 'rich'},
        'psutil':  {'min_version': '5.8.0',  'import_name': 'psutil'},
    },
    'optional': {
        'matplotlib': {'min_version': '3.3.0',  'import_name': 'matplotlib', 'optional': True},
        'seaborn':    {'min_version': '0.11.0', 'import_name': 'seaborn',    'optional': True},
        'openpyxl':   {'min_version': '3.0.0',  'import_name': 'openpyxl',   'optional': True},
    },
    'testing': {
        'pytest':         {'min_version': '6.0.0',  'import_name': 'pytest',         'optional': True},
        'pytest-asyncio': {'min_version': '0.15.0', 'import_name': 'pytest_asyncio', 'optional': True},
    }
}

# =====================================================================================
# 📋 [PARAM-2/8] 路徑配置 (v16 原樣保留 + 新增 EQUITY 輸出)
# =====================================================================================

OUTPUT_DIR          = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\dict\1-2-TWStockData"
TICKER_FILE         = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\dict\1-1_TickerList.csv"
INDEX_OUTPUT_DIR    = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\dict\1-3-TWIndexUniverse"
EQUITY_OUTPUT_DIR   = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\dict\1-4-TWEquityUniverse"  # v17 新增
LOG_DIR             = os.path.join(OUTPUT_DIR, "logs")
REPORT_DIR          = os.path.join(OUTPUT_DIR, "reports")
VERITAS_MODULE_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module"

# =====================================================================================
# 📋 [PARAM-3/8] 抓取時間範圍 (v16 原樣保留)
# =====================================================================================

INDEX_START_DATE        = "2026-01-01"
INDEX_END_DATE          = "2026-04-30"
USE_CURRENT_DATE_AS_END = True

# =====================================================================================
# 📋 [PARAM-4/8] 網路 / 重試 / 加速 (v16 保留 + v17 新增非同步批次)
# =====================================================================================

REQUEST_INTERVAL_SEC = 1.0
MAX_RETRIES          = 3
RETRY_DELAY          = 2
REQUEST_TIMEOUT      = 30
SKIP_WEEKENDS        = True

# v17 加速 (功能只增不減)
ENABLE_ASYNC_BATCH    = True          # 啟用 ThreadPoolExecutor 並發 (跨 sync/async 都穩定)
ASYNC_MAX_CONCURRENT  = 5             # 同時並發數 (避免被 ban)
HTTP_FALLBACK_ENABLED = True          # Aegis 失敗時 fallback requests 直連

# v17 公開 API endpoints (Path B fallback)
TWSE_PUBLIC_STOCK_DAY = "https://www.twse.com.tw/exchangeReport/MI_INDEX"
TPEX_PUBLIC_STOCK_DAY = "https://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php"

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}

# =====================================================================================
# 📋 [PARAM-5/8] 診斷與保護 (v16 保留 + v17 假日上限改 0=無限制)
# =====================================================================================

DIAGNOSTIC_MODE           = True
MAX_CONSECUTIVE_HOLIDAYS  = 0            # ★ v17: 0 = 假日長度不設限 (使用者指令)
PRINT_FIRST_RAW_RESPONSE  = True

# =====================================================================================
# 📋 [PARAM-6/8] 抓取項目開關 (v16 保留 + v17 新增全市場個股)
# =====================================================================================

# 指數層 (v16)
FETCH_TAIEX         = True
FETCH_TPEX          = True
FETCH_INDEX_PRICE   = True
FETCH_INSTITUTIONAL = True
FETCH_MARGIN        = True
FETCH_DAY_TRADING   = True
COMPUTE_DERIVED     = True

# 個股層 (v17 新增)
FETCH_ALL_EQUITIES_TWSE = True   # 全上市每日量價
FETCH_ALL_EQUITIES_TPEX = True   # 全上櫃每日量價

# 衍生指標參數
MARGIN_AVG_WINDOW   = 60
MARGIN_LEGAL_RATIO  = 166.0

# =====================================================================================
# 📋 [PARAM-7/8] I/O (v16 保留)
# =====================================================================================

OUTPUT_FORMATS      = ["csv", "parquet"]
CSV_ENCODING        = "utf-8-sig"
ENABLE_BACKUP       = True
MAX_BACKUP_FILES    = 5
ENABLE_INCREMENTAL  = True
AUTO_DEDUPLICATE    = True

# v17: 個股每日資料 partition 策略
EQUITY_PARTITION_BY_YEAR  = True   # 按年分檔 (1-4_TWEquity_2026.parquet)
EQUITY_FLAT_SCHEMA        = True   # Long format (Date, Ticker, Market, Open, High, Low, Close, Volume, ...)

# =====================================================================================
# 📋 [PARAM-8/8] 已知台股法定假日 + 預設股票清單 (v16 保留)
# =====================================================================================

TW_KNOWN_HOLIDAYS_2025_2026 = {
    # 2025
    "2025-01-01",
    "2025-01-27", "2025-01-28", "2025-01-29", "2025-01-30", "2025-01-31",
    "2025-02-28",
    "2025-04-03", "2025-04-04",
    "2025-05-01",
    "2025-09-29",
    "2025-10-10",
    # 2026
    "2026-01-01", "2026-01-02",
    "2026-02-16", "2026-02-17", "2026-02-18", "2026-02-19", "2026-02-20", "2026-02-23",
    "2026-02-27", "2026-02-28",
    "2026-04-03", "2026-04-06",
    "2026-05-01",
    "2026-06-19",
    "2026-09-25",
    "2026-10-09",
}

DEFAULT_STOCK_LIST = [
    {'ticker': '2330', 'name': '台積電'},
    {'ticker': '3324', 'name': '雙鴻'}
]

# =====================================================================================
# Veritas 與 logger 全域 (v16 原樣)
# =====================================================================================

VAN_AVAILABLE = False
VC_AVAILABLE  = False
van = None
vc  = None
veritas_logger = None

# 可用性 flags (由 _set_availability_flags 設定)
POLARS_AVAILABLE     = False
PYARROW_AVAILABLE    = False
RICH_AVAILABLE       = False
MATPLOTLIB_AVAILABLE = False

# =====================================================================================
# 🔍 [BLOCK-2] 智能依賴檢查器 (v15.1/v16 原樣保留, 0 改動)
# =====================================================================================

class IntelligentDependencyChecker:
    """智能依賴檢查器 - 只安裝真正需要的"""

    def __init__(self):
        self.python_executable = sys.executable
        self.installed_packages = {}
        self.missing_packages = {}
        self.outdated_packages = {}
        self.available_packages = {}
        self.installation_log = []
        print("🔍 初始化智能依賴檢查器...")

    def comprehensive_dependency_scan(self) -> Dict[str, Any]:
        print("\n🔍 執行全面依賴掃描...")
        scan_result = {
            'scan_time': datetime.now().isoformat(),
            'total_packages': 0,
            'available_packages': 0,
            'missing_packages': 0,
            'outdated_packages': 0,
            'installation_needed': False,
            'details': {}
        }
        self._scan_installed_packages()

        for category, packages in REQUIRED_PACKAGES.items():
            print(f"   📂 檢查 {category} 類別...")
            category_result = self._check_category_packages(category, packages)
            scan_result['details'][category] = category_result
            scan_result['total_packages'] += category_result['total']
            scan_result['available_packages'] += category_result['available']
            scan_result['missing_packages'] += category_result['missing']
            scan_result['outdated_packages'] += category_result['outdated']

        scan_result['installation_needed'] = (
            scan_result['missing_packages'] > 0 or scan_result['outdated_packages'] > 0
        )
        self._display_scan_summary(scan_result)
        return scan_result

    def _scan_installed_packages(self):
        print("   🔍 檢查已安裝的Python包...")
        try:
            result = subprocess.run(
                [self.python_executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                installed_list = json.loads(result.stdout)
                for package in installed_list:
                    self.installed_packages[package['name'].lower()] = package['version']
                print(f"     ✅ 發現 {len(self.installed_packages)} 個已安裝的包")
            else:
                print(f"     ⚠️ 無法獲取已安裝包列表: {result.stderr}")
        except Exception as e:
            print(f"     ❌ 掃描已安裝包時出錯: {e}")

    def _check_category_packages(self, category: str, packages: Dict) -> Dict[str, Any]:
        category_result = {'total': len(packages), 'available': 0, 'missing': 0, 'outdated': 0, 'packages': {}}
        for package_name, package_info in packages.items():
            check_result = self._check_single_package(package_name, package_info)
            category_result['packages'][package_name] = check_result
            if check_result['status'] == 'available':
                category_result['available'] += 1
                self.available_packages[package_name] = check_result
            elif check_result['status'] == 'missing':
                category_result['missing'] += 1
                self.missing_packages[package_name] = check_result
            elif check_result['status'] == 'outdated':
                category_result['outdated'] += 1
                self.outdated_packages[package_name] = check_result
        return category_result

    def _check_single_package(self, package_name: str, package_info: Dict) -> Dict[str, Any]:
        result = {
            'package_name': package_name,
            'import_name': package_info.get('import_name', package_name),
            'min_version': package_info.get('min_version'),
            'optional': package_info.get('optional', False),
            'status': 'unknown',
            'installed_version': None,
            'can_import': False,
            'needs_action': False,
            'action_type': None
        }
        installed_version = self._get_installed_version(package_name)
        if installed_version:
            result['installed_version'] = installed_version
            can_import = self._test_import(result['import_name'])
            result['can_import'] = can_import
            if can_import:
                if result['min_version']:
                    if self._compare_versions(installed_version, result['min_version']):
                        result['status'] = 'available'
                        print(f"     ✅ {package_name} ({installed_version})")
                    else:
                        result['status'] = 'outdated'
                        result['needs_action'] = True
                        result['action_type'] = 'upgrade'
                        print(f"     📈 {package_name} ({installed_version} → {result['min_version']}+)")
                else:
                    result['status'] = 'available'
                    print(f"     ✅ {package_name} ({installed_version})")
            else:
                result['status'] = 'import_error'
                result['needs_action'] = True
                result['action_type'] = 'reinstall'
                print(f"     🔄 {package_name} (安裝但無法導入)")
        else:
            result['status'] = 'missing'
            result['needs_action'] = True
            result['action_type'] = 'install'
            if result['optional']:
                print(f"     ⚪ {package_name} (可選，未安裝)")
            else:
                print(f"     ❌ {package_name} (缺少)")
        return result

    def _get_installed_version(self, package_name: str) -> Optional[str]:
        for name, version in self.installed_packages.items():
            if name.lower() == package_name.lower():
                return version
        try:
            import importlib.metadata
            return importlib.metadata.version(package_name)
        except Exception:
            pass
        return None

    def _test_import(self, import_name: str) -> bool:
        try:
            importlib.import_module(import_name)
            return True
        except (ImportError, Exception):
            return False

    def _compare_versions(self, installed: str, required: str) -> bool:
        try:
            from packaging import version
            return version.parse(installed) >= version.parse(required)
        except ImportError:
            installed_parts = [int(x) for x in installed.split('.') if x.isdigit()]
            required_parts = [int(x) for x in required.split('.') if x.isdigit()]
            for i in range(max(len(installed_parts), len(required_parts))):
                ip = installed_parts[i] if i < len(installed_parts) else 0
                rp = required_parts[i] if i < len(required_parts) else 0
                if ip > rp: return True
                elif ip < rp: return False
            return True

    def _display_scan_summary(self, scan_result: Dict):
        print(f"\n📊 依賴掃描摘要:")
        print(f"   總包數: {scan_result['total_packages']}")
        print(f"   ✅ 可用: {scan_result['available_packages']}")
        print(f"   ❌ 缺少: {scan_result['missing_packages']}")
        print(f"   📈 過舊: {scan_result['outdated_packages']}")
        availability_rate = (scan_result['available_packages'] / scan_result['total_packages']) * 100
        print(f"   📊 可用率: {availability_rate:.1f}%")
        if scan_result['installation_needed']:
            total_actions = scan_result['missing_packages'] + scan_result['outdated_packages']
            print(f"   🔧 需要操作: {total_actions} 個包")
        else:
            print(f"   🎉 所有依賴都已就緒！")

    def intelligent_install_missing_packages(self) -> Dict[str, Any]:
        if not self.missing_packages and not self.outdated_packages:
            print("🎉 所有依賴都已就緒，無需安裝任何包！")
            return {
                'installation_performed': False,
                'message': 'All dependencies are ready',
                'total_packages': 0,
                'successful_installs': 0,
                'failed_installs': 0
            }
        print(f"\n🔧 開始智能安裝流程...")
        installation_report = {
            'installation_performed': True,
            'installation_time': 0,
            'total_packages': 0,
            'successful_installs': 0,
            'failed_installs': 0,
            'skipped_packages': 0,
            'details': {},
            'failed_packages': []
        }
        start_time = time.time()
        packages_to_process = {**self.missing_packages, **self.outdated_packages}
        installation_report['total_packages'] = len(packages_to_process)
        print(f"   📦 需要處理 {len(packages_to_process)} 個包")
        priority_order = ['critical', 'performance', 'optional', 'testing']
        for category in priority_order:
            category_packages = []
            for package_name, package_info in packages_to_process.items():
                if any(package_name in REQUIRED_PACKAGES[cat] for cat in [category]):
                    category_packages.append((package_name, package_info))
            if category_packages:
                print(f"\n   📂 處理 {category} 類別 ({len(category_packages)} 個包)...")
                category_result = self._install_category_packages(category, category_packages)
                installation_report['details'][category] = category_result
                installation_report['successful_installs'] += category_result['successful']
                installation_report['failed_installs'] += category_result['failed']
                installation_report['skipped_packages'] += category_result['skipped']
        installation_report['installation_time'] = time.time() - start_time
        self._display_installation_summary(installation_report)
        return installation_report

    def _install_category_packages(self, category: str, packages: List[Tuple]) -> Dict[str, Any]:
        result = {'successful': 0, 'failed': 0, 'skipped': 0, 'packages': {}}
        for package_name, package_info in packages:
            action_type = package_info.get('action_type', 'install')
            optional = package_info.get('optional', False)
            print(f"     🔧 {action_type} {package_name}...")
            if optional and category == 'testing':
                print(f"       ⏭️ 跳過可選測試包")
                result['skipped'] += 1
                result['packages'][package_name] = 'skipped'
                continue
            success = self._install_single_package(package_name, action_type)
            if success:
                result['successful'] += 1
                result['packages'][package_name] = 'success'
                print(f"       ✅ 完成")
            else:
                result['failed'] += 1
                result['packages'][package_name] = 'failed'
                if not optional:
                    print(f"       ❌ 失敗 (必需包)")
                else:
                    print(f"       ⚠️ 失敗 (可選包)")
        return result

    def _install_single_package(self, package_name: str, action_type: str) -> bool:
        try:
            if action_type == 'upgrade':
                cmd = [self.python_executable, '-m', 'pip', 'install', '--upgrade', package_name]
            else:
                cmd = [self.python_executable, '-m', 'pip', 'install', package_name]
            cmd.extend(['--quiet', '--no-warn-script-location'])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                if self._verify_installation(package_name):
                    self.installation_log.append(f"SUCCESS: {action_type} {package_name}")
                    return True
                else:
                    self.installation_log.append(f"FAILED: {package_name} installed but can't import")
                    return False
            else:
                error_msg = result.stderr[:100] if result.stderr else "Unknown error"
                self.installation_log.append(f"FAILED: {package_name} - {error_msg}")
                return False
        except subprocess.TimeoutExpired:
            self.installation_log.append(f"TIMEOUT: {package_name}")
            return False
        except Exception as e:
            self.installation_log.append(f"ERROR: {package_name} - {e}")
            return False

    def _verify_installation(self, package_name: str) -> bool:
        for cat in ['critical', 'performance', 'optional', 'testing']:
            if package_name in REQUIRED_PACKAGES.get(cat, {}):
                package_info = REQUIRED_PACKAGES[cat][package_name]
                import_name = package_info.get('import_name', package_name)
                return self._test_import(import_name)
        return False

    def _display_installation_summary(self, report: Dict):
        print(f"\n📦 智能安裝摘要:")
        print(f"   處理包數: {report['total_packages']}")
        print(f"   ✅ 成功: {report['successful_installs']}")
        print(f"   ❌ 失敗: {report['failed_installs']}")
        print(f"   ⏭️ 跳過: {report['skipped_packages']}")
        print(f"   ⏱️ 耗時: {report['installation_time']:.1f} 秒")
        if report['failed_installs'] > 0:
            print(f"   ⚠️ 部分包安裝失敗，系統將在降級模式運行")
        else:
            print(f"   🎉 所有需要的包都已成功安裝！")


# =====================================================================================
# 🎯 [BLOCK-3] 智能模組導入器 (v15.1/v16 原樣保留 + 微擴 Veritas 偵測)
# =====================================================================================

class IntelligentModuleImporter:
    """智能模組導入器"""

    def __init__(self):
        self.imported_modules = {}
        self.failed_imports = []
        self.fallback_available = {}

    def smart_import_all_modules(self) -> bool:
        print("🔄 開始智能模組導入...")
        import_result = {
            'total_attempts': 0,
            'successful_imports': 0,
            'failed_imports': 0,
            'critical_missing': [],
            'modules': {}
        }

        critical_modules = {
            'pandas': 'pd',
            'numpy': 'np',
            'aiohttp': 'aiohttp',
            'requests': 'requests',
            'psutil': 'psutil'
        }
        for module_name, alias in critical_modules.items():
            success, module_obj = self._safe_import(module_name, alias)
            import_result['total_attempts'] += 1
            if success:
                import_result['successful_imports'] += 1
                self.imported_modules[alias] = module_obj
                globals()[alias] = module_obj
                print(f"   ✅ {module_name} → {alias}")
            else:
                import_result['failed_imports'] += 1
                if module_name in ('pandas', 'numpy', 'requests'):
                    import_result['critical_missing'].append(module_name)
                print(f"   ❌ {module_name} (關鍵模組)" if module_name in ('pandas', 'numpy', 'requests')
                      else f"   ⚠️ {module_name} (建議模組)")

        performance_modules = {'polars': 'pl', 'pyarrow': 'pa', 'rich': 'rich'}
        for module_name, alias in performance_modules.items():
            success, module_obj = self._safe_import(module_name, alias)
            import_result['total_attempts'] += 1
            if success:
                import_result['successful_imports'] += 1
                self.imported_modules[alias] = module_obj
                globals()[alias] = module_obj
                print(f"   ✅ {module_name} → {alias} (性能增強)")
            else:
                import_result['failed_imports'] += 1
                print(f"   ⚠️ {module_name} (性能模組，可選)")

        optional_modules = {
            'matplotlib.pyplot': 'plt',
            'seaborn': 'sns',
            'openpyxl': 'openpyxl'
        }
        for module_name, alias in optional_modules.items():
            success, module_obj = self._safe_import(module_name, alias)
            import_result['total_attempts'] += 1
            if success:
                import_result['successful_imports'] += 1
                self.imported_modules[alias] = module_obj
                globals()[alias] = module_obj
                print(f"   ✅ {module_name} → {alias} (可選)")
            else:
                import_result['failed_imports'] += 1
                print(f"   ⚪ {module_name} (可選模組)")

        # Veritas 載入 (v16 保留)
        self._load_veritas()

        self._set_availability_flags()

        success_rate = (import_result['successful_imports'] / import_result['total_attempts']) * 100
        print(f"\n📊 模組導入摘要:")
        print(f"   成功率: {success_rate:.1f}% ({import_result['successful_imports']}/{import_result['total_attempts']})")

        if import_result['critical_missing']:
            print(f"   ⚠️ 缺少關鍵模組: {', '.join(import_result['critical_missing'])}")
            return False
        else:
            print(f"   ✅ 所有關鍵模組都已就緒")
            return True

    def _safe_import(self, module_name: str, alias: str) -> Tuple[bool, Any]:
        try:
            if '.' in module_name:
                parts = module_name.split('.')
                module = __import__(module_name, fromlist=[parts[-1]])
                return True, module
            else:
                module = __import__(module_name)
                return True, module
        except (ImportError, Exception):
            return False, None

    def _load_veritas(self):
        """載入 Veritas 支援模組 (v16 保留 + v17 偵測個股 API)"""
        global VAN_AVAILABLE, VC_AVAILABLE, van, vc, veritas_logger
        if VERITAS_MODULE_PATH not in sys.path:
            sys.path.insert(0, VERITAS_MODULE_PATH)
        try:
            import VeritasAegisNexus as _van
            van = _van
            VAN_AVAILABLE = True
            globals()['van'] = van
            print(f"   ✅ VeritasAegisNexus (掛載自 {VERITAS_MODULE_PATH})")
            # v17 探測 Aegis 是否提供全市場個股 API
            stock_apis = []
            for fn in ['fetch_twse_stock_day', 'fetch_tpex_stock_day',
                       'fetch_twse_all_stocks', 'fetch_tpex_all_stocks',
                       'fetch_twse_daily_quote', 'fetch_tpex_daily_quote']:
                if hasattr(_van, fn):
                    stock_apis.append(fn)
            if stock_apis:
                print(f"   📡 Aegis 個股 API 偵測: {stock_apis}")
            else:
                print(f"   📡 Aegis 未提供個股 API → 將使用 HTTP fallback 抓 TWSE/TPEX 公開介面")
        except ImportError as e:
            print(f"   ⚠️ VeritasAegisNexus 載入失敗: {e} (將 fallback 至 requests)")
        try:
            import VeritasCeleritas as _vc
            vc = _vc
            VC_AVAILABLE = True
            globals()['vc'] = vc
            try:
                veritas_logger = vc.VRN_MasterLogger("VDF_MDL001_V17")
                vc.cross_init(mode="maxsafe", silent=True)
            except Exception as ex:
                print(f"   ⚠️ Celeritas init 警告: {ex}")
            print(f"   ✅ VeritasCeleritas")
        except ImportError as e:
            print(f"   ⚠️ VeritasCeleritas 載入失敗: {e}")

    def _set_availability_flags(self):
        global POLARS_AVAILABLE, PYARROW_AVAILABLE, RICH_AVAILABLE, MATPLOTLIB_AVAILABLE
        POLARS_AVAILABLE     = 'pl' in self.imported_modules
        PYARROW_AVAILABLE    = 'pa' in self.imported_modules
        RICH_AVAILABLE       = 'rich' in self.imported_modules
        MATPLOTLIB_AVAILABLE = 'plt' in self.imported_modules
        print(f"   🔧 設定可用性標誌:")
        print(f"     Polars: {'✅' if POLARS_AVAILABLE else '❌'}")
        print(f"     PyArrow: {'✅' if PYARROW_AVAILABLE else '❌'}")
        print(f"     Rich: {'✅' if RICH_AVAILABLE else '❌'}")
        print(f"     Matplotlib: {'✅' if MATPLOTLIB_AVAILABLE else '❌'}")
        print(f"     Veritas Aegis: {'✅' if VAN_AVAILABLE else '❌'}")
        print(f"     Veritas Celeritas: {'✅' if VC_AVAILABLE else '❌'}")


# =====================================================================================
# 🛠️ [BLOCK-4] 抓取工具函式 (v16 原樣保留)
# =====================================================================================

def _log(level: str, msg: str):
    """統一 log: 優先 Veritas logger, fallback print"""
    if veritas_logger is not None:
        method_name = {"warning": "warn", "warn": "warn",
                       "info": "info", "error": "error",
                       "debug": "debug", "success": "success"}.get(level, "info")
        method = getattr(veritas_logger, method_name, None)
        if callable(method):
            try: method(msg); return
            except Exception: pass
    print(f"[{level.upper()}] {msg}")


def to_twse_yyyymmdd(dt: datetime) -> str:
    return dt.strftime("%Y%m%d")

def to_twse_month(dt: datetime) -> str:
    return dt.strftime("%Y%m") + "01"

def to_roc_slash(dt: datetime) -> str:
    return f"{dt.year - 1911}/{dt.strftime('%m/%d')}"

def to_roc_dash(dt: datetime) -> str:
    """民國年-月-日 (TPEX 個股 API 用)"""
    return f"{dt.year - 1911}/{dt.strftime('%m')}/{dt.strftime('%d')}"

def to_western_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def get_date_range(s: str, e: str) -> List[datetime]:
    start = datetime.strptime(s, "%Y-%m-%d")
    end = datetime.strptime(e, "%Y-%m-%d")
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def is_known_tw_holiday(dt: datetime) -> bool:
    return to_western_iso(dt) in TW_KNOWN_HOLIDAYS_2025_2026


def safe_num(value: Any) -> Optional[float]:
    if value is None: return None
    s = str(value).strip().replace(",", "").replace("+", "")
    if s in ("", "-", "--", "None", "nan", "NaN"): return None
    try: return float(s)
    except (ValueError, TypeError): return None


def print_raw_response(api_name: str, args: tuple, resp: Any):
    """診斷模式 - 印 RAW"""
    print("\n" + "─" * 88)
    print(f"🔬 RAW: {api_name}({', '.join(repr(a) for a in args)})")
    print("─" * 88)
    print(f"  型態: {type(resp).__name__}")
    if isinstance(resp, dict):
        print(f"  Keys: {list(resp.keys())}")
        for k, v in resp.items():
            if isinstance(v, list) and v:
                print(f"  '{k}': list({len(v)}), 第 1 列 = {v[0]}")
                if len(v) > 1:
                    print(f"             最後 1 列 = {v[-1]}")
            elif isinstance(v, list):
                print(f"  '{k}': 空 list")
            else:
                print(f"  '{k}': {v}")
    elif resp is None:
        print("  ⚠️ None")
    else:
        print(f"  非 dict: {repr(resp)[:200]}")
    print("─" * 88 + "\n")


# =====================================================================================
# 📁 [BLOCK-5] IndexFileManager (v16 原樣保留)
# =====================================================================================

class IndexFileManager:
    """指數資料檔管理 (含 holiday cache)"""

    def __init__(self):
        self.output_dir = Path(INDEX_OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.csv_file     = self.output_dir / "TWIndex_Daily.csv"
        self.parquet_file = self.output_dir / "TWIndex_Daily.parquet"
        self.holiday_file = self.output_dir / "_TWIndex_HolidayDates.json"
        self.backup_dir   = self.output_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)

    def load_holiday_dates(self) -> set:
        if not self.holiday_file.exists():
            return set()
        try:
            with open(self.holiday_file, 'r', encoding='utf-8') as f:
                return set(json.load(f).get("dates", []))
        except Exception as e:
            _log("warning", f"載入 holiday 紀錄失敗: {e}")
            return set()

    def save_holiday_dates(self, dates: set):
        try:
            with open(self.holiday_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "dates": sorted(dates),
                    "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "note": "兩指數皆無資料的日期"
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            _log("warning", f"寫入 holiday 失敗: {e}")

    def create_backup(self, fp: Path) -> bool:
        if not ENABLE_BACKUP or not fp.exists(): return True
        try:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            import shutil
            shutil.copy2(fp, self.backup_dir / f"{ts}_{fp.name}")
            self.cleanup_old_backups()
            return True
        except Exception as e:
            _log("warning", f"備份失敗: {e}")
            return False

    def cleanup_old_backups(self):
        try:
            backups = sorted(self.backup_dir.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)
            for b in backups[MAX_BACKUP_FILES:]:
                b.unlink()
        except Exception:
            pass

    def load_existing(self):
        if not ENABLE_INCREMENTAL: return None
        pd = globals().get('pd')
        if pd is None: return None
        try:
            if self.parquet_file.exists() and globals().get('PYARROW_AVAILABLE'):
                _log("info", f"📂 載入既有 Parquet: {self.parquet_file.name}")
                return pd.read_parquet(self.parquet_file)
            elif self.csv_file.exists():
                _log("info", f"📂 載入既有 CSV: {self.csv_file.name}")
                return pd.read_csv(self.csv_file, encoding=CSV_ENCODING)
        except Exception as e:
            _log("warning", f"載入失敗: {e}")
        return None

    def save_dataframe(self, df) -> Dict[str, bool]:
        results = {"csv": False, "parquet": False}
        pd = globals().get('pd')
        if df is None or pd is None or df.empty: return results
        self.create_backup(self.csv_file)
        if globals().get('PYARROW_AVAILABLE'):
            self.create_backup(self.parquet_file)
        try:
            df.to_csv(self.csv_file, index=False, encoding=CSV_ENCODING)
            results["csv"] = True
            _log("success", f"✅ CSV 已儲存: {self.csv_file}")
        except Exception as e:
            _log("error", f"❌ CSV 儲存失敗: {e}")
        if globals().get('PYARROW_AVAILABLE') and "parquet" in OUTPUT_FORMATS:
            try:
                df.to_parquet(self.parquet_file, index=False)
                results["parquet"] = True
                _log("success", f"✅ Parquet 已儲存: {self.parquet_file}")
            except Exception as e:
                _log("error", f"❌ Parquet 儲存失敗: {e}")
        return results


# =====================================================================================
# 📁 [BLOCK-5b] EquityFileManager (v17 新增 — 全市場個股檔管理)
# =====================================================================================

class EquityFileManager:
    """全市場個股每日資料檔管理 (long format, 按年 partition)"""

    def __init__(self):
        self.output_dir = Path(EQUITY_OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.holiday_file = self.output_dir / "_TWEquity_HolidayDates.json"
        self.backup_dir   = self.output_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)

    def _year_files(self, year: int) -> Tuple[Path, Path]:
        csv_fp     = self.output_dir / f"TWEquity_Daily_{year}.csv"
        parquet_fp = self.output_dir / f"TWEquity_Daily_{year}.parquet"
        return csv_fp, parquet_fp

    def load_holiday_dates(self) -> set:
        if not self.holiday_file.exists():
            return set()
        try:
            with open(self.holiday_file, 'r', encoding='utf-8') as f:
                return set(json.load(f).get("dates", []))
        except Exception as e:
            _log("warning", f"載入 equity holiday 紀錄失敗: {e}")
            return set()

    def save_holiday_dates(self, dates: set):
        try:
            with open(self.holiday_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "dates": sorted(dates),
                    "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "note": "TWSE+TPEX 兩市場皆無個股資料的日期"
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            _log("warning", f"寫入 equity holiday 失敗: {e}")

    def load_existing_year(self, year: int):
        if not ENABLE_INCREMENTAL: return None
        pd = globals().get('pd')
        if pd is None: return None
        csv_fp, parquet_fp = self._year_files(year)
        try:
            if parquet_fp.exists() and globals().get('PYARROW_AVAILABLE'):
                _log("info", f"📂 載入既有個股 Parquet: {parquet_fp.name}")
                return pd.read_parquet(parquet_fp)
            elif csv_fp.exists():
                _log("info", f"📂 載入既有個股 CSV: {csv_fp.name}")
                return pd.read_csv(csv_fp, encoding=CSV_ENCODING, dtype={'Ticker': str})
        except Exception as e:
            _log("warning", f"載入個股檔 ({year}) 失敗: {e}")
        return None

    def get_existing_dates(self, year: int) -> set:
        """取得該年份已抓取的日期集合 (避免重抓)"""
        df = self.load_existing_year(year)
        if df is None or df.empty or "Date" not in df.columns:
            return set()
        return set(df["Date"].astype(str).tolist())

    def save_dataframe(self, df) -> Dict[str, Any]:
        results = {"csv": [], "parquet": [], "rows_per_year": {}}
        pd = globals().get('pd')
        if df is None or pd is None or df.empty: return results
        if "Date" not in df.columns:
            _log("error", "個股 DataFrame 缺 Date 欄位")
            return results
        # 按年分檔
        df["Year"] = pd.to_datetime(df["Date"]).dt.year
        for year, year_df in df.groupby("Year"):
            csv_fp, parquet_fp = self._year_files(int(year))
            year_df = year_df.drop(columns=["Year"])
            # 合併既有
            existing = self.load_existing_year(int(year))
            if existing is not None and not existing.empty:
                combined = pd.concat([existing, year_df], ignore_index=True)
                if AUTO_DEDUPLICATE and "Ticker" in combined.columns:
                    before = len(combined)
                    combined = combined.drop_duplicates(subset=["Date", "Ticker", "Market"], keep="last")
                    if before != len(combined):
                        _log("info", f"  個股 {year} 去重: {before} → {len(combined)}")
            else:
                combined = year_df
            combined = combined.sort_values(["Date", "Market", "Ticker"]).reset_index(drop=True)
            results["rows_per_year"][int(year)] = len(combined)
            # backup + 寫檔
            if csv_fp.exists():
                try:
                    import shutil
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    shutil.copy2(csv_fp, self.backup_dir / f"{ts}_{csv_fp.name}")
                except Exception:
                    pass
            try:
                combined.to_csv(csv_fp, index=False, encoding=CSV_ENCODING)
                results["csv"].append(csv_fp.name)
                _log("success", f"✅ 個股 CSV 已儲存: {csv_fp.name} ({len(combined)} 列)")
            except Exception as e:
                _log("error", f"❌ 個股 CSV 儲存失敗 ({year}): {e}")
            if globals().get('PYARROW_AVAILABLE') and "parquet" in OUTPUT_FORMATS:
                try:
                    combined.to_parquet(parquet_fp, index=False)
                    results["parquet"].append(parquet_fp.name)
                    _log("success", f"✅ 個股 Parquet 已儲存: {parquet_fp.name}")
                except Exception as e:
                    _log("error", f"❌ 個股 Parquet 儲存失敗 ({year}): {e}")
        return results


# =====================================================================================
# 📈 [BLOCK-6] RealIndexFetcher (v16 原樣保留 — TAIEX + TPEX 指數)
# =====================================================================================

class RealIndexFetcher:
    """真實 TWSE/TPEX 指數抓取器"""

    def __init__(self):
        self.fm = IndexFileManager()
        self._taiex_month_cache: Dict[str, dict] = {}
        self._new_holidays: set = set()
        self._diag_done = False

    def _get_taiex_month(self, dt: datetime):
        if van is None: return {}
        month_key = dt.strftime("%Y%m")
        if month_key not in self._taiex_month_cache:
            month_str = to_twse_month(dt)
            try:
                resp = van.fetch_taiex_daily(month_str)
                self._taiex_month_cache[month_key] = resp or {}
                if not self._diag_done and DIAGNOSTIC_MODE:
                    print_raw_response("fetch_taiex_daily", (month_str,), resp)
                if resp and isinstance(resp, dict):
                    n = len(resp.get('data', []))
                    _log("info", f"📊 TAIEX 月資料 cache {month_key}: {n} 筆")
                else:
                    _log("warning", f"TAIEX 月資料 {month_key} 為空")
            except Exception as e:
                _log("warning", f"TAIEX 月資料 {month_key} 異常: {e}")
                self._taiex_month_cache[month_key] = {}
        return self._taiex_month_cache.get(month_key)

    def _fetch_taiex_price(self, dt: datetime):
        result = {"Close": None, "Change": None, "Value": None, "Volume_Share": None, "Trades": None}
        if not FETCH_INDEX_PRICE: return result
        month_data = self._get_taiex_month(dt)
        if not month_data or "data" not in month_data: return result
        target_roc = to_roc_slash(dt)
        rows = month_data["data"]
        if not rows: return result
        date_variants = [
            target_roc,
            f"{dt.year - 1911}/{dt.month}/{dt.day}",
            f"{dt.year - 1911:>3}/{dt.month:02d}/{dt.day:02d}",
        ]
        found_row = None
        for row in rows:
            if not row or len(row) < 1: continue
            row_date = str(row[0]).strip()
            if row_date in date_variants:
                found_row = row
                break
        if found_row is None:
            if not self._diag_done and rows:
                _log("warning", f"TAIEX 找不到 {target_roc}, 月資料第一列日期: '{rows[0][0]}'")
            return result
        if len(found_row) >= 5:
            result["Volume_Share"] = safe_num(found_row[1])
            result["Value"]        = safe_num(found_row[2])
            result["Trades"]       = safe_num(found_row[3])
            result["Close"]        = safe_num(found_row[4])
            if len(found_row) >= 6:
                result["Change"] = safe_num(found_row[5])
        return result

    def _fetch_tpex_price(self, dt: datetime):
        result = {"Close": None, "Change": None, "Value": None, "Volume_Share": None, "Trades": None}
        if not FETCH_INDEX_PRICE or van is None: return result
        roc = to_roc_slash(dt)
        for attempt in range(MAX_RETRIES):
            try:
                resp = van.fetch_tpex_index_daily(roc)
                if not self._diag_done and attempt == 0:
                    print_raw_response("fetch_tpex_index_daily", (roc,), resp)
                if not resp or "data" not in resp: return result
                rows = resp["data"]
                if not rows: return result
                row = rows[0]
                if len(row) >= 2: result["Close"]        = safe_num(row[1])
                if len(row) >= 3: result["Change"]       = safe_num(row[2])
                if len(row) >= 4: result["Value"]        = safe_num(row[3])
                if len(row) >= 5: result["Volume_Share"] = safe_num(row[4])
                return result
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    _log("warning", f"TPEX index {roc} 重試: {e}")
                    time.sleep(RETRY_DELAY)
                else:
                    _log("warning", f"TPEX index {roc} 最終失敗: {e}")
        return result

    def _fetch_taiex_inst(self, dt: datetime):
        result = {"Foreign_Net": None, "Trust_Net": None, "Dealer_Net": None, "Inst_Total": None}
        if not FETCH_INSTITUTIONAL or van is None: return result
        try:
            resp = van.fetch_twse_institutional(to_twse_yyyymmdd(dt))
            if not self._diag_done:
                print_raw_response("fetch_twse_institutional", (to_twse_yyyymmdd(dt),), resp)
            if not resp or "data" not in resp: return result
            f, t, d = 0.0, 0.0, 0.0
            for r in resp["data"]:
                if not r or len(r) < 14: continue
                f += safe_num(r[4]) or 0.0
                t += safe_num(r[10]) or 0.0
                d += safe_num(r[13]) or 0.0
            result["Foreign_Net"] = f
            result["Trust_Net"]   = t
            result["Dealer_Net"]  = d
            result["Inst_Total"]  = f + t + d
        except Exception as e:
            _log("warning", f"TWSE inst 失敗: {e}")
        return result

    def _fetch_tpex_inst(self, dt: datetime):
        result = {"Foreign_Net": None, "Trust_Net": None, "Dealer_Net": None, "Inst_Total": None}
        if not FETCH_INSTITUTIONAL or van is None: return result
        try:
            resp = van.fetch_tpex_institutional(to_western_iso(dt))
            if not self._diag_done:
                print_raw_response("fetch_tpex_institutional", (to_western_iso(dt),), resp)
            if not resp: return result
            rows = resp.get("aaData") or resp.get("data") or []
            f, t, d = 0.0, 0.0, 0.0
            for r in rows:
                if not r or len(r) < 14: continue
                f += safe_num(r[4]) or 0.0
                t += safe_num(r[10]) or 0.0
                d += safe_num(r[13]) or 0.0
            result["Foreign_Net"] = f
            result["Trust_Net"]   = t
            result["Dealer_Net"]  = d
            result["Inst_Total"]  = f + t + d
        except Exception as e:
            _log("warning", f"TPEX inst 失敗: {e}")
        return result

    def _fetch_taiex_margin(self, dt: datetime):
        result = {"Margin_Bal": None, "Short_Bal": None}
        if not FETCH_MARGIN or van is None: return result
        try:
            resp = van.fetch_twse_margin(to_twse_yyyymmdd(dt))
            if not self._diag_done:
                print_raw_response("fetch_twse_margin", (to_twse_yyyymmdd(dt),), resp)
            if not resp or "data" not in resp: return result
            for r in resp["data"]:
                if not r: continue
                label = str(r[0]) if r[0] is not None else ""
                if any(k in label for k in ["融資(交易單位)", "融資餘額", "總計"]):
                    result["Margin_Bal"] = safe_num(r[5]) if len(r) > 5 else None
                    result["Short_Bal"]  = safe_num(r[11]) if len(r) > 11 else None
                    break
        except Exception as e:
            _log("warning", f"TWSE margin 失敗: {e}")
        return result

    def _fetch_tpex_margin(self, dt: datetime):
        result = {"Margin_Bal": None, "Short_Bal": None}
        if not FETCH_MARGIN or van is None: return result
        try:
            resp = van.fetch_tpex_margin(to_roc_slash(dt))
            if not self._diag_done:
                print_raw_response("fetch_tpex_margin", (to_roc_slash(dt),), resp)
            if not resp: return result
            rows = resp.get("aaData") or resp.get("data") or []
            if rows:
                summary = rows[-1]
                result["Margin_Bal"] = safe_num(summary[6]) if len(summary) > 6 else None
                result["Short_Bal"]  = safe_num(summary[12]) if len(summary) > 12 else None
        except Exception as e:
            _log("warning", f"TPEX margin 失敗: {e}")
        return result

    def _fetch_taiex_dt(self, dt: datetime):
        if not FETCH_DAY_TRADING or van is None: return None
        try:
            resp = van.fetch_twse_day_trading(to_twse_yyyymmdd(dt))
            if not self._diag_done:
                print_raw_response("fetch_twse_day_trading", (to_twse_yyyymmdd(dt),), resp)
            if not resp or "data" not in resp: return None
            total = sum((safe_num(r[-1]) or 0.0) for r in resp["data"] if r and len(r) >= 5)
            return total if total > 0 else None
        except Exception as e:
            _log("warning", f"TWSE day_trade 失敗: {e}")
            return None

    def _fetch_tpex_dt(self, dt: datetime):
        if not FETCH_DAY_TRADING or van is None: return None
        try:
            resp = van.fetch_tpex_day_trading(to_roc_slash(dt))
            if not self._diag_done:
                print_raw_response("fetch_tpex_day_trading", (to_roc_slash(dt),), resp)
            if not resp: return None
            rows = resp.get("data") or resp.get("aaData") or []
            total = sum((safe_num(r[-1]) or 0.0) for r in rows if r and len(r) >= 5)
            return total if total > 0 else None
        except Exception as e:
            _log("warning", f"TPEX day_trade 失敗: {e}")
            return None

    def fetch_one_day(self, dt: datetime) -> List[Dict[str, Any]]:
        date_iso = to_western_iso(dt)
        records = []
        if FETCH_TAIEX:
            rec = {"Date": date_iso, "Index": "TAIEX"}
            rec.update(self._fetch_taiex_price(dt))
            rec.update(self._fetch_taiex_inst(dt))
            rec.update(self._fetch_taiex_margin(dt))
            rec["DayTrade_Value"] = self._fetch_taiex_dt(dt)
            records.append(rec)
        if FETCH_TPEX:
            rec = {"Date": date_iso, "Index": "TPEX"}
            rec.update(self._fetch_tpex_price(dt))
            rec.update(self._fetch_tpex_inst(dt))
            rec.update(self._fetch_tpex_margin(dt))
            rec["DayTrade_Value"] = self._fetch_tpex_dt(dt)
            records.append(rec)
        if not self._diag_done:
            self._diag_done = True
            print("\n" + "=" * 88)
            print("🎯 第一日 RAW 診斷完畢, 後續日期不再印 RAW")
            print("=" * 88 + "\n")
        return records

    @staticmethod
    def compute_derived(df):
        pd = globals().get('pd')
        np = globals().get('np')
        if df is None or pd is None or np is None or df.empty or not COMPUTE_DERIVED:
            return df
        if "Short_Bal" in df.columns and "Margin_Bal" in df.columns:
            df["Short_Margin_Ratio_Pct"] = np.where(
                (df["Margin_Bal"].fillna(0) > 0),
                (df["Short_Bal"] / df["Margin_Bal"] * 100).round(2),
                np.nan,
            )
        if "DayTrade_Value" in df.columns and "Value" in df.columns:
            df["DayTrade_Pct"] = np.where(
                (df["Value"].fillna(0) > 0),
                (df["DayTrade_Value"] / df["Value"] * 100).round(2),
                np.nan,
            )
        if "Close" in df.columns and "Index" in df.columns and "Date" in df.columns:
            df = df.sort_values(["Index", "Date"]).reset_index(drop=True)
            min_p = max(1, min(20, MARGIN_AVG_WINDOW // 3))
            for idx_name in df["Index"].unique():
                mask = df["Index"] == idx_name
                avg = df.loc[mask, "Close"].rolling(window=MARGIN_AVG_WINDOW, min_periods=min_p).mean()
                df.loc[mask, "Margin_Maintenance_Pct"] = np.where(
                    avg.notna() & (avg > 0),
                    (df.loc[mask, "Close"] / avg * MARGIN_LEGAL_RATIO).round(2),
                    np.nan,
                )
        return df

    def get_missing_dates(self, existing_df, all_dates, known_holidays):
        if not ENABLE_INCREMENTAL:
            return all_dates
        existing = set()
        if existing_df is not None and not existing_df.empty and "Date" in existing_df.columns:
            existing = set(existing_df["Date"].astype(str).tolist())
        skip = existing | known_holidays
        return [d for d in all_dates if to_western_iso(d) not in skip]

    def run_extraction(self):
        """主執行: v16 邏輯 + v17 假日不設限"""
        pd = globals().get('pd')
        if pd is None:
            _log("error", "pandas 未載入")
            return None
        if not VAN_AVAILABLE:
            _log("error", "VeritasAegisNexus 未載入, 無法抓取真實指數資料")
            return None

        end_date = datetime.now() if USE_CURRENT_DATE_AS_END else datetime.strptime(INDEX_END_DATE, "%Y-%m-%d")
        all_dates = get_date_range(INDEX_START_DATE, end_date.strftime("%Y-%m-%d"))
        if SKIP_WEEKENDS:
            all_dates = [d for d in all_dates if d.weekday() < 5]

        known_holiday_count = sum(1 for d in all_dates if is_known_tw_holiday(d))
        if known_holiday_count > 0:
            all_dates = [d for d in all_dates if not is_known_tw_holiday(d)]
            _log("info", f"📅 預過濾已知法定假日: {known_holiday_count} 天")

        existing = self.fm.load_existing()
        known_holidays = self.fm.load_holiday_dates()

        if known_holidays and len(all_dates) > 0:
            holiday_overlap = sum(1 for d in all_dates if to_western_iso(d) in known_holidays)
            overlap_ratio = holiday_overlap / len(all_dates)
            has_real_data = existing is not None and not existing.empty
            if overlap_ratio > 0.80 and not has_real_data:
                _log("warning", f"⚠️ Holiday cache 異常 ({overlap_ratio:.0%}) 且既有資料空 → 自動重置")
                try:
                    self.fm.holiday_file.unlink()
                    known_holidays = set()
                except Exception as e:
                    _log("error", f"無法刪除 cache: {e}")

        if known_holidays:
            _log("info", f"📅 已知無資料日期 ({len(known_holidays)} 天) 將跳過")
        missing = self.get_missing_dates(existing, all_dates, known_holidays)

        _log("info", f"📅 共 {len(all_dates)} 個交易日, 需更新 {len(missing)} 日")
        if not missing:
            _log("info", "✅ 指數資料已是最新")
            if existing is not None:
                self._no_save = True
                return existing
            return pd.DataFrame()

        new_records: List[Dict[str, Any]] = []
        consecutive_holidays = 0

        for i, dt in enumerate(missing, start=1):
            _log("info", f"[{i}/{len(missing)}] 擷取指數 {to_western_iso(dt)}")
            recs = self.fetch_one_day(dt)
            all_empty = all(r.get("Close") is None for r in recs)

            if all_empty:
                self._new_holidays.add(to_western_iso(dt))
                consecutive_holidays += 1
                _log("info", f"  ⏭️ holiday (連續 {consecutive_holidays} 天)")
                # v17: MAX_CONSECUTIVE_HOLIDAYS = 0 表示不設限, 永遠不中斷
                if MAX_CONSECUTIVE_HOLIDAYS > 0 and consecutive_holidays >= MAX_CONSECUTIVE_HOLIDAYS:
                    _log("error", f"❌ 連續 {consecutive_holidays} 天無資料 → 停止")
                    break
            else:
                consecutive_holidays = 0
                new_records.extend(recs)
            time.sleep(REQUEST_INTERVAL_SEC)

        new_df = pd.DataFrame(new_records)
        if existing is not None and not existing.empty:
            df = pd.concat([existing, new_df], ignore_index=True)
        else:
            df = new_df

        if VC_AVAILABLE:
            try:
                df = vc.DataValidator.clean_dataframe(df)
            except Exception as e:
                _log("warning", f"Celeritas clean 失敗: {e}")

        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors='coerce').dt.strftime('%Y-%m-%d')

        if AUTO_DEDUPLICATE and "Date" in df.columns and "Index" in df.columns:
            before = len(df)
            df = df.drop_duplicates(subset=["Date", "Index"], keep="last")
            if before != len(df):
                _log("info", f"🔄 去重: {before} → {len(df)}")

        if "Date" in df.columns and "Index" in df.columns:
            df = df.sort_values(["Date", "Index"]).reset_index(drop=True)

        df = self.compute_derived(df)

        all_holidays = known_holidays | self._new_holidays
        if self._new_holidays:
            self.fm.save_holiday_dates(all_holidays)
            _log("info", f"📝 holiday 更新: 新增 {len(self._new_holidays)} 天 (總計 {len(all_holidays)} 天)")

        return df


# =====================================================================================
# 📈 [BLOCK-6b] RealEquityFetcher (v17 新增 — TWSE/TPEX 全市場個股每日量價)
# =====================================================================================

class RealEquityFetcher:
    """
    全市場個股每日量價抓取器
    Path A: Aegis fetch_twse/tpex_stock_day (若有)
    Path B: requests 直連 TWSE/TPEX 公開 API (HTTP_FALLBACK_ENABLED)
    Schema (long format):
      Date, Market(TWSE/TPEX), Ticker, Name,
      Volume_Share, Trades, Value, Open, High, Low, Close, Change, ChangePct
    """

    def __init__(self):
        self.fm = EquityFileManager()
        self._new_holidays: set = set()
        self._diag_done_twse = False
        self._diag_done_tpex = False
        # 偵測 Aegis 個股 API
        self.aegis_twse_fn = None
        self.aegis_tpex_fn = None
        if van is not None:
            for fn in ['fetch_twse_stock_day', 'fetch_twse_all_stocks', 'fetch_twse_daily_quote']:
                if hasattr(van, fn):
                    self.aegis_twse_fn = getattr(van, fn); break
            for fn in ['fetch_tpex_stock_day', 'fetch_tpex_all_stocks', 'fetch_tpex_daily_quote']:
                if hasattr(van, fn):
                    self.aegis_tpex_fn = getattr(van, fn); break

    # ─── TWSE 全上市個股 ────────────────────────────────────────────────
    def _fetch_twse_stocks_aegis(self, dt: datetime) -> Optional[dict]:
        if self.aegis_twse_fn is None: return None
        try:
            resp = self.aegis_twse_fn(to_twse_yyyymmdd(dt))
            if not self._diag_done_twse and DIAGNOSTIC_MODE:
                print_raw_response(self.aegis_twse_fn.__name__, (to_twse_yyyymmdd(dt),), resp)
            return resp
        except Exception as e:
            _log("warning", f"Aegis TWSE 個股 失敗: {e}")
            return None

    def _fetch_twse_stocks_http(self, dt: datetime) -> Optional[dict]:
        """HTTP fallback: TWSE MI_INDEX (type=ALLBUT0999 = 全部不含權證)"""
        if not HTTP_FALLBACK_ENABLED: return None
        requests = globals().get('requests')
        if requests is None: return None
        params = {
            "response": "json",
            "date":     to_twse_yyyymmdd(dt),
            "type":     "ALLBUT0999",
        }
        for attempt in range(MAX_RETRIES):
            try:
                r = requests.get(TWSE_PUBLIC_STOCK_DAY, params=params,
                                 headers=HTTP_HEADERS, timeout=REQUEST_TIMEOUT)
                if r.status_code == 200:
                    data = r.json()
                    if not self._diag_done_twse and DIAGNOSTIC_MODE:
                        print_raw_response("HTTP TWSE MI_INDEX",
                                           (to_twse_yyyymmdd(dt),), data)
                    return data
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    _log("warning", f"TWSE HTTP {to_twse_yyyymmdd(dt)} 重試 ({attempt+1}): {e}")
                    time.sleep(RETRY_DELAY)
        return None

    def _parse_twse_stocks(self, resp: dict, dt: datetime) -> List[Dict[str, Any]]:
        """解析 TWSE 個股 (相容 Aegis 與 HTTP 兩種格式)"""
        if not resp: return []
        records: List[Dict[str, Any]] = []
        date_iso = to_western_iso(dt)
        # TWSE MI_INDEX 回傳含多個 table; 個股表通常在 tables[idx] 或 data9
        rows = []
        if "tables" in resp:
            # 新版 MI_INDEX 格式
            for tbl in resp.get("tables", []):
                fields = tbl.get("fields", [])
                if ("證券代號" in fields or "證券代號 " in fields or
                    any("代號" in str(f) for f in fields)):
                    rows = tbl.get("data", [])
                    break
        if not rows:
            for k in ("data9", "data", "aaData"):
                v = resp.get(k)
                if isinstance(v, list) and len(v) > 100:   # 個股表通常 >100 列
                    rows = v
                    break
        for r in rows:
            if not r or len(r) < 9: continue
            ticker = str(r[0]).strip() if r[0] is not None else ""
            name   = str(r[1]).strip() if len(r) > 1 and r[1] else ""
            if not ticker or not ticker[0].isdigit(): continue
            rec = {
                "Date":         date_iso,
                "Market":       "TWSE",
                "Ticker":       ticker,
                "Name":         name,
                "Volume_Share": safe_num(r[2])  if len(r) > 2 else None,
                "Trades":       safe_num(r[3])  if len(r) > 3 else None,
                "Value":        safe_num(r[4])  if len(r) > 4 else None,
                "Open":         safe_num(r[5])  if len(r) > 5 else None,
                "High":         safe_num(r[6])  if len(r) > 6 else None,
                "Low":          safe_num(r[7])  if len(r) > 7 else None,
                "Close":        safe_num(r[8])  if len(r) > 8 else None,
                "Change":       safe_num(r[9])  if len(r) > 9 else None,
                "ChangePct":    None,
            }
            if rec["Close"] is not None and rec["Change"] is not None and rec["Close"] != rec["Change"]:
                prev = rec["Close"] - rec["Change"]
                if prev and prev > 0:
                    rec["ChangePct"] = round(rec["Change"] / prev * 100, 4)
            records.append(rec)
        return records

    def _fetch_twse_all(self, dt: datetime) -> List[Dict[str, Any]]:
        if not FETCH_ALL_EQUITIES_TWSE: return []
        resp = self._fetch_twse_stocks_aegis(dt)
        if resp is None:
            resp = self._fetch_twse_stocks_http(dt)
        recs = self._parse_twse_stocks(resp, dt)
        self._diag_done_twse = True
        return recs

    # ─── TPEX 全上櫃個股 ────────────────────────────────────────────────
    def _fetch_tpex_stocks_aegis(self, dt: datetime) -> Optional[dict]:
        if self.aegis_tpex_fn is None: return None
        try:
            # TPEX 多用民國年/月/日
            resp = self.aegis_tpex_fn(to_roc_slash(dt))
            if not self._diag_done_tpex and DIAGNOSTIC_MODE:
                print_raw_response(self.aegis_tpex_fn.__name__, (to_roc_slash(dt),), resp)
            return resp
        except Exception as e:
            _log("warning", f"Aegis TPEX 個股 失敗: {e}")
            return None

    def _fetch_tpex_stocks_http(self, dt: datetime) -> Optional[dict]:
        """HTTP fallback: TPEX daily_close_quotes (民國格式 YYY/MM/DD)"""
        if not HTTP_FALLBACK_ENABLED: return None
        requests = globals().get('requests')
        if requests is None: return None
        params = {
            "l":    "zh-tw",
            "d":    to_roc_slash(dt),
            "_":    str(int(time.time() * 1000)),
        }
        for attempt in range(MAX_RETRIES):
            try:
                r = requests.get(TPEX_PUBLIC_STOCK_DAY, params=params,
                                 headers=HTTP_HEADERS, timeout=REQUEST_TIMEOUT)
                if r.status_code == 200:
                    try:
                        data = r.json()
                    except Exception:
                        data = None
                    if not self._diag_done_tpex and DIAGNOSTIC_MODE:
                        print_raw_response("HTTP TPEX daily_close",
                                           (to_roc_slash(dt),), data)
                    return data
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    _log("warning", f"TPEX HTTP {to_roc_slash(dt)} 重試 ({attempt+1}): {e}")
                    time.sleep(RETRY_DELAY)
        return None

    def _parse_tpex_stocks(self, resp: dict, dt: datetime) -> List[Dict[str, Any]]:
        if not resp: return []
        records: List[Dict[str, Any]] = []
        date_iso = to_western_iso(dt)
        rows = []
        for k in ("aaData", "data"):
            v = resp.get(k)
            if isinstance(v, list) and v:
                rows = v; break
        for r in rows:
            if not r or len(r) < 9: continue
            ticker = str(r[0]).strip() if r[0] is not None else ""
            name   = str(r[1]).strip() if len(r) > 1 and r[1] else ""
            if not ticker or not ticker[0].isdigit(): continue
            # TPEX 欄位順序: 0=代號 1=名稱 2=收盤 3=漲跌 4=開盤 5=最高 6=最低 7=均價
            # 8=成交股數 9=成交金額 10=成交筆數 ... (隨年份微異)
            rec = {
                "Date":         date_iso,
                "Market":       "TPEX",
                "Ticker":       ticker,
                "Name":         name,
                "Close":        safe_num(r[2])  if len(r) > 2  else None,
                "Change":       safe_num(r[3])  if len(r) > 3  else None,
                "Open":         safe_num(r[4])  if len(r) > 4  else None,
                "High":         safe_num(r[5])  if len(r) > 5  else None,
                "Low":          safe_num(r[6])  if len(r) > 6  else None,
                "Volume_Share": safe_num(r[8])  if len(r) > 8  else None,
                "Value":        safe_num(r[9])  if len(r) > 9  else None,
                "Trades":       safe_num(r[10]) if len(r) > 10 else None,
                "ChangePct":    None,
            }
            if rec["Close"] is not None and rec["Change"] is not None:
                prev = rec["Close"] - rec["Change"]
                if prev and prev > 0:
                    rec["ChangePct"] = round(rec["Change"] / prev * 100, 4)
            records.append(rec)
        return records

    def _fetch_tpex_all(self, dt: datetime) -> List[Dict[str, Any]]:
        if not FETCH_ALL_EQUITIES_TPEX: return []
        resp = self._fetch_tpex_stocks_aegis(dt)
        if resp is None:
            resp = self._fetch_tpex_stocks_http(dt)
        recs = self._parse_tpex_stocks(resp, dt)
        self._diag_done_tpex = True
        return recs

    # ─── 同步一日 fetch ────────────────────────────────────────────────
    def fetch_one_day(self, dt: datetime) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        if FETCH_ALL_EQUITIES_TWSE:
            records.extend(self._fetch_twse_all(dt))
        if FETCH_ALL_EQUITIES_TPEX:
            records.extend(self._fetch_tpex_all(dt))
        return records

    # ─── 非同步批次 fetch (v17 加速 · 用 ThreadPoolExecutor 避免 asyncio 巢狀問題) ──
    def _fetch_batch_threaded(self, dates: List[datetime]) -> List[Dict[str, Any]]:
        """用 ThreadPoolExecutor 並發抓取一批日期。

        為什麼用 thread 而非 asyncio:
          requests 是 sync, 且若外層已在 event loop 內 (例如 process_stocks),
          asyncio.run() 會炸 RuntimeError. ThreadPoolExecutor 在 sync/async
          兩種環境都穩定運作.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        all_records: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=ASYNC_MAX_CONCURRENT) as pool:
            future_to_dt = {pool.submit(self.fetch_one_day, dt): dt for dt in dates}
            completed = 0
            for fut in as_completed(future_to_dt):
                try:
                    recs = fut.result()
                    all_records.extend(recs)
                except Exception as e:
                    dt = future_to_dt[fut]
                    _log("warning", f"  thread err {to_western_iso(dt)}: {e}")
                completed += 1
                if completed % 5 == 0 or completed == len(dates):
                    _log("info", f"  [thread] {completed}/{len(dates)} 日完成 (累計 {len(all_records)} 列)")
        return all_records

    # ─── 主執行 ────────────────────────────────────────────────────────
    def run_extraction(self):
        pd = globals().get('pd')
        if pd is None:
            _log("error", "pandas 未載入"); return None
        if not VAN_AVAILABLE and not HTTP_FALLBACK_ENABLED:
            _log("error", "無 Aegis 且 HTTP fallback 關閉, 無法抓個股"); return None

        end_date = datetime.now() if USE_CURRENT_DATE_AS_END else datetime.strptime(INDEX_END_DATE, "%Y-%m-%d")
        all_dates = get_date_range(INDEX_START_DATE, end_date.strftime("%Y-%m-%d"))
        if SKIP_WEEKENDS:
            all_dates = [d for d in all_dates if d.weekday() < 5]

        known_holiday_count = sum(1 for d in all_dates if is_known_tw_holiday(d))
        if known_holiday_count > 0:
            all_dates = [d for d in all_dates if not is_known_tw_holiday(d)]
            _log("info", f"📅 [Equity] 預過濾已知法定假日: {known_holiday_count} 天")

        # 既有資料 (按年聚合)
        existing_dates: set = set()
        years_in_range = set(d.year for d in all_dates)
        for yr in years_in_range:
            existing_dates |= self.fm.get_existing_dates(yr)
        known_holidays = self.fm.load_holiday_dates()

        # 污染 cache 自動偵測
        if known_holidays and len(all_dates) > 0:
            overlap = sum(1 for d in all_dates if to_western_iso(d) in known_holidays)
            ratio = overlap / len(all_dates)
            if ratio > 0.80 and not existing_dates:
                _log("warning", f"⚠️ Equity holiday cache 異常 ({ratio:.0%}) 且既有空 → 自動重置")
                try:
                    self.fm.holiday_file.unlink()
                    known_holidays = set()
                except Exception as e:
                    _log("error", f"無法刪除 equity cache: {e}")

        skip = existing_dates | known_holidays
        missing = [d for d in all_dates if to_western_iso(d) not in skip]

        _log("info", f"📅 [Equity] 共 {len(all_dates)} 個交易日, 需更新 {len(missing)} 日")
        if not missing:
            _log("info", "✅ 個股資料已是最新")
            # 仍載入既有檔案供 summary 統計; 標記 _no_save 屬性避免重複寫檔
            existing_dfs = []
            for yr in years_in_range:
                df_yr = self.fm.load_existing_year(yr)
                if df_yr is not None and not df_yr.empty:
                    existing_dfs.append(df_yr)
            if existing_dfs:
                merged = pd.concat(existing_dfs, ignore_index=True)
                self._no_save = True   # 提示 caller 不要再寫一遍
                return merged
            return pd.DataFrame()

        new_records: List[Dict[str, Any]] = []
        consecutive_holidays = 0

        if ENABLE_ASYNC_BATCH:
            _log("info", f"🚀 啟用 ThreadPool 並發抓取 (max_workers={ASYNC_MAX_CONCURRENT})")
            # 分批處理: 批間統計 holiday, 避免連續 holiday 卡死整個批次
            batch_size = ASYNC_MAX_CONCURRENT * 2
            for batch_start in range(0, len(missing), batch_size):
                batch = missing[batch_start:batch_start + batch_size]
                _log("info", f"  批次 {batch_start//batch_size + 1}: {to_western_iso(batch[0])} ~ {to_western_iso(batch[-1])}")
                batch_recs = self._fetch_batch_threaded(batch)
                # 統計每日有無資料, 標記 holiday
                got_dates = set(r["Date"] for r in batch_recs)
                for dt in batch:
                    if to_western_iso(dt) not in got_dates:
                        self._new_holidays.add(to_western_iso(dt))
                new_records.extend(batch_recs)
                time.sleep(REQUEST_INTERVAL_SEC)
        else:
            for i, dt in enumerate(missing, start=1):
                _log("info", f"[{i}/{len(missing)}] 擷取個股 {to_western_iso(dt)}")
                recs = self.fetch_one_day(dt)
                if not recs:
                    self._new_holidays.add(to_western_iso(dt))
                    consecutive_holidays += 1
                    _log("info", f"  ⏭️ holiday (連續 {consecutive_holidays} 天)")
                    if MAX_CONSECUTIVE_HOLIDAYS > 0 and consecutive_holidays >= MAX_CONSECUTIVE_HOLIDAYS:
                        _log("error", f"❌ 連續 {consecutive_holidays} 天無資料 → 停止")
                        break
                else:
                    consecutive_holidays = 0
                    new_records.extend(recs)
                    _log("info", f"  ✓ 抓到 {len(recs)} 檔個股")
                time.sleep(REQUEST_INTERVAL_SEC)

        df = pd.DataFrame(new_records)
        if df.empty:
            _log("warning", "個股抓取結果為空")
            return df

        if VC_AVAILABLE:
            try:
                df = vc.DataValidator.clean_dataframe(df)
            except Exception as e:
                _log("warning", f"Celeritas clean 失敗: {e}")

        # 標準型別
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors='coerce').dt.strftime('%Y-%m-%d')
        if "Ticker" in df.columns:
            df["Ticker"] = df["Ticker"].astype(str)

        # 更新 holiday cache
        all_holidays = known_holidays | self._new_holidays
        if self._new_holidays:
            self.fm.save_holiday_dates(all_holidays)
            _log("info", f"📝 [Equity] holiday 更新: 新增 {len(self._new_holidays)} 天")

        return df


# =====================================================================================
# 🚀 [BLOCK-7] SmartAutoDeployController (v16 原樣保留)
# =====================================================================================

class SmartAutoDeployController:
    """智能自動部署控制器"""

    def __init__(self):
        self.dependency_checker = IntelligentDependencyChecker()
        self.module_importer = IntelligentModuleImporter()
        self.deployment_successful = False
        print(f"🏛️ {SYSTEM_NAME} 初始化...")

    def run_smart_deployment(self) -> bool:
        try:
            print("\n" + "=" * 80)
            print("🚀 開始智能自動部署流程")
            print("=" * 80)

            print("\n📊 步驟1: 全面依賴掃描")
            scan_result = self.dependency_checker.comprehensive_dependency_scan()

            if scan_result['installation_needed']:
                print("\n🔧 步驟2: 智能安裝缺少的依賴")
                install_result = self.dependency_checker.intelligent_install_missing_packages()
            else:
                print("\n⏭️ 步驟2: 跳過安裝（所有依賴都已就緒）")
                install_result = {'installation_performed': False}

            print("\n🔄 步驟3: 智能模組導入")
            import_success = self.module_importer.smart_import_all_modules()

            print("\n✅ 步驟4: 系統就緒檢查")
            self.deployment_successful = self._validate_deployment_success(
                scan_result, install_result, import_success
            )

            print("\n📋 步驟5: 生成部署報告")
            self._generate_deployment_report(scan_result, install_result, import_success)

            return self.deployment_successful

        except Exception as e:
            print(f"\n❌ 智能部署失敗: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _validate_deployment_success(self, scan_result, install_result, import_success):
        print("   🔍 驗證部署結果...")
        validation_checks = []
        validation_checks.append(('關鍵模組導入', import_success))
        if install_result.get('installation_performed', False):
            install_success = install_result.get('failed_installs', 0) == 0
            validation_checks.append(('包安裝', install_success))
        availability_rate = (scan_result['available_packages'] / scan_result['total_packages']) * 100
        deps_ok = availability_rate >= 80
        validation_checks.append(('依賴可用性', deps_ok))
        validation_checks.append(('Veritas 可用 (非阻斷)', VAN_AVAILABLE))

        all_passed = True
        for check_name, passed in validation_checks:
            status = "✅ 通過" if passed else "❌ 失敗"
            print(f"     {check_name}: {status}")
            if not passed and "Veritas" not in check_name:
                all_passed = False

        if all_passed:
            print("   🎉 智能部署成功！系統已就緒")
        else:
            print("   ⚠️ 部分檢查未通過，將在降級模式運行")
        return all_passed

    def _generate_deployment_report(self, scan_result, install_result, import_success):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            Path(REPORT_DIR).mkdir(parents=True, exist_ok=True)
            report_data = {
                'timestamp': timestamp,
                'system_version': SYSTEM_VERSION,
                'deployment_type': 'vdf_mdl001_v17',
                'scan_result': scan_result,
                'install_result': install_result,
                'import_success': import_success,
                'deployment_successful': self.deployment_successful,
                'veritas_available': VAN_AVAILABLE,
                'celeritas_available': VC_AVAILABLE,
                'http_fallback_enabled': HTTP_FALLBACK_ENABLED,
                'async_batch_enabled': ENABLE_ASYNC_BATCH,
                'python_version': sys.version,
                'platform': platform.platform()
            }
            report_file = Path(REPORT_DIR) / f"vdf_mdl001_deployment_{timestamp}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"   💾 部署報告: {report_file.name}")
            try:
                import rich  # noqa
                self._display_rich_report(report_data)
            except ImportError:
                self._display_simple_report(report_data)
        except Exception as e:
            print(f"   ⚠️ 報告生成失敗: {e}")

    def _display_rich_report(self, report_data: Dict):
        try:
            from rich.console import Console
            from rich.table import Table
            console = Console()
            table = Table(title="🏛️ VDF MDL001 部署摘要 (v17)")
            table.add_column("項目", style="cyan", width=22)
            table.add_column("結果", style="green", width=15)
            table.add_column("詳情", style="yellow", width=42)
            scan = report_data['scan_result']
            inst = report_data['install_result']
            table.add_row("總包數", str(scan['total_packages']), "檢查了所有必需的依賴包")
            table.add_row("可用包數", str(scan['available_packages']), "無需安裝，直接可用")
            if inst.get('installation_performed'):
                table.add_row("新安裝", str(inst['successful_installs']), "成功安裝/升級的包")
                if inst['failed_installs'] > 0:
                    table.add_row("安裝失敗", str(inst['failed_installs']), "部分包安裝失敗")
            else:
                table.add_row("安裝操作", "無需安裝", "所有依賴都已就緒")
            table.add_row("Veritas Aegis",
                          "✅" if report_data['veritas_available'] else "⚠️",
                          "TWSE/TPEX 真實 API" if report_data['veritas_available'] else "未載入, 走 HTTP fallback")
            table.add_row("Veritas Celeritas",
                          "✅" if report_data['celeritas_available'] else "⚠️",
                          "DataValidator + logger" if report_data['celeritas_available'] else "未載入")
            table.add_row("HTTP Fallback",
                          "✅" if report_data['http_fallback_enabled'] else "❌",
                          "TWSE/TPEX 公開 API 直連可用")
            table.add_row("Async 並發",
                          "✅" if report_data['async_batch_enabled'] else "❌",
                          f"max_concurrent={ASYNC_MAX_CONCURRENT}" if report_data['async_batch_enabled'] else "關閉")
            table.add_row("系統狀態",
                          "✅ 就緒" if report_data['deployment_successful'] else "⚠️ 降級",
                          "可開始抓取" if report_data['deployment_successful'] else "部分功能受限")
            console.print(table)
        except Exception as e:
            print(f"   ⚠️ Rich報告顯示失敗: {e}")
            self._display_simple_report(report_data)

    def _display_simple_report(self, report_data: Dict):
        print("\n" + "=" * 60)
        print("📋 VDF MDL001 部署摘要 (v17)")
        print("=" * 60)
        scan = report_data['scan_result']
        inst = report_data['install_result']
        print(f"📊 依賴: 總 {scan['total_packages']} / 可用 {scan['available_packages']}")
        if inst.get('installation_performed'):
            print(f"🔧 安裝: 成功 {inst['successful_installs']} / 失敗 {inst['failed_installs']}")
        print(f"🔌 Veritas: {'✅' if report_data['veritas_available'] else '⚠️'}")
        print(f"🌐 HTTP fallback: {'✅' if report_data['http_fallback_enabled'] else '❌'}")
        print(f"⚡ Async: {'✅' if report_data['async_batch_enabled'] else '❌'}")
        print(f"🎯 狀態: {'✅ 就緒' if report_data['deployment_successful'] else '⚠️ 降級'}")
        print("=" * 60)


# =====================================================================================
# 📊 [BLOCK-8] EnhancedStockProcessor (v16 保留 + v17 新增個股全市場)
# =====================================================================================

class EnhancedStockProcessor:
    """增強股票處理器 — 整合指數抓取 (v16) + 全市場個股 (v17)"""

    def __init__(self):
        print("📈 初始化增強股票處理器...")
        self.pandas_available  = 'pd' in globals()
        self.aiohttp_available = 'aiohttp' in globals()
        self.veritas_available = VAN_AVAILABLE
        self.summary = {
            "index_rows":   0,
            "equity_rows":  0,
            "equity_years": [],
            "csv_files":    [],
            "parquet_files":[],
            "elapsed_sec":  0.0,
            "modes_ok":     [],
            "modes_failed": [],
            "latest_taiex": None,
            "latest_tpex":  None,
            "twse_stocks":  0,
            "tpex_stocks":  0,
        }
        print(f"   Pandas: {'✅' if self.pandas_available else '❌'}")
        print(f"   AsyncHTTP: {'✅' if self.aiohttp_available else '❌'}")
        print(f"   Veritas: {'✅' if self.veritas_available else '❌'}")

    async def process_stocks(self, mode: str = "all"):
        """主處理.
        mode: "all" / "index_only" / "equity_only"
        """
        t0 = time.time()
        results: Dict[str, bool] = {}

        # 1. 指數抓取
        if mode in ("all", "index_only"):
            if self.veritas_available:
                print("\n📊 [模式 A] 真實 TWSE/TPEX 指數抓取")
                ok = await self._fetch_real_indices()
                results["index_real"] = ok
                (self.summary["modes_ok"] if ok else self.summary["modes_failed"]).append("Index")
            else:
                print("\n⚠️ [模式 A] Veritas 未載入, 跳過指數抓取")
                results["index_real"] = False
                self.summary["modes_failed"].append("Index (no Aegis)")

        # 2. 全市場個股抓取 (v17 新增)
        if mode in ("all", "equity_only"):
            print("\n📊 [模式 B] 真實 TWSE/TPEX 全市場個股抓取")
            ok = await self._fetch_real_equities()
            results["equity_real"] = ok
            (self.summary["modes_ok"] if ok else self.summary["modes_failed"]).append("Equity")

        # 3. 個股 demo (v15.1 保留)
        if mode == "all":
            print("\n📊 [模式 C] 個股 Demo 處理 (沿用 v15.1, 假資料)")
            if self.pandas_available:
                results["stock_demo"] = await self._advanced_processing()
            else:
                results["stock_demo"] = self._basic_processing()
            (self.summary["modes_ok"] if results["stock_demo"] else self.summary["modes_failed"]).append("Demo")

        self.summary["elapsed_sec"] = round(time.time() - t0, 2)
        return any(results.values())

    async def _fetch_real_indices(self) -> bool:
        try:
            fetcher = RealIndexFetcher()
            df = fetcher.run_extraction()
            if df is None or df.empty:
                _log("warning", "指數抓取結果為空")
                return False
            if getattr(fetcher, "_no_save", False):
                _log("info", "指數資料已是最新, 跳過寫檔, 直接統計")
                save_results = {"csv": False, "parquet": False}
            else:
                save_results = fetcher.fm.save_dataframe(df)
            self.summary["index_rows"] = len(df)
            if save_results.get("csv"):     self.summary["csv_files"].append(fetcher.fm.csv_file.name)
            if save_results.get("parquet"): self.summary["parquet_files"].append(fetcher.fm.parquet_file.name)
            print(f"\n   ✅ 真實指數: {len(df)} 列 | CSV={save_results.get('csv')} | Parquet={save_results.get('parquet')}")
            if "Index" in df.columns and len(df) > 0:
                last_date = df["Date"].max()
                latest = df[df["Date"] == last_date]
                print(f"\n   最新日 ({last_date}):")
                for _, row in latest.iterrows():
                    line = f"     [{row['Index']}] Close={row.get('Close')}  Foreign={row.get('Foreign_Net')}  券資比={row.get('Short_Margin_Ratio_Pct')}%"
                    print(line)
                    if row["Index"] == "TAIEX": self.summary["latest_taiex"] = row.get("Close")
                    if row["Index"] == "TPEX":  self.summary["latest_tpex"]  = row.get("Close")
            return True
        except Exception as e:
            _log("error", f"指數抓取失敗: {e}")
            import traceback; traceback.print_exc()
            return False

    async def _fetch_real_equities(self) -> bool:
        try:
            fetcher = RealEquityFetcher()
            df = fetcher.run_extraction()
            if df is None:
                _log("warning", "個股抓取回傳 None")
                return False
            if df.empty:
                _log("warning", "個股抓取結果為空 (無增量, 且無既有資料)")
                return False
            # 若 fetcher 標記 _no_save (= 純載入既有), 跳過再寫一次
            if getattr(fetcher, "_no_save", False):
                _log("info", "個股資料已是最新, 跳過寫檔, 直接統計")
                save_results = {"rows_per_year": {}, "csv": [], "parquet": []}
            else:
                save_results = fetcher.fm.save_dataframe(df)
            self.summary["equity_rows"]  = len(df)
            self.summary["equity_years"] = sorted(save_results.get("rows_per_year", {}).keys())
            self.summary["csv_files"].extend(save_results.get("csv", []))
            self.summary["parquet_files"].extend(save_results.get("parquet", []))
            if "Market" in df.columns:
                self.summary["twse_stocks"] = int(df[df["Market"] == "TWSE"]["Ticker"].nunique())
                self.summary["tpex_stocks"] = int(df[df["Market"] == "TPEX"]["Ticker"].nunique())
            print(f"\n   ✅ 全市場個股: {len(df):,} 列 | TWSE={self.summary['twse_stocks']} 檔 | TPEX={self.summary['tpex_stocks']} 檔")
            print(f"   📁 輸出目錄: {fetcher.fm.output_dir}")
            return True
        except Exception as e:
            _log("error", f"個股抓取失敗: {e}")
            import traceback; traceback.print_exc()
            return False

    async def _advanced_processing(self) -> bool:
        print("   🚀 v15.1 個股 Demo (假資料)")
        pd = globals()['pd']
        data = []
        for stock in DEFAULT_STOCK_LIST:
            for i in range(10):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                data.append({
                    'date': date, 'ticker': stock['ticker'], 'name': stock['name'],
                    'close': 100 + random.uniform(-10, 10),
                    'volume': random.randint(1000000, 10000000)
                })
        df = pd.DataFrame(data)
        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        output_file = Path(OUTPUT_DIR) / f"stock_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"   ✅ Demo 完成: {len(df)} 筆 → {output_file.name}")
        return True

    def _basic_processing(self) -> bool:
        print("   🔧 基本處理 (fallback)")
        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        output_file = Path(OUTPUT_DIR) / f"stock_demo_basic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['date', 'ticker', 'name', 'close', 'volume'])
            for stock in DEFAULT_STOCK_LIST:
                for i in range(10):
                    date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                    writer.writerow([date, stock['ticker'], stock['name'],
                                     100 + random.uniform(-10, 10),
                                     random.randint(1000000, 10000000)])
        print(f"   ✅ 基本 demo: {output_file.name}")
        return True


# =====================================================================================
# 🎨 [BLOCK-8b] Rich Summary Matrix (v17 新增 — 詳細彙總表)
# =====================================================================================

def print_rich_summary_matrix(processor: EnhancedStockProcessor,
                              deployment_success: bool,
                              processing_success: bool):
    """印詳細彙總矩陣 (用 Rich)"""
    s = processor.summary
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich import box
    except ImportError:
        _print_plain_summary(processor, deployment_success, processing_success)
        return

    console = Console()

    # ─── Header banner ───────────────────────────────────────────────
    console.rule(f"[bold cyan]🏛️ VDF MDL001 - TW Equity Engine · 執行彙總矩陣[/bold cyan]")

    # ─── Table 1: 系統環境 ───────────────────────────────────────────
    t_env = Table(title="📦 [bold]系統環境 / 輔助工具[/bold]",
                  box=box.ROUNDED, header_style="bold magenta")
    t_env.add_column("組件", style="cyan", width=22)
    t_env.add_column("狀態", style="green", width=12, justify="center")
    t_env.add_column("作用", style="yellow", width=46)
    t_env.add_row("pandas",            "✅" if 'pd'  in globals() else "❌", "資料表處理 (DataFrame)")
    t_env.add_row("numpy",             "✅" if 'np'  in globals() else "❌", "衍生指標計算 (券資比/維持率)")
    t_env.add_row("requests",          "✅" if 'requests' in globals() else "❌", "HTTP fallback 抓 TWSE/TPEX 公開 API")
    t_env.add_row("aiohttp",           "✅" if 'aiohttp'  in globals() else "❌", "非同步加速 (備用)")
    t_env.add_row("polars",            "✅" if POLARS_AVAILABLE    else "⚪", "高速 DataFrame (可選)")
    t_env.add_row("pyarrow",           "✅" if PYARROW_AVAILABLE   else "⚪", "Parquet 輸出 (可選)")
    t_env.add_row("rich",              "✅" if RICH_AVAILABLE      else "⚪", "彩色終端表格")
    t_env.add_row("VeritasAegisNexus", "✅" if VAN_AVAILABLE       else "⚠️", "正式 TWSE/TPEX API 通道 (Path A)")
    t_env.add_row("VeritasCeleritas",  "✅" if VC_AVAILABLE        else "⚠️", "DataValidator + logger 加速器")
    console.print(t_env)

    # ─── Table 2: 抓取項目開關 ─────────────────────────────────────
    t_sw = Table(title="🎚️ [bold]抓取項目開關 (從頂部 PARAMETERS)[/bold]",
                 box=box.ROUNDED, header_style="bold magenta")
    t_sw.add_column("層級", style="cyan", width=10)
    t_sw.add_column("項目", style="cyan", width=28)
    t_sw.add_column("開關", style="green", width=10, justify="center")
    t_sw.add_column("資料維度", style="yellow", width=32)
    t_sw.add_row("指數層", "TAIEX (加權)",          "✅" if FETCH_TAIEX else "❌",         "Close/Change/Value/量/筆")
    t_sw.add_row("指數層", "TPEX (櫃買)",           "✅" if FETCH_TPEX else "❌",          "Close/Change/Value/量")
    t_sw.add_row("籌碼層", "三大法人 (Institutional)","✅" if FETCH_INSTITUTIONAL else "❌", "外資/投信/自營淨買賣超")
    t_sw.add_row("籌碼層", "融資融券 (Margin)",     "✅" if FETCH_MARGIN else "❌",        "融資餘額/融券餘額")
    t_sw.add_row("籌碼層", "當沖 (Day Trading)",    "✅" if FETCH_DAY_TRADING else "❌",    "當沖總值")
    t_sw.add_row("衍生層", "衍生指標 (Derived)",    "✅" if COMPUTE_DERIVED else "❌",      "券資比/維持率/當沖佔比")
    t_sw.add_row("個股層", "TWSE 全上市個股",       "✅" if FETCH_ALL_EQUITIES_TWSE else "❌", "OHLCV + 漲跌 (~1000 檔)")
    t_sw.add_row("個股層", "TPEX 全上櫃個股",       "✅" if FETCH_ALL_EQUITIES_TPEX else "❌", "OHLCV + 漲跌 (~800 檔)")
    console.print(t_sw)

    # ─── Table 3: 抓取結果 ──────────────────────────────────────────
    t_res = Table(title="📊 [bold]抓取結果[/bold]",
                  box=box.ROUNDED, header_style="bold magenta")
    t_res.add_column("指標", style="cyan", width=24)
    t_res.add_column("數值", style="green", width=20, justify="right")
    t_res.add_column("說明", style="yellow", width=32)
    t_res.add_row("時間區間",     f"{INDEX_START_DATE} ~ {'今日' if USE_CURRENT_DATE_AS_END else INDEX_END_DATE}", "INDEX_START_DATE/END_DATE")
    t_res.add_row("指數列數",     f"{s['index_rows']:,}",     "TAIEX + TPEX × 交易日")
    t_res.add_row("最新 TAIEX",   str(s['latest_taiex'] or '—'), "加權指數收盤")
    t_res.add_row("最新 TPEX",    str(s['latest_tpex']  or '—'), "櫃買指數收盤")
    t_res.add_row("個股列數",     f"{s['equity_rows']:,}",    "TWSE+TPEX × 個股 × 交易日")
    t_res.add_row("TWSE 個股數",  f"{s['twse_stocks']:,} 檔", "上市 unique tickers")
    t_res.add_row("TPEX 個股數",  f"{s['tpex_stocks']:,} 檔", "上櫃 unique tickers")
    t_res.add_row("分檔年份",     ", ".join(str(y) for y in s['equity_years']) or "—", "按年 partition")
    t_res.add_row("執行時間",     f"{s['elapsed_sec']} 秒",   "抓取總耗時")
    console.print(t_res)

    # ─── Table 4: 加速與網路 ─────────────────────────────────────────
    t_acc = Table(title="⚡ [bold]加速 / 網路 (功能只增不減)[/bold]",
                  box=box.ROUNDED, header_style="bold magenta")
    t_acc.add_column("功能", style="cyan", width=24)
    t_acc.add_column("狀態", style="green", width=12, justify="center")
    t_acc.add_column("參數值", style="yellow", width=44)
    t_acc.add_row("HTTP fallback",  "✅" if HTTP_FALLBACK_ENABLED else "❌", f"TWSE/TPEX 公開 API")
    t_acc.add_row("ThreadPool 並發", "✅" if ENABLE_ASYNC_BATCH    else "❌", f"ThreadPoolExecutor, max_workers={ASYNC_MAX_CONCURRENT}")
    t_acc.add_row("Parquet 輸出",   "✅" if PYARROW_AVAILABLE     else "⚪", f"{', '.join(OUTPUT_FORMATS)}")
    t_acc.add_row("增量更新",       "✅" if ENABLE_INCREMENTAL    else "❌", "讀既有檔, 只抓 missing")
    t_acc.add_row("自動去重",       "✅" if AUTO_DEDUPLICATE      else "❌", "drop_duplicates by (Date,Ticker,Market)")
    t_acc.add_row("自動備份",       "✅" if ENABLE_BACKUP         else "❌", f"max {MAX_BACKUP_FILES} 檔")
    t_acc.add_row("Veritas Celeritas","✅" if VC_AVAILABLE        else "⚠️", "DataValidator.clean_dataframe")
    t_acc.add_row("Request interval","✅", f"{REQUEST_INTERVAL_SEC}s · retry={MAX_RETRIES}")
    console.print(t_acc)

    # ─── Table 5: 假日處理 ──────────────────────────────────────────
    t_hol = Table(title="📅 [bold]假日處理 (使用者指令: 不設限)[/bold]",
                  box=box.ROUNDED, header_style="bold magenta")
    t_hol.add_column("規則", style="cyan", width=28)
    t_hol.add_column("設定", style="green", width=14, justify="center")
    t_hol.add_column("說明", style="yellow", width=38)
    t_hol.add_row("自動跳過週末",         "✅" if SKIP_WEEKENDS else "❌", "Mon-Fri only")
    t_hol.add_row("預知法定假日",         f"{len(TW_KNOWN_HOLIDAYS_2025_2026)} 天", "2025-2026")
    t_hol.add_row("動態 holiday cache",   "✅", "兩源皆空即標 holiday")
    t_hol.add_row("污染 cache 自動偵測",   "✅", "overlap > 80% 且既有空 → 重置")
    t_hol.add_row("MAX_CONSECUTIVE_HOLIDAYS", str(MAX_CONSECUTIVE_HOLIDAYS),
                  "0 = 不設限 (永不中斷)" if MAX_CONSECUTIVE_HOLIDAYS == 0 else f"{MAX_CONSECUTIVE_HOLIDAYS} 天")
    console.print(t_hol)

    # ─── Table 6: 輸出檔 ────────────────────────────────────────────
    t_out = Table(title="💾 [bold]輸出檔案[/bold]",
                  box=box.ROUNDED, header_style="bold magenta")
    t_out.add_column("路徑", style="cyan", width=68)
    t_out.add_column("用途", style="yellow", width=30)
    t_out.add_row(INDEX_OUTPUT_DIR,  "指數 + 籌碼 + 衍生")
    t_out.add_row(EQUITY_OUTPUT_DIR, "全市場個股 (按年分檔)")
    t_out.add_row(LOG_DIR,           "Log")
    t_out.add_row(REPORT_DIR,        "部署 / 抓取 JSON 報告")
    console.print(t_out)

    # ─── Summary banner ──────────────────────────────────────────────
    summary_lines = []
    summary_lines.append(f"  部署狀態     : {'✅ 成功' if deployment_success else '⚠️ 降級'}")
    summary_lines.append(f"  抓取狀態     : {'✅ 成功' if processing_success else '❌ 失敗'}")
    summary_lines.append(f"  完成模式     : {', '.join(s['modes_ok']) or '(無)'}")
    if s['modes_failed']:
        summary_lines.append(f"  失敗 / 跳過  : {', '.join(s['modes_failed'])}")
    summary_lines.append(f"  指數列數     : {s['index_rows']:,}")
    summary_lines.append(f"  個股列數     : {s['equity_rows']:,}  (TWSE {s['twse_stocks']} + TPEX {s['tpex_stocks']} 檔)")
    summary_lines.append(f"  執行耗時     : {s['elapsed_sec']} 秒")
    overall = "[bold green]✅ 系統運行正常[/bold green]" if (deployment_success and processing_success) else "[bold yellow]⚠️ 部分功能受限[/bold yellow]"
    panel = Panel.fit("\n".join(summary_lines) + f"\n\n  {overall}",
                      title="[bold cyan]🎯 整體狀態[/bold cyan]",
                      border_style="cyan")
    console.print(panel)
    console.rule(f"[dim]版本: {SYSTEM_VERSION} · 構建: {BUILD_DATE} · {AUTHOR}[/dim]")


def _print_plain_summary(processor, deployment_success, processing_success):
    """Rich 不可用時的純文字 fallback"""
    s = processor.summary
    bar = "=" * 80
    print(f"\n{bar}\n🏛️ VDF MDL001 - 執行彙總\n{bar}")
    print(f"  部署   : {'✅' if deployment_success else '⚠️'}")
    print(f"  抓取   : {'✅' if processing_success else '❌'}")
    print(f"  指數   : {s['index_rows']:,} 列")
    print(f"  個股   : {s['equity_rows']:,} 列 (TWSE {s['twse_stocks']} / TPEX {s['tpex_stocks']})")
    print(f"  耗時   : {s['elapsed_sec']}s")
    print(bar)


# =====================================================================================
# 🚀 [BLOCK-9] main() 主程式
# =====================================================================================

async def main():
    try:
        print("=" * 80)
        print(f"🏛️ {SYSTEM_NAME}")
        print(f"📋 版本: {SYSTEM_VERSION} | 構建: {BUILD_DATE}")
        print(f"📋 沿襲: v16 (smart_tw_system) → v17 (VDF MDL001, +全市場個股)")
        print("=" * 80)

        # CLI flags
        if "--reset-holidays" in sys.argv:
            for fm_cls in (IndexFileManager, EquityFileManager):
                fm = fm_cls()
                if fm.holiday_file.exists():
                    fm.holiday_file.unlink()
                    print(f"✅ 已刪除: {fm.holiday_file}")
                else:
                    print(f"ℹ️ 不存在: {fm.holiday_file}")
            if "--only-reset" in sys.argv:
                return 0

        if "--reset-all" in sys.argv:
            fm = IndexFileManager()
            for f in [fm.csv_file, fm.parquet_file, fm.holiday_file]:
                if f.exists():
                    f.unlink(); print(f"✅ 已刪除: {f}")
            efm = EquityFileManager()
            if efm.holiday_file.exists():
                efm.holiday_file.unlink(); print(f"✅ 已刪除: {efm.holiday_file}")
            for ext in ("csv", "parquet"):
                for fp in efm.output_dir.glob(f"TWEquity_Daily_*.{ext}"):
                    fp.unlink(); print(f"✅ 已刪除: {fp.name}")
            if "--only-reset" in sys.argv:
                return 0

        # 決定模式
        mode = "all"
        if "--index-only" in sys.argv:   mode = "index_only"
        if "--equity-only" in sys.argv:  mode = "equity_only"

        # Step 1: 智能部署
        controller = SmartAutoDeployController()
        deployment_success = controller.run_smart_deployment()

        # Step 2: 抓取
        print("\n" + "=" * 80)
        print(f"📈 開始資料抓取  (mode={mode})")
        print("=" * 80)
        processor = EnhancedStockProcessor()
        processing_success = await processor.process_stocks(mode=mode)

        # Step 3: Rich 彙總矩陣
        print("\n")
        print_rich_summary_matrix(processor, deployment_success, processing_success)

        # Step 4: 結束狀態
        if deployment_success and processing_success:
            return 0
        elif processing_success:
            return 0
        else:
            return 1

    except Exception as e:
        print(f"❌ 主程式執行失敗: {e}")
        import traceback; traceback.print_exc()
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        print(f"\n程式結束，退出碼: {exit_code}")
        if "--no-pause" not in sys.argv:
            try:
                input("按 Enter 鍵退出...")
            except (EOFError, KeyboardInterrupt):
                pass
    except KeyboardInterrupt:
        print("\n⚠️ 用戶中斷")
    except Exception as e:
        print(f"\n💥 系統錯誤: {e}")
        if "--no-pause" not in sys.argv:
            try:
                input("按 Enter 鍵退出...")
            except (EOFError, KeyboardInterrupt):
                pass
