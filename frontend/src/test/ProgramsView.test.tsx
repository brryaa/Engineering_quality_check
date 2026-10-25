import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ProgramsView } from '../views/ProgramsView';
import { api } from '../api/client';
import { Program, PaginatedResponse } from '../types';

const mockPrograms: Program[] = [
  {
    id: 1,
    code: 'EP9-CLOSURE',
    name: 'Electric Coupe Frameless',
    platform: 'EV-800V-Platform',
    phase: 'DV',
    sop_date: '2027-10-01',
    lead_engineer: 'Dr. Wei Chen',
    quality_manager: 'Ying Zhao',
    target_market: 'Global',
    description: 'Flagship frameless coupe closure system',
    created_at: '2026-10-01T08:00:00Z',
    updated_at: '2026-10-01T08:00:00Z'
  },
  {
    id: 2,
    code: 'ES7-SUV',
    name: 'Midsize Electric SUV',
    platform: 'SUV-MODULAR',
    phase: 'PV',
    sop_date: '2027-05-01',
    lead_engineer: 'Zhang Hao',
    quality_manager: 'Li Director',
    target_market: 'China-Domestic',
    description: 'SUV tailgate and primary seal',
    created_at: '2026-10-02T08:00:00Z',
    updated_at: '2026-10-02T08:00:00Z'
  }
];

const mockPaginated: PaginatedResponse<Program> = {
  items: mockPrograms,
  total: 2,
  page: 1,
  page_size: 50,
  pages: 1
};

describe('ProgramsView Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(api, 'getPrograms').mockResolvedValue(mockPaginated);
    vi.spyOn(api, 'createProgram').mockResolvedValue(mockPrograms[0]);
  });

  it('renders heading title', async () => {
    render(<ProgramsView />);
    expect(screen.getByText('车型项目与研发平台管理')).toBeInTheDocument();
  });

  it('renders list of programs', async () => {
    render(<ProgramsView />);
    await waitFor(() => {
      expect(screen.getByText('EP9-CLOSURE')).toBeInTheDocument();
      expect(screen.getByText('Electric Coupe Frameless')).toBeInTheDocument();
      expect(screen.getByText('ES7-SUV')).toBeInTheDocument();
    });
  });

  it('displays lead engineer and quality manager', async () => {
    render(<ProgramsView />);
    await waitFor(() => {
      expect(screen.getByText(/Dr. Wei Chen/)).toBeInTheDocument();
      expect(screen.getByText(/Ying Zhao/)).toBeInTheDocument();
    });
  });

  it('displays platform tags', async () => {
    render(<ProgramsView />);
    await waitFor(() => {
      expect(screen.getByText('EV-800V-Platform')).toBeInTheDocument();
      expect(screen.getByText('SUV-MODULAR')).toBeInTheDocument();
    });
  });

  it('displays phase badges', async () => {
    render(<ProgramsView />);
    await waitFor(() => {
      expect(screen.getByText('DV')).toBeInTheDocument();
      expect(screen.getByText('PV')).toBeInTheDocument();
    });
  });

  it('displays SOP date', async () => {
    render(<ProgramsView />);
    await waitFor(() => {
      expect(screen.getByText('2027-10-01')).toBeInTheDocument();
    });
  });

  it('opens new program modal on click', async () => {
    render(<ProgramsView />);
    const addBtn = screen.getByText('新建车型项目');
    fireEvent.click(addBtn);
    expect(screen.getByText('创建新车型工程项目')).toBeInTheDocument();
  });

  it('allows closing modal with cancel button', async () => {
    render(<ProgramsView />);
    fireEvent.click(screen.getByText('新建车型项目'));
    expect(screen.getByText('创建新车型工程项目')).toBeInTheDocument();
    fireEvent.click(screen.getByText('取消'));
    expect(screen.queryByText('创建新车型工程项目')).not.toBeInTheDocument();
  });

  it('submits new program form successfully', async () => {
    render(<ProgramsView />);
    fireEvent.click(screen.getByText('新建车型项目'));

    const codeInput = screen.getByPlaceholderText('例如: P-EP40');
    const nameInput = screen.getByPlaceholderText('例如: Aurora EV Coupe');

    fireEvent.change(codeInput, { target: { value: 'ET5-NEW' } });
    fireEvent.change(nameInput, { target: { value: 'New Sedan Program' } });

    const submitBtn = screen.getByText('保存并提交');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(api.createProgram).toHaveBeenCalledWith(expect.objectContaining({
        code: 'ET5-NEW',
        name: 'New Sedan Program'
      }));
    });
  });

  it('handles search input change and calls api', async () => {
    render(<ProgramsView />);
    const searchInput = screen.getByPlaceholderText('搜索项目代号/名称...');
    fireEvent.change(searchInput, { target: { value: 'Frameless' } });

    await waitFor(() => {
      expect(api.getPrograms).toHaveBeenCalledWith(expect.objectContaining({
        search: 'Frameless'
      }));
    });
  });

  it('handles phase filter select change', async () => {
    render(<ProgramsView />);
    const phaseSelect = screen.getByDisplayValue('全部开发阶段');
    fireEvent.change(phaseSelect, { target: { value: 'Proto-A' } });

    await waitFor(() => {
      expect(api.getPrograms).toHaveBeenCalledWith(expect.objectContaining({
        phase: 'Proto-A'
      }));
    });
  });

  it('renders empty state when no programs match', async () => {
    vi.spyOn(api, 'getPrograms').mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      pages: 1
    });
    render(<ProgramsView />);
    await waitFor(() => {
      expect(screen.getByText('暂无符合条件的车型项目')).toBeInTheDocument();
    });
  });
});
