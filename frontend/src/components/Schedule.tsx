import { useEffect, useMemo, useRef, useState } from 'react';
import { api } from '../api/client.ts';
import { missingPrereqs } from '../engine/planner.ts';
import type { Action } from '../state/store.ts';
import type { Course, PlanResult, Section, StudentProfile, TermId } from '../types.ts';
import { ChevronDown, ChevronLeft, ChevronRight, Close, Collapse, Expand, Panel, Search, StatusIcon } from './Icons.tsx';
import { DAYS, DAY_NAME, clock, meetingText, sectionsConflict, toMin } from './time.ts';
import { useDismiss } from './useDismiss.ts';
import { useMedia } from './useMedia.ts';

type Scope = 'term' | 'major' | 'all';
const START_HOUR = 8;
const END_HOUR = 21;
const HOUR = 52;

interface Props {
  profile: StudentProfile;
  plan: PlanResult;
  act: (a: Action) => void;
}

export default function Schedule({ profile, plan, act }: Props) {
  const narrow = useMedia('(max-width: 1199px)');
  const phone = useMedia('(max-width: 767px)');
  // Students schedule the current term (read-only, registered) and the next one.
  const termIds = useMemo(() => {
    const ids = api.terms().map((t) => t.id);
    const i = ids.indexOf(profile.currentTerm);
    return ids.slice(i, i + 2);
  }, [profile.currentTerm]);
  const [termId, setTermId] = useState<TermId>(termIds[1] ?? termIds[0]);
  const [catalogOpen, setCatalogOpen] = useState(!narrow);
  const [expanded, setExpanded] = useState(false);
  const [day, setDay] = useState(0);

  const term = api.term(termId);
  const readOnly = termId === profile.currentTerm;
  const chosen = (profile.schedule[termId] ?? []).map((id) => api.section(id)).filter(Boolean) as Section[];
  const credits = chosen.reduce((s, x) => s + (api.course(x.courseId)?.credits ?? 0), 0);

  useEffect(() => {
    if (!expanded) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setExpanded(false);
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [expanded]);

  const i = termIds.indexOf(termId);
  const showCatalog = catalogOpen && !expanded;

  return (
    <main className={`schedule${expanded ? ' expanded' : ''}`} style={expanded ? { position: 'fixed', inset: 0, zIndex: 30, background: 'var(--paper)' } : undefined}>
      <div className="page-head">
        {!expanded && (
          <button className="icon-btn" aria-pressed={catalogOpen} aria-label="Course catalog" title="Course catalog" onClick={() => setCatalogOpen((o) => !o)}>
            <Panel />
          </button>
        )}
        <div className="term-nav">
          <button className="icon-btn" aria-label="Previous term" disabled={i <= 0} onClick={() => setTermId(termIds[i - 1])}>
            <ChevronLeft />
          </button>
          <strong>{term.label}</strong>
          <button className="icon-btn" aria-label="Next term" disabled={i >= termIds.length - 1} onClick={() => setTermId(termIds[i + 1])}>
            <ChevronRight />
          </button>
        </div>
        <span className="head-meta num">
          {credits} credits{readOnly ? ' · registered' : ''}
        </span>
        <div className="head-right">
          <button className="icon-btn" aria-label={expanded ? 'Exit full screen' : 'Full screen calendar'} title={expanded ? 'Exit full screen' : 'Full screen'} onClick={() => setExpanded((e) => !e)}>
            {expanded ? <Collapse /> : <Expand />}
          </button>
        </div>
      </div>
      {phone && (
        <div className="day-switch">
          {DAYS.map((d, k) => (
            <button key={d} aria-pressed={k === day} onClick={() => setDay(k)}>
              {DAY_NAME[d]}
            </button>
          ))}
        </div>
      )}
      <div className="schedule-body">
        <aside className="catalog" data-open={showCatalog} aria-hidden={!showCatalog}>
          {showCatalog && (
            <Catalog
              profile={profile}
              plan={plan}
              termId={termId}
              readOnly={readOnly}
              chosen={chosen}
              act={act}
              onClose={narrow ? () => setCatalogOpen(false) : undefined}
            />
          )}
        </aside>
        <WeekCalendar
          sections={chosen}
          kind={readOnly ? 'enrolled' : 'planned'}
          days={phone ? [DAYS[day]] : DAYS}
          onToggle={readOnly ? undefined : (id) => act({ type: 'toggleSection', termId, sectionId: id })}
        />
      </div>
    </main>
  );
}

/* ---------------- catalog ---------------- */

function Catalog({
  profile,
  plan,
  termId,
  readOnly,
  chosen,
  act,
  onClose,
}: {
  profile: StudentProfile;
  plan: PlanResult;
  termId: TermId;
  readOnly: boolean;
  chosen: Section[];
  act: (a: Action) => void;
  onClose?: () => void;
}) {
  const [scope, setScope] = useState<Scope>('term');
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState<string | null>(null);
  const term = api.term(termId);

  // Courses taken (or planned) before this term, for prerequisite checks.
  const takenBefore = useMemo(() => {
    const s = new Set<string>(plan.prior.map((p) => p.courseId!).filter(Boolean));
    for (const pt of plan.terms) {
      if (pt.term.id === termId) break;
      for (const it of pt.items) if (it.courseId) s.add(it.courseId);
    }
    return s;
  }, [plan, termId]);

  const done = useMemo(() => {
    const s = new Set<string>();
    for (const c of profile.credits) if (c.status === 'completed') s.add(c.courseId);
    return s;
  }, [profile.credits]);

  const planTerm = plan.terms.find((t) => t.term.id === termId);

  const groups = useMemo(() => {
    const q = query.trim().toLowerCase();
    const match = (c: Course) => !q || c.id.toLowerCase().replace('-', ' ').includes(q.replace('-', ' ')) || c.title.toLowerCase().includes(q);
    const offered = (c: Course) => c.offered.includes(term.season);
    if (scope === 'term') {
      const rows: { label?: string; courses: Course[] }[] = [];
      const planned: Course[] = [];
      for (const it of planTerm?.items ?? []) {
        if (it.courseId) planned.push(api.course(it.courseId));
        else if (it.slot) rows.push({ label: it.slot.label, courses: it.slot.options.map((o) => api.course(o)).filter((c) => c && offered(c)) });
      }
      // Sections picked here but not in the plan (shouldn't happen, but never hide them).
      for (const s of chosen) if (!planned.some((c) => c.id === s.courseId)) planned.push(api.course(s.courseId));
      return [{ courses: planned.filter(match) }, ...rows.map((r) => ({ ...r, courses: r.courses.filter(match) }))];
    }
    if (scope === 'major') {
      const ids = new Set<string>();
      for (const m of profile.majors)
        for (const r of api.program(m)?.requirements ?? []) {
          if (r.kind === 'course') ids.add(r.courseId);
          else r.options.forEach((o) => ids.add(o));
        }
      const list = [...ids].map((id) => api.course(id)).filter((c) => c && !done.has(c.id) && offered(c) && match(c));
      return [{ courses: list.sort((a, b) => a.id.localeCompare(b.id)) }];
    }
    return [{ courses: api.courses().filter((c) => offered(c) && match(c)).sort((a, b) => a.id.localeCompare(b.id)) }];
  }, [scope, query, planTerm, chosen, profile.majors, done, term.season]);

  const total = groups.reduce((s, g) => s + g.courses.length, 0);

  return (
    <div className="catalog-inner">
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <label className="search" style={{ flex: 1 }}>
          <Search />
          <span className="sr">Search courses</span>
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search courses" />
          {query && (
            <button className="icon-btn" style={{ width: 24, height: 24 }} aria-label="Clear search" onClick={() => setQuery('')}>
              <Close size={14} />
            </button>
          )}
        </label>
        {onClose && (
          <button className="icon-btn" aria-label="Close catalog" onClick={onClose} style={{ marginRight: 12, marginTop: 8 }}>
            <Close />
          </button>
        )}
      </div>
      <div className="scope" role="tablist" aria-label="Catalog scope">
        {(
          [
            ['term', readOnly ? 'Registered' : 'This term'],
            ['major', 'Major'],
            ['all', 'All'],
          ] as [Scope, string][]
        ).map(([k, label]) => (
          <button key={k} role="tab" aria-selected={scope === k} onClick={() => setScope(k)}>
            {label}
          </button>
        ))}
      </div>
      <div className="catalog-list">
        {total === 0 && (
          <div className="catalog-empty">
            {scope === 'major' && profile.majors.length === 0 ? 'Pick a major on the four-year plan.' : query ? 'No matches.' : 'Nothing planned for this term.'}
          </div>
        )}
        {groups.map((g, gi) =>
          g.courses.length === 0 ? null : (
            <div key={g.label ?? `g${gi}`}>
              {g.label && <div className="menu-label" style={{ padding: '14px 16px 4px' }}>{g.label} · choose one</div>}
              {g.courses.map((c) => (
                <CatalogRow
                  key={c.id}
                  course={c}
                  termId={termId}
                  open={open === c.id}
                  onToggle={() => setOpen((o) => (o === c.id ? null : c.id))}
                  done={done.has(c.id)}
                  missing={missingPrereqs(c.id, takenBefore)}
                  chosen={chosen}
                  readOnly={readOnly}
                  act={act}
                />
              ))}
            </div>
          ),
        )}
      </div>
    </div>
  );
}

function CatalogRow({
  course,
  termId,
  open,
  onToggle,
  done,
  missing,
  chosen,
  readOnly,
  act,
}: {
  course: Course;
  termId: TermId;
  open: boolean;
  onToggle: () => void;
  done: boolean;
  missing?: string;
  chosen: Section[];
  readOnly: boolean;
  act: (a: Action) => void;
}) {
  const sections = api.sections(termId).filter((s) => s.courseId === course.id);
  const added = chosen.some((s) => s.courseId === course.id);
  const status = done ? 'completed' : added ? (readOnly ? 'enrolled' : 'planned') : missing ? 'unsatisfied' : null;
  return (
    <div className="c-row" data-open={open}>
      <button className="c-head" aria-expanded={open} onClick={onToggle}>
        {status ? <StatusIcon status={status} /> : <span style={{ width: 16, flex: 'none' }} />}
        <span className="c-code">{course.id}</span>
        <span className="c-title">{course.title}</span>
        <span className="c-meta num">{course.credits}</span>
        <ChevronDown className="chev" />
      </button>
      <div className="reveal" data-open={open}>
        <div>
          <div className="sec-list">
            {done && <div className="sec-note">Already completed.</div>}
            {missing && !done && <div className="sec-note" style={{ color: 'var(--danger)' }}>{missing}</div>}
            {sections.length === 0 && <div className="sec-note">No sections this term.</div>}
            {sections.map((s) => {
              const isAdded = chosen.some((x) => x.id === s.id);
              const clash = !isAdded ? chosen.find((x) => x.courseId !== s.courseId && sectionsConflict(x, s)) : undefined;
              return (
                <div className="sec-row" key={s.id}>
                  <span className="sec-time num">{s.meetings.map(meetingText).join(', ')}</span>
                  <span className="sec-who">
                    {clash ? (
                      <span className="sec-warn">Clashes with {clash.courseId}</span>
                    ) : s.available === 0 ? (
                      <span className="sec-warn">Full · waitlist only</span>
                    ) : (
                      `${s.instructor} · ${s.available} of ${s.capacity} open`
                    )}
                  </span>
                  {readOnly ? (
                    isAdded && <span className="sec-add" data-added="true">Registered</span>
                  ) : (
                    <button
                      className="sec-add"
                      data-added={isAdded}
                      disabled={done}
                      onClick={() => act({ type: 'toggleSection', termId, sectionId: s.id })}
                    >
                      {isAdded ? 'Added' : 'Add'}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------------- calendar ---------------- */

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

function WeekCalendar({
  sections,
  kind,
  days,
  onToggle,
}: {
  sections: Section[];
  kind: 'enrolled' | 'planned';
  days: string[];
  onToggle?: (sectionId: string) => void;
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
                      <span className="ev-code">{e.section.courseId}</span>
                      <span className="ev-time num">
                        {clock(minToHHMM(e.start))}–{clock(minToHHMM(e.end))}
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
                  aria-label={selEv.section.courseId}
                  style={{ top: ((selEv.end - START_HOUR * 60) / 60) * HOUR + 6, left: days.length === 1 ? 8 : d === 'F' || d === 'R' ? 'auto' : 8, right: d === 'F' || d === 'R' ? 8 : 'auto' }}
                >
                  <h4>
                    {selEv.section.courseId} · {api.course(selEv.section.courseId)?.title}
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
                    (() => {
                      const others = api
                        .sections(selEv.section.term)
                        .filter((s) => s.courseId === selEv.section.courseId && s.id !== selEv.section.id);
                      if (!others.length) return null;
                      return (
                        <div style={{ marginTop: 10, borderTop: '1px solid var(--line)', paddingTop: 6 }}>
                          {others.map((o) => {
                            const clash = sections.find((x) => x.courseId !== o.courseId && sectionsConflict(x, o));
                            return (
                              <button
                                key={o.id}
                                className="menu-item num"
                                style={{ margin: '0 -10px', width: 'calc(100% + 20px)' }}
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
                        </div>
                      );
                    })()}
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
            <div>{kind === 'planned' ? 'Add sections from the catalog.' : 'No classes this day.'}</div>
          </div>
        )}
      </div>
    </div>
  );
}

function minToHHMM(m: number) {
  return `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`;
}
