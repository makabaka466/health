<template>
  <div class="health-data-container">
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon">
          <el-icon size="32" color="#409EFF">
            <DataAnalysis />
          </el-icon>
        </div>
        <div class="header-text">
          <h1>健康数据</h1>
          <p>管理和查看您的健康数据记录</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button type="primary" class="add-btn" @click="openManualDialog">
          <el-icon><Plus /></el-icon>
          手动录入
        </el-button>
        <el-button class="upload-btn" @click="openFileDialog">
          <el-icon><UploadFilled /></el-icon>
          上传文件
        </el-button>
      </div>
    </div>
    
    <div class="content-section">
      <el-row :gutter="24">
        <el-col :span="24">
          <el-card class="stats-card" shadow="hover">
            <div class="stats-grid">
              <div v-for="item in statsCards" :key="item.title" class="stat-item">
                <div class="stat-icon" :style="{ color: item.color }">
                  <el-icon size="22"><component :is="item.icon" /></el-icon>
                </div>
                <div class="stat-info">
                  <h3>{{ item.title }}</h3>
                  <p class="stat-value">{{ item.value }}<span class="stat-unit">{{ item.unit }}</span></p>
                  <p class="stat-desc">{{ item.desc }}</p>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <el-row :gutter="24" style="margin-top: 24px;">
        <el-col :span="16">
          <el-card class="chart-card" shadow="hover">
            <div class="card-header">
              <h3>健康趋势</h3>
              <el-button type="text" @click="refreshData">刷新</el-button>
            </div>
            <div class="chart-placeholder">
              <div class="placeholder-content" v-if="healthRecords.length === 0">
                <el-icon size="48" color="#cbd5e1"><TrendCharts /></el-icon>
                <p>暂无数据，请添加健康记录</p>
              </div>
              <div v-else>
                <el-table :data="healthRecords" style="width: 100%" max-height="320">
                  <el-table-column prop="data_title" label="记录标题" min-width="180" show-overflow-tooltip />
                  <el-table-column prop="recorded_at" label="记录时间" width="180">
                    <template #default="scope">
                      {{ formatDate(scope.row.recorded_at) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="height" label="身高(cm)" width="100">
                    <template #default="scope">{{ displayMetric(scope.row, scope.row.height) }}</template>
                  </el-table-column>
                  <el-table-column prop="weight" label="体重(kg)" width="100">
                    <template #default="scope">{{ displayMetric(scope.row, scope.row.weight) }}</template>
                  </el-table-column>
                  <el-table-column prop="blood_pressure" label="血压(舒/收)" width="120">
                    <template #default="scope">{{ displayMetric(scope.row, scope.row.blood_pressure) }}</template>
                  </el-table-column>
                  <el-table-column prop="blood_lipid" label="血脂" width="100">
                    <template #default="scope">{{ displayMetric(scope.row, scope.row.blood_lipid) }}</template>
                  </el-table-column>
                  <el-table-column prop="heart_rate" label="心率" width="100">
                    <template #default="scope">{{ displayMetric(scope.row, scope.row.heart_rate) }}</template>
                  </el-table-column>
                  <el-table-column prop="blood_sugar" label="血糖" width="100">
                    <template #default="scope">{{ displayMetric(scope.row, scope.row.blood_sugar) }}</template>
                  </el-table-column>
                  <el-table-column :label="privacyColumnText" width="130" fixed="right">
                    <template #default="scope">
                      <el-space :size="6" wrap>
                        <el-tag :type="scope.row.is_private ? 'warning' : 'success'" size="small">
                          {{ scope.row.is_private ? privateText : publicText }}
                        </el-tag>
                        <el-tag v-if="scope.row.requires_private_key" type="danger" size="small">
                          {{ lockedTagText }}
                        </el-tag>
                      </el-space>
                    </template>
                  </el-table-column>
                  <el-table-column label="记录类型" width="100">
                    <template #default="scope">
                      <el-tag :type="recordTypeTagType(scope.row.record_type)" size="small">
                        {{ recordTypeLabel(scope.row.record_type) }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="附件" width="140">
                    <template #default="scope">
                      <span v-if="scope.row.is_private">{{ hiddenText }}</span>
                      <el-button v-else-if="scope.row.health_data_file" type="primary" text @click="openAttachment(scope.row)">
                        {{ scope.row.record_type === 'word' ? downloadWordText : viewPdfText }}
                      </el-button>
                      <span v-else>-</span>
                    </template>
                  </el-table-column>
                  <el-table-column :label="onchainColumnText" width="160">
                    <template #default="scope">
                      <el-popover
                        v-if="hasOnchainProof(scope.row)"
                        placement="top"
                        :width="360"
                        trigger="hover"
                      >
                        <template #reference>
                          <el-tag
                            size="small"
                            :type="resolveOnchainTagType(scope.row)"
                            class="onchain-tag"
                          >
                            {{ resolveOnchainLabel(scope.row) }}
                          </el-tag>
                        </template>
                        <div class="onchain-popover">
                          <div class="onchain-popover__title">链上存证详情</div>
                          <div class="onchain-popover__row">
                            <span class="onchain-popover__label">校验结果</span>
                            <span class="onchain-popover__value">{{ resolveOnchainTitle(scope.row) }}</span>
                          </div>
                          <div v-if="scope.row.onchain_tx_hash" class="onchain-popover__row">
                            <span class="onchain-popover__label">Tx Hash</span>
                            <span class="onchain-popover__hash">{{ scope.row.onchain_tx_hash }}</span>
                          </div>
                          <div v-if="scope.row.onchain_data_id" class="onchain-popover__row">
                            <span class="onchain-popover__label">Data ID</span>
                            <span class="onchain-popover__hash">{{ scope.row.onchain_data_id }}</span>
                          </div>
                        </div>
                      </el-popover>
                      <el-tag
                        v-else
                        size="small"
                        :type="resolveOnchainTagType(scope.row)"
                      >
                        {{ resolveOnchainLabel(scope.row) }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column :label="actionsColumnText" width="220" fixed="right">
                    <template #default="scope">
                      <el-button v-if="scope.row.is_private" type="primary" text @click="viewPrivateRecord(scope.row)">
                        {{ scope.row.record_type === 'manual' ? revealDataText : revealAttachmentText }}
                      </el-button>
                      <el-button type="text" @click="openGrantDialog(scope.row)">
                        {{ grantText }}
                      </el-button>
                      <el-button type="text" @click="editRecord(scope.row)">
                        {{ scope.row.record_type === 'pdf' ? replacePdfText : editText }}
                      </el-button>
                      <el-button type="text" style="color: #f56c6c" @click="deleteRecord(scope.row)">{{ deleteText }}</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="8">
          <el-card class="recent-card" shadow="hover">
            <div class="card-header">
              <h3>数据分析</h3>
              <el-button type="text" @click="analyzeHealthData">分析</el-button>
            </div>
            <div class="analysis-result" v-if="healthAnalysis.recommendations">
              <div class="analysis-item">
                <h4>健康建议</h4>
                <ul>
                  <li v-for="recommendation in healthAnalysis.recommendations" :key="recommendation">
                    {{ recommendation }}
                  </li>
                </ul>
              </div>
            </div>
            <div class="placeholder-content" v-else>
              <el-icon size="48" color="#cbd5e1"><DataAnalysis /></el-icon>
              <p>点击分析获取健康建议</p>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 添加/编辑健康数据对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑健康数据' : '添加健康数据'"
      width="600px"
    >
      <el-form :model="healthForm" :rules="healthRules" ref="healthFormRef" label-width="120px">
        <el-form-item label="记录标题" prop="data_title">
          <el-input
            v-model="healthForm.data_title"
            maxlength="80"
            show-word-limit
            placeholder="例如：2026-05-04 体检报告 / 晨起血压记录"
          />
        </el-form-item>
        <template v-if="formMode === 'manual'">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="体重(kg)" prop="weight">
              <el-input-number v-model="healthForm.weight" :precision="1" :step="0.1" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="身高(cm)" prop="height">
              <el-input-number v-model="healthForm.height" :precision="1" :step="0.1" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="血压(舒/收)" prop="blood_pressure">
              <el-input
                v-model="healthForm.blood_pressure"
                placeholder="例如 80/120（前舒张压，后收缩压）"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="血脂" prop="blood_lipid">
              <el-input-number v-model="healthForm.blood_lipid" :precision="1" :step="0.1" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="心率" prop="heart_rate">
              <el-input-number v-model="healthForm.heart_rate" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="血糖" prop="blood_sugar">
              <el-input-number v-model="healthForm.blood_sugar" :precision="1" :step="0.1" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="其他说明" prop="other_text">
          <el-input
            v-model="healthForm.other_text"
            type="textarea"
            :rows="3"
            placeholder="可填写如：睡眠情况、饮食变化、服药信息等"
          />
        </el-form-item>
        
        <el-form-item label="记录时间" prop="recorded_at">
          <el-date-picker
            v-model="healthForm.recorded_at"
            type="datetime"
            placeholder="选择日期时间"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="隐私保护">
          <el-switch
            v-model="healthForm.is_private"
            active-text="保密"
            inactive-text="公开"
          />
        </el-form-item>
        </template>

        <template v-else>
        <el-form-item label="记录时间" prop="recorded_at">
          <el-date-picker
            v-model="healthForm.recorded_at"
            type="datetime"
            placeholder="选择日期时间"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="隐私保护">
          <el-switch
            v-model="healthForm.is_private"
            active-text="保密"
            inactive-text="公开"
          />
        </el-form-item>

        <el-form-item :label="fileUploadLabel">
          <div class="upload-row">
            <el-upload
              :accept="fileAccept"
              :show-file-list="false"
              :auto-upload="false"
              :on-change="handleFileChange"
            >
              <el-button type="primary" plain>{{ uploadButtonLabel }}</el-button>
            </el-upload>
            <el-button v-if="healthForm.health_data_file" text type="danger" @click="removeFile">
              移除文件
            </el-button>
          </div>
          <el-alert
            :title="fileUploadAlertText"
            type="info"
            show-icon
            :closable="false"
            style="margin-top: 10px"
          />
          <div v-if="healthForm.health_data_file" class="upload-preview">
            <el-tag type="info">{{ healthForm.health_data_file_name || defaultUploadedFileName }}</el-tag>
          </div>
        </el-form-item>
        </template>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveHealthData" :loading="saving">
            {{ isEditing ? '更新' : '保存' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog
      v-model="privatePreviewDialogVisible"
      :title="privatePreviewTitle"
      width="640px"
    >
      <template v-if="privatePreviewRecord">
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="previewRecordedAtLabel">
            {{ formatDate(privatePreviewRecord.recorded_at) }}
          </el-descriptions-item>
          <el-descriptions-item :label="previewRecordTypeLabel">
            {{ recordTypeLabel(privatePreviewRecord.record_type) }}
          </el-descriptions-item>
          <el-descriptions-item :label="previewHeightLabel">
            {{ previewMetric(privatePreviewRecord.height) }}
          </el-descriptions-item>
          <el-descriptions-item :label="previewWeightLabel">
            {{ previewMetric(privatePreviewRecord.weight) }}
          </el-descriptions-item>
          <el-descriptions-item :label="previewBloodPressureLabel">
            {{ previewMetric(privatePreviewRecord.blood_pressure) }}
          </el-descriptions-item>
          <el-descriptions-item :label="previewBloodLipidLabel">
            {{ previewMetric(privatePreviewRecord.blood_lipid) }}
          </el-descriptions-item>
          <el-descriptions-item :label="previewHeartRateLabel">
            {{ previewMetric(privatePreviewRecord.heart_rate) }}
          </el-descriptions-item>
          <el-descriptions-item :label="previewBloodSugarLabel">
            {{ previewMetric(privatePreviewRecord.blood_sugar) }}
          </el-descriptions-item>
          <el-descriptions-item :label="previewPrivacyLabel">
            {{ privatePreviewRecord.is_private ? privateText : publicText }}
          </el-descriptions-item>
          <el-descriptions-item :label="previewOnchainLabel">
            {{ resolveOnchainLabel(privatePreviewRecord) }}
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="privatePreviewRecord.other_text" class="private-preview-text">
          <div class="private-preview-text__label">{{ previewOtherTextLabel }}</div>
          <div class="private-preview-text__content">{{ privatePreviewRecord.other_text }}</div>
        </div>

        <div
          v-else-if="showRawPrivateContent(privatePreviewRecord)"
          class="private-preview-text"
        >
          <div class="private-preview-text__label">{{ previewRawContentLabel }}</div>
          <div class="private-preview-text__content">{{ privatePreviewRecord.raw_content }}</div>
        </div>

        <div v-if="privatePreviewRecord.health_data_file" class="private-preview-actions">
          <el-button type="primary" @click="openUnlockedAttachment(privatePreviewRecord)">
            {{ previewAttachmentText }}
          </el-button>
        </div>
      </template>
    </el-dialog>


    <el-dialog
      v-model="grantDialogVisible"
      :title="grantDialogTitle"
      width="760px"
    >
      <template v-if="grantTargetRecord">
        <el-alert
          :title="grantDialogTip"
          type="info"
          show-icon
          :closable="false"
          style="margin-bottom: 14px"
        />
        <div class="grant-record-meta">
          <el-tag type="primary" size="small">记录ID：{{ grantTargetRecord.id }}</el-tag>
          <el-tag size="small">{{ formatDate(grantTargetRecord.recorded_at) }}</el-tag>
          <el-tag :type="grantTargetRecord.is_private ? 'warning' : 'success'" size="small">
            {{ grantTargetRecord.is_private ? privateText : publicText }}
          </el-tag>
        </div>

        <el-form :model="grantForm" label-width="96px" class="grant-form">
          <el-form-item :label="doctorFieldLabel">
            <el-select v-model="grantForm.doctor_id" :placeholder="doctorFieldPlaceholder" style="width: 100%">
              <el-option
                v-for="adminUser in grantableUsers"
                :key="adminUser.id"
                :label="`${adminUser.username}（管理员）`"
                :value="adminUser.id"
              >
                <div class="doctor-option">
                  <span class="doctor-option__name">{{ adminUser.username }}</span>
                  <span class="doctor-option__meta">系统管理员</span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item :label="expiryFieldLabel">
            <el-input-number v-model="grantForm.expires_days" :min="1" :max="365" />
            <span class="grant-form__suffix">{{ expiryFieldSuffix }}</span>
          </el-form-item>
          <el-form-item :label="remarkFieldLabel">
            <el-input v-model="grantForm.remark" type="textarea" :rows="2" :placeholder="remarkFieldPlaceholder" />
          </el-form-item>
        </el-form>

        <div class="grant-actions">
          <el-button type="primary" @click="addGrant">{{ addGrantText }}</el-button>
        </div>

        <div class="grant-list">
          <div class="grant-list__header">{{ grantedListTitle }}</div>
          <el-empty v-if="currentRecordGrants.length === 0" :description="emptyGrantListText" />
          <el-table v-else :data="currentRecordGrants" size="small" border>
            <el-table-column prop="grantee_username" label="被授权用户" min-width="140" />
            <el-table-column label="有效期(天)" width="100">
              <template #default="scope">
                {{ resolveExpiresDays(scope.row) }}
              </template>
            </el-table-column>
            <el-table-column label="到期时间" min-width="170">
              <template #default="scope">
                {{ formatDate(scope.row.expires_at) }}
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="scope">
                <el-tag :type="resolveGrantStatus(scope.row).type" size="small">
                  {{ resolveGrantStatus(scope.row).label }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="授权时间" min-width="160">
              <template #default="scope">
                {{ formatDate(scope.row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="备注" min-width="160">
              <template #default="scope">
                {{ scope.row.remark || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="scope">
                <el-button
                  v-if="!scope.row.revoked_at"
                  type="danger"
                  text
                  @click="revokeGrant(scope.row.id)"
                >
                  {{ revokeText }}
                </el-button>
                <span v-else style="color: #909399;">-</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </template>
    </el-dialog>  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated } from 'vue'
import { ElMessage } from 'element-plus'
import { healthApi } from '../api/health'
import { getPublicSystemSettings } from '../api/adminSystem'

const healthRecords = ref([])
const healthSummary = ref({})
const healthAnalysis = ref({})
const systemSettings = ref({
  default_health_data_public: false
})
const dialogVisible = ref(false)
const isEditing = ref(false)
const formMode = ref('manual')
const saving = ref(false)
const healthFormRef = ref()
const privatePreviewDialogVisible = ref(false)
const privatePreviewRecord = ref(null)
const grantDialogVisible = ref(false)
const grantTargetRecord = ref(null)
const grantableUsers = ref([])
const recordGrants = ref([])
const grantForm = ref({
  doctor_id: '',
  expires_days: 30,
  remark: ''
})

const healthForm = ref({
  data_title: '',
  weight: null,
  height: null,
  blood_pressure: '',
  blood_lipid: null,
  heart_rate: null,
  blood_sugar: null,
  other_text: '',
  record_type: 'manual',
  is_private: true,
  health_data_file_name: null,
  health_data_file: null,
  recorded_at: new Date()
})

const unlockSuccessText = '\u5df2\u81ea\u52a8\u89e3\u9501\u79c1\u5bc6\u5065\u5eb7\u6570\u636e'
const lockedRecordText = '\u8be5\u8bb0\u5f55\u4e3a\u4fdd\u5bc6\u6570\u636e\uff0c\u6b63\u5728\u5c1d\u8bd5\u4f7f\u7528\u5f53\u524d\u7528\u6237\u5bc6\u94a5\u81ea\u52a8\u89e3\u9501'
const unlockUnavailableText = '\u5f53\u524d\u8d26\u53f7\u7f3a\u5c11\u53ef\u7528\u5bc6\u94a5\uff0c\u65e0\u6cd5\u81ea\u52a8\u89e3\u9501\u79c1\u5bc6\u5065\u5eb7\u6570\u636e'
const lockedTagText = '\u672a\u89e3\u9501'
const hiddenText = '\u5df2\u9690\u85cf'
const privacyColumnText = '\u9690\u79c1'
const privateText = '\u4fdd\u5bc6'
const publicText = '\u516c\u5f00'
const actionsColumnText = '\u64cd\u4f5c'
const revealDataText = '\u5c55\u793a\u6570\u636e'
const revealAttachmentText = '\u5c55\u793a\u6587\u6863'
const privatePreviewTitle = '\u79c1\u5bc6\u5065\u5eb7\u6570\u636e'
const previewAttachmentText = '\u67e5\u770b\u9644\u4ef6'
const previewRecordedAtLabel = '\u8bb0\u5f55\u65f6\u95f4'
const previewRecordTypeLabel = '\u8bb0\u5f55\u7c7b\u578b'
const previewHeightLabel = '\u8eab\u9ad8(cm)'
const previewWeightLabel = '\u4f53\u91cd(kg)'
const previewBloodPressureLabel = '\u8840\u538b'
const previewBloodLipidLabel = '\u8840\u8102'
const previewHeartRateLabel = '\u5fc3\u7387'
const previewBloodSugarLabel = '\u8840\u7cd6'
const previewPrivacyLabel = '\u9690\u79c1\u72b6\u6001'
const previewOnchainLabel = '\u94fe\u4e0a\u4fe1\u606f'
const previewOtherTextLabel = '\u8865\u5145\u8bf4\u660e'
const previewRawContentLabel = '\u539f\u59cb\u6570\u636e'
const privateViewFailedText = '\u67e5\u770b\u79c1\u5bc6\u6570\u636e\u5931\u8d25'
const editText = '\u7f16\u8f91'
const replacePdfText = '\u7f16\u8f91'
const deleteText = '\u5220\u9664'
const grantText = '授权'
const viewPdfText = '\u67e5\u770bPDF'
const downloadWordText = '\u4e0b\u8f7dWord'
const onchainColumnText = '\u94fe\u4e0a\u9a8c\u771f'
const onchainVerifiedText = '\u5df2\u9a8c\u771f'
const onchainMismatchText = '\u5f02\u5e38'
const onchainPendingText = '\u5f85\u9a8c\u771f'
const onchainUnavailableText = '\u672a\u5b58\u8bc1'
const onchainUnlockRequiredText = '\u5f85\u89e3\u9501/\u7591\u4f3c\u635f\u574f'
const onchainServiceUnavailableText = '\u670d\u52a1\u672a\u542f\u7528'
const onchainRecordMissingText = '\u94fe\u4e0a\u8bb0\u5f55\u7f3a\u5931'
const onchainFailedText = '\u9a8c\u771f\u5931\u8d25'
const loadFailedText = '\u52a0\u8f7d\u5065\u5eb7\u6570\u636e\u5931\u8d25'
const analysisSuccessText = '\u5065\u5eb7\u5206\u6790\u5b8c\u6210'
const analysisFailedText = '\u5065\u5eb7\u5206\u6790\u5931\u8d25'
const grantDialogTitle = '数据授权管理'
const grantDialogTip = '可将私密数据授权给管理员账号查看。'
const doctorFieldLabel = '授权对象'
const doctorFieldPlaceholder = '请选择管理员'
const expiryFieldLabel = '有效期'
const expiryFieldSuffix = '天'
const remarkFieldLabel = '备注'
const remarkFieldPlaceholder = '可选：填写授权用途、就诊时间等说明'
const addGrantText = '添加授权'
const grantedListTitle = '当前记录已授权对象'
const emptyGrantListText = '暂无授权记录'
const revokeText = '撤销'

const fileAccept = computed(() => (
  '.pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document'
))

const fileUploadLabel = computed(() => '健康数据文件')
const uploadButtonLabel = computed(() => '上传文件')
const fileUploadAlertText = computed(() => '支持 PDF / Word（.doc/.docx），上传时可自由选择公开或保密')
const defaultUploadedFileName = computed(() => (
  healthForm.value.record_type === 'word' ? '已上传Word' : '已上传PDF'
))

const healthRules = {
  data_title: [{ max: 80, message: '记录标题最多 80 个字符', trigger: 'blur' }],
  weight: [{ type: 'number', message: '请输入有效的体重', trigger: 'blur' }],
  height: [{ type: 'number', message: '请输入有效的身高', trigger: 'blur' }],
  blood_pressure: [{
    validator: (_rule, value, callback) => {
      if (!value) {
        callback()
        return
      }
      if (!/^\s*\d{2,3}\s*\/\s*\d{2,3}\s*$/.test(value)) {
        callback(new Error('血压格式应为 舒张压/收缩压，例如 80/120'))
        return
      }
      callback()
    },
    trigger: 'blur'
  }],
  blood_lipid: [{ type: 'number', message: '请输入有效的血脂', trigger: 'blur' }],
  heart_rate: [{ type: 'number', message: '请输入有效的心率', trigger: 'blur' }],
  blood_sugar: [{ type: 'number', message: '请输入有效的血糖', trigger: 'blur' }],
  other_text: [{ max: 1000, message: '其他说明最多1000字', trigger: 'blur' }]
}

const parseBloodPressure = (value) => {
  if (!value || typeof value !== 'string') {
    return { diastolic: null, systolic: null }
  }
  const normalized = value.replace(/\s+/g, '')
  const parts = normalized.split('/')
  if (parts.length !== 2) {
    return { diastolic: null, systolic: null }
  }

  const diastolic = Number(parts[0])
  const systolic = Number(parts[1])
  if (Number.isNaN(diastolic) || Number.isNaN(systolic)) {
    return { diastolic: null, systolic: null }
  }

  return { diastolic, systolic }
}

const parseDataContent = (content) => {
  if (!content) {
    return { metrics: {}, other_text: '' }
  }
  try {
    const parsed = JSON.parse(content)
    if (parsed && typeof parsed === 'object') {
      return {
        metrics: parsed.metrics || {},
        other_text: parsed.other_text || ''
      }
    }
  } catch {
    return { metrics: {}, other_text: content }
  }
  return { metrics: {}, other_text: '' }
}

const toViewRecord = (record) => {
  const parsed = parseDataContent(record.data_content)
  const metrics = parsed.metrics || {}
  const fileType = record.file_type === 'pdf' ? 'pdf' : (record.file_type === 'word' ? 'word' : 'manual')
  const bloodPressure = metrics.blood_pressure || (
    metrics.blood_pressure_diastolic != null && metrics.blood_pressure_systolic != null
      ? `${metrics.blood_pressure_diastolic}/${metrics.blood_pressure_systolic}`
      : ''
  )
  return {
    ...record,
    data_title: record.data_title || '',
    record_type: fileType,
    is_private: !record.is_public,
    requires_private_key: !!record.requires_private_key,
    raw_content: record.data_content || '',
    onchain_verification_status: record.onchain_verification_status || '',
    onchain_data_id: record.onchain_data_id || '',
    onchain_tx_hash: record.onchain_tx_hash || '',
    onchain_verified: typeof record.onchain_verified === 'boolean' ? record.onchain_verified : null,
    onchain_verification_message: record.onchain_verification_message || '',
    file_mime_type: record.file_mime_type || '',
    health_data_file: record.pdf_data_base64 || null,
    health_data_file_name: fileType === 'manual'
      ? null
      : (record.data_title || (fileType === 'word' ? '健康数据Word' : '健康数据PDF')),
    recorded_at: record.recorded_at || record.created_at,
    weight: metrics.weight ?? null,
    height: metrics.height ?? null,
    blood_pressure: bloodPressure,
    blood_lipid: metrics.blood_lipid ?? null,
    heart_rate: metrics.heart_rate ?? null,
    blood_sugar: metrics.blood_sugar ?? null,
    other_text: parsed.other_text || ''
  }
}

const displayMetric = (record, value) => {
  if (record.is_private) return hiddenText
  if (value === null || value === undefined || value === '') return '-'
  return value
}

const previewMetric = (value) => {
  if (value === null || value === undefined || value === '') return '-'
  return value
}

const isAttachmentRecord = (record) => ['pdf', 'word'].includes(record?.record_type)

const showRawPrivateContent = (record) => {
  if (!record?.raw_content) return false
  const hasStructuredMetrics = [
    record.height,
    record.weight,
    record.blood_pressure,
    record.blood_lipid,
    record.heart_rate,
    record.blood_sugar
  ].some((item) => item !== null && item !== undefined && item !== '')
  return !hasStructuredMetrics && !record.other_text
}

const recordTypeLabel = (recordType) => {
  if (recordType === 'pdf') return 'PDF'
  if (recordType === 'word') return 'Word'
  return '手动'
}

const recordTypeTagType = (recordType) => {
  if (recordType === 'pdf') return 'info'
  if (recordType === 'word') return 'warning'
  return 'primary'
}

const resolveOnchainLabel = (record) => {
  switch (record.onchain_verification_status) {
    case 'verified':
      return onchainVerifiedText
    case 'mismatch':
      return onchainMismatchText
    case 'no_proof':
      return onchainUnavailableText
    case 'locked':
      return onchainUnlockRequiredText
    case 'service_unavailable':
      return onchainServiceUnavailableText
    case 'record_missing':
      return onchainRecordMissingText
    case 'source_empty':
    case 'hash_failed':
    case 'query_failed':
      return onchainFailedText
    default:
      if (!record.onchain_data_id) return onchainUnavailableText
      if (record.onchain_verified === true) return onchainVerifiedText
      if (record.onchain_verified === false) return onchainMismatchText
      return onchainPendingText
  }
}

const resolveOnchainTagType = (record) => {
  switch (record.onchain_verification_status) {
    case 'verified':
      return 'success'
    case 'mismatch':
    case 'record_missing':
    case 'source_empty':
    case 'hash_failed':
    case 'query_failed':
      return 'danger'
    case 'locked':
    case 'service_unavailable':
      return 'warning'
    case 'no_proof':
      return 'info'
    default:
      if (!record.onchain_data_id) return 'info'
      if (record.onchain_verified === true) return 'success'
      if (record.onchain_verified === false) return 'danger'
      return 'warning'
  }
}

const resolveOnchainTitle = (record) => {
  return record.onchain_verification_message || onchainUnavailableText
}

const hasOnchainProof = (record) => Boolean(record.onchain_data_id || record.onchain_tx_hash)

const statsCards = computed(() => {
  const averageHeartRate = healthSummary.value.average_heart_rate
  return [
    {
      title: '记录总数',
      value: totalRecords.value,
      unit: '条',
      icon: 'TrendCharts',
      color: '#2f6fd6',
      desc: `手动 ${manualRecords.value} / PDF ${pdfRecords.value} / Word ${wordRecords.value}`
    },
    {
      title: '本月记录',
      value: healthSummary.value.records_this_month || 0,
      unit: '条',
      icon: 'Calendar',
      color: '#2ea56b',
      desc: latestRecordLabel.value
    },
    {
      title: '平均心率',
      value: averageHeartRate ? Math.round(averageHeartRate) : '-',
      unit: averageHeartRate ? 'bpm' : '',
      icon: 'Bell',
      color: '#cc8a1b',
      desc: `保密 ${privateRecords.value} / 公开 ${publicRecords.value}`
    },
    {
      title: '最近记录',
      value: latestRecordDate.value,
      unit: '',
      icon: 'DataAnalysis',
      color: '#5d6d7e',
      desc: '按时间倒序展示全部记录'
    }
  ]
})

const totalRecords = computed(() => healthRecords.value.length)
const pdfRecords = computed(() => healthRecords.value.filter((item) => item.record_type === 'pdf').length)
const wordRecords = computed(() => healthRecords.value.filter((item) => item.record_type === 'word').length)
const manualRecords = computed(() => healthRecords.value.filter((item) => item.record_type === 'manual').length)
const privateRecords = computed(() => healthRecords.value.filter((item) => item.is_private).length)
const publicRecords = computed(() => healthRecords.value.filter((item) => !item.is_private).length)
const latestRecordDate = computed(() => {
  if (!healthRecords.value.length) return '-'
  return formatDate(healthRecords.value[0].recorded_at)
})
const currentRecordGrants = computed(() => {
  return [...recordGrants.value].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
})
const latestRecordLabel = computed(() => (healthRecords.value.length ? '已同步最近记录' : '暂无记录'))

const defaultIsPrivate = computed(() => !systemSettings.value.default_health_data_public)

const openManualDialog = () => {
  formMode.value = 'manual'
  isEditing.value = false
  healthForm.value = {
    data_title: '',
    weight: null,
    height: null,
    blood_pressure: '',
    blood_lipid: null,
    heart_rate: null,
    blood_sugar: null,
    other_text: '',
    record_type: 'manual',
    is_private: defaultIsPrivate.value,
    health_data_file_name: null,
    health_data_file: null,
    recorded_at: new Date()
  }
  dialogVisible.value = true
}

const openFileDialog = () => {
  formMode.value = 'file'
  isEditing.value = false
  healthForm.value = {
    data_title: '',
    weight: null,
    height: null,
    blood_pressure: '',
    blood_lipid: null,
    heart_rate: null,
    blood_sugar: null,
    other_text: '',
    record_type: 'pdf',
    is_private: defaultIsPrivate.value,
    health_data_file_name: null,
    health_data_file: null,
    recorded_at: new Date()
  }
  dialogVisible.value = true
}

const fetchUnlockedRecord = async (record) => {
  try {
    const recordData = await healthApi.getRecord(record.id)
    const viewRecord = toViewRecord(recordData)
    if (viewRecord.requires_private_key) {
      ElMessage.error(unlockUnavailableText)
      return null
    }
    return viewRecord
  } catch (error) {
    ElMessage.error(extractErrorDetail(error, privateViewFailedText))
    return null
  }
}

const viewPrivateRecord = async (record) => {
  const unlockedRecord = await fetchUnlockedRecord(record)
  if (!unlockedRecord) return

  if (isAttachmentRecord(unlockedRecord)) {
    openUnlockedAttachment(unlockedRecord)
    ElMessage.success(unlockSuccessText)
    return
  }

  privatePreviewRecord.value = unlockedRecord
  privatePreviewDialogVisible.value = true
  ElMessage.success(unlockSuccessText)
}

const editRecord = async (record) => {
  if (record.requires_private_key) {
    const unlockedRecord = await fetchUnlockedRecord(record)
    if (!unlockedRecord) {
      return
    }
    record = unlockedRecord
  }

  const parsed = parseDataContent(record.data_content)
  const metrics = parsed.metrics || {}
  const bloodPressure = metrics.blood_pressure || (
    metrics.blood_pressure_diastolic != null && metrics.blood_pressure_systolic != null
      ? `${metrics.blood_pressure_diastolic}/${metrics.blood_pressure_systolic}`
      : ''
  )
  formMode.value = record.record_type === 'manual' ? 'manual' : 'file'
  isEditing.value = true
  healthForm.value = {
    ...record,
    data_title: record.data_title || '',
    weight: metrics.weight ?? null,
    height: metrics.height ?? null,
    blood_pressure: bloodPressure,
    blood_lipid: metrics.blood_lipid ?? null,
    heart_rate: metrics.heart_rate ?? null,
    blood_sugar: metrics.blood_sugar ?? null,
    other_text: parsed.other_text || '',
    record_type: record.record_type || 'manual',
    is_private: Boolean(record.is_private),
    health_data_file_name: record.health_data_file_name || null,
    health_data_file: record.health_data_file || null,
    recorded_at: new Date(record.recorded_at)
  }
  dialogVisible.value = true
}

const handleFileChange = (uploadFile) => {
  const file = uploadFile?.raw || uploadFile
  if (!file) return

  const lowerName = file.name?.toLowerCase() || ''
  const inferredType = (
    file.type === 'application/msword'
      || file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      || lowerName.endsWith('.doc')
      || lowerName.endsWith('.docx')
  )
    ? 'word'
    : 'pdf'
  const isValidFile = inferredType === 'word'
    ? file.type === 'application/msword'
      || file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      || lowerName.endsWith('.doc')
      || lowerName.endsWith('.docx')
    : file.type === 'application/pdf' || lowerName.endsWith('.pdf')
  if (!isValidFile) {
    ElMessage.error('仅支持 PDF / Word 文件（.doc/.docx）')
    return
  }

  const maxSize = inferredType === 'word' ? 10 * 1024 * 1024 : 6 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error(inferredType === 'word' ? 'Word 不能超过 10MB' : 'PDF 不能超过 6MB')
    return
  }

  const reader = new FileReader()
  reader.onload = () => {
    healthForm.value.record_type = inferredType
    healthForm.value.health_data_file = reader.result
    healthForm.value.health_data_file_name = file.name
  }
  reader.readAsDataURL(file)
}

const removeFile = () => {
  healthForm.value.health_data_file_name = null
  healthForm.value.health_data_file = null
}

const extractErrorDetail = (error, fallback) => {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail[0]?.msg || fallback
  return fallback
}

const saveHealthData = async () => {
  if (!healthFormRef.value) return
  
  try {
    const valid = await healthFormRef.value.validate()
    if (!valid) return

    saving.value = true
    
    const metrics = {
      weight: healthForm.value.weight,
      height: healthForm.value.height,
      blood_pressure: healthForm.value.blood_pressure,
      blood_lipid: healthForm.value.blood_lipid,
      heart_rate: healthForm.value.heart_rate,
      blood_sugar: healthForm.value.blood_sugar
    }

    const parsedPressure = parseBloodPressure(healthForm.value.blood_pressure)
    metrics.blood_pressure_diastolic = parsedPressure.diastolic
    metrics.blood_pressure_systolic = parsedPressure.systolic

    const payload = {
      data_title: (healthForm.value.data_title || '').trim() || (
        formMode.value === 'manual'
          ? '手动健康记录'
          : (healthForm.value.health_data_file_name || (healthForm.value.record_type === 'word' ? '健康数据Word' : '健康数据PDF'))
      ),
      file_type: formMode.value === 'manual' ? 'text' : healthForm.value.record_type,
      is_public: !healthForm.value.is_private,
      recorded_at: healthForm.value.recorded_at ? new Date(healthForm.value.recorded_at).toISOString() : null,
      data_content: formMode.value === 'manual'
        ? JSON.stringify({ metrics, other_text: healthForm.value.other_text || '' })
        : null,
      pdf_data_base64: formMode.value === 'manual' ? null : healthForm.value.health_data_file
    }

    if (formMode.value !== 'manual') {
      if (!payload.pdf_data_base64) {
        ElMessage.error('请先上传文件')
        return
      }
    }

    if (isEditing.value) {
      await healthApi.updateRecord(healthForm.value.id, payload)
      ElMessage.success('健康数据更新成功')
    } else {
      await healthApi.createRecord(payload)
      ElMessage.success('健康数据添加成功')
    }
    
    dialogVisible.value = false
    await loadHealthData()
  } catch (error) {
    ElMessage.error(extractErrorDetail(error, '操作失败，请重试'))
  } finally {
    saving.value = false
  }
}

const deleteRecord = async (record) => {
  try {
    await healthApi.deleteRecord(record.id)
    ElMessage.success('健康数据删除成功')
    await loadHealthData()
  } catch (error) {
    ElMessage.error('删除失败，请重试')
  }
}

const resetGrantForm = () => {
  grantForm.value = {
    doctor_id: '',
    expires_days: 30,
    remark: ''
  }
}

const openGrantDialog = (record) => {
  if (!record?.is_private) {
    ElMessage.warning('公开记录无需授权')
    return
  }
  grantTargetRecord.value = record
  resetGrantForm()
  grantDialogVisible.value = true
  loadGrantableUsers()
  loadRecordGrants(record.id)
}

const addGrant = async () => {
  if (!grantTargetRecord.value) return
  if (!grantForm.value.doctor_id) {
    ElMessage.warning('请选择授权对象')
    return
  }

  const selectedAdmin = grantableUsers.value.find((item) => item.id === grantForm.value.doctor_id)
  if (!selectedAdmin) {
    ElMessage.error('授权对象不存在')
    return
  }
  try {
    await healthApi.createRecordGrant(grantTargetRecord.value.id, {
      grantee_user_id: selectedAdmin.id,
      expires_days: Number(grantForm.value.expires_days) || 30,
      remark: (grantForm.value.remark || '').trim()
    })
    ElMessage.success('授权成功')
    resetGrantForm()
    await loadRecordGrants(grantTargetRecord.value.id)
  } catch (error) {
    ElMessage.error(extractErrorDetail(error, '授权失败，请稍后重试'))
  }
}

const revokeGrant = async (grantId) => {
  if (!grantTargetRecord.value) return
  try {
    await healthApi.revokeRecordGrant(grantId)
    ElMessage.success('授权记录已撤销')
    await loadRecordGrants(grantTargetRecord.value.id)
  } catch (error) {
    ElMessage.error(extractErrorDetail(error, '撤销授权失败，请稍后重试'))
  }
}

const resolveGrantStatus = (grant) => {
  if (grant?.revoked_at) return { label: '已撤销', type: 'info' }
  if (grant?.expires_at && new Date(grant.expires_at).getTime() <= Date.now()) {
    return { label: '已过期', type: 'warning' }
  }
  return { label: '生效中', type: 'success' }
}

const resolveExpiresDays = (grant) => {
  if (!grant?.created_at || !grant?.expires_at) return '-'
  const ms = new Date(grant.expires_at).getTime() - new Date(grant.created_at).getTime()
  const days = Math.round(ms / (24 * 60 * 60 * 1000))
  return days > 0 ? days : 0
}

const loadGrantableUsers = async () => {
  try {
    const users = await healthApi.getGrantableUsers()
    grantableUsers.value = (users || []).filter((item) => item.role === 'admin')
  } catch (error) {
    grantableUsers.value = []
    ElMessage.error(extractErrorDetail(error, '加载授权对象失败'))
  }
}

const loadRecordGrants = async (recordId) => {
  try {
    recordGrants.value = await healthApi.getRecordGrants(recordId)
  } catch (error) {
    recordGrants.value = []
    ElMessage.error(extractErrorDetail(error, '加载授权记录失败'))
  }
}

const loadHealthData = async () => {
  try {
    const [records, summary] = await Promise.all([
      healthApi.getRecords(),
      healthApi.getSummary()
    ])
    healthRecords.value = records.map(toViewRecord)
    healthSummary.value = summary
  } catch (error) {
    ElMessage.error(extractErrorDetail(error, loadFailedText))
  }
}

const loadPublicSettings = async () => {
  try {
    const data = await getPublicSystemSettings()
    systemSettings.value = { ...systemSettings.value, ...data }
  } catch {
    // keep defaults when settings endpoint is unavailable
  }
}


const analyzeHealthData = async () => {
  try {
    const analysis = await healthApi.analyzeData({})
    healthAnalysis.value = analysis
    ElMessage.success(analysisSuccessText)
  } catch (error) {
    ElMessage.error(extractErrorDetail(error, analysisFailedText))
  }
}


const refreshData = () => {
  loadHealthData()
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const dataUrlToBlobUrl = (dataUrl) => {
  if (!dataUrl || typeof dataUrl !== 'string') return null
  const match = dataUrl.match(/^data:([^;]+);base64,(.+)$/)
  if (!match) return null
  const mimeType = match[1] || 'application/octet-stream'
  const base64 = match[2]
  const binary = window.atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i)
  }
  const blob = new Blob([bytes], { type: mimeType })
  return {
    blobUrl: URL.createObjectURL(blob),
    mimeType
  }
}

const openUnlockedAttachment = (record, popupWindow = null) => {
  if (!record?.health_data_file) return
  const blobInfo = dataUrlToBlobUrl(record.health_data_file)
  const attachmentUrl = blobInfo?.blobUrl || record.health_data_file

  if (record.record_type === 'word') {
    const link = document.createElement('a')
    link.href = attachmentUrl
    link.download = record.health_data_file_name || '健康数据.docx'
    link.target = '_blank'
    link.rel = 'noopener noreferrer'
    link.click()
    if (blobInfo?.blobUrl) {
      setTimeout(() => URL.revokeObjectURL(blobInfo.blobUrl), 60_000)
    }
    if (popupWindow && !popupWindow.closed) {
      popupWindow.close()
    }
    return
  }

  if (popupWindow && !popupWindow.closed) {
    popupWindow.location.replace(attachmentUrl)
    if (blobInfo?.blobUrl) {
      setTimeout(() => URL.revokeObjectURL(blobInfo.blobUrl), 60_000)
    }
    return
  }

  const link = document.createElement('a')
  link.href = attachmentUrl
  link.target = '_blank'
  link.rel = 'noopener noreferrer'
  link.click()
  if (blobInfo?.blobUrl) {
    setTimeout(() => URL.revokeObjectURL(blobInfo.blobUrl), 60_000)
  }
}

const openAttachment = async (record) => {
  let previewWindow = null
  if (record.requires_private_key) {
    // Open the tab on direct click first, then fill it after async unlock to avoid popup blocking.
    previewWindow = window.open('', '_blank')
    if (!previewWindow) {
      ElMessage.error('浏览器拦截了新窗口，请允许弹窗后重试')
      return
    }
    ElMessage.warning(lockedRecordText)
    const unlockedRecord = await fetchUnlockedRecord(record)
    if (!unlockedRecord) {
      if (previewWindow && !previewWindow.closed) {
        previewWindow.close()
      }
      return
    }
    record = unlockedRecord
  }

  openUnlockedAttachment(record, previewWindow)
}

onMounted(async () => {
  await loadPublicSettings()
  loadHealthData()
})

onActivated(() => {
  loadHealthData()
})
</script>

<style scoped>
.health-data-container {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding: 24px;
  background: linear-gradient(135deg, #409EFF 0%, #36A3F5 100%);
  border-radius: 16px;
  color: white;
  box-shadow: 0 8px 24px rgba(64, 158, 255, 0.2);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 64px;
  height: 64px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.header-text h1 {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 4px;
}

.header-text p {
  font-size: 16px;
  opacity: 0.9;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.add-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 12px 24px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.add-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.upload-btn {
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

.upload-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
}

.content-section {
  margin-bottom: 32px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.stats-card {
  border-radius: 16px;
  border: none;
  min-height: auto;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.chart-card, .recent-card {
  border-radius: 16px;
  border: 1px solid #e5eefb;
  min-height: 400px;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.recent-card {
  height: auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;
}

.card-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.chart-placeholder {
  min-height: 300px;
  display: block;
  background: linear-gradient(180deg, #f8fbff 0%, #f4f8ff 100%);
  border-radius: 12px;
  border: 1px dashed #d6e4f8;
  padding: 12px;
}

.upload-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.upload-preview {
  margin-top: 12px;
}

.private-preview-text {
  margin-top: 16px;
  padding: 14px 16px;
  border-radius: 12px;
  background: #f8fbff;
  border: 1px solid #dbeafe;
}

.private-preview-text__label {
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.private-preview-text__content {
  line-height: 1.7;
  color: #475569;
  white-space: pre-wrap;
  word-break: break-word;
}

.private-preview-actions {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.grant-record-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.grant-form__suffix {
  margin-left: 10px;
  color: #64748b;
  font-size: 13px;
}

.doctor-option {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.doctor-option__name {
  font-size: 13px;
  color: #1e293b;
}

.doctor-option__meta {
  font-size: 12px;
  color: #64748b;
}

.grant-actions {
  margin: 4px 0 14px;
  display: flex;
  justify-content: flex-end;
}

.grant-list {
  margin-top: 6px;
}

.grant-list__header {
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.onchain-tag {
  cursor: default;
}

.onchain-popover {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.onchain-popover__title {
  font-weight: 700;
  color: #1e293b;
}

.onchain-popover__row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.onchain-popover__label {
  font-size: 12px;
  color: #64748b;
}

.onchain-popover__value {
  font-size: 13px;
  color: #1e293b;
  line-height: 1.5;
}

.onchain-popover__hash {
  font-size: 12px;
  color: #334155;
  word-break: break-all;
  line-height: 1.5;
}

.placeholder-content {
  text-align: center;
  color: #94a3b8;
}

.placeholder-content p {
  margin-top: 12px;
  font-size: 14px;
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.recent-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, #f8fbff 0%, #f5f9ff 100%);
  border-radius: 12px;
  border: 1px solid #e4ecfb;
  transition: all 0.25s ease;
}

.recent-item:hover {
  background: #eef5ff;
  transform: translateY(-2px);
}

.recent-icon {
  width: 42px;
  height: 42px;
  background: white;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
  flex-shrink: 0;
}

.recent-content {
  flex: 1;
}

.recent-content h4 {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 2px;
}

.recent-content p {
  font-size: 12px;
  color: #64748b;
  margin: 0;
}

.recent-time {
  font-size: 12px;
  color: #94a3b8;
  flex-shrink: 0;
}

.stat-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, #f8fbff 0%, #f5f9ff 100%);
  border-radius: 12px;
  border: 1px solid #e4ecfb;
  transition: all 0.25s ease;
}

.stat-item:hover {
  background: #eef5ff;
  transform: translateY(-2px);
}

.stat-icon {
  width: 42px;
  height: 42px;
  background: white;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  margin: 2px 0;
}

.stat-unit {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 400;
}

.stat-desc {
  margin: 0;
  font-size: 12px;
  color: #64748b;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .header-actions {
    width: 100%;
    justify-content: center;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .chart-card, .recent-card {
    margin-bottom: 16px;
  }
}

@media (max-width: 576px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
