"use client";

type TextAreaProps = {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  maxLength: number;
  error?: string;
};

export function TextArea({
  id,
  label,
  value,
  onChange,
  placeholder,
  maxLength,
  error,
}: TextAreaProps) {
  const remaining = maxLength - value.length;
  const isNearLimit = remaining <= 20;

  return (
    <div>
      <label
        htmlFor={id}
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
      <textarea
        id={id}
        className="input-field"
        value={value}
        onChange={(e) => onChange(e.target.value.slice(0, maxLength))}
        placeholder={placeholder}
        rows={3}
        style={{ resize: "vertical", minHeight: 80 }}
      />
      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          marginTop: 4,
        }}
      >
        <span
          style={{
            fontSize: 12,
            color: isNearLimit ? "var(--color-error)" : "var(--color-text-muted)",
            fontWeight: isNearLimit ? 600 : 400,
          }}
        >
          {value.length}/{maxLength}
        </span>
      </div>
      {error && <p style={{ color: "var(--color-error)", fontSize: 13, marginTop: 2 }}>{error}</p>}
    </div>
  );
}
