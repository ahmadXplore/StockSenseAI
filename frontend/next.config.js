/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: "http://127.0.0.1:8005/api/v1/:path*",
      },
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8005/api/:path*",
      },
      {
        source: "/docs",
        destination: "http://127.0.0.1:8005/docs",
      },
      {
        source: "/openapi.json",
        destination: "http://127.0.0.1:8005/openapi.json",
      },
    ];
  },
};

module.exports = nextConfig;
