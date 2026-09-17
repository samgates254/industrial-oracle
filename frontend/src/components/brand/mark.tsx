export function OracleMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={className}
      aria-hidden
      fill="none"
    >
      <rect x="2.5" y="2.5" width="19" height="19" stroke="currentColor" strokeWidth="1.25" />
      <circle cx="12" cy="12" r="4.25" stroke="currentColor" strokeWidth="1.25" />
      <path d="M12 3.5v3.25M12 17.25V20.5M3.5 12h3.25M17.25 12H20.5" stroke="currentColor" strokeWidth="1.25" />
    </svg>
  );
}

export function Wordmark({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-2 text-brand">
      <OracleMark className="h-6 w-6" />
      {compact ? (
        <span className="type-ident text-primary">IO</span>
      ) : (
        <span className="leading-tight">
          <span className="block font-sans text-[11px] font-semibold uppercase tracking-[0.18em] text-primary">
            Industrial
          </span>
          <span className="block font-sans text-[11px] font-medium uppercase tracking-[0.22em] text-brand">
            Oracle
          </span>
        </span>
      )}
    </div>
  );
}
