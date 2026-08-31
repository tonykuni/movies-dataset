# VRNFourEngineSuite execution summary

- Run: `VRN4-70E4EB9FF1227BCF`
- Input: `/workspace/scratch/4596cd1a0b4d/upload/fetched text to be fixed..txt`
- Overall status: **WARN**

| Stage | Engine | Status | Duration (ms) | Counts |
|---|---|---:|---:|---|
| repair | VRNTextRepairEngine 1.0.0 | WARN | 461 | records=64, financial_data=189, summary_sentences=285, PASS=63, NEEDS_OCR=1 |
| layout | GenericLayoutEngine 2.1.0 | PASS | 3 | documents=64, elements=232 |
| text | VRNPDFTextFetcher 1.0.0 | PASS | 0 | records=64 |
| table | VRNPDFTableFetcher 1.0.0 | WARN | 14 | tables=0, cells=0 |

## Warnings

- repair: one or more records require source-PDF OCR
- layout: physical page/bbox unavailable in pre-fetched text attachment
- text: input is already fetched text; no PDF backend was rerun
- table: no conservative aligned-text table candidate detected
