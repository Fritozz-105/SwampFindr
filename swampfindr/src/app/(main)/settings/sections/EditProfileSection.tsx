"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { profileUpdateSchema } from "@/lib/validations/settings";
import { settings } from "@/data/settings";
import { errors } from "@/data/errors";
import { FormField, Alert } from "@/components/ui";

const API_URL = process.env.NEXT_PUBLIC_FLASK_API_URL ?? "http://localhost:8080";

type EditProfileSectionProps = {
  username: string;
  phone: string;
  onUpdate: () => void;
};

export function EditProfileSection({ username, phone, onUpdate }: EditProfileSectionProps) {
  const [form, setForm] = useState({ username, phone });
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  function handleChange(field: string, value: string) {
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
    const parsed = profileUpdateSchema.safeParse(form);
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

      const res = await fetch(`${API_URL}/api/v1/profiles/me`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session?.access_token}`,
        },
        body: JSON.stringify(parsed.data),
      });

      if (!res.ok) {
        setError(errors.settings.profileUpdateFailed);
        setSaving(false);
        return;
      }

      setSuccess(settings.messages.profileUpdated);
      onUpdate();
    } catch {
      setError(errors.settings.networkError);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <FormField
        id="settings-username"
        name="username"
        label="Username"
        placeholder="gator_albert"
        value={form.username}
        onChange={(e) => handleChange("username", e.target.value)}
        error={fieldErrors.username}
      />
      <FormField
        id="settings-phone"
        name="phone"
        label="Phone number"
        placeholder="(352) 555-1234"
        value={form.phone}
        onChange={(e) => handleChange("phone", e.target.value)}
        error={fieldErrors.phone}
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
        {saving ? settings.sections.profile.saving : settings.sections.profile.saveButton}
      </button>
    </div>
  );
}
