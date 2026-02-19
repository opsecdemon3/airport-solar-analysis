/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Static export for Netlify/static hosts; standalone for Docker
  output: process.env.DOCKER_BUILD === '1' ? 'standalone' : 'export',
  
  // Images: use unoptimized for static export
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;
