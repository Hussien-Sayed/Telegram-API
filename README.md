# Telegram API Microservice

A FastAPI microservice that wraps the Telegram Bot API, providing HTTP endpoints for sending messages, managing reply keyboards, fetching updates, and sending files. The service automatically transcribes voice messages locally using OpenAI Whisper without requiring an external API key, and is packaged as a Docker image with ffmpeg included for audio processing.

## Getting Started

### Prerequisites

- Docker (recommended) OR Python 3.11+
- ffmpeg (required for Whisper audio processing; included in Docker image)
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| TELEGRAM_BOT_TOKEN | Yes | — | Your Telegram bot token used to authenticate with the Telegram Bot API |
| WHISPER_MODEL | No | base | Whisper model size for voice transcription. Options: tiny, base, small, medium, large |
| WHISPER_DEVICE | No | cpu | Device for Whisper inference. Use `cpu` (default) or `cuda` for GPU acceleration |
| UPLOADS_PATH | No | uploads | Path to the uploads folder where files to be sent are stored (relative to app root) |

### Required Data

Files to be sent via the API must be placed in the `uploads/` folder at the project root. When running with Docker, this folder should be volume-mounted to make files available inside the container. Supported file types include documents, photos, videos, and audio files.

### Basic Run

1. Create a `.env` file with your Telegram bot token:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
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
- Send messages via POST /api/v1/send_message
- Send reply keyboards via POST /api/v1/send_reply_keyboard
- Remove keyboards via POST /api/v1/remove_reply_keyboard
- Fetch updates (voice messages auto-transcribed) via POST /api/v1/get_updates
- Get chat IDs via GET /api/v1/get_chat_ids
- Send files (documents, photos, videos, audio) via POST /api/v1/send_file

Example `get_updates` request with voice transcription:
```bash
curl -X POST http://localhost:8000/api/v1/get_updates \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'
```

Example response showing transcribed voice message in `text`:
```json
{
  "success": true,
  "updates": [
    {
      "update_id": 123,
      "chat_id": 456789,
      "text": "this is the transcribed voice message"
    }
  ],
  "error": null
}
```

Example send_file requests:
```bash
# Send a document
curl -X POST http://localhost:8000/api/v1/send_file \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": 123456789,
    "filename": "document.pdf",
    "file_type": "document",
    "caption": "Here is the document"
  }'

# Send a photo
curl -X POST http://localhost:8000/api/v1/send_file \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": 123456789,
    "filename": "image.jpg",
    "file_type": "photo",
    "caption": "Check out this image"
  }'

# Send a video
curl -X POST http://localhost:8000/api/v1/send_file \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": 123456789,
    "filename": "video.mp4",
    "file_type": "video"
  }'

# Send audio
curl -X POST http://localhost:8000/api/v1/send_file \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": 123456789,
    "filename": "audio.mp3",
    "file_type": "audio",
    "caption": "Listen to this"
  }'
```

## Configuration

All configuration is done through environment variables. See the Environment Variables table above.

### Docker Volume Mounting for Uploads

When running with Docker, mount the uploads folder to make files available inside the container:

Using docker run:
```bash
docker run -p 127.0.0.1:8000:8000 \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -v $(pwd)/uploads:/app/uploads \
  telegram-api
```

Using docker-compose.yml, add this to the service:
```yaml
volumes:
  - ./uploads:/app/uploads
```
