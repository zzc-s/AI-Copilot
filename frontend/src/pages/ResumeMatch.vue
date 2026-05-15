<script setup>
import { computed, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import client, { pollTask } from "../api/client";
import { useCopilotStore } from "../stores/copilot";
import PageHeader from "../components/PageHeader.vue";
import StepFlow from "../components/StepFlow.vue";
import EmptyGuide from "../components/EmptyGuide.vue";
import ScoreRing from "../components/ScoreRing.vue";
import RadarChart from "../components/RadarChart.vue";
import SkillTagCloud from "../components/SkillTagCloud.vue";
import JsonCollapse from "../components/JsonCollapse.vue";
import AsyncTaskProgress from "../components/AsyncTaskProgress.vue";

const store = useCopilotStore();
const loading = ref(false);
const asyncMode = ref(false);
const asyncRunning = ref(false);

const radarIndicators = computed(() => {
  const r = store.resumeReport;
  if (!r) return [];
  const gap = r.gap_analysis || {};
  const hit = gap.matched_keywords || [];
  const miss = gap.missing_keywords || [];
  const total = hit.length + miss.length || 1;
  const kw = Math.round((hit.length / total) * 100);
  const supplement = Math.round(100 - (miss.length / total) * 100);
  return [
    { name: "综合匹配", value: Number(r.match_score) || 0 },
    { name: "关键词覆盖", value: kw },
    { name: "补强完成度", value: supplement },
    { name: "提升空间", value: Math.min(100, Math.max(0, 100 - (Number(r.match_score) || 0))) }
  ];
});

const matchedKw = computed(() => store.resumeReport?.gap_analysis?.matched_keywords || []);
const missingKw = computed(() => store.resumeReport?.gap_analysis?.missing_keywords || []);

const rewriteItems = computed(() => {
  const rw = store.resumeReport?.rewrite_suggestions || {};
  const out = [];
  const labels = {
    project_experience: "项目经历",
    skills: "技能栏",
    profile: "个人总结",
    jd_evidence: "JD 原文依据"
  };
  for (const [k, v] of Object.entries(labels)) {
    const arr = rw[k];
    if (Array.isArray(arr) && arr.length) {
      out.push({ section: v, lines: arr });
    }
  }
  const pairs = rw.keyword_evidence_pairs;
  if (Array.isArray(pairs) && pairs.length) {
    const lines = pairs.map((p) => {
      const sn = (p.jd_snippet || "").slice(0, 160);
      return `「${p.keyword}」→ 建议写进「${p.suggest_section || "项目/技能"}」；JD 依据：${sn}${sn.length >= 160 ? "…" : ""}`;
    });
    out.push({ section: "关键词与 JD 对照", lines });
  }
  return out;
});

const matchResume = async () => {
  if (!store.jdId) return;
  loading.value = true;
  store.resumeReport = null;
  try {
    const payload = { ...store.resumeForm, jd_id: store.jdId };
    if (asyncMode.value) {
      asyncRunning.value = true;
      const { data } = await client.post("/resume/match", payload, { params: { async: true } });
      const pr = await pollTask(data.task_id);
      const inner = pr.result;
      if (inner?.status !== "ok" || !inner.data) throw new Error("异步任务返回异常");
      store.resumeReport = inner.data;
      ElMessage.success("异步匹配完成");
    } else {
      const { data } = await client.post("/resume/match", payload);
      store.resumeReport = data;
      ElMessage.success("匹配完成");
    }
  } catch (e) {
    const detail = e?.response?.data?.detail;
    const msg = typeof detail === "string" ? detail : e?.message || "请求失败";
    ElMessage.error(`匹配失败：${msg}`);
  } finally {
    loading.value = false;
    asyncRunning.value = false;
  }
};

const resetPage = async () => {
  try {
    await ElMessageBox.confirm("将清空本页表单与匹配结果，是否继续？", "重置本页", {
      type: "warning",
      confirmButtonText: "清空",
      cancelButtonText: "取消"
    });
  } catch {
    return;
  }
  store.resetResumePage();
  ElMessage.success("已清空简历匹配页");
};
</script>

<template>
  <div class="page-resume">
    <PageHeader
      :step="2"
      title="简历匹配"
      subtitle="基于已解析的 JD 与简历正文，输出匹配分、技能缺口与可执行的改写建议。"
      :tag-text="store.jdId ? '可匹配' : '需先解析 JD'"
      :tag-type="store.jdId ? 'success' : 'warning'"
    />
    <StepFlow :current-step="2" class="page-resume__steps" />

    <EmptyGuide
      v-if="!store.jdId"
      title="请先在「JD 解析」完成岗位解析"
      description="完成解析后会生成 JD ID，本页才能进行简历与岗位的匹配分析。"
      primary-label="去解析 JD"
      primary-path="/jd"
    />

    <el-row v-else :gutter="24">
      <el-col :xs="24" :md="10">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <span class="panel-card__title">简历信息</span>
          </template>
          <div class="async-switch">
            <el-switch v-model="asyncMode" active-text="异步执行（Celery）" />
          </div>
          <AsyncTaskProgress :visible="asyncRunning" />
          <el-form :model="store.resumeForm" label-width="100px">
            <el-form-item label="邮箱">
              <el-input v-model="store.resumeForm.user_email" />
            </el-form-item>
            <el-form-item label="用户名">
              <el-input v-model="store.resumeForm.user_name" />
            </el-form-item>
            <el-form-item label="简历标题">
              <el-input v-model="store.resumeForm.resume_title" />
            </el-form-item>
            <el-form-item label="简历内容">
              <el-input v-model="store.resumeForm.resume_text" type="textarea" :rows="8" />
            </el-form-item>
            <el-space wrap>
              <el-button type="primary" :loading="loading" :disabled="!store.jdId" @click="matchResume">
                开始匹配
              </el-button>
              <el-button @click="resetPage">重置本页</el-button>
            </el-space>
          </el-form>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="14">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <span class="panel-card__title">匹配报告</span>
          </template>
          <el-skeleton v-if="loading" :rows="10" animated />
          <div v-else-if="store.resumeReport" class="report">
            <el-row :gutter="16" class="report__charts">
              <el-col :span="10" :xs="24">
                <ScoreRing :value="Number(store.resumeReport.match_score) || 0" title="匹配分" />
              </el-col>
              <el-col :span="14" :xs="24">
                <RadarChart :indicators="radarIndicators" />
              </el-col>
            </el-row>
            <SkillTagCloud :matched="matchedKw" :missing="missingKw" class="report__cloud" />
            <div v-if="rewriteItems.length" class="rewrite">
              <h4 class="rewrite__title">改写建议</h4>
              <el-timeline>
                <el-timeline-item
                  v-for="(block, i) in rewriteItems"
                  :key="i"
                  :timestamp="block.section"
                  placement="top"
                  type="primary"
                  hollow
                >
                  <ul class="rewrite__list">
                    <li v-for="(line, j) in block.lines" :key="j">{{ line }}</li>
                  </ul>
                </el-timeline-item>
              </el-timeline>
            </div>
            <JsonCollapse label="完整响应 JSON" :data="store.resumeReport" />
          </div>
          <el-empty v-else description="点击「开始匹配」查看报告" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.page-resume__steps {
  margin-bottom: 24px;
}
.async-switch {
  margin-bottom: 12px;
}
.panel-card {
  border-radius: var(--app-radius-md) !important;
  border: 1px solid #e2e8f0 !important;
}
.panel-card__title {
  font-weight: 600;
  font-size: 15px;
}
.report__charts {
  margin-bottom: 8px;
}
.report__cloud {
  margin: 8px 0 20px;
}
.rewrite__title {
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}
.rewrite__list {
  margin: 0;
  padding-left: 18px;
  font-size: 14px;
  color: #475569;
  line-height: 1.55;
}
</style>
