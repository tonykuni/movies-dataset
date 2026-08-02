"""一鍵示範：python run_demo.py
讀 config.json，跑完整流程，輸出 SSOT + 候選佇列 + Markdown 摘要。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pmis_lite.pipeline import run

if __name__ == "__main__":
    cfg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    result = run(cfg)
    print("\n" + "=" * 70)
    print("完成。以下為 Markdown 摘要預覽：\n")
    print(result["markdown"])
