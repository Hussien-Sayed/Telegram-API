"""Pydantic request/response models for the Telegram API microservice."""

from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SendMessageRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chat_id": 123456789,
                "text": "Hello from the bot!",
                "kwargs": {"parse_mode": "Markdown"},
            }
        }
    )

    chat_id: int
    text: str
    kwargs: Optional[Dict[str, Any]] = None


class SendReplyKeyboardRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chat_id": 123456789,
                "text": "Pick an option",
                "keyboard": [["Yes", "No"], ["Cancel"]],
                "resize_keyboard": True,
                "one_time_keyboard": False,
                "kwargs": {},
            }
        }
    )

    chat_id: int
    text: str
    keyboard: List[List[str]]
    resize_keyboard: bool = True
    one_time_keyboard: bool = False
    kwargs: Optional[Dict[str, Any]] = None


class RemoveReplyKeyboardRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chat_id": 123456789,
                "text": "Keyboard removed.",
                "kwargs": {},
            }
        }
    )

    chat_id: int
    text: str = "Keyboard removed."
    kwargs: Optional[Dict[str, Any]] = None


class GetUpdatesRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chat_id": 123456789,
                "limit": 10,
                "timeout": 0,
            }
        }
    )

    chat_id: Optional[int] = None
    limit: int = Field(10, ge=1, le=100)
    timeout: int = Field(0, ge=0)


class GetChatIdsParams(BaseModel):
    """Query parameters for GET /get_chat_ids."""

    model_config = ConfigDict(
        json_schema_extra={"example": {"limit": 10}}
    )

    limit: int = Field(10, ge=1, le=100)


class SendFileRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chat_id": 123456789,
                "filename": "document.pdf",
                "caption": "Here is the document you requested",
                "file_type": "document",
                "kwargs": {},
            }
        }
    )

    chat_id: int
    filename: str
    caption: Optional[str] = None
    file_type: Literal["document", "photo", "video", "audio"]
    kwargs: Optional[Dict[str, Any]] = None

    @field_validator("file_type")
    @classmethod
    def validate_file_type(cls, v: str) -> str:
        """Validate that file_type is one of the allowed values."""
        allowed_types = {"document", "photo", "video", "audio"}
        if v not in allowed_types:
            raise ValueError(
                f"file_type must be one of: {', '.join(sorted(allowed_types))}"
            )
        return v


class MessageResponse(BaseModel):
    success: bool
    message_id: Optional[int] = None
    error: Optional[str] = None


class UpdatesResponse(BaseModel):
    success: bool
    updates: List[Dict[str, Any]]
    error: Optional[str] = None


class ChatIdsResponse(BaseModel):
    success: bool
    chat_ids: List[Dict[str, Any]]
    error: Optional[str] = None


class BotsResponse(BaseModel):
    success: bool
    bot_names: List[str]
    error: Optional[str] = None
