"""Unit tests for the BotManager multi-bot manager."""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Stub out the 'whisper' module before any project imports so tests run
# without openai-whisper installed locally (it lives in the Docker image).
_whisper_stub = MagicMock()
sys.modules.setdefault("whisper", _whisper_stub)

from telegram_api.bot_manager import BotManager


class TestBotManager:
    """Test cases for BotManager class."""

    def test_init(self):
        """BotManager can be initialized with an explicit clients dict."""
        mock_client1 = MagicMock()
        mock_client2 = MagicMock()
        clients = {"BotOne": mock_client1, "BotTwo": mock_client2}

        manager = BotManager(clients=clients)

        assert manager.get_client("BotOne") is mock_client1
        assert manager.get_client("BotTwo") is mock_client2
        assert manager.get_client("botone") is mock_client1
        assert manager.get_client("BOTONE") is mock_client1

    def test_load_bots_from_env(self):
        """With TELEGRAM_BOT_TOKEN_* env vars set, the manager loads the correct bots and names."""
        env_vars = {
            "TELEGRAM_BOT_TOKEN_MyBot": "token1",
            "TELEGRAM_BOT_TOKEN_AnotherBot": "token2",
            "TELEGRAM_BOT_TOKEN_ThirdBot": "token3",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with patch("telegram_api.bot_manager.TelegramClient") as MockClient:
                manager = BotManager()

                assert MockClient.call_count == 3
                call_tokens = [call.kwargs["token"] for call in MockClient.call_args_list]
                assert "token1" in call_tokens
                assert "token2" in call_tokens
                assert "token3" in call_tokens

                bot_names = manager.get_bot_names()
                assert "mybot" in bot_names
                assert "anotherbot" in bot_names
                assert "thirdbot" in bot_names

    def test_get_client(self):
        """Returns the correct client for a known bot name (case-insensitive)."""
        mock_client = MagicMock()
        manager = BotManager(clients={"TestBot": mock_client})

        assert manager.get_client("TestBot") is mock_client
        assert manager.get_client("testbot") is mock_client
        assert manager.get_client("TESTBOT") is mock_client

    def test_get_client_not_found(self):
        """Raises KeyError for an unknown bot name."""
        manager = BotManager(clients={"KnownBot": MagicMock()})

        with pytest.raises(KeyError) as exc_info:
            manager.get_client("UnknownBot")

        assert "UnknownBot" in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    def test_get_bot_names(self):
        """Returns sorted list of original names without tokens."""
        clients = {
            "ZebraBot": MagicMock(),
            "AlphaBot": MagicMock(),
            "MiddleBot": MagicMock(),
        }
        manager = BotManager(clients=clients)

        names = manager.get_bot_names()
        assert names == ["alphabot", "middlebot", "zebrabot"]

    @pytest.mark.asyncio
    async def test_shutdown_all(self):
        """Calls await client.shutdown() on every managed client."""
        mock_client1 = MagicMock()
        mock_client1.shutdown = AsyncMock()
        mock_client2 = MagicMock()
        mock_client2.shutdown = AsyncMock()

        manager = BotManager(clients={"Bot1": mock_client1, "Bot2": mock_client2})
        await manager.shutdown_all()

        mock_client1.shutdown.assert_awaited_once()
        mock_client2.shutdown.assert_awaited_once()
