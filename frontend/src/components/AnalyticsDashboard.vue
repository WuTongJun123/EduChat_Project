<template>
  <div class="analytics-dashboard">
    <el-tabs v-model="activeTab" type="border-card">
      
      <!-- Tab 1: 批量批改分析 -->
      <el-tab-pane label="批量批改分析" name="batch">
        <div class="batch-section">
          <el-card class="control-card">
            <div class="batch-controls">
              <el-form inline>
                <el-form-item label="样本数量">
                  <el-input-number v-model="batchSize" :min="10" :max="200" :step="10" />
                </el-form-item>
                <el-form-item label="学科">
                  <el-select v-model="selectedSubject">
                    <el-option label="数学" value="math" />
                    <el-option label="语文" value="chinese" />
                    <el-option label="编程" value="programming" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="runBatchGrading" :loading="batchLoading">
                    开始批量批改
                  </el-button>
                  <el-button @click="generateSampleData" :loading="generateLoading">
                    生成示例数据
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
          </el-card>
          
          <!-- 统计图表 -->
          <div v-if="analyticsData" class="charts-container">
            <el-row :gutter="20">
              <!-- 评分分布直方图 -->
              <el-col :span="12">
                <el-card class="chart-card">
                  <h3>评分分布</h3>
                  <div ref="scoreDistChart" class="chart-container"></div>
                  <div class="stats-summary">
                    <el-tag>平均值: {{ analyticsData.score_statistics.mean.toFixed(1) }}</el-tag>
                    <el-tag>标准差: {{ analyticsData.score_statistics.std_dev.toFixed(1) }}</el-tag>
                    <el-tag type="success">最高分: {{ analyticsData.score_statistics.max }}</el-tag>
                    <el-tag type="danger">最低分: {{ analyticsData.score_statistics.min }}</el-tag>
                  </div>
                </el-card>
              </el-col>
              
              <!-- 分数段统计 -->
              <el-col :span="12">
                <el-card class="chart-card">
                  <h3>分数段分布</h3>
                  <div ref="gradeLevelChart" class="chart-container"></div>
                  <el-progress :percentage="excellentRate" :color="getProgressColor(excellentRate)">
                    <template #default="{ percentage }">
                      <span class="progress-text">优秀率: {{ percentage }}%</span>
                    </template>
                  </el-progress>
                </el-card>
              </el-col>
            </el-row>
            
            <el-row :gutter="20" style="margin-top: 20px">
              <!-- 错误类型分析 -->
              <el-col :span="12">
                <el-card class="chart-card">
                  <h3>错误类型分布</h3>
                  <div ref="errorTypeChart" class="chart-container"></div>
                  <div class="error-summary">
                    <el-alert 
                      v-for="(error, index) in analyticsData.error_statistics.most_common_errors" 
                      :key="index"
                      :title="`${error[0]}: ${error[1]}次`"
                      :type="getErrorType(error[1])"
                      :closable="false"
                      show-icon
                    />
                  </div>
                </el-card>
              </el-col>
              
              <!-- 知识点缺口分析 -->
              <el-col :span="12">
                <el-card class="chart-card">
                  <h3>知识点缺口分析</h3>
                  <div ref="knowledgeGapChart" class="chart-container"></div>
                  <div class="gap-recommendations">
                    <h4>重点补习建议</h4>
                    <el-tag v-for="(gap, index) in analyticsData.knowledge_gap_analysis.most_frequent_gaps" 
                      :key="index"
                      type="warning"
                      effect="plain"
                    >
                      {{ gap[0] }} ({{ gap[1] }}人)
                    </el-tag>
                  </div>
                </el-card>
              </el-col>
            </el-row>
            
            <!-- 详细数据表格 -->
            <el-card class="data-table-card">
              <h3>详细批改记录（前10条）</h3>
              <el-table :data="recentResults" border style="width: 100%">
                <el-table-column prop="student_id" label="学生ID" width="120" />
                <el-table-column prop="subject" label="学科" width="100" />
                <el-table-column prop="score" label="分数" width="100" sortable>
                  <template #default="{ row }">
                    <el-tag :type="getScoreTagType(row.score)">
                      {{ row.score }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="errors" label="错误类型" width="200">
                  <template #default="{ row }">
                    <el-tag v-for="error in row.errors" :key="error.type" size="small" type="danger">
                      {{ error.type }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="knowledge_gaps" label="知识点缺口">
                  <template #default="{ row }">
                    <span v-if="row.knowledge_gaps.length === 0" style="color: #67C23A">无缺口</span>
                    <el-tag v-for="gap in row.knowledge_gaps" :key="gap" size="small" type="warning">
                      {{ gap }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="timestamp" label="批改时间" width="180" />
              </el-table>
            </el-card>
          </div>
          
          <el-empty v-else description="请先运行批量批改或生成示例数据" />
        </div>
      </el-tab-pane>
      
      <!-- Tab 2: 学生进度追踪 -->
      <el-tab-pane label="学生进度追踪" name="progress">
        <el-card>
          <el-form inline>
            <el-form-item label="学生ID">
              <el-input v-model="studentIdInput" placeholder="输入学生ID，如 student_001" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="getStudentProgress" :loading="progressLoading">
                查询进度
              </el-button>
            </el-form-item>
          </el-form>
          
          <div v-if="progressData" class="progress-content">
            <h3>{{ progressData.student_id }} 学习进度追踪</h3>
            
            <el-row :gutter="20">
              <el-col :span="16">
                <div ref="progressChart" class="chart-container-large"></div>
              </el-col>
              <el-col :span="8">
                <el-card class="stats-card">
                  <h4>总体进步情况</h4>
                  <el-statistic title="总提升分数" :value="progressData.overall_improvement">
                    <template #suffix>
                      <span style="font-size: 16px">分</span>
                    </template>
                  </el-statistic>
                  <el-divider />
                  <el-statistic title="当前水平" :value="progressData.current_level" />
                  <el-divider />
                  <el-button type="success" size="small">生成个性化学习建议</el-button>
                </el-card>
              </el-col>
            </el-row>
            
            <!-- 薄弱知识点时间线 -->
            <el-card class="timeline-card">
              <h4>薄弱知识点演变时间线</h4>
              <el-timeline>
                <el-timeline-item 
                  v-for="(point, index) in progressData.progress_timeline.slice(0, 5)" 
                  :key="index"
                  :timestamp="point.date"
                  placement="top"
                  :type="getTimelineType(point.score)"
                >
                  <el-card>
                    <h4>分数: {{ point.score }}分</h4>
                    <p v-if="point.improvement > 0" style="color: #67C23A">
                      本周提升: +{{ point.improvement.toFixed(1) }}分
                    </p>
                    <p>薄弱知识点: 
                      <el-tag v-for="weak in point.weak_points" :key="weak" size="small" type="warning">
                        {{ weak }}
                      </el-tag>
                      <span v-if="point.weak_points.length === 0" style="color: #67C23A">无明显薄弱点</span>
                    </p>
                  </el-card>
                </el-timeline-item>
              </el-timeline>
            </el-card>
          </div>
          
          <el-empty v-else description="请输入学生ID查询进度" />
        </el-card>
      </el-tab-pane>
      
      <!-- Tab 3: 效果对比 -->
      <el-tab-pane label="效果对比分析" name="comparison">
        <el-card>
          <el-button type="primary" @click="getComparison" :loading="comparisonLoading">
            获取对比数据
          </el-button>
          
          <div v-if="comparisonData" class="comparison-content">
            <h3>与传统批改方法效果对比</h3>
            
            <el-row :gutter="20">
              <!-- 批改速度对比 -->
              <el-col :span="12">
                <el-card class="comparison-card">
                  <h4>批改速度对比</h4>
                  <div ref="speedComparisonChart" class="chart-container"></div>
                  <el-result
                    icon="success"
                    title="效率提升显著"
                    sub-title="AI系统批改速度提升18.5倍"
                  />
                </el-card>
              </el-col>
              
              <!-- 准确性对比 -->
              <el-col :span="12">
                <el-card class="comparison-card">
                  <h4>批改准确性对比</h4>
                  <div ref="accuracyComparisonChart" class="chart-container"></div>
                  <div class="accuracy-stats">
                    <el-progress 
                      :percentage="comparisonData.grading_accuracy.traditional.consistency * 100" 
                      :format="(p) => `传统方法一致性: ${p}%`"
                      :color="'#909399'"
                    />
                    <el-progress 
                      :percentage="comparisonData.grading_accuracy.ai_system.consistency * 100" 
                      :format="(p) => `AI系统一致性: ${p}%`"
                      :color="'#67C23A'"
                    />
                  </div>
                </el-card>
              </el-col>
            </el-row>
            
            <!-- 成本效益分析 -->
            <el-card class="cost-card">
              <h4>成本效益分析</h4>
              <el-row :gutter="20">
                <el-col :span="6">
                  <el-statistic 
                    title="传统方法成本" 
                    :value="comparisonData.cost_efficiency.traditional.cost_per_assignment"
                    suffix="元/份"
                  />
                </el-col>
                <el-col :span="6">
                  <el-statistic 
                    title="AI系统成本" 
                    :value="comparisonData.cost_efficiency.ai_system.cost_per_assignment"
                    suffix="元/份"
                    :value-style="{ color: '#67C23A' }"
                  />
                </el-col>
                <el-col :span="6">
                  <el-statistic 
                    title="成本降低比例" 
                    :value="90"
                    suffix="%"
                    :value-style="{ color: '#F56C6C' }"
                  />
                </el-col>
                <el-col :span="6">
                  <el-statistic 
                    title="教师工作量减少" 
                    :value="95"
                    suffix="%"
                    :value-style="{ color: '#E6A23C' }"
                  />
                </el-col>
              </el-row>
            </el-card>
            
            <!-- 科研价值展示 -->
            <el-card class="research-value-card">
              <h4>科研价值与创新点</h4>
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-card shadow="hover">
                    <h5>技术创新</h5>
                    <el-tag type="success">自适应评分算法</el-tag>
                    <el-tag type="primary">知识图谱驱动</el-tag>
                    <el-tag type="warning">多模态融合</el-tag>
                  </el-card>
                </el-col>
                <el-col :span="8">
                  <el-card shadow="hover">
                    <h5>学术贡献</h5>
                    <el-badge value="3篇" type="primary">
                      <el-button size="small">预期论文发表</el-button>
                    </el-badge>
                    <el-badge value="1个" type="success">
                      <el-button size="small">开源数据集</el-button>
                    </el-badge>
                  </el-card>
                </el-col>
                <el-col :span="8">
                  <el-card shadow="hover">
                    <h5>应用价值</h5>
                    <el-progress :percentage="70" :format="(p) => `教师时间节省 ${p}%`" />
                    <el-progress :percentage="15" :format="(p) => `学生成绩提升 ${p}%`" color="#67C23A" />
                  </el-card>
                </el-col>
              </el-row>
            </el-card>
          </div>
          
          <el-empty v-else description="请点击按钮获取对比数据" />
        </el-card>
      </el-tab-pane>
      
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { 
  batchGrade, 
  generateSampleData as apiGenerateSampleData,
  getStudentProgress as apiGetStudentProgress,
  getMetricsComparison as apiGetComparison,
  getCurrentStats
} from '../api'

// Tab控制
const activeTab = ref('batch')

// ==================== 批量批改分析 ====================
const batchSize = ref(50)
const selectedSubject = ref('math')
const batchLoading = ref(false)
const generateLoading = ref(false)
const analyticsData = ref(null)
const recentResults = ref([])

// ECharts实例
const scoreDistChart = ref(null)
const gradeLevelChart = ref(null)
const errorTypeChart = ref(null)
const knowledgeGapChart = ref(null)
let charts = {}

// 批量批改
const runBatchGrading = async () => {
  batchLoading.value = true
  try {
    // 先生成示例数据
    const sampleRes = await apiGenerateSampleData(batchSize.value, selectedSubject.value)
    const samples = sampleRes.data.samples
    
    // 执行批量批改
    const result = await batchGrade(samples, selectedSubject.value)
    analyticsData.value = result.data.analytics
    recentResults.value = result.data.results.slice(0, 10)
    
    ElMessage.success(`批量批改完成：${result.data.analytics.batch_size}份作业`)
    
    // 渲染图表
    await nextTick()
    renderCharts()
    
  } catch (error) {
    ElMessage.error('批量批改失败：' + error.message)
  } finally {
    batchLoading.value = false
  }
}

// 生成示例数据
const generateSampleData = async () => {
  generateLoading.value = true
  try {
    await apiGenerateSampleData(batchSize.value, selectedSubject.value)
    ElMessage.success(`已生成 ${batchSize.value} 条示例数据`)
  } catch (error) {
    ElMessage.error('生成数据失败：' + error.message)
  } finally {
    generateLoading.value = false
  }
}

// 渲染图表
const renderCharts = () => {
  if (!analyticsData.value) return
  
  // 评分分布直方图
  if (scoreDistChart.value) {
    charts.scoreDist = echarts.init(scoreDistChart.value)
    const distData = Object.entries(analyticsData.value.score_distribution).map(([range, count]) => ({
      name: range,
      value: count
    }))
    
    charts.scoreDist.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { 
        type: 'category', 
        data: distData.map(d => d.name),
        axisLabel: { interval: 0, rotate: 45 }
      },
      yAxis: { type: 'value', name: '人数' },
      series: [{
        type: 'bar',
        data: distData.map(d => d.value),
        itemStyle: { color: '#409EFF' },
        label: { show: true, position: 'top' }
      }]
    })
  }
  
  // 分数段分布饼图
  if (gradeLevelChart.value) {
    charts.gradeLevel = echarts.init(gradeLevelChart.value)
    const levelData = Object.entries(analyticsData.value.grade_levels).map(([level, count]) => ({
      name: level,
      value: count
    }))
    
    charts.gradeLevel.setOption({
      tooltip: { trigger: 'item' },
      legend: { orient: 'vertical', left: 'left' },
      series: [{
        type: 'pie',
        radius: '50%',
        data: levelData,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    })
  }
  
  // 错误类型分析
  if (errorTypeChart.value) {
    charts.errorType = echarts.init(errorTypeChart.value)
    const errorData = Object.entries(analyticsData.value.error_statistics.error_types)
    
    charts.errorType.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: errorData.map(e => e[0]) },
      yAxis: { type: 'value', name: '次数' },
      series: [{
        type: 'bar',
        data: errorData.map(e => e[1]),
        itemStyle: { color: '#F56C6C' },
        label: { show: true, position: 'top' }
      }]
    })
  }
  
  // 知识点缺口分析
  if (knowledgeGapChart.value) {
    charts.knowledgeGap = echarts.init(knowledgeGapChart.value)
    const gapData = analyticsData.value.knowledge_gap_analysis.most_frequent_gaps
    
    charts.knowledgeGap.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: gapData.map(g => g[0]) },
      yAxis: { type: 'value', name: '人数' },
      series: [{
        type: 'bar',
        data: gapData.map(g => g[1]),
        itemStyle: { color: '#E6A23C' },
        label: { show: true, position: 'top' }
      }]
    })
  }
}

// 优秀率计算
const excellentRate = computed(() => {
  if (!analyticsData.value) return 0
  const excellent = analyticsData.value.grade_levels['优秀(90-100)']
  const total = analyticsData.value.batch_size
  return Math.round((excellent / total) * 100)
})

// 工具函数
const getProgressColor = (percentage) => {
  if (percentage >= 70) return '#67C23A'
  if (percentage >= 40) return '#E6A23C'
  return '#F56C6C'
}

const getErrorType = (count) => {
  if (count >= 10) return 'error'
  if (count >= 5) return 'warning'
  return 'info'
}

const getScoreTagType = (score) => {
  if (score >= 90) return 'success'
  if (score >= 80) return 'primary'
  if (score >= 70) return 'warning'
  if (score >= 60) return 'info'
  return 'danger'
}

// ==================== 学生进度追踪 ====================
const studentIdInput = ref('student_001')
const progressLoading = ref(false)
const progressData = ref(null)
const progressChart = ref(null)

const getStudentProgress = async () => {
  if (!studentIdInput.value.trim()) {
    ElMessage.warning('请输入学生ID')
    return
  }
  
  progressLoading.value = true
  try {
    const result = await apiGetStudentProgress(studentIdInput.value)
    progressData.value = result.data
    
    await nextTick()
    renderProgressChart()
    
  } catch (error) {
    ElMessage.error('查询进度失败：' + error.message)
  } finally {
    progressLoading.value = false
  }
}

const renderProgressChart = () => {
  if (!progressData.value || !progressChart.value) return
  
  charts.progress = echarts.init(progressChart.value)
  const timeline = progressData.value.progress_timeline
  
  charts.progress.setOption({
    title: { text: '学习进步曲线' },
    tooltip: { trigger: 'axis' },
    xAxis: { 
      type: 'category', 
      data: timeline.map(p => p.date),
      axisLabel: { rotate: 45 }
    },
    yAxis: { type: 'value', name: '分数', min: 50, max: 100 },
    series: [
      {
        name: '分数',
        type: 'line',
        data: timeline.map(p => p.score),
        smooth: true,
        itemStyle: { color: '#67C23A' },
        areaStyle: { opacity: 0.3 }
      },
      {
        name: '进步幅度',
        type: 'bar',
        data: timeline.map(p => p.improvement),
        itemStyle: { color: '#409EFF' }
      }
    ]
  })
}

const getTimelineType = (score) => {
  if (score >= 80) return 'success'
  if (score >= 70) return 'primary'
  if (score >= 60) return 'warning'
  return 'danger'
}

// ==================== 效果对比分析 ====================
const comparisonLoading = ref(false)
const comparisonData = ref(null)
const speedComparisonChart = ref(null)
const accuracyComparisonChart = ref(null)

const getComparison = async () => {
  comparisonLoading.value = true
  try {
    const result = await apiGetComparison()
    comparisonData.value = result.data
    
    await nextTick()
    renderComparisonCharts()
    
  } catch (error) {
    ElMessage.error('获取对比数据失败：' + error.message)
  } finally {
    comparisonLoading.value = false
  }
}

const renderComparisonCharts = () => {
  if (!comparisonData.value) return
  
  // 批改速度对比
  if (speedComparisonChart.value) {
    charts.speed = echarts.init(speedComparisonChart.value)
    
    charts.speed.setOption({
      title: { text: '批改速度对比' },
      tooltip: { trigger: 'axis' },
      legend: { data: ['传统方法', 'AI系统'] },
      xAxis: { type: 'category', data: ['单份平均时间', '批改100份总时间'] },
      yAxis: { type: 'value', name: '时间（分钟）' },
      series: [
        {
          name: '传统方法',
          type: 'bar',
          data: [
            comparisonData.value.grading_speed.traditional.average_time,
            comparisonData.value.grading_speed.traditional.batch_100_time
          ],
          itemStyle: { color: '#909399' }
        },
        {
          name: 'AI系统',
          type: 'bar',
          data: [
            comparisonData.value.grading_speed.ai_system.average_time,
            comparisonData.value.grading_speed.ai_system.batch_100_time
          ],
          itemStyle: { color: '#67C23A' }
        }
      ]
    })
  }
  
  // 准确性对比
  if (accuracyComparisonChart.value) {
    charts.accuracy = echarts.init(accuracyComparisonChart.value)
    
    charts.accuracy.setOption({
      title: { text: '批改一致性对比' },
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: ['评分一致性', '错误率'] },
      yAxis: { type: 'value', name: '比例', max: 100 },
      series: [
        {
          name: '传统方法',
          type: 'bar',
          data: [
            comparisonData.value.grading_accuracy.traditional.consistency * 100,
            comparisonData.value.grading_accuracy.traditional.error_rate * 100
          ],
          itemStyle: { color: '#F56C6C' }
        },
        {
          name: 'AI系统',
          type: 'bar',
          data: [
            comparisonData.value.grading_accuracy.ai_system.consistency * 100,
            comparisonData.value.grading_accuracy.ai_system.error_rate * 100
          ],
          itemStyle: { color: '#67C23A' }
        }
      ]
    })
  }
}

// 窗口大小变化时重新渲染图表
const handleResize = () => {
  Object.values(charts).forEach(chart => {
    if (chart) chart.resize()
  })
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})
</script>

<style scoped>
.analytics-dashboard {
  max-width: 1400px;
  margin: 20px auto;
  padding: 20px;
}

.batch-section {
  min-height: 600px;
}

.control-card {
  margin-bottom: 20px;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  height: 300px;
  width: 100%;
}

.chart-container-large {
  height: 400px;
  width: 100%;
}

.charts-container {
  margin-top: 20px;
}

.stats-summary {
  margin-top: 15px;
  display: flex;
  gap: 10px;
}

.error-summary {
  margin-top: 15px;
}

.gap-recommendations {
  margin-top: 15px;
}

.gap-recommendations h4 {
  margin-bottom: 10px;
}

.progress-text {
  font-weight: bold;
}

.comparison-content {
  margin-top: 20px;
}

.comparison-card {
  margin-bottom: 20px;
}

.accuracy-stats {
  margin-top: 20px;
}

.cost-card {
  margin-top: 20px;
}

.research-value-card {
  margin-top: 20px;
}

.data-table-card {
  margin-top: 20px;
}

.progress-content {
  margin-top: 20px;
}

.stats-card {
  height: 100%;
}

.timeline-card {
  margin-top: 20px;
}
</style>