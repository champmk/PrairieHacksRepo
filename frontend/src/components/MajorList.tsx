import { useMemo, useState } from 'react';
import type { Program } from '../api/types.ts';
import { Check, Search } from './Icons.tsx';

const ORDER = ['Humanities', 'Science', 'Social Studies', 'Interdisciplinary'];

/** Majors grouped by division, with a search box. Used by onboarding and the plan header. */
export default function MajorList({
  programs,
  selected,
  onToggle,
  variant,
  autoFocus,
}: {
  programs: Program[];
  selected: string[];
  onToggle: (id: string) => void;
  variant: 'page' | 'menu';
  autoFocus?: boolean;
}) {
  const [q, setQ] = useState('');
  const groups = useMemo(() => {
    const query = q.trim().toLowerCase();
    const hit = programs.filter((p) => !query || p.name.toLowerCase().includes(query));
    const by: Record<string, Program[]> = {};
    for (const p of hit) (by[p.division ?? 'Other'] ??= []).push(p);
    const rank = (d: string) => (ORDER.includes(d) ? ORDER.indexOf(d) : ORDER.length);
    const names = Object.keys(by).sort((a, b) => rank(a) - rank(b) || a.localeCompare(b));
    return names.map((name) => ({ name, items: by[name].sort((a, b) => a.name.localeCompare(b.name)) }));
  }, [programs, q]);

  return (
    <div className={`majors majors-${variant}`}>
      <label className="search majors-search">
        <Search />
        <span className="sr">Search majors</span>
        <input autoFocus={autoFocus} value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search majors" />
      </label>
      <div className="majors-scroll" role="group" aria-label="Majors">
        {groups.length === 0 && <div className="muted" style={{ padding: '10px 4px' }}>No majors match.</div>}
        {groups.map((g) => (
          <section key={g.name}>
            <div className="majors-group">{g.name}</div>
            {g.items.map((p) => {
              const on = selected.includes(p.id);
              return variant === 'page' ? (
                <button key={p.id} className="choice" role="checkbox" aria-checked={on} onClick={() => onToggle(p.id)}>
                  {p.name}
                  <span className="right" />
                  <span className="choice-check">{on && <Check size={12} />}</span>
                </button>
              ) : (
                <button key={p.id} className="menu-item" role="menuitemcheckbox" aria-checked={on} onClick={() => onToggle(p.id)}>
                  {p.name}
                  <span className="right">{on && <Check size={14} />}</span>
                </button>
              );
            })}
          </section>
        ))}
      </div>
    </div>
  );
}
