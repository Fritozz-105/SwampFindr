import Image from "next/image";
import Link from "next/link";
import { branding } from "@/data/branding";
import { auth } from "@/data/auth";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      {/* Left — branding panel (hidden on mobile) */}
      <div
        className="auth-left-panel"
        style={{ position: "relative", flex: "0 0 44%", overflow: "hidden" }}
      >
        <Image
          src="/hero-bg.jpg"
          alt=""
          fill
          priority
          style={{
            objectFit: "cover",
          }}
        />
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: "rgba(0, 0, 0, 0.55)",
          }}
        />

        <div
          style={{
            position: "relative",
            zIndex: 1,
            height: "100%",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            padding: "40px 48px",
          }}
        >
          <Link href="/" style={{ textDecoration: "none" }}>
            <span
              style={{
                fontFamily: "var(--font-display)",
                fontWeight: 700,
                fontSize: 18,
                color: "white",
                letterSpacing: "-0.02em",
              }}
            >
              {branding.appName}
            </span>
          </Link>

          <div>
            <p
              style={{
                fontSize: 11,
                fontWeight: 500,
                letterSpacing: "0.1em",
                textTransform: "uppercase",
                color: "rgba(255,255,255,0.5)",
                marginBottom: 18,
              }}
            >
              {branding.university}
            </p>
            <h2
              style={{
                fontFamily: "var(--font-display)",
                fontSize: "clamp(28px, 3vw, 40px)",
                fontWeight: 700,
                color: "white",
                lineHeight: 1.12,
                letterSpacing: "-0.02em",
                marginBottom: 16,
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
            </h2>
            <p
              style={{
                fontSize: 15,
                color: "rgba(255,255,255,0.6)",
                lineHeight: 1.6,
                maxWidth: 300,
              }}
            >
              {auth.layout.panelSubtitle}
            </p>
          </div>

          <p style={{ fontSize: 12, color: "rgba(255,255,255,0.3)" }}>
            {branding.copyright(new Date().getFullYear())}
          </p>
        </div>
      </div>

      {/* Right — form panel */}
      <div
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "var(--color-surface)",
          padding: "40px 24px",
          overflowY: "auto",
        }}
      >
        <div style={{ width: "100%", maxWidth: 400 }}>{children}</div>
      </div>
    </div>
  );
}
