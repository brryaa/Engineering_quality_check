import {
  Program, Part, DFMEA, DVPR, TestRun, EngineeringIssue,
  RootCauseAnalysis, EngineeringChange, QualityDashboardStats,
  KnowledgeItem, PaginatedResponse
} from '../types';

const BASE_URL = '/api/v1';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers
    },
    ...options
  });
  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const errorJson = await res.json();
      errorDetail = errorJson.detail || errorJson.error || errorDetail;
    } catch {
      // fallback to statusText
    }
    throw new Error(errorDetail);
  }
  if (res.status === 204) {
    return {} as T;
  }
  return res.json();
}

function buildQuery(params?: Record<string, any>): string {
  if (!params) return '';
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, val]) => {
    if (val !== undefined && val !== null && val !== '') {
      searchParams.append(key, String(val));
    }
  });
  const q = searchParams.toString();
  return q ? `?${q}` : '';
}

export const api = {
  // Module 1: Programs
  getPrograms: (params?: { page?: number; page_size?: number; search?: string; phase?: string; platform?: string; sort_by?: string; sort_order?: string }) =>
    fetchJson<PaginatedResponse<Program>>(`${BASE_URL}/programs${buildQuery(params)}`),
  getProgram: (id: number) => fetchJson<Program>(`${BASE_URL}/programs/${id}`),
  createProgram: (data: Partial<Program>) =>
    fetchJson<Program>(`${BASE_URL}/programs`, { method: 'POST', body: JSON.stringify(data) }),
  updateProgram: (id: number, data: Partial<Program>) =>
    fetchJson<Program>(`${BASE_URL}/programs/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteProgram: (id: number) =>
    fetchJson<void>(`${BASE_URL}/programs/${id}`, { method: 'DELETE' }),

  // Module 2: Parts
  getParts: (params?: { page?: number; page_size?: number; search?: string; program_id?: number; subsystem?: string; category?: string; safety_critical?: boolean; sort_by?: string; sort_order?: string }) =>
    fetchJson<PaginatedResponse<Part>>(`${BASE_URL}/parts${buildQuery(params)}`),
  getPart: (id: number) => fetchJson<Part>(`${BASE_URL}/parts/${id}`),
  createPart: (data: Partial<Part>) =>
    fetchJson<Part>(`${BASE_URL}/parts`, { method: 'POST', body: JSON.stringify(data) }),
  updatePart: (id: number, data: Partial<Part>) =>
    fetchJson<Part>(`${BASE_URL}/parts/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deletePart: (id: number) =>
    fetchJson<void>(`${BASE_URL}/parts/${id}`, { method: 'DELETE' }),

  // Module 3: DFMEA
  getDfmeas: (params?: { page?: number; page_size?: number; search?: string; part_id?: number; action_priority?: string; action_status?: string; min_rpn?: number; sort_by?: string; sort_order?: string }) =>
    fetchJson<PaginatedResponse<DFMEA>>(`${BASE_URL}/dfmea${buildQuery(params)}`),
  getDfmea: (id: number) => fetchJson<DFMEA>(`${BASE_URL}/dfmea/${id}`),
  createDfmea: (data: Partial<DFMEA>) =>
    fetchJson<DFMEA>(`${BASE_URL}/dfmea`, { method: 'POST', body: JSON.stringify(data) }),
  updateDfmea: (id: number, data: Partial<DFMEA>) =>
    fetchJson<DFMEA>(`${BASE_URL}/dfmea/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteDfmea: (id: number) =>
    fetchJson<void>(`${BASE_URL}/dfmea/${id}`, { method: 'DELETE' }),

  // Module 4: DVP&R
  getDvprs: (params?: { page?: number; page_size?: number; search?: string; program_id?: number; part_id?: number; test_phase?: string; status?: string; sort_by?: string; sort_order?: string }) =>
    fetchJson<PaginatedResponse<DVPR>>(`${BASE_URL}/dvpr${buildQuery(params)}`),
  getDvpr: (id: number) => fetchJson<DVPR>(`${BASE_URL}/dvpr/${id}`),
  createDvpr: (data: Partial<DVPR>) =>
    fetchJson<DVPR>(`${BASE_URL}/dvpr`, { method: 'POST', body: JSON.stringify(data) }),
  updateDvpr: (id: number, data: Partial<DVPR>) =>
    fetchJson<DVPR>(`${BASE_URL}/dvpr/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteDvpr: (id: number) =>
    fetchJson<void>(`${BASE_URL}/dvpr/${id}`, { method: 'DELETE' }),

  // Module 5: Tests
  getTestRuns: (params?: { page?: number; page_size?: number; search?: string; dvpr_id?: number; result?: string; sort_by?: string; sort_order?: string }) =>
    fetchJson<PaginatedResponse<TestRun>>(`${BASE_URL}/tests${buildQuery(params)}`),
  getTestRun: (id: number) => fetchJson<TestRun>(`${BASE_URL}/tests/${id}`),
  createTestRun: (data: Partial<TestRun>) =>
    fetchJson<TestRun>(`${BASE_URL}/tests`, { method: 'POST', body: JSON.stringify(data) }),
  updateTestRun: (id: number, data: Partial<TestRun>) =>
    fetchJson<TestRun>(`${BASE_URL}/tests/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteTestRun: (id: number) =>
    fetchJson<void>(`${BASE_URL}/tests/${id}`, { method: 'DELETE' }),

  // Module 6: Issues
  getIssues: (params?: { page?: number; page_size?: number; search?: string; program_id?: number; part_id?: number; severity?: string; status?: string; sort_by?: string; sort_order?: string }) =>
    fetchJson<PaginatedResponse<EngineeringIssue>>(`${BASE_URL}/issues${buildQuery(params)}`),
  getIssue: (id: number) => fetchJson<EngineeringIssue>(`${BASE_URL}/issues/${id}`),
  createIssue: (data: Partial<EngineeringIssue>) =>
    fetchJson<EngineeringIssue>(`${BASE_URL}/issues`, { method: 'POST', body: JSON.stringify(data) }),
  updateIssue: (id: number, data: Partial<EngineeringIssue>) =>
    fetchJson<EngineeringIssue>(`${BASE_URL}/issues/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteIssue: (id: number) =>
    fetchJson<void>(`${BASE_URL}/issues/${id}`, { method: 'DELETE' }),

  // Module 7: Root Cause
  getRootCauses: (params?: { page?: number; page_size?: number; issue_id?: number; analysis_method?: string; verification_result?: string }) =>
    fetchJson<PaginatedResponse<RootCauseAnalysis>>(`${BASE_URL}/root-cause${buildQuery(params)}`),
  getRootCause: (id: number) => fetchJson<RootCauseAnalysis>(`${BASE_URL}/root-cause/${id}`),
  getRootCauseByIssue: (issueId: number) => fetchJson<RootCauseAnalysis>(`${BASE_URL}/root-cause/by-issue/${issueId}`),
  createRootCause: (data: Partial<RootCauseAnalysis>) =>
    fetchJson<RootCauseAnalysis>(`${BASE_URL}/root-cause`, { method: 'POST', body: JSON.stringify(data) }),
  updateRootCause: (id: number, data: Partial<RootCauseAnalysis>) =>
    fetchJson<RootCauseAnalysis>(`${BASE_URL}/root-cause/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteRootCause: (id: number) =>
    fetchJson<void>(`${BASE_URL}/root-cause/${id}`, { method: 'DELETE' }),

  // Module 8: Changes
  getChanges: (params?: { page?: number; page_size?: number; search?: string; program_id?: number; part_id?: number; approval_status?: string; change_type?: string }) =>
    fetchJson<PaginatedResponse<EngineeringChange>>(`${BASE_URL}/changes${buildQuery(params)}`),
  getChange: (id: number) => fetchJson<EngineeringChange>(`${BASE_URL}/changes/${id}`),
  createChange: (data: Partial<EngineeringChange>) =>
    fetchJson<EngineeringChange>(`${BASE_URL}/changes`, { method: 'POST', body: JSON.stringify(data) }),
  updateChange: (id: number, data: Partial<EngineeringChange>) =>
    fetchJson<EngineeringChange>(`${BASE_URL}/changes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteChange: (id: number) =>
    fetchJson<void>(`${BASE_URL}/changes/${id}`, { method: 'DELETE' }),

  // Module 9: Dashboard
  getDashboardStats: (programId?: number) =>
    fetchJson<QualityDashboardStats>(`${BASE_URL}/dashboard/stats${buildQuery({ program_id: programId })}`),

  // Module 10: Knowledge
  getKnowledgeItems: (params?: { page?: number; page_size?: number; search?: string; subsystem?: string; category?: string; tag?: string }) =>
    fetchJson<PaginatedResponse<KnowledgeItem>>(`${BASE_URL}/knowledge${buildQuery(params)}`),
  getKnowledgeItem: (id: number) => fetchJson<KnowledgeItem>(`${BASE_URL}/knowledge/${id}`),
  createKnowledgeItem: (data: Partial<KnowledgeItem>) =>
    fetchJson<KnowledgeItem>(`${BASE_URL}/knowledge`, { method: 'POST', body: JSON.stringify(data) }),
  updateKnowledgeItem: (id: number, data: Partial<KnowledgeItem>) =>
    fetchJson<KnowledgeItem>(`${BASE_URL}/knowledge/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteKnowledgeItem: (id: number) =>
    fetchJson<void>(`${BASE_URL}/knowledge/${id}`, { method: 'DELETE' }),
};
