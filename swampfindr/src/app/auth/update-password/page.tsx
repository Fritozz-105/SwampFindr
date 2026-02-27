"use client";

import { useActionState } from "react";
import Link from "next/link";
import { updatePassword, type AuthResult } from "../actions";
import { auth } from "@/data/auth";
import { Alert, FormField, PasswordInput, SubmitButton } from "@/components/ui";

export default function UpdatePasswordPage() {
  const [state, formAction, isPending] = useActionState<AuthResult, FormData>(
    async (_prev, formData) => updatePassword(formData),
    {},
  );

  return (
    <div className="stagger">
      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: 32 }}>
        <h1
          style={{
            fontFamily: "var(--font-display)",
            fontSize: 28,
            fontWeight: 700,
            color: "var(--color-text)",
            letterSpacing: "-0.02em",
            marginBottom: 8,
          }}
        >
          {auth.updatePassword.heading}
        </h1>
        <p style={{ color: "var(--color-text-secondary)", fontSize: 15 }}>
          {auth.updatePassword.subtitle}
        </p>
      </div>

      <form action={formAction}>
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <PasswordInput
            id="password"
            name="password"
            label={auth.labels.newPassword}
            placeholder={auth.placeholders.newPassword}
            required
            aria-describedby={state.error ? "update-error" : undefined}
          />

          <FormField
            id="confirmPassword"
            name="confirmPassword"
            type="password"
            label={auth.labels.confirmNewPassword}
            placeholder={auth.placeholders.confirmNewPassword}
            required
          />

          {state.error && (
            <Alert variant="error" id="update-error">
              {state.error}
            </Alert>
          )}

          <SubmitButton isPending={isPending}>{auth.updatePassword.submitLabel}</SubmitButton>
        </div>
      </form>

      <p
        style={{
          textAlign: "center",
          fontSize: 14,
          color: "var(--color-text-secondary)",
          marginTop: 24,
        }}
      >
        <Link
          href="/auth/login"
          style={{
            color: "var(--color-primary)",
            fontWeight: 500,
            textDecoration: "none",
          }}
        >
          {auth.updatePassword.backLink}
        </Link>
      </p>
    </div>
  );
}
