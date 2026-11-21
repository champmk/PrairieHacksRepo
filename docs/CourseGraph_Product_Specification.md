---
title: 'CourseGraph | Product & Technical Specification'
subtitle: 'Your Entire Grinnell Degree, Mapped'
author: 'PrairieHacks Team • Working specification'
date: 'November 21, 2026'
version: '1.0 • Hackathon build'
---

# Executive summary

**CourseGraph** is a Grinnell-focused, interactive academic planning application. Students choose majors and concentrations, record completed and externally awarded coursework, explore prerequisite dependencies, inspect progress toward different requirements, and generate a provisional semester-by-semester plan. Its signature interaction is a *live what-if simulation*: changing a major, waiver, completed class, semester credit limit, or course availability causes the prerequisite network, eligibility explanations, requirement progress, and proposed plan to update together.

**Problem.** Grinnell offers individually advised academic paths, but students must interpret information distributed among the academic catalog, departmental advising resources, the course schedule, and Colleague Self-Service (COLSS). Existing campus systems offer useful registration and degree-planning functions; CourseGraph complements them with a clearer interactive dependency map, constraint explanations, and quick what-if comparisons rather than claiming to replace the official degree audit.

**Hackathon outcome.** Ship a polished, offline-capable prototype covering a **curated, source-tracked Computer Science + Mathematics demonstration**, not every major. The app must perform genuine calculations, never masquerade hard-coded screenshots as scheduling logic, and clearly distinguish confirmed academic facts from provisional planning assumptions. It is a **planning aid, not a determination of graduation eligibility**.

| Item | Decision |
|:--|:--|
| Primary audience | Grinnell students exploring course sequences and major choices |
| Primary prize target | Best Hack for Grinnell |
| Additional targets | Best Overall if awarded; Best Interdisciplinary if eligible |
| Single strongest demo moment | Toggle a waiver or planning constraint; graph, audit, and semester plan update immediately |
| Build approach | Four teammates, one repository, contract-first modules, frequent integration |
| MVP stack | React + Vite + TypeScript; React Flow; pure TypeScript planning engine; curated JSON; Vitest |
| Authoritative academic source | Applicable official academic catalog and Registrar policies, supplemented by departmental advising and public course search |
| Non-goal | Live COLSS login, automated enrollment, official degree certification, guaranteed future course availability |

# 1. Product intent and competition strategy

## 1.1 Vision

**Tagline:** *Your Entire Grinnell Degree, Mapped.*

**One-line pitch:** CourseGraph turns complex Grinnell degree requirements into a navigable map and a personalized, explainable academic roadmap.

**Value proposition:** Students should be able to answer: *What can I take next? What am I missing? What changes if I add another major, receive a prerequisite waiver, study abroad, or graduate early?* They should also understand *why* the answer changed.

## 1.2 Desired outcomes and success measures

The team succeeds if judges can observe one complete workflow, not merely several isolated screens.

| Goal ID | Outcome | Hackathon acceptance signal |
|:--|:--|:--|
| G-01 | Understand prerequisite dependencies | A directed graph renders a curated CS + Math dataset; click any course for its requirements |
| G-02 | Identify course eligibility | Completing or waiving a prerequisite produces correct, explainable eligible/blocked states |
| G-03 | Understand progress | Program-specific requirement progress and earned degree credits display **separately** |
| G-04 | Build a plausible academic plan | Terms are generated from course rules, credit budget, and available offering evidence |
| G-05 | Compare what-if scenarios | Changing one profile input updates graph, audit, and plan within a normal interaction, without reload |
| G-06 | Preserve trust | Any unsourced rule, unknown offering, or approval-dependent credit is visible as uncertain |
| G-07 | Make the team deliver | Fresh clone → install → run → build → test; a rehearsed live demo and fallback recording |

**Competition positioning.** *For Grinnell:* addresses an actual student advising workflow using college-specific policy distinctions. *Overall:* coherent UX + real graph/rule/planning computation + a working integrated system. *Interdisciplinary:* computer science, mathematical optimization, educational design, policy interpretation, information visualization. Eligibility for prizes, judging rubric, and AI-use rules must be checked against event-specific instructions; they are not assumed here.

## 1.3 Target users and jobs to be done

- **Exploring first-year student:** compares majors, sees prerequisite chains, avoids accidentally closing future options.
- **Double-major planner:** checks overlapping course needs, degree totals, department limits, and workload across future semesters.
- **Student with placement or external credits:** records both prerequisite clearance and actual credit awards without conflating them.
- **Study-away candidate:** identifies prerequisites and unresolved departmental approvals for courses taken off campus.
- **Academic adviser (future):** reviews a student's hypothetical plan and identifies decisions that need official confirmation.

## 1.4 Product principles

1. **Explainability over false precision.** Show the prerequisite or policy behind each recommendation.
2. **One profile, one calculation pipeline.** Every screen derives from the same current input state.
3. **No invented academic facts.** A missing rule is `unknown`, not automatically satisfied.
4. **Waivers are not credits.** Prerequisite permission, completed coursework, earned degree credit, and accepted major credit are distinct concepts.
5. **A credible narrow prototype beats a broken all-campus catalog.** Ship verified CS + Math first.
6. **Fast what-if exploration.** Users can compare choices without changing an official student record.
7. **Accessible and resilient.** Support keyboard operation, textual status alongside color, and offline sample data.

# 2. Product scope and release tiers

## 2.1 P0 — release-blocking MVP

| ID | Feature | Required behavior and acceptance |
|:--|:--|:--|
| FR-01 | Program selection | Select Computer Science and Mathematics; selected programs update the audit and plan |
| FR-02 | Student profile | Mark completed courses; separately mark prerequisite waivers; select start term, number of terms, and credit budget |
| FR-03 | Course explorer | Search/filter sample courses; inspect course title, credits, department, source, and data status |
| FR-04 | Prerequisite network | Directed edges; labels for Completed / Eligible / Planned / Blocked / Unknown; zoom, pan, select node |
| FR-05 | Eligibility engine | Deterministic `all`, `any`, and course prerequisites; explain missing conditions; never give credit for waiver alone |
| FR-06 | Degree/major audit | Show requirement completion and degree credits in separate metrics, with conservative uncertainty warnings |
| FR-07 | Semester planner | Generate a provisional, dependency-respecting term plan within a user-configurable credit budget; expose unscheduled classes |
| FR-08 | Dynamic recalculation | A profile change updates eligible courses, graph, progress, and plan without page refresh |
| FR-09 | Provenance & disclaimers | Show sourced vs provisional rules and clearly say this is not an official degree audit |
| FR-10 | Demo/test harness | One synthetic student, deterministic expected outcomes, runnable unit tests, and a polished end-to-end demo |

**MVP data boundary:** approximately 20–30 accurately sourced, relevant CS + Math courses *if possible during the event*. A smaller verified dataset is acceptable. Use synthetic, prominently labeled examples where official data remains unconfirmed. Never assert that a hypothetical edge is official.

## 2.2 P1 — competitive enhancements after P0 works

- **Richer requirements:** required classes; choose-N electives; minimum departmental/upper-level credits; allowable alternatives and approval-dependent credit.
- **Credit policy indicators:** degree credits, major-applicable credits, department/division counters, and transfer-credit limits—only when policies are verified and correctly scoped.
- **Better planning explanations:** “CSC-X moved from spring to fall because its prerequisite was not satisfied,” with source and confidence level.
- **Persistence and export:** browser-local saved profile, JSON export/import or printable provisional plan; no account required.
- **Course detail enrichment:** link to official catalog/department page, description, known season offerings, major/concentration applicability.
- **UI refinements:** planned-vs-eligible legend, minimap, hover dependencies, responsive sidebar, filtering by program/semester/department.

## 2.3 P2 — post-MVP and future roadmap

- More majors and concentrations, catalog-year versions, departmental exceptions and full double-major auditing.
- Approved study-away program mapping and transfer/equivalency review workflow.
- **Read-only** officially authorized COLSS data connector if an appropriate supported interface is available.
- Schedule collision detection, section selection, instructor/time preferences, and seat availability only from approved current data.
- Better scheduling optimization (e.g., objective-driven constraint programming), alternative plans and graduation-year comparison.
- Change monitoring for future catalog versions; **potential upcoming curriculum changes always flagged as speculative until enacted**.
- Optional natural-language AI *explanations* backed by the deterministic rule engine, not AI-created eligibility decisions.

## 2.4 Explicit non-goals for hackathon day

No official registration or adviser signoff; no collection of COLSS passwords or student records; no login-protected scraping; no FERPA-sensitive test data; no guarantee of future offerings, course seats, or early-graduation approval; no full-campus catalog promise; no blockchain integration; no separate server or database unless needed for a proven MVP requirement.

# 3. User journeys and interface specification

## 3.1 Primary happy-path journey

1. Open CourseGraph and load the labeled **synthetic demo profile**.
2. Select **Computer Science** and **Mathematics** as program goals.
3. Mark two or more courses completed and a separate CSC prerequisite placement/waiver.
4. View the graph: green Completed, blue Eligible, gray Blocked, purple Planned, amber Unknown (also show text/icons).
5. Click a blocked course; read the exact unsatisfied dependency and source status.
6. Press **Generate Plan** (or allow instant recomputation) to see a 4-year plan organized by Fall/Spring.
7. Change the waiver, term credit limit, program selection, or start term.
8. Observe the network, audit, and projected terms change together; optionally show a “what changed” summary.
9. View warnings and click official sources. Export a tentative plan if implemented.

## 3.2 Secondary journeys

**Major exploration:** switch from CS to CS + Math; show additional requirements and a changed remaining path. **External credit:** enter a test AP/transfer award with 4 degree credits but pending major approval; show overall credit update while major progress does not falsely increase. **Study-away:** mark a future term off campus; show eligible placeholders with approval required, not a guaranteed mapped course. **Unfeasible plan:** reduce credit budget or number of terms until required work does not fit; show a clear infeasibility/unscheduled warning rather than silently omitting courses.

## 3.3 Main screen layout

| Area | Contents | Design expectation |
|:--|:--|:--|
| Header | CourseGraph branding, catalog-year badge, demo-data notice, save/export action | Instantly identifiable as Grinnell-focused |
| Left controls | Major/concentration picker, completed courses, waivers, external credits, term/credit settings | Controls grouped by intent; labels explain waiver vs credit |
| Central canvas | Interactive prerequisite graph with arrows, course states, zoom/pan, search/filter | Nodes readable; show dependency direction |
| Right panel | Selected course details, reason blocked/eligible, verified source, alternatives | Never hide uncertainty |
| Lower panel / tabs | Major progress, credit audit, semester-by-semester roadmap, warnings and changes | Visible effect of any user input |

**Responsive behavior:** desktop-first for judged demo; on narrow screens, stack controls and use tabs so the graph remains usable. **Accessibility:** text labels alongside color; keyboard-focusable controls; high-contrast states; non-color-only error icons; sensible loading/empty/error states.

## 3.4 State vocabulary

- **Completed:** recorded as completed in the profile; must not automatically imply an approved major requirement if the record is external or invalid.
- **Eligible:** all implemented, verified prerequisite conditions are satisfied and there is no known blocking condition. This does **not** mean a seat is available or registration approved.
- **Blocked:** an explicitly required condition is not satisfied.
- **Planned:** scheduled in a provisional future term; eligibility for that term must be evaluated against completed work in prior terms.
- **Unknown:** missing source, permission-only rule, unsupported conditional, missing future offering data, or unresolved approval. Display what is unknown.

# 4. Academic policy engine and correctness constraints

## 4.1 Source hierarchy and versioning

When sources differ, use the **applicable catalog year and official Registrar policy first**, then departmental pages/advising guides, then public term-specific course listings. A department's example four-year plan is guidance, not proof that a course will be offered in a future term. Store `sourceId`, URL, page title, checked date, applicable catalog year and verification status (`verified`, `provisional`, `unknown`) on each rule or assertion.

The 2026 CS departmental advising guide explicitly notes *planned* curriculum changes for Fall 2027. Therefore CourseGraph must preserve `catalogYear` and avoid projecting the current CS requirements onto future cohorts as certain. [S5]

## 4.2 Academic facts and prototype implications

| Policy area | Research finding / status | Required behavior |
|:--|:--|:--|
| Graduation credits | Grinnell states 124 credits are required; includes Tutorial and a major. [S1] | Degree progress metric uses a sourced 124-credit target for the applicable cohort, with a caveat that other conditions also apply |
| Major credits | Majors are commonly 32–40 credits; requirements are program-specific. [S1] | Do not infer every major is exactly 32 credits; load program-specific verified rules |
| Tutorial | First-Year Tutorial is an academic requirement, subject to applicable entry/transfer exceptions. [S1][S7] | Model it as a standalone degree condition; do not count toward major unless current official rules permit it |
| Department limit | The 2026–27 AP policy refers to a 48-credit departmental limit and exempts AP/IB/A-level/CAPE credits from that departmental counting rule. [S2] | Implement only with verified counting rules and course/credit classification; display a warning if scope/exception is unknown |
| Division limit | Older publications refer to a 92-credit division limit, but current applicability and precise exceptions need catalog-year confirmation. [S11] | **Do not silently enforce** a 92-credit threshold as verified in the MVP |
| AP/IB/A-level awards | 2026–27 AP policy: awarded credits count toward 124, may satisfy prerequisite via listed equivalency, and count toward major only when explicitly labeled for major credit. [S2] | Track three separate flags; handle duplicate equivalency/cancellation policies conservatively |
| Transfer credit | Grinnell describes limits and departmental review of major requirement substitutions. [S1] | Track award and program applicability independently; unknown/pending approval does not become major credit |
| Study away | Advising recommends checking major/concentration sequencing; departments may need to approve major credit. [S8][S9] | Show “pending departmental approval” and impact on sequencing; no automatic major credit |
| Course offerings | Current schedule is term-specific; catalog lists courses but not reliably future term offerings. [S4] | Known offering applies only to matching term; unknown future offerings create tentative plan items |
| Double major | Program-specific requirements and limits must be checked in the applicable catalog. | Degree credits earned by a course are counted once; cross-major requirement overlap must not be assumed approved |
| Waiver/placement | A prerequisite waiver is not inherently a credit award. | Waiver changes prerequisite satisfaction, never earned credits by itself |

**Implementation warning:** “48 departmental” and “92 divisional” are not interchangeable. They need correctly defined countable credit groups, institution-specific exemptions, catalog year, and separate audit messages. Never simply sum all science classes and label it a verified rule violation.

## 4.3 The four credit questions must remain separate

For any course or outside award, represent independent dimensions:

1. **Requirement satisfaction:** Did this action satisfy a prerequisite or named requirement?
2. **Degree credits:** How many earned credits apply to the 124-credit total?
3. **Major credits:** How many may count toward each specific major or concentration?
4. **Department/division classification:** How do those credits apply to relevant caps or floors?

A waived CSC prerequisite might clear access to CSC 207 but add **zero degree and major credits**. An AP score may provide degree credit and a prerequisite equivalent but not major credit. A study-away course may provide degree credit while remaining unapproved for a major. Surface these outcomes explicitly.

## 4.4 Rules representation

Use machine-readable rules for `all`, `any`, `course`, `permission`, and `concurrent` conditions. Sample expression:

```json
{
  "kind": "any",
  "rules": [
    { "kind": "all", "rules": [
      { "kind": "course", "courseId": "EXAMPLE-101" },
      { "kind": "course", "courseId": "EXAMPLE-102" }
    ]},
    { "kind": "permission", "description": "Instructor permission" }
  ]
}
```

**This is illustrative schema data, not a Grinnell prerequisite.** An AND/OR rule is not identical to a simple directed graph: draw edges for visual dependencies, but use the full logical expression for eligibility. A permission-only rule unresolved in the demo returns `unknown`, not “eligible.” Concurrent enrollment is allowed only when explicitly supported and coded correctly.

## 4.5 Audit and error handling

- Award each completed course's degree credits **once**; two selected majors must not double the degree total.
- For a program-specific audit, only credits with relevant approval and correct requirement mapping count toward that program.
- Detect cycles in prerequisite data, invalid course references, duplicate identifiers, malformed JSON, contradictory rules, or missing source evidence.
- Keep unknowns in warnings. Never collapse “not verified” into “false” or “true” without explanation.
- Plan feasibility means **feasible under the implemented, verified constraints**—not a promise of graduation or course enrollment.

# 5. Scheduling and graph algorithms

## 5.1 Prerequisite dependency graph

Represent a course as a node and a strict prerequisite as a directed edge `prerequisite → dependent`. Use graph traversal to find upstream blockers, reachable courses, descendants and cycles. Use a topological sort only for a DAG of strict course dependencies; preserve AND/OR information separately. Display valid alternatives and permissions in the course details panel.

## 5.2 Eligibility calculation

**Input:** course records, student profile, awarded/waived equivalents and supported rules. **Output:** record per course containing `status`, `missing[]`, and human-readable `reasons[]`. Apply precedence and short-circuit rules carefully: `completed` overrides normal eligibility display; satisfied alternative prerequisites can unlock a course; unresolved instructor permission or unsupported concurrency yields `unknown` unless another verified path fully satisfies the rule.

## 5.3 Initial semester planner (heuristic, not proven optimum)

1. Determine selected program requirements and distinguish necessary from optional candidates.
2. Subtract completed requirements, verified equivalencies, and any specifically authorized substitutions.
3. Build strict dependency relations; detect missing or cyclic references before scheduling.
4. For each future semester, collect courses eligible at its **start**, considering previously completed or earlier-term planned courses only.
5. Filter against known Fall/Spring offerings; if term availability is unknown, place only tentatively and label it.
6. Rank useful candidates by critical-path dependency length, scarcity of known offering windows, requirement importance, and configurable student preferences.
7. Add candidates while satisfying the per-term credit budget and explicit concurrency restrictions; leave unresolved course choices marked as provisional.
8. Advance to the next semester; emit planned terms, unscheduled courses, conflicts and explanations.
9. If target completion cannot be proved, say so; do not declare an “optimal” or “guaranteed” graduation date.

**Hard invariant:** A strict prerequisite scheduled in term `t` cannot unlock a dependent in the same term `t`; only a verified corequisite rule may allow concurrency. Course-seat and time-collision checks are out of MVP scope unless trustworthy section data is available.

## 5.4 Dynamic recalculation pipeline

```text
User edits profile (major, completion, waiver, credit limit, term)
    ↓
Validate immutable StudentProfile update
    ↓
getEligibility(courses, profile)
    ↓
auditPrograms(courses, programs, profile)
    ↓
generatePlan(courses, programs, profile)
    ↓
React renders graph + course details + audit + semester plan
    ↓
Optional comparison explains what changed
```

Use one source of truth and memoized derived computations. Avoid separate mutable copies of eligibility or progress. For the small curated dataset, client-side recalculation should be immediate on typical laptops. Measure if datasets grow.

# 6. Architecture and integration contracts

## 6.1 Locked hackathon architecture

**Frontend:** React + Vite + TypeScript. **Graph:** `@xyflow/react`. **Engine:** pure, deterministic TypeScript under `src/engine`. **Data:** local JSON with provenance under `src/data`. **Tests:** Vitest. **State:** React owner component in `App.tsx`. **No server required** to perform the MVP “backend” automation. If a post-hackathon connector is needed, extract a read-only import adapter rather than rebuilding the engine.

**Why this is pragmatic:** one install, one application, no login or API secrets, minimal cross-origin/deployment failure, and four teammates can own separate files. Do not switch to Python + Streamlit midstream without a unanimous, documented architecture decision and revised contracts.

## 6.2 Repository layout and ownership

```text
coursegraph/
  AGENTS.md                    # team rules and AI assistant instructions
  docs/
    CONTRACTS.md              # canonical interfaces and schemas
    DATA_NOTES.md             # verification and uncertainties
    DEMO.md                   # tested demo sequence and backup
  src/
    App.tsx                   # P4: integration/state
    main.tsx                  # P4: entrypoint
    components/               # P1: UI / graph controls
      ProgramPicker.tsx
      ProfileEditor.tsx
      CourseNetwork.tsx
      CourseDetails.tsx
      ProgressDashboard.tsx
      SemesterPlan.tsx
    engine/                   # P2: pure domain logic
      types.ts
      eligibility.ts
      audit.ts
      planner.ts
      __tests__/
    data/                     # P3: verified/provisional data
      courses.json
      programs.json
      policies.json
      sources.json
      demoProfile.json
    styles/                   # P1: UI styles
  package.json                # P4: scripts and dependencies
  README.md                   # P4: install, scope, caveats
```

**Person labels P1–P4 here refer to teammates, not feature priorities P0/P1/P2.** Each file has one owner at a time. If two AI assistants need the same file, the integration lead mediates and coordinates a small PR.

## 6.3 Canonical domain contracts

The pre-existing team's `docs/CONTRACTS.md` is the source of truth for exact TypeScript definitions. Preserve these exports unless the team approves a versioned change:

```ts
export function getEligibility(
  courses: Course[], profile: StudentProfile
): Record<string, Eligibility>;

export function auditPrograms(
  courses: Course[], programs: Program[], profile: StudentProfile
): Audit;

export function generatePlan(
  courses: Course[], programs: Program[], profile: StudentProfile
): PlanResult;
```

**Essential entities:** `Course` (ID, credits, prerequisites, known offerings, source and verification); `Program` (major/concentration requirements); `StudentProfile` (selected programs, completed courses, separate prerequisite waivers, external credits, term constraints); `ExternalCredit` (degree credit, course equivalence, major approval); `Eligibility`; `Audit`; `PlannedTerm`; `PlanResult`; `SourceRef`.

The working contract provides concrete TypeScript interfaces. Any richer v2 model—grades, multiple versions, catalog-year overrides, conditional credit-cap classifications, explicit waiver types, section times—must be reviewed by the backend owner and data owner, updated in the contracts file, and migrated across all components before merge. **Do not let separate AI assistants invent competing schemas.**

## 6.4 Component contract and state flow

```ts
ProgramPicker({ programs, selectedIds, onChange })
ProfileEditor({ courses, profile, onChange })
CourseNetwork({ courses, eligibility, selectedCourseId, onSelectCourse, plannedCourseIds })
CourseDetails({ course, eligibility, sourceRefs })
ProgressDashboard({ audit })
SemesterPlan({ plan })
```

These are integration signatures, not separate apps. `App.tsx` owns the current `StudentProfile`; components emit controlled updates, and the engine returns derived results. The frontend cannot overwrite audit logic, and the engine cannot import React components.

## 6.5 Data contracts and source quality

Every claim should carry `verification`, `sourceIds`, `checkedAt`, and `catalogYear` when possible. The curated `courses.json`, `programs.json`, `policies.json`, and `sources.json` must be internally consistent and syntactically valid. Store the checked-at timestamp in the appropriate source record. Provide a runnable validator or explicit test to verify unique course IDs, valid prerequisites, supported term seasons, no dangling source references, and no impossible self-dependencies.

**Data modes:** `verified` = traceable to an official applicable source; `provisional` = team assumption or plausible example; `unknown` = insufficient evidence. The visible UI must not make provisional information look official. All demo profile data must be fictional.

# 7. COLSS / Ellucian research plan

## 7.1 What exists and what is unknown

Grinnell maintains a public COLSS course-search interface at `https://colss-prod.ec.grinnell.edu/Student/Courses`, and the College links to Colleague Self-Service for registration, degree progress and four-year planning. [S3][S4][S10] **A public browser page is not evidence of a supported, documented public API.** Treat API availability and reuse permissions as unconfirmed until verified.

## 7.2 Safe discovery checklist (data teammate)

1. Inspect Grinnell's official Academic Catalog, Registrar, course search, and advising pages; record provenance and catalog-year applicability.
2. Determine which data are publicly viewable without signing in: course IDs, titles, credits, prerequisites, section offerings and terms.
3. Check any published usage terms, robots restrictions and developer/API documentation. Do not bypass access controls or use private endpoints simply because the browser happens to request them.
4. Prefer a small manually curated, sourced JSON dataset for the hackathon.
5. If a supported authorized read-only interface is discovered, prototype an **offline import step** to JSON; do not make the live demo depend on network reliability.
6. Never request teammates' COLSS credentials, session cookies, access tokens, transcripts, or private student records.

**Go/no-go:** If a supported route to data cannot be established quickly, stop investigation and ship curated data. The graph and deterministic planner are the differentiators, not scraping an entire catalog.

# 8. Four-person execution plan

## 8.1 Roles, outputs and responsibilities

| Teammate | Owns | Minimum shippable output | Important coordination |
|:--|:--|:--|:--|
| **P1 — Frontend & visualization** | `src/components/*`, `src/styles/*` | Functional major picker, profile inputs, interactive dependency graph, detail and semester views | Import engine types; no invented eligibility calculations in components |
| **P2 — Backend logic** | `src/engine/*`, engine tests | Eligibility + audit + deterministic plan with explanations and edge-case tests | Publish types and return shapes **early**; negotiate schema with P3 |
| **P3 — Data & policy research** | `src/data/*`, `docs/DATA_NOTES.md` | Sourced CS + Math dataset; source registry; demo profile; uncertainty log | Never assume degree rules from memory or old catalog; coordinate with P2 |
| **P4 — Integration, QA & presentation** | `App.tsx`, config/scripts, README, demo, pitch | App bootstraps, modules merge, full workflow tested, clear pitch | Integration is a **coding role**; slides are not a full-day job |

**Recommended assignment:** strongest algorithmic teammate owns P2; strongest UI developer owns P1; detail-oriented researcher owns P3; best integrator/presenter owns P4. All four should be able to explain their contributions and the major system boundaries. Collaboration is measured by end-to-end function, not AI-generated line count.

## 8.2 Shared AI-assistant directive (paste into every agent)

> You are contributing to a **single four-person CourseGraph repository**, not building your own application. Read `AGENTS.md` and `docs/CONTRACTS.md` completely and inspect existing files before writing code. Your role is **[ROLE]**, and your owned files are **[FILES]**. Follow React + Vite + TypeScript, React Flow, pure deterministic TypeScript engine functions, curated JSON, and Vitest. Preserve all shared signatures and data keys. Never edit another role's files, add dependencies, or change the stack without integration-lead approval. Implement one small testable milestone, run the relevant commands, and report the exact files changed, exported functions, input/output expectations, actual test results, known limitations, and merge instructions. Do not invent official academic requirements or claim a plan is guaranteed. If a collaborator's module is missing, use an isolated mock that adheres to the agreed interface. Your code should be understandable enough for a teammate to defend to judges.

## 8.3 Branching, merge and review discipline

- One GitHub repository, initial buildable `main`, short-lived `feature/frontend`, `feature/engine`, `feature/data`, and integration changes by P4.
- Branch from current `main`; make small commits; push and open PRs; P4 reviews conflicts and merges frequently.
- **First integration checkpoint within roughly the first quarter of build time.** Use stub functions and sample data; do not wait until every component is complete.
- Never force-push shared `main`, copy entire alternate apps into the repository, or let an AI tool refactor teammates' modules without consent.
- Before merging, run `npm run build`, relevant Vitest suite, and a one-minute smoke demo. If failing, fix or revert the PR.
- Changes to `Course`, `Program`, `StudentProfile`, `getEligibility`, `auditPrograms`, `generatePlan`, or JSON keys require a documented interface change approved by P2, P3, and P4.

## 8.4 Illustrative one-day timetable (relative to official start)

| Phase | Suggested share | Exit criterion |
|:--|:--|:--|
| Align & bootstrap | 0–15% | One idea, locked interfaces, running Vite skeleton, team branches, mock dataset |
| Parallel build | 15–50% | UI, engine, and real curated data individually produce a tested artifact |
| First full integration | By ~50% | Profile control changes graph + initial audit + rough plan in one app |
| Stabilize and refine | 50–80% | Critical tests pass, explanations/source notes present, edge cases handled |
| Feature freeze + presentation | Last 20% | No new functionality; rehearse scripted demo, screenshots, backup, submission |

**Kill switches:** If a verified data import is too slow, use bundled JSON. If the advanced scheduler fails, use a transparent deterministic heuristic. If complete double-major requirement auditing is impossible, show correctly labeled partial progress. If the graph library causes instability, use a simpler but still interactive dependency view. Never fabricate plan validity or achievements.

# 9. Test plan and release acceptance

## 9.1 Critical engine unit tests

| Test | Fixture | Expected result |
|:--|:--|:--|
| UT-01 | Course with no prerequisite | Eligible when not completed |
| UT-02 | A is prerequisite for B, A not completed | B blocked, reason names A |
| UT-03 | A completed | B eligible |
| UT-04 | `any(A,B)` and `all(A,B)` | OR passes with one; AND requires both |
| UT-05 | Waive A only | B may unlock; earned degree credits do not increase |
| UT-06 | Same course contributes to two program requirement checks | Degree credits counted only once |
| UT-07 | External credits with pending major approval | Degree credit only if award valid; major credit is not silently accepted |
| UT-08 | Strict prerequisite A→B | A and B not planned in same term as sequential courses |
| UT-09 | Term budget and published offering | No overload or placement in a definitively unavailable season |
| UT-10 | Unknown future offering | Tentative placement + explicit warning |
| UT-11 | Cycle or dangling prerequisite ID | Warning/error; no falsely confident plan |
| UT-12 | Change major, waiver, or credit cap | Plan/audit/eligibility recompute coherently |
| UT-13 | Impossible term limit | Unscheduled requirements are reported, not dropped |
| UT-14 | Unknown permission requirement | Unknown status unless an independently valid alternative exists |

## 9.2 Visual and integration acceptance

- `npm install`, `npm run dev`, `npm run build`, and `npm run test` succeed on a teammate's clean checkout.
- The synthetic CS + Math scenario runs without login, live APIs, private files or network dependencies.
- Graph edges point from prerequisite to dependent; node statuses have visible text, not just color.
- A waiver modifies eligible nodes and the future schedule but **never** earned credits.
- A click on a blocked node explains missing dependencies; unknown rules show a distinct warning.
- All required P0 elements render together, with no blank screens, stale values, or uncaught errors.
- Data/provenance links work; all provisional data are visibly labeled; screenshots match actual app behavior.
- User can recover from empty selections, inconsistent profile inputs or infeasible schedule without a crash.

## 9.3 Quality expectations

**Performance:** responsive changes on the curated dataset (target subjectively instantaneous; profile only after measurement). **Reliability:** deterministic engine for identical inputs; no unexpected reliance on API calls. **Security:** no account integration, secret tokens or personal data in Git. **Accessibility:** labels, focus, contrast and color-independent statuses. **Reproducibility:** README includes exact commands, platform assumptions and known limitations.

# 10. Presentation, judging and demo script

## 10.1 Two-minute live demo outline

| Time | Presenter action | Message |
|:--|:--|:--|
| 0:00–0:20 | State problem, show scattered planning questions | A flexible curriculum can be surprisingly difficult to navigate |
| 0:20–0:40 | Select CS + Math and completed classes | CourseGraph personalizes the academic map |
| 0:40–1:05 | Click a blocked node, show why; toggle a waiver | A waiver can unlock a path **without** granting credits |
| 1:05–1:30 | Generate / inspect semester plan; change credit budget | The schedule recalculates from real constraints |
| 1:30–1:45 | Highlight policy/source warnings and how rules are computed | Explainability and academic accuracy matter |
| 1:45–2:00 | Close with Grinnell impact and future approved integrations | More accessible, transparent planning; not a substitute for advisers |

**Demo highlight:** Before changing the waiver, pause to let judges see the blocked status and planned term; then toggle it and narrate the exact visible change across multiple panels. If the chosen waiver doesn't change the plan under a particular fixture, adjust the synthetic fixture before judging—never force a fabricated effect.

## 10.2 Slide structure (if presentation format requires slides)

1. **Problem:** Course choices depend on policies, prerequisite chains, major goals and constraints.
2. **Product:** One interactive map, requirement audit, and semester plan.
3. **Live demo:** Profile → graph → what-if change → plan recalculation.
4. **Technical depth:** Graph algorithms, structured rule evaluation, deterministic scheduler, provenance-rich data.
5. **Impact and future:** Best Hack for Grinnell fit; interdisciplinary reasoning; approved catalog integrations, study-away workflow and adviser collaboration.

## 10.3 Talking points for judging questions

- **Why not use existing COLSS?** COLSS supports official course and academic-planning tasks; CourseGraph adds a visual dependency model, inspectable explanations and fast hypothetical comparisons. It does not replace official records. [S10]
- **Is the plan optimal?** No; initial planner is a deterministic heuristic and flags unknown future offerings. Optimization is a future extension.
- **How are waivers treated?** They can satisfy prerequisites but do not by themselves award degree/major credits.
- **Where does the data come from?** A curated, sourced Grinnell sample with source/version metadata; unsupported future information is marked uncertain.
- **Why interdisciplinary?** CS graph and scheduling algorithms + academic policy interpretation + UX and student advising.
- **What would deployment require?** Verified current catalog policy mapping, registrar/adviser review, source refreshes, data rights, and privacy/accessibility review.

# 11. Risks, assumptions and open decisions

| Risk | Likelihood / severity | Owner | Mitigation or fallback |
|:--|:--|:--|:--|
| COLSS has no usable approved API | High / Medium | P3 | Do not integrate live; curated JSON |
| Incorrect or outdated prerequisite data | High / High | P3 + P2 | Source year and verified status; demonstrably synthetic fixtures |
| Conflicting academic counting rules | Medium / High | P2 + P3 | Distinct credit dimensions; unknown until verified; warning rather than false audit |
| Team AI agents generate incompatible shapes | High / High | P4 | Locked `CONTRACTS.md`, exported types early, file ownership, small PRs |
| Graph rendering or build fails near deadline | Medium / High | P1 + P4 | Early skeleton, early integration, static dependency list fallback |
| Full semester optimizer exceeds time | High / Medium | P2 | Deterministic greedy plan clearly labeled heuristic |
| Demo requires network or student credentials | Medium / High | P4 | Offline fixture and local run; no credential use |
| Hackathon judging criteria differ | Medium / Medium | P4 | Confirm award list, AI rules, timing and submission format at registration |
| Future curriculum changes invalidate sample | Medium / High | P3 | Catalog-year selector, source metadata, warning for unapproved changes |

**Open decisions to resolve at kickoff:** (1) exact event deadline and judging format; (2) which official catalog version applies to the synthetic example student; (3) which 20–30 courses can be verified; (4) whether to display a 4-year or an accelerated scenario first; (5) whether example external credit will be demonstrated; (6) selected fallback if graph library/deployment fails; (7) whether there is a separate Best Overall prize.

# 12. Milestone checklist and definition of done

**M0 — Contract:** repo runs; schema and function exports approved; synthetic profile agreed; P4 has the demo script. **M1 — Thin vertical slice:** change a completed course → eligibility status changes → graph node updates. **M2 — Useful planner:** a multi-semester plan exists, respects strict prerequisites and credit budget, and reports unscheduled courses. **M3 — Academic audit:** graduation credits and major progress are clearly differentiated, with safe handling of waivers/external credits. **M4 — Source trust:** relevant policy/offerings have source links or visible warnings. **M5 — Submission:** fresh-clone run/build/test succeed, walkthrough rehearsed, screenshots/backup captured, team understands their code.

**Release definition:** The project is “ready” when all P0 capabilities work in one app, critical tests pass, a human can explain the logic, synthetic data are clearly marked, and the demo illustrates a genuine recalculation. Additional features do not count as progress if they destabilize this path.

# Appendix A. Implementation handoff checklist for every AI-assisted teammate

For every meaningful PR, return this exact checklist:

- **Role/branch:** who owns the change and what branch is used.
- **Files:** added/modified files and purpose; confirm no unauthorized edits.
- **Contract:** imported/exported types, function signatures, input and output examples.
- **Tests:** exact commands actually executed and results; state tests not run.
- **Manual verification:** steps to see behavior in the running app.
- **Limitations:** unresolved rules, unsupported cases, provisionally sourced facts.
- **Integration notes:** dependency added, interface migration needed, or PR review instructions.
- **Next smallest step:** one clear action to move the full demo forward.

# Appendix B. Shared interface examples

```ts
// Function signatures shared across ALL AI assistants.
export function getEligibility(
  courses: Course[], profile: StudentProfile
): Record<string, Eligibility>;

export function auditPrograms(
  courses: Course[], programs: Program[], profile: StudentProfile
): Audit;

export function generatePlan(
  courses: Course[], programs: Program[], profile: StudentProfile
): PlanResult;
```

```ts
// Illustrative, *not* a Grinnell catalog fact.
const sampleProfile = {
  selectedProgramIds: ["CS_MAJOR", "MATH_MAJOR"],
  completedCourses: ["EXAMPLE-101"],
  waivedPrerequisiteCourseIds: ["EXAMPLE-102"],
  externalCredits: [],
  startYear: 2027,
  startSeason: "Spring",
  numberOfTerms: 8,
  maxCreditsPerTerm: 16,
};
```

# Appendix C. Verified research sources and provenance

**Checked November 21, 2026.** These URLs are cited as source references throughout. Catalog-year applicability still must be checked for each specific student and program.

- **[S1] Grinnell College, Family Resources: Academics** — 124 credits, tutorial and major, transfer-credit context, general planning expectations. https://www.grinnell.edu/families/academics
- **[S2] Grinnell College, 2026–27 Advanced Placement Policy** — distinct general / prerequisite / major-credit treatment; 24-credit limit for first-time first-year students; departmental exemption statements. https://www.grinnell.edu/about/leadership/offices-services/registrar/resources-students/advanced-placement
- **[S3] Grinnell College, Colleague Self-Service public course search** — public course search landing page; *not proof of a public API*. https://colss-prod.ec.grinnell.edu/Student/Courses
- **[S4] Grinnell College, Prepare for Your First Registration** — catalog versus semester schedule, current registration course search context. https://www.grinnell.edu/academics/advising/new-student-registration
- **[S5] Grinnell College, Computer Science Departmental Advising Guide** — sample paths and warning about anticipated Fall 2027 curriculum revisions. https://www.grinnell.edu/academics/advising/advising-guide/computer-science
- **[S6] Grinnell College, Mathematics Course Sequence** — department's course sequence and major credits context; confirm current catalog for enforceable rules. https://www.grinnell.edu/academics/majors-concentrations/math/course-sequence
- **[S7] Grinnell College, Teaching Tutorial** — tutorial requirement and exception context. https://www.grinnell.edu/about/leadership/offices-services/dean/teaching-tutorial
- **[S8] Grinnell College, Study Away Advising** — need to plan course sequencing and consult advisers. https://www.grinnell.edu/academics/global/ocs/advising
- **[S9] Grinnell College, Off-Campus Study in Computer Science** — departmental considerations and approval questions for off-campus credit. https://www.grinnell.edu/academics/majors-concentrations/computer-science/off-campus
- **[S10] Grinnell College, Academic Resources / Registration and Planning** — links to COLSS registration, degree progress and four-year planning. https://www.grinnell.edu/students/academic
- **[S11] Grinnell archived catalog / materials** — historical 48-credit departmental and 92-credit divisional language, *not sufficient for confirming current applicability*. https://catalog.grinnell.edu/mime/media/8/718/catalog2003.pdf

**Research discipline:** a source's existence does not validate every rule we would like to encode. Enter the **exact applicable text, year, scope, exceptions and source** into the data log before implementing any high-stakes credit-policy rule. If unverified, show a warning and require adviser/Registrar confirmation.
