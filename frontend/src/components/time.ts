import type { Day, Meeting, Section } from '../api/types.ts';

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
  const suffix = toMin(m.end) >= 12 * 60 ? 'pm' : 'am';
  return `${m.days.join('')} ${clock(m.start)}–${clock(m.end)}${suffix}`;
}

export function overlaps(a: Meeting, b: Meeting) {
  return a.days.some((d) => b.days.includes(d)) && toMin(a.start) < toMin(b.end) && toMin(b.start) < toMin(a.end);
}

export function sectionsConflict(a: Section, b: Section) {
  return a.meetings.some((ma) => b.meetings.some((mb) => overlaps(ma, mb)));
}

export type TimeBand = 'any' | 'morning' | 'afternoon' | 'evening';
export function inBand(s: Section, band: TimeBand) {
  if (band === 'any') return true;
  return s.meetings.every((m) => {
    const start = toMin(m.start);
    if (band === 'morning') return start < 12 * 60;
    if (band === 'afternoon') return start >= 12 * 60 && start < 17 * 60;
    return start >= 17 * 60;
  });
}

export type DayPattern = 'any' | 'MWF' | 'TR';
export function onDays(s: Section, p: DayPattern) {
  if (p === 'any') return true;
  const want = p === 'MWF' ? ['M', 'W', 'F'] : ['T', 'R'];
  return s.meetings.every((m) => m.days.every((d) => want.includes(d)));
}
