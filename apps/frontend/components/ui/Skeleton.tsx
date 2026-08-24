import { HTMLAttributes } from "react";
import { cn } from "../../lib/cn";

export function Skeleton({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("animate-pulse rounded-lg bg-line/70", className)} {...props} />;
}

export function CardSkeleton() {
  return (
    <div className="rounded-2xl border border-line bg-card p-5">
      <Skeleton className="mb-3 h-4 w-1/3" />
      <Skeleton className="mb-2 h-3 w-full" />
      <Skeleton className="h-3 w-2/3" />
    </div>
  );
}
