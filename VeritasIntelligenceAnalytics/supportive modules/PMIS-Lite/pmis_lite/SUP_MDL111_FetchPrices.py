"""在你本機抓真實價格 → 產出可匯入 VIA 圖表的 CSV（含加權/櫃買指數）。

沙箱無法連 yfinance，這支腳本請在你的 Windows/本機跑（有網路）。
輸出 via_prices.csv：首欄 Date，其餘每欄一個代號 + TAIEX + TPEX，值為 adj close。
再到 VIA_ThreeGroup_Normalized.html 按「匯入真實 CSV」即成實際走勢（基準 2026-01-02=100）。

用法：
  pip install yfinance pandas
  python via_fetch_prices.py            # 預設 2026-01-02 起至今
  python via_fetch_prices.py 2026-01-02 2026-07-01
"""
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====
import sys

TICKERS = {
    # 散熱三雄
    "3017": "3017.TW", "3324": "3324.TW", "3653": "3653.TW",
    # 散熱供應鏈
    "8996": "8996.TW", "6805": "6805.TW", "3013": "3013.TW", "8210": "8210.TW",
    "3483": "3483.TW", "6591": "6591.TW", "2421": "2421.TW", "2486": "2486.TW",
    "6831": "6831.TWO",
    # 電源
    "2308": "2308.TW", "2301": "2301.TW", "6412": "6412.TW", "6203": "6203.TW",
    "6282": "6282.TW", "3015": "3015.TW", "3540": "3540.TW",
    # 指數
    "TAIEX": "^TWII", "TPEX": "^TWOII",
}


def main():
    try:
        import yfinance as yf
        import pandas as pd
    except Exception:
        print("請先安裝：pip install yfinance pandas")
        return
    start = sys.argv[1] if len(sys.argv) > 1 else "2026-01-02"
    end = sys.argv[2] if len(sys.argv) > 2 else None

    frames = {}
    for name, sym in TICKERS.items():
        try:
            df = yf.download(sym, start=start, end=end, auto_adjust=True, progress=False)
            if df is not None and len(df):
                col = "Close" if "Close" in df.columns else df.columns[0]
                frames[name] = df[col]
                print(f"  OK {name:6s} {sym:10s} {len(df)} rows")
            else:
                print(f"  -- {name:6s} {sym:10s} 無資料")
        except Exception as e:
            print(f"  !! {name:6s} {sym:10s} {e}")

    if not frames:
        print("沒有抓到任何資料。")
        return
    out = pd.DataFrame(frames)
    out.index.name = "Date"
    out.to_csv("via_prices.csv", encoding="utf-8-sig")
    print(f"\n完成 → via_prices.csv（{len(out)} 列 / {len(frames)} 欄）")
    print("到 VIA_ThreeGroup_Normalized.html 按「匯入真實 CSV」即成實際走勢。")


if __name__ == "__main__":
    main()
