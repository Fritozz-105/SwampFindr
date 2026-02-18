import type { ReactNode } from "react";
import { cn } from "@/lib/utils/cn";

type SubmitButtonProps = {
  isPending: boolean;
  children: ReactNode;
  className?: string;
};

export function SubmitButton({ isPending, children, className }: SubmitButtonProps) {
  return (
    <button
      type="submit"
      className={cn("btn-primary", className)}
      disabled={isPending}
    >
      {isPending ? (
        <span style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
          <span className="spinner" />
        </span>
      ) : (
        children
      )}
    </button>
  );
}
