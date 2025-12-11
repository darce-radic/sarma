from typing import Optional
from pydantic import BaseModel


class SystemSettingsPayload(BaseModel):
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    spoonacular_api_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    coles_woolworths_mcp_url: Optional[str] = None


class SystemSettingsResponse(SystemSettingsPayload):
    pass

