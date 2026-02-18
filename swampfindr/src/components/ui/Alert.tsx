import type { ReactNode } from "react";
import { cn } from "@/lib/utils/cn";

type AlertProps = {
  variant: "error" | "success";
  children: ReactNode;
  className?: string;
  id?: string;
};

const styles = {
  error: {
    padding: "12px 16px",
    borderRadius: "var(--radius-sm)",
    background: "rgba(248, 113, 113, 0.08)",
    border: "1px solid rgba(248, 113, 113, 0.2)",
    color: "var(--color-accent)",
    fontSize: 14,
  },
  success: {
    padding: "12px 16px",
    borderRadius: "var(--radius-sm)",
    background: "rgba(34, 197, 94, 0.08)",
    border: "1px solid rgba(34, 197, 94, 0.2)",
    color: "#15803d",
    fontSize: 14,
  },
} as const;

export function Alert({ variant, children, className, id }: AlertProps) {
  return (
    <div
      id={id}
      role={variant === "error" ? "alert" : "status"}
      className={cn(variant === "error" && "shake", className)}
      style={styles[variant]}
    >
      {children}
    </div>
  );
}
