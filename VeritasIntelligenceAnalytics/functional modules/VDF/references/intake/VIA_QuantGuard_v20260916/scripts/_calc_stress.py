from datetime import date, timedelta
import polars as pl
from quant_engine import RiskConfig, calculate_risk_metrics
scenarios={
'flash_crash': [0.01,0.005,-0.25,0.08,-0.04,0.02],
'volatility_spike':[0.001,-0.001,0.002,-0.002,0.003,-0.003,0.12,-0.10,0.08,-0.06],
'missing_gap':[0.01,None,-0.03,0.02,None,0.01,-0.02],
}
for name, returns in scenarios.items():
    frame=pl.DataFrame({'date':[date(2024,1,1)+timedelta(days=i) for i in range(len(returns))], 'ticker':['S']*len(returns), 'ret':returns, 'adj_close':[100.0]*len(returns)})
    cfg=RiskConfig(window=5,min_samples=3 if name=='missing_gap' else 5)
    out=calculate_risk_metrics(frame,config=cfg,return_col='ret')
    print(name, out.tail(1).select(['rolling_sharpe','rolling_sortino','rolling_var','rolling_cvar','rolling_max_drawdown','equity_curve']).to_dicts())
