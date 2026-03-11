"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import {
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  Heart,
  Bed,
  Bath,
  Maximize,
  Cat,
  Dog,
} from "lucide-react";
import { getListingDetail, toggleFavorite } from "@/lib/api/flask";
import { createClient } from "@/lib/supabase/client";
import type { Listing } from "@/types/listing";

function ImageGallery({ photos, address }: { photos: string[]; address: string }) {
  const [current, setCurrent] = useState(0);
  const [hovering, setHovering] = useState(false);
  const total = photos.length;

  const prev = useCallback(() => {
    setCurrent((c) => (c === 0 ? total - 1 : c - 1));
  }, [total]);

  const next = useCallback(() => {
    setCurrent((c) => (c === total - 1 ? 0 : c + 1));
  }, [total]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "ArrowLeft") prev();
      if (e.key === "ArrowRight") next();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [prev, next]);

  if (total === 0) {
    return (
      <div
        style={{
          width: "100%",
          borderRadius: 16,
          overflow: "hidden",
          aspectRatio: "16/9",
          background: "linear-gradient(135deg, var(--color-primary), var(--color-accent))",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "white",
          fontFamily: "var(--font-display)",
          fontSize: 18,
          fontWeight: 600,
        }}
      >
        No Photos Available
      </div>
    );
  }

  const arrowStyle: React.CSSProperties = {
    position: "absolute",
    top: "50%",
    transform: "translateY(-50%)",
    zIndex: 2,
    width: 44,
    height: 44,
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "rgba(0,0,0,0.4)",
    backdropFilter: "blur(8px)",
    color: "white",
    border: "none",
    cursor: "pointer",
    opacity: hovering ? 1 : 0,
    transition: "opacity 0.2s, background 0.15s",
  };

  return (
    <div
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => setHovering(false)}
      style={{
        position: "relative",
        width: "100%",
        borderRadius: 16,
        overflow: "hidden",
        aspectRatio: "16/9",
      }}
    >
      {/* Current image */}
      <Image
        src={photos[current]}
        alt={`${address} photo ${current + 1}`}
        fill
        sizes="900px"
        style={{ objectFit: "cover" }}
        priority={current === 0}
      />

      {/* Prev / Next arrows */}
      {total > 1 && (
        <>
          <button onClick={prev} style={{ ...arrowStyle, left: 14 }} aria-label="Previous photo">
            <ChevronLeft size={22} />
          </button>
          <button onClick={next} style={{ ...arrowStyle, right: 14 }} aria-label="Next photo">
            <ChevronRight size={22} />
          </button>
        </>
      )}

      {/* Dot indicators */}
      {total > 1 && (
        <div
          style={{
            position: "absolute",
            bottom: 14,
            left: "50%",
            transform: "translateX(-50%)",
            display: "flex",
            gap: 6,
            zIndex: 2,
          }}
        >
          {photos.map((_, i) => (
            <button
              key={i}
              onClick={() => setCurrent(i)}
              style={{
                width: i === current ? 24 : 8,
                height: 8,
                borderRadius: 4,
                border: "none",
                cursor: "pointer",
                background: i === current ? "white" : "rgba(255,255,255,0.5)",
                transition: "all 0.2s",
                padding: 0,
              }}
              aria-label={`Go to photo ${i + 1}`}
            />
          ))}
        </div>
      )}

      {/* Counter badge */}
      {total > 1 && (
        <div
          style={{
            position: "absolute",
            top: 14,
            right: 14,
            background: "rgba(0,0,0,0.5)",
            backdropFilter: "blur(8px)",
            color: "white",
            fontSize: 12,
            fontWeight: 500,
            padding: "4px 10px",
            borderRadius: 20,
          }}
        >
          {current + 1} / {total}
        </div>
      )}
    </div>
  );
}

export default function ListingDetailPage() {
  const params = useParams<{ listingId: string }>();
  const [listing, setListing] = useState<Listing | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [favorited, setFavorited] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const res = await getListingDetail(params.listingId);
        setListing(res.data);
        setFavorited(res.data.is_favorited ?? false);
      } catch {
        setError("Listing not found.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [params.listingId]);

  const handleFavorite = async () => {
    if (!listing) return;
    setFavorited((prev) => !prev);
    try {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session?.access_token) return;
      await toggleFavorite(session.access_token, listing.listing_id);
    } catch {
      setFavorited((prev) => !prev);
    }
  };

  if (loading) {
    return (
      <div style={{ maxWidth: 900, margin: "0 auto", padding: "32px 24px" }}>
        <div
          style={{
            width: "100%",
            aspectRatio: "16/9",
            borderRadius: 16,
            background: "var(--color-bg)",
            animation: "pulse 1.5s ease-in-out infinite",
          }}
        />
        <div style={{ marginTop: 24 }}>
          <div
            style={{
              height: 32,
              width: 200,
              borderRadius: 8,
              background: "var(--color-bg)",
              animation: "pulse 1.5s ease-in-out infinite",
              marginBottom: 12,
            }}
          />
          <div
            style={{
              height: 20,
              width: 300,
              borderRadius: 8,
              background: "var(--color-bg)",
              animation: "pulse 1.5s ease-in-out infinite",
            }}
          />
        </div>
      </div>
    );
  }

  if (error || !listing) {
    return (
      <div style={{ maxWidth: 900, margin: "0 auto", padding: "32px 24px", textAlign: "center" }}>
        <p style={{ color: "var(--color-text-secondary)", fontSize: 15, marginBottom: 16 }}>
          {error || "Listing not found."}
        </p>
        <Link
          href="/home"
          style={{
            color: "var(--color-primary)",
            fontSize: 14,
            fontWeight: 600,
            textDecoration: "none",
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <ArrowLeft size={16} />
          Back to feed
        </Link>
      </div>
    );
  }

  const priceLabel =
    listing.list_price_min === listing.list_price_max
      ? `$${listing.list_price_min.toLocaleString()}`
      : `$${listing.list_price_min.toLocaleString()} – $${listing.list_price_max.toLocaleString()}`;

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "32px 24px" }}>
      {/* Back link */}
      <Link
        href="/home"
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 6,
          color: "var(--color-text-secondary)",
          fontSize: 14,
          textDecoration: "none",
          marginBottom: 20,
          transition: "opacity 0.15s",
        }}
      >
        <ArrowLeft size={16} />
        Back to feed
      </Link>

      {/* Photo gallery */}
      <ImageGallery photos={listing.photos} address={listing.address} />

      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginTop: 28,
          marginBottom: 28,
        }}
      >
        <div>
          <h1
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 28,
              fontWeight: 700,
              color: "var(--color-text)",
              letterSpacing: "-0.02em",
              marginBottom: 6,
            }}
          >
            {priceLabel}
            <span
              style={{
                fontSize: 16,
                fontWeight: 400,
                color: "var(--color-text-secondary)",
                marginLeft: 4,
              }}
            >
              /mo
            </span>
          </h1>
          <p style={{ fontSize: 15, color: "var(--color-text-secondary)", margin: 0 }}>
            {listing.address}, {listing.city}, {listing.state} {listing.postal_code}
          </p>
        </div>

        <button
          onClick={handleFavorite}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            padding: "10px 16px",
            borderRadius: 8,
            fontSize: 14,
            fontWeight: 500,
            cursor: "pointer",
            border: favorited ? "1px solid #fecaca" : "1px solid var(--color-border)",
            background: favorited ? "#fef2f2" : "var(--color-surface)",
            color: favorited ? "#dc2626" : "var(--color-text-secondary)",
            transition: "all 0.2s",
          }}
        >
          <Heart size={18} fill={favorited ? "currentColor" : "none"} />
          {favorited ? "Saved" : "Save"}
        </button>
      </div>

      {/* Key details */}
      <div
        style={{
          display: "flex",
          gap: 32,
          padding: "20px 0",
          borderTop: "1px solid var(--color-border)",
          borderBottom: "1px solid var(--color-border)",
          marginBottom: 28,
          flexWrap: "wrap",
        }}
      >
        <DetailItem
          icon={<Bed size={18} color="var(--color-primary)" />}
          label="Bedrooms"
          value={
            listing.beds_min === listing.beds_max
              ? `${listing.beds_min}`
              : `${listing.beds_min}–${listing.beds_max}`
          }
        />
        <DetailItem
          icon={<Bath size={18} color="var(--color-primary)" />}
          label="Bathrooms"
          value={
            listing.baths_min === listing.baths_max
              ? `${listing.baths_min}`
              : `${listing.baths_min}–${listing.baths_max}`
          }
        />
        <DetailItem
          icon={<Maximize size={18} color="var(--color-primary)" />}
          label="Size"
          value={
            listing.sqft_min === listing.sqft_max
              ? `${listing.sqft_min.toLocaleString()} sqft`
              : `${listing.sqft_min.toLocaleString()}–${listing.sqft_max.toLocaleString()} sqft`
          }
        />
        {listing.cats !== null && (
          <DetailItem
            icon={<Cat size={18} color={listing.cats ? "#22c55e" : "#ef4444"} />}
            label="Cats"
            value={listing.cats ? "Allowed" : "Not allowed"}
          />
        )}
        {listing.dogs !== null && (
          <DetailItem
            icon={<Dog size={18} color={listing.dogs ? "#22c55e" : "#ef4444"} />}
            label="Dogs"
            value={listing.dogs ? "Allowed" : "Not allowed"}
          />
        )}
      </div>

      {/* Amenities */}
      {listing.details && (
        <div style={{ marginBottom: 28 }}>
          <h2
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 18,
              fontWeight: 700,
              color: "var(--color-text)",
              marginBottom: 14,
            }}
          >
            Amenities & Details
          </h2>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {listing.details.split(", ").map((item, i) => (
              <span
                key={i}
                style={{
                  fontSize: 13,
                  padding: "5px 14px",
                  background: "var(--color-bg)",
                  border: "1px solid var(--color-border)",
                  borderRadius: 20,
                  color: "var(--color-text-secondary)",
                }}
              >
                {item}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Units table */}
      {listing.units && listing.units.length > 0 && (
        <div>
          <h2
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 18,
              fontWeight: 700,
              color: "var(--color-text)",
              marginBottom: 14,
            }}
          >
            Available Units
          </h2>
          <div
            style={{
              border: "1px solid var(--color-border)",
              borderRadius: 16,
              overflow: "hidden",
            }}
          >
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
              <thead>
                <tr style={{ background: "var(--color-bg)" }}>
                  {["Beds", "Baths", "Sqft", "Price", "Available"].map((h) => (
                    <th
                      key={h}
                      style={{
                        padding: "12px 20px",
                        textAlign: "left",
                        fontWeight: 600,
                        fontSize: 13,
                        color: "var(--color-text-secondary)",
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {listing.units.map((unit, i) => (
                  <tr
                    key={i}
                    style={{ borderTop: i > 0 ? "1px solid var(--color-border)" : undefined }}
                  >
                    <td style={{ padding: "12px 20px", color: "var(--color-text)" }}>
                      {unit.beds}
                    </td>
                    <td style={{ padding: "12px 20px", color: "var(--color-text)" }}>
                      {unit.baths}
                    </td>
                    <td style={{ padding: "12px 20px", color: "var(--color-text)" }}>
                      {unit.sqft?.toLocaleString() ?? "—"}
                    </td>
                    <td style={{ padding: "12px 20px", color: "var(--color-text)" }}>
                      {unit.list_price ? `$${unit.list_price.toLocaleString()}` : "—"}
                    </td>
                    <td style={{ padding: "12px 20px", color: "var(--color-text)" }}>
                      {unit.availability ? new Date(unit.availability).toLocaleDateString() : "Now"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function DetailItem({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      {icon}
      <div>
        <div
          style={{
            fontSize: 11,
            textTransform: "uppercase",
            letterSpacing: "0.06em",
            color: "var(--color-text-tertiary)",
            marginBottom: 2,
          }}
        >
          {label}
        </div>
        <div style={{ fontSize: 15, fontWeight: 600, color: "var(--color-text)" }}>{value}</div>
      </div>
    </div>
  );
}
