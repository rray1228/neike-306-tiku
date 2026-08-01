import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "西综题库 · 内科、病理、外科与生理",
  description: "基于内科、病理、外科、生理讲义与学成选择题整理的交互式复习题库，含生理学 2027 讲义校正版。",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
