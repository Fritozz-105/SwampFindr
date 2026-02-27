"use client";

import { useState, useRef } from "react";
import { createClient } from "@/lib/supabase/client";
import { settings } from "@/data/settings";
import { errors } from "@/data/errors";
import { Alert } from "@/components/ui";

type MfaState = "loading" | "disabled" | "enrolling" | "verifying" | "enabled";

async function fetchMfaStatus(): Promise<{ state: MfaState; factorId: string }> {
  try {
    const supabase = createClient();
    const { data, error } = await supabase.auth.mfa.listFactors();
    if (error) return { state: "disabled", factorId: "" };
    const totp = data.totp.find((f) => f.status === "verified");
    return totp ? { state: "enabled", factorId: totp.id } : { state: "disabled", factorId: "" };
  } catch {
    return { state: "disabled", factorId: "" };
  }
}

export function MfaSection() {
  const [state, setState] = useState<MfaState>("loading");
  const [qrCode, setQrCode] = useState("");
  const [factorId, setFactorId] = useState("");
  const [verifyCode, setVerifyCode] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const initRef = useRef<Promise<void> | null>(null);

  // Trigger initial fetch once (React-safe ref initialization pattern)
  if (initRef.current == null) {
    initRef.current = fetchMfaStatus().then(({ state: s, factorId: fid }) => {
      setState(s);
      if (fid) setFactorId(fid);
    });
  }

  async function handleEnroll() {
    setError("");
    setState("enrolling");

    try {
      const supabase = createClient();
      const { data, error: enrollErr } = await supabase.auth.mfa.enroll({
        factorType: "totp",
      });

      if (enrollErr || !data) {
        setError(errors.settings.mfaEnrollFailed);
        setState("disabled");
        return;
      }

      setFactorId(data.id);
      setQrCode(data.totp.qr_code);
      setState("verifying");
    } catch {
      setError(errors.settings.mfaEnrollFailed);
      setState("disabled");
    }
  }

  async function handleVerify() {
    setError("");

    try {
      const supabase = createClient();
      const { data: challenge, error: challengeErr } = await supabase.auth.mfa.challenge({
        factorId,
      });

      if (challengeErr || !challenge) {
        setError(errors.settings.mfaVerifyFailed);
        return;
      }

      const { error: verifyErr } = await supabase.auth.mfa.verify({
        factorId,
        challengeId: challenge.id,
        code: verifyCode,
      });

      if (verifyErr) {
        setError(errors.settings.mfaVerifyFailed);
        return;
      }

      setSuccess(settings.messages.mfaEnabled);
      setVerifyCode("");
      setQrCode("");
      setState("enabled");
    } catch {
      setError(errors.settings.mfaVerifyFailed);
    }
  }

  async function handleUnenroll() {
    setError("");
    setSuccess("");

    try {
      const supabase = createClient();
      const { error: unenrollErr } = await supabase.auth.mfa.unenroll({
        factorId,
      });

      if (unenrollErr) {
        setError(errors.settings.mfaUnenrollFailed);
        return;
      }

      setSuccess(settings.messages.mfaDisabled);
      setFactorId("");
      setState("disabled");
    } catch {
      setError(errors.settings.mfaUnenrollFailed);
    }
  }

  const s = settings.sections.mfa;

  if (state === "loading") {
    return <p style={{ color: "var(--color-text-muted)", fontSize: 14 }}>Loading...</p>;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {state === "disabled" && (
        <>
          <p style={{ color: "var(--color-text-muted)", fontSize: 14 }}>{s.disabled}</p>
          <button
            type="button"
            className="btn-primary"
            onClick={handleEnroll}
            style={{ alignSelf: "flex-start", width: "auto", padding: "10px 24px" }}
          >
            {s.enableButton}
          </button>
        </>
      )}

      {state === "verifying" && (
        <>
          <p style={{ fontSize: 14, color: "var(--color-text-secondary)" }}>{s.scanPrompt}</p>
          {qrCode && (
            <div style={{ display: "flex", justifyContent: "center", padding: 16 }}>
              {/* eslint-disable-next-line @next/next/no-img-element -- QR is a data URI */}
              <img
                src={qrCode}
                alt="TOTP QR Code"
                style={{ width: 200, height: 200, borderRadius: 8 }}
              />
            </div>
          )}
          <div>
            <label
              htmlFor="mfa-code"
              style={{
                display: "block",
                fontSize: 14,
                fontWeight: 500,
                color: "var(--color-text)",
                marginBottom: 6,
              }}
            >
              {s.enterCode}
            </label>
            <input
              id="mfa-code"
              type="text"
              className="input-field"
              placeholder="000000"
              maxLength={6}
              value={verifyCode}
              onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, ""))}
              style={{ maxWidth: 200, letterSpacing: 4, textAlign: "center" }}
            />
          </div>
          <button
            type="button"
            className="btn-primary"
            disabled={verifyCode.length !== 6}
            onClick={handleVerify}
            style={{ alignSelf: "flex-start", width: "auto", padding: "10px 24px" }}
          >
            {s.verifyButton}
          </button>
        </>
      )}

      {state === "enabled" && (
        <>
          <p style={{ color: "var(--color-text-secondary)", fontSize: 14 }}>{s.enabled}</p>
          <button
            type="button"
            className="btn-secondary"
            onClick={handleUnenroll}
            style={{ alignSelf: "flex-start", padding: "10px 24px" }}
          >
            {s.disableButton}
          </button>
        </>
      )}

      {error && <Alert variant="error">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}
    </div>
  );
}
