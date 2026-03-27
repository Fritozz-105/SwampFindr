import type { SearchFilters } from "@/types/search";

export const pillStyle = (active: boolean): React.CSSProperties => ({
  padding: "6px 14px",
  fontSize: 13,
  fontWeight: 500,
  fontFamily: "var(--font-body)",
  border: active ? "1px solid #4F3CC9" : "1px solid #e2e2e8",
  borderRadius: 6,
  background: active ? "rgba(79, 60, 201, 0.06)" : "#fff",
  color: active ? "#4F3CC9" : "#1a1a2e",
  cursor: "pointer",
  transition: "all 0.15s ease",
  position: "relative" as const,
});

export const dropdownStyle: React.CSSProperties = {
  position: "absolute",
  top: "calc(100% + 6px)",
  left: 0,
  background: "#fff",
  border: "1px solid #e2e2e8",
  borderRadius: 8,
  padding: 16,
  boxShadow: "0 4px 16px rgba(0,0,0,0.08)",
  zIndex: 50,
  minWidth: 200,
};

export const inputStyle: React.CSSProperties = {
  width: 90,
  padding: "6px 8px",
  border: "1px solid #e2e2e8",
  borderRadius: 4,
  fontSize: 13,
  fontFamily: "var(--font-body)",
  outline: "none",
};

export const optionBtnStyle = (active: boolean): React.CSSProperties => ({
  padding: "6px 12px",
  border: active ? "1px solid #4F3CC9" : "1px solid #e2e2e8",
  borderRadius: 4,
  background: active ? "#4F3CC9" : "#fff",
  color: active ? "#fff" : "#1a1a2e",
  fontSize: 13,
  fontFamily: "var(--font-body)",
  cursor: "pointer",
  transition: "all 0.15s ease",
});

export function getPriceLabel(filters: SearchFilters) {
  if (filters.priceMin !== null && filters.priceMax !== null)
    return `$${filters.priceMin}\u2013$${filters.priceMax}`;
  if (filters.priceMin !== null) return `$${filters.priceMin}+`;
  if (filters.priceMax !== null) return `Up to $${filters.priceMax}`;
  return "Price";
}

export function getBedsLabel(filters: SearchFilters) {
  if (filters.bedsMin !== null) return `${filters.bedsMin}+ Beds`;
  return "Beds";
}

export function getBathsLabel(filters: SearchFilters) {
  if (filters.bathsMin !== null) return `${filters.bathsMin}+ Baths`;
  return "Baths";
}

export function getSqftLabel(filters: SearchFilters) {
  if (filters.sqftMin !== null && filters.sqftMax !== null)
    return `${filters.sqftMin}\u2013${filters.sqftMax} sqft`;
  if (filters.sqftMin !== null) return `${filters.sqftMin}+ sqft`;
  if (filters.sqftMax !== null) return `Up to ${filters.sqftMax} sqft`;
  return "Sqft";
}
