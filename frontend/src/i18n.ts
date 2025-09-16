import { createI18n } from 'vue-i18n'

export const SUPPORTED_LOCALES = [
  { value: 'en', label: 'English' },
  { value: 'zh-CN', label: '简体中文' },
  { value: 'zh-HK', label: '繁體中文' }
] as const

const STORAGE_KEY = 'audio-app-locale'
const envDefault = (import.meta.env.VITE_DEFAULT_LOCALE as string | undefined)?.trim()
const fallbackLocale = 'en'

function resolveInitialLocale(): string {
  if (typeof window === 'undefined') return envDefault || fallbackLocale
  const fromStorage = window.localStorage.getItem(STORAGE_KEY)
  if (fromStorage && SUPPORTED_LOCALES.some((locale) => locale.value === fromStorage)) {
    return fromStorage
  }
  if (envDefault && SUPPORTED_LOCALES.some((locale) => locale.value === envDefault)) {
    return envDefault
  }
  return fallbackLocale
}

const messages = {
  en: {
    common: {
      appName: 'Audio Transcription Console',
      tagline: 'Modern AI-assisted transcription with OpenAI and Azure support',
      theme: {
        label: 'Theme',
        light: 'Light',
        dark: 'Dark',
        system: 'System'
      },
      language: 'Language',
      mode: {
        basic: 'Basic',
        advanced: 'Advanced'
      }
    },
    login: {
      title: 'Audio Transcription Console',
      username: 'Username',
      password: 'Password',
      login: 'Log In',
      placeholders: {
        username: 'Enter username',
        password: 'Enter password'
      },
      success: 'Signed in successfully',
      failure: 'Log in failed'
    },
    provider: {
      title: 'Access Credentials',
      apiKey: 'API Key',
      endpoint: 'Endpoint',
      deployment: 'Deployment ID',
      apiVersion: 'API Version',
      validate: 'Validate Key',
      validating: 'Validating…',
      valid: 'Key validated',
      invalid: 'Validation failed',
      modelTitle: 'Model & Language',
      model: 'Model',
      format: 'Output Format',
      language: 'Audio Language',
      stream: 'Stream Output',
      streamHint: {
        available: 'Real-time preview enabled',
        unavailable: 'Current selection does not support streaming'
      },
      autoDetect: 'Auto detect',
      defaultKeyNotice: 'Using server default API key',
      defaultEndpointNotice: 'Using server default Azure endpoint',
      azureFormatNotice: 'Basic mode uses Azure defaults and outputs plain text only'
    },
    prompts: {
      title: 'Prompt Templates',
      punctuation: 'Punctuation',
      terminology: 'Terminology',
      filler: 'Filler Words',
      clear: 'Clear',
      textareaPlaceholder: 'Optional transcription hint',
      templates: {
        punctuation: 'Please add punctuation and split sentences.',
        terminology: 'The transcript is about OpenAI, DALL·E, GPT-4, ChatGPT. Keep original terminology.',
        filler: 'Keep pauses, filler words, and repetitions.',
        clear: ''
      },
      icons: {
        punctuation: 'ListOutline',
        terminology: 'GitNetworkOutline',
        filler: 'ChatbubbleEllipsesOutline',
        clear: 'CloseCircleOutline'
      }
    },
    upload: {
      title: 'File Upload',
      instructions: 'Drag audio/video here or click to upload',
      supported: 'Supports MP3, MP4, M4A, WAV, WEBM, OGG, FLAC and more',
      analyzing: 'Analyzing file…',
      ready: 'File analyzed. Ready to transcribe.',
      removed: 'Waiting for upload',
      size: 'Size',
      duration: 'Duration',
      costEstimate: 'Cost estimate: US$ {usd} · HK$ {hkd} · CNY {cny}',
      noDuration: 'Duration unavailable'
    },
    transcription: {
      title: 'Transcription Result',
      start: 'Start Transcription',
      download: 'Download Result',
      downloading: 'Downloading…',
      deleteFailure: 'Failed to delete file',
      downloadFailure: 'Download failed'
    },
    status: {
      waiting: 'Waiting for file…',
      analyzing: 'Analyzing file…',
      ready: 'File ready for transcription',
      transcribing: 'Transcribing…',
      success: 'Transcription completed',
      error: 'Transcription failed',
      updatedForModel: 'Cost updated for new model',
      streamUnavailable: 'Streaming only supports text format'
    },
    validation: {
      required: 'This field is required',
      apiKey: 'Enter a valid API key',
      endpoint: 'Enter a valid HTTPS endpoint',
      deployment: 'Enter a deployment ID'
    },
    logout: {
      clear: 'Clear Credentials'
    },
    models: {
      'gpt-4o-transcribe': {
        label: 'gpt-4o-transcribe · $0.006/min',
        description: 'Latest GPT-4o, highest quality'
      },
      'gpt-4o-mini-transcribe': {
        label: 'gpt-4o-mini-transcribe · $0.003/min',
        description: 'Fast and economical, ideal for batches'
      },
      'whisper-1': {
        label: 'whisper-1 · $0.006/min',
        description: 'Supports timestamps and multiple formats'
      }
    },
    formats: {
      text: { label: 'Plain text', description: 'Concise text output' },
      json: { label: 'JSON', description: 'Structured JSON output' },
      srt: { label: 'SRT subtitles', description: 'Standard subtitle format' },
      vtt: { label: 'VTT subtitles', description: 'Web video subtitle format' },
      verbose_json: { label: 'Verbose JSON', description: 'Includes timestamps and confidence' }
    }
  },
  'zh-CN': {
    common: {
      appName: '音频转录控制台',
      tagline: '连接 OpenAI 与 Azure 的现代转录体验',
      theme: {
        label: '主题',
        light: '浅色',
        dark: '深色',
        system: '跟随系统'
      },
      language: '语言',
      mode: {
        basic: '简易模式',
        advanced: '高级模式'
      }
    },
    login: {
      title: '音频转录控制台',
      username: '用户名',
      password: '密码',
      login: '登录',
      placeholders: {
        username: '请输入用户名',
        password: '请输入密码'
      },
      success: '登录成功',
      failure: '登录失败'
    },
    provider: {
      title: '访问凭证',
      apiKey: 'API Key',
      endpoint: 'Endpoint',
      deployment: '部署名称',
      apiVersion: 'API 版本',
      validate: '验证密钥',
      validating: '正在验证…',
      valid: '验证成功',
      invalid: '验证失败',
      modelTitle: '模型与语言',
      model: '模型',
      format: '输出格式',
      language: '音频语言',
      stream: '流式输出',
      streamHint: {
        available: '已开启实时预览',
        unavailable: '当前设置不支持流式输出'
      },
      autoDetect: '自动检测',
      defaultKeyNotice: '正在使用服务器默认 API 密钥',
      defaultEndpointNotice: '正在使用服务器默认 Azure Endpoint',
      azureFormatNotice: '基础模式使用 Azure 默认配置，仅输出纯文本'
    },
    prompts: {
      title: '提示词模板',
      punctuation: '标点',
      terminology: '术语',
      filler: '填充词',
      clear: '清空',
      textareaPlaceholder: '可选的转录提示',
      templates: {
        punctuation: '请为转录文本补全标点并分句。',
        terminology: '音频涉及 OpenAI、DALL·E、GPT-4、ChatGPT 等术语，请保持原文表述。',
        filler: '保留停顿、语气词和重复内容。',
        clear: ''
      },
      icons: {
        punctuation: 'ListOutline',
        terminology: 'GitNetworkOutline',
        filler: 'ChatbubbleEllipsesOutline',
        clear: 'CloseCircleOutline'
      }
    },
    upload: {
      title: '文件上传',
      instructions: '拖入音频/视频文件或点击上传',
      supported: '支持 MP3、MP4、M4A、WAV、WEBM、OGG、FLAC 等格式',
      analyzing: '正在分析文件…',
      ready: '分析完成，可以开始转录',
      removed: '等待文件上传',
      size: '大小',
      duration: '时长',
      costEstimate: '费用估算：US$ {usd} · HK$ {hkd} · CNY {cny}',
      noDuration: '无法获取时长'
    },
    transcription: {
      title: '转录结果',
      start: '开始转录',
      download: '下载结果',
      downloading: '正在下载…',
      deleteFailure: '删除文件失败',
      downloadFailure: '下载失败'
    },
    status: {
      waiting: '等待文件…',
      analyzing: '正在分析文件…',
      ready: '文件可转录',
      transcribing: '正在转录…',
      success: '转录完成',
      error: '转录失败',
      updatedForModel: '已根据新模型更新费用估算',
      streamUnavailable: '流式仅支持文本格式'
    },
    validation: {
      required: '请输入内容',
      apiKey: '请输入有效的 API Key',
      endpoint: '请输入有效的 HTTPS Endpoint',
      deployment: '请输入部署名称'
    },
    logout: {
      clear: '清除凭证'
    },
    models: {
      'gpt-4o-transcribe': {
        label: 'gpt-4o-transcribe · $0.006/分',
        description: '最新 GPT-4o，准确率最高'
      },
      'gpt-4o-mini-transcribe': {
        label: 'gpt-4o-mini-transcribe · $0.003/分',
        description: '快速且经济，适合批量处理'
      },
      'whisper-1': {
        label: 'whisper-1 · $0.006/分',
        description: '支持时间戳与多种输出格式'
      }
    },
    formats: {
      text: { label: '纯文本', description: '简洁的文本输出' },
      json: { label: 'JSON', description: '结构化 JSON 数据' },
      srt: { label: 'SRT 字幕', description: '标准字幕格式' },
      vtt: { label: 'VTT 字幕', description: 'Web 视频字幕格式' },
      verbose_json: { label: '详细 JSON', description: '包含时间戳与置信度' }
    }
  },
  'zh-HK': {
    common: {
      appName: '音頻轉錄控制台',
      tagline: '整合 OpenAI 及 Azure 的現代化轉錄體驗',
      theme: {
        label: '主題',
        light: '淺色',
        dark: '深色',
        system: '跟隨系統'
      },
      language: '語言',
      mode: {
        basic: '簡易模式',
        advanced: '進階模式'
      }
    },
    login: {
      title: '音頻轉錄控制台',
      username: '用戶名稱',
      password: '密碼',
      login: '登入',
      placeholders: {
        username: '請輸入用戶名稱',
        password: '請輸入密碼'
      },
      success: '登入成功',
      failure: '登入失敗'
    },
    provider: {
      title: '存取憑證',
      apiKey: 'API Key',
      endpoint: 'Endpoint',
      deployment: '部署名稱',
      apiVersion: 'API 版本',
      validate: '驗證密鑰',
      validating: '驗證中…',
      valid: '驗證成功',
      invalid: '驗證失敗',
      modelTitle: '模型與語言',
      model: '模型',
      format: '輸出格式',
      language: '音頻語言',
      stream: '串流輸出',
      streamHint: {
        available: '已啟用即時預覽',
        unavailable: '目前設定不支援串流輸出'
      },
      autoDetect: '自動偵測',
      defaultKeyNotice: '正在使用伺服器預設 API 密鑰',
      defaultEndpointNotice: '正在使用伺服器預設 Azure Endpoint',
      azureFormatNotice: '基本模式使用 Azure 預設設定，僅提供純文字輸出'
    },
    prompts: {
      title: '提示語模板',
      punctuation: '標點',
      terminology: '術語',
      filler: '語氣詞',
      clear: '清除',
      textareaPlaceholder: '可選的轉錄提示',
      templates: {
        punctuation: '請為轉錄文字補上標點並分句。',
        terminology: '音頻涉及 OpenAI、DALL·E、GPT-4、ChatGPT 等術語，請保持原文。',
        filler: '保留停頓、語氣詞及重複內容。',
        clear: ''
      },
      icons: {
        punctuation: 'ListOutline',
        terminology: 'GitNetworkOutline',
        filler: 'ChatbubbleEllipsesOutline',
        clear: 'CloseCircleOutline'
      }
    },
    upload: {
      title: '檔案上載',
      instructions: '拖曳音頻／影片或按此上載',
      supported: '支援 MP3、MP4、M4A、WAV、WEBM、OGG、FLAC 等格式',
      analyzing: '正在分析檔案…',
      ready: '分析完成，可開始轉錄',
      removed: '等待上載',
      size: '大小',
      duration: '時長',
      costEstimate: '費用估算：US$ {usd} · HK$ {hkd} · CNY {cny}',
      noDuration: '無法取得時長'
    },
    transcription: {
      title: '轉錄結果',
      start: '開始轉錄',
      download: '下載結果',
      downloading: '下載中…',
      deleteFailure: '刪除檔案失敗',
      downloadFailure: '下載失敗'
    },
    status: {
      waiting: '等待檔案…',
      analyzing: '正在分析檔案…',
      ready: '檔案可轉錄',
      transcribing: '正在轉錄…',
      success: '轉錄完成',
      error: '轉錄失敗',
      updatedForModel: '已依新模型更新費用估算',
      streamUnavailable: '串流僅支援文字格式'
    },
    validation: {
      required: '請輸入內容',
      apiKey: '請輸入有效的 API Key',
      endpoint: '請輸入有效的 HTTPS Endpoint',
      deployment: '請輸入部署名稱'
    },
    logout: {
      clear: '清除憑證'
    },
    models: {
      'gpt-4o-transcribe': {
        label: 'gpt-4o-transcribe · $0.006/分鐘',
        description: '最新 GPT-4o，最佳準確度'
      },
      'gpt-4o-mini-transcribe': {
        label: 'gpt-4o-mini-transcribe · $0.003/分鐘',
        description: '速度快且經濟，適合批量任務'
      },
      'whisper-1': {
        label: 'whisper-1 · $0.006/分鐘',
        description: '支援時間戳與多種格式'
      }
    },
    formats: {
      text: { label: '純文字', description: '簡潔的文字輸出' },
      json: { label: 'JSON', description: '結構化 JSON 輸出' },
      srt: { label: 'SRT 字幕', description: '標準字幕格式' },
      vtt: { label: 'VTT 字幕', description: 'Web 影片字幕格式' },
      verbose_json: { label: '詳細 JSON', description: '包含時間戳與信心值' }
    }
  }
}

export const i18n = createI18n({
  legacy: false,
  locale: resolveInitialLocale(),
  fallbackLocale,
  messages
})

export function persistLocale(locale: string) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(STORAGE_KEY, locale)
}
