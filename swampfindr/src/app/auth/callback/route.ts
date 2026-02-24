import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { errors } from "@/data/errors";

const FLASK_API_URL = process.env.FLASK_API_URL ?? "http://localhost:5000";

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const type = searchParams.get("type");
  const next = searchParams.get("next") ?? "/dashboard";

  // Validate redirect path — only allow relative paths to prevent open redirects
  const redirectPath = next.startsWith("/") && !next.startsWith("//") ? next : "/dashboard";

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);

    if (!error) {
      if (type === "recovery") {
        return NextResponse.redirect(`${origin}/auth/update-password`);
      }

      // Check onboarding status from backend
      let onboardingCompleted = false;
      try {
        const {
          data: { session },
        } = await supabase.auth.getSession();

        if (session?.access_token) {
          const res = await fetch(`${FLASK_API_URL}/api/v1/profiles/status`, {
            headers: { Authorization: `Bearer ${session.access_token}` },
          });
          if (res.ok) {
            const body = await res.json();
            onboardingCompleted = body.onboarding_completed === true;
          }
        }
      } catch {
        // Backend unreachable — graceful degradation, let through to dashboard
      }

      const response = NextResponse.redirect(
        `${origin}${onboardingCompleted ? redirectPath : "/onboarding"}`,
      );
      response.cookies.set("onboarding_completed", String(onboardingCompleted), {
        path: "/",
        maxAge: 60 * 60 * 24 * 365,
        sameSite: "lax",
      });
      return response;
    }
  }

  return NextResponse.redirect(
    `${origin}/auth/login?error=${errors.callback.authFailed}`,
  );
}
