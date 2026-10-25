import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { DfmeaView } from '../views/DfmeaView';
import { api } from '../api/client';
import { DFMEA, PaginatedResponse } from '../types';

const mockDfmeas: DFMEA[] = [
  {
    id: 1,
    part_id: 101,
    part_number: 'P-DOOR-SEAL-01',
    fmea_code: 'DFMEA-SEAL-001',
    item_function: 'Prevent high-pressure water ingress into door frame',
    failure_mode: 'EPDM seal lip compression set over time',
    failure_effect: 'Water seep onto door sill at 120 km/h rain',
    severity: 8,
    cause_mechanism: 'Plasticizer migration under UV exposure',
    occurrence: 5,
    prevention_control: 'UV stabilizer package additive',
    detection_control: '1000h Xenon arc weathering chamber test',
    detection: 4,
    rpn: 160,
    action_priority: 'High',
    recommended_action: 'Upgrade EPDM recipe to sulfur/peroxide dual cure',
    action_owner: 'Chemical Engineer Lin',
    target_date: '2026-11-20',
    action_status: 'Completed',
    post_severity: 8,
    post_occurrence: 2,
    post_detection: 2,
    post_rpn: 32,
    created_at: '2026-10-01T08:00:00Z',
    updated_at: '2026-10-01T08:00:00Z'
  },
  {
    id: 2,
    part_id: 102,
    part_number: 'P-WIN-REG-02',
    fmea_code: 'DFMEA-WIN-002',
    item_function: 'Smooth glass ascent and descent in < 3.5s',
    failure_mode: 'Regulator cable pulley groove slip',
    failure_effect: 'Window fails to close completely',
    severity: 5,
    cause_mechanism: 'Pulley POM flange deflection',
    occurrence: 2,
    prevention_control: 'Glass-fiber reinforced POM material',
    detection_control: 'EOL cable tension sensor',
    detection: 2,
    rpn: 20,
    action_priority: 'Low',
    action_status: 'Open',
    created_at: '2026-10-02T08:00:00Z',
    updated_at: '2026-10-02T08:00:00Z'
  }
];

const mockPaginatedDfmea: PaginatedResponse<DFMEA> = {
  items: mockDfmeas,
  total: 2,
  page: 1,
  page_size: 20,
  pages: 1
};

describe('DfmeaView Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(api, 'getDfmeas').mockResolvedValue(mockPaginatedDfmea);
  });

  it('renders DFMEA header title and total count', async () => {
    render(<DfmeaView />);
    await waitFor(() => {
      expect(screen.getByText(/DFMEA 设计潜在失效模式与后果分析/)).toBeInTheDocument();
      expect(screen.getByText(/2 项/)).toBeInTheDocument();
    });
  });

  it('renders FMEA codes', async () => {
    render(<DfmeaView />);
    await waitFor(() => {
      expect(screen.getByText('DFMEA-SEAL-001')).toBeInTheDocument();
      expect(screen.getByText('DFMEA-WIN-002')).toBeInTheDocument();
    });
  });

  it('renders failure modes', async () => {
    render(<DfmeaView />);
    await waitFor(() => {
      expect(screen.getByText('EPDM seal lip compression set over time')).toBeInTheDocument();
      expect(screen.getByText('Regulator cable pulley groove slip')).toBeInTheDocument();
    });
  });

  it('displays Action Priority badges', async () => {
    render(<DfmeaView />);
    await waitFor(() => {
      expect(screen.getByText('High')).toBeInTheDocument();
      expect(screen.getByText('Low')).toBeInTheDocument();
    });
  });

  it('displays RPN values', async () => {
    render(<DfmeaView />);
    await waitFor(() => {
      expect(screen.getByText('160')).toBeInTheDocument();
      expect(screen.getByText('20')).toBeInTheDocument();
    });
  });

  it('displays S/O/D ratings', async () => {
    render(<DfmeaView />);
    await waitFor(() => {
      expect(screen.getByText('8')).toBeInTheDocument();
      expect(screen.getAllByText('5').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('4')).toBeInTheDocument();
    });
  });

  it('displays part number tags', async () => {
    render(<DfmeaView />);
    await waitFor(() => {
      expect(screen.getByText('P-DOOR-SEAL-01')).toBeInTheDocument();
      expect(screen.getByText('P-WIN-REG-02')).toBeInTheDocument();
    });
  });

  it('filters by Action Priority dropdown', async () => {
    render(<DfmeaView />);
    const apSelect = screen.getByDisplayValue('全部 AP 优先级');
    fireEvent.change(apSelect, { target: { value: 'High' } });

    await waitFor(() => {
      expect(api.getDfmeas).toHaveBeenCalledWith(expect.objectContaining({
        action_priority: 'High'
      }));
    });
  });

  it('filters by Minimum RPN input', async () => {
    render(<DfmeaView />);
    const minRpnSelect = screen.getByDisplayValue('全部 RPN 阈值');
    fireEvent.change(minRpnSelect, { target: { value: '100' } });

    await waitFor(() => {
      expect(api.getDfmeas).toHaveBeenCalledWith(expect.objectContaining({
        min_rpn: 100
      }));
    });
  });

  it('searches DFMEA by text keyword', async () => {
    render(<DfmeaView />);
    const searchInput = screen.getByPlaceholderText('搜索失效模式/原因/功能...');
    fireEvent.change(searchInput, { target: { value: 'Plasticizer' } });

    await waitFor(() => {
      expect(api.getDfmeas).toHaveBeenCalledWith(expect.objectContaining({
        search: 'Plasticizer'
      }));
    });
  });

  it('opens detail drawer when row is clicked', async () => {
    render(<DfmeaView />);
    await waitFor(() => {
      const reviewBtns = screen.getAllByText('审查措施');
      fireEvent.click(reviewBtns[0]);
    });
    await waitFor(() => {
      expect(screen.getByText('DFMEA 风险措施审查')).toBeInTheDocument();
    });
  });

  it('renders empty table message when no DFMEAs found', async () => {
    vi.spyOn(api, 'getDfmeas').mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      pages: 1
    });
    render(<DfmeaView />);
    await waitFor(() => {
      expect(screen.getByText('无符合筛选条件的 DFMEA 记录')).toBeInTheDocument();
    });
  });
});
