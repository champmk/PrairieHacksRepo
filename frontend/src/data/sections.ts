// SAMPLE section times for the schedule page. The two CSC-151 sections
// for Spring 2027 follow the example captured in
// docs/backend/examples/ellucian_master_developer_reference.py; the rest
// are placeholders until the backend serves real sections.
import type { Day, Meeting, Section, TermId } from '../types.ts';

const MWF: Day[] = ['M', 'W', 'F'];
const TR: Day[] = ['T', 'R'];

const SLOTS: Record<string, Meeting> = {
  mwf8: { days: MWF, start: '08:00', end: '08:50' },
  mwf9: { days: MWF, start: '09:00', end: '09:50' },
  mwf10: { days: MWF, start: '10:00', end: '10:50' },
  mwf11: { days: MWF, start: '11:00', end: '11:50' },
  mwf1: { days: MWF, start: '13:00', end: '13:50' },
  mwf2: { days: MWF, start: '14:00', end: '14:50' },
  mwf3: { days: MWF, start: '15:00', end: '15:50' },
  tr8: { days: TR, start: '08:00', end: '09:20' },
  tr930: { days: TR, start: '09:30', end: '10:50' },
  tr11: { days: TR, start: '11:00', end: '12:20' },
  tr1: { days: TR, start: '13:00', end: '14:20' },
  tr230: { days: TR, start: '14:30', end: '15:50' },
  m7: { days: ['M'], start: '19:00', end: '20:20' },
};

function seats(seed: string): { available: number; capacity: number } {
  let h = 0;
  for (const ch of seed) h = (h * 31 + ch.charCodeAt(0)) % 997;
  const capacity = [16, 20, 24, 28][h % 4];
  return { available: h % (capacity + 1), capacity };
}

function sec(term: TermId, courseId: string, number: string, slot: string, instructor = 'Staff'): Section {
  return {
    id: `${term}-${courseId}-${number}`,
    courseId,
    term,
    number,
    instructor,
    ...seats(`${term}${courseId}${number}`),
    meetings: [SLOTS[slot]],
  };
}

const SP27 = '2027SP';
const FA26 = '2026FA';

export const SECTIONS: Section[] = [
  // Spring 2027 — the term students schedule next
  {
    id: `${SP27}-CSC-151-01`,
    courseId: 'CSC-151',
    term: SP27,
    number: '01',
    instructor: 'Samuel Rebelsky',
    available: 10,
    capacity: 24,
    meetings: [{ days: MWF, start: '08:00', end: '09:20', room: 'Noyce 3813' }],
  },
  {
    id: `${SP27}-CSC-151-02`,
    courseId: 'CSC-151',
    term: SP27,
    number: '02',
    instructor: 'Shawn Ong',
    available: 6,
    capacity: 24,
    meetings: [{ days: MWF, start: '13:10', end: '14:30' }],
  },
  sec(SP27, 'CSC-161', '01', 'mwf10'),
  sec(SP27, 'CSC-161', '02', 'tr1'),
  sec(SP27, 'CSC-207', '01', 'mwf9'),
  sec(SP27, 'CSC-207', '02', 'tr930'),
  sec(SP27, 'CSC-208', '01', 'tr8'),
  sec(SP27, 'CSC-211', '01', 'mwf11'),
  sec(SP27, 'CSC-211', '02', 'tr230'),
  sec(SP27, 'CSC-213', '01', 'tr11'),
  sec(SP27, 'CSC-322', '01', 'tr1'),
  sec(SP27, 'CSC-341', '01', 'mwf2'),
  sec(SP27, 'CSC-364', '01', 'mwf3'),
  sec(SP27, 'CSC-395', '01', 'tr230'),
  sec(SP27, 'MAT-131', '01', 'mwf8'),
  sec(SP27, 'MAT-131', '02', 'mwf1'),
  sec(SP27, 'MAT-133', '01', 'mwf9'),
  sec(SP27, 'MAT-208', '01', 'tr930'),
  sec(SP27, 'MAT-215', '01', 'mwf10'),
  sec(SP27, 'MAT-215', '02', 'tr11'),
  sec(SP27, 'MAT-218', '01', 'mwf2'),
  sec(SP27, 'MAT-218', '02', 'tr1'),
  sec(SP27, 'MAT-321', '01', 'mwf11'),
  sec(SP27, 'MAT-336', '01', 'tr1'),
  sec(SP27, 'MAT-444', '01', 'tr230'),
  sec(SP27, 'ANT-104', '01', 'tr930'),
  sec(SP27, 'ART-111', '01', 'tr230'),
  sec(SP27, 'BIO-150', '01', 'tr11'),
  sec(SP27, 'ECN-111', '01', 'mwf9'),
  sec(SP27, 'EDU-101', '01', 'tr1'),
  sec(SP27, 'ENG-120', '01', 'mwf1'),
  sec(SP27, 'FMS-155', '01', 'tr1'),
  sec(SP27, 'GDS-111', '01', 'mwf2'),
  sec(SP27, 'HIS-100', '01', 'mwf10'),
  sec(SP27, 'MUS-101', '01', 'tr11'),
  sec(SP27, 'MUS-120', '01', 'm7'),
  sec(SP27, 'PHI-101', '01', 'tr8'),
  sec(SP27, 'POL-101', '01', 'mwf11'),
  sec(SP27, 'PSY-113', '01', 'tr930'),
  sec(SP27, 'SOC-111', '01', 'mwf3'),
  sec(SP27, 'SPN-102', '01', 'mwf9'),
  sec(SP27, 'STA-209', '01', 'mwf2'),

  // Fall 2026 — the demo student's current, registered term
  sec(FA26, 'CSC-208', '01', 'tr8'),
  sec(FA26, 'FMS-155', '03', 'tr1'),
  { ...sec(FA26, 'STA-209', '06', 'mwf2'), meetings: [{ days: MWF, start: '14:30', end: '15:50' }] },
  sec(FA26, 'MUS-120', '02', 'm7'),
];

export const SECTION_BY_ID: Record<string, Section> = Object.fromEntries(SECTIONS.map((s) => [s.id, s]));

export function sectionsFor(courseId: string, term: TermId): Section[] {
  return SECTIONS.filter((s) => s.courseId === courseId && s.term === term);
}
