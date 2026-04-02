"use client";

import Image from "next/image";
import { Heart } from "lucide-react";
import type { Listing } from "@/types/listing";

interface ChatListingCardProps {
  listing: Listing;
  onViewDetails: () => void;
  onFavoriteToggle: () => void;
}

function formatPrice(min: number, max: number): string {
  const fmt = (n: number) =>
    "$" + n.toLocaleString("en-US", { maximumFractionDigits: 0 });
  return min === max ? fmt(min) : `${fmt(min)}–${fmt(max)}`;
}

export function ChatListingCard({
  listing,
  onViewDetails,
  onFavoriteToggle,
}: ChatListingCardProps) {
  return (
    <div
      style={{
        background: "var(--color-surface)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-md)",
        padding: 12,
        display: "flex",
        gap: 12,
        alignItems: "center",
      }}
    >
      {/* Thumbnail */}
      <div
        style={{
          width: 72,
          height: 54,
          borderRadius: "var(--radius-sm)",
          background: "var(--color-bg)",
          flexShrink: 0,
          overflow: "hidden",
          position: "relative",
        }}
      >
        {listing.photos.length > 0 ? (
          <Image
            src={listing.photos[0]}
            alt={listing.address}
            fill
            style={{ objectFit: "cover" }}
            sizes="72px"
          />
        ) : (
          <div
            style={{
              width: "100%",
              height: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 11,
              color: "var(--color-text-muted)",
            }}
          >
            No photo
          </div>
        )}
      </div>

      {/* Details */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontFamily: "var(--font-display)",
            fontWeight: 600,
            fontSize: 13,
            color: "var(--color-text)",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {listing.address}
        </div>
        <div
          style={{
            fontSize: 13,
            color: "var(--color-text-secondary)",
            marginTop: 2,
          }}
        >
          {formatPrice(listing.list_price_min, listing.list_price_max)} ·{" "}
          {listing.beds_min}
          {listing.beds_min !== listing.beds_max
            ? `–${listing.beds_max}`
            : ""}{" "}
          bd · {listing.baths_min}
          {listing.baths_min !== listing.baths_max
            ? `–${listing.baths_max}`
            : ""}{" "}
          ba
        </div>
        {listing.match_score != null && (
          <span
            style={{
              display: "inline-block",
              marginTop: 4,
              fontSize: 11,
              fontWeight: 500,
              letterSpacing: "0.02em",
              padding: "2px 6px",
              borderRadius: "var(--radius-sm)",
              background: "var(--color-primary-subtle)",
              color: "var(--color-primary)",
              textTransform: "uppercase",
            }}
          >
            {Math.round(listing.match_score * 100)}% match
          </span>
        )}
      </div>

      {/* Actions */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 8,
          alignItems: "center",
          flexShrink: 0,
        }}
      >
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onFavoriteToggle();
          }}
          style={{
            width: 28,
            height: 28,
            borderRadius: "var(--radius-sm)",
            border: "1px solid var(--color-border)",
            background: "var(--color-surface)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            color: listing.is_favorited
              ? "var(--color-error)"
              : "var(--color-text-muted)",
          }}
        >
          <Heart
            size={14}
            fill={listing.is_favorited ? "currentColor" : "none"}
            strokeWidth={1.5}
          />
        </button>
        <button
          onClick={onViewDetails}
          style={{
            fontSize: 11,
            fontWeight: 600,
            fontFamily: "var(--font-display)",
            padding: "4px 8px",
            borderRadius: "var(--radius-sm)",
            background: "var(--color-primary)",
            color: "#fff",
            border: "none",
            cursor: "pointer",
            whiteSpace: "nowrap",
          }}
        >
          View Details
        </button>
      </div>
    </div>
  );
}
