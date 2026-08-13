<template>
  <div class="causal-analysis">
    <el-card shadow="never" class="header-card">
      <div class="header-row">
        <div>
          <h2 class="title">因果推理引擎</h2>
          <p class="subtitle">AI + Education + Causal Inference — 从"改对错"到"找根因"</p>
        </div>
        <div class="header-actions">
          <el-select v-model="currentSubject" placeholder="选择学科" style="width: 140px" @change="loadGraph">
            <el-option label="数学" value="math" />
            <el-option label="语文" value="chinese" />
            <el-option label="编程" value="programming" />
          </el-select>
          <el-button type="primary" :icon="Refresh" @click="loadAll">刷新</el-button>
        </div>
      </div>
    </el-card>

    <el-tabs v-model="activeTab" class="main-tabs">
      <!-- ============ 因果图谱 ============ -->
      <el-tab-pane label="因果知识图谱" name="graph">
        <el-row :gutter="16">
          <el-col :span="16">
            <el-card shadow="never">
              <template #header>
                <div class="card-header">
                  <span>知识点因果网络</span>
                  <el-tag size="small" type="info">{{ graphData.nodes?.length || 0 }} 节点 / {{ graphData.edges?.length || 0 }} 因果边</el-tag>
                </div>
              </template>
              <div ref="graphChartRef" class="graph-chart"></div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="never" class="node-detail-card">
              <template #header><span>节点详情</span></template>
              <div v-if="selectedNode">
                <el-descriptions :column="1" border size="small">
                  <el-descriptions-item label="知识点">{{ selectedNode.name }}</el-descriptions-item>
                  <el-descriptions-item label="类别">
                    <el-tag size="small">{{ selectedNode.category }}</el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="难度">
                    <el-rate :model-value="selectedNode.difficulty" disabled size="small" />
                  </el-descriptions-item>
                  <el-descriptions-item label="掌握度">
                    <el-progress :percentage="Math.round(selectedNode.mastery * 100)" :color="masteryColor(selectedNode.mastery)" />
                  </el-descriptions-item>
                  <el-descriptions-item label="描述">{{ selectedNode.description }}</el-descriptions-item>
                </el-descriptions>
                <el-divider content-position="center">因果关系</el-divider>
                <div v-if="nodeRelations.length" class="relation-list">
                  <div v-for="rel in nodeRelations" :key="rel.target" class="relation-item">
                    <el-tag :type="rel.type === 'cause' ? 'danger' : 'success'" size="small">
                      {{ rel.type === 'cause' ? '导致' : '被导致' }}
                    </el-tag>
                    <span class="rel-name">{{ rel.name }}</span>
                    <span class="rel-weight">效应: {{ rel.weight.toFixed(2) }}</span>
                  </div>
                </div>
                <el-empty v-else description="无直接因果关系" :image-size="60" />
              </div>
              <el-empty v-else description="点击左侧图谱节点查看详情" :image-size="80" />
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- ============ 根因诊断 ============ -->
      <el-tab-pane label="根因诊断" name="diagnose">
        <el-row :gutter="16">
          <el-col :span="10">
            <el-card shadow="never">
              <template #header><span>诊断输入</span></template>
              <el-form label-position="top">
                <el-form-item label="学生ID">
                  <el-input v-model="diagForm.student_id" placeholder="如 student_001" />
                </el-form-item>
                <el-form-item label="错误知识点">
                  <el-select v-model="diagForm.error_nodes" multiple filterable placeholder="选择学生出错的知识点" style="width: 100%">
                    <el-option v-for="n in graphData.nodes" :key="n.id" :label="n.name" :value="n.id" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" :loading="diagLoading" @click="runDiagnose">运行根因分析</el-button>
                  <el-button @click="loadDemoDiagnose">载入示例</el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>
          <el-col :span="14">
            <el-card shadow="never" v-if="diagResult">
              <template #header>
                <div class="card-header">
                  <span>诊断结果</span>
                  <el-tag :type="diagResult.confidence > 0.7 ? 'success' : 'warning'" size="small">
                    置信度 {{ (diagResult.confidence * 100).toFixed(0) }}%
                  </el-tag>
                </div>
              </template>
              <el-alert :type="diagResult.confidence > 0.7 ? 'success' : 'warning'" :closable="false" show-icon
                :title="`根因: ${diagResult.root_cause_name}`"
                :description="diagResult.root_cause_description" style="margin-bottom: 16px" />
              <div class="diag-chain">
                <h4>因果链路</h4>
                <div v-for="(chain, cidx) in diagResult.causal_chain" :key="cidx" class="chain-flow" style="margin-bottom: 12px">
                  <template v-for="(name, nidx) in chain.node_names" :key="nidx">
                    <div class="chain-node" :class="{ 'root-node': nidx === 0 }">
                      <div class="chain-name">{{ name }}</div>
                      <div class="chain-meta">
                        <span v-if="nidx === chain.node_names.length - 1">效应 {{ (chain.effect * 100).toFixed(1) }}%</span>
                      </div>
                    </div>
                    <el-icon v-if="nidx < chain.node_names.length - 1" class="chain-arrow"><ArrowRight /></el-icon>
                  </template>
                </div>
              </div>
              <el-divider />
              <div class="diag-intervention">
                <h4>推荐干预方案</h4>
                <el-timeline>
                  <el-timeline-item v-for="(iv, idx) in diagResult.interventions" :key="idx"
                    :type="iv.priority === 'high' ? 'danger' : iv.priority === 'medium' ? 'warning' : 'info'"
                    :timestamp="iv.estimated_time">
                    <h5>{{ iv.action }}</h5>
                    <p>{{ iv.detail }}</p>
                    <p>预期提升: +{{ iv.expected_improvement.toFixed(0) }}分</p>
                  </el-timeline-item>
                </el-timeline>
              </div>
            </el-card>
            <el-empty v-else description="运行根因分析后查看结果" :image-size="100" />
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- ============ 反事实推理 ============ -->
      <el-tab-pane label="反事实推理" name="counterfactual">
        <el-row :gutter="16">
          <el-col :span="10">
            <el-card shadow="never">
              <template #header><span>反事实分析 (What-If)</span></template>
              <el-alert type="info" :closable="false" show-icon style="margin-bottom: 16px"
                title="反事实推理：假设某知识点掌握度改变，预测对学生整体成绩的影响" />
              <el-form label-position="top">
                <el-form-item label="学生ID">
                  <el-input v-model="cfForm.student_id" placeholder="如 student_001" />
                </el-form-item>
                <el-form-item label="干预知识点">
                  <el-select v-model="cfForm.target_node" filterable placeholder="选择干预的知识点" style="width: 100%">
                    <el-option v-for="n in graphData.nodes" :key="n.id" :label="n.name" :value="n.id" />
                  </el-select>
                </el-form-item>
                <el-form-item label="假设掌握度">
                  <el-slider v-model="cfForm.intervention_mastery" :min="0" :max="100" :step="5" show-input :format-value="v => v + '%'" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" :loading="cfLoading" @click="runCounterfactual">执行反事实推理</el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>
          <el-col :span="14">
            <el-card shadow="never" v-if="cfResult">
              <template #header><span>反事实推理结果</span></template>
              <div class="cf-comparison">
                <div class="cf-col cf-before">
                  <h4>当前掌握度</h4>
                  <div class="cf-score">{{ (cfResult.original_mastery * 100).toFixed(0) }}%</div>
                  <p>{{ cfResult.target_node_name }}</p>
                </div>
                <el-icon class="cf-arrow"><Right /></el-icon>
                <div class="cf-col cf-after">
                  <h4>干预后掌握度</h4>
                  <div class="cf-score">{{ (cfResult.intervention_value * 100).toFixed(0) }}%</div>
                  <p>do({{ cfResult.target_node_name }} = {{ (cfResult.intervention_value * 100).toFixed(0) }}%)</p>
                </div>
                <div class="cf-col cf-delta">
                  <h4>下游总预期提升</h4>
                  <div class="cf-score positive">
                    +{{ (cfResult.total_expected_improvement * 100).toFixed(1) }}%
                  </div>
                  <p>平均掌握度提升</p>
                </div>
              </div>
              <el-divider />
              <h4>下游知识点预测变化</h4>
              <div ref="cfChartRef" class="cf-chart"></div>
              <el-divider />
              <el-alert type="success" :closable="false" show-icon
                :title="`干预结论：将「${cfResult.target_node_name}」掌握度从 ${(cfResult.original_mastery * 100).toFixed(0)}% 提升至 ${(cfResult.intervention_value * 100).toFixed(0)}%，下游 ${cfResult.affected_count} 个知识点预计平均掌握度提升 ${(cfResult.total_expected_improvement * 100).toFixed(1)}%`" />
            </el-card>
            <el-empty v-else description="执行反事实推理后查看结果" :image-size="100" />
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- ============ 因果效应估计 ============ -->
      <el-tab-pane label="因果效应估计" name="effect">
        <el-card shadow="never">
          <template #header><span>知识点间因果效应估计</span></template>
          <el-form inline style="margin-bottom: 16px">
            <el-form-item label="原因知识点">
              <el-select v-model="effectForm.cause" filterable placeholder="选择" style="width: 180px">
                <el-option v-for="n in graphData.nodes" :key="n.id" :label="n.name" :value="n.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="结果知识点">
              <el-select v-model="effectForm.effect" filterable placeholder="选择" style="width: 180px">
                <el-option v-for="n in graphData.nodes" :key="n.id" :label="n.name" :value="n.id" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="effectLoading" @click="runEffect">估计因果效应</el-button>
            </el-form-item>
          </el-form>
          <div v-if="effectResult" class="effect-result">
            <el-row :gutter="16">
              <el-col :span="8">
                <el-statistic title="直接因果效应" :value="effectResult.direct_effect" :precision="3" />
              </el-col>
              <el-col :span="8">
                <el-statistic title="间接因果效应" :value="effectResult.indirect_effect" :precision="3" />
              </el-col>
              <el-col :span="8">
                <el-statistic title="总因果效应" :value="effectResult.total_effect" :precision="3" />
              </el-col>
            </el-row>
            <el-divider />
            <el-alert :type="effectResult.significant ? 'success' : 'info'" :closable="false" show-icon
              :title="effectResult.interpretation" />
            <div v-if="effectResult.path_details?.length" style="margin-top: 16px">
              <h4>因果路径分解</h4>
              <el-table :data="effectResult.path_details" border size="small">
                <el-table-column prop="path" label="路径" min-width="200" />
                <el-table-column prop="effect" label="效应值" width="120" />
                <el-table-column prop="type" label="类型" width="100" />
              </el-table>
            </div>
          </div>
          <el-empty v-else description="选择两个知识点估计因果效应" :image-size="100" />
        </el-card>
      </el-tab-pane>

      <!-- ============ 学习路径推荐 ============ -->
      <el-tab-pane label="学习路径推荐" name="path">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-card shadow="never">
              <template #header><span>路径推荐输入</span></template>
              <el-form label-position="top">
                <el-form-item label="学生ID">
                  <el-input v-model="pathForm.student_id" placeholder="如 student_001" />
                </el-form-item>
                <el-form-item label="目标知识点">
                  <el-select v-model="pathForm.target_nodes" multiple filterable placeholder="选择目标" style="width: 100%">
                    <el-option v-for="n in graphData.nodes" :key="n.id" :label="n.name" :value="n.id" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" :loading="pathLoading" @click="runPath">推荐学习路径</el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>
          <el-col :span="16">
            <el-card shadow="never" v-if="pathResult">
              <template #header>
                <div class="card-header">
                  <span>推荐学习路径</span>
                  <el-tag size="small" type="success">预计提升 +{{ pathResult.estimated_improvement?.toFixed(0) }} 分</el-tag>
                </div>
              </template>
              <div class="path-flow">
                <template v-for="(step, idx) in pathResult.path" :key="idx">
                  <div class="path-node" :class="{ 'path-start': idx === 0, 'path-end': idx === pathResult.path.length - 1 }">
                    <div class="path-num">Step {{ idx + 1 }}</div>
                    <div class="path-name">{{ step.node_name }}</div>
                    <div class="path-meta">
                      <span>掌握度 {{ (step.current_mastery * 100).toFixed(0) }}%</span>
                      <span>→ 目标 {{ (step.target_mastery * 100).toFixed(0) }}%</span>
                    </div>
                    <div class="path-action">{{ step.action }}</div>
                  </div>
                  <el-icon v-if="idx < pathResult.path.length - 1" class="path-arrow"><ArrowRight /></el-icon>
                </template>
              </div>
              <el-divider />
              <h4>路径分析</h4>
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="总步骤">{{ pathResult.path?.length }}</el-descriptions-item>
                <el-descriptions-item label="预计耗时">{{ pathResult.estimated_time }}</el-descriptions-item>
                <el-descriptions-item label="因果依据">{{ pathResult.causal_basis }}</el-descriptions-item>
                <el-descriptions-item label="优先级策略">{{ pathResult.strategy }}</el-descriptions-item>
              </el-descriptions>
            </el-card>
            <el-empty v-else description="推荐学习路径后查看结果" :image-size="100" />
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- ============ 科研报告 ============ -->
      <el-tab-pane label="科研报告" name="report">
        <el-card shadow="never" v-if="reportData">
          <template #header>
            <div class="card-header">
              <span>因果推理科研报告</span>
              <el-button type="primary" size="small" :icon="Download" @click="exportReport">导出报告</el-button>
            </div>
          </template>
          <div class="report-content">
            <h3>{{ reportData.title }}</h3>
            <p class="report-meta">生成时间: {{ reportData.generated_at }}</p>

            <div v-for="(sec, idx) in reportData.sections" :key="idx" class="report-section">
              <h4>{{ sec.title }}</h4>
              <p v-if="sec.content">{{ sec.content }}</p>
              <ul v-if="sec.items">
                <li v-for="(item, i) in sec.items" :key="i">{{ item }}</li>
              </ul>
              <el-table v-if="sec.table" :data="sec.table.data" border size="small" style="margin-top: 8px">
                <el-table-column v-for="col in sec.table.columns" :key="col.key" :prop="col.key" :label="col.label" :width="col.width" />
              </el-table>
            </div>

            <el-divider />
            <div class="report-citation">
              <h4>引用格式</h4>
              <p>{{ reportData.citation }}</p>
            </div>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, ArrowRight, Right, Download } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { causalApi } from '../api/index.js'

const currentSubject = ref('math')
const activeTab = ref('graph')
const graphData = ref({})
const selectedNode = ref(null)
const nodeRelations = ref([])
const graphChartRef = ref(null)
const cfChartRef = ref(null)
let graphChart = null
let cfChart = null

// 诊断
const diagForm = reactive({ student_id: 'student_001', error_nodes: [] })
const diagResult = ref(null)
const diagLoading = ref(false)

// 反事实
const cfForm = reactive({ student_id: 'student_001', target_node: '', intervention_mastery: 80 })
const cfResult = ref(null)
const cfLoading = ref(false)

// 因果效应
const effectForm = reactive({ cause: '', effect: '' })
const effectResult = ref(null)
const effectLoading = ref(false)

// 学习路径
const pathForm = reactive({ student_id: 'student_001', target_nodes: [] })
const pathResult = ref(null)
const pathLoading = ref(false)

// 报告
const reportData = ref(null)

const masteryColor = (m) => {
  if (m >= 0.8) return '#67c23a'
  if (m >= 0.6) return '#e6a23c'
  return '#f56c6c'
}

// 加载因果图谱
async function loadGraph() {
  try {
    const res = await causalApi.getGraph(currentSubject.value)
    graphData.value = res.data
    await nextTick()
    renderGraph()
  } catch (e) {
    ElMessage.error('加载图谱失败: ' + (e.response?.data?.detail || e.message))
  }
}

// 渲染图谱
function renderGraph() {
  if (!graphChartRef.value) return
  if (graphChart) graphChart.dispose()
  graphChart = echarts.init(graphChartRef.value)

  const categories = [
    { name: '基础概念' },
    { name: '运算技能' },
    { name: '应用能力' },
    { name: '高阶思维' },
  ]
  const catMap = { '基础概念': 0, '运算技能': 1, '应用能力': 2, '高阶思维': 3 }

  const nodes = (graphData.value.nodes || []).map(n => ({
    id: n.id,
    name: n.name,
    symbolSize: 20 + n.difficulty * 12,
    category: catMap[n.category] ?? 0,
    itemStyle: {
      color: masteryColor(n.mastery),
      opacity: 0.85,
    },
    label: { show: true, fontSize: 11 },
    value: n.mastery,
  }))

  const edges = (graphData.value.edges || []).map(e => ({
    source: e.source,
    target: e.target,
    lineStyle: {
      width: 1 + Math.abs(e.weight) * 4,
      color: e.weight > 0 ? '#409eff' : '#f56c6c',
      curveness: 0.2,
    },
    label: {
      show: true,
      formatter: e.weight?.toFixed(2),
      fontSize: 9,
    },
  }))

  graphChart.setOption({
    tooltip: {
      formatter: (p) => {
        if (p.dataType === 'node') return `${p.data.name}<br/>掌握度: ${(p.data.value * 100).toFixed(0)}%`
        if (p.dataType === 'edge') return `因果效应: ${p.data.label?.formatter || ''}`
        return p.name
      },
    },
    legend: [{ data: categories.map(c => c.name), bottom: 10 }],
    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      draggable: true,
      force: { repulsion: 300, edgeLength: 120, gravity: 0.1 },
      categories,
      nodes,
      edges,
      edgeSymbol: ['none', 'arrow'],
      edgeSymbolSize: 8,
      emphasis: { focus: 'adjacency', lineStyle: { width: 4 } },
    }],
  })

  graphChart.on('click', (params) => {
    if (params.dataType === 'node') {
      selectNode(params.data.id)
    }
  })
}

// 选择节点
function selectNode(nodeId) {
  const node = (graphData.value.nodes || []).find(n => n.id === nodeId)
  if (!node) return
  selectedNode.value = node
  const edges = graphData.value.edges || []
  nodeRelations.value = []
  edges.forEach(e => {
    if (e.source === nodeId) {
      const t = graphData.value.nodes.find(n => n.id === e.target)
      nodeRelations.value.push({ type: 'cause', name: t?.name || e.target, weight: e.weight, target: e.target })
    }
    if (e.target === nodeId) {
      const s = graphData.value.nodes.find(n => n.id === e.source)
      nodeRelations.value.push({ type: 'caused', name: s?.name || e.source, weight: e.weight, target: e.source })
    }
  })
}

// 根因诊断
async function runDiagnose() {
  if (!diagForm.error_nodes.length) { ElMessage.warning('请选择错误知识点'); return }
  diagLoading.value = true
  try {
    const res = await causalApi.diagnose({
      ...diagForm,
      subject: currentSubject.value,
    })
    const data = res.data
    // 映射后端字段到前端期望格式
    const topCause = data.root_causes?.[0] || {}
    diagResult.value = {
      ...data,
      root_cause_name: topCause.node_name || '未知',
      root_cause_description: topCause.description || '无描述',
      causal_chain: (data.causal_chains || []).map(c => ({
        node_names: c.chain,
        node_ids: c.chain_ids,
        effect: c.causal_effect,
      })),
      interventions: (data.intervention_priority || []).map(iv => ({
        priority: iv.priority <= 2 ? 'high' : iv.priority <= 4 ? 'medium' : 'low',
        action: iv.recommendation || `学习${iv.target_name || '相关知识'}`,
        detail: `当前掌握度 ${(iv.current_mastery * 100).toFixed(0)}%，影响 ${iv.affected_count} 个知识点`,
        estimated_time: `约${Math.max(1, Math.round((1 - iv.current_mastery) * 10))}天`,
        expected_improvement: (iv.expected_impact || 0) * 100,
      })),
    }
    ElMessage.success('根因分析完成')
  } catch (e) {
    ElMessage.error('诊断失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    diagLoading.value = false
  }
}

function loadDemoDiagnose() {
  diagForm.student_id = 'student_001'
  diagForm.error_nodes = ['k_equation_quadratic', 'k_function_quadratic']
  ElMessage.info('已载入示例数据，点击"运行根因分析"')
}

// 反事实推理
async function runCounterfactual() {
  if (!cfForm.target_node) { ElMessage.warning('请选择干预知识点'); return }
  cfLoading.value = true
  try {
    const res = await causalApi.counterfactual({
      ...cfForm,
      intervention_mastery: cfForm.intervention_mastery / 100,
      subject: currentSubject.value,
    })
    const data = res.data
    cfResult.value = {
      ...data,
      impacted_nodes: (data.detailed_results || []).map(r => ({
        node_name: r.node_name,
        node_id: r.node_id,
        current_mastery: r.original_mastery,
        predicted_mastery: r.predicted_mastery,
        improvement: r.improvement,
      })),
    }
    await nextTick()
    renderCfChart()
    ElMessage.success('反事实推理完成')
  } catch (e) {
    ElMessage.error('推理失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    cfLoading.value = false
  }
}

function renderCfChart() {
  if (!cfChartRef.value) return
  if (cfChart) cfChart.dispose()
  cfChart = echarts.init(cfChartRef.value)
  const impacted = cfResult.value.impacted_nodes || []
  cfChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['当前掌握度', '干预后预测'], bottom: 0 },
    xAxis: { type: 'category', data: impacted.map(n => n.node_name), axisLabel: { rotate: 30 } },
    yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
    series: [
      { name: '当前掌握度', type: 'bar', data: impacted.map(n => +(n.current_mastery * 100).toFixed(1)), itemStyle: { color: '#909399' } },
      { name: '干预后预测', type: 'bar', data: impacted.map(n => +(n.predicted_mastery * 100).toFixed(1)), itemStyle: { color: '#409eff' } },
    ],
  })
}

// 因果效应估计
async function runEffect() {
  if (!effectForm.cause || !effectForm.effect) { ElMessage.warning('请选择两个知识点'); return }
  effectLoading.value = true
  try {
    const res = await causalApi.estimateEffect(effectForm.cause, effectForm.effect, currentSubject.value)
    const data = res.data
    effectResult.value = {
      ...data,
      total_effect: data.total_causal_effect || 0,
      significant: (data.total_causal_effect || 0) >= 0.3,
      path_details: (data.paths || []).map(p => ({
        path: (p.path || []).join(' → '),
        effect: p.path_effect ?? p.avg_strength,
        type: p.length <= 2 ? '直接因果' : '间接因果',
      })),
    }
  } catch (e) {
    ElMessage.error('估计失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    effectLoading.value = false
  }
}

// 学习路径推荐
async function runPath() {
  if (!pathForm.target_nodes.length) { ElMessage.warning('请选择目标知识点'); return }
  pathLoading.value = true
  try {
    const res = await causalApi.learningPath({ ...pathForm, subject: currentSubject.value })
    const data = res.data
    // 映射后端字段到前端期望格式
    pathResult.value = {
      ...data,
      path: (data.learning_path || []).map(s => ({
        ...s,
        target_mastery: Math.min(1, s.current_mastery + 0.3),
        action: s.needs_learning ? `重点学习「${s.node_name}」，当前掌握度仅 ${(s.current_mastery * 100).toFixed(0)}%` : `巩固「${s.node_name}」，已基本掌握`,
      })),
      estimated_improvement: data.estimated_hours != null ? data.estimated_hours * 5 : 15,
      estimated_time: `约 ${data.estimated_hours || 5} 小时`,
      causal_basis: '基于因果知识图谱的拓扑排序与因果效应加权',
      strategy: '按因果层级排序，优先补足掌握度低的前提知识点',
    }
    ElMessage.success('路径推荐完成')
  } catch (e) {
    ElMessage.error('推荐失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    pathLoading.value = false
  }
}

// 科研报告
async function loadReport() {
  try {
    const res = await causalApi.report(currentSubject.value)
    reportData.value = res.data
  } catch (e) {
    ElMessage.error('加载报告失败')
  }
}

function exportReport() {
  const blob = new Blob([JSON.stringify(reportData.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `causal_report_${currentSubject.value}_${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('报告已导出')
}

async function loadAll() {
  await loadGraph()
  await loadReport()
}

watch(activeTab, (v) => {
  if (v === 'report' && !reportData.value) loadReport()
})

onMounted(() => {
  loadAll()
})
</script>

<style scoped>
.causal-analysis { padding: 0; }
.header-card { margin-bottom: 16px; }
.header-row { display: flex; justify-content: space-between; align-items: center; }
.title { margin: 0; font-size: 20px; }
.subtitle { margin: 4px 0 0; font-size: 13px; color: var(--el-text-color-secondary); }
.header-actions { display: flex; gap: 12px; }
.main-tabs { background: transparent; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.graph-chart { height: 500px; }
.node-detail-card { height: 100%; }
.relation-list { display: flex; flex-direction: column; gap: 8px; }
.relation-item { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.rel-name { flex: 1; }
.rel-weight { color: var(--el-text-color-secondary); font-size: 12px; }

/* 因果链 */
.chain-flow { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin: 16px 0; }
.chain-node { background: var(--el-fill-color-light); border-radius: 8px; padding: 12px 16px; text-align: center; min-width: 120px; }
.chain-node.root-node { background: var(--el-color-danger-light-9); border: 1px solid var(--el-color-danger-light-5); }
.chain-name { font-weight: 600; margin-bottom: 4px; }
.chain-meta { font-size: 12px; color: var(--el-text-color-secondary); display: flex; gap: 8px; justify-content: center; }
.chain-arrow { font-size: 20px; color: var(--el-text-color-secondary); }

/* 反事实 */
.cf-comparison { display: flex; align-items: center; justify-content: center; gap: 24px; }
.cf-col { text-align: center; flex: 1; }
.cf-score { font-size: 36px; font-weight: 700; margin: 8px 0; }
.cf-score.positive { color: var(--el-color-success); }
.cf-score.negative { color: var(--el-color-danger); }
.cf-arrow { font-size: 32px; color: var(--el-text-color-secondary); }
.cf-chart { height: 300px; }

/* 学习路径 */
.path-flow { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.path-node { background: var(--el-fill-color-light); border-radius: 8px; padding: 12px 16px; min-width: 140px; }
.path-node.path-start { border: 2px solid var(--el-color-warning); }
.path-node.path-end { border: 2px solid var(--el-color-success); }
.path-num { font-size: 12px; color: var(--el-text-color-secondary); }
.path-name { font-weight: 600; margin: 4px 0; }
.path-meta { font-size: 11px; color: var(--el-text-color-secondary); display: flex; gap: 8px; }
.path-action { font-size: 12px; margin-top: 4px; color: var(--el-color-primary); }
.path-arrow { font-size: 20px; color: var(--el-text-color-secondary); }

/* 报告 */
.report-content { line-height: 1.8; }
.report-meta { color: var(--el-text-color-secondary); font-size: 13px; }
.report-section { margin: 20px 0; }
.report-section h4 { border-left: 3px solid var(--el-color-primary); padding-left: 8px; }
.report-citation { background: var(--el-fill-color-light); padding: 12px; border-radius: 8px; }
.report-citation p { font-family: monospace; font-size: 13px; }
</style>
