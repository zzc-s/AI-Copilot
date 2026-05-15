import { defineStore } from "pinia";

const defaultJdForm = () => ({
  source: "manual",
  company: "",
  role: "",
  raw_text: ""
});

const defaultResumeForm = () => ({
  user_email: "student@example.com",
  user_name: "student",
  resume_title: "我的简历",
  resume_text: ""
});

const defaultInterviewProfile = () => ({
  user_email: "student@example.com",
  user_name: "student"
});

export const useCopilotStore = defineStore("copilot", {
  state: () => ({
    jdId: "",
    sessionId: "",
    questions: [],
    lastPlan: null,
    jdForm: defaultJdForm(),
    jdParsed: null,
    resumeForm: defaultResumeForm(),
    resumeReport: null,
    interviewProfile: defaultInterviewProfile(),
    interviewAnswers: {},
    interviewReport: null,
    planEmail: "student@example.com"
  }),
  actions: {
    resetJdPage() {
      this.jdForm = defaultJdForm();
      this.jdParsed = null;
      this.jdId = "";
    },
    resetResumePage() {
      this.resumeForm = defaultResumeForm();
      this.resumeReport = null;
    },
    resetInterviewPage() {
      this.interviewProfile = defaultInterviewProfile();
      this.interviewAnswers = {};
      this.interviewReport = null;
    },
    resetPlanPage() {
      this.planEmail = "student@example.com";
      this.lastPlan = null;
    },
    /** 清空 JD / 面试 session 等流程 ID，各 Tab 仍保留已填表单（除与 session 绑定的展示） */
    resetWorkflowIds() {
      this.jdId = "";
      this.sessionId = "";
      this.questions = [];
    },
    /** 表单 + 结果 + 流程 ID 全部恢复初始 */
    resetAllDraftsAndWorkflow() {
      this.resetJdPage();
      this.resetResumePage();
      this.resetInterviewPage();
      this.resetPlanPage();
      this.resetWorkflowIds();
    }
  }
});
