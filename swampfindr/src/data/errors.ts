export const errors = {
  login: {
    invalid: "Invalid email or password",
  },
  signup: {
    alreadyRegistered: "An account with this email already exists",
    generic: "Something went wrong. Please try again.",
  },
  resetPassword: {
    emailRequired: "Please enter your email address",
    generic: "Something went wrong. Please try again.",
  },
  updatePassword: {
    generic: "Failed to update password. Please try again.",
  },
  oauth: {
    providerFailed: "Could not connect to provider. Please try again.",
  },
  callback: {
    authFailed: "Could not authenticate. Please try again.",
  },
  onboarding: {
    submitFailed: "Could not save your profile. Please try again.",
    networkError: "Could not connect to the server. Please try again later.",
  },
} as const;
