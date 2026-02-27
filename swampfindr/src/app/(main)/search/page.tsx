export default function SearchPage() {
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
          Search
        </h1>
        <p style={{ color: "var(--color-text-secondary)", fontSize: 15 }}>
          Housing search is coming soon.
        </p>
      </div>
    </div>
  );
}
