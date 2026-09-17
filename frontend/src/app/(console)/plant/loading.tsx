import { Skeleton } from "@/components/ui/feedback";

export default function PlantLoading() {
  return (
    <div className="io-page io-grid" aria-busy="true" aria-label="Loading plant topology">
      <Skeleton className="h-8 w-56" />
      <Skeleton className="h-16" />
      <Skeleton className="h-12" />
      <Skeleton className="h-[28rem]" />
    </div>
  );
}
