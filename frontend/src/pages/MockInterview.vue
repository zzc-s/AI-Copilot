<script setup>
import { computed, ref } from "vue";
import client, { pollTask } from "../api/client";
import { useCopilotStore } from "../stores/copilot";
import { ElMessage, ElMessageBox } from "element-plus";
import PageHeader from "../components/PageHeader.vue";
import StepFlow from "../components/StepFlow.vue";
import EmptyGuide from "../components/EmptyGuide.vue";
import ScoreRing from "../components/ScoreRing.vue";
import DimensionBarChart from "../components/DimensionBarChart.vue";
import JsonCollapse from "../components/JsonCollapse.vue";
import AsyncTaskProgress from "../components/AsyncTaskProgress.vue";

const store = useCopilotStore();
const sessionLoading = ref(false);
const reportLoading = ref(false);
const activeCollapse = ref([]);
const asyncMode = ref(false);
const asyncRunning = ref(false);
const mediaHint = ref("");

const recordingQid = ref(null);
let mediaRecorder = null;
const audioChunks = ref([]);

const answeredLocalCount = computed(() => {
  const ids = store.questions.map((q) => q.id);
  return ids.filter((id) => {
    const t = store.interviewAnswers[id];
    return t && String(t).trim().length > 0;
  }).length;
});

const barItems = computed(() => {
  const rep = store.interviewReport;
  const total = store.questions.length || 1;
  const answered = rep?.questions_answered ?? answeredLocalCount.value;
  const progress = Math.min(100, Math.round((answered / total) * 100));
  const overall = rep?.overall_score != null ? Number(rep.overall_score) : 0;
  return [
    { name: "综合得分", value: Math.min(100, Math.max(0, overall)) },
    { name: "答题进度", value: progress }
  ];
});

const resetPage = async () => {
  try {
    await ElMessageBox.confirm(
      "将清空本页用户信息、作答、报告；并清除当前面试 Session 与题目（需重新生成问题）。是否继续？",
      "重置本页",
      { type: "warning", confirmButtonText: "清空", cancelButtonText: "取消" }
    );
  } catch {
    return;
  }
  store.resetInterviewPage();
  store.sessionId = "";
  store.questions = [];
  store.interviewReport = null;
  activeCollapse.value = [];
  stopStream();
  ElMessage.success("已清空模拟面试页");
};

const createSession = async () => {
  if (!store.jdId) {
    ElMessage.warning("请先完成 JD 解析，或从 JD 解析页面进入");
    return;
  }
  if (!store.interviewProfile.user_email || !store.interviewProfile.user_name) {
    ElMessage.warning("请填写邮箱和用户名");
    return;
  }
  sessionLoading.value = true;
  sessionLoading.value = true;
  store.interviewReport = null;
  activeCollapse.value = [];
  try {
    const payload = { ...store.interviewProfile, jd_id: store.jdId };
    if (asyncMode.value) {
      asyncRunning.value = true;
      const { data } = await client.post("/interview/session", payload, { params: { async: true } });
      const pr = await pollTask(data.task_id);
      const inner = pr.result;
      if (inner?.status !== "ok" || !inner.data) throw new Error("异步任务异常");
      store.sessionId = inner.data.session_id;
      store.questions = inner.data.questions || [];
    } else {
      const { data } = await client.post("/interview/session", payload);
      store.sessionId = data.session_id;
      store.questions = data.questions;
    }
    if (store.questions.length) {
      activeCollapse.value = [String(store.questions[0].id)];
    }
    ElMessage.success("已生成面试题");
  } catch (e) {
    const detail = e?.response?.data?.detail;
    ElMessage.error(typeof detail === "string" ? detail : e?.message || "创建会话失败");
  } finally {
    sessionLoading.value = false;
    asyncRunning.value = false;
  }
};

const submitAnswer = async (questionId) => {
  try {
    const body = {
      question_id: questionId,
      answer_text: store.interviewAnswers[questionId] || ""
    };
    if (asyncMode.value) {
      asyncRunning.value = true;
      const { data } = await client.post(`/interview/${store.sessionId}/answer`, body, { params: { async: true } });
      await pollTask(data.task_id);
      ElMessage.success("已提交（异步）");
    } else {
      await client.post(`/interview/${store.sessionId}/answer`, body);
      ElMessage.success("已提交");
    }
  } catch (e) {
    const detail = e?.response?.data?.detail;
    ElMessage.error(typeof detail === "string" ? detail : e?.message || "提交失败");
  } finally {
    asyncRunning.value = false;
  }
};

let micStream = null;
async function startRecording(qid) {
  mediaHint.value = "";
  try {
    micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch {
    mediaHint.value = "无法访问麦克风：请使用 localhost / https，并授予浏览器录音权限。";
    ElMessage.warning(mediaHint.value);
    return;
  }
  recordingQid.value = qid;
  audioChunks.value = [];
  mediaRecorder = new MediaRecorder(micStream);
  mediaRecorder.ondataavailable = (e) => {
    if (e.data.size) audioChunks.value.push(e.data);
  };
  mediaRecorder.start();
  ElMessage.info("录音中…再点「停止并提交」");
}

function stopStream() {
  if (micStream) {
    micStream.getTracks().forEach((t) => t.stop());
    micStream = null;
  }
  recordingQid.value = null;
}

async function stopRecordingAndSubmit(qid) {
  if (!mediaRecorder || recordingQid.value !== qid) return;
  const mr = mediaRecorder;
  const mime = mr.mimeType || "audio/webm";
  await new Promise((resolve) => {
    mr.onstop = resolve;
    mr.stop();
  });
  stopStream();
  const blob = new Blob(audioChunks.value, { type: mime });
  const fd = new FormData();
  fd.append("question_id", qid);
  fd.append("file", blob, "answer.webm");
  asyncRunning.value = true;
  try {
    const { data } = await client.post(`/interview/${store.sessionId}/answer/audio`, fd, {
      headers: { "Content-Type": "multipart/form-data" }
    });
    const pr = await pollTask(data.task_id);
    const inner = pr.result;
    if (inner?.status !== "ok" || !inner.data) throw new Error("语音任务异常");
    const d = inner.data;
    store.interviewAnswers[qid] = d.transcript || "";
    ElMessage.success("语音已转写并评分");
  } catch (e) {
    const detail = e?.response?.data?.detail;
    const msg =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((x) => x.msg || x).join("；")
          : e?.message || "语音提交失败";
    ElMessage.error(msg);
  } finally {
    asyncRunning.value = false;
    mediaRecorder = null;
  }
}

const fetchReport = async () => {
  if (!store.sessionId) return;
  reportLoading.value = true;
  try {
    const { data } = await client.get(`/interview/${store.sessionId}/report`);
    store.interviewReport = data;
    ElMessage.success("报告已更新");
  } catch (e) {
    const detail = e?.response?.data?.detail;
    ElMessage.error(typeof detail === "string" ? detail : "获取报告失败");
  } finally {
    reportLoading.value = false;
  }
};

function isAnswered(qid) {
  const t = store.interviewAnswers[qid];
  return Boolean(t && String(t).trim().length);
}
</script>

<template>
  <div class="page-iv">
    <PageHeader
      :step="3"
      title="模拟面试"
      subtitle="生成维度化面试题，演练作答后汇总得分与总结，并用于生成训练计划。"
      :tag-text="store.sessionId ? '会话进行中' : '待开始'"
      :tag-type="store.sessionId ? 'success' : 'info'"
    />
    <StepFlow :current-step="3" class="page-iv__steps" />

    <EmptyGuide
      v-if="!store.jdId"
      title="请先完成 JD 解析"
      description="模拟面试需要绑定岗位上下文，请先在 JD 解析页完成解析。"
      primary-label="去解析 JD"
      primary-path="/jd"
    />

    <template v-else>
      <el-card class="panel-card profile-card" shadow="never">
        <template #header>
          <span class="panel-card__title">候选人信息</span>
        </template>
        <div class="async-switch">
          <el-switch v-model="asyncMode" active-text="异步执行（生成题目/文本作答）" />
        </div>
        <AsyncTaskProgress :visible="asyncRunning" />
        <p v-if="mediaHint" class="media-hint">{{ mediaHint }}</p>
        <el-form :inline="true" :model="store.interviewProfile" class="profile-form">
          <el-form-item label="邮箱">
            <el-input v-model="store.interviewProfile.user_email" style="width: 220px" />
          </el-form-item>
          <el-form-item label="用户名">
            <el-input v-model="store.interviewProfile.user_name" style="width: 160px" />
          </el-form-item>
          <el-form-item>
            <el-space wrap>
              <el-button type="primary" :loading="sessionLoading" @click="createSession">生成面试问题</el-button>
              <el-button @click="resetPage">重置本页</el-button>
            </el-space>
          </el-form-item>
        </el-form>
        <p v-if="store.sessionId" class="session-line">
          Session:
          <el-tag type="info" effect="plain">{{ store.sessionId }}</el-tag>
        </p>
      </el-card>

      <el-row v-if="store.questions.length" :gutter="24" class="page-iv__body">
        <el-col :xs="24" :md="14">
          <el-card class="panel-card" shadow="never">
            <template #header>
              <span class="panel-card__title">题目列表</span>
            </template>
            <el-collapse v-model="activeCollapse" accordion>
              <el-collapse-item v-for="q in store.questions" :key="q.id" :name="String(q.id)">
                <template #title>
                  <span class="collapse-title" style="align-items: flex-start;">
                    <el-tag size="small" effect="plain" style="margin-top: 2px;">{{ q.dimension }}</el-tag>
                    <span class="collapse-title__text" style="white-space: normal; line-height: 1.6; margin: 0 8px; flex: 1;">{{ q.question_text }}</span>
                    <el-tag :type="isAnswered(q.id) ? 'success' : 'info'" size="small" round style="margin-top: 2px;">
                      {{ isAnswered(q.id) ? "已填写" : "待作答" }}
                    </el-tag>
                  </span>
                </template>
                <el-input
                  v-model="store.interviewAnswers[q.id]"
                  type="textarea"
                  :rows="4"
                  placeholder="在此输入你的回答…"
                />
                <div class="q-actions">
                  <el-button size="small" type="primary" @click="submitAnswer(q.id)">提交答案</el-button>
                  <el-button
                    v-if="recordingQid !== q.id"
                    size="small"
                    @click="startRecording(q.id)"
                  >
                    语音作答
                  </el-button>
                  <template v-else>
                    <el-button size="small" type="warning" @click="stopRecordingAndSubmit(q.id)">
                      停止并提交语音
                    </el-button>
                  </template>
                </div>
              </el-collapse-item>
            </el-collapse>
          </el-card>
        </el-col>
        <el-col :xs="24" :md="10">
          <el-card class="panel-card" shadow="never">
            <template #header>
              <span class="panel-card__title">面试报告</span>
            </template>
            <el-button
              v-if="store.sessionId"
              class="report-btn"
              :loading="reportLoading"
              type="primary"
              @click="fetchReport"
            >
              获取面试报告
            </el-button>
            <el-skeleton v-if="reportLoading" :rows="6" animated />
            <div v-else-if="store.interviewReport" class="report-block">
              <ScoreRing :value="Number(store.interviewReport.overall_score) || 0" title="综合分" />
              <DimensionBarChart :items="barItems" />
              <el-descriptions :column="1" border size="small" class="rep-desc">
                <el-descriptions-item label="状态">{{ store.interviewReport.status }}</el-descriptions-item>
                <el-descriptions-item label="已作答题数">
                  {{ store.interviewReport.questions_answered }}
                </el-descriptions-item>
              </el-descriptions>
              <p v-if="store.interviewReport.summary" class="rep-summary">{{ store.interviewReport.summary }}</p>
              <JsonCollapse label="报告 JSON" :data="store.interviewReport" />
            </div>
            <el-empty v-else description="提交作答后点击「获取面试报告」" />
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<style scoped>
.page-iv__steps {
  margin-bottom: 24px;
}
.async-switch {
  margin-bottom: 12px;
}
.media-hint {
  font-size: 12px;
  color: #d97706;
  margin: 0 0 10px;
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
.profile-form {
  flex-wrap: wrap;
}
.session-line {
  margin: 0;
  font-size: 13px;
  color: var(--app-muted);
}
.collapse-title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding-right: 12px;
}
.collapse-title__text {
  flex: 1;
  min-width: 0;
  font-weight: 500;
  color: #334155;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.q-actions {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.report-btn {
  margin-bottom: 16px;
}
.rep-summary {
  margin: 12px 0 0;
  padding: 12px 14px;
  background: #f8fafc;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.55;
  color: #475569;
}
.rep-desc {
  margin-top: 8px;
}
</style>
