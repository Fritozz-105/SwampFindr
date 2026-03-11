"use client";

interface PaginationProps {
  page: number;
  hasNext: boolean;
  onPageChange: (page: number) => void;
  total: number;
  perPage?: number;
}

export function Pagination({ page, hasNext, onPageChange, total, perPage = 12 }: PaginationProps) {
  const btnStyle = (disabled: boolean): React.CSSProperties => ({
    width: 100,
    padding: "8px 0",
    fontSize: 14,
    fontFamily: "var(--font-body)",
    borderWidth: 1,
    borderStyle: "solid",
    borderColor: "var(--color-border)",
    borderRadius: "var(--radius-sm)",
    background: disabled ? "var(--color-bg)" : "var(--color-surface)",
    color: disabled ? "var(--color-text-tertiary)" : "var(--color-text)",
    cursor: disabled ? "not-allowed" : "pointer",
    textAlign: "center" as const,
  });

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 16,
        padding: "24px 0",
      }}
    >
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        style={btnStyle(page <= 1)}
      >
        Previous
      </button>

      <span
        style={{
          fontSize: 14,
          color: "var(--color-text-secondary)",
          minWidth: 100,
          textAlign: "center",
        }}
      >
        Page {page} of {Math.max(1, Math.ceil(total / perPage))}
      </span>

      <button
        onClick={() => onPageChange(page + 1)}
        disabled={!hasNext}
        style={btnStyle(!hasNext)}
      >
        Next
      </button>
    </div>
  );
}
