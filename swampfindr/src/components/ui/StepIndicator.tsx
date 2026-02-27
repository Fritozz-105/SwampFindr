"use client";

type Step = {
  title: string;
};

type StepIndicatorProps = {
  steps: Step[];
  currentStep: number;
};

export function StepIndicator({ steps, currentStep }: StepIndicatorProps) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 0 }}>
      {steps.map((step, i) => {
        const isCompleted = i < currentStep;
        const isCurrent = i === currentStep;

        return (
          <div key={step.title} style={{ display: "flex", alignItems: "center" }}>
            {/* Circle */}
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
              <div
                className={`step-circle ${isCompleted || isCurrent ? "active" : ""}`}
              >
                {isCompleted ? (
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <path d="M2.5 7L5.5 10L11.5 4" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                ) : (
                  <span style={{ fontSize: 13, fontWeight: 600 }}>{i + 1}</span>
                )}
              </div>
              <span
                style={{
                  fontSize: 12,
                  fontWeight: isCurrent ? 600 : 400,
                  color: isCompleted || isCurrent ? "var(--color-primary)" : "var(--color-text-muted)",
                }}
              >
                {step.title}
              </span>
            </div>

            {/* Connecting line */}
            {i < steps.length - 1 && (
              <div
                className={`step-line ${isCompleted ? "completed" : ""}`}
                style={{ marginBottom: 22 }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
