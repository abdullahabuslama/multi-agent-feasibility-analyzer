import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In development the dashboard runs on Vite (port 5173) and the API on
// uvicorn (port 8000). The proxy sends /api calls to the API, so the browser
// sees one origin and no CORS setup is needed.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});
