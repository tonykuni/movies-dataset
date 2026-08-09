@echo off
rem ENG-049 整合去重引擎(整合優化令):把去重鐵律產品化,本機判定免上傳
rem 用法:via-dedup build=建全庫索引  via-dedup check "路徑"=逐檔判定  via-dedup report=戰役總表
py "%~dp0..\supportive modules\registry\via_dedup_index.py" %*
