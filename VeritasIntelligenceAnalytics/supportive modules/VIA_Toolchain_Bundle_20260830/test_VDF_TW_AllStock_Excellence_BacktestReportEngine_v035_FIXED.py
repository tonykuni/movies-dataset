import importlib.util, sys
from pathlib import Path
import numpy as np
import pandas as pd

ENGINE = Path(__file__).with_name("VDF_TW_AllStock_Excellence_BacktestReportEngine_v035.py")
spec = importlib.util.spec_from_file_location("v035", ENGINE)
v = importlib.util.module_from_spec(spec)
sys.modules["v035"] = v
spec.loader.exec_module(v)

def test_cny_rule():
    rows = []
    # Two tickers:
    # 1101 = healthy base
    # 1102 = very low prior-year base causing fake high growth
    for ticker in ["1101","1102"]:
        for year in [2024,2025,2026]:
            for month in range(1,13):
                if ticker=="1101":
                    base = 100 + (year-2024)*8 + month
                    if year==2026 and month in [1,2]:
                        base += 25
                else:
                    base = 100 + month
                    if year==2025 and month in [1,2]:
                        base = 20  # abnormal low base
                    if year==2026 and month in [1,2]:
                        base = 60  # +200% YoY but still low vs normal
                rows.append({"ticker":ticker,"period":f"{year}{month:02d}","revenue":base})
    df=pd.DataFrame(rows)
    q=v.def_build_cny_adjusted_monthly_growth(df)

    j26=q[(q.ticker=="1101")&(q.period==pd.Timestamp("2026-01-01"))].iloc[0]
    f26=q[(q.ticker=="1101")&(q.period==pd.Timestamp("2026-02-01"))].iloc[0]
    fake=q[(q.ticker=="1102")&(q.period==pd.Timestamp("2026-01-01"))].iloc[0]
    mar=q[(q.ticker=="1101")&(q.period==pd.Timestamp("2026-03-01"))].iloc[0]

    checks={
        "jan_uses_combined":j26.growth_basis=="JAN_FEB_COMBINED_YOY",
        "feb_uses_combined":f26.growth_basis=="JAN_FEB_COMBINED_YOY",
        "jan_feb_same_yoy":abs(j26.adjusted_yoy-f26.adjusted_yoy)<1e-12,
        "march_single_month":mar.growth_basis=="SINGLE_MONTH_YOY",
        "low_base_rejected":fake.low_base_flag==True,
        "fake_growth_not_quality":fake.growth_quality!="QUALITY_GROWTH",
        "fake_growth_score_zero":float(fake.base_adjusted_growth_score)==0.0,
    }
    failed=[k for k,x in checks.items() if not bool(x)]
    print({"checks":checks,"failed":failed,"fake_yoy":fake.adjusted_yoy,"fake_base_ratio":fake.base_ratio})
    assert not failed, failed

if __name__=="__main__":
    test_cny_rule()
