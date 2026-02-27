"use client";

import { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { preferencesUpdateSchema } from "@/lib/validations/settings";
import { settings } from "@/data/settings";
import { errors } from "@/data/errors";
import { onboarding } from "@/data/onboarding";
import {
  FormField,
  SelectField,
  RangeInput,
  CheckboxGroup,
  TextArea,
  Alert,
} from "@/components/ui";
import type { UserPreferences } from "@/types/profile";

const API_URL = process.env.NEXT_PUBLIC_FLASK_API_URL ?? "http://localhost:5000";

type EditPreferencesSectionProps = {
  preferences: UserPreferences | null;
  onUpdate: () => void;
};

const defaults: UserPreferences = {
  bedrooms: 1,
  bathrooms: 1,
  price_min: 500,
  price_max: 2000,
  distance_from_campus: "any",
  roommates: 0,
  amenities: [],
  excerpt: "",
};

export function EditPreferencesSection({ preferences, onUpdate }: EditPreferencesSectionProps) {
  const [form, setForm] = useState<UserPreferences>(preferences ?? defaults);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    if (preferences) {
      setForm(preferences);
    }
  }, [preferences]);

  function handleChange(field: keyof UserPreferences, value: unknown) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setFieldErrors((prev) => {
      if (!prev[field]) return prev;
      const next = { ...prev };
      delete next[field];
      return next;
    });
    setSuccess("");
  }

  async function handleSave() {
    const parsed = preferencesUpdateSchema.safeParse(form);
    if (!parsed.success) {
      const errs: Record<string, string> = {};
      for (const issue of parsed.error.issues) {
        const key = issue.path[0]?.toString();
        if (key && !errs[key]) errs[key] = issue.message;
      }
      setFieldErrors(errs);
      return;
    }

    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session?.access_token) {
        setError("Session expired. Please log in again.");
        setSaving(false);
        return;
      }

      const res = await fetch(`${API_URL}/api/v1/profiles/me/preferences`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session?.access_token}`,
        },
        body: JSON.stringify(parsed.data),
      });

      if (!res.ok) {
        setError(errors.settings.preferencesUpdateFailed);
        setSaving(false);
        return;
      }

      setSuccess(settings.messages.preferencesUpdated);
      onUpdate();
    } catch {
      setError(errors.settings.networkError);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "flex", gap: 16 }}>
        <div style={{ flex: 1 }}>
          <SelectField
            id="settings-bedrooms"
            label={onboarding.labels.bedrooms}
            value={String(form.bedrooms)}
            onChange={(v) => handleChange("bedrooms", Number(v))}
            options={Array.from({ length: 7 }, (_, i) => ({
              value: String(i),
              label: i === 0 ? "Studio" : String(i),
            }))}
            error={fieldErrors.bedrooms}
          />
        </div>
        <div style={{ flex: 1 }}>
          <SelectField
            id="settings-bathrooms"
            label={onboarding.labels.bathrooms}
            value={String(form.bathrooms)}
            onChange={(v) => handleChange("bathrooms", Number(v))}
            options={Array.from({ length: 6 }, (_, i) => ({
              value: String(i + 1),
              label: String(i + 1),
            }))}
            error={fieldErrors.bathrooms}
          />
        </div>
      </div>

      <RangeInput
        label={onboarding.labels.priceRange}
        minValue={form.price_min}
        maxValue={form.price_max}
        onMinChange={(v) => handleChange("price_min", v)}
        onMaxChange={(v) => handleChange("price_max", v)}
        minPlaceholder={onboarding.placeholders.priceMin}
        maxPlaceholder={onboarding.placeholders.priceMax}
        minLabel="$"
        maxLabel="$"
        error={fieldErrors.price_max}
      />

      <SelectField
        id="settings-distance"
        label={onboarding.labels.distance}
        value={form.distance_from_campus}
        onChange={(v) => handleChange("distance_from_campus", v)}
        options={[...onboarding.distanceOptions]}
        error={fieldErrors.distance_from_campus}
      />

      <FormField
        id="settings-roommates"
        name="roommates"
        type="number"
        label={onboarding.labels.roommates}
        placeholder={onboarding.placeholders.roommates}
        value={String(form.roommates)}
        onChange={(e) => handleChange("roommates", Number(e.target.value))}
        error={fieldErrors.roommates}
      />

      <CheckboxGroup
        label={onboarding.labels.amenities}
        options={[...onboarding.amenitiesList]}
        selected={form.amenities}
        onChange={(v) => handleChange("amenities", v)}
      />

      <TextArea
        id="settings-excerpt"
        label={onboarding.labels.excerpt}
        placeholder={onboarding.placeholders.excerpt}
        value={form.excerpt}
        onChange={(v) => handleChange("excerpt", v)}
        maxLength={onboarding.excerptMaxLength}
        error={fieldErrors.excerpt}
      />

      {error && <Alert variant="error">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}

      <button
        type="button"
        className="btn-primary"
        disabled={saving}
        onClick={handleSave}
        style={{ alignSelf: "flex-start", width: "auto", padding: "10px 24px" }}
      >
        {saving ? settings.sections.preferences.saving : settings.sections.preferences.saveButton}
      </button>
    </div>
  );
}
