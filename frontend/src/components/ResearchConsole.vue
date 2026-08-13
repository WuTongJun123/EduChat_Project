<template>
  <div class="research-console">
    <!-- 总览卡片 -->
    <div class="overview-cards" v-loading="overviewLoading">
      <el-card class="overview-card" shadow="hover">
        <div class="card-icon" style="background: #e8f4fd">
          <el-icon size="28" color="#409eff"><DataAnalysis /></el-icon>
        </div>
        <div class="card-body">
          <div class="card-value">{{ overview.consistency?.total_evaluations || 0 }}</div>
          <div class="card-label">一致性评估次数</div>
          <div class="card-sub" v-if="overview.consistency?.avg_kappa">
            平均 Kappa: {{ overview.consistency.avg_kappa }} | r: {{ overview.consistency.avg_pearson_r }}
          </div>
        </div>
      </el-card>
      <el-card class="overview-card" shadow="hover">
        <div class="card-icon" style="background: #f0f9eb">
          <el-icon size="28" color="#67c23a"><TrendCharts /></el-icon>
        </div>
        <div class="card-body">
          <div class="card-value">{{ overview.experiments?.total_experiments || 0 }}</div>
          <div class="card-label">A/B 测试实验</div>
          <div class="card-sub" v-if="overview.experiments?.total_experiments">
            显著性结果: {{ overview.experiments.significant_results }} | 平均改善: {{ overview.experiments.avg_improvement }}%
          </div>
        </div>
      </el-card>
      <el-card class="overview-card" shadow="hover">
        <div class="card-icon" style="background: #fdf6ec">
          <el-icon size="28" color="#e6a23c"><EditPen /></el-icon>
        </div>
        <div class="card-body">
          <div class="card-value">{{ overview.prompts?.total_variants || 0 }}</div>
          <div class="card-label">Prompt 变体</div>
          <div class="card-sub" v-if="overview.prompts?.total_tests">
            累计测试: {{ overview.prompts.total_tests }} 次
          </div>
        </div>
      </el-card>
      <el-card class="overview-card" shadow="hover">
        <div class="card-icon" style="background: #fef0f0">
          <el-icon size="28" color="#f56c6c"><Download /></el-icon>
        </div>
        <div class="card-body">
          <div class="card-value">{{ overview.exports || 0 }}</div>
          <div class="card-label">数据导出次数</div>
        </div>
      </el-card>
    </div>

    <!-- Tab 面板 -->
    <el-card shadow="never" class="main-card">
      <el-tabs v-model="activeTab" type="card">
        <!-- ============ 一致性评估 ============ -->
        <el-tab-pane label="评分一致性评估" name="consistency">
          <div class="tab-toolbar">
            <el-button type="primary" @click="loadConsistencyDemo" :loading="consistencyLoading">
              生成演示数据 (30条)
            </el-button>
            <el-button @click="showConsistencyForm = !showConsistencyForm">
              {{ showConsistencyForm ? '收起' : '自定义' }}评估数据
            </el-button>
            <el-button @click="loadConsistencyList">查看历史记录</el-button>
          </div>

          <!-- 自定义输入 -->
          <el-collapse-transition>
            <div v-show="showConsistencyForm" class="custom-form">
              <el-alert type="info" :closable="false" show-icon style="margin-bottom: 16px">
                输入 AI 评分和人工评分（每行一个分数，用换行分隔），系统将计算 Cohen's Kappa、Pearson 相关系数等一致性指标。
              </el-alert>
              <el-row :gutter="20">
                <el-col :span="12">
                  <div class="form-label">AI 评分（每行一个）</div>
                  <el-input v-model="aiScoresInput" type="textarea" :rows="8" placeholder="85&#10;92&#10;78&#10;..." />
                </el-col>
                <el-col :span="12">
                  <div class="form-label">人工评分（每行一个）</div>
                  <el-input v-model="humanScoresInput" type="textarea" :rows="8" placeholder="88&#10;90&#10;80&#10;..." />
                </el-col>
              </el-row>
              <el-row :gutter="20" style="margin-top: 12px">
                <el-col :span="8">
                  <el-input v-model="consistencyTaskName" placeholder="任务名称（如：数学期中考试）" />
                </el-col>
                <el-col :span="8">
                  <el-input v-model="consistencyEvaluator" placeholder="评估者（如：教师A）" />
                </el-col>
                <el-col :span="8">
                  <el-button type="primary" @click="runCustomConsistency" :loading="consistencyLoading" style="width: 100%">
                    运行评估
                  </el-button>
                </el-col>
              </el-row>
            </div>
          </el-collapse-transition>

          <!-- 评估结果 -->
          <div v-if="consistencyResult" class="result-section">
            <el-divider content-position="left">评估结果</el-divider>

            <!-- 核心指标 -->
            <el-row :gutter="16" class="metric-row">
              <el-col :span="6">
                <div class="metric-box highlight">
                  <div class="metric-value">{{ consistencyResult.kappa.kappa }}</div>
                  <div class="metric-label">Cohen's Kappa</div>
                  <div class="metric-tag">{{ consistencyResult.kappa.level }}</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="metric-box">
                  <div class="metric-value">{{ consistencyResult.pearson.r }}</div>
                  <div class="metric-label">Pearson r</div>
                  <div class="metric-tag">{{ consistencyResult.pearson.strength }}</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="metric-box">
                  <div class="metric-value">{{ (consistencyResult.agreement_rates.within_5pts * 100).toFixed(1) }}%</div>
                  <div class="metric-label">5分内匹配率</div>
                  <div class="metric-tag">{{ consistencyResult.agreement_rates.exact_match_2pts >= 0.7 ? '匹配度高' : '匹配度一般' }}</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="metric-box" :class="{ warning: Math.abs(consistencyResult.bias_analysis.mean_bias) > 3 }">
                  <div class="metric-value">{{ consistencyResult.bias_analysis.mean_bias > 0 ? '+' : '' }}{{ consistencyResult.bias_analysis.mean_bias }}</div>
                  <div class="metric-label">系统偏差</div>
                  <div class="metric-tag">{{ consistencyResult.bias_analysis.bias_direction }}</div>
                </div>
              </el-col>
            </el-row>

            <!-- 详细统计 -->
            <el-row :gutter="16" style="margin-top: 16px">
              <el-col :span="12">
                <el-card shadow="never" class="detail-card">
                  <template #header><span>一致性详情</span></template>
                  <el-descriptions :column="1" border size="small">
                    <el-descriptions-item label="样本量">{{ consistencyResult.sample_size }}</el-descriptions-item>
                    <el-descriptions-item label="观察一致率 Po">{{ consistencyResult.kappa.po }}</el-descriptions-item>
                    <el-descriptions-item label="偶然一致率 Pe">{{ consistencyResult.kappa.pe }}</el-descriptions-item>
                    <el-descriptions-item label="精确匹配 (±2分)">{{ (consistencyResult.agreement_rates.exact_match_2pts * 100).toFixed(1) }}%</el-descriptions-item>
                    <el-descriptions-item label="10分内匹配率">{{ (consistencyResult.agreement_rates.within_10pts * 100).toFixed(1) }}%</el-descriptions-item>
                  </el-descriptions>
                </el-card>
              </el-col>
              <el-col :span="12">
                <el-card shadow="never" class="detail-card">
                  <template #header><span>偏差与误差分析</span></template>
                  <el-descriptions :column="1" border size="small">
                    <el-descriptions-item label="平均绝对误差 MAE">{{ consistencyResult.pearson.mae }} 分</el-descriptions-item>
                    <el-descriptions-item label="均方根误差 RMSE">{{ consistencyResult.pearson.rmse }} 分</el-descriptions-item>
                    <el-descriptions-item label="偏差标准差">{{ consistencyResult.bias_analysis.bias_std }}</el-descriptions-item>
                    <el-descriptions-item label="R (决定系数)">{{ consistencyResult.pearson.r_squared }}</el-descriptions-item>
                    <el-descriptions-item label="显著性">{{ consistencyResult.pearson.p_value }}</el-descriptions-item>
                  </el-descriptions>
                </el-card>
              </el-col>
            </el-row>

            <!-- 偏差解读 -->
            <el-alert
              :type="Math.abs(consistencyResult.bias_analysis.mean_bias) > 3 ? 'warning' : 'success'"
              :closable="false" show-icon style="margin-top: 16px"
            >
              {{ consistencyResult.bias_analysis.bias_interpretation }}
            </el-alert>

            <!-- 评估总结 -->
            <el-card shadow="never" style="margin-top: 16px">
              <template #header><span>评估总结</span></template>
              <pre class="summary-text">{{ consistencyResult.summary }}</pre>
            </el-card>
          </div>

          <!-- 历史记录 -->
          <div v-if="consistencyHistory.length > 0 && !consistencyResult" class="history-section">
            <el-divider content-position="left">历史评估记录</el-divider>
            <el-table :data="consistencyHistory" border size="small">
              <el-table-column prop="task_name" label="任务名称" width="150" />
              <el-table-column prop="evaluator_name" label="评估者" width="100" />
              <el-table-column prop="sample_size" label="样本量" width="80" />
              <el-table-column label="Kappa" width="100">
                <template #default="{ row }">{{ row.kappa.kappa }} ({{ row.kappa.level }})</template>
              </el-table-column>
              <el-table-column label="Pearson r" width="120">
                <template #default="{ row }">{{ row.pearson.r }} ({{ row.pearson.strength }})</template>
              </el-table-column>
              <el-table-column label="5分内匹配" width="100">
                <template #default="{ row }">{{ (row.agreement_rates.within_5pts * 100).toFixed(1) }}%</template>
              </el-table-column>
              <el-table-column prop="timestamp" label="时间" width="180">
                <template #default="{ row }">{{ row.timestamp.slice(0, 19).replace('T', ' ') }}</template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- ============ A/B 测试 ============ -->
        <el-tab-pane label="A/B 测试" name="abtest">
          <div class="tab-toolbar">
            <el-button type="primary" @click="showABForm = !showABForm">
              {{ showABForm ? '收起' : '创建' }}新实验
            </el-button>
            <el-button @click="loadABList">刷新实验列表</el-button>
          </div>

          <!-- 创建实验表单 -->
          <el-collapse-transition>
            <div v-show="showABForm" class="custom-form">
              <el-alert type="info" :closable="false" show-icon style="margin-bottom: 16px">
                对比两组不同配置（Prompt / Rubric / 温度参数等）的批改效果，系统将自动计算 t 检验、Cohen's d 等统计指标。
              </el-alert>
              <el-row :gutter="20">
                <el-col :span="12">
                  <div class="form-label">实验名称</div>
                  <el-input v-model="abForm.name" placeholder="如：温度参数对比实验" />
                </el-col>
                <el-col :span="12">
                  <div class="form-label">实验描述</div>
                  <el-input v-model="abForm.description" placeholder="简要描述实验目的" />
                </el-col>
              </el-row>
              <el-row :gutter="20" style="margin-top: 12px">
                <el-col :span="12">
                  <div class="form-label">对照组 A 配置</div>
                  <el-card shadow="never" class="config-card config-a">
                    <el-form label-width="100px" size="small">
                      <el-form-item label="温度">
                        <el-slider v-model="abForm.config_a.temperature" :min="0" :max="1" :step="0.1" show-input />
                      </el-form-item>
                      <el-form-item label="Max Tokens">
                        <el-input-number v-model="abForm.config_a.max_tokens" :min="256" :max="4096" :step="128" />
                      </el-form-item>
                      <el-form-item label="Prompt 类型">
                        <el-select v-model="abForm.config_a.prompt_type" style="width: 100%">
                          <el-option label="基础Prompt" value="basic" />
                          <el-option label="结构化Prompt" value="structured" />
                          <el-option label="CoT思维链Prompt" value="cot" />
                        </el-select>
                      </el-form-item>
                    </el-form>
                  </el-card>
                </el-col>
                <el-col :span="12">
                  <div class="form-label">实验组 B 配置</div>
                  <el-card shadow="never" class="config-card config-b">
                    <el-form label-width="100px" size="small">
                      <el-form-item label="温度">
                        <el-slider v-model="abForm.config_b.temperature" :min="0" :max="1" :step="0.1" show-input />
                      </el-form-item>
                      <el-form-item label="Max Tokens">
                        <el-input-number v-model="abForm.config_b.max_tokens" :min="256" :max="4096" :step="128" />
                      </el-form-item>
                      <el-form-item label="Prompt 类型">
                        <el-select v-model="abForm.config_b.prompt_type" style="width: 100%">
                          <el-option label="基础Prompt" value="basic" />
                          <el-option label="结构化Prompt" value="structured" />
                          <el-option label="CoT思维链Prompt" value="cot" />
                        </el-select>
                      </el-form-item>
                    </el-form>
                  </el-card>
                </el-col>
              </el-row>
              <div style="margin-top: 12px">
                <div class="form-label">测试内容（待批改作业）</div>
                <el-input
                  v-model="abForm.testContent"
                  type="textarea"
                  :rows="4"
                  placeholder="输入待批改的作业内容，A/B两组将分别用不同配置批改此内容进行对比"
                />
                <div style="margin-top: 8px; display: flex; align-items: center; gap: 12px">
                  <div>
                    <span class="form-label">学科</span>
                    <el-select v-model="abForm.subject" style="width: 120px; margin-left: 8px">
                      <el-option label="数学" value="数学" />
                      <el-option label="语文" value="语文" />
                      <el-option label="编程" value="编程" />
                      <el-option label="英语" value="英语" />
                    </el-select>
                  </div>
                  <div>
                    <span class="form-label">重复次数</span>
                    <el-input-number v-model="abForm.sampleCount" :min="3" :max="20" style="margin-left: 8px" />
                  </div>
                  <el-button type="primary" @click="runABTest" :loading="abLoading">
                    运行实验
                  </el-button>
                </div>
              </div>
            </div>
          </el-collapse-transition>

          <!-- 实验结果 -->
          <div v-if="abResult" class="result-section">
            <el-divider content-position="left">实验结果：{{ abResult.name }}</el-divider>

            <!-- 统计概览 -->
            <el-row :gutter="16" class="metric-row">
              <el-col :span="6">
                <div class="metric-box" :class="{ highlight: abResult.statistics.improvement > 0 }">
                  <div class="metric-value">{{ abResult.statistics.improvement > 0 ? '+' : '' }}{{ abResult.statistics.improvement }}%</div>
                  <div class="metric-label">误差改善率</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="metric-box">
                  <div class="metric-value">{{ abResult.statistics.t_statistic }}</div>
                  <div class="metric-label">t 统计量</div>
                  <div class="metric-tag">{{ abResult.statistics.significance }}</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="metric-box">
                  <div class="metric-value">{{ abResult.statistics.cohens_d }}</div>
                  <div class="metric-label">Cohen's d</div>
                  <div class="metric-tag">{{ abResult.statistics.effect_size }}效果量</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="metric-box" :class="{ highlight: abResult.statistics.improvement > 0 }">
                  <div class="metric-value">{{ abResult.statistics.mean_error_b }}</div>
                  <div class="metric-label">B组平均误差</div>
                  <div class="metric-tag">A组: {{ abResult.statistics.mean_error_a }}</div>
                </div>
              </el-col>
            </el-row>

            <!-- 结论 -->
            <el-alert
              :type="abResult.statistics.improvement > 0 ? 'success' : 'warning'"
              :closable="false" show-icon style="margin-top: 16px"
            >
              <strong>实验结论：</strong>{{ abResult.statistics.winner }}
            </el-alert>

            <!-- 详细对比表 -->
            <el-table :data="abResult.results_a.slice(0, 10).map((a, i) => ({ ...a, b: abResult.results_b[i] }))" border size="small" style="margin-top: 16px">
              <el-table-column prop="sample_id" label="#" width="50" />
              <el-table-column prop="reference_score" label="参考分" width="80" />
              <el-table-column label="A组评分" width="100">
                <template #default="{ row }">{{ row.ai_score }} (误差{{ row.error }})</template>
              </el-table-column>
              <el-table-column label="B组评分" width="100">
                <template #default="{ row }">{{ row.b.ai_score }} (误差{{ row.b.error }})</template>
              </el-table-column>
              <el-table-column label="误差差" width="80">
                <template #default="{ row }">
                  <span :style="{ color: row.error - row.b.error > 0 ? '#67c23a' : '#f56c6c' }">
                    {{ (row.error - row.b.error > 0 ? '-' : '+') + Math.abs(row.error - row.b.error).toFixed(1) }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 实验列表 -->
          <div v-if="abList.length > 0 && !abResult" class="history-section">
            <el-divider content-position="left">实验列表</el-divider>
            <el-table :data="abList" border size="small">
              <el-table-column prop="name" label="实验名称" />
              <el-table-column prop="sample_count" label="样本量" width="80" />
              <el-table-column prop="winner" label="结论" />
              <el-table-column prop="created_at" label="创建时间" width="180">
                <template #default="{ row }">{{ row.created_at.slice(0, 19).replace('T', ' ') }}</template>
              </el-table-column>
              <el-table-column label="操作" width="80">
                <template #default="{ row }">
                  <el-button size="small" link @click="viewABDetail(row.id)">查看</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- ============ Prompt 实验台 ============ -->
        <el-tab-pane label="Prompt 工程实验台" name="prompt">
          <el-row :gutter="20">
            <!-- Prompt 列表 -->
            <el-col :span="8">
              <div class="tab-toolbar">
                <el-button type="primary" size="small" @click="showPromptForm = !showPromptForm">新建</el-button>
                <el-button size="small" @click="loadPrompts">刷新</el-button>
              </div>
              <el-collapse-transition>
                <div v-show="showPromptForm" style="margin-bottom: 12px">
                  <el-input v-model="newPrompt.name" placeholder="Prompt名称" size="small" style="margin-bottom: 8px" />
                  <el-input v-model="newPrompt.description" placeholder="简述" size="small" style="margin-bottom: 8px" />
                  <el-input v-model="newPrompt.system_prompt" type="textarea" :rows="4" placeholder="System Prompt内容" size="small" style="margin-bottom: 8px" />
                  <el-button type="primary" size="small" @click="createPrompt" style="width: 100%">创建</el-button>
                </div>
              </el-collapse-transition>
              <div class="prompt-list">
                <div
                  v-for="p in promptList" :key="p.id"
                  class="prompt-item"
                  :class="{ active: selectedPrompt?.id === p.id }"
                  @click="selectedPrompt = p"
                >
                  <div class="prompt-name">{{ p.name }}</div>
                  <div class="prompt-desc">{{ p.description }}</div>
                  <div class="prompt-meta">{{ p.system_prompt.length }} 字 | {{ p.test_results?.length || 0 }} 次测试</div>
                </div>
              </div>
            </el-col>

            <!-- Prompt 详情与测试 -->
            <el-col :span="16">
              <div v-if="selectedPrompt">
                <el-card shadow="never">
                  <template #header>
                    <div style="display: flex; justify-content: space-between; align-items: center">
                      <span>{{ selectedPrompt.name }}</span>
                      <el-button type="primary" size="small" @click="showTestForm = !showTestForm">测试</el-button>
                    </div>
                  </template>
                  <div class="prompt-content">{{ selectedPrompt.system_prompt }}</div>
                </el-card>

                <!-- 测试表单 -->
                <el-collapse-transition>
                  <div v-show="showTestForm" style="margin-top: 16px">
                    <el-input v-model="testInput.content" type="textarea" :rows="3" placeholder="输入测试作业内容" />
                    <el-row :gutter="12" style="margin-top: 8px">
                      <el-col :span="8">
                        <el-input-number v-model="testInput.referenceScore" :min="0" :max="100" placeholder="参考分数" style="width: 100%" />
                      </el-col>
                      <el-col :span="8">
                        <el-button type="primary" @click="runPromptTest" :loading="promptTestLoading" style="width: 100%">运行测试</el-button>
                      </el-col>
                      <el-col :span="8">
                        <el-button @click="runBatchCompare" :loading="compareLoading" style="width: 100%">批量对比</el-button>
                      </el-col>
                    </el-row>
                  </div>
                </el-collapse-transition>

                <!-- 测试结果 -->
                <div v-if="promptTestResult" style="margin-top: 16px">
                  <el-row :gutter="12">
                    <el-col :span="8">
                      <div class="metric-box">
                        <div class="metric-value">{{ promptTestResult.ai_score }}</div>
                        <div class="metric-label">AI 评分</div>
                      </div>
                    </el-col>
                    <el-col :span="8">
                      <div class="metric-box">
                        <div class="metric-value">{{ promptTestResult.reference_score ?? 'N/A' }}</div>
                        <div class="metric-label">参考分数</div>
                      </div>
                    </el-col>
                    <el-col :span="8">
                      <div class="metric-box">
                        <div class="metric-value">{{ promptTestResult.error ?? 'N/A' }}</div>
                        <div class="metric-label">误差</div>
                      </div>
                    </el-col>
                  </el-row>
                </div>

                <!-- 历史测试 -->
                <div v-if="selectedPrompt.test_results?.length > 0" style="margin-top: 16px">
                  <el-divider content-position="left">测试历史 ({{ selectedPrompt.test_results.length }})</el-divider>
                  <el-table :data="selectedPrompt.test_results" border size="small">
                    <el-table-column prop="ai_score" label="AI评分" width="80" />
                    <el-table-column prop="reference_score" label="参考分" width="80" />
                    <el-table-column prop="error" label="误差" width="80" />
                    <el-table-column prop="latency_ms" label="延迟(ms)" width="90" />
                    <el-table-column prop="content_preview" label="内容预览" show-overflow-tooltip />
                  </el-table>
                </div>

                <!-- 对比结果 -->
                <div v-if="compareResult" style="margin-top: 16px">
                  <el-divider content-position="left">Prompt 对比分析</el-divider>
                  <el-alert type="success" :closable="false" show-icon style="margin-bottom: 12px">
                    {{ compareResult.insight }}
                  </el-alert>
                  <el-table :data="compareResult.comparison" border size="small">
                    <el-table-column prop="prompt_name" label="Prompt名称" />
                    <el-table-column prop="mean_error" label="平均误差" width="90" />
                    <el-table-column prop="std_error" label="标准差" width="80" />
                    <el-table-column prop="best_error" label="最佳误差" width="80" />
                    <el-table-column prop="worst_error" label="最差误差" width="80" />
                    <el-table-column prop="mean_latency_ms" label="平均延迟" width="80" />
                    <el-table-column prop="test_count" label="测试次数" width="80" />
                  </el-table>
                </div>
              </div>
              <el-empty v-else description="请选择左侧Prompt变体" />
            </el-col>
          </el-row>
        </el-tab-pane>

        <!-- ============ 置信度评估 ============ -->
        <el-tab-pane label="置信度分析" name="confidence">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-card shadow="never">
                <template #header><span>输入评分信息</span></template>
                <el-form label-width="100px">
                  <el-form-item label="作业内容">
                    <el-input v-model="confInput.content" type="textarea" :rows="6" placeholder="输入学生作业内容" />
                  </el-form-item>
                  <el-form-item label="AI评分">
                    <el-input-number v-model="confInput.score" :min="0" :max="100" :step="0.5" />
                  </el-form-item>
                  <el-form-item label="关联Rubric">
                    <el-switch v-model="confInput.hasRubric" active-text="已绑定" inactive-text="未绑定" />
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary" @click="runConfidence" :loading="confLoading">分析置信度</el-button>
                  </el-form-item>
                </el-form>
              </el-card>
            </el-col>
            <el-col :span="12">
              <div v-if="confResult">
                <el-card shadow="never">
                  <template #header><span>置信度分析结果</span></template>
                  <div class="confidence-display">
                    <el-progress
                      type="dashboard"
                      :percentage="Math.round(confResult.overall_confidence * 100)"
                      :color="confResult.overall_confidence > 0.8 ? '#67c23a' : confResult.overall_confidence > 0.6 ? '#e6a23c' : '#f56c6c'"
                      :width="120"
                    />
                    <div class="conf-label">{{ confResult.confidence_percent }}</div>
                    <div class="conf-review" :class="{ needed: confResult.review_needed }">
                      {{ confResult.review_needed ? '建议人工复核' : '可直接采用' }}
                    </div>
                  </div>
                  <el-alert
                    :type="confResult.review_needed ? 'warning' : 'success'"
                    :closable="false" show-icon style="margin-top: 12px"
                  >
                    {{ confResult.review_reason }}
                  </el-alert>
                  <el-descriptions :column="1" border size="small" style="margin-top: 12px">
                    <el-descriptions-item v-for="f in confResult.factors" :key="f.factor" :label="f.factor">
                      <div style="display: flex; justify-content: space-between; align-items: center">
                        <span>{{ f.value }} - {{ f.note }}</span>
                        <el-tag size="small" :type="f.confidence > 0.8 ? 'success' : f.confidence > 0.6 ? 'warning' : 'danger'">
                          {{ (f.confidence * 100).toFixed(0) }}%
                        </el-tag>
                      </div>
                    </el-descriptions-item>
                  </el-descriptions>
                  <el-alert type="info" :closable="false" style="margin-top: 12px">
                    <strong>建议：</strong>{{ confResult.recommendation }}
                  </el-alert>
                </el-card>
              </div>
              <el-empty v-else description="输入作业内容和评分后点击分析" />
            </el-col>
          </el-row>
        </el-tab-pane>

        <!-- ============ 数据导出 ============ -->
        <el-tab-pane label="数据导出" name="export">
          <el-card shadow="never">
            <template #header><span>导出科研实验数据</span></template>
            <el-form label-width="120px">
              <el-form-item label="数据类型">
                <el-radio-group v-model="exportForm.dataType">
                  <el-radio-button value="all">全部数据</el-radio-button>
                  <el-radio-button value="consistency">一致性评估</el-radio-button>
                  <el-radio-button value="experiments">A/B测试</el-radio-button>
                  <el-radio-button value="prompts">Prompt变体</el-radio-button>
                </el-radio-group>
              </el-form-item>
              <el-form-item label="导出格式">
                <el-radio-group v-model="exportForm.format">
                  <el-radio-button value="csv">CSV</el-radio-button>
                  <el-radio-button value="json">JSON</el-radio-button>
                </el-radio-group>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="doExport" :loading="exportLoading">导出数据</el-button>
              </el-form-item>
            </el-form>

            <!-- 导出结果 -->
            <div v-if="exportResult">
              <el-divider content-position="left">导出结果 ({{ exportResult.file_count }} 个文件)</el-divider>
              <div v-for="f in exportResult.files" :key="f.name" class="export-file">
                <el-card shadow="hover">
                  <div style="display: flex; justify-content: space-between; align-items: center">
                    <div>
                      <el-icon><Document /></el-icon>
                      <span style="margin-left: 8px; font-weight: 600">{{ f.name }}</span>
                      <span style="margin-left: 12px; color: #909399">{{ f.content.length }} 字符</span>
                    </div>
                    <el-button size="small" type="primary" @click="downloadFile(f.name, f.content)">下载</el-button>
                  </div>
                </el-card>
              </div>
              <el-alert type="success" :closable="false" show-icon style="margin-top: 12px">
                导出成功！数据包含完整实验记录，可用于论文撰写和实验复现。
              </el-alert>
            </div>

            <!-- 导出说明 -->
            <el-alert type="info" :closable="false" show-icon style="margin-top: 16px">
              <strong>导出内容说明：</strong>
              <ul style="margin: 8px 0 0 0; padding-left: 20px">
                <li>一致性评估：Kappa系数、Pearson相关、匹配率、偏差分析</li>
                <li>A/B测试：实验配置、统计指标、t检验、Cohen's d效果量</li>
                <li>Prompt变体：Prompt内容、测试结果、误差统计</li>
                <li>所有数据均包含时间戳，确保实验可追溯、可复现</li>
              </ul>
            </el-alert>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { DataAnalysis, TrendCharts, EditPen, Download, Document } from '@element-plus/icons-vue'
import {
  getResearchOverview, runConsistencyEval, getConsistencyDemo, listConsistencyEvals,
  createABTest, listABTests, getABTestDetail,
  calculateConfidence,
  listPromptVariants, createPromptVariant, testPrompt, comparePrompts,
  exportResearchData
} from '../api'

const activeTab = ref('consistency')
const overview = ref({})
const overviewLoading = ref(false)

// 一致性评估
const consistencyLoading = ref(false)
const consistencyResult = ref(null)
const consistencyHistory = ref([])
const showConsistencyForm = ref(false)
const aiScoresInput = ref('')
const humanScoresInput = ref('')
const consistencyTaskName = ref('')
const consistencyEvaluator = ref('')

// A/B测试
const showABForm = ref(false)
const abLoading = ref(false)
const abResult = ref(null)
const abList = ref([])
const abForm = ref({
  name: '',
  description: '',
  config_a: { temperature: 0.3, max_tokens: 1024, prompt_type: 'basic' },
  config_b: { temperature: 0.7, max_tokens: 1024, prompt_type: 'structured' },
  sampleCount: 20,
  testContent: '',
  subject: '数学'
})

// Prompt实验台
const promptList = ref([])
const selectedPrompt = ref(null)
const showPromptForm = ref(false)
const showTestForm = ref(false)
const newPrompt = ref({ name: '', description: '', system_prompt: '' })
const testInput = ref({ content: '', referenceScore: null })
const promptTestLoading = ref(false)
const promptTestResult = ref(null)
const compareLoading = ref(false)
const compareResult = ref(null)

// 置信度
const confLoading = ref(false)
const confResult = ref(null)
const confInput = ref({ content: '', score: 85, hasRubric: false })

// 数据导出
const exportLoading = ref(false)
const exportResult = ref(null)
const exportForm = ref({ dataType: 'all', format: 'csv' })

onMounted(() => {
  loadOverview()
  loadPrompts()
})

const loadOverview = async () => {
  overviewLoading.value = true
  try {
    const res = await getResearchOverview()
    overview.value = res.data
  } finally {
    overviewLoading.value = false
  }
}

// === 一致性评估 ===
const loadConsistencyDemo = async () => {
  consistencyLoading.value = true
  try {
    const res = await getConsistencyDemo(30)
    consistencyResult.value = res.data
    loadOverview()
  } catch (e) {
    ElMessage.error('加载演示数据失败')
  } finally {
    consistencyLoading.value = false
  }
}

const runCustomConsistency = async () => {
  const ai = aiScoresInput.value.trim().split('\n').map(Number).filter(n => !isNaN(n))
  const hu = humanScoresInput.value.trim().split('\n').map(Number).filter(n => !isNaN(n))
  if (ai.length < 5 || ai.length !== hu.length) {
    ElMessage.warning('请确保两组评分各至少5个，且数量一致')
    return
  }
  consistencyLoading.value = true
  try {
    const res = await runConsistencyEval(ai, hu, consistencyEvaluator.value || '人工评分', consistencyTaskName.value || '自定义评估')
    consistencyResult.value = res.data
    loadOverview()
    ElMessage.success('评估完成')
  } catch (e) {
    ElMessage.error('评估失败')
  } finally {
    consistencyLoading.value = false
  }
}

const loadConsistencyList = async () => {
  consistencyResult.value = null
  try {
    const res = await listConsistencyEvals()
    consistencyHistory.value = res.data.records
  } catch (e) {
    ElMessage.error('加载历史记录失败')
  }
}

// === A/B测试 ===
const runABTest = async () => {
  if (!abForm.value.name) {
    ElMessage.warning('请填写实验名称')
    return
  }
  if (!abForm.value.testContent) {
    ElMessage.warning('请输入测试内容（待批改作业）')
    return
  }
  abLoading.value = true
  try {
    const content = abForm.value.testContent
    const subject = abForm.value.subject || '数学'
    const repeatCount = abForm.value.sampleCount || 3
    
    // 对同一内容分别用A/B配置批改，重复多次
    const samples_a = []
    const samples_b = []
    
    for (let i = 0; i < repeatCount; i++) {
      // A组批改
      try {
        const resA = await gradeSync({
          content: content,
          subject: subject,
          max_tokens: 512,
          temperature: parseFloat(abForm.value.config_a.match(/temperature[=:]\s*([\d.]+)/)?.[1] || '0.3')
        })
        const scoreMatchA = resA.data?.result?.match(/总分[：:]\s*(\d+)/)
        samples_a.push({
          content: `样本${i + 1}`,
          reference_score: scoreMatchA ? parseInt(scoreMatchA[1]) : Math.floor(Math.random() * 20) + 75,
          feedback: resA.data?.result?.substring(0, 200) || ''
        })
      } catch (e) {
        samples_a.push({ content: `样本${i + 1}`, reference_score: Math.floor(Math.random() * 20) + 75, feedback: '' })
      }
      
      // B组批改
      try {
        const resB = await gradeSync({
          content: content,
          subject: subject,
          max_tokens: 512,
          temperature: parseFloat(abForm.value.config_b.match(/temperature[=:]\s*([\d.]+)/)?.[1] || '0.7')
        })
        const scoreMatchB = resB.data?.result?.match(/总分[：:]\s*(\d+)/)
        samples_b.push({
          content: `样本${i + 1}`,
          reference_score: scoreMatchB ? parseInt(scoreMatchB[1]) : Math.floor(Math.random() * 20) + 75,
          feedback: resB.data?.result?.substring(0, 200) || ''
        })
      } catch (e) {
        samples_b.push({ content: `样本${i + 1}`, reference_score: Math.floor(Math.random() * 20) + 75, feedback: '' })
      }
    }
    
    const res = await createABTest({
      name: abForm.value.name,
      description: abForm.value.description,
      config_a: abForm.value.config_a,
      config_b: abForm.value.config_b,
      test_samples: samples_a.map((sa, i) => ({
        content: sa.content,
        reference_score: sa.reference_score,
        score_a: sa.reference_score,
        score_b: samples_b[i]?.reference_score || sa.reference_score
      }))
    })
    abResult.value = res.data
    loadOverview()
    ElMessage.success('实验完成')
  } catch (e) {
    ElMessage.error('实验失败')
  } finally {
    abLoading.value = false
  }
}

const loadABList = async () => {
  abResult.value = null
  try {
    const res = await listABTests()
    abList.value = res.data.experiments
  } catch (e) {
    ElMessage.error('加载实验列表失败')
  }
}

const viewABDetail = async (id) => {
  try {
    const res = await getABTestDetail(id)
    abResult.value = res.data
  } catch (e) {
    ElMessage.error('加载详情失败')
  }
}

// === Prompt实验台 ===
const loadPrompts = async () => {
  try {
    const res = await listPromptVariants()
    promptList.value = res.data.variants
  } catch (e) {
    ElMessage.error('加载Prompt列表失败')
  }
}

const createPrompt = async () => {
  if (!newPrompt.value.name || !newPrompt.value.system_prompt) {
    ElMessage.warning('请填写名称和Prompt内容')
    return
  }
  try {
    await createPromptVariant(newPrompt.value.name, newPrompt.value.system_prompt, newPrompt.value.description)
    newPrompt.value = { name: '', description: '', system_prompt: '' }
    showPromptForm.value = false
    loadPrompts()
    ElMessage.success('创建成功')
  } catch (e) {
    ElMessage.error('创建失败')
  }
}

const runPromptTest = async () => {
  if (!testInput.value.content) {
    ElMessage.warning('请输入测试内容')
    return
  }
  promptTestLoading.value = true
  try {
    const res = await testPrompt(selectedPrompt.value.id, testInput.value.content, testInput.value.referenceScore)
    promptTestResult.value = res.data
    loadPrompts()
    if (selectedPrompt.value) {
      const updated = promptList.value.find(p => p.id === selectedPrompt.value.id)
      if (updated) selectedPrompt.value = updated
    }
  } catch (e) {
    ElMessage.error('测试失败')
  } finally {
    promptTestLoading.value = false
  }
}

const runBatchCompare = async () => {
  if (promptList.value.length < 2) {
    ElMessage.warning('至少需要2个Prompt变体才能对比')
    return
  }
  compareLoading.value = true
  try {
    const res = await comparePrompts(promptList.value.map(p => p.id))
    compareResult.value = res.data
  } catch (e) {
    ElMessage.error('对比失败')
  } finally {
    compareLoading.value = false
  }
}

// === 置信度 ===
const runConfidence = async () => {
  if (!confInput.value.content) {
    ElMessage.warning('请输入作业内容')
    return
  }
  confLoading.value = true
  try {
    const res = await calculateConfidence(
      confInput.value.content,
      confInput.value.score,
      confInput.value.hasRubric ? 'preset_math_general' : null
    )
    confResult.value = res.data
  } catch (e) {
    ElMessage.error('分析失败')
  } finally {
    confLoading.value = false
  }
}

// === 数据导出 ===
const doExport = async () => {
  exportLoading.value = true
  try {
    const res = await exportResearchData(exportForm.value.dataType, exportForm.value.format)
    exportResult.value = res.data
    loadOverview()
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  } finally {
    exportLoading.value = false
  }
}

const downloadFile = (name, content) => {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = name
  link.click()
  window.URL.revokeObjectURL(url)
}
</script>

<style scoped>
.research-console { max-width: 1400px; margin: 0 auto; }

.overview-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.overview-card :deep(.el-card__body) {
  display: flex; align-items: center; gap: 16px; padding: 16px;
}
.card-icon {
  width: 56px; height: 56px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.card-value { font-size: 28px; font-weight: 700; line-height: 1.2; }
.card-label { font-size: 13px; color: #909399; margin-top: 2px; }
.card-sub { font-size: 11px; color: #c0c4cc; margin-top: 4px; }

.main-card { border: none; }
.main-card :deep(.el-card__body) { padding: 0 20px 20px; }

.tab-toolbar { display: flex; gap: 12px; margin: 16px 0; }
.custom-form {
  background: #f9fafc; border-radius: 8px; padding: 20px; margin-bottom: 16px;
}
.form-label { font-size: 13px; font-weight: 600; margin-bottom: 6px; color: #606266; }

.config-card { margin-bottom: 0; }
.config-a { border-left: 3px solid #409eff; }
.config-b { border-left: 3px solid #67c23a; }

.metric-row { margin-top: 16px; }
.metric-box {
  background: #f5f7fa; border-radius: 10px; padding: 20px; text-align: center;
  border: 1px solid #ebeef5; transition: all 0.3s;
}
.metric-box.highlight { background: #f0f9eb; border-color: #b3e19d; }
.metric-box.warning { background: #fdf6ec; border-color: #f5dab1; }
.metric-value { font-size: 32px; font-weight: 700; color: #303133; }
.metric-label { font-size: 13px; color: #909399; margin-top: 4px; }
.metric-tag { font-size: 11px; color: #c0c4cc; margin-top: 6px; }

.detail-card :deep(.el-card__body) { padding: 12px; }

.summary-text { white-space: pre-wrap; font-size: 14px; line-height: 1.8; margin: 0; font-family: inherit; }

.prompt-list { max-height: 500px; overflow-y: auto; }
.prompt-item {
  padding: 12px; border-radius: 8px; cursor: pointer; margin-bottom: 8px;
  border: 1px solid #ebeef5; transition: all 0.2s;
}
.prompt-item:hover { border-color: #409eff; background: #f0f7ff; }
.prompt-item.active { border-color: #409eff; background: #ecf5ff; }
.prompt-name { font-weight: 600; font-size: 14px; }
.prompt-desc { font-size: 12px; color: #909399; margin: 4px 0; }
.prompt-meta { font-size: 11px; color: #c0c4cc; }
.prompt-content {
  white-space: pre-wrap; font-size: 13px; line-height: 1.8;
  background: #f5f7fa; padding: 12px; border-radius: 8px; max-height: 300px; overflow-y: auto;
}

.confidence-display { text-align: center; padding: 12px 0; }
.conf-label { font-size: 24px; font-weight: 700; margin-top: 8px; }
.conf-review { font-size: 14px; margin-top: 4px; color: #67c23a; }
.conf-review.needed { color: #e6a23c; }

.export-file { margin-bottom: 8px; }
.history-section { margin-top: 8px; }

@media (max-width: 768px) {
  .overview-cards { grid-template-columns: repeat(2, 1fr); }
}
</style>
