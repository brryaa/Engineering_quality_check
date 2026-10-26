// Frontend TypeScript Types mirroring FastAPI schemas

export interface PaginatedResponse<T> {
  items: T[];
  total: int;
  page: number;
  page_size: number;
  pages: number;
}

export type int = number;

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: 'admin' | 'quality_lead' | 'design_engineer' | 'viewer';
  department: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
  user: User;
}

export interface Program {
  id: number;
  code: string;
  name: string;
  platform: string;
  phase: string;
  sop_date?: string;
  lead_engineer: string;
  quality_manager: string;
  target_market: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface Part {
  id: number;
  program_id: number;
  program_code?: string;
  part_number: string;
  name: string;
  subsystem: string;
  category: string;
  supplier: string;
  material: string;
  revision: string;
  weight_kg: number;
  safety_critical: boolean;
  created_at: string;
  updated_at: string;
}

export interface DFMEA {
  id: number;
  part_id: number;
  part_number?: string;
  fmea_code: string;
  item_function: string;
  failure_mode: string;
  failure_effect: string;
  severity: number;
  cause_mechanism: string;
  occurrence: number;
  prevention_control: string;
  detection_control: string;
  detection: number;
  rpn: number;
  action_priority: 'High' | 'Medium' | 'Low';
  recommended_action?: string;
  action_owner?: string;
  target_date?: string;
  action_status: string;
  post_severity?: number;
  post_occurrence?: number;
  post_detection?: number;
  post_rpn?: number;
  created_at: string;
  updated_at: string;
}

export interface DVPR {
  id: number;
  program_id: number;
  program_code?: string;
  part_id: number;
  part_number?: string;
  plan_code: string;
  test_phase: string;
  test_name: string;
  test_standard: string;
  acceptance_criteria: string;
  sample_size: number;
  test_facility: string;
  planned_start_date: string;
  planned_end_date: string;
  status: 'Planned' | 'In Progress' | 'Passed' | 'Failed' | 'Blocked';
  responsible_engineer: string;
  test_runs_count?: number;
  created_at: string;
  updated_at: string;
}

export interface TestRun {
  id: number;
  dvpr_id: number;
  plan_code?: string;
  test_name?: string;
  run_number: string;
  sample_id: string;
  test_date: string;
  test_facility: string;
  operator: string;
  temperature_c: number;
  humidity_rh: number;
  cycles_completed: number;
  measurement_data: string;
  result: 'Pass' | 'Fail' | 'Marginal';
  failure_summary?: string;
  report_file_url?: string;
  created_at: string;
  updated_at: string;
}

export interface EngineeringIssue {
  id: number;
  issue_code: string;
  program_id: number;
  program_code?: string;
  part_id: number;
  part_number?: string;
  test_run_id?: number;
  title: string;
  severity: 'S1-Critical' | 'S2-Major' | 'S3-Minor' | 'S4-Cosmetic';
  status: 'New' | 'Investigating' | 'Containment' | 'RootCauseVerified' | 'ActionImplemented' | 'ValidationPass' | 'Closed' | 'Rejected';
  description: string;
  occurrence_phase: string;
  containment_action?: string;
  assignee: string;
  reporter: string;
  due_date: string;
  closure_date?: string;
  has_root_cause?: boolean;
  created_at: string;
  updated_at: string;
}

export interface RootCauseAnalysis {
  id: number;
  issue_id: number;
  issue_code?: string;
  analysis_method: '5-Why' | 'Ishikawa-Fishbone' | 'FTA';
  direct_cause: string;
  why_1?: string;
  why_2?: string;
  why_3?: string;
  why_4?: string;
  why_5?: string;
  systemic_root_cause: string;
  fishbone_man?: string;
  fishbone_machine?: string;
  fishbone_material?: string;
  fishbone_method?: string;
  fishbone_measurement?: string;
  fishbone_environment?: string;
  verification_method: string;
  verification_result: 'Confirmed' | 'Rejected' | 'Pending';
  analyst: string;
  analyzed_at: string;
  created_at: string;
  updated_at: string;
}

export interface EngineeringChange {
  id: number;
  change_code: string;
  program_id: number;
  program_code?: string;
  part_id: number;
  part_number?: string;
  issue_id?: number;
  issue_code?: string;
  title: string;
  change_type: string;
  reason: string;
  pre_change_rev: string;
  post_change_rev: string;
  cost_impact_rmb: number;
  weight_impact_kg: number;
  tooling_lead_weeks: number;
  requires_homologation: boolean;
  requires_dvp_retest: boolean;
  approval_status: 'Draft' | 'Review-Eng' | 'Review-CostTooling' | 'Approved' | 'Rejected' | 'Implemented';
  initiator: string;
  approver?: string;
  approval_date?: string;
  implementation_date?: string;
  created_at: string;
  updated_at: string;
}

export interface SubsystemHealth {
  subsystem: string;
  total_issues: number;
  open_critical_issues: number;
  health_score: number;
}

export interface QualityDashboardStats {
  total_programs: number;
  total_parts: number;
  total_dfmeas: number;
  total_dvprs: number;
  total_test_runs: number;
  total_issues: number;
  total_changes: number;
  dfmea_high_ap_count: number;
  dfmea_medium_ap_count: number;
  dfmea_low_ap_count: number;
  dfmea_high_rpn_count: number;
  dvpr_status_counts: Record<string, number>;
  test_run_pass_rate_pct: number;
  test_run_result_counts: Record<string, number>;
  issue_severity_counts: Record<string, number>;
  issue_status_counts: Record<string, number>;
  open_critical_issues_count: number;
  total_change_cost_impact_rmb: number;
  changes_by_status: Record<string, number>;
  subsystem_health: SubsystemHealth[];
}

export interface KnowledgeItem {
  id: number;
  doc_code: string;
  title: string;
  subsystem: string;
  category: string;
  tags: string;
  content: string;
  keywords: string;
  source_reference?: string;
  applicable_programs?: string;
  author: string;
  created_at: string;
  updated_at: string;
}
