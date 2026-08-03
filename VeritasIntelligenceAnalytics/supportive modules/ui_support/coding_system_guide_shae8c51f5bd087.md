# 🔢 VeritasReportNova 編號編碼系統指南

## 📋 目錄

1. [系統概述](#系統概述)
2. [編碼格式規範](#編碼格式規範)
3. [使用方式](#使用方式)
4. [編碼範例](#編碼範例)
5. [資料庫結構](#資料庫結構)
6. [查詢與統計](#查詢與統計)
7. [最佳實踐](#最佳實踐)

---

## 📖 系統概述

**通用編號編碼系統** 為 VeritasReportNova 的所有處理對象提供唯一識別碼，確保：

✅ **唯一性** - 每個對象都有唯一編碼  
✅ **可追溯性** - 可追蹤處理歷史  
✅ **層次性** - 反映對象間的層級關係  
✅ **可讀性** - 人類可讀的編碼格式  
✅ **持久性** - SQLite 資料庫永久儲存

### 支援的編碼類型

| 類型 | 前綴 | 用途 |
|------|------|------|
| 文件編碼 | DOC | 識別每個 PDF 文件 |
| 頁面編碼 | PAG | 識別文件中的每一頁 |
| 區塊編碼 | BLK | 識別頁面中的每個區塊 |
| 表格編碼 | TBL | 識別抽取的表格 |
| OCR編碼 | OCR | 識別 OCR 處理結果 |
| 任務編碼 | TSK | 識別處理任務 |
| 批次編碼 | BAT | 識別批次處理 |

---

## 🎯 編碼格式規範

### 1. 文件編碼 (Document Code)

**格式**: `DOC-YYYYMMDD-NNNN`

```
DOC-20251010-0001
│   │        └─ 序號 (4位數，從0001開始)
│   └─ 日期 (年月日)
└─ 前綴
```

**範例**:
- `DOC-20251010-0001` - 2025年10月10日的第1個文件
- `DOC-20251010-0125` - 2025年10月10日的第125個文件

**用途**:
- 識別每個輸入的 PDF 文件
- 追蹤文件處理狀態
- 關聯文件的所有頁面

---

### 2. 頁面編碼 (Page Code)

**格式**: `PAG-{DOC_ID}-PPPP`

```
PAG-DOC20251010-0001-0025
│   │                └─ 頁碼 (4位數)
│   └─ 文件ID (移除前綴和破折號)
└─ 前綴
```

**範例**:
- `PAG-DOC20251010-0001-0001` - 文件 DOC-20251010-0001 的第1頁
- `PAG-DOC20251010-0001-0025` - 文件 DOC-20251010-0001 的第25頁

**用途**:
- 識別文件中的每一頁
- 關聯頁面上的所有區塊
- 追蹤頁面處理進度

---

### 3. 區塊編碼 (Block Code)

**格式**: `BLK-{PAG_ID}-{TYPE}-BBBB`

```
BLK-PAG-DOC20251010-0001-0025-TEXT-0012
│   │                         │    └─ 序號 (4位數)
│   │                         └─ 區塊類型 (4字母)
│   └─ 頁面ID
└─ 前綴
```

**區塊類型代碼**:

| 類型 | 代碼 | 說明 |
|------|------|------|
| 文字 | TEXT | 一般文字區塊 |
| 標題 | TITL | 標題區塊 |
| 頁首 | HEAD | 頁首區塊 |
| 頁尾 | FOOT | 頁尾區塊 |
| 表格 | TABL | 表格區塊 |
| 圖像 | IMAG | 圖像區塊 |
| 未知 | UNKN | 未識別類型 |

**範例**:
- `BLK-PAG-DOC20251010-0001-0001-TITL-0001` - 第1頁的第1個標題區塊
- `BLK-PAG-DOC20251010-0001-0001-TEXT-0012` - 第1頁的第12個文字區塊

**用途**:
- 識別頁面中的每個區塊
- 區分不同類型的內容
- 追蹤區塊處理狀態

---

### 4. 表格編碼 (Table Code)

**格式**: `TBL-{PAG_ID}-TTTT`

```
TBL-PAG-DOC20251010-0001-0025-0003
│   │                         └─ 表格序號 (4位數)
│   └─ 頁面ID
└─ 前綴
```

**範例**:
- `TBL-PAG-DOC20251010-0001-0001-0001` - 第1頁的第1個表格
- `TBL-PAG-DOC20251010-0001-0025-0003` - 第25頁的第3個表格

**用途**:
- 識別抽取的表格
- 記錄抽取引擎和置信度
- 比較不同引擎的結果

---

### 5. OCR編碼 (OCR Code)

**格式**: `OCR-{PAG_ID}-OOOO`

```
OCR-PAG-DOC20251010-0001-0025-0001
│   │                         └─ OCR序號 (4位數)
│   └─ 頁面ID
└─ 前綴
```

**範例**:
- `OCR-PAG-DOC20251010-0001-0001-0001` - 第1頁的第1次OCR結果
- `OCR-PAG-DOC20251010-0001-0025-0002` - 第25頁的第2次OCR結果

**用途**:
- 識別 OCR 處理結果
- 記錄 OCR 引擎和置信度
- 多引擎結果比較

---

### 6. 任務編碼 (Task Code)

**格式**: `TSK-YYYYMMDD-HHMM-TTTT`

```
TSK-20251010-1430-0001
│   │        │    └─ 任務序號 (4位數)
│   │        └─ 時間 (時分)
│   └─ 日期 (年月日)
└─ 前綴
```

**範例**:
- `TSK-20251010-1430-0001` - 2025年10月10日 14:30 的第1個任務
- `TSK-20251010-1430-0025` - 2025年10月10日 14:30 的第25個任務

**任務類型**:
- `scan` - 掃描任務
- `extract` - 抽取任務
- `ocr` - OCR任務
- `classify` - 分類任務

**用途**:
- 追蹤任務執行狀態
- 記錄任務開始和完成時間
- 任務效能分析

---

### 7. 批次編碼 (Batch Code)

**格式**: `BAT-YYYYMMDD-HHMM`

```
BAT-20251010-1430
│   │        └─ 時間 (時分)
│   └─ 日期 (年月日)
└─ 前綴
```

**範例**:
- `BAT-20251010-1430` - 2025年10月10日 14:30 的批次處理
- `BAT-20251011-0900` - 2025年10月11日 09:00 的批次處理

**用途**:
- 識別批次處理
- 統計批次處理文件數量
- 批次效能分析

---

## 🚀 使用方式

### 基礎使用

```python
from universal_coding_system import UniversalCodingSystem

# 1. 初始化系統
coding = UniversalCodingSystem("coding_system.db")

# 2. 生成文件編碼
doc_code = coding.generate_document_code(
    filename="annual_report.pdf",
    file_path="C:/input/annual_report.pdf",
    metadata={"size_mb": 15.3, "pages": 120}
)
print(f"文件編碼: {doc_code.code}")
# 輸出: DOC-20251010-0001

# 3. 生成頁面編碼
page_code = coding.generate_page_code(
    document_code=doc_code.code,
    page_number=25,
    metadata={"width": 595, "height": 842}
)
print(f"頁面編碼: {page_code.code}")
# 輸出: PAG-DOC20251010-0001-0025

# 4. 生成區塊編碼
block_code = coding.generate_block_code(
    page_code=page_code.code,
    block_type='text',
    bbox=(100, 100, 500, 200),
    content="這是文字區塊內容",
    metadata={"confidence": 0.95}
)
print(f"區塊編碼: {block_code.code}")
# 輸出: BLK-PAG-DOC20251010-0001-0025-TEXT-0001
```

### 整合到 Part 1

```python
from universal_coding_system import UniversalCodingSystem
from part1_ultimate_turbo_integrated import TurboPDFProcessor, UltimateTurboAccelerator

# 初始化
accel = UltimateTurboAccelerator()
processor = TurboPDFProcessor(accel)
coding = UniversalCodingSystem()

# 批次處理
batch_code = coding.generate_batch_code(document_count=0)

for pdf_path in pdf_files:
    # 生成文件編碼
    doc_code = coding.generate_document_code(
        filename=os.path.basename(pdf_path),
        file_path=pdf_path,
        metadata={"batch": batch_code.code}
    )
    
    # 處理 PDF
    info = processor.extract_pdf_info(pdf_path)
    
    # 為每一頁生成編碼
    for page_num in range(info['頁數']):
        page_code = coding.generate_page_code(
            document_code=doc_code.code,
            page_number=page_num + 1
        )

# 更新批次計數
batch_code.document_count = len(pdf_files)
```

### 整合到 Part 2

```python
from universal_coding_system import UniversalCodingSystem
from part2_ultimate_turbo_table_ocr import TurboTableExtractor, TurboOCRProcessor

# 初始化
coding = UniversalCodingSystem()
table_extractor = TurboTableExtractor(accel)
ocr_processor = TurboOCRProcessor(accel)

# 表格抽取
tables = table_extractor.extract_tables_single_page(pdf_path, page_num)

for engine_name, engine_tables in tables.items():
    for table_data in engine_tables:
        # 生成表格編碼
        table_code = coding.generate_table_code(
            page_code=page_code.code,
            engine=engine_name,
            confidence=0.92,
            table_data=str(table_data),
            metadata={"rows": len(table_data), "cols": len(table_data.columns)}
        )
        print(f"表格編碼: {table_code.code}")

# OCR 處理
ocr_results = ocr_processor.ocr_image(image)

for engine_name, result in ocr_results.items():
    # 生成 OCR 編碼
    ocr_code = coding.generate_ocr_code(
        page_code=page_code.code,
        engine=engine_name,
        confidence=result['confidence'],
        text=result['text'],
        metadata={"language": "chi_tra"}
    )
    print(f"OCR編碼: {ocr_code.code}")
```

### 整合到 Part 3

```python
from universal_coding_system import UniversalCodingSystem
from part3_ultimate_turbo_block_system import TurboBlockExtractor

# 初始化
coding = UniversalCodingSystem()
block_extractor = TurboBlockExtractor(accel)

# 區塊抽取
blocks = block_extractor.extract_blocks_from_page(pdf_path, page_num)

for block in blocks:
    # 生成區塊編碼
    block_code = coding.generate_block_code(
        page_code=page_code.code,
        block_type=block.block_type,
        bbox=block.bbox,
        content=block.content,
        metadata=block.metadata
    )
    
    # 更新區塊對象
    block.id = block_code.code
```

---

## 📊 編碼範例

### 完整的文件處理流程

```
批次處理: BAT-20251010-1430
└── 文件1: DOC-20251010-0001 (annual_report.pdf)
    ├── 頁面1: PAG-DOC20251010-0001-0001
    │   ├── 區塊1: BLK-PAG-DOC20251010-0001-0001-TITL-0001 (標題)
    │   ├── 區塊2: BLK-PAG-DOC20251010-0001-0001-TEXT-0002 (文字)
    │   ├── 表格1: TBL-PAG-DOC20251010-0001-0001-0001 (camelot)
    │   └── OCR1:  OCR-PAG-DOC20251010-0001-0001-0001 (tesseract)
    │
    ├── 頁面2: PAG-DOC20251010-0001-0002
    │   ├── 區塊1: BLK-PAG-DOC20251010-0001-0002-TEXT-0001
    │   └── 區塊2: BLK-PAG-DOC20251010-0001-0002-IMAG-0002 (圖像)
    │
    └── 頁面25: PAG-DOC20251010-0001-0025
        ├── 區塊1: BLK-PAG-DOC20251010-0001-0025-FOOT-0001 (頁尾)
        └── 表格1: TBL-PAG-DOC20251010-0001-0025-0001

└── 文件2: DOC-20251010-0002 (financial_data.pdf)
    └── ...
```

### 任務追蹤範例

```
任務1: TSK-20251010-1430-0001 (scan)
├── 狀態: completed
├── 開始: 2025-10-10 14:30:00
├── 完成: 2025-10-10 14:30:05
└── 處理: DOC-20251010-0001 到 DOC-20251010-0100

任務2: TSK-20251010-1430-0002 (extract_tables)
├── 狀態: running
├── 開始: 2025-10-10 14:30:05
└── 處理: DOC-20251010-0001 的所有頁面

任務3: TSK-20251010-1430-0003 (ocr)
├── 狀態: pending
└── 等待: 任務2完成
```

---

## 💾 資料庫結構

### SQLite 資料庫表格

#### 1. documents 表

| 欄位 | 類型 | 說明 |
|------|------|------|
| code | TEXT | 文件編碼 (主鍵) |
| original_filename | TEXT | 原始檔名 |
| file_path | TEXT | 檔案路徑 |
| file_hash | TEXT | MD5 hash (唯一) |
| created_at | TEXT | 建立時間 |
| metadata | TEXT | JSON 元數據 |

#### 2. pages 表

| 欄位 | 類型 | 說明 |
|------|------|------|
| code | TEXT | 頁面編碼 (主鍵) |
| document_code | TEXT | 文件編碼 (外鍵) |
| page_number | INTEGER | 頁碼 |
| page_hash | TEXT | 頁面 hash |
| metadata | TEXT | JSON 元數據 |

#### 3. blocks 表

| 欄位 | 類型 | 說明 |
|------|------|------|
| code | TEXT | 區塊編碼 (主鍵) |
| page_code | TEXT | 頁面編碼 (外鍵) |
| block_type | TEXT | 區塊類型 |
| sequence | INTEGER | 序號 |
| bbox | TEXT | 邊界框 JSON |
| content_hash | TEXT | 內容 hash |
| metadata | TEXT | JSON 元數據 |

#### 4. tables 表

| 欄位 | 類型 | 說明 |
|------|------|------|
| code | TEXT | 表格編碼 (主鍵) |
| page_code | TEXT | 頁面編碼 (外鍵) |
| sequence | INTEGER | 序號 |
| engine | TEXT | 抽取引擎 |
| confidence | REAL | 置信度 |
| table_hash | TEXT | 表格 hash |
| metadata | TEXT | JSON 元數據 |

#### 5. ocr_results 表

| 欄位 | 類型 | 說明 |
|------|------|------|
| code | TEXT | OCR編碼 (主鍵) |
| page_code | TEXT | 頁面編碼 (外鍵) |
| sequence | INTEGER | 序號 |
| engine | TEXT | OCR引擎 |
| confidence | REAL | 置信度 |
| text_hash | TEXT | 文字 hash |
| metadata | TEXT | JSON 元數據 |

#### 6. tasks 表

| 欄位 | 類型 | 說明 |
|------|------|------|
| code | TEXT | 任務編碼 (主鍵) |
| task_type | TEXT | 任務類型 |
| status | TEXT | 狀態 |
| created_at | TEXT | 建立時間 |
| completed_at | TEXT | 完成時間 |
| metadata | TEXT | JSON 元數據 |

#### 7. batches 表

| 欄位 | 類型 | 說明 |
|------|------|------|
| code | TEXT | 批次編碼 (主鍵) |
| document_count | INTEGER | 文件數量 |
| created_at | TEXT | 建立時間 |
| completed_at | TEXT | 完成時間 |
| metadata | TEXT | JSON 元數據 |

#### 8. counters 表

| 欄位 | 類型 | 說明 |
|------|------|------|
| category | TEXT | 類別 (主鍵) |
| date | TEXT | 日期 |
| count | INTEGER | 計數 |

---

## 🔍 查詢與統計

### 查詢範例

```python
# 1. 根據編碼查詢文件
doc = coding.get_document_by_code("DOC-20251010-0001")
print(f"檔名: {doc.original_filename}")
print(f"路徑: {doc.file_path}")

# 2. 查詢文件的所有頁面
pages = coding.get_pages_by_document("DOC-20251010-0001")
print(f"總頁數: {len(pages)}")

# 3. 查詢頁面的所有區塊
blocks = coding.get_blocks_by_page("PAG-DOC20251010-0001-0001")
print(f"區塊數: {len(blocks)}")

# 4. 顯示統計資訊
coding.show_statistics()
```

### SQL 查詢範例

```sql
-- 1. 查詢今天處理的所有文件
SELECT * FROM documents 
WHERE created_at LIKE '2025-10-10%'
ORDER BY code;

-- 2. 查詢特定文件的所有表格
SELECT t.* FROM tables t
JOIN pages p ON t.page_code = p.code
WHERE p.document_code = 'DOC-20251010-0001';

-- 3. 統計每個引擎抽取的表格數
SELECT engine, COUNT(*) as count
FROM tables
GROUP BY engine
ORDER BY count DESC;

-- 4. 查詢高置信度的 OCR 結果
SELECT * FROM ocr_results
WHERE confidence > 0.90
ORDER BY confidence DESC;

-- 5. 統計每種區塊類型的數量
SELECT block_type, COUNT(*) as count
FROM blocks
GROUP BY block_type
ORDER BY count DESC;
```

---

## 💡 最佳實踐

### 1. 始終使用編碼系統

```python
# ✓ 好: 使用編碼系統
doc_code = coding.generate_document_code(filename, path)
page_code = coding.generate_page_code(doc_code.code, page_num)

# ✗ 差: 自己生成ID
doc_id = f"doc_{datetime.now().timestamp()}"
```

### 2. 在元數據中儲存額外資訊

```python
# 文件元數據
metadata = {
    "size_mb": 15.3,
    "pages": 120,
    "quality_score": 95,
    "source": "scanner",
    "tags": ["financial", "annual_report"]
}

doc_code = coding.generate_document_code(
    filename, path, metadata=metadata
)
```

### 3. 追蹤處理狀態

```python
# 創建任務
task = coding.generate_task_code(
    task_type="extract_tables",
    metadata={"priority": "high", "documents": [doc_code.code]}
)

# 處理過程...

# 更新任務狀態 (需要自行實現update方法)
task.status = "completed"
task.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
```

### 4. 使用批次編碼組織處理

```python
# 開始批次處理
batch = coding.generate_batch_code(document_count=len(pdf_files))

for pdf_path in pdf_files:
    doc_code = coding.generate_document_code(
        filename=os.path.basename(pdf_path),
        file_path=pdf_path,
        metadata={"batch": batch.code}  # 關聯批次
    )
    # 處理文件...

# 完成批次
batch.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
```

### 5. 定期備份資料庫

```bash
# 備份 SQLite 資料庫
cp coding_system.db coding_system_backup_20251010.db

# 或使用 Python
import shutil
shutil.copy('coding_system.db', 'backup/coding_system_20251010.db')
```

---

## 🎯 總結

**通用編號編碼系統**提供:

✅ **7 種編碼類型** - 涵蓋所有處理對象  
✅ **SQLite 持久化** - 所有編碼永久儲存  
✅ **自動序號管理** - 無需手動維護計數器  
✅ **完整追溯性** - 可追蹤任何對象的處理歷史  
✅ **靈活的元數據** - JSON 格式儲存額外資訊  
✅ **查詢與統計** - 豐富的查詢和統計功能

現在所有的文件、頁面、區塊、表格、OCR結果都有了**唯一且有意義的編碼**！🎉