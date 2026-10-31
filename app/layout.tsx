import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "西综题库 · 内科、病理、外科、生理与生化",
  description: "基于内科、病理、外科、生理与生化讲义整理的交互式复习题库，含讲义校对与对应页图。",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <head>
        {/* The router also calls this API before the study workbench mounts. */}
        <script dangerouslySetInnerHTML={{ __html: 'if(!Object.hasOwn){Object.defineProperty(Object,"hasOwn",{value:function(object,key){return Object.prototype.hasOwnProperty.call(object,key)},writable:true,configurable:true})}' }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
