export type UserPreferences = {
  bedrooms: number;
  bathrooms: number;
  price_min: number;
  price_max: number;
  distance_from_campus: string;
  roommates: number;
  amenities: string[];
  excerpt: string;
};

export type ProfileData = {
  user_id: string;
  username: string;
  phone: string;
  avatar_url: string | null;
  preferences: UserPreferences;
  onboarding_completed: boolean;
  created_at: string;
  updated_at: string;
};
