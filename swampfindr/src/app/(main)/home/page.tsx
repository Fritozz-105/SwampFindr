import { createClient } from "@/lib/supabase/server";
import { dashboard } from "@/data/dashboard";

export default async function HomePage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const displayName =
    user?.user_metadata?.full_name || user?.email?.split("@")[0] || dashboard.defaultName;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "calc(100vh - 64px)",
      }}
    >
      <div
        className="animate-fade-up"
        style={{
          maxWidth: 480,
          width: "100%",
          borderRadius: "var(--radius-lg)",
          padding: "48px 36px",
          textAlign: "center",
          background: "var(--color-surface)",
          border: "1px solid var(--color-border)",
        }}
      >
        <div
          style={{
            width: 64,
            height: 64,
            borderRadius: "50%",
            background: "var(--color-primary)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "0 auto 24px",
            fontSize: 28,
            color: "white",
            fontFamily: "var(--font-display)",
            fontWeight: 700,
          }}
        >
          {displayName.charAt(0).toUpperCase()}
        </div>

        <h1
          style={{
            fontFamily: "var(--font-display)",
            fontSize: 24,
            fontWeight: 700,
            color: "var(--color-text)",
            letterSpacing: "-0.02em",
            marginBottom: 8,
          }}
        >
          {dashboard.greeting(displayName)}
        </h1>
        <p
          style={{
            color: "var(--color-text-secondary)",
            fontSize: 15,
          }}
        >
          {dashboard.placeholder}
        </p>
      </div>
    </div>
  );
}
