// Mock planning engine. Stands in for the backend's POST /recalculate.
// Pure and deterministic: same profile in, same plan out, no input mutation.
import { COURSE_BY_ID, DEGREE_CREDITS, PROGRAM_BY_ID, TERMS } from '../data/catalog.ts';
import type {
  ItemStatus,
  PlanItem,
  PlanResult,
  PlanSlot,
  PlanTerm,
  PrereqRule,
  ProgramProgress,
  Requirement,
  StudentProfile,
  TermId,
} from '../types.ts';

const PLACEHOLDER_CREDITS = 4;
const MAX_CHANGES = 4;

// ---- Prerequisite helpers ----------------------------------------------

function collectIds(rule: PrereqRule, out: string[]): void {
  if (rule.kind === 'course') {
    if (!out.includes(rule.id)) out.push(rule.id);
    return;
  }
  for (const r of rule.rules) collectIds(r, out);
}

function formatRule(rule: PrereqRule): string {
  if (rule.kind === 'course') return rule.id;
  const joiner = rule.kind === 'all' ? ' and ' : ' or ';
  if (rule.rules.length === 1) return formatRule(rule.rules[0]);
  return rule.rules
    .map((r) => (r.kind !== 'course' && r.kind !== rule.kind && r.rules.length > 1 ? `(${formatRule(r)})` : formatRule(r)))
    .join(joiner);
}

// The part of the rule that `taken` does not satisfy, or undefined if satisfied.
function missingRule(rule: PrereqRule, taken: ReadonlySet<string>): PrereqRule | undefined {
  if (rule.kind === 'course') return taken.has(rule.id) ? undefined : rule;
  if (rule.kind === 'all') {
    const missing: PrereqRule[] = [];
    for (const r of rule.rules) {
      const m = missingRule(r, taken);
      if (m) missing.push(m);
    }
    if (missing.length === 0) return undefined;
    return missing.length === 1 ? missing[0] : { kind: 'all', rules: missing };
  }
  if (rule.rules.length === 0) return undefined;
  const missing: PrereqRule[] = [];
  for (const r of rule.rules) {
    const m = missingRule(r, taken);
    if (!m) return undefined;
    missing.push(m);
  }
  return missing.length === 1 ? missing[0] : { kind: 'any', rules: missing };
}

/** Every course id mentioned in the course's prerequisite rule. */
export function directPrereqs(courseId: string): string[] {
  const rule = COURSE_BY_ID[courseId]?.prereq;
  const out: string[] = [];
  if (rule) collectIds(rule, out);
  return out;
}

/** Human text of the prerequisite rule, e.g. `CSC-207 and (CSC-208 or MAT-208)`. */
export function ruleText(courseId: string): string | undefined {
  const rule = COURSE_BY_ID[courseId]?.prereq;
  return rule ? formatRule(rule) : undefined;
}

/** undefined when `taken` satisfies the rule, else e.g. `Needs CSC-208 or MAT-208`. */
export function missingPrereqs(courseId: string, taken: Set<string>): string | undefined {
  const rule = COURSE_BY_ID[courseId]?.prereq;
  if (!rule) return undefined;
  const missing = missingRule(rule, taken);
  return missing ? `Needs ${formatRule(missing)}` : undefined;
}

// ---- Internal shapes -----------------------------------------------------

interface AutoUnit {
  key: string;
  courseId?: string;
  slot?: PlanSlot;
  order: number; // creation order, the final tie-break
  height: number; // length of the remaining dependency chain hanging off this unit
  everReady: boolean;
}

// One requirement unit of one program (a choose-2 yields two).
interface ProgramUnit {
  req: Requirement;
  courseId?: string; // course counted toward it (held, auto-scheduled or dismissed)
  slotKey?: string; // placeholder key when no course fills it
}

interface Located {
  item: PlanItem;
  termId?: TermId; // undefined for prior and unscheduled
  where: 'prior' | 'term' | 'unscheduled';
}

function creditsOf(courseId: string | undefined): number {
  if (!courseId) return PLACEHOLDER_CREDITS;
  return COURSE_BY_ID[courseId]?.credits ?? PLACEHOLDER_CREDITS;
}

function courseNumber(courseId: string): number {
  const n = parseInt(COURSE_BY_ID[courseId]?.number ?? courseId.split('-')[1] ?? '', 10);
  return Number.isNaN(n) ? Number.MAX_SAFE_INTEGER : n;
}

function compareCourseIds(a: string, b: string): number {
  return courseNumber(a) - courseNumber(b) || (a < b ? -1 : a > b ? 1 : 0);
}

// ---- recalculate ---------------------------------------------------------

export function recalculate(profile: StudentProfile, previous?: PlanResult): PlanResult {
  const termIndex = new Map<TermId, number>(TERMS.map((t, i) => [t.id, i]));
  const currentIdx = termIndex.get(profile.currentTerm) ?? -1;
  const lastTermLabel = TERMS[TERMS.length - 1]?.label ?? 'graduation';

  // 1. Fixed items: the student's record. termIdx -1 means prior credit.
  const fixed = new Map<string, { status: 'completed' | 'enrolled'; termIdx: number }>();
  for (const rec of profile.credits) {
    if (fixed.has(rec.courseId)) continue;
    const idx = rec.term === undefined ? -1 : (termIndex.get(rec.term) ?? -1);
    fixed.set(rec.courseId, { status: idx === -1 ? 'completed' : rec.status, termIdx: idx });
  }

  // 2. Pinned items: hand placements into future terms only.
  const pinned = new Map<string, number>();
  for (const courseId of Object.keys(profile.placements).sort(compareCourseIds)) {
    const idx = termIndex.get(profile.placements[courseId]);
    if (idx === undefined || idx <= currentIdx) continue;
    if (!COURSE_BY_ID[courseId] || fixed.has(courseId)) continue;
    pinned.set(courseId, idx);
  }

  const heldIdx = (courseId: string): number | undefined => fixed.get(courseId)?.termIdx ?? pinned.get(courseId);

  // 3. Requirements: decide which course counts toward which unit.
  const majors: string[] = [];
  for (const id of profile.majors) if (PROGRAM_BY_ID[id] && !majors.includes(id)) majors.push(id);
  const dismissed = new Set(profile.dismissed);

  const autoCourses: string[] = []; // concrete courses to auto-schedule, deduped across majors
  const blockedCourses = new Set<string>(); // required but dismissed: never auto-scheduled
  const programUnits = new Map<string, ProgramUnit[]>();
  const pendingSlots: { programId: string; req: Requirement & { kind: 'choose' }; index: number; unit: ProgramUnit }[] = [];

  for (const programId of majors) {
    const program = PROGRAM_BY_ID[programId];
    const claimed = new Set<string>(); // within one program a course counts once
    const byReq = new Map<string, ProgramUnit[]>();

    for (const req of program.requirements) {
      if (req.kind !== 'course') continue;
      claimed.add(req.courseId);
      byReq.set(req.id, [{ req, courseId: req.courseId }]);
      if (heldIdx(req.courseId) !== undefined) continue;
      if (dismissed.has(req.courseId) || !COURSE_BY_ID[req.courseId]) blockedCourses.add(req.courseId);
      else if (!autoCourses.includes(req.courseId)) autoCourses.push(req.courseId);
    }

    for (const req of program.requirements) {
      if (req.kind !== 'choose') continue;
      const candidates = req.options
        .map((courseId, optionIdx) => ({ courseId, optionIdx, idx: heldIdx(courseId) }))
        .filter((c) => c.idx !== undefined && !claimed.has(c.courseId))
        .sort((a, b) => (a.idx as number) - (b.idx as number) || a.optionIdx - b.optionIdx)
        .slice(0, req.count);
      const units: ProgramUnit[] = [];
      for (const c of candidates) {
        claimed.add(c.courseId);
        units.push({ req, courseId: c.courseId });
      }
      const missing = Math.max(0, req.count - candidates.length);
      for (let index = 0; index < missing; index++) {
        const unit: ProgramUnit = { req, slotKey: `slot:${req.id}:${index}` };
        units.push(unit);
        pendingSlots.push({ programId, req, index, unit });
      }
      byReq.set(req.id, units);
    }

    programUnits.set(
      programId,
      program.requirements.flatMap((req) => byReq.get(req.id) ?? []),
    );
  }

  // 4. Auto units: concrete required courses, then one placeholder per missing slot.
  const autoSet = new Set(autoCourses);
  const units: AutoUnit[] = [];
  for (const courseId of autoCourses) {
    units.push({ key: `course:${courseId}`, courseId, order: units.length, height: 0, everReady: false });
  }
  const seenSlotKeys = new Set<string>();
  for (const p of pendingSlots) {
    const key = p.unit.slotKey as string;
    if (seenSlotKeys.has(key)) continue;
    seenSlotKeys.add(key);
    units.push({
      key,
      slot: {
        programId: p.programId,
        requirementId: p.req.id,
        label: p.req.label,
        options: p.req.options.filter((o) => heldIdx(o) === undefined && !autoSet.has(o)),
      },
      order: units.length,
      height: 0,
      everReady: false,
    });
  }

  // Priority: how long a chain of remaining units waits on this one.
  const concrete = units.filter((u) => u.courseId !== undefined);
  const prereqIds = new Map<string, string[]>(concrete.map((u) => [u.key, directPrereqs(u.courseId as string)]));
  const heightMemo = new Map<string, number>();
  const heightOf = (u: AutoUnit, trail: Set<string>): number => {
    const known = heightMemo.get(u.key);
    if (known !== undefined) return known;
    if (trail.has(u.key)) return 0; // defensive: the catalog has no cycles
    trail.add(u.key);
    const provides = u.courseId !== undefined ? [u.courseId] : (u.slot as PlanSlot).options;
    let best = 0;
    for (const v of concrete) {
      if (v === u) continue;
      if ((prereqIds.get(v.key) as string[]).some((id) => provides.includes(id))) best = Math.max(best, heightOf(v, trail));
    }
    trail.delete(u.key);
    heightMemo.set(u.key, best + 1);
    return best + 1;
  };
  for (const u of units) u.height = heightOf(u, new Set());

  const queue = [...units].sort((a, b) => {
    if (a.height !== b.height) return b.height - a.height;
    const aSlot = a.courseId === undefined;
    const bSlot = b.courseId === undefined;
    if (aSlot !== bSlot) return aSlot ? 1 : -1;
    if (!aSlot && !bSlot) return compareCourseIds(a.courseId as string, b.courseId as string);
    return a.order - b.order;
  });

  // 5. Labels each course / placeholder counts toward.
  const satisfiesOf = new Map<string, string[]>(); // courseId or slot key -> labels
  for (const programId of majors) {
    for (const unit of programUnits.get(programId) ?? []) {
      const target = unit.courseId ?? (unit.slotKey as string);
      const label = `${programId} · ${unit.req.label}`;
      const list = satisfiesOf.get(target) ?? [];
      if (!list.includes(label)) list.push(label);
      satisfiesOf.set(target, list);
    }
  }
  const labelsFor = (target: string): string[] => [...(satisfiesOf.get(target) ?? [])];

  // 6. Walk the terms in order: fixed, then pinned, then greedy auto fill.
  const prior: PlanItem[] = [];
  const taken = new Set<string>(); // everything in strictly earlier terms
  for (const [courseId, f] of fixed) {
    if (f.termIdx !== -1) continue;
    prior.push({ key: `course:${courseId}`, courseId, status: 'completed', pinned: false, satisfies: labelsFor(courseId) });
    taken.add(courseId);
  }

  const remaining = new Set(queue.map((u) => u.key));
  const terms: PlanTerm[] = TERMS.map((term, ti) => {
    const items: PlanItem[] = [];
    let credits = 0;

    for (const [courseId, f] of fixed) {
      if (f.termIdx !== ti) continue;
      items.push({ key: `course:${courseId}`, courseId, status: f.status, pinned: false, satisfies: labelsFor(courseId) });
      credits += creditsOf(courseId);
    }

    if (ti > currentIdx) {
      const offeredNow = (courseId: string): boolean => COURSE_BY_ID[courseId]?.offered.includes(term.season) ?? false;

      for (const [courseId, idx] of pinned) {
        if (idx !== ti) continue;
        const missing = missingPrereqs(courseId, taken);
        const reason = missing ? `${missing} first` : offeredNow(courseId) ? undefined : `Not offered in ${term.season}`;
        const item: PlanItem = {
          key: `course:${courseId}`,
          courseId,
          status: reason ? 'unsatisfied' : 'planned',
          pinned: true,
          satisfies: labelsFor(courseId),
        };
        if (reason) item.reason = reason;
        items.push(item);
        credits += creditsOf(courseId);
      }

      const slotsPlacedHere = new Map<string, number>(); // requirementId -> placeholders placed this term
      for (const u of queue) {
        if (!remaining.has(u.key)) continue;
        let ready: boolean;
        if (u.courseId !== undefined) {
          ready = offeredNow(u.courseId) && missingPrereqs(u.courseId, taken) === undefined;
        } else {
          const slot = u.slot as PlanSlot;
          const readyOptions = slot.options.filter((o) => offeredNow(o) && missingPrereqs(o, taken) === undefined).length;
          ready = readyOptions > (slotsPlacedHere.get(slot.requirementId) ?? 0);
        }
        if (!ready) continue;
        u.everReady = true;
        const cost = creditsOf(u.courseId);
        if (credits + cost > profile.creditCap) continue;
        credits += cost;
        remaining.delete(u.key);
        if (u.courseId !== undefined) {
          items.push({ key: u.key, courseId: u.courseId, status: 'planned', pinned: false, satisfies: labelsFor(u.courseId) });
        } else {
          const slot = u.slot as PlanSlot;
          slotsPlacedHere.set(slot.requirementId, (slotsPlacedHere.get(slot.requirementId) ?? 0) + 1);
          items.push({
            key: u.key,
            slot: { ...slot, options: [...slot.options] },
            status: 'unsatisfied',
            reason: 'Choose one',
            pinned: false,
            satisfies: labelsFor(u.key),
          });
        }
      }
    }

    for (const item of items) if (item.courseId !== undefined) taken.add(item.courseId);
    return { term, items, credits };
  });

  // 7. Whatever never fit.
  const unscheduled: PlanItem[] = queue
    .filter((u) => remaining.has(u.key))
    .map((u) => {
      const item: PlanItem = {
        key: u.key,
        status: 'unsatisfied',
        reason: u.everReady ? `No room before ${lastTermLabel}` : 'Prerequisites not met in time',
        pinned: false,
        satisfies: labelsFor(u.courseId ?? u.key),
      };
      if (u.courseId !== undefined) item.courseId = u.courseId;
      else item.slot = { ...(u.slot as PlanSlot), options: [...(u.slot as PlanSlot).options] };
      return item;
    });

  // 8. Progress per major.
  const located = locate({ prior, terms, unscheduled });
  const progress: ProgramProgress[] = majors.map((programId) => {
    const list = programUnits.get(programId) ?? [];
    let completed = 0;
    let planned = 0;
    const requirements = list.map((unit) => {
      const key = unit.courseId !== undefined ? `course:${unit.courseId}` : (unit.slotKey as string);
      const loc = located.get(key);
      const status: ItemStatus = loc?.item.status ?? 'unsatisfied';
      if (status === 'completed') completed++;
      else if (status === 'enrolled' || status === 'planned') planned++;
      const entry: ProgramProgress['requirements'][number] = { id: unit.req.id, label: unit.req.label, status };
      if (loc?.termId !== undefined) entry.termId = loc.termId;
      if (unit.courseId !== undefined) entry.courseId = unit.courseId;
      return entry;
    });
    return { programId, name: PROGRAM_BY_ID[programId].name, total: list.length, completed, planned, requirements };
  });

  // 9. Credit totals.
  let earned = 0;
  let plannedCredits = 0;
  for (const item of prior) earned += creditsOf(item.courseId);
  terms.forEach((t, ti) => {
    for (const item of t.items) {
      if (item.status === 'completed') earned += creditsOf(item.courseId);
      else if (item.status === 'enrolled' || ti > currentIdx) plannedCredits += creditsOf(item.courseId);
    }
  });

  return {
    prior,
    terms,
    unscheduled,
    progress,
    totalCredits: { earned, planned: plannedCredits, required: DEGREE_CREDITS },
    changes: previous ? diffPlans(previous, located, lastTermLabel) : [],
  };
}

// ---- Diff ----------------------------------------------------------------

function locate(plan: Pick<PlanResult, 'prior' | 'terms' | 'unscheduled'>): Map<string, Located> {
  const out = new Map<string, Located>();
  for (const item of plan.prior) out.set(item.key, { item, where: 'prior' });
  for (const t of plan.terms) for (const item of t.items) out.set(item.key, { item, termId: t.term.id, where: 'term' });
  for (const item of plan.unscheduled) out.set(item.key, { item, where: 'unscheduled' });
  return out;
}

function diffPlans(previous: PlanResult, next: Map<string, Located>, lastTermLabel: string): string[] {
  const before = locate(previous);
  const order = new Map<TermId, number>(TERMS.map((t, i) => [t.id, i]));
  const label = (id: TermId | undefined): string => TERMS.find((t) => t.id === id)?.label ?? String(id);
  const at = (id: TermId | undefined): number => (id === undefined ? TERMS.length : (order.get(id) ?? TERMS.length));

  // rank: knock-on effects on the auto plan first, the student's own move last.
  const found: { rank: number; at: number; id: string; text: string }[] = [];
  const add = (kind: number, isPinned: boolean, termId: TermId | undefined, id: string, text: string) =>
    found.push({ rank: (isPinned ? 10 : 0) + kind, at: at(termId), id, text });

  for (const [key, now] of next) {
    const id = now.item.courseId;
    if (id === undefined) continue;
    const was = before.get(key);
    const wasTerm = was?.where === 'term' ? was.termId : undefined;
    if (now.where === 'term') {
      if (wasTerm !== undefined && wasTerm !== now.termId) {
        add(0, now.item.pinned, now.termId, id, `${id} moved from ${label(wasTerm)} to ${label(now.termId)}`);
      } else if (wasTerm === undefined && was?.where !== 'prior') {
        add(3, now.item.pinned, now.termId, id, `${id} added to ${label(now.termId)}`);
      }
    } else if (now.where === 'unscheduled' && wasTerm !== undefined) {
      add(1, false, wasTerm, id, `${id} no longer fits before ${lastTermLabel}`);
    }
  }
  for (const [key, was] of before) {
    const id = was.item.courseId;
    if (id === undefined || was.where !== 'term' || next.has(key)) continue;
    const text = was.item.pinned ? `${id} removed from ${label(was.termId)}` : `${id} no longer needed in ${label(was.termId)}`;
    add(2, was.item.pinned, was.termId, id, text);
  }

  found.sort((a, b) => a.rank - b.rank || a.at - b.at || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
  return found.slice(0, MAX_CHANGES).map((f) => f.text);
}
