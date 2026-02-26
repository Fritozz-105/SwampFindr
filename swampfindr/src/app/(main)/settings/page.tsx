import { createClient } from "@/lib/supabase/server";
import { settings } from "@/data/settings";
import { SettingsForm } from "./SettingsForm";

const FLASK_API_URL = process.env.FLASK_API_URL ?? "http://localhost:5000";

export default async function SettingsPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  let profile = null;
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (session?.access_token) {
      const res = await fetch(`${FLASK_API_URL}/api/v1/profiles/me`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
        cache: "no-store",
      });
      if (res.ok) {
        const body = await res.json();
        profile = body.data;
      }
    }
  } catch {
    // Flask unavailable — form will show loading state via client hook
  }

  return (
    <div style={{ maxWidth: 640, margin: "0 auto" }}>
      <div className="animate-fade-up" style={{ marginBottom: 32 }}>
        <h1
          style={{
            fontFamily: "var(--font-display)",
            fontSize: 28,
            fontWeight: 700,
            color: "var(--color-text)",
            letterSpacing: "-0.02em",
            marginBottom: 4,
          }}
        >
          {settings.heading}
        </h1>
        <p style={{ color: "var(--color-text-secondary)", fontSize: 15 }}>
          {settings.subtitle}
        </p>
      </div>

      <SettingsForm
        user={user ? { id: user.id, email: user.email ?? "", provider: user.app_metadata?.provider ?? "email" } : null}
        initialProfile={profile}
      />
    </div>
  );
}
