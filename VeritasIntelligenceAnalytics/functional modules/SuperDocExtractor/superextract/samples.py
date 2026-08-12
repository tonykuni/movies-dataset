"""Sample-file factory for the selftest.

Builds pathological-but-valid files BY HAND (raw OOXML zips, raw CSV bytes)
so the selftest exercises the extractor against exactly the failure modes
documented in the README — merged cells, tracked changes, nested tables,
Big5/mojibake encodings, ragged rows — without needing any writer library.
"""
from __future__ import annotations

import os
import zipfile

# ------------------------------------------------------------------ docx

_CONTENT_TYPES_DOCX = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>
</Types>"""

_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

_DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>
</Relationships>"""

_HEADER_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p><w:r><w:t>機密文件頁首 Confidential Header</w:t></w:r></w:p>
</w:hdr>"""


def _p(text: str) -> str:
    return f"<w:p><w:r><w:t xml:space=\"preserve\">{text}</w:t></w:r></w:p>"


def _tc(text: str, *, span: int = 0, vmerge: str = "") -> str:
    props = ""
    if span or vmerge:
        parts = ""
        if span:
            parts += f'<w:gridSpan w:val="{span}"/>'
        if vmerge == "restart":
            parts += '<w:vMerge w:val="restart"/>'
        elif vmerge == "continue":
            parts += "<w:vMerge/>"
        props = f"<w:tcPr>{parts}</w:tcPr>"
    return f"<w:tc>{props}{_p(text)}</w:tc>"


def _docx_body_v1() -> str:
    """Old version: tracked changes, invisible chars, merged-cell table,
    nested table, layout table."""
    nested = ("<w:tbl><w:tr>" + _tc("內層A") + _tc("內層B") + "</w:tr>"
              "<w:tr>" + _tc("內層C") + _tc("內層D") + "</w:tr></w:tbl>")
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>
  {_p("合約標題：採購協議書")}
  {_p("甲方：範例&#8203;科技&#160;股份有限公司")}
  <w:p>
    <w:r><w:t xml:space="preserve">本合約自民國115年1月1日起生效</w:t></w:r>
    <w:del w:id="1" w:author="reviewer"><w:r><w:delText>，舊條款已刪除</w:delText></w:r></w:del>
    <w:ins w:id="2" w:author="reviewer"><w:r><w:t>，並新增保密條款</w:t></w:r></w:ins>
  </w:p>
  <w:tbl>
    <w:tr>{_tc("類別")}{_tc("品名")}{_tc("數量")}{_tc("單價")}</w:tr>
    <w:tr>{_tc("3C設備", vmerge="restart")}{_tc("筆記型電腦")}{_tc("１０")}{_tc("30,000")}</w:tr>
    <w:tr>{_tc("", vmerge="continue")}{_tc("螢幕")}{_tc("20")}{_tc("5,000")}</w:tr>
    <w:tr>{_tc("備註", span=2)}{_tc("")}{_tc("含保固")}</w:tr>
  </w:tbl>
  {_p("下方為含巢狀表格的第二張表")}
  <w:tbl>
    <w:tr>{_tc("外層1")}<w:tc>{nested}{_p("外層2的說明")}</w:tc></w:tr>
    <w:tr>{_tc("外層3")}{_tc("外層4")}</w:tr>
  </w:tbl>
  <w:tbl>
    <w:tr>{_tc("簽名：________")}</w:tr>
  </w:tbl>
  <w:sectPr/>
</w:body>
</w:document>"""


def _docx_body_v2() -> str:
    """New version: one price changed, one row added, one paragraph edited."""
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>
  {_p("合約標題：採購協議書")}
  {_p("甲方：範例科技股份有限公司")}
  {_p("本合約自民國115年3月1日起生效，並新增保密條款")}
  <w:tbl>
    <w:tr>{_tc("類別")}{_tc("品名")}{_tc("數量")}{_tc("單價")}</w:tr>
    <w:tr>{_tc("3C設備", vmerge="restart")}{_tc("筆記型電腦")}{_tc("10")}{_tc("32,000")}</w:tr>
    <w:tr>{_tc("", vmerge="continue")}{_tc("螢幕")}{_tc("20")}{_tc("5,000")}</w:tr>
    <w:tr>{_tc("", vmerge="continue")}{_tc("鍵盤")}{_tc("50")}{_tc("800")}</w:tr>
    <w:tr>{_tc("備註", span=2)}{_tc("")}{_tc("含保固")}</w:tr>
  </w:tbl>
  <w:sectPr/>
</w:body>
</w:document>"""


def write_docx(path: str, body_xml: str, with_header: bool = True) -> str:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _CONTENT_TYPES_DOCX)
        zf.writestr("_rels/.rels", _RELS)
        zf.writestr("word/document.xml", body_xml)
        if with_header:
            zf.writestr("word/_rels/document.xml.rels", _DOC_RELS)
            zf.writestr("word/header1.xml", _HEADER_XML)
    return path


# ------------------------------------------------------------------ xlsx

_CONTENT_TYPES_XLSX = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>"""

_XLSX_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

_WORKBOOK = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="訂單" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""

_WORKBOOK_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

#: style 0 = general, style 1 = built-in date format 14 (m/d/yyyy)
_STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>
  <fills count="1"><fill><patternFill patternType="none"/></fill></fills>
  <borders count="1"><border/></borders>
  <cellStyleXfs count="1"><xf numFmtId="0"/></cellStyleXfs>
  <cellXfs count="2">
    <xf numFmtId="0" xfId="0" applyNumberFormat="0"/>
    <xf numFmtId="14" xfId="0" applyNumberFormat="1"/>
  </cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>"""

_SHARED_STRINGS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="8" uniqueCount="8">
  <si><t>員工編號</t></si>
  <si><t>姓名</t></si>
  <si><t>到職日</t></si>
  <si><t>薪資</t></si>
  <si><t>部門</t></si>
  <si><t>00123</t></si>
  <si><t>王小明</t></si>
  <si><t>研發部</t></si>
</sst>"""

# A1:E1 header; row2: 00123 (shared string keeps leading zeros), 王小明,
# date serial 45108 (2023-07-01) with date style, formula with cached 52000,
# 研發部 anchored in a A3:A4 vertical merge (D3 deliberately left empty).
_SHEET1 = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row r="1">
      <c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c>
      <c r="C1" t="s"><v>2</v></c><c r="D1" t="s"><v>3</v></c>
      <c r="E1" t="s"><v>4</v></c>
    </row>
    <row r="2">
      <c r="A2" t="s"><v>5</v></c><c r="B2" t="s"><v>6</v></c>
      <c r="C2" s="1"><v>45108</v></c>
      <c r="D2"><f>50000+2000</f><v>52000</v></c>
      <c r="E2" t="s"><v>7</v></c>
    </row>
    <row r="3">
      <c r="A3" t="inlineStr"><is><t>00456</t></is></c>
      <c r="B3" t="inlineStr"><is><t>李美麗</t></is></c>
      <c r="C3" s="1"><v>45474</v></c>
      <c r="E3" t="s"><v>7</v></c>
    </row>
    <row r="4">
      <c r="A4" t="inlineStr"><is><t>00789</t></is></c>
      <c r="B4" t="inlineStr"><is><t>陳大文</t></is></c>
      <c r="C4" s="1"><v>45108</v></c>
      <c r="D4"><v>48000</v></c>
      <c r="E4" t="inlineStr"><is><t xml:space="preserve"> 業務部 </t></is></c>
    </row>
  </sheetData>
  <mergeCells count="1"><mergeCell ref="E2:E3"/></mergeCells>
</worksheet>"""


def write_xlsx(path: str) -> str:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _CONTENT_TYPES_XLSX)
        zf.writestr("_rels/.rels", _XLSX_RELS)
        zf.writestr("xl/workbook.xml", _WORKBOOK)
        zf.writestr("xl/_rels/workbook.xml.rels", _WORKBOOK_RELS)
        zf.writestr("xl/styles.xml", _STYLES)
        zf.writestr("xl/sharedStrings.xml", _SHARED_STRINGS)
        zf.writestr("xl/worksheets/sheet1.xml", _SHEET1)
    return path


# ------------------------------------------------------------------ csv

def write_csvs(outdir: str) -> dict:
    """Write the encoding/structure trap set. Returns {label: path}."""
    paths = {}

    p = os.path.join(outdir, "big5_orders.csv")
    rows = ("產品編號,產品名稱,地區,金額\n"
            "A001,筆記型電腦,\"台北市, 台灣\",30000\n"
            "A002,無線滑鼠,高雄市,650\n")
    with open(p, "wb") as fh:
        fh.write(rows.encode("cp950"))
    paths["big5"] = p

    p = os.path.join(outdir, "utf8_bom.csv")
    with open(p, "wb") as fh:
        fh.write("\ufeffid,name\n1,測試\n".encode("utf-8"))
    paths["bom"] = p

    p = os.path.join(outdir, "mojibake.csv")
    good = "編號,城市\n1,台北\n2,高雄\n"
    # classic double-encoding: utf-8 bytes mis-read as latin-1, saved as utf-8
    with open(p, "wb") as fh:
        fh.write(good.encode("utf-8").decode("latin-1").encode("utf-8"))
    paths["mojibake"] = p

    p = os.path.join(outdir, "ragged.csv")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("a,b,c\n1,2,3\n4,5\n6,7,8,9\n,,\n")
    paths["ragged"] = p

    p = os.path.join(outdir, "semicolon.csv")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("id;name;total\n1;alpha;100\n2;beta;200\n")
    paths["semicolon"] = p

    return paths


def build_all(outdir: str) -> dict:
    """Generate every sample into *outdir*. Returns {label: path}."""
    os.makedirs(outdir, exist_ok=True)
    paths = {
        "docx_v1": write_docx(os.path.join(outdir, "contract_v1.docx"), _docx_body_v1()),
        "docx_v2": write_docx(os.path.join(outdir, "contract_v2.docx"), _docx_body_v2(),
                              with_header=False),
        "xlsx": write_xlsx(os.path.join(outdir, "employees.xlsx")),
    }
    paths.update(write_csvs(outdir))
    # a fake docx: OLE2 signature behind a .docx extension
    fake = os.path.join(outdir, "fake_legacy.docx")
    with open(fake, "wb") as fh:
        fh.write(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 64)
    paths["fake_docx"] = fake
    return paths
