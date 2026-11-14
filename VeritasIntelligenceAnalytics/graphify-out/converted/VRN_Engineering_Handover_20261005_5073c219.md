<!-- converted from VRN_Engineering_Handover_20261005.docx -->

VRN report extraction engineering handover
Prepared for Tony and the next implementation owner • Evidence cutoff 2026-10-05 • Executed baseline v0101
This handover records the engines and versions actually used, the functions that implement the current procedure, the outputs and tests available for reproduction, and the work needed to meet every later requirement. “Version” is the interpretation of “virgin number” in the request.
The current deliverable is a reviewed sample implementation. It restored seven native-text PDF first pages and selected financial pages; an eighth scanned PDF remains unresolved. It is not a completed production pipeline for all 106 requested inputs. Source text and numeric values remain separate from repairs and calculated checks.
| Verified result | Scope or qualification |
| --- | --- |
| 8 accessible PDFs | 7 native PDFs processed; 1 scanned PDF held for review |
| 53 table regions and 1,143 records | First pages plus 10 calibrated financial/comparison pages |
| 26 / 6 / 21 table routes | pdfplumber single / Tabula single / dual review |
| 156 arithmetic checks | 153 PASS; 3 source discrepancies retained as FAIL_REVIEW |
| 106 original requested files | 97 PDF, 7 DOCX, 1 TXT, 1 JPG; 89 requested PDFs unavailable |
| Latest requirements pending | Integrated OCR escalation, accelerator coverage, TEMP spill, canonical time fields, formal source SSOT numbering |

## What the recipient should do first
Reproduce v0101 with the included source fixtures, review the unresolved CTBC and scanned MQ examples, and obtain accessible copies of the remaining files and the real VDF cache. Implement the pending changes in a new version, preserving locked engines and the current baseline. Do not mark central governance or dataset acceptance complete until their own checks have run.
## Companion deliverables
The ZIP contains this report, engine_inventory.csv/json, function_inventory.csv/json, evidence_manifest.csv/json, selected source evidence, the existing v0101 code/results bundle, and reference runtime files. Every function declaration is inventoried; the report separately identifies which function paths were actually exercised. Inventory declarations are not a call trace.

# 1 Engine versions and execution status
Versions below describe this environment and session. They are not claims about the latest upstream release. The machine-readable inventory includes source paths and SHA-256 hashes where local source bytes exist.
| Engine | Version | Actual role and evidence |
| --- | --- | --- |
| PyMuPDF | 1.26.6 | EXECUTED — Native text spans and words; geometry; PDF crop/render |
| pdfplumber | 0.11.8 | EXECUTED — Native character reconstruction; table candidates; borders |
| pdfminer.six | 20251107 | INDIRECT — pdfplumber dependency |
| Tabula Java | 1.0.5 | EXECUTED — Stream/lattice table candidates |
| Apache PDFBox | 2.0.24 | INDIRECT — Bundled Tabula PDF processing |
| OpenJDK | 17.0.20 | EXECUTED — Tabula JVM runtime |
| Camelot | NOT INSTALLED | ADAPTER ONLY — Optional stream/lattice; optional network/hybrid |
| Tesseract | 5.3.4 | PROBE ONLY — English OCR at 200 DPI |
| Leptonica | 1.82.0 | INDIRECT — Tesseract image processing |
| Poppler pdftoppm | 26.05.0 | AVAILABLE — PDF rasterization utility |
| pypdf | 6.10.0 | AVAILABLE — PDF utility |
| pandas | 2.2.3 | EXECUTED — DataFrames and CSV/Parquet export |
| NumPy | 2.3.5 | EXECUTED — Array/numeric support |
| PyArrow | 25.0.1 | EXECUTED — Parquet serialization |
| DuckDB | 1.5.6 | SYNTHETIC TEST — Read-only cache access |
| Pillow | 12.3.0 | EXECUTED — Visual QA images |
| Python | 3.12.14 | EXECUTED — Adapter runtime |

Camelot was not installed by this session because the user assigned installation to another person. Its absence is explicitly recorded; there are no Camelot extraction results or proven Camelot accuracy figures. Tesseract was used only in a separate, unsuccessful light-OCR probe after v0101.
A package being available, a source file being downloaded, or an entry appearing in a lockbook does not prove that it processed a report. pdfminer.six and PDFBox were used transitively through other engines. They were not independently selected routes.

# 2 Local modules and reused repository engines
| Module or engine | Version and actual use |
| --- | --- |
| VRN_ReportRestore | v0101 — main executed restoration and export adapter |
| VRN_TableRouter | v0101 — single candidates and dual review |
| VRN_VDFCacheReader | v0101 — cache discovery; synthetic CSV/DuckDB tests |
| VRN_SevenFieldInput | v0100 — selected date, import and official-name functions only |
| segment_firstpages / finalize_layout | Unversioned local scripts — sample-calibrated layout |
| VRN ENG394 LayoutRestore | v0100 — _subcat, validate and rulebook use; not full engine restoration |
| VRN ENG395 ValuationMethodLexicon | v0100 — load_ssot and Matcher.match |
| VRN ENG396 ReportEntities | v0100 — target_prices and SSOT book |
| VDF MDL009 TWStockList | v0101 delegates v0100 — offline name normalization |
| vrn_sample_reader | Unversioned — filename ticker and broker candidates |
| verify_vrn_restore | Unversioned — source regression and cache fixture checks |

## Reference or adapter code without full execution
VDF MDL002 YFinanceFetchingEngine v0100 has an AST-based _post_process_data adapter, but no live prices reached it. VDF MDL008 FetchSystem v0107 was inspected as a thin-tail reference and not invoked. VRN ENG392 TextCompleteness v0100 and ENG394 LayoutRestore v0101 were reference files; the actual layout-rule version used was ENG394 v0100.
VeritasCeleritas v1141 passed a small apply_thread_limits / xrun smoke test only. Its filename is the locked version identity; the internal __version__ value “1.2.0” is stale and should not replace that identity. SUP MDL737 SuperAccelModule v0110 and SUP MDL867 TempSpill v0100 were read but not activated across the pipeline.
The three VIA_VRN rulebooks for LayoutRestore, ReportEntities and ValuationMethod are v0100 and were read without mutation. Do not assign a new central engine number to any local adapter on the strength of this report; central registration remains outstanding.

# 3 Discussed engines that were not utilized
Earlier lists in the conversation proposed several pairings. They were candidate ideas, not an execution record. No benchmark supports a universal “strongest”, five-star success rate, or a promise that all candidates are local, free and non-OCR.
| Candidate family | Implementation status |
| --- | --- |
| Unstructured + PyMuPDF | Unstructured not installed or invoked; native PyMuPDF used independently |
| LlamaParse + pdfplumber | LlamaParse not invoked; hosted parsing must not be confused with a separate local product |
| Docling + pdfminer.six | Docling not invoked; pdfminer was a pdfplumber dependency |
| Marker + PyMuPDF | Marker not invoked; OCR behavior and model licensing require explicit configuration |
| pdfplumber + pypdf | pypdf available, but this pair was not exercised |
| Camelot + pdfplumber | Adapter present; Camelot absent; no dual-pair result |
| Lido / Docparser / Airparser | No integration, runtime version or execution evidence |
| PyMuPDF + pdfimages / pikepdf | No extraction pair executed; pikepdf not installed |
| PDFBox / Ghostscript / Poppler pairs | PDFBox transitive via Tabula; other proposed standalone pairs not used |
| PaddleOCR / EasyOCR | No heavy OCR execution or installed model evidence |

Lockbook references include GenericLayoutHub v0110, PDFPlumberPlusHub v0102, VIAPolarsFrame v0100, PraddleExtractor v0100, via_ocr_super v0102 and VeritasAegisNexus v1652. These identities are recorded for the next owner; none is evidence of report extraction in this run.
## Version discipline for the next owner
Capture the installed distribution version, executable version, model identifier, model checksum and actual selected options at run start. An unavailable engine must report DEPENDENCY_UNAVAILABLE rather than inherit an assumed version. For Java, retain both the JAR hash and JVM version. For thin-tail engines, resolve and lock their full dependency chain before execution.

# 4 Input coverage and reproducible evidence
| ID | Ticker | Broker | Report date | Tables / records |
| --- | --- | --- | --- | --- |
| P01 | 2330 | JPM | 2025-07-18 | 6 / 149 |
| P02 | 1560 | MACQUARIE | 2026-05-20 | 0 / 0 |
| P03 | 3661 | MS | 2025-12-03 | 6 / 169 |
| P04 | 2637 | KGI | 2026-09-15 | 11 / 273 |
| P05 | 3665 | KGI | 2026-05-19 | 11 / 261 |
| P06 | 6533 | CTBC | 2025-12-06 | 9 / 133 |
| P07 | 4171 | CTBC | 2025-12-08 | 0 / 32 |
| P08 | 3017 | HUANAN | 2025-12-02 | 10 / 126 |

Exact filenames, byte sizes and hashes are retained in the output metadata and evidence manifest. P01 is JP 2330; P02 MQ 1560; P03 MS 3661; P04 KGI 2637; P05 KGI 3665; P06 CTBC 6533; P07 CTBC 4171; P08 Huanan 3017. P02 has zero restored records in the v0101 baseline.
## Financial page calibration
| Report | Pages and split profile |
| --- | --- |
| P01 JP | Page 20: annual income; balance sheet/cash flow; quarterly income; ratios/growth |
| P03 MS | Page 10: income, balance sheet, cash flow, ratios |
| P04 KGI 2637 | Page 4 mixed quarter/annual; page 5 five financial blocks |
| P05 KGI 3665 | Page 8 mixed quarter/annual; page 9 five financial blocks |
| P06 CTBC | Page 3 two comparison tables; page 5 four financial tables |
| P08 Huanan | Pages 5 and 6: three distinct tables each |

These coordinates are filename-specific FIN_PROFILES constants. Their inspected output covers 10 pages; it does not establish automatic table discovery on every page of every report. KGI mixed tables have separate quarter and annual crops with shared ITEM labels linked by row index and vertical anchors; the annual block starts at column 9 after eight quarter columns.
## Coverage gaps
The original manifest lists 106 inputs. DOCX, TXT and JPG handling has not been completed by this PDF implementation. Windows path strings are input references, not accessible bytes in this environment. No “all files processed” claim is justified until each manifest item has a hash, readable file and explicit processing outcome.

# 5 End to end procedure and function entry points
| Step | Implemented function path and output |
| --- | --- |
| 1 Load configuration | main → load_tools / load_engine; read layout JSON and three SSOT books |
| 2 Identify input | hash_file; SevenFieldInput helpers; metadata candidates from filename and printed page |
| 3 Segment layout | segment_firstpages / finalize_layout create calibrated parent zones and child regions |
| 4 Restore native text | lines_from_pdf → restore_text → heading_type / split_sentences / tidy_text |
| 5 Rebuild tables | restore_table → table_chars / geometry_rows / infer_column_edges → tidy_cell |
| 6 Check arithmetic | validate_table → canonical_metric / parse_number / rounding_unit; derived check rows only |
| 7 Compare engines | VRN_TableRouter.run → one_table → assess; candidate JSON retained |
| 8 Extract entities | extract_contacts / extract_report_metadata / valuation_and_eps; raw values and source anchors |
| 9 VDF enrichment | fetch_prices; cache scan; optional adapter; compare only when period, unit and basis qualify |
| 10 Export and review | verify_outputs / export_frame / table_html; JSON, CSV, Parquet, HTML and crop evidence |

## Order matters
Separate INFO from BODY before sentence repair. Exclude table and figure children from body reconstruction. Identify a financial page’s left/right groups before its top/bottom tables. Perform table reconstruction and source checks before mapping annual EPS or comparing financial periods. Preserve source values throughout candidate selection and enrichment.
## Function inventory interpretation
function_inventory.csv/json contains the AST signature, source line, docstring, module version and module status of available local functions. It includes functions in reference-only modules for handover completeness. Only the paths explicitly described here and in verification evidence are claimed as exercised. Source line numbers are navigation aids and cease to be stable after edits.
The v0101 code and results are packaged together. Runtime paths in logs can refer to this workspace; relocate them through the documented CLI options. Re-executing segmentation on a different broker template requires fresh validation, not reuse of calibrated coordinates without checking.

# 6 Layout segmentation and coordinate restoration
## Native first page method
PyMuPDF provides text dictionaries, spans, words and bounding boxes. The local layout scripts assign INFO and BODY parent zones and text/table/figure children, informed by the ENG394 v0100 categories and manual sample calibration. Borders, whitespace, aligned numeric columns and semantic headers inform table boundaries. Figures are retained as crops with native labels when present.
The requested generic neighborhood rule—look 3–4 lines upward and 2–3 downward around an aligned candidate, including a potentially empty upper-left ITEM cell—is a design requirement. Sample-calibrated cuts and reconstruction address several examples, but there is no demonstrated generic detector satisfying that rule across the full corpus.
## Reconstruction parameters already applied
| Parameter | v0101 behavior |
| --- | --- |
| Line grouping | 4.5-point center-Y tolerance for native words |
| Column anchors | Right-edge clusters within 4 points; at least 3 supporting words |
| First numeric boundary | Minimum left edge prevents loss of a leading digit |
| Comparison table headers | Explicit semantic headers override misleading percent-derived columns |
| Percentage points | ppts joins the prior numeric token instead of forming an extra column |
| Token assignment | Nearest semantic header center; preserve raw text and coordinates |
| Figure output | 130 DPI crop in baseline; native chart text and nearby source recorded separately |

## Merged cells and missing labels
Ruled rectangles provide span evidence; Camelot, when installed, can contribute horizontal/vertical span geometry. Empty numeric cells are never forward-filled, replaced by zero or silently inferred. Title, header, source and note records remain distinguishable from data rows. An empty upper-left label is a structural possibility, not permission to shift all columns.
Rebuilding a table’s readable grid does not guarantee perfect original visual reproduction. Border geometry and merged-cell evidence retain REVIEW status where ambiguous. The original PDF and crops remain the ultimate review source. Do not use a normalized table alone to resolve a disputed cell.

# 7 Single engine routing and dual engine review
CONFIG selects pdfplumber, then optional Camelot, then Tabula as single-engine candidates. A successful candidate can stop the route; unresolved or arithmetic-discrepant tables receive dual review. This order reduces unnecessary work while retaining evidence.
| Engine path | Actual settings |
| --- | --- |
| pdfplumber | lines and text strategies; intersection_tolerance 6; text_x_tolerance 2; text_y_tolerance 3 |
| Camelot stream | row_tol 3; column_tol 0; table_areas from converted crop coordinates |
| Camelot lattice | line_scale 40; no automatic OCR/ML selection |
| Camelot optional | network / hybrid listed but not enabled by default; installed-version support must be verified |
| Tabula Java | stream -t or lattice -l; page -p; area -a top,left,bottom,right; JSON output; 30-second timeout |
| Concurrency | ThreadPoolExecutor max_workers 3 across independent table regions |
| Cache key | SHA over reference grid, bbox, page, file size, mtime_ns, arithmetic state, engine availability and CONFIG |

Camelot uses bottom-origin coordinates: a top-origin [x0,y0,x1,y1] crop becomes x0,page_height−y0,x1,page_height−y1. Retain the conversion and original bbox in candidate evidence. A wrong coordinate convention can produce plausible but unrelated cells.
## Acceptance gate and its important limitation
assess compares numeric token multisets using Counter. Both precision and recall must be at least 0.97; there must be at least three reference numeric cells; every candidate row must have the reference width. This measures agreement with the coordinate reconstruction, not truth against the PDF. A row or column permutation can retain the multiset and pass. Replace or supplement it with position-aware row/column/header checks in the next version.
The retained output grid always remains the coordinate reconstruction from pdfplumber/native geometry. A SINGLE_TABULA label does not mean Tabula replaced the final grid. A DUAL_PDFPLUMBER_TABULA_REVIEW label records candidate comparison and unresolved review; it is not a proven automatic fusion or final acceptance.
Observed route totals: 26 SINGLE_PDFPLUMBER, 6 SINGLE_TABULA, 21 DUAL_PDFPLUMBER_TABULA_REVIEW. There are no executed Camelot routes. These counts must not be published as engine accuracy rankings.

# 8 OCR escalation and the scanned report
## Actual probe after v0101
P02 MQ 1560 has no usable native-text layer. A separate probe rendered its first page at 200 DPI with PyMuPDF and ran Tesseract 5.3.4 using the English model and PSM 3. It produced TXT, TSV and a searchable PDF. The baseline extraction output was not replaced by that probe.
tesseract temp_ocr_probe/page.png temp_ocr_probe/light -l eng --psm 3 tsv txt pdf
| Observation | Result |
| --- | --- |
| Word count | 658 |
| Mean / median confidence | 87.74 / 96.02 |
| Words below confidence 60 | 59 |
| Material price-date error | Printed 19 May 2026 became 19 May 2025 |
| Target price error | Printed TWD 855.00 row was not captured |
| EPS table errors | Decimal/cell loss; printed 9.3, 13.7, 19.3, 24.4 not reliably reconstructed |

High mean OCR confidence did not imply financial correctness. The probe is FAILED / REVIEW, with only candidate text retained. The source shows close TWD 644.00 and target TWD 855.00. A 250-DPI info crop was made for human inspection; it was not an OCR retry. Heavy OCR and the requested 350-DPI last retry have not run.
## Required next version procedure
- Run native text, layout and single/dual table candidates first; stop only the region whose structural and semantic gates pass.
- For remaining regions, render a light OCR crop and retain image hash, DPI, language/model, PSM, coordinates and token confidence.
- Escalate failed regions to a configured heavier OCR/layout engine; do not rerun successful regions. Verify model availability and language support first.
- If still unresolved, rerender those regions at 350 DPI and retry within bounded attempts. Keep the final failure explicit rather than inventing values.
- Use field and geometry gates: dates, decimal/sign preservation, headers, cell positions, target/current/prior distinctions and arithmetic. Confidence alone cannot authorize acceptance.
Traditional Chinese OCR is currently unavailable because only eng/osd models are present. Baseline CONFIG still has ocr_enabled=False. The staged scheduler, heavy-engine adapter, language provisioning and 350-DPI acceptance tests remain pending.

# 9 Text hierarchy figures and analyst contacts
## Text restoration
restore_text joins lines only inside the same zone and outside child table/figure boundaries. split_sentences protects decimals, abbreviations and email-like strings while producing sentence or heading records. tidy_text collapses redundant whitespace, removes CJK inter-character spacing and preserves English word boundaries. tidy_cell removes whitespace inside normalized table cells; raw source text remains alongside it.
heading_type uses size relative to the body baseline: H1 at 1.5× or above, H2 at 1.25×, H3 at 1.1× or bold/structural heading evidence. Heading candidates are capped at 65 characters. Adjacent wrapped H1/H2 lines with compatible fonts can join; bullet-only and body-text cases have safeguards. Observed counts are H1 15, H2 16 and H3 33. These are heuristic classes, not universal typography semantics.
## Figures
Keep figure number, title, crop, embedded/native chart text and source separately from table cells. A plotted label does not automatically become a numeric observation. The current pipeline retains six first-page figure crops and native labels where available; it does not recover every vector path or reconstruct chart data series.
## Analyst and broker association
extract_contacts uses email, Taiwan/Hong Kong telephone and role patterns. It seeks a printed analyst name above the contact line within roughly 40 points vertically and ±85 points horizontally; same-row phone association uses a wider horizontal window and less than 3 points center-Y difference. An email local part is a name candidate only, never an asserted person identity by itself.
| Evidence | Rule or retained distinction |
| --- | --- |
| Email | ASCII local-part pattern plus domain; raw address retained |
| Broker domains | jpmorgan.com, morganstanley.com, kgi.com, ctbcsis.com, entrust.com.tw, ubs.com, citi.com, gs.com, macquarie.com |
| Phone | Taiwan 886/local area codes, Hong Kong 852, optional extension; pattern is heuristic |
| Roles | Analyst, Research Analyst, Senior Analyst, Research Associate, Managing Director, Head of Research and Chinese equivalents |
| Validation | Printed KGI/Huanan names and MS +852 2848-7310 linkage included in fixtures |

The exact EMAIL_RX, PHONE_RX, ROLE_RX and DOMAIN_BROKERS are preserved in the source and method registry. A matched number is not proof of dialability or ownership. Unlinked contacts must remain review candidates rather than being assigned by proximity alone.

# 10 Metadata rating target prices EPS and valuation
FILENAME, FORMAT and SIZE come from the actual file, while REPORT_DATE, TICKER, NAME and BROKER combine source observations and explicit candidates. Source precedence and conflicts must remain visible. For P06, printed 2025-12-06 conflicts with the filename date 2025-12-08; the output preserves the conflict instead of silently choosing the filename.
## Ratings and target prices
Preserve the printed rating wording. Do not collapse Buy, Overweight, Outperform and local-language ratings into one meaning without a separate mapping. Current and prior target prices are separate fields and observations, even when equal. Entity extraction combines ENG396 target_prices with native label/number alignment; the fallback associates a label with a numeric line to its right within 110 points and less than 3 points center-Y difference.
| Report | Current TP | Prior TP |
| --- | --- | --- |
| P01 | 1275 | Not captured |
| P02 | Not captured | Not captured |
| P03 | 4388 | Not captured |
| P04 | 104 | 85 |
| P05 | 2600 | 2600 |
| P06 | 300 | 330 |
| P07 | Not captured | Not captured |
| P08 | 1780 | Not captured |

“Not captured” is not proof that a value is absent from the document. Body prose may also contain ratings and targets; retain each source occurrence rather than overwriting a first-page observation.
## Annual EPS
valuation_and_eps separates annual periods from quarter/growth rows and handles transposed financial tables. N is the report-year anchor; N+1 and N+2 follow the annual year. Diluted status is asserted only when printed explicitly. PRE_TAX remains distinct from basic/unspecified, adjusted and consensus measures. Source duplicates are retained.
Verified examples: KGI 3665 annual EPS 2026 / 2027 / 2028 is 66.09 / 106.99 / 145.75; quarterly 4Q26 EPS 20.98 must not become annual EPS. Huanan 3017 annual after-tax EPS 2025 / 2026 is 49.06 / 73.89; pre-tax 72.63 / 111.86 is a different measure.
## Valuation lexicon
ENG395 v0100 reads 16 method IDs: VAL_PE, PB, PS, PEG, DY, EV_EBITDA, EV_SALES, EV_EBIT, DCF, DDM, RIM, NAV, SOTP, COMPS, MA and BAND (each with VAL_ prefix). Actual matches were PE 3 and BAND 1. Unmatched expressions remain candidates for controlled SSOT expansion; the formal rulebook was not modified.

# 11 Table validation and preserved source discrepancies
validate_table uses canonical metric aliases, explicit period columns and displayed-precision rounding tolerance. It skips growth sections and Diff/YoY/QoQ comparison columns where additive identities do not apply. The test result is a separate derived record; it never overwrites a source cell.
| Identity | Treatment |
| --- | --- |
| Gross profit | Revenue − absolute cost |
| Operating profit | Gross profit − absolute operating expense |
| Balance sheet | Assets = liabilities + equity |
| Margin | Relevant profit ÷ revenue × 100; guard undefined division |
| Rounding | Propagate precision tolerance of displayed input and output values |
| Unrecognized rows | No broad fuzzy identity or blanket claim of full validation |

## Three CTBC discrepancies requiring review
P06-P003-T01, 4Q25(F), adjustment-before column: revenue 596, gross profit 595, operating profit 185 and net profit 159. The original source crop was checked visually. All three printed margins remain unchanged and flagged.
| Margin | Printed | Calculated from source |
| --- | --- | --- |
| Gross | 56.5% | 99.832215% |
| Operating | 21.9% | 31.040268% |
| Net | 16.9% | 26.677852% |

The system cannot infer which source figure is wrong. It must not replace the printed margins with computed values or force revenue to make the percentages agree. By contrast, 3Q25 gross profit 466 / revenue 467 yields about 99.7858%; a printed 100% is compatible with the implemented displayed-precision tolerance.
## What 153 passing checks mean
They show that the supported identities, on selected mapped cells, are numerically compatible under the implemented tolerance. They do not validate every table row, accounting classification, unit, source date or financial statement. Independent official-history validation is still pending. The three failures are expected retained evidence and do not make the regression test suite fail.
Regression fixtures also protect MS COGS (41,768), KGI revenue 16,995, CTBC revenue 1,058, a negative -20.2ppts cell and a merged 4Q25(F) header. These target observed reconstruction errors; they are not a corpus-wide accuracy study.

# 12 VDF names historical data and adjusted prices
## Official name lookup actually performed
VDF MDL009 v0101 normalizes the offline TWSE/TPEX snapshots. TWSE has 1,093 source rows dated 2026-08-04; TPEX has 890 dated 2026-08-05. The normalized lookup has 1,977 names. Source row totals and unique-name counts need not be identical. All eight sample ticker names were matched; these are August snapshots, not a fresh October 5 network lookup.
## Read only database adapter
VRN_VDFCacheReader supports CSV, JSON, Parquet, DuckDB and SQLite; .db is treated as SQLite. alias_frame maps ticker, date, Close, Adj Close, source, download vintage and financial metric fields. scan filters requested tickers and records paths/schema outcomes. Synthetic CSV and DuckDB tests confirmed unchanged input bytes and correct alias handling. They do not establish that the user’s real database was read.
Candidate roots include C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\dict\VDF\DATABASE and C:\Users\tonyk\OneDrive\<Desktop>\tw_stock\StockData.parquet, plus local cache paths. The Windows roots are inaccessible here. A previous dry-run database skeleton or report-derived staging CSV is not independent official history.
## Historical financial comparison gap
compare requires the same ticker, period, metric, unit and consolidation basis. Current restored tables do not populate unit_confirmed and basis_confirmed; therefore merely supplying a cache will not complete this feature. Populate these fields from printed evidence, normalize periods and map metrics explicitly before invoking comparison. Forecast differences must be FORECAST_VARIANCE rather than asserted extraction errors.
## Price and target adjustment gap
No real Close or Adj Close was retrieved. yfinance was absent, ordinary installation timed out and an elevated installation request was rejected by automatic environment approval policy. Cached Close must never substitute for missing Adj Close. Conflicting same-key price rows remain excluded/reviewed; downloaded vintage and source must be retained.
The adapter contemplates current TP × AdjClose/Close on the applicable price date. This is a proposed adjustment convention, not a validated valuation result. Previous target adjustment needs that target’s original issue date. The prior available cache date is only a prior-trading-day candidate until calendar and cache completeness are checked. Exact as-of daily close and intraday price are distinct; do not substitute one for the other.

# 13 Canonical time fields and source SSOT requirements
The latest requested date specification is not fully implemented in v0101. Some period_headers still retain FY, E or (F), and REPORT_DATE_DISPLAY can use slash formatting. The next version must add canonical fields while preserving the source spelling separately.
| Meaning | Canonical value | Separate metadata |
| --- | --- | --- |
| Year | 2026 | period_raw=FY2026E; forecast_status=estimate |
| Month | 2026-09 | period_kind=month; calendar/fiscal basis |
| Day | 2026-09-17 | date role, timezone if a timestamp is involved |
| Quarter | 2Q26 | period_kind=quarter; full year=2026 |
| Ambiguous Dec-26 | 2026, 4Q26 or 2026-12 | Resolve using annual/quarter/month table context; otherwise REVIEW |

Canonical values must contain no A/E/F prefixes or suffixes. Forecast/actual status, fiscal year basis, source label, source date and observation identity belong in separate fields. Do not coerce a quarter into a full-year EPS record merely because both contain 26.
## Source identity target contract
source_observation_id: centrally assigned ID, pending registration
source_file_sha256: immutable input identity
page / bbox / table_id / row / column: evidence location
field_or_metric: meaning of the observation
raw_value / normalized_value / normalized_period
unit / basis / forecast_status / extraction_method
engine_version / model_version / source_vintage
status / repair_method / related_observation_ids
This is a proposed contract, not a claim that every listed key already exists. Current report/block/table IDs provide local lineage. Formal central SSOT observation numbering has not been completed. Two sources reporting the same value must receive distinct observation identities linked to a common entity/metric; equality is not a deduplication key.
P05 current target 2600 and prior target 2600 illustrate the rule: the two observations remain separate because their roles and sources differ. A broker forecast and an official actual value must likewise remain separate even when their numbers coincide. Never invent a central SSOT number in a local handover to make registration appear complete.

# 14 Accelerator TEMP and bounded processing
## Current execution versus requested coverage
The table router uses a three-worker thread pool. VeritasCeleritas v1141 was imported and passed apply_thread_limits(2) plus xrun(lambda returning a small dictionary). That proves a small invocation works; it does not prove acceleration of extraction, OCR, cache reads, validation or export. No speed-up benchmark was run. The locked source hash is in engine_inventory.
SUP MDL867 TempSpill v0100 exposes temp_root, activate, purge, run_dir, doc_dir, done, connect, collect, read_csv_chunks, status and selftest. It was read, not activated. Its available integration points include TMP/TEMP/TMPDIR, POLARS_TEMP_DIR, VIA_DUCKDB_TEMP_DIR, DuckDB temp_directory/memory_limit/threads and CSV chunks (default 200,000). Current cache readers can load whole tables/files into pandas; memory-bounded streaming is not implemented there.
## Concrete integration sequence for the next version
- Resolve the existing accelerator bridge and locked dependency chain; do not patch a locked source or create a competing accelerator.
- Activate an owned TEMP run before heavy work. Allocate reusable artifacts by document hash, page, DPI and engine; keep original PDFs outside cleanup roots.
- Wrap independent, idempotent region work with xrun/xmap or the established accelerate bridge. Preserve result/error contracts. xrun can catch errors and retry/fallback; prevent double execution of mutations.
- Use bounded workers and queues, avoid nested CPU oversubscription, release page/image objects promptly, and spill large tables to disk-backed processing.
- Push ticker/date filters into database queries and use chunked CSV reads. Apply TEMP and memory limits before database/columnar operations.
- Cache successful stages and escalate only failed regions. Do not render every page at 350 DPI. Retain crop hashes and transformation history before cleanup.
- Measure elapsed time, peak RSS, peak TEMP bytes, cache hits, engine attempts and unresolved regions. Compare output equivalence as well as speed.
“Cover all actions with the accelerator” should mean governed scheduling and instrumentation where supported. A Python wrapper cannot guarantee that every third-party engine supports GPU execution. Record the backend actually used. TEMP is a memory-pressure mechanism, not a substitute for bounded concurrency or correct lifetime management.
Purge only owned temporary artifacts after durable provenance and review crops are saved. Do not purge original inputs, the registry, official caches or another process’s TEMP directories.

# 15 Output schemas evidence and regression checks
| Artifact | Purpose and interpretation |
| --- | --- |
| restored_reports.json | Nested document metadata, source records, tables, route decisions and summary |
| StockReportBasicInfo.csv / parquet | Seven core fields plus date conflicts, contacts, ratings, targets, EPS and valuation evidence |
| TextRecords.csv / parquet | TXT/TAB/FIG records; raw text, cleaned text, anchors, component and repair method |
| TableValidation.csv / parquet | Derived formula checks, source inputs and PASS / FAIL_REVIEW outcomes |
| EngineRouting.json / engine_candidates | Per-table candidate outputs, options, scores, errors and retained-grid decision |
| StockPrices / PriceCacheConflicts | Price-enrichment outcome; missing real prices remain missing |
| HistoricalCrosscheck / VDF_CacheAudit | History comparison and cache access/schema audit; currently pending |
| method_registry / TableEngineConfig | Parameters, regexes, restoration conventions and source hashes |
| HTML and page/crop evidence | Human review of restored content, segmentation and source context |
| VerificationReport.json | Regression outcome and explicit limitations; not dataset acceptance |

## Verification already completed
AST parsing/import checks, source-specific reconstructed cells, merged period scope, EPS quarter exclusion, current/prior target separation, printed-date conflict, analyst/phone linkage, read-only synthetic CSV/DuckDB fixtures, no Close-for-Adj-Close substitution and missing-Camelot behavior passed. The 10 financial-page overlays were visually inspected; no crop clipping was observed in that inspection.
The evidence manifest contains hashes for accessible source PDFs, official snapshots, baseline outputs, layout outputs and the OCR probe. It is a integrity/navigation aid; it does not mean every hashed artifact was semantically validated. The full original inputs are not duplicated in the handover ZIP; source hashes let the recipient verify their copies.
## Required new checks
Add position-aware routing tests that catch row/column swaps; OCR date and decimal-preservation fixtures; language-model availability; region-only escalation and bounded 350-DPI retry; ambiguous date normalization; distinct-source SSOT identity; unit/basis qualification; real-cache read-only tests; accelerator error-contract tests; and TEMP cleanup ownership tests. Benchmark only after semantic output parity is established.

# 16 Reproduction commands and operational recovery
Start with the included v0101 bundle and matching input bytes. The bundle preserves code/results; it does not supply all 106 source files, install Camelot, provision OCR models or recreate a complete governed repository. Use Python 3.12-compatible dependencies and the engine versions in the inventory. Java is required for Tabula.
## Baseline extraction from the original project root
python VRN_ReportRestore_v0101.py --offline
python verify_vrn_restore.py
Defaults expect samples/, repo_tools/, deps/ and VRN_FirstPage_Layout_20261005/layout.json beside the main script. When moving the code directory, supply paths explicitly and retain the matching layout and official snapshot dependencies. The next command illustrates user-local Windows operation; it was not executed on the user’s computer.
python VRN_ReportRestore_v0101.py --offline ^
--input-dir "C:\<report-input-folder>" ^
--layout-file "<layout-directory>\layout.json" ^
--output-dir "<new-output-directory>" ^
--database-root "<accessible-VDF-database-root>"
The caret is Windows cmd.exe continuation. In PowerShell use its continuation syntax or a single line. The layout manifest still selects the calibrated sample scope; supplying a larger directory does not automatically enable every file or page. Use a new output directory to preserve baseline evidence.
## Read only VDF cache probe
python VRN_VDFCacheReader_v0101.py \
--report-json VRN_ReportRestore_Output_v0101/restored_reports.json \
--database-root "<accessible-cache-root>" \
--output-dir VDF_CacheProbe
## Failure recovery rules
For a missing dependency, retain its status and continue only through available permitted routes. For an engine timeout/error, preserve the candidate record and crop and escalate that region. For an unreadable input, do not infer metadata as if bytes were parsed. For an ambiguous unit/date/header, retain REVIEW and raw evidence. For a failed financial identity, preserve the original values. For a missing official cache, leave external verification pending rather than validating a report against its own staging data.
Do not run unrestricted package upgrades to reproduce this baseline. The Camelot installer should record version and dependency changes, run representative stream/lattice samples, and return logs before its route is enabled for acceptance.

# 17 Governance state and ordered handover work
Repository guidance requires locked token/chain checks, handoff review, requirements/workflow SSOT registration, new versions rather than locked-source edits, accelerator reuse, command return codes and hashes, numbering audit, panorama checks and closeout evidence. This local handover does not substitute for those steps.
The mirrored VCGC v0142 token command initially failed on missing SUP751 and SUP752 dependencies. After they were fetched, the token gate reached GREEN, but the command stopped with return code 2 because the policy book was absent. Full functions/handoffcheck/SSOT panorama/numbering audit/SDD/checkpoint execution did not follow. An earlier HANDOFF_latest snapshot had GREEN handoff and YELLOW closeout; it is not acceptance of this work.
| Priority | Owner role | Action and acceptance evidence |
| --- | --- | --- |
| 1 | Input / data owner | Provide remaining source bytes and accessible VDF cache; reconcile every manifest item |
| 2 | Camelot installer | Install chosen version; return version/options/logs; real sample tests pass |
| 3 | Pipeline developer | Add position-aware table gates; preserve raw grid and candidate disagreement |
| 4 | OCR developer | Integrate native → light → heavy → 350 DPI region-only flow; MQ TP/date/EPS fixtures pass |
| 5 | Runtime developer | Integrate existing accelerator and TEMP bridge; measured RAM/disk/runtime; no duplicate mutations |
| 6 | Data-model owner | Canonical time fields and independent source observation IDs; ambiguous periods stay REVIEW |
| 7 | VDF integration owner | Populate unit/basis; read real cache; calendar/vintage-aware prices; official historical comparisons |
| 8 | Pipeline developer | Generalize layout detection and support remaining PDF/DOCX/TXT/JPG inputs |
| 9 | Governance owner | Restore full governed chain; register requirements/versions; audits and closeout evidence |
| 10 | Review owner | Review all unresolved regions, source discrepancies and final coverage before acceptance |

Owner roles are suggested handover responsibilities, not claims that a named person has accepted an assignment. The only explicit external installation assignment is Camelot. Existing pending requirements, including full input coverage and controlled routing escalation, must remain open until their own acceptance evidence exists.

# 18 Source references and final acceptance boundary
## Primary implementation evidence
The strongest evidence for this handover is the included local source, exact engine configuration, source-fixture tests, restored JSON, candidate logs, OCR outputs and SHA-256 manifest. Refer to engine_inventory for each module path/hash and function_inventory for signatures. The original working baseline version is v0101; no v0102 production implementation is claimed.
## Upstream documentation for implementation follow up
https://github.com/jsvine/pdfplumber
https://github.com/tabulapdf/tabula-java
https://github.com/camelot-dev/camelot
https://pymupdf.readthedocs.io/
https://github.com/tesseract-ocr/tesseract
https://docling-project.github.io/docling/reference/pipeline_options/
https://github.com/datalab-to/marker
https://developers.llamaindex.ai/llamaparse/general/cli/
https://github.com/tonykuni/movies-dataset/pulls
Upstream links support follow-up implementation, not claims that every product was installed or exercised. Third-party rankings and broad “free/local/non-OCR” assertions from earlier suggested pairings were not adopted as verified facts.
## Acceptance boundary
Completed: source-preserving sample restoration, single/dual candidate routing for available native engines, selected entity/EPS/valuation extraction, arithmetic checks, official snapshot name lookup, read-only cache adapters with synthetic tests, visual crop review and a failed light-OCR probe retained as evidence.
Outstanding: all-input coverage; general layout discovery; real Camelot execution; integrated OCR escalation and 350-DPI retry; full accelerator/TEMP coverage; canonical period/source-ID migration; real VDF prices and official historical comparison; and formal central governance closeout. None of these should be marked complete solely because this handover or the regression suite exists.
The next implementation should preserve this baseline, record a new version and produce a per-input/per-region completion ledger. Every accepted result needs source evidence, actual engine/model versions, the transformation history and a clear review status. Every unresolved result needs a specific failure reason and bounded next action.