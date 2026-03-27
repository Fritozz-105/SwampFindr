"use client";

import { Clock } from "lucide-react";
import type { SearchHistoryEntry } from "@/types/search";

interface RecentSearchesProps {
  searches: SearchHistoryEntry[];
  onSearchClick: (query: string) => void;
  loading?: boolean;
}

export function RecentSearches({
  searches,
  onSearchClick,
  loading = false,
}: RecentSearchesProps) {
  if (!loading && searches.length === 0) return null;

  return (
    <div>
      <h3
        style={{
          fontSize: 13,
          fontWeight: 600,
          color: "#8c8c9a",
          textTransform: "uppercase" as const,
          letterSpacing: "0.05em",
          marginBottom: 12,
          fontFamily: "var(--font-body)",
        }}
      >
        Recent Searches
      </h3>

      {loading ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              style={{
                height: 40,
                background: "#f5f5f7",
                borderRadius: 6,
                animation: "pulse 1.5s ease-in-out infinite",
              }}
            />
          ))}
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          {searches.map((entry, idx) => (
            <button
              key={`${entry.query}-${idx}`}
              onClick={() => onSearchClick(entry.query)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "10px 12px",
                background: "transparent",
                border: "none",
                borderRadius: 6,
                cursor: "pointer",
                width: "100%",
                textAlign: "left",
                transition: "background 0.15s ease",
                fontFamily: "var(--font-body)",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLButtonElement).style.background =
                  "#f5f5f7";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLButtonElement).style.background =
                  "transparent";
              }}
            >
              <Clock size={14} style={{ color: "#8c8c9a", flexShrink: 0 }} />
              <span
                style={{
                  flex: 1,
                  fontSize: 14,
                  color: "#1a1a2e",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {entry.query}
              </span>
              <span style={{ fontSize: 12, color: "#8c8c9a", flexShrink: 0 }}>
                {entry.result_count} results
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
