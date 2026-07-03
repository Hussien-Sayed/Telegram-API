"""FastAPI router exposing TelegramClient methods as HTTP endpoints."""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query
from telegram.error import TelegramError

from telegram_api import TelegramClient
from telegram_api.utils import transcribe_voice

from .models import (
    ChatIdsResponse,
    GetUpdatesRequest,
    MessageResponse,
    RemoveReplyKeyboardRequest,
    SendMessageRequest,
    SendFileRequest,
    SendReplyKeyboardRequest,
    UpdatesResponse,
)


def create_router(client: TelegramClient) -> APIRouter:
    """Create an APIRouter with endpoints backed by the given TelegramClient."""
    router = APIRouter(prefix="/api/v1")

    @router.post("/send_message", response_model=MessageResponse)
    async def send_message(request: SendMessageRequest) -> Dict[str, Any]:
        try:
            message = await client.send_message(
                chat_id=request.chat_id,
                text=request.text,
                **(request.kwargs or {}),
            )
            return {
                "success": True,
                "message_id": getattr(message, "message_id", None),
                "error": None,
            }
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except TelegramError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @router.post("/send_reply_keyboard", response_model=MessageResponse)
    async def send_reply_keyboard(
        request: SendReplyKeyboardRequest,
    ) -> Dict[str, Any]:
        try:
            message = await client.send_reply_keyboard(
                chat_id=request.chat_id,
                text=request.text,
                keyboard=request.keyboard,
                resize_keyboard=request.resize_keyboard,
                one_time_keyboard=request.one_time_keyboard,
                **(request.kwargs or {}),
            )
            return {
                "success": True,
                "message_id": getattr(message, "message_id", None),
                "error": None,
            }
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except TelegramError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @router.post("/remove_reply_keyboard", response_model=MessageResponse)
    async def remove_reply_keyboard(
        request: RemoveReplyKeyboardRequest,
    ) -> Dict[str, Any]:
        try:
            message = await client.remove_reply_keyboard(
                chat_id=request.chat_id,
                text=request.text,
                **(request.kwargs or {}),
            )
            return {
                "success": True,
                "message_id": getattr(message, "message_id", None),
                "error": None,
            }
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except TelegramError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @router.post("/send_file", response_model=MessageResponse)
    async def send_file(request: SendFileRequest) -> Dict[str, Any]:
        try:
            message = await client.send_file(
                chat_id=request.chat_id,
                filename=request.filename,
                caption=request.caption,
                file_type=request.file_type,
                **(request.kwargs or {}),
            )
            return {
                "success": True,
                "message_id": getattr(message, "message_id", None),
                "error": None,
            }
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except TelegramError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @router.post("/get_updates", response_model=UpdatesResponse)
    async def get_updates(request: GetUpdatesRequest) -> Dict[str, Any]:
        try:
            updates = await client.get_updates(
                chat_id=request.chat_id,
                limit=request.limit,
                timeout=request.timeout,
            )
            updates_list = []
            for update in updates:
                if update.message and update.message.voice:
                    text = await transcribe_voice(update.message.voice, client.bot)
                elif update.message and update.message.text:
                    text = update.message.text
                else:
                    text = None
                updates_list.append({
                    "update_id": update.update_id,
                    "chat_id": (
                        update.effective_chat.id
                        if update.effective_chat
                        else None
                    ),
                    "text": text,
                })
            return {
                "success": True,
                "updates": updates_list,
                "error": None,
            }
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except TelegramError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @router.get("/get_chat_ids", response_model=ChatIdsResponse)
    async def get_chat_ids(
        limit: int = Query(10, ge=1, le=100),
    ) -> Dict[str, Any]:
        try:
            updates = await client.get_updates(limit=limit)
            seen: set = set()
            chat_ids: List[Dict[str, Any]] = []
            for update in updates:
                chat_id = (
                    update.effective_chat.id if update.effective_chat else None
                )
                if update.message and update.message.voice:
                    text = await transcribe_voice(update.message.voice, client.bot)
                elif update.message and update.message.text:
                    text = update.message.text
                else:
                    text = None
                if chat_id is not None and chat_id not in seen:
                    seen.add(chat_id)
                    chat_ids.append({"chat_id": chat_id, "text": text})
            return {
                "success": True,
                "chat_ids": chat_ids,
                "error": None,
            }
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except TelegramError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return router
