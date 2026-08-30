"""
批量PDF表格驗證器 - 最小改動版
直接處理整個檔案夾中的所有PDF文件
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
import glob
from pathlib import Path
import json
from datetime import datetime
import logging

# 導入原有的驗證系統
from pdf_table_validator import PDFTableValidator, DocumentReport

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_validation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BatchPDFValidator:
    """批量PDF表格驗證器"""
    
    def __init__(self, folder_path: str, output_folder: str = None):
        self.folder_path = Path(folder_path)
        self.output_folder = Path(output_folder) if output_folder else Path('./validation_results')
        self.output_folder.mkdir(exist_ok=True)
        
        # 使用簡化配置以求最小改動
        self.config = {
            'min_confidence_score': 0.5,      # 稍微降低要求
            'min_structure_score': 0.4,
            'min_semantic_score': 0.3,
            'consensus_threshold': 0.34,       # 只需1/3引擎一致即可
            'spot_check_ratio': 0.05,          # 減少抽檢以加快速度
            'visual_output_dir': str(self.output_folder / 'visual'),
        }
        
        self.validator = PDFTableValidator(self.config)
        self.results = []
        
    def process_all_pdfs(self) -> dict:
        """處理資料夾中所有PDF文件"""
        # 找出所有PDF文件
        pdf_files = list(self.folder_path.glob('*.pdf')) + list(self.folder_path.glob('*.PDF'))
        
        if not pdf_files:
            logger.warning(f"在 {self.folder_path} 中沒有找到PDF文件")
            return self._create_summary_report([])
        
        logger.info(f"找到 {len(pdf_files)} 個PDF文件，開始批量處理...")
        
        successful_reports = []
        failed_files = []
        
        for i, pdf_file in enumerate(pdf_files, 1):
            logger.info(f"[{i}/{len(pdf_files)}] 處理: {pdf_file.name}")
            
            try:
                # 分析單個PDF
                report = self.validator.analyze_document(str(pdf_file))
                successful_reports.append(report)
                
                # 保存個別報告
                self._save_individual_report(report, pdf_file.stem)
                
                logger.info(f"✓ {pdf_file.name}: 發現 {report.total_tables} 個表格 "
                          f"(驗證率: {report.validation_rate:.1%})")
                
            except Exception as e:
                logger.error(f"✗ {pdf_file.name} 處理失敗: {str(e)}")
                failed_files.append({
                    'file': str(pdf_file),
                    'error': str(e)
                })
                continue
        
        # 生成匯總報告
        summary = self._create_summary_report(successful_reports, failed_files)
        self._save_summary_report(summary)
        
        logger.info(f"\n批量處理完成！")
        logger.info(f"成功: {len(successful_reports)} 個文件")
        logger.info(f"失敗: {len(failed_files)} 個文件")
        logger.info(f"總表格數: {summary['total_tables']}")
        logger.info(f"報告保存在: {self.output_folder}")
        
        return summary
    
    def _save_individual_report(self, report: DocumentReport, filename: str):
        """保存個別PDF的報告"""
        # 簡化版報告，只保留關鍵信息
        simple_report = {
            'file_name': filename,
            'total_pages': report.total_pages,
            'total_tables': report.total_tables,
            'validation_rate': round(report.validation_rate, 3),
            'processing_time': round(report.processing_time, 2),
            'confidence_distribution': report.confidence_distribution,
            'table_details': []
        }
        
        # 提取表格詳細信息（簡化版）
        for page in report.pages:
            for table in page.validated_tables:
                simple_report['table_details'].append({
                    'page': table.page_num + 1,
                    'confidence': table.confidence.value,
                    'rows': table.row_count,
                    'cols': table.col_count,
                    'structure_score': round(table.structure_score, 2),
                    'engines': table.detected_by
                })
        
        # 保存JSON格式（比YAML更通用）
        output_path = self.output_folder / f"{filename}_report.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(simple_report, f, indent=2, ensure_ascii=False)
    
    def _create_summary_report(self, reports: list, failed_files: list = None) -> dict:
        """創建匯總報告"""
        if not reports:
            return {
                'summary': {
                    'total_files_processed': 0,
                    'successful_files': 0,
                    'failed_files': len(failed_files) if failed_files else 0,
                    'total_tables': 0,
                    'average_validation_rate': 0,
                    'total_processing_time': 0
                },
                'failed_files': failed_files or [],
                'created_at': datetime.now().isoformat()
            }
        
        total_tables = sum(r.total_tables for r in reports)
        total_processing_time = sum(r.processing_time for r in reports)
        avg_validation_rate = sum(r.validation_rate for r in reports) / len(reports)
        
        # 合併置信度分佈
        combined_confidence = {}
        for report in reports:
            for conf, count in report.confidence_distribution.items():
                combined_confidence[conf] = combined_confidence.get(conf, 0) + count
        
        # 檔案級別統計
        file_stats = []
        for report in reports:
            file_stats.append({
                'file': Path(report.document_path).name,
                'tables': report.total_tables,
                'validation_rate': round(report.validation_rate, 3),
                'processing_time': round(report.processing_time, 2)
            })
        
        return {
            'summary': {
                'total_files_processed': len(reports) + len(failed_files or []),
                'successful_files': len(reports),
                'failed_files': len(failed_files or []),
                'total_tables': total_tables,
                'average_validation_rate': round(avg_validation_rate, 3),
                'total_processing_time': round(total_processing_time, 2),
                'confidence_distribution': combined_confidence
            },
            'file_statistics': file_stats,
            'failed_files': failed_files or [],
            'created_at': datetime.now().isoformat()
        }
    
    def _save_summary_report(self, summary: dict):
        """保存匯總報告"""
        summary_path = self.output_folder / 'BATCH_SUMMARY.json'
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # 同時生成易讀的文字摘要
        self._save_text_summary(summary)
    
    def _save_text_summary(self, summary: dict):
        """生成易讀的文字摘要"""
        summary_text = f"""
=== PDF 表格批量驗證摘要 ===
處理時間: {summary['created_at']}

📊 總體統計:
• 處理文件數: {summary['summary']['total_files_processed']}
• 成功文件數: {summary['summary']['successful_files']} 
• 失敗文件數: {summary['summary']['failed_files']}
• 發現表格總數: {summary['summary']['total_tables']}
• 平均驗證率: {summary['summary']['average_validation_rate']:.1%}
• 總處理時間: {summary['summary']['total_processing_time']:.1f} 秒

🎯 置信度分佈:
"""
        
        for conf, count in summary['summary']['confidence_distribution'].items():
            if count > 0:
                summary_text += f"• {conf.upper()}: {count} 個表格\n"
        
        summary_text += "\n📋 各文件詳情:\n"
        for file_stat in summary['file_statistics']:
            summary_text += (f"• {file_stat['file']}: {file_stat['tables']} 個表格 "
                           f"(驗證率: {file_stat['validation_rate']:.1%})\n")
        
        if summary['failed_files']:
            summary_text += "\n❌ 失敗文件:\n"
            for failed in summary['failed_files']:
                file_name = Path(failed['file']).name
                summary_text += f"• {file_name}: {failed['error']}\n"
        
        # 保存文字摘要
        text_path = self.output_folder / 'BATCH_SUMMARY.txt'
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(summary_text)


def main():
    """主函數 - 最簡單的使用方式"""
    
    # === 這裡是你唯一需要修改的地方 ===
    PDF_FOLDER = r"C:\Users\tonyk\OneDrive\App\VeritasIntelligenceSystem\VeritasReportNova™\input"  # 改成你的PDF資料夾路徑
    OUTPUT_FOLDER = r"C:\Users\tonyk\OneDrive\App\VeritasIntelligenceSystem\VeritasReportNova™\output"  # 改成你想要的輸出路徑（可選）
    
    # 檢查資料夾是否存在
    if not os.path.exists(PDF_FOLDER):
        print(f"❌ 錯誤: 找不到資料夾 {PDF_FOLDER}")
        print("請修改 PDF_FOLDER 變數為正確的路徑")
        return
    
    print(f"🚀 開始批量處理 PDF 資料夾: {PDF_FOLDER}")
    
    # 創建批量驗證器並運行
    batch_validator = BatchPDFValidator(PDF_FOLDER, OUTPUT_FOLDER)
    
    try:
        summary = batch_validator.process_all_pdfs()
        
        print(f"\n✅ 批量處理完成!")
        print(f"📊 總共發現 {summary['summary']['total_tables']} 個表格")
        print(f"📁 結果保存在: {batch_validator.output_folder}")
        print(f"📄 查看 BATCH_SUMMARY.txt 獲取詳細摘要")
        
    except Exception as e:
        print(f"❌ 批量處理失敗: {str(e)}")
        logger.error(f"批量處理失敗: {str(e)}")


# === 快速使用範例 ===
if __name__ == "__main__":
    # 方法1: 直接運行主函數（最簡單）
    main()
    
    # 方法2: 自定義使用（進階）
    """
    folder_path = "your_pdf_folder"  # 你的PDF資料夾
    batch_validator = BatchPDFValidator(folder_path)
    summary = batch_validator.process_all_pdfs()
    print(f"處理完成，共發現 {summary['summary']['total_tables']} 個表格")
    """


# === 一鍵執行腳本 ===
"""
將以下代碼保存為 run_batch_validation.py，然後雙擊運行：

import os
import subprocess
import sys

# 設置你的PDF資料夾路徑
PDF_FOLDER = input("請輸入PDF資料夾路徑: ").strip('"')

if not os.path.exists(PDF_FOLDER):
    print("資料夾不存在！")
    input("按Enter鍵退出...")
    sys.exit()

print(f"開始處理: {PDF_FOLDER}")
print("處理中，請稍候...")

# 運行批量驗證
try:
    from batch_pdf_validator import BatchPDFValidator
    batch_validator = BatchPDFValidator(PDF_FOLDER)
    summary = batch_validator.process_all_pdfs()
    print(f"完成！共發現 {summary['summary']['total_tables']} 個表格")
    
except Exception as e:
    print(f"錯誤: {e}")

input("按Enter鍵退出...")
"""