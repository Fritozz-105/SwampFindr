"use client";

import { CheckboxGroup, TextArea } from "@/components/ui";
import { onboarding } from "@/data";
import type { OnboardingData } from "@/lib/validations/onboarding";

type AmenitiesStepProps = {
  data: OnboardingData;
  onChange: (field: keyof OnboardingData, value: unknown) => void;
  errors: Record<string, string>;
};

export function AmenitiesStep({ data, onChange, errors }: AmenitiesStepProps) {
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
          {onboarding.steps.amenities.heading}
        </h2>
        <p style={{ color: "var(--color-text-secondary)", fontSize: 14, marginTop: 4 }}>
          {onboarding.steps.amenities.subtitle}
        </p>
      </div>

      <CheckboxGroup
        label={onboarding.labels.amenities}
        options={[...onboarding.amenitiesList]}
        selected={data.amenities}
        onChange={(selected) => onChange("amenities", selected)}
      />
      {errors.amenities && (
        <p style={{ color: "var(--color-error)", fontSize: 13 }}>{errors.amenities}</p>
      )}

      <TextArea
        id="excerpt"
        label={onboarding.labels.excerpt}
        value={data.excerpt}
        onChange={(v) => onChange("excerpt", v)}
        placeholder={onboarding.placeholders.excerpt}
        maxLength={onboarding.excerptMaxLength}
        error={errors.excerpt}
      />
    </div>
  );
}
