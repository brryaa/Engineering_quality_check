import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from '../App';
import { Badge } from '../components/Badge';
import { api } from '../api/client';
import { QualityDashboardStats, Program } from '../types';

const mockStats: QualityDashboardStats = {
  total_programs: 10,
  total_parts: 200,
  total_dfmeas: 300,
  total_dvprs: 500,
  total_test_runs: 1000,
  total_issues: 500,
  total_changes: 200,
  dfmea_high_ap_count: 50,
  dfmea_medium_ap_count: 100,
  dfmea_low_ap_count: 150,
  dfmea_high_rpn_count: 80,
  dvpr_status_counts: { Passed: 300, 'In Progress': 100, Failed: 100 },
  test_run_pass_rate_pct: 82.5,
  test_run_result_counts: { Pass: 825, Fail: 175 },
  issue_severity_counts: { 'S1-Critical': 40, 'S2-Major': 160 },
  issue_status_counts: { Closed: 200, Investigating: 150 },
  open_critical_issues_count: 10,
  total_change_cost_impact_rmb: 35000.0,
  changes_by_status: { Approved: 80, Implemented: 120 },
  subsystem_health: [
    { subsystem: 'Front Door Closure', total_issues: 35, open_critical_issues: 1, health_score: 85 }
  ]
};

const mockPrograms: Program[] = [
  {
    id: 1,
    code: 'EP9-CLOSURE',
    name: 'Electric Coupe Frameless',
    platform: 'EV-800V-Platform',
    phase: 'DV',
    lead_engineer: 'Lead',
    quality_manager: 'QM',
    target_market: 'Global',
    created_at: '2026-10-01T08:00:00Z',
    updated_at: '2026-10-01T08:00:00Z'
  }
];

describe('App & Global Component Suite', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(api, 'getDashboardStats').mockResolvedValue(mockStats);
    vi.spyOn(api, 'getPrograms').mockResolvedValue({
      items: mockPrograms,
      total: 1,
      page: 1,
      page_size: 50,
      pages: 1
    });
  });

  it('renders App with header branding', async () => {
    render(<App />);
    expect(screen.getByText('汽车研发工程质量管理平台')).toBeInTheDocument();
  });

  it('navigates to Programs view when tab clicked', async () => {
    render(<App />);
    const progTab = screen.getByText('车型项目');
    fireEvent.click(progTab);
    await waitFor(() => {
      expect(screen.getByText('车型项目与研发平台管理')).toBeInTheDocument();
    });
  });

  it('navigates to Parts view when tab clicked', async () => {
    vi.spyOn(api, 'getParts').mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20, pages: 1 });
    render(<App />);
    fireEvent.click(screen.getByText('零部件'));
    await waitFor(() => {
      expect(screen.getByText(/零部件与车身开闭件子系统目录/)).toBeInTheDocument();
    });
  });

  it('navigates to DFMEA view when tab clicked', async () => {
    vi.spyOn(api, 'getDfmeas').mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20, pages: 1 });
    render(<App />);
    fireEvent.click(screen.getByText('DFMEA风险'));
    await waitFor(() => {
      expect(screen.getByText(/DFMEA 设计潜在失效模式与后果分析/)).toBeInTheDocument();
    });
  });

  it('navigates to DVP&R view when tab clicked', async () => {
    vi.spyOn(api, 'getDvprs').mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20, pages: 1 });
    render(<App />);
    fireEvent.click(screen.getByText('DVP&R计划'));
    await waitFor(() => {
      expect(screen.getByText(/DVP&R 设计验证试验计划与报告/)).toBeInTheDocument();
    });
  });

  it('navigates to Test Runs view when tab clicked', async () => {
    vi.spyOn(api, 'getTestRuns').mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20, pages: 1 });
    render(<App />);
    fireEvent.click(screen.getByText('试验执行'));
    await waitFor(() => {
      expect(screen.getByText(/试验执行与台架遥测记录/)).toBeInTheDocument();
    });
  });

  it('navigates to Issues view when tab clicked', async () => {
    vi.spyOn(api, 'getIssues').mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20, pages: 1 });
    render(<App />);
    fireEvent.click(screen.getByText('问题跟踪'));
    await waitFor(() => {
      expect(screen.getByText(/工程问题跟踪与 PRTS 闭环/)).toBeInTheDocument();
    });
  });

  it('navigates to Root Cause view when tab clicked', async () => {
    vi.spyOn(api, 'getRootCauses').mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20, pages: 1 });
    render(<App />);
    fireEvent.click(screen.getByText('5-Why分析'));
    await waitFor(() => {
      expect(screen.getByText('故障根因分析 (5-Why & 因果鱼骨图归零)')).toBeInTheDocument();
    });
  });

  it('navigates to Changes view when tab clicked', async () => {
    vi.spyOn(api, 'getChanges').mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20, pages: 1 });
    render(<App />);
    fireEvent.click(screen.getByText('工程变更'));
    await waitFor(() => {
      expect(screen.getByText(/工程变更管理/)).toBeInTheDocument();
    });
  });

  it('navigates to Knowledge view when tab clicked', async () => {
    vi.spyOn(api, 'getKnowledgeItems').mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20, pages: 1 });
    render(<App />);
    fireEvent.click(screen.getByText('工程知识库'));
    await waitFor(() => {
      expect(screen.getByText(/工程知识与历史经验库检索/)).toBeInTheDocument();
    });
  });

  describe('Badge Component Rendering', () => {
    it('renders High AP with computed rose styling', () => {
      render(<Badge label="High" />);
      expect(screen.getByText('High')).toBeInTheDocument();
    });

    it('renders Medium AP with computed amber styling', () => {
      render(<Badge label="Medium" />);
      expect(screen.getByText('Medium')).toBeInTheDocument();
    });

    it('renders Low AP with computed emerald styling', () => {
      render(<Badge label="Low" />);
      expect(screen.getByText('Low')).toBeInTheDocument();
    });

    it('renders S1-Critical with danger styling', () => {
      render(<Badge label="S1-Critical" />);
      expect(screen.getByText('S1-Critical')).toBeInTheDocument();
    });

    it('renders Pass result with success badge', () => {
      render(<Badge label="Pass" />);
      expect(screen.getByText('Pass')).toBeInTheDocument();
    });

    it('renders Fail result with danger badge', () => {
      render(<Badge label="Fail" />);
      expect(screen.getByText('Fail')).toBeInTheDocument();
    });
  });
});
