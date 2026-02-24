type FormFieldProps = {
  id: string;
  name: string;
  type?: string;
  label: string;
  placeholder?: string;
  required?: boolean;
  "aria-describedby"?: string;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  error?: string;
};

export function FormField({
  id,
  name,
  type = "text",
  label,
  placeholder,
  required,
  "aria-describedby": ariaDescribedby,
  value,
  onChange,
  error,
}: FormFieldProps) {
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
      <input
        id={id}
        name={name}
        type={type}
        className="input-field"
        placeholder={placeholder}
        required={required}
        aria-describedby={ariaDescribedby}
        {...(value !== undefined ? { value, onChange } : {})}
      />
      {error && (
        <p style={{ color: "var(--color-accent)", fontSize: 13, marginTop: 4 }}>{error}</p>
      )}
    </div>
  );
}
