import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "内科题库 · 306 临床医学综合能力",
  description: "基于 57 份内科讲义与学成选择题整理的 B 型题为主交互式复习题库。",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
