import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],

  server: {
    host: "localhost",
    port: 5174,

    proxy: {
      "/api": {
        target: "https://cute-hoops-notice.loca.lt",

        changeOrigin: true,
        secure: true,

        headers: {
          "bypass-tunnel-reminder": "true",
        },

        rewrite: (path) =>
          path.replace(/^\/api/, ""),
      },
    },
  },
});