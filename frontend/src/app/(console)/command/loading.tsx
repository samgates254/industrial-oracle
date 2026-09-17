import { Skeleton } from "@/components/ui/feedback";

export default function CommandLoading() {
  return (
    <div className="io-page flex flex-col gap-5" aria-busy="true" aria-label="Loading command center">
      <Skeleton className="h-6 w-48" />
      <Skeleton className="h-8 w-full" />
      <Skeleton className="h-28 w-full" />
      <Skeleton className="h-48 w-full" />
    </div>
  );
}
