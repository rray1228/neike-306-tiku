import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "西综题库 · 内科与病理",
  description: "基于内科、病理讲义与学成选择题整理的 B 型题为主交互式复习题库。",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
