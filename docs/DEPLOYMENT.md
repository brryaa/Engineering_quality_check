# 汽车研发工程质量管理平台 (EQL) 部署与运维指南

## 一、生产环境推荐配置

- **操作系统**：Ubuntu 22.04 / 24.04 LTS 或 Debian 12 / Rocky Linux 9
- **CPU**：2 核以上 (推荐 4 核)
- **内存**：4 GB RAM 以上
- **磁盘**：20 GB SSD 存储空间 (用于持久化试验遥测日志与报告附件)
- **依赖环境**：
  - Docker 24.0+ 与 Docker Compose v2+
  - 或 Python 3.12+ 与 Node.js 20+

---

## 二、Docker Compose 生产环境容器化部署 (推荐)

### 2.1 编排架构
- `frontend` 服务：基于 Node 20 编译打包，生产阶段采用极轻量 `nginx:alpine` 镜像托管静态资源并反向代理 API 流量至后端。
- `backend` 服务：基于 `python:3.12-slim` 镜像运行 Uvicorn ASGI 服务，挂载外部数据卷 `eql_data` 持久化 SQLite WAL 数据库文件。

### 2.2 一键部署步骤
```bash
# 1. 克隆或进入代码仓库目录
cd /home/brrr/agy/Engineering_quality_check

# 2. 构建并启动全部容器服务
docker compose up --build -d

# 3. 检查容器运行状态
docker compose ps

# 4. 查看后端初始化与种子数据日志
docker compose logs -f backend
```

### 2.3 常用运维管理指令
```bash
# 停止容器服务
docker compose down

# 重启后端服务
docker compose restart backend

# 重启前端服务
docker compose restart frontend
```

---

## 三、原生 Linux Systemd 生产部署指南

若在无 Docker 环境下部署，可使用 Linux 原生 Systemd 管理守护进程。

### 3.1 后端服务配置 (`/etc/systemd/system/eql-backend.service`)
```ini
[Unit]
Description=EQL Automotive Engineering Quality Lab Backend
After=network.target

[Service]
Type=simple
User=brrr
WorkingDirectory=/home/brrr/agy/Engineering_quality_check/backend
Environment="PYTHONPATH=/home/brrr/agy/Engineering_quality_check/backend"
Environment="DATABASE_URL=sqlite:////home/brrr/agy/Engineering_quality_check/backend/eql_platform.db"
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8088 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

激活并启动后端：
```bash
sudo systemctl daemon-reload
sudo systemctl enable eql-backend
sudo systemctl start eql-backend
sudo systemctl status eql-backend
```

### 3.2 前端构建与 Nginx 反向代理配置
```bash
cd /home/brrr/agy/Engineering_quality_check/frontend
npm run build
```
产物将输出在 `frontend/dist` 目录。将该目录路径配置至系统主 Nginx 的 `root` 指向即可。

---

## 四、数据库备份与性能维护

SQLite 在 WAL 模式下具有极高的稳定性和读写并发能力，但需要定期的 Checkpoint 与冷备策略：

### 4.1 在线安全热备 (Online Backup)
```bash
# 使用 SQLite 官方在线备份接口（避免读写过程中直接拷贝损坏）
sqlite3 /home/brrr/agy/Engineering_quality_check/backend/eql_platform.db ".backup '/home/brrr/agy/Engineering_quality_check/backend/eql_backup_$(date +%Y%m%d).db'"
```

### 4.2 空间整理与 WAL 检查点 (VACUUM & Checkpoint)
```bash
# 定期清理碎片并回写 WAL 日志
sqlite3 /home/brrr/agy/Engineering_quality_check/backend/eql_platform.db "PRAGMA wal_checkpoint(TRUNCATE);"
sqlite3 /home/brrr/agy/Engineering_quality_check/backend/eql_platform.db "VACUUM;"
```
