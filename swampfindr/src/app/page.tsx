import Image from "next/image";
import Link from "next/link";
import { branding } from "@/data/branding";
import { landing } from "@/data/landing";

export default function Home() {
  return (
    <div style={{ position: "relative", minHeight: "100vh", overflow: "hidden" }}>
      {/* Background image */}
      <div style={{ position: "absolute", inset: 0 }}>
        <Image
          src="/hero-bg.jpg"
          alt=""
          fill
          priority
          style={{ objectFit: "cover" }}
        />
        <div style={{ position: "absolute", inset: 0, background: "rgba(0, 0, 0, 0.55)" }} />
      </div>

      {/* Content */}
      <div style={{ position: "relative", zIndex: 1, minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        <main style={{ flex: 1, display: "flex", alignItems: "center", padding: "80px 24px" }}>
          <div className="hero-grid animate-fade-up" style={{ maxWidth: 1100, margin: "0 auto", width: "100%" }}>

            {/* Left — copy */}
            <div>
              <p
                style={{
                  fontSize: 11,
                  fontWeight: 500,
                  letterSpacing: "0.1em",
                  textTransform: "uppercase",
                  color: "rgba(255,255,255,0.5)",
                  marginBottom: 24,
                }}
              >
                {branding.university} &mdash; {branding.tagline}
              </p>

              <h1
                style={{
                  fontFamily: "var(--font-display)",
                  fontSize: "clamp(40px, 6vw, 72px)",
                  fontWeight: 800,
                  color: "white",
                  lineHeight: 1.08,
                  letterSpacing: "-0.03em",
                  marginBottom: 22,
                }}
              >
                {branding.heading}{" "}
                <span
                  style={{
                    color: "var(--color-accent)",
                  }}
                >
                  {branding.highlightWord}
                </span>
              </h1>

              <p
                style={{
                  fontSize: "clamp(16px, 2vw, 18px)",
                  color: "rgba(255,255,255,0.65)",
                  lineHeight: 1.6,
                  marginBottom: 40,
                  maxWidth: 420,
                }}
              >
                {landing.tagline}
              </p>

              <div style={{ display: "flex", gap: 14, flexWrap: "wrap" }}>
                <Link
                  href="/auth/signup"
                  className="btn-primary"
                  style={{
                    width: "auto",
                    padding: "14px 32px",
                    textDecoration: "none",
                    display: "inline-block",
                  }}
                >
                  {landing.ctaPrimary}
                </Link>
                <Link
                  href="/auth/login"
                  style={{
                    padding: "14px 32px",
                    background: "rgba(255, 255, 255, 0.08)",
                    border: "1px solid rgba(255, 255, 255, 0.25)",
                    borderRadius: "var(--radius-sm)",
                    fontFamily: "var(--font-display)",
                    fontWeight: 600,
                    fontSize: 15,
                    color: "white",
                    textDecoration: "none",
                    display: "inline-block",
                  }}
                >
                  {landing.ctaSecondary}
                </Link>
              </div>
            </div>

            {/* Right — feature cards */}
            <div className="stagger" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {landing.features.map((f) => (
                <div
                  key={f.title}
                  style={{
                    padding: "20px 24px",
                    borderRadius: "var(--radius-md)",
                    background: "rgba(255, 255, 255, 0.06)",
                    borderTop: "1px solid rgba(255, 255, 255, 0.1)",
                    borderRight: "1px solid rgba(255, 255, 255, 0.1)",
                    borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
                    borderLeft: "3px solid var(--color-accent)",
                  }}
                >
                  <p
                    style={{
                      fontFamily: "var(--font-display)",
                      fontWeight: 600,
                      fontSize: 15,
                      letterSpacing: "-0.01em",
                      color: "white",
                      marginBottom: 6,
                    }}
                  >
                    {f.title}
                  </p>
                  <p
                    style={{
                      fontSize: 14,
                      color: "rgba(255,255,255,0.62)",
                      lineHeight: 1.6,
                    }}
                  >
                    {f.body}
                  </p>
                </div>
              ))}
            </div>

          </div>
        </main>
      </div>
    </div>
  );
}
