"use client";

import { getPasswordStrength } from "@/lib/utils/password";

type PasswordStrengthProps = {
  password: string;
};

const LEVELS = [1, 2, 3, 4, 5] as const;

export function PasswordStrength({ password }: PasswordStrengthProps) {
  if (!password) return null;

  const strength = getPasswordStrength(password);

  return (
    <div id="password-strength" style={{ marginTop: 8 }}>
      <div style={{ display: "flex", gap: 4, marginBottom: 4 }}>
        {LEVELS.map((level) => (
          <div
            key={level}
            style={{
              flex: 1,
              height: 3,
              borderRadius: 2,
              background:
                level <= strength.score ? strength.color : "rgba(0,0,0,0.08)",
              transition: "background 0.3s",
            }}
          />
        ))}
      </div>
      <span style={{ fontSize: 12, color: strength.color, fontWeight: 500 }}>
        {strength.label}
      </span>
    </div>
  );
}
