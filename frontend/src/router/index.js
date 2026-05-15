import { createRouter, createWebHistory } from "vue-router";
import Home from "../pages/Home.vue";
import JDAnalyze from "../pages/JDAnalyze.vue";
import ResumeMatch from "../pages/ResumeMatch.vue";
import MockInterview from "../pages/MockInterview.vue";
import ImprovementPlan from "../pages/ImprovementPlan.vue";
import History from "../pages/History.vue";

const routes = [
  { path: "/", component: Home },
  { path: "/jd", component: JDAnalyze },
  { path: "/resume-match", component: ResumeMatch },
  { path: "/interview", component: MockInterview },
  { path: "/plan", component: ImprovementPlan },
  { path: "/history", component: History }
];

export default createRouter({
  history: createWebHistory(),
  routes
});
