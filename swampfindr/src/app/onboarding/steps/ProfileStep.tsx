"use client";

import { FormField } from "@/components/ui";
import { onboarding } from "@/data";
import type { OnboardingData } from "@/lib/validations/onboarding";

function formatPhone(digits: string): string {
  if (digits.length === 0) return "";
  if (digits.length <= 3) return `(${digits}`;
  if (digits.length <= 6) return `(${digits.slice(0, 3)}) ${digits.slice(3)}`;
  return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
}

type ProfileStepProps = {
  data: OnboardingData;
  onChange: (field: keyof OnboardingData, value: string) => void;
  errors: Record<string, string>;
};

export function ProfileStep({ data, onChange, errors }: ProfileStepProps) {
  return (
    <div className="stagger" style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <div>
        <h2
          style={{
            fontFamily: "var(--font-display)",
            fontSize: 22,
            fontWeight: 700,
            color: "var(--color-text)",
            letterSpacing: "-0.015em",
          }}
        >
          {onboarding.steps.profile.heading}
        </h2>
        <p style={{ color: "var(--color-text-secondary)", fontSize: 14, marginTop: 4 }}>
          {onboarding.steps.profile.subtitle}
        </p>
      </div>

      <FormField
        id="username"
        name="username"
        label={onboarding.labels.username}
        placeholder={onboarding.placeholders.username}
        value={data.username}
        onChange={(e) => onChange("username", e.target.value)}
        error={errors.username}
      />

      <FormField
        id="phone"
        name="phone"
        type="tel"
        label={onboarding.labels.phone}
        placeholder={onboarding.placeholders.phone}
        value={formatPhone(data.phone)}
        onChange={(e) => {
          const digits = e.target.value.replace(/\D/g, "").slice(0, 10);
          onChange("phone", digits);
        }}
        error={errors.phone}
      />
    </div>
  );
}
