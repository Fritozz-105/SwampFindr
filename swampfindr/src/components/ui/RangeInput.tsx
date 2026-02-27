type RangeInputProps = {
  label: string;
  minValue: number;
  maxValue: number;
  onMinChange: (value: number) => void;
  onMaxChange: (value: number) => void;
  minPlaceholder?: string;
  maxPlaceholder?: string;
  minLabel?: string;
  maxLabel?: string;
  error?: string;
};

export function RangeInput({
  label,
  minValue,
  maxValue,
  onMinChange,
  onMaxChange,
  minPlaceholder,
  maxPlaceholder,
  minLabel = "Min",
  maxLabel = "Max",
  error,
}: RangeInputProps) {
  return (
    <div>
      <label
        style={{
          display: "block",
          fontSize: 13,
          fontWeight: 500,
          color: "var(--color-text-secondary)",
          marginBottom: 4,
        }}
      >
        {label}
      </label>
      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
        <div style={{ flex: 1 }}>
          <span
            style={{
              fontSize: 12,
              color: "var(--color-text-muted)",
              marginBottom: 2,
              display: "block",
            }}
          >
            {minLabel}
          </span>
          <input
            type="number"
            className="input-field"
            value={minValue}
            onChange={(e) => onMinChange(Number(e.target.value))}
            placeholder={minPlaceholder}
            min={0}
          />
        </div>
        <span style={{ color: "var(--color-border-strong)", marginTop: 18 }}>&ndash;</span>
        <div style={{ flex: 1 }}>
          <span
            style={{
              fontSize: 12,
              color: "var(--color-text-muted)",
              marginBottom: 2,
              display: "block",
            }}
          >
            {maxLabel}
          </span>
          <input
            type="number"
            className="input-field"
            value={maxValue}
            onChange={(e) => onMaxChange(Number(e.target.value))}
            placeholder={maxPlaceholder}
            min={0}
          />
        </div>
      </div>
      {error && <p style={{ color: "var(--color-error)", fontSize: 13, marginTop: 4 }}>{error}</p>}
    </div>
  );
}
