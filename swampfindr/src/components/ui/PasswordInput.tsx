"use client";

import { type ReactNode, useState } from "react";
import { EyeIcon, EyeSlashIcon } from "./icons";

type PasswordInputProps = {
  id: string;
  name: string;
  label: string;
  placeholder?: string;
  required?: boolean;
  "aria-describedby"?: string;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void;
  rightLabel?: ReactNode;
};

export function PasswordInput({
  id,
  name,
  label,
  placeholder,
  required,
  "aria-describedby": ariaDescribedby,
  value,
  onChange,
  onBlur,
  rightLabel,
}: PasswordInputProps) {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 4,
        }}
      >
        <label
          htmlFor={id}
          style={{ fontSize: 13, fontWeight: 500, color: "var(--color-text-secondary)" }}
        >
          {label}
        </label>
        {rightLabel}
      </div>
      <div style={{ position: "relative" }}>
        <input
          id={id}
          name={name}
          type={showPassword ? "text" : "password"}
          className="input-field"
          placeholder={placeholder}
          required={required}
          style={{ paddingRight: 48 }}
          aria-describedby={ariaDescribedby}
          value={value}
          onChange={onChange}
          onBlur={onBlur}
        />
        <button
          type="button"
          className="password-toggle"
          onClick={() => setShowPassword((prev) => !prev)}
          aria-label={showPassword ? "Hide password" : "Show password"}
        >
          {showPassword ? <EyeSlashIcon /> : <EyeIcon />}
        </button>
      </div>
    </div>
  );
}
