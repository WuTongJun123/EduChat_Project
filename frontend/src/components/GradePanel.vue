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

      <div v-if="result">
        <h3>批改结果</h3>
        <div class="result-content" v-html="formattedResult"></div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
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

// 将 Markdown 样式的文本转为 HTML（简单处理，可后续增强）
const formattedResult = computed(() => {
  if (!result.value) return ''
  return result.value
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/^###\s*(.*)$/gm, '<div class="result-h3">$1</div>')
    .replace(/^##\s*(.*)$/gm, '<div class="result-h2">$1</div>')
    .replace(/^#\s*(.*)$/gm, '<div class="result-h1">$1</div>')
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
.result-content {
  background-color: #f9fafc;
  padding: 20px;
  border-radius: 8px;
  line-height: 1.8;
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-word;
}
.result-content :deep(strong) {
  color: #303133;
}
.result-content :deep(.result-h1) {
  font-size: 18px;
  font-weight: 700;
  color: #303133;
  margin: 16px 0 8px 0;
  padding-bottom: 6px;
  border-bottom: 2px solid #409eff;
}
.result-content :deep(.result-h2) {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 14px 0 6px 0;
  padding-left: 8px;
  border-left: 3px solid #409eff;
}
.result-content :deep(.result-h3) {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  margin: 10px 0 4px 0;
}
</style>