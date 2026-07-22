import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker deployment
  output: "standalone",
  
  // Allow images from external domains (for athlete profiles)
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "*.strava.com",
      },
      {
        protocol: "https",
        hostname: "*.cloudfront.net",
      },
    ],
  },
  
  // Disable x-powered-by header
  poweredByHeader: false,
};

export default nextConfig;
