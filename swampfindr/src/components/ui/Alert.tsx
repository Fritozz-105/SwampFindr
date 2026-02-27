import type { ReactNode } from "react";

type AlertProps = {
  variant: "error" | "success";
  children: ReactNode;
  className?: string;
  id?: string;
};

const styles = {
  error: {
    padding: "12px 16px",
    borderRadius: "var(--radius-md)",
    background: "var(--color-error-bg)",
    border: "1px solid rgba(220, 38, 38, 0.2)",
    color: "var(--color-error)",
    fontSize: 14,
  },
  success: {
    padding: "12px 16px",
    borderRadius: "var(--radius-md)",
    background: "var(--color-success-bg)",
    border: "1px solid rgba(22, 163, 74, 0.2)",
    color: "var(--color-success)",
    fontSize: 14,
  },
} as const;

export function Alert({ variant, children, className, id }: AlertProps) {
  return (
    <div
      id={id}
      role={variant === "error" ? "alert" : "status"}
      className={className}
      style={styles[variant]}
    >
      {children}
    </div>
  );
}
