# VIA handover 2026-09-26 · status lock

Door: VCGC only (`VIA_FROM_VCGC=YES`).
Lock: `supportive modules/registry/VIA_StatusLock_v0100.json`.
Check: `CGC_MDL193_StatusLock_v0100.py`.

## Locked, retested on this commit

- Knowledge catalog: 13 assets, 13 GREEN, no dependency cycle, method log still linked.
- US macro parameters: 33 rows, 18 method series, index hash matches, hub `v0110`, central index 67 books.
- `VDF_ENG113_MacroMethod_v0100.py` selftest passed. The live refresh in the sandbox wrote 16,120 FRED rows and 1,113 Treasury rows into a temporary database, not the workstation data home.

## Still open

The workstation `us_macro` table was not refreshed here. VDF logic, the VDF bridge, and the VDF handover stay open. VRN logic, the VRN engine, and the VRN handover stay open. Those six were already open in `VIA_LampLock_v0100.json`. This lock does not close them and does not remove them.

Do not delete a locked id because a later scan omitted it. Do not edit the intake macro SSOT. Do not run `registry-sync --apply` or `TOOLS_PLAN_latest.ps1` from this lock.

Merged doors behind this point: #206 method, #207 knowledge catalog, #208 parameter book, #209 hub list.
