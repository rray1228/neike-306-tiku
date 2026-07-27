# 内科题库

## 手机访问

电脑和手机连接同一个 Wi‑Fi 后，在手机浏览器打开：

`http://10.158.152.207:4173/`

电脑需要保持运行题库服务。若电脑 IP 变化，用下面命令查看新地址：

```bash
ipconfig getifaddr en0
```

## 启动

```bash
pnpm run dev --host 0.0.0.0 --port 4173
```

如果希望离开电脑、使用任何网络访问，需要把 `dist/` 部署到 GitHub Pages、Netlify 或其他静态网站托管服务。
