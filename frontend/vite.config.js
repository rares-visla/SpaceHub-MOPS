import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // In dezvoltare, /api este trimis catre Django (python manage.py runserver).
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/tests/setup.js",
    coverage: { include: ["src/**/*.{js,jsx}"], exclude: ["src/tests/**", "src/main.jsx"] },
  },
});
