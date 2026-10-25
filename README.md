# 汽车研发工程质量管理平台 (Engineering Quality Lab - EQL)

面向汽车车身开闭件（车门、车窗、尾门、铰链系统）与全车气密/水密密封系统的高复杂度闭环质量管理 Web 平台。系统严格遵循汽车行业研发质量标准（AIAG & VDA 2019 FMEA、DVP&R 验证规范、PRTS 8D 缺陷追踪、ECR/ECO 工程变更闭环）。

---

## 一、技术栈总览

| 层面 | 技术选型 | 说明 |
| :--- | :--- | :--- |
| **后端架构** | Python 3.12 + FastAPI + Pydantic v2 | 高性能异步/同步 RESTful API，严格输入校验与异常处理 |
| **ORM & 数据层** | SQLAlchemy 2.0 + SQLite (WAL 模式) | 启用预写日志与外键级联，复合索引加固 |
| **前端架构** | React 18 + TypeScript + Vite | 现代化工程暗色质感界面，严格类型契约 |
| **后端测试** | Pytest + TestClient | 覆盖核心算法单元测试、API 契约、跨模块集成与全生命周期测试 |
| **前端测试** | Vitest + React Testing Library | 组件渲染与用户交互单元测试 |
| **端到端测试** | Playwright (Headless Chromium) | 浏览器真实自动化端到端测试 |
| **容器化部署** | Docker Compose + Nginx 反向代理 | 一键多容器编排部署 |

---

## 二、十个核心功能模块

1. **项目及车型管理 (Programs)**：整车开发阶段（Concept, Proto-A, Pre-series-B, PPAP, SOP）、SOP 里程碑、总工与质量经理责任人、目标市场与架构平台。
2. **零部件及子系统管理 (Parts)**：前门、后门、无框玻璃、电动尾门、主密封条、铰链限位器等零部件目录，材料规格、供方、安全法规标识。
3. **DFMEA 风险分析 (DFMEA)**：全面实现 **AIAG & VDA 2019 第1版 AP 行动优先级**（High/Medium/Low）判定引擎，严重度、频度、探测度、RPN 与预防探测控制对策。
4. **DVP&R 验证计划 (DVP&R)**：覆盖整车 DV-A、DV-B、PV 阶段试验（QC/T 627 门开闭耐久、ISO 20653 高压洗车、GMW 14147 低温压缩变形、ECE R21 防夹力）。
5. **试验记录与台架遥测 (Test Runs)**：采集 -40℃ ~ 85℃ 极端温湿度环境、循环圈数、门下垂量(mm)、车窗防夹力(N)、渗漏量(ml/min)遥测原始数据与通过率分析。
6. **工程问题跟踪 (PRTS Issues)**：从台架试验失效自动升单，分级管理 S1-Critical 至 S4-Cosmetic 缺陷，跟踪临时遏制措施 (Containment) 与关闭状态。
7. **故障根因分析 (Root Cause)**：可视化展现 **5-Why 递进逻辑链** 与 **石川因果鱼骨图 (6M: 人机料法环测)**，试验复现与工程归零。
8. **工程变更管理 (ECR / ECO)**：管控设计优化、材料替换、模具修整，核算单车成本变动与工装周期，审批下发后**自动联动零件版本 (Revision) 升级**。
9. **研发质量统计 Dashboard**：统计高风险 AP 帕累托分布、DVP&R 燃尽进度、问题存量与平均修复时长、子系统质量健康度排名 (Health Index)。
10. **工程知识检索 (Knowledge Base)**：全文字符串与标签检索历史经验教训、失效案例、国家/行业标准规范与设计准则。

---

## 三、模拟工程测试数据规模

平台内置了高度拟真的汽车开闭件与密封工程种子数据，全部在本地生成：
- **12 个** 虚构整车研发车型项目（覆盖 800V 高压纯电 SUV、轿跑、MPV、轻卡平台）
- **233 个** 车门/尾门/车窗/密封条在控零部件
- **360 条** DFMEA 潜在失效模式分析记录
- **560 项** DVP&R 设计验证与生产确认试验计划
- **1,116 条** 试验台架执行与环境遥测实测数据
- **530 件** 工程质量问题跟踪单 (PRTS)
- **424 条** 5-Why 与鱼骨图根因分析案例
- **230 项** 工程变更订单 (ECR/ECO)
- **6 篇** 车身开闭件与高压洗车漏水经验教训标准文档

---

## 四、快速启动说明

### 4.1 本地原生运行

#### 1. 后端启动
```bash
cd backend
# 1. 运行种子数据生成脚本 (如数据库不存在将自动创建并注入 1000+ 真实工况数据)
PYTHONPATH=. python3 -m app.seeds.seed_data

# 2. 启动 FastAPI 后端服务 (监听 8088 端口)
PYTHONPATH=. python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8088 --reload
```
API 文档地址：`http://localhost:8088/docs`

#### 2. 前端启动
```bash
cd frontend
# 安装前端依赖并启动 Vite 开发服务器 (开发模式自动反向代理至 8088 端口)
npm install
npm run dev
```
前端访问地址：`http://localhost:5173`

---

### 4.2 Docker Compose 一键容器化运行

```bash
# 在项目根目录下执行
docker compose up --build -d
```
- 前端 Web 访问地址：`http://localhost:3000`
- 后端 API 访问地址：`http://localhost:8088`

---

## 五、自动化测试执行指南

### 5.1 统一持续集成流水线 (CI Pipeline - 7 项质检全绿)
```bash
# 一键运行全部 7 道质检门禁（Ruff, Mypy, Pytest Coverage, TypeScript Strict, Vite Build, Vitest, Playwright 40 Flows）
bash scripts/ci_check.sh
```

### 5.2 后端高覆盖率测试套件 (Pytest - 211 项全量通过，92% 语句覆盖率)
```bash
# 包含 AIAG-VDA 1000 组合核验、乐观锁并发、9 大故障注入、安全注入审计、开闭件质量挑战与独立审计对抗测试
PYTHONPATH=backend python3 -m pytest backend/tests/ --cov=app --cov-config=backend/.coveragerc -v
```

### 5.3 前端组件与交互测试 (Vitest - 13 个套件，130 项全部通过)
```bash
cd frontend
npx vitest run
```

### 5.4 真实浏览器端到端自动化测试 (Playwright - 40 条完整业务流全量通过)
```bash
cd frontend
npx playwright test e2e/comprehensive_acceptance.spec.ts
```

---

## 六、工程文档清单 (Engineering Documentation)

| 阶段 | 文档名称 | 核心内容 |
| :--- | :--- | :--- |
| **基础交付** | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 四层架构分层、分层设计模式与完整数据库 ER 关系模型 |
| **基础交付** | [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | 本地多环境部署与 Docker Compose 容器化编排指南 |
| **基础交付** | [docs/PERFORMANCE_REPORT.md](docs/PERFORMANCE_REPORT.md) | 关键 API 响应延时与压测指标 |
| **基础交付** | [docs/SECURITY_REVIEW.md](docs/SECURITY_REVIEW.md) | 双轮代码审查与加固记录 |
| **基础交付** | [docs/TEST_AND_DEFECT_REPORT.md](docs/TEST_AND_DEFECT_REPORT.md) | 基础自动化测试与缺陷追踪记录 |
| **WP1** | [docs/WP1_AUTHENTICITY_EVIDENCE.md](docs/WP1_AUTHENTICITY_EVIDENCE.md) | 真实性核验证据矩阵与全模块可用性审查 |
| **WP3** | [docs/WP3_FAULT_INJECTION_REPORT.md](docs/WP3_FAULT_INJECTION_REPORT.md) | 9 大极端故障注入场景测试及容错加固报告 |
| **WP4** | [docs/WP4_DFMEA_VERIFICATION.md](docs/WP4_DFMEA_VERIFICATION.md) | AIAG & VDA 2019 第 1 版 AP 算法标准与 1000 种组合全覆盖验证 |
| **WP5** | [docs/WP5_DATABASE_UPGRADE.md](docs/WP5_DATABASE_UPGRADE.md) | SQLite + PostgreSQL 双方言适配、Alembic 迁移与并发乐观锁 |
| **WP6** | [docs/WP6_PERFORMANCE_SCALING.md](docs/WP6_PERFORMANCE_SCALING.md) | 1万 / 10万 / 100万级数据缩放吞吐与 P50/P95/P99 真实延迟压测 |
| **WP7** | [docs/WP7_SECURITY_AUDIT.md](docs/WP7_SECURITY_AUDIT.md) | SQL 注入、XSS、IDOR 越权、速率限制、OWASP 安全审计 |
| **WP8** | [docs/WP8_ARCHITECTURE_REFACTORING.md](docs/WP8_ARCHITECTURE_REFACTORING.md) | Controller-Service-Repository-Model 四层解耦与可测试性重构 |
| **WP9** | [docs/WP9_REAL_BROWSER_ACCEPTANCE.md](docs/WP9_REAL_BROWSER_ACCEPTANCE.md) | Playwright 真实浏览器 40 条关键业务流与 11 张页面全景快照验收 |
| **WP10** | [docs/WP10_ENGINEERING_QUALITY_CHALLENGES.md](docs/WP10_ENGINEERING_QUALITY_CHALLENGES.md) | 五类车门/密封系统工程挑战全链路闭环追溯验证 |
| **WP11** | [docs/WP11_CI_AND_MAINTAINABILITY.md](docs/WP11_CI_AND_MAINTAINABILITY.md) | 统一 CI 流水线、严格类型静态检查与构建工程化 |
| **WP12** | [docs/WP12_INDEPENDENT_AUDIT_REPORT.md](docs/WP12_INDEPENDENT_AUDIT_REPORT.md) | 独立第三方工程质量审查挑战、缺陷挖掘修复与终验报告 |
