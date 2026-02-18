"use client";

import { useActionState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { login, signInWithOAuth, type AuthResult } from "../actions";
import { auth } from "@/data/auth";
import {
  Alert,
  FormField,
  PasswordInput,
  SubmitButton,
  FormDivider,
  GoogleOAuthButton,
} from "@/components/ui";

function LoginForm() {
  const searchParams = useSearchParams();
  const message = searchParams.get("message");
  const errorParam = searchParams.get("error");

  const [state, formAction, isPending] = useActionState<AuthResult, FormData>(
    async (_prev, formData) => login(formData),
    {},
  );

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
          {auth.login.heading}
        </h1>
        <p style={{ color: "var(--color-text-secondary)", fontSize: 14 }}>
          {auth.login.subtitle}{" "}
          <Link
            href="/auth/signup"
            style={{
              color: "var(--color-primary)",
              fontWeight: 600,
              textDecoration: "none",
            }}
          >
            {auth.login.subtitleLink}
          </Link>
        </p>
      </div>

      {message && <Alert variant="success">{message}</Alert>}

      {errorParam && (
        <Alert variant="error" className="shake">
          {errorParam}
        </Alert>
      )}

      <GoogleOAuthButton onClick={() => signInWithOAuth("google")}>
        {auth.oauthGoogle}
      </GoogleOAuthButton>

      <FormDivider text={auth.dividerText} />

      {/* Login form */}
      <form action={formAction}>
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <FormField
            id="email"
            name="email"
            type="email"
            label={auth.labels.email}
            placeholder={auth.placeholders.email}
            required
            aria-describedby={state.error ? "login-error" : undefined}
          />

          <PasswordInput
            id="password"
            name="password"
            label={auth.labels.password}
            placeholder={auth.placeholders.password}
            required
            aria-describedby={state.error ? "login-error" : undefined}
            rightLabel={
              <Link
                href="/auth/reset-password"
                style={{
                  fontSize: 13,
                  color: "var(--color-primary)",
                  textDecoration: "none",
                }}
              >
                {auth.labels.forgotPassword}
              </Link>
            }
          />

          {state.error && (
            <Alert variant="error" id="login-error">
              {state.error}
            </Alert>
          )}

          <SubmitButton isPending={isPending}>
            {auth.login.submitLabel}
          </SubmitButton>
        </div>
      </form>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
