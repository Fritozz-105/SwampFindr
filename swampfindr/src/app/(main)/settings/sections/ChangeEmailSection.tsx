"use client";

import { useState } from "react";
import { changeEmail } from "../actions";
import { settings } from "@/data/settings";
import { FormField, Alert } from "@/components/ui";

type ChangeEmailSectionProps = {
  currentEmail: string;
};

export function ChangeEmailSection({ currentEmail }: ChangeEmailSectionProps) {
  const [email, setEmail] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function handleSubmit() {
    setSaving(true);
    setError("");
    setSuccess("");

    const formData = new FormData();
    formData.set("email", email);

    const result = await changeEmail(formData);

    if (result.error) {
      setError(result.error);
    } else {
      setSuccess(settings.messages.emailUpdated);
      setEmail("");
    }
    setSaving(false);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div>
        <label
          style={{
            display: "block",
            fontSize: 14,
            fontWeight: 500,
            color: "var(--color-text)",
            marginBottom: 6,
          }}
        >
          {settings.sections.email.currentLabel}
        </label>
        <p style={{ fontSize: 15, color: "var(--color-text-secondary)" }}>{currentEmail}</p>
      </div>

      <FormField
        id="settings-new-email"
        name="email"
        type="email"
        label={settings.sections.email.newLabel}
        placeholder="new@example.com"
        value={email}
        onChange={(e) => {
          setEmail(e.target.value);
          setSuccess("");
        }}
      />

      {error && <Alert variant="error">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}

      <button
        type="button"
        className="btn-primary"
        disabled={saving || !email}
        onClick={handleSubmit}
        style={{ alignSelf: "flex-start", width: "auto", padding: "10px 24px" }}
      >
        {saving ? settings.sections.email.saving : settings.sections.email.saveButton}
      </button>
    </div>
  );
}
