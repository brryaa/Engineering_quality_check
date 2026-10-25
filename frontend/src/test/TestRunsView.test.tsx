import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { TestRunsView } from '../views/TestRunsView';
import { api } from '../api/client';
import { TestRun, PaginatedResponse } from '../types';

const mockRuns: TestRun[] = [
  {
    id: 1,
    dvpr_id: 10,
    plan_code: 'DVP-SEAL-SPRAY-01',
    test_name: 'Water Ingress Chamber Test',
    run_number: 'RUN-SPRAY-202610-01',
    sample_id: 'SAMPLE-DOOR-01',
    test_date: '2026-10-15',
    test_facility: 'Water Chamber A',
    operator: 'Operator Li',
    temperature_c: 23.5,
    humidity_rh: 55.0,
    cycles_completed: 1000,
    measurement_data: '{"water_pressure_bar": 100, "flow_rate_lpm": 15}',
    result: 'Pass',
    created_at: '2026-10-15T08:00:00Z',
    updated_at: '2026-10-15T08:00:00Z'
  },
  {
    id: 2,
    dvpr_id: 11,
    plan_code: 'DVP-WIN-DUR-02',
    test_name: 'Window Regulator Cold Slam Durability',
    run_number: 'RUN-COLD-REG-02',
    sample_id: 'SAMPLE-WIN-04',
    test_date: '2026-10-16',
    test_facility: 'Climate Chamber #4',
    operator: 'Operator Zhang',
    temperature_c: -25.0,
    humidity_rh: 30.0,
    cycles_completed: 12500,
    measurement_data: '{"peak_current_a": 18.2, "stall_time_ms": 420}',
    result: 'Fail',
    failure_summary: 'Motor thermal trip triggered at cycle 12500 under -25C cold soak',
    created_at: '2026-10-16T08:00:00Z',
    updated_at: '2026-10-16T08:00:00Z'
  }
];

const mockPaginatedRuns: PaginatedResponse<TestRun> = {
  items: mockRuns,
  total: 2,
  page: 1,
  page_size: 20,
  pages: 1
};

describe('TestRunsView Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(api, 'getTestRuns').mockResolvedValue(mockPaginatedRuns);
  });

  it('renders test runs title and total counter', async () => {
    render(<TestRunsView />);
    await waitFor(() => {
      expect(screen.getByText(/试验执行与台架遥测记录/)).toBeInTheDocument();
      expect(screen.getByText(/2 轮次/)).toBeInTheDocument();
    });
  });

  it('renders run numbers in table', async () => {
    render(<TestRunsView />);
    await waitFor(() => {
      expect(screen.getByText('RUN-SPRAY-202610-01')).toBeInTheDocument();
      expect(screen.getByText('RUN-COLD-REG-02')).toBeInTheDocument();
    });
  });

  it('renders test names', async () => {
    render(<TestRunsView />);
    await waitFor(() => {
      expect(screen.getByText('Water Ingress Chamber Test')).toBeInTheDocument();
      expect(screen.getByText('Window Regulator Cold Slam Durability')).toBeInTheDocument();
    });
  });

  it('displays temperatures and humidity', async () => {
    render(<TestRunsView />);
    await waitFor(() => {
      expect(screen.getByText(/23.5℃/)).toBeInTheDocument();
      expect(screen.getByText(/-25℃/)).toBeInTheDocument();
    });
  });

  it('displays completed cycle counts', async () => {
    render(<TestRunsView />);
    await waitFor(() => {
      expect(screen.getByText(/1,000 次/)).toBeInTheDocument();
      expect(screen.getByText(/12,500 次/)).toBeInTheDocument();
    });
  });

  it('displays Pass and Fail result badges', async () => {
    render(<TestRunsView />);
    await waitFor(() => {
      expect(screen.getByText('Pass')).toBeInTheDocument();
      expect(screen.getByText('Fail')).toBeInTheDocument();
    });
  });

  it('displays operator names', async () => {
    render(<TestRunsView />);
    await waitFor(() => {
      expect(screen.getByText('Operator Li')).toBeInTheDocument();
      expect(screen.getByText('Operator Zhang')).toBeInTheDocument();
    });
  });

  it('displays test facilities', async () => {
    render(<TestRunsView />);
    await waitFor(() => {
      expect(screen.getByText('Water Chamber A')).toBeInTheDocument();
      expect(screen.getByText('Climate Chamber #4')).toBeInTheDocument();
    });
  });

  it('filters runs by result dropdown', async () => {
    render(<TestRunsView />);
    const resultSelect = screen.getByDisplayValue('全部试验结果');
    fireEvent.change(resultSelect, { target: { value: 'Fail' } });

    await waitFor(() => {
      expect(api.getTestRuns).toHaveBeenCalledWith(expect.objectContaining({
        result: 'Fail'
      }));
    });
  });

  it('searches runs by query keyword', async () => {
    render(<TestRunsView />);
    const searchInput = screen.getByPlaceholderText('搜索试验单号/样件/试验员...');
    fireEvent.change(searchInput, { target: { value: 'COLD-REG' } });

    await waitFor(() => {
      expect(api.getTestRuns).toHaveBeenCalledWith(expect.objectContaining({
        search: 'COLD-REG'
      }));
    });
  });

  it('opens telemetry detail modal when clicking a row', async () => {
    render(<TestRunsView />);
    await waitFor(() => {
      const detailBtns = screen.getAllByText(/详情/);
      fireEvent.click(detailBtns[0]);
    });

    await waitFor(() => {
      expect(screen.getByText('试验执行数据详情')).toBeInTheDocument();
    });
  });

  it('renders empty table when no test runs found', async () => {
    vi.spyOn(api, 'getTestRuns').mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      pages: 1
    });
    render(<TestRunsView />);
    await waitFor(() => {
      expect(screen.getByText('无符合条件的试验记录')).toBeInTheDocument();
    });
  });
});
