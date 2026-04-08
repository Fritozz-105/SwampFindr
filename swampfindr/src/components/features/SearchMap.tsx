"use client";

import { useEffect, useMemo, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { Listing } from "@/types/listing";
import { getListingPhotos } from "@/lib/utils/listing-photos";

interface SearchMapProps {
  listings: Listing[];
  onListingClick: (listingId: string) => void;
}

function createPriceIcon(price: string, selected: boolean): L.DivIcon {
  const bg = selected ? "#FF6B2C" : "#4F3CC9";
  return L.divIcon({
    className: "",
    html: `<div style="
      background: ${bg};
      color: #fff;
      font-size: 12px;
      font-weight: 600;
      padding: 4px 8px;
      border-radius: 12px;
      white-space: nowrap;
      box-shadow: 0 2px 6px rgba(0,0,0,0.2);
      text-align: center;
    ">${price}</div>`,
    iconSize: [60, 24],
    iconAnchor: [30, 12],
  });
}

function FitBounds({ listings }: { listings: Listing[] }) {
  const map = useMap();

  useEffect(() => {
    const valid = listings.filter(
      (l) => l.latitude !== null && l.longitude !== null,
    );
    if (valid.length === 0) return;

    const bounds = L.latLngBounds(
      valid.map((l) => [l.latitude!, l.longitude!] as L.LatLngTuple),
    );
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
  }, [listings, map]);

  return null;
}

function SearchMapInner({ listings, onListingClick }: SearchMapProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const mappable = useMemo(
    () =>
      listings.filter((l) => l.latitude !== null && l.longitude !== null),
    [listings],
  );

  if (mappable.length === 0) {
    return (
      <div
        style={{
          height: "calc(100vh - 200px)", minHeight: 400,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#f5f5f7",
          borderRadius: 8,
          border: "1px solid #e2e2e8",
          color: "#8c8c9a",
          fontSize: 14,
          fontFamily: "var(--font-body)",
        }}
      >
        No listings with coordinates to display on map
      </div>
    );
  }

  const center: L.LatLngTuple = [29.6516, -82.3248];

  return (
    <div style={{ borderRadius: 8, overflow: "hidden", border: "1px solid #e2e2e8" }}>
      <MapContainer
        center={center}
        zoom={13}
        style={{ height: "calc(100vh - 200px)", minHeight: 400, width: "100%" }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitBounds listings={mappable} />
        {mappable.map((listing) => {
          const priceLabel =
            listing.list_price_min === listing.list_price_max
              ? `$${listing.list_price_min.toLocaleString()}`
              : `$${listing.list_price_min.toLocaleString()}+`;

          return (
            <Marker
              key={listing.listing_id}
              position={[listing.latitude!, listing.longitude!]}
              icon={createPriceIcon(
                priceLabel,
                selectedId === listing.listing_id,
              )}
              eventHandlers={{
                click: () => setSelectedId(listing.listing_id),
              }}
            >
              <Popup>
                <div
                  style={{
                    width: 220,
                    fontFamily: "var(--font-body)",
                  }}
                >
                  <div
                    style={{
                      height: 120,
                      borderRadius: "6px 6px 0 0",
                      overflow: "hidden",
                      background:
                        getListingPhotos(listing).length > 0
                          ? `url(${getListingPhotos(listing)[0]}) center/cover`
                          : "linear-gradient(135deg, #4F3CC9, #FF6B2C)",
                      position: "relative",
                    }}
                  >
                    {listing.match_score !== null && (
                      <div
                        style={{
                          position: "absolute",
                          top: 8,
                          right: 8,
                          background: "#4F3CC9",
                          color: "#fff",
                          fontSize: 11,
                          fontWeight: 600,
                          padding: "2px 8px",
                          borderRadius: 10,
                        }}
                      >
                        {Math.round(listing.match_score * 100)}% match
                      </div>
                    )}
                  </div>

                  <div style={{ padding: 10 }}>
                    <div
                      style={{
                        fontSize: 13,
                        fontWeight: 600,
                        color: "#1a1a2e",
                        marginBottom: 4,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {listing.address}
                    </div>
                    <div
                      style={{
                        fontSize: 14,
                        fontWeight: 700,
                        color: "#4F3CC9",
                        marginBottom: 4,
                      }}
                    >
                      {listing.list_price_min === listing.list_price_max
                        ? `$${listing.list_price_min.toLocaleString()}/mo`
                        : `$${listing.list_price_min.toLocaleString()}–$${listing.list_price_max.toLocaleString()}/mo`}
                    </div>
                    <div
                      style={{
                        fontSize: 12,
                        color: "#8c8c9a",
                        marginBottom: 8,
                      }}
                    >
                      {listing.beds_min === listing.beds_max
                        ? `${listing.beds_min} bed`
                        : `${listing.beds_min}–${listing.beds_max} bed`}
                      {" · "}
                      {listing.baths_min === listing.baths_max
                        ? `${listing.baths_min} bath`
                        : `${listing.baths_min}–${listing.baths_max} bath`}
                      {listing.sqft_max > 0 &&
                        ` · ${listing.sqft_min.toLocaleString()} sqft`}
                    </div>
                    <button
                      onClick={() => onListingClick(listing.listing_id)}
                      style={{
                        width: "100%",
                        padding: "6px 0",
                        background: "#4F3CC9",
                        color: "#fff",
                        border: "none",
                        borderRadius: 4,
                        fontSize: 12,
                        fontWeight: 600,
                        cursor: "pointer",
                        fontFamily: "var(--font-body)",
                      }}
                    >
                      View Details
                    </button>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}

import dynamic from "next/dynamic";

const SearchMap = dynamic(() => Promise.resolve(SearchMapInner), {
  ssr: false,
  loading: () => (
    <div
      style={{
        height: "calc(100vh - 200px)", minHeight: 400,
        background: "#f5f5f7",
        borderRadius: 8,
        border: "1px solid #e2e2e8",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "#8c8c9a",
        fontSize: 14,
      }}
    >
      Loading map...
    </div>
  ),
});

export { SearchMap };
