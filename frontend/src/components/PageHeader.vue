<script setup>
defineProps({
  step: { type: Number, required: true },
  title: { type: String, required: true },
  subtitle: { type: String, default: "" },
  tagText: { type: String, default: "" },
  tagType: {
    type: String,
    default: "info"
  }
});
</script>

<template>
  <header class="page-header">
    <div class="page-header__badge">{{ step }}/4</div>
    <div class="page-header__text">
      <div class="page-header__row">
        <h1 class="page-header__title">{{ title }}</h1>
        <el-tag v-if="tagText" :type="tagType" effect="light" round>{{ tagText }}</el-tag>
      </div>
      <p v-if="subtitle" class="page-header__subtitle">{{ subtitle }}</p>
    </div>
  </header>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 24px;
}

.page-header__badge {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--app-gradient-brand);
  color: #fff;
  font-weight: 700;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--app-shadow-md);
}

.page-header__title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #0f172a;
}

.page-header__row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.page-header__subtitle {
  margin: 8px 0 0;
  font-size: 14px;
  color: var(--app-muted);
  line-height: 1.5;
  max-width: 720px;
}
</style>
