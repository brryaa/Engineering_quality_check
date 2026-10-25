import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { DvprView } from '../views/DvprView';
import { api } from '../api/client';
import { DVPR, Program, PaginatedResponse } from '../types';

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

const mockDvprs: DVPR[] = [
  {
    id: 1,
    program_id: 1,
    program_code: 'EP9-CLOSURE',
    part_id: 101,
    part_number: 'P-DOOR-SEAL-01',
    plan_code: 'DVP-SEAL-SPRAY-01',
    test_phase: 'DV-A',
    test_name: 'High Pressure Water Ingress Chamber Test',
    test_standard: 'ISO 20653 IPX9K',
    acceptance_criteria: 'Zero water penetration past secondary bulb',
    sample_size: 4,
    test_facility: 'Chamber #2',
    planned_start_date: '2026-11-01',
    planned_end_date: '2026-11-15',
    status: 'Passed',
    responsible_engineer: 'Eng. Lin',
    test_runs_count: 4,
    created_at: '2026-10-01T08:00:00Z',
    updated_at: '2026-10-01T08:00:00Z'
  },
  {
    id: 2,
    program_id: 1,
    program_code: 'EP9-CLOSURE',
    part_id: 102,
    part_number: 'P-WIN-REG-02',
    plan_code: 'DVP-WIN-DUR-02',
    test_phase: 'PV-C',
    test_name: 'Window Regulator 30,000 Cycle Durability',
    test_standard: 'QC/T 627',
    acceptance_criteria: 'Operating speed reduction < 15%',
    sample_size: 3,
    test_facility: 'Durability Rig #3',
    planned_start_date: '2026-11-10',
    planned_end_date: '2026-11-30',
    status: 'In Progress',
    responsible_engineer: 'Eng. Zhao',
    test_runs_count: 1,
    created_at: '2026-10-02T08:00:00Z',
    updated_at: '2026-10-02T08:00:00Z'
  }
];

const mockPaginatedDvpr: PaginatedResponse<DVPR> = {
  items: mockDvprs,
  total: 2,
  page: 1,
  page_size: 20,
  pages: 1
};

describe('DvprView Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(api, 'getDvprs').mockResolvedValue(mockPaginatedDvpr);
  });

  it('renders DVP&R title and total plan counter', async () => {
    render(<DvprView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText(/DVP&R 设计验证试验计划与报告/)).toBeInTheDocument();
      expect(screen.getByText(/2 项/)).toBeInTheDocument();
    });
  });

  it('renders plan codes', async () => {
    render(<DvprView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText('DVP-SEAL-SPRAY-01')).toBeInTheDocument();
      expect(screen.getByText('DVP-WIN-DUR-02')).toBeInTheDocument();
    });
  });

  it('renders test names', async () => {
    render(<DvprView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText('High Pressure Water Ingress Chamber Test')).toBeInTheDocument();
      expect(screen.getByText('Window Regulator 30,000 Cycle Durability')).toBeInTheDocument();
    });
  });

  it('displays test standards', async () => {
    render(<DvprView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText('ISO 20653 IPX9K')).toBeInTheDocument();
      expect(screen.getByText('QC/T 627')).toBeInTheDocument();
    });
  });

  it('displays test phases', async () => {
    render(<DvprView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText('DV-A')).toBeInTheDocument();
      expect(screen.getByText('PV-C')).toBeInTheDocument();
    });
  });

  it('displays status badges', async () => {
    render(<DvprView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText('Passed')).toBeInTheDocument();
      expect(screen.getByText('In Progress')).toBeInTheDocument();
    });
  });

  it('displays responsible engineers', async () => {
    render(<DvprView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText('Eng. Lin')).toBeInTheDocument();
      expect(screen.getByText('Eng. Zhao')).toBeInTheDocument();
    });
  });

  it('displays sample sizes and facility', async () => {
    render(<DvprView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText(/4 pcs/)).toBeInTheDocument();
      expect(screen.getByText('Chamber #2')).toBeInTheDocument();
    });
  });

  it('filters DVP&R by test phase', async () => {
    render(<DvprView programs={mockPrograms} />);
    const phaseSelect = screen.getByDisplayValue('全部验证阶段');
    fireEvent.change(phaseSelect, { target: { value: 'DV-A' } });

    await waitFor(() => {
      expect(api.getDvprs).toHaveBeenCalledWith(expect.objectContaining({
        test_phase: 'DV-A'
      }));
    });
  });

  it('filters DVP&R by status', async () => {
    render(<DvprView programs={mockPrograms} />);
    const statusSelect = screen.getByDisplayValue('全部计划状态');
    fireEvent.change(statusSelect, { target: { value: 'Passed' } });

    await waitFor(() => {
      expect(api.getDvprs).toHaveBeenCalledWith(expect.objectContaining({
        status: 'Passed'
      }));
    });
  });

  it('opens new verification plan modal', async () => {
    render(<DvprView programs={mockPrograms} />);
    fireEvent.click(screen.getByText('制定验证计划'));
    expect(screen.getByText('制定新 DVP&R 试验验证计划')).toBeInTheDocument();
  });

  it('renders empty table when no DVP records exist', async () => {
    vi.spyOn(api, 'getDvprs').mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      pages: 1
    });
    render(<DvprView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText('无符合条件的验证计划')).toBeInTheDocument();
    });
  });
});
