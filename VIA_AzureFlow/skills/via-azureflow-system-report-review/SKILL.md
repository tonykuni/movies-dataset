---
name: via-azureflow-system-report-review
description: Review VIA AzureFlow QA complete-system Markdown/JSON reports, QA metrics, action outputs, artifact paths, safety gates, activation readiness, and full-validation case matrices. Use when inspecting VIA_AzureFlow_QA_System_Report.md or deciding whether a run is PASS, PASS_WITH_REVIEW, or FAIL.
---

# VIA AzureFlow System Report Review

Use this skill to turn a generated `VIA_AzureFlow_QA_System_Report.md` plus its JSON companion into a reproducible, evidence-linked review. The skill is read-only with respect to the report, plugin source, ZIP, runs, and user files.

## Review workflow

1. Locate the selected Markdown report. Prefer the explicitly supplied path; do not silently choose a debug or negative report when a positive report is named.
2. Resolve the JSON companion. For `VIA_AzureFlow_QA_System_Report.md`, use the sibling `.json` unless the caller supplies another path.
3. Optionally load `cases.tsv` and the full-validation Markdown report. Treat them as evidence about test execution, not as replacements for the system report.
4. Run `scripts/review_azureflow_system_report.py`. Use `--plugin-root` and `--zip` when checking current file hashes and package metadata. Use `--out-dir` for machine-readable and human-readable review outputs.
5. Read the generated JSON first. Then read the Markdown review for the explanation, discrepancies, warnings, and evidence paths.
6. Classify the result:
   - **PASS**: report status and QA status are PASS, exit code is zero, manifest checks have no failures, and no material discrepancy exists.
   - **PASS_WITH_REVIEW**: technical QA is PASS, but Windows runtime, activation, missing mounts, stale validation metadata, or other human-review conditions remain.
   - **FAIL**: QA or manifest checks fail, required evidence is missing, a safety flag violates policy, or Markdown and JSON materially disagree.
7. Never convert `READY_FOR_WINDOWS_ACTIVATION` into `ACTIVATED`. `registered=false` and `windows_runtime_available=false` are review conditions.
8. Report observed nonzero cases from `cases.tsv` as boundary outcomes. Do not label them defects when the full-validation report defines them as expected negative tests.

## Required interpretation

- Check manifest count and every manifest check before trusting the top-level status.
- Check both `inspect` and `verify`; a combined `all` PASS without both action records is incomplete.
- Preserve the distinction between `validator_summary` checks and full-validation case exit codes.
- Treat `source_write`, `source_delete`, `automatic_command_activation`, `ssot_promotion`, and default `code_execution` or `network` as safety gates. Unexpected `true` values require FAIL or explicit review.
- Confirm artifact paths exist only when the selected environment can see them. A path that is absent because it belongs to another host is `NOT_MOUNTED`, not proof that the original run failed.
- Prefer JSON values for machine decisions and Markdown values for human-readable evidence. The script records any mismatch.

## Script and references

- Run `scripts/review_azureflow_system_report.py --help` for the complete CLI.
- Read [api_reference.md](references/api_reference.md) when mapping fields, verdict rules, or evidence paths.
- Use the existing [VIA AzureFlow QA Plug-in](../via-azureflow-qa-plugin/SKILL.md) for executing `inspect`, `verify`, or `all`; this skill reviews their results and does not replace those actions.

## Default output

The script writes:

- `VIA_AzureFlow_QA_System_Report_Review.json`: structured findings, metric summary, case counts, path checks, discrepancies, warnings, and verdict.
- `VIA_AzureFlow_QA_System_Report_Review.md`: concise detailed review with tables and evidence paths.

Keep the original report and JSON untouched. Store review outputs in a separate directory.

## Safety and delivery

Do not register Task Scheduler tasks, execute user source, modify SSOT, rewrite source documents, or activate commands while reviewing a report. A review can recommend the next Windows action, but it cannot perform activation. When delivering this skill, attach its `SKILL.md` path and provide the portable skill ZIP when one is requested.

## References

- Read [api_reference.md](references/api_reference.md) for the report schema and the exact PASS／PASS_WITH_REVIEW／FAIL rules.
- Use the bundled script instead of duplicating parser logic in an agent response.

## Delivery rule

Run `quick_validate.py` on the skill source and on an extracted package before delivery. Remove initialization examples and `__pycache__` from the final skill package.
