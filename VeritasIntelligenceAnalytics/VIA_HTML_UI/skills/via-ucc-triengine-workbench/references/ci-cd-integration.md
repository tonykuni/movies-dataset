# VIA CI/CD integration

## Quality-gate sequence

Run the same deterministic sequence on a developer machine and in CI:

1. **E1 / VSX**: extract the HTML, specification files, or source directory into `via_spec_ir.json`, Markdown, and Visual Lock HTML.
2. **Module validator generation**: read the IR and an industry profile; generate a Python validator, browser smoke script, and manifest.
3. **Module validation**: fail when required DOM IDs, runtime tokens, labels, or IR counts regress.
4. **E1/E2/E3 Hub selftest**: validate the Hub's own route, mount, envelope, and missing-engine degradation behavior.
5. **Hub route**: record which inputs would go to E1, E2, or E3 without executing source content.
6. **Hub pipeline**: run E1 → E2 → E3 handoffs where engines are available; write `pipeline_result.json` and per-step envelopes. Missing optional engines should be visible as `SKIP`/`MISSING`, not silently hidden.
7. **Artifact upload**: retain `ci_report.json`, `vsx/`, `validation/`, `hub-pipeline/`, and `logs/`.

## One-command local or CI invocation

```bash
python skills/via-ucc-triengine-workbench/scripts/run_via_ci.py \
  --extractor tools/via_spec_extractor.py \
  --hub tools/via_triengine_hub.py \
  --html ui/VIA-SYNCHRONIZER-Standalone.html \
  --profile config/industry-profile.json \
  --industry smart-manufacturing \
  --source ui/VIA-SYNCHRONIZER-Standalone.html \
  --out artifacts/via-ci \
  --root .
```

The command exits non-zero if VSX, generated validation, or Hub selftest fails. It writes a machine-readable `ci_report.json` and separate stdout/stderr logs for each stage.

## GitHub Actions

Copy [github-actions-via.yml](../templates/ci/github-actions-via.yml) into `.github/workflows/`. Set repository-specific paths in its `env` block. The workflow has no package installation requirement for the bundled scripts.

## GitLab CI

Copy [gitlab-ci-via.yml](../templates/ci/gitlab-ci-via.yml) into `.gitlab-ci.yml` or merge its job into the existing test stage. Keep the artifact paths so failed validation remains diagnosable.

## Safe integration rules

- Run the validator against the checked-out working tree, not a generated copy that bypasses review.
- Keep `--source` explicit; do not recursively scan secrets, `.git`, dependency caches, or build output.
- Store CI artifacts, not browser localStorage. Do not attempt to test `BroadcastChannel` across unrelated CI workers.
- Keep E3 source analysis in a sandboxed CI job if source files are untrusted; inspection should be read-only.
- Use a matrix for multiple industry profiles rather than copying the workflow. Each matrix entry writes to a separate output directory.
