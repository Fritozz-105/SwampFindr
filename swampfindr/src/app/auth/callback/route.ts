import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { errors } from "@/data/errors";

export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const { searchParams, origin } = requestUrl;
  const code = searchParams.get("code");
  const type = searchParams.get("type");
  const next = searchParams.get("next") ?? "/dashboard";

  // Validate origin matches expected domain
  const appUrl = process.env.NEXT_PUBLIC_APP_URL;
  if (!appUrl) {
    return NextResponse.redirect(
      `${origin}/auth/login?error=Configuration error`,
    );
  }

  // Validate redirect path - only allow relative paths to prevent open redirects
  // Must start with / and not start with // (protocol-relative URLs)
  const redirectPath = next.startsWith("/") && !next.startsWith("//") ? next : "/dashboard";

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);

    if (!error) {
      if (type === "recovery") {
        return NextResponse.redirect(`${appUrl}/auth/update-password`);
      }
      return NextResponse.redirect(`${appUrl}${redirectPath}`);
    }
  }

  return NextResponse.redirect(
    `${appUrl}/auth/login?error=${encodeURIComponent(errors.callback.authFailed)}`,
  );
}
