"use client";

import { useEffect, useState, useMemo, useCallback, useRef } from "react";
import dynamic from "next/dynamic";
import { useRouter, useSearchParams } from "next/navigation";
import { List, Map } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { searchListings, getSearchHistory, toggleFavorite } from "@/lib/api/flask";
import { SearchBar } from "@/components/features/SearchBar";
import { SearchFilters } from "@/components/features/SearchFilters";
import { RecentSearches } from "@/components/features/RecentSearches";
import { ListingCard } from "@/components/features/ListingCard";
import { Pagination } from "@/components/features/Pagination";
import type { Listing } from "@/types/listing";
import type { SearchFilters as SearchFiltersType, SearchHistoryEntry } from "@/types/search";

const SearchMap = dynamic(
  () => import("@/components/features/SearchMap").then((mod) => mod.SearchMap),
  { ssr: false },
);

const ITEMS_PER_PAGE = 12;

const EXAMPLE_QUERIES = [
  "Affordable 2-bedroom near campus",
  "Pet-friendly apartments under $1200",
  "Studios close to Butler Plaza",
  "Luxury apartments with pool and gym",
  "Quiet neighborhoods near UF",
];

const defaultFilters: SearchFiltersType = {
  priceMin: null,
  priceMax: null,
  bedsMin: null,
  bathsMin: null,
  sqftMin: null,
  sqftMax: null,
};

function SkeletonCard() {
  return (
    <div
      style={{
        borderRadius: "var(--radius-lg)",
        border: "1px solid var(--color-border)",
        background: "var(--color-surface)",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          aspectRatio: "16/10",
          background: "var(--color-bg)",
          animation: "pulse 1.5s ease-in-out infinite",
        }}
      />
      <div style={{ padding: 16 }}>
        <div
          style={{
            height: 20,
            width: "60%",
            background: "var(--color-bg)",
            borderRadius: 4,
            marginBottom: 8,
            animation: "pulse 1.5s ease-in-out infinite",
          }}
        />
        <div
          style={{
            height: 14,
            width: "80%",
            background: "var(--color-bg)",
            borderRadius: 4,
            marginBottom: 8,
            animation: "pulse 1.5s ease-in-out infinite",
          }}
        />
        <div
          style={{
            height: 13,
            width: "50%",
            background: "var(--color-bg)",
            borderRadius: 4,
            animation: "pulse 1.5s ease-in-out infinite",
          }}
        />
      </div>
    </div>
  );
}

export function SearchView() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Search state
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [filters, setFilters] = useState<SearchFiltersType>(defaultFilters);

  // View state
  const [view, setView] = useState<"list" | "map">("list");
  const [page, setPage] = useState(1);

  // History
  const [searchHistory, setSearchHistory] = useState<SearchHistoryEntry[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);

  // Track if a search has ever been submitted
  const [hasSearched, setHasSearched] = useState(false);

  // Restore search from URL query param on mount
  const initialLoadDone = useRef(false);
  useEffect(() => {
    if (initialLoadDone.current) return;
    initialLoadDone.current = true;
    const q = searchParams.get("q");
    if (q) {
      setQuery(q);
      handleSearch(q, true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Fetch search history on mount
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const supabase = createClient();
        const {
          data: { session },
        } = await supabase.auth.getSession();
        if (!session?.access_token) return;

        const res = await getSearchHistory(session.access_token);
        setSearchHistory(res.data);
      } catch {
        // History is non-critical
      } finally {
        setHistoryLoading(false);
      }
    };
    fetchHistory();
  }, []);

  // Client-side filtering
  const filteredResults = useMemo(() => {
    return results.filter((listing) => {
      const { priceMin, priceMax, bedsMin, bathsMin, sqftMin, sqftMax } = filters;
      return (
        (priceMin === null || listing.list_price_max >= priceMin) &&
        (priceMax === null || listing.list_price_min <= priceMax) &&
        (bedsMin === null || listing.beds_max >= bedsMin) &&
        (bathsMin === null || listing.baths_max >= bathsMin) &&
        (sqftMin === null || listing.sqft_max >= sqftMin) &&
        (sqftMax === null || listing.sqft_min <= sqftMax)
      );
    });
  }, [results, filters]);

  // Paginated results for list view
  const paginatedResults = useMemo(() => {
    const start = (page - 1) * ITEMS_PER_PAGE;
    return filteredResults.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredResults, page]);

  const totalPages = Math.ceil(filteredResults.length / ITEMS_PER_PAGE);

  const handleSearch = useCallback(
    async (q: string, isRestore = false) => {
      setHasSearched(true);
      setLoading(true);
      setError(null);
      setQuery(q);

      // Sync query to URL so browser back preserves it
      if (!isRestore) {
        const params = new URLSearchParams();
        params.set("q", q);
        router.replace(`/search?${params.toString()}`);
      }

      try {
        const supabase = createClient();
        const {
          data: { session },
        } = await supabase.auth.getSession();
        if (!session?.access_token) {
          setError("Not authenticated");
          return;
        }

        const res = await searchListings(session.access_token, q);
        setResults(res.data);
        setFilters(defaultFilters);
        setPage(1);

        // Refresh history
        try {
          const historyRes = await getSearchHistory(session.access_token);
          setSearchHistory(historyRes.data);
        } catch {
          // Non-critical
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Search failed");
      } finally {
        setLoading(false);
      }
    },
    [router],
  );

  const handleFiltersChange = (newFilters: SearchFiltersType) => {
    setFilters(newFilters);
    setPage(1);
  };

  const handleFavoriteToggle = async (listingId: string) => {
    // Optimistic update
    setResults((prev) =>
      prev.map((l) => (l.listing_id === listingId ? { ...l, is_favorited: !l.is_favorited } : l)),
    );

    try {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session?.access_token) return;
      await toggleFavorite(session.access_token, listingId);
    } catch {
      // Revert on failure
      setResults((prev) =>
        prev.map((l) => (l.listing_id === listingId ? { ...l, is_favorited: !l.is_favorited } : l)),
      );
    }
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleListingClick = (listingId: string) => {
    router.push(`/listing/${listingId}`);
  };

  // Initial state, no searches
  if (!hasSearched) {
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
          <h1
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 32,
              fontWeight: 700,
              color: "#1a1a2e",
              letterSpacing: "-0.02em",
              textAlign: "center",
              marginBottom: 24,
            }}
          >
            Find Your Place
          </h1>

          <SearchBar value={query} onChange={setQuery} onSubmit={handleSearch} loading={loading} />

          {/* Example query pills */}
          <div
            style={{
              display: "flex",
              gap: 8,
              marginTop: 16,
              overflowX: "auto",
              paddingBottom: 4,
              scrollbarWidth: "none",
            }}
          >
            {EXAMPLE_QUERIES.map((eq) => (
              <button
                key={eq}
                onClick={() => {
                  setQuery(eq);
                  handleSearch(eq);
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

          {/* Recent searches */}
          <div style={{ marginTop: 32 }}>
            <RecentSearches
              searches={searchHistory}
              onSearchClick={(q) => {
                setQuery(q);
                handleSearch(q);
              }}
              loading={historyLoading}
            />
          </div>
        </div>
      </div>
    );
  }

  // After search aka results state
  return (
    <div style={{ padding: "0 0 40px" }}>
      {/* Top bar: compact search + view toggle */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          marginBottom: 16,
        }}
      >
        <div style={{ flex: 1 }}>
          <SearchBar
            value={query}
            onChange={setQuery}
            onSubmit={handleSearch}
            compact
            loading={loading}
          />
        </div>
        <div
          style={{
            display: "flex",
            border: "1px solid #e2e2e8",
            borderRadius: 6,
            overflow: "hidden",
          }}
        >
          <button
            onClick={() => setView("list")}
            style={{
              padding: "8px 12px",
              background: view === "list" ? "#4F3CC9" : "#fff",
              color: view === "list" ? "#fff" : "#8c8c9a",
              border: "none",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
            }}
            aria-label="List view"
          >
            <List size={16} />
          </button>
          <button
            onClick={() => setView("map")}
            style={{
              padding: "8px 12px",
              background: view === "map" ? "#4F3CC9" : "#fff",
              color: view === "map" ? "#fff" : "#8c8c9a",
              border: "none",
              borderLeft: "1px solid #e2e2e8",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
            }}
            aria-label="Map view"
          >
            <Map size={16} />
          </button>
        </div>
      </div>

      {/* Filters */}
      {results.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <SearchFilters
            filters={filters}
            onFiltersChange={handleFiltersChange}
            totalResults={results.length}
            filteredCount={filteredResults.length}
          />
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
            gap: 20,
          }}
        >
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div style={{ textAlign: "center", padding: "48px 24px" }}>
          <p
            style={{
              color: "#8c8c9a",
              fontSize: 15,
              marginBottom: 16,
              fontFamily: "var(--font-body)",
            }}
          >
            {error}
          </p>
          <button
            onClick={() => handleSearch(query)}
            style={{
              padding: "8px 20px",
              fontSize: 14,
              fontFamily: "var(--font-body)",
              fontWeight: 600,
              background: "#4F3CC9",
              color: "#fff",
              border: "none",
              borderRadius: 6,
              cursor: "pointer",
            }}
          >
            Try Again
          </button>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && filteredResults.length === 0 && hasSearched && (
        <div style={{ textAlign: "center", padding: "48px 24px" }}>
          <p
            style={{
              color: "#8c8c9a",
              fontSize: 15,
              fontFamily: "var(--font-body)",
            }}
          >
            No listings matched your search. Try adjusting your filters or searching for something
            else.
          </p>
        </div>
      )}

      {/* List view */}
      {!loading && !error && view === "list" && filteredResults.length > 0 && (
        <>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: 20,
            }}
          >
            {paginatedResults.map((listing) => (
              <ListingCard
                key={listing.listing_id}
                listing={listing}
                onFavoriteToggle={handleFavoriteToggle}
              />
            ))}
          </div>

          {totalPages > 1 && (
            <Pagination
              page={page}
              hasNext={page < totalPages}
              onPageChange={handlePageChange}
              total={filteredResults.length}
              perPage={ITEMS_PER_PAGE}
            />
          )}
        </>
      )}

      {/* Map view */}
      {!loading && !error && view === "map" && filteredResults.length > 0 && (
        <SearchMap listings={filteredResults} onListingClick={handleListingClick} />
      )}
    </div>
  );
}
