import { useEffect, useState } from 'react';
import { api } from '../api/client.ts';
import { MAJOR_CHOICES } from '../data/catalog.ts';
import type { CreditRecord, StudentProfile } from '../types.ts';
import { Check, StatusIcon } from './Icons.tsx';

export default function Onboarding({ onDone }: { onDone: (p: StudentProfile) => void }) {
  const [step, setStep] = useState<1 | 2>(1);
  const [majors, setMajors] = useState<string[]>([]);
  const [imported, setImported] = useState<StudentProfile | null>(null);

  useEffect(() => {
    if (step !== 2 || imported) return;
    let live = true;
    api.importCredits().then((p) => live && setImported(p));
    return () => {
      live = false;
    };
  }, [step, imported]);

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
            <div className="choice-list" role="group" aria-label="Majors">
              {MAJOR_CHOICES.map((m) => (
                <button
                  key={m.id}
                  className="choice"
                  role="checkbox"
                  aria-checked={majors.includes(m.id)}
                  disabled={!m.available}
                  onClick={() => toggle(m.id)}
                >
                  {m.name}
                  <span className="right">{m.available ? '' : 'Soon'}</span>
                  {m.available && (
                    <span className="choice-check">{majors.includes(m.id) && <Check size={12} />}</span>
                  )}
                </button>
              ))}
            </div>
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
            <p className="lede">{imported ? 'Imported from your record.' : 'Importing from your record…'}</p>
            {imported ? (
              <CreditList credits={imported.credits} />
            ) : (
              <div className="import-bar" aria-hidden="true">
                <i />
              </div>
            )}
            <div className="onboard-actions">
              <button className="btn btn-quiet" onClick={() => setStep(1)}>
                Back
              </button>
              <button
                className="btn btn-primary"
                disabled={!imported}
                onClick={() => imported && onDone({ ...imported, majors })}
              >
                Build my plan
              </button>
            </div>
          </>
        )}
      </div>
    </main>
  );
}

function CreditList({ credits }: { credits: CreditRecord[] }) {
  const groups: { title: string; rows: CreditRecord[] }[] = [];
  const prior = credits.filter((c) => !c.term);
  if (prior.length) groups.push({ title: 'Before Grinnell', rows: prior });
  for (const t of api.terms()) {
    const rows = credits.filter((c) => c.term === t.id);
    if (!rows.length) continue;
    const inProgress = rows.some((r) => r.status === 'enrolled');
    groups.push({ title: inProgress ? `${t.label} · in progress` : t.label, rows });
  }
  const credit = (r: CreditRecord) => api.course(r.courseId)?.credits ?? 0;
  const earned = credits.filter((c) => c.status === 'completed').reduce((s, r) => s + credit(r), 0);
  const current = credits.filter((c) => c.status === 'enrolled').reduce((s, r) => s + credit(r), 0);
  let i = 0;
  return (
    <div>
      {groups.map((g) => (
        <section className="credit-group" key={g.title}>
          <h3>{g.title}</h3>
          {g.rows.map((r) => {
            const c = api.course(r.courseId);
            return (
              <div className="credit-row" key={r.courseId} style={{ animationDelay: `${i++ * 45}ms` }}>
                <StatusIcon status={r.status} />
                <span className="code">{r.courseId}</span>
                <span className="title">{r.note ?? c?.title}</span>
                <span className="muted num">{c?.credits}</span>
              </div>
            );
          })}
        </section>
      ))}
      <div className="credit-sum num">
        {earned} credits earned · {current} in progress
      </div>
    </div>
  );
}
