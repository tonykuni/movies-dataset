# Macro SSOT — VIA Master Registry
_Build date: 2026-05-26 · Schema version: 1.0.0_

**Totals:** 219 series · 9 derived models · 15 sources

**Naming convention:** `{Region}.{Macro_Theme}.{Sub_Theme}.{Indicator}`

---

## Series Registry by Theme

### Prices  · 44 series

| via_code | FRED/source ID | Indicator | Source | Freq | Unit |
|---|---|---|---|---|---|
| `EU.Prices.HICP.Core` | `CPHPLA01EZM659N` | EU HICP Core YoY | Eurostat | Monthly | Percent |
| `EU.Prices.HICP.Headline` | `CP0000EZ19M086NEST` | EU HICP All Items | Eurostat | Monthly | Index 2015=100 |
| `US.Prices.CPI.Apparel` | `CPIAPPSL` | Apparel | BLS | Monthly | Index |
| `US.Prices.CPI.Core` | `CPILFESL` | Core CPI (ex Food & Energy) | BLS | Monthly | Index 1982-84=100 |
| `US.Prices.CPI.Core.YoY` | `CPILFESL` | Core CPI YoY | BLS | Monthly | Percent |
| `US.Prices.CPI.Electricity` | `CUUR0000SEHF01` | Electricity | BLS | Monthly | Index |
| `US.Prices.CPI.Energy` | `CPIENGSL` | Energy | BLS | Monthly | Index |
| `US.Prices.CPI.Food` | `CPIUFDSL` | Food | BLS | Monthly | Index |
| `US.Prices.CPI.FoodAtHome` | `CUSR0000SAF11` | Food at Home | BLS | Monthly | Index |
| `US.Prices.CPI.FoodAwayFromHome` | `CUSR0000SEFV` | Food Away from Home | BLS | Monthly | Index |
| `US.Prices.CPI.FuelOil` | `CUSR0000SEHE` | Fuel Oil | BLS | Monthly | Index |
| `US.Prices.CPI.Gasoline` | `CUUR0000SETB01` | Gasoline | BLS | Monthly | Index |
| `US.Prices.CPI.Headline` | `CPIAUCSL` | CPI Headline | BLS | Monthly | Index 1982-84=100 |
| `US.Prices.CPI.Headline.YoY` | `CPIAUCSL` | CPI YoY | BLS | Monthly | Percent |
| `US.Prices.CPI.LodgingAwayFromHome` | `CUSR0000SEHB` | Lodging Away From Home | BLS | Monthly | Index |
| `US.Prices.CPI.MedicalCare` | `CPIMEDSL` | Medical Care | BLS | Monthly | Index |
| `US.Prices.CPI.MedicalCommodities` | `CUSR0000SAM1` | Medical Commodities | BLS | Monthly | Index |
| `US.Prices.CPI.MedicalServices` | `CUSR0000SAM2` | Medical Services | BLS | Monthly | Index |
| `US.Prices.CPI.MotorInsurance` | `CUUR0000SETA05` | Motor Vehicle Insurance | BLS | Monthly | Index |
| `US.Prices.CPI.NewVehicles` | `CUUR0000SETA01` | New Vehicles | BLS | Monthly | Index |
| `US.Prices.CPI.OER` | `CUSR0000SEHC` | Owners' Equivalent Rent | BLS | Monthly | Index |
| `US.Prices.CPI.Rent` | `CUSR0000SEHA` | Rent of Primary Residence | BLS | Monthly | Index |
| `US.Prices.CPI.RentOfShelter` | `CUSR0000SAS2RS` | Rent of Shelter | BLS | Monthly | Index |
| `US.Prices.CPI.Services` | `CUSR0000SAS` | Services | BLS | Monthly | Index |
| `US.Prices.CPI.ServicesLessRentOfShelter` | `CUSR0000SASL2RS` | Services Less Rent of Shelter (supercore proxy) | BLS | Monthly | Index |
| `US.Prices.CPI.Shelter` | `CUSR0000SAH1` | Shelter | BLS | Monthly | Index |
| `US.Prices.CPI.Transportation` | `CUUR0000SAT` | Transportation Services | BLS | Monthly | Index |
| `US.Prices.CPI.UsedCars` | `CUSR0000SETA02` | Used Cars & Trucks | BLS | Monthly | Index |
| `US.Prices.CPI.UtilityGas` | `CUUR0000SEHF02` | Utility Gas | BLS | Monthly | Index |
| `US.Prices.Export` | `IQ` | Export Price Index | BLS | Monthly | Index 2000=100 |
| `US.Prices.Import` | `IR` | Import Price Index | BLS | Monthly | Index 2000=100 |
| `US.Prices.PCE.Core` | `PCEPILFE` | Core PCE | BEA | Monthly | Index 2017=100 |
| `US.Prices.PCE.Core.YoY` | `PCEPILFE` | Core PCE YoY | BEA | Monthly | Percent |
| `US.Prices.PCE.Goods` | `DGDSRG3M086SBEA` | PCE Goods Prices | BEA | Monthly | Index 2017=100 |
| `US.Prices.PCE.Headline` | `PCEPI` | PCE Headline | BEA | Monthly | Index 2017=100 |
| `US.Prices.PCE.Headline.YoY` | `PCEPI` | PCE YoY | BEA | Monthly | Percent |
| `US.Prices.PCE.Services` | `DSERRG3M086SBEA` | PCE Services Prices | BEA | Monthly | Index 2017=100 |
| `US.Prices.PPI.AllCommodities` | `PPIACO` | PPI All Commodities | BLS | Monthly | Index 1982=100 |
| `US.Prices.PPI.ExFoodEnergy` | `PPICOR` | PPI Ex Food & Energy (Core) | BLS | Monthly | Index |
| `US.Prices.PPI.FinalDemand` | `PPIFID` | PPI Final Demand | BLS | Monthly | Index |
| `US.Prices.PPI.FinalDemand.Goods` | `WPSFD49207` | PPI Final Demand Goods | BLS | Monthly | Index |
| `US.Prices.PPI.FinalDemand.Services` | `WPSFD4131` | PPI Final Demand Services | BLS | Monthly | Index |
| `US.Prices.PPI.IntermediateDemand` | `WPSID61` | PPI Intermediate Demand Processed | BLS | Monthly | Index |
| `US.Prices.PPI.Unprocessed` | `WPSID62` | PPI Intermediate Demand Unprocessed | BLS | Monthly | Index |

### Labor  · 26 series

| via_code | FRED/source ID | Indicator | Source | Freq | Unit |
|---|---|---|---|---|---|
| `US.Labor.AvgHourlyEarnings` | `CES0500000003` | Avg Hourly Earnings | BLS | Monthly | Dollars |
| `US.Labor.AvgHourlyEarnings.YoY` | `CES0500000003` | AHE YoY | BLS | Monthly | Percent |
| `US.Labor.AvgWeeklyHours` | `AWHAETP` | Avg Weekly Hours | BLS | Monthly | Hours |
| `US.Labor.ConstructionPayrolls` | `USCONS` | Construction Payrolls | BLS | Monthly | Thousands |
| `US.Labor.ContinuingClaims` | `CCSA` | Continuing Claims | DOL | Weekly | Number |
| `US.Labor.ECI` | `ECIALLCIV` | Employment Cost Index | BLS | Quarterly | Index |
| `US.Labor.ECI.Benefits` | `ECIBEN` | ECI Benefits | BLS | Quarterly | Index |
| `US.Labor.ECI.Wages` | `ECIWAG` | ECI Wages | BLS | Quarterly | Index |
| `US.Labor.EmpPopRatio` | `EMRATIO` | Employment-Population Ratio | BLS | Monthly | Percent |
| `US.Labor.GovtPayrolls` | `USGOVT` | Government Payrolls | BLS | Monthly | Thousands |
| `US.Labor.InitialClaims` | `ICSA` | Initial Jobless Claims | DOL | Weekly | Number |
| `US.Labor.InsuredUnempRate` | `IURSA` | Insured Unemployment Rate | DOL | Weekly | Percent |
| `US.Labor.JOLTS.Hires` | `JTSHIL` | Hires | BLS | Monthly | Thousands |
| `US.Labor.JOLTS.JobOpenings` | `JTSJOL` | Job Openings | BLS | Monthly | Thousands |
| `US.Labor.JOLTS.Layoffs` | `JTSLDL` | Layoffs & Discharges | BLS | Monthly | Thousands |
| `US.Labor.JOLTS.Quits` | `JTSQUL` | Quits | BLS | Monthly | Thousands |
| `US.Labor.JOLTS.Separations` | `JTSTSL` | Total Separations | BLS | Monthly | Thousands |
| `US.Labor.MfgPayrolls` | `MANEMP` | Manufacturing Payrolls | BLS | Monthly | Thousands |
| `US.Labor.NFP` | `PAYEMS` | Nonfarm Payrolls | BLS | Monthly | Thousands |
| `US.Labor.NFP.MoM` | `PAYEMS` | NFP MoM Change | BLS | Monthly | Thousands |
| `US.Labor.ParticipationRate` | `CIVPART` | Labor Force Participation Rate | BLS | Monthly | Percent |
| `US.Labor.PrivatePayrolls` | `USPRIV` | Private Payrolls | BLS | Monthly | Thousands |
| `US.Labor.Productivity` | `OPHNFB` | Output Per Hour Nonfarm Business | BLS | Quarterly | Index |
| `US.Labor.UnempRate.U3` | `UNRATE` | Unemployment Rate U3 | BLS | Monthly | Percent |
| `US.Labor.UnempRate.U6` | `U6RATE` | U6 Underemployment Rate | BLS | Monthly | Percent |
| `US.Labor.UnitLaborCosts` | `ULCNFB` | Unit Labor Costs Nonfarm | BLS | Quarterly | Index |

### Business  · 26 series

| via_code | FRED/source ID | Indicator | Source | Freq | Unit |
|---|---|---|---|---|---|
| `CN.Business.PMI.Mfg.NBS` | `CHNMFGPMI` | China NBS Mfg PMI | NBS | Monthly | Index |
| `CN.Business.PMI.NonMfg.NBS` | `CHNNMFPMI` | China NBS NonMfg PMI | NBS | Monthly | Index |
| `EU.Business.PMI.Mfg` | `EUGLORPMI` | EU Mfg PMI | S&P Global | Monthly | Index |
| `EU.Business.PMI.Svc` | `EUSVPMI` | EU Svc PMI | S&P Global | Monthly | Index |
| `JP.Business.PMI.Mfg` | `JPNMFGPMI` | Japan Mfg PMI | Jibun Bank | Monthly | Index |
| `US.Business.ConsumerConfidence` | `CSCICP03USM665S` | Conference Board Consumer Confidence | ConfBoard | Monthly | Index |
| `US.Business.ISM.Mfg.Employment` | `NAPMEI` | ISM Mfg Employment | ISM | Monthly | Index |
| `US.Business.ISM.Mfg.Inventories` | `NAPMII` | ISM Mfg Inventories | ISM | Monthly | Index |
| `US.Business.ISM.Mfg.NewOrders` | `NAPMNOI` | ISM Mfg New Orders | ISM | Monthly | Index |
| `US.Business.ISM.Mfg.PMI` | `NAPM` | ISM Mfg PMI Headline | ISM | Monthly | Index |
| `US.Business.ISM.Mfg.Prices` | `NAPMPRI` | ISM Mfg Prices Paid | ISM | Monthly | Index |
| `US.Business.ISM.Mfg.Production` | `NAPMPI` | ISM Mfg Production | ISM | Monthly | Index |
| `US.Business.ISM.Mfg.SupplierDeliveries` | `NAPMSDI` | ISM Mfg Supplier Deliveries | ISM | Monthly | Index |
| `US.Business.ISM.Svc.BusinessActivity` | `NMFBAI` | ISM Svc Business Activity | ISM | Monthly | Index |
| `US.Business.ISM.Svc.Employment` | `NMFEI` | ISM Svc Employment | ISM | Monthly | Index |
| `US.Business.ISM.Svc.NewOrders` | `NMFNOI` | ISM Svc New Orders | ISM | Monthly | Index |
| `US.Business.ISM.Svc.PMI` | `NMFCI` | ISM Services PMI | ISM | Monthly | Index |
| `US.Business.ISM.Svc.Prices` | `NMFPI` | ISM Svc Prices Paid | ISM | Monthly | Index |
| `US.Business.LEI` | `USSLIND` | Conference Board LEI | ConfBoard | Monthly | Index |
| `US.Business.NFIB` | `NFIB` | NFIB Small Business Optimism | NFIB | Monthly | Index |
| `US.Business.RegionalFed.DallasFed` | `BACTSAMFRBDAL` | Dallas Fed Mfg Outlook | FRBDallas | Monthly | Diffusion Index |
| `US.Business.RegionalFed.EmpireState` | `GACDFSA066MSFRBNY` | Empire State Mfg Survey | FRBNY | Monthly | Diffusion Index |
| `US.Business.RegionalFed.PhillyFed` | `GACDISA066MSFRBPHI` | Philly Fed Business Survey | FRBPhilly | Monthly | Diffusion Index |
| `US.Business.SPG.PMI.Mfg` | `USMFGPMI` | S&P Global Mfg PMI | S&P Global | Monthly | Index |
| `US.Business.UMichExpectations` | `MICH` | U Mich Inflation Expectations | UMich | Monthly | Percent |
| `US.Business.UMichSentiment` | `UMCSENT` | U Mich Consumer Sentiment | UMich | Monthly | Index |

### Growth  · 14 series

| via_code | FRED/source ID | Indicator | Source | Freq | Unit |
|---|---|---|---|---|---|
| `US.Growth.CapUtil` | `TCU` | Capacity Utilization | Fed | Monthly | Percent |
| `US.Growth.DurableGoods.Core` | `NEWORDER` | Core Cap Goods Orders ex Defense ex Aircraft | Census | Monthly | Millions USD |
| `US.Growth.DurableGoods.Total` | `DGORDER` | Durable Goods Total Orders | Census | Monthly | Millions USD |
| `US.Growth.GDP.Deflator` | `GDPDEF` | GDP Deflator | BEA | Quarterly | Index |
| `US.Growth.GDP.GCE` | `GCE` | Govt Consumption & Investment | BEA | Quarterly | Billions USD |
| `US.Growth.GDP.GPDI` | `GPDI` | Gross Private Investment | BEA | Quarterly | Billions USD |
| `US.Growth.GDP.NetExports` | `NETEXP` | Net Exports | BEA | Quarterly | Billions USD |
| `US.Growth.GDP.Nominal` | `GDP` | Nominal GDP | BEA | Quarterly | Billions USD |
| `US.Growth.GDP.PCE` | `PCEC96` | PCE Real | BEA | Quarterly | Billions 2017 USD |
| `US.Growth.GDP.QoQ.Annualized` | `A191RL1Q225SBEA` | Real GDP QoQ Annualized | BEA | Quarterly | Percent |
| `US.Growth.GDP.Real` | `GDPC1` | Real GDP | BEA | Quarterly | Billions 2017 USD |
| `US.Growth.GDPNow` | `GDPNOW` | Atlanta Fed GDPNow | Atlanta Fed | Weekly | Percent |
| `US.Growth.IndProd.Mfg` | `IPMAN` | Industrial Production Mfg | Fed | Monthly | Index 2017=100 |
| `US.Growth.IndProd.Total` | `INDPRO` | Industrial Production Total | Fed | Monthly | Index 2017=100 |

### Consumer  · 8 series

| via_code | FRED/source ID | Indicator | Source | Freq | Unit |
|---|---|---|---|---|---|
| `US.Consumer.Credit.CardDelinquency` | `DRCCLACBS` | Credit Card Delinquency Rate | Fed | Quarterly | Percent |
| `US.Consumer.DPI` | `DSPI` | Disposable Personal Income | BEA | Monthly | Billions USD |
| `US.Consumer.PersonalIncome` | `PI` | Personal Income | BEA | Monthly | Billions USD |
| `US.Consumer.PersonalSpending` | `PCE` | Personal Consumption Expenditure | BEA | Monthly | Billions USD |
| `US.Consumer.RetailSales` | `RSAFS` | Retail Sales Total | Census | Monthly | Millions USD |
| `US.Consumer.RetailSales.Control` | `RSSTHD` | Retail Sales Control Group | Census | Monthly | Millions USD |
| `US.Consumer.RetailSales.ExAuto` | `RSFSXMV` | Retail Sales Ex Auto | Census | Monthly | Millions USD |
| `US.Consumer.SavingsRate` | `PSAVERT` | Personal Savings Rate | BEA | Monthly | Percent |

### Housing  · 14 series

| via_code | FRED/source ID | Indicator | Source | Freq | Unit |
|---|---|---|---|---|---|
| `US.Housing.BuildingPermits.SingleFamily` | `PERMIT1` | Building Permits Single Family | Census | Monthly | Thousands SAAR |
| `US.Housing.BuildingPermits.Total` | `PERMIT` | Building Permits Total | Census | Monthly | Thousands SAAR |
| `US.Housing.ExistingHomeSales` | `EXHOSLUSM495S` | Existing Home Sales | NAR | Monthly | Millions SAAR |
| `US.Housing.Mortgage.15Y` | `MORTGAGE15US` | 15-Year Fixed Mortgage Rate | Freddie Mac | Weekly | Percent |
| `US.Housing.Mortgage.30Y` | `MORTGAGE30US` | 30-Year Fixed Mortgage Rate | Freddie Mac | Weekly | Percent |
| `US.Housing.NAHB.Index` | `NAHBMMI` | NAHB Housing Market Index | NAHB | Monthly | Index |
| `US.Housing.NewHomeSales` | `HSN1F` | New Home Sales | Census | Monthly | Thousands SAAR |
| `US.Housing.PendingHomeSales` | `HSN1FNSA` | Pending Home Sales Index | NAR | Monthly | Index |
| `US.Housing.Prices.CaseShiller10` | `SPCS10RSA` | Case-Shiller 10-City | S&P | Monthly | Index |
| `US.Housing.Prices.CaseShiller20` | `SPCS20RSA` | Case-Shiller 20-City | S&P | Monthly | Index |
| `US.Housing.Prices.FHFA` | `USSTHPI` | FHFA House Price Index | FHFA | Quarterly | Index |
| `US.Housing.Starts.MultiFamily` | `HOUST5F` | Housing Starts 5+ Multi-Family | Census | Monthly | Thousands SAAR |
| `US.Housing.Starts.SingleFamily` | `HOUST1F` | Housing Starts Single Family | Census | Monthly | Thousands SAAR |
| `US.Housing.Starts.Total` | `HOUST` | Housing Starts Total | Census | Monthly | Thousands SAAR |

### Fiscal  · 18 series

| via_code | FRED/source ID | Indicator | Source | Freq | Unit |
|---|---|---|---|---|---|
| `US.Fiscal.DTS.NetFlow` | `_derived` | DTS Net Flow (Receipts - Outlays) | Treasury_FD | Daily | Millions USD |
| `US.Fiscal.DTS.OperatingCashBalance` | `v1/accounting/dts/op` | DTS Operating Cash Balance (TGA) | Treasury_FD | Daily | Millions USD |
| `US.Fiscal.DTS.PublicDebtIssues` | `v1/accounting/dts/pu` | DTS Public Debt Cash Issues | Treasury_FD | Daily | Millions USD |
| `US.Fiscal.DTS.PublicDebtRedemptions` | `v1/accounting/dts/pu` | DTS Public Debt Cash Redemptions | Treasury_FD | Daily | Millions USD |
| `US.Fiscal.DTS.TotalOutlays` | `v1/accounting/dts/de` | DTS Daily Total Withdrawals (Outlays) | Treasury_FD | Daily | Millions USD |
| `US.Fiscal.DTS.TotalReceipts` | `v1/accounting/dts/de` | DTS Daily Total Deposits (Receipts) | Treasury_FD | Daily | Millions USD |
| `US.Fiscal.Debt.HeldByPublic` | `FYGFDPUN` | Federal Debt Held by Public | Treasury | Annual | Millions USD |
| `US.Fiscal.Debt.NetInterest` | `FYOINT` | Federal Net Interest Outlays | OMB | Annual | Millions USD |
| `US.Fiscal.Debt.ToGDP` | `GFDEGDQ188S` | Federal Debt to GDP | Treasury | Quarterly | Percent |
| `US.Fiscal.Debt.TotalPublic` | `GFDEBTN` | Total Public Debt Outstanding | Treasury | Quarterly | Millions USD |
| `US.Fiscal.MTS.DeficitSurplus` | `v1/accounting/mts/mt` | MTS Current Month Deficit/Surplus | Treasury_FD | Monthly | Millions USD |
| `US.Fiscal.MTS.GrossOutlays` | `v1/accounting/mts/mt` | MTS Current Month Gross Outlays | Treasury_FD | Monthly | Millions USD |
| `US.Fiscal.MTS.GrossReceipts` | `v1/accounting/mts/mt` | MTS Current Month Gross Receipts | Treasury_FD | Monthly | Millions USD |
| `US.Fiscal.MTS.OutlaysByFunction` | `v1/accounting/mts/mt` | Outlays by Function (Defense/SocSec/Medicare/etc) | Treasury_FD | Monthly | Millions USD |
| `US.Fiscal.MTS.ReceiptsBySource` | `v1/accounting/mts/mt` | Receipts by Source (Indiv/Corp/Excise/Customs/etc) | Treasury_FD | Monthly | Millions USD |
| `US.Fiscal.MTS.YTD.DeficitSurplus` | `v1/accounting/mts/mt` | MTS YTD Deficit/Surplus | Treasury_FD | Monthly | Millions USD |
| `US.Fiscal.MTS.YTD.Outlays` | `v1/accounting/mts/mt` | MTS YTD Outlays | Treasury_FD | Monthly | Millions USD |
| `US.Fiscal.MTS.YTD.Receipts` | `v1/accounting/mts/mt` | MTS YTD Receipts | Treasury_FD | Monthly | Millions USD |

### Fed  · 18 series

| via_code | FRED/source ID | Indicator | Source | Freq | Unit |
|---|---|---|---|---|---|
| `US.Fed.BalanceSheet.BankReserves` | `WRESBAL` | Total Bank Reserves | Fed | Weekly | Billions USD |
| `US.Fed.BalanceSheet.MBS` | `WSHOMCB` | Fed Holdings of MBS | Fed | Weekly | Millions USD |
| `US.Fed.BalanceSheet.ReverseRepo` | `RRPONTSYD` | Overnight Reverse Repo (RRP) | FRBNY | Daily | Billions USD |
| `US.Fed.BalanceSheet.TGA` | `WTREGEN` | Treasury General Account (TGA) | Treasury | Weekly | Millions USD |
| `US.Fed.BalanceSheet.Total` | `WALCL` | Fed Total Assets (WALCL) | Fed | Weekly | Millions USD |
| `US.Fed.BalanceSheet.Treasuries` | `TREAST` | Fed Holdings of US Treasuries | Fed | Weekly | Millions USD |
| `US.Fed.ForwardGuidance.DotPlot` | `https://www.federalr` | FOMC Dot Plot Projections | Fed | Quarterly | Percent |
| `US.Fed.ForwardGuidance.FOMC.Statements` | `https://www.federalr` | FOMC Statement Text | Fed | PerMeeting | text |
| `US.Fed.MoneySupply.M1` | `M1SL` | M1 Money Supply | Fed | Monthly | Billions USD |
| `US.Fed.MoneySupply.M2` | `M2SL` | M2 Money Supply | Fed | Monthly | Billions USD |
| `US.Fed.MoneySupply.M2.YoY` | `M2SL` | M2 YoY | Fed | Monthly | Percent |
| `US.Fed.Rates.DiscountRate` | `INTDSRUSM193N` | Discount Rate (Primary Credit) | Fed | Monthly | Percent |
| `US.Fed.Rates.EFFR` | `EFFR` | Effective Federal Funds Rate (daily) | FRBNY | Daily | Percent |
| `US.Fed.Rates.FedFundsEffective` | `DFF` | Effective Fed Funds Rate | Fed | Daily | Percent |
| `US.Fed.Rates.FedFundsTarget.Lower` | `DFEDTARL` | Fed Funds Target Lower Bound | Fed | Daily | Percent |
| `US.Fed.Rates.FedFundsTarget.Upper` | `DFEDTARU` | Fed Funds Target Upper Bound | Fed | Daily | Percent |
| `US.Fed.Rates.IORB` | `IORB` | Interest on Reserve Balances | Fed | Daily | Percent |
| `US.Fed.Rates.SOFR` | `SOFR` | Secured Overnight Financing Rate | FRBNY | Daily | Percent |

### Rates  · 23 series

| via_code | FRED/source ID | Indicator | Source | Freq | Unit |
|---|---|---|---|---|---|
| `US.Rates.BreakEven.10Y` | `T10YIE` | 10Y Breakeven Inflation | Fed | Daily | Percent |
| `US.Rates.BreakEven.5Y` | `T5YIE` | 5Y Breakeven Inflation | Fed | Daily | Percent |
| `US.Rates.BreakEven.5Y5Y` | `T5YIFR` | 5Y5Y Forward Inflation | Fed | Daily | Percent |
| `US.Rates.Credit.CCC_OAS` | `BAMLH0A3HYC` | ICE BofA CCC OAS Spread | ICE/Fed | Daily | Percent |
| `US.Rates.Credit.HY_OAS` | `BAMLH0A0HYM2` | ICE BofA HY OAS Spread | ICE/Fed | Daily | Percent |
| `US.Rates.Credit.IG_OAS` | `BAMLC0A0CM` | ICE BofA IG OAS Spread | ICE/Fed | Daily | Percent |
| `US.Rates.Spread.2s10s` | `T10Y2Y` | 10Y-2Y Spread | Fed | Daily | Percent |
| `US.Rates.Spread.3m10y` | `T10Y3M` | 10Y-3M Spread (NY Fed Recession Model) | Fed | Daily | Percent |
| `US.Rates.TIPS.10Y` | `DFII10` | 10Y TIPS Real Yield | Fed | Daily | Percent |
| `US.Rates.TIPS.20Y` | `DFII20` | 20Y TIPS Real Yield | Fed | Daily | Percent |
| `US.Rates.TIPS.30Y` | `DFII30` | 30Y TIPS Real Yield | Fed | Daily | Percent |
| `US.Rates.TIPS.5Y` | `DFII5` | 5Y TIPS Real Yield | Fed | Daily | Percent |
| `US.Rates.Treasury.10Y` | `DGS10` | 10-Year Treasury | Fed | Daily | Percent |
| `US.Rates.Treasury.1M` | `DGS1MO` | 1-Month Treasury | Fed | Daily | Percent |
| `US.Rates.Treasury.1Y` | `DGS1` | 1-Year Treasury | Fed | Daily | Percent |
| `US.Rates.Treasury.20Y` | `DGS20` | 20-Year Treasury | Fed | Daily | Percent |
| `US.Rates.Treasury.2Y` | `DGS2` | 2-Year Treasury | Fed | Daily | Percent |
| `US.Rates.Treasury.30Y` | `DGS30` | 30-Year Treasury | Fed | Daily | Percent |
| `US.Rates.Treasury.3M` | `DTB3` | 3-Month T-Bill | Fed | Daily | Percent |
| `US.Rates.Treasury.3Y` | `DGS3` | 3-Year Treasury | Fed | Daily | Percent |
| `US.Rates.Treasury.5Y` | `DGS5` | 5-Year Treasury | Fed | Daily | Percent |
| `US.Rates.Treasury.6M` | `DTB6` | 6-Month T-Bill | Fed | Daily | Percent |
| `US.Rates.Treasury.7Y` | `DGS7` | 7-Year Treasury | Fed | Daily | Percent |

### Trade  · 5 series

| via_code | FRED/source ID | Indicator | Source | Freq | Unit |
|---|---|---|---|---|---|
| `US.Trade.DXY.Broad` | `DTWEXBGS` | USD Broad Trade-Weighted Index | Fed | Daily | Index Jan 2006=100 |
| `US.Trade.Goods.Balance` | `BOPGSTB` | Trade Balance Goods | Census/BEA | Monthly | Millions USD |
| `US.Trade.Goods.Exports` | `BOPGEXP` | Goods Exports | Census/BEA | Monthly | Millions USD |
| `US.Trade.Goods.Imports` | `BOPGIMP` | Goods Imports | Census/BEA | Monthly | Millions USD |
| `US.Trade.Services.Balance` | `IEABCS` | Trade Balance Services | BEA | Monthly | Millions USD |

### FinCond  · 4 series

| via_code | FRED/source ID | Indicator | Source | Freq | Unit |
|---|---|---|---|---|---|
| `US.FinCond.ANFCI` | `ANFCI` | Adjusted NFCI | Chicago Fed | Weekly | Index |
| `US.FinCond.NFCI` | `NFCI` | Chicago Fed NFCI | Chicago Fed | Weekly | Index |
| `US.FinCond.SLO.C&I` | `DRTSCIS` | Senior Loan Officer C&I Tightening | Fed | Quarterly | Net Percent |
| `US.FinCond.SLO.CommercialRE` | `DRTSCILM` | Senior Loan Officer CRE Tightening | Fed | Quarterly | Net Percent |

### Sentiment  · 13 series

| via_code | FRED/source ID | Indicator | Source | Freq | Unit |
|---|---|---|---|---|---|
| `US.Sentiment.AAII.Bearish` | `https://www.aaii.com` | AAII Bearish % | AAII | Weekly | Percent |
| `US.Sentiment.AAII.BullBearSpread` | `_derived` | AAII Bull-Bear Spread | AAII | Weekly | Percent |
| `US.Sentiment.AAII.Bullish` | `https://www.aaii.com` | AAII Bullish % | AAII | Weekly | Percent |
| `US.Sentiment.AAII.Neutral` | `https://www.aaii.com` | AAII Neutral % | AAII | Weekly | Percent |
| `US.Sentiment.CNN.FG.Breadth` | `https://production.d` | CNN F&G Breadth Component | CNN | Daily | Index 0-100 |
| `US.Sentiment.CNN.FG.Momentum` | `https://production.d` | CNN F&G Momentum Component | CNN | Daily | Index 0-100 |
| `US.Sentiment.CNN.FG.PutCall` | `https://production.d` | CNN F&G Put/Call Component | CNN | Daily | Index 0-100 |
| `US.Sentiment.CNN.FG.SafeHaven` | `https://production.d` | CNN F&G Safe Haven Demand | CNN | Daily | Index 0-100 |
| `US.Sentiment.CNN.FearGreed` | `https://production.d` | CNN Fear & Greed Composite | CNN | Daily | Index 0-100 |
| `US.Sentiment.MOVE` | `^MOVE` | ICE BofA MOVE (Bond Vol) | Yahoo | Daily | Index |
| `US.Sentiment.SKEW` | `^SKEW` | CBOE SKEW Tail-Risk | Yahoo | Daily | Index |
| `US.Sentiment.VIX` | `^VIX` | CBOE VIX | Yahoo | Daily | Index |
| `US.Sentiment.VVIX` | `^VVIX` | CBOE VVIX (Vol of Vol) | Yahoo | Daily | Index |

### ECB  · 2 series

| via_code | FRED/source ID | Indicator | Source | Freq | Unit |
|---|---|---|---|---|---|
| `EU.ECB.DepositFacilityRate` | `ECBDFR` | ECB Deposit Facility Rate | ECB | Daily | Percent |
| `EU.ECB.MainRefiRate` | `ECBMRRFR` | ECB Main Refinancing Rate | ECB | Daily | Percent |

### BOJ  · 1 series

| via_code | FRED/source ID | Indicator | Source | Freq | Unit |
|---|---|---|---|---|---|
| `JP.BOJ.PolicyRate` | `IRSTCB01JPM156N` | BOJ Policy Rate | BOJ | Monthly | Percent |

### BOE  · 1 series

| via_code | FRED/source ID | Indicator | Source | Freq | Unit |
|---|---|---|---|---|---|
| `UK.BOE.BankRate` | `IUDSOIA` | BOE Bank Rate (SONIA proxy) | BOE | Daily | Percent |

### OECD  · 2 series

| via_code | FRED/source ID | Indicator | Source | Freq | Unit |
|---|---|---|---|---|---|
| `Global.OECD.CLI.G20` | `G20LOLITONOSTSAM` | OECD CLI G20 | OECD | Monthly | Index |
| `Global.OECD.CLI.G7` | `G7LOLITONOSTSAM` | OECD CLI G7 | OECD | Monthly | Index |


---

## Derived Models  · 9 models

### `US.Model.FedPolicy.Stance`

Aggregate Fed policy stance: Tightening / Restrictive Hold / Neutral / Easing / Emergency Easing

- **Formula:** `f(FFR - r_neutral, inflation_gap, unemployment_gap)`
- **Inputs (5):** `US.Fed.Rates.FedFundsTarget.Upper`, `US.Fed.Rates.FedFundsTarget.Lower`, `US.Fed.BalanceSheet.Total`, `US.Prices.PCE.Core.YoY`, `US.Labor.UnempRate.U3`

### `US.Model.FedPolicy.LiquidityImpulse`

Change in net liquidity = Δ(Reserves + RRP_inverse + TGA_inverse). Drives risk assets.

- **Formula:** `Δ(Reserves - RRP - TGA)`
- **Inputs (3):** `US.Fed.BalanceSheet.BankReserves`, `US.Fed.BalanceSheet.ReverseRepo`, `US.Fed.BalanceSheet.TGA`

### `US.Model.USDIndex.PolicyDiff`

USD policy premium = Fed rate minus DXY-weighted G6 policy rates

- **Formula:** `FFR - (ECB*0.576 + BOJ*0.136 + BOE*0.119 + BOC*0.091 + SNB*0.036)`
- **Inputs (4):** `US.Fed.Rates.FedFundsTarget.Upper`, `EU.ECB.DepositFacilityRate`, `JP.BOJ.PolicyRate`, `UK.BOE.BankRate`

### `US.Model.USDIndex.YieldDiff2Y`

Short-end yield differential vs G10 weighted average

- **Formula:** `US2Y - weighted_G10_2Y`
- **Inputs (1):** `US.Rates.Treasury.2Y`

### `US.Model.USDIndex.RiskFactor`

USD as safe-haven proxy = VIX + MOVE + NFCI tightening

- **Formula:** `normalize(VIX) + normalize(MOVE) + normalize(NFCI)`
- **Inputs (3):** `US.Sentiment.VIX`, `US.Sentiment.MOVE`, `US.FinCond.NFCI`

### `US.Model.USDIndex.Composite`

DXY Engine — 4-layer composite (policy / yield / liquidity / risk)

- **Formula:** `0.35*PolicyDiff + 0.30*YieldDiff2Y + 0.10*YieldDiff10Y + 0.15*LiquidityImpulse + 0.10*RiskFactor`
- **Inputs (5):** `US.Model.USDIndex.PolicyDiff`, `US.Model.USDIndex.YieldDiff2Y`, `US.Rates.Spread.2s10s`, `US.Model.FedPolicy.LiquidityImpulse`, `US.Model.USDIndex.RiskFactor`

### `US.Model.YieldCurve.Inversion`

Recession signal: percent of yield curve points inverted

- **Formula:** `count(spread<0) / total_spreads`
- **Inputs (2):** `US.Rates.Spread.2s10s`, `US.Rates.Spread.3m10y`

### `US.Model.Fiscal.MonthlyImpulse`

Monthly fiscal impulse = (Outlays - Receipts) / GDP

- **Formula:** `(MTS_Outlays - MTS_Receipts) / GDP_nominal_monthly`
- **Inputs (3):** `US.Fiscal.MTS.GrossOutlays`, `US.Fiscal.MTS.GrossReceipts`, `US.Growth.GDP.Nominal`

### `US.Model.Sentiment.RiskOnOff`

Composite risk-on/off signal: AAII + CNN F&G + VIX inverse

- **Formula:** `normalize(AAII_Spread) + normalize(CNN_FG) - normalize(VIX)`
- **Inputs (3):** `US.Sentiment.AAII.BullBearSpread`, `US.Sentiment.CNN.FearGreed`, `US.Sentiment.VIX`

