import { useRef, useState } from 'react';
import type { Course, Section } from '../api/types.ts';
import { DAY_NAME, clock, meetingText, sectionsConflict, toMin } from './time.ts';
import { useDismiss } from './useDismiss.ts';

const START_HOUR = 8;
const END_HOUR = 22;
const HOUR = 52;

interface Ev {
  key: string;
  section: Section;
  day: string;
  start: number;
  end: number;
  lane: number;
  lanes: number;
  conflict: boolean;
}

function layout(sections: Section[], days: string[]): Ev[] {
  const evs: Ev[] = [];
  for (const s of sections)
    for (const m of s.meetings)
      for (const d of m.days)
        if (days.includes(d))
          evs.push({ key: `${s.id}-${d}-${m.start}`, section: s, day: d, start: toMin(m.start), end: toMin(m.end), lane: 0, lanes: 1, conflict: false });
  for (const d of days) {
    const list = evs.filter((e) => e.day === d).sort((a, b) => a.start - b.start || a.end - b.end);
    for (const e of list) {
      const over = list.filter((o) => o !== e && o.start < e.end && e.start < o.end);
      e.conflict = over.length > 0;
      const group = [e, ...over].sort((a, b) => a.start - b.start || a.section.id.localeCompare(b.section.id));
      e.lanes = group.length;
      e.lane = group.indexOf(e);
    }
  }
  return evs;
}

const hhmm = (m: number) => `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`;

export default function WeekCalendar({
  sections,
  allSections,
  kind,
  days,
  courseById,
  onToggle,
  empty,
}: {
  sections: Section[];
  allSections: Section[];
  kind: 'enrolled' | 'planned';
  days: string[];
  courseById: Record<string, Course>;
  onToggle?: (sectionId: string) => void;
  empty: string;
}) {
  const evs = layout(sections, days);
  const [sel, setSel] = useState<string | null>(null);
  const popRef = useRef<HTMLDivElement>(null);
  useDismiss(popRef, sel !== null, () => setSel(null));
  const hours = Array.from({ length: END_HOUR - START_HOUR }, (_, k) => START_HOUR + k);
  const selEv = evs.find((e) => e.key === sel);

  return (
    <div className="cal" style={{ ['--days' as string]: days.length, ['--hour' as string]: `${HOUR}px` }}>
      <div className="cal-days">
        <div />
        {days.map((d) => (
          <div className="cal-day" key={d}>
            {DAY_NAME[d as keyof typeof DAY_NAME]}
          </div>
        ))}
      </div>
      <div className="cal-scroll">
        <div className="cal-grid" style={{ paddingTop: 8 }}>
          <div className="cal-hours">
            {hours.map((h) => (
              <div className="cal-hour num" key={h}>
                {h === 12 ? '12pm' : h > 12 ? `${h - 12}pm` : `${h}am`}
              </div>
            ))}
          </div>
          {days.map((d) => (
            <div className="cal-col" key={d}>
              {hours.map((h) => (
                <div className="cal-line" key={h} />
              ))}
              {evs
                .filter((e) => e.day === d)
                .map((e) => {
                  const top = ((e.start - START_HOUR * 60) / 60) * HOUR;
                  const height = Math.max(((e.end - e.start) / 60) * HOUR - 2, 22);
                  const w = 100 / e.lanes;
                  return (
                    <button
                      key={e.key}
                      className="ev"
                      data-kind={kind}
                      data-conflict={e.conflict}
                      data-selected={sel === e.key}
                      style={{ top, height, left: `calc(${e.lane * w}% + 4px)`, right: 'auto', width: `calc(${w}% - 8px)` }}
                      onClick={(ev) => {
                        ev.stopPropagation();
                        setSel((s) => (s === e.key ? null : e.key));
                      }}
                    >
                      <span className="ev-code">{e.section.course}</span>
                      <span className="ev-time num">
                        {clock(hhmm(e.start))}–{clock(hhmm(e.end))}
                      </span>
                      {e.conflict && <span className="ev-warn">Time clash</span>}
                    </button>
                  );
                })}
              {selEv && selEv.day === d && (
                <div
                  ref={popRef}
                  className="menu ev-pop"
                  role="dialog"
                  aria-label={selEv.section.course}
                  style={{ top: ((selEv.end - START_HOUR * 60) / 60) * HOUR + 6, left: days.length === 1 ? 8 : d === 'F' || d === 'R' ? 'auto' : 8, right: d === 'F' || d === 'R' ? 8 : 'auto' }}
                >
                  <h4>
                    {selEv.section.course} · {courseById[selEv.section.course]?.title ?? ''}
                  </h4>
                  <p>
                    Section {selEv.section.number} · {selEv.section.instructor}
                  </p>
                  <p className="num">
                    {selEv.section.meetings.map(meetingText).join(', ')}
                    {selEv.section.meetings[0]?.room ? ` · ${selEv.section.meetings[0].room}` : ''}
                  </p>
                  <p className="num">
                    {selEv.section.available} of {selEv.section.capacity} seats open
                  </p>
                  {onToggle &&
                    allSections
                      .filter((s) => s.course === selEv.section.course && s.id !== selEv.section.id)
                      .map((o) => {
                        const clash = sections.find((x) => x.course !== o.course && sectionsConflict(x, o));
                        return (
                          <button
                            key={o.id}
                            className="menu-item num"
                            style={{ margin: '6px -10px 0', width: 'calc(100% + 20px)' }}
                            onClick={() => {
                              onToggle(o.id);
                              setSel(null);
                            }}
                          >
                            Switch to {o.meetings.map(meetingText).join(', ')}
                            <span className="right" style={clash ? { color: 'var(--danger)' } : undefined}>
                              {clash ? 'Clash' : o.available === 0 ? 'Full' : ''}
                            </span>
                          </button>
                        );
                      })}
                  <div className="pop-actions">
                    {onToggle ? (
                      <button
                        className="link"
                        style={{ color: 'var(--danger)' }}
                        onClick={() => {
                          onToggle(selEv.section.id);
                          setSel(null);
                        }}
                      >
                        Remove
                      </button>
                    ) : (
                      <span className="muted" style={{ fontSize: 12 }}>Registered</span>
                    )}
                    <button className="link" onClick={() => setSel(null)}>
                      Done
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
        {evs.length === 0 && (
          <div className="cal-empty">
            <div>{empty}</div>
          </div>
        )}
      </div>
    </div>
  );
}
