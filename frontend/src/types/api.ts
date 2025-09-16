export type ProviderKind = 'openai' | 'azure'

export interface OpenAIProviderConfig {
  provider: 'openai'
  api_key?: string | null
}

export interface AzureProviderConfig {
  provider: 'azure'
  api_key?: string | null
  endpoint: string
  deployment_id: string
  api_version: string
}

export type ProviderConfig = OpenAIProviderConfig | AzureProviderConfig

export interface ValidateKeyResponse {
  ok: boolean
  provider: ProviderKind
  message?: string
  used_default: boolean
}

export interface LanguageOption {
  code: string
  label: string
}

export interface ModelOption {
  name: string
  price_hint: string
  description: string
}

export interface FormatOption {
  value: string
  label: string
  description: string
}

export interface OptionsResponse {
  languages: LanguageOption[]
  models: ModelOption[]
  formats: Record<string, FormatOption[]>
  streamable_models: string[]
  defaults: ProviderDefaults
  has_default_keys: Record<ProviderKind, boolean>
}

export interface CostEstimate {
  usd: number
  hkd: number
  cny: number
  duration_minutes: number
}

export interface FileMetadata {
  file_id: string
  name: string
  size_bytes: number
  duration_seconds?: number | null
  duration_text?: string | null
  cost?: CostEstimate | null
}

export interface AnalyzeFileResponse {
  file: FileMetadata
}

export interface ProviderDefaults {
  provider: ProviderKind
  model: string
  language?: string | null
  stream_enabled: boolean
  azure_endpoint?: string | null
  azure_deployment_id?: string | null
  azure_api_version?: string | null
}

export interface TranscriptionRequest {
  file_id: string
  model: string
  format: string
  language?: string | null
  prompt?: string | null
  provider: ProviderConfig
  stream?: boolean
}

export interface TranscriptionResult {
  transcript_id: string
  format: string
  text_preview: string
  download_url: string
}

export interface TranscriptionResponse {
  result: TranscriptionResult
}

export interface StreamEventChunk {
  type: 'chunk'
  data: string
}

export interface StreamEventComplete {
  type: 'complete'
  data: string
  download_url: string
  transcript_id: string
}

export interface StreamEventError {
  type: 'error'
  data: string
}

export type StreamEvent = StreamEventChunk | StreamEventComplete | StreamEventError
