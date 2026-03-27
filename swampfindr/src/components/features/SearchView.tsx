"use client";

import dynamic from "next/dynamic";
import { List, Map } from "lucide-react";
import { useSearch } from "@/hooks/useSearch";
import { SearchBar } from "@/components/features/SearchBar";
import { SearchFilters } from "@/components/features/SearchFilters";
import { ListingCard } from "@/components/features/ListingCard";
import { Pagination } from "@/components/features/Pagination";
import { SkeletonCard } from "@/components/features/SkeletonCard";
import { SearchLanding } from "@/components/features/SearchLanding";

const SearchMap = dynamic(
  () => import("@/components/features/SearchMap").then((mod) => mod.SearchMap),
  { ssr: false },
);

export function SearchView() {
  const {
    query,
    setQuery,
    results,
    loading,
    error,
    filters,
    view,
    setView,
    page,
    searchHistory,
    historyLoading,
    hasSearched,
    filteredResults,
    paginatedResults,
    totalPages,
    handleSearch,
    handleFiltersChange,
    handleFavoriteToggle,
    handlePageChange,
    handleListingClick,
    ITEMS_PER_PAGE,
  } = useSearch();

  if (!hasSearched) {
    return (
      <SearchLanding
        query={query}
        onQueryChange={setQuery}
        onSearch={handleSearch}
        loading={loading}
        searchHistory={searchHistory}
        historyLoading={historyLoading}
      />
    );
  }

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
        <div className="search-grid">
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
          <div className="search-grid">
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
