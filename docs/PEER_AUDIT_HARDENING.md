# EQL 平台第一轮独立同行代码审计加固技术报告

## 一、概述

本报告详细记录了针对开源社区同行及独立安全审查员对 EQL（Engineering Quality Lab）提交版本（Commit `6c70ab5`）进行第一轮代码审计后所提出的 6 项高风险安全、权限、输入处理与测试严密性问题的完整整改与工程落地证据。

---

## 二、审计缺陷整改与证据矩阵

| 序号 | 审计发现 | 风险等级 | 根本原因 | 整改方案与核心代码改动 | 验证测试与状态 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **F-01** | `X-Benchmark: 1` 请求头导致任意客户端绕过 300次/分 限流 | **高危 (High)** | 中间件代码轻信客户端自报的 `X-Benchmark` 请求头，在生产代码中放行 | 彻底移除该请求头判断逻辑，生产逻辑仅对内部测试客户端在未设限标志时豁免。压测通过服务端配置 `RATE_LIMIT_ENABLED=false` 统一控制 | `test_security_audit.py::test_rate_limiting_defense_and_x_benchmark_cannot_bypass` (**已修复**) |
| **F-02** | `Content-Length` 请求头格式错误引发未捕获 `ValueError` (500错误) | **中危 (Medium)** | 直接使用 `int(content_length)`，遇到非数字或负数字符串引发异常 | 使用 `try...except (ValueError, TypeError)` 捕获并检查负值，格式非法直接返回 400 Bad Request，超 5MB 返回 413 | `test_security_audit.py::test_malformed_content_length_headers` (**已修复**) |
| **F-03** | 缺乏真正的用户身份认证与基于角色的权限控制 (RBAC) | **严重 (Critical)** | 各模块 API 接口仅挂载 `Depends(get_db)`，未校验 JWT Bearer Token 及用户角色 | 建立 `User` 模型，集成 PyJWT (HS256) 与 bcrypt 密码哈希，通过 `require_roles(...)` 依赖控制全部 10 模块增删改接口 | `test_auth_api.py` (8 项测试) & 模块级 RBAC 拦截 (**已修复**) |
| **F-04** | 原 IDOR 测试实际仅验证外键不存在引发的 400 校验 | **中危 (Medium)** | 历史测试用例 `test_idor_cross_program_isolation` 仅测了 `program_id: 88888` 不存在 | 重写安全测试套件：覆盖 Viewer 垂直越权 (403)、工程师越权删车 (403)、工程师自批 ECR 违规 (403)，以及水平数据隔离 | `test_security_audit.py` (11 项安全测试) (**已修复**) |
| **F-05** | 100 项跨模块业务检查存在同义反复与仅测 Happy Path | **低危 (Low)** | Check 003, 008, 014 等未主动传入非法/小写/负数参数验证校验器生效 | 在 Check 003（空平台拒绝）、Check 007（空负责人拒绝）、Check 008（小写自动大写规范化）、Check 014（重量<=0拒绝）、Check 017/018（空材料/供方拒绝）中实施对抗断言 | `test_100_business_consistency_checks.py` 100 项全部通过 (**已修复**) |
| **F-06** | Python `isinstance(True, int)` 导致布尔值绕过 DFMEA 参数校验 | **中危 (Medium)** | Python 中 `bool` 为 `int` 子类，`isinstance(True, int)` 返回 True | 使用 `type(val) is not int or isinstance(val, bool)` 双重校验，并推导数学验证 AIAG & VDA 2019 Table B 全部 1000 种组合 | `test_dfmea_1000_combinations.py` 证明：H=252, M=234, L=514，布尔值严格抛 TypeError (**已修复**) |

---

## 三、关键架构与代码重构说明

### 3.1 认证与 RBAC 架构设计

#### 1. 角色矩阵设计 (Automotive Engineering RBAC Matrix)

```mermaid
flowchart TD
    Admin["admin (系统管理员)"] -->|完全控制| AllModules["全部 10 个业务模块 + 用户管理"]
    QualityLead["quality_lead (质量经理)"] -->|审批权| DFMEA["DFMEA 批准"]
    QualityLead -->|最终审批 & 生效| ECR["工程变更 (ECR) 批准/生效"]
    QualityLead -->|创建 & 修改| ProgramsParts["车型项目 & 零部件"]
    DesignEng["design_engineer (设计工程师)"] -->|草拟 & 提交| ECRDraft["发起 ECR 变更申请 (Draft)"]
    DesignEng -->|编制 & 记录| TestDVPR["编制 DVP&R / 录入试验数据"]
    DesignEng -.->|禁止自批 (403)| ECR
    Viewer["viewer (独立审计员 / 访客)"] -->|只读查询 (200)| ReadOnly["全系统数据检索与看板"]
    Viewer -.->|任何修改/删除 (403)| Blocked["严格阻断"]
```

#### 2. 用户账号与鉴权凭据
平台预置 4 类角色的标准工程账号（密码均已通过 `bcrypt` 12 轮单向哈希加盐持久化）：
- **admin**: `admin` / `Admin@EQL2026!` (角色: `admin`)
- **quality_lead**: `quality_lead` / `Quality@Lead2026!` (角色: `quality_lead`)
- **design_engineer**: `design_eng` / `Design@Eng2026!` (角色: `design_engineer`)
- **viewer**: `auditor` / `Auditor@View2026!` (角色: `viewer`)

---

### 3.2 DFMEA 1000 组合数学证明

根据 AIAG & VDA 1st Edition (2019) DFMEA Handbook 标准 Table B：

1. **Severity 9-10 (Very High)**：
   - $O \in [8, 10]$ (3 档): $D \in [1, 10]$ 全部为 High $\rightarrow 3 \times 10 = 30$
   - $O \in [6, 7]$ (2 档): $D \in [1, 10]$ 全部为 High $\rightarrow 2 \times 10 = 20$
   - $O \in [4, 5]$ (2 档): $D \in [7, 10]$ 为 High (8), $D \in [2, 6]$ 为 Med (10), $D=1$ 为 Low (2)
   - $O \in [2, 3]$ (2 档): $D \in [5, 10]$ 为 Med (12), $D \in [1, 4]$ 为 Low (8)
   - $O = 1$ (1 档): $D \in [1, 10]$ 全部为 Low $\rightarrow 10$
   - **单档小计 (S=9 或 S=10)**: High = 58, Medium = 22, Low = 20 (合计 100)
   - **S=9, 10 汇总 (2 档)**: $\text{High} = 116,\quad \text{Medium} = 44,\quad \text{Low} = 40$

2. **Severity 7-8 (High)**：
   - 经相同格网展开，单档小计：High = 50, Medium = 26, Low = 24
   - **S=7, 8 汇总 (2 档)**: $\text{High} = 100,\quad \text{Medium} = 52,\quad \text{Low} = 48$

3. **Severity 4-6 (Moderate)**：
   - 经格网展开，单档小计：High = 12, Medium = 38, Low = 50
   - **S=4, 5, 6 汇总 (3 档)**: $\text{High} = 36,\quad \text{Medium} = 114,\quad \text{Low} = 150$

4. **Severity 2-3 (Low)**：
   - 经格网展开，单档小计：High = 0, Medium = 12, Low = 88
   - **S=2, 3 汇总 (2 档)**: $\text{High} = 0,\quad \text{Medium} = 24,\quad \text{Low} = 176$

5. **Severity 1 (Very Low)**：
   - 无论 O、D 取值，AP 恒为 Low：$\text{Low} = 100$

$$\begin{aligned}
\text{Total High} &= 116 + 100 + 36 + 0 + 0 = \mathbf{252} \\
\text{Total Medium} &= 44 + 52 + 114 + 24 + 0 = \mathbf{234} \\
\text{Total Low} &= 40 + 48 + 150 + 176 + 100 = \mathbf{514} \\
\sum &= 252 + 234 + 514 = \mathbf{1000}
\end{aligned}$$

`test_dfmea_1000_combinations.py` 严格校验此理论值，完全吻合。

---

## 四、验证命令与复现说明

```bash
# 1. 运行同行审计加固专用安全与权限测试
PYTHONPATH=backend python3 -m pytest backend/tests/test_security_audit.py -v

# 2. 运行认证及 RBAC 单元测试
PYTHONPATH=backend python3 -m pytest backend/tests/test_auth_api.py -v

# 3. 运行 1000 格 DFMEA 数学检验与布尔类型拒绝测试
PYTHONPATH=backend python3 -m pytest backend/tests/test_dfmea_1000_combinations.py -v

# 4. 运行 100 项负向加固业务一致性检查
PYTHONPATH=backend python3 -m pytest backend/tests/test_100_business_consistency_checks.py -v

# 5. 运行前端 Vitest 全量套件 (130 项测试)
cd frontend && npm test -- --run
```
