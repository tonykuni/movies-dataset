# VRN Phase-3 项目目录结构

```
C:\VeritasReportNova\
│
├── 重新整合\
│   └── output\
│       │
│       ├── phase1_extracted\              # Phase-1 输出（PDF 提取原始数据）
│       │   ├── raw_tables\
│       │   ├── images\
│       │   └── metadata\
│       │
│       ├── phase2_structured\             # Phase-2 输出（结构化表格）★ 输入源
│       │   ├── csv\                       # CSV 格式表格
│       │   │   ├── earnings_2024Q1.csv
│       │   │   ├── valuation_data.csv
│       │   │   └── ...
│       │   │
│       │   ├── csv_from_json\             # 从 JSON 转换的 CSV
│       │   │   ├── financial_metrics.csv
│       │   │   └── ...
│       │   │
│       │   ├── tables\                    # JSON 格式表格
│       │   │   ├── table_001.json
│       │   │   ├── table_002.jsonl
│       │   │   └── ...
│       │   │
│       │   └── metadata.json              # 元数据
│       │
│       └── phase3_final\                  # Phase-3 输出（最终报告）★ 输出目标
│           │
│           ├── excel\                     # Excel 输出
│           │   ├── phase3_output.xlsx
│           │   └── custom_report_*.xlsx
│           │
│           ├── html\                      # HTML 报告
│           │   ├── phase3_report.html
│           │   └── analysis_*.html
│           │
│           ├── json\                      # JSON 输出
│           │   ├── phase3_output.json
│           │   └── data_export_*.json
│           │
│           ├── parquet\                   # Parquet 文件
│           │   ├── earnings_2024Q1.parquet
│           │   ├── valuation_data.parquet
│           │   └── ...
│           │
│           ├── sqlite\                    # SQLite 数据库（可选）
│           │   └── phase3_database.db
│           │
│           ├── reports\                   # 分析报告
│           │   ├── summary_report.json
│           │   ├── validation_report.md
│           │   └── quality_report.html
│           │
│           └── phase3_log_*.txt           # 执行日志
│
├── phase_3\                               # Phase-3 脚本目录
│   ├── veritas_phase3_ultimate.py         # 主程序 ★
│   ├── quickstart_phase3.py               # 快速启动脚本 ★
│   ├── examples_phase3.py                 # 示例程序
│   ├── plugin_template.py                 # 插件模板
│   ├── requirements_phase3.txt            # 依赖清单
│   ├── README_Phase3.md                   # 使用说明 ★
│   │
│   ├── plugins\                           # 自定义插件目录
│   │   ├── __init__.py
│   │   ├── financial_analysis.py
│   │   ├── data_quality.py
│   │   └── custom_transforms.py
│   │
│   └── config\                            # 配置文件目录
│       ├── default_config.json
│       └── production_config.json
│
├── venv_isolated\                         # Python 虚拟环境
│   ├── Scripts\
│   ├── Lib\
│   └── ...
│
├── Activate-VrnEnv.ps1                    # 虚拟环境启动脚本
├── VRN_Environment_Guide.md               # 环境配置指南
└── vrn_optimization_config.json           # 优化配置

```

## 📂 关键目录说明

### 输入目录（Phase-2 输出）

**位置：** `重新整合/output/phase2_structured/`

**内容：**
- `csv/` - 标准 CSV 格式表格
- `csv_from_json/` - 从 JSON 转换的 CSV
- `tables/` - JSON/JSONL 格式表格

**要求：**
- 文件编码：UTF-8
- CSV 分隔符：逗号 (,)
- JSON 格式：标准 JSON 或 JSON Lines

### 输出目录（Phase-3 输出）

**位置：** `重新整合/output/phase3_final/`

**内容：**
- `excel/` - Excel 工作簿（多工作表）
- `html/` - 美化的 HTML 报告
- `json/` - JSON 格式数据
- `parquet/` - 列式存储文件（大数据）
- `reports/` - 摘要和分析报告

**特点：**
- 自动创建时间戳子目录
- 包含完整的执行日志
- 提供数据质量验证报告

### 脚本目录

**位置：** `phase_3/`

**关键文件：**
- `veritas_phase3_ultimate.py` - **主程序**，模块化系统核心
- `quickstart_phase3.py` - **快速启动**，交互式配置
- `examples_phase3.py` - **示例集**，展示各种用法
- `plugin_template.py` - **插件模板**，快速开发新功能
- `README_Phase3.md` - **完整文档**，使用说明和 API 参考

## 🔄 数据流向图

```
Phase-1 (PDF 提取)
    │
    │ 原始 PDF 文件
    ↓
┌──────────────────────┐
│ phase1_extracted/    │
│  - raw_tables/       │
│  - images/           │
└──────────────────────┘
    │
    │ 表格图片、元数据
    ↓
Phase-2 (表格结构化)
    │
    │ OCR、结构识别
    ↓
┌──────────────────────┐
│ phase2_structured/   │ ← Phase-3 输入源 ★
│  - csv/              │
│  - csv_from_json/    │
│  - tables/           │
└──────────────────────┘
    │
    │ 结构化表格数据
    ↓
Phase-3 (最终报告)
    │
    │ 数据处理、验证、转换
    ↓
┌──────────────────────┐
│ phase3_final/        │ ← Phase-3 输出目标 ★
│  - excel/            │
│  - html/             │
│  - json/             │
│  - parquet/          │
│  - reports/          │
└──────────────────────┘
    │
    │ 多格式最终报告
    ↓
下游应用
  - 人工审阅（Excel）
  - 在线展示（HTML）
  - API 集成（JSON）
  - 大数据分析（Parquet）
```

## 📋 文件命名规范

### 输入文件（Phase-2 输出）

```
格式：<类型>_<日期或序号>.<扩展名>

示例：
  earnings_2024Q1.csv
  valuation_data.csv
  table_001.json
  financial_metrics_20241103.jsonl
```

### 输出文件（Phase-3 生成）

```
格式：phase3_<类型>_<时间戳>.<扩展名>

示例：
  phase3_output_20251103_143052.xlsx
  phase3_report_20251103_143052.html
  phase3_log_20251103_143052.txt
  summary_report.json
```

### 日志文件

```
格式：phase3_log_YYYYMMDD_HHMMSS.txt

示例：
  phase3_log_20251103_143052.txt
```

## 🔍 目录权限要求

### Windows

```powershell
# 输入目录：只读
icacls "C:\VeritasReportNova\重新整合\output\phase2_structured" /grant Users:R

# 输出目录：读写
icacls "C:\VeritasReportNova\重新整合\output\phase3_final" /grant Users:(OI)(CI)F
```

### Linux/Mac

```bash
# 输入目录：只读
chmod -R 755 /path/to/phase2_structured

# 输出目录：读写
chmod -R 775 /path/to/phase3_final
```

## 💾 磁盘空间建议

| 数据规模 | Phase-2 输出 | Phase-3 输出 | 总需求 |
|---------|-------------|-------------|--------|
| 小型（< 100 MB） | 100 MB | 200 MB | 300 MB |
| 中型（100 MB - 1 GB） | 1 GB | 2 GB | 3 GB |
| 大型（> 1 GB） | 5 GB | 10 GB | 15 GB |

**建议：** 预留 2-3 倍的额外空间用于临时文件和日志。

## 🔧 目录维护

### 清理旧日志

```powershell
# 删除 30 天前的日志
Get-ChildItem "C:\VeritasReportNova\重新整合\output\phase3_final\phase3_log_*.txt" | 
  Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | 
  Remove-Item
```

### 归档旧输出

```powershell
# 将旧输出移动到归档目录
$archive = "C:\VeritasReportNova\archive\phase3_$(Get-Date -Format 'yyyyMM')"
New-Item -ItemType Directory -Force -Path $archive
Move-Item "C:\VeritasReportNova\重新整合\output\phase3_final\*" $archive
```

### 检查目录完整性

```python
# check_directories.py
from pathlib import Path

required_dirs = [
    'phase1_extracted',
    'phase2_structured',
    'phase2_structured/csv',
    'phase2_structured/tables',
    'phase3_final',
    'phase3_final/excel',
    'phase3_final/html',
    'phase3_final/json',
    'phase3_final/parquet'
]

root = Path(r"C:\VeritasReportNova\重新整合\output")

for dir_name in required_dirs:
    dir_path = root / dir_name
    if dir_path.exists():
        print(f"✓ {dir_name}")
    else:
        print(f"✗ {dir_name} (缺失)")
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  → 已创建")
```

---

**📌 重要提示：**

1. **不要手动修改** `phase2_structured` 目录中的文件（输入数据）
2. **定期备份** `phase3_final` 目录中的重要报告
3. **监控磁盘空间**，避免因空间不足导致输出失败
4. **检查日志文件**，及时发现和解决问题
