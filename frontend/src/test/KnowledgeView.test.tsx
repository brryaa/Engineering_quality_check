import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { KnowledgeView } from '../views/KnowledgeView';
import { api } from '../api/client';
import { KnowledgeItem, PaginatedResponse } from '../types';

const mockKnowledge: KnowledgeItem[] = [
  {
    id: 1,
    doc_code: 'KB-SEAL-001',
    title: 'Frameless Door Glass Run Sealing & Dynamic Wind Noise Design Guidelines',
    subsystem: 'Frameless Window System',
    category: 'Design Guideline',
    tags: 'frameless,wind-noise,EPDM,sealing',
    content: 'When designing frameless window glass guide systems, B-pillar outward suction force must be calculated at v=160km/h. Guide channel lateral compliance must not exceed 0.8 mm under 500 N load.',
    keywords: 'frameless, aeroacoustic, wind noise, guide channel',
    author: 'Chief Aerodynamics Specialist',
    created_at: '2026-10-01T08:00:00Z',
    updated_at: '2026-10-01T08:00:00Z'
  },
  {
    id: 2,
    doc_code: 'KB-MOTOR-002',
    title: 'Cold Weather Window Anti-Pinch False Trigger Prevention and Calibration',
    subsystem: 'Glass Regulator Module',
    category: 'Lessons Learned',
    tags: 'anti-pinch,cold-temperature,current-spike,calibration',
    content: 'At temperatures below -20C, glass run channel rubber hardness increases by 25 Shore A points. The motor ECU anti-pinch ripple count threshold must incorporate thermal compensation mapping.',
    keywords: 'anti-pinch, motor stall, cold climate, FMVSS 118',
    author: 'Electronics Quality Lead',
    created_at: '2026-10-05T08:00:00Z',
    updated_at: '2026-10-05T08:00:00Z'
  }
];

const mockPaginatedKnowledge: PaginatedResponse<KnowledgeItem> = {
  items: mockKnowledge,
  total: 2,
  page: 1,
  page_size: 20,
  pages: 1
};

describe('KnowledgeView Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(api, 'getKnowledgeItems').mockResolvedValue(mockPaginatedKnowledge);
    vi.spyOn(api, 'createKnowledgeItem').mockResolvedValue(mockKnowledge[0]);
  });

  it('renders knowledge base title and counter', async () => {
    render(<KnowledgeView />);
    await waitFor(() => {
      expect(screen.getByText(/工程知识与历史经验库检索/)).toBeInTheDocument();
      expect(screen.getByText(/2 篇/)).toBeInTheDocument();
    });
  });

  it('renders document codes', async () => {
    render(<KnowledgeView />);
    await waitFor(() => {
      expect(screen.getByText('KB-SEAL-001')).toBeInTheDocument();
      expect(screen.getByText('KB-MOTOR-002')).toBeInTheDocument();
    });
  });

  it('renders article titles', async () => {
    render(<KnowledgeView />);
    await waitFor(() => {
      expect(screen.getByText(/Frameless Door Glass Run Sealing/)).toBeInTheDocument();
      expect(screen.getByText(/Cold Weather Window Anti-Pinch/)).toBeInTheDocument();
    });
  });

  it('displays category badges', async () => {
    render(<KnowledgeView />);
    await waitFor(() => {
      expect(screen.getByText('Design Guideline')).toBeInTheDocument();
      expect(screen.getByText('Lessons Learned')).toBeInTheDocument();
    });
  });

  it('displays subsystem badges', async () => {
    render(<KnowledgeView />);
    await waitFor(() => {
      expect(screen.getByText('Frameless Window System')).toBeInTheDocument();
      expect(screen.getByText('Glass Regulator Module')).toBeInTheDocument();
    });
  });

  it('displays authors', async () => {
    render(<KnowledgeView />);
    await waitFor(() => {
      expect(screen.getByText(/Chief Aerodynamics Specialist/)).toBeInTheDocument();
      expect(screen.getByText(/Electronics Quality Lead/)).toBeInTheDocument();
    });
  });

  it('displays technical tags', async () => {
    render(<KnowledgeView />);
    await waitFor(() => {
      expect(screen.getByText('#frameless')).toBeInTheDocument();
      expect(screen.getByText('#anti-pinch')).toBeInTheDocument();
    });
  });

  it('filters knowledge articles by category', async () => {
    render(<KnowledgeView />);
    const catSelect = screen.getByDisplayValue('全部知识类型');
    fireEvent.change(catSelect, { target: { value: 'Design-Guideline' } });

    await waitFor(() => {
      expect(api.getKnowledgeItems).toHaveBeenCalledWith(expect.objectContaining({
        category: 'Design-Guideline'
      }));
    });
  });

  it('filters knowledge articles by alternate category', async () => {
    render(<KnowledgeView />);
    const catSelect = screen.getByDisplayValue('全部知识类型');
    fireEvent.change(catSelect, { target: { value: 'Lesson-Learned' } });

    await waitFor(() => {
      expect(api.getKnowledgeItems).toHaveBeenCalledWith(expect.objectContaining({
        category: 'Lesson-Learned'
      }));
    });
  });

  it('searches knowledge articles by query input', async () => {
    render(<KnowledgeView />);
    const searchInput = screen.getByPlaceholderText('全文字符检索 (如: 漏水 / 防夹 / 铰链 / EPDM)...');
    fireEvent.change(searchInput, { target: { value: 'aerodynamics' } });

    await waitFor(() => {
      expect(api.getKnowledgeItems).toHaveBeenCalledWith(expect.objectContaining({
        search: 'aerodynamics'
      }));
    });
  });

  it('expands article card to read full content', async () => {
    render(<KnowledgeView />);
    await waitFor(() => {
      const readMoreBtns = screen.getAllByText('展开全文阅读');
      fireEvent.click(readMoreBtns[0]);
    });

    await waitFor(() => {
      expect(screen.getByText('收起详情')).toBeInTheDocument();
    });
  });

  it('opens add knowledge modal', async () => {
    render(<KnowledgeView />);
    fireEvent.click(screen.getByText('沉淀工程知识'));
    expect(screen.getByText('沉淀工程知识与设计准则')).toBeInTheDocument();
  });
});
