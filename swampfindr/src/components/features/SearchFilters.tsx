"use client";

import { useState, useRef, useEffect } from "react";
import type { SearchFilters as SearchFiltersType } from "@/types/search";

interface SearchFiltersProps {
  filters: SearchFiltersType;
  onFiltersChange: (filters: SearchFiltersType) => void;
  totalResults: number;
  filteredCount: number;
}

type FilterKey = "price" | "beds" | "baths" | "sqft";

export function SearchFilters({
  filters,
  onFiltersChange,
  totalResults,
  filteredCount,
}: SearchFiltersProps) {
  const [openDropdown, setOpenDropdown] = useState<FilterKey | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpenDropdown(null);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const hasActiveFilters =
    filters.priceMin !== null ||
    filters.priceMax !== null ||
    filters.bedsMin !== null ||
    filters.bathsMin !== null ||
    filters.sqftMin !== null ||
    filters.sqftMax !== null;

  const pillStyle = (active: boolean): React.CSSProperties => ({
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

  const dropdownStyle: React.CSSProperties = {
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

  const inputStyle: React.CSSProperties = {
    width: 90,
    padding: "6px 8px",
    border: "1px solid #e2e2e8",
    borderRadius: 4,
    fontSize: 13,
    fontFamily: "var(--font-body)",
    outline: "none",
  };

  const optionBtnStyle = (active: boolean): React.CSSProperties => ({
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

  const getPriceLabel = () => {
    if (filters.priceMin !== null && filters.priceMax !== null)
      return `$${filters.priceMin}–$${filters.priceMax}`;
    if (filters.priceMin !== null) return `$${filters.priceMin}+`;
    if (filters.priceMax !== null) return `Up to $${filters.priceMax}`;
    return "Price";
  };

  const getBedsLabel = () => {
    if (filters.bedsMin !== null) return `${filters.bedsMin}+ Beds`;
    return "Beds";
  };

  const getBathsLabel = () => {
    if (filters.bathsMin !== null) return `${filters.bathsMin}+ Baths`;
    return "Baths";
  };

  const getSqftLabel = () => {
    if (filters.sqftMin !== null && filters.sqftMax !== null)
      return `${filters.sqftMin}–${filters.sqftMax} sqft`;
    if (filters.sqftMin !== null) return `${filters.sqftMin}+ sqft`;
    if (filters.sqftMax !== null) return `Up to ${filters.sqftMax} sqft`;
    return "Sqft";
  };

  return (
    <div
      ref={containerRef}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        flexWrap: "wrap",
      }}
    >
      {/* Price pill */}
      <div style={{ position: "relative" }}>
        <button
          onClick={() =>
            setOpenDropdown(openDropdown === "price" ? null : "price")
          }
          style={pillStyle(filters.priceMin !== null || filters.priceMax !== null)}
        >
          {getPriceLabel()}
        </button>
        {openDropdown === "price" && (
          <div style={dropdownStyle}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <span style={{ fontSize: 13, color: "#8c8c9a" }}>$</span>
              <input
                type="number"
                placeholder="Min"
                min={0}
                value={filters.priceMin ?? ""}
                onChange={(e) => {
                  const val = e.target.value ? Math.max(0, Number(e.target.value)) : null;
                  onFiltersChange({
                    ...filters,
                    priceMin: val,
                    priceMax: val !== null && filters.priceMax !== null && filters.priceMax < val ? val : filters.priceMax,
                  });
                }}
                style={inputStyle}
              />
              <span style={{ fontSize: 13, color: "#8c8c9a" }}>–</span>
              <span style={{ fontSize: 13, color: "#8c8c9a" }}>$</span>
              <input
                type="number"
                placeholder="Max"
                min={filters.priceMin ?? 0}
                value={filters.priceMax ?? ""}
                onChange={(e) => {
                  const val = e.target.value ? Math.max(filters.priceMin ?? 0, Number(e.target.value)) : null;
                  onFiltersChange({
                    ...filters,
                    priceMax: val,
                  });
                }}
                style={inputStyle}
              />
            </div>
          </div>
        )}
      </div>

      {/* Beds pill */}
      <div style={{ position: "relative" }}>
        <button
          onClick={() =>
            setOpenDropdown(openDropdown === "beds" ? null : "beds")
          }
          style={pillStyle(filters.bedsMin !== null)}
        >
          {getBedsLabel()}
        </button>
        {openDropdown === "beds" && (
          <div style={dropdownStyle}>
            <div style={{ display: "flex", gap: 6 }}>
              {[
                { label: "Any", value: null },
                { label: "1+", value: 1 },
                { label: "2+", value: 2 },
                { label: "3+", value: 3 },
                { label: "4+", value: 4 },
              ].map((opt) => (
                <button
                  key={opt.label}
                  onClick={() =>
                    onFiltersChange({ ...filters, bedsMin: opt.value })
                  }
                  style={optionBtnStyle(filters.bedsMin === opt.value)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Baths pill */}
      <div style={{ position: "relative" }}>
        <button
          onClick={() =>
            setOpenDropdown(openDropdown === "baths" ? null : "baths")
          }
          style={pillStyle(filters.bathsMin !== null)}
        >
          {getBathsLabel()}
        </button>
        {openDropdown === "baths" && (
          <div style={dropdownStyle}>
            <div style={{ display: "flex", gap: 6 }}>
              {[
                { label: "Any", value: null },
                { label: "1+", value: 1 },
                { label: "2+", value: 2 },
                { label: "3+", value: 3 },
              ].map((opt) => (
                <button
                  key={opt.label}
                  onClick={() =>
                    onFiltersChange({ ...filters, bathsMin: opt.value })
                  }
                  style={optionBtnStyle(filters.bathsMin === opt.value)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Sqft pill */}
      <div style={{ position: "relative" }}>
        <button
          onClick={() =>
            setOpenDropdown(openDropdown === "sqft" ? null : "sqft")
          }
          style={pillStyle(filters.sqftMin !== null || filters.sqftMax !== null)}
        >
          {getSqftLabel()}
        </button>
        {openDropdown === "sqft" && (
          <div style={dropdownStyle}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <input
                type="number"
                placeholder="Min"
                min={0}
                value={filters.sqftMin ?? ""}
                onChange={(e) => {
                  const val = e.target.value ? Math.max(0, Number(e.target.value)) : null;
                  onFiltersChange({
                    ...filters,
                    sqftMin: val,
                    sqftMax: val !== null && filters.sqftMax !== null && filters.sqftMax < val ? val : filters.sqftMax,
                  });
                }}
                style={inputStyle}
              />
              <span style={{ fontSize: 13, color: "#8c8c9a" }}>–</span>
              <input
                type="number"
                placeholder="Max"
                min={filters.sqftMin ?? 0}
                value={filters.sqftMax ?? ""}
                onChange={(e) => {
                  const val = e.target.value ? Math.max(filters.sqftMin ?? 0, Number(e.target.value)) : null;
                  onFiltersChange({
                    ...filters,
                    sqftMax: val,
                  });
                }}
                style={inputStyle}
              />
              <span style={{ fontSize: 12, color: "#8c8c9a" }}>sqft</span>
            </div>
          </div>
        )}
      </div>

      {/* Result count */}
      <div
        style={{
          marginLeft: "auto",
          fontSize: 13,
          color: "#8c8c9a",
          fontFamily: "var(--font-body)",
        }}
      >
        {hasActiveFilters
          ? `${filteredCount} of ${totalResults} results`
          : `${totalResults} results`}
      </div>
    </div>
  );
}
