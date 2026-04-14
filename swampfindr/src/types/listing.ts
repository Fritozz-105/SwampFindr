export interface Unit {
  listing_id: string;
  property_id: string;
  availability: string | null;
  beds: number;
  baths: number;
  sqft: number | null;
  list_price: number | null;
}

export interface Listing {
  listing_id: string;
  property_id: string;
  list_price_max: number;
  list_price_min: number;
  beds_max: number;
  beds_min: number;
  baths_max: number;
  baths_min: number;
  sqft_max: number;
  sqft_min: number;
  address: string;
  postal_code: string;
  city: string;
  state: string;
  cats: boolean | null;
  dogs: boolean | null;
  photos: string[];
  cleaned_photos?: string[];
  details: string;
  units: Unit[];
  match_score: number | null;
  is_favorited: boolean;
  latitude: number | null;
  longitude: number | null;
}

export interface PaginationMeta {
  page: number;
  per_page: number;
  total: number;
  has_next: boolean;
}

export interface RecommendationResponse {
  success: boolean;
  data: Listing[];
  pagination: PaginationMeta;
  source: "pinecone" | "fallback";
}
