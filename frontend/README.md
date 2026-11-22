# CourseGraph front end

React + Vite + TypeScript. Talks to the Python backend in `../backend` through `/api` (Vite proxies it to `127.0.0.1:8100`). The contract is `../backend/CONTRACT.md`.

```
# terminal 1 (backend)
cd backend
python -m uvicorn coursegraph.api:app --port 8100

# terminal 2 (front end)
cd frontend
npm install
npm run dev        # http://127.0.0.1:5320
```

If the backend is not running, the app says so and shows the command.

## Pages

**Onboarding.** Pick up to two majors, then review the credits loaded from the student record. Withdrawn and failed courses show as not counted.

**Course Picker** (page 1) covers the current term (registered, read-only) and the next term (planning):

- A filter bar for time, days, major courses, department and open seats.
- A collapsible catalog that starts with the courses your 4-year plan puts in that term.
- A week calendar that can go full screen.

Picking a section saves it to the student database as *planned*. Planned is only possible here, because only these terms have real sections. Clashes are flagged, and you can switch sections from a class popover.

**4-Year Plan** (page 2) shows eight semester nodes in a row, each holding course tablets:

- **Marks:** R means the tablet must satisfy a major requirement. ✓ means completed and counted.
- **Borders:** yellow dash is planned (from page 1), blue dash is in progress.
- **Clicking a tablet** opens the sidebar with only the courses that can fill it. Non-R tablets and **+** offer the whole catalog.
- **The pencil** turns on edit mode: ⊖ deletes a tablet and ⇄ swaps it. Past and in-progress tablets are locked.
- **Warnings** draw an arrow from the tablet to the earlier node that is missing something, ending in ⚠.

Arrows are laid out by `src/components/plan/layout.ts`. Lanes are assigned by interval partitioning, the gutter height follows the lane count on an 8 px grid, and corners are right angles. Arrows never share a lane segment.

## Where things live

- `src/api/` holds the HTTP client and the contract types.
- `src/state/useCourseGraph.ts` keeps the current student, majors and page-2 edits (with undo), and re-plans on every change.
- `src/components/CoursePicker.tsx` and `WeekCalendar.tsx` make up page 1.
- `src/components/plan/` holds page 2: the nodes, tablets, sidebar and arrow layout.
