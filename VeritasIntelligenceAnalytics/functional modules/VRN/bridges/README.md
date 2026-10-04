# VIA 自備接頭(lib.lopdf · lib.itext)

座位制插件的工作站接頭源碼;容器已實測端到端 6/6(直跑 rc0 · 壞檔 rc1 · 經插件+有界 runner
EXTRACTED_UNVERIFIED)。建置產物(target/、*.jar)不入倉,工作站自建。

## lopdf_cli(Rust · MIT)
```powershell
cd ".\functional modules\VRN\bridges\lopdf_cli"
cargo build --release          # 需 rustup;產物 target\release\lopdf_cli.exe
```
契約:`lopdf_cli <pdf>` → stdout 一行 JSON(pdf_version/page_count/object_count/encrypted/pages);
錯誤 stderr + rc 1。唯讀不改檔。

## itext_cli(Java · iText 7 Core,AGPL 授權註記:僅本機免費使用,不接付費雲服務)
```powershell
cd ".\functional modules\VRN\bridges\itext_cli"
mvn package                    # 需 JDK 11+ 與 Maven;產物 target\itext-cli.jar(fat jar)
```
契約:`java -jar itext-cli.jar <pdf>` → stdout 逐頁文字;錯誤 stderr + rc 1。

## 掛進插件(宿主 config)
```python
config = {"binary_paths": {
    "lopdf_cli": r"...\bridges\lopdf_cli\target\release\lopdf_cli.exe",
    "itext_cli": r"...\bridges\itext_cli\target\itext-cli.jar",
    "java": r"java",   # PATH 有則免
}}
plugins["lib.lopdf"]["call"]("objects", pdf, work, config=config, run_cli=有界runner)
plugins["lib.itext"]["call"]("text",    pdf, work, config=config, run_cli=有界runner)
```
建置驗證通過後,名冊 `VIA_LayoutPlugins_Registry` 尾版可把兩席 validation 由
BRIDGE_SEAT_PENDING_OPERATOR 轉實測狀態(出新尾版,不就地改)。
