<script setup>
import { ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import client, { pollTask } from "../api/client";
import { useCopilotStore } from "../stores/copilot";
import PageHeader from "../components/PageHeader.vue";
import StepFlow from "../components/StepFlow.vue";
import JsonCollapse from "../components/JsonCollapse.vue";
import AsyncTaskProgress from "../components/AsyncTaskProgress.vue";

const store = useCopilotStore();
const loading = ref(false);
const asyncMode = ref(false);
const asyncRunning = ref(false);

const submit = async () => {
  const f = store.jdForm;
  if (!f.company.trim() || !f.role.trim()) {
    ElMessage.warning("请填写公司和岗位");
    return;
  }
  if (f.raw_text.trim().length < 20) {
    ElMessage.warning("JD 正文至少需要 20 个字符，请粘贴完整职位描述");
    return;
  }
  loading.value = true;
  store.jdParsed = null;
  try {
    if (asyncMode.value) {
      asyncRunning.value = true;
      const { data } = await client.post("/jd/parse", { ...f }, { params: { async: true } });
      const pr = await pollTask(data.task_id);
      const inner = pr.result;
      if (inner?.status !== "ok" || !inner.data) throw new Error("异步任务返回异常");
      const d = inner.data;
      store.jdId = d.jd_id;
      store.jdParsed = d.parsed;
      ElMessage.success("异步解析完成");
    } else {
      const { data } = await client.post("/jd/parse", { ...f });
      store.jdId = data.jd_id;
      store.jdParsed = data.parsed;
      ElMessage.success("解析完成，可去「简历匹配」继续");
    }
  } catch (e) {
    const detail = e?.response?.data?.detail;
    const msg =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((x) => x.msg || x).join("；")
          : e?.message || "请求失败";
    ElMessage.error(`解析失败：${msg}`);
  } finally {
    loading.value = false;
    asyncRunning.value = false;
  }
};

const resetPage = async () => {
  try {
    await ElMessageBox.confirm(
      "将清空本页表单、解析结果及当前 JD ID（后续页需重新解析）。是否继续？",
      "重置本页",
      { type: "warning", confirmButtonText: "清空", cancelButtonText: "取消" }
    );
  } catch {
    return;
  }
  store.resetJdPage();
  ElMessage.success("已清空 JD 解析页");
};
</script>

<template>
  <div class="page-jd">
    <PageHeader
      :step="1"
      title="JD 解析"
      subtitle="粘贴完整职位描述，提取职责、要求与关键词，为简历匹配与面试生成上下文。"
      :tag-text="store.jdId ? '已解析' : '待解析'"
      :tag-type="store.jdId ? 'success' : 'info'"
    />
    <StepFlow :current-step="1" class="page-jd__steps" />

    <el-row :gutter="24">
      <el-col :xs="24" :md="10">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <span class="panel-card__title">输入</span>
          </template>
          <div class="async-switch">
            <el-switch v-model="asyncMode" active-text="异步执行（Celery）" />
          </div>
          <AsyncTaskProgress :visible="asyncRunning" />
          <el-form :model="store.jdForm" label-width="90px">
            <el-form-item label="公司">
              <el-input v-model="store.jdForm.company" placeholder="公司名称" />
            </el-form-item>
            <el-form-item label="岗位">
              <el-input v-model="store.jdForm.role" placeholder="岗位名称" />
            </el-form-item>
            <el-form-item label="JD">
              <el-input v-model="store.jdForm.raw_text" type="textarea" :rows="8" />
              <p class="jd-hint">请粘贴完整职位描述，正文至少 20 个字符。</p>
            </el-form-item>
            <el-space wrap>
              <el-button type="primary" :loading="loading" @click="submit">解析 JD</el-button>
              <el-button @click="resetPage">重置本页</el-button>
            </el-space>
          </el-form>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="14">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <span class="panel-card__title">解析结果</span>
          </template>
          <el-skeleton v-if="loading" :rows="8" animated />
          <div v-else-if="store.jdParsed" class="jd-result">
            <div class="jd-summary card-soft">
              <div class="jd-summary__row">
                <span class="jd-summary__label">公司</span>
                <span>{{ store.jdForm.company || "—" }}</span>
              </div>
              <div class="jd-summary__row">
                <span class="jd-summary__label">岗位</span>
                <span>{{ store.jdForm.role || "—" }}</span>
              </div>
              <div class="jd-summary__row">
                <span class="jd-summary__label">JD ID</span>
                <el-tag type="info" effect="plain">{{ store.jdId }}</el-tag>
              </div>
            </div>
            <div class="jd-sections">
              <div class="jd-block">
                <h4 class="jd-block__title">职责要点</h4>
                <ul class="jd-block__list">
                  <li v-for="(line, i) in store.jdParsed.responsibilities || []" :key="'r-' + i">{{ line }}</li>
                  <li v-if="!(store.jdParsed.responsibilities || []).length" class="jd-block__empty">无</li>
                </ul>
              </div>
              <div class="jd-block">
                <h4 class="jd-block__title">岗位要求</h4>
                <ul class="jd-block__list">
                  <li v-for="(line, i) in store.jdParsed.requirements || []" :key="'q-' + i">{{ line }}</li>
                  <li v-if="!(store.jdParsed.requirements || []).length" class="jd-block__empty">无</li>
                </ul>
              </div>
              <div class="jd-block">
                <h4 class="jd-block__title">关键词</h4>
                <div class="jd-tags">
                  <el-tag v-for="(k, i) in store.jdParsed.keywords || []" :key="'k-' + i" effect="light" round>
                    {{ k }}
                  </el-tag>
                  <span v-if="!(store.jdParsed.keywords || []).length" class="jd-block__empty">无</span>
                </div>
              </div>
            </div>
            <JsonCollapse label="原始 JSON" :data="store.jdParsed" />
          </div>
          <el-empty v-else description="在左侧填写并点击「解析 JD」查看结构化结果" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.page-jd__steps {
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
.jd-hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.4;
}
.jd-result {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.card-soft {
  padding: 14px 16px;
  border-radius: var(--app-radius-sm);
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}
.jd-summary__row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 14px;
}
.jd-summary__row:last-child {
  margin-bottom: 0;
}
.jd-summary__label {
  width: 52px;
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 600;
  color: var(--app-muted);
}
.jd-sections {
  display: grid;
  gap: 16px;
}
.jd-block__title {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 700;
  color: #334155;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.jd-block__list {
  margin: 0;
  padding-left: 18px;
  font-size: 14px;
  color: #475569;
  line-height: 1.55;
}
.jd-block__empty {
  color: #94a3b8;
  font-size: 13px;
  list-style: none;
  margin-left: -18px;
}
.jd-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
