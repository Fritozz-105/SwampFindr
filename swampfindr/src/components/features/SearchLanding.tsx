"use client";

import { SearchBar } from "@/components/features/SearchBar";
import { RecentSearches } from "@/components/features/RecentSearches";
import type { SearchHistoryEntry } from "@/types/search";

const EXAMPLE_QUERIES = [
  "Affordable 2-bedroom near campus",
  "Pet-friendly apartments under $1200",
  "Studios close to Butler Plaza",
  "Luxury apartments with pool and gym",
  "Quiet neighborhoods near UF",
];

interface SearchLandingProps {
  query: string;
  onQueryChange: (q: string) => void;
  onSearch: (q: string) => void;
  loading: boolean;
  searchHistory: SearchHistoryEntry[];
  historyLoading: boolean;
}

export function SearchLanding({
  query,
  onQueryChange,
  onSearch,
  loading,
  searchHistory,
  historyLoading,
}: SearchLandingProps) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "calc(100vh - 120px)",
        padding: "0 24px",
      }}
    >
      <div style={{ width: "100%", maxWidth: 640 }}>
        <h1 className="search-landing-heading">
          Find Your Place
        </h1>

        <SearchBar value={query} onChange={onQueryChange} onSubmit={onSearch} loading={loading} />

        <div className="search-chips">
          {EXAMPLE_QUERIES.map((eq) => (
            <button
              key={eq}
              onClick={() => {
                onQueryChange(eq);
                onSearch(eq);
              }}
              style={{
                padding: "6px 14px",
                fontSize: 13,
                fontFamily: "var(--font-body)",
                color: "#4F3CC9",
                background: "rgba(79, 60, 201, 0.06)",
                border: "1px solid rgba(79, 60, 201, 0.15)",
                borderRadius: 20,
                cursor: "pointer",
                whiteSpace: "nowrap",
                transition: "background 0.15s ease",
                flexShrink: 0,
              }}
            >
              {eq}
            </button>
          ))}
        </div>

        <div style={{ marginTop: 32 }}>
          <RecentSearches
            searches={searchHistory}
            onSearchClick={(q) => {
              onQueryChange(q);
              onSearch(q);
            }}
            loading={historyLoading}
          />
        </div>
      </div>
    </div>
  );
}
