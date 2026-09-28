import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5190,
    strictPort: true,
    proxy: { "/api": "http://127.0.0.1:8010" },
    // The linked @concourse/web sources live in the sibling Concourse repo.
    fs: { allow: [".", "../../concourse-demo/web"] },
  },
});
