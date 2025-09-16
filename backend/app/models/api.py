from __future__ import annotations

import json

from enum import Enum
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field, HttpUrl


class ProviderEnum(str, Enum):
    OPENAI = "openai"
    AZURE = "azure"


class BaseProviderConfig(BaseModel):
    provider: ProviderEnum


class OpenAIProviderConfig(BaseProviderConfig):
    provider: Literal[ProviderEnum.OPENAI] = ProviderEnum.OPENAI
    api_key: Optional[str] = None


class AzureProviderConfig(BaseProviderConfig):
    provider: Literal[ProviderEnum.AZURE] = ProviderEnum.AZURE
    api_key: Optional[str] = None
    endpoint: HttpUrl
    deployment_id: str = Field(..., min_length=1)
    api_version: str


ProviderConfig = Annotated[
    Union[OpenAIProviderConfig, AzureProviderConfig],
    Field(discriminator="provider"),
]


class ValidateKeyRequest(BaseModel):
    provider: ProviderConfig


class ValidateKeyResponse(BaseModel):
    ok: bool
    provider: ProviderEnum
    message: Optional[str] = None
    used_default: bool = False


class LanguageOption(BaseModel):
    code: str
    label: str


class ModelOption(BaseModel):
    name: str
    price_hint: str
    description: str


class FormatOption(BaseModel):
    value: str
    label: str
    description: str


class ProviderDefaults(BaseModel):
    provider: ProviderEnum
    model: str
    language: Optional[str]
    stream_enabled: bool
    azure_endpoint: Optional[str]
    azure_deployment_id: Optional[str]
    azure_api_version: Optional[str]


class OptionsResponse(BaseModel):
    languages: list[LanguageOption]
    models: list[ModelOption]
    formats: dict[str, list[FormatOption]]
    streamable_models: list[str]
    defaults: ProviderDefaults
    has_default_keys: dict[str, bool]


class CostEstimate(BaseModel):
    usd: float
    hkd: float
    cny: float
    duration_minutes: float


class FileMetadata(BaseModel):
    file_id: str
    name: str
    size_bytes: int
    duration_seconds: Optional[float]
    duration_text: Optional[str]
    cost: Optional[CostEstimate]


class AnalyzeFileResponse(BaseModel):
    file: FileMetadata


class TranscriptionRequest(BaseModel):
    file_id: str
    model: str
    format: str
    language: Optional[str]
    prompt: Optional[str]
    provider: ProviderConfig
    stream: bool = False


class TranscriptionResult(BaseModel):
    transcript_id: str
    format: str
    text_preview: str
    download_url: str


class TranscriptionResponse(BaseModel):
    result: TranscriptionResult


class StreamEvent(BaseModel):
    type: Literal["chunk", "complete", "error"]
    data: str
    download_url: Optional[str] = None
    transcript_id: Optional[str] = None

    def model_dump_sse(self) -> str:
        payload = self.model_dump()
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
