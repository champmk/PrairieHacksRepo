// Mock API. Each function stands in for an endpoint in the design doc
// (docs/CourseGraph_High_Level_Design.md). Swap the bodies for fetch()
// calls when the backend is ready; components only import from here.
import { COURSES, COURSE_BY_ID, PROGRAMS, PROGRAM_BY_ID, TERMS, TERM_BY_ID } from '../data/catalog.ts';
import { SECTIONS, SECTION_BY_ID } from '../data/sections.ts';
import { DEMO_STUDENT } from '../data/student.ts';
import { recalculate as runPlanner } from '../engine/planner.ts';
import type { PlanResult, StudentProfile, TermId } from '../types.ts';

export const api = {
  // GET /programs
  programs: () => PROGRAMS,
  program: (id: string) => PROGRAM_BY_ID[id],
  // GET /courses
  courses: () => COURSES,
  course: (id: string) => COURSE_BY_ID[id],
  terms: () => TERMS,
  term: (id: TermId) => TERM_BY_ID[id],
  // GET /sections?term=  (shape follows the teammate's normalized Section model)
  sections: (term: TermId) => SECTIONS.filter((s) => s.term === term),
  section: (id: string) => SECTION_BY_ID[id],
  // GET /demo-profile — stands in for importing completed and transfer credit
  async importCredits(): Promise<StudentProfile> {
    await new Promise((r) => setTimeout(r, 1100));
    return structuredClone(DEMO_STUDENT);
  },
  // POST /recalculate
  recalculate: (profile: StudentProfile, previous?: PlanResult): PlanResult => runPlanner(profile, previous),
};
