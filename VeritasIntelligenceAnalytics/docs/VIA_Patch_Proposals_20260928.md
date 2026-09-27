# VIA 修補提案 · 2026-09-28(待 via 審核;本檔只是文字,沒有任何一支引擎被改)

側線 2026-09-28(主線批號由併線的手指定 L25)· PR #327。操作員的 VCGC Master Prompt 規定:修補一律先經 via 審核,不自動套用(四 禁止清單)。下列 P1–P6 都已在容器實測過,但**全部沒有進樹**;要套哪一件由操作員裁。套法都是「新版號檔」(L04),或無版號冊就地;舊版一律留作版史。

| # | 提案 | 修什麼 | 容器實測 | 需要 |
|---|---|---|---|---|
| P1 | `__future__` 橋位修正(三支新版號) | b12e82ff 把加速橋注在 `from __future__` 之前 → SUP_MDL749 v0114 · VDF_ENG088 v0103 · CGC_MDL180 v0100 一 import 就 SyntaxError(`ast.parse` 不報,`compile` 才報)。SUP_MDL749 是 SSOT 增補冊樞紐 → **SSOT 連動 BROKEN 4 的根因** | SUP_MDL749 v0115 --selftest 50/50 · CGC_MDL180 v0101 7/7 · VDF_ENG088 v0104 5/2(與 v0102 相同,因為本境沒有來源庫)· 套上後 status:SSOT 連動 YELLOW 7 · GREEN 5 · BROKEN 0 | via 審核 |
| P2 | `VIA_SYSTEM_MANAGER_v0150.py`(CI 紅) | v0149 沒把 `do_list` / `_build_page` 轉給 v0148 → Windows bundled Chromium UAT 的 `test_master_control_contract_v0102` 在 setUpClass 就炸(main 同病) | setUpClass 通過,19 檢都跑到;**但還剩 test_11 頁不同步(131 vs 146)+ 一個 EditableTemplate FileNotFoundError(可能是我的測試方式造成)→ 單推 P2 不會讓這一檢轉綠** | via 審核 + 再查 test_11 |
| P3 | PS 模板章加固(工作站那版 → 容器這版) | ① 正主 `-RestoreOnly` 回傳的 dict 會漏到管線(每支腳本多印一段)② 點源正主會蓋掉宿主同名變數 `$RestoreOnly/$Report/$Body` ③ `Set-StrictMode -Off` 不在 finally,正主中途丟例外時嚴格度會外溢 ④ Register 鏈 17 層每層重載 ⑤ `Get-EventSubscriber` 不帶 `-Force` 看不到 Start 以 `-SupportEvent` 掛的訂閱 → 重複掛 | 容器沒有 pwsh:只做了括號平衡結構檢 59/59 0 問題,**ParseFile 沒量** | via 審核 + 工作站 ParseFile |
| P4 | VRN 邏輯索引冊重建(`via_vrn_logic_book_v0110 build`) | 冊上指標過期:SUP_MDL743 寫 v0105、樹上尾版 v0109 → 守門 RED → status 邏輯庫 RED、VRN 系統管理 logic RED | build 後 53/53 · 過期 0 · GREEN;邏輯庫 OK(若同時套 P1,冊上 SUP_MDL749 也要跟著指 v0115,build 會自己處理) | via 審核(冊的自有 build,一條指令) |
| P5 | InputConsole 冊補 `vcgc_layout_review` 一項 | 附件 VCGC_LAYOUT_ENGINE_v0104.zip(操作員指定的最新版)的這本冊比樹上多這一項;CGC_MDL149 v0148 的 layout 範圍登冊也指名 `central/vcgc_layout_review`。**但全格子會重生這本冊,又把它拿掉** → 手貼會被洗回去,根因在產生器 | 手貼之後 layout 登冊 0/0/0;跑格子後被洗掉(容器實證) | via 審核 + 先找產生器 |
| P6 | 主控台 `layout --selftest` 路由 | v0150 起主控台尾版先攔 `--selftest`,`via-vcgc layout --selftest` 量到的是主控台自己,不是版面樞紐 → 看起來綠的另一件事 | 樞紐 SUP_MDL743 v0109 自身 selftest 直接量 rc0 [OK] | via 審核(主控台新版號;先掃全部遠端版號 LL334) |

## 驗證方式(每件)

- P1:`python3 <新檔> --selftest`;`python3 -c "compile(open(p).read(),p,\"exec\")"`;再跑 `via-vcgc status` 看 SSOT 連動那一行。
- P2:`python3 "supportive modules/registry/tests/test_master_control_contract_v0102.py"`(CI 同一支)。
- P3:工作站 `[System.Management.Automation.Language.Parser]::ParseFile` 逐支驗;再真跑一支 `Invoke-VIA-VCGC-Lock.ps1`,比對跑前跑後的 `(Get-Process -Id $PID).PriorityClass`。
- P4:`python3 "supportive modules/registry/via_vrn_logic_book_v0110.py"`(守門)。

## diff · future_bridge_fix

```diff
diff --git a/supportive modules/70_VRN_Rules/SUP_MDL749_VRNFieldRuleHub_v0114.py b/supportive modules/70_VRN_Rules/SUP_MDL749_VRNFieldRuleHub_v0115.py
index dc47151f..8bb27112 100644
--- a/supportive modules/70_VRN_Rules/SUP_MDL749_VRNFieldRuleHub_v0114.py	
+++ b/supportive modules/70_VRN_Rules/SUP_MDL749_VRNFieldRuleHub_v0115.py	
@@ -1,18 +1,5 @@
 #!/usr/bin/env python3
-# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
-try:
-    import sys as _sa_sys
-    from pathlib import Path as _sa_Path
-    _sa_p = _sa_Path(__file__).resolve()
-    while _sa_p.parent != _sa_p:
-        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
-            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
-            break
-        _sa_p = _sa_p.parent
-    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
-except Exception:
-    VIA_ACCEL = None  # graceful:加速器缺席零影響
-# ===== [VIA:ACCEL-BRIDGE:END] =====
+# v0114→v0115(側線 2026-09-28(主線批號由併線的手指定 L25)· PR #327):拿掉 b12e82ff 誤注在 `from __future__` 之前的那段加速器橋(原第 2–15 行;模組一 import 就 SyntaxError);docstring 之後那段橋照留。其餘一字不動(v0114 留作版史 L04)。
 # 批631:本檔 v0108 的 docstring 裡有 `\d` / `\*` 這種**在字串裡不是合法跳脫**的序列,
 #   而那個 docstring 不是 raw string。py3.11 只給 DeprecationWarning(預設不印),
 #   **py3.12 給 SyntaxWarning 並印到終端**——工作站的矩陣輸出被它插進來,
diff --git a/functional modules/VDF/engine/VDF_ENG088_ConsensusFusionBridge_v0103.py b/functional modules/VDF/engine/VDF_ENG088_ConsensusFusionBridge_v0104.py
index 09fe80b5..7603fa05 100644
--- a/functional modules/VDF/engine/VDF_ENG088_ConsensusFusionBridge_v0103.py	
+++ b/functional modules/VDF/engine/VDF_ENG088_ConsensusFusionBridge_v0104.py	
@@ -1,19 +1,6 @@
 #!/usr/bin/env python3
 # -*- coding: utf-8 -*-
-# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
-try:
-    import sys as _sa_sys
-    from pathlib import Path as _sa_Path
-    _sa_p = _sa_Path(__file__).resolve()
-    while _sa_p.parent != _sa_p:
-        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
-            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
-            break
-        _sa_p = _sa_p.parent
-    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
-except Exception:
-    VIA_ACCEL = None  # graceful:加速器缺席零影響
-# ===== [VIA:ACCEL-BRIDGE:END] =====
+# v0103→v0104(側線 2026-09-28(主線批號由併線的手指定 L25)· PR #327):拿掉 b12e82ff 誤注在 `from __future__` 之前的那段加速器橋(原第 3–16 行;模組一 import 就 SyntaxError);docstring 之後那段橋照留。其餘一字不動(v0103 留作版史 L04)。
 # v0102→v0103(側線 2026-09-21 c):--selftest 要合成庫實跑,duckdb 不在本境 → [ABSENT] rc3(缺件≠壞掉),不再讓 ②④⑥ 連環紅;套件在時七檢照跑一字不動。
 r"""
 VDF_ENG088_ConsensusFusionBridge v0100 — 共識融合橋(批563 操作員「同意」)
diff --git a/supportive modules/registry/CGC_MDL180_FreezeSealAudit_v0100.py b/supportive modules/registry/CGC_MDL180_FreezeSealAudit_v0101.py
index 5cd477c0..8ec46cc9 100644
--- a/supportive modules/registry/CGC_MDL180_FreezeSealAudit_v0100.py	
+++ b/supportive modules/registry/CGC_MDL180_FreezeSealAudit_v0101.py	
@@ -1,19 +1,6 @@
 #!/usr/bin/env python3
 # -*- coding: utf-8 -*-
-# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
-try:
-    import sys as _sa_sys
-    from pathlib import Path as _sa_Path
-    _sa_p = _sa_Path(__file__).resolve()
-    while _sa_p.parent != _sa_p:
-        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
-            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
-            break
-        _sa_p = _sa_p.parent
-    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
-except Exception:
-    VIA_ACCEL = None  # graceful:加速器缺席零影響
-# ===== [VIA:ACCEL-BRIDGE:END] =====
+# v0100→v0101(側線 2026-09-28(主線批號由併線的手指定 L25)· PR #327):b12e82ff 把加速器橋注在 `from __future__` 之前(模組一 import 就 SyntaxError);橋原樣移到 `from __future__` 之後。其餘一字不動(v0100 留作版史 L04)。
 r"""
 CGC_MDL180_FreezeSealAudit v0100 — 封章對帳閘(批709)
 
@@ -50,10 +37,24 @@ CGC_MDL180_FreezeSealAudit v0100 — 封章對帳閘(批709)
 **基線外再冒出一支 BROKEN/TARGET_MISSING 就是 RED**。
 既有債可以背,新增的債不可以悄悄地背。
 
-用法:python3 CGC_MDL180_FreezeSealAudit_v0100.py [--json] | --selftest
+用法:python3 CGC_MDL180_FreezeSealAudit_v0101.py [--json] | --selftest
 律:零網路 · 零寫入(連被封的檔都不碰)· 不重新封章 · 不刪不搬 · 自己不封自己(LL133)。
 """
 from __future__ import annotations
+# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
+try:
+    import sys as _sa_sys
+    from pathlib import Path as _sa_Path
+    _sa_p = _sa_Path(__file__).resolve()
+    while _sa_p.parent != _sa_p:
+        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
+            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
+            break
+        _sa_p = _sa_p.parent
+    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
+except Exception:
+    VIA_ACCEL = None  # graceful:加速器缺席零影響
+# ===== [VIA:ACCEL-BRIDGE:END] =====
 
 import ast
 import hashlib
@@ -63,7 +64,7 @@ import sys
 from pathlib import Path
 
 ENGINE_ID = "CGC_MDL180_FreezeSealAudit"
-VERSION = "v0100"
+VERSION = "v0101"
 BATCH = "批709"
 HERE = Path(__file__).resolve().parent
 VIA = HERE.parent.parent
```

## diff · manager_v0150

```diff
--- /dev/null
+++ b/VeritasIntelligenceAnalytics/VIA_SYSTEM_MANAGER_v0150.py
@@ -0,0 +1,71 @@
+#!/usr/bin/env python3
+# -*- coding: utf-8 -*-
+"""v0149→v0150: forward every name the newest manager is asked for.
+
+v0149 only exposed selftest() and main(). The master-control contract test
+(tests/test_master_control_contract_v0102.py) loads the newest manager and
+calls do_list() and _build_page(), so the Windows UAT check went red on main.
+This file loads the v0149-patched v0148 module (TALib key still unplugged)
+and hands every other attribute to it. v0149 stays on disk.
+"""
+from __future__ import annotations
+
+# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
+try:
+    import sys as _sa_sys
+    from pathlib import Path as _sa_Path
+    _sa_p = _sa_Path(__file__).resolve()
+    while _sa_p.parent != _sa_p:
+        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
+            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
+            break
+        _sa_p = _sa_p.parent
+    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
+except Exception:
+    VIA_ACCEL = None  # graceful:加速器缺席零影響
+# ===== [VIA:ACCEL-BRIDGE:END] =====
+import importlib.util
+import sys
+from pathlib import Path
+
+HERE = Path(__file__).resolve().parent
+PRIOR = HERE / "VIA_SYSTEM_MANAGER_v0149.py"
+_BASE = None
+
+
+def _prior():
+    spec = importlib.util.spec_from_file_location("via_system_manager_v0149_for_v0150", PRIOR)
+    module = importlib.util.module_from_spec(spec)
+    sys.modules[spec.name] = module
+    spec.loader.exec_module(module)
+    return module
+
+
+def _base():
+    global _BASE
+    if _BASE is None:
+        _BASE = _prior()._load()
+    return _BASE
+
+
+def __getattr__(name: str):
+    return getattr(_base(), name)
+
+
+def selftest() -> int:
+    base = _base()
+    ok = all(callable(getattr(base, n, None)) for n in ("do_list", "_build_page"))
+    print(f"  [{'OK' if ok else 'FAIL'}] do_list / _build_page forwarded")
+    if not ok:
+        return 1
+    return _prior().selftest()
+
+
+def main() -> int:
+    if "--selftest" in sys.argv:
+        return selftest()
+    return _prior().main()
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
```

## diff · ps_template_hardening

```diff
diff --git a/VeritasIntelligenceAnalytics/Invoke-VIA-VCGC-Lock.ps1 b/VeritasIntelligenceAnalytics/Invoke-VIA-VCGC-Lock.ps1
index f068b4c7..46aa4c8e 100644
--- a/VeritasIntelligenceAnalytics/Invoke-VIA-VCGC-Lock.ps1
+++ b/VeritasIntelligenceAnalytics/Invoke-VIA-VCGC-Lock.ps1
@@ -1,17 +1,37 @@
-# CELERITAS-TEMPLATE-JOIN v1
+# CELERITAS-TEMPLATE-JOIN v1(不包裹接法 L103 ③;側線 2026-09-28(主線批號由併線的手指定 L25)· PR #327)
 #Requires -Version 7.0
-# ===== [VIA:PS-TEMPLATE:v0100] Celeritas 模板章(L102 ②;不包裹接法 L103 ③:不 cd、不動 param()、只動 $PID、關閉即還原;模板 StrictMode 不外溢) =====
+# ===== [VIA:PS-TEMPLATE:v0100] Celeritas PS7 模板章:只動本行程 · 關閉即還原 · 正主不在就略過 · 不包裹(param() 照常綁)=====
 try {
-    $VIACelProbe = $PSScriptRoot
-    while ($VIACelProbe -and (Split-Path $VIACelProbe -Parent)) {
-        $VIACelPS7 = Join-Path $VIACelProbe 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
-        if (Test-Path -LiteralPath $VIACelPS7) { . $VIACelPS7 -RestoreOnly; break }
-        $VIACelProbe = Split-Path $VIACelProbe -Parent
+    $VIACelTplFile = $null
+    $VIACelTplProbe = $PSScriptRoot
+    while ($VIACelTplProbe) {
+        $VIACelTplTry = Join-Path $VIACelTplProbe "supportive modules\ps7\VeritasCeleritas.PS7.ps1"
+        if (Test-Path -LiteralPath $VIACelTplTry) { $VIACelTplFile = $VIACelTplTry; break }
+        $VIACelTplUp = Split-Path $VIACelTplProbe -Parent
+        if ((-not $VIACelTplUp) -or ($VIACelTplUp -eq $VIACelTplProbe)) { break }
+        $VIACelTplProbe = $VIACelTplUp
     }
-    Set-StrictMode -Off
-    if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) {
-        if (-not (Get-EventSubscriber -SourceIdentifier PowerShell.Exiting -ErrorAction SilentlyContinue)) { $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { try { Restore-CeleritasPS7 } catch { } } }
+    if ($VIACelTplFile -and (-not (Get-Command Restore-CeleritasPS7 -ErrorAction Ignore))) {
+        # 正主帶 param(RestoreOnly/Report/Body);點源會蓋掉本 scope 同名變數,先存後還
+        $VIACelTplKeep = @{}
+        foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
+            $VIACelTplVar = Get-Variable -Name $VIACelTplName -Scope 0 -ErrorAction Ignore
+            if ($VIACelTplVar) { $VIACelTplKeep[$VIACelTplName] = $VIACelTplVar.Value }
+        }
+        try { $null = . $VIACelTplFile -RestoreOnly }
+        finally {
+            Set-StrictMode -Off
+            foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
+                if ($VIACelTplKeep.ContainsKey($VIACelTplName)) { Set-Variable -Name $VIACelTplName -Value $VIACelTplKeep[$VIACelTplName] -Scope 0 }
+                else { Remove-Variable -Name $VIACelTplName -Scope 0 -ErrorAction Ignore }
+            }
+        }
+    }
+    if (Get-Command Restore-CeleritasPS7 -ErrorAction Ignore) {
         [void](Start-CeleritasPS7)
+        if (-not (Get-EventSubscriber -Force -ErrorAction Ignore | Where-Object { $_.SourceIdentifier -eq 'PowerShell.Exiting' })) {
+            $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -SupportEvent -Action { try { Restore-CeleritasPS7 } catch { } }
+        }
     }
 } catch { }
 # ===== [VIA:PS-TEMPLATE:END] =====
@@ -23,6 +43,6 @@ $py = Join-Path $here "supportive modules/registry/CGC_MDL190_TALibLock_v0100.py
 Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
 & python $py
 Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
-if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] 關閉即還原
+if (Get-Command Restore-CeleritasPS7 -ErrorAction Ignore) { try { Restore-CeleritasPS7 } catch { } }
 exit $LASTEXITCODE
-if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] 關閉即還原
+if (Get-Command Restore-CeleritasPS7 -ErrorAction Ignore) { try { Restore-CeleritasPS7 } catch { } }
diff --git a/VeritasIntelligenceAnalytics/Register-VIA-Commands-v0260.ps1 b/VeritasIntelligenceAnalytics/Register-VIA-Commands-v0260.ps1
index b7c91b6e..071a4d27 100644
--- a/VeritasIntelligenceAnalytics/Register-VIA-Commands-v0260.ps1
+++ b/VeritasIntelligenceAnalytics/Register-VIA-Commands-v0260.ps1
@@ -1,17 +1,36 @@
-# CELERITAS-TEMPLATE-JOIN v1
+# CELERITAS-TEMPLATE-JOIN v1(不包裹接法 L103 ③;側線 2026-09-28(主線批號由併線的手指定 L25)· PR #327)
 #Requires -Version 7.0
-# ===== [VIA:PS-TEMPLATE:v0100] Celeritas 模板章(L102 ②;不包裹接法 L103 ③:不 cd、不動 param()、只動 $PID、關閉即還原;模板 StrictMode 不外溢) =====
+# ===== [VIA:PS-TEMPLATE:v0100] Celeritas PS7 模板章:只動本行程 · 關閉即還原 · 正主不在就略過 · 不包裹(param() 照常綁)=====
 try {
-    $VIACelProbe = $PSScriptRoot
-    while ($VIACelProbe -and (Split-Path $VIACelProbe -Parent)) {
-        $VIACelPS7 = Join-Path $VIACelProbe 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
-        if (Test-Path -LiteralPath $VIACelPS7) { . $VIACelPS7 -RestoreOnly; break }
-        $VIACelProbe = Split-Path $VIACelProbe -Parent
+    $VIACelTplFile = $null
+    $VIACelTplProbe = $PSScriptRoot
+    while ($VIACelTplProbe) {
+        $VIACelTplTry = Join-Path $VIACelTplProbe "supportive modules\ps7\VeritasCeleritas.PS7.ps1"
+        if (Test-Path -LiteralPath $VIACelTplTry) { $VIACelTplFile = $VIACelTplTry; break }
+        $VIACelTplUp = Split-Path $VIACelTplProbe -Parent
+        if ((-not $VIACelTplUp) -or ($VIACelTplUp -eq $VIACelTplProbe)) { break }
+        $VIACelTplProbe = $VIACelTplUp
     }
-    Set-StrictMode -Off
-    if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) {
-        if (-not (Get-EventSubscriber -SourceIdentifier PowerShell.Exiting -ErrorAction SilentlyContinue)) { $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { try { Restore-CeleritasPS7 } catch { } } }
-        # 短令冊只載函式;加速由各短令自己 Start/Restore
+    if ($VIACelTplFile -and (-not (Get-Command Restore-CeleritasPS7 -ErrorAction Ignore))) {
+        # 正主帶 param(RestoreOnly/Report/Body);點源會蓋掉本 scope 同名變數,先存後還
+        $VIACelTplKeep = @{}
+        foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
+            $VIACelTplVar = Get-Variable -Name $VIACelTplName -Scope 0 -ErrorAction Ignore
+            if ($VIACelTplVar) { $VIACelTplKeep[$VIACelTplName] = $VIACelTplVar.Value }
+        }
+        try { $null = . $VIACelTplFile -RestoreOnly }
+        finally {
+            Set-StrictMode -Off
+            foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
+                if ($VIACelTplKeep.ContainsKey($VIACelTplName)) { Set-Variable -Name $VIACelTplName -Value $VIACelTplKeep[$VIACelTplName] -Scope 0 }
+                else { Remove-Variable -Name $VIACelTplName -Scope 0 -ErrorAction Ignore }
+            }
+        }
+    }
+    if (Get-Command Restore-CeleritasPS7 -ErrorAction Ignore) {
+        if (-not (Get-EventSubscriber -Force -ErrorAction Ignore | Where-Object { $_.SourceIdentifier -eq 'PowerShell.Exiting' })) {
+            $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -SupportEvent -Action { try { Restore-CeleritasPS7 } catch { } }
+        }
     }
 } catch { }
 # ===== [VIA:PS-TEMPLATE:END] =====
```

## diff · inputconsole_layout_item

```diff
--- a/VeritasIntelligenceAnalytics/supportive modules/registry/VIA_InputConsole_Spec_v0100.json
+++ b/VeritasIntelligenceAnalytics/supportive modules/registry/VIA_InputConsole_Spec_v0100.json
@@ -7585,6 +7585,40 @@
        "net": false,
        "outputs": [],
        "timeout": 600
+      },
+      {
+       "id": "vcgc_layout_review",
+       "zh": "VRN 全頁版面與 FINANCIAL DATA 核對（既有 GLE；保留擷取鎖定）",
+       "engine": {
+        "dir": "supportive modules/registry",
+        "glob": "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py",
+        "verb": [
+         "layout"
+        ]
+       },
+       "test_verb": [
+        "layout",
+        "--selftest"
+       ],
+       "params": [
+        "dir",
+        "out",
+        "evidence",
+        "manifest",
+        "open"
+       ],
+       "net": false,
+       "outputs": [
+        "VIA_Reports/layout_review/LAYOUT_REVIEW.json",
+        "VIA_Reports/layout_review/LAYOUT_REVIEW.html",
+        "VIA_Reports/layout_review/LAYOUT_REPAIRED.json",
+        "VIA_Reports/layout_review/LAYOUT_REPAIRED.csv",
+        "VIA_Reports/layout_review/LAYOUT_REPAIRED.md",
+        "VIA_Reports/layout_review/ENGINE_CATALOG.json"
+       ],
+       "timeout": 600,
+       "note": "單一模組化入口；引擎頂部 ENGINE_MANIFEST 與 System Manager 共用 46 功能清冊；--evidence 重用位元核對的既有擷取；不可用合計吻合冒充完整。",
+       "capability_ssot": "supportive modules/registry/VIA_Layout_Capabilities_SSOT_v0100.json"
       }
      ]
     },
@@ -7899,4 +7933,4 @@
  },
  "contract_sync_ts": "20260916_151847",
  "batch": "CGC_MDL157"
-}
\ No newline at end of file
+}
```


## P7 · 換行假紅:三個「按原位元算 sha」的檔補進 .gitattributes 的 -text(追記 2026-09-28 05:50;待 via 審核)

**實錄**(操作員工作站 04:30 貼回):`SuccessLedger check · RED · rc=2 "lock_success": false`;同一棵樹 15b7e409 在容器量 `lock_success true`。

**根因(容器實證)**:CGC_MDL220 拿 `VIA_Policy_Laws_SSOT_v0100.json` 的**原位元** sha 前 16 碼去比 `VIA_EntryLock_v0100.json` 的 `policy_sha16`。
冊上釘的是 LF 版本:`c7aab42f7ebfd283`(LF 相符);同一份轉成 CRLF 是 `43b2de1213c987e7`(不符)。
`.gitattributes` 已經替收容件 / VTR / v0160A 鎖了位元(批546 同理由),**律冊沒有鎖** → Windows `core.autocrlf` 一轉就回報 `policy_sha` 缺 → `lock_success false`。這是判錯的紅燈(L16),不是律冊被改。

同病:layout 鎖冊 `VIA_Layout_Reuse_SSOT` 用**原位元** sha 鎖 11 個來源,SUP_MDL743 v0104 系一不相符就 `LOCK_MISMATCH`。Master Prompt 第 5 步說的「2 個 CRLF 工作複本(VRN_ENG112、VRN_ENG110)」就是這兩支沒被 `-text` 鎖住。工作站 `layout 批跑 C:\測試樣本報告 · RED` 很可能就是這一條(要看那一次的輸出才能定)。

**提案(只加三行,不改任何引擎、不改鎖冊哈希)**:

```diff
--- a/.gitattributes
+++ b/.gitattributes
@@
 VeritasIntelligenceAnalytics/**/references/intake/** -text
+
+# 側線 2026-09-28 P7:這三支被「原位元 sha」鎖住(EntryLock policy_sha16 / Layout_Reuse locked_sources);
+# Windows core.autocrlf 會轉 CRLF → sha 對不上 → 判錯的紅燈(SuccessLedger lock_success false、layout LOCK_MISMATCH)
+"VeritasIntelligenceAnalytics/supportive modules/registry/VIA_Policy_Laws_SSOT_v0100.json" -text
+"VeritasIntelligenceAnalytics/functional modules/VRN/VRN_ENG112_FinancialRead_v0100.py" -text
+"VeritasIntelligenceAnalytics/functional modules/VRN/VRN_ENG110_TabReport_v0114.py" -text
```

**套上之後工作站要做的一步**:屬性改了,已經是 CRLF 的工作複本不會自己變回來;用 `git checkout -- <那三支>` 從索引重寫一次(不是 Remove-Item)。倉裡的位元本來就是 LF,鎖冊哈希一個字都不用動。

**驗**:`python CGC_MDL220_SuccessLedger_v0100.py` → `lock_success true`;`via-vcgc layout --dir "C:\測試樣本報告" --out "C:\測試樣本報告\_核對"` → 不再 LOCK_MISMATCH。
