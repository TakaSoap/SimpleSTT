<template>
  <div class="layout" :class="{ 'basic-mode': isBasicMode }">
    <div v-if="!isBasicMode" class="sidebar">
      <n-card :title="t('provider.title')" size="large" class="card">
        <n-space vertical size="large">
          <n-radio-group v-model:value="provider" name="provider">
            <n-space>
              <n-radio-button value="openai">OpenAI</n-radio-button>
              <n-radio-button value="azure">Azure OpenAI</n-radio-button>
            </n-space>
          </n-radio-group>
          <n-form ref="providerFormRef" :model="providerForm" :rules="providerRules" label-placement="top">
            <n-form-item :label="t('provider.apiKey')" path="apiKey">
              <n-input v-model:value="providerForm.apiKey" type="password" show-password-on="mousedown" />
            </n-form-item>
            <n-alert v-if="isUsingDefaultKey" type="info" class="default-key" :show-icon="false">
              {{ t('provider.defaultKeyNotice') }}
            </n-alert>
            <template v-if="provider === 'azure'">
              <n-form-item :label="t('provider.endpoint')" path="azureEndpoint">
                <n-input
                  v-model:value="providerForm.azureEndpoint"
                  :placeholder="providerDefaults?.azure_endpoint ?? 'https://example.openai.azure.com/'"
                />
              </n-form-item>
              <n-alert v-if="isUsingDefaultAzureEndpoint" type="info" class="default-key" :show-icon="false">
                {{ t('provider.defaultEndpointNotice') }}
              </n-alert>
              <n-form-item :label="t('provider.deployment')" path="azureDeploymentId">
                <n-input v-model:value="providerForm.azureDeploymentId"
                  :placeholder="providerDefaults?.azure_deployment_id ?? ''" />
              </n-form-item>
              <n-form-item :label="t('provider.apiVersion')" path="azureApiVersion">
                <n-input v-model:value="providerForm.azureApiVersion"
                  :placeholder="providerDefaults?.azure_api_version ?? '2025-04-01-preview'" />
              </n-form-item>
            </template>
            <div class="key-actions">
              <n-button type="primary" :loading="isValidatingKey" @click="handleValidateKey">
                <n-space align="center" size="small">
                  <n-icon size="16" :component="ShieldCheckmarkOutline" />
                  <span>{{ t('provider.validate') }}</span>
                </n-space>
              </n-button>
              <n-tag v-if="keyStatusText" :type="keyStatusTagType" round>
                {{ keyStatusText }}
              </n-tag>
            </div>
          </n-form>
        </n-space>
      </n-card>

      <n-card :title="t('provider.modelTitle')" size="large" class="card">
        <n-form label-placement="top">
          <n-form-item :label="t('provider.model')">
            <n-select v-model:value="selectedModel" :options="modelSelectOptions" :disabled="provider === 'azure'" />
          </n-form-item>
          <n-form-item :label="t('provider.format')">
            <n-select
              v-model:value="selectedFormat"
              :options="formatSelectOptions"
              :disabled="provider === 'azure'"
            />
            <n-alert v-if="provider === 'azure'" type="info" class="format-notice" :show-icon="false">
              {{ t('provider.azureFormatNotice') }}
            </n-alert>
          </n-form-item>
          <n-form-item :label="t('provider.language')">
            <n-select v-model:value="selectedLanguage" :options="languageSelectOptions" />
          </n-form-item>
          <n-form-item :label="t('provider.stream')" style="margin-bottom: 0">
            <n-switch v-model:value="streamEnabled" :disabled="!canStream" />
            <span class="hint">
              {{ canStream ? t('provider.streamHint.available') : t('provider.streamHint.unavailable') }}
            </span>
          </n-form-item>
        </n-form>
      </n-card>

      <n-card :title="t('prompts.title')" size="large" class="card">
        <n-space wrap>
          <n-button v-for="template in promptTemplates" :key="template.key" size="small"
            @click="applyTemplate(template.text)">
            <template #icon>
              <n-icon :component="template.icon" />
            </template>
            <span>{{ template.label }}</span>
          </n-button>
        </n-space>
        <n-input
          v-model:value="prompt"
          type="textarea"
          :placeholder="t('prompts.textareaPlaceholder')"
          :autosize="{ minRows: 3, maxRows: 6 }"
          style="margin-top: 12px"
        />
      </n-card>
    </div>

    <div class="content">
      <div class="workflow-strip">
        <n-steps :current="workflowStep" :status="workflowStepStatus" size="small">
          <n-step :title="t('workflow.upload')" />
          <n-step :title="t('workflow.transcribe')" />
          <n-step :title="t('workflow.download')" />
        </n-steps>
        <n-alert v-if="isBasicMode" type="info" class="mode-summary" :show-icon="false">
          <n-space align="center" size="small" wrap>
            <n-tag type="info" round>{{ t('workflow.azureDefault') }}</n-tag>
            <span>{{ t('workflow.plainText') }}</span>
          </n-space>
        </n-alert>
      </div>

      <n-card :title="t('upload.title')" size="large" class="card">
        <n-upload v-model:file-list="uploadList" :max="1" :default-upload="false" accept="audio/*,video/*"
          @change="handleUploadChange" @update:file-list="handleFileListUpdate" @remove="handleRemove">
          <n-upload-dragger v-if="showUploader">
            <div class="upload-inner">
              <n-icon :component="CloudUploadOutline" size="48" />
              <p>{{ t('upload.instructions') }}</p>
              <p class="sub">{{ t('upload.supported') }}</p>
            </div>
          </n-upload-dragger>
        </n-upload>
        <n-alert v-if="fileMeta" type="success" class="info" :show-icon="false">
          <div class="file-line">
            <strong>{{ fileMeta.name }}</strong>
          </div>
          <div>{{ t('upload.size') }}：{{ formatSize(fileMeta.size_bytes) }}</div>
          <div>
            {{ t('upload.duration') }}：
            <span v-if="fileMeta.duration_text">{{ fileMeta.duration_text }}</span>
            <span v-else>{{ t('upload.noDuration') }}</span>
          </div>
          <div v-if="fileMeta.cost">
            {{ t('upload.costEstimate', {
              usd: formatNumber(fileMeta.cost.usd, 4),
              hkd: formatNumber(fileMeta.cost.hkd, 3),
              cny: formatNumber(fileMeta.cost.cny, 3)
            }) }}
          </div>
        </n-alert>
      </n-card>

      <n-card :title="t('transcription.title')" size="large" class="card">
        <n-space vertical size="large">
          <n-alert :type="statusType" :show-icon="false">{{ statusMessage }}</n-alert>
          <n-input
            type="textarea"
            :value="resultText"
            readonly
            :rows="18"
            :placeholder="t('transcription.placeholder')"
            :input-style="{ maxHeight: '480px', overflowY: 'auto', whiteSpace: 'pre-wrap' }"
          />
          <div class="actions">
            <n-button type="primary" size="large" :loading="transcribing" :disabled="!canTranscribe"
              @click="handleTranscribe">
              <template #icon>
                <n-icon :component="SparklesOutline" />
              </template>
              <span>{{ t('transcription.start') }}</span>
            </n-button>
            <n-button size="large" tertiary :disabled="!resultDownloadUrl" @click="handleDownload">
              <template #icon>
                <n-icon :component="DownloadOutline" />
              </template>
              <span>{{ t('transcription.download') }}</span>
            </n-button>
          </div>
        </n-space>
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import type { FormInst, FormRules, SelectOption, UploadFileInfo } from 'naive-ui'
import { useMessage } from 'naive-ui'
import {
  CloudUploadOutline,
  ShieldCheckmarkOutline,
  SparklesOutline,
  DownloadOutline,
  ListOutline,
  GitNetworkOutline,
  ChatbubbleEllipsesOutline,
  CloseCircleOutline
} from '@vicons/ionicons5'
import { useI18n } from 'vue-i18n'
import {
  analyzeFile,
  deleteFile,
  fetchOptions,
  streamTranscription,
  transcribe,
  validateKey
} from '../api/endpoints'
import { apiStream } from '../api/client'
import { useAppMode } from '../composables/useAppMode'
import type {
  AnalyzeFileResponse,
  FileMetadata,
  FormatOption,
  OptionsResponse,
  ProviderConfig,
  ProviderDefaults,
  TranscriptionRequest
} from '../types/api'

const message = useMessage()
const { t, te, locale } = useI18n({ useScope: 'global' })
const appMode = useAppMode()
const isBasicMode = computed(() => appMode.isBasic.value)

const providerFormRef = ref<FormInst | null>(null)
const provider = ref<'openai' | 'azure'>('openai')
const providerForm = reactive({
  apiKey: '',
  azureEndpoint: '',
  azureDeploymentId: '',
  azureApiVersion: ''
})
const keyStatus = ref<'idle' | 'loading' | 'valid' | 'invalid'>('idle')
const keyStatusText = ref('')

const options = ref<OptionsResponse | null>(null)
const providerDefaults = ref<ProviderDefaults | null>(null)
const hasDefaultKeys = ref<Record<'openai' | 'azure', boolean>>({ openai: false, azure: false })

const selectedModel = ref('gpt-4o-transcribe')
const selectedFormat = ref('text')
const selectedLanguage = ref('')
const streamEnabled = ref(true)

const uploadList = ref<UploadFileInfo[]>([])
const fileMeta = ref<FileMetadata | null>(null)
const currentFile = ref<File | null>(null)
const prompt = ref('')

interface AdvancedSnapshot {
  provider: 'openai' | 'azure'
  selectedModel: string
  selectedFormat: string
  selectedLanguage: string
  streamEnabled: boolean
  prompt: string
  providerForm: {
    apiKey: string
    azureEndpoint: string
    azureDeploymentId: string
    azureApiVersion: string
  }
}

const advancedSnapshot = ref<AdvancedSnapshot | null>(null)

const transcribing = ref(false)
const resultText = ref('')
const resultDownloadUrl = ref('')

const statusKey = ref<'waiting' | 'analyzing' | 'ready' | 'transcribing' | 'success' | 'error'>('waiting')
const statusType = ref<'default' | 'info' | 'success' | 'error'>('default')
const statusDetails = ref<string | null>(null)
const reanalyzing = ref(false)

const showUploader = computed(() => uploadList.value.length === 0)

const workflowStep = computed(() => {
  if (resultDownloadUrl.value) return 3
  if (fileMeta.value || transcribing.value) return 2
  return 1
})

const workflowStepStatus = computed(() => (statusType.value === 'error' ? 'error' : 'process'))

const isValidatingKey = computed(() => keyStatus.value === 'loading')
const keyStatusTagType = computed(() => {
  if (keyStatus.value === 'valid') return 'success'
  if (keyStatus.value === 'invalid') return 'error'
  if (keyStatus.value === 'loading') return 'warning'
  return 'default'
})

const statusMessage = computed(() => statusDetails.value ?? t(`status.${statusKey.value}`))

const canStream = computed(() => {
  if (provider.value !== 'openai') return false
  if (selectedFormat.value !== 'text') return false
  return (options.value?.streamable_models ?? []).includes(selectedModel.value)
})

const isStreaming = computed(() => streamEnabled.value && canStream.value)

const defaultKeyAvailable = computed(() => hasDefaultKeys.value[provider.value])
const isUsingDefaultKey = computed(() => !providerForm.apiKey && defaultKeyAvailable.value)
const defaultAzureEndpointAvailable = computed(() => Boolean(providerDefaults.value?.azure_endpoint))
const isUsingDefaultAzureEndpoint = computed(
  () => provider.value === 'azure' && !providerForm.azureEndpoint && defaultAzureEndpointAvailable.value
)

const canTranscribe = computed(() => Boolean(fileMeta.value && (providerForm.apiKey || defaultKeyAvailable.value)))

const languageDisplayNames = computed(() => {
  if (typeof Intl === 'undefined' || typeof Intl.DisplayNames === 'undefined') {
    return null
  }
  try {
    return new Intl.DisplayNames([locale.value], { type: 'language' })
  } catch (error) {
    return null
  }
})

const languageSelectOptions = computed<SelectOption[]>(() =>
  (options.value?.languages ?? []).map((lang) => {
    if (!lang.code) {
      return {
        label: t('provider.autoDetect'),
        value: ''
      }
    }
    const localizedLabel = languageDisplayNames.value?.of(lang.code)
    return {
      label: localizedLabel ?? lang.label,
      value: lang.code
    }
  })
)

const modelSelectOptions = computed<SelectOption[]>(() =>
  (options.value?.models ?? []).map((model) => {
    const labelKey = `models.${model.name}.label`
    const descriptionKey = `models.${model.name}.description`
    const label = te(labelKey) ? t(labelKey) : `${model.name} · ${model.price_hint}`
    const description = te(descriptionKey) ? t(descriptionKey) : model.description
    return {
      label,
      value: model.name,
      description
    }
  })
)

function mapFormat(format: FormatOption) {
  const labelKey = `formats.${format.value}.label`
  const descriptionKey = `formats.${format.value}.description`
  return {
    label: te(labelKey) ? t(labelKey) : format.label,
    value: format.value,
    description: te(descriptionKey) ? t(descriptionKey) : format.description
  }
}

const formatSelectOptions = computed<SelectOption[]>(() => {
  const base = (options.value?.formats.base ?? []).map(mapFormat)
  let available = base
  if (selectedModel.value === 'whisper-1') {
    const whisper = (options.value?.formats.whisper ?? []).map(mapFormat)
    available = available.concat(whisper)
  }
  if (provider.value === 'azure') {
    return available.filter((option) => option.value === 'text')
  }
  return available
})

const promptTemplates = computed(() => [
  { key: 'punctuation', label: t('prompts.punctuation'), text: t('prompts.templates.punctuation'), icon: ListOutline },
  { key: 'terminology', label: t('prompts.terminology'), text: t('prompts.templates.terminology'), icon: GitNetworkOutline },
  { key: 'filler', label: t('prompts.filler'), text: t('prompts.templates.filler'), icon: ChatbubbleEllipsesOutline },
  { key: 'clear', label: t('prompts.clear'), text: '', icon: CloseCircleOutline }
])

const providerRules: FormRules = {
  apiKey: [
    {
      validator: (_, value: string) => {
        if (value && value.trim().length >= 10) {
          return Promise.resolve()
        }
        if (!value && defaultKeyAvailable.value) {
          return Promise.resolve()
        }
        return Promise.reject(t('validation.apiKey'))
      },
      trigger: ['input', 'blur']
    }
  ],
  azureEndpoint: [
    {
      validator: () => {
        if (provider.value !== 'azure') return Promise.resolve()
        const effective = providerForm.azureEndpoint || providerDefaults.value?.azure_endpoint
        if (!effective) {
          return Promise.reject(t('validation.endpoint'))
        }
        try {
          const url = new URL(effective)
          if (!/^https:/i.test(url.protocol)) {
            return Promise.reject(t('validation.endpoint'))
          }
        } catch (error) {
          return Promise.reject(t('validation.endpoint'))
        }
        return Promise.resolve()
      },
      trigger: ['input', 'blur']
    }
  ],
  azureDeploymentId: [
    {
      validator: () => {
        if (provider.value !== 'azure') return Promise.resolve()
        const effective = providerForm.azureDeploymentId || providerDefaults.value?.azure_deployment_id
        if (!effective) {
          return Promise.reject(t('validation.deployment'))
        }
        return Promise.resolve()
      },
      trigger: ['blur', 'input']
    }
  ],
  azureApiVersion: [
    {
      validator: () => {
        if (provider.value !== 'azure') return Promise.resolve()
        const effective = providerForm.azureApiVersion || providerDefaults.value?.azure_api_version
        if (!effective) {
          return Promise.reject(t('validation.required'))
        }
        return Promise.resolve()
      },
      trigger: ['blur', 'input']
    }
  ]
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatNumber(value: number, fractionDigits: number): string {
  const localeMap: Record<string, string> = {
    en: 'en-US',
    'zh-CN': 'zh-CN',
    'zh-HK': 'zh-HK'
  }
  const nf = new Intl.NumberFormat(localeMap[locale.value] ?? 'en-US', {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits
  })
  return nf.format(value)
}

function setStatus(key: typeof statusKey.value, type: typeof statusType.value, detail?: string | null) {
  statusKey.value = key
  statusType.value = type
  statusDetails.value = detail ?? null
}

function applyTemplate(text: string) {
  prompt.value = text
}

async function handleValidateKey() {
  await providerFormRef.value?.validate()
  keyStatus.value = 'loading'
  keyStatusText.value = t('provider.validating')
  try {
    const providerConfig = buildProviderConfig()
    const response = await validateKey(providerConfig)
    keyStatus.value = response.ok ? 'valid' : 'invalid'
    if (response.used_default) {
      keyStatusText.value = response.message ?? t('provider.defaultKeyNotice')
    } else {
      keyStatusText.value = response.message ?? (response.ok ? t('provider.valid') : t('provider.invalid'))
    }
  } catch (error) {
    keyStatus.value = 'invalid'
    keyStatusText.value = error instanceof Error ? error.message : t('provider.invalid')
  }
}

function buildProviderConfig(): ProviderConfig {
  if (isBasicMode.value) {
    const defaults = providerDefaults.value
    if (!defaults) {
      throw new Error(t('status.error'))
    }
    const endpoint = defaults.azure_endpoint
    const deploymentId = defaults.azure_deployment_id
    const apiVersion = defaults.azure_api_version
    if (!endpoint) {
      throw new Error(t('validation.endpoint'))
    }
    if (!deploymentId) {
      throw new Error(t('validation.deployment'))
    }
    if (!apiVersion) {
      throw new Error(t('validation.required'))
    }
    provider.value = 'azure'
    return {
      provider: 'azure',
      api_key: null,
      endpoint,
      deployment_id: deploymentId,
      api_version: apiVersion
    }
  }
  if (provider.value === 'azure') {
    const endpoint = providerForm.azureEndpoint || providerDefaults.value?.azure_endpoint
    const deploymentId = providerForm.azureDeploymentId || providerDefaults.value?.azure_deployment_id
    const apiVersion = providerForm.azureApiVersion || providerDefaults.value?.azure_api_version
    if (!endpoint) {
      throw new Error(t('validation.endpoint'))
    }
    if (!deploymentId) {
      throw new Error(t('validation.deployment'))
    }
    if (!apiVersion) {
      throw new Error(t('validation.required'))
    }
    if (!providerForm.apiKey && !hasDefaultKeys.value.azure) {
      throw new Error(t('validation.apiKey'))
    }
    return {
      provider: 'azure',
      api_key: providerForm.apiKey || null,
      endpoint,
      deployment_id: deploymentId,
      api_version: apiVersion
    }
  }
  if (!providerForm.apiKey && !hasDefaultKeys.value.openai) {
    throw new Error(t('validation.apiKey'))
  }
  return {
    provider: 'openai',
    api_key: providerForm.apiKey || null
  }
}

async function handleUploadChange({
  file,
  fileList
}: {
  file: UploadFileInfo
  fileList: UploadFileInfo[]
}) {
  if (file.status === 'removed' || fileList.length === 0) {
    clearUploadState(true)
    return
  }

  if (!file.file) {
    return
  }

  currentFile.value = file.file as File
  setStatus('analyzing', 'info')
  try {
    const response: AnalyzeFileResponse = await analyzeFile(file.file as File, selectedModel.value)
    fileMeta.value = response.file
    resultText.value = ''
    resultDownloadUrl.value = ''
    setStatus('ready', 'success')
  } catch (error) {
    const msg = error instanceof Error ? error.message : t('status.error')
    setStatus('error', 'error', msg)
    fileMeta.value = null
    message.error(msg)
  }
}

async function handleRemove() {
  if (fileMeta.value) {
    try {
      await deleteFile(fileMeta.value.file_id)
    } catch (error) {
      message.error(t('transcription.deleteFailure'))
    }
  }
  uploadList.value = []
  clearUploadState()
}

function clearUploadState(force = false) {
  if (!force && uploadList.value.length > 0) {
    return
  }
  fileMeta.value = null
  currentFile.value = null
  resultText.value = ''
  resultDownloadUrl.value = ''
  setStatus('waiting', 'default')
}

function handleFileListUpdate(files: UploadFileInfo[]) {
  if (files.length === 0) {
    clearUploadState(true)
  }
}

function resolveModelForRequest(): string {
  if (provider.value === 'azure') {
    return providerForm.azureDeploymentId || providerDefaults.value?.azure_deployment_id || selectedModel.value
  }
  return selectedModel.value
}

async function handleTranscribe() {
  await providerFormRef.value?.validate()
  if (!fileMeta.value) {
    message.warning(t('upload.removed'))
    return
  }

  let providerConfig: ProviderConfig
  try {
    providerConfig = buildProviderConfig()
  } catch (error) {
    const msg = error instanceof Error ? error.message : t('validation.apiKey')
    message.error(msg)
    return
  }

  const payload: TranscriptionRequest = {
    file_id: fileMeta.value.file_id,
    model: resolveModelForRequest(),
    format: isBasicMode.value ? 'text' : selectedFormat.value,
    language: isBasicMode.value ? providerDefaults.value?.language ?? null : selectedLanguage.value || null,
    prompt: isBasicMode.value ? null : prompt.value || null,
    stream: isBasicMode.value ? false : isStreaming.value,
    provider: providerConfig
  }

  transcribing.value = true
  resultText.value = ''
  setStatus('transcribing', 'info')

  try {
    if (isStreaming.value) {
      for await (const event of streamTranscription(payload)) {
        if (event.type === 'chunk') {
          resultText.value += event.data
        } else if (event.type === 'complete') {
          resultDownloadUrl.value = event.download_url
          setStatus('success', 'success')
        } else if (event.type === 'error') {
          throw new Error(event.data)
        }
      }
    } else {
      const response = await transcribe(payload)
      resultText.value = response.result.text_preview
      resultDownloadUrl.value = response.result.download_url
      setStatus('success', 'success')
    }
  } catch (error) {
    const msg = error instanceof Error ? error.message : t('status.error')
    setStatus('error', 'error', msg)
    message.error(msg)
  } finally {
    transcribing.value = false
  }
}

async function handleDownload() {
  if (!resultDownloadUrl.value) return
  try {
    const response = await apiStream(resultDownloadUrl.value, { method: 'GET' })
    if (!response.ok) {
      throw new Error(await response.text())
    }
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const disposition = response.headers.get('content-disposition')
    const matches = disposition?.match(/filename="?([^";]+)"?/)
    const filename = matches?.[1] ?? 'transcription.txt'
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = filename
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    URL.revokeObjectURL(url)
  } catch (error) {
    const msg = error instanceof Error ? error.message : t('transcription.downloadFailure')
    message.error(msg)
  }
}

function applyDefaultsFromOptions(data: OptionsResponse) {
  const defaultValues = data.defaults
  providerDefaults.value = defaultValues
  hasDefaultKeys.value = {
    openai: data.has_default_keys.openai ?? false,
    azure: data.has_default_keys.azure ?? false
  }
  provider.value = defaultValues.provider
  selectedModel.value = defaultValues.model
  selectedLanguage.value = defaultValues.language ?? (data.languages[0]?.code ?? '')
  streamEnabled.value = provider.value === 'openai' ? defaultValues.stream_enabled : false
  providerForm.azureEndpoint = ''
  providerForm.azureDeploymentId = defaultValues.azure_deployment_id ?? ''
  providerForm.azureApiVersion = defaultValues.azure_api_version ?? ''
  if (isBasicMode.value) {
    provider.value = 'azure'
    selectedFormat.value = 'text'
    streamEnabled.value = false
    selectedLanguage.value = defaultValues.language ?? ''
  }
}

onMounted(async () => {
  try {
    const fetched = await fetchOptions()
    options.value = fetched
    applyDefaultsFromOptions(fetched)
    if (!selectedLanguage.value && fetched.languages.length) {
      selectedLanguage.value = fetched.languages[0].code
    }
  } catch (error) {
    const msg = error instanceof Error ? error.message : t('status.error')
    message.error(msg)
  }
})

watch(
  () => appMode.mode.value,
  (mode) => {
    if (mode === 'basic') {
      advancedSnapshot.value = {
        provider: provider.value,
        selectedModel: selectedModel.value,
        selectedFormat: selectedFormat.value,
        selectedLanguage: selectedLanguage.value,
        streamEnabled: streamEnabled.value,
        prompt: prompt.value,
        providerForm: {
          apiKey: providerForm.apiKey,
          azureEndpoint: providerForm.azureEndpoint,
          azureDeploymentId: providerForm.azureDeploymentId,
          azureApiVersion: providerForm.azureApiVersion
        }
      }
      provider.value = 'azure'
      selectedFormat.value = 'text'
      streamEnabled.value = false
      prompt.value = ''
      providerForm.apiKey = ''
      providerForm.azureEndpoint = ''
      providerForm.azureDeploymentId = ''
      providerForm.azureApiVersion = ''
      selectedLanguage.value = providerDefaults.value?.language ?? ''
    } else if (mode === 'advanced' && advancedSnapshot.value) {
      const snapshot = advancedSnapshot.value
      provider.value = snapshot.provider
      selectedModel.value = snapshot.selectedModel
      selectedFormat.value = snapshot.selectedFormat
      selectedLanguage.value = snapshot.selectedLanguage
      streamEnabled.value = snapshot.streamEnabled
      prompt.value = snapshot.prompt
      providerForm.apiKey = snapshot.providerForm.apiKey
      providerForm.azureEndpoint = snapshot.providerForm.azureEndpoint
      providerForm.azureDeploymentId = snapshot.providerForm.azureDeploymentId
      providerForm.azureApiVersion = snapshot.providerForm.azureApiVersion
    }
  }
)

watch(
  () => uploadList.value.length,
  (length) => {
    if (length === 0) {
      clearUploadState()
    }
  }
)

watch(provider, (value) => {
  if (value === 'azure') {
    streamEnabled.value = false
    if (selectedFormat.value !== 'text') {
      selectedFormat.value = 'text'
    }
  } else if (providerDefaults.value) {
    streamEnabled.value = providerDefaults.value.stream_enabled
  }
})

watch(selectedModel, async () => {
  if (provider.value === 'azure') return
  if (!currentFile.value || !fileMeta.value || reanalyzing.value) return
  try {
    reanalyzing.value = true
    setStatus('analyzing', 'info')
    const response: AnalyzeFileResponse = await analyzeFile(currentFile.value, selectedModel.value)
    fileMeta.value = response.file
    setStatus('ready', 'success', t('status.updatedForModel'))
  } catch (error) {
    const msg = error instanceof Error ? error.message : t('status.error')
    setStatus('error', 'error', msg)
  } finally {
    reanalyzing.value = false
  }
})
</script>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 24px;
  padding: 24px;
  min-height: 100%;
}

.layout.basic-mode {
  grid-template-columns: 1fr;
  max-width: 1080px;
  margin: 0 auto;
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.workflow-strip {
  display: grid;
  gap: 12px;
}

.card {
  box-shadow: 0 12px 32px -20px rgba(15, 23, 42, 0.35);
  border-radius: 16px;
}

.upload-inner {
  display: grid;
  place-items: center;
  padding: 24px;
  text-align: center;
  color: var(--sst-upload-text, #475569);
}

.upload-inner p {
  color: inherit;
}

.upload-inner :deep(.n-icon) {
  color: inherit;
}

.sub {
  font-size: 12px;
  color: var(--sst-upload-subtext, #94a3b8);
}

:global(body.theme-dark) {
  --sst-upload-text: rgba(226, 232, 240, 0.88);
  --sst-upload-subtext: rgba(203, 213, 225, 0.72);
}

.mode-summary {
  border-radius: 8px;
}

.info {
  margin-top: 16px;
}

.format-notice {
  margin-top: 8px;
}

.default-key {
  margin-bottom: 12px;
  background-color: rgba(59, 130, 246, 0.1);
  border-radius: 8px;
  color: rgba(30, 64, 175, 0.9);
}

.actions {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.hint {
  margin-left: 12px;
  color: #64748b;
  font-size: 13px;
}

.key-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

@media (max-width: 1200px) {
  .layout {
    grid-template-columns: 1fr;
  }

  .sidebar {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .sidebar .card {
    flex: 1 1 320px;
  }
}
</style>
