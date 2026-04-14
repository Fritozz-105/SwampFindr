"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { Heart, ArrowRight, Bed, Bath, Maximize } from "lucide-react";
import type { Listing } from "@/types/listing";
import { getListingPhotos } from "@/lib/utils/listing-photos";

interface ListingCardProps {
  listing: Listing;
  onFavoriteToggle: (listingId: string) => void;
  basePath?: string;
}

export function ListingCard({ listing, onFavoriteToggle, basePath = "/home" }: ListingCardProps) {
  const [hovered, setHovered] = useState(false);
  const photos = getListingPhotos(listing);
  const hasPhoto = photos.length > 0;
  const matchPercent = listing.match_score != null ? Math.round(listing.match_score * 100) : null;

  const priceLabel =
    listing.list_price_min === listing.list_price_max
      ? `$${listing.list_price_min.toLocaleString()}`
      : `$${listing.list_price_min.toLocaleString()} – $${listing.list_price_max.toLocaleString()}`;

  const bedsLabel =
    listing.beds_min === listing.beds_max
      ? `${listing.beds_min}`
      : `${listing.beds_min}–${listing.beds_max}`;

  const bathsLabel =
    listing.baths_min === listing.baths_max
      ? `${listing.baths_min}`
      : `${listing.baths_min}–${listing.baths_max}`;

  const sqftLabel =
    listing.sqft_min === listing.sqft_max
      ? `${listing.sqft_min.toLocaleString()}`
      : `${listing.sqft_min.toLocaleString()}–${listing.sqft_max.toLocaleString()}`;

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        position: "relative",
        borderRadius: 16,
        overflow: "hidden",
        transform: hovered ? "scale(1.02)" : "scale(1)",
        boxShadow: hovered
          ? "0 0 50px -15px rgba(79, 60, 201, 0.4)"
          : "0 0 30px -15px rgba(79, 60, 201, 0.2)",
        transition: "transform 0.5s ease, box-shadow 0.5s ease",
      }}
    >
      {/* Background image */}
      {hasPhoto ? (
        <Image
          src={photos[0]}
          alt={listing.address}
          fill
          sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
          style={{
            objectFit: "cover",
            transform: hovered ? "scale(1.08)" : "scale(1)",
            transition: "transform 0.5s ease",
          }}
        />
      ) : (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: "linear-gradient(135deg, var(--color-primary), var(--color-accent))",
          }}
        />
      )}

      {/* Gradient overlay */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(to top, rgba(30, 20, 60, 0.92), rgba(30, 20, 60, 0.45) 45%, transparent 75%)",
        }}
      />

      {/* Top row: favorite + match badge */}
      <div
        style={{
          position: "absolute",
          top: 12,
          left: 12,
          right: 12,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          zIndex: 2,
        }}
      >
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onFavoriteToggle(listing.listing_id);
          }}
          style={{
            width: 36,
            height: 36,
            borderRadius: "50%",
            border: "none",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            background: listing.is_favorited ? "rgba(239, 68, 68, 0.9)" : "rgba(255,255,255,0.4)",
            backdropFilter: "blur(8px)",
            color: "white",
            transition: "background 0.2s",
          }}
          aria-label={listing.is_favorited ? "Remove from favorites" : "Add to favorites"}
        >
          <Heart size={18} fill={listing.is_favorited ? "currentColor" : "none"} />
        </button>

        {matchPercent !== null && (
          <div
            style={{
              padding: "4px 12px",
              borderRadius: 20,
              fontSize: 12,
              fontWeight: 700,
              letterSpacing: "0.02em",
              backdropFilter: "blur(8px)",
              background: "rgba(79, 60, 201, 0.45)",
              border: "1px solid rgba(79, 60, 201, 0.5)",
              color: "white",
            }}
          >
            {matchPercent}% match
          </div>
        )}
      </div>

      {/* Content overlay */}
      <Link
        href={`${basePath}/${listing.listing_id}`}
        className="listing-card-link"
        style={{
          position: "relative",
          display: "flex",
          flexDirection: "column",
          justifyContent: "flex-end",
          height: "100%",
          padding: 20,
          color: "white",
          textDecoration: "none",
          zIndex: 1,
        }}
      >
        {/* Price */}
        <div
          style={{
            fontSize: 24,
            fontWeight: 700,
            fontFamily: "var(--font-display)",
            letterSpacing: "-0.02em",
          }}
        >
          {priceLabel}
          <span style={{ fontSize: 14, fontWeight: 400, opacity: 0.7, marginLeft: 4 }}>/mo</span>
        </div>

        {/* Details row */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 16,
            marginTop: 6,
            fontSize: 14,
            color: "rgba(255,255,255,0.8)",
          }}
        >
          <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <Bed size={14} /> {bedsLabel} bd
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <Bath size={14} /> {bathsLabel} ba
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <Maximize size={14} /> {sqftLabel}
          </span>
        </div>

        {/* Address */}
        <div
          style={{
            fontSize: 12,
            color: "rgba(255,255,255,0.55)",
            marginTop: 4,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {listing.address}, {listing.city}, {listing.state}
        </div>

        {/* View Details bar */}
        <div
          style={{
            marginTop: 16,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            backdropFilter: "blur(8px)",
            borderRadius: 8,
            padding: "10px 16px",
            background: hovered ? "rgba(79, 60, 201, 0.35)" : "rgba(79, 60, 201, 0.2)",
            borderWidth: 1,
            borderStyle: "solid",
            borderColor: hovered ? "rgba(79, 60, 201, 0.5)" : "rgba(79, 60, 201, 0.3)",
            transition: "background 0.3s, border-color 0.3s",
          }}
        >
          <span style={{ fontSize: 14, fontWeight: 600, letterSpacing: "0.02em" }}>
            View Details
          </span>
          <ArrowRight
            size={16}
            style={{
              transform: hovered ? "translateX(4px)" : "translateX(0)",
              transition: "transform 0.3s",
            }}
          />
        </div>
      </Link>
    </div>
  );
}
