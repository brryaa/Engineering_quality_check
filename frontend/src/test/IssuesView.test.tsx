import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { IssuesView } from '../views/IssuesView';
import { api } from '../api/client';
import { EngineeringIssue, PaginatedResponse } from '../types';

const mockIssues: EngineeringIssue[] = [
  {
    id: 1,
    issue_code: 'ISS-DOOR-LEAK-01',
    program_id: 1,
    program_code: 'EP9-CLOSURE',
    part_id: 101,
    part_number: 'P-DOOR-SEAL-01',
    title: 'Severe B-pillar weatherstrip water leak in car wash',
    severity: 'S1-Critical',
    status: 'Investigating',
    description: 'Water drips onto interior trim under high-pressure spray',
    occurrence_phase: 'PV-Trial',
    containment_action: 'Manual silicone caulking on pilot vehicle fleet',
    assignee: 'Eng. Lin',
    reporter: 'QA Inspector Wu',
    due_date: '2026-11-20',
    has_root_cause: true,
    created_at: '2026-10-10T08:00:00Z',
    updated_at: '2026-10-10T08:00:00Z'
  },
  {
    id: 2,
    issue_code: 'ISS-RATTLE-02',
    program_id: 1,
    program_code: 'EP9-CLOSURE',
    part_id: 102,
    part_number: 'P-WIN-REG-02',
    title: 'Door panel acoustic buzzing rattle at 1800 RPM engine harmonic',
    severity: 'S3-Minor',
    status: 'Closed',
    description: 'Resonance buzzing between guide channel bracket and door inner panel',
    occurrence_phase: 'Field-Feedback',
    assignee: 'Acoustic Specialist Hu',
    reporter: 'Ride & Handling Eng',
    due_date: '2026-11-05',
    closure_date: '2026-11-04',
    has_root_cause: false,
    created_at: '2026-10-12T08:00:00Z',
    updated_at: '2026-10-12T08:00:00Z'
  }
];

const mockPaginatedIssues: PaginatedResponse<EngineeringIssue> = {
  items: mockIssues,
  total: 2,
  page: 1,
  page_size: 20,
  pages: 1
};

describe('IssuesView Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(api, 'getIssues').mockResolvedValue(mockPaginatedIssues);
    vi.spyOn(api, 'updateIssue').mockResolvedValue(mockIssues[0]);
  });

  it('renders issues title and counter', async () => {
    render(<IssuesView />);
    await waitFor(() => {
      expect(screen.getByText(/工程问题跟踪与 PRTS 闭环/)).toBeInTheDocument();
      expect(screen.getByText(/2 件/)).toBeInTheDocument();
    });
  });

  it('renders issue codes', async () => {
    render(<IssuesView />);
    await waitFor(() => {
      expect(screen.getByText('ISS-DOOR-LEAK-01')).toBeInTheDocument();
      expect(screen.getByText('ISS-RATTLE-02')).toBeInTheDocument();
    });
  });

  it('renders issue titles', async () => {
    render(<IssuesView />);
    await waitFor(() => {
      expect(screen.getByText('Severe B-pillar weatherstrip water leak in car wash')).toBeInTheDocument();
      expect(screen.getByText('Door panel acoustic buzzing rattle at 1800 RPM engine harmonic')).toBeInTheDocument();
    });
  });

  it('displays severity badges with correct labels', async () => {
    render(<IssuesView />);
    await waitFor(() => {
      expect(screen.getByText('S1-Critical')).toBeInTheDocument();
      expect(screen.getByText('S3-Minor')).toBeInTheDocument();
    });
  });

  it('displays 8-D lifecycle status badges', async () => {
    render(<IssuesView />);
    await waitFor(() => {
      expect(screen.getByText('Investigating')).toBeInTheDocument();
      expect(screen.getByText('Closed')).toBeInTheDocument();
    });
  });

  it('displays assignee and reporter', async () => {
    render(<IssuesView />);
    await waitFor(() => {
      expect(screen.getByText(/Eng. Lin/)).toBeInTheDocument();
      expect(screen.getByText(/Acoustic Specialist Hu/)).toBeInTheDocument();
    });
  });

  it('displays part numbers associated with defects', async () => {
    render(<IssuesView />);
    await waitFor(() => {
      expect(screen.getByText('P-DOOR-SEAL-01')).toBeInTheDocument();
      expect(screen.getByText('P-WIN-REG-02')).toBeInTheDocument();
    });
  });

  it('displays root cause indicator badge when available', async () => {
    render(<IssuesView />);
    await waitFor(() => {
      expect(screen.getByText('✓ 已归零')).toBeInTheDocument();
    });
  });

  it('filters issues by severity dropdown', async () => {
    render(<IssuesView />);
    const sevSelect = screen.getByDisplayValue('全部严重度等级');
    fireEvent.change(sevSelect, { target: { value: 'S1-Critical' } });

    await waitFor(() => {
      expect(api.getIssues).toHaveBeenCalledWith(expect.objectContaining({
        severity: 'S1-Critical'
      }));
    });
  });

  it('filters issues by status dropdown', async () => {
    render(<IssuesView />);
    const statSelect = screen.getByDisplayValue('全部问题状态');
    fireEvent.change(statSelect, { target: { value: 'Investigating' } });

    await waitFor(() => {
      expect(api.getIssues).toHaveBeenCalledWith(expect.objectContaining({
        status: 'Investigating'
      }));
    });
  });

  it('searches issues by search input query', async () => {
    render(<IssuesView />);
    const searchInput = screen.getByPlaceholderText('搜索问题编号/标题/责任人...');
    fireEvent.change(searchInput, { target: { value: 'water leak' } });

    await waitFor(() => {
      expect(api.getIssues).toHaveBeenCalledWith(expect.objectContaining({
        search: 'water leak'
      }));
    });
  });

  it('opens issue detail drawer when clicking an issue card', async () => {
    render(<IssuesView />);
    await waitFor(() => {
      const detailBtns = screen.getAllByText('详情/推进');
      fireEvent.click(detailBtns[0]);
    });

    await waitFor(() => {
      expect(screen.getByText(/临时遏制措施/)).toBeInTheDocument();
      expect(screen.getByText('Manual silicone caulking on pilot vehicle fleet')).toBeInTheDocument();
    });
  });
});
