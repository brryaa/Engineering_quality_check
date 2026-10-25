import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { PartsView } from '../views/PartsView';
import { api } from '../api/client';
import { Part, Program, PaginatedResponse } from '../types';

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

const mockParts: Part[] = [
  {
    id: 101,
    program_id: 1,
    program_code: 'EP9-CLOSURE',
    part_number: 'P-DOOR-SEAL-01',
    name: 'Front Door Primary Weatherstrip Seal',
    subsystem: 'Primary Body Seal',
    category: 'EPDM-Sealing',
    supplier: 'Cooper Standard',
    material: 'EPDM Dual-Durometer Sponge',
    revision: 'A.2',
    weight_kg: 1.25,
    safety_critical: true,
    created_at: '2026-10-01T08:00:00Z',
    updated_at: '2026-10-01T08:00:00Z'
  },
  {
    id: 102,
    program_id: 1,
    program_code: 'EP9-CLOSURE',
    part_number: 'P-WIN-REG-02',
    name: 'Frameless Glass Cable Regulator',
    subsystem: 'Glass Regulator Module',
    category: 'Assembly',
    supplier: 'Brose Closures',
    material: 'Galvanized Steel / POM',
    revision: 'B.0',
    weight_kg: 2.40,
    safety_critical: false,
    created_at: '2026-10-02T08:00:00Z',
    updated_at: '2026-10-02T08:00:00Z'
  }
];

const mockPaginatedParts: PaginatedResponse<Part> = {
  items: mockParts,
  total: 2,
  page: 1,
  page_size: 20,
  pages: 1
};

describe('PartsView Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(api, 'getParts').mockResolvedValue(mockPaginatedParts);
    vi.spyOn(api, 'createPart').mockResolvedValue(mockParts[0]);
  });

  it('renders parts title and counter', async () => {
    render(<PartsView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText(/零部件与车身开闭件子系统目录/)).toBeInTheDocument();
      expect(screen.getByText(/2 件/)).toBeInTheDocument();
    });
  });

  it('renders part numbers in table', async () => {
    render(<PartsView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText('P-DOOR-SEAL-01')).toBeInTheDocument();
      expect(screen.getByText('P-WIN-REG-02')).toBeInTheDocument();
    });
  });

  it('renders part names', async () => {
    render(<PartsView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText('Front Door Primary Weatherstrip Seal')).toBeInTheDocument();
      expect(screen.getByText('Frameless Glass Cable Regulator')).toBeInTheDocument();
    });
  });

  it('displays subsystem badges', async () => {
    render(<PartsView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText('Primary Body Seal')).toBeInTheDocument();
      expect(screen.getByText('Glass Regulator Module')).toBeInTheDocument();
    });
  });

  it('displays supplier names', async () => {
    render(<PartsView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText('Cooper Standard')).toBeInTheDocument();
      expect(screen.getByText('Brose Closures')).toBeInTheDocument();
    });
  });

  it('displays revision tags', async () => {
    render(<PartsView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText('A.2')).toBeInTheDocument();
      expect(screen.getByText('B.0')).toBeInTheDocument();
    });
  });

  it('displays safety critical badge for critical parts', async () => {
    render(<PartsView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText('安全关键件')).toBeInTheDocument();
    });
  });

  it('displays part weights', async () => {
    render(<PartsView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText('1.25 kg')).toBeInTheDocument();
      expect(screen.getByText('2.4 kg')).toBeInTheDocument();
    });
  });

  it('opens add part modal on button click', async () => {
    render(<PartsView programs={mockPrograms} />);
    const addBtn = screen.getByText('录入新零件');
    fireEvent.click(addBtn);
    expect(screen.getByText('录入新研发零部件')).toBeInTheDocument();
  });

  it('filters parts by subsystem', async () => {
    render(<PartsView programs={mockPrograms} />);
    const subSelect = screen.getByDisplayValue('全部工程子系统');
    fireEvent.change(subSelect, { target: { value: 'Primary Body Seal' } });

    await waitFor(() => {
      expect(api.getParts).toHaveBeenCalledWith(expect.objectContaining({
        subsystem: 'Primary Body Seal'
      }));
    });
  });

  it('searches parts by text query', async () => {
    render(<PartsView programs={mockPrograms} />);
    const searchInput = screen.getByPlaceholderText('搜索件号/名称/供应商...');
    fireEvent.change(searchInput, { target: { value: 'Weatherstrip' } });

    await waitFor(() => {
      expect(api.getParts).toHaveBeenCalledWith(expect.objectContaining({
        search: 'Weatherstrip'
      }));
    });
  });

  it('renders empty table when no parts returned', async () => {
    vi.spyOn(api, 'getParts').mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      pages: 1
    });
    render(<PartsView programs={mockPrograms} />);
    await waitFor(() => {
      expect(screen.getByText('无符合条件的零部件记录')).toBeInTheDocument();
    });
  });
});
