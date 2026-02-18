"use client";

import { useActionState, useState } from "react";
import Link from "next/link";
import { signup, signInWithOAuth, type AuthResult } from "../actions";
import { passwordSchema } from "@/lib/validations/auth";
import { auth } from "@/data/auth";
import {
  Alert,
  FormField,
  PasswordInput,
  PasswordStrength,
  SubmitButton,
  FormDivider,
  GoogleOAuthButton,
} from "@/components/ui";

export default function SignupPage() {
  const [state, formAction, isPending] = useActionState<AuthResult, FormData>(
    async (_prev, formData) => signup(formData),
    {},
  );

  const [password, setPassword] = useState("");
  const [passwordErrors, setPasswordErrors] = useState<string[]>([]);

  function validatePassword(value: string) {
    const result = passwordSchema.safeParse(value);
    if (!result.success) {
      setPasswordErrors(result.error.issues.map((e) => e.message));
    } else {
      setPasswordErrors([]);
    }
  }

  return (
    <div className="stagger">
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1
          style={{
            fontFamily: "var(--font-display)",
            fontSize: 26,
            fontWeight: 700,
            color: "var(--color-text)",
            marginBottom: 6,
          }}
        >
          {auth.signup.heading}
        </h1>
        <p style={{ color: "var(--color-text-secondary)", fontSize: 14 }}>
          {auth.signup.subtitle}{" "}
          <Link
            href="/auth/login"
            style={{
              color: "var(--color-primary)",
              fontWeight: 600,
              textDecoration: "none",
            }}
          >
            {auth.signup.subtitleLink}
          </Link>
        </p>
      </div>

      <GoogleOAuthButton onClick={() => signInWithOAuth("google")}>
        {auth.oauthGoogle}
      </GoogleOAuthButton>

      <FormDivider text={auth.dividerText} />

      {/* Signup form */}
      <form action={formAction}>
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <FormField
            id="fullName"
            name="fullName"
            label={auth.labels.fullName}
            placeholder={auth.placeholders.fullName}
            required
          />

          <FormField
            id="email"
            name="email"
            type="email"
            label={auth.labels.email}
            placeholder={auth.placeholders.email}
            required
          />

          <div>
            <PasswordInput
              id="password"
              name="password"
              label={auth.labels.password}
              placeholder={auth.placeholders.createPassword}
              required
              aria-describedby="password-strength password-errors"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onBlur={(e) => validatePassword(e.target.value)}
            />

            <PasswordStrength password={password} />

            {passwordErrors.length > 0 && (
              <ul
                id="password-errors"
                role="alert"
                style={{
                  marginTop: 6,
                  paddingLeft: 16,
                  fontSize: 13,
                  color: "var(--color-accent)",
                  listStyle: "disc",
                }}
              >
                {passwordErrors.map((err) => (
                  <li key={err}>{err}</li>
                ))}
              </ul>
            )}
          </div>

          <FormField
            id="confirmPassword"
            name="confirmPassword"
            type="password"
            label={auth.labels.confirmPassword}
            placeholder={auth.placeholders.confirmPassword}
            required
          />

          {state.error && (
            <Alert variant="error">{state.error}</Alert>
          )}

          <SubmitButton isPending={isPending}>
            {auth.signup.submitLabel}
          </SubmitButton>
        </div>
      </form>
    </div>
  );
}
