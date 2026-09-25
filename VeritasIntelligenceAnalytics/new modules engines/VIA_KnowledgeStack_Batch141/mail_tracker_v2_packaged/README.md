# Mail Tracker V2

Modular email intelligence pipeline. **Layout unchanged** (`modules/` + orchestration); modules are richer; project is installable via modern packaging.

## Project structure (unchanged layout, richer modules)

```text
mail_tracker_v2_packaged/
├── pyproject.toml          # PEP 621 + PEP 735 dependency-groups
├── README.md
├── tests/
│   └── test_pipeline.py
└── mail_tracker_v2/
    ├── __init__.py         # public API re-exports
    ├── pipeline.py         # end-to-end orchestration (was main_mail_tracker_v2.py)
    └── modules/
        ├── __init__.py
        ├── email_identity.py      # SHA-256 UID v2
        ├── email_parser.py        # canonical schema + timestamp normalize
        ├── email_semantic.py      # rule matrix → category + risk + confidence
        ├── email_project_mapper.py
        ├── email_dept_mapper.py
        ├── email_sla.py           # SLA policy table
        ├── email_lifeline.py      # persistent tracker record
        └── email_workflow.py      # task ticket + priority
```

## Quick start

```bash
# with uv (recommended)
cd mail_tracker_v2_packaged
uv sync                  # project + default dev group
uv run mail-tracker      # sample run
uv run pytest

# or pip
pip install -e .
python -m mail_tracker_v2.pipeline
```

## API

```python
from mail_tracker_v2 import mail_tracker_v2

result = mail_tracker_v2({
    "sender": "rd_lead@example.com",
    "receiver": "pm@example.com",
    "subject": "P2382 risk on validation schedule",
    "body": "We see potential risk and delay on validation phase.",
    "timestamp": "2026-08-25 16:50",
})
# result["UID"], result["Semantic"], result["Task"], ...
```

## Packaging notes (summary of investigation)

| Topic | Choice here |
|-------|-------------|
| Metadata | **PEP 621** `[project]` in `pyproject.toml` |
| Build backend | **Hatchling** |
| Dev deps | **PEP 735** `[dependency-groups]` (`dev`, `lint`, `test`) — not published |
| Tool | **uv** (`uv sync`, `default-groups = ["dev"]`) |
| Lock | Commit `uv.lock` after first `uv lock` (universal, cross-platform) |
| Resolver | uv PubGrub + marker **forking**; optional `fork-strategy` |
| vs Poetry groups | Poetry: `[tool.poetry.group.dev.dependencies]` / `--with`; standard: `[dependency-groups]` + `uv sync --group test` |
| vs pip | pip = single-env resolvelib; uv/Poetry = universal-style locks |

### Dependency groups vs extras

- **Groups** (`[dependency-groups]`): developers only (`pytest`, `ruff`). `uv sync --group test`.
- **Extras** (`[project.optional-dependencies]`): features for end users of the package on PyPI.

### Useful uv commands

```bash
uv add --group test pytest
uv sync --group lint
uv sync --only-group test    # CI: lean install
uv lock
uv tree
```

## License

MIT
