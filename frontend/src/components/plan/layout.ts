// Warning-arrow layout for the four-year graph.
//
// Every arrow runs from a tablet in node k back to node j (j < k). Arrows
// travel through a gutter of horizontal lanes above the nodes. Lanes are
// assigned by interval partitioning: shortest spans first, each into the
// lowest lane whose existing spans do not overlap it, so two arrows in one
// lane never share horizontal space. The gutter height follows the lane
// count, snapped to an 8px grid, so arrows are always visible.

export const LANE = 16; // px between lanes
export const GRID = 8;
export const snap = (v: number, g = GRID) => Math.round(v / g) * g;

export interface Span {
  id: string;
  from: number; // source node index (k)
  to: number; // target node index (j)
}

export function assignLanes(spans: Span[]): { lane: Record<string, number>; lanes: number } {
  const sorted = [...spans].sort(
    (a, b) =>
      Math.abs(a.from - a.to) - Math.abs(b.from - b.to) ||
      Math.min(a.from, a.to) - Math.min(b.from, b.to) ||
      a.id.localeCompare(b.id),
  );
  const taken: [number, number][][] = [];
  const lane: Record<string, number> = {};
  for (const s of sorted) {
    const l = Math.min(s.from, s.to);
    const r = Math.max(s.from, s.to);
    let i = 0;
    while (taken[i]?.some(([a, b]) => l <= b && a <= r)) i++;
    (taken[i] ??= []).push([l, r]);
    lane[s.id] = i;
  }
  return { lane, lanes: taken.length };
}

/** Gutter height for a lane count: lanes × LANE plus breathing room, on the grid. */
// 40px of headroom stays clear for the strip above the lanes (prior credit, hints).
export const gutterFor = (lanes: number) => snap(lanes * LANE + 48);

export interface Box {
  left: number;
  top: number;
  width: number;
  height: number;
}

export interface Routed {
  id: string;
  d: string; // SVG path
  marker: { x: number; y: number }; // centre-top of the warning triangle
}

/**
 * Orthogonal route: tablet's left edge → channel in the gap left of its
 * node → up to the lane → across to the target node → down onto the
 * target's top edge, where the warning triangle sits. Arrows that leave the
 * same node use separate channels; arrows into the same node land at
 * separate x positions. Corners are rounded with a fixed radius.
 */
export function route(
  edges: { id: string; from: number; to: number; tablet: Box }[],
  nodes: Box[],
  lane: Record<string, number>,
  rowTop: number,
): Routed[] {
  const leaving: Record<number, string[]> = {};
  const arriving: Record<number, string[]> = {};
  for (const e of edges) {
    (leaving[e.from] ??= []).push(e.id);
    (arriving[e.to] ??= []).push(e.id);
  }
  const TRI = 16;
  return edges.map((e) => {
    const src = nodes[e.from];
    const dst = nodes[e.to];
    const out = leaving[e.from].indexOf(e.id);
    const inn = arriving[e.to].indexOf(e.id);
    const nIn = arriving[e.to].length;
    const sx = e.tablet.left;
    const sy = e.tablet.top + e.tablet.height / 2;
    const cx = snap(src.left - 12 - out * 6, 2);
    const ly = rowTop - LANE * (lane[e.id] + 1);
    const tx = snap(dst.left + dst.width / 2 + (inn - (nIn - 1) / 2) * 20, 2);
    const ty = dst.top - TRI;
    return { id: e.id, d: rounded([[sx, sy], [cx, sy], [cx, ly], [tx, ly], [tx, ty]], 6), marker: { x: tx, y: ty } };
  });
}

function rounded(pts: [number, number][], r: number): string {
  let d = `M${pts[0][0]} ${pts[0][1]}`;
  for (let i = 1; i < pts.length - 1; i++) {
    const [x0, y0] = pts[i - 1];
    const [x1, y1] = pts[i];
    const [x2, y2] = pts[i + 1];
    const a = Math.min(r, Math.hypot(x1 - x0, y1 - y0) / 2, Math.hypot(x2 - x1, y2 - y1) / 2);
    const u = [(x0 - x1) / (Math.hypot(x0 - x1, y0 - y1) || 1), (y0 - y1) / (Math.hypot(x0 - x1, y0 - y1) || 1)];
    const v = [(x2 - x1) / (Math.hypot(x2 - x1, y2 - y1) || 1), (y2 - y1) / (Math.hypot(x2 - x1, y2 - y1) || 1)];
    d += ` L${x1 + u[0] * a} ${y1 + u[1] * a} Q${x1} ${y1} ${x1 + v[0] * a} ${y1 + v[1] * a}`;
  }
  const last = pts[pts.length - 1];
  return `${d} L${last[0]} ${last[1]}`;
}
