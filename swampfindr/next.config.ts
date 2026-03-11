import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "*.supabase.co",
      },
      {
        protocol: "https",
        hostname: "ar.rdcpix.com",
      },
      {
        protocol: "https",
        hostname: "*.rdcpix.com",
      },
    ],
  },
};

export default nextConfig;
