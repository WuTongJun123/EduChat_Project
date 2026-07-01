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

export default api