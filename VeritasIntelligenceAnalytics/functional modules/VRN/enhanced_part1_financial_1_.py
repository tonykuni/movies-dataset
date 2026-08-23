#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced PDF Table Extraction System - Part 1: Financial Document Processing
Multi-format input support, document enhancement, and specialized financial data extraction
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
import sys
import subprocess
import platform
import logging
import json
import time
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
import re

# Image processing and OCR
try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    import pytesseract
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

# Document conversion
try:
    from docx2pdf import convert as docx_to_pdf
    DOCX2PDF_AVAILABLE = True
except ImportError:
    DOCX2PDF_AVAILABLE = False

try:
    import mammoth
    MAMMOTH_AVAILABLE = True
except ImportError:
    MAMMOTH_AVAILABLE = False

# Rich progress and display
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.panel import Panel
    from rich.table import Table
    from rich.logging import RichHandler
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

@dataclass
class DocumentMetadata:
    """Document metadata and analysis results"""
    file_path: str
    file_type: str
    page_count: int
    table_count: int
    categories: List[str] = field(default_factory=list)
    financial_indicators: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0
    processing_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'file_path': self.file_path,
            'file_type': self.file_type,
            'page_count': self.page_count,
            'table_count': self.table_count,
            'categories': self.categories,
            'financial_indicators': self.financial_indicators,
            'quality_score': self.quality_score,
            'processing_time': self.processing_time
        }

@dataclass
class FinancialDataRegion:
    """Financial data extraction region definition"""
    region_name: str
    coordinates: Tuple[float, float, float, float]  # (x1, y1, x2, y2) as percentages
    data_types: List[str]
    extraction_patterns: List[str]
    priority: int = 1

class DocumentConverter:
    """Multi-format document converter with quality enhancement"""
    
    def __init__(self, temp_dir: str = None):
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir()) / "pdf_converter"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.console = Console() if RICH_AVAILABLE else None
        
        # Financial document regions for targeted extraction
        self.financial_regions = {
            'price_target_top_left': FinancialDataRegion(
                region_name="price_target_top_left",
                coordinates=(0.0, 0.0, 0.3, 0.2),  # Top-left 30% x 20%
                data_types=["price_target", "current_price", "rating"],
                extraction_patterns=[
                    r"Price\s+Target[:\s]+\$?(\d+\.?\d*)",
                    r"Target[:\s]+\$?(\d+\.?\d*)",
                    r"Current[:\s]+\$?(\d+\.?\d*)",
                    r"Rating[:\s]+(\w+)",
                    r"(BUY|SELL|HOLD|STRONG BUY|STRONG SELL)"
                ],
                priority=1
            ),
            'price_target_top_right': FinancialDataRegion(
                region_name="price_target_top_right",
                coordinates=(0.7, 0.0, 1.0, 0.2),  # Top-right 30% x 20%
                data_types=["price_target", "recommendation"],
                extraction_patterns=[
                    r"Price\s+Target[:\s]+\$?(\d+\.?\d*)",
                    r"12-Month\s+Target[:\s]+\$?(\d+\.?\d*)",
                    r"Recommendation[:\s]+(\w+)"
                ],
                priority=1
            ),
            'financial_summary': FinancialDataRegion(
                region_name="financial_summary",
                coordinates=(0.0, 0.2, 1.0, 0.5),  # Main content area
                data_types=["revenue", "earnings", "ratios"],
                extraction_patterns=[
                    r"Revenue[:\s]+\$?(\d+\.?\d*[BMK]?)",
                    r"EPS[:\s]+\$?(\d+\.?\d*)",
                    r"P/E[:\s]+(\d+\.?\d*)",
                    r"Market\s+Cap[:\s]+\$?(\d+\.?\d*[BMK]?)"
                ],
                priority=2
            )
        }
    
    def display_message(self, message: str, style: str = "info"):
        """Display formatted message"""
        if self.console:
            if style == "success":
                self.console.print(f"✅ {message}", style="green")
            elif style == "error":
                self.console.print(f"❌ {message}", style="red")
            elif style == "warning":
                self.console.print(f"⚠️ {message}", style="yellow")
            else:
                self.console.print(f"ℹ️ {message}", style="blue")
        else:
            print(f"[{style.upper()}] {message}")
    
    def convert_to_pdf(self, input_path: str, enhance_quality: bool = True) -> Optional[str]:
        """Convert various formats to PDF with quality enhancement"""
        input_path = Path(input_path)
        
        if not input_path.exists():
            self.display_message(f"Input file not found: {input_path}", "error")
            return None
        
        file_ext = input_path.suffix.lower()
        output_path = self.temp_dir / f"{input_path.stem}_converted.pdf"
        
        try:
            if file_ext == '.pdf':
                # Already PDF, optionally enhance
                if enhance_quality:
                    return self.enhance_pdf_quality(str(input_path))
                else:
                    return str(input_path)
            
            elif file_ext in ['.docx', '.doc']:
                return self._convert_word_to_pdf(str(input_path), str(output_path))
            
            elif file_ext in ['.txt']:
                return self._convert_text_to_pdf(str(input_path), str(output_path))
            
            elif file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                return self._convert_image_to_pdf(str(input_path), str(output_path), enhance_quality)
            
            else:
                self.display_message(f"Unsupported file format: {file_ext}", "error")
                return None
                
        except Exception as e:
            self.display_message(f"Conversion failed: {e}", "error")
            return None
    
    def _convert_word_to_pdf(self, input_path: str, output_path: str) -> Optional[str]:
        """Convert Word document to PDF"""
        
        if DOCX2PDF_AVAILABLE:
            try:
                convert(input_path, output_path)
                self.display_message(f"Word document converted: {Path(output_path).name}", "success")
                return output_path
            except Exception as e:
                self.display_message(f"Word conversion failed: {e}", "error")
        
        # Fallback using LibreOffice if available
        try:
            subprocess.run([
                'libreoffice', '--headless', '--convert-to', 'pdf',
                '--outdir', str(Path(output_path).parent),
                input_path
            ], check=True, capture_output=True)
            
            self.display_message(f"Word document converted using LibreOffice: {Path(output_path).name}", "success")
            return output_path
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.display_message("LibreOffice not available for Word conversion", "warning")
            return None
    
    def _convert_text_to_pdf(self, input_path: str, output_path: str) -> Optional[str]:
        """Convert text file to PDF"""
        
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph
            from reportlab.lib.styles import getSampleStyleSheet
            
            with open(input_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()
            
            # Split text into paragraphs
            paragraphs = []
            for line in text_content.split('\n'):
                if line.strip():
                    paragraphs.append(Paragraph(line, styles['Normal']))
            
            doc.build(paragraphs)
            
            self.display_message(f"Text file converted: {Path(output_path).name}", "success")
            return output_path
            
        except ImportError:
            self.display_message("ReportLab not available for text conversion", "warning")
            return None
        except Exception as e:
            self.display_message(f"Text conversion failed: {e}", "error")
            return None
    
    def _convert_image_to_pdf(self, input_path: str, output_path: str, enhance_quality: bool = True) -> Optional[str]:
        """Convert image to PDF with quality enhancement"""
        
        if not PIL_AVAILABLE:
            self.display_message("PIL not available for image conversion", "error")
            return None
        
        try:
            # Load and enhance image
            image = Image.open(input_path)
            
            if enhance_quality:
                image = self._enhance_image_quality(image)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save as PDF
            image.save(output_path, "PDF", resolution=300.0, quality=95)
            
            self.display_message(f"Image converted: {Path(output_path).name}", "success")
            return output_path
            
        except Exception as e:
            self.display_message(f"Image conversion failed: {e}", "error")
            return None
    
    def _enhance_image_quality(self, image: Image.Image) -> Image.Image:
        """Enhance image quality for better OCR and table detection"""
        
        # Convert to grayscale for processing
        if image.mode != 'L':
            gray_image = image.convert('L')
        else:
            gray_image = image.copy()
        
        # Resize if too small (minimum 1200px width for good OCR)
        width, height = gray_image.size
        if width < 1200:
            scale_factor = 1200 / width
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            gray_image = gray_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(gray_image)
        enhanced_image = enhancer.enhance(1.2)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(enhanced_image)
        enhanced_image = enhancer.enhance(1.1)
        
        # Apply slight denoising
        enhanced_image = enhanced_image.filter(ImageFilter.MedianFilter(size=3))
        
        # Convert back to RGB
        if image.mode == 'RGB':
            enhanced_rgb = Image.new('RGB', enhanced_image.size)
            enhanced_rgb.paste(enhanced_image)
            return enhanced_rgb
        
        return enhanced_image
    
    def enhance_pdf_quality(self, pdf_path: str) -> Optional[str]:
        """Enhance existing PDF quality for better table extraction"""
        
        try:
            import fitz  # PyMuPDF
            
            input_doc = fitz.open(pdf_path)
            output_path = self.temp_dir / f"{Path(pdf_path).stem}_enhanced.pdf"
            output_doc = fitz.open()
            
            for page_num in range(len(input_doc)):
                page = input_doc[page_num]
                
                # Render page at high resolution
                mat = fitz.Matrix(2.0, 2.0)  # 2x scaling for better quality
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image for enhancement
                img_data = pix.tobytes("ppm")
                img = Image.open(io.BytesIO(img_data))
                
                # Enhance image
                enhanced_img = self._enhance_image_quality(img)
                
                # Convert back to PDF page
                img_pdf_bytes = io.BytesIO()
                enhanced_img.save(img_pdf_bytes, format='PDF')
                img_pdf_bytes.seek(0)
                
                img_doc = fitz.open("pdf", img_pdf_bytes.read())
                output_doc.insert_pdf(img_doc)
                img_doc.close()
            
            output_doc.save(output_path)
            output_doc.close()
            input_doc.close()
            
            self.display_message(f"PDF quality enhanced: {output_path.name}", "success")
            return str(output_path)
            
        except ImportError:
            self.display_message("PyMuPDF not available for PDF enhancement", "warning")
            return pdf_path
        except Exception as e:
            self.display_message(f"PDF enhancement failed: {e}", "error")
            return pdf_path

class FinancialDocumentAnalyzer:
    """Specialized analyzer for financial documents"""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        
        # Financial document categories
        self.document_categories = {
            'analyst_report': [
                'price target', 'recommendation', 'rating', 'analyst', 'coverage',
                'initiate', 'maintain', 'upgrade', 'downgrade'
            ],
            'earnings_report': [
                'earnings', 'quarterly', 'revenue', 'eps', 'guidance',
                'q1', 'q2', 'q3', 'q4', 'fiscal year'
            ],
            'financial_statement': [
                'balance sheet', 'income statement', 'cash flow',
                'assets', 'liabilities', 'equity', 'gaap'
            ],
            'presentation': [
                'investor presentation', 'conference call', 'slide',
                'management', 'outlook', 'strategy'
            ],
            'sec_filing': [
                '10-k', '10-q', '8-k', 'form', 'sec', 'filing',
                'edgar', 'proxy', 'schedule'
            ]
        }
        
        # Stock symbols pattern
        self.stock_pattern = re.compile(r'\b[A-Z]{1,5}\b(?:\.[A-Z]{1,2})?')
        
        # Financial metrics patterns
        self.financial_patterns = {
            'price_target': [
                r'Price\s+Target[:\s]+\$?(\d+\.?\d*)',
                r'Target[:\s]+\$?(\d+\.?\d*)',
                r'12[- ]?Month\s+Target[:\s]+\$?(\d+\.?\d*)'
            ],
            'current_price': [
                r'Current\s+Price[:\s]+\$?(\d+\.?\d*)',
                r'Last\s+Price[:\s]+\$?(\d+\.?\d*)',
                r'Close[:\s]+\$?(\d+\.?\d*)'
            ],
            'rating': [
                r'Rating[:\s]+(\w+(?:\s+\w+)?)',
                r'Recommendation[:\s]+(\w+(?:\s+\w+)?)',
                r'\b(BUY|SELL|HOLD|STRONG\s+BUY|STRONG\s+SELL|OUTPERFORM|UNDERPERFORM|NEUTRAL)\b'
            ],
            'market_cap': [
                r'Market\s+Cap[:\s]+\$?(\d+\.?\d*[BMK]?)',
                r'Mkt\s+Cap[:\s]+\$?(\d+\.?\d*[BMK]?)'
            ],
            'pe_ratio': [
                r'P/E[:\s]+(\d+\.?\d*)',
                r'Price[/\s]+Earnings[:\s]+(\d+\.?\d*)'
            ]
        }
    
    def analyze_document(self, pdf_path: str) -> DocumentMetadata:
        """Analyze document to extract metadata and categorize content"""
        
        start_time = time.time()
        
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            table_count = 0
            categories = []
            financial_indicators = {}
            
            # Extract text from all pages
            full_text = ""
            for page_num in range(page_count):
                page = doc[page_num]
                full_text += page.get_text()
                
                # Count tables on each page
                tables = page.find_tables()
                table_count += len(tables)
            
            doc.close()
            
            # Determine document categories
            categories = self._categorize_document(full_text)
            
            # Extract financial indicators
            financial_indicators = self._extract_financial_indicators(full_text)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(full_text, table_count, page_count)
            
            processing_time = time.time() - start_time
            
            metadata = DocumentMetadata(
                file_path=pdf_path,
                file_type="PDF",
                page_count=page_count,
                table_count=table_count,
                categories=categories,
                financial_indicators=financial_indicators,
                quality_score=quality_score,
                processing_time=processing_time
            )
            
            self.display_message(f"Document analyzed: {page_count} pages, {table_count} tables", "success")
            
            return metadata
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.display_message(f"Document analysis failed: {e}", "error")
            
            return DocumentMetadata(
                file_path=pdf_path,
                file_type="PDF",
                page_count=0,
                table_count=0,
                processing_time=processing_time
            )
    
    def _categorize_document(self, text: str) -> List[str]:
        """Categorize document based on content"""
        
        text_lower = text.lower()
        found_categories = []
        
        for category, keywords in self.document_categories.items():
            keyword_count = sum(1 for keyword in keywords if keyword in text_lower)
            if keyword_count >= 2:  # Require at least 2 matching keywords
                found_categories.append(category)
        
        # Default category if none found
        if not found_categories:
            found_categories.append('general_financial')
        
        return found_categories
    
    def _extract_financial_indicators(self, text: str) -> Dict[str, Any]:
        """Extract key financial indicators from text"""
        
        indicators = {}
        
        # Extract stock symbols
        stock_symbols = list(set(self.stock_pattern.findall(text)))
        if stock_symbols:
            indicators['stock_symbols'] = stock_symbols
        
        # Extract financial metrics
        for metric_name, patterns in self.financial_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    indicators[metric_name] = matches[0] if len(matches) == 1 else matches
                    break  # Use first successful pattern
        
        return indicators
    
    def _calculate_quality_score(self, text: str, table_count: int, page_count: int) -> float:
        """Calculate document quality score for extraction accuracy"""
        
        score = 0.0
        
        # Text length score (0-0.3)
        text_length = len(text.strip())
        if text_length > 5000:
            score += 0.3
        elif text_length > 1000:
            score += 0.2
        elif text_length > 100:
            score += 0.1
        
        # Table density score (0-0.3)
        if page_count > 0:
            table_density = table_count / page_count
            if table_density >= 2:
                score += 0.3
            elif table_density >= 1:
                score += 0.2
            elif table_density >= 0.5:
                score += 0.1
        
        # Financial content score (0-0.4)
        financial_keywords = [
            'price', 'target', 'rating', 'revenue', 'earnings',
            'market cap', 'p/e', 'eps', 'buy', 'sell', 'hold'
        ]
        text_lower = text.lower()
        financial_score = sum(1 for keyword in financial_keywords if keyword in text_lower)
        score += min(0.4, financial_score * 0.05)
        
        return min(1.0, score)
    
    def display_message(self, message: str, style: str = "info"):
        """Display formatted message"""
        if self.console:
            if style == "success":
                self.console.print(f"✅ {message}", style="green")
            elif style == "error":
                self.console.print(f"❌ {message}", style="red")
            elif style == "warning":
                self.console.print(f"⚠️ {message}", style="yellow")
            else:
                self.console.print(f"ℹ️ {message}", style="blue")
        else:
            print(f"[{style.upper()}] {message}")

class RegionalDataExtractor:
    """Extract data from specific regions of financial documents"""
    
    def __init__(self, financial_regions: Dict[str, FinancialDataRegion]):
        self.financial_regions = financial_regions
        self.console = Console() if RICH_AVAILABLE else None
    
    def extract_regional_data(self, pdf_path: str) -> Dict[str, Dict[str, Any]]:
        """Extract data from predefined regions in the document"""
        
        regional_data = {}
        
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            
            for page_num in range(min(2, len(doc))):  # Focus on first 2 pages
                page = doc[page_num]
                page_rect = page.rect
                
                for region_name, region in self.financial_regions.items():
                    # Calculate actual coordinates
                    x1 = page_rect.x0 + (region.coordinates[0] * page_rect.width)
                    y1 = page_rect.y0 + (region.coordinates[1] * page_rect.height)
                    x2 = page_rect.x0 + (region.coordinates[2] * page_rect.width)
                    y2 = page_rect.y0 + (region.coordinates[3] * page_rect.height)
                    
                    # Extract text from region
                    region_rect = fitz.Rect(x1, y1, x2, y2)
                    region_text = page.get_text(clip=region_rect)
                    
                    if region_text.strip():
                        # Extract patterns from region text
                        extracted_data = self._extract_patterns_from_text(
                            region_text, region.extraction_patterns, region.data_types
                        )
                        
                        if extracted_data:
                            if region_name not in regional_data:
                                regional_data[region_name] = {}
                            
                            regional_data[region_name][f'page_{page_num}'] = {
                                'text': region_text,
                                'extracted_data': extracted_data,
                                'coordinates': region.coordinates
                            }
            
            doc.close()
            
        except Exception as e:
            self.display_message(f"Regional extraction failed: {e}", "error")
        
        return regional_data
    
    def _extract_patterns_from_text(self, text: str, patterns: List[str], 
                                   data_types: List[str]) -> Dict[str, Any]:
        """Extract specific patterns from text"""
        
        extracted = {}
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Determine data type based on pattern
                if 'price' in pattern.lower() or '$' in pattern:
                    extracted['price_data'] = matches
                elif 'rating' in pattern.lower() or any(rating in pattern.upper() 
                                                       for rating in ['BUY', 'SELL', 'HOLD']):
                    extracted['rating_data'] = matches
                else:
                    extracted['other_data'] = matches
        
        return extracted
    
    def display_message(self, message: str, style: str = "info"):
        """Display formatted message"""
        if self.console:
            if style == "success":
                self.console.print(f"✅ {message}", style="green")
            elif style == "error":
                self.console.print(f"❌ {message}", style="red")
            elif style == "warning":
                self.console.print(f"⚠️ {message}", style="yellow")
            else:
                self.console.print(f"ℹ️ {message}", style="blue")
        else:
            print(f"[{style.upper()}] {message}")

class EnhancedPDFSystemDeployer:
    """Enhanced system deployer with financial document support"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path.cwd() / "enhanced_pdf_system"
        self.console = Console() if RICH_AVAILABLE else None
        
        # Initialize components
        self.converter = DocumentConverter(str(self.base_dir / "temp"))
        self.analyzer = FinancialDocumentAnalyzer()
        self.regional_extractor = RegionalDataExtractor(self.converter.financial_regions)
        
        # Enhanced configuration
        self.config = {
            'financial_mode': True,
            'auto_enhance_quality': True,
            'multi_format_support': True,
            'regional_extraction': True,
            'acceleration_mandatory': True,  # 加速工具不可減少
            'financial_validation': True,
            'export_stock_info': True
        }
        
        self.setup_logging()
    
    def setup_logging(self):
        """Setup enhanced logging for financial processing"""
        log_dir = self.base_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging with financial-specific handlers
        financial_handler = logging.FileHandler(log_dir / "financial_processing.log")
        conversion_handler = logging.FileHandler(log_dir / "document_conversion.log")
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        financial_handler.setFormatter(formatter)
        conversion_handler.setFormatter(formatter)
        
        # Setup loggers
        financial_logger = logging.getLogger('financial')
        financial_logger.addHandler(financial_handler)
        financial_logger.setLevel(logging.INFO)
        
        conversion_logger = logging.getLogger('conversion')
        conversion_logger.addHandler(conversion_handler)
        conversion_logger.setLevel(logging.INFO)
        
        self.logger = logging.getLogger(__name__)
    
    def process_financial_document(self, input_path: str, **kwargs) -> Dict[str, Any]:
        """Complete financial document processing pipeline"""
        
        start_time = time.time()
        
        if self.console:
            self.console.print(Panel.fit(
                f"Processing Financial Document: {Path(input_path).name}\n"
                "Multi-format support with quality enhancement",
                title="Financial Document Processing",
                border_style="blue"
            ))
        
        try:
            # Step 1: Convert to PDF if needed
            self.display_message("Step 1: Document conversion and enhancement...", "info")
            
            pdf_path = self.converter.convert_to_pdf(
                input_path, 
                enhance_quality=self.config['auto_enhance_quality']
            )
            
            if not pdf_path:
                return {'success': False, 'error': 'Document conversion failed'}
            
            # Step 2: Analyze document
            self.display_message("Step 2: Document analysis and categorization...", "info")
            
            metadata = self.analyzer.analyze_document(pdf_path)
            
            # Step 3: Regional data extraction
            self.display_message("Step 3: Extracting data from specific regions...", "info")
            
            regional_data = self.regional_extractor.extract_regional_data(pdf_path)
            
            # Step 4: Generate processing summary
            processing_time = time.time() - start_time
            
            result = {
                'success': True,
                'input_file': input_path,
                'converted_pdf': pdf_path,
                'metadata': metadata.to_dict(),
                'regional_data': regional_data,
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat()
            }
            
            # Display summary
            self._display_processing_summary(result)
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.display_message(f"Processing failed: {e}", "error")
            
            return {
                'success': False,
                'error': str(e),
                'input_file': input_path,
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat()
            }
    
    def _display_processing_summary(self, result: Dict[str, Any]):
        """Display comprehensive processing summary"""
        
        metadata = result['metadata']
        regional_data = result['regional_data']
        
        if self.console:
            # Create summary table
            summary_table = Table(title="Financial Document Processing Summary")
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Value", style="green")
            
            summary_table.add_row("File Type", metadata['file_type'])
            summary_table.add_row("Pages", str(metadata['page_count']))
            summary_table.add_row("Tables Found", str(metadata['table_count']))
            summary_table.add_row("Categories", ", ".join(metadata['categories']))
            summary_table.add_row("Quality Score", f"{metadata['quality_score']:.2f}")
            summary_table.add_row("Processing Time", f"{result['processing_time']:.2f}s")
            
            self.console.print(summary_table)
            
            # Display financial indicators
            if metadata['financial_indicators']:
                indicators_table = Table(title="Financial Indicators Detected")
                indicators_table.add_column("Indicator", style="cyan")
                indicators_table.add_column("Value", style="yellow")
                
                for key, value in metadata['financial_indicators'].items():
                    value_str = str(value) if not isinstance(value, list) else ", ".join(map(str, value))
                    indicators_table.add_row(key.replace('_', ' ').title(), value_str)
                
                self.console.print(indicators_table)
            
            # Display regional extraction results
            if regional_data:
                regional_table = Table(title="Regional Data Extraction")
                regional_table.add_column("Region", style="cyan")
                regional_table.add_column("Data Found", style="green")
                
                for region, data in regional_data.items():
                    data_count = sum(len(page_data.get('extracted_data', {})) for page_data in data.values())
                    regional_table.add_row(region.replace('_', ' ').title(), str(data_count) + " items")
                
                self.console.print(regional_table)
        
        else:
            print(f"\nProcessing Summary:")
            print(f"  File Type: {metadata['file_type']}")
            print(f"  Pages: {metadata['page_count']}")
            print(f"  Tables: {metadata['table_count']}")
            print(f"  Categories: {', '.join(metadata['categories'])}")
            print(f"  Quality Score: {metadata['quality_score']:.2f}")
            print(f"  Processing Time: {result['processing_time']:.2f}s")
    
    def display_message(self, message: str, style: str = "info"):
        """Display formatted message"""
        if self.console:
            if style == "success":
                self.console.print(f"✅ {message}", style="green")
            elif style == "error":
                self.console.print(f"❌ {message}", style="red")
            elif style == "warning":
                self.console.print(f"⚠️ {message}", style="yellow")
            else:
                self.console.print(f"ℹ️ {message}", style="blue")
        else:
            print(f"[{style.upper()}] {message}")

def main():
    """Enhanced main function for financial document processing"""
    
    # Initialize enhanced system
    deployer = EnhancedPDFSystemDeployer()
    
    print("Enhanced PDF Financial Document Processing System")
    print("=" * 60)
    print("Supports: PDF, Word, Text, Images")
    print("Features: Quality enhancement, Regional extraction, Financial analysis")
    print("加速工具不可減少 - Acceleration tools are mandatory")
    
    # Example usage
    test_files = [
        "sample_analyst_report.pdf",
        "earnings_presentation.docx", 
        "financial_statement.jpg",
        "market_analysis.txt"
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"\nProcessing: {test_file}")
            result = deployer.process_financial_document(test_file)
            
            if result['success']:
                print(f"✓ Success: {result['metadata']['table_count']} tables found")
            else:
                print(f"✗ Failed: {result['error']}")
        else:
            print(f"Test file not found: {test_file}")
    
    print("\nSystem ready for financial document processing!")

if __name__ == "__main__":
    main()
