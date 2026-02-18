"use client";

import { useActionState } from "react";
import Link from "next/link";
import { resetPassword, type AuthResult } from "../actions";
import { auth } from "@/data/auth";
import { CheckIcon } from "@/components/ui/icons";
import { Alert, FormField, SubmitButton } from "@/components/ui";

export default function ResetPasswordPage() {
  const [state, formAction, isPending] = useActionState<AuthResult, FormData>(
    async (_prev, formData) => resetPassword(formData),
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
            marginBottom: 8,
          }}
        >
          {auth.resetPassword.heading}
        </h1>
        <p style={{ color: "var(--color-text-secondary)", fontSize: 15 }}>
          {auth.resetPassword.subtitle}
        </p>
      </div>

      {state.success ? (
        /* Success state */
        <div style={{ textAlign: "center" }}>
          <div
            style={{
              width: 64,
              height: 64,
              borderRadius: "50%",
              background: "rgba(34, 197, 94, 0.1)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 20px",
            }}
          >
            <CheckIcon />
          </div>
          <h2
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 20,
              fontWeight: 600,
              marginBottom: 8,
            }}
          >
            {auth.resetPassword.successHeading}
          </h2>
          <p
            style={{
              color: "var(--color-text-secondary)",
              fontSize: 14,
              marginBottom: 24,
              lineHeight: 1.6,
            }}
          >
            {auth.resetPassword.successMessage}
          </p>
          <Link
            href="/auth/login"
            style={{
              color: "var(--color-primary)",
              fontWeight: 600,
              fontSize: 14,
              textDecoration: "none",
            }}
          >
            {auth.resetPassword.backLink}
          </Link>
        </div>
      ) : (
        /* Form state */
        <>
          <form action={formAction}>
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <FormField
                id="email"
                name="email"
                type="email"
                label={auth.labels.email}
                placeholder={auth.placeholders.email}
                required
              />

              {state.error && (
                <Alert variant="error">{state.error}</Alert>
              )}

              <SubmitButton isPending={isPending}>
                {auth.resetPassword.submitLabel}
              </SubmitButton>
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
            {auth.resetPassword.rememberPrompt}{" "}
            <Link
              href="/auth/login"
              style={{
                color: "var(--color-primary)",
                fontWeight: 600,
                textDecoration: "none",
              }}
            >
              {auth.login.heading}
            </Link>
          </p>
        </>
      )}
    </div>
  );
}
