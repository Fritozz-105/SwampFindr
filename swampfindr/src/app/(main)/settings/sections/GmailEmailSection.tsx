"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { getToken } from "@/lib/supabase/client";
import { settings } from "@/data/settings";
import { errors } from "@/data/errors";
import { Alert } from "@/components/ui";

const API_URL = process.env.NEXT_PUBLIC_FLASK_API_URL ?? "http://localhost:8080";

type GmailStatusResponse = {
  success: boolean;
  enabled: boolean;
  google_email: string | null;
  connected_at: string | null;
};

export function GmailEmailSection() {
  const searchParams = useSearchParams();
  const [enabled, setEnabled] = useState(false);
  const [googleEmail, setGoogleEmail] = useState("");
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadStatus = useCallback(async () => {
    setLoading(true);
    try {
      const token = await getToken();
      if (!token) {
        setError(errors.settings.gmailStatusFailed);
        setLoading(false);
        return;
      }

      const res = await fetch(`${API_URL}/api/v1/emailing/google/status`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        setError(errors.settings.gmailStatusFailed);
        setLoading(false);
        return;
      }

      const body = (await res.json()) as GmailStatusResponse;
      setEnabled(body.enabled);
      setGoogleEmail(body.google_email ?? "");
    } catch {
      setError(errors.settings.networkError);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  useEffect(() => {
    const gmailResult = searchParams.get("gmail");
    if (!gmailResult) return;

    if (gmailResult === "connected") {
      setSuccess(settings.messages.gmailConnected);
      setError("");
      loadStatus();
    } else if (gmailResult === "error") {
      setError(errors.settings.gmailConnectFailed);
      setSuccess("");
    }

    if (typeof window !== "undefined") {
      const url = new URL(window.location.href);
      url.searchParams.delete("gmail");
      url.searchParams.delete("reason");
      const search = url.searchParams.toString();
      window.history.replaceState({}, "", `${url.pathname}${search ? `?${search}` : ""}`);
    }
  }, [searchParams, loadStatus]);

  async function handleConnect() {
    setConnecting(true);
    setError("");
    setSuccess("");
    try {
      const token = await getToken();
      if (!token) {
        setError(errors.settings.gmailConnectFailed);
        setConnecting(false);
        return;
      }

      const res = await fetch(`${API_URL}/api/v1/emailing/google/connect`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        setError(errors.settings.gmailConnectFailed);
        setConnecting(false);
        return;
      }

      const body = (await res.json()) as { success: boolean; auth_url?: string };
      if (!body.auth_url) {
        setError(errors.settings.gmailConnectFailed);
        setConnecting(false);
        return;
      }
      window.location.assign(body.auth_url);
    } catch {
      setError(errors.settings.networkError);
      setConnecting(false);
    }
  }

  async function handleDisconnect() {
    setDisconnecting(true);
    setError("");
    setSuccess("");
    try {
      const token = await getToken();
      if (!token) {
        setError(errors.settings.gmailDisconnectFailed);
        setDisconnecting(false);
        return;
      }

      const res = await fetch(`${API_URL}/api/v1/emailing/google/disconnect`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        setError(errors.settings.gmailDisconnectFailed);
        setDisconnecting(false);
        return;
      }

      setEnabled(false);
      setGoogleEmail("");
      setSuccess(settings.messages.gmailDisconnected);
    } catch {
      setError(errors.settings.networkError);
    } finally {
      setDisconnecting(false);
    }
  }

  if (loading) {
    return <p style={{ color: "var(--color-text-muted)", fontSize: 14 }}>Loading...</p>;
  }

  const s = settings.sections.gmail;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <p style={{ color: "var(--color-text-secondary)", fontSize: 14 }}>
        {enabled
          ? `${s.connectedLabel}: ${googleEmail || "Google account"}`
          : s.disconnectedLabel}
      </p>

      {!enabled ? (
        <button
          type="button"
          className="btn-primary"
          disabled={connecting}
          onClick={handleConnect}
          style={{ alignSelf: "flex-start", width: "auto", padding: "10px 24px" }}
        >
          {connecting ? s.connecting : s.connectButton}
        </button>
      ) : (
        <button
          type="button"
          className="btn-secondary"
          disabled={disconnecting}
          onClick={handleDisconnect}
          style={{ alignSelf: "flex-start", width: "auto", padding: "10px 24px" }}
        >
          {disconnecting ? s.disconnecting : s.disconnectButton}
        </button>
      )}

      {error && <Alert variant="error">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}
    </div>
  );
}
