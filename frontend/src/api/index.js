import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000
})

// ==================== 基础批改API ====================

// 同步批改
export const gradeSync = (content, maxTokens = 1024, subject = null) => {
  return api.post('/grade/sync', { content, max_tokens: maxTokens, subject })
}

// 流式批改（使用 fetch + ReadableStream）
export const gradeStreamFetch = async (content, maxTokens, onChunk, subject = null) => {
  const response = await fetch('/api/grade/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, max_tokens: maxTokens, subject })
  })
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n\n')
    for (let i = 0; i < lines.length - 1; i++) {
      const line = lines[i].trim()
      if (line.startsWith('data: ')) {
        const data = line.slice(6)
        onChunk(data)
      }
    }
    buffer = lines[lines.length - 1]
  }
}

// 文件上传批改
export const gradeFile = async (file, maxTokens = 1024, subject = null) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('max_tokens', maxTokens)
  if (subject) formData.append('subject', subject)
  
  return api.post('/grade/file', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// ==================== 数据分析API ====================

// 批量批改作业
export const batchGrade = (submissions, subject = 'math') => {
  return api.post('/analytics/batch-grade', { submissions, subject })
}

// 生成示例数据
export const generateSampleData = (count = 50, subject = 'math') => {
  return api.get(`/analytics/generate-sample/${count}`, { params: { subject } })
}

// 获取学生进度追踪
export const getStudentProgress = (studentId) => {
  return api.get(`/analytics/progress/${studentId}`)
}

// 获取效果对比数据
export const getMetricsComparison = () => {
  return api.get('/analytics/comparison')
}

// 导出分析报告
export const exportAnalyticsReport = (format = 'json') => {
  return api.post('/analytics/export-report', null, { params: { format } })
}

// 获取当前统计数据
export const getCurrentStats = () => {
  return api.get('/analytics/current-stats')
}

// ==================== Rubric 评分标准API ====================

// 获取评分标准列表
export const getRubricList = (subject) => {
  return api.get('/rubric/list', subject ? { params: { subject } } : {})
}

// 获取单个评分标准详情
export const getRubricDetail = (rubricId) => {
  return api.get(`/rubric/${rubricId}`)
}

// 创建评分标准
export const createRubric = (data) => {
  return api.post('/rubric', data)
}

// 更新评分标准
export const updateRubric = (rubricId, data) => {
  return api.put(`/rubric/${rubricId}`, data)
}

// 删除评分标准
export const deleteRubric = (rubricId) => {
  return api.delete(`/rubric/${rubricId}`)
}

// 获取预设模板
export const getRubricTemplates = () => {
  return api.get('/rubric/templates/list')
}

// 克隆预设模板
export const cloneRubricTemplate = (templateId, newName) => {
  return api.post(`/rubric/templates/${templateId}/clone`, null, { params: { new_name: newName } })
}

// 使用评分标准批改作业
export const gradeWithRubric = (rubricId, content, studentId) => {
  return api.post(`/rubric/${rubricId}/grade`, { content, student_id: studentId })
}

// ========== 因果推理 API ==========
export const causalApi = {
  // 获取因果图谱
  getGraph: (subject = 'math') => api.get(`/research/causal/graph?subject=${subject}`),
  // 获取知识点列表
  getNodes: (subject = 'math') => api.get(`/research/causal/nodes?subject=${subject}`),
  // 根因诊断
  diagnose: (data) => api.post('/research/causal/diagnose', data),
  // 反事实推理
  counterfactual: (data) => api.post('/research/causal/counterfactual', data),
  // 因果效应估计
  estimateEffect: (causeNode, effectNode, subject = 'math') =>
    api.get(`/research/causal/effect?cause_node=${causeNode}&effect_node=${effectNode}&subject=${subject}`),
  // 因果发现
  discovery: (data) => api.post('/research/causal/discovery', data),
  // 学习路径推荐
  learningPath: (data) => api.post('/research/causal/learning-path', data),
  // 科研报告
  report: (subject = 'math') => api.get(`/research/causal/report?subject=${subject}`),
  // 总览
  overview: () => api.get('/research/causal/overview'),
}

export default api

// ==================== 科研评估 API ====================

// 科研数据总览
export const getResearchOverview = () => {
  return api.get('/research/overview')
}

// 一致性评估
export const runConsistencyEval = (aiScores, humanScores, evaluatorName, taskName) => {
  return api.post('/research/consistency/evaluate', {
    ai_scores: aiScores,
    human_scores: humanScores,
    evaluator_name: evaluatorName,
    task_name: taskName
  })
}

export const getConsistencyDemo = (count = 30) => {
  return api.get('/research/consistency/demo', { params: { count } })
}

export const listConsistencyEvals = () => {
  return api.get('/research/consistency/list')
}

// A/B 测试
export const createABTest = (data) => {
  return api.post('/research/ab-test/create', data)
}

export const listABTests = () => {
  return api.get('/research/ab-test/list')
}

export const getABTestDetail = (expId) => {
  return api.get(`/research/ab-test/${expId}`)
}

// 置信度评估
export const calculateConfidence = (content, score, rubricId) => {
  return api.post('/research/confidence', { content, score, rubric_id: rubricId })
}

// Prompt 工程实验台
export const listPromptVariants = () => {
  return api.get('/research/prompts/list')
}

export const createPromptVariant = (name, systemPrompt, description) => {
  return api.post('/research/prompts/create', { name, system_prompt: systemPrompt, description })
}

export const testPrompt = (promptId, testContent, referenceScore) => {
  return api.post(`/research/prompts/${promptId}/test`, {
    test_content: testContent,
    reference_score: referenceScore
  })
}

export const comparePrompts = (promptIds) => {
  return api.post('/research/prompts/compare', { prompt_ids: promptIds })
}

// 数据导出
export const exportResearchData = (dataType = 'all', format = 'csv') => {
  return api.post('/research/export', null, { params: { data_type: dataType, format } })
}