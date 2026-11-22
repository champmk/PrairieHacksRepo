// Types for backend/CONTRACT.md. Keep in sync with that file.

export type TermId = string; // '2026FA'
export type TermState = 'past' | 'current' | 'next' | 'future';
export type Day = 'M' | 'T' | 'W' | 'R' | 'F';

export type Prereq =
  | { course: string }
  | { all: Prereq[] }
  | { any: Prereq[] }
  | { coreq: string }
  | { consent: true }
  | null;

export interface Course {
  id: string;
  title: string;
  credits: number;
  department: string;
  division: string | null;
  level: number | null;
  offered: string[] | null;
  offered_note: string | null;
  prereq_text: string | null;
  prereq: Prereq;
  source_url?: string | null;
}

export interface Slot {
  id: string;
  label: string;
  kind: 'course' | 'choose';
  options: string[];
  route_term: number | null;
}

export interface Program {
  id: string;
  name: string;
  slots: Slot[];
  rules?: string[];
  source_url?: string | null;
}

export interface Catalog {
  catalog_year: string;
  courses: Course[];
  programs: Program[];
  divisions: Record<string, string>;
}

export interface StudentSummary {
  id: string;
  name: string;
  summary?: string;
}

export interface Enrollment {
  course: string;
  term: TermId | null;
  status: 'completed' | 'in_progress' | 'planned' | 'withdrawn' | 'failed' | 'dropped';
  grade: string | null;
  mode: 'letter' | 'sdf' | 'transfer';
}

export interface StudentTerm {
  id: TermId;
  label: string;
  state: TermState;
}

export interface Student {
  id: string;
  name: string;
  start_term: TermId;
  current_term: TermId;
  majors: string[];
  credit_cap: number;
  terms: StudentTerm[];
  enrollments: Enrollment[];
  schedule: Record<TermId, string[]>;
}

export interface Meeting {
  days: Day[];
  start: string;
  end: string;
  room?: string | null;
}

export interface Section {
  id: string;
  course: string;
  term: TermId;
  number: string;
  instructor: string;
  available: number;
  capacity: number;
  meetings: Meeting[];
}

export interface ScheduleResult {
  term: TermId;
  section_ids: string[];
  clashes: { a: string; b: string }[];
}

export type Edit =
  | { op: 'add'; term: TermId; course: string }
  | { op: 'remove'; term: TermId; tablet: string }
  | { op: 'swap'; term: TermId; tablet: string; course: string };

export type TabletStatus = 'completed' | 'not_counted' | 'in_progress' | 'planned' | 'projected' | 'open';

export interface Tablet {
  id: string;
  course: string | null;
  title: string | null;
  credits: number;
  status: TabletStatus;
  mark: string | null;
  required: boolean;
  locked: boolean;
  slot: { id: string; program: string; label: string; options: string[] } | null;
  counts_for: string[];
  warnings: string[];
}

export interface PlanTerm {
  id: TermId;
  label: string;
  season: 'Fall' | 'Spring';
  year: number;
  index: number;
  state: TermState;
  complete: boolean;
  credits: number;
  tablets: Tablet[];
}

export interface PlanEdge {
  id: string;
  from_tablet: string;
  from_term: TermId;
  to_term: TermId;
  kind: 'prereq' | 'coreq';
  missing: string[];
  message: string;
}

export interface PlanWarning {
  id: string;
  severity: 'warning' | 'error';
  code: string;
  message: string;
  term?: TermId | null;
  tablet?: string | null;
}

export interface Progress {
  program: string;
  name: string;
  total: number;
  done: number;
  in_progress: number;
  planned: number;
  slots: { id: string; label: string; status: TabletStatus; course: string | null; term: TermId | null }[];
}

export interface Plan {
  terms: PlanTerm[];
  prior: Tablet[]; // AP / transfer credit with no term
  edges: PlanEdge[];
  warnings: PlanWarning[];
  progress: Progress[];
  totals: {
    counted: number;
    in_progress: number;
    planned: number;
    open: number; // open elective tablets toward 124
    required: number;
    by_department: Record<string, number>;
    by_division: Record<string, number>;
  };
  unscheduled: { slot: string; label: string; reason: string }[];
}

export interface PlanRequest {
  student_id: string;
  majors: string[];
  credit_cap: number;
  edits: Edit[];
}

export interface OptionsResult {
  tablet: string | null;
  required: boolean;
  label: string;
  options: { course: string; title: string; credits: number; eligible: boolean; reason: string | null }[];
}
