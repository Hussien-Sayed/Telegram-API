"""Pydantic request/response models for the Telegram API microservice."""

from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SendMessageRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chat_id": 123456789,
                "text": "**Hello** from the bot!",
                "kwargs": {"parse_mode": "MarkdownV2"},
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
                "limit": 10,
                "timeout": 0,
            }
        }
    )

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


class EditMessageRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chat_id": 123456789,
                "message_id": 123,
                "text": "**Updated** message text",
                "kwargs": {"parse_mode": "MarkdownV2"},
            }
        }
    )

    chat_id: int
    message_id: int
    text: str
    kwargs: Optional[Dict[str, Any]] = None


class FileInfo(BaseModel):
    """Metadata about a file attachment in a Telegram update."""

    file_id: str
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None


class DownloadFileRequest(BaseModel):
    """Request to download a Telegram file to the shared workspace."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_id": "ABC...",
                "dest_path": "myproject/uploads/document.pdf",
            }
        }
    )

    file_id: str
    dest_path: str

    @field_validator("dest_path")
    @classmethod
    def validate_dest_path(cls, v: str) -> str:
        """Validate that dest_path is a safe relative path."""
        if not v:
            raise ValueError("dest_path is required")
        if v.startswith("/"):
            raise ValueError("dest_path must be relative, not absolute")
        if any(part == ".." for part in v.split("/")):
            raise ValueError("dest_path must not contain '..'")
        return v


class DownloadFileResponse(BaseModel):
    """Response from the download_file endpoint."""

    success: bool
    saved_path: Optional[str] = None
    error: Optional[str] = None


class UpdateEntry(BaseModel):
    """Single update entry returned by the get_updates endpoint."""

    update_id: int
    chat_id: Optional[int] = None
    message_type: Optional[Literal["voice", "text", "document", "photo", "video", "audio"]] = None
    text: Optional[str] = None
    reply_to_message_id: Optional[int] = None
    file: Optional[FileInfo] = None


class ChatIdEntry(BaseModel):
    """Single chat ID entry returned by the get_chat_ids endpoint."""

    chat_id: int
    message_type: Optional[Literal["voice", "text", "document", "photo", "video", "audio"]] = None
    text: Optional[str] = None


class MessageResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "message_id": 123,
                    "split": False,
                    "message_ids": None,
                    "error": None,
                },
                {
                    "success": True,
                    "message_id": None,
                    "split": True,
                    "message_ids": [123, 124, 125],
                    "error": None,
                },
            ]
        }
    )

    success: bool
    message_id: Optional[int] = None
    split: bool = False
    message_ids: Optional[List[int]] = None
    error: Optional[str] = None


class UpdatesResponse(BaseModel):
    success: bool
    updates: List[UpdateEntry]
    error: Optional[str] = None


class ChatIdsResponse(BaseModel):
    success: bool
    chat_ids: List[ChatIdEntry]
    error: Optional[str] = None


class BotsResponse(BaseModel):
    success: bool
    bot_names: List[str]
    error: Optional[str] = None
