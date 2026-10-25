import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { DashboardView } from '../views/DashboardView';
import { api } from '../api/client';
import { QualityDashboardStats } from '../types';

const mockStats: QualityDashboardStats = {
  total_programs: 12,
  total_parts: 233,
  total_dfmeas: 360,
  total_dvprs: 560,
  total_test_runs: 1116,
  total_issues: 530,
  total_changes: 230,
  dfmea_high_ap_count: 85,
  dfmea_medium_ap_count: 140,
  dfmea_low_ap_count: 135,
  dfmea_high_rpn_count: 120,
  dvpr_status_counts: { Passed: 320, 'In Progress': 150, Failed: 90 },
  test_run_pass_rate_pct: 84.5,
  test_run_result_counts: { Pass: 943, Fail: 173 },
  issue_severity_counts: { 'S1-Critical': 45, 'S2-Major': 180 },
  issue_status_counts: { Closed: 210, Investigating: 140 },
  open_critical_issues_count: 12,
  total_change_cost_impact_rmb: 45200.5,
  changes_by_status: { Approved: 90, Implemented: 140 },
  subsystem_health: [
    { subsystem: 'Front Door Closure', total_issues: 42, open_critical_issues: 1, health_score: 83 }
  ]
};

describe('DashboardView Component', () => {
  beforeEach(() => {
    vi.spyOn(api, 'getDashboardStats').mockResolvedValue(mockStats);
  });

  it('renders dashboard with stats metrics', async () => {
    render(<DashboardView />);

    await waitFor(() => {
      expect(screen.getByText('质量工程总览仪表盘 (全局统计)')).toBeInTheDocument();
      expect(screen.getByText('84.5%')).toBeInTheDocument();
      expect(screen.getAllByText('12').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('233')).toBeInTheDocument();
      expect(screen.getByText('Front Door Closure')).toBeInTheDocument();
    });
  });
});
