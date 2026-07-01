<template>
  <div id="app">
    <div class="app-header">
      <div class="header-content">
        <h1>📝 EduChat 智能作业批改系统</h1>
        <div class="header-nav">
          <el-radio-group v-model="currentModule" size="large">
            <el-radio-button value="grade">作业批改</el-radio-button>
            <el-radio-button value="rubric">评分标准</el-radio-button>
            <el-radio-button value="analytics">数据分析</el-radio-button>
            <el-radio-button value="research">科研评估</el-radio-button>
          </el-radio-group>
        </div>
        <div class="header-info">
          <el-tag type="success">科研级优化版本</el-tag>
          <el-tag type="info">多模态 + 自适应评分</el-tag>
        </div>
      </div>
    </div>
    
    <div class="app-content">
      <GradePanel v-if="currentModule === 'grade'" />
      <RubricManager v-if="currentModule === 'rubric'" />
      <AnalyticsDashboard v-if="currentModule === 'analytics'" />
      <ResearchConsole v-if="currentModule === 'research'" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import GradePanel from './components/GradePanel.vue'
import RubricManager from './components/RubricManager.vue'
import AnalyticsDashboard from './components/AnalyticsDashboard.vue'
import ResearchConsole from './components/ResearchConsole.vue'

const currentModule = ref('grade')
</script>

<style>
#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h1 {
  margin: 0;
  font-size: 24px;
}

.header-nav {
  display: flex;
  align-items: center;
}

.header-info {
  display: flex;
  gap: 10px;
}

.app-content {
  padding: 20px;
}
</style>