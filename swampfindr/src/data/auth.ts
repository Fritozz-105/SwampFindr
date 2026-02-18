export const auth = {
  login: {
    heading: "Sign in",
    subtitle: "Don\u2019t have an account?",
    subtitleLink: "Sign up",
    submitLabel: "Sign in",
  },
  signup: {
    heading: "Create account",
    subtitle: "Already have an account?",
    subtitleLink: "Sign in",
    submitLabel: "Create account",
  },
  resetPassword: {
    heading: "Reset password",
    subtitle: "Enter your email and we\u2019ll send you a reset link",
    submitLabel: "Send Reset Link",
    backLink: "Back to sign in",
    rememberPrompt: "Remember your password?",
    successHeading: "Check your email",
    successMessage:
      "If an account exists with that email, we\u2019ve sent password reset instructions.",
  },
  updatePassword: {
    heading: "Set new password",
    subtitle: "Choose a strong password for your account",
    submitLabel: "Update Password",
    backLink: "Back to sign in",
  },
  labels: {
    email: "Email",
    password: "Password",
    newPassword: "New password",
    confirmPassword: "Confirm password",
    confirmNewPassword: "Confirm new password",
    fullName: "Full name",
    forgotPassword: "Forgot password?",
  },
  placeholders: {
    email: "gator@ufl.edu",
    password: "Enter your password",
    newPassword: "Enter new password",
    confirmPassword: "Confirm your password",
    confirmNewPassword: "Confirm new password",
    createPassword: "Create a strong password",
    fullName: "Albert Gator",
  },
  dividerText: "or continue with email",
  oauthGoogle: "Continue with Google",
  layout: {
    panelSubtitle:
      "Describe what you need. We\u2019ll match you with listings that actually fit your life near campus.",
  },
  strength: {
    weak: "Weak",
    fair: "Fair",
    good: "Good",
    strong: "Strong",
  },
} as const;
