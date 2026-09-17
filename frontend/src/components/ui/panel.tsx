import { cn } from "@/lib/cn";

export function Panel({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLElement>) {
  return (
    <section
      className={cn(
        "rounded-panel border border-default bg-panel p-panel-pad",
        className,
      )}
      {...props}
    >
      {children}
    </section>
  );
}

export function SectionHeader({
  eyebrow,
  title,
  actions,
  className,
}: {
  eyebrow?: string;
  title: string;
  actions?: React.ReactNode;
  className?: string;
}) {
  return (
    <header className={cn("mb-3 flex items-start justify-between gap-3", className)}>
      <div>
        {eyebrow ? <p className="type-panel mb-1">{eyebrow}</p> : null}
        <h2 className="type-section">{title}</h2>
      </div>
      {actions ? <div className="flex items-center gap-1.5">{actions}</div> : null}
    </header>
  );
}

export function ActionBar({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-2 border-t border-subtle pt-3",
        className,
      )}
    >
      {children}
    </div>
  );
}
