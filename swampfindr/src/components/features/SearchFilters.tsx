"use client";

import { useState, useRef, useEffect } from "react";
import type { SearchFilters as SearchFiltersType } from "@/types/search";
import {
  pillStyle,
  dropdownStyle,
  inputStyle,
  optionBtnStyle,
  getPriceLabel,
  getBedsLabel,
  getBathsLabel,
  getSqftLabel,
} from "./searchFilterUtils";

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

  return (
    <div
      ref={containerRef}
      className="search-filters-bar"
    >
      {/* Price pill */}
      <div style={{ position: "relative" }}>
        <button
          onClick={() =>
            setOpenDropdown(openDropdown === "price" ? null : "price")
          }
          style={pillStyle(filters.priceMin !== null || filters.priceMax !== null)}
        >
          {getPriceLabel(filters)}
        </button>
        {openDropdown === "price" && (
          <div className="search-filter-dropdown" style={dropdownStyle}>
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
                  const val = e.target.value ? Number(e.target.value) : null;
                  onFiltersChange({ ...filters, priceMin: val });
                }}
                onBlur={() => {
                  const min = filters.priceMin !== null ? Math.max(0, filters.priceMin) : null;
                  const max = min !== null && filters.priceMax !== null && filters.priceMax < min ? min : filters.priceMax;
                  onFiltersChange({ ...filters, priceMin: min, priceMax: max });
                }}
                style={inputStyle}
              />
              <span style={{ fontSize: 13, color: "#8c8c9a" }}>{"\u2013"}</span>
              <span style={{ fontSize: 13, color: "#8c8c9a" }}>$</span>
              <input
                type="number"
                placeholder="Max"
                min={0}
                value={filters.priceMax ?? ""}
                onChange={(e) => {
                  const val = e.target.value ? Number(e.target.value) : null;
                  onFiltersChange({ ...filters, priceMax: val });
                }}
                onBlur={() => {
                  let max = filters.priceMax !== null ? Math.max(0, filters.priceMax) : null;
                  if (max !== null && filters.priceMin !== null && max < filters.priceMin) max = filters.priceMin;
                  onFiltersChange({ ...filters, priceMax: max });
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
          {getBedsLabel(filters)}
        </button>
        {openDropdown === "beds" && (
          <div className="search-filter-dropdown" style={dropdownStyle}>
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
          {getBathsLabel(filters)}
        </button>
        {openDropdown === "baths" && (
          <div className="search-filter-dropdown" style={dropdownStyle}>
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
          {getSqftLabel(filters)}
        </button>
        {openDropdown === "sqft" && (
          <div className="search-filter-dropdown" style={dropdownStyle}>
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
                  const val = e.target.value ? Number(e.target.value) : null;
                  onFiltersChange({ ...filters, sqftMin: val });
                }}
                onBlur={() => {
                  const min = filters.sqftMin !== null ? Math.max(0, filters.sqftMin) : null;
                  const max = min !== null && filters.sqftMax !== null && filters.sqftMax < min ? min : filters.sqftMax;
                  onFiltersChange({ ...filters, sqftMin: min, sqftMax: max });
                }}
                style={inputStyle}
              />
              <span style={{ fontSize: 13, color: "#8c8c9a" }}>{"\u2013"}</span>
              <input
                type="number"
                placeholder="Max"
                min={0}
                value={filters.sqftMax ?? ""}
                onChange={(e) => {
                  const val = e.target.value ? Number(e.target.value) : null;
                  onFiltersChange({ ...filters, sqftMax: val });
                }}
                onBlur={() => {
                  let max = filters.sqftMax !== null ? Math.max(0, filters.sqftMax) : null;
                  if (max !== null && filters.sqftMin !== null && max < filters.sqftMin) max = filters.sqftMin;
                  onFiltersChange({ ...filters, sqftMax: max });
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
        className="search-result-count"
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
