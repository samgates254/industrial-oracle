import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/cn";

export function Breadcrumbs({
  items,
  className,
}: {
  items: { href?: string; label: string }[];
  className?: string;
}) {
  return (
    <nav aria-label="Breadcrumb" className={cn("flex items-center gap-1", className)}>
      <ol className="flex items-center gap-1">
        {items.map((item, index) => (
          <li key={`${item.label}-${index}`} className="flex items-center gap-1">
            {index > 0 ? (
              <ChevronRight className="h-3 w-3 text-muted" aria-hidden />
            ) : null}
            {item.href && index < items.length - 1 ? (
              <Link href={item.href} className="type-meta text-secondary hover:text-primary">
                {item.label}
              </Link>
            ) : (
              <span className="type-meta text-primary" aria-current="page">
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
