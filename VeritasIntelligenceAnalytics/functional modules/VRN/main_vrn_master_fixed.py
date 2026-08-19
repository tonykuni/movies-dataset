#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║  VeritasReportNova™ 2025 Type-Safe Edition                                            ║
║  修正：完全類型安全 · 錯誤處理強化 · 座標轉換修正 · Worker 獨立環境                      ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import subprocess
import importlib.util
import time
import uuid
import hashlib
import shutil
import traceback
import re
import multiprocessing
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

# ==============================================================================
# SECTION 0: Auto-Deployer with Auto-Restart
# ==============================================================================
class AutoDeployer:
    REQUIRED = {
        "rich": "rich", "polars": "polars", "duckdb": "duckdb", "pyarrow": "pyarrow",
        "cv2": "opencv-python-headless", "skimage": "scikit-image", "pdf2image": "pdf2image",
        "rapidocr_onnxruntime": "rapidocr-onnxruntime",
        "rapid_layout": "rapid-layout", "rapid_table": "rapid-table",
        "img2table": "img2table", "pdfplumber": "pdfplumber", "spacy": "spacy"
    }
    MIRROR = "https://pypi.tuna.tsinghua.edu.cn/simple"

    @classmethod
    def check_and_install(cls):
        print("🔍 VRN 系統自檢啟動 (System Self-Check)...")
        missing = []
        for module, package in cls.REQUIRED.items():
            if not importlib.util.find_spec(module):
                missing.append(package)
        
        if missing:
            print(f"📦 發現缺失套件，正在補完: {', '.join(missing)}")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing + ["-i", cls.MIRROR])
                print("✅ 安裝完成，正在重啟程式以載入新套件...")
                print("-" * 60)
                os.execv(sys.executable, [sys.executable] + sys.argv)
            except Exception as e:
                print(f"❌ 部署失敗: {e}")
                sys.exit(1)
        else:
            print("✅ 環境完整性驗證通過 (Environment Integrity Verified)")

# 執行檢查
AutoDeployer.check_and_install()

# ==============================================================================
# Imports (Safe Now)
# ==============================================================================
import cv2
import numpy as np
import polars as pl
import duckdb
from pdf2image import convert_from_path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.panel import Panel
from rich import box

# Global Config
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DIRS = {k: BASE_DIR / v for k, v in {'input': "pdf_input", 'output': "pdf_output", 'temp': "temp_batches", 'db': "database_export", 'log': "logs"}.items()}
for d in DIRS.values(): d.mkdir(parents=True, exist_ok=True)

console = Console()
CPU_CORES = max(1, multiprocessing.cpu_count() - 2)

# ==============================================================================
# SECTION 1: ID Model (Type-Safe)
# ==============================================================================
class IDGenerator:
    @staticmethod
    def doc_id(filename: str, size: int) -> str:
        try:
            hash_input = f"{filename}_{size}".encode('utf-8')
            h = hashlib.md5(hash_input).hexdigest()[:6].upper()
            ts = datetime.now().strftime("%Y%m%d")
            return f"DOC_{ts}_{h}"
        except: return f"DOC_{uuid.uuid4().hex[:8]}"
    
    @staticmethod
    def page_id(doc_id: str, pg_num: int) -> str:
        return f"{doc_id}_P{int(pg_num):03d}"
        
    @staticmethod
    def item_id(page_id: str, type_prefix: str, idx: int) -> str:
        # ★ 強制確保所有輸入都是正確類型
        page_id = str(page_id)
        type_prefix = str(type_prefix)
        idx = int(idx)
        fmt = "{:02d}" if type_prefix == "T" else "{:04d}"
        return f"{page_id}_{type_prefix}{fmt.format(idx)}"

class FileFingerprint:
    @staticmethod
    def calculate(path: Path) -> dict:
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            while chunk := f.read(8192): h.update(chunk)
        return {'sha256': h.hexdigest()}

# ==============================================================================
# SECTION 2: Database (DuckDB)
# ==============================================================================
class VRNDatabase:
    def __init__(self, db_path: Path):
        self.conn = duckdb.connect(str(db_path))
        self.conn.execute("CREATE TABLE IF NOT EXISTS documents (doc_id VARCHAR PRIMARY KEY, filename VARCHAR, file_size BIGINT, hash VARCHAR, processed_at TIMESTAMP, pages INTEGER, status VARCHAR)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS master_data (unique_id VARCHAR PRIMARY KEY, doc_id VARCHAR, filename VARCHAR, page INTEGER, item_id VARCHAR, type VARCHAR, content VARCHAR, confidence DOUBLE, p1_tables INTEGER, timestamp TIMESTAMP)")
        
    def upsert_doc(self, meta: dict):
        self.conn.execute("INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT (doc_id) DO UPDATE SET processed_at = excluded.processed_at", 
                          (meta['doc_id'], meta['filename'], meta['size'], meta['hash'], datetime.now(), meta['pages'], meta['status']))

    def bulk_insert(self, df: pl.DataFrame):
        if df.is_empty(): return
        self.conn.register('temp', df)
        self.conn.execute("INSERT OR IGNORE INTO master_data SELECT concat(doc_id, '_', item_id), doc_id, filename, page, item_id, type, content, confidence, p1_tables, timestamp FROM temp")
        self.conn.unregister('temp')

# ==============================================================================
# SECTION 3: Data Assembler (Type-Safe)
# ==============================================================================
class DataAssembler:
    def __init__(self): 
        self.stops = ('.', '。', '!', '！')
    
    def assemble(self, blocks, doc_id, page):
        if not blocks: return []
        
        # ★ 強制類型轉換 - 修正排序錯誤
        try:
            blocks.sort(key=lambda b: (
                int(float(b['box'][1]) / 15),  # y 座標分組
                int(float(b['box'][0]))        # x 座標排序
            ))
        except (ValueError, TypeError, KeyError):
            # 如果排序失敗，保持原序
            pass
        
        results, buf_txt, buf_conf, idx = [], "", [], 1
        
        for b in blocks:
            txt = str(b.get('text', '')).strip()
            if not txt: continue
            
            if b.get('type') == 'Header':
                if buf_txt: 
                    results.append(self._pack(buf_txt, buf_conf, doc_id, page, idx, "Sentence"))
                    idx += 1
                    buf_txt, buf_conf = "", []
                results.append(self._pack(txt, [b.get('conf', 0.0)], doc_id, page, idx, "Header"))
                idx += 1
            else:
                buf_txt += txt
                buf_conf.append(float(b.get('conf', 0.0)))
                if buf_txt.endswith(self.stops):
                    results.append(self._pack(buf_txt, buf_conf, doc_id, page, idx, "Sentence"))
                    idx += 1
                    buf_txt, buf_conf = "", []
        
        if buf_txt: 
            results.append(self._pack(buf_txt, buf_conf, doc_id, page, idx, "Sentence"))
        
        return results

    def _pack(self, txt, confs, doc_id, page, idx, type_):
        txt = re.sub(r'(?<=[\u4e00-\u9fa5])\s+(?=[\u4e00-\u9fa5])', '', txt).strip()
        return {
            'doc_id': str(doc_id), 
            'page': int(page),
            'item_id': IDGenerator.item_id(IDGenerator.page_id(doc_id, page), "S", int(idx)),
            'type': str(type_), 
            'content': str(txt), 
            'confidence': float(sum(confs) / len(confs)) if confs else 0.0,
            'timestamp': datetime.now()
        }

# ==============================================================================
# SECTION 4: Worker Process (Type-Safe + Error Handling)
# ==============================================================================
def worker_task(pdf_path: Path):
    try:
        # Worker 內部獨立載入 (Multiprocessing Safe)
        from rapidocr_onnxruntime import RapidOCR
        ocr = RapidOCR()
        
        try: from rapid_layout import RapidLayout; r_layout = RapidLayout()
        except: r_layout = None
        
        try: from rapid_table import RapidTable; r_table = RapidTable()
        except: r_table = None
        
        assembler = DataAssembler()
        
        f_size = pdf_path.stat().st_size
        doc_id = IDGenerator.doc_id(pdf_path.name, f_size)
        
        try: images = convert_from_path(str(pdf_path), dpi=150)
        except Exception as e: 
            return {'status': 'error', 'msg': f'PDF Convert Fail: {e}', 'file': pdf_path.name}
        
        batch, p1_count = [], 0
        
        for i, img in enumerate(images):
            pg = int(i + 1)  # ★ 強制轉 int
            page_id = IDGenerator.page_id(doc_id, pg)
            
            # Enhance
            img_np = np.array(img)
            img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            enhanced = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

            layout_res, _ = r_layout(enhanced_bgr) if r_layout else ([], 0)
            ocr_blocks, t_idx = [], 1
            
            if layout_res:
                for region in layout_res:
                    try:
                        bbox, conf, label = region[0], region[1], region[2]
                        
                        # ★ 座標轉型 - 修正：先轉 float 再轉 int，防止字串錯誤
                        x1 = int(float(bbox[0]))
                        y1 = int(float(bbox[1]))
                        x2 = int(float(bbox[2]))
                        y2 = int(float(bbox[3]))
                        
                        # 邊界檢查
                        h, w = enhanced_bgr.shape[:2]
                        x1, y1 = max(0, x1), max(0, y1)
                        x2, y2 = min(w, x2), min(h, y2)
                        
                        if x2 <= x1 or y2 <= y1: continue  # 無效區域
                        
                        roi = enhanced_bgr[y1:y2, x1:x2]
                        if roi.size == 0: continue
                        
                        if str(label) == 'table':
                            if pg == 1: p1_count += 1
                            t_html = "(Table Structure Detected)"
                            
                            if r_table:
                                try: 
                                    t_html, _ = r_table(roi)
                                except: 
                                    pass
                            
                            batch.append({
                                'doc_id': str(doc_id), 
                                'filename': str(pdf_path.name), 
                                'page': int(pg),
                                'item_id': IDGenerator.item_id(page_id, "T", int(t_idx)),
                                'type': 'Table', 
                                'content': str(t_html), 
                                'confidence': float(conf),
                                'p1_tables': 0, 
                                'timestamp': datetime.now()
                            })
                            t_idx = int(t_idx) + 1  # ★ 確保是 int
                        else:
                            r, _ = ocr(roi)
                            if r: 
                                for l in r:
                                    try:
                                        # ★ 座標計算 - 先轉 float 再加法，最後轉 int
                                        box_x = int(float(l[0][0][0]) + float(x1))
                                        box_y = int(float(l[0][0][1]) + float(y1))
                                        text = str(l[1])
                                        conf_val = float(l[2])
                                        
                                        ocr_blocks.append({
                                            'box': [box_x, box_y], 
                                            'text': text, 
                                            'conf': conf_val, 
                                            'type': str(label).capitalize()
                                        })
                                    except (ValueError, IndexError, TypeError) as e:
                                        continue  # 跳過無效 OCR 結果
                    except (ValueError, IndexError, TypeError) as e:
                        continue  # 跳過無效 region
            else:
                # 無版面分析，直接 OCR
                r, _ = ocr(enhanced_bgr)
                if r: 
                    for l in r:
                        try:
                            box_x = int(float(l[0][0][0]))
                            box_y = int(float(l[0][0][1]))
                            text = str(l[1])
                            conf_val = float(l[2])
                            
                            ocr_blocks.append({
                                'box': [box_x, box_y], 
                                'text': text, 
                                'conf': conf_val, 
                                'type': 'Text'
                            })
                        except (ValueError, IndexError, TypeError):
                            continue

            sents = assembler.assemble(ocr_blocks, doc_id, pg)
            for s in sents: 
                s['filename'] = str(pdf_path.name)
                s['p1_tables'] = 0
                batch.append(s)

        # 設定 p1_tables
        for d in batch: 
            d['p1_tables'] = int(p1_count)
        
        if batch:
            df = pl.DataFrame(batch)
            out_path = DIRS['temp'] / f"{doc_id}.parquet"
            df.write_parquet(out_path)
            return {
                'status': 'success', 
                'file': pdf_path.name, 
                'meta': {
                    'doc_id': doc_id, 
                    'filename': pdf_path.name, 
                    'size': f_size, 
                    'hash': '', 
                    'pages': len(images), 
                    'status': 'ok'
                }
            }
            
        return {'status': 'empty', 'file': pdf_path.name, 'msg': 'No text detected'}

    except Exception as e:
        return {
            'status': 'crash', 
            'file': pdf_path.name, 
            'msg': f"{type(e).__name__}: {str(e)}"
        }

# ==============================================================================
# SECTION 5: Master Engine
# ==============================================================================
class MasterEngine:
    def run(self):
        # 1. Init & Check
        if DIRS['temp'].exists(): 
            shutil.rmtree(DIRS['temp'])
            DIRS['temp'].mkdir()
        
        pdfs = list(DIRS['input'].glob("*.pdf"))
        if not pdfs: 
            console.print("[red]❌ pdf_input 資料夾為空[/]")
            return
        
        db = VRNDatabase(DIRS['db'] / "vrn_master.duckdb")
        
        # 顯示模組狀態
        t = Table(title="🛠️ VRN 2025 Toolchain Status", box=box.SIMPLE)
        t.add_column("Module")
        t.add_column("Status")
        
        for m in ['rapid_layout', 'rapid_table', 'rapidocr_onnxruntime', 'duckdb', 'polars']:
            loaded = importlib.util.find_spec(m) is not None
            status = "[green]Ready[/]" if loaded else "[red]Missing[/]"
            t.add_row(m, status)
        
        console.print(t)
        
        console.print(f"\n[bold cyan]🚀 VRN 自律型系統啟動 | {CPU_CORES} 核心 | {len(pdfs)} 檔案[/]\n")
        
        # 2. Batch Processing
        with Progress(
            SpinnerColumn(), 
            TextColumn("[bold blue]{task.description}"), 
            BarColumn(), 
            TextColumn("{task.percentage:>3.0f}%"), 
            TimeElapsedColumn()
        ) as p:
            task = p.add_task("Processing...", total=len(pdfs))
            
            with ProcessPoolExecutor(max_workers=CPU_CORES) as ex:
                futures = {ex.submit(worker_task, f): f for f in pdfs}
                
                for f in as_completed(futures):
                    res = f.result()
                    p.advance(task)
                    
                    if res['status'] == 'success': 
                        db.upsert_doc(res['meta'])
                    else: 
                        console.print(f"[red]⚠️ {res['file']}: {res.get('msg', 'Unknown error')}[/]")

        # 3. Finalize
        self._finalize(db)

    def _finalize(self, db):
        console.print("\n[yellow]⚡ 生成戰情矩陣與報告...[/]")
        
        try:
            parquet_files = list(DIRS['temp'].glob("*.parquet"))
            if not parquet_files: 
                console.print("[red]❌ 無數據產出[/]")
                return
            
            df = pl.scan_parquet(str(DIRS['temp'] / "*.parquet")).collect()
            db.bulk_insert(df)
            
            # Export
            xlsx_path = DIRS['db'] / "VRN_Final_Report.xlsx"
            df.write_excel(xlsx_path)
            
            # Matrix Display
            t = Table(title="📊 VRN Final Matrix", box=box.ROUNDED)
            t.add_column("Filename", style="white", no_wrap=False)
            t.add_column("Page", justify="right", style="magenta")
            t.add_column("ID", style="cyan", no_wrap=False)
            t.add_column("P1 Tables", justify="center", style="yellow")
            t.add_column("Status", style="green")
            
            sample = df.sort(["doc_id", "page", "item_id"]).group_by("doc_id").head(2)
            
            for row in sample.iter_rows(named=True):
                filename_short = str(row['filename'])[:20] + "..." if len(str(row['filename'])) > 20 else str(row['filename'])
                status = "✅ OK" if float(row['confidence']) > 0.9 else "⚠️ Check"
                
                t.add_row(
                    filename_short, 
                    str(row['page']), 
                    str(row['item_id'])[:25], 
                    str(row['p1_tables']), 
                    status
                )
            
            console.print(t)
            console.print(f"\n[green]✅ 完成！報告已儲存至 {xlsx_path}[/]")
            console.print(f"[green]   資料庫位置: {DIRS['db'] / 'vrn_master.duckdb'}[/]\n")
            
        except Exception as e: 
            console.print(f"[red]❌ 最終化失敗: {e}[/]")
            traceback.print_exc()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    MasterEngine().run()
