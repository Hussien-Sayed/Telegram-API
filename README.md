# Telegram API Microservice

A FastAPI microservice that wraps the Telegram Bot API, providing HTTP endpoints for sending messages, managing reply keyboards, fetching updates, and sending files. The service supports multiple Telegram bots simultaneously, each identified by a unique bot name in the URL path, with tokens loaded via environment variables. Voice messages are automatically transcribed locally using OpenAI Whisper without requiring an external API key, and the service is packaged as a Docker image with ffmpeg included for audio processing.

## Getting Started

### Prerequisites

- Docker (recommended) OR Python 3.11+
- ffmpeg (required for Whisper audio processing; included in Docker image)
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| TELEGRAM_BOT_TOKEN_<BOT_NAME> | Yes | — | Set one environment variable per bot using the format `TELEGRAM_BOT_TOKEN_<BOT_NAME>`, where `<BOT_NAME>` is a unique identifier (e.g., `TELEGRAM_BOT_TOKEN_production`, `TELEGRAM_BOT_TOKEN_staging`) |
| WHISPER_MODEL | No | base | Whisper model size for voice transcription. Options: tiny, base, small, medium, large |
| WHISPER_DEVICE | No | cpu | Device for Whisper inference. Use `cpu` (default) or `cuda` for GPU acceleration |
| UPLOADS_PATH | No | uploads | Path to the uploads folder where files to be sent are stored (relative to app root) |

### Required Data

Files to be sent via the API must be placed in the `uploads/` folder at the project root. When running with Docker, this folder should be volume-mounted to make files available inside the container. Supported file types include documents, photos, videos, and audio files.

### Basic Run

1. Create a `.env` file with your Telegram bot token(s):

   ```
   TELEGRAM_BOT_TOKEN_production=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
   TELEGRAM_BOT_TOKEN_staging=987654321:ZYXwvutSRQponMLKjiHGfEDCBA
   TELEGRAM_BOT_TOKEN_dev=555555555:A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6
   WHISPER_MODEL=base
   WHISPER_DEVICE=cpu
   UPLOADS_PATH=uploads
   ```

2. Run with Docker (recommended):
   ```bash
   docker compose --env-file .env up --build
   ```

3. OR run locally:
   ```bash
   pip install -r requirements.txt
   uvicorn api.main:app --reload
   ```

4. Run tests:
   ```bash
   python -m pytest tests/test_api.py -v
   ```

### What You Can Do

- Access interactive Swagger UI at http://localhost:8000/docs
- Send health check: `curl http://localhost:8000/`
- List configured bots via GET /api/v1/bots
- Send messages via POST /api/v1/{bot_name}/send_message
- Send reply keyboards via POST /api/v1/{bot_name}/send_reply_keyboard
- Remove keyboards via POST /api/v1/{bot_name}/remove_reply_keyboard
- Fetch updates (voice messages auto-transcribed) via POST /api/v1/{bot_name}/get_updates
- Get chat IDs via GET /api/v1/{bot_name}/get_chat_ids
- Send files (documents, photos, videos, audio) via POST /api/v1/{bot_name}/send_file

Replace `{bot_name}` with your configured bot name (e.g., `production`, `staging`, `dev`).

Example API requests:
```bash
# List all registered bots
curl http://localhost:8000/api/v1/bots

# Send message using production bot
curl -X POST http://localhost:8000/api/v1/production/send_message \
  -H "Content-Type: application/json" \
  -d '{"chat_id": 123456789, "text": "Hello from production bot"}'

# Send message using staging bot
curl -X POST http://localhost:8000/api/v1/staging/send_message \
  -H "Content-Type: application/json" \
  -d '{"chat_id": 123456789, "text": "Hello from staging bot"}'

# Fetch updates with voice transcription
curl -X POST http://localhost:8000/api/v1/production/get_updates \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'

# Send a file
curl -X POST http://localhost:8000/api/v1/production/send_file \
  -H "Content-Type: application/json" \
  -d '{"chat_id": 123456789, "filename": "document.pdf", "file_type": "document", "caption": "Here is the document"}'
```

## Configuration

All configuration is done through environment variables. See the Environment Variables table above.

### Docker Volume Mounting for Uploads

When running with Docker, mount the uploads folder to make files available inside the container:

Using docker run:
```bash
docker run -p 127.0.0.1:8000:8000 \
  -e TELEGRAM_BOT_TOKEN_production=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ \
  -e TELEGRAM_BOT_TOKEN_staging=987654321:ZYXwvutSRQponMLKjiHGfEDCBA \
  -v $(pwd)/uploads:/app/uploads \
  telegram-api
```

Using docker-compose.yml, add this to the service:
```yaml
volumes:
  - ./uploads:/app/uploads
```
