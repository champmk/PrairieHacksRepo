import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ApiError, api } from '../api/client.ts';
import type { Catalog, Course, Edit, Plan, Student, StudentSummary, TermId } from '../api/types.ts';

// Per-viewer conveniences only (which student, majors picked, page-2 edits).
// The student record itself lives in the backend database.
const KEY = 'coursegraph.v2';
interface Saved {
  studentId: string;
  onboarded: Record<string, boolean>;
  majors: Record<string, string[]>;
  edits: Record<string, Edit[]>;
  cap: Record<string, number>;
}
const EMPTY: Saved = { studentId: 'alex', onboarded: {}, majors: {}, edits: {}, cap: {} };

function load(): Saved {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? { ...EMPTY, ...(JSON.parse(raw) as Saved) } : EMPTY;
  } catch {
    return EMPTY;
  }
}
function store(s: Saved) {
  try {
    localStorage.setItem(KEY, JSON.stringify(s));
  } catch {
    /* storage blocked: session-only */
  }
}

export type Status = 'loading' | 'ready' | 'offline' | 'error';

export function useCourseGraph() {
  const [saved, setSaved] = useState<Saved>(load);
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [students, setStudents] = useState<StudentSummary[]>([]);
  const [student, setStudent] = useState<Student | null>(null);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [planning, setPlanning] = useState(false);
  const [status, setStatus] = useState<Status>('loading');
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<Edit[][]>([]);
  const [retry, setRetry] = useState(0);

  useEffect(() => store(saved), [saved]);

  const sid = saved.studentId;
  const fail = useCallback((e: unknown) => {
    if (e instanceof ApiError && e.status === 0) setStatus('offline');
    else {
      setStatus('error');
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  // Catalog and student list, once (or on retry).
  useEffect(() => {
    let live = true;
    Promise.all([api.catalog(), api.students()])
      .then(([c, s]) => {
        if (!live) return;
        setCatalog(c);
        setStudents(s);
      })
      .catch((e) => live && fail(e));
    return () => {
      live = false;
    };
  }, [retry, fail]);

  const refreshStudent = useCallback(async () => {
    try {
      const s = await api.student(sid);
      setStudent(s);
      return s;
    } catch (e) {
      fail(e);
      return null;
    }
  }, [sid, fail]);

  useEffect(() => {
    setStudent(null);
    setPlan(null);
    setHistory([]);
    refreshStudent();
  }, [refreshStudent, retry]);

  const majors = useMemo(() => saved.majors[sid] ?? student?.majors ?? [], [saved.majors, sid, student]);
  const edits = useMemo(() => saved.edits[sid] ?? [], [saved.edits, sid]);
  const cap = saved.cap[sid] ?? student?.credit_cap ?? 18;

  // Re-plan whenever the inputs change; stale responses are dropped.
  const seq = useRef(0);
  useEffect(() => {
    if (!student || !catalog) return;
    const n = ++seq.current;
    setPlanning(true);
    const t = setTimeout(() => {
      api
        .plan({ student_id: student.id, majors, credit_cap: cap, edits })
        .then((p) => {
          if (n !== seq.current) return;
          setPlan(p);
          setStatus('ready');
        })
        .catch((e) => n === seq.current && fail(e))
        .finally(() => n === seq.current && setPlanning(false));
    }, 90);
    return () => clearTimeout(t);
  }, [student, catalog, majors, edits, cap, fail]);

  const patch = useCallback((fn: (s: Saved) => Saved) => setSaved((s) => fn(s)), []);

  const setEdits = useCallback(
    (next: Edit[], record = true) => {
      if (record) setHistory((h) => [...h.slice(-40), edits]);
      patch((s) => ({ ...s, edits: { ...s.edits, [sid]: next } }));
    },
    [edits, patch, sid],
  );

  const courseById = useMemo(() => {
    const m: Record<string, Course> = {};
    for (const c of catalog?.courses ?? []) m[c.id] = c;
    return m;
  }, [catalog]);

  const actions = useMemo(
    () => ({
      retry: () => {
        setStatus('loading');
        setError(null);
        setRetry((r) => r + 1);
      },
      switchStudent: (id: string) => patch((s) => ({ ...s, studentId: id })),
      finishOnboarding: (m: string[]) =>
        patch((s) => ({ ...s, onboarded: { ...s.onboarded, [sid]: true }, majors: { ...s.majors, [sid]: m } })),
      restartOnboarding: () =>
        patch((s) => ({ ...s, onboarded: { ...s.onboarded, [sid]: false }, edits: { ...s.edits, [sid]: [] } })),
      setMajors: (m: string[]) => {
        setHistory((h) => [...h.slice(-40), edits]);
        patch((s) => ({ ...s, majors: { ...s.majors, [sid]: m.slice(0, 2) } }));
      },
      setCap: (n: number) => patch((s) => ({ ...s, cap: { ...s.cap, [sid]: n } })),
      edit: (e: Edit) => setEdits([...edits, e]),
      undo: () => {
        const prev = history[history.length - 1];
        if (!prev) return;
        setHistory((h) => h.slice(0, -1));
        setEdits(prev, false);
      },
      resetEdits: () => setEdits([]),
      saveSchedule: async (term: TermId, sectionIds: string[]) => {
        if (!student) return null;
        const res = await api.saveSchedule(student.id, term, sectionIds);
        await refreshStudent();
        return res;
      },
    }),
    [patch, sid, edits, history, setEdits, student, refreshStudent],
  );

  return {
    status,
    error,
    catalog,
    students,
    student,
    plan,
    planning,
    majors,
    edits,
    cap,
    canUndo: history.length > 0,
    onboarded: !!saved.onboarded[sid],
    courseById,
    actions,
  };
}

export type CG = ReturnType<typeof useCourseGraph>;
