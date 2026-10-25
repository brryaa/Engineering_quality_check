import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { RootCauseView } from '../views/RootCauseView';
import { api } from '../api/client';
import { RootCauseAnalysis, PaginatedResponse } from '../types';

const mockRootCauses: RootCauseAnalysis[] = [
  {
    id: 1,
    issue_id: 101,
    issue_code: 'ISS-DOOR-LEAK-01',
    analysis_method: '5-Why',
    direct_cause: 'Extruded bulb seal lip lacked sufficient elastic rebound',
    why_1: 'Seal sponge porosity exceeded micro-cell density spec',
    why_2: 'Blowing agent dosage was reduced by 15% during extrusion run',
    why_3: 'Operator manually adjusted extruder feed hopper temperature',
    why_4: 'Automated closed-loop temperature control had thermocouple drift',
    why_5: 'Quarterly sensor calibration was delayed by 6 weeks',
    systemic_root_cause: 'Equipment PM quality gap: Critical sensor calibration intervals lacked ERP interlocking',
    fishbone_man: 'Operator manual override without formal sign-off',
    fishbone_machine: 'Thermocouple drift on heating zone 3',
    fishbone_material: 'Blowing agent decomposition rate variance',
    verification_method: 'Calibrate thermocouple and reproduce extrusion run; measure CLD >= 3.2 N/cm',
    verification_result: 'Confirmed',
    analyst: 'Quality Director Liu',
    analyzed_at: '2026-10-18',
    created_at: '2026-10-18T08:00:00Z',
    updated_at: '2026-10-18T08:00:00Z'
  },
  {
    id: 2,
    issue_id: 102,
    issue_code: 'ISS-RATTLE-02',
    analysis_method: 'Ishikawa-Fishbone',
    direct_cause: 'Clearance between glass guide bracket and inner door flange',
    systemic_root_cause: 'Tolerance stack-up in stamping assembly welding fixture',
    fishbone_machine: 'Welding fixture locator pin wear past 0.3mm limit',
    fishbone_method: 'Fixture wear inspection cycle not documented in control plan',
    verification_method: 'CMM scan of locator pins and vibration rig re-run',
    verification_result: 'Pending',
    analyst: 'Acoustic Specialist Hu',
    analyzed_at: '2026-10-20',
    created_at: '2026-10-20T08:00:00Z',
    updated_at: '2026-10-20T08:00:00Z'
  }
];

const mockPaginatedRc: PaginatedResponse<RootCauseAnalysis> = {
  items: mockRootCauses,
  total: 2,
  page: 1,
  page_size: 20,
  pages: 1
};

describe('RootCauseView Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(api, 'getRootCauses').mockResolvedValue(mockPaginatedRc);
  });

  it('renders root cause title and description', async () => {
    render(<RootCauseView />);
    expect(screen.getByText('故障根因分析 (5-Why & 因果鱼骨图归零)')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText('已归档根因案例 (2)')).toBeInTheDocument();
    });
  });

  it('renders list of root cause cases on left pane', async () => {
    render(<RootCauseView />);
    await waitFor(() => {
      expect(screen.getByText('ISS-DOOR-LEAK-01')).toBeInTheDocument();
      expect(screen.getByText('ISS-RATTLE-02')).toBeInTheDocument();
    });
  });

  it('displays analysis method badges', async () => {
    render(<RootCauseView />);
    await waitFor(() => {
      expect(screen.getByText(/分析方法: 5-Why/)).toBeInTheDocument();
    });
  });

  it('displays verification result badges', async () => {
    render(<RootCauseView />);
    await waitFor(() => {
      expect(screen.getByText('Confirmed')).toBeInTheDocument();
      expect(screen.getByText('Pending')).toBeInTheDocument();
    });
  });

  it('displays direct cause for selected case', async () => {
    render(<RootCauseView />);
    await waitFor(() => {
      expect(screen.getAllByText('Extruded bulb seal lip lacked sufficient elastic rebound').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('displays 5-Why cascading levels (Why 1 through Why 5)', async () => {
    render(<RootCauseView />);
    await waitFor(() => {
      expect(screen.getByText('Seal sponge porosity exceeded micro-cell density spec')).toBeInTheDocument();
      expect(screen.getByText('Blowing agent dosage was reduced by 15% during extrusion run')).toBeInTheDocument();
      expect(screen.getByText('Quarterly sensor calibration was delayed by 6 weeks')).toBeInTheDocument();
    });
  });

  it('displays systemic root cause banner', async () => {
    render(<RootCauseView />);
    await waitFor(() => {
      expect(screen.getByText(/Equipment PM quality gap/)).toBeInTheDocument();
    });
  });

  it('displays verification method and analyst', async () => {
    render(<RootCauseView />);
    await waitFor(() => {
      expect(screen.getByText(/Calibrate thermocouple and reproduce extrusion run/)).toBeInTheDocument();
      expect(screen.getByText(/Quality Director Liu/)).toBeInTheDocument();
    });
  });

  it('switches selected root cause when clicking second item in list', async () => {
    render(<RootCauseView />);
    await waitFor(() => {
      expect(screen.getByText('ISS-RATTLE-02')).toBeInTheDocument();
    });

    const secondItem = screen.getByText('ISS-RATTLE-02');
    fireEvent.click(secondItem);

    await waitFor(() => {
      expect(screen.getByText('Tolerance stack-up in stamping assembly welding fixture')).toBeInTheDocument();
    });
  });

  it('displays fishbone factors when available', async () => {
    render(<RootCauseView />);
    await waitFor(() => {
      expect(screen.getByText('Operator manual override without formal sign-off')).toBeInTheDocument();
      expect(screen.getByText('Thermocouple drift on heating zone 3')).toBeInTheDocument();
    });
  });

  it('renders analysis date in format YYYY-MM-DD', async () => {
    render(<RootCauseView />);
    await waitFor(() => {
      expect(screen.getByText(/2026-10-18/)).toBeInTheDocument();
    });
  });

  it('renders empty message when no root causes archived', async () => {
    vi.spyOn(api, 'getRootCauses').mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      pages: 1
    });
    render(<RootCauseView />);
    await waitFor(() => {
      expect(screen.getByText('暂无根因归零分析记录')).toBeInTheDocument();
    });
  });
});
