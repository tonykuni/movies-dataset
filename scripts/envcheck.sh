#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# envcheck.sh — 監測環境衝突快篩(local free libs Top 8 · uv 加速)
# 鏡像:清華 → 阿里 → 官方 PyPI 兜底(自動探測,失聯即切換)
#
# 用法:
#   scripts/envcheck.sh                 # fast:uv pip check + pipdeptree 衝突警告(秒級)
#   scripts/envcheck.sh full            # fast + deptry + pip-check-reqs + 解析預演
#   scripts/envcheck.sh tree            # 完整依賴樹
#   scripts/envcheck.sh why <pkg>       # 反查:誰依賴 <pkg>
#   scripts/envcheck.sh resolve <spec…> # 裝前衝突預測(pipgrip,免安裝)
#   scripts/envcheck.sh info <pkg>      # 裝前需求預檢(johnnydep)
#   scripts/envcheck.sh lock            # pip-compile 解析預演(pip-tools)
#   scripts/envcheck.sh setup           # 建 .venv 並依 requirements.txt 安裝(uv)
#   scripts/envcheck.sh doctor          # 鏡像連通性 + uv cache 體檢
#
# 環境變數:
#   ENVCHECK_PY      目標直譯器(預設 .venv → python3)
#   ENVCHECK_INDEX   auto|tsinghua|aliyun|official(預設 auto)
#   ENVCHECK_NO_MUTATE=1  full 模式不得在目標環境安裝檢測工具
# ═══════════════════════════════════════════════════════════════════════════
set -uo pipefail

TSINGHUA_URL="https://pypi.tuna.tsinghua.edu.cn/simple"
ALIYUN_URL="https://mirrors.aliyun.com/pypi/simple/"
OFFICIAL_URL="https://pypi.org/simple"
PROBE_TIMEOUT="${ENVCHECK_PROBE_TIMEOUT:-3}"

FAIL_COUNT=0
step() { # step <名稱> <指令…>:執行並記錄 ✔/✘
    local name="$1"; shift
    echo "▶ ${name}"
    if "$@"; then
        echo "  ✔ ${name}"
    else
        echo "  ✘ ${name}(exit=$?)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

probe_url() { # 鏡像連通性探測(curl → wget → 視為可用)
    local url="$1"
    if command -v curl >/dev/null 2>&1; then
        curl -fsS --max-time "$PROBE_TIMEOUT" -o /dev/null "${url%/}/pip/"
    elif command -v wget >/dev/null 2>&1; then
        wget -q --timeout="$PROBE_TIMEOUT" -O /dev/null "${url%/}/pip/"
    else
        return 0
    fi
}

pick_index() { # 決定索引順序並輸出 uv / pip 環境變數(官方永遠兜底)
    local choice="${ENVCHECK_INDEX:-auto}"
    if [ "$choice" = "auto" ]; then
        if probe_url "$TSINGHUA_URL" 2>/dev/null; then choice="tsinghua"
        elif probe_url "$ALIYUN_URL" 2>/dev/null; then choice="aliyun"
        else choice="official"; fi
    fi
    export UV_NO_CONFIG=1  # 索引全由本腳本指定,不受 cwd 設定檔影響
    case "$choice" in
        tsinghua)
            export UV_INDEX="${TSINGHUA_URL} ${ALIYUN_URL}"
            export UV_DEFAULT_INDEX="$OFFICIAL_URL"
            export PIP_INDEX_URL="$TSINGHUA_URL"
            export PIP_EXTRA_INDEX_URL="${ALIYUN_URL} ${OFFICIAL_URL}"
            ;;
        aliyun)
            export UV_INDEX="$ALIYUN_URL"
            export UV_DEFAULT_INDEX="$OFFICIAL_URL"
            export PIP_INDEX_URL="$ALIYUN_URL"
            export PIP_EXTRA_INDEX_URL="$OFFICIAL_URL"
            ;;
        official|*)
            unset UV_INDEX 2>/dev/null || true
            export UV_DEFAULT_INDEX="$OFFICIAL_URL"
            export PIP_INDEX_URL="$OFFICIAL_URL"
            unset PIP_EXTRA_INDEX_URL 2>/dev/null || true
            ;;
    esac
    ENVCHECK_INDEX_CHOSEN="$choice"
    echo "◆ 索引:${choice}(官方 PyPI 兜底)"
}

find_python() { # 目標直譯器:ENVCHECK_PY → .venv → python3 → python
    if [ -n "${ENVCHECK_PY:-}" ]; then echo "$ENVCHECK_PY"; return; fi
    for cand in .venv/bin/python .venv/Scripts/python.exe; do
        if [ -x "$cand" ]; then echo "$cand"; return; fi
    done
    command -v python3 || command -v python
}

require_uv() {
    if ! command -v uv >/dev/null 2>&1; then
        echo "✘ 未找到 uv(Top 1 工具兼加速器)。安裝:"
        echo "    pip install uv -i ${TSINGHUA_URL}"
        echo "    或 https://docs.astral.sh/uv/getting-started/installation/"
        return 1
    fi
}

# ── Top 8 檢測步驟 ──────────────────────────────────────────────────────────
check_uv_pip_check() {  # Top 1:uv pip check(毫秒級)
    uv pip check --python "$PY"
}
check_pip_check() {     # Top 3:pip 內建 check(uv 不在時的退路)
    "$PY" -m pip check
}
check_pipdeptree() {    # Top 2:pipdeptree 衝突警告(僅顯示問題,樹輸出丟棄)
    uvx pipdeptree --python "$PY" --warn fail >/dev/null
}
check_deptry() {        # Top 4:deptry 掃缺依賴/幽靈依賴/未用依賴
    uvx deptry .
}
check_reqs_drift() {    # Top 8:pip-check-reqs(需裝入目標環境才能讀其 metadata)
    if [ "${ENVCHECK_NO_MUTATE:-0}" = "1" ]; then
        echo "  (ENVCHECK_NO_MUTATE=1,略過 pip-check-reqs)"
        return 0
    fi
    uv pip install -q --python "$PY" pip-check-reqs || return 1
    local vbin; vbin="$(dirname "$PY")"
    "$vbin/pip-missing-reqs" --requirements-file=requirements.txt . && \
    "$vbin/pip-extra-reqs" --requirements-file=requirements.txt .
}
check_resolve_dryrun() { # Top 1 延伸:整組 requirements 解析預演(不落地安裝)
    uv pip install --dry-run -q -r requirements.txt --python "$PY"
}

cmd_fast() {
    if command -v uv >/dev/null 2>&1; then
        step "uv pip check(已裝套件相容性)" check_uv_pip_check
        step "pipdeptree --warn fail(依賴樹衝突)" check_pipdeptree
    else
        step "pip check(未裝 uv 的退路)" check_pip_check
    fi
}

cmd_full() {
    cmd_fast
    if [ -f pyproject.toml ] || [ -f requirements.txt ]; then
        step "deptry(依賴宣告 vs 實際 import)" check_deptry
    fi
    if [ -f requirements.txt ]; then
        step "pip-check-reqs(需求清單漂移)" check_reqs_drift
        step "uv --dry-run(整組需求解析預演)" check_resolve_dryrun
    fi
}

cmd_doctor() {
    echo "◆ uv:$(uv --version 2>/dev/null || echo '未安裝')"
    echo "◆ python:$("$PY" --version 2>&1)($PY)"
    for pair in "清華 $TSINGHUA_URL" "阿里 $ALIYUN_URL" "官方 $OFFICIAL_URL"; do
        set -- $pair
        t0="$(date +%s%N)"
        if probe_url "$2" 2>/dev/null; then
            t1="$(date +%s%N)"
            case "$t0$t1" in
                *[!0-9]*) echo "◆ 鏡像 $1:可用" ;;  # 無奈秒精度平台(如 macOS date)
                *)        echo "◆ 鏡像 $1:可用($(( (t1 - t0) / 1000000 ))ms)" ;;
            esac
        else
            echo "◆ 鏡像 $1:失聯"
        fi
    done
    echo "◆ 本次選用:${ENVCHECK_INDEX_CHOSEN}"
    command -v uv >/dev/null 2>&1 && echo "◆ uv cache:$(uv cache dir)" && du -sh "$(uv cache dir)" 2>/dev/null
}

MODE="${1:-fast}"
[ $# -gt 0 ] && shift

pick_index
PY="$(find_python)"
[ -z "$PY" ] && { echo "✘ 找不到 python 直譯器"; exit 2; }

case "$MODE" in
    fast)    require_uv || true; cmd_fast ;;
    full)    require_uv || exit 2; cmd_full ;;
    tree)    require_uv || exit 2; uvx pipdeptree --python "$PY"; exit $? ;;
    why)     require_uv || exit 2; uvx pipdeptree --python "$PY" -r -p "${1:?用法:envcheck.sh why <pkg>}"; exit $? ;;
    resolve) require_uv || exit 2; uvx pipgrip --tree "${@:?用法:envcheck.sh resolve <spec…>}"; exit $? ;;
    info)    require_uv || exit 2; uvx johnnydep "${1:?用法:envcheck.sh info <pkg>}" --fields name version_latest requires; exit $? ;;
    lock)    require_uv || exit 2; uvx --from pip-tools pip-compile --dry-run "${1:-requirements.txt}"; exit $? ;;
    setup)   require_uv || exit 2
             [ -d .venv ] || step "uv venv .venv" uv venv .venv
             PY="$(find_python)"
             [ -f requirements.txt ] && step "uv pip install -r requirements.txt" \
                 uv pip install -q -r requirements.txt --python "$PY" ;;
    doctor)  cmd_doctor; exit 0 ;;
    *) echo "未知模式:$MODE(fast|full|tree|why|resolve|info|lock|setup|doctor)"; exit 2 ;;
esac

echo "───────────────────────────────"
if [ "$FAIL_COUNT" -eq 0 ]; then
    echo "✅ 環境衝突檢測全數通過(python=$PY,索引=${ENVCHECK_INDEX_CHOSEN})"
else
    echo "⚠️  發現 ${FAIL_COUNT} 項問題(python=$PY)——詳見上方 ✘ 步驟輸出"
    exit 1
fi
