# VIA WorkOps Smart Workflow v0101

新增三個 LEGO 模組，不修改既有 ENG-028 / ENG-029 / ENG-030：

- ENG-031 Mandatory Reply Builder
- ENG-032 Project Fusion Classifier
- ENG-033 Project Registration Engine

## Governance
- Parameters: JSON
- Engine: Python
- UI: HTML/CSS/JavaScript
- Outlook: no automatic send/write
- Project classification: suggestion only, user confirmation required
- Project display name: user-owned and changeable
- Project ID: immutable `PRJ-YYYYMMDD-NNNNNN`
- Classification memory: append-only and learn from confirmed choices
- UI is mouse-first; static UI copies explicit commands instead of silently mutating SSOT

## Primary flow
Existing ENG-029 reply_status → ENG-030 follow-up state → ENG-031 follow-up pack
Outlook mail + optional `out/control_sheet.csv` → ENG-032 ranked project candidates → user click → ENG-033 register/confirm → learning memory → ENG-032 improves next run

## Test
`python -m pytest tests/test_engines.py -q`
