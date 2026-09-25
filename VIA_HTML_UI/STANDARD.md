# VIA Standardization Contract

## Runtime contract

`ui/VIA-Complete-System.html` is the single local launcher. `ui/VIA-UI-Standalone-NoServer.html` and `ui/VIA-SYNCHRONIZER-Standalone.html` are the two canonical functional entrypoints opened by the launcher. All three must open from `file://`, contain inline HTML/CSS/JavaScript, and avoid undeclared external resources. Use `localStorage`, `BroadcastChannel`, Blob downloads, and SpreadsheetML when local interoperability is required.

## State contract

The synchronizer state remains version 2 compatible. Unknown fields must survive UI normalization. Modules, chart definitions, history rows, pivot configuration, layout parameters, and add-on registrations remain in the same portable state envelope.

## Extension contract

A new industry profile must define stable module IDs, chart IDs, history schema, pivot fields, and enabled/pinned/order metadata. Generate browser and Python validators from the VSX IR, then run CI and the three-viewport E2E matrix.

## Offline contract

The package must remain usable from `file://` without network access. Keep an offline deployment guide, a checksum workflow, a same-origin SYNCHRONIZER test, a Chromium/Playwright E2E command, and a loopback-only fallback for browsers that restrict file-origin storage. The loopback server is a test convenience, not a runtime dependency.

## Optional companion contract

The Streamlit companion under `docs/references/streamlit_companion/` is not a canonical runtime dependency. It must use prepared local dependencies, user-provided data, deterministic fallback views, and must not write directly to browser localStorage or introduce a server requirement into the standalone HTML entrypoints.

## Delivery contract

A release is complete only when the launcher user-flow, HTML syntax checks, module/profile validation, TriEngine quality gate, cross-page sync, E2E matrix, ZIP integrity, checksum, and extracted-package verification all pass. Historical templates belong under `legacy/reference-templates/` and are never treated as canonical entrypoints.
