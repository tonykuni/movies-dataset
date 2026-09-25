# VIA Modern Compact UI System

## Implementation boundary

The VIA deliverables remain standalone `file://` HTML files. Chakra UI, Tailwind, GSAP, OpenType.js, Storybook, Tauri, PySide6, Textual, CustomTkinter, Flet, and Streamlit are therefore treated as design and future-wrapper references rather than remote runtime dependencies. The current implementation reproduces the useful layout behaviors inline so the files remain one-click usable without a server, CDN, package manager, or build step.

## Current inline implementation

| Requested ecosystem | Standalone implementation in this release |
|---|---|
| Chakra UI | Chakra-inspired semantic tokens, compact controls, focus rings, responsive panels, and accessible button/select sizing in inline CSS |
| Tailwind CSS | Inline 8pt spacing tokens: 4, 8, 12, 16, and 24px; responsive utility-like media rules; no Tailwind runtime |
| Golden-ratio typography | Restrained compact scale using 10, 11, 12, 16, and 24px roles so dense dashboards remain readable instead of using oversized article headings |
| Capsize | Capsize-like fixed baseline rhythm through explicit line-height, `font-size-adjust`, tight heading leading, and balanced text wrapping |
| Storybook | `LOCAL UI LAB · component sandbox` in the central UI, showing typography, controls, focus, local-only status, and layout tokens in isolation |
| GSAP | Zero-dependency CSS entrance and interaction motion, including `ui-enter`, hover transitions, and reduced-motion handling |
| OpenType.js | No runtime font parser is loaded; the template uses system font stacks and stable metrics. A future local add-on can register font metadata without changing the core UI |
| Tauri | The current HTML is already suitable as a WebView surface for a future Tauri shell because it has no server dependency |
| PySide6 / PyQt6 | The same state and layout model can be mapped to a future desktop wrapper; no Python GUI runtime is required by the HTML release |
| Textual / CustomTkinter / Flet / Streamlit | Future companion views can consume the v2 JSON state envelope; the browser template remains the canonical lightweight UI |

## Responsive rules

At PC widths, the central UI uses a horizontal workspace with a compact light sidebar, fixed topbar and footer, two-column KPI cards, and a three-column investment research band. At mobile widths, the sidebar becomes an overlay menu, KPI cards remain two columns, investment cards stack vertically, and the SYNCHRONIZER form grid becomes a single-column vertical flow with two-column action buttons where appropriate.

## Verification

The release was checked with real Chromium screenshots at 1440×1000 and 390×844, inline JavaScript syntax checks, file-only external dependency checks, investment range and scope interactions, UI Lab opening, investment template application, add-on API availability, and horizontal overflow assertions. The corrected mobile SYNCHRONIZER launch control is icon-only below 820px to prevent clipping.
