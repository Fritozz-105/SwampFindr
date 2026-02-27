export const onboarding = {
  heading: "Welcome to GatorHousing",
  subtitle: "Let\u2019s set up your profile so we can find your perfect place",

  steps: {
    profile: {
      title: "Profile",
      heading: "About you",
      subtitle: "Tell us a bit about yourself",
    },
    preferences: {
      title: "Preferences",
      heading: "Housing preferences",
      subtitle: "What are you looking for?",
    },
    amenities: {
      title: "Amenities",
      heading: "Finishing touches",
      subtitle: "Select must-haves and add any extra details",
    },
  },

  labels: {
    username: "Username",
    phone: "Phone number",
    bedrooms: "Bedrooms",
    bathrooms: "Bathrooms",
    priceRange: "Price range ($/month)",
    priceMin: "Min",
    priceMax: "Max",
    distance: "Distance from campus",
    roommates: "Roommates",
    amenities: "Must-have amenities",
    excerpt: "Tell us what you\u2019re looking for",
  },

  placeholders: {
    username: "gator_albert",
    phone: "(352) 555-1234",
    priceMin: "500",
    priceMax: "2000",
    roommates: "0",
    excerpt: "I\u2019m a night owl looking for a quiet building near the engineering campus\u2026",
  },

  distanceOptions: [
    { value: "any", label: "Any distance" },
    { value: "walking", label: "Walking (< 1 mile)" },
    { value: "biking", label: "Biking (1\u20133 miles)" },
    { value: "driving", label: "Driving (3\u20135 miles)" },
    { value: "far", label: "Far (5+ miles)" },
  ],

  amenitiesList: [
    "In-unit laundry",
    "Pool",
    "Gym/Fitness center",
    "Parking included",
    "Pet friendly",
    "Furnished",
    "Dishwasher",
    "Balcony/Patio",
    "Study room",
    "High-speed internet",
    "Gated community",
    "Bus route nearby",
  ],

  buttons: {
    continue: "Continue",
    back: "Back",
    finish: "Finish setup",
  },

  excerptMaxLength: 200,
} as const;
