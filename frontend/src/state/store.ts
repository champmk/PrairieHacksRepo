import { useCallback, useEffect, useMemo, useReducer, useRef } from 'react';
import { api } from '../api/client.ts';
import type { PlanResult, StudentProfile, TermId } from '../types.ts';

export type Action =
  | { type: 'load'; profile: StudentProfile }
  | { type: 'setMajors'; majors: string[] }
  | { type: 'place'; courseId: string; termId: TermId }
  | { type: 'unplace'; courseId: string }
  | { type: 'setCap'; cap: number }
  | { type: 'toggleSection'; termId: TermId; sectionId: string }
  | { type: 'undo' }
  | { type: 'reset' };

interface State {
  profile: StudentProfile | null;
  history: StudentProfile[];
}

const KEY = 'coursegraph.v1';

function readSaved(): StudentProfile | null {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as StudentProfile) : null;
  } catch {
    return null;
  }
}

function save(profile: StudentProfile | null) {
  try {
    if (profile) localStorage.setItem(KEY, JSON.stringify(profile));
    else localStorage.removeItem(KEY);
  } catch {
    /* storage unavailable: the app still works for this session */
  }
}

function apply(p: StudentProfile, a: Action): StudentProfile {
  switch (a.type) {
    case 'setMajors':
      return { ...p, majors: a.majors.slice(0, 2) };
    case 'place':
      return {
        ...p,
        placements: { ...p.placements, [a.courseId]: a.termId },
        dismissed: p.dismissed.filter((id) => id !== a.courseId),
      };
    case 'unplace': {
      const placements = { ...p.placements };
      delete placements[a.courseId];
      const schedule: Record<TermId, string[]> = {};
      for (const [t, ids] of Object.entries(p.schedule)) {
        schedule[t] = ids.filter((sid) => api.section(sid)?.courseId !== a.courseId || t === p.currentTerm);
      }
      // Required courses go back to the planner; others simply leave the plan.
      return { ...p, placements, schedule };
    }
    case 'setCap':
      return { ...p, creditCap: a.cap };
    case 'toggleSection': {
      const sec = api.section(a.sectionId);
      if (!sec) return p;
      const current = p.schedule[a.termId] ?? [];
      const has = current.includes(a.sectionId);
      // One section per course per term: picking another section switches.
      const next = has
        ? current.filter((id) => id !== a.sectionId)
        : [...current.filter((id) => api.section(id)?.courseId !== sec.courseId), a.sectionId];
      const placements = { ...p.placements };
      if (!has) placements[sec.courseId] = a.termId;
      return { ...p, schedule: { ...p.schedule, [a.termId]: next }, placements };
    }
    default:
      return p;
  }
}

function reducer(state: State, a: Action): State {
  if (a.type === 'load') return { profile: a.profile, history: [] };
  if (a.type === 'reset') return { profile: null, history: [] };
  if (!state.profile) return state;
  if (a.type === 'undo') {
    const prev = state.history[state.history.length - 1];
    return prev ? { profile: prev, history: state.history.slice(0, -1) } : state;
  }
  const next = apply(state.profile, a);
  if (next === state.profile) return state;
  return { profile: next, history: [...state.history.slice(-30), state.profile] };
}

export function useStore() {
  const [state, dispatch] = useReducer(reducer, undefined, () => ({ profile: readSaved(), history: [] }));
  useEffect(() => save(state.profile), [state.profile]);

  // Recalculate on every profile change; keep the previous plan so the
  // engine can describe what moved.
  // Diff against the plan last shown on screen (committed), so React's
  // double render in development cannot compare a plan with itself.
  const committed = useRef<PlanResult | undefined>(undefined);
  const lastCause = useRef<Action['type'] | null>(null);
  const plan = useMemo(
    () => (state.profile ? api.recalculate(state.profile, committed.current) : null),
    [state.profile],
  );
  useEffect(() => {
    committed.current = plan ?? undefined;
  }, [plan]);

  const act = useCallback((a: Action) => {
    lastCause.current = a.type;
    dispatch(a);
  }, []);

  return { profile: state.profile, plan, canUndo: state.history.length > 0, act, lastCause };
}
