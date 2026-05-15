<script setup>
import { computed } from "vue";

const props = defineProps({
  label: { type: String, default: "原始数据（调试）" },
  data: { type: [Object, Array, String, Number, Boolean], default: null }
});

const text = computed(() => {
  if (props.data === null || props.data === undefined) return "";
  if (typeof props.data === "string") return props.data;
  try {
    return JSON.stringify(props.data, null, 2);
  } catch {
    return String(props.data);
  }
});
</script>

<template>
  <el-collapse v-if="data !== null && data !== undefined" class="json-collapse">
    <el-collapse-item :title="label" name="raw">
      <pre class="json-collapse__pre">{{ text }}</pre>
    </el-collapse-item>
  </el-collapse>
</template>

<style scoped>
.json-collapse {
  margin-top: 12px;
  border: none;
}
.json-collapse :deep(.el-collapse-item__header) {
  font-size: 13px;
  color: var(--app-muted);
}
.json-collapse__pre {
  margin: 0;
  padding: 12px;
  font-size: 12px;
  line-height: 1.45;
  background: #0f172a;
  color: #e2e8f0;
  border-radius: 8px;
  overflow: auto;
  max-height: 240px;
}
</style>
