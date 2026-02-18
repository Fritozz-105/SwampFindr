import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { logout } from "@/app/auth/actions";
import { dashboard } from "@/data/dashboard";

export default async function DashboardPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/auth/login");
  }

  const displayName =
    user.user_metadata?.full_name || user.email?.split("@")[0] || dashboard.defaultName;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        padding: 24,
      }}
    >
      <div
        className="glass-strong animate-fade-up"
        style={{
          maxWidth: 480,
          width: "100%",
          borderRadius: "var(--radius-xl)",
          padding: "48px 36px",
          textAlign: "center",
          boxShadow: "var(--shadow-lg)",
        }}
      >
        <div
          style={{
            width: 64,
            height: 64,
            borderRadius: "50%",
            background: "var(--gradient-primary)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "0 auto 24px",
            fontSize: 28,
          }}
        >
          <span role="img" aria-label="waving hand" style={{ filter: "grayscale(0)" }}>
            {displayName.charAt(0).toUpperCase()}
          </span>
        </div>

        <h1
          style={{
            fontFamily: "var(--font-display)",
            fontSize: 24,
            fontWeight: 700,
            color: "var(--color-text)",
            marginBottom: 8,
          }}
        >
          {dashboard.greeting(displayName)}
        </h1>
        <p
          style={{
            color: "var(--color-text-secondary)",
            fontSize: 15,
            marginBottom: 32,
          }}
        >
          {dashboard.placeholder}
        </p>

        <form action={logout}>
          <button
            type="submit"
            style={{
              padding: "12px 32px",
              background: "transparent",
              border: "1.5px solid rgba(124, 92, 252, 0.2)",
              borderRadius: "var(--radius-sm)",
              fontFamily: "var(--font-display)",
              fontWeight: 600,
              fontSize: 15,
              color: "var(--color-text-secondary)",
              cursor: "pointer",
              transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
            }}
          >
            {dashboard.signOut}
          </button>
        </form>
      </div>
    </div>
  );
}
