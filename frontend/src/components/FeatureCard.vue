<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, required: true }
});
</script>

<template>
  <div class="feature-card">
    <div class="feature-card__icon">
      <slot name="icon" />
    </div>
    <h3 class="feature-card__title">{{ title }}</h3>
    <p class="feature-card__desc">{{ description }}</p>
  </div>
</template>

<style scoped>
.feature-card {
  padding: 22px 20px;
  border-radius: var(--app-radius-md);
  border: 1px solid #e2e8f0;
  background: var(--app-surface);
  box-shadow: var(--app-shadow-sm);
  transition: box-shadow 0.2s, transform 0.15s;
  height: 100%;
}

.feature-card:hover {
  box-shadow: var(--app-shadow-md);
  transform: translateY(-2px);
}

.feature-card__icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(139, 92, 246, 0.12));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  margin-bottom: 12px;
}

.feature-card__title {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
}

.feature-card__desc {
  margin: 0;
  font-size: 13px;
  color: var(--app-muted);
  line-height: 1.55;
}
</style>
