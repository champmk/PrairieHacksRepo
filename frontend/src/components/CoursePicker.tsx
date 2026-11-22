import { useEffect, useMemo, useRef, useState } from 'react';
import { ApiError, api } from '../api/client.ts';
import type { Course, Section, TermId } from '../api/types.ts';
import type { CG } from '../state/useCourseGraph.ts';
import { Check, ChevronDown, Close, Collapse, Expand, Panel, Search } from './Icons.tsx';
import WeekCalendar from './WeekCalendar.tsx';
import { DAYS, DAY_NAME, type DayPattern, type TimeBand, inBand, meetingText, onDays, sectionsConflict } from './time.ts';
import { useDismiss } from './useDismiss.ts';
import { useMedia } from './useMedia.ts';

type Scope = 'all' | 'major';

export default function CoursePicker({ cg }: { cg: CG }) {
  const { student, plan, courseById, catalog, majors } = cg;
  const narrow = useMedia('(max-width: 1199px)');
  const phone = useMedia('(max-width: 767px)');
  const current = student!.current_term;
  const next = student!.terms.find((t) => t.state === 'next')?.id ?? current;
  const [term, setTerm] = useState<TermId>(next);
  const [sections, setSections] = useState<Record<TermId, Section[]>>({});
  const [catalogOpen, setCatalogOpen] = useState(!narrow);
  const [expanded, setExpanded] = useState(false);
  const [day, setDay] = useState(0);
  const [time, setTime] = useState<TimeBand>('any');
  const [days, setDays] = useState<DayPattern>('any');
  const [scope, setScope] = useState<Scope>('all');
  const [dept, setDept] = useState('any');
  const [openOnly, setOpenOnly] = useState(false);
  const [query, setQuery] = useState('');
  const [openRow, setOpenRow] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const readOnly = term === current;
  const termLabel = (id: TermId) => student!.terms.find((t) => t.id === id)?.label ?? id;

  useEffect(() => {
    for (const t of [current, next])
      if (!sections[t])
        api
          .sections(t)
          .then((list) => setSections((s) => ({ ...s, [t]: list })))
          .catch(() => setSections((s) => ({ ...s, [t]: [] })));
  }, [current, next, sections]);

  useEffect(() => {
    if (!expanded) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setExpanded(false);
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [expanded]);

  const termSections = sections[term] ?? [];
  const byId = useMemo(() => Object.fromEntries(termSections.map((s) => [s.id, s])), [termSections]);
  const chosenIds = student!.schedule[term] ?? [];
  const chosen = chosenIds.map((id) => byId[id]).filter(Boolean) as Section[];
  const credits = chosen.reduce((s, x) => s + (courseById[x.course]?.credits ?? 0), 0);

  const toggle = async (sectionId: string) => {
    const sec = byId[sectionId];
    if (!sec || readOnly) return;
    const has = chosenIds.includes(sectionId);
    const ids = has ? chosenIds.filter((id) => id !== sectionId) : [...chosenIds.filter((id) => byId[id]?.course !== sec.course), sectionId];
    setMsg(null);
    try {
      const res = await cg.actions.saveSchedule(term, ids);
      if (res?.clashes.length) setMsg(`${res.clashes.length} time clash${res.clashes.length > 1 ? 'es' : ''} in this schedule`);
    } catch (e) {
      setMsg(e instanceof ApiError ? e.message : 'Could not save');
    }
  };

  // Courses in the plan for this term, so the student starts from their route.
  const planTerm = plan?.terms.find((t) => t.id === term);
  const required = useMemo(() => {
    const s = new Set<string>();
    for (const t of planTerm?.tablets ?? []) {
      if (t.required && t.course) s.add(t.course);
      if (t.required && !t.course) t.slot?.options.forEach((o) => s.add(o));
    }
    return s;
  }, [planTerm]);
  const majorCourses = useMemo(() => {
    const s = new Set<string>();
    for (const p of catalog?.programs ?? []) if (majors.includes(p.id)) p.slots.forEach((sl) => sl.options.forEach((o) => s.add(o)));
    return s;
  }, [catalog, majors]);
  const done = useMemo(
    () => new Set((student!.enrollments ?? []).filter((e) => e.status === 'completed').map((e) => e.course)),
    [student],
  );

  const offeredCourses = useMemo(() => {
    const ids = [...new Set(termSections.map((s) => s.course))];
    return ids.map((id) => courseById[id]).filter(Boolean) as Course[];
  }, [termSections, courseById]);
  const departments = useMemo(() => [...new Set(offeredCourses.map((c) => c.department))].sort(), [offeredCourses]);

  const sectionPass = (s: Section) => inBand(s, time) && onDays(s, days) && (!openOnly || s.available > 0);
  const q = query.trim().toLowerCase().replace('-', ' ');
  const visible = offeredCourses
    .filter((c) => scope === 'all' || majorCourses.has(c.id))
    .filter((c) => dept === 'any' || c.department === dept)
    .filter((c) => !q || c.id.toLowerCase().replace('-', ' ').includes(q) || c.title.toLowerCase().includes(q))
    .filter((c) => termSections.some((s) => s.course === c.id && sectionPass(s)) || chosen.some((s) => s.course === c.id))
    .sort((a, b) => Number(required.has(b.id)) - Number(required.has(a.id)) || a.id.localeCompare(b.id));
  const fromPlan = visible.filter((c) => required.has(c.id) || chosen.some((s) => s.course === c.id));
  const rest = visible.filter((c) => !fromPlan.includes(c));
  const showCatalog = catalogOpen && !expanded;

  return (
    <main className={`schedule${expanded ? ' expanded' : ''}`} style={expanded ? { position: 'fixed', inset: 0, zIndex: 30, background: 'var(--paper)' } : undefined}>
      <div className="page-head">
        {!expanded && (
          <button className="icon-btn" aria-pressed={catalogOpen} aria-label="Course catalog" title="Course catalog" onClick={() => setCatalogOpen((o) => !o)}>
            <Panel />
          </button>
        )}
        <div className="term-tabs" role="tablist" aria-label="Term">
          {[current, next].filter((t, i, a) => a.indexOf(t) === i).map((t) => (
            <button key={t} role="tab" aria-selected={term === t} onClick={() => setTerm(t)}>
              {termLabel(t)}
              <span>{t === current ? 'registered' : 'planning'}</span>
            </button>
          ))}
        </div>
        <span className="head-meta num">{credits} credits</span>
        <div className="head-right">
          <button className="icon-btn" aria-label={expanded ? 'Exit full screen' : 'Full screen calendar'} title={expanded ? 'Exit full screen' : 'Full screen'} onClick={() => setExpanded((e) => !e)}>
            {expanded ? <Collapse /> : <Expand />}
          </button>
        </div>
      </div>

      <div className="filters" role="toolbar" aria-label="Filters">
        <FilterMenu label="Time" value={time} onChange={setTime} options={[['any', 'Any time'], ['morning', 'Morning'], ['afternoon', 'Afternoon'], ['evening', 'Evening']]} />
        <FilterMenu label="Days" value={days} onChange={setDays} options={[['any', 'Any days'], ['MWF', 'Mon · Wed · Fri'], ['TR', 'Tue · Thu']]} />
        <FilterMenu
          label="Major"
          value={scope}
          onChange={setScope}
          options={[['all', 'All courses'], ['major', majors.length ? 'My major courses' : 'My major courses (pick a major)']]}
        />
        <FilterMenu label="Department" value={dept} onChange={setDept} options={[['any', 'Any department'], ...departments.map((d) => [d, d] as [string, string])]} />
        <button className="filter-btn" aria-pressed={openOnly} onClick={() => setOpenOnly((o) => !o)}>
          {openOnly && <Check size={14} />} Open seats
        </button>
        {msg && <span className="filters-msg">{msg}</span>}
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
                {narrow && (
                  <button className="icon-btn" aria-label="Close catalog" onClick={() => setCatalogOpen(false)} style={{ marginRight: 12, marginTop: 8 }}>
                    <Close />
                  </button>
                )}
              </div>
              <div className="catalog-list">
                {visible.length === 0 && <div className="catalog-empty">{termSections.length ? 'No courses match these filters.' : 'No sections loaded for this term.'}</div>}
                {fromPlan.length > 0 && <div className="group-label">From your 4-year plan</div>}
                {fromPlan.map((c) => courseRow(c))}
                {rest.length > 0 && fromPlan.length > 0 && <div className="group-label">All courses</div>}
                {rest.map((c) => courseRow(c))}
              </div>
            </div>
          )}
        </aside>
        <WeekCalendar
          sections={chosen}
          allSections={termSections}
          kind={readOnly ? 'enrolled' : 'planned'}
          days={phone ? [DAYS[day]] : DAYS}
          courseById={courseById}
          onToggle={readOnly ? undefined : toggle}
          empty={readOnly ? 'No registered classes.' : 'Add sections from the catalog.'}
        />
      </div>
    </main>
  );

  function courseRow(c: Course) {
    const open = openRow === c.id;
    const secs = termSections.filter((s) => s.course === c.id);
    const added = chosen.find((s) => s.course === c.id);
    return (
      <div className="c-row" data-open={open} key={c.id}>
        <button className="c-head" aria-expanded={open} onClick={() => setOpenRow(open ? null : c.id)}>
          <span className="r-mark" aria-label={required.has(c.id) ? 'Required for your major' : undefined}>{required.has(c.id) ? 'R' : ''}</span>
          <span className="c-code">{c.id}</span>
          <span className="c-title">{c.title}</span>
          {done.has(c.id) ? <span className="c-meta">done</span> : added ? <Check size={14} className="added-check" /> : <span className="c-meta num">{c.credits}</span>}
          <ChevronDown className="chev" />
        </button>
        <div className="reveal" data-open={open}>
          <div>
            <div className="sec-list">
              {c.prereq_text && c.prereq_text !== 'None' && <div className="sec-note">Prereq: {c.prereq_text}</div>}
              {secs.map((s) => {
                const isAdded = chosenIds.includes(s.id);
                const clash = !isAdded ? chosen.find((x) => x.course !== s.course && sectionsConflict(x, s)) : undefined;
                const hidden = !sectionPass(s) && !isAdded;
                if (hidden) return null;
                return (
                  <div className="sec-row" key={s.id}>
                    <span className="sec-time num">{s.meetings.map(meetingText).join(', ')}</span>
                    <span className="sec-who">
                      {clash ? (
                        <span className="sec-warn">Clashes with {clash.course}</span>
                      ) : s.available === 0 ? (
                        <span className="sec-warn">Full · waitlist</span>
                      ) : (
                        `${s.instructor} · ${s.available} of ${s.capacity} open`
                      )}
                    </span>
                    {readOnly ? (
                      isAdded && <span className="sec-add" data-added="true">Registered</span>
                    ) : (
                      <button className="sec-add" data-added={isAdded} disabled={done.has(c.id)} onClick={() => toggle(s.id)}>
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
}

function FilterMenu<T extends string>({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: T;
  onChange: (v: T) => void;
  options: [T, string][];
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useDismiss(ref, open, () => setOpen(false));
  const current = options.find(([v]) => v === value);
  const active = value !== options[0][0];
  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button className="filter-btn" data-active={active} aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
        {active ? current?.[1] : label}
        <ChevronDown size={14} />
      </button>
      {open && (
        <div className="menu" role="menu" style={{ left: 0, top: 36, maxHeight: 320, overflowY: 'auto' }}>
          {options.map(([v, text]) => (
            <button
              key={v}
              className="menu-item"
              role="menuitemradio"
              aria-checked={v === value}
              onClick={() => {
                onChange(v);
                setOpen(false);
              }}
            >
              {text}
              <span className="right">{v === value && <Check size={14} />}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
