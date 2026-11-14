# v0310 Reuse Closeout

## Fixed
- Bundled `internal/NON_STOCK_CORE_v0200.py`.
- Bundled VRN-2 layout module.
- Bundled VRN-2 TextRepair/TableRestorer module.
- Bundled VRN-2 local extractive NLP summarizer module.
- Added startup hard gate + SHA-256 doctor evidence.
- Repo/desktop no longer needs to locate these modules externally.

## Runtime lane
`Input -> bundled VRN M03 Layout -> bundled MDL003 repair -> bundled M07 extractive NLP -> bundled non-stock core -> one-report-one-row + child tables`

## Test
6 real available samples passed, including industry, aerospace, morning meeting, market strategy, macro weekly, Messenger.
