# VIA WorkOps Smart Workflow v0102

## New in v0102
- Multilingual Template Registry: Traditional Chinese (`zh-TW`), Simplified Chinese (`zh-CN`), English (`en`)
- Templates coexist; no overwrite required.
- Project-level default language/template + run-time override.
- ENG-034 Batch Follow-up Pack Builder
- ENG-037 Missing Information Guard
- ENG-038 Project Card Aggregator
- Mouse-first Template Center UI

## Template hierarchy
1. Run override (`--template`, `--language`)
2. Project default (`default_template`, `default_language`)
3. State default
4. Registry default

Project ID remains immutable. Display name, default template and default language may change through append-only project registry events.

## Safety
- Generates draft specifications only.
- No automatic Outlook send.
- No automatic mailbox move or category mutation.
- Closure, escalation, send and committed deadline changes remain human-confirmed actions.

## Main commands
```text
py engines/workops_missing_information_guard.py scan
py engines/workops_followup_pack_builder.py build --language zh-TW
py engines/workops_followup_pack_builder.py build --language zh-CN
py engines/workops_followup_pack_builder.py build --language en
py engines/workops_project_card_aggregator.py build
```

## UI
- `ui/template_center.html`: choose language and coexisting template by mouse.
- `ui/project_confirm.html`: confirm project classification by mouse.

## Test
`python -m pytest tests/test_engines.py tests/test_v0102.py -q`
