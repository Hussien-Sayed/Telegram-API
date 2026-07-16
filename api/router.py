"""FastAPI router exposing TelegramClient methods as HTTP endpoints."""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query
from telegram.error import TelegramError

from telegram_api import BotManager
from telegram_api.utils import transcribe_voice

from .models import (
    BotsResponse,
    ChatIdsResponse,
    EditMessageRequest,
    GetUpdatesRequest,
    MessageResponse,
    RemoveReplyKeyboardRequest,
    SendMessageRequest,
    SendFileRequest,
    SendReplyKeyboardRequest,
    UpdatesResponse,
)


def create_router(bot_manager: BotManager) -> APIRouter:
    router = APIRouter(prefix="/api/v1")

    @router.get("/bots", response_model=BotsResponse)
    async def get_bots() -> Dict[str, Any]:
        return {
            "success": True,
            "bot_names": bot_manager.get_bot_names(),
            "error": None,
        }

    @router.post("/{bot_name}/send_message", response_model=MessageResponse)
    async def send_message(bot_name: str, request: SendMessageRequest) -> Dict[str, Any]:
        try:
            client = bot_manager.get_client(bot_name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        try:
            message = await client.send_message(
                chat_id=request.chat_id,
                text=request.text,
                **(request.kwargs or {}),
            )
            # Handle new return format: Message object (non-split) or dict (split)
            if isinstance(message, dict):
                # Split case
                return {
                    "success": True,
                    "message_id": message["message_id"],
                    "split": True,
                    "message_ids": message["message_ids"],
                    "error": None,
                }
            else:
                # Non-split case (Message object)
                return {
                    "success": True,
                    "message_id": message.message_id,
                    "split": False,
                    "message_ids": None,
                    "error": None,
                }
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except TelegramError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @router.post("/{bot_name}/send_reply_keyboard", response_model=MessageResponse)
    async def send_reply_keyboard(
        bot_name: str,
        request: SendReplyKeyboardRequest,
    ) -> Dict[str, Any]:
        try:
            client = bot_manager.get_client(bot_name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
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

    @router.post("/{bot_name}/remove_reply_keyboard", response_model=MessageResponse)
    async def remove_reply_keyboard(
        bot_name: str,
        request: RemoveReplyKeyboardRequest,
    ) -> Dict[str, Any]:
        try:
            client = bot_manager.get_client(bot_name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
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

    @router.post("/{bot_name}/send_file", response_model=MessageResponse)
    async def send_file(bot_name: str, request: SendFileRequest) -> Dict[str, Any]:
        try:
            client = bot_manager.get_client(bot_name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
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

    @router.post("/{bot_name}/edit_message", response_model=MessageResponse)
    async def edit_message(bot_name: str, request: EditMessageRequest) -> Dict[str, Any]:
        try:
            client = bot_manager.get_client(bot_name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        try:
            message = await client.edit_message(
                chat_id=request.chat_id,
                message_id=request.message_id,
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

    @router.post("/{bot_name}/get_updates", response_model=UpdatesResponse)
    async def get_updates(bot_name: str, request: GetUpdatesRequest) -> Dict[str, Any]:
        try:
            client = bot_manager.get_client(bot_name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        try:
            updates = await client.get_updates(
                limit=request.limit,
                timeout=request.timeout,
            )
            updates_list = []
            for update in updates:
                if update.message and update.message.voice:
                    text = await transcribe_voice(update.message.voice, client.bot)
                    message_type = "voice"
                elif update.message and update.message.text:
                    text = update.message.text
                    message_type = "text"
                else:
                    text = None
                    message_type = None
                reply_to_message_id = (
                    update.message.reply_to_message.message_id
                    if update.message and update.message.reply_to_message
                    else None
                )
                updates_list.append({
                    "update_id": update.update_id,
                    "chat_id": (
                        update.effective_chat.id
                        if update.effective_chat
                        else None
                    ),
                    "message_type": message_type,
                    "text": text,
                    "reply_to_message_id": reply_to_message_id,
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

    @router.get("/{bot_name}/get_chat_ids", response_model=ChatIdsResponse)
    async def get_chat_ids(
        bot_name: str,
        limit: int = Query(10, ge=1, le=100),
    ) -> Dict[str, Any]:
        try:
            client = bot_manager.get_client(bot_name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
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
                    message_type = "voice"
                elif update.message and update.message.text:
                    text = update.message.text
                    message_type = "text"
                else:
                    text = None
                    message_type = None
                if chat_id is not None and chat_id not in seen:
                    seen.add(chat_id)
                    chat_ids.append({
                        "chat_id": chat_id,
                        "message_type": message_type,
                        "text": text,
                    })
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
