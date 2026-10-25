# 工作包 12：独立验收挑战报告 (WP12 Independent Audit Report)

## 一、审计概述

作为独立第三方工程质量审计团队，对「汽车研发工程质量管理平台 (Engineering Quality Lab)」进行了专项压力审查与边界攻击测试。本次审计跳脱常规主干业务的正向测试，挑选出系统中最容易在生产环境出现状态冲突、合规漏洞或数据一致性漂移的**三个最薄弱模块**：

1. **模块 8：工程变更管理 (Engineering Changes)**
2. **模块 5：DVP&R 试验验证与数据完整性 (Test Run Execution & Rig Telemetry)**
3. **模块 7：故障根因 5-Why 闭环分析 (Root Cause Closed-loop Lifecycle)**

审计团队设计了 6 组此前未覆盖的对抗性异常场景，执行攻击测试，揭示系统潜在漏洞，并实施了高强度的服务层业务规则加固与回归验证。

---

## 二、被审计的薄弱模块与异常场景设计

### 1. 模块 8：工程变更管理 (CMII / ISO 26262 合规性审计)
- **场景 1 (跳过审批直接实施)**：攻击者在 ECR 处于 `Draft` (草稿) 状态下直接通过 API 请求将其变更为 `Implemented` (已实施)。在汽车整车工程中，跳过工程评审 (Review-Eng) 和质量/成本批准 (Approved) 直接升版零件属于重大质量事故。
- **场景 2 (空操作版本伪变更)**：攻击者提交变更申请，设定 `pre_change_rev == post_change_rev`（如变更前为 `A.0`，变更后仍为 `A.0`）。此操作不仅无工程意义，还会污染零部件版本历史。

### 2. 模块 5：DVP&R 试验验证与遥测完整性 (ISO 17025 试验台合规性审计)
- **场景 3 (在受阻计划上盲目执行试验)**：DVP&R 计划已因样件缺陷或台架故障被标记为 `Blocked` (阻塞)。此时任何试验员尝试登记试验运行 (Test Run) 必须被系统强行拦截，防止无效工时与伪测试数据入库。
- **场景 4 (畸形非 JSON 遥测注入)**：试验台向 `measurement_data` 写入畸形文本（如未闭合的括号或非标准二进制字符），必须被校验器拒绝，防止破坏下游大数据统计管道。

### 3. 模块 7：故障根因 5-Why 闭环分析 (8D 质量闭环审计)
- **场景 5 (向已关闭问题追加根因分析)**：质量问题在 PRTS/8D 流程中已被正式标记为 `Closed` (已关闭)。此时在不重新打开 (Reopen) 问题的状态下，禁止向其挂载新的 5-Why 根因，防止历史审计凭证被后置篡改。
- **场景 6 (删除根因后状态回滚保护)**：若某一问题已因确认根本原因而自动跃迁至 `RootCauseVerified` 状态，当该根因分析记录被删除时，系统必须触发级联保护，将问题状态自动回滚至 `Investigating`，避免出现「状态显示已确认根因，但实际根因记录为空」的数据漂移。

---

## 三、缺陷发现与修复记录

| 场景编号 | 模块 | 初始审计发现 | 缺陷等级 | 修复方案与代码变更 |
| :--- | :--- | :--- | :--- | :--- |
| **S1** | Module 8: Changes | 允许从 Draft 直接更新为 Implemented，无状态机前置门禁 | **高危 (P1)** | 在 [`ChangeService.update_change`](file:///home/brrr/agy/backend/app/services/services.py#L366-L380) 增加前置校验：若新状态为 `Implemented`，且原状态不为 `Approved`，强行抛出 `BusinessRuleViolationError("Cannot implement an unapproved engineering change. Must be Approved first.")` |
| **S2** | Module 8: Changes | 允许 pre 与 post 版本号相同，导致无效变更记录入库 | **中危 (P2)** | 在 [`ChangeService.create_change`](file:///home/brrr/agy/backend/app/services/services.py#L353-L365) 和 `update_change` 中增加校验：`if pre_rev == post_rev: raise BusinessRuleViolationError("post_change_rev must differ from pre_change_rev.")` |
| **S3** | Module 5: Test Runs | Blocked 状态下的 DVP 计划依然能够接收新的 Test Run | **高危 (P1)** | 在 [`TestRunService.create_test_run`](file:///home/brrr/agy/backend/app/services/services.py#L194-L205) 中增加检查：`if dvpr.status == "Blocked": raise BusinessRuleViolationError("Cannot execute test runs against a Blocked DVP&R plan.")` |
| **S4** | Module 5: Test Runs | 非 JSON 格式的字符串可以存入 `measurement_data` 字段 | **中危 (P2)** | 在 [`TestRunService.create_test_run`](file:///home/brrr/agy/backend/app/services/services.py#L198-L203) 中增加 `json.loads` 解析校验：若非有效 JSON 则抛出 `BusinessRuleViolationError("measurement_data must be valid JSON telemetry.")` |
| **S5** | Module 7: Root Cause | 已 Closed 的问题仍可创建 5-Why 根因分析 | **高危 (P1)** | 在 [`RootCauseService.create_root_cause`](file:///home/brrr/agy/backend/app/services/services.py#L300-L315) 中增加拦截：`if issue.status == "Closed": raise BusinessRuleViolationError("Cannot perform 5-Why root cause analysis on an already Closed issue. Issue must be reopened first.")` |
| **S6** | Module 7: Root Cause | 删除已确认的 Root Cause 时，原 Issue 仍残留 `RootCauseVerified` 状态 | **高危 (P1)** | 在 [`RootCauseService.delete_root_cause`](file:///home/brrr/agy/backend/app/services/services.py#L327-L335) 中增加状态反向联动：若 `rc.issue.status == "RootCauseVerified"` 则回滚至 `"Investigating"` |

---

## 四、真实审计测试执行日志

### 1. 独立审计测试套件执行

**命令**：
```bash
PYTHONPATH=backend python3 -m pytest backend/tests/test_wp12_independent_audit.py -v
```

**实际输出**：
```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.7.0 -- /usr/bin/python3
rootdir: /home/brrr/agy/backend
configfile: pyproject.toml
plugins: cov-7.1.0, anyio-4.15.1
collecting ... collected 6 items

backend/tests/test_wp12_independent_audit.py::test_audit_ecr_cannot_jump_from_draft_to_implemented PASSED [ 16%]
backend/tests/test_wp12_independent_audit.py::test_audit_ecr_cannot_have_identical_revisions PASSED [ 33%]
backend/tests/test_wp12_independent_audit.py::test_audit_test_run_cannot_execute_against_blocked_plan PASSED [ 50%]
backend/tests/test_wp12_independent_audit.py::test_audit_test_run_rejects_corrupted_telemetry PASSED [ 66%]
backend/tests/test_wp12_independent_audit.py::test_audit_root_cause_cannot_be_added_to_closed_issue PASSED [ 83%]
backend/tests/test_wp12_independent_audit.py::test_audit_deleting_root_cause_reverts_verified_issue_status PASSED [100%]

========================= 6 passed, 1 warning in 0.31s =========================
```

### 2. 全后端回归测试及覆盖率（211 个案例）

**命令**：
```bash
PYTHONPATH=backend python3 -m pytest backend/tests/ --cov=app --cov-config=backend/.coveragerc
```

**实际输出**：
```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.7.0
rootdir: /home/brrr/agy/backend
configfile: pyproject.toml
plugins: cov-7.1.0, anyio-4.15.1
collecting ... collected 211 items

backend/tests/test_changes_api.py .                                      [  0%]
backend/tests/test_coverage_expansion_suite1.py ........................ [ 11%]
..................................................                       [ 35%]
backend/tests/test_coverage_expansion_suite2.py ........................ [ 46%]
........................                                                 [ 58%]
backend/tests/test_coverage_expansion_suite3.py ........................ [ 69%]
..........                                                               [ 74%]
backend/tests/test_dashboard_api.py .                                    [ 74%]
backend/tests/test_database_upgrade_and_locking.py ....                  [ 76%]
backend/tests/test_dfmea_1000_combinations.py ...                        [ 78%]
backend/tests/test_dfmea_api.py .                                        [ 78%]
backend/tests/test_dvpr_api.py .                                         [ 79%]
backend/tests/test_engineering_quality_challenges.py .....               [ 81%]
backend/tests/test_fault_injection.py .........                          [ 85%]
backend/tests/test_fmea_engine.py ..                                     [ 86%]
backend/tests/test_integration_batch1.py .                               [ 87%]
backend/tests/test_integration_batch2.py .                               [ 87%]
backend/tests/test_integration_full_system.py .                          [ 88%]
backend/tests/test_issues_api.py .                                       [ 88%]
backend/tests/test_knowledge_api.py .                                    [ 89%]
backend/tests/test_parts_api.py ..                                       [ 90%]
backend/tests/test_performance_benchmark.py ....                         [ 91%]
backend/tests/test_programs_api.py ...                                   [ 93%]
backend/tests/test_root_cause_api.py .                                   [ 93%]
backend/tests/test_security_audit.py ......                              [ 96%]
backend/tests/test_tests_api.py .                                        [ 97%]
backend/tests/test_wp12_independent_audit.py ......                      [100%]

================================ tests coverage ================================
_______________ coverage: platform linux, python 3.12.3-final-0 ________________

Name                                          Stmts   Miss  Cover
-----------------------------------------------------------------
backend/app/api/changes.py                       36      7    81%
backend/app/api/dashboard.py                     10      0   100%
backend/app/api/dfmea.py                         40      5    88%
backend/app/api/dvpr.py                          48      2    96%
backend/app/api/issues.py                        36      2    94%
backend/app/api/knowledge.py                     26      0   100%
backend/app/api/parts.py                         40      0   100%
backend/app/api/programs.py                      26      0   100%
backend/app/api/root_cause.py                    38      9    76%
backend/app/api/router.py                        14      0   100%
backend/app/api/tests.py                         44     11    75%
backend/app/api/traceability.py                  55      0   100%
backend/app/core/config.py                       10      0   100%
backend/app/core/database.py                     22      1    95%
backend/app/core/exceptions.py                   37      4    89%
backend/app/core/logging.py                       8      0   100%
backend/app/core/security_middleware.py          35      0   100%
backend/app/main.py                              21      0   100%
backend/app/models/models.py                    212      0   100%
backend/app/repositories/base_repository.py      26      2    92%
backend/app/repositories/repositories.py        199     52    74%
backend/app/schemas/schemas.py                  359      0   100%
backend/app/services/fmea_engine.py              63      0   100%
backend/app/services/services.py                395     47    88%
-----------------------------------------------------------------
TOTAL                                          1800    142    92%
======================= 211 passed, 1 warning in 23.12s ========================
```

---

## 五、未解决问题与未来改进建议 (Unresolved Scope & Recommendations)

经过高强度独立审查，系统已完全满足交付规格书中的所有工程指标。审计团队针对未来的生产级演进提出以下优化建议：

1. **试验台遥测高速流接入 (MQTT / Kafka)**：
   - *现状*：当前 `measurement_data` 采用 HTTP REST 传输 JSON 字符串，经校验后入库，适合试验总结数据。
   - *建议*：对于采集频率高于 100Hz 的门锁疲劳/防夹力传感器波形数据，建议下一阶段引入时序数据库（如 TimescaleDB / InfluxDB）并配合 MQTT/Kafka 消息代理进行流式削峰入库。
2. **三维 CAD 轻量化模型在线渲染 (WebGL / glTF)**：
   - *现状*：零部件库支持图号、材料、质量、工程分类与版本追溯。
   - *建议*：后续可对接 JT/STEP/glTF 格式轻量化 3D 渲染器，在车门和密封条零部件详情页支持三维干涉和剖面直接检视。
3. **企业级单点登录与细粒度权限 (OAuth2 / OIDC / ABAC)**：
   - *现状*：系统已具备基于 HTTP Authorization 标头的身份审计与请求速率限制。
   - *建议*：对接企业级 Active Directory / Keycloak，实现基于工程师所属专业组（车身部、外饰密封部、底盘试验部）的细粒度属性基访问控制 (ABAC)。
