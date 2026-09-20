# Light dashboard palette

Use a light Muji-like surface with small professional typography. The following Plotly/Seaborn-inspired sequence is intentionally embedded so the standalone HTML remains offline:

| Token | Hex | Use |
|---|---|---|
| `--plotly-blue` | `#4c78a8` | primary navigation, links, stable status |
| `--plotly-teal` | `#55a868` | healthy state, live flow, positive trend |
| `--plotly-coral` | `#c44e52` | alerts, attention, destructive state |
| `--plotly-purple` | `#8172b3` | secondary analytics, classification |
| `--plotly-gold` | `#ccb974` | warning, review, governance |
| `--plotly-cyan` | `#64b5cd` | auxiliary series |

Recommended surfaces:

- Page background: `#f7f8f5` → `#ecefeb`
- Sidebar: `#fcfcf9` → `#f1f4f1`
- Panel: `#fffefb`
- Line: `#dbd9d3`
- Ink: `#282725`
- Muted text: `#77736d`

Use color for state and hierarchy, not decoration. Keep chart series order stable across modules and keep warning/coral distinct from healthy/teal. Do not load a remote Plotly or Seaborn package for this standalone UI; these are visual tokens, not runtime dependencies.
