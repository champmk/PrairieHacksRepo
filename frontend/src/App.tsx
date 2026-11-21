import { useEffect, useRef, useState } from 'react';
import { useStore } from './state/store.ts';
import Onboarding from './components/Onboarding.tsx';
import Schedule from './components/Schedule.tsx';
import FourYearPlan from './components/FourYearPlan.tsx';
import { Mark } from './components/Icons.tsx';
import { useDismiss } from './components/useDismiss.ts';

type View = 'schedule' | 'plan';

function readView(): View {
  return location.hash === '#plan' ? 'plan' : 'schedule';
}

export default function App() {
  const { profile, plan, canUndo, act, lastCause } = useStore();
  const [view, setView] = useState<View>(readView);

  useEffect(() => {
    const onHash = () => setView(readView());
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);
  const go = (v: View) => {
    history.replaceState(null, '', v === 'plan' ? '#plan' : '#schedule');
    setView(v);
  };

  if (!profile || !plan) {
    return (
      <Onboarding
        onDone={(p) => {
          act({ type: 'load', profile: p });
          go('plan');
        }}
      />
    );
  }

  return (
    <div className="shell">
      <header className="topbar">
        <div className="wordmark">
          <Mark />
          <span className="wordmark-text">CourseGraph</span>
        </div>
        <nav className="tabs" role="tablist" aria-label="Pages">
          <button className="tab" role="tab" aria-selected={view === 'schedule'} onClick={() => go('schedule')}>
            Schedule
          </button>
          <button className="tab" role="tab" aria-selected={view === 'plan'} onClick={() => go('plan')}>
            Four-year plan
          </button>
        </nav>
        <div className="topbar-right">
          <span className="sample-note">Sample data</span>
          <AccountMenu name={profile.name} onRestart={() => act({ type: 'reset' })} />
        </div>
      </header>
      {view === 'schedule' ? (
        <Schedule profile={profile} plan={plan} act={act} />
      ) : (
        <FourYearPlan profile={profile} plan={plan} act={act} canUndo={canUndo} lastCause={lastCause} />
      )}
    </div>
  );
}

function AccountMenu({ name, onRestart }: { name: string; onRestart: () => void }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useDismiss(ref, open, () => setOpen(false));
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
        <div className="menu" role="menu" style={{ right: 0, top: 40 }}>
          <div className="menu-label">{name}</div>
          <button className="menu-item" role="menuitem" onClick={onRestart}>
            Start over
          </button>
        </div>
      )}
    </div>
  );
}
