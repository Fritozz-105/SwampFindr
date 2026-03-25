import type { Listing } from "./listing";

export interface SearchResponse {
  success: boolean;
  data: Listing[];
  query: string;
  total: number;
}

export interface SearchHistoryEntry {
  query: string;
  result_count: number;
  created_at: string;
}

export interface SearchHistoryResponse {
  success: boolean;
  data: SearchHistoryEntry[];
}

export interface SearchFilters {
  priceMin: number | null;
  priceMax: number | null;
  bedsMin: number | null;
  bathsMin: number | null;
  sqftMin: number | null;
  sqftMax: number | null;
}
