// @ts-check
import react from "@astrojs/react";
import { defineConfig } from "astro/config";

// https://astro.build/config
export default defineConfig({
  site: "https://www.l145.be",
  base: "/nnue-chessbot",
  integrations: [react()],
  output: "static",
  devToolbar: {
    enabled: false,
  },
});
