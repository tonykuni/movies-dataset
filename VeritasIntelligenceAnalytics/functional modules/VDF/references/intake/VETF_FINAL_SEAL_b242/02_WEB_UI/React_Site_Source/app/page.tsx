"use client";

import { ChangeEvent, useMemo, useRef, useState } from "react";
import {
  Activity,
  ArrowDownToLine,
  ArrowUpFromLine,
  BarChart3,
  ChevronDown,
  ChevronUp,
  CircleAlert,
  Database,
  FileJson,
  Filter,
  Layers3,
  LockKeyhole,
  RefreshCcw,
  Search,
  ShieldCheck,
  Sparkles,
  Target,
  Upload,
  UsersRound,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

type ProviderMode = "both" | "fs" | "yf";
type QualityMode = "all" | "PASS" | "REVIEW" | "FAIL";
type SortDirection = "asc" | "desc";
type SortKey = "weight" | "breadth" | "price" | "fsMedian" | "yfMedian" | "peN" | "peN1" | "peN2" | "upside";

type ETF = {
  code: string;
  name: string;
  issuer: string;
  manager: string;
  style: string;
  aum: number;
  nav: number;
  flowYtd: number;
  expense: number;
  sinceListing: number;
  distribution: string;
  returns: number[];
  isNew?: boolean;
};

type ConsensusBlock = {
  low: number | null;
  mean: number | null;
  median: number | null;
  high: number | null;
  analysts: number | null;
};

type Holding = {
  ticker: string;
  name: string;
  sector: string;
  price: number;
  priceDate: string;
  estimatedCost: number | null;
  action: string;
  quality: "PASS" | "REVIEW" | "FAIL";
  flags: string[];
  fundWeights: Record<string, number>;
  fs: ConsensusBlock;
  yf: ConsensusBlock;
  eps: {
    n: number | null;
    n1: number | null;
    n2: number | null;
    yearN: number | null;
    yearN1: number | null;
    yearN2: number | null;
  };
};

type AggregatedHolding = Holding & {
  weight: number;
  breadth: number;
  selectedFundCount: number;
  peN: number | null;
  peN1: number | null;
  peN2: number | null;
  fsUpside: number | null;
  yfUpside: number | null;
  providerGap: number | null;
};

const RETURN_LABELS = ["1D", "5D", "10D", "20D", "60D", "120D", "240D", "YTD"];

const ETF_DATA: ETF[] = [
  { code: "00981A", name: "主動統一台股增長", issuer: "統一投信", manager: "林哲緯", style: "成長", aum: 285, nav: 38.12, flowYtd: 20.2, expense: 0.85, sinceListing: 18.4, distribution: "不配息", returns: [1.0, 0.4, 2.3, 5.6, 6.8, 11.3, 16.0, 14.2] },
  { code: "00982A", name: "主動野村臺灣優選", issuer: "野村投信", manager: "陳柏宇", style: "優選", aum: 246, nav: 38.13, flowYtd: -5.2, expense: 0.89, sinceListing: 15.2, distribution: "不配息", returns: [0.5, 1.1, 2.4, 4.7, 7.2, 10.8, 15.4, 13.7] },
  { code: "00980A", name: "主動安聯台灣高息", issuer: "安聯投信", manager: "黃詩涵", style: "高息", aum: 198, nav: 38.10, flowYtd: -19.3, expense: 0.90, sinceListing: 9.6, distribution: "季配", returns: [0.2, -0.3, 1.6, 2.7, 5.4, 8.9, 12.4, 9.8] },
  { code: "00983A", name: "主動群益台灣強棒", issuer: "群益投信", manager: "張凱程", style: "成長", aum: 164, nav: 38.15, flowYtd: 2.8, expense: 0.88, sinceListing: 16.8, distribution: "不配息", returns: [0.7, 1.4, 2.6, 4.9, 7.5, 11.7, 16.8, 15.0] },
  { code: "00984A", name: "主動野村台灣50", issuer: "野村投信", manager: "吳承翰", style: "優選", aum: 142, nav: 38.17, flowYtd: 7.8, expense: 0.85, sinceListing: 12.1, distribution: "不配息", returns: [0.4, 0.8, 1.9, 3.8, 6.1, 9.5, 13.6, 11.9] },
  { code: "00985A", name: "主動富邦台灣成長", issuer: "富邦投信", manager: "李宗翰", style: "成長", aum: 128, nav: 38.18, flowYtd: 11.9, expense: 0.87, sinceListing: 14.3, distribution: "不配息", returns: [0.8, 1.3, 2.8, 4.5, 7.1, 10.9, 15.8, 13.6] },
  { code: "00986A", name: "主動元大台灣價值", issuer: "元大投信", manager: "周明哲", style: "價值", aum: 116, nav: 38.21, flowYtd: 4.4, expense: 0.86, sinceListing: 11.8, distribution: "半年配", returns: [0.3, 0.7, 1.5, 3.1, 5.8, 8.7, 12.9, 10.7] },
  { code: "00987A", name: "主動中信台灣科技", issuer: "中信投信", manager: "鄭宇晴", style: "科技", aum: 88, nav: 38.25, flowYtd: 8.1, expense: 0.92, sinceListing: 21.5, distribution: "不配息", returns: [1.2, 2.8, 3.1, 3.2, 7.9, 15.3, 21.2, 17.8] },
  { code: "00988A", name: "主動凱基台灣優勢", issuer: "凱基投信", manager: "許博鈞", style: "優選", aum: 79, nav: 38.07, flowYtd: 1.6, expense: 0.90, sinceListing: 10.4, distribution: "不配息", returns: [-0.1, 0.6, 1.7, 3.4, 6.3, 9.1, 13.4, 11.2] },
  { code: "009A01", name: "主動富邦台灣科技", issuer: "富邦投信", manager: "邱柏睿", style: "科技", aum: 22, nav: 15.08, flowYtd: -2.6, expense: 0.91, sinceListing: 15.6, distribution: "不配息", returns: [-0.4, -0.2, 4.0, 2.1, 7.6, 12.3, 16.4, 15.6], isNew: true },
  { code: "009A03", name: "主動元大台股創新", issuer: "元大投信", manager: "范植偉", style: "科技", aum: 17, nav: 15.11, flowYtd: -2.0, expense: 0.93, sinceListing: 16.7, distribution: "不配息", returns: [-0.4, -0.2, 4.3, 2.2, 8.2, 13.3, 17.6, 16.7], isNew: true },
];

const HOLDING_DATA: Holding[] = [
  { ticker: "2330.TW", name: "台積電", sector: "半導體", price: 560, priceDate: "2026-06-22", estimatedCost: 519.5, action: "超額配置", quality: "PASS", flags: [], fundWeights: { "00981A": 28, "00982A": 25, "00980A": 21, "00983A": 27, "00984A": 32, "00985A": 24, "00986A": 18, "00987A": 31, "00988A": 20, "009A01": 29, "009A03": 26 }, fs: { low: 590, mean: 696.2, median: 611.9, high: 760, analysts: 32 }, yf: { low: 580, mean: 664.2, median: 598.1, high: 740, analysts: 28 }, eps: { n: 25.4, n1: 31.2, n2: 36.8, yearN: 2026, yearN1: 2027, yearN2: 2028 } },
  { ticker: "2454.TW", name: "聯發科", sector: "半導體", price: 684, priceDate: "2026-06-22", estimatedCost: 652.7, action: "順勢加碼", quality: "PASS", flags: [], fundWeights: { "00981A": 7.2, "00982A": 5.1, "00983A": 7.8, "00985A": 6.6, "00987A": 9.4, "009A01": 8.1, "009A03": 9.0 }, fs: { low: 720, mean: 794.3, median: 839.5, high: 930, analysts: 25 }, yf: { low: 700, mean: 848.5, median: 717.3, high: 910, analysts: 22 }, eps: { n: 58.5, n1: 69.4, n2: 78.1, yearN: 2026, yearN1: 2027, yearN2: 2028 } },
  { ticker: "2317.TW", name: "鴻海", sector: "AI伺服器", price: 547, priceDate: "2026-06-22", estimatedCost: 485.8, action: "強勢重壓", quality: "REVIEW", flags: ["PROVIDER_DIVERGENCE"], fundWeights: { "00981A": 5.8, "00982A": 7.0, "00983A": 5.4, "00984A": 6.1, "00985A": 8.2, "00986A": 4.1, "00988A": 6.6 }, fs: { low: 560, mean: 627.4, median: 636.2, high: 720, analysts: 27 }, yf: { low: 530, mean: 627.2, median: 595, high: 700, analysts: 21 }, eps: { n: 27.8, n1: 33.5, n2: 39.2, yearN: 2026, yearN1: 2027, yearN2: 2028 } },
  { ticker: "6669.TW", name: "緯穎", sector: "AI伺服器", price: 399, priceDate: "2026-06-22", estimatedCost: 358.2, action: "強勢重壓", quality: "PASS", flags: [], fundWeights: { "00981A": 4.3, "00983A": 5.0, "00985A": 3.7, "00987A": 6.8, "009A01": 5.9, "009A03": 7.1 }, fs: { low: 408, mean: 465.2, median: 418.9, high: 520, analysts: 20 }, yf: { low: 405, mean: 434.9, median: 422.1, high: 500, analysts: 18 }, eps: { n: 19.5, n1: 24.8, n2: 29.9, yearN: 2026, yearN1: 2027, yearN2: 2028 } },
  { ticker: "2382.TW", name: "廣達", sector: "AI伺服器", price: 612, priceDate: "2026-06-22", estimatedCost: 564.6, action: "順勢加碼", quality: "REVIEW", flags: ["TARGET_DATE_AGE_97D"], fundWeights: { "00981A": 3.1, "00982A": 3.5, "00983A": 4.0, "00984A": 3.2, "00985A": 4.8, "00987A": 5.1 }, fs: { low: 650, mean: 751.6, median: 753, high: 840, analysts: 24 }, yf: { low: 640, mean: 687.7, median: 727.6, high: 810, analysts: 19 }, eps: { n: 36.1, n1: 43.8, n2: 49.7, yearN: 2026, yearN1: 2027, yearN2: 2028 } },
  { ticker: "1519.TW", name: "華城", sector: "重電", price: 649, priceDate: "2026-06-22", estimatedCost: 582.6, action: "強勢重壓", quality: "PASS", flags: [], fundWeights: { "00981A": 2.8, "00983A": 2.1, "00985A": 3.6, "00986A": 4.2, "00988A": 3.3 }, fs: { low: 690, mean: 804.2, median: 776.7, high: 890, analysts: 16 }, yf: { low: 680, mean: 689.7, median: 784.2, high: 850, analysts: 14 }, eps: { n: 28.8, n1: 35.4, n2: 41.1, yearN: 2026, yearN1: 2027, yearN2: 2028 } },
  { ticker: "2603.TW", name: "長榮", sector: "航運", price: 833, priceDate: "2026-06-22", estimatedCost: 777.1, action: "順勢加碼", quality: "PASS", flags: [], fundWeights: { "00980A": 3.8, "00982A": 2.4, "00984A": 2.1, "00986A": 3.7, "00988A": 2.7 }, fs: { low: 820, mean: 886.6, median: 900.6, high: 970, analysts: 18 }, yf: { low: 790, mean: 944.4, median: 877.2, high: 960, analysts: 15 }, eps: { n: 92, n1: 85.5, n2: 79.2, yearN: 2026, yearN1: 2027, yearN2: 2028 } },
  { ticker: "2049.TW", name: "上銀", sector: "機器人", price: 279, priceDate: "2026-06-22", estimatedCost: 254.6, action: "強勢重壓", quality: "REVIEW", flags: ["YFINANCE_TARGET_ORDER_INVALID"], fundWeights: { "00981A": 2.3, "00983A": 1.8, "00985A": 2.6, "00986A": 3.2, "00988A": 1.9, "009A03": 2.8 }, fs: { low: 290, mean: 324.4, median: 347.2, high: 380, analysts: 17 }, yf: { low: 285, mean: 301, median: 331.3, high: 365, analysts: 13 }, eps: { n: 13.2, n1: 17.6, n2: 21.9, yearN: 2026, yearN1: 2027, yearN2: 2028 } },
  { ticker: "2308.TW", name: "台達電", sector: "電源管理", price: 538, priceDate: "2026-06-22", estimatedCost: 516.3, action: "逢低承接", quality: "PASS", flags: [], fundWeights: { "00981A": 2.1, "00982A": 1.8, "00983A": 2.0, "00984A": 2.5, "00985A": 2.3, "00986A": 1.9, "00987A": 2.9, "009A01": 3.1 }, fs: { low: 560, mean: 581.2, median: 626, high: 690, analysts: 29 }, yf: { low: 550, mean: 638.6, median: 567.7, high: 680, analysts: 24 }, eps: { n: 21.5, n1: 25.9, n2: 30.4, yearN: 2026, yearN1: 2027, yearN2: 2028 } },
  { ticker: "2327.TW", name: "國巨", sector: "被動元件", price: 557, priceDate: "2026-06-22", estimatedCost: 525.5, action: "順勢加碼", quality: "PASS", flags: [], fundWeights: { "00982A": 2.2, "00983A": 1.9, "00984A": 2.1, "00986A": 2.7, "00987A": 2.3, "00988A": 2.0 }, fs: { low: 570, mean: 680.1, median: 608.6, high: 730, analysts: 23 }, yf: { low: 565, mean: 627.3, median: 588.8, high: 700, analysts: 18 }, eps: { n: 32.4, n1: 39.8, n2: 45.7, yearN: 2026, yearN1: 2027, yearN2: 2028 } },
  { ticker: "3661.TW", name: "世芯-KY", sector: "IC設計", price: 91, priceDate: "2026-06-22", estimatedCost: 80.4, action: "強勢重壓", quality: "PASS", flags: [], fundWeights: { "00981A": 1.9, "00983A": 2.3, "00985A": 1.7, "00987A": 3.2, "009A01": 2.8, "009A03": 3.6 }, fs: { low: 94, mean: 99.8, median: 100.7, high: 112, analysts: 19 }, yf: { low: 92, mean: 102.5, median: 103.5, high: 115, analysts: 16 }, eps: { n: 4.1, n1: 5.3, n2: 6.4, yearN: 2026, yearN1: 2027, yearN2: 2028 } },
  { ticker: "2881.TW", name: "富邦金", sector: "金融", price: 211, priceDate: "2026-06-22", estimatedCost: 206.1, action: "逢低承接", quality: "REVIEW", flags: ["MISSING_EPS_N2"], fundWeights: { "00980A": 2.5, "00982A": 1.8, "00984A": 2.2, "00986A": 3.1, "00988A": 2.6 }, fs: { low: 220, mean: 236.8, median: 240.4, high: 270, analysts: 18 }, yf: { low: 218, mean: 249.2, median: 236.9, high: 275, analysts: 15 }, eps: { n: 14.2, n1: 16.8, n2: null, yearN: 2026, yearN1: 2027, yearN2: 2028 } },
];

const ACTION_STAGES = [
  { no: "一", title: "破冰進場", subtitle: "從無到有", tone: "blue", items: [["首度布局", "第一次買進這家公司，建立持股。"], ["分批建倉", "連續數日增加持股，避免把成本推高。"]] },
  { no: "二", title: "乘勝追擊", subtitle: "由小變大", tone: "coral", items: [["順勢加碼", "股價上漲且主動買進仍為正。"], ["強勢重壓", "持股跨越高分位，形成核心部位。"], ["逢低承接", "價格修正時持股數量增加。"]] },
  { no: "三", title: "動態平衡", subtitle: "持股比重", tone: "teal", items: [["超額配置", "相對基準維持較高配置。"], ["基準配置", "主動交易量位於容忍帶。"], ["欠額配置", "相對基準配置較低但仍持有。"]] },
  { no: "四", title: "高檔防禦", subtitle: "由大變小", tone: "gold", items: [["逢高減碼", "價格快速上升後主動賣出。"], ["獲利調節", "現價高於估計成本且持股下降。"], ["降險減持", "集中度或風險超標後降低部位。"]] },
  { no: "五", title: "決絕離場", subtitle: "從有到無", tone: "green", items: [["獲利清倉", "持股歸零且現價高於估計成本。"], ["停損砍倉", "持股歸零且現價低於估計成本。"]] },
];

const DATA_SOURCES = [
  { name: "TWSE / TPEX", role: "Adj OHLCV · 上市櫃商品身分", state: "READY", tone: "green" },
  { name: "SITCA", role: "ETF 規模 · 費率 · 受益單位", state: "REVIEW", tone: "gold" },
  { name: "MOPS / 投信", role: "每日持股 · 公開說明書", state: "READY", tone: "green" },
  { name: "YFinance", role: "Adj Close · Target Consensus", state: "READY", tone: "green" },
  { name: "FactSet", role: "Target · EPS N～N+2 · Analysts", state: "KEYED", tone: "coral" },
  { name: "VDF Database", role: "Parquet · DuckDB · Append-Only", state: "CANDIDATE", tone: "blue" },
];

const REQUEST_JSON = `{
  "request": "tw_active_etf_consensus_enriched",
  "asof": "latest",
  "universe": { "type": "active_etf", "exchange": ["TWSE", "TPEX"] },
  "fields": [
    "holdings:weight,shares,manager_action",
    "price_adj",
    "target_yf:low,mean,median,high",
    "target_fs:low,mean,median,high",
    "eps_fs:N,N+1,N+2",
    "forward_pe:N,N+1,N+2"
  ],
  "verify": ["double_identity", "asof_no_lookahead", "currency_match"],
  "write_mode": "candidate",
  "sink": "mart_tw_active_etf_holdings_consensus_enriched"
}`;

function numberOrNull(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function formatNumber(value: number | null, digits = 1): string {
  if (value === null || !Number.isFinite(value)) return "—";
  return value.toLocaleString("zh-TW", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function formatPct(value: number | null, digits = 1): string {
  if (value === null || !Number.isFinite(value)) return "—";
  return `${value > 0 ? "+" : ""}${formatNumber(value, digits)}%`;
}

function calculatePe(price: number, eps: number | null): number | null {
  return eps !== null && eps > 0 && price > 0 ? price / eps : null;
}

function calculateUpside(target: number | null, price: number): number | null {
  return target !== null && price > 0 ? (target / price - 1) * 100 : null;
}

function returnClass(value: number): string {
  if (value >= 10) return "heat heat-strong";
  if (value > 0) return "heat heat-up";
  if (value < 0) return "heat heat-down";
  return "heat";
}

function actionTone(action: string): string {
  if (/超額|配置/.test(action)) return "teal";
  if (/重壓|加碼/.test(action)) return "coral";
  if (/承接|減碼/.test(action)) return "gold";
  if (/離場|清倉|停損/.test(action)) return "green";
  return "blue";
}

function qualityTone(value: string): string {
  if (value === "PASS") return "quality-pass";
  if (value === "FAIL") return "quality-fail";
  return "quality-review";
}

function normalizeFlags(value: unknown): string[] {
  if (Array.isArray(value)) return value.map(String);
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value);
      if (Array.isArray(parsed)) return parsed.map(String);
    } catch {
      return value ? [value] : [];
    }
  }
  return [];
}

function recordsToHoldings(records: Record<string, unknown>[]): { holdings: Holding[]; codes: string[] } {
  const grouped = new Map<string, Holding>();
  const codes = new Set<string>();
  records.forEach((record) => {
    const ticker = String(record.ticker ?? record.holding_ticker ?? "").trim();
    const etfCode = String(record.etf_code ?? "UNKNOWN").trim();
    if (!ticker) return;
    codes.add(etfCode);
    const quality = String(record.record_status ?? "REVIEW").toUpperCase();
    const current = grouped.get(ticker) ?? {
      ticker,
      name: String(record.company_name ?? record.name ?? ticker),
      sector: String(record.sector ?? record.industry ?? "未分類"),
      price: numberOrNull(record.price_adj_close) ?? 0,
      priceDate: String(record.price_date ?? record.analysis_date ?? "—"),
      estimatedCost: numberOrNull(record.estimated_cost),
      action: String(record.manager_action ?? "待分類"),
      quality: quality === "PASS" || quality === "FAIL" ? quality : "REVIEW",
      flags: normalizeFlags(record.quality_flags),
      fundWeights: {},
      fs: {
        low: numberOrNull(record.fs_target_low), mean: numberOrNull(record.fs_target_mean),
        median: numberOrNull(record.fs_target_median), high: numberOrNull(record.fs_target_high),
        analysts: numberOrNull(record.fs_target_analyst_count),
      },
      yf: {
        low: numberOrNull(record.yf_target_low), mean: numberOrNull(record.yf_target_mean),
        median: numberOrNull(record.yf_target_median), high: numberOrNull(record.yf_target_high),
        analysts: numberOrNull(record.yf_target_analyst_count),
      },
      eps: {
        n: numberOrNull(record.fs_eps_n_mean), n1: numberOrNull(record.fs_eps_n1_mean),
        n2: numberOrNull(record.fs_eps_n2_mean),
        yearN: numberOrNull(record.fs_eps_n_fiscal_year), yearN1: numberOrNull(record.fs_eps_n1_fiscal_year),
        yearN2: numberOrNull(record.fs_eps_n2_fiscal_year),
      },
    };
    current.fundWeights[etfCode] = numberOrNull(record.holding_weight) ?? 0;
    grouped.set(ticker, current);
  });
  return { holdings: [...grouped.values()], codes: [...codes].filter(Boolean) };
}

function downloadBlob(filename: string, content: string, type: string): void {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function SortButton({ label, sortKey, currentKey, direction, onSort }: { label: string; sortKey: SortKey; currentKey: SortKey; direction: SortDirection; onSort: (key: SortKey) => void }) {
  return (
    <button className="sort-button" onClick={() => onSort(sortKey)} type="button">
      {label}
      {currentKey === sortKey ? direction === "desc" ? <ChevronDown size={12} /> : <ChevronUp size={12} /> : null}
    </button>
  );
}

function MetricCard({ label, value, note, tone, icon }: { label: string; value: string; note: string; tone: string; icon: React.ReactNode }) {
  return (
    <article className={`metric-card metric-${tone}`}>
      <div className="metric-head"><span>{label}</span>{icon}</div>
      <strong>{value}</strong>
      <small>{note}</small>
    </article>
  );
}

export default function Home() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [etfs, setEtfs] = useState(ETF_DATA);
  const [selectedEtfs, setSelectedEtfs] = useState<Set<string>>(new Set(ETF_DATA.map((item) => item.code)));
  const [holdings, setHoldings] = useState(HOLDING_DATA);
  const [search, setSearch] = useState("");
  const [sector, setSector] = useState("all");
  const [quality, setQuality] = useState<QualityMode>("all");
  const [providerMode, setProviderMode] = useState<ProviderMode>("both");
  const [sortKey, setSortKey] = useState<SortKey>("weight");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [dataLabel, setDataLabel] = useState("DEMO SNAPSHOT");
  const [loadMessage, setLoadMessage] = useState("可載入 Adapter JSON 取代示範資料");

  const fundAum = useMemo(() => Object.fromEntries(etfs.map((item) => [item.code, item.aum || 1])), [etfs]);
  const sectors = useMemo(() => [...new Set(holdings.map((item) => item.sector))].sort(), [holdings]);

  const aggregated = useMemo<AggregatedHolding[]>(() => {
    return holdings.map((holding) => {
      const entries = Object.entries(holding.fundWeights).filter(([code]) => selectedEtfs.has(code));
      const denominator = [...selectedEtfs].reduce((total, code) => total + (fundAum[code] ?? 1), 0);
      const numerator = entries.reduce((total, [code, weight]) => total + (fundAum[code] ?? 1) * weight, 0);
      const weight = denominator > 0 ? numerator / denominator : 0;
      const breadth = selectedEtfs.size > 0 ? entries.length / selectedEtfs.size * 100 : 0;
      const fsUpside = calculateUpside(holding.fs.median, holding.price);
      const yfUpside = calculateUpside(holding.yf.median, holding.price);
      const providerGap = holding.fs.median && holding.yf.median
        ? (holding.yf.median - holding.fs.median) / Math.abs(holding.fs.median) * 100
        : null;
      return {
        ...holding,
        weight,
        breadth,
        selectedFundCount: entries.length,
        peN: calculatePe(holding.price, holding.eps.n),
        peN1: calculatePe(holding.price, holding.eps.n1),
        peN2: calculatePe(holding.price, holding.eps.n2),
        fsUpside,
        yfUpside,
        providerGap,
      };
    }).filter((holding) => holding.selectedFundCount > 0);
  }, [fundAum, holdings, selectedEtfs]);

  const filteredHoldings = useMemo(() => {
    const term = search.trim().toLowerCase();
    const rows = aggregated.filter((holding) => {
      const searchPassed = !term || `${holding.ticker} ${holding.name} ${holding.sector}`.toLowerCase().includes(term);
      return searchPassed && (sector === "all" || holding.sector === sector) && (quality === "all" || holding.quality === quality);
    });
    return rows.sort((left, right) => {
      const value = (row: AggregatedHolding) => {
        const mapping: Record<SortKey, number | null> = {
          weight: row.weight, breadth: row.breadth, price: row.price,
          fsMedian: row.fs.median, yfMedian: row.yf.median,
          peN: row.peN, peN1: row.peN1, peN2: row.peN2, upside: row.fsUpside,
        };
        return mapping[sortKey] ?? -Infinity;
      };
      const delta = (value(left) ?? -Infinity) - (value(right) ?? -Infinity);
      return sortDirection === "asc" ? delta : -delta;
    });
  }, [aggregated, quality, search, sector, sortDirection, sortKey]);

  const stats = useMemo(() => {
    const selectedAum = etfs.filter((item) => selectedEtfs.has(item.code)).reduce((sum, item) => sum + item.aum, 0);
    const totalWeight = aggregated.reduce((sum, item) => sum + item.weight, 0);
    const covered = aggregated.filter((item) => item.fs.median !== null && item.eps.n1 !== null);
    const coveredWeight = covered.reduce((sum, item) => sum + item.weight, 0);
    const coverage = totalWeight > 0 ? coveredWeight / totalWeight * 100 : 0;
    const earningsYield = covered.reduce((sum, item) => sum + item.weight / Math.max(coveredWeight, 0.0001) * ((item.eps.n1 ?? 0) / item.price), 0);
    const portfolioPe = earningsYield > 0 ? 1 / earningsYield : null;
    const weightedUpside = covered.reduce((sum, item) => sum + item.weight * (item.fsUpside ?? 0), 0) / Math.max(coveredWeight, 0.0001);
    const reviewCount = aggregated.filter((item) => item.quality !== "PASS").length;
    return { selectedAum, coverage, portfolioPe, weightedUpside, reviewCount };
  }, [aggregated, etfs, selectedEtfs]);

  function toggleEtf(code: string, checked: boolean): void {
    setSelectedEtfs((current) => {
      const next = new Set(current);
      if (checked) next.add(code); else next.delete(code);
      return next;
    });
  }

  function handleSort(key: SortKey): void {
    if (key === sortKey) setSortDirection((current) => current === "desc" ? "asc" : "desc");
    else { setSortKey(key); setSortDirection("desc"); }
  }

  async function handleFile(event: ChangeEvent<HTMLInputElement>): Promise<void> {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const parsed = JSON.parse(await file.text());
      const records = Array.isArray(parsed) ? parsed : parsed.records ?? parsed.data ?? [];
      if (!Array.isArray(records) || records.length === 0) throw new Error("JSON 找不到 records");
      const normalized = recordsToHoldings(records);
      if (normalized.holdings.length === 0) throw new Error("JSON 沒有可辨識的持股資料");
      setHoldings(normalized.holdings);
      const newEtfs = normalized.codes.map((code) => ETF_DATA.find((item) => item.code === code) ?? {
        code, name: `主動式 ETF ${code}`, issuer: "資料來源", manager: "—", style: "未分類",
        aum: 1, nav: 0, flowYtd: 0, expense: 0, sinceListing: 0, distribution: "—", returns: [0, 0, 0, 0, 0, 0, 0, 0],
      });
      setEtfs(newEtfs);
      setSelectedEtfs(new Set(normalized.codes));
      setDataLabel("LOADED CANDIDATE");
      setLoadMessage(`${file.name} · ${records.length} 筆 · ${normalized.holdings.length} 檔個股`);
    } catch (error) {
      setLoadMessage(`載入失敗：${error instanceof Error ? error.message : "未知格式"}`);
    } finally {
      event.target.value = "";
    }
  }

  function resetDemo(): void {
    setEtfs(ETF_DATA);
    setSelectedEtfs(new Set(ETF_DATA.map((item) => item.code)));
    setHoldings(HOLDING_DATA);
    setDataLabel("DEMO SNAPSHOT");
    setLoadMessage("已還原內建示範資料");
  }

  function exportJson(): void {
    downloadBlob("vetf_consensus_filtered.json", JSON.stringify(filteredHoldings, null, 2), "application/json;charset=utf-8");
  }

  function exportCsv(): void {
    const columns = ["ticker", "name", "sector", "weight", "breadth", "price", "fs_target_median", "yf_target_median", "eps_n", "eps_n1", "eps_n2", "forward_pe_n", "forward_pe_n1", "forward_pe_n2", "quality"];
    const rows = filteredHoldings.map((item) => [item.ticker, item.name, item.sector, item.weight, item.breadth, item.price, item.fs.median, item.yf.median, item.eps.n, item.eps.n1, item.eps.n2, item.peN, item.peN1, item.peN2, item.quality]);
    const csv = [columns, ...rows].map((row) => row.map((value) => `"${String(value ?? "").replaceAll('"', '""')}"`).join(",")).join("\n");
    downloadBlob("vetf_consensus_filtered.csv", `\ufeff${csv}`, "text/csv;charset=utf-8");
  }

  return (
    <main className="app-shell">
      <div className="top-stripe" aria-hidden="true"><i /><i /><i /><i /><i /><i /></div>

      <header className="brand-header">
        <div className="brand-lockup">
          <div className="seal" aria-hidden="true">理</div>
          <div>
            <p className="eyebrow">VERITAS INTELLIGENCE ANALYTICS</p>
            <h1>主動式台股 ETF <span>Consensus 戰情台</span></h1>
            <p className="brand-subtitle">Global Market · Industry · Equity · AI Research Intelligence Platform</p>
            <p className="motto">判天地之美，析萬物之理。</p>
          </div>
        </div>
        <div className="header-status">
          <Badge className="status-verified"><ShieldCheck size={13} /> SCHEMA VERIFIED</Badge>
          <span>AS OF 2026/06/22</span>
          <span className="candidate-lock"><LockKeyhole size={12} /> CANDIDATE LOCKED</span>
        </div>
      </header>

      <section className="request-strip" aria-label="資料狀態">
        <div className="request-title"><Sparkles size={15} /> VDF · VETF CONSENSUS ENRICHMENT</div>
        <div className="source-pills">
          <span className="pill pill-blue">TWSE→rest</span>
          <span className="pill pill-teal">MOPS→parse</span>
          <span className="pill pill-green">YFinance→pyproc</span>
          <span className="pill pill-coral">FactSet→keyed</span>
        </div>
        <div className="request-flow">Holdings → Identity → As-of Join → Forward P/E → Audit</div>
      </section>

      <section className="control-bar">
        <div className="data-state">
          <span className="data-label">{dataLabel}</span>
          <span>{loadMessage}</span>
        </div>
        <div className="control-actions">
          <input ref={fileInputRef} className="sr-only" type="file" accept="application/json,.json" onChange={handleFile} />
          <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()}><Upload size={14} /> 載入 Adapter JSON</Button>
          <Button variant="outline" size="sm" onClick={resetDemo}><RefreshCcw size={14} /> 示範資料</Button>
          <Button variant="outline" size="sm" onClick={exportCsv}><ArrowDownToLine size={14} /> CSV</Button>
          <Button variant="outline" size="sm" onClick={exportJson}><FileJson size={14} /> JSON</Button>
        </div>
      </section>

      <section className="metric-grid" aria-label="摘要指標">
        <MetricCard label="已選 ETF" value={`${selectedEtfs.size}`} note={`全部 ${etfs.length} 檔`} tone="coral" icon={<Layers3 size={16} />} />
        <MetricCard label="所選總規模" value={`$${formatNumber(stats.selectedAum, 0)}億`} note="AUM · TWD" tone="blue" icon={<Database size={16} />} />
        <MetricCard label="Consensus 涵蓋" value={`${formatNumber(stats.coverage, 1)}%`} note="FactSet Target + EPS N+1" tone="teal" icon={<ShieldCheck size={16} />} />
        <MetricCard label="組合 Forward P/E" value={`${formatNumber(stats.portfolioPe, 1)}×`} note="N+1 · Earnings Yield Method" tone="gold" icon={<Activity size={16} />} />
        <MetricCard label="FS Median 空間" value={formatPct(stats.weightedUpside, 1)} note="持股權重加權" tone="green" icon={<Target size={16} />} />
        <MetricCard label="待覆核" value={`${stats.reviewCount}`} note="Review / Fail 個股" tone="coral" icon={<CircleAlert size={16} />} />
      </section>

      <Tabs defaultValue="holdings" className="workspace-tabs">
        <TabsList className="main-tab-list">
          <TabsTrigger value="performance"><BarChart3 size={15} />績效矩陣</TabsTrigger>
          <TabsTrigger value="etfs"><Layers3 size={15} />ETF 清單</TabsTrigger>
          <TabsTrigger value="holdings"><UsersRound size={15} />持股 × Consensus</TabsTrigger>
          <TabsTrigger value="actions"><Activity size={15} />動作分類</TabsTrigger>
          <TabsTrigger value="request"><Database size={15} />資料請求</TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="tab-panel">
          <div className="section-title-row">
            <div><p className="section-kicker">PERFORMANCE MATRIX</p><h2>績效排行矩陣</h2></div>
            <span className="section-note">定期報酬 · 紅漲綠跌 · YTD 高至低</span>
          </div>
          <div className="table-shell">
            <Table>
              <TableHeader><TableRow><TableHead>#</TableHead><TableHead>代碼</TableHead><TableHead className="min-w-56">ETF 名稱</TableHead><TableHead>風格</TableHead><TableHead>經理人</TableHead>{RETURN_LABELS.map((label) => <TableHead key={label} className="text-right">{label}</TableHead>)}<TableHead className="text-right">規模(億)</TableHead><TableHead className="text-right">YTD流(億)</TableHead></TableRow></TableHeader>
              <TableBody>{[...etfs].sort((a, b) => b.returns[7] - a.returns[7]).map((item, index) => <TableRow key={item.code}>
                <TableCell className="rank-cell">{index + 1}</TableCell><TableCell><span className="ticker-code">{item.code}</span>{item.isNew && <span className="new-chip">NEW</span>}</TableCell><TableCell className="font-medium">{item.name}</TableCell><TableCell><span className={`style-chip style-${item.style}`}>{item.style}</span></TableCell><TableCell>{item.manager}</TableCell>
                {item.returns.map((value, valueIndex) => <TableCell key={`${item.code}-${valueIndex}`} className={`${returnClass(value)} text-right`}>{formatPct(value, 1)}</TableCell>)}
                <TableCell className="text-right font-semibold">{formatNumber(item.aum, 0)}</TableCell><TableCell className={`text-right ${item.flowYtd >= 0 ? "value-up" : "value-down"}`}>{formatPct(item.flowYtd, 1)}</TableCell>
              </TableRow>)}</TableBody>
            </Table>
          </div>
        </TabsContent>

        <TabsContent value="etfs" className="tab-panel">
          <div className="section-title-row">
            <div><p className="section-kicker">ACTIVE ETF UNIVERSE</p><h2>主動式 ETF 清單</h2></div>
            <div className="selection-actions"><Button variant="outline" size="sm" onClick={() => setSelectedEtfs(new Set(etfs.map((item) => item.code)))}>全選</Button><Button variant="outline" size="sm" onClick={() => setSelectedEtfs(new Set())}>清除</Button></div>
          </div>
          <div className="table-shell">
            <Table><TableHeader><TableRow><TableHead>選</TableHead><TableHead>代碼</TableHead><TableHead>ETF 名稱</TableHead><TableHead>投信</TableHead><TableHead>經理人</TableHead><TableHead>風格</TableHead><TableHead className="text-right">規模(億)</TableHead><TableHead className="text-right">淨值</TableHead><TableHead className="text-right">YTD流</TableHead><TableHead className="text-right">費用率</TableHead><TableHead className="text-right">上市來</TableHead><TableHead>配息</TableHead></TableRow></TableHeader>
            <TableBody>{etfs.map((item) => <TableRow key={item.code} data-selected={selectedEtfs.has(item.code)}><TableCell><Checkbox aria-label={`選擇 ${item.code}`} checked={selectedEtfs.has(item.code)} onCheckedChange={(value) => toggleEtf(item.code, Boolean(value))} /></TableCell><TableCell className="ticker-code">{item.code}</TableCell><TableCell className="font-medium">{item.name}</TableCell><TableCell>{item.issuer}</TableCell><TableCell>{item.manager}</TableCell><TableCell><span className={`style-chip style-${item.style}`}>{item.style}</span></TableCell><TableCell className="text-right font-semibold">{formatNumber(item.aum, 0)}</TableCell><TableCell className="text-right">{formatNumber(item.nav, 2)}</TableCell><TableCell className={`text-right ${item.flowYtd >= 0 ? "value-up" : "value-down"}`}>{formatPct(item.flowYtd, 1)}</TableCell><TableCell className="text-right">{formatPct(item.expense, 2)}</TableCell><TableCell className="text-right value-up">{formatPct(item.sinceListing, 1)}</TableCell><TableCell>{item.distribution}</TableCell></TableRow>)}</TableBody></Table>
          </div>
        </TabsContent>

        <TabsContent value="holdings" className="tab-panel">
          <div className="section-title-row holdings-heading">
            <div><p className="section-kicker">HOLDINGS × CONSENSUS</p><h2>總持股聚合與 Forward Valuation</h2></div>
            <div className="formula-note"><span>AUM 加權持股</span><i>·</i><span>As-of Join</span><i>·</i><span>Portfolio P/E = 1 ÷ Σ(w × EPS/P)</span></div>
          </div>

          <div className="holdings-layout">
            <aside className="fund-panel">
              <div className="fund-panel-head"><div><span>基金勾選</span><small>{selectedEtfs.size} / {etfs.length}</small></div><div><button onClick={() => setSelectedEtfs(new Set(etfs.map((item) => item.code)))}>全</button><button onClick={() => setSelectedEtfs(new Set())}>清</button></div></div>
              <div className="fund-list">{etfs.map((item) => <label key={item.code} className={selectedEtfs.has(item.code) ? "selected" : ""}><Checkbox checked={selectedEtfs.has(item.code)} onCheckedChange={(value) => toggleEtf(item.code, Boolean(value))} /><span><strong>{item.code}</strong>{item.name}</span></label>)}</div>
              <div className="coverage-block"><div><span>雙來源 Target 涵蓋</span><strong>{formatNumber(stats.coverage, 1)}%</strong></div><Progress value={stats.coverage} /></div>
            </aside>

            <div className="holdings-main">
              <div className="filter-toolbar">
                <div className="search-box"><Search size={14} /><Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="搜尋代碼、公司或族群" aria-label="搜尋持股" /></div>
                <Select value={sector} onValueChange={setSector}><SelectTrigger className="compact-select"><SelectValue placeholder="族群" /></SelectTrigger><SelectContent><SelectItem value="all">全部族群</SelectItem>{sectors.map((value) => <SelectItem key={value} value={value}>{value}</SelectItem>)}</SelectContent></Select>
                <Select value={quality} onValueChange={(value) => setQuality(value as QualityMode)}><SelectTrigger className="compact-select"><SelectValue placeholder="品質" /></SelectTrigger><SelectContent><SelectItem value="all">全部品質</SelectItem><SelectItem value="PASS">PASS</SelectItem><SelectItem value="REVIEW">REVIEW</SelectItem><SelectItem value="FAIL">FAIL</SelectItem></SelectContent></Select>
                <div className="provider-toggle" aria-label="Consensus 顯示來源"><button className={providerMode === "both" ? "active" : ""} onClick={() => setProviderMode("both")}>雙源</button><button className={providerMode === "fs" ? "active" : ""} onClick={() => setProviderMode("fs")}>FactSet</button><button className={providerMode === "yf" ? "active" : ""} onClick={() => setProviderMode("yf")}>YF</button></div>
                <span className="result-count"><Filter size={13} />{filteredHoldings.length} 檔</span>
              </div>

              <div className="table-shell holdings-table-shell">
                <Table className="consensus-table">
                  <TableHeader>
                    <TableRow className="group-header"><TableHead colSpan={5}>持股聚合</TableHead><TableHead colSpan={3}>價格與動作</TableHead>{providerMode !== "yf" && <TableHead colSpan={5} className="fs-group">FactSet Target</TableHead>}{providerMode !== "fs" && <TableHead colSpan={5} className="yf-group">YFinance Target</TableHead>}<TableHead colSpan={3} className="eps-group">Consensus EPS</TableHead><TableHead colSpan={3} className="pe-group">Forward P/E</TableHead><TableHead colSpan={2}>驗證</TableHead></TableRow>
                    <TableRow><TableHead>#</TableHead><TableHead className="sticky-company">個股</TableHead><TableHead>族群</TableHead><TableHead><SortButton label="權重" sortKey="weight" currentKey={sortKey} direction={sortDirection} onSort={handleSort} /></TableHead><TableHead><SortButton label="廣度" sortKey="breadth" currentKey={sortKey} direction={sortDirection} onSort={handleSort} /></TableHead><TableHead>動作</TableHead><TableHead>估均價</TableHead><TableHead><SortButton label="Adj Close" sortKey="price" currentKey={sortKey} direction={sortDirection} onSort={handleSort} /></TableHead>
                    {providerMode !== "yf" && <><TableHead className="fs-cell">Low</TableHead><TableHead className="fs-cell">Mean</TableHead><TableHead className="fs-cell"><SortButton label="Median" sortKey="fsMedian" currentKey={sortKey} direction={sortDirection} onSort={handleSort} /></TableHead><TableHead className="fs-cell">High</TableHead><TableHead className="fs-cell"><SortButton label="空間" sortKey="upside" currentKey={sortKey} direction={sortDirection} onSort={handleSort} /></TableHead></>}
                    {providerMode !== "fs" && <><TableHead className="yf-cell">Low</TableHead><TableHead className="yf-cell">Mean</TableHead><TableHead className="yf-cell"><SortButton label="Median" sortKey="yfMedian" currentKey={sortKey} direction={sortDirection} onSort={handleSort} /></TableHead><TableHead className="yf-cell">High</TableHead><TableHead className="yf-cell">空間</TableHead></>}
                    <TableHead className="eps-cell">N</TableHead><TableHead className="eps-cell">N+1</TableHead><TableHead className="eps-cell">N+2</TableHead><TableHead className="pe-cell"><SortButton label="N" sortKey="peN" currentKey={sortKey} direction={sortDirection} onSort={handleSort} /></TableHead><TableHead className="pe-cell"><SortButton label="N+1" sortKey="peN1" currentKey={sortKey} direction={sortDirection} onSort={handleSort} /></TableHead><TableHead className="pe-cell"><SortButton label="N+2" sortKey="peN2" currentKey={sortKey} direction={sortDirection} onSort={handleSort} /></TableHead><TableHead>品質</TableHead><TableHead>差異</TableHead></TableRow>
                  </TableHeader>
                  <TableBody>{filteredHoldings.map((item, index) => <TableRow key={item.ticker}>
                    <TableCell className="rank-cell">{index + 1}</TableCell><TableCell className="sticky-company"><div className="company-cell"><strong>{item.name}</strong><small>{item.ticker}</small></div></TableCell><TableCell>{item.sector}</TableCell><TableCell><div className="weight-cell"><strong>{formatPct(item.weight, 1)}</strong><span><i style={{ width: `${Math.min(item.weight / 32 * 100, 100)}%` }} /></span></div></TableCell><TableCell><div className="breadth-cell"><strong>{formatNumber(item.breadth, 0)}%</strong><small>{item.selectedFundCount}/{selectedEtfs.size}</small></div></TableCell><TableCell><span className={`action-chip action-${actionTone(item.action)}`}>{item.action}</span></TableCell><TableCell>{formatNumber(item.estimatedCost, 1)}</TableCell><TableCell className="price-cell"><strong>{formatNumber(item.price, 1)}</strong><small>{item.priceDate}</small></TableCell>
                    {providerMode !== "yf" && <><TableCell className="fs-cell">{formatNumber(item.fs.low, 1)}</TableCell><TableCell className="fs-cell">{formatNumber(item.fs.mean, 1)}</TableCell><TableCell className="fs-cell emphatic">{formatNumber(item.fs.median, 1)}</TableCell><TableCell className="fs-cell">{formatNumber(item.fs.high, 1)}</TableCell><TableCell className={`fs-cell ${item.fsUpside !== null && item.fsUpside >= 0 ? "value-up" : "value-down"}`}>{formatPct(item.fsUpside, 1)}</TableCell></>}
                    {providerMode !== "fs" && <><TableCell className="yf-cell">{formatNumber(item.yf.low, 1)}</TableCell><TableCell className="yf-cell">{formatNumber(item.yf.mean, 1)}</TableCell><TableCell className="yf-cell emphatic">{formatNumber(item.yf.median, 1)}</TableCell><TableCell className="yf-cell">{formatNumber(item.yf.high, 1)}</TableCell><TableCell className={`yf-cell ${item.yfUpside !== null && item.yfUpside >= 0 ? "value-up" : "value-down"}`}>{formatPct(item.yfUpside, 1)}</TableCell></>}
                    <TableCell className="eps-cell">{formatNumber(item.eps.n, 2)}</TableCell><TableCell className="eps-cell">{formatNumber(item.eps.n1, 2)}</TableCell><TableCell className="eps-cell">{formatNumber(item.eps.n2, 2)}</TableCell><TableCell className="pe-cell">{item.peN === null ? "—" : `${formatNumber(item.peN, 1)}×`}</TableCell><TableCell className="pe-cell emphatic">{item.peN1 === null ? "—" : `${formatNumber(item.peN1, 1)}×`}</TableCell><TableCell className="pe-cell">{item.peN2 === null ? "—" : `${formatNumber(item.peN2, 1)}×`}</TableCell><TableCell><span className={`quality-chip ${qualityTone(item.quality)}`}>{item.quality}</span>{item.flags.length > 0 && <small className="flag-count">{item.flags.length} flag</small>}</TableCell><TableCell className={item.providerGap !== null && Math.abs(item.providerGap) > 30 ? "value-down" : "muted-value"}>{formatPct(item.providerGap, 1)}</TableCell>
                  </TableRow>)}</TableBody>
                </Table>
                {filteredHoldings.length === 0 && <div className="empty-state"><Search size={24} /><strong>沒有符合條件的持股</strong><span>調整基金選擇、搜尋或品質條件。</span></div>}
              </div>
              <div className="table-legend"><span><i className="legend-dot fs-dot" />FactSet 欄位</span><span><i className="legend-dot yf-dot" />YFinance 欄位</span><span><i className="legend-dot eps-dot" />EPS／P/E</span><span><ShieldCheck size={12} />負 EPS、零 EPS與幣別錯配一律不計算</span></div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="actions" className="tab-panel">
          <div className="section-title-row"><div><p className="section-kicker">MANAGER ACTION LIFECYCLE</p><h2>經理人動作五態機</h2></div><span className="section-note">扣除申贖、價格與公司行動後的主動交易殘差</span></div>
          <div className="lifecycle-grid">{ACTION_STAGES.map((stage) => <article key={stage.no} className={`stage-card stage-${stage.tone}`}><header><small>{stage.no}</small><h3>{stage.title}</h3><span>{stage.subtitle}</span></header><div>{stage.items.map(([title, copy]) => <section key={title}><strong>{title}</strong><p>{copy}</p></section>)}</div></article>)}</div>
          <div className="logic-banner"><Activity size={18} /><div><strong>主動交易量</strong><span>ΔQ Active = ΔQ Actual − ΔQ Flow − ΔQ Corporate Action</span></div><p>五態不是只能單向前進；加碼、平衡、減碼可隨價格與持股決策反覆轉換。</p></div>
        </TabsContent>

        <TabsContent value="request" className="tab-panel">
          <div className="section-title-row"><div><p className="section-kicker">DATA REQUEST & LINEAGE</p><h2>資料請求、來源與驗證</h2></div><span className="section-note">Candidate Sandbox · Append-Only · No Look-Ahead</span></div>
          <div className="source-grid">{DATA_SOURCES.map((source) => <article key={source.name} className={`source-card source-${source.tone}`}><div><Database size={16} /><strong>{source.name}</strong><span className={`source-state state-${source.tone}`}>{source.state}</span></div><p>{source.role}</p></article>)}</div>
          <div className="request-grid">
            <article className="contract-card"><header><ShieldCheck size={17} /><h3>欄位與驗證契約</h3></header><ul><li><span>ETF / 個股身分</span><strong>ticker + ISIN／名稱／Provider ID</strong></li><li><span>價格對齊</span><strong>MAX(price_date) ≤ analysis_date</strong></li><li><span>Consensus 對齊</span><strong>MAX(snapshot_date) ≤ analysis_date</strong></li><li><span>來源規則</span><strong>FactSet 與 YFinance 不平均</strong></li><li><span>Forward P/E</span><strong>Adj Close ÷ Positive Consensus EPS</strong></li><li><span>寫入</span><strong>P0/P1 前僅 Candidate</strong></li></ul></article>
            <article className="json-card"><header><FileJson size={17} /><h3>request.json</h3><Button variant="outline" size="sm" onClick={() => navigator.clipboard?.writeText(REQUEST_JSON)}><ArrowUpFromLine size={13} />複製</Button></header><pre>{REQUEST_JSON}</pre></article>
          </div>
        </TabsContent>
      </Tabs>

      <footer><div><strong>VERITAS INTELLIGENCE ANALYTICS</strong><span>Observa · Intellege · Praevide</span></div><p>VETF Consensus Console · Visual Lock SSOT · Candidate Data Only</p></footer>
    </main>
  );
}
