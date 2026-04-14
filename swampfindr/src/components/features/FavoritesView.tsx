"use client";

import { useEffect, useState, useCallback } from "react";
import Image from "next/image";
import { getToken } from "@/lib/supabase/client";
import { getFavoriteListings, toggleFavorite } from "@/lib/api/flask";
import { ListingCard } from "@/components/features/ListingCard";
import type { Listing } from "@/types/listing";
import type { ProfileData } from "@/types/profile";

const FLASK_API_URL = process.env.NEXT_PUBLIC_FLASK_API_URL ?? "http://localhost:8080";

function SkeletonCard() {
  return (
    <div
      style={{
        borderRadius: 16,
        border: "1px solid var(--color-border)",
        background: "var(--color-surface)",
        overflow: "hidden",
        aspectRatio: "3/4",
      }}
    >
      <div
        style={{
          width: "100%",
          height: "100%",
          background: "var(--color-bg)",
          animation: "pulse 1.5s ease-in-out infinite",
        }}
      />
    </div>
  );
}

function ProfileHeader({ profile }: { profile: ProfileData }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 16,
        marginBottom: 32,
      }}
    >
      {profile.avatar_url ? (
        <Image
          src={profile.avatar_url}
          alt={profile.username}
          width={48}
          height={48}
          style={{
            borderRadius: "50%",
            objectFit: "cover",
            border: "2px solid var(--color-border)",
          }}
        />
      ) : (
        <div
          style={{
            width: 48,
            height: 48,
            borderRadius: "50%",
            background: "var(--color-primary)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#fff",
            fontFamily: "var(--font-display)",
            fontWeight: 700,
            fontSize: 20,
          }}
        >
          {profile.username.charAt(0).toUpperCase()}
        </div>
      )}
      <div>
        <h1
          style={{
            fontFamily: "var(--font-display)",
            fontSize: 28,
            fontWeight: 700,
            color: "var(--color-text)",
            letterSpacing: "-0.02em",
            margin: 0,
          }}
        >
          {profile.username}&apos;s Favorites
        </h1>
        <p
          style={{
            color: "var(--color-text-secondary)",
            fontSize: 14,
            margin: 0,
            marginTop: 2,
          }}
        >
          {/* Count will be set once listings load */}
        </p>
      </div>
    </div>
  );
}

export function FavoritesView() {
  const [listings, setListings] = useState<Listing[]>([]);
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) {
        setError("Not authenticated");
        return;
      }

      const [favRes, profileRes] = await Promise.all([
        getFavoriteListings(token),
        fetch(`${FLASK_API_URL}/api/v1/profiles/me`, {
          headers: { Authorization: `Bearer ${token}` },
        }).then((r) => r.json()),
      ]);

      if (favRes.success) {
        setListings(favRes.data);
      }
      if (profileRes.success) {
        setProfile(profileRes.data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load favorites");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleFavoriteToggle = async (listingId: string) => {
    // Optimistic removal from the list
    setListings((prev) => prev.filter((l) => l.listing_id !== listingId));

    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      await toggleFavorite(token, listingId);
    } catch {
      // Revert — re-fetch to get accurate state
      fetchData();
    }
  };

  if (error && listings.length === 0) {
    return (
      <div style={{ maxWidth: 1200, margin: "0 auto", padding: "32px 24px" }}>
        <div style={{ textAlign: "center", padding: "48px 24px" }}>
          <p
            style={{
              color: "var(--color-text-secondary)",
              fontSize: 15,
              marginBottom: 16,
            }}
          >
            {error}
          </p>
          <button
            onClick={fetchData}
            style={{
              padding: "8px 20px",
              fontSize: 14,
              fontFamily: "var(--font-display)",
              fontWeight: 600,
              background: "var(--color-primary)",
              color: "white",
              border: "none",
              borderRadius: "var(--radius-sm)",
              cursor: "pointer",
            }}
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: "32px 24px" }}>
      {profile && <ProfileHeader profile={profile} />}

      {!profile && !loading && (
        <div style={{ marginBottom: 32 }}>
          <h1
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 28,
              fontWeight: 700,
              color: "var(--color-text)",
              letterSpacing: "-0.02em",
              marginBottom: 4,
            }}
          >
            Your Favorites
          </h1>
        </div>
      )}

      {/* Count label */}
      {!loading && listings.length > 0 && (
        <p
          style={{
            color: "var(--color-text-muted)",
            fontSize: 13,
            fontWeight: 500,
            letterSpacing: "0.02em",
            marginBottom: 16,
          }}
        >
          {listings.length} {listings.length === 1 ? "LISTING" : "LISTINGS"}
        </p>
      )}

      {/* Grid: 3 per row */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 20,
        }}
      >
        {loading
          ? Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)
          : listings.map((listing) => (
              <ListingCard
                key={listing.listing_id}
                listing={listing}
                onFavoriteToggle={handleFavoriteToggle}
                basePath="/home"
              />
            ))}
      </div>

      {/* Empty state */}
      {!loading && listings.length === 0 && (
        <div
          style={{
            textAlign: "center",
            padding: "64px 24px",
          }}
        >
          <div
            style={{
              fontSize: 48,
              marginBottom: 16,
              opacity: 0.3,
            }}
          >
            <svg
              width="48"
              height="48"
              viewBox="0 0 24 24"
              fill="none"
              stroke="var(--color-text-muted)"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
            </svg>
          </div>
          <p
            style={{
              color: "var(--color-text-secondary)",
              fontSize: 15,
              marginBottom: 4,
            }}
          >
            No favorites yet
          </p>
          <p
            style={{
              color: "var(--color-text-muted)",
              fontSize: 13,
            }}
          >
            Heart a listing from the home feed or search results to save it here.
          </p>
        </div>
      )}
    </div>
  );
}
