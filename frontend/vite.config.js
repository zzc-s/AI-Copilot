import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules/echarts")) return "echarts";
          if (id.includes("node_modules/vue-echarts")) return "vue-echarts";
          if (id.includes("node_modules/element-plus")) return "element-plus";
        }
      }
    }
  }
});
