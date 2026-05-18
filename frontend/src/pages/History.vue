<script setup>
import { onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import client from "../api/client";
import { useCopilotStore } from "../stores/copilot";
import PageHeader from "../components/PageHeader.vue";

const store = useCopilotStore();
const router = useRouter();

const email = ref(store.resumeForm.user_email || "");
const PAGE_SIZE = 10;

const matchItems = ref([]);
const matchTotal = ref(0);
const matchPage = ref(1);
const matchPageSize = ref(PAGE_SIZE);
const matchKeyword = ref("");
const loadingMatch = ref(false);

const interviewItems = ref([]);
const interviewTotal = ref(0);
const interviewPage = ref(1);
const interviewPageSize = ref(PAGE_SIZE);
const interviewKeyword = ref("");
const loadingInterview = ref(false);

const planItems = ref([]);
const planTotal = ref(0);
const planPage = ref(1);
const planPageSize = ref(PAGE_SIZE);
const planKeyword = ref("");
const loadingPlan = ref(false);

const fmtTime = (iso) => {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString("zh-CN");
};

const historyParams = (page, pageSize, keyword) => ({
  user_email: email.value.trim(),
  page,
  page_size: pageSize,
  keyword: keyword.trim() || undefined
});

const loadMatches = async () => {
  if (!email.value.trim()) return;
  loadingMatch.value = true;
  try {
    const { data: res } = await client.get("/user/history/matches", {
      params: historyParams(matchPage.value, matchPageSize.value, matchKeyword.value)
    });
    matchItems.value = res.items || [];
    matchTotal.value = res.total ?? 0;
    matchPage.value = res.page ?? matchPage.value;
    matchPageSize.value = res.page_size ?? matchPageSize.value;
  } catch {
    ElMessage.error("简历匹配记录加载失败");
  } finally {
    loadingMatch.value = false;
  }
};

const loadInterviews = async () => {
  if (!email.value.trim()) return;
  loadingInterview.value = true;
  try {
    const { data: res } = await client.get("/user/history/interviews", {
      params: historyParams(interviewPage.value, interviewPageSize.value, interviewKeyword.value)
    });
    interviewItems.value = res.items || [];
    interviewTotal.value = res.total ?? 0;
    interviewPage.value = res.page ?? interviewPage.value;
    interviewPageSize.value = res.page_size ?? interviewPageSize.value;
  } catch {
    ElMessage.error("模拟面试记录加载失败");
  } finally {
    loadingInterview.value = false;
  }
};

const loadPlans = async () => {
  if (!email.value.trim()) return;
  loadingPlan.value = true;
  try {
    const { data: res } = await client.get("/user/history/plans", {
      params: historyParams(planPage.value, planPageSize.value, planKeyword.value)
    });
    planItems.value = res.items || [];
    planTotal.value = res.total ?? 0;
    planPage.value = res.page ?? planPage.value;
    planPageSize.value = res.page_size ?? planPageSize.value;
  } catch {
    ElMessage.error("训练计划记录加载失败");
  } finally {
    loadingPlan.value = false;
  }
};

const loadAll = async () => {
  const e = email.value.trim();
  if (!e) {
    ElMessage.warning("请输入邮箱");
    return;
  }
  store.setProfileEmail(e);
  matchPage.value = 1;
  interviewPage.value = 1;
  planPage.value = 1;
  await Promise.all([loadMatches(), loadInterviews(), loadPlans()]);
};

let matchDebounceTimer = null;
let interviewDebounceTimer = null;
let planDebounceTimer = null;

watch(matchKeyword, () => {
  if (!email.value.trim()) return;
  clearTimeout(matchDebounceTimer);
  matchDebounceTimer = setTimeout(() => {
    matchPage.value = 1;
    loadMatches();
  }, 300);
});

watch(interviewKeyword, () => {
  if (!email.value.trim()) return;
  clearTimeout(interviewDebounceTimer);
  interviewDebounceTimer = setTimeout(() => {
    interviewPage.value = 1;
    loadInterviews();
  }, 300);
});

watch(planKeyword, () => {
  if (!email.value.trim()) return;
  clearTimeout(planDebounceTimer);
  planDebounceTimer = setTimeout(() => {
    planPage.value = 1;
    loadPlans();
  }, 300);
});

const onMatchPageChange = (p) => {
  matchPage.value = p;
  loadMatches();
};
const onMatchSizeChange = (s) => {
  matchPageSize.value = s;
  matchPage.value = 1;
  loadMatches();
};

const onInterviewPageChange = (p) => {
  interviewPage.value = p;
  loadInterviews();
};
const onInterviewSizeChange = (s) => {
  interviewPageSize.value = s;
  interviewPage.value = 1;
  loadInterviews();
};

const onPlanPageChange = (p) => {
  planPage.value = p;
  loadPlans();
};
const onPlanSizeChange = (s) => {
  planPageSize.value = s;
  planPage.value = 1;
  loadPlans();
};

const useJd = (row) => {
  if (!row.jd_id) return;
  store.jdId = String(row.jd_id);
  ElMessage.success("已载入 JD，可继续匹配或面试");
  router.push("/resume-match");
};

const useInterview = (row) => {
  store.jdId = String(row.jd_id);
  store.sessionId = String(row.session_id);
  router.push("/interview");
};

const usePlan = (row) => {
  store.sessionId = String(row.session_id);
  store.planEmail = email.value.trim();
  router.push("/plan");
};

onMounted(() => {
  if (email.value.trim()) loadAll();
});

watch(
  () => store.resumeForm.user_email,
  (v) => {
    if (v && v !== email.value) email.value = v;
  }
);
</script>

<template>
  <div class="history-page">
    <PageHeader
      :step="0"
      title="我的记录"
      subtitle="按邮箱聚合简历匹配、模拟面试与训练计划；支持关键字模糊搜索与分页（每页 10 条）"
      tag-text="作品集"
      tag-type="success"
    />

    <el-card shadow="never" class="history-filter">
      <el-form inline @submit.prevent="loadAll">
        <el-form-item label="邮箱">
          <el-input v-model="email" placeholder="与各页填写一致" style="width: 280px" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadAll">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="history-block">
      <template #header>
        <span>简历匹配</span>
        <el-tag size="small" type="info">共 {{ matchTotal }} 条</el-tag>
      </template>
      <div class="history-toolbar">
        <el-input
          v-model="matchKeyword"
          placeholder="搜索公司、岗位"
          clearable
          style="max-width: 320px"
        />
      </div>
      <el-table v-loading="loadingMatch" :data="matchItems" empty-text="暂无记录">
        <el-table-column label="岗位" min-width="160">
          <template #default="{ row }">{{ row.company }} · {{ row.role }}</template>
        </el-table-column>
        <el-table-column label="匹配分" width="100">
          <template #default="{ row }">
            <el-tag :type="row.match_score >= 70 ? 'success' : 'warning'">{{ row.match_score }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="180">
          <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="primary" @click="useJd(row)">继续流程</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="matchTotal > 0" class="history-pagination">
        <el-pagination
          v-model:current-page="matchPage"
          v-model:page-size="matchPageSize"
          :total="matchTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="onMatchPageChange"
          @size-change="onMatchSizeChange"
        />
      </div>
    </el-card>

    <el-card shadow="never" class="history-block">
      <template #header>
        <span>模拟面试</span>
        <el-tag size="small" type="info">共 {{ interviewTotal }} 条</el-tag>
      </template>
      <div class="history-toolbar">
        <el-input
          v-model="interviewKeyword"
          placeholder="搜索公司、岗位、状态"
          clearable
          style="max-width: 320px"
        />
      </div>
      <el-table v-loading="loadingInterview" :data="interviewItems" empty-text="暂无记录">
        <el-table-column label="岗位" min-width="160">
          <template #default="{ row }">{{ row.company }} · {{ row.role }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column label="得分" width="90">
          <template #default="{ row }">{{ row.overall_score ?? "—" }}</template>
        </el-table-column>
        <el-table-column label="时间" width="180">
          <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="primary" @click="useInterview(row)">打开</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="interviewTotal > 0" class="history-pagination">
        <el-pagination
          v-model:current-page="interviewPage"
          v-model:page-size="interviewPageSize"
          :total="interviewTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="onInterviewPageChange"
          @size-change="onInterviewSizeChange"
        />
      </div>
    </el-card>

    <el-card shadow="never" class="history-block">
      <template #header>
        <span>训练计划</span>
        <el-tag size="small" type="info">共 {{ planTotal }} 条</el-tag>
      </template>
      <div class="history-toolbar">
        <el-input
          v-model="planKeyword"
          placeholder="搜索公司、岗位、计划/会话 ID"
          clearable
          style="max-width: 320px"
        />
      </div>
      <el-table v-loading="loadingPlan" :data="planItems" empty-text="暂无记录">
        <el-table-column label="岗位" min-width="160">
          <template #default="{ row }">
            <span v-if="row.company">{{ row.company }} · {{ row.role }}</span>
            <span v-else class="mono">—</span>
          </template>
        </el-table-column>
        <el-table-column label="计划 ID" min-width="200">
          <template #default="{ row }">
            <span class="mono">{{ row.plan_id }}</span>
          </template>
        </el-table-column>
        <el-table-column label="开始日" width="120">
          <template #default="{ row }">{{ fmtTime(row.start_date).slice(0, 10) }}</template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="primary" @click="usePlan(row)">查看计划</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="planTotal > 0" class="history-pagination">
        <el-pagination
          v-model:current-page="planPage"
          v-model:page-size="planPageSize"
          :total="planTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="onPlanPageChange"
          @size-change="onPlanSizeChange"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.history-filter {
  margin-bottom: 16px;
}
.history-block {
  margin-bottom: 16px;
}
.history-block :deep(.el-card__header) {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.history-toolbar {
  margin-bottom: 12px;
}
.history-pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
.mono {
  font-family: ui-monospace, monospace;
  font-size: 12px;
  color: #64748b;
}
</style>
