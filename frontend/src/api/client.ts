// HTTP client for backend/CONTRACT.md. Vite proxies /api to the Python
// backend on 127.0.0.1:8100 (see vite.config.ts).
import type {
  Catalog,
  OptionsResult,
  Plan,
  PlanRequest,
  ScheduleResult,
  Section,
  Student,
  StudentSummary,
  TermId,
} from './types.ts';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    });
  } catch {
    throw new ApiError(0, 'Backend not reachable');
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body?.detail === 'string' ? body.detail : JSON.stringify(body?.detail ?? body);
    } catch {
      /* keep statusText */
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  catalog: () => call<Catalog>('/catalog'),
  students: () => call<StudentSummary[]>('/students'),
  student: (id: string) => call<Student>(`/students/${encodeURIComponent(id)}`),
  sections: (term: TermId) => call<Section[]>(`/sections?term=${encodeURIComponent(term)}`),
  saveSchedule: (id: string, term: TermId, sectionIds: string[]) =>
    call<ScheduleResult>(`/students/${encodeURIComponent(id)}/schedule`, {
      method: 'PUT',
      body: JSON.stringify({ term, section_ids: sectionIds }),
    }),
  plan: (req: PlanRequest) => call<Plan>('/plan', { method: 'POST', body: JSON.stringify(req) }),
  options: (req: PlanRequest & { term: TermId; tablet?: string | null }) =>
    call<OptionsResult>('/options', { method: 'POST', body: JSON.stringify(req) }),
};
