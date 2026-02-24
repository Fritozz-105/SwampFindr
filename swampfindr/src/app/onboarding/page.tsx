import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { onboarding } from "@/data";
import { OnboardingForm } from "./OnboardingForm";

export default async function OnboardingPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/auth/login");
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "40px 16px",
      }}
    >
      <div
        className="glass-strong animate-fade-up"
        style={{
          width: "100%",
          maxWidth: 600,
          padding: "40px 36px",
          borderRadius: "var(--radius-xl)",
          boxShadow: "var(--shadow-lg)",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <h1
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 28,
              fontWeight: 700,
              color: "var(--color-text)",
            }}
          >
            {onboarding.heading}
          </h1>
          <p
            style={{
              color: "var(--color-text-secondary)",
              fontSize: 15,
              marginTop: 8,
            }}
          >
            {onboarding.subtitle}
          </p>
        </div>

        <OnboardingForm />
      </div>
    </div>
  );
}
