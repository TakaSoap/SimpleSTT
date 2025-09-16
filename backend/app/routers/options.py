from fastapi import APIRouter, Depends

from ..config import get_settings
from ..dependencies import CredentialsDep
from ..models.api import (
    FormatOption,
    LanguageOption,
    ModelOption,
    OptionsResponse,
    ProviderDefaults,
    ProviderEnum,
)

router = APIRouter(prefix="/api/options", tags=["options"])


LANGUAGES: list[LanguageOption] = [
    LanguageOption(label="自动检测", code=""),
    LanguageOption(label="中文", code="zh"),
    LanguageOption(label="英语", code="en"),
    LanguageOption(label="日语", code="ja"),
    LanguageOption(label="韩语", code="ko"),
    LanguageOption(label="法语", code="fr"),
    LanguageOption(label="德语", code="de"),
    LanguageOption(label="西班牙语", code="es"),
    LanguageOption(label="俄语", code="ru"),
    LanguageOption(label="阿拉伯语", code="ar"),
    LanguageOption(label="葡萄牙语", code="pt"),
    LanguageOption(label="意大利语", code="it"),
    LanguageOption(label="荷兰语", code="nl"),
    LanguageOption(label="波兰语", code="pl"),
    LanguageOption(label="土耳其语", code="tr"),
    LanguageOption(label="瑞典语", code="sv"),
    LanguageOption(label="丹麦语", code="da"),
    LanguageOption(label="挪威语", code="no"),
    LanguageOption(label="芬兰语", code="fi"),
    LanguageOption(label="匈牙利语", code="hu"),
    LanguageOption(label="捷克语", code="cs"),
    LanguageOption(label="泰语", code="th"),
    LanguageOption(label="越南语", code="vi"),
    LanguageOption(label="印地语", code="hi"),
    LanguageOption(label="印尼语", code="id"),
    LanguageOption(label="马来语", code="ms"),
    LanguageOption(label="希腊语", code="el"),
    LanguageOption(label="希伯来语", code="he"),
    LanguageOption(label="乌克兰语", code="uk"),
    LanguageOption(label="保加利亚语", code="bg"),
    LanguageOption(label="克罗地亚语", code="hr"),
    LanguageOption(label="斯洛伐克语", code="sk"),
    LanguageOption(label="斯洛文尼亚语", code="sl"),
    LanguageOption(label="罗马尼亚语", code="ro"),
    LanguageOption(label="拉脱维亚语", code="lv"),
    LanguageOption(label="立陶宛语", code="lt"),
    LanguageOption(label="爱沙尼亚语", code="et"),
]

MODELS: list[ModelOption] = [
    ModelOption(name="gpt-4o-transcribe", price_hint="$0.006/分", description="最新 GPT-4o, 最高质量"),
    ModelOption(name="gpt-4o-mini-transcribe", price_hint="$0.003/分", description="快速经济, 适合批量"),
    ModelOption(name="whisper-1", price_hint="$0.006/分", description="支持时间戳和多格式"),
]

FORMATS: dict[str, list[FormatOption]] = {
    "base": [
        FormatOption(value="text", label="纯文本", description="简洁文本输出"),
        FormatOption(value="json", label="JSON", description="结构化结果"),
    ],
    "whisper": [
        FormatOption(value="srt", label="SRT 字幕", description="标准字幕格式"),
        FormatOption(value="vtt", label="VTT 字幕", description="WebVTT 字幕"),
        FormatOption(value="verbose_json", label="详细 JSON", description="含时间戳和置信度"),
    ],
}

STREAMABLE_MODELS = ["gpt-4o-transcribe", "gpt-4o-mini-transcribe"]


@router.get("", response_model=OptionsResponse)
async def get_options(_: CredentialsDep) -> OptionsResponse:
    settings = get_settings()
    defaults = ProviderDefaults(
        provider=ProviderEnum(settings.default_provider),
        model=settings.default_model,
        language=settings.default_language or None,
        stream_enabled=settings.default_stream_enabled,
        azure_endpoint=str(settings.default_azure_endpoint) if settings.default_azure_endpoint else None,
        azure_deployment_id=settings.default_azure_deployment_id or None,
        azure_api_version=settings.default_azure_api_version,
    )

    return OptionsResponse(
        languages=LANGUAGES,
        models=MODELS,
        formats=FORMATS,
        streamable_models=STREAMABLE_MODELS,
        defaults=defaults,
        has_default_keys={
            "openai": bool(settings.default_openai_api_key),
            "azure": bool(settings.default_azure_api_key),
        },
    )
