import { test, expect } from '@playwright/test';

test.describe('Automotive Engineering Quality Lab - End-to-End System Tests', () => {
  test('User can inspect Quality Dashboard, navigate modules, and search Knowledge Base', async ({ page }) => {
    // 1. Visit root page
    await page.goto('/');

    // 2. Check brand header & dashboard
    await expect(page.locator('header').getByText('汽车研发工程质量管理平台')).toBeVisible();
    await expect(page.locator('text=质量工程总览仪表盘')).toBeVisible({ timeout: 10000 });
    
    // Check presence of KPI summary cards
    await expect(page.locator('text=开闭件与密封子系统健康度排名')).toBeVisible();
    await expect(page.locator('text=DFMEA 风险行动优先级')).toBeVisible();

    // 3. Navigate to Programs View
    await page.click('button:has-text("车型项目")');
    await expect(page.locator('text=车型项目与研发平台管理')).toBeVisible();
    await expect(page.locator('main').getByText('Aurora EV SUV').first()).toBeVisible();

    // 4. Navigate to Parts View
    await page.click('button:has-text("零部件")');
    await expect(page.locator('text=零部件与车身开闭件子系统目录')).toBeVisible();

    // 5. Navigate to DFMEA View
    await page.click('button:has-text("DFMEA风险")');
    await expect(page.locator('text=DFMEA 设计潜在失效模式与后果分析')).toBeVisible();
    await expect(page.locator('th:has-text("AP 行动优先级")')).toBeVisible();

    // 6. Navigate to 5-Why Root Cause View
    await page.click('button:has-text("5-Why分析")');
    await expect(page.locator('text=5-Why 递进失效逻辑链')).toBeVisible();
    await expect(page.locator('text=石川因果鱼骨图要素')).toBeVisible();

    // 7. Navigate to Knowledge Base View & perform search
    await page.click('button:has-text("工程知识库")');
    await expect(page.locator('text=工程知识与历史经验库检索')).toBeVisible();

    // Search for "漏水"
    const searchInput = page.locator('input[placeholder*="全文字符检索"]');
    await searchInput.fill('漏水');
    await expect(page.locator('text=车门主密封条在高压洗车工况下的微量进水机理及对策')).toBeVisible();
  });
});
