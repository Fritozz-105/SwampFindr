"use client";

import { useEffect, useState, useMemo, useCallback, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { searchListings, getSearchHistory, toggleFavorite } from "@/lib/api/flask";
import type { Listing } from "@/types/listing";
import type { SearchFilters as SearchFiltersType, SearchHistoryEntry } from "@/types/search";

const ITEMS_PER_PAGE = 12;

const defaultFilters: SearchFiltersType = {
  priceMin: null,
  priceMax: null,
  bedsMin: null,
  bathsMin: null,
  sqftMin: null,
  sqftMax: null,
};

export function useSearch() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<SearchFiltersType>(defaultFilters);
  const [view, setView] = useState<"list" | "map">("list");
  const [page, setPage] = useState(1);
  const [searchHistory, setSearchHistory] = useState<SearchHistoryEntry[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [hasSearched, setHasSearched] = useState(false);

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

        const res = await searchListings(session.access_token, q, 50, isRestore);
        setResults(res.data);
        setFilters(defaultFilters);
        setPage(1);

        if (!isRestore) {
          try {
            const historyRes = await getSearchHistory(session.access_token);
            setSearchHistory(historyRes.data);
          } catch {
            // Non-critical
          }
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
    router.push(`/home/${listingId}`);
  };

  return {
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
  };
}
