import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VIA Taiwan Active ETF Consensus Console",
  description: "主動式台股 ETF 持股聚合、FactSet／YFinance 目標價、Consensus EPS 與 Forward P/E 工作台。",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-Hant">
      <body>{children}</body>
    </html>
  );
}
