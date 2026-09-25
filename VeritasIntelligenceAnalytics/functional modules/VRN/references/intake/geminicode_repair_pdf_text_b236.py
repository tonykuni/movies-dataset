import fitz  # PyMuPDF
import re

def repair_pdf_text(pdf_path, title_size_threshold=14.0):
    doc = fitz.open(pdf_path)
    structured_data = []

    for page in doc:
        # 提取包含字體、大小、粗細等詳細排版資訊的字典格式
        blocks = page.get_text("dict")["blocks"]
        
        for b in blocks:
            if b.get('type') == 0:  # 確保是文字區塊 (Text Block)
                block_text = ""
                max_size = 0.0
                is_bold = False
                is_light = False

                # 遍歷行 (lines) 與文字片段 (spans) 以取得字體特徵
                for l in b["lines"]:
                    for s in l["spans"]:
                        text = s["text"].strip()
                        if not text:
                            continue
                        
                        # 1. 識別字體大小
                        max_size = max(max_size, s["size"])
                        
                        # 2. 識別粗體與細體
                        # bit 4 (16) 通常代表粗體，字體名稱也常包含 Bold / Light
                        if (s["flags"] & 16) or "Bold" in s["font"]:
                            is_bold = True
                        elif "Light" in s["font"] or "Thin" in s["font"]:
                            is_light = True
                            
                        block_text += text

                if not block_text:
                    continue

                # 3. 判斷是否為標題 (基於字體大小與粗體特徵)
                is_title = (max_size >= title_size_threshold) or is_bold

                if is_title:
                    # 標題處理：移除結尾的句號
                    clean_title = re.sub(r'[。\.]$', '', block_text)
                    structured_data.append({
                        "category": "Title",
                        "text": clean_title,
                        "font_size": round(max_size, 1),
                        "style": "Bold" if is_bold else ("Light" if is_light else "Normal")
                    })
                else:
                    # 內文處理：修復跳行與斷句
                    # 移除不正常的跳行換行符號，將段落接回
                    merged_text = block_text.replace('\n', '')
                    
                    # 依據句號、問號、驚嘆號進行拆分，保留分割符號
                    sentences = re.split(r'(?<=[。！？])', merged_text)
                    
                    for sent in sentences:
                        sent = sent.strip()
                        if sent:
                            # 確保一個資料一個句號：若結尾無標點，則補上句號
                            if not re.search(r'[。！？]$', sent):
                                sent += '。'
                                
                            structured_data.append({
                                "category": "Body",
                                "text": sent,
                                "font_size": round(max_size, 1),
                                "style": "Bold" if is_bold else ("Light" if is_light else "Normal")
                            })
                            
    return structured_data

# 執行範例
# result = repair_pdf_text("sample.pdf")
# for item in result:
#     print(item)