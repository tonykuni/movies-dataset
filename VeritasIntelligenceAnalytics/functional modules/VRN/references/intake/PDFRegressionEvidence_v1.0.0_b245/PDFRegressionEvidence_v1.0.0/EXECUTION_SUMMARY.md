# VRNFourEngineSuite execution summary

- Run: `VRN4-FFB97CB17E29FAB5`
- Input: `/workspace/scratch/4596cd1a0b4d/four_engine_work/regression_input/synthetic_financial_report.pdf`
- Overall status: **PASS**

| Stage | Engine | Status | Duration (ms) | Counts |
|---|---|---:|---:|---|
| repair | VRNTextRepairEngine 1.0.0 | PASS | 5 | pages=2, changes=0, financial_data=0, summary_sentences=2 |
| layout | GenericLayoutEngine 2.1.0 | PASS | 490 | pages=2, elements=32 |
| text | VRNPDFTextFetcher 1.0.0 | PASS | 128 | pages=2, characters=684 |
| table | VRNPDFTableFetcher 1.0.0 | PASS | 76 | tables=1, cells=12 |

## Warnings

- None
