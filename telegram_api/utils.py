"""Small Telegram API wrapper for sending messages and reading updates."""

import logging
import os
from typing import Any, Dict, List, Optional

from telegram import (
    Bot,
    InputFile,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.error import TelegramError
from telegramify_markdown import convert as md_convert
from telegramify_markdown import entities_to_markdownv2
from telegramify_markdown import split_markdownv2

import whisper

logger = logging.getLogger(__name__)

TELEGRAM_MESSAGE_LIMIT = 4096

# Load the Whisper model once at module level (singleton).
# Device is hardcoded to CPU — GPU is never used in this service.
_whisper_model_name = os.getenv("WHISPER_MODEL", "base")
logger.info("Loading Whisper model '%s' on cpu", _whisper_model_name)
_whisper_model = whisper.load_model(_whisper_model_name, device="cpu")

# Timeouts for large file transfers to/from Telegram (in seconds).
TELEGRAM_DOWNLOAD_TIMEOUT = float(os.getenv("TELEGRAM_DOWNLOAD_TIMEOUT", "300.0"))
TELEGRAM_UPLOAD_TIMEOUT = float(os.getenv("TELEGRAM_UPLOAD_TIMEOUT", "300.0"))


def _split_text_safely(text: str, limit: int = 4096) -> List[str]:
    if len(text) <= limit:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + limit
        
        if end >= len(text):
            chunks.append(text[start:])
            break
        
        # Prefer splitting at newline
        newline_pos = text.rfind('\n', start, end)
        if newline_pos > start:
            chunks.append(text[start:newline_pos])
            start = newline_pos + 1
            continue
        
        # Prefer splitting at space
        space_pos = text.rfind(' ', start, end)
        if space_pos > start:
            chunks.append(text[start:space_pos])
            start = space_pos + 1
            continue
        
        # Split at limit if no safe boundary
        chunks.append(text[start:end])
        start = end
    
    # Filter empty chunks
    return [chunk for chunk in chunks if chunk]


async def transcribe_voice(voice: Any, bot: Any) -> str:
    tmp_path = f"/tmp/voice_{voice.file_id}.ogg"
    try:
        tg_file = await bot.get_file(voice.file_id)
        await tg_file.download_to_drive(
            tmp_path, read_timeout=TELEGRAM_DOWNLOAD_TIMEOUT
        )
        result = _whisper_model.transcribe(str(tmp_path))
        return result["text"].strip()
    except Exception as exc:
        logger.error("Voice transcription failed: %s", exc)
        return "transcription failed"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def _convert_markdown(text: str) -> str:
    """Convert standard Markdown to Telegram-safe MarkdownV2.

    If the conversion fails for any reason, the original text is returned
    unchanged so the caller can still attempt to send it.
    """
    try:
        plain_text, entities = md_convert(text)
        return entities_to_markdownv2(plain_text, entities)
    except Exception as exc:
        logger.warning("Markdown conversion failed: %s. Sending original text.", exc)
        return text


def _split_markdownv2_safely(text: str, limit: int = TELEGRAM_MESSAGE_LIMIT) -> List[str]:
    """Convert standard Markdown to MarkdownV2 and split it safely.

    Uses telegramify_markdown's split_markdownv2 so formatting entities
    (bold, italic, code, etc.) are never torn across chunk boundaries.
    Falls back to the plain-text splitter if the conversion fails.
    """
    try:
        plain_text, entities = md_convert(text)
        return list(split_markdownv2(plain_text, entities, max_utf16_len=limit))
    except Exception as exc:
        logger.warning("MarkdownV2-aware split failed: %s. Falling back to plain split.", exc)
        return _split_text_safely(text, limit)


class TelegramClient:
    """Thin wrapper around python-telegram-bot's Bot class.

    The bot token is read from the ``TELEGRAM_BOT_TOKEN`` environment variable
    unless it is provided explicitly.
    """

    DEFAULT_PARSE_MODE: str = "MarkdownV2"

    def __init__(
        self, token: Optional[str] = None, offset_path: Optional[str] = None
    ) -> None:
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError(
                "A Telegram bot token is required. "
                "Set the TELEGRAM_BOT_TOKEN environment variable or pass it explicitly."
            )
        self.bot = Bot(token=self.token)
        self.offset_path = offset_path
        self._last_update_id: int = self._load_offset() if offset_path else 0

    def _prepare_kwargs(self, **kwargs: Any) -> Dict[str, Any]:
        """Apply the default ``parse_mode`` unless the caller overrides it."""
        return {"parse_mode": self.DEFAULT_PARSE_MODE, **kwargs}

    async def send_message(
        self, chat_id: int, text: str, **kwargs: Any
    ) -> Any:
        """Send ``text`` to ``chat_id``.

        All extra keyword arguments are forwarded to ``Bot.send_message``.
        Messages are parsed as Markdown by default; pass ``parse_mode`` to
        override (e.g. ``parse_mode="HTML"`` or ``parse_mode=None``).

        If the text exceeds Telegram's message limit (4096 characters), it is
        automatically split into multiple messages. For the default
        ``MarkdownV2`` parse mode, splitting is entity-aware so formatting
        markers such as ``**bold**`` are never torn across chunk boundaries.

        When split, a dictionary is returned with the following keys:

        - ``message_id``: the ID of the first message (for backward compatibility)
        - ``message_ids``: a list of all message IDs
        - ``split``: ``True`` when the message was split, ``False`` otherwise

        If the message is not split, the original ``Message`` object is returned.
        """
        if not text:
            raise ValueError("Message text cannot be empty.")

        send_kwargs = self._prepare_kwargs(**kwargs)
        if send_kwargs.get("parse_mode") == self.DEFAULT_PARSE_MODE:
            chunks = _split_markdownv2_safely(text, TELEGRAM_MESSAGE_LIMIT)
        else:
            chunks = _split_text_safely(text, TELEGRAM_MESSAGE_LIMIT)

        logger.info("Sending %d message chunk(s) to chat %s", len(chunks), chat_id)
        try:
            if len(chunks) == 1:
                return await self.bot.send_message(
                    chat_id=chat_id, text=chunks[0], **send_kwargs
                )

            message_ids = []
            for chunk in chunks:
                if not chunk:
                    continue
                message = await self.bot.send_message(
                    chat_id=chat_id, text=chunk, **send_kwargs
                )
                message_ids.append(message.message_id)

            return {
                "message_id": message_ids[0],
                "message_ids": message_ids,
                "split": True,
            }
        except TelegramError as exc:
            logger.error("Failed to send message to chat %s: %s", chat_id, exc)
            raise

    async def send_reply_keyboard(
        self,
        chat_id: int,
        text: str,
        keyboard: List[List[str]],
        resize_keyboard: bool = True,
        one_time_keyboard: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Send ``text`` to ``chat_id`` with a reply keyboard.

        ``keyboard`` is a list of rows; each row is a list of button labels.

        Example:
            [["Yes", "No"], ["Cancel"]]

        Extra keyword arguments are forwarded to ``send_message``.
        """
        if not text:
            raise ValueError("Message text cannot be empty.")
        if not keyboard:
            raise ValueError("Keyboard cannot be empty.")

        buttons = [
            [KeyboardButton(text=label) for label in row]
            for row in keyboard
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard=buttons,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=one_time_keyboard,
        )
        return await self.send_message(
            chat_id=chat_id, text=text, reply_markup=reply_markup, **kwargs
        )

    async def remove_reply_keyboard(
        self, chat_id: int, text: str = "Keyboard removed.", **kwargs: Any
    ) -> Any:
        """Send a message that removes the current reply keyboard from the chat.

        All extra keyword arguments are forwarded to ``send_message``.
        """
        if not text:
            raise ValueError("Message text cannot be empty.")

        return await self.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=ReplyKeyboardRemove(),
            **kwargs,
        )

    async def send_file(
        self,
        chat_id: int,
        filename: str,
        file_type: str,
        caption: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """Send a file to ``chat_id``.

        The file is loaded from the ``uploads/`` directory.

        ``file_type`` must be one of: ``document``, ``photo``, ``video``, ``audio``.

        Extra keyword arguments are forwarded to the appropriate send method.
        """
        # Construct full file path
        file_path = os.path.join("uploads", filename)

        # Validate file exists
        if not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Validate file_type
        valid_file_types = {"document", "photo", "video", "audio"}
        if file_type not in valid_file_types:
            error_msg = f"Invalid file_type: {file_type}. Must be one of: {valid_file_types}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        send_kwargs = self._prepare_kwargs(**kwargs)
        write_timeout = send_kwargs.pop("write_timeout", TELEGRAM_UPLOAD_TIMEOUT)
        if caption is not None and send_kwargs.get("parse_mode") == self.DEFAULT_PARSE_MODE:
            caption = _convert_markdown(caption)

        logger.info(
            "Sending %s to chat %s: %s (caption: %s)",
            file_type,
            chat_id,
            filename,
            caption,
        )

        try:
            # Open file and create InputFile
            with open(file_path, "rb") as f:
                input_file = InputFile(f.read(), filename=filename)

                # Use appropriate method based on file_type
                if file_type == "document":
                    return await self.bot.send_document(
                        chat_id=chat_id,
                        document=input_file,
                        caption=caption,
                        write_timeout=write_timeout,
                        **send_kwargs,
                    )
                elif file_type == "photo":
                    return await self.bot.send_photo(
                        chat_id=chat_id,
                        photo=input_file,
                        caption=caption,
                        write_timeout=write_timeout,
                        **send_kwargs,
                    )
                elif file_type == "video":
                    return await self.bot.send_video(
                        chat_id=chat_id,
                        video=input_file,
                        caption=caption,
                        write_timeout=write_timeout,
                        **send_kwargs,
                    )
                elif file_type == "audio":
                    return await self.bot.send_audio(
                        chat_id=chat_id,
                        audio=input_file,
                        caption=caption,
                        write_timeout=write_timeout,
                        **send_kwargs,
                    )
        except TelegramError as exc:
            logger.error(
                "Failed to send %s to chat %s: %s", file_type, chat_id, exc
            )
            raise

    async def edit_message(
        self, chat_id: int, message_id: int, text: str, **kwargs: Any
    ) -> Any:
        """Edit an existing message in ``chat_id``.

        All extra keyword arguments are forwarded to ``Bot.edit_message_text``.
        """
        if not text:
            raise ValueError("Message text cannot be empty.")

        edit_kwargs = self._prepare_kwargs(**kwargs)
        if edit_kwargs.get("parse_mode") == self.DEFAULT_PARSE_MODE:
            text = _convert_markdown(text)

        logger.info("Editing message %s in chat %s", message_id, chat_id)
        try:
            return await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                **edit_kwargs,
            )
        except TelegramError as exc:
            logger.error(
                "Failed to edit message %s in chat %s: %s", message_id, chat_id, exc
            )
            raise

    async def get_updates(
        self,
        limit: int = 10,
        timeout: int = 0,
    ) -> List[Update]:
        """Fetch recent updates from all chats.

        The wrapper keeps track of the last processed update ID so that the same
        updates are not returned twice.
        """
        try:
            updates = await self.bot.get_updates(
                offset=self._last_update_id + 1,
                limit=limit,
                timeout=timeout,
            )
        except TelegramError as exc:
            logger.error("Failed to fetch updates: %s", exc)
            raise

        if updates:
            self._last_update_id = max(update.update_id for update in updates)
            self._save_offset()

        return updates

    def _load_offset(self) -> int:
        if not self.offset_path:
            return 0
        try:
            with open(self.offset_path, "r") as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            return 0

    def _save_offset(self) -> None:
        if not self.offset_path:
            return
        try:
            with open(self.offset_path, "w") as f:
                f.write(str(self._last_update_id))
        except OSError as exc:
            logger.warning("Could not save update offset: %s", exc)

    async def shutdown(self) -> None:
        """Clean up the underlying bot session."""
        await self.bot.shutdown()
