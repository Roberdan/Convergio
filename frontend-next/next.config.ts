import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  /* Performance */
  reactStrictMode: true,
  poweredByHeader: false,

  /* Environment */
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9000',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:9000',
  },

  /* Optimization */
  compress: true,

  /* Images */
  images: {
    domains: ['localhost'],
  },
}

export default nextConfig
