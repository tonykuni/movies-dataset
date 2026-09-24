#!/usr/bin/env python3
"""Read-only, redacted map of the repository's current authentication surfaces.

This tool reports evidence; it neither grants access nor changes consent gates.
"""

import argparse
import json
import os
import re
from pathlib import Path


# Configuration: scan only active source families, never output or key files.
DEFAULT_ROOT = Path(__file__).resolve().parents[1]
VIA_DIR = "VeritasIntelligenceAnalytics"
REGISTRY_DIR = "supportive modules/registry"
NETWORK_DIR = "supportive modules/network"
FRED_DIR = "functional modules/VDF/engine"
SOURCE_LIMIT = 1_000_000
SCRAPE_TOKEN = "I_ACCEPT_RESPONSIBLE_SCRAPING"


def latest(directory: Path, family: str) -> Path | None:
    """Find a numbered active source, without reading archived versions."""
    candidates = []
    for path in directory.glob(f"{family}_v*.py"):
        match = re.search(r"_v(\d+)\.py$", path.name)
        if match and path.is_file():
            candidates.append((int(match.group(1)), path))
    return max(candidates, default=(0, None))[1]


def source(path: Path | None) -> str:
    if path is None or path.stat().st_size > SOURCE_LIMIT:
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def evidence(root: Path, path: Path | None) -> str:
    return path.relative_to(root).as_posix() if path else "missing"


def check(label: str, body: str, markers: tuple[str, ...], location: str) -> dict:
    return {
        "component": label,
        "state": "PRESENT" if body and all(m in body for m in markers) else "REVIEW",
        "source": location,
    }


def analyze(root: Path, env: dict[str, str]) -> dict:
    """Inspect only named code paths; never inspect credential contents."""
    via = root / VIA_DIR
    app_path = root / "streamlit_app.py"
    app = source(app_path if app_path.exists() else None)
    reg = via / REGISTRY_DIR
    deck_path = latest(reg, "CGC_MDL095_DeckServer")
    gate_path = latest(reg, "CGC_MDL133_ProductGate")
    net_path = latest(via / NETWORK_DIR, "SUP_MDL740_NetUnified")
    fred_path = latest(via / FRED_DIR, "VDF_ENG074_FredMacroSSOT")
    register_files = list(via.glob("Register-VIA-Commands-v*.ps1"))
    register_path = max(register_files, key=lambda p: int(re.search(r"v(\d+)\.ps1$", p.name).group(1))) if register_files else None
    deck, product, net, fred, register = (source(p) for p in (deck_path, gate_path, net_path, fred_path, register_path))

    app_login = bool(re.search(r"\bst\.(?:login|logout|experimental_user)\b|\b(?:authenticator|OAuth|JWT)\b", app, re.I))
    components = [
        {"component": "movie_ui_login", "state": "REVIEW" if app_login or not app else "ABSENT",
         "source": evidence(root, app_path if app else None)},
        check("local_bridge_csrf", deck,
              ("ThreadingHTTPServer((\"127.0.0.1\", PORT)", "secrets.token_urlsafe(32)",
               "hmac.compare_digest(token, self._token())", "origin == self._origin()",
               'fetch_site == "same-origin"', "if not self._trusted_mutation():"),
              evidence(root, deck_path)),
        check("network_consent", net,
              ('CONSENT_ENV = "VIA_NET_CONSENT"', 'SCRAPE_CONSENT_ENV = "VIA_SCRAPE_CONSENT"',
               "def _deny_if_closed()"), evidence(root, net_path)),
        check("fred_api_key", fred,
              ('os.environ.get("FRED_API_KEY"', 'KEY_FILE.read_text(', 'KEY_FILE.write_text(',
               "api_key={key}"), evidence(root, fred_path)),
        check("secret_fingerprint_audit", product, ("KEY_EXCLUDE", "sha256", '"G6"'),
              evidence(root, gate_path)),
    ]
    commands = [name for name in ("via-gates", "via-productgate", "via-netbench")
                if re.search(r"function\s+global:" + name + r"\b", register, re.I)]
    consent = {
        "network": "OPEN" if env.get("VIA_NET_CONSENT") == "YES" else "CLOSED",
        "scrape": "OPEN" if env.get("VIA_SCRAPE_CONSENT") == SCRAPE_TOKEN else "CLOSED",
        "fred_key": "SET" if env.get("FRED_API_KEY") else "UNSET_OR_FILE",
    }
    return {
        "kind": "static_read_only_audit",
        "sources": components,
        "existing_commands": commands,
        "command_source": evidence(root, register_path),
        "current_environment": consent,
        "findings": [
            "本機 CSRF 權杖保護請求，並非使用者身分驗證或產品授權。",
            "FRED key 可由環境、忽略追蹤的本機純文字檔或互動輸入提供；程式亦允許 --fred-key 命令列參數。",
            "FRED 請求把 key 放在 HTTPS URL 查詢參數；避免記錄完整 URL。",
            "靜態證據只涵蓋目前尾版；未執行服務，也未讀取任何 key 檔。",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--json", action="store_true", help="輸出不含憑證值的 JSON")
    args = parser.parse_args()
    root = args.root.resolve()
    if not (root / "streamlit_app.py").is_file() or not (root / VIA_DIR).is_dir():
        parser.error("--root 必須指向 movies-dataset 的根目錄")
    report = analyze(root, dict(os.environ))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for item in report["sources"]:
            print(f"{item['component']:25} {item['state']:7} {item['source']}")
        print("既有指令：" + ", ".join(report["existing_commands"]))
        print("同意閘：" + json.dumps(report["current_environment"], ensure_ascii=False))
        for finding in report["findings"]:
            print("- " + finding)
    return 0 if all(x["state"] != "REVIEW" for x in report["sources"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
