# VIA handover 2026-09-26 · Fed reserve method

Door: VCGC only (`VIA_FROM_VCGC=YES`).
Book: `functional modules/VDF/VDF_USMacro_Method_v0100.json`.
Refresh: `Invoke-VIA-VCGC-MacroMethod.ps1`. It writes the series below into `us_macro` from 2020-01-01. It does not edit the intake SSOT and it does not commit the database.

## Units

H.4.1 levels are millions of dollars: `WALCL`, `TREAST`, `WSHOMCB`, `WTREGEN`, `WRESBAL`, `WLCFLPCL`, `WCURCIR`, `WLRRAL`, `WLRRAFOIAL`, `WLRRAOL`.
Overnight reverse repo amounts are billions of dollars: `RRPONTSYD`, `RRPONTTLD`, `RRPONTSYSAD`. Multiply by 1000 before adding them to an H.4.1 line.
Rates are percent: `RRPONTSYOFFR`, `RRPONTSYAWARD`, `IORB`, `EFFR`.
`DTS_TGA_CLOSE` comes from the Daily Treasury Statement. The stored value is millions of dollars. `WTREGEN` is only the Wednesday Fed liability. The daily book peaks inside the week, and the Wednesday print catches up later.

## Identity

Change in reserve balances ≈ change in total assets − change in the TGA − change in reverse repo − change in currency.
Put reverse repo into millions first. Over the 37 Wednesdays of 2026 the correlation between the TGA change and the reserve change was −0.97. After removing the same week's asset change, the mean residual was about zero because domestic reverse repo was already empty.

## What not to mix

`WSHOTSL` moved with `TREAST` in this window. It is not a second measure of total securities.
`WLRRAL` is all reverse repo. After 2025 the remainder is `WLRRAFOIAL` (foreign official). `WLRRAOL` is the domestic facility and was about zero on 2026-09-23.
`DISCBORR` stopped in 2020. Do not treat it as live.

## Restore

This file plus the method book. The database stays in the local data home. Do not copy `vdf_global_market.duckdb` into git.
