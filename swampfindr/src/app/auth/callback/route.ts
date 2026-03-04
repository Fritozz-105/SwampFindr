import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { errors } from "@/data/errors";

const FLASK_API_URL = process.env.FLASK_API_URL ?? "http://localhost:8080";

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const type = searchParams.get("type");
  const next = searchParams.get("next") ?? "/home";

  // Validate redirect path — only allow relative paths to prevent open redirects
  const redirectPath = next.startsWith("/") && !next.startsWith("//") ? next : "/home";

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);

    if (!error) {
      if (type === "recovery") {
        return NextResponse.redirect(`${origin}/auth/update-password`);
      }

      // Check onboarding status from backend
      // null = couldn't reach Flask, preserve existing cookie
      let onboardingCompleted: boolean | null = null;
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
        // Backend unreachable — preserve existing cookie below
      }

      // If Flask was unreachable, fall back to the existing cookie value
      const existingCookie = request.headers.get("cookie") ?? "";
      const existingValue = existingCookie
        .split(";")
        .map((c) => c.trim())
        .find((c) => c.startsWith("onboarding_completed="))
        ?.split("=")[1];

      const finalValue =
        onboardingCompleted !== null
          ? onboardingCompleted
          : existingValue === "true";

      const response = NextResponse.redirect(
        `${origin}${finalValue ? redirectPath : "/onboarding"}`,
      );
      response.cookies.set("onboarding_completed", String(finalValue), {
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
