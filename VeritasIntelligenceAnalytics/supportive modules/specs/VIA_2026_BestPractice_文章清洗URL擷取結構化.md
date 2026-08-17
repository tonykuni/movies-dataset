<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# 讀取繁簡體中文英文文字修復斷句錯字區分標題本文及連續不同的內文將一連串訊息區分不同文章  URL  標題  本文  分類  可以進入URL EVERNOTE  抓取HTML擷取資訊如新聞媒體時間本文除去其他不相關的資訊

可以。這項工作可設計成一個「多語言文章整理與結構化擷取」流程，將一連串混合繁體中文、簡體中文、英文、URL 與雜訊的訊息，拆分成多篇文章，修復文字後輸出為：


| URL | 標題 | 本文 | 分類 |
| :-- | :-- | :-- | :-- |
| 文章網址 | 清理後標題 | 清理後正文 | 新聞、金融、科技、專案管理等 |

Evernote 可作為原始筆記來源；公開網頁可以透過 URL 擷取 HTML，再清除廣告、導覽列與其他無關內容。Evernote 本身也提供筆記整理與搜尋功能。[^1_1]

## 建議處理流程

1. **讀取來源**
    - 純文字、Markdown、HTML。
    - 一連串訊息。
    - Evernote 匯出檔，例如 ENEX、HTML、TXT。
    - 公開 URL。
    - 私人 Evernote 筆記則需要使用者提供匯出檔，或透過已授權的 Evernote API；目前此對話沒有可直接連線的 Evernote 連接器。
2. **分割不同文章**
依照下列線索判斷文章邊界：
    - URL 改變。
    - 出現新的標題。
    - 出現新聞媒體名稱或發布時間。
    - 明顯的分隔符號，例如 `---`、換行、項目符號。
    - 連續文字中出現新的網域。

```
- HTML 中的 `<article>`、`<h1>`、`<h2>`、`<time>` 區塊。
```

    - 同一篇文章的標題、時間、來源與正文應合併。
3. **擷取網頁內容**
    - 讀取 `<title>`、`og:title`、`h1`。
    - 擷取 `article`、`main` 或主要內容區塊。
    - 讀取 `article:published_time`、`datePublished`、`time`。
    - 擷取新聞媒體或網站名稱。
    - 移除廣告、Cookie 提示、留言區、推薦文章、導覽列、頁尾與重複文字。
4. **文字清理與修復**
    - 繁體中文、簡體中文、英文混合保留原意。
    - 修復錯誤換行與斷句。
    - 合併被拆開的中文字詞。
    - 修正 OCR 常見錯字。
    - 修復標點符號與段落。
    - 將全形、半形標點統一。
    - 移除重複標題、重複段落與無意義空白。
    - 不確定的錯字不直接改寫，可標記為待確認。
5. **判斷標題與正文**
    - 優先使用網頁的 `og:title`、`<h1>` 或結構化資料。
    - 若標題缺失，從開頭短句推測。
    - 正文保留段落，不把圖片說明、作者資訊、分享按鈕混入本文。
    - 來源、作者、發布時間可另外放在中間欄位或 metadata。
6. **文章分類**
可使用規則或 AI 分類，例如：
    - 新聞
    - 財經／投資
    - 科技
    - 軟體／開發
    - 專案管理
    - 政策／法規
    - 學術／研究
    - 教學
    - 其他

## 建議輸出格式

### 表格格式

```text
URL | 標題 | 本文 | 分類
```


### JSON 格式

```json
[
  {
    "url": "https://example.com/article",
    "title": "清理後的文章標題",
    "body": "清理後的文章正文……",
    "category": "科技",
    "source": "Example News",
    "published_at": "2026-08-12T10:30:00+08:00",
    "language": ["zh-TW", "en"],
    "quality_flags": []
  }
]
```


### Markdown 格式

```markdown
## 文章 1

- URL: https://example.com/article
- 標題：清理後的文章標題
- 分類：科技
- 媒體：Example News
- 發布時間：2026-08-12 10:30

### 本文

清理後的文章正文……
```


## Python 實作架構

如果要自行建立工具，可以採用以下模組：

```text
input/
├── evernote.enex
├── messages.txt
└── urls.txt

pipeline/
├── source_reader.py       # 讀取 TXT、HTML、ENEX
├── article_segmenter.py   # 分割不同文章
├── url_fetcher.py         # 擷取 URL
├── html_cleaner.py        # 移除網頁雜訊
├── text_normalizer.py     # 文字修復與格式統一
├── metadata_extractor.py  # 標題、媒體、日期
├── classifier.py          # 文章分類
└── exporter.py            # 輸出 CSV、JSON、Markdown、SQLite
```

可使用的開源 Python 套件包括：

```text
beautifulsoup4     HTML 解析
trafilatura        主要文章內容擷取
readability-lxml   網頁正文判斷
lxml               XML／HTML 處理
dateparser         多語言日期解析
langdetect         語言辨識
opencc             繁簡中文轉換
pandas              表格處理
sqlite3／DuckDB    結構化儲存
```


## 需要特別處理的情況

- **登入後的 Evernote 筆記**：不能只靠公開 URL 讀取，必須使用匯出檔或授權 API。
- **付費新聞網站**：若正文被登入牆遮蔽，只能擷取公開部分，不能繞過權限。
- **JavaScript 動態網頁**：一般 HTML 擷取可能沒有正文，需要瀏覽器自動化工具，例如 Playwright。
- **掃描 PDF 或圖片**：需要 OCR，並依文字座標重新組合段落。
- **錯字修復**：應採取保守模式，避免把專有名詞、股票代號、網址或程式碼錯誤改寫。
- **混合語言**：中文與英文內容應保留原語言，不建議在清理階段強制全部翻譯。


## 建議的實際操作方式

你可以直接提供以下任一種資料：

1. 貼上一串原始訊息。
2. 提供一個或多個公開 URL。
3. 上傳 Evernote 匯出的 `.enex` 或 `.html` 檔。
4. 提供包含 URL 的 TXT、CSV 或 Markdown 檔。

我可以依照上述規則，將內容分割、修復、清理，最後輸出成「URL、標題、本文、分類」表格；若需要，也可以進一步產生 CSV、JSON、Markdown 或適合匯入 SQLite／DuckDB 的資料格式。
<span style="display:none">[^1_10][^1_2][^1_3][^1_4][^1_5][^1_6][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://apps.microsoft.com/detail/9wzdncrfj3mb?hl=zh-HK\&gl=HK

[^1_2]: https://translate.google.com/?hl=zh-TW\&langpair=zh-TW|zh-CN

[^1_3]: https://translate.google.com/?hl=zh-TW

[^1_4]: https://www.cc.ntu.edu.tw/chinese/epaper/home/20230620_006507.html

[^1_5]: https://immersivetranslate.com/zh-TW/

[^1_6]: https://wordvice.ai/tw/tools/translate

[^1_7]: https://web.archive.org/web/20150922191632/http:/blog.mozilla.com.tw/posts/1012/【add-on-一點通】學生篇-「evernote-web-clipper」

[^1_8]: https://www.kjsh.ntpc.edu.tw/resource/openfid.php?id=12489

[^1_9]: https://www.twjh.tyc.edu.tw/modules/tadnews/index.php?op=tufdl\&files_sn=8594

[^1_10]: https://lib.ntsu.edu.tw/p/412-1005-3216.php?Lang=zh-tw


---

# 如何用 Python 實作 BeautifulSoup 擷取網頁內文

可以用 `requests` 下載 HTML，再用 `BeautifulSoup` 解析 DOM，最後依照網頁結構擷取標題、發布時間、媒體名稱與正文。BeautifulSoup 常用的定位方法包括 `find()`、`find_all()`、CSS selector 的 `select()`，而 `get_text()` 可取得標籤內的純文字。[^2_1][^2_2]

## 1. 安裝套件

```bash
pip install requests beautifulsoup4 lxml
```

- `requests`：下載網頁。
- `beautifulsoup4`：解析 HTML。
- `lxml`：較快速且容錯性較好的 HTML 解析器。


## 2. 基本擷取範例

```python
import requests
from bs4 import BeautifulSoup

url = "https://example.com/article"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    )
}

response = requests.get(
    url,
    headers=headers,
    timeout=20
)

response.raise_for_status()

soup = BeautifulSoup(response.text, "lxml")

title = soup.title.get_text(" ", strip=True) if soup.title else ""
body = soup.get_text("\n", strip=True)

print("標題：", title)
print("全文：")
print(body)
```

這種方法會讀取整個頁面的文字，因此通常會包含導覽列、廣告、登入提示、推薦文章與頁尾，不適合直接當作新聞正文。

## 3. 依 HTML 標籤擷取正文

假設網頁 HTML 如下：

```html
<h1 class="article-title">台灣市場今日焦點</h1>

<div class="article-meta">
    2026-08-12 18:30
</div>

<article class="article-content">
    <p>第一段新聞內容。</p>
    <p>第二段新聞內容。</p>
</article>
```

可以使用 CSS selector：

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, "lxml")

title_node = soup.select_one("h1.article-title")
time_node = soup.select_one(".article-meta")
content_node = soup.select_one("article.article-content")

title = title_node.get_text(" ", strip=True) if title_node else ""
published_at = time_node.get_text(" ", strip=True) if time_node else ""

if content_node:
    paragraphs = [
        p.get_text(" ", strip=True)
        for p in content_node.select("p")
    ]
    body = "\n\n".join(paragraphs)
else:
    body = ""

result = {
    "title": title,
    "published_at": published_at,
    "body": body
}
```

`select_one()` 只回傳第一個符合的節點；`select()` 則回傳所有符合 CSS selector 的節點。這種方式適合已經知道目標網站 HTML 結構的情況。

## 4. 通用新聞文章擷取器

不同網站使用的 class 名稱不同，因此可以準備多組候選 selector：

```python
import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    )
}


def clean_text(text: str) -> str:
    """清理多餘空白、空行與不可見字元。"""
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def first_text(soup: BeautifulSoup, selectors: list[str]) -> str:
    """依序嘗試多個 selector，回傳第一個有內容的結果。"""
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            text = clean_text(node.get_text(" ", strip=True))
            if text:
                return text
    return ""


def extract_article(url: str) -> dict:
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "lxml")

    # 移除不應進入正文的區塊
    for tag in soup.select(
        "script, style, noscript, iframe, nav, footer, "
        "header, aside, form, .advertisement, .ads, .cookie"
    ):
        tag.decompose()

    title = first_text(soup, [
        'meta[property="og:title"]',
        'meta[name="twitter:title"]',
        "h1",
        "title",
    ])

    # meta 標籤使用 content 屬性，不是 get_text()
    og_title = soup.select_one('meta[property="og:title"]')
    if og_title and og_title.get("content"):
        title = clean_text(og_title["content"])

    published_at = first_text(soup, [
        'meta[property="article:published_time"]',
        'meta[name="date"]',
        'meta[name="pubdate"]',
        "time[datetime]",
        "time",
        ".published-date",
        ".publish-date",
        ".article-date",
        ".post-date",
    ])

    time_node = soup.select_one("time[datetime]")
    if time_node and time_node.get("datetime"):
        published_at = time_node["datetime"]

    source = first_text(soup, [
        'meta[property="og:site_name"]',
        'meta[name="application-name"]',
        ".site-name",
        ".publisher",
    ])

    # 優先找常見的文章正文區塊
    content_node = None
    content_selectors = [
        "article",
        '[itemprop="articleBody"]',
        ".article-body",
        ".article-content",
        ".post-content",
        ".entry-content",
        ".story-body",
        ".news-content",
        "main",
    ]

    for selector in content_selectors:
        node = soup.select_one(selector)
        if node:
            content_node = node
            break

    if content_node:
        # 移除正文區塊內的雜訊
        for tag in content_node.select(
            "script, style, noscript, iframe, "
            "nav, footer, aside, form, .ads, .advertisement"
        ):
            tag.decompose()

        paragraphs = []

        for node in content_node.select("p, h2, h3, blockquote, li"):
            text = clean_text(node.get_text(" ", strip=True))

            # 避免短標籤、分享按鈕或重複文字混入
            if len(text) >= 15:
                paragraphs.append(text)

        body = "\n\n".join(dict.fromkeys(paragraphs))
    else:
        body = ""

    return {
        "url": url,
        "title": title,
        "published_at": published_at,
        "source": source,
        "body": body,
        "domain": urlparse(url).netloc,
    }


if __name__ == "__main__":
    url = "https://example.com/article"

    try:
        article = extract_article(url)
        print(json.dumps(article, ensure_ascii=False, indent=2))
    except requests.RequestException as exc:
        print(f"網頁下載失敗：{exc}")
```


## 5. 修正 `meta` 標籤擷取

`meta` 通常沒有文字內容，而是把資料放在 `content` 屬性中：

```html
<meta property="og:title" content="文章標題">
<meta property="article:published_time"
      content="2026-08-12T18:30:00+08:00">
```

正確寫法：

```python
def get_meta_content(soup, selector):
    node = soup.select_one(selector)
    return node.get("content", "").strip() if node else ""


title = get_meta_content(
    soup,
    'meta[property="og:title"]'
)

published_at = get_meta_content(
    soup,
    'meta[property="article:published_time"]'
)
```


## 6. 處理繁簡體與中英文內容

如果只需要保留原文，不要在擷取階段直接轉換繁簡體。若需要統一為繁體中文，可使用 OpenCC：

```bash
pip install opencc-python-reimplemented
```

```python
from opencc import OpenCC

converter = OpenCC("s2t")  # 簡體轉繁體

body_traditional = converter.convert(body)
title_traditional = converter.convert(title)
```

可選設定：

```python
OpenCC("s2t")      # 簡體中文轉繁體中文
OpenCC("t2s")      # 繁體中文轉簡體中文
OpenCC("s2tw")     # 簡體轉台灣繁體
OpenCC("tw2sp")    # 台灣繁體轉簡體
```

金融文章中的股票代號、英文公司名、URL、程式碼與數字，建議在轉換前後進行保護，避免專有名詞被錯誤處理。

## 7. 網頁沒有正文的常見原因

### JavaScript 動態載入

如果 `requests` 取得的 HTML 沒有文章內容，可能是正文由 JavaScript 載入。這時可使用 Playwright：

```bash
pip install playwright
playwright install chromium
```

```python
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def fetch_dynamic_html(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        html = page.content()
        browser.close()
        return html


html = fetch_dynamic_html("https://example.com/article")
soup = BeautifulSoup(html, "lxml")
```


### 需要登入或付費訂閱

BeautifulSoup 只能解析已取得的 HTML，不能自行繞過登入或付費牆。對私人 Evernote 筆記或需登入的網站，應使用合法授權、匯出檔或官方 API。

### 網站結構不固定

若要處理大量不同媒體網站，單純依賴 `.article-content` 不夠穩定。可以先使用：

```python
article = soup.find("article")
```

若沒有 `<article>`，再依序嘗試 `itemprop="articleBody"`、`main` 與常見 class。BeautifulSoup 負責 HTML 結構解析，但不一定能準確判斷哪一段是「主要文章內容」；這也是新聞擷取時通常會搭配正文抽取器的原因。

## 8. 輸出 CSV

```python
import pandas as pd

urls = [
    "https://example.com/article-1",
    "https://example.com/article-2",
]

records = []

for url in urls:
    try:
        records.append(extract_article(url))
    except Exception as exc:
        records.append({
            "url": url,
            "title": "",
            "published_at": "",
            "source": "",
            "body": "",
            "error": str(exc),
        })

df = pd.DataFrame(records)

df.to_csv(
    "articles.csv",
    index=False,
    encoding="utf-8-sig"
)
```

最實用的基本架構是：

```text
requests 下載 HTML
        ↓
BeautifulSoup 解析 DOM
        ↓
CSS selector 擷取 title、time、article
        ↓
清除 script、廣告、導覽列
        ↓
整理段落與空白
        ↓
OpenCC 統一繁簡體
        ↓
輸出 CSV／JSON／DuckDB
```

對單一網站，建議針對該網站的 HTML 結構寫專用 selector；對多個新聞網站，則採用「候選 selector + fallback + 品質檢查」的方式，並對正文長度、標題是否存在、發布時間是否可解析建立驗證欄位。
<span style="display:none">[^2_10][^2_3][^2_4][^2_5][^2_6][^2_7][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://steam.oxxostudio.tw/category/python/spider/beautiful-soup.html

[^2_2]: https://ithelp.ithome.com.tw/articles/10361966

[^2_3]: https://medium.com/此生故彼生/python-以beautiful-soup-抓取與解析網頁資料-網路爬蟲-351206c549b1

[^2_4]: https://medium.com/seaniap/python爬蟲-2-beautiful-soup的網頁爬取技巧-dbb8eb625897

[^2_5]: https://chwang12341.medium.com/coding起來-python自動化爬蟲-beautifulsoup美麗湯套件-方法教學-88225355840c

[^2_6]: https://www.learncodewithmike.com/2020/02/python-beautifulsoup-web-scraper.html

[^2_7]: https://ithelp.ithome.com.tw/articles/10186119

[^2_8]: https://blog.gtwang.org/programming/python-beautiful-soup-module-scrape-web-pages-tutorial/2/

[^2_9]: https://hackmd.io/@aaronlife/python-topic-beautifulsoup

[^2_10]: https://thunderbit.com/zh-Hant/blog/how-to-pull-data-from-a-website-python


---

# BeautifulSoup 的 find 與 select 效能比較

就 BeautifulSoup 而言，`find()` 與 `select_one()` 的效能差異通常不大；在簡單查詢中，`find()` 往往較快，而在複雜階層或 CSS selector 查詢中，`select()` 語法較方便，但不代表一定較快。真正影響整體爬蟲速度的通常是網路下載、HTML 解析與 JavaScript 載入，而不是單次節點搜尋。[^3_1][^3_2]

## 方法對照

| 需求 | BeautifulSoup 方法 | 回傳結果 | 適合情境 |
| :-- | :-- | :-- | :-- |
| 找第一個標籤 | `find()` | `Tag` 或 `None` | 簡單標籤或屬性查詢 |
| 找全部標籤 | `find_all()` | `ResultSet` | 多元素、條件式查詢 |
| 找第一個 CSS selector | `select_one()` | `Tag` 或 `None` | 複雜階層或 CSS 查詢 |
| 找全部 CSS selector | `select()` | `ResultSet` | class、id、後代、子元素、屬性選擇 |

常見對應關係如下：

```python
soup.find("article")
soup.select_one("article")
```

以及：

```python
soup.find_all("p")
soup.select("p")
```

但兩者的查詢語法不同：`find()` 使用標籤、屬性與關鍵字參數；`select()` 使用 CSS selector。[^3_3][^3_4]

## 簡單查詢的效能

例如只尋找第一個 `<article>`：

```python
article_1 = soup.find("article")
article_2 = soup.select_one("article")
```

這類簡單查詢通常建議使用：

```python
soup.find("article")
```

原因是 `find()` 的條件較直接，不需要解析 CSS selector。對大量頁面與大量重複查詢而言，這種差異可能累積起來。實際比較中，`find_all()` 對簡單標籤查詢有時會略快於 `select()`，但結果會受到 HTML 結構、解析器與 selector 複雜度影響。[^3_1]

## 複雜查詢的效能

以下 CSS selector：

```python
node = soup.select_one(
    "main article div.article-content > p:first-of-type"
)
```

若改用 `find()`，可能需要多層巢狀程式碼：

```python
main = soup.find("main")
article = main.find("article") if main else None
content = (
    article.find("div", class_="article-content")
    if article else None
)
paragraph = content.find("p") if content else None
```

因此複雜查詢通常使用 `select_one()` 可讀性較好：

```python
node = soup.select_one(
    "main article div.article-content > p:first-of-type"
)
```

這不表示 `select_one()` 必然更快，而是它能以一個 selector 表達較複雜的結構。當程式可讀性與維護性比微小效能差異重要時，使用 `select_one()` 通常更合適。

## 可重現的 benchmark

不要只測單次呼叫，應固定：

- 相同 HTML。
- 相同 BeautifulSoup 物件。
- 相同解析器，例如都使用 `lxml`。
- 相同匹配條件。
- 足夠多的迭代次數。
- 不把網路下載時間放進搜尋測試。

```python
from timeit import timeit
from bs4 import BeautifulSoup


html = """
<html>
<body>
    <main>
        <article class="news">
            <h1>測試標題</h1>
            <div class="article-content">
                <p>第一段內容。</p>
                <p>第二段內容。</p>
            </div>
        </article>
    </main>
</body>
</html>
""" * 100

soup = BeautifulSoup(html, "lxml")

tests = {
    "find": lambda: soup.find("article"),
    "select_one": lambda: soup.select_one("article"),
    "find_class": lambda: soup.find(
        "article",
        class_="news"
    ),
    "select_class": lambda: soup.select_one(
        "article.news"
    ),
    "find_all_p": lambda: soup.find_all("p"),
    "select_p": lambda: soup.select("p"),
    "find_nested": lambda: (
        soup.find("main")
        .find("article", class_="news")
        .find("div", class_="article-content")
        .find("p")
    ),
    "select_nested": lambda: soup.select_one(
        "main article.news > div.article-content > p"
    ),
}

for name, func in tests.items():
    seconds = timeit(func, number=1000)
    print(f"{name:16} {seconds:.6f} 秒")
```

這個測試的重點不是得到一個固定排名，而是比較「你實際使用的 HTML 結構與查詢方式」。不同網頁、不同 selector 和不同 BeautifulSoup 版本可能得到不同結果；公開測試也指出，效能會受到樹狀結構深度、搜尋位置與 selector 形式影響。[^3_1]

## 實務選擇建議

### 使用 `find()` 的情況

```python
title = soup.find("h1")
article = soup.find("article")
date = soup.find("time")
```

適合：

- 只找一個標籤。
- 只需要第一個符合項目。
- 查詢條件簡單。
- 大量頁面批次處理。
- 追求較低的查詢開銷。

帶屬性查詢：

```python
content = soup.find(
    "div",
    class_="article-content"
)
```

也可以使用正規表示式：

```python
import re

date_node = soup.find(
    "time",
    class_=re.compile(r"date|publish|time", re.I)
)
```


### 使用 `select()` 的情況

```python
paragraphs = soup.select(
    "article.article-content p"
)
```

適合：

- 多層 HTML 結構。
- CSS class 或 id 選擇。
- 後代、子元素、兄弟元素關係。
- 屬性選擇器。
- 需要 `:first-of-type` 等 CSS 條件。

例如：

```python
links = soup.select(
    "main article a[href]"
)
```

```python
images = soup.select(
    "article img[src]"
)
```

```python
first_paragraph = soup.select_one(
    "article > div.content > p:first-of-type"
)
```


## 對你的文章擷取流程的建議

針對「URL、標題、本文、分類、媒體、時間」擷取，可以採用混合策略：

```python
def get_first(soup, selectors):
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            return node
    return None


# 標題：使用 select_one，方便處理多種候選結構
title_node = get_first(soup, [
    'meta[property="og:title"]',
    'meta[name="twitter:title"]',
    "h1.article-title",
    "h1",
    "title",
])

# 正文容器：使用 select_one，支援多種網站 class
content_node = get_first(soup, [
    "article",
    '[itemprop="articleBody"]',
    ".article-content",
    ".article-body",
    ".post-content",
    "main",
])

# 段落：在已經定位的正文容器內使用 select
paragraphs = []

if content_node:
    for p in content_node.select("p"):
        text = p.get_text(" ", strip=True)
        if len(text) >= 15:
            paragraphs.append(text)

body = "\n\n".join(paragraphs)
```

這樣做的好處是：

1. 先用 `select_one()` 找可能的正文容器。
2. 再限定在正文容器內查詢，避免掃描整個文件。
3. 使用 `select("p")` 取得全部段落。
4. 不在每個段落上重新從 `soup` 搜尋。

## 重要的效能優化

### 先縮小搜尋範圍

不建議：

```python
paragraphs = soup.select("p")
```

因為可能把導覽列、推薦文章與頁尾的 `<p>` 一起抓進來。

較好：

```python
article = soup.select_one("article")

if article:
    paragraphs = article.select("p")
```


### 不要在迴圈中重複掃描整份 HTML

不建議：

```python
for keyword in keywords:
    node = soup.select_one(
        f"article p:contains('{keyword}')"
    )
```

應先取得正文：

```python
article = soup.select_one("article")
paragraphs = article.select("p") if article else []

for paragraph in paragraphs:
    text = paragraph.get_text(" ", strip=True)
    # 在 Python 中判斷關鍵字
```


### 避免把下載時間算入搜尋效能

以下測試混合了網路時間，不適合比較 `find()` 與 `select()`：

```python
def test():
    html = requests.get(url).text
    soup = BeautifulSoup(html, "lxml")
    return soup.find("article")
```

應拆成兩部分：

```python
html = requests.get(url, headers=HEADERS).content
soup = BeautifulSoup(html, "lxml")

find_time = timeit(
    lambda: soup.find("article"),
    number=1000
)

select_time = timeit(
    lambda: soup.select_one("article"),
    number=1000
)
```


## 結論

- **簡單單元素查詢**：優先使用 `find()`。
- **簡單多元素查詢**：使用 `find_all()`。
- **複雜階層、class、id 或屬性查詢**：使用 `select_one()` 或 `select()`。
- **需要全部結果**：比較 `find_all()` 與 `select()`，不要拿 `find()` 與 `select()` 直接比較。
- **文章擷取實務**：先用 `select_one()` 定位正文容器，再在容器內使用 `select("p")`。
- **高效能關鍵**：縮小搜尋範圍、避免重複掃描、固定 parser，並以實際網站 HTML 進行 benchmark。
<span style="display:none">[^3_10][^3_5][^3_6][^3_7][^3_8][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://stackoverflow.com/questions/39033612/bs4-select-one-vs-find/39036044

[^3_2]: https://stackoverflow.com/questions/38028384/beautifulsoup-difference-between-find-and-select

[^3_3]: https://nabi.104.com.tw/posts/nabi_post_e5292d37-e61c-4066-82b8-077336ea745f

[^3_4]: https://ithelp.ithome.com.tw/articles/10218559

[^3_5]: https://stackoverflow.com/questions/72531567/bs4-soup-select-vs-soup-find

[^3_6]: https://www.pythontutorials.net/blog/beautifulsoup-difference-between-find-and-select/

[^3_7]: https://www.zhanid.com/biancheng/4726.html

[^3_8]: https://blog.csdn.net/weixin_62543649/article/details/125769718

[^3_9]: https://blog.csdn.net/weixin_45730515/article/details/104951893

[^3_10]: https://www.learncodewithmike.com/2020/02/python-beautifulsoup-web-scraper.html


---

# bs4 findall 替代方案 lxml xpath

`BeautifulSoup.find_all()` 的主要替代方案是 `lxml.html` 搭配 XPath。BeautifulSoup 本身不原生支援 XPath；如果需要父節點、兄弟節點、條件判斷、索引或依文字定位，使用 `lxml` 會更直接。[^4_1][^4_2]

## 基本替換

### BeautifulSoup

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, "lxml")

nodes = soup.find_all("p")

for node in nodes:
    print(node.get_text(" ", strip=True))
```


### lxml XPath

```python
from lxml import html

tree = html.fromstring(html_content)

nodes = tree.xpath("//p")

for node in nodes:
    print(" ".join(node.itertext()).strip())
```

注意：上面的變數名稱不要同時叫作 `html`，否則會覆蓋 `lxml.html` 模組。建議使用：

```python
from lxml import html as lxml_html

tree = lxml_html.fromstring(html_content)
```


## 常見 `find_all()` 對照

| BeautifulSoup | lxml XPath |
| :-- | :-- |
| `soup.find_all("p")` | `tree.xpath("//p")` |
| `soup.find_all("a")` | `tree.xpath("//a")` |
| `soup.find_all("div", id="main")` | `tree.xpath('//div[@id="main"]')` |
| `soup.find_all("div", class_="item")` | `tree.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " item ")]')` |
| `soup.find_all("a", href=True)` | `tree.xpath("//a[@href]")` |
| `soup.find_all("input", type="text")` | `tree.xpath('//input[@type="text"]')` |
| `soup.find_all("li", limit=3)` | `tree.xpath("//li")[:3]` |
| `soup.select("article p")` | `tree.xpath("//article//p")` |
| `soup.select("article > p")` | `tree.xpath("//article/p")` |

## 擷取文字與屬性

### 擷取純文字

BeautifulSoup：

```python
texts = [
    node.get_text(" ", strip=True)
    for node in soup.find_all("p")
]
```

lxml：

```python
texts = [
    " ".join(node.itertext()).strip()
    for node in tree.xpath("//p")
]
```

也可以直接讓 XPath 回傳文字：

```python
texts = tree.xpath("//p//text()")
texts = [text.strip() for text in texts if text.strip()]
```

兩種寫法的差別是：

```python
tree.xpath("//p")
```

回傳 `<p>` 元素節點；而：

```python
tree.xpath("//p//text()")
```

回傳文字字串清單。

### 擷取連結

BeautifulSoup：

```python
links = [
    {
        "text": a.get_text(" ", strip=True),
        "href": a.get("href")
    }
    for a in soup.find_all("a", href=True)
]
```

lxml：

```python
links = [
    {
        "text": " ".join(a.itertext()).strip(),
        "href": a.get("href")
    }
    for a in tree.xpath("//a[@href]")
]
```

如果只需要 URL：

```python
hrefs = tree.xpath("//a[@href]/@href")
```

如果只需要圖片來源：

```python
image_urls = tree.xpath("//img[@src]/@src")
```


## XPath 的優勢

### 依文字內容查找

```python
nodes = tree.xpath(
    "//a[contains(normalize-space(.), '下一頁')]"
)
```

BeautifulSoup 若要做相同工作，通常需要先找出所有連結，再用 Python 篩選：

```python
nodes = [
    a for a in soup.find_all("a")
    if "下一頁" in a.get_text(" ", strip=True)
]
```


### 依兄弟節點查找

取得「標題為發布時間的元素」後面的下一個元素：

```python
nodes = tree.xpath(
    "//h2[contains(normalize-space(.), '發布時間')]/following-sibling::*[^4_1]"
)
```


### 依父節點查找

找出包含特定文字的段落所屬的 `<article>`：

```python
articles = tree.xpath(
    "//p[contains(., '市場分析')]/ancestor::article[^4_1]"
)
```


### 依位置選取

取得第一個、第二個與最後一個 `<li>`：

```python
first_item = tree.xpath("//li[^4_1]")
second_item = tree.xpath("//li[^4_2]")
last_item = tree.xpath("//li[last()]")
```

注意 XPath 的索引從 `1` 開始，不是 Python 常見的 `0`：

```python
tree.xpath("//li[^4_1]")  # 第一個 li
```


## 擷取新聞正文範例

```python
import re
import requests
from lxml import html as lxml_html
from urllib.parse import urljoin


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    )
}


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def node_text(node) -> str:
    return clean_text(" ".join(node.itertext()))


def first_node(tree, xpaths):
    for xpath in xpaths:
        nodes = tree.xpath(xpath)
        if nodes:
            node = nodes[^4_0]

            # 某些 XPath 可能直接回傳字串
            if isinstance(node, str):
                return node.strip()

            if node_text(node):
                return node
    return None


def extract_article(url: str) -> dict:
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    )
    response.raise_for_status()

    tree = lxml_html.fromstring(response.content)

    # 移除雜訊區塊
    for node in tree.xpath(
        "//script | //style | //noscript | //iframe | "
        "//nav | //footer | //aside | //form"
    ):
        parent = node.getparent()
        if parent is not None:
            parent.remove(node)

    title_node = first_node(tree, [
        '//meta[@property="og:title"]/@content',
        '//meta[@name="twitter:title"]/@content',
        "//h1",
        "//title",
    ])

    if isinstance(title_node, str):
        title = clean_text(title_node)
    elif title_node is not None:
        title = node_text(title_node)
    else:
        title = ""

    time_values = tree.xpath(
        '//meta[@property="article:published_time"]/@content'
    )

    if not time_values:
        time_values = tree.xpath("//time/@datetime")

    if not time_values:
        time_values = tree.xpath(
            "//time//text() | "
            '//*[contains(@class, "publish")]//text() | '
            '//*[contains(@class, "date")]//text()'
        )

    published_at = clean_text(" ".join(time_values))

    content_node = first_node(tree, [
        "//article",
        '//*[@itemprop="articleBody"]',
        '//*[contains(@class, "article-content")]',
        '//*[contains(@class, "article-body")]',
        '//*[contains(@class, "post-content")]',
        "//main",
    ])

    paragraphs = []

    if content_node is not None:
        for p in content_node.xpath(
            ".//p | .//h2 | .//h3 | .//blockquote"
        ):
            text = node_text(p)

            if len(text) >= 15:
                paragraphs.append(text)

    body = "\n\n".join(dict.fromkeys(paragraphs))

    return {
        "url": url,
        "title": title,
        "published_at": published_at,
        "body": body,
    }


article = extract_article("https://example.com/article")
print(article)
```


## `class` 查詢的注意事項

這個 XPath：

```python
tree.xpath('//div[@class="item"]')
```

只會匹配：

```html
<div class="item">
```

但不一定會匹配：

```html
<div class="item active">
```

因為 `class` 是多值屬性。較可靠的寫法是：

```python
tree.xpath(
    '//div[contains(concat(" ", normalize-space(@class), " "), " item ")]'
)
```

也可以使用 XPath 1.0 的 `contains()`：

```python
tree.xpath(
    '//div[contains(@class, "article-content")]'
)
```

但後者可能誤匹配：

```text
article-content-old
```

因此在正式爬蟲中，建議使用完整的 class token 寫法。

## 效能與選擇建議

`lxml` 以 C 實作核心，通常在大量 HTML 或大量 XPath 查詢時較有優勢；實際效能仍會受到解析器、HTML 大小、查詢複雜度和資料量影響，應用自己的資料 benchmark，而不是只依賴一般測試結果。[^4_3]


| 情境 | 建議 |
| :-- | :-- |
| 小型爬蟲、快速開發 | BeautifulSoup |
| 需要 XPath | `lxml.html` |
| 大量網頁批次處理 | 優先測試 `lxml` |
| HTML 結構複雜 | `lxml` + XPath |
| HTML 嚴重破損 | 比較 `lxml.html`、`html5lib` 的解析結果 |
| 需要簡單可讀的查詢 | BeautifulSoup `find_all()` |
| 需要依文字、父層、兄弟、位置查找 | XPath |
| 已經有 BeautifulSoup 程式碼 | 不必為了理論效能立即全部改寫 |

最實務的替代寫法是：

```python
# BeautifulSoup
nodes = soup.find_all(
    "div",
    class_="article-content"
)

# lxml XPath
nodes = tree.xpath(
    '//div[contains(concat(" ", normalize-space(@class), " "), " article-content ")]'
)
```

對你的新聞文章擷取流程，建議使用 `lxml.html` 建立解析樹，再用 XPath 擷取 `title`、`time`、`article`、`p` 和 `href`；若網站結構非常不固定，再搭配多組 XPath fallback。
<span style="display:none">[^4_10][^4_11][^4_12][^4_4][^4_5][^4_6][^4_7][^4_8][^4_9]</span>

<div align="center">⁂</div>

[^4_1]: https://stackoverflow.com/questions/11465555/can-we-use-xpath-with-beautifulsoup/11466033

[^4_2]: https://stackoverflow.com/questions/19031030/lxml-equivalent-for-beautifulsoup-find

[^4_3]: https://dev.to/dmitriiweb/beautifulsoup-vs-lxml-a-practical-performance-comparison-1l0a

[^4_4]: https://translate.google.com/?hl=zh-TW\&langpair=zh-TW|zh-CN

[^4_5]: https://apps.microsoft.com/detail/9wzdncrfj3mb?hl=zh-HK\&gl=HK

[^4_6]: https://www.cnblogs.com/Jacck/p/7778819.html

[^4_7]: https://gitcode.csdn.net/69f62d7254b52172bc716fa7.html

[^4_8]: https://blog.csdn.net/zhangdonghuirjdd/article/details/141461493

[^4_9]: https://developer.aliyun.com/article/638532

[^4_10]: https://blog.csdn.net/Dreamy_zsy/article/details/147514616

[^4_11]: https://scrappey.com/qa/python-web-scraping/beautifulsoup-vs-lxml

[^4_12]: https://ithelp.ithome.com.tw/articles/10186119


---

# 如何使用 CSS selector 抓取特定屬性

使用 CSS selector 時，`[屬性]` 是用來**篩選元素**，不是直接回傳屬性值；選到元素後，再用 `.get()` 或 `.attrs` 取得屬性。CSS 屬性選擇器支援存在、完全相等、包含、開頭與結尾等條件。[^5_1][^5_2]

## BeautifulSoup 基本用法

```python
from bs4 import BeautifulSoup

html = """
<div id="main" class="article news" data-category="finance">
    <a href="/news/123" title="市場新聞">查看文章</a>
    <img src="/images/chart.png" alt="市場圖表">
</div>
"""

soup = BeautifulSoup(html, "lxml")
```


### 取得 `href`

```python
links = soup.select("a")

for link in links:
    href = link.get("href")
    print(href)
```

輸出：

```text
/news/123
```

也可以使用字典語法：

```python
href = link["href"]
```

但如果屬性不存在，會產生 `KeyError`：

```python
href = link.get("href")       # 不存在時回傳 None
href = link.get("href", "")   # 不存在時回傳空字串
```


## 使用屬性 selector 篩選

### 只選取具有某個屬性的元素

```python
nodes = soup.select("[href]")
```

等同於：

```python
nodes = soup.select("a[href]")
```

只會取得具有 `href` 屬性的元素。

```python
for node in nodes:
    print(node.get("href"))
```


### 篩選特定屬性值

```python
nodes = soup.select(
    'div[data-category="finance"]'
)
```

也可以寫成：

```python
node = soup.select_one(
    'a[title="市場新聞"]'
)

if node:
    print(node.get("title"))
```


### 多個屬性條件

```python
nodes = soup.select(
    'a[href][title]'
)
```

這會選取同時具有 `href` 與 `title` 的 `<a>` 元素。

```python
nodes = soup.select(
    'a[href^="/news/"][title]'
)
```

這會選取：

- 具有 `href`。
- `href` 以 `/news/` 開頭。
- 具有 `title`。


## 常用屬性選擇器

| CSS selector | 意義 | 範例 |
| :-- | :-- | :-- |
| `[attr]` | 具有屬性 | `a[href]` |
| `[attr="value"]` | 屬性完全相等 | `input[type="text"]` |
| `[attr!="value"]` | 屬性不等於 | `a[href!=""]` |
| `[attr^="value"]` | 以某字串開頭 | `a[href^="https"]` |
| `[attr$="value"]` | 以某字串結尾 | `a[href$=".pdf"]` |
| `[attr*="value"]` | 包含某字串 | `a[href*="example.com"]` |
| `[attr~="value"]` | 空白分隔的值中包含某項 | `div[class~="active"]` |
| `[attr|="value"]` | 等於或以 `value-` 開頭 | `[lang|="zh"]` |

這些是標準 CSS attribute selector 的常見形式。[^5_2]

## 實際範例

### 抓取所有 PDF 連結

```python
pdf_links = soup.select(
    'a[href$=".pdf"]'
)

for link in pdf_links:
    print({
        "title": link.get_text(" ", strip=True),
        "url": link.get("href"),
    })
```


### 抓取所有外部連結

```python
external_links = soup.select(
    'a[href^="http"]'
)

for link in external_links:
    print(link.get("href"))
```


### 抓取含有 `data-url` 的元素

```python
nodes = soup.select("[data-url]")

for node in nodes:
    url = node.get("data-url")
    print(url)
```


### 抓取圖片資訊

```python
images = soup.select("img[src]")

records = []

for image in images:
    records.append({
        "src": image.get("src", ""),
        "alt": image.get("alt", ""),
        "width": image.get("width", ""),
        "height": image.get("height", ""),
    })
```


### 抓取新聞 metadata

```python
og_title = soup.select_one(
    'meta[property="og:title"]'
)

published_time = soup.select_one(
    'meta[property="article:published_time"]'
)

title = og_title.get("content", "") if og_title else ""
published_at = (
    published_time.get("content", "")
    if published_time else ""
)

print(title)
print(published_at)
```

`meta` 標籤通常把資料放在 `content` 屬性，因此應使用 `.get("content")`，而不是 `get_text()`。

## `class` 屬性的處理

HTML 的 `class` 可能有多個值：

```html
<div class="article news featured"></div>
```


### 使用 CSS selector

```python
nodes = soup.select("div.article")
```

```python
nodes = soup.select("div.article.news")
```

`div.article.news` 表示同時具有 `article` 與 `news` 兩個 class。

### 取得完整 class

```python
node = soup.select_one("div.article")

if node:
    classes = node.get("class", [])
    print(classes)
```

輸出：

```python
["article", "news", "featured"]
```

注意：

```python
node.get("class")
```

通常回傳 list；其他一般屬性通常回傳字串。[^5_3]

## 抓取元素與屬性的一次封裝

```python
def extract_attributes(soup, selector, attributes):
    records = []

    for node in soup.select(selector):
        record = {
            "text": node.get_text(" ", strip=True)
        }

        for attr in attributes:
            record[attr] = node.get(attr)

        records.append(record)

    return records


links = extract_attributes(
    soup,
    "a[href]",
    ["href", "title", "target", "rel"]
)

print(links)
```

可能得到：

```python
[
    {
        "text": "查看文章",
        "href": "/news/123",
        "title": "市場新聞",
        "target": None,
        "rel": None
    }
]
```


## lxml 使用 CSS selector

如果你前面已改用 `lxml`，CSS selector 仍然是先取得元素，再呼叫 `.get()`；CSS selector 通常不直接回傳屬性值。[^5_4][^5_5]

```bash
pip install lxml cssselect
```

```python
from lxml import html as lxml_html

tree = lxml_html.fromstring(html)

links = tree.cssselect("a[href]")

for link in links:
    print({
        "text": " ".join(link.itertext()).strip(),
        "href": link.get("href"),
        "title": link.get("title"),
    })
```

使用 `lxml.cssselect.CSSSelector`：

```python
from lxml.cssselect import CSSSelector

selector = CSSSelector(
    'a[href^="https://"]'
)

for node in selector(tree):
    print(node.get("href"))
```

`lxml` 的 CSS selector 也會回傳元素，屬性值仍需用：

```python
node.get("href")
```

若使用 XPath，則可以直接回傳屬性：

```python
hrefs = tree.xpath(
    '//a[@href]/@href'
)
```

這是 XPath 與 CSS selector 在取值方式上的重要差異。

## `::attr()` 的注意事項

以下寫法不要用於 BeautifulSoup：

```python
soup.select("a::attr(href)")
```

BeautifulSoup 的 `select()` 目標是元素，不是直接取出屬性值。正確方式是：

```python
hrefs = [
    node.get("href")
    for node in soup.select("a[href]")
]
```

如果是 `lxml`：

```python
hrefs = tree.xpath(
    '//a[@href]/@href'
)
```


## 適合你的文章擷取流程

```python
article = soup.select_one(
    "article, [itemprop='articleBody'], "
    ".article-content, .article-body, main"
)

if article:
    title_node = soup.select_one(
        'meta[property="og:title"], h1, title'
    )

    time_node = soup.select_one(
        'meta[property="article:published_time"], '
        'time[datetime], time'
    )

    title = (
        title_node.get("content")
        if title_node.name == "meta"
        else title_node.get_text(" ", strip=True)
    ) if title_node else ""

    published_at = (
        time_node.get("content")
        if time_node.name == "meta"
        else time_node.get("datetime")
        or time_node.get_text(" ", strip=True)
    ) if time_node else ""

    body = "\n\n".join(
        p.get_text(" ", strip=True)
        for p in article.select("p")
        if len(p.get_text(" ", strip=True)) >= 15
    )
```

實務上可記住這個模式：

```python
nodes = soup.select("CSS_SELECTOR")  # 找元素
value = node.get("attribute")        # 取屬性
text = node.get_text(strip=True)     # 取文字
```

例如：

```python
for link in soup.select("article a[href]"):
    url = link.get("href")
    text = link.get_text(" ", strip=True)
```

這就是使用 CSS selector 擷取特定 HTML 屬性最穩定、最容易維護的方式。
<span style="display:none">[^5_10][^5_11][^5_12][^5_13][^5_14][^5_15][^5_6][^5_7][^5_8][^5_9]</span>

<div align="center">⁂</div>

[^5_1]: https://web.dev/learn/css/selectors?hl=zh-tw

[^5_2]: https://developer.mozilla.org/zh-TW/docs/Web/CSS/Guides/Selectors

[^5_3]: https://ithelp.ithome.com.tw/articles/10206668

[^5_4]: https://stackoverflow.com/questions/8656707/python-css-selector-to-use-inside-lxml-cssselect

[^5_5]: https://lxml.de/api/lxml.cssselect.CSSSelector-class.html

[^5_6]: https://utrustcorp.com/python-beautifulsoup/

[^5_7]: https://gist.github.com/NEJmark/7a31488cd96fdc155cd8

[^5_8]: https://blog.jiatool.com/posts/sorted-out-css-selector/

[^5_9]: http://yhhuang1966.blogspot.com/2024/04/python-beautifulsoup.html

[^5_10]: https://blog.csdn.net/qq_40910788/article/details/84842951

[^5_11]: https://blog.csdn.net/Winterto1990/article/details/47808949

[^5_12]: https://dev.to/nelson_orina_a538ba52e9ed/mastering-beautifulsoup-parsing-navigating-and-extracting-data-like-a-pro-enl

[^5_13]: https://www.tutorialspoint.com/beautiful_soup/beautiful_soup_find_element_using_css_selectors.htm

[^5_14]: https://webscraping.ai/faq/lxml/how-do-i-extract-attribute-values-from-html-elements-with-lxml

[^5_15]: https://www.learncodewithmike.com/2020/02/python-beautifulsoup-web-scraper.html


---

# PLAYRIGHT

你應該是指 **Playwright**。它可以啟動真正的 Chromium、Firefox 或 WebKit 瀏覽器，等待 JavaScript 執行後，再擷取動態產生的 HTML；這正好補足 `requests + BeautifulSoup` 無法取得 JavaScript 內容的情況。[^6_1][^6_2]

## 安裝 Playwright

```bash
pip install playwright
python -m playwright install chromium
```

Playwright Python 需要另外安裝瀏覽器執行檔；只安裝 Python 套件通常還不夠。[^6_3][^6_1]

## 基本擷取範例

```python
from playwright.sync_api import sync_playwright


url = "https://example.com"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=30_000
    )

    print("標題：", page.title())
    print("網址：", page.url)
    print("正文：", page.locator("body").inner_text())

    browser.close()
```

如果要在除錯時觀察瀏覽器操作，可以設定：

```python
browser = p.chromium.launch(
    headless=False,
    slow_mo=300
)
```

正式批次擷取通常使用 `headless=True`。

## 使用 CSS selector 擷取

Playwright 的 locator 支援 CSS selector：

```python
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    page.goto(
        "https://example.com/article",
        wait_until="networkidle"
    )

    title = page.locator("h1").first.inner_text()

    paragraphs = page.locator(
        "article p"
    ).all_inner_texts()

    links = page.locator(
        "article a[href]"
    ).evaluate_all(
        """elements => elements.map(a => ({
            text: a.innerText.trim(),
            href: a.href,
            title: a.getAttribute('title')
        }))"""
    )

    print(title)
    print(paragraphs)
    print(links)

    browser.close()
```

常用方法：

```python
page.locator("h1").first.inner_text()
page.locator("article").inner_text()
page.locator("article").text_content()
page.locator("a[href]").count()
page.locator("img").all()
page.locator("a").all_inner_texts()
```

`inner_text()` 通常取得畫面上可見的文字；`text_content()` 會取得元素及子元素中的文字，即使部分文字是隱藏的。[^6_4]

## 等待動態內容

不建議只依賴：

```python
import time

time.sleep(5)
```

較好的方式是等待特定元素：

```python
page.goto(url, wait_until="domcontentloaded")

page.locator(
    "article"
).wait_for(
    state="visible",
    timeout=20_000
)

body = page.locator("article").inner_text()
```

等待特定文字：

```python
page.get_by_text("新聞內容").wait_for()
```

等待元素數量：

```python
page.locator("article p").nth(0).wait_for()
```

等待網路回應：

```python
with page.expect_response(
    lambda response: "/api/articles" in response.url
) as response_info:
    page.click("button.load-more")

response = response_info.value
data = response.json()
```

若網站資料是透過 API 載入，直接攔截 API 往往比解析整個畫面更穩定。

## Playwright 搭配 BeautifulSoup

如果你仍然想使用 BeautifulSoup 的清理與解析功能，可以先用 Playwright 取得「執行 JavaScript 後的 HTML」，再交給 BeautifulSoup：

```python
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def fetch_rendered_html(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(
            url,
            wait_until="networkidle",
            timeout=30_000
        )

        # 取得 JavaScript 執行後的 DOM
        rendered_html = page.content()

        browser.close()

    return rendered_html


html = fetch_rendered_html(
    "https://example.com/article"
)

soup = BeautifulSoup(html, "lxml")

title = soup.select_one("h1")
article = soup.select_one(
    "article, .article-content, main"
)

title_text = (
    title.get_text(" ", strip=True)
    if title else ""
)

body = ""

if article:
    paragraphs = [
        p.get_text(" ", strip=True)
        for p in article.select("p")
    ]
    body = "\n\n".join(
        p for p in paragraphs if p
    )

print(title_text)
print(body)
```

適合的架構是：

```text
Playwright
    ↓
等待 JavaScript 完成
    ↓
page.content()
    ↓
BeautifulSoup
    ↓
CSS selector、文字清理、文章分類
```


## 完整新聞擷取範例

```python
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def extract_dynamic_article(url: str) -> dict:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            locale="zh-TW",
            timezone_id="Asia/Taipei",
            viewport={
                "width": 1440,
                "height": 900
            }
        )

        page = context.new_page()

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30_000
        )

        # 優先等待文章區塊
        content_locator = page.locator(
            "article, "
            "[itemprop='articleBody'], "
            ".article-content, "
            ".article-body, "
            "main"
        ).first

        try:
            content_locator.wait_for(
                state="attached",
                timeout=15_000
            )
        except Exception:
            pass

        rendered_html = page.content()
        page_title = page.title()

        context.close()
        browser.close()

    soup = BeautifulSoup(rendered_html, "lxml")

    # 移除不相關區塊
    for tag in soup.select(
        "script, style, noscript, iframe, "
        "nav, footer, aside, form, "
        ".ads, .advertisement, .cookie"
    ):
        tag.decompose()

    title_node = soup.select_one(
        'meta[property="og:title"]'
    )

    if title_node:
        title = title_node.get("content", "")
    else:
        title_node = soup.select_one("h1, title")
        title = (
            title_node.get_text(" ", strip=True)
            if title_node else page_title
        )

    time_node = soup.select_one(
        'meta[property="article:published_time"], '
        'meta[name="date"], '
        'time[datetime], '
        "time"
    )

    if time_node and time_node.name == "meta":
        published_at = time_node.get("content", "")
    elif time_node:
        published_at = (
            time_node.get("datetime")
            or time_node.get_text(" ", strip=True)
        )
    else:
        published_at = ""

    article = soup.select_one(
        "article, "
        "[itemprop='articleBody'], "
        ".article-content, "
        ".article-body, "
        ".post-content, "
        "main"
    )

    paragraphs = []

    if article:
        for node in article.select(
            "p, h2, h3, blockquote"
        ):
            text = clean_text(
                node.get_text(" ", strip=True)
            )

            if len(text) >= 15:
                paragraphs.append(text)

    body = "\n\n".join(
        dict.fromkeys(paragraphs)
    )

    return {
        "url": url,
        "title": clean_text(title),
        "published_at": clean_text(published_at),
        "body": body,
    }


if __name__ == "__main__":
    result = extract_dynamic_article(
        "https://example.com/article"
    )

    print(result["title"])
    print(result["published_at"])
    print(result["body"])
```


## Playwright 與 requests 的選擇

| 情況 | 建議工具 |
| :-- | :-- |
| 靜態 HTML 已包含正文 | `requests + BeautifulSoup` |
| 需要 CSS selector 清理內容 | `BeautifulSoup` |
| 正文由 JavaScript 載入 | `Playwright` |
| 需要點擊「載入更多」 | `Playwright` |
| 需要登入後擷取 | `Playwright`，搭配合法授權 |
| 可以直接呼叫公開 API | `requests` 呼叫 API |
| 需要大量高速批次處理 | 優先研究 API，再考慮 Playwright |
| 需要取得完整渲染後 DOM | `Playwright + page.content()` |

Playwright 的優點是可以模擬使用者操作、等待動態內容並支援多種瀏覽器；但啟動瀏覽器的成本高於 `requests`，因此不應將它用於所有靜態頁面。[^6_5][^6_6]

## 常見問題

### `networkidle` 一直等不到

某些網站會持續發送分析、廣告或即時資料請求，導致 `networkidle` 不穩定。可以改用：

```python
page.goto(
    url,
    wait_until="domcontentloaded"
)

page.locator("article").wait_for(
    state="visible"
)
```


### 元素存在但無法擷取

可能是 iframe 內的內容：

```python
frame = page.frame_locator(
    "iframe"
)

text = frame.locator(
    "article"
).inner_text()
```


### 需要捲動才能載入正文

```python
page.evaluate(
    "window.scrollTo(0, document.body.scrollHeight)"
)

page.wait_for_timeout(1000)
```

但應優先等待實際元素，不要大量使用固定時間等待。

### 需要查看 selector

可以使用 Playwright Codegen：

```bash
python -m playwright codegen https://example.com
```

它可以記錄瀏覽器操作並產生 Python 程式碼，是建立 locator 與除錯 selector 的快速方法。[^6_3]

對你的「新聞 URL → 標題、時間、本文、分類」流程，最實用的配置是：

```text
requests：先處理靜態頁面
Playwright：只處理 JavaScript 動態頁面
BeautifulSoup：清理渲染後 HTML
CSS selector：擷取標題、時間與段落
OpenCC：必要時統一繁簡體
pandas／DuckDB：儲存結構化結果
```

<span style="display:none">[^6_10][^6_11][^6_12][^6_13][^6_14][^6_15][^6_7][^6_8][^6_9]</span>

<div align="center">⁂</div>

[^6_1]: https://thunderbit.com/zh-Hant/blog/playwright-python-tutorial

[^6_2]: https://playwright.tw/docs/intro

[^6_3]: https://easylearnai.com/playwright-python/

[^6_4]: https://developer.aliyun.com/article/1300337

[^6_5]: https://chimapp.com/blogs/playwright-started-1/

[^6_6]: https://www.olostep.com/blog/playwright-web-scraping

[^6_7]: https://learn.microsoft.com/zh-tw/training/modules/build-with-playwright/

[^6_8]: https://learn.microsoft.com/zh-tw/training/modules/build-with-playwright/3-set-up-playwright

[^6_9]: https://www.tpisoftware.com/tpu/articleDetails/3007

[^6_10]: https://playwright.tw/community/learn-videos

[^6_11]: https://hackmd.io/@kY8Wpop3SHWnMmEn8sqGIA/Sy9vEdRtn

[^6_12]: https://leoprocess.github.io/2025/09/07/2025-09-07-playwright-intro/

[^6_13]: https://blog.jiatool.com/posts/playwright/

[^6_14]: https://blog.laiweb.org/posts/playwright-test-1.html

[^6_15]: https://willismax.github.io/my-site/blog/用PlayWright抓取動態網站資料


---

# Playwright 與 Selenium 效能差異比較

一般而言，在**現代 JavaScript 網站、無頭模式與大量 E2E 操作**中，Playwright 通常比 Selenium 快、等待更穩定；但差距不是固定的，會受到瀏覽器、網路、測試流程、並行數、遠端執行環境與等待策略影響。若是靜態頁面爬蟲，`requests + BeautifulSoup/lxml` 通常比兩者都快。

## 核心差異

| 項目 | Playwright | Selenium |
| :-- | :-- | :-- |
| 通訊架構 | 持續連線控制瀏覽器 | WebDriver HTTP；Selenium 4 也逐步支援 BiDi |
| 等待機制 | 內建 auto-wait 與 locator retry | 通常需要明確等待策略 |
| 多瀏覽器 | Chromium、Firefox、WebKit | Chrome、Firefox、Edge、Safari 等 |
| 語言支援 | Python、JavaScript、Java、.NET | Python、Java、C\#、Ruby、JavaScript 等 |
| 啟動方式 | 套件可管理瀏覽器版本 | 通常需管理瀏覽器與 driver 相容性 |
| 速度 | 現代動態網站通常較快 | 等待設計不佳時容易變慢 |
| 穩定性 | locator 與 auto-wait 通常較不易 flaky | `sleep()` 或等待不足時較容易失敗 |
| 既有企業生態 | 較新 | 更成熟、整合範圍較廣 |
| 原生手機 App | 不支援 | 不支援；通常搭配 Appium |

Playwright 的常見優勢來自持續連線、瀏覽器上下文與自動等待；Selenium 的優勢則是長期累積的 WebDriver 生態、語言覆蓋與企業既有投資。[^7_1][^7_2]

## 為什麼 Playwright 常較快

### 1. 自動等待減少重試

Playwright 執行：

```python
page.get_by_role(
    "button",
    name="送出"
).click()
```

它會等待元素達到可操作狀態，例如：

- 元素已存在。
- 元素可見。
- 元素未被其他元素遮蔽。
- 元素已啟用。
- 元素位置穩定。

Selenium 若沒有適當的 explicit wait，常見寫法是：

```python
time.sleep(2)
driver.find_element(
    By.ID,
    "submit"
).click()
```

這會產生兩個問題：

- 頁面早就完成，白白等待。
- 頁面尚未完成，等待時間仍不夠。

較好的 Selenium 寫法是：

```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

button = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable(
        (By.ID, "submit")
    )
)

button.click()
```

所以實際差異往往不只是框架本身，也包括「Playwright 預設提供等待，而 Selenium 需要開發者正確設計等待」。

### 2. Browser Context 適合並行

Playwright 可以在同一個瀏覽器程序中建立多個隔離 context：

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()

    context_1 = browser.new_context()
    context_2 = browser.new_context()

    page_1 = context_1.new_page()
    page_2 = context_2.new_page()

    page_1.goto("https://example.com/user-a")
    page_2.goto("https://example.com/user-b")

    context_1.close()
    context_2.close()
    browser.close()
```

每個 context 可以擁有獨立的 Cookie、local storage、session 與權限，但不必啟動完整的新瀏覽器程序。

## 爬蟲情境的速度排序

對你的「URL → 標題 → 本文 → 分類」工作流，通常可以這樣理解：

```text
requests + lxml
        ↓
requests + BeautifulSoup
        ↓
Playwright
        ↓
Selenium
```

但這不是絕對排名。

### 靜態頁面

```python
import requests
from bs4 import BeautifulSoup

response = requests.get(url, timeout=20)
soup = BeautifulSoup(response.content, "lxml")
```

這通常最快，因為不需要啟動瀏覽器、排版頁面或執行 JavaScript。

### 動態頁面

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, wait_until="domcontentloaded")
    html = page.content()
    browser.close()
```

此時 Playwright 通常比 Selenium 更容易做到：

- 等待指定元素。
- 攔截 API。
- 控制多個 context。
- 進行平行瀏覽。
- 處理無限滾動。

第三方比較通常報告 Playwright 在現代動態網站和無頭執行中較快，但實際數字不應直接套用到你的環境；例如不同網站、網路延遲、瀏覽器版本與 selector 寫法，都可能改變結果。[^7_3][^7_4]

## 建議的 benchmark

不要只測瀏覽器啟動時間，應測量完整工作流程：

```text
啟動瀏覽器
→ 開啟頁面
→ 等待正文
→ 點擊或捲動
→ 取得正文
→ 關閉或重用瀏覽器
```


### Playwright benchmark

```python
import time
from playwright.sync_api import sync_playwright


def benchmark_playwright(url, rounds=5):
    durations = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for _ in range(rounds):
            context = browser.new_context()
            page = context.new_page()

            start = time.perf_counter()

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30_000
            )

            page.locator("body").wait_for(
                state="visible"
            )

            _ = page.locator("body").inner_text()

            durations.append(
                time.perf_counter() - start
            )

            context.close()

        browser.close()

    return durations
```


### Selenium benchmark

```python
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


def benchmark_selenium(url, rounds=5):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)
    durations = []

    try:
        for _ in range(rounds):
            start = time.perf_counter()

            driver.get(url)

            WebDriverWait(driver, 30).until(
                lambda d: d.find_element(
                    By.TAG_NAME,
                    "body"
                )
            )

            _ = driver.find_element(
                By.TAG_NAME,
                "body"
            ).text

            durations.append(
                time.perf_counter() - start
            )

    finally:
        driver.quit()

    return durations
```

比較平均值：

```python
import statistics

playwright_times = benchmark_playwright(url)
selenium_times = benchmark_selenium(url)

print(
    "Playwright 平均：",
    statistics.mean(playwright_times)
)

print(
    "Selenium 平均：",
    statistics.mean(selenium_times)
)
```

更公平的測試應該：

- 使用相同瀏覽器，例如都使用 Chromium。
- 都使用 headless 模式。
- 使用相同網路與機器。
- 使用相同 URL。
- 使用相同等待條件。
- 先執行一次 warm-up，再計算後續結果。
- 測試至少 10 次。
- 分別統計 p50、p95 和錯誤率。
- 將瀏覽器啟動成本與重用瀏覽器的成本分開測量。


## 實務建議

### 選 Playwright

適合：

- 新建 Python 爬蟲或 E2E 測試。
- JavaScript 動態渲染網站。
- 需要點擊、登入、捲動、上傳或下載。
- 需要多個隔離 session。
- 需要平行處理。
- 希望降低因等待不足造成的 flaky。


### 選 Selenium

適合：

- 公司已有完整 Selenium Grid。
- 已有大量 Selenium 測試案例。
- 團隊需要較廣泛的語言或企業工具整合。
- 必須支援特定 WebDriver 生態。
- 遷移成本高於效能收益。


### 不要使用瀏覽器自動化

如果文章內容已存在於 HTML 或公開 API：

```python
requests + lxml XPath
```

通常會比：

```python
Playwright
```

更省 CPU、記憶體與時間。

## 結論

對新專案而言，可以採用以下決策：

```text
正文在原始 HTML？
    ├─ 是 → requests + lxml / BeautifulSoup
    └─ 否 → Playwright
                  ↓
          需要沿用 WebDriver 生態？
              ├─ 是 → Selenium
              └─ 否 → Playwright
```

簡單說：

- **最快的靜態擷取**：`requests + lxml`。
- **現代動態網站自動化**：Playwright。
- **大型既有企業測試平台**：Selenium。
- **不要把「Playwright 快 30% 或 50%」當成固定規則**，應用實際網站與完整工作流程 benchmark；公開比較雖普遍顯示 Playwright 優勢，但不同測試的數字不可直接互相比較。[^7_5][^7_1]
<span style="display:none">[^7_10][^7_6][^7_7][^7_8][^7_9]</span>

<div align="center">⁂</div>

[^7_1]: https://katalon.com/resources-center/blog/playwright-vs-selenium

[^7_2]: https://www.drizz.dev/post/playwright-vs-selenium

[^7_3]: https://www.bright.cn/blog/web-data/playwright-vs-selenium

[^7_4]: https://thunderbit.com/zh-Hant/blog/playwright-vs-selenium

[^7_5]: https://blog.csdn.net/shanwei_spider/article/details/154536530

[^7_6]: https://cloud.tencent.com/developer/article/2601709

[^7_7]: https://blog.csdn.net/xinjichenlibing/article/details/147965372

[^7_8]: https://blog.csdn.net/m0_58552717/article/details/152008926

[^7_9]: https://blog.csdn.net/wx17343624830/article/details/147953677

[^7_10]: https://blog.csdn.net/qq_25894535/article/details/143266683


---

# 什麼情境下 Selenium 的執行速度會超越 Playwright

Selenium 可能超越 Playwright，但通常不是因為單次 DOM 操作本身更快，而是因為**測試情境、等待策略、瀏覽器啟動方式或基礎設施**對總時間的影響更大。公開測試也有簡單腳本中 Selenium 約快 5% 的案例，但這類結果不能泛化到所有網站或工作流程。[^8_1]

## 可能勝出的情境

### 1. 極短腳本且只執行少量操作

例如：

```text
啟動瀏覽器
→ 開啟簡單靜態頁面
→ 找一個元素
→ 讀取文字
→ 結束
```

這種情境中，Playwright 的初始化、Browser Context 建立與自動等待機制可能成為固定成本。若 Selenium 使用已啟動的 WebDriver，總時間可能更短。

```python
# Selenium：重用既有 driver
driver.get(url)
text = driver.find_element(
    By.CSS_SELECTOR,
    "h1"
).text
```

相比之下，若每次都重新建立：

```python
with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context()
    page = context.new_page()
```

短任務的初始化成本會被放大。

**適合比較的指標**：

```text
每次任務總耗時 = 啟動成本 + 導航成本 + 操作成本 + 關閉成本
```

不要只比較單一 `click()` 或 `find_element()`。

### 2. 頁面與元素已經完全就緒

Playwright 的 locator 會進行 actionability checks，例如檢查元素是否可見、可操作、未被遮蔽與位置是否穩定。

如果元素早已存在且可操作，Playwright 的自動等待未必帶來額外收益；Selenium 使用直接查找可能更快：

```python
element = driver.find_element(
    By.CSS_SELECTOR,
    "button.submit"
)
element.click()
```

Playwright：

```python
page.locator(
    "button.submit"
).click()
```

在頁面穩定、沒有動畫、沒有競態條件的簡單測試中，兩者可能非常接近，甚至 Selenium 略快。公開比較也指出，差距會依腳本長度與實際操作而變化，而不是固定由某個框架獲勝。[^8_1]

### 3. Playwright 使用了過於寬鬆或不必要的等待

例如：

```python
page.goto(
    url,
    wait_until="networkidle"
)
```

`networkidle` 可能等待頁面網路活動降到很低；但有些網站會持續執行分析、輪詢或廣告請求，導致額外等待。

Selenium 若只等待目標元素：

```python
driver.get(url)

WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located(
        (By.CSS_SELECTOR, "article")
    )
)
```

反而可能更快。

Playwright 較好的寫法也是等待真正需要的元素：

```python
page.goto(
    url,
    wait_until="domcontentloaded"
)

page.locator("article").wait_for(
    state="visible"
)
```

真正的比較是：

```text
Selenium：精準 explicit wait
Playwright：精準 locator wait
```

而不是：

```text
Selenium：直接操作
Playwright：networkidle + timeout
```


### 4. Selenium 重用既有瀏覽器與 session

如果應用程式讓 Selenium WebDriver 長時間存在，連續執行多個任務：

```python
driver = webdriver.Chrome(
    options=options
)

for url in urls:
    driver.get(url)
    extract_data(driver)

driver.quit()
```

它可能勝過每個 URL 都重新建立 Playwright browser/context 的寫法：

```python
for url in urls:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        browser.close()
```

正確的 Playwright 重用方式應該是：

```python
with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context()
    page = context.new_page()

    for url in urls:
        page.goto(
            url,
            wait_until="domcontentloaded"
        )
        extract_data(page)

    context.close()
    browser.close()
```

如果兩者都正確重用瀏覽器，差距通常會縮小。

### 5. 遠端 Grid 或雲端環境的網路延遲

在 Selenium Grid、Selenoid、BrowserStack 或其他遠端環境中，總耗時可能被以下因素主導：

- 測試執行器到 Grid 的網路延遲。
- Grid 節點排程。
- 瀏覽器容器啟動時間。
- 遠端影片錄製。
- 截圖與 log 傳輸。
- CPU 與記憶體資源競爭。

此時 Playwright 的單次命令優勢可能被網路 RTT 淹沒；一些比較也指出，在雲端或遠端基礎設施中，Playwright 與 Selenium 的速度差距會縮小。[^8_2]

甚至可能出現：

```text
Selenium Grid：已有熱機瀏覽器，立即執行
Playwright：需要等待新 worker 或 browser instance
```

結果 Selenium 的端到端總時間較短。

### 6. Selenium 使用最佳化的 JavaScript 批次操作

如果 Selenium 將多次 DOM 操作合併成一次 JavaScript：

```python
text = driver.execute_script("""
    return Array.from(
        document.querySelectorAll('article p')
    ).map(p => p.innerText).join('\\n\\n');
""")
```

就能減少 Python ↔ WebDriver ↔ 瀏覽器之間的往返次數。

Playwright 也可以做相同最佳化：

```python
text = page.locator(
    "article p"
).evaluate_all("""
    elements => elements
        .map(p => p.innerText)
        .join('\\n\\n')
""")
```

所以這不算 Selenium 的架構性優勢，而是**批次化操作**造成的優勢。

### 7. 只使用 Chrome 且 Selenium 直接搭配 CDP

Selenium 4 可以透過 Chrome DevTools Protocol 執行部分瀏覽器控制工作，例如取得效能資訊或攔截網路事件：

```python
driver.execute_cdp_cmd(
    "Network.enable",
    {}
)
```

若你的工作流完全鎖定 Chromium，且使用大量 CDP 操作，Selenium 可能接近 Playwright，某些短任務甚至更快。

不過這時比較的已經不是純 WebDriver 操作，而是：

```text
Selenium API + CDP
```

對比：

```text
Playwright API + CDP 封裝
```


### 8. 複雜平行處理由既有 Selenium Grid 提供

Playwright 的 browser context 通常很適合本機平行處理，但在企業環境中，Selenium Grid 可能已經具備：

- 預熱節點。
- 瀏覽器池。
- 負載平衡。
- 重試機制。
- 多平台節點。
- 與 CI/CD 整合。
- 測試結果與影片收集。

如果 Selenium Grid 可以立即分派任務，而 Playwright 需要自行建立 worker、容器與瀏覽器，整體 pipeline 可能仍由 Selenium 勝出。

這是**系統層級效能**，不代表 Selenium 單一瀏覽器操作更快。

## 哪些情境通常不會勝出

以下情況 Playwright 通常更有優勢：

- React、Vue、Angular 等 SPA。
- 大量動態元件與非同步請求。
- 多個瀏覽器 context。
- 多頁面平行處理。
- 需要等待網路回應。
- 需要攔截 API。
- 需要大量截圖或下載。
- 需要避免因等待不足造成重跑。
- 新建的現代 E2E 測試套件。

常見基準測試大多顯示 Playwright 在現代動態網站和並行場景較快，但第三方數字受到測試設計影響，不能視為普遍保證。[^8_3][^8_2]

## 公平 benchmark 方法

建議分開測量四種時間：

```text
1. browser startup
2. page navigation
3. element interaction
4. data extraction
```


### Selenium

```python
start = time.perf_counter()

driver.get(url)

WebDriverWait(driver, 20).until(
    EC.presence_of_element_located(
        (By.CSS_SELECTOR, "article")
    )
)

body = driver.find_element(
    By.CSS_SELECTOR,
    "article"
).text

elapsed = time.perf_counter() - start
```


### Playwright

```python
start = time.perf_counter()

page.goto(
    url,
    wait_until="domcontentloaded"
)

page.locator("article").wait_for(
    state="attached",
    timeout=20_000
)

body = page.locator(
    "article"
).inner_text()

elapsed = time.perf_counter() - start
```

測試時固定：

- 相同 Chromium 版本。
- 相同 headless/headed 模式。
- 相同網路。
- 相同 URL。
- 相同 selector。
- 相同等待條件。
- 相同瀏覽器重用策略。
- 相同並行數。
- 排除第一次 warm-up。
- 計算 p50、p95、錯誤率與重試次數。


## 對你的新聞擷取流程

若是：

```text
批次 URL
→ 開啟動態新聞頁
→ 等待 article
→ 擷取 HTML
→ BeautifulSoup 清理
```

建議：

- 靜態頁面：`requests + lxml`。
- 少量動態頁面：Playwright。
- 已有 Selenium Grid：先 benchmark，不要只因 Playwright 理論較快就遷移。
- Selenium：長時間重用 driver，避免每個 URL 啟動一次。
- Playwright：重用 browser，視情況重用 context 或建立隔離 context。
- 不要使用固定 `sleep()` 作為主要等待策略。
- 不要對所有頁面使用 `networkidle`。
- 若正文來自 API，直接擷取 API，通常比兩者都快。

**結論：** Selenium 最可能超越 Playwright 的情境是「短腳本、瀏覽器已熱機、元素已就緒、等待精準、遠端 Grid 已最佳化，或使用 JavaScript/CDP 批次操作」。若是兩者都採用正確等待、相同瀏覽器、相同重用與平行策略，Playwright 通常仍較有利，但實際專案應以完整流程 benchmark 決定，而不是比較單次 `find_element()` 與 `locator()` 的微小差異。
<span style="display:none">[^8_10][^8_4][^8_5][^8_6][^8_7][^8_8][^8_9]</span>

<div align="center">⁂</div>

[^8_1]: https://zhiminzhan.medium.com/playwright-vs-selenium-speed-comparison-3379dd45d3e4

[^8_2]: https://katalon.com/resources-center/blog/playwright-vs-selenium

[^8_3]: https://www.browsercat.com/post/playwright-vs-selenium-deep-comparison

[^8_4]: https://cloud.tencent.com/developer/article/2658500

[^8_5]: https://juejin.cn/post/7156934778246135822

[^8_6]: https://www.scrapeless.com/zh/blog/playwright-vs-selenium

[^8_7]: https://blog.csdn.net/m0_58552717/article/details/152008926

[^8_8]: https://blog.csdn.net/xinjichenlibing/article/details/147965372

[^8_9]: https://blog.csdn.net/shanwei_spider/article/details/154536530

[^8_10]: https://www.drizz.dev/post/playwright-vs-selenium


---

# Playwright 的自動等待機制運作原理

Playwright 的自動等待不是單純 `sleep()`，而是每次執行 locator 動作時，反覆檢查元素是否達到「可操作狀態」；條件成立後立即執行，超過 timeout 才拋出 `TimeoutError`。[^9_1][^9_2]

## 運作流程

以：

```python
page.locator("button.submit").click()
```

為例，Playwright 大致會執行：

```text
解析 locator
    ↓
等待元素出現在 DOM
    ↓
確認只匹配一個元素
    ↓
確認元素可見
    ↓
確認元素位置穩定
    ↓
確認元素能接收滑鼠事件
    ↓
確認元素未被 disabled
    ↓
必要時捲動至可視範圍
    ↓
執行 click
```

如果其中一個條件尚未滿足，Playwright 不會立即失敗，而是等待頁面變化後重新檢查。所有條件通過時就執行，不會固定等待完整 timeout。

## Actionability checks

不同動作需要的檢查不同：


| 動作 | Attached | Visible | Stable | Receives events | Enabled | Editable |
| :-- | --: | --: | --: | --: | --: | --: |
| `click()` | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| `dblclick()` | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| `hover()` | ✓ | ✓ | ✓ | ✓ | — | — |
| `fill()` | ✓ | ✓ | — | — | ✓ | ✓ |
| `check()` | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| `screenshot()` | ✓ | ✓ | ✓ | — | — | — |
| `select_text()` | ✓ | ✓ | — | — | — | — |
| `dispatch_event()` | ✓ | — | — | — | — | — |

例如 `fill()` 需要輸入框可見、啟用且可編輯，但不需要檢查它是否穩定或能接收滑鼠事件。[^9_1]

## 各項檢查的意義

### Attached

確認 locator 找到的元素仍存在於 DOM：

```html
<input id="email">
```

如果 React 或 Vue 重新渲染，舊元素可能被移除並建立新元素。Playwright 的 locator 會重新解析，而不是永遠使用第一次找到的節點。

### Exactly one element

對需要單一目標的操作，Playwright 會要求 locator 嚴格匹配一個元素：

```python
page.locator("button").click()
```

如果頁面有三個 `button`，可能得到 strict mode violation。應改用更精確的定位：

```python
page.get_by_role(
    "button",
    name="送出"
).click()
```

或：

```python
page.locator(
    "form#login button[type='submit']"
).click()
```

這可以避免「實際點到錯誤按鈕」的問題。

### Visible

元素必須具備可見的 layout box，且不能是：

```css
display: none;
visibility: hidden;
```

以下元素通常不符合可見條件：

```html
<button style="display:none">送出</button>
```

或：

```html
<div style="width:0;height:0">內容</div>
```

Playwright 官方說明中，可見性主要與非空的 bounding box 及 `visibility` 計算樣式有關。[^9_1]

### Stable

元素不能正在移動或動畫中。例如：

```css
button {
    transition: transform 1s;
}
```

Playwright 會確認元素的 bounding box 在至少兩個連續動畫 frame 中維持不變，才認定它穩定。[^9_1]

### Receives events

即使元素看起來可見，也可能被其他元素覆蓋：

```html
<div class="modal-overlay"></div>
<button id="submit">送出</button>
```

如果 overlay 擋在按鈕上，實際滑鼠事件不會送到按鈕，Playwright 會等待遮罩消失，而不是盲目執行點擊。

### Enabled

表單元素不能是 disabled：

```html
<button disabled>送出</button>
```

Playwright 會等待：

```html
<button>送出</button>
```

或直接在 timeout 後失敗。

## 與 locator 的關係

Locator 是「延遲解析、可重試的元素描述」，不是一次性取得的 WebElement：

```python
button = page.locator("button.submit")
```

這行通常不會立刻要求元素存在。真正執行以下操作時才會進行查找與 actionability checks：

```python
button.click()
button.inner_text()
button.is_visible()
```

例如：

```python
button = page.get_by_role(
    "button",
    name="載入資料"
)

page.locator("#result").wait_for(
    state="visible"
)

button.click()
```

如果按鈕稍後才由 JavaScript 建立，locator 可以等到它出現。這也是 Playwright 比傳統「先找元素、再操作元素」寫法更能處理 DOM 變動的原因。

## 斷言也會自動重試

Playwright 的 assertion 不只是立即比較一次：

```python
from playwright.sync_api import expect

expect(
    page.locator("#status")
).to_have_text("完成")
```

它會在 timeout 內反覆檢查，直到文字符合預期：

```text
目前文字：載入中
    ↓
目前文字：處理中
    ↓
目前文字：完成
    ↓
assertion 通過
```

這比固定等待更穩定：

```python
# 不建議
page.wait_for_timeout(3000)

assert page.locator(
    "#status"
).inner_text() == "完成"
```

官方文件也建議使用會自動等待的斷言，以減少競態條件與 flaky tests。[^9_3]

## 三種等待要分清楚

### 1. 動作自動等待

```python
page.get_by_role(
    "button",
    name="登入"
).click()
```

等待按鈕可操作。

### 2. 元素狀態等待

```python
page.locator(
    "article"
).wait_for(
    state="visible"
)
```

`wait_for()` 可等待：

```python
state="attached"   # 存在於 DOM
state="detached"   # 從 DOM 移除
state="visible"    # 可見
state="hidden"     # 隱藏或移除
```


### 3. 業務條件等待

```python
expect(
    page.locator(".result-count")
).to_have_text("100")
```

等待實際業務結果，而不是只等待一個空容器出現。

## 不會自動等待所有事情

Playwright 的自動等待主要針對 locator 動作與 assertion，不代表它會自動理解你的所有業務流程。

例如：

```python
page.get_by_role(
    "button",
    name="送出"
).click()

# 不一定代表 API 已完成或資料已顯示
print(page.locator("#result").inner_text())
```

如果按鈕點擊後會發送 API，應等待回應或結果：

```python
with page.expect_response(
    lambda response: (
        "/api/articles" in response.url
        and response.request.method == "POST"
    )
):
    page.get_by_role(
        "button",
        name="送出"
    ).click()

expect(
    page.locator("#result")
).to_contain_text("成功")
```

如果是頁面導航：

```python
with page.expect_navigation():
    page.get_by_role(
        "link",
        name="下一頁"
    ).click()
```

現代 Playwright 程式通常會優先等待「可觀察的結果」，而不是等待固定秒數。

## Timeout 如何運作

可以設定全域 timeout：

```python
context = browser.new_context()

context.set_default_timeout(10_000)
```

或針對單一操作設定：

```python
page.locator(
    "article"
).wait_for(
    state="visible",
    timeout=15_000
)
```

單次動作：

```python
page.get_by_role(
    "button",
    name="送出"
).click(
    timeout=10_000
)
```

測試 assertion 也可設定 timeout：

```python
expect(
    page.locator("#status")
).to_have_text(
    "完成",
    timeout=15_000
)
```

請不要把「30 秒」視為所有 Python Playwright API 的固定預設值；實際預設值會依 API、語言 binding 與 Playwright Test 設定而不同。重要的是理解：**等待條件若在指定 timeout 內不成立，就會失敗**。[^9_1]

## `force=True` 的風險

可以強制忽略部分 actionability checks：

```python
page.locator(
    "button.submit"
).click(force=True)
```

但這可能造成：

- 點到被遮蔽的元素。
- 點擊沒有產生實際使用者效果。
- 測試通過但真實使用者無法操作。
- 隱藏元件被錯誤觸發。

因此 `force=True` 適合少數已確認安全的情境，不應作為解決 locator 或等待問題的第一選擇。

## 對動態新聞擷取的應用

你的新聞擷取流程可以這樣設計：

```python
page.goto(
    url,
    wait_until="domcontentloaded"
)

article = page.locator(
    "article, "
    "[itemprop='articleBody'], "
    ".article-content, "
    ".article-body"
).first

article.wait_for(
    state="visible",
    timeout=15_000
)

paragraphs = article.locator(
    "p"
).all_inner_texts()
```

如果正文是由 API 載入，應等待實際正文，而不是使用：

```python
page.wait_for_timeout(5000)
```

可以改成：

```python
expect(article).to_contain_text(
    "新聞",
    timeout=15_000
)
```

或：

```python
page.wait_for_response(
    lambda response: "/api/news" in response.url
)
```


## 核心結論

Playwright 自動等待的核心是：

```text
Locator 延遲解析
+ 動作前 actionability checks
+ 條件未滿足時自動重試
+ assertion 自動重試
+ timeout 後明確失敗
```

它不是「等待固定時間」，而是「等待指定條件成立」。因此最佳實務是使用精確 locator、等待實際結果、使用 `expect()` 斷言，並避免以 `sleep()` 或 `wait_for_timeout()` 取代真正的同步條件。
<span style="display:none">[^9_10][^9_4][^9_5][^9_6][^9_7][^9_8][^9_9]</span>

<div align="center">⁂</div>

[^9_1]: https://playwright.dev/docs/actionability

[^9_2]: https://playwright.tw/docs/actionability

[^9_3]: https://playwright.tw/docs/writing-tests

[^9_4]: https://cloud.tencent.com/developer/article/2545220

[^9_5]: https://cloud.tencent.com/developer/article/2555168

[^9_6]: https://chimapp.com/blogs/playwright-advanced-1/

[^9_7]: https://playwright.dev.org.tw/java/docs/actionability

[^9_8]: https://www.cnblogs.com/hogwarts/p/19371630

[^9_9]: https://blog.csdn.net/qq_23827149/article/details/135282209

[^9_10]: https://blog.csdn.net/m0_59235945/article/details/147285726


---

# 如何識別HTML各區塊

識別 HTML 各區塊，建議依序使用：

```text
語意標籤
→ id／class
→ DOM 層級關係
→ data-* 與結構化資料
→ 文字密度與連結比例
→ Playwright 實際渲染後檢查
```

HTML5 的 `<main>` 通常代表頁面的主要內容，`<article>` 適合表示可獨立閱讀的文章，`<aside>` 則代表與主內容相關但可分離的補充區域。[^10_1]

## 1. 先看語意化標籤

常見頁面結構：

```html
<body>
    <header>
        <nav>網站導覽</nav>
    </header>

    <main>
        <article>
            <header>
                <h1>文章標題</h1>
                <time datetime="2026-08-12">
                    2026-08-12
                </time>
            </header>

            <section class="article-content">
                <p>第一段文章內容。</p>
                <p>第二段文章內容。</p>
            </section>
        </article>

        <aside>
            推薦文章
        </aside>
    </main>

    <footer>
        網站資訊
    </footer>
</body>
```

常見語意標籤：


| 標籤 | 常見用途 |
| :-- | :-- |
| `<header>` | 網站或區塊的頁首 |
| `<nav>` | 導覽連結 |
| `<main>` | 頁面的主要內容 |
| `<article>` | 可獨立閱讀的文章、新聞或貼文 |
| `<section>` | 主題相關的內容區段 |
| `<aside>` | 側欄、推薦、補充內容 |
| `<footer>` | 網站或區塊的頁尾 |
| `<h1>`～`<h6>` | 標題層級 |
| `<p>` | 文字段落 |
| `<figure>` | 圖片、圖表或其他獨立媒體 |

W3C 建議使用 `<main>` 識別頁面的主要內容區域，並使用 `<aside>` 表示與主內容分離但具有意義的輔助區塊。[^10_1]

## 2. 使用 BeautifulSoup 檢查區塊

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, "lxml")

for tag in soup.select(
    "header, nav, main, article, section, aside, footer"
):
    print(
        tag.name,
        tag.get("id"),
        tag.get("class"),
        tag.get_text(" ", strip=True)[:100]
    )
```

輸出可能是：

```text
header None ['site-header'] 網站名稱 導覽
nav main-nav ['menu'] 首頁 財經 科技
main main-content ['container'] 文章內容 推薦文章
article article-123 ['news-article'] 文章標題 第一段內容...
aside sidebar ['related-news'] 相關新聞
footer None ['site-footer'] 聯絡方式 著作權
```

這可以快速了解：

- 哪些語意標籤存在。
- `id` 是什麼。
- `class` 有哪些值。
- 每個區塊包含哪些文字。


## 3. 依 `id` 與 `class` 識別

現實網站常用大量 `<div>`，因此不能只依賴語意標籤：

```html
<div id="main-content">
    <div class="article-body news-content">
        <p>新聞內容。</p>
    </div>
</div>
```

可以使用：

```python
main = soup.select_one("#main-content")

article = soup.select_one(
    ".article-body, .news-content"
)
```

或：

```python
article = soup.find(
    "div",
    class_="article-body"
)
```

常見 class 名稱：

```python
CONTENT_SELECTORS = [
    "article",
    "[itemprop='articleBody']",
    "#article-body",
    "#main-content",
    ".article-body",
    ".article-content",
    ".news-content",
    ".post-content",
    ".entry-content",
    ".story-body",
    "main",
]
```

依序嘗試：

```python
def first_match(soup, selectors):
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            return node
    return None


article = first_match(
    soup,
    CONTENT_SELECTORS
)
```


## 4. 觀察 DOM 層級關係

有時 class 名稱很普通，但 DOM 結構很有規律：

```html
<main>
    <div class="layout">
        <div class="left-column">
            <article>
                ...
            </article>
        </div>

        <div class="right-column">
            ...
        </div>
    </div>
</main>
```

可以使用 CSS selector：

```python
article = soup.select_one(
    "main .left-column article"
)
```

或使用 XPath：

```python
from lxml import html as lxml_html

tree = lxml_html.fromstring(html_content)

article = tree.xpath(
    "//main//div[contains(@class, 'left-column')]//article"
)
```

常見關係：

```python
soup.select("main article")       # main 後代的 article
soup.select("main > article")     # main 直接子元素 article
soup.select("article > p")        # article 直接子元素 p
soup.select("article h1")         # article 內的 h1
soup.select("h1 + time")          # h1 後面緊鄰的 time
```


## 5. 使用結構化資料識別區塊

新聞網站可能使用 Schema.org：

```html
<article
    itemscope
    itemtype="https://schema.org/NewsArticle">

    <h1 itemprop="headline">
        文章標題
    </h1>

    <time
        itemprop="datePublished"
        datetime="2026-08-12T18:30:00+08:00">
    </time>

    <div itemprop="articleBody">
        文章正文。
    </div>
</article>
```

擷取方式：

```python
title_node = soup.select_one(
    '[itemprop="headline"]'
)

date_node = soup.select_one(
    '[itemprop="datePublished"]'
)

body_node = soup.select_one(
    '[itemprop="articleBody"]'
)

title = (
    title_node.get_text(" ", strip=True)
    if title_node else ""
)

published_at = (
    date_node.get("datetime")
    if date_node and date_node.name == "time"
    else ""
)

body = (
    body_node.get_text("\n", strip=True)
    if body_node else ""
)
```

也要檢查 JSON-LD：

```python
import json

for script in soup.select(
    'script[type="application/ld+json"]'
):
    try:
        data = json.loads(
            script.string or script.get_text()
        )

        if isinstance(data, dict):
            print(data.get("@type"))
            print(data.get("headline"))
            print(data.get("datePublished"))
    except json.JSONDecodeError:
        continue
```

新聞頁面可能使用：

```text
NewsArticle
Article
BlogPosting
WebPage
```

使用 JSON-LD 能補足 HTML 中沒有明確標記的標題、日期、作者與媒體資訊。

## 6. 用文字密度判斷正文

當網站只有大量 `<div>`，可以用一些啟發式指標判斷文章區塊：

- 文字總長度較長。
- `<p>` 數量較多。
- 文字與 HTML 標籤比例較高。
- `<a>` 連結比例較低。
- 內含 `<h1>` 或文章時間。
- 位於 `<main>` 或主要欄位。
- 不含大量 `nav`、`button`、`share`、`comment` 等元素。

簡單評分範例：

```python
def score_block(node):
    text = node.get_text(" ", strip=True)
    paragraphs = node.select("p")
    links = node.select("a")
    buttons = node.select("button")

    text_length = len(text)
    paragraph_score = len(paragraphs) * 100
    link_penalty = len(links) * 30
    button_penalty = len(buttons) * 50

    return (
        text_length
        + paragraph_score
        - link_penalty
        - button_penalty
    )


candidates = soup.select(
    "article, main, section, div"
)

ranked = sorted(
    candidates,
    key=score_block,
    reverse=True
)

best_block = ranked[^10_0] if ranked else None
```

這不是絕對正確的文章抽取演算法，但在沒有固定 class 的網站上，可以作為 fallback。

## 7. 排除不相關區塊

找到正文後，應先移除無關元素：

```python
article = soup.select_one(
    "article, .article-content, main"
)

if article:
    for tag in article.select(
        "script, style, noscript, iframe, "
        "nav, aside, footer, form, "
        ".ad, .ads, .advertisement, "
        ".share, .social, .comments, "
        ".related, .recommend"
    ):
        tag.decompose()
```

接著只讀取段落：

```python
paragraphs = []

if article:
    for node in article.select(
        "p, h2, h3, blockquote"
    ):
        text = node.get_text(" ", strip=True)

        if len(text) >= 15:
            paragraphs.append(text)

body = "\n\n".join(
    dict.fromkeys(paragraphs)
)
```


## 8. 用 Playwright 檢查實際區塊

如果內容是 JavaScript 動態載入，先用 Playwright 取得渲染後 HTML：

```python
from playwright.sync_api import sync_playwright


def get_rendered_html(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True
        )
        page = browser.new_page()

        page.goto(
            url,
            wait_until="domcontentloaded"
        )

        page.locator("body").wait_for(
            state="visible"
        )

        html = page.content()

        browser.close()

    return html
```

也可以列出頁面主要區塊：

```python
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    page.goto(url)

    for selector in [
        "header",
        "nav",
        "main",
        "article",
        "section",
        "aside",
        "footer"
    ]:
        count = page.locator(selector).count()
        print(selector, count)

    browser.close()
```

如果不知道某個區塊的 selector，可以使用：

```bash
python -m playwright codegen https://example.com
```

或在瀏覽器開發者工具中使用：

```text
F12 → Elements → 選取元素 → Copy selector
```

但自動產生的 selector 可能含有動態 class 或很長的 DOM 路徑，正式程式應改成較穩定的：

```python
page.get_by_role("article")
page.locator("[itemprop='articleBody']")
page.locator("main article")
```


## 9. 建立可重用的區塊識別器

```python
from dataclasses import dataclass


@dataclass
class PageRegions:
    header: object | None
    navigation: object | None
    main: object | None
    article: object | None
    sidebar: object | None
    footer: object | None


def identify_regions(soup):
    return PageRegions(
        header=soup.select_one("header"),
        navigation=soup.select_one("nav"),
        main=soup.select_one("main"),
        article=soup.select_one("article"),
        sidebar=soup.select_one("aside"),
        footer=soup.select_one("footer"),
    )
```

對新聞網站可增加 fallback：

```python
def identify_article(soup):
    selectors = [
        "article",
        "[itemprop='articleBody']",
        ".article-content",
        ".article-body",
        ".news-content",
        ".story-body",
        "main",
    ]

    for selector in selectors:
        node = soup.select_one(selector)

        if node and len(
            node.get_text(" ", strip=True)
        ) >= 200:
            return node

    return None
```


## 實務判斷順序

對「擷取新聞媒體、時間、標題、本文」的工作流，推薦順序如下：

```text
1. 找 <article>
2. 找 [itemprop="articleBody"]
3. 找 <main>
4. 找 og:title、h1、title
5. 找 article:published_time、datePublished、time
6. 找 article-body、article-content 等 class
7. 清除 nav、aside、footer、廣告、留言
8. 只保留 p、h2、h3、blockquote
9. 以正文長度與段落數做品質檢查
10. 對低品質結果使用文字密度 fallback
```

重點是不要只用：

```python
soup.get_text()
```

因為它會把導覽列、廣告、推薦文章、留言與頁尾全部混在一起。應先識別主要區塊，再從該區塊內擷取正文。 HTML 語意標籤有助於區分頁面角色，但實際網站仍常混用 `<div>`，所以應結合語意標籤、`id`／`class`、結構化資料與 DOM 層級判斷。
<span style="display:none">[^10_10][^10_11][^10_12][^10_13][^10_14][^10_15][^10_2][^10_3][^10_4][^10_5][^10_6][^10_7][^10_8][^10_9]</span>

<div align="center">⁂</div>

[^10_1]: https://www.w3.org/WAI/tutorials/page-structure/regions/

[^10_2]: https://ithelp.ithome.com.tw/articles/10299473

[^10_3]: https://www.opentech.com.tw/try/5uds220181214024831/if8le9hpdc20181214024831.pdf

[^10_4]: https://vocus.cc/article/6861fac8fd89780001d8a5cc

[^10_5]: https://medium.com/@cookie1996/html-簡介及基本架構-1283d130c419

[^10_6]: https://www.ileo.com.tw/school-detail/html-basics-tags-structure-web-principles/

[^10_7]: https://ithelp.ithome.com.tw/articles/10344005?sc=rss.qu

[^10_8]: https://hackmd.io/@training-camp/BJzoUvGV-e

[^10_9]: https://realnewbie.com/coding/html/html5-block-elements/

[^10_10]: https://progressbar.tw/posts/204

[^10_11]: https://cc3.ocu.edu.tw/wu/web/20_html.html

[^10_12]: https://ithelp.ithome.com.tw/articles/10326717\&rut=e3c4bf3c9d22deb925ea6936922ce3da6e9a9e38695404128e2005ce302e449f

[^10_13]: https://zoego.tech/page/web2-3.html

[^10_14]: https://selflearningsuccess.com/html-tags/

[^10_15]: https://miahsuwork.medium.com/第六週-api-基礎-html-tag-基本標籤認識-d2d9a1c66449

