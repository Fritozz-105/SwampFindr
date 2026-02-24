type SelectOption = {
  value: string;
  label: string;
};

type SelectFieldProps = {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  error?: string;
};

export function SelectField({ id, label, value, onChange, options, error }: SelectFieldProps) {
  return (
    <div>
      <label
        htmlFor={id}
        style={{
          display: "block",
          fontSize: 14,
          fontWeight: 500,
          color: "var(--color-text)",
          marginBottom: 6,
        }}
      >
        {label}
      </label>
      <select
        id={id}
        className="input-field"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={{ cursor: "pointer" }}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && (
        <p style={{ color: "var(--color-accent)", fontSize: 13, marginTop: 4 }}>{error}</p>
      )}
    </div>
  );
}
