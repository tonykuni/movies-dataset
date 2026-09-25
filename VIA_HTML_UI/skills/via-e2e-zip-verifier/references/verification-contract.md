# VIA package verification contract

## Expected package layout

The archive root may be named `via_all_latest` or another single directory. It must contain these operational areas:

- `ui/`: the standalone central UI and SYNCHRONIZER HTML files.
- `e2e/`: the reusable Playwright runner plus `results-final/` reports and screenshots.
- `complete-package/`: the synchronized delivery package.
- `skill/`: reusable VIA UCC/TriEngine resources.
- `analysis/`: optional performance and visual analysis artifacts.
- `assets/`: optional transparent logo and brand assets.

## Contract checks

Validate the SHA-256 digest before interpreting package contents. Reject absolute paths and any archive member containing a `..` path component. Run the ZIP CRC test before extraction. Extract into a temporary directory and never execute files from an untrusted archive without these checks.

For each standalone HTML file, require a body, expected product markers, no undeclared external resource tags, no local script or stylesheet references, and syntactically valid inline JavaScript. The central UI must expose the investment desk and chart markers. The SYNCHRONIZER must expose its versioned state key, BroadcastChannel path, add-on API, and Excel export function.

Parse the bundled E2E JSON and JUnit XML independently. A valid summary has equal total and passed counts, zero failed tests, zero browser/page errors, and a passing no-horizontal-overflow result for every declared viewport. JUnit must parse as XML and every testsuite must report zero failures and zero errors.

For industry profiles, validate both the reusable skill copy and the complete-package copy. The current registry requires four IDs: `smart-manufacturing`, `finance-cyber`, `smart-healthcare`, and `investment-research`. Each profile must contain at least one module with a stable ID, display name, type, and enabled state.
