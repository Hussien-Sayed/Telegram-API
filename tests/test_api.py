"""Unit tests for the Telegram API FastAPI microservice.

All Telegram API calls are mocked so the tests run without a real bot token.
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from telegram.error import TelegramError


os.environ["TELEGRAM_BOT_TOKEN_TEST"] = "fake-token-for-tests"

# Stub out the 'whisper' module before any project imports so tests run
# without openai-whisper installed locally (it lives in the Docker image).
_whisper_stub = MagicMock()
sys.modules.setdefault("whisper", _whisper_stub)


# Patch the Bot class before importing the FastAPI app, because the
# TelegramClient is created at module-import time.
with patch("telegram_api.utils.Bot") as _MockBot:
    _bot_instance = AsyncMock()
    _bot_instance.send_message = AsyncMock(
        return_value=AsyncMock(message_id=42)
    )
    _bot_instance.edit_message_text = AsyncMock(
        return_value=AsyncMock(message_id=42)
    )
    _bot_instance.get_updates = AsyncMock(return_value=[])
    _bot_instance.shutdown = AsyncMock()
    _MockBot.return_value = _bot_instance

    from api.main import app
    from api.models import SendFileRequest


client = TestClient(app)


def _fake_update(update_id: int, chat_id: int, text: str = "Hi", reply_to_message_id: int = None):
    update = AsyncMock()
    update.update_id = update_id
    update.effective_chat = AsyncMock(id=chat_id)
    update.message = AsyncMock(text=text)
    update.message.voice = None  # explicitly not a voice message
    if reply_to_message_id is not None:
        update.message.reply_to_message = AsyncMock()
        update.message.reply_to_message.message_id = reply_to_message_id
    else:
        update.message.reply_to_message = None
    return update


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "telegram-api"}


def test_send_message():
    response = client.post(
        "/api/v1/test/send_message",
        json={"chat_id": 123456789, "text": "Hello!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message_id"] == 42
    assert data["error"] is None


def test_send_message_empty_text():
    response = client.post(
        "/api/v1/test/send_message",
        json={"chat_id": 123456789, "text": ""},
    )
    assert response.status_code == 400
    assert "text" in response.json()["detail"].lower()


def test_send_message_uses_markdown_v2_by_default():
    """Messages are sent with parse_mode=MarkdownV2 and converted."""
    _bot_instance.send_message.reset_mock()
    response = client.post(
        "/api/v1/test/send_message",
        json={"chat_id": 123456789, "text": "**bold** _italic_"},
    )
    assert response.status_code == 200
    _bot_instance.send_message.assert_awaited_once()
    call_kwargs = _bot_instance.send_message.call_args.kwargs
    assert call_kwargs["chat_id"] == 123456789
    assert call_kwargs["text"] == "*bold* _italic_"
    assert call_kwargs["parse_mode"] == "MarkdownV2"


def test_send_message_long_text_split():
    """Test that long text (>4096 chars) is split into multiple messages."""
    # Configure mock to return different message_id values for each call
    _bot_instance.send_message.reset_mock()
    _bot_instance.send_message.side_effect = [
        AsyncMock(message_id=1),
        AsyncMock(message_id=2),
        AsyncMock(message_id=3),
    ]

    # Send text longer than 4096 characters
    long_text = "a" * 5000
    response = client.post(
        "/api/v1/test/send_message",
        json={"chat_id": 123456789, "text": long_text},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["split"] is True
    assert data["message_ids"] is not None
    assert len(data["message_ids"]) >= 2
    assert data["message_id"] == data["message_ids"][0]
    assert data["error"] is None

    # Verify send_message was called multiple times
    assert _bot_instance.send_message.call_count >= 2

    # Reset the mock to default behavior for other tests
    _bot_instance.send_message.reset_mock()
    _bot_instance.send_message.side_effect = None
    _bot_instance.send_message.return_value = AsyncMock(message_id=42)


def test_send_message_short_text_not_split():
    """Test that short text is not split and returns single message_id."""
    _bot_instance.send_message.reset_mock()
    _bot_instance.send_message.side_effect = None
    _bot_instance.send_message.return_value = AsyncMock(message_id=42)

    response = client.post(
        "/api/v1/test/send_message",
        json={"chat_id": 123456789, "text": "Hello!"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["split"] is False
    assert data["message_ids"] is None
    assert data["message_id"] == 42
    assert data["error"] is None

    # Verify send_message was called only once
    _bot_instance.send_message.assert_awaited_once()

    # Reset the mock to default behavior for other tests
    _bot_instance.send_message.reset_mock()
    _bot_instance.send_message.return_value = AsyncMock(message_id=42)


def test_send_message_allows_parse_mode_override():
    """Callers can override the default MarkdownV2 parse_mode via kwargs."""
    _bot_instance.send_message.reset_mock()
    response = client.post(
        "/api/v1/test/send_message",
        json={
            "chat_id": 123456789,
            "text": "<b>bold</b>",
            "kwargs": {"parse_mode": "HTML"},
        },
    )
    assert response.status_code == 200
    call_kwargs = _bot_instance.send_message.call_args.kwargs
    assert call_kwargs["parse_mode"] == "HTML"
    assert call_kwargs["text"] == "<b>bold</b>"


def test_send_message_skips_conversion_when_parse_mode_none():
    """If parse_mode is explicitly None, the original text is sent unchanged."""
    _bot_instance.send_message.reset_mock()
    response = client.post(
        "/api/v1/test/send_message",
        json={
            "chat_id": 123456789,
            "text": "**bold** _italic_",
            "kwargs": {"parse_mode": None},
        },
    )
    assert response.status_code == 200
    call_kwargs = _bot_instance.send_message.call_args.kwargs
    assert call_kwargs["parse_mode"] is None
    assert call_kwargs["text"] == "**bold** _italic_"


def test_edit_message():
    response = client.post(
        "/api/v1/test/edit_message",
        json={"chat_id": 123456789, "message_id": 123, "text": "Updated text"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message_id"] == 42
    assert data["error"] is None


def test_edit_message_empty_text():
    response = client.post(
        "/api/v1/test/edit_message",
        json={"chat_id": 123456789, "message_id": 123, "text": ""},
    )
    assert response.status_code == 400
    assert "text" in response.json()["detail"].lower()


def test_edit_message_uses_markdown_v2_by_default():
    """Edited messages are converted to Telegram MarkdownV2 by default."""
    _bot_instance.edit_message_text.reset_mock()
    response = client.post(
        "/api/v1/test/edit_message",
        json={"chat_id": 123456789, "message_id": 123, "text": "**bold**"},
    )
    assert response.status_code == 200
    _bot_instance.edit_message_text.assert_awaited_once()
    call_kwargs = _bot_instance.edit_message_text.call_args.kwargs
    assert call_kwargs["parse_mode"] == "MarkdownV2"
    assert call_kwargs["text"] == "*bold*"


def test_edit_message_invalid_bot():
    response = client.post(
        "/api/v1/unknown_bot/edit_message",
        json={"chat_id": 123456789, "message_id": 123, "text": "Updated text"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_edit_message_telegram_error():
    with patch("telegram_api.utils.TelegramClient.edit_message") as mock_edit:
        mock_edit.side_effect = TelegramError("Telegram API failure")
        response = client.post(
            "/api/v1/test/edit_message",
            json={"chat_id": 123456789, "message_id": 123, "text": "Updated text"},
        )
    assert response.status_code == 500
    assert "Telegram API failure" in response.json()["detail"]


def test_send_reply_keyboard():
    response = client.post(
        "/api/v1/test/send_reply_keyboard",
        json={
            "chat_id": 123456789,
            "text": "Pick an option",
            "keyboard": [["Yes", "No"], ["Cancel"]],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message_id"] == 42


def test_send_reply_keyboard_empty_keyboard():
    response = client.post(
        "/api/v1/test/send_reply_keyboard",
        json={"chat_id": 123456789, "text": "Pick", "keyboard": []},
    )
    assert response.status_code == 400


def test_remove_reply_keyboard():
    response = client.post(
        "/api/v1/test/remove_reply_keyboard",
        json={"chat_id": 123456789},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message_id"] == 42


def test_get_updates():
    updates = [
        _fake_update(1, 123456789, "msg1"),
        _fake_update(2, 99999, "msg2"),
    ]
    with patch("telegram_api.utils.TelegramClient.get_updates") as mock_get:
        mock_get.return_value = updates
        response = client.post(
            "/api/v1/test/get_updates",
            json={"limit": 10},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # The endpoint returns all updates without filtering by chat_id.
    assert len(data["updates"]) == 2
    # Verify updates from multiple chat IDs are returned
    chat_ids = {update["chat_id"] for update in data["updates"]}
    assert chat_ids == {123456789, 99999}
    # Text messages should be marked as type "text"
    assert all(update["message_type"] == "text" for update in data["updates"])
    mock_get.assert_awaited_once_with(limit=10, timeout=0)


def test_get_chat_ids():
    updates = [
        _fake_update(1, 123456789, "msg1"),
        _fake_update(2, 123456789, "msg2"),
        _fake_update(3, 99999, "msg3"),
    ]
    with patch("telegram_api.utils.TelegramClient.get_updates") as mock_get:
        mock_get.return_value = updates
        response = client.get("/api/v1/test/get_chat_ids?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    chat_ids = [entry["chat_id"] for entry in data["chat_ids"]]
    assert chat_ids == [123456789, 99999]
    # All entries came from text messages
    assert all(entry["message_type"] == "text" for entry in data["chat_ids"])
    mock_get.assert_awaited_once_with(limit=10)


def test_error_handling():
    with patch("telegram_api.utils.TelegramClient.send_message") as mock_send:
        mock_send.side_effect = TelegramError("Telegram API failure")
        response = client.post(
            "/api/v1/test/send_message",
            json={"chat_id": 123456789, "text": "Hello!"},
        )
    assert response.status_code == 500
    assert "Telegram API failure" in response.json()["detail"]


def test_get_bots():
    """Test GET /api/v1/bots returns the list of configured bots."""
    response = client.get("/api/v1/bots")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["bot_names"] == ["test"]
    assert data["error"] is None


def test_invalid_bot_name():
    """Test that an unknown bot name returns HTTP 404."""
    response = client.post(
        "/api/v1/unknown_bot/send_message",
        json={"chat_id": 123456789, "text": "Hello!"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_multiple_bots():
    """Test BotManager with multiple bot tokens configured."""
    from telegram_api import BotManager

    # Configure exactly two bot tokens, clearing other env vars so only these two are loaded.
    env_vars = {
        "TELEGRAM_BOT_TOKEN_BOT1": "token1",
        "TELEGRAM_BOT_TOKEN_BOT2": "token2",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        bot_manager = BotManager()
        bot_names = bot_manager.get_bot_names()
        assert sorted(bot_names) == ["bot1", "bot2"]


# ============================================================================
# Tests for transcribe_voice function
# ============================================================================

import asyncio
from telegram_api.utils import transcribe_voice


def _fake_voice(file_id: str = "test_file_id"):
    """Create a fake voice object with a file_id."""
    voice = MagicMock()
    voice.file_id = file_id
    return voice


def test_transcribe_voice_happy_path():
    """Test successful voice transcription."""
    async def _test():
        voice = _fake_voice("voice_123")
        bot = AsyncMock()

        # Mock the file object returned by bot.get_file
        tg_file = AsyncMock()
        tg_file.download_to_drive = AsyncMock()
        bot.get_file = AsyncMock(return_value=tg_file)

        # Mock the module-level singleton model (model is loaded once at import time)
        mock_model = MagicMock()
        mock_model.transcribe = MagicMock(return_value={"text": "  Hello world  "})

        with patch("telegram_api.utils._whisper_model", mock_model), \
             patch("telegram_api.utils.os.path.exists", return_value=True), \
             patch("telegram_api.utils.os.remove") as mock_remove:

            result = await transcribe_voice(voice, bot)

            # Verify the result is stripped
            assert result == "Hello world"

            # Verify the flow was called correctly
            bot.get_file.assert_awaited_once_with("voice_123")
            tg_file.download_to_drive.assert_awaited_once()
            mock_model.transcribe.assert_called_once()
            mock_remove.assert_called_once()

    asyncio.run(_test())


def test_transcribe_voice_transcription_failure():
    """Test transcription failure when the singleton model's transcribe raises."""
    async def _test():
        voice = _fake_voice("voice_456")
        bot = AsyncMock()

        # Mock the file object
        tg_file = AsyncMock()
        tg_file.download_to_drive = AsyncMock()
        bot.get_file = AsyncMock(return_value=tg_file)

        mock_model = MagicMock()
        mock_model.transcribe = MagicMock(side_effect=Exception("Whisper error"))

        with patch("telegram_api.utils._whisper_model", mock_model), \
             patch("telegram_api.utils.os.path.exists", return_value=True), \
             patch("telegram_api.utils.os.remove") as mock_remove:

            result = await transcribe_voice(voice, bot)

            # Verify it returns failure message without raising
            assert result == "transcription failed"

            # Verify cleanup still happens
            mock_remove.assert_called_once()

    asyncio.run(_test())


def test_transcribe_voice_download_failure():
    """Test transcription failure when bot.get_file raises exception."""
    async def _test():
        voice = _fake_voice("voice_789")
        bot = AsyncMock()

        bot.get_file = AsyncMock(side_effect=Exception("Download error"))

        with patch("telegram_api.utils.os.path.exists", return_value=False), \
             patch("telegram_api.utils.os.remove") as mock_remove:

            result = await transcribe_voice(voice, bot)

            # Verify it returns failure message without raising
            assert result == "transcription failed"

            # Verify cleanup is NOT called when file doesn't exist
            mock_remove.assert_not_called()

    asyncio.run(_test())


def test_transcribe_voice_file_cleanup_on_success():
    """Test that os.remove is called when file exists on success."""
    async def _test():
        voice = _fake_voice("voice_cleanup")
        bot = AsyncMock()

        tg_file = AsyncMock()
        tg_file.download_to_drive = AsyncMock()
        bot.get_file = AsyncMock(return_value=tg_file)

        mock_model = MagicMock()
        mock_model.transcribe = MagicMock(return_value={"text": "Test"})

        with patch("telegram_api.utils._whisper_model", mock_model), \
             patch("telegram_api.utils.os.path.exists", return_value=True), \
             patch("telegram_api.utils.os.remove") as mock_remove:

            result = await transcribe_voice(voice, bot)

            assert result == "Test"
            mock_remove.assert_called_once_with("/tmp/voice_voice_cleanup.ogg")

    asyncio.run(_test())


def test_transcribe_voice_file_cleanup_on_failure():
    """Test that os.remove is called when file exists on failure."""
    async def _test():
        voice = _fake_voice("voice_fail")
        bot = AsyncMock()

        tg_file = AsyncMock()
        tg_file.download_to_drive = AsyncMock()
        bot.get_file = AsyncMock(return_value=tg_file)

        mock_model = MagicMock()
        mock_model.transcribe = MagicMock(side_effect=Exception("Model error"))

        with patch("telegram_api.utils._whisper_model", mock_model), \
             patch("telegram_api.utils.os.path.exists", return_value=True), \
             patch("telegram_api.utils.os.remove") as mock_remove:

            result = await transcribe_voice(voice, bot)

            assert result == "transcription failed"
            mock_remove.assert_called_once_with("/tmp/voice_voice_fail.ogg")

    asyncio.run(_test())


def test_transcribe_voice_no_cleanup_when_file_missing():
    """Test that os.remove is NOT called when file doesn't exist."""
    async def _test():
        voice = _fake_voice("voice_missing")
        bot = AsyncMock()

        bot.get_file = AsyncMock(side_effect=Exception("Download failed"))

        with patch("telegram_api.utils.os.path.exists", return_value=False), \
             patch("telegram_api.utils.os.remove") as mock_remove:

            result = await transcribe_voice(voice, bot)

            assert result == "transcription failed"
            mock_remove.assert_not_called()

    asyncio.run(_test())


# ============================================================================
# Endpoint-level voice message tests
# ============================================================================

def _fake_voice_update(update_id: int, chat_id: int, file_id: str = "voice_file_id"):
    """Create a fake update with a voice message (no text)."""
    update = AsyncMock()
    update.update_id = update_id
    update.effective_chat = AsyncMock(id=chat_id)
    update.message = AsyncMock(spec=[])  # no auto-attributes
    update.message.text = None
    update.message.voice = AsyncMock()
    update.message.voice.file_id = file_id
    update.message.reply_to_message = None
    return update


def test_get_updates_voice_message():
    """Test that voice messages are transcribed and returned as text."""
    voice_update = _fake_voice_update(1, 123456789, "file_001")
    with patch("telegram_api.utils.TelegramClient.get_updates") as mock_get, \
         patch("api.router.transcribe_voice", new_callable=AsyncMock) as mock_transcribe:
        mock_get.return_value = [voice_update]
        mock_transcribe.return_value = "hello world"

        response = client.post(
            "/api/v1/test/get_updates",
            json={"chat_id": 123456789, "limit": 10},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["updates"][0]["text"] == "hello world"
    assert data["updates"][0]["chat_id"] == 123456789
    assert data["updates"][0]["message_type"] == "voice"


def test_get_updates_voice_transcription_failure():
    """Test that transcription failure returns the failure message."""
    voice_update = _fake_voice_update(2, 123456789, "file_002")
    with patch("telegram_api.utils.TelegramClient.get_updates") as mock_get, \
         patch("api.router.transcribe_voice", new_callable=AsyncMock) as mock_transcribe:
        mock_get.return_value = [voice_update]
        mock_transcribe.return_value = "transcription failed"

        response = client.post(
            "/api/v1/test/get_updates",
            json={"chat_id": 123456789, "limit": 10},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["updates"][0]["text"] == "transcription failed"
    assert data["updates"][0]["message_type"] == "voice"


def test_get_updates_text_message_unchanged():
    """Test that text messages are not affected by voice transcription mocking."""
    text_update = _fake_update(3, 123456789, "plain text message")
    with patch("telegram_api.utils.TelegramClient.get_updates") as mock_get, \
         patch("api.router.transcribe_voice", new_callable=AsyncMock) as mock_transcribe:
        mock_get.return_value = [text_update]

        response = client.post(
            "/api/v1/test/get_updates",
            json={"chat_id": 123456789, "limit": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["updates"][0]["text"] == "plain text message"
        assert data["updates"][0]["message_type"] == "text"
        assert data["updates"][0]["reply_to_message_id"] is None
        mock_transcribe.assert_not_called()


def test_get_updates_reply_to_message():
    """Test that reply_to_message_id is exposed for reply messages."""
    reply_update = _fake_update(4, 123456789, "reply text", reply_to_message_id=7)
    with patch("telegram_api.utils.TelegramClient.get_updates") as mock_get, \
         patch("api.router.transcribe_voice", new_callable=AsyncMock) as mock_transcribe:
        mock_get.return_value = [reply_update]

        response = client.post(
            "/api/v1/test/get_updates",
            json={"chat_id": 123456789, "limit": 10},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["updates"][0]["text"] == "reply text"
    assert data["updates"][0]["message_type"] == "text"
    assert data["updates"][0]["reply_to_message_id"] == 7
    mock_transcribe.assert_not_called()


def test_get_chat_ids_voice_message():
    """Test that get_chat_ids correctly handles mixed voice and text messages."""
    voice_update = _fake_voice_update(1, 111, "voice_a")
    text_update = _fake_update(2, 222, "text_b")
    with patch("telegram_api.utils.TelegramClient.get_updates") as mock_get, \
         patch("api.router.transcribe_voice", new_callable=AsyncMock) as mock_transcribe:
        mock_get.return_value = [voice_update, text_update]
        mock_transcribe.return_value = "voice transcript"

        response = client.get("/api/v1/test/get_chat_ids?limit=10")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["chat_ids"]) == 2

    # Find the entry for chat_id 111 (voice message)
    voice_entry = next(entry for entry in data["chat_ids"] if entry["chat_id"] == 111)
    assert voice_entry["text"] == "voice transcript"
    assert voice_entry["message_type"] == "voice"

    # Find the entry for chat_id 222 (text message)
    text_entry = next(entry for entry in data["chat_ids"] if entry["chat_id"] == 222)
    assert text_entry["text"] == "text_b"
    assert text_entry["message_type"] == "text"


# ============================================================================
# Tests for SendFileRequest model
# ============================================================================

def test_send_file():
    """Test SendFileRequest creation with all fields."""
    request = SendFileRequest(
        chat_id=123456789,
        filename="document.pdf",
        caption="Here is the document",
        file_type="document",
        kwargs={"parse_mode": "Markdown"},
    )
    assert request.chat_id == 123456789
    assert request.filename == "document.pdf"
    assert request.caption == "Here is the document"
    assert request.file_type == "document"
    assert request.kwargs == {"parse_mode": "Markdown"}


def test_send_file_not_found():
    """Test SendFileRequest with minimal required fields."""
    request = SendFileRequest(
        chat_id=123456789,
        filename="photo.jpg",
        file_type="photo",
    )
    assert request.chat_id == 123456789
    assert request.filename == "photo.jpg"
    assert request.file_type == "photo"
    assert request.caption is None
    assert request.kwargs is None


def test_send_file_invalid_type():
    """Test that invalid file_type raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        SendFileRequest(
            chat_id=123456789,
            filename="file.txt",
            file_type="invalid_type",
        )
    assert "Input should be 'document', 'photo', 'video' or 'audio'" in str(exc_info.value)


def test_send_file_document():
    """Test SendFileRequest with document file_type."""
    request = SendFileRequest(
        chat_id=123456789,
        filename="report.pdf",
        file_type="document",
    )
    assert request.file_type == "document"


def test_send_file_photo():
    """Test SendFileRequest with photo file_type."""
    request = SendFileRequest(
        chat_id=123456789,
        filename="image.jpg",
        file_type="photo",
    )
    assert request.file_type == "photo"


def test_send_file_video():
    """Test SendFileRequest with video file_type."""
    request = SendFileRequest(
        chat_id=123456789,
        filename="clip.mp4",
        file_type="video",
    )
    assert request.file_type == "video"


def test_send_file_audio():
    """Test SendFileRequest with audio file_type."""
    request = SendFileRequest(
        chat_id=123456789,
        filename="sound.mp3",
        file_type="audio",
    )
    assert request.file_type == "audio"
