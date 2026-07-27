# 内科题库

## 手机访问

优先使用已部署的个人网页（手机和电脑都可打开）：

<https://neike-306-tiku.phamkhanhs87501.chatgpt.site>

这是私有站点，需要在浏览器中登录与当前 Codex 相同的 ChatGPT/OpenAI 账号；登录后可在任意网络访问。

电脑需要保持运行题库服务。若电脑 IP 变化，用下面命令查看新地址：

```bash
ipconfig getifaddr en0
```

## 启动

```bash
pnpm run dev --host 0.0.0.0 --port 4173
```

如需在本地调试，仍可使用上面的局域网方式；本地服务必须保持电脑运行。
