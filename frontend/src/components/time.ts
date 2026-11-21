import type { Day, Meeting, Section } from '../types.ts';

export const DAYS: Day[] = ['M', 'T', 'W', 'R', 'F'];
export const DAY_NAME: Record<Day, string> = { M: 'Mon', T: 'Tue', W: 'Wed', R: 'Thu', F: 'Fri' };

export const toMin = (hhmm: string) => {
  const [h, m] = hhmm.split(':').map(Number);
  return h * 60 + m;
};

export function clock(hhmm: string) {
  const [h, m] = hhmm.split(':').map(Number);
  const h12 = ((h + 11) % 12) + 1;
  return `${h12}:${String(m).padStart(2, '0')}`;
}

export function meetingText(m: Meeting) {
  const end = toMin(m.end);
  const suffix = end >= 12 * 60 ? 'pm' : 'am';
  return `${m.days.join('')} ${clock(m.start)}–${clock(m.end)}${suffix}`;
}

export function overlaps(a: Meeting, b: Meeting) {
  return a.days.some((d) => b.days.includes(d)) && toMin(a.start) < toMin(b.end) && toMin(b.start) < toMin(a.end);
}

export function sectionsConflict(a: Section, b: Section) {
  return a.meetings.some((ma) => b.meetings.some((mb) => overlaps(ma, mb)));
}
