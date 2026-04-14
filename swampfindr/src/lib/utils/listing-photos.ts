import type { Listing } from "@/types/listing";

export function getListingPhotos(listing: Listing): string[] {
  return listing.cleaned_photos?.length ? listing.cleaned_photos : listing.photos;
}
