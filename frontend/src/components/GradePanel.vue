<template>
  <div class="grade-panel">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>智能作业批改</span>
          <el-tag type="info" size="small">EduChat-R1 驱动</el-tag>
        </div>
      </template>

      <!-- 学科选择 -->
      <div style="margin-bottom: 16px;">
        <span style="font-weight: 600; margin-right: 12px;">学科：</span>
        <el-radio-group v-model="form.subject" size="default">
          <el-radio-button value="数学">数学</el-radio-button>
          <el-radio-button value="语文">语文</el-radio-button>
          <el-radio-button value="编程">编程</el-radio-button>
          <el-radio-button value="英语">英语</el-radio-button>
          <el-radio-button value="通用">通用</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 作业输入 -->
      <el-input
        v-model="form.content"
        type="textarea"
        :rows="8"
        placeholder="请输入作业内容，或上传文件..."
        style="margin-bottom: 16px;"
      />

      <!-- 文件上传区域 -->
      <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;">
        <el-upload
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleFileChange"
          accept=".txt,.py,.jpg,.png,.csv,.xlsx"
        >
          <el-button type="primary" plain>选择文件</el-button>
        </el-upload>
        <span v-if="uploadedFileName" style="color: #67c23a; font-size: 14px;">✓ {{ uploadedFileName }}</span>
        <span style="color: #909399; font-size: 13px;">支持 .txt / .py / .jpg / .png / .csv / .xlsx 格式（.csv / .xlsx 为批量批改）</span>
        <el-button type="info" plain size="small" @click="downloadTemplate">下载批量模板</el-button>
      </div>

      <!-- 批量批改进度 -->
      <div v-if="batchProgress.total > 0" style="margin-bottom: 16px;">
        <el-progress :percentage="Math.round(batchProgress.done / batchProgress.total * 100)" :format="() => `${batchProgress.done} / ${batchProgress.total}`" />
      </div>

      <!-- Max Tokens 滑块 -->
      <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <span style="font-weight: 600; margin-right: 12px;">最大输出长度：</span>
        <el-slider v-model="maxTokens" :min="128" :max="2048" :step="128" style="flex: 1;" />
        <span class="slider-value">{{ maxTokens }}</span>
      </div>

      <!-- 操作按钮 -->
      <div style="display: flex; gap: 12px; margin-bottom: 20px;">
        <el-button type="primary" :loading="loading" @click="handleGrade">
          {{ loading ? '批改中...' : '流式批改' }}
        </el-button>
        <el-button @click="clear">清空</el-button>
      </div>

      <!-- 批改结果 -->
      <div v-if="result || loading" style="margin-top: 16px;">
        <div style="font-weight: 600; margin-bottom: 10px; font-size: 16px;">批改结果</div>
        <div v-if="loading && !result" class="loading-hint">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>模型正在批改中，请稍候...</span>
        </div>
        <div class="result-content" v-html="formattedResult"></div>
        <div v-if="loading" class="typing-cursor">|</div>
      </div>

      <!-- 批量批改结果 -->
      <div v-if="batchResults.length > 0" style="margin-top: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
          <span style="font-weight: 600; font-size: 16px;">批量批改结果（{{ batchResults.length }} 份）</span>
          <el-button type="success" plain size="small" @click="exportBatchResults">导出结果</el-button>
        </div>
        <el-table :data="batchResults" border stripe style="width: 100%;">
          <el-table-column prop="id" label="学号" width="100" />
          <el-table-column prop="name" label="姓名" width="80" />
          <el-table-column prop="subject" label="学科" width="70" />
          <el-table-column prop="score" label="评分" width="70">
            <template #default="{ row }">
              <el-tag :type="row.status === 'error' ? 'danger' : row.score === '—' ? 'info' : 'success'" size="small">
                {{ row.score }}{{ row.score !== '—' ? '分' : '' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="result" label="批改结果" min-width="300">
            <template #default="{ row }">
              <div style="max-height: 120px; overflow-y: auto; font-size: 13px; line-height: 1.6; white-space: pre-wrap;">{{ row.result }}</div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { gradeSync, gradeStreamFetch, gradeFile } from '../api'

const form = ref({
  content: '',
  subject: '数学'
})
const maxTokens = ref(1024)
const loading = ref(false)
const result = ref('')
const uploadedFile = ref(null)
const uploadedFileName = ref('')

// 批量批改
const batchResults = ref([])
const batchProgress = ref({ done: 0, total: 0 })

const handleFileChange = async (file) => {
  const fileName = file.name.toLowerCase()
  uploadedFileName.value = file.name

  // CSV / XLSX → 批量批改
  if (fileName.endsWith('.csv') || fileName.endsWith('.xlsx')) {
    uploadedFile.value = null
    await runBatchGrade(file.raw, fileName)
    return
  }

  // 单文件批改
  uploadedFile.value = file.raw
  if (file.raw.type === 'text/plain' || fileName.endsWith('.py')) {
    const reader = new FileReader()
    reader.onload = (e) => {
      form.value.content = e.target.result
    }
    reader.readAsText(file.raw)
  } else if (file.raw.type.startsWith('image/')) {
    ElMessage.info('图片文件将直接上传，无需手动输入内容')
  }
}

const handleGrade = async () => {
  if (!form.value.content.trim() && !uploadedFile.value) {
    ElMessage.warning('请填写作业内容或上传文件')
    return
  }

  loading.value = true
  result.value = ''

  try {
    if (uploadedFile.value) {
      const res = await gradeFile(uploadedFile.value, maxTokens.value, form.value.subject)
      result.value = res.data.result
    } else {
      await gradeStreamFetch(form.value.content, maxTokens.value, (chunk) => {
        result.value += chunk
      }, form.value.subject)
    }
  } catch (error) {
    ElMessage.error('批改失败：' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const clear = () => {
  form.value.content = ''
  uploadedFile.value = null
  uploadedFileName.value = ''
  result.value = ''
  batchResults.value = []
  batchProgress.value = { done: 0, total: 0 }
}

// ============ 批量批改 ============
const parseCSV = (text) => {
  const lines = text.trim().split('\n')
  if (lines.length < 2) return []
  const headers = lines[0].split(',').map(h => h.trim())
  const results = []
  for (let i = 1; i < lines.length; i++) {
    if (!lines[i].trim()) continue
    const values = []
    let current = ''
    let inQuotes = false
    for (const ch of lines[i]) {
      if (ch === '"') { inQuotes = !inQuotes }
      else if (ch === ',' && !inQuotes) { values.push(current.trim()); current = '' }
      else { current += ch }
    }
    values.push(current.trim())
    const row = {}
    headers.forEach((h, idx) => { row[h] = values[idx] || '' })
    if (row['作业内容'] || row['content']) {
      results.push({
        id: row['学号'] || row['id'] || String(i),
        name: row['姓名'] || row['name'] || `学生${i}`,
        subject: row['学科'] || row['subject'] || '数学',
        content: row['作业内容'] || row['content'] || ''
      })
    }
  }
  return results
}

const runBatchGrade = async (file, fileName) => {
  batchLoading: {
    loading.value = true
    batchResults.value = []
    batchProgress.value = { done: 0, total: 0 }

    try {
      let rows = []

      if (fileName.endsWith('.csv')) {
        const text = await file.text()
        rows = parseCSV(text)
      } else if (fileName.endsWith('.xlsx')) {
        // 动态加载 xlsx 库解析 Excel
        try {
          const XLSX = await import('xlsx')
          const data = await file.arrayBuffer()
          const wb = XLSX.read(data, { type: 'array' })
          const ws = wb.Sheets[wb.SheetNames[0]]
          const jsonData = XLSX.utils.sheet_to_json(ws)
          rows = jsonData.map((row, i) => ({
            id: row['学号'] || row['id'] || String(i + 1),
            name: row['姓名'] || row['name'] || `学生${i + 1}`,
            subject: row['学科'] || row['subject'] || '数学',
            content: row['作业内容'] || row['content'] || ''
          })).filter(r => r.content)
        } catch (e) {
          ElMessage.error('Excel 解析失败，请确保文件格式正确。建议使用 CSV 格式。')
          loading.value = false
          return
        }
      }

      if (rows.length === 0) {
        ElMessage.error('文件格式不正确，请确保包含"作业内容"列')
        loading.value = false
        return
      }

      batchProgress.value = { done: 0, total: rows.length }

      for (const row of rows) {
        try {
          const res = await gradeSync(row.content, 512, form.value.subject || row.subject)
          const resultText = res.data.result || ''
          const scoreMatch = resultText.match(/总分[：:]\s*(\d+)/)
          batchResults.value.push({
            id: row.id,
            name: row.name,
            subject: row.subject,
            score: scoreMatch ? scoreMatch[1] : '—',
            result: resultText,
            status: 'success'
          })
        } catch (e) {
          batchResults.value.push({
            id: row.id,
            name: row.name,
            subject: row.subject,
            score: '—',
            result: '批改失败: ' + e.message,
            status: 'error'
          })
        }
        batchProgress.value.done++
      }
      ElMessage.success(`批量批改完成！共 ${rows.length} 份`)
    } catch (e) {
      ElMessage.error('文件读取失败: ' + e.message)
    }
    loading.value = false
  }
}

const exportBatchResults = () => {
  const header = '学号,姓名,学科,评分,批改结果\n'
  const rows = batchResults.value.map(r =>
    `${r.id},${r.name},${r.subject},${r.score},"${r.result.replace(/"/g, '""').replace(/\n/g, ' ')}"`
  ).join('\n')
  const csv = '\uFEFF' + header + rows
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `批量批改结果_${new Date().toISOString().slice(0,10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

// 下载批量模板（Excel 格式）
const downloadTemplate = async () => {
  try {
    const XLSX = await import('xlsx')
    const data = [
      { '学号': '2024001', '姓名': '张三', '学科': '数学', '作业内容': '解方程：x²-5x+6=0\n解：因式分解(x-2)(x-3)=0\nx=2或x=3' },
      { '学号': '2024002', '姓名': '李四', '学科': '数学', '作业内容': '求函数f(x)=x²-4x+3的最小值\n解：f(x)=(x-2)²-1\n最小值为-1' },
      { '学号': '2024003', '姓名': '王五', '学科': '英语', '作业内容': 'My favorite season is summer because I can swimming in the pool.' }
    ]
    const ws = XLSX.utils.json_to_sheet(data)
    // 设置列宽
    ws['!cols'] = [{ wch: 12 }, { wch: 10 }, { wch: 8 }, { wch: 60 }]
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '批量批改模板')
    XLSX.writeFile(wb, '批量批改模板.xlsx')
  } catch (e) {
    // 如果 xlsx 库不可用，降级为 CSV
    const csv = '\uFEFF学号,姓名,学科,作业内容\n2024001,张三,数学,解方程：x²-5x+6=0\n2024002,李四,数学,求函数最小值\n2024003,王五,英语,英语作文内容'
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = '批量批改模板.csv'
    a.click()
    URL.revokeObjectURL(url)
  }
}

// 格式化批改结果
const formattedResult = computed(() => {
  if (!result.value) return ''
  let text = result.value

  text = text.replace(/(?!^)(?=##)/gm, '\n')

  const headers = ['整体评价', '错误分析', '评分', '学习建议', '鼓励性结尾', 'Overall Evaluation']
  headers.forEach(h => {
    text = text.replace(new RegExp(`(##\\s*${h}\\s*)(?!\\n)`, 'g'), '$1\n')
  })

  text = text.replace(/(?!^)(?=【)/g, '\n')

  text = text
    .replace(/^###\s*(.*)$/gm, '<div class="result-h3">$1</div>')
    .replace(/^##\s*(.*)$/gm, '<div class="result-h2">$1</div>')
    .replace(/^#\s*(.*)$/gm, '<div class="result-h1">$1</div>')
    .replace(/^【(.+?)】\s*(.*)$/gm, '<div class="result-h2">$1</div>')

  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  text = text.replace(/\n/g, '<br>')
  text = text.replace(/(<br>\s*){3,}/g, '<br><br>')

  return text
})
</script>

<style scoped>
.grade-panel {
  max-width: 1000px;
  margin: 30px auto;
  padding: 0 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 20px;
  font-weight: bold;
}
.slider-value {
  margin-left: 12px;
  color: #409eff;
}
.loading-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #409eff;
  font-size: 15px;
  padding: 20px 0;
}
.result-content {
  background-color: #f9fafc;
  padding: 24px;
  border-radius: 8px;
  line-height: 2;
  font-size: 15px;
  color: #333;
  word-break: break-word;
}
.result-content :deep(strong) {
  color: #e6a23c;
  font-weight: 600;
}
.result-content :deep(.result-h1) {
  font-size: 19px;
  font-weight: 700;
  color: #303133;
  margin: 18px 0 10px 0;
  padding-bottom: 6px;
  border-bottom: 2px solid #409eff;
}
.result-content :deep(.result-h2) {
  font-size: 17px;
  font-weight: 600;
  color: #303133;
  margin: 16px 0 8px 0;
  padding-left: 10px;
  border-left: 4px solid #409eff;
}
.result-content :deep(.result-h3) {
  font-size: 15px;
  font-weight: 600;
  color: #606266;
  margin: 12px 0 6px 0;
}
.typing-cursor {
  display: inline-block;
  color: #409eff;
  font-weight: bold;
  animation: blink 0.8s steps(2) infinite;
  margin-left: 2px;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>
