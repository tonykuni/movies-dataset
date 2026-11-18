#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Veritas Central Governance Console — MultiMatrix integration v0193.
One Python backend, one offline HTML frontend. No HTTP UI server.
New verb: via-vcgc matrix <action>. Other verbs delegate to the previous console.
[VIA:ACCEL-BRIDGE] Existing SuperAccel bridge + bounded local worker budget.
"""
from __future__ import annotations

# 01 · Parameters. Keep configuration together and preserve native old versions.
VERSION = 'v0193'
ANALYZER_REVISION = '0193.3'
ENGINE_FAMILY = 'CGC_MDL149_VeritasCentralGovernanceConsole'
FRONTEND_NAME = 'VCGC_MultiMatrix_v0193.html'
REFERENCE_COMMIT = '4647c8c12e931b6d69730cd0077ecfb41caba1b5'
DEFAULT_ROOTS = (r'C:\Users\tonyk\OneDrive\Documents\movies-dataset', r'C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics')
MAX_WORKERS = 4
MAX_SOURCE_BYTES = 32 * 1024 * 1024
MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_DETAIL_NODES = 100000
INLINE_NODES = 120
MAX_SAMPLE_FIELDS = 500
RECEIPT_TTL_HOURS = 24
MAX_COMMAND_SECONDS = 600
HEARTBEAT_SECONDS = 15
WATCH_INTERVAL_SECONDS = 2
SOURCE_EXTENSIONS = {'.py', '.ps1', '.psm1', '.psd1'}
DATA_EXTENSIONS = {'.json', '.csv', '.parquet'}
EXCLUDE_DIRS = {'.git', '.venv', 'venv', 'node_modules', 'site-packages', '__pycache__', '.matrix-cache'}
SYSTEMS = {'VCGC':'Veritas Central Governance Console 中央監管系統','VDF':'DataForge 資料系統','VRN':'ReportNova 報告系統','VQG':'VeritaQuantGuard 量化系統','VAP':'AutoPlot 圖形系統'}
STAGES = ('UNIT','INTEGRATION','SYSTEM','RESULT_VALIDATION','CLOSE_OUT')
MATRICES = [('M00','系統總覽'),('M01','檔案與 AST'),('M02','加速／網路覆蓋'),('M03','輸入契約'),('M04','輸出契約'),('M05','參數與時間'),('M06','VQG 指標'),('M07','VAP 圖形'),('M08','SSOT 與依賴'),('M09','測試與驗證'),('M10','錯誤與衝突'),('M11','全景修正'),('M12','執行與效能'),('M13','版本與稽核'),('M14','Skill 與跨平台工具'),('M15','舊版比較與整合'),('M16','註冊與更新')]
NET_PREFIXES = ('requests.', 'httpx.', 'aiohttp.', 'urllib.request.', 'socket.', 'yfinance.', 'curl_cffi.', 'playwright.', 'selenium.')
ACCEL_APIS = ('accel_map','parallel_map','run_fast','activate','apply_limits','ThreadPoolExecutor','ProcessPoolExecutor')
NET_BRIDGES = ('VIA_NET','via_net','network_adapter','governed_network','VIA_NET_TOOL')
SECRET_WORDS = ('password','secret','api_key','access_token','credential','private_key')
PS_AST_SCRIPT = r'''
$ErrorActionPreference='Stop'
$paths=Get-Content -LiteralPath $env:VCGC_AST_LIST -Raw -Encoding UTF8 | ConvertFrom-Json
$all=foreach($p in $paths){
 $tokens=$null;$errors=$null
 try {
  $a=[System.Management.Automation.Language.Parser]::ParseFile([string]$p,[ref]$tokens,[ref]$errors)
  $nodes=@($a.FindAll({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -or $n -is [System.Management.Automation.Language.CommandAst] -or $n -is [System.Management.Automation.Language.ParameterAst]},$true) | ForEach-Object {
   $kind=$_.GetType().Name;$name=if($_ -is [System.Management.Automation.Language.CommandAst]){$_.GetCommandName()}elseif($_ -is [System.Management.Automation.Language.FunctionDefinitionAst]){$_.Name}else{$_.Name.VariablePath.UserPath}
   @{kind=$kind;name=[string]$name;start_line=$_.Extent.StartLineNumber;end_line=$_.Extent.EndLineNumber;start_offset=$_.Extent.StartOffset;end_offset=$_.Extent.EndOffset;signature=($_.Extent.Text.Substring(0,[Math]::Min(500,$_.Extent.Text.Length)))}
  })
  @{path=$p;parser='powershell-ast';nodes=$nodes;errors=@($errors | ForEach-Object {@{message=$_.Message;line=$_.Extent.StartLineNumber;id=$_.ErrorId}})}
 }catch{@{path=$p;parser='powershell-ast';nodes=@();errors=@(@{message=$_.Exception.Message;line=0;id='PARSER_ERROR'})}}
}
ConvertTo-Json -InputObject @($all) -Depth 10 -Compress
'''
SKILL_CATALOG = [{'id': 'SKL-001', 'platform': 'Claude', 'name': 'Project instructions／專案知識', 'version': 'catalog-v0193', 'purpose': '保留 VIA 範圍、矩陣欄位與驗收規則', 'systems': ['VCGC', 'VDF', 'VRN', 'VQG', 'VAP'], 'how': '在 Claude Project 放入 README、最新 snapshot、契約與少量案例；專案指示要求先讀差異再開相關 AST。不要把整個原始碼樹當常駐上下文。', 'state': 'NOT_CONNECTED', 'evidence': 'https://support.claude.com/en/articles/12512180-use-skills-in-claude', 'updated_at': '2026-11-07', 'platform_version': '帳戶／客戶端實際版本待驗'}, {'id': 'SKL-002', 'platform': 'Claude', 'name': 'Custom Skills', 'version': 'catalog-v0193', 'purpose': '重用治理、契約、測試與報告流程', 'systems': ['VCGC', 'VRN'], 'how': '在 Customize → Skills 安裝符合平台格式的技能包；啟用所需程式執行。Project 中有檔案不等於已安裝技能。此套件提供引擎及操作文件，並非自動安裝的 Claude 技能包。', 'state': 'NOT_CONNECTED', 'evidence': 'https://support.claude.com/en/articles/12512180-use-skills-in-claude', 'updated_at': '2026-11-07', 'platform_version': '帳戶／客戶端實際版本待驗'}, {'id': 'SKL-003', 'platform': 'Claude', 'name': '文件／表格／報告技能', 'version': 'catalog-v0193', 'purpose': '把證據輸出轉成報告', 'systems': ['VRN', 'VCGC'], 'how': '以 CSV／JSON／Parquet 與驗證收據作輸入，保留來源雜湊；不得把文字摘要當測試通過。', 'state': 'NOT_CONNECTED', 'evidence': 'https://support.claude.com/en/articles/12512180-use-skills-in-claude', 'updated_at': '2026-11-07', 'platform_version': '帳戶／客戶端實際版本待驗'}, {'id': 'SKL-004', 'platform': 'Claude', 'name': 'Claude Code 本地執行', 'version': 'catalog-v0193', 'purpose': '在獲准的工作目錄執行 scan / test / install', 'systems': ['VCGC', 'VDF', 'VRN', 'VQG', 'VAP'], 'how': '由 Claude Code 使用本機 Python 執行命令。Claude Project 聊天本身不會因為看到 Windows 路徑就取得檔案存取。', 'state': 'NOT_CONNECTED', 'evidence': 'https://support.claude.com/en/articles/12512180-use-skills-in-claude', 'updated_at': '2026-11-07', 'platform_version': '帳戶／客戶端實際版本待驗'}, {'id': 'SKL-005', 'platform': 'ChatGPT', 'name': 'ChatGPT／Codex Skills 與插件', 'version': 'catalog-v0193', 'purpose': '重用指示、參照與工具工作流程', 'systems': ['VCGC', 'VDF', 'VRN', 'VQG', 'VAP'], 'how': '依目前產品支援載入插件或技能；將本套件 README 作專案指示來源，將 snapshot／差異作任務證據。平台權限與本機執行分開確認。', 'state': 'NOT_CONNECTED', 'evidence': 'https://developers.openai.com/plugins/concepts/skills', 'updated_at': '2026-11-07', 'platform_version': '帳戶／客戶端實際版本待驗'}, {'id': 'SKL-006', 'platform': 'ChatGPT', 'name': 'Codex 專案程式治理', 'version': 'catalog-v0193', 'purpose': 'AST、版本比較、測試與回歸修正', 'systems': ['VCGC', 'VDF', 'VRN', 'VQG', 'VAP'], 'how': '指向實際可讀取的工作目錄，先 scan 再選檔；變更以完整函式、雜湊守門和測試收據驗證。', 'state': 'NOT_CONNECTED', 'evidence': 'https://developers.openai.com/plugins/concepts/skills', 'updated_at': '2026-11-07', 'platform_version': '帳戶／客戶端實際版本待驗'}, {'id': 'SKL-007', 'platform': 'ChatGPT', 'name': '資料品質與報表', 'version': 'catalog-v0193', 'purpose': '分析結構、缺值與驗算結果', 'systems': ['VRN', 'VQG', 'VCGC'], 'how': '匯入真正的測試輸出和 golden reference；分析與資料品質任務不能代替原生 System testing。', 'state': 'NOT_CONNECTED', 'evidence': 'https://developers.openai.com/plugins/concepts/skills', 'updated_at': '2026-11-07', 'platform_version': '帳戶／客戶端實際版本待驗'}, {'id': 'SKL-008', 'platform': 'Manus', 'name': 'Project Skills', 'version': 'catalog-v0193', 'purpose': '專案共用執行步驟', 'systems': ['VCGC', 'VRN', 'VAP'], 'how': '在 Project Skills 管理已授權的技能，使用 Skill 面板或斜線呼叫；技能版本與輸出證據回寫本地清冊。', 'state': 'NOT_CONNECTED', 'evidence': 'https://help.manus.im/en/articles/14753565-how-to-share-and-use-skills-in-manus', 'updated_at': '2026-11-07', 'platform_version': '帳戶／客戶端實際版本待驗'}, {'id': 'SKL-009', 'platform': 'Manus', 'name': '技能匯入／分享', 'version': 'catalog-v0193', 'purpose': '共用 .skill、.zip 或 GitHub 技能來源', 'systems': ['VCGC'], 'how': '依官方 Add Skill 流程匯入相容技能；來源先驗證。此引擎 ZIP 不是技能格式，不能直接冒充 Skill 安裝。', 'state': 'NOT_CONNECTED', 'evidence': 'https://help.manus.im/en/articles/14753565-how-to-share-and-use-skills-in-manus', 'updated_at': '2026-11-07', 'platform_version': '帳戶／客戶端實際版本待驗'}, {'id': 'SKL-010', 'platform': 'Gemini', 'name': 'Gemini CLI Agent Skills', 'version': 'catalog-v0193', 'purpose': 'CLI 專案工作流程', 'systems': ['VCGC', 'VDF', 'VRN', 'VQG', 'VAP'], 'how': '依 Gemini CLI 官方 skills 文件載入技能；CLI 功能不等同 Gemini 網頁 Gems，實際客戶端版本需確認。', 'state': 'NOT_CONNECTED', 'evidence': 'https://geminicli.com/docs/cli/skills/', 'updated_at': '2026-11-07', 'platform_version': '帳戶／客戶端實際版本待驗'}, {'id': 'SKL-011', 'platform': 'Gemini', 'name': 'Gems／專案指示候選', 'version': 'catalog-v0193', 'purpose': '以文字規則協助讀取矩陣', 'systems': ['VCGC', 'VRN'], 'how': '可移植任務說明與輸出契約；帳戶端可用功能待確認，未宣稱 Gemini 網頁可執行本機 Python。', 'state': 'PLATFORM_CAPABILITY_REVIEW', 'evidence': 'https://geminicli.com/docs/cli/skills/', 'updated_at': '2026-11-07', 'platform_version': '帳戶／客戶端實際版本待驗'}, {'id': 'SKL-012', 'platform': 'Copilot', 'name': 'GitHub Copilot Agent Skills', 'version': 'catalog-v0193', 'purpose': '開發工作流程與程式審查', 'systems': ['VCGC', 'VDF', 'VRN', 'VQG', 'VAP'], 'how': '支援的 Copilot 客戶端可使用 .github/skills 等目錄。依官方支援範圍驗證；不推論 Microsoft 365 Copilot 相同。', 'state': 'NOT_CONNECTED', 'evidence': 'https://docs.github.com/en/copilot/concepts/customizations/agent-skills', 'updated_at': '2026-11-07', 'platform_version': '帳戶／客戶端實際版本待驗'}, {'id': 'SKL-013', 'platform': 'Copilot', 'name': 'Repository instructions／PR checks', 'version': 'catalog-v0193', 'purpose': '變更規則與審查證據', 'systems': ['VCGC'], 'how': '保留 AGENTS／repo instructions；輸出測試收據、版本差異與未完成事項。本套件不自動提交或推送 GitHub。', 'state': 'NOT_CONNECTED', 'evidence': 'https://docs.github.com/en/copilot/concepts/customizations/agent-skills', 'updated_at': '2026-11-07', 'platform_version': '帳戶／客戶端實際版本待驗'}, {'id': 'SKL-014', 'platform': '跨平台', 'name': 'Token read / slice / digest / etag / chain', 'version': 'catalog-v0193', 'purpose': '先定位、再讀取變更範圍', 'systems': ['VCGC', 'VDF', 'VRN', 'VQG', 'VAP'], 'how': '從既有 VCGC token 動詞開始；pin 鎖定版，避免全檔重讀。節省比例需實測。', 'state': 'NATIVE_DISCOVERY_REQUIRED', 'evidence': 'local VCGC registry / protocol and file contracts', 'updated_at': '2026-11-07', 'platform_version': '帳戶／客戶端實際版本待驗'}, {'id': 'SKL-015', 'platform': '跨平台', 'name': 'AST 與 SHA256 增量快取', 'version': 'catalog-v0193', 'purpose': '只重算有變動來源的靜態分析', 'systems': ['VCGC', 'VDF', 'VRN', 'VQG', 'VAP'], 'how': '掃描時自動有界批次；來源內容／解析器版本改變失效。未解析 PS 不能借用 Python 掃描結果。', 'state': 'IMPLEMENTED_LOCAL', 'evidence': 'local VCGC registry / protocol and file contracts', 'updated_at': '2026-11-07', 'platform_version': '帳戶／客戶端實際版本待驗'}, {'id': 'SKL-016', 'platform': '跨平台', 'name': 'JSON 契約與 Parquet／CSV', 'version': 'catalog-v0193', 'purpose': '跨系統傳遞結構及數據', 'systems': ['VCGC', 'VDF', 'VRN', 'VQG', 'VAP'], 'how': 'Schema 辨識、欄位分層、CSV UTF-8 BOM；Parquet 需已有 pyarrow。', 'state': 'IMPLEMENTED_LOCAL', 'evidence': 'local VCGC registry / protocol and file contracts', 'updated_at': '2026-11-07', 'platform_version': '帳戶／客戶端實際版本待驗'}, {'id': 'SKL-017', 'platform': '跨平台', 'name': 'U/I/S/R/C 測試收據', 'version': 'catalog-v0193', 'purpose': '不以 exit 0 代替結果驗證', 'systems': ['VCGC', 'VDF', 'VRN', 'VQG', 'VAP'], 'how': 'test-plan 明定腳本雜湊、資料、結果 JSON 與預期斷言；來源／環境／規則變動即過期。', 'state': 'IMPLEMENTED_LOCAL', 'evidence': 'local VCGC registry / protocol and file contracts', 'updated_at': '2026-11-07', 'platform_version': '帳戶／客戶端實際版本待驗'}, {'id': 'SKL-018', 'platform': '跨平台', 'name': 'Celeritas／SuperAccel', 'version': 'catalog-v0193', 'purpose': '既有加速器工具橋', 'systems': ['VCGC', 'VDF', 'VRN', 'VQG', 'VAP'], 'how': '校驗鎖定工具雜湊後呼叫既有 activate API；單純 marker 不算執行覆蓋，逐檔仍須實測。', 'state': 'NATIVE_DISCOVERY_REQUIRED', 'evidence': 'local VCGC registry / protocol and file contracts', 'updated_at': '2026-11-07', 'platform_version': '帳戶／客戶端實際版本待驗'}, {'id': 'SKL-019', 'platform': '跨平台', 'name': 'Aegis／統一網路工具', 'version': 'catalog-v0193', 'purpose': 'VDF 全引擎及所有對外出口', 'systems': ['VCGC', 'VDF', 'VRN', 'VQG', 'VAP'], 'how': '依本地工具鎖採用相容版本，驗證重試、快取、限速、timeout、來源與 DENY。無法直接連線不能宣稱通過。', 'state': 'NATIVE_DISCOVERY_REQUIRED', 'evidence': 'local VCGC registry / protocol and file contracts', 'updated_at': '2026-11-07', 'platform_version': '帳戶／客戶端實際版本待驗'}, {'id': 'SKL-020', 'platform': '跨平台', 'name': 'NLP／Layout／OCR', 'version': 'catalog-v0193', 'purpose': '文字分類、欄位與版面處理', 'systems': ['VCGC', 'VDF', 'VRN', 'VQG', 'VAP'], 'how': '沿用 VRN 管理器與現有鎖定工具；先輕量、再較重處理，輸出回到契約驗證。', 'state': 'NATIVE_DISCOVERY_REQUIRED', 'evidence': 'local VCGC registry / protocol and file contracts', 'updated_at': '2026-11-07', 'platform_version': '帳戶／客戶端實際版本待驗'}, {'id': 'SKL-021', 'platform': '跨平台', 'name': 'MCP 連接器', 'version': 'catalog-v0193', 'purpose': '平台與資料能力互通', 'systems': ['VCGC', 'VDF', 'VRN', 'VQG', 'VAP'], 'how': '沿用 VCGC mcp 動詞與各平台連接設定；連接存在不等於授權所有資料、也不等於技能完全通用。', 'state': 'NATIVE_DISCOVERY_REQUIRED', 'evidence': 'local VCGC registry / protocol and file contracts', 'updated_at': '2026-11-07', 'platform_version': '帳戶／客戶端實際版本待驗'}, {'id': 'SKL-022', 'platform': '跨平台', 'name': '差異摘要與檔案分頁', 'version': 'catalog-v0193', 'purpose': '降低送入模型的重複內容', 'systems': ['VCGC', 'VDF', 'VRN', 'VQG', 'VAP'], 'how': '優先 delta、file ID、AST node ID、受影響契約；失敗明細才向下讀取。', 'state': 'IMPLEMENTED_LOCAL', 'evidence': 'local VCGC registry / protocol and file contracts', 'updated_at': '2026-11-07', 'platform_version': '帳戶／客戶端實際版本待驗'}]
MERGE_BASELINE = [{'name': 'VIA_SystemIntegrationEngine(2).py', 'sha256': '4e580833fde0fdcbd0a33703c477ef2c9ab9b2acf753bf1d826efbec6046d63d', 'bytes': 84470, 'top_level_definitions': 34, 'redefined_names': {}, 'comparison': '34 個同名頂層定義中，32 個 AST 與 v0300 相同', 'decision': '共通治理能力整合至本後端；不重複啟動第二個 UI', 'preserve': 'DAG、圖形格式匯出及領域工作流程仍由既有引擎提供'}, {'name': 'VIA_MatrixGovernance_AllInOne_v0100(1).py', 'sha256': 'bb8d5911a0e15765b9a4e0ad9d01a6104a78a044878db71b509b326f1f80b7b0', 'bytes': 62334, 'top_level_definitions': 33, 'redefined_names': {}, 'comparison': '33 個同名頂層定義中，27 個 AST 與 v0300 相同', 'decision': '掃描、矩陣、測試證據、報告與稽核整合', 'preserve': '舊資料處理／oracle 專用測試保留，未宣稱同本次新自測'}, {'name': 'VIA_SystemIntegrationEngine_v0300(1).py', 'sha256': '97ca853d253ea58194a2938762899624852f8651c9853fa3224d93d46855f304', 'bytes': 2752636, 'top_level_definitions': 101, 'redefined_names': {'create_app': 3, 'main': 2}, 'comparison': 'create_app 定義 3 次；main 定義 2 次。可能是刻意包裝，需避免多入口重複啟動', 'decision': '前端單一靜態 HTML；治理入口單一 PY；新矩陣不啟動舊 HTTP UI', 'preserve': 'AgentOS 記憶、圖形介接等專用功能保留於原本管理器'}, {'name': 'CGC_MDL149_VeritasCentralGovernanceConsole_v0192.py', 'sha256': '66b1c49d014b004b04b4fb0933c032042aded54afc54cb94378295c4c92c9db3', 'bytes': 9735, 'comparison': '目前已讀取 GitHub 正本尾版', 'decision': '新增 v0193 的 matrix 動詞；其餘委派 v0192 鏈', 'preserve': '原生 token / mcp / handoff / functions / test / registry-sync'}, {'name': 'VIA_LayerMatrix_v0100.py', 'sha256': 'f5e8d1de782051b562ac4d98146155054970245556cfd2e4f9c23ca889f4ba8e', 'bytes': 31290, 'comparison': '既有階層矩陣及收尾審查工具', 'decision': '保留專用工具；M15 記錄來源，避免覆寫', 'preserve': '原收據與專用階層矩陣'}, {'name': 'VIA_SettleAll_v0117.py', 'sha256': '265fb560d3e461e34ca5e47c586a5db9b31b4b7c240dc5ce746bb64f6da61762', 'bytes': 219713, 'comparison': '已有 VDF / VRN / VQG / VAP / AgentOS 整合階段', 'decision': '保留系統編排；本引擎聚焦共同治理與證據', 'preserve': '各子系統自主流程；不自動執行 Git 同步'}]

import argparse
import ast
import collections
import concurrent.futures
import contextlib
import copy
import csv
import difflib
import hashlib
import importlib.util
import io
import json
import os
import platform
import re
import secrets
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import tokenize
import unittest
import uuid
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path

VIA_ACCEL = None
_PRIOR_MODULE = None

# 02 · Identity, safe persistence, locking and audit chain.
def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def json_bytes(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,default=str)+'\n').encode('utf-8')


def digest(value):
    return hashlib.sha256(value if isinstance(value,bytes) else json_bytes(value)).hexdigest()


def file_hash(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def read_json(path, default=None, max_bytes=MAX_JSON_BYTES):
    p=Path(path)
    if not p.exists():return default
    if p.stat().st_size>max_bytes:raise ValueError('JSON_SIZE_LIMIT: '+str(p))
    return json.loads(p.read_text(encoding='utf-8-sig'))


def atomic_write(path, content):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    data=content if isinstance(content,bytes) else content.encode('utf-8')
    fd,tmp=tempfile.mkstemp(prefix='.'+p.name+'.',suffix='.tmp',dir=p.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


def atomic_json(path, value):
    atomic_write(path,json_bytes(value))


def version_number(path):
    m=re.search(r'[_-]v(\d+)(?:\.[^.]+)?$',Path(path).stem)
    return int(m.group(1)) if m else -1


def tail(folder, pattern):
    return max(Path(folder).glob(pattern),key=version_number,default=None)


def within(path, roots):
    p=Path(path).resolve()
    return any(p.is_relative_to(Path(r).resolve()) for r in roots)


def stable_id(kind, value):
    return kind+'-'+str(uuid.uuid5(uuid.NAMESPACE_URL,'via:matrix:'+kind+':'+str(value)))


def public_value(name, value):
    if any(x in str(name).lower() for x in SECRET_WORDS):return '[REDACTED: credential_ref only]'
    def clean(item,depth=0):
        if depth>12:return '[DEPTH_LIMIT]'
        if isinstance(item,dict):return {str(k):('[REDACTED: credential_ref only]' if any(x in str(k).lower() for x in SECRET_WORDS) else clean(v,depth+1)) for k,v in item.items()}
        if isinstance(item,(list,tuple)):return [clean(v,depth+1) for v in item]
        if isinstance(item,set):return sorted((clean(v,depth+1) for v in item),key=str)
        if item is None or isinstance(item,(str,int,float,bool)):return item
        return repr(item)
    cleaned=clean(value);text=json.dumps(cleaned,ensure_ascii=False,default=str)
    return cleaned if len(text)<500 else text[:497]+'…'


@contextlib.contextmanager
def workspace_lock(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);p=folder/'.matrix.lock'
    try:fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError:raise RuntimeError('WORKSPACE_BUSY: '+str(p))
    try:
        os.write(fd,json_bytes({'pid':os.getpid(),'started_at':utc_now()}));os.close(fd);yield
    finally:p.unlink(missing_ok=True)


def audit_event(out, kind, payload):
    p=Path(out)/'events.jsonl';prev='0'*64
    if p.exists():
        with p.open('rb') as f:
            f.seek(max(0,p.stat().st_size-65536));lines=f.read().splitlines()
        if lines:prev=json.loads(lines[-1])['event_hash']
    row={'event_id':str(uuid.uuid4()),'at':utc_now(),'kind':kind,'payload':payload,'previous_hash':prev}
    row['event_hash']=digest(row)
    with p.open('ab') as f:f.write(json.dumps(row,ensure_ascii=False,sort_keys=True).encode()+b'\n');f.flush();os.fsync(f.fileno())
    return row


def verify_audit(path):
    previous='0'*64;count=0
    if not Path(path).exists():return {'status':'NOT_RUN','count':0}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        row=json.loads(line);saved=row.pop('event_hash')
        if row.get('previous_hash')!=previous or digest(row)!=saved:return {'status':'FAIL','count':count}
        previous=saved;count+=1
    return {'status':'PASS','count':count,'head':previous}


def discover_via(roots):
    candidates=[]
    for root in roots:
        p=Path(root).expanduser().resolve()
        if (p/'supportive modules'/'registry').is_dir():candidates.append(p)
        if (p/'VeritasIntelligenceAnalytics'/'supportive modules'/'registry').is_dir():candidates.append(p/'VeritasIntelligenceAnalytics')
    return list(dict.fromkeys(candidates))


def environment_fingerprint():
    return digest({'os':platform.platform(),'python':sys.version,'executable':sys.executable})


def resource_budget(workers=None):
    cpus=os.cpu_count() or 1;limit=max(1,min(int(workers or MAX_WORKERS),MAX_WORKERS,cpus))
    available=None
    try:
        if os.name=='posix':available=os.sysconf('SC_AVPHYS_PAGES')*os.sysconf('SC_PAGE_SIZE')
    except (ValueError,OSError):pass
    if available is not None:limit=min(limit,max(1,available//(256*1024*1024)))
    return {'cpu_count':cpus,'workers':int(limit),'available_memory_bytes':available,'source_batch_size':int(limit)*2,'global_os_changes':False}


def resolve_lock_path(via, path):
    parts=str(path).replace('\\','/').split('/')
    if 'VeritasIntelligenceAnalytics' in parts:parts=parts[parts.index('VeritasIntelligenceAnalytics')+1:]
    result=(Path(via)/Path(*parts)).resolve()
    if not result.is_relative_to(Path(via).resolve()):raise ValueError('TOOL_PATH_ESCAPE')
    return result


def inspect_tools(via):
    if not via:return []
    lock=read_json(Path(via)/'supportive modules/registry/VIA_ToolVersion_Lock_v0100.json',{})
    rows=[]
    for family,entry in lock.items():
        if not isinstance(entry,dict) or 'path' not in entry:continue
        row={'id':'TOOL-'+family,'name':family,'version':entry.get('version'),'expected_sha256':entry.get('sha256'),'state':'UNKNOWN','updated_at':entry.get('activated_at')}
        try:
            p=resolve_lock_path(via,entry['path']);row['path']=str(p);raw=p.read_bytes();row['sha256']=digest(raw)
            row['state']='LOCK_MATCH' if row['sha256']==entry.get('sha256') else ('LINE_ENDINGS_ONLY' if digest(raw.replace(b'\r\n',b'\n'))==entry.get('sha256') else 'LOCK_MISMATCH')
        except (OSError,ValueError) as e:row.update(state='MISSING',error=str(e))
        rows.append(row)
    return rows


def activate_accelerator(via, tools):
    """[VIA:ACCEL-BRIDGE:v0100] Load the existing bridge only against a matching lock."""
    global VIA_ACCEL
    VIA_ACCEL=None
    result={'builtin':'BOUNDED_EXECUTOR_READY','external':'NOT_AVAILABLE','executed':False}
    if not via:return result
    pin=next((x for x in tools if x['name']=='accelerator'),{})
    if pin.get('state') not in ('LOCK_MATCH','LINE_ENDINGS_ONLY'):
        result['external']='BLOCKED_TOOL_LOCK';return result
    bridge=Path(via)/'supportive modules/VIA_SuperAccel_Module.py'
    if not bridge.is_file():return result
    try:
        sys.dont_write_bytecode=True
        spec=importlib.util.spec_from_file_location('VIA_SuperAccel_Module',bridge)
        module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
        VIA_ACCEL=module
        value=module.activate(apply_limits=True) if callable(getattr(module,'activate',None)) else None
        applied=value.get('applied') if isinstance(value,dict) else None
        verified=bool(isinstance(applied,dict) and applied and not applied.get('err') and value.get('celeritas'))
        result.update(external='API_APPLIED' if verified else 'LOADED_NOT_VERIFIED',executed=True,bridge_sha256=file_hash(bridge),tool_sha256=pin.get('sha256'),result=value)
    except Exception as e:result.update(external='ERROR',error=type(e).__name__+': '+str(e))
    return result

# 03 · Recursive inventory and native AST analysis. Never import scanned targets.
def is_reparse(path):
    try:
        return path.is_symlink() or bool(getattr(path.lstat(),'st_file_attributes',0)&0x400)
    except OSError:return True


def enumerate_tree(roots, output=None):
    files={};excluded=[];errors=[]
    for root in roots:
        root=Path(root).expanduser().resolve()
        if not root.is_dir():errors.append({'path':str(root),'reason':'ROOT_MISSING'});continue
        def on_error(e):errors.append({'path':e.filename,'reason':'DIRECTORY_READ_ERROR','detail':str(e)})
        for directory,dirs,names in os.walk(root,followlinks=False,onerror=on_error):
            current=Path(directory);kept=[]
            for name in sorted(dirs):
                child=current/name;reason=None
                if name.lower() in EXCLUDE_DIRS or (child/'pyvenv.cfg').is_file():reason='DEPENDENCY_OR_RUNTIME'
                elif output and child.resolve()==Path(output).resolve():reason='OWN_REPORT_OUTPUT'
                elif is_reparse(child):reason='LINK_OR_REPARSE_UNENUMERATED';errors.append({'path':str(child),'reason':reason})
                if reason:excluded.append({'path':str(child),'reason':reason})
                else:kept.append(name)
            dirs[:]=kept
            for name in sorted(names):
                p=current/name
                if p.suffix.lower() not in SOURCE_EXTENSIONS|DATA_EXTENSIONS and name!='SKILL.md':continue
                if is_reparse(p):
                    excluded.append({'path':str(p),'reason':'LINK_OR_REPARSE'});errors.append({'path':str(p),'reason':'SOURCE_LINK_UNRESOLVED'});continue
                key=os.path.normcase(str(p.resolve()));files.setdefault(key,{'path':str(p.resolve()),'root':str(root)})
    return sorted(files.values(),key=lambda x:x['path'].lower()),excluded,errors


def classify_system(path):
    text=str(path).replace('\\','/');name=Path(path).name
    if re.search(r'(?:^|[/_])(?:VQG|QuantGuard|VeritaQuantGuard)(?:[/_.-]|$)',text,re.I):return 'VQG'
    if re.search(r'(?:^|[/_])VAP(?:[/_.-]|$)',text,re.I):return 'VAP'
    if re.search(r'(?:^|[/_])(?:VRN|VRN2|VRN-2)(?:[/_.-]|$)',text,re.I) or name.startswith('ActivateVRN'):return 'VRN'
    if re.search(r'(?:^|[/_])VDF(?:[/_.-]|$)',text,re.I):return 'VDF'
    return 'VCGC'


def qualified_call(node, aliases):
    if isinstance(node,ast.Name):return aliases.get(node.id,node.id)
    if isinstance(node,ast.Attribute):return qualified_call(node.value,aliases)+'.'+node.attr
    return '<dynamic>'


def analyze_python(source, path, entity_id):
    tree=ast.parse(source,filename=str(path));compile(tree,str(path),'exec');source_lines=source.splitlines()
    aliases={};imports=[];parameters=[];issues=[];nodes=[];calls=[];definition_signatures=[];counter=collections.Counter();truncated=False
    for n in ast.walk(tree):
        if isinstance(n,ast.Import):
            for a in n.names:aliases[a.asname or a.name.split('.')[0]]=a.name if a.asname else a.name.split('.')[0];imports.append(a.name)
        elif isinstance(n,ast.ImportFrom):
            for a in n.names:aliases[a.asname or a.name]=(n.module+'.' if n.module else '')+a.name
            imports.append('.'*n.level+(n.module or ''))
    for n in tree.body:
        if isinstance(n,(ast.Assign,ast.AnnAssign)):
            targets=n.targets if isinstance(n,ast.Assign) else [n.target]
            for target in targets:
                if isinstance(target,ast.Name) and target.id.isupper():
                    try:
                        if len(ast.dump(n.value))>10000:continue
                        value=ast.literal_eval(n.value)
                    except (ValueError,TypeError,RecursionError):continue
                    parameters.append({'id':stable_id('PAR',entity_id+target.id),'name':target.id,'default':public_value(target.id,value),'effective_value':None,'value_source':'STATIC_DECLARATION','line':n.lineno,'owner':classify_system(path)})
    selected=(ast.stmt,ast.Call,ast.ExceptHandler)
    def visit(n,parent_id,scope):
        nonlocal truncated
        current_parent=parent_id;new_scope=scope
        if isinstance(n,selected):
            isdef=isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))
            semantic=ast.dump(n,include_attributes=False);kind=type(n).__name__
            name=n.name if isdef else (qualified_call(n.func,aliases) if isinstance(n,ast.Call) else kind)
            identity=scope+'/'+kind+'/'+name if isdef else scope+'/'+kind+'/'+digest(semantic.encode())[:20]
            counter[identity]+=1;nid=stable_id('AST',entity_id+identity+':'+str(counter[identity]))
            signature=source_lines[n.lineno-1].strip()[:600]
            if isdef:
                definition_signatures.append({'name':scope+'.'+name if scope else name,'signature':signature,'line':n.lineno,'end_line':n.end_lineno,'node_id':nid});new_scope=scope+'.'+name
            if len(nodes)<MAX_DETAIL_NODES:
                nodes.append({'id':nid,'parent_id':parent_id,'kind':kind,'name':name,'signature':signature,'line':n.lineno,'end_line':n.end_lineno,'semantic_sha256':digest(semantic.encode()),'tests':{s:'NOT_RUN' for s in STAGES}})
            else:truncated=True
            current_parent=nid
            if isinstance(n,ast.Call):
                call=qualified_call(n.func,aliases);network=call.startswith(NET_PREFIXES) or call in ('urlopen','urlretrieve')
                if call.startswith(('subprocess.','os.system','os.popen')):
                    raw=ast.get_source_segment(source,n) or '';network=network or bool(re.search(r'curl|wget|https?://',raw,re.I))
                    issues.append({'rule':'SUBPROCESS_REVIEW','severity':'WARNING','node_id':nid,'line':n.lineno,'message':'子行程需確認出口與執行契約'})
                governed=any(x.lower() in call.lower() for x in NET_BRIDGES)
                calls.append({'node_id':nid,'name':call,'line':n.lineno,'network':network,'governed_candidate':governed})
                if call in ('eval','exec','__import__') or call.startswith('importlib.'):
                    issues.append({'rule':'DYNAMIC_RESOLUTION','severity':'WARNING','node_id':nid,'line':n.lineno,'message':'動態載入／執行的依賴與出口待解析'})
            if isinstance(n,ast.ExceptHandler) and n.type is None:issues.append({'rule':'BARE_EXCEPT','severity':'WARNING','node_id':nid,'line':n.lineno,'message':'無例外型別，可能掩蓋失敗'})
        for child in ast.iter_child_nodes(n):visit(child,current_parent,new_scope)
    visit(tree,None,'')
    names=collections.Counter(x['name'] for x in definition_signatures)
    for name,count in names.items():
        if count>1:issues.append({'rule':'DUPLICATE_DEFINITION','severity':'WARNING','node_id':None,'line':0,'message':f'{name} 定義 {count} 次；需判定是否刻意轉接'})
    bridge=any(v=='VIA_SuperAccel_Module' or v.startswith('VIA_SuperAccel_Module.') for v in aliases.values())
    accel_calls=[c for c in calls if c['name'].split('.')[-1] in ACCEL_APIS]
    net_calls=[c for c in calls if c['network']]
    net_bind=any(c['governed_candidate'] for c in calls) or any('via_net' in v.lower() or 'aegis' in v.lower() for v in imports)
    for c in net_calls:
        if not c['governed_candidate']:issues.append({'rule':'NETWORK_ROUTE_UNVERIFIED','severity':'WARNING','node_id':c['node_id'],'line':c['line'],'message':c['name']+' 需要工具轉接與實跑證據'})
    return {'parser':'python-ast','parse_state':'PARSED','nodes':nodes,'node_count':sum(counter.values()),'nodes_truncated':truncated,'definitions':definition_signatures,'imports':sorted(set(imports)),'parameters':parameters,'calls':calls,'issues':issues,'accelerator':{'state':'STATIC_CANDIDATE' if bridge and accel_calls else 'MARKER_ONLY' if '[VIA:ACCEL-BRIDGE' in source else 'MISSING','bridge_import':bridge,'api_calls':accel_calls},'network':{'required':classify_system(path)=='VDF' or bool(net_calls),'state':'STATIC_CANDIDATE' if net_bind else 'MISSING' if net_calls or classify_system(path)=='VDF' else 'APPLICABILITY_REVIEW','outlets':net_calls}}


def powershell_parse(paths, out):
    if not paths:return {}
    executable=shutil.which('pwsh') or (shutil.which('powershell') if os.name=='nt' else None)
    if not executable:return {p:{'parser':'unavailable','nodes':[],'errors':[],'parse_state':'PARSER_UNAVAILABLE'} for p in paths}
    results={}
    for offset in range(0,len(paths),50):
        with tempfile.TemporaryDirectory(prefix='vcgc_ps_') as temp:
            listing=Path(temp)/'files.json';atomic_json(listing,paths[offset:offset+50]);env=os.environ.copy();env['VCGC_AST_LIST']=str(listing)
            run=subprocess.run([executable,'-NoProfile','-NonInteractive','-Command',PS_AST_SCRIPT],env=env,capture_output=True,timeout=MAX_COMMAND_SECONDS)
            if run.returncode:raise RuntimeError('PS_PARSER_FAILED: '+run.stderr.decode('utf-8',errors='replace')[-2000:])
            data=json.loads(run.stdout.decode('utf-8-sig'))
            if isinstance(data,dict):data=[data]
            for row in data:results[row['path']]=row
    return results


def ps_analysis(source, path, entity_id, parsed):
    issues=[];nodes=[];calls=[];defs=[];seen=collections.Counter();rawnodes=parsed.get('nodes',[])
    for raw in rawnodes:
        key=raw['kind']+':'+raw['name'];seen[key]+=1;nid=stable_id('AST',entity_id+key+str(seen[key]));node={'id':nid,'parent_id':None,'kind':raw['kind'],'name':raw['name'],'signature':raw.get('signature',''),'line':raw.get('start_line'),'end_line':raw.get('end_line'),'tests':{s:'NOT_RUN' for s in STAGES}}
        containers=[n for n in nodes if n['kind']=='FunctionDefinitionAst' and n['line']<=node['line'] and n['end_line']>=node['end_line']]
        if containers:node['parent_id']=min(containers,key=lambda n:n['end_line']-n['line'])['id']
        nodes.append(node)
        if raw['kind']=='FunctionDefinitionAst':defs.append({'name':raw['name'],'signature':raw.get('signature',''),'line':raw.get('start_line'),'end_line':raw.get('end_line'),'node_id':nid})
        if raw['kind']=='CommandAst':calls.append({'node_id':nid,'name':raw['name'],'line':raw.get('start_line'),'network':raw['name'].lower() in ('invoke-webrequest','invoke-restmethod','curl','curl.exe','wget'),'governed_candidate':bool(re.search(r'via.*net|aegis',raw['name'],re.I))})
    for error in parsed.get('errors',[]):issues.append({'rule':'PS_SYNTAX','severity':'ERROR','node_id':None,'line':error.get('line',0),'message':error['message']})
    accel=any(re.search(r'accel|celeritas',c['name'],re.I) for c in calls)
    outlets=[c for c in calls if c['network']]
    if parsed.get('parser')=='unavailable':issues.append({'rule':'PS_AST_UNAVAILABLE','severity':'WARNING','line':0,'node_id':None,'message':'需要 PowerShell 原生 Parser；未以文字掃描冒充 AST'})
    return {'parser':parsed.get('parser'),'parse_state':'ERROR' if parsed.get('errors') else parsed.get('parse_state','PARSED'),'nodes':nodes,'node_count':len(nodes),'nodes_truncated':False,'definitions':defs,'imports':[],'parameters':[],'calls':calls,'issues':issues,'accelerator':{'state':'STATIC_CANDIDATE' if accel else 'MARKER_ONLY' if re.search(r'ACCEL|Celeritas',source,re.I) else 'MISSING','bridge_import':accel,'api_calls':[]},'network':{'required':classify_system(path)=='VDF' or bool(outlets),'state':'STATIC_CANDIDATE' if any(c['governed_candidate'] for c in calls) else 'APPLICABILITY_REVIEW','outlets':outlets}}


def analyze_file(item, ps_results, cached=None):
    p=Path(item['path']);eid=stable_id('FILE',os.path.normcase(str(p.resolve())))
    row={'id':eid,'governance_id':None,'owner':classify_system(p),'variant':'VRN-2' if re.search(r'VRN.?2|ActivateVRN',str(p),re.I) else None,'name':p.name,'path':str(p),'root':item['root'],'version':f'v{version_number(p):04d}' if version_number(p)>=0 else None,'kind':'file','status':'YELLOW','updated_at':None,'timestamp_basis':'filesystem_mtime','observed_at':utc_now(),'sha256':None,'issues':[],'tests':{s:'NOT_RUN' for s in STAGES},'parser':'unknown','parse_state':'UNKNOWN','accelerator':{'state':'UNKNOWN'},'network':{'required':None,'state':'UNKNOWN','outlets':[]},'nodes':[],'definitions':[],'calls':[],'imports':[],'parameters':[]}
    try:
        stat=p.stat();row.update(bytes=stat.st_size,updated_at=datetime.fromtimestamp(stat.st_mtime,timezone.utc).isoformat())
        if stat.st_size>MAX_SOURCE_BYTES:raise ValueError('SOURCE_SIZE_LIMIT; denominator retained')
        raw=p.read_bytes();row['sha256']=digest(raw)
        if cached and cached.get('sha256')==row['sha256'] and cached.get('analysis_version')==ANALYZER_REVISION and (p.suffix.lower()=='.py' or cached.get('parser')=='powershell-ast'):
            for key in ('parser','parse_state','nodes','node_count','nodes_truncated','definitions','imports','parameters','calls','issues','accelerator','network'):row[key]=copy.deepcopy(cached.get(key,row.get(key)))
            row['cache_reused']=True;row['version']=row['version'] or cached.get('version');return row
        if p.suffix.lower()=='.py':
            enc,_=tokenize.detect_encoding(io.BytesIO(raw).readline);source=raw.decode(enc);row.update(analyze_python(source,p,eid))
        else:
            source=raw.decode('utf-8-sig',errors='replace');row.update(ps_analysis(source,p,eid,ps_results.get(str(p),{'parser':'unavailable','parse_state':'PARSER_UNAVAILABLE'})))
    except (OSError,ValueError,SyntaxError,UnicodeError,RecursionError,TypeError,OverflowError) as e:
        row['parse_state']='ERROR';row['issues'].append({'rule':'SOURCE_PARSE','severity':'ERROR','node_id':None,'line':getattr(e,'lineno',0) or 0,'message':str(e)})
    row['analysis_version']=ANALYZER_REVISION
    if not row['version']:
        match=re.search(r'[_-](v[0-9]{3,4})(?:\([0-9]+\))?$',p.stem)
        declared=next((x.get('default') for x in row.get('parameters',[]) if x['name']=='VERSION'),None)
        row['version']=match.group(1) if match else str(declared) if isinstance(declared,(str,int,float)) else None
    return row

# 04 · Contracts, dependencies and evidence. Static discovery is never runtime proof.
def inspect_artifact(item):
    p=Path(item['path']);row={'id':stable_id('DATA',str(p)),'owner':classify_system(p),'path':str(p),'name':p.name,'version':f'v{version_number(p):04d}' if version_number(p)>=0 else None,'fields':[],'direction':'UNDECLARED','status':'DISCOVERED','row_count':None,'updated_at':None,'schema_complete':False,'catalog_entries':[]}
    try:
        row['updated_at']=datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat();row['bytes']=p.stat().st_size
        if p.suffix.lower()=='.csv':
            with p.open(encoding='utf-8-sig',newline='') as f:header=next(csv.reader(f),[])
            row['fields']=[{'name':x,'type':'unknown'} for x in header[:MAX_SAMPLE_FIELDS]];row['schema_complete']=len(header)<=MAX_SAMPLE_FIELDS
        elif p.suffix.lower()=='.parquet':
            try:
                import pyarrow.parquet as pq
                meta=pq.ParquetFile(p);row['row_count']=meta.metadata.num_rows;row['fields']=[{'name':f.name,'type':str(f.type)} for f in meta.schema_arrow][:MAX_SAMPLE_FIELDS];row['schema_complete']=len(meta.schema_arrow)<=MAX_SAMPLE_FIELDS
            except ImportError:row['status']='METADATA_READER_UNAVAILABLE'
        elif p.suffix.lower()=='.json':
            if p.stat().st_size>MAX_JSON_BYTES:row['status']='SCHEMA_REVIEW_SIZE_LIMIT';return row
            obj=read_json(p);row['sha256']=file_hash(p)
            fields=obj.get('properties') if isinstance(obj,dict) else None
            if isinstance(fields,dict):row['fields']=[{'name':k,'type':v.get('type','unknown') if isinstance(v,dict) else 'unknown','required':k in obj.get('required',[])} for k,v in list(fields.items())[:MAX_SAMPLE_FIELDS]];row['schema_complete']=len(fields)<=MAX_SAMPLE_FIELDS;row['status']='DECLARED_SCHEMA'
            else:
                sample=obj[0] if isinstance(obj,list) and obj else obj
                if isinstance(sample,dict):row['fields']=[{'name':k,'type':type(v).__name__,'basis':'SAMPLE_ONLY'} for k,v in list(sample.items())[:MAX_SAMPLE_FIELDS]]
                row['status']='SAMPLE_ONLY'
            def walk_catalog(value,trail='',depth=0):
                if depth>30 or len(row['catalog_entries'])>=MAX_SAMPLE_FIELDS:return
                if isinstance(value,dict):
                    keys=set(value)
                    if keys & {'formula','formula_text','indicator','indicator_id','chart_type','chart_id','x_axis','y_axis'}:
                        row['catalog_entries'].append({'key':trail,'definition':{k:public_value(k,v) for k,v in value.items()},'state':'DECLARED_NOT_EXECUTED'})
                    for k,v in value.items():walk_catalog(v,trail+'.'+str(k),depth+1)
                elif isinstance(value,list):
                    for i,v in enumerate(value):walk_catalog(v,trail+f'[{i}]',depth+1)
            if row['owner'] in ('VQG','VAP'):walk_catalog(obj)
            if isinstance(obj,dict) and obj.get('direction') in ('INPUT','OUTPUT'):row['direction']=obj['direction']
        else:row['status']='UNKNOWN_FORMAT'
    except Exception as e:row['status']='READ_ERROR';row['error']=str(e)
    return row


def discover_skills(items):
    rows=copy.deepcopy(SKILL_CATALOG)
    for item in items:
        p=Path(item['path'])
        if p.name!='SKILL.md':continue
        try:
            text=p.read_text(encoding='utf-8-sig')[:16000];name=re.search(r'^name:\s*(.+)',text,re.M);description=re.search(r'^description:\s*(.+)',text,re.M)
            group='跨平台';low=str(p).lower()
            if '.claude' in low:group='Claude'
            elif '.copilot' in low or '.github' in low:group='Copilot'
            elif '.gemini' in low:group='Gemini'
            elif '.codex' in low:group='ChatGPT'
            rows.append({'id':stable_id('SKILL',str(p)),'platform':group,'name':name.group(1).strip() if name else p.parent.name,'version':'UNDECLARED','purpose':description.group(1).strip() if description else '待補用途','systems':['VCGC'],'state':'LOCAL_FILE_FOUND','evidence':str(p),'sha256':file_hash(p),'how':'本地檔案存在；仍需平台載入和實際呼叫證據','updated_at':datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat()})
        except OSError:continue
    return rows


def dependency_graph(rows):
    by_module=collections.defaultdict(list)
    for row in rows:by_module[Path(row['path']).stem].append(row['id'])
    edges=[]
    for row in rows:
        for module in row.get('imports',[]):
            matches=by_module.get(module.split('.')[-1],[])
            edges.append({'from':row['id'],'to':matches[0] if len(matches)==1 else None,'module':module,'resolution':'LOCAL_EXACT_CANDIDATE' if len(matches)==1 else 'AMBIGUOUS' if matches else 'EXTERNAL_OR_DYNAMIC'})
    return edges


def evidence_context(rows, artifacts, tools):
    return {'sources':digest({r['id']:r.get('sha256') for r in rows}),'data':digest({r['id']:{'bytes':r.get('bytes'),'mtime':r.get('updated_at'),'sha256':r.get('sha256')} for r in artifacts}),'rules':digest({'tools':tools,'matrix_engine':VERSION}),'environment':environment_fingerprint()}


def validate_receipt(receipt, rows_by_id, context, roots):
    row=copy.deepcopy(receipt);reasons=[];state='UNVERIFIED'
    try:
        entity=rows_by_id.get(receipt.get('entity_id'));stage=receipt.get('stage');evidence=receipt.get('assertions',[])
        if not entity or stage not in STAGES:raise ValueError('ENTITY_OR_STAGE_UNKNOWN')
        if receipt.get('schema')!='via.matrix.receipt/1':raise ValueError('RECEIPT_SCHEMA')
        if receipt.get('source_sha256')!=entity.get('sha256'):reasons.append('SOURCE_CHANGED')
        if receipt.get('context')!=context:reasons.append('DEPENDENCIES_DATA_RULES_OR_ENV_CHANGED')
        observed=datetime.fromisoformat(receipt['finished_at']);age=(datetime.now(timezone.utc)-observed).total_seconds()
        if age<0 or age>RECEIPT_TTL_HOURS*3600:reasons.append('OUTSIDE_VALIDITY_WINDOW')
        checks=receipt.get('checked_files',[])
        if not checks:raise ValueError('NO_HASHED_EVIDENCE_FILES')
        for check in checks:
            p=Path(check['path'])
            if not within(p,roots):raise ValueError('EVIDENCE_PATH_OUTSIDE_SCOPE')
            if not p.is_file() or file_hash(p)!=check.get('sha256'):reasons.append('EVIDENCE_FILE_CHANGED_OR_MISSING')
        if not evidence or any(not isinstance(a,dict) or a.get('passed') is not True for a in evidence):state='FAIL'
        elif receipt.get('exit_code')!=0:state='FAIL'
        elif reasons:state='STALE'
        else:state='PASS'
    except (ValueError,KeyError,TypeError,OSError) as e:reasons.append(str(e));state='UNVERIFIED'
    row.update(validation_state=state,validation_reasons=reasons,validated_at=utc_now());return row


def read_receipts(out, rows, context, roots):
    result=[];by_id={r['id']:r for r in rows}
    for p in sorted((Path(out)/'receipts').glob('*.json')):
        try:
            row=validate_receipt(read_json(p),by_id,context,list(roots)+[out]);row['receipt_path']=str(p);result.append(row)
        except (ValueError,OSError) as e:result.append({'receipt_path':str(p),'validation_state':'UNVERIFIED','error':str(e)})
    latest={}
    for row in result:
        key=(row.get('entity_id'),row.get('stage'))
        if key not in latest or row.get('finished_at','')>latest[key].get('finished_at',''):latest[key]=row
    for (eid,stage),receipt in latest.items():
        if eid in by_id and stage in STAGES:by_id[eid]['tests'][stage]=receipt['validation_state']
    return result


def apply_tool_proofs(rows, receipts, tools):
    pins={t['name']:t for t in tools if t.get('state') in ('LOCK_MATCH','LINE_ENDINGS_ONLY')}
    by_id={r['id']:r for r in rows}
    latest={}
    for receipt in receipts:
        if receipt.get('stage') not in ('INTEGRATION','SYSTEM'):continue
        eid=receipt.get('entity_id')
        if eid not in latest or receipt.get('finished_at','')>latest[eid].get('finished_at',''):latest[eid]=receipt
    for eid,receipt in latest.items():
        if receipt.get('validation_state')!='PASS' or eid not in by_id:continue
        row=by_id[eid];probes=receipt.get('tool_probes',{})
        for family in ('accelerator','network'):
            probe=probes.get(family,{});pin=pins.get(family,{})
            if family=='network' and row['owner']!='VDF' and not row['network'].get('outlets') and probe.get('source_sha256')==row.get('sha256') and probe.get('not_applicable') is True and probe.get('scope_complete') is True:
                row['network']['state']='NOT_APPLICABLE';row['network']['receipt_id']=receipt.get('id');continue
            if not pin.get('sha256') or probe.get('tool_sha256')!=pin['sha256'] or probe.get('source_sha256')!=row.get('sha256'):continue
            if not isinstance(probe.get('call_count'),int) or probe['call_count']<=0 or probe.get('output_validated') is not True:continue
            if family=='network':
                outlets={x['node_id'] for x in row.get('network',{}).get('outlets',[])};covered=set(probe.get('outlet_node_ids',[]))
                if not outlets.issubset(covered) or probe.get('denied_respected') is not True or probe.get('origins_verified') is not True:continue
                row['issues']=[i for i in row['issues'] if not (i['rule']=='NETWORK_ROUTE_UNVERIFIED' and i.get('node_id') in covered)]
            row[family]['state']='RUNTIME_VERIFIED';row[family]['receipt_id']=receipt.get('id');row[family]['verified_at']=receipt.get('finished_at')


def fraction(numerator, denominator):
    return {'numerator':numerator,'denominator':denominator,'ratio':numerator/denominator if denominator else None,'state':'MEASURED' if denominator else 'NOT_APPLICABLE_OR_EMPTY'}


def rollup(rows, discovery_errors):
    executable=[r for r in rows if Path(r['path']).suffix.lower()!='.psd1'];net=[r for r in executable if r.get('network',{}).get('required')];unknown_net=[r for r in executable if r.get('network',{}).get('state') in ('UNKNOWN','APPLICABILITY_REVIEW')]
    parsed=sum(r.get('parse_state')=='PARSED' for r in rows);full=sum(r.get('parse_state')=='PARSED' and not r.get('nodes_truncated') for r in rows)
    metrics={'ast_parse':fraction(parsed,len(rows)),'ast_detail':fraction(full,len(rows)),'accelerator_static':fraction(sum(r.get('accelerator',{}).get('state')=='STATIC_CANDIDATE' for r in executable),len(executable)),'accelerator_runtime':fraction(sum(r.get('accelerator',{}).get('state')=='RUNTIME_VERIFIED' for r in executable),len(executable)),'network_static':fraction(sum(r['network']['state']=='STATIC_CANDIDATE' for r in net),len(net)),'network_runtime':fraction(sum(r['network']['state']=='RUNTIME_VERIFIED' for r in net),len(net)),'network_applicability_unresolved':len(unknown_net),'inventory_complete':not discovery_errors,'discovery_errors':len(discovery_errors)}
    for row in rows:
        states=list(row['tests'].values());errors=any(i['severity']=='ERROR' for i in row['issues'])
        row['status']='RED' if errors or 'FAIL' in states else 'GREEN' if states and all(s=='PASS' for s in states) and row.get('parse_state')=='PARSED' and not row['issues'] and row.get('accelerator',{}).get('state')=='RUNTIME_VERIFIED' and row.get('network',{}).get('state') in ('NOT_APPLICABLE','RUNTIME_VERIFIED') else 'YELLOW'
    return metrics


def native_inventory(via):
    if not via:return {'stations':[],'registries':[],'status':'NATIVE_ROOT_NOT_FOUND'}
    folder=Path(via)/'supportive modules/registry';registries=[];stations=[]
    for family in ('VIA_VCGC_FunctionInventory_SSOT','VIA_Requirements_SSOT','VIA_Workflow_VCGC_SSOT'):
        p=tail(folder,family+'_v*.json')
        if not p:continue
        obj=read_json(p,{});registries.append({'name':p.name,'path':str(p),'version':obj.get('version'),'sha256':file_hash(p),'updated_at':obj.get('ts')})
        if 'stations' in obj:stations=obj['stations']
    return {'stations':stations,'registries':registries,'status':'READ_ONLY_DISCOVERED'}


def scan(roots, out, frontend=None, workers=None, activate=False):
    started=time.monotonic();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True);roots=list(dict.fromkeys(str(Path(r).expanduser().resolve()) for r in roots))
    with workspace_lock(out):
        items,excluded,errors=enumerate_tree(roots,out);source_items=[x for x in items if Path(x['path']).suffix.lower() in SOURCE_EXTENSIONS];data_items=[x for x in items if Path(x['path']).suffix.lower() in DATA_EXTENSIONS]
        vias=discover_via(roots);via=vias[0] if vias else None;tools=inspect_tools(via);budget=resource_budget(workers);acceleration=activate_accelerator(via,tools) if activate else {'builtin':'BOUNDED_EXECUTOR_ACTIVE','external':'NOT_REQUESTED'}
        print(f'[VCGC] 來源檔 {len(source_items)}；資料契約候選 {len(data_items)}；平行上限 {budget["workers"]}',flush=True)
        cache=sqlite3.connect(out/'analysis_cache.sqlite');cache.execute('CREATE TABLE IF NOT EXISTS cache(path TEXT PRIMARY KEY, body TEXT NOT NULL)');rows=[]
        try:
            ps=powershell_parse([x['path'] for x in source_items if Path(x['path']).suffix.lower()!='.py'],out)
        except Exception as e:ps={};errors.append({'path':'powershell-parser','reason':'PARSER_RUN_FAILED','detail':str(e)})
        with concurrent.futures.ThreadPoolExecutor(max_workers=budget['workers']) as pool:
            for offset in range(0,len(source_items),budget['source_batch_size']):
                batch=source_items[offset:offset+budget['source_batch_size']];futures=[]
                for item in batch:
                    prior=cache.execute('SELECT body FROM cache WHERE path=?',(item['path'],)).fetchone();cached=json.loads(prior[0]) if prior else None
                    futures.append(pool.submit(analyze_file,item,ps,cached))
                for future in futures:
                    row=future.result();row['analysis_version']=ANALYZER_REVISION;rows.append(row);cache.execute('INSERT OR REPLACE INTO cache VALUES (?,?)',(row['path'],json.dumps(row,ensure_ascii=False)))
                cache.commit()
                if offset%max(1,budget['source_batch_size']*20)==0:print(f'[AST] {len(rows)}/{len(source_items)}',flush=True)
        cache.close();artifacts=[]
        with concurrent.futures.ThreadPoolExecutor(max_workers=budget['workers']) as pool:
            for offset in range(0,len(data_items),budget['source_batch_size']):artifacts.extend(pool.map(inspect_artifact,data_items[offset:offset+budget['source_batch_size']]))
        context=evidence_context(rows,artifacts,tools);receipts=read_receipts(out,rows,context,roots);apply_tool_proofs(rows,receipts,tools);metrics=rollup(rows,errors);edges=dependency_graph(rows)
        issues=[dict(i,entity_id=r['id'],owner=r['owner'],file=r['path']) for r in rows for i in r['issues']]
        for row in rows:
            detail={'id':row['id'],'sha256':row.get('sha256'),'nodes':row['nodes'],'definitions':row.get('definitions',[]),'calls':row.get('calls',[])};key=digest(row['id'].encode())
            atomic_json(out/'nodes'/f'{key}.json',detail);row['detail_file']=f'nodes/{key}.json';row['nodes']=row['nodes'][:INLINE_NODES];row['inline_limited']=row.get('node_count',0)>INLINE_NODES;row['call_count']=len(row.get('calls',[]));row['calls']=row.get('calls',[])[:INLINE_NODES]
        native=native_inventory(via);previous=read_json(out/'snapshot.json',{},max_bytes=128*1024*1024);previous_hashes={x['id']:x.get('sha256') for x in previous.get('files',[])}
        delta={'added':[r['id'] for r in rows if r['id'] not in previous_hashes],'changed':[r['id'] for r in rows if r['id'] in previous_hashes and r.get('sha256')!=previous_hashes[r['id']]],'removed':sorted(set(previous_hashes)-{r['id'] for r in rows})}
        state={'schema':'via.matrix.snapshot/1','version':VERSION,'run_id':str(uuid.uuid4()),'generated_at':utc_now(),'reference_commit':REFERENCE_COMMIT,'source':'LOCAL_SCAN','roots':roots,'systems':SYSTEMS,'matrices':MATRICES,'files':rows,'artifacts':artifacts,'issues':issues,'receipts':receipts,'dependencies':edges,'metrics':metrics,'tools':tools,'skills':discover_skills(items),'merges':MERGE_BASELINE,'native':native,'registration':read_json(out/'registration.json',{'state':'NOT_INSTALLED'}),'excluded':excluded,'discovery_errors':errors,'context':context,'delta':delta,'performance':dict(budget,elapsed_seconds=round(time.monotonic()-started,3),cache_hits=sum(r.get('cache_reused',False) for r in rows),acceleration=acceleration),'scope_note':'本地發現與證據；未執行的原生系統仍為 NOT_RUN。依賴目錄排除、連結與大小限制均列入報告。'}
        state['overall']='RED' if any(r['status']=='RED' for r in rows) else 'YELLOW' if errors or not rows or any(r['status']!='GREEN' for r in rows) else 'GREEN'
        atomic_json(out/'snapshot.json',state);audit_event(out,'SCAN',{'run_id':state['run_id'],'files':len(rows),'context':context,'overall':state['overall']});export_reports(state,out,frontend);return state


def export_reports(state, out, frontend=None):
    out=Path(out);fields=['status','id','name','version','owner','updated_at','path','parse_state','node_count','UNIT','INTEGRATION','SYSTEM','RESULT_VALIDATION','CLOSE_OUT']
    buffer=io.StringIO(newline='');writer=csv.DictWriter(buffer,fieldnames=fields,extrasaction='ignore');writer.writeheader()
    for row in state['files']:writer.writerow(dict(row,**row['tests']))
    atomic_write(out/'files.csv',b'\xef\xbb\xbf'+buffer.getvalue().encode('utf-8'))
    template=Path(frontend) if frontend else Path(__file__).with_name(FRONTEND_NAME)
    if not template.is_file():
        installed=Path(__file__).parent.parent/'VCGC_Matrix'/FRONTEND_NAME
        if installed.is_file():template=installed
    if template.is_file():
        html=template.read_text(encoding='utf-8');payload=json.dumps(state,ensure_ascii=False).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
        html=re.sub(r'(<script id="via-data" type="application/json">).*?(</script>)',lambda m:m.group(1)+payload+m.group(2),html,flags=re.S)
        atomic_write(out/FRONTEND_NAME,html)
    parquet={'state':'NOT_AVAILABLE','reason':'pyarrow optional'}
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        records=[{k:str(r.get(k,'')) for k in fields[:9]}|{k:r['tests'][k] for k in STAGES} for r in state['files']]
        if records:
            tmp=out/'files.parquet.tmp';pq.write_table(pa.Table.from_pylist(records),tmp);os.replace(tmp,out/'files.parquet');parquet={'state':'WRITTEN','rows':len(records)}
        else:parquet={'state':'EMPTY','rows':0}
    except ImportError:pass
    atomic_json(out/'exports.json',{'json':'snapshot.json','csv':'files.csv','parquet':parquet})

# 05 · Bounded process runner; explicit assertion-based U/I/S/R/C receipts.
def run_process(argv, cwd, out, label, timeout=MAX_COMMAND_SECONDS, extra_env=None):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);log=out/(re.sub(r'[^A-Za-z0-9_-]','_',label)+'_'+uuid.uuid4().hex[:10]+'.log');env=os.environ.copy();env.update({'PYTHONIOENCODING':'utf-8','PYTHONDONTWRITEBYTECODE':'1','VIA_FROM_VCGC':'YES','VIA_NO_OPEN':'1'});env.update(extra_env or {})
    started=time.monotonic();timed_out=False
    with log.open('wb') as stream:
        proc=subprocess.Popen([str(x) for x in argv],cwd=str(cwd),env=env,stdout=stream,stderr=subprocess.STDOUT,shell=False,start_new_session=os.name!='nt',creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name=='nt' else 0)
        last=0
        while proc.poll() is None:
            elapsed=time.monotonic()-started
            if elapsed>timeout:
                timed_out=True
                if os.name=='nt':subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True,timeout=30)
                else:
                    with contextlib.suppress(ProcessLookupError):os.killpg(proc.pid,signal.SIGTERM)
                    try:proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        with contextlib.suppress(ProcessLookupError):os.killpg(proc.pid,signal.SIGKILL)
                proc.wait(timeout=30);break
            if elapsed-last>=HEARTBEAT_SECONDS:print(f'[心跳] {label} {elapsed:.0f}s · log {log.name}',flush=True);last=elapsed
            time.sleep(0.2)
    return {'label':label,'argv':list(map(str,argv)),'exit_code':proc.returncode,'elapsed_seconds':round(time.monotonic()-started,3),'timed_out':timed_out,'log':str(log),'log_sha256':file_hash(log),'finished_at':utc_now(),'state':'TIMEOUT' if timed_out else 'RETURNED_ZERO' if proc.returncode==0 else 'NONZERO'}


def resolve_in_roots(value, base, roots):
    p=Path(value);p=(Path(base)/p).resolve() if not p.is_absolute() else p.resolve()
    if not within(p,roots):raise ValueError('PATH_OUTSIDE_SCOPE: '+str(p))
    return p


def select_json(obj, selector):
    value=obj
    for key in selector.split('.') if selector else []:value=value[int(key)] if isinstance(value,list) else value[key]
    return value


def run_test_plan(plan_path, roots, out):
    out=Path(out).resolve();plan=read_json(plan_path);snapshot=read_json(out/'snapshot.json',max_bytes=128*1024*1024)
    if not snapshot:raise ValueError('SCAN_REQUIRED')
    if plan.get('schema')!='via.matrix.test-plan/1':raise ValueError('TEST_PLAN_SCHEMA')
    bypath={str(Path(r['path']).resolve()):r for r in snapshot['files']};results=[]
    for test in plan.get('tests',[]):
        entity=resolve_in_roots(test['entity'],Path(plan_path).parent,roots);script=resolve_in_roots(test['script'],Path(plan_path).parent,roots);stage=test['stage']
        if stage not in STAGES or str(entity) not in bypath:raise ValueError('TEST_ENTITY_OR_STAGE')
        row=bypath[str(entity)]
        if file_hash(entity)!=row['sha256'] or file_hash(script)!=test.get('script_sha256'):raise ValueError('TEST_BASE_HASH_CHANGED')
        if script.suffix.lower()=='.py':prefix=[sys.executable,str(script)]
        elif script.suffix.lower()=='.ps1':
            ps=shutil.which('pwsh')
            if not ps:raise RuntimeError('POWERSHELL_7_REQUIRED')
            prefix=[ps,'-NoProfile','-NonInteractive','-File',str(script)]
        else:raise ValueError('TEST_SCRIPT_TYPE')
        args=test.get('args',[])
        if not isinstance(args,list) or not all(isinstance(x,str) for x in args):raise ValueError('TEST_ARGS_TYPE')
        assertions_spec=test.get('assertions',[])
        if not assertions_spec:raise ValueError('EXPLICIT_ASSERTIONS_REQUIRED')
        evidence_path=resolve_in_roots(test['result_json'],out,list(roots)+[out]);before=file_hash(evidence_path) if evidence_path.is_file() else None
        checked=[{'path':str(script),'sha256':file_hash(script)}];inputs=[]
        for item in test.get('input_files',[]):
            p=resolve_in_roots(item['path'],Path(plan_path).parent,roots)
            if file_hash(p)!=item['sha256']:raise ValueError('TEST_INPUT_HASH_CHANGED')
            inputs.append({'path':str(p),'sha256':item['sha256']})
        command=run_process(prefix+args,script.parent,out/'logs',test.get('id','test'),min(MAX_COMMAND_SECONDS,int(test.get('timeout',MAX_COMMAND_SECONDS))))
        assertions=[];tool_probes={}
        try:
            output=read_json(evidence_path)
            if output is None:raise ValueError('RESULT_JSON_MISSING')
            checked.append({'path':str(evidence_path),'sha256':file_hash(evidence_path)});tool_probes=output.get('tool_probes',{}) if isinstance(output,dict) else {}
            for a in assertions_spec:
                actual=select_json(output,a['path']);expected=a['equals'];assertions.append({'name':a.get('name',a['path']),'actual':actual,'expected':expected,'passed':type(actual)==type(expected) and actual==expected})
            # A prior unchanged result requires a fresh run ID in the output; absence is not proof.
            assertions.append({'name':'fresh_result','passed':before!=file_hash(evidence_path),'basis':'result JSON must change, preferably include a new run_id'})
        except (ValueError,KeyError,TypeError,OSError) as e:assertions.append({'name':'result_read','passed':False,'detail':str(e)})
        checked+=inputs;checked.append({'path':command['log'],'sha256':command['log_sha256']})
        receipt={'schema':'via.matrix.receipt/1','id':str(uuid.uuid4()),'entity_id':row['id'],'stage':stage,'source_sha256':row['sha256'],'context':snapshot['context'],'finished_at':command['finished_at'],'exit_code':command['exit_code'],'assertions':assertions,'checked_files':checked,'tool_probes':tool_probes,'command':command}
        validated=validate_receipt(receipt,{row['id']:row},snapshot['context'],list(roots)+[out]);atomic_json(out/'receipts'/(receipt['id']+'.json'),receipt);results.append(validated)
    atomic_json(out/'last_test_run.json',results);return results

# 06 · Native console compatibility. No subprocess shell; old verbs retain old owners.
def prior_console_path(folder=None):
    folder=Path(folder) if folder else Path(__file__).resolve().parent
    return max((p for p in folder.glob(ENGINE_FAMILY+'_v*.py') if 0<=version_number(p)<int(VERSION[1:])),key=version_number,default=None)


def load_prior():
    global _PRIOR_MODULE
    if _PRIOR_MODULE is None:
        p=prior_console_path()
        if p is None:raise RuntimeError('NATIVE_PRIOR_CONSOLE_MISSING; matrix 可獨立使用，舊動詞需安裝於原生 registry')
        spec=importlib.util.spec_from_file_location(ENGINE_FAMILY+'_prior_'+VERSION,p);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module);_PRIOR_MODULE=module
    return _PRIOR_MODULE


def __getattr__(name):
    if name.startswith('__') or name in ('setUpModule','tearDownModule','load_tests') or prior_console_path() is None:raise AttributeError(name)
    return getattr(load_prior(),name)


def native_command(via, verb, out, label=None, console=None):
    p=Path(console) if console else tail(Path(via)/'supportive modules/registry',ENGINE_FAMILY+'_v*.py')
    if p is None:raise RuntimeError('NATIVE_CONSOLE_MISSING')
    return run_process([sys.executable,str(p)]+list(verb),via,Path(out)/'native_logs',label or '-'.join(verb[:2]))


def native_suite(via, out, mode='quick'):
    if not via:raise RuntimeError('NATIVE_ROOT_NOT_FOUND')
    sequence=[['token'],['handoff','check'],['functions']]
    sequence+=([['test','--quick']] if mode=='quick' else [['token','chain',ENGINE_FAMILY],['ssot','panorama'],['test','--quick']])
    results=[]
    for command in sequence:
        row=native_command(via,command,out);results.append(row)
        if row['exit_code'] not in (0,2):break
    atomic_json(Path(out)/'native_checks.json',{'results':results,'state':'COMMANDS_COMPLETED_REQUIRES_NATIVE_RECEIPTS' if len(results)==len(sequence) and all(r['exit_code']==0 for r in results) else 'BLOCKED_OR_WARNING','note':'命令退出碼與原生收據分開；未轉成 U/I/S/R/C 通過證據'});return results

# 07 · Versioned integration transaction, native registries and rollback.
def next_registry(folder, family):
    current=tail(folder,family+'_v*.json')
    if current is None:raise RuntimeError('NATIVE_REGISTRY_MISSING: '+family)
    obj=read_json(current);num=version_number(current)+1;target=Path(folder)/(family+f'_v{num:04d}.json');obj['prior']=current.name;obj['version']=f'v{num:04d}';obj['ts']=utc_now();obj['matrix_integration']={'engine':ENGINE_FAMILY+'_'+VERSION,'state':'PENDING_NATIVE_VALIDATION','source_commit':REFERENCE_COMMIT,'central_id':None};return current,target,obj


def prepare_install(via, frontend):
    via=Path(via).resolve();folder=via/'supportive modules/registry';current=tail(folder,ENGINE_FAMILY+'_v*.py');self_path=Path(__file__).resolve();target=folder/(ENGINE_FAMILY+'_'+VERSION+'.py')
    if current and version_number(current)>int(VERSION[1:]):raise RuntimeError('NEWER_NATIVE_CONSOLE_PRESENT; rebase integration before install')
    if current and current==target and file_hash(current)==file_hash(self_path):
        installed_html=via/'supportive modules/VCGC_Matrix'/FRONTEND_NAME
        if not installed_html.is_file() or file_hash(installed_html)!=file_hash(frontend):raise RuntimeError('INSTALLED_FRONTEND_MISSING_OR_CHANGED')
        inventory_path=tail(folder,'VIA_VCGC_FunctionInventory_SSOT_v*.json')
        if inventory_path is None:raise RuntimeError('INSTALLED_INVENTORY_MISSING')
        inventory=read_json(inventory_path,{})
        if not any(x.get('id')=='C-multimatrix-'+VERSION for x in inventory.get('stations',[])):raise RuntimeError('INSTALLED_STATION_MISSING')
        return {'idempotent':True,'writes':[],'guards':[],'via':str(via)}
    if current is None or version_number(current)!=192:raise RuntimeError('EXPECTED_NATIVE_v0192; preserve current console and request compatible upgrade')
    template=Path(frontend)
    if not template.is_file():raise FileNotFoundError(template)
    writes=[{'path':str(target),'bytes':self_path.read_bytes()},{'path':str(via/'supportive modules/VCGC_Matrix'/FRONTEND_NAME),'bytes':template.read_bytes()}];guards=[{'path':str(current),'sha256':file_hash(current)}]
    reqcur,reqpath,req=next_registry(folder,'VIA_Requirements_SSOT');codes=[int(m.group(1)) for r in req.get('requirements',[]) if (m:=re.search(r'VCGC-REQ(\d+)',str(r.get('code',''))))];code='VCGC-REQ'+str(max(codes,default=0)+1).zfill(3)
    req.setdefault('requirements',[]).append({'code':code,'subsystem':'VCGC','status':'PARTIAL','name':'五系統多矩陣整合與證據治理 '+VERSION,'homes':['supportive modules/registry/'+target.name,'supportive modules/VCGC_Matrix/'+FRONTEND_NAME],'modules':[target.name],'evidence':[],'next':'Windows 原生 AST / 加速 / 網路與 U/I/S/R/C 證據驗收','ts':utc_now(),'ssot_id':None,'matrix_integration':True});req['matrix_integration']['requirement_code']=code;req['tally']=dict(collections.Counter(r.get('status','UNKNOWN') for r in req['requirements']))
    invcur,invpath,inv=next_registry(folder,'VIA_VCGC_FunctionInventory_SSOT');inv.setdefault('stations',[]).append({'id':'C-multimatrix-'+VERSION,'name':'VCGC 五系統多矩陣自測 '+VERSION,'argv':['matrix','selftest'],'timeout':180,'deps':['supportive modules/registry/'+target.name,'supportive modules/VCGC_Matrix/'+FRONTEND_NAME],'requirement':code})
    wfcur,wfpath,wf=next_registry(folder,'VIA_Workflow_VCGC_SSOT');numbers=[int(m.group(1)) for w in wf.get('workflows',[]) if (m:=re.search(r'VCGC-WKF(\d+)',str(w.get('code',''))))];wfcode='VCGC-WKF'+str(max(numbers,default=0)+1).zfill(3)
    wf.setdefault('workflows',[]).append({'code':wfcode,'alias':'multi_matrix_governance','kind':'procedure','name':'多矩陣掃描、驗證與註冊','spec':{'goal':'統一 VCGC 證據，各子系統維持獨立','requirements':[code],'acceptance':['完整枚舉','原生 AST','逐檔加速與網路證據','UNIT/INTEGRATION/SYSTEM/RESULT_VALIDATION/CLOSE_OUT 全部有收據']},'plan':{'enter':['token','handoff check'],'exit':['test --quick','checkpoint'],'order':['scan','verify','register','audit']},'steps':[{'code':wfcode+'-01','alias':'scan','engine':target.name,'verb':'matrix scan','evidence':'snapshot.json'},{'code':wfcode+'-02','alias':'validate','engine':target.name,'verb':'matrix run-tests','evidence':'receipts/*.json'},{'code':wfcode+'-03','alias':'registration','engine':target.name,'verb':'matrix register','evidence':'registration.json'}],'tests':{'self':['matrix selftest'],'cross':['test --quick'],'real':[],'real_run':False}})
    for before,after,obj in ((reqcur,reqpath,req),(invcur,invpath,inv),(wfcur,wfpath,wf)):
        guards.append({'path':str(before),'sha256':file_hash(before)});writes.append({'path':str(after),'bytes':json_bytes(obj)})
    return {'idempotent':False,'writes':writes,'guards':guards,'via':str(via),'requirement':code,'workflow':wfcode,'official_central_id':None,'native_prior':str(current)}


def commit_transaction(plan, out, fail_after=None):
    out=Path(out);created=[];record={'id':str(uuid.uuid4()),'at':utc_now(),'state':'PREPARED','created':[],'guards':plan['guards']}
    for guard in plan['guards']:
        if file_hash(guard['path'])!=guard['sha256']:raise RuntimeError('BASE_HASH_CHANGED: '+guard['path'])
    for item in plan['writes']:
        if Path(item['path']).exists():raise FileExistsError('VERSION_COLLISION: '+item['path'])
    try:
        for i,item in enumerate(plan['writes']):
            p=Path(item['path']);p.parent.mkdir(parents=True,exist_ok=True)
            # O_EXCL prevents overwrite if another process creates the version after preflight.
            with p.open('xb') as f:f.write(item['bytes']);f.flush();os.fsync(f.fileno())
            created.append({'path':str(p),'sha256':digest(item['bytes'])})
            if fail_after is not None and i==fail_after:raise RuntimeError('INJECTED_TRANSACTION_FAILURE')
        record.update(state='COMMITTED',created=created)
    except Exception:
        for item in reversed(created):
            if Path(item['path']).is_file() and file_hash(item['path'])==item['sha256']:Path(item['path']).unlink()
        record.update(state='ROLLED_BACK',created=created);atomic_json(out/'install_transaction.json',record);raise
    atomic_json(out/'install_transaction.json',record);return record


def rollback_install(out):
    out=Path(out);record=read_json(out/'install_transaction.json')
    if not record or record.get('state')!='COMMITTED':raise RuntimeError('NO_COMMITTED_TRANSACTION')
    with workspace_lock(out):
        for item in record['created']:
            if not Path(item['path']).is_file() or file_hash(item['path'])!=item['sha256']:raise RuntimeError('ROLLBACK_BLOCKED_CHANGED_FILE: '+item['path'])
        for item in reversed(record['created']):Path(item['path']).unlink()
        record['state']='ROLLED_BACK';record['rollback_at']=utc_now();atomic_json(out/'install_transaction.json',record);audit_event(out,'ROLLBACK',{'transaction':record['id']})
    return record


def register_native(via, out):
    results=[]
    # Let the native governance engine own central IDs and any numbering mutation.
    sequence=[['registry-sync','--apply']]
    transaction=read_json(Path(out)/'install_transaction.json',{})
    scoped=[str(Path(x['path']).relative_to(Path(via))) for x in transaction.get('created',[]) if within(x['path'],[via])]
    if scoped:
        sequence.append(['run','CGC_MDL237_NumberingSystem','--apply','--scope']+scoped)
        sequence.append(['run','CGC_MDL237_NumberingSystem','audit','--json'])
    sequence += [['ssot','panorama'],['test','--quick'],['handoff','check']]
    for args in sequence:
        result=native_command(via,args,out);results.append(result)
        if result['exit_code']!=0:break
    row={'state':'NATIVE_COMMANDS_COMPLETED_PENDING_CLOSEOUT' if len(results)==len(sequence) and all(r['exit_code']==0 for r in results) else 'PENDING_NATIVE_REPAIR','at':utc_now(),'results':results,'official_central_id':None,'closeout':'PENDING_NATIVE_AUDIT_REVIEW_AND_CHECKPOINT','note':'不自行製造 SSOT 中央編號；完整編號與 checkpoint 由既有中央治理流程裁定。'}
    atomic_json(Path(out)/'registration.json',row);return row


def install(roots, out, frontend, apply=False):
    vias=discover_via(roots)
    if not vias:raise RuntimeError('WINDOWS_VIA_ROOT_NOT_FOUND; --roots 可指定實際根目錄')
    via=vias[0];out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    with workspace_lock(out):
        plan=prepare_install(via,frontend);public={k:v for k,v in plan.items() if k!='writes'};public['writes']=[{'path':x['path'],'sha256':digest(x['bytes']),'bytes':len(x['bytes'])} for x in plan['writes']];atomic_json(out/'install_plan.json',public)
        if not apply or plan['idempotent']:return dict(public,state='ALREADY_INSTALLED' if plan['idempotent'] else 'PLAN_READY')
        checks=native_suite(via,out,'install')
        if len(checks)<6 or any(x['exit_code']!=0 for x in checks):raise RuntimeError('NATIVE_PREFLIGHT_BLOCKED; see native_checks.json, no integration files written')
        # Prevent a registry tail race as well as hash races.
        fresh=prepare_install(via,frontend)
        if [x['path'] for x in fresh['writes']]!=[x['path'] for x in plan['writes']]:raise RuntimeError('REGISTRY_TAIL_CHANGED')
        record=commit_transaction(plan,out);audit_event(out,'INSTALL',{'transaction':record['id'],'files':record['created']})
    registration=register_native(via,out);return dict(public,state='INSTALLED',registration=registration)

# 08 · File-backed UI actions; no web server and no arbitrary shell actions.
def create_session(out, roots):
    out=Path(out);session={'schema':'via.matrix.session/1','session_id':str(uuid.uuid4()),'token':secrets.token_urlsafe(32),'created_at':utc_now(),'roots':[str(Path(x).resolve()) for x in roots],'actions':['scan','native-quick','selftest','export'],'expires_at':(datetime.now(timezone.utc)+timedelta(hours=12)).isoformat()}
    atomic_json(out/'session.json',session);(out/'jobs').mkdir(exist_ok=True);return session


def validate_job(job, session, completed):
    if not isinstance(job,dict) or job.get('schema')!='via.matrix.job/1':raise ValueError('JOB_SCHEMA')
    if job.get('session_id')!=session['session_id'] or not secrets.compare_digest(str(job.get('token','')),session['token']):raise ValueError('SESSION_MISMATCH')
    if datetime.now(timezone.utc)>datetime.fromisoformat(session['expires_at']):raise ValueError('SESSION_EXPIRED')
    jid=job.get('id','')
    if not re.fullmatch(r'[A-Za-z0-9_-]{8,80}',jid) or jid in completed:raise ValueError('JOB_REPLAY_OR_ID')
    if job.get('action') not in session['actions']:raise ValueError('ACTION_NOT_ALLOWED')
    if set(job)-{'schema','session_id','token','id','action','created_at'}:raise ValueError('UNEXPECTED_JOB_PARAMETERS')
    return jid


def process_jobs(session, out, frontend):
    out=Path(out);completed=set(p.stem for p in (out/'job_results').glob('*.json'));results=[]
    for p in sorted((out/'jobs').glob('*.json')):
        try:
            if p.is_symlink():raise ValueError('JOB_SYMLINK')
            job=read_json(p,max_bytes=16000);jid=validate_job(job,session,completed)
            if p.stem!=jid:raise ValueError('JOB_FILENAME_ID_MISMATCH')
            # Reserve before execution. Interrupted jobs require a new job ID.
            atomic_json(out/'job_results'/f'{jid}.json',{'id':jid,'state':'RUNNING','started_at':utc_now()});completed.add(jid)
            if job['action']=='scan':value={'run_id':scan(session['roots'],out,frontend)['run_id']}
            elif job['action']=='native-quick':value=native_suite(next(iter(discover_via(session['roots'])),None),out)
            elif job['action']=='selftest':value=run_selftest(out/'selftest.json')
            else:
                value=read_json(out/'snapshot.json',max_bytes=128*1024*1024);export_reports(value,out,frontend);value={'state':'EXPORTED'}
            result={'id':jid,'state':'COMPLETED','action':job['action'],'finished_at':utc_now(),'result':value};atomic_json(out/'job_results'/f'{jid}.json',result);results.append(result)
        except Exception as e:
            result={'id':p.stem,'state':'REJECTED_OR_FAILED','error':str(e),'finished_at':utc_now()};atomic_json(out/'rejected_jobs'/(p.stem+'.json'),result);results.append(result)
            if re.fullmatch(r'[A-Za-z0-9_-]{8,80}',p.stem) and (out/'job_results'/(p.stem+'.json')).exists():atomic_json(out/'job_results'/(p.stem+'.json'),result)
        finally:
            destination=out/'processed_jobs'/p.name;destination.parent.mkdir(exist_ok=True);os.replace(p,destination)
    return results


def watch(roots, out, frontend):
    with workspace_lock(Path(out)/'watch_control'):
        session=create_session(out,roots);print('[VCGC] 零伺服器操作已啟動；HTML 選擇此資料夾：'+str(Path(out).resolve()),flush=True)
        try:
            while True:process_jobs(session,out,frontend);time.sleep(WATCH_INTERVAL_SECONDS)
        except KeyboardInterrupt:print('[VCGC] 監看已停止；PowerShell 視窗保留。')
        finally:
            session['expires_at']=utc_now();atomic_json(Path(out)/'session.json',session)

# 09 · Actionable repair plans. Native specialised engines retain ownership.
def repair_plan(state, out):
    steps=[]
    for row in state['files']:
        if row.get('parse_state')!='PARSED':steps.append({'entity_id':row['id'],'path':row['path'],'stage':'SYNTAX_FIRST','severity':'HIGH','base_sha256':row.get('sha256'),'action':'先使用原生語法解析器修正並重新掃描；語法未通過不得注入','state':'PENDING'})
        if Path(row['path']).suffix.lower()!='.psd1' and row.get('accelerator',{}).get('state')!='RUNTIME_VERIFIED':steps.append({'entity_id':row['id'],'path':row['path'],'stage':'ACCELERATOR','severity':'REVIEW','base_sha256':row.get('sha256'),'action':'透過既有 Celeritas/SuperAccel 導入流程接上鎖定版；以實際 API 呼叫及前後效能、輸出等價收據驗證。只有 marker 不算通過。','ast_anchors':[d['node_id'] for d in row.get('definitions',[])[:50]],'state':'PENDING_RUNTIME_PROOF'})
        if row.get('network',{}).get('required'):steps.append({'entity_id':row['id'],'path':row['path'],'stage':'NETWORK','severity':'REVIEW','base_sha256':row.get('sha256'),'action':'逐出口轉接鎖定網路工具；測試 timeout/retry/cache/rate-limit/DENY 不繞過與真實來源。VDF 所有引擎列入。','ast_anchors':[x['node_id'] for x in row['network'].get('outlets',[])],'state':'PENDING_RUNTIME_PROOF'})
    result={'schema':'via.matrix.repair-plan/1','version':VERSION,'at':utc_now(),'source_run_id':state['run_id'],'policy':'保留舊版本；先語法、再契約、再工具橋、再 U/I/S/R/C；禁止僅插註解即報 100%','steps':steps}
    atomic_json(Path(out)/'repair_plan.json',result);return result


def run_selftest(destination=None):
    from unittest import mock
    class GovernanceTests(unittest.TestCase):
        def setUp(self):
            self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name);self.root=self.base/'source';self.root.mkdir();self.out=self.base/'report';self.out.mkdir()
        def tearDown(self):self.temp.cleanup()
        def source(self,text='def main():\n    return 1\n',name='VDF_sample_v0100.py'):
            p=self.root/name;p.write_text(text,encoding='utf-8');return p
        def analysis(self,p):return analyze_file({'path':str(p),'root':str(self.root)},{})
        def receipt(self):
            p=self.source();row=self.analysis(p);proof=self.out/'proof.json';atomic_json(proof,{'ok':True});ctx={'sources':'a','data':'b','rules':'c','environment':'d'}
            r={'schema':'via.matrix.receipt/1','entity_id':row['id'],'stage':'UNIT','source_sha256':row['sha256'],'context':ctx,'finished_at':utc_now(),'exit_code':0,'assertions':[{'passed':True}],'checked_files':[{'path':str(proof),'sha256':file_hash(proof)}]};return row,r,ctx
        def test_python_ast(self):
            r=self.analysis(self.source('LIMIT=5\ndef main(x=1):\n    return x+LIMIT\n'));self.assertEqual(r['parse_state'],'PARSED');self.assertTrue(r['definitions']);self.assertEqual(r['parameters'][0]['default'],5)
        def test_syntax_failure(self):self.assertEqual(self.analysis(self.source('def broken(:\n'))['parse_state'],'ERROR')
        def test_no_import_execution(self):
            flag=self.base/'do_not_create';self.analysis(self.source(f'open({str(flag)!r},"w").write("bad")\n'));self.assertFalse(flag.exists())
        def test_marker_not_runtime(self):self.assertEqual(self.analysis(self.source('# [VIA:ACCEL-BRIDGE]\nx=1\n'))['accelerator']['state'],'MARKER_ONLY')
        def test_network_alias(self):self.assertTrue(self.analysis(self.source('import requests as r\ndef go():\n    return r.get("https://example.com")\n'))['network']['outlets'])
        def test_urllib_parse_not_network(self):
            row=self.analysis(self.source('import urllib.parse\nimport urllib.request\nurl=urllib.parse.urlsplit("https://example.com")\n','helper.py'));self.assertEqual(row['network']['outlets'],[])
        def test_download_copy_version(self):self.assertEqual(self.analysis(self.source('x=1','VDF_example_v0102(1).py'))['version'],'v0102')
        def test_dynamic_review(self):self.assertTrue(any(i['rule']=='DYNAMIC_RESOLUTION' for i in self.analysis(self.source('exec("x=1")\n'))['issues']))
        def test_duplicate_definitions(self):self.assertTrue(any(i['rule']=='DUPLICATE_DEFINITION' for i in self.analysis(self.source('def main(): return 1\ndef main(): return 2\n'))['issues']))
        def test_complex_literal_serialization(self):
            row=self.analysis(self.source("PARAMS={(1,2): {'alpha','beta'}}\n"));encoded=json.dumps(row);self.assertIn('alpha',encoded)
        def test_nested_secret_redaction(self):self.assertIn('REDACTED',public_value('CONFIG',{'api_key':'hidden'})['api_key'])
        def test_secret_redaction(self):self.assertIn('REDACTED',public_value('API_KEY','dontshow'))
        def test_overlapping_roots(self):
            self.source();items,_,_=enumerate_tree([self.root,self.root]);self.assertEqual(len(items),1)
        def test_missing_root_not_complete(self):
            _,_,errors=enumerate_tree([self.base/'missing']);self.assertFalse(rollup([],errors)['inventory_complete'])
        def test_runtime_tool_proof_requires_lock(self):
            row=self.analysis(self.source());probe={'tool_sha256':'tool','source_sha256':row['sha256'],'call_count':2,'output_validated':True};r={'id':'proof','entity_id':row['id'],'stage':'SYSTEM','validation_state':'PASS','finished_at':utc_now(),'tool_probes':{'accelerator':probe}};apply_tool_proofs([row],[r],[]);self.assertNotEqual(row['accelerator']['state'],'RUNTIME_VERIFIED')
            apply_tool_proofs([row],[r],[{'name':'accelerator','state':'LOCK_MATCH','sha256':'tool'}]);self.assertEqual(row['accelerator']['state'],'RUNTIME_VERIFIED')
        def test_network_proof_covers_every_outlet(self):
            row=self.analysis(self.source('import requests\nrequests.get("https://example.com")\n'));probe={'tool_sha256':'tool','source_sha256':row['sha256'],'call_count':1,'output_validated':True,'denied_respected':True,'origins_verified':True,'outlet_node_ids':[]};r={'id':'proof','entity_id':row['id'],'stage':'SYSTEM','validation_state':'PASS','finished_at':utc_now(),'tool_probes':{'network':probe}};pins=[{'name':'network','state':'LOCK_MATCH','sha256':'tool'}];apply_tool_proofs([row],[r],pins);self.assertNotEqual(row['network']['state'],'RUNTIME_VERIFIED');probe['outlet_node_ids']=[row['network']['outlets'][0]['node_id']];apply_tool_proofs([row],[r],pins);self.assertEqual(row['network']['state'],'RUNTIME_VERIFIED')
        def test_unresolved_network_not_green(self):
            row=self.analysis(self.source('def main(): return 1\n','helper.py'));row['accelerator']['state']='RUNTIME_VERIFIED';row['tests']={s:'PASS' for s in STAGES};rollup([row],[]);self.assertEqual(row['status'],'YELLOW')
        def test_zero_denominator(self):self.assertIsNone(fraction(0,0)['ratio'])
        def test_ps_unavailable_not_pass(self):
            p=self.source('function Test-Thing { 1 }','a.ps1');r=self.analysis(p);self.assertEqual(r['parse_state'],'PARSER_UNAVAILABLE')
        def test_cache_hash_change(self):
            p=self.source();first=self.analysis(p);p.write_text('x=2\n');second=analyze_file({'path':str(p),'root':str(self.root)},{},first);self.assertNotEqual(first['sha256'],second['sha256']);self.assertFalse(second.get('cache_reused',False))
        def test_receipt_pass(self):
            row,r,ctx=self.receipt();self.assertEqual(validate_receipt(r,{row['id']:row},ctx,[self.root,self.out])['validation_state'],'PASS')
        def test_exit_zero_false_assertion(self):
            row,r,ctx=self.receipt();r['assertions'][0]['passed']=False;self.assertEqual(validate_receipt(r,{row['id']:row},ctx,[self.root,self.out])['validation_state'],'FAIL')
        def test_empty_assertions_not_pass(self):
            row,r,ctx=self.receipt();r['assertions']=[];self.assertEqual(validate_receipt(r,{row['id']:row},ctx,[self.root,self.out])['validation_state'],'FAIL')
        def test_changed_source_stale(self):
            row,r,ctx=self.receipt();row['sha256']='new';self.assertEqual(validate_receipt(r,{row['id']:row},ctx,[self.root,self.out])['validation_state'],'STALE')
        def test_changed_dependency_stale(self):
            row,r,ctx=self.receipt();ctx2=dict(ctx,rules='changed');self.assertEqual(validate_receipt(r,{row['id']:row},ctx2,[self.root,self.out])['validation_state'],'STALE')
        def test_expired_receipt_stale(self):
            row,r,ctx=self.receipt();r['finished_at']=(datetime.now(timezone.utc)-timedelta(days=2)).isoformat();self.assertEqual(validate_receipt(r,{row['id']:row},ctx,[self.root,self.out])['validation_state'],'STALE')
        def test_evidence_changed_stale(self):
            row,r,ctx=self.receipt();atomic_json(self.out/'proof.json',{'ok':False});self.assertEqual(validate_receipt(r,{row['id']:row},ctx,[self.root,self.out])['validation_state'],'STALE')
        def test_path_escape(self):
            with self.assertRaises(ValueError):resolve_in_roots('../outside.py',self.root,[self.root])
        def test_scope_lock(self):
            with workspace_lock(self.out):
                with self.assertRaises(RuntimeError):
                    with workspace_lock(self.out):pass
        def test_transaction_rollback(self):
            a=self.root/'new1.py';b=self.root/'new2.py'
            with self.assertRaises(RuntimeError):commit_transaction({'guards':[],'writes':[{'path':str(a),'bytes':b'x=1'},{'path':str(b),'bytes':b'x=2'}]},self.out,0)
            self.assertFalse(a.exists());self.assertFalse(b.exists())
        def test_transaction_no_overwrite(self):
            p=self.source()
            with self.assertRaises(FileExistsError):commit_transaction({'guards':[],'writes':[{'path':str(p),'bytes':b'bad'}]},self.out)
            self.assertIn('def main',p.read_text())
        def test_transaction_guard(self):
            p=self.source()
            with self.assertRaises(RuntimeError):commit_transaction({'guards':[{'path':str(p),'sha256':'wrong'}],'writes':[]},self.out)
        def test_rollback_changed_file_blocked(self):
            p=self.root/'new.py';commit_transaction({'guards':[],'writes':[{'path':str(p),'bytes':b'x=1'}]},self.out);p.write_text('x=2')
            with self.assertRaises(RuntimeError):rollback_install(self.out)
        def test_audit_chain(self):
            audit_event(self.out,'ONE',{});audit_event(self.out,'TWO',{});self.assertEqual(verify_audit(self.out/'events.jsonl')['status'],'PASS')
        def test_audit_tamper(self):
            audit_event(self.out,'ONE',{});p=self.out/'events.jsonl';p.write_text(p.read_text().replace('ONE','TWO'));self.assertEqual(verify_audit(p)['status'],'FAIL')
        def test_job_auth(self):
            s=create_session(self.out,[self.root]);j={'schema':'via.matrix.job/1','session_id':s['session_id'],'token':'wrong','id':'job123456','action':'scan'}
            with self.assertRaises(ValueError):validate_job(j,s,set())
        def test_job_replay(self):
            s=create_session(self.out,[self.root]);j={'schema':'via.matrix.job/1','session_id':s['session_id'],'token':s['token'],'id':'job123456','action':'scan'}
            with self.assertRaises(ValueError):validate_job(j,s,{'job123456'})
        def test_job_shell_rejected(self):
            s=create_session(self.out,[self.root]);j={'schema':'via.matrix.job/1','session_id':s['session_id'],'token':s['token'],'id':'job123456','action':'shell'}
            with self.assertRaises(ValueError):validate_job(j,s,set())
        def test_job_extra_roots_rejected(self):
            s=create_session(self.out,[self.root]);j={'schema':'via.matrix.job/1','session_id':s['session_id'],'token':s['token'],'id':'job123456','action':'scan','roots':['/']}
            with self.assertRaises(ValueError):validate_job(j,s,set())
        def test_prior_tail_version(self):
            self.source('',ENGINE_FAMILY+'_v0191.py');p=self.source('',ENGINE_FAMILY+'_v0192.py');self.source('',ENGINE_FAMILY+'_v0193.py');self.assertEqual(prior_console_path(self.root),p)
        def test_csv_schema(self):
            p=self.root/'data.csv';p.write_text('date,close\n2026-01-01,1\n');r=inspect_artifact({'path':str(p)});self.assertTrue(r['schema_complete']);self.assertEqual(len(r['fields']),2)
        def test_json_sample_not_schema(self):
            p=self.root/'data.json';atomic_json(p,[{'x':1}]);self.assertFalse(inspect_artifact({'path':str(p)})['schema_complete'])
        def test_three_phase_scan_cache_and_delta(self):
            p=self.source();one=scan([self.root],self.out);two=scan([self.root],self.out);self.assertEqual(two['performance']['cache_hits'],1);self.assertEqual(two['delta']['changed'],[]);p.write_text('x=3\n');three=scan([self.root],self.out);self.assertEqual(len(three['delta']['changed']),1);self.assertNotEqual(one['context']['sources'],three['context']['sources'])
        def test_native_rc_not_green(self):
            p=self.source('print("ok")\n');r=run_process([sys.executable,str(p)],self.root,self.out,'fixture');self.assertEqual(r['state'],'RETURNED_ZERO');self.assertNotIn('PASS',r['state'])
        def test_hash_scope_guard_install(self):
            via=self.root/'VeritasIntelligenceAnalytics';reg=via/'supportive modules/registry';reg.mkdir(parents=True);(reg/(ENGINE_FAMILY+'_v0194.py')).write_text('')
            with self.assertRaises(RuntimeError):prepare_install(via,self.root/'ui.html')
    stream=io.StringIO();suite=unittest.defaultTestLoader.loadTestsFromTestCase(GovernanceTests);started=time.monotonic()
    with contextlib.redirect_stdout(io.StringIO()):result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    report={'schema':'via.matrix.qa/1','version':VERSION,'scope':'isolated fixtures; does not certify Windows VIA production','at':utc_now(),'tests':result.testsRun,'passed':result.testsRun-len(result.failures)-len(result.errors),'failures':len(result.failures),'errors':len(result.errors),'status':'PASS' if result.wasSuccessful() else 'FAIL','elapsed_seconds':round(time.monotonic()-started,3),'details':stream.getvalue(),'windows_native_ps_ast':'NOT_RUN' if not shutil.which('pwsh') else 'AVAILABLE_NOT_CERTIFIED','production_systems':'NOT_RUN'}
    if destination:atomic_json(destination,report)
    print(json.dumps({k:v for k,v in report.items() if k!='details'},ensure_ascii=False),flush=True)
    if not result.wasSuccessful():print(stream.getvalue())
    return report

def default_frontend():
    local=Path(__file__).with_name(FRONTEND_NAME)
    installed=Path(__file__).resolve().parent.parent/'VCGC_Matrix'/FRONTEND_NAME
    return local if local.is_file() else installed if installed.is_file() else local


# 10 · CLI / native verb dispatch. Double-click-free launch through Python or via-vcgc.
def main(argv=None):
    args=list(sys.argv[1:] if argv is None else argv)
    if args and args[0]!='matrix':return load_prior().main(args)
    if args:args=args[1:]
    parser=argparse.ArgumentParser(prog='via-vcgc matrix',description='VCGC 一個 PY + 一個離線 HTML；五系統獨立入口、17 矩陣、原生註冊與實測證據')
    parser.add_argument('action',nargs='?',default='scan',choices=['scan','doctor','selftest','install','register','watch','run-tests','native-check','repair-plan','rollback','export'])
    parser.add_argument('--roots',nargs='+',default=list(DEFAULT_ROOTS));parser.add_argument('--out',default=str(Path.home()/'AppData/Local/VCGC/MultiMatrix_v0193') if os.name=='nt' else str(Path.cwd()/'VCGC_Matrix_Output_v0193'));parser.add_argument('--frontend',default=str(default_frontend()));parser.add_argument('--workers',type=int,default=MAX_WORKERS);parser.add_argument('--plan');parser.add_argument('--apply',action='store_true');parser.add_argument('--activate-tools',action='store_true');parser.add_argument('--watch',action='store_true');parser.add_argument('--open',action='store_true');a=parser.parse_args(args)
    for stream in (sys.stdout,sys.stderr):
        with contextlib.suppress(AttributeError):stream.reconfigure(encoding='utf-8',errors='replace')
    out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True);vias=discover_via(a.roots);via=vias[0] if vias else None
    try:
        if a.action=='selftest':return 0 if run_selftest(out/'selftest.json')['status']=='PASS' else 1
        if a.action=='doctor':
            result={'version':VERSION,'python':sys.version,'platform':platform.platform(),'roots':[{'path':str(p),'exists':Path(p).is_dir()} for p in a.roots],'native_roots':list(map(str,vias)),'powershell':shutil.which('pwsh'),'tools':inspect_tools(via),'budget':resource_budget(a.workers),'frontend_exists':Path(a.frontend).is_file()};atomic_json(out/'doctor.json',result);print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if via else 2
        if a.action=='rollback':result=rollback_install(out)
        elif a.action=='install':
            result=install(a.roots,out,a.frontend,a.apply);print(json.dumps(result,ensure_ascii=False,indent=2))
            if a.apply:
                scan(a.roots,out,a.frontend,a.workers,a.activate_tools)
        elif a.action=='register':
            if not via:raise RuntimeError('NATIVE_ROOT_NOT_FOUND')
            result=register_native(via,out)
        elif a.action=='native-check':result=native_suite(via,out)
        elif a.action=='run-tests':
            if not a.plan:raise ValueError('--plan required')
            result=run_test_plan(a.plan,a.roots,out);scan(a.roots,out,a.frontend,a.workers)
        elif a.action=='repair-plan':result=repair_plan(read_json(out/'snapshot.json',max_bytes=128*1024*1024),out)
        elif a.action=='export':result=read_json(out/'snapshot.json',max_bytes=128*1024*1024);export_reports(result,out,a.frontend)
        else:result=scan(a.roots,out,a.frontend,a.workers,a.activate_tools);repair_plan(result,out)
        if isinstance(result,dict):print(json.dumps({k:v for k,v in result.items() if k in ('version','run_id','overall','state')},ensure_ascii=False))
        if a.open and (out/FRONTEND_NAME).is_file():webbrowser.open((out/FRONTEND_NAME).as_uri())
        if a.watch or a.action=='watch':watch(a.roots,out,a.frontend)
        return 0
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as e:
        atomic_json(out/'last_error.json',{'at':utc_now(),'type':type(e).__name__,'error':str(e)});print('[VCGC] '+str(e),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
