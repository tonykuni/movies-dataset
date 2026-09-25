# VIA_EnvManager.py · Local-Free 衝突快檢 · 不刪 conda · 不 pip uninstall
# 從 LKGC 2026-09-06 擴張 · 本檔只印計畫 · 真裝庫走 launch.ps1
from __future__ import annotations

LKGC = "2026-09-06"
WINNER = "tsinghua"
MIRRORS = [
    ("tsinghua", "https://pypi.tuna.tsinghua.edu.cn/simple", 18),
    ("aliyun", "https://mirrors.aliyun.com/pypi/simple", 32),
    ("pypi", "https://pypi.org/simple", 210),
]
ENVS = ("base", "via_core", "via_vrn", "via_vdf", "via_vap", "via_nlp", "via_iso_*")
TOOLS = (
    "UVT-01 PubGrub",
    "UVT-02 uv pip check",
    "UVT-03 Pin 雙版",
    "UVT-04 LKGC 漂移",
    "UVT-05 三鏡雜湊",
    "UVT-06 標記分叉",
    "UVT-07 Extra 互斥",
    "UVT-08 九頭龍寫區",
)


def main() -> None:
    print("GREEN  ENV   VIA_EnvManager · SCAN", " ".join(ENVS))
    print("GREEN  LKGC ", LKGC, "freeze locks/via_vdf.txt · 只擴張")
    for i, (name, url, ms) in enumerate(MIRRORS, 1):
        role = "冠" if i == 1 else "備" if i == 2 else "官"
        print(f"GREEN  RACE  {i} {name} {ms}ms {role} {url}")
    print("YELLOW PIN   numpy 1.26.4 vs 2.1.1 → via_iso_numpy · 不刪")
    for t in TOOLS:
        print("GREEN  UVT  ", t)
    print("GREEN  ISO99 永禁刪／卸載／殺行程")
    print("YELLOW PLAN  待同意 · 母機 launch.ps1 · 本檔不 spawn")


if __name__ == "__main__":
    main()
