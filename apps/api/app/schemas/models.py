from pydantic import BaseModel


class ChatModelOption(BaseModel):
    id: str
    label: str
    provider: str
    model: str
    base_url: str
    enabled: bool
    supports_thinking: bool = False
