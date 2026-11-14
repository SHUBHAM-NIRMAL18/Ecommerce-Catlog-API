import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Pages render on the server from live API data on every request,
  // so the Cache Components model (cacheComponents) is not used.
  reactCompiler: true,
  // Smaller production image for Docker (Part D).
  output: "standalone",
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
