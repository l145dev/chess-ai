// @ts-check
import node from "@astrojs/node";
import react from "@astrojs/react";
import { defineConfig } from "astro/config";

// https://astro.build/config
export default defineConfig({
  integrations: [react()],
  adapter: node({
    mode: "standalone",
  }),
  output: "server",
  devToolbar: {
    enabled: false,
  },
});
