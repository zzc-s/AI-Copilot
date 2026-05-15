<script setup>
defineProps({
  matched: { type: Array, default: () => [] },
  missing: { type: Array, default: () => [] },
  matchedLabel: { type: String, default: "命中关键词" },
  missingLabel: { type: String, default: "待补齐" }
});
</script>

<template>
  <div class="skill-cloud">
    <div class="skill-cloud__col">
      <div class="skill-cloud__head skill-cloud__head--ok">{{ matchedLabel }}</div>
      <div class="skill-cloud__tags">
        <el-tag
          v-for="(t, i) in matched"
          :key="'m-' + i"
          type="success"
          effect="light"
          round
        >
          {{ t }}
        </el-tag>
        <span v-if="!matched.length" class="skill-cloud__empty">暂无</span>
      </div>
    </div>
    <div class="skill-cloud__col">
      <div class="skill-cloud__head skill-cloud__head--warn">{{ missingLabel }}</div>
      <div class="skill-cloud__tags">
        <el-tag
          v-for="(t, i) in missing"
          :key="'x-' + i"
          type="warning"
          effect="light"
          round
        >
          {{ t }}
        </el-tag>
        <span v-if="!missing.length" class="skill-cloud__empty">暂无</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.skill-cloud {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

@media (max-width: 640px) {
  .skill-cloud {
    grid-template-columns: 1fr;
  }
}

.skill-cloud__head {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 10px;
}

.skill-cloud__head--ok {
  color: #059669;
}

.skill-cloud__head--warn {
  color: #d97706;
}

.skill-cloud__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  min-height: 32px;
}

.skill-cloud__empty {
  font-size: 13px;
  color: #94a3b8;
}
</style>
