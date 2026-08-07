@echo off
rem Storage Optimizer AIO(session storage-architecture 整合):自足式單檔 PS(內嵌引擎+HttpListener+GUI;env bootstrap+port fallback)
rem 用法:via-storage                → 預覽模式開 GUI(預設不刪檔,-Execute 才動手)
rem       via-storage -TestAll      → 全鏈測試;-SelfTest 自測;-MaxMB n 門檻;-NoBrowser 不開瀏覽器
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\..\VeritasStorageOptimizer\VeritasStorageOptimizer_AllInOne.ps1" %*
