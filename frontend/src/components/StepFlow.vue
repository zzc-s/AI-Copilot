<script setup>
import { useRouter } from "vue-router";

const props = defineProps({
  currentStep: { type: Number, default: 0 }
});

const router = useRouter();

const steps = [
  { step: 1, title: "JD 解析", desc: "结构化岗位要求与关键词", path: "/jd" },
  { step: 2, title: "简历匹配", desc: "缺口分析与改写建议", path: "/resume-match" },
  { step: 3, title: "模拟面试", desc: "生成题目与演练作答", path: "/interview" },
  { step: 4, title: "训练计划", desc: "7 天提升路径", path: "/plan" }
];

function go(path) {
  router.push(path);
}
</script>

<template>
  <div class="step-flow">
    <button
      v-for="s in steps"
      :key="s.path"
      type="button"
      class="step-flow__item"
      :class="{
        'step-flow__item--active': currentStep === s.step,
        'step-flow__item--done': currentStep > s.step
      }"
      @click="go(s.path)"
    >
      <span class="step-flow__num">{{ s.step }}</span>
      <span class="step-flow__body">
        <span class="step-flow__title">{{ s.title }}</span>
        <span class="step-flow__desc">{{ s.desc }}</span>
      </span>
    </button>
  </div>
</template>

<style scoped>
.step-flow {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

@media (max-width: 960px) {
  .step-flow {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 520px) {
  .step-flow {
    grid-template-columns: 1fr;
  }
}

.step-flow__item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  text-align: left;
  padding: 14px 16px;
  border: 1px solid #e2e8f0;
  border-radius: var(--app-radius-md);
  background: var(--app-surface);
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.15s;
  font: inherit;
  color: inherit;
}

.step-flow__item:hover {
  border-color: #c7d2fe;
  box-shadow: var(--app-shadow-sm);
  transform: translateY(-1px);
}

.step-flow__item--active {
  border-color: #818cf8;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}

.step-flow__item--done .step-flow__num {
  background: #10b981;
}

.step-flow__num {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: #94a3b8;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.step-flow__item--active .step-flow__num {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
}

.step-flow__body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.step-flow__title {
  font-weight: 600;
  font-size: 14px;
  color: #0f172a;
}

.step-flow__desc {
  font-size: 12px;
  color: var(--app-muted);
  line-height: 1.35;
}
</style>
