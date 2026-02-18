import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { errors } from "@/data/errors";

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
      return NextResponse.redirect(`${origin}${redirectPath}`);
    }
  }

  return NextResponse.redirect(
    `${origin}/auth/login?error=${errors.callback.authFailed}`,
  );
}
