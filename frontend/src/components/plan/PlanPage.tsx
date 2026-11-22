import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { ApiError, api } from '../../api/client.ts';
import type { OptionsResult, PlanTerm, PlanWarning, Tablet, TermId } from '../../api/types.ts';
import type { CG } from '../../state/useCourseGraph.ts';
import { Check, CheckDot, ChevronDown, ChevronLeft, ChevronRight, Close, Pencil, Plus, Remove, Search, Swap, Undo, Warn } from '../Icons.tsx';
import { useDismiss } from '../useDismiss.ts';
import { useMedia } from '../useMedia.ts';
import { assignLanes, gutterFor, route, type Box, type Routed } from './layout.ts';

type Selection =
  | { kind: 'tablet'; term: TermId; tablet: Tablet }
  | { kind: 'add'; term: TermId }
  | null;

export default function PlanPage({ cg }: { cg: CG }) {
  const { plan, student, catalog, majors, courseById, planning } = cg;
  const narrow = useMedia('(max-width: 1199px)');
  const [sideOpen, setSideOpen] = useState(!narrow);
  const [sel, setSel] = useState<Selection>(null);
  const [editing, setEditing] = useState<TermId | null>(null);
  const [hoverTablet, setHoverTablet] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const warningsById = useMemo(() => Object.fromEntries((plan?.warnings ?? []).map((w) => [w.id, w])), [plan]);
  const errors = plan?.warnings.filter((w) => w.severity === 'error').length ?? 0;
  const warns = (plan?.warnings.length ?? 0) - errors;

  const openSide = (s: Selection) => {
    setSel(s);
    setSideOpen(true);
  };

  const focusTablet = useCallback((tabletId?: string | null, termId?: string | null) => {
    const root = document.querySelector('.canvas');
    const el =
      (tabletId && root?.querySelector<HTMLElement>(`[data-tablet="${CSS.escape(tabletId)}"]`)) ||
      (termId && root?.querySelector<HTMLElement>(`[data-term="${CSS.escape(termId)}"]`));
    if (!el) return;
    el.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    const key = tabletId ?? termId ?? '';
    setFlash(key);
    setTimeout(() => setFlash((f) => (f === key ? null : f)), 1400);
  }, []);

  // Deleting a planned tablet removes that section from the page-1 schedule.
  const removeTablet = async (term: PlanTerm, t: Tablet) => {
    if (t.status === 'planned' && t.course && student) {
      const ids = (student.schedule[term.id] ?? []).filter((sid) => !sid.includes(`-${t.course}-`));
      try {
        await cg.actions.saveSchedule(term.id, ids);
        setNotice(`${t.course} removed from your ${term.label} schedule`);
      } catch (e) {
        setNotice(e instanceof ApiError ? e.message : 'Could not update the schedule');
      }
      return;
    }
    cg.actions.edit({ op: 'remove', term: term.id, tablet: t.id });
  };

  if (!plan || !student || !catalog) return <main className="plan2 loading-state">Building your plan…</main>;

  return (
    <main className="plan2">
      <div className="plan-head">
        <MajorMenu cg={cg} />
        <span className="head-meta num" title="Counted, in progress, planned and open electives toward 124">
          {plan.totals.counted + plan.totals.in_progress + plan.totals.planned + (plan.totals.open ?? 0)} of {plan.totals.required} credits
        </span>
        {(errors > 0 || warns > 0) && (
          <button className="warn-count" onClick={() => openSide(null)} title="Show warnings">
            <Warn size={14} tone={errors ? 'error' : 'warn'} />
            {errors > 0 ? `${errors} to fix` : ''}
            {errors > 0 && warns > 0 ? ' · ' : ''}
            {warns > 0 ? `${warns} to check` : ''}
          </button>
        )}
        {planning && <span className="spinner" aria-label="Updating plan" />}
        <Legend />
        <div className="head-right">
          <CapMenu cap={cg.cap} onChange={cg.actions.setCap} />
          <button className="icon-btn" aria-label="Undo" title="Undo" disabled={!cg.canUndo} onClick={cg.actions.undo}>
            <Undo />
          </button>
        </div>
      </div>
      {notice && (
        <div className="notice" role="status">
          <span>{notice}</span>
          <button className="icon-btn" style={{ marginLeft: 'auto', width: 24, height: 24 }} aria-label="Dismiss" onClick={() => setNotice(null)}>
            <Close size={14} />
          </button>
        </div>
      )}
      <div className="plan2-body">
        <aside className="side" data-open={sideOpen}>
          <div className="side-inner">
            {sel ? (
              <OptionsPanel cg={cg} sel={sel} onClose={() => setSel(null)} onPicked={() => setSel(null)} />
            ) : (
              <RequirementsPanel cg={cg} onFocus={focusTablet} />
            )}
          </div>
          <button className="side-toggle" aria-label={sideOpen ? 'Hide panel' : 'Show panel'} onClick={() => setSideOpen((o) => !o)}>
            {sideOpen ? <ChevronLeft /> : <ChevronRight />}
          </button>
        </aside>
        <Canvas
          terms={plan.terms}
          edges={plan.edges}
          warningsById={warningsById}
          nodeWarnings={plan.warnings.filter((w) => w.term && !w.tablet)}
          editing={editing}
          setEditing={setEditing}
          selected={sel}
          hoverTablet={hoverTablet}
          setHoverTablet={setHoverTablet}
          flash={flash}
          courseTitle={(id) => courseById[id]?.title ?? ''}
          onTablet={(term, t) => openSide({ kind: 'tablet', term: term.id, tablet: t })}
          onAdd={(term) => openSide({ kind: 'add', term: term.id })}
          onRemove={removeTablet}
          majorsPicked={majors.length > 0}
          deps={[sideOpen, planning]}
          prior={plan.prior ?? []}
        />
      </div>
    </main>
  );
}

/* ---------------- canvas: nodes + arrows ---------------- */

function Canvas({
  terms,
  edges,
  warningsById,
  nodeWarnings,
  editing,
  setEditing,
  selected,
  hoverTablet,
  setHoverTablet,
  flash,
  courseTitle,
  onTablet,
  onAdd,
  onRemove,
  majorsPicked,
  deps,
  prior,
}: {
  prior: Tablet[];
  terms: PlanTerm[];
  edges: { id: string; from_tablet: string; from_term: TermId; to_term: TermId; message: string; missing: string[] }[];
  warningsById: Record<string, PlanWarning>;
  nodeWarnings: PlanWarning[];
  editing: TermId | null;
  setEditing: (t: TermId | null) => void;
  selected: Selection;
  hoverTablet: string | null;
  setHoverTablet: (id: string | null) => void;
  flash: string | null;
  courseTitle: (id: string) => string;
  onTablet: (term: PlanTerm, t: Tablet) => void;
  onAdd: (term: PlanTerm) => void;
  onRemove: (term: PlanTerm, t: Tablet) => void;
  majorsPicked: boolean;
  deps: unknown[];
}) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLDivElement>(null);
  const index = useMemo(() => Object.fromEntries(terms.map((t, i) => [t.id, i])), [terms]);
  const spans = useMemo(
    () =>
      edges
        .filter((e) => index[e.from_term] !== undefined && index[e.to_term] !== undefined)
        .map((e) => ({ id: e.id, from: index[e.from_term], to: index[e.to_term] })),
    [edges, index],
  );
  const { lane, lanes } = useMemo(() => assignLanes(spans), [spans]);
  const gutter = gutterFor(lanes);
  const [routes, setRoutes] = useState<Routed[]>([]);
  const [size, setSize] = useState({ w: 0, h: 0 });

  const measure = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const base = canvas.getBoundingClientRect();
    const rel = (el: Element): Box => {
      const r = el.getBoundingClientRect();
      return { left: r.left - base.left, top: r.top - base.top, width: r.width, height: r.height };
    };
    const nodeEls = [...canvas.querySelectorAll<HTMLElement>('[data-node-index]')];
    const nodes: Box[] = [];
    for (const n of nodeEls) nodes[Number(n.dataset.nodeIndex)] = rel(n);
    const list = spans.flatMap((s) => {
      const e = edges.find((x) => x.id === s.id)!;
      const tab = canvas.querySelector(`[data-tablet="${CSS.escape(e.from_tablet)}"]`);
      return tab && nodes[s.from] && nodes[s.to] ? [{ id: s.id, from: s.from, to: s.to, tablet: rel(tab) }] : [];
    });
    const rowTop = nodes.length ? Math.min(...nodes.filter(Boolean).map((n) => n.top)) : gutter;
    setRoutes(route(list, nodes, lane, rowTop));
    setSize({ w: canvas.scrollWidth, h: canvas.scrollHeight });
  }, [spans, edges, lane, gutter]);

  useLayoutEffect(() => {
    measure();
  }, [measure, terms, editing, ...deps]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || typeof ResizeObserver === 'undefined') return;
    const ro = new ResizeObserver(() => measure());
    ro.observe(canvas);
    return () => ro.disconnect();
  }, [measure]);

  // Start scrolled to the current term.
  const scrolled = useRef(false);
  useEffect(() => {
    if (scrolled.current) return;
    const el = canvasRef.current?.querySelector<HTMLElement>('[data-state="current"]');
    if (el && wrapRef.current) {
      wrapRef.current.scrollLeft = Math.max(0, el.offsetLeft - 120);
      scrolled.current = true;
    }
  }, [terms]);

  const hoverEdges = new Set(edges.filter((e) => e.from_tablet === hoverTablet).map((e) => e.id));

  return (
    <div className="canvas-wrap" ref={wrapRef}>
      <div className="canvas" ref={canvasRef} style={{ paddingTop: gutter }}>
        <div className="canvas-top">
        {prior.length > 0 && (
          <div className="prior-strip" title="Credit from before Grinnell">
            <span className="muted">Before Grinnell</span>
            {prior.map((p) => (
              <span key={p.id} className="prior-item" data-status={p.status}>
                {p.status === 'completed' && <Check size={13} className="t-check" />}
                <b>{p.course}</b> {p.mark ? `(${p.mark})` : ''}
              </span>
            ))}
          </div>
        )}
        {!majorsPicked && <div className="canvas-hint">Pick a major to see required tablets.</div>}
        </div>
        <div className="row">
          {terms.map((t, i) => (
            <Node
              key={t.id}
              term={t}
              index={i}
              editing={editing === t.id}
              onEdit={() => setEditing(editing === t.id ? null : t.id)}
              selected={selected}
              warningsById={warningsById}
              nodeWarnings={nodeWarnings.filter((w) => w.term === t.id)}
              setHoverTablet={setHoverTablet}
              flash={flash}
              courseTitle={courseTitle}
              onTablet={(tab) => onTablet(t, tab)}
              onAdd={() => onAdd(t)}
              onRemove={(tab) => onRemove(t, tab)}
            />
          ))}
        </div>
        <svg className="edges" width={size.w} height={size.h} aria-hidden="true">
          {routes.map((r) => {
            const e = edges.find((x) => x.id === r.id);
            const hot = hoverEdges.has(r.id);
            return (
              <g key={r.id} data-hot={hot}>
                <path d={r.d} className="edge-path" />
                <g transform={`translate(${r.marker.x - 8} ${r.marker.y})`}>
                  <title>{e?.message}</title>
                  <path d="M8 0.8L15.6 14.4H0.4z" fill="var(--warn)" stroke="var(--paper)" strokeWidth="1.2" />
                  <path d="M8 5v4.4" stroke="#fff" strokeWidth="1.6" strokeLinecap="round" />
                  <circle cx="8" cy="11.6" r=".95" fill="#fff" />
                </g>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}

function Node({
  term,
  index,
  editing,
  onEdit,
  selected,
  warningsById,
  nodeWarnings,
  setHoverTablet,
  flash,
  courseTitle,
  onTablet,
  onAdd,
  onRemove,
}: {
  term: PlanTerm;
  index: number;
  editing: boolean;
  onEdit: () => void;
  selected: Selection;
  warningsById: Record<string, PlanWarning>;
  nodeWarnings: PlanWarning[];
  setHoverTablet: (id: string | null) => void;
  flash: string | null;
  courseTitle: (id: string) => string;
  onTablet: (t: Tablet) => void;
  onAdd: () => void;
  onRemove: (t: Tablet) => void;
}) {
  const editable = term.state === 'next' || term.state === 'future';
  const nodeErr = nodeWarnings.find((w) => w.severity === 'error');
  return (
    <section
      className="node2"
      data-node-index={index}
      data-term={term.id}
      data-state={term.state}
      data-flash={flash === term.id}
      aria-label={term.label}
    >
      {term.complete && (
        <span className="node-badge" title="Term complete">
          <CheckDot size={20} />
        </span>
      )}
      <header className="node2-head">
        <strong>{term.label}</strong>
        <span className="node2-state">{term.state === 'current' ? 'Now' : term.state === 'next' ? 'Next' : ''}</span>
        {nodeWarnings.length > 0 && (
          <span className="node2-warn" title={nodeWarnings.map((w) => w.message).join('\n')}>
            <Warn size={14} tone={nodeErr ? 'error' : 'warn'} />
          </span>
        )}
        <span className="node2-cr num">{term.credits} cr</span>
      </header>
      <div className="tablets">
        {term.tablets.map((t) => {
          const ws = t.warnings.map((id) => warningsById[id]).filter(Boolean);
          const err = ws.some((w) => w.severity === 'error');
          const isSel = selected?.kind === 'tablet' && selected.tablet.id === t.id;
          const canEdit = editing && editable && !t.locked;
          return (
            <div className="tab-row" key={t.id} data-flash={flash === t.id}>
              {canEdit ? (
                <button
                  className="tab-act"
                  aria-label={`Swap ${t.course ?? t.slot?.label ?? 'Elective'}`}
                  title={t.status === 'planned' ? 'Change this on the Course Picker' : 'Swap'}
                  disabled={t.status === 'planned'}
                  onClick={() => onTablet(t)}
                >
                  <Swap size={15} />
                </button>
              ) : (
                <span className="r-mark" title={t.required ? `Required: ${t.counts_for.join(', ')}` : undefined}>
                  {t.required ? 'R' : ''}
                </span>
              )}
              <button
                className="tablet"
                data-status={t.status}
                data-tablet={t.id}
                data-warn={ws.length ? (err ? 'error' : 'warn') : undefined}
                data-selected={isSel}
                onClick={() => onTablet(t)}
                onPointerEnter={() => setHoverTablet(t.id)}
                onPointerLeave={() => setHoverTablet(null)}
                title={[
                  t.course ? `${t.course} · ${t.title ?? courseTitle(t.course)}` : t.slot?.label,
                  t.counts_for.length ? `Counts for ${t.counts_for.join(', ')}` : '',
                  ...ws.map((w) => w.message),
                ]
                  .filter(Boolean)
                  .join('\n')}
              >
                <span className="t-code">{t.course ?? t.slot?.label ?? 'Elective'}</span>
                <span className="t-title">{t.course ? t.title ?? courseTitle(t.course) : t.required ? 'choose' : 'any course'}</span>
                {ws.length > 0 ? (
                  <Warn size={14} tone={err ? 'error' : 'warn'} />
                ) : t.status === 'completed' ? (
                  <Check size={15} className="t-check" />
                ) : t.status === 'not_counted' ? (
                  <span className="t-mark">{t.mark ?? '—'}</span>
                ) : null}
              </button>
              {canEdit && (
                <button className="tab-act" aria-label={`Delete ${t.course ?? t.slot?.label ?? 'Elective'}`} title="Delete" onClick={() => onRemove(t)}>
                  <Remove size={18} />
                </button>
              )}
            </div>
          );
        })}
        {term.tablets.length === 0 && <div className="node2-empty">{term.state === 'past' ? 'No courses' : 'Nothing yet'}</div>}
      </div>
      {editable && (
        <footer className="node2-foot">
          <button className="node-btn" aria-label={`Add a course to ${term.label}`} title="Add a course" onClick={onAdd}>
            <Plus size={15} />
          </button>
          <button className="node-btn" aria-pressed={editing} aria-label={`Edit ${term.label}`} title={editing ? 'Done editing' : 'Edit tablets'} onClick={onEdit}>
            {editing ? <Check size={15} /> : <Pencil size={15} />}
          </button>
        </footer>
      )}
    </section>
  );
}

/* ---------------- sidebar ---------------- */

function RequirementsPanel({ cg, onFocus }: { cg: CG; onFocus: (tablet?: string | null, term?: string | null) => void }) {
  const { plan } = cg;
  if (!plan) return null;
  const order = { error: 0, warning: 1 } as const;
  const warnings = [...plan.warnings].sort((a, b) => order[a.severity] - order[b.severity]);
  const pct = (n: number, d: number) => `${(n / Math.max(d, 1)) * 100}%`;
  return (
    <div className="side-panel">
      {plan.progress.length === 0 && <p className="muted">No major selected. Every tablet is open to any course.</p>}
      {plan.progress.map((p) => (
        <section className="prog" key={p.program}>
          <div className="prog-head">
            <strong>Required for {p.name}</strong>
            <span className="muted num">
              {p.done + p.in_progress + p.planned} of {p.total}
            </span>
          </div>
          <div className="bar" aria-hidden="true">
            <i style={{ width: pct(p.done, p.total), background: 'var(--done)' }} />
            <i style={{ width: pct(p.in_progress, p.total), background: 'var(--progress)' }} />
            <i style={{ width: pct(p.planned, p.total), background: 'var(--planned)' }} />
          </div>
          {p.slots.map((s, k) => (
            <button className="req" key={`${s.id}-${k}`} onClick={() => onFocus(s.term ? `slot:${s.id}` : null, s.term)}>
              <SlotIcon status={s.status} />
              <span className="req-label">{s.course ?? s.label}</span>
              <span className="req-term">{s.term ? shortTerm(s.term) : s.status === 'completed' ? 'AP' : ''}</span>
            </button>
          ))}
        </section>
      ))}
      <section className="prog">
        <div className="prog-head">
          <strong>Degree</strong>
          <span className="muted num">
            {plan.totals.counted + plan.totals.in_progress + plan.totals.planned} of {plan.totals.required}
          </span>
        </div>
        <div className="bar" aria-hidden="true">
          <i style={{ width: pct(plan.totals.counted, plan.totals.required), background: 'var(--done)' }} />
          <i style={{ width: pct(plan.totals.in_progress, plan.totals.required), background: 'var(--progress)' }} />
          <i style={{ width: pct(plan.totals.planned, plan.totals.required), background: 'var(--planned)' }} />
          <i style={{ width: pct(plan.totals.open ?? 0, plan.totals.required), background: 'var(--ink-4)' }} />
        </div>
        <p className="muted" style={{ margin: 0, fontSize: 12 }}>
          {plan.totals.counted} done · {plan.totals.in_progress} now · {plan.totals.planned} planned · {plan.totals.open ?? 0} open electives
        </p>
      </section>
      {warnings.length > 0 && (
        <section className="prog">
          <div className="prog-head">
            <strong>Warnings</strong>
            <span className="muted num">{warnings.length}</span>
          </div>
          {warnings.map((w) => (
            <button className="warn-row" key={w.id} onClick={() => onFocus(w.tablet, w.term)}>
              <Warn size={14} tone={w.severity === 'error' ? 'error' : 'warn'} />
              <span>{w.message}</span>
            </button>
          ))}
        </section>
      )}
    </div>
  );
}

function OptionsPanel({ cg, sel, onClose, onPicked }: { cg: CG; sel: NonNullable<Selection>; onClose: () => void; onPicked: () => void }) {
  const { student, majors, cap, edits, plan } = cg;
  const [data, setData] = useState<OptionsResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [q, setQ] = useState('');
  const term = plan?.terms.find((t) => t.id === sel.term);
  const tablet = sel.kind === 'tablet' ? sel.tablet : null;
  const readOnly = tablet && (tablet.locked || tablet.status === 'planned');

  useEffect(() => {
    if (!student || readOnly) return;
    let live = true;
    setData(null);
    setErr(null);
    api
      .options({ student_id: student.id, majors, credit_cap: cap, edits, term: sel.term, tablet: tablet?.id ?? null })
      .then((r) => live && setData(r))
      .catch((e) => live && setErr(e instanceof ApiError ? e.message : 'Could not load options'));
    return () => {
      live = false;
    };
  }, [student, majors, cap, edits, sel.term, tablet?.id, readOnly]);

  const pick = (course: string) => {
    if (tablet) cg.actions.edit({ op: 'swap', term: sel.term, tablet: tablet.id, course });
    else cg.actions.edit({ op: 'add', term: sel.term, course });
    onPicked();
  };

  const query = q.trim().toLowerCase().replace('-', ' ');
  const options = (data?.options ?? []).filter(
    (o) => !query || o.course.toLowerCase().replace('-', ' ').includes(query) || o.title.toLowerCase().includes(query),
  );
  const title = tablet ? tablet.course ?? tablet.slot?.label ?? 'Elective' : 'Add a course';

  return (
    <div className="side-panel">
      <div className="opt-head">
        <div>
          <div className="muted" style={{ fontSize: 12 }}>{term?.label}</div>
          <strong>{title}</strong>
        </div>
        <button className="icon-btn" aria-label="Close" onClick={onClose}>
          <Close />
        </button>
      </div>
      {tablet && (
        <div className="opt-facts">
          {tablet.title && <div>{tablet.title}</div>}
          {tablet.counts_for.length > 0 && <div className="muted">Counts for {tablet.counts_for.join(', ')}</div>}
          {tablet.mark && <div className="muted">Grade {tablet.mark}: no credit</div>}
          {tablet.status === 'planned' && <div className="muted">Planned on the Course Picker. Change the section there.</div>}
          {tablet.locked && tablet.status !== 'not_counted' && <div className="muted">{tablet.status === 'in_progress' ? 'In progress this term.' : 'Completed.'}</div>}
        </div>
      )}
      {!readOnly && (
        <>
          <p className="muted" style={{ margin: '4px 0 8px' }}>
            {data?.required ? `Only courses that satisfy ${data.label}.` : 'Any course in the catalog.'}
          </p>
          {!data?.required && (
            <label className="search" style={{ margin: '0 0 6px' }}>
              <Search />
              <input autoFocus value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search courses" />
            </label>
          )}
          {err && <p className="sec-warn">{err}</p>}
          {!data && !err && <p className="muted">Loading…</p>}
          <div className="opt-list">
            {options.map((o, k) => (
              <button key={o.course} className="opt" data-eligible={o.eligible} style={{ animationDelay: `${Math.min(k, 12) * 25}ms` }} onClick={() => pick(o.course)}>
                <span className="opt-text">
                  <b>{o.course}</b>
                  <span>{o.title}</span>
                </span>
                {o.eligible ? <span className="opt-ok">{o.credits} cr</span> : <span className="opt-why">{o.reason}</span>}
              </button>
            ))}
            {data && options.length === 0 && <p className="muted">No courses match.</p>}
          </div>
        </>
      )}
    </div>
  );
}

/* ---------------- header pieces ---------------- */

function MajorMenu({ cg }: { cg: CG }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useDismiss(ref, open, () => setOpen(false));
  const programs = cg.catalog?.programs ?? [];
  const label = cg.majors.length ? cg.majors.map((m) => programs.find((p) => p.id === m)?.name ?? m).join(' + ') : 'Choose a major';
  const toggle = (id: string) =>
    cg.actions.setMajors(cg.majors.includes(id) ? cg.majors.filter((m) => m !== id) : [...cg.majors, id].slice(-2));
  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button className="major-btn" aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
        {label}
        <ChevronDown />
      </button>
      {open && (
        <div className="menu" role="menu" style={{ left: 0, top: 42, width: 250 }}>
          <div className="menu-label">Majors · up to two</div>
          {programs.map((p) => (
            <button key={p.id} className="menu-item" role="menuitemcheckbox" aria-checked={cg.majors.includes(p.id)} onClick={() => toggle(p.id)}>
              {p.name}
              <span className="right">{cg.majors.includes(p.id) && <Check size={14} />}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function CapMenu({ cap, onChange }: { cap: number; onChange: (n: number) => void }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useDismiss(ref, open, () => setOpen(false));
  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button className="btn btn-quiet num" aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
        ≤ {cap} cr / term
        <ChevronDown />
      </button>
      {open && (
        <div className="menu" role="menu" style={{ right: 0, top: 40 }}>
          <div className="menu-label">Most credits per term</div>
          {[16, 18].map((n) => (
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
              {n} credits{n === 18 ? ' (more needs approval)' : ' (normal load)'}
              <span className="right">{n === cap && <Check size={14} />}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function Legend() {
  return (
    <div className="legend" aria-label="Legend">
      <span><b className="lg-r">R</b> required</span>
      <span><Check size={13} className="t-check" /> completed</span>
      <span><Warn size={13} /> conflict</span>
      <span><i className="lg-dash" data-kind="planned" /> planned</span>
      <span><i className="lg-dash" data-kind="progress" /> in progress</span>
    </div>
  );
}

function SlotIcon({ status }: { status: string }) {
  if (status === 'completed') return <CheckDot size={14} />;
  return <i className="slot-ico" data-status={status} aria-label={status} />;
}

function shortTerm(id: string) {
  return `${id.endsWith('FA') ? 'Fall' : 'Spr'} ’${id.slice(2, 4)}`;
}
