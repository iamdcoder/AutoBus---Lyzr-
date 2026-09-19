
from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        extra="ignore",
    )

    
    LYZR_API_KEY: str = Field(
        default="",
        description="Lyzr Agent API key. A credential, never an identifier: "
        "never logged, never returned by any endpoint.",
    )
    LYZR_BASE_URL: str = Field(
        default="https://agent-prod.studio.lyzr.ai",
        description="Base URL for the Lyzr Agent API.",
    )
    LYZR_CHAT_TIMEOUT: float = Field(
        default=90.0,
        gt=0,
        description="Timeout in seconds for a single Lyzr chat inference call.",
    )
    LYZR_USE_SDK: str = Field(
        default="1",
        description="'1' prefers the Lyzr ADK/SDK transport over the raw Agent API.",
    )
    LYZR_SDK_FALLBACK: str = Field(
        default="1",
        description="'1' allows falling back to the Agent API if the SDK is unavailable.",
    )
    LYZR_USER_ID: str = Field(
        default="buyer-system",
        description="Lyzr user id associated with agent sessions.",
    )

    
    BUYER_AGENT_ID: str = Field(default="", description="Lyzr Studio agent id for the Buyer agent.")
    SUPPLIER_AGENT_ID: str = Field(default="", description="Lyzr Studio agent id for the Supplier agent.")

    
    LYZR_GUARDRAIL_URL: str = Field(
        default="",
        description="Optional Lyzr Responsible AI custom guardrail endpoint. "
        "When set, governance calls fail closed if it is unreachable.",
    )
    LYZR_GUARDRAIL_TOKEN: str = Field(default="", description="Bearer token for LYZR_GUARDRAIL_URL.")
    LYZR_GOVERNANCE_TIMEOUT: float = Field(
        default=8.0,
        gt=0,
        description="Timeout in seconds for the external governance guardrail call.",
    )
    LYZR_RAI_POLICY_ID: str = Field(
        default="",
        description="Responsible AI policy id assigned to the Lyzr Studio agents, if any.",
    )
    LYZR_RESPONSIBLE_AI_ENABLED: str = Field(
        default="",
        description="Non-empty marker set once a Responsible AI policy has been "
        "enabled on the two Studio agents.",
    )
    LYZR_VERIFY_AGENT_FEATURES: str = Field(
        default="1",
        description="'1' verifies live Studio agent feature flags when reporting /api/lyzr/status.",
    )

    
    LYZR_AIMS_WEBHOOK_URL: str = Field(
        default="",
        description="Optional external AIMS-compatible event sink. Falls back to a "
        "local JSONL outbox when unset.",
    )
    LYZR_AIMS_TOKEN: str = Field(default="", description="Bearer token for LYZR_AIMS_WEBHOOK_URL.")
    LYZR_AIMS_OUTBOX: str = Field(
        default="data/aims_outbox.jsonl",
        description="Local fallback path for AIMS-envelope events when no external sink is configured.",
    )

    
    CORS_ORIGINS: str = Field(
        default="*",
        description="Comma-separated list of allowed CORS origins, or '*' for all.",
    )
    PUBLIC_BASE_URL: str = Field(default="", description="Public base URL of this deployment (display only).")

    
    
    
    

    @property
    def sdk_preferred(self) -> bool:
        return self.LYZR_USE_SDK == "1"

    @property
    def sdk_fallback_enabled(self) -> bool:
        return self.LYZR_SDK_FALLBACK == "1"

    @property
    def agent_feature_check_enabled(self) -> bool:
        return self.LYZR_VERIFY_AGENT_FEATURES == "1"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def lyzr_api_key_configured(self) -> bool:
        return bool(self.LYZR_API_KEY.strip())

    @property
    def studio_agents_configured(self) -> bool:
        return bool(self.BUYER_AGENT_ID.strip()) and bool(self.SUPPLIER_AGENT_ID.strip())

    @property
    def responsible_ai_endpoint_configured(self) -> bool:
        return bool(self.LYZR_GUARDRAIL_URL.strip())

    @property
    def aims_sink_configured(self) -> bool:
        return bool(self.LYZR_AIMS_WEBHOOK_URL.strip())


def get_settings() -> Settings:

    return Settings()
