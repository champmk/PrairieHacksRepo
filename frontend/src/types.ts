// Shared domain types. These mirror the endpoint contract in
// docs/CourseGraph_High_Level_Design.md so the mock API can be swapped
// for the real backend without touching components.

export type Season = 'Fall' | 'Spring';
export type TermId = string; // e.g. '2025FA', '2026SP'

export interface Term {
  id: TermId;
  season: Season;
  year: number;
  label: string; // 'Fall 2025'
}

export type PrereqRule =
  | { kind: 'course'; id: string }
  | { kind: 'all'; rules: PrereqRule[] }
  | { kind: 'any'; rules: PrereqRule[] };

export interface Course {
  id: string; // 'CSC-151'
  subject: string; // 'CSC'
  number: string; // '151'
  title: string;
  credits: number;
  offered: Season[];
  prereq?: PrereqRule;
}

export type Requirement =
  | { id: string; label: string; kind: 'course'; courseId: string }
  | { id: string; label: string; kind: 'choose'; count: number; options: string[] };

export interface Program {
  id: string; // 'CS' | 'MATH'
  name: string;
  requirements: Requirement[];
}

export type Day = 'M' | 'T' | 'W' | 'R' | 'F';

export interface Meeting {
  days: Day[];
  start: string; // '08:00' 24h
  end: string; // '09:20'
  room?: string;
}

export interface Section {
  id: string;
  courseId: string;
  term: TermId;
  number: string; // '01'
  instructor: string;
  available: number;
  capacity: number;
  meetings: Meeting[];
}

export type CreditSource = 'grinnell' | 'ap' | 'transfer';

export interface CreditRecord {
  courseId: string;
  source: CreditSource;
  // Term taken at Grinnell; omitted for AP / transfer credit.
  term?: TermId;
  status: 'completed' | 'enrolled';
  note?: string; // 'AP Calculus BC, score 5'
}

export interface StudentProfile {
  name: string;
  majors: string[]; // program ids, at most 2
  credits: CreditRecord[];
  startTerm: TermId; // first semester at Grinnell
  currentTerm: TermId; // term in progress
  creditCap: number; // max credits per term
  // Courses the student placed by hand (added, dragged, or chosen).
  placements: Record<string, TermId>; // courseId -> term
  // Courses the student removed from the auto plan (non-required only).
  dismissed: string[];
  // Sections picked on the schedule page, per term.
  schedule: Record<TermId, string[]>; // term -> section ids
}

// ---- Planner output (POST /recalculate) -------------------------------

export type ItemStatus = 'completed' | 'enrolled' | 'planned' | 'unsatisfied';

export interface PlanSlot {
  programId: string;
  requirementId: string;
  label: string; // 'CS elective'
  options: string[]; // course ids still eligible to fill the slot
}

export interface PlanItem {
  key: string; // stable across recalculations
  courseId?: string; // undefined for an unfilled slot
  slot?: PlanSlot; // set when the item fills (or awaits) a choose-N slot
  status: ItemStatus;
  reason?: string; // why unsatisfied, e.g. 'Needs CSC-207 first'
  pinned: boolean; // placed by the student
  satisfies: string[]; // requirement labels this item counts toward
}

export interface PlanTerm {
  term: Term;
  items: PlanItem[];
  credits: number;
}

export interface ProgramProgress {
  programId: string;
  name: string;
  total: number; // requirement units (a choose-2 counts as 2)
  completed: number;
  planned: number;
  requirements: {
    id: string;
    label: string;
    status: ItemStatus;
    termId?: TermId;
    courseId?: string;
  }[];
}

export interface PlanResult {
  prior: PlanItem[]; // AP / transfer credit, no term
  terms: PlanTerm[];
  unscheduled: PlanItem[]; // requirements that did not fit in eight terms
  progress: ProgramProgress[];
  totalCredits: { earned: number; planned: number; required: number };
  changes: string[]; // human-readable diff against the previous plan
}
