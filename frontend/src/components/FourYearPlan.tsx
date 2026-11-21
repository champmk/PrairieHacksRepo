import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type MutableRefObject } from 'react';
import { api } from '../api/client.ts';
import { MAJOR_CHOICES } from '../data/catalog.ts';
import { directPrereqs, missingPrereqs } from '../engine/planner.ts';
import type { Action } from '../state/store.ts';
import type { Course, PlanItem, PlanResult, PlanTerm, StudentProfile, Term, TermId } from '../types.ts';
import { Check, ChevronDown, Close, More, PanelRight, Plus, Search, StatusIcon, Undo } from './Icons.tsx';
import { useDismiss } from './useDismiss.ts';
import { useMedia } from './useMedia.ts';

interface Props {
  profile: StudentProfile;
  plan: PlanResult;
  act: (a: Action) => void;
  canUndo: boolean;
  lastCause: MutableRefObject<Action['type'] | null>;
}

const shortTerm = (id?: TermId) => {
  if (!id) return '';
  const t = api.term(id);
  return t ? `${t.season === 'Fall' ? 'Fall' : 'Spr'} ’${String(t.year).slice(2)}` : '';
};

export default function FourYearPlan({ profile, plan, act, canUndo, lastCause }: Props) {
  const narrow = useMedia('(max-width: 1199px)');
  const phone = useMedia('(max-width: 767px)');
  const cols = phone ? 1 : narrow ? 2 : 4;
  const [railOpen, setRailOpen] = useState(!narrow);
  const [hover, setHover] = useState<string | null>(null); // courseId under the pointer
  const [flash, setFlash] = useState<string | null>(null);
  const [notice, setNotice] = useState<string[]>([]);

  // Show what the optimizer changed after each student action.
  useEffect(() => {
    if (!lastCause.current || lastCause.current === 'load') return;
    lastCause.current = null;
    if (!plan.changes.length) return;
    setNotice(plan.changes);
    const t = setTimeout(() => setNotice([]), 9000);
    return () => clearTimeout(t);
  }, [plan, lastCause]);

  const termIndex = useMemo(() => Object.fromEntries(api.terms().map((t, i) => [t.id, i])), []);
  const nowIdx = termIndex[profile.currentTerm];
  const futureTerms = useMemo(() => api.terms().filter((t) => termIndex[t.id] > nowIdx), [termIndex, nowIdx]);

  // Everything on record or in the plan before a given term, for readiness hints.
  const takenBefore = useCallback(
    (termId: TermId) => {
      const s = new Set<string>(plan.prior.map((p) => p.courseId!).filter(Boolean));
      for (const pt of plan.terms) {
        if (pt.term.id === termId) break;
        for (const it of pt.items) if (it.courseId) s.add(it.courseId);
      }
      return s;
    },
    [plan],
  );

  const inPlan = useMemo(() => {
    const s = new Set<string>(plan.prior.map((p) => p.courseId!).filter(Boolean));
    for (const pt of plan.terms) for (const it of pt.items) if (it.courseId) s.add(it.courseId);
    return s;
  }, [plan]);

  const required = useMemo(() => {
    const s = new Set<string>();
    for (const m of profile.majors) for (const r of api.program(m)?.requirements ?? []) if (r.kind === 'course') s.add(r.courseId);
    return s;
  }, [profile.majors]);

  const related = useMemo(() => {
    if (!hover) return null;
    const s = new Set<string>([hover, ...directPrereqs(hover)]);
    for (const id of inPlan) if (directPrereqs(id).includes(hover)) s.add(id);
    return s;
  }, [hover, inPlan]);

  const total = plan.totalCredits.earned + plan.totalCredits.planned;
  const majorsLabel = profile.majors.length ? profile.majors.map((m) => api.program(m)?.name).join(' + ') : 'Undecided';

  const graphRef = useRef<HTMLDivElement>(null);
  const flashTo = (key: string) => {
    setFlash(key);
    graphRef.current?.querySelector(`[data-key="${CSS.escape(key)}"]`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    setTimeout(() => setFlash((f) => (f === key ? null : f)), 1300);
  };

  return (
    <main className="plan">
      <div className="plan-head">
        <MajorPicker label={majorsLabel} majors={profile.majors} onChange={(m) => act({ type: 'setMajors', majors: m })} />
        <span className="head-meta num">
          {total} of {plan.totalCredits.required} credits
        </span>
        <div className="legend" aria-hidden="true">
          <span><StatusIcon status="completed" /> Done</span>
          <span><StatusIcon status="planned" /> Planned</span>
          <span><StatusIcon status="unsatisfied" /> Open</span>
        </div>
        <div className="head-right">
          <PaceMenu cap={profile.creditCap} onChange={(cap) => act({ type: 'setCap', cap })} />
          <button className="icon-btn" aria-label="Undo" title="Undo" disabled={!canUndo} onClick={() => act({ type: 'undo' })}>
            <Undo />
          </button>
          <button className="icon-btn" aria-pressed={railOpen} aria-label="Requirements" title="Requirements" onClick={() => setRailOpen((o) => !o)}>
            <PanelRight />
          </button>
        </div>
      </div>

      {notice.length > 0 && (
        <div className="notice" role="status">
          <span>{notice.join(' · ')}</span>
          <button className="icon-btn" style={{ marginLeft: 'auto', width: 24, height: 24 }} aria-label="Dismiss" onClick={() => setNotice([])}>
            <Close size={14} />
          </button>
        </div>
      )}

      <div className="plan-body">
        <div
          className="graph-wrap"
          ref={graphRef}
          onPointerLeave={() => setHover(null)}
          onPointerMove={(e) => {
            if (!(e.target as HTMLElement).closest('[data-course]')) setHover(null);
          }}
          onPointerDown={(e) => {
            if (!(e.target as HTMLElement).closest('[data-course]')) setHover(null);
          }}
        >
          {plan.prior.length > 0 && (
            <div className="prior">
              <span className="muted">Before Grinnell</span>
              {plan.prior.map((p) => (
                <span key={p.key} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  <StatusIcon status="completed" />
                  <b>{p.courseId}</b>
                  {api.course(p.courseId!)?.title}
                </span>
              ))}
            </div>
          )}
          {profile.majors.length === 0 && <p className="empty-plan">Pick a major to build your plan.</p>}
          <Graph
            plan={plan}
            profile={profile}
            cols={cols}
            nowIdx={nowIdx}
            termIndex={termIndex}
            related={related}
            setHover={setHover}
            flash={flash}
            takenBefore={takenBefore}
            inPlan={inPlan}
            required={required}
            act={act}
            futureTerms={futureTerms}
          />
          {plan.unscheduled.length > 0 && (
            <div className="unscheduled">
              <h3>Doesn’t fit yet</h3>
              {plan.unscheduled.map((it) => (
                <div className="item" key={it.key} data-key={it.key}>
                  <StatusIcon status="unsatisfied" />
                  <span className="item-code">{it.courseId ?? it.slot?.label}</span>
                  <span className="item-title">{it.reason}</span>
                </div>
              ))}
            </div>
          )}
        </div>
        <aside className="rail" data-open={railOpen} aria-hidden={!railOpen}>
          <div className="rail-inner">
            {plan.progress.length === 0 && <p className="muted">No major selected.</p>}
            {plan.progress.map((p) => {
              const pct = (n: number) => `${(n / Math.max(p.total, 1)) * 100}%`;
              return (
                <section className="prog" key={p.programId}>
                  <div className="prog-head">
                    <strong>{p.name}</strong>
                    <span className="muted num">
                      {p.completed + p.planned} of {p.total}
                    </span>
                  </div>
                  <div className="bar" aria-hidden="true">
                    <i style={{ width: pct(p.completed), background: 'var(--done)' }} />
                    <i style={{ width: pct(p.planned), background: 'var(--planned)' }} />
                  </div>
                  {p.requirements.map((r, k) => (
                    <button
                      className="req"
                      key={`${r.id}-${k}`}
                      onClick={() => {
                        const key = r.courseId
                          ? r.status === 'completed' && !r.termId
                            ? null
                            : `course:${r.courseId}`
                          : findSlotKey(plan, r.id, r.termId);
                        if (key) flashTo(key);
                      }}
                    >
                      <StatusIcon status={r.status} />
                      <span className="req-label">{r.courseId ?? r.label}</span>
                      <span className="req-term">{r.termId ? shortTerm(r.termId) : r.status === 'completed' ? 'AP' : ''}</span>
                    </button>
                  ))}
                </section>
              );
            })}
          </div>
        </aside>
      </div>
    </main>
  );
}

function findSlotKey(plan: PlanResult, reqId: string, termId?: TermId) {
  for (const pt of plan.terms) {
    if (termId && pt.term.id !== termId) continue;
    const it = pt.items.find((x) => x.slot?.requirementId === reqId && !x.courseId);
    if (it) return it.key;
  }
  return plan.unscheduled.find((x) => x.slot?.requirementId === reqId)?.key ?? null;
}

/* ---------------- graph ---------------- */

interface GraphProps {
  plan: PlanResult;
  profile: StudentProfile;
  cols: number;
  nowIdx: number;
  termIndex: Record<string, number>;
  related: Set<string> | null;
  setHover: (id: string | null) => void;
  flash: string | null;
  takenBefore: (t: TermId) => Set<string>;
  inPlan: Set<string>;
  required: Set<string>;
  act: (a: Action) => void;
  futureTerms: Term[];
}

function Graph(props: GraphProps) {
  const { plan, cols, nowIdx, termIndex, related } = props;
  const wrapRef = useRef<HTMLDivElement>(null);
  const [paths, setPaths] = useState<string[]>([]);
  const hovered = related ? [...related][0] : null;

  // Draw prerequisite lines for the hovered course.
  useLayoutEffect(() => {
    const wrap = wrapRef.current;
    if (!wrap || !hovered || !related) {
      setPaths([]);
      return;
    }
    const box = wrap.getBoundingClientRect();
    const el = (id: string) => wrap.querySelector<HTMLElement>(`[data-course="${CSS.escape(id)}"]`);
    const target = el(hovered);
    if (!target) {
      setPaths([]);
      return;
    }
    const out: string[] = [];
    const link = (from: HTMLElement, to: HTMLElement) => {
      const a = from.getBoundingClientRect();
      const b = to.getBoundingClientRect();
      const x1 = a.left - box.left + 14;
      const y1 = a.top - box.top + a.height / 2;
      const x2 = b.left - box.left + 14;
      const y2 = b.top - box.top + b.height / 2;
      const dx = Math.max(Math.abs(x2 - x1) * 0.5, 40);
      out.push(`M${x1 - 8} ${y1} C${x1 - 8 - dx * 0.2} ${y1}, ${x1 - dx} ${y2}, ${x2 - 8} ${y2}`);
    };
    for (const id of directPrereqs(hovered)) {
      const e = el(id);
      if (e) link(e, target);
    }
    for (const id of related) {
      if (id === hovered || !directPrereqs(id).includes(hovered)) continue;
      const e = el(id);
      if (e) link(target, e);
    }
    setPaths(out);
  }, [hovered, related, plan]);

  return (
    <div ref={wrapRef} style={{ position: 'relative' }}>
      <div className="years">
        {plan.terms.map((pt, i) => (
          <SemesterNode
            key={pt.term.id}
            pt={pt}
            index={i}
            lastInRow={(i + 1) % cols === 0}
            when={termIndex[pt.term.id] < nowIdx ? 'past' : termIndex[pt.term.id] === nowIdx ? 'now' : 'future'}
            yearLabel={i % 2 === 0 ? `Year ${i / 2 + 1}` : ''}
            {...props}
          />
        ))}
      </div>
      <svg className="lines" aria-hidden="true">
        {paths.map((d, k) => (
          <path key={`${hovered}-${k}`} d={d} pathLength={1} />
        ))}
      </svg>
    </div>
  );
}

function SemesterNode({
  pt,
  lastInRow,
  when,
  yearLabel,
  profile,
  related,
  setHover,
  flash,
  takenBefore,
  inPlan,
  required,
  act,
  futureTerms,
  cols,
}: GraphProps & { pt: PlanTerm; index: number; lastInRow: boolean; when: 'past' | 'now' | 'future'; yearLabel: string }) {
  const [drop, setDrop] = useState(false);
  const future = when === 'future';
  const phoneLayout = cols === 1;
  const over = future && pt.credits > profile.creditCap;
  let n = 0;
  return (
    <section
      className="node"
      data-when={when}
      data-last-in-row={lastInRow}
      data-drop={drop}
      aria-label={pt.term.label}
      onDragOver={(e) => {
        if (!future || !e.dataTransfer.types.includes('text/course')) return;
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        setDrop(true);
      }}
      onDragLeave={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node)) setDrop(false);
      }}
      onDrop={(e) => {
        setDrop(false);
        const id = e.dataTransfer.getData('text/course');
        if (id && future) act({ type: 'place', courseId: id, termId: pt.term.id });
      }}
    >
      <div className="year-label">{yearLabel}</div>
      <div className="node-rail">
        <span className="node-dot" />
      </div>
      <div className="node-head">
        <strong>{pt.term.label}</strong>
        {when === 'now' && <span className="node-now">Now</span>}
        <span className="node-credits num" data-over={over} title={over ? `Over your ${profile.creditCap}-credit limit` : undefined}>
          {pt.credits} cr
        </span>
      </div>
      {pt.items.map((it) =>
        it.courseId ? (
          <CourseItem
            key={it.key}
            it={it}
            termId={pt.term.id}
            movable={future}
            dim={!!related && !related.has(it.courseId)}
            focus={!!related && related.has(it.courseId)}
            flash={flash === it.key}
            setHover={setHover}
            required={required.has(it.courseId)}
            act={act}
            delay={n++}
            futureTerms={futureTerms}
          />
        ) : (
          <Slot key={it.key} it={it} termId={pt.term.id} takenBefore={takenBefore} act={act} flash={flash === it.key} dim={!!related} />
        ),
      )}
      {pt.items.length === 0 && !future && <div className="item"><span className="item-title">No courses</span></div>}
      {future && <AddCourse termId={pt.term.id} profile={profile} takenBefore={takenBefore} inPlan={inPlan} act={act} alignRight={lastInRow && !phoneLayout} />}
    </section>
  );
}

function CourseItem({
  it,
  termId,
  movable,
  dim,
  focus,
  flash,
  setHover,
  required,
  act,
  delay,
  futureTerms,
}: {
  futureTerms: Term[];
  it: PlanItem;
  termId: TermId;
  movable: boolean;
  dim: boolean;
  focus: boolean;
  flash: boolean;
  setHover: (id: string | null) => void;
  required: boolean;
  act: (a: Action) => void;
  delay: number;
}) {
  const c = api.course(it.courseId!);
  const [menu, setMenu] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useDismiss(ref, menu, () => setMenu(false));
  const showReason = it.status === 'unsatisfied' && it.reason;
  return (
    <div
      ref={ref}
      className="item"
      data-key={it.key}
      data-course={it.courseId}
      data-dim={dim}
      data-focus={focus}
      data-flash={flash}
      data-has-reason={!!showReason}
      draggable={movable}
      style={{ animation: `rise 280ms var(--ease) ${delay * 30}ms backwards` }}
      onDragStart={(e) => {
        e.dataTransfer.setData('text/course', it.courseId!);
        e.dataTransfer.effectAllowed = 'move';
        setHover(null);
      }}
      onPointerEnter={() => setHover(it.courseId!)}
      onPointerLeave={() => setHover(null)}
      title={[c?.title, it.satisfies.join(', ')].filter(Boolean).join(' — ')}
    >
      <StatusIcon status={it.status} />
      <span className="item-code">{it.courseId}</span>
      <span className="item-title">{c?.title}</span>
      {showReason && <span className="item-reason">{it.reason}</span>}
      {movable ? (
        <button className="icon-btn" aria-label={`Options for ${it.courseId}`} aria-expanded={menu} onClick={() => setMenu((m) => !m)}>
          <More />
        </button>
      ) : (
        <span className="item-cr num">{c?.credits}</span>
      )}
      {menu && (
        <div className="menu" role="menu" style={{ right: 0, top: 34, width: 220 }}>
          <div className="menu-label">Move to</div>
          {futureTerms
            .filter((t) => t.id !== termId)
            .map((t) => {
              const ok = c?.offered.includes(t.season);
              return (
                <button
                  key={t.id}
                  className="menu-item"
                  role="menuitem"
                  onClick={() => {
                    setMenu(false);
                    act({ type: 'place', courseId: it.courseId!, termId: t.id });
                  }}
                >
                  {t.label}
                  <span className="right">{ok ? '' : 'Not offered'}</span>
                </button>
              );
            })}
          {it.pinned && (
            <>
              <div className="menu-sep" />
              <button
                className="menu-item"
                role="menuitem"
                onClick={() => {
                  setMenu(false);
                  act({ type: 'unplace', courseId: it.courseId! });
                }}
              >
                {required || it.slot ? 'Let the plan place it' : 'Remove from plan'}
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}

function Slot({
  it,
  termId,
  takenBefore,
  act,
  flash,
  dim,
}: {
  it: PlanItem;
  termId: TermId;
  takenBefore: (t: TermId) => Set<string>;
  act: (a: Action) => void;
  flash: boolean;
  dim: boolean;
}) {
  const [open, setOpen] = useState(false);
  const slot = it.slot!;
  const term = api.term(termId);
  const before = useMemo(() => (open ? takenBefore(termId) : new Set<string>()), [open, takenBefore, termId]);
  return (
    <div className="slot" data-open={open} data-key={it.key} data-flash={flash} style={{ opacity: dim ? 0.28 : 1, transition: 'opacity 160ms var(--ease)' }}>
      <button className="slot-head" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
        <StatusIcon status="unsatisfied" title="Choose a course" />
        <span className="slot-label">
          {slot.label} <em>· choose</em>
        </span>
        <ChevronDown className="chev" />
      </button>
      <div className="reveal" data-open={open}>
        <div>
          <div className="options" role="listbox" aria-label={`${slot.label} options`}>
            {slot.options.map((id, k) => {
              const c = api.course(id);
              if (!c) return null;
              const missing = open ? missingPrereqs(id, before) : undefined;
              const season = !c.offered.includes(term.season) ? `${c.offered.join(' / ')} only` : undefined;
              return (
                <button
                  key={id}
                  className="option"
                  role="option"
                  aria-selected={false}
                  style={{ animationDelay: `${60 + k * 40}ms` }}
                  onClick={() => {
                    setOpen(false);
                    act({ type: 'place', courseId: id, termId });
                  }}
                >
                  <span className="option-radio" />
                  <span className="option-text">
                    <b>{c.id}</b>
                    <span>{c.title}</span>
                  </span>
                  {(missing || season) && (
                    <span className="option-meta" data-warn="true">
                      {season ?? missing}
                    </span>
                  )}
                </button>
              );
            })}
            {slot.options.length === 0 && <div className="sec-note">No options left.</div>}
          </div>
        </div>
      </div>
    </div>
  );
}

function AddCourse({
  termId,
  profile,
  takenBefore,
  inPlan,
  act,
  alignRight,
}: {
  termId: TermId;
  profile: StudentProfile;
  takenBefore: (t: TermId) => Set<string>;
  inPlan: Set<string>;
  act: (a: Action) => void;
  alignRight: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');
  const [active, setActive] = useState(0);
  const ref = useRef<HTMLDivElement>(null);
  const close = useCallback(() => {
    setOpen(false);
    setQ('');
    setActive(0);
  }, []);
  useDismiss(ref, open, close);
  const term = api.term(termId);

  const results = useMemo(() => {
    if (!open) return [] as { c: Course; major: boolean }[];
    const majorIds = new Set<string>();
    for (const m of profile.majors)
      for (const r of api.program(m)?.requirements ?? []) {
        if (r.kind === 'course') majorIds.add(r.courseId);
        else r.options.forEach((o) => majorIds.add(o));
      }
    const query = q.trim().toLowerCase().replace('-', ' ');
    return api
      .courses()
      .filter((c) => !inPlan.has(c.id))
      .filter((c) => !query || c.id.toLowerCase().replace('-', ' ').includes(query) || c.title.toLowerCase().includes(query))
      .map((c) => ({ c, major: majorIds.has(c.id) }))
      .sort((a, b) => Number(b.major) - Number(a.major) || a.c.id.localeCompare(b.c.id))
      .slice(0, 40);
  }, [open, q, profile.majors, inPlan]);

  const before = useMemo(() => (open ? takenBefore(termId) : new Set<string>()), [open, takenBefore, termId]);
  const pick = (c: Course) => {
    act({ type: 'place', courseId: c.id, termId });
    close();
  };

  return (
    <div className="add" ref={ref}>
      <button className="add-btn" aria-label={`Add a course to ${term.label}`} aria-expanded={open} onClick={() => (open ? close() : setOpen(true))}>
        <Plus size={14} />
      </button>
      {open && (
        <div
          className="menu add-pop"
          role="dialog"
          aria-label={`Add to ${term.label}`}
          style={alignRight ? { left: 'auto', right: 0 } : undefined}
        >
          <label className="search">
            <Search />
            <input
              autoFocus
              value={q}
              placeholder={`Add to ${term.label}`}
              onChange={(e) => {
                setQ(e.target.value);
                setActive(0);
              }}
              onKeyDown={(e) => {
                if (e.key === 'ArrowDown') {
                  e.preventDefault();
                  setActive((a) => Math.min(a + 1, results.length - 1));
                } else if (e.key === 'ArrowUp') {
                  e.preventDefault();
                  setActive((a) => Math.max(a - 1, 0));
                } else if (e.key === 'Enter' && results[active]) {
                  pick(results[active].c);
                }
              }}
            />
          </label>
          <div className="add-results" role="listbox">
            {results.length === 0 && <div className="sec-note" style={{ padding: 8 }}>No matches.</div>}
            {results.map(({ c, major }, k) => {
              const season = !c.offered.includes(term.season);
              const missing = missingPrereqs(c.id, before);
              const showHeader = k === 0 || results[k - 1].major !== major;
              return (
                <div key={c.id}>
                  {showHeader && <div className="menu-label">{major ? 'For your major' : 'Other courses'}</div>}
                  <button
                    className="add-result"
                    role="option"
                    aria-selected={k === active}
                    data-active={k === active}
                    onPointerEnter={() => setActive(k)}
                    onClick={() => pick(c)}
                  >
                    <span className="c-code">{c.id}</span>
                    <span className="c-title">{c.title}</span>
                    {season || missing ? (
                      <span className="option-meta" data-warn="true">{season ? `${c.offered[0]} only` : missing}</span>
                    ) : (
                      <Check size={14} className="muted" />
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

/* ---------------- header menus ---------------- */

function MajorPicker({ label, majors, onChange }: { label: string; majors: string[]; onChange: (m: string[]) => void }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useDismiss(ref, open, () => setOpen(false));
  const toggle = (id: string) => onChange(majors.includes(id) ? majors.filter((m) => m !== id) : [...majors, id].slice(-2));
  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button className="major-btn" aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
        {label}
        <ChevronDown />
      </button>
      {open && (
        <div className="menu" role="menu" style={{ left: 0, top: 42, width: 240 }}>
          <div className="menu-label">Majors · up to two</div>
          {MAJOR_CHOICES.map((m) => (
            <button key={m.id} className="menu-item" role="menuitemcheckbox" aria-checked={majors.includes(m.id)} disabled={!m.available} onClick={() => toggle(m.id)}>
              {m.name}
              <span className="right">{m.available ? majors.includes(m.id) && <Check size={14} /> : 'Soon'}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function PaceMenu({ cap, onChange }: { cap: number; onChange: (n: number) => void }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useDismiss(ref, open, () => setOpen(false));
  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button className="btn btn-quiet num" aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
        {cap} cr / term
        <ChevronDown />
      </button>
      {open && (
        <div className="menu" role="menu" style={{ right: 0, top: 40 }}>
          <div className="menu-label">Most credits per term</div>
          {[12, 14, 16, 18].map((n) => (
            <button
              key={n}
              className="menu-item num"
              role="menuitemradio"
              aria-checked={n === cap}
              onClick={() => {
                onChange(n);
                setOpen(false);
              }}
            >
              {n} credits
              <span className="right">{n === cap && <Check size={14} />}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
