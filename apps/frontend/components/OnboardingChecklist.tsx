import { OnboardingStatus } from "../lib/api";
import { Card } from "./ui/Card";
import { cn } from "../lib/cn";

export default function OnboardingChecklist({ status }: { status: OnboardingStatus }) {
  if (status.all_done) return null;

  return (
    <Card>
      <div className="text-sm font-semibold text-ink">Getting started</div>
      <div className="mt-3 space-y-1">
        {status.steps.map((step) => (
          <div key={step.key} className="flex items-center gap-2.5 py-1.5">
            <span
              className={cn(
                "flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded-full text-[11px] text-white",
                step.done ? "bg-brand-emerald" : "bg-line"
              )}
            >
              {step.done ? "✓" : ""}
            </span>
            <span className={cn("flex-1 text-sm", step.done ? "text-muted line-through" : "text-ink")}>{step.label}</span>
            {!step.done && step.target > 1 && (
              <span className="text-xs text-muted">
                {step.progress}/{step.target}
              </span>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}
