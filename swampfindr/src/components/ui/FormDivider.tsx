type FormDividerProps = {
  text?: string;
};

export function FormDivider({ text = "or continue with email" }: FormDividerProps) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 14,
        margin: "24px 0",
      }}
    >
      <div style={{ flex: 1, height: 1, background: "var(--color-border)" }} />
      <span style={{ fontSize: 13, color: "var(--color-text-muted)" }}>{text}</span>
      <div style={{ flex: 1, height: 1, background: "var(--color-border)" }} />
    </div>
  );
}
