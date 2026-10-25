# 自动化测试与缺陷修复报告 (Testing & Defect Fix Report)

## 一、测试套件总览与执行结果

本平台坚持“测试驱动与真实运行验证”原则，所有测试均在本地 Linux 环境中真实运行并通过，杜绝虚标。

| 测试类型 | 测试框架 / 工具 | 测试用例数 | 实际运行结果 | 平均耗时 |
| :--- | :--- | :--- | :--- | :--- |
| **后端单元与算法测试** | Pytest + Pydantic | 6 用例 | **100% 全部通过 (PASSED)** | 0.28s |
| **后端单模块 API 测试** | Pytest + FastAPI TestClient | 10 用例 | **100% 全部通过 (PASSED)** | 0.52s |
| **跨模块集成与全生命周期测试** | Pytest + SQLAlchemy | 3 用例 | **100% 全部通过 (PASSED)** | 0.65s |
| **高并发性能基准测试** | Pytest + Benchmark | 4 用例 | **100% 全部通过 (PASSED)** | 1.19s |
| **前端组件单元测试** | Vitest + Testing Library | 6 用例 | **100% 全部通过 (PASSED)** | 5.09s |
| **端到端浏览器系统测试 (E2E)** | Playwright (Headless Chromium) | 1 套件 (完整闭环) | **100% 全部通过 (PASSED)** | 5.60s |
| **总计** | — | **30 项自动化用例** | **全部通过 (0 失败)** | — |

---

## 二、测试中发现的缺陷 (Defects) 与分析修复过程

在自主开发和持续测试过程中，测试套件共暴露并解决了以下 6 项真实工程缺陷：

### 缺陷 1：SQLite 内存数据库多连接隔离导致数据表丢失 (No such table)
- **现象**：在 Batch 1 运行 pytest 时，API 请求报 `sqlite3.OperationalError: no such table: programs`。
- **根因**：SQLite `sqlite:///:memory:` 默认在每次建立连接（包括 TestClient 多线程或新 session）时创建一个全新的独立内存库，导致 `create_all` 初始化的表结构对后续请求不可见。
- **修复**：在 `backend/tests/conftest.py` 中引入 `from sqlalchemy.pool import StaticPool`，强制所有 Session 共享同一内存连接池。

### 缺陷 2：FastAPI 与 Pydantic V2 弃用警告
- **现象**：测试控制台输出大量 deprecation warnings：`regex` 参数弃用、`class Config: from_attributes = True` 弃用、`datetime.utcnow()` 弃用。
- **修复**：
  1. 将 Query 中的 `regex=` 替换为 `pattern=`；
  2. 将模型配置升级为 Pydantic V2 规范：`model_config = ConfigDict(from_attributes=True)`；
  3. 将日期生成升级为时区感知规范：`datetime.now(timezone.utc)`。

### 缺陷 3：多表关联查询存在 N+1 延迟导致性能基准超标
- **现象**：在性能基准测试中，`test_benchmark_issues_multi_filter_search` 耗时 54.71ms，超过了 < 50ms 的性能红线。
- **根因**：`EngineeringIssue` 遍历输出时，每次循环均懒加载访问 `program`、`part`、`root_cause`，产生 20×3 = 60 次额外 SQL 查询。
- **修复**：在 `backend/app/api/issues.py` 中引入 `joinedload` 预加载：
  ```python
  query = query.options(
      joinedload(EngineeringIssue.program),
      joinedload(EngineeringIssue.part),
      joinedload(EngineeringIssue.root_cause),
  )
  ```
  优化后平均延迟由 54.71ms 直降至 **16.66ms**，性能提升约 70%。

### 缺陷 4：Vitest 默认扫描模式加载了 Playwright E2E 测试文件
- **现象**：运行 `npm test` 时报 `Playwright Test did not expect test.describe() to be called here`。
- **根因**：Vitest 默认测试匹配规则包含了根目录下 `e2e/` 中的所有 `*.spec.ts` 文件。
- **修复**：在 `frontend/vite.config.ts` 的 `test` 配置中显式约束 `include: ['src/**/*.{test,spec}.{ts,tsx}']`，将 E2E 目录与单元测试完全隔离。

### 缺陷 5：Playwright Strict Mode 元素多重定位冲突
- **现象**：E2E 测试在定位 `text=汽车研发工程质量管理平台` 和 `text=P-EP32` 时触发 strict mode violation 异常。
- **根因**：DOM 中存在多处相同文本（如 Navbar 标题与 Footer 备案信息；Navbar 下拉框 `<option>` 与页面主要内容卡片 `<h3>`）。
- **修复**：在 `e2e/eql_flow.spec.ts` 中精确定位容器，例如 `page.locator('header').getByText(...)` 及 `page.locator('main').getByText(...)`。

### 缺陷 6：本地环境 8000 端口被旧系统占用导致 Vite 代理 404
- **现象**：Playwright E2E 启动时前端提示 `数据加载失败: HTTP 404: Not Found`。
- **根因**：宿主机 8000 端口已被历史服务占用，导致 Playwright 复用了已有端口而未能将流量代理至新建的后端服务。
- **修复**：将 EQL 后端端口统一切换为独立端口 `8088`，更新 `vite.config.ts` 代理与 `playwright.config.ts` 服务编排配置，系统顺畅启动并执行完毕。
