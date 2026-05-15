<script setup>
import { useRouter } from "vue-router";

const props = defineProps({
  title: { type: String, required: true },
  description: { type: String, default: "" },
  primaryLabel: { type: String, default: "前往" },
  primaryPath: { type: String, required: true }
});

const router = useRouter();

function go() {
  router.push(props.primaryPath);
}
</script>

<template>
  <div class="empty-guide">
    <div class="empty-guide__illu" aria-hidden="true">📋</div>
    <h3 class="empty-guide__title">{{ title }}</h3>
    <p v-if="description" class="empty-guide__desc">{{ description }}</p>
    <el-button type="primary" @click="go">{{ primaryLabel }}</el-button>
  </div>
</template>

<style scoped>
.empty-guide {
  text-align: center;
  padding: 28px 20px;
  border: 1px dashed #cbd5e1;
  border-radius: var(--app-radius-md);
  background: #f8fafc;
}

.empty-guide__illu {
  font-size: 40px;
  line-height: 1;
  margin-bottom: 12px;
  filter: grayscale(0.2);
}

.empty-guide__title {
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 600;
  color: #334155;
}

.empty-guide__desc {
  margin: 0 0 16px;
  font-size: 13px;
  color: var(--app-muted);
  line-height: 1.5;
  max-width: 360px;
  margin-left: auto;
  margin-right: auto;
}
</style>
