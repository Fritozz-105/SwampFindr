export type PasswordStrengthResult = {
  score: number;
  label: string;
  color: string;
};

export function getPasswordStrength(password: string): PasswordStrengthResult {
  if (!password) return { score: 0, label: "", color: "transparent" };

  let score = 0;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[a-z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (password.length >= 12) score++;

  if (score <= 2) return { score, label: "Weak", color: "var(--color-accent)" };
  if (score <= 3) return { score, label: "Fair", color: "#f59e0b" };
  if (score <= 4) return { score, label: "Good", color: "#22c55e" };
  return { score, label: "Strong", color: "#15803d" };
}
