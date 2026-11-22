import { useEffect, useRef, useState } from 'react';
import { useCourseGraph } from './state/useCourseGraph.ts';
import Onboarding from './components/Onboarding.tsx';
import CoursePicker from './components/CoursePicker.tsx';
import PlanPage from './components/plan/PlanPage.tsx';
import { Check, Mark } from './components/Icons.tsx';
import { useDismiss } from './components/useDismiss.ts';

type View = 'picker' | 'plan';
const readView = (): View => (location.hash === '#plan' ? 'plan' : 'picker');

export default function App() {
  const cg = useCourseGraph();
  const [view, setView] = useState<View>(readView);

  useEffect(() => {
    const onHash = () => setView(readView());
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);
  const go = (v: View) => {
    history.replaceState(null, '', v === 'plan' ? '#plan' : '#picker');
    setView(v);
  };

  if (cg.status === 'offline' || cg.status === 'error') {
    return (
      <main className="onboard">
        <div className="onboard-inner">
          <h1>{cg.status === 'offline' ? 'The backend is not running' : 'Something went wrong'}</h1>
          <p className="lede">
            {cg.status === 'offline' ? (
              <>
                Start it from <code>backend/</code> with <code>python -m uvicorn coursegraph.api:app --port 8100</code>.
              </>
            ) : (
              cg.error
            )}
          </p>
          <button className="btn btn-primary" onClick={cg.actions.retry}>
            Try again
          </button>
        </div>
      </main>
    );
  }

  if (!cg.catalog || !cg.student) return <main className="onboard"><div className="import-bar" style={{ width: 200 }}><i /></div></main>;
  if (!cg.onboarded) return <Onboarding cg={cg} />;

  return (
    <div className="shell">
      <header className="topbar">
        <div className="wordmark">
          <Mark />
          <span className="wordmark-text">CourseGraph</span>
        </div>
        <nav className="tabs" role="tablist" aria-label="Pages">
          <button className="tab" role="tab" aria-selected={view === 'picker'} onClick={() => go('picker')}>
            Course Picker
          </button>
          <button className="tab" role="tab" aria-selected={view === 'plan'} onClick={() => go('plan')}>
            4-Year Plan
          </button>
        </nav>
        <div className="topbar-right">
          <span className="sample-note">Sample data · catalog {cg.catalog.catalog_year}</span>
          <AccountMenu cg={cg} />
        </div>
      </header>
      {view === 'picker' ? <CoursePicker key={cg.student.id} cg={cg} /> : <PlanPage key={cg.student.id} cg={cg} />}
    </div>
  );
}

function AccountMenu({ cg }: { cg: ReturnType<typeof useCourseGraph> }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useDismiss(ref, open, () => setOpen(false));
  const name = cg.student?.name ?? '';
  const initials = name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .slice(0, 2);
  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button className="avatar" aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen((o) => !o)} title={name}>
        {initials}
      </button>
      {open && (
        <div className="menu" role="menu" style={{ right: 0, top: 40, width: 240 }}>
          <div className="menu-label">Demo students</div>
          {cg.students.map((s) => (
            <button
              key={s.id}
              className="menu-item"
              role="menuitemradio"
              aria-checked={s.id === cg.student?.id}
              onClick={() => {
                cg.actions.switchStudent(s.id);
                setOpen(false);
              }}
            >
              <span>
                {s.name}
                {s.summary && <span className="menu-sub">{s.summary}</span>}
              </span>
              <span className="right">{s.id === cg.student?.id && <Check size={14} />}</span>
            </button>
          ))}
          <div className="menu-sep" />
          <button
            className="menu-item"
            role="menuitem"
            onClick={() => {
              cg.actions.resetEdits();
              setOpen(false);
            }}
          >
            Clear plan edits
          </button>
          <button
            className="menu-item"
            role="menuitem"
            onClick={() => {
              cg.actions.restartOnboarding();
              setOpen(false);
            }}
          >
            Start over
          </button>
        </div>
      )}
    </div>
  );
}
