import fitz  # PyMuPDF
import re

def build_document_hierarchy(pdf_path):
    doc = fitz.open(pdf_path)
    structured_blocks = []
    
    # 定義基礎字體大小範圍 (可依據實際文件微調)
    BODY_SIZE_MIN = 9.0
    BODY_SIZE_MAX = 12.5
    
    # 狀態機：是否已進入報告尾聲的附錄/免責聲明區
    in_appendix = False
    appendix_keywords = r"^(附錄|Appendix|免責聲明|References|參考文獻|Disclaimer)"

    for page_num, page in enumerate(doc):
        # 取得包含詳細排版與座標資訊的字典結構
        blocks = page.get_text("dict")["blocks"]
        page_height = page.rect.height
        
        for b in blocks:
            if b.get('type') == 0:  # 確保是文字區塊
                block_text = ""
                max_size = 0.0
                is_bold = False
                is_light = False
                
                # 取得區塊的底部 Y 座標，用於判斷頁尾
                y1_bottom = b["bbox"][3] 
                
                for l in b["lines"]:
                    for s in l["spans"]:
                        text = s["text"].strip()
                        if not text:
                            continue
                        
                        # 1. 抓取最大字體
                        max_size = max(max_size, s["size"])
                        
                        # 2. 識別粗體與細體
                        if (s["flags"] & 16) or "Bold" in s["font"]:
                            is_bold = True
                        elif "Light" in s["font"] or "Thin" in s["font"]:
                            is_light = True
                            
                        block_text += text
                
                if not block_text:
                    continue

                # 3. 判斷是否進入附錄區塊
                if not in_appendix and re.search(appendix_keywords, block_text, re.IGNORECASE):
                    in_appendix = True
                
                category = "Body"
                
                # ==========================
                # 階層分類邏輯 (Rule-based)
                # ==========================
                
                # 規則 A: 頁尾小字體不相關文字
                # 若位於頁面底部 10% 且字體極小，視為頁尾雜訊
                is_footer_area = y1_bottom > (page_height * 0.9)
                if max_size < BODY_SIZE_MIN and is_footer_area:
                    category = "Noise_Footer"
                    
                # 規則 B: 標題階層 (H1 大 / H2 中 / H3 小)
                elif max_size >= 18.0 or (max_size >= 16.0 and is_bold):
                    category = "Title_Large (H1)"
                elif max_size >= 14.0 or (max_size >= 13.0 and is_bold):
                    category = "Title_Medium (H2)"
                elif (max_size > BODY_SIZE_MAX) or (max_size >= BODY_SIZE_MIN and is_bold and len(block_text) < 50):
                    # 字體微大，或是常規大小但標粗體且很短
                    category = "Title_Small (H3)"
                    
                # 規則 C: 本文與細體
                elif is_light or max_size < BODY_SIZE_MIN:
                    category = "Body_Light_or_Small"
                else:
                    category = "Body"

                # ==========================
                # 狀態覆寫：附錄與報告後內容
                # ==========================
                if in_appendix:
                    if category.startswith("Title"):
                        category = "Appendix_Title"
                    elif category != "Noise_Footer":
                        category = "Appendix_Small_Text" # 報告後不相關文字

                # 封裝成標準化 JSON 格式
                structured_blocks.append({
                    "page": page_num + 1,
                    "category": category,
                    "text": block_text,
                    "font_size": round(max_size, 1),
                    "font_weight": "Bold" if is_bold else ("Light" if is_light else "Normal")
                })
                
    return structured_blocks

# 執行範例
# result = build_document_hierarchy("report.pdf")
# for item in result:
#     print(item)