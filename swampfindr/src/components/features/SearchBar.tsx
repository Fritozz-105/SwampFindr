"use client";

import { Search } from "lucide-react";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (value: string) => void;
  compact?: boolean;
  loading?: boolean;
}

export function SearchBar({
  value,
  onChange,
  onSubmit,
  compact = false,
  loading = false,
}: SearchBarProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (value.trim()) {
      onSubmit(value.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ width: "100%" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: compact ? 8 : 12,
          padding: compact ? "8px 12px" : "12px 16px",
          background: "#fff",
          border: "1px solid #e2e2e8",
          borderRadius: 8,
          transition: "border-color 0.15s ease",
        }}
        onFocus={(e) => {
          (e.currentTarget as HTMLDivElement).style.borderColor = "#4F3CC9";
        }}
        onBlur={(e) => {
          (e.currentTarget as HTMLDivElement).style.borderColor = "#e2e2e8";
        }}
      >
        <Search
          size={compact ? 16 : 20}
          style={{ color: "#8c8c9a", flexShrink: 0 }}
        />
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Search for housing near UF..."
          disabled={loading}
          style={{
            flex: 1,
            border: "none",
            outline: "none",
            background: "transparent",
            fontSize: compact ? 14 : 16,
            color: "#1a1a2e",
            fontFamily: "var(--font-body)",
          }}
        />
        {!compact && (
          <button
            type="submit"
            disabled={!value.trim() || loading}
            style={{
              padding: "8px 20px",
              background:
                !value.trim() || loading ? "#c4c0da" : "#4F3CC9",
              color: "#fff",
              border: "none",
              borderRadius: 6,
              fontSize: 14,
              fontWeight: 600,
              fontFamily: "var(--font-body)",
              cursor:
                !value.trim() || loading ? "not-allowed" : "pointer",
              transition: "background 0.15s ease",
              flexShrink: 0,
            }}
          >
            {loading ? "Searching..." : "Search"}
          </button>
        )}
      </div>
    </form>
  );
}
