import type { RecommendationResponse, Listing } from "@/types/listing";

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
