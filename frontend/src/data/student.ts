// A fictional demo student. No real records.
import type { StudentProfile } from '../types.ts';

export const DEMO_STUDENT: StudentProfile = {
  name: 'Alex Rivera',
  majors: [],
  credits: [
    { courseId: 'MAT-131', source: 'ap', status: 'completed', note: 'AP Calculus BC, score 5' },
    { courseId: 'TUT-100', source: 'grinnell', term: '2025FA', status: 'completed' },
    { courseId: 'CSC-151', source: 'grinnell', term: '2025FA', status: 'completed' },
    { courseId: 'MAT-133', source: 'grinnell', term: '2025FA', status: 'completed' },
    { courseId: 'PSY-113', source: 'grinnell', term: '2025FA', status: 'completed' },
    { courseId: 'CSC-161', source: 'grinnell', term: '2026SP', status: 'completed' },
    { courseId: 'MAT-215', source: 'grinnell', term: '2026SP', status: 'completed' },
    { courseId: 'ENG-120', source: 'grinnell', term: '2026SP', status: 'completed' },
    { courseId: 'MUS-101', source: 'grinnell', term: '2026SP', status: 'completed' },
    { courseId: 'CSC-208', source: 'grinnell', term: '2026FA', status: 'enrolled' },
    { courseId: 'FMS-155', source: 'grinnell', term: '2026FA', status: 'enrolled' },
    { courseId: 'STA-209', source: 'grinnell', term: '2026FA', status: 'enrolled' },
    { courseId: 'MUS-120', source: 'grinnell', term: '2026FA', status: 'enrolled' },
  ],
  startTerm: '2025FA',
  currentTerm: '2026FA',
  creditCap: 16,
  placements: {},
  dismissed: [],
  schedule: {
    '2026FA': ['2026FA-CSC-208-01', '2026FA-FMS-155-03', '2026FA-STA-209-06', '2026FA-MUS-120-02'],
  },
};
