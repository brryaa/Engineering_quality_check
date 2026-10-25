import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ChangesView } from '../views/ChangesView';
import { api } from '../api/client';
import { EngineeringChange, Program, PaginatedResponse } from '../types';

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

const mockChanges: EngineeringChange[] = [
  {
    id: 1,
    change_code: 'ECR-SEAL-001',
    program_id: 1,
    program_code: 'EP9-CLOSURE',
    part_id: 101,
    part_number: 'P-DOOR-SEAL-01',
    title: 'Reinforce B-pillar EPDM corner joint with localized sponge insert',
    change_type: 'Design-Mod',
    reason: 'Eliminate high-pressure car wash water seep',
    pre_change_rev: 'A.1',
    post_change_rev: 'B.0',
    cost_impact_rmb: 3.20,
    weight_impact_kg: 0.04,
    tooling_lead_weeks: 3,
    requires_homologation: false,
    requires_dvp_retest: true,
    approval_status: 'Approved',
    initiator: 'Eng. Lin',
    approver: 'Dr. Wei Chen',
    approval_date: '2026-10-22',
    created_at: '2026-10-20T08:00:00Z',
    updated_at: '2026-10-22T08:00:00Z'
  },
  {
    id: 2,
    change_code: 'ECR-WIN-002',
    program_id: 1,
    program_code: 'EP9-CLOSURE',
    part_id: 102,
    part_number: 'P-WIN-REG-02',
    title: 'Pulley POM material upgrade with 30% glass fiber',
    change_type: 'Material-Change',
    reason: 'Prevent cold temperature cable groove deflection',
    pre_change_rev: 'B.0',
    post_change_rev: 'B.1',
    cost_impact_rmb: 1.80,
    weight_impact_kg: -0.01,
    tooling_lead_weeks: 2,
    requires_homologation: false,
    requires_dvp_retest: true,
    approval_status: 'Review-Eng',
    initiator: 'Eng. Zhao',
    created_at: '2026-10-21T08:00:00Z',
    updated_at: '2026-10-21T08:00:00Z'
  }
];

const mockPaginatedChanges: PaginatedResponse<EngineeringChange> = {
  items: mockChanges,
  total: 2,
  page: 1,
  page_size: 20,
  pages: 1
};

describe('ChangesView Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(api, 'getChanges').mockResolvedValue(mockPaginatedChanges);
    vi.spyOn(api, 'updateChange').mockResolvedValue(mockChanges[0]);
  });

  it('renders engineering changes title and total counter', async () => {
    render(<ChangesView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText(/工程变更管理/)).toBeInTheDocument();
      expect(screen.getByText(/2 件/)).toBeInTheDocument();
    });
  });

  it('renders change codes in table', async () => {
    render(<ChangesView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText('ECR-SEAL-001')).toBeInTheDocument();
      expect(screen.getByText('ECR-WIN-002')).toBeInTheDocument();
    });
  });

  it('renders change titles', async () => {
    render(<ChangesView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText(/Reinforce B-pillar EPDM corner joint/)).toBeInTheDocument();
      expect(screen.getByText(/Pulley POM material upgrade with 30% glass fiber/)).toBeInTheDocument();
    });
  });

  it('displays pre-change and post-change revision tags', async () => {
    render(<ChangesView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText('A.1')).toBeInTheDocument();
      expect(screen.getAllByText('B.0').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('displays change types', async () => {
    render(<ChangesView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText('Design-Mod')).toBeInTheDocument();
      expect(screen.getByText('Material-Change')).toBeInTheDocument();
    });
  });

  it('displays approval status badges', async () => {
    render(<ChangesView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText('Approved')).toBeInTheDocument();
      expect(screen.getByText('Review-Eng')).toBeInTheDocument();
    });
  });

  it('displays cost impact in RMB', async () => {
    render(<ChangesView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText('+¥3.2')).toBeInTheDocument();
      expect(screen.getByText('+¥1.8')).toBeInTheDocument();
    });
  });

  it('displays tooling lead times in weeks', async () => {
    render(<ChangesView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText('3 周')).toBeInTheDocument();
      expect(screen.getByText('2 周')).toBeInTheDocument();
    });
  });

  it('filters changes by approval status', async () => {
    render(<ChangesView programs={mockPrograms} />);
    const statusSelect = screen.getByDisplayValue('全部审批状态');
    fireEvent.change(statusSelect, { target: { value: 'Approved' } });

    await waitFor(() => {
      expect(api.getChanges).toHaveBeenCalledWith(expect.objectContaining({
        approval_status: 'Approved'
      }));
    });
  });

  it('searches changes by query keyword', async () => {
    render(<ChangesView programs={mockPrograms} />);
    const searchInput = screen.getByPlaceholderText('搜索ECR单号/变更主题/发起人...');
    fireEvent.change(searchInput, { target: { value: 'pulley' } });

    await waitFor(() => {
      expect(api.getChanges).toHaveBeenCalledWith(expect.objectContaining({
        search: 'pulley'
      }));
    });
  });

  it('opens detail drawer when row is clicked', async () => {
    render(<ChangesView programs={mockPrograms} />);
    const detailBtns = await screen.findAllByText('详情/审批');
    fireEvent.click(detailBtns[0]);

    await waitFor(() => {
      expect(screen.getByText('变更起因与必要性说明:')).toBeInTheDocument();
      expect(screen.getAllByText('Eliminate high-pressure car wash water seep').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('renders empty table when no ECRs found', async () => {
    vi.spyOn(api, 'getChanges').mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      pages: 1
    });
    render(<ChangesView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText('无符合条件的工程变更记录')).toBeInTheDocument();
    });
  });
});
