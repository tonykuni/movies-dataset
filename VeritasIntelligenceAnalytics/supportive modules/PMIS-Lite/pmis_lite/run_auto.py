"""一鍵執行（給門外漢）：double-click 啟動 → 自動偵測 → 跑完 → 自動開結果頁。

完全不用碰命令列。出錯也不崩潰，把原因寫進 run.log 並開一頁告知。
"""
import os
import sys
import json
import traceback
import webbrowser
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _ensure_auto_config(path):
    """沒有 config.json 就生一份『自動偵測』的最小設定，門外漢零設定可跑。"""
    if os.path.exists(path):
        cfg = json.load(open(path, encoding="utf-8"))
        cfg["auto_detect"] = True          # 一鍵版一律開自動偵測
        json.dump(cfg, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        return
    cfg = {
        "_AUP_REMINDER": "本工具僅讀取您自己有權限的資料，於本機處理、不外傳。請確認符合貴公司 AUP。",
        "owner": "me", "locale": "zh-TW", "auto_detect": True,
        "numbering": {"prefix": "PRJ", "domain": "GEN", "hash_len": 6},
        "classification": {
            "_comment": "product/topic 桶會從你的資料自動長出來；status 用通用關鍵字。",
            "product": {}, "topic": {},
            "status": {"待辦": ["todo", "待辦"], "進行中": ["wip", "進行", "處理中"],
                       "已結": ["done", "完成", "結案", "已結"], "逾期": ["overdue", "逾期", "延遲"]}
        },
        "terms": {"seed": {}},
        "mining": {"min_frequency": 2, "min_confidence": 0.55, "auto_merge": False,
                   "stopwords": ["RD", "PM", "QA", "PE", "IT", "HR"]},
        "sources": [], "attachments": {"dir": "sample_data/attachments", "enabled": True},
        "output": {"store_dir": "ssot_store", "markdown": True, "pptx_template": None}
    }
    json.dump(cfg, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def main():
    cfg_path = os.path.join(HERE, "config.json")
    log_path = os.path.join(HERE, "run.log")
    try:
        _ensure_auto_config(cfg_path)
        from pmis_lite.pipeline import run
        from pmis_lite.report_html import build_html

        result = run(cfg_path)
        store_dir = json.load(open(cfg_path, encoding="utf-8"))["output"]["store_dir"]
        if not os.path.isabs(store_dir):
            store_dir = os.path.join(HERE, store_dir)
        html_path = os.path.join(store_dir, f"result_{datetime.now():%Y%m%d}.html")
        build_html(result, html_path)

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M} OK · {len(result['records'])} 筆 · "
                    f"完整性 {result['audit'].overall()['status']}\n")
        print("\n完成。開啟結果頁：", html_path)
        webbrowser.open("file://" + os.path.abspath(html_path))
    except Exception as e:
        err = traceback.format_exc()
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M} ERROR\n{err}\n")
        # 出錯也給門外漢一頁看得懂的說明
        msg_path = os.path.join(HERE, "error.html")
        with open(msg_path, "w", encoding="utf-8") as f:
            f.write(f"<meta charset='utf-8'><body style='font-family:sans-serif;padding:40px'>"
                    f"<h2>這次沒跑成功</h2><p>原因已記錄在 run.log。常見原因：缺少套件、找不到資料夾。</p>"
                    f"<pre style='background:#f5f4f0;padding:14px;border-radius:8px;white-space:pre-wrap'>"
                    f"{e.__class__.__name__}: {e}</pre>"
                    f"<p>把 run.log 給協助你的人看即可，不需驚動 IT。</p></body>")
        print("發生錯誤，已寫入 run.log：", e)
        try:
            webbrowser.open("file://" + os.path.abspath(msg_path))
        except Exception:
            pass


if __name__ == "__main__":
    main()
