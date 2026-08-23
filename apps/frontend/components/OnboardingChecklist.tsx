import { OnboardingStatus } from "../lib/api";
import { brand, card, mutedText } from "../lib/styles";

export default function OnboardingChecklist({ status }: { status: OnboardingStatus }) {
  if (status.all_done) return null;

  return (
    <div style={card}>
      <strong>Getting started</strong>
      <div style={{ marginTop: 12 }}>
        {status.steps.map((step) => (
          <div key={step.key} style={{ display: "flex", alignItems: "center", gap: 10, padding: "6px 0" }}>
            <span
              style={{
                width: 18,
                height: 18,
                borderRadius: 999,
                flexShrink: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 11,
                color: "#fff",
                background: step.done ? brand.emerald : brand.borderTint,
              }}
            >
              {step.done ? "✓" : ""}
            </span>
            <span style={{ flex: 1, textDecoration: step.done ? "line-through" : "none", color: step.done ? brand.mutedGreen : brand.deepForest }}>
              {step.label}
            </span>
            {!step.done && step.target > 1 && (
              <span style={mutedText}>
                {step.progress}/{step.target}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
