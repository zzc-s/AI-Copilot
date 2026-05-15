<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import StepFlow from "../components/StepFlow.vue";
import FeatureCard from "../components/FeatureCard.vue";
import { useCopilotStore } from "../stores/copilot";
import client from "../api/client";

const store = useCopilotStore();
const router = useRouter();

const llmStats = ref([]);
const statsError = ref("");

onMounted(async () => {
  try {
    const { data } = await client.get("/llm/stats", { params: { days: 30 } });
    llmStats.value = Array.isArray(data) ? data : [];
  } catch {
    statsError.value = "无法加载模型表现（请确认后端 API 已启动）";
  }
});

const hasJd = computed(() => Boolean(store.jdId));
const hasSession = computed(() => Boolean(store.sessionId));

function goJd() {
  router.push("/jd");
}

function goResume() {
  router.push("/resume-match");
}

function goInterview() {
  router.push("/interview");
}

function goPlan() {
  router.push("/plan");
}

function goHistory() {
  router.push("/history");
}

function scrollFeatures() {
  document.getElementById("features")?.scrollIntoView({ behavior: "smooth" });
}
</script>

<template>
  <div class="home">
    <section class="hero">
      <p class="hero__eyebrow">本地 MVP · 闭环演示</p>
      <h1 class="hero__title app-gradient-title">
        让 AI 陪你跑完一次完整求职闭环
      </h1>
      <p class="hero__lead">
        从岗位解析、简历对齐、模拟面试到 7 天训练计划，一步步把「投递—反馈—改进」变成可执行流程。
      </p>
      <div class="hero__actions">
        <el-button type="primary" size="large" round @click="goJd">开始解析 JD</el-button>
        <el-button size="large" round @click="scrollFeatures">了解能力模块</el-button>
        <el-button size="large" round @click="goHistory">我的记录</el-button>
      </div>
      <div v-if="hasJd || hasSession" class="hero__resume card-soft">
        <span class="hero__resume-label">继续上次</span>
        <el-space wrap>
          <el-button v-if="hasJd" type="primary" plain round @click="goResume">
            已有 JD → 去简历匹配
          </el-button>
          <el-button v-if="hasSession" type="primary" plain round @click="goPlan">
            已有面试 Session → 生成训练计划
          </el-button>
          <el-button v-if="hasSession" round @click="goInterview">回到模拟面试</el-button>
        </el-space>
      </div>
    </section>

    <section class="section">
      <h2 class="section__title">四步闭环</h2>
      <p class="section__subtitle">点击任意一步即可跳转；建议在 JD 解析完成后再进行后续步骤。</p>
      <StepFlow :current-step="0" />
    </section>

    <section id="features" class="section">
      <h2 class="section__title">核心能力</h2>
      <el-row :gutter="16">
        <el-col :xs="24" :sm="12" :md="6">
          <FeatureCard title="结构化 JD 解析" description="抽取职责、要求与关键词，为后续匹配与面试生成统一上下文。">
            <template #icon>🧩</template>
          </FeatureCard>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <FeatureCard title="简历匹配与改写" description="量化匹配分、展示命中与缺口，并给出可执行的改写方向。">
            <template #icon>📎</template>
          </FeatureCard>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <FeatureCard title="模拟面试演练" description="按维度生成题目，记录作答并汇总得分与总结。">
            <template #icon>💬</template>
          </FeatureCard>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <FeatureCard title="7 天训练计划" description="结合面试表现生成每日任务，形成可追踪的提升路径。">
            <template #icon>📅</template>
          </FeatureCard>
        </el-col>
      </el-row>
    </section>

    <section class="section">
      <div class="cta card-soft">
        <div>
          <h3 class="cta__title">准备好开始了吗？</h3>
          <p class="cta__desc">建议先准备一段真实 JD 与简历正文，体验完整链路。</p>
        </div>
        <el-button type="primary" size="large" round @click="goJd">立即解析 JD</el-button>
      </div>
    </section>

    <section v-if="statsError || llmStats.length" class="section">
      <el-collapse>
        <el-collapse-item title="模型表现（LLM 调用聚合）" name="stats">
          <p v-if="statsError" class="stats-err">{{ statsError }}</p>
          <el-table v-else :data="llmStats" size="small" border style="width: 100%">
            <el-table-column prop="model_name" label="模型" min-width="120" />
            <el-table-column prop="scene" label="场景" min-width="140" />
            <el-table-column prop="call_count" label="调用次数" width="100" />
            <el-table-column prop="avg_latency_ms" label="平均时延(ms)" width="130" />
            <el-table-column prop="total_cost" label="估算成本" width="110" />
          </el-table>
        </el-collapse-item>
      </el-collapse>
    </section>

    <footer class="footer">
      <p><strong>求职 AI Copilot</strong> · Vue 3 · Element Plus · FastAPI · PostgreSQL · pgvector · Celery</p>
      <p class="footer__muted">已启用：向量检索 · 异步队列 · 多模型路由 · 语音面试（mock 可演示）</p>
    </footer>
  </div>
</template>

<style scoped>
.home {
  max-width: 1120px;
  margin: 0 auto;
}

.hero {
  padding: 32px 0 40px;
  text-align: center;
}

.hero__eyebrow {
  margin: 0 0 12px;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #6366f1;
}

.hero__title {
  margin: 0;
  font-size: clamp(1.75rem, 4vw, 2.35rem);
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.2;
}

.hero__lead {
  margin: 16px auto 0;
  max-width: 560px;
  font-size: 15px;
  color: var(--app-muted);
  line-height: 1.65;
}

.hero__actions {
  margin-top: 28px;
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.hero__resume {
  margin-top: 28px;
  text-align: center;
}

.hero__resume-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 10px;
}

.card-soft {
  padding: 18px 20px;
  border-radius: var(--app-radius-md);
  background: #fff;
  border: 1px solid #e2e8f0;
  box-shadow: var(--app-shadow-sm);
}

.section {
  margin-bottom: 48px;
}

.section__title {
  margin: 0 0 8px;
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.section__subtitle {
  margin: 0 0 20px;
  font-size: 14px;
  color: var(--app-muted);
}

.cta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}

.cta__title {
  margin: 0 0 6px;
  font-size: 18px;
  font-weight: 700;
}

.cta__desc {
  margin: 0;
  font-size: 14px;
  color: var(--app-muted);
}

.footer {
  padding: 32px 0 48px;
  text-align: center;
  font-size: 13px;
  color: #64748b;
  border-top: 1px solid #e2e8f0;
}

.footer__muted {
  margin: 8px 0 0;
  font-size: 12px;
  color: #94a3b8;
}

.stats-err {
  margin: 0 0 12px;
  font-size: 13px;
  color: #d97706;
}
</style>
