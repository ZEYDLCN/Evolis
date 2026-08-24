/** @type {import('next').NextConfig} */
const nextConfig = {
  // Standalone output: the production Docker image only needs
  // .next/standalone + .next/static, not node_modules or the source tree.
  output: "standalone",
};

module.exports = nextConfig;
