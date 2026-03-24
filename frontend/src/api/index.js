import axios from 'axios'

const api = axios.create({
  baseURL: '/api',  // 开发环境代理到后端
  timeout: 60000
})

// 同步批改
export const gradeSync = (content, maxTokens = 1024) => {
  return api.post('/grade/sync', { content, max_tokens: maxTokens })
}

// 流式批改（使用 EventSource）
export const gradeStream = (content, maxTokens = 1024, onMessage, onError) => {
  const url = `/api/grade/stream`
  const eventSource = new EventSource(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, max_tokens: maxTokens })
  })
  // EventSource 默认只支持 GET，需要特殊处理，这里使用 fetch + ReadableStream 更简单
  // 故实际实现时使用 fetch 的 ReadableStream
}

// 使用 fetch 实现流式请求
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
export const gradeFile = (file, maxTokens = 1024) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('max_tokens', maxTokens)
  return api.post('/grade/file', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}