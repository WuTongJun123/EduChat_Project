<template>
  <div class="rubric-manager">
    <!-- 顶部操作栏 -->
    <div class="rubric-toolbar">
      <div class="toolbar-left">
        <el-select v-model="filterSubject" placeholder="按学科筛选" clearable style="width: 160px" @change="loadRubrics">
          <el-option label="全部学科" value="" />
          <el-option label="数学" value="math" />
          <el-option label="语文" value="chinese" />
          <el-option label="编程" value="programming" />
          <el-option label="英语" value="english" />
        </el-select>
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          新建评分标准
        </el-button>
        <el-button @click="showTemplateDialog = true">
          <el-icon><DocumentCopy /></el-icon>
          从模板创建
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-tag type="info">共 {{ rubrics.length }} 个评分标准</el-tag>
      </div>
    </div>

    <!-- 评分标准列表 -->
    <div class="rubric-list" v-loading="loading">
      <el-empty v-if="!loading && rubrics.length === 0" description="暂无评分标准，请创建或从模板导入" />
      
      <el-card v-for="rubric in rubrics" :key="rubric.id" class="rubric-card" shadow="hover">
        <div class="rubric-card-header">
          <div class="rubric-title-area">
            <el-tag :type="rubric.id.startsWith('preset_') ? 'warning' : 'success'" size="small">
              {{ rubric.id.startsWith('preset_') ? '预设' : '自定义' }}
            </el-tag>
            <h3 class="rubric-name">{{ rubric.name }}</h3>
            <el-tag size="small" effect="plain">{{ subjectMap[rubric.subject] || rubric.subject }}</el-tag>
          </div>
          <div class="rubric-actions">
            <el-button size="small" @click="viewRubric(rubric)">
              <el-icon><View /></el-icon>查看
            </el-button>
            <el-button size="small" type="primary" @click="openGradeDialog(rubric)">
              <el-icon><EditPen /></el-icon>批改作业
            </el-button>
            <el-button size="small" @click="openEditDialog(rubric)" :disabled="rubric.id.startsWith('preset_')">
              <el-icon><Edit /></el-icon>编辑
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(rubric)" :disabled="rubric.id.startsWith('preset_')">
              <el-icon><Delete /></el-icon>删除
            </el-button>
          </div>
        </div>
        
        <p class="rubric-desc">{{ rubric.description || '暂无描述' }}</p>
        
        <div class="rubric-criteria-preview">
          <div v-for="c in rubric.criteria" :key="c.id" class="criteria-tag">
            <span class="criteria-name">{{ c.name }}</span>
            <span class="criteria-weight">{{ (c.weight * 100).toFixed(0) }}%</span>
          </div>
        </div>
        
        <div class="rubric-footer">
          <span class="rubric-meta">
            <el-icon><Calendar /></el-icon>
            {{ rubric.id.startsWith('preset_') ? '系统预设' : formatDate(rubric.updated_at) }}
          </span>
          <span class="rubric-meta">
            {{ rubric.criteria.length }} 个维度 | 权重总和 {{ (rubric.total_weight * 100).toFixed(0) }}%
          </span>
        </div>
      </el-card>
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showEditDialog"
      :title="editMode === 'create' ? '新建评分标准' : '编辑评分标准'"
      width="900px"
      top="5vh"
      :close-on-click-modal="false"
    >
      <div class="rubric-editor">
        <!-- 基本信息 -->
        <el-form :model="editForm" label-width="100px" class="edit-form">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="标准名称" required>
                <el-input v-model="editForm.name" placeholder="如：期中考试数学评分标准" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="适用学科" required>
                <el-select v-model="editForm.subject" style="width: 100%">
                  <el-option label="数学" value="math" />
                  <el-option label="语文" value="chinese" />
                  <el-option label="编程" value="programming" />
                  <el-option label="英语" value="english" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="标准描述">
            <el-input v-model="editForm.description" type="textarea" :rows="2" placeholder="描述该评分标准的适用场景" />
          </el-form-item>
        </el-form>

        <el-divider content-position="left">评分维度（权重总和需为100%）</el-divider>

        <!-- 维度编辑器 -->
        <div class="criteria-editor">
          <div v-for="(criterion, idx) in editForm.criteria" :key="idx" class="criterion-block">
            <div class="criterion-header">
              <span class="criterion-index">维度 {{ idx + 1 }}</span>
              <div class="criterion-header-actions">
                <span class="weight-display">权重：{{ (criterion.weight * 100).toFixed(0) }}%</span>
                <el-slider v-model="criterion.weight" :min="0" :max="1" :step="0.05" style="width: 150px"
                  :format-tooltip="formatTooltip" @input="updateWeightDisplay" />
                <el-button size="small" type="danger" circle @click="removeCriterion(idx)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            
            <el-row :gutter="12">
              <el-col :span="8">
                <el-input v-model="criterion.name" placeholder="维度名称（如：答案正确性）" />
              </el-col>
              <el-col :span="16">
                <el-input v-model="criterion.description" placeholder="维度说明（可选）" />
              </el-col>
            </el-row>
            
            <!-- 评分等级 -->
            <div class="levels-editor">
              <div class="levels-header">
                <span>评分等级</span>
                <el-button size="small" text @click="addLevel(criterion)">
                  <el-icon><Plus /></el-icon>添加等级
                </el-button>
              </div>
              <div v-for="(level, lIdx) in criterion.levels" :key="lIdx" class="level-row">
                <el-input-number v-model="level.score" :min="0" :max="100" :step="5" size="small" style="width: 100px" />
                <el-input v-model="level.description" placeholder="该等级的描述" size="small" style="flex: 1" />
                <el-button size="small" type="danger" circle @click="removeLevel(criterion, lIdx)"
                  :disabled="criterion.levels.length <= 2">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </div>

          <el-button type="primary" plain class="add-criterion-btn" @click="addCriterion">
            <el-icon><Plus /></el-icon>添加评分维度
          </el-button>
          
          <!-- 权重校验提示 -->
          <div class="weight-validation">
            <el-alert
              :type="weightValid ? 'success' : 'warning'"
              :title="weightAlertTitle"
              :closable="false"
              show-icon
            />
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :disabled="!weightValid || !editForm.name">
          {{ editMode === 'create' ? '创建' : '保存' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 模板选择对话框 -->
    <el-dialog v-model="showTemplateDialog" title="从预设模板创建" width="600px">
      <div class="template-list">
        <el-card v-for="tpl in templates" :key="tpl.id" class="template-card" shadow="hover"
          @click="selectTemplate(tpl)">
          <div class="template-info">
            <h4>{{ tpl.name }}</h4>
            <p>{{ tpl.description }}</p>
            <div class="template-tags">
              <el-tag size="small">{{ subjectMap[tpl.subject] }}</el-tag>
              <el-tag size="small" type="info">{{ tpl.criteria.length }} 个维度</el-tag>
            </div>
          </div>
        </el-card>
      </div>
    </el-dialog>

    <!-- 查看详情对话框 -->
    <el-dialog v-model="showViewDialog" title="评分标准详情" width="700px">
      <div v-if="viewingRubric" class="rubric-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">{{ viewingRubric.name }}</el-descriptions-item>
          <el-descriptions-item label="学科">{{ subjectMap[viewingRubric.subject] }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ viewingRubric.description || '无' }}</el-descriptions-item>
        </el-descriptions>
        
        <div v-for="c in viewingRubric.criteria" :key="c.id" class="detail-criterion">
          <div class="detail-criterion-header">
            <h4>{{ c.name }}</h4>
            <el-tag type="warning">权重 {{ (c.weight * 100).toFixed(0) }}%</el-tag>
          </div>
          <p v-if="c.description" class="detail-criterion-desc">{{ c.description }}</p>
          <el-table :data="c.levels" border size="small">
            <el-table-column prop="score" label="分数" width="80" align="center" />
            <el-table-column prop="description" label="等级描述" />
          </el-table>
        </div>
      </div>
    </el-dialog>

    <!-- 批改作业对话框 -->
    <el-dialog v-model="showGradeDialog" title="使用评分标准批改作业" width="800px" top="5vh">
      <div v-if="gradingRubric" class="grade-dialog-content">
        <el-alert type="info" :closable="false" show-icon>
          <template #title>
            当前使用评分标准：<strong>{{ gradingRubric.name }}</strong>
          </template>
        </el-alert>
        
        <el-form class="grade-form" label-width="80px">
          <el-form-item label="学生ID">
            <el-input v-model="gradeForm.studentId" placeholder="选填，如 student_001" />
          </el-form-item>
          <el-form-item label="作业内容" required>
            <el-input v-model="gradeForm.content" type="textarea" :rows="8"
              placeholder="请输入学生作业内容..." />
          </el-form-item>
        </el-form>

        <!-- 批改结果 -->
        <div v-if="gradeResult" class="grade-result">
          <el-divider content-position="left">批改结果</el-divider>
          
          <div class="result-summary">
            <div class="score-circle" :class="scoreLevel(gradeResult.total_score)">
              <span class="score-value">{{ gradeResult.total_score }}</span>
              <span class="score-label">总分</span>
            </div>
            <div class="criterion-scores">
              <div v-for="cs in gradeResult.criterion_scores" :key="cs.criterion_id" class="criterion-score-item">
                <div class="cs-header">
                  <span>{{ cs.criterion_name }}</span>
                  <span class="cs-weight">({{ (cs.weight * 100).toFixed(0) }}%)</span>
                </div>
                <div class="cs-bar">
                  <div class="cs-bar-fill" :style="{ width: cs.level_score + '%' }"
                    :class="scoreLevel(cs.level_score)"></div>
                </div>
                <span class="cs-score">{{ cs.level_score }}分</span>
              </div>
            </div>
          </div>

          <div class="result-feedback" v-html="renderMarkdown(gradeResult.overall_feedback)"></div>
        </div>
      </div>

      <template #footer>
        <el-button @click="showGradeDialog = false">关闭</el-button>
        <el-button type="primary" @click="handleGrade" :loading="grading"
          :disabled="!gradeForm.content">开始批改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Edit, View, EditPen, DocumentCopy, Calendar } from '@element-plus/icons-vue'
import {
  getRubricList, getRubricDetail, createRubric, updateRubric, deleteRubric,
  getRubricTemplates, cloneRubricTemplate, gradeWithRubric
} from '../api'

const subjectMap = {
  math: '数学', chinese: '语文', programming: '编程', english: '英语'
}

const loading = ref(false)
const rubrics = ref([])
const filterSubject = ref('')

const showEditDialog = ref(false)
const editMode = ref('create')
const editingId = ref(null)

const showTemplateDialog = ref(false)
const templates = ref([])

const showViewDialog = ref(false)
const viewingRubric = ref(null)

const showGradeDialog = ref(false)
const gradingRubric = ref(null)
const grading = ref(false)
const gradeResult = ref(null)

const gradeForm = reactive({
  studentId: '',
  content: ''
})

const editForm = reactive({
  name: '',
  subject: 'math',
  description: '',
  criteria: []
})

const totalWeight = computed(() => {
  return editForm.criteria.reduce((sum, c) => sum + (c.weight || 0), 0)
})

const weightValid = computed(() => {
  return Math.abs(totalWeight.value - 1.0) < 0.001 && editForm.criteria.length > 0
})

const weightAlertTitle = computed(() => {
  const pct = (totalWeight.value * 100).toFixed(0)
  return weightValid.value ? `权重总和：${pct}% - 校验通过` : `权重总和：${pct}% - 需调整为100%`
})

const formatTooltip = (val) => {
  return (val * 100).toFixed(0) + '%'
}

// ==================== 数据加载 ====================

const loadRubrics = async () => {
  loading.value = true
  try {
    const res = await getRubricList(filterSubject.value || undefined)
    rubrics.value = res.data.rubrics
  } catch (e) {
    ElMessage.error('加载评分标准失败')
  } finally {
    loading.value = false
  }
}

const loadTemplates = async () => {
  try {
    const res = await getRubricTemplates()
    templates.value = res.data.templates
  } catch (e) {
    ElMessage.error('加载模板失败')
  }
}

// ==================== 创建/编辑 ====================

const openCreateDialog = () => {
  editMode.value = 'create'
  editingId.value = null
  editForm.name = ''
  editForm.subject = 'math'
  editForm.description = ''
  editForm.criteria = [createEmptyCriterion()]
  showEditDialog.value = true
}

const openEditDialog = (rubric) => {
  editMode.value = 'edit'
  editingId.value = rubric.id
  editForm.name = rubric.name
  editForm.subject = rubric.subject
  editForm.description = rubric.description
  editForm.criteria = JSON.parse(JSON.stringify(rubric.criteria))
  showEditDialog.value = true
}

const createEmptyCriterion = () => ({
  id: `c_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
  name: '',
  weight: 0.25,
  description: '',
  levels: [
    { score: 100, description: '优秀' },
    { score: 80, description: '良好' },
    { score: 60, description: '及格' },
    { score: 30, description: '不及格' }
  ]
})

const addCriterion = () => {
  editForm.criteria.push(createEmptyCriterion())
}

const removeCriterion = (idx) => {
  editForm.criteria.splice(idx, 1)
}

const addLevel = (criterion) => {
  criterion.levels.push({ score: 50, description: '' })
}

const removeLevel = (criterion, idx) => {
  criterion.levels.splice(idx, 1)
}

const updateWeightDisplay = () => {}

const handleSave = async () => {
  if (!weightValid.value) {
    ElMessage.warning('请确保权重总和为100%')
    return
  }
  
  try {
    const data = {
      name: editForm.name,
      subject: editForm.subject,
      description: editForm.description,
      criteria: editForm.criteria
    }
    
    if (editMode.value === 'create') {
      await createRubric(data)
      ElMessage.success('评分标准创建成功')
    } else {
      await updateRubric(editingId.value, data)
      ElMessage.success('评分标准更新成功')
    }
    
    showEditDialog.value = false
    loadRubrics()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

const handleDelete = async (rubric) => {
  try {
    await ElMessageBox.confirm(`确定删除「${rubric.name}」吗？`, '提示', { type: 'warning' })
    await deleteRubric(rubric.id)
    ElMessage.success('删除成功')
    loadRubrics()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

// ==================== 模板 ====================

const selectTemplate = async (tpl) => {
  try {
    const res = await cloneRubricTemplate(tpl.id, tpl.name + '（副本）')
    ElMessage.success('模板克隆成功，可在列表中编辑')
    showTemplateDialog.value = false
    loadRubrics()
  } catch (e) {
    ElMessage.error('克隆失败')
  }
}

// ==================== 查看详情 ====================

const viewRubric = (rubric) => {
  viewingRubric.value = rubric
  showViewDialog.value = true
}

// ==================== 批改作业 ====================

const openGradeDialog = (rubric) => {
  gradingRubric.value = rubric
  gradeResult.value = null
  gradeForm.content = ''
  gradeForm.studentId = ''
  showGradeDialog.value = true
}

const handleGrade = async () => {
  if (!gradeForm.content) {
    ElMessage.warning('请输入作业内容')
    return
  }
  
  grading.value = true
  gradeResult.value = null
  
  try {
    const res = await gradeWithRubric(
      gradingRubric.value.id,
      gradeForm.content,
      gradeForm.studentId || null
    )
    gradeResult.value = res.data
    ElMessage.success('批改完成')
  } catch (e) {
    ElMessage.error('批改失败：' + (e.response?.data?.detail || e.message))
  } finally {
    grading.value = false
  }
}

// ==================== 工具函数 ====================

const scoreLevel = (score) => {
  if (score >= 90) return 'excellent'
  if (score >= 80) return 'good'
  if (score >= 70) return 'medium'
  if (score >= 60) return 'pass'
  return 'fail'
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return dateStr.slice(0, 10)
}

const renderMarkdown = (text) => {
  if (!text) return ''
  return text
    .replace(/^### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^# (.+)$/gm, '<h2>$1</h2>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
}

onMounted(() => {
  loadRubrics()
  loadTemplates()
})
</script>

<style scoped>
.rubric-manager {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.rubric-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.toolbar-left {
  display: flex;
  gap: 12px;
}

.rubric-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.rubric-card {
  transition: transform 0.2s;
}

.rubric-card:hover {
  transform: translateY(-2px);
}

.rubric-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.rubric-title-area {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rubric-name {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.rubric-actions {
  display: flex;
  gap: 8px;
}

.rubric-desc {
  color: #666;
  font-size: 13px;
  margin: 8px 0;
}

.rubric-criteria-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 12px 0;
}

.criteria-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #f0f2f5;
  border-radius: 12px;
  padding: 4px 12px;
  font-size: 12px;
}

.criteria-name {
  color: #333;
}

.criteria-weight {
  color: #e6a23c;
  font-weight: 600;
}

.rubric-footer {
  display: flex;
  justify-content: space-between;
  color: #999;
  font-size: 12px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

.rubric-meta {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 编辑器样式 */
.criteria-editor {
  max-height: 500px;
  overflow-y: auto;
  padding-right: 8px;
}

.criterion-block {
  background: #f9fafc;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  border: 1px solid #ebeef5;
}

.criterion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.criterion-index {
  font-weight: 600;
  color: #409eff;
}

.criterion-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.weight-display {
  font-size: 13px;
  color: #e6a23c;
  white-space: nowrap;
}

.levels-editor {
  margin-top: 12px;
}

.levels-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 13px;
  color: #606266;
}

.level-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  align-items: center;
}

.add-criterion-btn {
  width: 100%;
  margin-top: 8px;
}

.weight-validation {
  margin-top: 16px;
}

/* 模板样式 */
.template-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.template-card {
  cursor: pointer;
  transition: all 0.2s;
}

.template-card:hover {
  border-color: #409eff;
}

.template-info h4 {
  margin: 0 0 4px 0;
}

.template-info p {
  margin: 0 0 8px 0;
  color: #666;
  font-size: 13px;
}

.template-tags {
  display: flex;
  gap: 8px;
}

/* 详情样式 */
.rubric-detail {
  max-height: 60vh;
  overflow-y: auto;
}

.detail-criterion {
  margin-top: 20px;
}

.detail-criterion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-criterion-desc {
  color: #666;
  font-size: 13px;
  margin: 4px 0 8px 0;
}

/* 批改结果样式 */
.grade-dialog-content {
  max-height: 70vh;
  overflow-y: auto;
}

.grade-form {
  margin: 20px 0;
}

.result-summary {
  display: flex;
  gap: 24px;
  margin: 20px 0;
}

.score-circle {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
  color: white;
}

.score-circle.excellent { background: #67c23a; }
.score-circle.good { background: #409eff; }
.score-circle.medium { background: #e6a23c; }
.score-circle.pass { background: #f56c6c; }
.score-circle.fail { background: #909399; }

.score-value {
  font-size: 28px;
  font-weight: bold;
}

.score-label {
  font-size: 12px;
}

.criterion-scores {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.criterion-score-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cs-header {
  width: 120px;
  font-size: 13px;
  flex-shrink: 0;
}

.cs-weight {
  color: #999;
  font-size: 11px;
}

.cs-bar {
  flex: 1;
  height: 8px;
  background: #f0f2f5;
  border-radius: 4px;
  overflow: hidden;
}

.cs-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.cs-bar-fill.excellent { background: #67c23a; }
.cs-bar-fill.good { background: #409eff; }
.cs-bar-fill.medium { background: #e6a23c; }
.cs-bar-fill.pass { background: #f56c6c; }
.cs-bar-fill.fail { background: #909399; }

.cs-score {
  width: 50px;
  text-align: right;
  font-size: 13px;
  font-weight: 600;
}

.result-feedback {
  background: #f9fafc;
  padding: 20px;
  border-radius: 8px;
  margin-top: 16px;
  line-height: 1.8;
  font-size: 14px;
}

.result-feedback :deep(h3) {
  margin: 16px 0 8px 0;
  color: #303133;
}

.result-feedback :deep(h4) {
  margin: 12px 0 6px 0;
  color: #606266;
}

.result-feedback :deep(strong) {
  color: #409eff;
}
</style>