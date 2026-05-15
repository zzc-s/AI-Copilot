<script setup>

import { computed } from "vue";

import { useRoute } from "vue-router";

import { ElMessage, ElMessageBox } from "element-plus";

import { RefreshRight } from "@element-plus/icons-vue";

import { useCopilotStore } from "./stores/copilot";



const store = useCopilotStore();

const route = useRoute();



const activeMenu = computed(() => route.path);



const resetAll = async () => {

  try {

    await ElMessageBox.confirm(

      "将清空四个页面的表单、解析/匹配/面试/计划结果，并清除 JD ID、面试 Session 等流程状态。是否继续？",

      "清空全部草稿",

      { type: "warning", confirmButtonText: "全部清空", cancelButtonText: "取消" }

    );

  } catch {

    return;

  }

  store.resetAllDraftsAndWorkflow();

  ElMessage.success("已清空全部草稿与流程状态");

};

</script>



<template>

  <el-container class="layout-root">

    <el-header class="app-header">

      <div class="app-header-inner">

        <div class="app-brand">

          <router-link to="/" class="app-brand__link">

            <span class="app-brand__logo app-gradient-title">Copilot</span>

            <span class="app-brand__name">求职 AI Copilot</span>

            <span class="app-brand__beta">Beta</span>

          </router-link>

        </div>

        <div class="app-actions">

          <el-button class="app-reset" type="danger" plain size="small" @click="resetAll">

            <el-icon class="app-reset__icon"><RefreshRight /></el-icon>

            清空全部草稿

          </el-button>

        </div>

      </div>

      <el-menu

        class="app-menu"

        mode="horizontal"

        :default-active="activeMenu"

        router

        :ellipsis="false"

      >

        <el-menu-item index="/">

          <span class="menu-step">0</span>

          首页

        </el-menu-item>

        <el-menu-item index="/jd">

          <span class="menu-step">1</span>

          JD 解析

        </el-menu-item>

        <el-menu-item index="/resume-match">

          <span class="menu-step">2</span>

          简历匹配

        </el-menu-item>

        <el-menu-item index="/interview">

          <span class="menu-step">3</span>

          模拟面试

        </el-menu-item>

        <el-menu-item index="/plan">

          <span class="menu-step">4</span>

          训练计划

        </el-menu-item>

        <el-menu-item index="/history">

          我的记录

        </el-menu-item>

      </el-menu>

    </el-header>

    <el-main class="app-main">

      <div class="app-shell">

        <router-view v-slot="{ Component }">

          <transition name="fade-slide" mode="out-in">

            <component :is="Component" />

          </transition>

        </router-view>

      </div>

    </el-main>

  </el-container>

</template>



<style scoped>

.layout-root {

  min-height: 100vh;

}



.app-header {

  height: auto !important;

  padding: 0;

  box-sizing: border-box;

  position: sticky;

  top: 0;

  z-index: 50;

  background: rgba(255, 255, 255, 0.82);

  backdrop-filter: blur(10px);

  -webkit-backdrop-filter: blur(10px);

  border-bottom: 1px solid rgba(226, 232, 240, 0.9);

}



.app-header-inner {

  display: flex;

  align-items: center;

  justify-content: space-between;

  gap: 16px;

  padding: 12px 24px 8px;

  flex-wrap: wrap;

}



.app-brand__link {

  display: inline-flex;

  align-items: center;

  gap: 10px;

  text-decoration: none !important;

  color: inherit;

}



.app-brand__logo {

  font-weight: 800;

  font-size: 1.05rem;

}



.app-brand__name {

  font-weight: 700;

  font-size: 1.15rem;

  color: #0f172a;

}



.app-brand__beta {

  font-size: 11px;

  font-weight: 600;

  padding: 2px 8px;

  border-radius: 999px;

  background: #eef2ff;

  color: #4f46e5;

}



.app-menu {

  border-bottom: none;

  flex-wrap: wrap;

  padding: 0 16px 4px;

  background: transparent;

}



.app-menu :deep(.el-menu-item) {

  position: relative;

  border-radius: 8px 8px 0 0;

}



.app-menu :deep(.el-menu-item.is-active) {

  color: #4f46e5 !important;

  font-weight: 600;

}



.app-menu :deep(.el-menu-item.is-active::after) {

  content: "";

  position: absolute;

  left: 12px;

  right: 12px;

  bottom: 0;

  height: 3px;

  border-radius: 3px 3px 0 0;

  background: var(--app-gradient-brand);

}



.menu-step {

  display: inline-flex;

  align-items: center;

  justify-content: center;

  width: 22px;

  height: 22px;

  margin-right: 8px;

  border-radius: 999px;

  font-size: 11px;

  font-weight: 700;

  background: #e2e8f0;

  color: #475569;

}



.app-menu :deep(.el-menu-item.is-active) .menu-step {

  background: linear-gradient(135deg, #6366f1, #8b5cf6);

  color: #fff;

}



.app-reset__icon {

  margin-right: 4px;

  vertical-align: middle;

}



.app-main {

  padding: 24px;

}



.app-shell {

  max-width: 1200px;

  margin: 0 auto;

}

</style>

