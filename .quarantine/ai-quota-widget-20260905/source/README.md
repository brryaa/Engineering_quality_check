# AI Quota Hub - 桌面浮窗小程序 (Codex / AGY / Grok Build)

这是一个专为 Linux 桌面开发的现代半透明暗黑风 **AI 算力余量监控浮窗小程序**。

## 🌟 功能特性

- **三合一算力余量展示**:
  - 🤖 **Codex (ChatGPT)**: 支持展示订阅计划（Plus / Pro）、可用额度、重置窗口、Token 有效期。
  - 🚀 **AGY (Antigravity)**: 展示今日请求余量（1,500 次/天）、活跃会话数、监控模型（Gemini 3.8 Flash）。
  - ⚡ **Grok Build (xAI)**: 展示 2 小时滑动窗口余量（140 / 140 次）、订阅计划（X Premium+）、重置倒计时。
- **灵活双模授权**:
  - 🌐 **浏览器授权**: 任意服务均可一键点击“浏览器授权”，打开本地授权服务器与官方网页，极速获取并同步凭证。
  - 💻 **本机已安装 App 现成 API (Codex)**: 一键无缝读取本机已安装并登录的 ChatGPT/Codex App 现成 API 与凭据。
  - 💻 **本机环境自动同步 (AGY / Grok)**: 自动检测本机正在运行的 AGY CLI 与 Grok 配置。
- **现代化桌面交互**:
  - **始终置顶 (Always on Top)**: 随时浮在代码编辑器上方，不遮挡主工作区。
  - **任意拖拽**: 鼠标按住浮窗任意空白区域或顶部栏即可拖动。
  - **双模式切换**: 支持【完整卡片视图】与【极简胶囊视图（折叠）】一键切换。
  - **定时自动刷新 & 手动刷新**: 默认 5 分钟自动刷新，可自定义频率。

## 🚀 快速使用

### 1. 启动桌面浮窗
```bash
ai-quota-widget
# 或者
python3 /home/brrr/agy/ai-quota-widget/main.py
```

### 2. 命令行查询 (无 GUI 模式)
```bash
ai-quota-widget --status
```

### 3. 打开指定服务的浏览器授权页
```bash
ai-quota-widget --auth codex   # Codex 网页授权
ai-quota-widget --auth grok    # Grok Build 网页授权
ai-quota-widget --auth agy     # AGY 网页授权
```

## ⚙️ 配置文件

配置文件位于：`~/.config/ai-quota-widget/config.json`（权限 0600，保证凭据安全）。
可在浮窗顶部点击 `⚙️` 图标打开可视化配置界面调整。
