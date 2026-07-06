"""Manager for multiple Telegram bot clients."""

import os
from typing import Dict, List, Optional

from telegram_api.utils import TelegramClient


class BotManager:
    """Manages multiple Telegram bot clients loaded from environment variables.

    Bot names are stored in a case-insensitive manner internally (normalized to lowercase),
    but the original display names are preserved for retrieval via `get_bot_names()`.
    """

    def __init__(self, clients: Optional[Dict[str, TelegramClient]] = None) -> None:
        """Initialize the BotManager.

        Args:
            clients: Optional dictionary mapping bot names to TelegramClient instances.
                     If None, bots are loaded from environment variables.
        """
        if clients is None:
            self._clients: Dict[str, TelegramClient] = {}
            self._original_names: Dict[str, str] = {}
            self.load_bots_from_env()
        else:
            self._clients = {}
            self._original_names = {}
            for name, client in clients.items():
                normalized = name.lower()
                self._clients[normalized] = client
                self._original_names[normalized] = normalized

    def load_bots_from_env(self) -> None:
        """Load bot clients from environment variables.

        Scans `os.environ` for keys starting with `TELEGRAM_BOT_TOKEN_`.
        The suffix after the prefix is used as the bot name.
        For example, `TELEGRAM_BOT_TOKEN_MyBot` creates a bot named "MyBot".
        """
        prefix = "TELEGRAM_BOT_TOKEN_"
        for key, value in os.environ.items():
            if key.startswith(prefix) and value:
                bot_name = key[len(prefix) :]
                if bot_name:
                    normalized = bot_name.lower()
                    self._clients[normalized] = TelegramClient(token=value)
                    self._original_names[normalized] = normalized

    def get_client(self, bot_name: str) -> TelegramClient:
        """Get a TelegramClient by bot name.

        Args:
            bot_name: The name of the bot (case-insensitive).

        Returns:
            The TelegramClient instance for the specified bot.

        Raises:
            KeyError: If no bot with the given name is registered.
        """
        normalized = bot_name.lower()
        if normalized not in self._clients:
            raise KeyError(f"Bot '{bot_name}' not found. Available bots: {self.get_bot_names()}")
        return self._clients[normalized]

    def get_bot_names(self) -> List[str]:
        """Get a sorted list of all registered bot names.

        Returns:
            Sorted list of original bot names (preserving original casing).
        """
        return sorted(self._original_names.values())

    async def shutdown_all(self) -> None:
        """Shutdown all bot clients.

        Iterates over all registered clients and calls their shutdown method.
        """
        for client in self._clients.values():
            await client.shutdown()
