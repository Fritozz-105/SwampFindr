export function SkeletonCard() {
  return (
    <div
      style={{
        borderRadius: "var(--radius-lg)",
        border: "1px solid var(--color-border)",
        background: "var(--color-surface)",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          aspectRatio: "16/10",
          background: "var(--color-bg)",
          animation: "pulse 1.5s ease-in-out infinite",
        }}
      />
      <div style={{ padding: 16 }}>
        <div
          style={{
            height: 20,
            width: "60%",
            background: "var(--color-bg)",
            borderRadius: 4,
            marginBottom: 8,
            animation: "pulse 1.5s ease-in-out infinite",
          }}
        />
        <div
          style={{
            height: 14,
            width: "80%",
            background: "var(--color-bg)",
            borderRadius: 4,
            marginBottom: 8,
            animation: "pulse 1.5s ease-in-out infinite",
          }}
        />
        <div
          style={{
            height: 13,
            width: "50%",
            background: "var(--color-bg)",
            borderRadius: 4,
            animation: "pulse 1.5s ease-in-out infinite",
          }}
        />
      </div>
    </div>
  );
}
