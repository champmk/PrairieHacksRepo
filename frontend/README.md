# CourseGraph front end

Design and flow prototype. Runs on sample data; no endpoints are connected yet.

```
npm install
npm run dev        # http://127.0.0.1:5320
npm run build      # typecheck + production build
npm run test:engine
```

## Screens

- **Onboarding** — pick up to two majors, then credits import (mocked).
- **Schedule** — collapsible course catalog beside a week calendar; full-screen calendar; one section per course; time clashes flagged; current term is read-only.
- **Four-year plan** — eight semester nodes. Completed, enrolled, planned and open courses show as icons. Major placeholders expand to the interchangeable options. Every future term has a + to add any course. Drag courses between terms or use the row menu. Hover a course to see its prerequisite lines. The requirements panel tracks each major, and undo reverts the last change.

## Where the backend plugs in

All data goes through `src/api/client.ts`. Each function there names the endpoint it stands in for (`GET /programs`, `GET /courses`, `GET /sections`, `GET /demo-profile`, `POST /recalculate`). Replace the bodies with `fetch` calls; components do not change.

`src/engine/planner.ts` is a mock of `POST /recalculate` so the plan reflows while we design. The real optimizer lives in the backend.

`src/data/` holds sample courses, requirements and sections. They are illustrative, not official Grinnell rules. The two Spring 2027 CSC-151 sections follow the example in `docs/backend/examples`.
