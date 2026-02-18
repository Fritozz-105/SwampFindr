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
      <div style={{ flex: 1, height: 1, background: "#e8e8e8" }} />
      <span style={{ fontSize: 13, color: "#aaa" }}>{text}</span>
      <div style={{ flex: 1, height: 1, background: "#e8e8e8" }} />
    </div>
  );
}
