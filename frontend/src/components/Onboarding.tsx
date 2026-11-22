import { useState } from 'react';
import type { Enrollment } from '../api/types.ts';
import type { CG } from '../state/useCourseGraph.ts';
import { CheckDot } from './Icons.tsx';
import MajorList from './MajorList.tsx';

export default function Onboarding({ cg }: { cg: CG }) {
  const { catalog, student, courseById } = cg;
  const [step, setStep] = useState<1 | 2>(1);
  const [majors, setMajors] = useState<string[]>(cg.majors);
  const toggle = (id: string) =>
    setMajors((m) => (m.includes(id) ? m.filter((x) => x !== id) : m.length >= 2 ? [m[1], id] : [...m, id]));

  return (
    <main className="onboard">
      <div className="onboard-inner" key={step}>
        <div className="steps" aria-label={`Step ${step} of 2`}>
          <span data-on="true" />
          <span data-on={step === 2} />
        </div>
        {step === 1 ? (
          <>
            <h1>What do you plan to major in?</h1>
            <p className="lede">Pick up to two. You can change this later.</p>
            <MajorList programs={catalog?.programs ?? []} selected={majors} onToggle={toggle} variant="page" />
            <div className="onboard-actions">
              <button className="btn btn-quiet" onClick={() => { setMajors([]); setStep(2); }}>
                Undecided
              </button>
              <button className="btn btn-primary" disabled={majors.length === 0} onClick={() => setStep(2)}>
                Continue
              </button>
            </div>
          </>
        ) : (
          <>
            <h1>Your credits</h1>
            <p className="lede">{student ? `Loaded from your record, ${student.name}.` : 'Loading your record…'}</p>
            {student ? <CreditList enrollments={student.enrollments} terms={student.terms} credits={(id) => courseById[id]?.credits ?? 0} title={(id) => courseById[id]?.title ?? ''} /> : <div className="import-bar" aria-hidden="true"><i /></div>}
            <div className="onboard-actions">
              <button className="btn btn-quiet" onClick={() => setStep(1)}>
                Back
              </button>
              <button className="btn btn-primary" disabled={!student} onClick={() => cg.actions.finishOnboarding(majors)}>
                Build my plan
              </button>
            </div>
          </>
        )}
      </div>
    </main>
  );
}

function CreditList({
  enrollments,
  terms,
  credits,
  title,
}: {
  enrollments: Enrollment[];
  terms: { id: string; label: string; state: string }[];
  credits: (id: string) => number;
  title: (id: string) => string;
}) {
  const groups: { title: string; rows: Enrollment[] }[] = [];
  const prior = enrollments.filter((e) => !e.term);
  if (prior.length) groups.push({ title: 'Before Grinnell', rows: prior });
  for (const t of terms) {
    const rows = enrollments.filter((e) => e.term === t.id && e.status !== 'planned');
    if (rows.length) groups.push({ title: t.state === 'current' ? `${t.label} · in progress` : t.label, rows });
  }
  const earned = enrollments.filter((e) => e.status === 'completed').reduce((s, e) => s + credits(e.course), 0);
  const now = enrollments.filter((e) => e.status === 'in_progress').reduce((s, e) => s + credits(e.course), 0);
  let i = 0;
  return (
    <div>
      {groups.map((g) => (
        <section className="credit-group" key={g.title}>
          <h3>{g.title}</h3>
          {g.rows.map((r) => {
            const counted = r.status === 'completed';
            const nc = r.status === 'withdrawn' || r.status === 'failed' || r.status === 'dropped';
            return (
              <div className="credit-row" key={`${r.course}-${r.term}`} data-nc={nc} style={{ animationDelay: `${i++ * 45}ms` }}>
                {counted ? <CheckDot /> : nc ? <span className="nc-mark">{r.grade ?? 'W'}</span> : <i className="slot-ico" data-status="in_progress" />}
                <span className="code">{r.course}</span>
                <span className="title">{r.mode === 'transfer' ? `${title(r.course)} (${r.grade ?? 'transfer'})` : title(r.course)}</span>
                <span className="muted num">{nc ? '0' : credits(r.course)}</span>
              </div>
            );
          })}
        </section>
      ))}
      <div className="credit-sum num">
        {earned} credits earned · {now} in progress
      </div>
    </div>
  );
}
