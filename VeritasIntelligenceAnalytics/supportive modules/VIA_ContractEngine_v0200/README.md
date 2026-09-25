# VIA Contract Interface Engine v0.2.0

這是 VIA 的第二階段「智慧化 Interface + Central SSOT Registry」參考引擎，將模組契約、依賴注入、不可變 URN、DAG 相依解析、健康度、Metrics、安全 Watchdog、Command Schema、HTML U/I 與數位雙生測試統一到同一個治理中樞。

## def 01 已實作能力

- `VIAModuleABC` 強制模組完整實作 `setup(context)`、`health_check()`、`execute(...)`、`teardown()`；`on_load()` 是標準載入入口。
- `ModuleManifest` 嚴格驗證 `name`、`version`、`author`、`dependencies`、權限及子系統。
- `VIASSOTRegistry` 是 Process Singleton，以 Writer-Preferring Read-Write Lock 保護執行期 Registry。
- SQLite Identity Ledger 以 `BEGIN IMMEDIATE` 配發不可變 URN，例如 `VIA-MOD-PY-ORDER-20260817-0001`，同一 `name + version + source hash` 重跑會取得同一 ID。
- `VIACommandRegistry` 是取得模組實例的唯一 Gateway；在 setup 前檢查 Manifest、函式簽章、Input/Output Contract、DI Provider 與相依 DAG。
- `register_many()` 先做拓撲排序，再依序 setup；卸載採逆拓撲順序，父模組仍被使用時 Fail-Closed。
- 每筆 Registry Record 保存 instance／PID、生命週期、依賴 URN、source hash、成功／失敗／逾時／健康 metrics。
- `StaticManifestScanner` 與 `VIAFileWatchdog` 只做 AST／JSON 靜態發現及 `DISCOVERED` 待審註冊，不會自動 import 或 execute 候選外掛；`VIAMemoryWatchdog` 只對非執行中的受治理實例做健康檢查。
- `VIASmartExecutor` 在進入商業邏輯前驗證輸入，執行後再次驗證輸出。
- `ProviderRegistry` 僅注入白名單型別，支援 Request Scope、Singleton 與同步／非同步資源回收。
- `SchemaToHTMLRenderer` 將 Pydantic JSON Schema 投射成有 HTML5 約束、ARIA 與穩定語意 Selector 的淺色 HTML U/I。
- `VIADigitalTwinTester` 自動生成合法值、缺少必填、上下界、型別錯誤、Enum 與額外欄位案例。
- Registry 可輸出 AI Function/Tool Schema，供 Agent 或 API Gateway 使用。
- 所有模組相依關係以拓撲順序註冊與逆序卸載，禁止卸載仍被依賴的模組。

## def 02 重要安全修正

原始概念中的 `issubclass(param.annotation, BaseModel)` 會在缺少型別註記時直接發生 `TypeError`，而且依參數名稱自動注入容易注入錯誤資源。本引擎改為：

1. 使用 `typing.get_type_hints()` 完整解析型別。
2. 未標註型別、`*args`、`**kwargs`、多個 Payload 一律 Fail-Closed。
3. DI 預設只接受型別白名單，不以參數名稱猜測。
4. HTML 表單資料仍可將 `"500"` 轉成數值，但 `"五百"` 會在模組執行前被攔截。
5. Output Contract 不接受模組隨意回傳錯誤 dict。
6. Context Manager Provider 在成功或失敗後都會自動關閉。

## def 03 Windows 11 / PowerShell 7 執行

在 PowerShell 7 執行：

```powershell
& ".\Invoke-VIA-ContractInterface-OneClick-v0200.ps1" `
    -PythonExe "C:\Path\To\via_core_312\Scripts\python.exe" `
    -Mode "All" `
    -OpenHtml $true
```

Launcher 不會安裝套件、不會修改 Canonical、也不會關閉 PowerShell。若缺少 Pydantic 或任何測試失敗，流程會 Fail-Closed。

## def 04 純 Python 執行

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m unittest discover -s tests -v
python -m via_interface_engine demo --output-dir via_contract_engine_output
```

輸出包含：

- `via_command_schema_catalog.json`
- `via_contract_command_console.html`
- `via_contract_twin_report.json`
- `via_contract_twin_report.html`
- `via_ssot_registry_snapshot.json`
- `via_ssot_registry.sqlite3`

## def 05 建立新模組

```python
from via_interface_engine import ModuleContext, ModuleManifest, VIAModuleABC


class MyModule(VIAModuleABC):
    __manifest__ = ModuleManifest(
        name="MyModule",
        version="1.0.0",
        author="VIA",
        dependencies=(),
    )

    def setup(self, context: ModuleContext) -> None:
        self.context = context

    def health_check(self) -> bool:
        return self.context is not None

    def execute(self, input_data: MyInput, logger: MyLogger) -> MyOutput:
        return MyOutput(status="SUCCESS")

    def teardown(self) -> None:
        self.context = None
```

模組不得自行取得全域 DB、Logger 或 Event Bus；資源必須由中央 `ProviderRegistry` 注入。

受控註冊範例：

```python
from pathlib import Path

from via_interface_engine import ProviderRegistry, VIACommandRegistry, VIASSOTRegistry


def def_build_registry() -> VIACommandRegistry:
    providers = ProviderRegistry()
    ssot = VIASSOTRegistry(Path(".via_ssot_registry/via_ssot_registry.sqlite3"))
    return VIACommandRegistry(providers, ssot)
```

所有查詢只能使用 `registry.get(module_name_or_urn)`；應用程式不得自行 import 已掛載模組來繞過 Registry。

## def 06 本階段邊界

- HTML 已完成 Schema-to-Form 與 Endpoint Binding，但本版不內建 FastAPI Server；可在下一階段加入受治理的 Gateway Adapter。
- Watchdog 的「自動註冊」只代表配發 URN 並進入 `DISCOVERED`；通過審核後仍須由受控 Loader 明確建立實例並 Promote 到 `READY`。
- Singleton 是單一 Python Process 範圍；SQLite Ledger 提供跨 Process 的 ID 唯一性與狀態事件，不宣稱跨 Process 共享 Python object instance。
- 同步 Python 函式無法被 Thread 安全強制中斷；高風險外掛仍應放在獨立 Process Sandbox。
- 數位雙生測試是契約與 UI Binding 測試，不會執行真實資料庫寫入。

## def 07 測試整合 Lesson Learned

本次整合的具體教訓、對應修正與永久回歸規則記錄於 [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md)。
