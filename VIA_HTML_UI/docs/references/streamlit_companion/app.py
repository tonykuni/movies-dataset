from __future__ import annotations

import io
import subprocess
from typing import Any

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="VIA Local Workflow Companion",
    page_icon="VIA",
    layout="wide",
    initial_sidebar_state="auto",
)

WORKFLOW_NODES = [
    {"id": "Data_Ingest", "label": "資料載入", "shape": "diamond", "color": "#4c78a8"},
    {"id": "Preprocess", "label": "資料檢查與前處理", "shape": "box", "color": "#72b7b2"},
    {"id": "Model", "label": "分析／模型", "shape": "box", "color": "#f2cf5b"},
    {"id": "Evaluate", "label": "結果評估", "shape": "ellipse", "color": "#e45756"},
    {"id": "Export", "label": "報告與匯出", "shape": "star", "color": "#54a24b"},
]
WORKFLOW_EDGES = [
    ("Data_Ingest", "Preprocess", "1. 載入"),
    ("Preprocess", "Model", "2. 前處理"),
    ("Model", "Evaluate", "3. 評估"),
    ("Evaluate", "Model", "重新調整"),
    ("Evaluate", "Export", "4. 通過"),
]


def mermaid_source() -> str:
    return """graph LR
    A[資料載入] --> B[資料檢查與前處理]
    B --> C[分析模型]
    C --> D{結果評估}
    D -->|重新調整| C
    D -->|通過| E[報告與匯出]
"""


def graphviz_source() -> str:
    lines = ["digraph VIA {", "  rankdir=LR;", "  graph [bgcolor=transparent, pad=0.15];"]
    for node in WORKFLOW_NODES:
        label = node["label"].replace("/", "／")
        lines.append(
            f'  {node["id"]} [label="{label}", shape={node["shape"]}, '
            f'style="filled,rounded", fillcolor="{node["color"]}"];'
        )
    for source, target, label in WORKFLOW_EDGES:
        style = ', style=dashed' if label == "重新調整" else ""
        lines.append(f'  {source} -> {target} [label="{label}"{style}];')
    lines.append("}")
    return "\n".join(lines)


def render_mermaid(enable_component: bool = False) -> None:
    source = mermaid_source()
    if not enable_component:
        st.info("Mermaid safe text mode：未啟用第三方 iframe component。")
        st.code(source, language="mermaid")
        return
    try:
        import streamlit_mermaid as st_mermaid
    except ImportError:
        st.info("尚未安裝 streamlit-mermaid；目前顯示可攜式 Mermaid 原始定義。")
        st.code(source, language="mermaid")
        return
    st_mermaid.st_mermaid(source, height="400px")


def render_graphviz() -> None:
    source = graphviz_source()
    try:
        rendered = subprocess.run(
            ["dot", "-Tpng"],
            input=source.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        st.image(rendered.stdout, caption="Graphviz static PNG", use_container_width=False)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:  # pragma: no cover - local optional runtime
        st.warning(f"Graphviz dot runtime 不可用，改顯示 DOT 定義：{exc}")
        st.code(source, language="dot")


def render_agraph() -> None:
    try:
        from streamlit_agraph import Config, Edge, Node, agraph
    except ImportError:
        st.info("尚未安裝 streamlit-agraph；目前顯示節點／邊資料表。")
        st.dataframe(pd.DataFrame(WORKFLOW_NODES), use_container_width=True, hide_index=True)
        st.dataframe(
            pd.DataFrame(WORKFLOW_EDGES, columns=["source", "target", "label"]),
            use_container_width=True,
            hide_index=True,
        )
        return

    nodes = [
        Node(
            id=node["id"],
            label=node["label"],
            size=25,
            color=node["color"],
            shape=node["shape"],
        )
        for node in WORKFLOW_NODES
    ]
    edges = [Edge(source=source, target=target, label=label, dashed=label == "重新調整") for source, target, label in WORKFLOW_EDGES]
    config = Config(width="100%", height=430, directed=True, physics=True, hierarchical=False)
    agraph(nodes=nodes, edges=edges, config=config)


def read_csv(uploaded_file: Any) -> pd.DataFrame | None:
    if uploaded_file is None:
        return None
    try:
        return pd.read_csv(io.BytesIO(uploaded_file.getvalue()))
    except Exception as exc:
        st.error(f"CSV 讀取失敗：{exc}")
        return None


def main() -> None:
    st.markdown(
        """
        <style>
        :root { color-scheme: light; }
        .via-note { padding: .65rem .8rem; border: 1px solid #dce5e0; border-radius: 8px; background: #f4f8f5; }
        div[data-testid="stMetricValue"] { font-size: 1.35rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("VIA Local Workflow Companion")
    st.caption("可選的 Python／Streamlit companion；不會改變 VIA 單檔 HTML 的正式執行契約。")

    with st.sidebar:
        st.header("控制面板")
        backend = st.selectbox("工作流後端", ["Mermaid", "Graphviz", "Agraph"], index=0)
        mermaid_component = st.checkbox("啟用 Mermaid component（實驗性）", value=False)
        uploaded = st.file_uploader("匯入 CSV（可選）", type=["csv"])
        st.markdown(
            '<div class="via-note">正式 HTML UI 仍可離線以 file:// 開啟。Streamlit 只在需要 Python 資料分析或互動工作流時啟動。</div>',
            unsafe_allow_html=True,
        )

    frame = read_csv(uploaded)
    metrics = st.columns(3)
    metrics[0].metric("工作流節點", len(WORKFLOW_NODES))
    metrics[1].metric("工作流邊", len(WORKFLOW_EDGES))
    metrics[2].metric("CSV 狀態", "已載入" if frame is not None else "未載入")

    overview, workflow, data_tab = st.tabs(["總覽", "工作流圖表", "CSV 分析"])
    with overview:
        st.subheader("Optional local companion")
        st.write(
            "這個 companion 將附件中的 Streamlit、Mermaid、Graphviz 與 Agraph 方案整理成可選本機模組。"
            "它適合資料分析、工作流探索與 Python 原型；VIA 的 canonical UI、SYNCHRONIZER、localStorage"
            " 與 BroadcastChannel 不會依賴它。"
        )
        st.json(
            {
                "runtime": "optional-local",
                "canonicalStandaloneUnaffected": True,
                "selectedBackend": backend,
                "csvLoaded": frame is not None,
            }
        )

    with workflow:
        st.subheader(f"{backend} 工作流")
        if backend == "Mermaid":
            render_mermaid(mermaid_component)
        elif backend == "Graphviz":
            render_graphviz()
        else:
            render_agraph()

    with data_tab:
        st.subheader("CSV 資料分析")
        if frame is None:
            st.info("請從左側匯入使用者自己的 CSV；此模板不生成虛構分析資料。")
        else:
            st.write(f"資料列：{len(frame)}，欄位：{len(frame.columns)}")
            st.dataframe(frame, use_container_width=True, hide_index=True)
            numeric = frame.select_dtypes(include="number")
            if not numeric.empty:
                st.markdown("#### 數值欄位趨勢")
                st.line_chart(numeric)
            st.download_button(
                "下載目前 CSV",
                data=frame.to_csv(index=False).encode("utf-8-sig"),
                file_name="via-companion-export.csv",
                mime="text/csv",
            )


if __name__ == "__main__":
    main()
