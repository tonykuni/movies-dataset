# VOFIE 範例需求

本文應依主題重構，轉為 Markdown、Word、PowerPoint、Excel、CSV，以及 HTML／CSS／JavaScript 模板。

## 文字內容

同一份資料先建立 Universal Content IR，再依用途輸出。原檔不可改寫，重複內容只標記，不可刪除。

## Python 元件

```python
def normalize_title(value: str) -> str:
    """Return a compact title without changing its words."""
    return " ".join(value.split())
```

## JavaScript 元件

```javascript
function selectTopic(id) {
  return topics.find((item) => item.id === id);
}
```

## HTML 規格

需要一個搜尋欄位、分類下拉選單、結果表格與匯出 CSV 按鈕。所有互動應支援鍵盤與可見焦點。

