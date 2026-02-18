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
          style={{ objectFit: "cover", filter: "blur(6px)", transform: "scale(1.08)" }}
        />
        <div style={{ position: "absolute", inset: 0, background: "rgba(10, 8, 28, 0.58)" }} />
      </div>

      {/* Content */}
      <div style={{ position: "relative", zIndex: 1, minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        <main style={{ flex: 1, display: "flex", alignItems: "center", padding: "80px 24px" }}>
          <div className="hero-grid animate-fade-up" style={{ maxWidth: 1100, margin: "0 auto", width: "100%" }}>

            {/* Left — copy */}
            <div>
              <p
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  letterSpacing: "0.12em",
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
                  fontSize: "clamp(36px, 5vw, 60px)",
                  fontWeight: 800,
                  color: "white",
                  lineHeight: 1.08,
                  marginBottom: 22,
                }}
              >
                {branding.heading}{" "}
                <span
                  style={{
                    background: "var(--gradient-primary)",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                  }}
                >
                  {branding.highlightWord}
                </span>
              </h1>

              <p
                style={{
                  fontSize: "clamp(16px, 2vw, 18px)",
                  color: "rgba(255,255,255,0.68)",
                  lineHeight: 1.7,
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
                    padding: "15px 36px",
                    textDecoration: "none",
                    display: "inline-block",
                    fontSize: 16,
                  }}
                >
                  {landing.ctaPrimary}
                </Link>
                <Link
                  href="/auth/login"
                  className="btn-outline-white"
                  style={{ textDecoration: "none" }}
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
                  className="glass"
                  style={{
                    padding: "22px 26px",
                    borderRadius: "var(--radius-md)",
                    borderLeft: "3px solid var(--color-primary)",
                  }}
                >
                  <p
                    style={{
                      fontFamily: "var(--font-display)",
                      fontWeight: 700,
                      fontSize: 15,
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
