"""
🎯 PDF 表格提取器 - 整合 FuzzyWuzzy 版本
支援更強大的字串比對功能

安裝需求:
pip install pdfplumber pandas openpyxl fuzzywuzzy python-Levenshtein

使用方法:
python pdf_extractor_fuzzy.py
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

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher  # Python 內建備用方案
import warnings

warnings.filterwarnings('ignore')

# ==================== 核心套件導入 ====================
import pdfplumber
import pandas as pd

# ==================== FuzzyWuzzy 導入（放在這裡！）====================
# 使用 try-except 確保即使沒安裝 fuzzywuzzy 也能運作
try:
    from fuzzywuzzy import fuzz
    from fuzzywuzzy import process
    FUZZYWUZZY_AVAILABLE = True
except ImportError as e:
    FUZZYWUZZY_AVAILABLE = False
except Exception as e:
    FUZZYWUZZY_AVAILABLE = False

# ==================== 日誌設定 ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 字串比對工具類別 ====================
class AdvancedStringMatcher:
    """進階字串比對器 - 自動選擇最佳方法"""
    
    def __init__(self):
        self.use_fuzzy = FUZZYWUZZY_AVAILABLE
        if self.use_fuzzy:
            logger.info("🚀 使用 FuzzyWuzzy 進行字串比對")
        else:
            logger.info("📊 使用 Python 內建 difflib 進行字串比對")
    
    def similarity(self, str1: str, str2: str) -> float:
        """
        計算兩個字串的相似度 (0-100)
        
        Args:
            str1: 第一個字串
            str2: 第二個字串
        
        Returns:
            相似度分數 (0-100)
        """
        if not str1 or not str2:
            return 0.0
        
        if self.use_fuzzy:
            # 使用 FuzzyWuzzy 的 ratio 方法
            return float(fuzz.ratio(str1, str2))
        else:
            # 使用 Python 內建的 SequenceMatcher
            return SequenceMatcher(None, str1.lower(), str2.lower()).ratio() * 100
    
    def partial_similarity(self, str1: str, str2: str) -> float:
        """
        部分匹配相似度（模糊搜尋）
        適合：「銷售額」vs「2024年銷售額總計」
        
        Args:
            str1: 較短的字串（搜尋詞）
            str2: 較長的字串（目標）
        
        Returns:
            部分匹配分數 (0-100)
        """
        if not str1 or not str2:
            return 0.0
        
        if self.use_fuzzy:
            # FuzzyWuzzy 的部分匹配
            return float(fuzz.partial_ratio(str1, str2))
        else:
            # 手動實現部分匹配
            str1, str2 = str1.lower(), str2.lower()
            if len(str1) > len(str2):
                str1, str2 = str2, str1
            
            max_ratio = 0.0
            for i in range(len(str2) - len(str1) + 1):
                substring = str2[i:i + len(str1)]
                ratio = SequenceMatcher(None, str1, substring).ratio()
                max_ratio = max(max_ratio, ratio)
            
            return max_ratio * 100
    
    def token_sort_similarity(self, str1: str, str2: str) -> float:
        """
        Token 排序相似度（忽略詞序）
        適合：「姓名 年齡」vs「年齡 姓名」
        
        Args:
            str1: 第一個字串
            str2: 第二個字串
        
        Returns:
            Token 排序後的相似度 (0-100)
        """
        if not str1 or not str2:
            return 0.0
        
        if self.use_fuzzy:
            return float(fuzz.token_sort_ratio(str1, str2))
        else:
            # 簡易實現：排序後比較
            tokens1 = sorted(str1.lower().split())
            tokens2 = sorted(str2.lower().split())
            sorted_str1 = ' '.join(tokens1)
            sorted_str2 = ' '.join(tokens2)
            return SequenceMatcher(None, sorted_str1, sorted_str2).ratio() * 100
    
    def best_match(self, query: str, choices: List[str], threshold: float = 60.0) -> Optional[Tuple[str, float]]:
        """
        從選項中找到最佳匹配
        
        Args:
            query: 查詢字串
            choices: 候選字串列表
            threshold: 最低相似度閾值
        
        Returns:
            (最佳匹配, 分數) 或 None
        """
        if not query or not choices:
            return None
        
        if self.use_fuzzy:
            # 使用 FuzzyWuzzy 的 process.extractOne
            result = process.extractOne(query, choices)
            if result and result[1] >= threshold:
                return (result[0], float(result[1]))
            return None
        else:
            # 手動實現
            best_match = None
            best_score = 0.0
            
            for choice in choices:
                score = self.similarity(query, choice)
                if score > best_score:
                    best_score = score
                    best_match = choice
            
            if best_score >= threshold:
                return (best_match, best_score)
            return None
    
    def extract_top_matches(self, query: str, choices: List[str], limit: int = 5) -> List[Tuple[str, float]]:
        """
        提取前 N 個最佳匹配
        
        Args:
            query: 查詢字串
            choices: 候選字串列表
            limit: 返回結果數量
        
        Returns:
            [(匹配字串, 分數), ...] 列表
        """
        if not query or not choices:
            return []
        
        if self.use_fuzzy:
            # 使用 FuzzyWuzzy 的 process.extract
            results = process.extract(query, choices, limit=limit)
            return [(match[0], float(match[1])) for match in results]
        else:
            # 手動實現
            scores = [(choice, self.similarity(query, choice)) for choice in choices]
            scores.sort(key=lambda x: x[1], reverse=True)
            return scores[:limit]


# ==================== PDF 表格提取器 ====================
class EnhancedPDFExtractor:
    """增強版 PDF 表格提取器 - 使用進階字串比對"""
    
    def __init__(self):
        self.matcher = AdvancedStringMatcher()
        self.tables = []
    
    def extract_tables_from_pdf(self, pdf_path: str) -> List[Dict]:
        """從 PDF 提取所有表格"""
        logger.info(f"📖 開始讀取: {pdf_path}")
        
        all_tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                logger.info(f"📄 總共 {len(pdf.pages)} 頁")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    logger.info(f"🔍 正在處理第 {page_num} 頁...")
                    
                    # 提取表格
                    tables = page.extract_tables()
                    
                    for table_num, table in enumerate(tables, 1):
                        if table and len(table) > 1:
                            logger.info(f"  ✅ 找到表格 #{table_num}")
                            
                            df = pd.DataFrame(table[1:], columns=table[0])
                            df = self._repair_table(df, page_num, table_num)
                            features = self._extract_features(df)
                            
                            all_tables.append({
                                'page': page_num,
                                'table_num': table_num,
                                'data': df,
                                'features': features,
                                'rows': len(df),
                                'cols': len(df.columns)
                            })
                    
                    # 備用方法
                    if not tables:
                        logger.info(f"  ⚠️ 未找到表格，嘗試文字提取...")
                        text_table = self._extract_text_as_table(page)
                        if text_table is not None:
                            features = self._extract_features(text_table)
                            all_tables.append({
                                'page': page_num,
                                'table_num': 1,
                                'data': text_table,
                                'features': features,
                                'rows': len(text_table),
                                'cols': len(text_table.columns)
                            })
        
        except Exception as e:
            logger.error(f"❌ 錯誤: {e}")
            import traceback
            traceback.print_exc()
            return []
        
        logger.info(f"✨ 完成！總共提取 {len(all_tables)} 個表格")
        return all_tables
    
    def _extract_features(self, df: pd.DataFrame) -> Dict:
        """提取表格特徵"""
        return {
            'num_cols': len(df.columns),
            'num_rows': len(df),
            'column_names': list(df.columns),
            'has_numeric': any(df.dtypes.apply(lambda x: pd.api.types.is_numeric_dtype(x))),
            'density': float(df.notna().sum().sum() / (len(df) * len(df.columns))) if len(df) > 0 else 0.0
        }
    
    def _repair_table(self, df: pd.DataFrame, page_num: int, table_num: int) -> pd.DataFrame:
        """修復表格（包含智能欄位匹配）"""
        repairs = []
        
        # 基本清理
        before_rows = len(df)
        df = df.dropna(how='all')
        if len(df) < before_rows:
            repairs.append(f"移除 {before_rows - len(df)} 個空白行")
        
        before_cols = len(df.columns)
        df = df.loc[:, df.notna().any(axis=0)]
        if len(df.columns) < before_cols:
            repairs.append(f"移除 {before_cols - len(df.columns)} 個空白列")
        
        # 清理欄位名稱
        new_columns = []
        for i, col in enumerate(df.columns):
            if pd.isna(col) or str(col).strip() == '':
                new_columns.append(f'欄位_{i+1}')
            else:
                clean_name = str(col).strip().replace('\n', ' ').replace('\r', '')
                new_columns.append(clean_name)
        
        df.columns = new_columns
        repairs.append("清理欄位名稱")
        
        # 使用進階字串匹配標準化欄位名稱
        df = self._standardize_column_names(df)
        
        # 向下填充
        filled = 0
        for col in df.columns:
            before = df[col].isna().sum()
            df[col] = df[col].fillna(method='ffill')
            filled += before - df[col].isna().sum()
        
        if filled > 0:
            repairs.append(f"填補 {filled} 個空白儲存格")
        
        # 智能轉換數字
        for col in df.columns:
            df[col] = self._smart_convert_numeric(df[col])
        
        if repairs:
            logger.info(f"    🔧 修復: {', '.join(repairs)}")
        
        return df
    
    def _standardize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        使用模糊匹配標準化欄位名稱
        例如：「姓 名」、「姓名」、「Name」都會被識別為同一欄位
        """
        # 常見欄位名稱對照表
        standard_columns = {
            '姓名': ['姓名', '名字', 'name', '人名', '姓 名'],
            '年齡': ['年齡', '歲數', 'age', '年纪', '年 齡'],
            '性別': ['性別', '性别', 'gender', '性 別'],
            '電話': ['電話', '电话', 'phone', 'tel', '手機', '電 話'],
            '地址': ['地址', 'address', '住址', '地 址'],
            '金額': ['金額', '金额', 'amount', '價格', '价格', '金 額'],
            '日期': ['日期', 'date', '時間', '时间', '日 期'],
            '編號': ['編號', '编号', 'id', 'number', '序號', '編 號'],
        }
        
        new_columns = []
        for col in df.columns:
            # 嘗試找到最佳匹配的標準欄位名
            best_standard = None
            best_score = 0.0
            
            for standard_name, variations in standard_columns.items():
                # 檢查是否與任何變體匹配
                for variation in variations:
                    score = self.matcher.similarity(col, variation)
                    if score > best_score and score >= 70:  # 70% 相似度閾值
                        best_score = score
                        best_standard = standard_name
            
            if best_standard:
                new_columns.append(best_standard)
                logger.info(f"    🔄 欄位標準化: '{col}' → '{best_standard}' (相似度: {best_score:.1f}%)")
            else:
                new_columns.append(col)
        
        df.columns = new_columns
        return df
    
    def _smart_convert_numeric(self, series: pd.Series) -> pd.Series:
        """智能轉換數字欄位"""
        if series.dtype != 'object':
            return series
        
        try:
            cleaned = series.astype(str).str.replace(',', '').str.replace('$', '').str.replace('NT$', '').str.replace('%', '')
            numeric = pd.to_numeric(cleaned, errors='coerce')
            
            if numeric.notna().sum() > len(series) * 0.5:
                return numeric
        except:
            pass
        
        return series
    
    def _extract_text_as_table(self, page) -> Optional[pd.DataFrame]:
        """從純文字提取表格"""
        try:
            words = page.extract_words(keep_blank_chars=True)
            if not words:
                return None
            
            rows = {}
            for word in words:
                y = round(word['top'], 1)
                if y not in rows:
                    rows[y] = []
                rows[y].append(word)
            
            sorted_rows = []
            for y in sorted(rows.keys()):
                row_words = sorted(rows[y], key=lambda w: w['x0'])
                row_text = ' '.join(w['text'] for w in row_words)
                sorted_rows.append(row_text.split())
            
            if len(sorted_rows) > 1 and sorted_rows:
                max_cols = max(len(row) for row in sorted_rows)
                padded_rows = [row + [''] * (max_cols - len(row)) for row in sorted_rows]
                df = pd.DataFrame(padded_rows[1:], columns=padded_rows[0])
                return df
        
        except Exception as e:
            logger.warning(f"    文字提取失敗: {e}")
        
        return None
    
    def save_tables(self, tables: List[Dict], output_dir: str = "output"):
        """保存所有表格並進行智能分群"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 使用進階字串匹配進行智能分群
        groups = self._smart_group_tables(tables)
        
        summary = {
            'total_tables': len(tables),
            'groups': {},
            'matcher_type': 'FuzzyWuzzy' if self.matcher.use_fuzzy else 'difflib'
        }
        
        for group_id, group_tables in groups.items():
            group_dir = output_path / f"group_{group_id}"
            group_dir.mkdir(exist_ok=True)
            
            group_features = self._analyze_group(group_tables)
            
            group_info = {
                'count': len(group_tables),
                'description': group_features['description'],
                'files': []
            }
            
            for table in group_tables:
                filename = f"page{table['page']:02d}_table{table['table_num']}.csv"
                filepath = group_dir / filename
                
                table['data'].to_csv(filepath, index=False, encoding='utf-8-sig')
                
                excel_filename = filename.replace('.csv', '.xlsx')
                excel_filepath = group_dir / excel_filename
                table['data'].to_excel(excel_filepath, index=False, engine='openpyxl')
                
                group_info['files'].append({
                    'filename': filename,
                    'page': table['page'],
                    'rows': table['rows'],
                    'cols': table['cols'],
                    'columns': table['features']['column_names'][:5]
                })
                
                logger.info(f"💾 已保存: {filepath}")
            
            summary['groups'][f'group_{group_id}'] = group_info
        
        summary_file = output_path / 'summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        self._generate_html_report(summary, output_path)
        
        logger.info(f"\n📊 摘要已保存: {summary_file}")
        return summary
    
    def _smart_group_tables(self, tables: List[Dict]) -> Dict[int, List[Dict]]:
        """
        智能分群：使用進階字串匹配
        相比基礎版本，這個版本能更準確地識別相似的表格
        """
        if not tables:
            return {}
        
        groups = {}
        group_id = 0
        
        for table in tables:
            best_group = None
            best_score = 0.0
            
            for gid, group_tables in groups.items():
                # 使用增強的相似度計算
                score = self._calculate_table_similarity_enhanced(table, group_tables[0])
                if score > best_score:
                    best_score = score
                    best_group = gid
            
            # 使用更寬鬆的閾值（因為模糊匹配更準確）
            if best_score > 65.0:  # 降低到 65%
                groups[best_group].append(table)
            else:
                groups[group_id] = [table]
                group_id += 1
        
        logger.info(f"🧠 智能分群完成: {len(groups)} 個群組")
        for gid, gtables in groups.items():
            logger.info(f"  群組 {gid}: {len(gtables)} 個表格")
        
        return groups
    
    def _calculate_table_similarity_enhanced(self, table1: Dict, table2: Dict) -> float:
        """
        增強版表格相似度計算 - 使用模糊匹配
        """
        feat1 = table1['features']
        feat2 = table2['features']
        
        # 1. 欄位數相似度 (30%)
        col_diff = abs(feat1['num_cols'] - feat2['num_cols'])
        col_similarity = max(0, 100 - (col_diff * 20))
        
        # 2. 欄位名稱模糊匹配相似度 (50%) - 這裡使用 FuzzyWuzzy！
        col_names_1 = feat1['column_names']
        col_names_2 = feat2['column_names']
        
        if col_names_1 and col_names_2:
            match_count = 0
            total_count = max(len(col_names_1), len(col_names_2))
            
            for name1 in col_names_1:
                # 使用模糊匹配找到最佳對應
                match = self.matcher.best_match(name1, col_names_2, threshold=60)
                if match:
                    match_count += 1
            
            name_similarity = (match_count / total_count) * 100 if total_count > 0 else 0
        else:
            name_similarity = 0
        
        # 3. 數據類型相似度 (20%)
        type_similarity = 100.0 if feat1['has_numeric'] == feat2['has_numeric'] else 0.0
        
        # 加權平均
        total_similarity = (
            col_similarity * 0.3 +
            name_similarity * 0.5 +
            type_similarity * 0.2
        )
        
        return total_similarity
    
    def _analyze_group(self, group_tables: List[Dict]) -> Dict:
        """分析群組特徵"""
        if not group_tables:
            return {'description': '空群組'}
        
        representative = group_tables[0]['features']
        
        description = f"{representative['num_cols']} 欄表格"
        if representative['has_numeric']:
            description += "（含數字資料）"
        
        return {
            'description': description,
            'num_cols': representative['num_cols'],
            'sample_columns': representative['column_names'][:5]
        }
    
    def _generate_html_report(self, summary: Dict, output_path: Path):
        """生成 HTML 報告"""
        matcher_badge = "🚀 FuzzyWuzzy" if summary['matcher_type'] == 'FuzzyWuzzy' else "📊 difflib"
        
        html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF 表格提取報告</title>
    <style>
        body {{
            font-family: 'Microsoft JhengHei', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .badge {{
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 5px 15px;
            border-radius: 20px;
            margin-top: 10px;
        }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .group {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .group-header {{
            background: #667eea;
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            margin-bottom: 15px;
        }}
        .file-list {{
            list-style: none;
            padding: 0;
        }}
        .file-item {{
            padding: 10px;
            border-left: 3px solid #667eea;
            margin-bottom: 10px;
            background: #f8f9fa;
        }}
        .stat {{
            display: inline-block;
            background: #e7e9fc;
            padding: 5px 15px;
            border-radius: 20px;
            margin: 5px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 PDF 表格提取報告</h1>
        <div class="badge">字串匹配引擎: {matcher_badge}</div>
    </div>
    
    <div class="summary">
        <h2>📈 總覽</h2>
        <div class="stat">📄 總表格數: {summary['total_tables']}</div>
        <div class="stat">📁 群組數: {len(summary['groups'])}</div>
    </div>
"""
        
        for group_name, group_info in summary['groups'].items():
            html_content += f"""
    <div class="group">
        <div class="group-header">
            <h3>{group_name} - {group_info['description']}</h3>
            <span>{group_info['count']} 個表格</span>
        </div>
        <ul class="file-list">
"""
            for file_info in group_info['files']:
                html_content += f"""
            <li class="file-item">
                <strong>{file_info['filename']}</strong><br>
                頁面: {file_info['page']} | 大小: {file_info['rows']} 行 × {file_info['cols']} 列<br>
                欄位: {', '.join(file_info['columns'][:3])}...
            </li>
"""
            html_content += """
        </ul>
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        html_file = output_path / 'report.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"📄 HTML 報告已生成: {html_file}")


def main():
    """主程序"""
    print("=" * 60)
    print("🎯 增強版 PDF 表格提取器")
    if FUZZYWUZZY_AVAILABLE:
        print("✅ 使用 FuzzyWuzzy 進行智能字串匹配")
    else:
        print("📊 使用 Python 內建方法（建議安裝 fuzzywuzzy）")
    print("=" * 60)
    print()
    
    pdf_path = input("📂 請輸入 PDF 檔案路徑: ").strip().strip('"')
    
    if not os.path.exists(pdf_path):
        print(f"❌ 找不到檔案: {pdf_path}")
        input("\n按 Enter 結束...")
        return
    
    output_dir = input("📁 輸出目錄 (直接按 Enter 使用 'output'): ").strip() or "output"
    
    print("\n" + "=" * 60)
    print("🚀 開始處理...")
    print("=" * 60 + "\n")
    
    extractor = EnhancedPDFExtractor()
    tables = extractor.extract_tables_from_pdf(pdf_path)
    
    if not tables:
        print("\n❌ 沒有找到任何表格")
        input("\n按 Enter 結束...")
        return
    
    summary = extractor.save_tables(tables, output_dir)
    
    print("\n" + "=" * 60)
    print("✨ 處理完成！")
    print("=" * 60)
    print(f"📊 總共提取: {summary['total_tables']} 個表格")
    print(f"📁 分成: {len(summary['groups'])} 個群組")
    print(f"💾 結果保存在: {output_dir}")
    print(f"📄 查看報告: {output_dir}\\report.html")
    print(f"🔧 匹配引擎: {summary['matcher_type']}")
    print("=" * 60)
    
    for group_name, group_info in summary['groups'].items():
        print(f"\n📦 {group_name}: {group_info['count']} 個表格 - {group_info['description']}")
        for file_info in group_info['files'][:2]:
            print(f"  - {file_info['filename']} ({file_info['rows']}行 x {file_info['cols']}列)")
        if group_info['count'] > 2:
            print(f"  ... 還有 {group_info['count'] - 2} 個檔案")
    
    print("\n" + "=" * 60)
    input("按 Enter 結束...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 使用者中斷")
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        input("\n按 Enter 結束...")
