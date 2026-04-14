"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { X, Heart, ChevronLeft, ChevronRight } from "lucide-react";
import type { Listing } from "@/types/listing";
import { getListingPhotos } from "@/lib/utils/listing-photos";

interface ListingDetailPopupProps {
  listing: Listing;
  onClose: () => void;
  onFavoriteToggle: (listingId: string) => void;
}

function formatPrice(n: number): string {
  return "$" + n.toLocaleString("en-US", { maximumFractionDigits: 0 });
}

export function ListingDetailPopup({
  listing,
  onClose,
  onFavoriteToggle,
}: ListingDetailPopupProps) {
  const router = useRouter();
  const [photoIndex, setPhotoIndex] = useState(0);

  const handleBackdropClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget) onClose();
    },
    [onClose],
  );

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [onClose]);

  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "";
    };
  }, []);

  const hasPhotos = getListingPhotos(listing).length > 0;
  const hasMultiplePhotos = getListingPhotos(listing).length > 1;

  return (
    <div
      onClick={handleBackdropClick}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0, 0, 0, 0.5)",
        zIndex: 1000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
      }}
    >
      <div
        style={{
          background: "var(--color-surface)",
          borderRadius: "var(--radius-lg)",
          width: "100%",
          maxWidth: 440,
          maxHeight: "85vh",
          overflowY: "auto",
          boxShadow: "var(--shadow-lg)",
        }}
      >
        {/* Photo area */}
        <div
          style={{
            height: 180,
            background: "var(--color-bg)",
            position: "relative",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {hasPhotos ? (
            <Image
              src={getListingPhotos(listing)[photoIndex]}
              alt={listing.address}
              fill
              style={{ objectFit: "cover" }}
              sizes="440px"
            />
          ) : (
            <span
              style={{ color: "var(--color-text-muted)", fontSize: 13 }}
            >
              No photos available
            </span>
          )}

          {/* Close button */}
          <button
            onClick={onClose}
            style={{
              position: "absolute",
              top: 12,
              right: 12,
              width: 28,
              height: 28,
              borderRadius: "var(--radius-sm)",
              background: "rgba(0, 0, 0, 0.5)",
              color: "#fff",
              border: "none",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <X size={14} strokeWidth={1.5} />
          </button>

          {/* Favorite button */}
          <button
            onClick={() => onFavoriteToggle(listing.listing_id)}
            style={{
              position: "absolute",
              top: 12,
              left: 12,
              width: 28,
              height: 28,
              borderRadius: "var(--radius-sm)",
              background: "rgba(0, 0, 0, 0.5)",
              color: listing.is_favorited ? "var(--color-error)" : "#fff",
              border: "none",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Heart
              size={14}
              fill={listing.is_favorited ? "currentColor" : "none"}
              strokeWidth={1.5}
            />
          </button>

          {/* Match badge */}
          {listing.match_score != null && (
            <div
              style={{
                position: "absolute",
                bottom: 12,
                right: 12,
                padding: "2px 6px",
                borderRadius: "var(--radius-sm)",
                background: "var(--color-primary)",
                color: "#fff",
                fontSize: 11,
                fontWeight: 500,
                letterSpacing: "0.02em",
                textTransform: "uppercase",
              }}
            >
              {Math.round(listing.match_score * 100)}% match
            </div>
          )}

          {/* Photo nav arrows */}
          {hasMultiplePhotos && (
            <>
              <button
                onClick={() =>
                  setPhotoIndex((i) =>
                    i === 0 ? getListingPhotos(listing).length - 1 : i - 1,
                  )
                }
                style={{
                  position: "absolute",
                  left: 8,
                  top: "50%",
                  transform: "translateY(-50%)",
                  width: 28,
                  height: 28,
                  borderRadius: "var(--radius-sm)",
                  background: "rgba(0, 0, 0, 0.5)",
                  color: "#fff",
                  border: "none",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <ChevronLeft size={16} strokeWidth={1.5} />
              </button>
              <button
                onClick={() =>
                  setPhotoIndex((i) =>
                    i === getListingPhotos(listing).length - 1 ? 0 : i + 1,
                  )
                }
                style={{
                  position: "absolute",
                  right: 8,
                  top: "50%",
                  transform: "translateY(-50%)",
                  width: 28,
                  height: 28,
                  borderRadius: "var(--radius-sm)",
                  background: "rgba(0, 0, 0, 0.5)",
                  color: "#fff",
                  border: "none",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <ChevronRight size={16} strokeWidth={1.5} />
              </button>
            </>
          )}

          {/* Dots */}
          {hasMultiplePhotos && (
            <div
              style={{
                position: "absolute",
                bottom: 12,
                left: "50%",
                transform: "translateX(-50%)",
                display: "flex",
                gap: 4,
              }}
            >
              {getListingPhotos(listing).slice(0, 5).map((_, i) => (
                <div
                  key={i}
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background:
                      i === photoIndex
                        ? "#FFFFFF"
                        : "rgba(255, 255, 255, 0.4)",
                  }}
                />
              ))}
            </div>
          )}
        </div>

        {/* Content */}
        <div style={{ padding: 16 }}>
          {/* Title */}
          <div
            style={{
              fontFamily: "var(--font-display)",
              fontWeight: 700,
              fontSize: 18,
              letterSpacing: "-0.01em",
              color: "var(--color-text)",
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
            {listing.city}, {listing.state} {listing.postal_code}
          </div>

          {/* Price */}
          <div style={{ marginTop: 12 }}>
            <span
              style={{
                fontFamily: "var(--font-display)",
                fontWeight: 700,
                fontSize: 24,
                letterSpacing: "-0.015em",
                color: "var(--color-primary)",
              }}
            >
              {formatPrice(listing.list_price_min)}
              {listing.list_price_min !== listing.list_price_max &&
                ` – ${formatPrice(listing.list_price_max)}`}
            </span>
            <span
              style={{
                fontSize: 13,
                color: "var(--color-text-secondary)",
                fontFamily: "var(--font-body)",
              }}
            >
              /mo
            </span>
          </div>

          {/* Stats grid */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: 8,
              marginTop: 12,
            }}
          >
            {[
              {
                value: listing.beds_min === listing.beds_max
                  ? listing.beds_min
                  : `${listing.beds_min}–${listing.beds_max}`,
                label: "BEDS",
              },
              {
                value: listing.baths_min === listing.baths_max
                  ? listing.baths_min
                  : `${listing.baths_min}–${listing.baths_max}`,
                label: "BATHS",
              },
              {
                value: listing.sqft_min === listing.sqft_max
                  ? listing.sqft_min.toLocaleString()
                  : `${listing.sqft_min.toLocaleString()}–${listing.sqft_max.toLocaleString()}`,
                label: "SQFT",
              },
            ].map((stat) => (
              <div
                key={stat.label}
                style={{
                  textAlign: "center",
                  padding: 8,
                  background: "var(--color-bg)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius-sm)",
                }}
              >
                <div
                  style={{
                    fontFamily: "var(--font-display)",
                    fontWeight: 600,
                    fontSize: 15,
                    color: "var(--color-text)",
                  }}
                >
                  {stat.value}
                </div>
                <div
                  style={{
                    fontSize: 11,
                    fontWeight: 500,
                    letterSpacing: "0.02em",
                    color: "var(--color-text-muted)",
                  }}
                >
                  {stat.label}
                </div>
              </div>
            ))}
          </div>

          {/* Pets */}
          {(listing.cats || listing.dogs) && (
            <div style={{ display: "flex", gap: 6, marginTop: 12 }}>
              {listing.cats && (
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 500,
                    letterSpacing: "0.02em",
                    padding: "2px 8px",
                    borderRadius: "var(--radius-sm)",
                    background: "var(--color-success-bg)",
                    border: "1px solid rgba(22, 163, 74, 0.2)",
                    color: "var(--color-success)",
                    textTransform: "uppercase",
                  }}
                >
                  Cats OK
                </span>
              )}
              {listing.dogs && (
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 500,
                    letterSpacing: "0.02em",
                    padding: "2px 8px",
                    borderRadius: "var(--radius-sm)",
                    background: "var(--color-success-bg)",
                    border: "1px solid rgba(22, 163, 74, 0.2)",
                    color: "var(--color-success)",
                    textTransform: "uppercase",
                  }}
                >
                  Dogs OK
                </span>
              )}
            </div>
          )}

          {/* Description */}
          {listing.details && (
            <div
              style={{
                marginTop: 12,
                fontSize: 13,
                color: "var(--color-text-secondary)",
                lineHeight: 1.6,
              }}
            >
              {listing.details}
            </div>
          )}

          {/* Units */}
          {listing.units.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <div
                style={{
                  fontFamily: "var(--font-display)",
                  fontWeight: 600,
                  fontSize: 13,
                  color: "var(--color-text)",
                  marginBottom: 6,
                }}
              >
                Available Units
              </div>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: 4,
                }}
              >
                {listing.units.map((unit, i) => (
                  <div
                    key={i}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      padding: 8,
                      background: "var(--color-bg)",
                      border: "1px solid var(--color-border)",
                      borderRadius: "var(--radius-sm)",
                      fontSize: 13,
                    }}
                  >
                    <span style={{ color: "var(--color-text-secondary)" }}>
                      {unit.beds} bd / {unit.baths} ba
                      {unit.sqft ? ` · ${unit.sqft.toLocaleString()} sqft` : ""}
                    </span>
                    <span
                      style={{
                        fontWeight: 600,
                        color: "var(--color-text)",
                      }}
                    >
                      {unit.list_price
                        ? `${formatPrice(unit.list_price)}/mo`
                        : "—"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Go to Listing button */}
          <button
            onClick={() => router.push(`/home/${listing.listing_id}`)}
            style={{
              width: "100%",
              marginTop: 16,
              padding: 12,
              border: "none",
              borderRadius: "var(--radius-sm)",
              background: "var(--color-primary)",
              color: "#fff",
              fontSize: 15,
              fontWeight: 600,
              fontFamily: "var(--font-display)",
              cursor: "pointer",
            }}
          >
            Go to Listing
          </button>
        </div>
      </div>
    </div>
  );
}
