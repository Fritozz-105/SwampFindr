"use client";

import { useEffect, useState, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import { getRecommendations, toggleFavorite } from "@/lib/api/flask";
import { ListingCard } from "@/components/features/ListingCard";
import { Pagination } from "@/components/features/Pagination";
import { dashboard } from "@/data/dashboard";
import type { Listing, PaginationMeta } from "@/types/listing";

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

export function HomeFeed() {
  const [listings, setListings] = useState<Listing[]>([]);
  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState<PaginationMeta | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchListings = useCallback(async (p: number) => {
    setLoading(true);
    setError(null);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session?.access_token) {
        setError("Not authenticated");
        return;
      }

      const res = await getRecommendations(session.access_token, p, 12);
      setListings(res.data);
      setPagination(res.pagination);
    } catch (err) {
      setError(err instanceof Error ? err.message : dashboard.feed.error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchListings(page);
  }, [page, fetchListings]);

  const handleFavoriteToggle = async (listingId: string) => {
    // Optimistic update
    setListings((prev) =>
      prev.map((l) =>
        l.listing_id === listingId ? { ...l, is_favorited: !l.is_favorited } : l,
      ),
    );

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session?.access_token) return;
      await toggleFavorite(session.access_token, listingId);
    } catch {
      // Revert on failure
      setListings((prev) =>
        prev.map((l) =>
          l.listing_id === listingId ? { ...l, is_favorited: !l.is_favorited } : l,
        ),
      );
    }
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  if (error && listings.length === 0) {
    return (
      <div style={{ textAlign: "center", padding: "48px 24px" }}>
        <p
          style={{
            color: "var(--color-text-secondary)",
            fontSize: 15,
            marginBottom: 16,
          }}
        >
          {error}
        </p>
        <button
          onClick={() => fetchListings(page)}
          style={{
            padding: "8px 20px",
            fontSize: 14,
            fontFamily: "var(--font-display)",
            fontWeight: 600,
            background: "var(--color-primary)",
            color: "white",
            border: "none",
            borderRadius: "var(--radius-sm)",
            cursor: "pointer",
          }}
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Listing grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
          gap: 20,
        }}
      >
        {loading
          ? Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)
          : listings.map((listing) => (
              <ListingCard
                key={listing.listing_id}
                listing={listing}
                onFavoriteToggle={handleFavoriteToggle}
              />
            ))}
      </div>

      {/* Empty state */}
      {!loading && listings.length === 0 && (
        <div style={{ textAlign: "center", padding: "48px 24px" }}>
          <p style={{ color: "var(--color-text-secondary)", fontSize: 15 }}>
            {dashboard.feed.empty}
          </p>
        </div>
      )}

      {/* Pagination */}
      {pagination && listings.length > 0 && (
        <Pagination
          page={page}
          hasNext={pagination.has_next}
          onPageChange={handlePageChange}
          total={pagination.total}
        />
      )}
    </div>
  );
}
