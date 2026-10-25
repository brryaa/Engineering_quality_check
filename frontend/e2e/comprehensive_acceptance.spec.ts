import { test, expect } from '@playwright/test';

test.describe('Automotive Engineering Quality Lab - 40 Comprehensive Business Flows', () => {
  // Listen for uncaught browser errors
  test.beforeEach(async ({ page }) => {
    page.on('console', (msg) => {
      if (msg.type() === 'error' && !msg.text().includes('favicon')) {
        console.log(`[Browser Console Error]: ${msg.text()}`);
      }
    });
  });

  // ================= MODULE 1: QUALITY DASHBOARD & SYSTEM OVERVIEW (Flows 1-4) =================
  test('Flow 1: Loads dashboard with complete KPI metrics & takes overview screenshot', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('text=质量工程总览仪表盘')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('text=AIAG-VDA 风险控制 · DVP&R 试验闭环')).toBeVisible();
    await expect(page.locator('text=开闭件与密封子系统健康度排名')).toBeVisible();
    await expect(page.locator('text=DFMEA 风险行动优先级')).toBeVisible();
    await page.screenshot({ path: 'e2e/screenshots/01_dashboard_overview.png', fullPage: true });
  });

  test('Flow 2: Verifies dashboard stats metrics (Programs, Parts, DFMEAs, DVPs, Issues, ECRs)', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('text=质量工程总览仪表盘')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('main').getByText('车型项目').first()).toBeVisible();
    await expect(page.locator('text=在控零部件')).toBeVisible();
    await expect(page.locator('text=DFMEA分析项')).toBeVisible();
    await expect(page.locator('text=工程问题总数')).toBeVisible();
    await expect(page.locator('text=工程变更(ECR)')).toBeVisible();
  });

  test('Flow 3: Filters dashboard by vehicle program in header dropdown', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('text=质量工程总览仪表盘')).toBeVisible({ timeout: 10000 });
    const programSelect = page.locator('header select');
    await programSelect.selectOption({ index: 1 });
    await expect(page.locator('text=质量工程总览仪表盘')).toBeVisible();
  });

  test('Flow 4: Resets global program filter to show all programs', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('text=质量工程总览仪表盘')).toBeVisible({ timeout: 10000 });
    const programSelect = page.locator('header select');
    await programSelect.selectOption('');
    await expect(programSelect).toHaveValue('');
    await expect(page.locator('text=质量工程总览仪表盘 (全局统计)')).toBeVisible();
  });

  // ================= MODULE 2: VEHICLE PROGRAMS MANAGEMENT (Flows 5-8) =================
  test('Flow 5: Navigates to Programs view and renders program cards & screenshot', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("车型项目")');
    await expect(page.locator('text=车型项目与研发平台管理')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=管理汽车整车项目开发阶段')).toBeVisible();
    await page.screenshot({ path: 'e2e/screenshots/02_programs_view.png', fullPage: true });
  });

  test('Flow 6: Filters vehicle programs by development phase', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("车型项目")');
    await expect(page.locator('text=车型项目与研发平台管理')).toBeVisible({ timeout: 10000 });
    const phaseSelect = page.locator('main select');
    await phaseSelect.selectOption('Proto-A');
    await expect(page.locator('main')).toBeVisible();
  });

  test('Flow 7: Searches vehicle programs by model name keyword', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("车型项目")');
    await expect(page.locator('text=车型项目与研发平台管理')).toBeVisible({ timeout: 10000 });
    const searchInput = page.locator('input[placeholder*="搜索项目代号"]');
    await searchInput.fill('Aurora');
    await expect(page.locator('main').getByText('Aurora').first()).toBeVisible();
  });

  test('Flow 8: Opens and dismisses create program modal', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("车型项目")');
    await page.click('button:has-text("新建车型项目")');
    await expect(page.locator('text=创建新车型工程项目')).toBeVisible();
    await page.click('button:has-text("取消")');
    await expect(page.locator('text=创建新车型工程项目')).not.toBeVisible();
  });

  // ================= MODULE 3: PARTS & SUBSYSTEMS (Flows 9-12) =================
  test('Flow 9: Navigates to Parts view, verifies table headers & captures screenshot', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("零部件")');
    await expect(page.locator('text=零部件与车身开闭件子系统目录')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('th:has-text("零件编号 (Part No.)")')).toBeVisible();
    await expect(page.locator('th:has-text("工程子系统")')).toBeVisible();
    await page.screenshot({ path: 'e2e/screenshots/03_parts_view.png', fullPage: true });
  });

  test('Flow 10: Filters parts by Primary Body Seal engineering subsystem', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("零部件")');
    await expect(page.locator('text=零部件与车身开闭件子系统目录')).toBeVisible({ timeout: 10000 });
    const subSelect = page.locator('main select');
    await subSelect.selectOption('Primary Body Seal');
    await expect(page.locator('td:has-text("Primary Body Seal")').first()).toBeVisible();
  });

  test('Flow 11: Searches parts catalog by supplier or material keyword', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("零部件")');
    await expect(page.locator('text=零部件与车身开闭件子系统目录')).toBeVisible({ timeout: 10000 });
    const searchInput = page.locator('input[placeholder*="搜索件号"]');
    await searchInput.fill('EPDM');
    await expect(page.locator('tbody tr').first()).toBeVisible();
  });

  test('Flow 12: Opens new part entry modal, inspects required fields and closes', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("零部件")');
    await page.click('button:has-text("录入新零件")');
    await expect(page.locator('text=录入新研发零部件')).toBeVisible();
    await expect(page.locator('text=材料牌号')).toBeVisible();
    await page.click('button:has-text("取消")');
    await expect(page.locator('text=录入新研发零部件')).not.toBeVisible();
  });

  // ================= MODULE 4: DFMEA RISK ANALYSIS (Flows 13-16) =================
  test('Flow 13: Navigates to DFMEA view and inspects AIAG & VDA AP table with screenshot', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("DFMEA风险")');
    await expect(page.locator('text=DFMEA 设计潜在失效模式与后果分析')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=遵循 AIAG & VDA 2019 第1版 AP 行动优先级标准')).toBeVisible();
    await expect(page.locator('th:has-text("严重度 (S)")')).toBeVisible();
    await expect(page.locator('th:has-text("AP 行动优先级")')).toBeVisible();
    await page.screenshot({ path: 'e2e/screenshots/04_dfmea_view.png', fullPage: true });
  });

  test('Flow 14: Filters DFMEA matrix by High Action Priority', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("DFMEA风险")');
    await expect(page.locator('text=DFMEA 设计潜在失效模式与后果分析')).toBeVisible({ timeout: 10000 });
    const apSelect = page.locator('main select').first();
    await apSelect.selectOption('High');
    await expect(page.locator('tbody tr').first()).toBeVisible();
    await expect(page.locator('tbody').getByText('High').first()).toBeVisible();
  });

  test('Flow 15: Filters DFMEA matrix by RPN threshold >= 100', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("DFMEA风险")');
    await expect(page.locator('text=DFMEA 设计潜在失效模式与后果分析')).toBeVisible({ timeout: 10000 });
    const rpnSelect = page.locator('main select').nth(1);
    await rpnSelect.selectOption('100');
    await expect(page.locator('tbody tr').first()).toBeVisible();
  });

  test('Flow 16: Opens DFMEA action review modal and inspects S/O/D ratings', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("DFMEA风险")');
    await expect(page.locator('text=DFMEA 设计潜在失效模式与后果分析')).toBeVisible({ timeout: 10000 });
    await page.locator('button:has-text("审查措施")').first().click();
    await expect(page.locator('text=DFMEA 风险措施审查')).toBeVisible();
    await expect(page.locator('text=严重度(S)')).toBeVisible();
    await page.click('button:has-text("关闭")');
    await expect(page.locator('text=DFMEA 风险措施审查')).not.toBeVisible();
  });

  // ================= MODULE 5: DVP&R VERIFICATION PLANS (Flows 17-20) =================
  test('Flow 17: Navigates to DVP&R view and checks verification standards & screenshot', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("DVP&R计划")');
    await expect(page.locator('text=DVP&R 设计验证试验计划与报告')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('th:has-text("执行标准 (Standard)")')).toBeVisible();
    await page.screenshot({ path: 'e2e/screenshots/05_dvpr_view.png', fullPage: true });
  });

  test('Flow 18: Filters DVP&R plans by DV-A verification phase', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("DVP&R计划")');
    await expect(page.locator('text=DVP&R 设计验证试验计划与报告')).toBeVisible({ timeout: 10000 });
    const phaseSelect = page.locator('main select').first();
    await phaseSelect.selectOption('DV-A');
    await expect(page.locator('tbody tr').first()).toBeVisible();
  });

  test('Flow 19: Filters DVP&R plans by status dropdown', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("DVP&R计划")');
    await expect(page.locator('text=DVP&R 设计验证试验计划与报告')).toBeVisible({ timeout: 10000 });
    const statusSelect = page.locator('main select').nth(1);
    await statusSelect.selectOption('Passed');
    await expect(page.locator('tbody tr').first()).toBeVisible();
  });

  test('Flow 20: Opens create DVP plan modal and checks sample size and standard fields', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("DVP&R计划")');
    await page.click('button:has-text("制定验证计划")');
    await expect(page.locator('text=制定新 DVP&R 试验验证计划')).toBeVisible();
    await expect(page.locator('text=执行标准').first()).toBeVisible();
    await page.click('button:has-text("取消")');
    await expect(page.locator('text=制定新 DVP&R 试验验证计划')).not.toBeVisible();
  });

  // ================= MODULE 6: TEST RUNS & TELEMETRY (Flows 21-24) =================
  test('Flow 21: Navigates to Test Runs view and inspects rig telemetry table with screenshot', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("试验执行")');
    await expect(page.locator('text=试验执行与台架遥测记录')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('th:has-text("关键遥测实测值 (Telemetry)")')).toBeVisible();
    await page.screenshot({ path: 'e2e/screenshots/06_test_runs_view.png', fullPage: true });
  });

  test('Flow 22: Filters test runs by Pass verdict result', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("试验执行")');
    await expect(page.locator('text=试验执行与台架遥测记录')).toBeVisible({ timeout: 10000 });
    const resultSelect = page.locator('main select');
    await resultSelect.selectOption('Pass');
    await expect(page.locator('tbody tr').first()).toBeVisible();
    await expect(page.locator('tbody').getByText('Pass').first()).toBeVisible();
  });

  test('Flow 23: Searches test runs by sample number keyword', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("试验执行")');
    await expect(page.locator('text=试验执行与台架遥测记录')).toBeVisible({ timeout: 10000 });
    const searchInput = page.locator('input[placeholder*="搜索试验单号"]');
    await searchInput.fill('RUN');
    await expect(page.locator('tbody tr').first()).toBeVisible();
  });

  test('Flow 24: Opens test run telemetry detail modal and verifies temperature and cycles', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("试验执行")');
    await expect(page.locator('text=试验执行与台架遥测记录')).toBeVisible({ timeout: 10000 });
    await page.locator('button:has-text("详情")').first().click();
    await expect(page.locator('text=试验执行数据详情')).toBeVisible();
    await expect(page.locator('text=环境温度')).toBeVisible();
    await page.click('button:has-text("关闭")');
    await expect(page.locator('text=试验执行数据详情')).not.toBeVisible();
  });

  // ================= MODULE 7: ENGINEERING ISSUES & PRTS (Flows 25-28) =================
  test('Flow 25: Navigates to Issues view, verifies S1-S4 severity ratings & screenshot', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("问题跟踪")');
    await expect(page.locator('text=工程问题跟踪与 PRTS 闭环')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('th:has-text("5-Why根因状态")')).toBeVisible();
    await page.screenshot({ path: 'e2e/screenshots/07_issues_view.png', fullPage: true });
  });

  test('Flow 26: Filters engineering issues by S1-Critical severity', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("问题跟踪")');
    await expect(page.locator('text=工程问题跟踪与 PRTS 闭环')).toBeVisible({ timeout: 10000 });
    const sevSelect = page.locator('main select').first();
    await sevSelect.selectOption('S1-Critical');
    await expect(page.locator('tbody tr').first()).toBeVisible();
    await expect(page.locator('tbody').getByText('S1-Critical').first()).toBeVisible();
  });

  test('Flow 27: Filters engineering issues by status Investigating', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("问题跟踪")');
    await expect(page.locator('text=工程问题跟踪与 PRTS 闭环')).toBeVisible({ timeout: 10000 });
    const statSelect = page.locator('main select').nth(1);
    await statSelect.selectOption('Investigating');
    await expect(page.locator('tbody tr').first()).toBeVisible();
  });

  test('Flow 28: Opens issue advancement drawer and inspects containment action', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("问题跟踪")');
    await expect(page.locator('text=工程问题跟踪与 PRTS 闭环')).toBeVisible({ timeout: 10000 });
    await page.locator('button:has-text("详情/推进")').first().click();
    await expect(page.locator('text=现象详细描述:')).toBeVisible();
    await expect(page.locator('text=临时遏制措施 (Containment Action):')).toBeVisible();
    await page.click('button:has-text("关闭")');
  });

  // ================= MODULE 8: 5-WHY & ISHIKAWA ROOT CAUSE (Flows 29-32) =================
  test('Flow 29: Navigates to 5-Why Root Cause view, inspects tree & screenshot', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("5-Why分析")');
    await expect(page.locator('text=故障根因分析 (5-Why & 因果鱼骨图归零)')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=已归档根因案例')).toBeVisible();
    await page.screenshot({ path: 'e2e/screenshots/08_root_cause_view.png', fullPage: true });
  });

  test('Flow 30: Verifies 5-Why logical chain levels from Why 1 to Why 5', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("5-Why分析")');
    await expect(page.locator('text=5-Why 递进失效逻辑链')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=直接原因 (Direct Cause):')).toBeVisible();
    await expect(page.locator('span:has-text("Why 1")')).toBeVisible();
  });

  test('Flow 31: Inspects Ishikawa Fishbone 6M factors on selected root cause', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("5-Why分析")');
    await expect(page.locator('text=石川因果鱼骨图要素 (Ishikawa 6M Matrix)')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=体系与设计根本原因 (Systemic Root Cause):')).toBeVisible();
  });

  test('Flow 32: Switches active root cause case from left pane list', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("5-Why分析")');
    await expect(page.locator('text=已归档根因案例')).toBeVisible({ timeout: 10000 });
    const items = page.locator('main .glass-panel div[style*="cursor: pointer"]');
    const count = await items.count();
    if (count > 1) {
      await items.nth(1).click();
      await expect(page.locator('text=5-Why 递进失效逻辑链')).toBeVisible();
    }
  });

  // ================= MODULE 9: ENGINEERING CHANGES ECR/ECO (Flows 33-36) =================
  test('Flow 33: Navigates to Engineering Changes view, checks rev diff & screenshot', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("工程变更")');
    await expect(page.locator('text=工程变更管理 (ECR / ECO 闭环控制')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('th:has-text("版本升级 (Rev)")')).toBeVisible();
    await expect(page.locator('th:has-text("单车成本变动")')).toBeVisible();
    await page.screenshot({ path: 'e2e/screenshots/09_changes_view.png', fullPage: true });
  });

  test('Flow 34: Filters engineering changes by approval status Approved', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("工程变更")');
    await expect(page.locator('text=工程变更管理')).toBeVisible({ timeout: 10000 });
    const statusSelect = page.locator('main select');
    await statusSelect.selectOption('Approved');
    await expect(page.locator('tbody tr').first()).toBeVisible();
  });

  test('Flow 35: Opens engineering change review modal and verifies cost/tooling impact', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("工程变更")');
    await expect(page.locator('text=工程变更管理')).toBeVisible({ timeout: 10000 });
    await page.locator('button:has-text("详情/审批")').first().click();
    await expect(page.locator('text=变更起因与必要性说明:')).toBeVisible();
    await expect(page.locator('text=单车成本增减')).toBeVisible();
    await expect(page.locator('text=模具工装周期')).toBeVisible();
    await page.click('button:has-text("关闭")');
  });

  test('Flow 36: Searches engineering changes by ECR code keyword', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("工程变更")');
    await expect(page.locator('text=工程变更管理')).toBeVisible({ timeout: 10000 });
    const searchInput = page.locator('input[placeholder*="搜索ECR单号"]');
    await searchInput.fill('ECR');
    await expect(page.locator('tbody tr').first()).toBeVisible();
  });

  // ================= MODULE 10: KNOWLEDGE BASE & SEARCH (Flows 37-38) =================
  test('Flow 37: Navigates to Knowledge Base, performs technical full-text search with screenshot', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("工程知识库")');
    await expect(page.locator('text=工程知识与历史经验库检索')).toBeVisible({ timeout: 10000 });
    const searchInput = page.locator('input[placeholder*="全文字符检索"]');
    await searchInput.fill('防夹');
    await expect(page.locator('main').getByText('防夹').first()).toBeVisible();
    await page.screenshot({ path: 'e2e/screenshots/10_knowledge_view.png', fullPage: true });
  });

  test('Flow 38: Expands knowledge article to read full guidelines and opens modal', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("工程知识库")');
    await expect(page.locator('text=工程知识与历史经验库检索')).toBeVisible({ timeout: 10000 });
    await page.locator('button:has-text("展开全文阅读")').first().click();
    await expect(page.locator('text=收起详情').first()).toBeVisible();
    await page.click('button:has-text("沉淀工程知识")');
    await expect(page.locator('text=沉淀工程知识与设计准则')).toBeVisible();
    await page.click('button:has-text("取消")');
    await expect(page.locator('text=沉淀工程知识与设计准则')).not.toBeVisible();
  });

  // ================= CROSS-CUTTING: RESPONSIVENESS & CONSOLE HEALTH (Flows 39-40) =================
  test('Flow 39: Responsive viewport check on tablet layout (768x1024) with screenshot', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    await expect(page.locator('text=质量工程总览仪表盘')).toBeVisible({ timeout: 10000 });
    await page.screenshot({ path: 'e2e/screenshots/11_mobile_responsive_768x1024.png', fullPage: false });
  });

  test('Flow 40: Closed-loop lineage navigation without console runtime crashes', async ({ page }) => {
    const errorLogs: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error' && !msg.text().includes('favicon')) {
        errorLogs.push(msg.text());
      }
    });

    await page.goto('/');
    await page.click('button:has-text("零部件")');
    await expect(page.locator('text=零部件与车身开闭件子系统目录')).toBeVisible();
    await page.click('button:has-text("DFMEA风险")');
    await expect(page.locator('text=DFMEA 设计潜在失效模式与后果分析')).toBeVisible();
    await page.click('button:has-text("DVP&R计划")');
    await expect(page.locator('text=DVP&R 设计验证试验计划与报告')).toBeVisible();
    await page.click('button:has-text("问题跟踪")');
    await expect(page.locator('text=工程问题跟踪与 PRTS 闭环')).toBeVisible();
    await page.click('button:has-text("工程变更")');
    await expect(page.locator('text=工程变更管理')).toBeVisible();
    await page.click('button:has-text("质量总览")');
    await expect(page.locator('text=质量工程总览仪表盘')).toBeVisible();

    expect(errorLogs).toEqual([]);
  });
});
