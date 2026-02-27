"use client";

import { FormField, SelectField, RangeInput } from "@/components/ui";
import { onboarding } from "@/data";
import type { OnboardingData } from "@/lib/validations/onboarding";

type PreferencesStepProps = {
  data: OnboardingData;
  onChange: (field: keyof OnboardingData, value: unknown) => void;
  errors: Record<string, string>;
};

export function PreferencesStep({ data, onChange, errors }: PreferencesStepProps) {
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
          {onboarding.steps.preferences.heading}
        </h2>
        <p style={{ color: "var(--color-text-secondary)", fontSize: 14, marginTop: 4 }}>
          {onboarding.steps.preferences.subtitle}
        </p>
      </div>

      <div style={{ display: "flex", gap: 16 }}>
        <div style={{ flex: 1 }}>
          <SelectField
            id="bedrooms"
            label={onboarding.labels.bedrooms}
            value={String(data.bedrooms)}
            onChange={(v) => onChange("bedrooms", Number(v))}
            options={Array.from({ length: 7 }, (_, i) => ({
              value: String(i),
              label: i === 0 ? "Studio" : String(i),
            }))}
            error={errors.bedrooms}
          />
        </div>
        <div style={{ flex: 1 }}>
          <SelectField
            id="bathrooms"
            label={onboarding.labels.bathrooms}
            value={String(data.bathrooms)}
            onChange={(v) => onChange("bathrooms", Number(v))}
            options={Array.from({ length: 6 }, (_, i) => ({
              value: String(i + 1),
              label: String(i + 1),
            }))}
            error={errors.bathrooms}
          />
        </div>
      </div>

      <RangeInput
        label={onboarding.labels.priceRange}
        minValue={data.price_min}
        maxValue={data.price_max}
        onMinChange={(v) => onChange("price_min", v)}
        onMaxChange={(v) => onChange("price_max", v)}
        minPlaceholder={onboarding.placeholders.priceMin}
        maxPlaceholder={onboarding.placeholders.priceMax}
        minLabel="$"
        maxLabel="$"
        error={errors.price_max}
      />

      <SelectField
        id="distance"
        label={onboarding.labels.distance}
        value={data.distance_from_campus}
        onChange={(v) => onChange("distance_from_campus", v)}
        options={[...onboarding.distanceOptions]}
        error={errors.distance_from_campus}
      />

      <FormField
        id="roommates"
        name="roommates"
        type="number"
        label={onboarding.labels.roommates}
        placeholder={onboarding.placeholders.roommates}
        value={String(data.roommates)}
        onChange={(e) => onChange("roommates", Number(e.target.value))}
        error={errors.roommates}
      />
    </div>
  );
}
