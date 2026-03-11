import { createClient } from "@/lib/supabase/server";
import { dashboard } from "@/data/dashboard";
import { HomeFeed } from "@/components/features/HomeFeed";

export default async function HomePage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const displayName =
    user?.user_metadata?.full_name || user?.email?.split("@")[0] || dashboard.defaultName;

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: "32px 24px" }}>
      <div style={{ marginBottom: 32 }}>
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
          {dashboard.greeting(displayName)}
        </h1>
        <p style={{ color: "var(--color-text-secondary)", fontSize: 15 }}>
          {dashboard.feed.subtitle}
        </p>
      </div>

      <HomeFeed />
    </div>
  );
}
