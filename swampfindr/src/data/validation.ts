export const validation = {
  email: {
    invalid: "Please enter a valid email address",
  },
  password: {
    required: "Password is required",
    minLength: "Password must be at least 8 characters",
    uppercase: "Password must contain at least one uppercase letter",
    lowercase: "Password must contain at least one lowercase letter",
    number: "Password must contain at least one number",
    specialChar: "Password must contain at least one special character",
    mismatch: "Passwords do not match",
  },
  fullName: {
    minLength: "Name must be at least 2 characters",
    maxLength: "Name is too long",
  },
} as const;
