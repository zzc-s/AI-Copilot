<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  text: { type: String, default: "后台任务执行中…" }
});
</script>

<template>
  <div v-if="visible" class="async-task">
    <el-progress indeterminate :stroke-width="4" />
    <p class="async-task__text">{{ text }}</p>
  </div>
</template>

<style scoped>
.async-task {
  margin-bottom: 16px;
}
.async-task__text {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
</style>
