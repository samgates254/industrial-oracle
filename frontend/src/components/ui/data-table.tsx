import { cn } from "@/lib/cn";

export function DataTable({
  columns,
  rows,
  caption,
  dense = true,
}: {
  columns: { key: string; header: string; numeric?: boolean }[];
  rows: Record<string, string>[];
  caption: string;
  dense?: boolean;
}) {
  return (
    <div className="overflow-x-auto rounded-panel border border-default">
      <table className="w-full text-table">
        <caption className="sr-only">{caption}</caption>
        <thead className="bg-elevated text-muted">
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                scope="col"
                className={cn(
                  "border-b border-subtle px-2 text-left type-panel font-medium",
                  dense ? "h-row" : "h-10",
                  col.numeric && "text-right",
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={row.id ?? String(i)} className="border-b border-subtle last:border-0">
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={cn(
                    "px-2 text-primary",
                    dense ? "h-row" : "h-10",
                    col.numeric && "text-right font-mono tabular",
                  )}
                >
                  {row[col.key] ?? "—"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
