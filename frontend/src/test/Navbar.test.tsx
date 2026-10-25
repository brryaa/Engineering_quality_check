import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Navbar } from '../components/Navbar';
import { Program } from '../types';

const mockPrograms: Program[] = [
  {
    id: 1,
    code: 'P-EP32',
    name: 'Aurora EV SUV',
    platform: 'EV-800V',
    phase: 'Proto-A',
    lead_engineer: 'Dr. Wei Chen',
    quality_manager: 'Ying Zhao',
    target_market: 'Global',
    created_at: '2026-01-01',
    updated_at: '2026-01-01'
  }
];

describe('Navbar Component', () => {
  it('renders branding title and navigation tabs', () => {
    const onSelectTab = vi.fn();
    const onSelectProgram = vi.fn();

    render(
      <Navbar
        activeTab="dashboard"
        onSelectTab={onSelectTab}
        programs={mockPrograms}
        onSelectProgram={onSelectProgram}
      />
    );

    expect(screen.getByText(/汽车研发工程质量管理平台/i)).toBeInTheDocument();
    expect(screen.getByText('质量总览')).toBeInTheDocument();
    expect(screen.getByText('DFMEA风险')).toBeInTheDocument();
    expect(screen.getByText('5-Why分析')).toBeInTheDocument();

    // Click on a tab
    fireEvent.click(screen.getByText('DFMEA风险'));
    expect(onSelectTab).toHaveBeenCalledWith('dfmea');
  });

  it('handles program filter change', () => {
    const onSelectTab = vi.fn();
    const onSelectProgram = vi.fn();

    render(
      <Navbar
        activeTab="dashboard"
        onSelectTab={onSelectTab}
        programs={mockPrograms}
        onSelectProgram={onSelectProgram}
      />
    );

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: '1' } });
    expect(onSelectProgram).toHaveBeenCalledWith(1);
  });
});
