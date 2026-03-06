// Core types matching backend Pydantic schemas

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'admin' | 'pm' | 'viewer';
  org_id: string;
}

export interface Project {
  id: string;
  site_name: string;
  site_number: string | null;
  carrier: string;
  market: string | null;
  state: string | null;
  scope_type: string | null;
  tower_type: string | null;
  status: ProjectStatus;
  ntp_date: string | null;
  target_completion: string | null;
  total_budget: number | null;
  total_actual: number | null;
  created_at: string;
}

export type ProjectStatus =
  | 'pre_construction'
  | 'active'
  | 'in_progress'
  | 'punch_list'
  | 'closeout'
  | 'complete'
  | 'on_hold';

export interface BudgetLine {
  id: string;
  category: string;
  description: string | null;
  budgeted_amount: number;
  actual_amount: number;
}

export interface TimeEntry {
  id: string;
  project_id: string;
  crew_member_id: string | null;
  work_date: string;
  hours: number;
  overtime_hours: number;
  source_platform: string;
  labor_cost: number | null;
}

export interface DashboardStats {
  total_projects: number;
  active_projects: number;
  total_budget: number;
  total_actual: number;
  over_budget_count: number;
  on_track_count: number;
}

export interface ProjectSummary {
  id: string;
  site_name: string;
  carrier: string;
  status: string;
  total_budget: number;
  total_actual: number;
  budget_pct: number;
  days_active: number | null;
}

// Carrier constants
export const CARRIERS = ['AT&T', 'Verizon', 'T-Mobile', 'L3Harris', 'DISH', 'Other'] as const;

export const STATUS_LABELS: Record<ProjectStatus, string> = {
  pre_construction: 'Pre-Construction',
  active: 'Idle (5d+)',
  in_progress: 'In Construction',
  punch_list: 'Punch List',
  closeout: 'Closeout',
  complete: 'Complete',
  on_hold: 'On Hold',
};

export const BUDGET_CATEGORIES = [
  'tower_labor',
  'civil',
  'electrical',
  'materials',
  'travel_per_diem',
  'equipment_crane',
  'subcontractor',
  'rigging',
  'other',
] as const;

export const CATEGORY_LABELS: Record<string, string> = {
  tower_labor: 'Tower Labor',
  civil: 'Civil / Ground',
  electrical: 'Electrical',
  materials: 'Materials',
  travel_per_diem: 'Travel / Per Diem',
  equipment_crane: 'Equipment / Crane',
  subcontractor: 'Subcontractor',
  rigging: 'Rigging',
  other: 'Other',
};
