import type { RecommendationResponse, Listing } from "@/types/listing";
import type { SearchResponse, SearchHistoryResponse } from "@/types/search";
import type { SendMessageResponse, ThreadsResponse, ChatHistoryResponse } from "@/types/chat";

const FLASK_API_URL = process.env.NEXT_PUBLIC_FLASK_API_URL ?? "http://localhost:8080";

interface FlaskFetchOptions {
  token?: string;
  method?: string;
  body?: unknown;
}

async function flaskFetch<T>(path: string, options: FlaskFetchOptions = {}): Promise<T> {
  const { token, method = "GET", body } = options;

  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${FLASK_API_URL}/api/v1${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.error || `Request failed: ${res.status}`);
  }

  return data as T;
}

export async function getRecommendations(
  token: string,
  page: number,
  perPage: number,
): Promise<RecommendationResponse> {
  return flaskFetch<RecommendationResponse>(`/recommendations/?page=${page}&per_page=${perPage}`, {
    token,
  });
}

export async function toggleFavorite(
  token: string,
  listingId: string,
): Promise<{ success: boolean; action: string; favorites: string[] }> {
  return flaskFetch(`/profiles/me/favorites`, {
    token,
    method: "POST",
    body: { listing_id: listingId },
  });
}

export async function getListingDetail(
  listingId: string,
): Promise<{ success: boolean; data: Listing }> {
  return flaskFetch(`/listings/${listingId}`);
}

export async function searchListings(
  token: string,
  query: string,
  topK: number = 100,
  skipHistory: boolean = false,
): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query, top_k: String(topK) });
  if (skipHistory) params.set("skip_history", "1");
  return flaskFetch<SearchResponse>(`/search/?${params.toString()}`, { token });
}

export async function getSearchHistory(token: string): Promise<SearchHistoryResponse> {
  return flaskFetch<SearchHistoryResponse>("/search/history", { token });
}

export async function getFavoriteListings(
  token: string,
): Promise<{ success: boolean; data: Listing[]; count: number }> {
  return flaskFetch(`/profiles/me/favorites/listings`, { token });
}

export async function sendChatMessage(
  token: string,
  query: string,
  threadId?: string,
): Promise<SendMessageResponse> {
  const body: Record<string, string> = { query };
  if (threadId) body.thread_id = threadId;
  return flaskFetch<SendMessageResponse>("/chat/", {
    token,
    method: "POST",
    body,
  });
}

export async function getThreads(token: string): Promise<ThreadsResponse> {
  return flaskFetch<ThreadsResponse>("/profiles/threads", { token });
}

export async function getChatHistory(
  token: string,
  threadId: string,
): Promise<ChatHistoryResponse> {
  return flaskFetch<ChatHistoryResponse>(`/profiles/chathistory?thread_id=${threadId}`, { token });
}

export async function deleteThread(
  token: string,
  threadId: string,
): Promise<{ success: boolean }> {
  return flaskFetch(`/profiles/threads/${threadId}`, { token, method: "DELETE" });
}
