"""FastAPI entry point for the Telegram API microservice."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from telegram_api import BotManager

from .router import create_router


_bot_manager = BotManager()
if not _bot_manager.get_bot_names():
    raise ValueError("No bot tokens configured. Set TELEGRAM_BOT_TOKEN_<BOT_NAME> environment variables.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Yield control to the app and shut down the client on exit."""
    yield
    await _bot_manager.shutdown_all()


app = FastAPI(
    title="Telegram API Microservice",
    description="HTTP wrapper around the Telegram Bot API.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "telegram-api"}


app.include_router(create_router(_bot_manager))
