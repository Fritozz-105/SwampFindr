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
  settings: {
    profileUpdateFailed: "Could not update profile. Please try again.",
    preferencesUpdateFailed: "Could not update preferences. Please try again.",
    passwordUpdateFailed: "Failed to update password. Please try again.",
    wrongCurrentPassword: "Current password is incorrect. Please try again.",
    emailUpdateFailed: "Failed to update email. Please try again.",
    gmailStatusFailed: "Could not load Gmail connection status.",
    gmailConnectFailed: "Could not start Google connection. Please try again.",
    gmailDisconnectFailed: "Could not disconnect Gmail. Please try again.",
    avatarUploadFailed: "Could not upload photo. Please try again.",
    mfaEnrollFailed: "Could not set up 2FA. Please try again.",
    mfaVerifyFailed: "Invalid code. Please try again.",
    mfaUnenrollFailed: "Could not disable 2FA. Please try again.",
    networkError: "Could not connect to the server. Please try again later.",
  },
} as const;
