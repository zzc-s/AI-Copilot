<script setup>
import { computed, onMounted, ref } from "vue";
import client, { pollTask } from "../api/client";
import { useCopilotStore } from "../stores/copilot";
import { ElMessage, ElMessageBox } from "element-plus";
import PageHeader from "../components/PageHeader.vue";
import StepFlow from "../components/StepFlow.vue";
import EmptyGuide from "../components/EmptyGuide.vue";
import JsonCollapse from "../components/JsonCollapse.vue";
import AsyncTaskProgress from "../components/AsyncTaskProgress.vue";

const store = useCopilotStore();
const loading = ref(false);
const asyncMode = ref(false);
const asyncRunning = ref(false);

const planPayload = computed(() => store.lastPlan?.plan || null);
const dailyTasks = computed(() => planPayload.value?.daily_tasks || []);
const planLevel = computed(() => planPayload.value?.level || "");
const startDate = computed(() => store.lastPlan?.start_date);

function fmtDate(iso) {
  if (!iso) return "";
  try {
    const d = typeof iso === "string" ? new Date(iso) : iso;
    return d.toLocaleString();
  } catch {
    return String(iso);
  }
}

const loadLatestPlan = async () => {
  if (!store.planEmail?.trim()) return;
  try {
    const { data } = await client.get("/plan/latest", {
      params: { user_email: store.planEmail.trim() }
    });
    store.lastPlan = data;
  } catch {
    /* 尚无计划 */
  }
};

onMounted(() => {
  if (!store.lastPlan && store.sessionId) loadLatestPlan();
});

const generate = async () => {
  if (!store.sessionId) return;
  loading.value = true;
  try {
    const body = { user_email: store.planEmail, session_id: store.sessionId };
    if (asyncMode.value) {
      asyncRunning.value = true;
      const { data } = await client.post("/plan/generate", body, { params: { async: true } });
      const pr = await pollTask(data.task_id);
      const inner = pr.result;
      if (inner?.status !== "ok" || !inner.data) throw new Error("异步任务异常");
      const d = inner.data;
      store.lastPlan = {
        plan_id: d.plan_id,
        start_date: d.start_date,
        plan: d.plan
      };
      ElMessage.success("计划已生成（异步）");
    } else {
      const { data } = await client.post("/plan/generate", body);
      store.lastPlan = data;
      ElMessage.success("计划已生成");
    }
  } catch (e) {
    const detail = e?.response?.data?.detail;
    ElMessage.error(typeof detail === "string" ? detail : e?.message || "生成失败");
  } finally {
    loading.value = false;
    asyncRunning.value = false;
  }
};

const resetPage = async () => {
  try {
    await ElMessageBox.confirm("将清空邮箱与已生成的计划展示，是否继续？", "重置本页", {
      type: "warning",
      confirmButtonText: "清空",
      cancelButtonText: "取消"
    });
  } catch {
    return;
  }
  store.resetPlanPage();
  ElMessage.success("已清空训练计划页");
};

function downloadMarkdown() {
  if (!store.lastPlan) return;
  const p = store.lastPlan.plan;
  const lines = [
    "# 7 天训练计划",
    "",
    `- **路线**: ${p?.level || "—"}`,
    `- **起始**: ${fmtDate(store.lastPlan.start_date)}`,
    `- **Plan ID**: ${store.lastPlan.plan_id}`,
    ""
  ];
  (p?.daily_tasks || []).forEach((t, i) => {
    lines.push(`## Day ${i + 1} · ${t.day || ""}`, "", t.task || "", "");
  });
  const blob = new Blob([lines.join("\n")], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "training-plan-7d.md";
  a.click();
  URL.revokeObjectURL(url);
  ElMessage.success("已下载 Markdown");
}
</script>

<template>
  <div class="page-plan">
    <PageHeader
      :step="4"
      title="训练计划"
      subtitle="基于最近一次模拟面试的综合表现，生成 7 日可执行任务清单（Foundation / Advanced）。"
      :tag-text="store.sessionId ? '可生成' : '需面试 Session'"
      :tag-type="store.sessionId ? 'success' : 'warning'"
    />
    <StepFlow :current-step="4" class="page-plan__steps" />

    <EmptyGuide
      v-if="!store.sessionId"
      title="请先在「模拟面试」创建会话并完成作答"
      description="训练计划会读取面试 Session 与综合得分；请先完成模拟面试并获取报告（可选）后再生成计划。"
      primary-label="去模拟面试"
      primary-path="/interview"
    />

    <template v-else>
      <el-card class="panel-card" shadow="never">
        <template #header>
          <span class="panel-card__title">生成计划</span>
        </template>
        <div class="async-switch">
          <el-switch v-model="asyncMode" active-text="异步执行（Celery）" />
        </div>
        <AsyncTaskProgress :visible="asyncRunning" />
        <el-form :inline="true" @submit.prevent>
          <el-form-item label="邮箱">
            <el-input v-model="store.planEmail" placeholder="与账户关联的邮箱" style="width: 280px" />
          </el-form-item>
          <el-form-item>
            <el-space wrap>
              <el-button type="primary" :loading="loading" :disabled="!store.sessionId" @click="generate">
                生成 7 天计划
              </el-button>
              <el-button @click="resetPage">重置本页</el-button>
            </el-space>
          </el-form-item>
        </el-form>
      </el-card>

      <el-skeleton v-if="loading" :rows="8" animated />

      <template v-else-if="store.lastPlan">
        <div class="plan-meta card-soft">
          <div class="plan-meta__row">
            <span class="plan-meta__label">路线</span>
            <el-tag type="primary" effect="dark" round>{{ planLevel }}</el-tag>
          </div>
          <div class="plan-meta__row">
            <span class="plan-meta__label">起始时间</span>
            <span>{{ fmtDate(startDate) }}</span>
          </div>
          <div class="plan-meta__row">
            <span class="plan-meta__label">Plan ID</span>
            <el-tag type="info" effect="plain">{{ store.lastPlan.plan_id }}</el-tag>
          </div>
          <el-button type="primary" plain @click="downloadMarkdown">下载为 Markdown</el-button>
        </div>

        <div class="day-strip">
          <div v-for="(d, i) in dailyTasks" :key="i" class="day-card">
            <div class="day-card__head">
              <span class="day-card__badge">Day {{ i + 1 }}</span>
              <span class="day-card__date">{{ d.day }}</span>
            </div>
            <p class="day-card__task">{{ d.task }}</p>
            <el-tag v-if="d.done" type="success" size="small" effect="light">已完成</el-tag>
            <el-tag v-else type="info" size="small" effect="plain">待完成</el-tag>
          </div>
        </div>

        <JsonCollapse label="完整计划 JSON" :data="store.lastPlan" />
      </template>

      <el-empty v-else description="点击「生成 7 天计划」查看日程卡片" />
    </template>
  </div>
</template>

<style scoped>
.page-plan__steps {
  margin-bottom: 24px;
}
.async-switch {
  margin-bottom: 12px;
}
.panel-card {
  border-radius: var(--app-radius-md) !important;
  border: 1px solid #e2e8f0 !important;
  margin-bottom: 20px;
}
.panel-card__title {
  font-weight: 600;
  font-size: 15px;
}
.card-soft {
  padding: 16px 18px;
  border-radius: var(--app-radius-md);
  background: #fff;
  border: 1px solid #e2e8f0;
  margin-bottom: 20px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 24px;
}
.plan-meta__row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}
.plan-meta__label {
  font-size: 12px;
  font-weight: 600;
  color: var(--app-muted);
  width: 72px;
}
.day-strip {
  display: flex;
  gap: 14px;
  overflow-x: auto;
  padding-bottom: 8px;
  margin-bottom: 16px;
  scroll-snap-type: x mandatory;
}
.day-card {
  flex: 0 0 min(260px, 85vw);
  scroll-snap-align: start;
  padding: 16px 18px;
  border-radius: var(--app-radius-md);
  border: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #fff 0%, #fafbff 100%);
  box-shadow: var(--app-shadow-sm);
}
.day-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
}
.day-card__badge {
  font-size: 12px;
  font-weight: 800;
  color: #4f46e5;
  letter-spacing: 0.06em;
}
.day-card__date {
  font-size: 12px;
  color: var(--app-muted);
}
.day-card__task {
  margin: 0 0 12px;
  font-size: 14px;
  line-height: 1.55;
  color: #334155;
}
</style>
