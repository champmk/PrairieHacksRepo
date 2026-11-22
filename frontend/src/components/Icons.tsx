type P = { size?: number; className?: string };

const base = (size = 16) => ({
  width: size,
  height: size,
  viewBox: '0 0 16 16',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.6,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
  'aria-hidden': true,
});

export const Check = ({ size, className }: P) => (
  <svg {...base(size)} className={className}><path d="M3.5 8.5l3 3 6-7" /></svg>
);
export const Plus = ({ size, className }: P) => (
  <svg {...base(size)} className={className}><path d="M8 3v10M3 8h10" /></svg>
);
export const Close = ({ size, className }: P) => (
  <svg {...base(size)} className={className}><path d="M4 4l8 8M12 4l-8 8" /></svg>
);
export const ChevronDown = ({ size, className }: P) => (
  <svg {...base(size)} className={className}><path d="M4 6l4 4 4-4" /></svg>
);
export const ChevronLeft = ({ size, className }: P) => (
  <svg {...base(size)} className={className}><path d="M10 3.5L5.5 8l4.5 4.5" /></svg>
);
export const ChevronRight = ({ size, className }: P) => (
  <svg {...base(size)} className={className}><path d="M6 3.5L10.5 8 6 12.5" /></svg>
);
export const Search = ({ size, className }: P) => (
  <svg {...base(size)} className={className}><circle cx="7" cy="7" r="4.25" /><path d="M10.5 10.5L13.5 13.5" /></svg>
);
export const Panel = ({ size, className }: P) => (
  <svg {...base(size)} className={className}><rect x="2" y="3" width="12" height="10" rx="2" /><path d="M6 3v10" /></svg>
);
export const PanelRight = ({ size, className }: P) => (
  <svg {...base(size)} className={className}><rect x="2" y="3" width="12" height="10" rx="2" /><path d="M10 3v10" /></svg>
);
export const Expand = ({ size, className }: P) => (
  <svg {...base(size)} className={className}><path d="M9.5 2.5h4v4M6.5 13.5h-4v-4M13.5 2.5L9 7M2.5 13.5L7 9" /></svg>
);
export const Collapse = ({ size, className }: P) => (
  <svg {...base(size)} className={className}><path d="M13 7H9V3M3 9h4v4M9 7l4.5-4.5M7 9l-4.5 4.5" /></svg>
);
export const Undo = ({ size, className }: P) => (
  <svg {...base(size)} className={className}><path d="M5.5 4L2.5 7l3 3" /><path d="M2.5 7H10a3.5 3.5 0 010 7H8" /></svg>
);
export const More = ({ size, className }: P) => (
  <svg {...base(size)} className={className}><circle cx="3.5" cy="8" r=".6" /><circle cx="8" cy="8" r=".6" /><circle cx="12.5" cy="8" r=".6" /></svg>
);

export const Pencil = ({ size, className }: P) => (
  <svg {...base(size)} className={className}><path d="M10.5 3l2.5 2.5L6 12.5H3.5V10z" /><path d="M9 4.5l2.5 2.5" /></svg>
);
export const Swap = ({ size, className }: P) => (
  <svg {...base(size)} className={className}><path d="M4 5.5h8l-2.5-2.5M12 10.5H4l2.5 2.5" /></svg>
);
export const Filter = ({ size, className }: P) => (
  <svg {...base(size)} className={className}><path d="M2.5 4h11M4.5 8h7M6.5 12h3" /></svg>
);

/** Red circle with a dash: delete this tablet. */
export const Remove = ({ size = 18 }: P) => (
  <svg width={size} height={size} viewBox="0 0 18 18" aria-hidden="true">
    <circle cx="9" cy="9" r="8" fill="var(--danger)" />
    <path d="M5.5 9h7" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" />
  </svg>
);

/** Warning triangle with "!". */
export const Warn = ({ size = 16, tone = 'warn' }: P & { tone?: 'warn' | 'error' }) => (
  <svg width={size} height={size} viewBox="0 0 16 16" aria-hidden="true">
    <path d="M8 1.6L15 14H1z" fill={tone === 'error' ? 'var(--danger)' : 'var(--warn)'} />
    <path d="M8 6v3.6" stroke="#fff" strokeWidth="1.6" strokeLinecap="round" />
    <circle cx="8" cy="11.8" r=".95" fill="#fff" />
  </svg>
);

export const CheckDot = ({ size = 16 }: P) => (
  <svg width={size} height={size} viewBox="0 0 16 16" aria-hidden="true">
    <circle cx="8" cy="8" r="8" fill="var(--done)" />
    <path d="M4.8 8.3l2.1 2.1 4.3-4.6" stroke="#fff" strokeWidth="1.6" fill="none" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const Mark = () => (
  <svg className="wordmark-mark" viewBox="0 0 18 18" aria-hidden="true">
    <circle cx="4" cy="4" r="2.5" fill="#111317" />
    <circle cx="14" cy="9" r="2.5" fill="#111317" />
    <circle cx="4" cy="14" r="2.5" fill="#111317" />
    <path d="M6 5l6 3M6 13l6-3" stroke="#111317" strokeWidth="1.4" strokeLinecap="round" />
  </svg>
);

