<template>
  <div class="grade-panel">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>📝 智能作业批改系统</span>
          <el-tag type="info">基于 EduChat-R1</el-tag>
        </div>
      </template>

      <el-form :model="form" label-width="80px">
        <el-form-item label="学科">
          <el-radio-group v-model="form.subject">
            <el-radio-button label="数学">数学</el-radio-button>
            <el-radio-button label="语文">语文</el-radio-button>
            <el-radio-button label="编程">编程</el-radio-button>
            <el-radio-button label="英语">英语</el-radio-button>
            <el-radio-button label="">通用</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="作业内容">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="8"
            placeholder="请输入学生作业内容（文本、代码等）或上传文件"
          />
        </el-form-item>

        <el-form-item label="上传文件">
          <el-upload
            ref="upload"
            action="#"
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
            accept=".txt,.py,.jpg,.jpeg,.png"
          >
            <el-button type="primary" plain>选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">支持 .txt / .py / .jpg / .png 格式</div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="详细程度">
          <el-slider v-model="maxTokens" :min="256" :max="4096" :step="128" show-stops />
          <span class="slider-value">{{ maxTokens }}</span>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleGrade" :loading="loading" :disabled="!form.content">
            开始批改
          </el-button>
          <el-button @click="clear">清空</el-button>
        </el-form-item>
      </el-form>

      <el-divider />

      <div v-if="result || loading">
        <h3>批改结果</h3>
        <div v-if="loading && !result" class="loading-hint">
          <el-icon class="is-loading"><Loading /></el-icon>
          模型正在加载中，首次请求需加载模型，请耐心等待...
        </div>
        <div class="result-content" v-html="formattedResult"></div>
        <span v-if="loading && result" class="typing-cursor">|</span>
      </div>

      <el-divider />

      <!-- 批量批改 -->
      <el-collapse>
        <el-collapse-item title="批量批改（上传 CSV 文件，一次批改多份作业）" name="batch">
          <el-alert type="info" :closable="false" style="margin-bottom: 12px">
            CSV 格式要求：第一行为表头，必须包含 <b>content</b> 列（作业内容），可选 <b>subject</b> 列（学科：数学/语文/编程/英语）。
            每行一份作业，建议不超过 20 份。
          </el-alert>
          <div style="display: flex; gap: 12px; align-items: center; margin-bottom: 12px">
            <el-upload
              ref="batchUpload"
              action="#"
              :auto-upload="false"
              :limit="1"
              accept=".csv"
              :on-change="handleBatchFile"
              :on-exceed="() => ElMessage.warning('只能上传一个文件')"
            >
              <template #trigger>
                <el-button type="primary" plain>选择 CSV 文件</el-button>
              </template>
            </el-upload>
            <el-button type="success" @click="runBatch" :loading="batchLoading" :disabled="!batchData.length">
              开始批量批改（{{ batchData.length }} 份）
            </el-button>
            <el-button @click="downloadTemplate">下载模板</el-button>
          </div>
          <div v-if="batchResults.length" style="margin-top: 12px">
            <el-table :data="batchResults" border stripe max-height="400" style="width: 100%">
              <el-table-column type="index" label="序号" width="60" />
              <el-table-column prop="subject" label="学科" width="80" />
              <el-table-column prop="content_preview" label="作业内容" show-overflow-tooltip />
              <el-table-column prop="score" label="评分" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.score >= 80 ? 'success' : row.score >= 60 ? 'warning' : 'danger'">
                    {{ row.score }}分
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="summary" label="批改摘要" show-overflow-tooltip />
              <el-table-column label="详情" width="80">
                <template #default="{ row }">
                  <el-button link type="primary" @click="showBatchDetail(row)">查看</el-button>
                </template>
              </el-table-column>
            </el-table>
            <div style="margin-top: 10px; display: flex; gap: 10px">
              <el-button size="small" @click="exportBatchCSV">导出结果 (CSV)</el-button>
              <span style="color: #999; font-size: 12px; line-height: 32px">
                平均分: {{ batchAvgScore }} | 最高: {{ batchMaxScore }} | 最低: {{ batchMinScore }}
              </span>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>

      <!-- 批量批改详情弹窗 -->
      <el-dialog v-model="batchDetailVisible" title="批改详情" width="600px">
        <div class="result-content" v-html="batchDetailHtml"></div>
      </el-dialog>

    </el-card>

    <!-- 批量批改 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header" @click="batchVisible = !batchVisible" style="cursor: pointer;">
          <span>📂 批量批改</span>
          <el-tag type="info" size="small">{{ batchVisible ? '收起' : '展开' }}</el-tag>
        </div>
      </template>
      <el-collapse-transition>
        <div v-show="batchVisible">
          <el-alert type="info" :closable="false" style="margin-bottom: 16px;">
            <p><strong>CSV 格式要求：</strong>第一行为表头，必须包含"作业内容"列，可选"学号""姓名""学科"列。</p>
            <p>示例：<code>学号,姓名,学科,作业内容</code></p>
            <p style="margin-top:6px;">
              <el-link type="primary" href="/batch-template.csv" download>下载 CSV 模板</el-link>
            </p>
          </el-alert>

          <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 16px; flex-wrap: wrap;">
            <el-upload
              :auto-upload="false"
              :show-file-list="true"
              accept=".csv"
              :limit="1"
              :on-change="handleBatchFile"
              :on-remove="() => batchFile = null"
            >
              <el-button type="primary" plain>选择 CSV 文件</el-button>
            </el-upload>
            <el-select v-model="batchSubject" style="width: 120px;">
              <el-option label="数学" value="数学" />
              <el-option label="语文" value="语文" />
              <el-option label="编程" value="编程" />
              <el-option label="英语" value="英语" />
              <el-option label="通用" value="通用" />
            </el-select>
            <el-button type="success" :loading="batchLoading" @click="runBatchGrade">
              {{ batchLoading ? `批改中 ${batchProgress.done}/${batchProgress.total}` : '开始批量批改' }}
            </el-button>
            <el-button v-if="batchResults.length > 0" type="warning" plain @click="exportBatchResults">
              导出结果 CSV
            </el-button>
          </div>

          <!-- 批量批改结果 -->
          <el-table v-if="batchResults.length > 0" :data="batchResults" border stripe style="width: 100%;">
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
      </el-collapse-transition>
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

const handleFileChange = (file) => {
  uploadedFile.value = file.raw
  // 可选：自动读取文件内容填充到文本框（仅文本文件）
  if (file.raw.type === 'text/plain' || file.name.endsWith('.py')) {
    const reader = new FileReader()
    reader.onload = (e) => {
      form.value.content = e.target.result
    }
    reader.readAsText(file.raw)
  } else if (file.raw.type.startsWith('image/')) {
    // 图片文件不自动填充，等待上传后后端处理
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
      // 文件上传批改
      const res = await gradeFile(uploadedFile.value, maxTokens.value, form.value.subject)
      result.value = res.data.result
    } else {
      // 使用流式批改（更佳体验）
      await gradeStreamFetch(form.value.content, maxTokens.value, (chunk) => {
        result.value += chunk
      }, form.value.subject)
      // 如果不想用流式，可用同步接口：
      // const res = await gradeSync(form.value.content, maxTokens.value)
      // result.value = res.data.result
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
  result.value = ''
}

// ============ 批量批改 ============
const batchVisible = ref(false)
const batchLoading = ref(false)
const batchFile = ref(null)
const batchSubject = ref('数学')
const batchResults = ref([])
const batchProgress = ref({ done: 0, total: 0 })

const handleBatchFile = (file) => {
  batchFile.value = file.raw
  return false // 阻止自动上传
}

const parseCSV = (text) => {
  const lines = text.trim().split('\n')
  if (lines.length < 2) return []
  const headers = lines[0].split(',').map(h => h.trim())
  const results = []
  for (let i = 1; i < lines.length; i++) {
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

const runBatchGrade = async () => {
  if (!batchFile.value) {
    ElMessage.warning('请先上传 CSV 文件')
    return
  }
  batchLoading.value = true
  batchResults.value = []
  try {
    const text = await batchFile.value.text()
    const rows = parseCSV(text)
    if (rows.length === 0) {
      ElMessage.error('CSV 文件格式不正确，请确保包含"作业内容"列')
      batchLoading.value = false
      return
    }
    batchProgress.value = { done: 0, total: rows.length }
    for (const row of rows) {
      try {
        const res = await gradeSync(row.content, 512, batchSubject.value || row.subject)
        const resultText = res.data.result || ''
        // 尝试从结果中提取分数
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
  batchLoading.value = false
}

const exportBatchResults = () => {
  const header = '学号,姓名,学科,评分,批改结果\n'
  const rows = batchResults.value.map(r =>
    `${r.id},${r.name},${r.subject},${r.score},"${r.result.replace(/"/g, '""').replace(/\n/g, ' ')}"`
  ).join('\n')
  const csv = '\uFEFF' + header + rows // BOM for Excel
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `批量批改结果_${new Date().toISOString().slice(0,10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

// 将模型输出转为格式化 HTML
const formattedResult = computed(() => {
  if (!result.value) return ''
  let text = result.value

  // Step 1: 在 ## 前插入换行（处理模型不换行的情况）
  text = text.replace(/(?!^)(?=##)/gm, '\n')

  // Step 2: 在已知标题后插入换行（标题和内容挤在同一行的情况）
  const headers = ['整体评价', '错误分析', '评分', '学习建议', '鼓励性结尾', 'Overall Evaluation']
  headers.forEach(h => {
    text = text.replace(new RegExp(`(##\\s*${h}\\s*)(?!\\n)`, 'g'), '$1\n')
  })

  // Step 3: 在 【xxx】 前插入换行
  text = text.replace(/(?!^)(?=【)/g, '\n')

  // Step 4: 转换标题为 div
  text = text
    .replace(/^###\s*(.*)$/gm, '<div class="result-h3">$1</div>')
    .replace(/^##\s*(.*)$/gm, '<div class="result-h2">$1</div>')
    .replace(/^#\s*(.*)$/gm, '<div class="result-h1">$1</div>')
    .replace(/^【(.+?)】\s*(.*)$/gm, '<div class="result-h2">$1</div>')

  // Step 5: 加粗
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')

  // Step 6: 换行
  text = text.replace(/\n/g, '<br>')

  // Step 7: 清理多余空行
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