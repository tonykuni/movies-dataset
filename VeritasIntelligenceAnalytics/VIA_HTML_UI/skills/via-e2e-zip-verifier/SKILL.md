---
name: via-e2e-zip-verifier
description: Validate VIA standalone HTML UI packages and cross-device E2E artifacts. Use for inspecting desktop/tablet/mobile compatibility reports, checking ZIP integrity and contents, verifying HTML/JavaScript/no-server contracts, validating industry modules and CI reports, or creating a final reusable package verification result.
---

# VIA E2E and ZIP Verifier

Use this skill when a VIA package must be checked as a deliverable rather than only from its source workspace. Prefer deterministic scripts, isolated extraction, and browser execution over visual assumptions.

## Quick workflow

1. **Read the supplied report.** Load `e2e/results-final/report.json` and `report.md`. Confirm the device list, total/passed/failed counts, browser/page errors, overflow measurements, geometry values, and slowest journeys.
2. **Verify the archive.** Run `scripts/validate_via_zip.py` against the ZIP. Supply the matching `.sha256` file when available. The script checks SHA-256, path traversal, ZIP CRC integrity, required files, standalone HTML contracts, inline JavaScript syntax, bundled E2E summaries, JUnit XML, industry profiles, copied UI synchronization, and screenshots.
3. **Verify the canonical template.** Run `scripts/validate_standardized_package.py` against a `VIA-Standardized-Template-Updated-*` directory. It checks the canonical directory contract, manifest hashes, the four-industry registry, standalone HTML, E2E, JUnit, and legacy reference boundary.
4. **Run the extracted package.** Add `--run-extracted-e2e` or `--run-e2e` when Chromium and Playwright are available. This runs the bundled runner against the HTML extracted from the ZIP, not against the source workspace.
5. **Analyze performance.** Run `/home/ubuntu/via_e2e/analyze_report.py` or copy it into the output package. Compare total, mean, median, p95, and slowest test durations by device. Treat UI interaction duration as test-run overhead, not as FCP or production latency unless the report explicitly measures browser performance APIs.
6. **Inspect modules.** Validate `skill/via-ucc-triengine-workbench/templates/industry-profile.json` and the complete-package copy. Confirm every required industry has at least one module and that module IDs, names, types, and enabled flags are present.
7. **Run the complete-system gate.** When `ci/run_complete_system.sh` is present, run it to cover canonical validation, cross-page sync, launcher user-flow, optional companion smoke, and ZIP verification in one pipeline.
8. **Report clearly.** Separate compatibility, functional coverage, package integrity, module coverage, and performance observations. Mark any source-workspace versus extracted-ZIP difference explicitly.

## Required acceptance criteria

- Every declared device has `failed: 0` and `browser_errors: 0`.
- The overall E2E report has `passed == total` and `failed == 0`.
- `responsive_no_horizontal_overflow` passes at every viewport.
- The standalone contract has no external resource tags or local script/link dependencies unless the package explicitly documents them.
- All inline scripts pass `node --check`.
- ZIP path safety and CRC tests pass.
- JUnit XML parses and every suite has zero failures and zero errors.
- The package contains current UI, SYNCHRONIZER, E2E runner, reports, screenshots, skill resources, and industry profile.
- The package contains `ui/VIA-Complete-System.html`, `e2e/test_complete_system.py`, and `ci/run_complete_system.sh`.
- For the current VIA package, expect these industry IDs: `smart-manufacturing`, `finance-cyber`, `smart-healthcare`, and `investment-research`.

## Useful commands

```bash
python3 scripts/validate_via_zip.py \
  /path/to/VIA-All-Latest.zip \
  --checksum-file /path/to/VIA-All-Latest.zip.sha256 \
  --out-dir /tmp/via-zip-verification \
  --run-extracted-e2e \
  --json /tmp/via-zip-verification/result.json

python3 scripts/validate_standardized_package.py \
  /path/to/VIA-Standardized-Template-Updated-2026-09-20 \
  --run-e2e \
  --out-dir /tmp/via-standardized-verification \
  --json /tmp/via-standardized-verification/result.json

python3 scripts/validate_standardized_zip.py \
  /path/to/VIA-Standardized-Template-Updated-2026-09-20.zip \
  --checksum-file /path/to/VIA-Standardized-Template-Updated-2026-09-20.zip.sha256 \
  --run-extracted-e2e \
  --out-dir /tmp/via-standardized-zip-verification \
  --json /tmp/via-standardized-zip-verification/result.json

python3 /home/ubuntu/via_e2e/analyze_report.py \
  /tmp/via-zip-verification/extracted/via_all_latest/e2e/results-final/report.json \
  /tmp/via-zip-verification/performance-summary.json
```

## References

- Read `references/verification-contract.md` for the expected archive layout and checks.
- Read `references/performance-analysis.md` when explaining device timings, p95 values, or limitations of test durations.

## Failure handling

- If the checksum fails, stop and rebuild or obtain the matching archive; do not call the package verified.
- If the archive is corrupt or contains unsafe paths, stop before extraction-based execution.
- If the bundled report passes but extracted E2E fails, treat the package as failed. Diagnose the packaged HTML, runner, and relative paths.
- If only a duplicated profile is stale, synchronize both copies, rebuild the ZIP, and rerun the complete validator.
- Do not hide skipped mobile checks. State which tests are intentionally skipped at desktop widths.
