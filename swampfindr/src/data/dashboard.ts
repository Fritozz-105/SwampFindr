export const dashboard = {
  greeting: (name: string) => `Welcome, ${name}!`,
  placeholder: "Your housing search dashboard is coming soon.",
  signOut: "Sign Out",
  defaultName: "Gator",
  feed: {
    subtitle: "Here are your personalized housing recommendations.",
    empty: "No recommendations yet. Update your preferences to get started.",
    error: "Failed to load recommendations. Please try again.",
    loading: "Finding your best matches...",
  },
} as const;
