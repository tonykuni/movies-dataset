"""Deterministic fixtures only. No tests below claim real PDF, market or financial retrieval."""
import copy
import json
import ast
import importlib.util
from pathlib import Path
import VRN_Evidence_Core as v

ROOT=Path(__file__).resolve().parent

def run_tests() -> dict:
    checks={}
    library=json.loads((ROOT/'SYNONYM_LIBRARY.json').read_text(encoding='utf-8'))
    for raw,expected in [('華南-3038-1141128.pdf','2025-11-28'),('CTBC250122.pdf','2025-01-22'),
                         ('CTBC(20)250122.pdf','2025-01-22'),('CTBC20250122.pdf','2025-01-22')]:
        checks['date_'+raw]=v.parse_filename(raw)['dates'][0]['iso']==expected
    checks['invalid_date_not_accepted']=v.parse_filename('20250230.pdf')['dates'][0]['iso'] is None
    checks['long_number_not_date']=v.parse_filename('926708.jpg')['dates'][0]['iso'] is None
    checks['MMDD_year_missing']=v.parse_filename('CTBC0915.pdf')['dates'][0]['status']=='YEAR_MISSING'
    checks['ETF_not_date']=not v.parse_filename('006208.pdf')['dates'] and v.parse_filename('006208.pdf')['codes'][0]['local_code']=='006208'
    checks['protect_ticker_before_split']=v.parse_filename('台積電(2330.TW)-20250122.pdf')['codes'][0]['raw']=='2330.TW'
    checks['year_ambiguity_retained']=v.parse_filename('2026年展望.pdf')['codes'][0]['status']=='YEAR_OR_STOCK_AMBIGUOUS'
    checks['stock_three_platform_match']=v.crosscheck_codes(['2330'],['2330.TW','2330 TT'],'TWSE')['status']=='MATCH'
    checks['code_mismatch_flagged']=v.crosscheck_codes(['2330'],['2317.TW'],'TWSE')['status']=='MISMATCH'
    checks['market_mismatch_flagged']=v.crosscheck_codes(['2330'],['2330.TWO'],'TWSE')['status']=='MARKET_MISMATCH'
    checks['ETF_full_code_not_first_four']=v.crosscheck_codes(['00981A'],['00981B.TW'],'TWSE')['status']=='MISMATCH'
    checks['page1_missing_unverified']=v.crosscheck_codes(['2330'],[],'TWSE')['status']=='INSUFFICIENT_EVIDENCE'
    checks['partial_broker_HuaNan']=v.match_broker_partial('華南投顧-3038-報告.pdf',library)['broker']=='HUANAN'
    checks['partial_broker_exclude_company']=v.match_broker_partial('凱基投顧_2891 中信金_分析師_20250122.pdf',library,['中信金'])['broker']=='KGI'
    checks['Latin_fragment_not_prefix_guess']=v.match_broker_partial('GFHK-report.pdf',library)['status']=='NO_MATCH'
    checks['longest_broker_alias']=v.match_broker_partial('Macquarie Capital-2330.pdf',library)['broker']=='MACQUARIE'
    records=[{'ticker':'6768','source':'TWSE','source_url':'https://www.twse.com.tw/',
              'as_of':'2026-09-01','official_security_name':'志強-KY','market':'TWSE','fixture':True}]
    company=v.official_company('6768',records)
    checks['official_KY_preserved']=company['official_name']=='志強-KY'
    checks['name_never_invented']=v.official_company('2330',[])['official_name'] is None
    checks['official_asof_guard']=v.official_company('6768',records,'2025-01-01')['status']=='OFFICIAL_LOOKUP_REQUIRED'
    lines=[{'id':'l1','page':1,'text':'公司營運持續','font_size':10,'bold':False,'region':'BODY','bbox':[10,100,250,112],'block_id':'b1','column_id':1},
           {'id':'l2','page':1,'text':'成長。目標價 1,200.5 元。','font_size':10,'bold':False,'region':'BODY','bbox':[10,114,250,126],'block_id':'b1','column_id':1},
           {'id':'l3','page':1,'text':'隔欄文字','font_size':10,'bold':False,'region':'BODY','bbox':[300,114,550,126],'block_id':'b2','column_id':2},
           {'id':'l4','page':1,'text':'重要主標題。','font_size':16,'bold':True,'region':'TOP','bbox':[10,20,500,40],'block_id':'b3','column_id':0},
           {'id':'l5','page':1,'text':'Copyright','font_size':6,'bold':False,'region':'FOOTER','bbox':[10,950,300,960],'block_id':'b4','column_id':0},
           {'id':'l6','page':1,'text':'稀釋EPS 單位:新台幣元','font_size':6,'bold':False,'region':'FOOTER','bbox':[10,965,300,975],'block_id':'b5','column_id':0}]
    labeled=v.classify_page1_lines(lines,1000,10)
    repaired=v.repair_lines(labeled)
    checks['title_period_is_not_absolute_rule']=labeled[3]['role']=='MAIN_TITLE'
    checks['footer_irrelevant_only']=labeled[4]['role']=='FOOTER_IRRELEVANT' and labeled[5]['role']=='RELEVANT_SMALL_PRINT'
    checks['repair_CJK_and_preserve_number']=repaired[0]['text']=='公司營運持續成長。' and repaired[1]['text']=='目標價 1,200.5 元。'
    checks['no_cross_column_join']=not any('l2' in r['source_ids'] and 'l3' in r['source_ids'] for r in repaired)
    target={'value':120,'currency':'TWD','share_basis':'2026_SPLIT_BASIS','adjustment_basis':'SAME_PER_SHARE_BASIS','evidence_ids':['p1:target']}
    price={'value':100,'currency':'TWD','share_basis':'2026_SPLIT_BASIS','adjustment_basis':'SAME_PER_SHARE_BASIS','price_type':'ADJUSTED_CLOSE','as_of':'2026-09-18'}
    upside=v.compute_upside(target,price)
    checks['upside20percent']=upside['upside_pct']==20
    checks['currency_mismatch_no_calculation']=v.compute_upside(target,dict(price,currency='USD'))['upside_pct'] is None
    checks['adjustment_mismatch_no_calculation']=v.compute_upside(target,dict(price,adjustment_basis='DIVIDEND_ADJUSTED_DIFFERENT'))['status']=='BASIS_MISMATCH'
    facts=[{'kind':'target_price','page':1,'evidence_ids':['p1:target'],'value':120},
           {'kind':'basic_eps','page':1,'evidence_ids':['p1:eps'],'value':5},
           {'kind':'risk','page':2,'evidence_ids':['p2:risk'],'text':'不得流入首頁摘要'}]
    summary=v.build_four_point_summary(company,'6768.TW',{'text':'營運展望','page':1,'evidence_ids':['p1:heading']},facts,upside)
    checks['four_points']=len(summary['points'])==4
    checks['official_title_format']=summary['header']=='志強-KY(6768.TW)-營運展望'
    checks['wrong_title_code_rejected']=v.build_four_point_summary(company,'2330.TW',{'text':'標題','page':1,'evidence_ids':['x']},[],{})['header'] is None
    checks['basic_not_diluted']=summary['points'][1]['status']=='DILUTED_EPS_NOT_DISCLOSED'
    checks['page2_not_first_page_summary']=summary['points'][3]['status']=='NOT_DISCLOSED_ON_PAGE1'
    cell={'ticker':'6768','period':'2025','concept':'REVENUE','scope':'CONSOLIDATED','currency':'TWD','unit':'THOUSAND',
          'accounting_basis':'IFRS','actual_or_estimate':'ACTUAL','value':100,'evidence_ids':['table1:r1c1']}
    official=dict(cell,source='MOPS',source_url='https://mops.twse.com.tw/',published_at='2026-03-01',fixture=True)
    result=v.reconcile_financial_cells([cell,dict(cell,concept='GROSS_PROFIT',value=20)],[official])
    checks['one_anchor_not_whole_table']=result['alignment_anchor_found'] and not result['table_verified']
    diff=v.reconcile_financial_cells([dict(cell,value=95)],[official])['cells'][0]
    checks['official_history_wins_preserve_difference']=diff['canonical_value']==100 and diff['report']['value']==95 and diff['delta']==-5
    checks['forecast_not_overwritten']=v.reconcile_financial_cells([dict(cell,actual_or_estimate='ESTIMATE',value=110)],[official])['cells'][0]['canonical_value']==110
    checks['basic_diluted_not_joined']=not v.reconcile_financial_cells([dict(cell,concept='EPS_BASIC')],[dict(official,concept='EPS_DILUTED')])['alignment_anchor_found']
    checks['unit_mismatch_not_joined']=not v.reconcile_financial_cells([cell],[dict(official,unit='MILLION')])['alignment_anchor_found']
    checks['point_in_time_no_future']=v.reconcile_financial_cells([cell],[official],'2025-12-31')['cells'][0]['status']=='UNVERIFIED'
    checks['sum_check']=v.check_arithmetic('SUM',[60,40],100,same_basis=True)['status']=='PASS'
    checks['subtract_check']=v.check_arithmetic('SUBTRACT',[100,60],40,same_basis=True)['status']=='PASS'
    checks['divide_margin_check']=v.check_arithmetic('RATIO_PERCENT',[40,100],40,same_basis=True)['status']=='PASS'
    checks['zero_denominator']=v.check_arithmetic('DIVIDE',[40,0],40,same_basis=True)['status']=='ZERO_DENOMINATOR'
    checks['null_not_zero']=v.decimal_value('—') is None and v.decimal_value('0')==0
    checks['parentheses_negative']=v.decimal_value('(1,200.5)')==-1200.5
    checks['numeric_basis_required']=v.check_arithmetic('SUM',[1,2],3)['status']=='BASIS_CHECK_REQUIRED'
    source=(ROOT/'VRN_Evidence_Core.py').read_text(encoding='utf-8')
    ast.parse(source)
    compile(source,'VRN_Evidence_Core.py','exec')
    checks['AST_compile_import']=True
    report={'suite':'VRN workflow fixture tests','checks':checks,'passed':sum(checks.values()),'total':len(checks),
            'all_passed':all(checks.values()),'scope':'Synthetic fixtures and supplied filenames. No live report extraction or live official financial validation.'}
    (ROOT/'VRN_WORKFLOW_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report

def main():
    report=run_tests()
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if not report['all_passed']:
        raise SystemExit(1)

if __name__=='__main__':
    main()
