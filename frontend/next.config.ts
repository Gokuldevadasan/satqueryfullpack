import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const backendUrl = (process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
    return [
      { source: "/outputs/:path*", destination: `${backendUrl}/outputs/:path*` },
    ];
  },
};

export default nextConfig;
