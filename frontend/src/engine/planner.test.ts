// Run from frontend/:  node src/engine/planner.test.ts
// The project has no @types/node, so the two Node bits are declared loosely here.
// @ts-ignore -- resolved by Node at run time
import assert from 'node:assert/strict';
import { COURSE_BY_ID, DEGREE_CREDITS, TERMS } from '../data/catalog.ts';
import { DEMO_STUDENT } from '../data/student.ts';
import type { PlanItem, PlanResult, StudentProfile } from '../types.ts';
import { directPrereqs, missingPrereqs, recalculate, ruleText } from './planner.ts';

declare const process: { exit(code: number): never };

const student = (over: Partial<StudentProfile> = {}): StudentProfile => ({ ...structuredClone(DEMO_STUDENT), ...over });

const allItems = (plan: PlanResult): PlanItem[] => [...plan.prior, ...plan.terms.flatMap((t) => t.items), ...plan.unscheduled];
const termOf = (plan: PlanResult, courseId: string): string | undefined =>
  plan.terms.find((t) => t.items.some((i) => i.courseId === courseId))?.term.id;
const find = (plan: PlanResult, courseId: string): PlanItem[] => allItems(plan).filter((i) => i.courseId === courseId);
const termIdx = (id: string | undefined): number => TERMS.findIndex((t) => t.id === id);

function assertUniqueKeys(plan: PlanResult): void {
  const keys = allItems(plan).map((i) => i.key);
  assert.equal(new Set(keys).size, keys.length, `duplicate keys: ${keys.join(', ')}`);
}

// Every planned item has its prereqs in strictly earlier terms and is offered that season.
function assertNoViolations(plan: PlanResult): void {
  const taken = new Set(plan.prior.map((i) => i.courseId as string));
  for (const t of plan.terms) {
    for (const item of t.items) {
      if (item.status !== 'planned' || !item.courseId) continue;
      assert.equal(missingPrereqs(item.courseId, taken), undefined, `${item.courseId} in ${t.term.label}`);
      assert.ok(COURSE_BY_ID[item.courseId].offered.includes(t.term.season), `${item.courseId} offered in ${t.term.label}`);
    }
    for (const item of t.items) if (item.courseId) taken.add(item.courseId);
  }
}

function assertCap(plan: PlanResult, profile: StudentProfile): void {
  const cur = termIdx(profile.currentTerm);
  plan.terms.forEach((t, i) => {
    const sum = t.items.reduce((n, item) => n + (item.courseId ? COURSE_BY_ID[item.courseId].credits : 4), 0);
    assert.equal(t.credits, sum, `credits sum in ${t.term.label}`);
    if (i > cur) assert.ok(t.credits <= profile.creditCap, `${t.term.label} over cap: ${t.credits}`);
  });
}

const tests: [string, () => void][] = [];
const test = (name: string, fn: () => void) => tests.push([name, fn]);

test('helpers: directPrereqs, ruleText, missingPrereqs', () => {
  assert.deepEqual(directPrereqs('CSC-301'), ['CSC-207', 'CSC-208', 'MAT-208']);
  assert.deepEqual(directPrereqs('CSC-151'), []);
  assert.equal(ruleText('CSC-301'), 'CSC-207 and (CSC-208 or MAT-208)');
  assert.equal(ruleText('MAT-444'), 'MAT-316 or MAT-321');
  assert.equal(ruleText('CSC-151'), undefined);
  assert.equal(missingPrereqs('CSC-301', new Set(['CSC-207', 'MAT-208'])), undefined);
  assert.equal(missingPrereqs('CSC-301', new Set(['CSC-208'])), 'Needs CSC-207');
  assert.equal(missingPrereqs('CSC-301', new Set(['CSC-207'])), 'Needs CSC-208 or MAT-208');
  assert.equal(missingPrereqs('CSC-301', new Set()), 'Needs CSC-207 and (CSC-208 or MAT-208)');
  assert.equal(missingPrereqs('CSC-151', new Set()), undefined);
});

test('1. no majors: only fixed items, prior has MAT-131', () => {
  const plan = recalculate(student());
  assert.deepEqual(plan.prior.map((i) => i.courseId), ['MAT-131']);
  assert.equal(plan.prior[0].status, 'completed');
  assert.equal(plan.terms.length, TERMS.length);
  assert.deepEqual(plan.terms[0].items.map((i) => i.courseId), ['TUT-100', 'CSC-151', 'MAT-133', 'PSY-113']);
  assert.deepEqual(plan.terms[2].items.map((i) => i.courseId), ['CSC-208', 'FMS-155', 'STA-209', 'MUS-120']);
  assert.ok(plan.terms[2].items.every((i) => i.status === 'enrolled'));
  assert.equal(plan.terms[2].credits, 13);
  for (const t of plan.terms.slice(3)) assert.deepEqual(t.items, []);
  assert.deepEqual(plan.unscheduled, []);
  assert.deepEqual(plan.progress, []);
  assert.deepEqual(plan.changes, []);
  assert.ok(allItems(plan).every((i) => i.satisfies.length === 0 && !i.pinned));
  assert.deepEqual(plan.totalCredits, { earned: 36, planned: 13, required: DEGREE_CREDITS });

  // Pinned items still work without majors; past/current placements are ignored.
  const pinned = recalculate(student({ placements: { 'PHI-101': '2027SP', 'ECN-111': '2026FA', 'HIS-100': '2025FA', 'CSC-151': '2028SP' } }));
  const future = pinned.terms.flatMap((t) => t.items).filter((i) => i.pinned);
  assert.deepEqual(future.map((i) => [i.key, i.status]), [['course:PHI-101', 'planned']]);
  assert.equal(find(pinned, 'CSC-151').length, 1);
});

test('2. CS only for the demo student', () => {
  const profile = student({ majors: ['CS'] });
  const plan = recalculate(profile);
  assertNoViolations(plan);
  assertCap(plan, profile);
  assertUniqueKeys(plan);
  assert.deepEqual(plan.unscheduled, []);

  const t213 = plan.terms.find((t) => t.term.id === termOf(plan, 'CSC-213'));
  if (!t213) throw new Error('CSC-213 not scheduled');
  assert.equal(t213.term.season, 'Spring');
  assert.ok(termIdx(termOf(plan, 'CSC-207')) < termIdx(t213.term.id));
  assert.ok(termIdx(termOf(plan, 'CSC-211')) < termIdx(t213.term.id));

  const slots = allItems(plan).filter((i) => i.slot);
  assert.deepEqual(slots.map((i) => i.key).sort(), ['slot:CS:elective:0', 'slot:CS:elective:1']);
  for (const s of slots) {
    assert.equal(s.courseId, undefined);
    assert.equal(s.status, 'unsatisfied');
    assert.equal(s.reason, 'Choose one');
    assert.deepEqual(s.satisfies, ['CS · CS elective']);
    assert.deepEqual(s.slot, {
      programId: 'CS',
      requirementId: 'CS:elective',
      label: 'CS elective',
      options: ['CSC-312', 'CSC-321', 'CSC-322', 'CSC-364', 'CSC-395'],
    });
  }
  assert.deepEqual(find(plan, 'CSC-208')[0].satisfies, ['CS · Discrete math']);
  assert.deepEqual(find(plan, 'CSC-207')[0].satisfies, ['CS · CSC 207']);
  assert.deepEqual(find(plan, 'FMS-155')[0].satisfies, []);
  assert.equal(find(plan, 'MAT-208').length, 0);

  const [cs] = plan.progress;
  assert.equal(cs.programId, 'CS');
  assert.equal(cs.total, 12);
  assert.equal(cs.completed, 3); // MAT-131, CSC-151, CSC-161
  assert.equal(cs.planned, 7); // CSC-208 enrolled + 207, 211, 213, 301, 324, 341
  assert.equal(cs.requirements.length, 12);
  const discrete = cs.requirements.find((r) => r.id === 'CS:discrete');
  assert.deepEqual(discrete, { id: 'CS:discrete', label: 'Discrete math', status: 'enrolled', termId: '2026FA', courseId: 'CSC-208' });
  assert.equal(cs.requirements.filter((r) => r.id === 'CS:elective' && r.status === 'unsatisfied').length, 2);

  const futureCredits = plan.terms.slice(3).reduce((n, t) => n + t.credits, 0);
  assert.deepEqual(plan.totalCredits, { earned: 36, planned: 13 + futureCredits, required: DEGREE_CREDITS });
});

test('3. pinning a requirement elsewhere removes its auto slot and reports a change', () => {
  // (a) Demo student: move CSC-341 to the last term.
  const base = student({ majors: ['CS'] });
  const before = recalculate(base);
  const was = TERMS[termIdx(termOf(before, 'CSC-341'))];
  const after = recalculate({ ...base, placements: { 'CSC-341': '2029SP' } }, before);
  assert.equal(find(after, 'CSC-341').length, 1);
  assert.equal(termOf(after, 'CSC-341'), '2029SP');
  assert.deepEqual(
    find(after, 'CSC-341').map((i) => [i.pinned, i.status]),
    [[true, 'planned']],
  );
  assert.ok(after.changes.includes(`CSC-341 moved from ${was.label} to Spring 2029`), after.changes.join(' | '));
  assert.ok(after.changes.length <= 4);
  assertNoViolations(after);
  assertUniqueKeys(after);

  // (b) A tight plan (one course per term) where CSC-207 is already in progress:
  // pulling CSC-341 forward frees its late slot and reshuffles what follows.
  const tight = student({ majors: ['CS'], creditCap: 4 });
  tight.credits = tight.credits.map((c) => (c.courseId === 'FMS-155' ? { ...c, courseId: 'CSC-207' } : c));
  const tightBefore = recalculate(tight);
  const lateTerm = termOf(tightBefore, 'CSC-341');
  assert.ok(termIdx(lateTerm) > termIdx('2027SP'), `auto CSC-341 starts late, got ${lateTerm}`);
  const tightAfter = recalculate({ ...tight, placements: { 'CSC-341': '2027SP' } }, tightBefore);
  assert.equal(find(tightAfter, 'CSC-341').length, 1);
  assert.equal(termOf(tightAfter, 'CSC-341'), '2027SP');
  assert.equal(find(tightAfter, 'CSC-341')[0].status, 'planned');
  assert.ok(!tightAfter.terms[termIdx(lateTerm)].items.some((i) => i.courseId === 'CSC-341'));
  assert.ok(tightAfter.changes.length > 0 && tightAfter.changes.length <= 4);
  assertNoViolations(tightAfter);
  assertCap(tightAfter, tight);

  // Unpinning it again reports the move back; no previous means no changes.
  const back = recalculate(base, after);
  assert.ok(back.changes.includes(`CSC-341 moved from Spring 2029 to ${was.label}`), back.changes.join(' | '));
  assert.deepEqual(recalculate({ ...base, placements: { 'CSC-341': '2029SP' } }).changes, []);

  // Adding a major reports additions; dropping it reports what is no longer needed.
  const none = recalculate(student());
  const added = recalculate(base, none);
  assert.ok(added.changes.some((c) => /^CSC-\d+ added to (Fall|Spring) \d{4}$/.test(c)), added.changes.join(' | '));
  const dropped = recalculate(student(), before);
  assert.ok(dropped.changes.some((c) => /^CSC-\d+ no longer needed in (Fall|Spring) \d{4}$/.test(c)), dropped.changes.join(' | '));
});

test('4. pinning before a prerequisite is unsatisfied but still counts once', () => {
  const profile = student({ majors: ['CS'], placements: { 'CSC-341': '2027SP' } });
  const plan = recalculate(profile);
  const items = find(plan, 'CSC-341');
  assert.equal(items.length, 1);
  assert.equal(items[0].status, 'unsatisfied');
  assert.equal(items[0].pinned, true);
  assert.equal(items[0].reason, 'Needs CSC-207 first');
  assert.equal(termOf(plan, 'CSC-341'), '2027SP');
  assert.deepEqual(items[0].satisfies, ['CS · CSC 341']);
  const entry = plan.progress[0].requirements.find((r) => r.courseId === 'CSC-341');
  assert.deepEqual(entry, { id: 'CS:CSC-341', label: 'CSC 341', status: 'unsatisfied', termId: '2027SP', courseId: 'CSC-341' });
  assertCap(plan, profile);
  assertUniqueKeys(plan);

  // Wrong season.
  const offSeason = recalculate(student({ majors: ['CS'], placements: { 'CSC-324': '2029SP' } }));
  assert.equal(find(offSeason, 'CSC-324').length, 1);
  assert.equal(find(offSeason, 'CSC-324')[0].reason, 'Not offered in Spring');
  assert.equal(find(offSeason, 'CSC-324')[0].status, 'unsatisfied');
});

test('5. CS + MATH double major', () => {
  const profile = student({ majors: ['CS', 'MATH'] });
  const plan = recalculate(profile);
  assertUniqueKeys(plan);
  assertNoViolations(plan);
  assertCap(plan, profile);
  assert.equal(find(plan, 'MAT-131').length, 1);
  assert.deepEqual(find(plan, 'MAT-131')[0].satisfies, ['CS · MAT 131', 'MATH · MAT 131']);
  assert.equal(plan.prior.length, 1);
  assert.deepEqual(find(plan, 'CSC-208')[0].satisfies, ['CS · Discrete math', 'MATH · Proofs course']);
  assert.ok(!allItems(plan).some((i) => i.slot?.requirementId === 'CS:discrete' || i.slot?.requirementId === 'MATH:proofs'));
  assert.deepEqual(plan.progress.map((p) => p.programId), ['CS', 'MATH']);
  const math = plan.progress[1];
  assert.equal(math.total, 9);
  assert.equal(math.completed, 3); // MAT-131, MAT-133, MAT-215
  assert.equal(math.requirements.find((r) => r.id === 'MATH:proofs')?.courseId, 'CSC-208');
  for (const id of ['MAT-218', 'MAT-316', 'MAT-321']) assert.equal(find(plan, id).length, 1, id);

  // A picked elective fills one slot of its own requirement only.
  const picked = recalculate({ ...profile, placements: { 'MAT-335': '2027FA' } });
  assert.deepEqual(find(picked, 'MAT-335')[0].satisfies, ['MATH · Math elective']);
  const mathSlots = allItems(picked).filter((i) => i.slot?.requirementId === 'MATH:elective');
  assert.deepEqual(mathSlots.map((i) => i.key), ['slot:MATH:elective:0']);
  assert.ok(!mathSlots[0].slot?.options.includes('MAT-335'));
  assertUniqueKeys(picked);
});

test('6. dismissed courses and placeholder options', () => {
  const profile = student({ majors: ['CS'], dismissed: ['PHI-101', 'CSC-312'] });
  const plan = recalculate(profile);
  assert.equal(find(plan, 'PHI-101').length, 0);
  assert.equal(find(plan, 'CSC-312').length, 0);
  // Nothing outside the major's requirements is ever auto-scheduled.
  const required = new Set(['MAT-131', 'CSC-151', 'CSC-161', 'CSC-207', 'CSC-211', 'CSC-213', 'CSC-301', 'CSC-324', 'CSC-341']);
  for (const item of plan.terms.slice(3).flatMap((t) => t.items)) {
    if (item.courseId) assert.ok(required.has(item.courseId), `${item.courseId} is not required`);
  }

  // Options drop courses that are already taken or pinned.
  const withElective = student({ majors: ['CS'], placements: { 'CSC-321': '2027FA' } });
  withElective.credits = [...withElective.credits, { courseId: 'CSC-312', source: 'transfer', status: 'completed' }];
  const plan2 = recalculate(withElective);
  assert.deepEqual(allItems(plan2).filter((i) => i.slot).map((i) => i.key), []);
  assert.equal(plan2.progress[0].requirements.filter((r) => r.id === 'CS:elective').length, 2);

  const oneLeft = student({ majors: ['CS'] });
  oneLeft.credits = [...oneLeft.credits, { courseId: 'CSC-312', source: 'transfer', status: 'completed' }];
  const plan3 = recalculate(oneLeft);
  const slots = allItems(plan3).filter((i) => i.slot);
  assert.deepEqual(slots.map((i) => i.key), ['slot:CS:elective:0']);
  assert.deepEqual(slots[0].slot?.options, ['CSC-321', 'CSC-322', 'CSC-364', 'CSC-395']);
  assert.equal(plan3.prior.length, 2);
});

test('7. deterministic and does not mutate its input', () => {
  const profile = student({ majors: ['CS', 'MATH'], placements: { 'CSC-341': '2029SP', 'PHI-101': '2027SP' }, dismissed: ['ART-111'] });
  const snapshot = structuredClone(profile);
  const first = recalculate(profile);
  const second = recalculate(profile);
  assert.deepEqual(first, second);
  assert.deepEqual(profile, snapshot);
  const prev = structuredClone(first);
  recalculate({ ...profile, placements: {} }, first);
  assert.deepEqual(first, prev);
  // Key order of placements does not matter.
  const reordered = recalculate({ ...profile, placements: { 'PHI-101': '2027SP', 'CSC-341': '2029SP' } });
  assert.deepEqual(reordered, first);
});

test('8. units that cannot fit are reported as unscheduled', () => {
  const tiny = recalculate(student({ majors: ['CS', 'MATH'], creditCap: 4 }));
  assert.ok(tiny.unscheduled.length > 0);
  assert.ok(tiny.unscheduled.every((i) => i.status === 'unsatisfied' && !i.pinned));
  assert.ok(tiny.unscheduled.some((i) => i.reason === 'No room before Spring 2029'));
  assert.ok(tiny.unscheduled.every((i) => i.reason === 'No room before Spring 2029' || i.reason === 'Prerequisites not met in time'));
  assertUniqueKeys(tiny);

  const start = performance.now();
  for (let i = 0; i < 200; i++) recalculate(student({ majors: ['CS', 'MATH'] }));
  const perCall = (performance.now() - start) / 200;
  assert.ok(perCall < 20, `recalculate took ${perCall.toFixed(2)} ms`);
});

let failed = 0;
for (const [name, fn] of tests) {
  try {
    fn();
    console.log(`ok   ${name}`);
  } catch (err) {
    failed++;
    console.error(`FAIL ${name}`);
    console.error(err);
  }
}
console.log(`${tests.length - failed}/${tests.length} passed`);
if (failed) process.exit(1);
