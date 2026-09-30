"""VRN route、批次判決、損毀檔保留及真擷取/Parquet 回歸。"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====


from contextlib import redirect_stdout
import io
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch


def manager_tests(manager):
    checks = []
    with patch.dict(manager.os.environ, {"VIA_FROM_VCGC":"YES"}), patch.object(manager.PRIOR,"read",return_value={"state":"GREEN","rows":["sentinel"]}) as read, redirect_stdout(io.StringIO()):
        checks.append(manager.main(["read","logic","--json"]) == 0 and read.call_args.args == ("logic",None,False))
    with patch.dict(manager.os.environ, {"VIA_FROM_VCGC":"NO"}), redirect_stdout(io.StringIO()):
        checks.append(manager.main(["probe"]) == 2)
    fake = Mock();fake.main.return_value = 7
    with patch.dict(manager.os.environ, {"VIA_FROM_VCGC":"YES"}),patch.object(manager,"_load",return_value=fake):
        checks.append(manager.main(["probe","--input","a","--output","b"]) == 7 and fake.main.call_args.args[0] == ["--input","a","--output","b"])
    print('[VRN 精確入口] fail=' + str(checks.count(False)))
    return int(not all(checks))


def run_tests(probe):
    checks = []
    def check(name, ok):
        checks.append(bool(ok));print(('[OK] ' if ok else '[FAIL] ') + name)
    check("批次失敗回 rc1", probe.summary_rc({"ProcessedFiles":2,"BasicRowsNew":1,"FailedFiles":1}) == 1)
    check("空批次回 rc2", probe.summary_rc({"ProcessedFiles":0}) == 2)
    check("OCR 略過回 rc2", probe.summary_rc({"ProcessedFiles":1,"BasicRowsNew":1,"SkippedOcrFiles":1}) == 2)
    check("處理成功只代表執行通過", probe.summary_rc({"ProcessedFiles":1,"BasicRowsNew":1}) == 0)
    with tempfile.TemporaryDirectory(prefix="vrn-probe-") as temp:
        base = Path(temp)
        body = probe.owner()
        broken = base / "broken.parquet"
        broken.write_bytes(b"intentionally invalid parquet")
        try:
            body.read_existing_parquet(broken,body.BASICINFO_COLUMNS)
            failed = False
        except Exception:
            failed = True
        check("損毀 Parquet 不視为空、不移走來源", failed and broken.read_bytes() == b"intentionally invalid parquet")
        store = probe.load(max(probe.VDF.glob("VDF_ParquetStore_v*.py")),"vrn_probe_store_test")
        data = base / "vdf"
        store.initialize(data)
        csv = base / "tickers.csv"
        csv.write_text('TICKER,NAME\n2330.TW,台積電\n0050.TW,元大台灣50\n6488.TWO,環球晶\n',encoding="utf-8")
        store.import_csv(data,csv)
        mapping = probe.vdf_lookup(data,base/"mapped.csv")
        lookup = body.load_local_ticker_ssot(base/"mapped.csv")
        check("VDF 到 VRN 名稱/市場對照一致", mapping["mapped"] == 2 and lookup['2330']['Name'] == '台積電' and lookup['6488']['YF_TICKER'] == '6488.TWO')
        check("不支援商品明列、不偷偷改代號", mapping["unsupported"] == ["0050.TW"])
        source = base / "20260929_2330_TestBroker.txt"
        source.write_text('Taiwan Semiconductor Manufacturing\nReport Date: 2026-09-29\nTicker: 2330\nRating: BUY\nTarget Price: 1200\nCurrent Price: 1000\nRevenue growth and margin outlook.\n',encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            report = probe.run(source,base/"run",data)
        check("真擷取寫入 Parquet / DuckDB", report['rc'] == 0 and report['actual_counts']['StockReportBasicInfo'] == 1)
        check("兩組 HEADER 與正主一致", [r[0] for r in report['headers']['StockReportBasicInfo']] == body.BASICINFO_COLUMNS and [r[0] for r in report['headers']['StockReportFinancialData']] == body.FINANCIALDATA_COLUMNS)
        check("原檔不變、未啟用線上與 AI", report['input_unchanged'] and report['network_enabled'] is False and report['llm_calls'] == 0)
        check("不得冒稱欄位正確/全樣本通過", report['state'] == 'EXECUTED_REVIEW_REQUIRED' and report['field_accuracy'] == 'REVIEW_REQUIRED')
        try:
            probe.run(source,base/"run")
            refused=False
        except FileExistsError:
            refused=True
        check("不覆写已有成功輸出", refused)
        empty=base/'empty';empty.mkdir()
        check("空輸入不建輸出", probe.run(empty,base/'unused')['rc'] == 2 and not (base/'unused').exists())
        pdf = probe.HERE/'references/intake/PDFRegressionEvidence_v1.0.0_b245/PDFRegressionEvidence_v1.0.0/synthetic_financial_report.pdf'
        if pdf.exists():
            with redirect_stdout(io.StringIO()):
                result=probe.run(pdf,base/'pdf')
            check("倉內合成 PDF 真解析與資料庫輸出", result['rc'] == 0 and result['actual_counts']['StockReportBasicInfo'] == 1)
        else:
            check("倉內合成 PDF fixture 可用", False)
    print(f"[VRN 實測入口] checks={len(checks)}; fail={checks.count(False)}")
    return int(not all(checks))
