"use client";

import { useState } from "react";
import { changePassword } from "../actions";
import { settings } from "@/data/settings";
import { PasswordInput, PasswordStrength, Alert } from "@/components/ui";

type ChangePasswordSectionProps = {
  provider: string;
};

export function ChangePasswordSection({ provider }: ChangePasswordSectionProps) {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  if (provider !== "email") {
    return (
      <p style={{ color: "var(--color-text-muted)", fontSize: 14 }}>
        {settings.sections.password.oauthMessage}
      </p>
    );
  }

  async function handleSubmit() {
    setSaving(true);
    setError("");
    setSuccess("");

    const formData = new FormData();
    formData.set("password", password);
    formData.set("confirmPassword", confirmPassword);

    const result = await changePassword(formData);

    if (result.error) {
      setError(result.error);
    } else {
      setSuccess(settings.messages.passwordUpdated);
      setPassword("");
      setConfirmPassword("");
    }
    setSaving(false);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div>
        <PasswordInput
          id="settings-password"
          name="password"
          label="New password"
          placeholder="Enter new password"
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
            setSuccess("");
          }}
        />
        <PasswordStrength password={password} />
      </div>

      <PasswordInput
        id="settings-confirm-password"
        name="confirmPassword"
        label="Confirm new password"
        placeholder="Confirm new password"
        value={confirmPassword}
        onChange={(e) => {
          setConfirmPassword(e.target.value);
          setSuccess("");
        }}
      />

      {error && <Alert variant="error">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}

      <button
        type="button"
        className="btn-primary"
        disabled={saving || !password || !confirmPassword}
        onClick={handleSubmit}
        style={{ alignSelf: "flex-start", width: "auto", padding: "10px 24px" }}
      >
        {saving ? settings.sections.password.saving : settings.sections.password.saveButton}
      </button>
    </div>
  );
}
