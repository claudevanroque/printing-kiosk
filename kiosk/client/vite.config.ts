import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),

    VitePWA({
      registerType: "autoUpdate",

      manifest: {
        name: "Printing Kiosk",

        short_name: "Print Kiosk",

        description: "Self-service printing, copying and scanning kiosk",

        theme_color: "#ffffff",

        background_color: "#f5f7fa",

        display: "standalone",

        start_url: "/",
      },
    }),
  ],
});
