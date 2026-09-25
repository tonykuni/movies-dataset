# VIA handover 2026-09-26 · TA-Lib lock

Door: VCGC only (`VIA_FROM_VCGC=YES`).
Policy: L50. QuantGuard is the indicator engine. TA-Lib is not installed, imported, or routed.

Locked tools:
- accelerator `VeritasCeleritas_v1141.py` (`ddcb5460bf64`)
- network `VeritasAegisNexus_v0116.py` (`adb254cc202c`)

Removed in this point:
- the v1.14.0 accelerator package (its engine called `_si("talib")`)
- retired `VIA_ENG003_TALibEngine.py`
- the TA-Lib intake baseline
- the indicator PDFs and the classification markdown

Kept on purpose:
- L50 and the kill gate. Those sentences are the ban, not an import.
- `VIA_Retired_TALib_B534.json`. The ledger says the engines were removed and must not be revived.

Check, in order: policy, token gate, env names, tools, version lock, then `CGC_MDL190_TALibLock_v0100.py`.
A live `.py` that contains `import talib`, `from talib`, or `_si("talib")` is RED.
A comment that names the ban is not an import.

Restore: this file plus `VIA_Reports/vcgc/RESTORE_20260926.json` after the lock command. Git history still has the deleted files. Do not copy them back.
