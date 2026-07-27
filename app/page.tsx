"use client";

// The existing, fully tested React study workbench remains the product surface.
// vinext supplies the Sites-compatible Cloudflare Worker build around it.
// @ts-expect-error The workbench is intentionally kept as JSX for the local Vite app.
import App from "../src/App.jsx";

export default function Home() {
  return <App />;
}
