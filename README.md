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
| **同行审计加固** | [docs/PEER_AUDIT_HARDENING.md](docs/PEER_AUDIT_HARDENING.md) | 针对第一轮同行审计反馈的 6 大安全、权限、算法与测试严密性全面加固报告 |

---

## 七、同行独立代码审计加固说明 (Peer Code Audit Hardening - 2026-10)

针对开源同行与独立安全审计提出的第一轮 6 项高风险/严密性反馈，本项目实施了彻底的工程重构与代码级安全加固：

### 1. 限流逻辑防御加固 (彻底废除 X-Benchmark 客户端豁免)
- **缺陷**：此前在中间件中允许任意客户端发送 `X-Benchmark: 1` 请求头跳过 300 次/分钟限流。
- **加固**：彻底移除 `security_middleware.py` 中的 `X-Benchmark` 客户端请求头豁免逻辑。生产环境严格执行 IP 级滑动窗口限流；压测环境统一通过服务端系统环境变量 `RATE_LIMIT_ENABLED=false` 配置控制。
- **验证**：`test_rate_limiting_defense_and_x_benchmark_cannot_bypass` 验证携带 `X-Benchmark: 1` 仍然被 429 阻断。

### 2. 请求头 Content-Length 健壮性防御
- **缺陷**：非数字或负数 Content-Length 请求头会导致 `int()` 抛出未捕获的 ValueError，引发非预期的 500 服务器内部错误。
- **加固**：使用 `try...except (ValueError, TypeError)` 严密捕获请求头非法值，并增加负数校验；非法请求头直接返回 HTTP 400 Bad Request，超大包体（>5MB）严格返回 HTTP 413。
- **验证**：`test_malformed_content_length_headers` 覆盖非数字与负数畸形请求头。

### 3. 企业级 JWT 身份认证与 RBAC 细粒度权限控制
- **缺陷**：API 路由此前仅依赖数据库会话 `get_db`，未对外部请求实施身份验证与基于角色的访问控制。
- **加固**：
  - 构建 `User` 模型，支持 `admin`、`quality_lead`、`design_engineer`、`viewer` 四级工程权限角色。
  - 实现基于 `bcrypt` 的安全密码哈希（12 轮加盐）与标准 `PyJWT` (HS256) 签名验证。
  - 新增 `/api/v1/auth/login`、`/register`、`/me`、`/users` 统一认证服务。
  - 为全部 10 个业务模块的变更路由（POST, PUT, DELETE）挂载 `require_roles(...)` 依赖守护。
  - 平台内置标准角色测试账号（详见下表）。
- **验证**：`test_auth_api.py` (8 项全覆盖) 与 `test_unauthenticated_mutations_rejected`。

| 角色 (Role) | 预设账号 | 默认密码 | 权限职责 |
| :--- | :--- | :--- | :--- |
| **admin** | `admin` | `Admin@EQL2026!` | 系统最高管理员，管理用户与全模块数据，拥有车型与知识文档唯一删除权 |
| **quality_lead** | `quality_lead` | `Quality@Lead2026!` | 质量经理，创建/维护车型与零部件，唯一拥有 ECR 变更批准/生效与 DFMEA 审批权 |
| **design_engineer** | `design_eng` | `Design@Eng2026!` | 研发设计工程师，创建零件、录入 DVP&R 与试验台架数据，草拟 ECR 变更单 |
| **viewer** | `auditor` | `Auditor@View2026!` | 独立合规审查员，全局只读访问，任何增删改均被 403 Forbidden 严格阻断 |

### 4. 真实 IDOR 越权与垂直提权对抗测试重写
- **缺陷**：此前 IDOR 测试仅验证了不存在的 `program_id` 触发外键约束 400，未真正测试水平与垂直越权。
- **加固**：
  - **垂直提权测试**：`viewer` 角色尝试创建车型、添加零件、发起 ECR，均被 403 阻断；`design_engineer` 尝试删除整车车型或擅自审批 ECR 变更单，均被 403 阻断。
  - **职责分离 (SoD) 测试**：研发工程师创建 Draft 变更单允许通过（201），但调用审批接口尝试自批时返回 403，只有 `quality_lead` 或 `admin` 审批才能返回 200。
  - **水平隔离测试**：验证跨车型项目零部件绑架、跨项目资源非法篡改的强校验与隔离。

### 5. 跨模块业务一致性检查 (100 项) 对抗性负向加固
- **缺陷**：此前 Check 003（平台分类）、Check 008（大写规范）、Check 014（零件重量正数）等测试仅做了 Happy Path 断言，未真正测试非法输入被系统拒绝。
- **加固**：
  - Check 003：主动输入空字符串与非法字符平台，验证被 Pydantic/Service 严格抛出校验异常拒绝。
  - Check 007：主动传入空责任工程师或空质量经理，验证被系统拒绝。
  - Check 008：主动向 API/Service 传入全小写代码 `"p-lower-case-08"`，验证系统自适应无感规范化为大写 `"P-LOWER-CASE-08"`。
  - Check 014：主动传入 `weight_kg = 0.0` 和负数 `weight_kg = -2.5`，验证被系统直接拒绝。
  - Check 017 & 018：主动传入空白材料与供方，验证被强类型规则直接拒绝。

### 6. DFMEA 算法严格类型防线与 AIAG & VDA 2019 表 B 1000 格数学证明
- **缺陷**：Python 中 `issubclass(bool, int) is True`，导致此前 `isinstance(True, int)` 绕过了类型校验。
- **加固**：
  - 重构 `_validate_sod()`，采用 `type(val) is not int or isinstance(val, bool)` 双重严密防线，彻底杜绝布尔值漏网。
  - 同步为 `calculate_rpn` 和 `calculate_action_priority` 挂载此类型检查。
  - **数学级分布核实**：针对 AIAG & VDA 2019 Table B 全部 1,000 种 S/O/D 组合进行全矩阵穷举，经数学推导与全量断言严格确认分布为：
    $$\text{High (H)} = 252,\quad \text{Medium (M)} = 234,\quad \text{Low (L)} = 514,\quad \sum = 1000$$
- **验证**：`test_dfmea_1000_combinations.py` 严格断言 `high_count == 252`, `medium_count == 234`, `low_count == 514`，并全面对 `True` / `False` 注入断言 `TypeError`。
