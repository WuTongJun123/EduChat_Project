import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000
})

// ==================== 基础批改API ====================

// 同步批改
export const gradeSync = (content, maxTokens = 1024) => {
  return api.post('/grade/sync', { content, max_tokens: maxTokens })
}

// 流式批改（使用 fetch + ReadableStream）
export const gradeStreamFetch = async (content, maxTokens, onChunk) => {
  const response = await fetch('/api/grade/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, max_tokens: maxTokens })
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
export const gradeFile = async (file, maxTokens = 1024) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('max_tokens', maxTokens)
  
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

export default api