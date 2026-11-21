// SAMPLE DATA for design and flow only. Course titles, prerequisites,
// offerings and major requirements here are illustrative, not official
// Grinnell rules. The backend replaces this with the cited catalog.
import type { Course, PrereqRule, Program, Season, Term } from '../types.ts';

const c = (id: string): PrereqRule => ({ kind: 'course', id });
const all = (...rules: PrereqRule[]): PrereqRule => ({ kind: 'all', rules });
const any = (...rules: PrereqRule[]): PrereqRule => ({ kind: 'any', rules });
const BOTH: Season[] = ['Fall', 'Spring'];
const FALL: Season[] = ['Fall'];
const SPRING: Season[] = ['Spring'];

function course(id: string, title: string, offered: Season[], prereq?: PrereqRule, credits = 4): Course {
  const [subject, number] = id.split('-');
  return { id, subject, number, title, credits, offered, prereq };
}

const DISCRETE = any(c('CSC-208'), c('MAT-208'));

export const COURSES: Course[] = [
  // Computer Science
  course('CSC-151', 'Functional Problem Solving', BOTH),
  course('CSC-161', 'Imperative Problem Solving', BOTH, c('CSC-151')),
  course('CSC-207', 'Object-Oriented Problem Solving', BOTH, c('CSC-161')),
  course('CSC-208', 'Discrete Structures', BOTH, c('CSC-151')),
  course('CSC-211', 'Computer Organization', BOTH, c('CSC-161')),
  course('CSC-213', 'Operating Systems', SPRING, all(c('CSC-211'), c('CSC-207'))),
  course('CSC-301', 'Analysis of Algorithms', FALL, all(c('CSC-207'), DISCRETE)),
  course('CSC-312', 'Programming Language Implementation', FALL, c('CSC-207')),
  course('CSC-321', 'Software Development Principles', FALL, c('CSC-207')),
  course('CSC-322', 'Team Software Development', SPRING, c('CSC-321')),
  course('CSC-324', 'Software Design and Development', FALL, c('CSC-207')),
  course('CSC-341', 'Automata and Complexity', SPRING, all(c('CSC-207'), DISCRETE)),
  course('CSC-364', 'Computer Networks', SPRING, c('CSC-213')),
  course('CSC-395', 'Topics: Machine Learning', SPRING, all(c('CSC-207'), c('MAT-215'))),
  // Mathematics
  course('MAT-131', 'Calculus I', BOTH),
  course('MAT-133', 'Calculus II', BOTH, c('MAT-131')),
  course('MAT-208', 'Discrete Bridges to Advanced Math', BOTH, c('MAT-131')),
  course('MAT-215', 'Linear Algebra', BOTH, c('MAT-133')),
  course('MAT-218', 'Combinatorics', SPRING, c('MAT-215')),
  course('MAT-220', 'Differential Equations', FALL, c('MAT-215')),
  course('MAT-306', 'Mathematical Modeling', FALL, c('MAT-215')),
  course('MAT-316', 'Foundations of Analysis', FALL, all(c('MAT-215'), DISCRETE)),
  course('MAT-321', 'Foundations of Abstract Algebra', SPRING, all(c('MAT-215'), DISCRETE)),
  course('MAT-335', 'Probability and Statistics I', FALL, c('MAT-133')),
  course('MAT-336', 'Probability and Statistics II', SPRING, c('MAT-335')),
  course('MAT-444', 'Senior Seminar', SPRING, any(c('MAT-316'), c('MAT-321'))),
  // Across the curriculum
  course('TUT-100', 'First-Year Tutorial', FALL),
  course('ANT-104', 'Anthropological Inquiry', BOTH),
  course('ART-111', 'Introduction to the Studio', BOTH),
  course('BIO-150', 'Introduction to Biological Inquiry', BOTH),
  course('CHM-129', 'General Chemistry', FALL),
  course('ECN-111', 'Introduction to Economics', BOTH),
  course('EDU-101', 'Educational Principles', BOTH),
  course('ENG-120', 'Literary Analysis', BOTH),
  course('FMS-155', 'Introduction to Film Studies', BOTH),
  course('GDS-111', 'Introduction to Gender Studies', BOTH),
  course('HIS-100', 'Historical Methods', BOTH),
  course('MUS-101', 'Fundamentals of Music', BOTH),
  course('MUS-120', 'Performance Ensemble', BOTH, undefined, 1),
  course('PHI-101', 'Introduction to Philosophy', BOTH),
  course('PHY-131', 'General Physics I', FALL, c('MAT-131')),
  course('POL-101', 'Introduction to Political Science', BOTH),
  course('PSY-113', 'Introduction to Psychology', BOTH),
  course('SOC-111', 'Introduction to Sociology', BOTH),
  course('SPN-101', 'Introductory Spanish I', FALL),
  course('SPN-102', 'Introductory Spanish II', SPRING, c('SPN-101')),
  course('STA-209', 'Applied Statistics', BOTH),
];

export const COURSE_BY_ID: Record<string, Course> = Object.fromEntries(COURSES.map((x) => [x.id, x]));

const req = (programId: string, courseId: string) => ({
  id: `${programId}:${courseId}`,
  label: courseId.replace('-', ' '),
  kind: 'course' as const,
  courseId,
});

export const PROGRAMS: Program[] = [
  {
    id: 'CS',
    name: 'Computer Science',
    requirements: [
      req('CS', 'MAT-131'),
      req('CS', 'CSC-151'),
      req('CS', 'CSC-161'),
      req('CS', 'CSC-207'),
      { id: 'CS:discrete', label: 'Discrete math', kind: 'choose', count: 1, options: ['CSC-208', 'MAT-208'] },
      req('CS', 'CSC-211'),
      req('CS', 'CSC-213'),
      req('CS', 'CSC-301'),
      req('CS', 'CSC-324'),
      req('CS', 'CSC-341'),
      {
        id: 'CS:elective',
        label: 'CS elective',
        kind: 'choose',
        count: 2,
        options: ['CSC-312', 'CSC-321', 'CSC-322', 'CSC-364', 'CSC-395'],
      },
    ],
  },
  {
    id: 'MATH',
    name: 'Mathematics',
    requirements: [
      req('MATH', 'MAT-131'),
      req('MATH', 'MAT-133'),
      req('MATH', 'MAT-215'),
      { id: 'MATH:proofs', label: 'Proofs course', kind: 'choose', count: 1, options: ['MAT-208', 'CSC-208'] },
      req('MATH', 'MAT-218'),
      req('MATH', 'MAT-316'),
      req('MATH', 'MAT-321'),
      {
        id: 'MATH:elective',
        label: 'Math elective',
        kind: 'choose',
        count: 2,
        options: ['MAT-220', 'MAT-306', 'MAT-335', 'MAT-336', 'MAT-444'],
      },
    ],
  },
];

export const PROGRAM_BY_ID: Record<string, Program> = Object.fromEntries(PROGRAMS.map((p) => [p.id, p]));

// Majors shown in onboarding. Only CS and Math have sample requirements.
export const MAJOR_CHOICES: { id: string; name: string; available: boolean }[] = [
  { id: 'CS', name: 'Computer Science', available: true },
  { id: 'MATH', name: 'Mathematics', available: true },
  { id: 'ECN', name: 'Economics', available: false },
  { id: 'PSY', name: 'Psychology', available: false },
  { id: 'BIO', name: 'Biology', available: false },
];

function term(year: number, season: Season): Term {
  return { id: `${year}${season === 'Fall' ? 'FA' : 'SP'}`, season, year, label: `${season} ${year}` };
}

// Eight semesters: Fall 2025 through Spring 2029.
export const TERMS: Term[] = [
  term(2025, 'Fall'),
  term(2026, 'Spring'),
  term(2026, 'Fall'),
  term(2027, 'Spring'),
  term(2027, 'Fall'),
  term(2028, 'Spring'),
  term(2028, 'Fall'),
  term(2029, 'Spring'),
];

export const TERM_BY_ID: Record<string, Term> = Object.fromEntries(TERMS.map((t) => [t.id, t]));

export const DEGREE_CREDITS = 124;
